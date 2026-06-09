import json
from pathlib import Path

import pandas as pd

from scripts.cr034_chapter3_backfill import (
    BackfillContext,
    fetch_adj_factor,
    fetch_market_cap,
    fetch_prices,
    fetch_trade_calendar,
    write_liquidity_capacity,
    write_prices_hfq,
    fetch_financial_pit,
    write_summary,
)


class FakePro:
    def trade_cal(self, **_: object) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"cal_date": "20000104", "is_open": 1, "pretrade_date": "19991230"},
                {"cal_date": "20000105", "is_open": 1, "pretrade_date": "20000104"},
            ]
        )

    def daily(self, **params: object) -> pd.DataFrame:
        day = str(params["trade_date"])
        return pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "trade_date": day,
                    "open": 10.0,
                    "high": 11.0,
                    "low": 9.5,
                    "close": 10.5,
                    "vol": 100.0,
                    "amount": 1000.0,
                }
            ]
        )

    def adj_factor(self, **params: object) -> pd.DataFrame:
        day = str(params["trade_date"])
        return pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": day, "adj_factor": 2.0}])

    def daily_basic(self, **params: object) -> pd.DataFrame:
        day = str(params["trade_date"])
        return pd.DataFrame(
            [
                {
                    "ts_code": "000001.SZ",
                    "trade_date": day,
                    "turnover_rate": 1.2,
                    "turnover_rate_f": 1.1,
                    "total_mv": 10000.0,
                    "circ_mv": 8000.0,
                    "pb": 1.5,
                }
            ]
        )

    def income(self, **params: object) -> pd.DataFrame:
        symbol = str(params["ts_code"])
        return pd.DataFrame(
            [
                {
                    "ts_code": symbol,
                    "ann_date": "20000331",
                    "end_date": "19991231",
                    "operate_profit": 100.0,
                    "n_income": 80.0,
                    "revenue": 1000.0,
                    "report_type": "1",
                    "update_flag": "0",
                }
            ]
        )

    def balancesheet(self, **params: object) -> pd.DataFrame:
        symbol = str(params["ts_code"])
        return pd.DataFrame(
            [
                {
                    "ts_code": symbol,
                    "ann_date": "20000331",
                    "end_date": "19991231",
                    "total_hldr_eqy_exc_min_int": 500.0,
                    "total_assets": 1500.0,
                    "total_liab": 1000.0,
                    "report_type": "1",
                    "update_flag": "0",
                }
            ]
        )

    def fina_indicator(self, **params: object) -> pd.DataFrame:
        symbol = str(params["ts_code"])
        return pd.DataFrame(
            [
                {
                    "ts_code": symbol,
                    "ann_date": "20000331",
                    "end_date": "19991231",
                    "roe": 16.0,
                    "grossprofit_margin": 30.0,
                    "netprofit_margin": 8.0,
                }
            ]
        )


def test_cr034_backfill_writes_candidate_without_publish(tmp_path: Path) -> None:
    ctx = BackfillContext(
        lake_root=tmp_path,
        run_id="run-cr034-test",
        start="2000-01-01",
        end="2000-01-05",
        sleep_seconds=0.0,
    )
    pro = FakePro()

    open_dates = fetch_trade_calendar(pro, ctx)
    prices = fetch_prices(pro, ctx, open_dates)
    factors = fetch_adj_factor(pro, ctx, open_dates)
    hfq = write_prices_hfq(ctx, prices, factors)
    market_cap = fetch_market_cap(pro, ctx, open_dates)
    liquidity = write_liquidity_capacity(ctx, prices, market_cap)
    financial = fetch_financial_pit(pro, ctx, symbols=("000001.SZ",))
    summary_path = write_summary(ctx)

    assert open_dates == ["2000-01-04", "2000-01-05"]
    assert len(prices) == 2
    assert len(factors) == 2
    assert len(hfq) == 2
    assert hfq["back_adjusted_close"].tolist() == [21.0, 21.0]
    assert len(market_cap) == 2
    assert len(liquidity) == 2
    assert len(financial) == 1
    assert financial["book_equity"].tolist() == [500.0]
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["catalog_current_pointer_publish"] == 0
    assert summary["qmt_operation"] == 0
    assert summary["simulation_or_live_run"] == 0
    assert (tmp_path / "canonical" / "prices_hfq" / "1.0" / "run_id=run-cr034-test" / "part-prices-hfq.parquet").exists()
    assert (tmp_path / "canonical" / "financial_pit" / "1.0" / "run_id=run-cr034-test" / "part-financial-pit.parquet").exists()
