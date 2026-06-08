from __future__ import annotations

import pandas as pd

from engine.factor_calculators import compute_equity_factor_matrices, factor_matrices_to_panel
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS


def _calculator_fixture(days: int = 280, symbols: int = 6) -> dict[str, object]:
    calendar = pd.bdate_range("2023-01-02", periods=days)
    symbol_list = [f"00000{i + 1}.SZ" for i in range(symbols)]
    price_rows: list[dict[str, object]] = []
    market_cap_rows: list[dict[str, object]] = []
    financial_rows: list[dict[str, object]] = []

    for symbol_index, symbol in enumerate(symbol_list):
        base_price = 10.0 + symbol_index
        base_market_cap = 1000.0 + symbol_index * 100.0
        for day_index, trade_date in enumerate(calendar):
            close = base_price * (1.0 + 0.001 * day_index + 0.0005 * symbol_index)
            market_cap = base_market_cap * (1.0 + 0.0008 * day_index)
            turnover = 0.6 + 0.02 * symbol_index + 0.001 * (day_index % 21)
            price_rows.append(
                {
                    "trade_date": trade_date.date(),
                    "symbol": symbol,
                    "close": close,
                    "book_to_market": (400.0 + symbol_index * 20.0) / market_cap,
                    "turnover_rate": turnover,
                }
            )
            market_cap_rows.append({"trade_date": trade_date.date(), "symbol": symbol, "market_cap": market_cap})
        for available_date in (calendar[0], calendar[130], calendar[260]):
            financial_rows.append(
                {
                    "symbol": symbol,
                    "available_date": available_date.date(),
                    "book_equity": 400.0 + symbol_index * 20.0,
                    "roe_ttm": 0.08 + symbol_index * 0.01,
                    "asset_growth": 0.05 + symbol_index * 0.005,
                    "total_assets": 900.0 + symbol_index * 80.0,
                }
            )

    prices = pd.DataFrame(price_rows)
    close = prices.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last")
    market_cap = pd.DataFrame(market_cap_rows).pivot_table(index="trade_date", columns="symbol", values="market_cap", aggfunc="last")
    turnover = prices.pivot_table(index="trade_date", columns="symbol", values="turnover_rate", aggfunc="last")
    returns = close.pct_change(fill_method=None)
    financials = pd.DataFrame(financial_rows)
    financial_daily: dict[str, pd.DataFrame] = {}
    for column in ("book_equity", "roe_ttm", "asset_growth", "total_assets"):
        matrix = financials.pivot_table(index="available_date", columns="symbol", values=column, aggfunc="last")
        financial_daily[column] = matrix.reindex(index=close.index, columns=close.columns).ffill()
    return {
        "prices": prices,
        "close": close,
        "returns": returns,
        "market_cap": market_cap,
        "turnover": turnover,
        "financial_daily": financial_daily,
    }


def test_compute_equity_factor_matrices_builds_generic_factor_outputs() -> None:
    fixture = _calculator_fixture()

    result = compute_equity_factor_matrices(
        close=fixture["close"],
        returns=fixture["returns"],
        price_frame=fixture["prices"],
        market_cap_matrix=fixture["market_cap"],
        turnover_matrix=fixture["turnover"],
        financial_daily=fixture["financial_daily"],
        min_period_ratio=0.5,
        min_cross_section=3,
    )

    assert set(result.raw_matrices) == set(DEFAULT_EQUITY_CORE_FACTOR_IDS)
    assert result.limitations == ()
    assert set(result.preprocessing_summary["factor_id"]) == set(DEFAULT_EQUITY_CORE_FACTOR_IDS)
    assert result.market_factor_return.notna().sum() > 0
    assert result.directional_matrices["size_total_market_cap"].max().max() < 0

    panel = factor_matrices_to_panel(result, source_dataset="factor_calculator_fixture")
    assert set(panel["factor_id"].unique()) == set(DEFAULT_EQUITY_CORE_FACTOR_IDS)
    assert {"raw_value", "directional_value", "winsorized_value", "zscore_value"} <= set(panel.columns)


def test_compute_equity_factor_matrices_reports_missing_inputs() -> None:
    fixture = _calculator_fixture()

    result = compute_equity_factor_matrices(
        close=fixture["close"],
        returns=fixture["returns"],
        price_frame=fixture["prices"][["trade_date", "symbol", "close"]],
        factor_ids=("size_total_market_cap", "value_bm", "profitability_roe_ttm"),
        min_cross_section=3,
    )

    assert result.raw_matrices == {}
    assert any("size_total_market_cap 缺 market_cap" in item for item in result.limitations)
    assert any("value_bm 缺 book_equity" in item for item in result.limitations)
    assert any("profitability_roe_ttm 缺 roe_ttm" in item for item in result.limitations)
