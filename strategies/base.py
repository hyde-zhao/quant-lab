"""策略扩展纯函数接口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from engine.diagnostics import start_diagnostic


@dataclass(frozen=True, slots=True)
class StrategyInput:
    close_df: pd.DataFrame
    signal_date: date
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class StrategyResult:
    strategy_name: str
    signal_date: date
    target_symbols: list[str]
    scores: dict[str, float]
    warnings: list[str] = field(default_factory=list)


class StrategyParameterError(ValueError):
    """策略参数非法。"""


def select_top(scores: dict[str, float], top_fraction: float) -> list[str]:
    if not 0 < top_fraction <= 1:
        raise StrategyParameterError("top_fraction 必须在 (0, 1] 内")
    if not scores:
        return []
    import math

    count = max(1, math.ceil(len(scores) * top_fraction))
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [symbol for symbol, _ in ranked[:count]]


def run_strategy(strategy_name: str, strategy_input: StrategyInput) -> StrategyResult:
    diag = start_diagnostic(
        "strategy_dispatch",
        "STORY-013",
        {
            "strategy_name": strategy_name,
            "signal_date": strategy_input.signal_date,
            "rows": len(strategy_input.close_df),
            "symbols": len(strategy_input.close_df.columns),
            "params": strategy_input.params,
        },
    )
    try:
        if strategy_name == "rsi":
            from strategies.rsi import run_rsi_strategy

            result = run_rsi_strategy(strategy_input)
        elif strategy_name == "macd":
            from strategies.macd import run_macd_strategy

            result = run_macd_strategy(strategy_input)
        elif strategy_name == "momentum":
            from strategies.momentum import MomentumConfig, build_momentum_targets

            cfg = MomentumConfig(
                lookback_days=int(strategy_input.params.get("lookback_days", strategy_input.params.get("lookback", 20))),
                top_fraction=float(strategy_input.params.get("top_fraction", strategy_input.params.get("fraction", 0.1))),
                sell_buffer=float(strategy_input.params.get("sell_buffer", 0.0)),
            )
            current_holdings = [str(symbol) for symbol in strategy_input.params.get("current_holdings", [])]
            momentum = build_momentum_targets(
                strategy_input.close_df,
                strategy_input.signal_date,
                cfg,
                current_holdings=current_holdings,
            )
            result = StrategyResult("momentum", momentum.signal_date, momentum.target_symbols, momentum.scores)
        else:
            raise StrategyParameterError(f"未知 strategy_name: {strategy_name}")
        if result.warnings:
            status = "empty_targets" if not result.target_symbols else "warmup_filtered"
            diag.warning(status, strategy_warnings=result.warnings)
        diag.end("success" if result.target_symbols else "empty", target_count=len(result.target_symbols))
        return result
    except Exception as exc:
        diag.error(exc)
        raise


__all__ = (
    "StrategyInput",
    "StrategyParameterError",
    "StrategyResult",
    "run_strategy",
    "select_top",
)
