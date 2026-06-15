"""CR014 Explicit Publish Gate 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Mapping

from .catalog import (
    CatalogPointer,
    build_cr018_current_pointer_update_plan,
    build_cr018_publish_evidence_record,
    validate_catalog_pointer,
)
from .contracts import (
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
)
from .manifest import (
    ManifestCompletenessResult,
    ManifestRecord,
    validate_manifest_record,
)

PUBLISH_NOT_AUTHORIZED = "publish_not_authorized"
QUALITY_NOT_PUBLISHABLE = "quality_not_publishable"
READINESS_NOT_PUBLISHABLE = "readiness_not_publishable"
LIFECYCLE_DENOMINATOR_MISSING = "lifecycle_denominator_missing"
CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH = "catalog_pointer_incomplete"
REAL_PUBLISH_NOT_AUTHORIZED = "real_publish_not_authorized"
RELEASE_READINESS_AUDIT_INCOMPLETE = "release_readiness_audit_incomplete"
RELEASE_READINESS_NOT_PUBLISHABLE = "release_readiness_not_publishable"
RELEASE_PUBLISH_PERMISSION_COUNTER_VIOLATION = "release_publish_permission_counter_violation"
RELEASE_PUBLISH_AUDIT_REQUIRED_FIELDS: tuple[str, ...] = (
    "release",
    "dataset",
    "quality",
    "blocked_claims",
    "rollback_target",
    "evidence_refs",
)
RELEASE_PUBLISH_OPERATION_COUNTERS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "real_lake_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "catalog_current_pointer_publish": 0,
    "qmt_operation": 0,
    "duckdb_dependency_change": 0,
}
PUBLISH_BLOCKED_MISSING_APPROVAL = "publish_blocked_missing_approval"
PUBLISH_BLOCKED_P0_READINESS_FAILED = "publish_blocked_p0_readiness_failed"
PUBLISH_BLOCKED_INCOMPLETE_EVIDENCE = "publish_blocked_incomplete_evidence"
PUBLISH_BLOCKED_ROLLBACK_TARGET_MISSING = "publish_blocked_rollback_target_missing"
AUTO_PUBLISH_FORBIDDEN = "auto_publish_forbidden"
PUBLISH_DECISION_ALLOWED = "allowed"
PUBLISH_DECISION_BLOCKED = "blocked"
AUTO_PUBLISH_PRODUCERS: tuple[str, ...] = (
    "validate",
    "parity",
    "quality",
    "duckdb_audit",
)


@dataclass(frozen=True, slots=True)
class PublishIntent:
    """显式发布意图；approval_token 只校验存在，不在结果中回显。"""

    publish: bool = False
    approval_token: str | None = None
    approved_by: str | None = None
    reason: str | None = None

    @property
    def is_explicit(self) -> bool:
        return self.publish and bool(str(self.approval_token or "").strip())


@dataclass(frozen=True, slots=True)
class PublishGateResult:
    publish_allowed: bool
    pointer_changes: int
    manifest_complete: bool
    catalog_pointer_complete: bool
    quality_status: str
    readiness_status: str
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PointerUpdateResult:
    publish_allowed: bool
    dry_run: bool
    pointer_changes: int
    catalog_writes: int
    real_lake_writes: int
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReleasePublishAuditHookResult:
    publish_allowed: bool
    production_publish_allowed_count: int
    current_pointer_publish_allowed: bool
    current_pointer_publish_count: int
    real_lake_write_count: int
    audit_report_complete: bool
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()
    operation_counts: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operation_counts"] = dict(self.operation_counts or RELEASE_PUBLISH_OPERATION_COUNTERS)
        return payload


@dataclass(frozen=True, slots=True)
class ReleasePublishRequest:
    """CR018 release-level explicit publish 输入；approval_id 只表达审批记录。"""

    release_id: str
    readiness_report: Mapping[str, Any] | Any
    approval_id: str | None = None
    rollback_target: Mapping[str, Any] | str | None = None
    approved_by: str | None = None
    approved_at: str | None = None
    operator: str | None = None
    dataset_details: tuple[dict[str, Any], ...] = ()
    evidence_refs: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ReleasePublishDecision:
    release_id: str
    status: str
    allowed: bool
    approval_id_present: bool
    production_publish_allowed_count: int
    current_pointer_update_plan: dict[str, Any] = field(default_factory=dict)
    publish_evidence: dict[str, Any] = field(default_factory=dict)
    blocked_reasons: tuple[dict[str, Any], ...] = ()
    auto_publish_count: int = 0
    operation_counts: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.release_id,
            "status": self.status,
            "allowed": self.allowed,
            "approval_id_present": self.approval_id_present,
            "production_publish_allowed_count": self.production_publish_allowed_count,
            "current_pointer_update_plan": dict(self.current_pointer_update_plan or {}),
            "publish_evidence": dict(self.publish_evidence or {}),
            "blocked_reasons": [dict(item) for item in self.blocked_reasons],
            "auto_publish_count": self.auto_publish_count,
            "operation_counts": dict(self.operation_counts or RELEASE_PUBLISH_OPERATION_COUNTERS),
        }


@dataclass(frozen=True, slots=True)
class AutoPublishGuardResult:
    producer_kind: str
    producer_status: str
    auto_publish_allowed: bool = False
    auto_publish_count: int = 0
    reason_code: str = AUTO_PUBLISH_FORBIDDEN
    operation_counts: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "producer_kind": self.producer_kind,
            "producer_status": self.producer_status,
            "auto_publish_allowed": self.auto_publish_allowed,
            "auto_publish_count": self.auto_publish_count,
            "reason_code": self.reason_code,
            "operation_counts": dict(self.operation_counts or RELEASE_PUBLISH_OPERATION_COUNTERS),
        }


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, CatalogPointer):
        return value.to_dict()
    if isinstance(value, ManifestRecord):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"不支持的 publish gate 输入类型: {type(value)!r}")


def _manifest_result(
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None,
) -> ManifestCompletenessResult:
    if isinstance(manifest, ManifestCompletenessResult):
        return manifest
    if manifest is None:
        return ManifestCompletenessResult(
            passed=False,
            publish_allowed=False,
            missing_fields=("manifest",),
            error_codes=("manifest_incomplete",),
            details=({"code": "manifest_incomplete", "missing_fields": ["manifest"]},),
        )
    return validate_manifest_record(manifest)


def _value_from_inputs(field: str, *payloads: Mapping[str, Any]) -> Any:
    for payload in payloads:
        value = payload.get(field)
        if value is not None:
            return value
    return None


def _has_lifecycle_denominator(
    lifecycle: Mapping[str, Any],
    candidate: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> bool:
    denominator = _value_from_inputs("coverage_denominator", lifecycle, candidate)
    denominator_ref = _value_from_inputs("lifecycle_denominator_ref", lifecycle, manifest)
    if denominator is not None and not isinstance(denominator, bool):
        if isinstance(denominator, int) and denominator >= 0:
            return True
    return bool(str(denominator_ref or "").strip())


def validate_release_publish_readiness_audit(
    readiness_report: Mapping[str, Any] | Any,
) -> ReleasePublishAuditHookResult:
    """publish 前 release readiness audit hook；只返回 dry-run 合同，不写 current pointer。"""

    payload = _as_mapping(readiness_report)
    missing_fields = tuple(field for field in RELEASE_PUBLISH_AUDIT_REQUIRED_FIELDS if field not in payload)
    counters = _normalise_release_publish_counters(payload.get("operation_counts"))
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []

    if missing_fields:
        error_codes.append(RELEASE_READINESS_AUDIT_INCOMPLETE)
        details.append({"code": RELEASE_READINESS_AUDIT_INCOMPLETE, "missing_fields": list(missing_fields)})

    report_allowed = bool(payload.get("publish_allowed")) and int(payload.get("production_publish_allowed_count") or 0) > 0
    if not report_allowed:
        error_codes.append(RELEASE_READINESS_NOT_PUBLISHABLE)
        details.append(
            {
                "code": RELEASE_READINESS_NOT_PUBLISHABLE,
                "blocked_claims": list(payload.get("blocked_claims") or ()),
                "blocked_reasons": list(payload.get("blocked_reasons") or ()),
            }
        )

    if any(value != 0 for value in counters.values()):
        error_codes.append(RELEASE_PUBLISH_PERMISSION_COUNTER_VIOLATION)
        details.append(
            {
                "code": RELEASE_PUBLISH_PERMISSION_COUNTER_VIOLATION,
                "operation_counts": dict(counters),
            }
        )

    allowed = not error_codes
    return ReleasePublishAuditHookResult(
        publish_allowed=allowed,
        production_publish_allowed_count=1 if allowed else 0,
        current_pointer_publish_allowed=False,
        current_pointer_publish_count=0,
        real_lake_write_count=0,
        audit_report_complete=not missing_fields,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
        operation_counts=counters,
    )


def explicit_publish_gate(
    request: ReleasePublishRequest | Mapping[str, Any],
) -> ReleasePublishDecision:
    """CR018 release-level Explicit Publish Gate；只生成 dry-run 决策和计划。"""

    publish_request = _normalise_release_publish_request(request)
    report_payload = _as_mapping(publish_request.readiness_report)
    hook = validate_release_publish_readiness_audit(report_payload)
    counters = _normalise_release_publish_counters(report_payload.get("operation_counts"))
    rollback_target = _release_rollback_target(publish_request.rollback_target, report_payload)
    blocked_reasons: list[dict[str, Any]] = []

    if not _release_non_empty(publish_request.approval_id):
        blocked_reasons.append(
            {
                "reason_code": PUBLISH_BLOCKED_MISSING_APPROVAL,
                "field": "approval_id",
                "release_id": publish_request.release_id,
            }
        )
    if not _release_rollback_target_complete(rollback_target):
        blocked_reasons.append(
            {
                "reason_code": PUBLISH_BLOCKED_ROLLBACK_TARGET_MISSING,
                "field": "rollback_target",
                "release_id": publish_request.release_id,
            }
        )
    if _release_incomplete_evidence(report_payload, hook):
        blocked_reasons.append(
            {
                "reason_code": PUBLISH_BLOCKED_INCOMPLETE_EVIDENCE,
                "field": "release_evidence",
                "missing_evidence_refs": list(report_payload.get("missing_evidence_refs") or ()),
                "release_id": publish_request.release_id,
            }
        )
    if _release_p0_or_quality_failed(report_payload):
        blocked_reasons.append(
            {
                "reason_code": PUBLISH_BLOCKED_P0_READINESS_FAILED,
                "field": "readiness_report",
                "release_id": publish_request.release_id,
            }
        )
    if any(value != 0 for value in counters.values()):
        blocked_reasons.append(
            {
                "reason_code": RELEASE_PUBLISH_PERMISSION_COUNTER_VIOLATION,
                "field": "operation_counts",
                "operation_counts": dict(counters),
                "release_id": publish_request.release_id,
            }
        )
    if not hook.publish_allowed and not blocked_reasons:
        blocked_reasons.append(
            {
                "reason_code": RELEASE_READINESS_NOT_PUBLISHABLE,
                "field": "readiness_report",
                "error_codes": list(hook.error_codes),
                "release_id": publish_request.release_id,
            }
        )

    reasons = tuple(_dedupe_release_publish_reasons(blocked_reasons))
    if reasons:
        return ReleasePublishDecision(
            release_id=publish_request.release_id,
            status=PUBLISH_DECISION_BLOCKED,
            allowed=False,
            approval_id_present=_release_non_empty(publish_request.approval_id),
            production_publish_allowed_count=0,
            blocked_reasons=reasons,
            operation_counts=counters,
        )

    dataset_details = publish_request.dataset_details or _release_dataset_details(report_payload)
    release_summary = dict(report_payload.get("release") or {"release_id": publish_request.release_id})
    approval = {
        "approval_id": str(publish_request.approval_id or ""),
        "approved_by": str(publish_request.approved_by or ""),
        "approved_at": str(publish_request.approved_at or ""),
        "operator": str(publish_request.operator or ""),
    }
    plan = build_cr018_current_pointer_update_plan(
        publish_request.release_id,
        dataset_details,
        rollback_target=rollback_target,
        permission_counters=counters,
    ).to_dict()
    evidence = build_cr018_publish_evidence_record(
        publish_request.release_id,
        release_summary=release_summary,
        dataset_details=dataset_details,
        quality_digest=dict(report_payload.get("quality") or {}),
        readiness_digest={
            "required_missing": list(report_payload.get("required_missing") or ()),
            "p0_failures": list(report_payload.get("p0_failures") or ()),
            "blocked_reasons": list(report_payload.get("blocked_reasons") or ()),
        },
        rollback_target=rollback_target,
        approval=approval,
        permission_counters=counters,
    ).to_dict()
    return ReleasePublishDecision(
        release_id=publish_request.release_id,
        status=PUBLISH_DECISION_ALLOWED,
        allowed=True,
        approval_id_present=True,
        production_publish_allowed_count=1,
        current_pointer_update_plan=plan,
        publish_evidence=evidence,
        operation_counts=counters,
    )


def forbid_auto_publish_guard(
    producer_kind: str,
    producer_status: str = "pass",
    *,
    permission_counters: Mapping[str, Any] | None = None,
) -> AutoPublishGuardResult:
    """Validate / parity / quality / DuckDB audit PASS 不得自动 publish。"""

    return AutoPublishGuardResult(
        producer_kind=str(producer_kind or "").strip().lower(),
        producer_status=str(producer_status or ""),
        auto_publish_allowed=False,
        auto_publish_count=0,
        reason_code=AUTO_PUBLISH_FORBIDDEN,
        operation_counts=_normalise_release_publish_counters(permission_counters),
    )


def _normalise_release_publish_counters(counters: Any) -> dict[str, int]:
    normalised = dict(RELEASE_PUBLISH_OPERATION_COUNTERS)
    if isinstance(counters, Mapping):
        for key, value in counters.items():
            try:
                normalised[str(key)] = int(value)
            except (TypeError, ValueError):
                normalised[str(key)] = 1
    return normalised


def _normalise_release_publish_request(
    request: ReleasePublishRequest | Mapping[str, Any],
) -> ReleasePublishRequest:
    if isinstance(request, ReleasePublishRequest):
        return request
    payload = dict(request)
    dataset_details = payload.get("dataset_details") or payload.get("dataset") or ()
    if isinstance(dataset_details, Mapping):
        dataset_tuple = tuple(dict(item) for item in dataset_details.values() if isinstance(item, Mapping))
    else:
        dataset_tuple = tuple(dict(item) for item in dataset_details if isinstance(item, Mapping))
    return ReleasePublishRequest(
        release_id=str(payload.get("release_id") or ""),
        readiness_report=payload.get("readiness_report") or payload,
        approval_id=payload.get("approval_id"),
        rollback_target=payload.get("rollback_target"),
        approved_by=payload.get("approved_by"),
        approved_at=payload.get("approved_at"),
        operator=payload.get("operator"),
        dataset_details=dataset_tuple,
        evidence_refs=payload.get("evidence_refs") if isinstance(payload.get("evidence_refs"), Mapping) else None,
    )


def _release_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _release_rollback_target(
    request_target: Mapping[str, Any] | str | None,
    report_payload: Mapping[str, Any],
) -> dict[str, Any]:
    value = request_target if request_target is not None else report_payload.get("rollback_target")
    if isinstance(value, Mapping):
        return dict(value)
    if _release_non_empty(value):
        return {"scope": "release", "target_release_id": str(value)}
    return {}


def _release_rollback_target_complete(target: Mapping[str, Any]) -> bool:
    scope = str(target.get("scope") or "release")
    target_release = (
        target.get("target_release_id")
        or target.get("to_release")
        or target.get("previous_release_id")
        or target.get("rollback_target")
    )
    return scope == "release" and _release_non_empty(target_release)


def _release_incomplete_evidence(
    report_payload: Mapping[str, Any],
    hook: ReleasePublishAuditHookResult,
) -> bool:
    if not hook.audit_report_complete or RELEASE_READINESS_AUDIT_INCOMPLETE in hook.error_codes:
        return True
    if report_payload.get("missing_evidence_refs"):
        return True
    for reason in report_payload.get("blocked_reasons") or ():
        if not isinstance(reason, Mapping):
            continue
        if str(reason.get("reason_code") or "") == "audit_evidence_incomplete":
            return True
    return False


def _release_p0_or_quality_failed(report_payload: Mapping[str, Any]) -> bool:
    if report_payload.get("p0_failures") or report_payload.get("quality_failures"):
        return True
    for reason in report_payload.get("blocked_reasons") or ():
        if not isinstance(reason, Mapping):
            continue
        if str(reason.get("reason_code") or "") in {
            "p0_readiness_failed",
            "quality_failed",
            "required_missing",
        }:
            return True
    return False


def _release_dataset_details(report_payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = report_payload.get("dataset") or ()
    return tuple(dict(item) for item in rows if isinstance(item, Mapping))


def _dedupe_release_publish_reasons(
    reasons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    output: list[dict[str, Any]] = []
    for reason in reasons:
        key = (str(reason.get("reason_code") or ""), str(reason.get("field") or ""))
        if key in seen:
            continue
        seen.add(key)
        output.append(reason)
    return output


def validate_publish_candidate(
    candidate: CatalogPointer | Mapping[str, Any],
    quality: Mapping[str, Any] | None = None,
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None = None,
    lifecycle: Mapping[str, Any] | None = None,
    intent: PublishIntent | None = None,
) -> PublishGateResult:
    """校验发布候选；Validate / parity PASS 不会隐式更新 pointer。"""

    candidate_payload = _as_mapping(candidate)
    quality_payload = dict(quality or {})
    lifecycle_payload = dict(lifecycle or {})
    manifest_check = _manifest_result(manifest)
    manifest_payload = _as_mapping(manifest) if manifest is not None and not isinstance(manifest, ManifestCompletenessResult) else {}
    pointer_check = validate_catalog_pointer(candidate_payload)

    quality_status = str(
        _value_from_inputs("quality_status", quality_payload, candidate_payload, manifest_payload)
        or ""
    )
    readiness_status = str(
        _value_from_inputs("readiness_status", quality_payload, candidate_payload, manifest_payload)
        or ""
    )
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []

    if not pointer_check.passed:
        error_codes.append(CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH)
        details.extend(pointer_check.details)
    if not manifest_check.passed:
        error_codes.extend(manifest_check.error_codes)
        details.extend(manifest_check.details)
    if quality_status != QUALITY_STATUS_PASS:
        error_codes.append(QUALITY_NOT_PUBLISHABLE)
        details.append({"code": QUALITY_NOT_PUBLISHABLE, "quality_status": quality_status or "missing"})
    if readiness_status != READINESS_STATUS_AVAILABLE:
        error_codes.append(READINESS_NOT_PUBLISHABLE)
        details.append(
            {
                "code": READINESS_NOT_PUBLISHABLE,
                "readiness_status": readiness_status or "missing",
            }
        )
    if not _has_lifecycle_denominator(lifecycle_payload, candidate_payload, manifest_payload):
        error_codes.append(LIFECYCLE_DENOMINATOR_MISSING)
        details.append({"code": LIFECYCLE_DENOMINATOR_MISSING})
    if intent is None or not intent.is_explicit:
        error_codes.append(PUBLISH_NOT_AUTHORIZED)
        details.append({"code": PUBLISH_NOT_AUTHORIZED})

    unique_codes = tuple(dict.fromkeys(error_codes))
    publish_allowed = not unique_codes
    return PublishGateResult(
        publish_allowed=publish_allowed,
        pointer_changes=1 if publish_allowed else 0,
        manifest_complete=manifest_check.passed,
        catalog_pointer_complete=pointer_check.passed,
        quality_status=quality_status,
        readiness_status=readiness_status,
        error_codes=unique_codes,
        details=tuple(details),
    )


def publish_current_pointer(
    store: object,
    candidate: CatalogPointer | Mapping[str, Any],
    intent: PublishIntent,
    *,
    dry_run: bool = True,
    quality: Mapping[str, Any] | None = None,
    manifest: ManifestRecord | Mapping[str, Any] | ManifestCompletenessResult | None = None,
    lifecycle: Mapping[str, Any] | None = None,
) -> PointerUpdateResult:
    """返回 current pointer 更新合同结果；默认 dry-run 且不写 catalog。"""

    del store
    gate = validate_publish_candidate(
        candidate,
        quality=quality,
        manifest=manifest,
        lifecycle=lifecycle,
        intent=intent,
    )
    if not gate.publish_allowed:
        return PointerUpdateResult(
            publish_allowed=False,
            dry_run=dry_run,
            pointer_changes=0,
            catalog_writes=0,
            real_lake_writes=0,
            error_codes=gate.error_codes,
            details=gate.details,
        )
    if dry_run:
        return PointerUpdateResult(
            publish_allowed=True,
            dry_run=True,
            pointer_changes=1,
            catalog_writes=0,
            real_lake_writes=0,
            details=({"code": "dry_run_only", "catalog_current_pointer_publish": 0},),
        )
    return PointerUpdateResult(
        publish_allowed=False,
        dry_run=False,
        pointer_changes=0,
        catalog_writes=0,
        real_lake_writes=0,
        error_codes=(REAL_PUBLISH_NOT_AUTHORIZED,),
        details=(
            {
                "code": REAL_PUBLISH_NOT_AUTHORIZED,
                "reason": "当前 Story 只授权 explicit publish gate dry-run 合同，不执行真实 current pointer 写入",
            },
        ),
    )


__all__ = [
    "CATALOG_POINTER_INCOMPLETE_FOR_PUBLISH",
    "LIFECYCLE_DENOMINATOR_MISSING",
    "PUBLISH_NOT_AUTHORIZED",
    "PUBLISH_BLOCKED_INCOMPLETE_EVIDENCE",
    "PUBLISH_BLOCKED_MISSING_APPROVAL",
    "PUBLISH_BLOCKED_P0_READINESS_FAILED",
    "PUBLISH_BLOCKED_ROLLBACK_TARGET_MISSING",
    "PUBLISH_DECISION_ALLOWED",
    "PUBLISH_DECISION_BLOCKED",
    "QUALITY_NOT_PUBLISHABLE",
    "READINESS_NOT_PUBLISHABLE",
    "REAL_PUBLISH_NOT_AUTHORIZED",
    "AUTO_PUBLISH_FORBIDDEN",
    "AUTO_PUBLISH_PRODUCERS",
    "RELEASE_PUBLISH_AUDIT_REQUIRED_FIELDS",
    "RELEASE_PUBLISH_OPERATION_COUNTERS",
    "RELEASE_PUBLISH_PERMISSION_COUNTER_VIOLATION",
    "RELEASE_READINESS_AUDIT_INCOMPLETE",
    "RELEASE_READINESS_NOT_PUBLISHABLE",
    "AutoPublishGuardResult",
    "PointerUpdateResult",
    "PublishGateResult",
    "PublishIntent",
    "ReleasePublishDecision",
    "ReleasePublishRequest",
    "ReleasePublishAuditHookResult",
    "explicit_publish_gate",
    "forbid_auto_publish_guard",
    "publish_current_pointer",
    "validate_release_publish_readiness_audit",
    "validate_publish_candidate",
]
