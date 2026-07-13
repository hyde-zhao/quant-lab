"""CR-166 deterministic Walk-forward/OOS evidence contracts and producer.

All inputs are explicit immutable values.  The module performs no file, env,
credential, provider, lake, runtime, broker, registry, or network operation.
Evidence refs are classified as strings only and are never dereferenced.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Mapping, Sequence

from engine.strategy_evidence import (
    ComponentDescriptor,
    EvidenceAvailability,
    StrategyEvidenceEnvelope,
    build_strategy_evidence_envelope,
    canonical_hash,
    canonical_json_value,
)


WALK_FORWARD_OOS_INPUT_SCHEMA_VERSION = "walk_forward_oos_input_v1"
WALK_FORWARD_OOS_COMPONENT_SCHEMA_VERSION = "walk_forward_oos_component_v1"
WALK_FORWARD_OOS_COMPONENT_CATALOG_VERSION = "v1"
WALK_FORWARD_OOS_PRODUCER_VERSION = "cr166_v1"

INPUT_HASH_DOMAIN = "quant-lab.walk-forward-oos.input.v1"
CONFIG_HASH_DOMAIN = "quant-lab.walk-forward-oos.config.v1"
COMPONENT_HASH_DOMAIN = "quant-lab.walk-forward-oos.component.v1"
FOLD_MEMBERSHIP_HASH_DOMAIN = "quant-lab.walk-forward-oos.fold-membership.v1"

ALLOWED_STATIC_REF_CLASSES = frozenset({"fixture", "static", "synthetic", "logical"})
ALLOWED_VALIDATION_MODES = frozenset({"fixture", "static", "fixture-static", "local-static"})


class WalkForwardInputStatus(str, Enum):
    VALIDATED = "validated"
    TYPED_UNAVAILABLE = "typed_unavailable"
    BLOCKED = "blocked"


class WalkForwardOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class FoldManifest:
    manifest_id: str
    manifest_ref: str
    manifest_hash: str
    declared_fold_count: int
    ordered_fold_ids: tuple[str, ...]
    membership_hash: str

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class SplitPolicy:
    policy_id: str
    strategy_kind: str
    mode: str
    window_unit: str
    policy_ref: str
    schema_version: str

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class TemporalFold:
    fold_id: str
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    oos_start: str
    oos_end: str

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class PurgeEmbargoPolicy:
    overlap_applicability: str
    unit: str
    label_or_window_horizon: int
    purge_required: int
    purge_applied: int
    embargo_required: int
    embargo_applied: int
    purge_policy_ref: str
    embargo_policy_ref: str

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class MetricPolicy:
    metric_id: str
    direction: str
    threshold: float
    mandatory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class FoldMetricValue:
    fold_id: str
    metric_id: str
    value: float

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class LineageBinding:
    lineage_ref: str
    lineage_hash: str
    fold_membership_hash: str
    source_refs: tuple[str, ...]
    source_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class AuthorizationMetadata:
    validation_mode: str
    ref_class: str
    authorization_ref: str = ""
    operation_counts: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class WalkForwardEvidenceInput:
    subject_ref: str
    manifest: FoldManifest | None
    split_policy: SplitPolicy | None
    folds: tuple[TemporalFold, ...]
    leakage_policy: PurgeEmbargoPolicy | None
    metric_policies: tuple[MetricPolicy, ...]
    fold_metrics: tuple[FoldMetricValue, ...]
    lineage: LineageBinding | None
    authorization: AuthorizationMetadata | None
    schema_version: str = WALK_FORWARD_OOS_INPUT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class WalkForwardValidationIssue:
    code: str
    field: str
    message: str
    severity: str
    fold_id: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WalkForwardInputValidation:
    status: WalkForwardInputStatus
    evidence_input: WalkForwardEvidenceInput
    issues: tuple[WalkForwardValidationIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status is WalkForwardInputStatus.VALIDATED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "evidence_input": self.evidence_input.to_dict(),
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True)
class MetricDecision:
    metric_id: str
    value: float
    direction: str
    threshold: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(asdict(self))


@dataclass(frozen=True, slots=True)
class FoldEvidence:
    fold_id: str
    metric_decisions: tuple[MetricDecision, ...]
    outcome: WalkForwardOutcome
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["outcome"] = self.outcome.value
        return canonical_json_value(data)


@dataclass(frozen=True, slots=True)
class WalkForwardOOSComponent:
    subject_ref: str
    availability: EvidenceAvailability
    outcome: WalkForwardOutcome | None
    fold_evidence: tuple[FoldEvidence, ...]
    declared_fold_count: int
    validated_fold_count: int
    passed_fold_count: int
    pass_rate: float | None
    split_policy_ref: str
    purge_policy_ref: str
    embargo_policy_ref: str
    overlap_applicability: str
    leakage_unit: str
    purge_applied: int
    embargo_applied: int
    input_hash: str
    config_hash: str
    component_ref: str
    component_hash: str
    reason_codes: tuple[str, ...]
    provenance: Mapping[str, Any]
    limitations: tuple[str, ...]
    schema_version: str = WALK_FORWARD_OOS_COMPONENT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["availability"] = self.availability.value
        data["outcome"] = self.outcome.value if self.outcome is not None else None
        return canonical_json_value(data)

    def unsigned_dict(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("component_ref", None)
        data.pop("component_hash", None)
        return data


@dataclass(frozen=True, slots=True)
class WalkForwardComponentValidation:
    availability: EvidenceAvailability
    issues: tuple[WalkForwardValidationIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT

    @property
    def structurally_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True, slots=True)
class WalkForwardOOSResult:
    validation: WalkForwardInputValidation
    component: WalkForwardOOSComponent
    descriptor: ComponentDescriptor
    envelope: StrategyEvidenceEnvelope


@dataclass(frozen=True, slots=True)
class EventWalkForwardApplicability:
    availability: EvidenceAvailability
    reason_code: str
    owner: str
    revisit_trigger: str
    producer_count: int = 0
    fixture_count: int = 0
    feed_access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["availability"] = self.availability.value
        return canonical_json_value(data)


def fold_membership_hash(fold_ids: Sequence[str]) -> str:
    return canonical_hash(tuple(fold_ids), domain=FOLD_MEMBERSHIP_HASH_DOMAIN)


def validate_walk_forward_oos_input(value: WalkForwardEvidenceInput) -> WalkForwardInputValidation:
    blocked: list[WalkForwardValidationIssue] = []
    unavailable: list[WalkForwardValidationIssue] = []

    _validate_authorization(value.authorization, blocked, unavailable)
    if value.schema_version != WALK_FORWARD_OOS_INPUT_SCHEMA_VERSION:
        blocked.append(_blocked("input_schema_unsupported", "schema_version", "Unsupported C2 input schema."))
    if not value.subject_ref.strip():
        unavailable.append(_unavailable("subject_ref_missing", "subject_ref", "Subject ref is required."))

    manifest = value.manifest
    if manifest is None:
        unavailable.append(_unavailable("fold_manifest_missing", "manifest", "Fold manifest is required."))
    else:
        _validate_manifest(manifest, value.folds, blocked, unavailable)

    split = value.split_policy
    if split is None:
        unavailable.append(_unavailable("split_policy_missing", "split_policy", "Split policy is required."))
    else:
        for field_name in ("policy_id", "strategy_kind", "mode", "window_unit", "policy_ref", "schema_version"):
            if not str(getattr(split, field_name) or "").strip():
                unavailable.append(_unavailable(f"split_{field_name}_missing", f"split_policy.{field_name}", f"{field_name} is required."))

    _validate_temporal_folds(value.folds, blocked, unavailable)
    _validate_leakage(value.leakage_policy, blocked, unavailable)
    _validate_metrics(value, blocked, unavailable)
    _validate_lineage(value.lineage, manifest, blocked, unavailable)

    issues = tuple(sorted((*blocked, *unavailable), key=_issue_sort_key))
    if blocked:
        return WalkForwardInputValidation(WalkForwardInputStatus.BLOCKED, value, issues)
    if unavailable:
        return WalkForwardInputValidation(WalkForwardInputStatus.TYPED_UNAVAILABLE, value, issues)
    return WalkForwardInputValidation(WalkForwardInputStatus.VALIDATED, value)


def adapt_daily_walk_forward_input(
    manifest: Any,
    *,
    subject_ref: str,
    temporal_folds: Sequence[TemporalFold | Mapping[str, Any]],
    metric_policies: Sequence[MetricPolicy | Mapping[str, Any]],
    fold_metrics: Sequence[FoldMetricValue | Mapping[str, Any]],
    lineage: LineageBinding | Mapping[str, Any] | None,
    authorization: AuthorizationMetadata | Mapping[str, Any] | None,
    split_policy: SplitPolicy | Mapping[str, Any] | None,
    leakage_policy: PurgeEmbargoPolicy | Mapping[str, Any] | None,
) -> WalkForwardInputValidation:
    data = _as_mapping(manifest)
    folds = tuple(_coerce(TemporalFold, item) for item in temporal_folds)
    ids = tuple(item.fold_id for item in folds)
    manifest_ids = tuple(str(_as_mapping(item).get("fold_id") or "") for item in data.get("folds", ())) or ids
    common_manifest = FoldManifest(
        manifest_id=str(data.get("manifest_ref") or "daily-walk-forward-manifest"),
        manifest_ref=str(data.get("manifest_ref") or ""),
        manifest_hash=canonical_hash(data, domain="quant-lab.walk-forward-oos.daily-manifest.v1") if data else "",
        declared_fold_count=len(manifest_ids),
        ordered_fold_ids=manifest_ids,
        membership_hash=fold_membership_hash(manifest_ids) if manifest_ids else "",
    )
    value = WalkForwardEvidenceInput(
        subject_ref=subject_ref,
        manifest=common_manifest,
        split_policy=_coerce_optional(SplitPolicy, split_policy),
        folds=folds,
        leakage_policy=_coerce_optional(PurgeEmbargoPolicy, leakage_policy),
        metric_policies=tuple(_coerce(MetricPolicy, item) for item in metric_policies),
        fold_metrics=tuple(_coerce(FoldMetricValue, item) for item in fold_metrics),
        lineage=_coerce_optional(LineageBinding, lineage),
        authorization=_coerce_optional(AuthorizationMetadata, authorization),
    )
    return validate_walk_forward_oos_input(value)


def adapt_ml_walk_forward_input(
    policy: Any,
    *,
    subject_ref: str,
    test_is_oos: bool,
    metric_policies: Sequence[MetricPolicy | Mapping[str, Any]],
    fold_metrics: Sequence[FoldMetricValue | Mapping[str, Any]],
    lineage: LineageBinding | Mapping[str, Any] | None,
    authorization: AuthorizationMetadata | Mapping[str, Any] | None,
) -> WalkForwardInputValidation:
    data = _as_mapping(policy)
    source_folds = tuple(_as_mapping(item) for item in data.get("folds", ()))
    folds = tuple(
        TemporalFold(
            fold_id=str(item.get("fold_id") or ""),
            train_start=str(item.get("train_start") or ""),
            train_end=str(item.get("train_end") or ""),
            validation_start=str(item.get("validation_start") or ""),
            validation_end=str(item.get("validation_end") or ""),
            oos_start=str(item.get("test_start") or "") if test_is_oos else "",
            oos_end=str(item.get("test_end") or "") if test_is_oos else "",
        )
        for item in source_folds
    )
    ids = tuple(item.fold_id for item in folds)
    policy_id = str(data.get("policy_id") or "")
    manifest = FoldManifest(
        manifest_id=policy_id,
        manifest_ref=f"logical://ml-cv/{policy_id}" if policy_id else "",
        manifest_hash=canonical_hash(data, domain="quant-lab.walk-forward-oos.ml-policy.v1") if data else "",
        declared_fold_count=len(ids),
        ordered_fold_ids=ids,
        membership_hash=fold_membership_hash(ids) if ids else "",
    )
    value = WalkForwardEvidenceInput(
        subject_ref=subject_ref,
        manifest=manifest,
        split_policy=SplitPolicy(
            policy_id=policy_id,
            strategy_kind="ml",
            mode="purged-embargo-walk-forward",
            window_unit="days",
            policy_ref=f"logical://ml-cv/{policy_id}" if policy_id else "",
            schema_version=str(data.get("schema_version") or ""),
        ),
        folds=folds,
        leakage_policy=PurgeEmbargoPolicy(
            overlap_applicability="overlapping-label-window",
            unit="days",
            label_or_window_horizon=_strict_int(data.get("label_horizon_days")),
            purge_required=_strict_int(data.get("label_horizon_days")),
            purge_applied=_strict_int(data.get("purge_window_days")),
            embargo_required=_strict_int(data.get("label_horizon_days")),
            embargo_applied=_strict_int(data.get("embargo_days")),
            purge_policy_ref=f"logical://ml-cv/{policy_id}/purge" if policy_id else "",
            embargo_policy_ref=f"logical://ml-cv/{policy_id}/embargo" if policy_id else "",
        ),
        metric_policies=tuple(_coerce(MetricPolicy, item) for item in metric_policies),
        fold_metrics=tuple(_coerce(FoldMetricValue, item) for item in fold_metrics),
        lineage=_coerce_optional(LineageBinding, lineage),
        authorization=_coerce_optional(AuthorizationMetadata, authorization),
    )
    return validate_walk_forward_oos_input(value)


def event_walk_forward_applicability(event_time_semantics: Any) -> EventWalkForwardApplicability:
    _ = _as_mapping(event_time_semantics)
    return EventWalkForwardApplicability(
        availability=EvidenceAvailability.NOT_APPLICABLE_WITH_REASON,
        reason_code="event_fold_semantics_unfrozen",
        owner="future-event-walk-forward-CR",
        revisit_trigger="freeze_event_window_available_at_and_reference_fixture",
    )


def produce_walk_forward_oos_evidence(validation: WalkForwardInputValidation) -> WalkForwardOOSResult:
    value = validation.evidence_input
    if validation.status is not WalkForwardInputStatus.VALIDATED:
        availability = (
            EvidenceAvailability.BLOCKED
            if validation.status is WalkForwardInputStatus.BLOCKED
            else EvidenceAvailability.TYPED_UNAVAILABLE
        )
        reasons = tuple(sorted({item.code for item in validation.issues}))
        component = _non_present_component(value, availability, reasons)
        return _assemble_result(validation, component)

    policy_by_id = {item.metric_id: item for item in value.metric_policies if item.mandatory}
    metric_by_fold = {(item.fold_id, item.metric_id): item.value for item in value.fold_metrics}
    fold_evidence: list[FoldEvidence] = []
    for fold in value.folds:
        decisions = tuple(
            MetricDecision(
                metric_id=metric_id,
                value=metric_by_fold[(fold.fold_id, metric_id)],
                direction=policy.direction,
                threshold=policy.threshold,
                passed=_metric_pass(metric_by_fold[(fold.fold_id, metric_id)], policy.direction, policy.threshold),
            )
            for metric_id, policy in sorted(policy_by_id.items())
        )
        passed = all(item.passed for item in decisions)
        fold_evidence.append(
            FoldEvidence(
                fold_id=fold.fold_id,
                metric_decisions=decisions,
                outcome=WalkForwardOutcome.PASS if passed else WalkForwardOutcome.FAIL,
                reason_codes=() if passed else tuple(f"metric_failed:{item.metric_id}" for item in decisions if not item.passed),
            )
        )
    declared = value.manifest.declared_fold_count if value.manifest is not None else 0
    passed_count = sum(item.outcome is WalkForwardOutcome.PASS for item in fold_evidence)
    pass_rate = passed_count / declared
    if passed_count == declared:
        outcome = WalkForwardOutcome.PASS
    elif passed_count == 0:
        outcome = WalkForwardOutcome.FAIL
    else:
        outcome = WalkForwardOutcome.NEEDS_REVIEW
    input_hash = canonical_hash(value.to_dict(), domain=INPUT_HASH_DOMAIN)
    config_hash = canonical_hash(_config_payload(value), domain=CONFIG_HASH_DOMAIN)
    split = value.split_policy
    leakage = value.leakage_policy
    unsigned = {
        "schema_version": WALK_FORWARD_OOS_COMPONENT_SCHEMA_VERSION,
        "subject_ref": value.subject_ref,
        "availability": EvidenceAvailability.PRESENT.value,
        "outcome": outcome.value,
        "fold_evidence": [item.to_dict() for item in fold_evidence],
        "declared_fold_count": declared,
        "validated_fold_count": len(fold_evidence),
        "passed_fold_count": passed_count,
        "pass_rate": pass_rate,
        "split_policy_ref": split.policy_ref if split else "",
        "purge_policy_ref": leakage.purge_policy_ref if leakage else "",
        "embargo_policy_ref": leakage.embargo_policy_ref if leakage else "",
        "overlap_applicability": leakage.overlap_applicability if leakage else "",
        "leakage_unit": leakage.unit if leakage else "",
        "purge_applied": leakage.purge_applied if leakage else 0,
        "embargo_applied": leakage.embargo_applied if leakage else 0,
        "input_hash": input_hash,
        "config_hash": config_hash,
        "reason_codes": [],
        "provenance": _provenance(value),
        "limitations": ["fixture_static_only", "not_real_oos_evidence", "not_runtime_authorization"],
    }
    component_hash = canonical_hash(unsigned, domain=COMPONENT_HASH_DOMAIN)
    component = WalkForwardOOSComponent(
        subject_ref=value.subject_ref,
        availability=EvidenceAvailability.PRESENT,
        outcome=outcome,
        fold_evidence=tuple(fold_evidence),
        declared_fold_count=declared,
        validated_fold_count=len(fold_evidence),
        passed_fold_count=passed_count,
        pass_rate=pass_rate,
        split_policy_ref=unsigned["split_policy_ref"],
        purge_policy_ref=unsigned["purge_policy_ref"],
        embargo_policy_ref=unsigned["embargo_policy_ref"],
        overlap_applicability=unsigned["overlap_applicability"],
        leakage_unit=unsigned["leakage_unit"],
        purge_applied=unsigned["purge_applied"],
        embargo_applied=unsigned["embargo_applied"],
        input_hash=input_hash,
        config_hash=config_hash,
        component_ref=f"evidence://walk-forward-oos/v1/{component_hash.removeprefix('sha256:')}",
        component_hash=component_hash,
        reason_codes=(),
        provenance=unsigned["provenance"],
        limitations=tuple(unsigned["limitations"]),
    )
    self_validation = validate_walk_forward_oos_component(component)
    if not self_validation.passed:
        reasons = tuple(sorted({item.code for item in self_validation.issues}))
        component = _non_present_component(value, EvidenceAvailability.BLOCKED, reasons)
    return _assemble_result(validation, component)


def validate_walk_forward_oos_component(component: WalkForwardOOSComponent) -> WalkForwardComponentValidation:
    issues: list[WalkForwardValidationIssue] = []
    if component.availability is not EvidenceAvailability.PRESENT:
        if component.outcome is not None or component.fold_evidence or component.pass_rate is not None:
            issues.append(_blocked("non_present_component_has_computed_result", "availability", "Non-present component cannot carry computed outcomes."))
        if component.component_ref or component.component_hash:
            issues.append(_blocked("non_present_component_has_identity", "component_ref", "Non-present component cannot carry a positive evidence identity."))
        if not component.reason_codes:
            issues.append(_blocked("non_present_reason_missing", "reason_codes", "Non-present component requires a reason code."))
        return WalkForwardComponentValidation(EvidenceAvailability.BLOCKED if issues else component.availability, tuple(issues))
    if component.schema_version != WALK_FORWARD_OOS_COMPONENT_SCHEMA_VERSION:
        issues.append(_blocked("component_schema_unsupported", "schema_version", "Unsupported component schema."))
    if component.declared_fold_count != len(component.fold_evidence) or component.validated_fold_count != len(component.fold_evidence):
        issues.append(_blocked("component_fold_count_mismatch", "declared_fold_count", "Component fold counts do not match evidence."))
    passed = sum(item.outcome is WalkForwardOutcome.PASS for item in component.fold_evidence)
    if passed != component.passed_fold_count:
        issues.append(_blocked("component_pass_count_mismatch", "passed_fold_count", "Component pass count mismatch."))
    expected_rate = passed / component.declared_fold_count if component.declared_fold_count else None
    if expected_rate != component.pass_rate:
        issues.append(_blocked("component_pass_rate_mismatch", "pass_rate", "Component pass rate mismatch."))
    for fold in component.fold_evidence:
        for metric in fold.metric_decisions:
            if not _finite(metric.value) or not _finite(metric.threshold) or metric.direction not in {"gte", "lte", "gt", "lt"}:
                issues.append(_blocked("metric_decision_invalid", "fold_evidence.metric_decisions", "Metric decision is not finite or uses an unsupported direction.", fold.fold_id))
                continue
            if metric.passed is not _metric_pass(metric.value, metric.direction, metric.threshold):
                issues.append(_blocked("metric_decision_mismatch", "fold_evidence.metric_decisions.passed", "Metric decision was not derived from its value and policy.", fold.fold_id))
        expected_outcome = WalkForwardOutcome.PASS if all(item.passed for item in fold.metric_decisions) else WalkForwardOutcome.FAIL
        if fold.outcome is not expected_outcome:
            issues.append(_blocked("fold_outcome_mismatch", "fold_evidence.outcome", "Fold outcome was not derived from metric decisions.", fold.fold_id))
    expected_outcome = (
        WalkForwardOutcome.PASS
        if passed == component.declared_fold_count
        else WalkForwardOutcome.FAIL
        if passed == 0
        else WalkForwardOutcome.NEEDS_REVIEW
    )
    if component.outcome is not expected_outcome:
        issues.append(_blocked("component_outcome_mismatch", "outcome", "Component outcome was not derived from declared fold results."))
    expected_hash = canonical_hash(component.unsigned_dict(), domain=COMPONENT_HASH_DOMAIN)
    expected_ref = f"evidence://walk-forward-oos/v1/{expected_hash.removeprefix('sha256:')}"
    if component.component_hash != expected_hash:
        issues.append(_blocked("component_hash_mismatch", "component_hash", "Component hash mismatch."))
    if component.component_ref != expected_ref:
        issues.append(_blocked("component_ref_mismatch", "component_ref", "Component ref does not match its hash."))
    return WalkForwardComponentValidation(EvidenceAvailability.BLOCKED if issues else EvidenceAvailability.PRESENT, tuple(issues))


def _assemble_result(validation: WalkForwardInputValidation, component: WalkForwardOOSComponent) -> WalkForwardOOSResult:
    descriptor = ComponentDescriptor(
        component_type="walk_forward_oos",
        component_schema_version=WALK_FORWARD_OOS_COMPONENT_CATALOG_VERSION,
        required=True,
        component_ref=component.component_ref,
        component_hash=component.component_hash,
        availability=component.availability,
        reason_codes=component.reason_codes,
    )
    authorization = validation.evidence_input.authorization
    envelope = build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref=validation.evidence_input.subject_ref,
        components=(descriptor,),
        logical_provenance=component.provenance,
        authorization_summary=authorization.to_dict() if authorization else {},
        limitations=component.limitations,
        reason_codes=component.reason_codes,
    )
    return WalkForwardOOSResult(validation=validation, component=component, descriptor=descriptor, envelope=envelope)


def _non_present_component(
    value: WalkForwardEvidenceInput,
    availability: EvidenceAvailability,
    reasons: Sequence[str],
) -> WalkForwardOOSComponent:
    split = value.split_policy
    leakage = value.leakage_policy
    return WalkForwardOOSComponent(
        subject_ref=value.subject_ref,
        availability=availability,
        outcome=None,
        fold_evidence=(),
        declared_fold_count=value.manifest.declared_fold_count if value.manifest else 0,
        validated_fold_count=0,
        passed_fold_count=0,
        pass_rate=None,
        split_policy_ref=split.policy_ref if split else "",
        purge_policy_ref=leakage.purge_policy_ref if leakage else "",
        embargo_policy_ref=leakage.embargo_policy_ref if leakage else "",
        overlap_applicability=leakage.overlap_applicability if leakage else "",
        leakage_unit=leakage.unit if leakage else "",
        purge_applied=leakage.purge_applied if leakage else 0,
        embargo_applied=leakage.embargo_applied if leakage else 0,
        input_hash="",
        config_hash="",
        component_ref="",
        component_hash="",
        reason_codes=tuple(sorted(set(reasons))),
        provenance=_provenance(value),
        limitations=("fixture_static_only", "not_real_oos_evidence", "not_runtime_authorization"),
    )


def _validate_authorization(
    authorization: AuthorizationMetadata | None,
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    if authorization is None:
        unavailable.append(_unavailable("authorization_metadata_missing", "authorization", "Authorization metadata is required."))
        return
    if authorization.validation_mode not in ALLOWED_VALIDATION_MODES:
        blocked.append(_blocked("validation_mode_unauthorized", "authorization.validation_mode", "Only fixture/static validation mode is authorized."))
    if authorization.ref_class not in ALLOWED_STATIC_REF_CLASSES:
        blocked.append(_blocked("real_or_external_ref_unauthorized", "authorization.ref_class", "Real/external refs are not authorized and were not dereferenced."))
    for name, count in authorization.operation_counts.items():
        if not isinstance(count, int) or isinstance(count, bool) or count != 0:
            blocked.append(_blocked("forbidden_operation_nonzero", f"authorization.operation_counts.{name}", "Forbidden operation counters must remain zero."))


def _validate_manifest(
    manifest: FoldManifest,
    folds: Sequence[TemporalFold],
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    for field_name in ("manifest_id", "manifest_ref", "manifest_hash", "membership_hash"):
        if not str(getattr(manifest, field_name) or "").strip():
            unavailable.append(_unavailable(f"{field_name}_missing", f"manifest.{field_name}", f"{field_name} is required."))
    if manifest.declared_fold_count <= 0 or not manifest.ordered_fold_ids:
        unavailable.append(_unavailable("fold_inventory_missing", "manifest.ordered_fold_ids", "A positive declared fold inventory is required."))
        return
    if len(set(manifest.ordered_fold_ids)) != len(manifest.ordered_fold_ids):
        blocked.append(_blocked("fold_id_duplicate", "manifest.ordered_fold_ids", "Fold ids must be unique."))
    if manifest.declared_fold_count != len(manifest.ordered_fold_ids):
        blocked.append(_blocked("declared_fold_count_mismatch", "manifest.declared_fold_count", "Declared count must equal manifest ids."))
    observed = tuple(item.fold_id for item in folds)
    if observed != manifest.ordered_fold_ids:
        blocked.append(_blocked("fold_inventory_mismatch", "folds", "Observed fold ids must exactly match declared order."))
    if manifest.membership_hash and manifest.membership_hash != fold_membership_hash(manifest.ordered_fold_ids):
        blocked.append(_blocked("fold_membership_hash_mismatch", "manifest.membership_hash", "Fold membership hash mismatch."))


def _validate_temporal_folds(
    folds: Sequence[TemporalFold],
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    if not folds:
        unavailable.append(_unavailable("temporal_folds_missing", "folds", "Temporal folds are required."))
        return
    previous_oos_start: datetime | None = None
    for fold in folds:
        if not fold.fold_id.strip():
            unavailable.append(_unavailable("fold_id_missing", "folds.fold_id", "Fold id is required."))
        values: list[datetime] = []
        missing = False
        for field_name in ("train_start", "train_end", "validation_start", "validation_end", "oos_start", "oos_end"):
            raw = getattr(fold, field_name)
            if not str(raw).strip():
                unavailable.append(_unavailable(f"{field_name}_missing", f"folds.{field_name}", f"{field_name} is required.", fold.fold_id))
                missing = True
                continue
            try:
                values.append(_parse_time(raw))
            except ValueError:
                blocked.append(_blocked("temporal_value_invalid", f"folds.{field_name}", "Timestamp must be ISO-8601.", fold.fold_id))
                missing = True
        if missing or len(values) != 6:
            continue
        # Boundary equality is allowed only between train/validation and validation/OOS.
        train_start, train_end, validation_start, validation_end, oos_start, oos_end = values
        valid = train_start < train_end <= validation_start < validation_end <= oos_start < oos_end
        if not valid:
            blocked.append(_blocked("temporal_order_invalid", "folds", "Fold must follow half-open train/validation/OOS order.", fold.fold_id))
        if previous_oos_start is not None and values[4] <= previous_oos_start:
            blocked.append(_blocked("oos_cutoff_not_monotonic", "folds.oos_start", "OOS cutoffs must be strictly increasing.", fold.fold_id))
        previous_oos_start = values[4]


def _validate_leakage(
    policy: PurgeEmbargoPolicy | None,
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    if policy is None:
        unavailable.append(_unavailable("purge_embargo_policy_missing", "leakage_policy", "Purge/embargo policy is required."))
        return
    if policy.overlap_applicability not in {"overlapping-label-window", "overlapping-event-window", "non-overlapping-deterministic"}:
        blocked.append(_blocked("overlap_applicability_invalid", "leakage_policy.overlap_applicability", "Overlap applicability must be explicit."))
    if not policy.unit.strip():
        unavailable.append(_unavailable("purge_embargo_unit_missing", "leakage_policy.unit", "Purge/embargo unit is required."))
    for field_name in ("label_or_window_horizon", "purge_required", "purge_applied", "embargo_required", "embargo_applied"):
        value = getattr(policy, field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            blocked.append(_blocked(f"{field_name}_invalid", f"leakage_policy.{field_name}", f"{field_name} must be a non-negative integer."))
    if policy.overlap_applicability.startswith("overlapping") and not policy.purge_policy_ref:
        unavailable.append(_unavailable("purge_policy_ref_missing", "leakage_policy.purge_policy_ref", "Overlapping windows require purge evidence."))
    if not policy.embargo_policy_ref:
        unavailable.append(_unavailable("embargo_policy_ref_missing", "leakage_policy.embargo_policy_ref", "Embargo evidence is required."))
    if policy.purge_applied < policy.purge_required:
        blocked.append(_blocked("purge_insufficient", "leakage_policy.purge_applied", "Applied purge is below the required minimum."))
    if policy.embargo_applied < policy.embargo_required:
        blocked.append(_blocked("embargo_insufficient", "leakage_policy.embargo_applied", "Applied embargo is below the required minimum."))


def _validate_metrics(
    value: WalkForwardEvidenceInput,
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    if not value.metric_policies:
        unavailable.append(_unavailable("metric_policy_missing", "metric_policies", "At least one metric policy is required."))
        return
    by_policy: dict[str, MetricPolicy] = {}
    for policy in value.metric_policies:
        if not policy.metric_id.strip():
            unavailable.append(_unavailable("metric_id_missing", "metric_policies.metric_id", "Metric id is required."))
            continue
        if policy.metric_id in by_policy:
            blocked.append(_blocked("metric_policy_duplicate", "metric_policies.metric_id", "Metric policy ids must be unique."))
        by_policy[policy.metric_id] = policy
        if policy.direction not in {"gte", "lte", "gt", "lt"}:
            blocked.append(_blocked("metric_direction_invalid", "metric_policies.direction", "Metric direction is unsupported."))
        if not _finite(policy.threshold):
            blocked.append(_blocked("metric_threshold_non_finite", "metric_policies.threshold", "Metric threshold must be finite."))
    metric_values: dict[tuple[str, str], FoldMetricValue] = {}
    for metric in value.fold_metrics:
        key = (metric.fold_id, metric.metric_id)
        if key in metric_values:
            blocked.append(_blocked("fold_metric_duplicate", "fold_metrics", "Fold metric identity must be unique.", metric.fold_id))
        metric_values[key] = metric
        if not _finite(metric.value):
            blocked.append(_blocked("fold_metric_non_finite", "fold_metrics.value", "Fold metric must be finite.", metric.fold_id))
    for fold in value.folds:
        for metric_id, policy in by_policy.items():
            if policy.mandatory and (fold.fold_id, metric_id) not in metric_values:
                unavailable.append(_unavailable("mandatory_fold_metric_missing", "fold_metrics", f"Mandatory metric {metric_id} is missing.", fold.fold_id))


def _validate_lineage(
    lineage: LineageBinding | None,
    manifest: FoldManifest | None,
    blocked: list[WalkForwardValidationIssue],
    unavailable: list[WalkForwardValidationIssue],
) -> None:
    if lineage is None:
        unavailable.append(_unavailable("lineage_missing", "lineage", "Lineage binding is required."))
        return
    for field_name in ("lineage_ref", "lineage_hash", "fold_membership_hash"):
        if not str(getattr(lineage, field_name) or "").strip():
            unavailable.append(_unavailable(f"{field_name}_missing", f"lineage.{field_name}", f"{field_name} is required."))
    if not lineage.source_refs or not lineage.source_hashes:
        unavailable.append(_unavailable("lineage_sources_missing", "lineage.source_refs", "Lineage source refs and hashes are required."))
    elif len(lineage.source_refs) != len(lineage.source_hashes):
        blocked.append(_blocked("lineage_source_binding_mismatch", "lineage.source_hashes", "Lineage refs and hashes must be paired."))
    if manifest is not None and lineage.fold_membership_hash and lineage.fold_membership_hash != manifest.membership_hash:
        blocked.append(_blocked("lineage_membership_mismatch", "lineage.fold_membership_hash", "Lineage fold membership does not match manifest."))


def _config_payload(value: WalkForwardEvidenceInput) -> dict[str, Any]:
    return {
        "split_policy": value.split_policy.to_dict() if value.split_policy else None,
        "leakage_policy": value.leakage_policy.to_dict() if value.leakage_policy else None,
        "metric_policies": [item.to_dict() for item in value.metric_policies],
    }


def _provenance(value: WalkForwardEvidenceInput) -> dict[str, Any]:
    return canonical_json_value(
        {
            "producer_version": WALK_FORWARD_OOS_PRODUCER_VERSION,
            "validation_mode": value.authorization.validation_mode if value.authorization else "",
            "lineage_ref": value.lineage.lineage_ref if value.lineage else "",
            "lineage_hash": value.lineage.lineage_hash if value.lineage else "",
            "manifest_ref": value.manifest.manifest_ref if value.manifest else "",
            "manifest_hash": value.manifest.manifest_hash if value.manifest else "",
        }
    )


def _metric_pass(value: float, direction: str, threshold: float) -> bool:
    return {
        "gte": value >= threshold,
        "lte": value <= threshold,
        "gt": value > threshold,
        "lt": value < threshold,
    }[direction]


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    to_dict = getattr(value, "to_dict", None)
    return dict(to_dict()) if callable(to_dict) else {}


def _coerce(cls: Any, value: Any) -> Any:
    return value if isinstance(value, cls) else cls(**_as_mapping(value))


def _coerce_optional(cls: Any, value: Any) -> Any:
    return None if value is None else _coerce(cls, value)


def _strict_int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else -1


def _blocked(code: str, field: str, message: str, fold_id: str = "") -> WalkForwardValidationIssue:
    return WalkForwardValidationIssue(code, field, message, "blocked", fold_id)


def _unavailable(code: str, field: str, message: str, fold_id: str = "") -> WalkForwardValidationIssue:
    return WalkForwardValidationIssue(code, field, message, "typed_unavailable", fold_id)


def _issue_sort_key(issue: WalkForwardValidationIssue) -> tuple[int, str, str, str]:
    return (0 if issue.severity == "blocked" else 1, issue.fold_id, issue.field, issue.code)


__all__ = [
    "AuthorizationMetadata",
    "EventWalkForwardApplicability",
    "FoldEvidence",
    "FoldManifest",
    "FoldMetricValue",
    "LineageBinding",
    "MetricDecision",
    "MetricPolicy",
    "PurgeEmbargoPolicy",
    "SplitPolicy",
    "TemporalFold",
    "WalkForwardComponentValidation",
    "WalkForwardEvidenceInput",
    "WalkForwardInputStatus",
    "WalkForwardInputValidation",
    "WalkForwardOOSComponent",
    "WalkForwardOOSResult",
    "WalkForwardOutcome",
    "adapt_daily_walk_forward_input",
    "adapt_ml_walk_forward_input",
    "event_walk_forward_applicability",
    "fold_membership_hash",
    "produce_walk_forward_oos_evidence",
    "validate_walk_forward_oos_component",
    "validate_walk_forward_oos_input",
]
