"""动量策略信号。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math

import pandas as pd


class MomentumSignalError(ValueError):
    """动量信号参数或输入非法。"""


@dataclass(frozen=True, slots=True)
class MomentumConfig:
    lookback_days: int = 20
    top_fraction: float = 0.1
    sell_buffer: float = 0.0


@dataclass(frozen=True, slots=True)
class MomentumSignal:
    signal_date: date
    target_symbols: list[str]
    scores: dict[str, float]


def rank_momentum(close_df: pd.DataFrame, signal_date: date, config: MomentumConfig) -> MomentumSignal:
    """按 `close[T]/close[T-lookback]-1` 生成目标股票集合。"""

    if config.lookback_days <= 0:
        raise MomentumSignalError("lookback_days 必须为正数")
    if not 0 < config.top_fraction <= 1:
        raise MomentumSignalError("top_fraction 必须在 (0, 1] 内")
    if signal_date not in close_df.index:
        raise MomentumSignalError(f"signal_date 不在 close_df: {signal_date}")
    index = list(close_df.index)
    position = index.index(signal_date)
    if position < config.lookback_days:
        raise MomentumSignalError("信号日不足 warm-up")
    current = close_df.iloc[position]
    previous = close_df.iloc[position - config.lookback_days]
    momentum = (current / previous) - 1.0
    momentum = momentum.replace([float("inf"), -float("inf")], pd.NA).dropna()
    if momentum.empty:
        return MomentumSignal(signal_date=signal_date, target_symbols=[], scores={})
    ranked = sorted(
        ((str(symbol), float(score)) for symbol, score in momentum.items()),
        key=lambda item: (-item[1], item[0]),
    )
    top_count = max(1, math.ceil(len(ranked) * config.top_fraction))
    target_symbols = [symbol for symbol, _ in ranked[:top_count]]
    return MomentumSignal(
        signal_date=signal_date,
        target_symbols=target_symbols,
        scores={symbol: score for symbol, score in ranked},
    )


def build_momentum_targets(
    close_df: pd.DataFrame,
    signal_date: date,
    config: MomentumConfig,
    *,
    current_holdings: list[str] | None = None,
) -> MomentumSignal:
    """生成动量目标持仓，支持“跌出缓冲区再卖出”的调仓规则。"""

    signal = rank_momentum(close_df, signal_date, config)
    if config.sell_buffer <= 0 or not current_holdings:
        return signal
    ranked_symbols = list(signal.scores)
    target_symbols = apply_sell_buffer(
        ranked_symbols,
        signal.target_symbols,
        current_holdings,
        config.sell_buffer,
    )
    return MomentumSignal(
        signal_date=signal.signal_date,
        target_symbols=target_symbols,
        scores=signal.scores,
    )


def apply_sell_buffer(
    ranked_symbols: list[str],
    target_symbols: list[str],
    current_holdings: list[str],
    sell_buffer: float,
) -> list[str]:
    """保留位于 top_count*(1+sell_buffer) 边界内的既有持仓。"""

    if sell_buffer < 0:
        raise MomentumSignalError("sell_buffer 不得为负")
    if not target_symbols:
        return []
    boundary = max(len(target_symbols), math.ceil(len(target_symbols) * (1 + sell_buffer)))
    keep_zone = set(ranked_symbols[:boundary])
    targets = set(target_symbols)
    targets.update(symbol for symbol in current_holdings if symbol in keep_zone)
    return sorted(targets, key=lambda symbol: ranked_symbols.index(symbol) if symbol in ranked_symbols else len(ranked_symbols))


__all__ = (
    "MomentumConfig",
    "MomentumSignal",
    "MomentumSignalError",
    "apply_sell_buffer",
    "build_momentum_targets",
    "rank_momentum",
)
