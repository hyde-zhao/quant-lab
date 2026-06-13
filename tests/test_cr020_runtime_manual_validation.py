from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from trading.qmt_client import QmtRestRequest
from trading.qmt_gateway_contracts import (
    CR020_QUERY_POSITIONS_PATH,
    CR020_QUERY_POSITIONS_SCOPE,
)
from trading.qmt_runtime import (
    QmtGatewayRuntime,
    RUNTIME_SCHEMA_VERSION,
    StdlibQmtRestTransport,
    XtQuantRuntimeAdapter,
    build_runtime_config,
    build_runtime_hmac_provider,
    load_runtime_env,
)


def test_runtime_env_loader_and_public_config_redact_secret_values(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "QMT_GATEWAY_HOST=127.0.0.1",
                "QMT_GATEWAY_PORT=18765",
                "QMT_GATEWAY_ALLOWED_SOURCE=127.0.0.1/32",
                "QMT_CLIENT_ID=client-fixture",
                "QMT_CLIENT_SECRET=secret-fixture",
                "QMT_MINIQMT_PATH=C:/qmt/userdata_mini",
                "QMT_ACCOUNT_REF=account-fixture",
                "QMT_ACCOUNT_TYPE=STOCK",
            ]
        ),
        encoding="utf-8",
    )

    env = load_runtime_env(env_path)
    config = build_runtime_config(env)
    public = config.to_public_dict()
    rendered = json.dumps(public, ensure_ascii=False)

    assert public["schema_version"] == RUNTIME_SCHEMA_VERSION
    assert public["host"] == "127.0.0.1"
    assert public["port"] == 18765
    assert public["client_secret_ref"] == "[REDACTED]"
    assert public["miniqmt_path_configured"] is True
    assert "secret-fixture" not in rendered
    assert "account-fixture" not in rendered


def test_runtime_auth_provider_signs_qmt_rest_request_body() -> None:
    config = build_runtime_config(
        {
            "QMT_CLIENT_ID": "client-fixture",
            "QMT_CLIENT_SECRET": "secret-fixture",
        }
    )
    provider = build_runtime_hmac_provider(config)
    request = QmtRestRequest(
        endpoint="query_positions",
        method="POST",
        path=CR020_QUERY_POSITIONS_PATH,
        base_url="http://127.0.0.1:18765",
        run_id="run-fixture",
        stage="manual_cp7",
        mode="live_readonly",
        required_scope=CR020_QUERY_POSITIONS_SCOPE,
        body=b'{"run_id":"run-fixture"}',
    )

    headers = provider.build_headers(request)

    assert headers["X-QMT-Client-Id"] == "client-fixture"
    assert headers["X-QMT-Signature"]
    assert set(headers) >= {
        "X-QMT-Client-Id",
        "X-QMT-Timestamp",
        "X-QMT-Nonce",
        "X-QMT-Signature",
    }


def test_runtime_gateway_query_positions_with_fake_xtquant_redacts_response() -> None:
    config = build_runtime_config(
        {
            "QMT_GATEWAY_ALLOWED_SOURCE": "127.0.0.1/32",
            "QMT_CLIENT_ID": "client-fixture",
            "QMT_CLIENT_SECRET": "secret-fixture",
            "QMT_MINIQMT_PATH": "C:/qmt/userdata_mini",
            "QMT_ACCOUNT_REF": "account-fixture",
            "QMT_ACCOUNT_TYPE": "STOCK",
        }
    )
    adapter = XtQuantRuntimeAdapter(config, module_loader=_fake_xtquant_loader)
    runtime = QmtGatewayRuntime(config, adapter)
    snapshot = runtime.login()
    body = _json_bytes(
        {
            "run_id": "run-runtime-fixture",
            "request_id": "request-runtime-fixture",
            "redaction_label": "qmt-positions-redacted",
            "payload": {},
        }
    )
    headers = build_runtime_hmac_provider(config).build_headers(
        QmtRestRequest(
            endpoint="query_positions",
            method="POST",
            path=CR020_QUERY_POSITIONS_PATH,
            base_url=config.base_url,
            run_id="run-runtime-fixture",
            stage="manual_cp7",
            mode="live_readonly",
            required_scope=CR020_QUERY_POSITIONS_SCOPE,
            body=body,
        )
    )

    result = runtime.query_positions(
        body=body,
        headers=headers,
        source_ip="127.0.0.1",
    )
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True)
    query_payload = result["allowed_payload"]["data"]["query_positions"]  # type: ignore[index]

    assert snapshot.ready is True
    assert result["allowed"] is True
    assert query_payload["position_count"] == 1
    assert query_payload["redaction_status"] == "pass"
    assert result["counters"]["readonly_positions_adapter_call"] == 1
    assert result["counters"]["real_order"] == 0
    assert result["counters"]["account_write"] == 0
    assert "account-fixture" not in rendered
    assert "000001.SZ" not in rendered


def test_runtime_adapter_uses_subscribe_when_xtquant_login_is_absent() -> None:
    config = build_runtime_config(
        {
            "QMT_MINIQMT_PATH": "C:/qmt/userdata_mini",
            "QMT_ACCOUNT_REF": "account-fixture",
            "QMT_ACCOUNT_TYPE": "STOCK",
        }
    )
    trader = _FakeSubscribeOnlyTrader()

    def loader(name: str) -> object:
        if name == "xtquant.xttrader":
            return SimpleNamespace(XtQuantTrader=lambda path, session_id: trader)
        if name == "xtquant.xttype":
            return SimpleNamespace(StockAccount=_FakeAccount)
        raise ImportError(name)

    adapter = XtQuantRuntimeAdapter(config, module_loader=loader)
    snapshot = adapter.login()

    assert snapshot.ready is True
    assert trader.subscribe_call_count == 1


def test_stdlib_rest_transport_normalizes_json_response_without_real_socket() -> None:
    body = {
        "status": "allowed",
        "allowed": True,
        "allowed_payload": {"data": {"ok": True}},
        "counters": {},
    }

    def fake_opener(request: object, timeout: int) -> object:
        assert timeout == 3
        return SimpleNamespace(
            status=200,
            read=lambda: json.dumps(body).encode("utf-8"),
        )

    transport = StdlibQmtRestTransport(opener=fake_opener)
    result = transport.send(
        QmtRestRequest(
            endpoint="health",
            method="GET",
            path="/qmt/health",
            base_url="http://127.0.0.1:18765",
            run_id="run-http-fixture",
            stage="manual_cp7",
            mode="dry_run",
            body=b"",
            timeout_seconds=3,
        )
    )

    assert result.status == "allowed"
    assert result.status_code == 200
    assert result.body["allowed"] is True


class _FakeTrader:
    def start(self) -> None:
        return None

    def connect(self) -> int:
        return 0

    def login(self, account: object) -> int:
        return 0

    def query_stock_positions(self, account: object) -> list[object]:
        return [
            SimpleNamespace(
                account_id="account-fixture",
                stock_code="000001.SZ",
                volume=500,
                can_use_volume=100,
                market_value=12345.6,
                direction="long",
            )
        ]


class _FakeSubscribeOnlyTrader:
    def __init__(self) -> None:
        self.subscribe_call_count = 0

    def start(self) -> None:
        return None

    def connect(self) -> int:
        return 0

    def subscribe(self, account: object) -> int:
        self.subscribe_call_count += 1
        return 0

    def query_stock_positions(self, account: object) -> list[object]:
        return []


class _FakeAccount:
    def __init__(self, account_id: str, account_type: str) -> None:
        self.account_id = account_id
        self.account_type = account_type


def _fake_xtquant_loader(name: str) -> object:
    if name == "xtquant.xttrader":
        return SimpleNamespace(XtQuantTrader=lambda path, session_id: _FakeTrader())
    if name == "xtquant.xttype":
        return SimpleNamespace(StockAccount=_FakeAccount)
    raise ImportError(name)


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
