"""通用因子排序检验与统计工具。"""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


def build_forward_return_matrix(
    close: pd.DataFrame,
    *,
    horizon: int,
    daily_returns: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if horizon <= 0:
        raise ValueError("horizon 必须为正数")
    if daily_returns is not None:
        growth = (1.0 + daily_returns).shift(-1)
        return growth.rolling(horizon, min_periods=horizon).apply(np.prod, raw=True).shift(-(horizon - 1)) - 1.0
    return close.shift(-horizon) / close - 1.0


def single_sort_returns(
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    weights: pd.DataFrame | None = None,
    weight_method: str = "equal",
    quantiles: int = 10,
    min_cross_section: int = 10,
) -> pd.DataFrame:
    if quantiles < 2:
        raise ValueError("quantiles 必须至少为 2")
    rows: list[dict[str, Any]] = []
    aligned_weights = weights.reindex(index=factor.index, columns=factor.columns) if weights is not None else None
    for trade_date in factor.index.intersection(forward_returns.index):
        valid = pd.DataFrame({"factor": factor.loc[trade_date], "forward_return": forward_returns.loc[trade_date]})
        if aligned_weights is not None:
            valid["weight"] = aligned_weights.loc[trade_date]
        valid = valid.dropna(subset=["factor", "forward_return"])
        if len(valid) < max(quantiles, min_cross_section):
            continue
        valid["group"] = _quantile_groups(valid["factor"], quantiles)
        for group_id, group in valid.dropna(subset=["group"]).groupby("group", sort=True):
            rows.append(
                {
                    "trade_date": _iso_date(trade_date),
                    "group": int(group_id),
                    "mean_forward_return": _weighted_average(group, weight_method=weight_method),
                    "symbol_count": int(len(group)),
                    "weight_method": weight_method,
                }
            )
    return pd.DataFrame(rows)


def independent_double_sort_returns(
    factor: pd.DataFrame,
    size: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    weights: pd.DataFrame | None = None,
    weight_method: str = "equal",
    groups: int = 5,
    min_cross_section: int = 25,
) -> pd.DataFrame:
    if groups < 2:
        raise ValueError("groups 必须至少为 2")
    rows: list[dict[str, Any]] = []
    aligned_weights = weights.reindex(index=factor.index, columns=factor.columns) if weights is not None else None
    common_dates = factor.index.intersection(size.index).intersection(forward_returns.index)
    for trade_date in common_dates:
        valid = pd.DataFrame(
            {
                "factor": factor.loc[trade_date],
                "size": size.loc[trade_date],
                "forward_return": forward_returns.loc[trade_date],
            }
        )
        if aligned_weights is not None:
            valid["weight"] = aligned_weights.loc[trade_date]
        valid = valid.dropna(subset=["factor", "size", "forward_return"])
        if len(valid) < min_cross_section:
            continue
        valid["size_group"] = _quantile_groups(valid["size"], groups)
        valid["factor_group"] = _quantile_groups(valid["factor"], groups)
        valid = valid.dropna(subset=["size_group", "factor_group"])
        for (size_group, factor_group), group in valid.groupby(["size_group", "factor_group"], sort=True):
            rows.append(
                {
                    "trade_date": _iso_date(trade_date),
                    "size_group": int(size_group),
                    "factor_group": int(factor_group),
                    "mean_forward_return": _weighted_average(group, weight_method=weight_method),
                    "symbol_count": int(len(group)),
                    "weight_method": weight_method,
                }
            )
    return pd.DataFrame(rows)


def conditional_double_sort_returns(
    conditioning_factor: pd.DataFrame,
    factor: pd.DataFrame,
    forward_returns: pd.DataFrame,
    *,
    weights: pd.DataFrame | None = None,
    weight_method: str = "equal",
    groups: int = 5,
    min_cross_section: int = 25,
) -> pd.DataFrame:
    if groups < 2:
        raise ValueError("groups 必须至少为 2")
    rows: list[dict[str, Any]] = []
    aligned_weights = weights.reindex(index=factor.index, columns=factor.columns) if weights is not None else None
    common_dates = conditioning_factor.index.intersection(factor.index).intersection(forward_returns.index)
    for trade_date in common_dates:
        valid = pd.DataFrame(
            {
                "conditioning_factor": conditioning_factor.loc[trade_date],
                "factor": factor.loc[trade_date],
                "forward_return": forward_returns.loc[trade_date],
            }
        )
        if aligned_weights is not None:
            valid["weight"] = aligned_weights.loc[trade_date]
        valid = valid.dropna(subset=["conditioning_factor", "factor", "forward_return"])
        if len(valid) < min_cross_section:
            continue
        valid["conditioning_group"] = _quantile_groups(valid["conditioning_factor"], groups)
        valid = valid.dropna(subset=["conditioning_group"])
        for conditioning_group, outer in valid.groupby("conditioning_group", sort=True):
            outer = outer.copy()
            outer["factor_group"] = _quantile_groups(outer["factor"], groups)
            for factor_group, group in outer.dropna(subset=["factor_group"]).groupby("factor_group", sort=True):
                rows.append(
                    {
                        "trade_date": _iso_date(trade_date),
                        "conditioning_group": int(conditioning_group),
                        "factor_group": int(factor_group),
                        "mean_forward_return": _weighted_average(group, weight_method=weight_method),
                        "symbol_count": int(len(group)),
                        "weight_method": weight_method,
                    }
                )
    return pd.DataFrame(rows)


def long_short_summary(
    group_returns: pd.DataFrame,
    *,
    high_minus_low: bool = True,
    t_stat_method: str = "newey_west",
    newey_west_lags: int | None = None,
) -> dict[str, Any]:
    if group_returns.empty:
        return {"status": "missing", "mean": None, "t_stat": None, "observation_count": 0}
    pivot = group_returns.pivot_table(index="trade_date", columns="group", values="mean_forward_return", aggfunc="mean")
    if pivot.empty:
        return {"status": "missing", "mean": None, "t_stat": None, "observation_count": 0}
    low = int(min(pivot.columns))
    high = int(max(pivot.columns))
    spread = pivot[high] - pivot[low] if high_minus_low else pivot[low] - pivot[high]
    spread = spread.dropna()
    return {
        "status": "pass" if not spread.empty else "missing",
        "mean": _safe_float(spread.mean()) if not spread.empty else None,
        "t_stat": newey_west_t_stat(spread, lags=newey_west_lags) if t_stat_method == "newey_west" else _t_stat(spread),
        "t_stat_method": t_stat_method,
        "observation_count": int(len(spread)),
    }


def long_short_summary_from_double_sort(
    group_returns: pd.DataFrame,
    *,
    outer_group_column: str = "size_group",
    factor_group_column: str = "factor_group",
    high_minus_low: bool = True,
    t_stat_method: str = "newey_west",
    newey_west_lags: int | None = None,
) -> dict[str, Any]:
    required = {"trade_date", outer_group_column, factor_group_column, "mean_forward_return"}
    if group_returns.empty or not required <= set(group_returns.columns):
        return {"status": "missing", "mean": None, "t_stat": None, "observation_count": 0}
    rows: list[dict[str, Any]] = []
    for trade_date, date_group in group_returns.groupby("trade_date", sort=True):
        pivot = date_group.pivot_table(index=outer_group_column, columns=factor_group_column, values="mean_forward_return")
        if pivot.empty:
            continue
        low = int(min(pivot.columns))
        high = int(max(pivot.columns))
        spread_by_outer = pivot[high] - pivot[low] if high_minus_low else pivot[low] - pivot[high]
        rows.append({"trade_date": trade_date, "spread": float(spread_by_outer.dropna().mean())})
    spread = pd.DataFrame(rows).set_index("trade_date")["spread"] if rows else pd.Series(dtype="float64")
    return {
        "status": "pass" if not spread.empty else "missing",
        "mean": _safe_float(spread.mean()) if not spread.empty else None,
        "t_stat": newey_west_t_stat(spread, lags=newey_west_lags) if t_stat_method == "newey_west" else _t_stat(spread),
        "t_stat_method": t_stat_method,
        "observation_count": int(len(spread)),
    }


def newey_west_t_stat(values: pd.Series | Sequence[float], *, lags: int | None = None) -> float | None:
    clean = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    n_obs = len(clean)
    if n_obs < 2:
        return None
    if lags is None:
        lags = int(np.floor(4 * (n_obs / 100.0) ** (2.0 / 9.0)))
    lags = max(0, min(int(lags), n_obs - 1))
    demeaned = clean.to_numpy(dtype="float64") - float(clean.mean())
    gamma0 = float(np.dot(demeaned, demeaned) / n_obs)
    variance = gamma0
    for lag in range(1, lags + 1):
        covariance = float(np.dot(demeaned[lag:], demeaned[:-lag]) / n_obs)
        variance += 2.0 * (1.0 - lag / (lags + 1.0)) * covariance
    if not np.isfinite(variance) or variance <= 0:
        return None
    standard_error = np.sqrt(variance / n_obs)
    if standard_error == 0 or not np.isfinite(standard_error):
        return None
    return float(clean.mean() / standard_error)


def fama_macbeth_regression(
    forward_returns: pd.DataFrame,
    factors: Mapping[str, pd.DataFrame],
    *,
    add_intercept: bool = True,
    min_cross_section: int = 20,
    newey_west_lags: int | None = None,
) -> pd.DataFrame:
    if not factors:
        raise ValueError("factors 不能为空")
    factor_ids = tuple(factors.keys())
    rows: list[dict[str, Any]] = []
    common_dates = forward_returns.index
    for matrix in factors.values():
        common_dates = common_dates.intersection(matrix.index)
    for trade_date in common_dates:
        columns: dict[str, Any] = {"forward_return": forward_returns.loc[trade_date]}
        columns.update({factor_id: factors[factor_id].loc[trade_date] for factor_id in factor_ids})
        cross_section = pd.DataFrame(columns).dropna()
        parameter_count = len(factor_ids) + (1 if add_intercept else 0)
        if len(cross_section) < max(min_cross_section, parameter_count + 1):
            continue
        y = cross_section["forward_return"].to_numpy(dtype="float64")
        x_columns = [cross_section[factor_id].to_numpy(dtype="float64") for factor_id in factor_ids]
        if add_intercept:
            x_columns.insert(0, np.ones(len(cross_section), dtype="float64"))
        x = np.column_stack(x_columns)
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        names = ("intercept",) + factor_ids if add_intercept else factor_ids
        for name, value in zip(names, beta, strict=True):
            rows.append(
                {
                    "trade_date": _iso_date(trade_date),
                    "coefficient": name,
                    "estimate": float(value),
                    "symbol_count": int(len(cross_section)),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["coefficient", "mean_estimate", "t_stat", "observation_count", "newey_west_lags"])
    time_series = pd.DataFrame(rows)
    summary_rows: list[dict[str, Any]] = []
    for coefficient, group in time_series.groupby("coefficient", sort=False):
        estimates = group["estimate"]
        summary_rows.append(
            {
                "coefficient": coefficient,
                "mean_estimate": float(estimates.mean()),
                "t_stat": newey_west_t_stat(estimates, lags=newey_west_lags),
                "observation_count": int(estimates.notna().sum()),
                "newey_west_lags": newey_west_lags,
            }
        )
    return pd.DataFrame(summary_rows)


def _quantile_groups(values: pd.Series, groups: int) -> pd.Series:
    ranks = values.rank(method="first")
    if ranks.notna().sum() < groups:
        return pd.Series(index=values.index, dtype="float64")
    try:
        labels = pd.qcut(ranks, groups, labels=False, duplicates="drop")
    except ValueError:
        return pd.Series(index=values.index, dtype="float64")
    return pd.Series(labels, index=values.index, dtype="float64") + 1


def _t_stat(values: pd.Series) -> float | None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if len(clean) < 2:
        return None
    std = clean.std(ddof=1)
    if not np.isfinite(std) or std == 0:
        return None
    return float(clean.mean() / (std / np.sqrt(len(clean))))


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _iso_date(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _weighted_average(group: pd.DataFrame, *, weight_method: str) -> float:
    if weight_method == "equal" or "weight" not in group.columns:
        return float(group["forward_return"].mean())
    if weight_method not in {"value", "market_cap"}:
        raise ValueError("weight_method 只能是 equal/value/market_cap")
    weights = pd.to_numeric(group["weight"], errors="coerce").where(lambda item: item > 0)
    values = pd.to_numeric(group["forward_return"], errors="coerce")
    valid = values.notna() & weights.notna()
    if not valid.any() or weights.loc[valid].sum() == 0:
        return float(values.mean())
    return float((values.loc[valid] * weights.loc[valid]).sum() / weights.loc[valid].sum())
