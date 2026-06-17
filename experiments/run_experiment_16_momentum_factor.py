"""实验十六：动量因子有效性检验。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import math
from pathlib import Path
import sys
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.run_experiment_15_factor_framework import (
    FORWARD_HORIZONS,
    FactorFrameworkError,
    build_factor_panel,
    build_matrices,
    format_value,
    load_local_frames,
    markdown_table,
    parse_factor_specs,
)


DEFAULT_MOMENTUM_FACTORS = ("momentum_5d", "momentum_20d", "momentum_60d")
DEFAULT_GROUP_COUNT = 5
DEFAULT_MIN_CROSS_SECTION = 5


@dataclass(frozen=True, slots=True)
class Experiment16Result:
    report_path: Path
    factor_panel_path: Path
    ic_timeseries_path: Path
    ic_summary_path: Path
    group_timeseries_path: Path
    group_returns_path: Path
    top_bottom_path: Path
    data_coverage_path: Path


def main() -> None:
    args = parse_args()
    result = run_momentum_factor_validation(args)
    print(f"报告已生成: {result.report_path}")
    print(f"IC 汇总已生成: {result.ic_summary_path}")
    print(f"分组收益已生成: {result.group_returns_path}")
    print(f"数据覆盖评估已生成: {result.data_coverage_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行实验十六动量因子有效性检验。")
    parser.add_argument("--data-dir", default="data", help="本地标准 parquet 目录。")
    parser.add_argument("--output-dir", default="reports/experiment_16")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--factors", nargs="+", default=list(DEFAULT_MOMENTUM_FACTORS))
    parser.add_argument("--group-count", type=int, default=DEFAULT_GROUP_COUNT, help="分组收益的横截面分组数。")
    parser.add_argument("--min-cross-section", type=int, default=DEFAULT_MIN_CROSS_SECTION, help="计算 IC 的最小横截面股票数。")
    parser.add_argument("--preview-rows", type=int, default=2000, help="因子面板 CSV 预览行数。")
    return parser.parse_args()


def run_momentum_factor_validation(args: argparse.Namespace) -> Experiment16Result:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.group_count < 2:
        raise FactorFrameworkError("group_count 必须至少为 2")
    if args.min_cross_section < 2:
        raise FactorFrameworkError("min_cross_section 必须至少为 2")

    specs = parse_factor_specs(args.factors)
    non_momentum = [spec.name for spec in specs if spec.family != "momentum"]
    if non_momentum:
        raise FactorFrameworkError("实验十六仅支持 momentum 因子: " + ", ".join(non_momentum))

    frames = load_local_frames(Path(args.data_dir))
    close_df, volume_df, universe, calendar = build_matrices(frames, args.start_date, args.end_date)
    factor_panel = build_factor_panel(close_df, volume_df, specs)
    if factor_panel.empty:
        raise FactorFrameworkError("动量因子面板为空")

    factor_panel_path = output_dir / "momentum_factor_panel.parquet"
    factor_panel.to_parquet(factor_panel_path, index=False)
    factor_panel.head(max(int(args.preview_rows), 0)).to_csv(output_dir / "momentum_factor_panel_preview.csv", index=False)

    ic_timeseries = calculate_ic_timeseries(factor_panel, min_cross_section=int(args.min_cross_section))
    ic_summary = summarize_ic(ic_timeseries)
    group_timeseries = calculate_group_timeseries(factor_panel, group_count=int(args.group_count))
    group_returns = summarize_group_returns(group_timeseries)
    top_bottom = summarize_top_bottom(group_timeseries, group_count=int(args.group_count))
    data_coverage = summarize_data_coverage(
        frames=frames,
        close_df=close_df,
        calendar=calendar,
        universe=universe,
        factor_panel=factor_panel,
        factor_windows={spec.name: spec.window for spec in specs},
    )

    ic_timeseries_path = output_dir / "ic_timeseries.csv"
    ic_summary_path = output_dir / "ic_summary.csv"
    group_timeseries_path = output_dir / "group_timeseries.csv"
    group_returns_path = output_dir / "group_returns.csv"
    top_bottom_path = output_dir / "top_bottom_spread.csv"
    data_coverage_path = output_dir / "data_coverage.csv"
    ic_timeseries.to_csv(ic_timeseries_path, index=False)
    ic_summary.to_csv(ic_summary_path, index=False)
    group_timeseries.to_csv(group_timeseries_path, index=False)
    group_returns.to_csv(group_returns_path, index=False)
    top_bottom.to_csv(top_bottom_path, index=False)
    data_coverage.to_csv(data_coverage_path, index=False)

    report_path = output_dir / "momentum_factor_report.md"
    report_path.write_text(
        render_report(
            args=args,
            close_df=close_df,
            universe=universe,
            calendar=calendar,
            factor_panel=factor_panel,
            ic_summary=ic_summary,
            group_returns=group_returns,
            top_bottom=top_bottom,
            data_coverage=data_coverage,
            paths={
                "report": report_path,
                "factor_panel": factor_panel_path,
                "ic_timeseries": ic_timeseries_path,
                "ic_summary": ic_summary_path,
                "group_timeseries": group_timeseries_path,
                "group_returns": group_returns_path,
                "top_bottom": top_bottom_path,
                "data_coverage": data_coverage_path,
            },
        ),
        encoding="utf-8",
    )
    return Experiment16Result(
        report_path=report_path,
        factor_panel_path=factor_panel_path,
        ic_timeseries_path=ic_timeseries_path,
        ic_summary_path=ic_summary_path,
        group_timeseries_path=group_timeseries_path,
        group_returns_path=group_returns_path,
        top_bottom_path=top_bottom_path,
        data_coverage_path=data_coverage_path,
    )


def calculate_ic_timeseries(factor_panel: pd.DataFrame, *, min_cross_section: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, factor_group in factor_panel.groupby("factor_name", sort=True):
        for horizon in FORWARD_HORIZONS:
            target_col = f"forward_return_{horizon}d"
            for trade_date, day_group in factor_group.groupby("date", sort=True):
                valid = day_group[["factor_value", target_col]].dropna()
                n = int(len(valid))
                ic = None
                rank_ic = None
                if n >= min_cross_section and _has_variation(valid["factor_value"]) and _has_variation(valid[target_col]):
                    ic = float(valid["factor_value"].corr(valid[target_col], method="pearson"))
                    rank_ic = _spearman_corr(valid["factor_value"], valid[target_col])
                rows.append(
                    {
                        "factor_name": str(factor_name),
                        "horizon": f"{horizon}d",
                        "date": str(trade_date),
                        "ic": ic,
                        "rank_ic": rank_ic,
                        "cross_section_n": n,
                    }
                )
    return pd.DataFrame(rows)


def summarize_ic(ic_timeseries: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (factor_name, horizon), group in ic_timeseries.groupby(["factor_name", "horizon"], sort=True):
        ic = pd.to_numeric(group["ic"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        ic_std = float(ic.std(ddof=1)) if len(ic) > 1 else 0.0
        rank_std = float(rank_ic.std(ddof=1)) if len(rank_ic) > 1 else 0.0
        rows.append(
            {
                "factor_name": factor_name,
                "horizon": horizon,
                "observation_days": int(len(group)),
                "valid_ic_days": int(len(ic)),
                "avg_cross_section_n": float(group["cross_section_n"].mean()) if not group.empty else 0.0,
                "ic_mean": _series_mean(ic),
                "ic_std": ic_std,
                "icir": _safe_divide(_series_mean(ic), ic_std),
                "rank_ic_mean": _series_mean(rank_ic),
                "rank_ic_std": rank_std,
                "rank_icir": _safe_divide(_series_mean(rank_ic), rank_std),
                "positive_ic_ratio": _positive_ratio(ic),
                "positive_rank_ic_ratio": _positive_ratio(rank_ic),
            }
        )
    return pd.DataFrame(rows)


def calculate_group_timeseries(factor_panel: pd.DataFrame, *, group_count: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for factor_name, factor_group in factor_panel.groupby("factor_name", sort=True):
        for horizon in FORWARD_HORIZONS:
            target_col = f"forward_return_{horizon}d"
            for trade_date, day_group in factor_group.groupby("date", sort=True):
                valid = day_group[["symbol", "factor_value", target_col]].dropna().copy()
                if len(valid) < group_count:
                    continue
                valid["group"] = assign_quantile_groups(valid["factor_value"], group_count)
                valid = valid.dropna(subset=["group"])
                if valid.empty:
                    continue
                for group_id, group_rows in valid.groupby("group", sort=True):
                    rows.append(
                        {
                            "factor_name": str(factor_name),
                            "horizon": f"{horizon}d",
                            "date": str(trade_date),
                            "group": int(group_id),
                            "mean_forward_return": float(group_rows[target_col].mean()),
                            "symbol_count": int(len(group_rows)),
                        }
                    )
    return pd.DataFrame(rows)


def summarize_group_returns(group_timeseries: pd.DataFrame) -> pd.DataFrame:
    if group_timeseries.empty:
        return pd.DataFrame(columns=["factor_name", "horizon", "group", "mean_forward_return", "std_forward_return", "date_count", "avg_symbol_count"])
    rows: list[dict[str, Any]] = []
    for (factor_name, horizon, group_id), group in group_timeseries.groupby(["factor_name", "horizon", "group"], sort=True):
        returns = pd.to_numeric(group["mean_forward_return"], errors="coerce").dropna()
        rows.append(
            {
                "factor_name": factor_name,
                "horizon": horizon,
                "group": int(group_id),
                "mean_forward_return": _series_mean(returns),
                "std_forward_return": float(returns.std(ddof=1)) if len(returns) > 1 else 0.0,
                "date_count": int(group["date"].nunique()),
                "avg_symbol_count": float(group["symbol_count"].mean()) if not group.empty else 0.0,
            }
        )
    return pd.DataFrame(rows)


def summarize_top_bottom(group_timeseries: pd.DataFrame, *, group_count: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (factor_name, horizon), group in group_timeseries.groupby(["factor_name", "horizon"], sort=True):
        pivot = group.pivot_table(index="date", columns="group", values="mean_forward_return", aggfunc="mean")
        if 1 not in pivot.columns or group_count not in pivot.columns:
            continue
        spread = (pivot[group_count] - pivot[1]).dropna()
        group_means = pivot.mean(axis=0).sort_index()
        monotonic = bool(group_means.is_monotonic_increasing)
        monotonic_score = None
        if len(group_means) >= 2 and _has_variation(pd.Series(group_means.index, dtype="float64")) and _has_variation(group_means):
            monotonic_score = _spearman_corr(pd.Series(group_means.index, dtype="float64"), group_means.reset_index(drop=True))
        spread_std = float(spread.std(ddof=1)) if len(spread) > 1 else 0.0
        rows.append(
            {
                "factor_name": factor_name,
                "horizon": horizon,
                "date_count": int(len(spread)),
                "top_bottom_mean": _series_mean(spread),
                "top_bottom_std": spread_std,
                "top_bottom_ir": _safe_divide(_series_mean(spread), spread_std),
                "positive_spread_ratio": _positive_ratio(spread),
                "monotonic_increasing": monotonic,
                "monotonic_score": monotonic_score,
            }
        )
    return pd.DataFrame(rows)


def summarize_data_coverage(
    *,
    frames: dict[str, pd.DataFrame],
    close_df: pd.DataFrame,
    calendar: list[date],
    universe: list[str],
    factor_panel: pd.DataFrame,
    factor_windows: dict[str, int],
) -> pd.DataFrame:
    prices = frames["prices"].copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"], errors="coerce").dt.date
    prices["symbol"] = prices["symbol"].astype("string").str.strip()
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    expected_cells = int(len(calendar) * len(universe))
    matrix_missing = int(close_df.isna().sum().sum())
    rows = [
        {
            "scope": "source_prices",
            "item": "raw_rows",
            "expected_count": None,
            "actual_count": int(len(prices)),
            "missing_count": None,
            "missing_ratio": None,
            "note": "prices.parquet 原始行数",
        },
        {
            "scope": "source_prices",
            "item": "duplicate_trade_date_symbol",
            "expected_count": 0,
            "actual_count": int(prices.duplicated(["trade_date", "symbol"]).sum()),
            "missing_count": None,
            "missing_ratio": None,
            "note": "同一 trade_date + symbol 重复行数",
        },
        {
            "scope": "source_prices",
            "item": "close_null",
            "expected_count": 0,
            "actual_count": int(prices["close"].isna().sum()),
            "missing_count": int(prices["close"].isna().sum()),
            "missing_ratio": _safe_divide(float(prices["close"].isna().sum()), float(len(prices))),
            "note": "close 字段为空或无法转为数值的原始行",
        },
        {
            "scope": "source_prices",
            "item": "close_non_positive",
            "expected_count": 0,
            "actual_count": int((prices["close"] <= 0).sum()),
            "missing_count": None,
            "missing_ratio": None,
            "note": "close 非正值会污染收益率计算",
        },
        {
            "scope": "price_matrix",
            "item": "close_matrix_cells",
            "expected_count": expected_cells,
            "actual_count": int(close_df.notna().sum().sum()),
            "missing_count": matrix_missing,
            "missing_ratio": _safe_divide(float(matrix_missing), float(expected_cells)),
            "note": "交易日历与固定股票池重建后的 close 矩阵覆盖",
        },
        {
            "scope": "price_matrix",
            "item": "symbols_with_any_missing_close",
            "expected_count": 0,
            "actual_count": int((close_df.isna().sum(axis=0) > 0).sum()),
            "missing_count": None,
            "missing_ratio": _safe_divide(float((close_df.isna().sum(axis=0) > 0).sum()), float(len(universe))),
            "note": "至少一个交易日 close 缺失的股票数",
        },
        {
            "scope": "price_matrix",
            "item": "dates_with_any_missing_close",
            "expected_count": 0,
            "actual_count": int((close_df.isna().sum(axis=1) > 0).sum()),
            "missing_count": None,
            "missing_ratio": _safe_divide(float((close_df.isna().sum(axis=1) > 0).sum()), float(len(calendar))),
            "note": "至少一个股票 close 缺失的交易日数",
        },
    ]
    max_horizon = max(FORWARD_HORIZONS)
    for factor_name, window in sorted(factor_windows.items()):
        expected_factor_rows = max(len(calendar) - window - max_horizon, 0) * len(universe)
        actual_factor_rows = int((factor_panel["factor_name"] == factor_name).sum())
        rows.append(
            {
                "scope": "factor_panel",
                "item": factor_name,
                "expected_count": int(expected_factor_rows),
                "actual_count": actual_factor_rows,
                "missing_count": int(max(expected_factor_rows - actual_factor_rows, 0)),
                "missing_ratio": _safe_divide(float(max(expected_factor_rows - actual_factor_rows, 0)), float(expected_factor_rows)),
                "note": f"{factor_name} 同时具备因子值与 1/5/10/20 日未来收益标签的样本覆盖",
            }
        )
    return pd.DataFrame(rows)


def render_report(
    *,
    args: argparse.Namespace,
    close_df: pd.DataFrame,
    universe: list[str],
    calendar: list[date],
    factor_panel: pd.DataFrame,
    ic_summary: pd.DataFrame,
    group_returns: pd.DataFrame,
    top_bottom: pd.DataFrame,
    data_coverage: pd.DataFrame,
    paths: dict[str, Path],
) -> str:
    best_rank_ic = _best_row(ic_summary, "rank_ic_mean")
    best_spread = _best_row(top_bottom, "top_bottom_mean")
    missing_rows = data_coverage[pd.to_numeric(data_coverage["missing_count"], errors="coerce").fillna(0) > 0]
    data_missing_conclusion = "未发现会影响本实验输入矩阵的 close 缺失。" if missing_rows.empty else "存在数据缺失或覆盖不足，详见数据覆盖评估表。"
    lines = [
        "# 实验十六：动量因子有效性检验报告",
        "",
        "## 执行结论",
        "",
        f"- 输出报告：`{paths['report']}`",
        f"- 检验因子：{', '.join(args.factors)}",
        "- 预测目标：未来 1日、5日、10日、20日 close-to-close 收益。",
        f"- 样本区间：{close_df.index.min().isoformat()} 至 {close_df.index.max().isoformat()}；股票数：{len(universe)}；交易日数：{len(calendar)}。",
        f"- IC/Rank IC 最优组合：{_format_best(best_rank_ic, 'rank_ic_mean')}。",
        f"- Top-Bottom spread 最优组合：{_format_best(best_spread, 'top_bottom_mean')}。",
        f"- 数据缺失评估：{data_missing_conclusion}",
        "",
        "## 方法说明",
        "",
        "- 因子定义：`momentum_Nd = close[t] / close[t-N] - 1`，使用当前日收盘后可得数据形成横截面排序。",
        "- 标签定义：`forward_return_Hd = close[t+H] / close[t] - 1`；本实验只保留 1/5/10/20 日标签完整的样本。",
        "- IC 使用 Pearson 相关，Rank IC 使用 Spearman 相关；ICIR = IC 均值 / IC 标准差，未做年化。",
        f"- 分组收益按每日横截面因子值分为 {args.group_count} 组，1 组为最低因子组，{args.group_count} 组为最高因子组。",
        "- Top-Bottom spread = 最高因子组平均未来收益 - 最低因子组平均未来收益，可视为等权 long-short 因子组合的单期收益代理。",
        "- 股票池来自当前 `index_members.parquet` 固定快照，不是严格 PIT 成分池，存在幸存者偏差。",
        "",
        "## 指标解释与判断方式",
        "",
        markdown_table(
            [
                {"指标": "IC 均值", "解释": "因子值与未来收益相关性", "判断方式": "越稳定偏离 0 越好，正值表示高动量更可能对应高未来收益"},
                {"指标": "Rank IC", "解释": "因子排名与未来收益排名相关性", "判断方式": "更适合横截面选股，符号与大小优先于单日极值"},
                {"指标": "ICIR", "解释": "IC 均值 / IC 标准差", "判断方式": "衡量稳定性，绝对值越高越稳定"},
                {"指标": "分组单调性", "解释": "高因子组是否收益更高", "判断方式": "组均收益随组号上升越单调越可信"},
                {"指标": "Top-Bottom", "解释": "最高组减最低组收益", "判断方式": "判断 long-short alpha，正值表示高动量组相对占优"},
            ],
            ["指标", "解释", "判断方式"],
        ),
        "",
        "## IC / Rank IC / ICIR 汇总",
        "",
        markdown_table(_records(ic_summary), ["factor_name", "horizon", "valid_ic_days", "avg_cross_section_n", "ic_mean", "ic_std", "icir", "rank_ic_mean", "rank_ic_std", "rank_icir", "positive_rank_ic_ratio"]),
        "",
        "## 分组收益",
        "",
        markdown_table(_records(group_returns), ["factor_name", "horizon", "group", "mean_forward_return", "date_count", "avg_symbol_count"]),
        "",
        "## Top-Bottom Spread 与单调性",
        "",
        markdown_table(_records(top_bottom), ["factor_name", "horizon", "date_count", "top_bottom_mean", "top_bottom_std", "top_bottom_ir", "positive_spread_ratio", "monotonic_increasing", "monotonic_score"]),
        "",
        "## 数据缺失与覆盖评估",
        "",
        markdown_table(_records(data_coverage), ["scope", "item", "expected_count", "actual_count", "missing_count", "missing_ratio", "note"]),
        "",
        "## 产物清单",
        "",
        markdown_table(
            [
                {"artifact": "momentum_factor_panel", "path": str(paths["factor_panel"]), "description": "动量因子长表 parquet"},
                {"artifact": "ic_timeseries", "path": str(paths["ic_timeseries"]), "description": "每日 IC / Rank IC 明细"},
                {"artifact": "ic_summary", "path": str(paths["ic_summary"]), "description": "IC、Rank IC、ICIR 汇总"},
                {"artifact": "group_timeseries", "path": str(paths["group_timeseries"]), "description": "每日分组未来收益明细"},
                {"artifact": "group_returns", "path": str(paths["group_returns"]), "description": "分组平均未来收益汇总"},
                {"artifact": "top_bottom_spread", "path": str(paths["top_bottom"]), "description": "Top-Bottom spread 与单调性汇总"},
                {"artifact": "data_coverage", "path": str(paths["data_coverage"]), "description": "源数据、价格矩阵和因子样本覆盖评估"},
            ],
            ["artifact", "path", "description"],
        ),
        "",
        "## 结论",
        "",
        render_conclusion(ic_summary, top_bottom, data_coverage),
        "",
    ]
    return "\n".join(lines)


def render_conclusion(ic_summary: pd.DataFrame, top_bottom: pd.DataFrame, data_coverage: pd.DataFrame) -> str:
    if ic_summary.empty or top_bottom.empty:
        return "- 有效性指标为空，需先检查输入数据覆盖。"
    best_rank = _best_row(ic_summary, "rank_ic_mean")
    best_spread = _best_row(top_bottom, "top_bottom_mean")
    missing_count = pd.to_numeric(data_coverage["missing_count"], errors="coerce").fillna(0).sum()
    lines = [
        f"- Rank IC 最高的是 `{best_rank.get('factor_name')}` 对 `{best_rank.get('horizon')}`，Rank IC 均值为 {format_value(best_rank.get('rank_ic_mean'))}。",
        f"- Top-Bottom spread 最高的是 `{best_spread.get('factor_name')}` 对 `{best_spread.get('horizon')}`，均值为 {format_value(best_spread.get('top_bottom_mean'))}。",
    ]
    if float(missing_count) > 0:
        lines.append("- 当前数据存在缺失或因子窗口/未来标签导致的样本覆盖不足；报告中的 IC 和分组收益已基于有效样本计算。")
    else:
        lines.append("- 未发现 close 输入矩阵缺失，样本减少主要来自因子回看窗口和未来收益标签窗口。")
    return "\n".join(lines)


def assign_quantile_groups(values: pd.Series, group_count: int) -> pd.Series:
    if len(values) < group_count or not _has_variation(values):
        return pd.Series([pd.NA] * len(values), index=values.index, dtype="Int64")
    ranks = values.rank(method="first")
    groups = pd.qcut(ranks, q=group_count, labels=range(1, group_count + 1))
    return groups.astype("Int64")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.where(pd.notna(frame), None).to_dict(orient="records")


def _best_row(frame: pd.DataFrame, field: str) -> dict[str, Any]:
    if frame.empty or field not in frame.columns:
        return {}
    values = pd.to_numeric(frame[field], errors="coerce")
    if values.dropna().empty:
        return {}
    return frame.loc[values.idxmax()].to_dict()


def _format_best(row: dict[str, Any], field: str) -> str:
    if not row:
        return "无有效数据"
    return f"`{row.get('factor_name')}` / `{row.get('horizon')}`（{field}={format_value(row.get(field))}）"


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


def _positive_ratio(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return float((series > 0).mean())


def _safe_divide(left: float | None, right: float | None) -> float | None:
    if left is None or right in (None, 0):
        return None
    if not math.isfinite(float(right)):
        return None
    return float(left) / float(right)


if __name__ == "__main__":
    main()
