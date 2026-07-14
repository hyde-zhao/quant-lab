"""CR-168 S01：C3 合同、身份分域和 fail-closed 输入校验。"""

from dataclasses import replace

import pytest

from engine.economic_cost_evidence import (
    EconomicCostEvidenceInput,
    economic_cost_semantic_hash,
    normalize_economic_cost_input,
    prepare_economic_cost_validation,
    validate_economic_cost_input,
    validate_economic_cost_semantic_hash,
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


def _codes(value: EconomicCostEvidenceInput) -> list[str]:
    normalized, _ = normalize_economic_cost_input(value)
    return [issue.code for issue in validate_economic_cost_input(normalized).issues]


def test_valid_nine_family_input_forms_typed_s01_result() -> None:
    result = prepare_economic_cost_validation(_valid_input())

    assert result.availability is EvidenceAvailability.PRESENT
    assert result.issues == ()
    assert result.attachment_context.strategy_ref == "fixture://strategy/daily"
    assert result.normalized_input.semantic_projection()["performance"]["gross_pnl"] == "100"


@pytest.mark.parametrize(
    ("changes", "expected_code", "expected_availability"),
    [
        ({"gross_pnl": None, "gross_return": None}, "c3_gross_performance_basis_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"traded_notional": None}, "c3_trade_turnover_notional_basis_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"cost_model_version": ""}, "c3_cost_model_version_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"effective_slippage_rate": None}, "c3_cost_model_version_missing", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"fee_rate": float("nan")}, "c3_nonfinite_numeric_invalid", EvidenceAvailability.BLOCKED),
        ({"fee_rate": "-0.01"}, "c3_negative_cost_invalid", EvidenceAvailability.BLOCKED),
        ({"cost_price_basis": "unadjusted_close"}, "c3_unit_price_notional_basis_mismatch", EvidenceAvailability.BLOCKED),
        ({"cost_currency": "USD"}, "c3_currency_price_calendar_mismatch", EvidenceAvailability.BLOCKED),
        ({"gross_return": "0.2"}, "c3_gross_cost_net_arithmetic_mismatch", EvidenceAvailability.BLOCKED),
        ({"authorization_refs": ()}, "c3_lineage_provenance_authorization_missing_or_mismatch", EvidenceAvailability.TYPED_UNAVAILABLE),
        ({"claimed_semantic_hash": "sha256:tampered"}, "c3_component_hash_tampered", EvidenceAvailability.BLOCKED),
    ],
)
def test_n01_to_n10_fail_closed_matrix(
    changes: dict[str, object], expected_code: str, expected_availability: EvidenceAvailability
) -> None:
    result = prepare_economic_cost_validation(_valid_input(**changes))

    assert expected_code in [issue.code for issue in result.issues]
    assert result.availability is expected_availability


@pytest.mark.parametrize("minor_unit", (None, "0", "-0.01"))
def test_missing_or_nonpositive_minor_unit_is_blocked(minor_unit: object) -> None:
    result = prepare_economic_cost_validation(_valid_input(currency_minor_unit=minor_unit))

    assert result.availability is EvidenceAvailability.BLOCKED
    assert "c3_unit_price_notional_basis_mismatch" in [issue.code for issue in result.issues]


def test_component_semantic_hash_excludes_attachment_identity_and_is_deterministic() -> None:
    daily_normalized, _ = normalize_economic_cost_input(_valid_input())
    ml_normalized, _ = normalize_economic_cost_input(
        _valid_input(
            manifest_ref="fixture://manifest/ml",
            run_ref="fixture://run/ml",
            strategy_ref="fixture://strategy/ml",
            package_ref="fixture://package/ml",
        )
    )

    hashes = {economic_cost_semantic_hash(daily_normalized) for _ in range(10)}
    assert hashes == {economic_cost_semantic_hash(ml_normalized)}
    assert len(hashes) == 1
    assert "strategy_ref" not in daily_normalized.semantic_projection()


def test_hash_tamper_is_blocked_by_explicit_self_validation() -> None:
    normalized, _ = normalize_economic_cost_input(_valid_input())
    valid_hash = economic_cost_semantic_hash(normalized)

    assert validate_economic_cost_semantic_hash(normalized, valid_hash).availability is EvidenceAvailability.PRESENT
    tampered = validate_economic_cost_semantic_hash(normalized, "sha256:tampered")
    assert tampered.availability is EvidenceAvailability.BLOCKED
    assert tampered.issues[0].code == "c3_component_hash_tampered"


def test_refs_remain_opaque_values_without_dereference() -> None:
    result = prepare_economic_cost_validation(
        _valid_input(
            lineage_refs=("https://example.invalid/lineage",),
            provenance_refs=("file:///unreadable/provenance",),
            authorization_refs=("opaque://authorization/static",),
        )
    )

    assert result.availability is EvidenceAvailability.PRESENT
    assert _codes(_valid_input()) == []
