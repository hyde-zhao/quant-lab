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
    CANONICAL_PRICES_COLUMNS,
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
    READINESS_STATUS_SCHEMA_MISMATCH,
    SCHEMA_VERSION,
)
from .lake_layout import LakeLayout, ensure_parent_dirs_for_write

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
        missing_dates = sorted({date for date, _symbol in expected_pairs - actual_pairs})
    else:
        expected_count = len(expected_dates)
        if expected_symbol_count:
            expected_count *= expected_symbol_count
        missing_rows_count = max(0, expected_count - actual_count)
    if dataset == DATASET_EVENTS:
        expected_dates = []
        missing_dates = []
        expected_count = actual_count
        missing_rows_count = 0
    coverage_denominator = expected_count
    coverage_ratio = (actual_count / coverage_denominator) if coverage_denominator else 0.0

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
        denominator_mode=(
            DENOMINATOR_MODE_TRADE_CALENDAR
            if dataset == DATASET_TRADE_CALENDAR
            else DENOMINATOR_MODE_PRICES
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
        "denominator_mode": DENOMINATOR_MODE_PRICES,
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
    "P0ValidationResult",
    "ReadQueryContract",
    "VALIDATE_DOES_NOT_PUBLISH",
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
