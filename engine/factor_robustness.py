"""Factor robustness and research guardrail tools.

本模块只消费本地第三章因子面板、forward-return 标签和 CR-036 异象面板，
不读取凭据、不触发 provider fetch、不写 data lake、不 publish catalog、
不触发 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_model_research import labels_to_forward_return_matrix, panel_to_factor_matrices
from engine.anomaly_research import quantile_groups
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS, get_equity_factor_definition
from engine.factor_statistics import newey_west_t_stat
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import safe_float


CHAPTER6_SCHEMA = "chapter6_factor_robustness_v1"
ROBUSTNESS_RETURN_SCHEMA = "chapter6_robustness_returns_v1"
ROLLING_IC_SCHEMA = "chapter6_rolling_ic_v1"
ANNUAL_METRIC_SCHEMA = "chapter6_annual_factor_metrics_v1"
MARKET_STATE_SCHEMA = "chapter6_market_state_results_v1"
DECAY_SCHEMA = "chapter6_decay_report_v1"

FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class Chapter6RobustnessResult:
    run_id: str
    status: str
    sample_id: str
    asset_ids: tuple[str, ...]
    panel_rows: int
    label_rows: int
    anomaly_panel_rows: int
    robustness_return_rows: int
    rolling_ic_rows: int
    annual_metric_rows: int
    market_state_rows: int
    decay_rows: int
    robustness_returns: pd.DataFrame
    rolling_ic: pd.DataFrame
    annual_factor_metrics: pd.DataFrame
    market_state_results: pd.DataFrame
    decay_report: pd.DataFrame
    ml_leakage_audit: Mapping[str, Any]
    robustness_admission_summary: tuple[dict[str, Any], ...]
    guardrail_summary: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, str], ...]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER6_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_id": self.sample_id,
            "asset_ids": list(self.asset_ids),
            "panel_rows": self.panel_rows,
            "label_rows": self.label_rows,
            "anomaly_panel_rows": self.anomaly_panel_rows,
            "robustness_return_rows": self.robustness_return_rows,
            "rolling_ic_rows": self.rolling_ic_rows,
            "annual_metric_rows": self.annual_metric_rows,
            "market_state_rows": self.market_state_rows,
            "decay_rows": self.decay_rows,
            "ml_leakage_audit": dict(self.ml_leakage_audit),
            "robustness_admission_summary": list(self.robustness_admission_summary),
            "guardrail_summary": list(self.guardrail_summary),
            "blocked_claims": list(self.blocked_claims),
            "operation_counts": dict(self.operation_counts),
        }


def run_chapter6_analysis(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    anomaly_panel: pd.DataFrame | None,
    *,
    run_id: str,
    sample_id: str,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
    min_cross_section: int = 30,
    quantiles: int = 5,
    rolling_window: int = 36,
    rolling_min_periods: int = 12,
    decay_horizons: Sequence[int] = (1, 3, 6),
) -> Chapter6RobustnessResult:
    validate_chapter6_inputs(panel, labels, anomaly_panel, factor_ids=factor_ids)
    factors = panel_to_factor_matrices(panel, factor_ids=factor_ids)
    forward_returns = labels_to_forward_return_matrix(labels)
    factor_assets = {factor_id: factors[factor_id] for factor_id in factor_ids}
    anomaly_assets = anomaly_panel_to_matrices(anomaly_panel) if anomaly_panel is not None and not anomaly_panel.empty else {}
    returns = build_robustness_returns(
        factor_assets,
        anomaly_assets,
        forward_returns,
        min_cross_section=min_cross_section,
        quantiles=quantiles,
    )
    rolling_ic = build_rolling_ic(returns, rolling_window=rolling_window, rolling_min_periods=rolling_min_periods)
    annual_metrics = build_annual_factor_metrics(returns)
    market_states = build_market_state_results(returns, forward_returns)
    decay = build_decay_report(returns, horizons=decay_horizons)
    leakage = build_ml_leakage_audit(panel, labels, anomaly_panel)
    admission = build_robustness_admission_summary(returns, rolling_ic, annual_metrics, decay)
    guardrails = build_guardrail_summary(leakage)
    status = "PASS" if not returns.empty and not annual_metrics.empty and leakage.get("status") == "PASS" else "BLOCKED"
    return Chapter6RobustnessResult(
        run_id=run_id,
        status=status,
        sample_id=sample_id,
        asset_ids=tuple(sorted(returns["asset_id"].dropna().astype(str).unique())) if not returns.empty else (),
        panel_rows=int(len(panel)),
        label_rows=int(len(labels)),
        anomaly_panel_rows=int(len(anomaly_panel)) if anomaly_panel is not None else 0,
        robustness_return_rows=int(len(returns)),
        rolling_ic_rows=int(len(rolling_ic)),
        annual_metric_rows=int(len(annual_metrics)),
        market_state_rows=int(len(market_states)),
        decay_rows=int(len(decay)),
        robustness_returns=returns,
        rolling_ic=rolling_ic,
        annual_factor_metrics=annual_metrics,
        market_state_results=market_states,
        decay_report=decay,
        ml_leakage_audit=leakage,
        robustness_admission_summary=tuple(admission),
        guardrail_summary=tuple(guardrails),
        blocked_claims=default_blocked_claims(run_id),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_chapter6_inputs(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    anomaly_panel: pd.DataFrame | None,
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
    if panel.empty or labels.empty:
        raise ValueError("factor panel 和 labels 不能为空")
    present = set(panel["factor_id"].dropna().astype(str).unique())
    missing_factors = set(factor_ids) - present
    if missing_factors:
        raise ValueError("factor panel 缺少因子: " + ", ".join(sorted(missing_factors)))
    merged = panel[["trade_date", "symbol", "available_at"]].merge(
        labels[["trade_date", "symbol", "label_available_at"]],
        on=["trade_date", "symbol"],
        how="inner",
    )
    if merged.empty:
        raise ValueError("factor panel 与 labels 没有可匹配样本")
    if _has_label_leakage(merged["available_at"], merged["label_available_at"]):
        raise ValueError("label_available_at 必须晚于因子 available_at，检测到潜在前视")
    if anomaly_panel is not None and not anomaly_panel.empty:
        required_anomaly = {"trade_date", "symbol", "anomaly_id", "zscore_value", "available_at"}
        missing_anomaly = required_anomaly - set(anomaly_panel.columns)
        if missing_anomaly:
            raise ValueError("anomaly panel 缺少字段: " + ", ".join(sorted(missing_anomaly)))
        merged_anomaly = anomaly_panel[["trade_date", "symbol", "available_at"]].merge(
            labels[["trade_date", "symbol", "label_available_at"]],
            on=["trade_date", "symbol"],
            how="inner",
        )
        if not merged_anomaly.empty and _has_label_leakage(merged_anomaly["available_at"], merged_anomaly["label_available_at"]):
            raise ValueError("anomaly panel 检测到潜在前视")


def anomaly_panel_to_matrices(anomaly_panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    matrices: dict[str, pd.DataFrame] = {}
    if anomaly_panel is None or anomaly_panel.empty:
        return matrices
    work = anomaly_panel.copy()
    work["trade_date"] = work["trade_date"].astype(str)
    for anomaly_id, group in work.groupby("anomaly_id", sort=True):
        matrix = group.pivot_table(index="trade_date", columns="symbol", values="zscore_value", aggfunc="last")
        matrices[str(anomaly_id)] = matrix.sort_index().apply(pd.to_numeric, errors="coerce")
    return matrices


def build_robustness_returns(
    factor_assets: Mapping[str, pd.DataFrame],
    anomaly_assets: Mapping[str, pd.DataFrame],
    forward_returns: pd.DataFrame,
    *,
    min_cross_section: int,
    quantiles: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for asset_type, assets in (("factor", factor_assets), ("anomaly", anomaly_assets)):
        for asset_id, matrix in assets.items():
            common_dates = matrix.index.intersection(forward_returns.index)
            for trade_date in common_dates:
                frame = pd.DataFrame({"score": matrix.loc[trade_date], "forward_return": forward_returns.loc[trade_date]}).dropna()
                if len(frame) < max(min_cross_section, quantiles * 2):
                    continue
                groups = quantile_groups(frame["score"], quantiles)
                frame = frame.assign(group=groups).dropna(subset=["group"])
                low = frame[frame["group"] == 1]
                high = frame[frame["group"] == quantiles]
                if low.empty or high.empty:
                    continue
                rank_ic = _safe_corr(frame["score"].rank(method="average"), frame["forward_return"].rank(method="average"))
                rows.append(
                    {
                        "schema_version": ROBUSTNESS_RETURN_SCHEMA,
                        "trade_date": str(trade_date),
                        "asset_type": asset_type,
                        "asset_id": str(asset_id),
                        "asset_name": _asset_name(str(asset_id), asset_type),
                        "long_short_return": float(high["forward_return"].mean() - low["forward_return"].mean()),
                        "long_mean_return": float(high["forward_return"].mean()),
                        "short_mean_return": float(low["forward_return"].mean()),
                        "rank_ic": rank_ic,
                        "symbol_count": int(len(frame)),
                        "long_count": int(len(high)),
                        "short_count": int(len(low)),
                        "quantiles": int(quantiles),
                    }
                )
    return pd.DataFrame(rows)


def build_rolling_ic(
    robustness_returns: pd.DataFrame,
    *,
    rolling_window: int,
    rolling_min_periods: int,
) -> pd.DataFrame:
    if robustness_returns.empty:
        return pd.DataFrame()
    rows: list[pd.DataFrame] = []
    for (asset_type, asset_id), group in robustness_returns.groupby(["asset_type", "asset_id"], sort=True):
        work = group.sort_values("trade_date").copy()
        rank_ic = pd.to_numeric(work["rank_ic"], errors="coerce")
        ls_return = pd.to_numeric(work["long_short_return"], errors="coerce")
        out = pd.DataFrame(
            {
                "schema_version": ROLLING_IC_SCHEMA,
                "trade_date": work["trade_date"].to_numpy(),
                "asset_type": asset_type,
                "asset_id": asset_id,
                "rolling_window": int(rolling_window),
                "rolling_min_periods": int(rolling_min_periods),
                "rolling_rank_ic": rank_ic.rolling(rolling_window, min_periods=rolling_min_periods).mean().to_numpy(),
                "rolling_rank_ic_abs_mean": rank_ic.abs().rolling(rolling_window, min_periods=rolling_min_periods).mean().to_numpy(),
                "rolling_long_short_return": ls_return.rolling(rolling_window, min_periods=rolling_min_periods).mean().to_numpy(),
                "rolling_positive_ratio": (ls_return > 0).astype(float).rolling(rolling_window, min_periods=rolling_min_periods).mean().to_numpy(),
            }
        )
        rows.append(out.dropna(subset=["rolling_rank_ic", "rolling_long_short_return"], how="all"))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_annual_factor_metrics(robustness_returns: pd.DataFrame) -> pd.DataFrame:
    if robustness_returns.empty:
        return pd.DataFrame()
    work = robustness_returns.copy()
    work["year"] = pd.to_datetime(work["trade_date"]).dt.year
    rows: list[dict[str, Any]] = []
    for (asset_type, asset_id, year), group in work.groupby(["asset_type", "asset_id", "year"], sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        if returns.empty:
            continue
        rows.append(
            {
                "schema_version": ANNUAL_METRIC_SCHEMA,
                "year": int(year),
                "asset_type": asset_type,
                "asset_id": asset_id,
                "mean_long_short_return": _safe_float(returns.mean()),
                "t_stat": newey_west_t_stat(returns),
                "mean_rank_ic": _safe_float(rank_ic.mean()) if not rank_ic.empty else None,
                "positive_period_ratio": _safe_float((returns > 0).mean()),
                "observation_count": int(len(returns)),
                "admission_hint": annual_admission_hint(returns, rank_ic),
            }
        )
    return pd.DataFrame(rows)


def build_market_state_results(robustness_returns: pd.DataFrame, forward_returns: pd.DataFrame) -> pd.DataFrame:
    if robustness_returns.empty or forward_returns.empty:
        return pd.DataFrame()
    market_proxy = forward_returns.mean(axis=1, skipna=True).dropna()
    if market_proxy.empty:
        return pd.DataFrame()
    low = float(market_proxy.quantile(0.33))
    high = float(market_proxy.quantile(0.67))
    states = market_proxy.map(lambda value: "bear" if value <= low else ("bull" if value >= high else "neutral"))
    state_frame = states.rename("market_state").reset_index().rename(columns={"index": "trade_date"})
    state_frame["trade_date"] = state_frame["trade_date"].astype(str)
    work = robustness_returns.merge(state_frame, on="trade_date", how="left").dropna(subset=["market_state"])
    rows: list[dict[str, Any]] = []
    for (asset_type, asset_id, state), group in work.groupby(["asset_type", "asset_id", "market_state"], sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        if returns.empty:
            continue
        rows.append(
            {
                "schema_version": MARKET_STATE_SCHEMA,
                "asset_type": asset_type,
                "asset_id": asset_id,
                "market_state": state,
                "mean_long_short_return": _safe_float(returns.mean()),
                "t_stat": newey_west_t_stat(returns),
                "mean_rank_ic": _safe_float(rank_ic.mean()) if not rank_ic.empty else None,
                "positive_period_ratio": _safe_float((returns > 0).mean()),
                "observation_count": int(len(returns)),
            }
        )
    return pd.DataFrame(rows)


def build_decay_report(robustness_returns: pd.DataFrame, *, horizons: Sequence[int]) -> pd.DataFrame:
    if robustness_returns.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (asset_type, asset_id), group in robustness_returns.groupby(["asset_type", "asset_id"], sort=True):
        series = pd.to_numeric(group.sort_values("trade_date")["long_short_return"], errors="coerce").reset_index(drop=True)
        horizon_one_mean = None
        for horizon in horizons:
            if horizon < 1:
                continue
            horizon_return = series.rolling(horizon, min_periods=horizon).sum().shift(-(horizon - 1)).dropna()
            mean_return = _safe_float(horizon_return.mean()) if not horizon_return.empty else None
            if horizon == 1:
                horizon_one_mean = mean_return
            retention = None
            if horizon_one_mean not in (None, 0) and mean_return is not None:
                retention = mean_return / (float(horizon) * float(horizon_one_mean))
            rows.append(
                {
                    "schema_version": DECAY_SCHEMA,
                    "asset_type": asset_type,
                    "asset_id": asset_id,
                    "horizon_periods": int(horizon),
                    "mean_horizon_return": mean_return,
                    "t_stat": newey_west_t_stat(horizon_return),
                    "observation_count": int(len(horizon_return)),
                    "retention_vs_horizon1": _safe_float(retention),
                    "decay_flag": decay_flag(retention),
                }
            )
    return pd.DataFrame(rows)


def build_ml_leakage_audit(panel: pd.DataFrame, labels: pd.DataFrame, anomaly_panel: pd.DataFrame | None) -> dict[str, Any]:
    panel_merged = panel[["trade_date", "symbol", "available_at"]].merge(
        labels[["trade_date", "symbol", "label_available_at"]],
        on=["trade_date", "symbol"],
        how="inner",
    )
    factor_leakage = _leakage_count(panel_merged["available_at"], panel_merged["label_available_at"])
    anomaly_leakage = 0
    anomaly_matches = 0
    if anomaly_panel is not None and not anomaly_panel.empty:
        anomaly_merged = anomaly_panel[["trade_date", "symbol", "available_at"]].merge(
            labels[["trade_date", "symbol", "label_available_at"]],
            on=["trade_date", "symbol"],
            how="inner",
        )
        anomaly_matches = int(len(anomaly_merged))
        anomaly_leakage = _leakage_count(anomaly_merged["available_at"], anomaly_merged["label_available_at"])
    return {
        "schema_version": "chapter6_ml_leakage_audit_v1",
        "status": "PASS" if factor_leakage == 0 and anomaly_leakage == 0 else "BLOCKED",
        "factor_label_matches": int(len(panel_merged)),
        "factor_leakage_count": int(factor_leakage),
        "anomaly_label_matches": int(anomaly_matches),
        "anomaly_leakage_count": int(anomaly_leakage),
        "purge_embargo_required": True,
        "recommended_split_policy": "time_series_split_with_purge_and_embargo",
        "minimum_embargo_periods": 1,
        "ml_training_authorized": False,
        "notes": "CR-037 只审计 leakage 边界，不训练 ML 模型；后续 ML 研究必须单独声明 purge / embargo 和解释性边界。",
    }


def build_robustness_admission_summary(
    robustness_returns: pd.DataFrame,
    rolling_ic: pd.DataFrame,
    annual_metrics: pd.DataFrame,
    decay_report: pd.DataFrame,
) -> list[dict[str, Any]]:
    if robustness_returns.empty:
        return []
    annual = annual_metrics.copy() if not annual_metrics.empty else pd.DataFrame()
    decay = decay_report.copy() if not decay_report.empty else pd.DataFrame()
    rolling = rolling_ic.copy() if not rolling_ic.empty else pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (asset_type, asset_id), group in robustness_returns.groupby(["asset_type", "asset_id"], sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        rank_ic = pd.to_numeric(group["rank_ic"], errors="coerce").dropna()
        annual_group = annual[(annual["asset_type"] == asset_type) & (annual["asset_id"] == asset_id)] if not annual.empty else pd.DataFrame()
        decay_group = decay[(decay["asset_type"] == asset_type) & (decay["asset_id"] == asset_id)] if not decay.empty else pd.DataFrame()
        rolling_group = rolling[(rolling["asset_type"] == asset_type) & (rolling["asset_id"] == asset_id)] if not rolling.empty else pd.DataFrame()
        admission = robustness_admission(returns, rank_ic, annual_group, decay_group)
        rows.append(
            {
                "asset_type": asset_type,
                "asset_id": asset_id,
                "admission": admission,
                "mean_long_short_return": _safe_float(returns.mean()) if not returns.empty else None,
                "t_stat": newey_west_t_stat(returns),
                "mean_rank_ic": _safe_float(rank_ic.mean()) if not rank_ic.empty else None,
                "positive_period_ratio": _safe_float((returns > 0).mean()) if not returns.empty else None,
                "positive_year_ratio": _safe_float((pd.to_numeric(annual_group.get("mean_long_short_return", pd.Series(dtype="float64")), errors="coerce") > 0).mean()) if not annual_group.empty else None,
                "rolling_observation_count": int(len(rolling_group)),
                "decay_flags": ",".join(sorted(set(decay_group.get("decay_flag", pd.Series(dtype="str")).dropna().astype(str)))) if not decay_group.empty else "",
                "reason": robustness_reason(admission),
                "handoff": "CR-038/CR-039 只能消费 baseline/candidate；watch/reject/needs-more-data 需要保留风险说明或剔除。",
            }
        )
    return rows


def build_guardrail_summary(leakage_audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "guardrail_id": "G-CR037-PHACKING-001",
            "status": "active",
            "rule": "任何新增因子或异象必须报告全量候选、参数网格和未通过对象，禁止只汇报样本内显著结果。",
        },
        {
            "guardrail_id": "G-CR037-OOS-001",
            "status": "active",
            "rule": "进入组合实践前必须至少有样本外或观察期证据，不能只凭 2000-2019 样本内 t 值准入。",
        },
        {
            "guardrail_id": "G-CR037-LEAKAGE-001",
            "status": str(leakage_audit.get("status", "UNKNOWN")),
            "rule": "feature available_at 必须早于 label_available_at；ML 研究必须使用 purge / embargo 时间切分。",
        },
        {
            "guardrail_id": "G-CR037-RUNTIME-001",
            "status": "active",
            "rule": "CR-037 不授权 provider fetch、lake write、publish、QMT、simulation、live、账户、订单或凭据读取。",
        },
    ]


def annual_admission_hint(returns: pd.Series, rank_ic: pd.Series) -> str:
    t_stat = newey_west_t_stat(returns)
    mean_return = float(returns.mean())
    mean_ic = float(rank_ic.mean()) if not rank_ic.empty else 0.0
    if mean_return <= 0 or (t_stat is not None and t_stat < 0):
        return "weak_or_reversed"
    if t_stat is not None and t_stat >= 1.5 and mean_ic > 0:
        return "stable_positive"
    return "mixed"


def robustness_admission(
    returns: pd.Series,
    rank_ic: pd.Series,
    annual_group: pd.DataFrame,
    decay_group: pd.DataFrame,
) -> str:
    if len(returns) < 12:
        return "needs-more-data"
    t_stat = newey_west_t_stat(returns)
    mean_return = float(returns.mean())
    positive_ratio = float((returns > 0).mean())
    mean_ic = float(rank_ic.mean()) if not rank_ic.empty else 0.0
    positive_year_ratio = 0.0
    if not annual_group.empty:
        positive_year_ratio = float((pd.to_numeric(annual_group["mean_long_short_return"], errors="coerce") > 0).mean())
    severe_decay = False
    if not decay_group.empty and "decay_flag" in decay_group:
        severe_decay = bool((decay_group["decay_flag"] == "severe_decay").any())
    if mean_return <= 0 or (t_stat is not None and t_stat < 0) or positive_year_ratio < 0.35:
        return "reject"
    if severe_decay or positive_ratio < 0.45:
        return "watch"
    if t_stat is not None and t_stat >= 2.0 and mean_ic > 0 and positive_year_ratio >= 0.60:
        return "baseline"
    if t_stat is not None and t_stat >= 1.0 and positive_year_ratio >= 0.50:
        return "candidate"
    return "watch"


def robustness_reason(admission: str) -> str:
    if admission == "baseline":
        return "收益、RankIC、年度方向和衰减指标达到 baseline 候选阈值；仍不等于生产或交易授权。"
    if admission == "candidate":
        return "总体方向为正但仍需组合层约束、成本敏感性或更长样本确认。"
    if admission == "watch":
        return "稳定性、衰减或市场状态分层不充分，只能观察。"
    if admission == "reject":
        return "多窗口收益方向或年度稳定性不满足准入下限。"
    return "有效样本不足或数据质量不足，需补齐后再评估。"


def decay_flag(retention: float | None) -> str:
    if retention is None:
        return "insufficient"
    if retention < 0:
        return "reversal"
    if retention < 0.35:
        return "severe_decay"
    if retention < 0.65:
        return "moderate_decay"
    return "stable"


def default_blocked_claims(run_id: str) -> tuple[dict[str, str], ...]:
    return (
        {"claim": "production_valid", "status": "blocked", "reason": "CR-037 仅生成离线稳健性研究证据。", "evidence_ref": run_id},
        {"claim": "qmt_ready", "status": "blocked", "reason": "CR-037 不授权 QMT、账户、订单或 broker runtime。", "evidence_ref": run_id},
        {"claim": "simulation_ready", "status": "blocked", "reason": "CR-037 不授权 simulation 或 live。", "evidence_ref": run_id},
        {"claim": "live_ready", "status": "blocked", "reason": "CR-037 不授权 simulation 或 live。", "evidence_ref": run_id},
        {"claim": "ml_model_ready", "status": "blocked", "reason": "CR-037 只做 ML leakage audit，不训练或准入 ML 模型。", "evidence_ref": run_id},
    )


def _asset_name(asset_id: str, asset_type: str) -> str:
    if asset_type == "factor":
        try:
            return get_equity_factor_definition(asset_id).name
        except KeyError:
            return asset_id
    return asset_id


def _has_label_leakage(available_at: pd.Series, label_available_at: pd.Series) -> bool:
    return _leakage_count(available_at, label_available_at) > 0


def _leakage_count(available_at: pd.Series, label_available_at: pd.Series) -> int:
    left = pd.to_datetime(available_at, errors="coerce", utc=True)
    right = pd.to_datetime(label_available_at, errors="coerce", utc=True)
    return int((left.notna() & right.notna() & (right <= left)).sum())


def _safe_corr(left: pd.Series, right: pd.Series) -> float | None:
    aligned = pd.concat([left.rename("left"), right.rename("right")], axis=1).dropna()
    if len(aligned) < 3:
        return None
    if aligned["left"].std(ddof=0) == 0 or aligned["right"].std(ddof=0) == 0:
        return None
    return _safe_float(aligned["left"].corr(aligned["right"]))


def _safe_float(value: Any) -> float | None:
    return safe_float(value)
