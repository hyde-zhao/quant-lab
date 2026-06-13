"""CR019-S04 的 Windows QMT gateway lifecycle 离线合同。

本模块只生成命令结构、生命周期计划和 heartbeat 摘要，不启动服务、
不绑定端口、不打开网络连接、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol

from trading.qmt_auth import QmtAuthAdmissionDecision
from trading.qmt_endpoint_matrix import (
    get_cr020_query_positions_spec,
    is_cr020_readonly_endpoint_allowed,
)
from trading.qmt_gateway_config import (
    CR020_GATEWAY_RUNTIME_SCHEMA_VERSION,
    GatewayConfig,
    GatewayConfigValidation,
    GatewayRuntimeFlags,
    build_gateway_config,
    build_gateway_runtime_flags,
    collect_gateway_runtime_counters,
    collect_gateway_safety_counters,
    validate_gateway_security,
)
from trading.qmt_gateway_contracts import (
    CR020_QUERY_POSITIONS_ENDPOINT_ID,
    CR020_QUERY_POSITIONS_SCOPE,
    QmtBlockedReason,
    QmtGatewayResult,
    QmtQueryPositionsRequest,
    build_query_positions_blocked_result,
    build_query_positions_request,
    build_query_positions_success_result,
    collect_query_positions_safety_counters,
    redact_query_positions_payload,
)
from trading.qmt_gateway_session import (
    QmtSessionBlockedReason,
    QmtSessionSnapshot,
    require_qmt_session_ready,
)
from trading.qmt_redaction import scan_qmt_auth_redaction_leaks


GATEWAY_SERVICE_SCHEMA_VERSION = "cr019-s04-gateway-service-v1"
GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION = CR020_GATEWAY_RUNTIME_SCHEMA_VERSION
HEARTBEAT_FAILED_REASON = "heartbeat_failed"
SERVICE_START_FORBIDDEN_REASON = "service_start_forbidden"
IMPLEMENTATION_NOT_ALLOWED_REASON = "implementation_not_allowed"
DEPENDENCY_CHANGE_NOT_ALLOWED_REASON = "dependency_change_not_allowed"
PORT_BIND_FORBIDDEN_REASON = "port_bind_forbidden"
CREDENTIAL_READ_FORBIDDEN_REASON = "credential_read_forbidden"
QMT_CALL_FORBIDDEN_REASON = "qmt_call_forbidden"
RUNTIME_AUTHORIZATION_MISSING_REASON = "runtime_authorization_missing"
CONFIG_VALIDATION_BLOCKED_REASON = "config_validation_blocked"
ADAPTER_UNAVAILABLE_REASON = "adapter_unavailable"
ADAPTER_ERROR_REASON = "adapter_error"
TRANSPORT_TIMEOUT_REASON = "transport_timeout"

_START_TRANSITIONS = frozenset({"start", "serve", "run", "launch", "bind"})


class GatewayLifecycleState(str, Enum):
    """S04 lifecycle 合同状态；当前实现不进入真实 running。"""

    CONFIGURED = "configured"
    BLOCKED_CONFIG = "blocked_config"
    READY_TO_START = "ready_to_start"
    RUNNING_OBSERVED = "running_observed"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"


class GatewayRuntimeAdmissionStatus(str, Enum):
    """CR020 runtime admission 状态；不表示服务已真实运行。"""

    BLOCKED_PRE_CP5 = "blocked_pre_cp5"
    BLOCKED_DEPENDENCY = "blocked_dependency"
    BLOCKED_CONFIG = "blocked_config"
    BLOCKED_RUNTIME_AUTHORIZATION = "blocked_runtime_authorization"
    READY_DRY_ADMISSION = "ready_dry_admission"
    RUNTIME_AUTHORIZED = "runtime_authorized"


@dataclass(frozen=True, slots=True)
class GatewayCommandSpec:
    """gateway 命令结构；仅用于文档和离线验证。"""

    command_name: str
    config_path: str
    bind_host: str
    port: int
    auth_mode: str
    arguments: tuple[str, ...]
    service_start_allowed: bool = False
    port_bind_allowed: bool = False
    dry_run_only: bool = True
    schema_version: str = GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "command_name": self.command_name,
            "config_path": self.config_path,
            "bind_host": self.bind_host,
            "port": self.port,
            "auth_mode": self.auth_mode,
            "arguments": list(self.arguments),
            "service_start_allowed": self.service_start_allowed,
            "port_bind_allowed": self.port_bind_allowed,
            "dry_run_only": self.dry_run_only,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class GatewayLifecyclePlan:
    """一次 lifecycle transition 的离线计划结果。"""

    requested_transition: str
    current_state: GatewayLifecycleState
    next_state: GatewayLifecycleState
    allowed: bool
    blocked_reason: str = ""
    command_spec: GatewayCommandSpec | None = None
    validation: GatewayConfigValidation | None = None
    counters: Mapping[str, int] = field(default_factory=collect_gateway_safety_counters)
    actions: tuple[str, ...] = ()
    schema_version: str = GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.allowed

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_transition": self.requested_transition,
            "current_state": self.current_state.value,
            "next_state": self.next_state.value,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "command_spec": (
                self.command_spec.to_dict() if self.command_spec is not None else None
            ),
            "validation": self.validation.to_dict() if self.validation is not None else None,
            "counters": dict(self.counters),
            "actions": list(self.actions),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class GatewayHealthSummary:
    """heartbeat 观测摘要；不主动连接 gateway。"""

    status: str
    state: GatewayLifecycleState
    healthy: bool
    blocked_reason: str = ""
    last_seen_at: str = ""
    latency_ms: int | None = None
    heartbeat_schema_version: str = ""
    redaction_status: str = "redacted"
    gateway_version: str = ""
    counters: Mapping[str, int] = field(default_factory=collect_gateway_safety_counters)
    schema_version: str = GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "state": self.state.value,
            "healthy": self.healthy,
            "blocked_reason": self.blocked_reason,
            "last_seen_at": self.last_seen_at,
            "latency_ms": self.latency_ms,
            "heartbeat_schema_version": self.heartbeat_schema_version,
            "redaction_status": self.redaction_status,
            "gateway_version": self.gateway_version,
            "counters": dict(self.counters),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class GatewayRuntimeAdmissionDecision:
    """CR020 gateway runtime 准入结果；只描述计划和阻断原因。"""

    requested_action: str
    status: GatewayRuntimeAdmissionStatus
    accepted: bool
    blocked_reason: str = ""
    reasons: tuple[str, ...] = ()
    flags: GatewayRuntimeFlags = field(default_factory=GatewayRuntimeFlags)
    config_validation: GatewayConfigValidation | None = None
    command_spec: GatewayCommandSpec | None = None
    counters: Mapping[str, int] = field(default_factory=collect_gateway_runtime_counters)
    redaction_status: str = "redacted"
    next_action: str = "review_admission"
    schema_version: str = GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.accepted

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_action": self.requested_action,
            "status": self.status.value,
            "accepted": self.accepted,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "reasons": list(self.reasons),
            "flags": self.flags.to_dict(),
            "config_validation": (
                self.config_validation.to_dict()
                if self.config_validation is not None
                else None
            ),
            "command_spec": (
                self.command_spec.to_dict() if self.command_spec is not None else None
            ),
            "counters": dict(self.counters),
            "redaction_status": self.redaction_status,
            "next_action": self.next_action,
            "schema_version": self.schema_version,
        }


class QmtQueryPositionsAdapter(Protocol):
    """Windows runtime 注入的只读持仓 adapter。"""

    def query_positions(
        self,
        request: QmtQueryPositionsRequest,
        session_snapshot: QmtSessionSnapshot,
    ) -> Mapping[str, object]:
        ...


def build_gateway_command_spec(
    config: GatewayConfig | Mapping[str, object] | None = None,
    *,
    command_name: str = "qmt-gateway",
) -> GatewayCommandSpec:
    """生成命令结构，不执行命令。"""

    current = build_gateway_config(config)
    arguments = (
        command_name,
        "serve",
        "--config",
        current.config_path,
        "--host",
        current.bind.bind_host,
        "--port",
        str(current.bind.port),
        "--auth-mode",
        current.auth_mode,
    )
    return GatewayCommandSpec(
        command_name=command_name,
        config_path=current.config_path,
        bind_host=current.bind.bind_host,
        port=current.bind.port,
        auth_mode=current.auth_mode,
        arguments=arguments,
    )


def plan_gateway_lifecycle(
    config: GatewayConfig | Mapping[str, object] | None = None,
    *,
    requested_transition: str = "plan",
    validation: GatewayConfigValidation | None = None,
) -> GatewayLifecyclePlan:
    """生成 lifecycle 计划；start / bind 类 transition 一律阻断。"""

    current_config = build_gateway_config(config)
    current_validation = validation or validate_gateway_security(current_config)
    command_spec = build_gateway_command_spec(current_config)
    transition = requested_transition.strip().lower() or "plan"

    if not current_validation.accepted:
        return GatewayLifecyclePlan(
            requested_transition=transition,
            current_state=GatewayLifecycleState.CONFIGURED,
            next_state=GatewayLifecycleState.BLOCKED_CONFIG,
            allowed=False,
            blocked_reason=current_validation.primary_reason,
            command_spec=command_spec,
            validation=current_validation,
            counters=collect_gateway_safety_counters(),
            actions=("fix_config",),
        )

    if transition in _START_TRANSITIONS:
        return GatewayLifecyclePlan(
            requested_transition=transition,
            current_state=GatewayLifecycleState.CONFIGURED,
            next_state=GatewayLifecycleState.CONFIGURED,
            allowed=False,
            blocked_reason=SERVICE_START_FORBIDDEN_REASON,
            command_spec=command_spec,
            validation=current_validation,
            counters=collect_gateway_safety_counters(),
            actions=("return_command_spec_only", "do_not_start_service"),
        )

    if transition in {"stop", "shutdown"}:
        return GatewayLifecyclePlan(
            requested_transition=transition,
            current_state=GatewayLifecycleState.CONFIGURED,
            next_state=GatewayLifecycleState.STOPPED,
            allowed=True,
            command_spec=command_spec,
            validation=current_validation,
            counters=collect_gateway_safety_counters(),
            actions=("record_stopped_state",),
        )

    return GatewayLifecyclePlan(
        requested_transition=transition,
        current_state=GatewayLifecycleState.CONFIGURED,
        next_state=GatewayLifecycleState.READY_TO_START,
        allowed=True,
        command_spec=command_spec,
        validation=current_validation,
        counters=collect_gateway_safety_counters(),
        actions=("validate_config", "publish_plan_only"),
    )


def evaluate_gateway_runtime_admission(
    config: GatewayConfig | Mapping[str, object] | None = None,
    *,
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
    requested_action: str = "admission",
    validation: GatewayConfigValidation | None = None,
) -> GatewayRuntimeAdmissionDecision:
    """统一评估 CR020 runtime admission；不启动服务、不绑定端口。"""

    current_config = build_gateway_config(config)
    current_flags = build_gateway_runtime_flags(flags)
    current_validation = validation or validate_gateway_security(current_config)
    command_spec = build_gateway_command_spec(current_config)
    action = requested_action.strip().lower() or "admission"
    counters = collect_gateway_runtime_counters()

    if not current_validation.accepted:
        reason = current_validation.primary_reason or CONFIG_VALIDATION_BLOCKED_REASON
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_CONFIG,
            accepted=False,
            blocked_reason=reason,
            reasons=(reason,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="fix_config",
        )

    if action in {"serve", "start", "run", "launch"} and not current_flags.service_start_allowed:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION,
            accepted=False,
            blocked_reason=SERVICE_START_FORBIDDEN_REASON,
            reasons=(SERVICE_START_FORBIDDEN_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="request_runtime_authorization",
        )

    if action in {"bind", "serve", "start", "run", "launch"} and not current_flags.port_bind_allowed:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION,
            accepted=False,
            blocked_reason=PORT_BIND_FORBIDDEN_REASON,
            reasons=(PORT_BIND_FORBIDDEN_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="request_port_bind_authorization",
        )

    if not current_flags.implementation_allowed:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_PRE_CP5,
            accepted=False,
            blocked_reason=IMPLEMENTATION_NOT_ALLOWED_REASON,
            reasons=(IMPLEMENTATION_NOT_ALLOWED_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="wait_for_cp5_and_dev_gate",
        )

    if not current_flags.dependency_change_allowed and action in {"dependency", "install"}:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_DEPENDENCY,
            accepted=False,
            blocked_reason=DEPENDENCY_CHANGE_NOT_ALLOWED_REASON,
            reasons=(DEPENDENCY_CHANGE_NOT_ALLOWED_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="do_not_modify_dependencies",
        )

    if action in {"credential", "login"} and not current_flags.credential_read_allowed:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION,
            accepted=False,
            blocked_reason=CREDENTIAL_READ_FORBIDDEN_REASON,
            reasons=(CREDENTIAL_READ_FORBIDDEN_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="do_not_read_real_env",
        )

    if action in {"qmt", "login", "query_positions"} and not current_flags.qmt_operation_allowed:
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION,
            accepted=False,
            blocked_reason=QMT_CALL_FORBIDDEN_REASON,
            reasons=(QMT_CALL_FORBIDDEN_REASON,),
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="do_not_call_qmt",
        )

    if action in {"serve", "start", "run", "launch", "bind", "login", "query_positions"}:
        if not current_flags.runtime_authorization_ref:
            return _runtime_decision(
                action,
                GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION,
                accepted=False,
                blocked_reason=RUNTIME_AUTHORIZATION_MISSING_REASON,
                reasons=(RUNTIME_AUTHORIZATION_MISSING_REASON,),
                flags=current_flags,
                validation=current_validation,
                command_spec=command_spec,
                counters=counters,
                next_action="provide_runtime_authorization_ref",
            )
        return _runtime_decision(
            action,
            GatewayRuntimeAdmissionStatus.RUNTIME_AUTHORIZED,
            accepted=True,
            flags=current_flags,
            validation=current_validation,
            command_spec=command_spec,
            counters=counters,
            next_action="return_authorized_plan_only",
        )

    return _runtime_decision(
        action,
        GatewayRuntimeAdmissionStatus.READY_DRY_ADMISSION,
        accepted=True,
        flags=current_flags,
        validation=current_validation,
        command_spec=command_spec,
        counters=counters,
        next_action="publish_admission_only",
    )


def plan_gateway_runtime_action(
    requested_action: str,
    config: GatewayConfig | Mapping[str, object] | None = None,
    *,
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
) -> GatewayRuntimeAdmissionDecision:
    """生成 CR020 runtime action 计划；不执行任何真实动作。"""

    return evaluate_gateway_runtime_admission(
        config,
        flags=flags,
        requested_action=requested_action,
    )


def build_gateway_runtime_health_summary(
    observation: Mapping[str, object] | None = None,
    *,
    config: GatewayConfig | Mapping[str, object] | None = None,
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
) -> dict[str, object]:
    """返回 heartbeat + admission 摘要；不主动探测网络。"""

    heartbeat = build_heartbeat_summary(observation)
    admission = evaluate_gateway_runtime_admission(
        config,
        flags=flags,
        requested_action="health",
    )
    return {
        "heartbeat": heartbeat.to_dict(),
        "admission": admission.to_dict(),
        "counters": collect_gateway_runtime_counters(),
        "schema_version": GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION,
    }


def build_gateway_runtime_diagnostics(
    config: GatewayConfig | Mapping[str, object] | None = None,
    *,
    flags: GatewayRuntimeFlags | Mapping[str, object] | None = None,
    requested_action: str = "diagnostics",
) -> dict[str, object]:
    """构造脱敏 diagnostics；只输出配置、准入和 zero counters。"""

    current_config = build_gateway_config(config)
    admission = evaluate_gateway_runtime_admission(
        current_config,
        flags=flags,
        requested_action=requested_action,
    )
    return {
        "config": current_config.to_dict(),
        "admission": admission.to_dict(),
        "redaction_status": "redacted",
        "counters": collect_gateway_runtime_counters(),
        "schema_version": GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION,
    }


def dispatch_qmt_gateway_endpoint(
    endpoint_id: str,
    request: Mapping[str, object] | QmtQueryPositionsRequest | None = None,
    *,
    session_snapshot: QmtSessionSnapshot | None = None,
    auth_admission: QmtAuthAdmissionDecision | None = None,
    adapter: QmtQueryPositionsAdapter | None = None,
    redaction_preflight: object | None = None,
) -> QmtGatewayResult:
    """Gateway endpoint dispatcher；CR020 只允许 `query_positions`。"""

    spec = get_cr020_query_positions_spec()
    if not is_cr020_readonly_endpoint_allowed(endpoint_id, spec.required_scope):
        return build_query_positions_blocked_result(
            QmtBlockedReason.ENDPOINT_NOT_SUPPORTED,
            "CR020 only allows query_positions readonly endpoint",
            endpoint_id=endpoint_id,
            detail={"allowed_endpoint_id": CR020_QUERY_POSITIONS_ENDPOINT_ID},
        )
    current_request = build_query_positions_request(request)
    return handle_query_positions(
        current_request,
        session_snapshot=session_snapshot,
        auth_admission=auth_admission,
        adapter=adapter,
        redaction_preflight=redaction_preflight,
    )


def handle_query_positions(
    request: QmtQueryPositionsRequest | Mapping[str, object],
    *,
    session_snapshot: QmtSessionSnapshot | None,
    auth_admission: QmtAuthAdmissionDecision | None,
    adapter: QmtQueryPositionsAdapter | None,
    redaction_preflight: object | None = None,
) -> QmtGatewayResult:
    """串联 endpoint/auth/session/redaction/adapter gate 后执行只读查询。"""

    current_request = build_query_positions_request(request)
    endpoint_id = CR020_QUERY_POSITIONS_ENDPOINT_ID

    auth_blocked = _auth_blocked_reason(auth_admission)
    if auth_blocked:
        return build_query_positions_blocked_result(
            auth_blocked,
            "query_positions auth admission blocked",
            detail={"required_scope": CR020_QUERY_POSITIONS_SCOPE},
        )
    if (
        auth_admission is not None
        and auth_admission.required_scope
        and auth_admission.required_scope != CR020_QUERY_POSITIONS_SCOPE
    ):
        return build_query_positions_blocked_result(
            QmtBlockedReason.SCOPE_DENIED,
            "query_positions requires exact qmt:positions:read scope",
            detail={"required_scope": CR020_QUERY_POSITIONS_SCOPE},
        )

    if session_snapshot is None:
        return build_query_positions_blocked_result(
            QmtSessionBlockedReason.SESSION_NOT_READY.value,
            "query_positions session snapshot is missing",
        )
    session_gate = require_qmt_session_ready(session_snapshot, endpoint_id=endpoint_id)
    if session_gate.blocked:
        reason = (
            session_gate.blocked_reason.value
            if session_gate.blocked_reason is not None
            else QmtSessionBlockedReason.SESSION_NOT_READY.value
        )
        return build_query_positions_blocked_result(
            reason,
            "query_positions session is not ready",
            detail={"session_state": session_gate.state.value},
        )

    if _redaction_preflight_blocked(redaction_preflight):
        return build_query_positions_blocked_result(
            QmtBlockedReason.REDACTION_FAILED,
            "query_positions redaction preflight blocked",
        )

    if adapter is None:
        return build_query_positions_blocked_result(
            ADAPTER_UNAVAILABLE_REASON,
            "query_positions adapter is unavailable",
        )

    try:
        raw_payload = adapter.query_positions(current_request, session_snapshot)
    except TimeoutError:
        return build_query_positions_blocked_result(
            TRANSPORT_TIMEOUT_REASON,
            "query_positions adapter timed out",
        )
    except Exception as exc:  # pragma: no cover - runtime adapter defensive branch
        return build_query_positions_blocked_result(
            ADAPTER_ERROR_REASON,
            f"query_positions adapter failed: {type(exc).__name__}",
        )

    redacted_payload = redact_query_positions_payload(
        raw_payload,
        max_items=current_request.max_positions,
    )
    leak_decision = scan_qmt_auth_redaction_leaks(redacted_payload.to_dict())
    if leak_decision.blocked:
        return build_query_positions_blocked_result(
            QmtBlockedReason.REDACTION_FAILED,
            "query_positions response redaction failed",
            detail={"redaction_status": leak_decision.redaction_status},
        )

    return build_query_positions_success_result(
        redacted_payload,
        counters=collect_query_positions_safety_counters(),
    )


def _runtime_decision(
    requested_action: str,
    status: GatewayRuntimeAdmissionStatus,
    *,
    accepted: bool,
    flags: GatewayRuntimeFlags,
    validation: GatewayConfigValidation,
    command_spec: GatewayCommandSpec,
    counters: Mapping[str, int],
    blocked_reason: str = "",
    reasons: tuple[str, ...] = (),
    next_action: str = "review_admission",
) -> GatewayRuntimeAdmissionDecision:
    return GatewayRuntimeAdmissionDecision(
        requested_action=requested_action,
        status=status,
        accepted=accepted,
        blocked_reason=blocked_reason,
        reasons=reasons,
        flags=flags,
        config_validation=validation,
        command_spec=command_spec,
        counters=counters,
        next_action=next_action,
    )


def build_heartbeat_summary(
    observation: Mapping[str, object] | None = None,
) -> GatewayHealthSummary:
    """基于 fixture observation 生成 heartbeat 摘要；不探测服务。"""

    current = dict(observation or {})
    healthy = bool(current.get("healthy", current.get("status", "healthy") == "healthy"))
    status = str(current.get("status", "healthy" if healthy else "unhealthy"))
    blocked_reason = str(current.get("blocked_reason", ""))
    if not healthy and not blocked_reason:
        blocked_reason = HEARTBEAT_FAILED_REASON

    return GatewayHealthSummary(
        status=status,
        state=(
            GatewayLifecycleState.RUNNING_OBSERVED
            if healthy
            else GatewayLifecycleState.UNHEALTHY
        ),
        healthy=healthy,
        blocked_reason=blocked_reason,
        last_seen_at=str(current.get("last_seen_at", "")),
        latency_ms=(
            int(current["latency_ms"]) if current.get("latency_ms") is not None else None
        ),
        heartbeat_schema_version=str(current.get("schema_version", "")),
        redaction_status=str(current.get("redaction_status", "redacted")),
        gateway_version=str(current.get("gateway_version", "")),
        counters=collect_gateway_safety_counters(),
    )


def service_start_forbidden(
    config: GatewayConfig | Mapping[str, object] | None = None,
) -> GatewayLifecyclePlan:
    """显式 start guard；返回 blocked plan，不执行任何启动动作。"""

    return plan_gateway_lifecycle(config, requested_transition="start")


def _auth_blocked_reason(
    admission: QmtAuthAdmissionDecision | None,
) -> str:
    if admission is None:
        return QmtBlockedReason.AUTH_REQUIRED.value
    if admission.accepted:
        return ""
    if admission.blocked_reason is not None:
        return admission.blocked_reason.value
    return QmtBlockedReason.AUTH_FAILED.value


def _redaction_preflight_blocked(decision: object | None) -> bool:
    if decision is None:
        return False
    if isinstance(decision, Mapping):
        accepted = decision.get("accepted")
        if accepted is not None:
            return not bool(accepted)
        status = str(decision.get("redaction_status", "pass"))
        return status == "failed"
    accepted = getattr(decision, "accepted", None)
    if accepted is not None:
        return not bool(accepted)
    status = str(getattr(decision, "redaction_status", "pass"))
    return status == "failed"
