"""Pure CSCV/PBO and raw-trial-count DSR evidence calculators for CR164."""

from __future__ import annotations

import math
from statistics import NormalDist, fmean, pstdev
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


OVERFIT_CALCULATOR_VERSION = "cr164_overfit_evidence_v1"
EULER_MASCHERONI = 0.5772156649015329


def validate_cscv_splits(
    *,
    partition_count: int,
    splits: Sequence[Mapping[str, Sequence[int]]],
) -> tuple[tuple[tuple[int, ...], tuple[int, ...], str], ...]:
    if not isinstance(partition_count, int) or isinstance(partition_count, bool) or partition_count < 2:
        raise ValueError("partition_count must be at least 2")
    if len(splits) < 4:
        raise ValueError("PBO/CSCV requires at least 4 valid splits")
    normalized: list[tuple[tuple[int, ...], tuple[int, ...], str]] = []
    seen: set[str] = set()
    universe = set(range(partition_count))
    for item in splits:
        train = tuple(sorted(_indices(item.get("train", ()), partition_count)))
        test = tuple(sorted(_indices(item.get("test", ()), partition_count)))
        if not train or not test:
            raise ValueError("CSCV train and test sides must be non-empty")
        if set(train) & set(test):
            raise ValueError("CSCV train and test sides must not overlap")
        if set(train) | set(test) != universe:
            raise ValueError("Each CSCV split must cover every partition exactly once")
        split_id = canonical_hash(
            {"train": train, "test": test}, domain="quant-lab.cscv-split.v1"
        )
        if split_id in seen:
            raise ValueError("Duplicate CSCV split")
        seen.add(split_id)
        normalized.append((train, test, split_id))
    return tuple(normalized)


def calculate_pbo_evidence(
    evidence_input: StatisticalEvidenceInput,
    *,
    partition_performance: Mapping[str, Sequence[float]],
    splits: Sequence[Mapping[str, Sequence[int]]],
    max_pbo: float = 0.2,
    evidence_ref: str = "",
) -> MethodEvidence:
    config = {
        "method": "cscv_pbo",
        "max_pbo": max_pbo,
        "ranking": "higher_is_better",
        "tie_break": "candidate_id_ascending",
        "calculator_version": OVERFIT_CALCULATOR_VERSION,
    }
    validation = validate_statistical_evidence_input(evidence_input)
    if validation.status is EvidenceStatus.BLOCKED:
        return blocked_method_evidence(StatisticalMethod.PBO_CSCV, evidence_input, reason_codes=[i.code for i in validation.issues], config=config)
    if len(evidence_input.candidate_ids) < 4 or len(splits) < 4:
        return unavailable_method_evidence(StatisticalMethod.PBO_CSCV, evidence_input, reason_code="pbo_cscv_minimum_unavailable", config=config)
    try:
        threshold = _probability(max_pbo, "max_pbo")
        matrix = _performance_matrix(partition_performance, evidence_input.candidate_ids)
        normalized_splits = validate_cscv_splits(partition_count=len(matrix[0]), splits=splits)
        split_results: list[dict[str, Any]] = []
        negative_logits = 0
        for train, test, split_id in normalized_splits:
            train_scores = {
                candidate_id: fmean(matrix[index][partition] for partition in train)
                for index, candidate_id in enumerate(evidence_input.candidate_ids)
            }
            selected_id = sorted(train_scores, key=lambda item: (-train_scores[item], item))[0]
            test_scores = {
                candidate_id: fmean(matrix[index][partition] for partition in test)
                for index, candidate_id in enumerate(evidence_input.candidate_ids)
            }
            ordered = sorted(test_scores, key=lambda item: (test_scores[item], item))
            rank = ordered.index(selected_id) + 1
            percentile = rank / (len(ordered) + 1.0)
            logit = math.log(percentile / (1.0 - percentile))
            if logit <= 0.0:
                negative_logits += 1
            split_results.append(
                {
                    "split_id": split_id,
                    "selected_candidate_id": selected_id,
                    "test_rank": rank,
                    "test_rank_percentile": percentile,
                    "logit": logit,
                }
            )
        pbo = negative_logits / len(split_results)
        result = {
            "candidate_count": len(evidence_input.candidate_ids),
            "valid_split_count": len(split_results),
            "pbo": pbo,
            "max_pbo": threshold,
            "method_pass": pbo <= threshold,
            "splits": split_results,
        }
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        return blocked_method_evidence(StatisticalMethod.PBO_CSCV, evidence_input, reason_codes=(f"pbo_cscv_input_invalid:{exc}",), config=config)
    status = EvidenceStatus.PASS if result["method_pass"] else EvidenceStatus.FAIL
    return make_method_evidence(
        method=StatisticalMethod.PBO_CSCV,
        evidence_input=evidence_input,
        status=status,
        config=config,
        result=result,
        provenance={**config, "split_ids": [item["split_id"] for item in result["splits"]]},
        reason_codes=() if status is EvidenceStatus.PASS else ("pbo_exceeds_threshold",),
        evidence_ref=evidence_ref or _evidence_ref("pbo_cscv", evidence_input, config, result),
    )


def calculate_dsr_evidence(
    evidence_input: StatisticalEvidenceInput,
    *,
    observed_sharpe: float,
    sample_length: int,
    skew: float,
    kurtosis: float,
    trial_sharpes: Sequence[float],
    returns: Sequence[float],
    min_dsr_probability: float = 0.95,
    evidence_ref: str = "",
) -> MethodEvidence:
    config = {
        "dsr_input_method": "raw_trial_count",
        "min_dsr_probability": min_dsr_probability,
        "calculator_version": OVERFIT_CALCULATOR_VERSION,
        "effective_trial_count": None,
        "effective_trial_count_ref": "",
        "effective_trial_count_method": "",
        "effective_trial_count_availability": "typed_unavailable",
    }
    validation = validate_statistical_evidence_input(evidence_input)
    if validation.status is EvidenceStatus.BLOCKED:
        return blocked_method_evidence(StatisticalMethod.DSR, evidence_input, reason_codes=[i.code for i in validation.issues], config=config)
    if evidence_input.raw_trial_count < 2 or sample_length < 30:
        return unavailable_method_evidence(
            StatisticalMethod.DSR,
            evidence_input,
            reason_code="dsr_minimum_unavailable",
            config=config,
            limitations=("effective_trial_count_typed_unavailable",),
        )
    try:
        threshold = _probability(min_dsr_probability, "min_dsr_probability")
        observed = _finite(observed_sharpe, "observed_sharpe")
        skew_value = _finite(skew, "skew")
        kurtosis_value = _finite(kurtosis, "kurtosis")
        if not isinstance(sample_length, int) or isinstance(sample_length, bool) or sample_length < 30:
            raise ValueError("sample_length must be at least 30")
        sharpes = tuple(_finite(item, "trial_sharpe") for item in trial_sharpes)
        if len(sharpes) != evidence_input.raw_trial_count:
            raise ValueError("trial_sharpes length must equal sealed raw trial count")
        if len(sharpes) < 2 or pstdev(sharpes) <= 0:
            raise ValueError("trial_sharpes require positive variance")
        sample_returns = tuple(_finite(item, "return") for item in returns)
        if len(sample_returns) != sample_length:
            raise ValueError("returns length must equal sample_length")
        if pstdev(sample_returns) <= 0:
            raise ValueError("returns require positive variance")
        expected_maximum = _expected_maximum_sharpe(sharpes)
        variance_term = 1.0 - skew_value * observed + ((kurtosis_value - 1.0) / 4.0) * observed * observed
        if variance_term <= 0:
            raise ValueError("DSR variance term must be positive")
        sharpe_standard_error = math.sqrt(variance_term / (sample_length - 1.0))
        z_score = (observed - expected_maximum) / sharpe_standard_error
        dsr_probability = NormalDist().cdf(z_score)
        result = {
            "dsr_input_method": "raw_trial_count",
            "raw_trial_count": evidence_input.raw_trial_count,
            "raw_trial_count_ref": evidence_input.family_ref,
            "observed_sharpe": observed,
            "expected_maximum_sharpe": expected_maximum,
            "sample_length": sample_length,
            "skew": skew_value,
            "kurtosis": kurtosis_value,
            "sharpe_standard_error": sharpe_standard_error,
            "z_score": z_score,
            "dsr_probability": dsr_probability,
            "min_dsr_probability": threshold,
            "method_pass": dsr_probability >= threshold,
            "effective_trial_count": None,
            "effective_trial_count_ref": "",
            "effective_trial_count_method": "",
            "effective_trial_count_availability": "typed_unavailable",
        }
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        return blocked_method_evidence(StatisticalMethod.DSR, evidence_input, reason_codes=(f"dsr_input_invalid:{exc}",), config=config)
    status = EvidenceStatus.PASS if result["method_pass"] else EvidenceStatus.FAIL
    return make_method_evidence(
        method=StatisticalMethod.DSR,
        evidence_input=evidence_input,
        status=status,
        config=config,
        result=result,
        provenance={
            "calculator_version": OVERFIT_CALCULATOR_VERSION,
            "dsr_input_method": "raw_trial_count",
            "raw_trial_count_ref": evidence_input.family_ref,
            "family_hash": evidence_input.family_hash,
        },
        reason_codes=() if status is EvidenceStatus.PASS else ("dsr_below_probability_threshold",),
        limitations=("effective_trial_count_typed_unavailable", "raw_trial_count_is_not_effective_trial_count"),
        evidence_ref=evidence_ref or _evidence_ref("dsr", evidence_input, config, result),
    )


def validate_dsr_non_alias(evidence: MethodEvidence) -> bool:
    if evidence.method is not StatisticalMethod.DSR:
        return False
    config = evidence.provenance
    result = evidence.result
    return bool(
        config.get("dsr_input_method") == "raw_trial_count"
        and result.get("dsr_input_method") == "raw_trial_count"
        and result.get("effective_trial_count") is None
        and result.get("effective_trial_count_ref") == ""
        and result.get("effective_trial_count_method") == ""
        and result.get("effective_trial_count_availability") == "typed_unavailable"
    )


def _expected_maximum_sharpe(trial_sharpes: Sequence[float]) -> float:
    trials = len(trial_sharpes)
    scale = pstdev(trial_sharpes)
    normal = NormalDist()
    first = normal.inv_cdf(1.0 - 1.0 / trials)
    second = normal.inv_cdf(1.0 - 1.0 / (trials * math.e))
    return fmean(trial_sharpes) + scale * ((1.0 - EULER_MASCHERONI) * first + EULER_MASCHERONI * second)


def _performance_matrix(
    values: Mapping[str, Sequence[float]], candidate_ids: Sequence[str]
) -> tuple[tuple[float, ...], ...]:
    if set(values) != set(candidate_ids):
        raise ValueError("partition performance candidate membership mismatch")
    rows: list[tuple[float, ...]] = []
    length: int | None = None
    for candidate_id in candidate_ids:
        row = tuple(_finite(item, "partition performance") for item in values[candidate_id])
        if len(row) < 2:
            raise ValueError("partition performance requires at least 2 partitions")
        if length is None:
            length = len(row)
        elif len(row) != length:
            raise ValueError("partition performance rows must be aligned")
        rows.append(row)
    return tuple(rows)


def _indices(values: Sequence[int], partition_count: int) -> tuple[int, ...]:
    result = tuple(values)
    if any(not isinstance(item, int) or isinstance(item, bool) or not 0 <= item < partition_count for item in result):
        raise ValueError("split indices are invalid")
    if len(set(result)) != len(result):
        raise ValueError("split indices must be unique")
    return result


def _evidence_ref(method: str, evidence_input: StatisticalEvidenceInput, config: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    digest = canonical_hash(
        {"input": evidence_input.to_dict(), "config": config, "result": result},
        domain=f"quant-lab.{method}.evidence-ref.v1",
    ).split(":", 1)[1]
    return f"statistical-evidence://{method}/{digest}"


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _probability(value: Any, name: str) -> float:
    number = _finite(value, name)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return number


__all__ = [
    "calculate_dsr_evidence",
    "calculate_pbo_evidence",
    "validate_cscv_splits",
    "validate_dsr_non_alias",
]
