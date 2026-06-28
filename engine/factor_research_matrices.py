"""Shared matrix and cross-sectional transforms for factor research."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def panel_to_matrix(
    panel: pd.DataFrame,
    *,
    value_column: str,
    date_column: str = "trade_date",
    symbol_column: str = "symbol",
) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    required = {date_column, symbol_column, value_column}
    missing = required.difference(panel.columns)
    if missing:
        raise ValueError(f"panel missing required columns: {sorted(missing)}")
    matrix = panel.pivot_table(
        index=date_column,
        columns=symbol_column,
        values=value_column,
        aggfunc="last",
    )
    matrix = matrix.sort_index()
    matrix.columns = matrix.columns.astype(str)
    return matrix


def matrices_to_panel(
    matrices: dict[str, pd.DataFrame],
    *,
    value_name: str = "value",
    date_name: str = "trade_date",
    symbol_name: str = "symbol",
    name_column: str = "factor_id",
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for name, matrix in matrices.items():
        if matrix.empty:
            continue
        frame = matrix.stack(dropna=False).rename(value_name).reset_index()
        frame.columns = [date_name, symbol_name, value_name]
        frame[name_column] = name
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=[date_name, symbol_name, value_name, name_column])
    return pd.concat(frames, ignore_index=True)


def cross_sectional_winsorize(frame: pd.DataFrame, lower: float = 0.01, upper: float = 0.99) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    low = frame.quantile(lower, axis=1)
    high = frame.quantile(upper, axis=1)
    return frame.clip(lower=low, upper=high, axis=0)


def cross_sectional_zscore(frame: pd.DataFrame, *, ddof: int = 1) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    mean = frame.mean(axis=1)
    std = frame.std(axis=1, ddof=ddof).replace(0, np.nan)
    return frame.sub(mean, axis=0).div(std, axis=0)


def quantile_groups(values: pd.Series, quantiles: int = 5, *, require_full_count: bool = False) -> pd.Series:
    ranked = values.rank(method="first")
    valid = ranked.dropna()
    if valid.empty or (require_full_count and len(valid) < quantiles):
        return pd.Series(index=values.index, dtype="float64")
    groups = pd.qcut(valid, q=min(quantiles, len(valid)), labels=False, duplicates="drop")
    result = pd.Series(index=values.index, dtype="float64")
    result.loc[groups.index] = groups.astype(float) + 1.0
    return result


def align_matrices(matrices: Iterable[pd.DataFrame]) -> list[pd.DataFrame]:
    matrices = [matrix.copy() for matrix in matrices]
    if not matrices:
        return []
    common_index = matrices[0].index
    common_columns = matrices[0].columns
    for matrix in matrices[1:]:
        common_index = common_index.intersection(matrix.index)
        common_columns = common_columns.intersection(matrix.columns)
    return [matrix.loc[common_index, common_columns] for matrix in matrices]
