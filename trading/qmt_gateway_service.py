"""CR019-S04 的 Windows QMT gateway lifecycle 离线合同。

本模块只生成命令结构、生命周期计划和 heartbeat 摘要，不启动服务、
不绑定端口、不打开网络连接、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from trading.qmt_gateway_config import (
    GatewayConfig,
    GatewayConfigValidation,
    build_gateway_config,
    collect_gateway_safety_counters,
    validate_gateway_security,
)


GATEWAY_SERVICE_SCHEMA_VERSION = "cr019-s04-gateway-service-v1"
HEARTBEAT_FAILED_REASON = "heartbeat_failed"
SERVICE_START_FORBIDDEN_REASON = "service_start_forbidden"

_START_TRANSITIONS = frozenset({"start", "serve", "run", "launch", "bind"})


class GatewayLifecycleState(str, Enum):
    """S04 lifecycle 合同状态；当前实现不进入真实 running。"""

    CONFIGURED = "configured"
    BLOCKED_CONFIG = "blocked_config"
    READY_TO_START = "ready_to_start"
    RUNNING_OBSERVED = "running_observed"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"


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
