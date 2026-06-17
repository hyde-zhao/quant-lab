from __future__ import annotations

from datetime import timedelta

import pandas as pd
import pytest

from engine.chapter3_factor_replication import (
    Chapter3ResearchPolicy,
    DEFAULT_FACTOR_IDS,
    audit_chapter3_data_issues,
    build_chapter3_return_matrix,
    canonicalize_chapter3_financials,
    chapter3_factor_definitions,
    conditional_double_sort_returns,
    fama_macbeth_regression,
    factor_matrices_to_panel,
    independent_double_sort_returns,
    long_short_summary,
    long_short_summary_from_double_sort,
    newey_west_t_stat,
    prepare_chapter3_research_data,
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


def test_canonicalize_chapter3_financials_prefers_latest_pit_record() -> None:
    financials = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "available_at": "2023-04-30",
                "report_period": "20221231",
                "record_type": "type3_original_initial",
                "book_equity": 90.0,
            },
            {
                "symbol": "000001.SZ",
                "available_at": "2023-04-30",
                "report_period": "20221231",
                "record_type": "type1_initial_latest",
                "book_equity": 100.0,
            },
            {
                "symbol": "000001.SZ",
                "available_at": "2024-04-30",
                "report_period": "20221231",
                "record_type": "type2_baseline_latest",
                "book_equity": 110.0,
            },
        ]
    )

    canonical = canonicalize_chapter3_financials(financials)

    assert len(canonical) == 2
    assert canonical.loc[canonical["available_at"] == pd.Timestamp("2023-04-30").date(), "book_equity"].iloc[0] == 100.0
    assert canonical.loc[canonical["available_at"] == pd.Timestamp("2024-04-30").date(), "book_equity"].iloc[0] == 110.0


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


def test_replicate_chapter3_factors_derives_book_profitability_and_annual_investment() -> None:
    calendar = pd.bdate_range("2024-04-29", periods=5)
    symbols = ("000001.SZ", "000002.SZ", "000003.SZ")
    price_rows: list[dict[str, object]] = []
    market_rows: list[dict[str, object]] = []
    financial_rows: list[dict[str, object]] = []
    for symbol_index, symbol in enumerate(symbols):
        for day_index, trade_date in enumerate(calendar):
            price_rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "hfq_close": 10.0 + symbol_index + day_index * 0.1,
                    "close": 10.0 + symbol_index + day_index * 0.1,
                    "turnover_rate": 0.5,
                }
            )
            market_rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "market_cap": 1000.0 + symbol_index * 100.0,
                    "turnover_rate": 0.5,
                }
            )
        equity_values = (80.0, 90.0, 100.0, 110.0)
        report_periods = ("20230630", "20230930", "20231231", "20240331")
        available_dates = ("2023-08-31", "2023-10-31", "2024-04-30", "2024-04-30")
        for report_period, available_at, equity in zip(report_periods, available_dates, equity_values):
            financial_rows.append(
                {
                    "symbol": symbol,
                    "available_at": available_at,
                    "report_period": report_period,
                    "book_equity": equity + symbol_index,
                    "operating_profit_ttm": 22.0 + symbol_index,
                    "total_assets": 1210.0 + symbol_index * 10.0 if report_period == "20231231" else 900.0,
                }
            )
        financial_rows.append(
            {
                "symbol": symbol,
                "available_at": "2023-04-30",
                "report_period": "20221231",
                "book_equity": 70.0 + symbol_index,
                "operating_profit_ttm": 18.0 + symbol_index,
                "total_assets": 1000.0 + symbol_index * 10.0,
            }
        )

    result = replicate_chapter3_factors(
        pd.DataFrame(price_rows),
        market_cap=pd.DataFrame(market_rows),
        financials=pd.DataFrame(financial_rows),
        trade_calendar=pd.DataFrame({"trade_date": [item.date().isoformat() for item in calendar], "is_open": True}),
        factor_ids=("profitability_roe_ttm", "investment_asset_growth"),
        min_cross_section=3,
    )

    first_date = calendar[1].date()
    assert result.raw_matrices["profitability_roe_ttm"].loc[first_date, "000001.SZ"] == pytest.approx(22.0 / 95.0)
    assert result.raw_matrices["investment_asset_growth"].loc[first_date, "000001.SZ"] == pytest.approx(0.21)


def test_replicate_chapter3_factors_rejects_bad_price_schema() -> None:
    with pytest.raises(ValueError, match="prices 缺少"):
        replicate_chapter3_factors(pd.DataFrame({"trade_date": ["2024-01-02"], "symbol": ["000001.SZ"]}))


def test_prepare_chapter3_research_data_applies_book_data_policies() -> None:
    dates = pd.bdate_range("2023-01-02", periods=4)
    symbols = ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ", "688001.SH", "000005.SZ"]
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        for day_index, trade_date in enumerate(dates):
            price = 10.0 + day_index
            rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "hfq_close": 20.0 if symbol == "000001.SZ" and day_index == 1 else price,
                    "close": 20.0 if symbol == "000001.SZ" and day_index == 1 else price,
                    "open": price,
                    "high": price,
                    "low": price,
                    "is_suspended": symbol == "000002.SZ" and day_index == 1,
                    "limit_up": symbol == "000003.SZ" and day_index == 2,
                    "limit_down": False,
                }
            )
    stock_basic = pd.DataFrame(
        [
            {"symbol": "000001.SZ", "list_date": "2020-01-01", "list_status": "L", "book_equity": 10.0},
            {"symbol": "000002.SZ", "list_date": "2020-01-01", "list_status": "L", "is_st": True, "book_equity": 10.0},
            {"symbol": "000003.SZ", "list_date": "2020-01-01", "list_status": "L", "book_equity": 10.0},
            {"symbol": "000004.SZ", "list_date": "2023-01-01", "list_status": "L", "book_equity": 10.0},
            {"symbol": "688001.SH", "list_date": "2020-01-01", "list_status": "L", "book_equity": 10.0},
            {"symbol": "000005.SZ", "list_date": "2020-01-01", "list_status": "D", "book_equity": -1.0},
        ]
    )

    prepared = prepare_chapter3_research_data(
        pd.DataFrame(rows),
        stock_basic=stock_basic,
        trade_calendar=pd.DataFrame({"trade_date": [item.date().isoformat() for item in dates], "is_open": True}),
        research_policy=Chapter3ResearchPolicy(new_stock_min_days=365),
    )

    assert prepared.selected_price_column == "hfq_close"
    assert prepared.returns.loc[dates[1].date(), "000001.SZ"] == pytest.approx(0.10)
    assert not prepared.universe_mask["000002.SZ"].any()
    assert not prepared.universe_mask["688001.SH"].any()
    assert not prepared.universe_mask["000004.SZ"].any()
    assert not prepared.universe_mask["000005.SZ"].any()
    assert not prepared.tradable_mask.loc[dates[1].date(), "000002.SZ"]
    assert not prepared.tradable_mask.loc[dates[2].date(), "000003.SZ"]
    assert prepared.rebalance_dates == (dates[-1].date(),)


def test_replicate_chapter3_factors_applies_universe_and_tradability_masks() -> None:
    frames = _fixture_frames(days=280, symbols=6)
    stock_basic = frames["stock_basic"].copy()
    stock_basic["list_date"] = "2020-01-01"
    stock_basic.loc[stock_basic["symbol"] == "000002.SZ", "is_st"] = True
    prices = frames["prices"].copy()
    blocked_date = pd.to_datetime(prices["trade_date"]).dt.date.max().isoformat()
    prices.loc[(prices["symbol"] == "000003.SZ") & (prices["trade_date"] == blocked_date), ["open", "high", "low", "close"]] = 10.0
    prices.loc[(prices["symbol"] == "000003.SZ") & (prices["trade_date"] == blocked_date), "limit_up"] = True

    result = replicate_chapter3_factors(
        prices,
        market_cap=frames["market_cap"],
        financials=frames["financials"],
        stock_basic=stock_basic,
        min_period_ratio=0.5,
        min_cross_section=3,
        research_policy=Chapter3ResearchPolicy(new_stock_min_days=0),
    )

    assert result.raw_matrices["size_total_market_cap"]["000002.SZ"].isna().all()
    assert pd.isna(result.raw_matrices["size_total_market_cap"].loc[pd.Timestamp(blocked_date).date(), "000003.SZ"])


def test_weighted_sort_double_sort_summary_and_newey_west_are_available() -> None:
    frames = _fixture_frames(days=280, symbols=6)
    result = replicate_chapter3_factors(
        frames["prices"],
        market_cap=frames["market_cap"],
        financials=frames["financials"],
        trade_calendar=frames["trade_calendar"],
        min_period_ratio=0.5,
        min_cross_section=3,
    )
    close = frames["prices"].pivot_table(index="trade_date", columns="symbol", values="adjusted_close", aggfunc="last")
    close.index = pd.to_datetime(close.index).date
    forward_returns = close.shift(-20) / close - 1.0
    weights = frames["market_cap"].pivot_table(index="trade_date", columns="symbol", values="market_cap", aggfunc="last")
    weights.index = pd.to_datetime(weights.index).date

    value_groups = single_sort_returns(
        result.zscore_matrices["value_bm"],
        forward_returns,
        weights=weights,
        weight_method="value",
        quantiles=3,
        min_cross_section=6,
    )
    summary = long_short_summary(value_groups, t_stat_method="newey_west")
    double_sort = independent_double_sort_returns(
        result.zscore_matrices["abnormal_turnover_21_252"],
        result.raw_matrices["size_total_market_cap"],
        forward_returns,
        weights=weights,
        weight_method="market_cap",
        groups=3,
        min_cross_section=6,
    )
    double_summary = long_short_summary_from_double_sort(double_sort)

    assert set(value_groups["weight_method"]) == {"value"}
    assert summary["t_stat_method"] == "newey_west"
    assert summary["observation_count"] > 0
    assert set(double_sort["weight_method"]) == {"market_cap"}
    assert double_summary["status"] == "pass"
    assert newey_west_t_stat(pd.Series([0.01, 0.02, 0.00, 0.03])) is not None


def test_conditional_double_sort_and_fama_macbeth_regression() -> None:
    frames = _fixture_frames(days=280, symbols=6)
    result = replicate_chapter3_factors(
        frames["prices"],
        market_cap=frames["market_cap"],
        financials=frames["financials"],
        trade_calendar=frames["trade_calendar"],
        min_period_ratio=0.5,
        min_cross_section=3,
    )
    close = frames["prices"].pivot_table(index="trade_date", columns="symbol", values="adjusted_close", aggfunc="last")
    close.index = pd.to_datetime(close.index).date
    forward_returns = close.shift(-20) / close - 1.0
    conditional = conditional_double_sort_returns(
        result.raw_matrices["profitability_roe_ttm"],
        result.zscore_matrices["investment_asset_growth"],
        forward_returns,
        groups=2,
        min_cross_section=6,
    )
    fmb = fama_macbeth_regression(
        forward_returns,
        {
            "value_bm": result.zscore_matrices["value_bm"],
            "profitability_roe_ttm": result.zscore_matrices["profitability_roe_ttm"],
        },
        min_cross_section=6,
    )

    assert not conditional.empty
    assert {"conditioning_group", "factor_group", "mean_forward_return"} <= set(conditional.columns)
    assert set(fmb["coefficient"]) == {"intercept", "value_bm", "profitability_roe_ttm"}
    assert fmb["observation_count"].min() > 0
