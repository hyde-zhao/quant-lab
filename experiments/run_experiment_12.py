"""实验十二：市场环境分段测试。"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.backtest import BacktestConfig, run_backtest
from engine.diagnostics import LOGGER_NAME
from engine.portfolio import PortfolioConfig
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv
from experiments.run_experiment_06_07 import SIMPLIFIED_SYMBOLS, _select_available_symbols, load_experiment_backtest_data
from market_data.benchmarks import BenchmarkPolicy, BenchmarkResult, resolve_hs300_benchmark


PERCENT_FIELDS = {
    "momentum_total_return",
    "rsi_total_return",
    "macd_total_return",
    "total_return",
    "annual_return",
    "max_drawdown",
    "turnover",
}


@dataclass(frozen=True, slots=True)
class MarketSegment:
    segment_id: str
    label: str
    market_state: str
    hs300_note: str
    reason: str
    start_date: str
    end_date: str


SEGMENTS = [
    MarketSegment("bull_2015_h1", "牛市 2015H1", "牛市", "+100%+", "A 股大水牛", "2015-01-01", "2015-06-30"),
    MarketSegment("bear_2015_h2", "熊市 2015H2", "熊市", "-45%", "股灾 1.0/2.0/3.0", "2015-06-01", "2016-01-31"),
    MarketSegment("slow_bull_2016_2018", "慢牛 2016-2018", "慢牛", "+50%", "白马蓝筹行情", "2016-02-01", "2018-01-31"),
    MarketSegment("bear_2018", "熊市 2018", "熊市", "-30%", "去杠杆 + 贸易战", "2018-01-01", "2019-01-31"),
    MarketSegment("range_bull_2019", "震荡偏牛 2019", "震荡偏牛", "+20%", "结构性行情", "2019-01-01", "2020-01-31"),
    MarketSegment("crash_2020_q1", "急跌 2020Q1", "急跌", "-15%", "疫情冲击", "2020-01-01", "2020-03-31"),
]


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
    metadata = {
        **loaded.metadata,
        "data_source_mode": "market_data_readonly" if args.market_data_lake_root else str(args.input_mode).replace("-", "_"),
        "market_data_root": args.market_data_lake_root,
        "initial_cash": args.initial_cash,
    }
    metadata = apply_benchmark_metadata_experiment_12(
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

    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for segment in SEGMENTS:
        segment_close = _slice_close(close_df, segment.start_date, segment.end_date)
        segment_details = run_segment(segment, segment_close, metadata, args.initial_cash)
        detail_rows.extend(segment_details)
        summary_rows.append(build_summary_row(segment, segment_close, segment_details))

    summary_path = write_rows_csv(summary_rows, output_dir / "segment_summary.csv", list(summary_rows[0]))
    detail_path = write_rows_csv(detail_rows, output_dir / "segment_strategy_detail.csv", list(detail_rows[0]))
    report_path = write_markdown_report(
        output_dir,
        summary_rows,
        detail_rows,
        {"summary": summary_path, "detail": detail_path},
        data_start=data_start,
        data_end=data_end,
        selected_symbols=selected_symbols,
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十二市场环境分段测试。")
    parser.add_argument("--input-mode", choices=["canonical-gold", "legacy-flat"], default="canonical-gold")
    parser.add_argument("--data-dir", default=None, help="仅在 --input-mode legacy-flat 时显式传入的外置兼容目录。")
    parser.add_argument("--quality-report", default=str(research_report_path("data_quality_report.csv")))
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_12")))
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
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


def apply_benchmark_metadata_experiment_12(
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
        metadata["hs300_relative_return_enabled"] = True
    else:
        metadata["benchmark_dataset"] = "proxy_baseline"
        metadata["benchmark_kind"] = "proxy_baseline"
        metadata.pop("hs300_index", None)
        metadata["hs300_relative_return_enabled"] = False
        metadata.setdefault("proxy_baseline", None)
    return metadata


def run_segment(
    segment: MarketSegment,
    close_df: pd.DataFrame,
    metadata: dict[str, Any],
    initial_cash: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for strategy_name, config in default_strategy_configs(initial_cash).items():
        base = {
            "segment_id": segment.segment_id,
            "label": segment.label,
            "market_state": segment.market_state,
            "requested_start": segment.start_date,
            "requested_end": segment.end_date,
            "actual_start": "" if close_df.empty else close_df.index[0],
            "actual_end": "" if close_df.empty else close_df.index[-1],
            "trade_days": len(close_df),
            "strategy_name": strategy_name,
        }
        if close_df.empty:
            rows.append(
                {
                    **base,
                    "status": "skipped_no_local_data",
                    "error_message": "本地数据不覆盖该分段",
                    "total_return": "",
                    "annual_return": "",
                    "max_drawdown": "",
                    "sharpe": "",
                    "turnover": "",
                    "final_value": "",
                }
            )
            continue
        try:
            result = run_backtest(close_df, config, metadata=metadata)
            rows.append(
                {
                    **base,
                    "status": "success",
                    "error_message": "",
                    "total_return": result.metrics["total_return"],
                    "annual_return": result.metrics["annual_return"],
                    "max_drawdown": result.metrics["max_drawdown"],
                    "sharpe": result.metrics["sharpe"],
                    "turnover": result.metrics["turnover"],
                    "final_value": result.metrics["final_value"],
                }
            )
        except Exception as exc:
            rows.append(
                {
                    **base,
                    "status": "failed",
                    "error_message": f"{type(exc).__name__}: {exc}",
                    "total_return": "",
                    "annual_return": "",
                    "max_drawdown": "",
                    "sharpe": "",
                    "turnover": "",
                    "final_value": "",
                }
            )
    return rows


def build_summary_row(segment: MarketSegment, close_df: pd.DataFrame, detail_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_strategy = {row["strategy_name"]: row for row in detail_rows}
    success_rows = [row for row in detail_rows if row["status"] == "success" and row["total_return"] not in ("", None)]
    best = max(success_rows, key=lambda row: float(row["total_return"]))["strategy_name"] if success_rows else ""
    if len(success_rows) == 3:
        status = "success"
        note = ""
    elif success_rows:
        status = "partial"
        failed = [row["strategy_name"] for row in detail_rows if row["status"] != "success"]
        note = "部分策略未完成回测: " + ", ".join(failed)
    elif close_df.empty:
        status = "skipped_no_local_data"
        note = "本地数据不足或分段过短，无法完成三策略回测"
    else:
        status = "failed"
        note = "本地数据不足或分段过短，无法完成三策略回测"
    return {
        "segment_id": segment.segment_id,
        "label": segment.label,
        "market_state": segment.market_state,
        "requested_start": segment.start_date,
        "requested_end": segment.end_date,
        "actual_start": "" if close_df.empty else close_df.index[0],
        "actual_end": "" if close_df.empty else close_df.index[-1],
        "trade_days": len(close_df),
        "momentum_total_return": by_strategy["momentum"]["total_return"],
        "rsi_total_return": by_strategy["rsi"]["total_return"],
        "macd_total_return": by_strategy["macd"]["total_return"],
        "best_strategy": best,
        "status": status,
        "note": note,
    }


def default_strategy_configs(initial_cash: float) -> dict[str, BacktestConfig]:
    return {
        "momentum": BacktestConfig(
            lookback_days=20,
            rebalance_freq=20,
            top_fraction=0.10,
            strategy_name="momentum",
            strategy_params={"sell_buffer": 2.0},
            portfolio_config=PortfolioConfig(initial_cash=initial_cash),
        ),
        "rsi": BacktestConfig(
            lookback_days=14,
            rebalance_freq=5,
            top_fraction=1.0,
            strategy_name="rsi",
            strategy_params={"period": 14, "oversold": 30, "overbought": 70, "top_fraction": 1.0},
            portfolio_config=PortfolioConfig(initial_cash=initial_cash),
        ),
        "macd": BacktestConfig(
            lookback_days=35,
            rebalance_freq=1,
            top_fraction=1.0,
            strategy_name="macd",
            strategy_params={"fast": 12, "slow": 26, "signal": 9, "top_fraction": 1.0},
            portfolio_config=PortfolioConfig(initial_cash=initial_cash),
        ),
    }


def write_markdown_report(
    output_dir: Path,
    summary_rows: list[dict[str, Any]],
    detail_rows: list[dict[str, Any]],
    paths: dict[str, str],
    *,
    data_start: str,
    data_end: str,
    selected_symbols: list[str],
) -> str:
    comparable = [row for row in summary_rows if row["status"] == "success"]
    lines = [
        "# 实验十二：市场环境分段测试报告",
        "",
        "## 数据与限制",
        "",
        f"- 本地数据覆盖：{data_start} 至 {data_end}。",
        f"- 股票池：{', '.join(selected_symbols)}。",
        "- 手动市场环境分段按题目给定区间执行；本地数据不覆盖 2015-2019，因此对应分段只记录为 skipped。",
        "- 分段内直接使用三策略默认参数回测：动量 20/20/10%，RSI 14/30/70，MACD 12/26/9。",
        "- 当前没有沪深300指数行情文件，市场状态标签来自题目给定，不由本地指数收益自动识别。",
        "",
        "## 分段对比表",
        "",
        _markdown_table(
            summary_rows,
            [
                "label",
                "market_state",
                "actual_start",
                "actual_end",
                "trade_days",
                "momentum_total_return",
                "rsi_total_return",
                "macd_total_return",
                "best_strategy",
                "status",
            ],
        ),
        "",
        "## 可验证结论",
        "",
    ]
    if comparable:
        lines.extend(build_conclusion_lines(comparable, detail_rows))
    else:
        lines.append("- 当前本地数据没有覆盖任何可三策略完整比较的手动分段，无法验证策略-市场环境假设。")
    partial = [row for row in summary_rows if row["status"] == "partial"]
    for row in partial:
        lines.append(f"- {row['label']} 只有部分策略完成，不能作为三策略横向比较依据；原因：{row['note']}。")
    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            f"- 分段汇总：`{paths['summary']}`",
            f"- 策略明细：`{paths['detail']}`",
            "",
        ]
    )
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def build_conclusion_lines(available_summary_rows: list[dict[str, Any]], detail_rows: list[dict[str, Any]]) -> list[str]:
    lines = []
    for row in available_summary_rows:
        best = row["best_strategy"]
        lines.append(
            f"- {row['label']}（{row['market_state']}）可回测，最优策略为 `{best}`，"
            f"收益：动量 {_format_value(row['momentum_total_return'], 'momentum_total_return')}、"
            f"RSI {_format_value(row['rsi_total_return'], 'rsi_total_return')}、"
            f"MACD {_format_value(row['macd_total_return'], 'macd_total_return')}。"
        )
    market_states = {row["market_state"] for row in available_summary_rows}
    if len(market_states) < 2:
        lines.append("- 可验证市场环境少于 2 类，不能据此确认“动量适合趋势市、RSI 适合震荡市”的总体假设。")
    return lines


def _slice_close(close_df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_date = _to_date(start)
    end_date = _to_date(end)
    return close_df[(pd.Index(close_df.index) >= start_date) & (pd.Index(close_df.index) <= end_date)]


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


def _resolve_date_range(data_dir: Path) -> tuple[str, str]:
    calendar = pd.read_parquet(data_dir / "trade_calendar.parquet")
    dates = pd.to_datetime(calendar["trade_date"], errors="coerce").dropna().sort_values()
    return dates.iloc[0].date().isoformat(), dates.iloc[-1].date().isoformat()


def _to_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


if __name__ == "__main__":
    main()
