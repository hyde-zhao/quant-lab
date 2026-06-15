"""本地日频研究工具的共享契约常量。

本模块只定义字段、状态和值列表，不执行 I/O、不访问网络，也不导入运行时依赖。
"""

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
)
