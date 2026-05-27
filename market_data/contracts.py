"""market_data 静态契约常量。"""

from __future__ import annotations

SCHEMA_VERSION = "1.0"

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
)

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
}

DATASET_PIT_FIELDS: dict[str, tuple[str, ...]] = {
    DATASET_INDEX_MEMBERS: ("effective_date", "available_date", "available_at"),
    DATASET_INDEX_WEIGHTS: ("effective_date", "available_date", "available_at"),
    DATASET_STOCK_BASIC: ("effective_date", "available_date", "available_at"),
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
    "DATASETS",
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
