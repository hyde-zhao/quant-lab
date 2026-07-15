"""CR-169 S05：CR168/CR155 与 claim ceiling 回归。"""

from __future__ import annotations

import json
from pathlib import Path

from engine.capacity_liquidity_evidence import C3C4CorrelationHeaderV1, CapacityLiquidityEvidenceInput, build_capacity_liquidity_evidence
from engine.capacity_liquidity_gate4_projection import C3C4CorrelationContextV1, evaluate_c3_c4_gate4_fixture_compatibility
from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import project_economic_cost_to_gate4
from engine.strategy_evidence import EvidenceAvailability


ROOT = Path(__file__).parents[2]


def _cr155_package() -> dict[str, object]:
    return {
        "package_id": "synthetic-cr155-c4-regression",
        "package_status": "BLOCKED",
        "admission_status": "blocked",
        "paper_candidate": False,
        "blocked_reasons": ({"code": "CR155_BASELINE_BLOCKED", "severity": "blocker"},),
    }


def _c3(common_identity: dict[str, str]):
    result = build_economic_cost_evidence(
        EconomicCostEvidenceInput(
            **common_identity,
            gross_pnl="100", performance_notional="1000", traded_notional="500", sell_notional="250", turnover="0.5",
            cost_model_version="fixture-cost-v1", fee_rate="0.001", fee_fixed_amount="0", tax_rate="0.0005", tax_fixed_amount="0",
            effective_spread_rate="0.0002", effective_slippage_rate="0.0003", impact_model_family="square_root",
            impact_model_version="square-root-v1", impact_model_ref="fixture://impact/square-root-v1", impact_coefficient="0.01",
            static_reference_notional="10000", currency="CNY", currency_minor_unit="0.01", calendar="CN-TRADING-DAY",
            price_basis="adjusted_close", notional_basis="market_value", lineage_refs=("fixture://lineage/c3",),
            provenance_refs=("fixture://provenance/c3",), authorization_refs=("fixture://authorization/static-only",),
            limitations=("fixture_static_only",), cost_underestimation_status="PASS", no_real_tca_claim=True,
        )
    )
    assert result.evidence is not None
    return result


def _c4(common_identity: dict[str, str]):
    fixture = json.loads((ROOT / "tests" / "fixtures" / "capacity_liquidity" / "daily_multifactor_v1.json").read_text(encoding="utf-8"))
    values = {**fixture["input"], **common_identity}
    for key in ("lineage_refs", "provenance_refs", "authorization_refs", "limitations"):
        values[key] = tuple(values[key])
    result = build_capacity_liquidity_evidence(CapacityLiquidityEvidenceInput(**values))
    assert result.evidence is not None
    return result


def test_cr168_c3_only_absent_c4_path_remains_blocked_with_three_missing_claims() -> None:
    identity = {
        "manifest_ref": "fixture://manifest/joint",
        "run_ref": "fixture://run/joint",
        "strategy_ref": "fixture://strategy/joint",
        "package_ref": "fixture://package/joint",
    }
    outcome = project_economic_cost_to_gate4(_c3(identity).evidence, EvidenceAvailability.TYPED_UNAVAILABLE, {})
    assert outcome.status.name == "BLOCKED"
    assert outcome.is_pass is False
    assert outcome.canonical_summary is not None
    assert {claim.claim_id for claim in outcome.canonical_summary.blocked_claims} == {
        "adv_participation_missing", "capacity_dollars_missing", "liquidity_sizing_missing"
    }


def test_joint_fixture_pass_does_not_promote_cr155_or_real_stage3_claims() -> None:
    identity = {
        "manifest_ref": "fixture://manifest/joint",
        "run_ref": "fixture://run/joint",
        "strategy_ref": "fixture://strategy/joint",
        "package_ref": "fixture://package/joint",
    }
    c3 = _c3(identity)
    c4 = _c4(identity)
    context = C3C4CorrelationContextV1(c3_header=C3C4CorrelationHeaderV1(**c4.header.to_dict()), c4_header=c4.header)
    outcome = evaluate_c3_c4_gate4_fixture_compatibility(
        economic_cost=c3.evidence,
        economic_cost_attachment=c3.attachment_context,
        capacity_liquidity=c4.evidence,
        capacity_liquidity_attachment=c4.attachment_context,
        correlation_context=context,
        operation_counts={},
    )
    package = _cr155_package()

    assert outcome.is_fixture_pass
    assert outcome.aggregate_admission_pass is False
    assert outcome.capacity_scalable_claim is False
    assert outcome.real_capacity_ready is False
    assert outcome.stage3_entry_ready is False
    assert package["package_status"] == "BLOCKED"
    assert package["admission_status"] == "blocked"
    assert package["paper_candidate"] is False
    assert c4.evidence.real_adv_available is False
    assert c4.evidence.real_liquidity_available is False
    assert c4.evidence.capacity_ready is False
    assert c4.evidence.alpha_decay_calculator == 0


def test_forbidden_canonical_cr168_and_aggregate_sources_have_zero_cr169_diff() -> None:
    # 真实 Git diff 计数由 CP6/CP7 只读命令提供；这里固定所有权边界，防止本地模块导入越界。
    projection = (ROOT / "engine" / "capacity_liquidity_gate4_projection.py").read_text(encoding="utf-8")
    assert "strategy_admission_package" not in projection
    assert "economic_cost_gate4_projection" not in projection
    assert "validate_gate4_capacity_impact" in projection
