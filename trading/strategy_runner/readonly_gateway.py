"""CR091 只读 gateway wrapper，默认 fake transport。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from trading.qmt_client import (
    QmtClient,
    QmtRestRequest,
    QmtTransportResult,
    collect_qmt_client_safety_counters,
)
from trading.qmt_endpoint_matrix import QmtEndpointCategory


ALLOWED_READONLY_ENDPOINTS = {"health", "capabilities", "query_positions"}


@dataclass(frozen=True, slots=True)
class ReadonlyGatewayResult:
    endpoint: str
    status: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    reason_code: str = ""
    operation_counters: Mapping[str, int] = field(default_factory=collect_qmt_client_safety_counters)

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

    def __init__(self, client: QmtClient | None = None, transport: FakeReadonlyQmtTransport | None = None) -> None:
        self.transport = transport or FakeReadonlyQmtTransport()
        self.client = client or QmtClient(
            transport=self.transport,
            gateway_available=True,
            auth_available=False,
        )

    def call(self, endpoint: str, *, run_id: str) -> ReadonlyGatewayResult:
        if endpoint not in ALLOWED_READONLY_ENDPOINTS:
            return ReadonlyGatewayResult(
                endpoint=endpoint,
                status="blocked",
                reason_code="blocked_scope_denied",
            )
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
