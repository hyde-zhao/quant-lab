"""实验十三：三策略横向对比。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.backtest import BacktestConfig, BacktestResult, run_backtest
from engine.diagnostics import LOGGER_NAME
from engine.experiment_report_helpers import resolve_date_range as _resolve_date_range
from engine.portfolio import PortfolioConfig
from engine.research_paths import research_report_path
from engine.reporting import write_rows_csv
from experiments.run_experiment_06_07 import (
    SIMPLIFIED_SYMBOLS,
    _select_available_symbols,
    add_market_data_input_args,
    build_equal_weight_benchmark,
    calculate_series_metrics,
    load_experiment_backtest_data,
)
from experiments.run_experiment_09 import calculate_win_rate
from experiments.run_experiment_12 import default_strategy_configs
from market_data.benchmarks import (
    BenchmarkCoverage,
    BenchmarkPolicy,
    BenchmarkResult,
    build_benchmark_field_payload,
    build_hs300_remediation_spec,
    build_next_action,
    resolve_hs300_benchmark,
)


PROXY_BASELINE_COLUMN = "proxy_baseline"
HS300_BENCHMARK_COLUMN = "hs300_index"

PERCENT_FIELDS = {
    PROXY_BASELINE_COLUMN,
    HS300_BENCHMARK_COLUMN,
    "动量",
    "RSI",
    "MACD",
}

PERCENT_DIMENSIONS = {
    "年化收益率",
    "proxy_excess_annual_return",
    "hs300_excess_annual_return",
    "最大回撤",
    "胜率",
    "样本内外衰减量",
    "含成本后年化收益",
    "成本侵蚀幅度",
}


class BenchmarkUnavailableError(RuntimeError):
    """真实 benchmark 被要求但不可用时的受控失败。"""

STRATEGY_LABELS = {
    "momentum": "动量",
    "rsi": "RSI",
    "macd": "MACD",
}

SUITABLE_MARKET = {
    "momentum": "趋势市",
    "rsi": "震荡市",
    "macd": "趋势确认",
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

    benchmark_result = resolve_benchmark_for_experiment_13(
        lake_root=args.market_data_lake_root,
        start_date=start_date,
        end_date=end_date,
        benchmark_kind=args.benchmark_kind,
        required=args.require_benchmark,
        allow_warn=args.allow_benchmark_warn,
        price_trade_dates=[str(item) for item in close_df.index],
    )
    benchmark_payload = build_experiment_13_benchmark(
        close_df,
        args.initial_cash,
        benchmark_result,
        require_benchmark=args.require_benchmark,
    )
    benchmark = benchmark_payload["benchmark"]
    benchmark_field_payload = benchmark_payload["field_payload"]
    metadata = apply_benchmark_metadata_experiment_13(
        benchmark_result,
        metadata,
        field_payload=benchmark_field_payload,
    )
    strategy_rows, diagnostics_rows = run_strategy_comparisons(close_df, metadata, args.initial_cash)
    decay_by_strategy = load_decay_by_strategy(Path(args.experiment_10_comparison))
    market_rows = load_market_segment_rows(Path(args.experiment_12_summary))

    comparison_rows = build_comparison_table(
        benchmark["metrics"],
        strategy_rows,
        decay_by_strategy,
        benchmark_column=str(benchmark_payload["comparison_column"]),
        excess_dimension=str(benchmark_payload["excess_dimension"]),
    )
    comparison_path = write_rows_csv(comparison_rows, output_dir / "cross_strategy_comparison.csv", list(comparison_rows[0]))
    diagnostics_path = write_rows_csv(diagnostics_rows, output_dir / "strategy_diagnostics.csv", list(diagnostics_rows[0]))
    benchmark_path = output_dir / str(benchmark_payload["equity_filename"])
    benchmark["equity"].to_csv(benchmark_path, index=False)
    benchmark_metadata_path = output_dir / "benchmark_metadata.json"
    benchmark_metadata_path.write_text(
        json.dumps(benchmark_field_payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    for row in strategy_rows:
        pd.DataFrame([asdict(trade) for trade in row["cost_result"].portfolio_result.trades]).to_csv(
            output_dir / f"{row['strategy_name']}_trades_with_cost.csv",
            index=False,
        )

    report_path = write_markdown_report(
        output_dir,
        comparison_rows,
        diagnostics_rows,
        market_rows,
        {
            "comparison": comparison_path,
            "diagnostics": diagnostics_path,
            "benchmark": str(benchmark_path),
            "benchmark_metadata": str(benchmark_metadata_path),
        },
        data_start=start_date,
        data_end=end_date,
        selected_symbols=selected_symbols,
        benchmark_field_payload=benchmark_field_payload,
        benchmark_column=str(benchmark_payload["comparison_column"]),
        benchmark_equity_label=str(benchmark_payload["equity_label"]),
        experiment_10_comparison=str(args.experiment_10_comparison),
        experiment_12_summary=str(args.experiment_12_summary),
    )
    print(f"报告已生成: {report_path}")
    diagnostics_logger.disabled = previous_disabled


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十三三策略横向对比。")
    add_market_data_input_args(parser)
    parser.add_argument("--quality-report", default=None, help="兼容旧参数；当前不读取旧质量报告内容。")
    parser.add_argument("--output-dir", default=str(research_report_path("experiment_13")))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--experiment-10-comparison", default=str(research_report_path("experiment_10", "out_of_sample_comparison.csv")))
    parser.add_argument("--experiment-12-summary", default=str(research_report_path("experiment_12", "segment_summary.csv")))
    parser.add_argument("--benchmark-kind", default="policy_unconfirmed", choices=["price_index", "total_return_index", "adjusted_index", "policy_unconfirmed"])
    parser.add_argument("--require-benchmark", action="store_true", help="缺少 hs300_index 时返回 required_missing metadata。")
    parser.add_argument("--allow-benchmark-warn", action="store_true", help="允许 quality warn 的 hs300_index 进入 benchmark metadata。")
    parser.add_argument("--verbose", action="store_true", help="输出结构化诊断日志。")
    return parser.parse_args()


def run_strategy_comparisons(
    close_df: pd.DataFrame,
    metadata: dict[str, Any],
    initial_cash: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    zero_cost = PortfolioConfig(initial_cash=initial_cash, commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0)
    cost = PortfolioConfig(initial_cash=initial_cash)
    for strategy_name, base_config in default_strategy_configs(initial_cash).items():
        no_cost_result = run_backtest(close_df, _with_portfolio_config(base_config, zero_cost), metadata=metadata)
        cost_result = run_backtest(close_df, _with_portfolio_config(base_config, cost), metadata=metadata)
        daily_returns = _daily_returns(cost_result)
        filled_trades = [trade for trade in cost_result.portfolio_result.trades if trade.status == "filled"]
        months = max(len(cost_result.portfolio_result.daily_snapshots) / 21.0, 1e-12)
        profit_loss_ratio = calculate_profit_loss_ratio(daily_returns)
        cost_erosion = calculate_cost_erosion(
            float(no_cost_result.metrics["annual_return"]),
            float(cost_result.metrics["annual_return"]),
        )
        row = {
            "strategy_name": strategy_name,
            "label": STRATEGY_LABELS[strategy_name],
            "no_cost_result": no_cost_result,
            "cost_result": cost_result,
            "annual_return_no_cost": no_cost_result.metrics["annual_return"],
            "annual_return_with_cost": cost_result.metrics["annual_return"],
            "sharpe": cost_result.metrics["sharpe"],
            "max_drawdown": cost_result.metrics["max_drawdown"],
            "win_rate": calculate_win_rate(daily_returns),
            "profit_loss_ratio": profit_loss_ratio,
            "monthly_trade_count": len(filled_trades) / months,
            "cost_erosion": cost_erosion,
            "turnover": cost_result.metrics["turnover"],
            "filled_trade_count": len(filled_trades),
        }
        rows.append(row)
        diagnostics.append(
            {
                "strategy_name": strategy_name,
                "annual_return_no_cost": row["annual_return_no_cost"],
                "annual_return_with_cost": row["annual_return_with_cost"],
                "sharpe": row["sharpe"],
                "max_drawdown": row["max_drawdown"],
                "win_rate": row["win_rate"],
                "profit_loss_ratio": row["profit_loss_ratio"],
                "monthly_trade_count": row["monthly_trade_count"],
                "filled_trade_count": row["filled_trade_count"],
                "turnover": row["turnover"],
                "cost_erosion": row["cost_erosion"],
                "total_return_with_cost": cost_result.metrics["total_return"],
                "final_value_with_cost": cost_result.metrics["final_value"],
            }
        )
    return rows, diagnostics


def build_comparison_table(
    benchmark_metrics: dict[str, Any],
    strategy_rows: list[dict[str, Any]],
    decay_by_strategy: dict[str, float | None],
    *,
    benchmark_column: str = PROXY_BASELINE_COLUMN,
    excess_dimension: str = "proxy_excess_annual_return",
) -> list[dict[str, Any]]:
    by_strategy = {row["strategy_name"]: row for row in strategy_rows}
    benchmark_annual = float(benchmark_metrics["annual_return"])
    return [
        _dimension_row(
            "年化收益率",
            benchmark_annual,
            {name: row["annual_return_no_cost"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            excess_dimension,
            "—",
            {name: float(row["annual_return_no_cost"]) - benchmark_annual for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "夏普比率",
            benchmark_metrics["sharpe"],
            {name: row["sharpe"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "最大回撤",
            benchmark_metrics["max_drawdown"],
            {name: row["max_drawdown"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "胜率",
            "",
            {name: row["win_rate"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "盈亏比",
            "",
            {name: row["profit_loss_ratio"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "月均交易次数",
            "",
            {name: row["monthly_trade_count"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "样本内外衰减量",
            "—",
            {name: decay_by_strategy.get(name) for name in by_strategy},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "含成本后年化收益",
            benchmark_annual,
            {name: row["annual_return_with_cost"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "成本侵蚀幅度",
            "—",
            {name: row["cost_erosion"] for name, row in by_strategy.items()},
            benchmark_column=benchmark_column,
        ),
        _dimension_row(
            "适合市场",
            "—",
            {name: SUITABLE_MARKET[name] for name in by_strategy},
            benchmark_column=benchmark_column,
        ),
    ]


def calculate_profit_loss_ratio(daily_returns: pd.Series) -> float | None:
    """日收益盈亏比：平均正收益 / 平均负收益绝对值。"""

    gains = daily_returns[daily_returns > 0]
    losses = daily_returns[daily_returns < 0]
    if gains.empty or losses.empty:
        return None
    avg_loss = abs(float(losses.mean()))
    if avg_loss == 0:
        return None
    return float(gains.mean()) / avg_loss


def calculate_cost_erosion(no_cost_annual_return: float, with_cost_annual_return: float) -> float | None:
    """成本侵蚀幅度，负收益策略使用绝对值分母避免符号反向。"""

    denominator = abs(float(no_cost_annual_return))
    if denominator == 0:
        return None
    return (float(no_cost_annual_return) - float(with_cost_annual_return)) / denominator


def resolve_benchmark_for_experiment_13(
    *,
    lake_root: str | None,
    start_date: str,
    end_date: str,
    benchmark_kind: str = "policy_unconfirmed",
    required: bool = False,
    allow_warn: bool = False,
    price_trade_dates: list[str] | None = None,
) -> BenchmarkResult | None:
    if not lake_root and not required:
        return None
    if not lake_root and required:
        return missing_benchmark_result_for_experiment_13(
            start_date=start_date,
            end_date=end_date,
            benchmark_kind=benchmark_kind,
            required=True,
            reason="lake_root_missing",
        )
    policy = BenchmarkPolicy.from_config(
        {
            "benchmark_kind": benchmark_kind,
            "confirmed": benchmark_kind != "policy_unconfirmed",
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
        price_trade_dates=price_trade_dates,
    )


def missing_benchmark_result_for_experiment_13(
    *,
    start_date: str,
    end_date: str,
    benchmark_kind: str,
    required: bool,
    reason: str,
) -> BenchmarkResult:
    status = "required_missing" if required else "unavailable"
    return BenchmarkResult(
        status=status,
        dataset="hs300_index",
        source="none",
        index_code="399300.SZ",
        interface="hs300_index.daily",
        start_date=start_date,
        end_date=end_date,
        available_start_date=None,
        available_end_date=None,
        coverage=BenchmarkCoverage(0, 0, 0.0, [], reason),
        quality_status="missing",
        missing_reason=reason,
        required=required,
        benchmark_kind=benchmark_kind,
        next_action=build_next_action(reason, required),
        remediation_job_spec=build_hs300_remediation_spec(
            start_date=start_date,
            end_date=end_date,
            lake_root_hint=None,
            reason=reason,
        ),
        catalog_entry=None,
        run_id=None,
        lineage={"status": "lineage_unavailable", "reason": reason},
        frame=None,
    )


def build_experiment_13_benchmark(
    close_df: pd.DataFrame,
    initial_cash: float,
    benchmark_result: BenchmarkResult | None,
    *,
    require_benchmark: bool = False,
) -> dict[str, Any]:
    proxy = build_equal_weight_benchmark(close_df, initial_cash)
    proxy["name"] = "proxy_baseline"

    if _is_available_hs300_for_experiment_13(benchmark_result):
        real = build_hs300_benchmark_equity(benchmark_result, close_df.index, initial_cash)
        field_payload = build_benchmark_field_payload(
            benchmark_result,
            hs300_metrics=real["metrics"],
        )
        return {
            "benchmark": real,
            "field_payload": field_payload,
            "comparison_column": HS300_BENCHMARK_COLUMN,
            "excess_dimension": "hs300_excess_annual_return",
            "equity_filename": "hs300_benchmark_equity_curve.csv",
            "equity_label": "真实沪深300 benchmark 净值",
        }

    if require_benchmark:
        status = benchmark_result.status if benchmark_result is not None else "required_missing"
        reason = (
            benchmark_result.missing_reason
            if benchmark_result is not None and benchmark_result.missing_reason
            else "benchmark_result_missing"
        )
        raise BenchmarkUnavailableError(
            f"真实 hs300_index benchmark 不可用: status={status}; missing_reason={reason}"
        )

    field_payload = build_benchmark_field_payload(
        benchmark_result,
        proxy_metrics=proxy_metrics_from_equal_weight(proxy["metrics"]),
        proxy_baseline={
            "status": "used",
            "source": "same_universe_equal_weight_buy_and_hold",
        },
    )
    return {
        "benchmark": proxy,
        "field_payload": field_payload,
        "comparison_column": PROXY_BASELINE_COLUMN,
        "excess_dimension": "proxy_excess_annual_return",
        "equity_filename": "benchmark_proxy_equity_curve.csv",
        "equity_label": "基准代理净值",
    }


def build_hs300_benchmark_equity(
    benchmark_result: BenchmarkResult,
    price_index: pd.Index,
    initial_cash: float,
) -> dict[str, Any]:
    if not _is_available_hs300_for_experiment_13(benchmark_result):
        raise BenchmarkUnavailableError(
            "真实 hs300_index benchmark 不可用: "
            f"status={benchmark_result.status}; missing_reason={benchmark_result.missing_reason}"
        )
    frame = benchmark_result.frame
    if frame is None or frame.empty or "trade_date" not in frame.columns or "close" not in frame.columns:
        raise BenchmarkUnavailableError(
            "真实 hs300_index benchmark 不可用: status=available; missing_reason=frame_missing"
        )

    target_dates = [str(item) for item in price_index]
    close = (
        frame.assign(trade_date=frame["trade_date"].astype(str))
        .drop_duplicates("trade_date", keep="last")
        .set_index("trade_date")["close"]
        .pipe(pd.to_numeric, errors="coerce")
        .sort_index()
    )
    aligned = close.reindex(target_dates).ffill()
    valid = aligned.dropna()
    if valid.empty or aligned.isna().any() or float(valid.iloc[0]) <= 0:
        raise BenchmarkUnavailableError(
            "真实 hs300_index benchmark 不可用: status=available; missing_reason=price_benchmark_overlap_missing"
        )
    nav = aligned / float(valid.iloc[0])
    values = nav * float(initial_cash)
    metrics = calculate_series_metrics(values)
    running_max = values.cummax()
    equity = pd.DataFrame(
        {
            "trade_date": target_dates,
            "total_value": values.to_numpy(),
            "nav": nav.to_numpy(),
            "drawdown": (values / running_max - 1.0).to_numpy(),
            "turnover_amount": [0.0] * len(values),
            "holding_count": [1] * len(values),
        }
    )
    return {
        "name": "hs300_index",
        "metrics": metrics,
        "equity": equity,
    }


def apply_benchmark_metadata_experiment_13(
    result: BenchmarkResult | None,
    existing_metadata: dict[str, Any],
    *,
    field_payload: dict[str, Any] | None = None,
    proxy_metrics: dict[str, Any] | None = None,
    hs300_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = field_payload or build_benchmark_field_payload(
        result,
        proxy_metrics=proxy_metrics,
        hs300_metrics=hs300_metrics,
    )
    metadata = dict(existing_metadata)
    metadata.update(payload)
    real_available = "hs300_index" in payload
    metadata["benchmark_dataset"] = "hs300_index" if real_available else "proxy_baseline"
    metadata["hs300_relative_return_enabled"] = real_available
    return metadata


def _is_available_hs300_for_experiment_13(result: BenchmarkResult | None) -> bool:
    return (
        isinstance(result, BenchmarkResult)
        and result.available
        and result.dataset == "hs300_index"
        and result.coverage.ratio == 1.0
        and result.frame is not None
        and result.missing_reason is None
    )


def proxy_metrics_from_equal_weight(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "annual_return": metrics.get("annual_return"),
        "total_return": metrics.get("total_return"),
        "sharpe": metrics.get("sharpe"),
        "max_drawdown": metrics.get("max_drawdown"),
        "turnover": metrics.get("turnover"),
        "final_value": metrics.get("final_value"),
    }


def load_decay_by_strategy(path: Path) -> dict[str, float | None]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if "strategy_name" not in frame.columns or "decay" not in frame.columns:
        return {}
    return {
        str(row["strategy_name"]): _to_optional_float(row["decay"])
        for _, row in frame.iterrows()
    }


def load_market_segment_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    return frame.to_dict("records")


def write_markdown_report(
    output_dir: Path,
    comparison_rows: list[dict[str, Any]],
    diagnostics_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
    paths: dict[str, str],
    *,
    data_start: str,
    data_end: str,
    selected_symbols: list[str],
    benchmark_field_payload: dict[str, Any],
    benchmark_column: str,
    benchmark_equity_label: str,
    experiment_10_comparison: str,
    experiment_12_summary: str,
) -> str:
    benchmark_lines = _benchmark_report_lines(benchmark_field_payload)
    lines = [
        "# 实验十三：三策略横向对比报告",
        "",
        "## 数据与口径",
        "",
        f"- 回测区间：{data_start} 至 {data_end}。",
        f"- 股票池：{', '.join(selected_symbols)}，三策略使用完全相同股票池和时间段。",
        f"- benchmark_status：`{benchmark_field_payload['benchmark_status']}`；benchmark_kind：`{benchmark_field_payload['benchmark_kind']}`；missing_reason：`{benchmark_field_payload['benchmark_missing_reason']}`。",
        *benchmark_lines,
        "- 主表“年化收益率”为无交易成本结果；“含成本后年化收益”使用默认成本：佣金 0.03%、滑点 0.02%、卖出印花税 0.10%。",
        "- 成本侵蚀幅度 = (无成本年化收益 - 含成本后年化收益) / abs(无成本年化收益)；负收益策略使用绝对值分母，避免符号反向。",
        "- 胜率口径：日胜率 = 正收益交易日 / 非零收益交易日；盈亏比口径：平均正日收益 / 平均负日收益绝对值。",
        f"- 样本内外衰减量读取：`{experiment_10_comparison}`；市场环境分段读取：`{experiment_12_summary}`。",
        "",
        "## 横向对比表",
        "",
        _markdown_table(
            comparison_rows,
            ["对比维度", benchmark_column, "动量", "RSI", "MACD"],
        ),
        "",
        "## 诊断明细",
        "",
        _markdown_table(
            diagnostics_rows,
            [
                "strategy_name",
                "annual_return_no_cost",
                "annual_return_with_cost",
                "sharpe",
                "max_drawdown",
                "win_rate",
                "profit_loss_ratio",
                "monthly_trade_count",
                "filled_trade_count",
                "turnover",
                "cost_erosion",
            ],
        ),
        "",
        "## 结论",
        "",
        *build_conclusion_lines(comparison_rows, diagnostics_rows, market_rows),
        "",
        "## 输出文件",
        "",
        f"- 横向对比表：`{paths['comparison']}`",
        f"- 策略诊断表：`{paths['diagnostics']}`",
        f"- {benchmark_equity_label}：`{paths['benchmark']}`",
        f"- benchmark metadata：`{paths['benchmark_metadata']}`",
        "",
    ]
    report_path = output_dir / "backtest_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def _benchmark_report_lines(benchmark_field_payload: dict[str, Any]) -> list[str]:
    if "hs300_index" in benchmark_field_payload:
        result = benchmark_field_payload["hs300_index"]
        coverage = result.get("coverage") if isinstance(result, dict) else {}
        lineage = result.get("lineage") if isinstance(result, dict) else {}
        return [
            "- 已使用真实 `hs300_index` benchmark；comparison 和 metadata 中真实字段使用 `hs300_*` / `hs300_index`。",
            f"- 真实 benchmark coverage：`{coverage}`；lineage：`{lineage}`。",
        ]
    return [
        "- `proxy_baseline` 使用同股票池等权买入持有，不是真实沪深300指数；缺真实 benchmark 时不输出 `hs300_*` 字段。",
        "- 当前报告只声明 proxy 对照收益，不声明沪深300超额收益。",
    ]


def build_conclusion_lines(
    comparison_rows: list[dict[str, Any]],
    diagnostics_rows: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
) -> list[str]:
    diagnostics = {row["strategy_name"]: row for row in diagnostics_rows}
    by_dimension = {row["对比维度"]: row for row in comparison_rows}
    annual = by_dimension["年化收益率"]
    sharpe = by_dimension["夏普比率"]
    max_drawdown = by_dimension["最大回撤"]
    decay = by_dimension["样本内外衰减量"]
    erosion = by_dimension["成本侵蚀幅度"]

    best_return = _best_strategy_from_row(annual, reverse=True)
    best_sharpe = _best_strategy_from_row(sharpe, reverse=True)
    worst_decay = _best_strategy_from_row(decay, reverse=True)
    worst_erosion = _best_strategy_from_row(erosion, reverse=True)
    lines = [
        f"- 收益最高：`{best_return}`。对应最大回撤为 {_format_value(max_drawdown[best_return], '最大回撤')}，需要和收益一起看，不能只按收益排序。",
        f"- 风险调整后收益最好：`{best_sharpe}`，即夏普比率最高。",
        f"- 参数最敏感/过拟合衰减最大：`{worst_decay}`，使用实验十的样本内外衰减量判断。",
        f"- 交易成本影响最大：`{worst_erosion}`，成本侵蚀幅度最高；月均交易次数分别为动量 {diagnostics['momentum']['monthly_trade_count']:.2f}、RSI {diagnostics['rsi']['monthly_trade_count']:.2f}、MACD {diagnostics['macd']['monthly_trade_count']:.2f}。",
    ]
    complete_segments = [row for row in market_rows if row.get("status") == "success"]
    if complete_segments:
        winners = ", ".join(f"{row['label']}={row['best_strategy']}" for row in complete_segments)
        lines.append(f"- 市场环境分段：当前可完整比较的分段为 {winners}。受本地数据限制，可验证环境不足，不能把该结论外推到所有牛熊市。")
    else:
        lines.append("- 市场环境分段：当前没有可完整比较的三策略分段，不能验证“动量适合趋势市、RSI 适合震荡市”的假设。")
    return lines


def _dimension_row(
    dimension: str,
    benchmark: Any,
    strategy_values: dict[str, Any],
    *,
    benchmark_column: str,
) -> dict[str, Any]:
    return {
        "对比维度": dimension,
        benchmark_column: benchmark,
        "动量": strategy_values.get("momentum", ""),
        "RSI": strategy_values.get("rsi", ""),
        "MACD": strategy_values.get("macd", ""),
    }


def _best_strategy_from_row(row: dict[str, Any], *, reverse: bool) -> str:
    values = {
        label: value
        for label, value in row.items()
        if label in {"动量", "RSI", "MACD"} and value not in ("", None, "—")
    }
    return sorted(values, key=lambda label: float(values[label]), reverse=reverse)[0]


def _daily_returns(result: BacktestResult) -> pd.Series:
    values = pd.Series(
        [snapshot.total_value for snapshot in result.portfolio_result.daily_snapshots],
        index=[snapshot.trade_date for snapshot in result.portfolio_result.daily_snapshots],
        dtype="float64",
    )
    return values.pct_change().dropna()


def _with_portfolio_config(config: BacktestConfig, portfolio_config: PortfolioConfig) -> BacktestConfig:
    return BacktestConfig(
        lookback_days=config.lookback_days,
        rebalance_freq=config.rebalance_freq,
        top_fraction=config.top_fraction,
        strategy_name=config.strategy_name,
        strategy_params=dict(config.strategy_params),
        portfolio_config=portfolio_config,
    )


def _markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    header = "| " + " | ".join(fields) + " |"
    sep = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(_format_value(row.get(field, ""), str(row.get("对比维度", field))) for field in fields) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def _format_value(value: Any, dimension: str) -> str:
    if value in ("", None):
        return ""
    if value == "—":
        return "—"
    if dimension in PERCENT_DIMENSIONS:
        try:
            return f"{float(value) * 100:.2f}%"
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _to_optional_float(value: Any) -> float | None:
    if value in ("", None) or pd.isna(value):
        return None
    return float(value)


if __name__ == "__main__":
    main()
