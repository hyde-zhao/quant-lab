from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.backtest import (
    BacktestConfig,
    ExecutionPolicyConfig,
    build_execution_price_frame,
    run_backtest,
)
from engine.research_dataset import (
    ResearchDataset,
    TradabilityGateMatrix,
    TradabilityGateRow,
    evaluate_execution_price_gate,
    resolve_execution_price_policy,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import DATASET_PRICES
from market_data.readers import ExecutionFeedRequest, ReaderResult, read_execution_feed


TARGET_FILES = (
    Path("market_data/readers.py"),
    Path("engine/research_dataset.py"),
    Path("engine/backtest.py"),
)


def test_read_execution_feed_missing_lake_root_is_typed_and_does_not_call_reader() -> None:
    calls: list[str] = []

    result = read_execution_feed(
        ExecutionFeedRequest(lake_root=None, trade_dates=("2026-01-05",), symbols=("AAA",)),
        reader=lambda dataset, *_args, **_kwargs: calls.append(dataset),
    )

    assert calls == []
    assert result.status == "required_missing"
    assert result.remediation_spec["auto_execute"] is False
    assert result.issues[0]["code"] == "lake_root_missing"


def test_read_execution_feed_exposes_ohlcv_vwap_status_without_deriving_vwap(tmp_path: Path) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def reader(dataset: str, _lake_root: Path, filters: dict[str, Any] | None = None, **_kwargs: Any) -> ReaderResult:
        calls.append((dataset, dict(filters or {})))
        return available_prices_reader(prices_frame(include_vwap=False))

    result = read_execution_feed(
        {
            "lake_root": tmp_path / "lake",
            "trade_dates": ("2026-01-06", "2026-01-05"),
            "symbols": ["AAA"],
        },
        reader=reader,
    )

    assert result.status == "available"
    assert calls == [
        (
            DATASET_PRICES,
            {"start_date": "2026-01-05", "end_date": "2026-01-06", "symbols": ("AAA",)},
        )
    ]
    assert result.frame is not None
    assert {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "vwap",
        "vwap_status",
        "vwap_or_proxy",
        "source_interface",
        "source_run_id",
    } <= set(result.frame.columns)
    assert set(result.frame["vwap_status"]) == {"required_missing"}
    assert result.frame["vwap"].isna().all()
    assert any(issue["code"] == "vwap_required_missing" for issue in result.issues)


@pytest.mark.parametrize("policy", ["open", "close", "vwap", "close_proxy"])
def test_execution_price_policy_accepts_only_four_exact_values(policy: str) -> None:
    result = resolve_execution_price_policy(
        {"policy": policy, "realism_mode": "production_strict"},
        available_prices_reader(prices_frame()),
    )

    assert result.execution_price_policy == policy


@pytest.mark.parametrize(
    "policy_request",
    [
        "next_open_day_close_proxy",
        " open ",
        "",
        "OPEN",
        {"policy": " open "},
        {"policy": ""},
        {"policy": "OPEN"},
        {"execution_price_policy": " close_proxy "},
        ExecutionPolicyConfig(policy=" close_proxy "),
    ],
)
def test_execution_price_policy_rejects_invalid_values(policy_request: Any) -> None:
    with pytest.raises(ValueError, match="invalid_execution_price_policy"):
        if isinstance(policy_request, ExecutionPolicyConfig):
            build_execution_price_frame(prices_frame(), policy_request)
        else:
            resolve_execution_price_policy(policy_request, available_prices_reader(prices_frame()))


def test_execution_price_policy_defaults_only_when_policy_field_missing() -> None:
    resolver_result = resolve_execution_price_policy({}, available_prices_reader(prices_frame()))
    frame_result = build_execution_price_frame(prices_frame(), {})

    assert resolver_result.execution_price_policy == "close_proxy"
    assert frame_result.metadata["execution_price_policy"] == "close_proxy"


def test_backtest_policy_coercion_rejects_explicit_empty_or_whitespace_metadata() -> None:
    index = [item.date() for item in pd.bdate_range("2026-01-01", periods=8)]
    close_df = pd.DataFrame({"AAA": range(10, 18), "BBB": range(20, 12, -1)}, index=index)
    full_feed = prices_frame(dates=tuple(str(item) for item in index), symbols=("AAA", "BBB"))

    with pytest.raises(ValueError, match="invalid_execution_price_policy"):
        run_backtest(
            close_df,
            BacktestConfig(lookback_days=2, rebalance_freq=2, top_fraction=0.5),
            metadata={"execution_price_policy": " open "},
            execution_feed=full_feed,
        )

    with pytest.raises(ValueError, match="invalid_execution_price_policy"):
        run_backtest(
            close_df,
            BacktestConfig(lookback_days=2, rebalance_freq=2, top_fraction=0.5),
            execution_policy={"policy": ""},
            execution_feed=full_feed,
        )

    defaulted = run_backtest(
        close_df,
        BacktestConfig(lookback_days=2, rebalance_freq=2, top_fraction=0.5),
        execution_feed=full_feed,
    )
    assert defaulted.metadata["execution_price_policy"] == "close_proxy"


def test_vwap_missing_does_not_fallback_to_close() -> None:
    feed = available_prices_reader(prices_frame(vwap_status="required_missing", vwap=None))

    result = resolve_execution_price_policy("vwap", feed)

    assert result.status == "required_missing"
    assert result.rows[0]["execution_price"] is None
    assert result.rows[0]["execution_price"] != 12.0
    assert result.rows[0]["unfilled_reason"] == "required_missing"
    assert result.metadata["close_substitution_count"] == 0
    assert any(item["claim"] == "real_vwap_execution" for item in result.blocked_claims)


def test_close_proxy_requires_degradation_and_blocks_real_execution_claims() -> None:
    feed = available_prices_reader(prices_frame(vwap_status="required_missing", vwap=None))

    result = resolve_execution_price_policy("close_proxy", feed)

    assert result.status == "available_with_warnings"
    assert result.rows[0]["execution_price"] == 12.0
    assert result.rows[0]["execution_degradation_reason"] == "policy_explicit_close_proxy"
    assert result.rows[0]["vwap_or_proxy"] == "proxy"
    blocked = {item["claim"] for item in result.blocked_claims}
    assert {"real_vwap_execution", "vwap_fill_claim", "real_open_execution", "real_tradable_execution"} <= blocked


def test_open_and_close_missing_prices_are_not_filled() -> None:
    frame = prices_frame()
    frame.loc[0, "open"] = 0.0
    frame.loc[0, "close"] = pd.NA
    feed = available_prices_reader(frame)

    open_result = resolve_execution_price_policy("open", feed)
    close_result = resolve_execution_price_policy("close", feed)

    assert open_result.rows[0]["execution_price"] is None
    assert open_result.rows[0]["unfilled_reason"] == "price_not_finite"
    assert close_result.rows[0]["execution_price"] is None
    assert close_result.rows[0]["unfilled_reason"] == "price_not_finite"
    assert open_result.metadata["missing_price_fill_count"] == 0
    assert close_result.metadata["missing_price_fill_count"] == 0


def test_tradability_blocked_row_is_not_reallowed_by_execution_price() -> None:
    matrix = TradabilityGateMatrix(
        rows=(
            TradabilityGateRow(
                trade_date="2026-01-05",
                symbol="AAA",
                side="buy",
                can_buy=False,
                can_sell=False,
                tradability_gate_status="blocked",
                blocked_reason="suspended",
                blocked_reasons=("suspended",),
            ),
        ),
        status="blocked",
    )

    result = resolve_execution_price_policy(
        {"policy": "open", "trade_intents": [{"trade_date": "2026-01-05", "symbol": "AAA", "side": "buy"}]},
        available_prices_reader(prices_frame()),
        tradability_matrix=matrix,
    )

    assert result.status == "blocked"
    assert result.rows[0]["execution_price"] is None
    assert result.rows[0]["unfilled_reason"] == "tradability_blocked"
    assert any(item["claim"] == "real_tradable_execution" for item in result.blocked_claims)


def test_evaluate_execution_price_gate_merges_metadata_and_blocks_real_claims() -> None:
    dataset = ResearchDataset(
        status="available",
        metadata={"realism_mode": "production_strict", "allowed_claims": ["real_tradable_execution", "framework_validation"]},
        allowed_claims=["real_tradable_execution", "framework_validation"],
    )

    evaluated = evaluate_execution_price_gate(
        dataset,
        {"policy": "close_proxy", "realism_mode": "production_strict"},
        feed_result=available_prices_reader(prices_frame(vwap_status="required_missing", vwap=None)),
    )

    assert evaluated.status == "available_with_warnings"
    assert evaluated.metadata["execution_price_policy"] == "close_proxy"
    assert evaluated.metadata["execution_degradation_reason"] == "policy_explicit_close_proxy"
    assert "real_tradable_execution" not in evaluated.allowed_claims
    assert any(item["claim"] == "real_vwap_execution" for item in evaluated.blocked_claims)
    assert evaluated.metadata["execution"]["close_substitution_count"] == 0


def test_backtest_consumes_execution_frame_and_keeps_missing_prices_unfilled() -> None:
    feed = prices_frame(dates=("2026-01-05", "2026-01-06"), symbols=("AAA", "BBB"))
    feed.loc[(feed["trade_date"] == "2026-01-06") & (feed["symbol"] == "AAA"), "close"] = pd.NA

    frame_result = build_execution_price_frame(feed, ExecutionPolicyConfig(policy="close_proxy"))

    assert pd.isna(frame_result.price_frame.loc[pd.to_datetime("2026-01-06").date(), "AAA"])
    assert frame_result.metadata["missing_price_fill_count"] == 0
    assert frame_result.metadata["execution_price_policy"] == "close_proxy"

    index = [item.date() for item in pd.bdate_range("2026-01-01", periods=8)]
    close_df = pd.DataFrame({"AAA": range(10, 18), "BBB": range(20, 12, -1)}, index=index)
    full_feed = prices_frame(dates=tuple(str(item) for item in index), symbols=("AAA", "BBB"))
    result = run_backtest(
        close_df,
        BacktestConfig(lookback_days=2, rebalance_freq=2, top_fraction=0.5),
        execution_policy="close_proxy",
        execution_feed=full_feed,
    )

    assert result.metadata["execution_price_policy"] == "close_proxy"
    assert result.metadata["execution"]["vwap_or_proxy"] == "proxy"
    assert any(item["claim"] == "real_vwap_execution" for item in result.metadata["blocked_claims"])


def test_s04_forbidden_boundaries_are_static_and_no_secret_leakage(monkeypatch) -> None:
    fake_secret = "CR011_S04_FAKE_SECRET_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("CR011_S04_FAKE_SECRET", fake_secret)
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

    result = evaluate_execution_price_gate(
        ResearchDataset(status="available", metadata={"realism_mode": "production_strict"}),
        {"policy": "close_proxy", "realism_mode": "production_strict"},
        feed_result=available_prices_reader(prices_frame(vwap_status="required_missing", vwap=None)),
    )
    combined = json.dumps([result.metadata, [issue.to_dict() for issue in result.issues]], ensure_ascii=False, default=str)
    assert fake_secret not in combined
    assert result.metadata.get("network_calls", 0) == 0
    assert result.metadata.get("lake_writes", 0) == 0
    assert result.metadata.get("credential_reads", 0) == 0
    assert result.metadata.get("legacy_data_operations", 0) == 0


def prices_frame(
    *,
    dates: tuple[str, ...] = ("2026-01-05",),
    symbols: tuple[str, ...] = ("AAA",),
    include_vwap: bool = True,
    vwap_status: str = "available",
    vwap: float | None = 11.5,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date in dates:
        for offset, symbol in enumerate(symbols):
            row = {
                "trade_date": trade_date,
                "symbol": symbol,
                "open": 10.0 + offset,
                "high": 13.0 + offset,
                "low": 9.0 + offset,
                "close": 12.0 + offset,
                "volume": 1000.0,
                "amount": 12000.0,
                "vwap_status": vwap_status,
                "available_at_rule": "close_after_available_at",
                "source_interface": "prices.daily",
                "source_run_id": "run-prices",
            }
            if include_vwap:
                row["vwap"] = vwap
            rows.append(row)
    return pd.DataFrame(rows)


def available_prices_reader(frame: pd.DataFrame) -> ReaderResult:
    return ReaderResult(
        status="available",
        frame=frame,
        catalog_entry=CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            readiness_status="available",
            source="fixture",
            source_interface="prices.daily",
            latest_manifest_run_id="run-prices",
            available_at_rule="close_after_available_at",
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
