from __future__ import annotations

from engine.multiple_testing_evidence import (
    benjamini_hochberg,
    calculate_bh_evidence,
    calculate_spa_evidence,
    calculate_wrc_evidence,
    stationary_bootstrap_indices,
)
from engine.statistical_evidence import EvidenceStatus, build_statistical_evidence_input


def _input(count: int = 4):
    ids = tuple(f"c{index}" for index in range(count))
    return build_statistical_evidence_input(
        lineage_projection={"target_ref": "family://v1", "target_hash": "sha256:f", "raw_trial_count": count},
        candidate_ids=ids,
        method_inputs={"bh": {}, "wrc": {}, "spa": {}},
    )


def test_bh_known_vector_and_stable_ties() -> None:
    result = benjamini_hochberg({"b": 0.04, "a": 0.01, "c": 0.03, "d": 0.2}, alpha=0.05)
    assert result["ordered_candidate_ids"] == ["a", "c", "b", "d"]
    assert result["adjusted_q_values"] == {"a": 0.04, "b": 0.05333333333333334, "c": 0.05333333333333334, "d": 0.2}
    assert result["rejected_candidate_ids"] == ["a"]


def test_bh_evidence_requires_exact_membership() -> None:
    value = _input()
    passed = calculate_bh_evidence(value, p_values={"c0": 0.001, "c1": 0.2, "c2": 0.3, "c3": 0.4})
    blocked = calculate_bh_evidence(value, p_values={"c0": 0.001, "c1": 0.2})
    assert passed.status is EvidenceStatus.PASS
    assert blocked.status is EvidenceStatus.BLOCKED


def test_stationary_bootstrap_is_seeded_and_fixed_window() -> None:
    first = stationary_bootstrap_indices(8, block_length=3, replications=20, seed=42)
    second = stationary_bootstrap_indices(8, block_length=3, replications=20, seed=42)
    assert first == second
    assert len(first) == 20
    assert all(len(row) == 8 for row in first)


def test_wrc_and_spa_record_full_fixed_window_provenance() -> None:
    value = _input()
    returns = {
        "c0": [0.04, 0.05, 0.03, 0.06, 0.04, 0.05],
        "c1": [0.01, -0.01, 0.02, 0.0, 0.01, -0.01],
        "c2": [-0.01, 0.0, -0.02, 0.01, -0.01, 0.0],
        "c3": [0.0, 0.01, 0.0, -0.01, 0.0, 0.01],
    }
    kwargs = dict(return_differentials=returns, alpha=0.2, block_length=2, replications=199, seed=7, benchmark="zero")
    wrc = calculate_wrc_evidence(value, **kwargs)
    spa = calculate_spa_evidence(value, **kwargs)
    for item in (wrc, spa):
        assert item.status in {EvidenceStatus.PASS, EvidenceStatus.FAIL}
        assert item.provenance["bootstrap_method"] == "stationary_bootstrap"
        assert item.provenance["block_length_mode"] == "fixed_window"
        assert item.provenance["block_length"] == 2
        assert item.provenance["seed"] == 7


def test_bootstrap_invalid_shape_or_config_blocks() -> None:
    value = _input()
    bad = calculate_wrc_evidence(
        value,
        return_differentials={candidate: [0.1, 0.2] for candidate in value.candidate_ids},
        block_length=0,
        replications=10,
        seed=1,
        benchmark="zero",
    )
    assert bad.status is EvidenceStatus.BLOCKED
