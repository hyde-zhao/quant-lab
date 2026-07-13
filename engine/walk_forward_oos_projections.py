"""Thin CR-166 projections into the three existing admission consumers."""

from __future__ import annotations

from typing import Any

from engine.strategy_evidence import EvidenceAvailability
from engine.strategy_admission_statistical_gate import WalkForwardValidationPlan
from engine.walk_forward_oos_evidence import (
    WalkForwardOOSComponent,
    WalkForwardOutcome,
    validate_walk_forward_oos_component,
)


def project_to_statistical_walk_forward_plan(component: WalkForwardOOSComponent) -> WalkForwardValidationPlan:
    """Map self-validated C2 evidence to the existing CR151 plan contract."""

    trusted = validate_walk_forward_oos_component(component).structurally_valid
    present = trusted and component.availability is EvidenceAvailability.PRESENT
    folds = component.fold_evidence if present else ()
    return WalkForwardValidationPlan(
        folds=component.declared_fold_count if present else 0,
        train_window="explicit-fold-manifest" if present else "",
        validation_window="explicit-fold-manifest" if present else "",
        oos_window="explicit-fold-manifest" if present else "",
        embargo_days=component.embargo_applied if present and component.leakage_unit == "days" else -1,
        fold_metrics=tuple(
            {
                "fold_id": item.fold_id,
                "passed": item.outcome is WalkForwardOutcome.PASS,
                "status": item.outcome.value,
                "reason_codes": item.reason_codes,
            }
            for item in folds
        ),
        report_ref=component.component_ref if present else "",
        evidence_ref=component.component_ref,
        evidence_hash=component.component_hash,
        evidence_availability=(component.availability.value if trusted else EvidenceAvailability.BLOCKED.value),
        evidence_outcome=component.outcome.value if present and component.outcome else "",
        evidence_reason_codes=component.reason_codes if trusted else ("component_self_validation_failed",),
    )


def project_to_reliability_gate2(component: WalkForwardOOSComponent) -> dict[str, Any]:
    """Map the same component identity to CR154 Gate 2's existing evidence surface."""

    trusted = validate_walk_forward_oos_component(component).structurally_valid
    present = trusted and component.availability is EvidenceAvailability.PRESENT
    reasons = component.reason_codes if trusted else ("component_self_validation_failed",)
    payload: dict[str, Any] = {
        "walk_forward_oos_component_ref": component.component_ref,
        "walk_forward_oos_component_hash": component.component_hash,
        "walk_forward_oos_availability": component.availability.value if trusted else EvidenceAvailability.BLOCKED.value,
        "walk_forward_oos_outcome": component.outcome.value if present and component.outcome else "",
        "walk_forward_oos_reason_codes": reasons,
    }
    if not present:
        return payload
    payload.update(
        {
            "split_policy_ref": component.split_policy_ref,
            "walk_forward_ref": component.component_ref,
            "oos_ref": component.component_ref,
            "purge_embargo_refs": tuple(
                ref for ref in (component.purge_policy_ref, component.embargo_policy_ref) if ref
            ),
            "embargo_gap_ref": component.embargo_policy_ref,
            "overlap_applicability": component.overlap_applicability,
        }
    )
    return payload


def component_projection_identity(component: WalkForwardOOSComponent) -> dict[str, Any]:
    """Return the immutable identity/reason surface shared by every projection."""

    trusted = validate_walk_forward_oos_component(component).structurally_valid
    return {
        "component_ref": component.component_ref,
        "component_hash": component.component_hash,
        "availability": component.availability.value if trusted else EvidenceAvailability.BLOCKED.value,
        "outcome": component.outcome.value if trusted and component.outcome else "",
        "reason_codes": component.reason_codes if trusted else ("component_self_validation_failed",),
    }


__all__ = [
    "component_projection_identity",
    "project_to_reliability_gate2",
    "project_to_statistical_walk_forward_plan",
]
