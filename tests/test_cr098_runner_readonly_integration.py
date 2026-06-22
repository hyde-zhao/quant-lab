from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import pytest

from trading.qmt_client import QmtClient, QmtClientConfig, QmtRestRequest, QmtTransportResult
from trading.strategy_runner import (
    ReadonlyGatewayClient,
    ReadonlyGatewayResult,
    ReadonlyGatewayRuntimeConfig,
    adapt_strategy_payload,
    build_evidence_summary,
)
from trading.strategy_runner.evidence import EvidenceRedactionError


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cr091_strategy_runner"


class HeaderProviderFixture:
    def build_headers(self, request: QmtRestRequest) -> Mapping[str, str]:
        return {
            "x-qmt-client-id": "fixture-client",
            "x-qmt-timestamp": "2026-06-19T12:00:00Z",
            "x-qmt-nonce": f"nonce-{request.run_id}-{request.endpoint}",
            "x-qmt-signature": "fixture-signature",
        }


class RecordingTransportFixture:
    def __init__(self) -> None:
        self.requests: list[QmtRestRequest] = []

    def send(self, request: QmtRestRequest) -> QmtTransportResult:
        self.requests.append(request)
        endpoint = str(getattr(request.endpoint, "value", request.endpoint))
        if endpoint == "health":
            data: dict[str, object] = {"health": "ok", "operation_authorized": False, "real_operation": False}
        elif endpoint == "capabilities":
            data = {
                "capabilities": ["health", "capabilities", "query_positions"],
                "operation_authorized": False,
                "real_operation": False,
            }
        else:
            data = {
                "query_positions": {
                    "position_count": 0,
                    "positions_digest": "sha256:empty-fixture",
                    "items_redacted": [],
                    "redaction_status": "pass",
                    "raw_payload_emitted": False,
                },
                "operation_authorized": False,
                "real_operation": False,
            }
        return QmtTransportResult(
            status="allowed",
            status_code=200,
            body={"status": "allowed", "allowed_payload": {"data": data}},
            redaction_status="redacted",
        )


def load_json(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def build_fixture_client(transport: RecordingTransportFixture) -> ReadonlyGatewayClient:
    qmt_client = QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18765",
            default_stage="manual_cp7",
            default_mode="live_readonly",
        ),
        transport=transport,
        auth_header_provider=HeaderProviderFixture(),
    )
    return ReadonlyGatewayClient(
        client=qmt_client,
        runtime_config=ReadonlyGatewayRuntimeConfig(
            base_url="http://127.0.0.1:18765",
            authorization_ref="cr098-fixture-readonly",
            runtime_env_ref="cr098-client-env:sha256:fixture",
        ),
    )


def test_cr098_default_gateway_client_remains_fake_and_offline() -> None:
    client = ReadonlyGatewayClient()

    health = client.health(run_id="cr098-offline")
    capabilities = client.capabilities(run_id="cr098-offline")
    positions = client.query_positions(run_id="cr098-offline")

    assert health.passed
    assert capabilities.passed
    assert positions.passed
    assert health.transport_kind == "fake"
    assert positions.payload["raw_payload_emitted"] is False
    assert all(value == 0 for value in positions.operation_counters.values())


def test_cr098_qmt_client_path_requires_explicit_runtime_authorization() -> None:
    transport = RecordingTransportFixture()
    qmt_client = QmtClient(
        config=QmtClientConfig(base_url="http://127.0.0.1:18765"),
        transport=transport,
        auth_header_provider=HeaderProviderFixture(),
    )
    client = ReadonlyGatewayClient(client=qmt_client)

    result = client.query_positions(run_id="cr098-missing-auth")

    assert result.status == "blocked"
    assert result.reason_code == "blocked_runtime_authorization_missing"
    assert transport.requests == []


def test_cr098_qmt_client_fixture_path_normalizes_readonly_results() -> None:
    transport = RecordingTransportFixture()
    client = build_fixture_client(transport)

    health = client.health(run_id="cr098-fixture")
    capabilities = client.capabilities(run_id="cr098-fixture")
    positions = client.query_positions(run_id="cr098-fixture")

    assert health.passed
    assert capabilities.payload["capabilities"] == ["health", "capabilities", "query_positions"]
    assert positions.passed
    assert positions.payload == {
        "position_count": 0,
        "positions_digest": "sha256:empty-fixture",
        "items_redacted_count": 0,
        "redaction_status": "pass",
        "raw_payload_emitted": False,
        "operation_authorized": False,
        "real_operation": False,
    }
    assert len(transport.requests) == 3
    assert {request.authorization_ref for request in transport.requests} == {"cr098-fixture-readonly"}


def test_cr098_readonly_gateway_still_blocks_order_like_endpoints() -> None:
    transport = RecordingTransportFixture()
    client = build_fixture_client(transport)

    result = client.call("submit_order", run_id="cr098-order-block")

    assert result.status == "blocked"
    assert result.reason_code == "blocked_scope_denied"
    assert transport.requests == []


def test_cr098_evidence_records_redacted_readonly_summary() -> None:
    payload = load_json("cr091_multifactor_admission_package_pass.json")
    adapter_result = adapt_strategy_payload(payload, run_id="cr098-evidence")
    readonly_client = build_fixture_client(RecordingTransportFixture())

    evidence = build_evidence_summary(
        run_id="cr098-evidence",
        package_id="fixture-package",
        adapter_type="multifactor_admission",
        adapter_result=adapter_result,
        readonly_health_result=readonly_client.health(run_id="cr098-evidence"),
        readonly_capabilities_result=readonly_client.capabilities(run_id="cr098-evidence"),
        readonly_result=readonly_client.query_positions(run_id="cr098-evidence"),
    )

    assert evidence.status == "pass"
    assert evidence.readonly_health_status == "ok"
    assert evidence.readonly_capabilities_status == "ok"
    assert evidence.readonly_position_count == 0
    assert evidence.readonly_positions_digest == "sha256:empty-fixture"
    assert evidence.readonly_items_redacted_count == 0
    assert evidence.runtime_authorization_ref == "cr098-fixture-readonly"
    assert evidence.runtime_env_ref == "cr098-client-env:sha256:fixture"


def test_cr098_evidence_blocks_sensitive_or_raw_readonly_payload() -> None:
    payload = load_json("cr091_multifactor_admission_package_pass.json")
    adapter_result = adapt_strategy_payload(payload, run_id="cr098-sensitive")
    readonly = ReadonlyGatewayResult(
        endpoint="query_positions",
        status="ok",
        payload={"raw_positions": [{"symbol": "SHOULD_NOT_APPEAR"}]},
    )

    with pytest.raises(EvidenceRedactionError, match="blocked_redaction_failed"):
        build_evidence_summary(
            run_id="cr098-sensitive",
            package_id="fixture-package",
            adapter_type="multifactor_admission",
            adapter_result=adapter_result,
            readonly_result=readonly,
        )


def test_cr098_readonly_gateway_source_does_not_import_runtime_boundaries() -> None:
    source = Path("trading/strategy_runner/readonly_gateway.py").read_text(encoding="utf-8")

    forbidden = ("xtquant", "load_runtime_env", "serve_gateway_runtime", "create_gateway_runtime")
    assert not [token for token in forbidden if token in source]
