from __future__ import annotations

import ast
import io
import json
from pathlib import Path

from trading.qmt_client import (
    QmtBlockedReason,
    QmtClient,
    QmtEndpointCategory,
    QmtRequest,
    QmtResponse,
    QmtResponseStatus,
    collect_qmt_client_safety_counters,
)
from trading.qmt_cli import run_qmt_cli
from trading.qmt_environment import scan_forbidden_broker_imports
from trading.qmt_transport import (
    REST_GATEWAY_AUTH_HEADER_SLOTS,
    REST_GATEWAY_PAYLOAD_METADATA_FIELDS,
    REST_GATEWAY_TRANSPORT_ERROR_CODES,
    REST_GATEWAY_TRANSPORT_KIND,
    TransportErrorCode,
    TransportKind,
    TransportStatus,
    build_rest_gateway_payload_metadata,
    rest_gateway_timeout_ack,
)


S03_SOURCE_PATHS = (
    Path("trading/qmt_client.py"),
    Path("trading/qmt_cli.py"),
    Path("trading/qmt_transport.py"),
)

REQUIRED_ZERO_COUNTERS = {
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
}


def _request(
    endpoint: QmtEndpointCategory,
    *,
    mode: str = "dry_run",
    authorization_ref: str = "",
) -> QmtRequest:
    return QmtRequest(
        run_id="run-cr019-s03-fixture",
        endpoint=endpoint,
        stage="shadow",
        mode=mode,
        intent_id="intent-cr019-s03-fixture",
        authorization_ref=authorization_ref,
        redaction_label="fixture-redacted",
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _assert_typed_blocked(response: QmtResponse, reason: QmtBlockedReason) -> None:
    assert response.blocked is True
    assert response.blocked_result is not None
    assert response.reason_code == reason.value
    assert response.blocked_result.reason_code == reason
    assert response.blocked_result.redaction_status == "redacted"
    _assert_zero_counters(response.counters)
    _assert_zero_counters(response.blocked_result.counters)


def test_cside_sources_have_zero_forbidden_broker_imports() -> None:
    scan = scan_forbidden_broker_imports(S03_SOURCE_PATHS)
    assert scan.passed is True
    assert scan.violation_count == 0
    _assert_zero_counters(collect_qmt_client_safety_counters())


def test_cside_sources_do_not_import_service_or_network_modules() -> None:
    forbidden_import_roots = {
        "fastapi",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "uvicorn",
    }
    imports: list[str] = []
    for path in (Path("trading/qmt_client.py"), Path("trading/qmt_cli.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)


class _FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def health(self, **kwargs: object) -> QmtResponse:
        self.calls.append(("health", kwargs))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=QmtEndpointCategory.HEALTH,
            run_id=str(kwargs["run_id"]),
            payload={"source": "fake-client"},
        )

    def capabilities(self, **kwargs: object) -> QmtResponse:
        self.calls.append(("capabilities", kwargs))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=QmtEndpointCategory.CAPABILITIES,
            run_id=str(kwargs["run_id"]),
            payload={"source": "fake-client"},
        )

    def query_market(self, request: QmtRequest) -> QmtResponse:
        self.calls.append(("query_market", request))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=request.endpoint,
            run_id=request.run_id,
            payload={"source": "fake-client"},
        )


def test_cli_reuses_injected_client_and_does_not_build_business_result() -> None:
    fake = _FakeClient()
    output = io.StringIO()

    exit_code = run_qmt_cli(
        ["health", "--run-id", "run-cli-fixture"],
        client_factory=lambda: fake,
        output_stream=output,
    )
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert fake.calls == [
        (
            "health",
            {
                "run_id": "run-cli-fixture",
                "stage": "shadow",
                "timeout_seconds": 3,
            },
        )
    ]
    assert payload["payload"] == {"source": "fake-client"}
    assert payload["status"] == "ok"

    output = io.StringIO()
    exit_code = run_qmt_cli(
        ["query-market", "--run-id", "run-cli-query", "--intent-id", "intent-001"],
        client_factory=lambda: fake,
        output_stream=output,
    )
    payload = json.loads(output.getvalue())

    assert exit_code == 0
    assert fake.calls[-1][0] == "query_market"
    request = fake.calls[-1][1]
    assert isinstance(request, QmtRequest)
    assert request.endpoint is QmtEndpointCategory.MARKET_QUERY
    assert payload["payload"] == {"source": "fake-client"}


def test_client_returns_typed_blocked_result_for_core_endpoint_groups() -> None:
    client = QmtClient()

    _assert_typed_blocked(
        client.health(run_id="run-health-fixture"),
        QmtBlockedReason.TRANSPORT_UNAVAILABLE,
    )
    _assert_typed_blocked(
        client.capabilities(run_id="run-capabilities-fixture"),
        QmtBlockedReason.TRANSPORT_UNAVAILABLE,
    )
    _assert_typed_blocked(
        client.query_market(_request(QmtEndpointCategory.MARKET_QUERY)),
        QmtBlockedReason.TRANSPORT_UNAVAILABLE,
    )
    _assert_typed_blocked(
        client.submit_order_intent(_request(QmtEndpointCategory.SIMULATION_SUBMIT)),
        QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
    )
    _assert_typed_blocked(
        client.submit_order_intent(
            _request(QmtEndpointCategory.LIVE_SUBMIT, mode="small_live"),
            endpoint=QmtEndpointCategory.LIVE_SUBMIT,
        ),
        QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
    )


def test_later_gated_endpoints_default_blocked_and_real_operation_counters_are_zero(
) -> None:
    client = QmtClient()

    responses = [
        client.query_account_like(
            QmtEndpointCategory.ACCOUNT_QUERY,
            _request(QmtEndpointCategory.ACCOUNT_QUERY, mode="live_readonly"),
        ),
        client.query_account_like(
            QmtEndpointCategory.POSITIONS,
            _request(QmtEndpointCategory.POSITIONS, mode="live_readonly"),
        ),
        client.submit_order_intent(
            _request(QmtEndpointCategory.LIVE_CANCEL, mode="small_live"),
            endpoint=QmtEndpointCategory.LIVE_CANCEL,
        ),
        client.reconcile(_request(QmtEndpointCategory.RECONCILIATION)),
        client.kill_switch(_request(QmtEndpointCategory.KILL_SWITCH)),
    ]

    for response in responses:
        _assert_typed_blocked(
            response,
            QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        )

    counters = collect_qmt_client_safety_counters()
    _assert_zero_counters(counters)
    assert counters["real_order"] == 0
    assert counters["real_cancel"] == 0
    assert counters["account_query"] == 0
    assert counters["qmt_api_call"] == 0


def test_rest_gateway_transport_contract_exists_without_file_drop_regression() -> None:
    required_metadata = {
        "endpoint",
        "run_id",
        "stage",
        "mode",
        "redaction_label",
    }

    assert REST_GATEWAY_TRANSPORT_KIND is TransportKind.REST_GATEWAY
    assert TransportKind.REST_GATEWAY.value == "rest_gateway"
    assert required_metadata <= REST_GATEWAY_PAYLOAD_METADATA_FIELDS
    assert {
        "client_id_ref",
        "timestamp_utc",
        "nonce_ref",
        "signature_ref",
    } == REST_GATEWAY_AUTH_HEADER_SLOTS
    assert TransportErrorCode.REST_GATEWAY_TIMEOUT in REST_GATEWAY_TRANSPORT_ERROR_CODES
    assert TransportErrorCode.REST_GATEWAY_UNAVAILABLE in REST_GATEWAY_TRANSPORT_ERROR_CODES

    result = build_rest_gateway_payload_metadata(
        {
            "transport_kind": "rest_gateway",
            "endpoint": "health",
            "run_id": "run-cr019-s03-fixture",
            "stage": "shadow",
            "mode": "dry_run",
            "redaction_label": "fixture-redacted",
            "request_id": "request-cr019-s03",
            "timeout_seconds": 3,
        }
    )
    assert result.accepted is True
    assert result.metadata is not None
    assert result.metadata.transport_kind is TransportKind.REST_GATEWAY
    assert result.sanitized_metadata["endpoint"] == "health"

    timeout = rest_gateway_timeout_ack("request-cr019-s03")
    assert timeout.status is TransportStatus.TIMEOUT
    assert timeout.error_code is TransportErrorCode.REST_GATEWAY_TIMEOUT
    assert all(value == 0 for value in timeout.counters.values())


def test_validate_intent_is_contract_only_and_keeps_counters_zero() -> None:
    client = QmtClient()
    response = client.validate_intent(_request(QmtEndpointCategory.VALIDATE_INTENT))

    assert response.status is QmtResponseStatus.OK
    assert response.payload["validated"] is True
    assert response.payload["real_operation"] is False
    assert response.transport_metadata["transport_kind"] == "rest_gateway"
    _assert_zero_counters(response.counters)
