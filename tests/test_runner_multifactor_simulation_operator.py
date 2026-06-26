from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from trading.qmt_client import QmtClient, QmtClientConfig, QmtRestRequest, QmtTransportResult
from trading.qmt_gateway_contracts import (
    QMT_SIMULATION_CANCEL_ENDPOINT_ID,
    QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
    build_allowed_result,
    build_simulation_order_request,
)
from trading.strategy_runner.simulation_operator import (
    RuntimeQmtSimulationGateway,
    build_runtime_qmt_client,
    request_from_mapping,
    run_multifactor_simulation_operator,
    write_operator_evidence,
)


class _Auth:
    def build_headers(self, request: QmtRestRequest) -> Mapping[str, str]:
        return {
            "X-QMT-Client-Id": "client-fixture",
            "X-QMT-Timestamp": "2026-06-25T00:00:00+00:00",
            "X-QMT-Nonce": "nonce-fixture",
            "X-QMT-Signature": "signature-fixture",
        }


class _Transport:
    def __init__(self) -> None:
        self.calls: list[QmtRestRequest] = []

    def send(self, request: QmtRestRequest) -> QmtTransportResult:
        self.calls.append(request)
        if request.path == "/qmt/account/positions":
            return QmtTransportResult(
                status="allowed",
                status_code=200,
                body=build_allowed_result(
                    "query_positions",
                    {
                        "query_positions": {
                            "position_count": 1,
                            "positions_digest": "positions:digest-fixture",
                            "items_redacted": [
                                {
                                    "instrument_ref": "instrument:redacted",
                                    "quantity_bucket": "101-1000",
                                }
                            ],
                            "redaction_status": "pass",
                            "raw_payload_emitted": False,
                        },
                        "readonly_query_authorized": True,
                        "operation_authorized": False,
                        "real_operation": False,
                    },
                ).to_dict(),
            )
        if request.path == "/qmt/simulation/orders":
            body = json.loads(request.body.decode("utf-8"))
            assert body["expected_runtime_mode"] == "simulation"
            assert body["expected_runtime_profile"] == "cr138-simulation"
            assert body["payload"]["symbol"] == "000001.SZ"
            assert body["payload"]["idempotency_key"]
            return QmtTransportResult(
                status="allowed",
                status_code=200,
                body={
                    "status": "allowed",
                    "allowed": True,
                    "allowed_payload": {
                        "endpoint_id": QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
                        "data": {
                            "simulation_operation": {
                                "operation": "submit",
                                "run_id": body["run_id"],
                                "order_intent_id": body["intent_id"],
                                "accepted": True,
                                "broker_order_ref": "broker:redacted",
                                "cancel_ref": "cancel-ref:fixture",
                                "adapter_status": "xtquant-simulation-submit-accepted",
                            }
                        },
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
                },
            )
        if request.path == "/qmt/simulation/orders/cancel":
            body = json.loads(request.body.decode("utf-8"))
            assert body["payload"]["broker_order_ref"] == "cancel-ref:fixture"
            return QmtTransportResult(
                status="allowed",
                status_code=200,
                body={
                    "status": "allowed",
                    "allowed": True,
                    "allowed_payload": {
                        "endpoint_id": QMT_SIMULATION_CANCEL_ENDPOINT_ID,
                        "data": {
                            "simulation_operation": {
                                "operation": "cancel",
                                "run_id": body["run_id"],
                                "order_intent_id": body["intent_id"],
                                "accepted": True,
                                "broker_order_ref": "broker:redacted",
                                "cancel_ref": "cancel-ref:fixture",
                                "adapter_status": "xtquant-simulation-cancel-accepted",
                            }
                        },
                        "operation_authorized": True,
                        "fixture_only": False,
                        "real_operation": True,
                    },
                    "counters": {
                        "qmt_operation": 1,
                        "qmt_api_call": 1,
                        "real_cancel": 1,
                        "simulation_or_live_run": 1,
                    },
                },
            )
        raise AssertionError(request.path)


def test_runtime_gateway_adapter_sends_nested_order_payload_to_real_runtime_contract() -> None:
    transport = _Transport()
    client = QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18765",
            allow_simulation_transport=True,
            expected_runtime_mode="simulation",
            expected_runtime_profile="cr138-simulation",
        ),
        transport=transport,
        auth_header_provider=_Auth(),
    )
    gateway = RuntimeQmtSimulationGateway(client, expected_runtime_profile="cr138-simulation")

    result = gateway.submit_order(
        build_simulation_order_request(
            {
                "run_id": "operator-run-fixture",
                "request_id": "submit-fixture",
                "order_intent_id": "intent-fixture",
                "symbol": "000001.SZ",
                "side": "buy",
                "quantity": 100,
                "price": 10,
                "authorization_ref": "runner-qmt-multifactor-runtime-20260625-simulation",
                "idempotency_key": "idem-fixture",
            }
        )
    )

    assert result.allowed is True


def test_operator_runs_end_to_end_and_writes_redacted_evidence(tmp_path: Path) -> None:
    transport = _Transport()
    client = QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18765",
            allow_simulation_transport=True,
            expected_runtime_mode="simulation",
            expected_runtime_profile="cr138-simulation",
        ),
        transport=transport,
        auth_header_provider=_Auth(),
    )
    spec = _spec(output_path=str(tmp_path / "evidence.json"))
    request = request_from_mapping(spec)

    result = run_multifactor_simulation_operator(request, qmt_client=client)
    path = write_operator_evidence(result, request.persistence_policy.output_path)
    rendered = path.read_text(encoding="utf-8")

    assert result.passed is True
    assert result.execution_summary["submitted_count"] == 1
    assert result.execution_summary["cancelled_count"] == 1
    assert result.stability_window["status"] == "pass"
    assert path.is_file()
    assert "000001.SZ" not in rendered
    assert "raw-account" not in rendered
    assert "secret-fixture" not in rendered
    assert "broker-order-raw" not in rendered
    assert result.to_dict()["persistence_policy"]["raw_payload_allowed"] is False


def test_operator_blocks_before_submit_when_runtime_session_is_not_usable(tmp_path: Path) -> None:
    class BlockedTransport(_Transport):
        def send(self, request: QmtRestRequest) -> QmtTransportResult:
            self.calls.append(request)
            if request.path == "/qmt/account/positions":
                return QmtTransportResult(
                    status="blocked",
                    status_code=403,
                    body={"status": "blocked", "blocked_reason": "session_expired"},
                    error_code="session_expired",
                )
            raise AssertionError("submit/cancel must not be called")

    transport = BlockedTransport()
    client = QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18765",
            allow_simulation_transport=True,
            expected_runtime_mode="simulation",
            expected_runtime_profile="cr138-simulation",
        ),
        transport=transport,
        auth_header_provider=_Auth(),
    )
    request = request_from_mapping(_spec(output_path=str(tmp_path / "blocked.json")))

    result = run_multifactor_simulation_operator(request, qmt_client=client)

    assert result.blocked is True
    assert result.blocked_reason == "session_expired"
    assert {call.path for call in transport.calls} == {"/qmt/account/positions"}


def test_operator_blocks_fixture_symbol_contract_before_runtime_transport(
    tmp_path: Path,
) -> None:
    transport = _Transport()
    client = QmtClient(
        config=QmtClientConfig(
            base_url="http://127.0.0.1:18765",
            allow_simulation_transport=True,
            expected_runtime_mode="simulation",
            expected_runtime_profile="cr138-simulation",
        ),
        transport=transport,
        auth_header_provider=_Auth(),
    )
    spec = _spec(output_path=str(tmp_path / "blocked.json"))
    spec["signal_rows"] = [
        {"symbol": "INSTRUMENT_FIXTURE_A", "score": "0.9", "signal_date": "2026-06-25"}
    ]
    spec["current_positions"] = {"INSTRUMENT_FIXTURE_A": 0}
    spec["risk_snapshot"] = {
        "cash_available": "20000",
        "positions_available": {"INSTRUMENT_FIXTURE_A": 0},
        "t1_sellable": {"INSTRUMENT_FIXTURE_A": 0},
        "raw_price_refs": {
            "INSTRUMENT_FIXTURE_A": {"price": "10", "evidence_ref": "fixture:price"}
        },
    }
    request = request_from_mapping(spec)

    result = run_multifactor_simulation_operator(request, qmt_client=client)

    assert result.blocked is True
    assert result.blocked_reason == "runtime_symbol_contract_invalid"
    assert transport.calls == []


def _spec(*, output_path: str = "process/evidence/operator-fixture.json") -> dict[str, object]:
    return {
        "strategy_id": "strategy-alpha",
        "run_id": "operator-run-fixture",
        "target_trade_date": "2026-06-25",
        "authorization_ref": "runner-qmt-multifactor-runtime-20260625-simulation",
        "expected_runtime_profile": "cr138-simulation",
        "signal_rows": [{"symbol": "000001.SZ", "score": "0.9", "signal_date": "2026-06-25"}],
        "top_n": 1,
        "capital_base": "10000",
        "current_positions": {"000001.SZ": 0},
        "risk_snapshot": {
            "cash_available": "20000",
            "positions_available": {"000001.SZ": 0},
            "t1_sellable": {"000001.SZ": 0},
            "raw_price_refs": {"000001.SZ": {"price": "10", "evidence_ref": "price-ref"}},
        },
        "risk_profile": {
            "risk_profile_id": "risk-profile-simulation",
            "max_single_symbol_notional": "20000",
            "max_portfolio_notional": "20000",
            "lot_size": 100,
        },
        "output_path": output_path,
        "cancel_submitted_after_submit": True,
    }
