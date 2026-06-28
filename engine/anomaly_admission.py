"""Admission decisions for automatic anomaly discovery candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


ANOMALY_ADMISSION_SCHEMA = "anomaly_admission_decision_v1"

ADMITTED_TO_FACTOR_CATALOG = ("factor_catalog_candidate", "stage3_candidate")


@dataclass(frozen=True, slots=True)
class AnomalyAdmissionDecision:
    anomaly_id: str
    factor_id: str
    admission_status: str
    source_decision: str
    multiple_testing_pass: bool
    required_actions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = ANOMALY_ADMISSION_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_anomaly_admission_decisions(
    reports: Sequence[Mapping[str, Any]],
    *,
    evidence_refs: Sequence[str] = (),
) -> tuple[AnomalyAdmissionDecision, ...]:
    decisions: list[AnomalyAdmissionDecision] = []
    for report in reports:
        anomaly_id = str(report["anomaly_id"])
        source_decision = str(report.get("decision", "watch_needs_robustness_review"))
        mt = report.get("multiple_testing", {})
        multiple_testing_pass = bool(isinstance(mt, Mapping) and mt.get("multiple_testing_pass"))
        mean_return = report.get("mean_long_short_return")
        missing_observations = mean_return is None
        status: str
        blocked_reasons: list[str] = []
        required_actions: list[str] = []

        if missing_observations:
            status = "blocked_insufficient_data"
            blocked_reasons.append("no_valid_long_short_observations")
        elif source_decision == "reject_or_reweight":
            status = "rejected"
            blocked_reasons.append("non_positive_mean_long_short_return")
        elif source_decision == "factor_catalog_candidate" and multiple_testing_pass:
            status = "stage3_candidate"
            required_actions.append("register_factor_catalog_entry")
            required_actions.append("include_in_stage3_candidate_search")
        elif source_decision == "factor_catalog_candidate":
            status = "factor_catalog_candidate"
            required_actions.append("review_multiple_testing_failure_before_stage3")
            blocked_reasons.append("multiple_testing_control_not_passed")
        elif source_decision == "alpha_feature_candidate" and multiple_testing_pass:
            status = "research_candidate"
            required_actions.append("complete_monotonicity_time_split_cost_or_catalog_review")
        else:
            status = "research_candidate"
            required_actions.append("continue_research_or_reject")

        decisions.append(
            AnomalyAdmissionDecision(
                anomaly_id=anomaly_id,
                factor_id=anomaly_id,
                admission_status=status,
                source_decision=source_decision,
                multiple_testing_pass=multiple_testing_pass,
                required_actions=tuple(required_actions),
                blocked_reasons=tuple(blocked_reasons),
                evidence_refs=tuple(evidence_refs),
            )
        )
    return tuple(decisions)


def admitted_factor_ids(decisions: Sequence[AnomalyAdmissionDecision | Mapping[str, Any]]) -> tuple[str, ...]:
    factor_ids: list[str] = []
    for decision in decisions:
        payload = decision.to_dict() if isinstance(decision, AnomalyAdmissionDecision) else decision
        if payload.get("admission_status") in ADMITTED_TO_FACTOR_CATALOG:
            factor_ids.append(str(payload.get("factor_id") or payload.get("anomaly_id")))
    return tuple(factor_ids)
