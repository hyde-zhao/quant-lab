"""CR045 readonly probe skeleton blocked-first 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from engine.goldminer_bridge_contract import (
    BridgeBlockedReason,
    mapping_sensitive_categories,
    sensitive_field_categories,
    zero_forbidden_operation_counts,
)


READONLY_PROBE_ACTION = "readonly_probe_skeleton"

READONLY_SKELETON_PROBE_KINDS: tuple[str, ...] = (
    "account_state_skeleton",
    "cash_skeleton",
    "position_skeleton",
    "order_skeleton",
    "fill_skeleton",
)

REAL_READONLY_QUERY_KINDS: tuple[str, ...] = (
    "account_query",
    "account_state_query",
    "cash_query",
    "position_query",
    "order_query",
    "fill_query",
)


@dataclass(frozen=True)
class ReadonlyProbeRequest:
    action: str = READONLY_PROBE_ACTION
    probe_kind: str = "account_state_skeleton"
    client_context: dict[str, Any] = field(default_factory=dict)
    contains_sensitive_material: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReadonlyProbeResponse:
    status: str = "blocked"
    reason: str = BridgeBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED.value
    real_readonly_verified: bool = False
    not_authorization: bool = True
    operation_counts: dict[str, int] = field(default_factory=zero_forbidden_operation_counts)
    data: dict[str, Any] = field(default_factory=dict)
    redaction_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def readonly_probe_kinds() -> tuple[str, ...]:
    return READONLY_SKELETON_PROBE_KINDS


def readonly_probe_forbidden_fields() -> tuple[str, ...]:
    return (
        *sensitive_field_categories(),
        "account_state",
        "cash",
        "position",
        "order",
        "fill",
    )


def build_readonly_probe_request(
    probe_kind: str,
    client_context: Mapping[str, Any] | None = None,
    *,
    contains_sensitive_material: bool = False,
) -> ReadonlyProbeRequest:
    return ReadonlyProbeRequest(
        probe_kind=probe_kind,
        client_context=dict(client_context or {}),
        contains_sensitive_material=contains_sensitive_material,
    )


def evaluate_readonly_probe_request(request: ReadonlyProbeRequest) -> ReadonlyProbeResponse:
    if request.action != READONLY_PROBE_ACTION:
        return build_blocked_readonly_response(
            request,
            BridgeBlockedReason.OPERATION_NOT_WHITELISTED.value,
        )
    redaction = mapping_sensitive_categories(request.client_context)
    if request.contains_sensitive_material or redaction.sensitive_fields_present:
        return build_blocked_readonly_response(
            request,
            BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT.value,
            redaction_summary=redaction.to_dict(),
        )
    if request.probe_kind in REAL_READONLY_QUERY_KINDS:
        return build_blocked_readonly_response(
            request,
            BridgeBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED.value,
        )
    if request.probe_kind not in READONLY_SKELETON_PROBE_KINDS:
        return build_blocked_readonly_response(
            request,
            BridgeBlockedReason.OPERATION_NOT_WHITELISTED.value,
        )
    return build_blocked_readonly_response(
        request,
        BridgeBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value,
    )


def build_blocked_readonly_response(
    request: ReadonlyProbeRequest,
    reason: str,
    *,
    redaction_summary: Mapping[str, Any] | None = None,
) -> ReadonlyProbeResponse:
    return ReadonlyProbeResponse(
        reason=reason,
        operation_counts=zero_forbidden_operation_counts(),
        data={},
        redaction_summary=dict(redaction_summary or {}),
    )
