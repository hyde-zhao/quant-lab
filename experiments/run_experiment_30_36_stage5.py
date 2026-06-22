"""实验三十至三十六：阶段五风控、可交易性与集成回测套件。"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import date
import json
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
from engine.portfolio import PortfolioConfig, PortfolioResult, RebalanceSignal, run_portfolio
from engine.research_paths import research_report_path
from experiments.run_experiment_15_factor_framework import FactorFrameworkError, load_local_frames, markdown_table
from experiments.run_experiment_17_21_factor_suite import (
    DEFAULT_FACTORS,
    MarketMatrices,
    build_market_matrices,
    build_multifactor_score,
    build_rebalance_signals,
    calculate_raw_factor_matrices,
    portfolio_equity_frame,
    preprocess_factor_matrices,
    select_factor_definitions,
)
from experiments.run_experiment_23_29_ml_factor_suite import MAIN_FACTORS, score_matrix_from_predictions


DEFAULT_OUTPUT_DIRS = {
    30: "experiment_30_stage5_baseline_risk",
    31: "experiment_31_drawdown_regime",
    32: "experiment_32_portfolio_constraints",
    33: "experiment_33_turnover_cost_control",
    34: "experiment_34_tradability_data_gap",
    35: "experiment_35_low_vol_enhancement",
    36: "experiment_36_stage5_summary",
}
DEFAULT_TOP_FRACTIONS = (0.1, 0.2)
DEFAULT_COST_GRID_BPS = (0, 5, 10, 20, 50, 100)
DEFAULT_AUM_GRID = (1_000_000, 5_000_000, 10_000_000, 50_000_000, 100_000_000)
DEFAULT_ML_PREDICTIONS_PATH = research_report_path("experiment_28_walk_forward", "walk_forward_predictions.parquet")
TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True, slots=True)
class StrategyRun:
    strategy_name: str
    model_type: str
    role: str
    top_fraction: float | None
    result: PortfolioResult | None
    equity: pd.DataFrame
    trades: pd.DataFrame
    summary: dict[str, Any]
    signals: list[RebalanceSignal]


@dataclass(frozen=True, slots=True)
class Stage5Result:
    report_paths: dict[str, Path]


def main() -> None:
    args = parse_args()
    result = run_stage5_suite(args)
    print("阶段五实验已完成。")
    for name, path in result.report_paths.items():
        print(f"{name}: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行阶段五风控、可交易性与集成回测套件。")
    parser.add_argument("--data-dir", required=True, help="显式传入本地标准 parquet 目录。")
    parser.add_argument("--output-root", default=str(research_report_path()))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--min-cross-section", type=int, default=5)
    parser.add_argument("--winsor-lower", type=float, default=0.01)
    parser.add_argument("--winsor-upper", type=float, default=0.99)
    parser.add_argument("--rebalance-freq", type=int, default=20)
    parser.add_argument("--top-fractions", nargs="+", type=float, default=list(DEFAULT_TOP_FRACTIONS))
    parser.add_argument("--exit-fraction", type=float, default=0.3)
    parser.add_argument("--initial-cash", type=float, default=1_000_000.0)
    parser.add_argument("--max-symbols", type=int, default=0, help="大于 0 时只取排序后的前 N 只股票，用于 smoke test。")
    parser.add_argument("--ml-predictions-path", default=str(DEFAULT_ML_PREDICTIONS_PATH))
    parser.add_argument("--preview-rows", type=int, default=2000)
    return parser.parse_args()


def run_stage5_suite(args: argparse.Namespace) -> Stage5Result:
    validate_args(args)
    output_dirs = make_output_dirs(Path(args.output_root))
    frames = load_local_frames(Path(args.data_dir))
    market = build_market_matrices(frames, args.start_date, args.end_date, max_symbols=int(args.max_symbols))
    scores = build_stage5_score_matrices(args, market)

    baseline_runs = run_baseline_strategies(args, market, scores)
    baseline_summary = pd.DataFrame([item.summary for item in baseline_runs])
    baseline_equity = concat_labeled_frames([item.equity for item in baseline_runs])
    baseline_trades = concat_labeled_frames([item.trades for item in baseline_runs])

    report_paths: dict[str, Path] = {}
    report_paths.update(write_experiment_30(args, output_dirs[30], market, baseline_runs, baseline_summary, baseline_equity, baseline_trades))
    report_paths.update(write_experiment_31(output_dirs[31], market, baseline_runs))

    constraint_runs, drawdown_overlays = run_constraint_experiments(args, market, scores, baseline_runs)
    report_paths.update(write_experiment_32(output_dirs[32], market, baseline_runs, constraint_runs, drawdown_overlays))

    turnover_runs, cost_stress, capacity, path_dependency = run_turnover_cost_experiments(args, market, scores, baseline_runs)
    report_paths.update(write_experiment_33(output_dirs[33], turnover_runs, cost_stress, capacity, path_dependency))

    tradability_coverage = build_tradability_coverage(frames, market)
    tradability_gaps = build_data_gap_register(tradability_coverage)
    report_paths.update(write_experiment_34(output_dirs[34], tradability_coverage, tradability_gaps))

    enhancement_runs, enhancement_backlog = run_low_vol_enhancement_experiments(args, market, scores, baseline_runs)
    report_paths.update(write_experiment_35(output_dirs[35], baseline_runs, enhancement_runs, enhancement_backlog))

    integrated = build_integrated_backtest_summary(baseline_runs, constraint_runs, drawdown_overlays, turnover_runs, enhancement_runs)
    p0_gap_count = int((tradability_gaps["priority"] == "P0").sum()) if not tradability_gaps.empty else 0
    report_paths.update(write_experiment_36(output_dirs[36], baseline_runs, integrated, capacity, p0_gap_count=p0_gap_count))
    return Stage5Result(report_paths=report_paths)


def validate_args(args: argparse.Namespace) -> None:
    if int(args.min_cross_section) < 2:
        raise FactorFrameworkError("min_cross_section 必须至少为 2")
    if int(args.rebalance_freq) <= 0:
        raise FactorFrameworkError("rebalance_freq 必须为正数")
    if float(args.initial_cash) <= 0:
        raise FactorFrameworkError("initial_cash 必须为正数")
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


def build_stage5_score_matrices(args: argparse.Namespace, market: MarketMatrices) -> dict[str, pd.DataFrame]:
    definitions = select_factor_definitions(list(DEFAULT_FACTORS))
    raw_matrices = calculate_raw_factor_matrices(market, definitions)
    zscore_matrices, _summary = preprocess_factor_matrices(
        raw_matrices,
        definitions,
        winsor_lower=float(args.winsor_lower),
        winsor_upper=float(args.winsor_upper),
        min_cross_section=int(args.min_cross_section),
    )
    main_factor_names = [item for item in MAIN_FACTORS if item in zscore_matrices]
    if not main_factor_names:
        raise FactorFrameworkError("阶段五需要至少一个阶段三主因子分数")
    scores = {
        "stage3_equal_weight_multifactor": build_multifactor_score(zscore_matrices, main_factor_names),
        "single_volatility_20d": zscore_matrices["volatility_20d"],
    }
    ml_score = load_ml_score_matrix(Path(str(args.ml_predictions_path)))
    if not ml_score.empty:
        scores["ml_lgbm"] = ml_score
    scores.update(build_low_vol_enhancement_scores(market, scores["single_volatility_20d"], min_cross_section=int(args.min_cross_section)))
    return scores


def load_ml_score_matrix(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    predictions = pd.read_parquet(path)
    if predictions.empty or not {"date", "symbol", "score"}.issubset(predictions.columns):
        return pd.DataFrame()
    if "mode" in predictions.columns:
        expanding = predictions[predictions["mode"].astype("string") == "expanding"].copy()
        if not expanding.empty:
            predictions = expanding
    return score_matrix_from_predictions(predictions[["date", "symbol", "score"]])


def run_baseline_strategies(args: argparse.Namespace, market: MarketMatrices, scores: Mapping[str, pd.DataFrame]) -> list[StrategyRun]:
    runs: list[StrategyRun] = []
    runs.append(run_proxy_benchmark(market.close, initial_cash=float(args.initial_cash)))
    for model_type in ("stage3_equal_weight_multifactor", "single_volatility_20d", "ml_lgbm"):
        matrix = scores.get(model_type)
        if matrix is None or matrix.empty:
            continue
        role = "ml_diagnostic" if model_type == "ml_lgbm" else "main_baseline"
        for top_fraction in args.top_fractions:
            runs.append(
                run_scored_strategy(
                    market.close,
                    matrix,
                    strategy_name=f"{model_type}_top{int(round(float(top_fraction) * 100))}",
                    model_type=model_type,
                    role=role,
                    top_fraction=float(top_fraction),
                    exit_fraction=float(args.exit_fraction),
                    rebalance_freq=int(args.rebalance_freq),
                    initial_cash=float(args.initial_cash),
                    cost_config=default_cost_config(float(args.initial_cash)),
                    cost_profile="default_a_share_cost",
                )
            )
    return runs


def run_proxy_benchmark(close_df: pd.DataFrame, *, initial_cash: float) -> StrategyRun:
    dates = list(close_df.index)
    signals = []
    if len(dates) >= 2:
        signals = [RebalanceSignal(signal_date=coerce_date(dates[0]), execution_date=coerce_date(dates[1]), target_symbols=[str(item) for item in close_df.columns])]
    result = run_portfolio(close_df, signals, default_cost_config(initial_cash)) if signals else None
    equity = portfolio_equity_frame(result) if result else pd.DataFrame()
    trades = pd.DataFrame([asdict(trade) for trade in result.trades]) if result else pd.DataFrame()
    benchmark_metrics = calculate_metrics(result) if result else {}
    summary = {
        "strategy_name": "proxy_equal_weight_buy_hold",
        "model_type": "proxy_benchmark",
        "role": "proxy_benchmark",
        "top_fraction": None,
        "exit_fraction": None,
        "rebalance_freq": None,
        "cost_profile": "default_a_share_cost",
        "status": "success",
        "signal_count": len(signals),
        **benchmark_metrics,
        **calculate_nav_risk_metrics(equity),
        **(calculate_concentration_metrics(result, close_df) if result else {}),
    }
    return StrategyRun(
        strategy_name="proxy_equal_weight_buy_hold",
        model_type="proxy_benchmark",
        role="proxy_benchmark",
        top_fraction=None,
        result=result,
        equity=label_frame(equity, "proxy_equal_weight_buy_hold", None),
        trades=label_frame(trades, "proxy_equal_weight_buy_hold", None),
        summary=json_safe(summary),
        signals=signals,
    )


def run_scored_strategy(
    close_df: pd.DataFrame,
    score_matrix: pd.DataFrame,
    *,
    strategy_name: str,
    model_type: str,
    role: str,
    top_fraction: float,
    exit_fraction: float,
    rebalance_freq: int,
    initial_cash: float,
    cost_config: PortfolioConfig,
    cost_profile: str,
) -> StrategyRun:
    signals = build_rebalance_signals(
        score_matrix,
        close_df,
        top_fraction=float(top_fraction),
        exit_fraction=float(exit_fraction),
        rebalance_freq=int(rebalance_freq),
    )
    if not signals:
        summary = {
            "strategy_name": strategy_name,
            "model_type": model_type,
            "role": role,
            "top_fraction": top_fraction,
            "exit_fraction": exit_fraction,
            "rebalance_freq": rebalance_freq,
            "cost_profile": cost_profile,
            "status": "skipped",
            "reason": "signal_schedule_empty",
            "signal_count": 0,
        }
        return StrategyRun(strategy_name, model_type, role, top_fraction, None, pd.DataFrame(), pd.DataFrame(), summary, [])
    result = run_portfolio(close_df, signals, cost_config)
    equity = portfolio_equity_frame(result)
    trades = pd.DataFrame([asdict(trade) for trade in result.trades])
    nav_metrics = calculate_nav_risk_metrics(equity)
    summary = {
        "strategy_name": strategy_name,
        "model_type": model_type,
        "role": role,
        "top_fraction": top_fraction,
        "exit_fraction": exit_fraction,
        "rebalance_freq": rebalance_freq,
        "cost_profile": cost_profile,
        "status": "success",
        "signal_count": len(signals),
        "first_signal_date": signals[0].signal_date.isoformat(),
        "last_signal_date": signals[-1].signal_date.isoformat(),
        "filled_trade_count": int((trades.get("status", pd.Series(dtype="object")) == "filled").sum()) if not trades.empty else 0,
        "turnover": float(result.turnover_amount) / max(float(initial_cash), 1.0),
        **nav_metrics,
        **calculate_concentration_metrics(result, close_df),
    }
    return StrategyRun(
        strategy_name=strategy_name,
        model_type=model_type,
        role=role,
        top_fraction=top_fraction,
        result=result,
        equity=label_frame(equity, strategy_name, top_fraction),
        trades=label_frame(trades, strategy_name, top_fraction),
        summary=json_safe(summary),
        signals=signals,
    )


def default_cost_config(initial_cash: float) -> PortfolioConfig:
    return PortfolioConfig(initial_cash=initial_cash, commission_rate=0.0003, slippage_rate=0.0002, sell_tax_rate=0.001)


def zero_cost_config(initial_cash: float) -> PortfolioConfig:
    return PortfolioConfig(initial_cash=initial_cash, commission_rate=0.0, slippage_rate=0.0, sell_tax_rate=0.0)


def total_cost_bps_config(initial_cash: float, cost_bps: float) -> PortfolioConfig:
    variable_rate = max(float(cost_bps), 0.0) / 10000.0
    return PortfolioConfig(
        initial_cash=initial_cash,
        commission_rate=variable_rate * 0.4,
        slippage_rate=variable_rate * 0.6,
        sell_tax_rate=0.001,
    )


def calculate_nav_risk_metrics(equity: pd.DataFrame) -> dict[str, Any]:
    if equity.empty or "total_value" not in equity.columns:
        return {}
    values = pd.Series(pd.to_numeric(equity["total_value"], errors="coerce").to_numpy(dtype="float64"), index=pd.to_datetime(equity["date"]))
    values = values.dropna()
    if values.empty:
        return {}
    returns = values.pct_change().dropna()
    initial = float(values.iloc[0])
    final = float(values.iloc[-1])
    years = max(len(values) / TRADING_DAYS_PER_YEAR, 1 / TRADING_DAYS_PER_YEAR)
    total_return = final / initial - 1.0 if initial > 0 else None
    annual_return = (final / initial) ** (1 / years) - 1.0 if initial > 0 else None
    annual_volatility = float(returns.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)) if not returns.empty else 0.0
    sharpe = None if annual_volatility == 0 or returns.empty else float(returns.mean() / returns.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
    running_max = values.cummax()
    drawdown = values / running_max - 1.0
    max_drawdown = float(drawdown.min())
    calmar = None if not annual_return or max_drawdown == 0 else float(annual_return / abs(max_drawdown))
    var_95 = float(returns.quantile(0.05)) if not returns.empty else None
    var_99 = float(returns.quantile(0.01)) if not returns.empty else None
    cvar_95 = float(returns[returns <= var_95].mean()) if var_95 is not None and not returns[returns <= var_95].empty else None
    cvar_99 = float(returns[returns <= var_99].mean()) if var_99 is not None and not returns[returns <= var_99].empty else None
    return {
        "start_date": values.index.min().date().isoformat(),
        "end_date": values.index.max().date().isoformat(),
        "daily_count": int(len(values)),
        "total_return": total_return,
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe": sharpe,
        "calmar": calmar,
        "max_drawdown": max_drawdown,
        "max_drawdown_recovery_days": max_drawdown_recovery_days(values),
        "daily_var_95": var_95,
        "daily_cvar_95": cvar_95,
        "daily_var_99": var_99,
        "daily_cvar_99": cvar_99,
        "best_daily_return": float(returns.max()) if not returns.empty else None,
        "worst_daily_return": float(returns.min()) if not returns.empty else None,
        "positive_day_ratio": float((returns > 0).mean()) if not returns.empty else None,
        "final_value": final,
    }


def max_drawdown_recovery_days(values: pd.Series) -> int:
    running_max = values.cummax()
    current = 0
    maximum = 0
    for value, peak in zip(values, running_max, strict=False):
        if value < peak:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return int(maximum)


def calculate_concentration_metrics(result: PortfolioResult | None, close_df: pd.DataFrame) -> dict[str, Any]:
    if result is None or not result.daily_snapshots:
        return {}
    rows = []
    for snapshot in result.daily_snapshots:
        if not snapshot.holdings:
            rows.append({"holding_count": 0, "max_weight": 0.0, "hhi": 0.0, "top10_weight": 0.0})
            continue
        try:
            prices = close_df.loc[snapshot.trade_date]
        except KeyError:
            continue
        weights = []
        for symbol, quantity in snapshot.holdings.items():
            price = prices.get(symbol)
            if price is None or pd.isna(price):
                continue
            weights.append(float(quantity) * float(price) / max(float(snapshot.total_value), 1.0))
        if not weights:
            rows.append({"holding_count": 0, "max_weight": 0.0, "hhi": 0.0, "top10_weight": 0.0})
            continue
        sorted_weights = sorted(weights, reverse=True)
        rows.append(
            {
                "holding_count": len(weights),
                "max_weight": sorted_weights[0],
                "hhi": sum(weight * weight for weight in sorted_weights),
                "top10_weight": sum(sorted_weights[:10]),
            }
        )
    if not rows:
        return {}
    frame = pd.DataFrame(rows)
    return {
        "avg_holding_count": float(frame["holding_count"].mean()),
        "min_holding_count": int(frame["holding_count"].min()),
        "max_holding_count": int(frame["holding_count"].max()),
        "avg_max_single_weight": float(frame["max_weight"].mean()),
        "max_single_weight": float(frame["max_weight"].max()),
        "avg_hhi": float(frame["hhi"].mean()),
        "max_hhi": float(frame["hhi"].max()),
        "avg_top10_weight": float(frame["top10_weight"].mean()),
    }


def write_experiment_30(
    args: argparse.Namespace,
    output_dir: Path,
    market: MarketMatrices,
    runs: Sequence[StrategyRun],
    summary: pd.DataFrame,
    equity: pd.DataFrame,
    trades: pd.DataFrame,
) -> dict[str, Path]:
    schema_path = output_dir / "risk_metric_schema.json"
    summary_path = output_dir / "baseline_strategy_summary.csv"
    equity_path = output_dir / "baseline_strategy_equity_curve.csv"
    trades_path = output_dir / "baseline_strategy_trades.csv"
    problem_path = output_dir / "STAGE5-PROBLEM-DEFINITION.md"
    report_path = output_dir / "stage5_baseline_risk_report.md"
    schema_path.write_text(json.dumps(build_risk_metric_schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary.to_csv(summary_path, index=False)
    equity.to_csv(equity_path, index=False)
    trades.to_csv(trades_path, index=False)
    problem_path.write_text(render_stage5_problem_definition(args, market, runs), encoding="utf-8")
    report_path.write_text(render_baseline_risk_report(summary, market, runs), encoding="utf-8")
    return {
        "experiment_30_schema": schema_path,
        "experiment_30_problem": problem_path,
        "experiment_30_report": report_path,
    }


def build_risk_metric_schema() -> dict[str, Any]:
    return {
        "version": "stage5-v1",
        "calendar": "日频交易日，年化按 252 个交易日计算",
        "metrics": {
            "annual_return": "由净值首尾值按交易日数量年化",
            "annual_volatility": "日收益标准差乘 sqrt(252)",
            "sharpe": "无风险利率按 0 处理，日均收益 / 日收益标准差 * sqrt(252)",
            "calmar": "年化收益 / abs(最大回撤)",
            "max_drawdown": "净值 / 历史高点 - 1 的最小值",
            "max_drawdown_recovery_days": "净值低于历史高点的最长连续交易日数",
            "daily_var_95": "日收益 5% 分位数",
            "daily_cvar_95": "小于等于 5% 分位数的日收益均值",
            "turnover": "成交名义金额 / 初始资金",
            "avg_holding_count": "日均持仓股票数",
            "avg_hhi": "日度权重平方和均值，用于集中度诊断",
            "capacity_participation_rate": "成交额占前 20 日 ADV 的比例",
        },
        "cost_assumption": {
            "default_a_share_cost": {
                "commission_rate": 0.0003,
                "slippage_rate": 0.0002,
                "sell_tax_rate": 0.001,
            }
        },
        "known_boundaries": [
            "当前数据没有行业、市值、ST、涨跌停、真实 VWAP 和真实 benchmark 全字段，相关结论只能作为研究口径。",
            "ML 分数只作为失败样本和辅助诊断，不作为阶段五主交易信号。",
        ],
    }


def render_stage5_problem_definition(args: argparse.Namespace, market: MarketMatrices, runs: Sequence[StrategyRun]) -> str:
    model_types = sorted({item.model_type for item in runs})
    return "\n".join(
        [
            "# 阶段五问题定义",
            "",
            "## 边界",
            "",
            "- 阶段五不把阶段四 ML 失败模型包装成主策略。",
            "- 主线对象是阶段三等权多因子和 `single_volatility_20d` 低波动强基线。",
            "- 代理 benchmark 只表示同股票池等权买入持有，不声明真实指数超额。",
            "- 可交易性、行业、市值和真实 benchmark 缺口必须单独披露。",
            "",
            "## 本次运行参数",
            "",
            f"- 样本区间：{market.calendar[0].isoformat()} 至 {market.calendar[-1].isoformat()}。",
            f"- 股票数：{len(market.universe)}；交易日数：{len(market.calendar)}。",
            f"- 调仓频率：每 {int(args.rebalance_freq)} 个交易日；跌出缓冲：Top {float(args.exit_fraction):.0%}。",
            f"- Top 比例：{', '.join(format_percent(item) for item in args.top_fractions)}。",
            f"- 纳入策略类型：{', '.join(model_types)}。",
            "",
            "## Go / No-Go 问题",
            "",
            "1. 低波动和多因子在默认成本后是否仍优于代理基准？",
            "2. 加入回撤、波动率、换手和成本约束后，收益是否立即消失？",
            "3. VaR / CVaR 和极端情景是否显示不可接受的尾部风险？",
            "4. 当前缺失的 P0 数据是否足以阻止模拟盘准备？",
            "5. 阶段五结束后应进入模拟盘准备、补数据重跑，还是暂停推进？",
            "",
        ]
    )


def render_baseline_risk_report(summary: pd.DataFrame, market: MarketMatrices, runs: Sequence[StrategyRun]) -> str:
    main = summary.copy()
    if not main.empty:
        main = main.sort_values(["role", "annual_return"], ascending=[True, False])
    proxy = first_row(summary, "strategy_name", "proxy_equal_weight_buy_hold")
    low_vol = summary[summary["model_type"] == "single_volatility_20d"] if "model_type" in summary else pd.DataFrame()
    low_vol_best = None if low_vol.empty else low_vol.sort_values("annual_return", ascending=False).iloc[0].to_dict()
    proxy_return = proxy.get("annual_return") if proxy else None
    low_vol_excess = None if low_vol_best is None or proxy_return is None else safe_float(low_vol_best.get("annual_return")) - safe_float(proxy_return)
    return "\n".join(
        [
            "# 实验三十：阶段五基线冻结与风险诊断",
            "",
            "## 执行结论",
            "",
            f"- 样本区间：{market.calendar[0].isoformat()} 至 {market.calendar[-1].isoformat()}；股票数 {len(market.universe)}。",
            f"- 低波动最佳策略：`{low_vol_best.get('strategy_name') if low_vol_best else 'N/A'}`，年化 {format_percent(low_vol_best.get('annual_return') if low_vol_best else None)}，相对代理基准年化差 {format_percent(low_vol_excess)}。",
            "- 阶段四 ML 只保留为诊断对照，不进入主线 go / no-go 决策。",
            "",
            "## 基线风险表",
            "",
            markdown_table(
                records_head(main, 30),
                [
                    "strategy_name",
                    "role",
                    "annual_return",
                    "annual_volatility",
                    "sharpe",
                    "calmar",
                    "max_drawdown",
                    "max_drawdown_recovery_days",
                    "daily_var_95",
                    "daily_cvar_95",
                    "turnover",
                    "avg_holding_count",
                    "avg_hhi",
                ],
            ),
            "",
            "## 初步判断",
            "",
            "- 若低波动或多因子在默认成本后仍优于代理基准，进入后续约束、成本和可交易性审计。",
            "- 若 ML 诊断策略表现较弱，不作为阶段五主信号推进。",
            "- 所有收益结论仍受真实 benchmark、行业、市值和交易状态字段缺失限制。",
            "",
            "## 产物清单",
            "",
            markdown_table(
                [
                    {"artifact": "风险指标口径", "path": "risk_metric_schema.json"},
                    {"artifact": "基线策略摘要", "path": "baseline_strategy_summary.csv"},
                    {"artifact": "基线净值曲线", "path": "baseline_strategy_equity_curve.csv"},
                    {"artifact": "基线交易明细", "path": "baseline_strategy_trades.csv"},
                ],
                ["artifact", "path"],
            ),
            "",
        ]
    )


def write_experiment_31(output_dir: Path, market: MarketMatrices, runs: Sequence[StrategyRun]) -> dict[str, Path]:
    yearly = pd.concat([build_period_return_table(item, "YE") for item in runs if not item.equity.empty], ignore_index=True)
    monthly = pd.concat([build_period_return_table(item, "ME") for item in runs if not item.equity.empty], ignore_index=True)
    tail = pd.DataFrame([build_tail_risk_row(item) for item in runs if not item.equity.empty])
    stress = pd.DataFrame([row for item in runs if not item.equity.empty for row in build_stress_rows(item)])
    contribution = build_symbol_contribution_table(select_primary_low_vol_run(runs), market.close)

    yearly_path = output_dir / "yearly_regime_metrics.csv"
    monthly_path = output_dir / "monthly_regime_metrics.csv"
    tail_path = output_dir / "tail_risk_summary.csv"
    stress_path = output_dir / "stress_test_summary.csv"
    contribution_path = output_dir / "symbol_contribution_proxy.csv"
    drawdown_report_path = output_dir / "drawdown_regime_report.md"
    tail_report_path = output_dir / "tail_risk_stress_report.md"

    yearly.to_csv(yearly_path, index=False)
    monthly.to_csv(monthly_path, index=False)
    tail.to_csv(tail_path, index=False)
    stress.to_csv(stress_path, index=False)
    contribution.to_csv(contribution_path, index=False)
    drawdown_report_path.write_text(render_drawdown_regime_report(yearly, monthly, contribution), encoding="utf-8")
    tail_report_path.write_text(render_tail_risk_report(tail, stress), encoding="utf-8")
    return {
        "experiment_31_drawdown": drawdown_report_path,
        "experiment_31_tail": tail_report_path,
    }


def build_period_return_table(run: StrategyRun, freq: str) -> pd.DataFrame:
    values = pd.Series(pd.to_numeric(run.equity["total_value"], errors="coerce").to_numpy(dtype="float64"), index=pd.to_datetime(run.equity["date"]))
    period = values.resample(freq).agg(["first", "last"])
    period = period[period["first"].notna() & period["last"].notna()].copy()
    period["period_return"] = period["last"] / period["first"] - 1.0
    period["strategy_name"] = run.strategy_name
    period["model_type"] = run.model_type
    period["period"] = period.index.strftime("%Y" if freq == "YE" else "%Y-%m")
    return period[["strategy_name", "model_type", "period", "period_return"]].reset_index(drop=True)


def build_tail_risk_row(run: StrategyRun) -> dict[str, Any]:
    metrics = calculate_nav_risk_metrics(run.equity)
    returns = pd.Series(pd.to_numeric(run.equity["total_value"], errors="coerce").to_numpy(dtype="float64")).pct_change().dropna()
    return {
        "strategy_name": run.strategy_name,
        "model_type": run.model_type,
        "daily_var_95": metrics.get("daily_var_95"),
        "daily_cvar_95": metrics.get("daily_cvar_95"),
        "daily_var_99": metrics.get("daily_var_99"),
        "daily_cvar_99": metrics.get("daily_cvar_99"),
        "worst_5d_return": rolling_return(returns, 5),
        "worst_20d_return": rolling_return(returns, 20),
        "worst_60d_return": rolling_return(returns, 60),
        "max_drawdown": metrics.get("max_drawdown"),
        "annual_return": metrics.get("annual_return"),
    }


def build_stress_rows(run: StrategyRun) -> list[dict[str, Any]]:
    returns = pd.Series(pd.to_numeric(run.equity["total_value"], errors="coerce").to_numpy(dtype="float64")).pct_change().dropna()
    worst_20d = rolling_return(returns, 20)
    worst_60d = rolling_return(returns, 60)
    scenarios = [
        ("synthetic_2015_liquidity_crash", -0.12, "单日 -12% 冲击，用于代理股灾流动性压力。"),
        ("synthetic_2018_bear_grind", min((worst_60d or 0.0) * 1.5, -0.08), "最差 60 日收益放大 1.5 倍。"),
        ("synthetic_2020_panic_window", min((worst_20d or 0.0) * 1.5, -0.06), "最差 20 日收益放大 1.5 倍。"),
    ]
    return [
        {
            "strategy_name": run.strategy_name,
            "model_type": run.model_type,
            "scenario": scenario,
            "shock_return": shock,
            "post_shock_nav_multiplier": 1.0 + shock,
            "note": note,
        }
        for scenario, shock, note in scenarios
    ]


def build_symbol_contribution_table(run: StrategyRun | None, close_df: pd.DataFrame) -> pd.DataFrame:
    if run is None or run.result is None:
        return pd.DataFrame(columns=["strategy_name", "symbol", "contribution", "abs_contribution_share"])
    returns = close_df.pct_change(fill_method=None)
    contributions: dict[str, float] = {}
    previous_snapshot = None
    for snapshot in run.result.daily_snapshots:
        if previous_snapshot is None:
            previous_snapshot = snapshot
            continue
        try:
            day_returns = returns.loc[snapshot.trade_date]
            prices = close_df.loc[previous_snapshot.trade_date]
        except KeyError:
            previous_snapshot = snapshot
            continue
        for symbol, quantity in previous_snapshot.holdings.items():
            ret = day_returns.get(symbol)
            price = prices.get(symbol)
            if ret is None or price is None or pd.isna(ret) or pd.isna(price):
                continue
            weight = float(quantity) * float(price) / max(float(previous_snapshot.total_value), 1.0)
            contributions[symbol] = contributions.get(symbol, 0.0) + weight * float(ret)
        previous_snapshot = snapshot
    total_abs = sum(abs(value) for value in contributions.values()) or 1.0
    rows = [
        {
            "strategy_name": run.strategy_name,
            "symbol": symbol,
            "contribution": value,
            "abs_contribution_share": abs(value) / total_abs,
        }
        for symbol, value in contributions.items()
    ]
    return pd.DataFrame(rows).sort_values("abs_contribution_share", ascending=False).head(50).reset_index(drop=True)


def render_drawdown_regime_report(yearly: pd.DataFrame, monthly: pd.DataFrame, contribution: pd.DataFrame) -> str:
    concentration_note = "N/A"
    if not contribution.empty:
        concentration_note = format_percent(float(contribution["abs_contribution_share"].head(10).sum()))
    return "\n".join(
        [
            "# 实验三十一：回撤、时间窗口与收益来源拆解",
            "",
            "## 执行结论",
            "",
            f"- 低波动主策略前 10 个股票贡献绝对占比：{concentration_note}。",
            "- 年度和月度拆解用于检查收益是否过度集中在少数时间段。",
            "- 股票贡献为基于日初持仓权重与当日收益的代理拆解，不等同于逐笔成交归因。",
            "",
            "## 年度收益",
            "",
            markdown_table(records_head(yearly, 40), ["strategy_name", "period", "period_return"]),
            "",
            "## 月度收益 Top/Bottom 样例",
            "",
            markdown_table(records_head(monthly.sort_values("period_return"), 20), ["strategy_name", "period", "period_return"]),
            "",
            "## 低波动股票贡献 Top 20",
            "",
            markdown_table(records_head(contribution, 20), ["symbol", "contribution", "abs_contribution_share"]),
            "",
        ]
    )


def render_tail_risk_report(tail: pd.DataFrame, stress: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 实验三十一：尾部风险与极端情景压力测试",
            "",
            "## 尾部风险",
            "",
            markdown_table(
                records_head(tail, 30),
                ["strategy_name", "daily_var_95", "daily_cvar_95", "daily_var_99", "daily_cvar_99", "worst_20d_return", "worst_60d_return", "max_drawdown"],
            ),
            "",
            "## 极端情景",
            "",
            markdown_table(records_head(stress, 60), ["strategy_name", "scenario", "shock_return", "post_shock_nav_multiplier", "note"]),
            "",
            "## 限制",
            "",
            "- 样本未覆盖完整 2015 股灾；极端情景使用合成冲击和历史最差窗口放大，只能作为压力代理。",
            "- 当前没有真实涨跌停、停牌细项和盘中成交路径，因此压力测试不声明真实可成交。",
            "",
        ]
    )


def run_constraint_experiments(
    args: argparse.Namespace,
    market: MarketMatrices,
    scores: Mapping[str, pd.DataFrame],
    baseline_runs: Sequence[StrategyRun],
) -> tuple[list[StrategyRun], pd.DataFrame]:
    runs: list[StrategyRun] = []
    for model_type in ("single_volatility_20d", "stage3_equal_weight_multifactor"):
        matrix = scores.get(model_type)
        if matrix is None or matrix.empty:
            continue
        for top_fraction in args.top_fractions:
            runs.append(
                run_scored_strategy(
                    market.close,
                    matrix,
                    strategy_name=f"{model_type}_top{int(float(top_fraction) * 100)}_buffer40_freq40",
                    model_type=model_type,
                    role="turnover_constraint",
                    top_fraction=float(top_fraction),
                    exit_fraction=0.4,
                    rebalance_freq=max(int(args.rebalance_freq), 40),
                    initial_cash=float(args.initial_cash),
                    cost_config=default_cost_config(float(args.initial_cash)),
                    cost_profile="default_a_share_cost",
                )
            )
    overlay_rows = []
    for run in [item for item in baseline_runs if item.model_type in {"single_volatility_20d", "stage3_equal_weight_multifactor"}]:
        if run.equity.empty:
            continue
        vol_overlay = apply_volatility_target_overlay(run, target_annual_vol=0.10, lookback=60, max_exposure=1.0)
        dd_overlay = apply_drawdown_pause_overlay(run, pause_threshold=-0.15, recovery_threshold=-0.05)
        overlay_rows.append(vol_overlay)
        overlay_rows.append(dd_overlay)
    drawdown_overlays = pd.DataFrame(overlay_rows)
    return runs, drawdown_overlays


def apply_volatility_target_overlay(run: StrategyRun, *, target_annual_vol: float, lookback: int, max_exposure: float) -> dict[str, Any]:
    values = pd.Series(pd.to_numeric(run.equity["total_value"], errors="coerce").to_numpy(dtype="float64"), index=pd.to_datetime(run.equity["date"]))
    returns = values.pct_change().fillna(0.0)
    realized = returns.rolling(lookback, min_periods=max(5, min(lookback, 20))).std(ddof=0).shift(1) * math.sqrt(TRADING_DAYS_PER_YEAR)
    exposure = (float(target_annual_vol) / realized.replace(0, np.nan)).clip(lower=0.0, upper=float(max_exposure)).fillna(1.0)
    overlay_returns = returns * exposure
    nav = (1.0 + overlay_returns).cumprod() * float(values.iloc[0])
    equity = pd.DataFrame({"date": nav.index.strftime("%Y-%m-%d"), "total_value": nav.to_numpy(dtype="float64")})
    metrics = calculate_nav_risk_metrics(equity)
    return {
        "strategy_name": f"{run.strategy_name}_vol_target_10pct",
        "source_strategy": run.strategy_name,
        "overlay_type": "volatility_target",
        "target_annual_vol": target_annual_vol,
        "avg_exposure": float(exposure.mean()),
        **metrics,
    }


def apply_drawdown_pause_overlay(run: StrategyRun, *, pause_threshold: float, recovery_threshold: float) -> dict[str, Any]:
    values = pd.Series(pd.to_numeric(run.equity["total_value"], errors="coerce").to_numpy(dtype="float64"), index=pd.to_datetime(run.equity["date"]))
    raw_returns = values.pct_change().fillna(0.0)
    raw_drawdown = values / values.cummax() - 1.0
    nav_values = [float(values.iloc[0])]
    paused = False
    paused_days = 0
    for index in range(1, len(values)):
        if paused and float(raw_drawdown.iloc[index - 1]) >= recovery_threshold:
            paused = False
        day_return = 0.0 if paused else float(raw_returns.iloc[index])
        if paused:
            paused_days += 1
        next_nav = nav_values[-1] * (1.0 + day_return)
        nav_values.append(next_nav)
        current_peak = max(nav_values)
        overlay_drawdown = next_nav / current_peak - 1.0 if current_peak > 0 else 0.0
        if not paused and overlay_drawdown <= pause_threshold:
            paused = True
    equity = pd.DataFrame({"date": values.index.strftime("%Y-%m-%d"), "total_value": nav_values})
    metrics = calculate_nav_risk_metrics(equity)
    return {
        "strategy_name": f"{run.strategy_name}_drawdown_pause_15pct",
        "source_strategy": run.strategy_name,
        "overlay_type": "drawdown_pause",
        "pause_threshold": pause_threshold,
        "recovery_threshold": recovery_threshold,
        "paused_days": paused_days,
        **metrics,
    }


def write_experiment_32(
    output_dir: Path,
    market: MarketMatrices,
    baseline_runs: Sequence[StrategyRun],
    constraint_runs: Sequence[StrategyRun],
    drawdown_overlays: pd.DataFrame,
) -> dict[str, Path]:
    concentration = pd.DataFrame([item.summary for item in baseline_runs])
    constraints = pd.DataFrame([item.summary for item in constraint_runs])
    concentration_path = output_dir / "concentration_summary.csv"
    constraints_path = output_dir / "portfolio_constraint_summary.csv"
    drawdown_path = output_dir / "drawdown_control_summary.csv"
    position_report_path = output_dir / "position_concentration_report.md"
    constraint_report_path = output_dir / "portfolio_constraint_report.md"
    drawdown_report_path = output_dir / "drawdown_control_report.md"
    concentration.to_csv(concentration_path, index=False)
    constraints.to_csv(constraints_path, index=False)
    drawdown_overlays.to_csv(drawdown_path, index=False)
    position_report_path.write_text(render_position_concentration_report(concentration, market), encoding="utf-8")
    constraint_report_path.write_text(render_portfolio_constraint_report(concentration, constraints, drawdown_overlays), encoding="utf-8")
    drawdown_report_path.write_text(render_drawdown_control_report(drawdown_overlays), encoding="utf-8")
    return {
        "experiment_32_position": position_report_path,
        "experiment_32_constraints": constraint_report_path,
        "experiment_32_drawdown": drawdown_report_path,
    }


def render_position_concentration_report(concentration: pd.DataFrame, market: MarketMatrices) -> str:
    return "\n".join(
        [
            "# 实验三十二：持仓集中度诊断",
            "",
            "## 执行结论",
            "",
            f"- 股票池数量：{len(market.universe)}。",
            "- 当前 Top10% / Top20% 口径持仓数量较多，单票权重和 HHI 主要用于识别是否存在异常集中，而非少数个股组合。",
            "- 本报告只回答“现状如何”，约束后变化见 `portfolio_constraint_report.md`。",
            "",
            "## 集中度表",
            "",
            markdown_table(
                records_head(concentration, 30),
                ["strategy_name", "avg_holding_count", "min_holding_count", "max_holding_count", "avg_max_single_weight", "max_single_weight", "avg_hhi", "avg_top10_weight"],
            ),
            "",
        ]
    )


def render_portfolio_constraint_report(base: pd.DataFrame, constraints: pd.DataFrame, overlays: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 实验三十二：组合约束与仓位控制报告",
            "",
            "## 干预设计",
            "",
            "- `buffer40_freq40`：跌出 Top40% 才卖出，并把调仓间隔放宽到至少 40 个交易日，用于测试低换手约束。",
            "- `vol_target_10pct`：使用过去 60 日已实现波动率估算仓位，目标年化波动 10%，最大暴露 100%。",
            "- `drawdown_pause_15pct`：组合回撤触达 -15% 后暂停，原始策略回撤恢复到 -5% 以内后恢复。",
            "",
            "## 原始策略",
            "",
            markdown_table(records_head(base, 20), ["strategy_name", "annual_return", "annual_volatility", "max_drawdown", "turnover", "avg_holding_count"]),
            "",
            "## 缓冲与低频调仓",
            "",
            markdown_table(records_head(constraints, 20), ["strategy_name", "annual_return", "annual_volatility", "max_drawdown", "turnover", "avg_holding_count"]),
            "",
            "## 仓位控制 Overlay",
            "",
            markdown_table(records_head(overlays, 40), ["strategy_name", "overlay_type", "annual_return", "annual_volatility", "max_drawdown", "sharpe", "avg_exposure", "paused_days"]),
            "",
            "## 判断",
            "",
            "- 若低换手约束后 alpha 完全消失，说明收益对高频换仓依赖较强。",
            "- 若波动率目标或回撤暂停只靠长期空仓改善回撤，应降级为风险提示，不能作为可实盘规则。",
            "",
        ]
    )


def render_drawdown_control_report(overlays: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 实验三十二：回撤控制状态机",
            "",
            "## 状态机规则",
            "",
            "| 状态 | 进入条件 | 行为 | 恢复条件 |",
            "| --- | --- | --- | --- |",
            "| active | 初始状态或恢复条件满足 | 按原策略收益暴露 | 组合回撤触达 -15% 切换 pause |",
            "| pause | active 状态下回撤触达 -15% | 日收益置 0，视作现金等待 | 原始策略回撤恢复到 -5% 以内 |",
            "",
            "## 结果",
            "",
            markdown_table(records_head(overlays[overlays.get("overlay_type") == "drawdown_pause"], 20), ["strategy_name", "annual_return", "max_drawdown", "paused_days", "sharpe"]),
            "",
            "## 限制",
            "",
            "- 当前实现是组合净值 overlay，不是逐笔订单级暂停；真实执行仍需接入交易状态、委托撤单和现金管理。",
            "",
        ]
    )


def run_turnover_cost_experiments(
    args: argparse.Namespace,
    market: MarketMatrices,
    scores: Mapping[str, pd.DataFrame],
    baseline_runs: Sequence[StrategyRun],
) -> tuple[list[StrategyRun], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    runs: list[StrategyRun] = []
    base_matrix = scores["single_volatility_20d"]
    for exit_fraction, freq in ((0.3, 20), (0.4, 20), (0.4, 40)):
        for top_fraction in args.top_fractions:
            runs.append(
                run_scored_strategy(
                    market.close,
                    base_matrix,
                    strategy_name=f"single_volatility_20d_top{int(float(top_fraction) * 100)}_exit{int(exit_fraction * 100)}_freq{freq}",
                    model_type="single_volatility_20d",
                    role="turnover_cost_control",
                    top_fraction=float(top_fraction),
                    exit_fraction=exit_fraction,
                    rebalance_freq=freq,
                    initial_cash=float(args.initial_cash),
                    cost_config=default_cost_config(float(args.initial_cash)),
                    cost_profile="default_a_share_cost",
                )
            )
    primary = select_primary_low_vol_run(baseline_runs)
    if primary is None:
        primary = runs[0] if runs else None
    cost_stress = build_cost_stress_grid(args, market, base_matrix)
    capacity = build_capacity_sensitivity(primary, market, initial_cash=float(args.initial_cash)) if primary else pd.DataFrame()
    path_dependency = build_path_dependency_summary(primary) if primary else pd.DataFrame()
    return runs, cost_stress, capacity, path_dependency


def build_cost_stress_grid(args: argparse.Namespace, market: MarketMatrices, score_matrix: pd.DataFrame) -> pd.DataFrame:
    rows = []
    top_fraction = float(args.top_fractions[0])
    for cost_bps in DEFAULT_COST_GRID_BPS:
        run = run_scored_strategy(
            market.close,
            score_matrix,
            strategy_name=f"single_volatility_20d_top{int(top_fraction * 100)}_cost{cost_bps}bps",
            model_type="single_volatility_20d",
            role="cost_stress",
            top_fraction=top_fraction,
            exit_fraction=float(args.exit_fraction),
            rebalance_freq=int(args.rebalance_freq),
            initial_cash=float(args.initial_cash),
            cost_config=zero_cost_config(float(args.initial_cash)) if cost_bps == 0 else total_cost_bps_config(float(args.initial_cash), cost_bps),
            cost_profile=f"variable_cost_{cost_bps}bps_plus_sell_tax",
        )
        rows.append(run.summary)
    return pd.DataFrame(rows)


def build_capacity_sensitivity(run: StrategyRun, market: MarketMatrices, *, initial_cash: float) -> pd.DataFrame:
    if run.trades.empty or market.amount.empty:
        return pd.DataFrame()
    amount = market.amount.copy()
    amount.index = pd.to_datetime(amount.index)
    adv20 = amount.rolling(20, min_periods=5).mean().shift(1)
    trades = run.trades.copy()
    trades = trades[trades.get("status", "filled") == "filled"].copy()
    if trades.empty:
        return pd.DataFrame()
    trades["execution_date"] = pd.to_datetime(trades["execution_date"])
    rows = []
    for aum in DEFAULT_AUM_GRID:
        scale = float(aum) / float(initial_cash)
        participations = []
        impact_costs = []
        missing_adv = 0
        for row in trades.to_dict(orient="records"):
            symbol = str(row.get("symbol"))
            execution_date = pd.Timestamp(row.get("execution_date"))
            notional = abs(float(row.get("notional") or 0.0)) * scale
            try:
                adv = adv20.loc[execution_date, symbol]
            except Exception:
                adv = np.nan
            if pd.isna(adv) or float(adv) <= 0:
                missing_adv += 1
                continue
            participation = notional / float(adv)
            participations.append(participation)
            impact_bps = participation * 100.0
            impact_costs.append(notional * impact_bps / 10000.0)
        part = pd.Series(participations, dtype="float64")
        rows.append(
            {
                "strategy_name": run.strategy_name,
                "aum": float(aum),
                "trade_count": int(len(trades)),
                "missing_adv_count": int(missing_adv),
                "max_participation_rate": float(part.max()) if not part.empty else None,
                "p95_participation_rate": float(part.quantile(0.95)) if not part.empty else None,
                "breach_10pct_adv_rate": float((part > 0.10).mean()) if not part.empty else None,
                "estimated_impact_cost": float(sum(impact_costs)),
                "estimated_impact_cost_bps_of_aum": float(sum(impact_costs)) / float(aum) * 10000.0 if aum else None,
                "capacity_status": "pass" if not part.empty and float(part.quantile(0.95)) <= 0.10 else "warn",
            }
        )
    return pd.DataFrame(rows)


def build_path_dependency_summary(run: StrategyRun) -> pd.DataFrame:
    if run.result is None or run.trades.empty:
        return pd.DataFrame()
    trades = run.trades.copy()
    trades = trades[trades.get("status", "filled") == "filled"].copy()
    if trades.empty:
        return pd.DataFrame()
    trades["execution_date"] = pd.to_datetime(trades["execution_date"]).dt.date
    snapshots = run.result.daily_snapshots
    previous_cash_by_date: dict[date, float] = {}
    for index, snapshot in enumerate(snapshots):
        if index == 0:
            previous_cash_by_date[snapshot.trade_date] = snapshot.cash
        else:
            previous_cash_by_date[snapshot.trade_date] = snapshots[index - 1].cash
    rows = []
    for (execution_date, rebalance_key), group in trades.groupby(["execution_date", "rebalance_key"], dropna=False):
        buy_notional = float(group[group["side"] == "buy"]["notional"].sum())
        buy_cost = float(group[group["side"] == "buy"]["cost"].sum())
        sell_notional = float(group[group["side"] == "sell"]["notional"].sum())
        start_cash = float(previous_cash_by_date.get(execution_date, 0.0))
        buy_first_cash_gap = max(0.0, buy_notional + buy_cost - start_cash)
        rows.append(
            {
                "strategy_name": run.strategy_name,
                "execution_date": execution_date.isoformat() if isinstance(execution_date, date) else str(execution_date),
                "rebalance_key": rebalance_key,
                "start_cash": start_cash,
                "sell_notional": sell_notional,
                "buy_notional": buy_notional,
                "buy_first_cash_gap": buy_first_cash_gap,
                "sell_then_buy_cash_gap": 0.0,
            }
        )
    return pd.DataFrame(rows)


def write_experiment_33(
    output_dir: Path,
    turnover_runs: Sequence[StrategyRun],
    cost_stress: pd.DataFrame,
    capacity: pd.DataFrame,
    path_dependency: pd.DataFrame,
) -> dict[str, Path]:
    turnover = pd.DataFrame([item.summary for item in turnover_runs])
    turnover_path = output_dir / "turnover_cost_summary.csv"
    cost_path = output_dir / "cost_stress_summary.csv"
    capacity_path = output_dir / "capacity_sensitivity.csv"
    path_path = output_dir / "path_dependency_summary.csv"
    turnover_report_path = output_dir / "turnover_cost_control_report.md"
    cost_report_path = output_dir / "cost_stress_test_report.md"
    turnover.to_csv(turnover_path, index=False)
    cost_stress.to_csv(cost_path, index=False)
    capacity.to_csv(capacity_path, index=False)
    path_dependency.to_csv(path_path, index=False)
    turnover_report_path.write_text(render_turnover_report(turnover, path_dependency), encoding="utf-8")
    cost_report_path.write_text(render_cost_stress_report(cost_stress, capacity), encoding="utf-8")
    return {
        "experiment_33_turnover": turnover_report_path,
        "experiment_33_cost": cost_report_path,
    }


def render_turnover_report(turnover: pd.DataFrame, path_dependency: pd.DataFrame) -> str:
    gap_count = int((path_dependency.get("buy_first_cash_gap", pd.Series(dtype="float64")) > 0).sum()) if not path_dependency.empty else 0
    return "\n".join(
        [
            "# 实验三十三：换手、调仓频率与调仓路径",
            "",
            "## 换手控制结果",
            "",
            markdown_table(records_head(turnover, 30), ["strategy_name", "annual_return", "max_drawdown", "turnover", "avg_holding_count", "filled_trade_count"]),
            "",
            "## 调仓路径依赖",
            "",
            f"- 若改为先买后卖，发生现金缺口的调仓批次：{gap_count}。",
            "- 当前组合引擎采用先卖后买；路径依赖表用于提示现金约束风险。",
            "",
            markdown_table(records_head(path_dependency.sort_values("buy_first_cash_gap", ascending=False) if not path_dependency.empty else path_dependency, 20), ["execution_date", "sell_notional", "buy_notional", "buy_first_cash_gap"]),
            "",
        ]
    )


def render_cost_stress_report(cost_stress: pd.DataFrame, capacity: pd.DataFrame) -> str:
    capacity_pass = capacity[capacity.get("capacity_status") == "pass"] if not capacity.empty else pd.DataFrame()
    max_pass_aum = None if capacity_pass.empty else float(capacity_pass["aum"].max())
    return "\n".join(
        [
            "# 实验三十三：成本压力、冲击成本与容量测试",
            "",
            "## 成本压力测试",
            "",
            markdown_table(records_head(cost_stress, 30), ["strategy_name", "cost_profile", "annual_return", "max_drawdown", "turnover", "sharpe"]),
            "",
            "## 容量敏感性",
            "",
            f"- 以 p95 成交参与率不超过 10% ADV 为保守通过线，当前通过 AUM 上限：{format_money(max_pass_aum)}。",
            "- 冲击成本采用简化线性代理：参与率每 1% ADV 约 1bp 额外成本；不等同于真实最优执行模型。",
            "",
            markdown_table(records_head(capacity, 20), ["aum", "p95_participation_rate", "max_participation_rate", "breach_10pct_adv_rate", "estimated_impact_cost_bps_of_aum", "capacity_status"]),
            "",
        ]
    )


def write_experiment_34(output_dir: Path, coverage: pd.DataFrame, gaps: pd.DataFrame) -> dict[str, Path]:
    coverage_path = output_dir / "tradability_field_coverage.csv"
    gap_path = output_dir / "data_gap_register.csv"
    report_path = output_dir / "tradability_data_gap_report.md"
    benchmark_path = output_dir / "benchmark_neutralization_plan.md"
    coverage.to_csv(coverage_path, index=False)
    gaps.to_csv(gap_path, index=False)
    report_path.write_text(render_tradability_gap_report(coverage, gaps), encoding="utf-8")
    benchmark_path.write_text(render_benchmark_neutralization_plan(), encoding="utf-8")
    return {
        "experiment_34_tradability": report_path,
        "experiment_34_benchmark_plan": benchmark_path,
    }


def build_tradability_coverage(frames: Mapping[str, pd.DataFrame], market: MarketMatrices) -> pd.DataFrame:
    prices = frames["prices"]
    total_rows = max(len(prices), 1)
    checks = [
        ("close", "成交价格代理", "P0", "close", "prices"),
        ("volume", "成交量 / ADV 来源", "P0", "volume", "prices"),
        ("amount", "成交额 / 容量来源", "P0", "amount", "prices"),
        ("is_suspended", "停牌状态", "P0", "is_suspended", "prices"),
        ("is_limit_up", "涨停不可买", "P0", "is_limit_up", "prices"),
        ("is_limit_down", "跌停不可卖", "P0", "is_limit_down", "prices"),
        ("st_flag", "ST 风险过滤", "P0", "st_flag", "prices"),
        ("turnover_rate", "换手率", "P0", "turnover_rate", "prices"),
        ("vwap", "真实 VWAP", "P1", "vwap", "prices"),
        ("open", "开盘成交价格", "P1", "open", "prices"),
        ("industry", "行业分类", "P0", "industry", "index_members"),
        ("market_cap", "市值 / 流通市值", "P0", "market_cap", "index_members"),
        ("real_benchmark", "真实沪深300 / 中证500 benchmark", "P0", None, "external"),
    ]
    rows = []
    for field, description, priority, column, dataset in checks:
        if dataset == "prices" and column in prices.columns:
            non_null = int(prices[column].notna().sum())
            coverage = non_null / total_rows
            status = "available" if coverage >= 0.95 else "partial"
        elif dataset == "index_members" and column in frames["index_members"].columns:
            members = frames["index_members"]
            non_null = int(members[column].notna().sum())
            coverage = non_null / max(len(members), 1)
            status = "available" if coverage >= 0.95 else "partial"
        else:
            non_null = 0
            coverage = 0.0
            status = "missing"
        rows.append(
            {
                "field": field,
                "description": description,
                "priority": priority,
                "dataset": dataset,
                "status": status,
                "non_null_count": non_null,
                "coverage_ratio": coverage,
                "sample_start": market.calendar[0].isoformat(),
                "sample_end": market.calendar[-1].isoformat(),
            }
        )
    return pd.DataFrame(rows)


def build_data_gap_register(coverage: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in coverage.to_dict(orient="records"):
        if row["status"] == "available":
            continue
        rows.append(
            {
                "field": row["field"],
                "priority": row["priority"],
                "gap_status": row["status"],
                "impact": data_gap_impact(str(row["field"])),
                "recommended_action": data_gap_action(str(row["field"])),
            }
        )
    return pd.DataFrame(rows)


def data_gap_impact(field: str) -> str:
    impacts = {
        "real_benchmark": "不能声明真实指数超额或 beta 暴露。",
        "industry": "无法判断低波动收益是否来自防御行业暴露。",
        "market_cap": "无法判断低波动收益是否来自大小盘暴露。",
        "is_limit_up": "无法判断买入是否受涨停约束。",
        "is_limit_down": "无法判断卖出是否受跌停约束。",
        "st_flag": "无法剔除 ST 或风险警示股票。",
        "vwap": "无法声明真实 VWAP 成交。",
        "open": "无法测试开盘成交路径。",
    }
    return impacts.get(field, "影响可交易性、容量或风格解释。")


def data_gap_action(field: str) -> str:
    if field == "real_benchmark":
        return "优先补沪深300、中证500、中证全指日收益和成分权重。"
    if field == "industry":
        return "优先补申万一级 / 二级行业，记录版本和缺失处理。"
    if field == "market_cap":
        return "补总市值和流通市值，支持分层与中性化。"
    if field in {"is_limit_up", "is_limit_down", "st_flag"}:
        return "补交易状态和价格限制字段后重跑阶段五主策略。"
    return "纳入 P0/P1 补数字段清单并重跑相关审计。"


def render_tradability_gap_report(coverage: pd.DataFrame, gaps: pd.DataFrame) -> str:
    p0_gaps = gaps[gaps["priority"] == "P0"] if not gaps.empty else pd.DataFrame()
    return "\n".join(
        [
            "# 实验三十四：可交易性与数据缺口审计",
            "",
            "## 执行结论",
            "",
            f"- P0 缺口数量：{len(p0_gaps)}。",
            "- 当前已有 `volume` / `amount` 可做 ADV 和容量代理，但缺真实 benchmark、行业、市值、ST 和涨跌停字段。",
            "- 因此阶段五最多支持研究级有条件结论，不支持直接模拟盘声明。",
            "",
            "## 字段覆盖",
            "",
            markdown_table(records_head(coverage, 30), ["field", "priority", "status", "coverage_ratio", "description"]),
            "",
            "## 缺口登记",
            "",
            markdown_table(records_head(gaps, 30), ["field", "priority", "gap_status", "impact", "recommended_action"]),
            "",
        ]
    )


def render_benchmark_neutralization_plan() -> str:
    return "\n".join(
        [
            "# Benchmark 与中性化设计",
            "",
            "## 真实 Benchmark",
            "",
            "- P0：补沪深300、中证500、中证全指日收益、成分股、权重和数据版本。",
            "- 当前代理基准只代表同股票池等权买入持有，不能写成指数超额。",
            "",
            "## 行业分类",
            "",
            "- 优先申万一级 / 二级；若数据源不可得，再考虑中信或 GICS。",
            "- 必须记录分类版本、覆盖率、缺失样本处理和调仓日可得性。",
            "",
            "## 市值中性",
            "",
            "- P0：补总市值和流通市值。",
            "- 先做分层诊断，再考虑行业内 / 市值分层排序；不在字段缺失时声明 size-neutral alpha。",
            "",
            "## 最小重跑集",
            "",
            "1. 阶段三因子 IC 与分组收益重跑。",
            "2. 阶段四 ML 负对照和 walk-forward 重跑。",
            "3. 阶段五风险、成本、容量和可交易性审计重跑。",
            "",
        ]
    )


def build_low_vol_enhancement_scores(market: MarketMatrices, low_vol_score: pd.DataFrame, *, min_cross_section: int) -> dict[str, pd.DataFrame]:
    close = market.close
    returns = close.pct_change(fill_method=None)
    downside = returns.clip(upper=0.0).pow(2).rolling(20, min_periods=20).mean().pow(0.5)
    vol = returns.rolling(20, min_periods=20).std(ddof=0)
    vol_change = vol - vol.shift(20)
    recovery = close / close.rolling(20, min_periods=20).max() - 1.0
    adv20 = market.amount.rolling(20, min_periods=20).mean()
    liquidity_mask = adv20.ge(adv20.median(axis=1), axis=0)
    z_downside = cross_section_zscore(-downside, min_cross_section=min_cross_section)
    z_vol_change = cross_section_zscore(-vol_change, min_cross_section=min_cross_section)
    z_recovery = cross_section_zscore(recovery, min_cross_section=min_cross_section)
    filtered_low_vol = low_vol_score.where(liquidity_mask)
    return {
        "low_vol_plus_downside": combine_score_matrices([low_vol_score, z_downside]),
        "low_vol_plus_vol_change": combine_score_matrices([low_vol_score, z_vol_change]),
        "low_vol_plus_recovery": combine_score_matrices([low_vol_score, z_recovery]),
        "low_vol_liquidity_filtered": filtered_low_vol,
    }


def cross_section_zscore(matrix: pd.DataFrame, *, min_cross_section: int) -> pd.DataFrame:
    def transform(row: pd.Series) -> pd.Series:
        valid = row.dropna()
        if len(valid) < min_cross_section:
            return pd.Series(np.nan, index=row.index)
        std = float(valid.std(ddof=0))
        if std == 0 or math.isnan(std):
            return pd.Series(np.nan, index=row.index)
        return (row - float(valid.mean())) / std

    return matrix.apply(transform, axis=1)


def combine_score_matrices(matrices: Sequence[pd.DataFrame]) -> pd.DataFrame:
    aligned = [matrix.astype("float64") for matrix in matrices]
    total = sum(aligned)
    count = sum(matrix.notna().astype("int64") for matrix in aligned)
    return total / count.replace(0, np.nan)


def run_low_vol_enhancement_experiments(
    args: argparse.Namespace,
    market: MarketMatrices,
    scores: Mapping[str, pd.DataFrame],
    baseline_runs: Sequence[StrategyRun],
) -> tuple[list[StrategyRun], pd.DataFrame]:
    runs: list[StrategyRun] = []
    for score_name in ("low_vol_plus_downside", "low_vol_plus_vol_change", "low_vol_plus_recovery", "low_vol_liquidity_filtered"):
        matrix = scores.get(score_name)
        if matrix is None or matrix.empty:
            continue
        for top_fraction in args.top_fractions:
            runs.append(
                run_scored_strategy(
                    market.close,
                    matrix,
                    strategy_name=f"{score_name}_top{int(float(top_fraction) * 100)}",
                    model_type=score_name,
                    role="low_vol_enhancement",
                    top_fraction=float(top_fraction),
                    exit_fraction=float(args.exit_fraction),
                    rebalance_freq=int(args.rebalance_freq),
                    initial_cash=float(args.initial_cash),
                    cost_config=default_cost_config(float(args.initial_cash)),
                    cost_profile="default_a_share_cost",
                )
            )
    baseline_lookup = {item.top_fraction: item.summary for item in baseline_runs if item.model_type == "single_volatility_20d"}
    backlog = build_low_vol_feature_backlog(runs, baseline_lookup)
    return runs, backlog


def build_low_vol_feature_backlog(runs: Sequence[StrategyRun], baseline_lookup: Mapping[float | None, Mapping[str, Any]]) -> pd.DataFrame:
    rows = []
    descriptions = {
        "low_vol_plus_downside": "下行波动越低越好，区分上涨波动与下跌风险。",
        "low_vol_plus_vol_change": "波动率变化越低越好，识别风险状态恶化。",
        "low_vol_plus_recovery": "回撤修复越接近新高越好，识别低波动中的修复能力。",
        "low_vol_liquidity_filtered": "保留 ADV20 高于当日中位数的股票，避免不可交易暴露。",
    }
    for run in runs:
        base = baseline_lookup.get(run.top_fraction, {})
        delta = safe_float(run.summary.get("annual_return")) - safe_float(base.get("annual_return")) if base else None
        rows.append(
            {
                "feature_name": run.model_type,
                "strategy_name": run.strategy_name,
                "top_fraction": run.top_fraction,
                "economic_meaning": descriptions.get(run.model_type, ""),
                "leakage_check": "仅使用 t 日及以前的 rolling close/amount 数据。",
                "annual_return": run.summary.get("annual_return"),
                "baseline_annual_return": base.get("annual_return"),
                "annual_return_delta": delta,
                "max_drawdown": run.summary.get("max_drawdown"),
                "turnover": run.summary.get("turnover"),
                "integrated_candidate": delta is not None and delta > 0 and safe_float(run.summary.get("max_drawdown")) >= safe_float(base.get("max_drawdown")) - 0.05,
            }
        )
    return pd.DataFrame(rows)


def write_experiment_35(
    output_dir: Path,
    baseline_runs: Sequence[StrategyRun],
    enhancement_runs: Sequence[StrategyRun],
    backlog: pd.DataFrame,
) -> dict[str, Path]:
    summary = pd.DataFrame([item.summary for item in enhancement_runs])
    summary_path = output_dir / "low_vol_enhancement_summary.csv"
    backlog_path = output_dir / "low_vol_feature_backlog.csv"
    backlog_md_path = output_dir / "low_vol_feature_backlog.md"
    report_path = output_dir / "low_vol_enhancement_report.md"
    summary.to_csv(summary_path, index=False)
    backlog.to_csv(backlog_path, index=False)
    backlog_md_path.write_text(render_low_vol_feature_backlog(backlog), encoding="utf-8")
    report_path.write_text(render_low_vol_enhancement_report(baseline_runs, summary, backlog), encoding="utf-8")
    return {
        "experiment_35_backlog": backlog_md_path,
        "experiment_35_report": report_path,
    }


def render_low_vol_feature_backlog(backlog: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 低波动增强特征 Backlog",
            "",
            "## 候选特征",
            "",
            markdown_table(records_head(backlog, 40), ["feature_name", "economic_meaning", "leakage_check", "integrated_candidate"]),
            "",
            "## 边界",
            "",
            "- 不做无约束特征搜索。",
            "- 所有增强必须与原始 `single_volatility_20d` 同周期、同成本、同股票池对比。",
            "- 若收益来自行业、市值或可交易性缺口，结论必须降级。",
            "",
        ]
    )


def render_low_vol_enhancement_report(baseline_runs: Sequence[StrategyRun], summary: pd.DataFrame, backlog: pd.DataFrame) -> str:
    low_vol_base = pd.DataFrame([item.summary for item in baseline_runs if item.model_type == "single_volatility_20d"])
    return "\n".join(
        [
            "# 实验三十五：低波动增强验证",
            "",
            "## 原始低波动对照",
            "",
            markdown_table(records_head(low_vol_base, 10), ["strategy_name", "annual_return", "max_drawdown", "turnover", "sharpe"]),
            "",
            "## 增强结果",
            "",
            markdown_table(records_head(summary, 30), ["strategy_name", "annual_return", "max_drawdown", "turnover", "sharpe", "avg_holding_count"]),
            "",
            "## 是否进入集成回测",
            "",
            markdown_table(records_head(backlog, 30), ["strategy_name", "annual_return_delta", "max_drawdown", "turnover", "integrated_candidate"]),
            "",
            "## 判断",
            "",
            "- 增强特征只有在同口径优于原始低波动且不显著恶化回撤时，才进入阶段五集成候选。",
            "- 流动性过滤若改善风险但牺牲收益，仍可保留为补数据后重跑候选。",
            "",
        ]
    )


def build_integrated_backtest_summary(
    baseline_runs: Sequence[StrategyRun],
    constraint_runs: Sequence[StrategyRun],
    overlays: pd.DataFrame,
    turnover_runs: Sequence[StrategyRun],
    enhancement_runs: Sequence[StrategyRun],
) -> pd.DataFrame:
    rows = []
    for source, runs in (
        ("baseline", baseline_runs),
        ("constraint", constraint_runs),
        ("turnover_cost", turnover_runs),
        ("low_vol_enhancement", enhancement_runs),
    ):
        for run in runs:
            if run.summary.get("status") != "success":
                continue
            rows.append({"source": source, **run.summary})
    if not overlays.empty:
        for row in overlays.to_dict(orient="records"):
            rows.append({"source": "risk_overlay", "role": "risk_overlay", "model_type": row.get("overlay_type"), **row})
    frame = pd.DataFrame(rows)
    if not frame.empty and "annual_return" in frame:
        frame = frame.sort_values(["annual_return", "max_drawdown"], ascending=[False, False]).reset_index(drop=True)
    return frame


def write_experiment_36(
    output_dir: Path,
    baseline_runs: Sequence[StrategyRun],
    integrated: pd.DataFrame,
    capacity: pd.DataFrame,
    *,
    p0_gap_count: int,
) -> dict[str, Path]:
    integrated_path = output_dir / "integrated_backtest_summary.csv"
    report_path = output_dir / "stage5_integrated_backtest_report.md"
    summary_path = output_dir / "stage5_summary.md"
    integrated.to_csv(integrated_path, index=False)
    decision = make_stage5_decision(baseline_runs, integrated, capacity, p0_gap_count=p0_gap_count)
    report_path.write_text(render_integrated_backtest_report(integrated), encoding="utf-8")
    summary_path.write_text(render_stage5_summary(decision, integrated, capacity), encoding="utf-8")
    return {
        "experiment_36_integrated": report_path,
        "experiment_36_summary": summary_path,
    }


def make_stage5_decision(
    baseline_runs: Sequence[StrategyRun],
    integrated: pd.DataFrame,
    capacity: pd.DataFrame,
    *,
    p0_gap_count: int,
) -> dict[str, Any]:
    proxy = next((item.summary for item in baseline_runs if item.model_type == "proxy_benchmark"), {})
    main = [item.summary for item in baseline_runs if item.model_type in {"single_volatility_20d", "stage3_equal_weight_multifactor"}]
    proxy_return = safe_float(proxy.get("annual_return"))
    best_main = max(main, key=lambda row: safe_float(row.get("annual_return")), default={})
    best_excess = safe_float(best_main.get("annual_return")) - proxy_return if best_main else None
    capacity_pass = capacity[capacity.get("capacity_status") == "pass"] if not capacity.empty else pd.DataFrame()
    max_capacity = None if capacity_pass.empty else float(capacity_pass["aum"].max())
    if best_main and best_excess is not None and best_excess > 0 and max_capacity:
        decision = "有条件通过"
        next_action = "补齐 P0 数据后重跑阶段三至阶段五关键实验，再决定是否进入小规模模拟盘。"
    elif best_main and best_excess is not None and best_excess > 0:
        decision = "有条件通过"
        next_action = "优先补容量和可交易性数据，暂不进入模拟盘。"
    else:
        decision = "失败"
        next_action = "暂停策略推进，回退特征工程与数据质量审计。"
    return {
        "decision": decision,
        "best_main_strategy": best_main.get("strategy_name"),
        "best_main_annual_return": best_main.get("annual_return"),
        "proxy_annual_return": proxy_return,
        "best_excess_annual_return": best_excess,
        "max_capacity_pass_aum": max_capacity,
        "p0_gap_count": p0_gap_count,
        "next_action": next_action,
    }


def render_integrated_backtest_report(integrated: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 实验三十六：阶段五集成回测报告",
            "",
            "## 集成候选排序",
            "",
            markdown_table(
                records_head(integrated, 40),
                ["source", "strategy_name", "model_type", "annual_return", "annual_volatility", "sharpe", "max_drawdown", "turnover", "avg_holding_count"],
            ),
            "",
            "## 解释",
            "",
            "- 集成表同时保留原始基线、低换手约束、风险 overlay 和低波动增强，不只选择收益最高组合。",
            "- ML 诊断策略若出现在表内，只用于解释阶段四失败样本，不作为阶段五主策略候选。",
            "",
        ]
    )


def render_stage5_summary(decision: Mapping[str, Any], integrated: pd.DataFrame, capacity: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# 阶段五总结",
            "",
            "## 1. 决策结论",
            "",
            f"- 决策：**{decision.get('decision')}**。",
            f"- 是否进入模拟盘准备：{'否，需先补 P0 数据并重跑。' if decision.get('decision') == '有条件通过' else '否。'}",
            f"- 下一步：{decision.get('next_action')}",
            "",
            "## 2. 主策略结论",
            "",
            f"- 最佳主策略：`{decision.get('best_main_strategy')}`。",
            f"- 最佳主策略年化：{format_percent(decision.get('best_main_annual_return'))}；代理基准年化：{format_percent(decision.get('proxy_annual_return'))}；年化差：{format_percent(decision.get('best_excess_annual_return'))}。",
            "",
            "## 3. 风险与尾部风险",
            "",
            "- 已输出最大回撤、恢复期、VaR / CVaR 和合成极端情景压力测试。",
            "- 风险 overlay 可改善部分回撤指标，但不能替代真实交易状态与流动性验证。",
            "",
            "## 4. 成本、容量与可交易性",
            "",
            f"- p95 参与率通过的保守 AUM 上限：{format_money(decision.get('max_capacity_pass_aum'))}。",
            f"- P0 数据缺口数量：{decision.get('p0_gap_count')}；缺口阻止直接进入模拟盘。",
            "",
            "## 5. Benchmark 与中性化",
            "",
            "- 当前不能声明真实指数超额。",
            "- 需要补真实 benchmark、申万 / 中信行业、市值 / 流通市值后，重跑低波动暴露诊断。",
            "",
            "## 6. 补数据工作量预估",
            "",
            "| 数据项 | 优先级 | 预估工作量 |",
            "| --- | --- | --- |",
            "| 真实 benchmark 与成分权重 | P0 | 1-2 天接入与覆盖校验 |",
            "| ST、涨跌停、停牌细项、上市天数 | P0 | 1-2 天接入与交易门控重跑 |",
            "| 行业分类 | P0 | 1 天接入，1 天中性化验证 |",
            "| 市值 / 流通市值 | P0 | 1-2 天接入与分层验证 |",
            "",
            "## 7. 最小重跑实验集",
            "",
            "1. 阶段三：因子 IC、分组收益、多因子 Top10 / Top20。",
            "2. 阶段四：ML 负对照、walk-forward 和模型决策记录。",
            "3. 阶段五：基线风险、成本容量、可交易性、低波动增强和集成回测。",
            "",
            "## 8. 下一步行动",
            "",
            "- 不进入正式模拟盘。",
            "- 先补 P0 数据，重跑阶段三至阶段五最小实验集。",
            "- 若补数后低波动仍优于代理和真实 benchmark，再设计小规模模拟盘 runbook。",
            "",
            "## 集成结果摘录",
            "",
            markdown_table(records_head(integrated, 20), ["source", "strategy_name", "annual_return", "max_drawdown", "turnover"]),
            "",
            "## 容量摘录",
            "",
            markdown_table(records_head(capacity, 10), ["aum", "p95_participation_rate", "estimated_impact_cost_bps_of_aum", "capacity_status"]),
            "",
        ]
    )


def select_primary_low_vol_run(runs: Sequence[StrategyRun]) -> StrategyRun | None:
    candidates = [item for item in runs if item.model_type == "single_volatility_20d" and item.summary.get("status") == "success"]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: safe_float(item.summary.get("annual_return")), reverse=True)[0]


def concat_labeled_frames(frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [frame for frame in frames if not frame.empty]
    normalized = [frame.dropna(axis=1, how="all") for frame in non_empty]
    return pd.concat(normalized, ignore_index=True, sort=False) if normalized else pd.DataFrame()


def label_frame(frame: pd.DataFrame, strategy_name: str, top_fraction: float | None) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.copy()
    result["strategy_name"] = strategy_name
    result["top_fraction"] = top_fraction
    return result


def first_row(frame: pd.DataFrame, column: str, value: Any) -> dict[str, Any] | None:
    if frame.empty or column not in frame.columns:
        return None
    rows = frame[frame[column] == value]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def records_head(frame: pd.DataFrame, rows: int) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []
    return [json_safe(row) for row in frame.head(rows).to_dict(orient="records")]


def rolling_return(returns: pd.Series, window: int) -> float | None:
    if len(returns) < window:
        return None
    values = (1.0 + returns).rolling(window).apply(np.prod, raw=True) - 1.0
    return float(values.min())


def coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def safe_float(value: Any) -> float:
    try:
        if value is None or pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if math.isnan(float(value)) else float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def format_percent(value: Any) -> str:
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):.2%}"
    except Exception:
        return "N/A"


def format_money(value: Any) -> str:
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):,.0f}"
    except Exception:
        return "N/A"


if __name__ == "__main__":
    main()
