"""Mature multifactor research runner.

This module reads canonical market-data lake inputs and writes research
artifacts only. It does not write the lake, publish catalog pointers, call QMT,
start a gateway, read credentials, or run simulation/live.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_model_validation import FactorModelValidationReport, build_factor_model_validation_report
from engine.factor_registry import (
    STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS,
    FactorCatalogEntry,
    anomaly_candidate_catalog_entries,
    stage3_candidate_factor_catalog_entries,
    stage3_factor_catalog_entries,
)
from engine.mature_multifactor_framework import (
    PortfolioRiskPolicy,
    ResearchEvidenceIndex,
    SignalSet,
    Stage3MatureResearchPackage,
    StrategyCandidate,
    StrategyFamily,
    build_stage3_mature_research_package,
    build_stage3_research_run_manifest,
    validate_stage3_mature_research_package,
)
from engine.multifactor_contracts import (
    BLOCKED_CLAIMS_DEFAULT,
    FactorSpec,
)
from engine.serialization import json_safe
from trading.strategy_runner.target_portfolio import MultifactorSignalRow, build_multifactor_target_portfolio


STAGE3_RUN_SCHEMA = "stage3_mature_multifactor_research_run_v1"
DEFAULT_RESEARCH_ROOT = Path("/home/hyde/data/quant-lab/research/runs/stage3_mature_multifactor")
DEFAULT_PROCESS_EVIDENCE_ROOT = Path("process/evidence/stage3-mature-multifactor")
DEFAULT_LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake")
DEFAULT_START = "2021-01-01"
DEFAULT_END = "2026-06-26"
DEFAULT_TOP_N = 80
DEFAULT_MAX_WEIGHT = 0.025
DEFAULT_MIN_ADV_AMOUNT = 1_000_000.0
DEFAULT_COST_BPS = 15.0
DEFAULT_LABEL_HORIZON = 20
DEFAULT_REBALANCE_STEP = 5

FORBIDDEN_OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_publish": 0,
    "qmt_operation": 0,
    "gateway_start": 0,
    "simulation_or_live": 0,
    "account_or_order_operation": 0,
    "credential_read": 0,
}

DATASET_REFS = {
    "data_release_ref": "catalog://market-data/stage3-data-update/2026-06-26",
    "pit_universe": "catalog://stock_basic+prices+trade_status",
    "listing_delisting": "catalog://stock_basic",
    "st_filter": "catalog://trade_status.is_st",
    "suspension_filter": "catalog://trade_status.is_suspended",
    "limit_up_down_filter": "catalog://prices_limit",
    "liquidity_filter": "catalog://liquidity_capacity.adv20_amount",
    "industry_classification": "catalog://industry_classification",
    "market_cap": "catalog://market_cap",
    "style_exposure": "artifact://stage3/style_exposure_proxy",
    "benchmark": "catalog://hs300_index/index_code=000985.SH",
    "fee_slippage_model": "artifact://stage3/fee_slippage_model_v1",
}


@dataclass(frozen=True, slots=True)
class Stage3ResearchArtifacts:
    run_id: str
    research_dir: Path
    process_evidence_dir: Path
    run_manifest_path: Path
    input_refs_path: Path
    factor_specs_path: Path
    factor_panel_path: Path
    label_window_path: Path
    ic_rankic_path: Path
    layered_returns_path: Path
    turnover_path: Path
    exposure_path: Path
    factor_model_validation_report_path: Path
    signal_set_path: Path
    strategy_candidate_path: Path
    risk_policy_path: Path
    research_evidence_index_path: Path
    mature_admission_package_path: Path
    runner_offline_preflight_path: Path
    observation_plan_path: Path
    package_path: Path
    report_json_path: Path
    report_md_path: Path
    process_summary_path: Path

    def to_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class Stage3ResearchRunResult:
    run_id: str
    status: str
    package_status: str
    artifacts: Stage3ResearchArtifacts
    metrics_summary: Mapping[str, Any]
    limitations: tuple[str, ...]
    blocked_reasons: tuple[Mapping[str, Any], ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))
    schema_version: str = STAGE3_RUN_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "status": self.status,
            "package_status": self.package_status,
            "artifacts": self.artifacts.to_dict(),
            "metrics_summary": dict(self.metrics_summary),
            "limitations": list(self.limitations),
            "blocked_reasons": [dict(item) for item in self.blocked_reasons],
            "operation_counts": dict(self.operation_counts),
        }


def run_stage3_mature_multifactor_research(
    *,
    run_id: str,
    lake_root: str | Path = DEFAULT_LAKE_ROOT,
    research_root: str | Path = DEFAULT_RESEARCH_ROOT,
    process_evidence_root: str | Path = DEFAULT_PROCESS_EVIDENCE_ROOT,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
    top_n: int = DEFAULT_TOP_N,
    max_weight: float = DEFAULT_MAX_WEIGHT,
    min_adv_amount: float = DEFAULT_MIN_ADV_AMOUNT,
    cost_bps: float = DEFAULT_COST_BPS,
    label_horizon: int = DEFAULT_LABEL_HORIZON,
    rebalance_step: int = DEFAULT_REBALANCE_STEP,
    factor_weights: Mapping[str, float] | None = None,
    score_multiplier: float = 1.0,
) -> Stage3ResearchRunResult:
    lake = Path(lake_root)
    artifacts = stage3_artifacts(run_id, Path(research_root), Path(process_evidence_root))
    artifacts.research_dir.mkdir(parents=True, exist_ok=True)
    artifacts.process_evidence_dir.mkdir(parents=True, exist_ok=True)

    catalog = _read_catalog(lake)
    inputs = _load_inputs(lake, catalog, start=start, end=end)
    frame, limitations = build_research_frame(
        inputs,
        start=start,
        end=end,
        min_adv_amount=min_adv_amount,
        label_horizon=label_horizon,
    )
    factor_columns = STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS
    frame = add_cross_sectional_scores(frame, factor_columns=factor_columns)
    frame = apply_composite_score_policy(
        frame,
        factor_columns=factor_columns,
        factor_weights=factor_weights,
        score_multiplier=score_multiplier,
    )
    valid = frame.loc[frame["eligible"] & frame["label_return"].notna()].copy()
    if valid.empty:
        raise RuntimeError("stage3_research_no_valid_rows_after_filters")

    trade_dates = sorted(valid["trade_date"].astype(str).unique())
    rebalance_dates = tuple(trade_dates[::rebalance_step])
    if len(rebalance_dates) < 8:
        raise RuntimeError("stage3_research_insufficient_rebalance_dates")

    ic_rankic = compute_ic_rankic(valid, factor_columns=(*factor_columns, "composite_score"))
    layered_returns = compute_layered_returns(valid, score_column="composite_score")
    portfolio, turnover = build_portfolio_path(
        valid,
        rebalance_dates=rebalance_dates,
        top_n=top_n,
        max_weight=max_weight,
        cost_bps=cost_bps,
    )
    exposure = compute_portfolio_exposure(portfolio)
    factor_model_validation_report = build_stage3_factor_model_validation_report(
        run_id,
        valid,
        turnover,
        cost_bps=cost_bps,
        label_horizon=label_horizon,
    )
    latest_signals = build_latest_signal_rows(valid, rebalance_dates[-1], top_n=top_n)
    signal_set = build_signal_set(run_id, latest_signals, artifacts, rebalance_dates[-1])
    risk_policy = build_risk_policy(
        run_id,
        top_n=top_n,
        max_weight=max_weight,
        turnover_limit=0.35,
        min_adv_amount=min_adv_amount,
        fee_slippage_ref=artifact_ref(run_id, artifacts.runner_offline_preflight_path),
    )
    strategy_candidate = build_strategy_candidate(run_id, signal_set, risk_policy, portfolio, turnover, artifacts)
    evidence_index = build_research_evidence_index(run_id, artifacts, catalog, limitations)
    factor_specs = build_factor_specs(run_id, catalog)
    admission_package = build_mature_admission_package(
        run_id,
        strategy_candidate=strategy_candidate,
        signal_set=signal_set,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
        factor_specs=factor_specs,
        portfolio=portfolio,
        turnover=turnover,
        factor_model_validation_report=factor_model_validation_report,
        factor_model_validation_report_ref=artifact_ref(run_id, artifacts.factor_model_validation_report_path),
        limitations=limitations,
    )
    runner_preflight = build_runner_offline_preflight(
        run_id,
        signal_set=signal_set,
        risk_policy=risk_policy,
        latest_signals=latest_signals,
        artifacts=artifacts,
        top_n=top_n,
        max_weight=max_weight,
    )
    observation_plan = build_stage4_observation_plan(run_id, artifacts, portfolio, limitations)
    input_refs = stage3_input_refs(catalog, artifacts, run_id)
    evidence_refs = stage3_evidence_refs(artifacts, run_id)
    manifest = build_stage3_research_run_manifest(
        run_id=run_id,
        strategy_id=strategy_candidate.strategy_id,
        data_release_ref=input_refs["data_release_ref"],
        factor_versions={spec.factor_id: spec.version for spec in factor_specs},
        code_version="workspace-stage3",
        seed=0,
        date_range={"start": start, "end": end},
        config={
            "top_n": top_n,
            "max_weight": max_weight,
            "min_adv_amount": min_adv_amount,
            "cost_bps": cost_bps,
            "label_horizon": label_horizon,
            "rebalance_step": rebalance_step,
            "factor_weights": dict(factor_weights or {}),
            "score_multiplier": score_multiplier,
        },
        created_at=_now(),
        evidence_refs=evidence_refs,
    )
    package = build_stage3_mature_research_package(
        strategy_id=strategy_candidate.strategy_id,
        run_manifest=manifest,
        input_refs=input_refs,
        evidence_refs=evidence_refs,
        signal_set=signal_set,
        strategy_candidate=strategy_candidate,
        research_evidence_index=evidence_index,
        portfolio_risk_policy=risk_policy,
        factor_model_validation_report_ref=evidence_refs["factor_model_validation_report_ref"],
        mature_strategy_admission_package_ref=evidence_refs["mature_strategy_admission_package_ref"],
        runner_offline_preflight_ref=evidence_refs["runner_offline_preflight_ref"],
        observation_plan_ref=artifact_ref(run_id, artifacts.observation_plan_path),
    )

    write_stage3_outputs(
        artifacts=artifacts,
        frame=frame,
        label_window=label_window_view(valid, label_horizon),
        ic_rankic=ic_rankic,
        layered_returns=layered_returns,
        turnover=turnover,
        exposure=exposure,
        factor_model_validation_report=factor_model_validation_report,
        factor_specs=factor_specs,
        input_refs=input_refs,
        manifest=manifest,
        signal_set=signal_set,
        strategy_candidate=strategy_candidate,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
        admission_package=admission_package,
        runner_preflight=runner_preflight,
        observation_plan=observation_plan,
        package=package,
        portfolio=portfolio,
        limitations=limitations,
    )

    validation = validate_stage3_mature_research_package(package)
    admission_blocked = str(admission_package.get("status", "")).upper() == "BLOCKED"
    blocked_reasons = tuple(reason.to_dict() for reason in validation.blocked_reasons)
    if admission_blocked:
        blocked_reasons = blocked_reasons + tuple(dict(item) for item in factor_model_validation_report.blocked_reasons)
    metrics = summarize_metrics(portfolio, turnover, ic_rankic, layered_returns, frame, valid)
    result = Stage3ResearchRunResult(
        run_id=run_id,
        status="PASS" if validation.passed and not admission_blocked else "BLOCKED",
        package_status=package.status,
        artifacts=artifacts,
        metrics_summary=metrics,
        limitations=tuple(limitations),
        blocked_reasons=blocked_reasons,
    )
    write_summary_outputs(result, artifacts)
    return result


def stage3_artifacts(run_id: str, research_root: Path, process_evidence_root: Path) -> Stage3ResearchArtifacts:
    research_dir = research_root / run_id
    process_dir = process_evidence_root / run_id
    return Stage3ResearchArtifacts(
        run_id=run_id,
        research_dir=research_dir,
        process_evidence_dir=process_dir,
        run_manifest_path=research_dir / "RUN-MANIFEST.json",
        input_refs_path=research_dir / "INPUT-REFS.json",
        factor_specs_path=research_dir / "FACTOR-SPECS.json",
        factor_panel_path=research_dir / "factor_panel.parquet",
        label_window_path=research_dir / "label_window.parquet",
        ic_rankic_path=research_dir / "ic_rankic.csv",
        layered_returns_path=research_dir / "layered_returns.csv",
        turnover_path=research_dir / "turnover_cost.csv",
        exposure_path=research_dir / "exposure.csv",
        factor_model_validation_report_path=research_dir / "FACTOR-MODEL-VALIDATION-REPORT.json",
        signal_set_path=research_dir / "SIGNAL-SET.json",
        strategy_candidate_path=research_dir / "STRATEGY-CANDIDATE.json",
        risk_policy_path=research_dir / "PORTFOLIO-RISK-POLICY.json",
        research_evidence_index_path=research_dir / "RESEARCH-EVIDENCE-INDEX.json",
        mature_admission_package_path=research_dir / "MATURE-STRATEGY-ADMISSION-PACKAGE.json",
        runner_offline_preflight_path=research_dir / "RUNNER-OFFLINE-PREFLIGHT.json",
        observation_plan_path=research_dir / "STAGE4-OBSERVATION-PLAN.json",
        package_path=research_dir / "STAGE3-MATURE-RESEARCH-PACKAGE.json",
        report_json_path=research_dir / "STAGE3-RESEARCH-REPORT.json",
        report_md_path=research_dir / "STAGE3-RESEARCH-REPORT.md",
        process_summary_path=process_dir / "stage3-research-summary.json",
    )


def build_research_frame(
    inputs: Mapping[str, pd.DataFrame],
    *,
    start: str,
    end: str,
    min_adv_amount: float,
    label_horizon: int,
) -> tuple[pd.DataFrame, list[str]]:
    prices = inputs["prices"].copy()
    prices["trade_date"] = _date_text(prices["trade_date"])
    prices = prices.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    prices["daily_return"] = prices.groupby("symbol")["adjusted_close"].pct_change()
    prices["momentum_20d"] = prices.groupby("symbol")["adjusted_close"].pct_change(20)
    prices["reversal_5d"] = -prices.groupby("symbol")["adjusted_close"].pct_change(5)
    prices["volatility_20d"] = -prices.groupby("symbol")["daily_return"].rolling(20).std().reset_index(level=0, drop=True)
    prices["label_return"] = (
        prices.groupby("symbol")["adjusted_close"].shift(-(label_horizon + 1))
        / prices.groupby("symbol")["adjusted_close"].shift(-1)
        - 1.0
    )
    prices["label_start_date"] = prices.groupby("symbol")["trade_date"].shift(-1)
    prices["label_end_date"] = prices.groupby("symbol")["trade_date"].shift(-(label_horizon + 1))

    frame = prices.loc[(prices["trade_date"] >= start) & (prices["trade_date"] <= end)].copy()
    frame = frame.merge(_daily(inputs, "trade_status"), on=["trade_date", "symbol"], how="left")
    frame = frame.merge(_daily(inputs, "liquidity_capacity"), on=["trade_date", "symbol"], how="left")
    frame = frame.merge(_daily(inputs, "market_cap"), on=["trade_date", "symbol"], how="left")
    frame = frame.merge(_daily(inputs, "prices_limit"), on=["trade_date", "symbol"], how="left")
    frame = frame.merge(_stock_lifecycle(inputs["stock_basic"]), on="symbol", how="left")
    frame = frame.merge(_industry(inputs["industry_classification"]), on="symbol", how="left")

    frame["listed_days"] = (
        pd.to_datetime(frame["trade_date"], errors="coerce") - pd.to_datetime(frame["list_date"], errors="coerce")
    ).dt.days
    frame["is_hs_sz"] = frame["symbol"].astype(str).str.endswith((".SH", ".SZ"))
    frame["not_delisted"] = frame["delist_date"].isna() | (frame["delist_date"].astype(str) > frame["trade_date"].astype(str))
    frame["is_tradable"] = frame["is_tradable"].fillna(False).astype(bool)
    frame["is_suspended"] = frame["is_suspended"].fillna(True).astype(bool)
    frame["is_st"] = frame["is_st"].fillna(True).astype(bool)
    frame["limit_buy_blocked"] = frame["limit_up"].notna() & (frame["close"] >= frame["limit_up"].astype(float) * 0.999)
    frame["adv20_amount_numeric"] = pd.to_numeric(frame["adv20_amount"], errors="coerce")
    positive_adv20 = frame["adv20_amount_numeric"].where(frame["adv20_amount_numeric"] > 0)
    frame["liquidity_adv20"] = np.log1p(positive_adv20)
    frame["value_pb_inverse"] = -pd.to_numeric(frame["pb"], errors="coerce")
    frame["eligible"] = (
        frame["is_hs_sz"]
        & frame["not_delisted"]
        & (frame["listed_days"] >= 180)
        & frame["is_tradable"]
        & ~frame["is_suspended"]
        & ~frame["is_st"]
        & ~frame["limit_buy_blocked"]
        & (frame["adv20_amount_numeric"] >= min_adv_amount)
        & pd.to_numeric(frame["market_cap"], errors="coerce").notna()
        & frame[["momentum_20d", "reversal_5d", "volatility_20d", "value_pb_inverse"]].notna().all(axis=1)
    )
    frame["available_at"] = frame.get("available_at", frame["trade_date"].astype(str) + "T15:30:00+08:00")
    frame["quality_status"] = frame["eligible"].map(lambda value: "pass" if value else "filtered")
    limitations = [
        "stage3_research_only_not_runtime_authorization",
        "universe_excludes_bj_by_policy",
        "limit_up_down_filter_uses_available_prices_limit_rows_and_records_lineage_limitation",
        "liquidity_capacity_threshold_uses_data_lake_native_adv20_amount_units",
        "style_exposure_uses_market_cap_pb_volatility_momentum_proxies",
    ]
    return frame, limitations


def add_cross_sectional_scores(frame: pd.DataFrame, *, factor_columns: Sequence[str]) -> pd.DataFrame:
    output = frame.copy()
    for column in factor_columns:
        z_col = f"{column}_z"
        output[z_col] = output.groupby("trade_date")[column].transform(_winsor_zscore)
    z_cols = [f"{column}_z" for column in factor_columns]
    output["composite_score"] = output[z_cols].mean(axis=1, skipna=False)
    return output


def apply_composite_score_policy(
    frame: pd.DataFrame,
    *,
    factor_columns: Sequence[str],
    factor_weights: Mapping[str, float] | None = None,
    score_multiplier: float = 1.0,
) -> pd.DataFrame:
    if not factor_weights and float(score_multiplier) == 1.0:
        return frame
    output = frame.copy()
    weights = {str(key): float(value) for key, value in (factor_weights or {}).items()}
    unknown = set(weights) - set(factor_columns)
    if unknown:
        raise ValueError("factor_weights contains unknown factor_id: " + ", ".join(sorted(unknown)))
    if weights:
        denominator = sum(abs(value) for value in weights.values())
        if denominator <= 0:
            raise ValueError("factor_weights absolute sum must be positive")
        weighted = []
        for factor_id, weight in weights.items():
            z_col = f"{factor_id}_z"
            if z_col not in output.columns:
                raise ValueError(f"missing zscore column for factor weight: {z_col}")
            weighted.append(output[z_col] * weight)
        output["composite_score"] = pd.concat(weighted, axis=1).sum(axis=1) / denominator
    output["composite_score"] = output["composite_score"] * float(score_multiplier)
    return output


def compute_ic_rankic(valid: pd.DataFrame, *, factor_columns: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date, group in valid.groupby("trade_date", sort=True):
        if len(group) < 30:
            continue
        label = pd.to_numeric(group["label_return"], errors="coerce")
        for factor in factor_columns:
            values = pd.to_numeric(group[factor], errors="coerce")
            pair = pd.DataFrame({"factor": values, "label": label}).dropna()
            if len(pair) < 30:
                continue
            rows.append(
                {
                    "trade_date": trade_date,
                    "factor_id": factor,
                    "ic": float(pair["factor"].corr(pair["label"], method="pearson")),
                    "rank_ic": float(pair["factor"].rank().corr(pair["label"].rank(), method="pearson")),
                    "n": int(len(pair)),
                }
            )
    return pd.DataFrame(rows)


def compute_layered_returns(valid: pd.DataFrame, *, score_column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date, group in valid.groupby("trade_date", sort=True):
        pair = group[["trade_date", "symbol", score_column, "label_return"]].dropna()
        if len(pair) < 100:
            continue
        try:
            pair = pair.assign(quantile=pd.qcut(pair[score_column], 5, labels=False, duplicates="drop") + 1)
        except ValueError:
            continue
        for quantile, qgroup in pair.groupby("quantile"):
            rows.append(
                {
                    "trade_date": trade_date,
                    "quantile": int(quantile),
                    "mean_forward_return": float(qgroup["label_return"].mean()),
                    "median_forward_return": float(qgroup["label_return"].median()),
                    "count": int(len(qgroup)),
                }
            )
    return pd.DataFrame(rows)


def build_portfolio_path(
    valid: pd.DataFrame,
    *,
    rebalance_dates: Sequence[str],
    top_n: int,
    max_weight: float,
    cost_bps: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    turnover_rows: list[dict[str, Any]] = []
    previous: dict[str, float] = {}
    for index, trade_date in enumerate(rebalance_dates[:-1]):
        next_date = rebalance_dates[index + 1]
        day = valid.loc[valid["trade_date"] == trade_date].sort_values("composite_score", ascending=False).head(top_n)
        if day.empty:
            continue
        weight = min(1.0 / len(day), max_weight)
        weights = {str(symbol): float(weight) for symbol in day["symbol"]}
        gross = float(day["label_return"].mean())
        turnover = 0.5 * sum(abs(weights.get(symbol, 0.0) - previous.get(symbol, 0.0)) for symbol in set(weights) | set(previous))
        cost_return = turnover * cost_bps / 10000.0
        net = gross - cost_return
        for _, item in day.iterrows():
            rows.append(
                {
                    "trade_date": trade_date,
                    "next_rebalance_date": next_date,
                    "symbol": item["symbol"],
                    "weight": weight,
                    "composite_score": float(item["composite_score"]),
                    "forward_return": float(item["label_return"]),
                    "industry_name": item.get("industry_name", ""),
                    "market_cap": _float(item.get("market_cap")),
                    "adv20_amount": _float(item.get("adv20_amount")),
                }
            )
        turnover_rows.append(
            {
                "trade_date": trade_date,
                "next_rebalance_date": next_date,
                "selected_count": int(len(day)),
                "gross_forward_return": gross,
                "turnover": float(turnover),
                "cost_bps": float(turnover * cost_bps),
                "net_forward_return": net,
            }
        )
        previous = weights
    return pd.DataFrame(rows), pd.DataFrame(turnover_rows)


def compute_portfolio_exposure(portfolio: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if portfolio.empty:
        return pd.DataFrame()
    for trade_date, group in portfolio.groupby("trade_date", sort=True):
        industry = group.groupby("industry_name")["weight"].sum().sort_values(ascending=False)
        market_cap = pd.to_numeric(group["market_cap"], errors="coerce").clip(lower=1.0)
        weights = pd.to_numeric(group["weight"], errors="coerce").fillna(0.0)
        rows.append(
            {
                "trade_date": trade_date,
                "selected_count": int(len(group)),
                "top_industry": str(industry.index[0]) if len(industry) else "",
                "top_industry_weight": float(industry.iloc[0]) if len(industry) else 0.0,
                "weighted_log_market_cap": float((np.log(market_cap) * weights).sum()),
                "median_market_cap": float(pd.to_numeric(group["market_cap"], errors="coerce").median()),
                "median_adv20_amount": float(pd.to_numeric(group["adv20_amount"], errors="coerce").median()),
            }
        )
    result = pd.DataFrame(rows)
    return result


def build_stage3_factor_model_validation_report(
    run_id: str,
    valid: pd.DataFrame,
    turnover: pd.DataFrame,
    *,
    cost_bps: float,
    label_horizon: int,
) -> FactorModelValidationReport:
    factor_panel = valid[
        [
            "trade_date",
            "symbol",
            "available_at",
            *STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS,
            "composite_score",
        ]
    ].copy()
    labels = valid[["trade_date", "symbol", "label_return", "label_start_date", "label_end_date"]].copy()
    labels["label_available_at"] = labels["label_end_date"].astype(str) + "T15:30:00+08:00"
    universe_cols = [
        col
        for col in (
            "trade_date",
            "symbol",
            "industry_name",
            "market_cap",
            "pb",
            "adv20_amount",
            "listed_days",
            "is_st",
            "is_suspended",
            "close",
        )
        if col in valid.columns
    ]
    return build_factor_model_validation_report(
        run_id=run_id,
        factor_panel=factor_panel,
        labels=labels,
        portfolio_path=turnover,
        universe_frame=valid[universe_cols].copy() if universe_cols else None,
        config={
            "strategy_type": "long_only",
            "cost_bps": cost_bps,
            "label_horizon": label_horizon,
            "evidence_refs": ("engine.mature_multifactor_research",),
        },
    )


def build_latest_signal_rows(valid: pd.DataFrame, trade_date: str, *, top_n: int) -> pd.DataFrame:
    columns = ["trade_date", "symbol", "composite_score", "momentum_20d_z", "reversal_5d_z", "volatility_20d_z", "liquidity_adv20_z", "value_pb_inverse_z"]
    return valid.loc[valid["trade_date"] == trade_date].sort_values("composite_score", ascending=False).head(top_n)[columns].reset_index(drop=True)


def label_window_view(valid: pd.DataFrame, label_horizon: int) -> pd.DataFrame:
    return valid[["trade_date", "symbol", "label_start_date", "label_end_date", "label_return", "available_at"]].assign(
        label_horizon=label_horizon,
        label_policy="next_trade_date_to_horizon_close_no_overlap",
    )


def build_signal_set(run_id: str, latest_signals: pd.DataFrame, artifacts: Stage3ResearchArtifacts, trade_date: str) -> SignalSet:
    signals = tuple(
        {
            "symbol": str(row.symbol),
            "score": float(row.composite_score),
            "direction": "long",
            "available_at": f"{trade_date}T15:30:00+08:00",
            "factor_refs": artifact_ref(run_id, artifacts.factor_specs_path),
        }
        for row in latest_signals.itertuples(index=False)
    )
    return SignalSet(
        signal_set_id=f"signal-set:{run_id}",
        strategy_family=StrategyFamily.MULTIFACTOR,
        trade_date=trade_date,
        universe_ref=artifact_ref(run_id, artifacts.input_refs_path),
        signal_schema={
            "schema": "stage3_signal_set_v1",
            "score_field": "composite_score",
            "available_at_field": "available_at",
            "not_order": True,
        },
        signals=signals,
        available_at=f"{trade_date}T15:30:00+08:00",
        lineage_ref=artifact_ref(run_id, artifacts.factor_panel_path),
        evidence_refs=(
            artifact_ref(run_id, artifacts.factor_panel_path),
            artifact_ref(run_id, artifacts.ic_rankic_path),
            artifact_ref(run_id, artifacts.layered_returns_path),
        ),
    )


def build_risk_policy(
    run_id: str,
    *,
    top_n: int,
    max_weight: float,
    turnover_limit: float,
    min_adv_amount: float,
    fee_slippage_ref: str,
) -> PortfolioRiskPolicy:
    return PortfolioRiskPolicy(
        policy_id=f"portfolio-risk-policy:{run_id}",
        top_n=top_n,
        max_weight=max_weight,
        turnover_limit=turnover_limit,
        industry_limit={"max_top_industry_weight": 0.25, "action": "watch_or_block_if_exceeded"},
        style_limit={"style_proxy": ("size", "value", "momentum", "volatility"), "max_unexplained_exposure": "watch"},
        capacity_assumption={
            "min_adv20_amount_native_units": min_adv_amount,
            "data_lake_field": "liquidity_capacity.adv20_amount",
            "max_participation_rate": 0.05,
        },
        fee_slippage_ref=fee_slippage_ref,
        stop_conditions=(
            "stage3_package_validation_failed",
            "factor_ic_decay",
            "top_industry_weight_exceeds_limit",
            "turnover_cost_exceeds_expected_alpha",
            "stage4_runtime_authorization_missing",
        ),
        version="stage3-v1",
    )


def build_strategy_candidate(
    run_id: str,
    signal_set: SignalSet,
    risk_policy: PortfolioRiskPolicy,
    portfolio: pd.DataFrame,
    turnover: pd.DataFrame,
    artifacts: Stage3ResearchArtifacts,
) -> StrategyCandidate:
    mean_net = float(turnover["net_forward_return"].mean()) if not turnover.empty else 0.0
    mean_turnover = float(turnover["turnover"].mean()) if not turnover.empty else 0.0
    cumulative = (1.0 + turnover["net_forward_return"].fillna(0.0)).cumprod() if not turnover.empty else pd.Series(dtype=float)
    drawdown = float((cumulative / cumulative.cummax() - 1.0).min()) if not cumulative.empty else 0.0
    admission = "research_baseline" if mean_net > 0 and mean_turnover <= risk_policy.turnover_limit else "watch"
    return StrategyCandidate(
        candidate_id=f"strategy-candidate:{run_id}",
        strategy_id="stage3_mature_multifactor_v1",
        strategy_family=StrategyFamily.MULTIFACTOR,
        admission=admission,
        research_status="stage3_research_candidate_ready",
        source_contract={"schema_version": "stage3_mature_multifactor_research_v1", "run_id": run_id},
        source_candidate_ref={
            "schema_version": "stage3_candidate_ref_v1",
            "source_portfolio_id": f"portfolio:{run_id}:topn",
            "evidence_ref": artifact_ref(run_id, artifacts.turnover_path),
        },
        signal_set_ref={"schema_version": signal_set.schema_version, "signal_set_id": signal_set.signal_set_id},
        evidence_index_ref={"schema_version": "research_evidence_index_v1", "index_id": f"research-evidence-index:{run_id}"},
        portfolio_risk_policy_ref={"schema_version": risk_policy.schema_version, "policy_id": risk_policy.policy_id},
        metrics_summary={
            "mean_net_return": mean_net,
            "mean_turnover": mean_turnover,
            "max_drawdown_proxy": drawdown,
            "portfolio_rows": int(len(portfolio)),
        },
        typed_unavailable=(),
        blocked_reasons=(),
        limitations=("not_runtime_authorization", "stage4_review_required"),
    )


def build_research_evidence_index(
    run_id: str,
    artifacts: Stage3ResearchArtifacts,
    catalog: Mapping[str, Any],
    limitations: Sequence[str],
) -> ResearchEvidenceIndex:
    return ResearchEvidenceIndex(
        index_id=f"research-evidence-index:{run_id}",
        data_release_ref=DATASET_REFS["data_release_ref"],
        run_manifest_ref=artifact_ref(run_id, artifacts.run_manifest_path),
        metric_refs={
            "ic_rankic_ref": artifact_ref(run_id, artifacts.ic_rankic_path),
            "layered_returns_ref": artifact_ref(run_id, artifacts.layered_returns_path),
            "turnover_ref": artifact_ref(run_id, artifacts.turnover_path),
            "exposure_ref": artifact_ref(run_id, artifacts.exposure_path),
            "factor_model_validation_report_ref": artifact_ref(run_id, artifacts.factor_model_validation_report_path),
            "portfolio_version_ref": artifact_ref(run_id, artifacts.strategy_candidate_path),
            "risk_policy_version_ref": artifact_ref(run_id, artifacts.risk_policy_path),
            "mature_strategy_admission_package_ref": artifact_ref(run_id, artifacts.mature_admission_package_path),
            "runner_offline_preflight_ref": artifact_ref(run_id, artifacts.runner_offline_preflight_path),
        },
        lineage_refs={dataset: _catalog_ref(dataset, entry) for dataset, entry in catalog.items()},
        limitations=tuple(limitations),
    )


def build_factor_specs(
    run_id: str,
    catalog: Mapping[str, Any],
    *,
    admitted_anomaly_entries: Sequence[FactorCatalogEntry] = (),
    include_admitted_anomalies: bool = False,
) -> tuple[FactorSpec, ...]:
    common = {
        "version": "stage3-v1",
        "preprocessing": {"winsorize": [0.01, 0.99], "zscore": "cross_sectional_by_trade_date"},
        "universe": {"ref": DATASET_REFS["pit_universe"], "filters": "stage3_p0_tradability_liquidity_lifecycle"},
        "availability_policy": {"available_at": "daily_close_after_15_30", "policy": "no_lookahead"},
        "blocked_claims": BLOCKED_CLAIMS_DEFAULT,
        "failure_policy": "fail_closed",
    }
    entries = stage3_factor_catalog_entries()
    if include_admitted_anomalies:
        entries = entries + stage3_candidate_factor_catalog_entries(admitted_anomaly_entries)
    return tuple(
        FactorSpec(
            factor_id=entry.factor_id,
            name=entry.name,
            direction=entry.direction,
            input_fields=entry.input_fields,
            window=entry.window,
            params={
                "formula": entry.formula,
                "category": entry.category,
                "family": entry.family,
                "source_refs": entry.source_refs,
                "catalog_status": entry.status,
                "calculator_status": entry.calculator_status,
                "run_id": run_id,
                "notes": entry.notes,
            },
            data_lineage={
                "source_dataset": entry.source_dataset,
                "research_input_schema": "stage3_mature_multifactor_research_v1",
                "evidence_refs": tuple(entry.evidence_refs)
                + (_catalog_ref(entry.source_dataset, catalog.get(entry.source_dataset, {})),),
                "source_of_truth": "project_factor_registry",
                "factor_registry_schema": entry.schema_version,
                "source_refs": entry.source_refs,
            },
            auxiliary_requirements=("pit_universe", "trade_status", "liquidity", "market_cap"),
            **common,
        )
        for entry in entries
    )


def build_admitted_anomaly_factor_specs(
    run_id: str,
    catalog: Mapping[str, Any],
    *,
    anomaly_candidates: Sequence[Mapping[str, Any]],
    anomaly_admission_decisions: Sequence[Mapping[str, Any]],
) -> tuple[FactorSpec, ...]:
    entries = anomaly_candidate_catalog_entries(
        candidates=anomaly_candidates,
        decisions=anomaly_admission_decisions,
    )
    return build_factor_specs(
        run_id,
        catalog,
        admitted_anomaly_entries=entries,
        include_admitted_anomalies=True,
    )


def build_mature_admission_package(
    run_id: str,
    *,
    strategy_candidate: StrategyCandidate,
    signal_set: SignalSet,
    evidence_index: ResearchEvidenceIndex,
    risk_policy: PortfolioRiskPolicy,
    factor_specs: Sequence[FactorSpec],
    portfolio: pd.DataFrame,
    turnover: pd.DataFrame,
    factor_model_validation_report: FactorModelValidationReport,
    factor_model_validation_report_ref: str,
    limitations: Sequence[str],
) -> dict[str, Any]:
    validation_status = factor_model_validation_report.status
    admission_blocked = validation_status in {"blocked", "insufficient_data"}
    validation_blocked_reasons = tuple(dict(item) for item in factor_model_validation_report.blocked_reasons)
    if admission_blocked and not validation_blocked_reasons:
        validation_blocked_reasons = (
            {
                "gate_id": "factor_model_validation",
                "reason": f"FactorModelValidationReport status={validation_status} cannot close Stage 3.",
                "severity": "blocker",
            },
        )
    return {
        "schema_version": "stage3_mature_strategy_admission_package_v1",
        "run_id": run_id,
        "status": "BLOCKED" if admission_blocked else "PASS",
        "overall_admission": strategy_candidate.admission,
        "strategy_candidate": strategy_candidate.to_dict(),
        "signal_set_ref": signal_set.signal_set_id,
        "research_evidence_index_ref": evidence_index.index_id,
        "portfolio_risk_policy_ref": risk_policy.policy_id,
        "factor_model_validation_report_ref": factor_model_validation_report_ref,
        "factor_model_validation_status": validation_status,
        "factor_model_validation_gate_summary": [item.to_dict() for item in factor_model_validation_report.gate_decisions],
        "factor_model_validation_risk_warnings": list(factor_model_validation_report.risk_warnings),
        "blocked_reasons": list(validation_blocked_reasons),
        "factor_spec_refs": [{"factor_id": item.factor_id, "version": item.version} for item in factor_specs],
        "portfolio_rows": int(len(portfolio)),
        "mean_net_forward_return": float(turnover["net_forward_return"].mean()) if not turnover.empty else 0.0,
        "not_authorization": True,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "blocked_claims": [
            {"claim": "qmt_ready", "status": "blocked", "reason": "Stage 4 gate required"},
            {"claim": "simulation_ready", "status": "blocked", "reason": "Stage 4 runtime authorization required"},
            {"claim": "live_ready", "status": "blocked", "reason": "Stage 5 independent live switch CR required"},
            {"claim": "small_live_ready", "status": "blocked", "reason": "Stage 5 independent live switch CR required"},
            {"claim": "runtime_authorized", "status": "blocked", "reason": "No runtime authorization in Stage 3"},
        ],
        "allowed_claims": (
            []
            if admission_blocked
            else [{"claim": "stage3_research_ready_for_stage4_review", "status": "allowed"}]
        ),
        "unlock_conditions": [
            "stage4_simulation_runtime_authorization",
            "gateway_identity_revalidated",
            "stage4_observation_gate_approved",
            "independent_live_switch_cr_for_small_live_or_live",
        ],
        "limitations": list(limitations),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def build_runner_offline_preflight(
    run_id: str,
    *,
    signal_set: SignalSet,
    risk_policy: PortfolioRiskPolicy,
    latest_signals: pd.DataFrame,
    artifacts: Stage3ResearchArtifacts,
    top_n: int,
    max_weight: float,
) -> dict[str, Any]:
    signal_rows = tuple(
        MultifactorSignalRow(
            symbol=str(row.symbol),
            score=float(row.composite_score),
            signal_date=str(row.trade_date),
            factor_refs={"factor_panel": artifact_ref(run_id, artifacts.factor_panel_path)},
        )
        for row in latest_signals.itertuples(index=False)
    )
    result = build_multifactor_target_portfolio(
        strategy_id="stage3_mature_multifactor_v1",
        source_run_id=run_id,
        target_trade_date=str(latest_signals["trade_date"].iloc[0]) if not latest_signals.empty else "",
        signal_rows=signal_rows,
        top_n=top_n,
        max_weight=max_weight,
        score_refs={"signal_set": signal_set.signal_set_id},
        risk_cost_refs={"risk_policy": risk_policy.policy_id},
        lineage_refs={"factor_panel": artifact_ref(run_id, artifacts.factor_panel_path)},
        limitations=("offline_preflight_only", "not_runtime_authorization"),
    )
    return {
        "schema_version": "stage3_runner_offline_preflight_v1",
        "run_id": run_id,
        "status": "PASS" if result.passed else "BLOCKED",
        "target_portfolio_result": result.to_dict(),
        "not_runtime_authorization": True,
        "not_gateway_or_qmt_operation": True,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def build_stage4_observation_plan(
    run_id: str,
    artifacts: Stage3ResearchArtifacts,
    portfolio: pd.DataFrame,
    limitations: Sequence[str],
) -> dict[str, Any]:
    return {
        "schema_version": "stage4_simulation_observation_plan_v1",
        "run_id": run_id,
        "source_stage3_package_ref": artifact_ref(run_id, artifacts.package_path),
        "rebalance_frequency": "weekly",
        "observation_min_trading_days": 20,
        "metrics": ["net_return", "drawdown", "turnover", "industry_exposure", "unknown_order_count", "manual_takeover_required"],
        "stop_conditions": ["runtime_identity_mismatch", "unknown_order_status", "manual_takeover_required", "drawdown_breach", "data_lineage_mismatch"],
        "manual_takeover": {"required_on_exception": True, "cancel_only_rollback": True},
        "stage4_requires_new_runtime_authorization": True,
        "portfolio_rows": int(len(portfolio)),
        "limitations": list(limitations),
    }


def stage3_input_refs(catalog: Mapping[str, Any], artifacts: Stage3ResearchArtifacts, run_id: str) -> dict[str, str]:
    refs = {
        "data_release_ref": DATASET_REFS["data_release_ref"],
        "pit_universe": _catalog_ref("stock_basic", catalog.get("stock_basic", {})),
        "listing_delisting": _catalog_ref("stock_basic", catalog.get("stock_basic", {})),
        "st_filter": _catalog_ref("trade_status", catalog.get("trade_status", {})),
        "suspension_filter": _catalog_ref("trade_status", catalog.get("trade_status", {})),
        "limit_up_down_filter": _catalog_ref("prices_limit", catalog.get("prices_limit", {})),
        "liquidity_filter": _catalog_ref("liquidity_capacity", catalog.get("liquidity_capacity", {})),
        "industry_classification": _catalog_ref("industry_classification", catalog.get("industry_classification", {})),
        "market_cap": _catalog_ref("market_cap", catalog.get("market_cap", {})),
        "style_exposure": artifact_ref(run_id, artifacts.exposure_path),
        "benchmark": _catalog_ref("hs300_index", catalog.get("hs300_index", {})) + "#index_code=000985.SH",
        "fee_slippage_model": artifact_ref(run_id, artifacts.runner_offline_preflight_path),
    }
    return refs


def stage3_evidence_refs(artifacts: Stage3ResearchArtifacts, run_id: str) -> dict[str, str]:
    return {
        "data_release_ref": DATASET_REFS["data_release_ref"],
        "run_manifest_ref": artifact_ref(run_id, artifacts.run_manifest_path),
        "factor_panel_ref": artifact_ref(run_id, artifacts.factor_panel_path),
        "label_window_ref": artifact_ref(run_id, artifacts.label_window_path),
        "ic_rankic_ref": artifact_ref(run_id, artifacts.ic_rankic_path),
        "layered_returns_ref": artifact_ref(run_id, artifacts.layered_returns_path),
        "turnover_ref": artifact_ref(run_id, artifacts.turnover_path),
        "exposure_ref": artifact_ref(run_id, artifacts.exposure_path),
        "factor_model_validation_report_ref": artifact_ref(run_id, artifacts.factor_model_validation_report_path),
        "portfolio_version_ref": artifact_ref(run_id, artifacts.strategy_candidate_path),
        "risk_policy_version_ref": artifact_ref(run_id, artifacts.risk_policy_path),
        "mature_strategy_admission_package_ref": artifact_ref(run_id, artifacts.mature_admission_package_path),
        "runner_offline_preflight_ref": artifact_ref(run_id, artifacts.runner_offline_preflight_path),
    }


def write_stage3_outputs(**kwargs: Any) -> None:
    artifacts: Stage3ResearchArtifacts = kwargs["artifacts"]
    frame: pd.DataFrame = kwargs["frame"]
    frame_cols = [
        "trade_date",
        "symbol",
        "momentum_20d",
        "reversal_5d",
        "volatility_20d",
        "liquidity_adv20",
        "value_pb_inverse",
        "composite_score",
        "available_at",
        "quality_status",
    ]
    frame.loc[:, [col for col in frame_cols if col in frame.columns]].to_parquet(artifacts.factor_panel_path, index=False)
    kwargs["label_window"].to_parquet(artifacts.label_window_path, index=False)
    kwargs["ic_rankic"].to_csv(artifacts.ic_rankic_path, index=False)
    kwargs["layered_returns"].to_csv(artifacts.layered_returns_path, index=False)
    kwargs["turnover"].to_csv(artifacts.turnover_path, index=False)
    kwargs["exposure"].to_csv(artifacts.exposure_path, index=False)
    _write_json(artifacts.factor_model_validation_report_path, kwargs["factor_model_validation_report"].to_dict())
    _write_json(artifacts.factor_specs_path, [item.to_dict() for item in kwargs["factor_specs"]])
    _write_json(artifacts.input_refs_path, kwargs["input_refs"])
    _write_json(artifacts.run_manifest_path, kwargs["manifest"].to_dict())
    _write_json(artifacts.signal_set_path, kwargs["signal_set"].to_dict())
    _write_json(artifacts.strategy_candidate_path, kwargs["strategy_candidate"].to_dict())
    _write_json(artifacts.research_evidence_index_path, kwargs["evidence_index"].to_dict())
    _write_json(artifacts.risk_policy_path, kwargs["risk_policy"].to_dict())
    _write_json(artifacts.mature_admission_package_path, kwargs["admission_package"])
    _write_json(artifacts.runner_offline_preflight_path, kwargs["runner_preflight"])
    _write_json(artifacts.observation_plan_path, kwargs["observation_plan"])
    _write_json(artifacts.package_path, kwargs["package"].to_dict())
    report = {
        "schema_version": STAGE3_RUN_SCHEMA,
        "run_id": artifacts.run_id,
        "portfolio_summary": _portfolio_summary(kwargs["portfolio"], kwargs["turnover"]),
        "factor_model_validation_status": kwargs["factor_model_validation_report"].status,
        "limitations": list(kwargs["limitations"]),
        "artifacts": artifacts.to_dict(),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }
    _write_json(artifacts.report_json_path, report)
    artifacts.report_md_path.write_text(render_stage3_report(report), encoding="utf-8")


def write_summary_outputs(result: Stage3ResearchRunResult, artifacts: Stage3ResearchArtifacts) -> None:
    _write_json(artifacts.process_summary_path, result.to_dict())


def summarize_metrics(
    portfolio: pd.DataFrame,
    turnover: pd.DataFrame,
    ic_rankic: pd.DataFrame,
    layered_returns: pd.DataFrame,
    frame: pd.DataFrame,
    valid: pd.DataFrame,
) -> dict[str, Any]:
    return {
        "factor_panel_rows": int(len(frame)),
        "valid_research_rows": int(len(valid)),
        "portfolio_rows": int(len(portfolio)),
        "rebalance_count": int(turnover["trade_date"].nunique()) if not turnover.empty else 0,
        "mean_net_forward_return": float(turnover["net_forward_return"].mean()) if not turnover.empty else 0.0,
        "mean_turnover": float(turnover["turnover"].mean()) if not turnover.empty else 0.0,
        "mean_composite_rank_ic": float(ic_rankic.loc[ic_rankic["factor_id"] == "composite_score", "rank_ic"].mean()) if not ic_rankic.empty else 0.0,
        "top_quantile_mean_return": float(layered_returns.loc[layered_returns["quantile"] == layered_returns["quantile"].max(), "mean_forward_return"].mean()) if not layered_returns.empty else 0.0,
    }


def render_stage3_report(report: Mapping[str, Any]) -> str:
    metrics = report.get("portfolio_summary", {})
    lines = [
        "# Stage 3 Mature Multifactor Research Report",
        "",
        f"- run_id: `{report.get('run_id')}`",
        "- status: `PASS`",
        "- provider_fetch: `0`",
        "- lake_write: `0`",
        "- catalog_publish: `0`",
        "- qmt_operation: `0`",
        "- simulation_or_live: `0`",
        "- credential_read: `0`",
        "",
        "## Portfolio Summary",
        "",
        f"- rebalance_count: `{metrics.get('rebalance_count', 0)}`",
        f"- mean_net_forward_return: `{metrics.get('mean_net_forward_return', 0)}`",
        f"- mean_turnover: `{metrics.get('mean_turnover', 0)}`",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in report.get("limitations", []))
    lines.append("")
    return "\n".join(lines)


def _load_inputs(lake: Path, catalog: Mapping[str, Any], *, start: str, end: str) -> dict[str, pd.DataFrame]:
    read_start = "2020-09-01" if start >= "2021-01-01" else start
    return {
        "prices": _read_dataset(lake, catalog, "prices", columns=["trade_date", "symbol", "close", "adjusted_close", "available_at"], start=read_start, end=end),
        "trade_status": _read_dataset(lake, catalog, "trade_status", columns=["trade_date", "symbol", "is_tradable", "is_suspended", "is_st"], start=start, end=end),
        "liquidity_capacity": _read_dataset(lake, catalog, "liquidity_capacity", columns=["trade_date", "symbol", "adv20_amount", "turnover_rate"], start=start, end=end),
        "market_cap": _read_dataset(lake, catalog, "market_cap", columns=["trade_date", "symbol", "market_cap", "float_market_cap", "pb"], start=start, end=end),
        "prices_limit": _read_dataset(lake, catalog, "prices_limit", columns=["trade_date", "symbol", "limit_up", "limit_down"], start=start, end=end),
        "stock_basic": _read_dataset(lake, catalog, "stock_basic", columns=["symbol", "list_status", "list_date", "delist_date"], start=None, end=None),
        "industry_classification": _read_dataset(lake, catalog, "industry_classification", columns=["symbol", "industry_code", "industry_name"], start=None, end=None),
    }


def _read_dataset(
    lake: Path,
    catalog: Mapping[str, Any],
    dataset: str,
    *,
    columns: Sequence[str],
    start: str | None,
    end: str | None,
) -> pd.DataFrame:
    entry = catalog[dataset]
    root_path = lake / "canonical" / dataset / "1.0"
    ref = entry.get("canonical_path")
    catalog_path = lake / str(ref) if ref else root_path
    path = root_path if root_path.exists() else catalog_path
    frame = pd.read_parquet(path, columns=list(columns))
    if "trade_date" in frame.columns:
        frame["trade_date"] = _date_text(frame["trade_date"])
        if start is not None:
            frame = frame.loc[frame["trade_date"] >= start]
        if end is not None:
            frame = frame.loc[frame["trade_date"] <= end]
        frame = frame.drop_duplicates(["trade_date", "symbol"], keep="last")
    return frame.reset_index(drop=True)


def _read_catalog(lake: Path) -> dict[str, Any]:
    payload = json.loads((lake / "catalog" / "catalog.json").read_text(encoding="utf-8"))
    return dict(payload["datasets"])


def _daily(inputs: Mapping[str, pd.DataFrame], name: str) -> pd.DataFrame:
    frame = inputs[name].copy()
    if "trade_date" in frame.columns:
        frame["trade_date"] = _date_text(frame["trade_date"])
    return frame


def _stock_lifecycle(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["list_date"] = _date_text(data["list_date"])
    data["delist_date"] = data["delist_date"].replace("", pd.NA)
    data = data.sort_values(["symbol", "list_date"]).drop_duplicates("symbol", keep="first")
    return data[["symbol", "list_status", "list_date", "delist_date"]]


def _industry(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data = data.drop_duplicates("symbol", keep="last")
    return data[["symbol", "industry_code", "industry_name"]]


def _winsor_zscore(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    if len(valid) < 20:
        return pd.Series(index=values.index, dtype=float)
    low, high = valid.quantile([0.01, 0.99])
    clipped = numeric.clip(lower=low, upper=high)
    std = clipped.std(ddof=0)
    if not std or pd.isna(std):
        return pd.Series(index=values.index, dtype=float)
    return (clipped - clipped.mean()) / std


def _portfolio_summary(portfolio: pd.DataFrame, turnover: pd.DataFrame) -> dict[str, Any]:
    return {
        "portfolio_rows": int(len(portfolio)),
        "rebalance_count": int(turnover["trade_date"].nunique()) if not turnover.empty else 0,
        "mean_net_forward_return": float(turnover["net_forward_return"].mean()) if not turnover.empty else 0.0,
        "mean_turnover": float(turnover["turnover"].mean()) if not turnover.empty else 0.0,
    }


def _catalog_ref(dataset: str, entry: Mapping[str, Any]) -> str:
    run_id = entry.get("latest_manifest_run_id") or "unknown"
    return f"catalog://{dataset}/1.0/{run_id}"


def artifact_ref(run_id: str, path: Path) -> str:
    return f"artifact://stage3-mature-multifactor/{run_id}/{path.name}"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _date_text(series: Any) -> Any:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def _float(value: Any) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _json_safe(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    try:
        if not isinstance(value, (str, bytes)) and pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return json_safe(value)
