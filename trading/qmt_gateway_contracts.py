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
