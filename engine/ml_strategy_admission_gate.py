"""CR152 ML strategy admission gate contracts.

本模块只聚合本地/static/fixture 证据，不训练模型，不读取真实数据，不写
model registry / store / catalog，也不触发 runtime 或交易链路。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import json_safe


ML_ADMISSION_GATE_SCHEMA = "ml_strategy_admission_gate_v1"
CR152_ML_FORBIDDEN_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            *FORBIDDEN_OPERATION_COUNTERS,
            "real_model_training",
            "real_data_validation",
            "feature_store_write",
            "label_store_write",
            "model_store_write",
            "model_registry_write",
            "prediction_store_write",
            "catalog_pointer_mutation",
        )
    )
)


class MLAdmissionGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class MLAdmissionGateIssue:
    code: str
    message: str
    source: str
    field: str = ""
    severity: str = "blocker"
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class MLAdmissionGate:
    status: MLAdmissionGateStatus
    gate_present: bool
    gate_required: bool
    gate_ref: str
    blocked_reasons: tuple[MLAdmissionGateIssue, ...]
    needs_review_reasons: tuple[MLAdmissionGateIssue, ...]
    evidence_refs: tuple[str, ...]
    operation_counts: Mapping[str, int]
    schema_version: str = ML_ADMISSION_GATE_SCHEMA

    @property
    def passed(self) -> bool:
        return self.status is MLAdmissionGateStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "gate_present": self.gate_present,
            "gate_required": self.gate_required,
            "gate_status": self.status.value,
            "gate_ref": self.gate_ref,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "needs_review_reasons": [reason.to_dict() for reason in self.needs_review_reasons],
            "evidence_refs": list(self.evidence_refs),
            "operation_counts": dict(self.operation_counts),
        }


def evaluate_ml_strategy_admission_gate(
    evidence: Mapping[str, Any] | None = None,
    *,
    operation_counts: Mapping[str, Any] | None = None,
    gate_required: bool = True,
    gate_ref: str = "",
) -> MLAdmissionGate:
    payload = dict(evidence or {})
    issues: list[MLAdmissionGateIssue] = []
    for key in ("pit_feature_matrix", "label_policy", "cv_policy", "training_metadata", "model_metadata", "prediction_metadata"):
        item = payload.get(key)
        if not item:
            issues.append(
                MLAdmissionGateIssue(
                    code="ml_gate_required_evidence_missing",
                    message=f"{key} evidence is required for CR152 ML admission gate.",
                    source=key,
                    field=key,
                )
            )
            continue
        issues.extend(_issues_from_payload(key, item))

    label_policy = _as_mapping(payload.get("label_policy"))
    label_method = str(label_policy.get("label_method") or "").strip().lower()
    if label_method in {"triple_barrier", "meta_label"}:
        issues.append(
            MLAdmissionGateIssue(
                code="ml_label_method_not_implemented",
                message=f"{label_method} is reserved in CR152 first wave and must return BLOCKED when active.",
                source="label_policy",
                field="label_method",
            )
        )

    counters = _normalise_operation_counts(operation_counts or payload.get("operation_counts"))
    issues.extend(
        MLAdmissionGateIssue(
            code="ml_gate_forbidden_operation_nonzero",
            message=f"{key} counter must be zero.",
            source="operation_counts",
            field=key,
        )
        for key, value in counters.items()
        if value != 0
    )

    blocked = tuple(issue for issue in issues if _issue_status(issue) is MLAdmissionGateStatus.BLOCKED)
    failed = tuple(issue for issue in issues if _issue_status(issue) is MLAdmissionGateStatus.FAIL)
    review = tuple(issue for issue in issues if _issue_status(issue) is MLAdmissionGateStatus.NEEDS_REVIEW)
    status = (
        MLAdmissionGateStatus.BLOCKED
        if blocked
        else MLAdmissionGateStatus.FAIL
        if failed
        else MLAdmissionGateStatus.NEEDS_REVIEW
        if review
        else MLAdmissionGateStatus.PASS
    )
    refs = _evidence_refs(payload)
    return MLAdmissionGate(
        status=status,
        gate_present=True,
        gate_required=bool(gate_required),
        gate_ref=str(gate_ref or payload.get("gate_ref") or ""),
        blocked_reasons=tuple(dict.fromkeys((*blocked, *failed))),
        needs_review_reasons=review,
        evidence_refs=refs,
        operation_counts=counters,
    )


def ml_gate_summary(gate: MLAdmissionGate | Mapping[str, Any]) -> dict[str, Any]:
    payload = gate.to_dict() if isinstance(gate, MLAdmissionGate) else json_safe(dict(gate))
    status = str(payload.get("status") or payload.get("gate_status") or MLAdmissionGateStatus.BLOCKED.value)
    return {
        "schema_version": payload.get("schema_version") or ML_ADMISSION_GATE_SCHEMA,
        "gate_present": bool(payload.get("gate_present", True)),
        "gate_required": bool(payload.get("gate_required", True)),
        "gate_status": status,
        "status": status,
        "gate_ref": str(payload.get("gate_ref") or ""),
        "blocked_reasons": tuple(payload.get("blocked_reasons") or ()),
        "needs_review_reasons": tuple(payload.get("needs_review_reasons") or ()),
        "evidence_refs": tuple(str(item) for item in payload.get("evidence_refs") or () if str(item)),
        "operation_counts": _normalise_operation_counts(payload.get("operation_counts")),
    }


def _issues_from_payload(source: str, payload: Any) -> tuple[MLAdmissionGateIssue, ...]:
    data = _as_mapping(payload)
    issues: list[MLAdmissionGateIssue] = []
    raw_items = data.get("issues") or data.get("blocked_reasons") or ()
    if isinstance(raw_items, Mapping):
        raw_items = (raw_items,)
    for item in raw_items:
        issue_data = _as_mapping(item)
        code = str(issue_data.get("code") or "ml_gate_input_issue")
        issues.append(
            MLAdmissionGateIssue(
                code=code,
                message=str(issue_data.get("message") or code),
                source=str(issue_data.get("source") or source),
                field=str(issue_data.get("field") or ""),
                severity=str(issue_data.get("severity") or _severity_from_code(code)),
                evidence_ref=str(issue_data.get("evidence_ref") or ""),
            )
        )
    status = str(data.get("status") or "").upper()
    if status in {"FAIL", "FAILED"}:
        issues.append(MLAdmissionGateIssue(code="ml_gate_input_status_fail", message=f"{source} status is FAIL.", source=source, severity="fail"))
    elif status == "NEEDS_REVIEW":
        issues.append(MLAdmissionGateIssue(code="ml_gate_input_status_needs_review", message=f"{source} status needs review.", source=source, severity="review"))
    elif status == "BLOCKED":
        issues.append(MLAdmissionGateIssue(code="ml_gate_input_status_blocked", message=f"{source} status is BLOCKED.", source=source))
    return tuple(issues)


def _issue_status(issue: MLAdmissionGateIssue) -> MLAdmissionGateStatus:
    severity = issue.severity.lower()
    code = issue.code.lower()
    if severity in {"review", "needs_review"}:
        return MLAdmissionGateStatus.NEEDS_REVIEW
    if severity in {"fail", "failed"} or "overlap" in code or "threshold" in code:
        return MLAdmissionGateStatus.FAIL
    return MLAdmissionGateStatus.BLOCKED


def _severity_from_code(code: str) -> str:
    normalized = code.lower()
    if "needs_review" in normalized:
        return "review"
    if "overlap" in normalized or "threshold" in normalized or normalized.endswith("_fail"):
        return "fail"
    return "blocker"


def _evidence_refs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for value in payload.values():
        data = _as_mapping(value)
        for field_name in ("evidence_ref", "ref", "gate_ref"):
            ref = str(data.get(field_name) or "")
            if ref:
                refs.append(ref)
        refs.extend(str(item) for item in data.get("evidence_refs") or () if str(item))
    return tuple(dict.fromkeys(refs))


def _normalise_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in CR152_ML_FORBIDDEN_OPERATION_COUNTERS}


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, MLAdmissionGate):
        return value.to_dict()
    if isinstance(value, MLAdmissionGateIssue):
        return value.to_dict()
    if isinstance(value, Mapping):
        return json_safe(dict(value))
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        return json_safe(dict(converted)) if isinstance(converted, Mapping) else {}
    return {}


__all__ = [
    "ML_ADMISSION_GATE_SCHEMA",
    "CR152_ML_FORBIDDEN_OPERATION_COUNTERS",
    "MLAdmissionGate",
    "MLAdmissionGateIssue",
    "MLAdmissionGateStatus",
    "evaluate_ml_strategy_admission_gate",
    "ml_gate_summary",
]
