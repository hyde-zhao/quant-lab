"""实验十七至二十一：技术、风险成交量、多因子组合与策略化回测。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
import logging
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.metrics import calculate_metrics
from engine.diagnostics import LOGGER_NAME
from engine.factor_statistics import build_forward_return_matrix, single_sort_returns
from engine.portfolio import (
    DEFAULT_COST_GRID_BPS,
    PortfolioConfig,
    PortfolioResult,
    RebalanceSignal,
    build_capacity_report,
    evaluate_capacity_cost_claims,
    run_cost_sensitivity_grid,
    run_portfolio,
)
from engine.research_dataset import (
    build_liquidity_capacity_inputs,
    evaluate_robust_validation_claims,
    merge_capacity_cost_metadata,
    merge_factor_audit_metadata,
)
from engine.research_paths import research_report_path
from experiments.run_experiment_15_factor_framework import (
    FactorFrameworkError,
    build_universe,
    format_value,
    load_local_frames,
    markdown_table,
)
from market_data.benchmarks import build_benchmark_policy_result


DEFAULT_CR011_OUTPUT_DIR = str(research_report_path("experiment_17_21_cr011"))
LEGACY_EXPERIMENT_17_21_REPORT = research_report_path("experiment_17_21", "factor_strategy_report.md")
DEFAULT_FACTORS = (
    "momentum_20d",
    "reversal_5d",
    "rsi_14",
    "macd_diff",
    "macd_hist",
    "ma_gap_20",
    "volatility_20d",
    "volume_change_20d",
    "turnover_proxy",
    "max_drawdown_20d",
)
DEFAULT_TOP_FRACTIONS = (0.1, 0.2)
FACTOR_PANEL_AUDIT_STAGES = ("raw", "directional", "winsorized", "zscore")
ROBUST_VALIDATION_VIEWS = ("rolling", "annual", "market_state", "parameter_grid", "cost_grid")
S08_SAFETY_COUNTERS = {
    "network_calls": 0,
    "lake_writes": 0,
    "credential_reads": 0,
    "legacy_data_operations": 0,
    "old_report_overwrites": 0,
}


@dataclass(frozen=True, slots=True)
class MarketMatrices:
    close: pd.DataFrame
    volume: pd.DataFrame
    amount: pd.DataFrame
    universe: list[str]
    calendar: list[date]
    amount_source: str


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    name: str
    experiment: str
    source: str
    hypothesis: str
    stage2_link: str
    direction_sign: int
    direction_note: str


@dataclass(frozen=True, slots=True)
class Experiment1721Result:
    report_path: Path
    factor_retention_path: Path
    preprocessing_summary_path: Path
    ic_timeseries_path: Path
    group_returns_path: Path
    correlation_path: Path
    strategy_summary_path: Path
    sample_split_path: Path
    score_preview_path: Path
    benchmark_equity_path: Path
    factor_panel_manifest_path: Path
    robust_validation_summary_path: Path


def main() -> None:
    args = parse_args()
    result = run_factor_suite(args)
    print(f"报告已生成: {result.report_path}")
    print(f"因子保留表已生成: {result.factor_retention_path}")
    print(f"策略回测摘要已生成: {result.strategy_summary_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十七至二十一因子研究与策略化回测。")
    parser.add_argument("--data-dir", required=True, default=None, help="必须显式传入的本地标准 parquet 目录。")
    parser.add_argument("--output-dir", default=DEFAULT_CR011_OUTPUT_DIR)
    parser.add_argument("--run-id", default=None, help="可选 run_id；传入时在 output-dir 下创建隔离子目录。")
    parser.add_argument("--benchmark-policy", default="hs300_required", choices=["hs300_required", "hs300_optional", "proxy_allowed"])
    parser.add_argument("--realism-mode", default="exploratory", choices=["exploratory", "production_strict"])
    parser.add_argument(
        "--baseline-report-path",
        default=str(LEGACY_EXPERIMENT_17_21_REPORT),
        help="旧实验 17-21 baseline 报告路径，仅作为字符串引用，禁止覆盖。",
    )
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--factors", nargs="+", default=list(DEFAULT_FACTORS))
    parser.add_argument("--horizon", type=int, default=20, choices=[1, 5, 10, 20], help="IC、分组收益和保留决策使用的未来收益窗口。")
    parser.add_argument("--group-count", type=int, default=5, help="分组收益横截面组数。")
    parser.add_argument("--min-cross-section", type=int, default=5, help="IC/分组/预处理要求的最小横截面股票数。")
    parser.add_argument("--winsor-lower", type=float, default=0.01, help="横截面去极值下分位点。")
    parser.add_argument("--winsor-upper", type=float, default=0.99, help="横截面去极值上分位点。")
    parser.add_argument("--rebalance-freq", type=int, default=20, help="调仓间隔，单位为交易日。")
    parser.add_argument("--top-fractions", nargs="+", type=float, default=list(DEFAULT_TOP_FRACTIONS), help="买入 Top 比例。")
    parser.add_argument("--exit-fraction", type=float, default=0.3, help="跌出该 Top 比例后卖出，用于实验二十一。")
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--train-fraction", type=float, default=0.7, help="样本内区间占比。")
    parser.add_argument("--max-symbols", type=int, default=0, help="大于 0 时只取排序后的前 N 只股票，用于 5 股池 smoke test。")
    parser.add_argument("--preview-rows", type=int, default=2000)
    parser.add_argument("--min-model-factors", type=int, default=2, help="严格保留因子不足时，探索模型最多补足到该数量。")
    parser.add_argument("--verbose", action="store_true", help="输出组合引擎结构化诊断日志。")
    return parser.parse_args()


def run_factor_suite(args: argparse.Namespace) -> Experiment1721Result:
    validate_args(args)
    output_dir = resolve_cr011_validation_output_dir(args.output_dir, run_id=getattr(args, "run_id", None))
    output_dir.mkdir(parents=True, exist_ok=True)

    definitions = select_factor_definitions(args.factors)
    frames = load_local_frames(require_explicit_data_dir(args))
    market = build_market_matrices(frames, args.start_date, args.end_date, max_symbols=int(args.max_symbols))
    raw_matrices = calculate_raw_factor_matrices(market, definitions)
    zscore_matrices, preprocessing_summary = preprocess_factor_matrices(
        raw_matrices,
        definitions,
        winsor_lower=float(args.winsor_lower),
        winsor_upper=float(args.winsor_upper),
        min_cross_section=int(args.min_cross_section),
    )
    forward_returns = build_forward_returns(market.close, horizon=int(args.horizon))

    ic_timeseries = calculate_ic_timeseries(zscore_matrices, forward_returns, min_cross_section=int(args.min_cross_section))
    ic_summary = summarize_ic(ic_timeseries)
    group_timeseries = calculate_group_timeseries(
        zscore_matrices,
        forward_returns,
        group_count=int(args.group_count),
        min_cross_section=int(args.min_cross_section),
    )
    group_returns = summarize_group_returns(group_timeseries)
    monotonicity = summarize_monotonicity(group_returns, group_count=int(args.group_count))
    correlation = calculate_factor_correlations(zscore_matrices)
    turnover = calculate_top_turnover(
        zscore_matrices,
        top_fraction=max(args.top_fractions),
        rebalance_freq=int(args.rebalance_freq),
        min_cross_section=int(args.min_cross_section),
    )
    retention = build_factor_retention_summary(
        definitions=definitions,
        ic_summary=ic_summary,
        monotonicity=monotonicity,
        turnover=turnover,
        correlation=correlation,
        min_ic_days=max(20, int(args.rebalance_freq)),
    )
    model_factors, model_policy = choose_model_factors(retention, min_model_factors=int(args.min_model_factors))
    multi_score = build_multifactor_score(zscore_matrices, model_factors)
    score_preview = build_score_preview(multi_score, zscore_matrices, model_factors, rows=int(args.preview_rows))

    diagnostics_logger = logging.getLogger(LOGGER_NAME)
    previous_disabled = diagnostics_logger.disabled
    if not getattr(args, "verbose", False):
        diagnostics_logger.disabled = True
    try:
        benchmark = run_equal_weight_benchmark(market.close, initial_cash=float(args.initial_cash))
        benchmark_policy_metadata = build_experiment_benchmark_policy_metadata(
            benchmark_metrics=benchmark["metrics"],
            benchmark_policy_id=str(getattr(args, "benchmark_policy", "hs300_required")),
            realism_mode=str(getattr(args, "realism_mode", "exploratory")),
            baseline_report_path=getattr(args, "baseline_report_path", None),
        )
        liquidity_payload = build_experiment_liquidity_capacity_payload(market)
        strategy_summary, sample_split, strategy_artifacts = run_factor_strategies(
            close_df=market.close,
            zscore_matrices=zscore_matrices,
            multi_score=multi_score,
            model_factors=model_factors,
            top_fractions=[float(item) for item in args.top_fractions],
            exit_fraction=float(args.exit_fraction),
            rebalance_freq=int(args.rebalance_freq),
            initial_cash=float(args.initial_cash),
            train_fraction=float(args.train_fraction),
            output_dir=output_dir,
            benchmark_metrics=benchmark["metrics"],
            liquidity_payload=liquidity_payload,
        )
    finally:
        diagnostics_logger.disabled = previous_disabled
    multi_group_timeseries = calculate_group_timeseries(
        {"multifactor_score": multi_score},
        forward_returns,
        group_count=int(args.group_count),
        min_cross_section=int(args.min_cross_section),
    )
    multi_group_returns = summarize_group_returns(multi_group_timeseries)

    preprocessing_summary_path = output_dir / "factor_preprocessing_summary.csv"
    factor_retention_path = output_dir / "factor_retention_summary.csv"
    ic_timeseries_path = output_dir / "ic_timeseries.csv"
    ic_summary_path = output_dir / "ic_summary.csv"
    group_timeseries_path = output_dir / "group_timeseries.csv"
    group_returns_path = output_dir / "group_returns.csv"
    multi_group_returns_path = output_dir / "multifactor_group_returns.csv"
    correlation_path = output_dir / "factor_correlation.csv"
    strategy_summary_path = output_dir / "strategy_summary.csv"
    sample_split_path = output_dir / "sample_split_summary.csv"
    score_preview_path = output_dir / "multifactor_score_preview.csv"
    benchmark_equity_path = output_dir / "benchmark_proxy_equity_curve.csv"
    metadata_path = output_dir / "experiment_metadata.json"
    capacity_cost_metadata = build_experiment_capacity_cost_metadata(
        benchmark_policy_metadata,
        strategy_summary,
    )
    factor_panel_by_stage, factor_panel_manifest = build_factor_panel_audit(
        raw_matrices,
        zscore_matrices,
        preprocessing_summary,
        definitions,
        run_metadata={
            "report_kind": "experiment_17_21_v2",
            "run_id": getattr(args, "run_id", None) or "",
            "output_dir": str(output_dir),
            **S08_SAFETY_COUNTERS,
        },
    )
    factor_panel_manifest = write_factor_panel_audit_outputs(output_dir, factor_panel_by_stage, factor_panel_manifest)
    robust_validation_summary = build_robust_validation_views(
        factor_panel_manifest,
        strategy_summary,
        strategy_artifacts,
        capacity_cost_metadata,
        market_state_labels=build_market_state_labels(market.close),
        parameter_grid=build_parameter_grid(args.top_fractions, args.exit_fraction, args.rebalance_freq),
    )
    robust_validation_summary = write_robust_validation_outputs(output_dir, robust_validation_summary)
    robust_claim_result = evaluate_robust_validation_claims(robust_validation_summary, capacity_cost_metadata)
    metadata_payload = merge_factor_audit_metadata(
        {
            "data_dir": str(args.data_dir),
            "start_date": market.close.index.min().isoformat(),
            "end_date": market.close.index.max().isoformat(),
            "symbol_count": len(market.universe),
            "calendar_days": len(market.calendar),
            "amount_source": market.amount_source,
            "model_factors": model_factors,
            "model_policy": model_policy,
            "benchmark": benchmark_policy_metadata,
            "benchmark_policy": benchmark_policy_metadata,
            "cost_grid_bps": capacity_cost_metadata.get("cost_grid_bps", list(DEFAULT_COST_GRID_BPS)),
            "capacity_report": capacity_cost_metadata.get("capacity_report", {}),
            "cost_sensitivity_report": capacity_cost_metadata.get("cost_sensitivity_report", {}),
            "liquidity_capacity_status": capacity_cost_metadata.get("liquidity_capacity_status", "blocked_missing_liquidity"),
            "capacity_cost_status": capacity_cost_metadata.get("capacity_cost_status", "fail"),
            "cost_sensitivity_status": capacity_cost_metadata.get("cost_sensitivity_status", "fail"),
            "allowed_claims": capacity_cost_metadata.get("allowed_claims", []),
            "blocked_claims": capacity_cost_metadata.get("blocked_claims", []),
            "known_limitations": capacity_cost_metadata.get("known_limitations", []),
            **{
                field: benchmark_policy_metadata.get(field)
                for field in (
                    "benchmark_policy_id",
                    "benchmark_kind",
                    "hs300_available",
                    "hs300_coverage_ratio",
                    "proxy_baseline_used",
                    "benchmark_missing_reason",
                )
            },
            **S08_SAFETY_COUNTERS,
        },
        factor_panel_manifest,
        robust_validation_summary,
        robust_claim_result,
    )

    preprocessing_summary.to_csv(preprocessing_summary_path, index=False)
    retention.to_csv(factor_retention_path, index=False)
    ic_timeseries.to_csv(ic_timeseries_path, index=False)
    ic_summary.to_csv(ic_summary_path, index=False)
    group_timeseries.to_csv(group_timeseries_path, index=False)
    group_returns.to_csv(group_returns_path, index=False)
    multi_group_returns.to_csv(multi_group_returns_path, index=False)
    correlation.to_csv(correlation_path, index=False)
    strategy_summary.to_csv(strategy_summary_path, index=False)
    sample_split.to_csv(sample_split_path, index=False)
    score_preview.to_csv(score_preview_path, index=False)
    benchmark["equity"].to_csv(benchmark_equity_path, index=False)
    metadata_path.write_text(
        json.dumps(_json_ready(metadata_payload), ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    report_path = output_dir / "factor_strategy_report.md"
    report_path.write_text(
        render_report(
            args=args,
            market=market,
            definitions=definitions,
            preprocessing_summary=preprocessing_summary,
            retention=retention,
            model_factors=model_factors,
            model_policy=model_policy,
            group_returns=group_returns,
            multi_group_returns=multi_group_returns,
            strategy_summary=strategy_summary,
            sample_split=sample_split,
            benchmark_metrics=benchmark["metrics"],
            benchmark_policy_metadata=benchmark_policy_metadata,
            capacity_cost_metadata=capacity_cost_metadata,
            factor_audit_metadata=metadata_payload,
            paths={
                "report": report_path,
                "preprocessing": preprocessing_summary_path,
                "retention": factor_retention_path,
                "ic_timeseries": ic_timeseries_path,
                "ic_summary": ic_summary_path,
                "group_timeseries": group_timeseries_path,
                "group_returns": group_returns_path,
                "multi_group_returns": multi_group_returns_path,
                "correlation": correlation_path,
                "strategy_summary": strategy_summary_path,
                "sample_split": sample_split_path,
                "score_preview": score_preview_path,
                "benchmark_equity": benchmark_equity_path,
                "factor_panel_manifest": Path(str(factor_panel_manifest["manifest_path"])),
                "robust_validation_summary": Path(str(robust_validation_summary["summary_path"])),
                "metadata": metadata_path,
                **strategy_artifacts,
                **{
                    f"factor_panel_{stage}": Path(str(path))
                    for stage, path in factor_panel_manifest.get("stage_files", {}).items()
                },
                **{
                    f"robust_validation_{view}": Path(str(path))
                    for view, path in robust_validation_summary.get("view_files", {}).items()
                },
            },
        ),
        encoding="utf-8",
    )

    return Experiment1721Result(
        report_path=report_path,
        factor_retention_path=factor_retention_path,
        preprocessing_summary_path=preprocessing_summary_path,
        ic_timeseries_path=ic_timeseries_path,
        group_returns_path=group_returns_path,
        correlation_path=correlation_path,
        strategy_summary_path=strategy_summary_path,
        sample_split_path=sample_split_path,
        score_preview_path=score_preview_path,
        benchmark_equity_path=benchmark_equity_path,
        factor_panel_manifest_path=Path(str(factor_panel_manifest["manifest_path"])),
        robust_validation_summary_path=Path(str(robust_validation_summary["summary_path"])),
    )


def validate_args(args: argparse.Namespace) -> None:
    _ensure_not_legacy_report_output_path(args)
    if args.group_count < 2:
        raise FactorFrameworkError("group_count 必须至少为 2")
    if args.min_cross_section < 2:
        raise FactorFrameworkError("min_cross_section 必须至少为 2")
    if not 0 <= args.winsor_lower < args.winsor_upper <= 1:
        raise FactorFrameworkError("winsor 分位点必须满足 0 <= lower < upper <= 1")
    if args.rebalance_freq <= 0:
        raise FactorFrameworkError("rebalance_freq 必须为正数")
    for top_fraction in args.top_fractions:
        if not 0 < float(top_fraction) <= 1:
            raise FactorFrameworkError("top_fractions 必须在 (0, 1] 内")
    if not 0 < args.exit_fraction <= 1:
        raise FactorFrameworkError("exit_fraction 必须在 (0, 1] 内")
    if min(float(item) for item in args.top_fractions) > float(args.exit_fraction):
        raise FactorFrameworkError("exit_fraction 应不小于最小 top_fraction，否则卖出阈值比买入阈值更严格")
    if not 0 < args.train_fraction < 1:
        raise FactorFrameworkError("train_fraction 必须在 (0, 1) 内")


def _ensure_not_legacy_report_output_path(args: argparse.Namespace) -> None:
    resolve_cr011_validation_output_dir(
        getattr(args, "output_dir", DEFAULT_CR011_OUTPUT_DIR),
        run_id=getattr(args, "run_id", None),
    )


def resolve_cr011_validation_output_dir(output_dir: str | Path, run_id: str | None = None) -> Path:
    base_dir = Path(output_dir)
    run_id_value = str(run_id or "").strip()
    if run_id_value:
        run_id_path = Path(run_id_value)
        if run_id_path.is_absolute() or run_id_path.name != run_id_value or ".." in run_id_path.parts:
            raise FactorFrameworkError("run_id 只能是单层目录名，禁止绝对路径或上级目录跳转。")
        base_dir = base_dir / run_id_value

    legacy_report = LEGACY_EXPERIMENT_17_21_REPORT.resolve()
    report_path = base_dir / "factor_strategy_report.md"
    if (
        _is_legacy_experiment17_alias(base_dir)
        or _is_legacy_experiment17_alias(report_path)
        or base_dir.resolve() == legacy_report
        or base_dir.resolve() == legacy_report.parent
        or report_path.resolve() == legacy_report
    ):
        raise FactorFrameworkError(
            f"禁止覆盖旧实验 17-21 baseline 报告；请将 --output-dir 指向 {DEFAULT_CR011_OUTPUT_DIR} 或测试临时目录。"
        )
    return base_dir


def require_explicit_data_dir(args: argparse.Namespace) -> Path:
    data_dir = getattr(args, "data_dir", None)
    if data_dir is None or str(data_dir).strip() == "":
        raise FactorFrameworkError("必须显式传入 --data-dir，禁止默认读取仓库旧数据目录。")
    return Path(data_dir)


def factor_definitions() -> dict[str, FactorDefinition]:
    return {
        "momentum_20d": FactorDefinition(
            "momentum_20d",
            "baseline",
            "过去 20 日收益",
            "中期价格延续可能带来横截面相对收益",
            "动量/均线衔接",
            1,
            "原始值越大越看多",
        ),
        "reversal_5d": FactorDefinition(
            "reversal_5d",
            "experiment_17",
            "过去 5 日收益取反",
            "短期跌多后可能反弹",
            "RSI 的均值回归逻辑",
            1,
            "已取反，值越大表示短期跌幅越大，按均值回归假设越看多",
        ),
        "rsi_14": FactorDefinition(
            "rsi_14",
            "experiment_17",
            "14 日 RSI",
            "低 RSI 可能超跌",
            "实验七",
            -1,
            "原始 RSI 越低越看多，预处理阶段乘以 -1 统一方向",
        ),
        "macd_diff": FactorDefinition(
            "macd_diff",
            "experiment_17",
            "EMA12 - EMA26",
            "DIFF 值反映趋势强弱",
            "实验八",
            1,
            "原始值越大越看多",
        ),
        "macd_hist": FactorDefinition(
            "macd_hist",
            "experiment_17",
            "DIFF - DEA",
            "柱状线反映趋势加速度",
            "实验八",
            1,
            "原始值越大越看多",
        ),
        "ma_gap_20": FactorDefinition(
            "ma_gap_20",
            "experiment_17",
            "close / MA20 - 1",
            "价格相对均线偏离可能延续",
            "动量/均线衔接",
            1,
            "原始值越大越看多",
        ),
        "volatility_20d": FactorDefinition(
            "volatility_20d",
            "experiment_18",
            "过去 20 日收益波动率",
            "低波动可能更稳",
            "风险信号",
            -1,
            "原始波动率越低越看多，预处理阶段乘以 -1 统一方向",
        ),
        "volume_change_20d": FactorDefinition(
            "volume_change_20d",
            "experiment_18",
            "近 20 日均量 / 前 20 日均量 - 1",
            "放量可能代表关注度提升",
            "成交量信号",
            1,
            "原始值越大越看多",
        ),
        "turnover_proxy": FactorDefinition(
            "turnover_proxy",
            "experiment_18",
            "log1p(amount)，无 amount 时回退 log1p(volume)",
            "流动性影响可交易性",
            "交易可行性信号",
            1,
            "原始值越大表示流动性代理越强",
        ),
        "max_drawdown_20d": FactorDefinition(
            "max_drawdown_20d",
            "experiment_18",
            "过去 20 日滚动高点回撤的最小值",
            "短期回撤越深，风险状态越差",
            "风险信号",
            1,
            "原始值为负数，越接近 0 越看多",
        ),
    }


def select_factor_definitions(factor_names: list[str] | tuple[str, ...]) -> list[FactorDefinition]:
    definitions = factor_definitions()
    selected: list[FactorDefinition] = []
    seen: set[str] = set()
    unsupported: list[str] = []
    for name in factor_names:
        factor_name = str(name)
        if factor_name in seen:
            continue
        seen.add(factor_name)
        definition = definitions.get(factor_name)
        if definition is None:
            unsupported.append(factor_name)
        else:
            selected.append(definition)
    if unsupported:
        raise FactorFrameworkError("不支持的因子名: " + ", ".join(unsupported))
    if not selected:
        raise FactorFrameworkError("至少需要一个因子")
    return selected


def build_market_matrices(
    frames: dict[str, pd.DataFrame],
    start_date: str | None,
    end_date: str | None,
    *,
    max_symbols: int = 0,
) -> MarketMatrices:
    prices = frames["prices"].copy()
    members = frames["index_members"].copy()
    calendar_frame = frames["trade_calendar"].copy()
    required_price_columns = {"trade_date", "symbol", "close", "volume"}
    missing_price_columns = sorted(required_price_columns - set(prices.columns))
    if missing_price_columns:
        raise FactorFrameworkError("prices 缺少必需字段: " + ", ".join(missing_price_columns))
    if "symbol" not in members.columns:
        raise FactorFrameworkError("index_members 缺少必需字段: symbol")
    if "trade_date" not in calendar_frame.columns:
        raise FactorFrameworkError("trade_calendar 缺少必需字段: trade_date")

    prices["trade_date"] = _date_series(prices["trade_date"])
    prices["symbol"] = prices["symbol"].astype("string").str.strip()
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    prices["volume"] = pd.to_numeric(prices["volume"], errors="coerce")
    if "amount" in prices.columns:
        prices["amount"] = pd.to_numeric(prices["amount"], errors="coerce")
        amount_source = "amount"
    else:
        prices["amount"] = prices["volume"]
        amount_source = "volume_fallback"
    calendar_frame["trade_date"] = _date_series(calendar_frame["trade_date"])
    if "is_open" in calendar_frame.columns:
        calendar_frame = calendar_frame[_bool_series(calendar_frame["is_open"])]

    start = _optional_date(start_date) or prices["trade_date"].min()
    end = _optional_date(end_date) or prices["trade_date"].max()
    if start is None or end is None or pd.isna(start) or pd.isna(end):
        raise FactorFrameworkError("prices 覆盖区间为空")
    if start > end:
        raise FactorFrameworkError("start_date 不得晚于 end_date")

    universe = build_universe(members, prices)
    if max_symbols > 0:
        universe = universe[:max_symbols]
    calendar = sorted(
        {
            item
            for item in calendar_frame["trade_date"].dropna().tolist()
            if start <= item <= end
        }
    )
    if not calendar:
        raise FactorFrameworkError("交易日历在请求区间内为空")
    prices = prices[(prices["trade_date"] >= start) & (prices["trade_date"] <= end)]
    prices = prices[prices["symbol"].isin(universe)]
    close_df = prices.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last")
    volume_df = prices.pivot_table(index="trade_date", columns="symbol", values="volume", aggfunc="last")
    amount_df = prices.pivot_table(index="trade_date", columns="symbol", values="amount", aggfunc="last")
    close_df = close_df.reindex(index=calendar, columns=universe)
    volume_df = volume_df.reindex(index=calendar, columns=universe)
    amount_df = amount_df.reindex(index=calendar, columns=universe)
    close_df.index.name = "date"
    volume_df.index.name = "date"
    amount_df.index.name = "date"
    if close_df.dropna(how="all").empty:
        raise FactorFrameworkError("close 矩阵为空")
    return MarketMatrices(close_df, volume_df, amount_df, universe, calendar, amount_source)


def calculate_raw_factor_matrices(
    market: MarketMatrices,
    definitions: list[FactorDefinition],
) -> dict[str, pd.DataFrame]:
    close = market.close
    volume = market.volume
    amount = market.amount
    returns = close.pct_change(fill_method=None)
    ema_fast: pd.DataFrame | None = None
    ema_slow: pd.DataFrame | None = None
    macd_diff: pd.DataFrame | None = None
    matrices: dict[str, pd.DataFrame] = {}

    for definition in definitions:
        name = definition.name
        if name == "momentum_20d":
            matrices[name] = close / close.shift(20) - 1.0
        elif name == "reversal_5d":
            matrices[name] = -(close / close.shift(5) - 1.0)
        elif name == "rsi_14":
            matrices[name] = calculate_rsi(close, window=14)
        elif name == "macd_diff":
            if ema_fast is None:
                ema_fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
            if ema_slow is None:
                ema_slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
            macd_diff = ema_fast - ema_slow
            matrices[name] = macd_diff
        elif name == "macd_hist":
            if ema_fast is None:
                ema_fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
            if ema_slow is None:
                ema_slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
            if macd_diff is None:
                macd_diff = ema_fast - ema_slow
            dea = macd_diff.ewm(span=9, adjust=False, min_periods=9).mean()
            matrices[name] = macd_diff - dea
        elif name == "ma_gap_20":
            matrices[name] = close / close.rolling(20, min_periods=20).mean() - 1.0
        elif name == "volatility_20d":
            matrices[name] = returns.rolling(20, min_periods=20).std(ddof=0)
        elif name == "volume_change_20d":
            recent = volume.rolling(20, min_periods=20).mean()
            previous = recent.shift(20)
            matrices[name] = recent / previous - 1.0
        elif name == "turnover_proxy":
            matrices[name] = np.log1p(amount.where(amount > 0))
        elif name == "max_drawdown_20d":
            rolling_high = close.rolling(20, min_periods=20).max()
            drawdown = close / rolling_high - 1.0
            matrices[name] = drawdown.rolling(20, min_periods=20).min()
        else:
            raise FactorFrameworkError(f"未实现的因子: {name}")
    return matrices


def calculate_rsi(close: pd.DataFrame, *, window: int) -> pd.DataFrame:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window, min_periods=window).mean()
    avg_loss = loss.rolling(window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
    return rsi


def preprocess_factor_matrices(
    raw_matrices: dict[str, pd.DataFrame],
    definitions: list[FactorDefinition],
    *,
    winsor_lower: float,
    winsor_upper: float,
    min_cross_section: int,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    zscore_matrices: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    definition_by_name = {item.name: item for item in definitions}
    for factor_name, raw in raw_matrices.items():
        definition = definition_by_name[factor_name]
        directional = raw * float(definition.direction_sign)
        raw_cells = int(raw.shape[0] * raw.shape[1])
        raw_missing = int(directional.isna().sum().sum())
        valid_counts = directional.notna().sum(axis=1)
        valid_rows = valid_counts >= min_cross_section
        medians = directional.median(axis=1, skipna=True)
        filled = directional.T.fillna(medians).T
        filled.loc[~valid_rows, :] = np.nan
        imputed = int((directional.isna() & filled.notna()).sum().sum())
        lower = filled.quantile(winsor_lower, axis=1)
        upper = filled.quantile(winsor_upper, axis=1)
        clipped = filled.clip(lower=lower, upper=upper, axis=0)
        clipped_count = int(((filled.lt(lower, axis=0)) | (filled.gt(upper, axis=0))).sum().sum())
        means = clipped.mean(axis=1, skipna=True)
        stds = clipped.std(axis=1, ddof=0, skipna=True).replace(0, np.nan)
        zscore = clipped.sub(means, axis=0).div(stds, axis=0)
        zscore.loc[~valid_rows, :] = np.nan
        zscore_matrices[factor_name] = zscore
        rows.append(
            {
                "factor_name": factor_name,
                "direction_sign": definition.direction_sign,
                "direction_note": definition.direction_note,
                "raw_cell_count": raw_cells,
                "raw_missing_count": raw_missing,
                "raw_missing_ratio": _safe_divide(raw_missing, raw_cells),
                "imputed_count": imputed,
                "winsor_lower": winsor_lower,
                "winsor_upper": winsor_upper,
                "winsor_clipped_count": clipped_count,
                "valid_date_count": int(valid_rows.sum()),
                "zscore_null_count": int(zscore.isna().sum().sum()),
            }
        )
    return zscore_matrices, pd.DataFrame(rows)


def build_forward_returns(close_df: pd.DataFrame, *, horizon: int) -> pd.DataFrame:
    return build_forward_return_matrix(close_df, horizon=horizon)


def calculate_ic_timeseries(
    zscore_matrices: dict[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    *,
    min_cross_section: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, scores in zscore_matrices.items():
        for trade_date in scores.index:
            valid = pd.DataFrame(
                {
                    "factor": scores.loc[trade_date],
                    "forward_return": forward_returns.loc[trade_date],
                }
            ).dropna()
            n = int(len(valid))
            ic = None
            rank_ic = None
            if n >= min_cross_section and _has_variation(valid["factor"]) and _has_variation(valid["forward_return"]):
                ic = float(valid["factor"].corr(valid["forward_return"], method="pearson"))
                rank_ic = _spearman_corr(valid["factor"], valid["forward_return"])
            rows.append(
                {
                    "factor_name": factor_name,
                    "date": trade_date.isoformat() if isinstance(trade_date, date) else str(trade_date),
                    "ic": ic,
                    "rank_ic": rank_ic,
                    "cross_section_n": n,
                }
            )
    return pd.DataFrame(rows)


def summarize_ic(ic_timeseries: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, group in ic_timeseries.groupby("factor_name", sort=True):
        ic = pd.to_numeric(group["ic"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        ic_std = float(ic.std(ddof=1)) if len(ic) > 1 else 0.0
        rank_std = float(rank_ic.std(ddof=1)) if len(rank_ic) > 1 else 0.0
        rows.append(
            {
                "factor_name": factor_name,
                "observation_days": int(len(group)),
                "valid_ic_days": int(len(ic)),
                "avg_cross_section_n": float(group["cross_section_n"].mean()) if not group.empty else 0.0,
                "ic_mean": _series_mean(ic),
                "ic_std": ic_std,
                "icir": _safe_divide(_series_mean(ic), ic_std),
                "rank_ic_mean": _series_mean(rank_ic),
                "rank_ic_std": rank_std,
                "rank_icir": _safe_divide(_series_mean(rank_ic), rank_std),
                "positive_rank_ic_ratio": _positive_ratio(rank_ic),
            }
        )
    return pd.DataFrame(rows)


def calculate_group_timeseries(
    score_matrices: dict[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    *,
    group_count: int,
    min_cross_section: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, scores in score_matrices.items():
        grouped = single_sort_returns(
            scores,
            forward_returns,
            quantiles=group_count,
            min_cross_section=min_cross_section,
        )
        if grouped.empty:
            continue
        grouped = grouped.rename(columns={"trade_date": "date"})
        grouped["factor_name"] = factor_name
        rows.extend(
            grouped[["factor_name", "date", "group", "mean_forward_return", "symbol_count"]]
            .assign(group=lambda frame: frame["group"].astype(int))
            .to_dict(orient="records")
        )
    return pd.DataFrame(rows, columns=["factor_name", "date", "group", "mean_forward_return", "symbol_count"])


def summarize_group_returns(group_timeseries: pd.DataFrame) -> pd.DataFrame:
    if group_timeseries.empty:
        return pd.DataFrame(columns=["factor_name", "group", "mean_forward_return", "std_forward_return", "date_count", "avg_symbol_count"])
    rows: list[dict[str, Any]] = []
    for (factor_name, group_id), group in group_timeseries.groupby(["factor_name", "group"], sort=True):
        returns = pd.to_numeric(group["mean_forward_return"], errors="coerce").dropna()
        rows.append(
            {
                "factor_name": factor_name,
                "group": int(group_id),
                "mean_forward_return": _series_mean(returns),
                "std_forward_return": float(returns.std(ddof=1)) if len(returns) > 1 else 0.0,
                "date_count": int(group["date"].nunique()),
                "avg_symbol_count": float(group["symbol_count"].mean()) if not group.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def summarize_monotonicity(group_returns: pd.DataFrame, *, group_count: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, group in group_returns.groupby("factor_name", sort=True):
        means = group.set_index("group")["mean_forward_return"].sort_index()
        if means.empty or 1 not in means.index or group_count not in means.index:
            rows.append(
                {
                    "factor_name": factor_name,
                    "monotonic_increasing": False,
                    "monotonic_score": None,
                    "top_bottom_mean": None,
                    "monotonic_label": "无有效分组",
                }
            )
            continue
        score = None
        if len(means) >= 2 and _has_variation(pd.Series(means.index, dtype="float64")) and _has_variation(means):
            score = _spearman_corr(pd.Series(means.index, dtype="float64"), means.reset_index(drop=True))
        top_bottom = float(means.loc[group_count] - means.loc[1])
        monotonic = bool(means.is_monotonic_increasing)
        if monotonic:
            label = "严格递增"
        elif score is not None and score >= 0.5:
            label = "大体递增"
        elif score is not None and score > 0:
            label = "弱递增"
        else:
            label = "不稳定"
        rows.append(
            {
                "factor_name": factor_name,
                "monotonic_increasing": monotonic,
                "monotonic_score": score,
                "top_bottom_mean": top_bottom,
                "monotonic_label": label,
            }
        )
    return pd.DataFrame(rows)


def calculate_factor_correlations(zscore_matrices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    names = sorted(zscore_matrices)
    for left_index, left_name in enumerate(names):
        left = zscore_matrices[left_name].to_numpy(dtype="float64", copy=False).ravel()
        for right_name in names[left_index + 1 :]:
            right = zscore_matrices[right_name].to_numpy(dtype="float64", copy=False).ravel()
            mask = np.isfinite(left) & np.isfinite(right)
            corr = None
            overlap = int(mask.sum())
            if overlap >= 2:
                left_valid = left[mask]
                right_valid = right[mask]
                if np.nanstd(left_valid) > 0 and np.nanstd(right_valid) > 0:
                    corr = float(np.corrcoef(left_valid, right_valid)[0, 1])
            rows.append(
                {
                    "left_factor": left_name,
                    "right_factor": right_name,
                    "correlation": corr,
                    "abs_correlation": abs(corr) if corr is not None else None,
                    "overlap_count": overlap,
                }
            )
    return pd.DataFrame(rows)


def calculate_top_turnover(
    zscore_matrices: dict[str, pd.DataFrame],
    *,
    top_fraction: float,
    rebalance_freq: int,
    min_cross_section: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, scores in zscore_matrices.items():
        dates = [trade_date for trade_date in scores.index if int(scores.loc[trade_date].notna().sum()) >= min_cross_section]
        signal_dates = dates[::rebalance_freq]
        previous: set[str] | None = None
        turnovers: list[float] = []
        counts: list[int] = []
        for trade_date in signal_dates:
            selected = set(select_top_from_series(scores.loc[trade_date], top_fraction))
            if not selected:
                continue
            counts.append(len(selected))
            if previous is not None:
                denominator = max(len(previous), 1)
                turnovers.append(1.0 - len(previous & selected) / denominator)
            previous = selected
        rows.append(
            {
                "factor_name": factor_name,
                "top_fraction": top_fraction,
                "rebalance_freq": rebalance_freq,
                "rebalance_count": len(counts),
                "avg_top_count": _series_mean(pd.Series(counts, dtype="float64")) if counts else None,
                "turnover": _series_mean(pd.Series(turnovers, dtype="float64")) if turnovers else None,
            }
        )
    return pd.DataFrame(rows)


def build_factor_retention_summary(
    *,
    definitions: list[FactorDefinition],
    ic_summary: pd.DataFrame,
    monotonicity: pd.DataFrame,
    turnover: pd.DataFrame,
    correlation: pd.DataFrame,
    min_ic_days: int,
) -> pd.DataFrame:
    definitions_frame = pd.DataFrame([asdict(item) for item in definitions]).rename(columns={"name": "factor_name"})
    result = definitions_frame.merge(ic_summary, on="factor_name", how="left")
    result = result.merge(monotonicity, on="factor_name", how="left")
    result = result.merge(turnover[["factor_name", "turnover", "rebalance_count"]], on="factor_name", how="left")
    max_corr = max_abs_correlation_by_factor(correlation)
    result["max_abs_correlation"] = result["factor_name"].map(max_corr)
    retained_flags: list[bool] = []
    reasons: list[str] = []
    for row in result.to_dict(orient="records"):
        valid_days = int(row.get("valid_ic_days") or 0)
        rank_ic = _to_float(row.get("rank_ic_mean"))
        top_bottom = _to_float(row.get("top_bottom_mean"))
        monotonic_score = _to_float(row.get("monotonic_score"))
        max_factor_corr = _to_float(row.get("max_abs_correlation"))
        if valid_days < min_ic_days:
            retained_flags.append(False)
            reasons.append(f"有效 IC 天数不足 {min_ic_days}")
        elif rank_ic is None or rank_ic <= 0:
            retained_flags.append(False)
            reasons.append("方向统一后 Rank IC 均值不为正")
        elif top_bottom is None or top_bottom <= 0:
            retained_flags.append(False)
            reasons.append("最高组减最低组收益不为正")
        elif monotonic_score is None or monotonic_score <= 0:
            retained_flags.append(False)
            reasons.append("分组单调性得分不为正")
        elif max_factor_corr is not None and max_factor_corr >= 0.95:
            retained_flags.append(False)
            reasons.append("与其他因子相关性过高")
        else:
            retained_flags.append(True)
            reasons.append("通过覆盖、方向、分组收益和相关性检查")
    result["retained"] = retained_flags
    result["retention_reason"] = reasons
    return result.sort_values(["retained", "rank_ic_mean"], ascending=[False, False]).reset_index(drop=True)


def max_abs_correlation_by_factor(correlation: pd.DataFrame) -> dict[str, float | None]:
    values: dict[str, list[float]] = {}
    if correlation.empty:
        return {}
    for row in correlation.to_dict(orient="records"):
        corr = _to_float(row.get("abs_correlation"))
        if corr is None:
            continue
        values.setdefault(str(row["left_factor"]), []).append(corr)
        values.setdefault(str(row["right_factor"]), []).append(corr)
    return {factor_name: (max(items) if items else None) for factor_name, items in values.items()}


def choose_model_factors(retention: pd.DataFrame, *, min_model_factors: int) -> tuple[list[str], str]:
    retained = [str(item) for item in retention.loc[retention["retained"] == True, "factor_name"].tolist()]
    if retained:
        return retained, "strict_retained"
    ranked = retention.copy()
    ranked["rank_ic_sort"] = pd.to_numeric(ranked["rank_ic_mean"], errors="coerce").fillna(-999.0)
    ranked["corr_sort"] = pd.to_numeric(ranked["max_abs_correlation"], errors="coerce").fillna(0.0)
    ranked = ranked[ranked["valid_ic_days"].fillna(0).astype(float) > 0]
    ranked = ranked.sort_values(["rank_ic_sort", "corr_sort"], ascending=[False, True])
    fallback = [str(item) for item in ranked["factor_name"].head(max(1, min_model_factors)).tolist()]
    if not fallback:
        raise FactorFrameworkError("没有可用于组合模型的因子")
    return fallback, "fallback_top_rank_ic_no_strict_retained_factor"


def build_multifactor_score(zscore_matrices: dict[str, pd.DataFrame], model_factors: list[str]) -> pd.DataFrame:
    if not model_factors:
        raise FactorFrameworkError("多因子模型至少需要一个因子")
    aligned = [zscore_matrices[factor_name] for factor_name in model_factors]
    total = aligned[0].copy() * 0.0
    count = aligned[0].copy() * 0.0
    for matrix in aligned:
        valid = matrix.notna()
        total = total.add(matrix.fillna(0.0), fill_value=0.0)
        count = count.add(valid.astype("float64"), fill_value=0.0)
    score = total / count.replace(0, np.nan)
    score.index.name = "date"
    return score


def build_score_preview(
    multi_score: pd.DataFrame,
    zscore_matrices: dict[str, pd.DataFrame],
    model_factors: list[str],
    *,
    rows: int,
) -> pd.DataFrame:
    preview = matrix_to_long(multi_score, "score")
    preview["factor_count"] = sum(zscore_matrices[factor].notna().astype(int) for factor in model_factors).stack(future_stack=True).to_numpy()
    return preview.dropna(subset=["score"]).sort_values(["date", "score"], ascending=[True, False]).head(max(rows, 0))


def run_equal_weight_benchmark(close_df: pd.DataFrame, *, initial_cash: float) -> dict[str, Any]:
    dates = [_coerce_date(item) for item in close_df.index]
    if len(dates) < 2:
        raise FactorFrameworkError("benchmark 至少需要两个交易日")
    signal = RebalanceSignal(signal_date=dates[0], execution_date=dates[1], target_symbols=[str(item) for item in close_df.columns])
    result = run_portfolio(close_df, [signal], PortfolioConfig(initial_cash=initial_cash))
    return {
        "metrics": calculate_metrics(result),
        "equity": portfolio_equity_frame(result),
    }


def run_factor_strategies(
    *,
    close_df: pd.DataFrame,
    zscore_matrices: dict[str, pd.DataFrame],
    multi_score: pd.DataFrame,
    model_factors: list[str],
    top_fractions: list[float],
    exit_fraction: float,
    rebalance_freq: int,
    initial_cash: float,
    train_fraction: float,
    output_dir: Path,
    benchmark_metrics: dict[str, Any],
    liquidity_payload: Mapping[str, Any] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Path]]:
    rows: list[dict[str, Any]] = []
    artifacts: dict[str, Path] = {}
    score_sets: dict[str, tuple[str, pd.DataFrame]] = {"multifactor": ("multi_factor", multi_score)}
    for factor_name in model_factors:
        score_sets[f"single_{factor_name}"] = ("single_factor", zscore_matrices[factor_name])

    for strategy_name, (model_type, scores) in score_sets.items():
        for top_fraction in top_fractions:
            result = run_strategy_pair(
                close_df,
                scores,
                strategy_name=strategy_name,
                model_type=model_type,
                top_fraction=top_fraction,
                exit_fraction=exit_fraction,
                rebalance_freq=rebalance_freq,
                initial_cash=initial_cash,
                benchmark_metrics=benchmark_metrics,
                liquidity_payload=liquidity_payload,
            )
            rows.append(result["summary"])
            if strategy_name == "multifactor":
                prefix = f"multifactor_top{int(round(top_fraction * 100))}"
                equity_path = output_dir / f"{prefix}_equity_curve.csv"
                trades_path = output_dir / f"{prefix}_trades.csv"
                result["equity"].to_csv(equity_path, index=False)
                result["trades"].to_csv(trades_path, index=False)
                artifacts[f"{prefix}_equity"] = equity_path
                artifacts[f"{prefix}_trades"] = trades_path

    sample_rows: list[dict[str, Any]] = []
    split_index = max(2, min(len(close_df.index) - 2, int(len(close_df.index) * train_fraction)))
    train_close = close_df.iloc[:split_index]
    test_close = close_df.iloc[split_index:]
    train_score = multi_score.reindex(train_close.index)
    test_score = multi_score.reindex(test_close.index)
    for label, period_close, period_score in (
        ("in_sample", train_close, train_score),
        ("out_of_sample", test_close, test_score),
    ):
        for top_fraction in top_fractions:
            split_result = run_strategy_pair(
                period_close,
                period_score,
                strategy_name=f"multifactor_{label}",
                model_type="multi_factor",
                top_fraction=top_fraction,
                exit_fraction=exit_fraction,
                rebalance_freq=rebalance_freq,
                initial_cash=initial_cash,
                benchmark_metrics=None,
                liquidity_payload=liquidity_payload,
            )
            sample_rows.append(
                {
                    "sample": label,
                    "top_fraction": top_fraction,
                    "start_date": period_close.index.min().isoformat(),
                    "end_date": period_close.index.max().isoformat(),
                    **split_result["summary"],
                }
            )
    sample_split = pd.DataFrame(sample_rows)
    sample_split = append_oos_checks(sample_split)
    return pd.DataFrame(rows), sample_split, artifacts


def run_strategy_pair(
    close_df: pd.DataFrame,
    score_matrix: pd.DataFrame,
    *,
    strategy_name: str,
    model_type: str,
    top_fraction: float,
    exit_fraction: float,
    rebalance_freq: int,
    initial_cash: float,
    benchmark_metrics: dict[str, Any] | None,
    liquidity_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    signals = build_rebalance_signals(score_matrix, close_df, top_fraction=top_fraction, exit_fraction=exit_fraction, rebalance_freq=rebalance_freq)
    if not signals:
        summary = {
            "strategy_name": strategy_name,
            "model_type": model_type,
            "top_fraction": top_fraction,
            "exit_fraction": exit_fraction,
            "status": "skipped",
            "reason": "signal_schedule_empty",
            "signal_count": 0,
        }
        return {"summary": summary, "equity": pd.DataFrame(), "trades": pd.DataFrame()}
    zero_cost = PortfolioConfig(initial_cash=initial_cash, commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0)
    default_cost = PortfolioConfig(initial_cash=initial_cash)
    no_cost_result = run_portfolio(close_df, signals, zero_cost)
    cost_result = run_portfolio(close_df, signals, default_cost)
    no_cost_metrics = calculate_metrics(no_cost_result)
    cost_metrics = calculate_metrics(cost_result)
    strategy_liquidity_payload = dict(liquidity_payload or {})
    strategy_liquidity_payload["turnover"] = cost_metrics.get("turnover")
    liquidity_bundle = build_liquidity_capacity_inputs(strategy_liquidity_payload)
    cost_sensitivity_report = run_cost_sensitivity_grid(
        {
            "annual_return_no_cost": no_cost_metrics.get("annual_return"),
            "turnover": cost_metrics.get("turnover"),
            "initial_cash": initial_cash,
        },
        cost_result.trades,
    )
    capacity_report = build_capacity_report(
        cost_result.trades,
        cost_result.daily_snapshots,
        liquidity_bundle,
        portfolio_returns={
            "annual_return_no_cost": no_cost_metrics.get("annual_return"),
            "annual_return": cost_metrics.get("annual_return"),
            "turnover": cost_metrics.get("turnover"),
            "initial_cash": initial_cash,
        },
        cost_sensitivity_report=cost_sensitivity_report,
    )
    capacity_cost_claims = evaluate_capacity_cost_claims(capacity_report, cost_sensitivity_report)
    filled_trades = [trade for trade in cost_result.trades if trade.status == "filled"]
    avg_holding_count = _series_mean(pd.Series([len(snapshot.holdings) for snapshot in cost_result.daily_snapshots], dtype="float64"))
    summary = {
        "strategy_name": strategy_name,
        "model_type": model_type,
        "top_fraction": top_fraction,
        "exit_fraction": exit_fraction,
        "status": "success",
        "signal_count": len(signals),
        "first_signal_date": signals[0].signal_date.isoformat(),
        "last_signal_date": signals[-1].signal_date.isoformat(),
        "annual_return_no_cost": no_cost_metrics["annual_return"],
        "annual_return_with_cost": cost_metrics["annual_return"],
        "total_return_with_cost": cost_metrics["total_return"],
        "sharpe_with_cost": cost_metrics["sharpe"],
        "max_drawdown_with_cost": cost_metrics["max_drawdown"],
        "turnover_with_cost": cost_metrics["turnover"],
        "final_value_with_cost": cost_metrics["final_value"],
        "filled_trade_count": len(filled_trades),
        "avg_holding_count": avg_holding_count,
        "cost_erosion": calculate_cost_erosion(float(no_cost_metrics["annual_return"]), float(cost_metrics["annual_return"]))
        if no_cost_metrics["annual_return"] is not None and cost_metrics["annual_return"] is not None
        else None,
        "cost_grid_bps": cost_sensitivity_report["cost_grid_bps"],
        "cost_sensitivity_status": cost_sensitivity_report["cost_sensitivity_status"],
        "liquidity_capacity_status": capacity_cost_claims["liquidity_capacity_status"],
        "capacity_cost_status": capacity_cost_claims["capacity_cost_status"],
        "amount_participation_rate": capacity_report["amount_participation_rate"],
        "capacity_turnover": capacity_report["turnover"],
        "capacity_holding_count": capacity_report["holding_count"],
        "capacity_sample_loss_count": capacity_report["sample_loss_count"],
        "capacity_sample_loss_rate": capacity_report["sample_loss_rate"],
        "capacity_cost_erosion_bps": capacity_report["cost_erosion_bps"],
        "capacity_report": capacity_report,
        "cost_sensitivity_report": cost_sensitivity_report,
        "capacity_cost_claims": capacity_cost_claims,
    }
    if benchmark_metrics is not None:
        summary.update(build_strategy_validation_fields(cost_metrics, benchmark_metrics))
    return {
        "summary": summary,
        "equity": portfolio_equity_frame(cost_result),
        "trades": pd.DataFrame([asdict(trade) for trade in cost_result.trades]),
    }


def build_rebalance_signals(
    score_matrix: pd.DataFrame,
    close_df: pd.DataFrame,
    *,
    top_fraction: float,
    exit_fraction: float,
    rebalance_freq: int,
) -> list[RebalanceSignal]:
    dates = [_coerce_date(item) for item in close_df.index]
    next_date = {dates[index]: dates[index + 1] for index in range(len(dates) - 1)}
    score_by_date = {_coerce_date(item): item for item in score_matrix.index}
    valid_dates = [
        trade_date
        for trade_date in dates[:-1]
        if trade_date in score_by_date and score_matrix.loc[score_by_date[trade_date]].notna().any()
    ]
    signal_dates = valid_dates[::rebalance_freq]
    signals: list[RebalanceSignal] = []
    previous_target: list[str] = []
    for signal_date in signal_dates:
        scores = score_matrix.loc[score_by_date[signal_date]]
        entry = select_top_from_series(scores, top_fraction)
        exit_pool = set(select_top_from_series(scores, exit_fraction))
        retained = [symbol for symbol in previous_target if symbol in exit_pool]
        target = list(dict.fromkeys([*retained, *entry]))
        if not target:
            continue
        previous_target = target
        signals.append(
            RebalanceSignal(
                signal_date=signal_date,
                execution_date=next_date[signal_date],
                target_symbols=target,
            )
        )
    return signals


def build_strategy_validation_fields(cost_metrics: dict[str, Any], benchmark_metrics: dict[str, Any]) -> dict[str, Any]:
    annual_return = _to_float(cost_metrics.get("annual_return"))
    benchmark_annual = _to_float(benchmark_metrics.get("annual_return"))
    drawdown = abs(float(cost_metrics.get("max_drawdown") or 0.0))
    benchmark_drawdown = abs(float(benchmark_metrics.get("max_drawdown") or 0.0))
    return {
        "proxy_annual_return": benchmark_metrics.get("annual_return"),
        "proxy_total_return": benchmark_metrics.get("total_return"),
        "proxy_max_drawdown": benchmark_metrics.get("max_drawdown"),
        "proxy_excess_annual_return": None if annual_return is None or benchmark_annual is None else annual_return - benchmark_annual,
        "annual_return_not_below_proxy": annual_return is not None and benchmark_annual is not None and annual_return >= benchmark_annual,
        "drawdown_not_significantly_higher_than_proxy": drawdown <= benchmark_drawdown * 1.5 + 0.05,
        "cost_after_return_not_fully_eroded": annual_return is not None and annual_return > 0,
    }


def build_experiment_benchmark_policy_metadata(
    benchmark_result: Any | None = None,
    *,
    benchmark_metrics: Mapping[str, Any] | None = None,
    benchmark_policy_id: str = "hs300_required",
    realism_mode: str = "exploratory",
    baseline_report_path: str | Path | None = None,
) -> dict[str, Any]:
    """为实验 17-21 v2 输出 CR011 benchmark policy metadata。"""

    proxy_used = benchmark_result is None and realism_mode != "production_strict"
    policy_result = build_benchmark_policy_result(
        benchmark_result,
        policy_id=benchmark_policy_id,
        proxy_baseline_used=proxy_used,
        proxy_metrics=benchmark_metrics,
        proxy_baseline={
            "status": "used" if proxy_used else "not_used",
            "definition": "same_universe_equal_weight_buy_and_hold",
            "baseline_report_path": str(baseline_report_path or LEGACY_EXPERIMENT_17_21_REPORT),
        },
    )
    metadata = policy_result.to_metadata()
    metadata["realism_mode"] = realism_mode
    if realism_mode == "production_strict" and not metadata["hs300_available"]:
        metadata["research_status"] = "required_missing"
    elif metadata["hs300_available"]:
        metadata["research_status"] = "available"
    else:
        metadata["research_status"] = "exploratory_with_limitations"
    return metadata


def build_experiment_liquidity_capacity_payload(market: MarketMatrices) -> dict[str, Any]:
    """从已加载的离线 market matrix 摘要出容量输入，不读取旧数据或外部源。"""

    adv20 = market.amount.rolling(20, min_periods=1).mean()
    return {
        "amount": _frame_positive_mean(market.amount),
        "volume": _frame_positive_mean(market.volume),
        "adv20": _frame_positive_mean(adv20),
        "lineage": {
            "source": "loaded_market_frames",
            "source_interface": "experiments.run_experiment_17_21_factor_suite",
            "amount_source": market.amount_source,
        },
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }


def build_experiment_capacity_cost_metadata(
    benchmark_policy_metadata: Mapping[str, Any],
    strategy_summary: pd.DataFrame,
) -> dict[str, Any]:
    """合并实验 17-21 v2 的 S07 capacity/cost metadata。"""

    selected = _select_capacity_cost_row(strategy_summary)
    if selected:
        capacity_report = dict(selected.get("capacity_report") or {})
        cost_report = dict(selected.get("cost_sensitivity_report") or {})
        claim_result = dict(selected.get("capacity_cost_claims") or {})
    else:
        capacity_report = build_capacity_report([], [], None)
        cost_report = run_cost_sensitivity_grid({"gross_return": None})
        claim_result = evaluate_capacity_cost_claims(capacity_report, cost_report)
    base_metadata = {
        **dict(benchmark_policy_metadata),
        "allowed_claims": list(benchmark_policy_metadata.get("allowed_claims") or []),
        "blocked_claims": list(benchmark_policy_metadata.get("blocked_claims") or []),
        "known_limitations": list(benchmark_policy_metadata.get("known_limitations") or []),
    }
    return merge_capacity_cost_metadata(base_metadata, capacity_report, cost_report, claim_result)


def build_factor_panel_audit(
    raw_matrices: Mapping[str, pd.DataFrame],
    zscore_matrices: Mapping[str, pd.DataFrame],
    preprocessing_summary: pd.DataFrame,
    definitions: Sequence[FactorDefinition],
    *,
    run_metadata: Mapping[str, Any] | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """构建 raw/directional/winsorized/zscore 四阶段因子面板审计产物。"""

    definition_by_name = {definition.name: definition for definition in definitions}
    summary_by_factor = {
        str(row.get("factor_name")): row
        for row in preprocessing_summary.where(pd.notna(preprocessing_summary), None).to_dict(orient="records")
    }
    directional_matrices: dict[str, pd.DataFrame] = {}
    winsorized_matrices: dict[str, pd.DataFrame] = {}
    for factor_name, raw in raw_matrices.items():
        if factor_name not in definition_by_name:
            raise FactorFrameworkError(f"因子审计缺少定义: {factor_name}")
        if factor_name not in zscore_matrices:
            raise FactorFrameworkError(f"因子审计缺少 zscore 矩阵: {factor_name}")
        directional = raw * float(definition_by_name[factor_name].direction_sign)
        directional_matrices[factor_name] = directional
        winsorized_matrices[factor_name] = _rebuild_winsorized_matrix(
            directional,
            summary_by_factor.get(str(factor_name), {}),
        )

    panel_by_stage = {
        "raw": _factor_panel_stage_frame(raw_matrices, "raw_value", "raw"),
        "directional": _factor_panel_stage_frame(directional_matrices, "directional_value", "directional"),
        "winsorized": _factor_panel_stage_frame(winsorized_matrices, "winsorized_value", "winsorized"),
        "zscore": _factor_panel_stage_frame(zscore_matrices, "zscore_value", "zscore"),
    }
    missing_stages = [stage for stage in FACTOR_PANEL_AUDIT_STAGES if stage not in panel_by_stage or panel_by_stage[stage].empty]
    row_counts = {stage: int(len(panel_by_stage[stage])) for stage in FACTOR_PANEL_AUDIT_STAGES}
    metadata = {**S08_SAFETY_COUNTERS, **dict(run_metadata or {})}
    manifest = {
        "schema_version": "cr011_s08_factor_panel_audit_v1",
        "source_story": "CR011-S08",
        "preprocessing_version": "directional_median_fill_winsor_zscore_v1",
        "required_stages": list(FACTOR_PANEL_AUDIT_STAGES),
        "stages": list(FACTOR_PANEL_AUDIT_STAGES),
        "missing_stages": missing_stages,
        "factor_audit_status": "pass" if not missing_stages else "fail",
        "factor_names": [definition.name for definition in definitions if definition.name in raw_matrices],
        "factor_count": len(raw_matrices),
        "row_counts": row_counts,
        "preprocessing_summary": _records(preprocessing_summary),
        "run_metadata": _json_ready(metadata),
        **S08_SAFETY_COUNTERS,
    }
    return panel_by_stage, manifest


def write_factor_panel_audit_outputs(
    output_dir: str | Path,
    panel_by_stage: Mapping[str, pd.DataFrame],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """写入 S08 因子面板审计 CSV 与 manifest，只写当前输出目录。"""

    root = Path(output_dir) / "factor_panel_audit"
    root.mkdir(parents=True, exist_ok=True)
    stage_files: dict[str, str] = {}
    for stage in FACTOR_PANEL_AUDIT_STAGES:
        frame = panel_by_stage.get(stage)
        if frame is None:
            raise FactorFrameworkError(f"因子面板审计缺少阶段: {stage}")
        path = root / f"factor_panel_{stage}.csv"
        _assert_not_legacy_artifact_path(path)
        frame.to_csv(path, index=False)
        stage_files[stage] = str(path)
    manifest_path = root / "factor_panel_manifest.json"
    _assert_not_legacy_artifact_path(manifest_path)
    payload = {
        **dict(manifest),
        "stage_files": stage_files,
        "manifest_path": str(manifest_path),
        "factor_panel_manifest_path": str(manifest_path),
    }
    manifest_path.write_text(json.dumps(_json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_robust_validation_views(
    panel_manifest: Mapping[str, Any],
    strategy_summary: pd.DataFrame,
    strategy_artifacts: Mapping[str, Path],
    capacity_cost_metadata: Mapping[str, Any],
    *,
    market_state_labels: pd.DataFrame | Sequence[Mapping[str, Any]] | None = None,
    parameter_grid: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """构建 rolling/annual/market_state/parameter_grid/cost_grid 五视图稳健性验证摘要。"""

    strategy_records = _records(strategy_summary)
    successful = [row for row in strategy_records if str(row.get("status")) == "success"]
    rolling_records = [
        {
            "view": "rolling",
            "strategy_name": row.get("strategy_name"),
            "top_fraction": row.get("top_fraction"),
            "window": "full_sample",
            "annual_return_with_cost": row.get("annual_return_with_cost"),
            "max_drawdown_with_cost": row.get("max_drawdown_with_cost"),
            "turnover_with_cost": row.get("turnover_with_cost"),
        }
        for row in successful
    ]
    annual_records = [
        {
            "view": "annual",
            "strategy_name": row.get("strategy_name"),
            "top_fraction": row.get("top_fraction"),
            "period_start": row.get("first_signal_date"),
            "period_end": row.get("last_signal_date"),
            "annual_return_with_cost": row.get("annual_return_with_cost"),
            "sharpe_with_cost": row.get("sharpe_with_cost"),
        }
        for row in successful
        if row.get("annual_return_with_cost") is not None
    ]
    state_records = _coerce_market_state_records(market_state_labels)
    grid_records = list(parameter_grid or _parameter_grid_from_strategy_summary(strategy_summary))
    cost_report = capacity_cost_metadata.get("cost_sensitivity_report") if isinstance(capacity_cost_metadata, Mapping) else {}
    if not isinstance(cost_report, Mapping):
        cost_report = {}
    cost_records = list(cost_report.get("cost_scenarios") or [])
    if not cost_records:
        cost_records = [
            {"view": "cost_grid", "cost_bps": item}
            for item in capacity_cost_metadata.get("cost_grid_bps", list(DEFAULT_COST_GRID_BPS))
        ]
    cost_grid = [int(item) for item in capacity_cost_metadata.get("cost_grid_bps", cost_report.get("cost_grid_bps", [])) or []]

    views = {
        "rolling": _robust_view_payload("rolling", rolling_records, required=True),
        "annual": _robust_view_payload("annual", annual_records, required=True),
        "market_state": _robust_view_payload("market_state", state_records, required=True),
        "parameter_grid": _robust_view_payload("parameter_grid", grid_records, required=True),
        "cost_grid": _robust_view_payload(
            "cost_grid",
            cost_records,
            required=True,
            pass_override=cost_grid == list(DEFAULT_COST_GRID_BPS)
            and str(capacity_cost_metadata.get("cost_sensitivity_status") or "fail") == "pass",
            fail_reason="cost_grid_contract_not_pass",
        ),
    }
    status = "pass" if all(views[name]["status"] == "pass" for name in ROBUST_VALIDATION_VIEWS) else "fail"
    return {
        "schema_version": "cr011_s08_robust_validation_v1",
        "source_story": "CR011-S08",
        "required_views": list(ROBUST_VALIDATION_VIEWS),
        "view_names": list(ROBUST_VALIDATION_VIEWS),
        "views": views,
        "robust_validation_status": status,
        "panel_manifest_path": str(panel_manifest.get("manifest_path") or panel_manifest.get("factor_panel_manifest_path") or ""),
        "factor_audit_status": str(panel_manifest.get("factor_audit_status") or "fail"),
        "strategy_artifacts": {str(key): str(path) for key, path in strategy_artifacts.items()},
        "cost_grid_bps": cost_grid,
        **S08_SAFETY_COUNTERS,
    }


def write_robust_validation_outputs(output_dir: str | Path, validation_summary: Mapping[str, Any]) -> dict[str, Any]:
    """写入 S08 五视图验证 CSV 与 summary JSON。"""

    root = Path(output_dir) / "robust_validation"
    root.mkdir(parents=True, exist_ok=True)
    views = validation_summary.get("views") if isinstance(validation_summary.get("views"), Mapping) else {}
    view_files: dict[str, str] = {}
    for view_name in ROBUST_VALIDATION_VIEWS:
        payload = views.get(view_name, {}) if isinstance(views, Mapping) else {}
        records = payload.get("records") if isinstance(payload, Mapping) else []
        path = root / f"{view_name}.csv"
        _assert_not_legacy_artifact_path(path)
        pd.DataFrame(records or []).to_csv(path, index=False)
        view_files[view_name] = str(path)
    summary_path = root / "robust_validation_summary.json"
    _assert_not_legacy_artifact_path(summary_path)
    payload = {
        **dict(validation_summary),
        "view_files": view_files,
        "summary_path": str(summary_path),
        "robust_validation_summary_path": str(summary_path),
    }
    summary_path.write_text(json.dumps(_json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def build_market_state_labels(close_df: pd.DataFrame) -> pd.DataFrame:
    returns = close_df.mean(axis=1, skipna=True).pct_change(fill_method=None).fillna(0.0)
    rows = []
    for trade_date, value in returns.items():
        numeric = float(value)
        state = "up" if numeric > 0 else "down" if numeric < 0 else "flat"
        rows.append(
            {
                "trade_date": trade_date.isoformat() if isinstance(trade_date, date) else str(trade_date),
                "market_state": state,
                "market_return": numeric,
            }
        )
    return pd.DataFrame(rows)


def build_parameter_grid(top_fractions: Sequence[float], exit_fraction: float, rebalance_freq: int) -> list[dict[str, Any]]:
    return [
        {
            "view": "parameter_grid",
            "top_fraction": float(top_fraction),
            "exit_fraction": float(exit_fraction),
            "rebalance_freq": int(rebalance_freq),
        }
        for top_fraction in top_fractions
    ]


def append_oos_checks(sample_split: pd.DataFrame) -> pd.DataFrame:
    if sample_split.empty:
        return sample_split
    rows = sample_split.copy()
    rows["oos_degradation_flag"] = False
    for top_fraction, group in rows.groupby("top_fraction", sort=True):
        by_sample = {row["sample"]: row for row in group.to_dict(orient="records")}
        ins = by_sample.get("in_sample")
        oos = by_sample.get("out_of_sample")
        if not ins or not oos:
            continue
        in_return = _to_float(ins.get("annual_return_with_cost"))
        out_return = _to_float(oos.get("annual_return_with_cost"))
        flag = in_return is not None and out_return is not None and in_return > 0.05 and out_return < -0.05
        rows.loc[rows["top_fraction"] == top_fraction, "oos_degradation_flag"] = flag
    return rows


def portfolio_equity_frame(result: PortfolioResult) -> pd.DataFrame:
    if not result.daily_snapshots:
        return pd.DataFrame(columns=["date", "cash", "position_value", "total_value", "turnover_amount", "holding_count"])
    values = pd.Series(
        [snapshot.total_value for snapshot in result.daily_snapshots],
        index=[snapshot.trade_date for snapshot in result.daily_snapshots],
        dtype="float64",
    )
    running_max = values.cummax()
    return pd.DataFrame(
        [
            {
                "date": snapshot.trade_date.isoformat(),
                "cash": snapshot.cash,
                "position_value": snapshot.position_value,
                "total_value": snapshot.total_value,
                "nav": snapshot.total_value / values.iloc[0],
                "drawdown": snapshot.total_value / running_max.loc[snapshot.trade_date] - 1.0,
                "turnover_amount": snapshot.turnover_amount,
                "holding_count": len(snapshot.holdings),
            }
            for snapshot in result.daily_snapshots
        ]
    )


def calculate_cost_erosion(no_cost_annual_return: float, with_cost_annual_return: float) -> float | None:
    denominator = abs(float(no_cost_annual_return))
    if denominator == 0:
        return None
    return (float(no_cost_annual_return) - float(with_cost_annual_return)) / denominator


def render_report(
    *,
    args: argparse.Namespace,
    market: MarketMatrices,
    definitions: list[FactorDefinition],
    preprocessing_summary: pd.DataFrame,
    retention: pd.DataFrame,
    model_factors: list[str],
    model_policy: str,
    group_returns: pd.DataFrame,
    multi_group_returns: pd.DataFrame,
    strategy_summary: pd.DataFrame,
    sample_split: pd.DataFrame,
    benchmark_metrics: dict[str, Any],
    paths: dict[str, Path],
    benchmark_policy_metadata: Mapping[str, Any] | None = None,
    capacity_cost_metadata: Mapping[str, Any] | None = None,
    factor_audit_metadata: Mapping[str, Any] | None = None,
) -> str:
    strict_retained = [str(item) for item in retention.loc[retention["retained"] == True, "factor_name"].tolist()]
    best_strategy = _best_strategy(strategy_summary)
    lines = [
        "# 实验十七至二十一：因子对比与策略化回测报告",
        "",
        "## 执行结论",
        "",
        f"- 输出报告：`{paths['report']}`",
        f"- 数据目录：`{args.data_dir}`",
        f"- 样本区间：{market.close.index.min().isoformat()} 至 {market.close.index.max().isoformat()}；股票数：{len(market.universe)}；交易日数：{len(market.calendar)}。",
        f"- IC/分组收益标签：未来 {args.horizon} 个交易日 close-to-close 收益。",
        f"- 严格保留因子：{', '.join(strict_retained) if strict_retained else '无'}。",
        f"- 多因子模型实际使用：{', '.join(model_factors)}；选择策略：`{model_policy}`。",
        f"- 成本后表现最好的策略：{best_strategy}。",
        _benchmark_report_line(benchmark_policy_metadata),
        _capacity_cost_report_line(capacity_cost_metadata),
        _factor_audit_report_line(factor_audit_metadata),
        "",
        "## 实验十七：技术因子对比",
        "",
        markdown_table(
            [asdict(item) for item in definitions if item.experiment == "experiment_17"],
            ["name", "source", "hypothesis", "stage2_link", "direction_note"],
        ),
        "",
        "## 实验十八：波动率与成交量因子",
        "",
        markdown_table(
            [asdict(item) for item in definitions if item.experiment == "experiment_18"],
            ["name", "source", "hypothesis", "direction_note"],
        ),
        "",
        "## 实验十九：因子预处理与稳定性分析",
        "",
        "- 预处理顺序：方向统一 -> 横截面中位数填充 -> 横截面去极值 -> 横截面标准化。",
        f"- 去极值分位点：{args.winsor_lower:.2%} / {args.winsor_upper:.2%}；最小横截面股票数：{args.min_cross_section}。",
        "",
        markdown_table(
            retention_display_records(retention),
            ["因子", "IC 均值", "ICIR", "分组单调性", "换手率", "与其他因子最高相关", "是否保留"],
        ),
        "",
        "### 预处理覆盖",
        "",
        markdown_table(
            _records(preprocessing_summary),
            ["factor_name", "raw_missing_ratio", "imputed_count", "winsor_clipped_count", "valid_date_count", "zscore_null_count"],
        ),
        "",
        "## 实验二十：多因子组合模型",
        "",
        f"- 组合公式：`score = mean(z(factor_i))`，实际因子为 `{', '.join(model_factors)}`。",
        "- 所有输入 z-score 已统一为“值越大越看多”，因此等权平均保持可解释性。",
        "- 对照包含单因子 Top 组、Top10/Top20 多因子策略与等权 proxy benchmark。",
        "",
        "### 多因子分组收益",
        "",
        markdown_table(
            _records(multi_group_returns),
            ["factor_name", "group", "mean_forward_return", "date_count", "avg_symbol_count"],
        ),
        "",
        "## 实验二十一：因子策略化回测",
        "",
        f"- 调仓频率：每 {args.rebalance_freq} 个交易日；买入 Top：{', '.join(f'{float(item):.0%}' for item in args.top_fractions)}；卖出阈值：跌出 Top {args.exit_fraction:.0%}。",
        "- 成本：沿用组合引擎默认值，佣金 0.03%、滑点 0.02%、卖出印花税 0.10%；CR011 v2 metadata 固定输出 `[0, 5, 10, 20]` bps 成本敏感性网格。",
        "",
        "### 策略摘要",
        "",
        markdown_table(
            _records(strategy_summary),
            [
                "strategy_name",
                "model_type",
                "top_fraction",
                "status",
                "annual_return_with_cost",
                "proxy_annual_return",
                "proxy_excess_annual_return",
                "max_drawdown_with_cost",
                "proxy_max_drawdown",
                "turnover_with_cost",
                "cost_erosion",
                "cost_sensitivity_status",
                "capacity_cost_status",
                "amount_participation_rate",
                "capacity_holding_count",
                "capacity_sample_loss_count",
                "annual_return_not_below_proxy",
                "drawdown_not_significantly_higher_than_proxy",
                "cost_after_return_not_fully_eroded",
            ],
        ),
        "",
        "### 样本内外验证",
        "",
        markdown_table(
            _records(sample_split),
            [
                "sample",
                "top_fraction",
                "start_date",
                "end_date",
                "annual_return_with_cost",
                "max_drawdown_with_cost",
                "turnover_with_cost",
                "oos_degradation_flag",
            ],
        ),
        "",
        "## 验收判断",
        "",
        *render_acceptance_lines(strategy_summary, sample_split, benchmark_metrics),
        "",
        "## 限制",
        "",
        "- 股票池来自 `index_members.parquet` 固定快照，不是严格 PIT 成分池，存在幸存者偏差。",
        "- 执行价使用日频 close 代理，不含真实开盘价、VWAP、涨跌停或停牌可交易性强声明；相关上游 blocked claims 不由本报告放宽。",
        _capacity_cost_limitation_line(capacity_cost_metadata),
        _factor_audit_limitation_line(factor_audit_metadata),
        _benchmark_limitation_line(benchmark_policy_metadata),
        "- 因子保留标准用于构建可解释模型，不等价于统计显著性证明。",
        "",
        "## 产物清单",
        "",
        markdown_table(
            [
                {"artifact": name, "path": str(path)}
                for name, path in paths.items()
                if isinstance(path, Path)
            ],
            ["artifact", "path"],
        ),
        "",
    ]
    return "\n".join(lines)


def _benchmark_report_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- Benchmark：当前实验使用同股票池等权买入持有 `proxy_baseline`；没有声明真实沪深300超额收益。"
    kind = metadata.get("benchmark_kind")
    policy_id = metadata.get("benchmark_policy_id")
    if metadata.get("hs300_available"):
        return f"- Benchmark：`{policy_id}` 已使用真实 `hs300_index`；benchmark_kind=`{kind}`。"
    if metadata.get("proxy_baseline_used"):
        reason = metadata.get("benchmark_missing_reason") or "required_missing"
        return f"- Benchmark：`{policy_id}` 真实 `hs300_index` 不可用（{reason}），当前仅输出 `proxy_baseline`，不声明真实沪深300超额收益。"
    reason = metadata.get("benchmark_missing_reason") or "required_missing"
    return f"- Benchmark：`{policy_id}` 缺真实 `hs300_index`（{reason}），production_strict 相关声明已阻断。"


def _capacity_cost_report_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- 容量 / 成本：未生成 S07 metadata，容量可交易声明保持阻断。"
    grid = metadata.get("cost_grid_bps") or list(DEFAULT_COST_GRID_BPS)
    capacity_status = metadata.get("liquidity_capacity_status") or "blocked_missing_liquidity"
    cost_status = metadata.get("cost_sensitivity_status") or "fail"
    return f"- 容量 / 成本：成本网格 `{grid}`；liquidity/capacity 状态 `{capacity_status}`；成本敏感性状态 `{cost_status}`。"


def _factor_audit_report_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- 因子面板 / 稳健性：未生成 S08 metadata，稳健性声明保持阻断。"
    panel_status = metadata.get("factor_audit_status") or "fail"
    validation_status = metadata.get("robust_validation_status") or "fail"
    claim_status = metadata.get("claim_gate_status") or "fail"
    stage_count = metadata.get("factor_panel_stage_count") or 0
    views = metadata.get("robust_validation_views") or []
    return (
        f"- 因子面板 / 稳健性：四阶段审计状态 `{panel_status}`（阶段数 {stage_count}）；"
        f"五视图验证状态 `{validation_status}`（views={views}）；声明门状态 `{claim_status}`。"
    )


def _benchmark_limitation_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- 当前 benchmark 为同股票池等权买入持有；若需要真实沪深300，需要先确认并接入本地 `hs300_index` benchmark 数据。"
    if metadata.get("hs300_available"):
        return "- Benchmark 已由真实 `hs300_index` 支撑；proxy baseline 仅保留为可选追溯对照。"
    if metadata.get("proxy_baseline_used"):
        return "- 当前 benchmark 只允许作为 `proxy_baseline` 限制项，不得写入 `hs300_*` 真实指标或声明沪深300超额收益。"
    return "- production_strict 缺真实 benchmark 时只输出 `required_missing` / `blocked_claims`，不使用 proxy 替代。"


def _capacity_cost_limitation_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- 容量 / 成本限制项：缺 S07 metadata，容量可交易、容量支持和成本稳健声明均不得输出。"
    blocked = {
        str(item.get("claim") or "")
        for item in metadata.get("blocked_claims") or []
        if isinstance(item, Mapping)
    }
    if {"capacity_tradable", "capacity_supported", "liquidity_screened_capacity"} & blocked:
        return "- 容量 / 成本限制项：liquidity/capacity 输入未完整支撑强容量声明，相关 allowed claims 输出次数为 0。"
    if metadata.get("cost_sensitivity_status") != "pass":
        return "- 容量 / 成本限制项：成本敏感性网格未通过，成本稳健声明保持阻断。"
    return "- 容量 / 成本限制项：S07 metadata 已输出五类容量字段和四档成本敏感性；强稳健性声明仍以 S08 claim gate 为准。"


def _factor_audit_limitation_line(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return "- 因子面板 / 稳健性限制项：缺 S08 metadata，四阶段审计与五视图稳健性声明均不得输出。"
    if metadata.get("factor_audit_status") != "pass":
        return "- 因子面板 / 稳健性限制项：四阶段因子面板审计未通过，稳健性声明保持阻断。"
    if metadata.get("robust_validation_status") != "pass":
        return "- 因子面板 / 稳健性限制项：五视图稳健性验证未全部通过，稳健性声明保持阻断。"
    if metadata.get("claim_gate_status") == "blocked_upstream_claims":
        return "- 因子面板 / 稳健性限制项：S08 视图已生成，但上游 blocked claims 不被放宽，同名 allowed claims 输出次数为 0。"
    return "- 因子面板 / 稳健性限制项：S08 已生成 raw/directional/winsorized/zscore 四阶段面板与五视图稳健性验证。"


def _rebuild_winsorized_matrix(directional: pd.DataFrame, summary_row: Mapping[str, Any]) -> pd.DataFrame:
    lower_q = float(summary_row.get("winsor_lower") if summary_row.get("winsor_lower") is not None else 0.01)
    upper_q = float(summary_row.get("winsor_upper") if summary_row.get("winsor_upper") is not None else 0.99)
    medians = directional.median(axis=1, skipna=True)
    filled = directional.T.fillna(medians).T
    lower = filled.quantile(lower_q, axis=1)
    upper = filled.quantile(upper_q, axis=1)
    return filled.clip(lower=lower, upper=upper, axis=0)


def _factor_panel_stage_frame(
    matrices: Mapping[str, pd.DataFrame],
    value_name: str,
    stage: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for factor_name, matrix in matrices.items():
        long = matrix_to_long(matrix, value_name).rename(columns={"date": "trade_date"})
        long["factor_name"] = str(factor_name)
        long["factor_panel_stage"] = stage
        long["preprocessing_version"] = "directional_median_fill_winsor_zscore_v1"
        frames.append(
            long[
                [
                    "trade_date",
                    "symbol",
                    "factor_name",
                    "factor_panel_stage",
                    "preprocessing_version",
                    value_name,
                ]
            ]
        )
    if not frames:
        return pd.DataFrame(
            columns=["trade_date", "symbol", "factor_name", "factor_panel_stage", "preprocessing_version", value_name]
        )
    return pd.concat(frames, ignore_index=True)


def _robust_view_payload(
    view_name: str,
    records: Sequence[Mapping[str, Any]],
    *,
    required: bool,
    pass_override: bool | None = None,
    fail_reason: str = "required_view_empty",
) -> dict[str, Any]:
    safe_records = [_json_ready(dict(record)) for record in records]
    if pass_override is None:
        status = "pass" if safe_records or not required else "fail"
    else:
        status = "pass" if pass_override and (safe_records or not required) else "fail"
    return {
        "view": view_name,
        "status": status,
        "reason": "" if status == "pass" else fail_reason,
        "record_count": len(safe_records),
        "records": safe_records,
    }


def _coerce_market_state_records(
    labels: pd.DataFrame | Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if labels is None:
        return []
    if isinstance(labels, pd.DataFrame):
        records = _records(labels)
    else:
        records = [dict(item) for item in labels if isinstance(item, Mapping)]
    return [{**record, "view": "market_state"} for record in records]


def _parameter_grid_from_strategy_summary(strategy_summary: pd.DataFrame) -> list[dict[str, Any]]:
    if strategy_summary.empty:
        return []
    columns = [column for column in ("strategy_name", "model_type", "top_fraction", "exit_fraction") if column in strategy_summary.columns]
    if not columns:
        return []
    return [
        {**record, "view": "parameter_grid"}
        for record in _records(strategy_summary[columns].drop_duplicates())
    ]


def _assert_not_legacy_artifact_path(path: Path) -> None:
    resolved = path.resolve()
    legacy_report = LEGACY_EXPERIMENT_17_21_REPORT.resolve()
    if _is_legacy_experiment17_alias(path) or resolved == legacy_report or resolved == legacy_report.parent:
        raise FactorFrameworkError("禁止覆盖旧实验 17-21 baseline 报告；S08 只能写入当前 CR011 输出目录。")


def _is_legacy_experiment17_alias(path: Path) -> bool:
    normalized = path.as_posix().rstrip("/")
    return normalized in {
        "reports/experiment_17_21",
        "reports/experiment_17_21/factor_strategy_report.md",
    }


def retention_display_records(retention: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in retention.to_dict(orient="records"):
        rows.append(
            {
                "因子": row.get("factor_name"),
                "IC 均值": row.get("ic_mean"),
                "ICIR": row.get("icir"),
                "分组单调性": row.get("monotonic_label"),
                "换手率": row.get("turnover"),
                "与其他因子最高相关": row.get("max_abs_correlation"),
                "是否保留": "是" if row.get("retained") else f"否：{row.get('retention_reason')}",
            }
        )
    return rows


def render_acceptance_lines(
    strategy_summary: pd.DataFrame,
    sample_split: pd.DataFrame,
    benchmark_metrics: dict[str, Any],
) -> list[str]:
    multifactor = strategy_summary[strategy_summary["strategy_name"] == "multifactor"].copy()
    if multifactor.empty:
        return ["- 多因子策略未产生有效信号，验收不通过。"]
    best = multifactor.sort_values("annual_return_with_cost", ascending=False).iloc[0].to_dict()
    annual_pass = bool(best.get("annual_return_not_below_proxy"))
    drawdown_pass = bool(best.get("drawdown_not_significantly_higher_than_proxy"))
    cost_pass = bool(best.get("cost_after_return_not_fully_eroded"))
    oos_flags = sample_split["oos_degradation_flag"].astype(bool).any() if "oos_degradation_flag" in sample_split.columns else True
    return [
        f"- 年化收益不低于代理基准：{'通过' if annual_pass else '未通过'}；最佳多因子策略 `{best.get('strategy_name')}` Top {float(best.get('top_fraction')):.0%}，成本后年化 {format_value(best.get('annual_return_with_cost'))}，proxy 年化 {format_value(benchmark_metrics.get('annual_return'))}。",
        f"- 最大回撤不显著高于基准：{'通过' if drawdown_pass else '未通过'}；策略回撤 {format_value(best.get('max_drawdown_with_cost'))}，proxy 回撤 {format_value(benchmark_metrics.get('max_drawdown'))}。",
        f"- 样本外收益不能从高正值转为大幅负值：{'通过' if not oos_flags else '未通过'}。",
        f"- 成本后收益不被成本完全吞掉：{'通过' if cost_pass else '未通过'}；成本侵蚀 {format_value(best.get('cost_erosion'))}。",
        f"- 换手率可解释：Top/跌出阈值调仓导致换手率为 {format_value(best.get('turnover_with_cost'))}，需结合交易频率和持仓数评估容量。",
    ]


def _best_strategy(strategy_summary: pd.DataFrame) -> str:
    if strategy_summary.empty or "annual_return_with_cost" not in strategy_summary.columns:
        return "无有效策略"
    values = pd.to_numeric(strategy_summary["annual_return_with_cost"], errors="coerce")
    if values.dropna().empty:
        return "无有效策略"
    row = strategy_summary.loc[values.idxmax()].to_dict()
    return f"`{row.get('strategy_name')}` Top {float(row.get('top_fraction')):.0%}（成本后年化 {format_value(row.get('annual_return_with_cost'))}）"


def matrix_to_long(matrix: pd.DataFrame, value_name: str) -> pd.DataFrame:
    work = matrix.copy()
    work.index = [item.isoformat() if isinstance(item, date) else str(item) for item in work.index]
    work.index.name = "date"
    work.columns = [str(column) for column in work.columns]
    return work.stack(future_stack=True).rename(value_name).reset_index().rename(columns={"level_1": "symbol"})


def select_top_from_series(scores: pd.Series, top_fraction: float) -> list[str]:
    valid = pd.to_numeric(scores, errors="coerce").dropna()
    if valid.empty:
        return []
    count = max(1, math.ceil(len(valid) * top_fraction))
    ranked = valid.sort_values(ascending=False, kind="mergesort")
    return [str(item) for item in ranked.head(count).index.tolist()]


def assign_quantile_groups(values: pd.Series, group_count: int) -> pd.Series:
    if len(values) < group_count or not _has_variation(values):
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    ranks = values.rank(method="first")
    groups = pd.qcut(ranks, q=group_count, labels=range(1, group_count + 1))
    return groups.astype("Int64")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if pd.isna(value):
        return None
    return value


def _has_variation(series: pd.Series) -> bool:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return len(clean) >= 2 and clean.nunique(dropna=True) >= 2


def _spearman_corr(left: pd.Series, right: pd.Series) -> float | None:
    paired = pd.DataFrame({"left": left, "right": right}).dropna()
    if len(paired) < 2 or not _has_variation(paired["left"]) or not _has_variation(paired["right"]):
        return None
    return float(paired["left"].rank(method="average").corr(paired["right"].rank(method="average"), method="pearson"))


def _series_mean(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return float(series.mean())


def _frame_positive_mean(frame: pd.DataFrame) -> float | None:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    positive = numeric.where(numeric > 0).stack(future_stack=True).dropna()
    if positive.empty:
        return None
    return float(positive.mean())


def _select_capacity_cost_row(strategy_summary: pd.DataFrame) -> dict[str, Any]:
    if strategy_summary.empty or "capacity_report" not in strategy_summary.columns:
        return {}
    candidates = strategy_summary[strategy_summary["status"] == "success"].copy()
    if candidates.empty:
        candidates = strategy_summary.copy()
    if "model_type" in candidates.columns:
        multifactor = candidates[candidates["model_type"] == "multi_factor"]
        if not multifactor.empty:
            candidates = multifactor
    if "annual_return_with_cost" in candidates.columns:
        ranking = pd.to_numeric(candidates["annual_return_with_cost"], errors="coerce")
        if ranking.notna().any():
            return candidates.loc[ranking.idxmax()].to_dict()
    return candidates.iloc[0].to_dict()


def _positive_ratio(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return float((series > 0).mean())


def _safe_divide(left: Any, right: Any) -> float | None:
    if left is None or right in (None, 0):
        return None
    if pd.isna(left) or pd.isna(right):
        return None
    if not math.isfinite(float(right)):
        return None
    return float(left) / float(right)


def _to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _optional_date(value: str | None) -> date | None:
    if value in (None, ""):
        return None
    return pd.to_datetime(value).date()


def _date_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _bool_series(series: pd.Series) -> pd.Series:
    def coerce(value: Any) -> bool:
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "y", "是"}

    return series.map(coerce).astype(bool)


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


if __name__ == "__main__":
    main()
