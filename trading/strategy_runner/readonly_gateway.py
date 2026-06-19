"""CR091/CR098 只读 gateway wrapper，默认 fake transport。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from trading.qmt_client import (
    QmtClient,
    QmtClientConfig,
    QmtResponse,
    QmtResponseStatus,
    QmtRestRequest,
    QmtTransportResult,
    collect_qmt_client_safety_counters,
)
from trading.qmt_endpoint_matrix import QmtEndpointCategory


ALLOWED_READONLY_ENDPOINTS = {"health", "capabilities", "query_positions"}


@dataclass(frozen=True, slots=True)
class ReadonlyGatewayRuntimeConfig:
    base_url: str
    authorization_ref: str
    runtime_env_ref: str
    timeout_seconds: int = 10
    transport_kind: str = "rest_gateway"

    @property
    def enabled(self) -> bool:
        return bool(self.base_url.strip() and self.authorization_ref.strip())


@dataclass(frozen=True, slots=True)
class ReadonlyGatewayResult:
    endpoint: str
    status: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    reason_code: str = ""
    operation_counters: Mapping[str, int] = field(default_factory=collect_qmt_client_safety_counters)
    transport_kind: str = "fake"
    runtime_env_ref: str = ""
    authorization_ref: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "status": self.status,
            "payload": dict(self.payload),
            "reason_code": self.reason_code,
            "operation_counters": dict(self.operation_counters),
            "transport_kind": self.transport_kind,
            "runtime_env_ref": self.runtime_env_ref,
            "authorization_ref": self.authorization_ref,
        }


class FakeReadonlyQmtTransport:
    """离线 fake transport，不打开 socket，不读取账号。"""

    def send(self, request: QmtRestRequest) -> QmtTransportResult:
        endpoint = _endpoint_name(request.endpoint)
        if endpoint == "health":
            body = {"health": "ok", "fake_transport": True, "operation_authorized": False}
        elif endpoint == "capabilities":
            body = {"capabilities": ["health", "capabilities", "query_positions"], "fake_transport": True}
        elif endpoint in {"positions", "query_positions"}:
            body = {
                "position_count": 1,
                "positions_digest": "sha256:fixture-redacted-positions",
                "items_redacted": [
                    {
                        "position_ref": "pos-ref-fixture",
                        "instrument_ref": "instrument-ref-fixture",
                        "quantity_bucket": "small",
                        "value_bucket": "fixture",
                    }
                ],
                "redaction_status": "pass",
                "raw_payload_emitted": False,
            }
        else:
            return QmtTransportResult(
                status="blocked",
                status_code=403,
                body={"reason_code": "scope_denied"},
                message="endpoint scope denied by CR091 readonly wrapper",
            )
        return QmtTransportResult(status="ok", status_code=200, body=body)


class ReadonlyGatewayClient:
    """只允许 health / capabilities / query_positions 的 broker-neutral wrapper。"""

    def __init__(
        self,
        client: QmtClient | None = None,
        transport: FakeReadonlyQmtTransport | None = None,
        runtime_config: ReadonlyGatewayRuntimeConfig | None = None,
    ) -> None:
        self.transport = transport or FakeReadonlyQmtTransport()
        self.client = client
        self.runtime_config = runtime_config

    def call(self, endpoint: str, *, run_id: str) -> ReadonlyGatewayResult:
        if endpoint not in ALLOWED_READONLY_ENDPOINTS:
            return ReadonlyGatewayResult(
                endpoint=endpoint,
                status="blocked",
                reason_code="blocked_scope_denied",
            )
        if self.client is not None:
            return self._call_qmt_client(endpoint, run_id=run_id)
        return self._call_fake_transport(endpoint, run_id=run_id)

    @classmethod
    def from_transport(
        cls,
        *,
        base_url: str,
        authorization_ref: str,
        runtime_env_ref: str,
        transport: object,
        auth_header_provider: object,
        timeout_seconds: int = 10,
    ) -> "ReadonlyGatewayClient":
        runtime_config = ReadonlyGatewayRuntimeConfig(
            base_url=base_url,
            authorization_ref=authorization_ref,
            runtime_env_ref=runtime_env_ref,
            timeout_seconds=timeout_seconds,
        )
        client = QmtClient(
            config=QmtClientConfig(
                base_url=base_url,
                default_stage="manual_cp7",
                default_mode="live_readonly",
                default_timeout_seconds=timeout_seconds,
            ),
            transport=transport,  # type: ignore[arg-type]
            auth_header_provider=auth_header_provider,  # type: ignore[arg-type]
        )
        return cls(client=client, runtime_config=runtime_config)

    def _call_fake_transport(self, endpoint: str, *, run_id: str) -> ReadonlyGatewayResult:
        request_endpoint = QmtEndpointCategory.POSITIONS if endpoint == "query_positions" else endpoint
        result = self.transport.send(
            QmtRestRequest(
                endpoint=request_endpoint,
                method="GET" if endpoint != "query_positions" else "POST",
                path=f"/offline/{endpoint}",
                base_url="",
                run_id=run_id,
                stage="shadow",
                mode="dry_run",
                required_scope="qmt:positions:read" if endpoint == "query_positions" else f"qmt:{endpoint}",
            )
        )
        status = "ok" if result.status == "ok" else "blocked"
        return ReadonlyGatewayResult(
            endpoint=endpoint,
            status=status,
            payload=dict(result.body),
            reason_code=str(result.body.get("reason_code", "")),
            operation_counters=result.counters,
            transport_kind="fake",
        )

    def _call_qmt_client(self, endpoint: str, *, run_id: str) -> ReadonlyGatewayResult:
        if self.runtime_config is None or not self.runtime_config.enabled:
            return ReadonlyGatewayResult(
                endpoint=endpoint,
                status="blocked",
                reason_code="blocked_runtime_authorization_missing",
                payload={
                    "operation_authorized": False,
                    "real_operation": False,
                    "runtime_env_ref": _safe_runtime_env_ref(self.runtime_config),
                },
                transport_kind="qmt_client",
                runtime_env_ref=_safe_runtime_env_ref(self.runtime_config),
                authorization_ref="" if self.runtime_config is None else self.runtime_config.authorization_ref,
            )
        if endpoint == "health":
            response = self.client.health(
                run_id=run_id,
                authorization_ref=self.runtime_config.authorization_ref,
                timeout_seconds=self.runtime_config.timeout_seconds,
            )
        elif endpoint == "capabilities":
            response = self.client.capabilities(
                run_id=run_id,
                authorization_ref=self.runtime_config.authorization_ref,
                timeout_seconds=self.runtime_config.timeout_seconds,
            )
        else:
            response = self.client.query_positions(
                run_id=run_id,
                authorization_ref=self.runtime_config.authorization_ref,
                timeout_seconds=self.runtime_config.timeout_seconds,
            )
        return _readonly_result_from_qmt_response(
            endpoint,
            response,
            runtime_config=self.runtime_config,
        )

    def health(self, *, run_id: str) -> ReadonlyGatewayResult:
        return self.call("health", run_id=run_id)

    def capabilities(self, *, run_id: str) -> ReadonlyGatewayResult:
        return self.call("capabilities", run_id=run_id)

    def query_positions(self, *, run_id: str) -> ReadonlyGatewayResult:
        return self.call("query_positions", run_id=run_id)

def _endpoint_name(endpoint: object) -> str:
    if endpoint is QmtEndpointCategory.POSITIONS:
        return "positions"
    return str(getattr(endpoint, "value", endpoint))


def _readonly_result_from_qmt_response(
    endpoint: str,
    response: QmtResponse,
    *,
    runtime_config: ReadonlyGatewayRuntimeConfig,
) -> ReadonlyGatewayResult:
    status = "ok" if response.status == QmtResponseStatus.OK else "blocked"
    return ReadonlyGatewayResult(
        endpoint=endpoint,
        status=status,
        payload=_readonly_payload(endpoint, response.payload),
        reason_code=response.reason_code,
        operation_counters=response.counters,
        transport_kind=runtime_config.transport_kind,
        runtime_env_ref=runtime_config.runtime_env_ref,
        authorization_ref=runtime_config.authorization_ref,
    )


def _readonly_payload(endpoint: str, payload: Mapping[str, object]) -> dict[str, object]:
    if endpoint == "query_positions":
        current = payload.get("query_positions")
        if not isinstance(current, Mapping):
            current = payload
        items = current.get("items_redacted")
        return {
            "position_count": int(current.get("position_count", 0) or 0),
            "positions_digest": str(current.get("positions_digest", "")),
            "items_redacted_count": len(items) if isinstance(items, list) else int(current.get("items_redacted_count", 0) or 0),
            "redaction_status": str(current.get("redaction_status", "redacted")),
            "raw_payload_emitted": bool(current.get("raw_payload_emitted", False)),
            "operation_authorized": bool(payload.get("operation_authorized", False)),
            "real_operation": bool(payload.get("real_operation", False)),
        }
    if endpoint == "capabilities":
        capabilities = payload.get("capabilities", [])
        if isinstance(capabilities, Mapping):
            capabilities = capabilities.get("capabilities", [])
        return {
            "capabilities": list(capabilities) if isinstance(capabilities, list | tuple) else [],
            "operation_authorized": bool(payload.get("operation_authorized", False)),
            "real_operation": bool(payload.get("real_operation", False)),
        }
    return {
        "health": str(payload.get("health", payload.get("status", "ok"))),
        "operation_authorized": bool(payload.get("operation_authorized", False)),
        "real_operation": bool(payload.get("real_operation", False)),
    }


def _safe_runtime_env_ref(runtime_config: ReadonlyGatewayRuntimeConfig | None) -> str:
    if runtime_config is None:
        return ""
    return runtime_config.runtime_env_ref
