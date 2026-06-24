"""CR019-S03 的 QMT C 侧 client 离线合同。

本模块只生成 typed request / response / blocked result，不启动服务、不访问
gateway、不读取凭据、不执行交易、行情、账户或 broker lake 操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import hashlib
import json
from typing import Protocol, Mapping

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
class QmtClientConfig:
    """CR020 C 端 REST client 配置；不得从环境变量或文件隐式读取。"""

    base_url: str = ""
    default_timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS
    default_stage: str = "shadow"
    default_mode: str = "dry_run"
    redaction_label: str = DEFAULT_REDACTION_LABEL
    allow_simulation_transport: bool = False

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.strip().rstrip("/")


@dataclass(frozen=True, slots=True)
class QmtRetryPolicy:
    """REST client 的保守 retry 合同；positions 默认不自动 retry。"""

    max_attempts: int = 1
    retry_on: tuple[str, ...] = ("transport_timeout", "gateway_unavailable")

    def attempts_for(self, endpoint: QmtEndpointCategory | str) -> int:
        category = _coerce_endpoint(endpoint)
        if category is QmtEndpointCategory.POSITIONS:
            return 1
        if category in {QmtEndpointCategory.HEALTH, QmtEndpointCategory.CAPABILITIES}:
            return max(1, min(int(self.max_attempts), 2))
        return 1

    def should_retry(self, reason_code: str) -> bool:
        return reason_code in set(self.retry_on)


@dataclass(frozen=True, slots=True)
class QmtRestRequest:
    """发送给可注入 REST transport 的脱敏 request 合同。"""

    endpoint: QmtEndpointCategory | str
    method: str
    path: str
    base_url: str
    run_id: str
    stage: str
    mode: str
    request_id: str = ""
    intent_id: str = ""
    authorization_ref: str = ""
    redaction_label: str = DEFAULT_REDACTION_LABEL
    required_scope: str = ""
    payload: Mapping[str, object] = field(default_factory=dict)
    body: bytes = b""
    headers: Mapping[str, str] = field(default_factory=dict)
    timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS
    schema_version: str = CLIENT_SCHEMA_VERSION
    transport_metadata: Mapping[str, str] = field(default_factory=dict)

    def to_transport_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {
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
        metadata.update(dict(self.transport_metadata))
        return metadata


@dataclass(frozen=True, slots=True)
class QmtTransportResult:
    """REST transport 返回给 client 的结构化结果。"""

    status: str
    status_code: int = 0
    body: Mapping[str, object] = field(default_factory=dict)
    error_code: str = ""
    message: str = ""
    elapsed_ms: int = 0
    attempts: int = 1
    redaction_status: str = "redacted"
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_client_safety_counters()
    )


class QmtRestTransport(Protocol):
    """可注入 REST transport；S03 默认不提供真实 HTTP 实现。"""

    def send(self, request: QmtRestRequest) -> QmtTransportResult | Mapping[str, object]:
        ...


class QmtAuthHeaderProvider(Protocol):
    """S04 拥有的 HMAC / scope header provider；S03 只消费输出。"""

    def build_headers(self, request: QmtRestRequest) -> Mapping[str, str]:
        ...


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
    """QMT C 侧 Python REST client；默认无授权 transport 时 fail-closed。"""

    def __init__(
        self,
        *,
        config: QmtClientConfig | None = None,
        transport: QmtRestTransport | None = None,
        auth_header_provider: QmtAuthHeaderProvider | None = None,
        retry_policy: QmtRetryPolicy | None = None,
        gateway_available: bool = False,
        auth_available: bool = False,
        default_stage: str = "shadow",
        default_mode: str = "dry_run",
    ) -> None:
        self.config = config or QmtClientConfig(
            default_stage=default_stage,
            default_mode=default_mode,
        )
        self.transport = transport
        self.auth_header_provider = auth_header_provider
        self.retry_policy = retry_policy or QmtRetryPolicy()
        self.gateway_available = gateway_available
        self.auth_available = auth_available
        self.default_stage = self.config.default_stage
        self.default_mode = self.config.default_mode

    def health(
        self,
        *,
        run_id: str = "qmt-health-check",
        stage: str | None = None,
        request_id: str = "",
        authorization_ref: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    ) -> QmtResponse:
        request = self._request(
            QmtEndpointCategory.HEALTH,
            run_id=run_id,
            stage=stage,
            request_id=request_id,
            authorization_ref=authorization_ref,
            timeout_seconds=timeout_seconds,
        )
        return self._send_rest_request(request)

    def capabilities(
        self,
        *,
        run_id: str = "qmt-capabilities-check",
        stage: str | None = None,
        request_id: str = "",
        authorization_ref: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    ) -> QmtResponse:
        request = self._request(
            QmtEndpointCategory.CAPABILITIES,
            run_id=run_id,
            stage=stage,
            request_id=request_id,
            authorization_ref=authorization_ref,
            timeout_seconds=timeout_seconds,
        )
        return self._send_rest_request(
            request,
            fallback_payload={"capabilities": build_capabilities_payload()},
        )

    def diagnostics(
        self,
        *,
        run_id: str = "qmt-client-diagnostics",
        stage: str | None = None,
        request_id: str = "",
        timeout_seconds: int = REST_GATEWAY_DEFAULT_TIMEOUT_SECONDS,
    ) -> QmtResponse:
        request = self._request(
            QmtEndpointCategory.HEALTH,
            run_id=run_id,
            stage=stage,
            request_id=request_id,
            timeout_seconds=timeout_seconds,
        )
        validation_error = self._validate_required_fields(request)
        if validation_error is not None:
            return validation_error
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=QmtEndpointCategory.HEALTH,
            run_id=request.run_id,
            payload={
                "diagnostics": True,
                "base_url_configured": bool(self.config.normalized_base_url),
                "base_url_ref": _redacted_ref(self.config.normalized_base_url, "base_url"),
                "transport_configured": self.transport is not None,
                "auth_provider_configured": self.auth_header_provider is not None,
                "default_timeout_seconds": self.config.default_timeout_seconds,
                "retry_max_attempts": self.retry_policy.max_attempts,
                "retry_on": list(self.retry_policy.retry_on),
                "operation_authorized": False,
                "real_operation": False,
            },
            counters=collect_qmt_client_safety_counters(),
            transport_metadata=self._transport_metadata(request),
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
        current = request or self._request(
            QmtEndpointCategory.POSITIONS,
            mode="live_readonly",
            **kwargs,
        )
        current = self._with_endpoint(current, QmtEndpointCategory.POSITIONS)
        return self._send_rest_request(current)

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
        if self.config.allow_simulation_transport:
            return self._send_rest_request(current)
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
        if self.config.allow_simulation_transport:
            return self._send_rest_request(current)
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

    def _send_rest_request(
        self,
        request: QmtRequest,
        *,
        fallback_payload: Mapping[str, object] | None = None,
    ) -> QmtResponse:
        validation_error = self._validate_required_fields(request)
        if validation_error is not None:
            return validation_error
        if not self.config.normalized_base_url or self.transport is None:
            return self._transport_unavailable(request, payload=fallback_payload)

        rest_request = self._build_rest_request(request)
        auth_result = self._attach_auth_headers(rest_request, request)
        if isinstance(auth_result, QmtResponse):
            return auth_result
        rest_request = auth_result

        max_attempts = self.retry_policy.attempts_for(request.endpoint)
        last_response: QmtResponse | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                raw_result = self.transport.send(rest_request)
            except Exception as exc:  # pragma: no cover
                raw_result = QmtTransportResult(
                    status="error",
                    error_code="gateway_unavailable",
                    message=f"REST transport 抛出异常: {type(exc).__name__}",
                    attempts=attempt,
                )
            response = self._normalize_transport_result(
                request,
                rest_request,
                raw_result,
                attempt=attempt,
            )
            last_response = response
            if not response.blocked or not self.retry_policy.should_retry(response.reason_code):
                return response
            if attempt >= max_attempts:
                return response
        return last_response or self._transport_unavailable(request, payload=fallback_payload)

    def _build_rest_request(self, request: QmtRequest) -> QmtRestRequest:
        spec = get_endpoint_spec(request.endpoint)
        body = _json_payload_bytes(
            {
                "run_id": request.run_id,
                "request_id": request.request_id,
                "intent_id": request.intent_id,
                "authorization_ref": request.authorization_ref,
                "redaction_label": request.redaction_label,
                "payload": dict(request.payload),
            }
        )
        return QmtRestRequest(
            endpoint=request.endpoint,
            method=spec.method,
            path=spec.path,
            base_url=self.config.normalized_base_url,
            run_id=request.run_id,
            stage=request.stage,
            mode=request.mode,
            request_id=request.request_id,
            intent_id=request.intent_id,
            authorization_ref=request.authorization_ref,
            redaction_label=request.redaction_label,
            required_scope=spec.required_scope,
            payload=request.payload,
            body=body,
            timeout_seconds=request.timeout_seconds,
            schema_version=request.schema_version,
        )

    def _attach_auth_headers(
        self,
        rest_request: QmtRestRequest,
        original_request: QmtRequest,
    ) -> QmtRestRequest | QmtResponse:
        if self.auth_header_provider is None:
            return self._auth_error(
                original_request,
                "CR020 REST client 需要 auth header provider",
                TransportErrorCode.AUTH_REQUIRED.value,
            )
        try:
            headers = dict(self.auth_header_provider.build_headers(rest_request))
        except Exception as exc:  # pragma: no cover
            return self._auth_error(
                original_request,
                f"auth header provider 执行失败: {type(exc).__name__}",
                TransportErrorCode.AUTH_FAILED.value,
            )
        if not headers:
            return self._auth_error(
                original_request,
                "CR020 REST client 需要 auth headers",
                TransportErrorCode.AUTH_REQUIRED.value,
            )
        blocked_reason = str(headers.get("blocked_reason", "") or headers.get("reason_code", ""))
        if blocked_reason:
            return self._auth_error(
                original_request,
                "auth header provider 阻断请求",
                blocked_reason,
            )
        return replace(
            rest_request,
            headers=headers,
            transport_metadata=_auth_headers_to_metadata(headers),
        )

    def _normalize_transport_result(
        self,
        request: QmtRequest,
        rest_request: QmtRestRequest,
        raw_result: QmtTransportResult | Mapping[str, object],
        *,
        attempt: int,
    ) -> QmtResponse:
        result = _coerce_transport_result(raw_result, attempt=attempt)
        reason_code = _reason_from_transport(result, result.body)
        body = _redact_object(result.body)
        transport_metadata = self._transport_metadata(
            rest_request,
            extra={
                "attempts": str(attempt),
                "status_code": str(result.status_code),
                "elapsed_ms": str(result.elapsed_ms),
                "transport_status": result.status,
            },
        )
        if reason_code:
            return self._blocked(
                request,
                reason_code,
                result.message or _message_from_body(body) or f"REST 结果被阻断: {reason_code}",
                status=_status_for_reason(reason_code),
                detail_code=result.error_code,
                payload={
                    "gateway_body": body,
                    "attempts": attempt,
                    "operation_authorized": False,
                    "real_operation": False,
                },
                transport_metadata=transport_metadata,
            )

        payload = _success_payload_from_body(body)
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=request.endpoint,
            run_id=request.run_id,
            payload={
                **payload,
                "operation_authorized": bool(payload.get("operation_authorized", False)),
                "real_operation": bool(payload.get("real_operation", False)),
                "gateway_result": body,
                "attempts": attempt,
            },
            redaction_status=result.redaction_status,
            counters=collect_qmt_client_safety_counters(result.counters),
            transport_metadata=transport_metadata,
        )

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

    def _auth_error(
        self,
        request: QmtRequest,
        message: str,
        detail_code: str,
    ) -> QmtResponse:
        return self._blocked(
            request,
            detail_code or QmtBlockedReason.AUTH_REQUIRED,
            message,
            status=QmtResponseStatus.AUTH_ERROR,
            detail_code=detail_code,
        )

    def _blocked(
        self,
        request: QmtRequest,
        reason: QmtBlockedReason | str,
        message: str,
        *,
        status: QmtResponseStatus,
        detail_code: str = "",
        payload: Mapping[str, object] | None = None,
        transport_metadata: Mapping[str, str] | None = None,
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
            reason_code=_enum_value(reason),
            message=message,
            payload=response_payload,
            counters=counters,
            transport_metadata=transport_metadata or self._transport_metadata(request),
        )

    def _transport_metadata(
        self,
        request: QmtRequest | QmtRestRequest,
        *,
        extra: Mapping[str, str] | None = None,
    ) -> Mapping[str, str]:
        build_result = build_rest_gateway_payload_metadata(request.to_transport_metadata())
        metadata = dict(build_result.sanitized_metadata)
        if extra:
            metadata.update({str(key): str(value) for key, value in extra.items()})
        return metadata


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


def _coerce_transport_result(
    raw_result: QmtTransportResult | Mapping[str, object],
    *,
    attempt: int,
) -> QmtTransportResult:
    if isinstance(raw_result, QmtTransportResult):
        return replace(raw_result, attempts=attempt)
    body = raw_result.get("body", {})
    return QmtTransportResult(
        status=str(raw_result.get("status", "")),
        status_code=int(raw_result.get("status_code", 0) or 0),
        body=body if isinstance(body, Mapping) else {"raw_body": str(body)},
        error_code=str(raw_result.get("error_code", "")),
        message=str(raw_result.get("message", "")),
        elapsed_ms=int(raw_result.get("elapsed_ms", 0) or 0),
        attempts=attempt,
        redaction_status=str(raw_result.get("redaction_status", "redacted")),
        counters=collect_qmt_client_safety_counters(
            raw_result.get("counters") if isinstance(raw_result.get("counters"), Mapping) else None
        ),
    )


def _reason_from_transport(
    result: QmtTransportResult,
    body: Mapping[str, object],
) -> str:
    error_code = _normalize_reason(result.error_code)
    if error_code:
        return error_code
    status_code = result.status_code
    if status_code == 401:
        return TransportErrorCode.AUTH_FAILED.value
    if status_code == 403:
        return QmtBlockedReason.SCOPE_DENIED.value
    if status_code in {408, 504}:
        return "transport_timeout"
    if status_code >= 500:
        return "gateway_unavailable"

    body_status = str(body.get("status", "")).lower()
    if _session_not_ready(body):
        return "session_not_ready"
    if _redaction_failed(body) or result.redaction_status in {"failed", "redaction_failed"}:
        return QmtBlockedReason.REDACTION_FAILED.value
    if body_status in {"blocked", "rejected", "error"}:
        reason = str(
            body.get("blocked_reason")
            or body.get("reason_code")
            or body.get("error_code")
            or ""
        )
        error = body.get("error")
        if isinstance(error, Mapping):
            reason = reason or str(error.get("blocked_reason") or error.get("code") or "")
        return _normalize_reason(reason) or "gateway_unavailable"

    result_status = result.status.lower()
    if result_status in {"blocked", "rejected", "error", "timeout", "unavailable"}:
        if result_status == "timeout":
            return "transport_timeout"
        return "gateway_unavailable"
    return ""


def _normalize_reason(reason: str) -> str:
    value = reason.strip()
    mapping = {
        TransportErrorCode.REST_GATEWAY_UNAVAILABLE.value: "gateway_unavailable",
        TransportErrorCode.REST_GATEWAY_TIMEOUT.value: "transport_timeout",
        "timeout": "transport_timeout",
        "rest_gateway_timeout": "transport_timeout",
        "rest_gateway_unavailable": "gateway_unavailable",
        "transport_unavailable": QmtBlockedReason.TRANSPORT_UNAVAILABLE.value,
        "scope_insufficient": QmtBlockedReason.SCOPE_DENIED.value,
        "scope_denied": QmtBlockedReason.SCOPE_DENIED.value,
    }
    return mapping.get(value, value)


def _status_for_reason(reason_code: str) -> QmtResponseStatus:
    if reason_code in {
        "gateway_unavailable",
        "transport_timeout",
        QmtBlockedReason.TRANSPORT_UNAVAILABLE.value,
    }:
        return QmtResponseStatus.TRANSPORT_ERROR
    if reason_code in {
        TransportErrorCode.AUTH_REQUIRED.value,
        TransportErrorCode.AUTH_FAILED.value,
        QmtBlockedReason.AUTH_REQUIRED.value,
        QmtBlockedReason.AUTH_FAILED.value,
    } or reason_code.startswith("auth_"):
        return QmtResponseStatus.AUTH_ERROR
    if reason_code == QmtBlockedReason.INVALID_REQUEST.value:
        return QmtResponseStatus.VALIDATION_ERROR
    return QmtResponseStatus.BLOCKED


def _success_payload_from_body(body: Mapping[str, object]) -> dict[str, object]:
    allowed_payload = body.get("allowed_payload")
    if isinstance(allowed_payload, Mapping):
        data = allowed_payload.get("data")
        if isinstance(data, Mapping):
            payload = dict(data)
        else:
            payload = {"data": data} if data is not None else {}
        for key in ("operation_authorized", "fixture_only", "real_operation"):
            if key in allowed_payload:
                payload[key] = allowed_payload[key]
        return payload
    payload = body.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    if "data" in body and isinstance(body["data"], Mapping):
        return dict(body["data"])  # type: ignore[index]
    return dict(body)


def _message_from_body(body: Mapping[str, object]) -> str:
    message = str(body.get("message", ""))
    error = body.get("error")
    if message or not isinstance(error, Mapping):
        return message
    return str(error.get("message", ""))


def _session_not_ready(body: Mapping[str, object]) -> bool:
    if body.get("session_ready") is False:
        return True
    allowed_payload = body.get("allowed_payload")
    if isinstance(allowed_payload, Mapping):
        data = allowed_payload.get("data")
        if isinstance(data, Mapping) and data.get("session_ready") is False:
            return True
    payload = body.get("payload")
    return isinstance(payload, Mapping) and payload.get("session_ready") is False


def _redaction_failed(body: Mapping[str, object]) -> bool:
    statuses = {
        str(body.get("redaction_status", "")),
        str(body.get("redaction", "")),
    }
    error = body.get("error")
    if isinstance(error, Mapping):
        statuses.add(str(error.get("redaction_status", "")))
        statuses.add(str(error.get("code", "")))
    return bool(statuses & {"failed", "redaction_failed", "redaction_required"})


def _redact_object(value: object) -> object:
    if isinstance(value, Mapping):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            key_str = str(key)
            if _sensitive_key_or_value(key_str):
                redacted[key_str] = "[REDACTED]"
            else:
                redacted[key_str] = _redact_object(item)
        return redacted
    if isinstance(value, list):
        return [_redact_object(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_object(item) for item in value)
    if _sensitive_key_or_value(value):
        return "[REDACTED]"
    return value


def _sensitive_key_or_value(value: object) -> bool:
    normalized = str(value).lower()
    markers = (
        ".env",
        "account",
        "token",
        "session",
        "cookie",
        "password",
        "secret",
        "private_key",
        "credential",
        "signature=",
    )
    return any(marker in normalized for marker in markers)


def _json_payload_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _auth_headers_to_metadata(headers: Mapping[str, str]) -> dict[str, str]:
    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    metadata: dict[str, str] = {}
    client_ref = normalized.get("client_id_ref") or _redacted_ref(
        normalized.get("x-qmt-client-id", ""),
        "client_id",
    )
    nonce_ref = normalized.get("nonce_ref") or _redacted_ref(
        normalized.get("x-qmt-nonce", ""),
        "nonce",
    )
    signature_ref = normalized.get("signature_ref") or _redacted_ref(
        normalized.get("x-qmt-signature", ""),
        "signature",
    )
    timestamp = normalized.get("timestamp_utc") or normalized.get("x-qmt-timestamp", "")
    if client_ref:
        metadata["client_id_ref"] = _safe_ref_value(client_ref, "client_id")
    if timestamp:
        metadata["timestamp_utc"] = timestamp
    if nonce_ref:
        metadata["nonce_ref"] = _safe_ref_value(nonce_ref, "nonce")
    if signature_ref:
        metadata["signature_ref"] = _safe_ref_value(signature_ref, "signature")
    return metadata


def _safe_ref_value(value: str, label: str) -> str:
    return _redacted_ref(value, label) if _sensitive_key_or_value(value) else value


def _redacted_ref(value: str, label: str) -> str:
    if not value:
        return ""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{label}_ref:{digest}"


def _coerce_endpoint(value: QmtEndpointCategory | str) -> QmtEndpointCategory | None:
    try:
        return value if isinstance(value, QmtEndpointCategory) else QmtEndpointCategory(str(value))
    except ValueError:
        return None


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)
