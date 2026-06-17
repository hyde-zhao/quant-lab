"""实验八：MACD 金叉/死叉策略回测报告。"""

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

from engine.backtest import BacktestConfig, run_backtest
from engine.charts import generate_backtest_charts
from engine.diagnostics import LOGGER_NAME
from engine.portfolio import PortfolioConfig
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv
from experiments.run_experiment_06_07 import (
    SIMPLIFIED_SYMBOLS,
    add_market_data_input_args,
    build_equal_weight_benchmark,
    build_equity_frame,
    load_experiment_backtest_data,
)


PERCENT_FIELDS = {
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
    selected_symbols = _select_available_symbols(loaded.close_df, SIMPLIFIED_SYMBOLS)
    close_df = loaded.close_df[selected_symbols]
    metadata = {
        **loaded.metadata,
        "start_date": start_date,
        "end_date": end_date,
        "initial_cash": args.initial_cash,
    }

    default_summary = run_macd_case(
        "exp08_macd_default",
        close_df,
        fast=12,
        slow=26,
        signal=9,
        metadata=metadata,
        output_dir=output_dir,
        initial_cash=args.initial_cash,
        title="实验八：MACD 金叉/死叉策略（5只股票）",
    )
    split_index = int(len(close_df) * args.train_ratio)
    train_close = close_df.iloc[:split_index]
    test_close = close_df.iloc[split_index:]
    sweep_rows = run_macd_parameter_sweep(train_close, metadata, args.initial_cash)
    top_candidates = _top_rows(sweep_rows, "sharpe", args.oos_candidates)
    oos_rows = [
        run_macd_oos_item(test_close, candidate, metadata, args.initial_cash)
        for candidate in top_candidates
    ]

    summary_path = write_rows_csv([default_summary], output_dir / "summary.csv", list(default_summary))
    sweep_path = write_rows_csv(sweep_rows, output_dir / "macd_param_sweep_train.csv", list(sweep_rows[0]))
    oos_path = write_rows_csv(oos_rows, output_dir / "macd_oos_top_candidates.csv", list(oos_rows[0]))
    report_path = write_markdown_report(
        output_dir,
        default_summary,
        sweep_rows,
        oos_rows,
        {
            "summary": summary_path,
            "sweep": sweep_path,
            "oos": oos_path,
        },
        selected_symbols=selected_symbols,
        train_start=str(train_close.index[0]),
        train_end=str(train_close.index[-1]),
        test_start=str(test_close.index[0]),
        test_end=str(test_close.index[-1]),
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验八 MACD 金叉/死叉策略。")
    add_market_data_input_args(parser)
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_08")))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--oos-candidates", type=int, default=5)
    parser.add_argument("--verbose", action="store_true", help="输出结构化诊断日志。")
    return parser.parse_args()


def run_macd_case(
    run_id: str,
    close_df: pd.DataFrame,
    *,
    fast: int,
    slow: int,
    signal: int,
    metadata: dict[str, Any],
    output_dir: Path,
    initial_cash: float,
    title: str,
) -> dict[str, Any]:
    config = _macd_config(fast, slow, signal, initial_cash)
    result = run_backtest(close_df, config, metadata=metadata)
    equity = build_equity_frame(result)
    benchmark = build_equal_weight_benchmark(close_df, initial_cash)
    trades = [asdict(trade) for trade in result.portfolio_result.trades]

    equity_path = output_dir / f"{run_id}_equity_curve.csv"
    benchmark_path = output_dir / f"{run_id}_benchmark_equity_curve.csv"
    trades_path = output_dir / f"{run_id}_trades.csv"
    equity.to_csv(equity_path, index=False)
    benchmark["equity"].to_csv(benchmark_path, index=False)
    pd.DataFrame(trades).to_csv(trades_path, index=False)
    generate_backtest_charts(equity, output_dir / "charts", prefix=f"{run_id}_")
    generate_backtest_charts(benchmark["equity"], output_dir / "charts", prefix=f"{run_id}_benchmark_")

    return _summary_row(
        run_id,
        title,
        close_df,
        result.metrics,
        benchmark["metrics"],
        fast,
        slow,
        signal,
        len(result.schedule),
        str(equity_path),
        str(benchmark_path),
        str(trades_path),
    )


def run_macd_parameter_sweep(close_df: pd.DataFrame, metadata: dict[str, Any], initial_cash: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fast, slow, signal in product([8, 12, 16], [21, 26, 35], [5, 9]):
        if fast >= slow:
            continue
        try:
            result = run_backtest(close_df, _macd_config(fast, slow, signal, initial_cash), metadata=metadata)
            rows.append(
                {
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "status": "success",
                    "error_message": "",
                    **_metric_fields(result.metrics),
                }
            )
        except Exception as exc:
            rows.append(_failed_row(fast, slow, signal, exc))
    return rows


def run_macd_oos_item(
    close_df: pd.DataFrame,
    candidate: dict[str, Any],
    metadata: dict[str, Any],
    initial_cash: float,
) -> dict[str, Any]:
    fast = int(candidate["fast"])
    slow = int(candidate["slow"])
    signal = int(candidate["signal"])
    try:
        result = run_backtest(close_df, _macd_config(fast, slow, signal, initial_cash), metadata=metadata)
        return {
            "fast": fast,
            "slow": slow,
            "signal": signal,
            "train_sharpe": candidate.get("sharpe", ""),
            "status": "success",
            "error_message": "",
            **_metric_fields(result.metrics),
        }
    except Exception as exc:
        row = _failed_row(fast, slow, signal, exc)
        row["train_sharpe"] = candidate.get("sharpe", "")
        return row


def write_markdown_report(
    output_dir: Path,
    summary: dict[str, Any],
    sweep_rows: list[dict[str, Any]],
    oos_rows: list[dict[str, Any]],
    paths: dict[str, str],
    *,
    selected_symbols: list[str],
    train_start: str,
    train_end: str,
    test_start: str,
    test_end: str,
) -> str:
    lines = [
        "# 实验八：MACD 策略回测报告",
        "",
        "## 数据与口径",
        "",
        f"- 股票池：{', '.join(selected_symbols)}。",
        "- 策略规则：DIFF 上穿 DEA 买入；DIFF 下穿 DEA 卖出；每日收盘后生成信号，下一交易日按收盘价代理成交。",
        "- 默认参数：fast=12、slow=26、signal=9。",
        "- Benchmark：同股票池等权买入持有。",
        f"- 参数扫描训练区间：{train_start} 至 {train_end}；样本外区间：{test_start} 至 {test_end}。",
        "",
        "## 默认回测结果",
        "",
        _markdown_table(
            [summary],
            [
                "run_id",
                "title",
                "fast",
                "slow",
                "signal",
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
        "## 参数扫描 Top 10（训练集）",
        "",
        _markdown_table(
            _top_rows(sweep_rows, "sharpe", 10),
            ["fast", "slow", "signal", "total_return", "annual_return", "max_drawdown", "sharpe", "turnover"],
        ),
        "",
        "## 样本外测试（训练集 Top 参数）",
        "",
        _markdown_table(
            oos_rows,
            [
                "fast",
                "slow",
                "signal",
                "train_sharpe",
                "status",
                "error_message",
                "total_return",
                "annual_return",
                "max_drawdown",
                "sharpe",
                "turnover",
            ],
        ),
        "",
        "## 输出文件",
        "",
        f"- 汇总表：`{paths['summary']}`",
        f"- 训练集参数扫描：`{paths['sweep']}`",
        f"- 样本外候选结果：`{paths['oos']}`",
        f"- 图表目录：`{output_dir / 'charts'}`",
        "",
    ]
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _macd_config(fast: int, slow: int, signal: int, initial_cash: float) -> BacktestConfig:
    return BacktestConfig(
        lookback_days=slow + signal,
        rebalance_freq=1,
        top_fraction=1.0,
        strategy_name="macd",
        strategy_params={"fast": fast, "slow": slow, "signal": signal, "top_fraction": 1.0},
        portfolio_config=PortfolioConfig(initial_cash=initial_cash),
    )


def _summary_row(
    run_id: str,
    title: str,
    close_df: pd.DataFrame,
    metrics: dict[str, Any],
    benchmark_metrics: dict[str, Any],
    fast: int,
    slow: int,
    signal: int,
    schedule_count: int,
    equity_path: str,
    benchmark_path: str,
    trades_path: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "title": title,
        "benchmark_name": "equal_weight_buy_hold_same_universe",
        "strategy_name": "macd",
        "symbols": len(close_df.columns),
        "trade_days": len(close_df.index),
        "schedule_count": schedule_count,
        "fast": fast,
        "slow": slow,
        "signal": signal,
        **_metric_fields(metrics),
        "benchmark_total_return": benchmark_metrics["total_return"],
        "benchmark_annual_return": benchmark_metrics["annual_return"],
        "benchmark_max_drawdown": benchmark_metrics["max_drawdown"],
        "benchmark_sharpe": benchmark_metrics["sharpe"],
        "excess_return": metrics["total_return"] - benchmark_metrics["total_return"],
        "equity_curve_path": equity_path,
        "benchmark_equity_curve_path": benchmark_path,
        "trades_path": trades_path,
    }


def _metric_fields(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_return": metrics["total_return"],
        "annual_return": metrics["annual_return"],
        "max_drawdown": metrics["max_drawdown"],
        "sharpe": metrics["sharpe"],
        "turnover": metrics["turnover"],
        "final_value": metrics["final_value"],
    }


def _failed_row(fast: int, slow: int, signal: int, exc: Exception) -> dict[str, Any]:
    return {
        "fast": fast,
        "slow": slow,
        "signal": signal,
        "status": "failed",
        "error_message": f"{type(exc).__name__}: {exc}",
        "total_return": "",
        "annual_return": "",
        "max_drawdown": "",
        "sharpe": "",
        "turnover": "",
        "final_value": "",
    }


def _top_rows(rows: list[dict[str, Any]], metric: str, limit: int) -> list[dict[str, Any]]:
    success = [row for row in rows if row.get("status") == "success" and row.get(metric) not in ("", None)]
    return sorted(success, key=lambda row: float(row[metric]), reverse=True)[:limit]


def _markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    header = "| " + " | ".join(_format_header(field) for field in fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(_format_value(row.get(field, ""), field) for field in fields) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def _format_header(field: str) -> str:
    if field in PERCENT_FIELDS:
        return f"{field}(%)"
    return field


def _format_value(value: Any, field: str) -> str:
    if value in ("", None):
        return ""
    if field in PERCENT_FIELDS:
        try:
            return f"{float(value) * 100:.2f}%"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


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
        raise ValueError(f"MACD 股票池缺少本地行情: {missing}")
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


def _resolve_date_range(data_dir: Path, start_date: str | None, end_date: str | None) -> tuple[str, str]:
    calendar = pd.read_parquet(data_dir / "trade_calendar.parquet")
    dates = pd.to_datetime(calendar["trade_date"], errors="coerce").dropna().sort_values()
    start = start_date or dates.iloc[0].date().isoformat()
    end = end_date or dates.iloc[-1].date().isoformat()
    return start, end


if __name__ == "__main__":
    main()
