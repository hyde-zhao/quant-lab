"""CR-039 多因子策略候选研究准入工具。

本模块只消费本地 CR-038 组合研究 artifact 和准入摘要，生成研究级
策略候选、风险成本摘要、因子贡献和准入包。不读取凭据、不访问网络、
不写 data lake、不 publish catalog、不触发 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


STRATEGY_RESEARCH_SCHEMA = "multifactor_strategy_research_v1"
STRATEGY_SCORE_SCHEMA = "multifactor_strategy_scores_v1"
BACKTEST_RESULT_SCHEMA = "multifactor_strategy_backtest_results_v1"
FACTOR_CONTRIBUTION_SCHEMA = "multifactor_strategy_factor_contribution_v1"
RISK_COST_SCHEMA = "multifactor_strategy_risk_cost_summary_v1"
STRATEGY_ADMISSION_PACKAGE_SCHEMA = "multifactor_strategy_admission_package_v1"

FORBIDDEN_OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
RUNTIME_CLAIMS = (
    "qmt_ready",
    "simulation_ready",
    "live_ready",
    "production_valid",
    "account_or_order_ready",
    "provider_or_lake_publish_ready",
)


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    strategy_id: str
    source_portfolio_id: str
    admission: str
    simulation_candidate: bool
    evidence_status: str
    mean_net_return_25bps: float
    mean_turnover: float
    max_drawdown_proxy: float
    capacity_evidence: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class StrategyResearchResult:
    run_id: str
    status: str
    strategy_candidates: tuple[StrategyCandidate, ...]
    strategy_scores: pd.DataFrame
    backtest_results: pd.DataFrame
    factor_contribution: pd.DataFrame
    risk_cost_summary: pd.DataFrame
    admission_package: Mapping[str, Any]
    blocked_reasons: tuple[dict[str, Any], ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = STRATEGY_RESEARCH_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "strategy_candidates": [item.to_dict() for item in self.strategy_candidates],
            "strategy_score_rows": int(len(self.strategy_scores)),
            "backtest_result_rows": int(len(self.backtest_results)),
            "factor_contribution_rows": int(len(self.factor_contribution)),
            "risk_cost_summary_rows": int(len(self.risk_cost_summary)),
            "admission_package": dict(self.admission_package),
            "blocked_reasons": list(self.blocked_reasons),
            "operation_counts": dict(self.operation_counts),
        }


def run_strategy_research(
    *,
    run_id: str,
    upstream_research_summaries: Mapping[str, Mapping[str, Any]],
    portfolio_admission_payload: Mapping[str, Any],
    alpha_scores: pd.DataFrame,
    portfolio_metrics: pd.DataFrame,
    turnover_cost_analysis: pd.DataFrame,
    capacity_liquidity_analysis: pd.DataFrame,
    risk_exposure: pd.DataFrame,
    performance_attribution: pd.DataFrame,
    input_refs: Mapping[str, str] | None = None,
) -> StrategyResearchResult:
    """基于 CR-038 本地产物生成 CR-039 策略候选准入结果。"""

    validate_upstream_research_summaries(upstream_research_summaries)
    validate_portfolio_admission_payload(portfolio_admission_payload)
    candidates = build_strategy_candidates(portfolio_admission_payload)
    candidates, excluded = filter_capacity_passing_candidates(candidates, capacity_liquidity_analysis)
    if not candidates:
        return blocked_missing_evidence_result(
            run_id,
            [f"all_candidate_capacity_nonpass:{','.join(excluded)}" if excluded else "no_candidate_after_capacity_gate"],
            input_refs=input_refs,
        )
    missing = missing_evidence(
        portfolio_metrics=portfolio_metrics,
        turnover_cost_analysis=turnover_cost_analysis,
        capacity_liquidity_analysis=capacity_liquidity_analysis,
        risk_exposure=risk_exposure,
        performance_attribution=performance_attribution,
        candidate_portfolios=[item.source_portfolio_id for item in candidates],
    )
    if missing:
        return blocked_missing_evidence_result(run_id, missing, input_refs=input_refs)

    backtest_results = build_backtest_results(portfolio_metrics, turnover_cost_analysis)
    candidate_portfolios = {item.source_portfolio_id for item in candidates}
    backtest_results = backtest_results.loc[backtest_results["portfolio_id"].astype(str).isin(candidate_portfolios)].reset_index(drop=True)
    risk_cost_summary = build_risk_cost_summary(
        backtest_results,
        capacity_liquidity_analysis,
        risk_exposure,
        candidates,
    )
    factor_contribution = build_factor_contribution(performance_attribution, candidate_portfolios=candidate_portfolios)
    strategy_scores = build_strategy_scores(alpha_scores, candidates)
    candidates = refine_candidate_admissions(candidates, risk_cost_summary)
    package = build_strategy_admission_package(
        run_id=run_id,
        candidates=candidates,
        upstream_research_summaries=upstream_research_summaries,
        portfolio_admission_payload=portfolio_admission_payload,
        risk_cost_summary=risk_cost_summary,
        input_refs=input_refs or {},
    )
    status = "PASS" if candidates and any(item.admission in {"research_baseline", "watch"} for item in candidates) else "BLOCKED"
    return StrategyResearchResult(
        run_id=run_id,
        status=status,
        strategy_candidates=tuple(candidates),
        strategy_scores=strategy_scores,
        backtest_results=backtest_results,
        factor_contribution=factor_contribution,
        risk_cost_summary=risk_cost_summary,
        admission_package=package,
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def validate_portfolio_admission_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "chapter7_portfolio_admission_payload_v1":
        raise RuntimeError(f"CR-038 portfolio admission schema 不匹配: {payload.get('schema_version')}")
    if payload.get("not_authorization") is not True:
        raise RuntimeError("CR-038 portfolio admission 必须声明 not_authorization=true")
    assert_zero_operation_counts(payload.get("operation_counts") or {}, source="CR-038 portfolio admission")
    samples = payload.get("samples")
    if not isinstance(samples, list) or not samples:
        raise RuntimeError("CR-038 portfolio admission samples 不能为空")


def assert_zero_operation_counts(counts: Mapping[str, Any], *, source: str) -> None:
    missing = set(FORBIDDEN_OPERATION_COUNTERS) - set(counts)
    extra = set(counts) - set(FORBIDDEN_OPERATION_COUNTERS)
    if missing or extra:
        detail = []
        if missing:
            detail.append("missing=" + ",".join(sorted(missing)))
        if extra:
            detail.append("extra=" + ",".join(sorted(extra)))
        raise RuntimeError(f"{source} operation_counts 字段必须与 FORBIDDEN_OPERATION_COUNTERS 完全一致: {'; '.join(detail)}")
    nonzero = {str(key): value for key, value in counts.items() if int(value or 0) != 0}
    if nonzero:
        raise RuntimeError(f"{source} operation_counts 必须全为 0: " + ",".join(sorted(nonzero)))


def validate_upstream_research_summaries(summaries: Mapping[str, Mapping[str, Any]]) -> None:
    expected = {
        "cr035_model_admission": "chapter4_model_admission_summary_v1",
        "cr036_anomaly_admission": "chapter5_anomaly_admission_summary_v1",
        "cr037_robustness_admission": "chapter6_robustness_admission_summary_v1",
    }
    missing = set(expected) - set(summaries)
    if missing:
        raise RuntimeError("CR-039 缺少上游研究摘要: " + ",".join(sorted(missing)))
    for key, schema in expected.items():
        summary = summaries[key]
        if summary.get("schema_version") != schema:
            raise RuntimeError(f"{key} schema 不匹配: expected={schema}, actual={summary.get('schema_version')}")
        if summary.get("not_authorization") is not True:
            raise RuntimeError(f"{key} 必须声明 not_authorization=true")
        assert_zero_operation_counts(summary.get("operation_counts") or {}, source=key)


def upstream_summary_checks(summaries: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        key: {
            "schema_version": value.get("schema_version"),
            "not_authorization": value.get("not_authorization") is True,
            "operation_counts_zero": True,
            "sample_count": len(value.get("samples", [])) if isinstance(value.get("samples"), list) else 0,
        }
        for key, value in summaries.items()
    }


def missing_evidence(
    *,
    portfolio_metrics: pd.DataFrame,
    turnover_cost_analysis: pd.DataFrame,
    capacity_liquidity_analysis: pd.DataFrame,
    risk_exposure: pd.DataFrame,
    performance_attribution: pd.DataFrame,
    candidate_portfolios: Sequence[str],
) -> tuple[str, ...]:
    required = {
        "portfolio_metrics": (portfolio_metrics, {"trade_date", "portfolio_id", "gross_return", "turnover", "sample_id"}),
        "turnover_cost_analysis": (turnover_cost_analysis, {"trade_date", "portfolio_id", "cost_bps", "net_return", "sample_id"}),
        "capacity_liquidity_analysis": (
            capacity_liquidity_analysis,
            {"trade_date", "portfolio_id", "max_single_name_weight", "capacity_status", "sample_id"},
        ),
        "risk_exposure": (risk_exposure, {"trade_date", "portfolio_id", "risk_factor", "weighted_exposure", "sample_id"}),
        "performance_attribution": (
            performance_attribution,
            {"trade_date", "portfolio_id", "risk_factor", "attribution_proxy", "sample_id"},
        ),
    }
    missing: list[str] = []
    for name, (frame, columns) in required.items():
        if frame.empty:
            missing.append(f"{name}:empty")
            continue
        absent = columns - set(frame.columns)
        if absent:
            missing.append(f"{name}:missing_columns:{','.join(sorted(absent))}")
    if missing:
        return tuple(missing)

    target = portfolio_metrics.loc[portfolio_metrics["portfolio_id"].astype(str).isin(set(candidate_portfolios))]
    if target.empty:
        missing.append("portfolio_metrics:no_candidate_portfolio_rows")
        return tuple(missing)
    pairs = set(tuple(item) for item in target[["sample_id", "portfolio_id"]].astype(str).drop_duplicates().to_numpy())
    cost25 = turnover_cost_analysis.loc[pd.to_numeric(turnover_cost_analysis["cost_bps"], errors="coerce") == 25.0]
    for sample_id, portfolio_id in sorted(pairs):
        checks = {
            "turnover_cost_analysis:missing_25bps": cost25,
            "capacity_liquidity_analysis:missing_portfolio_sample": capacity_liquidity_analysis,
            "risk_exposure:missing_portfolio_sample": risk_exposure,
            "performance_attribution:missing_portfolio_sample": performance_attribution,
        }
        for label, frame in checks.items():
            subset = frame.loc[(frame["sample_id"].astype(str) == sample_id) & (frame["portfolio_id"].astype(str) == portfolio_id)]
            if subset.empty:
                missing.append(f"{label}:{sample_id}:{portfolio_id}")
    return tuple(missing)


def filter_capacity_passing_candidates(
    candidates: Sequence[StrategyCandidate],
    capacity_liquidity_analysis: pd.DataFrame,
) -> tuple[list[StrategyCandidate], list[str]]:
    if capacity_liquidity_analysis.empty or "capacity_status" not in capacity_liquidity_analysis.columns:
        return list(candidates), []
    kept: list[StrategyCandidate] = []
    excluded: list[str] = []
    for candidate in candidates:
        cap = capacity_liquidity_analysis.loc[capacity_liquidity_analysis["portfolio_id"].astype(str) == candidate.source_portfolio_id]
        if cap.empty or bool((cap["capacity_status"].astype(str) != "PASS").any()):
            excluded.append(candidate.source_portfolio_id)
            continue
        kept.append(candidate)
    return kept, excluded


def blocked_missing_evidence_result(
    run_id: str,
    missing: Sequence[str],
    *,
    input_refs: Mapping[str, str] | None = None,
) -> StrategyResearchResult:
    reason = {
        "code": "CR039_BLOCKED_MISSING_EVIDENCE",
        "severity": "blocker",
        "message": "缺少 CR-038 成本、容量、风险暴露或归因证据，策略准入 fail-closed。",
        "missing": list(missing),
    }
    package = {
        "schema_version": STRATEGY_ADMISSION_PACKAGE_SCHEMA,
        "run_id": run_id,
        "status": "BLOCKED",
        "overall_admission": "blocked_missing_evidence",
        "not_authorization": True,
        "strategy_candidates": [],
        "blocked_reasons": [reason],
        "allowed_claims": allowed_claims(run_id),
        "blocked_claims": blocked_claims(run_id),
        "unlock_conditions": unlock_conditions(),
        "input_refs": dict(input_refs or {}),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    return StrategyResearchResult(
        run_id=run_id,
        status="BLOCKED",
        strategy_candidates=(),
        strategy_scores=pd.DataFrame(),
        backtest_results=pd.DataFrame(),
        factor_contribution=pd.DataFrame(),
        risk_cost_summary=pd.DataFrame(),
        admission_package=package,
        blocked_reasons=(reason,),
        operation_counts=dict(FORBIDDEN_OPERATION_COUNTS),
    )


def build_strategy_candidates(payload: Mapping[str, Any]) -> list[StrategyCandidate]:
    by_portfolio: dict[str, list[Mapping[str, Any]]] = {}
    for sample in payload.get("samples", []):
        if not isinstance(sample, Mapping):
            continue
        for row in sample.get("portfolio_admission_summary", []):
            if not isinstance(row, Mapping):
                continue
            portfolio_id = str(row.get("portfolio_id", ""))
            if portfolio_id:
                by_portfolio.setdefault(portfolio_id, []).append(row)

    candidates: list[StrategyCandidate] = []
    for portfolio_id, rows in sorted(by_portfolio.items()):
        net_values = [_safe_float(row.get("net_mean_return_25bps"), default=0.0) for row in rows]
        turnover_values = [_safe_float(row.get("mean_turnover"), default=0.0) for row in rows]
        drawdowns = [_safe_float(row.get("max_drawdown_proxy"), default=0.0) for row in rows]
        upstream_simulation = any(bool(row.get("simulation_candidate")) for row in rows)
        capacity_ok = all(str(row.get("capacity_evidence", "")) == "proxy_available" for row in rows)
        upstream_research = all(str(row.get("admission", "")).startswith("research") for row in rows)
        mean_net = float(np.mean(net_values)) if net_values else 0.0
        admission = "research_baseline" if upstream_research and capacity_ok and mean_net > 0 else "watch"
        candidates.append(
            StrategyCandidate(
                strategy_id=f"strategy_{portfolio_id}",
                source_portfolio_id=portfolio_id,
                admission=admission,
                simulation_candidate=False if not upstream_simulation else admission == "simulation_candidate",
                evidence_status="complete",
                mean_net_return_25bps=mean_net,
                mean_turnover=float(np.mean(turnover_values)) if turnover_values else 0.0,
                max_drawdown_proxy=float(min(drawdowns)) if drawdowns else 0.0,
                capacity_evidence="proxy_available" if capacity_ok else "missing",
                reason=(
                    "CR-038 未给出 simulation_candidate，只能作为研究基线。"
                    if not upstream_simulation
                    else "上游存在 simulation_candidate，但仍需后续交易 CR 单独授权。"
                ),
            )
        )
    return candidates[:3]


def build_backtest_results(portfolio_metrics: pd.DataFrame, turnover_cost_analysis: pd.DataFrame) -> pd.DataFrame:
    costs = turnover_cost_analysis.loc[pd.to_numeric(turnover_cost_analysis["cost_bps"], errors="coerce") == 25.0].copy()
    cols = ["trade_date", "portfolio_id", "sample_id", "net_return", "cost_drag", "cum_net_return"]
    work = portfolio_metrics.merge(costs[cols], on=["trade_date", "portfolio_id", "sample_id"], how="left")
    work["strategy_id"] = work["portfolio_id"].map(lambda value: f"strategy_{value}")
    work["evaluation_window"] = work.apply(_evaluation_window, axis=1)
    work["schema_version"] = BACKTEST_RESULT_SCHEMA
    if "cum_net_return" not in work or work["cum_net_return"].isna().all():
        work["cum_net_return"] = work.groupby("strategy_id")["net_return"].transform(lambda s: (1.0 + s.fillna(0.0)).cumprod() - 1.0)
    return work[
        [
            "schema_version",
            "trade_date",
            "sample_id",
            "evaluation_window",
            "strategy_id",
            "portfolio_id",
            "gross_return",
            "net_return",
            "turnover",
            "cost_drag",
            "cum_gross_return",
            "cum_net_return",
            "holding_count",
            "max_weight",
        ]
    ]


def build_risk_cost_summary(
    backtest_results: pd.DataFrame,
    capacity_liquidity_analysis: pd.DataFrame,
    risk_exposure: pd.DataFrame,
    candidates: Sequence[StrategyCandidate],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    candidate_map = {item.source_portfolio_id: item for item in candidates}
    capacity = capacity_liquidity_analysis.groupby(["sample_id", "portfolio_id"]).agg(
        max_single_name_weight=("max_single_name_weight", "max"),
        max_low_liquidity_proxy_weight=("low_liquidity_proxy_weight", "max"),
        max_small_cap_proxy_weight=("small_cap_proxy_weight", "max"),
        capacity_watch_count=("capacity_status", lambda s: int((s != "PASS").sum())),
    )
    risk = risk_exposure.groupby(["sample_id", "portfolio_id"]).agg(
        max_abs_weighted_exposure=("weighted_exposure", lambda s: float(pd.to_numeric(s, errors="coerce").abs().max())),
        mean_abs_weighted_exposure=("weighted_exposure", lambda s: float(pd.to_numeric(s, errors="coerce").abs().mean())),
        risk_factor_count=("risk_factor", "nunique"),
    )
    for (sample_id, portfolio_id, window), group in backtest_results.groupby(["sample_id", "portfolio_id", "evaluation_window"], sort=True):
        cap = capacity.loc[(sample_id, portfolio_id)] if (sample_id, portfolio_id) in capacity.index else None
        risk_row = risk.loc[(sample_id, portfolio_id)] if (sample_id, portfolio_id) in risk.index else None
        candidate = candidate_map.get(str(portfolio_id))
        rows.append(
            {
                "schema_version": RISK_COST_SCHEMA,
                "sample_id": sample_id,
                "evaluation_window": window,
                "strategy_id": f"strategy_{portfolio_id}",
                "portfolio_id": portfolio_id,
                "admission": "" if candidate is None else candidate.admission,
                "simulation_candidate": False,
                "mean_gross_return": _safe_float(group["gross_return"].mean(), default=0.0),
                "mean_net_return_25bps": _safe_float(group["net_return"].mean(), default=0.0),
                "mean_turnover": _safe_float(group["turnover"].mean(), default=0.0),
                "max_drawdown_proxy": _max_drawdown(group["net_return"]),
                "max_single_name_weight": None if cap is None else float(cap["max_single_name_weight"]),
                "max_low_liquidity_proxy_weight": None if cap is None else float(cap["max_low_liquidity_proxy_weight"]),
                "max_small_cap_proxy_weight": None if cap is None else float(cap["max_small_cap_proxy_weight"]),
                "capacity_watch_count": None if cap is None else int(cap["capacity_watch_count"]),
                "max_abs_weighted_exposure": None if risk_row is None else float(risk_row["max_abs_weighted_exposure"]),
                "mean_abs_weighted_exposure": None if risk_row is None else float(risk_row["mean_abs_weighted_exposure"]),
                "risk_factor_count": None if risk_row is None else int(risk_row["risk_factor_count"]),
            }
        )
    return pd.DataFrame(rows)


def build_factor_contribution(performance_attribution: pd.DataFrame, *, candidate_portfolios: set[str]) -> pd.DataFrame:
    work = performance_attribution.loc[performance_attribution["portfolio_id"].astype(str).isin(candidate_portfolios)].copy()
    grouped = work.groupby(["sample_id", "portfolio_id", "risk_factor"], sort=True).agg(
        mean_weighted_exposure=("weighted_exposure", "mean"),
        mean_attribution_proxy=("attribution_proxy", "mean"),
        absolute_attribution_proxy=("attribution_proxy", lambda s: float(pd.to_numeric(s, errors="coerce").abs().mean())),
        observations=("trade_date", "count"),
    )
    out = grouped.reset_index()
    out["schema_version"] = FACTOR_CONTRIBUTION_SCHEMA
    out["strategy_id"] = out["portfolio_id"].map(lambda value: f"strategy_{value}")
    return out[
        [
            "schema_version",
            "sample_id",
            "strategy_id",
            "portfolio_id",
            "risk_factor",
            "mean_weighted_exposure",
            "mean_attribution_proxy",
            "absolute_attribution_proxy",
            "observations",
        ]
    ]


def build_strategy_scores(alpha_scores: pd.DataFrame, candidates: Sequence[StrategyCandidate]) -> pd.DataFrame:
    if alpha_scores.empty or not candidates:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for candidate in candidates:
        frame = alpha_scores.copy()
        frame["schema_version"] = STRATEGY_SCORE_SCHEMA
        frame["strategy_id"] = candidate.strategy_id
        frame["source_portfolio_id"] = candidate.source_portfolio_id
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    preferred = [
        "schema_version",
        "run_id",
        "sample_id",
        "trade_date",
        "symbol",
        "strategy_id",
        "source_portfolio_id",
        "alpha_score",
        "source_admission",
    ]
    return out[[col for col in preferred if col in out.columns]]


def refine_candidate_admissions(candidates: Sequence[StrategyCandidate], risk_cost_summary: pd.DataFrame) -> list[StrategyCandidate]:
    refined: list[StrategyCandidate] = []
    for candidate in candidates:
        rows = risk_cost_summary.loc[risk_cost_summary["strategy_id"] == candidate.strategy_id]
        windows = set(rows["evaluation_window"].dropna().astype(str))
        has_all_windows = {"in_sample_2000_2014", "validation_2015_2019", "out_of_sample_2020_2026_ytd"} <= windows
        positive_windows = bool((pd.to_numeric(rows["mean_net_return_25bps"], errors="coerce") > 0).all()) if not rows.empty else False
        admission = candidate.admission
        reason = candidate.reason
        if not has_all_windows:
            admission = "watch"
            reason = "缺少样本内、验证期或 2020-2026 YTD 任一窗口证据，只能观察。"
        elif candidate.admission == "research_baseline" and not positive_windows:
            admission = "watch"
            reason = "至少一个评估窗口成本后收益不为正，只能观察。"
        refined.append(
            StrategyCandidate(
                strategy_id=candidate.strategy_id,
                source_portfolio_id=candidate.source_portfolio_id,
                admission=admission,
                simulation_candidate=False,
                evidence_status=candidate.evidence_status,
                mean_net_return_25bps=candidate.mean_net_return_25bps,
                mean_turnover=candidate.mean_turnover,
                max_drawdown_proxy=candidate.max_drawdown_proxy,
                capacity_evidence=candidate.capacity_evidence,
                reason=reason,
            )
        )
    return refined


def build_strategy_admission_package(
    *,
    run_id: str,
    candidates: Sequence[StrategyCandidate],
    upstream_research_summaries: Mapping[str, Mapping[str, Any]],
    portfolio_admission_payload: Mapping[str, Any],
    risk_cost_summary: pd.DataFrame,
    input_refs: Mapping[str, str],
) -> dict[str, Any]:
    overall = "research_baseline" if any(item.admission == "research_baseline" for item in candidates) else "watch"
    return {
        "schema_version": STRATEGY_ADMISSION_PACKAGE_SCHEMA,
        "run_id": run_id,
        "status": "PASS",
        "overall_admission": overall,
        "not_authorization": True,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "strategy_candidates": [candidate.to_dict() for candidate in candidates],
        "sample_windows": sorted(risk_cost_summary["evaluation_window"].dropna().astype(str).unique().tolist()),
        "allowed_claims": allowed_claims(run_id),
        "blocked_claims": blocked_claims(run_id),
        "unlock_conditions": unlock_conditions(),
        "upstream_summary_checks": upstream_summary_checks(upstream_research_summaries),
        "cr037_cr038_gate_summary": cr037_cr038_gate_summary(portfolio_admission_payload),
        "input_refs": dict(input_refs),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def cr037_cr038_gate_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    allowed: set[str] = set()
    watch: set[str] = set()
    rejected: set[str] = set()
    upstream_simulation_candidate = False
    for sample in payload.get("samples", []):
        if not isinstance(sample, Mapping):
            continue
        for asset in sample.get("allowed_assets", []):
            if isinstance(asset, Mapping) and asset.get("asset_id"):
                allowed.add(str(asset["asset_id"]))
        for asset in sample.get("watch_assets_policy", []):
            if isinstance(asset, Mapping) and asset.get("asset_id"):
                watch.add(str(asset["asset_id"]))
        for asset in sample.get("rejected_assets_excluded", []):
            if isinstance(asset, Mapping) and asset.get("asset_id"):
                rejected.add(str(asset["asset_id"]))
        for row in sample.get("portfolio_admission_summary", []):
            if isinstance(row, Mapping):
                upstream_simulation_candidate = upstream_simulation_candidate or bool(row.get("simulation_candidate"))
    return {
        "allowed_assets": sorted(allowed),
        "watch_assets_policy": sorted(watch),
        "rejected_assets_excluded": sorted(rejected),
        "upstream_simulation_candidate": upstream_simulation_candidate,
        "policy": "只消费 CR-037 baseline/candidate；watch 只能观察；reject/缺证 fail-closed。",
    }


def allowed_claims(run_id: str) -> list[dict[str, str]]:
    return [
        {
            "claim": "research_baseline_candidate",
            "status": "allowed",
            "reason": "仅允许作为本地离线研究候选和后续人工决策输入。",
            "evidence_ref": run_id,
        }
    ]


def blocked_claims(run_id: str) -> list[dict[str, str]]:
    reasons = {
        "qmt_ready": "CR-039 不连接 QMT，不查询账户，不发单或撤单。",
        "simulation_ready": "CR-039 只形成研究输入；simulation 必须另起 CR 并取得运行授权。",
        "live_ready": "CR-039 不构成 live 或 small-live 准入。",
        "production_valid": "CR-039 输出不等于 production-valid 或实盘可用证据。",
        "account_or_order_ready": "CR-039 不授权账户、订单、撤单或 broker runtime。",
        "provider_or_lake_publish_ready": "CR-039 不触发 provider fetch、lake write 或 catalog publish。",
    }
    return [{"claim": claim, "status": "blocked", "reason": reasons[claim], "evidence_ref": run_id} for claim in RUNTIME_CLAIMS]


def unlock_conditions() -> list[str]:
    return [
        "如需 simulation，另起 CR-021 或后续 simulation 准入 CR。",
        "后续 CR 必须重新取得账户、订单、资金、标的范围、时间窗口和回滚策略授权。",
        "后续 CR 必须复核 QMT gateway / simulation runtime 和 broker lake 边界。",
    ]


def _evaluation_window(row: Mapping[str, Any]) -> str:
    sample_id = str(row.get("sample_id", ""))
    if "2020_2026" in sample_id or "observation" in sample_id:
        return "out_of_sample_2020_2026_ytd"
    trade_date = pd.to_datetime(row.get("trade_date"), errors="coerce")
    if pd.notna(trade_date) and int(trade_date.year) >= 2015:
        return "validation_2015_2019"
    return "in_sample_2000_2014"


def _max_drawdown(returns: pd.Series) -> float:
    curve = (1.0 + pd.to_numeric(returns, errors="coerce").fillna(0.0)).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    return float(drawdown.min()) if not drawdown.empty else 0.0


def _safe_float(value: Any, default: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        if default is None:
            return float("nan")
        return default
    if pd.isna(number):
        if default is None:
            return float("nan")
        return default
    return number
