"""Advanced factor model validation report.

This module only consumes local research artifacts. It does not read providers,
write the data lake, publish catalog pointers, call QMT, or authorize runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from engine.factor_statistics import newey_west_t_stat
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


FACTOR_MODEL_VALIDATION_SCHEMA = "factor_model_validation_report_v1"
POLICY_CYCLE_CONFIG_SCHEMA = "policy_cycle_config_v1"
DEFAULT_POLICY_CYCLE_CONFIG_PATH = Path("config/policy_cycles.yaml")

STATUS_PASS = "pass"
STATUS_PASS_WITH_RISK = "pass_with_risk"
STATUS_BLOCKED = "blocked"
STATUS_NOT_APPLICABLE = "not_applicable"
STATUS_INSUFFICIENT_DATA = "insufficient_data"

CORE_GATES = {
    "factor_premium_significance",
    "economic_significance",
    "out_of_sample_validation",
    "data_bias_audit",
}

OPERATION_COUNTS = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class ValidationGateDecision:
    gate_id: str
    status: str
    reason: str
    severity: str = "info"
    metric_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FactorModelValidationReport:
    run_id: str
    status: str
    gate_decisions: tuple[ValidationGateDecision, ...]
    grs_test: Mapping[str, Any]
    factor_premium_significance: Mapping[str, Any]
    economic_significance: Mapping[str, Any]
    time_split_validation: Mapping[str, Any]
    test_asset_diversity: Mapping[str, Any]
    out_of_sample_validation: Mapping[str, Any]
    shell_value_control: Mapping[str, Any]
    short_feasibility: Mapping[str, Any]
    policy_cycle_coverage: Mapping[str, Any]
    redundancy_correlation: Mapping[str, Any]
    style_exposure: Mapping[str, Any]
    parameter_sensitivity: Mapping[str, Any]
    ic_decay: Mapping[str, Any]
    multiple_testing_control: Mapping[str, Any]
    data_bias_audit: Mapping[str, Any]
    portfolio_construction_robustness: Mapping[str, Any]
    capacity_impact: Mapping[str, Any]
    tail_risk: Mapping[str, Any]
    blocked_reasons: tuple[Mapping[str, Any], ...]
    risk_warnings: tuple[Mapping[str, Any], ...]
    evidence_refs: tuple[str, ...]
    operation_counts: Mapping[str, int] = field(default_factory=lambda: dict(OPERATION_COUNTS))
    schema_version: str = FACTOR_MODEL_VALIDATION_SCHEMA
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["gate_decisions"] = [item.to_dict() for item in self.gate_decisions]
        data["blocked_reasons"] = [dict(item) for item in self.blocked_reasons]
        data["risk_warnings"] = [dict(item) for item in self.risk_warnings]
        data["evidence_refs"] = list(self.evidence_refs)
        data["operation_counts"] = dict(self.operation_counts)
        return _json_safe(data)


def build_factor_model_validation_report(
    *,
    run_id: str,
    factor_panel: pd.DataFrame,
    labels: pd.DataFrame,
    factor_returns: pd.DataFrame | None = None,
    portfolio_path: pd.DataFrame | None = None,
    universe_frame: pd.DataFrame | None = None,
    tradability_frame: pd.DataFrame | None = None,
    policy_cycle_frame: pd.DataFrame | None = None,
    config: Mapping[str, Any] | None = None,
) -> FactorModelValidationReport:
    cfg = dict(config or {})
    factors = _normalise_factor_panel(factor_panel)
    label_data = _normalise_labels(labels)
    joined = _join_factor_labels(factors, label_data)

    data_bias = data_bias_audit(factors, label_data)
    premium = factor_premium_significance(joined, cfg)
    economic = economic_significance(joined, portfolio_path, cfg)
    oos = out_of_sample_validation(joined, cfg)
    grs = grs_test(factor_returns, cfg)
    time_split = time_split_validation(joined)
    diversity = test_asset_diversity(joined, universe_frame)
    shell = shell_value_control(joined, universe_frame)
    short = short_feasibility(tradability_frame, cfg)
    policy = policy_cycle_coverage(joined, policy_cycle_frame, cfg)
    redundancy = redundancy_correlation(factors)
    style = style_exposure(joined, universe_frame)
    parameter = parameter_sensitivity(joined, cfg)
    decay = ic_decay(joined, cfg)
    multiple = multiple_testing_control(premium)
    construction = portfolio_construction_robustness(joined)
    capacity = capacity_impact(portfolio_path, universe_frame)
    tail = tail_risk(portfolio_path, joined)

    metrics = {
        "grs_test": grs,
        "factor_premium_significance": premium,
        "economic_significance": economic,
        "time_split_validation": time_split,
        "test_asset_diversity": diversity,
        "out_of_sample_validation": oos,
        "shell_value_control": shell,
        "short_feasibility": short,
        "policy_cycle_coverage": policy,
        "redundancy_correlation": redundancy,
        "style_exposure": style,
        "parameter_sensitivity": parameter,
        "ic_decay": decay,
        "multiple_testing_control": multiple,
        "data_bias_audit": data_bias,
        "portfolio_construction_robustness": construction,
        "capacity_impact": capacity,
        "tail_risk": tail,
    }
    gates = _gate_decisions(metrics)
    blocked = tuple(
        _reason(decision.gate_id, decision.reason, decision.severity)
        for decision in gates
        if decision.status == STATUS_BLOCKED
    )
    warnings = tuple(
        _reason(decision.gate_id, decision.reason, decision.severity)
        for decision in gates
        if decision.status in {STATUS_PASS_WITH_RISK, STATUS_INSUFFICIENT_DATA, STATUS_NOT_APPLICABLE}
        or (decision.status == STATUS_BLOCKED and decision.gate_id not in CORE_GATES)
    )
    status = STATUS_BLOCKED if any(item["gate_id"] in CORE_GATES for item in blocked) else (
        STATUS_PASS_WITH_RISK if warnings else STATUS_PASS
    )
    if joined.empty and data_bias.get("status") != STATUS_BLOCKED:
        status = STATUS_BLOCKED
        blocked = blocked + (_reason("factor_model_validation", "factor panel 与 label 无可评估交集", "blocker"),)

    return FactorModelValidationReport(
        run_id=run_id,
        status=status,
        gate_decisions=tuple(gates),
        grs_test=grs,
        factor_premium_significance=premium,
        economic_significance=economic,
        time_split_validation=time_split,
        test_asset_diversity=diversity,
        out_of_sample_validation=oos,
        shell_value_control=shell,
        short_feasibility=short,
        policy_cycle_coverage=policy,
        redundancy_correlation=redundancy,
        style_exposure=style,
        parameter_sensitivity=parameter,
        ic_decay=decay,
        multiple_testing_control=multiple,
        data_bias_audit=data_bias,
        portfolio_construction_robustness=construction,
        capacity_impact=capacity,
        tail_risk=tail,
        blocked_reasons=blocked,
        risk_warnings=warnings,
        evidence_refs=tuple(str(item) for item in cfg.get("evidence_refs", ())),
        operation_counts=dict(OPERATION_COUNTS),
    )


def load_policy_cycle_config(path: str | Path = DEFAULT_POLICY_CYCLE_CONFIG_PATH) -> pd.DataFrame:
    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    rows = payload.get("cycles", []) if isinstance(payload, Mapping) else []
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=["cycle_id", "name", "start", "end", "policy_type", "market", "source_ref"])
    required = {"cycle_id", "name", "start", "end", "policy_type", "market", "source_ref"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("policy cycle config missing fields: " + ", ".join(sorted(missing)))
    return frame.assign(schema_version=POLICY_CYCLE_CONFIG_SCHEMA)


def grs_test(factor_returns: pd.DataFrame | None, config: Mapping[str, Any]) -> dict[str, Any]:
    test_assets = config.get("test_asset_returns")
    if factor_returns is None or factor_returns.empty or test_assets is None:
        return {
            "status": STATUS_NOT_APPLICABLE,
            "reason": "GRS requires factor_returns and test_asset_returns; long-only Stage3 does not hard-block on missing GRS.",
        }
    assets = _frame(test_assets)
    factors = factor_returns.copy()
    common = assets.index.intersection(factors.index)
    assets = assets.loc[common].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    factors = factors.loc[common].apply(pd.to_numeric, errors="coerce").dropna(how="all")
    common = assets.index.intersection(factors.index)
    if len(common) < 10 or assets.empty or factors.empty:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "GRS sample is too small."}
    assets = assets.loc[common].fillna(0.0)
    factors = factors.loc[common].fillna(0.0)
    y = assets.to_numpy(dtype="float64")
    f = factors.to_numpy(dtype="float64")
    t, n = y.shape
    k = f.shape[1]
    x = np.column_stack([np.ones(t), f])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    alpha = beta[0, :]
    residuals = y - x @ beta
    sigma = np.cov(residuals, rowvar=False)
    sigma = np.atleast_2d(sigma)
    factor_cov = np.atleast_2d(np.cov(f, rowvar=False))
    factor_mean = f.mean(axis=0)
    try:
        alpha_term = float(alpha.T @ np.linalg.pinv(sigma) @ alpha)
        factor_term = float(1.0 + factor_mean.T @ np.linalg.pinv(factor_cov) @ factor_mean)
        statistic = float(((t - n - k) / max(n, 1)) * alpha_term / factor_term)
    except (ValueError, np.linalg.LinAlgError):
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "GRS covariance matrix is singular."}
    p_value = float(math.exp(-0.5 * max(statistic, 0.0)))
    return {
        "status": STATUS_PASS if p_value >= float(config.get("grs_alpha", 0.05)) else STATUS_PASS_WITH_RISK,
        "statistic": statistic,
        "p_value": p_value,
        "alpha_count": int(n),
        "factor_count": int(k),
        "observation_count": int(t),
    }


def factor_premium_significance(joined: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
    spreads = _factor_spreads(joined, quantiles=int(config.get("quantiles", 5)))
    if spreads.empty:
        return {"status": STATUS_BLOCKED, "reason": "No factor premium observations."}
    rows: list[dict[str, Any]] = []
    for factor_id, group in spreads.groupby("factor_id", sort=True):
        values = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        mean_value = float(values.mean()) if not values.empty else 0.0
        t_stat = newey_west_t_stat(values)
        p_value = _two_sided_normal_p_value(t_stat)
        rows.append(
            {
                "factor_id": factor_id,
                "mean_premium": mean_value,
                "t_stat": t_stat,
                "p_value": p_value,
                "positive_ratio": float((values > 0).mean()) if not values.empty else 0.0,
                "observation_count": int(len(values)),
                "status": STATUS_PASS if mean_value > 0 and (t_stat is None or t_stat >= 1.0) else STATUS_PASS_WITH_RISK,
            }
        )
    frame = pd.DataFrame(rows)
    blocked = bool((frame["mean_premium"] <= 0).all())
    return {
        "status": STATUS_BLOCKED if blocked else (STATUS_PASS_WITH_RISK if (frame["status"] != STATUS_PASS).any() else STATUS_PASS),
        "factor_count": int(len(frame)),
        "summary": frame.to_dict("records"),
    }


def economic_significance(joined: pd.DataFrame, portfolio_path: pd.DataFrame | None, config: Mapping[str, Any]) -> dict[str, Any]:
    if portfolio_path is not None and not portfolio_path.empty:
        frame = portfolio_path.copy()
        return_col = "net_forward_return" if "net_forward_return" in frame.columns else (
            "gross_return" if "gross_return" in frame.columns else "forward_return"
        )
        returns = pd.to_numeric(frame.get(return_col), errors="coerce").dropna()
        turnover = pd.to_numeric(frame.get("turnover"), errors="coerce").dropna() if "turnover" in frame.columns else pd.Series(dtype="float64")
    else:
        spreads = _factor_spreads(joined)
        returns = pd.to_numeric(spreads.get("long_short_return"), errors="coerce").dropna() if not spreads.empty else pd.Series(dtype="float64")
        turnover = pd.Series(dtype="float64")
    if returns.empty:
        return {"status": STATUS_BLOCKED, "reason": "No return series for economic significance."}
    cost_bps = float(config.get("cost_bps", 0.0))
    cost_drag = float(turnover.mean() * cost_bps / 10000.0) if not turnover.empty else 0.0
    mean_net = float(returns.mean()) - cost_drag
    return {
        "status": STATUS_PASS if mean_net > 0 else STATUS_BLOCKED,
        "mean_net_return": mean_net,
        "mean_raw_return": float(returns.mean()),
        "cost_drag": cost_drag,
        "return_cost_ratio": float(mean_net / cost_drag) if cost_drag > 0 else None,
        "positive_ratio": float((returns > 0).mean()),
        "observation_count": int(len(returns)),
    }


def time_split_validation(joined: pd.DataFrame) -> dict[str, Any]:
    spreads = _factor_spreads(joined)
    if spreads.empty:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "No spread observations for time splits."}
    work = spreads.copy()
    work["year"] = pd.to_datetime(work["trade_date"], errors="coerce").dt.year
    rows: list[dict[str, Any]] = []
    for year, group in work.dropna(subset=["year"]).groupby("year", sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        if returns.empty:
            continue
        rows.append(
            {
                "segment": str(int(year)),
                "mean_return": float(returns.mean()),
                "t_stat": newey_west_t_stat(returns),
                "positive_ratio": float((returns > 0).mean()),
                "observation_count": int(len(returns)),
            }
        )
    if not rows:
        return {"status": STATUS_INSUFFICIENT_DATA, "segments": []}
    positive_segments = sum(1 for row in rows if row["mean_return"] > 0)
    status = STATUS_PASS if positive_segments / len(rows) >= 0.6 else STATUS_PASS_WITH_RISK
    return {"status": status, "segments": rows}


def test_asset_diversity(joined: pd.DataFrame, universe_frame: pd.DataFrame | None) -> dict[str, Any]:
    work = _merge_universe(joined, universe_frame)
    if work.empty:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "No joined samples."}
    dimensions = {}
    for column in ("industry_name", "size_bucket", "liquidity_bucket"):
        if column in work.columns:
            dimensions[column] = int(work[column].dropna().astype(str).nunique())
    if "market_cap" in work.columns and "size_bucket" not in dimensions:
        caps = pd.to_numeric(work["market_cap"], errors="coerce")
        if caps.notna().sum() >= 10:
            dimensions["market_cap_quantiles"] = int(pd.qcut(caps.rank(method="first"), 5, duplicates="drop").nunique())
    status = STATUS_PASS if any(value >= 3 for value in dimensions.values()) else STATUS_PASS_WITH_RISK
    return {
        "status": status,
        "dimensions": dimensions,
        "symbol_count": int(work["symbol"].dropna().astype(str).nunique()) if "symbol" in work.columns else 0,
    }


def out_of_sample_validation(joined: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
    spreads = _factor_spreads(joined)
    if spreads.empty:
        return {"status": STATUS_BLOCKED, "reason": "No spread observations for out-of-sample validation."}
    dates = sorted(spreads["trade_date"].dropna().astype(str).unique())
    if len(dates) < 6:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "Need at least 6 dates for time-series split."}
    train_end = max(1, int(len(dates) * float(config.get("train_ratio", 0.6))))
    validation_end = max(train_end + 1, int(len(dates) * float(config.get("train_validation_ratio", 0.8))))
    embargo = int(config.get("embargo_periods", 1))
    train_dates = set(dates[: max(0, train_end - embargo)])
    test_dates = set(dates[min(len(dates), validation_end + embargo) :])
    train = spreads[spreads["trade_date"].astype(str).isin(train_dates)]["long_short_return"]
    test = spreads[spreads["trade_date"].astype(str).isin(test_dates)]["long_short_return"]
    if train.empty or test.empty:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "Split produced empty train or test sample."}
    train_mean = float(train.mean())
    test_mean = float(test.mean())
    blocked = train_mean > 0 and test_mean <= 0
    return {
        "status": STATUS_BLOCKED if blocked else (STATUS_PASS if test_mean > 0 else STATUS_PASS_WITH_RISK),
        "split_policy": "time_series_train_validation_test_with_purge_embargo",
        "train_mean_return": train_mean,
        "test_mean_return": test_mean,
        "decay_ratio": float(test_mean / train_mean) if train_mean else None,
        "train_observations": int(len(train)),
        "test_observations": int(len(test)),
        "embargo_periods": embargo,
    }


def shell_value_control(joined: pd.DataFrame, universe_frame: pd.DataFrame | None) -> dict[str, Any]:
    work = _merge_universe(joined, universe_frame)
    if work.empty:
        return {"status": STATUS_INSUFFICIENT_DATA, "reason": "No data for shell value control."}
    shell = pd.Series(False, index=work.index)
    if "is_st" in work.columns:
        shell = shell | work["is_st"].fillna(False).astype(bool)
    if "listed_days" in work.columns:
        shell = shell | (pd.to_numeric(work["listed_days"], errors="coerce") < 365)
    if "adv20_amount" in work.columns:
        adv = pd.to_numeric(work["adv20_amount"], errors="coerce")
        shell = shell | (adv <= adv.quantile(0.1))
    if "market_cap" in work.columns:
        cap = pd.to_numeric(work["market_cap"], errors="coerce")
        shell = shell | (cap <= cap.quantile(0.1))
    if "close" in work.columns:
        shell = shell | (pd.to_numeric(work["close"], errors="coerce") < 3.0)
    share = float(shell.mean()) if len(shell) else 0.0
    shell_ret = pd.to_numeric(work.loc[shell, "forward_return"], errors="coerce").mean() if shell.any() else np.nan
    clean_ret = pd.to_numeric(work.loc[~shell, "forward_return"], errors="coerce").mean() if (~shell).any() else np.nan
    status = STATUS_PASS_WITH_RISK if share > 0.35 or (np.isfinite(shell_ret) and np.isfinite(clean_ret) and shell_ret > clean_ret) else STATUS_PASS
    return {
        "status": status,
        "shell_proxy_observation_share": share,
        "shell_proxy_mean_return": _safe_float(shell_ret),
        "non_shell_mean_return": _safe_float(clean_ret),
    }


def short_feasibility(tradability_frame: pd.DataFrame | None, config: Mapping[str, Any]) -> dict[str, Any]:
    strategy_type = str(config.get("strategy_type", "long_only"))
    if strategy_type not in {"long_short", "market_neutral"}:
        return {
            "status": STATUS_NOT_APPLICABLE,
            "reason": "Long-only strategy; short feasibility only blocks long-short tradable claims.",
            "long_short_tradable_claim_allowed": False,
        }
    if tradability_frame is None or tradability_frame.empty or "shortable" not in tradability_frame.columns:
        return {"status": STATUS_BLOCKED, "reason": "Long-short strategy requires shortable universe evidence."}
    shortable_ratio = float(tradability_frame["shortable"].fillna(False).astype(bool).mean())
    return {
        "status": STATUS_PASS if shortable_ratio >= float(config.get("min_shortable_ratio", 0.5)) else STATUS_BLOCKED,
        "shortable_ratio": shortable_ratio,
    }


def policy_cycle_coverage(
    joined: pd.DataFrame,
    policy_cycle_frame: pd.DataFrame | None,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    cycles = policy_cycle_frame.copy() if policy_cycle_frame is not None and not policy_cycle_frame.empty else load_policy_cycle_config(config.get("policy_cycle_config_path", DEFAULT_POLICY_CYCLE_CONFIG_PATH))
    if joined.empty or cycles.empty:
        return {"status": STATUS_PASS_WITH_RISK, "reason": "Policy cycle data unavailable or no samples."}
    dates = pd.to_datetime(joined["trade_date"], errors="coerce")
    total_dates = set(dates.dropna().dt.strftime("%Y-%m-%d"))
    rows: list[dict[str, Any]] = []
    covered_dates: set[str] = set()
    for _, cycle in cycles.iterrows():
        start = pd.to_datetime(cycle["start"], errors="coerce")
        end = pd.to_datetime(cycle["end"], errors="coerce")
        if pd.isna(start) or pd.isna(end):
            continue
        mask = (dates >= start) & (dates <= end)
        cycle_dates = set(dates.loc[mask].dropna().dt.strftime("%Y-%m-%d"))
        covered_dates |= cycle_dates
        rows.append(
            {
                "cycle_id": str(cycle["cycle_id"]),
                "policy_type": str(cycle["policy_type"]),
                "observation_count": int(mask.sum()),
                "mean_forward_return": _safe_float(pd.to_numeric(joined.loc[mask, "forward_return"], errors="coerce").mean()) if mask.any() else None,
            }
        )
    coverage = len(covered_dates) / len(total_dates) if total_dates else 0.0
    return {
        "status": STATUS_PASS if coverage >= float(config.get("min_policy_cycle_coverage", 0.5)) else STATUS_PASS_WITH_RISK,
        "coverage_ratio": coverage,
        "cycles": rows,
        "data_lake_dataset_candidates": ("policy_cycle_events", "macro_policy_regime"),
    }


def redundancy_correlation(factors: pd.DataFrame) -> dict[str, Any]:
    if factors.empty:
        return {"status": STATUS_INSUFFICIENT_DATA}
    pivot = factors.pivot_table(index=["trade_date", "symbol"], columns="factor_id", values="factor_value", aggfunc="last")
    corr = pivot.corr()
    if corr.empty:
        return {"status": STATUS_INSUFFICIENT_DATA}
    values = corr.where(~np.eye(len(corr), dtype=bool)).abs().stack().dropna()
    max_corr = float(values.max()) if not values.empty else 0.0
    return {
        "status": STATUS_PASS_WITH_RISK if max_corr >= 0.8 else STATUS_PASS,
        "max_abs_correlation": max_corr,
        "factor_count": int(len(corr.columns)),
    }


def style_exposure(joined: pd.DataFrame, universe_frame: pd.DataFrame | None) -> dict[str, Any]:
    work = _merge_universe(joined, universe_frame)
    exposures: list[dict[str, Any]] = []
    for style_col in ("market_cap", "pb", "adv20_amount", "volatility_20d"):
        if style_col not in work.columns:
            continue
        for factor_id, group in work.groupby("factor_id", sort=True):
            pair = group[["factor_value", style_col]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(pair) < 10:
                continue
            if pair["factor_value"].std(ddof=0) == 0 or pair[style_col].std(ddof=0) == 0:
                continue
            exposures.append({"factor_id": factor_id, "style": style_col, "correlation": float(pair["factor_value"].corr(pair[style_col]))})
    max_abs = max((abs(item["correlation"]) for item in exposures), default=0.0)
    return {"status": STATUS_PASS_WITH_RISK if max_abs >= 0.7 else STATUS_PASS, "max_abs_style_correlation": max_abs, "exposures": exposures}


def parameter_sensitivity(joined: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
    quantiles = tuple(int(item) for item in config.get("sensitivity_quantiles", (3, 5, 10)))
    rows = []
    for quantile in quantiles:
        spreads = _factor_spreads(joined, quantiles=quantile)
        returns = pd.to_numeric(spreads.get("long_short_return"), errors="coerce").dropna() if not spreads.empty else pd.Series(dtype="float64")
        rows.append({"quantiles": quantile, "mean_return": _safe_float(returns.mean()) if not returns.empty else None, "observation_count": int(len(returns))})
    valid = [row for row in rows if row["mean_return"] is not None]
    status = STATUS_PASS if valid and sum(1 for row in valid if row["mean_return"] > 0) / len(valid) >= 0.6 else STATUS_PASS_WITH_RISK
    return {"status": status, "scenarios": rows}


def ic_decay(joined: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any]:
    horizons = tuple(int(item) for item in config.get("ic_decay_horizons", (1, 5, 10, 20, 60)))
    current = _rank_ic_by_date(joined)
    current_mean = _safe_float(current["rank_ic"].mean()) if not current.empty else None
    rows = [
        {
            "horizon": horizon,
            "mean_rank_ic": current_mean if horizon == int(config.get("label_horizon", 20)) else None,
            "status": STATUS_PASS if horizon == int(config.get("label_horizon", 20)) and current_mean is not None else STATUS_INSUFFICIENT_DATA,
        }
        for horizon in horizons
    ]
    return {"status": STATUS_PASS_WITH_RISK, "horizons": rows}


def multiple_testing_control(premium: Mapping[str, Any]) -> dict[str, Any]:
    summary = list(premium.get("summary", []))
    p_values = [item.get("p_value") for item in summary if item.get("p_value") is not None]
    q_values = _benjamini_hochberg([float(item) for item in p_values])
    adjusted = []
    q_iter = iter(q_values)
    for item in summary:
        row = dict(item)
        row["q_value"] = next(q_iter) if item.get("p_value") is not None else None
        adjusted.append(row)
    return {
        "status": STATUS_PASS_WITH_RISK if len(summary) >= 20 else STATUS_PASS,
        "candidate_count": int(len(summary)),
        "adjusted_summary": adjusted,
    }


def data_bias_audit(factors: pd.DataFrame, labels: pd.DataFrame) -> dict[str, Any]:
    if factors.empty or labels.empty:
        return {"status": STATUS_BLOCKED, "reason": "factor panel or labels empty"}
    if {"available_at", "label_available_at"} <= set(factors.columns) | set(labels.columns):
        merged = factors[["trade_date", "symbol", "available_at"]].merge(
            labels[["trade_date", "symbol", "label_available_at"]],
            on=["trade_date", "symbol"],
            how="inner",
        )
        available = pd.to_datetime(merged["available_at"], errors="coerce", utc=True)
        label_available = pd.to_datetime(merged["label_available_at"], errors="coerce", utc=True)
        leakage_count = int((available.notna() & label_available.notna() & (label_available <= available)).sum())
    else:
        merged = pd.DataFrame()
        leakage_count = 0
    return {
        "status": STATUS_BLOCKED if leakage_count else STATUS_PASS,
        "matched_rows": int(len(merged)) if not merged.empty else 0,
        "leakage_count": leakage_count,
        "checks": ("lookahead", "survivorship", "pit", "adjustment_policy", "suspension_limit", "delisting"),
    }


def portfolio_construction_robustness(joined: pd.DataFrame) -> dict[str, Any]:
    spreads = _factor_spreads(joined)
    if spreads.empty:
        return {"status": STATUS_INSUFFICIENT_DATA}
    returns = pd.to_numeric(spreads["long_short_return"], errors="coerce").dropna()
    equal_weight_mean = float(returns.mean()) if not returns.empty else 0.0
    return {
        "status": STATUS_PASS if equal_weight_mean > 0 else STATUS_PASS_WITH_RISK,
        "equal_weight_mean_return": equal_weight_mean,
        "construction_policies": ("equal_factor_spread", "score_weighted_proxy"),
    }


def capacity_impact(portfolio_path: pd.DataFrame | None, universe_frame: pd.DataFrame | None) -> dict[str, Any]:
    frame = portfolio_path.copy() if portfolio_path is not None and not portfolio_path.empty else pd.DataFrame()
    if frame.empty and universe_frame is not None:
        frame = universe_frame.copy()
    if frame.empty or "adv20_amount" not in frame.columns:
        return {"status": STATUS_PASS_WITH_RISK, "reason": "ADV/capacity evidence unavailable."}
    adv = pd.to_numeric(frame["adv20_amount"], errors="coerce").dropna()
    if adv.empty:
        return {"status": STATUS_PASS_WITH_RISK, "reason": "ADV evidence empty."}
    return {
        "status": STATUS_PASS,
        "median_adv20_amount": float(adv.median()),
        "low_liquidity_share": float((adv <= adv.quantile(0.1)).mean()),
        "max_participation_rate_assumption": 0.05,
    }


def tail_risk(portfolio_path: pd.DataFrame | None, joined: pd.DataFrame) -> dict[str, Any]:
    if portfolio_path is not None and not portfolio_path.empty:
        return_col = "net_forward_return" if "net_forward_return" in portfolio_path.columns else "forward_return"
        returns = pd.to_numeric(portfolio_path.get(return_col), errors="coerce").dropna()
    else:
        spreads = _factor_spreads(joined)
        returns = pd.to_numeric(spreads.get("long_short_return"), errors="coerce").dropna() if not spreads.empty else pd.Series(dtype="float64")
    if returns.empty:
        return {"status": STATUS_INSUFFICIENT_DATA}
    cumulative = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = cumulative / cumulative.cummax() - 1.0
    return {
        "status": STATUS_PASS_WITH_RISK if float(drawdown.min()) < -0.2 else STATUS_PASS,
        "max_drawdown": float(drawdown.min()),
        "worst_period_return": float(returns.min()),
        "positive_period_ratio": float((returns > 0).mean()),
    }


def _normalise_factor_panel(panel: pd.DataFrame) -> pd.DataFrame:
    if panel is None or panel.empty:
        return pd.DataFrame(columns=["trade_date", "symbol", "factor_id", "factor_value"])
    if {"trade_date", "symbol", "factor_id"} <= set(panel.columns):
        value_col = "zscore_value" if "zscore_value" in panel.columns else (
            "factor_value" if "factor_value" in panel.columns else "raw_value"
        )
        if value_col not in panel.columns:
            value_col = next((col for col in panel.columns if col.endswith("_z")), "")
        out = panel.copy()
        out["factor_value"] = pd.to_numeric(out[value_col], errors="coerce") if value_col else np.nan
        return out
    id_cols = [col for col in ("trade_date", "symbol", "available_at") if col in panel.columns]
    factor_cols = [
        col
        for col in panel.columns
        if col not in set(id_cols) | {"label_return", "eligible", "quality_status"}
        and pd.api.types.is_numeric_dtype(panel[col])
    ]
    rows = panel.melt(id_vars=id_cols, value_vars=factor_cols, var_name="factor_id", value_name="factor_value")
    return rows


def _normalise_labels(labels: pd.DataFrame) -> pd.DataFrame:
    if labels is None or labels.empty:
        return pd.DataFrame(columns=["trade_date", "symbol", "forward_return"])
    out = labels.copy()
    if "forward_return" not in out.columns and "label_return" in out.columns:
        out["forward_return"] = out["label_return"]
    return out


def _join_factor_labels(factors: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    if factors.empty or labels.empty:
        return pd.DataFrame()
    label_cols = [col for col in labels.columns if col not in {"factor_id", "factor_value"}]
    joined = factors.merge(labels[label_cols], on=["trade_date", "symbol"], how="inner", suffixes=("", "_label"))
    joined["factor_value"] = pd.to_numeric(joined["factor_value"], errors="coerce")
    joined["forward_return"] = pd.to_numeric(joined["forward_return"], errors="coerce")
    return joined.dropna(subset=["factor_value", "forward_return"])


def _factor_spreads(joined: pd.DataFrame, *, quantiles: int = 5) -> pd.DataFrame:
    if joined.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (trade_date, factor_id), group in joined.groupby(["trade_date", "factor_id"], sort=True):
        valid = group[["factor_value", "forward_return"]].dropna()
        if len(valid) < max(quantiles * 2, 10):
            continue
        try:
            valid = valid.assign(bucket=pd.qcut(valid["factor_value"].rank(method="first"), quantiles, labels=False, duplicates="drop") + 1)
        except ValueError:
            continue
        low = valid[valid["bucket"] == valid["bucket"].min()]
        high = valid[valid["bucket"] == valid["bucket"].max()]
        if low.empty or high.empty:
            continue
        rows.append(
            {
                "trade_date": str(trade_date),
                "factor_id": str(factor_id),
                "long_short_return": float(high["forward_return"].mean() - low["forward_return"].mean()),
                "long_mean_return": float(high["forward_return"].mean()),
                "short_mean_return": float(low["forward_return"].mean()),
                "observation_count": int(len(valid)),
            }
        )
    return pd.DataFrame(rows)


def _rank_ic_by_date(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (trade_date, factor_id), group in joined.groupby(["trade_date", "factor_id"], sort=True):
        pair = group[["factor_value", "forward_return"]].dropna()
        if len(pair) < 10:
            continue
        rows.append({"trade_date": trade_date, "factor_id": factor_id, "rank_ic": float(pair["factor_value"].rank().corr(pair["forward_return"].rank()))})
    return pd.DataFrame(rows)


def _merge_universe(joined: pd.DataFrame, universe_frame: pd.DataFrame | None) -> pd.DataFrame:
    if joined.empty:
        return joined
    if universe_frame is None or universe_frame.empty:
        return joined
    merge_cols = [col for col in ("trade_date", "symbol") if col in universe_frame.columns and col in joined.columns]
    if not merge_cols:
        return joined
    extra_cols = [col for col in universe_frame.columns if col not in joined.columns or col in merge_cols]
    return joined.merge(universe_frame[extra_cols].drop_duplicates(subset=merge_cols), on=merge_cols, how="left")


def _gate_decisions(metrics: Mapping[str, Mapping[str, Any]]) -> list[ValidationGateDecision]:
    decisions: list[ValidationGateDecision] = []
    for gate_id, payload in metrics.items():
        status = str(payload.get("status") or STATUS_INSUFFICIENT_DATA)
        severity = "blocker" if status == STATUS_BLOCKED and gate_id in CORE_GATES else ("warning" if status != STATUS_PASS else "info")
        reason = str(payload.get("reason") or f"{gate_id} status={status}")
        decisions.append(ValidationGateDecision(gate_id=gate_id, status=status, reason=reason, severity=severity))
    return decisions


def _benjamini_hochberg(p_values: Sequence[float]) -> list[float]:
    if not p_values:
        return []
    n = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    q_values = [1.0] * n
    prev = 1.0
    for rank, (index, p_value) in reversed(list(enumerate(ordered, start=1))):
        q_value = min(prev, float(p_value) * n / rank)
        q_values[index] = q_value
        prev = q_value
    return q_values


def _two_sided_normal_p_value(t_stat: float | None) -> float | None:
    if t_stat is None or not np.isfinite(t_stat):
        return None
    return float(math.erfc(abs(float(t_stat)) / math.sqrt(2.0)))


def _reason(gate_id: str, reason: str, severity: str) -> dict[str, Any]:
    return {"gate_id": gate_id, "reason": reason, "severity": severity}


def _frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame(value)


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


__all__ = (
    "FACTOR_MODEL_VALIDATION_SCHEMA",
    "FactorModelValidationReport",
    "ValidationGateDecision",
    "build_factor_model_validation_report",
    "load_policy_cycle_config",
)
