"""canonical 数据质量校验与报告输出。"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import pandas as pd

from .contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_RAW,
    ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
    CANONICAL_PRICES_COLUMNS,
    CR017_REQUIRED_FIELD_SETS,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_IDS,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_RETURNS_ADJUSTED,
    CR018_BENCHMARK_BLOCKED_CLAIMS,
    CR018_BENCHMARK_DATASET_COMPONENTS,
    CR018_BENCHMARK_DATASET_PRICES,
    CR018_BENCHMARK_DATASET_TYPES,
    CR018_BENCHMARK_DATASET_WEIGHTS,
    CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS,
    CR018_BENCHMARK_IDS,
    CR018_BENCHMARK_INDEX_CODES,
    CR018_BENCHMARK_REASON_BY_DATASET_TYPE,
    CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT,
    CR018_BENCHMARK_REASON_COMPONENTS_MISSING,
    CR018_BENCHMARK_REASON_PERMISSION_COUNTER_VIOLATION,
    CR018_BENCHMARK_REASON_TRADE_CALENDAR_DENOMINATOR_MISSING,
    CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH,
    CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
    CR018_BENCHMARK_REQUIRED_FOR_PUBLISH,
    CR018_CODE_CHANGE_EVIDENCE_FIELDS,
    CR018_FORBIDDEN_OPERATION_COUNTERS,
    CR018_LIFECYCLE_READINESS_DATASET_ID,
    CR018_LIFECYCLE_REQUIRED_FIELDS,
    CR018_P0_READINESS_BLOCKED_CLAIMS,
    CR018_PIT_READINESS_DATASET_ID,
    CR018_PIT_REQUIRED_FIELDS,
    CR018_PRICES_LIMIT_REQUIRED_FIELDS,
    CR018_REASON_ACTIVE_DENOMINATOR_MISSING,
    CR018_REASON_AS_OF_JOIN_VIOLATION,
    CR018_REASON_CODE_CHANGE_REQUIRED_MISSING,
    CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT,
    CR018_REASON_LIFECYCLE_FIELD_MISSING,
    CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED,
    CR018_REASON_PERMISSION_COUNTER_VIOLATION,
    CR018_REASON_PIT_AVAILABLE_FIELD_MISSING,
    CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING,
    CR018_REASON_ST_SUSPEND_REQUIRED_MISSING,
    CR018_REASON_TRADE_STATUS_REQUIRED_MISSING,
    CR018_ST_SUSPEND_REQUIRED_FIELDS,
    CR018_TRADABILITY_READINESS_DATASET_ID,
    CR018_TRADE_STATUS_REQUIRED_FIELDS,
    DATASET_HS300_INDEX,
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES_LIMIT,
    DATASET_KEY_COLUMNS,
    DATASET_PIT_FIELDS,
    DATASET_PRICES,
    DATASET_SCHEMA_REGISTRY,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_FAILED,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    PIT_STATUS_NOT_APPLICABLE,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_MISSING,
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARN,
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_NON_PIT_SNAPSHOT,
    READINESS_STATUS_PIT_INCOMPLETE,
    READINESS_STATUS_QUALITY_FAILED,
    READINESS_STATUS_REQUIRED_MISSING,
    READINESS_STATUS_SCHEMA_MISMATCH,
    SCHEMA_VERSION,
)
from .lake_layout import LakeLayout, ensure_parent_dirs_for_write
from .quality import UNEXPLAINED_ADJUSTMENT_JUMP, check_unexplained_adjustment_jump

DENOMINATOR_MODE_PRICES = "open_trade_dates_in_requested_range_x_target_symbols"
DENOMINATOR_MODE_TRADE_CALENDAR_REQUIRED = "trade_calendar_required"
DENOMINATOR_MODE_TRADE_CALENDAR = "calendar_days_in_requested_range_x_exchange"
DENOMINATOR_MODE_BENCHMARK = "trade_calendar_open_dates"


class QualityValidationError(ValueError):
    """质量校验失败。"""


class QualityReportError(RuntimeError):
    """质量报告写入失败。"""


@dataclass(frozen=True, slots=True)
class QualityThresholds:
    prices_missing_rate_pass: float = 0.0
    prices_missing_rate_warn: float = 0.02
    prices_missing_rate_fail: float = 0.05
    allow_negative_price: bool = False
    max_duplicate_keys: int = 0
    coverage_threshold: float = 1.0


@dataclass(frozen=True, slots=True)
class CoverageSummary:
    requested_start: str
    requested_end: str
    actual_start: str | None
    actual_end: str | None
    requested_symbols_count: int
    actual_symbols_count: int
    open_trade_dates_count: int
    expected_rows: int
    actual_rows: int
    missing_rows: int
    missing_rate: float


@dataclass(frozen=True, slots=True)
class QualityResult:
    run_id: str
    generated_at: str
    dataset: str
    source_name: str
    source_interface: str
    target_dataset: str
    input_config_hash: str
    quality_status: str
    fetch_status: str
    dataset_status: str
    coverage: CoverageSummary
    denominator_mode: str = DENOMINATOR_MODE_PRICES
    thresholds: QualityThresholds = field(default_factory=QualityThresholds)
    issue_count: int = 0
    missing_required_fields: list[str] = field(default_factory=list)
    duplicate_keys: list[dict[str, Any]] = field(default_factory=list)
    negative_price_rows: list[dict[str, Any]] = field(default_factory=list)
    coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    manifest_inconsistencies: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_pit_universe: bool = False
    universe_mode: str = "non_pit_static"
    pit_status: str = "non_pit_disclosed"
    survivorship_bias_note: str = (
        "non-PIT 股票池可能把未上市、退市、停牌或非有效股票计入缺失分母。"
    )
    schema_version: str = SCHEMA_VERSION
    coverage_threshold: float = 1.0
    missing_dates: list[str] = field(default_factory=list)
    gap_reason: str = ""
    issue_codes: list[str] = field(default_factory=list)
    duplicate_key_count: int = 0
    source_run_id: str = ""
    manifest_run_id: str = ""
    lineage_raw_checksum: str = ""
    benchmark_kind: str = ""
    index_code: str = ""
    calendar_source: str = ""
    missing_trade_dates: list[str] = field(default_factory=list)
    unavailable_mapping: str = "unavailable"
    readiness_status: str = READINESS_STATUS_AVAILABLE

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "dataset": self.dataset,
            "schema_version": self.schema_version,
            "start_date": self.coverage.requested_start,
            "end_date": self.coverage.requested_end,
            "source_name": self.source_name,
            "source": self.source_name,
            "source_interface": self.source_interface,
            "source_run_id": self.source_run_id or self.run_id,
            "manifest_run_id": self.manifest_run_id or self.run_id,
            "lineage_raw_checksum": self.lineage_raw_checksum,
            "target_dataset": self.target_dataset,
            "input_config_hash": self.input_config_hash,
            "quality_status": self.quality_status,
            "fetch_status": self.fetch_status,
            "dataset_status": self.dataset_status,
            "issue_count": self.issue_count,
            **asdict(self.coverage),
            "coverage_numerator": self.coverage.actual_rows,
            "coverage_denominator": self.coverage.expected_rows,
            "coverage_ratio": (
                self.coverage.actual_rows / self.coverage.expected_rows
                if self.coverage.expected_rows
                else 0.0
            ),
            "coverage_threshold": self.coverage_threshold,
            "missing_dates_json": _json_text(self.missing_dates),
            "gap_reason": self.gap_reason,
            "duplicate_key_count": self.duplicate_key_count or len(self.duplicate_keys),
            "denominator_mode": self.denominator_mode,
            "thresholds_json": _json_text(asdict(self.thresholds)),
            "quality_thresholds_json": _json_text(asdict(self.thresholds)),
            "issue_codes_json": _json_text(self.issue_codes),
            "missing_required_fields_json": _json_text(self.missing_required_fields),
            "duplicate_keys_json": _json_text(self.duplicate_keys),
            "negative_price_rows_json": _json_text(self.negative_price_rows),
            "coverage_gaps_json": _json_text(self.coverage_gaps),
            "manifest_inconsistencies_json": _json_text(self.manifest_inconsistencies),
            "warnings_json": _json_text(self.warnings),
            "is_pit_universe": self.is_pit_universe,
            "universe_mode": self.universe_mode,
            "pit_status": self.pit_status,
            "survivorship_bias_note": self.survivorship_bias_note,
            "benchmark_kind": self.benchmark_kind,
            "index_code": self.index_code,
            "calendar_source": self.calendar_source,
            "missing_trade_dates_json": _json_text(self.missing_trade_dates),
            "unavailable_mapping": self.unavailable_mapping,
            "readiness_status": self.readiness_status,
        }


@dataclass(frozen=True, slots=True)
class GateValidationResult:
    status: str
    passed: bool
    issues: list[dict[str, Any]] = field(default_factory=list)


VALIDATE_DOES_NOT_PUBLISH = "validate_does_not_publish"
P0_CANDIDATE_REQUIRED = "p0_candidate_required"
P0_CANDIDATE_UNPUBLISHED = "candidate_unpublished"
P0_CURRENT_POINTER_REQUIRED = "current_pointer_required"
P0_CANDIDATE_AUDIT_REQUIRED = "candidate_audit_evidence_required"
P0_READ_SCOPE_INVALID = "read_scope_invalid"
CR017_MISSING_FACTOR_DIRECTION = "missing_factor_direction"
CR017_INVALID_FACTOR_DIRECTION = "invalid_factor_direction"
CR017_MISSING_LINEAGE = "missing_lineage"
CR017_INVALID_RAW_OHLC = "invalid_raw_ohlc"
CR017_INVALID_ADJ_FACTOR = "invalid_adj_factor"
CR017_DERIVED_OVERWRITES_RAW = "derived_overwrites_raw"
CR017_REASON_REQUIRED_MISSING = "required_missing"
CR017_MIXED_ADJUSTMENT_POLICY = "mixed_adjustment_policy"
CR017_EXECUTION_REQUIRES_RAW = "execution_requires_raw"
CR017_UNEXPLAINED_ADJUSTMENT_JUMP = UNEXPLAINED_ADJUSTMENT_JUMP
CR017_MISSING_AS_OF_TRADE_DATE = "missing_as_of_trade_date"
CR017_WARNING_NOT_PRODUCTION_PASS = "warning_not_production_pass"
CR017_PARITY_MISMATCH = "parity_mismatch"
CR017_QUALITY_FAILED = "quality_failed"
CR017_REQUIRED_MISSING_REASON_CODES: tuple[str, ...] = (
    CR017_REASON_REQUIRED_MISSING,
    CR017_MISSING_FACTOR_DIRECTION,
    CR017_MISSING_LINEAGE,
    CR017_MISSING_AS_OF_TRADE_DATE,
)
CR017_QUALITY_FAIL_REASON_CODES: tuple[str, ...] = (
    CR017_INVALID_FACTOR_DIRECTION,
    CR017_INVALID_RAW_OHLC,
    CR017_INVALID_ADJ_FACTOR,
    CR017_DERIVED_OVERWRITES_RAW,
    CR017_MIXED_ADJUSTMENT_POLICY,
    CR017_EXECUTION_REQUIRES_RAW,
    CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
    CR017_PARITY_MISMATCH,
    CR017_QUALITY_FAILED,
)
CR017_S05_REASON_CODES: tuple[str, ...] = (
    CR017_REASON_REQUIRED_MISSING,
    CR017_MIXED_ADJUSTMENT_POLICY,
    CR017_EXECUTION_REQUIRES_RAW,
    CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
    CR017_MISSING_AS_OF_TRADE_DATE,
)
CR017_S05_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "dependency_change": 0,
    "legacy_qfq_overwrite": 0,
    "qmt_api_call": 0,
    "real_order": 0,
    "old_report_read": 0,
    "real_lake_read": 0,
}
CR018_ADJUSTMENT_REASON_VIEW_REQUIRED_MISSING = "adjustment_view_required_missing"
CR018_ADJUSTMENT_REASON_FIELD_COVERAGE_INCOMPLETE = "adjustment_field_coverage_incomplete"
CR018_ADJUSTMENT_REASON_FACTOR_COVERAGE_INCOMPLETE = "adjustment_factor_coverage_incomplete"
CR018_ADJUSTMENT_REASON_POLICY_MISMATCH = "adjustment_policy_mismatch"
CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_REQUIRED = "legacy_qfq_baseline_required"
CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_OVERWRITE = "legacy_qfq_baseline_overwrite"
CR018_ADJUSTMENT_REASON_QMT_REQUIRES_RAW = CR017_EXECUTION_REQUIRES_RAW
CR018_ADJUSTMENT_REQUIRED_VIEW_IDS: tuple[str, ...] = (
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)
CR018_ADJUSTMENT_EXPECTED_POLICIES: dict[str, str] = {
    CR017_VIEW_PRICES_RAW: ADJUSTMENT_POLICY_RAW,
    CR017_VIEW_ADJ_FACTOR: ADJUSTMENT_POLICY_RAW,
    CR017_VIEW_PRICES_QFQ: ADJUSTMENT_POLICY_QFQ,
    CR017_VIEW_PRICES_HFQ: ADJUSTMENT_POLICY_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED: ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
}
CR018_ADJUSTMENT_OPERATION_COUNTERS: dict[str, int] = {
    **CR018_FORBIDDEN_OPERATION_COUNTERS,
    "legacy_qfq_overwrite": 0,
    "qmt_adjusted_execution_allowed": 0,
}
CR018_RELEASE_READINESS_AUDIT_SCHEMA = "cr018.release_readiness_audit.v1"
CR018_RELEASE_AUDIT_REQUIRED_FIELDS: tuple[str, ...] = (
    "release",
    "dataset",
    "quality",
    "blocked_claims",
    "rollback_target",
    "evidence_refs",
)
CR018_RELEASE_AUDIT_REQUIRED_EVIDENCE_REFS: tuple[str, ...] = (
    "raw",
    "manifest",
    "candidate",
    "quality",
    "release_history",
)
CR018_RELEASE_AUDIT_HISTORICAL_EVIDENCE_KEYS: tuple[str, ...] = (
    "raw",
    "manifest",
    "candidate",
    "quality",
    "release_history",
)
CR018_RELEASE_AUDIT_OPERATION_COUNTERS: dict[str, int] = {
    **CR018_FORBIDDEN_OPERATION_COUNTERS,
    "real_lake_write": 0,
    "catalog_current_pointer_publish": 0,
}
CR018_RELEASE_REASON_P0_READINESS_FAILED = "p0_readiness_failed"
CR018_RELEASE_REASON_REQUIRED_MISSING = "required_missing"
CR018_RELEASE_REASON_QUALITY_FAILED = "quality_failed"
CR018_RELEASE_REASON_ROLLBACK_TARGET_REQUIRED = "rollback_target_required"
CR018_RELEASE_REASON_ROLLBACK_SCOPE_NOT_RELEASE = "rollback_scope_not_release"
CR018_RELEASE_REASON_AUDIT_EVIDENCE_INCOMPLETE = "audit_evidence_incomplete"
CR018_RELEASE_REASON_PERMISSION_COUNTER_VIOLATION = "permission_counter_violation"

ADJUSTMENT_GATE_STATUS_PASS = QUALITY_STATUS_PASS
ADJUSTMENT_GATE_STATUS_WARN = QUALITY_STATUS_WARN
ADJUSTMENT_GATE_STATUS_FAIL = QUALITY_STATUS_FAIL
ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING = CR017_REASON_REQUIRED_MISSING
ADJUSTMENT_LEAKAGE_STATUS_BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AdjustmentQualityResult:
    status: str
    passed: bool
    production_pass: bool
    reason_code: str = ""
    reason_detail: str = ""
    view_id: str = ""
    source_run_id: str = ""
    lineage_checksum: str = ""
    missing_fields: tuple[str, ...] = ()
    issues: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR017_S05_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "production_pass": self.production_pass,
            "reason_code": self.reason_code,
            "reason_detail": self.reason_detail,
            "view_id": self.view_id,
            "source_run_id": self.source_run_id,
            "lineage_checksum": self.lineage_checksum,
            "missing_fields": list(self.missing_fields),
            "issues": [dict(item) for item in self.issues],
            "warnings": list(self.warnings),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class ParityCheckResult:
    status: str
    passed: bool
    reason_code: str = ""
    mismatch_reason: dict[str, Any] = field(default_factory=dict)
    view_id: str = ""
    expected_count: int = 0
    actual_count: int = 0
    mismatches: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR017_S05_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "reason_code": self.reason_code,
            "mismatch_reason": dict(self.mismatch_reason),
            "view_id": self.view_id,
            "expected_count": self.expected_count,
            "actual_count": self.actual_count,
            "mismatches": [dict(item) for item in self.mismatches],
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class LeakageGuardResult:
    status: str
    passed: bool
    reason_code: str = ""
    blocked_reason: str = ""
    field_name: str = ""
    policy: str = ""
    view_id: str = ""
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR017_S05_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "reason_code": self.reason_code,
            "blocked_reason": self.blocked_reason,
            "field_name": self.field_name,
            "policy": self.policy,
            "view_id": self.view_id,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class P0ValidationResult:
    dataset: str
    quality_status: str
    readiness_status: str
    passed: bool
    candidate_unpublished: bool = True
    publish_count: int = 0
    current_pointer_changes: int = 0
    provider_fetches: int = 0
    lake_writes: int = 0
    credential_reads: int = 0
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "quality_status": self.quality_status,
            "readiness_status": self.readiness_status,
            "passed": self.passed,
            "candidate_unpublished": self.candidate_unpublished,
            "publish_count": self.publish_count,
            "current_pointer_changes": self.current_pointer_changes,
            "provider_fetches": self.provider_fetches,
            "lake_writes": self.lake_writes,
            "credential_reads": self.credential_reads,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ReadQueryContract:
    dataset: str
    read_scope: str
    allowed: bool
    source_of_truth: str
    current_truth_visible: bool
    provider_fetches: int = 0
    lake_writes: int = 0
    credential_reads: int = 0
    unpublished_lake_scans: int = 0
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "read_scope": self.read_scope,
            "allowed": self.allowed,
            "source_of_truth": self.source_of_truth,
            "current_truth_visible": self.current_truth_visible,
            "provider_fetches": self.provider_fetches,
            "lake_writes": self.lake_writes,
            "credential_reads": self.credential_reads,
            "unpublished_lake_scans": self.unpublished_lake_scans,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class BenchmarkGroupReadinessResult:
    passed: bool
    release_blocked: bool
    rows: tuple[dict[str, Any], ...]
    required_missing: tuple[dict[str, Any], ...]
    allowed_claims: tuple[str, ...]
    blocked_claims: tuple[dict[str, Any], ...]
    error_codes: tuple[str, ...]
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS))
    production_excess_return_allowed_count: int = 0
    index_enhancement_allowed_count: int = 0
    tracking_error_allowed_count: int = 0

    @property
    def required_missing_count(self) -> int:
        return len(self.required_missing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "release_blocked": self.release_blocked,
            "rows": [dict(item) for item in self.rows],
            "required_missing": [dict(item) for item in self.required_missing],
            "required_missing_count": self.required_missing_count,
            "allowed_claims": list(self.allowed_claims),
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "error_codes": list(self.error_codes),
            "operation_counts": dict(self.operation_counts),
            "production_excess_return_allowed_count": self.production_excess_return_allowed_count,
            "index_enhancement_allowed_count": self.index_enhancement_allowed_count,
            "tracking_error_allowed_count": self.tracking_error_allowed_count,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkPitValidationResult:
    passed: bool
    rows: tuple[dict[str, Any], ...]
    required_missing: tuple[dict[str, Any], ...]
    error_codes: tuple[str, ...]
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "rows": [dict(item) for item in self.rows],
            "required_missing": [dict(item) for item in self.required_missing],
            "error_codes": list(self.error_codes),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class PitReadinessResult:
    dataset_id: str
    pit_status: str
    passed: bool
    production_publish_allowed_count: int
    as_of_join_violation_count: int = 0
    current_snapshot_used: bool = False
    current_snapshot_not_pit_count: int = 0
    missing_fields: tuple[str, ...] = ()
    issues: tuple[dict[str, Any], ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "pit_status": self.pit_status,
            "passed": self.passed,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "as_of_join_violation_count": self.as_of_join_violation_count,
            "current_snapshot_used": self.current_snapshot_used,
            "current_snapshot_not_pit_count": self.current_snapshot_not_pit_count,
            "missing_fields": list(self.missing_fields),
            "issues": [dict(item) for item in self.issues],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class LifecycleReadinessResult:
    dataset_id: str
    lifecycle_status: str
    passed: bool
    production_publish_allowed_count: int
    active_denominator: int = 0
    missing_lifecycle_fields: tuple[str, ...] = ()
    code_change_ready: bool = False
    issues: tuple[dict[str, Any], ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "lifecycle_status": self.lifecycle_status,
            "passed": self.passed,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "active_denominator": self.active_denominator,
            "missing_lifecycle_fields": list(self.missing_lifecycle_fields),
            "code_change_ready": self.code_change_ready,
            "issues": [dict(item) for item in self.issues],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class TradabilityReadinessResult:
    dataset_id: str
    tradability_status: str
    passed: bool
    production_publish_allowed_count: int
    trade_status_ready: bool = False
    prices_limit_ready: bool = False
    st_suspend_ready: bool = False
    can_buy_ready: bool = False
    can_sell_ready: bool = False
    issues: tuple[dict[str, Any], ...] = ()
    blocked_claims: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_FORBIDDEN_OPERATION_COUNTERS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "tradability_status": self.tradability_status,
            "passed": self.passed,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "trade_status_ready": self.trade_status_ready,
            "prices_limit_ready": self.prices_limit_ready,
            "st_suspend_ready": self.st_suspend_ready,
            "can_buy_ready": self.can_buy_ready,
            "can_sell_ready": self.can_sell_ready,
            "issues": [dict(item) for item in self.issues],
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class AdjustmentPublishReadinessResult:
    release_id: str
    passed: bool
    publish_allowed: bool
    production_publish_allowed_count: int
    readiness_field_coverage_ratio: float
    factor_coverage_ratio: float
    required_view_ids: tuple[str, ...]
    ready_view_ids: tuple[str, ...]
    missing_view_ids: tuple[str, ...]
    view_readiness: dict[str, bool]
    coverage_by_view: dict[str, float]
    policy_metadata: dict[str, Any]
    issues: tuple[dict[str, Any], ...] = ()
    blocked_reasons: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_ADJUSTMENT_OPERATION_COUNTERS))
    qmt_adjusted_execution_allowed_count: int = 0
    legacy_qfq_baseline_preserved: bool = False
    legacy_qfq_baseline_overwrite_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "passed": self.passed,
            "publish_allowed": self.publish_allowed,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "readiness_field_coverage_ratio": self.readiness_field_coverage_ratio,
            "factor_coverage_ratio": self.factor_coverage_ratio,
            "required_view_ids": list(self.required_view_ids),
            "ready_view_ids": list(self.ready_view_ids),
            "missing_view_ids": list(self.missing_view_ids),
            "view_readiness": dict(self.view_readiness),
            "coverage_by_view": dict(self.coverage_by_view),
            "policy_metadata": dict(self.policy_metadata),
            "issues": [dict(item) for item in self.issues],
            "blocked_reasons": [dict(item) for item in self.blocked_reasons],
            "operation_counts": dict(self.operation_counts),
            "qmt_adjusted_execution_allowed_count": int(self.qmt_adjusted_execution_allowed_count),
            "legacy_qfq_baseline_preserved": self.legacy_qfq_baseline_preserved,
            "legacy_qfq_baseline_overwrite_count": int(self.legacy_qfq_baseline_overwrite_count),
        }


@dataclass(frozen=True, slots=True)
class ReleaseReadinessAuditReport:
    release: dict[str, Any]
    dataset: tuple[dict[str, Any], ...]
    quality: dict[str, Any]
    blocked_claims: tuple[dict[str, Any], ...]
    rollback_target: dict[str, Any]
    evidence_refs: tuple[str, ...]
    publish_allowed: bool
    production_publish_allowed_count: int
    required_missing: tuple[dict[str, Any], ...] = ()
    p0_failures: tuple[dict[str, Any], ...] = ()
    quality_failures: tuple[dict[str, Any], ...] = ()
    blocked_reasons: tuple[dict[str, Any], ...] = ()
    missing_evidence_refs: tuple[str, ...] = ()
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(CR018_RELEASE_AUDIT_OPERATION_COUNTERS))
    historical_evidence_delete_counts: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in CR018_RELEASE_AUDIT_HISTORICAL_EVIDENCE_KEYS}
    )
    required_fields: tuple[str, ...] = CR018_RELEASE_AUDIT_REQUIRED_FIELDS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": CR018_RELEASE_READINESS_AUDIT_SCHEMA,
            "release": dict(self.release),
            "dataset": [dict(item) for item in self.dataset],
            "quality": dict(self.quality),
            "blocked_claims": [dict(item) for item in self.blocked_claims],
            "rollback_target": dict(self.rollback_target),
            "evidence_refs": list(self.evidence_refs),
            "publish_allowed": self.publish_allowed,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "required_missing": [dict(item) for item in self.required_missing],
            "p0_failures": [dict(item) for item in self.p0_failures],
            "quality_failures": [dict(item) for item in self.quality_failures],
            "blocked_reasons": [dict(item) for item in self.blocked_reasons],
            "missing_evidence_refs": list(self.missing_evidence_refs),
            "operation_counts": dict(self.operation_counts),
            "historical_evidence_delete_counts": dict(self.historical_evidence_delete_counts),
            "required_fields": list(self.required_fields),
        }


def validate_benchmark_group_readiness(
    readiness_rows: Any,
    *,
    permission_counters: Mapping[str, Any] | None = None,
) -> BenchmarkGroupReadinessResult:
    """校验 CR018 四类 benchmark x 三类 dataset type readiness matrix。"""

    rows = _benchmark_rows(readiness_rows)
    row_by_key = {
        (str(row.get("benchmark_id") or ""), str(row.get("dataset_type") or "")): row
        for row in rows
    }
    counters = _normalise_cr018_benchmark_counters(permission_counters)
    counter_violation = any(value != 0 for value in counters.values())

    output_rows: list[dict[str, Any]] = []
    required_missing: list[dict[str, Any]] = []
    blocked_claims: list[dict[str, Any]] = []
    error_codes: list[str] = []

    for benchmark_id in CR018_BENCHMARK_IDS:
        for dataset_type in CR018_BENCHMARK_DATASET_TYPES:
            row = dict(row_by_key.get((benchmark_id, dataset_type), {}))
            reason_code = ""
            status = str(row.get("readiness_status") or row.get("status") or READINESS_STATUS_REQUIRED_MISSING)
            if not row:
                reason_code = CR018_BENCHMARK_REASON_BY_DATASET_TYPE[dataset_type]
                status = READINESS_STATUS_REQUIRED_MISSING
            elif not bool(row.get("required_for_publish", CR018_BENCHMARK_REQUIRED_FOR_PUBLISH)):
                reason_code = CR018_BENCHMARK_REASON_BY_DATASET_TYPE[dataset_type]
                status = READINESS_STATUS_REQUIRED_MISSING
            elif not _is_benchmark_status_available(status):
                reason_code = str(row.get("reason_code") or CR018_BENCHMARK_REASON_BY_DATASET_TYPE[dataset_type])
            elif not str(row.get("coverage_denominator") or "").strip():
                reason_code = CR018_BENCHMARK_REASON_TRADE_CALENDAR_DENOMINATOR_MISSING
                status = READINESS_STATUS_REQUIRED_MISSING

            matrix_row = {
                "benchmark_id": benchmark_id,
                "index_code": str(row.get("index_code") or CR018_BENCHMARK_INDEX_CODES[benchmark_id]),
                "dataset_type": dataset_type,
                "required_for_publish": CR018_BENCHMARK_REQUIRED_FOR_PUBLISH,
                "readiness_status": status,
                "coverage_denominator": str(row.get("coverage_denominator") or ""),
                "reason_code": reason_code,
                "claim_impact": list(CR018_BENCHMARK_BLOCKED_CLAIMS),
            }
            output_rows.append(matrix_row)
            if not reason_code:
                continue
            error_codes.append(reason_code)
            missing_row = {
                "benchmark_id": benchmark_id,
                "index_code": matrix_row["index_code"],
                "dataset_type": dataset_type,
                "reason_code": reason_code,
                "readiness_status": status,
                "required_for_publish": True,
            }
            required_missing.append(missing_row)
            blocked_claims.extend(_benchmark_blocked_claim_rows(missing_row))

    if counter_violation:
        error_codes.append(CR018_BENCHMARK_REASON_PERMISSION_COUNTER_VIOLATION)
        blocked_claims.extend(
            {
                "claim": claim,
                "reason_code": CR018_BENCHMARK_REASON_PERMISSION_COUNTER_VIOLATION,
                "operation_counts": dict(counters),
            }
            for claim in CR018_BENCHMARK_BLOCKED_CLAIMS
        )

    passed = not required_missing and not counter_violation
    allowed_claims = CR018_BENCHMARK_BLOCKED_CLAIMS if passed else ()
    allowed_count = 1 if passed else 0
    return BenchmarkGroupReadinessResult(
        passed=passed,
        release_blocked=not passed,
        rows=tuple(output_rows),
        required_missing=tuple(required_missing),
        allowed_claims=allowed_claims,
        blocked_claims=_dedupe_cr018_rows(blocked_claims),
        error_codes=tuple(dict.fromkeys(error_codes)),
        operation_counts=counters,
        production_excess_return_allowed_count=allowed_count,
        index_enhancement_allowed_count=allowed_count,
        tracking_error_allowed_count=allowed_count,
    )


def validate_benchmark_components_weights_pit(
    components_rows: Any,
    weights_rows: Any,
    *,
    benchmark_ids: Sequence[str] | None = None,
) -> BenchmarkPitValidationResult:
    """校验 benchmark components / weights 的 PIT 和 membership 对齐边界。"""

    components = _benchmark_rows(components_rows)
    weights = _benchmark_rows(weights_rows)
    ids = tuple(
        dict.fromkeys(
            str(item)
            for item in (
                benchmark_ids
                or tuple(row.get("benchmark_id") for row in (*components, *weights) if row.get("benchmark_id"))
                or CR018_BENCHMARK_IDS
            )
        )
    )
    result_rows: list[dict[str, Any]] = []
    required_missing: list[dict[str, Any]] = []
    error_codes: list[str] = []

    for benchmark_id in ids:
        component_rows = [row for row in components if str(row.get("benchmark_id") or "") == benchmark_id]
        weight_rows = [row for row in weights if str(row.get("benchmark_id") or "") == benchmark_id]
        if not component_rows:
            missing = {
                "benchmark_id": benchmark_id,
                "dataset_type": CR018_BENCHMARK_DATASET_COMPONENTS,
                "reason_code": CR018_BENCHMARK_REASON_COMPONENTS_MISSING,
            }
            required_missing.append(missing)
            error_codes.append(CR018_BENCHMARK_REASON_COMPONENTS_MISSING)
            result_rows.append({**missing, "readiness_status": READINESS_STATUS_REQUIRED_MISSING})
        if not weight_rows:
            missing = {
                "benchmark_id": benchmark_id,
                "dataset_type": CR018_BENCHMARK_DATASET_WEIGHTS,
                "reason_code": CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
            }
            required_missing.append(missing)
            error_codes.append(CR018_BENCHMARK_REASON_WEIGHTS_MISSING)
            result_rows.append({**missing, "readiness_status": READINESS_STATUS_REQUIRED_MISSING})

        if component_rows and any(_is_current_snapshot(row) or not _has_pit_fields(row) for row in component_rows):
            issue = {
                "benchmark_id": benchmark_id,
                "dataset_type": CR018_BENCHMARK_DATASET_COMPONENTS,
                "reason_code": CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT,
            }
            required_missing.append(issue)
            error_codes.append(CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT)
            result_rows.append({**issue, "readiness_status": READINESS_STATUS_NON_PIT_SNAPSHOT})

        if weight_rows and any(not _has_pit_fields(row) for row in weight_rows):
            issue = {
                "benchmark_id": benchmark_id,
                "dataset_type": CR018_BENCHMARK_DATASET_WEIGHTS,
                "reason_code": CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
            }
            required_missing.append(issue)
            error_codes.append(CR018_BENCHMARK_REASON_WEIGHTS_MISSING)
            result_rows.append({**issue, "readiness_status": READINESS_STATUS_REQUIRED_MISSING})

        if component_rows and weight_rows:
            component_symbols = _membership_symbols(component_rows)
            weight_symbols = _weight_symbols(weight_rows)
            if component_symbols != weight_symbols:
                issue = {
                    "benchmark_id": benchmark_id,
                    "dataset_type": CR018_BENCHMARK_DATASET_WEIGHTS,
                    "reason_code": CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH,
                    "component_symbols": sorted(component_symbols),
                    "weight_symbols": sorted(weight_symbols),
                }
                required_missing.append(issue)
                error_codes.append(CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH)
                result_rows.append({**issue, "readiness_status": READINESS_STATUS_PIT_INCOMPLETE})

        if not any(row.get("benchmark_id") == benchmark_id for row in result_rows):
            result_rows.append(
                {
                    "benchmark_id": benchmark_id,
                    "dataset_type": "components_weights_pit",
                    "readiness_status": READINESS_STATUS_AVAILABLE,
                    "reason_code": "",
                }
            )

    return BenchmarkPitValidationResult(
        passed=not required_missing,
        rows=tuple(result_rows),
        required_missing=_dedupe_cr018_rows(required_missing),
        error_codes=tuple(dict.fromkeys(error_codes)),
    )


def validate_pit_universe_readiness(
    universe_rows: Any,
    *,
    dataset_id: str = CR018_PIT_READINESS_DATASET_ID,
    decision_time: str | None = None,
    permission_counters: Mapping[str, Any] | None = None,
) -> PitReadinessResult:
    """校验 PIT universe readiness，缺可得性字段或当前快照时 fail closed。"""

    rows = _readiness_rows(universe_rows)
    counters = _normalise_cr018_counters(permission_counters)
    issues: list[dict[str, Any]] = []
    missing_fields = _missing_required_fields(rows, CR018_PIT_REQUIRED_FIELDS)
    if missing_fields:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_PIT_AVAILABLE_FIELD_MISSING,
                field=",".join(missing_fields),
                detail={"missing_fields": list(missing_fields)},
            )
        )

    snapshot_rows = [row for row in rows if _cr018_current_snapshot_not_pit(row)]
    if snapshot_rows:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT,
                field="snapshot_date",
                detail={"current_snapshot_not_pit_count": len(snapshot_rows)},
            )
        )

    as_of_join_violation_count = _as_of_join_violation_count(rows, decision_time=decision_time)
    if as_of_join_violation_count:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_AS_OF_JOIN_VIOLATION,
                field="available_at",
                detail={"as_of_join_violation_count": as_of_join_violation_count},
            )
        )

    _append_counter_issue(issues, dataset_id, counters)
    passed = not issues
    if passed:
        status = READINESS_STATUS_AVAILABLE
    elif snapshot_rows:
        status = READINESS_STATUS_NON_PIT_SNAPSHOT
    elif missing_fields:
        status = READINESS_STATUS_REQUIRED_MISSING
    else:
        status = READINESS_STATUS_QUALITY_FAILED
    return PitReadinessResult(
        dataset_id=dataset_id,
        pit_status=status,
        passed=passed,
        production_publish_allowed_count=1 if passed else 0,
        as_of_join_violation_count=as_of_join_violation_count,
        current_snapshot_used=bool(snapshot_rows),
        current_snapshot_not_pit_count=len(snapshot_rows),
        missing_fields=tuple(missing_fields),
        issues=tuple(issues),
        blocked_claims=_cr018_blocked_claims(issues),
        operation_counts=counters,
    )


def validate_lifecycle_readiness(
    lifecycle_rows: Any,
    *,
    code_change_rows: Any = None,
    as_of_trade_date: str | None = None,
    active_denominator: int | None = None,
    dataset_id: str = CR018_LIFECYCLE_READINESS_DATASET_ID,
    permission_counters: Mapping[str, Any] | None = None,
) -> LifecycleReadinessResult:
    """校验 lifecycle / code-change readiness，active denominator 不可算时阻断。"""

    rows = _readiness_rows(lifecycle_rows)
    counters = _normalise_cr018_counters(permission_counters)
    issues: list[dict[str, Any]] = []
    missing_fields = _missing_required_fields(rows, CR018_LIFECYCLE_REQUIRED_FIELDS)
    if missing_fields:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_LIFECYCLE_FIELD_MISSING,
                field=",".join(missing_fields),
                detail={"missing_fields": list(missing_fields)},
            )
        )

    code_change_ready = _code_change_ready(rows, code_change_rows)
    if not code_change_ready:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_CODE_CHANGE_REQUIRED_MISSING,
                field="code_change_mapping",
            )
        )

    denominator = _active_denominator(rows, as_of_trade_date, active_denominator)
    if denominator <= 0:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_ACTIVE_DENOMINATOR_MISSING,
                field="active_denominator",
            )
        )

    _append_counter_issue(issues, dataset_id, counters)
    passed = not issues
    status = READINESS_STATUS_AVAILABLE if passed else READINESS_STATUS_REQUIRED_MISSING
    return LifecycleReadinessResult(
        dataset_id=dataset_id,
        lifecycle_status=status,
        passed=passed,
        production_publish_allowed_count=1 if passed else 0,
        active_denominator=denominator,
        missing_lifecycle_fields=tuple(missing_fields),
        code_change_ready=code_change_ready,
        issues=tuple(issues),
        blocked_claims=_cr018_blocked_claims(issues),
        operation_counts=counters,
    )


def validate_tradability_readiness(
    trade_status_rows: Any,
    prices_limit_rows: Any,
    *,
    st_suspend_rows: Any = None,
    trade_intents: Any = None,
    dataset_id: str = CR018_TRADABILITY_READINESS_DATASET_ID,
    permission_counters: Mapping[str, Any] | None = None,
) -> TradabilityReadinessResult:
    """校验 ST / suspend / trade_status / prices_limit readiness，不做涨跌停假设。"""

    trade_rows = _readiness_rows(trade_status_rows)
    limit_rows = _readiness_rows(prices_limit_rows)
    st_rows = _readiness_rows(st_suspend_rows) if st_suspend_rows is not None else trade_rows
    intent_rows = _readiness_rows(trade_intents)
    counters = _normalise_cr018_counters(permission_counters)
    issues: list[dict[str, Any]] = []

    trade_missing = _missing_required_fields(trade_rows, CR018_TRADE_STATUS_REQUIRED_FIELDS)
    if trade_missing:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_TRADE_STATUS_REQUIRED_MISSING,
                field=",".join(trade_missing),
                detail={"missing_fields": list(trade_missing)},
            )
        )
    st_missing = _missing_required_fields(st_rows, CR018_ST_SUSPEND_REQUIRED_FIELDS)
    if st_missing:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_ST_SUSPEND_REQUIRED_MISSING,
                field=",".join(st_missing),
                detail={"missing_fields": list(st_missing)},
            )
        )
    limit_missing = _prices_limit_missing_fields(limit_rows)
    if limit_missing:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING,
                field=",".join(limit_missing),
                detail={"missing_fields": list(limit_missing)},
            )
        )
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED,
                field="limit_up,limit_down",
                detail={"reason": "missing prices_limit cannot imply buy/sell fillability"},
            )
        )

    limit_assumption_count = _limit_assumption_block_count(intent_rows, limit_rows)
    if limit_assumption_count:
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED,
                field="execution_price",
                detail={"limit_bound_intent_count": limit_assumption_count},
            )
        )

    _append_counter_issue(issues, dataset_id, counters)
    trade_status_ready = not trade_missing
    prices_limit_ready = not limit_missing
    st_suspend_ready = not st_missing
    passed = not issues
    return TradabilityReadinessResult(
        dataset_id=dataset_id,
        tradability_status=READINESS_STATUS_AVAILABLE if passed else READINESS_STATUS_REQUIRED_MISSING,
        passed=passed,
        production_publish_allowed_count=1 if passed else 0,
        trade_status_ready=trade_status_ready,
        prices_limit_ready=prices_limit_ready,
        st_suspend_ready=st_suspend_ready,
        can_buy_ready=passed,
        can_sell_ready=passed,
        issues=tuple(issues),
        blocked_claims=_cr018_blocked_claims(issues),
        operation_counts=counters,
    )


def validate_adjustment_publish_readiness(
    readiness_rows: Any,
    *,
    release_id: str = "",
    factor_coverage_ratio: float | None = None,
    legacy_qfq_baseline_ref: str | None = None,
    permission_counters: Mapping[str, Any] | None = None,
    policy_metadata: Mapping[str, Any] | None = None,
) -> AdjustmentPublishReadinessResult:
    """校验 CR018-S05 raw / adj_factor / qfq / hfq / returns_adjusted readiness。

    本入口只消费调用方传入的 fixture / metadata；PASS 仅表示 release
    candidate 可进入后续显式 publish gate，不会触发 catalog current pointer。
    """

    rows = _adjustment_readiness_rows(readiness_rows)
    row_by_view = {_adjustment_view_id(row): row for row in rows if _adjustment_view_id(row)}
    counters = _normalise_cr018_adjustment_counters(permission_counters)
    issues: list[dict[str, Any]] = []
    coverage_by_view: dict[str, float] = {}
    view_readiness: dict[str, bool] = {}
    policies_seen_by_view: dict[str, list[str]] = {}

    for view_id in CR018_ADJUSTMENT_REQUIRED_VIEW_IDS:
        row = row_by_view.get(view_id)
        if row is None:
            coverage_by_view[view_id] = 0.0
            view_readiness[view_id] = False
            issues.append(
                _adjustment_readiness_issue(
                    view_id,
                    CR018_ADJUSTMENT_REASON_VIEW_REQUIRED_MISSING,
                    field="view_id",
                    detail={"required_view_id": view_id},
                )
            )
            continue

        required_fields = CR017_REQUIRED_FIELD_SETS.get(view_id, ())
        missing_fields = _adjustment_missing_required_fields(row, required_fields)
        coverage = _field_coverage_ratio(required_fields, missing_fields)
        coverage_by_view[view_id] = coverage

        policies = _adjustment_row_policies(row)
        policies_seen_by_view[view_id] = list(policies)
        policy_ok = _adjustment_policy_matches(view_id, policies)
        status_ready = _is_adjustment_status_available(
            str(row.get("readiness_status") or row.get("quality_status") or row.get("status") or READINESS_STATUS_AVAILABLE)
        )
        view_ready = coverage == 1.0 and status_ready and policy_ok
        view_readiness[view_id] = view_ready

        if coverage < 1.0:
            issues.append(
                _adjustment_readiness_issue(
                    view_id,
                    CR018_ADJUSTMENT_REASON_FIELD_COVERAGE_INCOMPLETE,
                    field=",".join(missing_fields),
                    detail={
                        "field_coverage_ratio": coverage,
                        "missing_fields": list(missing_fields),
                    },
                )
            )
        if not status_ready:
            issues.append(
                _adjustment_readiness_issue(
                    view_id,
                    str(row.get("reason_code") or CR017_QUALITY_FAILED),
                    field="readiness_status",
                    detail={
                        "readiness_status": str(row.get("readiness_status") or row.get("quality_status") or row.get("status") or ""),
                    },
                )
            )
        if not policy_ok:
            issues.append(
                _adjustment_readiness_issue(
                    view_id,
                    CR017_MIXED_ADJUSTMENT_POLICY if len(policies) > 1 else CR018_ADJUSTMENT_REASON_POLICY_MISMATCH,
                    field="research_adjustment_policy",
                    detail={
                        "expected_policy": CR018_ADJUSTMENT_EXPECTED_POLICIES.get(view_id, ""),
                        "policies_seen": list(policies),
                    },
                )
            )

    factor_ratio = _adjustment_factor_coverage_ratio(
        row_by_view.get(CR017_VIEW_ADJ_FACTOR),
        explicit_ratio=factor_coverage_ratio,
    )
    if factor_ratio < 1.0:
        issues.append(
            _adjustment_readiness_issue(
                CR017_VIEW_ADJ_FACTOR,
                CR018_ADJUSTMENT_REASON_FACTOR_COVERAGE_INCOMPLETE,
                field="factor_coverage_ratio",
                detail={"factor_coverage_ratio": factor_ratio},
            )
        )

    legacy_ref = str(legacy_qfq_baseline_ref or (policy_metadata or {}).get("legacy_qfq_baseline_ref") or "")
    legacy_preserved = bool(legacy_ref)
    if not legacy_preserved:
        issues.append(
            _adjustment_readiness_issue(
                CR017_VIEW_PRICES_QFQ,
                CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_REQUIRED,
                field="legacy_qfq_baseline_ref",
            )
        )

    legacy_overwrite_count = int(counters.get("legacy_qfq_overwrite", 0))
    if legacy_overwrite_count:
        issues.append(
            _adjustment_readiness_issue(
                CR017_VIEW_PRICES_QFQ,
                CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_OVERWRITE,
                field="legacy_qfq_baseline_overwrite",
                detail={"legacy_qfq_baseline_overwrite_count": legacy_overwrite_count},
            )
        )

    qmt_adjusted_allowed = int(counters.get("qmt_adjusted_execution_allowed", 0))
    if qmt_adjusted_allowed:
        issues.append(
            _adjustment_readiness_issue(
                "qmt_execution",
                CR018_ADJUSTMENT_REASON_QMT_REQUIRES_RAW,
                field="execution_price_policy",
                detail={"qmt_adjusted_execution_allowed_count": qmt_adjusted_allowed},
            )
        )
    _append_adjustment_counter_issue(issues, counters)

    ready_view_ids = tuple(view_id for view_id in CR018_ADJUSTMENT_REQUIRED_VIEW_IDS if view_readiness.get(view_id))
    missing_view_ids = tuple(view_id for view_id in CR018_ADJUSTMENT_REQUIRED_VIEW_IDS if not view_readiness.get(view_id))
    readiness_coverage = (
        len(ready_view_ids) / len(CR018_ADJUSTMENT_REQUIRED_VIEW_IDS)
        if CR018_ADJUSTMENT_REQUIRED_VIEW_IDS
        else 0.0
    )
    passed = not issues and readiness_coverage == 1.0 and factor_ratio == 1.0
    metadata = {
        "schema_name": "cr018_adjustment_readiness_v1",
        "release_id": str(release_id),
        "required_view_ids": list(CR018_ADJUSTMENT_REQUIRED_VIEW_IDS),
        "coverage_by_view": dict(coverage_by_view),
        "view_readiness": dict(view_readiness),
        "policies_seen_by_view": policies_seen_by_view,
        "expected_policies": dict(CR018_ADJUSTMENT_EXPECTED_POLICIES),
        "legacy_qfq_baseline_preserved": legacy_preserved,
        "legacy_qfq_baseline_ref": legacy_ref,
        **dict(policy_metadata or {}),
    }
    return AdjustmentPublishReadinessResult(
        release_id=str(release_id),
        passed=passed,
        publish_allowed=passed,
        production_publish_allowed_count=1 if passed else 0,
        readiness_field_coverage_ratio=float(readiness_coverage),
        factor_coverage_ratio=float(factor_ratio),
        required_view_ids=CR018_ADJUSTMENT_REQUIRED_VIEW_IDS,
        ready_view_ids=ready_view_ids,
        missing_view_ids=missing_view_ids,
        view_readiness=view_readiness,
        coverage_by_view=coverage_by_view,
        policy_metadata=metadata,
        issues=tuple(issues),
        blocked_reasons=tuple(_adjustment_blocked_reasons(issues)),
        operation_counts=counters,
        qmt_adjusted_execution_allowed_count=qmt_adjusted_allowed,
        legacy_qfq_baseline_preserved=legacy_preserved,
        legacy_qfq_baseline_overwrite_count=legacy_overwrite_count,
    )


def build_release_readiness_audit_report(
    release_id: str,
    dataset_readiness: Any,
    *,
    quality: Mapping[str, Any] | None = None,
    blocked_claims: Sequence[Mapping[str, Any]] | None = None,
    rollback_target: str | Mapping[str, Any] | None = None,
    evidence_refs: Sequence[str] | Mapping[str, Any] | None = None,
    required_evidence_refs: Sequence[str] = CR018_RELEASE_AUDIT_REQUIRED_EVIDENCE_REFS,
    permission_counters: Mapping[str, Any] | None = None,
    release_metadata: Mapping[str, Any] | None = None,
) -> ReleaseReadinessAuditReport:
    """聚合 release-level readiness audit；只消费显式 metadata，不触发真实 publish。"""

    release_payload = {
        "release_id": str(release_id),
        "schema_name": CR018_RELEASE_READINESS_AUDIT_SCHEMA,
        "scope": "release",
        **dict(release_metadata or {}),
    }
    dataset_rows = _release_dataset_rows(dataset_readiness)
    quality_summary = _release_quality_summary(quality, dataset_rows)
    counters = _normalise_release_audit_counters(permission_counters)
    rollback_payload, rollback_errors = _release_rollback_target_payload(rollback_target)
    evidence_list, missing_evidence = _release_evidence_refs(evidence_refs, required_evidence_refs)

    p0_failures: list[dict[str, Any]] = []
    required_missing: list[dict[str, Any]] = []
    generated_blocked_claims: list[dict[str, Any]] = []
    for row in dataset_rows:
        if str(row.get("priority") or "P0") == "P1":
            continue
        if row.get("required_missing_count", 0):
            required_missing.append(
                {
                    "dataset_id": row["dataset_id"],
                    "reason_code": CR018_RELEASE_REASON_REQUIRED_MISSING,
                    "readiness_status": row["readiness_status"],
                    "required_missing_count": row["required_missing_count"],
                }
            )
        if not bool(row.get("passed")) or row.get("required_missing_count", 0):
            failure = {
                "dataset_id": row["dataset_id"],
                "reason_code": CR018_RELEASE_REASON_P0_READINESS_FAILED,
                "readiness_status": row["readiness_status"],
                "required_missing_count": row["required_missing_count"],
                "quality_status": row.get("quality_status", ""),
            }
            p0_failures.append(failure)
            generated_blocked_claims.extend(_release_p0_blocked_claims(failure))
            generated_blocked_claims.extend(_normalise_release_blocked_claims(row.get("blocked_claims", ())))

    quality_failures: list[dict[str, Any]] = []
    if bool(quality_summary.get("quality_failed")):
        failure = {
            "dataset_id": str(quality_summary.get("dataset_id") or "release_quality"),
            "reason_code": CR018_RELEASE_REASON_QUALITY_FAILED,
            "quality_status": str(quality_summary.get("quality_status") or quality_summary.get("status") or ""),
        }
        quality_failures.append(failure)
        generated_blocked_claims.extend(_release_p0_blocked_claims(failure))

    blocked_reasons: list[dict[str, Any]] = []
    blocked_reasons.extend(p0_failures)
    blocked_reasons.extend(required_missing)
    blocked_reasons.extend(quality_failures)
    for error_code in rollback_errors:
        blocked_reasons.append({"reason_code": error_code, "field": "rollback_target"})
        generated_blocked_claims.extend(_release_p0_blocked_claims({"reason_code": error_code, "field": "rollback_target"}))
    if missing_evidence:
        evidence_failure = {
            "reason_code": CR018_RELEASE_REASON_AUDIT_EVIDENCE_INCOMPLETE,
            "field": "evidence_refs",
            "missing_evidence_refs": list(missing_evidence),
        }
        blocked_reasons.append(evidence_failure)
        generated_blocked_claims.extend(_release_p0_blocked_claims(evidence_failure))
    if any(value != 0 for value in counters.values()):
        counter_failure = {
            "reason_code": CR018_RELEASE_REASON_PERMISSION_COUNTER_VIOLATION,
            "field": "operation_counts",
            "operation_counts": dict(counters),
        }
        blocked_reasons.append(counter_failure)
        generated_blocked_claims.extend(_release_p0_blocked_claims(counter_failure))

    explicit_blocked_claims = _normalise_release_blocked_claims(blocked_claims or ())
    all_blocked_claims = _dedupe_release_rows((*explicit_blocked_claims, *generated_blocked_claims))
    publish_allowed = not blocked_reasons
    release_payload["publish_readiness_pass"] = publish_allowed
    release_payload["allowed_claims"] = (
        ["production_current_truth_scoped_release", "production_publish"]
        if publish_allowed
        else []
    )
    return ReleaseReadinessAuditReport(
        release=release_payload,
        dataset=tuple(dataset_rows),
        quality=quality_summary,
        blocked_claims=all_blocked_claims,
        rollback_target=rollback_payload,
        evidence_refs=tuple(evidence_list),
        publish_allowed=publish_allowed,
        production_publish_allowed_count=1 if publish_allowed else 0,
        required_missing=tuple(required_missing),
        p0_failures=tuple(p0_failures),
        quality_failures=tuple(quality_failures),
        blocked_reasons=_dedupe_release_rows(blocked_reasons),
        missing_evidence_refs=tuple(missing_evidence),
        operation_counts=counters,
    )


def _release_dataset_rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        rows = value.get("rows") or value.get("datasets")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return [_release_dataset_row(item, index) for index, item in enumerate(rows)]
        if any(
            key in value
            for key in (
                "dataset_id",
                "dataset",
                "view_id",
                "readiness_status",
                "passed",
                "required_missing",
                "required_missing_count",
            )
        ):
            return [_release_dataset_row(value, 0)]
        output = []
        for index, (dataset_id, payload) in enumerate(value.items()):
            if str(dataset_id) in {"release_id", "quality", "blocked_claims", "rollback_target", "evidence_refs"}:
                continue
            row_payload = _contract_payload(payload)
            row_payload.setdefault("dataset_id", str(dataset_id))
            output.append(_release_dataset_row(row_payload, index))
        return output
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_release_dataset_row(item, index) for index, item in enumerate(value)]
    return [_release_dataset_row(value, 0)]


def _release_dataset_row(value: Any, index: int) -> dict[str, Any]:
    payload = _contract_payload(value)
    nested = payload.get("readiness")
    if nested is not None:
        nested_payload = _contract_payload(nested)
        payload = {**nested_payload, **{key: val for key, val in payload.items() if key != "readiness"}}
    dataset_id = str(
        payload.get("dataset_id")
        or payload.get("dataset")
        or payload.get("view_id")
        or payload.get("release_dataset_id")
        or payload.get("benchmark_dataset_id")
        or payload.get("benchmark_id")
        or f"dataset_{index}"
    )
    readiness_status = _release_readiness_status(payload)
    required_missing = payload.get("required_missing") or ()
    required_missing_count = _release_int(payload.get("required_missing_count"), len(required_missing))
    passed = _release_dataset_passed(payload, readiness_status, required_missing_count)
    production_allowed = _release_int(
        payload.get("production_publish_allowed_count"),
        1 if passed else 0,
    )
    return {
        "dataset_id": dataset_id,
        "priority": str(payload.get("priority") or "P0"),
        "readiness_status": readiness_status,
        "quality_status": str(payload.get("quality_status") or payload.get("status") or ""),
        "passed": passed,
        "production_publish_allowed_count": production_allowed if passed else 0,
        "required_missing_count": required_missing_count,
        "required_missing": [dict(item) for item in required_missing if isinstance(item, Mapping)],
        "blocked_claims": [dict(item) for item in payload.get("blocked_claims", ()) if isinstance(item, Mapping)],
        "operation_counts": dict(payload.get("operation_counts") or payload.get("permission_counters") or {}),
    }


def _release_readiness_status(payload: Mapping[str, Any]) -> str:
    status = (
        payload.get("readiness_status")
        or payload.get("pit_status")
        or payload.get("lifecycle_status")
        or payload.get("tradability_status")
        or payload.get("status")
    )
    if status is None and "passed" in payload:
        return READINESS_STATUS_AVAILABLE if bool(payload.get("passed")) else READINESS_STATUS_REQUIRED_MISSING
    return str(status or READINESS_STATUS_REQUIRED_MISSING)


def _release_dataset_passed(
    payload: Mapping[str, Any],
    readiness_status: str,
    required_missing_count: int,
) -> bool:
    if "passed" in payload:
        passed = bool(payload.get("passed"))
    elif "publish_allowed" in payload:
        passed = bool(payload.get("publish_allowed"))
    else:
        passed = _release_status_available(readiness_status)
    if required_missing_count:
        return False
    if _release_quality_status_failed(str(payload.get("quality_status") or "")):
        return False
    return passed and _release_status_available(readiness_status)


def _release_quality_summary(
    quality: Mapping[str, Any] | None,
    dataset_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    payload = dict(quality or {})
    status = str(
        payload.get("quality_status")
        or payload.get("status")
        or (
            QUALITY_STATUS_FAIL
            if any(_release_quality_status_failed(str(row.get("quality_status") or "")) for row in dataset_rows)
            else QUALITY_STATUS_PASS
        )
    )
    failed = _release_quality_status_failed(status)
    failures = [dict(item) for item in payload.get("failures", ()) if isinstance(item, Mapping)]
    if failed and not failures:
        failures.append({"reason_code": CR018_RELEASE_REASON_QUALITY_FAILED, "quality_status": status})
    return {
        "quality_status": status,
        "status": status,
        "quality_failed": failed,
        "failure_count": len(failures),
        "failures": failures,
        **{key: value for key, value in payload.items() if key not in {"quality_status", "status", "failures"}},
    }


def _release_rollback_target_payload(
    rollback_target: str | Mapping[str, Any] | None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    if rollback_target is None:
        return (
            {"scope": "release", "target_release_id": "", "release_level": True},
            (CR018_RELEASE_REASON_ROLLBACK_TARGET_REQUIRED,),
        )
    if isinstance(rollback_target, Mapping):
        payload = dict(rollback_target)
    else:
        payload = {"target_release_id": str(rollback_target)}
    scope = str(payload.get("scope") or "release")
    target_release = str(
        payload.get("target_release_id")
        or payload.get("to_release")
        or payload.get("previous_release_id")
        or payload.get("rollback_target")
        or ""
    )
    errors: list[str] = []
    if scope != "release":
        errors.append(CR018_RELEASE_REASON_ROLLBACK_SCOPE_NOT_RELEASE)
    if not target_release.strip():
        errors.append(CR018_RELEASE_REASON_ROLLBACK_TARGET_REQUIRED)
    return (
        {
            **payload,
            "scope": scope,
            "target_release_id": target_release,
            "release_level": scope == "release",
            "dataset_only_rollback_allowed": False,
            "dataset_level_rollback_only_allowed_count": 0,
        },
        tuple(dict.fromkeys(errors)),
    )


def _release_evidence_refs(
    evidence_refs: Sequence[str] | Mapping[str, Any] | None,
    required_evidence_refs: Sequence[str],
) -> tuple[list[str], tuple[str, ...]]:
    if isinstance(evidence_refs, Mapping):
        refs_by_kind = {
            str(key): str(value)
            for key, value in evidence_refs.items()
            if key != "delete_counts" and _non_empty(value)
        }
        refs = [refs_by_kind[key] for key in refs_by_kind]
        missing = tuple(kind for kind in required_evidence_refs if not refs_by_kind.get(str(kind)))
        return refs, missing
    refs = [
        str(item)
        for item in (evidence_refs or ())
        if _non_empty(item)
    ]
    missing = () if refs else tuple(required_evidence_refs)
    return refs, missing


def _normalise_release_audit_counters(counters: Mapping[str, Any] | None) -> dict[str, int]:
    normalised = dict(CR018_RELEASE_AUDIT_OPERATION_COUNTERS)
    for key, value in dict(counters or {}).items():
        try:
            normalised[str(key)] = int(value)
        except (TypeError, ValueError):
            normalised[str(key)] = 1
    return normalised


def _normalise_release_blocked_claims(
    claims: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    rows = []
    for item in claims:
        payload = dict(item)
        is_p1 = str(payload.get("priority") or "") == "P1" or str(payload.get("reason_code") or "") == "p1_auxiliary_missing"
        if is_p1:
            payload.setdefault("core_release_blocking", False)
            payload.setdefault("capability_available", False)
        rows.append(payload)
    return _dedupe_release_rows(rows)


def _release_p0_blocked_claims(reason: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "claim": claim,
            "dataset_id": reason.get("dataset_id") or reason.get("field") or "release",
            "reason_code": reason.get("reason_code"),
            "priority": "P0",
            "core_release_blocking": True,
        }
        for claim in CR018_P0_READINESS_BLOCKED_CLAIMS
    )


def _dedupe_release_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("claim") or ""),
            str(payload.get("dataset_id") or ""),
            str(payload.get("field") or ""),
            str(payload.get("reason_code") or ""),
            str(payload.get("priority") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return tuple(output)


def _release_status_available(status: str) -> bool:
    return status.strip().lower() in {
        READINESS_STATUS_AVAILABLE,
        QUALITY_STATUS_PASS,
        QUALITY_STATUS_WARN,
        "available",
        "pass",
        "published",
        "ready",
        "ok",
    }


def _release_quality_status_failed(status: str) -> bool:
    return status.strip().lower() in {
        QUALITY_STATUS_FAIL,
        QUALITY_STATUS_MISSING,
        READINESS_STATUS_REQUIRED_MISSING,
        READINESS_STATUS_QUALITY_FAILED,
        "fail",
        "failed",
        "missing",
    }


def _release_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _readiness_rows(value: Any) -> list[dict[str, Any]]:
    return _benchmark_rows(value)


def _adjustment_readiness_rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        if "view_id" in value or "dataset_id" in value or "dataset" in value:
            return [dict(value)]
        rows = value.get("rows")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return [dict(item) for item in rows if isinstance(item, Mapping)]
        keyed_rows = []
        for view_id in CR018_ADJUSTMENT_REQUIRED_VIEW_IDS:
            item = value.get(view_id)
            if isinstance(item, Mapping):
                keyed_rows.append({"view_id": view_id, **dict(item)})
            elif item is not None:
                keyed_rows.append({"view_id": view_id, "readiness_status": item})
        if keyed_rows:
            return keyed_rows
        return [dict(value)]
    return _benchmark_rows(value)


def _adjustment_view_id(row: Mapping[str, Any]) -> str:
    raw = str(row.get("view_id") or row.get("dataset_id") or row.get("dataset") or "").strip()
    aliases = {
        DATASET_PRICES: CR017_VIEW_PRICES_RAW,
        "raw": CR017_VIEW_PRICES_RAW,
        "qfq": CR017_VIEW_PRICES_QFQ,
        "hfq": CR017_VIEW_PRICES_HFQ,
    }
    return aliases.get(raw, raw)


def _adjustment_missing_required_fields(
    row: Mapping[str, Any],
    required_fields: Sequence[str],
) -> tuple[str, ...]:
    return tuple(field_name for field_name in required_fields if _cr017_is_missing(row.get(field_name)))


def _field_coverage_ratio(
    required_fields: Sequence[str],
    missing_fields: Sequence[str],
) -> float:
    if not required_fields:
        return 1.0
    return round((len(required_fields) - len(missing_fields)) / len(required_fields), 6)


def _adjustment_row_policies(row: Mapping[str, Any]) -> tuple[str, ...]:
    values: set[str] = set()
    for key in ("research_adjustment_policy", "adjustment_policy", "policy"):
        value = str(row.get(key) or "").strip()
        if value:
            values.add(value)
    raw_seen = row.get("policies_seen")
    if isinstance(raw_seen, Sequence) and not isinstance(raw_seen, (str, bytes, bytearray)):
        values.update(str(item).strip() for item in raw_seen if str(item).strip())
    return tuple(sorted(values))


def _adjustment_policy_matches(view_id: str, policies: Sequence[str]) -> bool:
    expected = CR018_ADJUSTMENT_EXPECTED_POLICIES.get(view_id)
    if not expected:
        return True
    if not policies and view_id in {CR017_VIEW_PRICES_RAW, CR017_VIEW_ADJ_FACTOR}:
        return True
    return tuple(policies) == (expected,)


def _is_adjustment_status_available(status: str) -> bool:
    return status.strip().lower() in {
        READINESS_STATUS_AVAILABLE,
        QUALITY_STATUS_PASS,
        "available",
        "pass",
        "published",
        "ready",
        "ok",
    }


def _adjustment_factor_coverage_ratio(
    adj_factor_row: Mapping[str, Any] | None,
    *,
    explicit_ratio: float | None,
) -> float:
    if explicit_ratio is not None:
        return _clamped_ratio(explicit_ratio)
    if adj_factor_row is None:
        return 0.0
    for key in ("factor_coverage_ratio", "coverage_ratio", "coverage"):
        if key in adj_factor_row and not _cr017_is_missing(adj_factor_row.get(key)):
            return _clamped_ratio(adj_factor_row.get(key))
    missing = _adjustment_missing_required_fields(
        adj_factor_row,
        CR017_REQUIRED_FIELD_SETS.get(CR017_VIEW_ADJ_FACTOR, ()),
    )
    return 1.0 if not missing else 0.0


def _clamped_ratio(value: Any) -> float:
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, ratio))


def _normalise_cr018_adjustment_counters(counters: Mapping[str, Any] | None) -> dict[str, int]:
    normalised = dict(CR018_ADJUSTMENT_OPERATION_COUNTERS)
    for key, value in dict(counters or {}).items():
        try:
            normalised[str(key)] = int(value)
        except (TypeError, ValueError):
            normalised[str(key)] = 1
    return normalised


def _append_adjustment_counter_issue(
    issues: list[dict[str, Any]],
    counters: Mapping[str, int],
) -> None:
    forbidden_keys = set(CR018_FORBIDDEN_OPERATION_COUNTERS)
    if any(counters.get(key, 0) != 0 for key in forbidden_keys):
        issues.append(
            _adjustment_readiness_issue(
                "adjustment_publish_readiness",
                CR018_REASON_PERMISSION_COUNTER_VIOLATION,
                field="operation_counts",
                detail={"operation_counts": dict(counters)},
            )
        )


def _adjustment_readiness_issue(
    view_id: str,
    reason_code: str,
    *,
    field: str = "",
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "view_id": view_id,
        "dataset_id": view_id,
        "field": field,
        "reason_code": reason_code,
        "severity": "BLOCKING",
        "claim_impact": list(CR018_P0_READINESS_BLOCKED_CLAIMS),
        **dict(detail or {}),
    }


def _adjustment_blocked_reasons(
    issues: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for issue in issues:
        payload = {
            "view_id": str(issue.get("view_id") or issue.get("dataset_id") or ""),
            "field": str(issue.get("field") or ""),
            "reason_code": str(issue.get("reason_code") or ""),
            "severity": str(issue.get("severity") or "BLOCKING"),
            "claim_impact": list(issue.get("claim_impact") or ()),
        }
        key = (payload["view_id"], payload["field"], payload["reason_code"])
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return output


def _missing_required_fields(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> list[str]:
    if not rows:
        return list(fields)
    missing: list[str] = []
    for field_name in fields:
        if all(field_name not in row for row in rows):
            missing.append(field_name)
            continue
        if any(field_name not in row or not _non_empty(row.get(field_name)) for row in rows):
            missing.append(field_name)
    return missing


def _cr018_current_snapshot_not_pit(row: Mapping[str, Any]) -> bool:
    if _is_current_snapshot(row):
        return True
    if _non_empty(row.get("snapshot_date")) and not _truthy(row.get("is_pit_universe")):
        return True
    return False


def _as_of_join_violation_count(
    rows: Sequence[Mapping[str, Any]],
    *,
    decision_time: str | None = None,
) -> int:
    count = 0
    for row in rows:
        as_of_value = decision_time or row.get("decision_time") or row.get("as_of_trade_date") or row.get("trade_date")
        if not _non_empty(as_of_value):
            continue
        as_of_ts = pd.to_datetime(as_of_value, utc=True, errors="coerce")
        available_ts = pd.to_datetime(row.get("available_at"), utc=True, errors="coerce")
        effective_ts = pd.to_datetime(row.get("effective_date"), utc=True, errors="coerce")
        if pd.isna(as_of_ts):
            continue
        if (not pd.isna(available_ts) and available_ts > as_of_ts) or (
            not pd.isna(effective_ts) and effective_ts > as_of_ts
        ):
            count += 1
    return count


def _code_change_ready(rows: Sequence[Mapping[str, Any]], code_change_rows: Any) -> bool:
    explicit_rows = _readiness_rows(code_change_rows)
    if explicit_rows:
        return True
    for row in rows:
        if any(_non_empty(row.get(field_name)) for field_name in CR018_CODE_CHANGE_EVIDENCE_FIELDS):
            return True
    return False


def _active_denominator(
    rows: Sequence[Mapping[str, Any]],
    as_of_trade_date: str | None,
    active_denominator: int | None,
) -> int:
    if active_denominator is not None:
        try:
            return max(0, int(active_denominator))
        except (TypeError, ValueError):
            return 0
    if not rows or not _non_empty(as_of_trade_date):
        return 0
    as_of_ts = pd.to_datetime(as_of_trade_date, utc=True, errors="coerce")
    if pd.isna(as_of_ts):
        return 0
    count = 0
    for row in rows:
        list_ts = pd.to_datetime(row.get("list_date"), utc=True, errors="coerce")
        delist_ts = pd.to_datetime(row.get("delist_date"), utc=True, errors="coerce")
        if pd.isna(list_ts) or pd.isna(delist_ts):
            continue
        if list_ts <= as_of_ts < delist_ts:
            count += 1
    return count


def _prices_limit_missing_fields(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    if not rows:
        return list(CR018_PRICES_LIMIT_REQUIRED_FIELDS)
    missing = []
    for field_name in ("trade_date", "symbol"):
        if field_name in _missing_required_fields(rows, (field_name,)):
            missing.append(field_name)
    limit_up_present = any(_non_empty(row.get("limit_up")) or _non_empty(row.get("upper_limit")) for row in rows)
    limit_down_present = any(_non_empty(row.get("limit_down")) or _non_empty(row.get("lower_limit")) for row in rows)
    if not limit_up_present:
        missing.append("limit_up")
    if not limit_down_present:
        missing.append("limit_down")
    return missing


def _limit_assumption_block_count(
    intents: Sequence[Mapping[str, Any]],
    limit_rows: Sequence[Mapping[str, Any]],
) -> int:
    if not intents or not limit_rows:
        return 0
    limits: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in limit_rows:
        key = (str(row.get("trade_date") or ""), str(row.get("symbol") or ""))
        if key != ("", ""):
            limits[key] = row
    count = 0
    for intent in intents:
        key = (str(intent.get("trade_date") or ""), str(intent.get("symbol") or ""))
        row = limits.get(key)
        if row is None:
            continue
        side = str(intent.get("side") or "").lower()
        price = _cr017_to_float(intent.get("execution_price") or intent.get("price"))
        limit_up = _cr017_to_float(row.get("limit_up") if "limit_up" in row else row.get("upper_limit"))
        limit_down = _cr017_to_float(row.get("limit_down") if "limit_down" in row else row.get("lower_limit"))
        if side == "buy" and price is not None and limit_up is not None and price >= limit_up:
            count += 1
        elif side == "sell" and price is not None and limit_down is not None and price <= limit_down:
            count += 1
    return count


def _normalise_cr018_counters(counters: Mapping[str, Any] | None) -> dict[str, int]:
    normalised = dict(CR018_FORBIDDEN_OPERATION_COUNTERS)
    for key, value in dict(counters or {}).items():
        try:
            normalised[str(key)] = int(value)
        except (TypeError, ValueError):
            normalised[str(key)] = 1
    return normalised


def _append_counter_issue(
    issues: list[dict[str, Any]],
    dataset_id: str,
    counters: Mapping[str, int],
) -> None:
    if any(value != 0 for value in counters.values()):
        issues.append(
            _cr018_readiness_issue(
                dataset_id,
                CR018_REASON_PERMISSION_COUNTER_VIOLATION,
                field="operation_counts",
                detail={"operation_counts": dict(counters)},
            )
        )


def _cr018_readiness_issue(
    dataset_id: str,
    reason_code: str,
    *,
    field: str = "",
    detail: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "field": field,
        "reason_code": reason_code,
        "severity": "BLOCKING",
        "claim_impact": list(CR018_P0_READINESS_BLOCKED_CLAIMS),
        **dict(detail or {}),
    }


def _cr018_blocked_claims(issues: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    rows = []
    for issue in issues:
        for claim in CR018_P0_READINESS_BLOCKED_CLAIMS:
            rows.append(
                {
                    "claim": claim,
                    "dataset_id": issue.get("dataset_id"),
                    "field": issue.get("field"),
                    "reason_code": issue.get("reason_code"),
                    "severity": issue.get("severity", "BLOCKING"),
                }
            )
    return _dedupe_cr018_rows(rows)


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "pit", "pit_universe"}
    return bool(value)


def _contract_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _benchmark_rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return [dict(item) for item in value.to_dict("records")]
    if isinstance(value, Mapping):
        rows = value.get("rows")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return [dict(item) for item in rows if isinstance(item, Mapping)]
        return [dict(value)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _benchmark_rows(to_dict())
    rows_attr = getattr(value, "rows", None)
    if rows_attr is not None:
        return _benchmark_rows(rows_attr)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _normalise_cr018_benchmark_counters(
    counters: Mapping[str, Any] | None,
) -> dict[str, int]:
    normalised = dict(CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS)
    for key, value in dict(counters or {}).items():
        try:
            normalised[str(key)] = int(value)
        except (TypeError, ValueError):
            normalised[str(key)] = 1
    return normalised


def _is_benchmark_status_available(status: str) -> bool:
    return status in {
        READINESS_STATUS_AVAILABLE,
        QUALITY_STATUS_PASS,
        "available",
        "pass",
        "published",
        "ready",
        "ok",
    }


def _benchmark_blocked_claim_rows(missing_row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "claim": claim,
            "benchmark_id": missing_row.get("benchmark_id"),
            "index_code": missing_row.get("index_code"),
            "dataset_type": missing_row.get("dataset_type"),
            "reason_code": missing_row.get("reason_code"),
            "readiness_status": missing_row.get("readiness_status"),
            "required_for_publish": True,
        }
        for claim in CR018_BENCHMARK_BLOCKED_CLAIMS
    ]


def _dedupe_cr018_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = dict(row)
        key = (
            str(payload.get("claim") or ""),
            str(payload.get("benchmark_id") or ""),
            str(payload.get("dataset_type") or ""),
            str(payload.get("reason_code") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(payload)
    return tuple(output)


def _has_pit_fields(row: Mapping[str, Any]) -> bool:
    return _non_empty(row.get("effective_date")) and _non_empty(row.get("available_at"))


def _is_current_snapshot(row: Mapping[str, Any]) -> bool:
    value = row.get("is_current_snapshot", row.get("current_snapshot", False))
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "current_snapshot"}
    return bool(value)


def _membership_symbols(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    symbols: set[str] = set()
    for row in rows:
        if row.get("is_member", True) in {False, "false", "False", 0, "0"}:
            continue
        symbol = row.get("symbol") or row.get("con_code")
        if _non_empty(symbol):
            symbols.add(str(symbol))
    return symbols


def _weight_symbols(rows: Sequence[Mapping[str, Any]]) -> set[str]:
    symbols: set[str] = set()
    for row in rows:
        symbol = row.get("symbol") or row.get("con_code")
        weight = row.get("weight")
        if _non_empty(symbol) and _non_empty(weight):
            symbols.add(str(symbol))
    return symbols


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    try:
        return not bool(pd.isna(value))
    except (TypeError, ValueError):
        return True


def adjustment_quality_gate(
    metadata: Any,
    *,
    required_fields: Sequence[str] | None = None,
    require_as_of: bool | None = None,
    jump_threshold: float = 0.5,
) -> AdjustmentQualityResult:
    """CR017 复权 quality gate；只消费调用方传入的 fixture metadata。"""

    payload = _cr017_payload(metadata)
    view_id = str(payload.get("view_id") or "")
    source_run_id = str(payload.get("source_run_id") or "")
    lineage_checksum = str(payload.get("lineage_checksum") or "")
    required = ["view_id", "source_run_id", "lineage_checksum", "quality_status"]
    required.extend(str(item) for item in (required_fields or ()))
    if view_id == "adj_factor":
        required.append("provider_factor_direction")
    if require_as_of is True or (
        require_as_of is None and view_id == "prices_qfq"
    ):
        required.append("as_of_trade_date")
    missing = _cr017_missing_fields(payload, tuple(dict.fromkeys(required)))
    if missing:
        if "as_of_trade_date" in missing:
            return _adjustment_quality_result(
                status=ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING,
                reason_code=CR017_MISSING_AS_OF_TRADE_DATE,
                reason_detail=CR017_MISSING_AS_OF_TRADE_DATE,
                view_id=view_id,
                source_run_id=source_run_id,
                lineage_checksum=lineage_checksum,
                missing_fields=missing,
            )
        detail = _required_missing_detail(missing)
        return _adjustment_quality_result(
            status=ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING,
            reason_code=CR017_REASON_REQUIRED_MISSING,
            reason_detail=detail,
            view_id=view_id,
            source_run_id=source_run_id,
            lineage_checksum=lineage_checksum,
            missing_fields=missing,
        )

    quality_status = str(payload.get("quality_status") or "")
    if quality_status == QUALITY_STATUS_WARN:
        return _adjustment_quality_result(
            status=ADJUSTMENT_GATE_STATUS_WARN,
            reason_code=CR017_WARNING_NOT_PRODUCTION_PASS,
            reason_detail=CR017_WARNING_NOT_PRODUCTION_PASS,
            view_id=view_id,
            source_run_id=source_run_id,
            lineage_checksum=lineage_checksum,
            warnings=(CR017_WARNING_NOT_PRODUCTION_PASS,),
        )
    if quality_status in {QUALITY_STATUS_FAIL, QUALITY_STATUS_MISSING}:
        return _adjustment_quality_result(
            status=ADJUSTMENT_GATE_STATUS_FAIL,
            reason_code=CR017_QUALITY_FAILED,
            reason_detail=quality_status,
            view_id=view_id,
            source_run_id=source_run_id,
            lineage_checksum=lineage_checksum,
        )

    jump_check = check_unexplained_adjustment_jump(payload, threshold=jump_threshold)
    if not jump_check.passed:
        return _adjustment_quality_result(
            status=ADJUSTMENT_GATE_STATUS_FAIL,
            reason_code=CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
            reason_detail=CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
            view_id=view_id,
            source_run_id=source_run_id,
            lineage_checksum=lineage_checksum,
            issues=(jump_check.to_dict(),),
        )

    return AdjustmentQualityResult(
        status=ADJUSTMENT_GATE_STATUS_PASS,
        passed=True,
        production_pass=True,
        view_id=view_id,
        source_run_id=source_run_id,
        lineage_checksum=lineage_checksum,
    )


def check_adjustment_parity(
    actual: Any,
    expected: Any,
    *,
    value_fields: Sequence[str] | None = None,
    key_fields: Sequence[str] = ("trade_date", "symbol"),
    tolerance: float = 1e-9,
    view_id: str | None = None,
    require_as_of: bool | None = None,
) -> ParityCheckResult:
    """比较 fixture actual / expected 行，输出结构化 parity 失败原因。"""

    actual_rows = _cr017_rows(actual)
    expected_rows = _cr017_rows(expected)
    actual_view_id = str(view_id or _first_row_value(actual_rows, "view_id") or "")
    if not actual_rows or not expected_rows:
        return _parity_failure(
            CR017_REASON_REQUIRED_MISSING,
            {
                "code": CR017_REASON_REQUIRED_MISSING,
                "actual_rows": len(actual_rows),
                "expected_rows": len(expected_rows),
            },
            actual_view_id,
            actual_rows,
            expected_rows,
        )

    policies = _policy_values(actual_rows)
    if len(policies) > 1:
        return _parity_failure(
            CR017_MIXED_ADJUSTMENT_POLICY,
            {"code": CR017_MIXED_ADJUSTMENT_POLICY, "policies_seen": list(policies)},
            actual_view_id,
            actual_rows,
            expected_rows,
        )

    asof_required = require_as_of is True or (
        require_as_of is None and actual_view_id == "prices_qfq"
    )
    if asof_required:
        missing_asof = [
            _row_key(row, key_fields)
            for row in actual_rows
            if _cr017_is_missing(row.get("as_of_trade_date"))
        ]
        if missing_asof:
            return _parity_failure(
                CR017_MISSING_AS_OF_TRADE_DATE,
                {
                    "code": CR017_MISSING_AS_OF_TRADE_DATE,
                    "missing_keys": [list(item) for item in missing_asof],
                    "field": "as_of_trade_date",
                },
                actual_view_id,
                actual_rows,
                expected_rows,
            )

    fields = tuple(value_fields or _common_parity_fields(actual_rows, expected_rows))
    if not fields:
        return _parity_failure(
            CR017_REASON_REQUIRED_MISSING,
            {"code": CR017_REASON_REQUIRED_MISSING, "missing_fields": ["value_fields"]},
            actual_view_id,
            actual_rows,
            expected_rows,
        )

    actual_index = {_row_key(row, key_fields): row for row in actual_rows}
    expected_index = {_row_key(row, key_fields): row for row in expected_rows}
    mismatches: list[dict[str, Any]] = []
    for key in sorted(set(actual_index) | set(expected_index)):
        actual_row = actual_index.get(key)
        expected_row = expected_index.get(key)
        if actual_row is None or expected_row is None:
            mismatches.append(
                {
                    "code": CR017_PARITY_MISMATCH,
                    "key": list(key),
                    "field": "__row__",
                    "expected": "present" if expected_row is not None else "missing",
                    "actual": "present" if actual_row is not None else "missing",
                }
            )
            continue
        for field_name in fields:
            if not _parity_values_match(
                actual_row.get(field_name),
                expected_row.get(field_name),
                tolerance,
            ):
                mismatches.append(
                    {
                        "code": CR017_PARITY_MISMATCH,
                        "key": list(key),
                        "field": field_name,
                        "expected": expected_row.get(field_name),
                        "actual": actual_row.get(field_name),
                    }
                )
    if mismatches:
        return _parity_failure(
            CR017_PARITY_MISMATCH,
            dict(mismatches[0]),
            actual_view_id,
            actual_rows,
            expected_rows,
            tuple(mismatches),
        )

    return ParityCheckResult(
        status=ADJUSTMENT_GATE_STATUS_PASS,
        passed=True,
        view_id=actual_view_id,
        expected_count=len(expected_rows),
        actual_count=len(actual_rows),
    )


def guard_execution_price_leakage(intent_or_metadata: Any) -> LeakageGuardResult:
    """阻断 qfq/hfq/returns_adjusted 进入 execution price 字段。"""

    payload = _cr017_payload(intent_or_metadata)
    policy = str(
        payload.get("execution_price_policy")
        or payload.get("price_policy")
        or payload.get("policy")
        or payload.get("research_adjustment_policy")
        or ""
    )
    view_id = str(
        payload.get("execution_price_view_id")
        or payload.get("price_source_view_id")
        or payload.get("view_id")
        or ""
    )
    adjusted_field = _adjusted_execution_field(payload)
    if adjusted_field:
        return _leakage_blocked(policy, view_id, adjusted_field)
    if policy and policy != ADJUSTMENT_POLICY_RAW and _has_execution_price_field(payload):
        return _leakage_blocked(policy, view_id, "execution_price_policy")
    if view_id in _adjusted_view_ids() and _has_execution_price_field(payload):
        return _leakage_blocked(policy, view_id, "view_id")
    ref_field = _adjusted_price_ref_field(payload)
    if ref_field:
        return _leakage_blocked(policy, view_id, ref_field)
    return LeakageGuardResult(
        status=ADJUSTMENT_GATE_STATUS_PASS,
        passed=True,
        policy=policy or ADJUSTMENT_POLICY_RAW,
        view_id=view_id,
    )


def build_ts017_matrix() -> dict[str, tuple[dict[str, str], ...]]:
    """返回 TS-017 稳定场景矩阵；每类至少一个正向和一个失败场景。"""

    return {
        "TS-017-01": (
            {
                "scenario_id": "TS-017-01-PASS-quality-lineage",
                "kind": "positive",
                "interface": "adjustment_quality_gate",
                "expected_reason_code": "",
            },
            {
                "scenario_id": "TS-017-01-FAIL-required-missing-direction",
                "kind": "failure",
                "interface": "adjustment_quality_gate",
                "expected_reason_code": CR017_REASON_REQUIRED_MISSING,
            },
            {
                "scenario_id": "TS-017-01-FAIL-unexplained-adjustment-jump",
                "kind": "failure",
                "interface": "adjustment_quality_gate",
                "expected_reason_code": CR017_UNEXPLAINED_ADJUSTMENT_JUMP,
            },
        ),
        "TS-017-02": (
            {
                "scenario_id": "TS-017-02-PASS-qfq-asof-parity",
                "kind": "positive",
                "interface": "check_adjustment_parity",
                "expected_reason_code": "",
            },
            {
                "scenario_id": "TS-017-02-FAIL-missing-as-of",
                "kind": "failure",
                "interface": "check_adjustment_parity",
                "expected_reason_code": CR017_MISSING_AS_OF_TRADE_DATE,
            },
            {
                "scenario_id": "TS-017-02-FAIL-parity-mismatch",
                "kind": "failure",
                "interface": "check_adjustment_parity",
                "expected_reason_code": CR017_PARITY_MISMATCH,
            },
        ),
        "TS-017-03": (
            {
                "scenario_id": "TS-017-03-PASS-raw-execution-price",
                "kind": "positive",
                "interface": "guard_execution_price_leakage",
                "expected_reason_code": "",
            },
            {
                "scenario_id": "TS-017-03-FAIL-execution-requires-raw",
                "kind": "failure",
                "interface": "guard_execution_price_leakage",
                "expected_reason_code": CR017_EXECUTION_REQUIRES_RAW,
            },
            {
                "scenario_id": "TS-017-03-FAIL-mixed-adjustment-policy",
                "kind": "failure",
                "interface": "check_adjustment_parity",
                "expected_reason_code": CR017_MIXED_ADJUSTMENT_POLICY,
            },
        ),
    }


def _adjustment_quality_result(
    *,
    status: str,
    reason_code: str,
    reason_detail: str,
    view_id: str,
    source_run_id: str,
    lineage_checksum: str,
    missing_fields: tuple[str, ...] = (),
    issues: tuple[dict[str, Any], ...] = (),
    warnings: tuple[str, ...] = (),
) -> AdjustmentQualityResult:
    issue_list = list(issues)
    if reason_code:
        issue_list.insert(
            0,
            {
                "code": reason_code,
                "detail": reason_detail,
                "view_id": view_id,
                "missing_fields": list(missing_fields),
            },
        )
    return AdjustmentQualityResult(
        status=status,
        passed=False,
        production_pass=False,
        reason_code=reason_code,
        reason_detail=reason_detail,
        view_id=view_id,
        source_run_id=source_run_id,
        lineage_checksum=lineage_checksum,
        missing_fields=missing_fields,
        issues=tuple(issue_list),
        warnings=warnings,
    )


def _parity_failure(
    reason_code: str,
    mismatch_reason: dict[str, Any],
    view_id: str,
    actual_rows: Sequence[Mapping[str, Any]],
    expected_rows: Sequence[Mapping[str, Any]],
    mismatches: tuple[dict[str, Any], ...] = (),
) -> ParityCheckResult:
    return ParityCheckResult(
        status=(
            ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING
            if reason_code in {CR017_REASON_REQUIRED_MISSING, CR017_MISSING_AS_OF_TRADE_DATE}
            else ADJUSTMENT_GATE_STATUS_FAIL
        ),
        passed=False,
        reason_code=reason_code,
        mismatch_reason=dict(mismatch_reason),
        view_id=view_id,
        expected_count=len(expected_rows),
        actual_count=len(actual_rows),
        mismatches=mismatches or (dict(mismatch_reason),),
    )


def _leakage_blocked(policy: str, view_id: str, field_name: str) -> LeakageGuardResult:
    return LeakageGuardResult(
        status=ADJUSTMENT_LEAKAGE_STATUS_BLOCKED,
        passed=False,
        reason_code=CR017_EXECUTION_REQUIRES_RAW,
        blocked_reason=CR017_EXECUTION_REQUIRES_RAW,
        field_name=field_name,
        policy=policy,
        view_id=view_id,
    )


def _cr017_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, pd.DataFrame):
        payload = dict(value.attrs)
        if not value.empty:
            payload.update(value.iloc[0].to_dict())
        return payload
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            if isinstance(item, Mapping):
                return dict(item)
        return {}
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _cr017_rows(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return [dict(item) for item in value.to_dict("records")]
    if isinstance(value, Mapping):
        rows = value.get("rows")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
            return [dict(item) for item in rows if isinstance(item, Mapping)]
        return [dict(value)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _cr017_rows(to_dict())
    rows_attr = getattr(value, "rows", None)
    if rows_attr is not None:
        return _cr017_rows(rows_attr)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _cr017_missing_fields(payload: Mapping[str, Any], required: Sequence[str]) -> tuple[str, ...]:
    return tuple(field_name for field_name in required if _cr017_is_missing(payload.get(field_name)))


def _required_missing_detail(missing_fields: Sequence[str]) -> str:
    missing = set(missing_fields)
    if "provider_factor_direction" in missing:
        return CR017_MISSING_FACTOR_DIRECTION
    if {"source_run_id", "lineage_checksum"} & missing:
        return CR017_MISSING_LINEAGE
    return CR017_REASON_REQUIRED_MISSING


def _policy_values(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    values = {
        str(row.get("research_adjustment_policy") or row.get("adjustment_policy") or row.get("policy") or "").strip()
        for row in rows
    }
    return tuple(sorted(item for item in values if item))


def _first_row_value(rows: Sequence[Mapping[str, Any]], field_name: str) -> str:
    for row in rows:
        value = str(row.get(field_name) or "").strip()
        if value:
            return value
    return ""


def _common_parity_fields(
    actual_rows: Sequence[Mapping[str, Any]],
    expected_rows: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    actual_fields = set().union(*(set(row.keys()) for row in actual_rows))
    expected_fields = set().union(*(set(row.keys()) for row in expected_rows))
    preferred = (
        "adjusted_open",
        "adjusted_high",
        "adjusted_low",
        "adjusted_close",
        "adjusted_return",
        "open",
        "high",
        "low",
        "close",
    )
    return tuple(field for field in preferred if field in actual_fields and field in expected_fields)


def _row_key(row: Mapping[str, Any], key_fields: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(row.get(field_name) or "") for field_name in key_fields)


def _parity_values_match(actual: Any, expected: Any, tolerance: float) -> bool:
    actual_float = _cr017_to_float(actual)
    expected_float = _cr017_to_float(expected)
    if actual_float is not None and expected_float is not None:
        return abs(actual_float - expected_float) <= tolerance
    return actual == expected


def _adjusted_execution_field(payload: Mapping[str, Any]) -> str:
    for field_name in (
        "adjusted_execution_price",
        "adjusted_order_price",
        "adjusted_limit_price",
        "adjusted_price",
    ):
        if field_name in payload and not _cr017_is_missing(payload.get(field_name)):
            return field_name
    field_name = str(payload.get("field_name") or payload.get("execution_field") or "")
    if field_name.startswith("adjusted_") or field_name in {
        "execution_price",
        "order_price",
        "limit_price",
    }:
        policy = str(payload.get("policy") or payload.get("research_adjustment_policy") or "")
        if policy in _adjusted_policies():
            return field_name
    return ""


def _has_execution_price_field(payload: Mapping[str, Any]) -> bool:
    return any(
        field_name in payload and not _cr017_is_missing(payload.get(field_name))
        for field_name in (
            "execution_price",
            "order_price",
            "limit_price",
            "target_price",
            "price",
            "execution_price_policy",
        )
    )


def _adjusted_price_ref_field(payload: Mapping[str, Any]) -> str:
    for field_name in ("execution_price_ref", "price_ref", "source_ref"):
        value = str(payload.get(field_name) or "")
        if any(value.startswith(f"{view_id}:") for view_id in _adjusted_view_ids()):
            return field_name
    return ""


def _adjusted_policies() -> set[str]:
    return {
        ADJUSTMENT_POLICY_QFQ,
        ADJUSTMENT_POLICY_HFQ,
        ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
    }


def _adjusted_view_ids() -> set[str]:
    return {"prices_qfq", "prices_hfq", "returns_adjusted"}


def _cr017_is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _cr017_to_float(value: Any) -> float | None:
    if _cr017_is_missing(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def validate_p0_candidate(
    candidate: Any,
    lifecycle: Mapping[str, Any] | None = None,
    thresholds: Mapping[str, Any] | None = None,
) -> P0ValidationResult:
    """校验 P0 candidate；PASS 也不触发 publish。"""

    del thresholds
    payload = _contract_payload(candidate)
    lifecycle_payload = dict(lifecycle or {})
    dataset = str(payload.get("dataset") or lifecycle_payload.get("dataset") or "")
    quality_status = str(payload.get("quality_status") or QUALITY_STATUS_PASS)
    readiness_status = str(payload.get("readiness_status") or READINESS_STATUS_AVAILABLE)
    error_codes: list[str] = []
    details: list[dict[str, Any]] = [
        {
            "code": VALIDATE_DOES_NOT_PUBLISH,
            "unblock_condition": "call_explicit_publish_gate_with_publish_intent",
        }
    ]
    if not payload:
        error_codes.append(P0_CANDIDATE_REQUIRED)
        details.append(
            {
                "code": P0_CANDIDATE_REQUIRED,
                "unblock_condition": "provide_normalize_or_replay_candidate",
            }
        )
    if payload.get("status") == "blocked":
        error_codes.extend(str(code) for code in payload.get("error_codes", ()))
        details.extend(
            dict(item) for item in payload.get("details", ()) if isinstance(item, Mapping)
        )
    passed = not error_codes and quality_status == QUALITY_STATUS_PASS
    return P0ValidationResult(
        dataset=dataset,
        quality_status=quality_status,
        readiness_status=readiness_status,
        passed=passed,
        candidate_unpublished=True,
        publish_count=0,
        current_pointer_changes=0,
        provider_fetches=0,
        lake_writes=0,
        credential_reads=0,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
    )


def publish_p0_candidate(
    candidate: Any,
    validation: P0ValidationResult | Mapping[str, Any],
    publish_intent: Any = None,
    *,
    manifest: Any = None,
    lifecycle: Mapping[str, Any] | None = None,
    dry_run: bool = True,
) -> Any:
    """委托 S02 Explicit Publish Gate；未授权时 pointer changes 为 0。"""

    from .publish import PublishIntent, publish_current_pointer

    if isinstance(publish_intent, PublishIntent):
        intent = publish_intent
    elif isinstance(publish_intent, Mapping):
        intent = PublishIntent(
            publish=bool(publish_intent.get("publish")),
            approval_token=publish_intent.get("approval_token"),
            approved_by=publish_intent.get("approved_by"),
            reason=publish_intent.get("reason"),
        )
    else:
        intent = PublishIntent(publish=False)
    validation_payload = (
        validation.to_dict() if isinstance(validation, P0ValidationResult) else dict(validation)
    )
    quality = {
        "quality_status": validation_payload.get("quality_status"),
        "readiness_status": validation_payload.get("readiness_status"),
    }
    return publish_current_pointer(
        store=None,
        candidate=candidate,
        intent=intent,
        dry_run=dry_run,
        quality=quality,
        manifest=manifest,
        lifecycle=lifecycle,
    )


def read_p0_current_truth(
    dataset: str,
    catalog_pointer: Any = None,
    *,
    read_scope: str = "published_current_truth",
    candidate_audit_evidence: Mapping[str, Any] | None = None,
) -> ReadQueryContract:
    """read/query 只读 published pointer 或受控 candidate audit evidence。"""

    if read_scope == "published_current_truth":
        from .catalog import validate_catalog_pointer

        pointer_payload = _contract_payload(catalog_pointer)
        if not pointer_payload:
            return ReadQueryContract(
                dataset=dataset,
                read_scope=read_scope,
                allowed=False,
                source_of_truth="catalog_current_pointer",
                current_truth_visible=False,
                error_codes=(P0_CURRENT_POINTER_REQUIRED,),
                details=(
                    {
                        "code": P0_CURRENT_POINTER_REQUIRED,
                        "unblock_condition": "publish_candidate_through_explicit_publish_gate",
                    },
                ),
            )
        validation = validate_catalog_pointer(pointer_payload)
        return ReadQueryContract(
            dataset=dataset,
            read_scope=read_scope,
            allowed=validation.passed,
            source_of_truth="catalog_current_pointer",
            current_truth_visible=validation.current_truth_visible,
            error_codes=validation.error_codes,
            details=validation.details,
        )
    if read_scope == "candidate_audit":
        if not candidate_audit_evidence:
            return ReadQueryContract(
                dataset=dataset,
                read_scope=read_scope,
                allowed=False,
                source_of_truth="candidate_audit_evidence",
                current_truth_visible=False,
                error_codes=(P0_CANDIDATE_AUDIT_REQUIRED,),
                details=(
                    {
                        "code": P0_CANDIDATE_AUDIT_REQUIRED,
                        "unblock_condition": "provide_controlled_candidate_audit_evidence",
                    },
                ),
            )
        return ReadQueryContract(
            dataset=dataset,
            read_scope=read_scope,
            allowed=True,
            source_of_truth="candidate_audit_evidence",
            current_truth_visible=False,
            details=(
                {
                    "code": P0_CANDIDATE_UNPUBLISHED,
                    "note": "candidate audit evidence is not current truth",
                },
            ),
        )
    return ReadQueryContract(
        dataset=dataset,
        read_scope=read_scope,
        allowed=False,
        source_of_truth="none",
        current_truth_visible=False,
        error_codes=(P0_READ_SCOPE_INVALID,),
        details=(
            {
                "code": P0_READ_SCOPE_INVALID,
                "allowed": ["published_current_truth", "candidate_audit"],
            },
        ),
    )


Clock = Callable[[], datetime]


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(clock: Clock | None) -> str:
    value = (clock or _now)()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _config_hash(value: Mapping[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _discover_parquet(layout: LakeLayout, dataset: str) -> list[Path]:
    root = layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _read_canonical(paths: Sequence[Path]) -> pd.DataFrame:
    frames = [pd.read_parquet(path) for path in paths]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _date_values(start: str, end: str, open_trade_dates: Sequence[str] | None) -> list[str]:
    if open_trade_dates is not None:
        return [str(item) for item in open_trade_dates]
    values = pd.date_range(start=start, end=end, freq="D")
    return [item.date().isoformat() for item in values]


def _context_records(validation_context: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = validation_context.get("manifest_records", [])
    if isinstance(records, list):
        return [item for item in records if isinstance(item, Mapping)]
    return []


def _first_record(records: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return records[0] if records else {}


def _lineage_value(frame: pd.DataFrame, column: str, fallback: object = "") -> str:
    if column in frame.columns and not frame.empty:
        values = [str(item) for item in frame[column].dropna().unique() if str(item)]
        if values:
            return values[0]
    return str(fallback or "")


def _date_range_values(start: str, end: str) -> list[str]:
    return [item.date().isoformat() for item in pd.date_range(start=start, end=end, freq="D")]


def _expected_pair_set(validation_context: Mapping[str, Any]) -> set[tuple[str, str]]:
    pairs = validation_context.get("expected_pairs", [])
    result: set[tuple[str, str]] = set()
    for item in pairs:
        if isinstance(item, Mapping):
            date_value = item.get("trade_date")
            symbol_value = item.get("symbol")
        else:
            try:
                date_value, symbol_value = item
            except (TypeError, ValueError):
                continue
        if date_value not in (None, "") and symbol_value not in (None, ""):
            result.add((str(date_value), str(symbol_value)))
    return result


def build_prices_coverage_gate(
    *,
    start_date: str,
    end_date: str,
    symbols_count: int,
    date_slices: Sequence[Mapping[str, Any]],
    open_trade_dates: Sequence[str] | None = None,
    minimum_coverage_ratio: float = 1.0,
    quality_status_required: str = QUALITY_STATUS_PASS,
) -> dict[str, Any]:
    if symbols_count < 0:
        raise QualityValidationError("symbols_count 不能小于 0")
    if open_trade_dates is None:
        calendar_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
        denominator = max(0, calendar_days) * symbols_count
        denominator_mode = DENOMINATOR_MODE_TRADE_CALENDAR_REQUIRED
        denominator_status = "trade_calendar_required"
        open_dates_count = None
    else:
        open_dates = [str(item) for item in open_trade_dates]
        denominator = len(open_dates) * symbols_count
        denominator_mode = DENOMINATOR_MODE_PRICES
        denominator_status = "ready"
        open_dates_count = len(open_dates)
    return {
        "dataset": DATASET_PRICES,
        "requested_start": start_date,
        "requested_end": end_date,
        "symbols_count": symbols_count,
        "date_slice_count": len(list(date_slices)),
        "denominator_mode": denominator_mode,
        "coverage_denominator_status": denominator_status,
        "open_trade_dates_count": open_dates_count,
        "expected_rows": denominator,
        "minimum_coverage_ratio": minimum_coverage_ratio,
        "quality_status_required": quality_status_required,
        "coverage_pass_claimed": False,
        "requires_trade_calendar": open_trade_dates is None,
        "old_data_operations": {
            "read": 0,
            "list": 0,
            "migrate": 0,
            "copy": 0,
            "compare": 0,
            "delete": 0,
        },
    }


def _generic_dataset_quality(
    dataset: str,
    lake_root: str | Path,
    expected_range: tuple[str, str],
    expected_keys: Sequence[str] | None,
    thresholds: QualityThresholds,
    validation_context: Mapping[str, Any],
    *,
    required: bool,
    clock: Clock | None,
) -> QualityResult:
    if dataset not in DATASET_SCHEMA_REGISTRY:
        raise QualityValidationError(f"未知 dataset: {dataset}")
    layout = LakeLayout(lake_root)
    paths = validation_context.get("canonical_paths") or _discover_parquet(layout, dataset)
    paths = [Path(path) for path in paths]
    frame = _read_canonical(paths)
    exchange = validation_context.get("exchange")
    if exchange and "exchange" in frame.columns:
        frame = frame[frame["exchange"].astype(str).str.upper() == str(exchange).upper()]
    index_code = validation_context.get("index_code")
    if index_code and "index_code" in frame.columns:
        frame = frame[frame["index_code"].astype(str).str.upper() == str(index_code).upper()]
    registry = DATASET_SCHEMA_REGISTRY[dataset]
    required_columns = tuple(registry.get("columns", ()))
    key_columns = tuple(registry.get("key_columns", DATASET_KEY_COLUMNS.get(dataset, ())))
    missing_fields = [column for column in required_columns if column not in frame.columns]

    duplicated = pd.DataFrame()
    duplicate_keys: list[dict[str, Any]] = []
    if key_columns and all(column in frame.columns for column in key_columns):
        duplicated = frame[frame.duplicated(list(key_columns), keep=False)]
        duplicate_keys = duplicated[list(key_columns)].drop_duplicates().to_dict("records")

    expected_dates = [str(item) for item in validation_context.get("expected_dates", [])]
    if not expected_dates:
        expected_dates = _date_range_values(expected_range[0], expected_range[1])
    date_column = "trade_date" if "trade_date" in required_columns or "trade_date" in frame.columns else ""
    if dataset == DATASET_EVENTS and "event_date" in frame.columns:
        date_column = "event_date"
    actual_dates = set(frame[date_column].astype(str)) if date_column and date_column in frame.columns else set()
    missing_dates = [date for date in expected_dates if date not in actual_dates]
    expected_symbol_count = (
        len([str(item) for item in expected_keys])
        if expected_keys
        else int(validation_context.get("expected_symbols_count", 0) or 0)
    )
    actual_count = int(len(frame))
    expected_pairs = _expected_pair_set(validation_context)
    if expected_pairs and {"trade_date", "symbol"}.issubset(frame.columns):
        actual_pairs = {
            (str(row.trade_date), str(row.symbol))
            for row in frame[["trade_date", "symbol"]].itertuples(index=False)
        }
        expected_count = len(expected_pairs)
        missing_rows_count = len(expected_pairs - actual_pairs)
        coverage_numerator = len(expected_pairs & actual_pairs)
        missing_dates = sorted({date for date, _symbol in expected_pairs - actual_pairs})
    else:
        expected_count = len(expected_dates)
        if expected_symbol_count:
            expected_count *= expected_symbol_count
        missing_rows_count = max(0, expected_count - actual_count)
        coverage_numerator = actual_count
    if dataset == DATASET_EVENTS:
        expected_dates = []
        missing_dates = []
        expected_count = actual_count
        missing_rows_count = 0
        coverage_numerator = actual_count
    coverage_denominator = expected_count
    coverage_ratio = (coverage_numerator / coverage_denominator) if coverage_denominator else 0.0

    issue_codes: list[str] = []
    if missing_fields:
        issue_codes.append("schema_mismatch")
    if duplicate_keys:
        issue_codes.append("duplicate_key")
    lineage_fields = ("source", "source_interface", "source_run_id", "lineage_raw_checksum")
    missing_lineage = [
        column
        for column in lineage_fields
        if column in required_columns and (column not in frame.columns or frame[column].isna().any() or (frame[column].astype(str) == "").any())
    ]
    if missing_lineage:
        issue_codes.append("lineage_unavailable")
    w3_required = tuple(registry.get("w3_required", ()))
    missing_w3_required = [
        column
        for column in w3_required
        if column not in frame.columns
        or frame[column].isna().any()
        or (frame[column].astype(str) == "").any()
    ]
    if missing_w3_required:
        issue_codes.append("available_at_missing" if "available_at" in missing_w3_required else "w3_required_missing")
    if (
        dataset in {DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS}
        and "source_interface" in frame.columns
    ):
        interfaces = {
            str(item).strip().upper()
            for item in frame["source_interface"].dropna().unique()
            if str(item).strip()
        }
        if interfaces & {"UNKNOWN", "UNRESOLVED"}:
            issue_codes.append("w3_source_unresolved")
    if coverage_denominator == 0 and dataset != DATASET_EVENTS:
        issue_codes.append("coverage_denominator_zero")
    elif dataset != DATASET_EVENTS and coverage_ratio < thresholds.coverage_threshold:
        issue_codes.append("coverage_gap")
    pit_fields = tuple(registry.get("pit_fields", DATASET_PIT_FIELDS.get(dataset, ())))
    pit_status = PIT_STATUS_NOT_APPLICABLE
    readiness_status = READINESS_STATUS_AVAILABLE
    is_pit_universe = bool(validation_context.get("is_pit_universe", False))
    if pit_fields:
        missing_pit_fields = [
            column
            for column in pit_fields
            if column not in frame.columns
            or frame[column].isna().any()
            or (frame[column].astype(str) == "").any()
        ]
        if missing_pit_fields:
            issue_codes.append("pit_incomplete")
            pit_status = PIT_STATUS_INCOMPLETE
            readiness_status = READINESS_STATUS_PIT_INCOMPLETE
        elif not frame.empty:
            if "pit_status" in frame.columns:
                pit_values = {
                    str(item)
                    for item in frame["pit_status"].dropna().unique()
                    if str(item)
                }
                if PIT_STATUS_FAILED in pit_values:
                    issue_codes.append("pit_failed")
                    pit_status = PIT_STATUS_FAILED
                    readiness_status = READINESS_STATUS_QUALITY_FAILED
                elif PIT_STATUS_INCOMPLETE in pit_values:
                    issue_codes.append("pit_incomplete")
                    pit_status = PIT_STATUS_INCOMPLETE
                    readiness_status = READINESS_STATUS_PIT_INCOMPLETE
                elif PIT_STATUS_NON_PIT_SNAPSHOT in pit_values:
                    issue_codes.append("non_pit_snapshot")
                    pit_status = PIT_STATUS_NON_PIT_SNAPSHOT
                    readiness_status = READINESS_STATUS_NON_PIT_SNAPSHOT
                elif PIT_STATUS_AVAILABLE in pit_values:
                    pit_status = PIT_STATUS_AVAILABLE
            else:
                pit_status = PIT_STATUS_AVAILABLE
            if "is_pit_universe" in frame.columns and not frame.empty:
                is_pit_universe = bool(frame["is_pit_universe"].astype(bool).all())
            if dataset == DATASET_INDEX_MEMBERS and pit_status == PIT_STATUS_AVAILABLE and not is_pit_universe:
                issue_codes.append("pit_incomplete")
                pit_status = PIT_STATUS_INCOMPLETE
                readiness_status = READINESS_STATUS_PIT_INCOMPLETE
            decision_time = validation_context.get("decision_time")
            if decision_time is not None and "available_at" in frame.columns:
                available = pd.to_datetime(frame["available_at"], utc=True, errors="coerce")
                decision = pd.to_datetime(pd.Series([decision_time] * len(frame)), utc=True, errors="coerce")
                if available.isna().any() or decision.isna().any():
                    issue_codes.append("pit_failed")
                    pit_status = PIT_STATUS_FAILED
                    readiness_status = READINESS_STATUS_QUALITY_FAILED
                elif bool((available > decision).any()):
                    issue_codes.append("future_availability")
                    pit_status = PIT_STATUS_FAILED
                    readiness_status = READINESS_STATUS_QUALITY_FAILED
        else:
            pit_status = PIT_STATUS_INCOMPLETE
            readiness_status = READINESS_STATUS_PIT_INCOMPLETE

    hard_fail = bool(
        {
            "schema_mismatch",
            "duplicate_key",
            "lineage_unavailable",
            "coverage_denominator_zero",
            "available_at_missing",
            "w3_required_missing",
            "w3_source_unresolved",
            "pit_failed",
            "future_availability",
        }
        & set(issue_codes)
    )
    if hard_fail or "coverage_gap" in issue_codes:
        quality_status = QUALITY_STATUS_FAIL
        if "schema_mismatch" in issue_codes:
            readiness_status = READINESS_STATUS_SCHEMA_MISMATCH
        elif readiness_status == READINESS_STATUS_AVAILABLE:
            readiness_status = READINESS_STATUS_QUALITY_FAILED
    elif {"pit_incomplete", "non_pit_snapshot"} & set(issue_codes):
        quality_status = QUALITY_STATUS_WARN
    else:
        quality_status = QUALITY_STATUS_PASS
    dataset_status = "available"
    if quality_status == QUALITY_STATUS_FAIL:
        dataset_status = "required_missing" if required and actual_count == 0 else "quality_failed"
        if duplicate_keys:
            dataset_status = "duplicate_key"
        elif missing_fields:
            dataset_status = "schema_mismatch"
    elif quality_status == QUALITY_STATUS_WARN:
        dataset_status = "warn"
    records = _context_records(validation_context)
    first_record = _first_record(records)
    coverage = CoverageSummary(
        requested_start=str(expected_range[0]),
        requested_end=str(expected_range[1]),
        actual_start=None if frame.empty or not date_column else str(frame[date_column].min()),
        actual_end=None if frame.empty or not date_column else str(frame[date_column].max()),
        requested_symbols_count=expected_symbol_count,
        actual_symbols_count=(
            0
            if frame.empty
            else int(frame["symbol"].nunique())
            if "symbol" in frame.columns
            else int(frame["con_code"].nunique())
            if "con_code" in frame.columns
            else 0
        ),
        open_trade_dates_count=len(expected_dates),
        expected_rows=coverage_denominator,
        actual_rows=actual_count,
        missing_rows=missing_rows_count,
        missing_rate=(missing_rows_count / coverage_denominator)
        if coverage_denominator
        else (0.0 if dataset == DATASET_EVENTS else 1.0),
    )
    source = _lineage_value(frame, "source", first_record.get("source", validation_context.get("source_name", "unknown")))
    interface = _lineage_value(
        frame,
        "source_interface",
        first_record.get("interface", validation_context.get("source_interface", "unknown")),
    )
    run_id = _lineage_value(frame, "source_run_id", first_record.get("run_id", validation_context.get("run_id", "unknown")))
    checksum = _lineage_value(frame, "lineage_raw_checksum", first_record.get("raw_checksum", ""))
    config_for_hash = {
        "dataset": dataset,
        "expected_range": list(expected_range),
        "thresholds": asdict(thresholds),
        "source": source,
        "interface": interface,
    }
    return QualityResult(
        run_id=run_id,
        generated_at=_iso(clock),
        dataset=dataset,
        source_name=source,
        source_interface=interface,
        target_dataset=dataset,
        input_config_hash=_config_hash(config_for_hash),
        quality_status=quality_status,
        fetch_status=str(first_record.get("status", validation_context.get("fetch_status", "not_applicable"))),
        dataset_status=dataset_status,
        coverage=coverage,
        denominator_mode=str(
            validation_context.get(
                "denominator_mode",
                DENOMINATOR_MODE_TRADE_CALENDAR
                if dataset == DATASET_TRADE_CALENDAR
                else DENOMINATOR_MODE_PRICES,
            )
        ),
        thresholds=thresholds,
        issue_count=len(issue_codes),
        missing_required_fields=missing_fields,
        duplicate_keys=duplicate_keys,
        coverage_gaps=[{"missing_dates": missing_dates}] if missing_dates else [],
        warnings=[
            code
            for code in ("pit_incomplete", "non_pit_snapshot")
            if code in issue_codes
        ],
        is_pit_universe=is_pit_universe,
        pit_status=pit_status,
        schema_version=SCHEMA_VERSION,
        coverage_threshold=thresholds.coverage_threshold,
        missing_dates=missing_dates,
        gap_reason="coverage_gap" if missing_dates else "",
        issue_codes=issue_codes,
        duplicate_key_count=len(duplicate_keys),
        source_run_id=run_id,
        manifest_run_id=str(first_record.get("run_id", run_id)),
        lineage_raw_checksum=checksum,
        unavailable_mapping="required_missing" if required else "unavailable",
        readiness_status=readiness_status,
    )


def validate_dataset(
    dataset: str,
    lake_root: str | Path,
    expected_range: tuple[str, str],
    expected_symbols: Sequence[str] | None = None,
    thresholds: QualityThresholds | None = None,
    validation_context: Mapping[str, Any] | None = None,
    *,
    required: bool = False,
    clock: Clock | None = None,
) -> QualityResult:
    if dataset != DATASET_PRICES:
        return _generic_dataset_quality(
            dataset,
            lake_root,
            expected_range,
            expected_symbols,
            thresholds or QualityThresholds(),
            dict(validation_context or {}),
            required=required,
            clock=clock,
        )
    thresholds = thresholds or QualityThresholds()
    validation_context = dict(validation_context or {})
    layout = LakeLayout(lake_root)
    paths = validation_context.get("canonical_paths") or _discover_parquet(layout, dataset)
    paths = [Path(path) for path in paths]
    frame = _read_canonical(paths)
    records = _context_records(validation_context)
    first_record = _first_record(records)

    missing_fields = [field for field in CANONICAL_PRICES_COLUMNS if field not in frame.columns]
    duplicate_keys: list[dict[str, Any]] = []
    negative_rows: list[dict[str, Any]] = []
    inconsistencies: list[dict[str, Any]] = []
    warnings: list[str] = []
    if {"trade_date", "symbol"} <= set(frame.columns):
        duplicated = frame[frame.duplicated(["trade_date", "symbol"], keep=False)]
        duplicate_keys = duplicated[["trade_date", "symbol"]].drop_duplicates().to_dict("records")
    if "close" in frame.columns:
        if not thresholds.allow_negative_price:
            negative_rows = frame[frame["close"].astype(float) < 0][
                ["trade_date", "symbol", "close"]
            ].to_dict("records")
    if first_record and {"source_run_id", "source"} <= set(frame.columns):
        run_id = str(first_record.get("run_id") or "")
        source = str(first_record.get("source") or "")
        if not frame.empty and set(frame["source_run_id"].astype(str)) - {run_id}:
            inconsistencies.append({"field": "source_run_id", "expected": run_id})
        if not frame.empty and set(frame["source"].astype(str)) - {source}:
            inconsistencies.append({"field": "source", "expected": source})
    if missing_fields:
        dataset_status = "fail"
    else:
        dataset_status = "pass"

    open_dates = _date_values(
        expected_range[0],
        expected_range[1],
        validation_context.get("open_trade_dates"),
    )
    expected_symbol_values = [str(item) for item in (expected_symbols or [])]
    expected_pairs = _expected_pair_set(validation_context)
    expected_rows = len(expected_pairs) if expected_pairs else len(open_dates) * len(expected_symbol_values)
    actual_rows = int(len(frame))
    if expected_pairs and {"trade_date", "symbol"}.issubset(frame.columns):
        actual_pairs = {
            (str(row.trade_date), str(row.symbol))
            for row in frame[["trade_date", "symbol"]].itertuples(index=False)
        }
        missing_rows = len(expected_pairs - actual_pairs)
    else:
        missing_rows = max(0, expected_rows - actual_rows)
    missing_rate = (missing_rows / expected_rows) if expected_rows else 0.0
    actual_start = None if frame.empty or "trade_date" not in frame else str(frame["trade_date"].min())
    actual_end = None if frame.empty or "trade_date" not in frame else str(frame["trade_date"].max())
    actual_symbols = 0 if frame.empty or "symbol" not in frame else int(frame["symbol"].nunique())
    coverage = CoverageSummary(
        requested_start=str(expected_range[0]),
        requested_end=str(expected_range[1]),
        actual_start=actual_start,
        actual_end=actual_end,
        requested_symbols_count=len(expected_symbol_values),
        actual_symbols_count=actual_symbols,
        open_trade_dates_count=len(open_dates),
        expected_rows=expected_rows,
        actual_rows=actual_rows,
        missing_rows=missing_rows,
        missing_rate=missing_rate,
    )
    coverage_gaps = []
    if missing_rows:
        coverage_gaps.append({"missing_rows": missing_rows, "missing_rate": missing_rate})
    if "open_trade_dates" not in validation_context:
        warnings.append("open_trade_dates 未显式传入，使用自然日范围计算 coverage")
    if not bool(validation_context.get("is_pit_universe", False)):
        warnings.append("warn_non_pit_universe")

    fail_issue_count = (
        len(missing_fields)
        + len(duplicate_keys)
        + len(negative_rows)
        + len(inconsistencies)
    )
    if missing_rate >= thresholds.prices_missing_rate_fail and missing_rows:
        fail_issue_count += 1
    warn_issue_count = len(warnings)
    if thresholds.prices_missing_rate_warn <= missing_rate < thresholds.prices_missing_rate_fail:
        warn_issue_count += 1
    if fail_issue_count:
        quality_status = "fail"
        dataset_status = "fail"
    elif warn_issue_count or missing_rate > thresholds.prices_missing_rate_pass:
        quality_status = "warn"
        dataset_status = "warn"
    else:
        quality_status = "pass"

    config_for_hash = {
        "dataset": dataset,
        "expected_range": list(expected_range),
        "expected_symbols": expected_symbol_values,
        "thresholds": asdict(thresholds),
        "denominator_mode": validation_context.get("denominator_mode", DENOMINATOR_MODE_PRICES),
        "target_dataset": dataset,
        "source": first_record.get("source", validation_context.get("source_name", "unknown")),
        "interface": first_record.get(
            "interface",
            validation_context.get("source_interface", "unknown"),
        ),
    }
    return QualityResult(
        run_id=str(first_record.get("run_id", validation_context.get("run_id", "unknown"))),
        generated_at=_iso(clock),
        dataset=dataset,
        source_name=str(first_record.get("source", validation_context.get("source_name", "unknown"))),
        source_interface=str(
            first_record.get("interface", validation_context.get("source_interface", "unknown"))
        ),
        target_dataset=dataset,
        input_config_hash=_config_hash(config_for_hash),
        quality_status=quality_status,
        fetch_status=str(first_record.get("status", validation_context.get("fetch_status", "unknown"))),
        dataset_status=dataset_status,
        coverage=coverage,
        denominator_mode=str(validation_context.get("denominator_mode", DENOMINATOR_MODE_PRICES)),
        thresholds=thresholds,
        issue_count=fail_issue_count + warn_issue_count,
        missing_required_fields=missing_fields,
        duplicate_keys=duplicate_keys,
        duplicate_key_count=len(duplicate_keys),
        negative_price_rows=negative_rows,
        coverage_gaps=coverage_gaps,
        manifest_inconsistencies=inconsistencies,
        warnings=warnings,
        coverage_threshold=1.0 - thresholds.prices_missing_rate_warn,
        missing_dates=[],
        gap_reason="coverage_gap" if coverage_gaps else "",
        issue_codes=[
            *(["schema_mismatch"] if missing_fields else []),
            *(["duplicate_key"] if duplicate_keys else []),
            *(["negative_price"] if negative_rows else []),
            *(["manifest_inconsistency"] if inconsistencies else []),
            *(["coverage_gap"] if coverage_gaps else []),
        ],
        source_run_id=str(first_record.get("run_id", validation_context.get("run_id", "unknown"))),
        manifest_run_id=str(first_record.get("run_id", validation_context.get("run_id", "unknown"))),
        lineage_raw_checksum=str(first_record.get("raw_checksum", "")),
        is_pit_universe=bool(validation_context.get("is_pit_universe", False)),
        universe_mode=str(validation_context.get("universe_mode", "non_pit_static")),
        pit_status=str(validation_context.get("pit_status", "non_pit_disclosed")),
    )


def _open_calendar_dates(trade_calendar: pd.DataFrame, start: str, end: str) -> list[str]:
    if "trade_date" not in trade_calendar.columns or "is_open" not in trade_calendar.columns:
        raise QualityValidationError("trade_calendar 缺少 trade_date/is_open")
    frame = trade_calendar.copy()
    frame["trade_date"] = frame["trade_date"].astype(str)
    open_frame = frame[
        (frame["trade_date"] >= str(start))
        & (frame["trade_date"] <= str(end))
        & (frame["is_open"].astype(bool))
    ]
    return sorted(open_frame["trade_date"].astype(str).unique().tolist())


def validate_hs300_index(
    lake_root: str | Path,
    index_code: str,
    expected_range: tuple[str, str],
    trade_calendar: pd.DataFrame,
    thresholds: QualityThresholds | None = None,
    *,
    required: bool = True,
    canonical_paths: Sequence[str | Path] | None = None,
    benchmark_policy_confirmed: bool = True,
    clock: Clock | None = None,
) -> QualityResult:
    thresholds = thresholds or QualityThresholds()
    layout = LakeLayout(lake_root)
    paths = [Path(path) for path in (canonical_paths or _discover_parquet(layout, DATASET_HS300_INDEX))]
    frame = _read_canonical(paths)
    open_dates = _open_calendar_dates(trade_calendar, expected_range[0], expected_range[1])
    if "index_code" in frame.columns:
        frame = frame[frame["index_code"].astype(str) == str(index_code)]
    required_columns = tuple(DATASET_SCHEMA_REGISTRY[DATASET_HS300_INDEX]["columns"])
    missing_fields = [column for column in required_columns if column not in frame.columns]
    duplicate_keys: list[dict[str, Any]] = []
    if {"trade_date", "index_code"} <= set(frame.columns):
        duplicated = frame[frame.duplicated(["trade_date", "index_code"], keep=False)]
        duplicate_keys = duplicated[["trade_date", "index_code"]].drop_duplicates().to_dict("records")
        actual_dates = set(frame["trade_date"].astype(str))
    else:
        actual_dates = set()
    missing_dates = [date for date in open_dates if date not in actual_dates]
    denominator = len(open_dates)
    numerator = denominator - len(missing_dates)
    ratio = (numerator / denominator) if denominator else 0.0
    issue_codes: list[str] = []
    if denominator == 0:
        issue_codes.append("calendar_missing")
    if missing_fields:
        issue_codes.append("schema_mismatch")
    if duplicate_keys:
        issue_codes.append("duplicate_key")
    lineage_missing = [
        column
        for column in ("source", "source_interface", "source_run_id", "lineage_raw_checksum")
        if column not in frame.columns or frame[column].isna().any() or (frame[column].astype(str) == "").any()
    ]
    if lineage_missing:
        issue_codes.append("lineage_unavailable")
    benchmark_kind = _lineage_value(frame, "benchmark_kind", "price_index")
    if not benchmark_policy_confirmed:
        issue_codes.append("policy_unconfirmed")
    if ratio < thresholds.coverage_threshold:
        issue_codes.append("coverage_gap")

    hard_fail_codes = {
        "calendar_missing",
        "schema_mismatch",
        "duplicate_key",
        "lineage_unavailable",
        "coverage_gap",
    }
    if set(issue_codes) & hard_fail_codes:
        quality_status = QUALITY_STATUS_FAIL if frame is not None else QUALITY_STATUS_MISSING
        dataset_status = "duplicate_key" if duplicate_keys else ("required_missing" if required else "unavailable")
    elif "policy_unconfirmed" in issue_codes:
        quality_status = QUALITY_STATUS_WARN
        dataset_status = "policy_unconfirmed"
    else:
        quality_status = QUALITY_STATUS_PASS
        dataset_status = "available"

    source = _lineage_value(frame, "source", "unknown")
    interface = _lineage_value(frame, "source_interface", "unknown")
    run_id = _lineage_value(frame, "source_run_id", "unknown")
    checksum = _lineage_value(frame, "lineage_raw_checksum", "")
    coverage = CoverageSummary(
        requested_start=str(expected_range[0]),
        requested_end=str(expected_range[1]),
        actual_start=None if frame.empty or "trade_date" not in frame else str(frame["trade_date"].min()),
        actual_end=None if frame.empty or "trade_date" not in frame else str(frame["trade_date"].max()),
        requested_symbols_count=1,
        actual_symbols_count=1 if not frame.empty else 0,
        open_trade_dates_count=denominator,
        expected_rows=denominator,
        actual_rows=numerator,
        missing_rows=len(missing_dates),
        missing_rate=(len(missing_dates) / denominator) if denominator else 1.0,
    )
    return QualityResult(
        run_id=run_id,
        generated_at=_iso(clock),
        dataset=DATASET_HS300_INDEX,
        source_name=source,
        source_interface=interface,
        target_dataset=DATASET_HS300_INDEX,
        input_config_hash=_config_hash(
            {
                "dataset": DATASET_HS300_INDEX,
                "index_code": index_code,
                "expected_range": list(expected_range),
                "thresholds": asdict(thresholds),
            }
        ),
        quality_status=quality_status,
        fetch_status="not_applicable",
        dataset_status=dataset_status,
        coverage=coverage,
        denominator_mode=DENOMINATOR_MODE_BENCHMARK,
        thresholds=thresholds,
        issue_count=len(issue_codes),
        missing_required_fields=missing_fields,
        duplicate_keys=duplicate_keys,
        coverage_gaps=(
            [{"missing_trade_dates": missing_dates}]
            if missing_dates
            else ([{"reason": "calendar_missing"}] if denominator == 0 else [])
        ),
        warnings=["policy_unconfirmed"] if "policy_unconfirmed" in issue_codes else [],
        schema_version=SCHEMA_VERSION,
        coverage_threshold=thresholds.coverage_threshold,
        missing_dates=missing_dates,
        gap_reason="calendar_missing" if denominator == 0 else ("coverage_gap" if missing_dates else ""),
        issue_codes=issue_codes,
        duplicate_key_count=len(duplicate_keys),
        source_run_id=run_id,
        manifest_run_id=run_id,
        lineage_raw_checksum=checksum,
        benchmark_kind=benchmark_kind,
        index_code=str(index_code),
        calendar_source=DATASET_TRADE_CALENDAR,
        missing_trade_dates=missing_dates,
        unavailable_mapping="required_missing" if required else "unavailable",
    )


def validate_pit_asof(
    frame: pd.DataFrame,
    decision_calendar: pd.DataFrame | Sequence[str] | None = None,
    dataset: str = "",
    keys: Sequence[str] = (),
    decision_time_column: str = "decision_time",
) -> GateValidationResult:
    del decision_calendar
    required_columns = {"available_at", decision_time_column, *keys}
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        return GateValidationResult(
            status="pit_failed",
            passed=False,
            issues=[{"code": "pit_field_missing", "dataset": dataset, "fields": missing}],
        )
    available = pd.to_datetime(frame["available_at"], utc=True, errors="coerce")
    decision = pd.to_datetime(frame[decision_time_column], utc=True, errors="coerce")
    if available.isna().any() or decision.isna().any():
        return GateValidationResult(
            status="pit_failed",
            passed=False,
            issues=[{"code": "pit_datetime_invalid", "dataset": dataset}],
        )
    future = frame[available > decision]
    if not future.empty:
        return GateValidationResult(
            status="pit_failed",
            passed=False,
            issues=[
                {
                    "code": "future_availability",
                    "dataset": dataset,
                    "count": int(len(future)),
                }
            ],
        )
    duplicate_columns = [*keys, decision_time_column, "available_at"]
    if duplicate_columns and frame.duplicated(duplicate_columns, keep=False).any():
        return GateValidationResult(
            status="pit_failed",
            passed=False,
            issues=[{"code": "pit_key_not_unique", "dataset": dataset}],
        )
    return GateValidationResult(status="pass", passed=True)


def validate_adjustment_consistency(
    prices_frame: pd.DataFrame,
    adjustment_policy: str = "qfq",
) -> GateValidationResult:
    required_columns = [
        "adjustment_policy",
        "adj_factor",
        "adjusted_open",
        "adjusted_high",
        "adjusted_low",
        "adjusted_close",
    ]
    missing = [column for column in required_columns if column not in prices_frame.columns]
    if missing:
        return GateValidationResult(
            status="adjustment_failed",
            passed=False,
            issues=[{"code": "adjusted_price_missing", "fields": missing}],
        )
    policies = {str(item) for item in prices_frame["adjustment_policy"].dropna().unique()}
    if len(policies) != 1 or (adjustment_policy and policies != {str(adjustment_policy)}):
        return GateValidationResult(
            status="adjustment_failed",
            passed=False,
            issues=[
                {
                    "code": "adjustment_policy_conflict",
                    "expected": adjustment_policy,
                    "actual": sorted(policies),
                }
            ],
        )
    if prices_frame["adj_factor"].isna().any():
        return GateValidationResult(
            status="adjustment_failed",
            passed=False,
            issues=[{"code": "adj_factor_missing"}],
        )
    adjusted_columns = ["adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"]
    if prices_frame[adjusted_columns].isna().any().any():
        return GateValidationResult(
            status="adjustment_failed",
            passed=False,
            issues=[{"code": "adjusted_price_missing", "fields": adjusted_columns}],
        )
    return GateValidationResult(status="pass", passed=True)


QUALITY_CSV_FIELDS: tuple[str, ...] = tuple(QualityResult(
    run_id="",
    generated_at="",
    dataset="",
    source_name="",
    source_interface="",
    target_dataset="",
    input_config_hash="",
    quality_status="pass",
    fetch_status="success",
    dataset_status="pass",
    coverage=CoverageSummary("", "", None, None, 0, 0, 0, 0, 0, 0, 0.0),
).to_csv_row().keys())


def _quality_paths(result: QualityResult, layout: LakeLayout) -> tuple[Path, Path]:
    root = layout.quality_root / result.run_id
    return root / f"{result.dataset}_quality.csv", root / f"{result.dataset}_quality.md"


def write_quality_reports(
    result: QualityResult,
    layout: LakeLayout | str | Path,
) -> tuple[Path, Path]:
    layout = layout if isinstance(layout, LakeLayout) else LakeLayout(layout)
    csv_path, md_path = _quality_paths(result, layout)
    row = result.to_csv_row()
    for key, value in row.items():
        if isinstance(value, (list, dict)):
            raise QualityReportError(f"复杂字段未序列化: {key}")
    for key in row:
        if key.endswith("_json"):
            json.loads(str(row[key]))
    csv_tmp = csv_path.with_name(csv_path.name + ".tmp")
    md_tmp = md_path.with_name(md_path.name + ".tmp")
    ensure_parent_dirs_for_write(csv_tmp)
    with csv_tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(QUALITY_CSV_FIELDS))
        writer.writeheader()
        writer.writerow(row)
        fh.flush()
        os.fsync(fh.fileno())
    csv_tmp.replace(csv_path)

    markdown = (
        f"# Quality Report: {result.dataset}\n\n"
        f"- run_id: `{result.run_id}`\n"
        f"- quality_status: `{result.quality_status}`\n"
        f"- fetch_status: `{result.fetch_status}`\n"
        f"- dataset_status: `{result.dataset_status}`\n"
        f"- denominator_mode: `{result.denominator_mode}`\n"
        f"- issue_count: `{result.issue_count}`\n"
        "\n> Markdown 仅供人工阅读；机器入口以 CSV 为准。\n"
    )
    ensure_parent_dirs_for_write(md_tmp)
    with md_tmp.open("w", encoding="utf-8") as fh:
        fh.write(markdown)
        fh.flush()
        os.fsync(fh.fileno())
    md_tmp.replace(md_path)
    return csv_path, md_path


__all__ = [
    "CoverageSummary",
    "DENOMINATOR_MODE_BENCHMARK",
    "DENOMINATOR_MODE_PRICES",
    "DENOMINATOR_MODE_TRADE_CALENDAR",
    "DENOMINATOR_MODE_TRADE_CALENDAR_REQUIRED",
    "QUALITY_CSV_FIELDS",
    "QualityReportError",
    "QualityResult",
    "QualityThresholds",
    "QualityValidationError",
    "GateValidationResult",
    "P0_CANDIDATE_AUDIT_REQUIRED",
    "P0_CANDIDATE_REQUIRED",
    "P0_CANDIDATE_UNPUBLISHED",
    "P0_CURRENT_POINTER_REQUIRED",
    "P0_READ_SCOPE_INVALID",
    "CR017_MISSING_FACTOR_DIRECTION",
    "CR017_INVALID_FACTOR_DIRECTION",
    "CR017_MISSING_LINEAGE",
    "CR017_INVALID_RAW_OHLC",
    "CR017_INVALID_ADJ_FACTOR",
    "CR017_DERIVED_OVERWRITES_RAW",
    "CR017_REASON_REQUIRED_MISSING",
    "CR017_MIXED_ADJUSTMENT_POLICY",
    "CR017_EXECUTION_REQUIRES_RAW",
    "CR017_UNEXPLAINED_ADJUSTMENT_JUMP",
    "CR017_MISSING_AS_OF_TRADE_DATE",
    "CR017_WARNING_NOT_PRODUCTION_PASS",
    "CR017_PARITY_MISMATCH",
    "CR017_QUALITY_FAILED",
    "CR017_REQUIRED_MISSING_REASON_CODES",
    "CR017_QUALITY_FAIL_REASON_CODES",
    "CR017_S05_REASON_CODES",
    "CR017_S05_FORBIDDEN_OPERATION_COUNTERS",
    "CR018_ADJUSTMENT_EXPECTED_POLICIES",
    "CR018_ADJUSTMENT_OPERATION_COUNTERS",
    "CR018_ADJUSTMENT_REASON_FACTOR_COVERAGE_INCOMPLETE",
    "CR018_ADJUSTMENT_REASON_FIELD_COVERAGE_INCOMPLETE",
    "CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_OVERWRITE",
    "CR018_ADJUSTMENT_REASON_LEGACY_QFQ_BASELINE_REQUIRED",
    "CR018_ADJUSTMENT_REASON_POLICY_MISMATCH",
    "CR018_ADJUSTMENT_REASON_QMT_REQUIRES_RAW",
    "CR018_ADJUSTMENT_REASON_VIEW_REQUIRED_MISSING",
    "CR018_ADJUSTMENT_REQUIRED_VIEW_IDS",
    "CR018_RELEASE_AUDIT_HISTORICAL_EVIDENCE_KEYS",
    "CR018_RELEASE_AUDIT_OPERATION_COUNTERS",
    "CR018_RELEASE_AUDIT_REQUIRED_EVIDENCE_REFS",
    "CR018_RELEASE_AUDIT_REQUIRED_FIELDS",
    "CR018_RELEASE_READINESS_AUDIT_SCHEMA",
    "CR018_RELEASE_REASON_AUDIT_EVIDENCE_INCOMPLETE",
    "CR018_RELEASE_REASON_P0_READINESS_FAILED",
    "CR018_RELEASE_REASON_PERMISSION_COUNTER_VIOLATION",
    "CR018_RELEASE_REASON_QUALITY_FAILED",
    "CR018_RELEASE_REASON_REQUIRED_MISSING",
    "CR018_RELEASE_REASON_ROLLBACK_SCOPE_NOT_RELEASE",
    "CR018_RELEASE_REASON_ROLLBACK_TARGET_REQUIRED",
    "ADJUSTMENT_GATE_STATUS_PASS",
    "ADJUSTMENT_GATE_STATUS_WARN",
    "ADJUSTMENT_GATE_STATUS_FAIL",
    "ADJUSTMENT_GATE_STATUS_REQUIRED_MISSING",
    "ADJUSTMENT_LEAKAGE_STATUS_BLOCKED",
    "AdjustmentQualityResult",
    "ParityCheckResult",
    "LeakageGuardResult",
    "BenchmarkGroupReadinessResult",
    "BenchmarkPitValidationResult",
    "AdjustmentPublishReadinessResult",
    "ReleaseReadinessAuditReport",
    "PitReadinessResult",
    "LifecycleReadinessResult",
    "TradabilityReadinessResult",
    "P0ValidationResult",
    "ReadQueryContract",
    "VALIDATE_DOES_NOT_PUBLISH",
    "adjustment_quality_gate",
    "check_adjustment_parity",
    "guard_execution_price_leakage",
    "build_ts017_matrix",
    "validate_adjustment_publish_readiness",
    "build_release_readiness_audit_report",
    "validate_benchmark_group_readiness",
    "validate_benchmark_components_weights_pit",
    "validate_pit_universe_readiness",
    "validate_lifecycle_readiness",
    "validate_tradability_readiness",
    "publish_p0_candidate",
    "read_p0_current_truth",
    "validate_dataset",
    "validate_hs300_index",
    "validate_p0_candidate",
    "validate_pit_asof",
    "validate_adjustment_consistency",
    "build_prices_coverage_gate",
    "write_quality_reports",
]
