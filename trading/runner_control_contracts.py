"""CR138 Runner 控制面共享合同。

本模块只定义本地 fixture / contract 对象，不读取凭据、不连接 QMT、
不启动 gateway、不访问 NAS / provider / lake / catalog / Git remote。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence


RUNNER_CONTROL_SCHEMA_VERSION = "cr138-runner-control-contracts-v1"

FORBIDDEN_OPERATION_COUNTER_FIELDS: tuple[str, ...] = (
    "runtime_start",
    "gateway_start",
    "port_bind",
    "credential_read",
    "qmt_operation",
    "xtquant_import",
    "account_query",
    "market_query",
    "order_query",
    "order_submit",
    "order_cancel",
    "simulation_run",
    "live_run",
    "nas_access",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "git_remote_write",
    "adapter_calls",
)


class AuthorizationStatus(str, Enum):
    MISSING = "missing"
    AUTHORIZED = "authorized"
    EXPIRED = "expired"
    DENIED = "denied"


class ControlResultStatus(str, Enum):
    ACCEPTED = "accepted"
    PASS = "pass"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class RunnerCommandType(str, Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    MANUAL_TAKEOVER = "manual_takeover"
    DRY_RUN_REVIEW = "dry_run_review"


class RunStateValue(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    DEGRADED = "degraded"
    PAUSED = "paused"
    MANUAL_TAKEOVER = "manual_takeover"
    BLOCKED = "blocked"
    COMPLETED_LOCAL = "completed_local"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class NoRealOperationCounters:
    runtime_start: int = 0
    gateway_start: int = 0
    port_bind: int = 0
    credential_read: int = 0
    qmt_operation: int = 0
    xtquant_import: int = 0
    account_query: int = 0
    market_query: int = 0
    order_query: int = 0
    order_submit: int = 0
    order_cancel: int = 0
    simulation_run: int = 0
    live_run: int = 0
    nas_access: int = 0
    provider_fetch: int = 0
    lake_write: int = 0
    catalog_publish: int = 0
    git_remote_write: int = 0
    adapter_calls: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            key: int(getattr(self, key))
            for key in FORBIDDEN_OPERATION_COUNTER_FIELDS
        }


@dataclass(frozen=True, slots=True)
class AuthorizationRecord:
    scope: str
    status: AuthorizationStatus | str = AuthorizationStatus.MISSING
    authorization_ref: str = ""
    expires_at: str = ""
    redaction_status: str = "redacted"
    allowed_actions: tuple[str, ...] = ()
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    @property
    def authorized(self) -> bool:
        return _enum_value(self.status) == AuthorizationStatus.AUTHORIZED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope,
            "status": _enum_value(self.status),
            "authorization_ref": self.authorization_ref,
            "expires_at": self.expires_at,
            "redaction_status": self.redaction_status,
            "allowed_actions": list(self.allowed_actions),
        }


@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id: str
    request_id: str
    actor: str
    action: str
    scope: str
    result: str
    created_at: str = field(default_factory=_utc_now)
    redaction_status: str = "redacted"
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "request_id": self.request_id,
            "actor": self.actor,
            "action": self.action,
            "scope": self.scope,
            "result": self.result,
            "created_at": self.created_at,
            "redaction_status": self.redaction_status,
        }


@dataclass(frozen=True, slots=True)
class BlockedResult:
    status: ControlResultStatus | str
    blocked_reason: str
    scope_required: str = ""
    audit_id: str = ""
    request_id: str = ""
    adapter_calls: int = 0
    counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return _enum_value(self.status) in {
            ControlResultStatus.BLOCKED.value,
            ControlResultStatus.REJECTED.value,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": _enum_value(self.status),
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "scope_required": self.scope_required,
            "audit_id": self.audit_id,
            "request_id": self.request_id,
            "adapter_calls": self.adapter_calls,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class RunPlan:
    run_id: str
    strategy_id: str
    target_date: str
    strategy_version: str = ""
    data_release_ref: str = ""
    mode_request: str = "dry_run_review"
    authorization_ref: str = ""
    request_id: str = ""
    audit_id: str = ""
    status: str = "planned"
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return _dataclass_dict(self)


@dataclass(frozen=True, slots=True)
class RunPlanBatch:
    batch_id: str
    plans: tuple[RunPlan, ...]
    batch_policy: str = "fail_closed"
    aggregate_status: str = "planned"
    local_registry_ref: str = ""
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "plans": [plan.to_dict() for plan in self.plans],
            "batch_policy": self.batch_policy,
            "aggregate_status": self.aggregate_status,
            "local_registry_ref": self.local_registry_ref,
        }


@dataclass(frozen=True, slots=True)
class PreflightResult:
    run_id: str
    status: ControlResultStatus | str
    blocked_reasons: tuple[str, ...] = ()
    gateway_health_ref: str = ""
    auth_status: str = "missing"
    audit_id: str = ""
    adapter_calls: int = 0
    counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return _enum_value(self.status) == ControlResultStatus.PASS.value

    @property
    def blocked(self) -> bool:
        return _enum_value(self.status) == ControlResultStatus.BLOCKED.value

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": _enum_value(self.status),
            "passed": self.passed,
            "blocked": self.blocked,
            "blocked_reasons": list(self.blocked_reasons),
            "gateway_health_ref": self.gateway_health_ref,
            "auth_status": self.auth_status,
            "audit_id": self.audit_id,
            "adapter_calls": self.adapter_calls,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class BatchPreflightResult:
    batch_id: str
    per_run_results: tuple[PreflightResult, ...]
    aggregate_status: str
    aggregate_blocked_reasons: tuple[str, ...] = ()
    adapter_calls: int = 0
    counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "per_run_results": [result.to_dict() for result in self.per_run_results],
            "aggregate_status": self.aggregate_status,
            "aggregate_blocked_reasons": list(self.aggregate_blocked_reasons),
            "adapter_calls": self.adapter_calls,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class RunnerCommand:
    command_id: str
    run_id: str
    command_type: RunnerCommandType | str
    idempotency_key: str
    request_id: str = ""
    audit_id: str = ""
    scope_required: str = "runner:control"
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "run_id": self.run_id,
            "command_type": _enum_value(self.command_type),
            "idempotency_key": self.idempotency_key,
            "request_id": self.request_id,
            "audit_id": self.audit_id,
            "scope_required": self.scope_required,
        }


@dataclass(frozen=True, slots=True)
class RunnerCommandResult:
    command_id: str
    run_id: str
    status: ControlResultStatus | str
    blocked_reason: str = ""
    audit_id: str = ""
    duplicate_of: str = ""
    adapter_calls: int = 0
    counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "run_id": self.run_id,
            "status": _enum_value(self.status),
            "blocked_reason": self.blocked_reason,
            "audit_id": self.audit_id,
            "duplicate_of": self.duplicate_of,
            "adapter_calls": self.adapter_calls,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class SignalEvent:
    event_id: str
    run_id: str
    payload_ref: str
    idempotency_key: str = ""
    audit_id: str = ""
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return _dataclass_dict(self)


@dataclass(frozen=True, slots=True)
class OrderIntentDraft:
    intent_id: str
    run_id: str
    side: str
    qty_policy: str
    symbol_ref: str
    blocked_reason: str = ""
    submit_allowed: bool = False
    cancel_allowed: bool = False
    broker_order_ref: str = ""
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return _dataclass_dict(self)


@dataclass(frozen=True, slots=True)
class RebalancePlan:
    run_id: str
    status: str
    target_summary: str
    current_summary_ref: str
    risk_status: str
    order_intent_drafts: tuple[OrderIntentDraft, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    audit_id: str = ""
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "target_summary": self.target_summary,
            "current_summary_ref": self.current_summary_ref,
            "risk_status": self.risk_status,
            "order_intent_drafts": [draft.to_dict() for draft in self.order_intent_drafts],
            "blocked_reasons": list(self.blocked_reasons),
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True, slots=True)
class RunState:
    run_id: str
    state: RunStateValue | str
    gateway_status: str = ""
    latest_report_state: str = ""
    blocked_reasons: tuple[str, ...] = ()
    incident_refs: tuple[str, ...] = ()
    audit_id: str = ""
    last_event_at: str = field(default_factory=_utc_now)
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": _enum_value(self.state),
            "gateway_status": self.gateway_status,
            "latest_report_state": self.latest_report_state,
            "blocked_reasons": list(self.blocked_reasons),
            "incident_refs": list(self.incident_refs),
            "audit_id": self.audit_id,
            "last_event_at": self.last_event_at,
        }


@dataclass(frozen=True, slots=True)
class OpsSummary:
    run_id: str
    state: str
    gateway_status: str
    latest_report_state: str
    blocked_reasons: tuple[str, ...]
    next_manual_action: str
    no_real_operation_counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": self.state,
            "gateway_status": self.gateway_status,
            "latest_report_state": self.latest_report_state,
            "blocked_reasons": list(self.blocked_reasons),
            "next_manual_action": self.next_manual_action,
            "no_real_operation_counters": dict(self.no_real_operation_counters),
        }


@dataclass(frozen=True, slots=True)
class BatchOpsSummary:
    batch_id: str
    run_count: int
    status_counts: Mapping[str, int]
    blocked_run_refs: tuple[str, ...] = ()
    latest_local_registry_ref: str = ""
    no_real_operation_counters: Mapping[str, int] = field(default_factory=lambda: collect_no_real_operation_counters())
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "batch_id": self.batch_id,
            "run_count": self.run_count,
            "status_counts": dict(self.status_counts),
            "blocked_run_refs": list(self.blocked_run_refs),
            "latest_local_registry_ref": self.latest_local_registry_ref,
            "no_real_operation_counters": dict(self.no_real_operation_counters),
        }


@dataclass(frozen=True, slots=True)
class RunEvidence:
    run_id: str
    evidence_refs: tuple[str, ...]
    audit_ids: tuple[str, ...]
    redaction_status: str = "redacted"
    status: str = "indexed"
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "evidence_refs": list(self.evidence_refs),
            "audit_ids": list(self.audit_ids),
            "redaction_status": self.redaction_status,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ReviewSummary:
    run_id: str
    period: str
    metrics_summary: Mapping[str, object]
    incidents: tuple[str, ...] = ()
    follow_up_candidates: tuple[str, ...] = ()
    redaction_status: str = "redacted"
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "period": self.period,
            "metrics_summary": dict(self.metrics_summary),
            "incidents": list(self.incidents),
            "follow_up_candidates": list(self.follow_up_candidates),
            "redaction_status": self.redaction_status,
        }


@dataclass(frozen=True, slots=True)
class IncidentRecord:
    incident_id: str
    run_id: str
    severity: str
    state: str
    recovery_plan_ref: str
    audit_id: str = ""
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return _dataclass_dict(self)


@dataclass(frozen=True, slots=True)
class StrategyChangePlan:
    change_id: str
    change_type: str
    diff_ref: str
    rollback_target: str
    status: str
    blocked_reason: str = ""
    apply_allowed: bool = False
    schema_version: str = RUNNER_CONTROL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return _dataclass_dict(self)


def collect_no_real_operation_counters(
    counters: Mapping[str, int] | NoRealOperationCounters | None = None,
) -> dict[str, int]:
    normalized = NoRealOperationCounters().to_dict()
    if counters is None:
        return normalized
    raw = counters.to_dict() if isinstance(counters, NoRealOperationCounters) else dict(counters)
    for key, value in raw.items():
        normalized[str(key)] = int(value)
    return normalized


def require_scope(
    scope: str,
    authorization: AuthorizationRecord | Mapping[str, object] | None,
    *,
    request_id: str = "",
    audit_id: str = "",
) -> BlockedResult | None:
    current = build_authorization_record(authorization, scope=scope)
    if current.authorized and current.scope == scope:
        return None
    reason = "authorization_missing" if current.status == AuthorizationStatus.MISSING else "scope_denied"
    return BlockedResult(
        status=ControlResultStatus.BLOCKED,
        blocked_reason=reason,
        scope_required=scope,
        request_id=request_id,
        audit_id=audit_id,
        adapter_calls=0,
        counters=collect_no_real_operation_counters(),
    )


def build_authorization_record(
    source: AuthorizationRecord | Mapping[str, object] | None,
    *,
    scope: str,
) -> AuthorizationRecord:
    if isinstance(source, AuthorizationRecord):
        return source
    raw = dict(source or {})
    return AuthorizationRecord(
        scope=str(raw.get("scope") or scope),
        status=str(raw.get("status") or AuthorizationStatus.MISSING.value),
        authorization_ref=str(raw.get("authorization_ref") or ""),
        expires_at=str(raw.get("expires_at") or ""),
        redaction_status=str(raw.get("redaction_status") or "redacted"),
        allowed_actions=tuple(str(item) for item in raw.get("allowed_actions") or ()),
    )


def new_audit_record(
    *,
    actor: str,
    action: str,
    scope: str,
    result: str,
    request_id: str = "",
) -> AuditRecord:
    current_request = request_id or stable_id("request", actor, action, scope)
    audit_id = stable_id("audit", current_request, actor, action, scope, result)
    return AuditRecord(
        audit_id=audit_id,
        request_id=current_request,
        actor=actor,
        action=action,
        scope=scope,
        result=result,
    )


def validate_contract_ids(payload: object) -> BlockedResult | None:
    request_id = _object_value(payload, "request_id")
    audit_id = _object_value(payload, "audit_id")
    if request_id or audit_id:
        return None
    return BlockedResult(
        status=ControlResultStatus.REJECTED,
        blocked_reason="missing_audit_identity",
        adapter_calls=0,
    )


def stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps([str(part) for part in parts], sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest[:16]}"


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _object_value(payload: object, key: str) -> str:
    if isinstance(payload, Mapping):
        return str(payload.get(key) or "")
    return str(getattr(payload, key, "") or "")


def _dataclass_dict(instance: object) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key in getattr(instance, "__dataclass_fields__", {}):
        value = getattr(instance, key)
        if isinstance(value, Enum):
            payload[key] = value.value
        elif isinstance(value, Sequence) and not isinstance(value, str):
            payload[key] = list(value)
        else:
            payload[key] = value
    return payload
