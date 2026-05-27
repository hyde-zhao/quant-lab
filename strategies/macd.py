"""MACD 示例策略。"""

from __future__ import annotations

import math

import pandas as pd

from strategies.base import StrategyInput, StrategyParameterError, StrategyResult


def run_macd_strategy(strategy_input: StrategyInput) -> StrategyResult:
    fast = int(strategy_input.params.get("fast", 12))
    slow = int(strategy_input.params.get("slow", 26))
    signal_period = int(strategy_input.params.get("signal", 9))
    top_fraction = float(strategy_input.params.get("top_fraction", strategy_input.params.get("fraction", 0.1)))
    current_holdings = [str(symbol) for symbol in strategy_input.params.get("current_holdings", [])]
    if fast <= 0 or slow <= 0 or signal_period <= 0 or fast >= slow:
        raise StrategyParameterError("MACD 参数必须满足 0 < fast < slow 且 signal > 0")
    close = strategy_input.close_df
    if strategy_input.signal_date not in close.index:
        raise StrategyParameterError("signal_date 不在 close_df")
    position = list(close.index).index(strategy_input.signal_date)
    if position < slow + signal_period:
        return StrategyResult("macd", strategy_input.signal_date, [], {}, ["warmup_insufficient"])
    macd = calculate_macd(close, fast=fast, slow=slow, signal=signal_period)
    previous_date = close.index[position - 1]
    targets, scores = build_macd_targets(
        macd["dif"].loc[previous_date],
        macd["dea"].loc[previous_date],
        macd["hist"].loc[previous_date],
        macd["dif"].loc[strategy_input.signal_date],
        macd["dea"].loc[strategy_input.signal_date],
        macd["hist"].loc[strategy_input.signal_date],
        top_fraction=top_fraction,
        current_holdings=current_holdings,
    )
    warnings = [] if targets else ["empty_targets"]
    return StrategyResult("macd", strategy_input.signal_date, targets, scores, warnings)


def calculate_macd(close: pd.DataFrame, *, fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, pd.DataFrame]:
    """计算 MACD 指标，EMA 使用 adjust=False。"""

    if fast <= 0 or slow <= 0 or signal <= 0 or fast >= slow:
        raise StrategyParameterError("MACD 参数必须满足 0 < fast < slow 且 signal > 0")
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = dif - dea
    return {"dif": dif, "dea": dea, "hist": hist}


def build_macd_targets(
    prev_dif: pd.Series,
    prev_dea: pd.Series,
    prev_hist: pd.Series,
    current_dif: pd.Series,
    current_dea: pd.Series,
    current_hist: pd.Series,
    *,
    top_fraction: float,
    current_holdings: list[str] | None = None,
) -> tuple[list[str], dict[str, float]]:
    """按金叉买入、死叉卖出生成目标持仓。"""

    if not 0 < top_fraction <= 1:
        raise StrategyParameterError("top_fraction 必须在 (0, 1] 内")
    current = [str(symbol) for symbol in (current_holdings or [])]
    frame = pd.DataFrame(
        {
            "prev_dif": prev_dif,
            "prev_dea": prev_dea,
            "prev_hist": prev_hist,
            "current_dif": current_dif,
            "current_dea": current_dea,
            "current_hist": current_hist,
        }
    ).dropna()
    if frame.empty:
        return [], {}
    frame.index = frame.index.astype(str)
    frame["golden_cross"] = (frame["prev_dif"] <= frame["prev_dea"]) & (frame["current_dif"] > frame["current_dea"])
    frame["death_cross"] = (frame["prev_dif"] >= frame["prev_dea"]) & (frame["current_dif"] < frame["current_dea"])
    frame["cross_strength"] = frame["current_hist"] - frame["prev_hist"]
    scores = {str(symbol): float(value) for symbol, value in frame["cross_strength"].items()}

    keep = [symbol for symbol in current if symbol in frame.index and not bool(frame.loc[symbol, "death_cross"])]
    golden = frame[frame["golden_cross"]].copy()
    if not golden.empty:
        golden = golden.sort_values(
            ["cross_strength", "current_hist"],
            ascending=[False, False],
            kind="mergesort",
        )
        ranked_symbols = sorted(
            golden.index.tolist(),
            key=lambda symbol: (-float(golden.loc[symbol, "cross_strength"]), -float(golden.loc[symbol, "current_hist"]), symbol),
        )
        buy_count = max(1, math.ceil(len(frame) * top_fraction))
        buy = ranked_symbols[:buy_count]
    else:
        buy = []

    targets = set(keep)
    targets.update(buy)
    ordered = sorted(
        targets,
        key=lambda symbol: (
            -float(frame.loc[symbol, "current_hist"]) if symbol in frame.index else 0.0,
            symbol,
        ),
    )
    return ordered, scores


__all__ = ("build_macd_targets", "calculate_macd", "run_macd_strategy")
