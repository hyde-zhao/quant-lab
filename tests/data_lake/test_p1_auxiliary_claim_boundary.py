from market_data.dataset_groups import (
    CLAIM_CAPACITY_TRADABLE,
    CLAIM_CAPITAL_AMPLIFICATION,
    CLAIM_INDUSTRY_NEUTRALIZED,
    CLAIM_MARKET_CAP_NEUTRALIZED,
    CLAIM_PRODUCTION_CURRENT_TRUTH,
    CLAIM_PURE_ALPHA,
    CLAIM_SCALE_UP_READY,
    P1_BLOCKED_CLAIMS,
    REASON_P1_AUXILIARY_MISSING,
)
from market_data.readers import (
    CR018_P1_AUXILIARY_FIELD_IDS,
    build_cr018_p1_auxiliary_availability_metadata,
)
from market_data.release_scope import FORBIDDEN_OPERATION_COUNTER_KEYS
from engine.research_dataset import build_cr018_p1_claim_boundary


def test_reader_p1_metadata_covers_all_auxiliary_families_without_lake_scan() -> None:
    availability = build_cr018_p1_auxiliary_availability_metadata(
        "cr018-prod-20260528",
        {},
        release_metadata={
            "release_status": "candidate_unpublished",
            "candidate_path": "/not/read/by/this/helper",
        },
    )

    assert tuple(availability["field_ids"]) == CR018_P1_AUXILIARY_FIELD_IDS
    assert set(availability["fields"]) == {
        "industry",
        "market_cap",
        "float_market_cap",
        "beta_style",
        "adv",
        "turnover",
        "liquidity",
        "capacity",
        "impact_cost",
    }
    assert {row["dataset_id"] for row in availability["fields"].values()} == {
        "industry_classification",
        "market_cap_total",
        "market_cap_float",
        "beta_style_factors",
        "adv",
        "turnover_rate",
        "liquidity_capacity",
        "market_impact_cost",
    }
    assert all(row["available"] is False for row in availability["fields"].values())
    assert set(availability["missing_reasons"]) == set(availability["fields"])
    assert availability["p1_blocks_core_release"] is False
    assert availability["p0_core_readiness_impact"] == "none"
    assert availability["explicit_metadata_only"] is True
    assert availability["reader_policy"]["scan_unpublished_lake"] is False
    assert availability["reader_policy"]["auto_discover_candidate_lake"] is False
    assert availability["unpublished_lake_scan_count"] == 0
    assert availability["permission_counters"] == {key: 0 for key in FORBIDDEN_OPERATION_COUNTER_KEYS}


def test_p1_missing_does_not_block_core_readiness_but_blocks_auxiliary_claims() -> None:
    availability = build_cr018_p1_auxiliary_availability_metadata("cr018-prod-20260528", {})
    boundary = build_cr018_p1_claim_boundary(
        availability,
        core_readiness={
            "publish_readiness_pass": True,
            "release_blocked": False,
            "allowed_claims": [{"claim": CLAIM_PRODUCTION_CURRENT_TRUTH}],
        },
    )

    assert boundary["core_readiness"]["publish_readiness_pass"] is True
    assert boundary["p0_core_readiness_blocked"] is False
    assert boundary["core_release_blocked_by_p1"] is False
    assert CLAIM_PRODUCTION_CURRENT_TRUTH in boundary["allowed_claims"]
    assert set(P1_BLOCKED_CLAIMS).isdisjoint(boundary["allowed_claims"])
    assert set(P1_BLOCKED_CLAIMS) <= {item["claim"] for item in boundary["blocked_claims"]}
    assert {item["reason_code"] for item in boundary["blocked_claims"] if item["claim"] in P1_BLOCKED_CLAIMS} == {
        REASON_P1_AUXILIARY_MISSING
    }
    assert boundary["industry_neutral_allowed_count"] == 0
    assert boundary["market_cap_neutral_allowed_count"] == 0
    assert boundary["pure_alpha_allowed_count"] == 0
    assert boundary["capacity_allowed_count"] == 0
    assert boundary["scale_up_allowed_count"] == 0
    assert boundary["capital_amplification_allowed_count"] == 0
    assert boundary["provider_fetch"] == 0
    assert boundary["lake_write"] == 0
    assert boundary["credential_read"] == 0
    assert boundary["current_pointer_publish"] == 0
    assert boundary["qmt_operation"] == 0
    assert boundary["unpublished_lake_scan_count"] == 0


def test_complete_explicit_p1_metadata_allows_only_requested_p1_claims() -> None:
    availability = build_cr018_p1_auxiliary_availability_metadata(
        "cr018-prod-20260528",
        {
            "industry_classification": {"status": "available", "evidence_ref": "fixture://industry"},
            "market_cap_total": {"status": "available"},
            "market_cap_float": {"readiness_status": "pass"},
            "beta": "available",
            "adv20": {"status": "published"},
            "turnover_rate": {"available": True},
            "liquidity": {"status": "ready"},
            "capacity": {"status": "ok"},
            "market_impact_cost": {"status": "available"},
        },
    )
    boundary = build_cr018_p1_claim_boundary(
        availability,
        core_readiness={
            "publish_readiness_pass": True,
            "release_blocked": False,
            "allowed_claims": [CLAIM_PRODUCTION_CURRENT_TRUTH],
        },
        requested_claims=(
            CLAIM_INDUSTRY_NEUTRALIZED,
            CLAIM_MARKET_CAP_NEUTRALIZED,
            CLAIM_PURE_ALPHA,
            CLAIM_CAPACITY_TRADABLE,
            CLAIM_SCALE_UP_READY,
            CLAIM_CAPITAL_AMPLIFICATION,
        ),
    )

    assert availability["all_p1_available"] is True
    assert boundary["blocked_claims"] == []
    assert set(P1_BLOCKED_CLAIMS) <= set(boundary["allowed_claims"])
    assert boundary["industry_neutral_allowed_count"] == 1
    assert boundary["market_cap_neutral_allowed_count"] == 1
    assert boundary["pure_alpha_allowed_count"] == 1
    assert boundary["capacity_allowed_count"] == 1
    assert boundary["scale_up_allowed_count"] == 1
    assert boundary["capital_amplification_allowed_count"] == 1
