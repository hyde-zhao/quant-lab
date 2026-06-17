import json
from pathlib import Path

from market_data.catalog import build_cr018_release_contract_metadata
from market_data.dataset_groups import (
    CLAIM_PRODUCTION_CURRENT_TRUTH,
    P1_BLOCKED_CLAIMS,
    PRIORITY_P0,
    PRIORITY_P1,
    REASON_UNREGISTERED_DATASET,
    build_release_claim_matrix,
    list_dataset_groups,
    serialize_release_readiness_summary,
)
from market_data.release_scope import (
    CLAIM_SINCE_INCEPTION_CURRENT_TRUTH,
    CR018_PRE_2015_STATUS,
    CR018_RELEASE_SCOPE_START_DATE,
    FORBIDDEN_OPERATION_COUNTER_KEYS,
    REASON_PRE_2015_FUTURE_BACKFILL,
    resolve_release_scope,
)


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_P0 = {
    "prices_raw",
    "adj_factor",
    "prices_qfq",
    "prices_hfq",
    "returns_adjusted",
    "trade_calendar",
    "pit_universe",
    "lifecycle_code_change",
    "trade_status",
    "prices_limit_st_suspend",
    "benchmark_group",
}

EXPECTED_P1 = {
    "industry_classification",
    "market_cap_total",
    "market_cap_float",
    "beta_style_factors",
    "adv",
    "turnover_rate",
    "liquidity_capacity",
    "market_impact_cost",
}


def _p0_available() -> dict[str, str]:
    return {entry.dataset_id: "available" for entry in list_dataset_groups(PRIORITY_P0)}


def test_release_scope_is_2015_to_latest_closed_trade_date_and_zero_counters() -> None:
    result = resolve_release_scope(
        "cr018-prod-20260528",
        latest_closed_trade_date="2026-05-28",
        calendar_source="fixture_trade_calendar.latest_closed",
    )

    assert result.passed is True
    assert result.release_scope is not None
    assert result.release_scope.start_date == CR018_RELEASE_SCOPE_START_DATE
    assert result.release_scope.end_date == "2026-05-28"
    assert result.release_scope.as_of_trade_date == "2026-05-28"
    assert result.release_scope.coverage_denominator_policy == "open_trade_dates_within_scoped_release"
    assert result.permission_counters == {key: 0 for key in FORBIDDEN_OPERATION_COUNTER_KEYS}
    assert all(value == 0 for value in result.permission_counters.values())


def test_pre_2015_and_since_inception_claims_are_future_backfill_blocked() -> None:
    result = resolve_release_scope(
        "cr018-prod-20260528",
        start_date="2014-01-01",
        latest_closed_trade_date="2026-05-28",
        calendar_source="fixture_trade_calendar.latest_closed",
    )

    assert result.passed is True
    assert result.release_scope is not None
    assert result.release_scope.requested_start_date == "2014-01-01"
    assert result.release_scope.start_date == "2015-01-05"
    assert result.release_scope.pre_2015_status == CR018_PRE_2015_STATUS
    assert result.release_scope.since_inception_allowed_claim_count == 0
    assert CLAIM_SINCE_INCEPTION_CURRENT_TRUTH not in {item["claim"] for item in result.allowed_claims}
    assert {
        (item["claim"], item["reason_code"], item["status"])
        for item in result.blocked_claims
    } == {
        (
            CLAIM_SINCE_INCEPTION_CURRENT_TRUTH,
            REASON_PRE_2015_FUTURE_BACKFILL,
            CR018_PRE_2015_STATUS,
        )
    }


def test_p0_p1_registry_and_required_for_publish_contract() -> None:
    p0 = list_dataset_groups(PRIORITY_P0)
    p1 = list_dataset_groups(PRIORITY_P1)

    assert {entry.dataset_id for entry in p0} == EXPECTED_P0
    assert {entry.dataset_id for entry in p1} == EXPECTED_P1
    assert all(entry.required_for_publish for entry in p0)
    assert all(entry.blocks_core_release for entry in p0)
    assert all(not entry.required_for_publish for entry in p1)
    assert all(not entry.blocks_core_release for entry in p1)


def test_p1_missing_blocks_neutralized_pure_alpha_capacity_and_scale_up_claims_only() -> None:
    matrix = build_release_claim_matrix(_p0_available(), p1_available=False)

    assert matrix.release_blocked is False
    assert CLAIM_PRODUCTION_CURRENT_TRUTH in {item["claim"] for item in matrix.allowed_claims}
    assert CLAIM_PRODUCTION_CURRENT_TRUTH not in {item["claim"] for item in matrix.blocked_claims}
    blocked_claims = {item["claim"] for item in matrix.blocked_claims}
    assert set(P1_BLOCKED_CLAIMS) <= blocked_claims
    assert all(item["reason_code"] == "p1_auxiliary_missing" for item in matrix.blocked_claims)
    assert matrix.required_missing == ()


def test_unknown_dataset_blocks_publish_readiness_and_never_passes() -> None:
    readiness = {**_p0_available(), "mystery_factor": "available"}
    matrix = build_release_claim_matrix(readiness, p1_available=True)

    assert matrix.release_blocked is True
    assert matrix.allowed_claims == ()
    assert REASON_UNREGISTERED_DATASET in matrix.error_codes
    assert matrix.unknown_datasets == ("mystery_factor",)
    assert matrix.unknown_dataset_readiness_pass_count == 0
    assert any(item["reason_code"] == REASON_UNREGISTERED_DATASET for item in matrix.required_missing)
    assert any(item["reason_code"] == REASON_UNREGISTERED_DATASET for item in matrix.blocked_claims)


def test_readiness_summary_and_catalog_metadata_are_json_ready_without_publish() -> None:
    scope = resolve_release_scope(
        "cr018-prod-20260528",
        latest_closed_trade_date="2026-05-28",
        calendar_source="fixture_trade_calendar.latest_closed",
    )
    summary = serialize_release_readiness_summary(scope, _p0_available(), p1_available=False)
    metadata = build_cr018_release_contract_metadata(
        release_scope_summary=scope,
        dataset_group_summary=summary,
        base_metadata={"existing": "kept"},
    )

    json.dumps(summary, ensure_ascii=False, sort_keys=True)
    json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    assert summary["publish_readiness_pass"] is True
    assert summary["required_for_publish"] == sorted(summary["required_for_publish"], key=summary["required_for_publish"].index)
    assert all(value == 0 for value in summary["permission_counters"].values())
    assert metadata["existing"] == "kept"
    assert metadata["current_pointer_publish_allowed"] is False
    assert metadata["current_pointer_publish_count"] == 0


def test_docs_expose_cr018_s01_scoped_release_and_blocked_claims() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "docs/USER-MANUAL.md").read_text(encoding="utf-8")
    combined = f"{readme}\n{manual}"

    assert "CR-018 S01 production current truth" in combined
    assert "2015-01-05..latest_closed_trade_date" in combined
    assert "blocked/future_backfill" in combined
    assert "P0 dataset group" in combined
    assert "P1 dataset group" in combined
    assert "neutralized" in combined
    assert "pure-alpha" in combined
    assert "capacity" in combined
    assert "scale_up" in combined
    assert "provider fetch、lake write、credential read、current pointer publish、QMT operation 计数均为 `0`" in combined
