from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.events import evaluate_event_gate
from engine.research_dataset import (
    ResearchDataset,
    apply_tradability_gates,
    build_tradability_gate_matrix,
)
from engine.trade_status import evaluate_trade_status_gate
from engine.trading_constraints import evaluate_price_limit_gate
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
)
from market_data.readers import ReaderResult, TradabilityInputRequest, read_tradability_inputs


TARGET_FILES = (
    Path("market_data/readers.py"),
    Path("engine/trade_status.py"),
    Path("engine/trading_constraints.py"),
    Path("engine/events.py"),
    Path("engine/research_dataset.py"),
)


def test_read_tradability_inputs_missing_lake_root_is_typed_and_does_not_call_reader() -> None:
    calls: list[str] = []

    result = read_tradability_inputs(
        TradabilityInputRequest(lake_root=None, trade_dates=("2026-01-05",), symbols=("AAA",)),
        reader=lambda dataset, *_args, **_kwargs: calls.append(dataset),
    )

    assert calls == []
    assert set(result) == {DATASET_TRADE_STATUS, DATASET_PRICES_LIMIT, DATASET_EVENTS, DATASET_STOCK_BASIC}
    assert all(item.status == "required_missing" for item in result.values())
    assert all(item.remediation_spec["auto_execute"] is False for item in result.values())


def test_read_tradability_inputs_passes_filters_without_fetching_or_writing(tmp_path: Path) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def reader(dataset: str, _lake_root: Path, filters: dict[str, Any] | None = None, **_kwargs: Any) -> ReaderResult:
        calls.append((dataset, dict(filters or {})))
        frames = {
            DATASET_TRADE_STATUS: trade_status_frame(["AAA"]),
            DATASET_PRICES_LIMIT: prices_limit_frame(["AAA"]),
            DATASET_EVENTS: events_frame([]),
            DATASET_STOCK_BASIC: lifecycle_frame(["AAA"]),
        }
        return available_reader(dataset, frames[dataset])

    result = read_tradability_inputs(
        {
            "lake_root": tmp_path / "lake",
            "trade_dates": ("2026-01-05", "2026-01-02"),
            "symbols": ["AAA"],
        },
        reader=reader,
    )

    assert all(item.status == "available" for item in result.values())
    assert calls[0] == (
        DATASET_TRADE_STATUS,
        {"start_date": "2026-01-02", "end_date": "2026-01-05", "symbols": ("AAA",)},
    )
    assert {dataset for dataset, _filters in calls} == {
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
        DATASET_STOCK_BASIC,
    }


def test_individual_gates_return_structured_statuses() -> None:
    suspended = {"trade_date": "2026-01-05", "symbol": "SUSP", "side": "buy", "execution_price": 10.0}
    trade_gate = evaluate_trade_status_gate(
        suspended,
        available_reader(DATASET_TRADE_STATUS, trade_status_frame(["SUSP"], suspended={"SUSP"})),
        available_reader(DATASET_STOCK_BASIC, lifecycle_frame(["SUSP"])),
        min_listing_days=20,
    )
    assert trade_gate.status == "blocked"
    assert trade_gate.can_buy is False
    assert trade_gate.blocked_reason == "suspended"
    assert trade_gate.to_dict()["suspended"] is True

    limit_buy = evaluate_price_limit_gate(
        {"trade_date": "2026-01-05", "symbol": "UP", "side": "buy", "execution_price": 11.0},
        available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(["UP"])),
    )
    assert limit_buy.status == "blocked"
    assert limit_buy.blocked_reason == "limit_up_blocked_buy"
    assert limit_buy.can_buy is False

    event_gate = evaluate_event_gate(
        {"trade_date": "2026-01-05", "symbol": "EVT", "side": "buy"},
        available_reader(DATASET_EVENTS, events_frame(["EVT"])),
        decision_time="2026-01-05",
    )
    assert event_gate.status == "blocked"
    assert event_gate.blocked_reason == "event_blocked"
    assert event_gate.event_blocked is True


def test_build_tradability_matrix_covers_six_gate_classes() -> None:
    symbols = ["AAA", "SUSP", "ST", "NOTRADE", "NEW", "UP", "DOWN", "EVT"]
    intents = [
        intent("AAA", "buy", 10.0),
        intent("SUSP", "buy", 10.0),
        intent("ST", "sell", 10.0),
        intent("NOTRADE", "buy", 10.0),
        intent("NEW", "buy", 10.0),
        intent("UP", "buy", 11.0),
        intent("DOWN", "sell", 9.0),
        intent("EVT", "buy", 10.0),
    ]

    matrix = build_tradability_gate_matrix(
        intents,
        {
            DATASET_TRADE_STATUS: available_reader(
                DATASET_TRADE_STATUS,
                trade_status_frame(symbols, suspended={"SUSP"}, st={"ST"}, no_trade={"NOTRADE"}),
            ),
            DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(symbols)),
            DATASET_EVENTS: available_reader(DATASET_EVENTS, events_frame(["EVT"])),
            DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, lifecycle_frame(symbols, new_symbols={"NEW"})),
        },
        realism_mode="production_strict",
        decision_time="2026-01-05",
        min_listing_days=20,
    )

    assert matrix.status == "blocked"
    assert matrix.available_count == 1
    assert matrix.blocked_count == 7
    assert matrix.required_missing_count == 0
    assert {
        "suspended",
        "st_status",
        "no_trade",
        "min_listing_days",
        "limit_up_blocked_buy",
        "limit_down_blocked_sell",
        "event_blocked",
    } <= set(matrix.reason_counts)
    for row in matrix.rows:
        if row.tradability_gate_status != "available":
            payload = row.to_dict()
            assert payload["trade_date"]
            assert payload["symbol"]
            assert payload["side"] in {"buy", "sell", "hold"}
            assert payload["blocked_reason"]


def test_missing_or_empty_p0_gate_fails_closed_and_blocks_real_claims() -> None:
    missing_source = build_tradability_gate_matrix(
        [intent("AAA", "buy", 10.0)],
        {
            DATASET_TRADE_STATUS: ReaderResult(
                status="required_missing",
                issues=[{"code": "source_unresolved", "dataset": DATASET_TRADE_STATUS}],
                remediation_spec={"auto_execute": False},
            ),
            DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(["AAA"])),
            DATASET_EVENTS: available_reader(DATASET_EVENTS, events_frame([])),
            DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, lifecycle_frame(["AAA"])),
        },
        realism_mode="production_strict",
        decision_time="2026-01-05",
    )
    assert missing_source.status == "required_missing"
    assert missing_source.available_count == 0
    assert any(item["claim"] == "real_tradable_execution" for item in missing_source.blocked_claims)
    assert missing_source.remediation_spec["auto_execute"] is False

    empty_status = build_tradability_gate_matrix(
        [intent("AAA", "buy", 10.0)],
        {
            DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, trade_status_frame([])),
            DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(["AAA"])),
            DATASET_EVENTS: available_reader(DATASET_EVENTS, events_frame([])),
            DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, lifecycle_frame(["AAA"])),
        },
        realism_mode="production_strict",
        decision_time="2026-01-05",
    )
    assert empty_status.status == "required_missing"
    assert empty_status.available_count == 0
    assert empty_status.rows[0].blocked_reason == "trade_status_empty"


def test_events_available_at_missing_or_future_is_fail_fast() -> None:
    missing_available_at = evaluate_event_gate(
        {"trade_date": "2026-01-05", "symbol": "EVT", "side": "buy"},
        available_reader(DATASET_EVENTS, events_frame(["EVT"]).drop(columns=["available_at"])),
        decision_time="2026-01-05",
    )
    assert missing_available_at.status == "required_missing"
    assert missing_available_at.blocked_reason == "available_at_missing"

    future_available_at = evaluate_event_gate(
        {"trade_date": "2026-01-05", "symbol": "EVT", "side": "buy"},
        available_reader(DATASET_EVENTS, events_frame(["EVT"], available_at="2026-01-06")),
        decision_time="2026-01-05",
    )
    assert future_available_at.status == "blocked"
    assert future_available_at.blocked_reason == "event_future_available_at"


def test_apply_tradability_gates_production_strict_and_exploratory_claims() -> None:
    base = ResearchDataset(
        status="available",
        metadata={
            "realism_mode": "exploratory",
            "allowed_claims": [
                "framework_validation",
                "real_tradable_execution",
                "tradability_screened",
                "true_fillability",
                "realistic_fillability",
            ],
            "known_limitations": [],
        },
        allowed_claims=[
            "framework_validation",
            "real_tradable_execution",
            "tradability_screened",
            "true_fillability",
            "realistic_fillability",
        ],
        reader_results={
            DATASET_TRADE_STATUS: ReaderResult(status="required_missing", issues=[{"code": "source_unresolved"}]),
            DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(["AAA"])),
            DATASET_EVENTS: available_reader(DATASET_EVENTS, events_frame([])),
            DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, lifecycle_frame(["AAA"])),
        },
    )

    exploratory = apply_tradability_gates(base, [intent("AAA", "buy", 10.0)], realism_mode="exploratory")

    assert exploratory.status == "available_with_warnings"
    assert exploratory.metadata["tradability_gate_status"] == "required_missing"
    assert exploratory.metadata["tradability_available_count"] == 0
    assert {"framework_validation", "exploratory_analysis"} <= set(exploratory.allowed_claims)
    assert not {
        "real_tradable_execution",
        "tradability_screened",
        "true_fillability",
        "realistic_fillability",
    } & set(exploratory.allowed_claims)
    assert any(item["claim"] == "real_tradable_execution" for item in exploratory.blocked_claims)
    assert exploratory.known_limitations

    strict = apply_tradability_gates(base, [intent("AAA", "buy", 10.0)], realism_mode="production_strict")
    assert strict.status == "required_missing"
    assert strict.gate_result.status == "fail"
    assert strict.metadata["remediation_spec"]["auto_execute"] is False


def test_s03_forbidden_boundaries_are_static_and_no_secret_leakage(monkeypatch) -> None:
    fake_secret = "CR011_S03_FAKE_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("CR011_S03_FAKE_SECRET", fake_secret)
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
    }
    for path in TARGET_FILES:
        imports = imported_modules(path)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imports for forbidden in forbidden_modules)
        source = path.read_text(encoding="utf-8")
        assert "reports/experiment_17_21/factor_strategy_report.md" not in source
        assert "TUSHARE_TOKEN" not in source

    dataset = apply_tradability_gates(
        ResearchDataset(
            status="available",
            metadata={"realism_mode": "production_strict"},
            reader_results={
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, trade_status_frame(["AAA"])),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, prices_limit_frame(["AAA"])),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, events_frame([])),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, lifecycle_frame(["AAA"])),
            },
        ),
        [intent("AAA", "buy", 10.0)],
        realism_mode="production_strict",
        decision_time="2026-01-05",
        min_listing_days=20,
    )
    combined = json.dumps([dataset.metadata, [issue.to_dict() for issue in dataset.issues]], ensure_ascii=False, default=str)
    assert fake_secret not in combined
    assert dataset.metadata.get("network_calls", 0) == 0
    assert dataset.metadata.get("lake_writes", 0) == 0
    assert dataset.metadata.get("credential_reads", 0) == 0
    assert dataset.metadata.get("legacy_data_operations", 0) == 0


def intent(symbol: str, side: str, execution_price: float) -> dict[str, Any]:
    return {
        "trade_date": "2026-01-05",
        "symbol": symbol,
        "side": side,
        "execution_price": execution_price,
        "decision_time": "2026-01-05",
    }


def trade_status_frame(
    symbols: list[str],
    *,
    suspended: set[str] | None = None,
    st: set[str] | None = None,
    no_trade: set[str] | None = None,
) -> pd.DataFrame:
    suspended = suspended or set()
    st = st or set()
    no_trade = no_trade or set()
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": symbol,
                "can_buy": True,
                "can_sell": True,
                "is_suspended": symbol in suspended,
                "is_st": symbol in st,
                "is_tradable": symbol not in no_trade,
                "no_trade": symbol in no_trade,
                "volume": 0 if symbol in no_trade else 1000,
                "status_reason": "fixture",
                "available_at": "2026-01-05",
                "source_interface": "trade_status.daily",
            }
            for symbol in symbols
        ]
    )


def prices_limit_frame(symbols: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-05",
                "symbol": symbol,
                "limit_up": 11.0,
                "limit_down": 9.0,
                "can_buy": True,
                "can_sell": True,
                "available_at": "2026-01-05",
                "source_interface": "prices_limit.daily",
            }
            for symbol in symbols
        ]
    )


def events_frame(symbols: list[str], *, available_at: str = "2026-01-04") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_date": "2026-01-05",
                "symbol": symbol,
                "event_type": "halt",
                "is_blocking": True,
                "available_at": available_at,
                "source_interface": "events.disclosure",
                "source_run_id": "run-events",
            }
            for symbol in symbols
        ],
        columns=[
            "event_date",
            "symbol",
            "event_type",
            "is_blocking",
            "available_at",
            "source_interface",
            "source_run_id",
        ],
    )


def lifecycle_frame(symbols: list[str], *, new_symbols: set[str] | None = None) -> pd.DataFrame:
    new_symbols = new_symbols or set()
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "list_date": "2026-01-01" if symbol in new_symbols else "2020-01-01",
                "delist_date": None,
                "list_status": "L",
                "available_at": "2026-01-01",
                "source_interface": "stock_basic.snapshot",
            }
            for symbol in symbols
        ]
    )


def available_reader(dataset: str, frame: pd.DataFrame) -> ReaderResult:
    return ReaderResult(
        status="available",
        frame=frame,
        catalog_entry=CatalogEntry(
            dataset=dataset,
            quality_status="pass",
            dataset_status="available",
            readiness_status="available",
            source="fixture",
            source_interface=f"{dataset}.fixture",
            latest_manifest_run_id=f"run-{dataset}",
            published=True,
        ),
    )


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
