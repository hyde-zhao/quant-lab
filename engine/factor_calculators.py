"""通用权益因子矩阵计算工具。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS, equity_core_factor_definitions


FACTOR_CALCULATOR_SCHEMA = "factor_calculator_v1"
FactorCalculator = Callable[["FactorCalculationContext"], pd.DataFrame | None]


@dataclass(frozen=True, slots=True)
class FactorCalculationContext:
    close: pd.DataFrame
    returns: pd.DataFrame
    price_frame: pd.DataFrame
    market_cap_matrix: pd.DataFrame | None
    turnover_matrix: pd.DataFrame | None
    financial_daily: Mapping[str, pd.DataFrame]
    min_period_ratio: float

    @property
    def calendar(self) -> list[Any]:
        return list(self.close.index)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(str(item) for item in self.close.columns)


@dataclass(frozen=True, slots=True)
class FactorMatrixResult:
    raw_matrices: dict[str, pd.DataFrame]
    directional_matrices: dict[str, pd.DataFrame]
    winsorized_matrices: dict[str, pd.DataFrame]
    zscore_matrices: dict[str, pd.DataFrame]
    market_factor_return: pd.Series
    preprocessing_summary: pd.DataFrame
    limitations: tuple[str, ...]
    schema_version: str = FACTOR_CALCULATOR_SCHEMA


def compute_equity_factor_matrices(
    *,
    close: pd.DataFrame,
    returns: pd.DataFrame,
    price_frame: pd.DataFrame,
    market_cap_matrix: pd.DataFrame | None = None,
    turnover_matrix: pd.DataFrame | None = None,
    financial_daily: Mapping[str, pd.DataFrame] | None = None,
    factor_ids: Sequence[str] = DEFAULT_EQUITY_CORE_FACTOR_IDS,
    calculator_registry: Mapping[str, FactorCalculator] | None = None,
    eligibility_mask: pd.DataFrame | None = None,
    winsor_limits: tuple[float, float] = (0.01, 0.99),
    min_period_ratio: float = 2.0 / 3.0,
    min_cross_section: int = 5,
) -> FactorMatrixResult:
    """计算通用权益因子矩阵。

    调用方负责提供已经离线准备好的价格、收益、股票池和可交易性矩阵。
    本函数不读取凭据、不抓取 provider、不写 lake。
    """

    if not 0 <= winsor_limits[0] < winsor_limits[1] <= 1:
        raise ValueError("winsor_limits 必须满足 0 <= lower < upper <= 1")
    if not 0 < min_period_ratio <= 1:
        raise ValueError("min_period_ratio 必须在 (0, 1] 内")
    if min_cross_section < 2:
        raise ValueError("min_cross_section 必须至少为 2")

    calendar = list(close.index)
    symbols = tuple(str(item) for item in close.columns)
    financial_daily = financial_daily or {}
    requested = set(factor_ids)
    context = FactorCalculationContext(
        close=close,
        returns=returns,
        price_frame=price_frame,
        market_cap_matrix=market_cap_matrix,
        turnover_matrix=turnover_matrix,
        financial_daily=financial_daily,
        min_period_ratio=min_period_ratio,
    )
    market_factor_return = _market_return(returns, market_cap_matrix)

    raw: dict[str, pd.DataFrame] = {}
    limitations: list[str] = []
    calculators = dict(core_equity_factor_calculators())
    if calculator_registry:
        calculators.update(calculator_registry)

    for factor_id in factor_ids:
        calculator = calculators.get(factor_id)
        if calculator is None:
            limitations.append(f"{factor_id} 缺 calculator，无法计算。")
            continue
        matrix = calculator(context)
        if matrix is None:
            limitations.append(_missing_input_message(factor_id))
            continue
        raw[factor_id] = matrix

    if eligibility_mask is not None:
        eligibility = eligibility_mask.reindex(index=calendar, columns=symbols, fill_value=False).astype(bool)
        raw = {factor_id: matrix.reindex(index=calendar, columns=symbols).where(eligibility) for factor_id, matrix in raw.items()}

    direction_by_factor = {item.factor_id: item.direction for item in equity_core_factor_definitions()}
    directional = {
        factor_id: _apply_direction(matrix, direction_by_factor.get(factor_id, "positive"))
        for factor_id, matrix in raw.items()
    }
    winsorized, zscores, summary = preprocess_factor_matrices(
        directional,
        winsor_limits=winsor_limits,
        min_cross_section=min_cross_section,
    )

    return FactorMatrixResult(
        raw_matrices=raw,
        directional_matrices=directional,
        winsorized_matrices=winsorized,
        zscore_matrices=zscores,
        market_factor_return=market_factor_return,
        preprocessing_summary=summary,
        limitations=tuple(limitations),
    )


def core_equity_factor_calculators() -> dict[str, FactorCalculator]:
    return {
        "market_beta_252": _calculate_market_beta_252,
        "size_total_market_cap": _calculate_size_total_market_cap,
        "value_bm": _calculate_value_bm,
        "momentum_12_1": _calculate_momentum_12_1,
        "profitability_roe_ttm": _calculate_profitability_roe_ttm,
        "investment_asset_growth": _calculate_investment_asset_growth,
        "abnormal_turnover_21_252": _calculate_abnormal_turnover_21_252,
    }


def _calculate_market_beta_252(context: FactorCalculationContext) -> pd.DataFrame | None:
    market_return = _market_return(context.returns, context.market_cap_matrix)
    return _rolling_beta(context.returns, market_return, window=252, min_period_ratio=context.min_period_ratio)


def _calculate_size_total_market_cap(context: FactorCalculationContext) -> pd.DataFrame | None:
    if context.market_cap_matrix is None:
        return None
    return np.log(context.market_cap_matrix.where(context.market_cap_matrix > 0))


def _calculate_value_bm(context: FactorCalculationContext) -> pd.DataFrame | None:
    return _bm_matrix(
        context.price_frame,
        context.market_cap_matrix,
        context.financial_daily,
        context.calendar,
        context.symbols,
    )


def _calculate_momentum_12_1(context: FactorCalculationContext) -> pd.DataFrame | None:
    return context.close.shift(21) / context.close.shift(252) - 1.0


def _calculate_profitability_roe_ttm(context: FactorCalculationContext) -> pd.DataFrame | None:
    return _roe_ttm_matrix(context.financial_daily)


def _calculate_investment_asset_growth(context: FactorCalculationContext) -> pd.DataFrame | None:
    return _asset_growth_matrix(context.financial_daily)


def _calculate_abnormal_turnover_21_252(context: FactorCalculationContext) -> pd.DataFrame | None:
    if context.turnover_matrix is None:
        return None
    return calculate_abnormal_turnover_21_252(
        context.turnover_matrix,
        min_period_ratio=context.min_period_ratio,
    )


def calculate_abnormal_turnover_21_252(
    turnover_matrix: pd.DataFrame,
    *,
    short_window: int = 21,
    long_window: int = 252,
    short_min_periods: int | None = None,
    long_min_periods: int | None = None,
    min_period_ratio: float = 2.0 / 3.0,
    clip_bounds: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """计算 abnormal turnover 矩阵，不读取外部数据。"""

    if short_min_periods is None:
        short_min_periods = _window_min_periods(short_window, min_period_ratio)
    if long_min_periods is None:
        long_min_periods = _window_min_periods(long_window, min_period_ratio)
    result = (
        turnover_matrix.rolling(short_window, min_periods=short_min_periods).mean()
        / turnover_matrix.rolling(long_window, min_periods=long_min_periods).mean()
    )
    if clip_bounds is not None:
        result = result.clip(lower=clip_bounds[0], upper=clip_bounds[1])
    return result


def _missing_input_message(factor_id: str) -> str:
    messages = {
        "size_total_market_cap": "size_total_market_cap 缺 market_cap，无法复刻。",
        "value_bm": "value_bm 缺 book_equity/book_to_market 或 market_cap，无法复刻。",
        "profitability_roe_ttm": "profitability_roe_ttm 缺 roe_ttm 或 operating_profit_ttm/book_equity，无法复刻。",
        "investment_asset_growth": "investment_asset_growth 缺 total_assets/asset_growth，无法复刻。",
        "abnormal_turnover_21_252": "abnormal_turnover_21_252 缺 turnover_rate，无法复刻。",
    }
    return messages.get(factor_id, f"{factor_id} 缺必要输入，无法计算。")


def factor_matrices_to_panel(
    result: FactorMatrixResult | Any,
    *,
    source_dataset: str = "research_input_v1",
    factor_version: str = "v1",
    quality_status: str = "pass",
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for factor_id, raw in result.raw_matrices.items():
        directional = result.directional_matrices[factor_id]
        winsorized = result.winsorized_matrices[factor_id]
        zscore = result.zscore_matrices[factor_id]
        merged: pd.DataFrame | None = None
        for value_name, matrix in (
            ("raw_value", raw),
            ("directional_value", directional),
            ("winsorized_value", winsorized),
            ("zscore_value", zscore),
        ):
            long = _stack_matrix(matrix, value_name)
            long.columns = ["trade_date", "symbol", value_name]
            if merged is None:
                merged = long
            else:
                merged = merged.merge(long, on=["trade_date", "symbol"], how="left")
        if merged is None:
            continue
        merged["factor_id"] = factor_id
        merged["factor_version"] = factor_version
        merged["source_dataset"] = source_dataset
        merged["quality_status"] = quality_status
        rows.append(merged)
    if not rows:
        return pd.DataFrame(
            columns=[
                "trade_date",
                "symbol",
                "raw_value",
                "directional_value",
                "winsorized_value",
                "zscore_value",
                "factor_id",
                "factor_version",
                "source_dataset",
                "quality_status",
            ]
        )
    return pd.concat(rows, ignore_index=True)


def preprocess_factor_matrices(
    directional: Mapping[str, pd.DataFrame],
    *,
    winsor_limits: tuple[float, float],
    min_cross_section: int,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    winsorized: dict[str, pd.DataFrame] = {}
    zscores: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    lower_q, upper_q = winsor_limits
    for factor_id, matrix in directional.items():
        valid_counts = matrix.notna().sum(axis=1)
        valid_rows = valid_counts >= min_cross_section
        lower = matrix.quantile(lower_q, axis=1)
        upper = matrix.quantile(upper_q, axis=1)
        clipped = matrix.clip(lower=lower, upper=upper, axis=0)
        clipped.loc[~valid_rows, :] = np.nan
        means = clipped.mean(axis=1, skipna=True)
        stds = clipped.std(axis=1, ddof=0, skipna=True).replace(0, np.nan)
        zscore = clipped.sub(means, axis=0).div(stds, axis=0)
        zscore.loc[~valid_rows, :] = np.nan
        winsorized[factor_id] = clipped
        zscores[factor_id] = zscore
        rows.append(
            {
                "factor_id": factor_id,
                "date_count": int(matrix.shape[0]),
                "symbol_count": int(matrix.shape[1]),
                "valid_date_count": int(valid_rows.sum()),
                "raw_observation_count": int(matrix.notna().sum().sum()),
                "zscore_observation_count": int(zscore.notna().sum().sum()),
                "winsor_lower": lower_q,
                "winsor_upper": upper_q,
                "min_cross_section": min_cross_section,
            }
        )
    return winsorized, zscores, pd.DataFrame(rows)


def _market_return(returns: pd.DataFrame, market_cap: pd.DataFrame | None) -> pd.Series:
    if market_cap is None:
        return returns.mean(axis=1, skipna=True).rename("market_return")
    weights = market_cap.shift(1).reindex_like(returns)
    weights = weights.where(weights > 0)
    weighted = returns * weights
    return (weighted.sum(axis=1, skipna=True) / weights.where(returns.notna()).sum(axis=1, skipna=True)).rename("market_return")


def _rolling_beta(
    returns: pd.DataFrame,
    market_return: pd.Series,
    *,
    window: int,
    min_period_ratio: float,
) -> pd.DataFrame:
    min_periods = _window_min_periods(window, min_period_ratio)
    market = market_return.reindex(returns.index)
    variance = market.rolling(window, min_periods=min_periods).var(ddof=0)
    beta = pd.DataFrame(index=returns.index, columns=returns.columns, dtype="float64")
    for symbol in returns.columns:
        covariance = returns[symbol].rolling(window, min_periods=min_periods).cov(market, ddof=0)
        beta[symbol] = covariance / variance
    return beta


def _bm_matrix(
    price_frame: pd.DataFrame,
    market_cap: pd.DataFrame | None,
    financial_daily: Mapping[str, pd.DataFrame],
    calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame | None:
    direct_column = _first_existing(price_frame, ("book_to_market", "bm", "book_equity_to_market"))
    if direct_column is not None:
        return _pivot_numeric(price_frame, direct_column, trade_calendar=list(calendar), symbols=symbols)
    book = _first_existing_matrix(financial_daily, ("book_equity", "total_equity", "net_assets", "total_hldr_eqy_exc_min_int"))
    if book is None or market_cap is None:
        return None
    return book / market_cap.replace(0, np.nan)


def _roe_ttm_matrix(financial_daily: Mapping[str, pd.DataFrame]) -> pd.DataFrame | None:
    direct = _first_existing_matrix(financial_daily, ("roe_ttm", "chapter3_roe_ttm", "roe"))
    if direct is not None:
        return direct
    profit = _first_existing_matrix(financial_daily, ("operating_profit_ttm", "operate_profit_ttm", "net_profit_ttm"))
    book = _first_existing_matrix(
        financial_daily,
        (
            "chapter3_book_equity_avg4q",
            "book_equity_avg_4q",
            "book_equity_mean_4q",
            "book_equity",
            "total_equity",
            "net_assets",
            "total_hldr_eqy_exc_min_int",
        ),
    )
    if profit is None or book is None:
        return None
    return profit / book.replace(0, np.nan)


def _asset_growth_matrix(financial_daily: Mapping[str, pd.DataFrame]) -> pd.DataFrame | None:
    direct = _first_existing_matrix(
        financial_daily,
        ("asset_growth", "chapter3_annual_asset_growth", "total_assets_growth", "total_asset_growth"),
    )
    if direct is not None:
        return direct
    assets = _first_existing_matrix(financial_daily, ("total_assets", "total_asset"))
    if assets is None:
        return None
    return assets / assets.shift(252) - 1.0


def _first_existing_matrix(financial_daily: Mapping[str, pd.DataFrame], names: Sequence[str]) -> pd.DataFrame | None:
    for name in names:
        matrix = financial_daily.get(name)
        if matrix is not None:
            return matrix
    return None


def _apply_direction(matrix: pd.DataFrame, direction: str) -> pd.DataFrame:
    if direction == "negative":
        return -matrix
    return matrix.copy()


def _pivot_numeric(
    frame: pd.DataFrame,
    value_column: str,
    *,
    trade_calendar: Sequence[Any],
    symbols: Sequence[str],
) -> pd.DataFrame:
    work = frame.copy()
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce")
    matrix = work.pivot_table(index="trade_date", columns="symbol", values=value_column, aggfunc="last")
    matrix = matrix.reindex(index=list(trade_calendar), columns=list(symbols)).sort_index()
    matrix.columns = [str(column) for column in matrix.columns]
    return matrix


def _first_existing(frame: pd.DataFrame, columns: Sequence[str]) -> str | None:
    for column in columns:
        if column in frame.columns:
            return column
    return None


def _window_min_periods(window: int, min_period_ratio: float) -> int:
    return max(1, int(np.ceil(window * min_period_ratio)))


def _stack_matrix(matrix: pd.DataFrame, value_name: str) -> pd.DataFrame:
    try:
        return matrix.stack(future_stack=True).rename(value_name).reset_index()
    except TypeError:
        return matrix.stack(dropna=False).rename(value_name).reset_index()
