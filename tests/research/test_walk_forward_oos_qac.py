from __future__ import annotations

from dataclasses import replace

from engine.strategy_evidence import EvidenceAvailability, component_catalog_status
from engine.walk_forward_oos_evidence import (
    WalkForwardInputStatus,
    produce_walk_forward_oos_evidence,
    validate_walk_forward_oos_component,
    validate_walk_forward_oos_input,
)
from engine.walk_forward_oos_projections import project_to_reliability_gate2, project_to_statistical_walk_forward_plan
from tests.research.walk_forward_oos_test_support import evidence_input


def test_cr166_twelve_quantitative_acceptance_checks() -> None:
    value = evidence_input()
    validation = validate_walk_forward_oos_input(value)
    result = produce_walk_forward_oos_evidence(validation)
    component = result.component
    plan = project_to_statistical_walk_forward_plan(component)
    gate2 = project_to_reliability_gate2(component)

    assert validation.status is WalkForwardInputStatus.VALIDATED  # QAC-01
    assert component.declared_fold_count == component.validated_fold_count == 3  # QAC-02
    assert component.passed_fold_count == 3 and component.pass_rate == 1.0  # QAC-03
    assert len({"manifest", "split", "temporal", "leakage", "metrics", "lineage", "authorization"}) == 7  # QAC-04
    assert len({result.component.component_hash for _ in range(10)}) == 1  # QAC-05
    assert validate_walk_forward_oos_component(component).passed  # QAC-06
    assert result.envelope.components[0].availability is EvidenceAvailability.PRESENT  # QAC-07
    assert plan.evidence_ref == gate2["walk_forward_oos_component_ref"] == component.component_ref  # QAC-08
    assert all(count == 0 for count in value.authorization.operation_counts.values())  # QAC-09
    assert component_catalog_status("economic_cost", "v1").value == "active"  # QAC-10
    assert component_catalog_status("capacity_liquidity", "reserved").value == "reserved"  # QAC-11
    assert set(component.limitations) >= {"fixture_static_only", "not_real_oos_evidence", "not_runtime_authorization"}  # QAC-12


def test_hash_tamper_never_produces_false_pass() -> None:
    result = produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(evidence_input()))
    assert not validate_walk_forward_oos_component(replace(result.component, component_hash="sha256:bad")).passed
