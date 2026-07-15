"""CR-169 S04：strict C3+C4 Gate4 fixture adapter。"""

from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from engine.capacity_liquidity_evidence import (
    C3C4CorrelationHeaderV1,
    CORRELATION_HEADER_FIELDS,
    CapacityLiquidityEvidenceInput,
    build_capacity_liquidity_evidence,
)
from engine.capacity_liquidity_gate4_projection import (
    C3C4CorrelationContextV1,
    GATE4_JOINT_PAYLOAD_KEYS,
    GATE4_RELEASE_PROFILE,
    _payload_has_reason_or_extra_escape,
    evaluate_c3_c4_gate4_fixture_compatibility,
)
from engine.cross_strategy_reliability_gates import (
    GATE_4_CAPACITY_IMPACT,
    BlockedClaim,
    ReliabilityGateStatus,
    ReliabilityGateSummary,
)
from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence


def _pair():
    common_identity = {
        "manifest_ref": "fixture://manifest/joint",
        "run_ref": "fixture://run/joint",
        "strategy_ref": "fixture://strategy/joint",
        "package_ref": "fixture://package/joint",
    }
    c3 = build_economic_cost_evidence(
        EconomicCostEvidenceInput(
            **common_identity,
            gross_pnl="100", performance_notional="1000", traded_notional="500", sell_notional="250", turnover="0.5",
            cost_model_version="fixture-cost-v1", fee_rate="0.001", fee_fixed_amount="0", tax_rate="0.0005", tax_fixed_amount="0",
            effective_spread_rate="0.0002", effective_slippage_rate="0.0003", impact_model_family="square_root", impact_model_version="square-root-v1", impact_model_ref="fixture://impact/square-root-v1", impact_coefficient="0.01", static_reference_notional="10000",
            currency="CNY", currency_minor_unit="0.01", calendar="CN-TRADING-DAY", price_basis="adjusted_close", notional_basis="market_value",
            lineage_refs=("fixture://lineage/c3",), provenance_refs=("fixture://provenance/c3",), authorization_refs=("fixture://authorization/static-only",), limitations=("fixture_static_only",), cost_underestimation_status="PASS", no_real_tca_claim=True,
        )
    )
    c4 = build_capacity_liquidity_evidence(
        CapacityLiquidityEvidenceInput(
            **common_identity,
            price_basis="adjusted_close", notional_basis="market_value", currency="CNY", calendar="CN-TRADING-DAY",
            as_of="2026-07-10", horizon_start="2026-01-01", horizon_end="2026-06-30",
            lineage_context_ref="fixture://context/lineage/shared", authorization_context_ref="fixture://context/authorization/static-only",
            synthetic_adv="1000000", requested_notional="50000", turnover_notional="250000", participation_cap="0.10", currency_minor_unit="0.01", method="static_adv_cap_v1", model_version="fixture-static-adv-cap-v1",
            lineage_refs=("fixture://lineage/c4",), provenance_refs=("fixture://provenance/c4",), authorization_refs=("fixture://authorization/static-only",), limitations=("fixture_static_only",),
        )
    )
    assert c3.evidence is not None and c4.evidence is not None
    c3_header = C3C4CorrelationHeaderV1(**c4.header.to_dict())
    context = C3C4CorrelationContextV1(c3_header=c3_header, c4_header=c4.header)
    return c3, c4, context


def _evaluate(c3, c4, context, **kwargs):
    return evaluate_c3_c4_gate4_fixture_compatibility(
        economic_cost=c3.evidence,
        economic_cost_attachment=c3.attachment_context,
        capacity_liquidity=c4.evidence,
        capacity_liquidity_attachment=c4.attachment_context,
        correlation_context=context,
        operation_counts={},
        **kwargs,
    )


def test_valid_pair_calls_public_candidate_release_with_exact_seven_keys() -> None:
    c3, c4, context = _pair()
    outcome = _evaluate(c3, c4, context)

    assert tuple(outcome.payload) == GATE4_JOINT_PAYLOAD_KEYS
    assert len(outcome.payload) == 7
    assert outcome.canonical_invocations == 1
    assert outcome.status is ReliabilityGateStatus.PASS
    assert outcome.reason_code == "gate4_fixture_contract_pass"
    assert outcome.is_fixture_pass
    assert outcome.canonical_summary is not None
    assert outcome.canonical_summary.gate_id == GATE_4_CAPACITY_IMPACT


@pytest.mark.parametrize("field_name", CORRELATION_HEADER_FIELDS)
def test_each_header_mismatch_blocks_before_canonical(field_name: str) -> None:
    c3, c4, context = _pair()
    calls: list[object] = []

    def validator(payload, *, release_profile, operation_counts):
        calls.append(payload)
        return ReliabilityGateSummary(GATE_4_CAPACITY_IMPACT, ReliabilityGateStatus.PASS, operation_counts=operation_counts)

    mismatched = replace(context.c4_header, **{field_name: f"mismatch-{field_name}"})
    outcome = _evaluate(c3, c4, replace(context, c4_header=mismatched), gate4_validator=validator)

    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "c4_c3_c4_correlation_header_mismatch"
    assert outcome.canonical_invocations == 0
    assert calls == []


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [("adv_participation_ref", ""), ("capacity_dollars_ref", ""), ("liquidity_sizing_refs", ())],
)
def test_each_c4_ref_non_present_blocks_before_canonical(field_name: str, bad_value: object) -> None:
    c3, c4, context = _pair()
    assert c4.evidence is not None
    bad_c4 = replace(c4.evidence, **{field_name: bad_value})
    c4_result = replace(c4, evidence=bad_c4)

    outcome = _evaluate(c3, c4_result, context)

    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "c4_gate4_ref_not_typed_present"
    assert outcome.canonical_invocations == 0


@pytest.mark.parametrize(
    "reason_key",
    (
        "adv_participation_ref_na_reason",
        "capacity_dollars_ref_n_a_reason",
        "liquidity_sizing_refs_na_reason",
        "na_reason",
        "n_a_reason",
        "eighth_key",
    ),
)
def test_reason_or_extra_key_is_rejected_by_local_payload_guard(reason_key: str) -> None:
    clean = {key: "typed-present" for key in GATE4_JOINT_PAYLOAD_KEYS}
    clean["liquidity_sizing_refs"] = ["typed-present"]
    injected = {**clean, reason_key: "even-empty-presence-is-forbidden"}

    assert _payload_has_reason_or_extra_escape(clean) is False
    assert _payload_has_reason_or_extra_escape(injected) is True


def test_canonical_non_pass_is_never_upgraded() -> None:
    c3, c4, context = _pair()
    claim = BlockedClaim("fixture_block", "blocked", GATE_4_CAPACITY_IMPACT, "fixture only")

    def validator(payload, *, release_profile, operation_counts):
        return ReliabilityGateSummary(
            GATE_4_CAPACITY_IMPACT,
            ReliabilityGateStatus.BLOCKED,
            blocked_claims=(claim,),
            operation_counts=operation_counts,
        )

    outcome = _evaluate(c3, c4, context, gate4_validator=validator)
    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "fixture_block"
    assert outcome.is_fixture_pass is False


def test_public_callable_double_unexpected_pass_fails_postcondition() -> None:
    c3, c4, context = _pair()

    def validator(payload, *, release_profile, operation_counts):
        assert release_profile == GATE4_RELEASE_PROFILE
        return ReliabilityGateSummary("wrong_gate", ReliabilityGateStatus.PASS, operation_counts=operation_counts)

    outcome = _evaluate(c3, c4, context, gate4_validator=validator)
    assert outcome.status == "REJECTED"
    assert outcome.reason_code == "gate4_fixture_postcondition_violation"
    assert outcome.canonical_invocations == 1


def test_nonzero_operation_count_blocks_before_canonical() -> None:
    c3, c4, context = _pair()
    outcome = evaluate_c3_c4_gate4_fixture_compatibility(
        economic_cost=c3.evidence,
        economic_cost_attachment=c3.attachment_context,
        capacity_liquidity=c4.evidence,
        capacity_liquidity_attachment=c4.attachment_context,
        correlation_context=context,
        operation_counts={"real_lake_read": 1},
    )
    assert outcome.reason_code == "external_operation_forbidden"
    assert outcome.canonical_invocations == 0


def test_claim_ceiling_and_public_protocol_seam_are_fixed() -> None:
    import engine.capacity_liquidity_gate4_projection as module

    c3, c4, context = _pair()
    outcome = _evaluate(c3, c4, context)
    assert outcome.aggregate_admission_pass is False
    assert outcome.capacity_scalable_claim is False
    assert outcome.real_capacity_ready is False
    assert outcome.stage3_entry_ready is False
    signature = inspect.signature(evaluate_c3_c4_gate4_fixture_compatibility)
    assert signature.parameters["gate4_validator"].kind is inspect.Parameter.KEYWORD_ONLY
    source = inspect.getsource(module)
    assert "strategy_admission_package" not in source
    assert "economic_cost_gate4_projection" not in source
    assert "validate_gate4_capacity_impact" in source
