from __future__ import annotations

from market_data.benchmarks import build_benchmark_readiness_rows
from market_data.catalog import (
    CR018_ROLLBACK_DATASET_ONLY_BLOCKED,
    CR018_ROLLBACK_SCOPE_DATASET,
    build_cr018_release_rollback_contract,
)
from market_data.contracts import (
    CR017_DERIVATION_VERSION,
    CR017_SCHEMA_VERSION,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_RETURNS_ADJUSTED,
)
from market_data.dataset_groups import (
    CLAIM_INDUSTRY_NEUTRALIZED,
    REASON_P1_AUXILIARY_MISSING,
)
from market_data.publish import (
    RELEASE_READINESS_NOT_PUBLISHABLE,
    validate_release_publish_readiness_audit,
)
from market_data.validation import (
    CR018_RELEASE_AUDIT_REQUIRED_FIELDS,
    CR018_RELEASE_REASON_P0_READINESS_FAILED,
    CR018_RELEASE_REASON_QUALITY_FAILED,
    build_release_readiness_audit_report,
    validate_adjustment_publish_readiness,
    validate_benchmark_group_readiness,
    validate_lifecycle_readiness,
    validate_pit_universe_readiness,
    validate_tradability_readiness,
)


def _complete_adjustment_rows() -> list[dict[str, object]]:
    common = {
        "trade_date": "2026-01-05",
        "symbol": "000001.SZ",
        "source_run_id": "run-cr018-s06",
        "batch_id": "batch-cr018-s06",
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
            "input_snapshot_id": "snapshot-cr018-s06",
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
            "input_snapshot_id": "snapshot-cr018-s06",
        },
    ]


def _p0_readiness_rows() -> list[dict[str, object]]:
    pit = validate_pit_universe_readiness(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "effective_date": "2026-01-05",
                "available_date": "2026-01-05",
                "available_at": "2026-01-05T08:30:00+08:00",
            }
        ],
        decision_time="2026-01-05T15:00:00+08:00",
    )
    lifecycle = validate_lifecycle_readiness(
        [
            {
                "symbol": "000001.SZ",
                "list_date": "1991-04-03",
                "delist_date": "2099-12-31",
                "code_change_mapping": "none",
            }
        ],
        as_of_trade_date="2026-01-05",
    )
    tradability = validate_tradability_readiness(
        trade_status_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "is_tradable": True,
                "is_st": False,
                "is_suspended": False,
            }
        ],
        prices_limit_rows=[
            {
                "trade_date": "2026-01-05",
                "symbol": "000001.SZ",
                "limit_up": 11.0,
                "limit_down": 9.0,
            }
        ],
    )
    benchmark = validate_benchmark_group_readiness(build_benchmark_readiness_rows())
    adjustment = validate_adjustment_publish_readiness(
        _complete_adjustment_rows(),
        release_id="cr018-prod-20260528",
        legacy_qfq_baseline_ref="legacy://qfq-baseline/cr017",
    )
    return [
        pit.to_dict(),
        lifecycle.to_dict(),
        tradability.to_dict(),
        {"dataset_id": "benchmark_group", "readiness": benchmark.to_dict()},
        {"dataset_id": "adjustment_dual_view", "readiness": adjustment.to_dict()},
    ]


def _evidence_refs() -> dict[str, str]:
    return {
        "raw": "fixture://raw/cr018-prod-20260528",
        "manifest": "fixture://manifest/cr018-prod-20260528",
        "candidate": "fixture://candidate/cr018-prod-20260528",
        "quality": "fixture://quality/cr018-prod-20260528",
        "release_history": "fixture://release-history/cr018-prod-20260528",
    }


def test_release_readiness_audit_report_covers_contract_fields_and_p1_claims() -> None:
    report = build_release_readiness_audit_report(
        "cr018-prod-20260528",
        _p0_readiness_rows(),
        quality={"quality_status": "pass"},
        blocked_claims=[
            {
                "claim": CLAIM_INDUSTRY_NEUTRALIZED,
                "priority": "P1",
                "reason_code": REASON_P1_AUXILIARY_MISSING,
            }
        ],
        rollback_target={"scope": "release", "target_release_id": "cr018-prod-previous"},
        evidence_refs=_evidence_refs(),
    )
    payload = report.to_dict()

    assert set(CR018_RELEASE_AUDIT_REQUIRED_FIELDS) <= set(payload)
    assert report.publish_allowed is True
    assert report.production_publish_allowed_count == 1
    assert payload["release"]["publish_readiness_pass"] is True
    assert CLAIM_INDUSTRY_NEUTRALIZED not in payload["release"]["allowed_claims"]
    p1_claim = next(item for item in payload["blocked_claims"] if item["claim"] == CLAIM_INDUSTRY_NEUTRALIZED)
    assert p1_claim["capability_available"] is False
    assert p1_claim["core_release_blocking"] is False

    hook = validate_release_publish_readiness_audit(report)
    assert hook.publish_allowed is True
    assert hook.production_publish_allowed_count == 1
    assert hook.current_pointer_publish_allowed is False
    assert hook.current_pointer_publish_count == 0
    assert hook.real_lake_write_count == 0


def test_p0_required_missing_or_quality_fail_blocks_publish_allowed_count() -> None:
    required_missing_rows = [
        *_p0_readiness_rows(),
        {
            "dataset_id": "required_missing_fixture",
            "readiness_status": "required_missing",
            "passed": False,
            "required_missing_count": 1,
        },
    ]
    readiness_fail = build_release_readiness_audit_report(
        "cr018-prod-20260528",
        required_missing_rows,
        quality={"quality_status": "pass"},
        rollback_target={"scope": "release", "target_release_id": "cr018-prod-previous"},
        evidence_refs=_evidence_refs(),
    )
    readiness_hook = validate_release_publish_readiness_audit(readiness_fail)

    assert readiness_fail.publish_allowed is False
    assert readiness_fail.production_publish_allowed_count == 0
    assert readiness_hook.publish_allowed is False
    assert readiness_hook.production_publish_allowed_count == 0
    assert RELEASE_READINESS_NOT_PUBLISHABLE in readiness_hook.error_codes
    assert CR018_RELEASE_REASON_P0_READINESS_FAILED in {
        item["reason_code"] for item in readiness_fail.blocked_reasons
    }

    quality_fail = build_release_readiness_audit_report(
        "cr018-prod-20260528",
        _p0_readiness_rows(),
        quality={"quality_status": "fail"},
        rollback_target={"scope": "release", "target_release_id": "cr018-prod-previous"},
        evidence_refs=_evidence_refs(),
    )

    assert quality_fail.publish_allowed is False
    assert quality_fail.production_publish_allowed_count == 0
    assert CR018_RELEASE_REASON_QUALITY_FAILED in {
        item["reason_code"] for item in quality_fail.blocked_reasons
    }


def test_rollback_contract_is_release_level_and_dataset_only_is_blocked() -> None:
    dataset_only = build_cr018_release_rollback_contract(
        "cr018-prod-20260528",
        "cr018-prod-previous",
        scope=CR018_ROLLBACK_SCOPE_DATASET,
        dataset_id="prices_raw",
        reason="fixture dataset rollback must be blocked",
        operator="fixture",
        evidence_refs=_evidence_refs(),
    )
    release_level = build_cr018_release_rollback_contract(
        "cr018-prod-20260528",
        "cr018-prod-previous",
        reason="fixture release rollback contract",
        operator="fixture",
        evidence_refs=_evidence_refs(),
    )

    assert dataset_only.allowed is False
    assert CR018_ROLLBACK_DATASET_ONLY_BLOCKED in dataset_only.error_codes
    assert dataset_only.dataset_level_rollback_only_allowed_count == 0
    assert dataset_only.current_pointer_publish_count == 0
    assert all(value == 0 for value in dataset_only.historical_evidence_delete_counts.values())

    assert release_level.allowed is True
    assert release_level.rollback_target["scope"] == "release"
    assert release_level.rollback_target["release_level"] is True
    assert release_level.dataset_level_rollback_only_allowed_count == 0
    assert release_level.current_pointer_publish_count == 0


def test_historical_evidence_and_real_operation_counts_remain_zero() -> None:
    rollback = build_cr018_release_rollback_contract(
        "cr018-prod-20260528",
        "cr018-prod-previous",
        reason="fixture release rollback contract",
        operator="fixture",
        evidence_refs=_evidence_refs(),
    )
    report = build_release_readiness_audit_report(
        "cr018-prod-20260528",
        _p0_readiness_rows(),
        quality={"quality_status": "pass"},
        rollback_target=rollback.rollback_target,
        evidence_refs=_evidence_refs(),
    )
    hook = validate_release_publish_readiness_audit(report)

    assert all(value == 0 for value in report.historical_evidence_delete_counts.values())
    assert all(value == 0 for value in rollback.historical_evidence_delete_counts.values())
    assert report.operation_counts["real_lake_write"] == 0
    assert report.operation_counts["current_pointer_publish"] == 0
    assert report.operation_counts["provider_fetch"] == 0
    assert report.operation_counts["credential_read"] == 0
    assert report.operation_counts["qmt_operation"] == 0
    assert report.operation_counts["duckdb_dependency_change"] == 0
    assert hook.operation_counts == {
        "provider_fetch": 0,
        "lake_write": 0,
        "real_lake_write": 0,
        "credential_read": 0,
        "current_pointer_publish": 0,
        "catalog_current_pointer_publish": 0,
        "qmt_operation": 0,
        "duckdb_dependency_change": 0,
    }
    assert hook.current_pointer_publish_count == 0
    assert hook.real_lake_write_count == 0
