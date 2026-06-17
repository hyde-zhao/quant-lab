import pytest

from engine.research_dataset import (
    assert_no_derived_real_vwap_claim,
    attach_unsupported_claims_to_research_metadata,
)
from market_data.claims import (
    CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
    CLAIM_UNSUPPORTED_ALLOWED,
    ClaimBoundarySummary,
    resolve_microstructure_claim_boundary,
    validate_claim_boundary,
    validate_unsupported_claim_boundary,
)
from market_data.contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
)
from market_data.unsupported import (
    CAPABILITY_EXECUTION_DETAIL,
    CAPABILITY_LEVEL2_ORDER_BOOK,
    CAPABILITY_MICROSTRUCTURE_IMPACT_COST,
    CAPABILITY_MINUTE_BAR,
    CAPABILITY_ORDER_BOOK,
    CAPABILITY_ORDER_MATCH_EXECUTION,
    CAPABILITY_REAL_VWAP_EXECUTION,
    CAPABILITY_TICK_TRADE,
    CAPABILITY_VWAP_FILL_CLAIM,
    CAPABILITY_W3_SOURCE_INTERFACE,
    CR014_BASE_RELEASE_CONDITIONS,
    CR014_REAL_VWAP_RELEASE_CONDITIONS,
    CR014_UNSUPPORTED_CAPABILITY_ORDER,
    CR014_UNSUPPORTED_CAPABILITY_SET,
    CR014_UNSUPPORTED_PRODUCTION_CLAIMS,
    ERROR_CLOSE_PROXY_REAL_EXECUTION_CLAIM_ATTEMPT,
    ERROR_DERIVED_VWAP_CLAIM_ATTEMPT,
    blocked_claim_rows,
    get_cr014_unsupported_decision_matrix,
    get_unsupported_decision,
    resolve_unsupported_capabilities,
    validate_release_conditions_complete,
)


def _structured_row(claim: str = CR014_CLAIM_FULL_A_SINCE_INCEPTION) -> dict[str, object]:
    return {
        "claim": claim,
        "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
        "dataset": "prices",
        "gap_code": "candidate_unpublished",
        "evidence_path": "candidate://cr014-s05/prices",
        "remediation": "publish_current_truth_after_gate",
        "release_condition": "all P0 gates pass and explicit publish gate approves current pointer",
        "severity": "P0",
    }


def _s05_blocked_summary() -> ClaimBoundarySummary:
    return ClaimBoundarySummary(
        allowed_claims=(
            {"claim": "framework_validation", "claim_scope": "research"},
            {"claim": "real_vwap_execution", "claim_scope": "invalid_upstream_attempt"},
        ),
        blocked_claims=(_structured_row(),),
        required_missing=(
            {
                "dataset": "prices",
                "gap_code": "candidate_unpublished",
                "evidence_path": "candidate://cr014-s05/prices",
                "remediation": "publish_current_truth_after_gate",
                "release_condition": "all P0 gates pass and explicit publish gate approves current pointer",
            },
        ),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
        full_a_allowed_claim_count=0,
        status="blocked",
    )


def _s05_allowed_summary() -> ClaimBoundarySummary:
    return ClaimBoundarySummary(
        allowed_claims=(
            {
                "claim": CR014_CLAIM_FULL_A_SINCE_INCEPTION,
                "claim_scope": CLAIM_FULL_A_SINCE_INCEPTION_PRODUCTION,
            },
            {"claim": "framework_validation", "claim_scope": "research"},
            {"claim": "real_vwap_execution", "claim_scope": "invalid_upstream_attempt"},
        ),
        blocked_claims=(),
        required_missing=(),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
        full_a_allowed_claim_count=1,
        status="allowed",
    )


def test_unsupported_matrix_exact_set_release_conditions_and_zero_allowed() -> None:
    matrix = get_cr014_unsupported_decision_matrix(as_of_trade_date="2026-05-26")
    release_validation = validate_release_conditions_complete(matrix)

    assert CR014_UNSUPPORTED_CAPABILITY_ORDER == (
        CAPABILITY_W3_SOURCE_INTERFACE,
        CAPABILITY_MINUTE_BAR,
        CAPABILITY_TICK_TRADE,
        CAPABILITY_LEVEL2_ORDER_BOOK,
        CAPABILITY_ORDER_BOOK,
        CAPABILITY_ORDER_MATCH_EXECUTION,
        CAPABILITY_EXECUTION_DETAIL,
        CAPABILITY_REAL_VWAP_EXECUTION,
        CAPABILITY_VWAP_FILL_CLAIM,
        CAPABILITY_MICROSTRUCTURE_IMPACT_COST,
    )
    assert matrix.capability_set == CR014_UNSUPPORTED_CAPABILITY_SET
    assert matrix.production_allowed_claim_count == 0
    assert all(decision.production_allowed_claim is False for decision in matrix.decisions)
    assert release_validation.passed is True
    for decision in matrix.decisions:
        assert set(CR014_BASE_RELEASE_CONDITIONS).issubset(set(decision.release_condition))
    for capability in (CAPABILITY_REAL_VWAP_EXECUTION, CAPABILITY_VWAP_FILL_CLAIM):
        decision = get_unsupported_decision(capability, matrix)
        assert set(CR014_REAL_VWAP_RELEASE_CONDITIONS).issubset(set(decision.release_condition))


def test_exact_capability_resolver_does_not_use_substring_or_fuzzy_matching() -> None:
    resolved = resolve_unsupported_capabilities(
        [
            "minute",
            CAPABILITY_MINUTE_BAR,
            "level2",
            CAPABILITY_LEVEL2_ORDER_BOOK,
            "vwap",
            CAPABILITY_REAL_VWAP_EXECUTION,
        ]
    )

    assert [decision.capability for decision in resolved] == [
        CAPABILITY_MINUTE_BAR,
        CAPABILITY_LEVEL2_ORDER_BOOK,
        CAPABILITY_REAL_VWAP_EXECUTION,
    ]
    with pytest.raises(KeyError):
        get_unsupported_decision("minute")


def test_s08_boundary_appends_to_s05_blocked_claims_without_reallowing_unsupported_claims() -> None:
    merged = resolve_microstructure_claim_boundary(
        requested_claims=["real_vwap_execution", "minute_execution"],
        s05_claim_boundary=_s05_blocked_summary(),
    )
    validation = validate_unsupported_claim_boundary(merged)

    blocked_claims = {item["claim"] for item in merged.blocked_claims}
    required_capabilities = {item.get("capability") for item in merged.required_missing}
    allowed_claims = {item["claim"] for item in merged.allowed_claims}

    assert _structured_row()["claim"] in blocked_claims
    assert "real_vwap_execution" in blocked_claims
    assert "minute_execution" in blocked_claims
    assert CR014_UNSUPPORTED_CAPABILITY_SET.issubset(required_capabilities)
    assert allowed_claims.isdisjoint(CR014_UNSUPPORTED_PRODUCTION_CLAIMS)
    assert validation.passed is True
    assert {
        key: merged.permission_counters[key]
        for key in CR014_FORBIDDEN_OPERATION_COUNTERS
    } == CR014_FORBIDDEN_OPERATION_COUNTERS


def test_s08_boundary_preserves_s05_full_a_allowed_claim_while_blocking_microstructure() -> None:
    merged = resolve_microstructure_claim_boundary(s05_claim_boundary=_s05_allowed_summary())
    validation = validate_claim_boundary(merged)
    unsupported_validation = validate_unsupported_claim_boundary(merged)

    allowed_claims = {item["claim"] for item in merged.allowed_claims}
    blocked_claims = {item["claim"] for item in merged.blocked_claims}

    assert CR014_CLAIM_FULL_A_SINCE_INCEPTION in allowed_claims
    assert "framework_validation" in allowed_claims
    assert "real_vwap_execution" not in allowed_claims
    assert {"real_vwap_execution", "vwap_fill_claim", "microstructure_impact_cost"} <= blocked_claims
    assert merged.full_a_allowed_claim_count == 1
    assert validation.passed is True
    assert unsupported_validation.passed is True


def test_close_proxy_and_amount_volume_derived_vwap_are_blocked_not_real_vwap_claims() -> None:
    close_proxy = assert_no_derived_real_vwap_claim(
        execution_policy="close_proxy",
        requested_claims=["real_vwap_execution"],
    )
    amount_volume = assert_no_derived_real_vwap_claim(
        available_fields=["amount", "volume"],
        requested_claims=["real_vwap_execution"],
    )
    explicit_derived = assert_no_derived_real_vwap_claim(
        requested_claims=["derived_vwap_from_amount_volume"],
    )

    assert close_proxy["passed"] is False
    assert close_proxy["errors"][0]["code"] == ERROR_CLOSE_PROXY_REAL_EXECUTION_CLAIM_ATTEMPT
    assert amount_volume["passed"] is False
    assert amount_volume["errors"][0]["code"] == ERROR_DERIVED_VWAP_CLAIM_ATTEMPT
    assert explicit_derived["passed"] is False
    assert explicit_derived["errors"][0]["code"] == ERROR_DERIVED_VWAP_CLAIM_ATTEMPT
    with pytest.raises(ValueError, match=ERROR_DERIVED_VWAP_CLAIM_ATTEMPT):
        assert_no_derived_real_vwap_claim(
            requested_claims=["amount_volume_derived_vwap"],
            fail_on_error=True,
        )


def test_attach_unsupported_claims_to_research_metadata_preserves_upstream_claims() -> None:
    boundary = resolve_microstructure_claim_boundary(s05_claim_boundary=_s05_blocked_summary())
    metadata = attach_unsupported_claims_to_research_metadata(
        {
            "allowed_claims": ["framework_validation", "real_vwap_execution"],
            "blocked_claims": [_structured_row()],
            "required_missing": [],
            "known_limitations": [],
        },
        boundary,
    )

    blocked_claims = {item["claim"] for item in metadata["blocked_claims"]}
    required_capabilities = {item.get("capability") for item in metadata["required_missing"]}

    assert "framework_validation" in metadata["allowed_claims"]
    assert "real_vwap_execution" not in metadata["allowed_claims"]
    assert _structured_row()["claim"] in blocked_claims
    assert "real_vwap_execution" in blocked_claims
    assert CR014_UNSUPPORTED_CAPABILITY_SET.issubset(required_capabilities)
    assert metadata["production_allowed_unsupported_claim_count"] == 0
    assert metadata["real_vwap_allowed_claim_count"] == 0
    assert metadata["vwap_fill_allowed_claim_count"] == 0
    assert metadata["microstructure_allowed_claim_count"] == 0


def test_unsupported_validator_rejects_any_production_allowed_unsupported_row() -> None:
    bad_summary = ClaimBoundarySummary(
        allowed_claims=({"claim": "real_vwap_execution"},),
        blocked_claims=(
            {
                **blocked_claim_rows()[0],
                "production_allowed_claim": True,
            },
        ),
        required_missing=(),
        permission_counters=dict(CR014_FORBIDDEN_OPERATION_COUNTERS),
        full_a_allowed_claim_count=0,
    )
    result = validate_unsupported_claim_boundary(bad_summary)

    assert result.passed is False
    assert CLAIM_UNSUPPORTED_ALLOWED in result.error_codes


def test_cr014_s08_forbidden_real_operation_counters_remain_zero() -> None:
    assert CR014_FORBIDDEN_OPERATION_COUNTERS == {
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
    matrix = get_cr014_unsupported_decision_matrix()
    assert matrix.to_dict()["permission_counters"] == CR014_FORBIDDEN_OPERATION_COUNTERS
