"""market_data 静态契约常量。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "1.0"

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

LAKE_LAYERS: tuple[str, ...] = (
    "raw",
    "manifest",
    "canonical",
    "gold",
    "quality",
    "catalog",
)

DATASET_PRICES = "prices"
DATASET_ADJ_FACTOR = "adj_factor"
DATASET_HS300_INDEX = "hs300_index"
DATASET_INDEX_MEMBERS = "index_members"
DATASET_INDEX_WEIGHTS = "index_weights"
DATASET_TRADE_CALENDAR = "trade_calendar"
DATASET_STOCK_BASIC = "stock_basic"
DATASET_TRADE_STATUS = "trade_status"
DATASET_PRICES_LIMIT = "prices_limit"
DATASET_EVENTS = "events"
DATASET_LIQUIDITY_CAPACITY = "liquidity_capacity"
DATASET_MARKET_CAP = "market_cap"
DATASET_INDUSTRY_CLASSIFICATION = "industry_classification"
DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES = "prices_limit_code_change_fixes"
DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS = "prices_limit_coverage_exclusions"
DATASETS: tuple[str, ...] = (
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_TRADE_CALENDAR,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    DATASET_PRICES_LIMIT,
    DATASET_EVENTS,
    DATASET_LIQUIDITY_CAPACITY,
    DATASET_MARKET_CAP,
    DATASET_INDUSTRY_CLASSIFICATION,
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES,
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS,
)

CR018_BENCHMARK_HS300 = "HS300"
CR018_BENCHMARK_ZZ500 = "ZZ500"
CR018_BENCHMARK_ZZ1000 = "ZZ1000"
CR018_BENCHMARK_CSI_ALL_SHARE = "CSI_ALL_SHARE"
CR018_BENCHMARK_IDS: tuple[str, ...] = (
    CR018_BENCHMARK_HS300,
    CR018_BENCHMARK_ZZ500,
    CR018_BENCHMARK_ZZ1000,
    CR018_BENCHMARK_CSI_ALL_SHARE,
)
CR018_BENCHMARK_INDEX_CODES: dict[str, str] = {
    CR018_BENCHMARK_HS300: "399300.SZ",
    CR018_BENCHMARK_ZZ500: "000905.SH",
    CR018_BENCHMARK_ZZ1000: "000852.SH",
    CR018_BENCHMARK_CSI_ALL_SHARE: "000985.SH",
}
CR018_BENCHMARK_DATASET_PRICES = "prices"
CR018_BENCHMARK_DATASET_COMPONENTS = "components"
CR018_BENCHMARK_DATASET_WEIGHTS = "weights"
CR018_BENCHMARK_DATASET_TYPES: tuple[str, ...] = (
    CR018_BENCHMARK_DATASET_PRICES,
    CR018_BENCHMARK_DATASET_COMPONENTS,
    CR018_BENCHMARK_DATASET_WEIGHTS,
)
CR018_BENCHMARK_REQUIRED_FOR_PUBLISH = True
CR018_BENCHMARK_CLAIM_PRODUCTION_EXCESS_RETURN = "production_excess_return"
CR018_BENCHMARK_CLAIM_INDEX_ENHANCEMENT = "index_enhancement"
CR018_BENCHMARK_CLAIM_TRACKING_ERROR = "tracking_error"
CR018_BENCHMARK_BLOCKED_CLAIMS: tuple[str, ...] = (
    CR018_BENCHMARK_CLAIM_PRODUCTION_EXCESS_RETURN,
    CR018_BENCHMARK_CLAIM_INDEX_ENHANCEMENT,
    CR018_BENCHMARK_CLAIM_TRACKING_ERROR,
)
CR018_BENCHMARK_REASON_REQUIREMENT_MISSING = "benchmark_requirement_missing"
CR018_BENCHMARK_REASON_PRICES_MISSING = "benchmark_prices_missing"
CR018_BENCHMARK_REASON_COMPONENTS_MISSING = "benchmark_components_missing"
CR018_BENCHMARK_REASON_WEIGHTS_MISSING = "benchmark_weights_missing"
CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT = (
    "benchmark_component_current_snapshot_not_pit"
)
CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH = "benchmark_weight_membership_mismatch"
CR018_BENCHMARK_REASON_PROXY_USED_AS_REAL = "proxy_benchmark_used_as_real"
CR018_BENCHMARK_REASON_TRADE_CALENDAR_DENOMINATOR_MISSING = (
    "trade_calendar_denominator_missing"
)
CR018_BENCHMARK_REASON_PERMISSION_COUNTER_VIOLATION = "benchmark_permission_counter_violation"
CR018_BENCHMARK_REASON_BY_DATASET_TYPE: dict[str, str] = {
    CR018_BENCHMARK_DATASET_PRICES: CR018_BENCHMARK_REASON_PRICES_MISSING,
    CR018_BENCHMARK_DATASET_COMPONENTS: CR018_BENCHMARK_REASON_COMPONENTS_MISSING,
    CR018_BENCHMARK_DATASET_WEIGHTS: CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
}
CR018_BENCHMARK_READINESS_ROW_FIELDS: tuple[str, ...] = (
    "benchmark_id",
    "index_code",
    "dataset_type",
    "required_for_publish",
    "readiness_status",
    "coverage_denominator",
    "reason_code",
    "claim_impact",
)
CR018_BENCHMARK_COMPONENT_PIT_FIELDS: tuple[str, ...] = (
    "effective_date",
    "available_at",
    "symbol",
    "is_member",
)
CR018_BENCHMARK_WEIGHT_PIT_FIELDS: tuple[str, ...] = (
    "effective_date",
    "available_at",
    "symbol",
    "weight",
)
CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "qmt_operation": 0,
}

CR018_PIT_READINESS_DATASET_ID = "pit_universe"
CR018_LIFECYCLE_READINESS_DATASET_ID = "lifecycle_code_change"
CR018_TRADABILITY_READINESS_DATASET_ID = "prices_limit_st_suspend"
CR018_PIT_REQUIRED_FIELDS: tuple[str, ...] = (
    "effective_date",
    "available_date",
    "available_at",
)
CR018_LIFECYCLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "symbol",
    "list_date",
    "delist_date",
)
CR018_CODE_CHANGE_EVIDENCE_FIELDS: tuple[str, ...] = (
    "code_change_mapping",
    "code_change_ref",
    "predecessor_id",
    "successor_id",
)
CR018_TRADE_STATUS_REQUIRED_FIELDS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "is_tradable",
)
CR018_ST_SUSPEND_REQUIRED_FIELDS: tuple[str, ...] = (
    "is_st",
    "is_suspended",
)
CR018_PRICES_LIMIT_REQUIRED_FIELDS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "limit_up",
    "limit_down",
)
CR018_REASON_PIT_AVAILABLE_FIELD_MISSING = "pit_available_field_missing"
CR018_REASON_AS_OF_JOIN_VIOLATION = "as_of_join_violation"
CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT = "current_snapshot_not_pit"
CR018_REASON_LIFECYCLE_FIELD_MISSING = "lifecycle_field_missing"
CR018_REASON_CODE_CHANGE_REQUIRED_MISSING = "code_change_required_missing"
CR018_REASON_ACTIVE_DENOMINATOR_MISSING = "active_denominator_missing"
CR018_REASON_TRADE_STATUS_REQUIRED_MISSING = "trade_status_required_missing"
CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING = "prices_limit_required_missing"
CR018_REASON_ST_SUSPEND_REQUIRED_MISSING = "st_suspend_required_missing"
CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED = "limit_trade_assumption_blocked"
CR018_REASON_UNPUBLISHED_READINESS_SOURCE = "unpublished_readiness_source"
CR018_REASON_PERMISSION_COUNTER_VIOLATION = "permission_counter_violation"
CR018_P0_READINESS_BLOCKED_CLAIMS: tuple[str, ...] = (
    "production_current_truth_scoped_release",
    "production_publish",
    "real_tradable_execution",
    "tradability_screened",
)
CR018_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "qmt_operation": 0,
    "duckdb_dependency_change": 0,
}

CANONICAL_PRICES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "close",
    "source",
    "source_run_id",
)
CANONICAL_PRICES_CONDITIONAL_COLUMNS: tuple[str, ...] = (
    "adjustment_policy",
    "available_at",
    "available_at_rule",
)
CANONICAL_PRICES_COLUMNS: tuple[str, ...] = (
    *CANONICAL_PRICES_REQUIRED_COLUMNS,
    *CANONICAL_PRICES_CONDITIONAL_COLUMNS,
)
CR005_CANONICAL_PRICES_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "adj_factor",
    "adjusted_open",
    "adjusted_high",
    "adjusted_low",
    "adjusted_close",
    "adjustment_policy",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "available_at",
    "available_at_rule",
    "lineage_raw_checksum",
)

MANIFEST_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "run_id",
    "batch_id",
    "idempotency_key",
    "source",
    "interface",
    "params",
    "params_hash",
    "requested_at",
    "started_at",
    "finished_at",
    "attempts",
    "status",
    "raw_path",
    "raw_checksum",
    "raw_row_count",
    "canonical_path",
    "error_type",
    "error_message",
    "retryable",
)

MANIFEST_STATUS_VALUES: tuple[str, ...] = (
    "pending",
    "running",
    "success",
    "partial_success",
    "failed",
    "skipped",
    "circuit_open",
    "orphan_raw",
)
TERMINAL_MANIFEST_STATUS_VALUES: tuple[str, ...] = (
    "success",
    "partial_success",
    "failed",
    "skipped",
    "circuit_open",
    "orphan_raw",
)

SOURCE_STATUS_RESOLVED = "resolved"
SOURCE_STATUS_DISABLED = "disabled"
SOURCE_STATUS_UNRESOLVED = "unresolved"
SOURCE_STATUS_VALUES: tuple[str, ...] = (
    SOURCE_STATUS_RESOLVED,
    SOURCE_STATUS_DISABLED,
    SOURCE_STATUS_UNRESOLVED,
)

CONNECTOR_ERROR_TYPES: tuple[str, ...] = (
    "source_disabled",
    "source_unresolved",
    "interface_not_allowed",
    "missing_credential",
    "quota_or_rate_limited",
    "permission_denied",
    "remote_error",
    "schema_mismatch",
    "quality_failed",
    "lake_root_invalid",
    "lake_root_missing",
    "resume_conflict",
    "network_error",
    "rate_limited",
    "provider_error",
    "contract_error",
    "circuit_open",
    "storage_error",
    "credential_exposure",
)

QUALITY_STATUS_PASS = "pass"
QUALITY_STATUS_WARN = "warn"
QUALITY_STATUS_FAIL = "fail"
QUALITY_STATUS_MISSING = "missing"
QUALITY_STATUS_VALUES: tuple[str, ...] = (
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARN,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_MISSING,
)
DATASET_STATUS_VALUES: tuple[str, ...] = (
    "available",
    "warn",
    "fail",
    "normalized",
    "unavailable",
    "required_missing",
    "schema_mismatch",
    "invalid_date",
    "duplicate_key",
    "future_availability",
    "pit_failed",
    "adjustment_policy_conflict",
    "adjustment_failed",
    "quality_failed",
    "policy_unconfirmed",
    "pit_incomplete",
    "non_pit_snapshot",
)

READINESS_STATUS_AVAILABLE = "available"
READINESS_STATUS_WARN = "warn"
READINESS_STATUS_UNAVAILABLE = "unavailable"
READINESS_STATUS_REQUIRED_MISSING = "required_missing"
READINESS_STATUS_QUALITY_FAILED = "quality_failed"
READINESS_STATUS_SCHEMA_MISMATCH = "schema_mismatch"
READINESS_STATUS_PIT_INCOMPLETE = "pit_incomplete"
READINESS_STATUS_NON_PIT_SNAPSHOT = "non_pit_snapshot"
READINESS_STATUS_VALUES: tuple[str, ...] = (
    READINESS_STATUS_AVAILABLE,
    READINESS_STATUS_WARN,
    READINESS_STATUS_UNAVAILABLE,
    READINESS_STATUS_REQUIRED_MISSING,
    READINESS_STATUS_QUALITY_FAILED,
    READINESS_STATUS_SCHEMA_MISMATCH,
    READINESS_STATUS_PIT_INCOMPLETE,
    READINESS_STATUS_NON_PIT_SNAPSHOT,
)

PIT_STATUS_AVAILABLE = "pit_available"
PIT_STATUS_INCOMPLETE = "pit_incomplete"
PIT_STATUS_NON_PIT_SNAPSHOT = "non_pit_snapshot"
PIT_STATUS_FAILED = "pit_failed"
PIT_STATUS_NOT_APPLICABLE = "not_applicable"
PIT_STATUS_VALUES: tuple[str, ...] = (
    PIT_STATUS_AVAILABLE,
    PIT_STATUS_INCOMPLETE,
    PIT_STATUS_NON_PIT_SNAPSHOT,
    PIT_STATUS_FAILED,
    PIT_STATUS_NOT_APPLICABLE,
)

SOURCE_FAKE = "fake"
SOURCE_AKSHARE = "akshare"
SOURCE_TUSHARE = "tushare"
SOURCE_JQDATA = "jqdata"
SOURCE_TICKFLOW = "tickflow"
SOURCE_VALUES: tuple[str, ...] = (
    SOURCE_FAKE,
    SOURCE_AKSHARE,
    SOURCE_TUSHARE,
    SOURCE_JQDATA,
    SOURCE_TICKFLOW,
)

INTERFACE_PRICES_DAILY = "prices.daily"
INTERFACE_PRICES_ADJ_FACTOR = "prices.adj_factor"
INTERFACE_HS300_INDEX_DAILY = "hs300_index.daily"
INTERFACE_INDEX_MEMBERS_SNAPSHOT = "index_members.snapshot"
INTERFACE_INDEX_WEIGHTS_SNAPSHOT = "index_weights.snapshot"
INTERFACE_TRADE_CALENDAR_DAILY = "trade_calendar.daily"
INTERFACE_STOCK_BASIC_SNAPSHOT = "stock_basic.snapshot"
INTERFACE_TRADE_STATUS_DAILY = "trade_status.daily"
INTERFACE_PRICES_LIMIT_DAILY = "prices_limit.daily"
INTERFACE_EVENTS_DISCLOSURE = "events.disclosure"

DATASET_KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    DATASET_PRICES: ("trade_date", "symbol"),
    DATASET_ADJ_FACTOR: ("trade_date", "symbol"),
    DATASET_HS300_INDEX: ("trade_date", "index_code"),
    DATASET_TRADE_CALENDAR: ("trade_date", "exchange"),
    DATASET_INDEX_WEIGHTS: ("trade_date", "index_code", "con_code"),
    DATASET_INDEX_MEMBERS: ("trade_date", "index_code", "con_code"),
    DATASET_STOCK_BASIC: ("symbol",),
    DATASET_TRADE_STATUS: ("trade_date", "symbol"),
    DATASET_PRICES_LIMIT: ("trade_date", "symbol"),
    DATASET_EVENTS: ("symbol", "event_type", "event_date", "available_at"),
    DATASET_LIQUIDITY_CAPACITY: ("trade_date", "symbol"),
    DATASET_MARKET_CAP: ("trade_date", "symbol"),
    DATASET_INDUSTRY_CLASSIFICATION: ("symbol", "classification_standard", "effective_date"),
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES: (
        "trade_date",
        "symbol",
        "source_symbol",
        "mapping_type",
    ),
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS: ("trade_date", "symbol", "exclusion_reason"),
}

DATASET_PIT_FIELDS: dict[str, tuple[str, ...]] = {
    DATASET_INDEX_MEMBERS: ("effective_date", "available_date", "available_at"),
    DATASET_INDEX_WEIGHTS: ("effective_date", "available_date", "available_at"),
    DATASET_STOCK_BASIC: ("effective_date", "available_date", "available_at"),
    DATASET_INDUSTRY_CLASSIFICATION: ("effective_date", "available_date", "available_at"),
}

CANONICAL_HS300_INDEX_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "index_code",
    "close",
    "pre_close",
    "pct_chg",
    "open",
    "high",
    "low",
    "volume",
    "amount",
    "benchmark_kind",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "available_at",
    "available_at_rule",
    "lineage_raw_checksum",
)

CANONICAL_ADJ_FACTOR_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "adj_factor",
    "adjustment_policy",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_TRADE_CALENDAR_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "exchange",
    "is_open",
    "pretrade_date",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_INDEX_WEIGHTS_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "index_code",
    "con_code",
    "weight",
    "effective_date",
    "available_date",
    "available_at",
    "available_at_rule",
    "pit_status",
    "readiness_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_INDEX_MEMBERS_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "index_code",
    "con_code",
    "in_date",
    "out_date",
    "is_member",
    "effective_date",
    "available_date",
    "available_at",
    "available_at_rule",
    "is_pit_universe",
    "pit_status",
    "readiness_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
    "derived_from",
)

CANONICAL_STOCK_BASIC_COLUMNS: tuple[str, ...] = (
    "symbol",
    "name",
    "market",
    "list_status",
    "list_date",
    "delist_date",
    "effective_date",
    "available_date",
    "available_at",
    "available_at_rule",
    "pit_status",
    "readiness_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_TRADE_STATUS_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "is_tradable",
    "is_suspended",
    "is_st",
    "status_reason",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_PRICES_LIMIT_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "limit_up",
    "limit_down",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_EVENTS_COLUMNS: tuple[str, ...] = (
    "symbol",
    "event_type",
    "event_date",
    "available_at",
    "available_at_rule",
    "payload",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_LIQUIDITY_CAPACITY_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "volume",
    "amount",
    "amount_unit",
    "adv20_amount",
    "adv20_volume",
    "turnover_rate",
    "turnover_rate_f",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_MARKET_CAP_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "market_cap",
    "float_market_cap",
    "turnover_rate",
    "turnover_rate_f",
    "volume_ratio",
    "pe",
    "pe_ttm",
    "pb",
    "ps",
    "ps_ttm",
    "dv_ratio",
    "dv_ttm",
    "total_share",
    "float_share",
    "free_share",
    "market_cap_unit",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_INDUSTRY_CLASSIFICATION_COLUMNS: tuple[str, ...] = (
    "symbol",
    "industry_code",
    "industry_name",
    "classification_standard",
    "effective_date",
    "available_date",
    "available_at",
    "available_at_rule",
    "pit_status",
    "readiness_status",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_PRICES_LIMIT_CODE_CHANGE_FIXES_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "source_symbol",
    "limit_up",
    "limit_down",
    "mapping_type",
    "mapping_effective_date",
    "reason",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_PRICES_LIMIT_COVERAGE_EXCLUSIONS_COLUMNS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "exclusion_reason",
    "reference_date",
    "reference_symbol",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
)

DATASET_SCHEMA_REGISTRY: dict[str, dict[str, tuple[str, ...]]] = {
    DATASET_PRICES: {
        "columns": CR005_CANONICAL_PRICES_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_PRICES],
        "adjusted_price_columns": (
            "adjusted_open",
            "adjusted_high",
            "adjusted_low",
            "adjusted_close",
        ),
    },
    DATASET_ADJ_FACTOR: {
        "columns": CANONICAL_ADJ_FACTOR_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_ADJ_FACTOR],
    },
    DATASET_HS300_INDEX: {
        "columns": CANONICAL_HS300_INDEX_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_HS300_INDEX],
    },
    DATASET_TRADE_CALENDAR: {
        "columns": CANONICAL_TRADE_CALENDAR_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_TRADE_CALENDAR],
    },
    DATASET_INDEX_WEIGHTS: {
        "columns": CANONICAL_INDEX_WEIGHTS_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_INDEX_WEIGHTS],
        "pit_fields": DATASET_PIT_FIELDS[DATASET_INDEX_WEIGHTS],
        "readiness_status_values": READINESS_STATUS_VALUES,
        "pit_status_values": PIT_STATUS_VALUES,
    },
    DATASET_INDEX_MEMBERS: {
        "columns": CANONICAL_INDEX_MEMBERS_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_INDEX_MEMBERS],
        "pit_fields": DATASET_PIT_FIELDS[DATASET_INDEX_MEMBERS],
        "readiness_status_values": READINESS_STATUS_VALUES,
        "pit_status_values": PIT_STATUS_VALUES,
    },
    DATASET_STOCK_BASIC: {
        "columns": CANONICAL_STOCK_BASIC_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_STOCK_BASIC],
        "pit_fields": DATASET_PIT_FIELDS[DATASET_STOCK_BASIC],
        "readiness_status_values": READINESS_STATUS_VALUES,
        "pit_status_values": PIT_STATUS_VALUES,
    },
    DATASET_TRADE_STATUS: {
        "columns": CANONICAL_TRADE_STATUS_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_TRADE_STATUS],
        "w3_required": ("source_interface", "available_at"),
    },
    DATASET_PRICES_LIMIT: {
        "columns": CANONICAL_PRICES_LIMIT_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_PRICES_LIMIT],
        "w3_required": ("source_interface", "available_at"),
    },
    DATASET_EVENTS: {
        "columns": CANONICAL_EVENTS_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_EVENTS],
        "w3_required": ("available_at",),
    },
    DATASET_LIQUIDITY_CAPACITY: {
        "columns": CANONICAL_LIQUIDITY_CAPACITY_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_LIQUIDITY_CAPACITY],
        "w3_required": ("source_interface", "available_at"),
    },
    DATASET_MARKET_CAP: {
        "columns": CANONICAL_MARKET_CAP_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_MARKET_CAP],
        "w3_required": ("source_interface", "available_at"),
    },
    DATASET_INDUSTRY_CLASSIFICATION: {
        "columns": CANONICAL_INDUSTRY_CLASSIFICATION_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_INDUSTRY_CLASSIFICATION],
        "pit_fields": DATASET_PIT_FIELDS[DATASET_INDUSTRY_CLASSIFICATION],
        "readiness_status_values": READINESS_STATUS_VALUES,
        "pit_status_values": PIT_STATUS_VALUES,
    },
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES: {
        "columns": CANONICAL_PRICES_LIMIT_CODE_CHANGE_FIXES_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES],
        "w3_required": ("source_interface",),
    },
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS: {
        "columns": CANONICAL_PRICES_LIMIT_COVERAGE_EXCLUSIONS_COLUMNS,
        "key_columns": DATASET_KEY_COLUMNS[DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS],
        "w3_required": ("source_interface",),
    },
}

ADJUSTMENT_POLICY_RAW = "raw"
ADJUSTMENT_POLICY_QFQ = "qfq"
ADJUSTMENT_POLICY_HFQ = "hfq"
ADJUSTMENT_POLICY_RETURNS_ADJUSTED = "returns_adjusted"
ADJUSTMENT_POLICY_VALUES: tuple[str, ...] = (
    ADJUSTMENT_POLICY_RAW,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
)

CR017_VIEW_PRICES_RAW = "prices_raw"
CR017_VIEW_ADJ_FACTOR = DATASET_ADJ_FACTOR
CR017_VIEW_PRICES_QFQ = "prices_qfq"
CR017_VIEW_PRICES_HFQ = "prices_hfq"
CR017_VIEW_RETURNS_ADJUSTED = "returns_adjusted"
CR017_VIEW_IDS: tuple[str, ...] = (
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)
CR017_DERIVED_VIEW_IDS: tuple[str, ...] = (
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)
CR017_SCHEMA_VERSION = "1.0"
CR017_DERIVATION_VERSION = "cr017.derived.v1"

CR017_PRICES_RAW_REQUIRED_FIELDS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "source",
    "source_interface",
    "source_run_id",
    "batch_id",
    "available_at",
    "available_at_rule",
    "lineage_checksum",
    "quality_status",
)
CR017_ADJ_FACTOR_REQUIRED_FIELDS: tuple[str, ...] = (
    "trade_date",
    "symbol",
    "adj_factor",
    "provider_factor_direction",
    "factor_base_date_policy",
    "source_run_id",
    "batch_id",
    "available_at",
    "as_of_trade_date",
    "lineage_checksum",
    "quality_status",
)
CR017_SOURCE_LINEAGE_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_run_id",
    "batch_id",
    "lineage_checksum",
)
CR017_DERIVED_COMMON_REQUIRED_FIELDS: tuple[str, ...] = (
    "view_id",
    "schema_version",
    "derivation_version",
    "source_run_id",
    "lineage_checksum",
    "quality_status",
)
CR017_PRICES_QFQ_REQUIRED_FIELDS: tuple[str, ...] = (
    *CR017_DERIVED_COMMON_REQUIRED_FIELDS,
    "trade_date",
    "symbol",
    "research_adjustment_policy",
    "adjusted_open",
    "adjusted_high",
    "adjusted_low",
    "adjusted_close",
    "as_of_trade_date",
    "input_snapshot_id",
)
CR017_PRICES_HFQ_REQUIRED_FIELDS: tuple[str, ...] = (
    *CR017_DERIVED_COMMON_REQUIRED_FIELDS,
    "trade_date",
    "symbol",
    "research_adjustment_policy",
    "adjusted_open",
    "adjusted_high",
    "adjusted_low",
    "adjusted_close",
    "base_trade_date",
    "factor_base_date_policy",
)
CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS: tuple[str, ...] = (
    *CR017_DERIVED_COMMON_REQUIRED_FIELDS,
    "trade_date",
    "symbol",
    "research_adjustment_policy",
    "return_type",
    "adjusted_return",
    "start_price_ref",
    "end_price_ref",
    "input_snapshot_id",
)
CR017_REQUIRED_FIELD_SETS: dict[str, tuple[str, ...]] = {
    CR017_VIEW_PRICES_RAW: CR017_PRICES_RAW_REQUIRED_FIELDS,
    CR017_VIEW_ADJ_FACTOR: CR017_ADJ_FACTOR_REQUIRED_FIELDS,
    CR017_VIEW_PRICES_QFQ: CR017_PRICES_QFQ_REQUIRED_FIELDS,
    CR017_VIEW_PRICES_HFQ: CR017_PRICES_HFQ_REQUIRED_FIELDS,
    CR017_VIEW_RETURNS_ADJUSTED: CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS,
}
CR017_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "dependency_change": 0,
    "legacy_qfq_overwrite": 0,
}

CR014_UNIVERSE_SCOPE_ALL_A_SHARE = "all_a_share"
CR014_COVERAGE_START_POLICY_SECURITY_INCEPTION = "security_inception_or_list_date"
CR014_CURRENT_TRADE_DATE_POLICY_LAST_CLOSED = "last_closed_open_trade_date"

CR014_UNIVERSE_METADATA_FIELDS: tuple[str, ...] = (
    "universe_scope",
    "coverage_start_policy",
    "current_trade_date_policy",
    "as_of_trade_date",
    "calendar_source",
)

CR014_LIFECYCLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "list_date",
    "delist_date",
    "list_status",
    "code_change_mapping",
    "exchange",
    "board",
    "effective_date",
    "available_at",
    "source_interface",
    "run_id",
)

CR014_SECURITY_IDENTITY_FIELDS: tuple[str, ...] = (
    "security_id",
    "symbol",
    "exchange",
    "valid_from",
    "valid_to",
    "predecessor_id",
    "successor_id",
    "lifecycle_status",
)

CR014_LIFECYCLE_STATUS_ACTIVE = "active"
CR014_LIFECYCLE_STATUS_DELISTED = "delisted"
CR014_LIFECYCLE_STATUS_SUSPENDED = "suspended"
CR014_LIFECYCLE_STATUS_NOT_YET_LISTED = "not_yet_listed"
CR014_LIFECYCLE_STATUS_REQUIRED_MISSING = "required_missing"
CR014_LIFECYCLE_STATUS_VALUES: tuple[str, ...] = (
    CR014_LIFECYCLE_STATUS_ACTIVE,
    CR014_LIFECYCLE_STATUS_DELISTED,
    CR014_LIFECYCLE_STATUS_SUSPENDED,
    CR014_LIFECYCLE_STATUS_NOT_YET_LISTED,
    CR014_LIFECYCLE_STATUS_REQUIRED_MISSING,
)

CR014_LIST_STATUS_LISTED = "listed"
CR014_LIST_STATUS_DELISTED = "delisted"
CR014_LIST_STATUS_SUSPENDED = "suspended"
CR014_LIST_STATUS_PRE_LISTED = "pre_listed"
CR014_LIST_STATUS_UNKNOWN = "unknown"
CR014_LIST_STATUS_VALUES: tuple[str, ...] = (
    CR014_LIST_STATUS_LISTED,
    CR014_LIST_STATUS_DELISTED,
    CR014_LIST_STATUS_SUSPENDED,
    CR014_LIST_STATUS_PRE_LISTED,
    CR014_LIST_STATUS_UNKNOWN,
)

CR014_CLAIM_FULL_A_SINCE_INCEPTION = "full_a_since_inception"

CR014_REQUIRED_MISSING_LIFECYCLE = "lifecycle_required_missing"
CR014_REQUIRED_MISSING_CALENDAR = "calendar_required_missing"
CR014_REQUIRED_MISSING_CODE_CHANGE = "code_change_required_missing"
CR014_CODE_CHANGE_CHAIN_CONFLICT = "code_change_chain_conflict"
CR014_CURRENT_TRADE_DATE_UNAVAILABLE = "current_trade_date_unavailable"
CR014_UNKNOWN_LIFECYCLE_STATUS = "unknown_lifecycle_status"
CR014_REQUIRED_MISSING_CODES: tuple[str, ...] = (
    CR014_REQUIRED_MISSING_LIFECYCLE,
    CR014_REQUIRED_MISSING_CALENDAR,
    CR014_REQUIRED_MISSING_CODE_CHANGE,
    CR014_CODE_CHANGE_CHAIN_CONFLICT,
    CR014_CURRENT_TRADE_DATE_UNAVAILABLE,
    CR014_UNKNOWN_LIFECYCLE_STATUS,
)

CR014_FORBIDDEN_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "credential_read": 0,
    "legacy_data_operation": 0,
    "old_report_overwrite": 0,
    "duckdb_dependency_change": 0,
    "duckdb_write": 0,
    "catalog_current_pointer_publish": 0,
    "s09_real_execution": 0,
}

__all__ = [
    "DATA_LAKE_V4_CONTRACT_VERSION",
    "FallbackRule",
    "SchemaChangeKind",
    "SchemaCompatibilityResult",
    "SchemaContractFreeze",
    "evaluate_schema_compatibility",
    "SCHEMA_VERSION",
    "LAKE_LAYERS",
    "DATASET_PRICES",
    "DATASET_ADJ_FACTOR",
    "DATASET_HS300_INDEX",
    "DATASET_INDEX_MEMBERS",
    "DATASET_INDEX_WEIGHTS",
    "DATASET_TRADE_CALENDAR",
    "DATASET_STOCK_BASIC",
    "DATASET_TRADE_STATUS",
    "DATASET_PRICES_LIMIT",
    "DATASET_EVENTS",
    "DATASET_LIQUIDITY_CAPACITY",
    "DATASET_MARKET_CAP",
    "DATASET_INDUSTRY_CLASSIFICATION",
    "DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES",
    "DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS",
    "DATASETS",
    "CR018_BENCHMARK_HS300",
    "CR018_BENCHMARK_ZZ500",
    "CR018_BENCHMARK_ZZ1000",
    "CR018_BENCHMARK_CSI_ALL_SHARE",
    "CR018_BENCHMARK_IDS",
    "CR018_BENCHMARK_INDEX_CODES",
    "CR018_BENCHMARK_DATASET_PRICES",
    "CR018_BENCHMARK_DATASET_COMPONENTS",
    "CR018_BENCHMARK_DATASET_WEIGHTS",
    "CR018_BENCHMARK_DATASET_TYPES",
    "CR018_BENCHMARK_REQUIRED_FOR_PUBLISH",
    "CR018_BENCHMARK_CLAIM_PRODUCTION_EXCESS_RETURN",
    "CR018_BENCHMARK_CLAIM_INDEX_ENHANCEMENT",
    "CR018_BENCHMARK_CLAIM_TRACKING_ERROR",
    "CR018_BENCHMARK_BLOCKED_CLAIMS",
    "CR018_BENCHMARK_REASON_REQUIREMENT_MISSING",
    "CR018_BENCHMARK_REASON_PRICES_MISSING",
    "CR018_BENCHMARK_REASON_COMPONENTS_MISSING",
    "CR018_BENCHMARK_REASON_WEIGHTS_MISSING",
    "CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT",
    "CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH",
    "CR018_BENCHMARK_REASON_PROXY_USED_AS_REAL",
    "CR018_BENCHMARK_REASON_TRADE_CALENDAR_DENOMINATOR_MISSING",
    "CR018_BENCHMARK_REASON_PERMISSION_COUNTER_VIOLATION",
    "CR018_BENCHMARK_REASON_BY_DATASET_TYPE",
    "CR018_BENCHMARK_READINESS_ROW_FIELDS",
    "CR018_BENCHMARK_COMPONENT_PIT_FIELDS",
    "CR018_BENCHMARK_WEIGHT_PIT_FIELDS",
    "CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS",
    "CR018_PIT_READINESS_DATASET_ID",
    "CR018_LIFECYCLE_READINESS_DATASET_ID",
    "CR018_TRADABILITY_READINESS_DATASET_ID",
    "CR018_PIT_REQUIRED_FIELDS",
    "CR018_LIFECYCLE_REQUIRED_FIELDS",
    "CR018_CODE_CHANGE_EVIDENCE_FIELDS",
    "CR018_TRADE_STATUS_REQUIRED_FIELDS",
    "CR018_ST_SUSPEND_REQUIRED_FIELDS",
    "CR018_PRICES_LIMIT_REQUIRED_FIELDS",
    "CR018_REASON_PIT_AVAILABLE_FIELD_MISSING",
    "CR018_REASON_AS_OF_JOIN_VIOLATION",
    "CR018_REASON_CURRENT_SNAPSHOT_NOT_PIT",
    "CR018_REASON_LIFECYCLE_FIELD_MISSING",
    "CR018_REASON_CODE_CHANGE_REQUIRED_MISSING",
    "CR018_REASON_ACTIVE_DENOMINATOR_MISSING",
    "CR018_REASON_TRADE_STATUS_REQUIRED_MISSING",
    "CR018_REASON_PRICES_LIMIT_REQUIRED_MISSING",
    "CR018_REASON_ST_SUSPEND_REQUIRED_MISSING",
    "CR018_REASON_LIMIT_TRADE_ASSUMPTION_BLOCKED",
    "CR018_REASON_UNPUBLISHED_READINESS_SOURCE",
    "CR018_REASON_PERMISSION_COUNTER_VIOLATION",
    "CR018_P0_READINESS_BLOCKED_CLAIMS",
    "CR018_FORBIDDEN_OPERATION_COUNTERS",
    "DATASET_KEY_COLUMNS",
    "DATASET_PIT_FIELDS",
    "DATASET_SCHEMA_REGISTRY",
    "QUALITY_STATUS_PASS",
    "QUALITY_STATUS_WARN",
    "QUALITY_STATUS_FAIL",
    "QUALITY_STATUS_MISSING",
    "QUALITY_STATUS_VALUES",
    "DATASET_STATUS_VALUES",
    "READINESS_STATUS_AVAILABLE",
    "READINESS_STATUS_WARN",
    "READINESS_STATUS_UNAVAILABLE",
    "READINESS_STATUS_REQUIRED_MISSING",
    "READINESS_STATUS_QUALITY_FAILED",
    "READINESS_STATUS_SCHEMA_MISMATCH",
    "READINESS_STATUS_PIT_INCOMPLETE",
    "READINESS_STATUS_NON_PIT_SNAPSHOT",
    "READINESS_STATUS_VALUES",
    "PIT_STATUS_AVAILABLE",
    "PIT_STATUS_INCOMPLETE",
    "PIT_STATUS_NON_PIT_SNAPSHOT",
    "PIT_STATUS_FAILED",
    "PIT_STATUS_NOT_APPLICABLE",
    "PIT_STATUS_VALUES",
    "CANONICAL_PRICES_REQUIRED_COLUMNS",
    "CANONICAL_PRICES_CONDITIONAL_COLUMNS",
    "CANONICAL_PRICES_COLUMNS",
    "CR005_CANONICAL_PRICES_COLUMNS",
    "CANONICAL_ADJ_FACTOR_COLUMNS",
    "CANONICAL_HS300_INDEX_COLUMNS",
    "CANONICAL_TRADE_CALENDAR_COLUMNS",
    "CANONICAL_INDEX_WEIGHTS_COLUMNS",
    "CANONICAL_INDEX_MEMBERS_COLUMNS",
    "CANONICAL_STOCK_BASIC_COLUMNS",
    "CANONICAL_TRADE_STATUS_COLUMNS",
    "CANONICAL_PRICES_LIMIT_COLUMNS",
    "CANONICAL_EVENTS_COLUMNS",
    "ADJUSTMENT_POLICY_RAW",
    "ADJUSTMENT_POLICY_QFQ",
    "ADJUSTMENT_POLICY_HFQ",
    "ADJUSTMENT_POLICY_RETURNS_ADJUSTED",
    "ADJUSTMENT_POLICY_VALUES",
    "CR017_VIEW_PRICES_RAW",
    "CR017_VIEW_ADJ_FACTOR",
    "CR017_VIEW_PRICES_QFQ",
    "CR017_VIEW_PRICES_HFQ",
    "CR017_VIEW_RETURNS_ADJUSTED",
    "CR017_VIEW_IDS",
    "CR017_DERIVED_VIEW_IDS",
    "CR017_SCHEMA_VERSION",
    "CR017_DERIVATION_VERSION",
    "CR017_PRICES_RAW_REQUIRED_FIELDS",
    "CR017_ADJ_FACTOR_REQUIRED_FIELDS",
    "CR017_SOURCE_LINEAGE_REQUIRED_FIELDS",
    "CR017_DERIVED_COMMON_REQUIRED_FIELDS",
    "CR017_PRICES_QFQ_REQUIRED_FIELDS",
    "CR017_PRICES_HFQ_REQUIRED_FIELDS",
    "CR017_RETURNS_ADJUSTED_REQUIRED_FIELDS",
    "CR017_REQUIRED_FIELD_SETS",
    "CR017_FORBIDDEN_OPERATION_COUNTERS",
    "MANIFEST_REQUIRED_FIELDS",
    "MANIFEST_STATUS_VALUES",
    "TERMINAL_MANIFEST_STATUS_VALUES",
    "SOURCE_STATUS_RESOLVED",
    "SOURCE_STATUS_DISABLED",
    "SOURCE_STATUS_UNRESOLVED",
    "SOURCE_STATUS_VALUES",
    "CONNECTOR_ERROR_TYPES",
    "SOURCE_FAKE",
    "SOURCE_AKSHARE",
    "SOURCE_TUSHARE",
    "SOURCE_JQDATA",
    "SOURCE_TICKFLOW",
    "SOURCE_VALUES",
    "INTERFACE_PRICES_DAILY",
    "INTERFACE_PRICES_ADJ_FACTOR",
    "INTERFACE_HS300_INDEX_DAILY",
    "INTERFACE_INDEX_MEMBERS_SNAPSHOT",
    "INTERFACE_INDEX_WEIGHTS_SNAPSHOT",
    "INTERFACE_TRADE_CALENDAR_DAILY",
    "INTERFACE_STOCK_BASIC_SNAPSHOT",
    "INTERFACE_TRADE_STATUS_DAILY",
    "INTERFACE_PRICES_LIMIT_DAILY",
    "INTERFACE_EVENTS_DISCLOSURE",
    "CR014_UNIVERSE_SCOPE_ALL_A_SHARE",
    "CR014_COVERAGE_START_POLICY_SECURITY_INCEPTION",
    "CR014_CURRENT_TRADE_DATE_POLICY_LAST_CLOSED",
    "CR014_UNIVERSE_METADATA_FIELDS",
    "CR014_LIFECYCLE_REQUIRED_FIELDS",
    "CR014_SECURITY_IDENTITY_FIELDS",
    "CR014_LIFECYCLE_STATUS_ACTIVE",
    "CR014_LIFECYCLE_STATUS_DELISTED",
    "CR014_LIFECYCLE_STATUS_SUSPENDED",
    "CR014_LIFECYCLE_STATUS_NOT_YET_LISTED",
    "CR014_LIFECYCLE_STATUS_REQUIRED_MISSING",
    "CR014_LIFECYCLE_STATUS_VALUES",
    "CR014_LIST_STATUS_LISTED",
    "CR014_LIST_STATUS_DELISTED",
    "CR014_LIST_STATUS_SUSPENDED",
    "CR014_LIST_STATUS_PRE_LISTED",
    "CR014_LIST_STATUS_UNKNOWN",
    "CR014_LIST_STATUS_VALUES",
    "CR014_CLAIM_FULL_A_SINCE_INCEPTION",
    "CR014_REQUIRED_MISSING_LIFECYCLE",
    "CR014_REQUIRED_MISSING_CALENDAR",
    "CR014_REQUIRED_MISSING_CODE_CHANGE",
    "CR014_CODE_CHANGE_CHAIN_CONFLICT",
    "CR014_CURRENT_TRADE_DATE_UNAVAILABLE",
    "CR014_UNKNOWN_LIFECYCLE_STATUS",
    "CR014_REQUIRED_MISSING_CODES",
    "CR014_FORBIDDEN_OPERATION_COUNTERS",
]
