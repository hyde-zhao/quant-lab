from __future__ import annotations

import pytest

from engine.research_dataset import (
    CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN,
    CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
    CR018_S08_REASON_PROXY_INPUT_FORBIDDEN,
    CR018_S08_REASON_REQUIRED_MISSING,
    CR018_S08_STATUS_BLOCKED,
    CR018_S08_STATUS_PASS,
    load_production_current_truth_dataset,
)
from engine.production_current_truth_rerun import (
    RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN,
    ProductionRerunRequest,
    assert_s08_real_operation_counts_zero,
    build_qmt_admission_evidence,
    old_report_overwrite_guard,
    production_current_truth_rerun_entry,
)


RELEASE_ID = "cr018-prod-20260528"
P0_DATASET_IDS = (
    "prices",
    "adj_factor",
    "trade_calendar",
    "index_members",
    "index_weights",
    "stock_basic",
)
REAL_OPERATION_COUNTER_KEYS = (
    "old_report_overwrite",
    "provider_fetch",
    "lake_write",
    "credential_read",
    "qmt_operation",
    "candidate_read_count",
    "proxy_input_allowed_count",
    "duckdb_dependency_change",
)


def _request(**overrides: object) -> ProductionRerunRequest:
    values = {
        "release_id": RELEASE_ID,
        "strategy_set": ("factor_17_21_core", "stage_5_risk_overlay"),
        "research_phases": ("phase_3", "phase_4", "phase_5"),
        "research_adjustment_policy": "qfq",
        "benchmark_policy": "hs300_required",
        "as_of_trade_date": "2026-05-28",
        "report_target": f"reports/production_current_truth/{RELEASE_ID}/dry-run/rerun-report.json",
        "run_id": "dry-run",
        "release_scope": {"coverage_start": "2015-01-05", "coverage_end": "2026-05-28"},
    }
    values.update(overrides)
    return ProductionRerunRequest(**values)


def _release_metadata(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "release_id": RELEASE_ID,
        "status": "published",
        "published": True,
        "release_scope": {"coverage_start": "2015-01-05", "coverage_end": "2026-05-28"},
        "as_of_trade_date": "2026-05-28",
    }
    values.update(overrides)
    return values


def _current_truth_metadata(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "release_id": RELEASE_ID,
        "status": "published_current_truth",
        "published": True,
        "release_scope": {"coverage_start": "2015-01-05", "coverage_end": "2026-05-28"},
        "as_of_trade_date": "2026-05-28",
        "benchmark": {"benchmark_id": "hs300", "status": "available", "policy": "hs300_required"},
        "pit_universe": {"status": "available", "asof_join": "pass"},
        "tradability": {"status": "available", "trade_status": "pass", "price_limit": "pass"},
        "adjustment_policy": "qfq",
        "blocked_claims": [],
        "required_missing": [],
    }
    values.update(overrides)
    return values


def _current_reader_result(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "schema_name": "cr018.current_reader_smoke.v1",
        "status": "pass",
        "release_id": RELEASE_ID,
        "dataset_group": "p0",
        "datasets": list(P0_DATASET_IDS),
        "covered_datasets": list(P0_DATASET_IDS),
        "row_counts": {dataset_id: index + 10 for index, dataset_id in enumerate(P0_DATASET_IDS)},
        "policy_metadata": {
            "read_source": "published_current_pointer",
            "published_current_pointer_only": True,
            "candidate_fallback_allowed": False,
            "p0_dataset_group_covered": True,
        },
        "candidate_fallback_blocked": False,
        "candidate_read_count": 0,
        "unpublished_lake_scan_count": 0,
        "operation_counts": {key: 0 for key in REAL_OPERATION_COUNTER_KEYS},
    }
    values.update(overrides)
    return values


def _research_results(status: str = "pass") -> dict[str, object]:
    return {
        "status": status,
        "metrics": {"annual_return": 0.12, "max_drawdown": -0.08, "ic_mean": 0.04},
        "evidence_paths": {"factor_panel": "fixture://research/factor-panel"},
    }


def _old_baseline() -> dict[str, object]:
    return {
        "proxy_baseline": True,
        "fixed_baseline": True,
        "metrics": {"annual_return": 0.09, "max_drawdown": -0.11, "ic_mean": 0.02},
    }


def _run_entry(**overrides: object) -> dict[str, object]:
    values = {
        "request": _request(),
        "release_metadata": _release_metadata(),
        "current_truth_metadata": _current_truth_metadata(),
        "current_reader_result": _current_reader_result(),
        "research_results_fixture": _research_results(),
        "old_baseline_fixture": _old_baseline(),
    }
    values.update(overrides)
    return production_current_truth_rerun_entry(**values)


def _reason_codes(payload: dict[str, object]) -> set[str]:
    return {
        str(item["reason_code"])
        for item in payload.get("blocked_reasons", [])
        if isinstance(item, dict) and item.get("reason_code")
    }


def _assert_required_counts_zero(payload: dict[str, object]) -> None:
    counts = dict(payload.get("operation_counts") or payload)
    assert {key: counts.get(key, 0) for key in REAL_OPERATION_COUNTER_KEYS} == {
        key: 0 for key in REAL_OPERATION_COUNTER_KEYS
    }
    assert_s08_real_operation_counts_zero(payload)


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        (
            {"release_metadata": _release_metadata(status="candidate_unpublished", published=False)},
            CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
        ),
        (
            {"current_reader_result": _current_reader_result(status="catalog_not_published")},
            CR018_S08_REASON_CATALOG_NOT_PUBLISHED,
        ),
        (
            {"required_missing": [{"dataset_id": "index_members", "reason_code": "required_missing"}]},
            CR018_S08_REASON_REQUIRED_MISSING,
        ),
        (
            {"candidate_path": "fixture://candidate/cr018-prod-20260528/prices"},
            CR018_S08_REASON_CANDIDATE_INPUT_FORBIDDEN,
        ),
        (
            {"proxy_input": {"baseline": "reports/experiment_17_21/benchmark_proxy_equity_curve.csv"}},
            CR018_S08_REASON_PROXY_INPUT_FORBIDDEN,
        ),
        (
            {"provider_raw_fallback": True},
            "provider_fetch_forbidden",
        ),
    ],
)
def test_unpublished_missing_required_candidate_proxy_and_provider_fallback_are_blocked(
    overrides: dict[str, object],
    expected_reason: str,
) -> None:
    report = _run_entry(**overrides)

    assert report["status"] == CR018_S08_STATUS_BLOCKED
    assert report["pass"] is False
    assert report["production_rerun_allowed_count"] == 0
    assert report["qmt_admission_evidence"]["qmt_admission_allowed_count"] == 0
    assert expected_reason in _reason_codes(report)
    _assert_required_counts_zero(report)


def test_production_current_truth_loader_reads_only_published_current_reader_metadata() -> None:
    dataset = load_production_current_truth_dataset(
        RELEASE_ID,
        release_metadata=_release_metadata(),
        current_truth_metadata=_current_truth_metadata(),
        current_reader_result=_current_reader_result(),
    )

    assert dataset["status"] == CR018_S08_STATUS_PASS
    assert dataset["allowed_count"] == 1
    assert dataset["read_source"] == "published_current_pointer"
    assert dataset["published_current_pointer_only"] is True
    assert dataset["candidate_fallback_allowed"] is False
    assert dataset["proxy_input_allowed"] is False
    assert dataset["current_reader_metadata"]["policy_metadata"]["read_source"] == "published_current_pointer"
    assert dataset["candidate_read_count"] == 0
    assert dataset["proxy_input_allowed_count"] == 0
    _assert_required_counts_zero(dataset)


def test_rerun_report_payload_records_release_scope_policies_baseline_diff_and_pass() -> None:
    report = _run_entry()

    assert report["schema_name"] == "cr018.production_current_truth_rerun_report.v1"
    assert report["mode"] == "fixture_dry_run"
    assert report["real_stage_3_to_5_execution"] is False
    assert report["release_id"] == RELEASE_ID
    assert report["release_scope"]["coverage_start"] == "2015-01-05"
    assert report["as_of_trade_date"] == "2026-05-28"
    assert report["benchmark"]["benchmark_id"] == "hs300"
    assert report["pit_universe"]["status"] == "available"
    assert report["tradability"]["trade_status"] == "pass"
    assert report["adjustment_policy"] == "qfq"
    assert report["old_proxy_fixed_baseline_diff"]["old_proxy_baseline_present"] is True
    assert report["old_proxy_fixed_baseline_diff"]["old_fixed_baseline_present"] is True
    assert report["old_proxy_fixed_baseline_diff"]["old_proxy_or_fixed_input_allowed"] is False
    assert report["status"] == CR018_S08_STATUS_PASS
    assert report["pass"] is True
    assert report["fail"] is False
    assert report["qmt_admission_evidence"]["qmt_admission_allowed_count"] == 1
    _assert_required_counts_zero(report)


def test_s08_not_pass_blocks_qmt_admission_allowed_count() -> None:
    report = _run_entry(research_results_fixture=_research_results(status="fail"))
    evidence = build_qmt_admission_evidence(report)

    assert report["status"] == "fail"
    assert report["pass"] is False
    assert evidence["allowed"] is False
    assert evidence["qmt_admission_allowed_count"] == 0
    assert evidence["qmt_operation"] == 0
    _assert_required_counts_zero(report)


def test_old_report_overwrite_is_blocked_or_unique_target_is_returned() -> None:
    old_target = "reports/experiment_17_21/factor_strategy_report.md"
    guard = old_report_overwrite_guard(
        old_target,
        existing_report_targets=[old_target],
        release_id=RELEASE_ID,
        run_id="dry-run",
    )

    assert guard["status"] == CR018_S08_STATUS_BLOCKED
    assert guard["reason_code"] == RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN
    assert guard["old_report_overwrite"] == 0
    assert guard["overwrite_allowed"] is False
    assert guard["unique_target"] != old_target
    _assert_required_counts_zero(guard)

    unique_guard = old_report_overwrite_guard(
        f"reports/production_current_truth/{RELEASE_ID}/dry-run/rerun-report.json",
        existing_report_targets=[old_target],
        release_id=RELEASE_ID,
        run_id="dry-run",
    )
    assert unique_guard["status"] == "unique_target"
    assert unique_guard["target_unique"] is True
    assert unique_guard["old_report_overwrite"] == 0
    _assert_required_counts_zero(unique_guard)


def test_old_report_overwrite_conflict_blocks_rerun_report_without_overwriting() -> None:
    target = f"reports/production_current_truth/{RELEASE_ID}/dry-run/rerun-report.json"
    report = _run_entry(existing_report_targets=[target])

    assert report["status"] == CR018_S08_STATUS_BLOCKED
    assert RERUN_REASON_OLD_REPORT_OVERWRITE_FORBIDDEN in _reason_codes(report)
    assert report["report_target"]["guard"]["old_report_overwrite"] == 0
    assert report["qmt_admission_evidence"]["qmt_admission_allowed_count"] == 0
    _assert_required_counts_zero(report)
