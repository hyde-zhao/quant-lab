"""CR-168 S02：static Decimal calculator 与唯一 producer 编排测试。"""

from dataclasses import replace
from decimal import Decimal

import pytest

from engine.economic_cost_evidence import (
    EconomicCostEvidenceInput,
    build_economic_cost_evidence,
    economic_cost_component_hash,
    validate_economic_cost_evidence,
)
from engine.strategy_evidence import EvidenceAvailability


def _valid_input(**changes: object) -> EconomicCostEvidenceInput:
    base = EconomicCostEvidenceInput(
        manifest_ref="fixture://manifest/daily",
        run_ref="fixture://run/daily",
        strategy_ref="fixture://strategy/daily",
        package_ref="fixture://package/daily",
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
        limitations=("synthetic-static-only", "no-real-tca"),
        cost_underestimation_status="PASS",
        no_real_tca_claim=True,
    )
    return replace(base, **changes)


def test_public_producer_calculates_exact_static_bases_and_net_return() -> None:
    result = build_economic_cost_evidence(_valid_input())

    assert result.availability is EvidenceAvailability.PRESENT
    assert result.calculator_invocations == 1
    assert result.evidence is not None
    breakdown = result.evidence.breakdown
    assert breakdown.fee == Decimal("0.5")
    assert breakdown.tax == Decimal("0.125")
    assert breakdown.spread == Decimal("0.1")
    assert breakdown.slippage == Decimal("0.15")
    assert breakdown.impact == Decimal("500") * Decimal("0.01") * Decimal("0.05").sqrt()
    assert breakdown.total_cost == Decimal("1.99")
    assert breakdown.net_pnl == Decimal("98.01")
    assert breakdown.net_return == Decimal("0.09801")
    assert result.evidence.impact_model_family == "square_root"
    assert result.evidence.no_real_tca_claim is True
    assert validate_economic_cost_evidence(result.evidence).availability is EvidenceAvailability.PRESENT


def test_issue_path_short_circuits_before_calculator() -> None:
    result = build_economic_cost_evidence(_valid_input(effective_slippage_rate=None))

    assert result.availability is EvidenceAvailability.TYPED_UNAVAILABLE
    assert result.evidence is None
    assert result.calculator_invocations == 0
    assert [item.code for item in result.issues] == ["c3_cost_model_version_missing"]


def test_gross_return_uses_the_explicit_performance_notional() -> None:
    result = build_economic_cost_evidence(_valid_input(gross_pnl=None, gross_return="0.1"))

    assert result.passed
    assert result.evidence is not None
    assert result.evidence.breakdown.gross_pnl == Decimal("100")
    assert result.evidence.breakdown.net_return == Decimal("0.09801")


@pytest.mark.parametrize(
    ("traded_notional", "sell_notional", "turnover", "static_reference_notional", "expected_proxy"),
    [
        ("0", "0", "0", "10000", Decimal("0")),
        ("500", "250", "0.5", "500", Decimal("1")),
        ("500", "250", "0.5", "250", Decimal("2")),
    ],
)
def test_proxy_zero_one_and_above_one_are_present(
    traded_notional: str, sell_notional: str, turnover: str, static_reference_notional: str, expected_proxy: Decimal
) -> None:
    result = build_economic_cost_evidence(
        _valid_input(
            traded_notional=traded_notional,
            sell_notional=sell_notional,
            turnover=turnover,
            static_reference_notional=static_reference_notional,
        )
    )

    assert result.passed
    assert result.evidence is not None
    assert result.evidence.breakdown.participation_proxy == expected_proxy


def test_zero_static_reference_blocks_after_validated_orchestration() -> None:
    result = build_economic_cost_evidence(_valid_input(static_reference_notional="0"))

    assert result.availability is EvidenceAvailability.BLOCKED
    assert result.evidence is None
    assert result.calculator_invocations == 1
    assert result.issues[0].code == "c3_negative_cost_invalid"


def test_raw_sum_is_quantized_once_not_per_item() -> None:
    result = build_economic_cost_evidence(
        _valid_input(
            traded_notional="1",
            sell_notional="1",
            turnover="1",
            fee_rate="0.004",
            tax_rate="0.004",
            effective_spread_rate="0.004",
            effective_slippage_rate="0.004",
            impact_coefficient="0",
            static_reference_notional="1",
        )
    )

    assert result.passed
    assert result.evidence is not None
    breakdown = result.evidence.breakdown
    assert breakdown.raw_total_cost == Decimal("0.016")
    assert breakdown.total_cost == Decimal("0.02")
    assert sum(item.quantize(Decimal("0.01")) for item in (breakdown.fee, breakdown.tax, breakdown.spread, breakdown.slippage, breakdown.impact)) == Decimal("0.00")


@pytest.mark.parametrize("minor_unit", (None, "0", "-0.01"))
def test_invalid_minor_unit_is_blocked_without_calculator(minor_unit: object) -> None:
    result = build_economic_cost_evidence(_valid_input(currency_minor_unit=minor_unit))

    assert result.availability is EvidenceAvailability.BLOCKED
    assert result.calculator_invocations == 0
    assert "c3_unit_price_notional_basis_mismatch" in [item.code for item in result.issues]


def test_component_hash_is_deterministic_and_tamper_is_blocked() -> None:
    results = [build_economic_cost_evidence(_valid_input()) for _ in range(10)]
    hashes = {result.evidence.component_hash for result in results if result.evidence is not None}

    assert len(hashes) == 1
    evidence = results[0].evidence
    assert evidence is not None
    tampered = replace(evidence, component_hash="sha256:tampered")
    assert economic_cost_component_hash(evidence) == evidence.component_hash
    assert "strategy_ref" not in evidence.to_dict()
    assert "package_ref" not in evidence.to_dict()
    assert validate_economic_cost_evidence(tampered).availability is EvidenceAvailability.BLOCKED
    assert "c3_component_hash_tampered" in [item.code for item in validate_economic_cost_evidence(tampered).issues]
