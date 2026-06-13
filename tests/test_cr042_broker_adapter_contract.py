from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path
from typing import Any, Mapping

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PAYLOAD_KEYS = {
    "account_id",
    "broker_order_id",
    "client_order_id",
    "entrust_no",
    "order_id",
    "password",
    "session",
    "token",
}


@pytest.fixture()
def broker_adapter():
    module = importlib.import_module("engine.broker_adapter")
    required_attrs = {
        "BrokerAdapter",
        "BrokerAdapterCapability",
        "BrokerCashSnapshot",
        "BrokerPositionSnapshot",
        "BrokerOrderRequest",
        "BrokerFillEvent",
        "BrokerAdapterResult",
        "PaperBrokerAdapter",
        "GoldminerStubBrokerAdapter",
        "validate_order_intent_batch",
        "normalize_adapter_error",
        "zero_adapter_operation_counts",
    }
    missing = sorted(name for name in required_attrs if not hasattr(module, name))
    assert missing == []
    return module


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _payload_contains_key(payload: Any, target_key: str) -> bool:
    if isinstance(payload, Mapping):
        return any(
            str(key).lower() == target_key.lower() or _payload_contains_key(value, target_key)
            for key, value in payload.items()
        )
    if isinstance(payload, list):
        return any(_payload_contains_key(item, target_key) for item in payload)
    return False


def _assert_no_forbidden_payload_keys(payload: Any) -> None:
    present = {key for key in FORBIDDEN_PAYLOAD_KEYS if _payload_contains_key(payload, key)}
    assert present == set()


def _assert_zero_counts(counts: Mapping[str, Any]) -> None:
    assert counts
    assert all(int(value) == 0 for value in counts.values())


def _intent(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "paper_order_intent_v1",
        "intent_id": "intent-cr042-000001",
        "strategy_id": "strategy_equal_weight_baseline",
        "signal_date": "2026-06-10",
        "target_trade_date": "2026-06-11",
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 100,
        "execution_price_policy": "raw_open",
        "not_authorization": True,
        "operation_counts": {},
        "reason": "fixture",
    }
    payload.update(overrides)
    return payload


def _market_row(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "trade_date": "2026-06-11",
        "symbol": "000001.SZ",
        "raw_open": 10.0,
        "raw_close": 10.5,
        "volume": 10_000,
        "trade_status": "trading",
        "up_limit": 11.0,
        "down_limit": 9.0,
    }
    payload.update(overrides)
    return payload


def test_cr042_capability_contract_is_broker_neutral_and_api_less(broker_adapter) -> None:
    paper = broker_adapter.PaperBrokerAdapter(
        initial_cash=100_000.0,
        positions={"000001.SZ": {"quantity": 100, "sellable_qty": 100, "average_cost": 9.5}},
        market_data=[_market_row()],
        as_of="2026-06-11",
    )

    capability = _jsonable(paper.capabilities())
    cash = _jsonable(paper.query_cash())
    positions = _jsonable(paper.query_positions())

    assert capability["schema_version"] == "broker_adapter_capability_v1"
    assert capability["adapter_kind"] == "paper_fixture"
    assert capability["requires_credentials"] is False
    assert capability["real_broker_enabled"] is False
    assert capability["simulation_ready"] is False
    assert capability["live_ready"] is False
    assert capability["not_authorization"] is True
    assert "raw_open" in capability["supported_execution_price_policies"]
    _assert_zero_counts(capability["operation_counts"])
    assert cash["schema_version"] == "broker_cash_snapshot_v1"
    assert cash["cash"] == pytest.approx(100_000.0)
    assert positions[0]["schema_version"] == "broker_position_snapshot_v1"
    assert positions[0]["symbol"] == "000001.SZ"
    _assert_no_forbidden_payload_keys({"capability": capability, "cash": cash, "positions": positions})


def test_cr042_paper_adapter_normalizes_order_fills_cash_and_positions_without_real_broker(
    broker_adapter,
) -> None:
    paper = broker_adapter.PaperBrokerAdapter(
        initial_cash=100_000.0,
        positions={},
        market_data=[_market_row()],
        config={
            "slippage_bps": 10.0,
            "commission_bps": 3.0,
            "stamp_tax_bps": 10.0,
            "transfer_fee_bps": 0.1,
            "max_participation_rate": 0.10,
        },
        as_of="2026-06-11",
    )

    result = _jsonable(paper.submit_order_intents([_intent()]))

    assert result["schema_version"] == "broker_adapter_result_v1"
    assert result["status"] == "pass"
    assert result["passed"] is True
    assert result["adapter_kind"] == "paper_fixture"
    assert result["not_authorization"] is True
    assert result["simulation_ready"] is False
    assert result["live_ready"] is False
    assert result["order_requests"][0]["schema_version"] == "broker_order_request_v1"
    assert result["order_requests"][0]["quantity"] == 100
    assert result["fills"][0]["schema_version"] == "broker_fill_event_v1"
    assert result["fills"][0]["status"] == "filled"
    assert result["fills"][0]["filled_qty"] == 100
    assert result["fills"][0]["exec_price"] == pytest.approx(10.01)
    assert result["cash_snapshot"]["cash"] < 100_000.0
    assert result["positions"][0]["symbol"] == "000001.SZ"
    assert result["positions"][0]["quantity"] == 100
    _assert_zero_counts(result["operation_counts"])
    _assert_zero_counts(result["capability"]["operation_counts"])
    _assert_no_forbidden_payload_keys(result)


def test_cr042_adapter_blocks_sensitive_material_and_nonzero_operation_counts(
    broker_adapter,
) -> None:
    paper = broker_adapter.PaperBrokerAdapter(
        initial_cash=100_000.0,
        positions={},
        market_data=[_market_row()],
    )

    result = _jsonable(
        paper.submit_order_intents(
            [
                _intent(
                    account_id="real-account-should-block",
                    operation_counts={"provider_fetch": 1},
                )
            ]
        )
    )

    assert result["status"] == "blocked"
    assert result["passed"] is False
    assert result["fills"] == []
    assert any("sensitive_material_present" in reason for reason in result["blocked_reasons"])
    assert any("forbidden_operation_nonzero" in reason for reason in result["blocked_reasons"])
    assert result["operation_counts"]["provider_fetch"] == 1
    assert result["operation_counts"]["real_broker_call"] == 0


def test_cr042_non_raw_execution_policy_fails_closed_before_fill_engine(broker_adapter) -> None:
    paper = broker_adapter.PaperBrokerAdapter(
        initial_cash=100_000.0,
        positions={},
        market_data=[_market_row()],
    )

    result = _jsonable(paper.submit_order_intents([_intent(execution_price_policy="qfq")]))

    assert result["status"] == "blocked"
    assert result["fills"] == []
    assert any("non_raw_execution_price_policy" in reason for reason in result["blocked_reasons"])


def test_cr042_goldminer_adapter_is_stub_only_until_independent_spike(broker_adapter) -> None:
    stub = broker_adapter.GoldminerStubBrokerAdapter()

    capability = _jsonable(stub.capabilities())
    result = _jsonable(stub.submit_order_intents([_intent()]))

    assert capability["adapter_kind"] == "goldminer_stub"
    assert capability["requires_credentials"] is False
    assert capability["can_submit_order_intents"] is False
    assert capability["blocked_reasons"] == ["goldminer_spike_required"]
    assert result["status"] == "blocked"
    assert result["blocked_reasons"] == ["goldminer_spike_required"]
    assert result["errors"][0]["code"] == "goldminer_spike_required"
    _assert_zero_counts(result["operation_counts"])


def test_cr042_error_normalization_is_json_safe_and_auditable(broker_adapter) -> None:
    error = _jsonable(
        broker_adapter.normalize_adapter_error(
            broker_adapter.BrokerAdapterBlockedReason.UNSUPPORTED_ADAPTER_OPERATION,
            "cancel is not supported",
            source="paper_fixture",
        )
    )

    assert error["schema_version"] == "broker_adapter_error_v1"
    assert error["code"] == "unsupported_adapter_operation"
    assert error["source"] == "paper_fixture"
    assert error["retryable"] is False
    assert error["not_authorization"] is True
    _assert_zero_counts(error["operation_counts"])


def test_cr042_static_import_boundary_excludes_broker_network_goldminer_and_trading_runtime() -> None:
    path = PROJECT_ROOT / "engine" / "broker_adapter.py"
    forbidden_import_roots = {
        "aiohttp",
        "backtrader",
        "broker",
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
    forbidden_call_names = {
        "cancel_order",
        "connect",
        "download",
        "fetch",
        "login",
        "publish",
        "query_account",
        "submit_order",
    }

    findings: list[tuple[str, str]] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports = [alias.name for alias in node.names]
            findings.extend(
                (path.name, name)
                for name in imports
                if any(name == root or name.startswith(f"{root}.") for root in forbidden_import_roots)
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            name = node.module
            if any(name == root or name.startswith(f"{root}.") for root in forbidden_import_roots):
                findings.append((path.name, name))
        elif isinstance(node, ast.Call):
            func = node.func
            call_name = ""
            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr
            if call_name in forbidden_call_names:
                findings.append((path.name, call_name))

    assert findings == []
