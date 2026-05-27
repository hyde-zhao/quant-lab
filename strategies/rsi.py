"""RSI 示例策略。"""

from __future__ import annotations

import pandas as pd

from strategies.base import StrategyInput, StrategyParameterError, StrategyResult, select_top


def run_rsi_strategy(strategy_input: StrategyInput) -> StrategyResult:
    period = int(strategy_input.params.get("period", 14))
    top_fraction = float(strategy_input.params.get("top_fraction", strategy_input.params.get("fraction", 0.1)))
    oversold = float(strategy_input.params.get("oversold", strategy_input.params.get("buy_threshold", 30)))
    overbought = float(strategy_input.params.get("overbought", strategy_input.params.get("sell_threshold", 70)))
    current_holdings = [str(symbol) for symbol in strategy_input.params.get("current_holdings", [])]
    if period <= 1:
        raise StrategyParameterError("RSI period 必须大于 1")
    if not 0 <= oversold < overbought <= 100:
        raise StrategyParameterError("RSI 阈值必须满足 0 <= oversold < overbought <= 100")
    close = strategy_input.close_df
    if strategy_input.signal_date not in close.index:
        raise StrategyParameterError("signal_date 不在 close_df")
    position = list(close.index).index(strategy_input.signal_date)
    if position < period:
        return StrategyResult("rsi", strategy_input.signal_date, [], {}, ["warmup_insufficient"])
    rsi = calculate_rsi(close, period)
    rsi_today = rsi.loc[strategy_input.signal_date].dropna()
    scores = (100 - rsi_today).to_dict()
    scores = {str(symbol): float(score) for symbol, score in scores.items()}
    targets = build_rsi_targets(
        rsi_today,
        top_fraction=top_fraction,
        oversold=oversold,
        overbought=overbought,
        current_holdings=current_holdings,
    )
    warnings = [] if targets else ["empty_targets"]
    return StrategyResult("rsi", strategy_input.signal_date, targets, scores, warnings)


def calculate_rsi(close: pd.DataFrame, period: int) -> pd.DataFrame:
    """使用 Wilder 平滑口径计算 RSI。"""

    if period <= 1:
        raise StrategyParameterError("RSI period 必须大于 1")
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.where(avg_loss != 0)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    rsi = rsi.mask((avg_gain == 0) & (avg_loss > 0), 0.0)
    return rsi.fillna(50.0)


def build_rsi_targets(
    rsi_today: pd.Series,
    *,
    top_fraction: float,
    oversold: float,
    overbought: float,
    current_holdings: list[str] | None = None,
) -> list[str]:
    """按“超卖买入、超买卖出”生成目标持仓。"""

    if not 0 < top_fraction <= 1:
        raise StrategyParameterError("top_fraction 必须在 (0, 1] 内")
    if not 0 <= oversold < overbought <= 100:
        raise StrategyParameterError("RSI 阈值必须满足 0 <= oversold < overbought <= 100")
    current = [str(symbol) for symbol in (current_holdings or [])]
    numeric = pd.to_numeric(rsi_today, errors="coerce").dropna()
    keep = [
        symbol
        for symbol in current
        if symbol in numeric.index and float(numeric.loc[symbol]) <= overbought
    ]
    oversold_scores = {
        str(symbol): float(100 - value)
        for symbol, value in numeric.items()
        if float(value) < oversold
    }
    buy = select_top(oversold_scores, top_fraction) if oversold_scores else []
    targets = set(keep)
    targets.update(buy)
    ordered = sorted(targets, key=lambda symbol: (float(numeric.get(symbol, 50.0)), symbol))
    return ordered


__all__ = ("build_rsi_targets", "calculate_rsi", "run_rsi_strategy")
