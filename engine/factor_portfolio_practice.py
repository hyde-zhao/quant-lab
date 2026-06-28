"""Factor portfolio practice, risk and capacity analysis tools.

本模块只消费本地第三章因子面板、forward-return 标签和 CR-037 稳健性
准入摘要，不读取凭据、不触发 provider fetch、不写 data lake、不 publish
catalog、不触发 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_model_research import labels_to_forward_return_matrix, panel_to_factor_matrices
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import safe_float


CHAPTER7_SCHEMA = "chapter7_factor_practice_v1"
ALPHA_SCORE_SCHEMA = "chapter7_alpha_scores_v1"
PORTFOLIO_WEIGHT_SCHEMA = "chapter7_portfolio_weights_v1"
PORTFOLIO_METRIC_SCHEMA = "chapter7_portfolio_metrics_v1"
RISK_EXPOSURE_SCHEMA = "chapter7_risk_exposure_v1"
ATTRIBUTION_SCHEMA = "chapter7_performance_attribution_v1"
COST_SCHEMA = "chapter7_turnover_cost_analysis_v1"
CAPACITY_SCHEMA = "chapter7_capacity_liquidity_analysis_v1"

ALLOWED_ADMISSIONS = {"baseline", "candidate"}
WATCH_ADMISSIONS = {"watch"}
REJECTED_ADMISSIONS = {"reject", "needs-more-data", "blocked_missing_evidence", "blocked-missing-evidence"}
FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class Chapter7Config:
    top_n: int = 30
    min_cross_section: int = 30
    max_weight: float = 0.08
    cost_bps: tuple[float, ...] = (0.0, 10.0, 25.0, 50.0)
    default_cost_bps: float = 25.0
    capacity_weight_limit: float = 0.10


@dataclass(frozen=True, slots=True)
class AdmissionAsset:
    asset_id: str
    asset_type: str
    admission: str
    weight: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Chapter7AnalysisResult:
    run_id: str
    status: str
    sample_id: str
    allowed_assets: tuple[AdmissionAsset, ...]
    watch_assets: tuple[AdmissionAsset, ...]
    rejected_assets: tuple[AdmissionAsset, ...]
    panel_rows: int
    label_rows: int
    alpha_score_rows: int
    portfolio_weight_rows: int
    portfolio_metric_rows: int
    risk_exposure_rows: int
    attribution_rows: int
    cost_rows: int
    capacity_rows: int
    alpha_scores: pd.DataFrame
    optimized_portfolios: pd.DataFrame
    portfolio_metrics: pd.DataFrame
    risk_exposure: pd.DataFrame
    performance_attribution: pd.DataFrame
    turnover_cost_analysis: pd.DataFrame
    capacity_liquidity_analysis: pd.DataFrame
    portfolio_admission_summary: tuple[dict[str, Any], ...]
    blocked_claims: tuple[dict[str, str], ...]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = CHAPTER7_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "sample_id": self.sample_id,
            "allowed_assets": [item.to_dict() for item in self.allowed_assets],
            "watch_assets": [item.to_dict() for item in self.watch_assets],
            "rejected_assets": [item.to_dict() for item in self.rejected_assets],
            "panel_rows": self.panel_rows,
            "label_rows": self.label_rows,
            "alpha_score_rows": self.alpha_score_rows,
            "portfolio_weight_rows": self.portfolio_weight_rows,
            "portfolio_metric_rows": self.portfolio_metric_rows,
            "risk_exposure_rows": self.risk_exposure_rows,
            "attribution_rows": self.attribution_rows,
            "cost_rows": self.cost_rows,
            "capacity_rows": self.capacity_rows,
            "portfolio_admission_summary": list(self.portfolio_admission_summary),
            "blocked_claims": list(self.blocked_claims),
            "operation_counts": dict(self.operation_counts),
        }


def run_chapter7_analysis(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    robustness_admission: Mapping[str, Any],
    *,
    run_id: str,
    sample_id: str,
    config: Chapter7Config | None = None,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
) -> Chapter7AnalysisResult:
    cfg = config or Chapter7Config()
    validate_chapter7_inputs(panel, labels, robustness_admission, factor_ids=factor_ids)
    factors = panel_to_factor_matrices(panel, factor_ids=factor_ids)
    forward_returns = labels_to_forward_return_matrix(labels)
    allowed, watch, rejected = parse_robustness_admission(robustness_admission, sample_id=sample_id)
    if not allowed:
        raise ValueError("CR-037 准入摘要没有 baseline/candidate 资产，CR-038 fail-closed")

    alpha_scores = build_alpha_scores(factors, allowed, run_id=run_id)
    optimized_portfolios = build_portfolio_weights(alpha_scores, config=cfg, run_id=run_id)
    portfolio_metrics = build_portfolio_metrics(optimized_portfolios, forward_returns)
    risk_exposure = build_risk_exposure(optimized_portfolios, factors)
    performance_attribution = build_performance_attribution(portfolio_metrics, risk_exposure)
    turnover_cost_analysis = build_turnover_cost_analysis(portfolio_metrics, config=cfg)
    capacity_liquidity_analysis = build_capacity_liquidity_analysis(optimized_portfolios, factors, config=cfg)
    summary = build_portfolio_admission_summary(
        portfolio_metrics,
        turnover_cost_analysis,
        capacity_liquidity_analysis,
        allowed_assets=allowed,
        watch_assets=watch,
        rejected_assets=rejected,
        run_id=run_id,
    )
    status = "PASS" if not alpha_scores.empty and not optimized_portfolios.empty and not summary.empty else "BLOCKED"
    return Chapter7AnalysisResult(
        run_id=run_id,
        status=status,
        sample_id=sample_id,
        allowed_assets=tuple(allowed),
        watch_assets=tuple(watch),
        rejected_assets=tuple(rejected),
        panel_rows=int(len(panel)),
        label_rows=int(len(labels)),
        alpha_score_rows=int(len(alpha_scores)),
        portfolio_weight_rows=int(len(optimized_portfolios)),
        portfolio_metric_rows=int(len(portfolio_metrics)),
        risk_exposure_rows=int(len(risk_exposure)),
        attribution_rows=int(len(performance_attribution)),
        cost_rows=int(len(turnover_cost_analysis)),
        capacity_rows=int(len(capacity_liquidity_analysis)),
        alpha_scores=alpha_scores,
        optimized_portfolios=optimized_portfolios,
        portfolio_metrics=portfolio_metrics,
        risk_exposure=risk_exposure,
        performance_attribution=performance_attribution,
        turnover_cost_analysis=turnover_cost_analysis,
        capacity_liquidity_analysis=capacity_liquidity_analysis,
        portfolio_admission_summary=tuple(summary.to_dict("records")),
        blocked_claims=default_blocked_claims(run_id),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_chapter7_inputs(
    panel: pd.DataFrame,
    labels: pd.DataFrame,
    robustness_admission: Mapping[str, Any],
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
    if not robustness_admission or "samples" not in robustness_admission:
        raise ValueError("缺少 CR-037 robustness admission samples")
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


def parse_robustness_admission(
    robustness_admission: Mapping[str, Any],
    *,
    sample_id: str,
) -> tuple[list[AdmissionAsset], list[AdmissionAsset], list[AdmissionAsset]]:
    rows = _admission_rows_for_sample(robustness_admission, sample_id)
    allowed: list[AdmissionAsset] = []
    watch: list[AdmissionAsset] = []
    rejected: list[AdmissionAsset] = []
    for row in rows:
        asset = AdmissionAsset(
            asset_id=str(row.get("asset_id", "")),
            asset_type=str(row.get("asset_type", "")),
            admission=str(row.get("admission", "")).strip(),
            weight=_admission_weight(row),
            reason=str(row.get("reason", "")),
        )
        if not asset.asset_id:
            continue
        if asset.admission in ALLOWED_ADMISSIONS:
            allowed.append(asset)
        elif asset.admission in WATCH_ADMISSIONS:
            watch.append(asset)
        elif asset.admission in REJECTED_ADMISSIONS:
            rejected.append(asset)
        else:
            rejected.append(asset)
    total = sum(item.weight for item in allowed)
    if total > 0:
        allowed = [AdmissionAsset(item.asset_id, item.asset_type, item.admission, item.weight / total, item.reason) for item in allowed]
    return allowed, watch, rejected


def build_alpha_scores(
    factors: Mapping[str, pd.DataFrame],
    allowed_assets: Sequence[AdmissionAsset],
    *,
    run_id: str,
) -> pd.DataFrame:
    score: pd.DataFrame | None = None
    component_cols: dict[str, pd.DataFrame] = {}
    for asset in allowed_assets:
        if asset.asset_type != "factor" or asset.asset_id not in factors:
            continue
        weighted = factors[asset.asset_id] * asset.weight
        score = weighted if score is None else score.add(weighted, fill_value=0.0)
        component_cols[asset.asset_id] = factors[asset.asset_id]
    if score is None or score.empty:
        raise ValueError("CR-038 当前只允许消费 CR-037 baseline/candidate factor；没有可用 factor 输入")
    zscore = score.apply(_zscore_row, axis=1)
    rows = zscore.stack(future_stack=True).rename("alpha_score").reset_index()
    rows.columns = ["trade_date", "symbol", "alpha_score"]
    rows = rows.dropna(subset=["alpha_score"])
    rows["schema_version"] = ALPHA_SCORE_SCHEMA
    rows["run_id"] = run_id
    rows["source_admission"] = ",".join(asset.asset_id for asset in allowed_assets)
    for asset_id, matrix in component_cols.items():
        component = matrix.stack(future_stack=True).rename(asset_id).reset_index()
        component.columns = ["trade_date", "symbol", asset_id]
        rows = rows.merge(component, on=["trade_date", "symbol"], how="left")
    return rows[["schema_version", "run_id", "trade_date", "symbol", "alpha_score", "source_admission", *component_cols.keys()]]


def build_portfolio_weights(alpha_scores: pd.DataFrame, *, config: Chapter7Config, run_id: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date, group in alpha_scores.groupby("trade_date", sort=True):
        ranked = group.dropna(subset=["alpha_score"]).sort_values("alpha_score", ascending=False)
        if len(ranked) < config.min_cross_section:
            continue
        selected = ranked.head(min(config.top_n, len(ranked))).copy()
        equal_weight = 1.0 / len(selected)
        for _, row in selected.iterrows():
            rows.append(_weight_row(run_id, trade_date, row["symbol"], "equal_weight_baseline", equal_weight, row["alpha_score"]))
        raw = selected["alpha_score"] - selected["alpha_score"].min()
        if float(raw.sum()) <= 0:
            raw = pd.Series(1.0, index=selected.index)
        weights = _cap_and_normalize(raw / raw.sum(), config.max_weight)
        for (_, row), weight in zip(selected.iterrows(), weights, strict=False):
            rows.append(_weight_row(run_id, trade_date, row["symbol"], "risk_adjusted_constrained", float(weight), row["alpha_score"]))
    return pd.DataFrame(rows)


def build_portfolio_metrics(portfolios: pd.DataFrame, forward_returns: pd.DataFrame) -> pd.DataFrame:
    if portfolios.empty:
        return pd.DataFrame()
    returns = forward_returns.stack(future_stack=True).rename("forward_return").reset_index()
    returns.columns = ["trade_date", "symbol", "forward_return"]
    work = portfolios.merge(returns, on=["trade_date", "symbol"], how="left")
    rows: list[dict[str, Any]] = []
    previous: dict[str, pd.Series] = {}
    for (portfolio_id, trade_date), group in work.groupby(["portfolio_id", "trade_date"], sort=True):
        weights = group.set_index("symbol")["target_weight"].astype(float)
        rets = pd.to_numeric(group.set_index("symbol")["forward_return"], errors="coerce").fillna(0.0)
        gross_return = float((weights * rets).sum())
        prev = previous.get(str(portfolio_id), pd.Series(dtype=float))
        turnover = _turnover(prev, weights)
        previous[str(portfolio_id)] = weights
        rows.append(
            {
                "schema_version": PORTFOLIO_METRIC_SCHEMA,
                "trade_date": str(trade_date),
                "portfolio_id": portfolio_id,
                "gross_return": gross_return,
                "turnover": turnover,
                "holding_count": int((weights > 0).sum()),
                "max_weight": float(weights.max()) if not weights.empty else 0.0,
                "missing_return_count": int(group["forward_return"].isna().sum()),
            }
        )
    metrics = pd.DataFrame(rows)
    if not metrics.empty:
        metrics["cum_gross_return"] = metrics.groupby("portfolio_id")["gross_return"].transform(lambda s: (1.0 + s).cumprod() - 1.0)
    return metrics


def build_risk_exposure(portfolios: pd.DataFrame, factors: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    if portfolios.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for factor_id, matrix in factors.items():
        exposures = matrix.stack(future_stack=True).rename("factor_exposure").reset_index()
        exposures.columns = ["trade_date", "symbol", "factor_exposure"]
        work = portfolios.merge(exposures, on=["trade_date", "symbol"], how="left")
        for (portfolio_id, trade_date), group in work.groupby(["portfolio_id", "trade_date"], sort=True):
            rows.append(
                {
                    "schema_version": RISK_EXPOSURE_SCHEMA,
                    "trade_date": str(trade_date),
                    "portfolio_id": portfolio_id,
                    "risk_factor": factor_id,
                    "weighted_exposure": _safe_float((group["target_weight"] * group["factor_exposure"].fillna(0.0)).sum()),
                    "absolute_exposure": _safe_float((group["target_weight"] * group["factor_exposure"].fillna(0.0).abs()).sum()),
                    "missing_exposure_count": int(group["factor_exposure"].isna().sum()),
                }
            )
    return pd.DataFrame(rows)


def build_performance_attribution(portfolio_metrics: pd.DataFrame, risk_exposure: pd.DataFrame) -> pd.DataFrame:
    if portfolio_metrics.empty or risk_exposure.empty:
        return pd.DataFrame()
    mean_returns = portfolio_metrics.groupby("portfolio_id")["gross_return"].mean().rename("mean_gross_return").reset_index()
    work = risk_exposure.merge(mean_returns, on="portfolio_id", how="left")
    rows = []
    for _, row in work.iterrows():
        rows.append(
            {
                "schema_version": ATTRIBUTION_SCHEMA,
                "trade_date": row["trade_date"],
                "portfolio_id": row["portfolio_id"],
                "risk_factor": row["risk_factor"],
                "weighted_exposure": row["weighted_exposure"],
                "attribution_proxy": _safe_float(row["weighted_exposure"] * row["mean_gross_return"]),
                "method": "exposure_times_portfolio_mean_return_proxy",
            }
        )
    return pd.DataFrame(rows)


def build_turnover_cost_analysis(portfolio_metrics: pd.DataFrame, *, config: Chapter7Config) -> pd.DataFrame:
    if portfolio_metrics.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for _, row in portfolio_metrics.iterrows():
        for cost_bps in config.cost_bps:
            cost = float(row["turnover"]) * float(cost_bps) / 10000.0
            rows.append(
                {
                    "schema_version": COST_SCHEMA,
                    "trade_date": row["trade_date"],
                    "portfolio_id": row["portfolio_id"],
                    "cost_bps": float(cost_bps),
                    "gross_return": row["gross_return"],
                    "turnover": row["turnover"],
                    "cost_drag": cost,
                    "net_return": float(row["gross_return"]) - cost,
                }
            )
    out = pd.DataFrame(rows)
    if not out.empty:
        out["cum_net_return"] = out.groupby(["portfolio_id", "cost_bps"])["net_return"].transform(lambda s: (1.0 + s).cumprod() - 1.0)
    return out


def build_capacity_liquidity_analysis(
    portfolios: pd.DataFrame,
    factors: Mapping[str, pd.DataFrame],
    *,
    config: Chapter7Config,
) -> pd.DataFrame:
    if portfolios.empty:
        return pd.DataFrame()
    size = factors.get("size_total_market_cap", pd.DataFrame()).stack(future_stack=True).rename("size_exposure").reset_index()
    turnover = factors.get("abnormal_turnover_21_252", pd.DataFrame()).stack(future_stack=True).rename("turnover_exposure").reset_index()
    if not size.empty:
        size.columns = ["trade_date", "symbol", "size_exposure"]
    if not turnover.empty:
        turnover.columns = ["trade_date", "symbol", "turnover_exposure"]
    work = portfolios.copy()
    if not size.empty:
        work = work.merge(size, on=["trade_date", "symbol"], how="left")
    else:
        work["size_exposure"] = np.nan
    if not turnover.empty:
        work = work.merge(turnover, on=["trade_date", "symbol"], how="left")
    else:
        work["turnover_exposure"] = np.nan
    rows: list[dict[str, Any]] = []
    for (portfolio_id, trade_date), group in work.groupby(["portfolio_id", "trade_date"], sort=True):
        weights = pd.to_numeric(group["target_weight"], errors="coerce").fillna(0.0)
        low_liquidity_weight = float(weights[group["turnover_exposure"].fillna(0.0) < -0.5].sum())
        small_cap_weight = float(weights[group["size_exposure"].fillna(0.0) < -0.5].sum())
        max_weight = float(weights.max()) if not weights.empty else 0.0
        rows.append(
            {
                "schema_version": CAPACITY_SCHEMA,
                "trade_date": str(trade_date),
                "portfolio_id": portfolio_id,
                "holding_count": int((weights > 0).sum()),
                "max_single_name_weight": max_weight,
                "low_liquidity_proxy_weight": low_liquidity_weight,
                "small_cap_proxy_weight": small_cap_weight,
                "capacity_status": "PASS" if max_weight <= config.capacity_weight_limit else "WATCH",
                "capacity_proxy": "size_total_market_cap + abnormal_turnover_21_252",
            }
        )
    return pd.DataFrame(rows)


def build_portfolio_admission_summary(
    portfolio_metrics: pd.DataFrame,
    turnover_cost_analysis: pd.DataFrame,
    capacity_liquidity_analysis: pd.DataFrame,
    *,
    allowed_assets: Sequence[AdmissionAsset],
    watch_assets: Sequence[AdmissionAsset],
    rejected_assets: Sequence[AdmissionAsset],
    run_id: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if portfolio_metrics.empty:
        return pd.DataFrame()
    default_cost = turnover_cost_analysis.sort_values("cost_bps").groupby(["portfolio_id", "cost_bps"], sort=True)
    net_by_portfolio: dict[str, float] = {}
    for (portfolio_id, cost_bps), group in default_cost:
        if float(cost_bps) == 25.0:
            net_by_portfolio[str(portfolio_id)] = float(group["net_return"].mean())
    capacity = capacity_liquidity_analysis.groupby("portfolio_id").agg(
        max_single_name_weight=("max_single_name_weight", "max"),
        max_low_liquidity_proxy_weight=("low_liquidity_proxy_weight", "max"),
        max_small_cap_proxy_weight=("small_cap_proxy_weight", "max"),
        capacity_watch_count=("capacity_status", lambda s: int((s != "PASS").sum())),
    )
    for portfolio_id, group in portfolio_metrics.groupby("portfolio_id", sort=True):
        gross_mean = float(group["gross_return"].mean())
        turnover_mean = float(group["turnover"].mean())
        cap = capacity.loc[portfolio_id] if portfolio_id in capacity.index else None
        capacity_ok = bool(cap is not None and int(cap["capacity_watch_count"]) == 0)
        net_mean = net_by_portfolio.get(str(portfolio_id), gross_mean)
        admission = "research_candidate" if net_mean > 0 and capacity_ok else "research_watch"
        rows.append(
            {
                "schema_version": "chapter7_portfolio_admission_summary_v1",
                "run_id": run_id,
                "portfolio_id": portfolio_id,
                "admission": admission,
                "simulation_candidate": False,
                "gross_mean_return": gross_mean,
                "net_mean_return_25bps": net_mean,
                "mean_turnover": turnover_mean,
                "max_drawdown_proxy": _max_drawdown(group["gross_return"]),
                "capacity_evidence": "proxy_available" if cap is not None else "missing",
                "max_single_name_weight": None if cap is None else float(cap["max_single_name_weight"]),
                "max_low_liquidity_proxy_weight": None if cap is None else float(cap["max_low_liquidity_proxy_weight"]),
                "max_small_cap_proxy_weight": None if cap is None else float(cap["max_small_cap_proxy_weight"]),
                "allowed_assets": [item.to_dict() for item in allowed_assets],
                "watch_assets_policy": [item.to_dict() for item in watch_assets],
                "rejected_assets_excluded": [item.to_dict() for item in rejected_assets],
                "not_authorization": True,
                "handoff": "仅供 CR-039 研究准入消费；不构成 simulation-ready、live-ready、QMT-ready 或 production-valid。",
            }
        )
    return pd.DataFrame(rows)


def default_blocked_claims(run_id: str) -> tuple[dict[str, str], ...]:
    return (
        {"claim": "production_valid", "status": "blocked", "reason": "CR-038 仅生成离线组合研究证据。", "evidence_ref": run_id},
        {"claim": "qmt_ready", "status": "blocked", "reason": "CR-038 不授权 QMT、账户、订单或 broker runtime。", "evidence_ref": run_id},
        {"claim": "simulation_ready", "status": "blocked", "reason": "CR-038 不授权 simulation 或 live。", "evidence_ref": run_id},
        {"claim": "live_ready", "status": "blocked", "reason": "CR-038 不授权 simulation 或 live。", "evidence_ref": run_id},
        {"claim": "provider_or_lake_publish_ready", "status": "blocked", "reason": "CR-038 不授权 provider fetch、lake write 或 catalog publish。", "evidence_ref": run_id},
    )


def _admission_rows_for_sample(robustness_admission: Mapping[str, Any], sample_id: str) -> list[Mapping[str, Any]]:
    samples = robustness_admission.get("samples", [])
    if not isinstance(samples, list):
        raise ValueError("CR-037 robustness admission samples 必须为数组")
    fallback: list[Mapping[str, Any]] = []
    for sample in samples:
        rows = sample.get("robustness_admission_summary", []) if isinstance(sample, Mapping) else []
        if not isinstance(rows, list):
            continue
        if str(sample.get("sample_id", "")) == sample_id:
            return [row for row in rows if isinstance(row, Mapping)]
        fallback.extend(row for row in rows if isinstance(row, Mapping))
    return fallback


def _admission_weight(row: Mapping[str, Any]) -> float:
    t_stat = abs(_safe_float(row.get("t_stat"), default=0.0))
    rank_ic = abs(_safe_float(row.get("mean_rank_ic"), default=0.0)) * 10.0
    mean_return = max(_safe_float(row.get("mean_long_short_return"), default=0.0), 0.0) * 100.0
    return max(t_stat + rank_ic + mean_return, 0.01)


def _weight_row(run_id: str, trade_date: Any, symbol: Any, portfolio_id: str, weight: float, alpha_score: Any) -> dict[str, Any]:
    return {
        "schema_version": PORTFOLIO_WEIGHT_SCHEMA,
        "run_id": run_id,
        "trade_date": str(trade_date),
        "symbol": str(symbol),
        "portfolio_id": portfolio_id,
        "target_weight": float(weight),
        "alpha_score": _safe_float(alpha_score),
        "research_only": True,
    }


def _zscore_row(row: pd.Series) -> pd.Series:
    values = pd.to_numeric(row, errors="coerce")
    std = float(values.std(ddof=0))
    if not np.isfinite(std) or std == 0.0:
        return values * 0.0
    return (values - float(values.mean())) / std


def _cap_and_normalize(weights: pd.Series, cap: float) -> pd.Series:
    out = weights.clip(lower=0.0).astype(float)
    if float(out.sum()) <= 0:
        out = pd.Series(1.0 / len(out), index=out.index)
    out = out / float(out.sum())
    for _ in range(20):
        over = out > cap
        if not bool(over.any()):
            break
        excess = float((out[over] - cap).sum())
        out[over] = cap
        under = ~over
        if not bool(under.any()) or float(out[under].sum()) <= 0:
            break
        out[under] += out[under] / float(out[under].sum()) * excess
    total = float(out.sum())
    return out / total if total > 0 else out


def _turnover(previous: pd.Series, current: pd.Series) -> float:
    if previous.empty:
        return float(current.abs().sum())
    aligned = pd.concat([previous.rename("previous"), current.rename("current")], axis=1).fillna(0.0)
    return float((aligned["current"] - aligned["previous"]).abs().sum() / 2.0)


def _max_drawdown(returns: pd.Series) -> float:
    curve = (1.0 + pd.to_numeric(returns, errors="coerce").fillna(0.0)).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _safe_float(value: Any, default: float | None = None) -> float:
    number = safe_float(value)
    if number is not None:
        return number
    if default is None:
        return float("nan")
    return default
