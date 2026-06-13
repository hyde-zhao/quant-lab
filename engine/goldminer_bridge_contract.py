"""CR045 Goldminer bridge L2 合同。

本模块只提供离线 skeleton、fixture response 和静态证据结构，不导入、
不探测、不启动任何 Goldminer、Windows bridge 或 broker runtime。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


CR045_BRIDGE_SCHEMA_VERSION = "cr045.l2.v1"

ALLOWED_L2_ACTIONS: tuple[str, ...] = (
    "health",
    "capabilities",
    "readonly_probe_skeleton",
)

NOT_AUTHORIZED_ACTIONS: tuple[str, ...] = (
    "credential_read",
    "token_account_id_collection",
    "windows_bridge_runtime_start",
    "goldminer_login",
    "goldminer_connect",
    "account_query",
    "cash_query",
    "position_query",
    "order_query",
    "fill_query",
    "order_submit",
    "order_cancel",
    "simulation_runtime",
    "live_runtime",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
)

SENSITIVE_FIELD_CATEGORIES: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "passwd",
    "cookie",
    "session",
    "private_key",
    "account_id",
    "broker_account",
    "real_account",
    "trade_password",
    "credential",
)

FORBIDDEN_OPERATION_COUNTERS: tuple[str, ...] = (
    "real_broker_call",
    "real_order_call",
    "real_cancel_call",
    "real_account_query",
    "real_position_query",
    "real_cash_query",
    "real_order_query",
    "real_fill_query",
    "credential_read",
    "goldminer_import_or_call",
    "gmtrade_import_or_call",
    "windows_bridge_runtime_start",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "simulation_runtime_start",
    "live_runtime_start",
)


class BridgeBlockedReason(str, Enum):
    WINDOWS_BRIDGE_RUNTIME_NOT_AUTHORIZED = "windows_bridge_runtime_not_authorized"
    GLOBAL_KILL_SWITCH_DISABLED = "global_kill_switch_disabled"
    PER_RUN_AUTHORIZATION_MISSING = "per_run_authorization_missing"
    OPERATION_NOT_WHITELISTED = "operation_not_whitelisted"
    GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED = "goldminer_readonly_query_not_authorized"
    SENSITIVE_MATERIAL_PRESENT = "sensitive_material_present"
    FORBIDDEN_OPERATION_NONZERO = "forbidden_operation_nonzero"


@dataclass(frozen=True)
class RedactionSummary:
    """只记录字段类别和计数，不记录字段值。"""

    schema_version: str = CR045_BRIDGE_SCHEMA_VERSION
    sensitive_fields_present: bool = False
    redacted_value: str = "REDACTED"
    category_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BridgeHealth:
    schema_version: str = CR045_BRIDGE_SCHEMA_VERSION
    status: str = "blocked"
    runtime_started: bool = False
    not_authorization: bool = True
    reason: str = BridgeBlockedReason.WINDOWS_BRIDGE_RUNTIME_NOT_AUTHORIZED.value
    operation_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BridgeCapabilities:
    schema_version: str = CR045_BRIDGE_SCHEMA_VERSION
    real_broker_enabled: bool = False
    readonly_probe_ready: bool = False
    simulation_ready: bool = False
    live_ready: bool = False
    allowed_actions: tuple[str, ...] = ALLOWED_L2_ACTIONS
    not_authorized_actions: tuple[str, ...] = NOT_AUTHORIZED_ACTIONS
    not_authorization: bool = True
    reason: str = BridgeBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
    operation_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def allowed_l2_actions() -> tuple[str, ...]:
    return ALLOWED_L2_ACTIONS


def sensitive_field_categories() -> tuple[str, ...]:
    return SENSITIVE_FIELD_CATEGORIES


def not_authorized_actions() -> tuple[str, ...]:
    return NOT_AUTHORIZED_ACTIONS


def forbidden_operation_counter_names() -> tuple[str, ...]:
    return FORBIDDEN_OPERATION_COUNTERS


def zero_forbidden_operation_counts() -> dict[str, int]:
    return {name: 0 for name in FORBIDDEN_OPERATION_COUNTERS}


def classify_sensitive_field_name(field_name: str) -> str | None:
    normalized = field_name.lower()
    for category in sorted(SENSITIVE_FIELD_CATEGORIES, key=len, reverse=True):
        if category in normalized:
            return category
    return None


def summarize_sensitive_field_names(field_names: list[str] | tuple[str, ...]) -> RedactionSummary:
    counts: dict[str, int] = {}
    for field_name in field_names:
        category = classify_sensitive_field_name(field_name)
        if category is not None:
            counts[category] = counts.get(category, 0) + 1
    return RedactionSummary(
        sensitive_fields_present=bool(counts),
        category_counts=counts,
    )


def mapping_sensitive_categories(payload: Mapping[str, Any]) -> RedactionSummary:
    return summarize_sensitive_field_names(tuple(str(key) for key in payload.keys()))


def build_bridge_health() -> BridgeHealth:
    return BridgeHealth(operation_counts=zero_forbidden_operation_counts())


def build_bridge_capabilities() -> BridgeCapabilities:
    return BridgeCapabilities(operation_counts=zero_forbidden_operation_counts())


def build_blocked_payload(
    *,
    action: str,
    reason: BridgeBlockedReason = BridgeBlockedReason.OPERATION_NOT_WHITELISTED,
    field_names: tuple[str, ...] = (),
) -> dict[str, Any]:
    redaction = summarize_sensitive_field_names(field_names)
    return {
        "schema_version": CR045_BRIDGE_SCHEMA_VERSION,
        "status": "blocked",
        "action": action,
        "reason": reason.value,
        "not_authorization": True,
        "operation_counts": zero_forbidden_operation_counts(),
        "redaction_summary": redaction.to_dict(),
    }


def assert_zero_operation_counts(operation_counts: Mapping[str, int]) -> None:
    nonzero = {name: count for name, count in operation_counts.items() if count != 0}
    if nonzero:
        names = ", ".join(sorted(nonzero))
        raise ValueError(f"{BridgeBlockedReason.FORBIDDEN_OPERATION_NONZERO.value}: {names}")
