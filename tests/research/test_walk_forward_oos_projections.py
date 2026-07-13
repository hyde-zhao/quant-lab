from __future__ import annotations

from dataclasses import replace

from engine.cross_strategy_reliability_gates import ReliabilityGateStatus, validate_gate2_cv_governance
from engine.strategy_admission_package import attach_walk_forward_oos_evidence
from engine.strategy_evidence import EvidenceAvailability
from engine.strategy_admission_statistical_gate import validate_walk_forward_plan
from engine.walk_forward_oos_projections import (
    component_projection_identity,
    project_to_reliability_gate2,
    project_to_statistical_walk_forward_plan,
)
from tests.research.walk_forward_oos_test_support import passing_component
from tests.research.walk_forward_oos_test_support import evidence_input
from engine.walk_forward_oos_evidence import produce_walk_forward_oos_evidence, validate_walk_forward_oos_input


def _base_package(status: str = "pass") -> dict:
    return {
        "admission_status": status,
        "evidence_refs": (),
        "blocked_reasons": (),
        "limitations": (),
        "not_authorized_counters": {},
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }


def test_same_c2_identity_projects_to_all_three_existing_consumers() -> None:
    component = passing_component()
    identity = component_projection_identity(component)
    plan = project_to_statistical_walk_forward_plan(component)
    gate2_payload = project_to_reliability_gate2(component)
    package = attach_walk_forward_oos_evidence(_base_package(), component)
    assert validate_walk_forward_plan(plan) == ()
    assert plan.embargo_days == 1
    assert plan.evidence_ref == gate2_payload["walk_forward_oos_component_ref"] == identity["component_ref"]
    assert plan.evidence_hash == gate2_payload["walk_forward_oos_component_hash"] == identity["component_hash"]
    assert package["walk_forward_oos_evidence"] == identity
    assert identity["component_ref"] in package["evidence_refs"]


def test_gate2_consumes_projection_without_new_gate_or_raw_recompute() -> None:
    payload = project_to_reliability_gate2(passing_component())
    summary = validate_gate2_cv_governance(payload, strategy_class="ml", release_profile="candidate-release")
    assert summary.gate_id == "gate_2_cv"
    assert summary.status is ReliabilityGateStatus.PASS
    assert summary.evidence_identity["component_ref"] == payload["walk_forward_oos_component_ref"]
    assert summary.evidence_identity["component_hash"] == payload["walk_forward_oos_component_hash"]


def test_projection_and_package_merge_are_fail_closed_for_tamper() -> None:
    component = passing_component()
    tampered = replace(component, component_hash="sha256:tampered")
    plan = project_to_statistical_walk_forward_plan(tampered)
    gate2 = project_to_reliability_gate2(tampered)
    package = attach_walk_forward_oos_evidence(_base_package(), tampered)
    assert plan.evidence_availability == "blocked"
    assert gate2["walk_forward_oos_availability"] == "blocked"
    assert package["admission_status"] == "blocked"


def test_passing_c2_never_improves_existing_blocked_status_or_authorization() -> None:
    package = attach_walk_forward_oos_evidence(_base_package("blocked"), passing_component())
    assert package["admission_status"] == "blocked"
    assert all(
        package[field]
        for field in (
            "not_qmt_authorization",
            "not_simulation_authorization",
            "not_live_authorization",
            "not_broker_order",
        )
    )


def test_typed_unavailable_identity_is_preserved_without_becoming_false_pass() -> None:
    value = evidence_input()
    unavailable = produce_walk_forward_oos_evidence(
        validate_walk_forward_oos_input(replace(value, fold_metrics=value.fold_metrics[:-1]))
    ).component
    identity = component_projection_identity(unavailable)
    package = attach_walk_forward_oos_evidence(_base_package(), unavailable)
    assert identity["availability"] == EvidenceAvailability.TYPED_UNAVAILABLE.value
    assert package["admission_status"] == "blocked"
