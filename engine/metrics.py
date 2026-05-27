"""回测指标计算。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from engine.portfolio import PortfolioResult


class MetricsError(ValueError):
    """指标计算错误。"""


def calculate_metrics(result: PortfolioResult) -> dict[str, Any]:
    """根据日度净值快照计算收益、回撤、Sharpe 和换手。"""

    if not result.daily_snapshots:
        raise MetricsError("PortfolioResult 缺少 daily_snapshots")
    values = pd.Series(
        [snapshot.total_value for snapshot in result.daily_snapshots],
        index=[snapshot.trade_date for snapshot in result.daily_snapshots],
        dtype="float64",
    )
    validate_nav_integrity(values)
    initial = float(values.iloc[0])
    final = float(values.iloc[-1])
    daily_returns = values.pct_change().dropna()
    total_return = final / initial - 1.0 if initial else 0.0
    years = max(len(values) / 252.0, 1 / 252.0)
    annual_return = (final / initial) ** (1 / years) - 1.0 if initial > 0 else None
    drawdown = values / values.cummax() - 1.0
    std = float(daily_returns.std(ddof=0)) if not daily_returns.empty else 0.0
    sharpe = None if std == 0 else float(daily_returns.mean() / std * (252 ** 0.5))
    turnover = result.turnover_amount / max(initial, 1.0)
    return {
        "total_return": total_return,
        "cumulative_return": total_return,
        "annual_return": annual_return,
        "max_drawdown": float(drawdown.min()),
        "sharpe": sharpe,
        "turnover": turnover,
        "final_nav": final,
        "final_value": final,
    }


def validate_nav_integrity(values: pd.Series) -> None:
    """校验净值序列为正且无缺失。"""

    if values.empty:
        raise MetricsError("净值序列为空")
    if values.isna().any():
        raise MetricsError("净值序列包含空值")
    if (values <= 0).any():
        raise MetricsError("净值序列必须为正")


__all__ = ("MetricsError", "calculate_metrics", "validate_nav_integrity")
