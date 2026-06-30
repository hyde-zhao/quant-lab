"""本地日频研究工具的共享契约常量。

本模块只定义字段、状态和值列表，不执行 I/O、不访问网络，也不导入运行时依赖。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

PRICE_REQUIRED_COLUMNS = (
    "trade_date",
    "symbol",
    "close",
)

PRICE_OPTIONAL_COLUMNS = (
    "available_at",
    "adjustment_policy",
    "volume",
    "amount",
    "is_suspended",
    "limit_up",
    "limit_down",
)

PRICE_ALL_COLUMNS = PRICE_REQUIRED_COLUMNS + PRICE_OPTIONAL_COLUMNS

INDEX_MEMBERS_REQUIRED_COLUMNS = (
    "symbol",
)

INDEX_MEMBERS_OPTIONAL_COLUMNS = (
    "snapshot_date",
    "effective_date",
    "available_at",
    "is_member",
    "is_pit_universe",
    "index_code",
)

INDEX_MEMBERS_ALL_COLUMNS = (
    INDEX_MEMBERS_REQUIRED_COLUMNS + INDEX_MEMBERS_OPTIONAL_COLUMNS
)

TRADE_CALENDAR_REQUIRED_COLUMNS = (
    "trade_date",
)

TRADE_CALENDAR_OPTIONAL_COLUMNS = (
    "is_open",
)

TRADE_CALENDAR_ALL_COLUMNS = (
    TRADE_CALENDAR_REQUIRED_COLUMNS + TRADE_CALENDAR_OPTIONAL_COLUMNS
)

MANIFEST_REQUIRED_FIELDS = (
    "schema_version",
    "run_id",
    "batch_id",
    "source",
    "interface",
    "request_params",
    "symbol_range",
    "date_range",
    "requested_at",
    "request_started_at",
    "request_finished_at",
    "completed_at",
    "manifest_written_at",
    "attempts",
    "retry_events",
    "raw_path",
    "standardized_output_path",
    "coverage_start",
    "coverage_end",
    "success_items",
    "failed_items",
    "error_type",
    "error_message",
    "status",
)

MANIFEST_STATUS_VALUES = (
    "pending",
    "running",
    "success",
    "partial_success",
    "failed",
    "skipped",
)

QUALITY_STATUS_VALUES = (
    "pass",
    "warn",
    "fail",
)

PARQUET_SCHEMA_VERSION = "1.0"

QUALITY_REPORT_SCHEMA_VERSION = "1.0"

DATASET_NAMES = (
    "prices",
    "index_members",
    "trade_calendar",
)

STANDARD_PARQUET_FILES = {
    "prices": "prices.parquet",
    "index_members": "index_members.parquet",
    "trade_calendar": "trade_calendar.parquet",
}

DATASET_REQUIRED_COLUMNS = {
    "prices": PRICE_REQUIRED_COLUMNS,
    "index_members": INDEX_MEMBERS_REQUIRED_COLUMNS,
    "trade_calendar": TRADE_CALENDAR_REQUIRED_COLUMNS,
}

DATASET_ALL_COLUMNS = {
    "prices": PRICE_ALL_COLUMNS,
    "index_members": INDEX_MEMBERS_ALL_COLUMNS,
    "trade_calendar": TRADE_CALENDAR_ALL_COLUMNS,
}

QUALITY_REPORT_FIELDS = (
    "report_schema_version",
    "manifest_run_id",
    "dataset",
    "fetch_status",
    "dataset_status",
    "coverage_start",
    "coverage_end",
    "coverage_denominator",
    "requested_start",
    "requested_end",
    "missing_rate",
    "failed_batch_count",
    "failed_symbol_dates",
    "missing_required_fields",
    "duplicate_record_count",
    "abnormal_price_count",
    "backfill_trade_days",
    "backfill_record_count",
    "last_successful_update_at",
    "data_freshness_trade_days",
    "data_freshness_calendar_days",
    "quality_status",
    "denominator_mode",
    "thresholds_json",
    "input_config_hash",
    "available_at_rule",
    "adjustment_policy",
    "is_pit_universe",
    "survivorship_bias_note",
    "source_manifest_path",
    "standardized_output_paths",
)

QUALITY_REPORT_FORMATS = (
    "csv",
    "markdown",
)

DATA_LAKE_V4_CONTRACT_VERSION = "data_lake_v4"


class SchemaChangeKind(str, Enum):
    """Reader-facing schema compatibility decision."""

    COMPATIBLE = "compatible"
    ADDITIVE = "additive"
    READER_FALLBACK = "reader_fallback"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class FallbackRule:
    field: str
    fallback_kind: str = "default"
    value: Any = None
    source_field: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SchemaContractFreeze:
    """Frozen dataset schema contract used by readers before accepting data."""

    dataset: str
    contract_version: str = DATA_LAKE_V4_CONTRACT_VERSION
    required_fields: tuple[str, ...] = ()
    field_types: Mapping[str, str] = field(default_factory=dict)
    primary_key: tuple[str, ...] = ()
    status: str = "frozen"
    compatible_from: tuple[str, ...] = ()
    breaking_changes: tuple[dict[str, Any], ...] = ()
    allowed_reader_fallbacks: tuple[FallbackRule, ...] = ()
    frozen_at: str = ""
    owner_feature: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_reader_fallbacks"] = [
            item.to_dict() for item in self.allowed_reader_fallbacks
        ]
        return payload


@dataclass(frozen=True, slots=True)
class SchemaCompatibilityResult:
    dataset: str
    contract_version: str
    change_kind: SchemaChangeKind
    compatible: bool
    missing_required_fields: tuple[str, ...] = ()
    type_mismatches: tuple[dict[str, str], ...] = ()
    additive_fields: tuple[str, ...] = ()
    fallback_fields: tuple[str, ...] = ()
    fallback_rules: tuple[FallbackRule, ...] = ()
    blocked_reasons: tuple[dict[str, Any], ...] = ()

    @property
    def reader_fallback_required(self) -> bool:
        return self.change_kind == SchemaChangeKind.READER_FALLBACK

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["change_kind"] = self.change_kind.value
        payload["fallback_rules"] = [item.to_dict() for item in self.fallback_rules]
        return payload


def evaluate_schema_compatibility(
    dataset_schema: Mapping[str, Any],
    contract: SchemaContractFreeze,
) -> SchemaCompatibilityResult:
    """Classify dataset schema changes without touching storage or runtime."""

    fields = _schema_fields(dataset_schema)
    field_types = _schema_field_types(dataset_schema)
    primary_key = tuple(str(item) for item in dataset_schema.get("primary_key", ()))
    contract_versions = {contract.contract_version, *contract.compatible_from}
    schema_version = str(dataset_schema.get("contract_version") or contract.contract_version)
    fallback_by_field = {rule.field: rule for rule in contract.allowed_reader_fallbacks}

    blocked_reasons: list[dict[str, Any]] = []
    fallback_rules: list[FallbackRule] = []
    if contract.status != "frozen":
        blocked_reasons.append({"code": "schema_contract_not_frozen", "status": contract.status})
    if schema_version not in contract_versions:
        blocked_reasons.append(
            {
                "code": "schema_contract_version_mismatch",
                "dataset_contract_version": schema_version,
                "expected_contract_version": contract.contract_version,
                "compatible_from": list(contract.compatible_from),
            }
        )

    missing_required: list[str] = []
    for field_name in contract.required_fields:
        if field_name in fields:
            continue
        rule = fallback_by_field.get(field_name)
        if rule is None:
            missing_required.append(field_name)
        else:
            fallback_rules.append(rule)

    type_mismatches: list[dict[str, str]] = []
    for field_name, expected_type in contract.field_types.items():
        actual_type = field_types.get(field_name)
        if actual_type is None or _schema_type_compatible(actual_type, expected_type):
            continue
        rule = fallback_by_field.get(field_name)
        if rule is None:
            type_mismatches.append(
                {
                    "field": field_name,
                    "expected": str(expected_type),
                    "actual": str(actual_type),
                }
            )
        else:
            fallback_rules.append(rule)

    if contract.primary_key and primary_key and tuple(primary_key) != tuple(contract.primary_key):
        blocked_reasons.append(
            {
                "code": "schema_primary_key_mismatch",
                "expected_primary_key": list(contract.primary_key),
                "actual_primary_key": list(primary_key),
            }
        )

    if missing_required:
        blocked_reasons.append(
            {
                "code": "schema_required_fields_missing",
                "missing_fields": list(missing_required),
            }
        )
    if type_mismatches:
        blocked_reasons.append(
            {
                "code": "schema_field_type_mismatch",
                "type_mismatches": type_mismatches,
            }
        )

    additive_fields = tuple(sorted(fields - set(contract.required_fields) - set(contract.field_types)))
    unique_fallback_rules = tuple(_dedupe_fallback_rules(fallback_rules))
    if blocked_reasons:
        change_kind = SchemaChangeKind.BLOCKED
        compatible = False
    elif unique_fallback_rules:
        change_kind = SchemaChangeKind.READER_FALLBACK
        compatible = True
    elif additive_fields:
        change_kind = SchemaChangeKind.ADDITIVE
        compatible = True
    else:
        change_kind = SchemaChangeKind.COMPATIBLE
        compatible = True

    return SchemaCompatibilityResult(
        dataset=contract.dataset,
        contract_version=contract.contract_version,
        change_kind=change_kind,
        compatible=compatible,
        missing_required_fields=tuple(missing_required),
        type_mismatches=tuple(type_mismatches),
        additive_fields=additive_fields,
        fallback_fields=tuple(rule.field for rule in unique_fallback_rules),
        fallback_rules=unique_fallback_rules,
        blocked_reasons=tuple(blocked_reasons),
    )


def _schema_fields(dataset_schema: Mapping[str, Any]) -> set[str]:
    raw_fields = dataset_schema.get("fields")
    if raw_fields is None:
        raw_fields = dataset_schema.get("columns", ())
    if isinstance(raw_fields, Mapping):
        return {str(key) for key in raw_fields}
    return {str(item) for item in raw_fields or ()}


def _schema_field_types(dataset_schema: Mapping[str, Any]) -> dict[str, str]:
    raw_fields = dataset_schema.get("fields")
    if not isinstance(raw_fields, Mapping):
        return {}
    output: dict[str, str] = {}
    for field_name, spec in raw_fields.items():
        if isinstance(spec, Mapping):
            output[str(field_name)] = str(spec.get("type") or spec.get("dtype") or "")
        else:
            output[str(field_name)] = str(spec)
    return output


def _schema_type_compatible(actual: str, expected: str) -> bool:
    if not expected:
        return True
    actual_text = actual.lower()
    expected_text = expected.lower()
    if actual_text == expected_text:
        return True
    aliases = {
        "string": {"object", "str", "string"},
        "str": {"object", "str", "string"},
        "int": {"int", "int64", "int32", "integer"},
        "float": {"float", "float64", "float32", "double"},
        "bool": {"bool", "boolean"},
        "datetime": {"datetime", "datetime64[ns]", "timestamp"},
    }
    return actual_text in aliases.get(expected_text, {expected_text})


def _dedupe_fallback_rules(rules: Sequence[FallbackRule]) -> list[FallbackRule]:
    seen: set[str] = set()
    output: list[FallbackRule] = []
    for rule in rules:
        if rule.field in seen:
            continue
        seen.add(rule.field)
        output.append(rule)
    return output

DEFAULT_ADJUSTMENT_POLICY = "qfq"

DEFAULT_AVAILABLE_AT_RULE = "trade_date_close_after"

DEFAULT_DECISION_TIME_RULE = DEFAULT_AVAILABLE_AT_RULE

QUALITY_POLICY_VALUES = (
    "fail_on_warn_or_fail",
    "require_pass",
    "pass_only",
    "strict",
    "allow_warn",
    "pass_warn",
)

DEFAULT_QUALITY_POLICY = "fail_on_warn_or_fail"

QUALITY_REPORT_REQUIRED_FIELDS = (
    "dataset",
    "quality_status",
    "fetch_status",
    "dataset_status",
    "missing_rate",
    "failed_batch_count",
    "manifest_run_id",
    "coverage_denominator",
    "denominator_mode",
    "thresholds_json",
    "input_config_hash",
)

DATASET_STATUS_PASS_VALUES = (
    "pass",
    "available",
    "ok",
)

DATASET_STATUS_WARN_VALUES = (
    "warn",
    "available_with_warnings",
)

DATASET_STATUS_FAIL_VALUES = (
    "fail",
    "quality_failed",
    "required_missing",
    "unavailable",
    "duplicate_key",
    "schema_mismatch",
)

FETCH_STATUS_SUCCESS_VALUES = (
    "success",
    "not_applicable",
    "cached",
)

AVAILABLE_AT_POLICY_VALUES = (
    "explicit",
    "trade_date_close_after",
    "close_after",
)

LOADER_WARNING_CODES = (
    "warn_non_pit_universe",
    "warn_source_fetch_failed_but_local_valid",
    "warn_minor_missing_rate",
    "warn_markdown_report_ignored",
)

LOADER_METADATA_FIELDS = (
    "loader_schema_version",
    "requested_start",
    "requested_end",
    "loaded_start",
    "loaded_end",
    "price_row_count",
    "universe_size",
    "calendar_size",
    "adjustment_policy",
    "available_at_rule",
    "quality_status",
    "fetch_status",
    "dataset_status",
    "quality_policy",
    "allow_warn",
    "quality_source",
    "quality_decision_reason",
    "derived_quality_summary",
    "missing_rate",
    "failed_batch_count",
    "manifest_run_id",
    "last_successful_update_at",
    "data_freshness_trade_days",
    "data_freshness_calendar_days",
    "is_pit_universe",
    "universe_mode",
    "pit_status",
    "survivorship_bias_note",
    "source_parquet_paths",
    "source_manifest_path",
    "source_quality_report_path",
    "filtered_symbol_count",
    "dropped_non_open_days",
    "warnings",
)

SURVIVORSHIP_BIAS_NOTE = (
    "第一版使用固定当前成分股快照，is_pit_universe=false，存在幸存者偏差。"
)

PIT_UNIVERSE_FIXED_SNAPSHOT_FORBIDDEN = "pit_universe_fixed_snapshot_forbidden"
PIT_UNIVERSE_REQUIRED_FIELD_MISSING = "pit_universe_required_field_missing"
PIT_UNIVERSE_AVAILABLE_AFTER_DECISION_TIME = "pit_universe_available_after_decision_time"


@dataclass(frozen=True, slots=True)
class PitUniverseConstituent:
    symbol: str
    effective_from: str
    effective_to: str
    available_at: str
    source_run_id: str
    lineage_checksum: str
    membership_status: str = "member"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PitUniverseConstituentChain:
    universe_id: str
    as_of_date: str
    policy_version: str
    universe_policy_ref: str
    constituents: tuple[PitUniverseConstituent, ...]
    is_pit_universe: bool = True
    survivorship_bias_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "universe_id": self.universe_id,
            "as_of_date": self.as_of_date,
            "policy_version": self.policy_version,
            "universe_policy_ref": self.universe_policy_ref,
            "constituents": [item.to_dict() for item in self.constituents],
            "is_pit_universe": self.is_pit_universe,
            "survivorship_bias_note": self.survivorship_bias_note,
        }


@dataclass(frozen=True, slots=True)
class PitUniverseChainValidationResult:
    passed: bool
    issues: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "issues": [dict(item) for item in self.issues]}


def validate_pit_universe_constituent_chain(
    chain: PitUniverseConstituentChain | Mapping[str, Any],
    *,
    decision_time: str | None = None,
) -> PitUniverseChainValidationResult:
    payload = chain.to_dict() if isinstance(chain, PitUniverseConstituentChain) else dict(chain)
    issues: list[dict[str, Any]] = []
    required = ("universe_id", "as_of_date", "policy_version", "universe_policy_ref", "constituents")
    missing = [field_name for field_name in required if _is_missing(payload.get(field_name))]
    if missing:
        issues.append({"code": PIT_UNIVERSE_REQUIRED_FIELD_MISSING, "missing_fields": missing})
    if not bool(payload.get("is_pit_universe")) or "固定当前" in str(payload.get("survivorship_bias_note") or ""):
        issues.append({"code": PIT_UNIVERSE_FIXED_SNAPSHOT_FORBIDDEN, "field": "is_pit_universe"})

    constituents = [dict(item) for item in payload.get("constituents") or ()]
    required_constituent = (
        "symbol",
        "effective_from",
        "effective_to",
        "available_at",
        "source_run_id",
        "lineage_checksum",
    )
    for index, constituent in enumerate(constituents):
        missing_constituent = [field_name for field_name in required_constituent if _is_missing(constituent.get(field_name))]
        if missing_constituent:
            issues.append(
                {
                    "code": PIT_UNIVERSE_REQUIRED_FIELD_MISSING,
                    "row_index": index,
                    "missing_fields": missing_constituent,
                }
            )
    if decision_time:
        decision = _parse_contract_timestamp(decision_time)
        for index, constituent in enumerate(constituents):
            available = _parse_contract_timestamp(constituent.get("available_at"))
            if decision is not None and available is not None and available > decision:
                issues.append(
                    {
                        "code": PIT_UNIVERSE_AVAILABLE_AFTER_DECISION_TIME,
                        "row_index": index,
                        "symbol": constituent.get("symbol"),
                        "decision_time": str(decision_time),
                        "available_at": str(constituent.get("available_at")),
                    }
                )
    return PitUniverseChainValidationResult(passed=not issues, issues=tuple(issues))


def _is_missing(value: Any) -> bool:
    return value is None or str(value).strip() == "" or value == ()


def _parse_contract_timestamp(value: Any) -> Any:
    if _is_missing(value):
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


DATA_PREP_CONFIG_KEYS = (
    "request_interval_seconds",
    "batch_size",
    "max_concurrency",
    "max_retries",
    "backoff_policy",
    "backoff_base_seconds",
    "backoff_max_seconds",
    "recent_trade_days_backfill",
    "raw_cache_retention",
    "raw_cache_path_pattern",
)

BACKTEST_REPORT_FIELDS = (
    "run_id",
    "strategy_name",
    "start_date",
    "end_date",
    "initial_cash",
    "final_value",
    "cumulative_return",
    "annual_return",
    "max_drawdown",
    "sharpe",
    "turnover",
    "adjustment_policy",
    "available_at_rule",
    "signal_time_rule",
    "execution_time_rule",
    "quality_status",
    "is_pit_universe",
    "survivorship_bias_note",
    "trade_limitations_note",
)

SWEEP_REPORT_FIELDS = (
    "run_id",
    "strategy_name",
    "lookback",
    "rebalance_freq",
    "fraction",
    "status",
    "error_message",
    "cumulative_return",
    "annual_return",
    "max_drawdown",
    "sharpe",
    "turnover",
    "quality_status",
    "missing_rate",
    "failed_batch_count",
    "elapsed_seconds",
    "adjustment_policy",
    "available_at_rule",
    "is_pit_universe",
)

CANDIDATE_REPORT_FIELDS = (
    "candidate_id",
    "candidate_type",
    "selection_reason",
    "lookback",
    "rebalance_freq",
    "fraction",
    "local_cumulative_return",
    "local_annual_return",
    "local_max_drawdown",
    "local_sharpe",
    "local_turnover",
    "joinquant_result_status",
    "joinquant_cumulative_return",
    "joinquant_max_drawdown",
    "joinquant_sharpe",
    "difference_note",
    "quality_status",
    "limitations_metadata",
)

TRADE_STATUS_REQUIRED_COLUMNS = (
    "trade_date",
    "symbol",
    "can_buy",
    "can_sell",
)

TRADE_STATUS_OPTIONAL_COLUMNS = (
    "status",
    "reason",
    "available_at",
)

LIMIT_PRICE_REQUIRED_COLUMNS = (
    "trade_date",
    "symbol",
    "limit_up",
    "limit_down",
)

LIMIT_PRICE_OPTIONAL_COLUMNS = (
    "available_at",
)

EVENT_REQUIRED_COLUMNS = (
    "event_date",
    "symbol",
    "event_type",
    "available_at",
)

AUDIT_REPORT_FIELDS = (
    "param_key",
    "baseline_run_id",
    "enhanced_run_id",
    "baseline_total_return",
    "enhanced_total_return",
    "return_delta",
    "baseline_max_drawdown",
    "enhanced_max_drawdown",
    "max_drawdown_delta",
    "baseline_sharpe",
    "enhanced_sharpe",
    "sharpe_delta",
    "candidate_rank_delta_status",
    "warning",
)

__all__ = (
    "DATA_LAKE_V4_CONTRACT_VERSION",
    "FallbackRule",
    "SchemaChangeKind",
    "SchemaCompatibilityResult",
    "SchemaContractFreeze",
    "PRICE_REQUIRED_COLUMNS",
    "PRICE_OPTIONAL_COLUMNS",
    "PRICE_ALL_COLUMNS",
    "INDEX_MEMBERS_REQUIRED_COLUMNS",
    "INDEX_MEMBERS_OPTIONAL_COLUMNS",
    "INDEX_MEMBERS_ALL_COLUMNS",
    "TRADE_CALENDAR_REQUIRED_COLUMNS",
    "TRADE_CALENDAR_OPTIONAL_COLUMNS",
    "TRADE_CALENDAR_ALL_COLUMNS",
    "MANIFEST_REQUIRED_FIELDS",
    "MANIFEST_STATUS_VALUES",
    "QUALITY_STATUS_VALUES",
    "PARQUET_SCHEMA_VERSION",
    "QUALITY_REPORT_SCHEMA_VERSION",
    "DATASET_NAMES",
    "STANDARD_PARQUET_FILES",
    "DATASET_REQUIRED_COLUMNS",
    "DATASET_ALL_COLUMNS",
    "QUALITY_REPORT_FIELDS",
    "QUALITY_REPORT_FORMATS",
    "DEFAULT_ADJUSTMENT_POLICY",
    "DEFAULT_AVAILABLE_AT_RULE",
    "DEFAULT_DECISION_TIME_RULE",
    "QUALITY_POLICY_VALUES",
    "DEFAULT_QUALITY_POLICY",
    "QUALITY_REPORT_REQUIRED_FIELDS",
    "DATASET_STATUS_PASS_VALUES",
    "DATASET_STATUS_WARN_VALUES",
    "DATASET_STATUS_FAIL_VALUES",
    "FETCH_STATUS_SUCCESS_VALUES",
    "AVAILABLE_AT_POLICY_VALUES",
    "LOADER_WARNING_CODES",
    "LOADER_METADATA_FIELDS",
    "SURVIVORSHIP_BIAS_NOTE",
    "PIT_UNIVERSE_FIXED_SNAPSHOT_FORBIDDEN",
    "PIT_UNIVERSE_REQUIRED_FIELD_MISSING",
    "PIT_UNIVERSE_AVAILABLE_AFTER_DECISION_TIME",
    "PitUniverseConstituent",
    "PitUniverseConstituentChain",
    "PitUniverseChainValidationResult",
    "validate_pit_universe_constituent_chain",
    "DATA_PREP_CONFIG_KEYS",
    "BACKTEST_REPORT_FIELDS",
    "SWEEP_REPORT_FIELDS",
    "CANDIDATE_REPORT_FIELDS",
    "TRADE_STATUS_REQUIRED_COLUMNS",
    "TRADE_STATUS_OPTIONAL_COLUMNS",
    "LIMIT_PRICE_REQUIRED_COLUMNS",
    "LIMIT_PRICE_OPTIONAL_COLUMNS",
    "EVENT_REQUIRED_COLUMNS",
    "AUDIT_REPORT_FIELDS",
    "evaluate_schema_compatibility",
)
