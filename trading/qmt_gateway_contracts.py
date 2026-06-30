"""CR019-S06 的 QMT gateway typed result 离线合同。

本模块只定义 allowed / blocked 结果、错误 payload 和禁止操作计数，
不读取凭据、不启动服务、不打开网络、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Iterable, Mapping, Sequence


QMT_GATEWAY_CONTRACT_SCHEMA_VERSION = "cr019-s06-qmt-gateway-contracts-v1"
CR020_QUERY_POSITIONS_SCHEMA_VERSION = "cr020-s05-query-positions-readonly-v1"
CR020_QUERY_POSITIONS_ENDPOINT_ID = "query_positions"
CR020_QUERY_POSITIONS_PATH = "/qmt/account/positions"
CR020_QUERY_POSITIONS_SCOPE = "qmt:positions:read"
QMT_SIMULATION_SUBMIT_ENDPOINT_ID = "submit_simulation"
QMT_SIMULATION_SUBMIT_PATH = "/qmt/simulation/orders"
QMT_SIMULATION_SUBMIT_SCOPE = "qmt:simulation:submit"
QMT_SIMULATION_CANCEL_ENDPOINT_ID = "cancel_simulation"
QMT_SIMULATION_CANCEL_PATH = "/qmt/simulation/orders/cancel"
QMT_SIMULATION_CANCEL_SCOPE = "qmt:simulation:cancel"
COST_PRETRADE_GATE_ALLOWED = "allowed"
COST_PRETRADE_GATE_BLOCKED = "blocked"
COST_SCHEDULE_MISSING = "cost_schedule_missing"
COST_SCHEDULE_VERSION_MISSING = "cost_schedule_version_missing"
COST_MODEL_REF_MISSING = "cost_model_ref_missing"
LIQUIDITY_REF_MISSING = "liquidity_ref_missing"
TRADABILITY_UNAVAILABLE = "tradability_unavailable"
ORDER_NOTIONAL_INVALID = "order_notional_invalid"

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

QMT_QUERY_POSITIONS_COUNTER_FIELDS: tuple[str, ...] = (
    *QMT_GATEWAY_FORBIDDEN_COUNTER_FIELDS,
    "adapter_call",
    "query_positions_read_attempt",
    "readonly_positions_adapter_call",
    "raw_positions_emit",
    "redaction_fallback_to_raw",
)

CR138_GATEWAY_SERVICE_SCHEMA_VERSION = "cr138-qmt-gateway-service-layer-v1"
QMT_SIMULATION_ORDER_SCHEMA_VERSION = "qmt-simulation-order-runtime-v1"
QMT_RUNTIME_IDENTITY_SCHEMA_VERSION = "qmt-runtime-identity-v1"


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
    RUNTIME_PROFILE_MISMATCH = "runtime_profile_mismatch"
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
class QmtQueryPositionsRequest:
    """`query_positions` 只读请求；不包含账号、secret 或原始凭据。"""

    run_id: str
    request_id: str = ""
    redaction_label: str = "qmt-positions-redacted"
    include_empty: bool = True
    max_positions: int = 200
    filter_ref: str = ""
    payload: Mapping[str, object] = field(default_factory=dict)
    schema_version: str = CR020_QUERY_POSITIONS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "redaction_label": self.redaction_label,
            "include_empty": self.include_empty,
            "max_positions": self.max_positions,
            "filter_ref": self.filter_ref,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class QmtSimulationOrderRequest:
    """模拟账户真实委托请求；只允许脱敏字段进入 gateway。"""

    run_id: str
    request_id: str
    order_intent_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    price_type: str = "FIX_PRICE"
    authorization_ref: str = ""
    idempotency_key: str = ""
    redaction_label: str = "qmt-simulation-order-redacted"
    schema_version: str = QMT_SIMULATION_ORDER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "order_intent_id": self.order_intent_id,
            "symbol_ref": _stable_ref(self.symbol, "symbol"),
            "side": self.side,
            "quantity": self.quantity,
            "price_ref": _stable_ref(str(self.price), "price"),
            "price_type": self.price_type,
            "authorization_ref": self.authorization_ref,
            "idempotency_key": self.idempotency_key,
            "redaction_label": self.redaction_label,
        }


@dataclass(frozen=True, slots=True)
class QmtSimulationCancelRequest:
    """模拟账户真实撤单请求；broker order ref 只以脱敏引用输出。"""

    run_id: str
    request_id: str
    order_intent_id: str
    broker_order_ref: str
    symbol: str = ""
    authorization_ref: str = ""
    idempotency_key: str = ""
    redaction_label: str = "qmt-simulation-cancel-redacted"
    schema_version: str = QMT_SIMULATION_ORDER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "order_intent_id": self.order_intent_id,
            "broker_order_ref": _stable_ref(self.broker_order_ref, "broker-order"),
            "symbol_ref": _stable_ref(self.symbol, "symbol") if self.symbol else "",
            "authorization_ref": self.authorization_ref,
            "idempotency_key": self.idempotency_key,
            "redaction_label": self.redaction_label,
        }


@dataclass(frozen=True, slots=True)
class QmtRuntimeIdentityExpectation:
    """请求侧期望的 runtime 身份；不包含账号原文或凭据。"""

    expected_runtime_mode: str = ""
    expected_runtime_profile: str = ""
    schema_version: str = QMT_RUNTIME_IDENTITY_SCHEMA_VERSION

    @property
    def complete(self) -> bool:
        return bool(self.expected_runtime_mode and self.expected_runtime_profile)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "expected_runtime_mode": self.expected_runtime_mode,
            "expected_runtime_profile": self.expected_runtime_profile,
        }


@dataclass(frozen=True, slots=True)
class QmtSimulationOperationPayload:
    """模拟账户 submit/cancel 的脱敏执行结果。"""

    operation: str
    run_id: str
    order_intent_id: str
    accepted: bool
    broker_order_ref: str = ""
    cancel_ref: str = ""
    adapter_status: str = ""
    redaction_status: str = "redacted"
    schema_version: str = QMT_SIMULATION_ORDER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "run_id": self.run_id,
            "order_intent_id": self.order_intent_id,
            "accepted": self.accepted,
            "broker_order_ref": (
                _stable_ref(self.broker_order_ref, "broker-order")
                if self.broker_order_ref
                else ""
            ),
            "cancel_ref": self.cancel_ref,
            "adapter_status": self.adapter_status,
            "redaction_status": self.redaction_status,
        }


@dataclass(frozen=True, slots=True)
class QmtRedactedPositionRecord:
    """脱敏后的单条持仓摘要；不输出证券代码、数量或市值原文。"""

    position_ref: str
    instrument_ref: str
    side_ref: str = "side:unknown"
    quantity_bucket: str = "unknown"
    value_bucket: str = "unknown"
    schema_version: str = CR020_QUERY_POSITIONS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "position_ref": self.position_ref,
            "instrument_ref": self.instrument_ref,
            "side_ref": self.side_ref,
            "quantity_bucket": self.quantity_bucket,
            "value_bucket": self.value_bucket,
        }


@dataclass(frozen=True, slots=True)
class QmtQueryPositionsPayload:
    """`query_positions` 对外响应 payload；只保留脱敏摘要。"""

    position_count: int
    positions_digest: str
    items_redacted: tuple[QmtRedactedPositionRecord, ...] = ()
    redaction_status: str = "pass"
    raw_payload_emitted: bool = False
    schema_version: str = CR020_QUERY_POSITIONS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "position_count": self.position_count,
            "positions_digest": self.positions_digest,
            "items_redacted": [item.to_dict() for item in self.items_redacted],
            "redaction_status": self.redaction_status,
            "raw_payload_emitted": self.raw_payload_emitted,
        }


@dataclass(frozen=True, slots=True)
class QmtQueryPositionsResult:
    """S05 专用结果包装；内部仍复用 gateway typed result。"""

    gateway_result: "QmtGatewayResult"
    query_payload: QmtQueryPositionsPayload | None = None
    schema_version: str = CR020_QUERY_POSITIONS_SCHEMA_VERSION

    @property
    def allowed(self) -> bool:
        return self.gateway_result.allowed

    @property
    def blocked(self) -> bool:
        return self.gateway_result.blocked

    @property
    def reason_code(self) -> str:
        return self.gateway_result.reason_code

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "reason_code": self.reason_code,
            "query_payload": (
                self.query_payload.to_dict()
                if self.query_payload is not None
                else None
            ),
            "gateway_result": self.gateway_result.to_dict(),
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


def collect_query_positions_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """归一化 `query_positions` 安全计数。"""

    normalized = {key: 0 for key in QMT_QUERY_POSITIONS_COUNTER_FIELDS}
    if counters is None:
        return normalized
    for key, value in dict(counters).items():
        normalized[str(key)] = int(value)
    return normalized


def build_query_positions_request(
    source: Mapping[str, object] | QmtQueryPositionsRequest | None = None,
    *,
    run_id: str = "qmt-query-positions-run",
    request_id: str = "",
    redaction_label: str = "qmt-positions-redacted",
    include_empty: bool = True,
    max_positions: int = 200,
    filter_ref: str = "",
    payload: Mapping[str, object] | None = None,
) -> QmtQueryPositionsRequest:
    """构造只读持仓请求；敏感过滤条件只能以 ref 形态传递。"""

    if isinstance(source, QmtQueryPositionsRequest):
        return source
    raw = dict(source or {})
    return QmtQueryPositionsRequest(
        run_id=str(raw.get("run_id") or run_id),
        request_id=str(raw.get("request_id") or request_id),
        redaction_label=str(raw.get("redaction_label") or redaction_label),
        include_empty=_as_bool(raw.get("include_empty", include_empty)),
        max_positions=max(0, int(raw.get("max_positions", max_positions))),
        filter_ref=str(raw.get("filter_ref") or filter_ref),
        payload=dict(raw.get("payload") or payload or {}),
    )


def build_simulation_order_request(
    source: Mapping[str, object] | QmtSimulationOrderRequest | None = None,
) -> QmtSimulationOrderRequest:
    """构造模拟账户委托请求；缺失关键字段由调用方 gate 阻断。"""

    if isinstance(source, QmtSimulationOrderRequest):
        return source
    raw = dict(source or {})
    payload = raw.get("payload")
    nested = payload if isinstance(payload, Mapping) else {}
    merged = {**nested, **raw}
    return QmtSimulationOrderRequest(
        run_id=str(merged.get("run_id") or ""),
        request_id=str(merged.get("request_id") or ""),
        order_intent_id=str(merged.get("order_intent_id") or merged.get("intent_id") or ""),
        symbol=str(merged.get("symbol") or ""),
        side=str(merged.get("side") or ""),
        quantity=_as_int(merged.get("quantity") or merged.get("qty")),
        price=_as_float(merged.get("price") or merged.get("order_price")),
        price_type=str(merged.get("price_type") or "FIX_PRICE"),
        authorization_ref=str(merged.get("authorization_ref") or ""),
        idempotency_key=str(merged.get("idempotency_key") or ""),
        redaction_label=str(merged.get("redaction_label") or "qmt-simulation-order-redacted"),
    )


def build_simulation_cancel_request(
    source: Mapping[str, object] | QmtSimulationCancelRequest | None = None,
) -> QmtSimulationCancelRequest:
    """构造模拟账户撤单请求；缺失关键字段由调用方 gate 阻断。"""

    if isinstance(source, QmtSimulationCancelRequest):
        return source
    raw = dict(source or {})
    payload = raw.get("payload")
    nested = payload if isinstance(payload, Mapping) else {}
    merged = {**nested, **raw}
    return QmtSimulationCancelRequest(
        run_id=str(merged.get("run_id") or ""),
        request_id=str(merged.get("request_id") or ""),
        order_intent_id=str(merged.get("order_intent_id") or merged.get("intent_id") or ""),
        broker_order_ref=str(merged.get("broker_order_ref") or ""),
        symbol=str(merged.get("symbol") or ""),
        authorization_ref=str(merged.get("authorization_ref") or ""),
        idempotency_key=str(merged.get("idempotency_key") or ""),
        redaction_label=str(merged.get("redaction_label") or "qmt-simulation-cancel-redacted"),
    )


def build_runtime_identity_expectation(
    source: Mapping[str, object] | QmtRuntimeIdentityExpectation | None = None,
    *,
    expected_runtime_mode: str = "",
    expected_runtime_profile: str = "",
) -> QmtRuntimeIdentityExpectation:
    """从请求或显式参数提取 runtime identity expectation。"""

    if isinstance(source, QmtRuntimeIdentityExpectation):
        return source
    raw = dict(source or {})
    payload = raw.get("payload")
    nested = payload if isinstance(payload, Mapping) else {}
    merged = {**nested, **raw}
    return QmtRuntimeIdentityExpectation(
        expected_runtime_mode=str(
            merged.get("expected_runtime_mode") or expected_runtime_mode
        ),
        expected_runtime_profile=str(
            merged.get("expected_runtime_profile") or expected_runtime_profile
        ),
    )


def build_simulation_operation_result(
    endpoint_id: str,
    payload: QmtSimulationOperationPayload,
    *,
    counters: Mapping[str, int] | None = None,
) -> QmtGatewayResult:
    """构造模拟账户真实操作的脱敏 allowed result。"""

    return build_allowed_result(
        endpoint_id,
        QmtAllowedPayload(
            endpoint_id=endpoint_id,
            data={"simulation_operation": payload.to_dict()},
            operation_authorized=True,
            fixture_only=False,
            real_operation=True,
        ),
        counters=counters,
    )


def _as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _stable_ref(value: str, prefix: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def redact_query_positions_payload(
    raw_payload: object,
    *,
    max_items: int = 200,
) -> QmtQueryPositionsPayload:
    """把 QMT 原始持仓响应压缩为不可逆脱敏摘要。"""

    positions = tuple(_extract_position_rows(raw_payload))
    limited = positions[: max(0, int(max_items))]
    items = tuple(
        _redacted_position_record(position, index=index)
        for index, position in enumerate(limited)
    )
    digest_source = {
        "position_count": len(positions),
        "items": [item.to_dict() for item in items],
    }
    return QmtQueryPositionsPayload(
        position_count=len(positions),
        positions_digest=f"positions:{_stable_hash(digest_source)[:16]}",
        items_redacted=items,
        redaction_status="pass",
        raw_payload_emitted=False,
    )


def build_query_positions_blocked_result(
    reason: QmtBlockedReason | str,
    message: str = "",
    *,
    endpoint_id: str = CR020_QUERY_POSITIONS_ENDPOINT_ID,
    detail: Mapping[str, object] | None = None,
    counters: Mapping[str, int] | None = None,
) -> QmtGatewayResult:
    """构造 `query_positions` typed blocked result。"""

    return build_blocked_result(
        endpoint_id,
        reason,
        message,
        detail=detail,
        counters=collect_query_positions_safety_counters(counters),
        redaction_status="redacted",
    )


def build_query_positions_success_result(
    payload: QmtQueryPositionsPayload,
    *,
    endpoint_id: str = CR020_QUERY_POSITIONS_ENDPOINT_ID,
    counters: Mapping[str, int] | None = None,
    fixture_only: bool = False,
) -> QmtGatewayResult:
    """构造 `query_positions` 成功响应；仅暴露脱敏摘要。"""

    current_counters = collect_query_positions_safety_counters(
        {
            **dict(counters or {}),
            "query_positions_read_attempt": 1,
            "readonly_positions_adapter_call": 1,
        }
    )
    return build_allowed_result(
        endpoint_id,
        QmtAllowedPayload(
            endpoint_id=endpoint_id,
            data={
                "endpoint_id": endpoint_id,
                "scope": CR020_QUERY_POSITIONS_SCOPE,
                "query_positions": payload.to_dict(),
                "readonly_query_authorized": True,
                "operation_authorized": False,
                "real_operation": False,
            },
            operation_authorized=False,
            fixture_only=fixture_only,
            real_operation=False,
            schema_version=CR020_QUERY_POSITIONS_SCHEMA_VERSION,
        ),
        counters=current_counters,
    )


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _extract_position_rows(raw_payload: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(raw_payload, Mapping):
        for key in ("positions", "data", "items", "result"):
            value = raw_payload.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return tuple(
                    item if isinstance(item, Mapping) else _object_to_mapping(item)
                    for item in value
                )
        return (raw_payload,)
    if isinstance(raw_payload, Sequence) and not isinstance(raw_payload, (str, bytes)):
        return tuple(
            item if isinstance(item, Mapping) else _object_to_mapping(item)
            for item in raw_payload
        )
    return (_object_to_mapping(raw_payload),)


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    fields = {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and _is_public_position_value(getattr(value, name))
    }
    return fields or {"value_ref": f"value:{_stable_hash(str(type(value)))[:12]}"}


def _is_public_position_value(value: object) -> bool:
    return isinstance(value, (str, int, float, bool, type(None)))


def _redacted_position_record(
    position: Mapping[str, object],
    *,
    index: int,
) -> QmtRedactedPositionRecord:
    instrument = _first_value(
        position,
        (
            "instrument",
            "instrument_id",
            "stock_code",
            "symbol",
            "code",
            "证券代码",
        ),
    )
    side = _first_value(position, ("side", "direction", "position_side", "持仓方向"))
    quantity = _first_value(
        position,
        ("quantity", "volume", "current_amount", "can_use_volume", "持仓数量"),
    )
    value = _first_value(
        position,
        ("market_value", "value", "position_value", "市值"),
    )
    return QmtRedactedPositionRecord(
        position_ref=f"position:{_stable_hash({'index': index, 'row': position})[:16]}",
        instrument_ref=f"instrument:{_stable_hash(instrument or index)[:12]}",
        side_ref=f"side:{_stable_hash(side or 'unknown')[:8]}",
        quantity_bucket=_quantity_bucket(quantity),
        value_bucket=_value_bucket(value),
    )


def _first_value(mapping: Mapping[str, object], keys: Iterable[str]) -> object:
    for key in keys:
        if key in mapping and mapping[key] not in ("", None):
            return mapping[key]
    return ""


def _quantity_bucket(value: object) -> str:
    number = _as_float(value)
    if number is None:
        return "unknown"
    if number <= 0:
        return "zero"
    if number <= 100:
        return "1-100"
    if number <= 1000:
        return "101-1000"
    if number <= 10000:
        return "1001-10000"
    return "10000+"


def _value_bucket(value: object) -> str:
    number = _as_float(value)
    if number is None:
        return "unknown"
    if number <= 0:
        return "zero"
    if number <= 10000:
        return "0-1w"
    if number <= 100000:
        return "1w-10w"
    if number <= 1000000:
        return "10w-100w"
    return "100w+"


def _as_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_hash(value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class GatewayHealth:
    """CR138 Gateway health；health 不等于账户、行情或交易授权。"""

    status: str
    request_id: str = ""
    last_heartbeat: str = ""
    degraded_reason: str = ""
    capabilities_ref: str = "capabilities:rest-only"
    runtime_authorized: bool = False
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "healthy": self.healthy,
            "request_id": self.request_id,
            "last_heartbeat": self.last_heartbeat,
            "degraded_reason": self.degraded_reason,
            "capabilities_ref": self.capabilities_ref,
            "runtime_authorized": self.runtime_authorized,
        }


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    """CR138 REST-only P0 capability snapshot。"""

    protocols: tuple[str, ...] = ("REST",)
    deferred_protocols: tuple[str, ...] = ("SSE", "WebSocket", "gRPC", "FIX")
    query_scopes: tuple[str, ...] = ("calendar:read", "commission:read", "pnl:read")
    market_scopes: tuple[str, ...] = ("market_readonly",)
    order_scopes: tuple[str, ...] = ("order_write", "submit_cancel")
    runtime_authorized: bool = False
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "protocols": list(self.protocols),
            "deferred_protocols": list(self.deferred_protocols),
            "query_scopes": list(self.query_scopes),
            "market_scopes": list(self.market_scopes),
            "order_scopes": list(self.order_scopes),
            "runtime_authorized": self.runtime_authorized,
        }


@dataclass(frozen=True, slots=True)
class TradingSession:
    session_state: str
    account_label: str = "<redacted-account-ref>"
    scope: str = "account_readonly"
    expires_at: str = ""
    blocked_reason: str = ""
    redaction_status: str = "redacted"
    adapter_calls: int = 0
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return bool(self.blocked_reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "session_state": self.session_state,
            "account_label": self.account_label,
            "scope": self.scope,
            "expires_at": self.expires_at,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "redaction_status": self.redaction_status,
            "adapter_calls": self.adapter_calls,
        }


@dataclass(frozen=True, slots=True)
class RestRouteSpec:
    endpoint_id: str
    method: str
    path: str
    group: str
    required_scope: str = ""
    runtime_authorized: bool = False
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "endpoint_id": self.endpoint_id,
            "method": self.method,
            "path": self.path,
            "group": self.group,
            "required_scope": self.required_scope,
            "runtime_authorized": self.runtime_authorized,
        }


@dataclass(frozen=True, slots=True)
class TradingCalendar:
    market: str
    date_range: str
    trading_days: tuple[str, ...]
    source: str
    freshness: str
    status: str = "available"
    unavailable_reason: str = ""
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "market": self.market,
            "date_range": self.date_range,
            "trading_days": list(self.trading_days),
            "source": self.source,
            "freshness": self.freshness,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass(frozen=True, slots=True)
class CommissionSchedule:
    instrument_type: str
    rate: float
    min_fee: float
    source: str
    authorization_ref: str = ""
    freshness: str = ""
    version: str = "commission-config-v1"
    effective_from: str = "2026-06-30"
    release_id: str = "config-facts-cr139-v1"
    slippage_bps: float = 0.0
    stamp_duty_rate: float = 0.0
    transfer_fee_rate: float = 0.0
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "instrument_type": self.instrument_type,
            "rate": self.rate,
            "min_fee": self.min_fee,
            "source": self.source,
            "authorization_ref": self.authorization_ref,
            "freshness": self.freshness,
            "version": self.version,
            "effective_from": self.effective_from,
            "release_id": self.release_id,
            "slippage_bps": self.slippage_bps,
            "stamp_duty_rate": self.stamp_duty_rate,
            "transfer_fee_rate": self.transfer_fee_rate,
        }


@dataclass(frozen=True, slots=True)
class CostEstimate:
    order_intent_ref: str
    estimated_fee: float
    source: str
    schedule_source: str
    broker_fact: bool = False
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "order_intent_ref": self.order_intent_ref,
            "estimated_fee": self.estimated_fee,
            "source": self.source,
            "schedule_source": self.schedule_source,
            "broker_fact": self.broker_fact,
        }


@dataclass(frozen=True, slots=True)
class CostPretradeGateInput:
    order_intent_ref: str
    notional: float
    side: str
    tradability_status: str
    schedule: CommissionSchedule | None = None
    cost_model_ref: str = ""
    liquidity_ref: str = ""
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "order_intent_ref": self.order_intent_ref,
            "notional": self.notional,
            "side": self.side,
            "tradability_status": self.tradability_status,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "cost_model_ref": self.cost_model_ref,
            "liquidity_ref": self.liquidity_ref,
        }


@dataclass(frozen=True, slots=True)
class CostPretradeGateDecision:
    order_intent_ref: str
    status: str
    blocked_reasons: tuple[str, ...] = ()
    estimated_total_cost: float = 0.0
    schedule_version: str = ""
    schedule_release_id: str = ""
    cost_model_ref: str = ""
    liquidity_ref: str = ""
    operation_counters: Mapping[str, int] = field(
        default_factory=lambda: {key: 0 for key in QMT_GATEWAY_FORBIDDEN_COUNTER_FIELDS}
    )
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def allowed(self) -> bool:
        return self.status == COST_PRETRADE_GATE_ALLOWED

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "order_intent_ref": self.order_intent_ref,
            "status": self.status,
            "allowed": self.allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "estimated_total_cost": self.estimated_total_cost,
            "schedule_version": self.schedule_version,
            "schedule_release_id": self.schedule_release_id,
            "cost_model_ref": self.cost_model_ref,
            "liquidity_ref": self.liquidity_ref,
            "operation_counters": dict(self.operation_counters),
        }


def evaluate_cost_pretrade_gate(
    gate_input: CostPretradeGateInput | Mapping[str, object],
) -> CostPretradeGateDecision:
    """Evaluate local cost/tradability evidence before any broker/runtime call."""

    request = _cost_gate_input(gate_input)
    schedule = request.schedule
    reasons: list[str] = []
    if schedule is None:
        reasons.append(COST_SCHEDULE_MISSING)
    elif not (schedule.version and schedule.release_id and schedule.effective_from):
        reasons.append(COST_SCHEDULE_VERSION_MISSING)
    if not request.cost_model_ref:
        reasons.append(COST_MODEL_REF_MISSING)
    if not request.liquidity_ref:
        reasons.append(LIQUIDITY_REF_MISSING)
    if str(request.tradability_status).strip().lower() not in {"available", "tradable", "pass", "ready"}:
        reasons.append(TRADABILITY_UNAVAILABLE)
    if request.notional <= 0:
        reasons.append(ORDER_NOTIONAL_INVALID)

    status = COST_PRETRADE_GATE_BLOCKED if reasons else COST_PRETRADE_GATE_ALLOWED
    return CostPretradeGateDecision(
        order_intent_ref=request.order_intent_ref,
        status=status,
        blocked_reasons=tuple(reasons),
        estimated_total_cost=0.0 if reasons or schedule is None else _estimated_pretrade_cost(request),
        schedule_version=schedule.version if schedule else "",
        schedule_release_id=schedule.release_id if schedule else "",
        cost_model_ref=request.cost_model_ref,
        liquidity_ref=request.liquidity_ref,
    )


def _cost_gate_input(value: CostPretradeGateInput | Mapping[str, object]) -> CostPretradeGateInput:
    if isinstance(value, CostPretradeGateInput):
        return value
    payload = dict(value)
    raw_schedule = payload.get("schedule")
    schedule = raw_schedule if isinstance(raw_schedule, CommissionSchedule) else None
    if schedule is None and isinstance(raw_schedule, Mapping):
        schedule = CommissionSchedule(
            instrument_type=str(raw_schedule.get("instrument_type") or ""),
            rate=float(raw_schedule.get("rate") or 0.0),
            min_fee=float(raw_schedule.get("min_fee") or 0.0),
            source=str(raw_schedule.get("source") or ""),
            authorization_ref=str(raw_schedule.get("authorization_ref") or ""),
            freshness=str(raw_schedule.get("freshness") or ""),
            version=str(raw_schedule.get("version") or ""),
            effective_from=str(raw_schedule.get("effective_from") or ""),
            release_id=str(raw_schedule.get("release_id") or ""),
            slippage_bps=float(raw_schedule.get("slippage_bps") or 0.0),
            stamp_duty_rate=float(raw_schedule.get("stamp_duty_rate") or 0.0),
            transfer_fee_rate=float(raw_schedule.get("transfer_fee_rate") or 0.0),
        )
    return CostPretradeGateInput(
        order_intent_ref=str(payload.get("order_intent_ref") or ""),
        notional=float(payload.get("notional") or 0.0),
        side=str(payload.get("side") or ""),
        tradability_status=str(payload.get("tradability_status") or ""),
        schedule=schedule,
        cost_model_ref=str(payload.get("cost_model_ref") or ""),
        liquidity_ref=str(payload.get("liquidity_ref") or ""),
    )


def _estimated_pretrade_cost(request: CostPretradeGateInput) -> float:
    schedule = request.schedule
    if schedule is None:
        return 0.0
    base_fee = max(request.notional * schedule.rate, schedule.min_fee)
    slippage = request.notional * schedule.slippage_bps / 10_000
    stamp_duty = request.notional * schedule.stamp_duty_rate if request.side.strip().lower() == "sell" else 0.0
    transfer_fee = request.notional * schedule.transfer_fee_rate
    return round(base_fee + slippage + stamp_duty + transfer_fee, 6)


@dataclass(frozen=True, slots=True)
class PnLSnapshot:
    period: str
    source: str
    realized_summary: str = ""
    unrealized_summary: str = ""
    authorization_ref: str = ""
    redaction_status: str = "redacted"
    status: str = "available"
    blocked_reason: str = ""
    adapter_calls: int = 0
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return bool(self.blocked_reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "period": self.period,
            "source": self.source,
            "realized_summary": self.realized_summary,
            "unrealized_summary": self.unrealized_summary,
            "authorization_ref": self.authorization_ref,
            "redaction_status": self.redaction_status,
            "status": self.status,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "adapter_calls": self.adapter_calls,
        }


@dataclass(frozen=True, slots=True)
class ReturnSummary:
    period: str
    return_pct: float | None
    source: str
    status: str = "available"
    unavailable_reason: str = ""
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "period": self.period,
            "return_pct": self.return_pct,
            "source": self.source,
            "status": self.status,
            "unavailable_reason": self.unavailable_reason,
        }


@dataclass(frozen=True, slots=True)
class MarketSubscription:
    subscription_id: str
    symbols: tuple[str, ...]
    period: str
    state: str
    scope_required: str = "market_readonly"
    blocked_reason: str = ""
    adapter_calls: int = 0
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return bool(self.blocked_reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "subscription_id": self.subscription_id,
            "symbols": list(self.symbols),
            "period": self.period,
            "state": self.state,
            "scope_required": self.scope_required,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "adapter_calls": self.adapter_calls,
        }


@dataclass(frozen=True, slots=True)
class GatewayCommand:
    command_id: str
    command_type: str
    scope: str
    order_intent_id: str = ""
    idempotency_key: str = ""
    audit_id: str = ""
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "command_type": self.command_type,
            "scope": self.scope,
            "order_intent_id": self.order_intent_id,
            "idempotency_key": self.idempotency_key,
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True, slots=True)
class GatewayCommandDecision:
    command_id: str
    status: str
    blocked_reason: str = ""
    local_reject: bool = True
    broker_reject: bool = False
    adapter_calls: int = 0
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def hard_rejected(self) -> bool:
        return self.status == "hard_rejected"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "command_id": self.command_id,
            "status": self.status,
            "blocked_reason": self.blocked_reason,
            "local_reject": self.local_reject,
            "broker_reject": self.broker_reject,
            "hard_rejected": self.hard_rejected,
            "adapter_calls": self.adapter_calls,
        }


@dataclass(frozen=True, slots=True)
class GatewayEvent:
    event_id: str
    event_type: str
    state: str
    payload_ref: str = ""
    audit_id: str = ""
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "state": self.state,
            "payload_ref": self.payload_ref,
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    report_id: str
    state: str
    filled_qty: int = 0
    broker_order_ref: str = "<redacted-broker-order-ref>"
    audit_id: str = ""
    redaction_status: str = "redacted"
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    @property
    def manual_takeover_required(self) -> bool:
        return self.state in {"unknown", "stale"}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "state": self.state,
            "filled_qty": self.filled_qty,
            "broker_order_ref": self.broker_order_ref,
            "audit_id": self.audit_id,
            "redaction_status": self.redaction_status,
            "manual_takeover_required": self.manual_takeover_required,
        }


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    degraded_reason: str
    manual_action: str
    cooldown_until: str = ""
    auto_retry_allowed: bool = False
    auto_unlock_allowed: bool = False
    schema_version: str = CR138_GATEWAY_SERVICE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "degraded_reason": self.degraded_reason,
            "manual_action": self.manual_action,
            "cooldown_until": self.cooldown_until,
            "auto_retry_allowed": self.auto_retry_allowed,
            "auto_unlock_allowed": self.auto_unlock_allowed,
        }
