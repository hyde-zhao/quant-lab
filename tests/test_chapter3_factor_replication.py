from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from engine.chapter3_factor_replication import (
    DEFAULT_FACTOR_IDS,
    audit_chapter3_data_issues,
    chapter3_factor_definitions,
    factor_matrices_to_panel,
    independent_double_sort_returns,
    long_short_summary,
    replicate_chapter3_factors,
    single_sort_returns,
)


def _fixture_frames(days: int = 280, symbols: int = 6) -> dict[str, pd.DataFrame]:
    calendar = pd.bdate_range("2023-01-02", periods=days)
    symbol_list = [f"00000{i + 1}.SZ" for i in range(symbols)]
    price_rows: list[dict[str, object]] = []
    market_cap_rows: list[dict[str, object]] = []
    financial_rows: list[dict[str, object]] = []
    stock_rows: list[dict[str, object]] = []

    for symbol_index, symbol in enumerate(symbol_list):
        base_price = 10.0 + symbol_index
        base_market_cap = 1000.0 + symbol_index * 100.0
        list_date = calendar[0].date().isoformat()
        stock_rows.append(
            {
                "symbol": symbol,
                "list_date": list_date,
                "list_status": "L",
                "is_st": False,
                "book_equity": 400.0 + symbol_index * 20.0,
            }
        )
        for day_index, trade_date in enumerate(calendar):
            close = base_price * (1.0 + 0.001 * day_index + 0.0005 * symbol_index)
            market_cap = base_market_cap * (1.0 + 0.0008 * day_index)
            turnover = 0.6 + 0.02 * symbol_index + 0.001 * (day_index % 21)
            price_rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "open": close * 0.995,
                    "high": close * 1.010,
                    "low": close * 0.990,
                    "adjusted_close": close,
                    "close": close,
                    "volume": 10000 + day_index * 10 + symbol_index,
                    "amount": close * (10000 + day_index * 10 + symbol_index),
                    "adj_factor": 1.0,
                    "adjustment_policy": "qfq",
                    "available_at": f"{trade_date.date().isoformat()}T16:30:00",
                    "turnover_rate": turnover,
                    "limit_up": False,
                    "limit_down": False,
                    "is_suspended": False,
                }
            )
            market_cap_rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "market_cap": market_cap,
                    "turnover_rate": turnover,
                    "available_at": f"{trade_date.date().isoformat()}T16:30:00",
                }
            )
        for available_date in (calendar[0], calendar[130], calendar[260]):
            financial_rows.append(
                {
                    "symbol": symbol,
                    "available_at": available_date.date().isoformat(),
                    "report_period": (available_date - timedelta(days=30)).date().isoformat(),
                    "end_date": (available_date - timedelta(days=30)).date().isoformat(),
                    "statement_type": "initial",
                    "update_flag": "latest_pit",
                    "book_equity": 400.0 + symbol_index * 20.0,
                    "roe_ttm": 0.08 + symbol_index * 0.01,
                    "asset_growth": 0.05 + symbol_index * 0.005,
                    "total_assets": 900.0 + symbol_index * 80.0,
                }
            )

    trade_calendar = pd.DataFrame({"trade_date": [item.date().isoformat() for item in calendar], "is_open": True})
    return {
        "prices": pd.DataFrame(price_rows),
        "market_cap": pd.DataFrame(market_cap_rows),
        "financials": pd.DataFrame(financial_rows),
        "trade_calendar": trade_calendar,
        "trade_status": pd.DataFrame(
            {
                "trade_date": [calendar[0].date().isoformat()],
                "symbol": [symbol_list[0]],
                "is_suspended": [False],
                "trade_status": ["trading"],
            }
        ),
        "prices_limit": pd.DataFrame(
            {
                "trade_date": [calendar[0].date().isoformat()],
                "symbol": [symbol_list[0]],
                "limit_up": [False],
                "limit_down": [False],
            }
        ),
        "stock_basic": pd.DataFrame(stock_rows),
    }


def test_chapter3_data_issue_audit_reports_coverage_statuses() -> None:
    frames = _fixture_frames()

    audit = audit_chapter3_data_issues(frames)
    by_id = audit.set_index("issue_id")

    assert by_id.loc["C3-DATA-01", "status"] == "covered"
    assert by_id.loc["C3-FIN-01", "status"] == "covered"
    assert by_id.loc["C3-TRADE-01", "status"] == "covered"
    assert by_id.loc["C3-PREP-01", "status"] == "covered"
    assert by_id.loc["C3-TEST-01", "status"] == "covered"

    missing = audit_chapter3_data_issues({"prices": frames["prices"][["trade_date", "symbol", "close"]]})
    missing_by_id = missing.set_index("issue_id")

    assert missing_by_id.loc["C3-FIN-01", "status"] == "missing"
    assert missing_by_id.loc["C3-UNIV-01", "status"] == "missing"
    assert missing_by_id.loc["C3-DATA-01", "status"] == "partial"


def test_chapter3_factor_definitions_cover_book_factor_set() -> None:
    definitions = chapter3_factor_definitions()
    factor_ids = {definition.factor_id for definition in definitions}

    assert set(DEFAULT_FACTOR_IDS) <= factor_ids
    assert {definition.book_name for definition in definitions} >= {
        "市场因子",
        "规模因子",
        "价值因子",
        "动量因子",
        "盈利因子",
        "投资因子",
        "换手率因子",
    }


def test_replicate_chapter3_factors_builds_matrices_panel_and_sorting_results() -> None:
    frames = _fixture_frames()

    result = replicate_chapter3_factors(
        frames["prices"],
        market_cap=frames["market_cap"],
        financials=frames["financials"],
        trade_calendar=frames["trade_calendar"],
        min_period_ratio=0.5,
        min_cross_section=3,
    )

    assert set(result.raw_matrices) == set(DEFAULT_FACTOR_IDS)
    assert result.limitations == ()
    assert result.market_factor_return.notna().sum() > 0
    assert set(result.preprocessing_summary["factor_id"]) == set(DEFAULT_FACTOR_IDS)

    last_date = result.directional_matrices["size_total_market_cap"].dropna(how="all").index[-1]
    size_scores = result.directional_matrices["size_total_market_cap"].loc[last_date].sort_values(ascending=False)
    assert size_scores.index[0] == "000001.SZ"

    panel = factor_matrices_to_panel(result, source_dataset="chapter3_fixture")
    assert {"raw_value", "directional_value", "winsorized_value", "zscore_value"} <= set(panel.columns)
    assert set(panel["factor_id"].unique()) == set(DEFAULT_FACTOR_IDS)

    close = frames["prices"].pivot_table(index="trade_date", columns="symbol", values="adjusted_close", aggfunc="last")
    close.index = pd.to_datetime(close.index).date
    forward_returns = close.shift(-20) / close - 1.0
    value_groups = single_sort_returns(
        result.zscore_matrices["value_bm"],
        forward_returns,
        quantiles=3,
        min_cross_section=6,
    )
    summary = long_short_summary(value_groups, high_minus_low=True)

    assert not value_groups.empty
    assert summary["status"] == "pass"
    assert summary["observation_count"] > 0

    double_sort = independent_double_sort_returns(
        result.zscore_matrices["abnormal_turnover_21_252"],
        result.raw_matrices["size_total_market_cap"],
        forward_returns,
        groups=3,
        min_cross_section=6,
    )

    assert not double_sort.empty
    assert {"size_group", "factor_group", "mean_forward_return", "symbol_count"} <= set(double_sort.columns)


def test_replicate_chapter3_factors_reports_missing_required_inputs() -> None:
    frames = _fixture_frames()

    result = replicate_chapter3_factors(
        frames["prices"],
        trade_calendar=frames["trade_calendar"],
        factor_ids=("size_total_market_cap", "value_bm", "profitability_roe_ttm"),
        min_cross_section=3,
    )

    assert result.raw_matrices == {}
    assert any("size_total_market_cap 缺 market_cap" in item for item in result.limitations)
    assert any("value_bm 缺 book_equity" in item for item in result.limitations)
    assert any("profitability_roe_ttm 缺 roe_ttm" in item for item in result.limitations)


def test_replicate_chapter3_factors_rejects_bad_price_schema() -> None:
    with pytest.raises(ValueError, match="prices 缺少"):
        replicate_chapter3_factors(pd.DataFrame({"trade_date": ["2024-01-02"], "symbol": ["000001.SZ"]}))
