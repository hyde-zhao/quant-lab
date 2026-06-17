from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path
from typing import Any, Mapping

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_RUNTIME_IMPORT_ROOTS = {
    "aiohttp",
    "broker",
    "gm",
    "gmtrade",
    "httpx",
    "miniqmt",
    "qmt",
    "requests",
    "socket",
    "subprocess",
    "trading",
    "xtquant",
}

FORBIDDEN_REAL_RUNTIME_CALLS = {
    "connect",
    "download",
    "fetch",
    "get_cash",
    "get_position",
    "get_positions",
    "login",
    "order_batch",
    "order_cancel",
    "order_volume",
    "publish",
    "query_account",
    "query_orders",
    "query_positions",
}

FORBIDDEN_SENSITIVE_VALUES = {
    "real-account-001",
    "super-secret-token",
    "SESSION-123",
    "broker-order-777",
    "exec-888",
}


@pytest.fixture()
def broker_adapter():
    return importlib.import_module("engine.broker_adapter")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _contains_value(payload: Any, target: str) -> bool:
    if isinstance(payload, Mapping):
        return any(_contains_value(key, target) or _contains_value(value, target) for key, value in payload.items())
    if isinstance(payload, list):
        return any(_contains_value(item, target) for item in payload)
    return str(payload) == target


def _assert_no_sensitive_values(payload: Any) -> None:
    leaked = {value for value in FORBIDDEN_SENSITIVE_VALUES if _contains_value(payload, value)}
    assert leaked == set()


def _assert_zero_counts(counts: Mapping[str, Any]) -> None:
    assert counts
    assert all(int(value) == 0 for value in counts.values())


def _intent(**overrides: Any) -> dict[str, Any]:
    payload = {
        "intent_id": "intent-cr044-000001",
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 100,
        "target_trade_date": "2026-06-11",
        "execution_price_policy": "raw_open",
        "not_authorization": True,
        "operation_counts": {},
    }
    payload.update(overrides)
    return payload


def test_cr044_authorization_layers_and_redaction_are_fixture_only(broker_adapter) -> None:
    layers = broker_adapter.cr044_authorization_layers()
    actions = broker_adapter.cr044_not_authorized_actions()
    payload = {
        "account_id": "real-account-001",
        "nested": {"token": "super-secret-token", "session": "SESSION-123"},
        "ordinary_field": "fixture-only",
    }

    redaction = broker_adapter.redact_sensitive_payload(payload)

    assert layers[0]["status"] == "authorized_current_scope"
    assert layers[2]["status"] == "not_authorized"
    assert {
        "credential_read",
        "cash_query",
        "position_query",
        "order_submit",
        "order_cancel",
        "simulation_runtime",
        "live_runtime",
        "provider_fetch",
        "lake_write",
        "catalog_publish",
    }.issubset(actions)
    assert redaction["schema_version"] == "cr044_redaction_summary_v1"
    assert redaction["status"] == "redacted"
    assert redaction["redacted_count"] == 3
    assert {field["value"] for field in redaction["fields"]} == {"REDACTED"}
    assert {field["field_path"] for field in redaction["fields"]} == {
        "account_id",
        "nested.session",
        "nested.token",
    }
    _assert_no_sensitive_values(redaction)


def test_cr044_no_real_goldminer_runtime_import_or_call_in_adapter() -> None:
    path = PROJECT_ROOT / "engine" / "broker_adapter.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: list[tuple[str, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports = [alias.name for alias in node.names]
            findings.extend(
                (path.name, name)
                for name in imports
                if any(name == root or name.startswith(f"{root}.") for root in FORBIDDEN_RUNTIME_IMPORT_ROOTS)
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            name = node.module
            if any(name == root or name.startswith(f"{root}.") for root in FORBIDDEN_RUNTIME_IMPORT_ROOTS):
                findings.append((path.name, name))
        elif isinstance(node, ast.Call):
            func = node.func
            call_name = ""
            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr
            if call_name in FORBIDDEN_REAL_RUNTIME_CALLS:
                findings.append((path.name, call_name))

    assert findings == []


def test_cr044_goldminer_capability_and_readonly_queries_fail_closed(broker_adapter) -> None:
    stub = broker_adapter.GoldminerStubBrokerAdapter()

    capability = _jsonable(stub.capabilities())
    admission = _jsonable(stub.cr044_admission_state("cash_query"))

    assert capability["adapter_kind"] == "goldminer_stub"
    assert capability["can_query_cash"] is False
    assert capability["can_query_positions"] is False
    assert capability["real_broker_enabled"] is False
    assert capability["simulation_ready"] is False
    assert capability["live_ready"] is False
    assert capability["blocked_reasons"] == ["goldminer_spike_required"]
    _assert_zero_counts(capability["operation_counts"])

    assert admission["schema_version"] == "cr044_goldminer_admission_v1"
    assert admission["allowed"] is False
    assert admission["capability_state"] == "blocked_no_authorization"
    assert "cash_query_not_authorized" in admission["blocked_reasons"]
    assert admission["simulation_ready"] is False
    assert admission["live_ready"] is False
    _assert_zero_counts(admission["operation_counts"])

    with pytest.raises(broker_adapter.BrokerAdapterValidationError) as cash_error:
        stub.query_cash()
    with pytest.raises(broker_adapter.BrokerAdapterValidationError) as position_error:
        stub.query_positions()
    assert str(cash_error.value) == "goldminer_readonly_query_not_authorized"
    assert str(position_error.value) == "goldminer_readonly_query_not_authorized"
    _assert_no_sensitive_values({"cash_error": str(cash_error.value), "position_error": str(position_error.value)})


def test_cr044_readonly_candidate_mapping_is_blocked_unknown_and_never_real_verified(broker_adapter) -> None:
    rows = broker_adapter.goldminer_readonly_candidate_mapping()
    cash_rows = broker_adapter.goldminer_readonly_candidate_mapping("cash_query")
    statuses = {row["mapping_status"] for row in rows}
    admission = _jsonable(broker_adapter.evaluate_goldminer_admission("position_query"))

    assert rows
    assert cash_rows
    assert "real_verified" not in statuses
    assert "static_candidate" in statuses
    assert "unknown_broker_field" in statuses
    assert "redacted_sensitive_field" in statuses
    assert all(row["schema_version"] == "cr044_readonly_mapping_v1" for row in rows)
    assert admission["allowed"] is False
    assert "position_query_not_authorized" in admission["blocked_reasons"]
    _assert_zero_counts(admission["operation_counts"])


def test_cr044_submit_cancel_are_blocked_by_kill_switch_with_zero_real_operation_counts(broker_adapter) -> None:
    stub = broker_adapter.GoldminerStubBrokerAdapter()

    submit_result = _jsonable(stub.submit_order_intents([_intent(token="super-secret-token")]))
    cancel_result = _jsonable(stub.cancel_order("broker-order-777", reason="fixture"))
    submit_gate = _jsonable(broker_adapter.evaluate_goldminer_admission("order_submit", payload=_intent()))
    cancel_gate = _jsonable(broker_adapter.evaluate_goldminer_admission("order_cancel"))

    assert submit_result["status"] == "blocked"
    assert submit_result["fills"] == []
    assert submit_result["order_requests"] == []
    assert submit_result["blocked_reasons"] == ["goldminer_spike_required"]
    assert submit_result["simulation_ready"] is False
    assert submit_result["live_ready"] is False
    _assert_zero_counts(submit_result["operation_counts"])
    _assert_no_sensitive_values(submit_result)

    assert cancel_result["status"] == "blocked"
    assert cancel_result["fills"] == []
    assert cancel_result["order_requests"] == []
    assert cancel_result["blocked_reasons"] == ["goldminer_submit_cancel_not_authorized"]
    _assert_zero_counts(cancel_result["operation_counts"])
    _assert_no_sensitive_values(cancel_result)

    for gate in (submit_gate, cancel_gate):
        assert gate["allowed"] is False
        assert "global_kill_switch_disabled" in gate["blocked_reasons"]
        assert "per_run_authorization_missing" in gate["blocked_reasons"]
        assert "operation_not_whitelisted" in gate["blocked_reasons"]
        assert gate["simulation_ready"] is False
        assert gate["live_ready"] is False
        _assert_zero_counts(gate["operation_counts"])


def test_cr044_reconciliation_evidence_is_redacted_manual_review_only_and_no_compensation(
    broker_adapter,
) -> None:
    stub = broker_adapter.GoldminerStubBrokerAdapter()
    blocked_result = stub.submit_order_intents([_intent()])
    evidence = _jsonable(
        broker_adapter.build_goldminer_reconciliation_evidence(
            blocked_result,
            payload={
                "account_id": "real-account-001",
                "broker_order_id": "broker-order-777",
                "execution_ref": "exec-888",
            },
            discrepancies=(broker_adapter.CR044DiscrepancyCode.FIXTURE_MISMATCH.value,),
        )
    )

    assert evidence["schema_version"] == "cr044_reconciliation_evidence_v1"
    assert evidence["source"] == "blocked_goldminer_stub"
    assert evidence["status"] == "mismatch_requires_manual_review"
    assert evidence["manual_review_required"] is True
    assert "goldminer_spike_required" in evidence["blocked_reasons"]
    assert "runtime_not_authorized" in evidence["discrepancies"]
    assert "field_unknown" in evidence["discrepancies"]
    assert "sensitive_material_present" in evidence["discrepancies"]
    assert "fixture_mismatch" in evidence["discrepancies"]
    assert evidence["mapping_status_summary"]["unknown_broker_field"] >= 1
    assert evidence["redaction_summary"]["redacted_count"] == 3
    assert evidence["simulation_ready"] is False
    assert evidence["live_ready"] is False
    _assert_zero_counts(evidence["operation_counts"])
    _assert_no_sensitive_values(evidence)
