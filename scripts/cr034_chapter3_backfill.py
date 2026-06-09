"""CR-034 第三章真实数据补齐脚本。

该脚本只写 run-scoped canonical candidate 和 quality summary，不更新 catalog current
pointer，不触发 QMT / simulation / live。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from market_data.contracts import (
    CR005_CANONICAL_PRICES_COLUMNS,
    CANONICAL_ADJ_FACTOR_COLUMNS,
    CANONICAL_TRADE_CALENDAR_COLUMNS,
    DATASET_ADJ_FACTOR,
    DATASET_PRICES,
    DATASET_TRADE_CALENDAR,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SCHEMA_VERSION,
    SOURCE_TUSHARE,
)
from market_data.lake_layout import LakeLayout, ensure_parent_dirs_for_write


DATASET_PRICES_HFQ = "prices_hfq"
DATASET_MARKET_CAP = "market_cap"
DATASET_LIQUIDITY_CAPACITY = "liquidity_capacity"
DATASET_FINANCIAL_PIT = "financial_pit"
INTERFACE_DAILY_BASIC = "daily_basic.daily"
INTERFACE_FINANCIAL_PIT = "income+balancesheet+fina_indicator"

CANONICAL_PRICES_HFQ_COLUMNS = (
    "trade_date",
    "symbol",
    "hfq_open",
    "hfq_high",
    "hfq_low",
    "hfq_close",
    "back_adjusted_open",
    "back_adjusted_high",
    "back_adjusted_low",
    "back_adjusted_close",
    "raw_open",
    "raw_high",
    "raw_low",
    "raw_close",
    "adj_factor",
    "research_adjustment_policy",
    "base_trade_date",
    "factor_base_date_policy",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "available_at",
    "available_at_rule",
    "lineage_raw_checksum",
)

CANONICAL_MARKET_CAP_COLUMNS = (
    "trade_date",
    "symbol",
    "market_cap",
    "float_market_cap",
    "turnover_rate",
    "turnover_rate_f",
    "volume_ratio",
    "pe",
    "pe_ttm",
    "pb",
    "ps",
    "ps_ttm",
    "dv_ratio",
    "dv_ttm",
    "total_share",
    "float_share",
    "free_share",
    "market_cap_unit",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_LIQUIDITY_CAPACITY_COLUMNS = (
    "trade_date",
    "symbol",
    "volume",
    "amount",
    "amount_unit",
    "adv20_amount",
    "adv20_volume",
    "turnover_rate",
    "turnover_rate_f",
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
)

CANONICAL_FINANCIAL_PIT_COLUMNS = (
    "symbol",
    "report_period",
    "ann_date",
    "available_at",
    "available_at_rule",
    "book_equity",
    "total_assets",
    "total_liabilities",
    "operating_profit",
    "net_profit",
    "revenue",
    "roe",
    "roe_ttm",
    "gross_profit_margin",
    "net_profit_margin",
    "statement_type",
    "report_type",
    "update_flag",
    "source",
    "source_interface",
    "source_run_id",
    "schema_version",
    "lineage_raw_checksum",
    "payload",
)


@dataclass(slots=True)
class DatasetSummary:
    rows: int = 0
    paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BackfillContext:
    lake_root: Path
    run_id: str
    start: str
    end: str
    sleep_seconds: float
    dry_run: bool = False
    network_calls: int = 0
    summaries: dict[str, DatasetSummary] = field(default_factory=dict)

    @property
    def layout(self) -> LakeLayout:
        return LakeLayout(self.lake_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CR-034 第三章数据补齐")
    parser.add_argument("--lake-root", default=os.environ.get("MARKET_DATA_LAKE_ROOT", ""))
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument("--end", default="2014-12-31")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--sleep-seconds", type=float, default=0.12)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--datasets",
        default="trade_calendar,prices,adj_factor,prices_hfq,market_cap,liquidity",
        help="逗号分隔：trade_calendar,prices,adj_factor,prices_hfq,market_cap,liquidity,financial_pit",
    )
    parser.add_argument("--symbols", default="", help="财务 PIT 可选 symbol CSV；缺省时读取 Tushare stock_basic L/D/P")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.lake_root:
        raise SystemExit("缺少 --lake-root 或 MARKET_DATA_LAKE_ROOT")
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("缺少 TUSHARE_TOKEN")
    import tushare as ts

    run_id = args.run_id or f"run-cr034-chapter3-backfill-{compact_day(args.start)}-{compact_day(args.end)}-{datetime.now().strftime('%H%M%S')}"
    ctx = BackfillContext(
        lake_root=Path(args.lake_root),
        run_id=run_id,
        start=iso_day(args.start),
        end=iso_day(args.end),
        sleep_seconds=args.sleep_seconds,
        dry_run=bool(args.dry_run),
    )
    pro = ts.pro_api(token)
    selected = {item.strip() for item in str(args.datasets).split(",") if item.strip()}
    open_dates = fetch_trade_calendar(pro, ctx) if "trade_calendar" in selected else existing_open_dates(ctx)
    price_frame = pd.DataFrame()
    adj_frame = pd.DataFrame()
    if {"prices", "prices_hfq", "liquidity"} & selected:
        price_frame = fetch_prices(pro, ctx, open_dates)
    if {"adj_factor", "prices_hfq"} & selected:
        adj_frame = fetch_adj_factor(pro, ctx, open_dates)
    if "prices_hfq" in selected:
        write_prices_hfq(ctx, price_frame, adj_frame)
    market_cap = pd.DataFrame()
    if {"market_cap", "liquidity"} & selected:
        market_cap = fetch_market_cap(pro, ctx, open_dates)
    if "liquidity" in selected:
        write_liquidity_capacity(ctx, price_frame, market_cap)
    if "financial_pit" in selected:
        symbols = [item.strip().upper() for item in str(args.symbols).split(",") if item.strip()]
        fetch_financial_pit(pro, ctx, symbols=symbols)
    summary_path = write_summary(ctx)
    print(
        json.dumps(
            {
                "ok": True,
                "run_id": ctx.run_id,
                "start": ctx.start,
                "end": ctx.end,
                "dry_run": ctx.dry_run,
                "network_calls": ctx.network_calls,
                "summary_path": str(summary_path),
                "catalog_current_pointer_publish": 0,
                "qmt_operation": 0,
                "simulation_or_live_run": 0,
                "datasets": {key: value.rows for key, value in sorted(ctx.summaries.items())},
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def fetch_trade_calendar(pro: Any, ctx: BackfillContext) -> list[str]:
    rows = fetch_records(
        pro,
        ctx,
        "trade_cal",
        exchange="SSE",
        start_date=compact_day(ctx.start),
        end_date=compact_day(ctx.end),
    )
    output_rows = []
    open_dates: list[str] = []
    checksum = checksum_text(f"{ctx.run_id}:trade_calendar:{len(rows)}")
    for row in rows:
        day = iso_day(row.get("cal_date"))
        is_open = str(row.get("is_open")) == "1"
        if is_open:
            open_dates.append(day)
        output_rows.append(
            {
                "trade_date": day,
                "exchange": "SSE",
                "is_open": is_open,
                "pretrade_date": iso_day(row.get("pretrade_date")) if row.get("pretrade_date") else None,
                "source": SOURCE_TUSHARE,
                "source_interface": INTERFACE_TRADE_CALENDAR_DAILY,
                "source_run_id": ctx.run_id,
                "available_at": timestamp(day, "00:00:00"),
                "available_at_rule": "tushare_trade_cal_static",
                "schema_version": SCHEMA_VERSION,
                "lineage_raw_checksum": checksum,
            }
        )
    frame = pd.DataFrame(output_rows, columns=CANONICAL_TRADE_CALENDAR_COLUMNS)
    write_dataset_frame(ctx, DATASET_TRADE_CALENDAR, frame, "part-trade-calendar.parquet")
    return sorted(open_dates)


def existing_open_dates(ctx: BackfillContext) -> list[str]:
    root = ctx.layout.canonical_dataset_root(DATASET_TRADE_CALENDAR, SCHEMA_VERSION)
    frames = []
    for path in sorted(root.glob("run_id=*/*.parquet")):
        try:
            frame = pd.read_parquet(path, columns=["trade_date", "is_open"])
        except Exception:
            continue
        frame["trade_date"] = frame["trade_date"].astype(str)
        frame = frame[(frame["trade_date"] >= ctx.start) & (frame["trade_date"] <= ctx.end) & (frame["is_open"].astype(bool))]
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return []
    return sorted(pd.concat(frames, ignore_index=True)["trade_date"].drop_duplicates().tolist())


def fetch_prices(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for day in open_dates:
        raw = fetch_records(pro, ctx, "daily", trade_date=compact_day(day))
        checksum = checksum_text(f"{ctx.run_id}:prices:{day}:{len(raw)}")
        for row in raw:
            symbol = symbol_value(row)
            close = float_or_none(row.get("close"))
            if not symbol or close is None:
                continue
            open_price = float_or_default(row.get("open"), close)
            high = float_or_default(row.get("high"), close)
            low = float_or_default(row.get("low"), close)
            rows.append(
                {
                    "trade_date": iso_day(row.get("trade_date") or day),
                    "symbol": symbol,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": float_or_none(row.get("vol")),
                    "amount": float_or_none(row.get("amount")),
                    "adj_factor": 1.0,
                    "adjusted_open": open_price,
                    "adjusted_high": high,
                    "adjusted_low": low,
                    "adjusted_close": close,
                    "adjustment_policy": "raw",
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_PRICES_DAILY,
                    "source_run_id": ctx.run_id,
                    "schema_version": SCHEMA_VERSION,
                    "available_at": timestamp(day, "16:00:00"),
                    "available_at_rule": "tushare_daily_16:00",
                    "lineage_raw_checksum": checksum,
                }
            )
    frame = pd.DataFrame(rows, columns=CR005_CANONICAL_PRICES_COLUMNS).drop_duplicates(["trade_date", "symbol"])
    frame = frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_PRICES, frame, "part-prices.parquet")
    return frame


def fetch_adj_factor(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for day in open_dates:
        raw = fetch_records(pro, ctx, "adj_factor", trade_date=compact_day(day))
        checksum = checksum_text(f"{ctx.run_id}:adj_factor:{day}:{len(raw)}")
        for row in raw:
            symbol = symbol_value(row)
            factor = float_or_none(row.get("adj_factor"))
            if not symbol or factor is None:
                continue
            rows.append(
                {
                    "trade_date": iso_day(row.get("trade_date") or day),
                    "symbol": symbol,
                    "adj_factor": factor,
                    "adjustment_policy": "hfq_factor",
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_PRICES_ADJ_FACTOR,
                    "source_run_id": ctx.run_id,
                    "available_at": timestamp(day, "16:00:00"),
                    "available_at_rule": "tushare_adj_factor_16:00",
                    "schema_version": SCHEMA_VERSION,
                    "lineage_raw_checksum": checksum,
                }
            )
    frame = pd.DataFrame(rows, columns=CANONICAL_ADJ_FACTOR_COLUMNS).drop_duplicates(["trade_date", "symbol"])
    frame = frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_ADJ_FACTOR, frame, "part-adj-factor.parquet")
    return frame


def write_prices_hfq(ctx: BackfillContext, prices: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    if prices.empty or factors.empty:
        frame = pd.DataFrame(columns=CANONICAL_PRICES_HFQ_COLUMNS)
        write_dataset_frame(ctx, DATASET_PRICES_HFQ, frame, "part-prices-hfq.parquet")
        return frame
    merged = prices.merge(
        factors[["trade_date", "symbol", "adj_factor"]],
        on=["trade_date", "symbol"],
        how="inner",
        suffixes=("", "_factor"),
    )
    merged["lineage_raw_checksum"] = checksum_text(f"{ctx.run_id}:prices_hfq:{len(merged)}")
    frame = pd.DataFrame(
        {
            "trade_date": merged["trade_date"],
            "symbol": merged["symbol"],
            "hfq_open": merged["open"] * merged["adj_factor_factor"],
            "hfq_high": merged["high"] * merged["adj_factor_factor"],
            "hfq_low": merged["low"] * merged["adj_factor_factor"],
            "hfq_close": merged["close"] * merged["adj_factor_factor"],
            "back_adjusted_open": merged["open"] * merged["adj_factor_factor"],
            "back_adjusted_high": merged["high"] * merged["adj_factor_factor"],
            "back_adjusted_low": merged["low"] * merged["adj_factor_factor"],
            "back_adjusted_close": merged["close"] * merged["adj_factor_factor"],
            "raw_open": merged["open"],
            "raw_high": merged["high"],
            "raw_low": merged["low"],
            "raw_close": merged["close"],
            "adj_factor": merged["adj_factor_factor"],
            "research_adjustment_policy": "hfq",
            "base_trade_date": "provider_adj_factor_base",
            "factor_base_date_policy": "tushare_hfq_close_equals_raw_close_times_adj_factor",
            "source": SOURCE_TUSHARE,
            "source_interface": "prices.daily+prices.adj_factor",
            "source_run_id": ctx.run_id,
            "schema_version": SCHEMA_VERSION,
            "available_at": merged["trade_date"].map(lambda value: timestamp(value, "16:00:00")),
            "available_at_rule": "tushare_daily_adj_factor_16:00",
            "lineage_raw_checksum": merged["lineage_raw_checksum"],
        },
        columns=CANONICAL_PRICES_HFQ_COLUMNS,
    ).drop_duplicates(["trade_date", "symbol"])
    frame = frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_PRICES_HFQ, frame, "part-prices-hfq.parquet")
    return frame


def fetch_market_cap(pro: Any, ctx: BackfillContext, open_dates: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    fields = ",".join(
        [
            "ts_code",
            "trade_date",
            "turnover_rate",
            "turnover_rate_f",
            "volume_ratio",
            "pe",
            "pe_ttm",
            "pb",
            "ps",
            "ps_ttm",
            "dv_ratio",
            "dv_ttm",
            "total_share",
            "float_share",
            "free_share",
            "total_mv",
            "circ_mv",
        ]
    )
    for day in open_dates:
        raw = fetch_records(pro, ctx, "daily_basic", trade_date=compact_day(day), fields=fields)
        checksum = checksum_text(f"{ctx.run_id}:daily_basic:{day}:{len(raw)}")
        for row in raw:
            symbol = symbol_value(row)
            if not symbol:
                continue
            rows.append(
                {
                    "trade_date": iso_day(row.get("trade_date") or day),
                    "symbol": symbol,
                    "market_cap": float_or_none(row.get("total_mv")),
                    "float_market_cap": float_or_none(row.get("circ_mv")),
                    "turnover_rate": float_or_none(row.get("turnover_rate")),
                    "turnover_rate_f": float_or_none(row.get("turnover_rate_f")),
                    "volume_ratio": float_or_none(row.get("volume_ratio")),
                    "pe": float_or_none(row.get("pe")),
                    "pe_ttm": float_or_none(row.get("pe_ttm")),
                    "pb": float_or_none(row.get("pb")),
                    "ps": float_or_none(row.get("ps")),
                    "ps_ttm": float_or_none(row.get("ps_ttm")),
                    "dv_ratio": float_or_none(row.get("dv_ratio")),
                    "dv_ttm": float_or_none(row.get("dv_ttm")),
                    "total_share": float_or_none(row.get("total_share")),
                    "float_share": float_or_none(row.get("float_share")),
                    "free_share": float_or_none(row.get("free_share")),
                    "market_cap_unit": "ten_thousand_cny",
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_DAILY_BASIC,
                    "source_run_id": ctx.run_id,
                    "available_at": timestamp(day, "16:00:00"),
                    "available_at_rule": "tushare_daily_basic_16:00",
                    "schema_version": SCHEMA_VERSION,
                    "lineage_raw_checksum": checksum,
                }
            )
    frame = pd.DataFrame(rows, columns=CANONICAL_MARKET_CAP_COLUMNS).drop_duplicates(["trade_date", "symbol"])
    frame = frame.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_MARKET_CAP, frame, "part-market-cap.parquet")
    return frame


def write_liquidity_capacity(ctx: BackfillContext, prices: pd.DataFrame, market_cap: pd.DataFrame) -> pd.DataFrame:
    if prices.empty:
        frame = pd.DataFrame(columns=CANONICAL_LIQUIDITY_CAPACITY_COLUMNS)
        write_dataset_frame(ctx, DATASET_LIQUIDITY_CAPACITY, frame, "part-liquidity-capacity.parquet")
        return frame
    cap = market_cap[["trade_date", "symbol", "turnover_rate", "turnover_rate_f"]] if not market_cap.empty else pd.DataFrame(columns=["trade_date", "symbol", "turnover_rate", "turnover_rate_f"])
    frame = prices[["trade_date", "symbol", "volume", "amount"]].merge(cap, on=["trade_date", "symbol"], how="left")
    frame = frame.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    frame["adv20_amount"] = frame.groupby("symbol")["amount"].transform(lambda series: series.rolling(20, min_periods=5).mean())
    frame["adv20_volume"] = frame.groupby("symbol")["volume"].transform(lambda series: series.rolling(20, min_periods=5).mean())
    frame["amount_unit"] = "thousand_cny"
    frame["source"] = SOURCE_TUSHARE
    frame["source_interface"] = "prices.daily+daily_basic.daily"
    frame["source_run_id"] = ctx.run_id
    frame["available_at"] = frame["trade_date"].map(lambda value: timestamp(value, "16:00:00"))
    frame["available_at_rule"] = "daily_close_fact"
    frame["schema_version"] = SCHEMA_VERSION
    frame["lineage_raw_checksum"] = checksum_text(f"{ctx.run_id}:liquidity:{len(frame)}")
    frame = frame[list(CANONICAL_LIQUIDITY_CAPACITY_COLUMNS)]
    write_dataset_frame(ctx, DATASET_LIQUIDITY_CAPACITY, frame, "part-liquidity-capacity.parquet")
    return frame


def fetch_financial_pit(pro: Any, ctx: BackfillContext, *, symbols: Sequence[str] = ()) -> pd.DataFrame:
    target_symbols = list(symbols) if symbols else fetch_stock_symbols(pro, ctx)
    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(target_symbols, start=1):
        if index == 1 or index % 200 == 0:
            print(f"[financial_pit] {index}/{len(target_symbols)} {symbol}", flush=True)
        income_rows = fetch_records(
            pro,
            ctx,
            "income",
            ts_code=symbol,
            start_date=compact_day(ctx.start),
            end_date=compact_day(ctx.end),
        )
        balance_rows = fetch_records(
            pro,
            ctx,
            "balancesheet",
            ts_code=symbol,
            start_date=compact_day(ctx.start),
            end_date=compact_day(ctx.end),
        )
        indicator_rows = fetch_records(
            pro,
            ctx,
            "fina_indicator",
            ts_code=symbol,
            start_date=compact_day(ctx.start),
            end_date=compact_day(ctx.end),
        )
        balance_lookup = {financial_key(row): row for row in balance_rows if financial_key(row)}
        indicator_lookup = {financial_key(row): row for row in indicator_rows if financial_key(row)}
        keys = sorted({financial_key(row) for row in [*income_rows, *balance_rows, *indicator_rows] if financial_key(row)})
        for key in keys:
            income = next((row for row in income_rows if financial_key(row) == key), {})
            balance = balance_lookup.get(key, {})
            indicator = indicator_lookup.get(key, {})
            merged_payload = {
                "income": compact_payload(income),
                "balancesheet": compact_payload(balance),
                "fina_indicator": compact_payload(indicator),
            }
            ann_date = first_value(income, balance, indicator, names=("ann_date", "f_ann_date"))
            report_period = first_value(income, balance, indicator, names=("end_date", "report_period"))
            if not report_period:
                continue
            available_day = iso_day(ann_date or report_period)
            checksum = checksum_text(f"{ctx.run_id}:financial_pit:{symbol}:{key}")
            rows.append(
                {
                    "symbol": symbol,
                    "report_period": iso_day(report_period),
                    "ann_date": iso_day(ann_date) if ann_date else "",
                    "available_at": timestamp(available_day, "16:00:00"),
                    "available_at_rule": "tushare_ann_date_16:00_or_report_period_fallback",
                    "book_equity": first_float(balance, "total_hldr_eqy_exc_min_int", "total_hldr_eqy_inc_min_int", "total_hldr_eqy_inc_min_int"),
                    "total_assets": first_float(balance, "total_assets"),
                    "total_liabilities": first_float(balance, "total_liab"),
                    "operating_profit": first_float(income, "operate_profit", "op_profit"),
                    "net_profit": first_float(income, "n_income", "n_income_attr_p", "net_profit"),
                    "revenue": first_float(income, "revenue", "total_revenue"),
                    "roe": first_float(indicator, "roe", "roe_dt", "roe_waa"),
                    "roe_ttm": first_float(indicator, "roe_ttm", "roe_dt", "roe"),
                    "gross_profit_margin": first_float(indicator, "grossprofit_margin"),
                    "net_profit_margin": first_float(indicator, "netprofit_margin"),
                    "statement_type": str(first_value(income, balance, indicator, names=("comp_type", "type")) or ""),
                    "report_type": str(first_value(income, balance, indicator, names=("report_type",)) or ""),
                    "update_flag": str(first_value(income, balance, indicator, names=("update_flag",)) or ""),
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_FINANCIAL_PIT,
                    "source_run_id": ctx.run_id,
                    "schema_version": SCHEMA_VERSION,
                    "lineage_raw_checksum": checksum,
                    "payload": json.dumps(merged_payload, ensure_ascii=False, sort_keys=True, default=str),
                }
            )
    frame = pd.DataFrame(rows, columns=CANONICAL_FINANCIAL_PIT_COLUMNS).drop_duplicates(
        ["symbol", "report_period", "available_at", "update_flag"]
    )
    frame = frame.sort_values(["symbol", "report_period", "available_at"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_FINANCIAL_PIT, frame, "part-financial-pit.parquet")
    return frame


def fetch_stock_symbols(pro: Any, ctx: BackfillContext) -> list[str]:
    symbols: set[str] = set()
    for status in ("L", "D", "P"):
        rows = fetch_records(pro, ctx, "stock_basic", exchange="", list_status=status, fields="ts_code")
        symbols.update(symbol_value(row) for row in rows if symbol_value(row))
    return sorted(symbols)


def financial_key(row: dict[str, Any]) -> tuple[str, str]:
    report_period = row.get("end_date") or row.get("report_period")
    ann_date = row.get("ann_date") or row.get("f_ann_date") or report_period
    return (iso_day(report_period), iso_day(ann_date)) if report_period else ("", "")


def first_value(*rows: dict[str, Any], names: Sequence[str]) -> Any:
    for row in rows:
        for name in names:
            value = row.get(name)
            if value not in (None, ""):
                return value
    return None


def first_float(row: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = float_or_none(row.get(name))
        if value is not None:
            return value
    return None


def compact_payload(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "ts_code",
        "ann_date",
        "f_ann_date",
        "end_date",
        "report_type",
        "comp_type",
        "update_flag",
    )
    return {key: row.get(key) for key in keys if key in row}


def fetch_records(pro: Any, ctx: BackfillContext, method_name: str, **params: Any) -> list[dict[str, Any]]:
    if ctx.dry_run:
        return []
    method = getattr(pro, method_name)
    frame = method(**params)
    ctx.network_calls += 1
    if ctx.sleep_seconds > 0:
        time.sleep(ctx.sleep_seconds)
    if hasattr(frame, "to_dict"):
        return [dict(item) for item in frame.to_dict("records")]
    return [dict(item) for item in frame or []]


def write_dataset_frame(ctx: BackfillContext, dataset: str, frame: pd.DataFrame, filename: str) -> Path:
    summary = ctx.summaries.setdefault(dataset, DatasetSummary())
    summary.rows += len(frame)
    path = ctx.layout.canonical_dataset_root(dataset, SCHEMA_VERSION) / f"run_id={ctx.run_id}" / filename
    summary.paths.append(str(path))
    if not ctx.dry_run:
        ensure_parent_dirs_for_write(path)
        frame.to_parquet(path, index=False)
    return path


def write_summary(ctx: BackfillContext) -> Path:
    payload = {
        "schema_name": "cr034.chapter3_backfill_summary.v1",
        "run_id": ctx.run_id,
        "start": ctx.start,
        "end": ctx.end,
        "dry_run": ctx.dry_run,
        "network_calls": ctx.network_calls,
        "catalog_current_pointer_publish": 0,
        "qmt_operation": 0,
        "simulation_or_live_run": 0,
        "datasets": {
            key: {"rows": value.rows, "paths": value.paths, "notes": value.notes}
            for key, value in sorted(ctx.summaries.items())
        },
    }
    path = ctx.layout.quality_root / ctx.run_id / "cr034_chapter3_backfill_summary.json"
    if not ctx.dry_run:
        ensure_parent_dirs_for_write(path)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def checksum_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def iso_day(value: Any) -> str:
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def compact_day(value: Any) -> str:
    return iso_day(value).replace("-", "")


def timestamp(day: Any, time_text: str) -> str:
    return f"{iso_day(day)}T{time_text}+08:00"


def symbol_value(row: dict[str, Any]) -> str:
    return str(row.get("ts_code") or row.get("symbol") or "").strip().upper()


def float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def float_or_default(value: Any, default: float) -> float:
    result = float_or_none(value)
    return default if result is None else result


if __name__ == "__main__":
    raise SystemExit(main())
