from __future__ import annotations

from engine.overfit_evidence import calculate_dsr_evidence, calculate_pbo_evidence, validate_dsr_non_alias
from engine.statistical_evidence import EvidenceStatus, build_statistical_evidence_input


def _input(count: int = 4):
    ids = tuple(f"c{index}" for index in range(count))
    return build_statistical_evidence_input(
        lineage_projection={"target_ref": "family://v1", "target_hash": "sha256:f", "raw_trial_count": count},
        candidate_ids=ids,
        method_inputs={"pbo_cscv": {}, "dsr": {}},
    )


def _splits():
    return (
        {"train": (0, 1), "test": (2, 3)},
        {"train": (0, 2), "test": (1, 3)},
        {"train": (0, 3), "test": (1, 2)},
        {"train": (1, 2), "test": (0, 3)},
    )


def test_pbo_has_stable_valid_split_manifest() -> None:
    value = _input()
    performance = {
        "c0": (0.4, 0.3, -0.1, -0.2),
        "c1": (0.2, 0.1, 0.15, 0.1),
        "c2": (0.1, 0.2, 0.1, 0.2),
        "c3": (0.0, 0.1, 0.0, 0.1),
    }
    result = calculate_pbo_evidence(value, partition_performance=performance, splits=_splits(), max_pbo=0.75)
    assert result.status in {EvidenceStatus.PASS, EvidenceStatus.FAIL}
    assert result.result["valid_split_count"] == 4
    assert 0 <= result.result["pbo"] <= 1
    assert len({item["split_id"] for item in result.result["splits"]}) == 4


def test_pbo_leaky_or_insufficient_splits_fail_closed() -> None:
    value = _input()
    performance = {candidate: (0.1, 0.2, 0.3, 0.4) for candidate in value.candidate_ids}
    leaky = tuple(_splits()[:3]) + ({"train": (0, 1), "test": (1, 2, 3)},)
    assert calculate_pbo_evidence(value, partition_performance=performance, splits=leaky).status is EvidenceStatus.BLOCKED
    assert calculate_pbo_evidence(value, partition_performance=performance, splits=_splits()[:3]).status is EvidenceStatus.TYPED_UNAVAILABLE


def test_dsr_declares_raw_count_and_never_aliases_effective_count() -> None:
    value = _input()
    returns = [(-1.0 if index % 3 == 0 else 1.5) / 100 for index in range(30)]
    result = calculate_dsr_evidence(
        value,
        observed_sharpe=1.5,
        sample_length=30,
        skew=0.1,
        kurtosis=3.2,
        trial_sharpes=(0.2, 0.4, 0.6, 1.5),
        returns=returns,
        min_dsr_probability=0.5,
    )
    assert result.status in {EvidenceStatus.PASS, EvidenceStatus.FAIL}
    assert result.result["dsr_input_method"] == "raw_trial_count"
    assert result.result["raw_trial_count"] == 4
    assert result.result["effective_trial_count"] is None
    assert result.result["effective_trial_count_availability"] == "typed_unavailable"
    assert validate_dsr_non_alias(result)


def test_dsr_count_mismatch_degenerate_or_low_sample_fail_closed() -> None:
    value = _input()
    low = calculate_dsr_evidence(value, observed_sharpe=1.0, sample_length=20, skew=0, kurtosis=3, trial_sharpes=(0.1,) * 4, returns=(0.1,) * 20)
    mismatch = calculate_dsr_evidence(value, observed_sharpe=1.0, sample_length=30, skew=0, kurtosis=3, trial_sharpes=(0.1, 0.2), returns=tuple(range(30)))
    degenerate = calculate_dsr_evidence(value, observed_sharpe=1.0, sample_length=30, skew=0, kurtosis=3, trial_sharpes=(0.1, 0.2, 0.3, 0.4), returns=(0.1,) * 30)
    assert low.status is EvidenceStatus.TYPED_UNAVAILABLE
    assert mismatch.status is EvidenceStatus.BLOCKED
    assert degenerate.status is EvidenceStatus.BLOCKED
