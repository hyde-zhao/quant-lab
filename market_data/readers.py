"""canonical/gold parquet 只读 reader。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .catalog import CatalogEntry, CatalogError, CatalogStore
from .contracts import (
    DATASETS,
    DATASET_SCHEMA_REGISTRY,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_FAILED,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from .contracts import DATASET_INDEX_MEMBERS, DATASET_TRADE_CALENDAR
from .lake_layout import LakeLayout
from .validation import validate_adjustment_consistency, validate_pit_asof


class ReaderBoundaryError(RuntimeError):
    """reader 边界或读取请求不合法。"""


DATASET_CORPORATE_ACTIONS = "corporate_actions"


@dataclass(frozen=True, slots=True)
class QualityPolicy:
    allow_warn: bool = False
    required: bool = False


@dataclass(frozen=True, slots=True)
class ReaderResult:
    status: str
    frame: pd.DataFrame | None = None
    issues: list[dict[str, Any]] = field(default_factory=list)
    catalog_entry: CatalogEntry | None = None
    remediation_spec: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status == "available"


@dataclass(frozen=True, slots=True)
class LightweightInputRequest:
    """轻量回测只读输入请求。"""

    dataset: str = DATASET_PRICES
    lake_root: str | Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    adjustment_policy: str = "qfq"
    quality_policy: str = "require_pass"
    input_mode: str = "canonical_gold"
    legacy_flat_enabled: bool = False
    legacy_flat_dir: str | Path | None = None


@dataclass(frozen=True, slots=True)
class ResearchInputReaderRequest:
    """研究数据集批量只读输入请求。

    该 helper 服务 engine 侧 builder，但不导入 engine 类型；缺少显式
    lake_root 时直接返回 typed missing，避免 read_dataset 的 env fallback。
    """

    lake_root: str | Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    datasets: tuple[str, ...] = (DATASET_PRICES, DATASET_TRADE_CALENDAR, DATASET_INDEX_MEMBERS)
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None
    index_code: str | None = None
    exchange: str | None = None
    require_prices: bool = True
    require_calendar: bool = True
    require_index_members: bool = True
    require_stock_lifecycle: bool = False


@dataclass(frozen=True, slots=True)
class AuxiliaryInputRequest:
    """S06 辅助数据只读 readiness 请求。

    该请求只表达消费侧需要哪些辅助 capability，不授权抓取、补数或写湖。
    """

    lake_root: str | Path | None = None
    capabilities: tuple[str, ...] = (
        "tradability",
        "ohlcv_vwap",
        "industry_classification",
        "market_cap",
        "adjustment_audit",
        "liquidity",
        "style_exposure",
        "pit_universe",
        "label_quality",
    )
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None


@dataclass(frozen=True, slots=True)
class ExposureInputRequest:
    """CR011-S06 行业 / 市值 / 风格暴露只读请求。"""

    lake_root: str | Path | None = None
    capabilities: tuple[str, ...] = (
        "industry_classification",
        "market_cap",
        "float_market_cap",
        "style_exposure",
    )
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    decision_time: str | None = None
    classification_standard: str | None = None
    style_factors: tuple[str, ...] = ("beta",)
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None
    pit_required: bool = True
    source_datasets: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TradabilityInputRequest:
    """S03 可交易性 gate 只读输入请求。

    该请求必须显式传入 lake_root；缺失或指向 repo `data/**` 时直接返回
    typed missing / invalid，不触发 env fallback、补数、联网或写湖。
    """

    lake_root: str | Path | None = None
    trade_dates: tuple[str, ...] | None = None
    symbols: tuple[str, ...] | None = None
    start_date: str | None = None
    end_date: str | None = None
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None
    include_lifecycle: bool = True


@dataclass(frozen=True, slots=True)
class ExecutionFeedRequest:
    """S04 OHLCV / VWAP 执行价 feed 只读请求。

    该请求必须显式传入 lake_root；缺失或指向 repo `data/**` 时直接返回
    typed missing / invalid，不触发 env fallback、补数、联网或写湖。
    """

    lake_root: str | Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    trade_dates: tuple[str, ...] | None = None
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None


@dataclass(frozen=True, slots=True)
class AdjustmentAuditRequest:
    """S05 复权与公司行动审计只读输入请求。"""

    lake_root: str | Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    adjustment_policy: str = "qfq"
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None
    decision_time: str | None = None
    require_corporate_actions: bool = True


@dataclass(frozen=True, slots=True)
class AdjustmentAuditReaderResult:
    """reader 层 adjustment audit 聚合结果。"""

    status: str
    adjustment_policy: str
    adj_factor_lineage: dict[str, Any]
    corporate_action_status: str
    adjustment_audit_status: str
    mixed_adjustment_policy_count: int = 0
    issues: list[dict[str, Any]] = field(default_factory=list)
    reader_results: dict[str, ReaderResult] = field(default_factory=dict)
    remediation_spec: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status == "available" and self.adjustment_audit_status == "pass"

    def to_metadata(self) -> dict[str, Any]:
        lineage_checksum = self.adj_factor_lineage.get("lineage_raw_checksum")
        corporate_action_missing_reason = _first_issue_code_for_dataset(self.issues, DATASET_CORPORATE_ACTIONS)
        return {
            "adjustment_policy": self.adjustment_policy,
            "adj_factor_lineage": dict(self.adj_factor_lineage),
            "corporate_action_status": self.corporate_action_status,
            "corporate_action_missing_reason": corporate_action_missing_reason,
            "adjustment_audit_status": self.adjustment_audit_status,
            "lineage_raw_checksum": lineage_checksum,
            "mixed_adjustment_policy_count": int(self.mixed_adjustment_policy_count),
            "issues": list(self.issues),
            "remediation_spec": dict(self.remediation_spec),
        }


@dataclass(frozen=True, slots=True)
class BacktraderCleanFeedRequest:
    """Backtrader clean feed 只读输入请求。

    S03 边界要求该入口只读 canonical/gold clean feed；必须由调用方显式传入
    lake_root，避免运行期回退到 env/token 或旧 data 目录。
    """

    dataset: str = DATASET_PRICES
    lake_root: str | Path | None = None
    start_date: str | None = None
    end_date: str | None = None
    symbols: tuple[str, ...] | None = None
    adjustment_policy: str = "qfq"
    quality_policy: str = "require_pass"
    benchmark_result: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class LightweightInputResult:
    """轻量回测只读输入结果。"""

    status: str
    close_df: pd.DataFrame | None = None
    universe: list[str] = field(default_factory=list)
    calendar: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, Any]] = field(default_factory=list)
    remediation_job_spec: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True, slots=True)
class BacktraderCleanFeedBundle:
    """Backtrader 只读 clean feed bundle。

    该对象只承载内存 DataFrame、合同元数据与 lineage 标识，不承载 raw/manifest
    路径、数据层运行句柄或可执行补数计划。
    """

    status: str
    ohlcv: pd.DataFrame | None = None
    calendar: list[Any] = field(default_factory=list)
    factor_panel: pd.DataFrame | None = None
    score: pd.DataFrame | None = None
    benchmark_result: Mapping[str, Any] | None = None
    input_contract: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, Any]] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)
    remediation_job_spec: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.status == "available"


def _canonical_paths(layout: LakeLayout, dataset: str) -> list[Path]:
    root = layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _policy(value: QualityPolicy | Mapping[str, Any] | str | None, required: bool) -> QualityPolicy:
    if isinstance(value, QualityPolicy):
        return QualityPolicy(allow_warn=value.allow_warn, required=value.required or required)
    if isinstance(value, Mapping):
        return QualityPolicy(allow_warn=bool(value.get("allow_warn", False)), required=bool(value.get("required", required)))
    if value == "allow_warn":
        return QualityPolicy(allow_warn=True, required=required)
    return QualityPolicy(required=required)


def _lake_root(value: str | Path | None) -> Path | None:
    if value is not None:
        return Path(value)
    env_value = os.getenv("MARKET_DATA_LAKE_ROOT")
    return Path(env_value) if env_value else None


def _entry_path(lake_root: Path, path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else lake_root / candidate


def _read_paths(paths: Sequence[Path]) -> pd.DataFrame:
    if not paths:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)


def _entry_paths(layout: LakeLayout, dataset: str, entry: CatalogEntry) -> list[Path]:
    root = layout.lake_root
    canonical_path = _entry_path(root, entry.canonical_path)
    if canonical_path and canonical_path.exists():
        if canonical_path.is_dir():
            return sorted(
                path
                for path in canonical_path.rglob("*.parquet")
                if ".tmp" not in path.name
            )
        return [canonical_path]
    if entry.latest_manifest_run_id:
        run_root = (
            layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
            / f"run_id={entry.latest_manifest_run_id}"
        )
        if run_root.exists():
            return sorted(
                path
                for path in run_root.rglob("*.parquet")
                if ".tmp" not in path.name
            )
    return _canonical_paths(layout, dataset)


def _filter_frame(
    frame: pd.DataFrame,
    *,
    start: str | None = None,
    end: str | None = None,
    symbols: Sequence[str] | None = None,
    index_code: str | None = None,
    exchange: str | None = None,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    date_column = "trade_date" if "trade_date" in frame.columns else "event_date" if "event_date" in frame.columns else ""
    if start is not None and date_column:
        frame = frame[frame[date_column].astype(str) >= str(start)]
    if end is not None and date_column:
        frame = frame[frame[date_column].astype(str) <= str(end)]
    if symbols is not None and "symbol" in frame.columns:
        symbol_set = {str(item) for item in symbols}
        frame = frame[frame["symbol"].astype(str).isin(symbol_set)]
    if index_code is not None and "index_code" in frame.columns:
        frame = frame[frame["index_code"].astype(str) == str(index_code)]
    if exchange is not None and "exchange" in frame.columns:
        frame = frame[frame["exchange"].astype(str).str.upper() == str(exchange).upper()]
    if columns is not None:
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ReaderBoundaryError(f"请求列不存在: {','.join(missing)}")
        frame = frame[list(columns)]
    return frame.reset_index(drop=True)


def _column_values(frame: pd.DataFrame, column: str) -> set[str]:
    if column not in frame.columns or frame.empty:
        return set()
    return {str(item) for item in frame[column].dropna().unique() if str(item)}


def _readiness_issues(dataset: str, frame: pd.DataFrame) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    readiness_values = _column_values(frame, "readiness_status")
    pit_values = _column_values(frame, "pit_status")
    if readiness_values and readiness_values != {READINESS_STATUS_AVAILABLE}:
        issues.append(
            {
                "code": "readiness_not_available",
                "dataset": dataset,
                "readiness_status": sorted(readiness_values),
            }
        )
    if PIT_STATUS_FAILED in pit_values:
        issues.append({"code": "pit_failed", "dataset": dataset})
    if PIT_STATUS_INCOMPLETE in pit_values:
        issues.append({"code": "pit_incomplete", "dataset": dataset})
    if PIT_STATUS_NON_PIT_SNAPSHOT in pit_values:
        issues.append({"code": "non_pit_snapshot", "dataset": dataset})
    if dataset == DATASET_INDEX_MEMBERS and "is_pit_universe" in frame.columns:
        if not frame.empty and not bool(frame["is_pit_universe"].astype(bool).all()):
            issues.append({"code": "non_pit_universe", "dataset": dataset})
    return issues


def _readiness_remediation(dataset: str) -> dict[str, Any]:
    return {
        "action": "run_explicit_market_data_job",
        "dataset": dataset,
        "dry_run_default": True,
        "auto_execute": False,
    }


_W3_UNRESOLVED_DATASETS = frozenset(
    {
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    }
)


def _w3_unresolved_result(dataset: str, policy: QualityPolicy) -> ReaderResult:
    status = "required_missing" if policy.required else "unavailable"
    return ReaderResult(
        status=status,
        issues=[
            {
                "code": "w3_source_unresolved",
                "dataset": dataset,
                "reason": "exact source/interface 未确认，禁止伪造可用数据",
            }
        ],
        remediation_spec={
            "action": "confirm_exact_w3_source_interface_then_plan_data_story",
            "dataset": dataset,
            "dry_run_default": True,
            "auto_execute": False,
        },
    )


def _w3_contract_issues(dataset: str, frame: pd.DataFrame, entry: CatalogEntry) -> list[dict[str, Any]]:
    """校验 W3 数据集必须显式声明 source/interface 与 available_at。"""

    if dataset not in _W3_UNRESOLVED_DATASETS:
        return []
    issues: list[dict[str, Any]] = []
    required_fields = tuple(DATASET_SCHEMA_REGISTRY.get(dataset, {}).get("w3_required", ()))
    missing_fields = [field for field in required_fields if field not in frame.columns]
    if missing_fields:
        issues.append(
            {
                "code": "w3_required_fields_missing",
                "dataset": dataset,
                "fields": missing_fields,
            }
        )
    if "available_at" in required_fields:
        if "available_at" not in frame.columns or (
            not frame.empty and frame["available_at"].isna().all()
        ):
            issues.append(
                {
                    "code": "available_at_missing",
                    "dataset": dataset,
                    "reason": "W3 决策输入必须显式提供 available_at",
                }
            )
    source_interface = str(entry.source_interface or "").strip().upper()
    if source_interface in {"", "UNKNOWN", "UNRESOLVED"}:
        issues.append(
            {
                "code": "w3_source_unresolved",
                "dataset": dataset,
                "reason": "catalog source_interface 未冻结",
            }
        )
    if "source_interface" in frame.columns and not frame.empty:
        frame_interfaces = {
            str(value).strip().upper()
            for value in frame["source_interface"].dropna().unique()
            if str(value).strip()
        }
        if not frame_interfaces or frame_interfaces & {"UNKNOWN", "UNRESOLVED"}:
            issues.append(
                {
                    "code": "w3_source_unresolved",
                    "dataset": dataset,
                    "reason": "canonical source_interface 未冻结",
                    "source_interface": sorted(frame_interfaces),
                }
            )
    return issues


_AUXILIARY_CAPABILITY_DATASETS = {
    "tradability": DATASET_PRICES,
    "ohlcv_vwap": DATASET_PRICES,
    "industry_classification": "industry_classification",
    "market_cap": "market_cap",
    "adjustment_audit": DATASET_PRICES,
    "liquidity": DATASET_PRICES,
    "style_exposure": "style_exposure",
    "pit_universe": DATASET_INDEX_MEMBERS,
    "label_quality": "label_window",
}

_EXPOSURE_CAPABILITY_DATASETS = {
    "industry_classification": "industry_classification",
    "market_cap": "market_cap",
    "float_market_cap": "market_cap",
    "style_exposure": "style_exposure",
}
_EXPOSURE_REQUIRED_COLUMNS = {
    "industry_classification": (
        "symbol",
        "effective_date",
        "available_at",
        "classification_standard",
        "pit_status",
    ),
    "market_cap": ("trade_date", "symbol", "market_cap", "available_at"),
    "float_market_cap": ("trade_date", "symbol", "float_market_cap", "available_at"),
    "style_exposure": (
        "trade_date",
        "symbol",
        "style_factor",
        "exposure_value",
        "model_version",
        "available_at",
    ),
}


def read_auxiliary_inputs(
    request: AuxiliaryInputRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> dict[str, ReaderResult]:
    """只读返回辅助数据 readiness，不触发补数或写湖。

    未登记或当前仓库尚未生产的数据集返回 typed unavailable；remediation
    只描述人工后续动作，始终 `auto_execute=false`。
    """

    req = _coerce_auxiliary_input_request(request)
    reader_fn = reader or read_dataset
    if req.lake_root is None:
        return {
            capability: _auxiliary_reader_error(capability, "required_missing", "lake_root_missing")
            for capability in req.capabilities
        }
    if _is_repo_data_path(req.lake_root):
        return {
            capability: _auxiliary_reader_error(capability, "invalid_request", "repo_data_reference_only")
            for capability in req.capabilities
        }

    results: dict[str, ReaderResult] = {}
    for capability in req.capabilities:
        dataset = _AUXILIARY_CAPABILITY_DATASETS.get(capability)
        if dataset is None or dataset not in DATASETS:
            results[capability] = _auxiliary_reader_error(capability, "unavailable", "auxiliary_dataset_not_registered")
            continue
        filters: dict[str, Any] = {
            "start_date": req.start_date,
            "end_date": req.end_date,
        }
        if req.symbols is not None:
            filters["symbols"] = req.symbols
        result = reader_fn(
            dataset,
            req.lake_root,
            filters=filters,
            quality_policy=req.quality_policy,
            required=False,
        )
        results[capability] = ReaderResult(
            status=result.status,
            frame=result.frame,
            issues=[*list(result.issues), {"code": "auxiliary_capability_readiness", "capability": capability, "dataset": dataset}],
            catalog_entry=result.catalog_entry,
            remediation_spec={**(result.remediation_spec or {}), **_auxiliary_remediation(capability, dataset)},
        )
    return results


def _coerce_auxiliary_input_request(request: AuxiliaryInputRequest | Mapping[str, Any]) -> AuxiliaryInputRequest:
    if isinstance(request, AuxiliaryInputRequest):
        return request
    values = dict(request)
    if values.get("capabilities") is not None and not isinstance(values["capabilities"], tuple):
        values["capabilities"] = tuple(str(item) for item in values["capabilities"])
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    return AuxiliaryInputRequest(**values)


def _auxiliary_reader_error(capability: str, status: str, code: str) -> ReaderResult:
    dataset = _AUXILIARY_CAPABILITY_DATASETS.get(capability, capability)
    return ReaderResult(
        status=status,
        issues=[{"code": code, "capability": capability, "dataset": dataset}],
        remediation_spec=_auxiliary_remediation(capability, dataset),
    )


def _auxiliary_remediation(capability: str, dataset: str) -> dict[str, Any]:
    return {
        "action": "declare_auxiliary_missing_or_plan_explicit_data_story",
        "capability": capability,
        "dataset": dataset,
        "dry_run_default": True,
        "auto_execute": False,
    }


def read_exposure_inputs(
    request: ExposureInputRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> dict[str, ReaderResult]:
    """只读返回 exposure readiness，不触发补数、联网或写湖。

    `reader` 可以是 in-memory Mapping，用于测试或上游已读结果；未登记的真实
    source 返回 `source_unresolved`，并保持 remediation `auto_execute=false`。
    """

    req = _coerce_exposure_input_request(request)
    supplied_results = reader if isinstance(reader, Mapping) else None
    if supplied_results is None:
        if req.lake_root is None:
            return {
                capability: _exposure_reader_error(capability, "required_missing", "lake_root_missing", req)
                for capability in req.capabilities
            }
        if _is_repo_data_path(req.lake_root):
            return {
                capability: _exposure_reader_error(capability, "invalid_request", "repo_data_reference_only", req)
                for capability in req.capabilities
            }

    results: dict[str, ReaderResult] = {}
    reader_fn = reader or read_dataset
    for capability in req.capabilities:
        dataset = _exposure_dataset_for(capability, req)
        if supplied_results is not None:
            supplied = supplied_results.get(capability, supplied_results.get(dataset))
            if supplied is None:
                results[capability] = _exposure_reader_error(
                    capability,
                    "source_unresolved",
                    "exposure_source_unresolved",
                    req,
                    dataset=dataset,
                )
            else:
                results[capability] = _exposure_reader_result(
                    capability,
                    dataset,
                    _coerce_reader_result(supplied, dataset),
                    req,
                )
            continue

        if capability not in _EXPOSURE_CAPABILITY_DATASETS or dataset not in DATASETS:
            results[capability] = _exposure_reader_error(
                capability,
                "source_unresolved",
                "exposure_source_unresolved",
                req,
                dataset=dataset,
            )
            continue
        filters: dict[str, Any] = {"start_date": req.start_date, "end_date": req.end_date}
        if req.symbols is not None:
            filters["symbols"] = req.symbols
        raw_result = reader_fn(
            dataset,
            req.lake_root,
            filters=filters,
            quality_policy=req.quality_policy,
            required=False,
        )
        result = raw_result if isinstance(raw_result, ReaderResult) else _coerce_reader_result(raw_result, dataset)
        results[capability] = _exposure_reader_result(capability, dataset, result, req)
    return results


def _coerce_exposure_input_request(request: ExposureInputRequest | Mapping[str, Any]) -> ExposureInputRequest:
    if isinstance(request, ExposureInputRequest):
        return request
    values = dict(request)
    if values.get("capabilities") is not None and not isinstance(values["capabilities"], tuple):
        values["capabilities"] = tuple(str(item) for item in values["capabilities"])
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    if values.get("style_factors") is not None and not isinstance(values["style_factors"], tuple):
        values["style_factors"] = tuple(str(item).strip() for item in values["style_factors"] if str(item).strip())
    return ExposureInputRequest(**values)


def _exposure_dataset_for(capability: str, req: ExposureInputRequest) -> str:
    return str(req.source_datasets.get(capability) or _EXPOSURE_CAPABILITY_DATASETS.get(capability, capability))


def _exposure_reader_result(
    capability: str,
    dataset: str,
    result: ReaderResult,
    req: ExposureInputRequest,
) -> ReaderResult:
    frame = result.frame
    observed_columns = list(frame.columns) if frame is not None else []
    missing_columns = _exposure_missing_columns(capability, observed_columns)
    issues = list(result.issues)
    status = result.status
    if result.status == "available" and missing_columns:
        status = "required_missing"
        issues.append(
            {
                "code": "exposure_required_columns_missing",
                "capability": capability,
                "dataset": dataset,
                "missing_columns": missing_columns,
            }
        )
    issues.append(
        {
            "code": "exposure_capability_readiness",
            "capability": capability,
            "dataset": dataset,
            "required_columns": list(_EXPOSURE_REQUIRED_COLUMNS.get(capability, ())),
            "observed_columns": observed_columns,
            "missing_columns": missing_columns,
            "coverage": _exposure_reader_coverage(frame, req),
            "pit_required": bool(req.pit_required),
        }
    )
    remediation = {
        **dict(result.remediation_spec or {}),
        **_exposure_remediation(capability, dataset, missing_columns),
    }
    return ReaderResult(
        status=status,
        frame=frame,
        issues=issues,
        catalog_entry=result.catalog_entry,
        remediation_spec=remediation,
    )


def _exposure_missing_columns(capability: str, observed_columns: Sequence[str]) -> list[str]:
    observed = {str(column) for column in observed_columns}
    missing = [column for column in _EXPOSURE_REQUIRED_COLUMNS.get(capability, ()) if column not in observed]
    if capability == "industry_classification" and not ({"industry_code", "industry_name"} & observed):
        missing.append("industry_code|industry_name")
    return missing


def _exposure_reader_coverage(frame: pd.DataFrame | None, req: ExposureInputRequest) -> dict[str, Any]:
    requested_symbols = {str(item).strip() for item in req.symbols or () if str(item).strip()}
    if frame is None or frame.empty:
        return {"coverage_ratio": 0.0, "missing_rate": 1.0, "sample_count": len(requested_symbols), "covered_count": 0}
    if not requested_symbols or "symbol" not in frame.columns:
        return {"coverage_ratio": 1.0, "missing_rate": 0.0, "sample_count": int(len(frame)), "covered_count": int(len(frame))}
    covered_symbols = {str(item).strip() for item in frame["symbol"].dropna().tolist() if str(item).strip()}
    covered_count = len(requested_symbols & covered_symbols)
    sample_count = len(requested_symbols)
    ratio = 1.0 if sample_count == 0 else covered_count / sample_count
    return {
        "coverage_ratio": float(ratio),
        "missing_rate": float(1.0 - ratio),
        "sample_count": sample_count,
        "covered_count": covered_count,
    }


def _exposure_reader_error(
    capability: str,
    status: str,
    code: str,
    req: ExposureInputRequest,
    *,
    dataset: str | None = None,
) -> ReaderResult:
    source_dataset = dataset or _exposure_dataset_for(capability, req)
    return ReaderResult(
        status=status,
        issues=[{"code": code, "capability": capability, "dataset": source_dataset}],
        remediation_spec=_exposure_remediation(capability, source_dataset, []),
    )


def _exposure_remediation(capability: str, dataset: str, missing_columns: Sequence[str]) -> dict[str, Any]:
    return {
        "action": "declare_exposure_missing_or_plan_explicit_data_story",
        "capability": capability,
        "dataset": dataset,
        "required_columns": list(_EXPOSURE_REQUIRED_COLUMNS.get(capability, ())),
        "missing_columns": list(missing_columns),
        "dry_run_default": True,
        "auto_execute": False,
    }


def read_tradability_inputs(
    request: TradabilityInputRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> dict[str, ReaderResult]:
    """读取 S03 可交易性 gate 所需输入，不触发补数或真实 provider。

    返回 key 至少包含 `trade_status`、`prices_limit`、`events`；默认还包含
    `stock_basic` lifecycle 结果。任何 source/interface、schema 或
    `available_at` 缺失均通过 ReaderResult 暴露，并保证 remediation
    `auto_execute=false`。
    """

    req = _coerce_tradability_input_request(request)
    datasets = [DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS]
    if req.include_lifecycle:
        datasets.append(DATASET_STOCK_BASIC)
    if req.lake_root is None:
        return {
            dataset: _tradability_reader_error(dataset, "required_missing", "lake_root_missing")
            for dataset in datasets
        }
    if _is_repo_data_path(req.lake_root):
        return {
            dataset: _tradability_reader_error(dataset, "invalid_request", "repo_data_reference_only")
            for dataset in datasets
        }

    start_date, end_date = _tradability_date_window(req)
    reader_fn = reader or read_dataset
    results: dict[str, ReaderResult] = {}
    for dataset in (DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS):
        filters: dict[str, Any] = {"start_date": start_date, "end_date": end_date}
        if req.symbols is not None:
            filters["symbols"] = req.symbols
        result = reader_fn(
            dataset,
            req.lake_root,
            filters=filters,
            quality_policy=req.quality_policy,
            required=True,
        )
        results[dataset] = _with_auto_execute_false(result, dataset)
    if req.include_lifecycle:
        results[DATASET_STOCK_BASIC] = read_stock_lifecycle(
            req.lake_root,
            symbols=req.symbols,
            start_date=start_date,
            end_date=end_date,
            required=True,
            reader=reader_fn,
            quality_policy=req.quality_policy,
        )
    return results


def read_execution_feed(
    request: ExecutionFeedRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> ReaderResult:
    """读取 prices current truth 并暴露逻辑 execution_prices view。

    本入口只消费 `DATASET_PRICES`，不从 amount/volume 派生真实 VWAP。
    VWAP 缺失会写入 `vwap_status=required_missing` 与 typed issue，供消费侧
    显式阻断或选择 `close_proxy` 降级。
    """

    req = _coerce_execution_feed_request(request)
    if req.lake_root is None:
        return _execution_feed_error("required_missing", "lake_root_missing")
    if _is_repo_data_path(req.lake_root):
        return _execution_feed_error("invalid_request", "repo_data_reference_only")

    start_date, end_date = _execution_date_window(req)
    filters: dict[str, Any] = {"start_date": start_date, "end_date": end_date}
    if req.symbols is not None:
        filters["symbols"] = req.symbols

    reader_fn = reader or read_dataset
    result = reader_fn(
        DATASET_PRICES,
        req.lake_root,
        filters=filters,
        quality_policy=_policy(req.quality_policy, True),
        required=True,
    )
    if not isinstance(result, ReaderResult):
        return _execution_feed_error("invalid_request", "reader_result_invalid")
    result = _with_auto_execute_false(result, DATASET_PRICES)
    if not result.available or result.frame is None:
        return ReaderResult(
            status=result.status,
            frame=None,
            issues=[
                *list(result.issues),
                {"code": "execution_prices_source_unavailable", "dataset": DATASET_PRICES},
            ],
            catalog_entry=result.catalog_entry,
            remediation_spec=_normalize_reader_remediation(result.remediation_spec, DATASET_PRICES),
        )

    frame, issues = _execution_feed_frame(result.frame, result.catalog_entry)
    status = "required_missing" if any(issue.get("severity") == "ERROR" for issue in issues) else "available"
    return ReaderResult(
        status=status,
        frame=frame if status == "available" else None,
        issues=[*list(result.issues), *issues],
        catalog_entry=result.catalog_entry,
        remediation_spec=_normalize_reader_remediation(result.remediation_spec, DATASET_PRICES),
    )


def read_adjustment_audit_inputs(
    request: AdjustmentAuditRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> AdjustmentAuditReaderResult:
    """只读聚合 S05 复权 lineage 与公司行动 availability。

    该入口不会使用 `_lake_root` env fallback；缺少显式 lake_root 时直接
    返回 typed missing，便于离线测试和研究消费层安全失败。
    """

    req = _coerce_adjustment_audit_request(request)
    if req.lake_root is None:
        return _adjustment_audit_error(req, "required_missing", "lake_root_missing")
    if _is_repo_data_path(req.lake_root):
        return _adjustment_audit_error(req, "invalid_request", "repo_data_reference_only")

    filters: dict[str, Any] = {"start_date": req.start_date, "end_date": req.end_date}
    if req.symbols is not None:
        filters["symbols"] = req.symbols

    reader_fn = reader or read_dataset
    reader_results: dict[str, ReaderResult] = {}
    for dataset in (DATASET_PRICES, DATASET_ADJ_FACTOR, DATASET_CORPORATE_ACTIONS):
        result = reader_fn(
            dataset,
            req.lake_root,
            filters=filters,
            quality_policy=_policy(req.quality_policy, dataset != DATASET_CORPORATE_ACTIONS),
            required=dataset != DATASET_CORPORATE_ACTIONS or req.require_corporate_actions,
        )
        if not isinstance(result, ReaderResult):
            result = ReaderResult(
                status="invalid_request",
                issues=[{"code": "reader_result_invalid", "dataset": dataset}],
            )
        reader_results[dataset] = _with_auto_execute_false(result, dataset)

    lineage = extract_adj_factor_lineage(
        reader_results.get(DATASET_PRICES),
        reader_results.get(DATASET_ADJ_FACTOR),
    )
    corporate_action = evaluate_corporate_action_availability(
        reader_results.get(DATASET_CORPORATE_ACTIONS),
        decision_time=req.decision_time,
    )
    policy_state = _adjustment_policy_state(
        req.adjustment_policy,
        reader_results.get(DATASET_PRICES),
        reader_results.get(DATASET_ADJ_FACTOR),
    )
    issues: list[dict[str, Any]] = [
        *list(reader_results.get(DATASET_PRICES, ReaderResult(status="missing")).issues),
        *list(reader_results.get(DATASET_ADJ_FACTOR, ReaderResult(status="missing")).issues),
        *list(lineage.get("issues") or []),
        *list(corporate_action.get("issues") or []),
        *list(policy_state.get("issues") or []),
    ]

    audit_status = _adjustment_audit_status(
        policy_state=policy_state,
        lineage=lineage,
        corporate_action_status=str(corporate_action.get("corporate_action_status") or "required_missing"),
    )
    status = "available" if audit_status == "pass" else audit_status
    remediation = _adjustment_audit_remediation(
        audit_status,
        reader_results,
        lineage,
        corporate_action,
        policy_state,
    )
    policy = str(policy_state.get("adjustment_policy") or req.adjustment_policy)
    return AdjustmentAuditReaderResult(
        status=status,
        adjustment_policy=policy,
        adj_factor_lineage={key: value for key, value in lineage.items() if key != "issues"},
        corporate_action_status=str(corporate_action.get("corporate_action_status") or "required_missing"),
        adjustment_audit_status=audit_status,
        mixed_adjustment_policy_count=int(policy_state.get("mixed_adjustment_policy_count") or 0),
        issues=issues,
        reader_results=reader_results,
        remediation_spec=remediation,
    )


def extract_adj_factor_lineage(
    prices_result: ReaderResult | Mapping[str, Any] | None,
    adj_factor_result: ReaderResult | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """抽取 adj_factor lineage，不把它提升为完整公司行动审计。"""

    adj_result = _coerce_reader_result(adj_factor_result, DATASET_ADJ_FACTOR)
    prices = _coerce_reader_result(prices_result, DATASET_PRICES)
    if adj_result is not None and adj_result.status == "quality_failed":
        return {
            "status": "quality_failed",
            "source_dataset": DATASET_ADJ_FACTOR,
            "missing_reason": "adj_factor_quality_failed",
            "issues": [{"code": "adj_factor_quality_failed", "dataset": DATASET_ADJ_FACTOR}],
        }
    if adj_result is not None and adj_result.available and adj_result.frame is not None:
        payload = _lineage_payload_from_frame(DATASET_ADJ_FACTOR, adj_result.frame, adj_result.catalog_entry)
        if payload.get("lineage_raw_checksum") or payload.get("source_run_id"):
            return payload
        return {
            **payload,
            "status": "required_missing",
            "missing_reason": "adj_factor_lineage_missing",
            "issues": [{"code": "adj_factor_lineage_missing", "dataset": DATASET_ADJ_FACTOR}],
        }

    if prices is not None and prices.status == "quality_failed":
        return {
            "status": "quality_failed",
            "source_dataset": DATASET_PRICES,
            "missing_reason": "prices_quality_failed",
            "issues": [{"code": "prices_quality_failed", "dataset": DATASET_PRICES}],
        }
    if prices is not None and prices.available and prices.frame is not None and "adj_factor" in prices.frame.columns:
        payload = _lineage_payload_from_frame(DATASET_PRICES, prices.frame, prices.catalog_entry)
        payload["source_dataset"] = "prices_embedded_adj_factor"
        if payload.get("lineage_raw_checksum") or payload.get("source_run_id"):
            return payload

    missing_code = "adj_factor_required_missing"
    if adj_result is not None and adj_result.status:
        missing_code = f"adj_factor_{adj_result.status}"
    return {
        "status": "required_missing",
        "source_dataset": DATASET_ADJ_FACTOR,
        "missing_reason": missing_code,
        "issues": [{"code": missing_code, "dataset": DATASET_ADJ_FACTOR}],
    }


def evaluate_corporate_action_availability(
    corporate_action_result: ReaderResult | Mapping[str, Any] | None,
    *,
    decision_time: str | None = None,
) -> dict[str, Any]:
    """评估 corporate_actions 是否可支撑完整公司行动审计声明。"""

    result = _coerce_reader_result(corporate_action_result, DATASET_CORPORATE_ACTIONS)
    if result is None:
        return _corporate_action_result("required_missing", "corporate_actions_source_unresolved")
    if result.status == "quality_failed":
        return _corporate_action_result("quality_failed", "corporate_actions_quality_failed", result)
    if not result.available or result.frame is None:
        code = _first_issue_code(result.issues) or f"corporate_actions_{result.status or 'missing'}"
        return _corporate_action_result("required_missing", code, result)

    frame = result.frame
    required_columns = ("symbol", "event_date", "event_type", "available_at", "payload", "source_run_id", "lineage_raw_checksum")
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if frame.empty:
        return _corporate_action_result("required_missing", "corporate_actions_empty_source_unresolved", result)
    if missing_columns:
        return _corporate_action_result("required_missing", "corporate_actions_required_fields_missing", result, {"missing_columns": missing_columns})
    source_issue = _corporate_action_source_issue(result)
    if source_issue:
        return _corporate_action_result("required_missing", source_issue, result)
    if frame["available_at"].isna().any() or frame["available_at"].astype(str).str.strip().eq("").any():
        return _corporate_action_result("required_missing", "corporate_action_available_at_missing", result)
    if decision_time:
        available_at = pd.to_datetime(frame["available_at"], errors="coerce")
        decision = pd.to_datetime(decision_time, errors="coerce")
        if pd.isna(decision) or available_at.isna().any():
            return _corporate_action_result("required_missing", "corporate_action_available_at_unparseable", result)
        if bool((available_at > decision).any()):
            return _corporate_action_result("required_missing", "corporate_action_future_available_at", result)

    return {
        "corporate_action_status": "available",
        "missing_reason": "",
        "source_run_id": _first_non_empty(frame, "source_run_id"),
        "lineage_raw_checksum": _first_non_empty(frame, "lineage_raw_checksum"),
        "event_type_count": int(frame["event_type"].dropna().astype(str).nunique()),
        "row_count": int(len(frame)),
        "issues": [],
    }


def _coerce_tradability_input_request(
    request: TradabilityInputRequest | Mapping[str, Any],
) -> TradabilityInputRequest:
    if isinstance(request, TradabilityInputRequest):
        return request
    values = dict(request)
    if values.get("trade_dates") is not None and not isinstance(values["trade_dates"], tuple):
        values["trade_dates"] = tuple(str(item).strip() for item in values["trade_dates"] if str(item).strip())
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    return TradabilityInputRequest(**values)


def _coerce_execution_feed_request(
    request: ExecutionFeedRequest | Mapping[str, Any],
) -> ExecutionFeedRequest:
    if isinstance(request, ExecutionFeedRequest):
        return request
    values = dict(request)
    if values.get("trade_dates") is not None and not isinstance(values["trade_dates"], tuple):
        values["trade_dates"] = tuple(str(item).strip() for item in values["trade_dates"] if str(item).strip())
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    return ExecutionFeedRequest(**values)


def _coerce_adjustment_audit_request(
    request: AdjustmentAuditRequest | Mapping[str, Any],
) -> AdjustmentAuditRequest:
    if isinstance(request, AdjustmentAuditRequest):
        return request
    values = dict(request)
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    return AdjustmentAuditRequest(**values)


def _coerce_reader_result(value: ReaderResult | Mapping[str, Any] | None, dataset: str) -> ReaderResult | None:
    if value is None:
        return None
    if isinstance(value, ReaderResult):
        return value
    if isinstance(value, Mapping):
        return ReaderResult(
            status=str(value.get("status") or "unavailable"),
            frame=value.get("frame") if isinstance(value.get("frame"), pd.DataFrame) else None,
            issues=[dict(item) for item in value.get("issues") or [] if isinstance(item, Mapping)],
            catalog_entry=value.get("catalog_entry") if isinstance(value.get("catalog_entry"), CatalogEntry) else None,
            remediation_spec=dict(value.get("remediation_spec") or _readiness_remediation(dataset)),
        )
    return ReaderResult(status="invalid_request", issues=[{"code": "reader_result_invalid", "dataset": dataset}])


def _adjustment_audit_error(req: AdjustmentAuditRequest, status: str, code: str) -> AdjustmentAuditReaderResult:
    issue = {"code": code, "dataset": "adjustment_audit"}
    return AdjustmentAuditReaderResult(
        status=status,
        adjustment_policy=req.adjustment_policy,
        adj_factor_lineage={
            "status": "required_missing" if status != "quality_failed" else "quality_failed",
            "source_dataset": DATASET_ADJ_FACTOR,
            "missing_reason": code,
        },
        corporate_action_status="required_missing",
        adjustment_audit_status="required_missing" if status != "quality_failed" else "quality_failed",
        mixed_adjustment_policy_count=0,
        issues=[issue],
        remediation_spec={
            "action": "provide_explicit_adjustment_audit_inputs",
            "reason": code,
            "dataset": "adjustment_audit",
            "dry_run_default": True,
            "auto_execute": False,
        },
    )


def _adjustment_policy_state(
    request_policy: str,
    prices_result: ReaderResult | None,
    adj_factor_result: ReaderResult | None,
) -> dict[str, Any]:
    requested = str(request_policy or "").strip()
    policies: set[str] = set()
    for result in (prices_result, adj_factor_result):
        if result is None or result.frame is None:
            continue
        policies.update(_frame_adjustment_policies(result.frame))
        entry_values = _catalog_adjustment_policies(result.catalog_entry)
        policies.update(entry_values)
    issues: list[dict[str, Any]] = []
    status = "pass"
    if not requested:
        status = "quality_failed"
        issues.append({"code": "adjustment_policy_missing", "dataset": DATASET_PRICES})
    elif len(policies) > 1:
        status = "quality_failed"
        issues.append({"code": "adjustment_policy_mixed", "dataset": DATASET_PRICES, "policies_seen": sorted(policies)})
    elif policies and requested not in policies:
        status = "quality_failed"
        issues.append({"code": "adjustment_policy_mismatch", "dataset": DATASET_PRICES, "expected": requested, "actual": sorted(policies)})
    elif not policies:
        status = "required_missing"
        issues.append({"code": "adjustment_policy_missing", "dataset": DATASET_PRICES})
    return {
        "status": status,
        "adjustment_policy": requested,
        "policies_seen": sorted(policies),
        "mixed_adjustment_policy_count": len(policies) if len(policies) > 1 else 0,
        "issues": issues,
    }


def _frame_adjustment_policies(frame: pd.DataFrame) -> set[str]:
    if "adjustment_policy" not in frame.columns:
        return set()
    return {
        str(item).strip()
        for item in frame["adjustment_policy"].dropna().unique()
        if str(item).strip()
    }


def _catalog_adjustment_policies(entry: CatalogEntry | None) -> set[str]:
    if entry is None:
        return set()
    values: set[str] = set()
    for key in ("adjustment_policy", "policy", "data_adjustment_policy"):
        value = str(getattr(entry, key, "") or "").strip()
        if value:
            values.add(value)
    coverage = getattr(entry, "coverage", None)
    if isinstance(coverage, Mapping):
        for key in ("adjustment_policy", "policy", "data_adjustment_policy"):
            value = str(coverage.get(key) or "").strip()
            if value:
                values.add(value)
    return values


def _lineage_payload_from_frame(dataset: str, frame: pd.DataFrame, entry: CatalogEntry | None) -> dict[str, Any]:
    policies = sorted(_frame_adjustment_policies(frame) or _catalog_adjustment_policies(entry))
    payload = {
        "status": "available",
        "source_dataset": dataset,
        "source_run_id": _first_non_empty(frame, "source_run_id"),
        "lineage_raw_checksum": _first_non_empty(frame, "lineage_raw_checksum") or (entry.lineage_raw_checksum if entry else ""),
        "manifest_run_id": entry.latest_manifest_run_id if entry else _first_non_empty(frame, "manifest_run_id"),
        "source_interface": entry.source_interface if entry else _first_non_empty(frame, "source_interface"),
        "adjustment_policy": policies[0] if len(policies) == 1 else "",
        "policies_seen": policies,
        "row_count": int(len(frame)),
    }
    if "adj_factor" in frame.columns:
        payload["adj_factor_non_null_count"] = int(frame["adj_factor"].notna().sum())
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _corporate_action_result(
    status: str,
    code: str,
    result: ReaderResult | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    issue = {
        "code": code,
        "dataset": DATASET_CORPORATE_ACTIONS,
        **dict(details or {}),
    }
    return {
        "corporate_action_status": status,
        "missing_reason": code,
        "issues": [issue, *([] if result is None else list(result.issues))],
        "remediation_spec": _normalize_reader_remediation((result.remediation_spec if result else {}) or {}, DATASET_CORPORATE_ACTIONS),
    }


def _corporate_action_source_issue(result: ReaderResult) -> str:
    entry_interface = str(getattr(result.catalog_entry, "source_interface", "") or "").strip().upper()
    if entry_interface in {"", "UNKNOWN", "UNRESOLVED"}:
        return "corporate_actions_source_unresolved"
    frame = result.frame
    if frame is not None and "source_interface" in frame.columns and not frame.empty:
        interfaces = {
            str(value).strip().upper()
            for value in frame["source_interface"].dropna().unique()
            if str(value).strip()
        }
        if not interfaces or interfaces & {"UNKNOWN", "UNRESOLVED"}:
            return "corporate_actions_source_unresolved"
    return ""


def _adjustment_audit_status(
    *,
    policy_state: Mapping[str, Any],
    lineage: Mapping[str, Any],
    corporate_action_status: str,
) -> str:
    if policy_state.get("status") == "quality_failed" or lineage.get("status") == "quality_failed":
        return "quality_failed"
    if lineage.get("status") != "available":
        return "required_missing"
    if corporate_action_status == "quality_failed":
        return "quality_failed"
    if corporate_action_status != "available":
        return "required_missing"
    if policy_state.get("status") != "pass":
        return "required_missing"
    return "pass"


def _adjustment_audit_remediation(
    audit_status: str,
    reader_results: Mapping[str, ReaderResult],
    lineage: Mapping[str, Any],
    corporate_action: Mapping[str, Any],
    policy_state: Mapping[str, Any],
) -> dict[str, Any]:
    specs: list[dict[str, Any]] = []
    for dataset, result in reader_results.items():
        if result.remediation_spec:
            specs.append(_normalize_reader_remediation(result.remediation_spec, dataset))
    for payload in (lineage, corporate_action, policy_state):
        spec = payload.get("remediation_spec") if isinstance(payload, Mapping) else None
        if isinstance(spec, Mapping):
            specs.append(dict(spec))
    if not specs:
        specs.append(
            {
                "action": "no_action_required" if audit_status == "pass" else "declare_adjustment_audit_missing_or_plan_explicit_data_story",
                "dataset": "adjustment_audit",
                "dry_run_default": True,
                "auto_execute": False,
            }
        )
    return {
        "actions": specs,
        "auto_execute": False,
        "dry_run_default": True,
    }


def _first_issue_code(issues: Sequence[Mapping[str, Any]]) -> str:
    for issue in issues:
        code = str(issue.get("code") or "").strip()
        if code:
            return code
    return ""


def _first_issue_code_for_dataset(issues: Sequence[Mapping[str, Any]], dataset: str) -> str:
    for issue in issues:
        if str(issue.get("dataset") or "") == dataset:
            code = str(issue.get("code") or "").strip()
            if code:
                return code
    return ""


def _tradability_date_window(req: TradabilityInputRequest) -> tuple[str | None, str | None]:
    if req.trade_dates:
        ordered = sorted(str(item) for item in req.trade_dates if str(item))
        if ordered:
            return ordered[0], ordered[-1]
    return req.start_date, req.end_date


def _execution_date_window(req: ExecutionFeedRequest) -> tuple[str | None, str | None]:
    if req.trade_dates:
        ordered = sorted(str(item) for item in req.trade_dates if str(item))
        if ordered:
            return ordered[0], ordered[-1]
    return req.start_date, req.end_date


def _tradability_reader_error(dataset: str, status: str, code: str) -> ReaderResult:
    return ReaderResult(
        status=status,
        issues=[{"code": code, "dataset": dataset}],
        remediation_spec={
            "action": "provide_explicit_tradability_inputs",
            "dataset": dataset,
            "reason": code,
            "dry_run_default": True,
            "auto_execute": False,
        },
    )


def _execution_feed_error(status: str, code: str) -> ReaderResult:
    return ReaderResult(
        status=status,
        issues=[{"code": code, "dataset": DATASET_PRICES, "logical_dataset": "execution_prices"}],
        remediation_spec={
            "action": "provide_explicit_execution_feed_inputs",
            "dataset": DATASET_PRICES,
            "logical_dataset": "execution_prices",
            "reason": code,
            "dry_run_default": True,
            "auto_execute": False,
        },
    )


def _execution_feed_frame(frame: pd.DataFrame, entry: CatalogEntry | None) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    required = ("trade_date", "symbol", "open", "high", "low", "close", "volume", "amount")
    missing_required = [column for column in required if column not in frame.columns]
    if missing_required:
        return pd.DataFrame(), [
            {
                "code": "execution_prices_required_fields_missing",
                "dataset": DATASET_PRICES,
                "logical_dataset": "execution_prices",
                "missing_columns": missing_required,
                "severity": "ERROR",
            }
        ]

    output = frame.copy()
    issues: list[dict[str, Any]] = []
    vwap_column_missing = "vwap" not in output.columns
    if vwap_column_missing:
        output["vwap"] = pd.NA
        issues.append(
            {
                "code": "vwap_required_missing",
                "dataset": DATASET_PRICES,
                "logical_dataset": "execution_prices",
                "field": "vwap",
                "severity": "WARNING",
            }
        )
    if "vwap_status" not in output.columns:
        output["vwap_status"] = "required_missing"
        issues.append(
            {
                "code": "vwap_status_required_missing",
                "dataset": DATASET_PRICES,
                "logical_dataset": "execution_prices",
                "field": "vwap_status",
                "severity": "WARNING",
            }
        )
    output["vwap_status"] = output["vwap_status"].fillna("required_missing").astype(str).str.strip()
    output.loc[output["vwap_status"] == "", "vwap_status"] = "required_missing"
    if vwap_column_missing:
        output["vwap_status"] = "required_missing"

    if "available_at_rule" not in output.columns:
        output["available_at_rule"] = entry.available_at_rule if entry and entry.available_at_rule else "close_after_available_at"
    if "source_interface" not in output.columns:
        output["source_interface"] = entry.source_interface if entry and entry.source_interface else ""
    if "source_run_id" not in output.columns:
        output["source_run_id"] = entry.latest_manifest_run_id if entry and entry.latest_manifest_run_id else ""
    output["vwap_or_proxy"] = output["vwap_status"].map(lambda value: "vwap" if value == "available" else "missing")
    output["logical_dataset"] = "execution_prices"

    missing_lineage = []
    if output["source_interface"].astype(str).str.strip().eq("").all():
        missing_lineage.append("source_interface")
    if output["source_run_id"].astype(str).str.strip().eq("").all():
        missing_lineage.append("source_run_id")
    if missing_lineage:
        issues.append(
            {
                "code": "execution_lineage_missing",
                "dataset": DATASET_PRICES,
                "logical_dataset": "execution_prices",
                "missing_columns": missing_lineage,
                "severity": "WARNING",
            }
        )

    columns = [
        "trade_date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "vwap",
        "vwap_status",
        "vwap_or_proxy",
        "available_at_rule",
        "source_interface",
        "source_run_id",
        "logical_dataset",
    ]
    return output[columns].reset_index(drop=True), issues


def _with_auto_execute_false(result: ReaderResult, dataset: str) -> ReaderResult:
    remediation = _normalize_reader_remediation(result.remediation_spec or {}, dataset)
    if remediation == result.remediation_spec:
        return result
    return ReaderResult(
        status=result.status,
        frame=result.frame,
        issues=list(result.issues),
        catalog_entry=result.catalog_entry,
        remediation_spec=remediation,
    )


def _normalize_reader_remediation(value: Mapping[str, Any], dataset: str) -> dict[str, Any]:
    normalized = dict(value)
    normalized.setdefault("dataset", dataset)
    normalized["auto_execute"] = False
    normalized.setdefault("dry_run_default", True)
    if "dry_run" in normalized:
        normalized["dry_run"] = True
    return normalized


def read_research_inputs(
    request: ResearchInputReaderRequest | Mapping[str, Any],
    *,
    reader: Any = None,
) -> dict[str, ReaderResult]:
    """批量只读读取 research builder 所需 canonical/gold 输入。

    本函数只调度 reader，不触发抓取层、运行层或写湖层，不执行补数；当
    lake_root 缺失或指向 repo-relative data/** 时直接返回 typed result。
    """

    req = _coerce_research_input_reader_request(request)
    reader_fn = reader or read_dataset
    if req.lake_root is None:
        return {
            dataset: _research_reader_error(
                dataset,
                "required_missing" if _research_dataset_required(req, dataset) else "unavailable",
                "lake_root_missing",
            )
            for dataset in req.datasets
        }
    if _is_repo_data_path(req.lake_root):
        return {
            dataset: _research_reader_error(dataset, "invalid_request", "repo_data_reference_only")
            for dataset in req.datasets
        }

    results: dict[str, ReaderResult] = {}
    for dataset in req.datasets:
        filters: dict[str, Any] = {
            "start_date": req.start_date,
            "end_date": req.end_date,
        }
        if dataset == DATASET_PRICES and req.symbols is not None:
            filters["symbols"] = req.symbols
        if dataset == DATASET_INDEX_MEMBERS:
            if req.index_code:
                filters["index_code"] = req.index_code
            if req.symbols is not None:
                filters["symbols"] = req.symbols
        if dataset == DATASET_INDEX_WEIGHTS:
            if req.index_code:
                filters["index_code"] = req.index_code
        if dataset == DATASET_STOCK_BASIC and req.symbols is not None:
            filters["symbols"] = req.symbols
        if dataset == DATASET_TRADE_CALENDAR and req.exchange:
            filters["exchange"] = req.exchange
        if dataset == DATASET_STOCK_BASIC:
            results[dataset] = read_stock_lifecycle(
                req.lake_root,
                symbols=req.symbols,
                start_date=req.start_date,
                end_date=req.end_date,
                required=_research_dataset_required(req, dataset),
                reader=reader_fn,
                quality_policy=req.quality_policy,
            )
            continue
        results[dataset] = reader_fn(
            dataset,
            req.lake_root,
            filters=filters,
            quality_policy=req.quality_policy,
            required=_research_dataset_required(req, dataset),
        )
    return results


def _coerce_research_input_reader_request(
    request: ResearchInputReaderRequest | Mapping[str, Any],
) -> ResearchInputReaderRequest:
    if isinstance(request, ResearchInputReaderRequest):
        return request
    values = dict(request)
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item).strip() for item in values["symbols"] if str(item).strip())
    if values.get("datasets") is not None and not isinstance(values["datasets"], tuple):
        values["datasets"] = tuple(str(item) for item in values["datasets"])
    return ResearchInputReaderRequest(**values)


def _research_dataset_required(req: ResearchInputReaderRequest, dataset: str) -> bool:
    if dataset == DATASET_PRICES:
        return req.require_prices
    if dataset == DATASET_TRADE_CALENDAR:
        return req.require_calendar
    if dataset == DATASET_INDEX_MEMBERS:
        return req.require_index_members
    if dataset == DATASET_STOCK_BASIC:
        return req.require_stock_lifecycle
    return False


def _research_reader_error(dataset: str, status: str, code: str) -> ReaderResult:
    return ReaderResult(
        status=status,
        issues=[{"code": code, "dataset": dataset}],
        remediation_spec={
            "action": "provide_explicit_research_lake_root",
            "dataset": dataset,
            "auto_execute": False,
            "dry_run_default": True,
        },
    )


def read_lightweight_input(request: LightweightInputRequest | Mapping[str, Any] | None = None) -> LightweightInputResult:
    """读取 canonical/gold，为轻量 engine 返回可运行输入。

    external legacy_flat 是可选兼容入口；默认禁用，且本函数不从旧 repo data
    复制或推断任何输入。
    """

    req = _coerce_lightweight_request(request)
    if req.input_mode not in {"canonical_gold", "legacy_flat"}:
        return _lightweight_error("invalid_request", "input_mode_invalid", req)
    if req.input_mode == "legacy_flat" and not req.legacy_flat_enabled:
        return _lightweight_error("invalid_request", "legacy_flat_disabled", req)
    if req.input_mode == "legacy_flat" and req.legacy_flat_dir is None:
        return _lightweight_error("invalid_request", "legacy_flat_dir_missing", req)
    if req.input_mode == "legacy_flat" and _is_repo_data_path(req.legacy_flat_dir):
        return _lightweight_error("invalid_request", "repo_data_reference_only", req)
    if req.dataset != DATASET_PRICES:
        return _lightweight_error("invalid_request", "unsupported_lightweight_dataset", req)

    reader = read_dataset(
        req.dataset,
        req.lake_root,
        filters={
            "start_date": req.start_date,
            "end_date": req.end_date,
            "symbols": req.symbols,
        },
        quality_policy=QualityPolicy(allow_warn=req.quality_policy in {"allow_warn", "pass_warn"}),
        required=True,
    )
    if reader.status != "available" or reader.frame is None:
        return _map_reader_failure(req, reader)
    if not _has_lineage(reader):
        return LightweightInputResult(
            status="lineage_missing",
            issues=[{"code": "lineage_missing", "dataset": req.dataset}],
            remediation_job_spec=_remediation(req),
        )
    frame = reader.frame.copy()
    if "adjustment_policy" in frame.columns:
        actual = sorted({str(value) for value in frame["adjustment_policy"].dropna().unique()})
        if actual and actual != [req.adjustment_policy]:
            return LightweightInputResult(
                status="quality_failed",
                issues=[
                    {
                        "code": "adjustment_policy_mismatch",
                        "expected": req.adjustment_policy,
                        "actual": actual,
                    }
                ],
                remediation_job_spec=_remediation(req),
            )
    required_columns = {"trade_date", "symbol", "close"}
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        return LightweightInputResult(
            status="required_missing",
            issues=[{"code": "required_columns_missing", "dataset": req.dataset, "columns": missing}],
            remediation_job_spec=_remediation(req),
        )
    close_column = "adjusted_close" if "adjusted_close" in frame.columns else "close"
    work = frame.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"], errors="coerce").dt.date
    work["symbol"] = work["symbol"].astype("string").str.strip()
    work[close_column] = pd.to_numeric(work[close_column], errors="coerce")
    close_df = work.pivot_table(index="trade_date", columns="symbol", values=close_column, aggfunc="last")
    close_df = close_df.sort_index()
    close_df = close_df.reindex(columns=sorted(close_df.columns))
    if close_df.empty:
        return LightweightInputResult(
            status="required_missing",
            issues=[{"code": "empty_lightweight_prices", "dataset": req.dataset}],
            remediation_job_spec=_remediation(req),
        )
    metadata = {
        "input_mode": req.input_mode,
        "dataset": req.dataset,
        "quality_status": reader.catalog_entry.quality_status if reader.catalog_entry else "",
        "dataset_status": reader.catalog_entry.dataset_status if reader.catalog_entry else "",
        "source": reader.catalog_entry.source if reader.catalog_entry else _first_non_empty(frame, "source"),
        "source_interface": reader.catalog_entry.source_interface if reader.catalog_entry else _first_non_empty(frame, "source_interface"),
        "source_run_id": _first_non_empty(frame, "source_run_id"),
        "manifest_run_id": reader.catalog_entry.latest_manifest_run_id if reader.catalog_entry else "",
        "schema_version": reader.catalog_entry.schema_version if reader.catalog_entry else _first_non_empty(frame, "schema_version"),
        "lineage_raw_checksum": reader.catalog_entry.lineage_raw_checksum if reader.catalog_entry else _first_non_empty(frame, "lineage_raw_checksum"),
        "adjustment_policy": req.adjustment_policy,
        "start_date": close_df.index.min().isoformat(),
        "end_date": close_df.index.max().isoformat(),
    }
    return LightweightInputResult(
        status="ok",
        close_df=close_df,
        universe=[str(symbol) for symbol in close_df.columns],
        calendar=list(close_df.index),
        metadata=metadata,
        issues=list(reader.issues),
    )


def read_backtrader_clean_feed(
    request: BacktraderCleanFeedRequest | Mapping[str, Any] | None = None,
) -> BacktraderCleanFeedBundle:
    """读取 Backtrader 可选后端所需的 clean feed。

    本入口只允许读 canonical/gold clean feed，并返回内存 bundle。它不会触发
    数据层任务、抓取、回补、原始层读取或 env/token
    读取；缺少显式 lake_root 时返回结构化缺失结果。
    """

    req = _coerce_backtrader_clean_feed_request(request)
    if req.dataset != DATASET_PRICES:
        return _backtrader_feed_error("invalid_request", "unsupported_backtrader_dataset", req)
    if req.lake_root is None:
        return _backtrader_feed_error("required_missing", "lake_root_required", req)
    if _is_repo_data_path(req.lake_root):
        return _backtrader_feed_error("invalid_request", "repo_data_reference_only", req)

    reader = read_dataset(
        req.dataset,
        req.lake_root,
        filters={
            "start_date": req.start_date,
            "end_date": req.end_date,
            "symbols": req.symbols,
        },
        quality_policy=QualityPolicy(allow_warn=req.quality_policy in {"allow_warn", "pass_warn"}),
        required=True,
    )
    if reader.status != "available" or reader.frame is None:
        return _map_backtrader_reader_failure(req, reader)
    if not _has_lineage(reader):
        return BacktraderCleanFeedBundle(
            status="lineage_missing",
            issues=[{"code": "lineage_missing", "dataset": req.dataset}],
            remediation_job_spec=_backtrader_remediation(req),
        )

    frame = reader.frame.copy()
    if "adjustment_policy" in frame.columns:
        actual = sorted({str(value) for value in frame["adjustment_policy"].dropna().unique()})
        if actual and actual != [req.adjustment_policy]:
            return BacktraderCleanFeedBundle(
                status="quality_failed",
                issues=[
                    {
                        "code": "adjustment_policy_mismatch",
                        "expected": req.adjustment_policy,
                        "actual": actual,
                    }
                ],
                remediation_job_spec=_backtrader_remediation(req),
            )

    required_base = {"trade_date", "symbol"}
    missing_base = sorted(required_base - set(frame.columns))
    if missing_base:
        return BacktraderCleanFeedBundle(
            status="required_missing",
            issues=[{"code": "required_columns_missing", "dataset": req.dataset, "columns": missing_base}],
            remediation_job_spec=_backtrader_remediation(req),
        )

    ohlc_map = {
        "open": "adjusted_open" if "adjusted_open" in frame.columns else "open",
        "high": "adjusted_high" if "adjusted_high" in frame.columns else "high",
        "low": "adjusted_low" if "adjusted_low" in frame.columns else "low",
        "close": "adjusted_close" if "adjusted_close" in frame.columns else "close",
    }
    missing_prices = sorted({source for source in ohlc_map.values() if source not in frame.columns})
    if missing_prices:
        return BacktraderCleanFeedBundle(
            status="required_missing",
            issues=[{"code": "required_price_columns_missing", "dataset": req.dataset, "columns": missing_prices}],
            remediation_job_spec=_backtrader_remediation(req),
        )

    pit_status = "pass"
    if {"available_at", "decision_time"}.issubset(frame.columns):
        pit = validate_pit_asof(frame, frame["trade_date"].dropna().unique(), dataset=req.dataset, keys=("symbol",))
        if not pit.passed:
            return BacktraderCleanFeedBundle(status="pit_failed", issues=pit.issues, remediation_job_spec=_backtrader_remediation(req))

    work = pd.DataFrame(
        {
            "trade_date": pd.to_datetime(frame["trade_date"], errors="coerce").dt.date,
            "symbol": frame["symbol"].astype("string").str.strip(),
            "open": pd.to_numeric(frame[ohlc_map["open"]], errors="coerce"),
            "high": pd.to_numeric(frame[ohlc_map["high"]], errors="coerce"),
            "low": pd.to_numeric(frame[ohlc_map["low"]], errors="coerce"),
            "close": pd.to_numeric(frame[ohlc_map["close"]], errors="coerce"),
            "adjustment_policy": req.adjustment_policy,
        }
    )
    for column in ("volume", "amount", "available_at", "decision_time"):
        if column in frame.columns:
            work[column] = frame[column]
    work = work.dropna(subset=["trade_date", "symbol", "open", "high", "low", "close"]).reset_index(drop=True)
    if work.empty:
        return BacktraderCleanFeedBundle(
            status="required_missing",
            issues=[{"code": "empty_backtrader_clean_feed", "dataset": req.dataset}],
            remediation_job_spec=_backtrader_remediation(req),
        )

    entry = reader.catalog_entry
    quality_status = entry.quality_status if entry else _first_non_empty(frame, "quality_status") or "pass"
    lineage = {
        "dataset": req.dataset,
        "source": entry.source if entry else _first_non_empty(frame, "source"),
        "source_interface": entry.source_interface if entry else _first_non_empty(frame, "source_interface"),
        "source_run_id": _first_non_empty(frame, "source_run_id"),
        "manifest_run_id": entry.latest_manifest_run_id if entry else _first_non_empty(frame, "manifest_run_id"),
        "schema_version": entry.schema_version if entry else _first_non_empty(frame, "schema_version"),
        "lineage_raw_checksum": entry.lineage_raw_checksum if entry else _first_non_empty(frame, "lineage_raw_checksum"),
    }
    contract = {
        "source_dataset": req.dataset,
        "quality_status": quality_status,
        "pit_checked": True,
        "pit_status": pit_status,
        "adjusted_price_ready": True,
        "adjustment_policy": req.adjustment_policy,
        "clean_feed_reader": "read_backtrader_clean_feed",
        "forbidden_data_layer_inputs": False,
    }
    return BacktraderCleanFeedBundle(
        status="available",
        ohlcv=work,
        calendar=sorted(work["trade_date"].dropna().unique()),
        benchmark_result=req.benchmark_result,
        input_contract=contract,
        issues=list(reader.issues),
        lineage={key: value for key, value in lineage.items() if value not in (None, "")},
    )


def _coerce_lightweight_request(request: LightweightInputRequest | Mapping[str, Any] | None) -> LightweightInputRequest:
    if request is None:
        return LightweightInputRequest()
    if isinstance(request, LightweightInputRequest):
        return request
    values = dict(request)
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item) for item in values["symbols"])
    if values.get("input_mode") == "canonical-gold":
        values["input_mode"] = "canonical_gold"
    if values.get("input_mode") == "legacy-flat":
        values["input_mode"] = "legacy_flat"
    return LightweightInputRequest(**values)


def _coerce_backtrader_clean_feed_request(
    request: BacktraderCleanFeedRequest | Mapping[str, Any] | None,
) -> BacktraderCleanFeedRequest:
    if request is None:
        return BacktraderCleanFeedRequest()
    if isinstance(request, BacktraderCleanFeedRequest):
        return request
    values = dict(request)
    if values.get("symbols") is not None and not isinstance(values["symbols"], tuple):
        values["symbols"] = tuple(str(item) for item in values["symbols"])
    return BacktraderCleanFeedRequest(**values)


def _map_reader_failure(req: LightweightInputRequest, result: ReaderResult) -> LightweightInputResult:
    status = result.status
    if status == "unavailable":
        codes = {str(issue.get("code")) for issue in result.issues}
        status = "quality_failed" if "quality_warn_blocked" in codes else "required_missing"
    if status not in {"required_missing", "quality_failed", "lineage_missing", "invalid_request"}:
        status = "required_missing"
    return LightweightInputResult(
        status=status,
        issues=list(result.issues),
        remediation_job_spec={**_remediation(req), **(result.remediation_spec or {})},
    )


def _map_backtrader_reader_failure(req: BacktraderCleanFeedRequest, result: ReaderResult) -> BacktraderCleanFeedBundle:
    status = result.status
    if status == "unavailable":
        codes = {str(issue.get("code")) for issue in result.issues}
        status = "quality_failed" if "quality_warn_blocked" in codes else "required_missing"
    if status not in {"required_missing", "quality_failed", "lineage_missing", "pit_failed", "invalid_request"}:
        status = "required_missing"
    return BacktraderCleanFeedBundle(
        status=status,
        issues=list(result.issues),
        remediation_job_spec={**_backtrader_remediation(req), **(result.remediation_spec or {})},
    )


def _has_lineage(result: ReaderResult) -> bool:
    entry = result.catalog_entry
    if entry is not None and (entry.latest_manifest_run_id or entry.lineage_raw_checksum):
        return True
    frame = result.frame
    if frame is None or frame.empty:
        return False
    return any(
        column in frame.columns and frame[column].notna().any()
        for column in ("source_run_id", "lineage_raw_checksum")
    )


def _first_non_empty(frame: pd.DataFrame, column: str) -> str:
    if column not in frame.columns:
        return ""
    values = [str(value) for value in frame[column].dropna().unique() if str(value)]
    return values[0] if values else ""


def _remediation(req: LightweightInputRequest) -> dict[str, Any]:
    return {
        "action": "run_explicit_market_data_job",
        "dataset": req.dataset,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "dry_run_default": True,
        "auto_execute": False,
    }


def _backtrader_remediation(req: BacktraderCleanFeedRequest) -> dict[str, Any]:
    return {
        "action": "run_explicit_market_data_job",
        "dataset": req.dataset,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "dry_run_default": True,
        "auto_execute": False,
    }


def _lightweight_error(status: str, code: str, req: LightweightInputRequest) -> LightweightInputResult:
    return LightweightInputResult(
        status=status,
        issues=[{"code": code, "dataset": req.dataset}],
        remediation_job_spec=_remediation(req),
    )


def _backtrader_feed_error(status: str, code: str, req: BacktraderCleanFeedRequest) -> BacktraderCleanFeedBundle:
    return BacktraderCleanFeedBundle(
        status=status,
        issues=[{"code": code, "dataset": req.dataset}],
        remediation_job_spec=_backtrader_remediation(req),
    )


def _is_repo_data_path(value: str | Path | None) -> bool:
    if value is None:
        return False
    path = Path(value)
    return not path.is_absolute() and (path.parts == ("data",) or path.parts[:1] == ("data",))


def read_canonical(
    dataset: str,
    lake_root: str | Path,
    start: str | None = None,
    end: str | None = None,
    symbols: Sequence[str] | None = None,
    columns: Sequence[str] | None = None,
    quality_policy: object = None,
) -> pd.DataFrame:
    del quality_policy
    if dataset not in DATASETS or dataset != DATASET_PRICES:
        raise ReaderBoundaryError(f"本批次 reader 仅支持 exact dataset={DATASET_PRICES}: {dataset}")
    layout = LakeLayout(lake_root)
    # catalog 只用于确认 dataset 已登记；缺失时仍允许读取已存在 canonical，便于测试和后续恢复。
    try:
        CatalogStore(layout).get(dataset)
    except Exception:
        pass
    paths = _canonical_paths(layout, dataset)
    if not paths:
        raise ReaderBoundaryError(f"canonical parquet 不存在: {dataset}")
    frame = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
    if start is not None:
        frame = frame[frame["trade_date"].astype(str) >= str(start)]
    if end is not None:
        frame = frame[frame["trade_date"].astype(str) <= str(end)]
    if symbols is not None:
        symbol_set = {str(item) for item in symbols}
        frame = frame[frame["symbol"].astype(str).isin(symbol_set)]
    if columns is not None:
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ReaderBoundaryError(f"请求列不存在: {','.join(missing)}")
        frame = frame[list(columns)]
    return frame.reset_index(drop=True)


def read_dataset(
    dataset: str,
    lake_root: str | Path | None = None,
    filters: Mapping[str, Any] | None = None,
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None,
    *,
    required: bool = False,
) -> ReaderResult:
    policy = _policy(quality_policy, required)
    root = _lake_root(lake_root)
    if root is None:
        status = "required_missing" if policy.required else "unavailable"
        return ReaderResult(
            status=status,
            issues=[{"code": "lake_root_missing", "dataset": dataset}],
            remediation_spec={
                "action": "set_lake_root",
                "env": "MARKET_DATA_LAKE_ROOT",
                "dataset": dataset,
                "dry_run_default": True,
                "auto_execute": False,
            },
        )
    if dataset not in DATASETS:
        return ReaderResult(
            status="unavailable",
            issues=[{"code": "unknown_dataset", "dataset": dataset}],
        )
    layout = LakeLayout(root)
    try:
        entry = CatalogStore(layout).get(dataset)
    except CatalogError as exc:
        text = str(exc)
        if "quality fail" in text:
            return ReaderResult(
                status="quality_failed",
                issues=[{"code": "quality_failed", "dataset": dataset}],
            )
        if "quality warn blocked" in text:
            return ReaderResult(
                status="unavailable",
                issues=[{"code": "quality_warn_blocked", "dataset": dataset}],
            )
        status = "required_missing" if policy.required else "unavailable"
        return ReaderResult(
            status=status,
            issues=[{"code": "catalog_missing", "dataset": dataset}],
            remediation_spec=_readiness_remediation(dataset),
        )

    if not entry.published:
        status = "required_missing" if policy.required else "unavailable"
        return ReaderResult(
            status=status,
            issues=[
                {
                    "code": "catalog_not_published",
                    "dataset": dataset,
                    "quality_status": entry.quality_status,
                }
            ],
            catalog_entry=entry,
            remediation_spec={
                "action": "publish_dataset",
                "dataset": dataset,
                "dry_run_default": False,
                "auto_execute": False,
            },
        )
    if dataset in _W3_UNRESOLVED_DATASETS and str(entry.source_interface or "").upper() in {
        "",
        "UNKNOWN",
        "UNRESOLVED",
    }:
        return _w3_unresolved_result(dataset, policy)
    if entry.quality_status == "fail":
        return ReaderResult(
            status="quality_failed",
            issues=[{"code": "quality_failed", "dataset": dataset}],
            catalog_entry=entry,
        )
    if entry.quality_status == "warn" and not policy.allow_warn:
        return ReaderResult(
            status="unavailable",
            issues=[{"code": "quality_warn_blocked", "dataset": dataset}],
            catalog_entry=entry,
        )
    paths = [path for path in _entry_paths(layout, dataset, entry) if path.exists()]
    if not paths:
        status = "required_missing" if policy.required else "unavailable"
        return ReaderResult(
            status=status,
            issues=[{"code": "canonical_missing", "dataset": dataset}],
            catalog_entry=entry,
            remediation_spec={
                **_readiness_remediation(dataset),
                "start_date": entry.start_date,
                "end_date": entry.end_date,
            },
        )
    frame = _read_paths(paths)
    filters = dict(filters or {})
    frame = _filter_frame(
        frame,
        start=filters.get("start") or filters.get("start_date"),
        end=filters.get("end") or filters.get("end_date"),
        symbols=filters.get("symbols"),
        index_code=filters.get("index_code"),
        exchange=filters.get("exchange"),
        columns=filters.get("columns"),
    )
    issues = [{"code": "quality_warn", "dataset": dataset}] if entry.quality_status == "warn" else []
    w3_issues = _w3_contract_issues(dataset, frame, entry)
    if w3_issues:
        status = "required_missing" if policy.required else "unavailable"
        return ReaderResult(
            status=status,
            issues=[*issues, *w3_issues],
            catalog_entry=entry,
            remediation_spec=_readiness_remediation(dataset),
        )
    readiness_issues = _readiness_issues(dataset, frame)
    issues.extend(readiness_issues)
    blocking_codes = {str(issue.get("code")) for issue in readiness_issues}
    if PIT_STATUS_FAILED in _column_values(frame, "pit_status"):
        return ReaderResult(
            status="pit_failed",
            issues=issues,
            catalog_entry=entry,
            remediation_spec=_readiness_remediation(dataset),
        )
    if blocking_codes & {
        "pit_incomplete",
        "non_pit_snapshot",
        "non_pit_universe",
        "readiness_not_available",
    } and not policy.allow_warn:
        return ReaderResult(
            status="unavailable",
            issues=issues,
            catalog_entry=entry,
            remediation_spec=_readiness_remediation(dataset),
        )
    return ReaderResult(status="available", frame=frame, issues=issues, catalog_entry=entry)


def read_index_universe(
    lake_root: str | Path | None = None,
    *,
    index_code: str = "399300.SZ",
    start_date: str | None = None,
    end_date: str | None = None,
    symbols: Sequence[str] | None = None,
    pit_required: bool = True,
    required: bool = True,
) -> ReaderResult:
    """只读沪深 300 成分集 readiness，不从 index_weights 推导成分。

    该 helper 是 S03 的消费侧防线：完整成分集只能来自
    DATASET_INDEX_MEMBERS；当 PIT 不完整或 catalog 缺失时返回 structured
    unavailable / required_missing，不读取抓取层、运行层或写湖层。
    """

    result = read_dataset(
        DATASET_INDEX_MEMBERS,
        lake_root,
        filters={
            "index_code": index_code,
            "start_date": start_date,
            "end_date": end_date,
            "symbols": symbols,
        },
        quality_policy=QualityPolicy(allow_warn=not pit_required, required=required),
        required=required,
    )
    if result.status != "available" or result.frame is None:
        remediation = {
            **(result.remediation_spec or {}),
            "dataset": DATASET_INDEX_MEMBERS,
            "not_substituted_by": DATASET_INDEX_WEIGHTS,
            "auto_execute": False,
        }
        return ReaderResult(
            status=result.status,
            frame=None,
            issues=[
                *list(result.issues),
                {
                    "code": "index_members_not_available",
                    "dataset": DATASET_INDEX_MEMBERS,
                    "not_substituted_by": DATASET_INDEX_WEIGHTS,
                },
            ],
            catalog_entry=result.catalog_entry,
            remediation_spec=remediation,
        )
    unresolved_issues = _pit_source_unresolved_issues(DATASET_INDEX_MEMBERS, result)
    if unresolved_issues:
        return ReaderResult(
            status="required_missing" if required else "unavailable",
            issues=[*list(result.issues), *unresolved_issues],
            catalog_entry=result.catalog_entry,
            remediation_spec={
                **_readiness_remediation(DATASET_INDEX_MEMBERS),
                "reason": "source_unresolved",
                "not_substituted_by": DATASET_INDEX_WEIGHTS,
                "auto_execute": False,
            },
        )
    frame = result.frame
    if pit_required:
        pit_values = _column_values(frame, "pit_status")
        pit_pass_values = {PIT_STATUS_AVAILABLE, "pass"}
        is_pit = (
            "is_pit_universe" in frame.columns
            and not frame.empty
            and bool(frame["is_pit_universe"].astype(bool).all())
        )
        if not pit_values or not pit_values <= pit_pass_values or not is_pit:
            quality_status = str(getattr(result.catalog_entry, "quality_status", "") or "")
            extra_issues = []
            if quality_status == "pass":
                extra_issues.append(
                    {
                        "code": "quality_pass_not_pit_available",
                        "dataset": DATASET_INDEX_MEMBERS,
                        "quality_status": quality_status,
                        "pit_status": sorted(pit_values),
                        "is_pit_universe": bool(is_pit),
                    }
                )
            return ReaderResult(
                status="unavailable",
                issues=[
                    *list(result.issues),
                    *extra_issues,
                    {
                        "code": "pit_universe_not_available",
                        "dataset": DATASET_INDEX_MEMBERS,
                        "pit_status": sorted(pit_values),
                        "not_substituted_by": DATASET_INDEX_WEIGHTS,
                    },
                ],
                catalog_entry=result.catalog_entry,
                remediation_spec={
                    **_readiness_remediation(DATASET_INDEX_MEMBERS),
                    "not_substituted_by": DATASET_INDEX_WEIGHTS,
                },
            )
    return result


def read_stock_lifecycle(
    lake_root: str | Path | None = None,
    *,
    symbols: Sequence[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    required: bool = True,
    reader: Any = None,
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None,
) -> ReaderResult:
    """只读 stock_basic lifecycle 字段，不把当前快照声明为 PIT universe。

    该入口只返回 lifecycle gate 所需字段与结构化 issue；发现缺失或
    source/interface 未冻结时 fail-fast，remediation 始终不可自动执行。
    """

    reader_fn = reader or read_dataset
    result = reader_fn(
        DATASET_STOCK_BASIC,
        lake_root,
        filters={"start_date": start_date, "end_date": end_date, "symbols": symbols},
        quality_policy=quality_policy,
        required=required,
    )
    status = "required_missing" if required else "unavailable"
    if result.status != "available" or result.frame is None:
        return ReaderResult(
            status=result.status,
            frame=None,
            issues=[
                *list(result.issues),
                {
                    "code": "lifecycle_missing",
                    "dataset": DATASET_STOCK_BASIC,
                    "reader_status": result.status,
                },
            ],
            catalog_entry=result.catalog_entry,
            remediation_spec={
                **(result.remediation_spec or {}),
                **_stock_lifecycle_remediation("lifecycle_missing"),
            },
        )
    unresolved_issues = _pit_source_unresolved_issues(DATASET_STOCK_BASIC, result)
    if unresolved_issues:
        return ReaderResult(
            status=status,
            frame=None,
            issues=[*list(result.issues), *unresolved_issues],
            catalog_entry=result.catalog_entry,
            remediation_spec=_stock_lifecycle_remediation("source_unresolved"),
        )

    frame = result.frame.copy()
    if "ts_code" in frame.columns and "symbol" not in frame.columns:
        frame["symbol"] = frame["ts_code"]
    required_columns = ("symbol", "list_date", "list_status", "available_at")
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if frame.empty or missing_columns:
        return ReaderResult(
            status=status,
            frame=None,
            issues=[
                *list(result.issues),
                {
                    "code": "lifecycle_missing",
                    "dataset": DATASET_STOCK_BASIC,
                    "missing_columns": missing_columns,
                    "empty": bool(frame.empty),
                },
            ],
            catalog_entry=result.catalog_entry,
            remediation_spec=_stock_lifecycle_remediation("lifecycle_missing"),
        )
    issues = [
        *list(result.issues),
        {
            "code": "stock_basic_not_pit_universe",
            "dataset": DATASET_STOCK_BASIC,
            "severity": "INFO",
            "reason": "stock_basic 仅用于 lifecycle gate，不证明 PIT membership",
        },
    ]
    return ReaderResult(
        status="available",
        frame=frame.reset_index(drop=True),
        issues=issues,
        catalog_entry=result.catalog_entry,
        remediation_spec=result.remediation_spec,
    )


def _pit_source_unresolved_issues(dataset: str, result: ReaderResult) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    entry_interface = str(getattr(result.catalog_entry, "source_interface", "") or "").strip().upper()
    if entry_interface in {"", "UNKNOWN", "UNRESOLVED"}:
        issues.append(
            {
                "code": "source_unresolved",
                "dataset": dataset,
                "reason": "catalog source_interface 未冻结，禁止伪造 available",
            }
        )
    frame = result.frame
    if frame is not None and "source_interface" in frame.columns and not frame.empty:
        interfaces = {
            str(value).strip().upper()
            for value in frame["source_interface"].dropna().unique()
            if str(value).strip()
        }
        if not interfaces or interfaces & {"UNKNOWN", "UNRESOLVED"}:
            issues.append(
                {
                    "code": "source_unresolved",
                    "dataset": dataset,
                    "reason": "canonical source_interface 未冻结",
                    "source_interface": sorted(interfaces),
                }
            )
    return issues


def _stock_lifecycle_remediation(reason: str) -> dict[str, Any]:
    return {
        "action": "confirm_stock_lifecycle_source_interface_or_declare_missing",
        "dataset": DATASET_STOCK_BASIC,
        "reason": reason,
        "dry_run_default": True,
        "auto_execute": False,
    }


def read_factor_panel(
    datasets: Mapping[str, pd.DataFrame] | None = None,
    decision_calendar: pd.DataFrame | Sequence[str] | None = None,
    pit_policy: Mapping[str, Any] | None = None,
    adjustment_policy: str = "qfq",
    quality_policy: QualityPolicy | Mapping[str, Any] | str | None = None,
    lake_root: str | Path | None = None,
) -> ReaderResult:
    del pit_policy
    frames: dict[str, pd.DataFrame] = dict(datasets or {})
    issues: list[dict[str, Any]] = []
    if not frames and lake_root is not None:
        prices = read_dataset(DATASET_PRICES, lake_root, quality_policy=quality_policy, required=True)
        if not prices.available or prices.frame is None:
            return prices
        frames[DATASET_PRICES] = prices.frame
    prices_frame = frames.get(DATASET_PRICES)
    if prices_frame is None:
        return ReaderResult(status="required_missing", issues=[{"code": "prices_missing"}])
    adjustment = validate_adjustment_consistency(prices_frame, adjustment_policy)
    if not adjustment.passed:
        return ReaderResult(status="adjustment_failed", issues=adjustment.issues)

    for dataset, frame in frames.items():
        if dataset == DATASET_PRICES:
            continue
        if "decision_time" in frame.columns or "available_at" in frame.columns:
            keys = ("index_code", "con_code") if dataset == DATASET_INDEX_WEIGHTS else ()
            pit = validate_pit_asof(frame, decision_calendar, dataset=dataset, keys=keys)
            if not pit.passed:
                return ReaderResult(status="pit_failed", issues=pit.issues)
    output = prices_frame.copy()
    rename_map = {
        "adjusted_open": "open",
        "adjusted_high": "high",
        "adjusted_low": "low",
        "adjusted_close": "close",
    }
    for source, target in rename_map.items():
        output[target] = output[source]
    output["adjustment_policy"] = adjustment_policy
    issues.extend({"code": "input_quality_warn", "dataset": key} for key in frames if key != DATASET_PRICES)
    return ReaderResult(status="available", frame=output.reset_index(drop=True), issues=issues)


__all__ = [
    "AdjustmentAuditReaderResult",
    "AdjustmentAuditRequest",
    "AuxiliaryInputRequest",
    "BacktraderCleanFeedBundle",
    "BacktraderCleanFeedRequest",
    "DATASET_CORPORATE_ACTIONS",
    "ExecutionFeedRequest",
    "ExposureInputRequest",
    "LightweightInputRequest",
    "LightweightInputResult",
    "QualityPolicy",
    "ReaderBoundaryError",
    "ReaderResult",
    "ResearchInputReaderRequest",
    "TradabilityInputRequest",
    "read_canonical",
    "read_backtrader_clean_feed",
    "read_auxiliary_inputs",
    "read_dataset",
    "read_execution_feed",
    "read_exposure_inputs",
    "read_adjustment_audit_inputs",
    "read_factor_panel",
    "read_index_universe",
    "read_lightweight_input",
    "read_research_inputs",
    "read_stock_lifecycle",
    "read_tradability_inputs",
    "evaluate_corporate_action_availability",
    "extract_adj_factor_lineage",
]
