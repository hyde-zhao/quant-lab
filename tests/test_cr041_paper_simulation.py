from __future__ import annotations

import ast
import dataclasses
import importlib
import json
from pathlib import Path
from typing import Any, Mapping

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_OPERATION_COUNTERS = {
    "account_or_order_operation": 0,
    "broker_connection": 0,
    "qmt_operation": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_publish": 0,
    "dependency_change": 0,
    "external_quote_subscription": 0,
    "reports_overwrite": 0,
    "credential_read": 0,
    "simulation_or_live": 0,
}

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
def paper_simulation():
    module = importlib.import_module("engine.paper_simulation")
    required_attrs = {
        "load_strategy_admission_package",
        "validate_strategy_admission_package",
        "build_admission_view",
        "build_order_intents",
        "PaperBrokerConfig",
        "simulate_fills",
        "apply_fills_to_ledger",
        "run_paper_simulation",
    }
    missing = sorted(name for name in required_attrs if not hasattr(module, name))
    assert missing == []
    return module


def _jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _jsonable(value.to_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _write_json(path: Path, payload: Mapping[str, Any] | list[Mapping[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _status(payload: Mapping[str, Any]) -> str:
    status = payload.get("status") or payload.get("validation_status") or payload.get("admission_status")
    if status:
        return str(status)
    if payload.get("passed") is False:
        return "blocked"
    if payload.get("passed") is True:
        return "passed"
    return ""


def _passed(payload: Mapping[str, Any]) -> bool:
    if "passed" in payload:
        return bool(payload["passed"])
    return _status(payload).lower() in {"pass", "passed", "valid", "accepted"}


def _blocked_reasons(payload: Mapping[str, Any]) -> set[str]:
    raw = (
        payload.get("blocked_reasons")
        or payload.get("reasons")
        or payload.get("violations")
        or payload.get("errors")
        or []
    )
    reasons: set[str] = set()
    for item in raw:
        if isinstance(item, Mapping):
            for key in ("code", "reason_code", "reason", "field"):
                if item.get(key):
                    reasons.add(str(item[key]))
        else:
            reasons.add(str(item))
    return reasons


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


def _assert_zero_counters(counters: Mapping[str, Any]) -> None:
    assert set(FORBIDDEN_OPERATION_COUNTERS).issubset(counters)
    assert all(int(counters[key]) == 0 for key in FORBIDDEN_OPERATION_COUNTERS)


def _package_operation_counts() -> dict[str, int]:
    # 准入包 fixture 不放 credential_read 字段，避免把“禁止操作计数键”误判为真实凭据字段；
    # 输出视图和报告仍必须补齐完整 forbidden counter surface。
    return {
        key: value
        for key, value in FORBIDDEN_OPERATION_COUNTERS.items()
        if key != "credential_read"
    }


def _valid_admission_package(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "multifactor_strategy_admission_package_v1",
        "run_id": "run-cr039-fixture",
        "status": "PASS",
        "overall_admission": "research_baseline",
        "not_authorization": True,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "operation_counts": _package_operation_counts(),
        "allowed_claims": [
            {"claim": "multifactor_research_baseline", "status": "allowed", "reason": "fixture"}
        ],
        "blocked_claims": [
            {"claim": "simulation_ready", "status": "blocked", "reason": "not authorized"},
            {"claim": "live_ready", "status": "blocked", "reason": "not authorized"},
            {"claim": "broker_order_ready", "status": "blocked", "reason": "not authorized"},
        ],
        "input_refs": {"strategy_admission_package": "fixture://cr039/strategy-admission-package"},
        "unlock_conditions": ["independent simulation/live authorization is required"],
        "strategy_candidates": [
            {
                "strategy_id": "strategy_equal_weight_baseline",
                "strategy_name": "equal weight baseline fixture",
                "source_portfolio_id": "portfolio-cr039-equal-weight-fixture",
                "admission": "research_baseline",
                "simulation_candidate": False,
                "blocked_claims": [
                    {"claim": "simulation_ready", "status": "blocked", "reason": "not authorized"}
                ],
                "allowed_claims": [
                    {"claim": "research_baseline", "status": "allowed", "reason": "fixture"}
                ],
            }
        ],
    }
    payload.update(overrides)
    return payload


def _target_portfolio(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "paper_target_portfolio_v1",
        "target_portfolio_id": "target-cr041-fixture",
        "source_run_id": "run-cr039-fixture",
        "strategy_id": "strategy_equal_weight_baseline",
        "signal_date": "2026-06-10",
        "initial_equity": 100_000.0,
        "estimated_price_policy": "raw_close",
        "rows": [
            {
                "symbol": "000001.SZ",
                "target_qty": 155,
                "target_weight": 0.0155,
                "estimated_price": 10.0,
                "reason": "buy lot rounding fixture",
            },
            {
                "symbol": "000002.SZ",
                "target_qty": 0,
                "target_weight": 0.0,
                "estimated_price": 20.0,
                "reason": "sell sellable cap fixture",
            },
        ],
        "operation_counts": _package_operation_counts(),
    }
    payload.update(overrides)
    return payload


def _trade_calendar() -> list[str]:
    return ["2026-06-10", "2026-06-11", "2026-06-12"]


def _current_positions() -> dict[str, Any]:
    return {
        "000001.SZ": {"qty": 0, "sellable_qty": 0, "average_cost": 0.0},
        "000002.SZ": {"qty": 300, "sellable_qty": 200, "average_cost": 18.0},
    }


def _admission_view_payload() -> dict[str, Any]:
    package = _valid_admission_package()
    return {
        "schema_version": "paper_simulation_admission_view_v1",
        "strategy_id": "strategy_equal_weight_baseline",
        "run_id": "run-cr039-fixture",
        "source_path": "fixture://strategy-admission-package",
        "package_hash": "0" * 64,
        "status": "PASS",
        "overall_admission": "research_baseline",
        "simulation_candidate": False,
        "not_authorization": True,
        "blocked_claims": package["blocked_claims"],
        "allowed_claims": package["allowed_claims"],
        "input_refs": package["input_refs"],
        "operation_counts": _package_operation_counts(),
        "candidate": package["strategy_candidates"][0],
        "validation": {"passed": True},
    }


def _intent(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "paper_order_intent_v1",
        "intent_id": "intent-cr041-fixture-000001",
        "source_run_id": "run-cr039-fixture",
        "signal_date": "2026-06-10",
        "target_trade_date": "2026-06-11",
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 100,
        "execution_price_policy": "raw_open",
        "valuation_price_policy": "raw_close",
        "not_authorization": True,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTERS),
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


def _broker_config(paper_simulation, **overrides: Any) -> Any:
    del paper_simulation
    config = {
        "slippage_bps": 10.0,
        "commission_bps": 3.0,
        "stamp_tax_bps": 10.0,
        "transfer_fee_bps": 0.1,
        "fixed_slippage_bps": 10.0,
        "commission_rate": 0.0003,
        "min_commission": 5.0,
        "stamp_duty_rate": 0.001,
        "transfer_fee_rate": 0.00001,
        "max_participation_rate": 0.10,
    }
    config.update(overrides)
    return config


def _valuation_rows() -> list[dict[str, Any]]:
    return [
        {"trade_date": "2026-06-11", "symbol": "000001.SZ", "raw_close": 10.5},
        {"trade_date": "2026-06-12", "symbol": "000001.SZ", "raw_close": 11.0},
    ]


def test_s01_strategy_admission_package_reader_accepts_research_baseline_without_upgrading_authorization(
    paper_simulation, tmp_path: Path
) -> None:
    package_path = _write_json(tmp_path / "STRATEGY-ADMISSION-PACKAGE.json", _valid_admission_package())

    payload = paper_simulation.load_strategy_admission_package(package_path)
    validation = _jsonable(
        paper_simulation.validate_strategy_admission_package(payload, "strategy_equal_weight_baseline")
    )
    view = _jsonable(
        paper_simulation.build_admission_view(payload, package_path, "strategy_equal_weight_baseline")
    )

    assert _passed(validation) is True
    assert view["schema_version"] == "paper_simulation_admission_view_v1"
    assert view["strategy_id"] == "strategy_equal_weight_baseline"
    assert view["source_run_id"] == "run-cr039-fixture"
    assert view["source_portfolio_id"] == "portfolio-cr039-equal-weight-fixture"
    assert view["simulation_candidate"] is False
    assert view["not_authorization"] is True
    assert view["not_simulation_authorization"] is True
    assert view["not_live_authorization"] is True
    assert view["not_broker_order"] is True
    assert isinstance(view["package_hash"], str) and len(view["package_hash"]) == 64
    _assert_zero_counters(view["operation_counts"])


@pytest.mark.parametrize(
    ("mutator", "expected_reason"),
    [
        (
            lambda package: package["operation_counts"].update({"credential_read": 1}),
            "credential_read",
        ),
        (
            lambda package: package.update({"allowed_claims": [{"claim": "simulation_ready", "status": "allowed"}]}),
            "simulation_ready",
        ),
        (
            lambda package: package.update({"token": "should-block"}),
            "token",
        ),
        (
            lambda package: package.update({"status": "FAIL"}),
            "package_not_passed",
        ),
    ],
)
def test_s01_strategy_admission_package_validation_fails_closed_for_unsafe_or_invalid_inputs(
    paper_simulation, mutator, expected_reason: str
) -> None:
    package = _valid_admission_package()
    mutator(package)

    validation = _jsonable(
        paper_simulation.validate_strategy_admission_package(package, "strategy_equal_weight_baseline")
    )

    assert _passed(validation) is False
    assert _status(validation).lower() in {"blocked", "failed", "fail", "invalid"}
    assert any(expected_reason in reason for reason in _blocked_reasons(validation))


def test_s01_validation_failure_to_dict_is_json_safe_for_audit(paper_simulation) -> None:
    violation = paper_simulation.PaperSimulationViolation(
        code="fixture_violation",
        message="fixture validation failure",
        field="fixture_field",
    )
    validation = paper_simulation.PaperSimulationValidation(False, (violation,))

    payload = validation.to_dict()

    assert payload["passed"] is False
    assert payload["status"] == "blocked"
    assert payload["violations"] == [
        {
            "code": "fixture_violation",
            "message": "fixture validation failure",
            "severity": "blocker",
            "field": "fixture_field",
        }
    ]
    assert "fixture_field" in " ".join(payload["blocked_reasons"])


def test_s02_target_portfolio_builds_t_plus_one_raw_order_intents_without_broker_fields(
    paper_simulation,
) -> None:
    intents = _jsonable(
        paper_simulation.build_order_intents(
            _admission_view_payload(),
            _target_portfolio(),
            _trade_calendar(),
            current_positions=_current_positions(),
        )
    )

    assert [intent["symbol"] for intent in intents] == ["000001.SZ", "000002.SZ"]
    buy_intent, sell_intent = intents
    assert buy_intent["schema_version"] == "paper_order_intent_v1"
    assert buy_intent["signal_date"] == "2026-06-10"
    assert buy_intent["target_trade_date"] == "2026-06-11"
    assert buy_intent["side"] == "buy"
    assert buy_intent["target_qty"] == 100
    assert buy_intent["execution_price_policy"] == "raw_open"
    assert buy_intent.get("valuation_price_policy", "raw_close") == "raw_close"
    assert buy_intent["not_authorization"] is True
    _assert_zero_counters(buy_intent.get("operation_counts", buy_intent["operation_counters"]))
    assert sell_intent["side"] == "sell"
    assert sell_intent["target_qty"] == 200
    assert any("sellable" in str(value).lower() or "可卖" in str(value) for value in sell_intent.values())
    _assert_no_forbidden_payload_keys(intents)


@pytest.mark.parametrize(
    "target_payload",
    [
        {"rows": [{"symbol": "000001.SZ", "target_qty": 100, "account_id": "acct-should-block"}]},
        {"estimated_price_policy": "qfq", "rows": [{"symbol": "000001.SZ", "target_qty": 100}]},
        {"rows": [{"symbol": "000001.SZ"}]},
    ],
)
def test_s02_target_portfolio_builder_fails_closed_for_broker_pollution_non_raw_or_missing_targets(
    paper_simulation, target_payload: dict[str, Any]
) -> None:
    target = _target_portfolio(**target_payload)

    result = _jsonable(
        paper_simulation.build_order_intents(
            _admission_view_payload(),
            target,
            _trade_calendar(),
            current_positions=_current_positions(),
        )
    )

    if isinstance(result, list):
        assert result
        assert all(item["side"] == "rejected" or item.get("blocked_reasons") for item in result)
    else:
        assert _passed(result) is False
        assert _status(result).lower() in {"blocked", "failed", "fail", "invalid"}


def test_s03_fill_engine_applies_slippage_costs_and_volume_cap_without_mutating_ledger(paper_simulation) -> None:
    intents = [
        _intent(intent_id="buy-000001", symbol="000001.SZ", side="buy", target_qty=100),
        _intent(intent_id="sell-000002", symbol="000002.SZ", side="sell", target_qty=200),
        _intent(intent_id="partial-000003", symbol="000003.SZ", side="buy", target_qty=1_000),
    ]
    market_data = [
        _market_row(symbol="000001.SZ", raw_open=10.0, raw_close=10.5, volume=10_000, up_limit=11.0, down_limit=9.0),
        _market_row(symbol="000002.SZ", raw_open=20.0, raw_close=19.8, volume=10_000, up_limit=22.0, down_limit=18.0),
        _market_row(symbol="000003.SZ", raw_open=30.0, raw_close=30.5, volume=3_000, up_limit=33.0, down_limit=27.0),
    ]

    fills = _jsonable(
        paper_simulation.simulate_fills(
            intents,
            market_data,
            _broker_config(paper_simulation),
            cash_snapshot={"cash": 100_000.0},
            position_snapshot={"000002.SZ": {"qty": 300, "sellable_qty": 300}},
        )
    )

    by_symbol = {fill["symbol"]: fill for fill in fills}
    buy_fill = by_symbol["000001.SZ"]
    sell_fill = by_symbol["000002.SZ"]
    partial_fill = by_symbol["000003.SZ"]

    assert buy_fill["status"] == "filled"
    assert buy_fill["filled_qty"] == 100
    assert buy_fill["exec_price"] == pytest.approx(10.01)
    assert buy_fill["costs"]["commission"] == pytest.approx(5.0)
    assert buy_fill["costs"].get("stamp_duty", buy_fill["costs"].get("stamp_tax", 0.0)) == pytest.approx(0.0)
    assert sell_fill["status"] == "filled"
    assert sell_fill["exec_price"] == pytest.approx(19.98)
    assert sell_fill["costs"].get("stamp_duty", sell_fill["costs"].get("stamp_tax")) == pytest.approx(
        200 * 19.98 * 0.001
    )
    assert partial_fill["status"] == "partial"
    assert partial_fill["filled_qty"] == 300
    assert partial_fill.get("unfilled_qty", partial_fill["requested_qty"] - partial_fill["filled_qty"]) == 700
    _assert_no_forbidden_payload_keys(fills)


@pytest.mark.parametrize(
    ("intent", "market_row", "expected_reason"),
    [
        (_intent(side="buy"), _market_row(raw_open=11.0, up_limit=11.0), "limit"),
        (_intent(side="sell"), _market_row(raw_open=9.0, down_limit=9.0), "limit"),
        (_intent(side="buy"), _market_row(trade_status="suspended"), "suspend"),
        (_intent(side="buy"), {"trade_date": "2026-06-11", "symbol": "000001.SZ", "raw_open": 10.0}, "missing"),
    ],
)
def test_s03_fill_engine_rejects_limit_suspension_and_missing_market_fields_fail_closed(
    paper_simulation, intent: dict[str, Any], market_row: dict[str, Any], expected_reason: str
) -> None:
    fills = _jsonable(
        paper_simulation.simulate_fills(
            [intent],
            [market_row],
            _broker_config(paper_simulation),
            cash_snapshot={"cash": 100_000.0},
            position_snapshot={"000001.SZ": {"qty": 300, "sellable_qty": 300}},
        )
    )

    assert len(fills) == 1
    assert fills[0]["status"] == "rejected"
    assert expected_reason in str(fills[0].get("reason_code", fills[0].get("reason", ""))).lower()


def test_s04_ledger_updates_cash_positions_equity_and_t_plus_one_sellable_quantities(paper_simulation) -> None:
    filled_buy = {
        "schema_version": "paper_fill_v1",
        "fill_id": "fill-buy-000001",
        "intent_id": "buy-000001",
        "trade_date": "2026-06-11",
        "symbol": "000001.SZ",
        "side": "buy",
        "status": "filled",
        "filled_qty": 100,
        "exec_price": 10.0,
        "gross_amount": 1_000.0,
        "costs": {"commission": 5.0, "stamp_duty": 0.0, "transfer_fee": 0.0, "total": 5.0},
        "not_authorization": True,
    }

    result = _jsonable(
        paper_simulation.apply_fills_to_ledger(
            initial_state={"cash": 10_000.0, "positions": {}},
            fills=[filled_buy],
            valuation_data=_valuation_rows(),
            config={"reconciliation_tolerance": 0.01},
        )
    )

    ending_cash = result.get("cash", {}).get("ending_cash", result["final_state"]["cash"])
    assert ending_cash == pytest.approx(8_995.0)
    final_positions = {row["symbol"]: row for row in result["positions"]}
    assert final_positions["000001.SZ"].get("qty", final_positions["000001.SZ"].get("quantity")) == 100
    assert final_positions["000001.SZ"]["sellable_qty"] == 100
    equity_by_date = {row["trade_date"]: row for row in result["equity_curve"]}
    assert equity_by_date["2026-06-12"]["equity"] == pytest.approx(10_095.0)
    assert result["reconciliation"]["status"] in {"pass", "passed"}
    assert abs(result["reconciliation"]["diff"]) <= 0.01


def test_s04_ledger_never_allows_negative_cash_or_positions_and_blocks_missing_raw_close(paper_simulation) -> None:
    buy_with_missing_close = {
        "schema_version": "paper_fill_v1",
        "fill_id": "fill-buy-missing-close",
        "intent_id": "buy-missing-close",
        "trade_date": "2026-06-11",
        "symbol": "000001.SZ",
        "side": "buy",
        "status": "filled",
        "filled_qty": 100,
        "exec_price": 10.0,
        "gross_amount": 1_000.0,
        "costs": {"commission": 5.0, "stamp_duty": 0.0, "transfer_fee": 0.0, "total": 5.0},
        "not_authorization": True,
    }
    missing_close = [{"trade_date": "2026-06-11", "symbol": "000001.SZ"}]

    result = _jsonable(
            paper_simulation.apply_fills_to_ledger(
                initial_state={"cash": 10_000.0, "positions": {}},
                fills=[buy_with_missing_close],
                valuation_data=missing_close,
                config={"reconciliation_tolerance": 0.01},
            )
    )

    assert _passed(result) is False
    assert _status(result).lower() in {"blocked", "failed", "fail", "invalid"}
    assert result.get("cash", {}).get("ending_cash", result.get("final_state", {}).get("cash", 0.0)) >= 0.0
    assert all(row.get("qty", row.get("quantity", 0)) >= 0 for row in result.get("positions", []))
    reasons = _blocked_reasons(result)
    assert any("cash" in reason or "raw_close" in reason or "close" in reason for reason in reasons)


def test_s05_run_paper_simulation_writes_local_artifacts_and_zero_forbidden_counters(
    paper_simulation, tmp_path: Path
) -> None:
    admission_path = _write_json(tmp_path / "inputs" / "STRATEGY-ADMISSION-PACKAGE.json", _valid_admission_package())
    target_path = _write_json(tmp_path / "inputs" / "target_portfolio.json", _target_portfolio())
    market_path = _write_json(
        tmp_path / "inputs" / "market_data.json",
        [
            _market_row(symbol="000001.SZ", raw_open=10.0, raw_close=10.5, volume=10_000),
            _market_row(symbol="000002.SZ", raw_open=20.0, raw_close=19.8, volume=10_000),
        ],
    )
    output_root = tmp_path / "reports" / "paper_simulation"

    result = _jsonable(
        paper_simulation.run_paper_simulation(
            {
                "run_id": "run-cr041-fixture",
                "admission_package": str(admission_path),
                "admission_package_path": str(admission_path),
                "strategy_package_path": str(admission_path),
                "target_portfolio": str(target_path),
                "target_portfolio_path": str(target_path),
                "market_data": str(market_path),
                "market_data_path": str(market_path),
                "trade_calendar": _trade_calendar(),
                "initial_state": {"cash": 100_000.0, "positions": _current_positions()},
                "current_positions": _current_positions(),
                "initial_cash": 100_000.0,
                "output_root": str(output_root),
                "expected_strategy_id": "strategy_equal_weight_baseline",
                "cost_config": {
                    "fixed_slippage_bps": 10.0,
                    "commission_rate": 0.0003,
                    "min_commission": 5.0,
                    "stamp_duty_rate": 0.001,
                    "transfer_fee_rate": 0.00001,
                    "max_participation_rate": 0.10,
                },
            }
        )
    )

    assert _passed(result) is True
    run_dir = output_root / "run-cr041-fixture"
    expected_artifacts = {
        "order_intents.json",
        "fills.json",
        "positions.json",
        "cash_ledger.json",
        "equity_curve.json",
        "reconciliation.json",
        "run_manifest.json",
        "PAPER-SIMULATION-REPORT.json",
        "PAPER-SIMULATION-REPORT.md",
    }
    assert expected_artifacts.issubset({path.name for path in run_dir.iterdir()})

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "PAPER-SIMULATION-REPORT.json").read_text(encoding="utf-8"))
    summary_md = (run_dir / "PAPER-SIMULATION-REPORT.md").read_text(encoding="utf-8")

    assert manifest["run_id"] == "run-cr041-fixture"
    assert manifest["not_authorization"] is True
    assert manifest["not_simulation_authorization"] is True
    assert manifest["not_live_authorization"] is True
    assert manifest["not_broker_order"] is True
    _assert_zero_counters(manifest["operation_counts"])
    _assert_zero_counters(report["operation_counts"])
    assert "not_authorization" in summary_md
    assert "simulation_ready" in summary_md
    assert "live_ready" in summary_md
    _assert_no_forbidden_payload_keys(report)


def test_s05_runner_blocks_nonzero_forbidden_counters_without_writing_artifacts(
    paper_simulation, tmp_path: Path
) -> None:
    unsafe_package = _valid_admission_package()
    unsafe_package["operation_counts"]["provider_fetch"] = 1
    admission_path = _write_json(tmp_path / "inputs" / "STRATEGY-ADMISSION-PACKAGE.json", unsafe_package)
    target_path = _write_json(tmp_path / "inputs" / "target_portfolio.json", _target_portfolio())
    market_path = _write_json(tmp_path / "inputs" / "market_data.json", [_market_row()])
    output_root = tmp_path / "reports" / "paper_simulation"

    result = _jsonable(
        paper_simulation.run_paper_simulation(
            {
                "run_id": "run-cr041-blocked",
                "admission_package": str(admission_path),
                "admission_package_path": str(admission_path),
                "strategy_package_path": str(admission_path),
                "target_portfolio": str(target_path),
                "target_portfolio_path": str(target_path),
                "market_data": str(market_path),
                "market_data_path": str(market_path),
                "trade_calendar": _trade_calendar(),
                "initial_state": {"cash": 100_000.0, "positions": _current_positions()},
                "current_positions": _current_positions(),
                "initial_cash": 100_000.0,
                "output_root": str(output_root),
                "expected_strategy_id": "strategy_equal_weight_baseline",
            }
        )
    )

    assert _passed(result) is False
    assert _status(result).lower() in {"blocked", "failed", "fail", "invalid"}
    assert "provider_fetch" in " ".join(_blocked_reasons(result))
    assert not (output_root / "run-cr041-blocked").exists()


def test_s05_cli_entrypoint_exists_and_missing_input_path_fails_closed(tmp_path: Path) -> None:
    cli = importlib.import_module("scripts.run_paper_simulation")
    assert hasattr(cli, "main")

    exit_code = cli.main(
        [
            "--admission-package",
            str(tmp_path / "missing-admission.json"),
            "--target-portfolio",
            str(tmp_path / "target.json"),
            "--market-data",
            str(tmp_path / "market.json"),
            "--initial-cash",
            "100000",
            "--run-id",
            "run-cr041-missing-input",
            "--output-root",
            str(tmp_path / "reports"),
        ]
    )

    assert int(exit_code) != 0
    assert not (tmp_path / "reports" / "run-cr041-missing-input").exists()


def test_s05_static_import_boundary_excludes_provider_broker_network_and_runtime_side_effects() -> None:
    paths = [
        PROJECT_ROOT / "engine" / "paper_simulation.py",
        PROJECT_ROOT / "scripts" / "run_paper_simulation.py",
    ]
    forbidden_import_roots = {
        "akshare",
        "aiohttp",
        "backtrader",
        "broker",
        "httpx",
        "jqdatasdk",
        "miniqmt",
        "qmt",
        "requests",
        "socket",
        "subprocess",
        "trading",
        "tushare",
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
    for path in paths:
        assert path.exists(), f"missing CR041 contract file: {path.relative_to(PROJECT_ROOT)}"
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
