"""CR-168 S04：C3-only Gate4 projection containment。"""

from __future__ import annotations

import inspect

import pytest

from engine.cross_strategy_reliability_gates import (
    GATE_4_CAPACITY_IMPACT,
    BlockedClaim,
    ReliabilityGateStatus,
    ReliabilityGateSummary,
)
from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import (
    GATE4_C3_ALLOWLIST,
    GATE4_C4_REASON_DENYLIST,
    GATE4_EXPECTED_C4_MISSING_CLAIMS,
    GATE4_RELEASE_PROFILE,
    project_economic_cost_to_gate4,
)
from engine.strategy_evidence import EvidenceAvailability


def _present_evidence():
    result = build_economic_cost_evidence(
        EconomicCostEvidenceInput(
            manifest_ref="fixture://manifest/gate4",
            run_ref="fixture://run/gate4",
            strategy_ref="fixture://strategy/gate4",
            package_ref="fixture://package/gate4",
            gross_pnl="100",
            performance_notional="1000",
            traded_notional="500",
            sell_notional="250",
            turnover="0.5",
            cost_model_version="fixture-cost-v1",
            fee_rate="0.001",
            fee_fixed_amount="0",
            tax_rate="0.0005",
            tax_fixed_amount="0",
            effective_spread_rate="0.0002",
            effective_slippage_rate="0.0003",
            impact_model_family="square_root",
            impact_model_version="square-root-v1",
            impact_model_ref="fixture://impact/square-root-v1",
            impact_coefficient="0.01",
            static_reference_notional="10000",
            currency="CNY",
            currency_minor_unit="0.01",
            calendar="CN-TRADING-DAY",
            price_basis="adjusted_close",
            notional_basis="market_value",
            lineage_refs=("fixture://lineage/c3",),
            provenance_refs=("fixture://provenance/c3",),
            authorization_refs=("fixture://authorization/static-only",),
            limitations=("synthetic-static-only",),
            cost_underestimation_status="PASS",
            no_real_tca_claim=True,
        )
    )
    assert result.evidence is not None
    return result.evidence


def _typed_unavailable(**extra: object) -> dict[str, object]:
    return {"availability": EvidenceAvailability.TYPED_UNAVAILABLE.value, **extra}


def _claim(claim_id: str) -> BlockedClaim:
    return BlockedClaim(claim_id, "fixture blocked", GATE_4_CAPACITY_IMPACT, "fixture only")


def test_safe_absent_b01_calls_candidate_release_and_requires_exact_c4_missing_claims() -> None:
    outcome = project_economic_cost_to_gate4(_present_evidence(), _typed_unavailable(), {})

    assert tuple(outcome.payload) == GATE4_C3_ALLOWLIST
    assert outcome.canonical_invoked is True
    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "gate4_c4_typed_unavailable"
    assert outcome.is_pass is False
    assert outcome.canonical_summary is not None
    assert outcome.canonical_summary.status is ReliabilityGateStatus.BLOCKED
    assert tuple(item.claim_id for item in outcome.canonical_summary.blocked_claims) == GATE4_EXPECTED_C4_MISSING_CLAIMS
    assert all(key not in outcome.payload for key in (*GATE4_C4_REASON_DENYLIST, "adv_participation_ref", "capacity_dollars_ref", "liquidity_sizing_refs"))


@pytest.mark.parametrize("reason_key", GATE4_C4_REASON_DENYLIST)
def test_each_c4_reason_escape_b02_is_blocked_before_canonical_call(reason_key: str) -> None:
    calls: list[dict[str, object]] = []

    def fake_validator(payload, *, release_profile, operation_counts):
        calls.append({"payload": payload, "release_profile": release_profile, "operation_counts": operation_counts})
        return ReliabilityGateSummary(GATE_4_CAPACITY_IMPACT, ReliabilityGateStatus.PASS)

    outcome = project_economic_cost_to_gate4(
        _present_evidence(),
        _typed_unavailable(**{reason_key: "C4 not built"}),
        {},
        gate4_validator=fake_validator,
    )

    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "gate4_reason_escape_rejected"
    assert outcome.canonical_invoked is False
    assert calls == []


def test_extra_mapping_never_passes_through_and_c4_ref_presence_is_rejected() -> None:
    clean = project_economic_cost_to_gate4(_present_evidence(), _typed_unavailable(untrusted_extra="ignored"), {})
    assert tuple(clean.payload) == GATE4_C3_ALLOWLIST
    assert "untrusted_extra" not in clean.payload

    c4_present = project_economic_cost_to_gate4(
        _present_evidence(),
        _typed_unavailable(adv_participation_ref=""),
        {},
    )
    assert c4_present.reason_code == "c4_present_out_of_scope"
    assert c4_present.canonical_invoked is False


def test_unavailable_c3_and_nonzero_operation_count_are_pre_call_blocked() -> None:
    unavailable = project_economic_cost_to_gate4(None, _typed_unavailable(), {})
    nonzero = project_economic_cost_to_gate4(_present_evidence(), _typed_unavailable(), {"real_lake_read": 1})

    assert unavailable.reason_code == "economic_cost_evidence_unavailable"
    assert unavailable.canonical_invoked is False
    assert nonzero.reason_code == "external_operation_forbidden"
    assert nonzero.canonical_invoked is False


def test_c4_present_is_rejected_without_canonical_call() -> None:
    outcome = project_economic_cost_to_gate4(_present_evidence(), EvidenceAvailability.PRESENT, {})

    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "c4_present_out_of_scope"
    assert outcome.canonical_invoked is False


def test_public_double_unexpected_pass_is_contained() -> None:
    observed: list[tuple[dict[str, object], str]] = []

    def fake_validator(payload, *, release_profile, operation_counts):
        observed.append((payload, release_profile))
        return ReliabilityGateSummary(GATE_4_CAPACITY_IMPACT, ReliabilityGateStatus.PASS, operation_counts=operation_counts)

    outcome = project_economic_cost_to_gate4(_present_evidence(), _typed_unavailable(), {}, gate4_validator=fake_validator)

    assert observed[0][1] == GATE4_RELEASE_PROFILE
    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "gate4_unexpected_pass"
    assert outcome.canonical_invoked is True
    assert outcome.is_pass is False


def test_public_double_missing_c4_claim_is_postcondition_violation() -> None:
    def fake_validator(payload, *, release_profile, operation_counts):
        return ReliabilityGateSummary(
            GATE_4_CAPACITY_IMPACT,
            ReliabilityGateStatus.BLOCKED,
            blocked_claims=(_claim("adv_participation_missing"), _claim("capacity_dollars_missing")),
            operation_counts=operation_counts,
        )

    outcome = project_economic_cost_to_gate4(_present_evidence(), _typed_unavailable(), {}, gate4_validator=fake_validator)

    assert outcome.status is ReliabilityGateStatus.BLOCKED
    assert outcome.reason_code == "gate4_postcondition_violation"
    assert outcome.canonical_invoked is True


def test_public_adapter_has_one_keyword_only_double_seam_and_no_private_or_aggregate_dependency() -> None:
    import engine.economic_cost_gate4_projection as module

    signature = inspect.signature(project_economic_cost_to_gate4)
    assert signature.parameters["gate4_validator"].kind is inspect.Parameter.KEYWORD_ONLY
    source = inspect.getsource(module)
    assert "_has_na_reason" not in source
    assert "strategy_admission_package" not in source
    assert source.count("validate_gate4_capacity_impact") == 2  # import + production default binding
    assert len(GATE4_C3_ALLOWLIST) == 4
    assert len(GATE4_C4_REASON_DENYLIST) == 8
