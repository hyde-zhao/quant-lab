"""Factor model pricing and comparison research tools.

本模块只消费本地第三章因子面板和 forward-return 标签，不读取凭据、
不触发 provider fetch、不写 data lake、不 publish catalog、不触发 QMT /
simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS, get_equity_factor_definition
from engine.factor_research_matrices import panel_to_matrix
from engine.factor_statistics import fama_macbeth_regression, newey_west_t_stat
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import safe_float


CHAPTER4_SCHEMA = "chapter4_factor_models_v1"
FACTOR_MODEL_RETURN_SCHEMA = "chapter4_factor_model_returns_v1"
MODEL_COMPARISON_SCHEMA = "chapter4_model_comparison_v1"

FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class FactorModelDefinition:
    model_id: str
    name: str
    factor_ids: tuple[str, ...]
    source_ref: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter4AnalysisResult:
    run_id: str
    status: str
    sample_id: str
    factor_ids: tuple[str, ...]
    model_ids: tuple[str, ...]
    panel_rows: int
    label_rows: int
    matched_rows: int
    rebalance_count: int
    fama_macbeth_results: pd.DataFrame
    factor_model_returns: pd.DataFrame
    model_comparison: pd.DataFrame
    factor_correlation: pd.DataFrame
    model_correlation: pd.DataFrame
    model_admission_summary: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, str], ...]
    limitations: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER4_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_id": self.sample_id,
            "factor_ids": list(self.factor_ids),
            "model_ids": list(self.model_ids),
            "panel_rows": self.panel_rows,
            "label_rows": self.label_rows,
            "matched_rows": self.matched_rows,
            "rebalance_count": self.rebalance_count,
            "fama_macbeth_rows": int(len(self.fama_macbeth_results)),
            "factor_model_return_rows": int(len(self.factor_model_returns)),
            "model_comparison_rows": int(len(self.model_comparison)),
            "model_admission_summary": list(self.model_admission_summary),
            "blocked_claims": list(self.blocked_claims),
            "limitations": list(self.limitations),
            "operation_counts": dict(self.operation_counts),
        }


DEFAULT_CHAPTER4_MODELS: tuple[FactorModelDefinition, ...] = (
    FactorModelDefinition(
        model_id="capm_market",
        name="CAPM 市场模型",
        factor_ids=("market_beta_252",),
        source_ref="book:factor_investing:chapter4:mainstream_models",
        description="以市场 beta 作为单因子定价基准。",
    ),
    FactorModelDefinition(
        model_id="ff3_equity_core",
        name="三因子模型",
        factor_ids=("market_beta_252", "size_total_market_cap", "value_bm"),
        source_ref="book:factor_investing:chapter4:mainstream_models",
        description="市场、规模、价值三类主流定价因子。",
    ),
    FactorModelDefinition(
        model_id="carhart4_momentum",
        name="四因子动量扩展模型",
        factor_ids=("market_beta_252", "size_total_market_cap", "value_bm", "momentum_12_1"),
        source_ref="book:factor_investing:chapter4:mainstream_models",
        description="在三因子模型上加入动量因子。",
    ),
    FactorModelDefinition(
        model_id="ff5_like_profit_investment",
        name="五因子盈利投资模型",
        factor_ids=(
            "market_beta_252",
            "size_total_market_cap",
            "value_bm",
            "profitability_roe_ttm",
            "investment_asset_growth",
        ),
        source_ref="book:factor_investing:chapter4:model_comparison",
        description="市场、规模、价值、盈利、投资五类因子的项目内可执行版本。",
    ),
    FactorModelDefinition(
        model_id="q_factor_like",
        name="q-factor 类模型",
        factor_ids=(
            "market_beta_252",
            "size_total_market_cap",
            "profitability_roe_ttm",
            "investment_asset_growth",
        ),
        source_ref="book:factor_investing:chapter4:model_comparison",
        description="市场、规模、盈利和投资组合成的轻量 q-factor 类对照模型。",
    ),
    FactorModelDefinition(
        model_id="ashare_pricing_candidate",
        name="A 股候选定价模型",
        factor_ids=(
            "size_total_market_cap",
            "value_bm",
            "momentum_12_1",
            "profitability_roe_ttm",
            "investment_asset_growth",
            "abnormal_turnover_21_252",
        ),
        source_ref="book:factor_investing:chapter4:a_share_pricing",
        description="不含市场 beta 的 A 股截面候选因子集合，用于观察哪些风格被定价。",
    ),
    FactorModelDefinition(
        model_id="seven_factor_full",
        name="七因子全模型",
        factor_ids=DEFAULT_EQUITY_CORE_FACTOR_IDS,
        source_ref="book:factor_investing:chapter4:parsimony",
        description="第三章七因子的完整截面定价模型，用于简约性对照。",
    ),
)


def run_chapter4_analysis(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    run_id: str,
    sample_id: str,
    models: Sequence[FactorModelDefinition] = DEFAULT_CHAPTER4_MODELS,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
    min_cross_section: int = 30,
    quantiles: int = 5,
    newey_west_lags: int | None = None,
) -> Chapter4AnalysisResult:
    validate_chapter4_inputs(panel, labels, factor_ids=factor_ids)
    factors = panel_to_factor_matrices(panel, factor_ids=factor_ids)
    forward_returns = labels_to_forward_return_matrix(labels)
    matched_index = _matched_index_rows(factors, forward_returns)
    factor_model_returns = build_factor_model_returns(
        forward_returns,
        factors,
        models=models,
        min_cross_section=min_cross_section,
        quantiles=quantiles,
    )
    fama_macbeth_results = build_fama_macbeth_results(
        forward_returns,
        factors,
        models=models,
        min_cross_section=min_cross_section,
        newey_west_lags=newey_west_lags,
    )
    model_comparison = build_model_comparison(
        factor_model_returns,
        baseline_model_id="capm_market",
        newey_west_lags=newey_west_lags,
    )
    factor_corr = factor_correlation(factors)
    model_corr = model_return_correlation(factor_model_returns)
    summary = build_model_admission_summary(model_comparison)
    status = "PASS" if not model_comparison.empty and not fama_macbeth_results.empty else "BLOCKED"
    return Chapter4AnalysisResult(
        run_id=run_id,
        status=status,
        sample_id=sample_id,
        factor_ids=tuple(factor_ids),
        model_ids=tuple(model.model_id for model in models),
        panel_rows=int(len(panel)),
        label_rows=int(len(labels)),
        matched_rows=matched_index,
        rebalance_count=int(forward_returns.index.nunique()),
        fama_macbeth_results=fama_macbeth_results,
        factor_model_returns=factor_model_returns,
        model_comparison=model_comparison,
        factor_correlation=factor_corr,
        model_correlation=model_corr,
        model_admission_summary=tuple(summary),
        blocked_claims=default_blocked_claims(run_id),
        limitations=(),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_chapter4_inputs(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    *,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
) -> None:
    required_panel = {"trade_date", "symbol", "factor_id", "zscore_value", "available_at", "run_id", "data_lineage"}
    required_labels = {"trade_date", "symbol", "forward_return", "label_available_at"}
    missing_panel = required_panel - set(panel.columns)
    missing_labels = required_labels - set(labels.columns)
    if missing_panel:
        raise ValueError("factor panel 缺少字段: " + ", ".join(sorted(missing_panel)))
    if missing_labels:
        raise ValueError("labels 缺少字段: " + ", ".join(sorted(missing_labels)))
    present = set(panel["factor_id"].dropna().astype(str).unique())
    missing_factors = set(factor_ids) - present
    if missing_factors:
        raise ValueError("factor panel 缺少因子: " + ", ".join(sorted(missing_factors)))
    if panel.empty or labels.empty:
        raise ValueError("factor panel 和 labels 不能为空")
    merged = panel[["trade_date", "symbol", "available_at"]].merge(
        labels[["trade_date", "symbol", "label_available_at"]],
        on=["trade_date", "symbol"],
        how="inner",
    )
    if merged.empty:
        raise ValueError("factor panel 与 labels 没有可匹配样本")
    available_at = pd.to_datetime(merged["available_at"], errors="coerce", utc=True)
    label_available_at = pd.to_datetime(merged["label_available_at"], errors="coerce", utc=True)
    invalid = available_at.notna() & label_available_at.notna() & (label_available_at <= available_at)
    if bool(invalid.any()):
        raise ValueError("label_available_at 必须晚于因子 available_at，检测到潜在前视")


def panel_to_factor_matrices(
    panel: pd.DataFrame,
    *,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
    value_column: str = "zscore_value",
) -> dict[str, pd.DataFrame]:
    matrices: dict[str, pd.DataFrame] = {}
    work = panel.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    for factor_id in factor_ids:
        part = work[work["factor_id"] == factor_id]
        matrix = panel_to_matrix(part, value_column=value_column).apply(pd.to_numeric, errors="coerce")
        matrices[factor_id] = matrix
    return matrices


def labels_to_forward_return_matrix(labels: pd.DataFrame) -> pd.DataFrame:
    work = labels.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    matrix = panel_to_matrix(work, value_column="forward_return")
    return matrix.sort_index().apply(pd.to_numeric, errors="coerce")


def build_fama_macbeth_results(
    forward_returns: pd.DataFrame,
    factors: Mapping[str, pd.DataFrame],
    *,
    models: Sequence[FactorModelDefinition] = DEFAULT_CHAPTER4_MODELS,
    min_cross_section: int = 30,
    newey_west_lags: int | None = None,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for model in models:
        model_factors = {factor_id: factors[factor_id] for factor_id in model.factor_ids if factor_id in factors}
        if set(model.factor_ids) - set(model_factors):
            continue
        summary = fama_macbeth_regression(
            forward_returns,
            model_factors,
            min_cross_section=min_cross_section,
            newey_west_lags=newey_west_lags,
        )
        if summary.empty:
            continue
        summary = summary.copy()
        summary.insert(0, "model_id", model.model_id)
        summary.insert(1, "model_name", model.name)
        summary["factor_name"] = summary["coefficient"].map(_factor_name)
        summary["source_ref"] = model.source_ref
        rows.append(summary)
    if not rows:
        return pd.DataFrame(
            columns=[
                "model_id",
                "model_name",
                "coefficient",
                "factor_name",
                "mean_estimate",
                "t_stat",
                "observation_count",
                "newey_west_lags",
                "source_ref",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def build_factor_model_returns(
    forward_returns: pd.DataFrame,
    factors: Mapping[str, pd.DataFrame],
    *,
    models: Sequence[FactorModelDefinition] = DEFAULT_CHAPTER4_MODELS,
    min_cross_section: int = 30,
    quantiles: int = 5,
) -> pd.DataFrame:
    if quantiles < 2:
        raise ValueError("quantiles 必须至少为 2")
    rows: list[dict[str, Any]] = []
    for model in models:
        common_dates = forward_returns.index
        for factor_id in model.factor_ids:
            common_dates = common_dates.intersection(factors[factor_id].index)
        for trade_date in common_dates:
            frame = pd.DataFrame({"forward_return": forward_returns.loc[trade_date]})
            for factor_id in model.factor_ids:
                frame[factor_id] = factors[factor_id].loc[trade_date]
            frame = frame.dropna()
            if len(frame) < max(min_cross_section, quantiles * 2):
                continue
            frame["model_score"] = frame[list(model.factor_ids)].mean(axis=1)
            groups = _quantile_groups(frame["model_score"], quantiles)
            frame = frame.assign(group=groups).dropna(subset=["group"])
            low = frame[frame["group"] == 1]
            high = frame[frame["group"] == quantiles]
            if low.empty or high.empty:
                continue
            rows.append(
                {
                    "schema_version": FACTOR_MODEL_RETURN_SCHEMA,
                    "trade_date": str(trade_date),
                    "model_id": model.model_id,
                    "model_name": model.name,
                    "model_return": float(high["forward_return"].mean() - low["forward_return"].mean()),
                    "long_mean_return": float(high["forward_return"].mean()),
                    "short_mean_return": float(low["forward_return"].mean()),
                    "symbol_count": int(len(frame)),
                    "long_count": int(len(high)),
                    "short_count": int(len(low)),
                    "quantiles": int(quantiles),
                    "factor_ids": ",".join(model.factor_ids),
                }
            )
    return pd.DataFrame(rows)


def build_model_comparison(
    model_returns: pd.DataFrame,
    *,
    baseline_model_id: str = "capm_market",
    newey_west_lags: int | None = None,
) -> pd.DataFrame:
    if model_returns.empty:
        return pd.DataFrame()
    pivot = model_returns.pivot_table(index="trade_date", columns="model_id", values="model_return", aggfunc="last").sort_index()
    baseline = pivot[baseline_model_id].dropna() if baseline_model_id in pivot.columns else pd.Series(dtype="float64")
    rows: list[dict[str, Any]] = []
    for model_id in pivot.columns:
        series = pivot[model_id].dropna()
        alpha, alpha_t, beta = _alpha_vs_baseline(series, baseline)
        corr = _safe_corr(series, baseline)
        rows.append(
            {
                "schema_version": MODEL_COMPARISON_SCHEMA,
                "model_id": model_id,
                "mean_return": _safe_float(series.mean()),
                "t_stat": newey_west_t_stat(series, lags=newey_west_lags),
                "observation_count": int(len(series)),
                "positive_period_ratio": _safe_float((series > 0).mean()) if len(series) else None,
                "correlation_to_baseline": corr,
                "alpha_vs_baseline": alpha,
                "alpha_t_stat": alpha_t,
                "beta_to_baseline": beta,
                "admission": model_admission(series, corr),
            }
        )
    return pd.DataFrame(rows)


def factor_correlation(factors: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.Series] = []
    for factor_id, matrix in factors.items():
        series = matrix.stack(future_stack=True).dropna().rename(factor_id)
        frames.append(series)
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1)
    wide = _drop_constant_columns(wide)
    return wide.corr(min_periods=30)


def model_return_correlation(model_returns: pd.DataFrame) -> pd.DataFrame:
    if model_returns.empty:
        return pd.DataFrame()
    pivot = model_returns.pivot_table(index="trade_date", columns="model_id", values="model_return", aggfunc="last")
    pivot = _drop_constant_columns(pivot)
    return pivot.corr(min_periods=6)


def build_model_admission_summary(model_comparison: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in model_comparison.to_dict("records"):
        admission = str(item.get("admission") or "watch")
        rows.append(
            {
                "model_id": str(item.get("model_id") or ""),
                "admission": admission,
                "reason": _admission_reason(item),
                "handoff": "CR-037 robustness review required before CR-038/CR-039 strategy admission",
            }
        )
    return rows


def model_admission(series: pd.Series, corr_to_baseline: float | None) -> str:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) < 12:
        return "watch_insufficient_observations"
    t_stat = newey_west_t_stat(clean)
    mean_return = clean.mean()
    if mean_return <= 0 or (t_stat is not None and t_stat < 0):
        return "reject_or_reweight"
    if t_stat is not None and t_stat >= 2.0 and (corr_to_baseline is None or abs(corr_to_baseline) < 0.95):
        return "baseline_candidate"
    return "needs_robustness_review"


def default_blocked_claims(run_id: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "claim": "production_valid",
            "status": "blocked",
            "reason": "CR-035 仅生成离线研究证据，不构成生产有效声明。",
            "evidence_ref": run_id,
        },
        {
            "claim": "qmt_ready",
            "status": "blocked",
            "reason": "CR-035 不授权 QMT、账户、订单或 broker runtime。",
            "evidence_ref": run_id,
        },
        {
            "claim": "simulation_ready",
            "status": "blocked",
            "reason": "CR-035 不授权 simulation 或 live。",
            "evidence_ref": run_id,
        },
        {
            "claim": "live_ready",
            "status": "blocked",
            "reason": "CR-035 不授权 simulation 或 live。",
            "evidence_ref": run_id,
        },
    )


def _matched_index_rows(factors: Mapping[str, pd.DataFrame], forward_returns: pd.DataFrame) -> int:
    if not factors:
        return 0
    stacked = [matrix.stack(future_stack=True).dropna().rename(factor_id) for factor_id, matrix in factors.items()]
    factor_frame = pd.concat(stacked, axis=1).dropna(how="all")
    labels = forward_returns.stack(future_stack=True).dropna().rename("forward_return")
    return int(factor_frame.join(labels, how="inner").dropna(subset=["forward_return"]).shape[0])


def _alpha_vs_baseline(series: pd.Series, baseline: pd.Series) -> tuple[float | None, float | None, float | None]:
    aligned = pd.concat([series.rename("model"), baseline.rename("baseline")], axis=1).dropna()
    if len(aligned) < 3:
        return None, None, None
    y = aligned["model"].to_numpy(dtype="float64")
    x = aligned["baseline"].to_numpy(dtype="float64")
    design = np.column_stack([np.ones(len(aligned)), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    alpha = float(beta[0])
    slope = float(beta[1])
    alpha_series = aligned["model"] - slope * aligned["baseline"]
    return alpha, newey_west_t_stat(alpha_series), slope


def _safe_corr(left: pd.Series, right: pd.Series) -> float | None:
    aligned = pd.concat([left.rename("left"), right.rename("right")], axis=1).dropna()
    if len(aligned) < 3:
        return None
    if aligned["left"].std(ddof=0) == 0 or aligned["right"].std(ddof=0) == 0:
        return None
    value = aligned["left"].corr(aligned["right"])
    return _safe_float(value)


def _quantile_groups(values: pd.Series, groups: int) -> pd.Series:
    ranks = values.rank(method="first")
    if ranks.notna().sum() < groups:
        return pd.Series(index=values.index, dtype="float64")
    try:
        labels = pd.qcut(ranks, groups, labels=False, duplicates="drop")
    except ValueError:
        return pd.Series(index=values.index, dtype="float64")
    return pd.Series(labels, index=values.index, dtype="float64") + 1


def _factor_name(coefficient: str) -> str:
    if coefficient == "intercept":
        return "截距"
    try:
        return get_equity_factor_definition(coefficient).name
    except KeyError:
        return coefficient


def _admission_reason(item: Mapping[str, Any]) -> str:
    admission = str(item.get("admission") or "")
    if admission == "baseline_candidate":
        return "样本内模型收益为正且 t 值达到 baseline 候选阈值；仍需 CR-037 稳健性复验。"
    if admission == "reject_or_reweight":
        return "模型收益或显著性方向不满足进入 baseline 的下限，后续只能作为观察或重加权对象。"
    if admission == "watch_insufficient_observations":
        return "有效期数不足，不能形成准入结论。"
    return "模型收益为正但显著性、冗余性或稳定性仍需第6章稳健性复验。"


def _safe_float(value: Any) -> float | None:
    return safe_float(value)


def _drop_constant_columns(frame: pd.DataFrame) -> pd.DataFrame:
    keep: list[str] = []
    for column in frame.columns:
        series = pd.to_numeric(frame[column], errors="coerce").dropna()
        if len(series) >= 2 and float(series.std(ddof=0)) > 0:
            keep.append(column)
    return frame[keep] if keep else pd.DataFrame(index=frame.index)
