"""CR019-S06 的 QMT gateway typed result 离线合同。

本模块只定义 allowed / blocked 结果、错误 payload 和禁止操作计数，
不读取凭据、不启动服务、不打开网络、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


QMT_GATEWAY_CONTRACT_SCHEMA_VERSION = "cr019-s06-qmt-gateway-contracts-v1"

QMT_GATEWAY_FORBIDDEN_COUNTER_FIELDS: tuple[str, ...] = (
    "dependency_change",
    "service_start",
    "service_bind",
    "credential_read",
    "qmt_operation",
    "qmt_api_call",
    "xtquant_import",
    "real_order",
    "real_cancel",
    "account_query",
    "account_write",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "simulation_or_live_run",
    "http_client_call",
    "gateway_socket_open",
)


class QmtGatewayResultStatus(str, Enum):
    """Gateway 合同结果状态。"""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


class QmtBlockedReason(str, Enum):
    """QMT endpoint / gateway 共享的稳定阻断原因。"""

    UNKNOWN_ENDPOINT = "unknown_endpoint"
    VALIDATION_BLOCKED = "validation_blocked"
    TRANSPORT_BLOCKED = "transport_blocked"
    AUTH_BLOCKED = "auth_blocked"
    SCOPE_DENIED = "scope_denied"
    STAGE_GATE_BLOCKED = "stage_gate_blocked"
    RISK_GATE_BLOCKED = "risk_gate_blocked"
    KILL_SWITCH_ACTIVE = "kill_switch_active"
    AUTHORIZATION_MISSING = "authorization_missing"
    RAW_POLICY_BLOCKED = "raw_policy_blocked"
    QMT_OPERATION_NOT_AUTHORIZED = "qmt_operation_not_authorized"
    FALLBACK_BLOCKED = "fallback_blocked"
    REDACTION_FAILED = "redaction_failed"
    BROKER_LAKE_WRITE_FORBIDDEN = "broker_lake_write_forbidden"

    # S03 client 既有合同值，继续兼容薄 CLI / client 回归测试。
    TRANSPORT_UNAVAILABLE = "transport_unavailable"
    AUTH_REQUIRED = "auth_required"
    AUTH_FAILED = "auth_failed"
    STAGE_GATE_MISSING = "stage_gate_missing"
    PER_RUN_AUTHORIZATION_MISSING = "per_run_authorization_missing"
    ENDPOINT_NOT_SUPPORTED = "endpoint_not_supported"
    INVALID_REQUEST = "invalid_request"
    REDACTION_REQUIRED = "redaction_required"
    REAL_OPERATION_FORBIDDEN = "real_operation_forbidden"


@dataclass(frozen=True, slots=True)
class QmtGatewaySafetyCounters:
    """S06 合同必须保持为 0 的真实操作计数。"""

    dependency_change: int = 0
    service_start: int = 0
    service_bind: int = 0
    credential_read: int = 0
    qmt_operation: int = 0
    qmt_api_call: int = 0
    xtquant_import: int = 0
    real_order: int = 0
    real_cancel: int = 0
    account_query: int = 0
    account_write: int = 0
    provider_fetch: int = 0
    lake_write: int = 0
    broker_lake_write: int = 0
    publish: int = 0
    current_pointer_publish: int = 0
    simulation_or_live_run: int = 0
    http_client_call: int = 0
    gateway_socket_open: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            key: int(getattr(self, key))
            for key in QMT_GATEWAY_FORBIDDEN_COUNTER_FIELDS
        }


@dataclass(frozen=True, slots=True)
class QmtAllowedPayload:
    """allowed 结果的结构化 payload；当前只用于 fixture 合同。"""

    endpoint_id: str
    data: Mapping[str, object] = field(default_factory=dict)
    operation_authorized: bool = False
    fixture_only: bool = True
    real_operation: bool = False
    schema_version: str = QMT_GATEWAY_CONTRACT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "endpoint_id": self.endpoint_id,
            "data": dict(self.data),
            "operation_authorized": self.operation_authorized,
            "fixture_only": self.fixture_only,
            "real_operation": self.real_operation,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class QmtErrorPayload:
    """blocked / error 结果的结构化暴露，不包含 secret 或敏感值。"""

    code: str
    message: str
    endpoint_id: str
    blocked_reason: QmtBlockedReason | str
    redaction_status: str = "redacted"
    detail: Mapping[str, object] = field(default_factory=dict)
    schema_version: str = QMT_GATEWAY_CONTRACT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "endpoint_id": self.endpoint_id,
            "blocked_reason": _enum_value(self.blocked_reason),
            "redaction_status": self.redaction_status,
            "detail": dict(self.detail),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class QmtGatewayResult:
    """Gateway allowed / blocked 的统一 typed result。"""

    status: QmtGatewayResultStatus | str
    endpoint_id: str
    allowed_payload: QmtAllowedPayload | None = None
    error: QmtErrorPayload | None = None
    blocked_reason: QmtBlockedReason | str | None = None
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_gateway_contract_counters()
    )
    schema_version: str = QMT_GATEWAY_CONTRACT_SCHEMA_VERSION

    @property
    def allowed(self) -> bool:
        return _enum_value(self.status) == QmtGatewayResultStatus.ALLOWED.value

    @property
    def blocked(self) -> bool:
        return not self.allowed

    @property
    def reason_code(self) -> str:
        return "" if self.blocked_reason is None else _enum_value(self.blocked_reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": _enum_value(self.status),
            "endpoint_id": self.endpoint_id,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "blocked_reason": self.reason_code,
            "allowed_payload": (
                self.allowed_payload.to_dict()
                if self.allowed_payload is not None
                else None
            ),
            "error": self.error.to_dict() if self.error is not None else None,
            "counters": dict(self.counters),
        }


def collect_qmt_gateway_contract_counters(
    counters: Mapping[str, int] | QmtGatewaySafetyCounters | None = None,
) -> dict[str, int]:
    """归一化 S06 禁止操作计数；默认全部为 0。"""

    normalized = QmtGatewaySafetyCounters().to_dict()
    if counters is None:
        return normalized
    raw = counters.to_dict() if isinstance(counters, QmtGatewaySafetyCounters) else dict(counters)
    for key, value in raw.items():
        normalized[str(key)] = int(value)
    return normalized


def build_allowed_result(
    endpoint_id: str,
    payload: Mapping[str, object] | QmtAllowedPayload | None = None,
    *,
    counters: Mapping[str, int] | QmtGatewaySafetyCounters | None = None,
) -> QmtGatewayResult:
    """构造 fixture-only allowed result；不代表真实 QMT 操作授权。"""

    allowed_payload = (
        payload
        if isinstance(payload, QmtAllowedPayload)
        else QmtAllowedPayload(endpoint_id=endpoint_id, data=payload or {})
    )
    return QmtGatewayResult(
        status=QmtGatewayResultStatus.ALLOWED,
        endpoint_id=endpoint_id,
        allowed_payload=allowed_payload,
        counters=collect_qmt_gateway_contract_counters(counters),
    )


def build_blocked_result(
    endpoint_id: str,
    reason: QmtBlockedReason | str,
    message: str = "",
    *,
    detail: Mapping[str, object] | None = None,
    counters: Mapping[str, int] | QmtGatewaySafetyCounters | None = None,
    redaction_status: str = "redacted",
) -> QmtGatewayResult:
    """构造 typed blocked result；真实操作计数默认全部为 0。"""

    reason_value = _enum_value(reason)
    error = QmtErrorPayload(
        code=reason_value,
        message=message or f"endpoint {endpoint_id} blocked: {reason_value}",
        endpoint_id=endpoint_id,
        blocked_reason=reason,
        redaction_status=redaction_status,
        detail=detail or {},
    )
    return QmtGatewayResult(
        status=QmtGatewayResultStatus.BLOCKED,
        endpoint_id=endpoint_id,
        error=error,
        blocked_reason=reason,
        counters=collect_qmt_gateway_contract_counters(counters),
    )


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)
