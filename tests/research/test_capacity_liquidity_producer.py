"""CR-169 S02：纯 Decimal static C4 calculator 与 producer。"""

from dataclasses import replace
from decimal import Decimal

import pytest

from engine.capacity_liquidity_evidence import (
    CapacityLiquidityEvidenceInput,
    build_capacity_liquidity_evidence,
    capacity_liquidity_component_hash,
    validate_capacity_liquidity_evidence,
)
from engine.strategy_evidence import EvidenceAvailability


def _valid_input(**changes: object) -> CapacityLiquidityEvidenceInput:
    base = CapacityLiquidityEvidenceInput(
        manifest_ref="fixture://manifest/daily",
        run_ref="fixture://run/daily",
        strategy_ref="fixture://strategy/daily",
        package_ref="fixture://package/daily",
        price_basis="adjusted_close",
        notional_basis="market_value",
        currency="CNY",
        calendar="CN-TRADING-DAY",
        as_of="2026-07-10",
        horizon_start="2026-01-01",
        horizon_end="2026-06-30",
        lineage_context_ref="fixture://context/lineage/daily",
        authorization_context_ref="fixture://context/authorization/static-only",
        synthetic_adv="1000000",
        requested_notional="50000",
        turnover_notional="250000",
        participation_cap="0.10",
        currency_minor_unit="0.01",
        method="static_adv_cap_v1",
        model_version="fixture-static-adv-cap-v1",
        lineage_refs=("fixture://lineage/c4",),
        provenance_refs=("fixture://provenance/c4",),
        authorization_refs=("fixture://authorization/static-only",),
        limitations=("fixture_static_only", "no_real_adv"),
    )
    return replace(base, **changes)


def test_public_producer_calculates_exact_proxy_and_three_refs() -> None:
    result = build_capacity_liquidity_evidence(_valid_input())

    assert result.passed
    assert result.calculator_invocations == 1
    assert result.evidence is not None
    breakdown = result.evidence.breakdown
    assert breakdown.participation_ratio == Decimal("0.05")
    assert breakdown.raw_capacity_amount == Decimal("100000.00")
    assert breakdown.capacity_amount == Decimal("100000.00")
    assert breakdown.liquidity_headroom == Decimal("50000.00")
    assert breakdown.within_declared_cap is True
    assert result.evidence.adv_participation_ref.startswith("sha256:")
    assert result.evidence.capacity_dollars_ref.startswith("sha256:")
    assert len(result.evidence.liquidity_sizing_refs) == 1
    assert result.evidence.liquidity_sizing_refs[0].startswith("sha256:")
    assert validate_capacity_liquidity_evidence(result.evidence).passed


def test_input_issue_short_circuits_before_calculator() -> None:
    result = build_capacity_liquidity_evidence(_valid_input(model_version=""))

    assert result.availability is EvidenceAvailability.TYPED_UNAVAILABLE
    assert result.evidence is None
    assert result.calculator_invocations == 0
    assert [issue.code for issue in result.issues] == ["c4_proxy_model_version_missing"]


def test_ratio_at_cap_passes_and_above_cap_blocks_after_one_calculation() -> None:
    at_cap = build_capacity_liquidity_evidence(_valid_input(requested_notional="100000"))
    above = build_capacity_liquidity_evidence(_valid_input(requested_notional="100000.01"))

    assert at_cap.passed
    assert at_cap.evidence is not None
    assert at_cap.evidence.breakdown.participation_ratio == Decimal("0.10")
    assert above.availability is EvidenceAvailability.BLOCKED
    assert above.evidence is None
    assert above.calculator_invocations == 1
    assert [issue.code for issue in above.issues] == ["c4_negative_or_participation_cap_invalid"]


@pytest.mark.parametrize("cap", ("0", "-0.01", "1.01"))
def test_invalid_cap_blocks_without_calculator(cap: str) -> None:
    result = build_capacity_liquidity_evidence(_valid_input(participation_cap=cap))

    assert result.availability is EvidenceAvailability.BLOCKED
    assert result.calculator_invocations == 0
    assert "c4_negative_or_participation_cap_invalid" in [issue.code for issue in result.issues]


def test_half_even_rounding_occurs_only_at_capacity_and_headroom_outputs() -> None:
    result = build_capacity_liquidity_evidence(
        _valid_input(synthetic_adv="100.05", requested_notional="5", participation_cap="0.1")
    )

    assert result.passed
    assert result.evidence is not None
    breakdown = result.evidence.breakdown
    assert breakdown.raw_capacity_amount == Decimal("10.005")
    assert breakdown.capacity_amount == Decimal("10.00")
    assert breakdown.liquidity_headroom == Decimal("5.00")


def test_component_hash_and_ref_triplet_are_deterministic_and_tamper_fails() -> None:
    results = [build_capacity_liquidity_evidence(_valid_input()) for _ in range(10)]
    hashes = {result.evidence.component_hash for result in results if result.evidence is not None}
    triplets = {
        (
            result.evidence.adv_participation_ref,
            result.evidence.capacity_dollars_ref,
            result.evidence.liquidity_sizing_refs,
        )
        for result in results
        if result.evidence is not None
    }
    assert len(hashes) == 1
    assert len(triplets) == 1
    evidence = results[0].evidence
    assert evidence is not None
    assert capacity_liquidity_component_hash(evidence) == evidence.component_hash
    tampered = replace(evidence, capacity_dollars_ref="sha256:tampered")
    validation = validate_capacity_liquidity_evidence(tampered)
    assert validation.availability is EvidenceAvailability.BLOCKED
    assert "c4_component_or_envelope_hash_tampered" in [issue.code for issue in validation.issues]


def test_no_real_and_alpha_claim_ceiling_is_frozen() -> None:
    evidence = build_capacity_liquidity_evidence(_valid_input()).evidence

    assert evidence is not None
    assert evidence.real_adv_available is False
    assert evidence.real_liquidity_available is False
    assert evidence.capacity_ready is False
    assert evidence.alpha_decay_calculator == 0
    payload = evidence.to_dict()
    assert all("alpha_decay" not in key or key == "alpha_decay_calculator" for key in payload)
    assert payload["alpha_decay_calculator"] == 0


def test_capacity_dollars_payload_preserves_declared_currency_not_usd_assumption() -> None:
    evidence = build_capacity_liquidity_evidence(_valid_input(currency="CNY")).evidence

    assert evidence is not None
    capacity_payload = next(item for item in evidence.ref_payloads if item.kind == "capacity_dollars")
    assert capacity_payload.value["declared_currency"] == "CNY"
