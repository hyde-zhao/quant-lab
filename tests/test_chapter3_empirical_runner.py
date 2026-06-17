from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_chapter3_empirical import (
    assert_full_mode_window_allowed,
    chapter3_financial_run_ids,
    chapter3_price_run_ids,
    chapter3_prices_limit_run_ids,
    chapter3_trade_status_run_ids,
    memory_budget_summary,
    run_empirical_from_frames,
)


def _fixture_frames(days: int = 320, symbols: int = 40) -> dict[str, pd.DataFrame]:
    calendar = pd.bdate_range("2000-01-04", periods=days)
    symbol_list = [f"{index + 1:06d}.SZ" for index in range(symbols)]
    price_rows: list[dict[str, object]] = []
    market_rows: list[dict[str, object]] = []
    financial_rows: list[dict[str, object]] = []
    stock_rows: list[dict[str, object]] = []
    trade_status_rows: list[dict[str, object]] = []
    limit_rows: list[dict[str, object]] = []

    for symbol_index, symbol in enumerate(symbol_list):
        stock_rows.append(
            {
                "symbol": symbol,
                "list_status": "L",
                "list_date": "1999-01-01",
                "delist_date": "",
                "market": "主板",
            }
        )
        base_price = 10.0 + symbol_index * 0.1
        base_cap = 1000.0 + symbol_index * 20.0
        for day_index, trade_date in enumerate(calendar):
            day = trade_date.date().isoformat()
            close = base_price * (1.0 + day_index * 0.001 + symbol_index * 0.0002)
            price_rows.append(
                {
                    "trade_date": day,
                    "symbol": symbol,
                    "open": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "back_adjusted_close": close,
                    "volume": 10000.0 + day_index,
                    "amount": close * (10000.0 + day_index),
                }
            )
            market_rows.append(
                {
                    "trade_date": day,
                    "symbol": symbol,
                    "market_cap": base_cap * (1.0 + day_index * 0.0005),
                    "turnover_rate": 0.5 + symbol_index * 0.01 + (day_index % 21) * 0.001,
                }
            )
            trade_status_rows.append(
                {
                    "trade_date": day,
                    "symbol": symbol,
                    "is_tradable": True,
                    "is_suspended": False,
                    "is_st": False,
                    "status_reason": "trading",
                }
            )
            limit_rows.append({"trade_date": day, "symbol": symbol, "limit_up": close * 1.1, "limit_down": close * 0.9})
        for offset in (30, 150, 270):
            available = calendar[offset]
            financial_rows.append(
                {
                    "symbol": symbol,
                    "available_at": available.date().isoformat(),
                    "ann_date": available.date().isoformat(),
                    "report_period": (available - timedelta(days=30)).date().isoformat(),
                    "update_flag": "0",
                    "revision_as_of": available.date().isoformat(),
                    "revision_sequence": 1,
                    "pit_policy": "fixture",
                    "book_equity": 400.0 + symbol_index * 10.0,
                    "roe_ttm": 0.08 + symbol_index * 0.001,
                    "total_assets": 900.0 + symbol_index * 30.0 + offset,
                    "asset_growth": 0.04 + symbol_index * 0.0005,
                }
            )

    return {
        "prices": pd.DataFrame(price_rows),
        "market_cap": pd.DataFrame(market_rows),
        "financials": pd.DataFrame(financial_rows),
        "stock_basic": pd.DataFrame(stock_rows),
        "trade_status": pd.DataFrame(trade_status_rows),
        "prices_limit": pd.DataFrame(limit_rows),
        "trade_calendar": pd.DataFrame({"trade_date": [item.date().isoformat() for item in calendar], "is_open": True}),
    }


def test_run_chapter3_empirical_from_frames_writes_panel_and_report(tmp_path: Path) -> None:
    result = run_empirical_from_frames(
        _fixture_frames(),
        run_id="run-test-chapter3-empirical",
        start="2000-01-01",
        end="2001-12-31",
        output_root=tmp_path / "process",
        panel_root=tmp_path / "reports",
        min_cross_section=10,
        min_period_ratio=0.5,
    )

    assert result.status == "PASS"
    assert result.monthly_panel_rows > 0
    assert result.label_rows > 0
    assert len(result.factor_summaries) == 7
    assert result.artifacts.factor_panel_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.artifacts.portfolio_plan_path.exists()
    assert all("long_short_t_stat" in item for item in result.factor_summaries)
    report_text = result.artifacts.report_md_path.read_text(encoding="utf-8")
    assert "| factor_id | status | observations | long_short_return | long_short_t_stat |" in report_text
    assert result.memory_budget["max_memory_gb"] == 16.0
    assert result.memory_budget["status"] == "pass"


def test_full_mode_rejects_large_window_without_explicit_override() -> None:
    with pytest.raises(RuntimeError, match="full 模式只允许两年以内调试窗口"):
        assert_full_mode_window_allowed("2000-01-01", "2019-12-31", allow_large=False)

    assert_full_mode_window_allowed("2000-01-01", "2001-12-31", allow_large=False)
    assert_full_mode_window_allowed("2000-01-01", "2019-12-31", allow_large=True)


def test_memory_budget_summary_reports_observed_rss() -> None:
    summary = memory_budget_summary(16.0)

    assert summary["max_memory_gb"] == 16.0
    assert summary["max_rss_bytes_observed"] > 0
    assert summary["budget_bytes"] == 16 * 1024 * 1024 * 1024
    assert summary["status"] == "pass"


def test_chapter3_run_id_selection_covers_2020_2026_ytd() -> None:
    price_run_ids = chapter3_price_run_ids(2020, 2026)
    assert "run-cr014-s14-prices-adj-factor-2020*" in price_run_ids
    assert "run-cr014-s14-prices-adj-factor-2025*" in price_run_ids
    assert "run-cr014-s11-full-a-2026-ytd-date-batch-143508" in price_run_ids

    assert chapter3_financial_run_ids(2020, 2026) == ("run-cr034-financial-pit-2020-2026*ytd*audited",)
    assert "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529" in chapter3_trade_status_run_ids(2020, 2026)
    assert "run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529" in chapter3_prices_limit_run_ids(2020, 2026)
