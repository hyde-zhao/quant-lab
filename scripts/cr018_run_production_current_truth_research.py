"""CR018 published current truth 阶段三到阶段五核心研究重跑。

该脚本只读 published catalog current pointer，写入 release-scoped research
reports，不读取凭据、不调用 provider、不发布 catalog、不操作 QMT。
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.metrics import calculate_metrics
from engine.portfolio import PortfolioConfig, RebalanceSignal, TradeGate, run_portfolio
from engine.research_paths import research_report_path
from market_data.catalog import CatalogEntry, CatalogStore, build_production_readiness_report
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
)
from market_data.lake_layout import LakeLayout, ensure_parent_dirs_for_write


CORE_DATASETS = (
    DATASET_PRICES,
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    DATASET_INDEX_MEMBERS,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_STATUS,
    DATASET_PRICES_LIMIT,
    DATASET_EVENTS,
)
PHASES = ("phase_3", "phase_4", "phase_5")
TRADING_DAYS_PER_YEAR = 252


class StatusTradeGate:
    """按 published trade_status / ST 状态约束交易。"""

    def __init__(self, tradable: pd.DataFrame, suspended: pd.DataFrame, st_flag: pd.DataFrame) -> None:
        self.tradable = tradable
        self.suspended = suspended
        self.st_flag = st_flag

    def can_execute_trade(self, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
        key = _coerce_date(trade_date)
        if not _matrix_bool(self.tradable, key, symbol):
            return False, "not_tradable"
        if _matrix_bool(self.suspended, key, symbol):
            return False, "suspended"
        if side == "buy" and _matrix_bool(self.st_flag, key, symbol):
            return False, "st_buy_blocked"
        return True, ""


class LimitTradeGate:
    """按涨跌停约束买卖。"""

    def __init__(self, limit_up: pd.DataFrame, limit_down: pd.DataFrame) -> None:
        self.limit_up = limit_up
        self.limit_down = limit_down

    def can_execute_trade(self, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
        key = _coerce_date(trade_date)
        if side == "buy" and _matrix_bool(self.limit_up, key, symbol):
            return False, "limit_up_buy_blocked"
        if side == "sell" and _matrix_bool(self.limit_down, key, symbol):
            return False, "limit_down_sell_blocked"
        return True, ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CR018 production current truth research rerun")
    parser.add_argument("--lake-root", default="/mnt/ugreen-data-lake")
    parser.add_argument("--release-id", default="release-cr018-production-current-truth-20150101-20260528-20260529")
    parser.add_argument("--run-id", default="run-cr018-production-rerun-20150101-20260528-20260529-01")
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default="2026-05-28")
    parser.add_argument("--output-root", default=str(research_report_path("production_current_truth")))
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--rebalance-freq", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--min-cross-section", type=int, default=30)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_root) / args.release_id / args.run_id
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "output_dir_exists",
                    "output_dir": str(output_dir),
                    "remediation": "use a new --run-id or pass --overwrite",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    layout = LakeLayout(Path(args.lake_root))
    catalog = CatalogStore(layout)
    readiness = build_production_readiness_report(layout, realism_mode="production_strict")
    if readiness.get("status") != "pass":
        write_json(output_dir / "rerun-report.json", _blocked_report(args, readiness, "readiness_not_pass"))
        return 1

    entries = {dataset: catalog.get(dataset) for dataset in CORE_DATASETS}
    catalog_issues = validate_catalog_entries(entries)
    if catalog_issues:
        write_json(output_dir / "rerun-report.json", _blocked_report(args, readiness, "catalog_entry_invalid", catalog_issues))
        return 1

    bundle = load_current_truth_bundle(layout, entries, args.start_date, args.end_date)
    materialized = materialize_standard_inputs(output_dir / "input_data", bundle)
    market = build_market_matrices(bundle)

    phase3 = run_phase3_core(args, market)
    phase4 = run_phase4_core(args, market, phase3)
    phase5 = run_phase5_core(args, market, phase3)
    report = build_report(args, output_dir, readiness, entries, materialized, phase3, phase4, phase5)

    write_json(output_dir / "rerun-report.json", report)
    write_json(output_dir / "qmt-admission-evidence.json", report["qmt_admission_evidence"])
    write_json(output_dir / "old-proxy-fixed-baseline-diff.json", report["old_proxy_fixed_baseline_diff"])
    write_markdown(output_dir / "rerun-summary.md", report)
    write_csv_outputs(output_dir, phase3, phase4, phase5)

    print(json.dumps(_json_safe({"ok": True, "report_path": str(output_dir / "rerun-report.json"), **report["summary"]}), ensure_ascii=False, sort_keys=True))
    return 0


def validate_catalog_entries(entries: Mapping[str, CatalogEntry]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for dataset, entry in entries.items():
        if not entry.published:
            issues.append({"dataset": dataset, "code": "catalog_not_published"})
        if entry.quality_status != QUALITY_STATUS_PASS:
            issues.append({"dataset": dataset, "code": "quality_not_pass", "quality_status": entry.quality_status})
        if entry.readiness_status != READINESS_STATUS_AVAILABLE:
            issues.append({"dataset": dataset, "code": "readiness_not_available", "readiness_status": entry.readiness_status})
        if not entry.canonical_path:
            issues.append({"dataset": dataset, "code": "canonical_path_missing"})
    return issues


def load_current_truth_bundle(
    layout: LakeLayout,
    entries: Mapping[str, CatalogEntry],
    start_date: str,
    end_date: str,
) -> dict[str, pd.DataFrame]:
    prices = read_entry_frame(
        layout,
        entries[DATASET_PRICES],
        columns=[
            "trade_date",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "adjusted_open",
            "adjusted_high",
            "adjusted_low",
            "adjusted_close",
            "adjustment_policy",
            "source_run_id",
            "available_at_rule",
        ],
    )
    status = read_entry_frame(
        layout,
        entries[DATASET_TRADE_STATUS],
        columns=["trade_date", "symbol", "is_tradable", "is_suspended", "is_st", "status_reason"],
    )
    limits = read_entry_frame(
        layout,
        entries[DATASET_PRICES_LIMIT],
        columns=["trade_date", "symbol", "limit_up", "limit_down"],
    )
    calendar = read_entry_frame(
        layout,
        entries[DATASET_TRADE_CALENDAR],
        columns=["trade_date", "is_open"],
    )
    benchmarks = read_entry_frame(
        layout,
        entries[DATASET_HS300_INDEX],
        columns=["trade_date", "index_code", "close", "pre_close", "pct_chg", "benchmark_kind"],
    )
    index_members = read_entry_frame(
        layout,
        entries[DATASET_INDEX_MEMBERS],
        columns=["trade_date", "index_code", "con_code", "is_member", "is_pit_universe", "pit_status"],
    )
    stock_basic = read_entry_frame(
        layout,
        entries[DATASET_STOCK_BASIC],
        columns=["symbol", "name", "market", "list_status", "list_date", "delist_date", "pit_status", "readiness_status"],
    )

    for frame in (prices, status, limits, calendar, benchmarks, index_members):
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    start = pd.to_datetime(start_date).date()
    end = pd.to_datetime(end_date).date()
    return {
        "prices": prices[(prices["trade_date"] >= start) & (prices["trade_date"] <= end)].reset_index(drop=True),
        "trade_status": status[(status["trade_date"] >= start) & (status["trade_date"] <= end)].reset_index(drop=True),
        "prices_limit": limits[(limits["trade_date"] >= start) & (limits["trade_date"] <= end)].reset_index(drop=True),
        "trade_calendar": calendar[(calendar["trade_date"] >= start) & (calendar["trade_date"] <= end)].reset_index(drop=True),
        "benchmarks": benchmarks[(benchmarks["trade_date"] >= start) & (benchmarks["trade_date"] <= end)].reset_index(drop=True),
        "index_members": index_members[(index_members["trade_date"] >= start) & (index_members["trade_date"] <= end)].reset_index(drop=True),
        "stock_basic": stock_basic.reset_index(drop=True),
    }


def read_entry_frame(layout: LakeLayout, entry: CatalogEntry, *, columns: Sequence[str]) -> pd.DataFrame:
    path = layout.lake_root / str(entry.canonical_path)
    if not path.exists():
        raise FileNotFoundError(f"catalog canonical_path 不存在: {path}")
    dataset = ds.dataset(str(path), format="parquet")
    available = set(dataset.schema.names)
    selected = [column for column in columns if column in available]
    missing = sorted(set(columns) - set(selected))
    if missing:
        raise ValueError(f"{entry.dataset} 缺少字段: {missing}")
    return dataset.to_table(columns=selected).to_pandas()


def materialize_standard_inputs(output_dir: Path, bundle: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prices = enrich_prices(bundle)
    members = bundle["trade_status"][["trade_date", "symbol", "is_tradable", "is_suspended", "is_st"]].copy()
    members["is_member"] = (
        members["is_tradable"].fillna(False).astype(bool)
        & ~members["is_suspended"].fillna(False).astype(bool)
        & ~members["is_st"].fillna(False).astype(bool)
    )
    calendar = bundle["trade_calendar"].copy()

    prices_path = output_dir / "prices.parquet"
    members_path = output_dir / "index_members.parquet"
    calendar_path = output_dir / "trade_calendar.parquet"
    benchmark_path = output_dir / "benchmark_index.parquet"
    prices.to_parquet(prices_path, index=False)
    members.to_parquet(members_path, index=False)
    calendar.to_parquet(calendar_path, index=False)
    bundle["benchmarks"].to_parquet(benchmark_path, index=False)
    return {
        "input_data_dir": str(output_dir),
        "prices_path": str(prices_path),
        "index_members_path": str(members_path),
        "trade_calendar_path": str(calendar_path),
        "benchmark_path": str(benchmark_path),
        "prices_rows": int(len(prices)),
        "index_members_rows": int(len(members)),
        "calendar_rows": int(len(calendar)),
        "benchmark_rows": int(len(bundle["benchmarks"])),
    }


def enrich_prices(bundle: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    prices = bundle["prices"].copy()
    prices["symbol"] = prices["symbol"].astype("string").str.strip()
    for column in ("open", "high", "low", "close", "volume", "amount", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"):
        prices[column] = pd.to_numeric(prices[column], errors="coerce")
    prices = prices.rename(columns={"open": "raw_open", "high": "raw_high", "low": "raw_low", "close": "raw_close"})
    prices["open"] = prices["adjusted_open"].fillna(prices["raw_open"])
    prices["high"] = prices["adjusted_high"].fillna(prices["raw_high"])
    prices["low"] = prices["adjusted_low"].fillna(prices["raw_low"])
    prices["close"] = prices["adjusted_close"].fillna(prices["raw_close"])

    status = bundle["trade_status"][["trade_date", "symbol", "is_tradable", "is_suspended", "is_st"]].copy()
    limits = bundle["prices_limit"][["trade_date", "symbol", "limit_up", "limit_down"]].copy()
    limits["limit_up"] = pd.to_numeric(limits["limit_up"], errors="coerce")
    limits["limit_down"] = pd.to_numeric(limits["limit_down"], errors="coerce")
    prices = prices.merge(status, on=["trade_date", "symbol"], how="left")
    prices = prices.merge(limits, on=["trade_date", "symbol"], how="left")
    prices["is_tradable"] = prices["is_tradable"].fillna(False).astype(bool)
    prices["is_suspended"] = prices["is_suspended"].fillna(False).astype(bool)
    prices["is_st"] = prices["is_st"].fillna(False).astype(bool)
    prices["st_flag"] = prices["is_st"]
    prices["is_limit_up"] = prices["limit_up"].notna() & prices["raw_close"].ge(prices["limit_up"] * 0.9999)
    prices["is_limit_down"] = prices["limit_down"].notna() & prices["raw_close"].le(prices["limit_down"] * 1.0001)
    prices["adjustment_policy"] = "qfq"
    return prices.sort_values(["trade_date", "symbol"]).reset_index(drop=True)


def build_market_matrices(bundle: Mapping[str, pd.DataFrame]) -> dict[str, Any]:
    prices = enrich_prices(bundle)
    calendar = bundle["trade_calendar"].copy()
    calendar["trade_date"] = pd.to_datetime(calendar["trade_date"]).dt.date
    if "is_open" in calendar.columns:
        calendar = calendar[calendar["is_open"].fillna(False).astype(bool)]
    dates = sorted(calendar["trade_date"].dropna().unique().tolist())
    universe = sorted(prices["symbol"].dropna().astype(str).unique().tolist())

    def pivot(column: str, fill: Any | None = None) -> pd.DataFrame:
        matrix = prices.pivot_table(index="trade_date", columns="symbol", values=column, aggfunc="last")
        matrix = matrix.reindex(index=dates, columns=universe)
        if fill is not None:
            matrix = matrix.where(matrix.notna(), fill)
            if isinstance(fill, bool):
                matrix = matrix.astype(bool)
        matrix.index.name = "date"
        return matrix

    close = pivot("close")
    volume = pivot("volume")
    amount = pivot("amount")
    tradable = pivot("is_tradable", False).astype(bool)
    suspended = pivot("is_suspended", False).astype(bool)
    st_flag = pivot("st_flag", False).astype(bool)
    limit_up = pivot("is_limit_up", False).astype(bool)
    limit_down = pivot("is_limit_down", False).astype(bool)
    benchmarks = build_benchmark_matrices(bundle["benchmarks"], dates)
    return {
        "prices": prices,
        "calendar": dates,
        "universe": universe,
        "close": close,
        "volume": volume,
        "amount": amount,
        "tradable": tradable,
        "suspended": suspended,
        "st_flag": st_flag,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "benchmarks": benchmarks,
        "status_gate": StatusTradeGate(tradable, suspended, st_flag),
        "limit_gate": LimitTradeGate(limit_up, limit_down),
    }


def build_benchmark_matrices(frame: pd.DataFrame, dates: Sequence[date]) -> pd.DataFrame:
    work = frame.copy()
    work["trade_date"] = pd.to_datetime(work["trade_date"]).dt.date
    work["close"] = pd.to_numeric(work["close"], errors="coerce")
    matrix = work.pivot_table(index="trade_date", columns="index_code", values="close", aggfunc="last")
    return matrix.reindex(index=list(dates)).sort_index()


def run_phase3_core(args: argparse.Namespace, market: Mapping[str, Any]) -> dict[str, Any]:
    close = market["close"]
    volume = market["volume"]
    amount = market["amount"]
    buyable = market["tradable"] & ~market["suspended"] & ~market["st_flag"] & ~market["limit_up"]
    factors = build_factor_scores(close, volume, amount)
    forward_20d = close.shift(-20) / close - 1.0
    ic_summary = build_ic_summary(factors, forward_20d, buyable, int(args.min_cross_section))
    group_returns = build_group_returns(factors["volatility_20d"], forward_20d, buyable, int(args.min_cross_section))
    strategies = {
        "single_volatility_20d_top20": run_top_n_strategy(args, market, factors["volatility_20d"], "single_volatility_20d_top20", int(args.top_n)),
        "single_volatility_20d_top10": run_top_n_strategy(args, market, factors["volatility_20d"], "single_volatility_20d_top10", 10),
        "stage3_equal_weight_multifactor_top20": run_top_n_strategy(args, market, factors["multifactor_score"], "stage3_equal_weight_multifactor_top20", int(args.top_n)),
        "momentum_20d_top20_negative_control": run_top_n_strategy(args, market, factors["momentum_20d"], "momentum_20d_top20_negative_control", int(args.top_n)),
    }
    benchmark_metrics = {
        code: calculate_series_metrics(market["benchmarks"][code].dropna())
        for code in market["benchmarks"].columns
    }
    return {
        "factor_ic_summary": ic_summary,
        "low_vol_group_returns": group_returns,
        "strategies": {name: strategy_payload(result) for name, result in strategies.items()},
        "strategy_objects": strategies,
        "benchmark_metrics": benchmark_metrics,
    }


def build_factor_scores(close: pd.DataFrame, volume: pd.DataFrame, amount: pd.DataFrame) -> dict[str, pd.DataFrame]:
    returns = close.pct_change(fill_method=None)
    momentum_20d = close / close.shift(20) - 1.0
    reversal_5d = -(close / close.shift(5) - 1.0)
    volatility_20d = -returns.rolling(20, min_periods=20).std(ddof=0)
    rolling_max = close.rolling(20, min_periods=20).max()
    max_drawdown_20d = close / rolling_max - 1.0
    volume_change_20d = volume.rolling(20, min_periods=20).mean() / volume.rolling(40, min_periods=40).mean() - 1.0
    turnover_proxy = np.log1p(amount.where(amount > 0))
    raw = {
        "momentum_20d": momentum_20d,
        "reversal_5d": reversal_5d,
        "volatility_20d": volatility_20d,
        "max_drawdown_20d": max_drawdown_20d,
        "volume_change_20d": volume_change_20d,
        "turnover_proxy": turnover_proxy,
    }
    zscores = {name: cross_section_zscore(frame) for name, frame in raw.items()}
    main = [zscores[name] for name in ("volatility_20d", "reversal_5d", "max_drawdown_20d") if name in zscores]
    zscores["multifactor_score"] = sum(main) / len(main)
    return zscores


def cross_section_zscore(frame: pd.DataFrame) -> pd.DataFrame:
    mean = frame.mean(axis=1, skipna=True)
    std = frame.std(axis=1, skipna=True, ddof=0).replace(0, np.nan)
    return frame.sub(mean, axis=0).div(std, axis=0)


def build_ic_summary(
    factors: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    mask: pd.DataFrame,
    min_cross_section: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, matrix in factors.items():
        if name == "multifactor_score":
            continue
        valid = matrix.where(mask).notna() & forward_returns.notna()
        sample_counts = valid.sum(axis=1)
        pearson = matrix.where(mask).corrwith(forward_returns, axis=1)
        rank_ic = matrix.where(mask).rank(axis=1).corrwith(forward_returns.rank(axis=1), axis=1)
        pearson = pearson[sample_counts >= min_cross_section].dropna()
        rank_ic = rank_ic[sample_counts >= min_cross_section].dropna()
        rows.append(
            {
                "factor": name,
                "ic_mean": _float_or_none(pearson.mean()),
                "rank_ic_mean": _float_or_none(rank_ic.mean()),
                "icir": _safe_div(pearson.mean(), pearson.std(ddof=0)),
                "rank_icir": _safe_div(rank_ic.mean(), rank_ic.std(ddof=0)),
                "valid_dates": int(len(rank_ic)),
                "avg_cross_section": _float_or_none(sample_counts[sample_counts >= min_cross_section].mean()),
            }
        )
    return rows


def build_group_returns(
    score: pd.DataFrame,
    forward_returns: pd.DataFrame,
    mask: pd.DataFrame,
    min_cross_section: int,
    group_count: int = 5,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[int, list[float]] = {group: [] for group in range(1, group_count + 1)}
    for current_date in score.index:
        day = pd.DataFrame({"score": score.loc[current_date], "forward": forward_returns.loc[current_date], "eligible": mask.loc[current_date]})
        day = day[day["eligible"] & day["score"].notna() & day["forward"].notna()].copy()
        if len(day) < min_cross_section:
            continue
        ranks = day["score"].rank(method="first")
        day["group"] = pd.qcut(ranks, group_count, labels=False, duplicates="drop") + 1
        for group, group_frame in day.groupby("group"):
            grouped[int(group)].append(float(group_frame["forward"].mean()))
    for group in range(1, group_count + 1):
        values = grouped[group]
        rows.append({"group": group, "mean_forward_20d": _float_or_none(np.mean(values) if values else None), "sample_dates": len(values)})
    top = rows[-1]["mean_forward_20d"]
    bottom = rows[0]["mean_forward_20d"]
    rows.append({"group": "top_minus_bottom", "mean_forward_20d": _safe_subtract(top, bottom), "sample_dates": min(rows[0]["sample_dates"], rows[-1]["sample_dates"])})
    return rows


def run_top_n_strategy(
    args: argparse.Namespace,
    market: Mapping[str, Any],
    score: pd.DataFrame,
    strategy_name: str,
    top_n: int,
    *,
    config: PortfolioConfig | None = None,
) -> dict[str, Any]:
    close = market["close"]
    buyable = market["tradable"] & ~market["suspended"] & ~market["st_flag"] & ~market["limit_up"]
    signals = build_top_n_signals(score, buyable, int(args.rebalance_freq), top_n)
    result = run_portfolio(
        close,
        signals,
        config or PortfolioConfig(initial_cash=float(args.initial_cash)),
        trade_gate=market["status_gate"],
        limit_gate=market["limit_gate"],
    )
    metrics = calculate_metrics(result)
    trades = pd.DataFrame([asdict(trade) for trade in result.trades])
    equity = pd.DataFrame(
        [
            {
                "date": item.trade_date,
                "strategy_name": strategy_name,
                "total_value": item.total_value,
                "cash": item.cash,
                "position_value": item.position_value,
                "holding_count": len(item.holdings),
                "turnover_amount": item.turnover_amount,
            }
            for item in result.daily_snapshots
        ]
    )
    reason_counts = Counter(trades.loc[trades["status"] == "unfilled", "reason"].astype(str).tolist()) if not trades.empty else Counter()
    return {
        "strategy_name": strategy_name,
        "top_n": top_n,
        "signals": signals,
        "result": result,
        "equity": equity,
        "trades": trades,
        "metrics": {
            **metrics,
            "signal_count": len(signals),
            "filled_trade_count": int((trades["status"] == "filled").sum()) if not trades.empty else 0,
            "unfilled_trade_count": int((trades["status"] == "unfilled").sum()) if not trades.empty else 0,
            "unfilled_reason_counts": dict(reason_counts),
        },
    }


def build_top_n_signals(score: pd.DataFrame, buyable: pd.DataFrame, rebalance_freq: int, top_n: int) -> list[RebalanceSignal]:
    dates = list(score.index)
    signals: list[RebalanceSignal] = []
    for idx in range(20, len(dates) - 1, rebalance_freq):
        signal_date = dates[idx]
        execution_date = dates[idx + 1]
        day_score = score.loc[signal_date].where(buyable.loc[signal_date]).dropna()
        if day_score.empty:
            continue
        ranked = day_score.sort_values(ascending=False).head(top_n)
        signals.append(
            RebalanceSignal(
                signal_date=_coerce_date(signal_date),
                execution_date=_coerce_date(execution_date),
                target_symbols=[str(item) for item in ranked.index],
            )
        )
    return signals


def run_phase4_core(args: argparse.Namespace, market: Mapping[str, Any], phase3: Mapping[str, Any]) -> dict[str, Any]:
    low_vol = phase3["strategy_objects"]["single_volatility_20d_top20"]
    equity = low_vol["equity"].copy()
    annual = annual_equity_breakdown(equity)
    factor_rows = pd.DataFrame(phase3["factor_ic_summary"])
    low_vol_ic = factor_rows[factor_rows["factor"] == "volatility_20d"].to_dict(orient="records")
    negative_controls = {
        "momentum_20d_top20_negative_control": phase3["strategies"]["momentum_20d_top20_negative_control"]["metrics"],
    }
    return {
        "annual_low_vol_breakdown": annual,
        "low_vol_ic": low_vol_ic[0] if low_vol_ic else {},
        "negative_controls": negative_controls,
        "robustness_status": "pass" if low_vol_ic and float(low_vol_ic[0].get("rank_ic_mean") or 0.0) > 0 else "fail",
    }


def run_phase5_core(args: argparse.Namespace, market: Mapping[str, Any], phase3: Mapping[str, Any]) -> dict[str, Any]:
    del args
    low_vol = phase3["strategy_objects"]["single_volatility_20d_top20"]
    equity = low_vol["equity"]
    trades = low_vol["trades"]
    daily_returns = equity["total_value"].pct_change(fill_method=None).dropna() if not equity.empty else pd.Series(dtype="float64")
    risk = {
        "daily_var_95": _float_or_none(daily_returns.quantile(0.05) if not daily_returns.empty else None),
        "daily_cvar_95": _float_or_none(daily_returns[daily_returns <= daily_returns.quantile(0.05)].mean() if not daily_returns.empty else None),
        "max_drawdown": low_vol["metrics"].get("max_drawdown"),
        "turnover": low_vol["metrics"].get("turnover"),
    }
    cost_grid = build_cost_grid(low_vol)
    capacity = build_capacity_summary(trades, market["amount"])
    tradability = {
        "unfilled_trade_count": int(low_vol["metrics"].get("unfilled_trade_count") or 0),
        "unfilled_reason_counts": dict(low_vol["metrics"].get("unfilled_reason_counts") or {}),
        "tradability_fields": {
            "is_suspended": "available",
            "is_limit_up": "available",
            "is_limit_down": "available",
            "st_flag": "available",
            "amount": "available",
            "turnover_rate": "missing",
            "vwap": "missing",
            "industry": "missing",
            "market_cap": "missing",
        },
    }
    return {"risk": risk, "cost_grid": cost_grid, "capacity": capacity, "tradability": tradability}


def build_cost_grid(strategy: Mapping[str, Any]) -> list[dict[str, Any]]:
    base = strategy["metrics"]
    turnover = float(base.get("turnover") or 0.0)
    annual = float(base.get("annual_return") or 0.0)
    rows = []
    for bps in (0, 5, 10, 20, 50, 100):
        annual_after_cost = annual - turnover * (bps / 10000.0)
        rows.append({"cost_bps": bps, "annual_return_after_cost_proxy": annual_after_cost})
    return rows


def build_capacity_summary(trades: pd.DataFrame, amount: pd.DataFrame) -> dict[str, Any]:
    if trades.empty or "status" not in trades.columns:
        return {"status": "no_trades", "sample_count": 0}
    filled = trades[trades["status"] == "filled"].copy()
    if filled.empty:
        return {"status": "no_filled_trades", "sample_count": 0}
    lookup = amount.stack(future_stack=True).rename("amount").reset_index().rename(columns={"date": "execution_date", "level_1": "symbol"})
    lookup["execution_date"] = pd.to_datetime(lookup["execution_date"]).dt.date
    filled["execution_date"] = pd.to_datetime(filled["execution_date"]).dt.date
    sample = filled.merge(lookup, on=["execution_date", "symbol"], how="left")
    sample["participation_rate"] = sample["notional"] / sample["amount"].replace(0, np.nan)
    rates = sample["participation_rate"].replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "status": "available" if not rates.empty else "amount_missing",
        "sample_count": int(len(sample)),
        "valid_participation_count": int(len(rates)),
        "mean_participation_rate": _float_or_none(rates.mean() if not rates.empty else None),
        "p95_participation_rate": _float_or_none(rates.quantile(0.95) if not rates.empty else None),
        "max_participation_rate": _float_or_none(rates.max() if not rates.empty else None),
        "over_10pct_count": int((rates > 0.10).sum()) if not rates.empty else 0,
    }


def build_report(
    args: argparse.Namespace,
    output_dir: Path,
    readiness: Mapping[str, Any],
    entries: Mapping[str, CatalogEntry],
    materialized: Mapping[str, Any],
    phase3: Mapping[str, Any],
    phase4: Mapping[str, Any],
    phase5: Mapping[str, Any],
) -> dict[str, Any]:
    low_vol = phase3["strategies"]["single_volatility_20d_top20"]["metrics"]
    hs300 = phase3["benchmark_metrics"].get("399300.SZ", {})
    low_vol_annual = float(low_vol.get("annual_return") or 0.0)
    hs300_annual = float(hs300.get("annual_return") or 0.0)
    low_vol_drawdown = float(low_vol.get("max_drawdown") or 0.0)
    hs300_drawdown = float(hs300.get("max_drawdown") or 0.0)
    rank_ic = float((phase4.get("low_vol_ic") or {}).get("rank_ic_mean") or 0.0)
    strategy_pass = low_vol_annual > hs300_annual and low_vol_drawdown >= hs300_drawdown and rank_ic > 0
    blocked_claims = []
    if not strategy_pass:
        blocked_claims.append(
            {
                "claim": "qmt_admission",
                "reason_code": "production_rerun_strategy_criteria_failed",
                "severity": "BLOCKING",
            }
        )
    for claim in ("pure_alpha", "industry_neutralized", "market_cap_neutralized", "risk_model_adjusted_alpha"):
        blocked_claims.append({"claim": claim, "reason_code": "p1_auxiliary_missing", "severity": "NON_BLOCKING_FOR_CORE_RELEASE"})

    status = "pass" if strategy_pass else "fail"
    operation_counts = {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "catalog_current_pointer_publish": 0,
        "qmt_operation": 0,
        "old_report_overwrite": 0,
        "candidate_read_count": 0,
        "proxy_input_allowed_count": 0,
        "duckdb_dependency_change": 0,
    }
    return _json_safe(
        {
            "schema_name": "cr018.production_current_truth_real_rerun_report.v1",
            "mode": "real_published_current_truth_rerun",
            "fixture_only": False,
            "real_stage_3_to_5_execution": True,
            "status": status,
            "pass": strategy_pass,
            "fail": not strategy_pass,
            "release_id": args.release_id,
            "run_id": args.run_id,
            "research_phases": list(PHASES),
            "coverage_start": args.start_date,
            "coverage_end": args.end_date,
            "as_of_trade_date": args.end_date,
            "research_adjustment_policy": "qfq",
            "benchmark_policy": "real_index_required",
            "readiness": {
                "status": readiness.get("status"),
                "blockers": readiness.get("blockers"),
                "allowed_claims": readiness.get("allowed_claims"),
            },
            "catalog_entries": {
                dataset: {
                    "canonical_path": entry.canonical_path,
                    "published": entry.published,
                    "quality_status": entry.quality_status,
                    "readiness_status": entry.readiness_status,
                    "coverage_denominator": entry.coverage_denominator,
                }
                for dataset, entry in entries.items()
            },
            "materialized_inputs": dict(materialized),
            "phase_3": {key: value for key, value in phase3.items() if key != "strategy_objects"},
            "phase_4": dict(phase4),
            "phase_5": dict(phase5),
            "summary": {
                "status": status,
                "low_vol_top20_annual_return": low_vol_annual,
                "hs300_annual_return": hs300_annual,
                "low_vol_minus_hs300_annual_return": low_vol_annual - hs300_annual,
                "low_vol_top20_max_drawdown": low_vol_drawdown,
                "hs300_max_drawdown": hs300_drawdown,
                "low_vol_rank_ic_mean": rank_ic,
                "strategy_pass": strategy_pass,
                "qmt_admission_allowed_count": 1 if strategy_pass else 0,
            },
            "old_proxy_fixed_baseline_diff": {
                "schema_name": "cr018.old_proxy_fixed_baseline_diff.v1",
                "old_baseline_policy": "comparison_only_not_production_input",
                "old_proxy_or_fixed_input_allowed": False,
                "proxy_input_allowed_count": 0,
                "note": "本次未读取旧报告正文，仅在报告中声明旧 baseline 不作为 production input。",
            },
            "qmt_admission_evidence": {
                "schema_name": "cr018.qmt_admission_evidence_from_real_s08.v1",
                "release_id": args.release_id,
                "rerun_status": status,
                "s08_pass": strategy_pass,
                "allowed": strategy_pass,
                "qmt_admission_allowed_count": 1 if strategy_pass else 0,
                "qmt_operation": 0,
                "evidence_paths": {"rerun_report": str(output_dir / "rerun-report.json")},
                "blocked_claims": blocked_claims if not strategy_pass else [item for item in blocked_claims if item["severity"] != "BLOCKING"],
            },
            "blocked_claims": blocked_claims,
            "operation_counts": operation_counts,
            **operation_counts,
        }
    )


def write_csv_outputs(output_dir: Path, phase3: Mapping[str, Any], phase4: Mapping[str, Any], phase5: Mapping[str, Any]) -> None:
    pd.DataFrame(phase3["factor_ic_summary"]).to_csv(output_dir / "phase3-factor-ic-summary.csv", index=False)
    pd.DataFrame(phase3["low_vol_group_returns"]).to_csv(output_dir / "phase3-low-vol-group-returns.csv", index=False)
    pd.DataFrame(
        [
            {"strategy_name": name, **payload["metrics"]}
            for name, payload in phase3["strategies"].items()
        ]
    ).to_csv(output_dir / "phase3-strategy-summary.csv", index=False)
    pd.DataFrame(phase4["annual_low_vol_breakdown"]).to_csv(output_dir / "phase4-low-vol-annual-breakdown.csv", index=False)
    pd.DataFrame(phase5["cost_grid"]).to_csv(output_dir / "phase5-cost-grid.csv", index=False)


def write_markdown(path: Path, report: Mapping[str, Any]) -> None:
    summary = report["summary"]
    phase5 = report["phase_5"]
    lines = [
        "# CR018 Production Current Truth Rerun Summary",
        "",
        f"- release_id: `{report['release_id']}`",
        f"- run_id: `{report['run_id']}`",
        f"- status: `{summary['status']}`",
        f"- research_adjustment_policy: `{report['research_adjustment_policy']}`",
        f"- coverage: `{report['coverage_start']}`..`{report['coverage_end']}`",
        f"- low_vol_top20_annual_return: `{summary['low_vol_top20_annual_return']:.4%}`",
        f"- hs300_annual_return: `{summary['hs300_annual_return']:.4%}`",
        f"- low_vol_minus_hs300_annual_return: `{summary['low_vol_minus_hs300_annual_return']:.4%}`",
        f"- low_vol_top20_max_drawdown: `{summary['low_vol_top20_max_drawdown']:.4%}`",
        f"- hs300_max_drawdown: `{summary['hs300_max_drawdown']:.4%}`",
        f"- low_vol_rank_ic_mean: `{summary['low_vol_rank_ic_mean']:.6f}`",
        f"- qmt_admission_allowed_count: `{summary['qmt_admission_allowed_count']}`",
        "",
        "## Phase 5 Tradability",
        "",
        f"- unfilled_trade_count: `{phase5['tradability']['unfilled_trade_count']}`",
        f"- unfilled_reason_counts: `{json.dumps(phase5['tradability']['unfilled_reason_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- capacity_status: `{phase5['capacity'].get('status')}`",
        "",
        "## Operation Counts",
        "",
        "```json",
        json.dumps(report["operation_counts"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def strategy_payload(strategy: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "strategy_name": strategy["strategy_name"],
        "top_n": strategy["top_n"],
        "metrics": strategy["metrics"],
    }


def annual_equity_breakdown(equity: pd.DataFrame) -> list[dict[str, Any]]:
    if equity.empty:
        return []
    work = equity.copy()
    work["date"] = pd.to_datetime(work["date"])
    rows = []
    for year, group in work.groupby(work["date"].dt.year):
        values = group.sort_values("date")["total_value"]
        if len(values) < 2:
            continue
        rows.append({"year": int(year), "return": float(values.iloc[-1] / values.iloc[0] - 1.0), "days": int(len(values))})
    return rows


def calculate_series_metrics(close: pd.Series) -> dict[str, Any]:
    close = pd.to_numeric(close, errors="coerce").dropna()
    if len(close) < 2:
        return {"status": "insufficient_data"}
    returns = close.pct_change(fill_method=None).dropna()
    total_return = float(close.iloc[-1] / close.iloc[0] - 1.0)
    annual_return = float((1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / max(len(returns), 1)) - 1.0)
    nav = close / close.iloc[0]
    drawdown = nav / nav.cummax() - 1.0
    sharpe = _safe_div(returns.mean() * TRADING_DAYS_PER_YEAR, returns.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
    return {
        "status": "available",
        "total_return": total_return,
        "annual_return": annual_return,
        "max_drawdown": _float_or_none(drawdown.min()),
        "sharpe": sharpe,
        "start_date": str(close.index.min()),
        "end_date": str(close.index.max()),
    }


def _blocked_report(args: argparse.Namespace, readiness: Mapping[str, Any], reason: str, issues: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    return {
        "schema_name": "cr018.production_current_truth_real_rerun_report.v1",
        "status": "blocked",
        "release_id": args.release_id,
        "run_id": args.run_id,
        "reason_code": reason,
        "issues": [dict(item) for item in issues],
        "readiness": dict(readiness),
        "qmt_admission_evidence": {"allowed": False, "qmt_admission_allowed_count": 0, "qmt_operation": 0},
    }


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    ensure_parent_dirs_for_write(path)
    path.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _matrix_bool(matrix: pd.DataFrame, current_date: date, symbol: str) -> bool:
    try:
        value = matrix.at[current_date, symbol]
    except KeyError:
        return False
    return bool(value) if pd.notna(value) else False


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def _float_or_none(value: Any) -> float | None:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def _safe_div(numerator: Any, denominator: Any) -> float | None:
    left = _float_or_none(numerator)
    right = _float_or_none(denominator)
    if left is None or right in (None, 0.0):
        return None
    return left / right


def _safe_subtract(left: Any, right: Any) -> float | None:
    a = _float_or_none(left)
    b = _float_or_none(right)
    if a is None or b is None:
        return None
    return a - b


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


if __name__ == "__main__":
    raise SystemExit(main())
