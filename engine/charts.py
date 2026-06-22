"""回测报告图表生成工具。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from engine.research_paths import research_report_path


class ChartGenerationError(Exception):
    """图表生成错误。"""


@dataclass(frozen=True, slots=True)
class ChartArtifact:
    title: str
    kind: str
    path: str
    source_path: str


def generate_report_charts(report_dir: str | Path = research_report_path()) -> list[ChartArtifact]:
    """从标准报告目录读取已存在结果，生成可嵌入 Markdown 的 PNG 图表。"""

    root = Path(report_dir)
    chart_dir = root / "charts"
    artifacts: list[ChartArtifact] = []

    equity_path = root / "equity_curve.csv"
    if equity_path.exists():
        artifacts.extend(generate_backtest_charts(equity_path, chart_dir))

    sweep_path = root / "momentum_param_sweep_local.csv"
    if sweep_path.exists():
        artifacts.extend(generate_sweep_charts(sweep_path, chart_dir))

    candidate_path = root / "momentum_candidates_local.csv"
    if candidate_path.exists():
        artifacts.extend(generate_candidate_charts(candidate_path, chart_dir))

    if not artifacts:
        raise ChartGenerationError(f"未找到可生成图表的标准报告文件: {root}")

    write_chart_index(artifacts, chart_dir / "index.md")
    return artifacts


def generate_backtest_charts(
    equity_curve: str | Path | pd.DataFrame | Sequence[dict[str, Any]],
    output_dir: str | Path,
    *,
    prefix: str = "",
) -> list[ChartArtifact]:
    """生成单次回测图表：净值、回撤、月度收益、换手与持仓。"""

    source_path, frame = _load_frame(equity_curve)
    df = _prepare_equity_frame(frame)
    out = _ensure_directory(output_dir)
    name = _name_builder(prefix)
    artifacts: list[ChartArtifact] = []

    artifacts.append(
        _save_line_chart(
            df,
            out / name("equity_curve.png"),
            title="Equity Curve",
            y_column="nav",
            y_label="NAV",
            kind="backtest_equity",
            source_path=source_path,
        )
    )
    artifacts.append(_save_drawdown_chart(df, out / name("drawdown.png"), source_path))

    monthly = _monthly_returns(df)
    if not monthly.empty:
        artifacts.append(_save_monthly_returns_chart(monthly, out / name("monthly_returns.png"), source_path))

    turnover_chart = _save_turnover_holdings_chart(df, out / name("turnover_holdings.png"), source_path)
    if turnover_chart is not None:
        artifacts.append(turnover_chart)

    return artifacts


def generate_sweep_charts(
    sweep_rows: str | Path | pd.DataFrame | Sequence[dict[str, Any]],
    output_dir: str | Path,
    *,
    metrics: Iterable[str] = ("sharpe", "cumulative_return"),
) -> list[ChartArtifact]:
    """为参数扫描结果生成 lookback x rebalance_freq 热力图。"""

    source_path, frame = _load_frame(sweep_rows)
    frame = _normalize_sweep_columns(frame)
    required = {"lookback", "rebalance_freq", "fraction", "status"}
    _require_columns(frame, required, "参数扫描图表")
    out = _ensure_directory(output_dir)
    status = frame["status"].fillna("").astype(str).str.strip().str.lower()
    work = frame[(status == "success") | (status == "")].copy()
    if work.empty:
        raise ChartGenerationError("参数扫描图表没有 status=success 的扫描行")
    for column in ("lookback", "rebalance_freq", "fraction", *tuple(metrics)):
        if column in work:
            work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["lookback", "rebalance_freq", "fraction"])
    if work.empty:
        raise ChartGenerationError("参数扫描图表没有有效参数组合: lookback, rebalance_freq, fraction")

    artifacts: list[ChartArtifact] = []
    for fraction in sorted(work["fraction"].dropna().unique()):
        subset = work[work["fraction"] == fraction]
        for metric in metrics:
            if metric not in subset:
                continue
            metric_frame = subset.dropna(subset=[metric])
            if metric_frame.empty:
                continue
            suffix = f"top{int(round(float(fraction) * 100))}"
            path = out / f"param_heatmap_{metric}_{suffix}.png"
            artifacts.append(_save_heatmap(metric_frame, metric, path, fraction, source_path))
    if not artifacts:
        requested = ", ".join(metrics)
        raise ChartGenerationError(f"参数扫描图表没有可绘制的指标字段或有效数值: {requested}")
    return artifacts


def generate_candidate_charts(
    candidates: str | Path | pd.DataFrame | Sequence[dict[str, Any]],
    output_dir: str | Path,
) -> list[ChartArtifact]:
    """生成候选参数对比图。"""

    source_path, frame = _load_frame(candidates)
    _require_columns(frame, {"candidate_id"}, "候选图表")
    out = _ensure_directory(output_dir)
    metric_map = {
        "local_sharpe": "Sharpe",
        "local_cumulative_return": "Return",
        "local_max_drawdown": "Max Drawdown",
        "local_turnover": "Turnover",
    }
    available = [column for column in metric_map if column in frame]
    if not available or frame.empty:
        return []

    work = frame.copy()
    for column in available:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    labels = work["candidate_id"].astype(str).tolist()
    fig, axes = plt.subplots(len(available), 1, figsize=(10, max(3, 2.2 * len(available))), squeeze=False)
    for ax, column in zip(axes.flatten(), available, strict=False):
        values = work[column]
        colors = ["#2E86AB" if value >= 0 else "#C0392B" for value in values.fillna(0)]
        ax.bar(labels, values, color=colors)
        ax.set_title(metric_map[column])
        ax.grid(True, axis="y", alpha=0.25)
        _annotate_bars(ax, values)
    fig.suptitle("Candidate Comparison")
    fig.tight_layout()
    path = out / "candidates_compare.png"
    _save_figure(fig, path)
    return [ChartArtifact("Candidate Comparison", "candidate_compare", str(path), source_path)]


def write_chart_index(artifacts: list[ChartArtifact], output_path: str | Path) -> str:
    """生成 Markdown 图表索引，便于在报告中查看全部 PNG 图表。"""

    target = Path(output_path)
    _ensure_parent_directory(target)
    lines = [
        "# 回测图表索引",
        "",
        "本文件由 `engine.charts.generate_report_charts` 生成，图片文件位于报告目录的 `charts/` 子目录。",
        "",
    ]
    for artifact in artifacts:
        rel = Path(artifact.path).relative_to(target.parent)
        lines.extend(
            [
                f"## {artifact.title}",
                "",
                f"- 类型：`{artifact.kind}`",
                f"- 数据源：`{artifact.source_path}`",
                "",
                f"![{artifact.title}]({rel.as_posix()})",
                "",
            ]
        )
    target.write_text("\n".join(lines), encoding="utf-8")
    return str(target)


def _prepare_equity_frame(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(frame, {"trade_date"}, "回测净值图表")
    df = frame.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df = df.dropna(subset=["trade_date"]).sort_values("trade_date")
    if df.empty:
        raise ChartGenerationError("回测净值图表没有有效 trade_date")
    if "nav" not in df:
        if "total_value" not in df:
            raise ChartGenerationError("回测净值图表需要 nav 或 total_value 字段")
        first_value = pd.to_numeric(df["total_value"], errors="coerce").dropna()
        if first_value.empty or first_value.iloc[0] == 0:
            raise ChartGenerationError("total_value 首值无效，无法计算 nav")
        df["nav"] = pd.to_numeric(df["total_value"], errors="coerce") / float(first_value.iloc[0])
    else:
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    if "drawdown" not in df:
        running_max = df["nav"].cummax()
        df["drawdown"] = df["nav"] / running_max - 1.0
    else:
        df["drawdown"] = pd.to_numeric(df["drawdown"], errors="coerce")
    if "turnover_amount" in df:
        df["turnover_amount"] = pd.to_numeric(df["turnover_amount"], errors="coerce")
    if "holding_count" in df:
        df["holding_count"] = pd.to_numeric(df["holding_count"], errors="coerce")
    return df


def _monthly_returns(df: pd.DataFrame) -> pd.Series:
    monthly_nav = df.set_index("trade_date")["nav"].resample("ME").last().dropna()
    return monthly_nav.pct_change().dropna()


def _save_line_chart(
    df: pd.DataFrame,
    path: Path,
    *,
    title: str,
    y_column: str,
    y_label: str,
    kind: str,
    source_path: str,
) -> ChartArtifact:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["trade_date"], df[y_column], color="#1F77B4", linewidth=1.6)
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(fig, path)
    return ChartArtifact(title, kind, str(path), source_path)


def _save_drawdown_chart(df: pd.DataFrame, path: Path, source_path: str) -> ChartArtifact:
    values = df["drawdown"] * 100
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.fill_between(df["trade_date"], values, 0, color="#C0392B", alpha=0.28)
    ax.plot(df["trade_date"], values, color="#922B21", linewidth=1.0)
    ax.set_title("Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown %")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(fig, path)
    return ChartArtifact("Drawdown", "backtest_drawdown", str(path), source_path)


def _save_monthly_returns_chart(monthly: pd.Series, path: Path, source_path: str) -> ChartArtifact:
    values = monthly * 100
    labels = [item.strftime("%Y-%m") for item in values.index]
    colors = ["#2E86AB" if value >= 0 else "#C0392B" for value in values]
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Monthly Returns")
    ax.set_xlabel("Month")
    ax.set_ylabel("Return %")
    ax.grid(True, axis="y", alpha=0.25)
    step = max(1, len(labels) // 12)
    ax.set_xticks(range(0, len(labels), step), labels[::step], rotation=45, ha="right")
    fig.tight_layout()
    _save_figure(fig, path)
    return ChartArtifact("Monthly Returns", "backtest_monthly_returns", str(path), source_path)


def _save_turnover_holdings_chart(df: pd.DataFrame, path: Path, source_path: str) -> ChartArtifact | None:
    has_turnover = "turnover_amount" in df and df["turnover_amount"].notna().any()
    has_holdings = "holding_count" in df and df["holding_count"].notna().any()
    if not has_turnover and not has_holdings:
        return None
    fig, ax = plt.subplots(figsize=(12, 4))
    if has_turnover:
        ax.plot(df["trade_date"], df["turnover_amount"], color="#7D3C98", linewidth=1.4, label="Turnover Amount")
        ax.set_ylabel("Turnover Amount")
    if has_holdings:
        target_ax = ax.twinx() if has_turnover else ax
        target_ax.plot(df["trade_date"], df["holding_count"], color="#117864", linewidth=1.2, label="Holding Count")
        target_ax.set_ylabel("Holding Count")
    ax.set_title("Turnover and Holdings")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    _save_figure(fig, path)
    return ChartArtifact("Turnover and Holdings", "backtest_turnover_holdings", str(path), source_path)


def _save_heatmap(df: pd.DataFrame, metric: str, path: Path, fraction: float, source_path: str) -> ChartArtifact:
    pivot = df.pivot_table(index="lookback", columns="rebalance_freq", values=metric, aggfunc="mean").sort_index()
    if pivot.empty:
        raise ChartGenerationError(f"参数扫描热力图无有效数据: {metric}")
    fig, ax = plt.subplots(figsize=(8, 6))
    values = pivot.to_numpy(dtype=float)
    im = ax.imshow(values, aspect="auto", cmap="RdYlGn")
    ax.set_title(f"{metric} Heatmap, top_fraction={fraction:.0%}")
    ax.set_xlabel("Rebalance Frequency")
    ax.set_ylabel("Lookback Days")
    ax.set_xticks(range(len(pivot.columns)), [str(int(item)) for item in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), [str(int(item)) for item in pivot.index])
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            value = values[i, j]
            if pd.notna(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, label=metric)
    fig.tight_layout()
    _save_figure(fig, path)
    return ChartArtifact(f"{metric} Heatmap top {fraction:.0%}", "sweep_heatmap", str(path), source_path)


def _annotate_bars(ax: plt.Axes, values: pd.Series) -> None:
    for index, value in enumerate(values):
        if pd.isna(value):
            continue
        va = "bottom" if value >= 0 else "top"
        ax.text(index, value, f"{value:.2f}", ha="center", va=va, fontsize=8)


def _save_figure(fig: plt.Figure, path: Path) -> None:
    _ensure_parent_directory(path)
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _load_frame(source: str | Path | pd.DataFrame | Sequence[dict[str, Any]]) -> tuple[str, pd.DataFrame]:
    if isinstance(source, pd.DataFrame):
        return "<dataframe>", source.copy()
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Path)):
        return "<records>", pd.DataFrame.from_records(source)
    path = Path(source)
    if not path.exists():
        raise ChartGenerationError(f"图表数据文件不存在: {path}")
    return str(path), pd.read_csv(path)


def _normalize_sweep_columns(frame: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "lookback_days": "lookback",
        "top_fraction": "fraction",
    }
    rename_map = {
        alias: canonical
        for alias, canonical in aliases.items()
        if alias in frame.columns and canonical not in frame.columns
    }
    return frame.rename(columns=rename_map)


def _require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns - set(frame.columns))
    if missing:
        raise ChartGenerationError(f"{label}缺少字段: {', '.join(missing)}")


def _ensure_directory(path: str | Path) -> Path:
    target = Path(path)
    if target.exists() and not target.is_dir():
        raise ChartGenerationError(f"图表输出路径被非目录占用: {target}")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _ensure_parent_directory(path: Path) -> None:
    parent = path.parent
    if parent.exists() and not parent.is_dir():
        raise ChartGenerationError(f"图表输出路径被非目录占用: {parent}")
    parent.mkdir(parents=True, exist_ok=True)


def _name_builder(prefix: str):
    clean = prefix.strip("_")

    def build(filename: str) -> str:
        return f"{clean}_{filename}" if clean else filename

    return build


__all__ = (
    "ChartArtifact",
    "ChartGenerationError",
    "generate_backtest_charts",
    "generate_candidate_charts",
    "generate_report_charts",
    "generate_sweep_charts",
    "write_chart_index",
)
