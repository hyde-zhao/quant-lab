"""CR154 local/static cross-strategy reliability gate contracts.

This module only evaluates passed-in fixture/static metadata. It does not read
files, credentials, data lakes, NAS paths, providers, runtime adapters, brokers,
catalogs, registries, event feeds, order systems, or external frameworks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.experiment_family_lineage import FamilyEvidenceProjection, LineageAvailability
from engine.serialization import json_safe
from engine.strategy_admission_statistical_gate import ValidationBoundFamilyEvidence, consume_family_lineage_projection


CR154_RELIABILITY_SCHEMA_VERSION = "cross_strategy_reliability_gates_v1"

GATE_1_STATISTICAL = "gate_1_statistical"
GATE_2_CV = "gate_2_cv"
GATE_3_PIT_UNIVERSE = "gate_3_pit_universe"
GATE_4_CAPACITY_IMPACT = "gate_4_capacity_impact"
GATE_5_REGIME_ATTRIBUTION_RECONCILIATION = "gate_5_regime_attribution_reconciliation"
GATE_6_ADMISSION_POLICY = "gate_6_admission_policy"

GATE_IDS = (
    GATE_1_STATISTICAL,
    GATE_2_CV,
    GATE_3_PIT_UNIVERSE,
    GATE_4_CAPACITY_IMPACT,
    GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
    GATE_6_ADMISSION_POLICY,
)

FORBIDDEN_OPERATION_FIELDS = (
    "credential_read",
    "env_read",
    "real_lake_read",
    "real_lake_write",
    "nas_access",
    "nas_sync",
    "provider_fetch",
    "qmt_runtime",
    "miniqmt_runtime",
    "xtquant_runtime",
    "simulation_paper_live_run",
    "broker_access",
    "trading_operation",
    "feed_listener",
    "real_order_flow",
    "real_reconciliation",
    "store_write",
    "catalog_pointer_mutation",
    "model_registry_write",
    "external_framework_run",
    "git_remote_write",
    "publish_execution",
)

STATISTICAL_ARTIFACT_SLOTS = (
    "multiple_testing_correction_refs",
    "fdr_bh_refs",
    "white_reality_check_or_hansen_spa_refs",
    "pbo_or_cscv_refs",
    "dsr_or_sharpe_ic_deflation_refs",
    "trial_count_and_effective_trials",
    "oos_split_refs",
    "purge_embargo_refs",
    "survivorship_audit_refs",
    "impact_capacity_refs",
    "blocked_claims",
    "release_blocking_reason",
)

IMPACT_MODEL_FAMILIES = ("square_root", "almgren_chriss", "gatheral", "custom", "n/a-with-reason")
STRATEGY_CLASSES = ("multifactor", "ml", "event-driven", "hybrid")
T3_RELEASE_PROFILES = ("paper", "live", "trading", "runtime")
T2_RELEASE_PROFILES = ("release-readiness", "release_readiness", "production-like", "production_like", "simulation-readiness", "simulation_readiness")
T1_RELEASE_PROFILES = ("admission-package", "admission_package", "candidate-release", "candidate_release")
T0_RELEASE_PROFILES = ("exploratory", "research-note", "research_note")


class ReliabilityGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


class AdmissionGateMode(str, Enum):
    OPT_IN = "opt-in"
    DEFAULT_REQUIRED = "default-required"
    RELEASE_BLOCKING = "release-blocking"
    NOT_AUTHORIZED = "not-authorized"


@dataclass(frozen=True, slots=True)
class ReleaseBlockingReason:
    reason_id: str
    message: str
    source_gate: str = ""
    unlock_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class BlockedClaim:
    claim_id: str
    reason: str
    source_gate: str
    release_wording_impact: str
    unlock_condition: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_type: str
    ref: str = ""
    source_cr: str = ""
    owner_gate: str = "shared"
    status: ReliabilityGateStatus | str = ReliabilityGateStatus.PASS
    n_a_reason: str = ""
    reason_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        return dict(json_safe(data))


@dataclass(frozen=True, slots=True)
class TrialCountAndEffectiveTrials:
    raw_trial_count: int
    effective_trial_count: float
    approximation_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class ReliabilityGateSummary:
    gate_id: str
    status: ReliabilityGateStatus | str
    artifact_refs: tuple[ArtifactRef | Mapping[str, Any], ...] = ()
    blocked_claims: tuple[BlockedClaim | Mapping[str, Any], ...] = ()
    release_blocking_reason: ReleaseBlockingReason | Mapping[str, Any] | None = None
    evidence_completeness: str = "complete"
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    family_lineage_projection: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = CR154_RELIABILITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = _status_value(self.status)
        data["artifact_refs"] = [_artifact_dict(item) for item in self.artifact_refs]
        data["blocked_claims"] = [_blocked_claim_dict(item) for item in self.blocked_claims]
        if self.release_blocking_reason is not None:
            data["release_blocking_reason"] = _release_reason_dict(self.release_blocking_reason)
        return dict(json_safe(data))


@dataclass(frozen=True, slots=True)
class AdmissionPolicyResult:
    tier: str
    gate_mode: AdmissionGateMode | str
    status: ReliabilityGateStatus | str
    release_wording: str
    blocked_claims: tuple[BlockedClaim | Mapping[str, Any], ...] = ()
    release_blocking_reason: ReleaseBlockingReason | Mapping[str, Any] | None = None
    fallback_reason: str = ""
    source_rule_id: str = ""
    readiness_disclaimers: tuple[str, ...] = (
        "gate_pass_only_local_static_fixture_contract",
        "not_paper_live_trading_broker_runtime_readiness",
        "not_real_data_validation_or_true_tca",
    )
    schema_version: str = CR154_RELIABILITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["gate_mode"] = _enum_value(self.gate_mode)
        data["status"] = _status_value(self.status)
        data["blocked_claims"] = [_blocked_claim_dict(item) for item in self.blocked_claims]
        if self.release_blocking_reason is not None:
            data["release_blocking_reason"] = _release_reason_dict(self.release_blocking_reason)
        return dict(json_safe(data))


def artifact_ref_to_dict(ref: ArtifactRef | Mapping[str, Any]) -> dict[str, Any]:
    return _artifact_dict(ref)


def blocked_claim_to_dict(claim: BlockedClaim | Mapping[str, Any]) -> dict[str, Any]:
    return _blocked_claim_dict(claim)


def build_shared_gate_summary(
    *,
    gate_id: str,
    artifact_refs: Sequence[ArtifactRef | Mapping[str, Any]] = (),
    blocked_claims: Sequence[BlockedClaim | Mapping[str, Any]] = (),
    release_blocking_reason: ReleaseBlockingReason | Mapping[str, Any] | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    evidence_completeness: str = "complete",
    limitations: Sequence[str] = (),
) -> ReliabilityGateSummary:
    normalized_counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, claims = evaluate_shared_contract(
        artifact_refs=artifact_refs,
        blocked_claims=blocked_claims,
        release_blocking_reason=release_blocking_reason,
        operation_counts=normalized_counts,
        gate_id=gate_id,
    )
    if release_blocking_reason is None:
        release_blocking_reason = reason
    return ReliabilityGateSummary(
        gate_id=gate_id,
        status=status,
        artifact_refs=tuple(artifact_refs),
        blocked_claims=tuple(claims),
        release_blocking_reason=release_blocking_reason,
        evidence_completeness=evidence_completeness,
        operation_counts=normalized_counts,
        limitations=tuple(str(item) for item in limitations if str(item)),
    )


def evaluate_shared_contract(
    *,
    artifact_refs: Sequence[ArtifactRef | Mapping[str, Any]],
    blocked_claims: Sequence[BlockedClaim | Mapping[str, Any]] = (),
    release_blocking_reason: ReleaseBlockingReason | Mapping[str, Any] | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    gate_id: str = "shared",
) -> tuple[ReliabilityGateStatus, ReleaseBlockingReason | None, tuple[BlockedClaim, ...]]:
    normalized_counts = normalize_forbidden_operation_counts(operation_counts)
    claims = [_blocked_claim_from_any(item) for item in blocked_claims]
    nonzero = [key for key, value in normalized_counts.items() if int(value) != 0]
    if nonzero:
        reason = ReleaseBlockingReason(
            reason_id="forbidden_operation_detected",
            message=f"Forbidden operation counters must remain zero: {', '.join(nonzero)}.",
            source_gate=gate_id,
            unlock_condition="remove_real_runtime_data_or_trading_operation_from_CR154_first_wave",
        )
        claims.append(
            BlockedClaim(
                claim_id="runtime_or_real_data_readiness",
                reason=reason.message,
                source_gate=gate_id,
                release_wording_impact="Block paper/live/trading/runtime/real-data wording.",
                unlock_condition=reason.unlock_condition,
            )
        )
        return ReliabilityGateStatus.BLOCKED, reason, tuple(claims)

    artifacts = [_artifact_dict(item) for item in artifact_refs]
    for artifact in artifacts:
        if not str(artifact.get("artifact_type") or "").strip():
            return _blocked_missing("artifact_type", gate_id, claims)
        has_ref = bool(str(artifact.get("ref") or "").strip())
        has_na = bool(str(artifact.get("n_a_reason") or "").strip())
        if not has_ref and not has_na:
            return _blocked_missing(str(artifact.get("artifact_type") or "artifact_ref"), gate_id, claims)

    statuses = {_status_value(artifact.get("status")) for artifact in artifacts}
    if ReliabilityGateStatus.BLOCKED.value in statuses:
        return ReliabilityGateStatus.BLOCKED, _release_reason_from_any(release_blocking_reason), tuple(claims)
    if ReliabilityGateStatus.FAIL.value in statuses:
        return ReliabilityGateStatus.FAIL, _release_reason_from_any(release_blocking_reason), tuple(claims)
    if ReliabilityGateStatus.NEEDS_REVIEW.value in statuses:
        return ReliabilityGateStatus.NEEDS_REVIEW, _release_reason_from_any(release_blocking_reason), tuple(claims)
    return ReliabilityGateStatus.PASS, _release_reason_from_any(release_blocking_reason), tuple(claims)


def normalize_forbidden_operation_counts(operation_counts: Mapping[str, Any] | None = None) -> dict[str, int]:
    data = _as_mapping(operation_counts)
    normalized: dict[str, int] = {}
    for field_name in tuple(FORBIDDEN_OPERATION_FIELDS) + tuple(str(key) for key in data if str(key) not in FORBIDDEN_OPERATION_FIELDS):
        try:
            normalized[field_name] = int(data.get(field_name, 0) or 0)
        except (TypeError, ValueError):
            normalized[field_name] = 1
    return normalized


def evaluate_gate1_statistical_reliability(
    artifacts: Mapping[str, Any],
    *,
    strategy_class: str = "multifactor",
    release_profile: str = "candidate-release",
    claim_types: Sequence[str] = (),
    gate3_summary: ReliabilityGateSummary | Mapping[str, Any] | None = None,
    gate4_summary: ReliabilityGateSummary | Mapping[str, Any] | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    family_lineage_projection: ValidationBoundFamilyEvidence | FamilyEvidenceProjection | Mapping[str, Any] | None = None,
) -> ReliabilityGateSummary:
    lineage = consume_family_lineage_projection(family_lineage_projection)
    projected_artifacts = dict(artifacts)
    if lineage["availability"] == LineageAvailability.PRESENT.value:
        projected_artifacts["trial_count_and_effective_trials"] = {
            "raw_trial_count": lineage["raw_trial_count"],
            "effective_trial_count": None,
            "provenance_ref": lineage["target_ref"],
            "lineage_hash": lineage["target_hash"],
            "effective_trial_count_availability": LineageAvailability.TYPED_UNAVAILABLE.value,
            "effective_trial_count_ref": "",
            "effective_trial_count_method": "",
        }
    counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, blocked = evaluate_shared_contract(
        artifact_refs=_gate1_artifact_refs(projected_artifacts),
        operation_counts=counts,
        gate_id=GATE_1_STATISTICAL,
    )
    if status is ReliabilityGateStatus.BLOCKED:
        return ReliabilityGateSummary(GATE_1_STATISTICAL, status, blocked_claims=blocked, release_blocking_reason=reason, operation_counts=counts, family_lineage_projection=lineage)

    claims = list(blocked)
    refs = list(_gate1_artifact_refs(projected_artifacts))
    source_gate_claims, source_reason = _propagate_gate3_gate4(gate3_summary, gate4_summary, refs, release_profile)
    claims.extend(source_gate_claims)
    if source_reason is not None:
        status = ReliabilityGateStatus.BLOCKED if _is_release_blocking_profile(release_profile) else ReliabilityGateStatus.NEEDS_REVIEW
        reason = source_reason

    if status is ReliabilityGateStatus.PASS:
        severity_status, severity_reason, severity_claims = _gate1_statistical_artifact_policy(projected_artifacts, release_profile, claim_types)
        status = severity_status
        reason = severity_reason
        claims.extend(severity_claims)

    # CR163 supplies only validated raw lineage.  Effective trials remain
    # typed-unavailable, so C1/deflated-performance wording is non-computable.
    claims.append(
        BlockedClaim(
            "effective_trial_count_unavailable",
            "effective trial count is typed_unavailable; C1 is non-computable.",
            GATE_1_STATISTICAL,
            "Block deflated performance and admission-readiness wording.",
            "approve_and_implement_an_effective_trial_count_method_under_a_later_CR",
            evidence_ref=str(lineage.get("target_ref") or ""),
        )
    )
    status = ReliabilityGateStatus.BLOCKED
    reason = ReleaseBlockingReason(
        "effective_trial_count_unavailable",
        "Gate 1 remains blocked because effective trials are unavailable.",
        GATE_1_STATISTICAL,
        "provide_a_separately_approved_effective_trial_count_method",
    )

    return ReliabilityGateSummary(
        gate_id=GATE_1_STATISTICAL,
        status=status,
        artifact_refs=tuple(refs),
        blocked_claims=tuple(_dedupe_blocked_claims(claims)),
        release_blocking_reason=reason,
        operation_counts=counts,
        limitations=("local_static_fixture_only", f"strategy_class={strategy_class}"),
        family_lineage_projection=lineage,
    )


def validate_gate2_cv_governance(
    evidence: Mapping[str, Any],
    *,
    strategy_class: str = "ml",
    release_profile: str = "candidate-release",
    operation_counts: Mapping[str, Any] | None = None,
) -> ReliabilityGateSummary:
    counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, claims = evaluate_shared_contract(artifact_refs=(), operation_counts=counts, gate_id=GATE_2_CV)
    if status is ReliabilityGateStatus.BLOCKED:
        return ReliabilityGateSummary(GATE_2_CV, status, blocked_claims=claims, release_blocking_reason=reason, operation_counts=counts)

    refs: list[ArtifactRef] = []
    blocked: list[BlockedClaim] = []
    split_refs = _refs_from_value(evidence.get("split_policy_ref") or evidence.get("split_policy_refs"), "split_policy_ref", GATE_2_CV)
    walk_forward_refs = _refs_from_value(evidence.get("walk_forward_ref") or evidence.get("walk_forward_refs"), "walk_forward_ref", GATE_2_CV)
    oos_refs = _refs_from_value(evidence.get("oos_ref") or evidence.get("oos_split_refs"), "oos_ref", GATE_2_CV)
    refs.extend(split_refs)
    refs.extend(walk_forward_refs)
    refs.extend(oos_refs)
    if not split_refs and not _has_na_reason(evidence, "split_policy"):
        blocked.append(
            BlockedClaim(
                claim_id="split_policy_missing",
                reason="split policy evidence or n/a-with-reason is required.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block split-governed validation wording.",
                unlock_condition="provide_split_policy_ref_or_structured_na_reason",
            )
        )
    if not walk_forward_refs and not _has_na_reason(evidence, "walk_forward"):
        blocked.append(
            BlockedClaim(
                claim_id="walk_forward_missing",
                reason="walk-forward evidence or n/a-with-reason is required.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block walk-forward validation wording.",
                unlock_condition="provide_walk_forward_ref_or_structured_na_reason",
            )
        )
    if not oos_refs and not _has_na_reason(evidence, "oos"):
        blocked.append(
            BlockedClaim(
                claim_id="oos_split_missing",
                reason="OOS split evidence or n/a-with-reason is required.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block OOS-proven and production-like validation wording.",
                unlock_condition="provide_oos_ref_or_structured_na_reason",
            )
        )
    overlap_applicability = str(evidence.get("overlap_applicability") or "").strip().lower()
    if not overlap_applicability:
        if bool(evidence.get("overlapping_labels_or_windows")):
            overlap_applicability = "overlapping-label-window" if strategy_class == "ml" else "overlapping-event-window"
        else:
            overlap_applicability = "unknown"
    requires_purge = overlap_applicability in {"overlapping-label-window", "overlapping-event-window"}
    if overlap_applicability == "unknown" and strategy_class in {"ml", "event-driven", "hybrid"}:
        blocked.append(
            BlockedClaim(
                claim_id="overlap_applicability_unknown",
                reason="overlap_applicability must be explicit for leakage governance.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block leakage-safe CV wording.",
                unlock_condition="declare_overlap_applicability_or_structured_non_overlap_reason",
            )
        )
    purge_refs = _refs_from_value(evidence.get("purge_embargo_refs") or evidence.get("purge_window_ref") or evidence.get("purge_window_refs"), "purge_embargo_refs", GATE_2_CV)
    embargo_refs = _refs_from_value(evidence.get("embargo_gap_ref") or evidence.get("embargo_gap_refs"), "embargo_gap_ref", GATE_2_CV)
    event_gap_refs = _refs_from_value(evidence.get("event_safe_gap_refs"), "event_safe_gap_refs", GATE_2_CV)
    if requires_purge and not purge_refs:
        na_reason = str(evidence.get("purge_embargo_na_reason") or evidence.get("n_a_reason") or "")
        if not na_reason:
            blocked.append(
                BlockedClaim(
                    claim_id="leakage_safe_cv",
                    reason="purge/embargo evidence or n/a-with-reason is required.",
                    source_gate=GATE_2_CV,
                    release_wording_impact="Block leakage-safe CV wording.",
                    unlock_condition="provide_purge_embargo_ref_or_explicit_non_overlap_reason",
                )
            )
        else:
            refs.append(ArtifactRef("purge_embargo_refs", owner_gate=GATE_2_CV, status=ReliabilityGateStatus.NEEDS_REVIEW, n_a_reason=na_reason))
    if overlap_applicability == "overlapping-label-window" and not embargo_refs:
        blocked.append(
            BlockedClaim(
                claim_id="embargo_gap_missing",
                reason="ML overlapping label windows require embargo gap evidence.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block leakage-safe CV wording.",
                unlock_condition="provide_embargo_gap_ref",
            )
        )
    if overlap_applicability == "overlapping-event-window" and not (embargo_refs or event_gap_refs):
        blocked.append(
            BlockedClaim(
                claim_id="event_safe_gap_missing",
                reason="Event overlapping windows require event-safe gap / embargo analog evidence.",
                source_gate=GATE_2_CV,
                release_wording_impact="Block leakage-safe event validation wording.",
                unlock_condition="provide_event_safe_gap_ref",
            )
        )
    refs.extend(embargo_refs)
    refs.extend(event_gap_refs)
    if overlap_applicability == "non-overlapping-deterministic" and not purge_refs:
        na_reason = str(evidence.get("purge_embargo_na_reason") or evidence.get("n_a_reason") or "")
        if not na_reason:
            blocked.append(
                BlockedClaim(
                    claim_id="non_overlap_na_reason_missing",
                    reason="non-overlapping CV requires an explicit n/a-with-reason for purge/embargo.",
                    source_gate=GATE_2_CV,
                    release_wording_impact="Block leakage-safe CV wording.",
                    unlock_condition="provide_non_overlap_na_reason",
                )
            )
        else:
            refs.append(ArtifactRef("purge_embargo_refs", owner_gate=GATE_2_CV, status=ReliabilityGateStatus.NEEDS_REVIEW, n_a_reason=na_reason))
    refs.extend(purge_refs)
    if blocked and _is_release_blocking_profile(release_profile):
        status = ReliabilityGateStatus.BLOCKED
        reason = ReleaseBlockingReason("missing_purge_embargo_governance", "CV governance evidence is incomplete.", GATE_2_CV)
    elif blocked:
        status = ReliabilityGateStatus.NEEDS_REVIEW
    else:
        status = ReliabilityGateStatus.PASS
    return ReliabilityGateSummary(GATE_2_CV, status, tuple(refs), tuple(blocked), reason, operation_counts=counts)


def validate_gate3_pit_universe(
    evidence: Mapping[str, Any],
    *,
    release_profile: str = "candidate-release",
    operation_counts: Mapping[str, Any] | None = None,
) -> ReliabilityGateSummary:
    counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, claims = evaluate_shared_contract(artifact_refs=(), operation_counts=counts, gate_id=GATE_3_PIT_UNIVERSE)
    if status is ReliabilityGateStatus.BLOCKED:
        return ReliabilityGateSummary(GATE_3_PIT_UNIVERSE, status, blocked_claims=claims, release_blocking_reason=reason, operation_counts=counts)
    refs = list(_refs_from_value(evidence.get("pit_universe_refs"), "pit_universe_refs", GATE_3_PIT_UNIVERSE))
    refs.extend(_refs_from_value(evidence.get("cr153_universe_pit_audit_refs"), "cr153_universe_pit_audit_refs", GATE_3_PIT_UNIVERSE, source_cr="CR-153"))
    lifecycle = str(evidence.get("cr153_slot_lifecycle") or "retained_as_source_ref")
    blocked: list[BlockedClaim] = []
    if lifecycle not in {"retained_as_source_ref", "delegated_to_cr154", "deprecation_deferred"}:
        blocked.append(BlockedClaim("cr153_universe_slot_lifecycle", "CR153 universe_pit_audit lifecycle must be explicit.", GATE_3_PIT_UNIVERSE, "Block PIT universe compatibility wording.", "declare_retained_delegated_or_deferred_lifecycle"))
    if not refs and not str(evidence.get("n_a_reason") or "").strip():
        blocked.append(BlockedClaim("survivorship_free_universe", "PIT / survivorship-free universe refs or n/a-with-reason are required.", GATE_3_PIT_UNIVERSE, "Block survivorship-free and full-history wording.", "provide_local_static_pit_universe_ref_or_na_reason"))
    if blocked:
        status = ReliabilityGateStatus.BLOCKED if _is_release_blocking_profile(release_profile) else ReliabilityGateStatus.NEEDS_REVIEW
        reason = ReleaseBlockingReason("missing_pit_universe_contract", "PIT universe gate evidence is incomplete.", GATE_3_PIT_UNIVERSE)
    else:
        status = ReliabilityGateStatus.PASS
    return ReliabilityGateSummary(GATE_3_PIT_UNIVERSE, status, tuple(refs), tuple(blocked), reason, operation_counts=counts, limitations=("no_real_universe_build",))


def validate_gate4_capacity_impact(
    evidence: Mapping[str, Any],
    *,
    release_profile: str = "candidate-release",
    operation_counts: Mapping[str, Any] | None = None,
) -> ReliabilityGateSummary:
    counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, claims = evaluate_shared_contract(artifact_refs=(), operation_counts=counts, gate_id=GATE_4_CAPACITY_IMPACT)
    if status is ReliabilityGateStatus.BLOCKED:
        return ReliabilityGateSummary(GATE_4_CAPACITY_IMPACT, status, blocked_claims=claims, release_blocking_reason=reason, operation_counts=counts)
    family = str(evidence.get("impact_model_family") or "").strip()
    refs = list(_refs_from_value(evidence.get("impact_model_ref"), "impact_model_ref", GATE_4_CAPACITY_IMPACT))
    refs.extend(_refs_from_value(evidence.get("adv_participation_ref"), "adv_participation_ref", GATE_4_CAPACITY_IMPACT))
    refs.extend(_refs_from_value(evidence.get("capacity_dollars_ref"), "capacity_dollars_ref", GATE_4_CAPACITY_IMPACT))
    refs.extend(_refs_from_value(evidence.get("liquidity_sizing_refs"), "liquidity_sizing_refs", GATE_4_CAPACITY_IMPACT))
    blocked: list[BlockedClaim] = []
    if family not in IMPACT_MODEL_FAMILIES:
        blocked.append(BlockedClaim("impact_model_family_invalid", "impact_model_family must be a controlled enum.", GATE_4_CAPACITY_IMPACT, "Block market-impact wording.", "use_square_root_almgren_chriss_gatheral_custom_or_na_with_reason"))
    if family in {"square_root", "almgren_chriss", "gatheral", "custom"} and not _has_ref(evidence.get("impact_model_ref")):
        blocked.append(BlockedClaim("impact_model_ref_missing", "impact_model_ref is required for active impact model families.", GATE_4_CAPACITY_IMPACT, "Block impact-model wording.", "provide_static_impact_model_ref"))
    if family == "n/a-with-reason" and not str(evidence.get("impact_model_na_reason") or "").strip():
        blocked.append(BlockedClaim("impact_model_na_reason_missing", "n/a-with-reason requires a reason.", GATE_4_CAPACITY_IMPACT, "Block impact-model wording.", "provide_impact_model_na_reason"))
    if family == "n/a-with-reason" and not _has_na_claim_boundary(evidence, "impact_model"):
        blocked.append(BlockedClaim("impact_model_na_boundary_missing", "n/a-with-reason requires claim_limit, owner and trigger.", GATE_4_CAPACITY_IMPACT, "Block impact-model wording.", "provide_claim_limit_owner_and_trigger"))
    if family == "custom":
        custom_policy = _as_mapping(evidence.get("custom_model_policy"))
        missing_custom_fields = [
            field_name
            for field_name in ("custom_model_name", "method_rationale", "input_refs", "validation_boundary", "release_wording_limit")
            if not _truthy_field(custom_policy.get(field_name))
        ]
        if missing_custom_fields:
            blocked.append(BlockedClaim("custom_impact_policy_missing", f"custom impact model policy missing: {', '.join(missing_custom_fields)}.", GATE_4_CAPACITY_IMPACT, "Block custom impact wording.", "provide_complete_custom_model_policy"))
    for field_name, claim_id, impact in (
        ("adv_participation_ref", "adv_participation_missing", "Block scalable capacity wording."),
        ("capacity_dollars_ref", "capacity_dollars_missing", "Block production capacity wording."),
        ("liquidity_sizing_refs", "liquidity_sizing_missing", "Block liquidity sizing wording."),
    ):
        if not _has_ref(evidence.get(field_name)) and not _has_na_reason(evidence, field_name):
            blocked.append(BlockedClaim(claim_id, f"{field_name} evidence or n/a-with-reason is required.", GATE_4_CAPACITY_IMPACT, impact, f"provide_{field_name}_or_structured_na_reason"))
    cost_status = _status_value(evidence.get("cost_underestimation_status") or ReliabilityGateStatus.BLOCKED.value)
    if cost_status != ReliabilityGateStatus.PASS.value and not str(evidence.get("cost_underestimation_na_reason") or "").strip():
        blocked.append(BlockedClaim("cost_underestimation_status_missing", "cost_underestimation_status must be PASS or carry a reason.", GATE_4_CAPACITY_IMPACT, "Block complete cost / true TCA wording.", "provide_cost_underestimation_status_or_reason"))
    if evidence.get("no_real_tca_claim") is not True:
        blocked.append(BlockedClaim("no_real_tca_claim_missing", "CR154 first wave must explicitly avoid real TCA claims.", GATE_4_CAPACITY_IMPACT, "Block true TCA / execution-ready wording.", "set_no_real_tca_claim_true_and_remove_real_execution_claims"))
    if bool(evidence.get("real_tca_claim") or evidence.get("broker_fill_claim") or evidence.get("execution_replay_claim") or evidence.get("order_book_claim") or evidence.get("runtime_calibration_claim") or evidence.get("execution_ready_claim")):
        blocked.append(BlockedClaim("real_tca_not_authorized", "Real TCA, broker fill and execution replay claims are not authorized.", GATE_4_CAPACITY_IMPACT, "Block real TCA / broker readiness wording.", "open_runtime_or_execution_data_authorization_gate"))
    if blocked:
        status = ReliabilityGateStatus.BLOCKED if _is_release_blocking_profile(release_profile) else ReliabilityGateStatus.NEEDS_REVIEW
        reason = ReleaseBlockingReason("capacity_impact_contract_incomplete", "Capacity/impact evidence is incomplete or overclaims real TCA.", GATE_4_CAPACITY_IMPACT)
    else:
        status = ReliabilityGateStatus.PASS
    return ReliabilityGateSummary(GATE_4_CAPACITY_IMPACT, status, tuple(refs), tuple(blocked), reason, operation_counts=counts, limitations=("no_real_tca",))


def validate_gate5_slots(
    evidence: Mapping[str, Any],
    *,
    release_profile: str = "candidate-release",
    operation_counts: Mapping[str, Any] | None = None,
) -> ReliabilityGateSummary:
    counts = normalize_forbidden_operation_counts(operation_counts)
    status, reason, claims = evaluate_shared_contract(artifact_refs=(), operation_counts=counts, gate_id=GATE_5_REGIME_ATTRIBUTION_RECONCILIATION)
    if status is ReliabilityGateStatus.BLOCKED:
        return ReliabilityGateSummary(GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, status, blocked_claims=claims, release_blocking_reason=reason, operation_counts=counts)
    refs: list[ArtifactRef] = []
    blocked: list[BlockedClaim] = []
    if evidence.get("no_runtime_reconciliation_claim") is not True:
        blocked.append(
            BlockedClaim(
                "no_runtime_reconciliation_claim_missing",
                "CR154 first wave must explicitly avoid runtime/broker reconciliation claims.",
                GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
                "Block reconciliation-ready wording.",
                "set_no_runtime_reconciliation_claim_true_and_remove_runtime_reconciliation_claims",
            )
        )
    for slot, expected_type in (("regime_slots", "regime"), ("attribution_slots", "attribution"), ("reconciliation_slots", "reconciliation")):
        slot_items = _as_sequence(evidence.get(slot))
        if not slot_items:
            if _has_na_reason(evidence, slot) and _has_na_claim_boundary(evidence, slot):
                refs.append(ArtifactRef(slot, owner_gate=GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, status=ReliabilityGateStatus.NEEDS_REVIEW, n_a_reason=str(evidence.get(f"{slot}_na_reason") or evidence.get("n_a_reason") or "")))
            else:
                blocked.append(BlockedClaim(slot, f"{slot} requires structured slot refs or n/a-with-reason.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {slot} readiness wording.", f"provide_{slot}_refs_or_structured_na_reason"))
        for item in slot_items:
            slot_ref, slot_claims = _validate_gate5_slot(item, expected_type)
            refs.extend(slot_ref)
            blocked.extend(slot_claims)
    if bool(
        evidence.get("real_reconciliation_claim")
        or evidence.get("broker_reconciliation_claim")
        or evidence.get("broker_account_claim")
        or evidence.get("order_reconciliation_claim")
        or evidence.get("cash_position_claim")
        or evidence.get("offline_live_reconciliation_claim")
        or evidence.get("paper_live_reconciliation_claim")
    ):
        blocked.append(BlockedClaim("real_reconciliation_not_authorized", "Real broker/runtime reconciliation is not authorized in CR154.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, "Block real reconciliation wording.", "open_runtime_reconciliation_authorization_gate"))
    if blocked:
        status = ReliabilityGateStatus.BLOCKED if _is_release_blocking_profile(release_profile) else ReliabilityGateStatus.NEEDS_REVIEW
        reason = ReleaseBlockingReason("gate5_slots_incomplete", "Gate 5 slots are incomplete or overclaim real reconciliation.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION)
    else:
        status = ReliabilityGateStatus.PASS
    return ReliabilityGateSummary(GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, status, tuple(refs), tuple(blocked), reason, operation_counts=counts, limitations=("no_real_reconciliation",))


def resolve_admission_policy(
    *,
    strategy_class: str,
    release_profile: str,
    gate_summaries: Sequence[ReliabilityGateSummary | Mapping[str, Any]],
    requested_claims: Sequence[str] = (),
    operation_counts: Mapping[str, Any] | None = None,
) -> AdmissionPolicyResult:
    normalized_strategy = _normalize_strategy_class(strategy_class)
    normalized_profile = _normalize_release_profile(release_profile)
    counts = normalize_forbidden_operation_counts(operation_counts)
    all_claims: list[BlockedClaim] = []
    for summary in gate_summaries:
        all_claims.extend(_blocked_claim_from_any(item) for item in _as_sequence(_summary_dict(summary).get("blocked_claims")))
    nonzero = [key for key, value in counts.items() if value != 0]
    if normalized_strategy == "unknown":
        return _policy_blocked("UNKNOWN", AdmissionGateMode.RELEASE_BLOCKING, "unknown_strategy_class", "Unknown strategy class must fail closed.", all_claims)
    if normalized_profile == "unknown":
        return _policy_blocked("UNKNOWN", AdmissionGateMode.RELEASE_BLOCKING, "unknown_release_profile_fail_closed", "Unknown release profile must fail closed.", all_claims)
    if normalized_profile in T3_RELEASE_PROFILES:
        return _policy_blocked("T3", AdmissionGateMode.NOT_AUTHORIZED, "runtime_profile_not_authorized", "Paper/live/trading/runtime profiles are not authorized by CR154.", all_claims, wording="not-authorized; no paper/live/trading/broker/runtime readiness")
    if nonzero:
        return _policy_blocked("T2", AdmissionGateMode.RELEASE_BLOCKING, "forbidden_operation_detected", "Forbidden operation counters must remain zero.", all_claims)

    tier, mode = _tier_and_mode(normalized_profile)
    gate_data = [_summary_dict(summary) for summary in gate_summaries]
    gate_statuses = [_status_value(summary.get("status")) for summary in gate_data]
    present_gate_ids = {str(summary.get("gate_id") or "").strip() for summary in gate_data}
    mandatory_gate_ids = {GATE_1_STATISTICAL, GATE_2_CV, GATE_3_PIT_UNIVERSE, GATE_4_CAPACITY_IMPACT, GATE_5_REGIME_ATTRIBUTION_RECONCILIATION}
    has_distinct_mandatory_gates = mandatory_gate_ids <= present_gate_ids
    if tier == "T2" and any(status in {ReliabilityGateStatus.BLOCKED.value, ReliabilityGateStatus.FAIL.value} for status in gate_statuses):
        return _policy_blocked(tier, mode, "mandatory_gate_evidence_blocked", "Release-readiness wording requires Gate 1-5 not blocked or failed.", all_claims)
    if tier == "T2" and not has_distinct_mandatory_gates:
        return _policy_blocked(tier, mode, "mandatory_gate_evidence_missing", "Release-readiness wording requires Gate 1-5 evidence.", all_claims)
    if tier == "T1" and not has_distinct_mandatory_gates:
        return _policy_blocked(tier, mode, "default_required_gate_evidence_missing", "Admission candidate wording requires explicit Gate 1-5 evidence or structured n/a reasons.", all_claims)
    if tier == "T1" and any(status in {ReliabilityGateStatus.BLOCKED.value, ReliabilityGateStatus.FAIL.value} for status in gate_statuses):
        return _policy_blocked(tier, mode, "default_required_gate_blocked", "Admission candidate wording cannot bypass blocked gates.", all_claims)

    requested = {str(claim) for claim in requested_claims}
    wording = "local/static/fixture reliability gate contract passed; not paper/live/trading/broker/runtime readiness"
    normalized_requested = {claim.strip().lower().replace("-", "_") for claim in requested}
    if normalized_requested & {"paper_ready", "paper_readiness", "live_ready", "live_readiness", "trading_ready", "trading_readiness", "broker_ready", "broker_readiness", "runtime_ready", "runtime_readiness"}:
        return _policy_blocked(tier, mode, "runtime_readiness_claim_not_authorized", "Runtime readiness claims are not authorized.", all_claims)
    return AdmissionPolicyResult(tier=tier, gate_mode=mode, status=ReliabilityGateStatus.PASS, release_wording=wording, blocked_claims=tuple(_dedupe_blocked_claims(all_claims)), source_rule_id=f"cr154-{tier.lower()}-{_enum_value(mode)}")


def fixture_cases_shared_contract() -> tuple[dict[str, Any], ...]:
    return (
        {
            "case_id": "shared_minimal_pass",
            "summary": build_shared_gate_summary(
                gate_id="shared",
                artifact_refs=(ArtifactRef("contract_ref", "fixture://cr154/shared/pass", owner_gate="shared"),),
            ).to_dict(),
            "expected_status": ReliabilityGateStatus.PASS.value,
        },
        {
            "case_id": "shared_forbidden_operation_blocked",
            "summary": build_shared_gate_summary(
                gate_id="shared",
                artifact_refs=(ArtifactRef("contract_ref", "fixture://cr154/shared/blocked", owner_gate="shared"),),
                operation_counts={"credential_read": 1},
            ).to_dict(),
            "expected_status": ReliabilityGateStatus.BLOCKED.value,
        },
    )


def _gate1_artifact_refs(artifacts: Mapping[str, Any]) -> tuple[ArtifactRef, ...]:
    refs: list[ArtifactRef] = []
    for slot in STATISTICAL_ARTIFACT_SLOTS:
        if slot in {"blocked_claims", "release_blocking_reason", "trial_count_and_effective_trials"}:
            continue
        refs.extend(_refs_from_value(artifacts.get(slot), slot, GATE_1_STATISTICAL))
    return tuple(refs)


def _gate1_statistical_artifact_policy(
    artifacts: Mapping[str, Any],
    release_profile: str,
    claim_types: Sequence[str],
) -> tuple[ReliabilityGateStatus, ReleaseBlockingReason | None, tuple[BlockedClaim, ...]]:
    claims = {str(item) for item in claim_types}
    blocked: list[BlockedClaim] = []
    needs_review: list[BlockedClaim] = []
    wrc_refs = _as_sequence(artifacts.get("white_reality_check_or_hansen_spa_refs"))
    multiple_testing_refs = _as_sequence(artifacts.get("multiple_testing_correction_refs"))
    fdr_bh_refs = _as_sequence(artifacts.get("fdr_bh_refs"))
    pbo_refs = _as_sequence(artifacts.get("pbo_or_cscv_refs"))
    dsr_refs = _as_sequence(artifacts.get("dsr_or_sharpe_ic_deflation_refs"))
    trial = _as_mapping(artifacts.get("trial_count_and_effective_trials"))
    if _is_release_blocking_profile(release_profile) or {"statistical_significance", "performance_robustness", "production_like"} & claims:
        if not multiple_testing_refs and not str(artifacts.get("multiple_testing_correction_na_reason") or "").strip():
            blocked.append(BlockedClaim("multiple_testing_correction", "multiple-testing correction refs are required.", GATE_1_STATISTICAL, "Block statistical reliability wording.", "provide_multiple_testing_correction_ref_or_na_reason"))
        if not fdr_bh_refs and not str(artifacts.get("fdr_bh_na_reason") or "").strip():
            blocked.append(BlockedClaim("fdr_bh_correction", "FDR/BH or equivalent refs are required.", GATE_1_STATISTICAL, "Block FDR/significance wording.", "provide_fdr_bh_or_equivalent_ref_or_na_reason"))
    if not wrc_refs:
        claim = BlockedClaim("statistical_significance", "WRC/SPA or equivalent data-snooping correction is missing.", GATE_1_STATISTICAL, "Block statistical significance / robustness wording.", "provide_wrc_spa_or_equivalent_ref")
        if _is_release_blocking_profile(release_profile) or "statistical_significance" in claims:
            blocked.append(claim)
        else:
            needs_review.append(claim)
    if _is_release_blocking_profile(release_profile) and not pbo_refs:
        blocked.append(BlockedClaim("performance_robustness", "PBO/CSCV evidence is missing.", GATE_1_STATISTICAL, "Block performance robustness wording.", "provide_pbo_or_cscv_ref"))
    if {"sharpe", "ic", "performance_robustness"} & claims and not dsr_refs:
        blocked.append(BlockedClaim("sharpe_ic_reliability", "DSR / Sharpe / IC deflation evidence is missing.", GATE_1_STATISTICAL, "Block Sharpe/IC reliability wording.", "provide_dsr_or_deflation_ref"))
    if (pbo_refs or dsr_refs or _is_release_blocking_profile(release_profile)) and not _valid_trial_counts(trial):
        blocked.append(BlockedClaim("trial_count_policy", "raw_trial_count and effective_trial_count must be >= 1, effective_trial_count must not exceed raw_trial_count without approximation_reason, and provenance_ref is required.", GATE_1_STATISTICAL, "Block deflated performance wording.", "provide_valid_trial_counts"))
    if _trial_counts_need_review(trial):
        needs_review.append(
            BlockedClaim(
                "trial_count_approximation_review",
                "effective_trial_count exceeds raw_trial_count and relies on approximation_reason.",
                GATE_1_STATISTICAL,
                "Restrict deflated performance wording pending review.",
                "review_effective_trial_count_approximation",
            )
        )
    if blocked:
        return ReliabilityGateStatus.BLOCKED, ReleaseBlockingReason("statistical_reliability_artifact_missing", "Gate 1 mandatory statistical reliability artifacts are missing.", GATE_1_STATISTICAL), tuple(blocked)
    if needs_review:
        return ReliabilityGateStatus.NEEDS_REVIEW, None, tuple(needs_review)
    return ReliabilityGateStatus.PASS, None, ()


def _propagate_gate3_gate4(
    gate3_summary: ReliabilityGateSummary | Mapping[str, Any] | None,
    gate4_summary: ReliabilityGateSummary | Mapping[str, Any] | None,
    refs: list[ArtifactRef],
    release_profile: str,
) -> tuple[tuple[BlockedClaim, ...], ReleaseBlockingReason | None]:
    claims: list[BlockedClaim] = []
    reason: ReleaseBlockingReason | None = None
    for gate_id, summary, slot, claim_id in (
        (GATE_3_PIT_UNIVERSE, gate3_summary, "survivorship_audit_refs", "survivorship_free"),
        (GATE_4_CAPACITY_IMPACT, gate4_summary, "impact_capacity_refs", "capacity_scalable"),
    ):
        data = _summary_dict(summary)
        if not data:
            continue
        status = _status_value(data.get("status"))
        if status in {ReliabilityGateStatus.BLOCKED.value, ReliabilityGateStatus.FAIL.value, ReliabilityGateStatus.NEEDS_REVIEW.value}:
            refs.append(ArtifactRef(slot, ref=str(data.get("gate_ref") or f"summary://{gate_id}"), owner_gate=GATE_1_STATISTICAL, status=status, source_cr="CR-154", reason_id=str(data.get("release_blocking_reason", {}).get("reason_id") if isinstance(data.get("release_blocking_reason"), Mapping) else "")))
            claims.append(BlockedClaim(claim_id, f"{gate_id} status is {status}.", gate_id, f"Block {claim_id} wording.", f"resolve_{gate_id}"))
            if status in {ReliabilityGateStatus.BLOCKED.value, ReliabilityGateStatus.FAIL.value} or _is_release_blocking_profile(release_profile):
                reason = ReleaseBlockingReason(f"{gate_id}_propagated_blocker", f"{gate_id} prevents clean Gate 1 reliability wording.", gate_id)
    return tuple(claims), reason


def _refs_from_value(value: Any, artifact_type: str, owner_gate: str, source_cr: str = "CR-154") -> tuple[ArtifactRef, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, ArtifactRef):
        return (value,)
    if isinstance(value, Mapping):
        data = dict(value)
        return (
            ArtifactRef(
                artifact_type=str(data.get("artifact_type") or artifact_type),
                ref=str(data.get("ref") or data.get("path") or ""),
                source_cr=str(data.get("source_cr") or source_cr),
                owner_gate=str(data.get("owner_gate") or owner_gate),
                status=str(data.get("status") or ReliabilityGateStatus.PASS.value),
                n_a_reason=str(data.get("n_a_reason") or data.get("na_reason") or ""),
                reason_id=str(data.get("reason_id") or ""),
            ),
        )
    if isinstance(value, str):
        return (ArtifactRef(artifact_type, value, source_cr=source_cr, owner_gate=owner_gate),)
    refs: list[ArtifactRef] = []
    for item in _as_sequence(value):
        refs.extend(_refs_from_value(item, artifact_type, owner_gate, source_cr=source_cr))
    return tuple(refs)


def _valid_trial_counts(trial: Mapping[str, Any]) -> bool:
    try:
        raw = int(trial.get("raw_trial_count", 0) or 0)
        effective = float(trial.get("effective_trial_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    has_provenance = bool(str(trial.get("provenance_ref") or trial.get("trial_count_ref") or "").strip())
    if raw < 1 or effective < 1 or not has_provenance:
        return False
    return effective <= raw or bool(str(trial.get("approximation_reason") or "").strip())


def _trial_counts_need_review(trial: Mapping[str, Any]) -> bool:
    try:
        raw = int(trial.get("raw_trial_count", 0) or 0)
        effective = float(trial.get("effective_trial_count", 0) or 0)
    except (TypeError, ValueError):
        return False
    return raw >= 1 and effective > raw and bool(str(trial.get("approximation_reason") or "").strip())


def _has_ref(value: Any) -> bool:
    return any(bool(str(ref.ref or "").strip()) for ref in _refs_from_value(value, "ref", "shared"))


def _has_na_reason(evidence: Mapping[str, Any], prefix: str) -> bool:
    candidates = (
        f"{prefix}_na_reason",
        f"{prefix}_n_a_reason",
        "n_a_reason",
        "na_reason",
    )
    return any(bool(str(evidence.get(name) or "").strip()) for name in candidates)


def _has_na_claim_boundary(evidence: Mapping[str, Any], prefix: str) -> bool:
    return all(
        bool(str(evidence.get(field_name) or evidence.get(f"{prefix}_{field_name}") or "").strip())
        for field_name in ("claim_limit", "owner", "trigger")
    )


def _truthy_field(value: Any) -> bool:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(tuple(value))
    return bool(str(value or "").strip())


def _validate_gate5_slot(item: Any, expected_type: str) -> tuple[tuple[ArtifactRef, ...], tuple[BlockedClaim, ...]]:
    data = _as_mapping(item)
    claims: list[BlockedClaim] = []
    refs: list[ArtifactRef] = []
    if not data:
        claims.append(
            BlockedClaim(
                f"{expected_type}_slot_shape_invalid",
                "Gate 5 slots must be structured objects, not bare refs.",
                GATE_5_REGIME_ATTRIBUTION_RECONCILIATION,
                f"Block {expected_type} slot wording.",
                "provide_structured_gate5_slot",
            )
        )
        return (), tuple(claims)

    slot_id = str(data.get("slot_id") or "").strip()
    slot_type = str(data.get("slot_type") or "").strip()
    status = _status_value(data.get("status") or ReliabilityGateStatus.BLOCKED.value)
    if not slot_id:
        claims.append(BlockedClaim(f"{expected_type}_slot_id_missing", "slot_id is required.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "provide_slot_id"))
    if slot_type != expected_type:
        claims.append(BlockedClaim(f"{expected_type}_slot_type_invalid", f"slot_type must be {expected_type}.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "provide_valid_slot_type"))
    if status in {ReliabilityGateStatus.BLOCKED.value, ReliabilityGateStatus.FAIL.value}:
        claims.append(BlockedClaim(f"{expected_type}_slot_status_blocked", f"{expected_type} slot status is {status}.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "resolve_slot_status"))
    for field_name in ("owner", "claim_limit", "last_review_ref"):
        if not str(data.get(field_name) or "").strip():
            claims.append(BlockedClaim(f"{expected_type}_slot_{field_name}_missing", f"{field_name} is required.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", f"provide_{field_name}"))
    if not _as_sequence(data.get("limitations")):
        claims.append(BlockedClaim(f"{expected_type}_slot_limitations_missing", "limitations are required.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "provide_slot_limitations"))

    refs.extend(_refs_from_value(data.get("refs"), f"{expected_type}_slot_refs", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION))
    na_reason = str(data.get("n_a_reason") or data.get("na_reason") or "").strip()
    if not refs and not na_reason:
        claims.append(BlockedClaim(f"{expected_type}_slot_refs_missing", "slot refs or n/a-with-reason are required.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "provide_slot_refs_or_na_reason"))
    if na_reason and not all(str(data.get(field_name) or "").strip() for field_name in ("owner", "claim_limit", "last_review_ref")):
        claims.append(BlockedClaim(f"{expected_type}_slot_na_boundary_missing", "n/a slots require owner, claim_limit and last_review_ref.", GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, f"Block {expected_type} slot wording.", "provide_na_owner_claim_limit_last_review"))
        refs.append(ArtifactRef(f"{expected_type}_slot_refs", owner_gate=GATE_5_REGIME_ATTRIBUTION_RECONCILIATION, status=ReliabilityGateStatus.NEEDS_REVIEW, n_a_reason=na_reason))
    if refs:
        return tuple(refs), tuple(claims)
    return (), tuple(claims)


def _policy_blocked(
    tier: str,
    mode: AdmissionGateMode,
    reason_id: str,
    message: str,
    blocked_claims: Sequence[BlockedClaim],
    *,
    wording: str = "release-blocking; local/static/fixture gate evidence incomplete",
) -> AdmissionPolicyResult:
    reason = ReleaseBlockingReason(reason_id, message, GATE_6_ADMISSION_POLICY)
    claims = list(blocked_claims)
    claims.append(BlockedClaim(reason_id, message, GATE_6_ADMISSION_POLICY, "Block release / readiness wording.", "resolve_CR154_gate_policy_blocker"))
    return AdmissionPolicyResult(
        tier=tier,
        gate_mode=mode,
        status=ReliabilityGateStatus.BLOCKED,
        release_wording=wording,
        blocked_claims=tuple(_dedupe_blocked_claims(claims)),
        release_blocking_reason=reason,
        fallback_reason=reason_id,
        source_rule_id=f"cr154-{tier.lower()}-{_enum_value(mode)}",
    )


def _tier_and_mode(profile: str) -> tuple[str, AdmissionGateMode]:
    if profile in T0_RELEASE_PROFILES:
        return "T0", AdmissionGateMode.OPT_IN
    if profile in T1_RELEASE_PROFILES:
        return "T1", AdmissionGateMode.DEFAULT_REQUIRED
    if profile in T2_RELEASE_PROFILES:
        return "T2", AdmissionGateMode.RELEASE_BLOCKING
    return "UNKNOWN", AdmissionGateMode.RELEASE_BLOCKING


def _normalize_strategy_class(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("_", "-")
    return normalized if normalized in STRATEGY_CLASSES else "unknown"


def _normalize_release_profile(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in set(T0_RELEASE_PROFILES + T1_RELEASE_PROFILES + T2_RELEASE_PROFILES + T3_RELEASE_PROFILES) else "unknown"


def _is_release_blocking_profile(profile: str) -> bool:
    normalized = _normalize_release_profile(profile)
    return normalized in set(T1_RELEASE_PROFILES + T2_RELEASE_PROFILES + T3_RELEASE_PROFILES)


def _blocked_missing(field_name: str, gate_id: str, claims: list[BlockedClaim]) -> tuple[ReliabilityGateStatus, ReleaseBlockingReason, tuple[BlockedClaim, ...]]:
    reason = ReleaseBlockingReason("missing_mandatory_artifact", f"{field_name} is mandatory for CR154 reliability gates.", gate_id)
    claims.append(BlockedClaim(field_name, reason.message, gate_id, f"Block wording depending on {field_name}.", "provide_ref_or_na_with_reason"))
    return ReliabilityGateStatus.BLOCKED, reason, tuple(claims)


def _artifact_dict(ref: ArtifactRef | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(ref, ArtifactRef):
        return ref.to_dict()
    data = dict(_as_mapping(ref))
    if "status" in data:
        data["status"] = _status_value(data["status"])
    return dict(json_safe(data))


def _blocked_claim_dict(claim: BlockedClaim | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(claim, BlockedClaim):
        return claim.to_dict()
    return dict(json_safe(dict(_as_mapping(claim))))


def _blocked_claim_from_any(claim: BlockedClaim | Mapping[str, Any]) -> BlockedClaim:
    if isinstance(claim, BlockedClaim):
        return claim
    data = _as_mapping(claim)
    return BlockedClaim(
        claim_id=str(data.get("claim_id") or data.get("claim") or ""),
        reason=str(data.get("reason") or data.get("message") or ""),
        source_gate=str(data.get("source_gate") or ""),
        release_wording_impact=str(data.get("release_wording_impact") or data.get("limitation") or ""),
        unlock_condition=str(data.get("unlock_condition") or ""),
        evidence_ref=str(data.get("evidence_ref") or ""),
    )


def _release_reason_dict(reason: ReleaseBlockingReason | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(reason, ReleaseBlockingReason):
        return reason.to_dict()
    return dict(json_safe(dict(_as_mapping(reason))))


def _release_reason_from_any(reason: ReleaseBlockingReason | Mapping[str, Any] | None) -> ReleaseBlockingReason | None:
    if reason is None:
        return None
    if isinstance(reason, ReleaseBlockingReason):
        return reason
    data = _as_mapping(reason)
    if not data:
        return None
    return ReleaseBlockingReason(
        reason_id=str(data.get("reason_id") or ""),
        message=str(data.get("message") or ""),
        source_gate=str(data.get("source_gate") or ""),
        unlock_condition=str(data.get("unlock_condition") or ""),
    )


def _summary_dict(summary: ReliabilityGateSummary | Mapping[str, Any] | None) -> dict[str, Any]:
    if summary is None:
        return {}
    if isinstance(summary, ReliabilityGateSummary):
        return summary.to_dict()
    return dict(json_safe(dict(_as_mapping(summary))))


def _dedupe_blocked_claims(claims: Sequence[BlockedClaim]) -> tuple[BlockedClaim, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[BlockedClaim] = []
    for claim in claims:
        key = (claim.claim_id, claim.source_gate, claim.reason)
        if key not in seen:
            seen.add(key)
            result.append(claim)
    return tuple(result)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "to_dict"):
        maybe = value.to_dict()
        if isinstance(maybe, Mapping):
            return maybe
    return {}


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, Mapping, ArtifactRef, BlockedClaim)):
        return (value,)
    try:
        return tuple(value)
    except TypeError:
        return (value,)


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _status_value(value: Any) -> str:
    normalized = _enum_value(value).strip().upper()
    if normalized in {item.value for item in ReliabilityGateStatus}:
        return normalized
    return ReliabilityGateStatus.BLOCKED.value


def project_computable_statistical_evidence(summary: Any) -> dict[str, Any]:
    """Map CR164 evidence into existing Gate-1 artifact slots without a new gate."""

    from engine.statistical_evidence import EvidenceStatus, StatisticalEvidenceSummary, project_summary

    if not isinstance(summary, StatisticalEvidenceSummary):
        return {
            "status": ReliabilityGateStatus.BLOCKED.value,
            "artifacts": {},
            "blocked_claims": ("computable_statistical_summary_untrusted_or_unavailable",),
            "effective_trial_count_availability": EvidenceStatus.TYPED_UNAVAILABLE.value,
        }
    projection = project_summary(summary, consumer_id="cr154-cross-strategy-reliability")
    refs_by_method = {item.method.value: item.evidence_ref for item in summary.method_evidences}
    status = {
        EvidenceStatus.PASS: ReliabilityGateStatus.PASS.value,
        EvidenceStatus.FAIL: ReliabilityGateStatus.FAIL.value,
        EvidenceStatus.TYPED_UNAVAILABLE: ReliabilityGateStatus.BLOCKED.value,
        EvidenceStatus.BLOCKED: ReliabilityGateStatus.BLOCKED.value,
    }[summary.status]
    return dict(
        json_safe(
            {
                "status": status,
                "summary_projection": projection,
                "artifacts": {
                    "multiple_testing_correction_refs": tuple(
                        ref for method, ref in refs_by_method.items() if method in {"bh", "wrc", "spa"} and ref
                    ),
                    "fdr_bh_refs": (refs_by_method["bh"],) if refs_by_method.get("bh") else (),
                    "white_reality_check_or_hansen_spa_refs": tuple(
                        refs_by_method[method] for method in ("wrc", "spa") if refs_by_method.get(method)
                    ),
                    "pbo_or_cscv_refs": (refs_by_method["pbo_cscv"],) if refs_by_method.get("pbo_cscv") else (),
                    "dsr_or_sharpe_ic_deflation_refs": (refs_by_method["dsr"],) if refs_by_method.get("dsr") else (),
                    "trial_count_and_effective_trials": {
                        "raw_trial_count": summary.method_evidences[0].raw_trial_count if summary.method_evidences else None,
                        "effective_trial_count": None,
                        "effective_trial_count_ref": "",
                        "effective_trial_count_method": "",
                        "effective_trial_count_availability": EvidenceStatus.TYPED_UNAVAILABLE.value,
                    },
                },
                "blocked_claims": () if status == ReliabilityGateStatus.PASS.value else tuple(summary.reason_codes),
                "effective_trial_count_availability": EvidenceStatus.TYPED_UNAVAILABLE.value,
            }
        )
    )


__all__ = [
    "AdmissionGateMode",
    "AdmissionPolicyResult",
    "ArtifactRef",
    "BlockedClaim",
    "CR154_RELIABILITY_SCHEMA_VERSION",
    "FORBIDDEN_OPERATION_FIELDS",
    "GATE_1_STATISTICAL",
    "GATE_2_CV",
    "GATE_3_PIT_UNIVERSE",
    "GATE_4_CAPACITY_IMPACT",
    "GATE_5_REGIME_ATTRIBUTION_RECONCILIATION",
    "GATE_6_ADMISSION_POLICY",
    "IMPACT_MODEL_FAMILIES",
    "ReliabilityGateStatus",
    "ReliabilityGateSummary",
    "ReleaseBlockingReason",
    "STATISTICAL_ARTIFACT_SLOTS",
    "TrialCountAndEffectiveTrials",
    "artifact_ref_to_dict",
    "blocked_claim_to_dict",
    "build_shared_gate_summary",
    "evaluate_gate1_statistical_reliability",
    "evaluate_shared_contract",
    "fixture_cases_shared_contract",
    "normalize_forbidden_operation_counts",
    "project_computable_statistical_evidence",
    "resolve_admission_policy",
    "validate_gate2_cv_governance",
    "validate_gate3_pit_universe",
    "validate_gate4_capacity_impact",
    "validate_gate5_slots",
]
