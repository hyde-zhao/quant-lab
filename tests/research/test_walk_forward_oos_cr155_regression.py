from __future__ import annotations

from engine.strategy_admission_package import attach_walk_forward_oos_evidence
from tests.research.walk_forward_oos_test_support import passing_component


def test_cr155_blocked_package_cannot_be_promoted_by_passing_fixture_c2() -> None:
    package = {
        "package_id": "synthetic-cr155",
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
    attached = attach_walk_forward_oos_evidence(package, passing_component())
    assert attached["package_status"] == "BLOCKED"
    assert attached["paper_candidate"] is False
    assert attached["walk_forward_oos_evidence"]["availability"] == "present"
    assert attached.get("historical_backfill_count", 0) == 0
