"""实验十：样本外测试与过拟合风险排序。"""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.diagnostics import LOGGER_NAME
from engine.experiment_report_helpers import (
    format_value as _shared_format_value,
    markdown_table as _shared_markdown_table,
    resolve_date_range as _resolve_date_range,
)
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv
from experiments.run_experiment_06_07 import SIMPLIFIED_SYMBOLS, _select_available_symbols, load_experiment_backtest_data
from experiments.run_experiment_09 import build_scan_tasks, run_queue_scan
from market_data.benchmarks import BenchmarkPolicy, BenchmarkResult, resolve_hs300_benchmark


PERCENT_FIELDS = {
    "in_sample_annual_return",
    "out_sample_annual_return",
    "decay",
    "in_sample_total_return",
    "out_sample_total_return",
    "in_sample_max_drawdown",
    "out_sample_max_drawdown",
}


def main() -> None:
    args = parse_args()
    diagnostics_logger = logging.getLogger(LOGGER_NAME)
    previous_disabled = diagnostics_logger.disabled
    if not args.verbose:
        diagnostics_logger.disabled = True
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    loaded, data_start, data_end = load_experiment_backtest_data(args, None, None)
    selected_symbols = _select_available_symbols(loaded.close_df, SIMPLIFIED_SYMBOLS)
    close_df = loaded.close_df[selected_symbols]
    train_close = _slice_close(close_df, args.train_start, args.train_end)
    test_close = _slice_close(close_df, args.test_start, args.test_end)
    if train_close.empty or test_close.empty:
        raise ValueError("训练期或样本外测试期为空，请检查本地数据覆盖范围")

    metadata = {
        **loaded.metadata,
        "data_source_mode": "market_data_readonly" if args.market_data_lake_root else str(args.input_mode).replace("-", "_"),
        "market_data_root": args.market_data_lake_root,
        "initial_cash": args.initial_cash,
        "requested_train_start": args.train_start,
        "requested_train_end": args.train_end,
        "requested_test_start": args.test_start,
        "requested_test_end": args.test_end,
    }
    metadata = apply_benchmark_metadata_experiment_10(
        resolve_benchmark_for_experiment(
            lake_root=args.market_data_lake_root,
            start_date=data_start,
            end_date=data_end,
            benchmark_kind=args.benchmark_kind,
            required=args.require_benchmark,
            allow_warn=args.allow_benchmark_warn,
            benchmark_path=args.benchmark_path,
        ),
        metadata,
    )

    tasks = build_scan_tasks(args.initial_cash)
    train_rows = run_queue_scan(train_close, metadata, tasks)
    selected_rows = run_out_of_sample(train_close, test_close, metadata, tasks, train_rows)
    ranked_rows = rank_overfit_risk(selected_rows)

    train_path = write_rows_csv(train_rows, output_dir / "in_sample_scan_all.csv", list(train_rows[0]))
    selected_path = write_rows_csv(ranked_rows, output_dir / "out_of_sample_comparison.csv", list(ranked_rows[0]))
    ranking_path = write_rows_csv(
        [
            {
                "risk_rank": row["risk_rank"],
                "strategy_name": row["strategy_name"],
                "decay": row["decay"],
                "overfit_risk": row["overfit_risk"],
            }
            for row in ranked_rows
        ],
        output_dir / "overfit_risk_ranking.csv",
        ["risk_rank", "strategy_name", "decay", "overfit_risk"],
    )
    report_path = write_markdown_report(
        output_dir,
        ranked_rows,
        {
            "train": train_path,
            "comparison": selected_path,
            "ranking": ranking_path,
        },
        actual_train_start=str(train_close.index[0]),
        actual_train_end=str(train_close.index[-1]),
        actual_test_start=str(test_close.index[0]),
        actual_test_end=str(test_close.index[-1]),
        requested_train_start=args.train_start,
        requested_train_end=args.train_end,
        requested_test_start=args.test_start,
        requested_test_end=args.test_end,
        data_start=data_start,
        data_end=data_end,
        selected_symbols=selected_symbols,
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十样本外测试。")
    parser.add_argument("--input-mode", choices=["canonical-gold", "legacy-flat"], default="canonical-gold")
    parser.add_argument("--data-dir", default=None, help="仅在 --input-mode legacy-flat 时显式传入的外置兼容目录。")
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_10")))
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--train-start", default="2015-01-01")
    parser.add_argument("--train-end", default="2020-12-31")
    parser.add_argument("--test-start", default="2021-01-01")
    parser.add_argument("--test-end", default="2025-12-31")
    parser.add_argument("--market-data-root", "--market-data-lake-root", dest="market_data_lake_root", default=None, help="显式启用 market_data 只读 reader / benchmark resolver。")
    parser.add_argument("--benchmark-path", default=None, help="显式本地 hs300_index benchmark fixture 路径；只读读取。")
    parser.add_argument("--benchmark-kind", default="policy_unconfirmed", choices=["price_index", "total_return_index", "adjusted_index", "policy_unconfirmed"])
    parser.add_argument("--require-benchmark", action="store_true", help="缺少 hs300_index 时返回 required_missing metadata。")
    parser.add_argument("--allow-benchmark-unavailable", action="store_true", help="兼容参数；默认缺基准写入 unavailable metadata 并继续，--require-benchmark 返回 required_missing。")
    parser.add_argument("--allow-benchmark-warn", action="store_true", help="允许 quality warn 的 hs300_index 进入 benchmark metadata。")
    parser.add_argument("--verbose", action="store_true", help="输出结构化诊断日志。")
    return parser.parse_args()


def resolve_benchmark_for_experiment(
    *,
    lake_root: str | None,
    start_date: str,
    end_date: str,
    benchmark_kind: str = "policy_unconfirmed",
    required: bool = False,
    allow_warn: bool = False,
    benchmark_path: str | None = None,
) -> BenchmarkResult | None:
    if not lake_root and not benchmark_path and not required:
        return None
    policy = BenchmarkPolicy.from_config(
        {
            "benchmark_kind": benchmark_kind,
            "confirmed": benchmark_kind != "policy_unconfirmed" or bool(benchmark_path),
            "required": required,
            "allow_warn": allow_warn,
        },
        required=required,
    )
    return resolve_hs300_benchmark(
        lake_root=lake_root,
        start_date=start_date,
        end_date=end_date,
        policy=policy,
        benchmark_path=benchmark_path,
    )


def apply_benchmark_metadata_experiment_10(
    result: BenchmarkResult | None,
    existing_metadata: dict[str, Any],
) -> dict[str, Any]:
    metadata = dict(existing_metadata)
    if result is None:
        return metadata
    result_metadata = result.to_metadata()
    metadata["benchmark_result"] = result_metadata
    metadata["benchmark_status"] = result.status
    metadata["benchmark_source"] = result_metadata.get("benchmark_source")
    metadata["benchmark_path"] = result_metadata.get("benchmark_path")
    metadata["benchmark_missing_reason"] = result.missing_reason
    metadata["benchmark_unavailable_reason"] = result.missing_reason
    metadata["hs300_benchmark_dataset"] = result.dataset
    metadata["hs300_benchmark_is_proxy"] = False
    if result.available:
        metadata["benchmark_dataset"] = result.dataset
        metadata["benchmark_kind"] = "hs300"
        metadata["hs300_index"] = result_metadata
        metadata["benchmark_relative_return_enabled"] = True
    else:
        metadata["benchmark_dataset"] = "proxy_baseline"
        metadata["benchmark_kind"] = "proxy_baseline"
        metadata.pop("hs300_index", None)
        metadata["benchmark_relative_return_enabled"] = False
    return metadata


def run_out_of_sample(
    train_close: pd.DataFrame,
    test_close: pd.DataFrame,
    metadata: dict[str, Any],
    tasks: list[dict[str, Any]],
    train_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy_name in ("momentum", "rsi", "macd"):
        train_strategy_rows = [
            row
            for row in train_rows
            if row["strategy_name"] == strategy_name
            and row["status"] == "success"
            and row["annual_return"] not in ("", None)
        ]
        if not train_strategy_rows:
            raise ValueError(f"{strategy_name} 样本内没有成功参数组合")
        best_train = sorted(
            train_strategy_rows,
            key=lambda row: (float(row["annual_return"]), float(row["sharpe"] or -999), float(row["total_return"])),
            reverse=True,
        )[0]
        task = find_task_for_row(tasks, best_train)
        test_row = run_queue_scan(test_close, metadata, [task])[0]
        rows.append(build_comparison_row(strategy_name, best_train, test_row, train_close, test_close))
    return rows


def find_task_for_row(tasks: list[dict[str, Any]], row: dict[str, Any]) -> dict[str, Any]:
    for task in tasks:
        if task["strategy_name"] != row["strategy_name"]:
            continue
        if task["strategy_name"] == "momentum" and int(task["lookback"]) == int(row["lookback"]) and int(task["rebalance_freq"]) == int(row["rebalance_freq"]):
            return task
        if task["strategy_name"] == "rsi" and int(task["period"]) == int(row["period"]) and int(task["oversold"]) == int(row["oversold"]) and int(task["overbought"]) == int(row["overbought"]):
            return task
        if task["strategy_name"] == "macd" and int(task["fast"]) == int(row["fast"]) and int(task["slow"]) == int(row["slow"]) and int(task["signal"]) == int(row["signal"]):
            return task
    raise ValueError(f"未找到参数对应任务: {row}")


def build_comparison_row(
    strategy_name: str,
    train_row: dict[str, Any],
    test_row: dict[str, Any],
    train_close: pd.DataFrame,
    test_close: pd.DataFrame,
) -> dict[str, Any]:
    in_annual = float(train_row["annual_return"])
    out_annual = float(test_row["annual_return"])
    params = format_params(train_row)
    return {
        "strategy_name": strategy_name,
        "best_params": params,
        "train_start": train_close.index[0],
        "train_end": train_close.index[-1],
        "test_start": test_close.index[0],
        "test_end": test_close.index[-1],
        "in_sample_annual_return": in_annual,
        "out_sample_annual_return": out_annual,
        "decay": in_annual - out_annual,
        "in_sample_total_return": train_row["total_return"],
        "out_sample_total_return": test_row["total_return"],
        "in_sample_sharpe": train_row["sharpe"],
        "out_sample_sharpe": test_row["sharpe"],
        "in_sample_max_drawdown": train_row["max_drawdown"],
        "out_sample_max_drawdown": test_row["max_drawdown"],
        "overfit_risk": "",
        "risk_rank": "",
    }


def rank_overfit_risk(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(rows, key=lambda row: float(row["decay"]), reverse=True)
    labels = ["高", "中", "低"]
    for index, row in enumerate(ranked, start=1):
        row["risk_rank"] = index
        row["overfit_risk"] = labels[index - 1] if index <= len(labels) else "低"
    return ranked


def format_params(row: dict[str, Any]) -> str:
    if row["strategy_name"] == "momentum":
        return f"lookback={row['lookback']}, rebalance_freq={row['rebalance_freq']}"
    if row["strategy_name"] == "rsi":
        return f"period={row['period']}, oversold={row['oversold']}, overbought={row['overbought']}"
    return f"fast={row['fast']}, slow={row['slow']}, signal={row['signal']}"


def write_markdown_report(
    output_dir: Path,
    rows: list[dict[str, Any]],
    paths: dict[str, str],
    *,
    actual_train_start: str,
    actual_train_end: str,
    actual_test_start: str,
    actual_test_end: str,
    requested_train_start: str,
    requested_train_end: str,
    requested_test_start: str,
    requested_test_end: str,
    data_start: str,
    data_end: str,
    selected_symbols: list[str],
) -> str:
    lines = [
        "# 实验十：样本外测试报告",
        "",
        "## 数据与口径",
        "",
        f"- 股票池：{', '.join(selected_symbols)}。",
        f"- 请求训练期：{requested_train_start} 至 {requested_train_end}；实际训练期：{actual_train_start} 至 {actual_train_end}。",
        f"- 请求样本外：{requested_test_start} 至 {requested_test_end}；实际样本外：{actual_test_start} 至 {actual_test_end}。",
        f"- 当前本地数据覆盖 {data_start} 至 {data_end}；本报告按可用数据裁剪后执行。",
        "- 每个策略在样本内参数扫描中按年化收益最高选择最优参数，样本外使用同一参数回测。",
        "- 衰减量 = 样本内年化收益 - 样本外年化收益；衰减量越大，过拟合风险越高。",
        "",
        "## 样本外测试对比表",
        "",
        _markdown_table(
            rows,
            [
                "strategy_name",
                "best_params",
                "in_sample_annual_return",
                "out_sample_annual_return",
                "decay",
                "overfit_risk",
            ],
        ),
        "",
        "## 过拟合风险排序",
        "",
        _markdown_table(rows, ["risk_rank", "strategy_name", "decay", "overfit_risk"]),
        "",
        "## 详细指标",
        "",
        _markdown_table(
            rows,
            [
                "strategy_name",
                "in_sample_total_return",
                "out_sample_total_return",
                "in_sample_sharpe",
                "out_sample_sharpe",
                "in_sample_max_drawdown",
                "out_sample_max_drawdown",
            ],
        ),
        "",
        "## 输出文件",
        "",
        f"- 样本内全量扫描：`{paths['train']}`",
        f"- 样本外对比表：`{paths['comparison']}`",
        f"- 过拟合风险排序：`{paths['ranking']}`",
        "",
    ]
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _slice_close(close_df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_date = _to_date(start)
    end_date = _to_date(end)
    return close_df[(pd.Index(close_df.index) >= start_date) & (pd.Index(close_df.index) <= end_date)]


def _markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    return _shared_markdown_table(rows, fields, percent_fields=PERCENT_FIELDS)


def _format_value(value: Any, field: str) -> str:
    return _shared_format_value(value, field, percent_fields=PERCENT_FIELDS)


def _to_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


if __name__ == "__main__":
    main()
