import json
from pathlib import Path

import pandas as pd

from scripts.data_lake.backfill_market_data import (
    BackfillContext,
    fetch_adj_factor,
    fetch_market_cap,
    fetch_prices,
    fetch_trade_calendar,
    fetch_namechange_history,
    write_liquidity_capacity,
    write_prices_hfq,
    write_chapter3_events,
    fetch_financial_pit,
    write_financial_pit_audit,
    write_tradability_and_limit_datasets,
    write_dataset_frame,
    write_summary,
)
from market_data.contracts import CANONICAL_STOCK_BASIC_COLUMNS, DATASET_STOCK_BASIC


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

    def namechange(self, **params: object) -> pd.DataFrame:
        symbol = str(params["ts_code"])
        return pd.DataFrame(
            [
                {
                    "ts_code": symbol,
                    "name": "*ST测试",
                    "start_date": "20000104",
                    "end_date": "20000105",
                    "ann_date": "20000104",
                    "change_reason": "ST",
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


def test_cr034_derives_chapter3_constraints_and_audited_financial_pit(tmp_path: Path) -> None:
    ctx = BackfillContext(
        lake_root=tmp_path,
        run_id="run-cr034-derived",
        start="2000-01-01",
        end="2000-01-05",
        sleep_seconds=0.0,
    )
    pro = FakePro()

    open_dates = fetch_trade_calendar(pro, ctx)
    fetch_prices(pro, ctx, open_dates)
    financial = fetch_financial_pit(pro, ctx, symbols=("000001.SZ",))
    audited = write_financial_pit_audit(ctx)

    stock_basic = pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "name": "测试银行",
                "market": "主板",
                "list_status": "L",
                "list_date": "1999-01-01",
                "delist_date": "",
                "effective_date": "1999-01-01",
                "available_date": "2000-01-05",
                "available_at": "2000-01-05T00:00:00+08:00",
                "available_at_rule": "fixture",
                "pit_status": "available",
                "readiness_status": "available",
                "source": "fixture",
                "source_interface": "fixture",
                "source_run_id": ctx.run_id,
                "schema_version": "1.0",
                "lineage_raw_checksum": "sha256:fixture",
            }
        ],
        columns=CANONICAL_STOCK_BASIC_COLUMNS,
    )
    write_dataset_frame(ctx, DATASET_STOCK_BASIC, stock_basic, "part-stock-basic.parquet")

    lifecycle = stock_basic
    namechange = fetch_namechange_history(pro, ctx, symbols=("000001.SZ",))
    events = write_chapter3_events(ctx, lifecycle, namechange)
    write_tradability_and_limit_datasets(ctx, lifecycle, namechange, write_trade_status=True, write_prices_limit=True)

    trade_status = pd.read_parquet(
        tmp_path / "canonical" / "trade_status" / "1.0" / "run_id=run-cr034-derived" / "part-trade-status-derived-2000.parquet"
    )
    prices_limit = pd.read_parquet(
        tmp_path / "canonical" / "prices_limit" / "1.0" / "run_id=run-cr034-derived" / "part-prices-limit-derived-2000.parquet"
    )

    assert len(financial) == 1
    assert {"revision_as_of", "revision_sequence", "pit_policy"} <= set(audited.columns)
    assert set(events["event_type"]) >= {"list", "st_status"}
    assert trade_status["is_st"].all()
    assert trade_status["is_tradable"].all()
    second_day_limit = prices_limit.loc[prices_limit["trade_date"] == "2000-01-05"].iloc[0]
    assert second_day_limit["limit_up"] == 11.03
    assert second_day_limit["limit_down"] == 9.98
