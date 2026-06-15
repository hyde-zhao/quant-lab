"""CR-036 第五章异象复刻与 alpha 检验工具。

本模块只消费本地第三章因子面板、forward-return 标签和 CR-035 模型收益，
不读取凭据、不触发 provider fetch、不写 data lake、不 publish catalog、
不触发 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.chapter4_factor_models import labels_to_forward_return_matrix, panel_to_factor_matrices
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS
from engine.factor_statistics import newey_west_t_stat
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


CHAPTER5_SCHEMA = "chapter5_anomalies_v1"
ANOMALY_PANEL_SCHEMA = "chapter5_anomaly_panel_v1"
ANOMALY_RETURNS_SCHEMA = "chapter5_anomaly_returns_v1"
ALPHA_TEST_SCHEMA = "chapter5_alpha_tests_v1"

FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class AnomalyDefinition:
    anomaly_id: str
    name: str
    chapter_ref: str
    source_ref: str
    required_factor_ids: tuple[str, ...]
    direction: str
    formula: str
    strict_gap: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter5AnalysisResult:
    run_id: str
    status: str
    sample_id: str
    anomaly_ids: tuple[str, ...]
    panel_rows: int
    label_rows: int
    anomaly_panel_rows: int
    anomaly_return_rows: int
    alpha_test_rows: int
    rebalance_count: int
    anomaly_panel: pd.DataFrame
    anomaly_returns: pd.DataFrame
    alpha_tests: pd.DataFrame
    anomaly_correlation: pd.DataFrame
    anomaly_admission_summary: tuple[dict[str, Any], ...]
    gap_register: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, str], ...]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER5_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_id": self.sample_id,
            "anomaly_ids": list(self.anomaly_ids),
            "panel_rows": self.panel_rows,
            "label_rows": self.label_rows,
            "anomaly_panel_rows": self.anomaly_panel_rows,
            "anomaly_return_rows": self.anomaly_return_rows,
            "alpha_test_rows": self.alpha_test_rows,
            "rebalance_count": self.rebalance_count,
            "anomaly_admission_summary": list(self.anomaly_admission_summary),
            "gap_register": list(self.gap_register),
            "blocked_claims": list(self.blocked_claims),
            "operation_counts": dict(self.operation_counts),
        }


DEFAULT_CHAPTER5_ANOMALIES: tuple[AnomalyDefinition, ...] = (
    AnomalyDefinition(
        anomaly_id="valuation_extreme_spread",
        name="估值高低极端异象",
        chapter_ref="5.1",
        source_ref="book:factor_investing:chapter5:5.1",
        required_factor_ids=("value_bm",),
        direction="positive",
        formula="abs(zscore(value_bm))；衡量估值高低极端程度，不等同于第三章价值因子本身。",
        strict_gap="缺少第5章原文与更细分估值变量时，当前只做项目内可执行极端估值代理。",
    ),
    AnomalyDefinition(
        anomaly_id="fundamental_anchor_reversal",
        name="基本面锚定反转异象",
        chapter_ref="5.2",
        source_ref="book:factor_investing:chapter5:5.2",
        required_factor_ids=("value_bm", "profitability_roe_ttm", "investment_asset_growth", "momentum_12_1"),
        direction="positive",
        formula="mean(value_bm, profitability_roe_ttm, investment_asset_growth) - momentum_12_1；高基本面锚定且低近期动量为高分。",
        strict_gap="缺少书中更精确的基本面锚定字段时，当前使用第三章已审计基本面因子形成代理。",
    ),
    AnomalyDefinition(
        anomaly_id="idiosyncratic_volatility_proxy",
        name="特质性波动率异象代理",
        chapter_ref="5.3",
        source_ref="book:factor_investing:chapter5:5.3",
        required_factor_ids=DEFAULT_EQUITY_CORE_FACTOR_IDS,
        direction="negative",
        formula="rolling_std(residual(next_rebalance_return ~ seven_factor_full), 12 rebalance periods, min_obs=6)；低特质波动率为高分。",
        strict_gap="缺少日收益残差和书中精确定价模型残差时，当前输出月度残差波动率代理，并保留 strict gap。",
    ),
)


def run_chapter5_analysis(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    model_returns: pd.DataFrame,
    *,
    run_id: str,
    sample_id: str,
    anomalies: Sequence[AnomalyDefinition] = DEFAULT_CHAPTER5_ANOMALIES,
    min_cross_section: int = 30,
    quantiles: int = 5,
    residual_window: int = 12,
    residual_min_periods: int = 6,
    alpha_model_ids: Sequence[str] = ("seven_factor_full", "ashare_pricing_candidate", "ff3_equity_core"),
) -> Chapter5AnalysisResult:
    validate_chapter5_inputs(panel, labels, model_returns, anomalies=anomalies)
    factors = panel_to_factor_matrices(panel, factor_ids=DEFAULT_EQUITY_CORE_FACTOR_IDS)
    forward_returns = labels_to_forward_return_matrix(labels)
    anomaly_matrices = build_anomaly_matrices(
        factors,
        forward_returns,
        anomalies=anomalies,
        min_cross_section=min_cross_section,
        residual_window=residual_window,
        residual_min_periods=residual_min_periods,
    )
    anomaly_panel = anomaly_matrices_to_panel(anomaly_matrices, anomalies=anomalies, run_id=run_id)
    anomaly_returns = build_anomaly_returns(
        anomaly_matrices,
        forward_returns,
        anomalies=anomalies,
        min_cross_section=min_cross_section,
        quantiles=quantiles,
    )
    alpha_tests = build_alpha_tests(anomaly_returns, model_returns, model_ids=alpha_model_ids)
    correlation = anomaly_correlation(anomaly_matrices)
    summary = build_anomaly_admission_summary(anomaly_returns, alpha_tests)
    gaps = build_gap_register(anomalies)
    status = "PASS" if not anomaly_panel.empty and not anomaly_returns.empty and not alpha_tests.empty else "BLOCKED"
    return Chapter5AnalysisResult(
        run_id=run_id,
        status=status,
        sample_id=sample_id,
        anomaly_ids=tuple(item.anomaly_id for item in anomalies),
        panel_rows=int(len(panel)),
        label_rows=int(len(labels)),
        anomaly_panel_rows=int(len(anomaly_panel)),
        anomaly_return_rows=int(len(anomaly_returns)),
        alpha_test_rows=int(len(alpha_tests)),
        rebalance_count=int(forward_returns.index.nunique()),
        anomaly_panel=anomaly_panel,
        anomaly_returns=anomaly_returns,
        alpha_tests=alpha_tests,
        anomaly_correlation=correlation,
        anomaly_admission_summary=tuple(summary),
        gap_register=tuple(gaps),
        blocked_claims=default_blocked_claims(run_id),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_chapter5_inputs(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    model_returns: pd.DataFrame,
    *,
    anomalies: Sequence[AnomalyDefinition] = DEFAULT_CHAPTER5_ANOMALIES,
) -> None:
    required_panel = {"trade_date", "symbol", "factor_id", "zscore_value", "available_at", "run_id", "data_lineage"}
    required_labels = {"trade_date", "symbol", "forward_return", "label_available_at"}
    required_model_returns = {"trade_date", "model_id", "model_return"}
    missing_panel = required_panel - set(panel.columns)
    missing_labels = required_labels - set(labels.columns)
    missing_model = required_model_returns - set(model_returns.columns)
    if missing_panel:
        raise ValueError("factor panel 缺少字段: " + ", ".join(sorted(missing_panel)))
    if missing_labels:
        raise ValueError("labels 缺少字段: " + ", ".join(sorted(missing_labels)))
    if missing_model:
        raise ValueError("model_returns 缺少字段: " + ", ".join(sorted(missing_model)))
    if panel.empty or labels.empty or model_returns.empty:
        raise ValueError("panel、labels 和 model_returns 不能为空")
    present = set(panel["factor_id"].dropna().astype(str).unique())
    required_factors = {factor_id for item in anomalies for factor_id in item.required_factor_ids}
    missing_factors = required_factors - present
    if missing_factors:
        raise ValueError("factor panel 缺少异象必需因子: " + ", ".join(sorted(missing_factors)))
    merged = panel[["trade_date", "symbol", "available_at"]].merge(
        labels[["trade_date", "symbol", "label_available_at"]],
        on=["trade_date", "symbol"],
        how="inner",
    )
    if merged.empty:
        raise ValueError("factor panel 与 labels 没有可匹配样本")
    available_at = pd.to_datetime(merged["available_at"], errors="coerce", utc=True)
    label_available_at = pd.to_datetime(merged["label_available_at"], errors="coerce", utc=True)
    if bool((available_at.notna() & label_available_at.notna() & (label_available_at <= available_at)).any()):
        raise ValueError("label_available_at 必须晚于因子 available_at，检测到潜在前视")


def build_anomaly_matrices(
    factors: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    *,
    anomalies: Sequence[AnomalyDefinition] = DEFAULT_CHAPTER5_ANOMALIES,
    min_cross_section: int = 30,
    residual_window: int = 12,
    residual_min_periods: int = 6,
) -> dict[str, pd.DataFrame]:
    matrices: dict[str, pd.DataFrame] = {}
    for anomaly in anomalies:
        if anomaly.anomaly_id == "valuation_extreme_spread":
            matrices[anomaly.anomaly_id] = factors["value_bm"].abs()
        elif anomaly.anomaly_id == "fundamental_anchor_reversal":
            anchor = pd.concat(
                [
                    factors["value_bm"].stack(future_stack=True).rename("value_bm"),
                    factors["profitability_roe_ttm"].stack(future_stack=True).rename("profitability_roe_ttm"),
                    factors["investment_asset_growth"].stack(future_stack=True).rename("investment_asset_growth"),
                    factors["momentum_12_1"].stack(future_stack=True).rename("momentum_12_1"),
                ],
                axis=1,
            )
            raw = anchor[["value_bm", "profitability_roe_ttm", "investment_asset_growth"]].mean(axis=1) - anchor["momentum_12_1"]
            matrices[anomaly.anomaly_id] = raw.unstack().reindex(index=forward_returns.index)
        elif anomaly.anomaly_id == "idiosyncratic_volatility_proxy":
            residuals = cross_sectional_residuals(
                forward_returns,
                {factor_id: factors[factor_id] for factor_id in DEFAULT_EQUITY_CORE_FACTOR_IDS},
                min_cross_section=min_cross_section,
            )
            raw_vol = residuals.rolling(residual_window, min_periods=residual_min_periods).std()
            matrices[anomaly.anomaly_id] = -raw_vol
        else:
            raise ValueError(f"未知异象: {anomaly.anomaly_id}")
    return {key: cross_sectional_zscore(cross_sectional_winsorize(value)) for key, value in matrices.items()}


def cross_sectional_residuals(
    forward_returns: pd.DataFrame,
    factors: Mapping[str, pd.DataFrame],
    *,
    min_cross_section: int,
) -> pd.DataFrame:
    rows: list[pd.Series] = []
    factor_ids = tuple(factors.keys())
    common_dates = forward_returns.index
    for matrix in factors.values():
        common_dates = common_dates.intersection(matrix.index)
    for trade_date in common_dates:
        frame = pd.DataFrame({"forward_return": forward_returns.loc[trade_date]})
        for factor_id in factor_ids:
            frame[factor_id] = factors[factor_id].loc[trade_date]
        frame = frame.dropna()
        parameter_count = len(factor_ids) + 1
        if len(frame) < max(min_cross_section, parameter_count + 1):
            continue
        y = frame["forward_return"].to_numpy(dtype="float64")
        x = np.column_stack([np.ones(len(frame)), *[frame[factor_id].to_numpy(dtype="float64") for factor_id in factor_ids]])
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        fitted = x @ beta
        residual = pd.Series(y - fitted, index=frame.index, name=trade_date)
        rows.append(residual)
    if not rows:
        return pd.DataFrame(index=forward_returns.index, columns=forward_returns.columns, dtype="float64")
    return pd.DataFrame(rows).reindex(index=forward_returns.index, columns=forward_returns.columns)


def anomaly_matrices_to_panel(
    matrices: Mapping[str, pd.DataFrame],
    *,
    anomalies: Sequence[AnomalyDefinition],
    run_id: str,
) -> pd.DataFrame:
    definitions = {item.anomaly_id: item for item in anomalies}
    rows: list[pd.DataFrame] = []
    for anomaly_id, matrix in matrices.items():
        stacked = matrix.stack(future_stack=True).dropna().rename("zscore_value").reset_index()
        if stacked.empty:
            continue
        stacked.columns = ["trade_date", "symbol", "zscore_value"]
        definition = definitions[anomaly_id]
        stacked["schema_version"] = ANOMALY_PANEL_SCHEMA
        stacked["anomaly_id"] = anomaly_id
        stacked["anomaly_name"] = definition.name
        stacked["chapter_ref"] = definition.chapter_ref
        stacked["source_ref"] = definition.source_ref
        stacked["direction"] = definition.direction
        stacked["raw_value"] = stacked["zscore_value"]
        stacked["directional_value"] = stacked["zscore_value"]
        stacked["winsorized_value"] = stacked["zscore_value"]
        stacked["available_at"] = stacked["trade_date"].map(lambda day: f"{day}T16:30:00+08:00")
        stacked["run_id"] = run_id
        stacked["data_lineage"] = "cr034_chapter3_panel_plus_cr035_model_returns"
        rows.append(stacked)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_anomaly_returns(
    matrices: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    *,
    anomalies: Sequence[AnomalyDefinition],
    min_cross_section: int,
    quantiles: int,
) -> pd.DataFrame:
    names = {item.anomaly_id: item.name for item in anomalies}
    rows: list[dict[str, Any]] = []
    for anomaly_id, matrix in matrices.items():
        common_dates = matrix.index.intersection(forward_returns.index)
        for trade_date in common_dates:
            frame = pd.DataFrame({"score": matrix.loc[trade_date], "forward_return": forward_returns.loc[trade_date]}).dropna()
            if len(frame) < max(min_cross_section, quantiles * 2):
                continue
            frame["group"] = quantile_groups(frame["score"], quantiles)
            frame = frame.dropna(subset=["group"])
            low = frame[frame["group"] == 1]
            high = frame[frame["group"] == quantiles]
            if low.empty or high.empty:
                continue
            rows.append(
                {
                    "schema_version": ANOMALY_RETURNS_SCHEMA,
                    "trade_date": str(trade_date),
                    "anomaly_id": anomaly_id,
                    "anomaly_name": names[anomaly_id],
                    "long_short_return": float(high["forward_return"].mean() - low["forward_return"].mean()),
                    "long_mean_return": float(high["forward_return"].mean()),
                    "short_mean_return": float(low["forward_return"].mean()),
                    "symbol_count": int(len(frame)),
                    "long_count": int(len(high)),
                    "short_count": int(len(low)),
                    "quantiles": int(quantiles),
                }
            )
    return pd.DataFrame(rows)


def build_alpha_tests(
    anomaly_returns: pd.DataFrame,
    model_returns: pd.DataFrame,
    *,
    model_ids: Sequence[str],
) -> pd.DataFrame:
    if anomaly_returns.empty or model_returns.empty:
        return pd.DataFrame()
    anomaly_pivot = anomaly_returns.pivot_table(index="trade_date", columns="anomaly_id", values="long_short_return", aggfunc="last")
    model_pivot = model_returns.pivot_table(index="trade_date", columns="model_id", values="model_return", aggfunc="last")
    rows: list[dict[str, Any]] = []
    for anomaly_id in anomaly_pivot.columns:
        y_series = anomaly_pivot[anomaly_id]
        for model_id in model_ids:
            if model_id not in model_pivot.columns:
                continue
            aligned = pd.concat([y_series.rename("anomaly"), model_pivot[model_id].rename("model")], axis=1).dropna()
            if len(aligned) < 6:
                continue
            y = aligned["anomaly"].to_numpy(dtype="float64")
            x = aligned["model"].to_numpy(dtype="float64")
            design = np.column_stack([np.ones(len(aligned)), x])
            beta, *_ = np.linalg.lstsq(design, y, rcond=None)
            alpha = float(beta[0])
            slope = float(beta[1])
            alpha_series = aligned["anomaly"] - slope * aligned["model"]
            rows.append(
                {
                    "schema_version": ALPHA_TEST_SCHEMA,
                    "anomaly_id": anomaly_id,
                    "model_id": model_id,
                    "alpha": alpha,
                    "alpha_t_stat": newey_west_t_stat(alpha_series),
                    "beta_to_model": slope,
                    "observation_count": int(len(aligned)),
                    "mean_anomaly_return": float(aligned["anomaly"].mean()),
                    "mean_model_return": float(aligned["model"].mean()),
                }
            )
    return pd.DataFrame(rows)


def build_anomaly_admission_summary(
    anomaly_returns: pd.DataFrame,
    alpha_tests: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if anomaly_returns.empty:
        return rows
    for anomaly_id, group in anomaly_returns.groupby("anomaly_id", sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        alpha_group = alpha_tests[alpha_tests["anomaly_id"] == anomaly_id] if not alpha_tests.empty else pd.DataFrame()
        best_alpha_t = pd.to_numeric(alpha_group.get("alpha_t_stat", pd.Series(dtype="float64")), errors="coerce").dropna()
        t_stat = newey_west_t_stat(returns)
        mean_return = float(returns.mean()) if not returns.empty else None
        admission = anomaly_admission(mean_return, t_stat, best_alpha_t)
        rows.append(
            {
                "anomaly_id": anomaly_id,
                "admission": admission,
                "mean_long_short_return": mean_return,
                "t_stat": t_stat,
                "max_abs_alpha_t_stat": float(best_alpha_t.abs().max()) if not best_alpha_t.empty else None,
                "observation_count": int(len(returns)),
                "handoff": "CR-037 robustness review required before CR-038/CR-039 strategy admission",
            }
        )
    return rows


def anomaly_admission(mean_return: float | None, t_stat: float | None, alpha_t_stats: pd.Series) -> str:
    if mean_return is None:
        return "blocked_no_observations"
    if mean_return <= 0 or (t_stat is not None and t_stat < 0):
        return "reject_or_reweight"
    if t_stat is not None and t_stat >= 2.0 and (not alpha_t_stats.empty and float(alpha_t_stats.abs().max()) >= 2.0):
        return "alpha_feature_candidate"
    if t_stat is not None and t_stat >= 1.0:
        return "watch_needs_robustness_review"
    return "watch"


def anomaly_correlation(matrices: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    frames = [matrix.stack(future_stack=True).dropna().rename(anomaly_id) for anomaly_id, matrix in matrices.items()]
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1)
    return wide.corr(min_periods=30)


def build_gap_register(anomalies: Sequence[AnomalyDefinition]) -> list[dict[str, Any]]:
    rows = [
        {
            "gap_id": "CR036-GAP-BOOK-CHAPTER5-SOURCE",
            "status": "open-with-proxy-implemented",
            "severity": "medium",
            "description": "本仓库未找到第5章书籍 Markdown 原文；当前按 CR-036 已列出的 5.1/5.2/5.3 主题实现项目内可执行定义。",
            "impact": "报告不得宣称逐字严格复刻第5章，只能宣称项目内可执行复刻。",
        }
    ]
    for anomaly in anomalies:
        if anomaly.strict_gap:
            rows.append(
                {
                    "gap_id": f"CR036-GAP-{anomaly.anomaly_id}",
                    "status": "open-with-proxy-implemented",
                    "severity": "medium",
                    "description": anomaly.strict_gap,
                    "impact": "进入 CR-037/CR-038 前必须复验或补齐字段。",
                }
            )
    return rows


def default_blocked_claims(run_id: str) -> tuple[dict[str, str], ...]:
    return (
        {"claim": "production_valid", "status": "blocked", "reason": "CR-036 仅生成离线研究证据。", "evidence_ref": run_id},
        {"claim": "qmt_ready", "status": "blocked", "reason": "CR-036 不授权 QMT、账户、订单或 broker runtime。", "evidence_ref": run_id},
        {"claim": "simulation_ready", "status": "blocked", "reason": "CR-036 不授权 simulation 或 live。", "evidence_ref": run_id},
        {"claim": "live_ready", "status": "blocked", "reason": "CR-036 不授权 simulation 或 live。", "evidence_ref": run_id},
    )


def cross_sectional_winsorize(matrix: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    def _winsorize(row: pd.Series) -> pd.Series:
        clean = pd.to_numeric(row, errors="coerce")
        if clean.notna().sum() < 3:
            return clean
        return clean.clip(lower=clean.quantile(lower), upper=clean.quantile(upper))

    return matrix.apply(_winsorize, axis=1)


def cross_sectional_zscore(matrix: pd.DataFrame) -> pd.DataFrame:
    mean = matrix.mean(axis=1)
    std = matrix.std(axis=1, ddof=0).replace(0, np.nan)
    return matrix.sub(mean, axis=0).div(std, axis=0)


def quantile_groups(values: pd.Series, groups: int) -> pd.Series:
    ranks = values.rank(method="first")
    if ranks.notna().sum() < groups:
        return pd.Series(index=values.index, dtype="float64")
    try:
        labels = pd.qcut(ranks, groups, labels=False, duplicates="drop")
    except ValueError:
        return pd.Series(index=values.index, dtype="float64")
    return pd.Series(labels, index=values.index, dtype="float64") + 1
