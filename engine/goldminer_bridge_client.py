"""CR045 WSL/Linux bridge client L2 fixture 合同。

client 只构造 allowlist request、消费 fixture response，并返回声明性
network precheck；不会打开 socket、HTTP、subprocess 或 Windows runtime。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from engine.goldminer_bridge_contract import (
    BridgeBlockedReason,
    allowed_l2_actions,
    build_blocked_payload,
    build_bridge_capabilities,
    build_bridge_health,
    mapping_sensitive_categories,
    zero_forbidden_operation_counts,
)


@dataclass(frozen=True)
class BridgeClientRequest:
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    client_context: dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BridgeClientResponse:
    status: str
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)
    not_authorization: bool = True
    operation_counts: dict[str, int] = field(default_factory=dict)
    redaction_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NetworkPrecheckResult:
    runtime_reachable: bool = False
    runtime_start_attempted: bool = False
    real_connection_attempted: bool = False
    not_authorization: bool = True
    reason: str = BridgeBlockedReason.WINDOWS_BRIDGE_RUNTIME_NOT_AUTHORIZED.value
    operation_counts: dict[str, int] = field(default_factory=zero_forbidden_operation_counts)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_bridge_client_request(
    action: str,
    payload: Mapping[str, Any] | None = None,
    client_context: Mapping[str, Any] | None = None,
) -> BridgeClientRequest:
    request_payload = dict(payload or {})
    request_context = dict(client_context or {})
    if action not in allowed_l2_actions():
        return BridgeClientRequest(
            action=action,
            payload={},
            client_context={},
            blocked=True,
            reason=BridgeBlockedReason.OPERATION_NOT_WHITELISTED.value,
        )
    redaction = mapping_sensitive_categories({**request_payload, **request_context})
    if redaction.sensitive_fields_present:
        return BridgeClientRequest(
            action=action,
            payload={},
            client_context={},
            blocked=True,
            reason=BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT.value,
        )
    return BridgeClientRequest(
        action=action,
        payload=request_payload,
        client_context=request_context,
    )


def network_precheck() -> NetworkPrecheckResult:
    return NetworkPrecheckResult()


def fixture_transport(request: BridgeClientRequest) -> BridgeClientResponse:
    if request.blocked:
        payload = build_blocked_payload(action=request.action, reason=BridgeBlockedReason(request.reason))
        return parse_bridge_response(payload)
    if request.action == "health":
        return parse_bridge_response(build_bridge_health().to_dict())
    if request.action == "capabilities":
        return parse_bridge_response(build_bridge_capabilities().to_dict())
    if request.action == "readonly_probe_skeleton":
        payload = build_blocked_payload(
            action=request.action,
            reason=BridgeBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED,
        )
        payload["real_readonly_verified"] = False
        payload["data"] = {}
        return parse_bridge_response(payload)
    payload = build_blocked_payload(action=request.action, reason=BridgeBlockedReason.OPERATION_NOT_WHITELISTED)
    return parse_bridge_response(payload)


def parse_bridge_response(payload: Mapping[str, Any]) -> BridgeClientResponse:
    redaction = mapping_sensitive_categories(payload)
    if redaction.sensitive_fields_present:
        return BridgeClientResponse(
            status="blocked",
            reason=BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT.value,
            payload={},
            operation_counts=zero_forbidden_operation_counts(),
            redaction_summary=redaction.to_dict(),
        )
    status = str(payload.get("status") or "blocked")
    reason = str(payload.get("reason") or BridgeBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value)
    operation_counts = dict(payload.get("operation_counts") or zero_forbidden_operation_counts())
    return BridgeClientResponse(
        status=status,
        reason=reason,
        payload=dict(payload),
        not_authorization=bool(payload.get("not_authorization", True)),
        operation_counts=operation_counts,
        redaction_summary=redaction.to_dict(),
    )
