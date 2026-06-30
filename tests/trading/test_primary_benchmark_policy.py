from __future__ import annotations

import pytest

from engine.benchmark_policy import (
    BenchmarkId,
    BenchmarkReadinessStatus,
    build_benchmark_dashboard,
    build_benchmark_readiness,
    collect_benchmark_policy_safety_counters,
    reject_proxy_as_real_benchmark,
    required_stage6_benchmarks,
    select_primary_benchmark,
    serialize_benchmark_dashboard,
)


REQUIRED_ZERO_COUNTERS = {
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "credential_read",
    "qmt_api_call",
    "xtquant_import",
    "service_start",
    "dependency_change",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "simulation_or_live_run",
}


def _complete_readiness_fixture() -> dict[str, dict[str, object]]:
    return {
        benchmark.value: {
            "prices_ready": True,
            "components_ready": True,
            "weights_ready": True,
            "source_ref": f"process/checks/CP7-CR018-S03-fixture#{benchmark.value}",
            "as_of_trade_date": "2026-05-29",
        }
        for benchmark in required_stage6_benchmarks()
    }


def _readiness_rows():
    return build_benchmark_readiness(_complete_readiness_fixture())


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def test_required_benchmark_fields_cover_all_four_stage6_benchmarks() -> None:
    rows = _readiness_rows()
    dashboard = build_benchmark_dashboard(
        rows,
        select_primary_benchmark({"universe": "large_cap"}, {}, rows),
    )
    serialized = serialize_benchmark_dashboard(dashboard)

    assert tuple(required_stage6_benchmarks()) == (
        BenchmarkId.HS300,
        BenchmarkId.ZZ500,
        BenchmarkId.ZZ1000,
        BenchmarkId.CSI_ALL_SHARE,
    )
    assert {row.benchmark_id for row in rows} == set(required_stage6_benchmarks())
    assert len(rows) == 4
    assert dashboard.status == "ready"
    assert serialized["benchmark_count"] == 4
    assert all(
        row.prices_ready
        and row.components_ready
        and row.weights_ready
        and row.source_ref
        and row.as_of_trade_date == "2026-05-29"
        and row.status == BenchmarkReadinessStatus.READY
        for row in rows
    )
    _assert_zero_counters(dashboard.permission_counters)


@pytest.mark.parametrize(
    ("universe_profile", "style_profile", "expected_primary"),
    (
        ({"universe": "large_cap"}, {"style": "large_cap"}, BenchmarkId.HS300),
        ({"universe": "mid_cap"}, {"style": "mid_cap"}, BenchmarkId.ZZ500),
        ({"universe": "small_cap"}, {"style": "small_cap"}, BenchmarkId.ZZ1000),
        (
            {"universe": "all_market"},
            {"style": "broad_market"},
            BenchmarkId.CSI_ALL_SHARE,
        ),
    ),
)
def test_primary_benchmark_selection_is_deterministic_by_universe_and_style(
    universe_profile: dict[str, str],
    style_profile: dict[str, str],
    expected_primary: BenchmarkId,
) -> None:
    decision = select_primary_benchmark(
        universe_profile,
        style_profile,
        _readiness_rows(),
    )

    assert decision.primary_benchmark == expected_primary
    assert decision.status == "selected"
    assert decision.blocked is False
    assert any(expected_primary.value in item for item in decision.selection_basis)


def test_missing_readiness_blocks_without_triggering_backfill_or_publish() -> None:
    fixture = _complete_readiness_fixture()
    fixture[BenchmarkId.ZZ1000.value] = {
        "prices_ready": True,
        "components_ready": True,
        "weights_ready": False,
        "source_ref": "process/checks/CP7-CR018-S03-fixture#ZZ1000",
        "as_of_trade_date": "2026-05-29",
    }
    rows = build_benchmark_readiness(fixture)
    decision = select_primary_benchmark({"universe": "small_cap"}, {}, rows)
    dashboard = build_benchmark_dashboard(rows, decision)

    zz1000 = next(row for row in rows if row.benchmark_id == BenchmarkId.ZZ1000)
    assert zz1000.status == BenchmarkReadinessStatus.UNAVAILABLE
    assert zz1000.reason_code == "benchmark_unavailable"
    assert "weights_ready" in zz1000.missing_fields
    assert decision.primary_benchmark == "unresolved"
    assert decision.reason_code == "primary_benchmark_unresolved"
    assert dashboard.status == "blocked"
    assert "benchmark_unavailable" in dashboard.blocked_reasons
    assert "primary_benchmark_unresolved" in dashboard.blocked_reasons
    _assert_zero_counters(dashboard.permission_counters)


def test_proxy_benchmark_is_forbidden_in_real_benchmark_fields() -> None:
    clean_proxy_payload = {
        "benchmark_kind": "proxy_baseline",
        "proxy_benchmark_ref": "fixture:proxy:same-universe-equal-weight",
        "comparison_only": True,
    }
    invalid_proxy_payload = {
        "benchmark_kind": "proxy_baseline",
        "proxy_benchmark_ref": "fixture:proxy:same-universe-equal-weight",
        "real_benchmark_id": BenchmarkId.HS300.value,
        "primary_benchmark": BenchmarkId.HS300.value,
    }

    assert reject_proxy_as_real_benchmark(clean_proxy_payload) is None
    error = reject_proxy_as_real_benchmark(invalid_proxy_payload)
    assert error is not None
    assert error["reason_code"] == "proxy_benchmark_forbidden"
    assert error["proxy_as_real_count"] == 2

    rows = _readiness_rows()
    dashboard = build_benchmark_dashboard(
        rows,
        select_primary_benchmark({"universe": "large_cap"}, {}, rows),
        benchmark_payload=invalid_proxy_payload,
    )
    assert dashboard.status == "blocked"
    assert "proxy_benchmark_forbidden" in dashboard.blocked_reasons
    _assert_zero_counters(dashboard.permission_counters)


def test_conflicting_profile_or_unavailable_primary_is_unresolved_and_blocked() -> None:
    conflict = select_primary_benchmark(
        {"universe": "large_cap"},
        {"style": "small_cap"},
        _readiness_rows(),
    )

    assert conflict.primary_benchmark == "unresolved"
    assert conflict.reason_code == "primary_benchmark_unresolved"
    assert "universe_style_conflict" in conflict.blocked_reasons

    fixture = _complete_readiness_fixture()
    fixture[BenchmarkId.HS300.value]["prices_ready"] = False
    rows = build_benchmark_readiness(fixture)
    unavailable = select_primary_benchmark({"universe": "large_cap"}, {}, rows)
    dashboard = build_benchmark_dashboard(rows, unavailable)

    assert unavailable.primary_benchmark == "unresolved"
    assert unavailable.reason_code == "primary_benchmark_unresolved"
    assert "benchmark_unavailable" in unavailable.blocked_reasons
    assert dashboard.status == "blocked"
    assert "primary_benchmark_unresolved" in dashboard.blocked_reasons
    _assert_zero_counters(dashboard.permission_counters)


def test_forbidden_operation_counters_default_to_zero_and_nonzero_blocks() -> None:
    rows = _readiness_rows()
    decision = select_primary_benchmark({"universe": "all_market"}, {}, rows)
    counters = collect_benchmark_policy_safety_counters()
    clean_dashboard = build_benchmark_dashboard(rows, decision, counters)
    blocked_dashboard = build_benchmark_dashboard(
        rows,
        decision,
        {**counters, "provider_fetch": 1},
    )

    _assert_zero_counters(counters)
    assert clean_dashboard.status == "ready"
    assert blocked_dashboard.status == "blocked"
    assert "real_operation_forbidden" in blocked_dashboard.blocked_reasons
    assert blocked_dashboard.permission_counters["provider_fetch"] == 1
