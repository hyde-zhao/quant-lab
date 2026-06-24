from __future__ import annotations

import ast
import builtins
import io
import json
from pathlib import Path
from typing import Mapping

from trading.qmt_client import (
    QmtClient,
    QmtClientConfig,
    QmtEndpointCategory,
    QmtRequest,
    QmtResponse,
    QmtResponseStatus,
    QmtRestRequest,
    QmtRetryPolicy,
    QmtTransportResult,
    collect_qmt_client_safety_counters,
)
from trading.qmt_client_cli import (
    QmtClientCliDependencyBlocked,
    QmtClientCliOptions,
    build_qmt_client_cli_command_matrix,
    create_qmt_client_typer_app,
    execute_qmt_client_cli_command,
    run_qmt_client_cli,
)
from trading.qmt_gateway_contracts import QmtBlockedReason, build_allowed_result
from trading.qmt_transport import TransportErrorCode


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


def _assert_zero_counters(counters: Mapping[str, int]) -> None:
    current = dict(counters)
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


class _FakeAuthProvider:
    def __init__(self, headers: Mapping[str, str] | None = None, *, raises: bool = False) -> None:
        self.headers = dict(
            headers
            or {
                "client_id_ref": "client-ref-fixture",
                "timestamp_utc": "2026-06-05T00:00:00+00:00",
                "nonce_ref": "nonce-ref-fixture",
                "signature_ref": "signature-ref-fixture",
            }
        )
        self.raises = raises
        self.calls: list[QmtRestRequest] = []

    def build_headers(self, request: QmtRestRequest) -> Mapping[str, str]:
        self.calls.append(request)
        if self.raises:
            raise RuntimeError("fixture auth failure")
        return self.headers


class _FakeTransport:
    def __init__(self, results: list[QmtTransportResult]) -> None:
        self.results = list(results)
        self.calls: list[QmtRestRequest] = []

    def send(self, request: QmtRestRequest) -> QmtTransportResult:
        self.calls.append(request)
        index = min(len(self.calls) - 1, len(self.results) - 1)
        return self.results[index]


def _client(
    transport: _FakeTransport,
    *,
    auth_provider: _FakeAuthProvider | None = None,
    retry_policy: QmtRetryPolicy | None = None,
    allow_simulation_transport: bool = False,
) -> QmtClient:
    return QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18080/",
            allow_simulation_transport=allow_simulation_transport,
        ),
        transport=transport,
        auth_header_provider=auth_provider or _FakeAuthProvider(),
        retry_policy=retry_policy,
    )


def _allowed_body(endpoint_id: str, payload: Mapping[str, object]) -> Mapping[str, object]:
    return build_allowed_result(endpoint_id, payload).to_dict()


def test_query_positions_uses_injected_rest_transport_and_redacts_output() -> None:
    transport = _FakeTransport(
        [
            QmtTransportResult(
                status="allowed",
                status_code=200,
                body=_allowed_body(
                    "query_positions",
                    {
                        "session_ready": True,
                        "positions": [
                            {
                                "account_id": "raw-account-001",
                                "symbol": "000001.SZ",
                                "quantity": 100,
                            }
                        ],
                    },
                ),
            )
        ]
    )
    auth = _FakeAuthProvider()
    client = _client(transport, auth_provider=auth)

    response = client.query_positions(
        run_id="run-cr020-s03",
        request_id="request-cr020-s03",
        authorization_ref="auth-ref-fixture",
        payload={"symbol": "000001.SZ"},
    )

    assert response.status is QmtResponseStatus.OK
    assert response.payload["positions"] == [
        {"account_id": "[REDACTED]", "symbol": "000001.SZ", "quantity": 100}
    ]
    assert response.payload["operation_authorized"] is False
    assert response.payload["real_operation"] is False
    assert response.transport_metadata["endpoint"] == "positions"
    assert response.transport_metadata["client_id_ref"] == "client-ref-fixture"
    assert transport.calls[0].base_url == "http://127.0.0.1:18080"
    assert transport.calls[0].path == "/qmt/account/positions"
    assert transport.calls[0].required_scope == "qmt:positions:read"
    assert auth.calls[0].required_scope == "qmt:positions:read"
    assert "raw-account-001" not in json.dumps(response.to_dict(), ensure_ascii=False)
    _assert_zero_counters(response.counters)


def test_default_client_without_base_url_or_transport_fails_closed() -> None:
    client = QmtClient()

    response = client.query_positions(run_id="run-no-transport")

    assert response.status is QmtResponseStatus.TRANSPORT_ERROR
    assert response.reason_code == QmtBlockedReason.TRANSPORT_UNAVAILABLE.value
    assert response.blocked is True
    _assert_zero_counters(response.counters)


def test_account_like_endpoints_other_than_query_positions_remain_blocked() -> None:
    transport = _FakeTransport(
        [QmtTransportResult(status="allowed", body=_allowed_body("query_positions", {}))]
    )
    client = _client(transport)

    response = client.query_account_like(
        QmtEndpointCategory.ACCOUNT_QUERY,
        QmtRequest(
            run_id="run-account-blocked",
            endpoint=QmtEndpointCategory.ACCOUNT_QUERY,
            stage="shadow",
            mode="live_readonly",
        ),
    )

    assert response.status is QmtResponseStatus.AUTH_ERROR
    assert response.reason_code == QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
    assert transport.calls == []
    _assert_zero_counters(response.counters)


def test_simulation_submit_uses_rest_transport_only_when_explicitly_enabled() -> None:
    body = {
        "status": "allowed",
        "allowed": True,
        "allowed_payload": {
            "endpoint_id": "submit_simulation",
            "data": {"simulation_operation": {"operation": "submit", "accepted": True}},
            "operation_authorized": True,
            "fixture_only": False,
            "real_operation": True,
        },
        "counters": {
            "qmt_operation": 1,
            "qmt_api_call": 1,
            "real_order": 1,
            "simulation_or_live_run": 1,
        },
    }
    blocked_transport = _FakeTransport([QmtTransportResult(status="allowed", body=body)])
    blocked_client = _client(blocked_transport)

    blocked = blocked_client.submit_simulation(
        run_id="run-simulation-client",
        request_id="request-simulation-client",
        intent_id="intent-simulation-client",
        authorization_ref="auth-simulation-client",
        payload={"symbol": "000001.SZ", "side": "buy", "quantity": 100, "price": 10.0},
    )

    assert blocked.status is QmtResponseStatus.AUTH_ERROR
    assert blocked.reason_code == QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
    assert blocked_transport.calls == []
    _assert_zero_counters(blocked.counters)

    transport = _FakeTransport(
        [
            QmtTransportResult(
                status="allowed",
                status_code=200,
                body=body,
                counters=body["counters"],  # type: ignore[arg-type]
            )
        ]
    )
    client = _client(transport, allow_simulation_transport=True)

    response = client.submit_simulation(
        run_id="run-simulation-client",
        request_id="request-simulation-client",
        intent_id="intent-simulation-client",
        authorization_ref="auth-simulation-client",
        payload={"symbol": "000001.SZ", "side": "buy", "quantity": 100, "price": 10.0},
    )

    assert response.status is QmtResponseStatus.OK
    assert response.payload["operation_authorized"] is True
    assert response.payload["real_operation"] is True
    assert response.payload["simulation_operation"] == {"operation": "submit", "accepted": True}
    assert response.counters["real_order"] == 1
    assert transport.calls[0].path == "/qmt/simulation/orders"
    assert transport.calls[0].required_scope == "qmt:simulation:submit"


def test_auth_provider_missing_or_failing_blocks_before_transport_send() -> None:
    transport = _FakeTransport(
        [QmtTransportResult(status="allowed", body=_allowed_body("health", {}))]
    )
    no_auth_client = QmtClient(
        config=QmtClientConfig(base_url="http://127.0.0.1:18080"),
        transport=transport,
    )

    response = no_auth_client.health(run_id="run-auth-required")

    assert response.status is QmtResponseStatus.AUTH_ERROR
    assert response.reason_code == TransportErrorCode.AUTH_REQUIRED.value
    assert transport.calls == []

    failing_auth = _FakeAuthProvider(raises=True)
    client = _client(transport, auth_provider=failing_auth)
    response = client.health(run_id="run-auth-failed")

    assert response.status is QmtResponseStatus.AUTH_ERROR
    assert response.reason_code == TransportErrorCode.AUTH_FAILED.value
    assert len(transport.calls) == 0


def test_transport_error_mapping_session_scope_and_timeout_bounds() -> None:
    session_transport = _FakeTransport(
        [
            QmtTransportResult(
                status="allowed",
                body=_allowed_body("query_positions", {"session_ready": False}),
            )
        ]
    )
    client = _client(session_transport)

    session_response = client.query_positions(run_id="run-session-not-ready")

    assert session_response.status is QmtResponseStatus.BLOCKED
    assert session_response.reason_code == "session_not_ready"

    scope_transport = _FakeTransport(
        [
            QmtTransportResult(
                status="blocked",
                status_code=403,
                body={"status": "blocked", "blocked_reason": "scope_insufficient"},
            )
        ]
    )
    client = _client(scope_transport)
    scope_response = client.query_positions(run_id="run-scope-denied")

    assert scope_response.status is QmtResponseStatus.BLOCKED
    assert scope_response.reason_code == QmtBlockedReason.SCOPE_DENIED.value

    invalid_timeout = client.query_positions(
        run_id="run-invalid-timeout",
        timeout_seconds=31,
    )
    assert invalid_timeout.status is QmtResponseStatus.VALIDATION_ERROR
    assert invalid_timeout.reason_code == QmtBlockedReason.INVALID_REQUEST.value
    assert len(scope_transport.calls) == 1


def test_retry_policy_retries_health_but_not_query_positions() -> None:
    retry_policy = QmtRetryPolicy(max_attempts=2)
    health_transport = _FakeTransport(
        [
            QmtTransportResult(
                status="error",
                error_code=TransportErrorCode.REST_GATEWAY_UNAVAILABLE.value,
            ),
            QmtTransportResult(
                status="allowed",
                status_code=200,
                body=_allowed_body("health", {"session_ready": True}),
            ),
        ]
    )
    client = _client(health_transport, retry_policy=retry_policy)

    response = client.health(run_id="run-health-retry")

    assert response.status is QmtResponseStatus.OK
    assert response.payload["attempts"] == 2
    assert len(health_transport.calls) == 2

    positions_transport = _FakeTransport(
        [
            QmtTransportResult(
                status="error",
                error_code=TransportErrorCode.REST_GATEWAY_UNAVAILABLE.value,
            ),
            QmtTransportResult(
                status="allowed",
                status_code=200,
                body=_allowed_body("query_positions", {"session_ready": True}),
            ),
        ]
    )
    client = _client(positions_transport, retry_policy=retry_policy)

    response = client.query_positions(run_id="run-positions-no-retry")

    assert response.status is QmtResponseStatus.TRANSPORT_ERROR
    assert response.reason_code == "gateway_unavailable"
    assert len(positions_transport.calls) == 1


class _FakeCliClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def health(self, **kwargs: object) -> QmtResponse:
        self.calls.append(("health", kwargs))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=QmtEndpointCategory.HEALTH,
            run_id=str(kwargs["run_id"]),
            payload={"source": "fake-cli-client"},
        )

    def diagnostics(self, **kwargs: object) -> QmtResponse:
        self.calls.append(("diagnostics", kwargs))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=QmtEndpointCategory.HEALTH,
            run_id=str(kwargs["run_id"]),
            payload={"source": "fake-cli-client"},
        )

    def query_positions(self, request: QmtRequest) -> QmtResponse:
        self.calls.append(("query_positions", request))
        return QmtResponse(
            status=QmtResponseStatus.OK,
            endpoint=request.endpoint,
            run_id=request.run_id,
            payload={"source": "fake-cli-client"},
        )


def test_client_cli_command_matrix_delegates_to_qmt_client_without_typer() -> None:
    command_names = {command.name for command in build_qmt_client_cli_command_matrix()}
    assert {
        "health",
        "capabilities",
        "diagnostics",
        "pairing-status",
        "validate-pairing",
        "query-positions",
        "validate-query-positions",
    } <= command_names

    fake = _FakeCliClient()
    options = QmtClientCliOptions(
        base_url="http://127.0.0.1:18080",
        run_id="run-cli-fixture",
        mode="live_readonly",
        request_id="request-cli-fixture",
    )

    response = execute_qmt_client_cli_command(
        "health",
        options,
        client_factory=lambda: fake,
    )
    assert response.payload["source"] == "fake-cli-client"
    assert fake.calls[-1][0] == "health"

    execute_qmt_client_cli_command("pairing-status", options, client_factory=lambda: fake)
    assert fake.calls[-1][0] == "diagnostics"

    execute_qmt_client_cli_command("query-positions", options, client_factory=lambda: fake)
    method, request = fake.calls[-1]
    assert method == "query_positions"
    assert isinstance(request, QmtRequest)
    assert request.endpoint is QmtEndpointCategory.POSITIONS
    assert request.mode == "live_readonly"


def test_typer_missing_fails_closed_without_import_time_dependency(monkeypatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "typer":
            raise ImportError("fixture blocks typer")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    app = create_qmt_client_typer_app()
    assert isinstance(app, QmtClientCliDependencyBlocked)

    output = io.StringIO()
    exit_code = run_qmt_client_cli(["health"], output_stream=output)
    payload = json.loads(output.getvalue())

    assert exit_code == 3
    assert payload["status"] == "blocked"
    assert payload["reason_code"] == "typer_dependency_missing"
    _assert_zero_counters(payload["counters"])


def test_sources_have_no_forbidden_imports_or_env_reads(monkeypatch) -> None:
    source_paths = (
        Path("trading/qmt_client.py"),
        Path("trading/qmt_client_cli.py"),
        Path("trading/qmt_transport.py"),
    )
    forbidden_import_roots = {
        "fastapi",
        "httpx",
        "requests",
        "socket",
        "urllib",
        "uvicorn",
        "xtquant",
        "MiniQMT",
    }
    imports: list[str] = []
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)

    real_open = builtins.open
    real_read_text = Path.read_text

    def guarded_open(file: object, *args: object, **kwargs: object) -> object:
        if ".env" in str(file):
            raise AssertionError(f"unexpected env read: {file}")
        return real_open(file, *args, **kwargs)

    def guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if ".env" in str(self):
            raise AssertionError(f"unexpected env read: {self}")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    transport = _FakeTransport(
        [QmtTransportResult(status="allowed", body=_allowed_body("health", {}))]
    )
    client = _client(transport)
    response = client.diagnostics(run_id="run-no-env-read")

    assert response.status is QmtResponseStatus.OK
    _assert_zero_counters(collect_qmt_client_safety_counters())
