from __future__ import annotations

from dataclasses import replace

from engine.strategy_evidence import EvidenceAvailability, validate_strategy_evidence_envelope
from engine.walk_forward_oos_evidence import (
    WalkForwardInputStatus,
    WalkForwardOutcome,
    produce_walk_forward_oos_evidence,
    validate_walk_forward_oos_component,
    validate_walk_forward_oos_input,
)
from tests.research.walk_forward_oos_test_support import evidence_input


def test_producer_recomputes_fold_outcomes_and_declared_denominator() -> None:
    value = evidence_input((1.0, 0.4, 0.8))
    result = produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(value))
    assert result.component.availability is EvidenceAvailability.PRESENT
    assert result.component.outcome is WalkForwardOutcome.NEEDS_REVIEW
    assert result.component.passed_fold_count == 2
    assert result.component.pass_rate == 2 / 3
    assert validate_walk_forward_oos_component(result.component).passed
    assert validate_strategy_evidence_envelope(result.envelope).passed


def test_identical_normalized_input_produces_one_component_and_envelope_hash() -> None:
    hashes = {
        (
            result.component.component_hash,
            result.envelope.envelope_hash,
        )
        for result in (
            produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(evidence_input()))
            for _ in range(10)
        )
    }
    assert len(hashes) == 1


def test_nonvalidated_input_never_produces_present_component() -> None:
    value = evidence_input()
    validation = validate_walk_forward_oos_input(replace(value, fold_metrics=value.fold_metrics[:-1]))
    result = produce_walk_forward_oos_evidence(validation)
    assert validation.status is WalkForwardInputStatus.TYPED_UNAVAILABLE
    assert result.component.availability is EvidenceAvailability.TYPED_UNAVAILABLE
    assert result.component.pass_rate is None
    assert not result.component.component_ref


def test_component_tamper_is_blocked_by_self_validation() -> None:
    component = produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(evidence_input())).component
    tampered = replace(component, pass_rate=0.0)
    validation = validate_walk_forward_oos_component(tampered)
    assert validation.availability is EvidenceAvailability.BLOCKED
    assert {item.code for item in validation.issues} >= {"component_pass_rate_mismatch", "component_hash_mismatch"}


def test_semantic_tamper_is_blocked_even_if_component_hash_is_recomputed_later() -> None:
    component = produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(evidence_input())).component
    decision = replace(component.fold_evidence[0].metric_decisions[0], passed=False)
    fold = replace(component.fold_evidence[0], metric_decisions=(decision,), outcome=WalkForwardOutcome.FAIL)
    tampered = replace(component, fold_evidence=(fold, *component.fold_evidence[1:]))
    validation = validate_walk_forward_oos_component(tampered)
    assert validation.availability is EvidenceAvailability.BLOCKED
    assert "metric_decision_mismatch" in {item.code for item in validation.issues}
