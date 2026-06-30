"""实验九：三类策略参数敏感性分析。"""

from __future__ import annotations

import argparse
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
from engine.diagnostics import LOGGER_NAME
from engine.experiment_report_helpers import (
    format_value as _shared_format_value,
    markdown_table as _shared_markdown_table,
    resolve_date_range as _resolve_date_range,
)
from engine.portfolio import PortfolioConfig
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv
from experiments.run_experiment_06_07 import (
    SIMPLIFIED_SYMBOLS,
    _select_available_symbols,
    add_market_data_input_args,
    load_experiment_backtest_data,
)


PERCENT_FIELDS = {
    "annual_return",
    "max_drawdown",
    "total_return",
    "turnover",
    "win_rate",
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

    sanity_rows = run_sanity_checks(close_df, metadata, args.initial_cash)
    if not all(row["status"] == "pass" for row in sanity_rows):
        write_rows_csv(sanity_rows, output_dir / "sanity_check.csv", list(sanity_rows[0]))
        raise RuntimeError("sanity check 未通过：存在参数组收益完全相同，已停止参数扫描")

    tasks = build_scan_tasks(args.initial_cash)
    scan_rows = run_queue_scan(close_df, metadata, tasks)
    by_strategy = {
        strategy: [row for row in scan_rows if row["strategy_name"] == strategy]
        for strategy in ("momentum", "rsi", "macd")
    }

    sanity_path = write_rows_csv(sanity_rows, output_dir / "sanity_check.csv", list(sanity_rows[0]))
    all_path = write_rows_csv(scan_rows, output_dir / "parameter_sensitivity_all.csv", list(scan_rows[0]))
    momentum_path = write_rows_csv(by_strategy["momentum"], output_dir / "momentum_sensitivity.csv", list(scan_rows[0]))
    rsi_path = write_rows_csv(by_strategy["rsi"], output_dir / "rsi_sensitivity.csv", list(scan_rows[0]))
    macd_path = write_rows_csv(by_strategy["macd"], output_dir / "macd_sensitivity.csv", list(scan_rows[0]))
    report_path = write_markdown_report(
        output_dir,
        sanity_rows,
        by_strategy,
        {
            "sanity": sanity_path,
            "all": all_path,
            "momentum": momentum_path,
            "rsi": rsi_path,
            "macd": macd_path,
        },
        selected_symbols=selected_symbols,
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验九参数敏感性分析。")
    add_market_data_input_args(parser)
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_09")))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--verbose", action="store_true", help="输出结构化诊断日志。")
    return parser.parse_args()


def run_sanity_checks(close_df: pd.DataFrame, metadata: dict[str, Any], initial_cash: float) -> list[dict[str, Any]]:
    """用极端参数验证策略参数已真实注入并影响结果。"""

    pairs = [
        (
            "momentum",
            _momentum_config(5, 5, initial_cash),
            _momentum_config(60, 30, initial_cash),
            "lookback=5/rebalance=5 vs lookback=60/rebalance=30",
        ),
        (
            "rsi",
            _rsi_config(7, 35, 65, initial_cash),
            _rsi_config(28, 20, 80, initial_cash),
            "period=7/35-65 vs period=28/20-80",
        ),
        (
            "macd",
            _macd_config(6, 13, 5, initial_cash),
            _macd_config(24, 52, 15, initial_cash),
            "6/13/5 vs 24/52/15",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for strategy_name, left_cfg, right_cfg, description in pairs:
        left = run_backtest(close_df, left_cfg, metadata=metadata)
        right = run_backtest(close_df, right_cfg, metadata=metadata)
        left_return = float(left.metrics["total_return"])
        right_return = float(right.metrics["total_return"])
        delta = abs(left_return - right_return)
        rows.append(
            {
                "strategy_name": strategy_name,
                "description": description,
                "left_total_return": left_return,
                "right_total_return": right_return,
                "abs_delta": delta,
                "status": "pass" if delta > 1e-12 else "failed_same_return",
            }
        )
    return rows


def build_scan_tasks(initial_cash: float) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for lookback, rebalance_freq in product([5, 10, 20, 30, 60], [5, 10, 20, 30]):
        tasks.append(
            {
                "strategy_name": "momentum",
                "lookback": lookback,
                "rebalance_freq": rebalance_freq,
                "period": "",
                "oversold": "",
                "overbought": "",
                "fast": "",
                "slow": "",
                "signal": "",
                "config": _momentum_config(lookback, rebalance_freq, initial_cash),
            }
        )
    for period, thresholds in product([7, 14, 21, 28], [(20, 80), (25, 75), (30, 70), (35, 65)]):
        oversold, overbought = thresholds
        tasks.append(
            {
                "strategy_name": "rsi",
                "lookback": "",
                "rebalance_freq": 5,
                "period": period,
                "oversold": oversold,
                "overbought": overbought,
                "fast": "",
                "slow": "",
                "signal": "",
                "config": _rsi_config(period, oversold, overbought, initial_cash),
            }
        )
    for fast, slow, _base_signal in [(6, 13, 9), (12, 26, 9), (24, 52, 18)]:
        for signal in [5, 9, 15]:
            tasks.append(
                {
                    "strategy_name": "macd",
                    "lookback": "",
                    "rebalance_freq": 1,
                    "period": "",
                    "oversold": "",
                    "overbought": "",
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "config": _macd_config(fast, slow, signal, initial_cash),
                }
            )
    return tasks


def run_queue_scan(close_df: pd.DataFrame, metadata: dict[str, Any], tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """使用 running[:] 遍历副本 + while 循环的串行队列扫描。"""

    rows: list[dict[str, Any]] = []
    running = list(tasks)
    sequence = 0
    while running:
        for task in running[:]:
            sequence += 1
            row = run_scan_task(close_df, metadata, task, sequence)
            rows.append(row)
            running.remove(task)
    return rows


def run_scan_task(close_df: pd.DataFrame, metadata: dict[str, Any], task: dict[str, Any], sequence: int) -> dict[str, Any]:
    base = {
        "run_id": f"exp09-{sequence:03d}",
        "strategy_name": task["strategy_name"],
        "lookback": task["lookback"],
        "rebalance_freq": task["rebalance_freq"],
        "period": task["period"],
        "oversold": task["oversold"],
        "overbought": task["overbought"],
        "fast": task["fast"],
        "slow": task["slow"],
        "signal": task["signal"],
    }
    try:
        result = run_backtest(close_df, task["config"], metadata=metadata)
        daily_returns = pd.Series(
            [snapshot.total_value for snapshot in result.portfolio_result.daily_snapshots],
            index=[snapshot.trade_date for snapshot in result.portfolio_result.daily_snapshots],
            dtype="float64",
        ).pct_change().dropna()
        return {
            **base,
            "status": "success",
            "error_message": "",
            "total_return": result.metrics["total_return"],
            "annual_return": result.metrics["annual_return"],
            "sharpe": result.metrics["sharpe"],
            "max_drawdown": result.metrics["max_drawdown"],
            "win_rate": calculate_win_rate(daily_returns),
            "turnover": result.metrics["turnover"],
            "final_value": result.metrics["final_value"],
        }
    except Exception as exc:
        return {
            **base,
            "status": "failed",
            "error_message": f"{type(exc).__name__}: {exc}",
            "total_return": "",
            "annual_return": "",
            "sharpe": "",
            "max_drawdown": "",
            "win_rate": "",
            "turnover": "",
            "final_value": "",
        }


def calculate_win_rate(daily_returns: pd.Series) -> float | None:
    """日胜率：正收益交易日 / 非零收益交易日。"""

    active = daily_returns[daily_returns != 0]
    if active.empty:
        return None
    return float((active > 0).mean())


def write_markdown_report(
    output_dir: Path,
    sanity_rows: list[dict[str, Any]],
    by_strategy: dict[str, list[dict[str, Any]]],
    paths: dict[str, str],
    *,
    selected_symbols: list[str],
) -> str:
    lines = [
        "# 实验九：参数敏感性分析报告",
        "",
        "## 数据与口径",
        "",
        f"- 股票池：{', '.join(selected_symbols)}。",
        "- 扫描方式：使用 `running[:]` 遍历副本 + `while running` 的串行队列调参模式。",
        "- sanity check：每个策略先用两组极端参数回测；若累计收益完全相同则停止扫描。",
        "- 胜率口径：日胜率 = 正收益交易日 / 非零收益交易日。",
        "",
        "## Sanity Check",
        "",
        _markdown_table(
            sanity_rows,
            ["strategy_name", "description", "left_total_return", "right_total_return", "abs_delta", "status"],
        ),
        "",
    ]
    for strategy_name, title in (
        ("momentum", "动量参数敏感性 Top 10"),
        ("rsi", "RSI 参数敏感性 Top 10"),
        ("macd", "MACD 参数敏感性 Top 10"),
    ):
        rows = _top_rows(by_strategy[strategy_name], "sharpe", 10)
        fields = _strategy_fields(strategy_name)
        lines.extend(["## " + title, "", _markdown_table(rows, fields), ""])
    lines.extend(
        [
            "## 输出文件",
            "",
            f"- sanity check 记录：`{paths['sanity']}`",
            f"- 全量扫描结果：`{paths['all']}`",
            f"- 动量扫描结果：`{paths['momentum']}`",
            f"- RSI 扫描结果：`{paths['rsi']}`",
            f"- MACD 扫描结果：`{paths['macd']}`",
            "",
        ]
    )
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _strategy_fields(strategy_name: str) -> list[str]:
    common = ["annual_return", "sharpe", "max_drawdown", "win_rate", "total_return", "turnover"]
    if strategy_name == "momentum":
        return ["lookback", "rebalance_freq", *common]
    if strategy_name == "rsi":
        return ["period", "oversold", "overbought", *common]
    return ["fast", "slow", "signal", *common]


def _momentum_config(lookback: int, rebalance_freq: int, initial_cash: float) -> BacktestConfig:
    return BacktestConfig(
        lookback_days=lookback,
        rebalance_freq=rebalance_freq,
        top_fraction=0.10,
        strategy_name="momentum",
        strategy_params={"sell_buffer": 2.0},
        portfolio_config=PortfolioConfig(initial_cash=initial_cash),
    )


def _rsi_config(period: int, oversold: int, overbought: int, initial_cash: float) -> BacktestConfig:
    return BacktestConfig(
        lookback_days=period,
        rebalance_freq=5,
        top_fraction=1.0,
        strategy_name="rsi",
        strategy_params={"period": period, "oversold": oversold, "overbought": overbought, "top_fraction": 1.0},
        portfolio_config=PortfolioConfig(initial_cash=initial_cash),
    )


def _macd_config(fast: int, slow: int, signal: int, initial_cash: float) -> BacktestConfig:
    return BacktestConfig(
        lookback_days=slow + signal,
        rebalance_freq=1,
        top_fraction=1.0,
        strategy_name="macd",
        strategy_params={"fast": fast, "slow": slow, "signal": signal, "top_fraction": 1.0},
        portfolio_config=PortfolioConfig(initial_cash=initial_cash),
    )


def _top_rows(rows: list[dict[str, Any]], metric: str, limit: int) -> list[dict[str, Any]]:
    success = [row for row in rows if row.get("status") == "success" and row.get(metric) not in ("", None)]
    return sorted(success, key=lambda row: float(row[metric]), reverse=True)[:limit]


def _markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    return _shared_markdown_table(rows, fields, percent_fields=PERCENT_FIELDS)


def _format_value(value: Any, field: str) -> str:
    return _shared_format_value(value, field, percent_fields=PERCENT_FIELDS)


if __name__ == "__main__":
    main()
