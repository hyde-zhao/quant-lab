"""CR-168 不能提升 CR-155 admission package。"""

from __future__ import annotations

import json
from pathlib import Path

from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import project_economic_cost_to_gate4
from engine.strategy_admission_package import attach_walk_forward_oos_evidence
from engine.strategy_evidence import EvidenceAvailability
from tests.research.walk_forward_oos_test_support import passing_component


def _cr155_package() -> dict[str, object]:
    return {
        "package_id": "synthetic-cr155-c3",
        "package_status": "BLOCKED",
        "admission_status": "blocked",
        "paper_candidate": False,
        "evidence_refs": (),
        "blocked_reasons": ({"code": "CR155_BASELINE_BLOCKED", "severity": "blocker"},),
        "limitations": ("historical_evidence_unavailable",),
        "not_authorized_counters": {},
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }


def _c3_component():
    root = Path(__file__).parents[2]
    fixture = json.loads((root / "tests" / "fixtures" / "economic_cost" / "daily_multifactor_synthetic.json").read_text(encoding="utf-8"))
    result = build_economic_cost_evidence(EconomicCostEvidenceInput(**fixture["input"]))
    assert result.evidence is not None
    return result.evidence


def test_cr155_remains_blocked_when_c2_is_present_and_c3_is_only_gate4_safe_absent() -> None:
    package = attach_walk_forward_oos_evidence(_cr155_package(), passing_component())
    outcome = project_economic_cost_to_gate4(_c3_component(), EvidenceAvailability.TYPED_UNAVAILABLE, {})

    assert package["package_status"] == "BLOCKED"
    assert package["admission_status"] == "blocked"
    assert package["paper_candidate"] is False
    assert package.get("historical_backfill_count", 0) == 0
    assert outcome.status.name == "BLOCKED"
    assert outcome.is_pass is False
    assert outcome.canonical_summary is not None
    assert {claim.claim_id for claim in outcome.canonical_summary.blocked_claims} == {
        "adv_participation_missing", "capacity_dollars_missing", "liquidity_sizing_missing"
    }


def test_cr155_promotion_and_final_aggregate_integration_are_not_implemented_by_cr168() -> None:
    root = Path(__file__).parents[2]
    source = (root / "engine" / "economic_cost_gate4_projection.py").read_text(encoding="utf-8")
    assert "strategy_admission_package" not in source
    assert "attach_walk_forward_oos_evidence" not in source
    assert _cr155_package()["paper_candidate"] is False
