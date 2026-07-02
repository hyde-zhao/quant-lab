"""CR153 metadata-only event strategy companion contracts.

This module validates passed-in event study metadata only. It does not read
event feeds, files, credentials, lake/NAS/provider data, runtime adapters,
brokers, event stores, catalogs, registries, Git remotes, or real returns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.research_production_contracts import CR153_EVENT_FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import as_mapping, json_safe, safe_float


EVENT_STUDY_METHOD_SPEC_SCHEMA = "event_study_method_spec_v1"
EVENT_STUDY_TEST_REPORT_SCHEMA = "event_study_test_report_v1"
EVENT_STUDY_STATUS_PASS = "PASS"
EVENT_STUDY_STATUS_FAIL = "FAIL"
EVENT_STUDY_STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
EVENT_STUDY_STATUS_BLOCKED = "BLOCKED"
EVENT_AUDIT_SLOT_STATUS_PRESENT = "present"
EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE = "not_applicable"
EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154 = "deferred_cr154"
EVENT_AUDIT_SLOT_STATUS_NEEDS_REVIEW = "needs_review"
EVENT_AUDIT_SLOT_STATUS_BLOCKED = "blocked"

EVENT_STUDY_REQUIRED_TEST_FAMILIES = (
    "patell",
    "bmp",
    "generalized_sign",
    "rank",
    "bootstrap",
)
EVENT_STUDY_DEFERRED_ALGORITHMS = (
    "white_reality_check",
    "hansen_spa",
    "romano_wolf",
    "pbo",
    "dsr",
)
EVENT_STUDY_FORBIDDEN_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            *CR153_EVENT_FORBIDDEN_OPERATION_COUNTERS,
            "real_data_validation",
            "external_framework_run",
            "git_remote_write",
            "real_order_flow",
        )
    )
)
EVENT_AUDIT_ALLOWED_SLOT_STATUSES = (
    EVENT_AUDIT_SLOT_STATUS_PRESENT,
    EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE,
    EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154,
    EVENT_AUDIT_SLOT_STATUS_NEEDS_REVIEW,
    EVENT_AUDIT_SLOT_STATUS_BLOCKED,
)
EVENT_RELIABILITY_REQUIRED_DEFERRED_AREAS = (
    "capacity",
    "impact",
    "regime",
    "reconciliation",
)
EVENT_BIAS_AUDIT_SUMMARY_SCHEMA = "event_bias_risk_audit_summary_v1"


class EventStudyStatus(str, Enum):
    PASS = EVENT_STUDY_STATUS_PASS
    FAIL = EVENT_STUDY_STATUS_FAIL
    NEEDS_REVIEW = EVENT_STUDY_STATUS_NEEDS_REVIEW
    BLOCKED = EVENT_STUDY_STATUS_BLOCKED


class EventAuditSlotStatus(str, Enum):
    PRESENT = EVENT_AUDIT_SLOT_STATUS_PRESENT
    NOT_APPLICABLE = EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE
    DEFERRED_CR154 = EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154
    NEEDS_REVIEW = EVENT_AUDIT_SLOT_STATUS_NEEDS_REVIEW
    BLOCKED = EVENT_AUDIT_SLOT_STATUS_BLOCKED


@dataclass(frozen=True, slots=True)
class EventStudyValidationIssue:
    code: str
    severity: str
    message: str
    field: str = ""
    evidence_ref: str = ""
    status: str = EVENT_STUDY_STATUS_BLOCKED

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventEvidenceRef:
    ref_id: str
    kind: str
    path_or_id: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventStudyWindowSpec:
    window_id: str
    relative_start: int | None = None
    relative_end: int | None = None
    calendar_start: str = ""
    calendar_end: str = ""
    anchor: str = "event_available_at_or_decision_time"
    trading_calendar_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class NormalReturnModelSpec:
    model_id: str
    model_type: str
    status: EventStudyStatus | str = EventStudyStatus.PASS
    market_benchmark_ref: str = ""
    factor_model_ref: str = ""
    estimation_method: str = ""
    n_a_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventStudyMethodSlot:
    method_name: str
    status: EventStudyStatus | str
    support_level: str = "slot_only"
    report_ref: str = ""
    n_a_reason: str = ""
    implementation_state: str = "slot_only"
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = dict(json_safe(asdict(self)))
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True, slots=True)
class EventStudyMethodSpec:
    method_id: str
    event_research_spec_id: str
    estimation_window: EventStudyWindowSpec | Mapping[str, Any] | None
    event_window: EventStudyWindowSpec | Mapping[str, Any] | None
    normal_return_model: NormalReturnModelSpec | Mapping[str, Any] | None
    return_horizon: str | int | Mapping[str, Any]
    car_method_slot: EventStudyMethodSlot | Mapping[str, Any] | None
    bhar_method_slot: EventStudyMethodSlot | Mapping[str, Any] | None
    calendar_time_method_slot: EventStudyMethodSlot | Mapping[str, Any] | None
    method_ref: str = ""
    n_a_reason: str = ""
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = EVENT_STUDY_METHOD_SPEC_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "method_id": self.method_id,
            "event_research_spec_id": self.event_research_spec_id,
            "estimation_window": _json_mapping(self.estimation_window),
            "event_window": _json_mapping(self.event_window),
            "normal_return_model": _json_mapping(self.normal_return_model),
            "return_horizon": json_safe(self.return_horizon),
            "car_method_slot": _json_mapping(self.car_method_slot),
            "bhar_method_slot": _json_mapping(self.bhar_method_slot),
            "calendar_time_method_slot": _json_mapping(self.calendar_time_method_slot),
            "method_ref": self.method_ref,
            "n_a_reason": self.n_a_reason,
            "operation_counts": normalise_event_study_operation_counts(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class EventStudyTestFamilySlot:
    family_id: str
    status: EventStudyStatus | str
    sample_count: int
    raw_p_value: float | None = None
    adjusted_p_value: float | None = None
    report_ref: str = ""
    n_a_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventStudyMultipleTestingSlot:
    family_id: str
    tested_window_count: int
    correction_method: str
    adjusted_p_value: float | None
    status: EventStudyStatus | str
    report_ref: str = ""
    n_a_reason: str = ""
    implementation_state: str = "slot_only"

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventStudyTestReport:
    report_id: str
    method_id: str
    test_family_slots: tuple[EventStudyTestFamilySlot | Mapping[str, Any], ...]
    multiple_testing_or_data_snooping_slot: EventStudyMultipleTestingSlot | Mapping[str, Any] | None
    sample_count: int
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = EVENT_STUDY_TEST_REPORT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "method_id": self.method_id,
            "test_family_slots": [_json_mapping(slot) for slot in self.test_family_slots],
            "multiple_testing_or_data_snooping_slot": _json_mapping(self.multiple_testing_or_data_snooping_slot),
            "sample_count": self.sample_count,
            "operation_counts": normalise_event_study_operation_counts(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class EventBiasAuditSlot:
    slot_name: str
    status: EventAuditSlotStatus | str
    evidence_refs: tuple[EventEvidenceRef | Mapping[str, Any] | str, ...] = ()
    n_a_reason: str = ""
    deferred_to: str = ""
    deferred_reason: str = ""
    limitations: tuple[str, ...] = ()
    cluster_dimensions: tuple[str, ...] = ()
    treatment_family: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "slot_name": self.slot_name,
            "status": _status_value(self.status),
            "evidence_refs": [_json_mapping(ref) for ref in self.evidence_refs],
            "n_a_reason": self.n_a_reason,
            "deferred_to": self.deferred_to,
            "deferred_reason": self.deferred_reason,
            "limitations": list(self.limitations),
            "cluster_dimensions": list(self.cluster_dimensions),
            "treatment_family": self.treatment_family,
        }


@dataclass(frozen=True, slots=True)
class EventCVSplitAuditRefs:
    status: EventAuditSlotStatus | str
    split_audit_refs: tuple[EventEvidenceRef | Mapping[str, Any] | str, ...] = ()
    n_a_reason: str = ""
    deferred_to: str = ""
    deferred_reason: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": _status_value(self.status),
            "split_audit_refs": [_json_mapping(ref) for ref in self.split_audit_refs],
            "n_a_reason": self.n_a_reason,
            "deferred_to": self.deferred_to,
            "deferred_reason": self.deferred_reason,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class UniversePITAuditSlot:
    status: EventAuditSlotStatus | str
    universe_snapshot_refs: tuple[EventEvidenceRef | Mapping[str, Any] | str, ...] = ()
    pit_policy_ref: EventEvidenceRef | Mapping[str, Any] | str | None = None
    n_a_reason: str = ""
    deferred_to: str = ""
    deferred_reason: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": _status_value(self.status),
            "universe_snapshot_refs": [_json_mapping(ref) for ref in self.universe_snapshot_refs],
            "pit_policy_ref": _json_mapping(self.pit_policy_ref),
            "n_a_reason": self.n_a_reason,
            "deferred_to": self.deferred_to,
            "deferred_reason": self.deferred_reason,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class EventReliabilityDeferredRef:
    risk_area: str
    follow_up_ref: str
    n_a_reason: str
    status: EventAuditSlotStatus | str = EventAuditSlotStatus.DEFERRED_CR154
    deferred_to: str = "CR154"
    deferred_reason: str = ""
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_area": self.risk_area,
            "status": _status_value(self.status),
            "deferred_to": self.deferred_to,
            "n_a_reason": self.n_a_reason,
            "deferred_reason": self.deferred_reason,
            "follow_up_ref": self.follow_up_ref,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class EventBiasRiskAuditSummary:
    summary_id: str
    event_study_report_ref: str
    overlap_report_slot: EventBiasAuditSlot | Mapping[str, Any] | None
    cluster_report_slot: EventBiasAuditSlot | Mapping[str, Any] | None
    endogeneity_treatment_slot: EventBiasAuditSlot | Mapping[str, Any] | None
    event_cv_split_audit_refs: EventCVSplitAuditRefs | Mapping[str, Any] | None
    universe_pit_audit: UniversePITAuditSlot | Mapping[str, Any] | None
    reliability_deferred_refs: tuple[EventReliabilityDeferredRef | Mapping[str, Any], ...]
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = EVENT_BIAS_AUDIT_SUMMARY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "summary_id": self.summary_id,
            "event_study_report_ref": self.event_study_report_ref,
            "overlap_report_slot": _json_mapping(self.overlap_report_slot),
            "cluster_report_slot": _json_mapping(self.cluster_report_slot),
            "endogeneity_treatment_slot": _json_mapping(self.endogeneity_treatment_slot),
            "event_cv_split_audit_refs": _json_mapping(self.event_cv_split_audit_refs),
            "universe_pit_audit": _json_mapping(self.universe_pit_audit),
            "reliability_deferred_refs": [_json_mapping(ref) for ref in self.reliability_deferred_refs],
            "operation_counts": normalise_event_study_operation_counts(self.operation_counts),
        }


def validate_event_study_method_spec(
    spec: EventStudyMethodSpec | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(spec)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue("event_study_method_missing", "spec", "EventStudyMethodSpec is mandatory."),)
    if not _text(data.get("method_id")):
        issues.append(_issue("event_study_method_id_missing", "method_id", "method_id is required."))
    if not _text(data.get("event_research_spec_id")):
        issues.append(
            _issue(
                "event_study_research_spec_id_missing",
                "event_research_spec_id",
                "event_research_spec_id must reference the S01 event research anchor.",
            )
        )
    issues.extend(_validate_window(data.get("estimation_window"), "estimation_window", "event_study_estimation_window_missing"))
    issues.extend(_validate_window(data.get("event_window"), "event_window", "event_study_event_window_missing"))
    issues.extend(_validate_normal_return_model(data.get("normal_return_model")))
    if _blank(data.get("return_horizon")) or _looks_like_forward_return_only(data):
        issues.append(
            _issue(
                "event_study_return_horizon_missing",
                "return_horizon",
                "return_horizon and event-study method evidence are required; ordinary forward return is not a substitute.",
            )
        )
    for field_name in ("car_method_slot", "bhar_method_slot", "calendar_time_method_slot"):
        issues.extend(_validate_method_slot(data.get(field_name), field_name))
    if not _text(data.get("method_ref")) and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_study_method_ref_or_na_missing",
                "method_ref",
                "method_ref or n_a_reason is required for method evidence traceability.",
            )
        )
    issues.extend(forbidden_event_operation_counts_zero(data.get("operation_counts")))
    return tuple(issues)


def validate_event_study_test_report(
    report: EventStudyTestReport | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(report)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue("event_study_test_report_missing", "report", "EventStudyTestReport is mandatory."),)
    if not _text(data.get("report_id")):
        issues.append(_issue("event_study_test_report_id_missing", "report_id", "report_id is required."))
    if not _text(data.get("method_id")):
        issues.append(_issue("event_study_test_method_id_missing", "method_id", "method_id is required."))
    if _as_int(data.get("sample_count")) <= 0:
        issues.append(_issue("event_study_test_report_sample_count_invalid", "sample_count", "sample_count must be positive."))
    slots = _slot_mapping(data.get("test_family_slots"))
    if not slots:
        issues.append(
            _issue(
                "event_study_test_family_slots_missing",
                "test_family_slots",
                "Patell/BMP/generalized sign/rank/bootstrap slots are mandatory.",
            )
        )
    for family_id in EVENT_STUDY_REQUIRED_TEST_FAMILIES:
        if family_id not in slots:
            issues.append(
                _issue(
                    "event_study_test_family_slot_missing",
                    f"test_family_slots.{family_id}",
                    f"{family_id} test family slot is mandatory.",
                )
            )
            continue
        issues.extend(_validate_test_family_slot(slots[family_id], f"test_family_slots.{family_id}"))
    if _blank(data.get("multiple_testing_or_data_snooping_slot")):
        issues.append(
            _issue(
                "event_study_multiple_testing_slot_missing",
                "multiple_testing_or_data_snooping_slot",
                "EV-GAP-7 multiple-testing/data-snooping slot is mandatory.",
            )
        )
    else:
        issues.extend(validate_event_multiple_testing_slot(data.get("multiple_testing_or_data_snooping_slot")))
    issues.extend(forbidden_event_operation_counts_zero(data.get("operation_counts")))
    return tuple(issues)


def validate_event_bias_audit_slot(
    slot: EventBiasAuditSlot | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    return _validate_audit_status_rule(
        _as_mapping(slot),
        field_prefix="bias_audit_slot",
        ref_fields=("evidence_refs",),
        missing_code="event_bias_audit_slot_missing",
    )


def validate_event_cv_split_audit_refs(
    audit_refs: EventCVSplitAuditRefs | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    return _validate_audit_status_rule(
        _as_mapping(audit_refs),
        field_prefix="event_cv_split_audit_refs",
        ref_fields=("split_audit_refs",),
        missing_code="event_cv_split_audit_refs_missing",
    )


def validate_universe_pit_audit(
    audit: UniversePITAuditSlot | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    return _validate_audit_status_rule(
        _as_mapping(audit),
        field_prefix="universe_pit_audit",
        ref_fields=("universe_snapshot_refs", "pit_policy_ref"),
        missing_code="universe_pit_audit_missing",
    )


def validate_event_reliability_deferred_refs(
    refs: Sequence[EventReliabilityDeferredRef | Mapping[str, Any]] | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    items = _deferred_ref_mapping(refs)
    issues: list[EventStudyValidationIssue] = []
    for risk_area in EVENT_RELIABILITY_REQUIRED_DEFERRED_AREAS:
        if risk_area not in items:
            issues.append(
                _issue(
                    "event_reliability_deferred_ref_missing",
                    f"reliability_deferred_refs.{risk_area}",
                    f"{risk_area} deferred CR154 ref is mandatory.",
                )
            )
            continue
        data = items[risk_area]
        issues.extend(
            _validate_audit_status_rule(
                data,
                field_prefix=f"reliability_deferred_refs.{risk_area}",
                ref_fields=("follow_up_ref",),
                missing_code="event_reliability_deferred_ref_missing",
                require_deferred=True,
            )
        )
        if _normalise_id(data.get("risk_area")) != risk_area:
            issues.append(
                _issue(
                    "event_reliability_deferred_ref_area_mismatch",
                    f"reliability_deferred_refs.{risk_area}.risk_area",
                    "Deferred reliability ref risk_area must match the required CR154 risk family.",
                )
            )
    return tuple(issues)


def validate_event_bias_risk_audit_summary(
    summary: EventBiasRiskAuditSummary | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(summary)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue("event_bias_risk_audit_summary_missing", "summary", "EventBiasRiskAuditSummary is mandatory."),)
    if not _text(data.get("summary_id")):
        issues.append(_issue("event_bias_risk_audit_summary_id_missing", "summary_id", "summary_id is required."))
    for field_name in ("overlap_report_slot", "cluster_report_slot", "endogeneity_treatment_slot"):
        if _blank(data.get(field_name)):
            issues.append(_issue("event_bias_audit_slot_missing", field_name, f"{field_name} is mandatory."))
        else:
            issues.extend(validate_event_bias_audit_slot(data.get(field_name)))
    if _blank(data.get("event_cv_split_audit_refs")):
        issues.append(
            _issue(
                "event_cv_split_audit_refs_missing",
                "event_cv_split_audit_refs",
                "event_cv_split_audit_refs is mandatory.",
            )
        )
    else:
        issues.extend(validate_event_cv_split_audit_refs(data.get("event_cv_split_audit_refs")))
    if _blank(data.get("universe_pit_audit")):
        issues.append(_issue("universe_pit_audit_missing", "universe_pit_audit", "universe_pit_audit is mandatory."))
    else:
        issues.extend(validate_universe_pit_audit(data.get("universe_pit_audit")))
    issues.extend(validate_event_reliability_deferred_refs(data.get("reliability_deferred_refs")))
    issues.extend(forbidden_event_operation_counts_zero(data.get("operation_counts")))
    return tuple(issues)


def validate_event_multiple_testing_slot(
    slot: EventStudyMultipleTestingSlot | Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(slot)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (
            _issue(
                "event_study_multiple_testing_slot_missing",
                "multiple_testing_or_data_snooping_slot",
                "EV-GAP-7 multiple-testing/data-snooping slot is mandatory.",
            ),
        )
    if not _text(data.get("family_id")):
        issues.append(_issue("event_study_multiple_testing_family_id_missing", "family_id", "family_id is required."))
    if _as_int(data.get("tested_window_count")) <= 0:
        issues.append(
            _issue(
                "event_study_multiple_testing_window_count_invalid",
                "tested_window_count",
                "tested_window_count must be positive.",
            )
        )
    correction_method = _normalise_id(data.get("correction_method"))
    if not correction_method:
        issues.append(_issue("event_study_multiple_testing_correction_method_missing", "correction_method", "correction_method is required."))
    status = _status_value(data.get("status"))
    if status not in {item.value for item in EventStudyStatus}:
        issues.append(_issue("event_study_status_invalid", "status", "status must be PASS, FAIL, NEEDS_REVIEW or BLOCKED."))
    if status in {EVENT_STUDY_STATUS_PASS, EVENT_STUDY_STATUS_FAIL}:
        if not _valid_p_value(data.get("adjusted_p_value")):
            issues.append(
                _issue(
                    "event_study_adjusted_p_value_invalid",
                    "adjusted_p_value",
                    "adjusted_p_value must be in [0, 1] for PASS/FAIL multiple-testing slots.",
                )
            )
    elif data.get("adjusted_p_value") is not None and not _valid_p_value(data.get("adjusted_p_value")):
        issues.append(_issue("event_study_adjusted_p_value_invalid", "adjusted_p_value", "adjusted_p_value must be in [0, 1]."))
    if not _text(data.get("report_ref")) and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_study_multiple_testing_report_ref_or_na_missing",
                "report_ref",
                "report_ref or n_a_reason is required.",
            )
        )
    if correction_method in EVENT_STUDY_DEFERRED_ALGORITHMS and _active_implementation(data):
        issues.append(
            _issue(
                "event_study_unsupported_algorithm_active",
                "correction_method",
                f"{correction_method} is slot-only/deferred in CR153 first wave.",
            )
        )
    return tuple(issues)


def forbidden_event_operation_counts_zero(
    operation_counts: Mapping[str, Any] | None,
) -> tuple[EventStudyValidationIssue, ...]:
    normalized = normalise_event_study_operation_counts(operation_counts)
    return tuple(
        _issue(
            "event_study_forbidden_operation_nonzero",
            key,
            "CR153 S02 is local/static/fixture-only; forbidden operation counters must remain zero.",
        )
        for key, value in normalized.items()
        if int(value) != 0
    )


def normalise_event_study_operation_counts(operation_counts: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(operation_counts or {})
    keys = tuple(dict.fromkeys((*EVENT_STUDY_FORBIDDEN_OPERATION_COUNTERS, *tuple(str(key) for key in source))))
    normalized: dict[str, int] = {}
    for key in keys:
        try:
            normalized[key] = int(source.get(key, 0) or 0)
        except (TypeError, ValueError):
            normalized[key] = 1
    return normalized


def _validate_window(value: Any, field_name: str, missing_code: str) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(value)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue(missing_code, field_name, f"{field_name} is required."),)
    if not _text(data.get("window_id")):
        issues.append(_issue(f"{field_name}_id_missing", f"{field_name}.window_id", "window_id is required."))
    has_relative = data.get("relative_start") is not None and data.get("relative_end") is not None
    has_calendar = _text(data.get("calendar_start")) and _text(data.get("calendar_end"))
    if not has_relative and not has_calendar:
        issues.append(
            _issue(
                f"{field_name}_boundary_missing",
                field_name,
                "Window must define complete relative or calendar boundaries.",
            )
        )
    if has_relative and _as_int(data.get("relative_start")) > _as_int(data.get("relative_end")):
        issues.append(_issue(f"{field_name}_relative_boundary_invalid", field_name, "relative_start must be <= relative_end."))
    return tuple(issues)


def _validate_normal_return_model(value: Any) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(value)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue("event_study_normal_return_model_missing", "normal_return_model", "normal_return_model is required."),)
    model_type = _normalise_id(data.get("model_type"))
    if not model_type:
        issues.append(_issue("event_study_normal_return_model_type_missing", "normal_return_model.model_type", "model_type is required."))
    if model_type == "factor_model" and not _text(data.get("factor_model_ref")):
        issues.append(
            _issue(
                "event_study_factor_model_ref_missing",
                "normal_return_model.factor_model_ref",
                "factor_model requires factor_model_ref.",
            )
        )
    if _status_value(data.get("status", EVENT_STUDY_STATUS_PASS)) == EVENT_STUDY_STATUS_BLOCKED and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_study_normal_return_model_blocked_reason_missing",
                "normal_return_model.n_a_reason",
                "Blocked normal return model requires n_a_reason.",
            )
        )
    return tuple(issues)


def _validate_method_slot(value: Any, field_name: str) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(value)
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue("event_study_method_slot_missing", field_name, f"{field_name} is required."),)
    if not _text(data.get("method_name")):
        issues.append(_issue("event_study_method_slot_name_missing", f"{field_name}.method_name", "method_name is required."))
    status = _status_value(data.get("status"))
    if status not in {item.value for item in EventStudyStatus}:
        issues.append(_issue("event_study_status_invalid", f"{field_name}.status", "status must be PASS, FAIL, NEEDS_REVIEW or BLOCKED."))
    if not _text(data.get("report_ref")) and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_study_method_slot_report_ref_or_na_missing",
                f"{field_name}.report_ref",
                "report_ref or n_a_reason is required.",
            )
        )
    if _normalise_id(data.get("method_name")) in EVENT_STUDY_DEFERRED_ALGORITHMS and _active_implementation(data):
        issues.append(
            _issue(
                "event_study_unsupported_algorithm_active",
                f"{field_name}.method_name",
                "Deferred algorithms are slot-only in CR153 first wave.",
            )
        )
    return tuple(issues)


def _validate_test_family_slot(value: Any, field_name: str) -> tuple[EventStudyValidationIssue, ...]:
    data = _as_mapping(value)
    issues: list[EventStudyValidationIssue] = []
    if not _text(data.get("family_id")):
        issues.append(_issue("event_study_test_family_id_missing", f"{field_name}.family_id", "family_id is required."))
    status = _status_value(data.get("status"))
    if status not in {item.value for item in EventStudyStatus}:
        issues.append(_issue("event_study_status_invalid", f"{field_name}.status", "status must be PASS, FAIL, NEEDS_REVIEW or BLOCKED."))
    sample_count = _as_int(data.get("sample_count"))
    if sample_count <= 0 and not _text(data.get("n_a_reason")):
        issues.append(_issue("event_study_test_family_sample_count_invalid", f"{field_name}.sample_count", "sample_count must be positive."))
    if status in {EVENT_STUDY_STATUS_PASS, EVENT_STUDY_STATUS_FAIL}:
        if not _valid_p_value(data.get("raw_p_value")):
            issues.append(_issue("event_study_raw_p_value_invalid", f"{field_name}.raw_p_value", "raw_p_value must be in [0, 1]."))
        if not _valid_p_value(data.get("adjusted_p_value")):
            issues.append(_issue("event_study_adjusted_p_value_invalid", f"{field_name}.adjusted_p_value", "adjusted_p_value must be in [0, 1]."))
    else:
        for p_value_field in ("raw_p_value", "adjusted_p_value"):
            if data.get(p_value_field) is not None and not _valid_p_value(data.get(p_value_field)):
                issues.append(_issue(f"event_study_{p_value_field}_invalid", f"{field_name}.{p_value_field}", f"{p_value_field} must be in [0, 1]."))
    if not _text(data.get("report_ref")) and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_study_test_family_report_ref_or_na_missing",
                f"{field_name}.report_ref",
                "report_ref or n_a_reason is required.",
            )
        )
    return tuple(issues)


def _validate_audit_status_rule(
    data: Mapping[str, Any],
    *,
    field_prefix: str,
    ref_fields: Sequence[str],
    missing_code: str,
    require_deferred: bool = False,
) -> tuple[EventStudyValidationIssue, ...]:
    issues: list[EventStudyValidationIssue] = []
    if not data:
        return (_issue(missing_code, field_prefix, f"{field_prefix} is mandatory."),)
    status = _normalise_id(_status_value(data.get("status")))
    if status not in EVENT_AUDIT_ALLOWED_SLOT_STATUSES:
        issues.append(
            _issue(
                "event_audit_slot_status_invalid",
                f"{field_prefix}.status",
                "S03 audit slot status must be present, not_applicable, deferred_cr154, needs_review or blocked.",
            )
        )
        return tuple(issues)
    if require_deferred and status != EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154:
        issues.append(
            _issue(
                "event_reliability_deferred_ref_status_invalid",
                f"{field_prefix}.status",
                "Capacity, impact, regime and reconciliation refs must remain deferred_cr154 in CR153.",
            )
        )
    has_refs = _has_any_ref(data, ref_fields)
    has_reason = _has_audit_reason(data)
    if status == EVENT_AUDIT_SLOT_STATUS_PRESENT and not has_refs:
        issues.append(
            _issue(
                "event_audit_present_refs_missing",
                f"{field_prefix}.evidence_refs",
                "present S03 audit slots require explicit static refs.",
            )
        )
    if status == EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE and not _text(data.get("n_a_reason")):
        issues.append(
            _issue(
                "event_audit_not_applicable_reason_missing",
                f"{field_prefix}.n_a_reason",
                "not_applicable S03 audit slots require n_a_reason.",
            )
        )
    if status == EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154:
        if _text(data.get("deferred_to")) != "CR154":
            issues.append(
                _issue(
                    "event_audit_deferred_to_cr154_missing",
                    f"{field_prefix}.deferred_to",
                    "deferred_cr154 S03 audit slots require deferred_to=CR154.",
                )
            )
        if not has_reason:
            issues.append(
                _issue(
                    "event_audit_deferred_reason_missing",
                    f"{field_prefix}.n_a_reason",
                    "deferred_cr154 S03 audit slots require a concrete deferred reason.",
                )
            )
    if status == EVENT_AUDIT_SLOT_STATUS_NEEDS_REVIEW and (not has_reason or not (has_refs or _has_limitations(data))):
        issues.append(
            _issue(
                "event_audit_needs_review_evidence_or_reason_missing",
                field_prefix,
                "needs_review S03 audit slots require a reason plus refs or limitations.",
            )
        )
    return tuple(issues)


def _deferred_ref_mapping(
    refs: Sequence[EventReliabilityDeferredRef | Mapping[str, Any]] | Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    if refs is None:
        raw_items: tuple[Any, ...] = ()
    elif isinstance(refs, Mapping):
        raw_items = tuple(refs.values()) if all(isinstance(item, Mapping) for item in refs.values()) else tuple(refs.items())
    else:
        raw_items = tuple(refs)
    result: dict[str, dict[str, Any]] = {}
    for item in raw_items:
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[1], Mapping):
            data = _as_mapping(item[1])
            risk_area = _normalise_id(data.get("risk_area") or item[0])
        else:
            data = _as_mapping(item)
            risk_area = _normalise_id(data.get("risk_area"))
        if risk_area:
            result[risk_area] = data
    return result


def _has_any_ref(data: Mapping[str, Any], ref_fields: Sequence[str]) -> bool:
    for field_name in ref_fields:
        value = data.get(field_name)
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, Mapping) and any(_text(item) for item in value.values()):
            return True
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0:
            return True
    return False


def _has_audit_reason(data: Mapping[str, Any]) -> bool:
    if _text(data.get("n_a_reason")) or _text(data.get("deferred_reason")) or _text(data.get("follow_up_ref")):
        return True
    return _has_limitations(data)


def _has_limitations(data: Mapping[str, Any]) -> bool:
    return bool(_sequence(data.get("limitations")))


def _slot_mapping(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, Mapping):
        raw_items = value.values() if all(isinstance(item, Mapping) for item in value.values()) else value.items()
    else:
        raw_items = _sequence(value)
    slots: dict[str, dict[str, Any]] = {}
    for item in raw_items:
        data = _as_mapping(item)
        family_id = _normalise_id(data.get("family_id"))
        if family_id:
            slots[family_id] = data
    return slots


def _as_mapping(value: Any) -> dict[str, Any]:
    return as_mapping(value, none_as_empty=True) or {}


def _json_mapping(value: Any) -> Any:
    if value is None:
        return None
    mapped = as_mapping(value)
    return json_safe(mapped if mapped is not None else value)


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return tuple(value.values())
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _status_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value or "")


def _normalise_id(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _valid_p_value(value: Any) -> bool:
    numeric = safe_float(value)
    return numeric is not None and 0.0 <= numeric <= 1.0


def _active_implementation(data: Mapping[str, Any]) -> bool:
    state = _normalise_id(data.get("implementation_state") or data.get("support_level") or "")
    active_claim = bool(data.get("active_implementation") or data.get("implemented"))
    return active_claim or state in {"active", "implemented", "active_implementation"}


def _looks_like_forward_return_only(data: Mapping[str, Any]) -> bool:
    has_forward = any(key in data for key in ("forward_return_days", "forward_return_label", "ordinary_forward_return"))
    method_slots = (data.get("car_method_slot"), data.get("bhar_method_slot"), data.get("calendar_time_method_slot"))
    return has_forward and any(_blank(slot) for slot in method_slots)


def _issue(code: str, field: str, message: str) -> EventStudyValidationIssue:
    return EventStudyValidationIssue(code=code, severity="blocker", message=message, field=field)


__all__ = [
    "EVENT_AUDIT_ALLOWED_SLOT_STATUSES",
    "EVENT_AUDIT_SLOT_STATUS_BLOCKED",
    "EVENT_AUDIT_SLOT_STATUS_DEFERRED_CR154",
    "EVENT_AUDIT_SLOT_STATUS_NEEDS_REVIEW",
    "EVENT_AUDIT_SLOT_STATUS_NOT_APPLICABLE",
    "EVENT_AUDIT_SLOT_STATUS_PRESENT",
    "EVENT_BIAS_AUDIT_SUMMARY_SCHEMA",
    "EVENT_RELIABILITY_REQUIRED_DEFERRED_AREAS",
    "EVENT_STUDY_DEFERRED_ALGORITHMS",
    "EVENT_STUDY_FORBIDDEN_OPERATION_COUNTERS",
    "EVENT_STUDY_METHOD_SPEC_SCHEMA",
    "EVENT_STUDY_REQUIRED_TEST_FAMILIES",
    "EVENT_STUDY_STATUS_BLOCKED",
    "EVENT_STUDY_STATUS_FAIL",
    "EVENT_STUDY_STATUS_NEEDS_REVIEW",
    "EVENT_STUDY_STATUS_PASS",
    "EVENT_STUDY_TEST_REPORT_SCHEMA",
    "EventAuditSlotStatus",
    "EventBiasAuditSlot",
    "EventBiasRiskAuditSummary",
    "EventCVSplitAuditRefs",
    "EventEvidenceRef",
    "EventReliabilityDeferredRef",
    "EventStudyMethodSlot",
    "EventStudyMethodSpec",
    "EventStudyMultipleTestingSlot",
    "EventStudyStatus",
    "EventStudyTestFamilySlot",
    "EventStudyTestReport",
    "EventStudyValidationIssue",
    "EventStudyWindowSpec",
    "NormalReturnModelSpec",
    "UniversePITAuditSlot",
    "forbidden_event_operation_counts_zero",
    "normalise_event_study_operation_counts",
    "validate_event_bias_audit_slot",
    "validate_event_bias_risk_audit_summary",
    "validate_event_cv_split_audit_refs",
    "validate_event_multiple_testing_slot",
    "validate_event_reliability_deferred_refs",
    "validate_event_study_method_spec",
    "validate_event_study_test_report",
    "validate_universe_pit_audit",
]
