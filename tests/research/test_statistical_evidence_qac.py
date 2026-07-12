from __future__ import annotations

from engine.statistical_evidence import (
    EvidenceStatus,
    StatisticalMethod,
    aggregate_statistical_evidence,
    build_statistical_evidence_input,
    make_method_evidence,
    project_summary,
    validate_method_evidence,
    validate_statistical_evidence_input,
)


def _complete():
    methods = (StatisticalMethod.BH, StatisticalMethod.WRC, StatisticalMethod.PBO_CSCV, StatisticalMethod.DSR)
    ids = ("c0", "c1", "c2", "c3")
    value = build_statistical_evidence_input(
        lineage_projection={"target_ref": "family://v1", "target_hash": "sha256:f", "raw_trial_count": 4},
        candidate_ids=ids,
        method_inputs={method.value: {} for method in methods},
    )
    evidences = tuple(
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
    )
    return methods, value, evidences


def test_qac_coverage_binding_count_determinism_orphans_and_consumers() -> None:
    methods, value, evidences = _complete()
    assert validate_statistical_evidence_input(value).passed
    assert all(validate_method_evidence(item, expected_input=value).passed for item in evidences)
    assert value.raw_trial_count == len(value.candidate_ids)
    summary_hashes = {
        aggregate_statistical_evidence(claim_id="strategy-admission", mandatory_methods=methods, evidences=evidences).summary_hash
        for _ in range(10)
    }
    assert len(summary_hashes) == 1
    summary = aggregate_statistical_evidence(claim_id="strategy-admission", mandatory_methods=methods, evidences=evidences)
    assert len(summary.method_evidences) == 4
    assert all(item.evidence_ref for item in summary.method_evidences)
    consumers = {
        project_summary(summary, consumer_id="uc58-multifactor")["consumer_id"],
        project_summary(summary, consumer_id="uc59-ml-compatibility")["consumer_id"],
        project_summary(summary, consumer_id="uc60-event-compatibility")["consumer_id"],
    }
    assert len(consumers) == 3


def test_qac_negative_fail_closed_and_overclaim_zero() -> None:
    methods, value, evidences = _complete()
    cases = [
        evidences[:1],
        tuple(make_method_evidence(
            method=item.method,
            evidence_input=value,
            status=EvidenceStatus.BLOCKED if index == 0 else item.status,
            config={"method": item.method.value},
            reason_codes=("fixture_blocked",) if index == 0 else (),
            evidence_ref=item.evidence_ref,
        ) for index, item in enumerate(evidences)),
    ]
    summaries = [aggregate_statistical_evidence(claim_id="strategy-admission", mandatory_methods=methods, evidences=case) for case in cases]
    assert all(item.status is EvidenceStatus.BLOCKED for item in summaries)
    assert all(project_summary(item, consumer_id="fixture")["effective_trial_count"] is None for item in summaries)
