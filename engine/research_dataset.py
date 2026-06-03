"""研究输入 metadata 合同。

本模块只定义 CR008 的 research_input_v1 报告合同，不读取真实数据、不触发
connector/runtime/storage，也不消费旧报告内容。
"""

from __future__ import annotations

import csv
from copy import deepcopy
from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
from datetime import date, datetime
from enum import Enum
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

import pandas as pd

from engine.events import evaluate_event_gate
from engine.quality import normalize_quality_status, quality_status_from_reader_result
from engine.trade_status import evaluate_trade_status_gate
from engine.trading_constraints import evaluate_price_limit_gate
from engine.universe import UniverseRequest, UniverseResolution, resolve_universe
from market_data.benchmarks import (
    BENCHMARK_POLICY_FIELDS,
    BenchmarkPolicy,
    build_benchmark_policy_result,
    resolve_hs300_benchmark,
)
from market_data.adjustment_readers import single_policy_gate
from market_data.contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
)
from market_data.dataset_groups import (
    CLAIM_CAPACITY_TRADABLE,
    CLAIM_CAPITAL_AMPLIFICATION,
    CLAIM_INDUSTRY_NEUTRALIZED,
    CLAIM_MARKET_CAP_NEUTRALIZED,
    CLAIM_PURE_ALPHA,
    CLAIM_SCALE_UP_READY,
    P1_BLOCKED_CLAIMS,
    REASON_P1_AUXILIARY_MISSING,
)
from market_data.readers import (
    AdjustmentAuditReaderResult,
    CurrentReaderSmokeResult,
    DATASET_CORPORATE_ACTIONS,
    QualityPolicy,
    ReaderResult,
    ResearchInputReaderRequest,
    evaluate_corporate_action_availability,
    extract_adj_factor_lineage,
    current_reader_smoke,
    read_dataset,
    read_adjustment_audit_inputs,
    read_research_inputs,
)
from market_data.release_scope import FORBIDDEN_OPERATION_COUNTER_KEYS, normalise_permission_counters
from market_data.unsupported import (
    CR014_UNSUPPORTED_PRODUCTION_CLAIMS,
    assert_no_derived_real_vwap_claim as _assert_no_derived_real_vwap_claim,
)

RESEARCH_INPUT_SCHEMA_NAME = "research_input_v1"
LEGACY_REPORT_POLICY = "legacy_only_not_current_truth"
CR013_PERMISSION_COUNTERS = {
    "provider_fetches": 0,
    "lake_writes": 0,
    "credential_reads": 0,
    "legacy_data_reads": 0,
    "old_report_overwrites": 0,
}

CR013_EXECUTION_UNSUPPORTED_CLAIMS = (
    "minute_execution",
    "tick_execution",
    "level2_execution",
    "order_book_execution",
    "order_detail_execution",
    "trade_detail_execution",
    "order_match_execution",
    "minute_tick_level2_order_match",
)

CR013_EXECUTION_RELEASE_CRITERIA = (
    "prices.vwap field published as real current truth",
    "vwap_status=available",
    "execution audit pass",
    "separate Story / CP5 / explicit user authorization before real provider or lake operations",
)

RESEARCH_INPUT_REQUIRED_FIELDS = frozenset(
    {
        "schema_name",
        "report_kind",
        "coverage_start",
        "coverage_end",
        "benchmark_status",
        "universe_mode",
        "adjustment_policy",
        "forward_return_horizon",
        "label_available_end",
        "quality_status",
        "readiness_status",
        "known_limitations",
        "allowed_claims",
        "legacy_report_policy",
    }
)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SENSITIVE_KEY_RE = re.compile(r"(token|secret|password|credential|api[_-]?key|private[_-]?key)", re.IGNORECASE)
_SENSITIVE_VALUE_RE = re.compile(
    r"(?i)\b(token|secret|password|credential|api[_-]?key|private[_-]?key)\s*[:=]\s*[^\s,;]+"
)
_VALID_UNIVERSE_MODES = frozenset({"fixed_snapshot", "pit_required", "pit_optional"})
_UNIVERSE_MODE_ALIASES = {"pit": "pit_required", "required": "pit_required"}
_VALID_ANALYSIS_MODES = frozenset({"research", "exploratory"})
_VALID_REALISM_MODES = frozenset({"production_strict", "exploratory"})
_VALID_BENCHMARK_POLICIES = frozenset({"hs300_required", "hs300_optional", "proxy_allowed"})
_W3_RESEARCH_DATASETS = (DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS)
_TRADABILITY_REQUIRED_DATASETS = _W3_RESEARCH_DATASETS
_TRADABILITY_REAL_CLAIMS = (
    "real_tradable_execution",
    "tradability_screened",
    "tradability_screened_execution",
    "true_fillability",
    "realistic_fillability",
)
_TRADABILITY_BASE_EXPLORATORY_CLAIMS = ("framework_validation", "exploratory_analysis")
_EXECUTION_PRICE_POLICIES = frozenset({"open", "close", "vwap", "close_proxy"})
_POLICY_MISSING = object()
_EXECUTION_REAL_CLAIMS = (
    "real_vwap_execution",
    "vwap_fill_claim",
    "vwap_execution",
    "real_open_execution",
    "open_execution",
    "real_tradable_execution",
    "tradability_screened_execution",
    "true_fillability",
    "realistic_fillability",
)
_ADJUSTMENT_CONSERVATIVE_CLAIMS = (
    "adjusted_price_used",
    "adjustment_policy_consistent",
    "adj_factor_lineage_available",
)
_ADJUSTMENT_COMPLETE_AUDIT_CLAIMS = (
    "corporate_action_audited",
    "auditable_adjustment_chain",
    "complete_corporate_action_audit",
)
_ADJUSTMENT_RESEARCH_CLAIMS = (
    "adjustment_consistent_research",
    "factor_calculation_adjustment_audited",
)

_AUXILIARY_BASE_ALLOWED_CLAIMS = (
    "framework_validation",
    "exploratory_analysis",
    "raw_factor_performance",
    "close_only_exploration",
    "volume_only_exploration",
)

_AUXILIARY_CAPABILITY_DEFAULTS: dict[str, dict[str, Any]] = {
    "tradability": {
        "source_dataset": "tradability",
        "required_columns": ("trade_date", "symbol", "is_tradable", "is_suspended", "is_st", "limit_status"),
        "required_for_claims": (
            "real_tradable_execution",
            "tradability_screened",
            "tradability_screened_execution",
            "true_fillability",
            "realistic_fillability",
        ),
        "status_field": "tradability_status",
    },
    "ohlcv_vwap": {
        "source_dataset": DATASET_PRICES,
        "required_columns": ("open", "high", "low", "close", "volume", "amount", "vwap"),
        "required_for_claims": (
            "vwap_execution",
            "open_execution",
            "intraday_range_factor",
            "full_ohlcv_factor",
        ),
        "status_field": "ohlcv_vwap_status",
    },
    "industry_classification": {
        "source_dataset": "industry_classification",
        "required_columns": ("trade_date", "symbol", "industry_code", "effective_date", "available_at"),
        "required_for_claims": (
            "industry_neutral",
            "industry_attribution",
            "industry_zscore",
            "industry_group_ic",
        ),
        "status_field": "industry_classification_status",
    },
    "market_cap": {
        "source_dataset": "market_cap",
        "required_columns": ("trade_date", "symbol", "market_cap", "float_market_cap"),
        "required_for_claims": (
            "size_neutral",
            "market_cap_neutral",
            "market_cap_weighted_ic",
            "capacity_analysis",
        ),
        "status_field": "market_cap_status",
    },
    "adjustment_audit": {
        "source_dataset": DATASET_PRICES,
        "required_columns": ("trade_date", "symbol", "adj_factor", "lineage_raw_checksum"),
        "required_for_claims": ("corporate_action_audited", "auditable_adjustment_chain"),
        "status_field": "adjustment_audit_status",
    },
    "liquidity": {
        "source_dataset": DATASET_PRICES,
        "required_columns": ("trade_date", "symbol", "amount", "turnover_rate"),
        "required_for_claims": (
            "liquidity_controlled",
            "tradable_capacity",
            "capacity_analysis",
            "liquidity_screened",
        ),
        "status_field": "liquidity_status",
    },
    "style_exposure": {
        "source_dataset": "style_exposure",
        "required_columns": ("trade_date", "symbol", "beta", "size", "value", "liquidity"),
        "required_for_claims": (
            "pure_alpha",
            "style_neutral",
            "style_neutral_alpha",
            "risk_model_adjusted",
            "risk_model_adjusted_alpha",
        ),
        "status_field": "style_exposure_status",
    },
    "pit_universe": {
        "source_dataset": DATASET_INDEX_MEMBERS,
        "required_columns": ("trade_date", "symbol", "effective_date", "available_at", "is_pit_universe", "pit_status"),
        "required_for_claims": (
            "pit_factor_research",
            "pit_universe_research",
            "survivorship_bias_controlled",
        ),
        "status_field": "pit_universe_status",
    },
    "label_quality": {
        "source_dataset": "label_window",
        "required_columns": ("label_available_end", "label_status", "forward_return_horizon"),
        "required_for_claims": ("complete_forward_return_label",),
        "status_field": "label_quality_status",
    },
}

_AUXILIARY_CAPABILITY_ORDER = tuple(_AUXILIARY_CAPABILITY_DEFAULTS)
_AUXILIARY_AVAILABLE_STATUSES = frozenset({"available", "pass"})

_EXPOSURE_CAPABILITY_DEFAULTS: dict[str, dict[str, Any]] = {
    "industry_classification": {
        "source_dataset": "industry_classification",
        "required_columns": (
            "symbol",
            "effective_date",
            "available_at",
            "classification_standard",
            "pit_status",
        ),
        "one_of_columns": (("industry_code", "industry_name"),),
        "required_for_claims": (
            "industry_neutral_ic",
            "industry_neutral",
            "industry_attribution",
            "industry_zscore",
            "industry_group_ic",
        ),
        "status_field": "industry_availability",
    },
    "market_cap": {
        "source_dataset": "market_cap",
        "required_columns": ("trade_date", "symbol", "market_cap", "available_at"),
        "required_for_claims": (
            "market_cap_neutral_ic",
            "market_cap_neutral",
            "size_neutral",
            "market_cap_weighted_ic",
            "capacity_size_supported",
        ),
        "status_field": "market_cap_availability",
    },
    "float_market_cap": {
        "source_dataset": "market_cap",
        "required_columns": ("trade_date", "symbol", "float_market_cap", "available_at"),
        "required_for_claims": (
            "market_cap_neutral_ic",
            "market_cap_neutral",
            "size_neutral",
            "market_cap_weighted_ic",
            "float_cap_neutral",
            "capacity_size_supported",
        ),
        "status_field": "float_market_cap_availability",
    },
    "style_exposure": {
        "source_dataset": "style_exposure",
        "required_columns": (
            "trade_date",
            "symbol",
            "style_factor",
            "exposure_value",
            "model_version",
            "available_at",
        ),
        "required_for_claims": (
            "style_neutral_ic",
            "style_neutral",
            "pure_alpha",
            "risk_model_adjusted_alpha",
        ),
        "status_field": "style_exposure_availability",
    },
}
_EXPOSURE_CAPABILITY_ORDER = tuple(_EXPOSURE_CAPABILITY_DEFAULTS)
_EXPOSURE_AVAILABLE_STATUSES = frozenset({"available"})
_EXPOSURE_BASE_ALLOWED_CLAIMS = ("framework_validation", "exploratory_analysis", "raw_factor_performance")
_NEUTRALIZATION_METRIC_CLAIMS = frozenset(
    {
        "industry_neutral_ic",
        "market_cap_neutral_ic",
        "style_neutral_ic",
        "pure_alpha",
        "risk_model_adjusted_alpha",
    }
)
_LIQUIDITY_CAPACITY_REQUIRED_INPUTS: dict[str, tuple[str, ...]] = {
    "amount": ("amount", "trade_amount", "daily_amount", "notional"),
    "volume": ("volume", "trade_volume", "daily_volume", "shares_traded"),
    "turnover": ("turnover", "turnover_rate", "portfolio_turnover", "turnover_with_cost"),
    "adv": ("adv", "adv20", "average_daily_amount", "average_daily_notional", "average_daily_volume"),
}
_LIQUIDITY_CAPACITY_STRONG_CLAIMS = (
    "capacity_tradable",
    "capacity_supported",
    "liquidity_screened_capacity",
    "tradable_capacity",
    "capacity_analysis",
    "liquidity_controlled",
)
_FACTOR_PANEL_REQUIRED_STAGES = ("raw", "directional", "winsorized", "zscore")
_ROBUST_VALIDATION_REQUIRED_VIEWS = ("rolling", "annual", "market_state", "parameter_grid", "cost_grid")
_FACTOR_AUDIT_STRONG_CLAIMS = (
    "factor_panel_audited",
    "robust_factor_validation_supported",
    "robust_factor_claim_supported",
)
_SAFETY_COUNTER_FIELDS = ("network_calls", "lake_writes", "credential_reads", "legacy_data_operations", "old_report_overwrites")


class ResearchDatasetStatus(str, Enum):
    """研究数据集构建结果状态。"""

    AVAILABLE = "available"
    AVAILABLE_WITH_WARNINGS = "available_with_warnings"
    REQUIRED_MISSING = "required_missing"
    QUALITY_FAILED = "quality_failed"
    INVALID_REQUEST = "invalid_request"
    GATE_FAILED = "gate_failed"


class GateStatus(str, Enum):
    """研究准入门状态。"""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True, slots=True)
class ResearchDatasetIssue:
    """统一研究数据集的结构化问题。"""

    code: str
    message: str
    severity: str = "ERROR"
    dataset: str | None = None
    field: str | None = None
    details: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "dataset": self.dataset,
            "field": self.field,
            "details": self.details,
        }
        return {key: _json_safe(value, key) for key, value in payload.items() if value not in (None, {}, [])}


@dataclass(slots=True)
class GateResult:
    """S03 基础 gate 容器，供后续 S04/S05/S06 扩展。"""

    status: str = GateStatus.NOT_EVALUATED.value
    issues: list[ResearchDatasetIssue] = dataclass_field(default_factory=list)
    checks: list[dict[str, Any]] = dataclass_field(default_factory=list)
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
            "checks": _json_safe(self.checks),
            "remediation_spec": _json_safe(self.remediation_spec),
        }


@dataclass(frozen=True, slots=True)
class ResearchDatasetRequest:
    """研究数据集只读构建请求。"""

    lake_root: str | Path | None = None
    start_date: str | date | None = None
    end_date: str | date | None = None
    universe: str = "csi300"
    universe_mode: str = "fixed_snapshot"
    benchmark_policy: str | Mapping[str, Any] | BenchmarkPolicy = "proxy_allowed"
    adjustment_policy: str = "qfq"
    forward_return_horizon: int = 20
    analysis_mode: str = "research"
    realism_mode: str | None = None
    symbols: tuple[str, ...] | None = None
    report_kind: str = "research_dataset"

    def __post_init__(self) -> None:
        object.__setattr__(self, "universe_mode", _normalize_universe_mode(self.universe_mode))
        if self.realism_mode == "exploratory":
            object.__setattr__(self, "analysis_mode", "exploratory")
        elif self.realism_mode == "production_strict":
            object.__setattr__(self, "analysis_mode", "research")


@dataclass(frozen=True, slots=True)
class AuxiliaryAvailabilityEntry:
    """单个辅助能力的可用性合同。"""

    capability: str
    status: str
    required_for_claims: list[str] = dataclass_field(default_factory=list)
    missing_reason: str = ""
    source_dataset: str | None = None
    required_columns: list[str] = dataclass_field(default_factory=list)
    observed_columns: list[str] = dataclass_field(default_factory=list)
    missing_columns: list[str] = dataclass_field(default_factory=list)
    quality_status: str | None = None
    lineage_status: str | None = None
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status in _AUXILIARY_AVAILABLE_STATUSES and not self.missing_columns

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "capability": self.capability,
            "status": self.status,
            "required_for_claims": self.required_for_claims,
            "missing_reason": self.missing_reason,
            "source_dataset": self.source_dataset,
            "required_columns": self.required_columns,
            "observed_columns": self.observed_columns,
            "missing_columns": self.missing_columns,
            "quality_status": self.quality_status,
            "lineage_status": self.lineage_status,
            "remediation_spec": self.remediation_spec,
        }
        return {key: _json_safe(value, key) for key, value in payload.items() if value not in (None, [], {}, "")}


@dataclass(frozen=True, slots=True)
class AuxiliaryAvailabilityMatrix:
    """辅助能力 availability matrix。"""

    entries: dict[str, AuxiliaryAvailabilityEntry] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {capability: entry.to_dict() for capability, entry in self.entries.items()}


@dataclass(frozen=True, slots=True)
class AllowedClaimsResult:
    """S06 allowed / blocked claims 评估结果。"""

    allowed_claims: list[str] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    auxiliary_availability: dict[str, Any] = dataclass_field(default_factory=dict)
    gate_status: str = GateStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_claims": _json_safe(self.allowed_claims),
            "blocked_claims": _json_safe(self.blocked_claims),
            "known_limitations": _json_safe(self.known_limitations),
            "auxiliary_availability": _json_safe(self.auxiliary_availability),
            "gate_status": self.gate_status,
        }


@dataclass(frozen=True, slots=True)
class ExposureAvailabilityEntry:
    """CR011-S06 单个 exposure capability 的 PIT availability。"""

    capability: str
    status: str
    coverage_ratio: float = 0.0
    missing_rate: float = 1.0
    sample_count: int = 0
    missing_count: int = 0
    as_of_join_violation_count: int = 0
    required_for_claims: list[str] = dataclass_field(default_factory=list)
    missing_reason: str = ""
    source_dataset: str | None = None
    required_columns: list[str] = dataclass_field(default_factory=list)
    observed_columns: list[str] = dataclass_field(default_factory=list)
    missing_columns: list[str] = dataclass_field(default_factory=list)
    lineage_status: str | None = None
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)

    @property
    def available(self) -> bool:
        return (
            self.status in _EXPOSURE_AVAILABLE_STATUSES
            and self.coverage_ratio >= 1.0
            and not self.missing_columns
            and self.as_of_join_violation_count == 0
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "capability": self.capability,
            "status": self.status,
            "coverage_ratio": float(self.coverage_ratio),
            "missing_rate": float(self.missing_rate),
            "sample_count": int(self.sample_count),
            "missing_count": int(self.missing_count),
            "as_of_join_violation_count": int(self.as_of_join_violation_count),
            "required_for_claims": self.required_for_claims,
            "missing_reason": self.missing_reason,
            "source_dataset": self.source_dataset,
            "required_columns": self.required_columns,
            "observed_columns": self.observed_columns,
            "missing_columns": self.missing_columns,
            "lineage_status": self.lineage_status,
            "remediation_spec": self.remediation_spec,
        }
        return {key: _json_safe(value, key) for key, value in payload.items() if value not in (None, [], {}, "")}


@dataclass(frozen=True, slots=True)
class ExposureAvailabilityMatrix:
    """CR011-S06 exposure availability matrix。"""

    entries: dict[str, ExposureAvailabilityEntry] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {capability: entry.to_dict() for capability, entry in self.entries.items()}


@dataclass(frozen=True, slots=True)
class NeutralizationClaimGateResult:
    """CR011-S06 中性化 / pure alpha 声明门禁结果。"""

    neutralization_status: str
    raw_ic: float | None = None
    industry_neutral_ic: float | None = None
    market_cap_neutral_ic: float | None = None
    style_neutral_ic: float | None = None
    allowed_claims: list[str] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    exposure_availability: dict[str, Any] = dataclass_field(default_factory=dict)
    gate_status: str = GateStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "neutralization_status": self.neutralization_status,
            "raw_ic": self.raw_ic,
            "industry_neutral_ic": self.industry_neutral_ic,
            "market_cap_neutral_ic": self.market_cap_neutral_ic,
            "style_neutral_ic": self.style_neutral_ic,
            "allowed_claims": _json_safe(self.allowed_claims),
            "blocked_claims": _json_safe(self.blocked_claims),
            "known_limitations": _json_safe(self.known_limitations),
            "exposure_availability": _json_safe(self.exposure_availability),
            "gate_status": self.gate_status,
        }


@dataclass(frozen=True, slots=True)
class _PitLifecycleGate:
    """CR011-S02 PIT universe + stock lifecycle gate 聚合结果。"""

    metadata: dict[str, Any] = dataclass_field(default_factory=dict)
    issues: list[ResearchDatasetIssue] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    checks: list[dict[str, Any]] = dataclass_field(default_factory=list)


@dataclass(slots=True)
class ResearchDataset:
    """统一研究数据集内存结果。"""

    status: str
    prices: pd.DataFrame | None = None
    close_df: pd.DataFrame | None = None
    calendar: list[date] = dataclass_field(default_factory=list)
    universe_symbols: list[str] = dataclass_field(default_factory=list)
    benchmark_result: Any | None = None
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)
    gate_result: GateResult = dataclass_field(default_factory=GateResult)
    issues: list[ResearchDatasetIssue] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    allowed_claims: list[str] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    auxiliary_availability: dict[str, Any] = dataclass_field(default_factory=dict)
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)
    reader_results: dict[str, ReaderResult] = dataclass_field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status in {
            ResearchDatasetStatus.AVAILABLE.value,
            ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value,
        }

    def to_metadata(self) -> dict[str, Any]:
        return metadata_to_dict(self.metadata)


@dataclass(frozen=True, slots=True)
class TradabilityGateRow:
    """单个 symbol/date/side 的 S03 可交易性 gate 行。"""

    trade_date: str
    symbol: str
    side: str
    can_buy: bool
    can_sell: bool
    tradability_gate_status: str
    blocked_reason: str = ""
    blocked_reasons: tuple[str, ...] = ()
    gate_details: dict[str, Any] = dataclass_field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.tradability_gate_status == "available"

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "side": self.side,
            "can_buy": self.can_buy,
            "can_sell": self.can_sell,
            "tradability_gate_status": self.tradability_gate_status,
            "blocked_reason": self.blocked_reason,
            "blocked_reasons": list(self.blocked_reasons),
            "gate_details": _json_safe(self.gate_details),
        }


@dataclass(frozen=True, slots=True)
class TradabilityGateMatrix:
    """S03 tradability matrix 聚合结果。"""

    rows: tuple[TradabilityGateRow, ...] = ()
    status: str = "required_missing"
    reason_counts: dict[str, int] = dataclass_field(default_factory=dict)
    checks: list[dict[str, Any]] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)

    @property
    def available_count(self) -> int:
        return sum(1 for row in self.rows if row.tradability_gate_status == "available")

    @property
    def blocked_count(self) -> int:
        return sum(1 for row in self.rows if row.tradability_gate_status == "blocked")

    @property
    def required_missing_count(self) -> int:
        return sum(1 for row in self.rows if row.tradability_gate_status == "required_missing")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "row_count": len(self.rows),
            "available_count": self.available_count,
            "blocked_count": self.blocked_count,
            "required_missing_count": self.required_missing_count,
            "reason_counts": dict(self.reason_counts),
            "rows": [row.to_dict() for row in self.rows],
            "checks": _json_safe(self.checks),
            "blocked_claims": _json_safe(self.blocked_claims),
            "known_limitations": _json_safe(self.known_limitations),
            "remediation_spec": _json_safe(self.remediation_spec),
        }


@dataclass(frozen=True, slots=True)
class ExecutionPolicyRequest:
    """CR011-S04 执行价 policy 请求。"""

    policy: str = "close_proxy"
    realism_mode: str = "production_strict"
    trade_intents: tuple[Mapping[str, Any], ...] = ()
    degradation_reason: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionPolicyResult:
    """CR011-S04 执行价解析结果。"""

    execution_price_policy: str
    status: str
    rows: tuple[dict[str, Any], ...] = ()
    checks: list[dict[str, Any]] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.rows))

    def to_metadata(self) -> dict[str, Any]:
        return metadata_to_dict(
            {
                "execution_price_policy": self.execution_price_policy,
                "execution_availability_status": self.status,
                **self.metadata,
                "blocked_claims": self.blocked_claims,
                "known_limitations": self.known_limitations,
            }
        )


@dataclass(frozen=True, slots=True)
class AdjustmentAuditResult:
    """CR011-S05 adjustment / corporate action audit gate 结果。"""

    adjustment_policy: str
    adj_factor_lineage: dict[str, Any]
    corporate_action_status: str
    adjustment_audit_status: str
    mixed_adjustment_policy_count: int = 0
    checks: list[dict[str, Any]] = dataclass_field(default_factory=list)
    issues: list[ResearchDatasetIssue] = dataclass_field(default_factory=list)
    allowed_claims: list[str] = dataclass_field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    known_limitations: list[Any] = dataclass_field(default_factory=list)
    remediation_spec: dict[str, Any] = dataclass_field(default_factory=dict)
    factor_calculation_entry_count: int = 0

    @property
    def passed(self) -> bool:
        return self.adjustment_audit_status == "pass"

    def to_metadata(self) -> dict[str, Any]:
        return metadata_to_dict(
            {
                "adjustment_policy": self.adjustment_policy,
                "adj_factor_lineage": self.adj_factor_lineage,
                "corporate_action_status": self.corporate_action_status,
                "corporate_action_missing_reason": _adjustment_audit_missing_reason(self),
                "adjustment_audit_status": self.adjustment_audit_status,
                "lineage_raw_checksum": self.adj_factor_lineage.get("lineage_raw_checksum"),
                "mixed_adjustment_policy_count": int(self.mixed_adjustment_policy_count),
                "factor_calculation_entry_count": int(self.factor_calculation_entry_count),
                "allowed_claims": self.allowed_claims,
                "blocked_claims": self.blocked_claims,
                "known_limitations": self.known_limitations,
                "remediation_spec": self.remediation_spec,
            }
        )


@dataclass(frozen=True, slots=True)
class ResearchInputMetadataIssue:
    """research_input_v1 校验问题。"""

    code: str
    field: str
    message: str
    severity: str = "ERROR"


class ResearchInputMetadataError(ValueError):
    """metadata 缺失或违反合同，阻止报告生成。"""

    def __init__(self, issues: list[ResearchInputMetadataIssue] | tuple[ResearchInputMetadataIssue, ...]):
        self.issues = tuple(issues)
        details = "; ".join(f"{issue.code}:{issue.field}:{issue.message}" for issue in self.issues)
        super().__init__(details or "research_input_v1 metadata validation failed")


@dataclass(frozen=True, slots=True)
class ResearchInputMetadata:
    """CR008 后新研究报告必须携带的 research_input_v1 metadata。"""

    schema_name: str
    report_kind: str
    lineage: dict[str, Any]
    coverage_start: str
    coverage_end: str
    benchmark: dict[str, Any]
    universe: dict[str, Any]
    adjustment_policy: str
    label_window: dict[str, Any]
    quality: dict[str, Any]
    known_limitations: list[Any]
    allowed_claims: list[str]
    legacy_report_policy: str = LEGACY_REPORT_POLICY
    blocked_claims: list[dict[str, Any]] = dataclass_field(default_factory=list)
    auxiliary_availability: dict[str, Any] = dataclass_field(default_factory=dict)


CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS = {
    **dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
    "old_report_read": 0,
    "candidate_lake_scan": 0,
    "duckdb_open": 0,
    "duckdb_sql_view": 0,
    "docs_write": 0,
}

CR017_CONSUMER_TYPES = ("chart", "long_horizon_research", "factor_research", "qmt_order_intent")
CR017_EXECUTION_RAW_POLICY = "raw"
CR017_NON_RAW_EXECUTION_POLICIES = ("qfq", "hfq", "returns_adjusted")
CR017_UNSUPPORTED_EXECUTION_FEATURES = (
    "real_vwap_execution",
    "minute_execution",
    "tick_execution",
    "level2_execution",
    "order_match_execution",
    "microstructure_impact_cost",
)
CR017_CONSUMER_FORBIDDEN_COUNTERS = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "real_order_call": 0,
    "real_cancel_call": 0,
    "account_query_call": 0,
    "dependency_change": 0,
    "legacy_qfq_overwrite": 0,
    "non_raw_execution_allowed": 0,
    "production_adjustment_governance_claim_allowed": 0,
    "scale_up_allowed": 0,
}

CR018_P1_FIELD_REQUIREMENTS_BY_CLAIM: dict[str, tuple[str, ...]] = {
    CLAIM_INDUSTRY_NEUTRALIZED: ("industry",),
    CLAIM_MARKET_CAP_NEUTRALIZED: ("market_cap", "float_market_cap"),
    CLAIM_PURE_ALPHA: ("industry", "market_cap", "float_market_cap", "beta_style"),
    CLAIM_CAPACITY_TRADABLE: ("float_market_cap", "adv", "turnover", "liquidity", "capacity", "impact_cost"),
    CLAIM_SCALE_UP_READY: ("adv", "turnover", "liquidity", "capacity", "impact_cost"),
    CLAIM_CAPITAL_AMPLIFICATION: ("liquidity", "capacity", "impact_cost"),
}
CR018_P1_CLAIM_ALLOWED_COUNT_FIELDS: dict[str, str] = {
    CLAIM_INDUSTRY_NEUTRALIZED: "industry_neutral_allowed_count",
    CLAIM_MARKET_CAP_NEUTRALIZED: "market_cap_neutral_allowed_count",
    CLAIM_PURE_ALPHA: "pure_alpha_allowed_count",
    CLAIM_CAPACITY_TRADABLE: "capacity_allowed_count",
    CLAIM_SCALE_UP_READY: "scale_up_allowed_count",
    CLAIM_CAPITAL_AMPLIFICATION: "capital_amplification_allowed_count",
}
CR018_P1_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    **{key: 0 for key in FORBIDDEN_OPERATION_COUNTER_KEYS},
    "unpublished_lake_scan": 0,
}
CR018_S08_PRODUCTION_CURRENT_TRUTH_SCHEMA = "cr018_production_current_truth_dataset_v1"
CR018_S08_STATUS_PASS = "pass"
CR018_S08_STATUS_BLOCKED = "blocked"
CR018_S08_REASON_CATALOG_NOT_PUBLISHED = "catalog_not_published"
CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN = "candidate_input_forbidden"
CR018_S08_REASON_PROXY_INPUT_FORBIDDEN = "proxy_input_forbidden"
CR018_S08_REASON_REQUIRED_MISSING = "required_missing"
CR018_S08_REASON_PROVIDER_FETCH_FORBIDDEN = "provider_fetch_forbidden"
CR018_S08_REASON_LAKE_WRITE_FORBIDDEN = "lake_write_forbidden"
CR018_S08_REASON_CREDENTIAL_READ_FORBIDDEN = "credential_read_forbidden"
CR018_S08_REASON_QMT_OPERATION_FORBIDDEN = "qmt_operation_forbidden"
CR018_S08_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN = "old_report_overwrite_forbidden"
CR018_S08_REASON_DUCKDB_DEPENDENCY_CHANGE_FORBIDDEN = "duckdb_dependency_change_forbidden"
CR018_S08_OPERATION_COUNTERS: dict[str, int] = {
    "old_report_overwrite": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "qmt_operation": 0,
    "candidate_read_count": 0,
    "proxy_input_allowed_count": 0,
    "duckdb_dependency_change": 0,
}


@dataclass(frozen=True, slots=True)
class ResearchConsumerRequest:
    """CR014-S07 研究消费只读请求。"""

    universe_scope: str
    as_of_trade_date: str
    realism_mode: str = "production_strict"
    requested_claims: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "universe_scope", str(self.universe_scope or "").strip())
        object.__setattr__(self, "as_of_trade_date", str(self.as_of_trade_date or "").strip())
        object.__setattr__(self, "realism_mode", str(self.realism_mode or "production_strict").strip())
        object.__setattr__(
            self,
            "requested_claims",
            tuple(str(item) for item in self.requested_claims if str(item)),
        )


@dataclass(frozen=True, slots=True)
class DuckDbEvidenceRef:
    """S04 DuckDB audit/parity 证据引用，不是事实源。"""

    run_id: str
    evidence_path: str
    parity_status: str
    audit_scope: str

    def to_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "evidence_path": self.evidence_path,
            "parity_status": self.parity_status,
            "audit_scope": self.audit_scope,
        }


@dataclass(frozen=True, slots=True)
class ResearchConsumerBoundaryCheck:
    """CR014-S07 forbidden operation 自检结果。"""

    passed: bool
    counters: dict[str, int]
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counters": dict(self.counters),
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ConsumerGuidance:
    """CR017-S06 研究 / QMT consumer policy 指引。"""

    consumer_type: str
    recommended_policy: str
    allowed_policies: tuple[str, ...]
    blocked_policies: tuple[str, ...]
    purpose: str
    execution_price_policy: str = ""
    allowed_claims: tuple[str, ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    non_raw_execution_allowed_count: int = 0
    adjusted_execution_price_pass_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "consumer_type": self.consumer_type,
            "recommended_policy": self.recommended_policy,
            "allowed_policies": list(self.allowed_policies),
            "blocked_policies": list(self.blocked_policies),
            "purpose": self.purpose,
            "execution_price_policy": self.execution_price_policy,
            "allowed_claims": list(self.allowed_claims),
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "non_raw_execution_allowed_count": int(self.non_raw_execution_allowed_count),
            "adjusted_execution_price_pass_count": int(self.adjusted_execution_price_pass_count),
        }


@dataclass(frozen=True, slots=True)
class AdjustmentGovernanceStatus:
    """CR017-S06 production governance / scale-up blocked claim 输出。"""

    cr017_status: str
    stage: str
    cr017_verified: bool
    adjustment_governance_status: str
    allowed_claims: tuple[str, ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    production_adjustment_governance_claim_allowed_count: int = 0
    scale_up_allowed_count: int = 0
    release_conditions: tuple[str, ...] = ()
    operation_counts: dict[str, int] = dataclass_field(default_factory=lambda: dict(CR017_CONSUMER_FORBIDDEN_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return metadata_to_dict(
            {
                "cr017_status": self.cr017_status,
                "stage": self.stage,
                "cr017_verified": self.cr017_verified,
                "adjustment_governance_status": self.adjustment_governance_status,
                "allowed_claims": list(self.allowed_claims),
                "blocked_claims": [dict(item) for item in self.blocked_claims],
                "production_adjustment_governance_claim_allowed_count": int(
                    self.production_adjustment_governance_claim_allowed_count
                ),
                "scale_up_allowed_count": int(self.scale_up_allowed_count),
                "release_conditions": list(self.release_conditions),
                "operation_counts": dict(self.operation_counts),
            }
        )


def build_research_dataset_from_published_truth(
    request: ResearchConsumerRequest | Mapping[str, Any],
    *,
    published_current_truth: Mapping[str, Any] | Any | None = None,
    clean_reader_output: Mapping[str, Any] | Any | None = None,
    claim_boundary_summary: Mapping[str, Any] | Any | None = None,
    duckdb_evidence_refs: Sequence[Mapping[str, Any] | DuckDbEvidenceRef] = (),
    permission_counters: Mapping[str, Any] | None = None,
) -> ResearchDataset:
    """只消费 published current truth / clean reader output 与结构化 claim boundary。

    缺少 published current truth、claim boundary 或出现 candidate / direct DuckDB
    输入时返回 typed `required_missing` / `blocked_claims`，不触发 reader、
    provider、backfill、lake write、credential read、旧 data/report 或 DuckDB 操作。
    """

    req = _coerce_research_consumer_request(request)
    counters = _cr014_research_consumer_counters(permission_counters)
    truth_payload = _coerce_published_truth_payload(published_current_truth, clean_reader_output)
    claim_payload = _coerce_claim_boundary_payload(claim_boundary_summary)
    evidence_refs = [consume_duckdb_audit_evidence_ref(ref) for ref in duckdb_evidence_refs]

    issues: list[ResearchDatasetIssue] = []
    blocked_claims = [dict(item) for item in claim_payload.get("blocked_claims") or [] if isinstance(item, Mapping)]
    required_missing = [
        dict(item)
        for item in claim_payload.get("required_missing") or []
        if isinstance(item, Mapping)
    ]
    known_limitations = list(claim_payload.get("known_limitations") or [])

    truth_status = _published_truth_status(truth_payload)
    if truth_status != "published_current_truth":
        issue_code = "candidate_lake_scan_attempt" if truth_status == "candidate_unpublished" else "published_current_truth_missing"
        issue = ResearchDatasetIssue(
            code=issue_code,
            dataset="published_current_truth",
            message="CR014-S07 research consumer 只能消费已发布 current truth。",
            details={"truth_status": truth_status},
        )
        issues.append(issue)
        row = _cr014_required_missing_row(
            dataset="published_current_truth",
            gap_code=issue_code,
            evidence_path=str(truth_payload.get("evidence_path") or "catalog_current_truth://missing"),
            remediation="provide_published_catalog_current_pointer_or_clean_reader_output",
            release_condition="published current truth pointer exists and candidate paths are not supplied",
            claim=CR014_CLAIM_FULL_A_SINCE_INCEPTION,
        )
        required_missing.append({key: row[key] for key in ("dataset", "gap_code", "evidence_path", "remediation", "release_condition")})
        blocked_claims.append(row)

    if not claim_payload:
        issue = ResearchDatasetIssue(
            code="claim_boundary_missing",
            dataset="claim_boundary",
            message="缺少 S05/S08 结构化 claim boundary，研究消费层必须 fail closed。",
        )
        issues.append(issue)
        row = _cr014_required_missing_row(
            dataset="claim_boundary",
            gap_code="claim_boundary_missing",
            evidence_path="claim_boundary://missing",
            remediation="provide_verified_s05_s08_claim_boundary_summary",
            release_condition="CR014-S05 and CR014-S08 CP7 pass before S07 consumption",
        )
        required_missing.append({key: row[key] for key in ("dataset", "gap_code", "evidence_path", "remediation", "release_condition")})
        blocked_claims.append(row)

    non_zero_counters = [key for key, value in counters.items() if int(value) != 0]
    if non_zero_counters:
        issues.append(
            ResearchDatasetIssue(
                code="research_consumer_forbidden_operation_counter_nonzero",
                dataset="permission",
                message="CR014-S07 forbidden operation counter 必须全部为 0。",
                details={"non_zero_counters": non_zero_counters},
            )
        )
        row = _cr014_required_missing_row(
            dataset="permission",
            gap_code="research_consumer_forbidden_operation_counter_nonzero",
            evidence_path="permission_counters://cr014-s07",
            remediation="reset_forbidden_operation_counters_and_rerun_offline",
            release_condition="provider/lake/credential/legacy/report/DuckDB/publish/S09/docs counters are all 0",
        )
        required_missing.append({key: row[key] for key in ("dataset", "gap_code", "evidence_path", "remediation", "release_condition")})
        blocked_claims.append(row)

    for evidence in evidence_refs:
        if set(evidence) != {"run_id", "evidence_path", "parity_status", "audit_scope"}:
            issues.append(
                ResearchDatasetIssue(
                    code=str(evidence.get("error_code") or "duckdb_evidence_ref_invalid"),
                    dataset="duckdb_evidence",
                    message="DuckDB evidence 在研究消费层只能作为 run_id/evidence_path/parity_status/audit_scope 引用。",
                    details=evidence,
                )
            )

    blocked_names = _blocked_claim_names(blocked_claims)
    allowed_claims = [
        claim
        for claim in _claim_names(claim_payload.get("allowed_claims") or [])
        if claim not in blocked_names
    ]
    if issues:
        allowed_claims = []

    status = ResearchDatasetStatus.AVAILABLE.value if not issues else ResearchDatasetStatus.REQUIRED_MISSING.value
    gate_status = GateStatus.PASS.value if not issues else GateStatus.FAIL.value
    metadata = metadata_to_dict(
        {
            "schema_name": "cr014_research_consumer_boundary_v1",
            "consumer_gate": "cr014_s07_research_consumer_readonly",
            "consumer_gate_status": status,
            "universe_scope": req.universe_scope,
            "as_of_trade_date": req.as_of_trade_date,
            "realism_mode": req.realism_mode,
            "truth_source": truth_status,
            "published_current_truth_ref": truth_payload if truth_status == "published_current_truth" else {},
            "claim_boundary_summary": claim_payload,
            "allowed_claims": allowed_claims,
            "blocked_claims": blocked_claims,
            "required_missing": _dedupe_json_safe(required_missing),
            "duckdb_evidence_refs": [
                evidence
                for evidence in evidence_refs
                if set(evidence) == {"run_id", "evidence_path", "parity_status", "audit_scope"}
            ],
            "duckdb_evidence_policy": "reference_only",
            "permission_counters": counters,
            "forbidden_operations": counters,
            "provider_fetches": 0,
            "lake_writes": 0,
            "credential_reads": 0,
            "legacy_data_operations": 0,
            "old_report_reads": 0,
            "old_report_overwrites": 0,
            "candidate_lake_scans": 0,
            "duckdb_opens": 0,
            "duckdb_sql_views": 0,
            "docs_writes": 0,
        }
    )
    checks = [
        _gate_check(
            "cr014_research_consumer_readonly",
            "pass" if not issues else "fail",
            status,
            "INFO" if not issues else "ERROR",
            "S07 research consumer gate 只消费 published current truth / clean reader output 和结构化 claim boundary。",
            {
                "truth_source": truth_status,
                "required_missing_count": len(required_missing),
                "blocked_claim_count": len(blocked_claims),
                "permission_counters": counters,
            },
        )
    ]
    return ResearchDataset(
        status=status,
        prices=_extract_clean_frame(truth_payload, clean_reader_output),
        close_df=None,
        calendar=[],
        universe_symbols=[],
        benchmark_result=None,
        metadata=metadata,
        gate_result=GateResult(status=gate_status, issues=issues, checks=checks, remediation_spec=_cr014_research_remediation(status)),
        issues=issues,
        known_limitations=_dedupe_json_safe(known_limitations),
        allowed_claims=allowed_claims,
        blocked_claims=_dedupe_claim_payloads(blocked_claims),
        remediation_spec=_cr014_research_remediation(status),
        reader_results={},
    )


def consume_duckdb_audit_evidence_ref(evidence_ref: DuckDbEvidenceRef | Mapping[str, Any]) -> dict[str, str]:
    """把 DuckDB audit/parity 产物压缩成只读 evidence 引用。"""

    payload = evidence_ref.to_dict() if isinstance(evidence_ref, DuckDbEvidenceRef) else dict(evidence_ref)
    forbidden_keys = {
        "sql",
        "query",
        "connection",
        "connection_string",
        "view",
        "view_name",
        "duckdb_path",
        "candidate_path",
        "lake_path",
    }
    present_forbidden = sorted(key for key in forbidden_keys if payload.get(key))
    required = ("run_id", "evidence_path", "parity_status", "audit_scope")
    missing = [key for key in required if not payload.get(key)]
    if present_forbidden:
        return {
            "error_code": "direct_duckdb_access_attempt",
            "blocked_fields": ",".join(present_forbidden),
            "allowed_fields": ",".join(required),
        }
    if missing:
        return {
            "error_code": "duckdb_evidence_ref_missing_field",
            "missing_fields": ",".join(missing),
            "allowed_fields": ",".join(required),
        }
    return {key: str(payload[key]) for key in required}


def assert_research_consumer_forbidden_operations(
    counters: Mapping[str, Any] | None = None,
    *,
    touched_files: Sequence[str] = (),
    duckdb_evidence_refs: Sequence[Mapping[str, Any] | DuckDbEvidenceRef] = (),
) -> ResearchConsumerBoundaryCheck:
    """断言 S07 没有 provider/lake/credential/legacy/report/DuckDB/publish/S09/docs 副作用。"""

    normalised = _cr014_research_consumer_counters(counters)
    errors = [f"{key}_nonzero" for key, value in normalised.items() if int(value) != 0]
    details: list[dict[str, Any]] = []
    forbidden_touched = [
        path
        for path in touched_files
        if path.startswith(("README", "docs/", "data/", "reports/"))
        or path in {"pyproject.toml", "uv.lock", ".env"}
    ]
    if forbidden_touched:
        errors.append("forbidden_file_touched")
        details.append({"forbidden_touched": forbidden_touched})
    invalid_evidence = []
    for ref in duckdb_evidence_refs:
        evidence = consume_duckdb_audit_evidence_ref(ref)
        if set(evidence) != {"run_id", "evidence_path", "parity_status", "audit_scope"}:
            invalid_evidence.append(evidence)
    if invalid_evidence:
        errors.append("duckdb_evidence_ref_invalid")
        details.append({"invalid_evidence_refs": invalid_evidence})
    unique_errors = tuple(dict.fromkeys(errors))
    return ResearchConsumerBoundaryCheck(
        passed=not unique_errors,
        counters=normalised,
        error_codes=unique_errors,
        details=tuple(details),
    )


def build_cr018_p1_claim_boundary(
    p1_availability_metadata: Mapping[str, Any] | None,
    *,
    core_readiness: Mapping[str, Any] | None = None,
    requested_claims: Sequence[str] | None = None,
    permission_counters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """把 CR018 P1 availability metadata 映射为 claim boundary。

    P1 缺失只阻断行业 / 市值 / pure alpha / capacity / scale_up / 资金放大
    声明；不改变 P0 core current truth readiness 的默认语义。
    """

    fields = _cr018_p1_fields(p1_availability_metadata)
    requested = _ordered_unique(list(requested_claims or P1_BLOCKED_CLAIMS))
    core = dict(core_readiness or {})
    allowed_claims = _cr018_claim_names(core.get("allowed_claims") or [])
    blocked_claims = [
        dict(item)
        for item in core.get("blocked_claims") or []
        if isinstance(item, Mapping)
    ]
    p1_blocked_names: set[str] = set()
    for claim in requested:
        missing_field = _cr018_missing_field_for_claim(claim, fields)
        if missing_field:
            blocked_claims.append(_cr018_p1_blocked_claim(claim, missing_field, fields.get(missing_field, {})))
            p1_blocked_names.add(claim)
            continue
        allowed_claims.append(claim)

    allowed_claims = [claim for claim in _ordered_unique(allowed_claims) if claim not in p1_blocked_names]
    claim_allowed_counts = {
        count_field: 1 if claim in allowed_claims else 0
        for claim, count_field in CR018_P1_CLAIM_ALLOWED_COUNT_FIELDS.items()
    }
    counters = _cr018_p1_operation_counters(permission_counters, p1_availability_metadata)
    p0_release_blocked = bool(core.get("release_blocked", False))
    publish_readiness_pass = bool(core.get("publish_readiness_pass", not p0_release_blocked))
    return metadata_to_dict(
        {
            "schema_name": "cr018_p1_claim_boundary_v1",
            "core_readiness": {
                "release_blocked": p0_release_blocked,
                "publish_readiness_pass": publish_readiness_pass,
                "source": core.get("source", "explicit_core_readiness"),
            },
            "p0_core_readiness_blocked": p0_release_blocked,
            "core_release_blocked_by_p1": False,
            "p1_blocks_core_release": False,
            "p1_availability": dict(p1_availability_metadata or {}),
            "allowed_claims": allowed_claims,
            "blocked_claims": _dedupe_claim_payloads(blocked_claims),
            "p1_blocked_claims": [claim for claim in requested if claim in p1_blocked_names],
            "claim_allowed_counts": claim_allowed_counts,
            **claim_allowed_counts,
            "operation_counts": counters,
            "permission_counters": counters,
            "provider_fetch": counters.get("provider_fetch", 0),
            "lake_write": counters.get("lake_write", 0),
            "credential_read": counters.get("credential_read", 0),
            "current_pointer_publish": counters.get("current_pointer_publish", 0),
            "qmt_operation": counters.get("qmt_operation", 0),
            "unpublished_lake_scan_count": counters.get("unpublished_lake_scan", 0),
        }
    )


def _cr018_p1_fields(p1_availability_metadata: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    raw = dict(p1_availability_metadata or {})
    fields = raw.get("fields") if isinstance(raw.get("fields"), Mapping) else raw
    return {
        str(field_id): dict(payload)
        for field_id, payload in dict(fields or {}).items()
        if isinstance(payload, Mapping)
    }


def _cr018_claim_names(value: Sequence[Any]) -> list[str]:
    names: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            claim = item.get("claim")
        else:
            claim = item
        if claim:
            names.append(str(claim))
    return _ordered_unique(names)


def _cr018_missing_field_for_claim(claim: str, fields: Mapping[str, Mapping[str, Any]]) -> str:
    for field_id in CR018_P1_FIELD_REQUIREMENTS_BY_CLAIM.get(str(claim), ()):
        payload = fields.get(field_id, {})
        if not bool(payload.get("available", False)):
            return field_id
    return ""


def _cr018_p1_blocked_claim(claim: str, field_id: str, field_payload: Mapping[str, Any]) -> dict[str, Any]:
    reason = str(field_payload.get("missing_reason") or f"{REASON_P1_AUXILIARY_MISSING}:{field_id}")
    return {
        "claim": str(claim),
        "field_id": str(field_id),
        "dataset_id": str(field_payload.get("dataset_id") or field_id),
        "reason_code": REASON_P1_AUXILIARY_MISSING,
        "reason": reason,
        "status": "blocked",
        "severity": "BLOCKING",
        "source_story": "CR018-S04",
        "release_condition": "publish explicit P1 auxiliary dataset metadata and repeat CP5/CP6/CP7 gates before allowing this claim",
        "evidence_ref": str(field_payload.get("evidence_ref") or "explicit_metadata://cr018-p1-missing"),
    }


def _cr018_p1_operation_counters(
    permission_counters: Mapping[str, Any] | None,
    p1_availability_metadata: Mapping[str, Any] | None,
) -> dict[str, int]:
    counters = dict(CR018_P1_FORBIDDEN_OPERATION_COUNTERS)
    counters.update(normalise_permission_counters(permission_counters))
    metadata_counters = {}
    if isinstance(p1_availability_metadata, Mapping):
        metadata_counters = dict(p1_availability_metadata.get("permission_counters") or {})
    for key, value in metadata_counters.items():
        try:
            counters[str(key)] = int(value)
        except (TypeError, ValueError):
            counters[str(key)] = 1
    counters["unpublished_lake_scan"] = int(counters.get("unpublished_lake_scan") or 0)
    return counters


def load_production_current_truth_dataset(
    release_id: str,
    *,
    release_metadata: Mapping[str, Any] | Any | None = None,
    current_truth_metadata: Mapping[str, Any] | Any | None = None,
    current_reader_result: CurrentReaderSmokeResult | Mapping[str, Any] | Any | None = None,
    current_reader_metadata: Mapping[str, Any] | Any | None = None,
    p0_dataset_ids: Sequence[str] | None = None,
    current_pointers: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    candidate_path: str | Path | None = None,
    candidate_pointers: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    proxy_input: Mapping[str, Any] | Sequence[Any] | str | None = None,
    provider_raw_fallback: bool = False,
    required_missing: Sequence[Mapping[str, Any] | str] | None = None,
    permission_counters: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """加载 S08 production current truth dry-run bundle。

    该 loader 只消费 S07 published current reader 结果或显式 current truth
    metadata。candidate、proxy、provider raw fallback、真实 lake 写入、凭据读取
    和 QMT 操作都在合同层 fail closed，不读取任何外部路径。
    """

    normalized_release_id = str(release_id or "").strip()
    release_payload = _plain_payload(release_metadata)
    truth_payload = _plain_payload(current_truth_metadata)
    reader_payload = _cr018_s08_current_reader_payload(
        normalized_release_id,
        current_reader_result=current_reader_result,
        current_reader_metadata=current_reader_metadata,
        current_pointers=current_pointers,
        p0_dataset_ids=p0_dataset_ids,
    )
    counters = _cr018_s08_operation_counters(permission_counters, reader_payload)
    blocked_reasons: list[dict[str, Any]] = []

    if not normalized_release_id:
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                "release_id_missing",
                "release_id",
                "production rerun 必须显式绑定 published release_id。",
            )
        )

    if (
        candidate_path
        or candidate_pointers
        or _cr018_s08_payload_has_candidate(release_payload)
        or _cr018_s08_payload_has_candidate(truth_payload)
        or _cr018_s08_payload_has_candidate(reader_payload)
    ):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN,
                "candidate",
                "production current truth loader 不允许 candidate path / pointer / metadata 作为输入。",
            )
        )

    if proxy_input is not None or _cr018_s08_payload_has_proxy(release_payload) or _cr018_s08_payload_has_proxy(truth_payload):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_PROXY_INPUT_FORBIDDEN,
                "proxy",
                "production rerun 不允许 proxy baseline 作为 production input。",
            )
        )

    if (
        provider_raw_fallback
        or _cr018_s08_payload_has_provider_raw(release_payload)
        or _cr018_s08_payload_has_provider_raw(truth_payload)
        or _cr018_s08_payload_has_provider_raw(reader_payload)
    ):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_PROVIDER_FETCH_FORBIDDEN,
                "provider_raw_fallback",
                "provider/raw fallback 在 S08 fixture-only rerun 中被禁止。",
            )
        )

    if _cr018_s08_payload_explicit_unpublished(release_payload, truth_payload) or not _cr018_s08_is_published_release(
        normalized_release_id,
        release_payload,
        truth_payload,
    ):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
                "release_metadata",
                "release 必须已 published，且 catalog current pointer 已发布后才能进入 production rerun。",
            )
        )

    if not _cr018_s08_current_reader_is_published_only(reader_payload):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
                "current_reader",
                "production current truth loader 必须消费 S07 published current pointer reader metadata。",
            )
        )

    required_missing_items = _cr018_s08_required_missing_items(
        required_missing,
        release_payload,
        truth_payload,
        reader_payload,
    )
    if required_missing_items:
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                CR018_S08_REASON_REQUIRED_MISSING,
                "required_missing",
                "P0 required_missing 存在时 production rerun 必须 blocked。",
                {"required_missing": required_missing_items},
            )
        )

    for reason_code in _cr018_s08_counter_reason_codes(counters):
        blocked_reasons.append(
            _cr018_s08_blocked_reason(
                reason_code,
                "operation_counts",
                "S08 受控离线合同要求真实操作和 forbidden input 计数全部为 0。",
                {"operation_counts": counters},
            )
        )

    deduped_blocked = _dedupe_claim_payloads(blocked_reasons)
    status = CR018_S08_STATUS_PASS if not deduped_blocked else CR018_S08_STATUS_BLOCKED
    release_scope = _cr018_s08_first_mapping(
        "release_scope",
        "scope",
        "dataset_scope",
        payloads=(truth_payload, release_payload),
    )
    benchmark = _cr018_s08_first_mapping(
        "benchmark",
        "benchmark_policy",
        "benchmark_readiness",
        payloads=(truth_payload, release_payload),
    )
    pit_universe = _cr018_s08_first_mapping(
        "pit_universe",
        "pit",
        "pit_readiness",
        payloads=(truth_payload, release_payload),
    )
    tradability = _cr018_s08_first_mapping(
        "tradability",
        "tradability_readiness",
        payloads=(truth_payload, release_payload),
    )
    adjustment_policy = _cr018_s08_first_value(
        "adjustment_policy",
        "research_adjustment_policy",
        payloads=(truth_payload, release_payload),
        default="",
    )
    blocked_claims = _dedupe_claim_payloads(
        [
            *list(truth_payload.get("blocked_claims") or []),
            *list(release_payload.get("blocked_claims") or []),
            *deduped_blocked,
        ]
    )

    return metadata_to_dict(
        {
            "schema_name": CR018_S08_PRODUCTION_CURRENT_TRUTH_SCHEMA,
            "status": status,
            "allowed": status == CR018_S08_STATUS_PASS,
            "allowed_count": 1 if status == CR018_S08_STATUS_PASS else 0,
            "release_id": normalized_release_id,
            "release_metadata": release_payload,
            "current_truth_metadata": truth_payload,
            "current_reader_metadata": reader_payload,
            "read_source": "published_current_pointer",
            "published_current_pointer_only": True,
            "candidate_fallback_allowed": False,
            "proxy_input_allowed": False,
            "provider_raw_fallback_allowed": False,
            "release_scope": release_scope,
            "as_of_trade_date": _cr018_s08_first_value(
                "as_of_trade_date",
                "coverage_end",
                "latest_closed_trade_date",
                payloads=(truth_payload, release_payload),
                default="",
            ),
            "benchmark": benchmark,
            "pit_universe": pit_universe,
            "tradability": tradability,
            "adjustment_policy": adjustment_policy,
            "required_missing": required_missing_items,
            "blocked_claims": blocked_claims,
            "blocked_reasons": deduped_blocked,
            "operation_counts": counters,
            **counters,
        }
    )


def _cr018_s08_current_reader_payload(
    release_id: str,
    *,
    current_reader_result: CurrentReaderSmokeResult | Mapping[str, Any] | Any | None,
    current_reader_metadata: Mapping[str, Any] | Any | None,
    current_pointers: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    p0_dataset_ids: Sequence[str] | None,
) -> dict[str, Any]:
    if current_reader_result is not None:
        if hasattr(current_reader_result, "to_dict"):
            return dict(current_reader_result.to_dict())
        return _plain_payload(current_reader_result)
    if current_reader_metadata is not None:
        payload = _plain_payload(current_reader_metadata)
        if "policy_metadata" not in payload:
            payload = {
                "status": payload.get("status", payload.get("reader_status", "")),
                "policy_metadata": payload,
                **payload,
            }
        return payload
    if current_pointers is not None:
        return current_reader_smoke(
            release_id,
            p0_dataset_ids=p0_dataset_ids,
            current_pointers=current_pointers,
        ).to_dict()
    return {}


def _cr018_s08_operation_counters(
    permission_counters: Mapping[str, Any] | None,
    current_reader_payload: Mapping[str, Any] | None,
) -> dict[str, int]:
    counters = dict(CR018_S08_OPERATION_COUNTERS)
    for source in (permission_counters or {}, dict((current_reader_payload or {}).get("operation_counts") or {})):
        for key, value in source.items():
            normalized = str(key)
            if normalized in {"real_lake_write", "lake_writes"}:
                normalized = "lake_write"
            elif normalized in {"credential_reads"}:
                normalized = "credential_read"
            elif normalized in {"provider_fetches"}:
                normalized = "provider_fetch"
            elif normalized in {"old_report_overwrites"}:
                normalized = "old_report_overwrite"
            elif normalized in {"dependency_change"}:
                normalized = "duckdb_dependency_change"
            if normalized in counters:
                counters[normalized] = _safe_int(value)
    reader = dict(current_reader_payload or {})
    counters["candidate_read_count"] = max(
        counters["candidate_read_count"],
        _safe_int(reader.get("candidate_read_count")),
    )
    counters["proxy_input_allowed_count"] = max(
        counters["proxy_input_allowed_count"],
        _safe_int(reader.get("proxy_input_allowed_count")),
    )
    return counters


def _cr018_s08_counter_reason_codes(counters: Mapping[str, int]) -> list[str]:
    reason_by_counter = {
        "old_report_overwrite": CR018_S08_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN,
        "provider_fetch": CR018_S08_REASON_PROVIDER_FETCH_FORBIDDEN,
        "lake_write": CR018_S08_REASON_LAKE_WRITE_FORBIDDEN,
        "credential_read": CR018_S08_REASON_CREDENTIAL_READ_FORBIDDEN,
        "qmt_operation": CR018_S08_REASON_QMT_OPERATION_FORBIDDEN,
        "candidate_read_count": CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN,
        "proxy_input_allowed_count": CR018_S08_REASON_PROXY_INPUT_FORBIDDEN,
        "duckdb_dependency_change": CR018_S08_REASON_DUCKDB_DEPENDENCY_CHANGE_FORBIDDEN,
    }
    return [
        reason
        for key, reason in reason_by_counter.items()
        if _safe_int(counters.get(key)) != 0
    ]


def _cr018_s08_is_published_release(
    release_id: str,
    release_payload: Mapping[str, Any],
    truth_payload: Mapping[str, Any],
) -> bool:
    for payload in (truth_payload, release_payload):
        if not payload:
            continue
        payload_release_id = str(payload.get("release_id") or payload.get("id") or release_id).strip()
        if payload_release_id and release_id and payload_release_id != release_id:
            continue
        status = str(
            payload.get("status")
            or payload.get("release_status")
            or payload.get("truth_status")
            or ""
        ).strip().lower()
        if bool(payload.get("published")) or status in {"published", "published_current_truth", "pass"}:
            return True
    return False


def _cr018_s08_payload_explicit_unpublished(*payloads: Mapping[str, Any]) -> bool:
    for payload in payloads:
        if not isinstance(payload, Mapping) or not payload:
            continue
        if payload.get("published") is False:
            return True
        status = str(
            payload.get("status")
            or payload.get("release_status")
            or payload.get("truth_status")
            or ""
        ).strip().lower()
        if status in {"candidate_unpublished", "unpublished", "not_published", "catalog_not_published"}:
            return True
    return False


def _cr018_s08_current_reader_is_published_only(reader_payload: Mapping[str, Any]) -> bool:
    if not reader_payload:
        return False
    status = str(reader_payload.get("status") or "").strip().lower()
    policy = dict(reader_payload.get("policy_metadata") or {})
    read_source = str(policy.get("read_source") or reader_payload.get("read_source") or "").strip()
    return (
        status == "pass"
        and read_source == "published_current_pointer"
        and bool(policy.get("published_current_pointer_only", reader_payload.get("published_current_pointer_only", False)))
        and not bool(policy.get("candidate_fallback_allowed", reader_payload.get("candidate_fallback_allowed", True)))
    )


def _cr018_s08_required_missing_items(
    explicit_missing: Sequence[Mapping[str, Any] | str] | None,
    *payloads: Mapping[str, Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in explicit_missing or ():
        if isinstance(item, Mapping):
            items.append(dict(item))
        elif str(item).strip():
            items.append({"reason_code": CR018_S08_REASON_REQUIRED_MISSING, "field": str(item)})
    for payload in payloads:
        if not isinstance(payload, Mapping):
            continue
        for item in payload.get("required_missing") or ():
            if isinstance(item, Mapping):
                items.append(dict(item))
            elif str(item).strip():
                items.append({"reason_code": CR018_S08_REASON_REQUIRED_MISSING, "field": str(item)})
        if _safe_int(payload.get("p0_required_missing_count")) > 0:
            items.append(
                {
                    "reason_code": CR018_S08_REASON_REQUIRED_MISSING,
                    "field": "p0_required_missing_count",
                    "count": _safe_int(payload.get("p0_required_missing_count")),
                }
            )
        readiness_status = str(payload.get("readiness_status") or payload.get("p0_readiness_status") or "").lower()
        if readiness_status == CR018_S08_REASON_REQUIRED_MISSING:
            items.append(
                {
                    "reason_code": CR018_S08_REASON_REQUIRED_MISSING,
                    "field": "readiness_status",
                    "status": readiness_status,
                }
            )
    return _dedupe_claim_payloads(items)


def _cr018_s08_payload_has_candidate(value: Any) -> bool:
    return _cr018_s08_payload_has_marker(
        value,
        keys={"candidate_path", "candidate_paths", "candidate_pointer", "candidate_pointers", "candidate_ref"},
        text_markers=("candidate://", "fixture://candidate", "/candidate/", "candidate_unpublished"),
    )


def _cr018_s08_payload_has_proxy(value: Any) -> bool:
    return _cr018_s08_payload_has_marker(
        value,
        keys={"proxy_input", "proxy_baseline", "proxy_path", "proxy_ref"},
        text_markers=("proxy://", "proxy_baseline", "proxy_input", "benchmark_proxy"),
    )


def _cr018_s08_payload_has_provider_raw(value: Any) -> bool:
    return _cr018_s08_payload_has_marker(
        value,
        keys={"provider_raw_path", "provider_raw_fallback", "raw_provider_fallback", "provider_fetch"},
        text_markers=("provider_raw://", "raw_provider", "provider_fallback"),
    )


def _cr018_s08_payload_has_marker(
    value: Any,
    *,
    keys: set[str],
    text_markers: tuple[str, ...],
) -> bool:
    if isinstance(value, Mapping):
        for raw_key, raw_value in value.items():
            key = str(raw_key).strip().lower()
            if key in keys and bool(raw_value):
                return True
            if _cr018_s08_payload_has_marker(raw_value, keys=keys, text_markers=text_markers):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_cr018_s08_payload_has_marker(item, keys=keys, text_markers=text_markers) for item in value)
    if isinstance(value, (str, Path)):
        text = str(value).strip().lower()
        return any(marker in text for marker in text_markers)
    return False


def _cr018_s08_first_mapping(
    *keys: str,
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    for payload in payloads:
        for key in keys:
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, Mapping):
                return _json_safe(dict(value))
    return {}


def _cr018_s08_first_value(
    *keys: str,
    payloads: Sequence[Mapping[str, Any]],
    default: Any = "",
) -> Any:
    for payload in payloads:
        for key in keys:
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if value not in (None, "", [], {}):
                return _json_safe(value)
    return default


def _cr018_s08_blocked_reason(
    reason_code: str,
    field: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "reason_code": str(reason_code),
        "field": str(field),
        "status": CR018_S08_STATUS_BLOCKED,
        "message": str(message),
        "severity": "BLOCKING",
        "source_story": "CR018-S08",
        "details": _json_safe(dict(details or {})),
    }


def build_consumer_guidance_matrix() -> dict[str, dict[str, Any]]:
    """构建 CR017-S06 consumer guidance matrix，不执行任何外部操作。"""

    rows = (
        ConsumerGuidance(
            consumer_type="chart",
            recommended_policy="qfq",
            allowed_policies=("qfq", "raw"),
            blocked_policies=(),
            purpose="Price charts may display qfq when the chart labels the adjustment policy explicitly.",
            allowed_claims=("chart_qfq_display",),
        ),
        ConsumerGuidance(
            consumer_type="long_horizon_research",
            recommended_policy="hfq_or_returns_adjusted",
            allowed_policies=("hfq", "returns_adjusted", "qfq"),
            blocked_policies=("raw_execution_claim",),
            purpose="Long-horizon research should prefer hfq price continuity or returns_adjusted return series.",
            allowed_claims=("long_horizon_adjusted_research",),
        ),
        ConsumerGuidance(
            consumer_type="factor_research",
            recommended_policy="returns_adjusted",
            allowed_policies=("returns_adjusted", "qfq", "hfq"),
            blocked_policies=("mixed_policy_in_one_run",),
            purpose="Factor research should use returns_adjusted by default and keep one policy per run.",
            allowed_claims=("factor_research_adjustment_metadata",),
        ),
        ConsumerGuidance(
            consumer_type="qmt_order_intent",
            recommended_policy=CR017_EXECUTION_RAW_POLICY,
            allowed_policies=(CR017_EXECUTION_RAW_POLICY,),
            blocked_policies=CR017_NON_RAW_EXECUTION_POLICIES,
            purpose="QMT order intent may carry research metadata, but execution price must stay raw / broker reference.",
            execution_price_policy=CR017_EXECUTION_RAW_POLICY,
            blocked_claims=(
                {
                    "claim": "qmt_execution_non_raw_policy",
                    "reason_code": "execution_requires_raw",
                    "blocked_policies": list(CR017_NON_RAW_EXECUTION_POLICIES),
                    "release_condition": "No release inside CR017-S06; execution remains raw / broker reference only.",
                    "severity": "BLOCKING",
                },
            ),
            non_raw_execution_allowed_count=0,
            adjusted_execution_price_pass_count=0,
        ),
    )
    return {row.consumer_type: row.to_dict() for row in rows}


def build_adjustment_blocked_claims(
    cr017_status: str = "not_verified",
    stage: str = "research",
    *,
    allow_production_claim_after_verified: bool = False,
    allow_scale_up_after_verified: bool = False,
) -> dict[str, Any]:
    """构建 CR017 production governance / scale_up blocked claims。

    verified 只表示 CR017 证据可进入后续 gate；生产治理完成声明和 scale_up
    默认仍不自动放行，必须由后续 Story / CP gate 显式授权。
    """

    normalized_status = _normalize_cr017_status(cr017_status)
    normalized_stage = str(stage or "research").strip() or "research"
    verified = _cr017_status_verified(normalized_status)
    production_allowed = bool(verified and allow_production_claim_after_verified)
    scale_up_allowed = bool(verified and allow_scale_up_after_verified)
    blocked: list[dict[str, Any]] = []
    if not production_allowed:
        blocked.append(
            {
                "claim": "production_adjustment_governance",
                "reason_code": "cr017_not_verified" if not verified else "production_claim_requires_downstream_gate",
                "stage": normalized_stage,
                "release_condition": "CR017 S01-S06 CP7 PASS plus explicit downstream production governance gate.",
                "severity": "BLOCKING",
            }
        )
    if not scale_up_allowed:
        blocked.append(
            {
                "claim": "scale_up",
                "reason_code": "cr017_not_verified" if not verified else "scale_up_requires_cr016_gate",
                "stage": normalized_stage,
                "release_condition": "CR017 verified plus CR016 scale_up gate and explicit user authorization.",
                "severity": "BLOCKING",
            }
        )
    allowed = []
    if production_allowed:
        allowed.append("production_adjustment_governance")
    if scale_up_allowed:
        allowed.append("scale_up")

    status = "allowed_by_explicit_downstream_gate" if production_allowed or scale_up_allowed else "blocked_until_verified_and_gated"
    result = AdjustmentGovernanceStatus(
        cr017_status=normalized_status,
        stage=normalized_stage,
        cr017_verified=verified,
        adjustment_governance_status=status,
        allowed_claims=tuple(allowed),
        blocked_claims=tuple(blocked),
        production_adjustment_governance_claim_allowed_count=1 if production_allowed else 0,
        scale_up_allowed_count=1 if scale_up_allowed else 0,
        release_conditions=(
            "CR017-S06 is not itself CR017 verification.",
            "CR017未 verified 时 production adjustment governance claim allowed count 必须为 0。",
            "CR017未 verified 时 scale_up allowed count 必须为 0。",
            "真实 QMT、真实发单、撤单、账户查询、真实抓取、真实写湖和 publish 不在本 Story 授权范围内。",
        ),
        operation_counts=dict(CR017_CONSUMER_FORBIDDEN_COUNTERS),
    )
    return result.to_dict()


def research_dataset_policy_metadata(
    cr017_status: str = "not_verified",
    stage: str = "research",
    *,
    research_adjustment_policy: str = "qfq",
) -> dict[str, Any]:
    """输出 CR017-S06 consumer / governance metadata，供文档和后续 gate 消费。"""

    consumer_matrix = build_consumer_guidance_matrix()
    governance = build_adjustment_blocked_claims(cr017_status=cr017_status, stage=stage)
    qmt_guidance = consumer_matrix["qmt_order_intent"]
    blocked_claims = _dedupe_claim_payloads(
        [
            *list(governance.get("blocked_claims") or []),
            *list(qmt_guidance.get("blocked_claims") or []),
        ]
    )
    allowed_claims = [
        claim
        for claim in _ordered_unique(
            [
                "chart_qfq_display",
                "long_horizon_adjusted_research",
                "factor_research_adjustment_metadata",
                *list(governance.get("allowed_claims") or []),
            ]
        )
        if claim not in _blocked_claim_names(blocked_claims)
    ]
    return metadata_to_dict(
        {
            "schema_name": "cr017_research_qmt_consumer_boundary_v1",
            "research_adjustment_policy": str(research_adjustment_policy or "qfq"),
            "allowed_research_adjustment_policies": ["qfq", "hfq", "returns_adjusted"],
            "execution_price_policy": CR017_EXECUTION_RAW_POLICY,
            "qmt_execution_raw_only": True,
            "qmt_non_raw_execution_allowed_count": int(qmt_guidance["non_raw_execution_allowed_count"]),
            "adjusted_execution_price_pass_count": int(qmt_guidance["adjusted_execution_price_pass_count"]),
            "consumer_guidance_matrix": consumer_matrix,
            "adjustment_governance_status": governance["adjustment_governance_status"],
            "cr017_verified": governance["cr017_verified"],
            "production_adjustment_governance_claim_allowed_count": int(
                governance["production_adjustment_governance_claim_allowed_count"]
            ),
            "scale_up_allowed_count": int(governance["scale_up_allowed_count"]),
            "allowed_claims": allowed_claims,
            "blocked_claims": blocked_claims,
            "migration_contract": {
                "legacy_qfq_baseline_preserved": True,
                "legacy_qfq_compatibility_entry": "legacy_qfq_readonly",
                "old_report_overwrite_allowed": False,
                "new_prices_qfq_replaces_legacy_qfq": False,
            },
            "unsupported_execution_features": list(CR017_UNSUPPORTED_EXECUTION_FEATURES),
            "unsupported_execution_feature_allowed_count": 0,
            "operation_counts": dict(CR017_CONSUMER_FORBIDDEN_COUNTERS),
        }
    )


def render_migration_guide_sections() -> dict[str, str]:
    """渲染 CR017-S06 文档片段，供离线文档测试复核。"""

    matrix = build_consumer_guidance_matrix()
    metadata = research_dataset_policy_metadata(cr017_status="not_verified", stage="scale_up")
    matrix_lines = [
        "## Consumer Guidance Matrix",
        "",
        "| Consumer | Recommended policy | Allowed policies | Execution policy | Blocked policies |",
        "|---|---|---|---|---|",
    ]
    for consumer_type in CR017_CONSUMER_TYPES:
        row = matrix[consumer_type]
        matrix_lines.append(
            "| {consumer} | `{recommended}` | `{allowed}` | `{execution}` | `{blocked}` |".format(
                consumer=row["consumer_type"],
                recommended=row["recommended_policy"],
                allowed=", ".join(row["allowed_policies"]),
                execution=row["execution_price_policy"] or "N/A",
                blocked=", ".join(row["blocked_policies"]) or "none",
            )
        )
    governance_lines = [
        "## Governance And Scale-Up Boundary",
        "",
        f"- QMT execution raw-only: `{str(metadata['qmt_execution_raw_only']).lower()}`.",
        f"- Non-raw execution allowed count: `{metadata['qmt_non_raw_execution_allowed_count']}`.",
        "- Production adjustment governance claim allowed count before CR017 verified: "
        f"`{metadata['production_adjustment_governance_claim_allowed_count']}`.",
        f"- Scale_up allowed count before CR017 verified: `{metadata['scale_up_allowed_count']}`.",
    ]
    unsupported_lines = [
        "## Unsupported Execution Features",
        "",
        "| Feature | Status |",
        "|---|---|",
        *[f"| `{feature}` | unsupported / blocked |" for feature in CR017_UNSUPPORTED_EXECUTION_FEATURES],
    ]
    legacy_lines = [
        "## Legacy QFQ Preservation",
        "",
        "- Legacy qfq remains `legacy_qfq_readonly`.",
        "- Old reports overwrite allowed: `false`.",
        "- New `prices_qfq` does not replace or overwrite legacy qfq evidence.",
    ]
    return {
        "consumer_guidance": "\n".join(matrix_lines),
        "governance": "\n".join(governance_lines),
        "unsupported_execution_features": "\n".join(unsupported_lines),
        "legacy_qfq": "\n".join(legacy_lines),
    }


def _normalize_cr017_status(status: str) -> str:
    return str(status or "not_verified").strip().lower().replace(" ", "_").replace("-", "_")


def _cr017_status_verified(status: str) -> bool:
    return _normalize_cr017_status(status) in {"verified", "cp7_pass", "pass_verified"}


def _coerce_research_consumer_request(request: ResearchConsumerRequest | Mapping[str, Any]) -> ResearchConsumerRequest:
    if isinstance(request, ResearchConsumerRequest):
        return request
    data = dict(request)
    requested_claims = data.get("requested_claims") or ()
    if isinstance(requested_claims, str):
        requested_claims = (requested_claims,)
    return ResearchConsumerRequest(
        universe_scope=str(data.get("universe_scope") or data.get("universe") or ""),
        as_of_trade_date=str(data.get("as_of_trade_date") or data.get("trade_date") or ""),
        realism_mode=str(data.get("realism_mode") or "production_strict"),
        requested_claims=tuple(str(item) for item in requested_claims),
    )


def _cr014_research_consumer_counters(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    output = dict(CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS)
    aliases = {
        "provider_fetches": "provider_fetch",
        "lake_writes": "lake_write",
        "credential_reads": "credential_read",
        "legacy_data_operations": "legacy_data_operation",
        "legacy_data_reads": "legacy_data_operation",
        "old_data_read": "legacy_data_operation",
        "old_report_reads": "old_report_read",
        "old_report_overwrites": "old_report_overwrite",
        "duckdb_writes": "duckdb_write",
        "duckdb_opens": "duckdb_open",
        "duckdb_sql_views": "duckdb_sql_view",
        "dependency_changes": "duckdb_dependency_change",
        "current_pointer_changes": "catalog_current_pointer_publish",
        "publish_count": "catalog_current_pointer_publish",
        "candidate_lake_scans": "candidate_lake_scan",
        "docs_writes": "docs_write",
    }
    for raw_key, raw_value in dict(counters or {}).items():
        key = aliases.get(str(raw_key), str(raw_key))
        if key in output:
            output[key] = _safe_int(raw_value)
    return output


def _coerce_published_truth_payload(
    published_current_truth: Mapping[str, Any] | Any | None,
    clean_reader_output: Mapping[str, Any] | Any | None,
) -> dict[str, Any]:
    payload = _published_truth_payload_from_value(published_current_truth)
    clean_payload = _published_truth_payload_from_value(clean_reader_output)
    merged = {**clean_payload, **payload}
    if "catalog_entry" in merged:
        merged["catalog_entry"] = _plain_payload(merged.get("catalog_entry"))
    if "catalog_pointer" in merged:
        merged["catalog_pointer"] = _plain_payload(merged.get("catalog_pointer"))
    return {
        key: value
        for key, value in merged.items()
        if key != "frame" and value not in (None, "", [], {})
    }


def _published_truth_payload_from_value(value: Mapping[str, Any] | Any | None) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "status") and hasattr(value, "frame"):
        payload: dict[str, Any] = {
            "reader_status": str(getattr(value, "status", "")),
            "frame_available": getattr(value, "frame", None) is not None,
        }
        catalog_entry = getattr(value, "catalog_entry", None)
        if catalog_entry is not None:
            entry = _plain_payload(catalog_entry)
            payload["catalog_pointer"] = entry
            payload["published"] = bool(entry.get("published", True))
            payload["published_path"] = entry.get("published_path") or entry.get("canonical_path")
            payload["published_at"] = entry.get("published_at")
        return payload
    return _plain_payload(value)


def _plain_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _coerce_claim_boundary_payload(claim_boundary_summary: Mapping[str, Any] | Any | None) -> dict[str, Any]:
    if claim_boundary_summary is None:
        return {}
    payload = _plain_payload(claim_boundary_summary)
    if not payload:
        return {}
    payload["allowed_claims"] = [dict(item) if isinstance(item, Mapping) else {"claim": str(item)} for item in payload.get("allowed_claims") or []]
    payload["blocked_claims"] = [dict(item) for item in payload.get("blocked_claims") or [] if isinstance(item, Mapping)]
    payload["required_missing"] = [dict(item) for item in payload.get("required_missing") or [] if isinstance(item, Mapping)]
    payload["permission_counters"] = _cr014_research_consumer_counters(payload.get("permission_counters"))
    return metadata_to_dict(payload)


def _published_truth_status(payload: Mapping[str, Any]) -> str:
    if not payload:
        return "required_missing"
    raw_status = str(payload.get("status") or payload.get("reader_status") or payload.get("truth_status") or "").lower()
    if (
        payload.get("candidate_path")
        or payload.get("candidate_unpublished")
        or raw_status in {"candidate", "candidate_unpublished", "unpublished", "audit_only"}
    ):
        return "candidate_unpublished"
    catalog_pointer = payload.get("catalog_pointer") if isinstance(payload.get("catalog_pointer"), Mapping) else {}
    has_pointer = bool(
        payload.get("catalog_pointer")
        or payload.get("catalog_pointer_path")
        or payload.get("current_pointer")
        or payload.get("published_path")
        or catalog_pointer.get("published_path")
        or catalog_pointer.get("catalog_pointer_path")
    )
    published_flag = (
        payload.get("published_current_truth") is True
        or payload.get("published") is True
        or catalog_pointer.get("published") is True
        or bool(catalog_pointer.get("published_at"))
    )
    if has_pointer and (published_flag or raw_status in {"available", "published", "published_current_truth", "current_truth"}):
        return "published_current_truth"
    return "required_missing"


def _cr014_required_missing_row(
    *,
    dataset: str,
    gap_code: str,
    evidence_path: str,
    remediation: str,
    release_condition: str,
    claim: str = CR014_CLAIM_FULL_A_SINCE_INCEPTION,
) -> dict[str, Any]:
    return {
        "claim": claim,
        "claim_scope": "full_a_since_inception_production",
        "dataset": dataset,
        "gap_code": gap_code,
        "evidence_path": evidence_path,
        "remediation": remediation,
        "release_condition": release_condition,
        "severity": "P0",
    }


def _claim_names(values: Sequence[Any]) -> list[str]:
    output: list[str] = []
    for value in values:
        if isinstance(value, Mapping):
            claim = str(value.get("claim") or "")
        else:
            claim = str(value or "")
        if claim:
            output.append(claim)
    return _ordered_unique(output)


def _extract_clean_frame(
    truth_payload: Mapping[str, Any],
    clean_reader_output: Mapping[str, Any] | Any | None,
) -> pd.DataFrame | None:
    if _published_truth_status(truth_payload) != "published_current_truth":
        return None
    frame = None
    if hasattr(clean_reader_output, "frame"):
        frame = getattr(clean_reader_output, "frame")
    elif isinstance(clean_reader_output, Mapping):
        frame = clean_reader_output.get("frame")
        if frame is None:
            frame = clean_reader_output.get("prices")
    return frame.copy() if isinstance(frame, pd.DataFrame) else None


def _cr014_research_remediation(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "auto_execute": False,
        "auto_backfill": False,
        "provider_fetch": False,
        "lake_write": False,
        "credential_read": False,
        "candidate_scan": False,
        "duckdb_open": False,
        "docs_write": False,
        "dry_run_default": True,
    }


def build_research_dataset(
    request: ResearchDatasetRequest | Mapping[str, Any],
    *,
    reader: Any = read_dataset,
    benchmark_resolver: Any = resolve_hs300_benchmark,
    apply_s04_gates: bool = False,
) -> ResearchDataset:
    """只读聚合研究所需 prices、calendar、universe、benchmark 与 metadata。"""

    req = _coerce_research_dataset_request(request)
    parsed = _ParsedRequest.from_request(req)
    issues = list(parsed.issues)
    if issues:
        return _finish_research_dataset(
            req,
            parsed,
            status=ResearchDatasetStatus.INVALID_REQUEST.value,
            issues=issues,
            prices=None,
            close_df=None,
            calendar=[],
            universe_symbols=[],
            benchmark_result=None,
            reader_results={},
            known_limitations=["invalid request; reader and benchmark resolver were not called"],
        )

    require_index_members = req.symbols is None
    index_code = _universe_index_code(req.universe)
    research_datasets = _research_reader_datasets(req, require_index_members)
    reader_results = read_research_inputs(
        ResearchInputReaderRequest(
            lake_root=req.lake_root,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            symbols=req.symbols,
            datasets=research_datasets,
            quality_policy=QualityPolicy(allow_warn=req.analysis_mode == "exploratory", required=True),
            index_code=index_code,
            require_prices=True,
            require_calendar=True,
            require_index_members=require_index_members,
            require_stock_lifecycle=req.realism_mode == "production_strict",
        ),
        reader=reader,
    )

    prices_result = reader_results.get(DATASET_PRICES)
    calendar_result = reader_results.get(DATASET_TRADE_CALENDAR)
    universe_result = reader_results.get(DATASET_INDEX_MEMBERS)
    stock_lifecycle_result = reader_results.get(DATASET_STOCK_BASIC)
    index_weights_result = reader_results.get(DATASET_INDEX_WEIGHTS)

    issues.extend(_reader_issues(DATASET_PRICES, prices_result, required=True))
    issues.extend(_reader_issues(DATASET_TRADE_CALENDAR, calendar_result, required=True))
    issues.extend(_reader_issues(DATASET_INDEX_MEMBERS, universe_result, required=require_index_members))
    issues.extend(_reader_issues(DATASET_STOCK_BASIC, stock_lifecycle_result, required=req.realism_mode == "production_strict"))
    if req.realism_mode == "production_strict":
        for w3_dataset in _W3_RESEARCH_DATASETS:
            issues.extend(_reader_issues(w3_dataset, reader_results.get(w3_dataset), required=True))

    prices = _available_frame(prices_result)
    calendar = _build_research_calendar(calendar_result, prices, parsed, issues)
    universe_resolution = resolve_universe(
        UniverseRequest(
            index_code=index_code,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            analysis_mode=req.analysis_mode,
            universe_mode=req.universe_mode,
            symbols=req.symbols,
            decision_calendar=calendar,
            universe=req.universe,
        ),
        index_members_result=_pit_status_normalized_reader_result(universe_result),
        stock_basic_result=stock_lifecycle_result,
        index_weights_result=index_weights_result,
    )
    issues.extend(_universe_resolution_issues(universe_resolution))
    pit_lifecycle_gate = _evaluate_pit_lifecycle_gate(
        req,
        parsed,
        calendar,
        universe_resolution,
        universe_result,
        stock_lifecycle_result,
    )
    issues.extend(pit_lifecycle_gate.issues)
    universe_symbols = list(universe_resolution.symbols) or _build_research_universe(req, universe_result, issues)
    close_df = _build_research_close_df(req, parsed, prices, calendar, universe_symbols, issues)

    benchmark_result = _resolve_benchmark(req, parsed, benchmark_resolver, prices)
    if isinstance(benchmark_result, ResearchDatasetIssue):
        issues.append(benchmark_result)
        benchmark_result_value = None
    else:
        benchmark_result_value = benchmark_result
        issues.extend(_benchmark_issues(req, benchmark_result_value))
    if req.realism_mode == "production_strict":
        issues.extend(
            _production_strict_realism_issues(
                req,
                prices=prices,
                benchmark_result=benchmark_result_value,
                reader_results=reader_results,
                universe_resolution=universe_resolution,
            )
        )

    known_limitations = _merge_universe_known_limitations(
        _known_limitations(req, issues, prices, benchmark_result_value),
        universe_resolution,
    )
    known_limitations = _merge_pit_lifecycle_known_limitations(known_limitations, pit_lifecycle_gate)
    allowed_claims = _apply_universe_allowed_claims(
        req,
        _allowed_claims(req, issues, benchmark_result_value),
        universe_resolution,
    )
    allowed_claims = _apply_pit_lifecycle_allowed_claims(allowed_claims, pit_lifecycle_gate)
    status = _aggregate_research_status(issues)
    dataset = _finish_research_dataset(
        req,
        parsed,
        status=status,
        issues=issues,
        prices=prices,
        close_df=close_df,
        calendar=calendar,
        universe_symbols=universe_symbols,
        benchmark_result=benchmark_result_value,
        reader_results=reader_results,
        known_limitations=known_limitations,
        allowed_claims=allowed_claims,
        universe_resolution=universe_resolution,
        pit_lifecycle_gate=pit_lifecycle_gate,
    )
    if apply_s04_gates:
        return evaluate_research_gates(dataset, req, reader_results=reader_results)
    return dataset


def build_tradability_gate_matrix(
    trade_intents: Sequence[Mapping[str, Any]] | pd.DataFrame,
    reader_results: Mapping[str, ReaderResult] | None,
    *,
    realism_mode: str = "production_strict",
    decision_time: str | date | datetime | None = None,
    min_listing_days: int = 0,
) -> TradabilityGateMatrix:
    """按 trade_status、prices_limit、events、lifecycle 聚合 S03 gate matrix。"""

    intents = _coerce_trade_intents(trade_intents)
    source_results = dict(reader_results or {})
    missing_reader_reasons = _tradability_reader_missing_reasons(source_results)
    remediation_spec = _collect_remediation_spec(source_results, None, [])
    if not intents:
        reason_counts = {"trade_intents_missing": 1}
        return TradabilityGateMatrix(
            rows=(),
            status="required_missing",
            reason_counts=reason_counts,
            checks=[
                _gate_check(
                    "tradability_gate",
                    "fail",
                    "trade_intents_missing",
                    "ERROR",
                    "缺少计划交易行，不能把空矩阵声明为可交易。",
                    {"realism_mode": realism_mode},
                )
            ],
            blocked_claims=_tradability_blocked_claims("trade_intents_missing", None, "required_missing"),
            known_limitations=[_tradability_limitation("trade_intents_missing", "required_missing")],
            remediation_spec=remediation_spec,
        )

    rows: list[TradabilityGateRow] = []
    reason_counts: dict[str, int] = {}
    for intent in intents:
        if missing_reader_reasons:
            reasons = tuple(dict.fromkeys(missing_reader_reasons))
            row_status = "required_missing"
            details = {"missing_readers": reasons}
            can_buy = False
            can_sell = False
        else:
            trade_status = evaluate_trade_status_gate(
                intent,
                source_results.get(DATASET_TRADE_STATUS),
                source_results.get(DATASET_STOCK_BASIC),
                min_listing_days=min_listing_days,
            )
            price_limit = evaluate_price_limit_gate(intent, source_results.get(DATASET_PRICES_LIMIT))
            event_gate = evaluate_event_gate(
                intent,
                source_results.get(DATASET_EVENTS),
                decision_time=intent.get("decision_time") or decision_time,
            )
            gate_results = (trade_status, price_limit, event_gate)
            reasons = tuple(dict.fromkeys(reason for result in gate_results for reason in getattr(result, "reasons", ()) if reason))
            row_status = _tradability_row_status(gate_results)
            can_buy = bool(trade_status.can_buy and price_limit.can_buy and event_gate.can_buy)
            can_sell = bool(trade_status.can_sell and price_limit.can_sell and event_gate.can_sell)
            details = {
                "trade_status": trade_status.to_dict(),
                "price_limit": price_limit.to_dict(),
                "events": event_gate.to_dict(),
            }
        if row_status != "available" and not reasons:
            reasons = (row_status,)
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        rows.append(
            TradabilityGateRow(
                trade_date=str(intent.get("trade_date") or intent.get("date") or ""),
                symbol=str(intent.get("symbol") or ""),
                side=_normalize_trade_side(intent.get("side")),
                can_buy=can_buy,
                can_sell=can_sell,
                tradability_gate_status=row_status,
                blocked_reason=reasons[0] if reasons else "",
                blocked_reasons=reasons,
                gate_details=details,
            )
        )

    matrix_status = _tradability_matrix_status(rows, realism_mode)
    if matrix_status == "required_missing" and realism_mode == "production_strict":
        rows = tuple(
            TradabilityGateRow(
                trade_date=row.trade_date,
                symbol=row.symbol,
                side=row.side,
                can_buy=False,
                can_sell=False,
                tradability_gate_status="required_missing" if row.tradability_gate_status == "available" else row.tradability_gate_status,
                blocked_reason=row.blocked_reason or "p0_gate_required_missing",
                blocked_reasons=row.blocked_reasons or ("p0_gate_required_missing",),
                gate_details=row.gate_details,
            )
            for row in rows
        )
    else:
        rows = tuple(rows)
    checks = [
        _gate_check(
            "tradability_gate",
            "pass" if matrix_status == "available" else "fail" if realism_mode == "production_strict" else "warn",
            matrix_status,
            "INFO" if matrix_status == "available" else "ERROR" if realism_mode == "production_strict" else "WARNING",
            "S03 可交易性 gate matrix 评估完成。",
            {
                "realism_mode": realism_mode,
                "row_count": len(rows),
                "available_count": sum(1 for row in rows if row.tradability_gate_status == "available"),
                "blocked_count": sum(1 for row in rows if row.tradability_gate_status == "blocked"),
                "required_missing_count": sum(1 for row in rows if row.tradability_gate_status == "required_missing"),
                "reason_counts": reason_counts,
            },
        )
    ]
    blocked_claims = _tradability_matrix_blocked_claims(rows, matrix_status)
    limitations = []
    if matrix_status != "available":
        limitations.append(_tradability_limitation("tradability_gate_not_available", matrix_status))
    return TradabilityGateMatrix(
        rows=rows,
        status=matrix_status,
        reason_counts=reason_counts,
        checks=checks,
        blocked_claims=blocked_claims,
        known_limitations=limitations,
        remediation_spec=remediation_spec,
    )


def apply_tradability_gates(
    dataset: ResearchDataset,
    trade_intents: Sequence[Mapping[str, Any]] | pd.DataFrame,
    reader_results: Mapping[str, ReaderResult] | None = None,
    *,
    realism_mode: str | None = None,
    decision_time: str | date | datetime | None = None,
    min_listing_days: int = 0,
) -> ResearchDataset:
    """将 S03 tradability matrix 合并进 ResearchDataset metadata / claims。"""

    mode = realism_mode or str(dataset.metadata.get("realism_mode") or "production_strict")
    effective_reader_results = dict(reader_results or dataset.reader_results)
    matrix = build_tradability_gate_matrix(
        trade_intents,
        effective_reader_results,
        realism_mode=mode,
        decision_time=decision_time,
        min_listing_days=min_listing_days,
    )
    base_metadata = metadata_to_dict(dataset.metadata)
    blocked_claims = _dedupe_claim_payloads([*list(dataset.blocked_claims), *matrix.blocked_claims])
    limitations = _dedupe_json_safe([*list(dataset.known_limitations), *matrix.known_limitations])
    allowed_claims = _tradability_allowed_claims(dataset.allowed_claims, matrix, mode)
    metadata = dict(base_metadata)
    metadata["tradability"] = matrix.to_dict()
    metadata["tradability_gate_status"] = matrix.status
    metadata["tradability_available_count"] = matrix.available_count
    metadata["tradability_blocked_count"] = matrix.blocked_count
    metadata["tradability_required_missing_count"] = matrix.required_missing_count
    metadata["known_limitations"] = limitations
    metadata["allowed_claims"] = allowed_claims
    metadata["blocked_claims"] = blocked_claims
    metadata["remediation_spec"] = _normalize_remediation_spec(
        {
            **dict(dataset.remediation_spec or {}),
            "tradability": matrix.remediation_spec,
            "auto_execute": False,
            "dry_run_default": True,
        }
    )

    new_status = dataset.status
    if mode == "production_strict":
        if matrix.status == "required_missing":
            new_status = ResearchDatasetStatus.REQUIRED_MISSING.value
        elif matrix.status == "blocked":
            new_status = ResearchDatasetStatus.GATE_FAILED.value
    elif matrix.status != "available" and dataset.status == ResearchDatasetStatus.AVAILABLE.value:
        new_status = ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value

    issue_severity = "ERROR" if mode == "production_strict" and matrix.status != "available" else "WARNING"
    issues = list(dataset.issues)
    if matrix.status != "available":
        issues.append(
            ResearchDatasetIssue(
                code=f"tradability_{matrix.status}",
                dataset="tradability",
                severity=issue_severity,
                message="S03 可交易性 gate 未通过，真实可成交相关声明被阻断。",
                details={"reason_counts": matrix.reason_counts, "realism_mode": mode},
            )
        )
    gate_status = GateStatus.FAIL.value if mode == "production_strict" and matrix.status != "available" else GateStatus.WARN.value if matrix.status != "available" else dataset.gate_result.status
    gate_result = GateResult(
        status=gate_status,
        issues=issues,
        checks=_merge_gate_checks(dataset.gate_result.checks, matrix.checks),
        remediation_spec=metadata["remediation_spec"],
    )
    return ResearchDataset(
        status=new_status,
        prices=dataset.prices,
        close_df=dataset.close_df,
        calendar=list(dataset.calendar),
        universe_symbols=list(dataset.universe_symbols),
        benchmark_result=dataset.benchmark_result,
        metadata=metadata_to_dict(metadata),
        gate_result=gate_result,
        issues=issues,
        known_limitations=limitations,
        allowed_claims=allowed_claims,
        blocked_claims=blocked_claims,
        auxiliary_availability=dict(dataset.auxiliary_availability),
        remediation_spec=metadata["remediation_spec"],
        reader_results=effective_reader_results,
    )


def resolve_execution_price_policy(
    policy_request: ExecutionPolicyRequest | Mapping[str, Any] | str,
    feed_result: ReaderResult,
    *,
    tradability_matrix: TradabilityGateMatrix | Mapping[str, Any] | None = None,
) -> ExecutionPolicyResult:
    """解析 CR011-S04 四值 execution price policy。

    VWAP 缺失不会回退 close；`close_proxy` 是显式降级并阻断真实 VWAP /
    真实成交声明。
    """

    req = _coerce_execution_policy_request(policy_request)
    if req.policy not in _EXECUTION_PRICE_POLICIES:
        raise ValueError(f"invalid_execution_price_policy: {req.policy}")

    frame = feed_result.frame.copy() if feed_result.available and feed_result.frame is not None else pd.DataFrame()
    intents = _execution_trade_intents(req.trade_intents, frame)
    tradability_rows = _tradability_rows_by_key(tradability_matrix)
    rows: list[dict[str, Any]] = []
    for intent in intents:
        rows.append(_resolve_execution_row(req, intent, frame, tradability_rows, feed_result))

    status = _execution_result_status(req, rows, feed_result)
    blocked_claims = _execution_result_blocked_claims(req, rows, status)
    limitations = _execution_limitations(req, rows, status, blocked_claims)
    metadata = _execution_result_metadata(req, rows, status)
    checks = [
        _gate_check(
            "execution_price_gate",
            "pass" if status == "available" else "warn" if status == "available_with_warnings" else "fail",
            status,
            "INFO" if status == "available" else "WARNING" if status == "available_with_warnings" else "ERROR",
            "CR011-S04 execution price policy 评估完成。",
            metadata,
        )
    ]
    return ExecutionPolicyResult(
        execution_price_policy=req.policy,
        status=status,
        rows=tuple(rows),
        checks=checks,
        blocked_claims=blocked_claims,
        known_limitations=limitations,
        metadata=metadata,
    )


def evaluate_execution_price_gate(
    dataset: ResearchDataset,
    request: ExecutionPolicyRequest | ResearchDatasetRequest | Mapping[str, Any] | str,
    *,
    feed_result: ReaderResult | None = None,
    tradability_matrix: TradabilityGateMatrix | Mapping[str, Any] | None = None,
) -> ResearchDataset:
    """将 CR011-S04 execution price gate 合并进 ResearchDataset。"""

    policy_req = _coerce_execution_policy_request(_execution_policy_payload_from_request(request))
    effective_feed = feed_result or dataset.reader_results.get(DATASET_PRICES) or ReaderResult(
        status="required_missing",
        issues=[{"code": "execution_feed_missing", "dataset": DATASET_PRICES}],
        remediation_spec={"auto_execute": False, "dry_run_default": True},
    )
    result = resolve_execution_price_policy(policy_req, effective_feed, tradability_matrix=tradability_matrix)
    metadata = merge_execution_metadata(dataset.metadata, result)

    blocked_claims = _dedupe_claim_payloads([*list(dataset.blocked_claims), *result.blocked_claims])
    allowed_claims = _execution_allowed_claims(dataset.allowed_claims, result)
    limitations = _dedupe_json_safe([*list(dataset.known_limitations), *result.known_limitations])
    metadata["allowed_claims"] = allowed_claims
    metadata["blocked_claims"] = blocked_claims
    metadata["known_limitations"] = limitations
    metadata["execution_price_policy"] = result.execution_price_policy
    metadata["execution_availability_status"] = result.status
    metadata["network_calls"] = int(metadata.get("network_calls") or 0)
    metadata["lake_writes"] = int(metadata.get("lake_writes") or 0)
    metadata["credential_reads"] = int(metadata.get("credential_reads") or 0)
    metadata["legacy_data_operations"] = int(metadata.get("legacy_data_operations") or 0)

    issues = list(dataset.issues)
    if result.status != "available":
        severity = "WARNING" if result.status == "available_with_warnings" else "ERROR"
        issues.append(
            ResearchDatasetIssue(
                code=f"execution_{result.status}",
                dataset=DATASET_PRICES,
                severity=severity,
                message="CR011-S04 执行价 gate 未完全满足，真实 VWAP / 真实成交声明按合同阻断。",
                details=result.metadata,
            )
        )
    mode = policy_req.realism_mode
    status = _execution_dataset_status(dataset.status, result.status, mode)
    gate_status = _execution_gate_status(dataset.gate_result.status, result.status, mode)
    gate_result = GateResult(
        status=gate_status,
        issues=issues,
        checks=[*list(dataset.gate_result.checks), *result.checks],
        remediation_spec=_normalize_remediation_spec(
            {
                **dict(dataset.remediation_spec or {}),
                "execution": {
                    "auto_execute": False,
                    "dry_run_default": True,
                    "status": result.status,
                },
            }
        ),
    )
    return ResearchDataset(
        status=status,
        prices=dataset.prices,
        close_df=dataset.close_df,
        calendar=list(dataset.calendar),
        universe_symbols=list(dataset.universe_symbols),
        benchmark_result=dataset.benchmark_result,
        metadata=metadata_to_dict(metadata),
        gate_result=gate_result,
        issues=issues,
        known_limitations=limitations,
        allowed_claims=allowed_claims,
        blocked_claims=blocked_claims,
        auxiliary_availability=dict(dataset.auxiliary_availability),
        remediation_spec=gate_result.remediation_spec,
        reader_results=dict(dataset.reader_results),
    )


def evaluate_adjustment_audit(
    dataset: ResearchDataset,
    request: ResearchDatasetRequest | Mapping[str, Any],
    *,
    audit_result: AdjustmentAuditReaderResult | Mapping[str, Any] | None = None,
    reader_results: Mapping[str, ReaderResult] | None = None,
) -> AdjustmentAuditResult:
    """评估 CR011-S05 adjustment audit，不执行任何外部 I/O。"""

    req = _coerce_research_dataset_request(request)
    effective_reader_results = dict(reader_results or dataset.reader_results)
    reader_result = _coerce_adjustment_audit_reader_result(audit_result)
    if reader_result is None and audit_result is None and req.lake_root is not None and not _is_repo_data_request_path(req.lake_root):
        reader_result = read_adjustment_audit_inputs(
            {
                "lake_root": req.lake_root,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "symbols": req.symbols,
                "adjustment_policy": req.adjustment_policy,
                "quality_policy": QualityPolicy(allow_warn=req.analysis_mode == "exploratory", required=True),
            },
            reader=read_dataset,
        )
        effective_reader_results.update(reader_result.reader_results)

    prices_result = effective_reader_results.get(DATASET_PRICES) or ReaderResult(status="available", frame=dataset.prices)
    adj_factor_result = effective_reader_results.get(DATASET_ADJ_FACTOR)
    corporate_action_result = effective_reader_results.get(DATASET_CORPORATE_ACTIONS)
    if reader_result is not None:
        lineage = dict(reader_result.adj_factor_lineage)
        corporate_action_status = reader_result.corporate_action_status
        audit_status_from_reader = reader_result.adjustment_audit_status
        mixed_count_from_reader = int(reader_result.mixed_adjustment_policy_count)
        reader_issues = list(reader_result.issues)
        remediation_spec = dict(reader_result.remediation_spec)
    else:
        lineage = {
            key: value
            for key, value in extract_adj_factor_lineage(prices_result, adj_factor_result).items()
            if key != "issues"
        }
        corporate_action = evaluate_corporate_action_availability(corporate_action_result)
        corporate_action_status = str(corporate_action.get("corporate_action_status") or "required_missing")
        audit_status_from_reader = ""
        mixed_count_from_reader = 0
        reader_issues = list(corporate_action.get("issues") or [])
        remediation_spec = {
            "auto_execute": False,
            "dry_run_default": True,
            "actions": [],
        }

    adjustment_gate = evaluate_adjustment_gate(
        dataset.prices,
        req.adjustment_policy,
        dataset.metadata,
        reader_results=effective_reader_results,
    )
    adjustment_metadata = dict(adjustment_gate["metadata"])
    mixed_count = max(
        mixed_count_from_reader,
        len(adjustment_metadata.get("policies_seen") or []) if len(adjustment_metadata.get("policies_seen") or []) > 1 else 0,
    )
    issues = list(adjustment_gate["issues"])
    issues.extend(_adjustment_reader_issues(reader_issues))
    issues.extend(_lineage_issues(lineage))
    issues.extend(_corporate_action_issues(corporate_action_status, reader_issues))

    audit_status = _resolve_adjustment_audit_status(
        audit_status_from_reader,
        adjustment_gate,
        lineage,
        corporate_action_status,
    )
    allowed_claims = _adjustment_audit_allowed_claims(adjustment_gate, lineage, corporate_action_status, audit_status)
    blocked_claims = _adjustment_audit_blocked_claims(audit_status, lineage, corporate_action_status, mixed_count)
    limitations = _adjustment_audit_limitations(audit_status, lineage, corporate_action_status, blocked_claims)
    factor_entry_count = 1 if audit_status == "pass" else 0
    if audit_status != "pass":
        factor_entry_count = 0
    metadata = {
        "adjustment_policy": adjustment_metadata.get("adjustment_policy") or adjustment_metadata.get("request_policy") or req.adjustment_policy,
        "adj_factor_lineage": lineage,
        "corporate_action_status": corporate_action_status,
        "adjustment_audit_status": audit_status,
        "lineage_raw_checksum": lineage.get("lineage_raw_checksum"),
        "mixed_adjustment_policy_count": int(mixed_count),
        "factor_calculation_entry_count": int(factor_entry_count),
    }
    checks = [
        _gate_check(
            "adjustment_audit_gate",
            "pass" if audit_status == "pass" else "warn" if _only_corporate_action_missing(audit_status, lineage, corporate_action_status) else "fail",
            audit_status,
            "INFO" if audit_status == "pass" else "WARNING" if _only_corporate_action_missing(audit_status, lineage, corporate_action_status) else "ERROR",
            "CR011-S05 adjustment audit gate 评估完成。",
            metadata,
        )
    ]
    return AdjustmentAuditResult(
        adjustment_policy=str(metadata["adjustment_policy"] or req.adjustment_policy),
        adj_factor_lineage=lineage,
        corporate_action_status=corporate_action_status,
        adjustment_audit_status=audit_status,
        mixed_adjustment_policy_count=int(mixed_count),
        checks=checks,
        issues=issues,
        allowed_claims=allowed_claims,
        blocked_claims=blocked_claims,
        known_limitations=limitations,
        remediation_spec=_normalize_remediation_spec(remediation_spec),
        factor_calculation_entry_count=int(factor_entry_count),
    )


def apply_adjustment_audit_gate(
    dataset: ResearchDataset,
    request: ResearchDatasetRequest | Mapping[str, Any],
    *,
    audit_result: AdjustmentAuditResult | AdjustmentAuditReaderResult | Mapping[str, Any] | None = None,
    reader_results: Mapping[str, ReaderResult] | None = None,
    fail_on_required_missing: bool = True,
) -> ResearchDataset:
    """把 CR011-S05 audit gate 合并进 ResearchDataset metadata / claims。"""

    result = (
        audit_result
        if isinstance(audit_result, AdjustmentAuditResult)
        else evaluate_adjustment_audit(dataset, request, audit_result=audit_result, reader_results=reader_results)
    )
    assert isinstance(result, AdjustmentAuditResult)
    metadata = metadata_to_dict(dataset.metadata)
    audit_metadata = result.to_metadata()
    metadata["adjustment_audit"] = audit_metadata
    for field in (
        "adjustment_policy",
        "adj_factor_lineage",
        "corporate_action_status",
        "adjustment_audit_status",
        "lineage_raw_checksum",
        "mixed_adjustment_policy_count",
        "factor_calculation_entry_count",
    ):
        metadata[field] = audit_metadata.get(field)
    blocked_claims = _dedupe_claim_payloads([*list(dataset.blocked_claims), *result.blocked_claims])
    blocked_names = {str(item.get("claim") or "") for item in blocked_claims}
    allowed_claims = _ordered_unique([*list(dataset.allowed_claims), *result.allowed_claims])
    allowed_claims = [claim for claim in allowed_claims if claim not in blocked_names]
    limitations = _dedupe_json_safe([*list(dataset.known_limitations), *result.known_limitations])
    metadata["allowed_claims"] = allowed_claims
    metadata["blocked_claims"] = blocked_claims
    metadata["known_limitations"] = limitations
    metadata["network_calls"] = int(metadata.get("network_calls") or 0)
    metadata["lake_writes"] = int(metadata.get("lake_writes") or 0)
    metadata["credential_reads"] = int(metadata.get("credential_reads") or 0)
    metadata["legacy_data_operations"] = int(metadata.get("legacy_data_operations") or 0)

    issues = [*list(dataset.issues), *list(result.issues)]
    new_status = _adjustment_audit_dataset_status(dataset.status, result, fail_on_required_missing)
    gate_result = GateResult(
        status=_adjustment_audit_gate_status(dataset.gate_result.status, result, fail_on_required_missing),
        issues=issues,
        checks=[*list(dataset.gate_result.checks), *result.checks],
        remediation_spec=_normalize_remediation_spec(
            {
                **dict(dataset.remediation_spec or {}),
                "adjustment_audit": {
                    **dict(result.remediation_spec or {}),
                    "status": result.adjustment_audit_status,
                    "auto_execute": False,
                    "dry_run_default": True,
                },
            }
        ),
    )
    return ResearchDataset(
        status=new_status,
        prices=dataset.prices,
        close_df=dataset.close_df,
        calendar=list(dataset.calendar),
        universe_symbols=list(dataset.universe_symbols),
        benchmark_result=dataset.benchmark_result,
        metadata=metadata_to_dict(metadata),
        gate_result=gate_result,
        issues=issues,
        known_limitations=limitations,
        allowed_claims=allowed_claims,
        blocked_claims=blocked_claims,
        auxiliary_availability=dict(dataset.auxiliary_availability),
        remediation_spec=gate_result.remediation_spec,
        reader_results={**dict(dataset.reader_results), **dict(reader_results or {})},
    )


def merge_execution_metadata(
    metadata: Mapping[str, Any],
    execution_result: ExecutionPolicyResult | Mapping[str, Any],
) -> dict[str, Any]:
    """把 execution policy result 合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    result = execution_result if isinstance(execution_result, ExecutionPolicyResult) else _execution_result_from_mapping(execution_result)
    execution = result.to_metadata()
    base["execution"] = execution
    for key, value in execution.items():
        if key in {
            "execution_price_policy",
            "execution_availability_status",
            "execution_degradation_reason",
            "vwap_status",
            "vwap_or_proxy",
            "vwap_status_counts",
            "unfilled_reason_counts",
            "close_substitution_count",
        }:
            base[key] = value
    return metadata_to_dict(base)


def read_execution_price_audit(execution_price_audit_path: str | Path) -> dict[str, Any]:
    """只读解析 CR-013 execution audit，不触发 provider、lake 或凭据访问。"""

    path = Path(execution_price_audit_path)
    required_fields = {
        "logical_dataset",
        "source_dataset",
        "reader_status",
        "execution_price_status",
        "missing_ohlcv_columns",
        "true_vwap_available_count",
        "blocked_claims",
        "remediation",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required_fields.difference(reader.fieldnames or ()))
        if missing:
            raise ValueError(f"execution_audit_missing_fields: {','.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("execution_audit_missing_rows")
    if len(rows) != 1:
        raise ValueError("execution_audit_unexpected_row_count")

    row = dict(rows[0])
    row["missing_ohlcv_columns"] = _split_semicolon_field(row.get("missing_ohlcv_columns"))
    row["blocked_claims"] = _split_semicolon_field(row.get("blocked_claims"))
    row["true_vwap_available_count"] = _safe_int(row.get("true_vwap_available_count"))
    row["permission_counters"] = dict(CR013_PERMISSION_COUNTERS)
    row["old_baseline_preserved"] = True
    return row


def resolve_execution_claim_boundary(
    audit: Mapping[str, Any],
    requested_claims: Sequence[str] | None = None,
    *,
    fail_on_derived_vwap: bool = False,
) -> dict[str, Any]:
    """根据 CR-013 audit 固化真实 VWAP / 分钟执行价 blocked 声明。"""

    requested = _ordered_unique([str(item) for item in (requested_claims or ()) if str(item)])
    status = str(audit.get("execution_price_status") or audit.get("reader_status") or "required_missing")
    true_vwap_count = _safe_int(audit.get("true_vwap_available_count"))
    vwap_status = str(audit.get("vwap_status") or "")
    blocked_claims = _ordered_unique(
        [
            *[str(item) for item in audit.get("blocked_claims") or () if str(item)],
            "real_vwap_execution",
            "vwap_fill_claim",
        ]
    )
    if status != "available" or true_vwap_count <= 0 or vwap_status != "available":
        blocked_claims = _ordered_unique([*blocked_claims, "vwap_execution", "minute_execution", "order_match_execution"])

    derived_markers = {
        "amount_volume_derived_vwap",
        "amount/volume",
        "derived_vwap",
        "derived_vwap_from_amount_volume",
    }
    derived_attempts = [claim for claim in requested if claim in derived_markers]
    if derived_attempts and fail_on_derived_vwap:
        raise ValueError("derived_vwap_claim_attempt")

    unsupported_claims = list(CR013_EXECUTION_UNSUPPORTED_CLAIMS)
    denied = set(blocked_claims).union(unsupported_claims).union(derived_markers)
    allowed_claims = [claim for claim in requested if claim not in denied]
    research_degradation_claims = ["close_proxy_research_degradation"] if "close_proxy" in requested else []

    errors = []
    if derived_attempts:
        errors.append(
            {
                "code": "derived_vwap_claim_attempt",
                "claims": derived_attempts,
                "message": "amount/volume 不得被声明为真实 VWAP。",
            }
        )

    return {
        "execution_claim_boundary": "blocked",
        "execution_price_status": status,
        "missing_ohlcv_columns": list(audit.get("missing_ohlcv_columns") or ()),
        "true_vwap_available_count": true_vwap_count,
        "vwap_status": vwap_status or "required_missing",
        "blocked_claims": blocked_claims,
        "unsupported_claims": unsupported_claims,
        "allowed_claims": allowed_claims,
        "research_degradation_claims": research_degradation_claims,
        "release_criteria": list(CR013_EXECUTION_RELEASE_CRITERIA),
        "real_vwap_allowed_claim_count": 0,
        "vwap_fill_allowed_claim_count": 0,
        "minute_execution_allowed_claim_count": 0,
        "derived_vwap_allowed_claim_count": 0,
        "errors": errors,
        "old_baseline_preserved": True,
        "permission_counters": dict(CR013_PERMISSION_COUNTERS),
    }


def attach_execution_claim_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    claim_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    """把 CR-013 execution claim boundary 合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    boundary = metadata_to_dict(claim_boundary)
    blocked_payloads = [
        {
            "claim": claim,
            "missing_capability": "execution_price",
            "reason": "cr013_execution_claim_boundary_blocked",
            "severity": "BLOCKING",
        }
        for claim in boundary.get("blocked_claims") or ()
    ]
    merged_blocked = _dedupe_claim_payloads([*list(base.get("blocked_claims") or []), *blocked_payloads])
    blocked_names = _blocked_claim_names(merged_blocked)
    base["execution_claim_boundary"] = boundary
    base["blocked_claims"] = merged_blocked
    base["allowed_claims"] = [
        claim
        for claim in _ordered_unique([*list(base.get("allowed_claims") or []), *list(boundary.get("allowed_claims") or [])])
        if claim not in blocked_names
    ]
    base["known_limitations"] = _dedupe_json_safe(
        [
            *list(base.get("known_limitations") or []),
            {
                "code": "cr013_execution_claim_boundary",
                "blocked_claims": list(boundary.get("blocked_claims") or []),
                "unsupported_claims": list(boundary.get("unsupported_claims") or []),
                "release_criteria": list(boundary.get("release_criteria") or []),
            },
        ]
    )
    base["permission_counters"] = dict(CR013_PERMISSION_COUNTERS)
    return metadata_to_dict(base)


def assert_no_derived_real_vwap_claim(
    *,
    execution_policy: str | None = None,
    available_fields: Sequence[str] = (),
    requested_claims: Sequence[str] = (),
    fail_on_error: bool = False,
) -> dict[str, Any]:
    """研究消费层阻断 close proxy / amount-volume 派生真实 VWAP 声明。"""

    return _assert_no_derived_real_vwap_claim(
        execution_policy=execution_policy,
        available_fields=available_fields,
        requested_claims=requested_claims,
        fail_on_error=fail_on_error,
    )


def attach_unsupported_claims_to_research_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    unsupported_boundary: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """把 CR014-S08 unsupported / blocked boundary 合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    to_dict = getattr(unsupported_boundary, "to_dict", None)
    boundary = metadata_to_dict(to_dict() if callable(to_dict) else dict(unsupported_boundary))
    boundary_blocked = [dict(item) for item in boundary.get("blocked_claims") or [] if isinstance(item, Mapping)]
    boundary_required = [dict(item) for item in boundary.get("required_missing") or [] if isinstance(item, Mapping)]
    merged_blocked = _dedupe_claim_payloads([*list(base.get("blocked_claims") or []), *boundary_blocked])
    blocked_names = _blocked_claim_names(merged_blocked)
    unsupported_names = set(CR014_UNSUPPORTED_PRODUCTION_CLAIMS)
    base_allowed = [str(item.get("claim") if isinstance(item, Mapping) else item) for item in base.get("allowed_claims") or []]
    boundary_allowed = [
        str(item.get("claim") if isinstance(item, Mapping) else item)
        for item in boundary.get("allowed_claims") or []
    ]
    allowed_claims = [
        claim
        for claim in _ordered_unique([*base_allowed, *boundary_allowed])
        if claim not in blocked_names and claim not in unsupported_names
    ]
    base["unsupported_claim_boundary"] = boundary
    base["blocked_claims"] = merged_blocked
    base["required_missing"] = _dedupe_json_safe([*list(base.get("required_missing") or []), *boundary_required])
    base["allowed_claims"] = allowed_claims
    base["known_limitations"] = _dedupe_json_safe(
        [
            *list(base.get("known_limitations") or []),
            {
                "code": "cr014_s08_unsupported_boundary",
                "blocked_claims": [item.get("claim") for item in boundary_blocked],
                "required_missing": [item.get("gap_code") for item in boundary_required],
                "production_allowed_claim": False,
            },
        ]
    )
    base["production_allowed_unsupported_claim_count"] = 0
    base["real_vwap_allowed_claim_count"] = 0
    base["vwap_fill_allowed_claim_count"] = 0
    base["microstructure_allowed_claim_count"] = 0
    base["permission_counters"] = dict(boundary.get("permission_counters") or CR014_FORBIDDEN_OPERATION_COUNTERS)
    return metadata_to_dict(base)


def _split_semicolon_field(value: Any) -> list[str]:
    if isinstance(value, str):
        return [part.strip() for part in value.split(";") if part.strip()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(part).strip() for part in value if str(part).strip()]
    return []


def _safe_int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _coerce_adjustment_audit_reader_result(
    value: AdjustmentAuditReaderResult | Mapping[str, Any] | None,
) -> AdjustmentAuditReaderResult | None:
    if value is None:
        return None
    if isinstance(value, AdjustmentAuditReaderResult):
        return value
    if isinstance(value, Mapping):
        return AdjustmentAuditReaderResult(
            status=str(value.get("status") or value.get("adjustment_audit_status") or "required_missing"),
            adjustment_policy=str(value.get("adjustment_policy") or "qfq"),
            adj_factor_lineage=dict(value.get("adj_factor_lineage") or {}),
            corporate_action_status=str(value.get("corporate_action_status") or "required_missing"),
            adjustment_audit_status=str(value.get("adjustment_audit_status") or value.get("status") or "required_missing"),
            mixed_adjustment_policy_count=int(value.get("mixed_adjustment_policy_count") or 0),
            issues=[dict(item) for item in value.get("issues") or [] if isinstance(item, Mapping)],
            remediation_spec=dict(value.get("remediation_spec") or {"auto_execute": False, "dry_run_default": True}),
        )
    return None


def _adjustment_reader_issues(issues: Sequence[Mapping[str, Any]]) -> list[ResearchDatasetIssue]:
    output: list[ResearchDatasetIssue] = []
    for issue in issues:
        code = str(issue.get("code") or "")
        dataset = str(issue.get("dataset") or "") or None
        if not code:
            continue
        if code.startswith("corporate_action") or code.startswith("corporate_actions"):
            continue
        severity = "ERROR" if code not in {"quality_warn"} else "WARNING"
        output.append(
            ResearchDatasetIssue(
                code=code,
                dataset=dataset,
                severity=severity,
                message="adjustment audit reader issue",
                details=dict(issue),
            )
        )
    return output


def _lineage_issues(lineage: Mapping[str, Any]) -> list[ResearchDatasetIssue]:
    status = str(lineage.get("status") or "")
    if status == "available":
        return []
    code = str(lineage.get("missing_reason") or "adj_factor_lineage_missing")
    return [
        ResearchDatasetIssue(
            code=code,
            dataset=DATASET_ADJ_FACTOR,
            field="adj_factor_lineage",
            message="缺少可审计 adj_factor lineage，禁止进入因子计算。",
            details=dict(lineage),
        )
    ]


def _corporate_action_issues(
    corporate_action_status: str,
    raw_issues: Sequence[Mapping[str, Any]],
) -> list[ResearchDatasetIssue]:
    if corporate_action_status == "available":
        return []
    codes = [
        str(issue.get("code") or "")
        for issue in raw_issues
        if str(issue.get("dataset") or "") == DATASET_CORPORATE_ACTIONS and str(issue.get("code") or "")
    ]
    code = codes[0] if codes else "corporate_action_required_missing"
    severity = "ERROR" if corporate_action_status == "quality_failed" else "WARNING"
    return [
        ResearchDatasetIssue(
            code=code,
            dataset=DATASET_CORPORATE_ACTIONS,
            field="corporate_action_status",
            severity=severity,
            message="公司行动 source/interface/available_at 未满足完整审计声明要求。",
            details={"corporate_action_status": corporate_action_status, "issue_codes": codes},
        )
    ]


def _resolve_adjustment_audit_status(
    reader_status: str,
    adjustment_gate: Mapping[str, Any],
    lineage: Mapping[str, Any],
    corporate_action_status: str,
) -> str:
    if reader_status in {"pass", "required_missing", "quality_failed"}:
        if reader_status == "quality_failed":
            return "quality_failed"
        if reader_status == "required_missing" and str(lineage.get("status") or "") != "available":
            return "required_missing"
    check = adjustment_gate.get("check") if isinstance(adjustment_gate.get("check"), Mapping) else {}
    if check.get("status") == "fail" or str(lineage.get("status") or "") == "quality_failed" or corporate_action_status == "quality_failed":
        return "quality_failed"
    if str(lineage.get("status") or "") != "available":
        return "required_missing"
    if corporate_action_status != "available":
        return "required_missing"
    return "pass"


def _adjustment_audit_allowed_claims(
    adjustment_gate: Mapping[str, Any],
    lineage: Mapping[str, Any],
    corporate_action_status: str,
    audit_status: str,
) -> list[str]:
    check = adjustment_gate.get("check") if isinstance(adjustment_gate.get("check"), Mapping) else {}
    adjustment_passed = check.get("status") == "pass"
    lineage_available = str(lineage.get("status") or "") == "available"
    claims: list[str] = []
    if adjustment_passed and lineage_available:
        claims.extend(_ADJUSTMENT_CONSERVATIVE_CLAIMS)
    if audit_status == "pass" and corporate_action_status == "available":
        claims.extend(_ADJUSTMENT_COMPLETE_AUDIT_CLAIMS)
        claims.extend(_ADJUSTMENT_RESEARCH_CLAIMS)
    return _ordered_unique(claims)


def _adjustment_audit_blocked_claims(
    audit_status: str,
    lineage: Mapping[str, Any],
    corporate_action_status: str,
    mixed_count: int,
) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    if corporate_action_status != "available":
        reason = corporate_action_status if corporate_action_status else "corporate_action_required_missing"
        blocked.extend(
            _adjustment_blocked_claim_payload(claim, "corporate_actions", reason)
            for claim in _ADJUSTMENT_COMPLETE_AUDIT_CLAIMS
        )
    lineage_available = str(lineage.get("status") or "") == "available"
    if audit_status == "quality_failed" or not lineage_available or mixed_count > 0:
        reason = "adjustment_policy_mixed" if mixed_count > 0 else str(lineage.get("missing_reason") or audit_status)
        blocked.extend(
            _adjustment_blocked_claim_payload(claim, "adjustment_audit", reason)
            for claim in (*_ADJUSTMENT_RESEARCH_CLAIMS, *_ADJUSTMENT_COMPLETE_AUDIT_CLAIMS)
        )
    return _dedupe_claim_payloads(blocked)


def _adjustment_blocked_claim_payload(claim: str, capability: str, reason: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "missing_capability": capability,
        "reason": reason,
        "severity": "BLOCKING",
        "details": {
            "adjustment_audit_status": reason,
            "auto_execute": False,
        },
    }


def _adjustment_audit_limitations(
    audit_status: str,
    lineage: Mapping[str, Any],
    corporate_action_status: str,
    blocked_claims: Sequence[Mapping[str, Any]],
) -> list[Any]:
    limitations: list[Any] = []
    if audit_status != "pass":
        limitations.append(
            {
                "code": "adjustment_audit_limitation",
                "adjustment_audit_status": audit_status,
                "adj_factor_lineage_status": lineage.get("status", "required_missing"),
                "corporate_action_status": corporate_action_status,
                "blocked_claims": [item.get("claim") for item in blocked_claims],
            }
        )
    return limitations


def _only_corporate_action_missing(
    audit_status: str,
    lineage: Mapping[str, Any],
    corporate_action_status: str,
) -> bool:
    return (
        audit_status == "required_missing"
        and str(lineage.get("status") or "") == "available"
        and corporate_action_status != "available"
    )


def _adjustment_audit_dataset_status(
    previous_status: str,
    result: AdjustmentAuditResult,
    fail_on_required_missing: bool,
) -> str:
    if previous_status in {
        ResearchDatasetStatus.INVALID_REQUEST.value,
        ResearchDatasetStatus.QUALITY_FAILED.value,
        ResearchDatasetStatus.REQUIRED_MISSING.value,
        ResearchDatasetStatus.GATE_FAILED.value,
    }:
        return previous_status
    if result.adjustment_audit_status == "quality_failed":
        return ResearchDatasetStatus.GATE_FAILED.value
    if result.adjustment_audit_status == "required_missing":
        if _only_corporate_action_missing(result.adjustment_audit_status, result.adj_factor_lineage, result.corporate_action_status):
            return ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
        return ResearchDatasetStatus.GATE_FAILED.value if fail_on_required_missing else ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    if previous_status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value:
        return previous_status
    return ResearchDatasetStatus.AVAILABLE.value


def _adjustment_audit_gate_status(
    previous_gate_status: str,
    result: AdjustmentAuditResult,
    fail_on_required_missing: bool,
) -> str:
    if previous_gate_status == GateStatus.FAIL.value:
        return previous_gate_status
    if result.adjustment_audit_status == "pass":
        return previous_gate_status if previous_gate_status in {GateStatus.WARN.value, GateStatus.PASS.value} else GateStatus.PASS.value
    if _only_corporate_action_missing(result.adjustment_audit_status, result.adj_factor_lineage, result.corporate_action_status):
        return GateStatus.WARN.value
    if result.adjustment_audit_status == "required_missing" and not fail_on_required_missing:
        return GateStatus.WARN.value
    return GateStatus.FAIL.value


def _adjustment_audit_missing_reason(result: AdjustmentAuditResult) -> str:
    if result.corporate_action_status == "available":
        return ""
    for issue in result.issues:
        if issue.dataset == DATASET_CORPORATE_ACTIONS:
            return issue.code
    return result.corporate_action_status


def _is_repo_data_request_path(value: str | Path | None) -> bool:
    if value is None:
        return False
    path = Path(value)
    return not path.is_absolute() and (path.parts == ("data",) or path.parts[:1] == ("data",))


def _coerce_execution_policy_request(
    request: ExecutionPolicyRequest | Mapping[str, Any] | str,
) -> ExecutionPolicyRequest:
    if isinstance(request, ExecutionPolicyRequest):
        return request
    if isinstance(request, str):
        return ExecutionPolicyRequest(policy=request)
    values = dict(request)
    policy_value = _explicit_policy_value(values)
    policy = "close_proxy" if policy_value is _POLICY_MISSING else "" if policy_value is None else str(policy_value)
    realism_mode = str(values.get("realism_mode") or "production_strict").strip() or "production_strict"
    intents_value = values.get("trade_intents", None)
    if intents_value is None:
        intents_value = values.get("planned_trades", ())
    if isinstance(intents_value, pd.DataFrame):
        intents = tuple(intents_value.to_dict(orient="records"))
    else:
        intents = tuple(dict(item) for item in intents_value)
    return ExecutionPolicyRequest(
        policy=policy,
        realism_mode=realism_mode,
        trade_intents=intents,
        degradation_reason=str(values.get("degradation_reason") or values.get("execution_degradation_reason") or ""),
    )


def _explicit_policy_value(values: Mapping[str, Any]) -> Any:
    if "policy" in values:
        return values["policy"]
    if "execution_price_policy" in values:
        return values["execution_price_policy"]
    return _POLICY_MISSING


def _execution_policy_payload_from_request(
    request: ExecutionPolicyRequest | ResearchDatasetRequest | Mapping[str, Any] | str,
) -> ExecutionPolicyRequest | Mapping[str, Any] | str:
    if isinstance(request, (ExecutionPolicyRequest, str, Mapping)):
        return request
    metadata = getattr(request, "metadata", None)
    if isinstance(metadata, Mapping):
        return metadata
    return {
        "policy": getattr(request, "execution_price_policy", "close_proxy"),
        "realism_mode": getattr(request, "realism_mode", None) or "production_strict",
    }


def _execution_trade_intents(
    requested_intents: Sequence[Mapping[str, Any]],
    frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    if requested_intents:
        return _coerce_trade_intents(requested_intents)
    if frame.empty:
        return []
    source = frame.to_dict(orient="records")
    return _coerce_trade_intents(source)


def _tradability_rows_by_key(
    tradability_matrix: TradabilityGateMatrix | Mapping[str, Any] | None,
) -> dict[tuple[str, str, str], dict[str, Any]]:
    if tradability_matrix is None:
        return {}
    if isinstance(tradability_matrix, TradabilityGateMatrix):
        rows = [row.to_dict() for row in tradability_matrix.rows]
    else:
        rows = list(tradability_matrix.get("rows") or [])
    output: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("trade_date") or payload.get("date") or ""),
            str(payload.get("symbol") or ""),
            _normalize_trade_side(payload.get("side")),
        )
        output[key] = payload
    return output


def _resolve_execution_row(
    req: ExecutionPolicyRequest,
    intent: Mapping[str, Any],
    frame: pd.DataFrame,
    tradability_rows: Mapping[tuple[str, str, str], Mapping[str, Any]],
    feed_result: ReaderResult,
) -> dict[str, Any]:
    trade_date = str(intent.get("trade_date") or intent.get("date") or "")
    symbol = str(intent.get("symbol") or "")
    side = _normalize_trade_side(intent.get("side"))
    source_row = _execution_source_row(frame, trade_date, symbol)
    tradability = _execution_tradability_row(tradability_rows, trade_date, symbol, side)
    blocked_reason = _tradability_execution_blocked_reason(tradability)

    payload: dict[str, Any] = {
        "trade_date": trade_date,
        "symbol": symbol,
        "side": side,
        "execution_price_policy": req.policy,
        "execution_price": None,
        "execution_degradation_reason": "",
        "unfilled_reason": "",
        "vwap_status": "required_missing",
        "vwap_or_proxy": "missing",
        "tradability_gate_status": str(tradability.get("tradability_gate_status") or "not_evaluated") if tradability else "not_evaluated",
        "blocked_claims": [],
    }

    if feed_result.status != "available":
        payload["unfilled_reason"] = _feed_missing_reason(feed_result)
        payload["execution_degradation_reason"] = payload["unfilled_reason"]
        payload["blocked_claims"] = _row_blocked_claims(req.policy, payload["unfilled_reason"])
        return payload
    if source_row is None:
        payload["unfilled_reason"] = "missing_execution_price"
        payload["execution_degradation_reason"] = "missing_execution_price"
        payload["blocked_claims"] = _row_blocked_claims(req.policy, "missing_execution_price")
        return payload

    payload["vwap_status"] = str(source_row.get("vwap_status") or "required_missing")
    payload["vwap_or_proxy"] = str(source_row.get("vwap_or_proxy") or ("vwap" if payload["vwap_status"] == "available" else "missing"))
    if blocked_reason:
        payload["unfilled_reason"] = "tradability_blocked" if blocked_reason != "required_missing" else "tradability_required_missing"
        payload["execution_degradation_reason"] = blocked_reason
        payload["blocked_claims"] = _row_blocked_claims(req.policy, blocked_reason)
        return payload

    if req.policy in {"open", "close"}:
        price, reason = _execution_price_from_row(source_row, req.policy)
        if reason:
            payload["unfilled_reason"] = reason
            payload["execution_degradation_reason"] = reason
            payload["blocked_claims"] = _row_blocked_claims(req.policy, reason)
        else:
            payload["execution_price"] = price
            payload["vwap_or_proxy"] = req.policy
        return payload

    if req.policy == "vwap":
        if payload["vwap_status"] != "available":
            payload["unfilled_reason"] = str(payload["vwap_status"] or "vwap_required_missing")
            payload["execution_degradation_reason"] = payload["unfilled_reason"]
            payload["blocked_claims"] = _row_blocked_claims(req.policy, payload["unfilled_reason"])
            return payload
        price, reason = _execution_price_from_row(source_row, "vwap")
        if reason:
            payload["unfilled_reason"] = "vwap_required_missing" if reason == "missing_execution_price" else reason
            payload["execution_degradation_reason"] = payload["unfilled_reason"]
            payload["blocked_claims"] = _row_blocked_claims(req.policy, payload["unfilled_reason"])
        else:
            payload["execution_price"] = price
            payload["vwap_or_proxy"] = "vwap"
        return payload

    price, reason = _execution_price_from_row(source_row, "close")
    payload["execution_degradation_reason"] = req.degradation_reason or "policy_explicit_close_proxy"
    payload["vwap_or_proxy"] = "proxy"
    payload["blocked_claims"] = _row_blocked_claims(req.policy, payload["execution_degradation_reason"])
    if reason:
        payload["unfilled_reason"] = reason
    else:
        payload["execution_price"] = price
    return payload


def _execution_source_row(frame: pd.DataFrame, trade_date: str, symbol: str) -> dict[str, Any] | None:
    if frame.empty or "trade_date" not in frame.columns or "symbol" not in frame.columns:
        return None
    mask = (frame["trade_date"].astype(str) == trade_date) & (frame["symbol"].astype(str) == symbol)
    if not mask.any():
        return None
    return dict(frame.loc[mask].iloc[0].to_dict())


def _execution_tradability_row(
    rows: Mapping[tuple[str, str, str], Mapping[str, Any]],
    trade_date: str,
    symbol: str,
    side: str,
) -> Mapping[str, Any]:
    return rows.get((trade_date, symbol, side)) or rows.get((trade_date, symbol, "hold")) or {}


def _tradability_execution_blocked_reason(row: Mapping[str, Any]) -> str:
    status = str(row.get("tradability_gate_status") or "")
    if status == "available" or not status:
        return ""
    reason = str(row.get("blocked_reason") or "")
    if not reason:
        reasons = row.get("blocked_reasons") or []
        reason = str(reasons[0]) if reasons else status
    return reason or status


def _execution_price_from_row(row: Mapping[str, Any], field: str) -> tuple[float | None, str]:
    if field not in row:
        return None, "missing_execution_price"
    value = row.get(field)
    if not _valid_execution_price(value):
        return None, "price_not_finite"
    return float(value), ""


def _valid_execution_price(value: Any) -> bool:
    if value is None or pd.isna(value):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _feed_missing_reason(feed_result: ReaderResult) -> str:
    for issue in feed_result.issues:
        code = str(issue.get("code") or "")
        if code:
            return code
    return feed_result.status or "execution_feed_missing"


def _row_blocked_claims(policy: str, reason: str) -> list[dict[str, Any]]:
    if policy == "close_proxy":
        claims = _EXECUTION_REAL_CLAIMS
    elif policy == "vwap":
        claims = ("real_vwap_execution", "vwap_fill_claim", "vwap_execution", "real_tradable_execution", "true_fillability")
    elif policy == "open":
        claims = ("real_open_execution", "open_execution", "real_tradable_execution", "true_fillability")
    else:
        claims = ("real_tradable_execution", "true_fillability")
    return [
        {
            "claim": claim,
            "reason_code": reason,
            "blocked_reason": reason,
            "missing_capability": "execution_price",
            "severity": "ERROR",
        }
        for claim in claims
    ]


def _execution_result_status(
    req: ExecutionPolicyRequest,
    rows: Sequence[Mapping[str, Any]],
    feed_result: ReaderResult,
) -> str:
    if feed_result.status != "available":
        return "required_missing" if feed_result.status == "required_missing" else "gate_failed"
    if not rows:
        return "required_missing"
    reasons = [str(row.get("unfilled_reason") or "") for row in rows if row.get("unfilled_reason")]
    if any(reason in {"source_unresolved", "lake_root_missing"} or reason.endswith("required_missing") for reason in reasons):
        return "required_missing"
    if any("tradability" in reason for reason in reasons):
        return "blocked"
    if reasons:
        return "gate_failed" if req.realism_mode == "production_strict" else "available_with_warnings"
    if req.policy == "close_proxy":
        return "available_with_warnings"
    return "available"


def _execution_result_blocked_claims(
    req: ExecutionPolicyRequest,
    rows: Sequence[Mapping[str, Any]],
    status: str,
) -> list[dict[str, Any]]:
    blocked: list[Mapping[str, Any]] = []
    for row in rows:
        blocked.extend(row.get("blocked_claims") or [])
    if req.policy == "close_proxy" and not blocked:
        blocked.extend(_row_blocked_claims(req.policy, req.degradation_reason or "policy_explicit_close_proxy"))
    if status not in {"available", "available_with_warnings"} and not blocked:
        blocked.extend(_row_blocked_claims(req.policy, status))
    return _dedupe_claim_payloads(blocked)


def _execution_limitations(
    req: ExecutionPolicyRequest,
    rows: Sequence[Mapping[str, Any]],
    status: str,
    blocked_claims: Sequence[Mapping[str, Any]],
) -> list[Any]:
    limitations: list[Any] = []
    if req.policy == "close_proxy":
        limitations.append(
            {
                "code": "execution_close_proxy_degradation",
                "execution_price_policy": req.policy,
                "execution_degradation_reason": req.degradation_reason or "policy_explicit_close_proxy",
                "blocked_claims": [item.get("claim") for item in blocked_claims],
            }
        )
    reason_counts = _execution_reason_counts(rows, "unfilled_reason")
    if status not in {"available", "available_with_warnings"} or reason_counts:
        limitations.append(
            {
                "code": "execution_price_limitation",
                "execution_availability_status": status,
                "unfilled_reason_counts": reason_counts,
            }
        )
    return limitations


def _execution_result_metadata(
    req: ExecutionPolicyRequest,
    rows: Sequence[Mapping[str, Any]],
    status: str,
) -> dict[str, Any]:
    executable_count = sum(1 for row in rows if row.get("execution_price") is not None and not row.get("unfilled_reason"))
    metadata = {
        "execution_price_policy": req.policy,
        "execution_availability_status": status,
        "execution_degradation_reason": req.degradation_reason or ("policy_explicit_close_proxy" if req.policy == "close_proxy" else ""),
        "row_count": len(rows),
        "executable_count": executable_count,
        "unfilled_count": len(rows) - executable_count,
        "close_substitution_count": 0,
        "missing_price_fill_count": 0,
        "vwap_status_counts": _execution_reason_counts(rows, "vwap_status"),
        "vwap_or_proxy_counts": _execution_reason_counts(rows, "vwap_or_proxy"),
        "unfilled_reason_counts": _execution_reason_counts(rows, "unfilled_reason"),
        "execution_degradation_reason_counts": _execution_reason_counts(rows, "execution_degradation_reason"),
        "vwap_status": _dominant_value(rows, "vwap_status"),
        "vwap_or_proxy": _dominant_value(rows, "vwap_or_proxy"),
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
    }
    return metadata


def _execution_reason_counts(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field) or "")
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _dominant_value(rows: Sequence[Mapping[str, Any]], field: str) -> str:
    counts = _execution_reason_counts(rows, field)
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _execution_allowed_claims(
    existing_claims: Sequence[str],
    result: ExecutionPolicyResult,
) -> list[str]:
    blocked = {str(item.get("claim") or "") for item in result.blocked_claims}
    retained = [claim for claim in existing_claims if claim not in blocked and claim not in _EXECUTION_REAL_CLAIMS]
    if result.status == "available" and result.execution_price_policy == "vwap":
        retained.extend(["vwap_execution"])
    elif result.status == "available" and result.execution_price_policy == "open":
        retained.extend(["open_execution"])
    elif result.status == "available":
        retained.extend(["execution_price_available"])
    elif result.status == "available_with_warnings":
        retained.extend(["framework_validation", "exploratory_analysis"])
    return _ordered_unique(retained)


def _execution_dataset_status(previous_status: str, execution_status: str, realism_mode: str) -> str:
    if previous_status in {
        ResearchDatasetStatus.INVALID_REQUEST.value,
        ResearchDatasetStatus.REQUIRED_MISSING.value,
        ResearchDatasetStatus.QUALITY_FAILED.value,
        ResearchDatasetStatus.GATE_FAILED.value,
    }:
        return previous_status
    if execution_status == "available":
        return previous_status
    if execution_status == "available_with_warnings":
        return ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    if realism_mode == "production_strict":
        return ResearchDatasetStatus.REQUIRED_MISSING.value if execution_status == "required_missing" else ResearchDatasetStatus.GATE_FAILED.value
    return ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value


def _execution_gate_status(previous_status: str, execution_status: str, realism_mode: str) -> str:
    if previous_status == GateStatus.FAIL.value:
        return previous_status
    if execution_status == "available":
        return previous_status if previous_status != GateStatus.NOT_EVALUATED.value else GateStatus.PASS.value
    if execution_status == "available_with_warnings":
        return GateStatus.WARN.value
    if realism_mode == "production_strict":
        return GateStatus.FAIL.value
    return GateStatus.WARN.value


def _execution_result_from_mapping(value: Mapping[str, Any]) -> ExecutionPolicyResult:
    return ExecutionPolicyResult(
        execution_price_policy=str(value.get("execution_price_policy") or "close_proxy"),
        status=str(value.get("execution_availability_status") or value.get("status") or "available_with_warnings"),
        rows=tuple(dict(item) for item in value.get("rows") or ()),
        checks=[dict(item) for item in value.get("checks") or ()],
        blocked_claims=[dict(item) for item in value.get("blocked_claims") or ()],
        known_limitations=list(value.get("known_limitations") or ()),
        metadata=dict(value.get("metadata") or value),
    )


def _coerce_trade_intents(trade_intents: Sequence[Mapping[str, Any]] | pd.DataFrame) -> list[dict[str, Any]]:
    if isinstance(trade_intents, pd.DataFrame):
        source = trade_intents.to_dict(orient="records")
    else:
        source = list(trade_intents)
    intents: list[dict[str, Any]] = []
    for item in source:
        values = dict(item)
        values["trade_date"] = str(values.get("trade_date") or values.get("date") or "")
        values["symbol"] = str(values.get("symbol") or "").strip()
        values["side"] = _normalize_trade_side(values.get("side"))
        if values["trade_date"] and values["symbol"]:
            intents.append(values)
    return intents


def _normalize_trade_side(value: Any) -> str:
    text = str(value or "hold").strip().lower()
    return text if text in {"buy", "sell", "hold"} else "hold"


def _tradability_reader_missing_reasons(reader_results: Mapping[str, ReaderResult]) -> list[str]:
    reasons: list[str] = []
    for dataset in _TRADABILITY_REQUIRED_DATASETS:
        result = reader_results.get(dataset)
        if result is None:
            reasons.append(f"{dataset}_required_missing")
            continue
        if result.status != "available":
            issue_codes = [str(issue.get("code") or "") for issue in result.issues if issue.get("code")]
            if any(code in {"w3_source_unresolved", "source_unresolved"} for code in issue_codes):
                reasons.append("source_unresolved")
            elif "available_at_missing" in issue_codes or "w3_required_fields_missing" in issue_codes:
                reasons.append("available_at_missing")
            else:
                reasons.append(f"{dataset}_required_missing")
    return list(dict.fromkeys(reasons))


def _tradability_row_status(gate_results: Sequence[Any]) -> str:
    statuses = [str(getattr(result, "status", "") or "") for result in gate_results]
    if "required_missing" in statuses:
        return "required_missing"
    if "blocked" in statuses:
        return "blocked"
    return "available"


def _tradability_matrix_status(rows: Sequence[TradabilityGateRow], realism_mode: str) -> str:
    if not rows:
        return "required_missing"
    if any(row.tradability_gate_status == "required_missing" for row in rows):
        return "required_missing"
    if any(row.tradability_gate_status == "blocked" for row in rows):
        return "blocked"
    return "available"


def _tradability_matrix_blocked_claims(rows: Sequence[TradabilityGateRow], status: str) -> list[dict[str, Any]]:
    if status == "available":
        return []
    reasons = sorted({reason for row in rows for reason in row.blocked_reasons} or {status})
    blocked: list[dict[str, Any]] = []
    for claim in _TRADABILITY_REAL_CLAIMS:
        blocked.append(
            {
                "claim": claim,
                "reason_code": reasons[0],
                "blocked_reason": reasons[0],
                "missing_capability": "tradability" if status == "required_missing" else "",
                "severity": "ERROR",
                "details": {"reason_codes": reasons, "tradability_gate_status": status},
            }
        )
    return blocked


def _tradability_blocked_claims(reason: str, dataset: str | None, status: str) -> list[dict[str, Any]]:
    return [
        {
            "claim": claim,
            "reason_code": reason,
            "dataset": dataset,
            "missing_capability": "tradability",
            "severity": "ERROR",
            "details": {"tradability_gate_status": status},
        }
        for claim in _TRADABILITY_REAL_CLAIMS
    ]


def _tradability_limitation(reason: str, status: str) -> dict[str, Any]:
    return {
        "code": "tradability_gate_limitation",
        "reason_code": reason,
        "tradability_gate_status": status,
        "blocked_claims": list(_TRADABILITY_REAL_CLAIMS),
    }


def _tradability_allowed_claims(
    existing_claims: Sequence[str],
    matrix: TradabilityGateMatrix,
    realism_mode: str,
) -> list[str]:
    retained = [claim for claim in existing_claims if claim not in _TRADABILITY_REAL_CLAIMS]
    if realism_mode == "exploratory":
        return _ordered_unique([*retained, *_TRADABILITY_BASE_EXPLORATORY_CLAIMS])
    if matrix.status == "available":
        return _ordered_unique([*retained, "tradability_screened"])
    return _ordered_unique(retained)


def _dedupe_claim_payloads(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        claim = str(item.get("claim") or "")
        reason = str(item.get("reason_code") or item.get("blocked_reason") or "")
        key = (claim, reason)
        if key in seen:
            continue
        seen.add(key)
        output.append(_json_safe(dict(item)))
    return output


def evaluate_research_gates(
    dataset: ResearchDataset,
    request: ResearchDatasetRequest | Mapping[str, Any],
    *,
    reader_results: Mapping[str, ReaderResult] | None = None,
) -> ResearchDataset:
    """执行 S04 quality / adjustment / label window gate 并返回更新后的数据集。"""

    req = _coerce_research_dataset_request(request)
    parsed = _ParsedRequest.from_request(req)
    effective_reader_results = dict(reader_results or dataset.reader_results)
    existing_issues = list(dataset.issues)
    s04_issues: list[ResearchDatasetIssue] = []
    s04_checks: list[dict[str, Any]] = []
    limitations = _active_limitations_without_s03_gate_placeholder(dataset.known_limitations)
    prices = dataset.prices.copy() if dataset.prices is not None else None
    calendar = list(dataset.calendar)
    close_df = dataset.close_df

    if parsed.issues:
        s04_issues.extend(parsed.issues)

    quality_result = evaluate_quality_gate(effective_reader_results, dataset.metadata)
    s04_checks.append(quality_result["check"])
    s04_issues.extend(quality_result["issues"])
    limitations.extend(quality_result["limitations"])

    adjustment_result = evaluate_adjustment_gate(
        prices,
        req.adjustment_policy,
        dataset.metadata,
        reader_results=effective_reader_results,
    )
    s04_checks.append(adjustment_result["check"])
    s04_issues.extend(adjustment_result["issues"])

    label_result = evaluate_label_window_gate(prices, req)
    s04_checks.append(label_result["check"])
    s04_issues.extend(label_result["issues"])
    limitations.extend(label_result["limitations"])

    if label_result["metadata"].get("label_status") == "truncated":
        prices, calendar, close_df, rebuild_issues = _apply_label_truncation(
            prices,
            calendar,
            req,
            parsed,
            label_result["metadata"].get("label_available_end"),
            dataset.universe_symbols,
        )
        s04_issues.extend(rebuild_issues)

    all_issues = existing_issues + s04_issues
    result_status = _aggregate_s04_dataset_status(dataset.status, s04_issues, all_issues)
    allowed_claims = _s04_allowed_claims(req, result_status, s04_checks)
    metadata = _merge_s04_metadata(
        dataset.metadata,
        status=result_status,
        quality=quality_result["metadata"],
        adjustment=adjustment_result["metadata"],
        label_window=label_result["metadata"],
        known_limitations=limitations,
        allowed_claims=allowed_claims,
        issues=all_issues,
    )
    gate_result = GateResult(
        status=_s04_gate_status(result_status, s04_checks, all_issues),
        issues=all_issues,
        checks=_merge_gate_checks(dataset.gate_result.checks, s04_checks),
        remediation_spec=dataset.remediation_spec,
    )
    return ResearchDataset(
        status=result_status,
        prices=prices,
        close_df=close_df,
        calendar=calendar,
        universe_symbols=list(dataset.universe_symbols),
        benchmark_result=dataset.benchmark_result,
        metadata=metadata,
        gate_result=gate_result,
        issues=all_issues,
        known_limitations=limitations,
        allowed_claims=allowed_claims,
        remediation_spec=dataset.remediation_spec,
        reader_results=effective_reader_results,
    )


def build_auxiliary_availability(
    reader_results: Mapping[str, Any] | None,
    requirements: Mapping[str, Any] | Sequence[str] | None = None,
    *,
    gate_result: GateResult | Mapping[str, Any] | None = None,
    universe_metadata: Mapping[str, Any] | None = None,
) -> AuxiliaryAvailabilityMatrix:
    """构建 S06 辅助数据 availability matrix。

    本函数只消费调用方传入的 reader / metadata 结果，不读取数据湖、不触发
    connector/runtime/storage，也不执行补数。
    """

    source_results = dict(reader_results or {})
    normalized_requirements = _coerce_auxiliary_requirements(requirements)
    entries: dict[str, AuxiliaryAvailabilityEntry] = {}
    for capability, requirement in normalized_requirements.items():
        source_dataset = str(requirement.get("source_dataset") or capability)
        result = source_results.get(capability, source_results.get(source_dataset))
        if capability == "pit_universe":
            entry = _pit_universe_availability_entry(capability, requirement, result, universe_metadata)
        elif capability == "label_quality":
            entry = _label_quality_availability_entry(capability, requirement, result, gate_result)
        else:
            entry = _availability_entry_from_reader(capability, requirement, result)
        entries[capability] = entry
    return AuxiliaryAvailabilityMatrix(entries=entries)


def evaluate_allowed_claims(
    auxiliary_availability: AuxiliaryAvailabilityMatrix | Mapping[str, Any],
    requested_claims: Sequence[str] | None = None,
    *,
    base_allowed_claims: Sequence[str] | None = None,
    fail_on_blocked_claims: bool = False,
) -> AllowedClaimsResult:
    """根据 availability matrix 生成 allowed / blocked claims。"""

    matrix = _coerce_auxiliary_matrix(auxiliary_availability)
    requested = _ordered_unique(
        list(requested_claims)
        if requested_claims is not None
        else [claim for defaults in _AUXILIARY_CAPABILITY_DEFAULTS.values() for claim in defaults["required_for_claims"]]
    )
    base_allowed = _ordered_unique(list(base_allowed_claims or _AUXILIARY_BASE_ALLOWED_CLAIMS))
    blocked: list[dict[str, Any]] = []
    blocked_claims: set[str] = set()
    allowed: list[str] = []
    for claim in requested:
        missing_capability = _first_missing_capability_for_claim(claim, matrix)
        if missing_capability:
            entry = matrix.entries[missing_capability]
            blocked.append(_blocked_claim_payload(claim, entry))
            blocked_claims.add(claim)
        else:
            allowed.append(claim)

    final_allowed = _ordered_unique([*base_allowed, *allowed])
    final_allowed = [claim for claim in final_allowed if claim not in blocked_claims]
    limitations = [_limitation_from_blocked_claim(item) for item in blocked]
    return AllowedClaimsResult(
        allowed_claims=final_allowed,
        blocked_claims=blocked,
        known_limitations=limitations,
        auxiliary_availability=matrix.to_dict(),
        gate_status=GateStatus.FAIL.value if fail_on_blocked_claims and blocked else GateStatus.PASS.value,
    )


def merge_auxiliary_claims_into_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    claims_result: AllowedClaimsResult | Mapping[str, Any],
) -> dict[str, Any]:
    """把 S06 availability / claims 合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    result = _coerce_allowed_claims_result(claims_result)
    merged_limitations = _dedupe_json_safe(
        [
            *list(base.get("known_limitations") or []),
            *list(result.known_limitations),
        ]
    )
    base["auxiliary_availability"] = _json_safe(result.auxiliary_availability)
    base["allowed_claims"] = list(result.allowed_claims)
    base["blocked_claims"] = _json_safe(result.blocked_claims)
    base["known_limitations"] = merged_limitations
    for capability, entry in result.auxiliary_availability.items():
        if isinstance(entry, Mapping):
            status_field = _AUXILIARY_CAPABILITY_DEFAULTS.get(capability, {}).get("status_field")
            if status_field:
                base[str(status_field)] = entry.get("status", "")
    return metadata_to_dict(base)


def apply_auxiliary_data_contract(
    dataset: ResearchDataset,
    *,
    requirements: Mapping[str, Any] | Sequence[str] | None = None,
    requested_claims: Sequence[str] | None = None,
    fail_on_blocked_claims: bool = False,
) -> ResearchDataset:
    """将 S06 辅助数据合同应用到既有 ResearchDataset。"""

    matrix = build_auxiliary_availability(
        dataset.reader_results,
        requirements,
        gate_result=dataset.metadata,
        universe_metadata=dataset.metadata.get("universe") if isinstance(dataset.metadata.get("universe"), Mapping) else dataset.metadata,
    )
    claims = evaluate_allowed_claims(
        matrix,
        requested_claims,
        base_allowed_claims=dataset.allowed_claims,
        fail_on_blocked_claims=fail_on_blocked_claims,
    )
    metadata = merge_auxiliary_claims_into_metadata(dataset.metadata, claims)
    status = ResearchDatasetStatus.GATE_FAILED.value if claims.gate_status == GateStatus.FAIL.value else dataset.status
    checks = _merge_gate_checks(dataset.gate_result.checks, [{"name": "auxiliary_claims_gate", "status": claims.gate_status}])
    gate_result = GateResult(
        status=GateStatus.FAIL.value if claims.gate_status == GateStatus.FAIL.value else dataset.gate_result.status,
        issues=list(dataset.gate_result.issues),
        checks=checks,
        remediation_spec=dataset.gate_result.remediation_spec,
    )
    return ResearchDataset(
        status=status,
        prices=dataset.prices,
        close_df=dataset.close_df,
        calendar=list(dataset.calendar),
        universe_symbols=list(dataset.universe_symbols),
        benchmark_result=dataset.benchmark_result,
        metadata=metadata,
        gate_result=gate_result,
        issues=list(dataset.issues),
        known_limitations=list(metadata.get("known_limitations") or []),
        allowed_claims=list(claims.allowed_claims),
        blocked_claims=list(claims.blocked_claims),
        auxiliary_availability=dict(claims.auxiliary_availability),
        remediation_spec=dataset.remediation_spec,
        reader_results=dict(dataset.reader_results),
    )


def build_liquidity_capacity_inputs(
    research_metadata: Mapping[str, Any] | None,
    execution_frame: pd.DataFrame | Mapping[str, Any] | None = None,
    *,
    required: bool = True,
) -> dict[str, Any]:
    """构建 CR011-S07 liquidity / capacity input availability，不触发任何外部读取。"""

    metadata = metadata_to_dict(research_metadata or {})
    declared_inputs = metadata.get("liquidity_capacity_inputs")
    if not isinstance(declared_inputs, Mapping):
        declared_inputs = metadata.get("liquidity_inputs") if isinstance(metadata.get("liquidity_inputs"), Mapping) else {}
    source_payload = {**metadata, **dict(declared_inputs)}
    frame = execution_frame if isinstance(execution_frame, pd.DataFrame) else None
    frame_payload = dict(execution_frame) if isinstance(execution_frame, Mapping) else {}

    availability: dict[str, dict[str, Any]] = {}
    missing_fields: list[str] = []
    missing_reasons: list[str] = []
    for field_name, aliases in _LIQUIDITY_CAPACITY_REQUIRED_INPUTS.items():
        available, source, observed_alias = _liquidity_capacity_field_available(source_payload, frame_payload, frame, aliases)
        status = "available" if available else ("required_missing" if required else "missing")
        if not available:
            missing_fields.append(field_name)
            missing_reasons.append(f"missing_liquidity_capacity_input:{field_name}")
        availability[field_name] = {
            "field": field_name,
            "status": status,
            "source": source,
            "observed_alias": observed_alias,
            "required_aliases": list(aliases),
            "missing_reason": "" if available else f"missing_liquidity_capacity_input:{field_name}",
        }

    status = "available" if not missing_fields else "blocked_missing_liquidity"
    blocked_claims = [] if status == "available" else _liquidity_capacity_blocked_claims(missing_fields)
    allowed_claims = list(_LIQUIDITY_CAPACITY_STRONG_CLAIMS[:3]) if status == "available" else []
    payload = {
        "status": status,
        "liquidity_capacity_status": status,
        "capacity_cost_status": "liquidity_inputs_available" if status == "available" else "blocked_missing_liquidity",
        "availability": availability,
        "missing_fields": missing_fields,
        "missing_reasons": missing_reasons,
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "lineage": _liquidity_capacity_lineage(metadata),
        "remediation_spec": {
            "code": "liquidity_capacity_inputs_missing" if missing_fields else "none",
            "auto_execute": False,
            "missing_fields": list(missing_fields),
            "next_action": "publish_liquidity_capacity_inputs" if missing_fields else "",
        },
        "network_calls": int(metadata.get("network_calls") or 0),
        "lake_writes": int(metadata.get("lake_writes") or 0),
        "credential_reads": int(metadata.get("credential_reads") or 0),
        "legacy_data_operations": int(metadata.get("legacy_data_operations") or 0),
        "old_report_overwrites": int(metadata.get("old_report_overwrites") or 0),
    }
    for field_name in _LIQUIDITY_CAPACITY_REQUIRED_INPUTS:
        payload[field_name] = _liquidity_capacity_payload_value(source_payload, frame_payload, frame, field_name)
    return _json_safe(payload)


def merge_capacity_cost_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    capacity_report: Mapping[str, Any],
    cost_report: Mapping[str, Any],
    claim_result: Mapping[str, Any],
) -> dict[str, Any]:
    """把 CR011-S07 capacity / cost sensitivity 合同合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    capacity = _json_safe(dict(capacity_report))
    cost = _json_safe(dict(cost_report))
    claims = _json_safe(dict(claim_result))
    merged_blocked = _dedupe_json_safe(
        [
            *list(base.get("blocked_claims") or []),
            *list(claims.get("blocked_claims") or []),
        ]
    )
    blocked_names = {
        str(item.get("claim"))
        for item in merged_blocked
        if isinstance(item, Mapping) and item.get("claim")
    }
    base["capacity_report"] = capacity
    base["cost_sensitivity_report"] = cost
    base["cost_grid_bps"] = list(cost.get("cost_grid_bps") or [])
    base["liquidity_capacity_status"] = str(
        claims.get("liquidity_capacity_status")
        or capacity.get("liquidity_capacity_status")
        or "blocked_missing_liquidity"
    )
    base["capacity_cost_status"] = str(claims.get("capacity_cost_status") or "fail")
    base["cost_sensitivity_status"] = str(
        claims.get("cost_sensitivity_status")
        or cost.get("cost_sensitivity_status")
        or "fail"
    )
    base["capacity_allowed_claims"] = [str(item) for item in claims.get("allowed_claims") or []]
    base["capacity_blocked_claims"] = [dict(item) for item in claims.get("blocked_claims") or [] if isinstance(item, Mapping)]
    base["allowed_claims"] = [
        claim
        for claim in _ordered_unique([*list(base.get("allowed_claims") or []), *base["capacity_allowed_claims"]])
        if claim not in blocked_names
    ]
    base["blocked_claims"] = merged_blocked
    base["known_limitations"] = _dedupe_json_safe(
        [
            *list(base.get("known_limitations") or []),
            *_capacity_cost_limitations(merged_blocked),
        ]
    )
    for field in ("network_calls", "lake_writes", "credential_reads", "legacy_data_operations", "old_report_overwrites"):
        base[field] = int(base.get(field) or 0)
    return metadata_to_dict(base)


def evaluate_robust_validation_claims(
    validation_summary: Mapping[str, Any],
    upstream_claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """评估 CR011-S08 五视图稳健性验证声明，不放宽上游 blocked claims。"""

    summary = _json_safe(dict(validation_summary or {}))
    upstream = _json_safe(dict(upstream_claims or {}))
    views = _robust_validation_views_by_name(summary)
    missing_views = [view_name for view_name in _ROBUST_VALIDATION_REQUIRED_VIEWS if view_name not in views]
    failed_views: list[dict[str, Any]] = []
    for view_name in _ROBUST_VALIDATION_REQUIRED_VIEWS:
        payload = views.get(view_name)
        if payload is None:
            continue
        status = str(payload.get("status") or payload.get(f"{view_name}_status") or "fail")
        if status != "pass":
            failed_views.append(
                {
                    "view": view_name,
                    "status": status,
                    "reason": str(payload.get("reason") or payload.get("missing_reason") or "view_not_pass"),
                }
            )

    upstream_blocked = _claim_entries(upstream.get("blocked_claims"))
    summary_blocked = _claim_entries(summary.get("blocked_claims"))
    validation_blocked = (
        _factor_audit_blocked_claims("missing_required_views", missing_views=missing_views, failed_views=failed_views)
        if missing_views
        else []
    )
    if failed_views:
        validation_blocked.extend(
            _factor_audit_blocked_claims("required_view_not_pass", missing_views=missing_views, failed_views=failed_views)
        )
    panel_status = str(summary.get("factor_audit_status") or "pass")
    if panel_status != "pass":
        validation_blocked.extend(
            _factor_audit_blocked_claims("factor_panel_audit_not_pass", missing_views=missing_views, failed_views=failed_views)
        )
    blocked_claims = _dedupe_json_safe([*upstream_blocked, *summary_blocked, *validation_blocked])
    blocked_names = _blocked_claim_names(blocked_claims)

    views_status = "pass" if not missing_views and not failed_views else "fail"
    if views_status != "pass" or panel_status != "pass":
        claim_gate_status = "fail"
    elif upstream_blocked or summary_blocked:
        claim_gate_status = "blocked_upstream_claims"
    else:
        claim_gate_status = "pass"

    candidate_allowed = [str(item) for item in upstream.get("allowed_claims") or [] if str(item)]
    if claim_gate_status == "pass":
        candidate_allowed.extend(_FACTOR_AUDIT_STRONG_CLAIMS)
    allowed_claims = [claim for claim in _ordered_unique(candidate_allowed) if claim not in blocked_names]

    return {
        "robust_validation_status": views_status,
        "claim_gate_status": claim_gate_status,
        "factor_audit_status": panel_status,
        "required_views": list(_ROBUST_VALIDATION_REQUIRED_VIEWS),
        "present_views": [view_name for view_name in _ROBUST_VALIDATION_REQUIRED_VIEWS if view_name in views],
        "missing_views": missing_views,
        "failed_views": failed_views,
        "upstream_blocked_claim_count": len(upstream_blocked),
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
    }


def merge_factor_audit_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    manifest: Mapping[str, Any],
    validation_summary: Mapping[str, Any],
    claim_result: Mapping[str, Any],
) -> dict[str, Any]:
    """把 CR011-S08 factor panel audit 与 robust validation 合同合并进 research metadata。"""

    base = metadata_to_dict(metadata)
    panel_manifest = _json_safe(dict(manifest or {}))
    validation = _json_safe(dict(validation_summary or {}))
    claims = _json_safe(dict(claim_result or {}))
    merged_blocked = _dedupe_json_safe(
        [
            *list(base.get("blocked_claims") or []),
            *list(claims.get("blocked_claims") or []),
        ]
    )
    blocked_names = _blocked_claim_names(merged_blocked)

    panel_stages = [str(item) for item in panel_manifest.get("stages") or []]
    missing_panel_stages = [stage for stage in _FACTOR_PANEL_REQUIRED_STAGES if stage not in panel_stages]
    panel_row_counts = dict(panel_manifest.get("row_counts") or {})
    panel_status = str(panel_manifest.get("factor_audit_status") or ("pass" if not missing_panel_stages else "fail"))

    base["factor_panel_manifest"] = panel_manifest
    base["factor_panel_manifest_path"] = str(
        panel_manifest.get("manifest_path") or panel_manifest.get("factor_panel_manifest_path") or ""
    )
    base["factor_panel_stage_count"] = len(panel_stages)
    base["factor_panel_stages"] = panel_stages
    base["factor_panel_required_stages"] = list(_FACTOR_PANEL_REQUIRED_STAGES)
    base["factor_panel_missing_stages"] = missing_panel_stages
    base["factor_panel_row_counts"] = {str(key): int(value or 0) for key, value in panel_row_counts.items()}
    base["factor_audit_status"] = panel_status
    base["robust_validation_summary"] = validation
    base["robust_validation_summary_path"] = str(validation.get("summary_path") or validation.get("robust_validation_summary_path") or "")
    base["robust_validation_status"] = str(claims.get("robust_validation_status") or validation.get("robust_validation_status") or "fail")
    base["robust_validation_views"] = list(claims.get("present_views") or validation.get("view_names") or [])
    base["robust_validation_required_views"] = list(_ROBUST_VALIDATION_REQUIRED_VIEWS)
    base["claim_gate_status"] = str(claims.get("claim_gate_status") or "fail")
    base["factor_audit_allowed_claims"] = [str(item) for item in claims.get("allowed_claims") or []]
    base["factor_audit_blocked_claims"] = [
        dict(item) for item in claims.get("blocked_claims") or [] if isinstance(item, Mapping)
    ]
    base["allowed_claims"] = [
        claim
        for claim in _ordered_unique([*list(base.get("allowed_claims") or []), *base["factor_audit_allowed_claims"]])
        if claim not in blocked_names
    ]
    base["blocked_claims"] = merged_blocked
    base["known_limitations"] = _dedupe_json_safe(
        [
            *list(base.get("known_limitations") or []),
            *_factor_audit_limitations(merged_blocked),
        ]
    )
    for field in _SAFETY_COUNTER_FIELDS:
        base[field] = int(base.get(field) or 0)
    return metadata_to_dict(base)


def build_exposure_availability_matrix(
    reader_results: Mapping[str, Any] | None,
    factor_sample: pd.DataFrame | None = None,
    *,
    universe_metadata: Mapping[str, Any] | None = None,
    decision_time: str | date | datetime | None = None,
    requested_style_factors: Sequence[str] | None = None,
) -> ExposureAvailabilityMatrix:
    """构建 CR011-S06 行业 / 市值 / 风格 PIT exposure availability。"""

    source_results = dict(reader_results or {})
    entries: dict[str, ExposureAvailabilityEntry] = {}
    for capability, requirement in _EXPOSURE_CAPABILITY_DEFAULTS.items():
        source_dataset = str(requirement.get("source_dataset") or capability)
        result = source_results.get(capability, source_results.get(source_dataset))
        entries[capability] = _exposure_entry_from_reader(
            capability,
            requirement,
            result,
            factor_sample,
            universe_metadata=universe_metadata,
            decision_time=decision_time,
            requested_style_factors=requested_style_factors,
        )
    return ExposureAvailabilityMatrix(entries=entries)


def evaluate_neutralization_claims(
    exposure_matrix: ExposureAvailabilityMatrix | Mapping[str, Any],
    requested_claims: Sequence[str] | None = None,
    *,
    factor_metrics: Mapping[str, Any] | None = None,
    research_mode: str = "exploratory",
    base_allowed_claims: Sequence[str] | None = None,
    fail_on_blocked_claims: bool = False,
) -> NeutralizationClaimGateResult:
    """根据 exposure availability 控制中性化 / pure alpha 强声明。"""

    del research_mode
    matrix = _coerce_exposure_matrix(exposure_matrix)
    metrics = dict(factor_metrics or {})
    requested = _ordered_unique(
        list(requested_claims)
        if requested_claims is not None
        else [claim for defaults in _EXPOSURE_CAPABILITY_DEFAULTS.values() for claim in defaults["required_for_claims"]]
    )
    base_allowed = _ordered_unique(list(base_allowed_claims or _EXPOSURE_BASE_ALLOWED_CLAIMS))
    blocked: list[dict[str, Any]] = []
    blocked_claims: set[str] = set()
    allowed: list[str] = []
    for claim in requested:
        missing_capability = _first_missing_exposure_capability_for_claim(claim, matrix)
        if missing_capability:
            entry = matrix.entries[missing_capability]
            blocked.append(_neutralization_blocked_claim_payload(claim, entry))
            blocked_claims.add(claim)
            continue
        if claim in _NEUTRALIZATION_METRIC_CLAIMS and _is_empty(metrics.get(claim)):
            blocked.append(
                {
                    "claim": claim,
                    "missing_capability": _primary_exposure_capability_for_claim(claim),
                    "missing_status": "metric_missing",
                    "reason": "neutralization_metric_missing",
                    "severity": "BLOCKING",
                    "source_story": "CR011-S06",
                }
            )
            blocked_claims.add(claim)
            continue
        allowed.append(claim)

    final_allowed = _ordered_unique([*base_allowed, *allowed])
    final_allowed = [claim for claim in final_allowed if claim not in blocked_claims]
    limitations = [_neutralization_limitation_from_blocked_claim(item) for item in blocked]
    return NeutralizationClaimGateResult(
        neutralization_status=_neutralization_status(blocked),
        raw_ic=_metric_value(metrics, "raw_ic"),
        industry_neutral_ic=None if "industry_neutral_ic" in blocked_claims else _metric_value(metrics, "industry_neutral_ic"),
        market_cap_neutral_ic=None if "market_cap_neutral_ic" in blocked_claims else _metric_value(metrics, "market_cap_neutral_ic"),
        style_neutral_ic=None if "style_neutral_ic" in blocked_claims else _metric_value(metrics, "style_neutral_ic"),
        allowed_claims=final_allowed,
        blocked_claims=blocked,
        known_limitations=limitations,
        exposure_availability=matrix.to_dict(),
        gate_status=GateStatus.FAIL.value if fail_on_blocked_claims and blocked else GateStatus.PASS.value,
    )


def merge_exposure_claims_into_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
    gate_result: NeutralizationClaimGateResult | Mapping[str, Any],
) -> dict[str, Any]:
    """把 CR011-S06 exposure availability / neutralization claims 合并进 metadata。"""

    base = metadata_to_dict(metadata)
    result = _coerce_neutralization_gate_result(gate_result)
    exposure_availability = _json_safe(result.exposure_availability)
    base["exposure_availability"] = exposure_availability
    base["industry_availability"] = exposure_availability.get("industry_classification", {})
    base["market_cap_availability"] = exposure_availability.get("market_cap", {})
    base["float_market_cap_availability"] = exposure_availability.get("float_market_cap", {})
    base["float_market_cap"] = base["float_market_cap_availability"]
    base["style_exposure_availability"] = exposure_availability.get("style_exposure", {})
    auxiliary = dict(base.get("auxiliary_availability") or {})
    auxiliary.update(exposure_availability)
    base["auxiliary_availability"] = auxiliary
    base["neutralization_status"] = result.neutralization_status
    base["raw_ic"] = result.raw_ic
    base["industry_neutral_ic"] = result.industry_neutral_ic
    base["market_cap_neutral_ic"] = result.market_cap_neutral_ic
    base["style_neutral_ic"] = result.style_neutral_ic
    merged_blocked = _dedupe_json_safe([*list(base.get("blocked_claims") or []), *list(result.blocked_claims)])
    blocked_claim_names = {
        str(item.get("claim"))
        for item in merged_blocked
        if isinstance(item, Mapping) and item.get("claim")
    }
    base["allowed_claims"] = [
        claim
        for claim in _ordered_unique([*list(base.get("allowed_claims") or []), *list(result.allowed_claims)])
        if claim not in blocked_claim_names
    ]
    base["blocked_claims"] = merged_blocked
    base["known_limitations"] = _dedupe_json_safe(
        [*list(base.get("known_limitations") or []), *list(result.known_limitations)]
    )
    for field in ("network_calls", "lake_writes", "credential_reads", "legacy_data_operations"):
        base[field] = int(base.get(field) or 0)
    return metadata_to_dict(base)


def evaluate_quality_gate(
    reader_results: Mapping[str, ReaderResult] | None,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """只基于 reader/catalog/metadata 评估 quality gate。"""

    source_results = dict(reader_results or {})
    statuses: list[tuple[str, str, str]] = []
    prices_result = source_results.get(DATASET_PRICES)
    if prices_result is not None:
        status, source = quality_status_from_reader_result(prices_result, None)
        statuses.append((DATASET_PRICES, status, source))
    if not statuses and metadata:
        status, source = quality_status_from_reader_result(None, dict(metadata))
        statuses.append(("metadata", status, source))
    if not statuses:
        statuses.append((DATASET_PRICES, "missing", "missing"))

    canonical_status = _worst_quality_status([item[1] for item in statuses])
    quality_source = _quality_source(statuses)
    issues: list[ResearchDatasetIssue] = []
    limitations: list[Any] = []
    if canonical_status == "fail":
        issues.append(
            ResearchDatasetIssue(
                code="quality_failed",
                dataset=DATASET_PRICES,
                message="quality_status=fail，严肃研究入口必须阻断。",
                details={"statuses": _quality_status_details(statuses)},
            )
        )
    elif canonical_status == "missing":
        issues.append(
            ResearchDatasetIssue(
                code="quality_missing",
                dataset=DATASET_PRICES,
                message="缺少 reader/catalog/metadata quality truth，禁止用旧质量报告补证。",
                details={"statuses": _quality_status_details(statuses)},
            )
        )
    elif canonical_status == "warn":
        warning = {
            "code": "quality_warn",
            "quality_status": "warn",
            "quality_source": quality_source,
            "limitation": "quality_status=warn，仅允许带限制说明继续。",
        }
        limitations.append(warning)
        issues.append(
            ResearchDatasetIssue(
                code="quality_warn",
                dataset=DATASET_PRICES,
                severity="WARNING",
                message="quality_status=warn，已写入 known_limitations。",
                details={"statuses": _quality_status_details(statuses)},
            )
        )

    check = _gate_check(
        "quality_gate",
        "fail" if canonical_status in {"fail", "missing"} else "warn" if canonical_status == "warn" else "pass",
        "quality_failed" if canonical_status == "fail" else "quality_missing" if canonical_status == "missing" else "quality_warn" if canonical_status == "warn" else "quality_pass",
        "ERROR" if canonical_status in {"fail", "missing"} else "WARNING" if canonical_status == "warn" else "INFO",
        f"quality gate status={canonical_status}",
        {"quality_status": canonical_status, "quality_source": quality_source, "statuses": _quality_status_details(statuses)},
    )
    return {
        "check": check,
        "issues": issues,
        "limitations": limitations,
        "metadata": {
            "quality_status": canonical_status,
            "quality_source": quality_source,
        },
    }


def extract_adjustment_policies(
    prices: pd.DataFrame | None,
    metadata: Mapping[str, Any] | None,
    request_policy: str | None = None,
    *,
    reader_results: Mapping[str, ReaderResult] | None = None,
) -> dict[str, Any]:
    """抽取数据侧复权口径；request_policy 只作为期望值，不作为数据证明。"""

    del request_policy
    values: set[str] = set()
    missing_sample_count = 0
    row_count = 0
    sources: list[str] = []
    if prices is not None:
        row_count = int(len(prices))
        policy_columns = [
            column
            for column in ("research_adjustment_policy", "adjustment_policy", "policy")
            if column in prices.columns
        ]
        if policy_columns:
            has_policy = pd.Series(False, index=prices.index)
            for column in policy_columns:
                series = prices[column]
                text_values = series.fillna("").astype(str).str.strip()
                values.update(item for item in text_values.tolist() if item)
                has_policy = has_policy | text_values.ne("")
                sources.append(f"prices.{column}")
            missing_sample_count = int((~has_policy).sum())
        else:
            missing_sample_count = int(len(prices))

        for attr_name in ("research_adjustment_policy", "adjustment_policy", "policy"):
            attr_policy = _normalize_policy_value(prices.attrs.get(attr_name))
            if attr_policy:
                values.add(attr_policy)
                sources.append(f"prices.attrs.{attr_name}")

    metadata_values = _adjustment_values_from_metadata(metadata)
    if metadata_values:
        values.update(metadata_values)
        sources.append("metadata.adjustment")

    for dataset, result in sorted((reader_results or {}).items()):
        if dataset != DATASET_PRICES:
            continue
        entry = result.catalog_entry
        entry_values = _adjustment_values_from_catalog_entry(entry)
        if entry_values:
            values.update(entry_values)
            sources.append(f"catalog_entry:{dataset}")

    return {
        "policies_seen": sorted(values),
        "sources": sorted(set(sources)),
        "missing_sample_count": int(missing_sample_count),
        "row_count": int(row_count),
    }


def evaluate_adjustment_gate(
    prices: pd.DataFrame | None,
    request_policy: str | None,
    metadata: Mapping[str, Any] | None,
    *,
    reader_results: Mapping[str, ReaderResult] | None = None,
) -> dict[str, Any]:
    """评估单一复权口径 gate。"""

    requested = _normalize_policy_value(request_policy)
    extracted = extract_adjustment_policies(prices, metadata, requested, reader_results=reader_results)
    policies_seen = extracted["policies_seen"]
    issues: list[ResearchDatasetIssue] = []
    status = "pass"
    code = "adjustment_policy_pass"
    message = "adjustment policy gate passed"
    if not requested:
        status = "fail"
        code = "adjustment_policy_missing"
        message = "ResearchDatasetRequest.adjustment_policy 缺失。"
    elif extracted["missing_sample_count"] > 0 and not policies_seen:
        status = "fail"
        code = "adjustment_policy_missing"
        message = "prices/catalog/metadata 未提供数据侧 adjustment_policy。"
    elif len(policies_seen) > 1:
        status = "fail"
        code = "adjustment_policy_mixed"
        message = "同一 ResearchDataset 出现多个 adjustment_policy。"
    elif policies_seen and policies_seen[0] != requested:
        status = "fail"
        code = "adjustment_policy_mismatch"
        message = "数据侧 adjustment_policy 与 request 不一致。"
    elif not policies_seen:
        status = "fail"
        code = "adjustment_policy_missing"
        message = "缺少数据侧 adjustment_policy 证明。"

    if status == "fail":
        issues.append(
            ResearchDatasetIssue(
                code=code,
                dataset=DATASET_PRICES,
                field="adjustment_policy",
                message=message,
                details={"request_policy": requested, **extracted},
            )
        )
    metadata_payload = {
        "adjustment_policy": policies_seen[0] if len(policies_seen) == 1 else None,
        "request_policy": requested,
        "policies_seen": policies_seen,
        "missing_sample_count": extracted["missing_sample_count"],
        "sources": extracted["sources"],
        "adjustment_status": "available" if status == "pass" else "failed",
    }
    policy_gate_input: Mapping[str, Any] | pd.DataFrame | None = metadata
    if prices is not None:
        policy_gate_input = prices.copy(deep=False)
        if metadata:
            policy_gate_input.attrs.update(metadata_to_dict(metadata))
    policy_gate = single_policy_gate(policy_gate_input, requested)
    metadata_payload["single_policy_gate_status"] = (
        "pass" if status == "pass" and policy_gate.passed else "blocked"
    )
    metadata_payload["single_policy_gate_reason"] = "" if status == "pass" else code
    return {
        "check": _gate_check(
            "adjustment_gate",
            status,
            code,
            "ERROR" if status == "fail" else "INFO",
            message,
            metadata_payload,
        ),
        "issues": issues,
        "metadata": metadata_payload,
    }


def evaluate_label_window_gate(
    prices: pd.DataFrame | None,
    request: ResearchDatasetRequest | Mapping[str, Any],
) -> dict[str, Any]:
    """按可用交易日和 forward horizon 评估 label window gate。"""

    req = _coerce_research_dataset_request(request)
    parsed = _ParsedRequest.from_request(req)
    horizon = int(req.forward_return_horizon) if isinstance(req.forward_return_horizon, int) else 0
    metadata = {
        "forward_return_horizon": req.forward_return_horizon,
        "requested_decision_end": parsed.end_date,
        "label_available_end": None,
        "label_status": "empty",
        "truncated_sample_count": 0,
        "truncated_date_count": 0,
        "label_unavailable_start": None,
    }
    issues: list[ResearchDatasetIssue] = []
    limitations: list[Any] = []

    if prices is None or "trade_date" not in prices.columns:
        truncated_count = 0 if prices is None else int(len(prices))
        metadata["truncated_sample_count"] = truncated_count
        issue = ResearchDatasetIssue(
            code="label_window_empty",
            dataset=DATASET_PRICES,
            field="trade_date",
            message="缺少 prices.trade_date，无法计算 forward return label window。",
            details=metadata,
        )
        issues.append(issue)
        return _label_gate_result("fail", "label_window_empty", issue.message, metadata, issues, limitations)

    work = prices.copy()
    work["_s04_trade_date"] = pd.to_datetime(work["trade_date"], errors="coerce").dt.date
    valid_dates = sorted({item for item in work["_s04_trade_date"].dropna().tolist()})
    requested_end = parsed.end or (valid_dates[-1] if valid_dates else None)
    metadata["requested_decision_end"] = requested_end.isoformat() if requested_end else parsed.end_date
    if horizon < 1 or len(valid_dates) <= horizon:
        decision_mask = work["_s04_trade_date"].notna()
        if requested_end is not None:
            decision_mask &= work["_s04_trade_date"] <= requested_end
        metadata["truncated_sample_count"] = int(decision_mask.sum())
        metadata["truncated_date_count"] = len([item for item in valid_dates if requested_end is None or item <= requested_end])
        issue = ResearchDatasetIssue(
            code="label_window_empty",
            dataset=DATASET_PRICES,
            field="forward_return_horizon",
            message="可用交易日数量不足以生成任何完整 forward return 标签。",
            details=metadata,
        )
        issues.append(issue)
        return _label_gate_result("fail", "label_window_empty", issue.message, metadata, issues, limitations)

    label_available_end = valid_dates[-horizon - 1]
    metadata["label_available_end"] = label_available_end.isoformat()
    if requested_end is None or requested_end <= label_available_end:
        metadata["label_status"] = "available"
        return _label_gate_result("pass", "label_window_available", "label window available", metadata, issues, limitations)

    unavailable_dates = [item for item in valid_dates if label_available_end < item <= requested_end]
    unavailable_mask = (work["_s04_trade_date"] > label_available_end) & (work["_s04_trade_date"] <= requested_end)
    metadata["truncated_sample_count"] = int(unavailable_mask.sum())
    metadata["truncated_date_count"] = len(unavailable_dates)
    metadata["label_unavailable_start"] = unavailable_dates[0].isoformat() if unavailable_dates else None

    if req.analysis_mode == "exploratory":
        metadata["label_status"] = "truncated"
        limitation = {
            "code": "label_window_truncated",
            "label_available_end": metadata["label_available_end"],
            "truncated_sample_count": metadata["truncated_sample_count"],
            "truncated_date_count": metadata["truncated_date_count"],
            "allowed_claims": ["framework_validation", "exploratory_analysis"],
        }
        limitations.append(limitation)
        issues.append(
            ResearchDatasetIssue(
                code="label_window_truncated",
                dataset=DATASET_PRICES,
                severity="WARNING",
                message="探索模式已截断末端 label window 不足样本。",
                details=metadata,
            )
        )
        return _label_gate_result("warn", "label_window_truncated", "label window truncated for exploratory mode", metadata, issues, limitations)

    metadata["label_status"] = "insufficient"
    issue = ResearchDatasetIssue(
        code="label_window_insufficient",
        dataset=DATASET_PRICES,
        field="forward_return_horizon",
        message="严肃研究模式下 label window 不足，禁止继续声明 available。",
        details=metadata,
    )
    issues.append(issue)
    return _label_gate_result("fail", "label_window_insufficient", issue.message, metadata, issues, limitations)


def apply_label_window_policy(
    dataset: ResearchDataset,
    label_result: Mapping[str, Any],
    request: ResearchDatasetRequest | Mapping[str, Any],
) -> ResearchDataset:
    """单独应用 label 截断策略；严肃失败路径保持原数据并返回 gate_failed。"""

    req = _coerce_research_dataset_request(request)
    parsed = _ParsedRequest.from_request(req)
    metadata = dict(label_result.get("metadata") or {})
    if metadata.get("label_status") != "truncated":
        return dataset
    prices, calendar, close_df, rebuild_issues = _apply_label_truncation(
        dataset.prices,
        dataset.calendar,
        req,
        parsed,
        metadata.get("label_available_end"),
        dataset.universe_symbols,
    )
    issues = list(dataset.issues) + rebuild_issues
    dataset.prices = prices
    dataset.calendar = calendar
    dataset.close_df = close_df
    dataset.issues = issues
    return dataset


@dataclass(frozen=True, slots=True)
class _ParsedRequest:
    start_date: str
    end_date: str
    start: date | None
    end: date | None
    issues: tuple[ResearchDatasetIssue, ...] = ()

    @classmethod
    def from_request(cls, req: ResearchDatasetRequest) -> "_ParsedRequest":
        issues: list[ResearchDatasetIssue] = []
        start = _parse_request_date(req.start_date, "start_date", issues)
        end = _parse_request_date(req.end_date, "end_date", issues)
        if start is not None and end is not None and start > end:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_date_range",
                    field="start_date",
                    message="start_date 不得晚于 end_date。",
                )
            )
        if req.lake_root is None:
            issues.append(
                ResearchDatasetIssue(
                    code="lake_root_required",
                    field="lake_root",
                    message="ResearchDatasetRequest.lake_root 必须显式传入，禁止 env fallback。",
                )
            )
        elif _is_repo_data_path(req.lake_root):
            issues.append(
                ResearchDatasetIssue(
                    code="repo_data_reference_only",
                    field="lake_root",
                    message="repo-relative data / data/** 只能作为历史引用，禁止作为 research lake_root。",
                )
            )
        if not isinstance(req.forward_return_horizon, int) or req.forward_return_horizon < 1:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_forward_return_horizon",
                    field="forward_return_horizon",
                    message="forward_return_horizon 必须为 >= 1 的整数。",
                )
            )
        if req.universe_mode not in _VALID_UNIVERSE_MODES:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_universe_mode",
                    field="universe_mode",
                    message=f"universe_mode 必须属于 {sorted(_VALID_UNIVERSE_MODES)}。",
                )
            )
        if req.analysis_mode not in _VALID_ANALYSIS_MODES:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_analysis_mode",
                    field="analysis_mode",
                    message=f"analysis_mode 必须属于 {sorted(_VALID_ANALYSIS_MODES)}。",
                )
            )
        if req.realism_mode is not None and req.realism_mode not in _VALID_REALISM_MODES:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_realism_mode",
                    field="realism_mode",
                    message=f"realism_mode 必须属于 {sorted(_VALID_REALISM_MODES)}。",
                )
            )
        if isinstance(req.benchmark_policy, str) and req.benchmark_policy not in _VALID_BENCHMARK_POLICIES:
            issues.append(
                ResearchDatasetIssue(
                    code="invalid_benchmark_policy",
                    field="benchmark_policy",
                    message=f"benchmark_policy 必须属于 {sorted(_VALID_BENCHMARK_POLICIES)} 或 BenchmarkPolicy / Mapping。",
                )
            )
        return cls(
            start_date=start.isoformat() if start else "",
            end_date=end.isoformat() if end else "",
            start=start,
            end=end,
            issues=tuple(issues),
        )


def _coerce_research_dataset_request(request: ResearchDatasetRequest | Mapping[str, Any]) -> ResearchDatasetRequest:
    if isinstance(request, ResearchDatasetRequest):
        return request
    values = dict(request)
    if "universe_mode" in values:
        values["universe_mode"] = _normalize_universe_mode(values["universe_mode"])
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    return ResearchDatasetRequest(**values)


def _research_reader_datasets(req: ResearchDatasetRequest, require_index_members: bool) -> tuple[str, ...]:
    datasets = [DATASET_PRICES, DATASET_TRADE_CALENDAR]
    if require_index_members or req.realism_mode == "production_strict":
        datasets.append(DATASET_INDEX_MEMBERS)
    if req.realism_mode == "production_strict":
        datasets.extend((DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC))
    if req.realism_mode == "production_strict":
        datasets.extend(_W3_RESEARCH_DATASETS)
    return tuple(dict.fromkeys(datasets))


def _normalize_universe_mode(value: Any) -> str:
    text = str(value or "").strip()
    return _UNIVERSE_MODE_ALIASES.get(text, text)


def _parse_request_date(value: str | date | datetime | None, field_name: str, issues: list[ResearchDatasetIssue]) -> date | None:
    if value is None:
        issues.append(
            ResearchDatasetIssue(
                code="required_field_missing",
                field=field_name,
                message=f"{field_name} 必须显式传入。",
            )
        )
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        parsed = pd.to_datetime(pd.Series([value]), errors="coerce")
    except Exception:
        parsed = pd.Series([pd.NaT])
    if parsed.isna().iloc[0]:
        issues.append(
            ResearchDatasetIssue(
                code="invalid_date",
                field=field_name,
                message=f"{field_name} 必须是可解析日期。",
            )
        )
        return None
    return parsed.dt.date.iloc[0]


def _is_repo_data_path(value: str | Path | None) -> bool:
    if value is None:
        return False
    path = Path(value)
    return not path.is_absolute() and (path.parts == ("data",) or path.parts[:1] == ("data",))


def _available_frame(result: ReaderResult | None) -> pd.DataFrame | None:
    if result is None or result.status != "available" or result.frame is None:
        return None
    return result.frame.copy()


def _pit_status_normalized_reader_result(result: ReaderResult | None) -> ReaderResult | None:
    """兼容 CR011 `pit_status=pass` 输入，同时不修改原 reader result。"""

    if result is None or result.frame is None or "pit_status" not in result.frame.columns:
        return result
    frame = result.frame.copy()
    frame["pit_status"] = frame["pit_status"].map(
        lambda value: PIT_STATUS_AVAILABLE if str(value).strip() == "pass" else value
    )
    return ReaderResult(
        status=result.status,
        frame=frame,
        issues=list(result.issues),
        catalog_entry=result.catalog_entry,
        remediation_spec=dict(result.remediation_spec),
    )


def _evaluate_pit_lifecycle_gate(
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    calendar: Sequence[date],
    universe_resolution: UniverseResolution,
    index_members_result: ReaderResult | None,
    stock_lifecycle_result: ReaderResult | None,
) -> _PitLifecycleGate:
    """评估 CR011-S02 的 PIT as-of 与股票生命周期 gate。"""

    decision_time = _decision_time(parsed, calendar)
    strict = req.realism_mode == "production_strict"
    universe_meta = universe_resolution.metadata
    if not strict:
        survivorship_bias_note = str(getattr(universe_meta, "survivorship_bias_note", "") or "")
        return _PitLifecycleGate(
            metadata={
                "universe": {
                    "universe_mode": getattr(universe_meta, "universe_mode", req.universe_mode),
                    "is_pit_universe": bool(getattr(universe_meta, "is_pit_universe", False)),
                    "pit_status": str(getattr(universe_meta, "pit_status", "") or ""),
                    "as_of_join_violation_count": 0,
                    "survivorship_bias_note": survivorship_bias_note,
                },
                "lifecycle": {
                    "lifecycle_status": "not_evaluated",
                    "lifecycle_missing_count": 0,
                    "lifecycle_blocked_count": 0,
                    "as_of_join_violation_count": 0,
                },
                "as_of_join_violation_count": 0,
                "lifecycle_status": "not_evaluated",
            },
            known_limitations=[] if not survivorship_bias_note else [
                {
                    "code": "fixed_snapshot_survivorship_bias",
                    "survivorship_bias_note": survivorship_bias_note,
                }
            ],
            checks=[],
        )
    index_frame = _available_frame(index_members_result)
    lifecycle_frame = _available_frame(stock_lifecycle_result)
    asof_violations = _asof_join_violation_count(index_frame, decision_time, ("effective_date", "available_at"))
    lifecycle_metadata, lifecycle_issues = _stock_lifecycle_metadata(
        lifecycle_frame,
        stock_lifecycle_result,
        symbols=list(universe_resolution.symbols) or list(req.symbols or ()),
        decision_time=decision_time,
        strict=strict,
    )
    asof_violations += int(lifecycle_metadata.get("as_of_join_violation_count", 0) or 0)

    issues: list[ResearchDatasetIssue] = list(lifecycle_issues)
    pit_status = str(getattr(universe_meta, "pit_status", "") or "")
    pit_ok = (
        req.universe_mode == "pit_required"
        and bool(getattr(universe_meta, "is_pit_universe", False))
        and pit_status in {"pass", PIT_STATUS_AVAILABLE}
        and asof_violations == 0
    )
    lifecycle_ok = lifecycle_metadata.get("lifecycle_status") == "pass"
    if asof_violations:
        issues.append(
            ResearchDatasetIssue(
                code="as_of_join_violation",
                dataset=DATASET_INDEX_MEMBERS,
                message="PIT membership 或 stock lifecycle 存在 available_at/effective_date 晚于 decision_time 的记录。",
                details={
                    "as_of_join_violation_count": asof_violations,
                    "decision_time": "" if decision_time is None else decision_time.isoformat(),
                },
            )
        )
    if strict and not pit_ok:
        issues.append(
            ResearchDatasetIssue(
                code="production_strict_pit_lifecycle_gate_failed",
                dataset=DATASET_INDEX_MEMBERS,
                message="production_strict 必须同时满足 PIT universe、pit_status、as-of 与 lifecycle gate。",
                details={
                    "universe_mode": "pit" if req.universe_mode == "pit_required" else req.universe_mode,
                    "is_pit_universe": bool(getattr(universe_meta, "is_pit_universe", False)),
                    "pit_status": pit_status,
                    "as_of_join_violation_count": asof_violations,
                    "lifecycle_status": lifecycle_metadata.get("lifecycle_status"),
                },
            )
        )
    if strict and not lifecycle_ok:
        issues.append(
            ResearchDatasetIssue(
                code=str(lifecycle_metadata.get("lifecycle_status") or "lifecycle_missing"),
                dataset=DATASET_STOCK_BASIC,
                message="production_strict 必须具备 pass 状态的股票生命周期 gate。",
                details=lifecycle_metadata,
            )
        )

    survivorship_bias_note = str(getattr(universe_meta, "survivorship_bias_note", "") or "")
    limitations: list[Any] = []
    if survivorship_bias_note:
        limitations.append(
            {
                "code": "fixed_snapshot_survivorship_bias",
                "survivorship_bias_note": survivorship_bias_note,
            }
        )
    if lifecycle_metadata.get("lifecycle_status") != "pass":
        limitations.append(
            {
                "code": str(lifecycle_metadata.get("lifecycle_status") or "lifecycle_missing"),
                "dataset": DATASET_STOCK_BASIC,
                "lifecycle_missing_count": lifecycle_metadata.get("lifecycle_missing_count", 0),
                "lifecycle_blocked_count": lifecycle_metadata.get("lifecycle_blocked_count", 0),
            }
        )

    metadata = {
        "universe": {
            "universe_mode": "pit" if req.universe_mode == "pit_required" and bool(getattr(universe_meta, "is_pit_universe", False)) else getattr(universe_meta, "universe_mode", req.universe_mode),
            "is_pit_universe": bool(getattr(universe_meta, "is_pit_universe", False)),
            "pit_status": pit_status,
            "as_of_join_violation_count": asof_violations,
            "survivorship_bias_note": survivorship_bias_note,
        },
        "lifecycle": lifecycle_metadata,
        "as_of_join_violation_count": asof_violations,
        "lifecycle_status": lifecycle_metadata.get("lifecycle_status", "not_evaluated"),
    }
    checks = [
        {
            "name": "pit_lifecycle_gate",
            "status": "pass" if pit_ok and lifecycle_ok else "fail" if strict else "warn",
            "code": "pit_lifecycle_gate",
            "severity": "INFO" if pit_ok and lifecycle_ok else "ERROR" if strict else "WARNING",
            "message": "PIT universe 与股票生命周期 gate 评估结果。",
            "details": metadata,
        }
    ]
    return _PitLifecycleGate(metadata=metadata, issues=issues, known_limitations=limitations, checks=checks)


def _stock_lifecycle_metadata(
    frame: pd.DataFrame | None,
    result: ReaderResult | None,
    *,
    symbols: Sequence[str],
    decision_time: date | None,
    strict: bool,
) -> tuple[dict[str, Any], list[ResearchDatasetIssue]]:
    symbol_set = {str(symbol).strip() for symbol in symbols if str(symbol).strip()}
    base = {
        "lifecycle_status": "not_evaluated",
        "lifecycle_missing_count": 0,
        "lifecycle_blocked_count": 0,
        "listing_days_min": None,
        "as_of_join_violation_count": 0,
        "blocked_symbols": [],
        "missing_symbols": [],
        "list_status_values": [],
    }
    if frame is None or frame.empty:
        issue_details = {"reader_status": None if result is None else result.status}
        return (
            {
                **base,
                "lifecycle_status": "lifecycle_missing",
                "lifecycle_missing_count": len(symbol_set) if symbol_set else 1,
            },
            [
                ResearchDatasetIssue(
                    code="lifecycle_missing",
                    dataset=DATASET_STOCK_BASIC,
                    severity="ERROR" if strict else "WARNING",
                    message="stock_basic lifecycle 不可用。",
                    details=issue_details,
                )
            ],
        )

    work = frame.copy()
    if "ts_code" in work.columns and "symbol" not in work.columns:
        work["symbol"] = work["ts_code"]
    required_columns = ("symbol", "list_date", "list_status", "available_at")
    missing_columns = [column for column in required_columns if column not in work.columns]
    if missing_columns:
        return (
            {
                **base,
                "lifecycle_status": "lifecycle_missing",
                "lifecycle_missing_count": len(symbol_set) if symbol_set else len(work),
                "missing_columns": missing_columns,
            },
            [
                ResearchDatasetIssue(
                    code="lifecycle_missing",
                    dataset=DATASET_STOCK_BASIC,
                    severity="ERROR" if strict else "WARNING",
                    message="stock_basic 缺少 lifecycle 必需字段。",
                    details={"missing_columns": missing_columns},
                )
            ],
        )

    work["symbol"] = work["symbol"].astype("string").str.strip()
    if symbol_set:
        work = work[work["symbol"].isin(symbol_set)].copy()
    available_symbols = {str(symbol) for symbol in work["symbol"].dropna().tolist() if str(symbol)}
    missing_symbols = sorted(symbol_set - available_symbols)
    list_dates = _series_to_dates(work["list_date"])
    delist_dates = _series_to_dates(work["delist_date"]) if "delist_date" in work.columns else pd.Series(pd.NaT, index=work.index)
    available_at = _series_to_dates(work["available_at"])
    status_values = sorted({str(value).strip() for value in work["list_status"].dropna().tolist() if str(value).strip()})
    normalized_status = work["list_status"].map(_normalize_list_status)
    blocked_mask = pd.Series(False, index=work.index)
    missing_mask = list_dates.isna() | available_at.isna() | normalized_status.eq("unknown")
    if decision_time is not None:
        blocked_mask = blocked_mask | (list_dates > decision_time)
        blocked_mask = blocked_mask | (delist_dates.notna() & (delist_dates <= decision_time))
        asof_mask = (available_at > decision_time)
    else:
        asof_mask = pd.Series(False, index=work.index)
    blocked_mask = blocked_mask | normalized_status.ne("active")
    blocked_symbols = sorted({str(symbol) for symbol in work.loc[blocked_mask.fillna(False), "symbol"].dropna().tolist() if str(symbol)})
    asof_count = int(asof_mask.fillna(False).sum())
    lifecycle_missing_count = len(missing_symbols) + int(missing_mask.fillna(False).sum())
    lifecycle_blocked_count = len(blocked_symbols)
    listing_days_min = None
    if decision_time is not None and list_dates.notna().any():
        listing_days = [(decision_time - item).days for item in list_dates.dropna().tolist() if item <= decision_time]
        if listing_days:
            listing_days_min = int(min(listing_days))
    if lifecycle_missing_count:
        lifecycle_status = "lifecycle_missing"
    elif asof_count:
        lifecycle_status = "as_of_join_violation"
    elif lifecycle_blocked_count:
        lifecycle_status = "lifecycle_blocked"
    else:
        lifecycle_status = "pass"
    metadata = {
        **base,
        "lifecycle_status": lifecycle_status,
        "lifecycle_missing_count": lifecycle_missing_count,
        "lifecycle_blocked_count": lifecycle_blocked_count,
        "listing_days_min": listing_days_min,
        "as_of_join_violation_count": asof_count,
        "blocked_symbols": blocked_symbols,
        "missing_symbols": missing_symbols,
        "list_status_values": status_values,
    }
    issues: list[ResearchDatasetIssue] = []
    if lifecycle_missing_count:
        issues.append(
            ResearchDatasetIssue(
                code="lifecycle_missing",
                dataset=DATASET_STOCK_BASIC,
                severity="ERROR" if strict else "WARNING",
                message="stock_basic lifecycle 覆盖或必填字段不完整。",
                details=metadata,
            )
        )
    if lifecycle_blocked_count:
        issues.append(
            ResearchDatasetIssue(
                code="lifecycle_blocked",
                dataset=DATASET_STOCK_BASIC,
                severity="ERROR" if strict else "WARNING",
                message="存在未上市、已退市、暂停或未知状态股票。",
                details=metadata,
            )
        )
    return metadata, issues


def _decision_time(parsed: _ParsedRequest, calendar: Sequence[date]) -> date | None:
    if calendar:
        return max(calendar)
    return parsed.end or parsed.start


def _asof_join_violation_count(frame: pd.DataFrame | None, decision_time: date | None, fields: Sequence[str]) -> int:
    if frame is None or frame.empty or decision_time is None:
        return 0
    work = frame.copy()
    if "trade_date" in work.columns:
        decisions = _series_to_dates(work["trade_date"])
    else:
        decisions = pd.Series([decision_time] * len(work), index=work.index, dtype=object)
    violations = pd.Series(False, index=work.index)
    for field in fields:
        if field not in work.columns:
            continue
        values = _series_to_dates(work[field])
        violations = violations | (values.notna() & decisions.notna() & (values > decisions))
    return int(violations.fillna(False).sum())


def _series_to_dates(series: pd.Series) -> pd.Series:
    values = series.map(_coerce_date_value)
    return pd.Series(values, index=series.index, dtype=object)


def _coerce_date_value(value: Any) -> date | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return pd.NaT
    parsed = pd.to_datetime(pd.Series([text]), errors="coerce")
    if parsed.isna().iloc[0]:
        return pd.NaT
    return parsed.dt.date.iloc[0]


def _normalize_list_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"l", "listed", "active", "上市"}:
        return "active"
    if text in {"d", "delisted", "退市", "p", "paused", "暂停", "暂停上市"}:
        return "blocked"
    return "unknown"


def _reader_issues(dataset: str, result: ReaderResult | None, *, required: bool) -> list[ResearchDatasetIssue]:
    if result is None:
        if required:
            return [
                ResearchDatasetIssue(
                    code=f"{dataset}_required_missing",
                    dataset=dataset,
                    message=f"{dataset} reader result 缺失。",
                )
            ]
        return []
    if result.status == "available" and result.frame is not None:
        return []
    if result.status == "quality_failed":
        severity = "ERROR"
        code = f"{dataset}_quality_failed"
        message = f"{dataset} reader quality_failed。"
    elif required:
        severity = "ERROR"
        code = f"{dataset}_required_missing"
        message = f"{dataset} 是必需输入但不可用: status={result.status}。"
    else:
        severity = "WARNING"
        code = f"{dataset}_unavailable"
        message = f"{dataset} 不可用，当前请求将以显式 symbols 或限制说明继续。"
    details = {"reader_status": result.status, "reader_issues": list(result.issues)}
    return [ResearchDatasetIssue(code=code, dataset=dataset, severity=severity, message=message, details=details)]


def _production_strict_realism_issues(
    req: ResearchDatasetRequest,
    *,
    prices: pd.DataFrame | None,
    benchmark_result: Any,
    reader_results: Mapping[str, ReaderResult],
    universe_resolution: UniverseResolution,
) -> list[ResearchDatasetIssue]:
    """production_strict 下禁止把缺口降级为研究可用。"""

    issues: list[ResearchDatasetIssue] = []
    universe_meta = universe_resolution.metadata
    if not bool(getattr(universe_meta, "is_pit_universe", False)):
        issues.append(
            ResearchDatasetIssue(
                code="production_strict_pit_universe_required",
                dataset=DATASET_INDEX_MEMBERS,
                message="production_strict 必须使用 PIT universe，不能由 fixed snapshot、index_weights 或 stock_basic 替代。",
                details={
                    "universe_mode": getattr(universe_meta, "universe_mode", ""),
                    "pit_status": getattr(universe_meta, "pit_status", ""),
                },
            )
        )
    if not _benchmark_available(benchmark_result):
        issues.append(
            ResearchDatasetIssue(
                code="production_strict_real_benchmark_required",
                dataset="benchmark",
                message="production_strict 必须具备真实 benchmark。",
                details={
                    "benchmark_status": _benchmark_status(benchmark_result),
                    "benchmark_missing_reason": _benchmark_missing_reason(benchmark_result),
                },
            )
        )
    if prices is None:
        issues.append(
            ResearchDatasetIssue(
                code="production_strict_prices_required",
                dataset=DATASET_PRICES,
                message="production_strict 必须具备 prices 输入。",
            )
        )
    else:
        if "adjusted_close" not in prices.columns or "adj_factor" not in prices.columns:
            issues.append(
                ResearchDatasetIssue(
                    code="production_strict_adjustment_required",
                    dataset=DATASET_PRICES,
                    message="production_strict 必须具备复权一致性字段 adjusted_close 与 adj_factor。",
                )
            )
        if "adjustment_policy" in prices.columns:
            policies = sorted({str(value) for value in prices["adjustment_policy"].dropna().unique() if str(value)})
            if policies and policies != [req.adjustment_policy]:
                issues.append(
                    ResearchDatasetIssue(
                        code="production_strict_adjustment_policy_mismatch",
                        dataset=DATASET_PRICES,
                        message="production_strict 复权口径必须与请求一致。",
                        details={"expected": req.adjustment_policy, "actual": policies},
                    )
                )
    for dataset in _W3_RESEARCH_DATASETS:
        result = reader_results.get(dataset)
        if result is None or result.status != "available":
            issues.append(
                ResearchDatasetIssue(
                    code=f"production_strict_{dataset}_required_missing",
                    dataset=dataset,
                    message=f"production_strict 必须具备 {dataset}，缺失时不能声明真实可成交或事件时点真实。",
                    details={} if result is None else {"reader_status": result.status, "reader_issues": list(result.issues)},
                )
            )
    return issues


def _build_research_calendar(
    result: ReaderResult | None,
    prices: pd.DataFrame | None,
    parsed: _ParsedRequest,
    issues: list[ResearchDatasetIssue],
) -> list[date]:
    frame = _available_frame(result)
    if frame is not None:
        if "trade_date" not in frame.columns:
            issues.append(
                ResearchDatasetIssue(
                    code="trade_calendar_required_columns_missing",
                    dataset=DATASET_TRADE_CALENDAR,
                    field="trade_date",
                    message="trade_calendar 缺少 trade_date 字段。",
                )
            )
        else:
            work = frame.copy()
            if "is_open" in work.columns:
                work = work[_bool_series(work["is_open"])]
            dates = _date_values(work["trade_date"], parsed)
            if dates:
                return dates
            issues.append(
                ResearchDatasetIssue(
                    code="trade_calendar_empty",
                    dataset=DATASET_TRADE_CALENDAR,
                    message="trade_calendar 在请求区间内为空。",
                )
            )
    if prices is not None and "trade_date" in prices.columns:
        fallback = _date_values(prices["trade_date"], parsed)
        if fallback:
            return fallback
    return []


def _build_research_universe(
    req: ResearchDatasetRequest,
    result: ReaderResult | None,
    issues: list[ResearchDatasetIssue],
) -> list[str]:
    if req.symbols:
        return list(dict.fromkeys(str(symbol).strip() for symbol in req.symbols if str(symbol).strip()))
    frame = _available_frame(result)
    if frame is None:
        return []
    symbol_column = "symbol" if "symbol" in frame.columns else "con_code" if "con_code" in frame.columns else ""
    if not symbol_column:
        issues.append(
            ResearchDatasetIssue(
                code="index_members_symbol_missing",
                dataset=DATASET_INDEX_MEMBERS,
                field="symbol",
                message="index_members 缺少 symbol 或 con_code 字段。",
            )
        )
        return []
    work = frame.copy()
    if "is_member" in work.columns:
        work = work[_bool_series(work["is_member"])]
    symbols = sorted({str(symbol).strip() for symbol in work[symbol_column].dropna().tolist() if str(symbol).strip()})
    if not symbols:
        issues.append(
            ResearchDatasetIssue(
                code="index_members_empty",
                dataset=DATASET_INDEX_MEMBERS,
                message="index_members 在请求范围内未提供有效股票池。",
            )
        )
    return symbols


def _universe_index_code(universe: str) -> str:
    mapping = {
        "csi300": "399300.SZ",
        "hs300": "399300.SZ",
        "沪深300": "399300.SZ",
    }
    value = str(universe or "").strip()
    return mapping.get(value.lower(), value or "399300.SZ")


def _universe_resolution_issues(resolution: UniverseResolution) -> list[ResearchDatasetIssue]:
    return [
        ResearchDatasetIssue(
            code=issue.code,
            dataset=issue.dataset,
            field=issue.field,
            severity=issue.severity,
            message=issue.message,
            details=issue.details,
        )
        for issue in resolution.issues
    ]


def _merge_universe_known_limitations(
    limitations: list[Any],
    resolution: UniverseResolution,
) -> list[Any]:
    merged = list(limitations)
    for item in resolution.known_limitations:
        if item not in merged:
            merged.append(item)
    return merged


def _merge_pit_lifecycle_known_limitations(
    limitations: list[Any],
    gate: _PitLifecycleGate | None,
) -> list[Any]:
    if gate is None:
        return limitations
    merged = list(limitations)
    for item in gate.known_limitations:
        if item not in merged:
            merged.append(item)
    return merged


def _apply_universe_allowed_claims(
    req: ResearchDatasetRequest,
    claims: list[str],
    resolution: UniverseResolution,
) -> list[str]:
    if resolution.status not in {"available", "available_with_warnings"}:
        return []
    if resolution.metadata.is_pit_universe:
        return _ordered_unique([*claims, *resolution.allowed_claims])
    fixed_claims = [claim for claim in claims if claim in {"framework_validation", "exploratory_analysis"}]
    if req.universe_mode == "fixed_snapshot" or resolution.metadata.universe_mode == "fixed_snapshot":
        fixed_claims.append("fixed_snapshot_exploration")
    return _ordered_unique([*fixed_claims, *resolution.allowed_claims])


def _apply_pit_lifecycle_allowed_claims(
    claims: list[str],
    gate: _PitLifecycleGate | None,
) -> list[str]:
    if gate is None:
        return claims
    lifecycle = gate.metadata.get("lifecycle", {})
    asof_count = int(gate.metadata.get("as_of_join_violation_count", 0) or 0)
    if lifecycle.get("lifecycle_status") == "pass" and asof_count == 0 and "pit_universe_research" in claims:
        return _ordered_unique([*claims, "survivorship_bias_controlled"])
    return claims


def _build_research_close_df(
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    prices: pd.DataFrame | None,
    calendar: list[date],
    universe_symbols: list[str],
    issues: list[ResearchDatasetIssue],
) -> pd.DataFrame | None:
    if prices is None:
        return None
    missing = sorted({"trade_date", "symbol"} - set(prices.columns))
    if missing:
        issues.append(
            ResearchDatasetIssue(
                code="prices_required_columns_missing",
                dataset=DATASET_PRICES,
                field=",".join(missing),
                message="prices 缺少必需字段: " + ", ".join(missing),
            )
        )
        return None
    value_column = "adjusted_close" if "adjusted_close" in prices.columns else "close" if "close" in prices.columns else ""
    if not value_column:
        issues.append(
            ResearchDatasetIssue(
                code="prices_close_column_missing",
                dataset=DATASET_PRICES,
                field="close",
                message="prices 缺少 adjusted_close 或 close 字段。",
            )
        )
        return None
    work = prices.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"], errors="coerce").dt.date
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    if parsed.start is not None:
        work = work[work["trade_date"] >= parsed.start]
    if parsed.end is not None:
        work = work[work["trade_date"] <= parsed.end]
    if universe_symbols:
        work = work[work["symbol"].isin(universe_symbols)]
    work = work.dropna(subset=["trade_date", "symbol", value_column])
    if work.empty:
        issues.append(
            ResearchDatasetIssue(
                code="prices_empty_after_filter",
                dataset=DATASET_PRICES,
                message="prices 过滤到请求范围和股票池后为空。",
            )
        )
        return None
    close_df = work.pivot_table(index="trade_date", columns="symbol", values=value_column, aggfunc="last")
    if calendar:
        close_df = close_df.reindex(index=calendar)
    if universe_symbols:
        close_df = close_df.reindex(columns=universe_symbols)
    close_df.index.name = "trade_date"
    if close_df.empty:
        issues.append(
            ResearchDatasetIssue(
                code="close_df_empty",
                dataset=DATASET_PRICES,
                message="close_df 为空。",
            )
        )
        return None
    return close_df


def _date_values(series: pd.Series, parsed: _ParsedRequest) -> list[date]:
    values = pd.to_datetime(series, errors="coerce").dt.date.dropna().tolist()
    dates = sorted({item for item in values if (parsed.start is None or item >= parsed.start) and (parsed.end is None or item <= parsed.end)})
    return dates


def _resolve_benchmark(
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    benchmark_resolver: Any,
    prices: pd.DataFrame | None,
) -> Any:
    policy, required = _benchmark_policy_for_resolver(req)
    price_trade_dates = []
    if prices is not None and "trade_date" in prices.columns:
        price_trade_dates = [str(item) for item in sorted(set(prices["trade_date"].astype(str)))]
    try:
        return benchmark_resolver(
            lake_root=req.lake_root,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            policy=policy,
            required=required,
            price_trade_dates=price_trade_dates,
        )
    except Exception as exc:
        return ResearchDatasetIssue(
            code="benchmark_resolver_failed",
            dataset="benchmark",
            message=f"benchmark resolver 返回异常: {type(exc).__name__}",
            details={"required": required},
        )


def _benchmark_policy_for_resolver(req: ResearchDatasetRequest) -> tuple[BenchmarkPolicy | Mapping[str, Any], bool]:
    if isinstance(req.benchmark_policy, BenchmarkPolicy):
        return req.benchmark_policy, bool(req.benchmark_policy.required)
    if isinstance(req.benchmark_policy, Mapping):
        required = bool(req.benchmark_policy.get("required", False))
        return BenchmarkPolicy.from_config(req.benchmark_policy, required=required), required
    required = req.benchmark_policy == "hs300_required"
    return (
        BenchmarkPolicy.from_config(
            {"benchmark_kind": "price_index", "confirmed": True, "required": required},
            required=required,
        ),
        required,
    )


def _benchmark_issues(req: ResearchDatasetRequest, result: Any) -> list[ResearchDatasetIssue]:
    status = _benchmark_status(result)
    if status == "available":
        return []
    required = _benchmark_required(req, result)
    reason = _benchmark_missing_reason(result) or status or "unknown"
    details = {
        "benchmark_status": status,
        "benchmark_missing_reason": reason,
        "benchmark_policy_id": _benchmark_policy_id(req),
    }
    if status == "quality_failed":
        return [
            ResearchDatasetIssue(
                code="benchmark_quality_failed",
                dataset="benchmark",
                message=f"benchmark quality_failed: {reason}",
                details=details,
            )
        ]
    if required:
        return [
            ResearchDatasetIssue(
                code="benchmark_required_missing",
                dataset="benchmark",
                message=f"必需 benchmark 不可用: {reason}",
                details=details,
            )
        ]
    return [
        ResearchDatasetIssue(
            code="benchmark_unavailable_proxy_allowed",
            dataset="benchmark",
            severity="WARNING",
            message=f"真实 benchmark 不可用，仅允许 proxy_baseline 语义: {reason}",
            details=details,
        )
    ]


def _benchmark_required(req: ResearchDatasetRequest, result: Any) -> bool:
    if isinstance(req.benchmark_policy, str):
        return req.benchmark_policy == "hs300_required"
    return bool(getattr(result, "required", False))


def _benchmark_status(result: Any) -> str:
    if result is None:
        return "unavailable"
    if hasattr(result, "status"):
        return str(getattr(result, "status"))
    if isinstance(result, Mapping):
        return str(result.get("benchmark_status") or result.get("status") or "unavailable")
    return "unavailable"


def _benchmark_missing_reason(result: Any) -> str:
    if result is None:
        return "not_requested"
    if hasattr(result, "missing_reason"):
        value = getattr(result, "missing_reason")
        return "" if value is None else str(value)
    if isinstance(result, Mapping):
        value = result.get("benchmark_missing_reason") or result.get("missing_reason") or ""
        return str(value)
    return ""


def _benchmark_available(result: Any) -> bool:
    return _benchmark_status(result) == "available" and not _benchmark_missing_reason(result)


def _known_limitations(
    req: ResearchDatasetRequest,
    issues: Sequence[ResearchDatasetIssue],
    prices: pd.DataFrame | None,
    benchmark_result: Any,
) -> list[Any]:
    limitations: list[Any] = [
        "S03/S05 builder does not execute S04 quality/label or S06 auxiliary data gates.",
    ]
    if prices is not None and "adjusted_close" not in prices.columns:
        limitations.append("adjusted_close unavailable; close is used for S03 close_df compatibility.")
    if req.symbols:
        limitations.append("explicit symbols are treated as fixed snapshot until S05 PIT universe contract is applied.")
    if not _benchmark_available(benchmark_result):
        limitations.append(
            {
                "code": "real_benchmark_unavailable",
                "benchmark_status": _benchmark_status(benchmark_result),
                "benchmark_missing_reason": _benchmark_missing_reason(benchmark_result),
            }
        )
    limitations.extend(issue.to_dict() for issue in issues if issue.severity == "WARNING")
    return limitations


def _allowed_claims(req: ResearchDatasetRequest, issues: Sequence[ResearchDatasetIssue], benchmark_result: Any) -> list[str]:
    if any(issue.severity == "ERROR" for issue in issues):
        return []
    claims = ["framework_validation", "exploratory_analysis"]
    if req.analysis_mode == "research" and _benchmark_available(benchmark_result):
        claims.append("research_input_contract_available")
    return claims


def _blocked_claims(req: ResearchDatasetRequest, issues: Sequence[ResearchDatasetIssue]) -> list[dict[str, Any]]:
    blocked: list[dict[str, Any]] = []
    mapping = {
        "pit": "pit_universe_research",
        "benchmark": "real_benchmark_research",
        "adjustment": "adjustment_consistent_research",
        "lifecycle": "survivorship_bias_controlled",
        DATASET_TRADE_STATUS: "real_tradable_execution",
        DATASET_PRICES_LIMIT: "realistic_fillability",
        DATASET_EVENTS: "event_timing_research",
        "quality": "quality_pass_research",
    }
    for issue in issues:
        if issue.severity != "ERROR":
            continue
        claim = ""
        code = issue.code
        if code in {"stock_basic_not_pit_universe", "index_weights_not_members"}:
            claim = mapping["pit"]
        elif "lifecycle" in code or issue.dataset == DATASET_STOCK_BASIC:
            claim = mapping["lifecycle"]
        elif "pit_universe" in code or issue.dataset == DATASET_INDEX_MEMBERS:
            claim = mapping["pit"]
        elif "benchmark" in code or issue.dataset == "benchmark":
            claim = mapping["benchmark"]
        elif "adjustment" in code:
            claim = mapping["adjustment"]
        elif issue.dataset in _W3_RESEARCH_DATASETS:
            claim = mapping[str(issue.dataset)]
        elif "quality" in code:
            claim = mapping["quality"]
        elif req.realism_mode == "production_strict":
            claim = "production_strict_research"
        if claim and not any(item.get("claim") == claim and item.get("reason_code") == code for item in blocked):
            blocked.append(
                {
                    "claim": claim,
                    "reason_code": code,
                    "dataset": issue.dataset,
                    "severity": issue.severity,
                    "details": _json_safe(issue.details),
                }
            )
    return blocked


def _aggregate_research_status(issues: Sequence[ResearchDatasetIssue]) -> str:
    if any(issue.code in {"lake_root_required", "repo_data_reference_only", "invalid_date_range", "invalid_date"} for issue in issues):
        return ResearchDatasetStatus.INVALID_REQUEST.value
    if any("quality_failed" in issue.code or issue.code == "adjustment_policy_mismatch" for issue in issues if issue.severity == "ERROR"):
        return ResearchDatasetStatus.QUALITY_FAILED.value
    if any("required_missing" in issue.code or "missing" in issue.code for issue in issues if issue.severity == "ERROR"):
        return ResearchDatasetStatus.REQUIRED_MISSING.value
    if any(issue.severity == "ERROR" for issue in issues):
        return ResearchDatasetStatus.GATE_FAILED.value
    if any(issue.severity == "WARNING" for issue in issues):
        return ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    return ResearchDatasetStatus.AVAILABLE.value


def _finish_research_dataset(
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    *,
    status: str,
    issues: list[ResearchDatasetIssue],
    prices: pd.DataFrame | None,
    close_df: pd.DataFrame | None,
    calendar: list[date],
    universe_symbols: list[str],
    benchmark_result: Any,
    reader_results: dict[str, ReaderResult],
    known_limitations: list[Any] | None = None,
    allowed_claims: list[str] | None = None,
    universe_resolution: UniverseResolution | None = None,
    pit_lifecycle_gate: _PitLifecycleGate | None = None,
) -> ResearchDataset:
    remediation_spec = _collect_remediation_spec(reader_results, benchmark_result, issues)
    limitations = known_limitations if known_limitations is not None else _known_limitations(req, issues, prices, benchmark_result)
    claims = allowed_claims if allowed_claims is not None else _allowed_claims(req, issues, benchmark_result)
    blocked_claims = _blocked_claims(req, issues)
    metadata = _research_dataset_metadata(
        req,
        parsed,
        status,
        prices=prices,
        close_df=close_df,
        calendar=calendar,
        universe_symbols=universe_symbols,
        benchmark_result=benchmark_result,
        issues=issues,
        known_limitations=limitations,
        allowed_claims=claims,
        blocked_claims=blocked_claims,
        remediation_spec=remediation_spec,
        reader_results=reader_results,
        universe_resolution=universe_resolution,
        pit_lifecycle_gate=pit_lifecycle_gate,
    )
    gate_status = _gate_status_for(status, issues)
    gate_result = GateResult(
        status=gate_status,
        issues=list(issues),
        checks=[*_gate_checks(reader_results, benchmark_result), *([] if pit_lifecycle_gate is None else pit_lifecycle_gate.checks)],
        remediation_spec=remediation_spec,
    )
    return ResearchDataset(
        status=status,
        prices=prices,
        close_df=close_df,
        calendar=calendar,
        universe_symbols=universe_symbols,
        benchmark_result=benchmark_result,
        metadata=metadata,
        gate_result=gate_result,
        issues=list(issues),
        known_limitations=limitations,
        allowed_claims=claims,
        blocked_claims=blocked_claims,
        remediation_spec=remediation_spec,
        reader_results=dict(reader_results),
    )


def _gate_status_for(status: str, issues: Sequence[ResearchDatasetIssue]) -> str:
    if status in {ResearchDatasetStatus.AVAILABLE.value}:
        return GateStatus.PASS.value
    if status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value:
        return GateStatus.WARN.value
    if issues:
        return GateStatus.FAIL.value
    return GateStatus.NOT_EVALUATED.value


def _gate_checks(reader_results: Mapping[str, ReaderResult], benchmark_result: Any) -> list[dict[str, Any]]:
    checks = [
        {"name": f"reader:{dataset}", "status": result.status}
        for dataset, result in sorted(reader_results.items())
    ]
    checks.append({"name": "benchmark", "status": _benchmark_status(benchmark_result)})
    return checks


def _gate_check(
    name: str,
    status: str,
    code: str,
    severity: str,
    message: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "code": code,
        "severity": severity,
        "message": message,
        "details": _json_safe(dict(details or {})),
    }


def _merge_gate_checks(existing: Sequence[Mapping[str, Any]], s04_checks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    retained = [dict(item) for item in existing if not str(item.get("name", "")).endswith("_gate")]
    retained.extend(dict(item) for item in s04_checks)
    return retained


def _s04_gate_status(status: str, checks: Sequence[Mapping[str, Any]], issues: Sequence[ResearchDatasetIssue]) -> str:
    if any(issue.severity == "ERROR" for issue in issues) or any(check.get("status") == "fail" for check in checks):
        return GateStatus.FAIL.value
    if status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value or any(check.get("status") == "warn" for check in checks):
        return GateStatus.WARN.value
    if status == ResearchDatasetStatus.AVAILABLE.value:
        return GateStatus.PASS.value
    return GateStatus.NOT_EVALUATED.value


def _aggregate_s04_dataset_status(
    previous_status: str,
    s04_issues: Sequence[ResearchDatasetIssue],
    all_issues: Sequence[ResearchDatasetIssue],
) -> str:
    if previous_status == ResearchDatasetStatus.INVALID_REQUEST.value:
        return previous_status
    s04_errors = [issue for issue in s04_issues if issue.severity == "ERROR"]
    if any(issue.code in {"quality_failed", "quality_missing"} for issue in s04_errors):
        return ResearchDatasetStatus.QUALITY_FAILED.value
    if s04_errors:
        return ResearchDatasetStatus.GATE_FAILED.value
    if previous_status not in {ResearchDatasetStatus.AVAILABLE.value, ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value}:
        return previous_status
    if any(issue.severity == "WARNING" for issue in all_issues):
        return ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    return ResearchDatasetStatus.AVAILABLE.value


def _s04_allowed_claims(
    req: ResearchDatasetRequest,
    status: str,
    checks: Sequence[Mapping[str, Any]],
) -> list[str]:
    if status not in {ResearchDatasetStatus.AVAILABLE.value, ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value}:
        return []
    claims = ["framework_validation", "exploratory_analysis"]
    if req.analysis_mode == "research" and all(check.get("status") == "pass" for check in checks):
        claims.append("research_input_contract_available")
    return claims


def _active_limitations_without_s03_gate_placeholder(limitations: Sequence[Any]) -> list[Any]:
    placeholders = {
        "S03 baseline builder does not execute S04 quality/label, S05 PIT universe, or S06 auxiliary data gates.",
        "S03/S05 builder does not execute S04 quality/label or S06 auxiliary data gates.",
    }
    return [item for item in limitations if not (isinstance(item, str) and item in placeholders)]


def _merge_s04_metadata(
    base_metadata: Mapping[str, Any],
    *,
    status: str,
    quality: Mapping[str, Any],
    adjustment: Mapping[str, Any],
    label_window: Mapping[str, Any],
    known_limitations: Sequence[Any],
    allowed_claims: Sequence[str],
    issues: Sequence[ResearchDatasetIssue],
) -> dict[str, Any]:
    metadata = metadata_to_dict(base_metadata)
    metadata["quality"] = {**dict(metadata.get("quality") or {}), **dict(quality), "gate_status": status}
    metadata["quality_status"] = quality.get("quality_status", metadata.get("quality_status"))
    metadata["readiness_status"] = "research_ready" if status == ResearchDatasetStatus.AVAILABLE.value else status
    metadata["adjustment"] = {**dict(metadata.get("adjustment") or {}), **dict(adjustment)}
    metadata["adjustment_policy"] = (
        adjustment.get("adjustment_policy")
        or adjustment.get("request_policy")
        or metadata.get("adjustment_policy")
    )
    metadata["policy"] = metadata["adjustment_policy"]
    metadata["research_adjustment_policy"] = metadata["adjustment_policy"]
    metadata["single_policy_gate_status"] = adjustment.get(
        "single_policy_gate_status",
        metadata.get("single_policy_gate_status", "blocked"),
    )
    metadata["label_window"] = {**dict(metadata.get("label_window") or {}), **dict(label_window)}
    if "label_available_end" in label_window:
        metadata["label_available_end"] = label_window.get("label_available_end")
    metadata["forward_return_horizon"] = label_window.get("forward_return_horizon", metadata.get("forward_return_horizon"))
    metadata["known_limitations"] = list(known_limitations)
    metadata["allowed_claims"] = list(allowed_claims)
    metadata["issues"] = [issue.to_dict() for issue in issues]
    metadata["s04_gates"] = {
        "quality_status": quality.get("quality_status"),
        "adjustment_status": adjustment.get("adjustment_status"),
        "label_status": label_window.get("label_status"),
    }
    return metadata_to_dict(metadata)


def _worst_quality_status(statuses: Sequence[str]) -> str:
    normalized = [normalize_quality_status(status) for status in statuses]
    if "fail" in normalized:
        return "fail"
    if "missing" in normalized:
        return "missing"
    if "warn" in normalized:
        return "warn"
    return "pass" if normalized else "missing"


def _quality_source(statuses: Sequence[tuple[str, str, str]]) -> str:
    for _, status, source in statuses:
        if normalize_quality_status(status) != "missing":
            return source
    return "missing"


def _quality_status_details(statuses: Sequence[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [{"dataset": dataset, "quality_status": status, "quality_source": source} for dataset, status, source in statuses]


def _normalize_policy_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _adjustment_values_from_metadata(metadata: Mapping[str, Any] | None) -> set[str]:
    if not metadata:
        return set()
    adjustment = metadata.get("adjustment")
    values: set[str] = set()
    if isinstance(adjustment, Mapping):
        for key in ("research_adjustment_policy", "adjustment_policy", "policy", "data_adjustment_policy"):
            value = _normalize_policy_value(adjustment.get(key))
            if value:
                values.add(value)
        raw_seen = adjustment.get("policies_seen")
        if isinstance(raw_seen, Sequence) and not isinstance(raw_seen, (str, bytes)):
            values.update(value for value in (_normalize_policy_value(item) for item in raw_seen) if value)
    for key in ("research_adjustment_policy", "adjustment_policy", "policy", "data_adjustment_policy"):
        value = _normalize_policy_value(metadata.get(key))
        if value:
            values.add(value)
    return values


def _adjustment_values_from_catalog_entry(entry: Any) -> set[str]:
    if entry is None:
        return set()
    values: set[str] = set()
    for key in ("research_adjustment_policy", "adjustment_policy", "policy", "data_adjustment_policy"):
        value = _normalize_policy_value(getattr(entry, key, None))
        if value:
            values.add(value)
    coverage = getattr(entry, "coverage", None)
    if isinstance(coverage, Mapping):
        for key in ("research_adjustment_policy", "adjustment_policy", "policy", "data_adjustment_policy"):
            value = _normalize_policy_value(coverage.get(key))
            if value:
                values.add(value)
    return values


def _label_gate_result(
    status: str,
    code: str,
    message: str,
    metadata: Mapping[str, Any],
    issues: Sequence[ResearchDatasetIssue],
    limitations: Sequence[Any],
) -> dict[str, Any]:
    return {
        "check": _gate_check(
            "label_window_gate",
            status,
            code,
            "ERROR" if status == "fail" else "WARNING" if status == "warn" else "INFO",
            message,
            metadata,
        ),
        "issues": list(issues),
        "limitations": list(limitations),
        "metadata": dict(metadata),
    }


def _apply_label_truncation(
    prices: pd.DataFrame | None,
    calendar: Sequence[date],
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    label_available_end: Any,
    universe_symbols: Sequence[str],
) -> tuple[pd.DataFrame | None, list[date], pd.DataFrame | None, list[ResearchDatasetIssue]]:
    if prices is None or not label_available_end:
        return prices, list(calendar), None, []
    cutoff = _parse_request_date(label_available_end, "label_available_end", [])
    if cutoff is None:
        return prices, list(calendar), None, []
    work = prices.copy()
    trade_dates = pd.to_datetime(work["trade_date"], errors="coerce").dt.date if "trade_date" in work.columns else pd.Series([], dtype=object)
    work = work[trade_dates <= cutoff].copy()
    truncated_calendar = [item for item in calendar if item <= cutoff]
    rebuild_issues: list[ResearchDatasetIssue] = []
    close_df = _build_research_close_df(req, parsed, work, truncated_calendar, list(universe_symbols), rebuild_issues)
    return work, truncated_calendar, close_df, rebuild_issues


def _research_dataset_metadata(
    req: ResearchDatasetRequest,
    parsed: _ParsedRequest,
    status: str,
    *,
    prices: pd.DataFrame | None,
    close_df: pd.DataFrame | None,
    calendar: list[date],
    universe_symbols: list[str],
    benchmark_result: Any,
    issues: Sequence[ResearchDatasetIssue],
    known_limitations: list[Any],
    allowed_claims: list[str],
    blocked_claims: list[dict[str, Any]],
    remediation_spec: dict[str, Any],
    reader_results: Mapping[str, ReaderResult],
    universe_resolution: UniverseResolution | None = None,
    pit_lifecycle_gate: _PitLifecycleGate | None = None,
) -> dict[str, Any]:
    coverage_start, coverage_end = _coverage_range(parsed, prices, calendar)
    benchmark = _benchmark_metadata_for_dataset(req, benchmark_result)
    if universe_resolution is not None:
        universe = universe_resolution.metadata.to_dict()
    else:
        universe = {
            "universe": req.universe,
            "universe_mode": req.universe_mode,
            "symbol_count": len(universe_symbols),
            "symbols": list(universe_symbols),
            "is_pit_universe": False,
            "pit_status": "not_evaluated",
            "readiness_status": "pending_s05" if req.universe_mode != "fixed_snapshot" else "fixed_snapshot",
            "survivorship_bias_note": "",
        }
    if pit_lifecycle_gate is not None:
        universe = {**dict(universe), **dict(pit_lifecycle_gate.metadata.get("universe", {}))}
    lifecycle = dict(pit_lifecycle_gate.metadata.get("lifecycle", {})) if pit_lifecycle_gate is not None else {
        "lifecycle_status": "not_evaluated",
        "lifecycle_missing_count": 0,
        "lifecycle_blocked_count": 0,
        "as_of_join_violation_count": 0,
    }
    as_of_join_violation_count = int(
        pit_lifecycle_gate.metadata.get("as_of_join_violation_count", 0) if pit_lifecycle_gate is not None else 0
    )
    quality_status = _quality_status(status, reader_results)
    readiness_status = "research_ready" if status == ResearchDatasetStatus.AVAILABLE.value else status
    label_available_end = coverage_end or parsed.end_date
    lineage = _lineage_from_readers(reader_results)
    realism_mode = req.realism_mode or (
        "exploratory" if req.analysis_mode == "exploratory" else "production_strict"
    )
    payload = {
        "schema_name": RESEARCH_INPUT_SCHEMA_NAME,
        "schema_version": RESEARCH_INPUT_SCHEMA_NAME,
        "report_kind": req.report_kind,
        "analysis_mode": req.analysis_mode,
        "realism_mode": realism_mode,
        "lineage": lineage,
        "manifest_run_id": lineage.get("manifest_run_id", ""),
        "source_run_id": lineage.get("source_run_id", "research-dataset-builder"),
        "coverage_start": coverage_start or parsed.start_date,
        "coverage_end": coverage_end or parsed.end_date,
        "coverage": {
            "start_date": coverage_start or parsed.start_date,
            "end_date": coverage_end or parsed.end_date,
            "calendar_count": len(calendar),
            "symbol_count": len(universe_symbols),
            "price_row_count": 0 if prices is None else int(len(prices)),
            "close_shape": None if close_df is None else [int(close_df.shape[0]), int(close_df.shape[1])],
        },
        "benchmark": benchmark,
        "benchmark_policy": benchmark,
        "benchmark_policy_id": benchmark.get("benchmark_policy_id", ""),
        "benchmark_status": benchmark.get("benchmark_status", ""),
        "benchmark_kind": benchmark.get("benchmark_kind", ""),
        "hs300_available": bool(benchmark.get("hs300_available", False)),
        "hs300_coverage_ratio": benchmark.get("hs300_coverage_ratio"),
        "proxy_baseline_used": bool(benchmark.get("proxy_baseline_used", False)),
        "benchmark_missing_reason": benchmark.get("benchmark_missing_reason", ""),
        "universe": universe,
        "universe_mode": universe.get("universe_mode", req.universe_mode),
        "is_pit_universe": bool(universe.get("is_pit_universe", False)),
        "pit_status": universe.get("pit_status", ""),
        "survivorship_bias_note": universe.get("survivorship_bias_note", ""),
        "as_of_join_violation_count": as_of_join_violation_count,
        "lifecycle": lifecycle,
        "lifecycle_status": lifecycle.get("lifecycle_status", "not_evaluated"),
        "adjustment_policy": req.adjustment_policy,
        "label_window": {
            "forward_return_horizon": req.forward_return_horizon,
            "label_available_end": label_available_end,
            "label_status": "not_evaluated_until_s04",
        },
        "forward_return_horizon": req.forward_return_horizon,
        "label_available_end": label_available_end,
        "quality": {
            "quality_status": quality_status,
            "readiness_status": readiness_status,
            "gate_status": status,
            "issue_count": len(issues),
        },
        "quality_status": quality_status,
        "readiness_status": readiness_status,
        "readiness": _readiness_metadata(reader_results, universe, issues),
        "known_limitations": known_limitations,
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "issues": [issue.to_dict() for issue in issues],
        "remediation_spec": remediation_spec,
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }
    if req.benchmark_policy == "proxy_allowed" and not bool(benchmark.get("hs300_available", False)):
        payload.pop("hs300_available", None)
        payload.pop("hs300_coverage_ratio", None)
    return metadata_to_dict(payload)


def _readiness_metadata(
    reader_results: Mapping[str, ReaderResult],
    universe: Mapping[str, Any],
    issues: Sequence[ResearchDatasetIssue],
) -> dict[str, Any]:
    datasets: dict[str, Any] = {}
    for dataset, result in reader_results.items():
        entry = result.catalog_entry
        datasets[dataset] = {
            "status": result.status,
            "quality_status": getattr(entry, "quality_status", "") if entry else "",
            "readiness_status": getattr(entry, "readiness_status", "") if entry else result.status,
            "pit_status": getattr(entry, "pit_status", "") if entry else "",
            "issue_codes": [str(issue.get("code")) for issue in result.issues],
        }
    return {
        "datasets": datasets,
        "pit": {
            "is_pit_universe": bool(universe.get("is_pit_universe", False)),
            "pit_status": universe.get("pit_status", ""),
            "universe_mode": universe.get("universe_mode", ""),
        },
        "w3": {
            dataset: datasets.get(dataset, {"status": "not_requested"})
            for dataset in _W3_RESEARCH_DATASETS
        },
        "issue_codes": [issue.code for issue in issues],
    }


def _coverage_range(parsed: _ParsedRequest, prices: pd.DataFrame | None, calendar: list[date]) -> tuple[str, str]:
    if calendar:
        return calendar[0].isoformat(), calendar[-1].isoformat()
    if prices is not None and "trade_date" in prices.columns:
        dates = _date_values(prices["trade_date"], parsed)
        if dates:
            return dates[0].isoformat(), dates[-1].isoformat()
    return parsed.start_date, parsed.end_date


def _quality_status(status: str, reader_results: Mapping[str, ReaderResult]) -> str:
    if status == ResearchDatasetStatus.QUALITY_FAILED.value:
        return "fail"
    values = []
    for result in reader_results.values():
        entry = result.catalog_entry
        if entry is not None and getattr(entry, "quality_status", None):
            values.append(str(getattr(entry, "quality_status")))
    if "fail" in values:
        return "fail"
    if "warn" in values or status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value:
        return "warn"
    if values:
        return "pass"
    return "missing" if status != ResearchDatasetStatus.AVAILABLE.value else "pass"


def _benchmark_metadata_for_dataset(req: ResearchDatasetRequest, result: Any) -> dict[str, Any]:
    policy_result = build_benchmark_policy_result(
        result if result is not None else None,
        policy_id=_benchmark_policy_id(req),
        proxy_baseline_used=_proxy_baseline_used_for_policy(req, result),
    )
    return _json_safe(policy_result.to_metadata())


def _benchmark_policy_id(req: ResearchDatasetRequest) -> str:
    if isinstance(req.benchmark_policy, str):
        return req.benchmark_policy
    if isinstance(req.benchmark_policy, BenchmarkPolicy):
        return "hs300_required" if req.benchmark_policy.required else "hs300_optional"
    if isinstance(req.benchmark_policy, Mapping):
        value = req.benchmark_policy.get("benchmark_policy_id") or req.benchmark_policy.get("policy_id")
        if value:
            return str(value)
        return "hs300_required" if bool(req.benchmark_policy.get("required", False)) else "hs300_optional"
    return "hs300_optional"


def _proxy_baseline_used_for_policy(req: ResearchDatasetRequest, result: Any) -> bool:
    if _benchmark_available(result):
        return False
    if req.realism_mode == "production_strict":
        return False
    return req.analysis_mode == "exploratory" or req.benchmark_policy == "proxy_allowed"


def _lineage_from_readers(reader_results: Mapping[str, ReaderResult]) -> dict[str, Any]:
    lineage: dict[str, Any] = {}
    for dataset, result in reader_results.items():
        entry = result.catalog_entry
        if entry is not None:
            lineage.setdefault("manifest_run_id", getattr(entry, "latest_manifest_run_id", "") or "")
            lineage.setdefault("lineage_raw_checksum", getattr(entry, "lineage_raw_checksum", "") or "")
            lineage.setdefault("source", getattr(entry, "source", "") or "")
            lineage.setdefault("source_interface", getattr(entry, "source_interface", "") or "")
        frame = result.frame
        if frame is not None and not frame.empty:
            lineage.setdefault("source_run_id", _first_frame_value(frame, "source_run_id") or "")
            lineage.setdefault("lineage_raw_checksum", _first_frame_value(frame, "lineage_raw_checksum") or lineage.get("lineage_raw_checksum", ""))
        if lineage.get("manifest_run_id") or lineage.get("source_run_id"):
            break
    lineage.setdefault("source_run_id", "research-dataset-builder")
    lineage["datasets"] = sorted(reader_results)
    return {key: value for key, value in lineage.items() if value not in (None, "")}


def _first_frame_value(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return ""
    values = [str(value) for value in frame[column].dropna().tolist() if str(value)]
    return values[0] if values else ""


def _collect_remediation_spec(
    reader_results: Mapping[str, ReaderResult],
    benchmark_result: Any,
    issues: Sequence[ResearchDatasetIssue],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for dataset, result in sorted(reader_results.items()):
        if result.remediation_spec:
            spec = _normalize_remediation_spec({**result.remediation_spec, "dataset": dataset})
            actions.append(spec)
    if benchmark_result is not None:
        metadata = benchmark_metadata_from_result(benchmark_result) if hasattr(benchmark_result, "to_metadata") else benchmark_result
        if isinstance(metadata, Mapping):
            for key in ("next_action", "remediation_job_spec"):
                if metadata.get(key):
                    actions.append(_normalize_remediation_spec({key: metadata[key], "dataset": "benchmark"}))
    for issue in issues:
        if issue.severity == "ERROR" and not actions:
            actions.append(
                {
                    "action": "explicit_upstream_remediation_required",
                    "code": issue.code,
                    "dataset": issue.dataset,
                    "auto_execute": False,
                    "dry_run_default": True,
                }
            )
    return _normalize_remediation_spec({"auto_execute": False, "dry_run_default": True, "actions": actions})


def _normalize_remediation_spec(value: Any) -> Any:
    raw = _metadata_value(value)
    if isinstance(raw, Mapping):
        normalized = {str(key): _normalize_remediation_spec(item) for key, item in raw.items()}
        normalized["auto_execute"] = False
        normalized.setdefault("dry_run_default", True)
        if "dry_run" in normalized:
            normalized["dry_run"] = True
        return normalized
    if isinstance(raw, list):
        return [_normalize_remediation_spec(item) for item in raw]
    if isinstance(raw, tuple):
        return [_normalize_remediation_spec(item) for item in raw]
    return _json_safe(raw)


def _metadata_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "to_metadata") and callable(value.to_metadata):
        return value.to_metadata()
    if is_dataclass(value):
        return asdict(value)
    return value


def build_research_input_metadata(payload: Mapping[str, Any]) -> ResearchInputMetadata:
    """从扁平或嵌套 payload 构建并校验 research_input_v1 metadata。"""

    data = _copy_mapping(payload)
    pre_issues: list[ResearchInputMetadataIssue] = []
    if "allowed_claims" not in data:
        pre_issues.append(
            ResearchInputMetadataIssue(
                "missing_required_fields",
                "allowed_claims",
                "allowed_claims 必须显式存在；可以为空列表，但不能缺省。",
            )
        )

    benchmark = _benchmark_payload(data)
    universe = _universe_payload(data)
    label_window = _label_window_payload(data)
    quality = _quality_payload(data)
    metadata = ResearchInputMetadata(
        schema_name=str(data.get("schema_name") or RESEARCH_INPUT_SCHEMA_NAME),
        report_kind=str(data.get("report_kind") or ""),
        lineage=_lineage_payload(data),
        coverage_start=str(_first_present(data, "coverage_start", ("coverage", "start_date")) or ""),
        coverage_end=str(_first_present(data, "coverage_end", ("coverage", "end_date")) or ""),
        benchmark=benchmark,
        universe=universe,
        adjustment_policy=str(data.get("adjustment_policy") or ""),
        label_window=label_window,
        quality=quality,
        known_limitations=list(data.get("known_limitations") or []),
        allowed_claims=[str(item) for item in data.get("allowed_claims", [])],
        legacy_report_policy=str(data.get("legacy_report_policy") or LEGACY_REPORT_POLICY),
        blocked_claims=[dict(item) for item in data.get("blocked_claims") or [] if isinstance(item, Mapping)],
        auxiliary_availability=dict(data.get("auxiliary_availability") or {}),
    )
    issues = [*pre_issues, *validate_research_input_metadata(metadata)]
    if issues:
        raise ResearchInputMetadataError(issues)
    return metadata


def validate_research_input_metadata(
    metadata: ResearchInputMetadata | Mapping[str, Any],
) -> list[ResearchInputMetadataIssue]:
    """返回结构化校验问题；调用方据此阻止缺字段报告生成。"""

    raw = metadata_to_dict(metadata) if isinstance(metadata, ResearchInputMetadata) else _copy_mapping(metadata)
    issues: list[ResearchInputMetadataIssue] = []

    for field in sorted(RESEARCH_INPUT_REQUIRED_FIELDS):
        value = _field_value(raw, field)
        if field == "allowed_claims":
            if value is None:
                issues.append(_missing_issue(field))
            continue
        if field == "known_limitations":
            if not isinstance(value, list) or not value:
                issues.append(_missing_issue(field))
            continue
        if _is_empty(value):
            issues.append(_missing_issue(field))

    lineage = raw.get("lineage") if isinstance(raw.get("lineage"), Mapping) else {}
    manifest_run_id = raw.get("manifest_run_id") or lineage.get("manifest_run_id")
    source_run_id = raw.get("source_run_id") or lineage.get("source_run_id")
    if _is_empty(manifest_run_id) and _is_empty(source_run_id):
        issues.append(
            ResearchInputMetadataIssue(
                "lineage_missing",
                "lineage",
                "manifest_run_id 与 source_run_id 至少需要一个。",
            )
        )

    if raw.get("schema_name") != RESEARCH_INPUT_SCHEMA_NAME:
        issues.append(
            ResearchInputMetadataIssue(
                "invalid_schema_name",
                "schema_name",
                f"schema_name 必须为 {RESEARCH_INPUT_SCHEMA_NAME}。",
            )
        )

    if raw.get("legacy_report_policy") != LEGACY_REPORT_POLICY:
        issues.append(
            ResearchInputMetadataIssue(
                "legacy_report_current_truth_attempt",
                "legacy_report_policy",
                f"legacy_report_policy 必须为 {LEGACY_REPORT_POLICY}。",
            )
        )

    issues.extend(_validate_coverage_dates(raw))
    return issues


def benchmark_metadata_from_result(result: Any) -> dict[str, Any]:
    """从 CR007 BenchmarkResult 或 dict 映射为 research_input benchmark metadata。"""

    if hasattr(result, "to_metadata") and callable(result.to_metadata):
        raw = result.to_metadata()
    elif isinstance(result, Mapping):
        raw = result
    else:
        raise TypeError("BenchmarkResult 必须提供 to_metadata() 或 Mapping 接口。")

    metadata = _copy_mapping(raw)
    status = metadata.get("benchmark_status") or metadata.get("status") or ""
    metadata["benchmark_status"] = status
    metadata.setdefault("benchmark_kind", metadata.get("dataset") or metadata.get("index_code") or "unknown")
    metadata.setdefault("missing_reason", "")
    if "denominator_mode" not in metadata and isinstance(metadata.get("coverage"), Mapping):
        metadata["denominator_mode"] = metadata["coverage"].get("denominator_mode", "")
    return metadata


def metadata_to_dict(metadata: ResearchInputMetadata | Mapping[str, Any]) -> dict[str, Any]:
    """导出 JSON-safe dict，并补齐 required flat fields。"""

    if isinstance(metadata, ResearchInputMetadata):
        raw = asdict(metadata)
    else:
        raw = _copy_mapping(metadata)

    lineage = raw.get("lineage") if isinstance(raw.get("lineage"), Mapping) else {}
    benchmark = raw.get("benchmark") if isinstance(raw.get("benchmark"), Mapping) else {}
    benchmark_policy = raw.get("benchmark_policy") if isinstance(raw.get("benchmark_policy"), Mapping) else benchmark
    universe = raw.get("universe") if isinstance(raw.get("universe"), Mapping) else {}
    label_window = raw.get("label_window") if isinstance(raw.get("label_window"), Mapping) else {}
    quality = raw.get("quality") if isinstance(raw.get("quality"), Mapping) else {}

    raw.setdefault("schema_name", RESEARCH_INPUT_SCHEMA_NAME)
    raw["manifest_run_id"] = raw.get("manifest_run_id") or lineage.get("manifest_run_id", "")
    raw["source_run_id"] = raw.get("source_run_id") or lineage.get("source_run_id", "")
    raw["benchmark_status"] = raw.get("benchmark_status") or benchmark.get("benchmark_status") or benchmark.get("status", "")
    suppress_proxy_hs300_flat_fields = (
        str(raw.get("benchmark_policy_id") or benchmark_policy.get("benchmark_policy_id") or "") == "proxy_allowed"
        and str(benchmark_policy.get("benchmark_kind") or benchmark.get("benchmark_kind") or "") == "proxy_baseline"
        and not bool(benchmark_policy.get("hs300_available", benchmark.get("hs300_available", False)))
    )
    for field_name in BENCHMARK_POLICY_FIELDS:
        if suppress_proxy_hs300_flat_fields and field_name.startswith("hs300_"):
            continue
        if field_name not in raw:
            raw[field_name] = benchmark_policy.get(field_name, benchmark.get(field_name, ""))
    raw["universe_mode"] = raw.get("universe_mode") or universe.get("universe_mode") or universe.get("mode", "")
    raw["forward_return_horizon"] = (
        raw.get("forward_return_horizon")
        if raw.get("forward_return_horizon") is not None
        else label_window.get("forward_return_horizon", label_window.get("horizon", ""))
    )
    if "label_available_end" in raw:
        raw["label_available_end"] = raw.get("label_available_end")
    else:
        raw["label_available_end"] = label_window.get("label_available_end") if "label_available_end" in label_window else label_window.get("label_usable_end", "")
    raw["quality_status"] = raw.get("quality_status") or quality.get("quality_status") or quality.get("status", "")
    raw["readiness_status"] = raw.get("readiness_status") or quality.get("readiness_status", "")
    raw.setdefault("legacy_report_policy", LEGACY_REPORT_POLICY)
    return _json_safe(raw)


def _benchmark_payload(data: dict[str, Any]) -> dict[str, Any]:
    raw = {}
    if "benchmark_result" in data:
        raw.update(benchmark_metadata_from_result(data["benchmark_result"]))
    if isinstance(data.get("benchmark"), Mapping):
        raw.update(_copy_mapping(data["benchmark"]))
    for key in ("benchmark_status", "benchmark_kind", "missing_reason", "denominator_mode"):
        if key in data:
            raw[key] = data[key]
    if "status" in raw and "benchmark_status" not in raw:
        raw["benchmark_status"] = raw["status"]
    return raw


def _universe_payload(data: dict[str, Any]) -> dict[str, Any]:
    raw = _copy_mapping(data.get("universe", {})) if isinstance(data.get("universe"), Mapping) else {}
    if "universe_mode" in data:
        raw["universe_mode"] = data["universe_mode"]
    return raw


def _label_window_payload(data: dict[str, Any]) -> dict[str, Any]:
    raw = _copy_mapping(data.get("label_window", {})) if isinstance(data.get("label_window"), Mapping) else {}
    if "forward_return_horizon" in data:
        raw["forward_return_horizon"] = data["forward_return_horizon"]
    if "label_available_end" in data:
        raw["label_available_end"] = data["label_available_end"]
    return raw


def _quality_payload(data: dict[str, Any]) -> dict[str, Any]:
    raw = _copy_mapping(data.get("quality", {})) if isinstance(data.get("quality"), Mapping) else {}
    if "quality_status" in data:
        raw["quality_status"] = data["quality_status"]
    if "readiness_status" in data:
        raw["readiness_status"] = data["readiness_status"]
    return raw


def _lineage_payload(data: dict[str, Any]) -> dict[str, Any]:
    raw = _copy_mapping(data.get("lineage", {})) if isinstance(data.get("lineage"), Mapping) else {}
    for key in ("manifest_run_id", "source_run_id", "lineage_raw_checksum"):
        if key in data:
            raw[key] = data[key]
    return raw


def _first_present(data: dict[str, Any], flat_key: str, nested_key: tuple[str, str]) -> Any:
    if flat_key in data:
        return data[flat_key]
    parent = data.get(nested_key[0])
    if isinstance(parent, Mapping):
        return parent.get(nested_key[1])
    return None


def _field_value(raw: Mapping[str, Any], field: str) -> Any:
    if field in raw:
        return raw[field]
    if field == "benchmark_status":
        benchmark = raw.get("benchmark")
        if isinstance(benchmark, Mapping):
            return benchmark.get("benchmark_status") or benchmark.get("status")
    if field == "universe_mode":
        universe = raw.get("universe")
        if isinstance(universe, Mapping):
            return universe.get("universe_mode") or universe.get("mode")
    if field in {"forward_return_horizon", "label_available_end"}:
        label_window = raw.get("label_window")
        if isinstance(label_window, Mapping):
            return label_window.get(field) or (label_window.get("horizon") if field == "forward_return_horizon" else None)
    if field in {"quality_status", "readiness_status"}:
        quality = raw.get("quality")
        if isinstance(quality, Mapping):
            return quality.get(field) or (quality.get("status") if field == "quality_status" else None)
    return None


def _validate_coverage_dates(raw: Mapping[str, Any]) -> list[ResearchInputMetadataIssue]:
    start = str(raw.get("coverage_start") or "")
    end = str(raw.get("coverage_end") or "")
    issues: list[ResearchInputMetadataIssue] = []
    for field, value in (("coverage_start", start), ("coverage_end", end), ("label_available_end", str(raw.get("label_available_end") or ""))):
        if value and not _DATE_PATTERN.match(value):
            issues.append(ResearchInputMetadataIssue("invalid_date", field, f"{field} 必须为 YYYY-MM-DD。"))
    if _DATE_PATTERN.match(start) and _DATE_PATTERN.match(end) and start > end:
        issues.append(
            ResearchInputMetadataIssue("invalid_coverage_range", "coverage_start", "coverage_start 不得晚于 coverage_end。")
        )
    return issues


def _missing_issue(field: str) -> ResearchInputMetadataIssue:
    return ResearchInputMetadataIssue("missing_required_fields", field, f"{field} 是 research_input_v1 必填字段。")


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _copy_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata payload 必须是 Mapping。")
    return deepcopy(dict(value))


def _liquidity_capacity_field_available(
    source_payload: Mapping[str, Any],
    frame_payload: Mapping[str, Any],
    frame: pd.DataFrame | None,
    aliases: Sequence[str],
) -> tuple[bool, str, str]:
    for alias in aliases:
        if alias in source_payload and _liquidity_capacity_value_available(source_payload.get(alias)):
            return True, "metadata", alias
        if alias in frame_payload and _liquidity_capacity_value_available(frame_payload.get(alias)):
            return True, "execution_payload", alias
        if frame is not None and alias in frame.columns and _liquidity_capacity_series_available(frame[alias]):
            return True, "execution_frame", alias
    return False, "missing", ""


def _liquidity_capacity_value_available(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, pd.Series):
        return _liquidity_capacity_series_available(value)
    if isinstance(value, pd.DataFrame):
        return not value.dropna(how="all").empty
    if isinstance(value, Mapping):
        return any(_liquidity_capacity_value_available(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_liquidity_capacity_value_available(item) for item in value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value).strip() != ""
    return math.isfinite(number) and number > 0


def _liquidity_capacity_series_available(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce")
    if not numeric.dropna().empty:
        return bool((numeric.dropna() > 0).any())
    return bool(series.dropna().astype(str).str.strip().ne("").any())


def _liquidity_capacity_payload_value(
    source_payload: Mapping[str, Any],
    frame_payload: Mapping[str, Any],
    frame: pd.DataFrame | None,
    field_name: str,
) -> Any:
    aliases = _LIQUIDITY_CAPACITY_REQUIRED_INPUTS[field_name]
    for alias in aliases:
        if alias in source_payload and _liquidity_capacity_value_available(source_payload.get(alias)):
            return _liquidity_capacity_compact_value(source_payload.get(alias))
        if alias in frame_payload and _liquidity_capacity_value_available(frame_payload.get(alias)):
            return _liquidity_capacity_compact_value(frame_payload.get(alias))
        if frame is not None and alias in frame.columns and _liquidity_capacity_series_available(frame[alias]):
            return _liquidity_capacity_compact_value(frame[alias])
    return None


def _liquidity_capacity_compact_value(value: Any) -> Any:
    if isinstance(value, pd.Series):
        numeric = pd.to_numeric(value, errors="coerce").dropna()
        return None if numeric.empty else float(numeric.mean())
    if isinstance(value, pd.DataFrame):
        return {"rows": int(len(value)), "columns": [str(item) for item in value.columns]}
    if isinstance(value, Mapping):
        return {str(key): _liquidity_capacity_compact_value(item) for key, item in value.items() if key != "token"}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        numeric = pd.to_numeric(pd.Series(list(value)), errors="coerce").dropna()
        return None if numeric.empty else float(numeric.mean())
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    return number if math.isfinite(number) else None


def _liquidity_capacity_blocked_claims(missing_fields: Sequence[str]) -> list[dict[str, Any]]:
    missing = sorted(str(item) for item in missing_fields)
    return [
        {
            "claim": claim,
            "missing_capability": "liquidity_capacity_inputs",
            "missing_fields": missing,
            "reason": "capacity_inputs_missing",
            "severity": "BLOCKING",
            "source_story": "CR011-S07",
        }
        for claim in _LIQUIDITY_CAPACITY_STRONG_CLAIMS
    ]


def _liquidity_capacity_lineage(metadata: Mapping[str, Any]) -> dict[str, Any]:
    lineage = metadata.get("lineage") if isinstance(metadata.get("lineage"), Mapping) else {}
    return _json_safe(
        {
            "source": metadata.get("liquidity_source") or metadata.get("source") or lineage.get("source") or "explicit_input",
            "source_interface": metadata.get("source_interface") or lineage.get("source_interface") or "",
            "manifest_run_id": metadata.get("manifest_run_id") or lineage.get("manifest_run_id") or "",
            "source_run_id": metadata.get("source_run_id") or lineage.get("source_run_id") or "",
            "readiness_status": metadata.get("readiness_status") or metadata.get("quality_status") or "",
        }
    )


def _capacity_cost_limitations(blocked_claims: Sequence[Any]) -> list[dict[str, Any]]:
    limitations: list[dict[str, Any]] = []
    for item in blocked_claims:
        if not isinstance(item, Mapping):
            continue
        source_story = str(item.get("source_story") or "")
        if source_story and source_story != "CR011-S07":
            continue
        limitations.append(
            {
                "code": "capacity_cost_claim_blocked",
                "claim": str(item.get("claim") or ""),
                "missing_capability": str(item.get("missing_capability") or ""),
                "reason": str(item.get("reason") or item.get("reason_code") or ""),
                "severity": str(item.get("severity") or "BLOCKING"),
            }
        )
    return limitations


def _robust_validation_views_by_name(summary: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw_views = summary.get("views")
    views: dict[str, dict[str, Any]] = {}
    if isinstance(raw_views, Mapping):
        for view_name, payload in raw_views.items():
            views[str(view_name)] = _view_payload(view_name, payload)
    elif isinstance(raw_views, Sequence) and not isinstance(raw_views, (str, bytes, bytearray)):
        for payload in raw_views:
            if not isinstance(payload, Mapping):
                continue
            view_name = payload.get("view") or payload.get("view_name") or payload.get("name")
            if view_name:
                views[str(view_name)] = _view_payload(str(view_name), payload)
    for view_name in _ROBUST_VALIDATION_REQUIRED_VIEWS:
        payload = summary.get(view_name)
        if isinstance(payload, Mapping):
            views.setdefault(view_name, _view_payload(view_name, payload))
    return views


def _view_payload(view_name: Any, payload: Any) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        view = dict(payload)
    else:
        view = {"records": payload}
    view.setdefault("view", str(view_name))
    return _json_safe(view)


def _claim_entries(value: Any) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return entries
    for item in value:
        if isinstance(item, Mapping):
            entries.append(dict(item))
    return entries


def _blocked_claim_names(blocked_claims: Sequence[Any]) -> set[str]:
    return {
        str(item.get("claim"))
        for item in blocked_claims
        if isinstance(item, Mapping) and item.get("claim")
    }


def _factor_audit_blocked_claims(
    reason: str,
    *,
    missing_views: Sequence[str],
    failed_views: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "claim": claim,
            "missing_capability": "factor_panel_robust_validation",
            "missing_views": [str(item) for item in missing_views],
            "failed_views": [dict(item) for item in failed_views],
            "reason": reason,
            "severity": "BLOCKING",
            "source_story": "CR011-S08",
        }
        for claim in _FACTOR_AUDIT_STRONG_CLAIMS
    ]


def _factor_audit_limitations(blocked_claims: Sequence[Any]) -> list[dict[str, Any]]:
    limitations: list[dict[str, Any]] = []
    for item in blocked_claims:
        if not isinstance(item, Mapping):
            continue
        source_story = str(item.get("source_story") or "")
        if source_story and source_story != "CR011-S08":
            continue
        limitations.append(
            {
                "code": "factor_panel_robust_validation_blocked",
                "claim": str(item.get("claim") or ""),
                "missing_capability": str(item.get("missing_capability") or ""),
                "reason": str(item.get("reason") or item.get("reason_code") or ""),
                "severity": str(item.get("severity") or "BLOCKING"),
            }
        )
    return limitations


def _coerce_auxiliary_requirements(requirements: Mapping[str, Any] | Sequence[str] | None) -> dict[str, dict[str, Any]]:
    if requirements is None:
        capability_names = list(_AUXILIARY_CAPABILITY_ORDER)
        overrides: Mapping[str, Any] = {}
    elif isinstance(requirements, Mapping):
        if "capabilities" in requirements and not _is_auxiliary_capability_mapping(requirements):
            capability_names = [str(item) for item in requirements.get("capabilities") or []]
            overrides = requirements
        else:
            capability_names = [str(item) for item in requirements]
            overrides = requirements
    else:
        capability_names = [str(item) for item in requirements]
        overrides = {}

    normalized: dict[str, dict[str, Any]] = {}
    for capability in capability_names:
        if capability not in _AUXILIARY_CAPABILITY_DEFAULTS:
            normalized[capability] = {
                "source_dataset": capability,
                "required_columns": (),
                "required_for_claims": (),
                "status_field": f"{capability}_status",
            }
        else:
            normalized[capability] = dict(_AUXILIARY_CAPABILITY_DEFAULTS[capability])
        override = overrides.get(capability) if isinstance(overrides, Mapping) else None
        if isinstance(override, Mapping):
            normalized[capability].update(dict(override))
    if not normalized:
        return {capability: dict(_AUXILIARY_CAPABILITY_DEFAULTS[capability]) for capability in _AUXILIARY_CAPABILITY_ORDER}
    return normalized


def _is_auxiliary_capability_mapping(value: Mapping[str, Any]) -> bool:
    return any(key in _AUXILIARY_CAPABILITY_DEFAULTS for key in value)


def _availability_entry_from_reader(
    capability: str,
    requirement: Mapping[str, Any],
    result: Any,
) -> AuxiliaryAvailabilityEntry:
    source_dataset = str(requirement.get("source_dataset") or capability)
    required_columns = [str(item) for item in requirement.get("required_columns") or []]
    required_for_claims = [str(item) for item in requirement.get("required_for_claims") or []]
    payload = _reader_result_payload(result)
    observed_columns = [str(item) for item in payload.get("observed_columns") or []]
    missing_columns = sorted(column for column in required_columns if column not in set(observed_columns))
    raw_status = str(payload.get("status") or ("missing" if result is None else "unknown"))
    quality_status = payload.get("quality_status")
    remediation_spec = _normalize_remediation_spec(payload.get("remediation_spec") or {})

    if result is None:
        status = "missing"
    elif raw_status in {"available", "pass"} and not missing_columns:
        status = "available"
    elif raw_status in {"available", "pass"} and missing_columns:
        status = "partial"
    elif "quality_failed" in raw_status or raw_status in {"pit_failed", "adjustment_failed"}:
        status = "quality_failed"
    elif raw_status in {"required_missing", "missing"}:
        status = "missing"
    elif raw_status in {"unavailable", "invalid_request"}:
        status = raw_status
    else:
        status = "unknown"

    reason = str(payload.get("missing_reason") or "")
    if missing_columns:
        reason = f"required_columns_missing:{','.join(missing_columns)}"
    if status not in _AUXILIARY_AVAILABLE_STATUSES and not reason:
        reason = _issue_reason(payload.get("issues")) or f"auxiliary_capability_not_available:{capability}"
    lineage_status = str(payload.get("lineage_status") or ("available" if _has_lineage_columns(observed_columns) else "missing"))
    if capability in {"adjustment_audit", "industry_classification", "market_cap", "style_exposure"} and status == "available" and lineage_status == "missing":
        status = "partial"
        reason = reason or f"lineage_missing:{capability}"
    return AuxiliaryAvailabilityEntry(
        capability=capability,
        status=status,
        required_for_claims=required_for_claims,
        missing_reason="" if status == "available" else reason,
        source_dataset=source_dataset,
        required_columns=required_columns,
        observed_columns=observed_columns,
        missing_columns=missing_columns,
        quality_status=str(quality_status) if quality_status not in (None, "") else None,
        lineage_status=lineage_status,
        remediation_spec=remediation_spec if remediation_spec else {},
    )


def _pit_universe_availability_entry(
    capability: str,
    requirement: Mapping[str, Any],
    result: Any,
    universe_metadata: Mapping[str, Any] | None,
) -> AuxiliaryAvailabilityEntry:
    entry = _availability_entry_from_reader(capability, requirement, result)
    metadata = dict(universe_metadata or {})
    pit_status = str(metadata.get("pit_status") or metadata.get("readiness_status") or "")
    is_pit = bool(metadata.get("is_pit_universe"))
    if is_pit and pit_status in {"pit_available", "available", "pass"}:
        return AuxiliaryAvailabilityEntry(
            capability=entry.capability,
            status="available",
            required_for_claims=entry.required_for_claims,
            source_dataset=entry.source_dataset,
            required_columns=entry.required_columns,
            observed_columns=entry.observed_columns,
            missing_columns=[],
            quality_status=entry.quality_status,
            lineage_status="available",
            remediation_spec=entry.remediation_spec,
        )
    reason = (
        str(metadata.get("survivorship_bias_note") or "")
        or f"pit_universe_not_available:{pit_status or 'missing'}"
    )
    return AuxiliaryAvailabilityEntry(
        capability=entry.capability,
        status="missing" if entry.status == "available" else entry.status,
        required_for_claims=entry.required_for_claims,
        missing_reason=reason,
        source_dataset=entry.source_dataset,
        required_columns=entry.required_columns,
        observed_columns=entry.observed_columns,
        missing_columns=entry.missing_columns,
        quality_status=entry.quality_status,
        lineage_status="missing",
        remediation_spec=entry.remediation_spec,
    )


def _label_quality_availability_entry(
    capability: str,
    requirement: Mapping[str, Any],
    result: Any,
    gate_result: GateResult | Mapping[str, Any] | None,
) -> AuxiliaryAvailabilityEntry:
    entry = _availability_entry_from_reader(capability, requirement, result)
    metadata = _gate_metadata(gate_result)
    label_window = metadata.get("label_window") if isinstance(metadata.get("label_window"), Mapping) else metadata
    label_status = str(label_window.get("label_status") or label_window.get("status") or "")
    label_available_end = str(label_window.get("label_available_end") or "")
    if label_status in {"available", "complete_only", "pass"} and label_available_end:
        return AuxiliaryAvailabilityEntry(
            capability=entry.capability,
            status="available",
            required_for_claims=entry.required_for_claims,
            source_dataset=entry.source_dataset,
            required_columns=entry.required_columns,
            observed_columns=entry.observed_columns,
            missing_columns=[],
            quality_status=entry.quality_status,
            lineage_status="not_applicable",
            remediation_spec=entry.remediation_spec,
        )
    if label_status == "truncated":
        status = "partial"
        reason = "label_window_truncated"
    else:
        status = "missing" if entry.status == "available" else entry.status
        reason = entry.missing_reason or f"label_quality_not_available:{label_status or 'missing'}"
    return AuxiliaryAvailabilityEntry(
        capability=entry.capability,
        status=status,
        required_for_claims=entry.required_for_claims,
        missing_reason=reason,
        source_dataset=entry.source_dataset,
        required_columns=entry.required_columns,
        observed_columns=entry.observed_columns,
        missing_columns=entry.missing_columns,
        quality_status=entry.quality_status,
        lineage_status="not_applicable",
        remediation_spec=entry.remediation_spec,
    )


def _reader_result_payload(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, ReaderResult):
        frame = result.frame
        entry = result.catalog_entry
        quality_status = getattr(entry, "quality_status", None) if entry is not None else None
        lineage_status = "available" if entry is not None and getattr(entry, "lineage_raw_checksum", None) else None
        return {
            "status": result.status,
            "observed_columns": list(frame.columns) if frame is not None else [],
            "issues": list(result.issues),
            "quality_status": quality_status,
            "lineage_status": lineage_status,
            "remediation_spec": dict(result.remediation_spec or {}),
        }
    if isinstance(result, Mapping):
        raw = dict(result)
        frame = raw.get("frame")
        if isinstance(frame, pd.DataFrame):
            raw.setdefault("observed_columns", list(frame.columns))
        return raw
    return {"status": str(getattr(result, "status", "unknown"))}


def _issue_reason(issues: Any) -> str:
    if not issues:
        return ""
    first = list(issues)[0] if not isinstance(issues, Mapping) else issues
    if isinstance(first, Mapping):
        return str(first.get("reason") or first.get("message") or first.get("code") or "")
    return str(first)


def _has_lineage_columns(columns: Sequence[str]) -> bool:
    column_set = {str(column) for column in columns}
    return bool(column_set & {"available_at", "effective_date", "source_run_id", "lineage_raw_checksum", "adj_factor"})


def _gate_metadata(gate_result: GateResult | Mapping[str, Any] | None) -> dict[str, Any]:
    if gate_result is None:
        return {}
    if isinstance(gate_result, Mapping):
        return dict(gate_result)
    return gate_result.to_dict()


def _coerce_auxiliary_matrix(value: AuxiliaryAvailabilityMatrix | Mapping[str, Any]) -> AuxiliaryAvailabilityMatrix:
    if isinstance(value, AuxiliaryAvailabilityMatrix):
        return value
    entries: dict[str, AuxiliaryAvailabilityEntry] = {}
    for capability, raw in dict(value).items():
        if isinstance(raw, AuxiliaryAvailabilityEntry):
            entries[str(capability)] = raw
        elif isinstance(raw, Mapping):
            entries[str(capability)] = AuxiliaryAvailabilityEntry(
                capability=str(raw.get("capability") or capability),
                status=str(raw.get("status") or "unknown"),
                required_for_claims=[str(item) for item in raw.get("required_for_claims") or []],
                missing_reason=str(raw.get("missing_reason") or raw.get("reason") or ""),
                source_dataset=str(raw.get("source_dataset")) if raw.get("source_dataset") else None,
                required_columns=[str(item) for item in raw.get("required_columns") or []],
                observed_columns=[str(item) for item in raw.get("observed_columns") or []],
                missing_columns=[str(item) for item in raw.get("missing_columns") or []],
                quality_status=str(raw.get("quality_status")) if raw.get("quality_status") else None,
                lineage_status=str(raw.get("lineage_status")) if raw.get("lineage_status") else None,
                remediation_spec=dict(raw.get("remediation_spec") or {}),
            )
    return AuxiliaryAvailabilityMatrix(entries=entries)


def _first_missing_capability_for_claim(claim: str, matrix: AuxiliaryAvailabilityMatrix) -> str:
    required_capabilities = _claim_required_capabilities(claim)
    for capability in required_capabilities:
        entry = matrix.entries.get(capability)
        if entry is None:
            return capability
        if not entry.available:
            return capability
    return ""


def _claim_required_capabilities(claim: str) -> list[str]:
    required = []
    for capability in _AUXILIARY_CAPABILITY_ORDER:
        defaults = _AUXILIARY_CAPABILITY_DEFAULTS[capability]
        if claim in defaults["required_for_claims"]:
            required.append(capability)
    return required


def _blocked_claim_payload(claim: str, entry: AuxiliaryAvailabilityEntry) -> dict[str, Any]:
    reason = entry.missing_reason or f"auxiliary_capability_not_available:{entry.capability}"
    return {
        "claim": claim,
        "missing_capability": entry.capability,
        "missing_status": entry.status,
        "reason": reason,
        "severity": "BLOCKING",
    }


def _limitation_from_blocked_claim(blocked_claim: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "code": "auxiliary_claim_blocked",
        "claim": str(blocked_claim.get("claim") or ""),
        "missing_capability": str(blocked_claim.get("missing_capability") or ""),
        "reason": str(blocked_claim.get("reason") or ""),
        "severity": str(blocked_claim.get("severity") or "BLOCKING"),
    }


def _coerce_allowed_claims_result(value: AllowedClaimsResult | Mapping[str, Any]) -> AllowedClaimsResult:
    if isinstance(value, AllowedClaimsResult):
        return value
    raw = dict(value)
    return AllowedClaimsResult(
        allowed_claims=[str(item) for item in raw.get("allowed_claims") or []],
        blocked_claims=[dict(item) for item in raw.get("blocked_claims") or [] if isinstance(item, Mapping)],
        known_limitations=list(raw.get("known_limitations") or []),
        auxiliary_availability=dict(raw.get("auxiliary_availability") or {}),
        gate_status=str(raw.get("gate_status") or GateStatus.PASS.value),
    )


def _exposure_entry_from_reader(
    capability: str,
    requirement: Mapping[str, Any],
    result: Any,
    factor_sample: pd.DataFrame | None,
    *,
    universe_metadata: Mapping[str, Any] | None,
    decision_time: str | date | datetime | None,
    requested_style_factors: Sequence[str] | None,
) -> ExposureAvailabilityEntry:
    source_dataset = str(requirement.get("source_dataset") or capability)
    required_columns = [str(item) for item in requirement.get("required_columns") or []]
    required_for_claims = [str(item) for item in requirement.get("required_for_claims") or []]
    payload = _reader_result_payload(result)
    frame = _frame_from_reader_payload(result, payload)
    observed_columns = [str(item) for item in payload.get("observed_columns") or []]
    missing_columns = _exposure_missing_columns_for_requirement(requirement, observed_columns)
    raw_status = str(payload.get("status") or ("required_missing" if result is None else "unknown"))
    remediation_spec = _normalize_remediation_spec(payload.get("remediation_spec") or {})
    coverage = _exposure_coverage(capability, frame, factor_sample, requested_style_factors)
    decision = _coerce_decision_date(decision_time, factor_sample)
    asof_count = _exposure_asof_violation_count(capability, frame, decision)
    lineage_status = _exposure_lineage_status(observed_columns, payload)
    status = _exposure_status_from_raw(raw_status, result, missing_columns, coverage, asof_count)
    reason = _exposure_missing_reason(capability, status, payload, missing_columns, coverage, asof_count)

    snapshot_reason = _current_snapshot_reason(capability, frame, observed_columns)
    if snapshot_reason and status == "available":
        status = "blocked_non_pit"
        reason = snapshot_reason
    pit_failure = _pit_exposure_gate_failure(universe_metadata)
    if pit_failure and status == "available":
        status = "blocked_non_pit"
        reason = pit_failure
    if status == "available" and lineage_status == "missing":
        status = "partial"
        reason = f"lineage_missing:{capability}"

    missing_count = int(coverage["sample_count"] - coverage["covered_count"])
    return ExposureAvailabilityEntry(
        capability=capability,
        status=status,
        coverage_ratio=float(coverage["coverage_ratio"]),
        missing_rate=float(coverage["missing_rate"]),
        sample_count=int(coverage["sample_count"]),
        missing_count=missing_count,
        as_of_join_violation_count=int(asof_count),
        required_for_claims=required_for_claims,
        missing_reason="" if status == "available" else reason,
        source_dataset=source_dataset,
        required_columns=required_columns,
        observed_columns=observed_columns,
        missing_columns=missing_columns,
        lineage_status=lineage_status,
        remediation_spec=remediation_spec if remediation_spec else {},
    )


def _frame_from_reader_payload(result: Any, payload: Mapping[str, Any]) -> pd.DataFrame | None:
    if isinstance(result, ReaderResult):
        return result.frame.copy() if result.frame is not None else None
    frame = payload.get("frame")
    return frame.copy() if isinstance(frame, pd.DataFrame) else None


def _exposure_missing_columns_for_requirement(
    requirement: Mapping[str, Any],
    observed_columns: Sequence[str],
) -> list[str]:
    observed = {str(column) for column in observed_columns}
    missing = [str(column) for column in requirement.get("required_columns") or [] if str(column) not in observed]
    for group in requirement.get("one_of_columns") or ():
        group_values = [str(column) for column in group]
        if not any(column in observed for column in group_values):
            missing.append("|".join(group_values))
    return missing


def _exposure_status_from_raw(
    raw_status: str,
    result: Any,
    missing_columns: Sequence[str],
    coverage: Mapping[str, Any],
    asof_count: int,
) -> str:
    if result is None:
        return "source_unresolved"
    if raw_status in {"source_unresolved", "unavailable"}:
        return "source_unresolved"
    if raw_status in {"quality_failed", "pit_failed", "adjustment_failed"} or "quality_failed" in raw_status:
        return "quality_failed"
    if raw_status in {"required_missing", "missing", "invalid_request"}:
        return "required_missing"
    if missing_columns:
        return "required_missing"
    if asof_count:
        return "pit_incomplete"
    if float(coverage.get("coverage_ratio") or 0.0) < 1.0:
        return "partial"
    if raw_status in {"available", "pass"}:
        return "available"
    return "required_missing"


def _exposure_missing_reason(
    capability: str,
    status: str,
    payload: Mapping[str, Any],
    missing_columns: Sequence[str],
    coverage: Mapping[str, Any],
    asof_count: int,
) -> str:
    if missing_columns:
        return f"required_columns_missing:{','.join(missing_columns)}"
    if asof_count:
        return "as_of_join_violation"
    if status == "partial":
        return f"coverage_incomplete:{coverage.get('coverage_ratio', 0.0):.6f}"
    if status == "source_unresolved":
        return _issue_reason(payload.get("issues")) or f"{capability}_source_unresolved"
    if status == "required_missing":
        return _issue_reason(payload.get("issues")) or f"{capability}_missing"
    if status == "quality_failed":
        return _issue_reason(payload.get("issues")) or f"{capability}_quality_failed"
    return ""


def _current_snapshot_reason(capability: str, frame: pd.DataFrame | None, observed_columns: Sequence[str]) -> str:
    observed = {str(column) for column in observed_columns}
    if frame is None or frame.empty:
        return ""
    if "available_at" not in observed:
        return "current_snapshot_not_pit_exposure"
    if capability == "industry_classification":
        if "effective_date" not in observed or "pit_status" not in observed:
            return "current_snapshot_not_pit_exposure"
        pit_values = {str(value).strip() for value in frame["pit_status"].dropna().tolist() if str(value).strip()}
        if not pit_values or not pit_values <= {"pass", "pit_available", "available"}:
            return "current_snapshot_not_pit_exposure"
    return ""


def _pit_exposure_gate_failure(universe_metadata: Mapping[str, Any] | None) -> str:
    if not universe_metadata:
        return ""
    metadata = dict(universe_metadata)
    universe = metadata.get("universe") if isinstance(metadata.get("universe"), Mapping) else metadata
    lifecycle = metadata.get("lifecycle") if isinstance(metadata.get("lifecycle"), Mapping) else metadata
    pit_status = str(universe.get("pit_status") or metadata.get("pit_status") or "")
    is_pit_present = "is_pit_universe" in universe or "is_pit_universe" in metadata
    is_pit = bool(universe.get("is_pit_universe", metadata.get("is_pit_universe", False)))
    asof_count = int(
        metadata.get("as_of_join_violation_count")
        or universe.get("as_of_join_violation_count")
        or 0
    )
    lifecycle_status = str(lifecycle.get("lifecycle_status") or metadata.get("lifecycle_status") or "")
    if asof_count:
        return "pit_universe_gate_not_passed"
    if is_pit_present and not is_pit:
        return "pit_universe_gate_not_passed"
    if pit_status and pit_status not in {"pass", "pit_available", "available"}:
        return "pit_universe_gate_not_passed"
    if lifecycle_status and lifecycle_status not in {"pass", "not_evaluated"}:
        return "pit_universe_gate_not_passed"
    return ""


def _exposure_lineage_status(observed_columns: Sequence[str], payload: Mapping[str, Any]) -> str:
    explicit = payload.get("lineage_status")
    if explicit:
        return str(explicit)
    return "available" if _has_lineage_columns(observed_columns) else "missing"


def _coerce_decision_date(value: str | date | datetime | None, factor_sample: pd.DataFrame | None) -> date | None:
    if value is not None:
        parsed = _coerce_date_value(value)
        return None if pd.isna(parsed) else parsed
    if factor_sample is not None and not factor_sample.empty and "trade_date" in factor_sample.columns:
        dates = _series_to_dates(factor_sample["trade_date"]).dropna().tolist()
        if dates:
            return max(dates)
    return None


def _exposure_asof_violation_count(capability: str, frame: pd.DataFrame | None, decision_time: date | None) -> int:
    if frame is None or frame.empty or decision_time is None:
        return 0
    fields = ("available_at", "effective_date") if capability == "industry_classification" else ("available_at", "trade_date")
    violations = pd.Series(False, index=frame.index)
    for field in fields:
        if field not in frame.columns:
            continue
        values = _series_to_dates(frame[field])
        violations = violations | (values.notna() & (values > decision_time))
    return int(violations.fillna(False).sum())


def _exposure_coverage(
    capability: str,
    frame: pd.DataFrame | None,
    factor_sample: pd.DataFrame | None,
    requested_style_factors: Sequence[str] | None,
) -> dict[str, Any]:
    if frame is None or frame.empty:
        sample_count = _sample_denominator(capability, factor_sample, requested_style_factors)
        return {"coverage_ratio": 0.0, "missing_rate": 1.0, "sample_count": sample_count, "covered_count": 0}
    if factor_sample is None or factor_sample.empty:
        row_count = int(len(frame))
        return {"coverage_ratio": 1.0, "missing_rate": 0.0, "sample_count": row_count, "covered_count": row_count}
    if capability == "industry_classification":
        return _symbol_coverage(frame, factor_sample)
    if capability in {"market_cap", "float_market_cap"}:
        return _symbol_date_coverage(frame, factor_sample)
    if capability == "style_exposure":
        return _style_factor_coverage(frame, factor_sample, requested_style_factors)
    return _symbol_coverage(frame, factor_sample)


def _sample_denominator(
    capability: str,
    factor_sample: pd.DataFrame | None,
    requested_style_factors: Sequence[str] | None,
) -> int:
    if factor_sample is None or factor_sample.empty:
        return 1
    if capability == "industry_classification" and "symbol" in factor_sample.columns:
        return len({str(item) for item in factor_sample["symbol"].dropna().tolist() if str(item)})
    if {"symbol", "trade_date"}.issubset(factor_sample.columns):
        base = len(_symbol_date_keys(factor_sample))
        if capability == "style_exposure":
            return base * len(_requested_style_factors(requested_style_factors))
        return base
    return int(len(factor_sample))


def _symbol_coverage(frame: pd.DataFrame, factor_sample: pd.DataFrame) -> dict[str, Any]:
    if "symbol" not in frame.columns or "symbol" not in factor_sample.columns:
        return {"coverage_ratio": 0.0, "missing_rate": 1.0, "sample_count": int(len(factor_sample)), "covered_count": 0}
    requested = {str(item).strip() for item in factor_sample["symbol"].dropna().tolist() if str(item).strip()}
    covered = {str(item).strip() for item in frame["symbol"].dropna().tolist() if str(item).strip()}
    covered_count = len(requested & covered)
    sample_count = len(requested)
    return _coverage_payload(sample_count, covered_count)


def _symbol_date_coverage(frame: pd.DataFrame, factor_sample: pd.DataFrame) -> dict[str, Any]:
    if not {"symbol", "trade_date"}.issubset(frame.columns) or not {"symbol", "trade_date"}.issubset(factor_sample.columns):
        return _symbol_coverage(frame, factor_sample)
    requested = _symbol_date_keys(factor_sample)
    covered = _symbol_date_keys(frame)
    return _coverage_payload(len(requested), len(requested & covered))


def _style_factor_coverage(
    frame: pd.DataFrame,
    factor_sample: pd.DataFrame,
    requested_style_factors: Sequence[str] | None,
) -> dict[str, Any]:
    if not {"symbol", "trade_date"}.issubset(frame.columns) or not {"symbol", "trade_date"}.issubset(factor_sample.columns):
        return _symbol_coverage(frame, factor_sample)
    if "style_factor" not in frame.columns:
        return _coverage_payload(_sample_denominator("style_exposure", factor_sample, requested_style_factors), 0)
    factors = _requested_style_factors(requested_style_factors)
    requested = {
        (symbol, trade_date, factor)
        for symbol, trade_date in _symbol_date_keys(factor_sample)
        for factor in factors
    }
    work = frame.copy()
    work["_exposure_trade_date"] = _series_to_dates(work["trade_date"]).map(lambda item: "" if pd.isna(item) else item.isoformat())
    covered = {
        (str(row["symbol"]).strip(), str(row["_exposure_trade_date"]), str(row["style_factor"]).strip())
        for _, row in work.iterrows()
        if str(row.get("symbol", "")).strip() and str(row.get("style_factor", "")).strip()
    }
    return _coverage_payload(len(requested), len(requested & covered))


def _symbol_date_keys(frame: pd.DataFrame) -> set[tuple[str, str]]:
    work = frame.copy()
    work["_exposure_trade_date"] = _series_to_dates(work["trade_date"]).map(lambda item: "" if pd.isna(item) else item.isoformat())
    return {
        (str(row["symbol"]).strip(), str(row["_exposure_trade_date"]))
        for _, row in work.iterrows()
        if str(row.get("symbol", "")).strip() and str(row.get("_exposure_trade_date", "")).strip()
    }


def _coverage_payload(sample_count: int, covered_count: int) -> dict[str, Any]:
    ratio = 1.0 if sample_count == 0 else covered_count / sample_count
    return {
        "coverage_ratio": float(ratio),
        "missing_rate": float(1.0 - ratio),
        "sample_count": int(sample_count),
        "covered_count": int(covered_count),
    }


def _requested_style_factors(value: Sequence[str] | None) -> tuple[str, ...]:
    factors = tuple(str(item).strip() for item in (value or ("beta",)) if str(item).strip())
    return factors or ("beta",)


def _coerce_exposure_matrix(value: ExposureAvailabilityMatrix | Mapping[str, Any]) -> ExposureAvailabilityMatrix:
    if isinstance(value, ExposureAvailabilityMatrix):
        return value
    entries: dict[str, ExposureAvailabilityEntry] = {}
    for capability, raw in dict(value).items():
        if isinstance(raw, ExposureAvailabilityEntry):
            entries[str(capability)] = raw
        elif isinstance(raw, Mapping):
            entries[str(capability)] = ExposureAvailabilityEntry(
                capability=str(raw.get("capability") or capability),
                status=str(raw.get("status") or "unknown"),
                coverage_ratio=float(raw.get("coverage_ratio") or 0.0),
                missing_rate=float(raw.get("missing_rate") or 0.0),
                sample_count=int(raw.get("sample_count") or 0),
                missing_count=int(raw.get("missing_count") or 0),
                as_of_join_violation_count=int(raw.get("as_of_join_violation_count") or 0),
                required_for_claims=[str(item) for item in raw.get("required_for_claims") or []],
                missing_reason=str(raw.get("missing_reason") or raw.get("reason") or ""),
                source_dataset=str(raw.get("source_dataset")) if raw.get("source_dataset") else None,
                required_columns=[str(item) for item in raw.get("required_columns") or []],
                observed_columns=[str(item) for item in raw.get("observed_columns") or []],
                missing_columns=[str(item) for item in raw.get("missing_columns") or []],
                lineage_status=str(raw.get("lineage_status")) if raw.get("lineage_status") else None,
                remediation_spec=dict(raw.get("remediation_spec") or {}),
            )
    return ExposureAvailabilityMatrix(entries=entries)


def _first_missing_exposure_capability_for_claim(claim: str, matrix: ExposureAvailabilityMatrix) -> str:
    for capability in _exposure_claim_required_capabilities(claim):
        entry = matrix.entries.get(capability)
        if entry is None:
            return capability
        if not entry.available:
            return capability
    return ""


def _exposure_claim_required_capabilities(claim: str) -> list[str]:
    if claim in {
        "market_cap_neutral_ic",
        "market_cap_neutral",
        "size_neutral",
        "market_cap_weighted_ic",
        "capacity_size_supported",
    }:
        return ["market_cap", "float_market_cap"]
    required = []
    for capability in _EXPOSURE_CAPABILITY_ORDER:
        defaults = _EXPOSURE_CAPABILITY_DEFAULTS[capability]
        if claim in defaults["required_for_claims"]:
            required.append(capability)
    return required


def _primary_exposure_capability_for_claim(claim: str) -> str:
    required = _exposure_claim_required_capabilities(claim)
    return required[0] if required else "neutralization_metric"


def _neutralization_blocked_claim_payload(claim: str, entry: ExposureAvailabilityEntry) -> dict[str, Any]:
    reason = entry.missing_reason or f"exposure_capability_not_available:{entry.capability}"
    return {
        "claim": claim,
        "missing_capability": entry.capability,
        "missing_status": entry.status,
        "reason": reason,
        "severity": "BLOCKING",
        "source_story": "CR011-S06",
    }


def _neutralization_limitation_from_blocked_claim(blocked_claim: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "code": "neutralization_claim_blocked",
        "claim": str(blocked_claim.get("claim") or ""),
        "missing_capability": str(blocked_claim.get("missing_capability") or ""),
        "reason": str(blocked_claim.get("reason") or ""),
        "severity": str(blocked_claim.get("severity") or "BLOCKING"),
        "source_story": "CR011-S06",
    }


def _neutralization_status(blocked_claims: Sequence[Mapping[str, Any]]) -> str:
    if not blocked_claims:
        return "pass"
    if any(str(item.get("reason") or "") == "pit_universe_gate_not_passed" for item in blocked_claims):
        return "blocked_non_pit"
    if all(str(item.get("reason") or "") == "neutralization_metric_missing" for item in blocked_claims):
        return "metric_missing"
    capabilities = {str(item.get("missing_capability") or "") for item in blocked_claims}
    if "industry_classification" in capabilities:
        return "blocked_missing_industry"
    if {"market_cap", "float_market_cap"} & capabilities:
        return "blocked_missing_market_cap"
    if "style_exposure" in capabilities:
        return "blocked_missing_style"
    return "blocked_missing_exposure"


def _metric_value(metrics: Mapping[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if _is_empty(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_neutralization_gate_result(
    value: NeutralizationClaimGateResult | Mapping[str, Any],
) -> NeutralizationClaimGateResult:
    if isinstance(value, NeutralizationClaimGateResult):
        return value
    raw = dict(value)
    return NeutralizationClaimGateResult(
        neutralization_status=str(raw.get("neutralization_status") or "blocked_missing_exposure"),
        raw_ic=_metric_value(raw, "raw_ic"),
        industry_neutral_ic=_metric_value(raw, "industry_neutral_ic"),
        market_cap_neutral_ic=_metric_value(raw, "market_cap_neutral_ic"),
        style_neutral_ic=_metric_value(raw, "style_neutral_ic"),
        allowed_claims=[str(item) for item in raw.get("allowed_claims") or []],
        blocked_claims=[dict(item) for item in raw.get("blocked_claims") or [] if isinstance(item, Mapping)],
        known_limitations=list(raw.get("known_limitations") or []),
        exposure_availability=dict(raw.get("exposure_availability") or {}),
        gate_status=str(raw.get("gate_status") or GateStatus.PASS.value),
    )


def _dedupe_json_safe(values: Sequence[Any]) -> list[Any]:
    seen: set[str] = set()
    output: list[Any] = []
    for value in values:
        safe = _json_safe(value)
        key = json_key(safe)
        if key in seen:
            continue
        seen.add(key)
        output.append(safe)
    return output


def json_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _ordered_unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _bool_series(series: pd.Series) -> pd.Series:
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}

    return series.map(coerce).astype(bool)


def _json_safe(value: Any, key: str = "") -> Any:
    if key in {
        "network_calls",
        "lake_writes",
        "credential_reads",
        "legacy_data_operations",
        "provider_fetch",
        "lake_write",
        "credential_read",
        "legacy_data_operation",
        "old_report_read",
        "old_report_overwrite",
        "duckdb_dependency_change",
        "duckdb_write",
        "catalog_current_pointer_publish",
        "s09_real_execution",
        "candidate_lake_scan",
        "duckdb_open",
        "duckdb_sql_view",
        "docs_write",
    }:
        return value
    if _SENSITIVE_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(item_key): _json_safe(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, str):
        return _SENSITIVE_VALUE_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value).replace("\n", " ").replace("\r", " ")
    return value


__all__ = (
    "AdjustmentAuditResult",
    "AdjustmentGovernanceStatus",
    "AllowedClaimsResult",
    "AuxiliaryAvailabilityEntry",
    "AuxiliaryAvailabilityMatrix",
    "ConsumerGuidance",
    "ExecutionPolicyRequest",
    "ExecutionPolicyResult",
    "ExposureAvailabilityEntry",
    "ExposureAvailabilityMatrix",
    "GateResult",
    "GateStatus",
    "LEGACY_REPORT_POLICY",
    "CR013_PERMISSION_COUNTERS",
    "CR014_RESEARCH_CONSUMER_FORBIDDEN_COUNTERS",
    "CR017_CONSUMER_FORBIDDEN_COUNTERS",
    "CR017_UNSUPPORTED_EXECUTION_FEATURES",
    "CR018_P1_CLAIM_ALLOWED_COUNT_FIELDS",
    "CR018_P1_FIELD_REQUIREMENTS_BY_CLAIM",
    "CR018_P1_FORBIDDEN_OPERATION_COUNTERS",
    "CR018_S08_OPERATION_COUNTERS",
    "CR018_S08_PRODUCTION_CURRENT_TRUTH_SCHEMA",
    "CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN",
    "CR018_S08_REASON_CATALOG_NOT_PUBLISHED",
    "CR018_S08_REASON_PROXY_INPUT_FORBIDDEN",
    "CR018_S08_REASON_REQUIRED_MISSING",
    "CR018_S08_STATUS_BLOCKED",
    "CR018_S08_STATUS_PASS",
    "DuckDbEvidenceRef",
    "NeutralizationClaimGateResult",
    "RESEARCH_INPUT_REQUIRED_FIELDS",
    "RESEARCH_INPUT_SCHEMA_NAME",
    "ResearchConsumerBoundaryCheck",
    "ResearchConsumerRequest",
    "ResearchDataset",
    "ResearchDatasetIssue",
    "ResearchDatasetRequest",
    "ResearchDatasetStatus",
    "ResearchInputMetadata",
    "ResearchInputMetadataError",
    "ResearchInputMetadataIssue",
    "TradabilityGateMatrix",
    "TradabilityGateRow",
    "apply_auxiliary_data_contract",
    "apply_adjustment_audit_gate",
    "apply_tradability_gates",
    "attach_execution_claim_metadata",
    "attach_unsupported_claims_to_research_metadata",
    "apply_label_window_policy",
    "assert_no_derived_real_vwap_claim",
    "benchmark_metadata_from_result",
    "build_auxiliary_availability",
    "build_cr018_p1_claim_boundary",
    "build_exposure_availability_matrix",
    "build_liquidity_capacity_inputs",
    "build_research_dataset",
    "build_research_dataset_from_published_truth",
    "load_production_current_truth_dataset",
    "build_research_input_metadata",
    "build_tradability_gate_matrix",
    "evaluate_adjustment_gate",
    "evaluate_allowed_claims",
    "evaluate_adjustment_audit",
    "evaluate_execution_price_gate",
    "evaluate_robust_validation_claims",
    "evaluate_neutralization_claims",
    "evaluate_label_window_gate",
    "evaluate_quality_gate",
    "evaluate_research_gates",
    "extract_adjustment_policies",
    "merge_auxiliary_claims_into_metadata",
    "merge_capacity_cost_metadata",
    "merge_exposure_claims_into_metadata",
    "merge_execution_metadata",
    "merge_factor_audit_metadata",
    "metadata_to_dict",
    "read_execution_price_audit",
    "consume_duckdb_audit_evidence_ref",
    "resolve_execution_claim_boundary",
    "resolve_execution_price_policy",
    "assert_research_consumer_forbidden_operations",
    "build_adjustment_blocked_claims",
    "validate_research_input_metadata",
    "build_consumer_guidance_matrix",
    "render_migration_guide_sections",
    "research_dataset_policy_metadata",
)
