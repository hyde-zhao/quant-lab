"""Multiple-testing controls for automatic anomaly discovery."""

from __future__ import annotations

from math import erfc, sqrt
from typing import Any, Mapping, Sequence


MULTIPLE_TESTING_SCHEMA = "anomaly_multiple_testing_v1"


def apply_multiple_testing_control(
    reports: Sequence[Mapping[str, Any]],
    *,
    alpha: float = 0.05,
) -> tuple[dict[str, Any], ...]:
    """Attach Bonferroni and Benjamini-Hochberg decisions to reports.

    P-values use a normal approximation from the reported sorting t-stat. The
    approximation is intentional here: the gate is a conservative governance
    filter, not a replacement for the detailed anomaly report.
    """

    enriched = [dict(report) for report in reports]
    tested = [item for item in enriched if item.get("sorting_t_stat") is not None]
    test_count = len(tested)
    for item in enriched:
        t_stat = item.get("sorting_t_stat")
        raw_p = None if t_stat is None else two_sided_normal_p_value(float(t_stat))
        item["multiple_testing"] = {
            "schema_version": MULTIPLE_TESTING_SCHEMA,
            "method": "bonferroni_and_bh_fdr",
            "alpha": float(alpha),
            "candidate_count": int(test_count),
            "raw_p_value": raw_p,
            "bonferroni_p_value": None if raw_p is None else min(1.0, raw_p * max(test_count, 1)),
            "fdr_bh_q_value": None,
            "bonferroni_pass": False,
            "fdr_bh_pass": False,
            "multiple_testing_pass": False,
        }

    ranked = sorted(
        (item for item in enriched if item["multiple_testing"]["raw_p_value"] is not None),
        key=lambda item: item["multiple_testing"]["raw_p_value"],
    )
    if ranked:
        q_values = _bh_q_values([float(item["multiple_testing"]["raw_p_value"]) for item in ranked])
        for item, q_value in zip(ranked, q_values, strict=True):
            mt = item["multiple_testing"]
            mt["fdr_bh_q_value"] = q_value
            mt["bonferroni_pass"] = bool(mt["bonferroni_p_value"] is not None and mt["bonferroni_p_value"] <= alpha)
            mt["fdr_bh_pass"] = bool(q_value <= alpha)
            mt["multiple_testing_pass"] = bool(mt["bonferroni_pass"] or mt["fdr_bh_pass"])
    return tuple(enriched)


def two_sided_normal_p_value(t_stat: float) -> float:
    return float(erfc(abs(t_stat) / sqrt(2.0)))


def _bh_q_values(p_values: Sequence[float]) -> list[float]:
    n = len(p_values)
    raw = [min(1.0, p_value * n / rank) for rank, p_value in enumerate(p_values, start=1)]
    adjusted = raw[:]
    for index in range(n - 2, -1, -1):
        adjusted[index] = min(adjusted[index], adjusted[index + 1])
    return adjusted
