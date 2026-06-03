"""CR019-S03 的 QMT C 侧 client 离线合同。

本模块只生成 typed request / response / blocked result，不启动服务、不访问
gateway、不读取凭据、不执行交易、行情、账户或 broker lake 操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from trading.qmt_endpoint_matrix import (
    ACCOUNT_LIKE_ENDPOINTS,
    LATER_GATED_ENDPOINTS,
    QmtEndpointCategory,
    build_capabilities_payload,
    get_endpoint_spec,
    resolve_endpoint_spec,
)
from trading.qmt_gateway_contracts import (
    QmtBlockedReason,
    build_allowed_result,
    build_blocked_result,
)
from trading.qmt_transport import (
    REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    REST_GATEWAY_TRANSPORT_KIND,
    TransportErrorCode,
    build_rest_gateway_payload_metadata,
)


class QmtResponseStatus(str, Enum):
    """client 对调用方暴露的稳定结果状态。"""

    OK = "ok"
    BLOCKED = "blocked"
    TRANSPORT_ERROR = "transport_error"
    AUTH_ERROR = "auth_error"
    VALIDATION_ERROR = "validation_error"


CLIENT_SCHEMA_VERSION = "cr019-s03-qmt-client-v1"
DEFAULT_REDACTION_LABEL = "qmt-client-redacted"

FORBIDDEN_OPERATION_COUNTERS: tuple[str, ...] = (
    "dependency_change",
    "service_start",
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
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
)


@dataclass(frozen=True, slots=True)
class QmtClientSafetyCounters:
    """S03 client 必须保持为 0 的禁止操作计数。"""

    dependency_change: int = 0
    service_start: int = 0
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
    service_bind: int = 0
    http_client_call: int = 0
    gateway_socket_open: int = 0

    def to_dict(self) -> dict[str, int]:
        return {key: int(getattr(self, key)) for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class QmtRequest:
    """调用 QMT gateway contract 的最小 request。"""

    run_id: str
    endpoint: QmtEndpointCategory | str
    stage: str
    mode: str = "dry_run"
    intent_id: str = ""
    authorization_ref: str = ""
    redaction_label: str = DEFAULT_REDACTION_LABEL
    request_id: str = ""
    strategy_id: str = ""
    operator_ref: str = ""
    payload: Mapping[str, object] = field(default_factory=dict)
    timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS
    schema_version: str = CLIENT_SCHEMA_VERSION

    def to_transport_metadata(self) -> dict[str, object]:
        return {
            "transport_kind": REST_GATEWAY_TRANSPORT_KIND.value,
            "endpoint": _enum_value(self.endpoint),
            "run_id": self.run_id,
            "stage": self.stage,
            "mode": self.mode,
            "redaction_label": self.redaction_label,
            "request_id": self.request_id,
            "intent_id": self.intent_id,
            "authorization_ref": self.authorization_ref,
            "schema_version": self.schema_version,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True, slots=True)
class QmtBlockedResult:
    """调用被阻断时的 typed result。"""

    endpoint: QmtEndpointCategory | str
    run_id: str
    reason_code: QmtBlockedReason | str
    message: str
    status: QmtResponseStatus | str = QmtResponseStatus.BLOCKED
    detail_code: str = ""
    redaction_status: str = "redacted"
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_client_safety_counters()
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": _enum_value(self.status),
            "endpoint": _enum_value(self.endpoint),
            "run_id": self.run_id,
            "reason_code": _enum_value(self.reason_code),
            "detail_code": self.detail_code,
            "message": self.message,
            "redaction_status": self.redaction_status,
            "counters": dict(self.counters),
        }


@dataclass(frozen=True, slots=True)
class QmtResponse:
    """QMT client 的统一响应结构。"""

    status: QmtResponseStatus | str
    endpoint: QmtEndpointCategory | str
    run_id: str
    payload: Mapping[str, object] = field(default_factory=dict)
    blocked_result: QmtBlockedResult | None = None
    reason_code: str = ""
    message: str = ""
    redaction_status: str = "redacted"
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_client_safety_counters()
    )
    transport_metadata: Mapping[str, str] = field(default_factory=dict)
    schema_version: str = CLIENT_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return self.blocked_result is not None or _enum_value(self.status) in {
            QmtResponseStatus.BLOCKED.value,
            QmtResponseStatus.AUTH_ERROR.value,
            QmtResponseStatus.TRANSPORT_ERROR.value,
            QmtResponseStatus.VALIDATION_ERROR.value,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": _enum_value(self.status),
            "endpoint": _enum_value(self.endpoint),
            "run_id": self.run_id,
            "reason_code": self.reason_code,
            "message": self.message,
            "redaction_status": self.redaction_status,
            "payload": dict(self.payload),
            "blocked_result": (
                self.blocked_result.to_dict() if self.blocked_result is not None else None
            ),
            "counters": dict(self.counters),
            "transport_metadata": dict(self.transport_metadata),
        }


class QmtClient:
    """QMT C 侧 Python client；S03 阶段默认全部保持离线阻断。"""

    def __init__(
        self,
        *,
        gateway_available: bool = False,
        auth_available: bool = False,
        default_stage: str = "shadow",
        default_mode: str = "dry_run",
    ) -> None:
        self.gateway_available = gateway_available
        self.auth_available = auth_available
        self.default_stage = default_stage
        self.default_mode = default_mode

    def health(
        self,
        *,
        run_id: str = "qmt-health-check",
        stage: str | None = None,
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    ) -> QmtResponse:
        request = self._request(
            QmtEndpointCategory.HEALTH,
            run_id=run_id,
            stage=stage,
            timeout_seconds=timeout_seconds,
        )
        return self._transport_unavailable(request)

    def capabilities(
        self,
        *,
        run_id: str = "qmt-capabilities-check",
        stage: str | None = None,
    ) -> QmtResponse:
        request = self._request(
            QmtEndpointCategory.CAPABILITIES,
            run_id=run_id,
            stage=stage,
        )
        return self._transport_unavailable(
            request,
            payload={"capabilities": build_capabilities_payload()},
        )

    def validate_intent(self, request: QmtRequest) -> QmtResponse:
        current = self._with_endpoint(request, QmtEndpointCategory.VALIDATE_INTENT)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        spec = get_endpoint_spec(current.endpoint)
        gateway_result = build_allowed_result(
            spec.endpoint_id,
            {
                "validated": True,
                "real_operation": False,
                "operation_authorized": False,
            },
        )
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=current.endpoint,
            run_id=current.run_id,
            payload={
                "validated": True,
                "real_operation": False,
                "operation_authorized": False,
                "endpoint": _enum_value(current.endpoint),
                "endpoint_spec": spec.to_dict(),
                "gateway_result": gateway_result.to_dict(),
            },
            counters=collect_qmt_client_safety_counters(),
            transport_metadata=self._transport_metadata(current),
        )

    def dry_run(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(QmtEndpointCategory.DRY_RUN, **kwargs)
        current = self._with_endpoint(current, QmtEndpointCategory.DRY_RUN)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        spec = get_endpoint_spec(current.endpoint)
        gateway_result = build_allowed_result(
            spec.endpoint_id,
            {
                "dry_run": True,
                "mock_only": True,
                "real_operation": False,
                "operation_authorized": False,
            },
        )
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=current.endpoint,
            run_id=current.run_id,
            payload={
                "dry_run": True,
                "mock_only": True,
                "real_operation": False,
                "operation_authorized": False,
                "endpoint_spec": spec.to_dict(),
                "gateway_result": gateway_result.to_dict(),
            },
            counters=collect_qmt_client_safety_counters(),
            transport_metadata=self._transport_metadata(current),
        )

    def query_market(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(QmtEndpointCategory.MARKET_QUERY, **kwargs)
        current = self._with_endpoint(current, QmtEndpointCategory.MARKET_QUERY)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._transport_unavailable(current)

    def query_account_like(
        self,
        category: QmtEndpointCategory | str = QmtEndpointCategory.ACCOUNT_QUERY,
        request: QmtRequest | None = None,
        **kwargs: object,
    ) -> QmtResponse:
        endpoint = _coerce_endpoint(category) or QmtEndpointCategory.ACCOUNT_QUERY
        if endpoint not in ACCOUNT_LIKE_ENDPOINTS:
            return self._unsupported_endpoint(
                self._request(QmtEndpointCategory.ACCOUNT_QUERY, **kwargs),
                detail_code=_enum_value(category),
            )
        current = request or self._request(endpoint, mode="live_readonly", **kwargs)
        current = self._with_endpoint(current, endpoint)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def query_account(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        return self.query_account_like(QmtEndpointCategory.ACCOUNT_QUERY, request, **kwargs)

    def query_positions(
        self,
        request: QmtRequest | None = None,
        **kwargs: object,
    ) -> QmtResponse:
        return self.query_account_like(QmtEndpointCategory.POSITIONS, request, **kwargs)

    def query_orders(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        return self.query_account_like(QmtEndpointCategory.ORDERS, request, **kwargs)

    def query_trades(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        return self.query_account_like(QmtEndpointCategory.TRADES, request, **kwargs)

    def submit_order_intent(
        self,
        request: QmtRequest | None = None,
        *,
        endpoint: QmtEndpointCategory | str = QmtEndpointCategory.SIMULATION_SUBMIT,
        **kwargs: object,
    ) -> QmtResponse:
        category = _coerce_endpoint(endpoint) or QmtEndpointCategory.SIMULATION_SUBMIT
        current = request or self._request(category, mode="simulation", **kwargs)
        current = self._with_endpoint(current, category)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        if category in LATER_GATED_ENDPOINTS:
            return self._later_gated_block(current)
        return self._transport_unavailable(current)

    def submit_simulation(
        self,
        request: QmtRequest | None = None,
        **kwargs: object,
    ) -> QmtResponse:
        current = request or self._request(
            QmtEndpointCategory.SIMULATION_SUBMIT,
            mode="simulation",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.SIMULATION_SUBMIT)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def cancel_simulation(
        self,
        request: QmtRequest | None = None,
        **kwargs: object,
    ) -> QmtResponse:
        current = request or self._request(
            QmtEndpointCategory.SIMULATION_CANCEL,
            mode="simulation",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.SIMULATION_CANCEL)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def live_readonly_snapshot(
        self,
        request: QmtRequest | None = None,
        **kwargs: object,
    ) -> QmtResponse:
        current = request or self._request(
            QmtEndpointCategory.LIVE_READONLY,
            mode="live_readonly",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.LIVE_READONLY)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def submit_live(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(
            QmtEndpointCategory.LIVE_SUBMIT,
            mode="small_live",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.LIVE_SUBMIT)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def cancel_live(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(
            QmtEndpointCategory.LIVE_CANCEL,
            mode="small_live",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.LIVE_CANCEL)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def reconcile(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(QmtEndpointCategory.RECONCILIATION, **kwargs)
        current = self._with_endpoint(current, QmtEndpointCategory.RECONCILIATION)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def kill_switch(self, request: QmtRequest | None = None, **kwargs: object) -> QmtResponse:
        current = request or self._request(QmtEndpointCategory.KILL_SWITCH, **kwargs)
        current = self._with_endpoint(current, QmtEndpointCategory.KILL_SWITCH)
        validation_error = self._validate_required_fields(current)
        if validation_error is not None:
            return validation_error
        return self._later_gated_block(current)

    def _request(
        self,
        endpoint: QmtEndpointCategory,
        *,
        run_id: str = "qmt-client-fixture-run",
        stage: str | None = None,
        mode: str | None = None,
        intent_id: str = "",
        authorization_ref: str = "",
        redaction_label: str = DEFAULT_REDACTION_LABEL,
        request_id: str = "",
        strategy_id: str = "",
        operator_ref: str = "",
        payload: Mapping[str, object] | None = None,
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    ) -> QmtRequest:
        return QmtRequest(
            run_id=run_id,
            endpoint=endpoint,
            stage=stage or self.default_stage,
            mode=mode or self.default_mode,
            intent_id=intent_id,
            authorization_ref=authorization_ref,
            redaction_label=redaction_label,
            request_id=request_id,
            strategy_id=strategy_id,
            operator_ref=operator_ref,
            payload=payload or {},
            timeout_seconds=timeout_seconds,
        )

    def _with_endpoint(
        self,
        request: QmtRequest,
        endpoint: QmtEndpointCategory,
    ) -> QmtRequest:
        return QmtRequest(
            run_id=request.run_id,
            endpoint=endpoint,
            stage=request.stage,
            mode=request.mode,
            intent_id=request.intent_id,
            authorization_ref=request.authorization_ref,
            redaction_label=request.redaction_label,
            request_id=request.request_id,
            strategy_id=request.strategy_id,
            operator_ref=request.operator_ref,
            payload=request.payload,
            timeout_seconds=request.timeout_seconds,
            schema_version=request.schema_version,
        )

    def _validate_required_fields(self, request: QmtRequest) -> QmtResponse | None:
        if not request.run_id:
            return self._validation_error(request, "run_id is required", "run_id")
        if not request.stage:
            return self._validation_error(request, "stage is required", "stage")
        if not request.mode:
            return self._validation_error(request, "mode is required", "mode")
        if not request.redaction_label:
            return self._validation_error(
                request,
                "redaction_label is required",
                QmtBlockedReason.REDACTION_REQUIRED.value,
            )
        build_result = build_rest_gateway_payload_metadata(request.to_transport_metadata())
        if not build_result.accepted:
            return self._validation_error(
                request,
                build_result.ack.message,
                (
                    build_result.ack.error_code.value
                    if build_result.ack.error_code is not None
                    else TransportErrorCode.MALFORMED_PAYLOAD.value
                ),
            )
        return None

    def _transport_unavailable(
        self,
        request: QmtRequest,
        *,
        payload: Mapping[str, object] | None = None,
    ) -> QmtResponse:
        if self.gateway_available:
            return self._blocked(
                request,
                QmtBlockedReason.REAL_OPERATION_FORBIDDEN,
                "S03 does not authorize real gateway transport calls",
                status=QmtResponseStatus.BLOCKED,
                payload=payload,
            )
        return self._blocked(
            request,
            QmtBlockedReason.TRANSPORT_UNAVAILABLE,
            "REST gateway transport is unavailable in the S03 offline contract",
            status=QmtResponseStatus.TRANSPORT_ERROR,
            payload=payload,
        )

    def _later_gated_block(self, request: QmtRequest) -> QmtResponse:
        spec = get_endpoint_spec(request.endpoint)
        reason = spec.blocked_reason
        message = spec.blocked_cases[0].message
        return self._blocked(request, reason, message, status=QmtResponseStatus.AUTH_ERROR)

    def _unsupported_endpoint(self, request: QmtRequest, *, detail_code: str) -> QmtResponse:
        return self._blocked(
            request,
            QmtBlockedReason.ENDPOINT_NOT_SUPPORTED,
            "endpoint category is not supported by this client method",
            status=QmtResponseStatus.BLOCKED,
            detail_code=detail_code,
        )

    def _validation_error(
        self,
        request: QmtRequest,
        message: str,
        detail_code: str,
    ) -> QmtResponse:
        return self._blocked(
            request,
            QmtBlockedReason.INVALID_REQUEST,
            message,
            status=QmtResponseStatus.VALIDATION_ERROR,
            detail_code=detail_code,
        )

    def _blocked(
        self,
        request: QmtRequest,
        reason: QmtBlockedReason,
        message: str,
        *,
        status: QmtResponseStatus,
        detail_code: str = "",
        payload: Mapping[str, object] | None = None,
    ) -> QmtResponse:
        counters = collect_qmt_client_safety_counters()
        spec = resolve_endpoint_spec(request.endpoint)
        endpoint_id = spec.endpoint_id if spec is not None else _enum_value(request.endpoint)
        endpoint_payload: Mapping[str, object] = (
            spec.to_dict()
            if spec is not None
            else {
                "endpoint_id": endpoint_id,
                "category": endpoint_id,
                "blocked_reason": QmtBlockedReason.UNKNOWN_ENDPOINT.value,
            }
        )
        gateway_result = build_blocked_result(
            endpoint_id,
            reason,
            message,
            detail={"detail_code": detail_code} if detail_code else {},
        )
        response_payload = {
            "endpoint_spec": endpoint_payload,
            "gateway_result": gateway_result.to_dict(),
            "operation_authorized": False,
            "real_operation": False,
        }
        if payload is not None:
            response_payload.update(payload)
        blocked = QmtBlockedResult(
            endpoint=request.endpoint,
            run_id=request.run_id,
            reason_code=reason,
            detail_code=detail_code,
            message=message,
            counters=counters,
        )
        return QmtResponse(
            status=status,
            endpoint=request.endpoint,
            run_id=request.run_id,
            blocked_result=blocked,
            reason_code=reason.value,
            message=message,
            payload=response_payload,
            counters=counters,
            transport_metadata=self._transport_metadata(request),
        )

    def _transport_metadata(self, request: QmtRequest) -> Mapping[str, str]:
        build_result = build_rest_gateway_payload_metadata(request.to_transport_metadata())
        return build_result.sanitized_metadata


def collect_qmt_client_safety_counters(
    counters: Mapping[str, int] | QmtClientSafetyCounters | None = None,
) -> dict[str, int]:
    """归一化 S03 禁止操作计数；默认全 0。"""

    normalized = QmtClientSafetyCounters().to_dict()
    if counters is None:
        return normalized
    raw = counters.to_dict() if isinstance(counters, QmtClientSafetyCounters) else dict(counters)
    for key, value in raw.items():
        normalized[str(key)] = int(value)
    return normalized


def _coerce_endpoint(value: QmtEndpointCategory | str) -> QmtEndpointCategory | None:
    try:
        return value if isinstance(value, QmtEndpointCategory) else QmtEndpointCategory(str(value))
    except ValueError:
        return None


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)
