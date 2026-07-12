from __future__ import annotations

import pytest

from engine.cross_strategy_reliability_gates import GATE_IDS, project_computable_statistical_evidence
from engine.statistical_evidence import (
    EvidenceStatus,
    StatisticalMethod,
    aggregate_statistical_evidence,
    build_statistical_evidence_input,
    make_method_evidence,
)
from engine.strategy_admission_package import attach_computable_statistical_evidence
from engine.strategy_admission_statistical_gate import consume_computable_statistical_evidence


METHODS = (StatisticalMethod.BH, StatisticalMethod.WRC, StatisticalMethod.PBO_CSCV, StatisticalMethod.DSR)


def _input():
    ids = tuple(f"c{index}" for index in range(4))
    return build_statistical_evidence_input(
        lineage_projection={"target_ref": "family://v1", "target_hash": "sha256:f", "raw_trial_count": 4},
        candidate_ids=ids,
        method_inputs={method.value: {} for method in METHODS},
    )


def _summary(statuses):
    value = _input()
    evidences = []
    for method, status in zip(METHODS, statuses, strict=True):
        limitations = ("effective_trial_count_typed_unavailable",) if method is StatisticalMethod.DSR else ()
        evidences.append(
            make_method_evidence(
                method=method,
                evidence_input=value,
                status=status,
                config={"method": method.value},
                result={"method_pass": status is EvidenceStatus.PASS},
                reason_codes=() if status is EvidenceStatus.PASS else (f"{method.value}_{status.value}",),
                limitations=limitations,
                evidence_ref=f"evidence://{method.value}",
            )
        )
    return aggregate_statistical_evidence(claim_id="strategy-admission", mandatory_methods=METHODS, evidences=evidences)


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ((EvidenceStatus.PASS,) * 4, "pass"),
        ((EvidenceStatus.PASS, EvidenceStatus.PASS, EvidenceStatus.FAIL, EvidenceStatus.PASS), "fail"),
        ((EvidenceStatus.PASS, EvidenceStatus.PASS, EvidenceStatus.PASS, EvidenceStatus.TYPED_UNAVAILABLE), "blocked"),
        ((EvidenceStatus.PASS, EvidenceStatus.BLOCKED, EvidenceStatus.PASS, EvidenceStatus.PASS), "blocked"),
    ],
)
def test_cr151_projection_is_conservative(statuses, expected) -> None:
    projection = consume_computable_statistical_evidence(_summary(statuses))
    assert projection["statistical_gate_status"].lower() == expected
    assert projection["effective_trial_count"] is None


def test_cr154_projection_fills_existing_slots_without_new_gate() -> None:
    projection = project_computable_statistical_evidence(_summary((EvidenceStatus.PASS,) * 4))
    artifacts = projection["artifacts"]
    assert projection["status"] == "PASS"
    assert artifacts["fdr_bh_refs"] == ("evidence://bh",)
    assert artifacts["white_reality_check_or_hansen_spa_refs"] == ("evidence://wrc",)
    assert artifacts["pbo_or_cscv_refs"] == ("evidence://pbo_cscv",)
    assert artifacts["dsr_or_sharpe_ic_deflation_refs"] == ("evidence://dsr",)
    assert artifacts["trial_count_and_effective_trials"]["effective_trial_count"] is None
    assert len(GATE_IDS) == 6


@pytest.mark.parametrize("initial", ("pass", "warn", "fail", "blocked"))
def test_package_status_never_improves(initial: str) -> None:
    package = {
        "admission_status": initial,
        "evidence_refs": (),
        "blocked_reasons": (),
        "limitations": (),
        "not_authorized_counters": {},
    }
    failed = attach_computable_statistical_evidence(
        package,
        _summary((EvidenceStatus.PASS, EvidenceStatus.FAIL, EvidenceStatus.PASS, EvidenceStatus.PASS)),
    )
    severity = {"pass": 0, "warn": 1, "fail": 2, "blocked": 3}
    assert severity[failed["admission_status"]] >= severity[initial]
    assert failed["computable_statistical_evidence"]["effective_trial_count"] is None


def test_serialized_summary_cannot_be_positive_truth() -> None:
    summary = _summary((EvidenceStatus.PASS,) * 4)
    assert consume_computable_statistical_evidence(summary.to_dict())["statistical_gate_status"] == "BLOCKED"
    assert project_computable_statistical_evidence(summary.to_dict())["status"] == "BLOCKED"
    package = attach_computable_statistical_evidence({"admission_status": "pass"}, summary.to_dict())
    assert package["admission_status"] == "blocked"
