"""实验六/七：动量与 RSI 策略回测报告生成脚本。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from itertools import product
import logging
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.backtest import BacktestConfig, BacktestResult, run_backtest
from engine.charts import generate_backtest_charts
from engine.data_loader import LoaderConfig, load_backtest_data
from engine.diagnostics import LOGGER_NAME
from engine.experiment_report_helpers import (
    format_value as _shared_format_value,
    markdown_table as _shared_markdown_table,
    resolve_date_range as _resolve_date_range,
)
from engine.metrics import validate_nav_integrity
from engine.portfolio import PortfolioConfig
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv


SIMPLIFIED_SYMBOLS = [
    "sz000001",  # 平安银行
    "sh600519",  # 贵州茅台
    "sz000858",  # 五粮液
    "sh600276",  # 恒瑞医药
    "sz000725",  # 京东方A
]

PERCENT_FIELDS = {
    "fraction",
    "total_return",
    "annual_return",
    "benchmark_total_return",
    "benchmark_annual_return",
    "benchmark_max_drawdown",
    "excess_return",
    "max_drawdown",
    "turnover",
}


def main() -> None:
    args = parse_args()
    diagnostics_logger = logging.getLogger(LOGGER_NAME)
    previous_disabled = diagnostics_logger.disabled
    if not args.verbose:
        diagnostics_logger.disabled = True
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    loaded, start_date, end_date = load_experiment_backtest_data(args, args.start_date, args.end_date)
    metadata = {
        **loaded.metadata,
        "start_date": start_date,
        "end_date": end_date,
        "initial_cash": args.initial_cash,
    }

    simplified_symbols = _select_available_symbols(loaded.close_df, SIMPLIFIED_SYMBOLS)
    simplified_close = loaded.close_df[simplified_symbols]
    local_full_symbols = loaded.universe[: args.full_symbol_limit] if args.full_symbol_limit else loaded.universe
    full_close = loaded.close_df[local_full_symbols]

    summaries: list[dict[str, Any]] = []
    summaries.append(
        run_case(
            "exp06_momentum_simplified",
            simplified_close,
            BacktestConfig(
                lookback_days=20,
                rebalance_freq=20,
                top_fraction=0.10,
                strategy_name="momentum",
                strategy_params={"sell_buffer": 2.0},
                portfolio_config=_portfolio_config(args.initial_cash),
            ),
            metadata,
            output_dir,
            "实验六：动量策略简化版（5只股票）",
        )
    )
    summaries.append(
        run_case(
            "exp06_momentum_full_local",
            full_close,
            BacktestConfig(
                lookback_days=20,
                rebalance_freq=20,
                top_fraction=0.10,
                strategy_name="momentum",
                strategy_params={"sell_buffer": 2.0},
                portfolio_config=_portfolio_config(args.initial_cash),
            ),
            metadata,
            output_dir,
            f"实验六：动量策略完整版代理（本地固定股票池前{len(local_full_symbols)}只）",
        )
    )
    summaries.append(
        run_case(
            "exp07_rsi_simplified",
            simplified_close,
            BacktestConfig(
                lookback_days=14,
                rebalance_freq=args.rsi_rebalance_freq,
                top_fraction=1.0,
                strategy_name="rsi",
                strategy_params={"period": 14, "oversold": 30, "overbought": 70, "top_fraction": 1.0},
                portfolio_config=_portfolio_config(args.initial_cash),
            ),
            metadata,
            output_dir,
            "实验七：RSI 策略（5只股票）",
        )
    )

    summary_path = write_rows_csv(summaries, output_dir / "summary.csv", list(summaries[0]))
    momentum_sweep = run_momentum_sweep(simplified_close, metadata, args.initial_cash)
    rsi_sweep = run_rsi_sweep(simplified_close, metadata, args.initial_cash, args.rsi_rebalance_freq)
    momentum_sweep_path = write_rows_csv(momentum_sweep, output_dir / "momentum_param_sweep.csv", list(momentum_sweep[0]))
    rsi_sweep_path = write_rows_csv(rsi_sweep, output_dir / "rsi_param_sweep.csv", list(rsi_sweep[0]))
    report_path = write_markdown_report(
        output_dir,
        summaries,
        momentum_sweep,
        rsi_sweep,
        {
            "summary": summary_path,
            "momentum_sweep": momentum_sweep_path,
            "rsi_sweep": rsi_sweep_path,
        },
        loaded_universe_count=len(loaded.universe),
        full_symbol_count=len(local_full_symbols),
        simplified_symbols=simplified_symbols,
        rsi_rebalance_freq=args.rsi_rebalance_freq,
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验六动量策略与实验七 RSI 策略。")
    add_market_data_input_args(parser)
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiments_06_07")))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--full-symbol-limit", type=int, default=300)
    parser.add_argument("--rsi-rebalance-freq", type=int, default=5)
    parser.add_argument("--verbose", action="store_true", help="输出结构化诊断日志。")
    return parser.parse_args()


def add_market_data_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input-mode", choices=["canonical-gold", "legacy-flat"], default="canonical-gold")
    parser.add_argument("--market-data-lake-root", default=None, help="canonical/gold reader 的只读 lake root。")
    parser.add_argument("--data-dir", default=None, help="仅在 --input-mode legacy-flat 时显式传入的外置兼容目录。")


def load_experiment_backtest_data(
    args: argparse.Namespace,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[Any, str, str]:
    input_mode = str(args.input_mode).replace("-", "_")
    if input_mode == "legacy_flat":
        if not args.data_dir:
            raise ValueError("--input-mode legacy-flat 需要显式传入外置 --data-dir")
        resolved_start, resolved_end = _resolve_date_range(Path(args.data_dir), start_date, end_date)
        loaded = load_backtest_data(
            LoaderConfig(
                input_mode="legacy_flat",
                data_dir=args.data_dir,
                quality_report_path=args.quality_report,
                start_date=resolved_start,
                end_date=resolved_end,
                legacy_flat_enabled=True,
            )
        )
        loaded.metadata["legacy_flat_enabled"] = True
        return loaded, resolved_start, resolved_end
    loaded = load_backtest_data(
        LoaderConfig(
            input_mode="canonical_gold",
            market_data_lake_root=args.market_data_lake_root,
            quality_report_path=args.quality_report,
            start_date=start_date,
            end_date=end_date,
        )
    )
    resolved_start = start_date or str(loaded.metadata.get("start_date") or "")
    resolved_end = end_date or str(loaded.metadata.get("end_date") or "")
    return loaded, resolved_start, resolved_end


def run_case(
    run_id: str,
    close_df: pd.DataFrame,
    config: BacktestConfig,
    metadata: dict[str, Any],
    output_dir: Path,
    title: str,
) -> dict[str, Any]:
    result = run_backtest(close_df, config, metadata=metadata)
    equity = build_equity_frame(result)
    benchmark = build_equal_weight_benchmark(close_df, metadata["initial_cash"])
    trades = [asdict(trade) for trade in result.portfolio_result.trades]
    equity_path = output_dir / f"{run_id}_equity_curve.csv"
    benchmark_path = output_dir / f"{run_id}_benchmark_equity_curve.csv"
    trades_path = output_dir / f"{run_id}_trades.csv"
    equity.to_csv(equity_path, index=False)
    benchmark["equity"].to_csv(benchmark_path, index=False)
    pd.DataFrame(trades).to_csv(trades_path, index=False)
    generate_backtest_charts(equity, output_dir / "charts", prefix=f"{run_id}_")
    generate_backtest_charts(benchmark["equity"], output_dir / "charts", prefix=f"{run_id}_benchmark_")
    return {
        "run_id": run_id,
        "title": title,
        "benchmark_name": benchmark["name"],
        "strategy_name": config.strategy_name,
        "symbols": len(close_df.columns),
        "trade_days": len(close_df.index),
        "schedule_count": len(result.schedule),
        "lookback": config.lookback_days,
        "rebalance_freq": config.rebalance_freq,
        "fraction": config.top_fraction,
        "total_return": result.metrics["total_return"],
        "annual_return": result.metrics["annual_return"],
        "max_drawdown": result.metrics["max_drawdown"],
        "sharpe": result.metrics["sharpe"],
        "turnover": result.metrics["turnover"],
        "final_value": result.metrics["final_value"],
        "benchmark_total_return": benchmark["metrics"]["total_return"],
        "benchmark_annual_return": benchmark["metrics"]["annual_return"],
        "benchmark_max_drawdown": benchmark["metrics"]["max_drawdown"],
        "benchmark_sharpe": benchmark["metrics"]["sharpe"],
        "excess_return": result.metrics["total_return"] - benchmark["metrics"]["total_return"],
        "quality_status": result.metadata.get("quality_status", ""),
        "equity_curve_path": str(equity_path),
        "benchmark_equity_curve_path": str(benchmark_path),
        "trades_path": str(trades_path),
    }


def run_momentum_sweep(close_df: pd.DataFrame, metadata: dict[str, Any], initial_cash: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lookback, rebalance_freq, fraction in product([5, 10, 20, 30, 60], [5, 10, 20, 30], [0.05, 0.10, 0.20]):
        sell_buffer = max(0.0, 0.30 / fraction - 1.0)
        row = run_sweep_item(
            close_df,
            BacktestConfig(
                lookback_days=lookback,
                rebalance_freq=rebalance_freq,
                top_fraction=fraction,
                strategy_name="momentum",
                strategy_params={"sell_buffer": sell_buffer},
                portfolio_config=_portfolio_config(initial_cash),
            ),
            metadata,
        )
        row.update({"lookback": lookback, "rebalance_freq": rebalance_freq, "fraction": fraction})
        rows.append(row)
    return rows


def run_rsi_sweep(
    close_df: pd.DataFrame,
    metadata: dict[str, Any],
    initial_cash: float,
    rebalance_freq: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period, oversold, overbought in product([7, 14, 21, 28], [20, 25, 30, 35], [65, 70, 75, 80]):
        row = run_sweep_item(
            close_df,
            BacktestConfig(
                lookback_days=period,
                rebalance_freq=rebalance_freq,
                top_fraction=1.0,
                strategy_name="rsi",
                strategy_params={
                    "period": period,
                    "oversold": oversold,
                    "overbought": overbought,
                    "top_fraction": 1.0,
                },
                portfolio_config=_portfolio_config(initial_cash),
            ),
            metadata,
        )
        row.update({"period": period, "oversold": oversold, "overbought": overbought})
        rows.append(row)
    return rows


def run_sweep_item(close_df: pd.DataFrame, config: BacktestConfig, metadata: dict[str, Any]) -> dict[str, Any]:
    try:
        result = run_backtest(close_df, config, metadata=metadata)
        return {
            "strategy_name": config.strategy_name,
            "status": "success",
            "error_message": "",
            "total_return": result.metrics["total_return"],
            "annual_return": result.metrics["annual_return"],
            "max_drawdown": result.metrics["max_drawdown"],
            "sharpe": result.metrics["sharpe"],
            "turnover": result.metrics["turnover"],
            "final_value": result.metrics["final_value"],
        }
    except Exception as exc:
        return {
            "strategy_name": config.strategy_name,
            "status": "failed",
            "error_message": f"{type(exc).__name__}: {exc}",
            "total_return": "",
            "annual_return": "",
            "max_drawdown": "",
            "sharpe": "",
            "turnover": "",
            "final_value": "",
        }


def build_equity_frame(result: BacktestResult) -> pd.DataFrame:
    rows = []
    initial = result.portfolio_result.daily_snapshots[0].total_value
    running_max = initial
    for snapshot in result.portfolio_result.daily_snapshots:
        running_max = max(running_max, snapshot.total_value)
        nav = snapshot.total_value / initial
        rows.append(
            {
                "trade_date": snapshot.trade_date,
                "cash": snapshot.cash,
                "position_value": snapshot.position_value,
                "total_value": snapshot.total_value,
                "nav": nav,
                "drawdown": snapshot.total_value / running_max - 1.0,
                "turnover_amount": snapshot.turnover_amount,
                "holding_count": len(snapshot.holdings),
            }
        )
    return pd.DataFrame(rows)


def build_equal_weight_benchmark(close_df: pd.DataFrame, initial_cash: float) -> dict[str, Any]:
    """构建同股票池等权买入持有 benchmark。"""

    cleaned = close_df.apply(pd.to_numeric, errors="coerce").ffill()
    first_prices = cleaned.iloc[0].dropna()
    first_prices = first_prices[first_prices > 0]
    if first_prices.empty:
        raise ValueError("benchmark 无法构建：首日没有有效价格")
    work = cleaned[first_prices.index].copy()
    relative = work.divide(first_prices, axis="columns")
    nav = relative.mean(axis=1).ffill()
    values = nav * float(initial_cash)
    metrics = calculate_series_metrics(values)
    running_max = values.cummax()
    equity = pd.DataFrame(
        {
            "trade_date": list(close_df.index),
            "total_value": values.to_numpy(),
            "nav": nav.to_numpy(),
            "drawdown": (values / running_max - 1.0).to_numpy(),
            "turnover_amount": [float(initial_cash)] * len(values),
            "holding_count": [len(first_prices)] * len(values),
        }
    )
    return {
        "name": "equal_weight_buy_hold_same_universe",
        "metrics": metrics,
        "equity": equity,
    }


def calculate_series_metrics(values: pd.Series) -> dict[str, Any]:
    """按组合净值序列计算 benchmark 指标。"""

    values = pd.Series(values, index=values.index, dtype="float64")
    validate_nav_integrity(values)
    initial = float(values.iloc[0])
    final = float(values.iloc[-1])
    daily_returns = values.pct_change().dropna()
    years = max(len(values) / 252.0, 1 / 252.0)
    drawdown = values / values.cummax() - 1.0
    std = float(daily_returns.std(ddof=0)) if not daily_returns.empty else 0.0
    sharpe = None if std == 0 else float(daily_returns.mean() / std * (252**0.5))
    return {
        "total_return": final / initial - 1.0 if initial else 0.0,
        "annual_return": (final / initial) ** (1 / years) - 1.0 if initial > 0 else None,
        "max_drawdown": float(drawdown.min()),
        "sharpe": sharpe,
        "final_value": final,
    }


def write_markdown_report(
    output_dir: Path,
    summaries: list[dict[str, Any]],
    momentum_sweep: list[dict[str, Any]],
    rsi_sweep: list[dict[str, Any]],
    paths: dict[str, str],
    *,
    loaded_universe_count: int,
    full_symbol_count: int,
    simplified_symbols: list[str],
    rsi_rebalance_freq: int,
) -> str:
    lines = [
        "# 实验六/七回测报告",
        "",
        "## 数据与限制",
        "",
        f"- 数据区间：{summaries[0].get('trade_days')} 个交易日，默认报告使用本地 parquet 离线数据。",
        f"- 简化版股票池：{', '.join(simplified_symbols)}。",
        f"- 完整版代理股票池：本地固定股票池前 {full_symbol_count} 只；当前离线成分表总数 {loaded_universe_count} 只。",
        "- 当前 `data/index_members.parquet` 是固定快照且 `is_pit_universe=false`，不是严格历史沪深300 PIT 成分；报告保留幸存者偏差说明。",
        "- 当前未启用真实交易状态/涨跌停门禁，缺价会导致成交跳过；组合引擎按金额成交，未模拟 A 股 100 股一手取整。",
        "- Benchmark：当前没有沪深300指数行情文件，默认使用同股票池等权买入持有基准（equal_weight_buy_hold_same_universe）。",
        f"- RSI 策略默认每 {rsi_rebalance_freq} 个交易日检查一次信号；可通过 `--rsi-rebalance-freq` 调整。",
        "",
        "## 默认回测结果",
        "",
        _markdown_table(
            summaries,
            [
                "run_id",
                "title",
                "symbols",
                "total_return",
                "benchmark_total_return",
                "excess_return",
                "annual_return",
                "max_drawdown",
                "benchmark_max_drawdown",
                "sharpe",
                "benchmark_sharpe",
                "turnover",
                "final_value",
            ],
        ),
        "",
        "## 动量参数变体 Top 10（简化版股票池）",
        "",
        _markdown_table(
            _top_rows(momentum_sweep, "sharpe", 10),
            ["lookback", "rebalance_freq", "fraction", "total_return", "annual_return", "max_drawdown", "sharpe", "turnover"],
        ),
        "",
        "## RSI 参数变体 Top 10（简化版股票池）",
        "",
        _markdown_table(
            _top_rows(rsi_sweep, "sharpe", 10),
            ["period", "oversold", "overbought", "total_return", "annual_return", "max_drawdown", "sharpe", "turnover"],
        ),
        "",
        "## 输出文件",
        "",
        f"- 汇总表：`{paths['summary']}`",
        f"- 动量参数表：`{paths['momentum_sweep']}`",
        f"- RSI 参数表：`{paths['rsi_sweep']}`",
        f"- 图表目录：`{output_dir / 'charts'}`",
        "",
    ]
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _top_rows(rows: list[dict[str, Any]], metric: str, limit: int) -> list[dict[str, Any]]:
    success = [row for row in rows if row.get("status") == "success" and row.get(metric) not in ("", None)]
    return sorted(success, key=lambda row: float(row[metric]), reverse=True)[:limit]


def _markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    return _shared_markdown_table(rows, fields, percent_fields=PERCENT_FIELDS)


def _format_value(value: Any, field: str) -> str:
    return _shared_format_value(value, field, percent_fields=PERCENT_FIELDS)


def _select_available_symbols(close_df: pd.DataFrame, symbols: list[str]) -> list[str]:
    selected: list[str] = []
    missing: list[str] = []
    for symbol in symbols:
        matched = _match_symbol(close_df.columns, symbol)
        if matched:
            selected.append(matched)
        else:
            missing.append(symbol)
    for symbol in close_df.columns:
        if len(selected) >= len(symbols):
            break
        if symbol not in selected:
            selected.append(str(symbol))
    if not selected:
        raise ValueError(f"简化版股票池缺少本地行情: {missing}")
    return selected


def _match_symbol(columns: pd.Index, symbol: str) -> str | None:
    if symbol in columns:
        return symbol
    aliases = _symbol_aliases(symbol)
    for alias in aliases:
        if alias in columns:
            return alias
    return None


def _symbol_aliases(symbol: str) -> list[str]:
    lower = symbol.lower()
    if len(lower) == 8 and lower.startswith(("sz", "sh")):
        code = lower[2:]
        suffix = "SZ" if lower.startswith("sz") else "SH"
        return [f"{code}.{suffix}"]
    if len(symbol) == 9 and symbol[6] == ".":
        code = symbol[:6]
        suffix = symbol[7:].upper()
        prefix = "sz" if suffix == "SZ" else "sh" if suffix == "SH" else ""
        return [f"{prefix}{code}"] if prefix else []
    return []


def _portfolio_config(initial_cash: float) -> PortfolioConfig:
    return PortfolioConfig(initial_cash=initial_cash)


if __name__ == "__main__":
    main()
