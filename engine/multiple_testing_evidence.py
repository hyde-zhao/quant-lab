"""Pure BH, White Reality Check, and SPA evidence calculators for CR164."""

from __future__ import annotations

import math
import random
from statistics import fmean, pstdev
from typing import Any, Mapping, Sequence

from engine.statistical_evidence import (
    EvidenceStatus,
    MethodEvidence,
    StatisticalEvidenceInput,
    StatisticalMethod,
    blocked_method_evidence,
    canonical_hash,
    make_method_evidence,
    unavailable_method_evidence,
    validate_statistical_evidence_input,
)


MULTIPLE_TESTING_CALCULATOR_VERSION = "cr164_multiple_testing_v1"


def benjamini_hochberg(p_values: Mapping[str, float], *, alpha: float = 0.05) -> dict[str, Any]:
    """Return stable BH q-values and decisions keyed by candidate id."""

    _alpha(alpha)
    if len(p_values) < 2:
        raise ValueError("BH requires at least 2 candidates")
    items: list[tuple[str, float]] = []
    for candidate_id, value in p_values.items():
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("candidate ids must be non-empty strings")
        p_value = _probability(value, "p_value")
        items.append((candidate_id, p_value))
    if len({item[0] for item in items}) != len(items):
        raise ValueError("candidate ids must be unique")
    ranked = sorted(items, key=lambda item: (item[1], item[0]))
    count = len(ranked)
    raw_q = [min(1.0, p_value * count / rank) for rank, (_, p_value) in enumerate(ranked, start=1)]
    adjusted = raw_q[:]
    for index in range(count - 2, -1, -1):
        adjusted[index] = min(adjusted[index], adjusted[index + 1])
    q_values = {candidate_id: adjusted[index] for index, (candidate_id, _) in enumerate(ranked)}
    rejected = tuple(sorted(candidate_id for candidate_id, q_value in q_values.items() if q_value <= alpha))
    return {
        "alpha": float(alpha),
        "candidate_count": count,
        "ordered_candidate_ids": [candidate_id for candidate_id, _ in ranked],
        "raw_p_values": {key: float(p_values[key]) for key in sorted(p_values)},
        "adjusted_q_values": {key: q_values[key] for key in sorted(q_values)},
        "rejected_candidate_ids": list(rejected),
        "rejected_count": len(rejected),
        "method_pass": bool(rejected),
    }


def calculate_bh_evidence(
    evidence_input: StatisticalEvidenceInput,
    *,
    p_values: Mapping[str, float],
    alpha: float = 0.05,
    evidence_ref: str = "",
) -> MethodEvidence:
    validation = validate_statistical_evidence_input(evidence_input)
    config = {"alpha": alpha, "calculator_version": MULTIPLE_TESTING_CALCULATOR_VERSION}
    if validation.status is EvidenceStatus.BLOCKED:
        return blocked_method_evidence(StatisticalMethod.BH, evidence_input, reason_codes=[i.code for i in validation.issues], config=config)
    if len(evidence_input.candidate_ids) < 2 or not p_values:
        return unavailable_method_evidence(StatisticalMethod.BH, evidence_input, reason_code="bh_minimum_candidates_unavailable", config=config)
    if set(p_values) != set(evidence_input.candidate_ids):
        return blocked_method_evidence(StatisticalMethod.BH, evidence_input, reason_codes=("bh_candidate_membership_mismatch",), config=config)
    try:
        result = benjamini_hochberg(p_values, alpha=alpha)
    except (TypeError, ValueError) as exc:
        return blocked_method_evidence(StatisticalMethod.BH, evidence_input, reason_codes=(f"bh_input_invalid:{exc}",), config=config)
    status = EvidenceStatus.PASS if result["method_pass"] else EvidenceStatus.FAIL
    ref = evidence_ref or _evidence_ref("bh", evidence_input, config, result)
    return make_method_evidence(
        method=StatisticalMethod.BH,
        evidence_input=evidence_input,
        status=status,
        config=config,
        result=result,
        provenance={"calculator_version": MULTIPLE_TESTING_CALCULATOR_VERSION, "method": "benjamini_hochberg"},
        reason_codes=() if status is EvidenceStatus.PASS else ("bh_no_rejection_at_alpha",),
        evidence_ref=ref,
    )


def stationary_bootstrap_indices(
    sample_length: int,
    *,
    block_length: int,
    replications: int,
    seed: int,
) -> tuple[tuple[int, ...], ...]:
    """Generate deterministic stationary-bootstrap index sequences.

    Each next observation starts a new uniformly sampled block with probability
    ``1 / block_length``; otherwise it advances circularly.
    """

    if not isinstance(sample_length, int) or sample_length < 2:
        raise ValueError("sample_length must be at least 2")
    if not isinstance(block_length, int) or isinstance(block_length, bool) or block_length < 1:
        raise ValueError("block_length must be a positive integer")
    if not isinstance(replications, int) or isinstance(replications, bool) or replications < 1:
        raise ValueError("replications must be a positive integer")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    restart_probability = 1.0 / block_length
    output: list[tuple[int, ...]] = []
    for _ in range(replications):
        index = rng.randrange(sample_length)
        row = [index]
        for _position in range(1, sample_length):
            if rng.random() < restart_probability:
                index = rng.randrange(sample_length)
            else:
                index = (index + 1) % sample_length
            row.append(index)
        output.append(tuple(row))
    return tuple(output)


def calculate_wrc_evidence(
    evidence_input: StatisticalEvidenceInput,
    *,
    return_differentials: Mapping[str, Sequence[float]],
    alpha: float = 0.05,
    block_length: int,
    replications: int,
    seed: int,
    benchmark: str,
    null: str = "no_predictive_superiority",
    evidence_ref: str = "",
) -> MethodEvidence:
    return _calculate_bootstrap_evidence(
        StatisticalMethod.WRC,
        evidence_input,
        return_differentials=return_differentials,
        alpha=alpha,
        block_length=block_length,
        replications=replications,
        seed=seed,
        benchmark=benchmark,
        null=null,
        evidence_ref=evidence_ref,
    )


def calculate_spa_evidence(
    evidence_input: StatisticalEvidenceInput,
    *,
    return_differentials: Mapping[str, Sequence[float]],
    alpha: float = 0.05,
    block_length: int,
    replications: int,
    seed: int,
    benchmark: str,
    null: str = "no_superior_predictive_ability",
    evidence_ref: str = "",
) -> MethodEvidence:
    return _calculate_bootstrap_evidence(
        StatisticalMethod.SPA,
        evidence_input,
        return_differentials=return_differentials,
        alpha=alpha,
        block_length=block_length,
        replications=replications,
        seed=seed,
        benchmark=benchmark,
        null=null,
        evidence_ref=evidence_ref,
    )


def _calculate_bootstrap_evidence(
    method: StatisticalMethod,
    evidence_input: StatisticalEvidenceInput,
    *,
    return_differentials: Mapping[str, Sequence[float]],
    alpha: float,
    block_length: int,
    replications: int,
    seed: int,
    benchmark: str,
    null: str,
    evidence_ref: str,
) -> MethodEvidence:
    config = {
        "alpha": alpha,
        "bootstrap_method": "stationary_bootstrap",
        "block_length_mode": "fixed_window",
        "block_length": block_length,
        "replications": replications,
        "seed": seed,
        "benchmark": benchmark,
        "null": null,
        "calculator_version": MULTIPLE_TESTING_CALCULATOR_VERSION,
    }
    validation = validate_statistical_evidence_input(evidence_input)
    if validation.status is EvidenceStatus.BLOCKED:
        return blocked_method_evidence(method, evidence_input, reason_codes=[item.code for item in validation.issues], config=config)
    if len(evidence_input.candidate_ids) < 2 or not return_differentials:
        return unavailable_method_evidence(method, evidence_input, reason_code=f"{method.value}_minimum_candidates_unavailable", config=config)
    try:
        _alpha(alpha)
        if not benchmark or not null:
            raise ValueError("benchmark and null are required")
        matrix = _return_matrix(return_differentials, evidence_input.candidate_ids)
        indices = stationary_bootstrap_indices(
            len(matrix[0]), block_length=block_length, replications=replications, seed=seed
        )
        observed, bootstrapped = _bootstrap_statistics(method, matrix, indices)
        p_value = (1 + sum(value >= observed for value in bootstrapped)) / (replications + 1)
        result = {
            "alpha": alpha,
            "candidate_count": len(matrix),
            "sample_length": len(matrix[0]),
            "observed_statistic": observed,
            "bootstrap_p_value": p_value,
            "method_pass": p_value <= alpha,
        }
    except (TypeError, ValueError) as exc:
        return blocked_method_evidence(method, evidence_input, reason_codes=(f"{method.value}_input_invalid:{exc}",), config=config)
    status = EvidenceStatus.PASS if result["method_pass"] else EvidenceStatus.FAIL
    ref = evidence_ref or _evidence_ref(method.value, evidence_input, config, result)
    return make_method_evidence(
        method=method,
        evidence_input=evidence_input,
        status=status,
        config=config,
        result=result,
        provenance=config,
        reason_codes=() if status is EvidenceStatus.PASS else (f"{method.value}_not_significant",),
        evidence_ref=ref,
    )


def _bootstrap_statistics(
    method: StatisticalMethod,
    matrix: tuple[tuple[float, ...], ...],
    indices: Sequence[Sequence[int]],
) -> tuple[float, tuple[float, ...]]:
    length = len(matrix[0])
    means = tuple(fmean(row) for row in matrix)
    if method is StatisticalMethod.WRC:
        observed = math.sqrt(length) * max(means)
        centered = tuple(tuple(value - mean for value in row) for row, mean in zip(matrix, means, strict=True))
        bootstrap = tuple(math.sqrt(length) * max(fmean(row[index] for index in sample) for row in centered) for sample in indices)
        return observed, bootstrap
    standard_errors = tuple(pstdev(row) / math.sqrt(length) for row in matrix)
    if any(value <= 0 for value in standard_errors):
        raise ValueError("SPA requires positive candidate return variance")
    observed = max(mean / error for mean, error in zip(means, standard_errors, strict=True))
    recentered = tuple(
        tuple(value - max(mean, 0.0) for value in row)
        for row, mean in zip(matrix, means, strict=True)
    )
    bootstrap = tuple(
        max(
            fmean(row[index] for index in sample) / error
            for row, error in zip(recentered, standard_errors, strict=True)
        )
        for sample in indices
    )
    return observed, bootstrap


def _return_matrix(
    values: Mapping[str, Sequence[float]], candidate_ids: Sequence[str]
) -> tuple[tuple[float, ...], ...]:
    if set(values) != set(candidate_ids):
        raise ValueError("return matrix candidate membership mismatch")
    rows: list[tuple[float, ...]] = []
    expected_length: int | None = None
    for candidate_id in candidate_ids:
        row = tuple(_finite_float(item, "return differential") for item in values[candidate_id])
        if len(row) < 2:
            raise ValueError("return differential rows require at least 2 observations")
        if expected_length is None:
            expected_length = len(row)
        elif len(row) != expected_length:
            raise ValueError("return differential rows must be aligned")
        rows.append(row)
    return tuple(rows)


def _evidence_ref(
    method: str, evidence_input: StatisticalEvidenceInput, config: Mapping[str, Any], result: Mapping[str, Any]
) -> str:
    digest = canonical_hash(
        {"input": evidence_input.to_dict(), "config": config, "result": result},
        domain=f"quant-lab.{method}.evidence-ref.v1",
    ).split(":", 1)[1]
    return f"statistical-evidence://{method}/{digest}"


def _probability(value: Any, name: str) -> float:
    number = _finite_float(value, name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return number


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _alpha(value: Any) -> float:
    number = _probability(value, "alpha")
    if number == 0:
        raise ValueError("alpha must be positive")
    return number


__all__ = [
    "benjamini_hochberg",
    "calculate_bh_evidence",
    "calculate_spa_evidence",
    "calculate_wrc_evidence",
    "stationary_bootstrap_indices",
]
