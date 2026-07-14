"""CR-168 S03：C3 component 与 CR-166 neutral envelope 的兼容性。"""

from dataclasses import replace

from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.strategy_evidence import (
    ComponentCatalogStatus,
    ComponentDescriptor,
    EvidenceAvailability,
    build_strategy_evidence_envelope,
    component_catalog_status,
    validate_strategy_evidence_envelope,
)


def _input(**changes: object) -> EconomicCostEvidenceInput:
    values: dict[str, object] = {
        "manifest_ref": "fixture://manifest/daily",
        "run_ref": "fixture://run/daily",
        "strategy_ref": "fixture://strategy/daily",
        "package_ref": "fixture://package/daily",
        "gross_pnl": "100", "performance_notional": "1000", "traded_notional": "500", "sell_notional": "250", "turnover": "0.5",
        "cost_model_version": "fixture-cost-v1", "fee_rate": "0.001", "fee_fixed_amount": "0", "tax_rate": "0.0005", "tax_fixed_amount": "0",
        "effective_spread_rate": "0.0002", "effective_slippage_rate": "0.0003", "impact_model_family": "square_root", "impact_model_version": "square-root-v1", "impact_model_ref": "fixture://impact/square-root-v1", "impact_coefficient": "0.01", "static_reference_notional": "10000",
        "currency": "CNY", "currency_minor_unit": "0.01", "calendar": "CN-TRADING-DAY", "price_basis": "adjusted_close", "notional_basis": "market_value",
        "lineage_refs": ("fixture://lineage/c3",), "provenance_refs": ("fixture://provenance/c3",), "authorization_refs": ("fixture://authorization/static-only",), "limitations": ("synthetic-static-only",), "cost_underestimation_status": "PASS", "no_real_tca_claim": True,
    }
    values.update(changes)
    return EconomicCostEvidenceInput(**values)


def _envelope(result, subject: str, package: str):
    assert result.evidence is not None
    component = result.evidence
    return build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref=subject,
        components=(ComponentDescriptor(component_type="economic_cost", component_schema_version="v1", required=False, component_ref=component.component_ref, component_hash=component.component_hash, availability=EvidenceAvailability.PRESENT),),
        logical_provenance={"package_ref": package, "run_ref": f"fixture://run/{subject.rsplit('/', 1)[-1]}"},
        authorization_summary={"mode": "fixture-static", "authorization_ref": "fixture://authorization/static-only"},
        limitations=("fixture_static_only", "no_real_tca"),
    )


def test_c3_catalog_is_active_while_c4_stays_reserved() -> None:
    assert component_catalog_status("economic_cost", "v1") is ComponentCatalogStatus.ACTIVE
    assert component_catalog_status("capacity_liquidity", "reserved") is ComponentCatalogStatus.RESERVED
    assert component_catalog_status("economic_cost", "reserved") is ComponentCatalogStatus.UNKNOWN


def test_daily_ml_share_component_hash_but_not_envelope_identity() -> None:
    daily = build_economic_cost_evidence(_input())
    ml = build_economic_cost_evidence(_input(manifest_ref="fixture://manifest/ml", run_ref="fixture://run/ml", strategy_ref="fixture://strategy/ml", package_ref="fixture://package/ml"))
    assert daily.evidence is not None and ml.evidence is not None
    assert daily.evidence.component_hash == ml.evidence.component_hash
    daily_envelope = _envelope(daily, "strategy://daily", "fixture://package/daily")
    ml_envelope = _envelope(ml, "strategy://ml", "fixture://package/ml")
    assert daily_envelope.envelope_hash != ml_envelope.envelope_hash
    assert validate_strategy_evidence_envelope(daily_envelope).availability is EvidenceAvailability.PRESENT
    assert validate_strategy_evidence_envelope(ml_envelope).availability is EvidenceAvailability.PRESENT


def test_attachment_identity_tamper_with_stale_envelope_hash_is_blocked() -> None:
    result = build_economic_cost_evidence(_input())
    envelope = _envelope(result, "strategy://daily", "fixture://package/daily")
    tampered = replace(envelope, subject_ref="strategy://tampered")
    assert validate_strategy_evidence_envelope(tampered).availability is EvidenceAvailability.BLOCKED
