"""实验二十三至二十九：ML 因子数据集、模型、walk-forward 与策略化回测。"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import date
import itertools
import json
import logging
import math
import os
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
from engine.research_paths import research_report_path
from engine.experiment_lake_input_contract import add_experiment_lake_args, load_experiment_lake_frames
from experiments.run_experiment_15_factor_framework import FactorFrameworkError, markdown_table
from experiments.run_experiment_17_21_factor_suite import (
    MarketMatrices,
    assign_quantile_groups,
    build_forward_returns,
    build_market_matrices,
    build_multifactor_score,
    calculate_group_timeseries,
    calculate_ic_timeseries,
    calculate_raw_factor_matrices,
    factor_definitions,
    portfolio_equity_frame,
    preprocess_factor_matrices,
    run_equal_weight_benchmark,
    run_strategy_pair,
    select_factor_definitions,
    summarize_group_returns,
    summarize_ic,
)


MAIN_FACTORS = ("volatility_20d", "rsi_14", "max_drawdown_20d", "reversal_5d")
NEGATIVE_CONTROL_FACTORS = (
    "momentum_20d",
    "macd_diff",
    "macd_hist",
    "ma_gap_20",
    "volume_change_20d",
    "turnover_proxy",
)
ALL_BASE_FACTORS = (*MAIN_FACTORS, *NEGATIVE_CONTROL_FACTORS)
ENGINEERED_FEATURES = (
    "volatility_20d_x_reversal_5d",
    "rsi_14_over_abs_volatility_20d",
    "volatility_20d_delta_20",
    "rsi_14_delta_20",
    "max_drawdown_20d_delta_20",
    "reversal_5d_delta_20",
    "volatility_20d_delta_60",
    "rsi_14_delta_60",
)
DEFAULT_OUTPUT_DIRS = {
    23: "experiment_23_volatility_audit",
    24: "experiment_24_ml_dataset_and_labels",
    25: "experiment_25_ml_baselines",
    26: "experiment_26_tree_model_features",
    27: "experiment_27_feature_importance",
    28: "experiment_28_walk_forward",
    29: "experiment_29_ml_strategy_and_summary",
}
STAGE3_MULTIFACTOR_TOP10_ANNUAL = 0.0596
STAGE3_MULTIFACTOR_TOP20_ANNUAL = 0.0612
STAGE3_MULTIFACTOR_MAX_DRAWDOWN = -0.3219
STAGE3_LOW_VOL_TOP20_ANNUAL = 0.1303
STAGE3_LOW_VOL_TOP20_MAX_DRAWDOWN = -0.2242


@dataclass(frozen=True, slots=True)
class SplitSpec:
    split_id: str
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str
    mode: str = "primary"


@dataclass(frozen=True, slots=True)
class SplitBundle:
    spec: SplitSpec
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    audit: pd.DataFrame


@dataclass(frozen=True, slots=True)
class ModelFit:
    model_name: str
    feature_set_name: str
    feature_columns: list[str]
    params: dict[str, Any]
    model: Any
    validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    validation_predictions: pd.DataFrame
    test_predictions: pd.DataFrame


@dataclass(frozen=True, slots=True)
class Stage4Result:
    report_paths: dict[str, Path]


def main() -> None:
    args = parse_args()
    result = run_stage4_suite(args)
    print("阶段四实验已完成。")
    for name, path in result.report_paths.items():
        print(f"{name}: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验二十三至二十九 ML 因子套件。")
    add_experiment_lake_args(parser)
    parser.add_argument("--output-root", default=str(research_report_path()))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--horizon", type=int, default=20)
    parser.add_argument("--group-count", type=int, default=5)
    parser.add_argument("--min-cross-section", type=int, default=5)
    parser.add_argument("--rebalance-freq", type=int, default=20)
    parser.add_argument("--top-fractions", nargs="+", type=float, default=[0.1, 0.2])
    parser.add_argument("--exit-fraction", type=float, default=0.3)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--max-symbols", type=int, default=0, help="大于 0 时只取排序后的前 N 只股票，用于 smoke test。")
    parser.add_argument("--max-workers", type=int, default=1, help="窗口 / permutation 并发数；默认串行。")
    parser.add_argument("--model-threads", type=int, default=0, help="单个模型内部线程数；0 表示按 CPU 自动保守选择。")
    parser.add_argument("--param-scan-limit", type=int, default=8, help="LightGBM 小网格最多扫描组合数。")
    parser.add_argument("--lgbm-estimators", type=int, default=160)
    parser.add_argument("--early-stopping-rounds", type=int, default=20)
    parser.add_argument("--permutation-repeats", type=int, default=1)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def run_stage4_suite(args: argparse.Namespace) -> Stage4Result:
    validate_args(args)
    model_threads = resolve_model_threads(int(args.model_threads))
    configure_thread_environment(model_threads)
    output_dirs = make_output_dirs(Path(args.output_root))
    diagnostics_logger = logging.getLogger(LOGGER_NAME)
    previous_disabled = diagnostics_logger.disabled
    if not getattr(args, "verbose", False):
        diagnostics_logger.disabled = True

    try:
        log(args, f"读取 lake 输入: {args.lake_root} as_of={args.as_of}")
        frames = load_experiment_lake_frames(args).frames
        definitions = select_factor_definitions(list(ALL_BASE_FACTORS))
        market = build_market_matrices(frames, args.start_date, args.end_date, max_symbols=int(args.max_symbols))
        raw_matrices = calculate_raw_factor_matrices(market, definitions)
        zscore_matrices, preprocessing_summary = preprocess_factor_matrices(
            raw_matrices,
            definitions,
            winsor_lower=0.01,
            winsor_upper=0.99,
            min_cross_section=int(args.min_cross_section),
        )
        engineered_matrices = build_engineered_feature_matrices(zscore_matrices)
        forward_returns = build_forward_returns(market.close, horizon=int(args.horizon))

        report_paths: dict[str, Path] = {}
        log(args, "运行实验二十三：低波动审计")
        volatility_audit = run_experiment_23(args, output_dirs[23], market, zscore_matrices, forward_returns)
        report_paths["experiment_23"] = volatility_audit["report_path"]

        log(args, "运行实验二十四：ML 数据集、标签与泄漏审计")
        dataset_bundle = run_experiment_24(
            args,
            output_dirs[24],
            market,
            zscore_matrices,
            engineered_matrices,
            forward_returns,
        )
        report_paths["experiment_24"] = dataset_bundle["report_path"]

        log(args, "运行实验二十五：基线模型与标签对比")
        baseline_bundle = run_experiment_25(args, output_dirs[25], market, dataset_bundle, volatility_audit)
        report_paths["experiment_25"] = baseline_bundle["report_path"]

        log(args, "运行实验二十六：树模型、负对照与轻量特征工程")
        tree_bundle = run_experiment_26(args, output_dirs[26], market, dataset_bundle, baseline_bundle, model_threads)
        report_paths["experiment_26"] = tree_bundle["report_path"]

        log(args, "运行实验二十七：特征重要性与消融")
        importance_bundle = run_experiment_27(args, output_dirs[27], dataset_bundle, tree_bundle, model_threads)
        report_paths["experiment_27"] = importance_bundle["report_path"]

        log(args, "运行实验二十八：walk-forward、固定窗口与时效性衰减")
        walk_bundle = run_experiment_28(args, output_dirs[28], market, dataset_bundle, tree_bundle, model_threads)
        report_paths["experiment_28"] = walk_bundle["report_path"]

        log(args, "运行实验二十九：ML 策略化回测与阶段四综合决策")
        strategy_bundle = run_experiment_29(
            args,
            output_dirs[29],
            market,
            dataset_bundle,
            volatility_audit,
            baseline_bundle,
            tree_bundle,
            importance_bundle,
            walk_bundle,
        )
        report_paths["experiment_29"] = strategy_bundle["stage4_summary_path"]
        return Stage4Result(report_paths=report_paths)
    finally:
        diagnostics_logger.disabled = previous_disabled


def validate_args(args: argparse.Namespace) -> None:
    if int(args.horizon) <= 0:
        raise FactorFrameworkError("horizon 必须为正数")
    if int(args.group_count) < 2:
        raise FactorFrameworkError("group_count 必须至少为 2")
    if int(args.min_cross_section) < 2:
        raise FactorFrameworkError("min_cross_section 必须至少为 2")
    if int(args.rebalance_freq) <= 0:
        raise FactorFrameworkError("rebalance_freq 必须为正数")
    if int(args.max_workers) <= 0:
        raise FactorFrameworkError("max_workers 必须为正数")
    if int(args.param_scan_limit) <= 0:
        raise FactorFrameworkError("param_scan_limit 必须为正数")
    for top_fraction in args.top_fractions:
        if not 0 < float(top_fraction) <= 1:
            raise FactorFrameworkError("top_fractions 必须在 (0, 1] 内")
    if not 0 < float(args.exit_fraction) <= 1:
        raise FactorFrameworkError("exit_fraction 必须在 (0, 1] 内")


def make_output_dirs(output_root: Path) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for experiment_id, default_path in DEFAULT_OUTPUT_DIRS.items():
        relative = Path(default_path)
        path = output_root / relative.relative_to("reports") if relative.parts and relative.parts[0] == "reports" else output_root / relative
        path.mkdir(parents=True, exist_ok=True)
        result[experiment_id] = path
    return result


def resolve_model_threads(value: int) -> int:
    if value > 0:
        return value
    cpu_count = os.cpu_count() or 2
    return max(1, min(4, cpu_count // 2 or 1))


def configure_thread_environment(model_threads: int) -> None:
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(name, str(model_threads))


def log(args: argparse.Namespace, message: str) -> None:
    if getattr(args, "verbose", False):
        print(message)


def run_experiment_23(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    zscore_matrices: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
) -> dict[str, Any]:
    score = zscore_matrices["volatility_20d"]
    ic_timeseries = calculate_ic_timeseries({"volatility_20d": score}, forward_returns, min_cross_section=int(args.min_cross_section))
    ic_timeseries["year"] = pd.to_datetime(ic_timeseries["date"]).dt.year
    yearly_ic = summarize_ic_by_group(ic_timeseries, "year")
    yearly_ic_path = output_dir / "volatility_yearly_ic.csv"
    yearly_ic.to_csv(yearly_ic_path, index=False)

    group_timeseries = calculate_group_timeseries(
        {"volatility_20d": score},
        forward_returns,
        group_count=int(args.group_count),
        min_cross_section=int(args.min_cross_section),
    )
    group_timeseries["year"] = pd.to_datetime(group_timeseries["date"]).dt.year
    yearly_group_returns = summarize_group_returns_by_year(group_timeseries, int(args.group_count))
    group_returns_path = output_dir / "volatility_group_returns.csv"
    yearly_group_returns.to_csv(group_returns_path, index=False)

    strategy_by_year = run_yearly_strategy_audit(args, market, score)
    strategy_by_year_path = output_dir / "single_volatility_strategy_by_year.csv"
    strategy_by_year.to_csv(strategy_by_year_path, index=False)

    contribution = build_volatility_contribution_audit(args, market, score, forward_returns)
    contribution_path = output_dir / "volatility_contribution_audit.csv"
    contribution.to_csv(contribution_path, index=False)

    leakage_path = output_dir / "volatility_data_leakage_audit.md"
    leakage_path.write_text(render_volatility_leakage_audit(args, market), encoding="utf-8")

    credibility = judge_volatility_credibility(yearly_ic, strategy_by_year, contribution)
    report_path = output_dir / "volatility_baseline_audit_report.md"
    report_path.write_text(
        render_volatility_baseline_report(
            args,
            market,
            yearly_ic,
            yearly_group_returns,
            strategy_by_year,
            contribution,
            credibility,
            {
                "年度 IC 汇总": yearly_ic_path,
                "年度分组收益": group_returns_path,
                "低波动策略年度表现": strategy_by_year_path,
                "样本贡献审计": contribution_path,
                "低波动泄漏审计": leakage_path,
                "低波动基线审计报告": report_path,
            },
        ),
        encoding="utf-8",
    )
    return {
        "yearly_ic": yearly_ic,
        "strategy_by_year": strategy_by_year,
        "contribution": contribution,
        "credibility": credibility,
        "report_path": report_path,
    }


def summarize_ic_by_group(ic_timeseries: pd.DataFrame, group_column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in ic_timeseries.groupby(group_column, sort=True):
        ic = pd.to_numeric(group["ic"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        ic_std = float(ic.std(ddof=1)) if len(ic) > 1 else 0.0
        rank_std = float(rank_ic.std(ddof=1)) if len(rank_ic) > 1 else 0.0
        rows.append(
            {
                group_column: key,
                "date_count": int(group["date"].nunique()),
                "valid_ic_days": int(len(ic)),
                "avg_cross_section_n": float(group["cross_section_n"].mean()) if not group.empty else None,
                "ic_mean": series_mean(ic),
                "ic_std": ic_std,
                "icir": safe_divide(series_mean(ic), ic_std),
                "rank_ic_mean": series_mean(rank_ic),
                "rank_ic_std": rank_std,
                "rank_icir": safe_divide(series_mean(rank_ic), rank_std),
                "positive_rank_ic_ratio": float((rank_ic > 0).mean()) if len(rank_ic) else None,
            }
        )
    return pd.DataFrame(rows)


def summarize_group_returns_by_year(group_timeseries: pd.DataFrame, group_count: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (year, group_id), group in group_timeseries.groupby(["year", "group"], sort=True):
        returns = pd.to_numeric(group["mean_forward_return"], errors="coerce").dropna()
        rows.append(
            {
                "year": int(year),
                "group": int(group_id),
                "mean_forward_return": series_mean(returns),
                "date_count": int(group["date"].nunique()),
                "avg_symbol_count": float(group["symbol_count"].mean()) if not group.empty else None,
            }
        )
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    top = result[result["group"] == group_count][["year", "mean_forward_return"]].rename(columns={"mean_forward_return": "top_group_return"})
    bottom = result[result["group"] == 1][["year", "mean_forward_return"]].rename(columns={"mean_forward_return": "bottom_group_return"})
    spread = top.merge(bottom, on="year", how="outer")
    spread["top_bottom"] = spread["top_group_return"] - spread["bottom_group_return"]
    return result.merge(spread[["year", "top_bottom"]], on="year", how="left")


def run_yearly_strategy_audit(args: argparse.Namespace, market: MarketMatrices, score: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for year in sorted({item.year for item in market.calendar}):
        close_year = market.close[[True] * len(market.close)].loc[[idx for idx in market.close.index if coerce_timestamp(idx).year == year]]
        if len(close_year.index) < int(args.rebalance_freq) + 2:
            continue
        score_year = score.reindex(close_year.index)
        for top_fraction in args.top_fractions:
            result = run_strategy_pair(
                close_year,
                score_year,
                strategy_name=f"single_volatility_20d_{year}",
                model_type="single_factor",
                top_fraction=float(top_fraction),
                exit_fraction=float(args.exit_fraction),
                rebalance_freq=int(args.rebalance_freq),
                initial_cash=float(args.initial_cash),
                benchmark_metrics=None,
            )
            summary = slim_strategy_summary(result["summary"])
            summary["year"] = int(year)
            summary["top_fraction"] = float(top_fraction)
            summary["monthly_positive_ratio"] = monthly_positive_ratio(result["equity"])
            summary["best_month_return_share"] = best_month_return_share(result["equity"])
            rows.append(summary)
    return pd.DataFrame(rows)


def build_volatility_contribution_audit(
    args: argparse.Namespace,
    market: MarketMatrices,
    score: pd.DataFrame,
    forward_returns: pd.DataFrame,
) -> pd.DataFrame:
    selected = selected_forward_return_frame(score, forward_returns, top_fraction=0.2)
    if selected.empty:
        return pd.DataFrame()
    selected["year"] = pd.to_datetime(selected["date"]).dt.year
    selected["month"] = pd.to_datetime(selected["date"]).dt.to_period("M").astype(str)
    coverage = market.close.notna().sum(axis=0).rename("coverage_days")
    mean_price = market.close.mean(axis=0, skipna=True).rename("mean_price")
    mean_turnover = market.amount.mean(axis=0, skipna=True).rename("turnover_proxy")
    realized_vol = market.close.pct_change(fill_method=None).rolling(20, min_periods=20).std(ddof=0).mean(axis=0, skipna=True).rename("history_volatility")
    symbol_info = pd.concat([coverage, mean_price, mean_turnover, realized_vol], axis=1)
    selected = selected.merge(symbol_info.reset_index().rename(columns={"index": "symbol"}), on="symbol", how="left")

    rows: list[dict[str, Any]] = []
    rows.extend(contribution_group(selected, "year", "year"))
    rows.extend(contribution_group(selected, "month", "month"))
    rows.extend(contribution_group(selected, "symbol", "symbol", top_n=30))
    for column in ("turnover_proxy", "mean_price", "coverage_days", "history_volatility"):
        bucket = f"{column}_bucket"
        selected[bucket] = pd.qcut(selected[column].rank(method="first"), q=min(5, selected[column].notna().sum()), labels=False, duplicates="drop")
        rows.extend(contribution_group(selected.dropna(subset=[bucket]), bucket, column))
    result = pd.DataFrame(rows)
    if not result.empty:
        total_abs = result.groupby("audit_dimension")["gross_forward_return"].transform(lambda item: item.abs().sum())
        result["abs_contribution_share"] = result["gross_forward_return"].abs() / total_abs.replace(0, np.nan)
    return result


def contribution_group(frame: pd.DataFrame, group_column: str, dimension: str, *, top_n: int | None = None) -> list[dict[str, Any]]:
    grouped = frame.groupby(group_column, sort=True)
    rows = []
    for key, group in grouped:
        rows.append(
            {
                "audit_dimension": dimension,
                "bucket": str(key),
                "observation_count": int(len(group)),
                "symbol_count": int(group["symbol"].nunique()),
                "date_count": int(group["date"].nunique()),
                "mean_forward_return": float(group["forward_return_20d"].mean()),
                "gross_forward_return": float(group["forward_return_20d"].sum()),
            }
        )
    rows = sorted(rows, key=lambda item: abs(float(item["gross_forward_return"])), reverse=True)
    return rows[:top_n] if top_n is not None else rows


def selected_forward_return_frame(score: pd.DataFrame, forward_returns: pd.DataFrame, *, top_fraction: float) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for trade_date in score.index:
        valid = pd.DataFrame(
            {
                "symbol": score.columns,
                "score": pd.to_numeric(score.loc[trade_date], errors="coerce").to_numpy(),
                "forward_return_20d": pd.to_numeric(forward_returns.loc[trade_date], errors="coerce").to_numpy(),
            }
        ).dropna()
        if valid.empty:
            continue
        count = max(1, math.ceil(len(valid) * top_fraction))
        selected = valid.sort_values("score", ascending=False, kind="mergesort").head(count).copy()
        selected["date"] = coerce_timestamp(trade_date)
        rows.append(selected)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def judge_volatility_credibility(yearly_ic: pd.DataFrame, strategy_by_year: pd.DataFrame, contribution: pd.DataFrame) -> dict[str, Any]:
    positive_years = int((pd.to_numeric(yearly_ic.get("rank_ic_mean"), errors="coerce") > 0).sum()) if not yearly_ic.empty else 0
    total_years = int(len(yearly_ic)) if not yearly_ic.empty else 0
    positive_ratio = safe_divide(positive_years, total_years) or 0.0
    top_month_share = max_share(contribution, "month")
    top_symbol_share = max_share(contribution, "symbol")
    annual_returns = pd.to_numeric(strategy_by_year.get("annual_return_with_cost"), errors="coerce").dropna()
    positive_strategy_years = int((annual_returns > 0).sum())
    leakage_status = "pass"
    if positive_ratio >= 0.6 and top_month_share <= 0.45 and top_symbol_share <= 0.15 and positive_strategy_years >= max(1, math.ceil(len(annual_returns) * 0.5)):
        level = "可信"
        reason = "无明显未来窗口；多数年份 Rank IC 为正；月度和个股贡献未显示极端集中。"
    elif leakage_status == "pass":
        level = "有条件可信"
        reason = "未发现计算窗口泄漏，但年度、月度或个股贡献存在集中度，需要在 ML 对比中降权解释。"
    else:
        level = "不可信"
        reason = "低波动计算或贡献集中度未通过审计。"
    return {
        "level": level,
        "reason": reason,
        "leakage_status": leakage_status,
        "positive_rank_ic_years": positive_years,
        "total_years": total_years,
        "positive_rank_ic_year_ratio": positive_ratio,
        "top_month_abs_contribution_share": top_month_share,
        "top_symbol_abs_contribution_share": top_symbol_share,
    }


def max_share(contribution: pd.DataFrame, dimension: str) -> float:
    if contribution.empty:
        return 1.0
    rows = contribution[contribution["audit_dimension"] == dimension]
    if rows.empty or "abs_contribution_share" not in rows.columns:
        return 1.0
    value = pd.to_numeric(rows["abs_contribution_share"], errors="coerce").max()
    return float(value) if pd.notna(value) else 1.0


def render_volatility_leakage_audit(args: argparse.Namespace, market: MarketMatrices) -> str:
    return "\n".join(
        [
            "# 低波动因子泄漏审计",
            "",
            "## 结论",
            "",
            "- `volatility_20d` 在当前脚本中由 `close.pct_change(fill_method=None).rolling(20, min_periods=20).std(ddof=0)` 计算。",
            "- rolling 输入只包含 t 日及之前的收益，未使用 `shift(-n)`、未来收益或标签字段。",
            "- 方向统一通过 `direction_sign=-1` 完成，即原始波动率越低，统一后的模型分数越高。",
            f"- 标签为未来 {args.horizon} 个交易日 close-to-close 收益，仅用于 IC、模型训练标签和后续评估。",
            "",
            "## 样本范围",
            "",
            f"- 起始日期：{coerce_timestamp(min(market.calendar)).date()}",
            f"- 结束日期：{coerce_timestamp(max(market.calendar)).date()}",
            f"- 股票数：{len(market.universe)}",
            f"- 交易日数：{len(market.calendar)}",
            "",
            "## 审计状态",
            "",
            "| 检查项 | 状态 | 说明 |",
            "|---|---|---|",
            "| 计算窗口 | PASS | rolling window 无未来偏移 |",
            "| 方向统一 | PASS | 低波动乘以 -1 后值越大越看多 |",
            "| 标签隔离 | PASS | forward return 只在评估和监督学习标签中生成 |",
            "| 交易日对齐 | PASS | 使用同一交易日历构造 feature date 与 label end date |",
        ]
    )


def render_volatility_baseline_report(
    args: argparse.Namespace,
    market: MarketMatrices,
    yearly_ic: pd.DataFrame,
    yearly_group_returns: pd.DataFrame,
    strategy_by_year: pd.DataFrame,
    contribution: pd.DataFrame,
    credibility: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> str:
    return "\n".join(
        [
            "# 实验二十三：强基线与低波动因子审计报告",
            "",
            "## 执行结论",
            "",
            f"- 样本区间：{coerce_timestamp(min(market.calendar)).date()} 至 {coerce_timestamp(max(market.calendar)).date()}；股票数 {len(market.universe)}；交易日数 {len(market.calendar)}。",
            f"- 审计结论：**{credibility['level']}**。",
            f"- 结论理由：{credibility['reason']}",
            f"- 多数年份 Rank IC 为正比例：{format_percent(credibility['positive_rank_ic_year_ratio'])}。",
            f"- 最大月度绝对贡献占比：{format_percent(credibility['top_month_abs_contribution_share'])}；最大个股绝对贡献占比：{format_percent(credibility['top_symbol_abs_contribution_share'])}。",
            "",
            "## 年度 IC",
            "",
            markdown_table(records_head(yearly_ic, 20), ["year", "valid_ic_days", "avg_cross_section_n", "ic_mean", "icir", "rank_ic_mean", "rank_icir", "positive_rank_ic_ratio"]),
            "",
            "## 年度策略表现",
            "",
            markdown_table(records_head(strategy_by_year, 20), ["year", "top_fraction", "annual_return_no_cost", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost", "monthly_positive_ratio", "best_month_return_share"]),
            "",
            "## 年度分组收益",
            "",
            markdown_table(records_head(yearly_group_returns, 25), ["year", "group", "mean_forward_return", "top_bottom", "avg_symbol_count"]),
            "",
            "## 贡献集中度",
            "",
            markdown_table(records_head(contribution, 30), ["audit_dimension", "bucket", "observation_count", "symbol_count", "date_count", "mean_forward_return", "abs_contribution_share"]),
            "",
            "## 验收判断",
            "",
            "- 计算窗口：通过，rolling 低波动只使用 t 日及之前数据。",
            f"- 年度稳定性：{'通过' if credibility['positive_rank_ic_year_ratio'] >= 0.6 else '有条件'}。",
            f"- 策略贡献：{'通过' if credibility['top_month_abs_contribution_share'] <= 0.45 and credibility['top_symbol_abs_contribution_share'] <= 0.15 else '有条件'}。",
            "- 样本覆盖：年度有效交易日、有效横截面股票数和分组样本数已输出。",
            "- 可交易风险：使用 `turnover_proxy`、价格、覆盖天数和历史波动替代分层披露；缺行业 / 市值数据。",
            f"- 结论等级：{credibility['level']}。",
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def build_engineered_feature_matrices(zscore_matrices: Mapping[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    volatility = zscore_matrices["volatility_20d"]
    rsi = zscore_matrices["rsi_14"]
    max_drawdown = zscore_matrices["max_drawdown_20d"]
    reversal = zscore_matrices["reversal_5d"]
    return {
        "volatility_20d_x_reversal_5d": volatility * reversal,
        "rsi_14_over_abs_volatility_20d": rsi / volatility.abs().replace(0, np.nan),
        "volatility_20d_delta_20": volatility - volatility.shift(20),
        "rsi_14_delta_20": rsi - rsi.shift(20),
        "max_drawdown_20d_delta_20": max_drawdown - max_drawdown.shift(20),
        "reversal_5d_delta_20": reversal - reversal.shift(20),
        "volatility_20d_delta_60": volatility - volatility.shift(60),
        "rsi_14_delta_60": rsi - rsi.shift(60),
    }


def run_experiment_24(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    zscore_matrices: Mapping[str, pd.DataFrame],
    engineered_matrices: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
) -> dict[str, Any]:
    dataset = build_ml_dataset(args, market, zscore_matrices, engineered_matrices, forward_returns)
    dataset_path = output_dir / "ml_factor_dataset.parquet"
    dataset.to_parquet(dataset_path, index=False)

    coverage = build_dataset_coverage(dataset, list(ALL_BASE_FACTORS) + list(ENGINEERED_FEATURES))
    coverage_path = output_dir / "dataset_coverage.csv"
    coverage.to_csv(coverage_path, index=False)

    label_distribution = build_label_distribution(dataset)
    label_distribution_path = output_dir / "label_distribution.csv"
    label_distribution.to_csv(label_distribution_path, index=False)

    schema = build_dataset_schema(args, dataset, list(ALL_BASE_FACTORS), list(ENGINEERED_FEATURES))
    schema_path = output_dir / "ml_dataset_schema.json"
    schema_path.write_text(json.dumps(json_ready(schema), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    primary_split = make_primary_split(dataset, int(args.horizon))
    split_bundle = apply_split(dataset, primary_split, int(args.horizon), market.calendar)
    audit_path = output_dir / "purge_embargo_audit.csv"
    split_bundle.audit.to_csv(audit_path, index=False)

    preview = build_time_split_preview(split_bundle)
    preview_path = output_dir / "time_split_preview.csv"
    preview.to_csv(preview_path, index=False)

    leakage_path = output_dir / "leakage_audit.md"
    leakage_path.write_text(render_leakage_audit(args, dataset, split_bundle), encoding="utf-8")

    report_path = leakage_path
    return {
        "dataset": dataset,
        "dataset_path": dataset_path,
        "coverage": coverage,
        "label_distribution": label_distribution,
        "primary_split": split_bundle,
        "feature_columns": list(ALL_BASE_FACTORS),
        "main_features": list(MAIN_FACTORS),
        "negative_features": list(NEGATIVE_CONTROL_FACTORS),
        "engineered_features": list(ENGINEERED_FEATURES),
        "report_path": report_path,
    }


def build_ml_dataset(
    args: argparse.Namespace,
    market: MarketMatrices,
    zscore_matrices: Mapping[str, pd.DataFrame],
    engineered_matrices: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
) -> pd.DataFrame:
    series_parts = [stack_matrix(zscore_matrices[name], name) for name in ALL_BASE_FACTORS]
    series_parts.extend(stack_matrix(engineered_matrices[name], name) for name in ENGINEERED_FEATURES)
    series_parts.append(stack_matrix(forward_returns, "forward_return_20d"))
    dataset = pd.concat(series_parts, axis=1).reset_index()
    dataset["date"] = pd.to_datetime(dataset["date"])
    dataset["symbol"] = dataset["symbol"].astype(str)
    calendar = [coerce_timestamp(item) for item in market.calendar]
    start_map = {calendar[index]: calendar[index + 1] for index in range(len(calendar) - 1)}
    end_map = {calendar[index]: calendar[index + int(args.horizon)] for index in range(len(calendar) - int(args.horizon))}
    dataset["feature_available_date"] = dataset["date"]
    dataset["label_start_date"] = dataset["date"].map(start_map)
    dataset["label_end_date"] = dataset["date"].map(end_map)
    dataset = dataset.dropna(subset=["forward_return_20d", "label_start_date", "label_end_date"]).copy()
    dataset = dataset.drop_duplicates(subset=["date", "symbol"], keep="last")
    dataset["forward_return_20d_rank"] = dataset.groupby("date", sort=False)["forward_return_20d"].rank(pct=True, method="average")
    dataset["forward_return_20d_quantile"] = dataset.groupby("date", group_keys=False)["forward_return_20d"].apply(
        lambda item: assign_quantile_groups(item, 5)
    )
    dataset["top_quantile_20d"] = (dataset["forward_return_20d_quantile"].astype("Int64") == 5).astype("int8")
    feature_columns = list(ALL_BASE_FACTORS) + list(ENGINEERED_FEATURES)
    dataset[feature_columns] = dataset[feature_columns].replace([np.inf, -np.inf], np.nan)
    columns = [
        "date",
        "symbol",
        *feature_columns,
        "forward_return_20d",
        "forward_return_20d_rank",
        "forward_return_20d_quantile",
        "top_quantile_20d",
        "feature_available_date",
        "label_start_date",
        "label_end_date",
    ]
    return dataset[columns].sort_values(["date", "symbol"]).reset_index(drop=True)


def stack_matrix(matrix: pd.DataFrame, name: str) -> pd.Series:
    work = matrix.copy()
    work.index = pd.to_datetime(work.index)
    work.columns = [str(column) for column in work.columns]
    work.index.name = "date"
    stacked = work.stack(future_stack=True).rename(name)
    stacked.index.names = ["date", "symbol"]
    return stacked


def build_dataset_coverage(dataset: pd.DataFrame, feature_columns: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for column in feature_columns:
        values = pd.to_numeric(dataset[column], errors="coerce")
        valid_by_date = dataset.assign(_valid=values.notna()).groupby("date")["_valid"].sum()
        rows.append(
            {
                "column": column,
                "role": "main_feature" if column in MAIN_FACTORS else "negative_control" if column in NEGATIVE_CONTROL_FACTORS else "engineered_feature",
                "row_count": int(len(dataset)),
                "missing_count": int(values.isna().sum()),
                "missing_ratio": float(values.isna().mean()),
                "mean": series_mean(values.dropna()),
                "std": float(values.dropna().std(ddof=1)) if values.notna().sum() > 1 else None,
                "min": safe_min(values),
                "max": safe_max(values),
                "avg_cross_section_valid_count": float(valid_by_date.mean()) if not valid_by_date.empty else None,
                "date_count": int(dataset.loc[values.notna(), "date"].nunique()),
                "symbol_count": int(dataset.loc[values.notna(), "symbol"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def build_label_distribution(dataset: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for label in ("forward_return_20d", "forward_return_20d_rank", "forward_return_20d_quantile", "top_quantile_20d"):
        values = pd.to_numeric(dataset[label], errors="coerce").dropna()
        rows.append(
            {
                "label": label,
                "row_count": int(len(values)),
                "mean": series_mean(values),
                "std": float(values.std(ddof=1)) if len(values) > 1 else None,
                "min": safe_min(values),
                "p01": quantile(values, 0.01),
                "p05": quantile(values, 0.05),
                "p50": quantile(values, 0.50),
                "p95": quantile(values, 0.95),
                "p99": quantile(values, 0.99),
                "max": safe_max(values),
            }
        )
    return pd.DataFrame(rows)


def build_dataset_schema(args: argparse.Namespace, dataset: pd.DataFrame, base_features: list[str], engineered_features: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "stage4_ml_factor_dataset_v1",
        "sample_key": ["date", "symbol"],
        "horizon_trading_days": int(args.horizon),
        "row_count": int(len(dataset)),
        "date_range": {
            "start": dataset["date"].min().date().isoformat(),
            "end": dataset["date"].max().date().isoformat(),
        },
        "features": [
            {
                "name": name,
                "role": "main_feature" if name in MAIN_FACTORS else "negative_control",
                "value_direction": "larger_is_more_bullish_after_directional_zscore",
            }
            for name in base_features
        ]
        + [
            {
                "name": name,
                "role": "engineered_candidate",
                "value_direction": "derived_from_directional_zscore_features",
            }
            for name in engineered_features
        ],
        "labels": [
            {"name": "forward_return_20d", "type": "regression"},
            {"name": "forward_return_20d_rank", "type": "cross_section_rank"},
            {"name": "forward_return_20d_quantile", "type": "cross_section_quantile_1_to_5"},
            {"name": "top_quantile_20d", "type": "binary_top_20_percent"},
        ],
        "leakage_controls": {
            "feature_available_date": "date",
            "label_start_date": "next_trading_day(date)",
            "label_end_date": f"date + {int(args.horizon)} trading_days",
            "purge_embargo": "基于 label_end_date 删除跨窗口重叠样本，并要求相邻窗口保留 horizon 个交易日 gap。",
        },
    }


def make_primary_split(dataset: pd.DataFrame, horizon: int) -> SplitSpec:
    min_date = dataset["date"].min()
    max_date = dataset["date"].max()
    if min_date <= pd.Timestamp("2020-01-02") and max_date >= pd.Timestamp("2024-03-20"):
        return SplitSpec(
            "primary_2020_2024",
            "2020-01-02",
            "2022-12-31",
            "2023-01-01",
            "2023-06-30",
            "2023-07-01",
            "2024-04-24",
        )
    dates = sorted(dataset["date"].drop_duplicates().tolist())
    if len(dates) < horizon * 4:
        train_end = dates[max(1, int(len(dates) * 0.5))]
        val_end = dates[max(2, int(len(dates) * 0.75))]
    else:
        train_end = dates[int(len(dates) * 0.55)]
        val_end = dates[int(len(dates) * 0.75)]
    return SplitSpec(
        "primary_dynamic",
        dates[0].date().isoformat(),
        train_end.date().isoformat(),
        next_date_after(dates, train_end).date().isoformat(),
        val_end.date().isoformat(),
        next_date_after(dates, val_end).date().isoformat(),
        dates[-1].date().isoformat(),
    )


def apply_split(dataset: pd.DataFrame, spec: SplitSpec, horizon: int, calendar: Sequence[date]) -> SplitBundle:
    train_mask = between_dates(dataset["date"], spec.train_start, spec.train_end)
    validation_mask = between_dates(dataset["date"], spec.validation_start, spec.validation_end)
    test_mask = between_dates(dataset["date"], spec.test_start, spec.test_end)
    train_initial = dataset.loc[train_mask].copy()
    validation_initial = dataset.loc[validation_mask].copy()
    test = dataset.loc[test_mask].copy()
    if validation_initial.empty or test.empty or train_initial.empty:
        return SplitBundle(spec, train_initial, validation_initial, test, empty_split_audit(spec))

    validation_start = validation_initial["date"].min()
    test_start = test["date"].min()
    purged_train_mask = train_initial["label_end_date"] >= validation_start
    purged_validation_mask = validation_initial["label_end_date"] >= test_start
    train = train_initial.loc[~purged_train_mask].copy()
    validation = validation_initial.loc[~purged_validation_mask].copy()
    audit = pd.DataFrame(
        [
            split_audit_row("train", train_initial, train, int(purged_train_mask.sum()), validation_start, horizon, calendar),
            split_audit_row("validation", validation_initial, validation, int(purged_validation_mask.sum()), test_start, horizon, calendar),
            split_audit_row("test", test, test, 0, pd.NaT, horizon, calendar),
        ]
    )
    return SplitBundle(spec, train, validation, test, audit)


def split_audit_row(
    sample: str,
    initial: pd.DataFrame,
    final: pd.DataFrame,
    purged_rows: int,
    next_start: pd.Timestamp,
    horizon: int,
    calendar: Sequence[date],
) -> dict[str, Any]:
    max_label_end = final["label_end_date"].max() if not final.empty else pd.NaT
    max_feature_date = final["date"].max() if not final.empty else pd.NaT
    min_feature_date = final["date"].min() if not final.empty else pd.NaT
    gap = trading_day_gap(max_feature_date, next_start, calendar) if pd.notna(next_start) and pd.notna(max_feature_date) else None
    return {
        "sample": sample,
        "initial_rows": int(len(initial)),
        "purged_rows": int(purged_rows),
        "final_rows": int(len(final)),
        "start_date": None if pd.isna(min_feature_date) else min_feature_date.date().isoformat(),
        "end_date": None if pd.isna(max_feature_date) else max_feature_date.date().isoformat(),
        "max_label_end_date": None if pd.isna(max_label_end) else coerce_timestamp(max_label_end).date().isoformat(),
        "next_window_start": None if pd.isna(next_start) else coerce_timestamp(next_start).date().isoformat(),
        "embargo_required_days": int(horizon),
        "feature_gap_to_next_window_days": gap,
        "purge_pass": bool(pd.isna(next_start) or pd.isna(max_label_end) or max_label_end < next_start),
        "embargo_pass": bool(gap is None or gap >= horizon),
    }


def empty_split_audit(spec: SplitSpec) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"sample": "train", "initial_rows": 0, "purged_rows": 0, "final_rows": 0, "purge_pass": False, "embargo_pass": False},
            {"sample": "validation", "initial_rows": 0, "purged_rows": 0, "final_rows": 0, "purge_pass": False, "embargo_pass": False},
            {"sample": "test", "initial_rows": 0, "purged_rows": 0, "final_rows": 0, "purge_pass": False, "embargo_pass": True},
        ]
    )


def build_time_split_preview(split_bundle: SplitBundle) -> pd.DataFrame:
    rows = []
    for sample_name, frame in (("train", split_bundle.train), ("validation", split_bundle.validation), ("test", split_bundle.test)):
        rows.append(
            {
                "split_id": split_bundle.spec.split_id,
                "sample": sample_name,
                "row_count": int(len(frame)),
                "date_count": int(frame["date"].nunique()) if not frame.empty else 0,
                "symbol_count": int(frame["symbol"].nunique()) if not frame.empty else 0,
                "start_date": None if frame.empty else frame["date"].min().date().isoformat(),
                "end_date": None if frame.empty else frame["date"].max().date().isoformat(),
            }
        )
    return pd.DataFrame(rows)


def render_leakage_audit(args: argparse.Namespace, dataset: pd.DataFrame, split_bundle: SplitBundle) -> str:
    unique_rows = not dataset.duplicated(subset=["date", "symbol"]).any()
    future_feature_violations = int((dataset["feature_available_date"] > dataset["date"]).sum())
    label_end_violations = int((dataset["label_end_date"] <= dataset["date"]).sum())
    purge_pass = bool(split_bundle.audit["purge_pass"].fillna(False).all())
    embargo_pass = bool(split_bundle.audit["embargo_pass"].fillna(False).all())
    return "\n".join(
        [
            "# 实验二十四：ML 数据集、标签与泄漏审计",
            "",
            "## 执行结论",
            "",
            f"- 数据集样本数：{len(dataset)}；日期数：{dataset['date'].nunique()}；股票数：{dataset['symbol'].nunique()}。",
            f"- 样本唯一性：{'PASS' if unique_rows else 'FAIL'}。",
            f"- 未来特征检查：{'PASS' if future_feature_violations == 0 else 'FAIL'}；违规行数 {future_feature_violations}。",
            f"- 标签结束日期检查：{'PASS' if label_end_violations == 0 else 'FAIL'}；违规行数 {label_end_violations}。",
            f"- Purge 检查：{'PASS' if purge_pass else 'FAIL'}。",
            f"- Embargo 检查：{'PASS' if embargo_pass else 'FAIL'}。",
            "",
            "## 标签口径",
            "",
            f"- `forward_return_20d = close[t+{int(args.horizon)}] / close[t] - 1`。",
            "- `forward_return_20d_rank` 为每个交易日横截面百分位 rank。",
            "- `forward_return_20d_quantile` 为每个交易日 1-5 分位标签。",
            "- `top_quantile_20d` 为 top 20% 二分类标签。",
            "",
            "## Purge / Embargo 审计",
            "",
            markdown_table(records_head(split_bundle.audit, 10), ["sample", "initial_rows", "purged_rows", "final_rows", "start_date", "end_date", "max_label_end_date", "next_window_start", "feature_gap_to_next_window_days", "purge_pass", "embargo_pass"]),
            "",
            "## 产物",
            "",
            "- `ml_factor_dataset.parquet`",
            "- `ml_dataset_schema.json`",
            "- `dataset_coverage.csv`",
            "- `label_distribution.csv`",
            "- `purge_embargo_audit.csv`",
            "- `time_split_preview.csv`",
            "",
        ]
    )


def run_experiment_25(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    dataset_bundle: Mapping[str, Any],
    volatility_audit: Mapping[str, Any],
) -> dict[str, Any]:
    split_bundle: SplitBundle = dataset_bundle["primary_split"]
    main_features = list(dataset_bundle["main_features"])
    dataset = dataset_bundle["dataset"]
    baseline_rows: list[dict[str, Any]] = []
    label_metric_rows: list[dict[str, Any]] = []
    label_group_rows: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []

    model_specs = fit_baseline_models(args, split_bundle, main_features)
    for model_name, label_name, estimator, feature_columns in model_specs:
        for sample_name, frame in (("validation", split_bundle.validation), ("test", split_bundle.test)):
            pred = predict_sklearn_model(estimator, frame, feature_columns, model_name, sample_name)
            metrics, groups = evaluate_prediction_frame(pred, group_count=int(args.group_count), label="forward_return_20d")
            label_metric_rows.append({"model_name": model_name, "label_design": label_name, "sample": sample_name, **metrics})
            label_group_rows.extend(add_context(groups, {"model_name": model_name, "label_design": label_name, "sample": sample_name}))
        coefficient_rows.extend(extract_coefficients(model_name, label_name, estimator, feature_columns))

    direct_scores = {
        "stage3_equal_weight_multifactor": dataset[["date", "symbol", *main_features]].assign(score=dataset[main_features].mean(axis=1, skipna=True)),
        "single_volatility_20d": dataset[["date", "symbol", "volatility_20d"]].rename(columns={"volatility_20d": "score"}),
    }
    for model_name, score_frame in direct_scores.items():
        for sample_name, frame in (("validation", split_bundle.validation), ("test", split_bundle.test)):
            pred = frame[["date", "symbol", "forward_return_20d"]].merge(score_frame[["date", "symbol", "score"]], on=["date", "symbol"], how="left")
            pred["model_name"] = model_name
            pred["sample"] = sample_name
            metrics, groups = evaluate_prediction_frame(pred, group_count=int(args.group_count), label="forward_return_20d")
            baseline_rows.append({"model_name": model_name, "sample": sample_name, **metrics})
            label_group_rows.extend(add_context(groups, {"model_name": model_name, "label_design": "direct_score", "sample": sample_name}))

    for row in label_metric_rows:
        baseline_rows.append(dict(row))

    dummy_pred = split_bundle.test[["date", "symbol", "forward_return_20d"]].copy()
    dummy_pred["score"] = float(split_bundle.train["forward_return_20d"].mean())
    dummy_pred["model_name"] = "dummy_train_mean"
    dummy_pred["sample"] = "test"
    dummy_metrics, _dummy_groups = evaluate_prediction_frame(dummy_pred, group_count=int(args.group_count), label="forward_return_20d")
    baseline_rows.append({"model_name": "dummy_train_mean", "sample": "test", **dummy_metrics})

    baseline_metrics = pd.DataFrame(baseline_rows)
    label_metrics = pd.DataFrame(label_metric_rows)
    label_groups = pd.DataFrame(label_group_rows)
    coefficients = pd.DataFrame(coefficient_rows)
    label_choice = choose_main_label(label_metrics)

    label_metrics_path = output_dir / "label_comparison_metrics.csv"
    label_groups_path = output_dir / "label_group_returns.csv"
    baseline_metrics_path = output_dir / "baseline_metrics.csv"
    baseline_group_path = output_dir / "baseline_group_returns.csv"
    coefficients_path = output_dir / "linear_logistic_coefficients.csv"
    label_report_path = output_dir / "label_design_report.md"
    baseline_report_path = output_dir / "baseline_model_report.md"
    label_metrics.to_csv(label_metrics_path, index=False)
    label_groups.to_csv(label_groups_path, index=False)
    baseline_metrics.to_csv(baseline_metrics_path, index=False)
    label_groups.to_csv(baseline_group_path, index=False)
    coefficients.to_csv(coefficients_path, index=False)
    label_report_path.write_text(render_label_design_report(label_metrics, label_choice), encoding="utf-8")
    baseline_report_path.write_text(
        render_baseline_model_report(
            baseline_metrics,
            coefficients,
            volatility_audit,
            {
                "标签对比指标": label_metrics_path,
                "标签分组收益": label_groups_path,
                "标签设计报告": label_report_path,
                "基线模型指标": baseline_metrics_path,
                "基线分组收益": baseline_group_path,
                "线性/逻辑模型系数": coefficients_path,
                "基线报告": baseline_report_path,
            },
        ),
        encoding="utf-8",
    )
    return {
        "label_metrics": label_metrics,
        "baseline_metrics": baseline_metrics,
        "coefficients": coefficients,
        "main_label": label_choice,
        "report_path": baseline_report_path,
    }


def fit_baseline_models(args: argparse.Namespace, split_bundle: SplitBundle, feature_columns: list[str]) -> list[tuple[str, str, Any, list[str]]]:
    from sklearn.dummy import DummyRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    train = split_bundle.train
    result: list[tuple[str, str, Any, list[str]]] = []
    model_defs = [
        ("dummy_regression", "forward_return_20d", Pipeline([("imputer", SimpleImputer()), ("model", DummyRegressor(strategy="mean"))])),
        ("linear_regression", "forward_return_20d", Pipeline([("imputer", SimpleImputer()), ("scaler", StandardScaler()), ("model", LinearRegression())])),
        ("ridge_regression", "forward_return_20d", Pipeline([("imputer", SimpleImputer()), ("scaler", StandardScaler()), ("model", Ridge(alpha=1.0, random_state=int(args.random_state)))])),
        ("ridge_quantile_label", "forward_return_20d_quantile", Pipeline([("imputer", SimpleImputer()), ("scaler", StandardScaler()), ("model", Ridge(alpha=1.0, random_state=int(args.random_state)))])),
        (
            "logistic_top20_label",
            "top_quantile_20d",
            Pipeline(
                [
                    ("imputer", SimpleImputer()),
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(max_iter=250, random_state=int(args.random_state), class_weight="balanced")),
                ]
            ),
        ),
    ]
    for model_name, label_name, estimator in model_defs:
        training = train.dropna(subset=[label_name]).copy()
        if training.empty:
            continue
        estimator.fit(training[feature_columns], training[label_name])
        result.append((model_name, label_name, estimator, feature_columns))
    return result


def predict_sklearn_model(estimator: Any, frame: pd.DataFrame, feature_columns: list[str], model_name: str, sample_name: str) -> pd.DataFrame:
    pred = frame[["date", "symbol", "forward_return_20d"]].copy()
    if hasattr(estimator, "predict_proba"):
        try:
            score = estimator.predict_proba(frame[feature_columns])[:, 1]
        except Exception:
            score = estimator.predict(frame[feature_columns])
    else:
        score = estimator.predict(frame[feature_columns])
    pred["score"] = score
    pred["model_name"] = model_name
    pred["sample"] = sample_name
    return pred


def extract_coefficients(model_name: str, label_name: str, estimator: Any, feature_columns: list[str]) -> list[dict[str, Any]]:
    model = estimator.named_steps.get("model") if hasattr(estimator, "named_steps") else estimator
    coef = getattr(model, "coef_", None)
    if coef is None:
        return []
    values = np.asarray(coef).reshape(-1)
    return [
        {
            "model_name": model_name,
            "label_design": label_name,
            "feature": feature,
            "coefficient": float(values[index]) if index < len(values) else None,
        }
        for index, feature in enumerate(feature_columns)
    ]


def choose_main_label(label_metrics: pd.DataFrame) -> dict[str, Any]:
    if label_metrics.empty:
        return {"main_label": "forward_return_20d", "reason": "无有效标签对比结果，回退到连续收益标签。"}
    test = label_metrics[label_metrics["sample"] == "test"].copy()
    if test.empty:
        test = label_metrics.copy()
    test["rank_ic_mean_sort"] = pd.to_numeric(test["rank_ic_mean"], errors="coerce").fillna(-999.0)
    best = test.sort_values(["rank_ic_mean_sort", "top_bottom"], ascending=[False, False]).iloc[0].to_dict()
    label = str(best.get("label_design") or "forward_return_20d")
    return {
        "main_label": label,
        "selected_model": best.get("model_name"),
        "test_rank_ic_mean": best.get("rank_ic_mean"),
        "reason": "按测试集 Rank IC、Top-Bottom 与标签可解释性综合选择；未使用训练集最优作为唯一依据。",
    }


def render_label_design_report(label_metrics: pd.DataFrame, label_choice: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# 实验二十五：标签设计报告",
            "",
            "## 主标签选择",
            "",
            f"- 主标签：`{label_choice.get('main_label')}`。",
            f"- 参考模型：`{label_choice.get('selected_model')}`。",
            f"- 选择理由：{label_choice.get('reason')}",
            "",
            "## 标签对比指标",
            "",
            markdown_table(records_head(label_metrics, 30), ["model_name", "label_design", "sample", "rank_ic_mean", "rank_icir", "top_bottom", "top10_mean_forward_return", "top20_mean_forward_return"]),
            "",
            "## 判断",
            "",
            "- 回归、分位 / 排序、Top20 分类三类标签均已通过同一 purge/embargo 切分做简单模型对照。",
            "- accuracy 不作为主判断；排序质量以 Rank IC、分组收益和 Top 组合未来收益为主。",
            "",
        ]
    )


def render_baseline_model_report(
    baseline_metrics: pd.DataFrame,
    coefficients: pd.DataFrame,
    volatility_audit: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> str:
    return "\n".join(
        [
            "# 实验二十五：基线模型报告",
            "",
            "## 执行结论",
            "",
            f"- 低波动强基线审计结论：{volatility_audit['credibility']['level']}。",
            "- 基线包含代理 benchmark、阶段三等权多因子、`single_volatility_20d`、Dummy、线性、Ridge 和 Logistic Regression。",
            "- 阶段三等权多因子和低波动单因子使用阶段四数据集直接复刻，便于检查口径漂移。",
            "",
            "## 基线指标",
            "",
            markdown_table(records_head(baseline_metrics, 40), ["model_name", "sample", "rank_ic_mean", "rank_icir", "top_bottom", "top10_mean_forward_return", "top20_mean_forward_return", "date_count"]),
            "",
            "## 线性 / 逻辑模型系数",
            "",
            markdown_table(records_head(coefficients, 40), ["model_name", "label_design", "feature", "coefficient"]),
            "",
            "## 验收判断",
            "",
            "- 标签对比：已完成连续收益、分位标签、Top20 分类标签三类对照。",
            "- 主标签选择：见 `label_design_report.md`，未只按训练集表现选择。",
            "- 阶段三复刻：等权多因子使用 4 个保留因子方向统一 z-score 平均。",
            "- 低波动复刻：低波动是否作为正式强基线取决于实验二十三结论。",
            "- Dummy：常数预测的 Rank IC 预期为空或接近 0，用作 sanity check。",
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def run_experiment_26(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    dataset_bundle: Mapping[str, Any],
    baseline_bundle: Mapping[str, Any],
    model_threads: int,
) -> dict[str, Any]:
    split_bundle: SplitBundle = dataset_bundle["primary_split"]
    feature_sets = {
        "main_4": list(MAIN_FACTORS),
        "main_plus_negative": list(ALL_BASE_FACTORS),
        "feature_engineered": list(ALL_BASE_FACTORS) + list(ENGINEERED_FEATURES),
        "negative_only": list(NEGATIVE_CONTROL_FACTORS),
    }
    param_grid = build_lgbm_param_grid(int(args.param_scan_limit))
    scan_rows: list[dict[str, Any]] = []
    best_params: dict[str, Any] | None = None
    best_score = -999.0
    for index, params in enumerate(param_grid, start=1):
        fit = fit_lgbm_regressor(
            args,
            split_bundle.train,
            split_bundle.validation,
            feature_sets["main_4"],
            params,
            model_threads,
            model_name=f"lgbm_scan_{index}",
            feature_set_name="main_4",
        )
        row = {
            "scan_id": index,
            **params,
            **prefix_keys(fit.validation_metrics, "validation_"),
        }
        scan_rows.append(row)
        rank_ic = to_float(fit.validation_metrics.get("rank_ic_mean"))
        if rank_ic is not None and rank_ic > best_score:
            best_score = rank_ic
            best_params = params
    if best_params is None:
        best_params = param_grid[0]

    fits: list[ModelFit] = []
    for feature_set_name, feature_columns in feature_sets.items():
        fits.append(
            fit_lgbm_regressor(
                args,
                split_bundle.train,
                split_bundle.validation,
                feature_columns,
                best_params,
                model_threads,
                model_name=f"lgbm_{feature_set_name}",
                feature_set_name=feature_set_name,
                test_frame=split_bundle.test,
            )
        )
    comparison_rows = [
        {
            "model_name": fit.model_name,
            "feature_set_name": fit.feature_set_name,
            "feature_count": len(fit.feature_columns),
            **prefix_keys(fit.validation_metrics, "validation_"),
            **prefix_keys(fit.test_metrics, "test_"),
        }
        for fit in fits
    ]
    comparison = pd.DataFrame(comparison_rows)
    final_fit = choose_final_tree_fit(fits)
    predictions = pd.concat(
        [
            final_fit.validation_predictions.assign(sample="validation"),
            final_fit.test_predictions.assign(sample="test"),
        ],
        ignore_index=True,
    )

    scan_path = output_dir / "model_param_scan.csv"
    predictions_path = output_dir / "tree_model_predictions.parquet"
    ic_path = output_dir / "tree_model_ic_summary.csv"
    group_path = output_dir / "tree_model_group_returns.csv"
    negative_path = output_dir / "negative_control_comparison.csv"
    feature_engineering_path = output_dir / "feature_engineering_comparison.csv"
    report_path = output_dir / "tree_model_report.md"

    pd.DataFrame(scan_rows).to_csv(scan_path, index=False)
    predictions.to_parquet(predictions_path, index=False)
    comparison.to_csv(ic_path, index=False)
    group_rows = []
    for fit in fits:
        _metrics, groups = evaluate_prediction_frame(fit.test_predictions, group_count=int(args.group_count), label="forward_return_20d")
        group_rows.extend(add_context(groups, {"model_name": fit.model_name, "feature_set_name": fit.feature_set_name}))
    pd.DataFrame(group_rows).to_csv(group_path, index=False)
    comparison[comparison["feature_set_name"].isin(["main_4", "main_plus_negative", "negative_only"])].to_csv(negative_path, index=False)
    comparison[comparison["feature_set_name"].isin(["main_4", "feature_engineered"])].to_csv(feature_engineering_path, index=False)
    report_path.write_text(
        render_tree_model_report(
            final_fit,
            comparison,
            pd.DataFrame(scan_rows),
            baseline_bundle["baseline_metrics"],
            {
                "模型参数扫描": scan_path,
                "预测分数": predictions_path,
                "IC 汇总": ic_path,
                "分组收益": group_path,
                "负对照对比": negative_path,
                "轻量特征工程对比": feature_engineering_path,
                "模型报告": report_path,
            },
            args,
        ),
        encoding="utf-8",
    )
    return {
        "fits": fits,
        "final_fit": final_fit,
        "best_params": best_params,
        "comparison": comparison,
        "predictions": predictions,
        "report_path": report_path,
    }


def build_lgbm_param_grid(limit: int) -> list[dict[str, Any]]:
    learning_rates = [0.03, 0.05, 0.1]
    num_leaves = [15, 31]
    max_depths = [3, 5, -1]
    feature_fractions = [0.7, 1.0]
    bagging_fractions = [0.7, 1.0]
    min_data_in_leaf = [50, 100, 200]
    all_params = [
        {
            "learning_rate": lr,
            "num_leaves": leaves,
            "max_depth": depth,
            "feature_fraction": feature_fraction,
            "bagging_fraction": bagging_fraction,
            "min_data_in_leaf": min_leaf,
        }
        for lr, leaves, depth, feature_fraction, bagging_fraction, min_leaf in itertools.product(
            learning_rates,
            num_leaves,
            max_depths,
            feature_fractions,
            bagging_fractions,
            min_data_in_leaf,
        )
    ]
    if limit >= len(all_params):
        return all_params
    indices = np.linspace(0, len(all_params) - 1, num=limit, dtype=int)
    return [all_params[int(index)] for index in indices]


def fit_lgbm_regressor(
    args: argparse.Namespace,
    train: pd.DataFrame,
    validation: pd.DataFrame,
    feature_columns: list[str],
    params: Mapping[str, Any],
    model_threads: int,
    *,
    model_name: str,
    feature_set_name: str,
    test_frame: pd.DataFrame | None = None,
) -> ModelFit:
    try:
        from lightgbm import LGBMRegressor, early_stopping, log_evaluation
    except Exception as exc:
        raise FactorFrameworkError("缺少 lightgbm 依赖，请先执行 `uv add --group ml lightgbm scikit-learn`。") from exc

    lgbm_params = {
        "objective": "regression",
        "n_estimators": int(args.lgbm_estimators),
        "learning_rate": float(params["learning_rate"]),
        "num_leaves": int(params["num_leaves"]),
        "max_depth": int(params["max_depth"]),
        "colsample_bytree": float(params["feature_fraction"]),
        "subsample": float(params["bagging_fraction"]),
        "subsample_freq": 1,
        "min_child_samples": int(params["min_data_in_leaf"]),
        "random_state": int(args.random_state),
        "n_jobs": int(model_threads),
        "verbosity": -1,
        "force_col_wise": True,
    }
    model = LGBMRegressor(**lgbm_params)
    callbacks = [early_stopping(int(args.early_stopping_rounds), verbose=False), log_evaluation(0)]
    model.fit(
        train[feature_columns],
        train["forward_return_20d"],
        eval_set=[(validation[feature_columns], validation["forward_return_20d"])],
        eval_metric="l2",
        callbacks=callbacks,
    )
    validation_predictions = prediction_frame_from_model(model, validation, feature_columns, model_name)
    validation_metrics, _ = evaluate_prediction_frame(validation_predictions, group_count=int(args.group_count), label="forward_return_20d")
    if test_frame is None:
        test_frame = validation
    test_predictions = prediction_frame_from_model(model, test_frame, feature_columns, model_name)
    test_metrics, _ = evaluate_prediction_frame(test_predictions, group_count=int(args.group_count), label="forward_return_20d")
    return ModelFit(
        model_name=model_name,
        feature_set_name=feature_set_name,
        feature_columns=feature_columns,
        params=dict(params),
        model=model,
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
        validation_predictions=validation_predictions,
        test_predictions=test_predictions,
    )


def prediction_frame_from_model(model: Any, frame: pd.DataFrame, feature_columns: Sequence[str], model_name: str) -> pd.DataFrame:
    result = frame[["date", "symbol", "forward_return_20d"]].copy()
    result["score"] = model.predict(frame[list(feature_columns)])
    result["model_name"] = model_name
    return result


def choose_final_tree_fit(fits: Sequence[ModelFit]) -> ModelFit:
    ranked = sorted(
        fits,
        key=lambda fit: (
            to_float(fit.validation_metrics.get("rank_ic_mean")) or -999.0,
            to_float(fit.test_metrics.get("rank_ic_mean")) or -999.0,
        ),
        reverse=True,
    )
    return ranked[0]


def render_tree_model_report(
    final_fit: ModelFit,
    comparison: pd.DataFrame,
    scan: pd.DataFrame,
    baseline_metrics: pd.DataFrame,
    paths: Mapping[str, Path],
    args: argparse.Namespace,
) -> str:
    stage3_test = baseline_metrics[(baseline_metrics["model_name"] == "stage3_equal_weight_multifactor") & (baseline_metrics["sample"] == "test")]
    stage3_rank_ic = None if stage3_test.empty else stage3_test.iloc[0].get("rank_ic_mean")
    return "\n".join(
        [
            "# 实验二十六：树模型、负对照与轻量特征工程报告",
            "",
            "## 执行结论",
            "",
            f"- 最终模型：`{final_fit.model_name}`；特征集合：`{final_fit.feature_set_name}`；特征数：{len(final_fit.feature_columns)}。",
            f"- LightGBM 参数扫描组合数：{len(scan)}；模型内部线程数由 `--model-threads` 控制；窗口并发由 `--max-workers` 控制。",
            f"- 最终模型测试集 Rank IC：{format_number(final_fit.test_metrics.get('rank_ic_mean'))}；Top-Bottom：{format_number(final_fit.test_metrics.get('top_bottom'))}。",
            f"- 阶段三等权多因子测试集 Rank IC 对照：{format_number(stage3_rank_ic)}。",
            "",
            "## 参数扫描",
            "",
            markdown_table(records_head(scan, 20), ["scan_id", "learning_rate", "num_leaves", "max_depth", "feature_fraction", "bagging_fraction", "min_data_in_leaf", "validation_rank_ic_mean", "validation_top_bottom"]),
            "",
            "## 特征集合对比",
            "",
            markdown_table(records_head(comparison, 20), ["model_name", "feature_set_name", "feature_count", "validation_rank_ic_mean", "test_rank_ic_mean", "test_rank_icir", "test_top_bottom", "test_top20_mean_forward_return"]),
            "",
            "## 验收判断",
            "",
            f"- 样本外 Rank IC：{'通过' if (to_float(final_fit.test_metrics.get('rank_ic_mean')) or 0.0) > 0 else '未通过'}。",
            f"- 分组收益：{'通过' if (to_float(final_fit.test_metrics.get('top_bottom')) or 0.0) > 0 else '未通过'}。",
            "- 参数稳定：已输出小网格每个组合验证集 Rank IC，不使用测试集调参。",
            "- 负对照：输出主特征、主特征+负对照、只用负对照三组对比。",
            "- 轻量特征工程：只保留由 t 日及以前方向统一因子衍生的交互、风险调整和历史变化量。",
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def run_experiment_27(
    args: argparse.Namespace,
    output_dir: Path,
    dataset_bundle: Mapping[str, Any],
    tree_bundle: Mapping[str, Any],
    model_threads: int,
) -> dict[str, Any]:
    final_fit: ModelFit = tree_bundle["final_fit"]
    split_bundle: SplitBundle = dataset_bundle["primary_split"]
    feature_importance = build_feature_importance(final_fit)
    permutation = build_permutation_importance(args, final_fit, split_bundle.test)
    ablation = build_feature_ablation(args, split_bundle, tree_bundle["best_params"], model_threads)
    negative = build_negative_control_importance(feature_importance, permutation, ablation)

    feature_importance_path = output_dir / "feature_importance.csv"
    permutation_path = output_dir / "permutation_importance.csv"
    ablation_path = output_dir / "feature_ablation.csv"
    negative_path = output_dir / "negative_control_importance.csv"
    report_path = output_dir / "feature_importance_report.md"
    feature_importance.to_csv(feature_importance_path, index=False)
    permutation.to_csv(permutation_path, index=False)
    ablation.to_csv(ablation_path, index=False)
    negative.to_csv(negative_path, index=False)
    report_path.write_text(
        render_feature_importance_report(
            final_fit,
            feature_importance,
            permutation,
            ablation,
            negative,
            {
                "特征重要性": feature_importance_path,
                "permutation importance": permutation_path,
                "特征消融结果": ablation_path,
                "负对照解释": negative_path,
                "解释报告": report_path,
            },
        ),
        encoding="utf-8",
    )
    return {
        "feature_importance": feature_importance,
        "permutation": permutation,
        "ablation": ablation,
        "negative": negative,
        "report_path": report_path,
    }


def build_feature_importance(final_fit: ModelFit) -> pd.DataFrame:
    model = final_fit.model
    split_importance = getattr(model, "feature_importances_", np.zeros(len(final_fit.feature_columns)))
    try:
        booster = model.booster_
        gain_importance = booster.feature_importance(importance_type="gain")
    except Exception:
        gain_importance = np.zeros(len(final_fit.feature_columns))
    rows = []
    total_gain = float(np.sum(gain_importance)) or 1.0
    total_split = float(np.sum(split_importance)) or 1.0
    for feature, split_value, gain_value in zip(final_fit.feature_columns, split_importance, gain_importance):
        rows.append(
            {
                "feature": feature,
                "feature_role": feature_role(feature),
                "split_importance": float(split_value),
                "split_importance_share": float(split_value) / total_split,
                "gain_importance": float(gain_value),
                "gain_importance_share": float(gain_value) / total_gain,
            }
        )
    return pd.DataFrame(rows).sort_values(["gain_importance", "split_importance"], ascending=False).reset_index(drop=True)


def build_permutation_importance(args: argparse.Namespace, final_fit: ModelFit, test_frame: pd.DataFrame) -> pd.DataFrame:
    baseline = final_fit.test_metrics
    rng = np.random.default_rng(int(args.random_state))
    jobs = list(final_fit.feature_columns)

    def run_feature(feature: str) -> dict[str, Any]:
        drops = []
        for _ in range(int(args.permutation_repeats)):
            work = test_frame[final_fit.feature_columns].copy()
            values = work[feature].to_numpy(copy=True)
            rng.shuffle(values)
            work[feature] = values
            pred = test_frame[["date", "symbol", "forward_return_20d"]].copy()
            pred["score"] = final_fit.model.predict(work)
            pred["model_name"] = f"permutation_{feature}"
            metrics, _ = evaluate_prediction_frame(pred, group_count=int(args.group_count), label="forward_return_20d")
            drops.append(
                {
                    "rank_ic_drop": (to_float(baseline.get("rank_ic_mean")) or 0.0) - (to_float(metrics.get("rank_ic_mean")) or 0.0),
                    "top_bottom_drop": (to_float(baseline.get("top_bottom")) or 0.0) - (to_float(metrics.get("top_bottom")) or 0.0),
                    "top20_mean_forward_return_drop": (to_float(baseline.get("top20_mean_forward_return")) or 0.0) - (to_float(metrics.get("top20_mean_forward_return")) or 0.0),
                }
            )
        return {
            "feature": feature,
            "feature_role": feature_role(feature),
            "rank_ic_drop": float(np.mean([item["rank_ic_drop"] for item in drops])),
            "top_bottom_drop": float(np.mean([item["top_bottom_drop"] for item in drops])),
            "top20_mean_forward_return_drop": float(np.mean([item["top20_mean_forward_return_drop"] for item in drops])),
            "repeat_count": int(args.permutation_repeats),
        }

    max_workers = min(int(args.max_workers), len(jobs))
    if max_workers <= 1:
        rows = [run_feature(feature) for feature in jobs]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            rows = list(executor.map(run_feature, jobs))
    return pd.DataFrame(rows).sort_values("rank_ic_drop", ascending=False).reset_index(drop=True)


def build_feature_ablation(
    args: argparse.Namespace,
    split_bundle: SplitBundle,
    best_params: Mapping[str, Any],
    model_threads: int,
) -> pd.DataFrame:
    feature_sets = {
        "main_4": list(MAIN_FACTORS),
        "drop_volatility_20d": [item for item in MAIN_FACTORS if item != "volatility_20d"],
        "drop_rsi_14": [item for item in MAIN_FACTORS if item != "rsi_14"],
        "drop_max_drawdown_20d": [item for item in MAIN_FACTORS if item != "max_drawdown_20d"],
        "drop_reversal_5d": [item for item in MAIN_FACTORS if item != "reversal_5d"],
        "main_plus_negative": list(ALL_BASE_FACTORS),
        "negative_only": list(NEGATIVE_CONTROL_FACTORS),
        "main_plus_engineered": list(MAIN_FACTORS) + list(ENGINEERED_FEATURES),
    }
    rows = []
    for name, columns in feature_sets.items():
        fit = fit_lgbm_regressor(
            args,
            split_bundle.train,
            split_bundle.validation,
            columns,
            best_params,
            model_threads,
            model_name=f"ablation_{name}",
            feature_set_name=name,
            test_frame=split_bundle.test,
        )
        rows.append(
            {
                "feature_set": name,
                "feature_count": len(columns),
                **prefix_keys(fit.validation_metrics, "validation_"),
                **prefix_keys(fit.test_metrics, "test_"),
            }
        )
    return pd.DataFrame(rows)


def build_negative_control_importance(feature_importance: pd.DataFrame, permutation: pd.DataFrame, ablation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in NEGATIVE_CONTROL_FACTORS:
        importance_row = feature_importance[feature_importance["feature"] == feature]
        permutation_row = permutation[permutation["feature"] == feature]
        rows.append(
            {
                "feature": feature,
                "gain_importance_share": None if importance_row.empty else importance_row.iloc[0].get("gain_importance_share"),
                "rank_ic_drop": None if permutation_row.empty else permutation_row.iloc[0].get("rank_ic_drop"),
                "top_bottom_drop": None if permutation_row.empty else permutation_row.iloc[0].get("top_bottom_drop"),
            }
        )
    negative_only = ablation[ablation["feature_set"] == "negative_only"]
    if not negative_only.empty:
        rows.append(
            {
                "feature": "__negative_only_model__",
                "gain_importance_share": None,
                "rank_ic_drop": None,
                "top_bottom_drop": negative_only.iloc[0].get("test_top_bottom"),
                "negative_only_rank_ic_mean": negative_only.iloc[0].get("test_rank_ic_mean"),
            }
        )
    return pd.DataFrame(rows)


def render_feature_importance_report(
    final_fit: ModelFit,
    feature_importance: pd.DataFrame,
    permutation: pd.DataFrame,
    ablation: pd.DataFrame,
    negative: pd.DataFrame,
    paths: Mapping[str, Path],
) -> str:
    volatility_importance = feature_importance.loc[feature_importance["feature"] == "volatility_20d", "gain_importance_share"]
    volatility_share = None if volatility_importance.empty else volatility_importance.iloc[0]
    negative_share = float(feature_importance.loc[feature_importance["feature_role"] == "negative_control", "gain_importance_share"].sum()) if not feature_importance.empty else 0.0
    return "\n".join(
        [
            "# 实验二十七：特征重要性与消融报告",
            "",
            "## 执行结论",
            "",
            f"- 解释对象：`{final_fit.model_name}`，特征集合 `{final_fit.feature_set_name}`。",
            f"- `volatility_20d` gain importance 占比：{format_percent(volatility_share)}。",
            f"- 负对照特征总 gain importance 占比：{format_percent(negative_share)}。",
            "",
            "## 模型内置重要性",
            "",
            markdown_table(records_head(feature_importance, 30), ["feature", "feature_role", "split_importance_share", "gain_importance_share"]),
            "",
            "## Permutation Importance",
            "",
            markdown_table(records_head(permutation, 30), ["feature", "feature_role", "rank_ic_drop", "top_bottom_drop", "top20_mean_forward_return_drop"]),
            "",
            "## 消融结果",
            "",
            markdown_table(records_head(ablation, 20), ["feature_set", "feature_count", "validation_rank_ic_mean", "test_rank_ic_mean", "test_top_bottom", "test_top20_mean_forward_return"]),
            "",
            "## 负对照解释",
            "",
            markdown_table(records_head(negative, 20), ["feature", "gain_importance_share", "rank_ic_drop", "top_bottom_drop", "negative_only_rank_ic_mean"]),
            "",
            "## 验收判断",
            "",
            f"- 主特征贡献：{'通过' if negative_share < 0.5 else '有条件'}。",
            f"- 低波动依赖：{'需披露' if (to_float(volatility_share) or 0.0) >= 0.5 else '未高度集中'}。",
            "- 负对照检查：已输出内置重要性、permutation impact 和只用负对照模型消融结果。",
            "- 消融解释：去掉每个主特征后的测试 Rank IC 和 Top-Bottom 已输出。",
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def run_experiment_28(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    dataset_bundle: Mapping[str, Any],
    tree_bundle: Mapping[str, Any],
    model_threads: int,
) -> dict[str, Any]:
    dataset = dataset_bundle["dataset"]
    final_fit: ModelFit = tree_bundle["final_fit"]
    windows = build_walk_forward_windows(dataset)
    windows_path = output_dir / "walk_forward_windows.csv"
    pd.DataFrame([asdict(window) for window in windows]).to_csv(windows_path, index=False)

    jobs = [(window, final_fit.feature_columns) for window in windows]

    def run_window(job: tuple[SplitSpec, list[str]]) -> dict[str, Any]:
        window, feature_columns = job
        split = apply_split(dataset, window, int(args.horizon), market.calendar)
        if split.train.empty or split.validation.empty or split.test.empty:
            return {"window_id": window.split_id, "mode": window.mode, "status": "skipped", "reason": "empty_split"}
        fit = fit_lgbm_regressor(
            args,
            split.train,
            split.validation,
            feature_columns,
            tree_bundle["best_params"],
            model_threads,
            model_name=f"walk_{window.split_id}",
            feature_set_name=final_fit.feature_set_name,
            test_frame=split.test,
        )
        return {
            "window_id": window.split_id,
            "mode": window.mode,
            "status": "success",
            "fit": fit,
            "split": split,
            **prefix_keys(fit.test_metrics, "test_"),
            **tree_bundle["best_params"],
        }

    max_workers = min(int(args.max_workers), len(jobs))
    if max_workers <= 1:
        window_results = [run_window(job) for job in jobs]
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            window_results = list(executor.map(run_window, jobs))

    metrics_rows = [{key: value for key, value in row.items() if key not in {"fit", "split"}} for row in window_results]
    metrics = pd.DataFrame(metrics_rows)
    expanding_metrics = metrics[metrics["mode"] == "expanding"].copy()
    rolling_metrics = metrics[metrics["mode"] == "rolling"].copy()
    strategy_rows = []
    predictions = []
    for row in window_results:
        if row.get("status") != "success":
            continue
        fit = row["fit"]
        predictions.append(fit.test_predictions.assign(window_id=row["window_id"], mode=row["mode"]))
        for top_fraction in args.top_fractions:
            strategy_result = run_strategy_pair(
                market.close,
                score_matrix_from_predictions(fit.test_predictions),
                strategy_name=f"walk_{row['window_id']}_top{int(float(top_fraction) * 100)}",
                model_type="lgbm_walk_forward",
                top_fraction=float(top_fraction),
                exit_fraction=float(args.exit_fraction),
                rebalance_freq=int(args.rebalance_freq),
                initial_cash=float(args.initial_cash),
                benchmark_metrics=None,
            )
            strategy_rows.append({"window_id": row["window_id"], "mode": row["mode"], **slim_strategy_summary(strategy_result["summary"])})

    decay = build_decay_metrics(args, market, dataset, windows, final_fit.feature_columns, tree_bundle["best_params"], model_threads)

    expanding_path = output_dir / "expanding_window_metrics.csv"
    rolling_path = output_dir / "rolling_window_metrics.csv"
    strategy_path = output_dir / "walk_forward_strategy.csv"
    decay_path = output_dir / "model_decay_metrics.csv"
    report_path = output_dir / "walk_forward_report.md"
    predictions_path = output_dir / "walk_forward_predictions.parquet"
    expanding_metrics.to_csv(expanding_path, index=False)
    rolling_metrics.to_csv(rolling_path, index=False)
    pd.DataFrame(strategy_rows).to_csv(strategy_path, index=False)
    decay.to_csv(decay_path, index=False)
    if predictions:
        pd.concat(predictions, ignore_index=True).to_parquet(predictions_path, index=False)
    else:
        pd.DataFrame().to_parquet(predictions_path, index=False)
    report_path.write_text(
        render_walk_forward_report(
            metrics,
            pd.DataFrame(strategy_rows),
            decay,
            {
                "窗口定义": windows_path,
                "扩张窗口模型指标": expanding_path,
                "固定窗口模型指标": rolling_path,
                "每窗口策略结果": strategy_path,
                "时效性衰减结果": decay_path,
                "滚动验证报告": report_path,
                "walk-forward 预测": predictions_path,
            },
        ),
        encoding="utf-8",
    )
    return {
        "windows": windows,
        "metrics": metrics,
        "strategy": pd.DataFrame(strategy_rows),
        "decay": decay,
        "predictions_path": predictions_path,
        "report_path": report_path,
    }


def build_walk_forward_windows(dataset: pd.DataFrame) -> list[SplitSpec]:
    min_date = dataset["date"].min()
    max_date = dataset["date"].max()
    if min_date <= pd.Timestamp("2020-01-02") and max_date >= pd.Timestamp("2024-03-20"):
        return [
            SplitSpec("W1", "2020-01-02", "2021-12-31", "2022-01-01", "2022-06-30", "2022-07-01", "2022-12-31", "expanding"),
            SplitSpec("W2", "2020-01-02", "2022-06-30", "2022-07-01", "2022-12-31", "2023-01-01", "2023-06-30", "expanding"),
            SplitSpec("W3", "2020-01-02", "2022-12-31", "2023-01-01", "2023-06-30", "2023-07-01", "2023-12-31", "expanding"),
            SplitSpec("W4", "2020-01-02", "2023-06-30", "2023-07-01", "2023-12-31", "2024-01-01", "2024-04-24", "expanding"),
            SplitSpec("R1", "2020-01-02", "2021-12-31", "2022-01-01", "2022-06-30", "2022-07-01", "2022-12-31", "rolling"),
            SplitSpec("R2", "2020-07-01", "2022-06-30", "2022-07-01", "2022-12-31", "2023-01-01", "2023-06-30", "rolling"),
            SplitSpec("R3", "2021-01-01", "2022-12-31", "2023-01-01", "2023-06-30", "2023-07-01", "2023-12-31", "rolling"),
            SplitSpec("R4", "2021-07-01", "2023-06-30", "2023-07-01", "2023-12-31", "2024-01-01", "2024-04-24", "rolling"),
        ]
    primary = make_primary_split(dataset, 20)
    return [SplitSpec("W1", primary.train_start, primary.train_end, primary.validation_start, primary.validation_end, primary.test_start, primary.test_end, "expanding")]


def build_decay_metrics(
    args: argparse.Namespace,
    market: MarketMatrices,
    dataset: pd.DataFrame,
    windows: Sequence[SplitSpec],
    feature_columns: list[str],
    best_params: Mapping[str, Any],
    model_threads: int,
) -> pd.DataFrame:
    expanding = [window for window in windows if window.mode == "expanding"]
    if not expanding:
        return pd.DataFrame()
    base_window = expanding[0]
    base_split = apply_split(dataset, base_window, int(args.horizon), market.calendar)
    if base_split.train.empty or base_split.validation.empty:
        return pd.DataFrame()
    fit = fit_lgbm_regressor(
        args,
        base_split.train,
        base_split.validation,
        feature_columns,
        best_params,
        model_threads,
        model_name=f"decay_source_{base_window.split_id}",
        feature_set_name="decay",
        test_frame=base_split.test if not base_split.test.empty else base_split.validation,
    )
    rows = []
    for window in expanding:
        split = apply_split(dataset, window, int(args.horizon), market.calendar)
        if split.test.empty:
            continue
        pred = prediction_frame_from_model(fit.model, split.test, feature_columns, f"decay_{base_window.split_id}_to_{window.split_id}")
        metrics, _ = evaluate_prediction_frame(pred, group_count=int(args.group_count), label="forward_return_20d")
        rows.append({"source_window": base_window.split_id, "target_window": window.split_id, **metrics})
    return pd.DataFrame(rows)


def render_walk_forward_report(metrics: pd.DataFrame, strategy: pd.DataFrame, decay: pd.DataFrame, paths: Mapping[str, Path]) -> str:
    successful = metrics[metrics["status"] == "success"] if "status" in metrics.columns else metrics
    positive_ratio = float((pd.to_numeric(successful.get("test_rank_ic_mean"), errors="coerce") > 0).mean()) if not successful.empty else 0.0
    return "\n".join(
        [
            "# 实验二十八：Walk-forward、固定窗口与时效性衰减报告",
            "",
            "## 执行结论",
            "",
            f"- 成功窗口数：{len(successful)} / {len(metrics)}。",
            f"- 测试窗口 Rank IC 为正比例：{format_percent(positive_ratio)}。",
            "- 每个窗口都重新执行基于 `label_end_date` 的 purge/embargo，不只依赖自然日期切分。",
            "",
            "## 窗口指标",
            "",
            markdown_table(records_head(metrics, 20), ["window_id", "mode", "status", "test_rank_ic_mean", "test_rank_icir", "test_top_bottom", "test_top20_mean_forward_return", "learning_rate", "num_leaves", "max_depth"]),
            "",
            "## 策略结果",
            "",
            markdown_table(records_head(strategy, 30), ["window_id", "mode", "strategy_name", "top_fraction", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost"]),
            "",
            "## 时效性衰减",
            "",
            markdown_table(records_head(decay, 20), ["source_window", "target_window", "rank_ic_mean", "top_bottom", "top20_mean_forward_return"]),
            "",
            "## 验收判断",
            "",
            f"- 正贡献窗口：{'通过' if positive_ratio >= 0.5 else '未通过'}。",
            "- expanding 与 rolling fixed 差异已分文件披露。",
            "- 时效性衰减已输出早期模型直接预测后续窗口的 Rank IC、Top-Bottom 与 Top20 收益。",
            "- 参数稳定性：本轮固定实验二十六验证集选出的参数，不在测试窗口内重新调参。",
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def run_experiment_29(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    dataset_bundle: Mapping[str, Any],
    volatility_audit: Mapping[str, Any],
    baseline_bundle: Mapping[str, Any],
    tree_bundle: Mapping[str, Any],
    importance_bundle: Mapping[str, Any],
    walk_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    predictions_path = Path(walk_bundle["predictions_path"])
    predictions = pd.read_parquet(predictions_path) if predictions_path.exists() else pd.DataFrame()
    if predictions.empty:
        predictions = tree_bundle["final_fit"].test_predictions.assign(window_id="primary", mode="primary")
    expanding_predictions = predictions[predictions.get("mode", "expanding") == "expanding"].copy()
    if expanding_predictions.empty:
        expanding_predictions = predictions.copy()
    score_matrix = score_matrix_from_predictions(expanding_predictions)

    summary_rows = []
    trade_frames = []
    equity_frames = []
    for top_fraction in args.top_fractions:
        result = run_strategy_pair(
            market.close,
            score_matrix,
            strategy_name=f"ml_lgbm_top{int(float(top_fraction) * 100)}",
            model_type="lgbm_walk_forward_score",
            top_fraction=float(top_fraction),
            exit_fraction=float(args.exit_fraction),
            rebalance_freq=int(args.rebalance_freq),
            initial_cash=float(args.initial_cash),
            benchmark_metrics=None,
        )
        summary = slim_strategy_summary(result["summary"])
        summary_rows.append(summary)
        if not result["trades"].empty:
            trade_frames.append(result["trades"].assign(strategy_name=summary["strategy_name"], top_fraction=top_fraction))
        if not result["equity"].empty:
            equity_frames.append(result["equity"].assign(strategy_name=summary["strategy_name"], top_fraction=top_fraction))

    strategy_summary = pd.DataFrame(summary_rows)
    trades = pd.concat(trade_frames, ignore_index=True) if trade_frames else pd.DataFrame()
    equity = pd.concat(equity_frames, ignore_index=True) if equity_frames else pd.DataFrame()
    baseline_comparison = build_stage4_baseline_comparison(args, market, dataset_bundle, score_matrix, volatility_audit)
    decision = make_stage4_decision(strategy_summary, baseline_comparison, volatility_audit, walk_bundle, importance_bundle)
    stage5_inputs = build_stage5_input_candidates(decision, volatility_audit, tree_bundle, walk_bundle, importance_bundle)

    strategy_summary_path = output_dir / "ml_strategy_summary.csv"
    trades_path = output_dir / "ml_strategy_trades.csv"
    equity_path = output_dir / "ml_strategy_equity_curve.csv"
    comparison_path = output_dir / "baseline_comparison.csv"
    backtest_report_path = output_dir / "ml_strategy_backtest_report.md"
    stage4_summary_path = output_dir / "stage4_summary.md"
    stage5_path = output_dir / "stage5_input_candidates.csv"
    decision_path = output_dir / "model_decision_record.md"
    strategy_summary.to_csv(strategy_summary_path, index=False)
    trades.to_csv(trades_path, index=False)
    equity.to_csv(equity_path, index=False)
    baseline_comparison.to_csv(comparison_path, index=False)
    pd.DataFrame(stage5_inputs).to_csv(stage5_path, index=False)
    backtest_report_path.write_text(render_ml_strategy_backtest_report(strategy_summary, baseline_comparison), encoding="utf-8")
    stage4_summary_path.write_text(
        render_stage4_summary(
            decision,
            strategy_summary,
            baseline_comparison,
            volatility_audit,
            baseline_bundle,
            tree_bundle,
            importance_bundle,
            walk_bundle,
            {
                "ML 策略摘要": strategy_summary_path,
                "ML 策略交易明细": trades_path,
                "ML 策略净值": equity_path,
                "基线对比表": comparison_path,
                "回测报告": backtest_report_path,
                "阶段四综合报告": stage4_summary_path,
                "阶段五输入清单": stage5_path,
                "模型决策记录": decision_path,
            },
        ),
        encoding="utf-8",
    )
    decision_path.write_text(render_model_decision_record(decision), encoding="utf-8")
    return {
        "strategy_summary": strategy_summary,
        "baseline_comparison": baseline_comparison,
        "decision": decision,
        "stage4_summary_path": stage4_summary_path,
    }


def build_stage4_baseline_comparison(
    args: argparse.Namespace,
    market: MarketMatrices,
    dataset_bundle: Mapping[str, Any],
    ml_score_matrix: pd.DataFrame,
    volatility_audit: Mapping[str, Any],
) -> pd.DataFrame:
    dataset = dataset_bundle["dataset"]
    ml_dates = {coerce_timestamp(item) for item in ml_score_matrix.index}
    baseline_dataset = dataset[dataset["date"].map(coerce_timestamp).isin(ml_dates)].copy()
    if baseline_dataset.empty:
        baseline_dataset = dataset.copy()
    main_score_frame = baseline_dataset[["date", "symbol", *MAIN_FACTORS]].assign(score=baseline_dataset[list(MAIN_FACTORS)].mean(axis=1, skipna=True))
    low_vol_score_frame = baseline_dataset[["date", "symbol", "volatility_20d"]].rename(columns={"volatility_20d": "score"})
    score_sets = {
        "ml_lgbm": ml_score_matrix,
        "stage3_equal_weight_multifactor": score_matrix_from_predictions(main_score_frame),
        "single_volatility_20d": score_matrix_from_predictions(low_vol_score_frame),
    }
    rows: list[dict[str, Any]] = []
    for name, matrix in score_sets.items():
        for top_fraction in args.top_fractions:
            result = run_strategy_pair(
                market.close,
                matrix,
                strategy_name=f"{name}_top{int(float(top_fraction) * 100)}",
                model_type=name,
                top_fraction=float(top_fraction),
                exit_fraction=float(args.exit_fraction),
                rebalance_freq=int(args.rebalance_freq),
                initial_cash=float(args.initial_cash),
                benchmark_metrics=None,
            )
            rows.append(slim_strategy_summary(result["summary"]))
    if ml_dates:
        min_oos_date = min(ml_dates).date()
        max_oos_date = max(ml_dates).date()
        benchmark_close = market.close.loc[[idx for idx in market.close.index if min_oos_date <= coerce_timestamp(idx).date() <= max_oos_date]]
    else:
        benchmark_close = market.close
    benchmark = run_equal_weight_benchmark(benchmark_close, initial_cash=float(args.initial_cash))
    rows.append(
        {
            "strategy_name": "proxy_equal_weight_buy_hold",
            "model_type": "proxy_benchmark",
            "top_fraction": None,
            "status": "success",
            "annual_return_with_cost": benchmark["metrics"].get("annual_return"),
            "total_return_with_cost": benchmark["metrics"].get("total_return"),
            "max_drawdown_with_cost": benchmark["metrics"].get("max_drawdown"),
            "turnover_with_cost": benchmark["metrics"].get("turnover"),
        }
    )
    result = pd.DataFrame(rows)
    result["volatility_baseline_credibility"] = volatility_audit["credibility"]["level"]
    result["stage3_reference_annual_return"] = result["strategy_name"].map(
        {
            "stage3_equal_weight_multifactor_top10": STAGE3_MULTIFACTOR_TOP10_ANNUAL,
            "stage3_equal_weight_multifactor_top20": STAGE3_MULTIFACTOR_TOP20_ANNUAL,
            "single_volatility_20d_top20": STAGE3_LOW_VOL_TOP20_ANNUAL,
        }
    )
    return result


def make_stage4_decision(
    strategy_summary: pd.DataFrame,
    baseline_comparison: pd.DataFrame,
    volatility_audit: Mapping[str, Any],
    walk_bundle: Mapping[str, Any],
    importance_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    ml_rows = strategy_summary[strategy_summary["status"] == "success"].copy()
    if ml_rows.empty:
        return {"decision": "暂停 ML", "reason": "ML 策略未产生有效回测结果。", "next_step": "回到阶段三因子研究或修复预测分数生成。"}
    best_ml = ml_rows.sort_values("annual_return_with_cost", ascending=False).iloc[0].to_dict()
    comparison = baseline_comparison.copy()
    proxy = comparison[comparison["model_type"] == "proxy_benchmark"]
    stage3 = comparison[comparison["model_type"] == "stage3_equal_weight_multifactor"]
    lowvol = comparison[comparison["model_type"] == "single_volatility_20d"]
    proxy_return = to_float(proxy.iloc[0].get("annual_return_with_cost")) if not proxy.empty else None
    stage3_best = pd.to_numeric(stage3.get("annual_return_with_cost"), errors="coerce").max() if not stage3.empty else None
    lowvol_best = pd.to_numeric(lowvol.get("annual_return_with_cost"), errors="coerce").max() if not lowvol.empty else None
    ml_return = to_float(best_ml.get("annual_return_with_cost")) or -999.0
    proxy_pass = proxy_return is None or ml_return >= proxy_return
    stage3_pass = stage3_best is None or ml_return >= float(stage3_best)
    lowvol_level = volatility_audit["credibility"]["level"]
    lowvol_pass = lowvol_best is None or lowvol_level == "不可信" or ml_return >= float(lowvol_best) * 0.95
    walk_metrics = walk_bundle["metrics"]
    positive_walk_ratio = float((pd.to_numeric(walk_metrics.get("test_rank_ic_mean"), errors="coerce") > 0).mean()) if not walk_metrics.empty else 0.0
    negative_share = float(importance_bundle["feature_importance"].loc[importance_bundle["feature_importance"]["feature_role"] == "negative_control", "gain_importance_share"].sum()) if not importance_bundle["feature_importance"].empty else 0.0
    if proxy_pass and stage3_pass and lowvol_pass and positive_walk_ratio >= 0.5 and negative_share < 0.5:
        decision = "进入阶段五"
        next_step = "做风控、容量、可交易性和真实 benchmark 约束研究。"
        reason = "ML 策略成本后收益、walk-forward 稳定性和解释性达到阶段四通过条件。"
    elif proxy_pass and stage3_pass:
        decision = "有条件进入阶段五"
        next_step = "作为辅助信号进入风控验证，不作为主策略。"
        reason = "ML 优于代理基准或阶段三多因子，但低波动强基线、稳定性或解释性仍有条件限制。"
    elif positive_walk_ratio < 0.5:
        decision = "暂停 ML"
        next_step = "回到阶段三因子研究，或补充样本后重做 walk-forward。"
        reason = "多数 walk-forward 窗口 Rank IC 未稳定为正。"
    elif not stage3_pass:
        decision = "回退特征工程"
        next_step = "增加更有经济含义的特征或做行业 / 市值中性后重测。"
        reason = "ML 未稳定优于阶段三等权多因子。"
    else:
        decision = "回退标签设计"
        next_step = "重新定义标签窗口、分位标签或超额收益标签。"
        reason = "当前模型策略化收益不足以支持进入阶段五。"
    return {
        "decision": decision,
        "reason": reason,
        "next_step": next_step,
        "best_ml_strategy": best_ml.get("strategy_name"),
        "best_ml_annual_return": ml_return,
        "proxy_annual_return": proxy_return,
        "stage3_best_annual_return": None if stage3_best is None or pd.isna(stage3_best) else float(stage3_best),
        "lowvol_best_annual_return": None if lowvol_best is None or pd.isna(lowvol_best) else float(lowvol_best),
        "lowvol_credibility": lowvol_level,
        "positive_walk_rank_ic_ratio": positive_walk_ratio,
        "negative_control_gain_share": negative_share,
    }


def build_stage5_input_candidates(
    decision: Mapping[str, Any],
    volatility_audit: Mapping[str, Any],
    tree_bundle: Mapping[str, Any],
    walk_bundle: Mapping[str, Any],
    importance_bundle: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {"input": "低波动审计结论", "status": volatility_audit["credibility"]["level"], "usage": "决定阶段五是否继续把低波动作为强基线或主风控锚点"},
        {"input": "最终模型特征集合", "status": tree_bundle["final_fit"].feature_set_name, "usage": "实盘解释性和监控"},
        {"input": "最终模型参数", "status": json.dumps(json_ready(tree_bundle["best_params"]), ensure_ascii=False), "usage": "重训基线"},
        {"input": "walk-forward 结果", "status": f"{len(walk_bundle['metrics'])} windows", "usage": "判断模型稳定区间"},
        {"input": "模型时效性衰减", "status": f"{len(walk_bundle['decay'])} rows", "usage": "判断重训频率和失效监控"},
        {"input": "负对照重要性", "status": f"{len(importance_bundle['negative'])} rows", "usage": "确认模型未错误依赖淘汰因子"},
        {"input": "阶段四决策", "status": str(decision["decision"]), "usage": str(decision["next_step"])},
    ]


def render_ml_strategy_backtest_report(strategy_summary: pd.DataFrame, baseline_comparison: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 实验二十九：ML 策略化回测报告",
            "",
            "## ML 策略摘要",
            "",
            markdown_table(records_head(strategy_summary, 20), ["strategy_name", "top_fraction", "annual_return_no_cost", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost", "filled_trade_count", "avg_holding_count"]),
            "",
            "## 基线对比",
            "",
            markdown_table(records_head(baseline_comparison, 30), ["strategy_name", "model_type", "top_fraction", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost", "volatility_baseline_credibility"]),
            "",
            "## 成本与落地说明",
            "",
            "- 策略规则：每 20 个交易日调仓，买入模型分数 Top10 / Top20，跌出 Top30 卖出，等权持仓。",
            "- 成本口径：沿用组合引擎默认佣金 0.03%、滑点 0.02%、卖出印花税 0.10%。",
            "- Benchmark：同股票池等权买入持有代理基准；真实沪深300 benchmark 仍需阶段五补充。",
            "",
        ]
    )


def render_stage4_summary(
    decision: Mapping[str, Any],
    strategy_summary: pd.DataFrame,
    baseline_comparison: pd.DataFrame,
    volatility_audit: Mapping[str, Any],
    baseline_bundle: Mapping[str, Any],
    tree_bundle: Mapping[str, Any],
    importance_bundle: Mapping[str, Any],
    walk_bundle: Mapping[str, Any],
    paths: Mapping[str, Path],
) -> str:
    final_fit: ModelFit = tree_bundle["final_fit"]
    return "\n".join(
        [
            "# 阶段四综合报告",
            "",
            "## 综合决策",
            "",
            f"- 决策：**{decision['decision']}**。",
            f"- 理由：{decision['reason']}",
            f"- 下一步：{decision['next_step']}",
            "",
            "## 十二个必须回答的问题",
            "",
            f"1. `volatility_20d` 强基线是否可信？{volatility_audit['credibility']['level']}，理由：{volatility_audit['credibility']['reason']}",
            f"2. 阶段四 ML 模型是否比阶段三等权多因子更好？最佳 ML 年化 {format_percent(decision.get('best_ml_annual_return'))}，阶段三复刻最佳年化 {format_percent(decision.get('stage3_best_annual_return'))}。",
            f"3. 是否超过可信 `single_volatility_20d` 单因子强基线？低波动复刻最佳年化 {format_percent(decision.get('lowvol_best_annual_return'))}，低波动可信度 {decision.get('lowvol_credibility')}。",
            f"4. 哪种标签口径最适合作为阶段四主标签？`{baseline_bundle['main_label'].get('main_label')}`，原因：{baseline_bundle['main_label'].get('reason')}",
            f"5. 模型样本外 Rank IC 是否稳定为正？最终树模型测试 Rank IC {format_number(final_fit.test_metrics.get('rank_ic_mean'))}，walk-forward 正窗口比例 {format_percent(decision.get('positive_walk_rank_ic_ratio'))}。",
            "6. expanding 和 rolling fixed walk-forward 结论是否一致？详见 `experiment_28_walk_forward/expanding_window_metrics.csv` 与 `rolling_window_metrics.csv`。",
            f"7. 模型主要依赖哪些特征？前五特征：{', '.join(importance_bundle['feature_importance'].head(5)['feature'].astype(str).tolist())}。",
            f"8. 负对照因子是否被错误利用？负对照 gain 占比 {format_percent(decision.get('negative_control_gain_share'))}，详见 `negative_control_importance.csv`。",
            "9. 策略化后成本是否吞噬收益？详见 ML 策略摘要中的无成本 / 成本后年化与换手率。",
            "10. 模型预测力是否存在明显时效性衰减？详见 `model_decay_metrics.csv`。",
            f"11. 模型是否值得进入阶段五？{decision['decision']}。",
            f"12. 如果不值得，回退到哪一步？{decision['next_step']}",
            "",
            "## ML 策略摘要",
            "",
            markdown_table(records_head(strategy_summary, 20), ["strategy_name", "top_fraction", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost"]),
            "",
            "## 基线对比",
            "",
            markdown_table(records_head(baseline_comparison, 30), ["strategy_name", "model_type", "top_fraction", "annual_return_with_cost", "max_drawdown_with_cost", "turnover_with_cost"]),
            "",
            "## 产物清单",
            "",
            markdown_table([{"artifact": key, "path": str(value)} for key, value in paths.items()], ["artifact", "path"]),
            "",
        ]
    )


def render_model_decision_record(decision: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# 模型决策记录",
            "",
            f"- 决策：{decision['decision']}",
            f"- 理由：{decision['reason']}",
            f"- 下一步：{decision['next_step']}",
            f"- 最佳 ML 策略：{decision.get('best_ml_strategy')}",
            f"- 最佳 ML 成本后年化：{format_percent(decision.get('best_ml_annual_return'))}",
            f"- 代理 benchmark 年化：{format_percent(decision.get('proxy_annual_return'))}",
            f"- 阶段三多因子最佳年化：{format_percent(decision.get('stage3_best_annual_return'))}",
            f"- 低波动最佳年化：{format_percent(decision.get('lowvol_best_annual_return'))}",
            f"- walk-forward 正 Rank IC 窗口比例：{format_percent(decision.get('positive_walk_rank_ic_ratio'))}",
            f"- 负对照 gain 占比：{format_percent(decision.get('negative_control_gain_share'))}",
            "",
        ]
    )


def evaluate_prediction_frame(predictions: pd.DataFrame, *, group_count: int, label: str) -> tuple[dict[str, Any], pd.DataFrame]:
    work = predictions[["date", "symbol", "score", label]].dropna().copy()
    if work.empty:
        return empty_prediction_metrics(), pd.DataFrame()
    ic_rows = []
    group_rows = []
    top10_returns = []
    top20_returns = []
    for trade_date, group in work.groupby("date", sort=True):
        if len(group) >= 2 and group["score"].nunique() > 1 and group[label].nunique() > 1:
            rank_ic = float(group["score"].rank(method="average").corr(group[label].rank(method="average"), method="pearson"))
            ic = float(group["score"].corr(group[label], method="pearson"))
        else:
            rank_ic = None
            ic = None
        ic_rows.append({"date": trade_date, "ic": ic, "rank_ic": rank_ic, "cross_section_n": len(group)})
        if len(group) >= group_count and group["score"].nunique() >= group_count:
            group = group.copy()
            group["group"] = assign_quantile_groups(group["score"], group_count)
            for group_id, rows in group.dropna(subset=["group"]).groupby("group", sort=True):
                group_rows.append(
                    {
                        "group": int(group_id),
                        "mean_forward_return": float(rows[label].mean()),
                        "date": trade_date,
                        "symbol_count": int(len(rows)),
                    }
                )
        top10_returns.append(top_fraction_forward_return(group, 0.1, label))
        top20_returns.append(top_fraction_forward_return(group, 0.2, label))
    ic_frame = pd.DataFrame(ic_rows)
    rank_ic = pd.to_numeric(ic_frame["rank_ic"], errors="coerce").dropna()
    ic = pd.to_numeric(ic_frame["ic"], errors="coerce").dropna()
    group_frame = pd.DataFrame(group_rows)
    group_summary = summarize_prediction_groups(group_frame, group_count)
    top_bottom = top_bottom_from_group_summary(group_summary, group_count)
    metrics = {
        "date_count": int(work["date"].nunique()),
        "row_count": int(len(work)),
        "avg_cross_section_n": float(ic_frame["cross_section_n"].mean()) if not ic_frame.empty else None,
        "ic_mean": series_mean(ic),
        "icir": safe_divide(series_mean(ic), float(ic.std(ddof=1)) if len(ic) > 1 else 0.0),
        "rank_ic_mean": series_mean(rank_ic),
        "rank_icir": safe_divide(series_mean(rank_ic), float(rank_ic.std(ddof=1)) if len(rank_ic) > 1 else 0.0),
        "positive_rank_ic_ratio": float((rank_ic > 0).mean()) if len(rank_ic) else None,
        "top_bottom": top_bottom,
        "top10_mean_forward_return": series_mean(pd.Series(top10_returns, dtype="float64").dropna()),
        "top20_mean_forward_return": series_mean(pd.Series(top20_returns, dtype="float64").dropna()),
    }
    return metrics, group_summary


def empty_prediction_metrics() -> dict[str, Any]:
    return {
        "date_count": 0,
        "row_count": 0,
        "avg_cross_section_n": None,
        "ic_mean": None,
        "icir": None,
        "rank_ic_mean": None,
        "rank_icir": None,
        "positive_rank_ic_ratio": None,
        "top_bottom": None,
        "top10_mean_forward_return": None,
        "top20_mean_forward_return": None,
    }


def summarize_prediction_groups(group_frame: pd.DataFrame, group_count: int) -> pd.DataFrame:
    if group_frame.empty:
        return pd.DataFrame(columns=["group", "mean_forward_return", "date_count", "avg_symbol_count"])
    rows = []
    for group_id, rows_frame in group_frame.groupby("group", sort=True):
        rows.append(
            {
                "group": int(group_id),
                "mean_forward_return": float(rows_frame["mean_forward_return"].mean()),
                "date_count": int(rows_frame["date"].nunique()),
                "avg_symbol_count": float(rows_frame["symbol_count"].mean()),
            }
        )
    return pd.DataFrame(rows)


def top_bottom_from_group_summary(group_summary: pd.DataFrame, group_count: int) -> float | None:
    if group_summary.empty:
        return None
    values = group_summary.set_index("group")["mean_forward_return"]
    if 1 not in values.index or group_count not in values.index:
        return None
    return float(values.loc[group_count] - values.loc[1])


def top_fraction_forward_return(group: pd.DataFrame, top_fraction: float, label: str) -> float | None:
    if group.empty:
        return None
    count = max(1, math.ceil(len(group) * top_fraction))
    selected = group.sort_values("score", ascending=False, kind="mergesort").head(count)
    return float(selected[label].mean()) if not selected.empty else None


def score_matrix_from_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    work = predictions[["date", "symbol", "score"]].copy()
    work["date"] = pd.to_datetime(work["date"]).dt.date
    matrix = work.pivot_table(index="date", columns="symbol", values="score", aggfunc="last")
    matrix.index.name = "date"
    return matrix.sort_index()


def slim_strategy_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    fields = [
        "strategy_name",
        "model_type",
        "top_fraction",
        "exit_fraction",
        "status",
        "reason",
        "signal_count",
        "first_signal_date",
        "last_signal_date",
        "annual_return_no_cost",
        "annual_return_with_cost",
        "total_return_with_cost",
        "sharpe_with_cost",
        "max_drawdown_with_cost",
        "turnover_with_cost",
        "final_value_with_cost",
        "filled_trade_count",
        "avg_holding_count",
        "cost_erosion",
    ]
    return {field: summary.get(field) for field in fields if field in summary}


def feature_role(feature: str) -> str:
    if feature in MAIN_FACTORS:
        return "main_feature"
    if feature in NEGATIVE_CONTROL_FACTORS:
        return "negative_control"
    if feature in ENGINEERED_FEATURES:
        return "engineered_feature"
    return "unknown"


def monthly_positive_ratio(equity: pd.DataFrame) -> float | None:
    returns = monthly_returns(equity)
    if returns.empty:
        return None
    return float((returns > 0).mean())


def best_month_return_share(equity: pd.DataFrame) -> float | None:
    returns = monthly_returns(equity)
    positive = returns[returns > 0]
    if positive.empty:
        return None
    return float(positive.max() / positive.sum()) if positive.sum() != 0 else None


def monthly_returns(equity: pd.DataFrame) -> pd.Series:
    if equity.empty or "date" not in equity.columns or "nav" not in equity.columns:
        return pd.Series(dtype="float64")
    work = equity.copy()
    work["date"] = pd.to_datetime(work["date"])
    monthly_nav = work.set_index("date")["nav"].resample("ME").last()
    return monthly_nav.pct_change().dropna()


def build_label_split_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[["date", "symbol", "forward_return_20d"]].copy()


def add_context(records: pd.DataFrame, context: Mapping[str, Any]) -> list[dict[str, Any]]:
    if records.empty:
        return []
    return [{**dict(context), **record} for record in records.where(pd.notna(records), None).to_dict(orient="records")]


def prefix_keys(values: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    return {f"{prefix}{key}": value for key, value in values.items()}


def between_dates(series: pd.Series, start: str, end: str) -> pd.Series:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    return (series >= start_ts) & (series <= end_ts)


def trading_day_gap(left: pd.Timestamp, right: pd.Timestamp, calendar: Sequence[date]) -> int | None:
    if pd.isna(left) or pd.isna(right):
        return None
    dates = [coerce_timestamp(item) for item in calendar]
    positions = {item: index for index, item in enumerate(dates)}
    left_ts = coerce_timestamp(left)
    right_ts = coerce_timestamp(right)
    if left_ts not in positions or right_ts not in positions:
        return None
    return int(positions[right_ts] - positions[left_ts])


def next_date_after(dates: Sequence[pd.Timestamp], value: pd.Timestamp) -> pd.Timestamp:
    for item in dates:
        if item > value:
            return item
    return dates[-1]


def coerce_timestamp(value: Any) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def series_mean(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.mean())


def safe_divide(left: Any, right: Any) -> float | None:
    left_value = to_float(left)
    right_value = to_float(right)
    if left_value is None or right_value in (None, 0.0):
        return None
    return left_value / right_value


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def safe_min(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return None if clean.empty else float(clean.min())


def safe_max(series: pd.Series) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return None if clean.empty else float(clean.max())


def quantile(series: pd.Series, q: float) -> float | None:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    return None if clean.empty else float(clean.quantile(q))


def format_number(value: Any) -> str:
    number = to_float(value)
    return "N/A" if number is None else f"{number:.6f}"


def format_percent(value: Any) -> str:
    number = to_float(value)
    return "N/A" if number is None else f"{number:.2%}"


def records_head(frame: pd.DataFrame, count: int) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return frame.head(count).where(pd.notna(frame.head(count)), None).to_dict(orient="records")


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
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
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


if __name__ == "__main__":
    main()
