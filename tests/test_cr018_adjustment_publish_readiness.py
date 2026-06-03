from __future__ import annotations

from market_data.adjustment_policy import (
    EXECUTION_REQUIRES_RAW,
    build_cr018_adjustment_publish_policy_metadata,
    cr018_adjustment_operation_counts,
)
from market_data.contracts import (
    CR017_DERIVATION_VERSION,
    CR017_SCHEMA_VERSION,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_RETURNS_ADJUSTED,
    CR018_FORBIDDEN_OPERATION_COUNTERS,
)
from market_data.readers import build_cr018_adjustment_reader_policy_metadata
from market_data.validation import (
    CR018_ADJUSTMENT_REASON_FACTOR_COVERAGE_INCOMPLETE,
    CR018_ADJUSTMENT_REASON_VIEW_REQUIRED_MISSING,
    validate_adjustment_publish_readiness,
)


def _complete_adjustment_rows() -> list[dict[str, object]]:
    common = {
        "trade_date": "2026-01-05",
        "symbol": "000001.SZ",
        "source_run_id": "run-cr018-s05",
        "batch_id": "batch-cr018-s05",
        "lineage_checksum": "sha256:fixture",
        "quality_status": "pass",
    }
    return [
        {
            **common,
            "view_id": CR017_VIEW_PRICES_RAW,
            "open": 10.0,
            "high": 10.5,
            "low": 9.8,
            "close": 10.2,
            "volume": 1000,
            "amount": 10200.0,
            "source": "fixture",
            "source_interface": "fixture_only",
            "available_at": "2026-01-05T15:30:00+08:00",
            "available_at_rule": "close_after_available_at",
        },
        {
            **common,
            "view_id": CR017_VIEW_ADJ_FACTOR,
            "adj_factor": 1.25,
            "provider_factor_direction": "forward",
            "factor_base_date_policy": "latest_factor_equals_1",
            "available_at": "2026-01-05T15:30:00+08:00",
            "as_of_trade_date": "2026-01-05",
            "factor_coverage_ratio": 1.0,
        },
        {
            **common,
            "view_id": CR017_VIEW_PRICES_QFQ,
            "schema_version": CR017_SCHEMA_VERSION,
            "derivation_version": CR017_DERIVATION_VERSION,
            "research_adjustment_policy": "qfq",
            "adjusted_open": 12.5,
            "adjusted_high": 13.125,
            "adjusted_low": 12.25,
            "adjusted_close": 12.75,
            "as_of_trade_date": "2026-01-05",
            "input_snapshot_id": "snapshot-cr018-s05",
        },
        {
            **common,
            "view_id": CR017_VIEW_PRICES_HFQ,
            "schema_version": CR017_SCHEMA_VERSION,
            "derivation_version": CR017_DERIVATION_VERSION,
            "research_adjustment_policy": "hfq",
            "adjusted_open": 8.0,
            "adjusted_high": 8.4,
            "adjusted_low": 7.84,
            "adjusted_close": 8.16,
            "base_trade_date": "2026-01-05",
            "factor_base_date_policy": "latest_factor_equals_1",
        },
        {
            **common,
            "view_id": CR017_VIEW_RETURNS_ADJUSTED,
            "schema_version": CR017_SCHEMA_VERSION,
            "derivation_version": CR017_DERIVATION_VERSION,
            "research_adjustment_policy": "returns_adjusted",
            "return_type": "close_to_close",
            "adjusted_return": 0.02,
            "start_price_ref": "prices_qfq:2026-01-02:000001.SZ",
            "end_price_ref": "prices_qfq:2026-01-05:000001.SZ",
            "input_snapshot_id": "snapshot-cr018-s05",
        },
    ]


def test_five_adjustment_readiness_fields_reach_100_percent_before_publish_allowed() -> None:
    result = validate_adjustment_publish_readiness(
        _complete_adjustment_rows(),
        release_id="cr018-s05-fixture",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    assert result.passed is True
    assert result.publish_allowed is True
    assert result.production_publish_allowed_count == 1
    assert result.readiness_field_coverage_ratio == 1.0
    assert result.factor_coverage_ratio == 1.0
    assert set(result.ready_view_ids) == {
        CR017_VIEW_PRICES_RAW,
        CR017_VIEW_ADJ_FACTOR,
        CR017_VIEW_PRICES_QFQ,
        CR017_VIEW_PRICES_HFQ,
        CR017_VIEW_RETURNS_ADJUSTED,
    }
    assert all(value == 1.0 for value in result.coverage_by_view.values())
    assert result.operation_counts["current_pointer_publish"] == 0
    assert result.operation_counts["qmt_operation"] == 0


def test_missing_adj_factor_or_incomplete_factor_coverage_blocks_publish() -> None:
    rows = [row for row in _complete_adjustment_rows() if row["view_id"] != CR017_VIEW_ADJ_FACTOR]

    result = validate_adjustment_publish_readiness(
        rows,
        release_id="cr018-s05-fixture",
        factor_coverage_ratio=0.8,
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    reasons = {item["reason_code"] for item in result.blocked_reasons}
    assert result.passed is False
    assert result.publish_allowed is False
    assert result.production_publish_allowed_count == 0
    assert result.factor_coverage_ratio == 0.8
    assert CR017_VIEW_ADJ_FACTOR in result.missing_view_ids
    assert CR018_ADJUSTMENT_REASON_VIEW_REQUIRED_MISSING in reasons
    assert CR018_ADJUSTMENT_REASON_FACTOR_COVERAGE_INCOMPLETE in reasons


def test_qmt_execution_consumer_is_raw_only_for_adjusted_views() -> None:
    adjusted_results = [
        build_cr018_adjustment_reader_policy_metadata(
            "cr018-s05-fixture",
            view_id,
            consumer_kind="qmt_execution",
            legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
        )
        for view_id in (CR017_VIEW_PRICES_QFQ, CR017_VIEW_PRICES_HFQ, CR017_VIEW_RETURNS_ADJUSTED)
    ]
    raw_result = build_cr018_adjustment_reader_policy_metadata(
        "cr018-s05-fixture",
        CR017_VIEW_PRICES_RAW,
        consumer_kind="qmt_execution",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    assert raw_result["allowed"] is True
    assert raw_result["execution_price_policy"] == "raw"
    assert {item["blocked_reason"] for item in adjusted_results} == {EXECUTION_REQUIRES_RAW}
    assert sum(int(item["allowed"]) for item in adjusted_results) == 0
    assert all(item["qmt_adjusted_execution_allowed_count"] == 0 for item in adjusted_results)
    assert all(item["qmt_operation"] == 0 for item in adjusted_results)


def test_legacy_qfq_baseline_is_readonly_and_policy_metadata_blocks_without_overwrite() -> None:
    readiness = validate_adjustment_publish_readiness(
        _complete_adjustment_rows(),
        release_id="cr018-s05-fixture",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )
    metadata = build_cr018_adjustment_publish_policy_metadata(
        "cr018-s05-fixture",
        readiness=readiness.to_dict(),
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    assert metadata["publish_allowed"] is True
    assert metadata["legacy_qfq_baseline_preserved"] is True
    assert metadata["legacy_qfq_baseline_overwrite_count"] == 0
    assert metadata["qmt_execution_price_policy"] == "raw"
    assert metadata["qmt_adjusted_execution_allowed_count"] == 0
    assert metadata["operation_counts"] == cr018_adjustment_operation_counts()


def test_reader_metadata_records_policy_view_consumer_legacy_and_blocked_reason() -> None:
    metadata = build_cr018_adjustment_reader_policy_metadata(
        "cr018-s05-fixture",
        CR017_VIEW_PRICES_QFQ,
        consumer_kind="factor_research",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    assert metadata["adjustment_policy"] == "qfq"
    assert metadata["view_kind"] == "derived_adjusted_view"
    assert metadata["consumer_kind"] == "factor_research"
    assert metadata["legacy_qfq_baseline_preserved"] is True
    assert metadata["blocked_reason"] == ""
    assert metadata["scan_unpublished_lake"] is False
    assert metadata["unpublished_lake_scan_count"] == 0


def test_forbidden_operation_counts_remain_zero() -> None:
    result = validate_adjustment_publish_readiness(
        _complete_adjustment_rows(),
        release_id="cr018-s05-fixture",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )
    reader_metadata = build_cr018_adjustment_reader_policy_metadata(
        "cr018-s05-fixture",
        CR017_VIEW_PRICES_QFQ,
        consumer_kind="factor_research",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )

    assert {key: result.operation_counts[key] for key in CR018_FORBIDDEN_OPERATION_COUNTERS} == dict(
        CR018_FORBIDDEN_OPERATION_COUNTERS
    )
    assert reader_metadata["operation_counts"]["legacy_qfq_overwrite"] == 0
    assert reader_metadata["provider_fetch"] == 0
    assert reader_metadata["lake_write"] == 0
    assert reader_metadata["credential_read"] == 0
    assert reader_metadata["current_pointer_publish"] == 0
    assert reader_metadata["qmt_operation"] == 0
    assert reader_metadata["duckdb_dependency_change"] == 0
