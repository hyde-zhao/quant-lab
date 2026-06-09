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
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from market_data.contracts import (
    CR005_CANONICAL_PRICES_COLUMNS,
    CANONICAL_ADJ_FACTOR_COLUMNS,
    CANONICAL_EVENTS_COLUMNS,
    CANONICAL_PRICES_LIMIT_COLUMNS,
    CANONICAL_STOCK_BASIC_COLUMNS,
    CANONICAL_TRADE_STATUS_COLUMNS,
    CANONICAL_TRADE_CALENDAR_COLUMNS,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    DATASET_TRADE_CALENDAR,
    INTERFACE_EVENTS_DISCLOSURE,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_PRICES_LIMIT_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_STATUS_DAILY,
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

AUDITED_FINANCIAL_PIT_COLUMNS = (
    *CANONICAL_FINANCIAL_PIT_COLUMNS,
    "revision_as_of",
    "revision_sequence",
    "is_latest_known_on_available_at",
    "pit_policy",
    "revision_source_limitation",
)

DERIVED_EVENTS_INTERFACE = "stock_basic.lifecycle+namechange.history"
DERIVED_TRADE_STATUS_INTERFACE = "prices.daily+stock_basic.lifecycle+namechange.history"
DERIVED_PRICES_LIMIT_INTERFACE = "prices.daily+stock_basic.lifecycle+namechange.history"


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
        help=(
            "逗号分隔：trade_calendar,prices,adj_factor,prices_hfq,market_cap,liquidity,"
            "financial_pit,financial_pit_audit,trade_status,prices_limit,events"
        ),
    )
    parser.add_argument("--symbols", default="", help="财务 PIT 可选 symbol CSV；缺省时读取 Tushare stock_basic L/D/P")
    parser.add_argument(
        "--namechange-symbols",
        default="",
        help="历史 ST/namechange 可选 symbol CSV；缺省时读取 lake stock_basic 符号",
    )
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
    if "financial_pit_audit" in selected:
        write_financial_pit_audit(ctx)
    if {"trade_status", "prices_limit", "events"} & selected:
        stock_basic = load_stock_basic_lifecycle(ctx)
        namechange_symbols = [item.strip().upper() for item in str(args.namechange_symbols).split(",") if item.strip()]
        if not namechange_symbols:
            namechange_symbols = sorted(stock_basic["symbol"].dropna().astype(str).str.upper().unique().tolist())
        namechange = fetch_namechange_history(pro, ctx, symbols=namechange_symbols)
        if "events" in selected:
            write_chapter3_events(ctx, stock_basic, namechange)
        if "trade_status" in selected or "prices_limit" in selected:
            write_tradability_and_limit_datasets(ctx, stock_basic, namechange, write_trade_status="trade_status" in selected, write_prices_limit="prices_limit" in selected)
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


def write_financial_pit_audit(ctx: BackfillContext) -> pd.DataFrame:
    """把已有公告日财务 PIT 固化为带 revision/as-of 审计字段的候选 run。"""

    frame = read_canonical_dataset(
        ctx,
        DATASET_FINANCIAL_PIT,
        columns=CANONICAL_FINANCIAL_PIT_COLUMNS,
        start=ctx.start,
        end=ctx.end,
        date_column="available_at",
    )
    if frame.empty:
        audited = pd.DataFrame(columns=AUDITED_FINANCIAL_PIT_COLUMNS)
        write_dataset_frame(ctx, DATASET_FINANCIAL_PIT, audited, "part-financial-pit-audited.parquet")
        ctx.summaries[DATASET_FINANCIAL_PIT].notes.append("financial_pit_audit_empty")
        return audited
    audited = frame.copy()
    audited["available_at"] = audited["available_at"].map(lambda value: timestamp(iso_day(value), "16:00:00") if "T" not in str(value) else str(value))
    audited["revision_as_of"] = audited["available_at"]
    audited = audited.sort_values(["symbol", "report_period", "available_at", "update_flag"]).reset_index(drop=True)
    audited["revision_sequence"] = audited.groupby(["symbol", "report_period"]).cumcount() + 1
    max_sequence = audited.groupby(["symbol", "report_period"])["revision_sequence"].transform("max")
    audited["is_latest_known_on_available_at"] = audited["revision_sequence"].eq(max_sequence)
    audited["pit_policy"] = "ann_date_available_at_no_lookahead"
    audited["revision_source_limitation"] = (
        "Tushare income/balancesheet/fina_indicator expose ann_date/report_period/update_flag; "
        "vendor revision ingestion timestamp is not provided, so revision_as_of equals available_at."
    )
    audited["source_run_id"] = ctx.run_id
    audited["source_interface"] = INTERFACE_FINANCIAL_PIT + "+audit"
    audited["lineage_raw_checksum"] = checksum_text(f"{ctx.run_id}:financial_pit_audit:{len(audited)}")
    audited = audited[list(AUDITED_FINANCIAL_PIT_COLUMNS)].drop_duplicates(
        ["symbol", "report_period", "available_at", "update_flag", "revision_sequence"]
    )
    write_dataset_frame(ctx, DATASET_FINANCIAL_PIT, audited, "part-financial-pit-audited.parquet")
    return audited


def load_stock_basic_lifecycle(ctx: BackfillContext) -> pd.DataFrame:
    frame = read_canonical_dataset(ctx, DATASET_STOCK_BASIC, columns=CANONICAL_STOCK_BASIC_COLUMNS)
    if frame.empty:
        raise RuntimeError("缺少 stock_basic canonical，无法构造第三章历史股票生命周期分母")
    frame = frame.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["list_date"] = frame["list_date"].map(iso_day)
    frame["delist_date"] = frame["delist_date"].map(lambda value: iso_day(value) if str(value).strip() else "")
    frame["_list_date_sort"] = frame["list_date"].replace("", "9999-12-31")
    frame["_delist_date_sort"] = frame["delist_date"].replace("", "9999-12-31")
    frame["_status_priority"] = frame.get("list_status", "").map(lambda value: {"L": 0, "D": 1, "P": 2}.get(str(value), 9))
    frame = frame.sort_values(["symbol", "_status_priority", "_list_date_sort", "_delist_date_sort"])
    frame = frame.drop_duplicates(["symbol"], keep="first")
    return frame.drop(columns=[column for column in ("_list_date_sort", "_delist_date_sort", "_status_priority") if column in frame.columns])


def fetch_namechange_history(pro: Any, ctx: BackfillContext, *, symbols: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, symbol in enumerate(symbols, start=1):
        if index == 1 or index % 500 == 0:
            print(f"[namechange] {index}/{len(symbols)} {symbol}", flush=True)
        try:
            raw = fetch_records(pro, ctx, "namechange", ts_code=symbol)
        except Exception as exc:  # noqa: BLE001
            ctx.summaries.setdefault(DATASET_EVENTS, DatasetSummary()).notes.append(f"namechange_failed:{symbol}:{exc.__class__.__name__}")
            continue
        for row in raw:
            start_date = row.get("start_date") or row.get("ann_date") or row.get("change_date") or row.get("trade_date")
            if not start_date:
                continue
            end_date = row.get("end_date") or ""
            rows.append(
                {
                    "symbol": symbol_value(row) or symbol,
                    "name": str(row.get("name") or ""),
                    "start_date": iso_day(start_date),
                    "end_date": iso_day(end_date) if str(end_date).strip() else "",
                    "ann_date": iso_day(row.get("ann_date")) if str(row.get("ann_date") or "").strip() else iso_day(start_date),
                    "change_reason": str(row.get("change_reason") or row.get("reason") or ""),
                }
            )
    frame = pd.DataFrame(rows, columns=["symbol", "name", "start_date", "end_date", "ann_date", "change_reason"])
    if frame.empty:
        return frame
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame = frame.drop_duplicates(["symbol", "start_date", "end_date", "name", "change_reason"])
    frame = frame.sort_values(["symbol", "start_date", "end_date", "name"]).reset_index(drop=True)
    ctx.summaries.setdefault(DATASET_EVENTS, DatasetSummary()).notes.append(f"namechange_rows={len(frame)}")
    return frame


def write_chapter3_events(ctx: BackfillContext, stock_basic: pd.DataFrame, namechange: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    checksum = checksum_text(f"{ctx.run_id}:events:lifecycle:{len(stock_basic)}:namechange:{len(namechange)}")
    for row in records_from_frame(stock_basic):
        symbol = str(row.get("symbol") or "").upper()
        if not symbol:
            continue
        list_date = str(row.get("list_date") or "")
        delist_date = str(row.get("delist_date") or "")
        if list_date:
            rows.append(event_row(ctx, symbol, "list", list_date, "stock_basic_lifecycle", row, checksum))
        if delist_date:
            rows.append(event_row(ctx, symbol, "delist", delist_date, "stock_basic_lifecycle", row, checksum))
    for row in records_from_frame(namechange):
        symbol = str(row.get("symbol") or "").upper()
        event_date = str(row.get("ann_date") or row.get("start_date") or "")
        if not symbol or not event_date:
            continue
        event_type = "st_status" if row_indicates_st(row) else "name_change"
        rows.append(event_row(ctx, symbol, event_type, event_date, "namechange_history", row, checksum))
    frame = pd.DataFrame(rows, columns=CANONICAL_EVENTS_COLUMNS).drop_duplicates(["symbol", "event_type", "event_date", "available_at"])
    frame = frame.sort_values(["symbol", "event_date", "event_type"]).reset_index(drop=True)
    write_dataset_frame(ctx, DATASET_EVENTS, frame, "part-events-lifecycle-namechange.parquet")
    return frame


def write_tradability_and_limit_datasets(
    ctx: BackfillContext,
    stock_basic: pd.DataFrame,
    namechange: pd.DataFrame,
    *,
    write_trade_status: bool,
    write_prices_limit: bool,
) -> None:
    open_dates = existing_open_dates(ctx)
    if not open_dates:
        raise RuntimeError("缺少 trade_calendar open dates，无法派生 trade_status/prices_limit")
    st_intervals = build_st_intervals(namechange)
    previous_close_by_symbol: dict[str, float] = {}
    for year in range(parse_date(ctx.start).year, parse_date(ctx.end).year + 1):
        year_start = max(ctx.start, f"{year}-01-01")
        year_end = min(ctx.end, f"{year}-12-31")
        year_open_dates = [item for item in open_dates if year_start <= item <= year_end]
        if not year_open_dates:
            continue
        print(f"[chapter3_constraints] {year} open_dates={len(year_open_dates)}", flush=True)
        prices = read_price_close_for_window(ctx, year_start, year_end)
        price_pairs = prices[["trade_date", "symbol"]].drop_duplicates(["trade_date", "symbol"]) if not prices.empty else pd.DataFrame(columns=["trade_date", "symbol"])
        active_pairs = active_lifecycle_pairs(stock_basic, year_open_dates)
        st_pairs = st_pairs_for_dates(st_intervals, year_open_dates)
        if write_trade_status:
            trade_status = build_trade_status_frame(ctx, year, active_pairs, price_pairs, st_pairs)
            write_dataset_frame(ctx, DATASET_TRADE_STATUS, trade_status, f"part-trade-status-derived-{year}.parquet")
        if write_prices_limit:
            prices_limit, previous_close_by_symbol = build_prices_limit_frame(ctx, year, prices, st_pairs, previous_close_by_symbol)
            write_dataset_frame(ctx, DATASET_PRICES_LIMIT, prices_limit, f"part-prices-limit-derived-{year}.parquet")


def build_trade_status_frame(
    ctx: BackfillContext,
    year: int,
    active_pairs: pd.DataFrame,
    price_pairs: pd.DataFrame,
    st_pairs: pd.DataFrame,
) -> pd.DataFrame:
    frame = active_pairs.merge(price_pairs.assign(_has_price=True), on=["trade_date", "symbol"], how="left")
    frame = frame.merge(st_pairs.assign(_is_st=True), on=["trade_date", "symbol"], how="left")
    frame["is_suspended"] = ~frame["_has_price"].eq(True)
    frame["is_st"] = frame["_is_st"].eq(True)
    frame["is_tradable"] = ~frame["is_suspended"]
    frame["status_reason"] = "trading"
    frame.loc[frame["is_st"], "status_reason"] = "st"
    frame.loc[frame["is_suspended"], "status_reason"] = "suspended_derived_missing_daily"
    frame.loc[frame["is_suspended"] & frame["is_st"], "status_reason"] = "st_suspended_derived_missing_daily"
    frame["source"] = SOURCE_TUSHARE
    frame["source_interface"] = DERIVED_TRADE_STATUS_INTERFACE
    frame["source_run_id"] = ctx.run_id
    frame["available_at"] = frame["trade_date"].map(lambda value: timestamp(value, "09:30:00"))
    frame["available_at_rule"] = "derived_from_lifecycle_daily_namechange_09:30"
    frame["schema_version"] = SCHEMA_VERSION
    frame["lineage_raw_checksum"] = checksum_text(f"{ctx.run_id}:trade_status:{year}:{len(frame)}")
    return frame[list(CANONICAL_TRADE_STATUS_COLUMNS)].sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def build_prices_limit_frame(
    ctx: BackfillContext,
    year: int,
    prices: pd.DataFrame,
    st_pairs: pd.DataFrame,
    previous_close_by_symbol: Mapping[str, float],
) -> tuple[pd.DataFrame, dict[str, float]]:
    if prices.empty:
        empty = pd.DataFrame(columns=CANONICAL_PRICES_LIMIT_COLUMNS)
        return empty, dict(previous_close_by_symbol)
    frame = prices.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    frame["previous_close"] = frame.groupby("symbol")["close"].shift(1)
    first_indices = frame.groupby("symbol", sort=False).head(1).index
    frame.loc[first_indices, "previous_close"] = frame.loc[first_indices, "symbol"].map(previous_close_by_symbol)
    st_keys = {tuple(item) for item in st_pairs[["trade_date", "symbol"]].itertuples(index=False, name=None)}
    frame["_is_st"] = [tuple(item) in st_keys for item in frame[["trade_date", "symbol"]].itertuples(index=False, name=None)]
    frame["limit_ratio"] = frame["_is_st"].map(lambda value: 0.05 if value else 0.10)
    frame["limit_up"] = [
        round_price_half_up(previous_close * (1.0 + ratio))
        for previous_close, ratio in frame[["previous_close", "limit_ratio"]].itertuples(index=False, name=None)
    ]
    frame["limit_down"] = [
        round_price_half_up(previous_close * (1.0 - ratio))
        for previous_close, ratio in frame[["previous_close", "limit_ratio"]].itertuples(index=False, name=None)
    ]
    frame.loc[frame["previous_close"].isna(), ["limit_up", "limit_down"]] = pd.NA
    frame["source"] = SOURCE_TUSHARE
    frame["source_interface"] = DERIVED_PRICES_LIMIT_INTERFACE
    frame["source_run_id"] = ctx.run_id
    frame["available_at"] = frame["trade_date"].map(lambda value: timestamp(value, "08:40:00"))
    frame["available_at_rule"] = "derived_from_previous_close_st_policy_08:40"
    frame["schema_version"] = SCHEMA_VERSION
    frame["lineage_raw_checksum"] = checksum_text(f"{ctx.run_id}:prices_limit:{year}:{len(frame)}")
    last_close = frame.dropna(subset=["close"]).groupby("symbol")["close"].last().to_dict()
    output = frame[list(CANONICAL_PRICES_LIMIT_COLUMNS)].drop_duplicates(["trade_date", "symbol"])
    return output.sort_values(["trade_date", "symbol"]).reset_index(drop=True), {str(key): float(value) for key, value in last_close.items()}


def read_price_close_for_window(ctx: BackfillContext, start: str, end: str) -> pd.DataFrame:
    frame = read_canonical_dataset(ctx, DATASET_PRICES, columns=("trade_date", "symbol", "close"), start=start, end=end)
    if frame.empty:
        return pd.DataFrame(columns=["trade_date", "symbol", "close"])
    frame["trade_date"] = frame["trade_date"].astype(str)
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    return frame.dropna(subset=["close"]).drop_duplicates(["trade_date", "symbol"], keep="last")


def active_lifecycle_pairs(stock_basic: pd.DataFrame, open_dates: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for day in open_dates:
        active = stock_basic[
            (stock_basic["list_date"].astype(str) <= day)
            & ((stock_basic["delist_date"].astype(str) == "") | (stock_basic["delist_date"].astype(str) >= day))
        ]
        rows.extend({"trade_date": day, "symbol": symbol} for symbol in active["symbol"].astype(str).str.upper().tolist())
    if not rows:
        return pd.DataFrame(columns=["trade_date", "symbol"])
    return pd.DataFrame(rows).drop_duplicates(["trade_date", "symbol"])


def build_st_intervals(namechange: pd.DataFrame) -> dict[str, list[tuple[str, str]]]:
    intervals: dict[str, list[tuple[str, str]]] = {}
    if namechange.empty:
        return intervals
    for row in records_from_frame(namechange):
        if not row_indicates_st(row):
            continue
        symbol = str(row.get("symbol") or "").upper()
        start_date = str(row.get("start_date") or row.get("ann_date") or "")
        if not symbol or not start_date:
            continue
        end_date = str(row.get("end_date") or "9999-12-31")
        intervals.setdefault(symbol, []).append((start_date, end_date))
    return intervals


def st_pairs_for_dates(intervals: Mapping[str, Sequence[tuple[str, str]]], open_dates: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for symbol, ranges in intervals.items():
        for start_date, end_date in ranges:
            rows.extend({"trade_date": day, "symbol": symbol} for day in open_dates if start_date <= day <= end_date)
    if not rows:
        return pd.DataFrame(columns=["trade_date", "symbol"])
    return pd.DataFrame(rows).drop_duplicates(["trade_date", "symbol"])


def row_indicates_st(row: Mapping[str, Any]) -> bool:
    text = " ".join(str(row.get(key) or "") for key in ("name", "change_reason", "type_name", "event_type")).upper()
    return "ST" in text or "退" in text


def event_row(
    ctx: BackfillContext,
    symbol: str,
    event_type: str,
    event_date: str,
    available_at_rule: str,
    payload: Mapping[str, Any],
    checksum: str,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "event_type": event_type,
        "event_date": iso_day(event_date),
        "available_at": timestamp(event_date, "09:20:00"),
        "available_at_rule": available_at_rule,
        "payload": json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, default=str),
        "source": SOURCE_TUSHARE,
        "source_interface": DERIVED_EVENTS_INTERFACE,
        "source_run_id": ctx.run_id,
        "schema_version": SCHEMA_VERSION,
        "lineage_raw_checksum": checksum,
    }


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


def read_canonical_dataset(
    ctx: BackfillContext,
    dataset: str,
    *,
    columns: Sequence[str] | None = None,
    start: str = "",
    end: str = "",
    date_column: str = "trade_date",
) -> pd.DataFrame:
    root = ctx.layout.canonical_dataset_root(dataset, SCHEMA_VERSION)
    if not root.exists():
        return pd.DataFrame(columns=list(columns or ()))
    frames: list[pd.DataFrame] = []
    for path in sorted(root.glob("run_id=*/*.parquet")):
        try:
            frame = pd.read_parquet(path, columns=list(columns) if columns else None)
        except Exception:
            try:
                frame = pd.read_parquet(path)
            except Exception:
                continue
            if columns:
                for column in columns:
                    if column not in frame.columns:
                        frame[column] = pd.NA
                frame = frame[list(columns)]
        if frame.empty:
            continue
        if date_column in frame.columns and (start or end):
            dates = frame[date_column].map(iso_day)
            if start:
                frame = frame[dates >= start]
                dates = dates.loc[frame.index]
            if end:
                frame = frame[dates <= end]
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=list(columns or ()))
    return pd.concat(frames, ignore_index=True)


def records_from_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    clean = frame.where(pd.notna(frame), None)
    return [dict(row) for row in clean.to_dict("records")]


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


def parse_date(value: Any) -> date:
    return datetime.strptime(compact_day(value), "%Y%m%d").date()


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


def round_price_half_up(value: Any) -> float | None:
    if value in (None, "") or pd.isna(value):
        return None
    try:
        return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, TypeError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
