"""CR153 event strategy admission gate.

This module evaluates passed-in static metadata only. It does not read event
feeds, files, credentials, lake/NAS/provider data, runtime adapters, brokers,
event stores, catalogs, registries, Git remotes, or real returns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.event_strategy_contracts import (
    validate_event_bias_risk_audit_summary,
    validate_event_study_method_spec,
    validate_event_study_test_report,
)
from engine.research_production_contracts import CR153_EVENT_FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import as_mapping, json_safe


EVENT_ADMISSION_GATE_SCHEMA = "event_strategy_admission_gate_v1"
EVENT_GATE_LIMITATIONS = (
    "event_gate_pass_not_runtime_ready",
    "no_real_event_feed",
    "no_live_event_listener",
    "no_qmt_runtime",
    "no_simulation_or_live_authorization",
    "no_broker_order",
    "no_trading_authorization",
    "no_event_store_or_registry_publication",
)
EVENT_FORBIDDEN_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            *CR153_EVENT_FORBIDDEN_OPERATION_COUNTERS,
            "credential_read",
            "real_lake_read",
            "real_lake_write",
            "nas_access",
            "nas_read",
            "nas_write",
            "nas_sync_or_write",
            "provider_fetch",
            "real_event_feed",
            "real_event_feed_read",
            "live_event_listener",
            "live_listener_started",
            "event_store_write",
            "catalog_pointer_mutation",
            "model_registry_write",
            "registry_write",
            "feature_store_write",
            "label_store_write",
            "prediction_store_write",
            "runtime_operation",
            "runtime_started",
            "qmt_runtime",
            "miniqmt_runtime",
            "xtquant_runtime",
            "gateway_start",
            "simulation_or_live_run",
            "paper_trading_run",
            "broker_access",
            "broker_or_order_flow",
            "account_query",
            "real_order",
            "order_submit",
            "order_cancel",
            "trading_operation",
            "external_framework_run",
            "git_remote_write",
        )
    )
)


class EventAdmissionGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class EventAdmissionGateIssue:
    code: str
    message: str
    source: str
    field: str = ""
    severity: str = "blocker"
    evidence_ref: str = ""
    unlock_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class EventStrategyAdmissionGate:
    status: EventAdmissionGateStatus | str
    gate_present: bool = True
    gate_required: bool = True
    gate_ref: str = ""
    blocked_reasons: tuple[EventAdmissionGateIssue | Mapping[str, Any], ...] = ()
    needs_review_reasons: tuple[EventAdmissionGateIssue | Mapping[str, Any], ...] = ()
    evidence_refs: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    limitations: tuple[str, ...] = EVENT_GATE_LIMITATIONS
    schema_version: str = EVENT_ADMISSION_GATE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        status = _status_value(self.status) or EventAdmissionGateStatus.BLOCKED.value
        return {
            "schema_version": self.schema_version,
            "gate_present": bool(self.gate_present),
            "gate_required": bool(self.gate_required),
            "gate_status": status,
            "status": status,
            "gate_ref": self.gate_ref,
            "blocked_reasons": [_issue_payload(reason) for reason in self.blocked_reasons],
            "needs_review_reasons": [_issue_payload(reason) for reason in self.needs_review_reasons],
            "evidence_refs": tuple(str(item) for item in self.evidence_refs if str(item)),
            "operation_counts": dict(self.operation_counts),
            "limitations": tuple(dict.fromkeys((*EVENT_GATE_LIMITATIONS, *self.limitations))),
        }


def evaluate_event_strategy_admission_gate(
    *,
    pit_gate: Mapping[str, Any] | Any,
    method_spec: Mapping[str, Any] | Any,
    test_report: Mapping[str, Any] | Any,
    multiple_testing_slot: Mapping[str, Any] | Any | None = None,
    bias_risk_audit: Mapping[str, Any] | Any | None = None,
    trace_evidence: Mapping[str, Any] | Sequence[Any] | Any | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    gate_required: bool = True,
    gate_ref: str = "",
) -> EventStrategyAdmissionGate:
    """Evaluate CR153 event admission evidence without side effects."""

    pit_data = _as_mapping(pit_gate)
    method_data = _as_mapping(method_spec)
    report_data = _as_mapping(test_report)
    multiple_data = _as_mapping(multiple_testing_slot) or _as_mapping(
        report_data.get("multiple_testing_or_data_snooping_slot")
    )
    bias_data = _as_mapping(bias_risk_audit)
    trace_data = _trace_mapping(trace_evidence)

    normalized_counts = normalise_event_gate_operation_counts(
        _merge_operation_counts(
            pit_data.get("operation_counts"),
            method_data.get("operation_counts"),
            report_data.get("operation_counts"),
            bias_data.get("operation_counts"),
            trace_data.get("operation_counts"),
            operation_counts,
        )
    )

    issues: list[EventAdmissionGateIssue] = []
    issues.extend(validate_event_gate_operation_counters(normalized_counts))

    mandatory_inputs = (
        ("pit_gate", pit_data, "event_gate_pit_evidence_missing", "PIT/revision evidence is mandatory."),
        ("method_spec", method_data, "event_gate_method_evidence_missing", "Event study method evidence is mandatory."),
        ("test_report", report_data, "event_gate_test_family_evidence_missing", "Event study test family evidence is mandatory."),
        (
            "multiple_testing_or_data_snooping_slot",
            multiple_data,
            "event_gate_multiple_testing_evidence_missing",
            "Multiple-testing/data-snooping evidence is mandatory.",
        ),
        ("trace_evidence", trace_data, "event_gate_trace_evidence_missing", "Event trace evidence is mandatory."),
    )
    for source, data, code, message in mandatory_inputs:
        if not data:
            issues.append(_issue(code, message, source, severity="blocker"))

    if method_data:
        issues.extend(_from_validation_issues(validate_event_study_method_spec(method_data), "method_spec"))
    if report_data:
        issues.extend(_from_validation_issues(validate_event_study_test_report(report_data), "test_report"))
    if bias_data:
        issues.extend(_from_validation_issues(validate_event_bias_risk_audit_summary(bias_data), "bias_risk_audit"))

    status_inputs = (
        ("pit_gate", pit_data),
        ("method_spec", method_data),
        ("test_report", report_data),
        ("multiple_testing_or_data_snooping_slot", multiple_data),
        ("bias_risk_audit", bias_data),
        ("trace_evidence", trace_data),
    )
    for source, data in status_inputs:
        if data:
            issues.extend(_status_issues(source, data))
            issues.extend(_nested_status_issues(source, data))

    blocked = tuple(issue for issue in issues if _severity(issue) == "blocker")
    fails = tuple(issue for issue in issues if _severity(issue) == "fail")
    reviews = tuple(issue for issue in issues if _severity(issue) == "review")
    if blocked:
        status = EventAdmissionGateStatus.BLOCKED
    elif fails:
        status = EventAdmissionGateStatus.FAIL
    elif reviews:
        status = EventAdmissionGateStatus.NEEDS_REVIEW
    else:
        status = EventAdmissionGateStatus.PASS

    evidence_refs = _collect_refs(
        gate_ref,
        pit_data,
        method_data,
        report_data,
        multiple_data,
        bias_data,
        trace_data,
        *(issue.to_dict() for issue in issues),
    )
    return EventStrategyAdmissionGate(
        status=status,
        gate_present=True,
        gate_required=gate_required,
        gate_ref=gate_ref or (evidence_refs[0] if evidence_refs else ""),
        blocked_reasons=tuple((*blocked, *fails)),
        needs_review_reasons=reviews,
        evidence_refs=evidence_refs,
        operation_counts=normalized_counts,
        limitations=EVENT_GATE_LIMITATIONS,
    )


def event_gate_summary(gate: EventStrategyAdmissionGate | Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(gate, EventStrategyAdmissionGate):
        return gate.to_dict()
    data = _as_mapping(gate)
    if not data:
        blocked = _issue(
            "event_gate_summary_missing",
            "Event admission gate summary is missing.",
            "event_gate_summary",
            severity="blocker",
        )
        return EventStrategyAdmissionGate(
            status=EventAdmissionGateStatus.BLOCKED,
            gate_present=False,
            gate_required=True,
            blocked_reasons=(blocked,),
            operation_counts=normalise_event_gate_operation_counts({}),
        ).to_dict()
    status = _known_event_status(data.get("gate_status") or data.get("status"))
    if status is None:
        blocked = _issue(
            "event_gate_unknown_status",
            "Event admission gate summary status is unknown and must fail closed.",
            "event_gate_summary",
            field="status",
            severity="blocker",
        )
        data = dict(data)
        data["gate_status"] = EventAdmissionGateStatus.BLOCKED.value
        data["status"] = EventAdmissionGateStatus.BLOCKED.value
        data["blocked_reasons"] = tuple((*_sequence(data.get("blocked_reasons")), blocked.to_dict()))
    else:
        data = dict(data)
        data["gate_status"] = status.value
        data["status"] = status.value
    data.setdefault("schema_version", EVENT_ADMISSION_GATE_SCHEMA)
    data.setdefault("gate_present", True)
    data.setdefault("gate_required", True)
    data.setdefault("gate_ref", "")
    data.setdefault("blocked_reasons", ())
    data.setdefault("needs_review_reasons", ())
    data.setdefault("evidence_refs", ())
    data["operation_counts"] = normalise_event_gate_operation_counts(data.get("operation_counts"))
    data["limitations"] = tuple(dict.fromkeys((*EVENT_GATE_LIMITATIONS, *_sequence(data.get("limitations")))))
    return dict(json_safe(data))


def validate_event_gate_operation_counters(counters: Mapping[str, Any] | None) -> tuple[EventAdmissionGateIssue, ...]:
    normalized = normalise_event_gate_operation_counts(counters)
    return tuple(
        _issue(
            "event_gate_forbidden_operation_nonzero",
            "CR153 S04 is local/static/fixture-only; forbidden operation counters must be zero.",
            "operation_counts",
            field=key,
            severity="blocker",
            unlock_condition="reset_forbidden_operation_counter_to_zero_and_start_independent_authorization",
        )
        for key, value in normalized.items()
        if int(value) != 0
    )


def normalise_event_gate_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    keys = tuple(dict.fromkeys((*EVENT_FORBIDDEN_OPERATION_COUNTERS, *tuple(str(key) for key in source))))
    normalized: dict[str, int] = {}
    for key in keys:
        try:
            normalized[key] = int(source.get(key, 0) or 0)
        except (TypeError, ValueError):
            normalized[key] = 1
    return normalized


def _from_validation_issues(issues: Sequence[Any], source: str) -> tuple[EventAdmissionGateIssue, ...]:
    result: list[EventAdmissionGateIssue] = []
    for issue in issues:
        data = _as_mapping(issue)
        severity = _issue_severity_from_status(data)
        result.append(
            _issue(
                str(data.get("code") or "event_gate_input_validation_issue"),
                str(data.get("message") or "Event input validation issue."),
                source,
                field=str(data.get("field") or ""),
                severity=severity,
                evidence_ref=str(data.get("evidence_ref") or ""),
            )
        )
    return tuple(result)


def _status_issues(source: str, data: Mapping[str, Any]) -> tuple[EventAdmissionGateIssue, ...]:
    raw = data.get("gate_status") or data.get("status")
    if raw is None or str(raw).strip() == "":
        return ()
    status = _known_event_status(raw)
    if status is EventAdmissionGateStatus.BLOCKED:
        return (
            _issue(
                "event_gate_input_status_blocked",
                f"{source} status is BLOCKED.",
                source,
                field="status",
                severity="blocker",
                evidence_ref=_first_ref(data),
            ),
        )
    if status is EventAdmissionGateStatus.FAIL:
        return (
            _issue(
                "event_gate_input_status_fail",
                f"{source} status is FAIL.",
                source,
                field="status",
                severity="fail",
                evidence_ref=_first_ref(data),
            ),
        )
    if status is EventAdmissionGateStatus.NEEDS_REVIEW:
        return (
            _issue(
                "event_gate_input_status_needs_review",
                f"{source} status requires review.",
                source,
                field="status",
                severity="review",
                evidence_ref=_first_ref(data),
            ),
        )
    if status is EventAdmissionGateStatus.PASS:
        return ()
    return (
        _issue(
            "event_gate_unknown_input_status",
            f"{source} status is unknown and must fail closed.",
            source,
            field="status",
            severity="blocker",
            evidence_ref=_first_ref(data),
        ),
    )


def _nested_status_issues(source: str, data: Mapping[str, Any]) -> tuple[EventAdmissionGateIssue, ...]:
    issues: list[EventAdmissionGateIssue] = []
    for field_name, value in data.items():
        if field_name in {"status", "gate_status", "schema_version", "operation_counts"}:
            continue
        if isinstance(value, Mapping):
            issues.extend(_status_issues(source, {**value, "field": field_name}))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for index, item in enumerate(value):
                item_data = _as_mapping(item)
                if item_data:
                    issues.extend(_status_issues(source, {**item_data, "field": f"{field_name}.{index}"}))
    return tuple(issues)


def _known_event_status(value: Any) -> EventAdmissionGateStatus | None:
    normalized = _status_value(value).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "PASSED": "PASS",
        "FAILED": "FAIL",
        "REVIEW": "NEEDS_REVIEW",
        "WARN": "NEEDS_REVIEW",
        "WARNING": "NEEDS_REVIEW",
        "BLOCK": "BLOCKED",
        "PRESENT": "PASS",
        "NOT_APPLICABLE": "PASS",
        "DEFERRED_CR154": "PASS",
    }
    normalized = aliases.get(normalized, normalized)
    for status in EventAdmissionGateStatus:
        if normalized == status.value:
            return status
    return None


def _issue_severity_from_status(data: Mapping[str, Any]) -> str:
    severity = str(data.get("severity") or "").strip().lower()
    if severity in {"blocker", "fail", "review"}:
        return severity
    status = _known_event_status(data.get("status"))
    if status is EventAdmissionGateStatus.FAIL:
        return "fail"
    if status is EventAdmissionGateStatus.NEEDS_REVIEW:
        return "review"
    return "blocker"


def _severity(issue: EventAdmissionGateIssue) -> str:
    return issue.severity if issue.severity in {"blocker", "fail", "review"} else "blocker"


def _merge_operation_counts(*items: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in items:
        for key, value in _as_mapping(item).items():
            merged[str(key)] = value
    return merged


def _trace_mapping(trace_evidence: Any) -> dict[str, Any]:
    if trace_evidence is None:
        return {}
    data = _as_mapping(trace_evidence)
    if data:
        return data
    refs = tuple(str(item) for item in _sequence(trace_evidence) if str(item))
    return {"status": EventAdmissionGateStatus.PASS.value, "evidence_refs": refs} if refs else {}


def _collect_refs(*items: Any) -> tuple[str, ...]:
    refs: list[str] = []
    for item in items:
        _append_refs(refs, item)
    return tuple(dict.fromkeys(ref for ref in refs if ref))


def _append_refs(refs: list[str], value: Any) -> None:
    data = _as_mapping(value)
    if not data:
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
        return
    for field_name in (
        "gate_ref",
        "event_gate_ref",
        "evidence_ref",
        "ref",
        "report_ref",
        "trace_ref",
        "method_ref",
        "revision_policy_ref",
        "summary_id",
        "report_id",
    ):
        text = str(data.get(field_name) or "").strip()
        if text:
            refs.append(text)
    for field_name in (
        "evidence_refs",
        "revision_source_refs",
        "source_snapshot_refs",
        "split_audit_refs",
        "universe_snapshot_refs",
        "reliability_deferred_refs",
        "test_family_slots",
    ):
        for item in _sequence(data.get(field_name)):
            _append_refs(refs, item)
    for field_name in (
        "pit_policy_ref",
        "overlap_report_slot",
        "cluster_report_slot",
        "endogeneity_treatment_slot",
        "event_cv_split_audit_refs",
        "universe_pit_audit",
        "multiple_testing_or_data_snooping_slot",
    ):
        _append_refs(refs, data.get(field_name))


def _first_ref(data: Mapping[str, Any]) -> str:
    refs = _collect_refs(data)
    return refs[0] if refs else ""


def _issue(
    code: str,
    message: str,
    source: str,
    *,
    field: str = "",
    severity: str = "blocker",
    evidence_ref: str = "",
    unlock_condition: str = "",
) -> EventAdmissionGateIssue:
    return EventAdmissionGateIssue(
        code=code,
        message=message,
        source=source,
        field=field,
        severity=severity,
        evidence_ref=evidence_ref,
        unlock_condition=unlock_condition,
    )


def _issue_payload(issue: EventAdmissionGateIssue | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(issue, EventAdmissionGateIssue):
        return issue.to_dict()
    return dict(json_safe(dict(issue)))


def _as_mapping(value: Any) -> dict[str, Any]:
    return as_mapping(value, none_as_empty=True) or {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _status_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value or "")


__all__ = [
    "EVENT_ADMISSION_GATE_SCHEMA",
    "EVENT_FORBIDDEN_OPERATION_COUNTERS",
    "EVENT_GATE_LIMITATIONS",
    "EventAdmissionGateIssue",
    "EventAdmissionGateStatus",
    "EventStrategyAdmissionGate",
    "evaluate_event_strategy_admission_gate",
    "event_gate_summary",
    "normalise_event_gate_operation_counts",
    "validate_event_gate_operation_counters",
]
