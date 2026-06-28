"""Anomaly research, alpha testing and admission support.

本模块只消费本地第三章因子面板、forward-return 标签和 CR-035 模型收益，
不读取凭据、不触发 provider fetch、不写 data lake、不 publish catalog、
不触发 QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_model_research import labels_to_forward_return_matrix, panel_to_factor_matrices
from engine.factor_research_matrices import (
    cross_sectional_winsorize as _shared_cross_sectional_winsorize,
    cross_sectional_zscore as _shared_cross_sectional_zscore,
    quantile_groups as _shared_quantile_groups,
)
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS
from engine.factor_statistics import newey_west_t_stat
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


CHAPTER5_SCHEMA = "chapter5_anomalies_v1"
ANOMALY_PANEL_SCHEMA = "chapter5_anomaly_panel_v1"
ANOMALY_RETURNS_SCHEMA = "chapter5_anomaly_returns_v1"
ALPHA_TEST_SCHEMA = "chapter5_alpha_tests_v1"
ANOMALY_CANDIDATE_SCHEMA = "anomaly_candidate_v1"
ANOMALY_RESEARCH_REPORT_SCHEMA = "anomaly_research_report_v1"

HARVEY_T_STAT_THRESHOLD = 3.0
CONTROL_ALPHA_T_THRESHOLD = 2.0
TIME_SPLIT_T_THRESHOLD = 2.0
DEFAULT_ONE_WAY_COST_RATE = 0.003

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
    source_type: str = ""
    hypothesis: str = ""
    economic_rationale: str = ""
    prior_logic_ref: str = ""
    a_share_adjustments: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnomalyCandidate:
    anomaly_id: str
    name: str
    source_type: str
    hypothesis: str
    economic_rationale: str
    expected_direction: str
    input_fields: tuple[str, ...]
    required_factor_ids: tuple[str, ...]
    formula: str
    prior_logic_ref: str
    a_share_adjustments: tuple[str, ...]
    schema_version: str = ANOMALY_CANDIDATE_SCHEMA

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
    anomaly_candidates: tuple[dict[str, Any], ...]
    anomaly_research_reports: tuple[dict[str, Any], ...]
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
            "anomaly_candidates": list(self.anomaly_candidates),
            "anomaly_research_reports": list(self.anomaly_research_reports),
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
        source_type="financial_extension",
        hypothesis="估值极端股票可能反映过度定价或深度折价，极端组应呈现可检验的未来收益差异。",
        economic_rationale="估值极端异象需要区分风险补偿与投资者过度反应；A 股中还需控制壳价值和小市值污染。",
        prior_logic_ref="book:factor_investing:chapter5:5.1:valuation_extreme",
        a_share_adjustments=("exclude_smallest_30pct_market_cap", "long_only_feasibility", "policy_cycle_coverage"),
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
        source_type="behavioral_theory",
        hypothesis="价格相对基本面锚点偏离后可能出现反转，投资者锚定和过度反应共同形成收益差异。",
        economic_rationale="该异象应解释为行为偏差而非纯统计巧合，并在控制价值、盈利、投资和动量后仍保留 alpha 才可升级。",
        prior_logic_ref="book:factor_investing:chapter5:5.2:anchor_reversal",
        a_share_adjustments=("exclude_smallest_30pct_market_cap", "long_only_feasibility", "transaction_cost_0_3pct_one_way"),
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
        source_type="risk_theory",
        hypothesis="高特质波动股票可能被投资者偏好彩票型收益而高估，低特质波动组合应有更稳健的风险调整收益。",
        economic_rationale="需要说明该异象是风险约束、行为偏好或交易限制导致，而不是残差估计噪声。",
        prior_logic_ref="book:factor_investing:chapter5:5.3:idiosyncratic_volatility",
        a_share_adjustments=("long_only_feasibility", "policy_cycle_coverage", "transaction_cost_0_3pct_one_way"),
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
    candidates = build_anomaly_candidates(anomalies)
    research_reports = build_anomaly_research_reports(anomaly_returns, alpha_tests, candidates)
    summary = build_anomaly_admission_summary(anomaly_returns, alpha_tests, research_reports=research_reports)
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
        anomaly_candidates=tuple(candidate.to_dict() for candidate in candidates),
        anomaly_research_reports=tuple(research_reports),
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
            group_returns = frame.groupby("group")["forward_return"].mean()
            group_payload = {
                f"group_{index}_mean_return": float(group_returns.get(float(index), np.nan))
                for index in range(1, quantiles + 1)
            }
            monotonicity_score = monotonicity_pass_score(tuple(group_payload.values()))
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
                    "monotonicity_score": monotonicity_score,
                    "monotonicity_pass": bool(monotonicity_score >= 1.0),
                    **group_payload,
                }
            )
    return pd.DataFrame(rows)


def monotonicity_pass_score(group_returns: Sequence[float]) -> float:
    values = pd.to_numeric(pd.Series(tuple(group_returns)), errors="coerce").dropna().to_numpy(dtype="float64")
    if len(values) < 2:
        return 0.0
    diffs = np.diff(values)
    return float((diffs >= 0).sum() / len(diffs))


def build_anomaly_candidates(anomalies: Sequence[AnomalyDefinition]) -> tuple[AnomalyCandidate, ...]:
    candidates: list[AnomalyCandidate] = []
    for anomaly in anomalies:
        if not anomaly.hypothesis or not anomaly.economic_rationale or not anomaly.prior_logic_ref:
            raise ValueError(f"异象候选缺少先验逻辑字段: {anomaly.anomaly_id}")
        candidates.append(
            AnomalyCandidate(
                anomaly_id=anomaly.anomaly_id,
                name=anomaly.name,
                source_type=anomaly.source_type or "unspecified",
                hypothesis=anomaly.hypothesis,
                economic_rationale=anomaly.economic_rationale,
                expected_direction=anomaly.direction,
                input_fields=tuple(anomaly.required_factor_ids),
                required_factor_ids=tuple(anomaly.required_factor_ids),
                formula=anomaly.formula,
                prior_logic_ref=anomaly.prior_logic_ref,
                a_share_adjustments=tuple(anomaly.a_share_adjustments),
            )
        )
    return tuple(candidates)


def build_anomaly_research_reports(
    anomaly_returns: pd.DataFrame,
    alpha_tests: pd.DataFrame,
    candidates: Sequence[AnomalyCandidate],
    *,
    one_way_cost_rate: float = DEFAULT_ONE_WAY_COST_RATE,
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    candidate_by_id = {candidate.anomaly_id: candidate for candidate in candidates}
    for anomaly_id, candidate in candidate_by_id.items():
        group = anomaly_returns[anomaly_returns["anomaly_id"] == anomaly_id] if not anomaly_returns.empty else pd.DataFrame()
        returns = pd.to_numeric(group.get("long_short_return", pd.Series(dtype="float64")), errors="coerce").dropna()
        alpha_group = alpha_tests[alpha_tests["anomaly_id"] == anomaly_id] if not alpha_tests.empty else pd.DataFrame()
        alpha_t = pd.to_numeric(alpha_group.get("alpha_t_stat", pd.Series(dtype="float64")), errors="coerce").dropna()
        t_stat = newey_west_t_stat(returns)
        mean_return = float(returns.mean()) if not returns.empty else None
        monotonicity = pd.to_numeric(group.get("monotonicity_score", pd.Series(dtype="float64")), errors="coerce").dropna()
        monotonicity_score = float(monotonicity.mean()) if not monotonicity.empty else 0.0
        first_t, second_t = time_split_t_stats(group)
        max_abs_alpha_t = float(alpha_t.abs().max()) if not alpha_t.empty else None
        net_return = None if mean_return is None else float(mean_return - 2 * one_way_cost_rate)
        harvey_pass = bool(t_stat is not None and t_stat >= HARVEY_T_STAT_THRESHOLD)
        monotonicity_pass = bool(monotonicity_score >= 1.0)
        alpha_control_pass = bool(max_abs_alpha_t is not None and max_abs_alpha_t >= CONTROL_ALPHA_T_THRESHOLD)
        time_split_pass = bool(
            first_t is not None
            and second_t is not None
            and first_t >= TIME_SPLIT_T_THRESHOLD
            and second_t >= TIME_SPLIT_T_THRESHOLD
        )
        cost_pass = bool(net_return is not None and net_return > 0)
        economic_story_pass = bool(candidate.economic_rationale and candidate.hypothesis)
        decision = anomaly_admission_decision(
            mean_return=mean_return,
            harvey_pass=harvey_pass,
            monotonicity_pass=monotonicity_pass,
            alpha_control_pass=alpha_control_pass,
            time_split_pass=time_split_pass,
            cost_pass=cost_pass,
            economic_story_pass=economic_story_pass,
        )
        reports.append(
            {
                "schema_version": ANOMALY_RESEARCH_REPORT_SCHEMA,
                "anomaly_id": anomaly_id,
                "source_type": candidate.source_type,
                "hypothesis": candidate.hypothesis,
                "economic_rationale": candidate.economic_rationale,
                "prior_logic_ref": candidate.prior_logic_ref,
                "sorting_t_stat": t_stat,
                "harvey_t_threshold": HARVEY_T_STAT_THRESHOLD,
                "harvey_pass": harvey_pass,
                "mean_long_short_return": mean_return,
                "monotonicity_score": monotonicity_score,
                "monotonicity_pass": monotonicity_pass,
                "factor_control_max_abs_alpha_t_stat": max_abs_alpha_t,
                "factor_control_pass": alpha_control_pass,
                "first_half_t_stat": first_t,
                "second_half_t_stat": second_t,
                "time_split_pass": time_split_pass,
                "one_way_cost_rate": float(one_way_cost_rate),
                "net_long_short_return_after_cost": net_return,
                "cost_pass": cost_pass,
                "turnover_status": "insufficient_data",
                "a_share_controls": {
                    "exclude_smallest_30pct_market_cap": "required_before_factor_catalog_candidate",
                    "long_only_test": "required_before_stage3_candidate",
                    "policy_cycle_coverage": "required_before_stage3_candidate",
                    "short_feasibility": "not_applicable_for_long_only_research",
                },
                "economic_story_status": "pass" if economic_story_pass else "blocked",
                "decision": decision,
                "blocked_claims": anomaly_research_blocked_claims(decision),
            }
        )
    return reports


def time_split_t_stats(anomaly_returns: pd.DataFrame) -> tuple[float | None, float | None]:
    if anomaly_returns.empty or "trade_date" not in anomaly_returns:
        return None, None
    work = anomaly_returns.copy()
    work["trade_date_sort"] = pd.to_datetime(work["trade_date"], errors="coerce")
    work = work.sort_values("trade_date_sort")
    returns = pd.to_numeric(work["long_short_return"], errors="coerce").dropna()
    if len(returns) < 4:
        return None, None
    split = len(returns) // 2
    return newey_west_t_stat(returns.iloc[:split]), newey_west_t_stat(returns.iloc[split:])


def anomaly_admission_decision(
    *,
    mean_return: float | None,
    harvey_pass: bool,
    monotonicity_pass: bool,
    alpha_control_pass: bool,
    time_split_pass: bool,
    cost_pass: bool,
    economic_story_pass: bool,
) -> str:
    if mean_return is None:
        return "blocked_no_observations"
    if mean_return <= 0:
        return "reject_or_reweight"
    if not economic_story_pass:
        return "blocked_missing_economic_logic"
    if harvey_pass and monotonicity_pass and alpha_control_pass and time_split_pass and cost_pass:
        return "factor_catalog_candidate"
    if harvey_pass and alpha_control_pass and economic_story_pass:
        return "alpha_feature_candidate"
    return "watch_needs_robustness_review"


def anomaly_research_blocked_claims(decision: str) -> tuple[dict[str, str], ...]:
    claims = [
        {"claim": "qmt_ready", "status": "blocked", "reason": "异象研究不授权 QMT。"},
        {"claim": "simulation_ready", "status": "blocked", "reason": "异象研究不授权 simulation。"},
        {"claim": "live_ready", "status": "blocked", "reason": "异象研究不授权 live。"},
    ]
    if decision != "factor_catalog_candidate":
        claims.append(
            {
                "claim": "factor_catalog_candidate",
                "status": "blocked",
                "reason": "未同时通过 Harvey、单调性、控制因子、时间切分、成本和经济逻辑门禁。",
            }
        )
    return tuple(claims)


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
    *,
    research_reports: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if anomaly_returns.empty:
        return rows
    reports = {str(item.get("anomaly_id")): item for item in (research_reports or ())}
    for anomaly_id, group in anomaly_returns.groupby("anomaly_id", sort=True):
        returns = pd.to_numeric(group["long_short_return"], errors="coerce").dropna()
        alpha_group = alpha_tests[alpha_tests["anomaly_id"] == anomaly_id] if not alpha_tests.empty else pd.DataFrame()
        best_alpha_t = pd.to_numeric(alpha_group.get("alpha_t_stat", pd.Series(dtype="float64")), errors="coerce").dropna()
        t_stat = newey_west_t_stat(returns)
        mean_return = float(returns.mean()) if not returns.empty else None
        report = reports.get(str(anomaly_id), {})
        admission = str(report.get("decision") or anomaly_admission(mean_return, t_stat, best_alpha_t))
        rows.append(
            {
                "anomaly_id": anomaly_id,
                "admission": admission,
                "mean_long_short_return": mean_return,
                "t_stat": t_stat,
                "harvey_pass": bool(report.get("harvey_pass", False)),
                "monotonicity_score": report.get("monotonicity_score"),
                "time_split_pass": bool(report.get("time_split_pass", False)),
                "cost_pass": bool(report.get("cost_pass", False)),
                "economic_story_status": report.get("economic_story_status", ""),
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
    if t_stat is not None and t_stat >= HARVEY_T_STAT_THRESHOLD and (not alpha_t_stats.empty and float(alpha_t_stats.abs().max()) >= CONTROL_ALPHA_T_THRESHOLD):
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
    return _shared_cross_sectional_winsorize(matrix, lower=lower, upper=upper)


def cross_sectional_zscore(matrix: pd.DataFrame) -> pd.DataFrame:
    return _shared_cross_sectional_zscore(matrix, ddof=0)


def quantile_groups(values: pd.Series, groups: int) -> pd.Series:
    try:
        return _shared_quantile_groups(values, groups, require_full_count=True)
    except ValueError:
        return pd.Series(index=values.index, dtype="float64")
