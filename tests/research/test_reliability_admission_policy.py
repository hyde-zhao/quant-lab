from __future__ import annotations

from engine.cross_strategy_reliability_gates import (
    AdmissionGateMode,
    ArtifactRef,
    GATE_1_STATISTICAL,
    GATE_2_CV,
    GATE_3_PIT_UNIVERSE,
    GATE_4_CAPACITY_IMPACT,
    GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
    ReliabilityGateStatus,
    ReliabilityGateSummary,
    build_shared_gate_summary,
    resolve_admission_policy,
)


MANDATORY_GATE_IDS = (
    GATE_1_STATISTICAL,
    GATE_2_CV,
    GATE_3_PIT_UNIVERSE,
    GATE_4_CAPACITY_IMPACT,
    GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
)


def _summary(gate_id: str, status: ReliabilityGateStatus) -> ReliabilityGateSummary:
    return ReliabilityGateSummary(
        gate_id=gate_id,
        status=status,
        artifact_refs=(
            ArtifactRef(
                artifact_type="contract_ref",
                ref=f"fixture://cr170/{gate_id}",
                owner_gate=gate_id,
                status=status,
            ),
        ),
    )


def _summaries(review_gate: str = GATE_3_PIT_UNIVERSE) -> tuple[ReliabilityGateSummary, ...]:
    return tuple(
        _summary(
            gate_id,
            ReliabilityGateStatus.NEEDS_REVIEW if gate_id == review_gate else ReliabilityGateStatus.PASS,
        )
        for gate_id in MANDATORY_GATE_IDS
    )


def test_protected_shared_merge_preserves_needs_review() -> None:
    summary = build_shared_gate_summary(
        gate_id=GATE_3_PIT_UNIVERSE,
        artifact_refs=(
            ArtifactRef(
                "pit_contract",
                n_a_reason="complete owned fixture boundary",
                owner_gate=GATE_3_PIT_UNIVERSE,
                status=ReliabilityGateStatus.NEEDS_REVIEW,
            ),
        ),
    )
    assert summary.status is ReliabilityGateStatus.NEEDS_REVIEW


def test_t0_mandatory_needs_review_remains_diagnostic_only() -> None:
    result = resolve_admission_policy(
        strategy_class="ml",
        release_profile="exploratory",
        gate_summaries=_summaries(),
    )
    assert result.status is ReliabilityGateStatus.NEEDS_REVIEW
    assert result.gate_mode is AdmissionGateMode.OPT_IN
    assert result.source_rule_id == "cr170-t0-mandatory-needs-review"
    assert "diagnostic-only" in result.release_wording
    assert "passed" not in result.release_wording.lower()
    assert "readiness claim" in result.release_wording


def test_t1_mandatory_needs_review_is_blocked() -> None:
    result = resolve_admission_policy(
        strategy_class="multifactor",
        release_profile="candidate-release",
        gate_summaries=_summaries(GATE_4_CAPACITY_IMPACT),
    )
    assert result.status is ReliabilityGateStatus.BLOCKED
    assert result.gate_mode is AdmissionGateMode.DEFAULT_REQUIRED
    assert result.source_rule_id == "cr170-t1-mandatory-needs-review-blocked"
    assert result.fallback_reason == "mandatory_gate_needs_review"


def test_t2_mandatory_needs_review_is_blocked() -> None:
    result = resolve_admission_policy(
        strategy_class="event-driven",
        release_profile="release-readiness",
        gate_summaries=_summaries(GATE_5_REGIME_ATTRIBUTION_RECONCILIATION),
    )
    assert result.status is ReliabilityGateStatus.BLOCKED
    assert result.gate_mode is AdmissionGateMode.RELEASE_BLOCKING
    assert result.source_rule_id == "cr170-t2-mandatory-needs-review-blocked"


def test_t3_existing_not_authorized_representation_is_unchanged() -> None:
    result = resolve_admission_policy(
        strategy_class="hybrid",
        release_profile="runtime",
        gate_summaries=_summaries(),
    )
    assert result.status is ReliabilityGateStatus.BLOCKED
    assert result.gate_mode is AdmissionGateMode.NOT_AUTHORIZED
    assert result.source_rule_id == "cr154-t3-not-authorized"
    assert result.fallback_reason == "runtime_profile_not_authorized"


def test_unknown_profile_remains_fail_closed() -> None:
    result = resolve_admission_policy(
        strategy_class="ml",
        release_profile="unknown-new-profile",
        gate_summaries=_summaries(),
    )
    assert result.status is ReliabilityGateStatus.BLOCKED
    assert result.fallback_reason == "unknown_release_profile_fail_closed"


def test_resolver_does_not_reinterpret_audit_only_artifact_ref_status() -> None:
    summaries = list(_summaries(review_gate="none"))
    summaries[1] = ReliabilityGateSummary(
        gate_id=GATE_2_CV,
        status=ReliabilityGateStatus.PASS,
        artifact_refs=(
            ArtifactRef(
                artifact_type="g2_p05_n_a_boundary",
                n_a_reason="conditional not-applicable boundary",
                owner_gate=GATE_2_CV,
                status=ReliabilityGateStatus.NEEDS_REVIEW,
                reason_id="gate2_g2_p05_complete_na_requires_review",
            ),
        ),
    )
    result = resolve_admission_policy(
        strategy_class="ml",
        release_profile="candidate-release",
        gate_summaries=summaries,
    )
    assert result.status is ReliabilityGateStatus.PASS


def test_gate_id_order_in_needs_review_wording_is_deterministic() -> None:
    summaries = list(_summaries(GATE_5_REGIME_ATTRIBUTION_RECONCILIATION))
    summaries[0] = _summary(GATE_1_STATISTICAL, ReliabilityGateStatus.NEEDS_REVIEW)
    result = resolve_admission_policy(
        strategy_class="ml",
        release_profile="exploratory",
        gate_summaries=tuple(reversed(summaries)),
    )
    assert result.status is ReliabilityGateStatus.NEEDS_REVIEW
    assert result.release_wording.index(GATE_1_STATISTICAL) < result.release_wording.index(
        GATE_5_REGIME_ATTRIBUTION_RECONCILIATION
    )
