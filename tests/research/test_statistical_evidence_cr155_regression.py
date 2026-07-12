from __future__ import annotations

from engine.statistical_evidence import (
    EvidenceStatus,
    StatisticalMethod,
    aggregate_statistical_evidence,
    build_statistical_evidence_input,
    make_method_evidence,
)
from engine.strategy_admission_package import (
    attach_computable_statistical_evidence,
    attach_family_lineage_to_admission_package,
)


def _passing_summary():
    methods = (StatisticalMethod.BH, StatisticalMethod.WRC, StatisticalMethod.PBO_CSCV, StatisticalMethod.DSR)
    ids = ("c0", "c1", "c2", "c3")
    value = build_statistical_evidence_input(
        lineage_projection={"target_ref": "family://future-native", "target_hash": "sha256:f", "raw_trial_count": 4},
        candidate_ids=ids,
        method_inputs={method.value: {} for method in methods},
    )
    evidences = [
        make_method_evidence(
            method=method,
            evidence_input=value,
            status=EvidenceStatus.PASS,
            config={"method": method.value},
            result={"method_pass": True},
            limitations=("effective_trial_count_typed_unavailable",) if method is StatisticalMethod.DSR else (),
            evidence_ref=f"evidence://{method.value}",
        )
        for method in methods
    ]
    return aggregate_statistical_evidence(claim_id="strategy-admission", mandatory_methods=methods, evidences=evidences)


def test_cr155_without_native_lineage_stays_blocked_even_with_unrelated_passing_summary() -> None:
    package = {
        "package_id": "synthetic-cr155",
        "package_status": "PASS",
        "admission_status": "pass",
        "paper_candidate": True,
        "evidence_refs": (),
        "blocked_reasons": (),
        "limitations": (),
        "not_authorized_counters": {},
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }
    lineage_blocked = attach_family_lineage_to_admission_package(package, None)
    attached = attach_computable_statistical_evidence(lineage_blocked, _passing_summary())
    assert attached["package_status"] == "BLOCKED"
    assert attached["paper_candidate"] is False
    assert attached["family_lineage_projection"]["availability"] == "typed_unavailable"
    assert attached["computable_statistical_evidence"]["effective_trial_count"] is None
    assert attached.get("historical_backfill_count", 0) == 0
