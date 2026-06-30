from market_data.benchmarks import (
    build_benchmark_claim_boundary,
    build_benchmark_readiness_rows,
    list_benchmark_dataset_requirements,
    list_required_benchmarks,
)
from market_data.contracts import (
    CR018_BENCHMARK_BLOCKED_CLAIMS,
    CR018_BENCHMARK_CSI_ALL_SHARE,
    CR018_BENCHMARK_DATASET_COMPONENTS,
    CR018_BENCHMARK_DATASET_PRICES,
    CR018_BENCHMARK_DATASET_TYPES,
    CR018_BENCHMARK_DATASET_WEIGHTS,
    CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS,
    CR018_BENCHMARK_HS300,
    CR018_BENCHMARK_IDS,
    CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT,
    CR018_BENCHMARK_REASON_COMPONENTS_MISSING,
    CR018_BENCHMARK_REASON_PROXY_USED_AS_REAL,
    CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH,
    CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
    CR018_BENCHMARK_ZZ1000,
)
from market_data.validation import (
    validate_benchmark_components_weights_pit,
    validate_benchmark_group_readiness,
)


def test_required_benchmark_registry_and_4x3_requirements_are_p0() -> None:
    benchmarks = list_required_benchmarks()
    requirements = list_benchmark_dataset_requirements()

    assert {item.benchmark_id for item in benchmarks} == set(CR018_BENCHMARK_IDS)
    assert len(requirements) == 12
    assert {
        (item.benchmark_id, item.dataset_type)
        for item in requirements
    } == {
        (benchmark_id, dataset_type)
        for benchmark_id in CR018_BENCHMARK_IDS
        for dataset_type in CR018_BENCHMARK_DATASET_TYPES
    }
    assert all(item.required_for_publish for item in requirements)
    assert {item.dataset_type for item in requirements} == {
        CR018_BENCHMARK_DATASET_PRICES,
        CR018_BENCHMARK_DATASET_COMPONENTS,
        CR018_BENCHMARK_DATASET_WEIGHTS,
    }


def test_complete_benchmark_readiness_allows_real_claims_with_zero_operations() -> None:
    result = validate_benchmark_group_readiness(build_benchmark_readiness_rows())
    boundary = build_benchmark_claim_boundary(
        result,
        proxy_usage_metadata={
            "benchmark_kind": "proxy_baseline",
            "proxy_baseline": {"kind": "same_universe_equal_weight_buy_and_hold"},
            "proxy_annual_return": 0.08,
        },
    )

    assert result.passed is True
    assert result.release_blocked is False
    assert len(result.rows) == 12
    assert result.required_missing == ()
    assert set(result.allowed_claims) == set(CR018_BENCHMARK_BLOCKED_CLAIMS)
    assert result.production_excess_return_allowed_count == 1
    assert result.index_enhancement_allowed_count == 1
    assert result.tracking_error_allowed_count == 1
    assert result.operation_counts == dict(CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS)
    assert all(value == 0 for value in result.operation_counts.values())

    assert boundary.real_benchmark_claim_allowed is True
    assert boundary.proxy_as_real_count == 0
    assert boundary.proxy_fields_used_as_real_count == 0
    assert boundary.blocked_claims == ()
    assert boundary.operation_counts == dict(CR018_BENCHMARK_FORBIDDEN_OPERATION_COUNTERS)
    assert all(value == 0 for value in boundary.operation_counts.values())


def test_missing_any_benchmark_dataset_blocks_real_excess_enhancement_and_tracking_error() -> None:
    rows = build_benchmark_readiness_rows(
        missing=((CR018_BENCHMARK_ZZ1000, CR018_BENCHMARK_DATASET_WEIGHTS),)
    )
    result = validate_benchmark_group_readiness(rows)
    boundary = build_benchmark_claim_boundary(result)

    assert result.passed is False
    assert result.release_blocked is True
    assert result.allowed_claims == ()
    assert result.production_excess_return_allowed_count == 0
    assert result.index_enhancement_allowed_count == 0
    assert result.tracking_error_allowed_count == 0
    assert {
        (item["benchmark_id"], item["dataset_type"], item["reason_code"])
        for item in result.required_missing
    } == {
        (
            CR018_BENCHMARK_ZZ1000,
            CR018_BENCHMARK_DATASET_WEIGHTS,
            CR018_BENCHMARK_REASON_WEIGHTS_MISSING,
        )
    }
    assert {item["claim"] for item in result.blocked_claims} == set(CR018_BENCHMARK_BLOCKED_CLAIMS)
    assert boundary.real_benchmark_claim_allowed is False
    assert boundary.allowed_claims == ()
    assert boundary.required_missing_count == 1


def test_missing_entire_benchmark_blocks_claims_even_when_hs300_is_ready() -> None:
    rows = tuple(
        row
        for row in build_benchmark_readiness_rows()
        if row["benchmark_id"] != CR018_BENCHMARK_CSI_ALL_SHARE
    )
    result = validate_benchmark_group_readiness(rows)

    assert result.passed is False
    assert result.production_excess_return_allowed_count == 0
    assert result.index_enhancement_allowed_count == 0
    assert result.tracking_error_allowed_count == 0
    assert len(result.required_missing) == 3
    assert {
        item["dataset_type"] for item in result.required_missing
    } == set(CR018_BENCHMARK_DATASET_TYPES)
    assert {item["claim"] for item in result.blocked_claims} == set(CR018_BENCHMARK_BLOCKED_CLAIMS)


def test_current_component_snapshot_and_weights_only_do_not_pass_pit_membership() -> None:
    snapshot_components = (
        {
            "benchmark_id": CR018_BENCHMARK_HS300,
            "symbol": "000001.SZ",
            "is_member": True,
            "is_current_snapshot": True,
            "snapshot_asof": "2026-05-28",
        },
    )
    pit_weights = (
        {
            "benchmark_id": CR018_BENCHMARK_HS300,
            "symbol": "000001.SZ",
            "weight": 0.1,
            "effective_date": "2026-05-28",
            "available_at": "2026-05-29T00:00:00+08:00",
        },
    )
    snapshot_result = validate_benchmark_components_weights_pit(
        snapshot_components,
        pit_weights,
        benchmark_ids=(CR018_BENCHMARK_HS300,),
    )

    assert snapshot_result.passed is False
    assert CR018_BENCHMARK_REASON_COMPONENT_CURRENT_SNAPSHOT_NOT_PIT in snapshot_result.error_codes

    weights_only_result = validate_benchmark_components_weights_pit(
        (),
        pit_weights,
        benchmark_ids=(CR018_BENCHMARK_HS300,),
    )
    assert weights_only_result.passed is False
    assert CR018_BENCHMARK_REASON_COMPONENTS_MISSING in weights_only_result.error_codes

    mismatch_result = validate_benchmark_components_weights_pit(
        (
            {
                "benchmark_id": CR018_BENCHMARK_HS300,
                "symbol": "000001.SZ",
                "is_member": True,
                "effective_date": "2026-05-28",
                "available_at": "2026-05-29T00:00:00+08:00",
            },
        ),
        (
            {
                "benchmark_id": CR018_BENCHMARK_HS300,
                "symbol": "000002.SZ",
                "weight": 0.1,
                "effective_date": "2026-05-28",
                "available_at": "2026-05-29T00:00:00+08:00",
            },
        ),
        benchmark_ids=(CR018_BENCHMARK_HS300,),
    )
    assert mismatch_result.passed is False
    assert CR018_BENCHMARK_REASON_WEIGHT_MEMBERSHIP_MISMATCH in mismatch_result.error_codes


def test_proxy_benchmark_never_writes_real_fields_or_allows_proxy_as_real() -> None:
    result = validate_benchmark_group_readiness(build_benchmark_readiness_rows())

    clean_boundary = build_benchmark_claim_boundary(
        result,
        proxy_usage_metadata={
            "benchmark_kind": "proxy_baseline",
            "proxy_baseline": {"kind": "same_universe_equal_weight_buy_and_hold"},
            "proxy_total_return": 0.12,
        },
    )
    assert clean_boundary.proxy_as_real_count == 0
    assert clean_boundary.real_benchmark_claim_allowed is True

    invalid_boundary = build_benchmark_claim_boundary(
        result,
        proxy_usage_metadata={
            "benchmark_kind": "proxy_baseline",
            "proxy_baseline": {"kind": "same_universe_equal_weight_buy_and_hold"},
            "benchmark_total_return": 0.12,
            "real_benchmark_id": CR018_BENCHMARK_HS300,
        },
    )
    assert invalid_boundary.real_benchmark_claim_allowed is False
    assert invalid_boundary.proxy_as_real_count == 2
    assert CR018_BENCHMARK_REASON_PROXY_USED_AS_REAL in {
        item["reason_code"] for item in invalid_boundary.blocked_claims
    }
    assert invalid_boundary.allowed_claims == ()
