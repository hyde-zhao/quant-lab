from __future__ import annotations

from dataclasses import replace

import pytest

from engine.statistical_evidence import (
    EvidenceStatus,
    StatisticalMethod,
    aggregate_statistical_evidence,
    build_statistical_evidence_input,
    candidate_membership_hash,
    canonical_hash,
    make_method_evidence,
    project_summary,
    validate_method_evidence,
    validate_statistical_evidence_input,
)


def evidence_input(count: int = 4):
    candidate_ids = tuple(f"candidate-{index}" for index in range(count))
    return build_statistical_evidence_input(
        lineage_projection={
            "target_ref": "family://sealed-v1",
            "target_hash": "sha256:family",
            "raw_trial_count": count,
        },
        candidate_ids=candidate_ids,
        method_inputs={method.value: {} for method in StatisticalMethod},
    )


def method_evidence(method: StatisticalMethod, status: EvidenceStatus, *, ref: bool = True):
    value = evidence_input()
    return make_method_evidence(
        method=method,
        evidence_input=value,
        status=status,
        config={"version": 1},
        result={"value": 0.1},
        reason_codes=() if status is EvidenceStatus.PASS else (f"{method.value}_{status.value}",),
        evidence_ref=f"evidence://{method.value}" if ref else "",
    )


def test_input_binding_and_canonical_hash_are_deterministic() -> None:
    value = evidence_input()
    assert validate_statistical_evidence_input(value).status is EvidenceStatus.PASS
    assert value.candidate_membership_hash == candidate_membership_hash(value.candidate_ids)
    assert len({canonical_hash(value.to_dict()) for _ in range(10)}) == 1


def test_count_hash_and_non_finite_conflicts_block() -> None:
    value = evidence_input()
    assert validate_statistical_evidence_input(replace(value, raw_trial_count=3)).status is EvidenceStatus.BLOCKED
    assert validate_statistical_evidence_input(replace(value, candidate_membership_hash="sha256:bad")).status is EvidenceStatus.BLOCKED
    with pytest.raises(ValueError, match="non-finite"):
        replace(value, method_inputs={"bh": {"p": float("nan")}}).to_dict()


def test_method_evidence_binds_exact_input() -> None:
    value = evidence_input()
    item = method_evidence(StatisticalMethod.BH, EvidenceStatus.PASS)
    assert validate_method_evidence(item, expected_input=value).passed
    changed = replace(value, family_hash="sha256:other")
    assert validate_method_evidence(item, expected_input=changed).status is EvidenceStatus.BLOCKED


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([EvidenceStatus.PASS] * 4, EvidenceStatus.PASS),
        ([EvidenceStatus.PASS, EvidenceStatus.FAIL, EvidenceStatus.PASS, EvidenceStatus.PASS], EvidenceStatus.FAIL),
        ([EvidenceStatus.PASS, EvidenceStatus.TYPED_UNAVAILABLE, EvidenceStatus.PASS, EvidenceStatus.PASS], EvidenceStatus.TYPED_UNAVAILABLE),
        ([EvidenceStatus.PASS, EvidenceStatus.BLOCKED, EvidenceStatus.FAIL, EvidenceStatus.PASS], EvidenceStatus.BLOCKED),
    ],
)
def test_conservative_aggregation_lattice(statuses, expected) -> None:
    methods = (StatisticalMethod.BH, StatisticalMethod.WRC, StatisticalMethod.PBO_CSCV, StatisticalMethod.DSR)
    summary = aggregate_statistical_evidence(
        claim_id="strategy-admission",
        mandatory_methods=methods,
        evidences=[method_evidence(method, status) for method, status in zip(methods, statuses, strict=True)],
    )
    assert summary.status is expected
    assert len({summary.summary_hash for _ in range(10)}) == 1
    assert project_summary(summary, consumer_id="test")["effective_trial_count"] is None


def test_missing_or_orphan_method_evidence_blocks() -> None:
    methods = (StatisticalMethod.BH, StatisticalMethod.WRC)
    missing = aggregate_statistical_evidence(
        claim_id="claim", mandatory_methods=methods, evidences=[method_evidence(StatisticalMethod.BH, EvidenceStatus.PASS)]
    )
    orphan = aggregate_statistical_evidence(
        claim_id="claim",
        mandatory_methods=methods,
        evidences=[method_evidence(StatisticalMethod.BH, EvidenceStatus.PASS), method_evidence(StatisticalMethod.WRC, EvidenceStatus.PASS, ref=False)],
    )
    assert missing.status is EvidenceStatus.BLOCKED
    assert orphan.status is EvidenceStatus.BLOCKED
    assert "method_evidence_ref_missing" in orphan.reason_codes
