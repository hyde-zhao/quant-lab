"""参数扫描与策略分发。"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
import time
from typing import Any, Callable

import pandas as pd

from engine.backtest import BacktestConfig, run_backtest
from engine.contracts import SWEEP_REPORT_FIELDS
from engine.diagnostics import start_diagnostic
from engine.reporting import sanitize_tabular_text, write_rows_csv


class SweepError(Exception):
    """参数扫描错误。"""


@dataclass(frozen=True, slots=True)
class SweepParameter:
    lookback: int
    rebalance_freq: int
    fraction: float
    strategy_name: str = "momentum"
    strategy_params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SweepConfig:
    parameters: list[SweepParameter] = field(default_factory=list)
    continue_on_error: bool = True


@dataclass(slots=True)
class SweepResult:
    rows: list[dict[str, Any]]
    success_count: int
    failed_count: int


def build_default_grid() -> list[SweepParameter]:
    """构建 5*4*3=60 组默认动量扫描参数。"""

    lookbacks = [5, 10, 20, 30, 60]
    rebalance_freqs = [5, 10, 20, 30]
    fractions = [0.05, 0.10, 0.20]
    return [
        SweepParameter(lookback, rebalance_freq, fraction)
        for lookback, rebalance_freq, fraction in product(lookbacks, rebalance_freqs, fractions)
    ]


def run_parameter_sweep(
    close_df: pd.DataFrame,
    config: SweepConfig | None = None,
    *,
    run_id_prefix: str = "sweep",
    backtest_runner: Callable[[pd.DataFrame, BacktestConfig], Any] | None = None,
) -> SweepResult:
    """运行参数扫描；单组失败按配置保留失败行。"""

    cfg = config or SweepConfig(parameters=build_default_grid())
    params = cfg.parameters or build_default_grid()
    diag = start_diagnostic(
        "scanner",
        "STORY-007",
        {
            "rows": len(close_df),
            "symbols": len(close_df.columns),
            "parameter_count": len(params),
            "continue_on_error": cfg.continue_on_error,
        },
    )
    rows: list[dict[str, Any]] = []
    success_count = 0
    failed_count = 0
    runner = backtest_runner or (lambda frame, bt_cfg: run_backtest(frame, bt_cfg))
    try:
        for index, param in enumerate(params, start=1):
            started = time.monotonic()
            run_id = f"{run_id_prefix}-{index:03d}"
            try:
                result = runner(
                    close_df,
                    BacktestConfig(
                        lookback_days=param.lookback,
                        rebalance_freq=param.rebalance_freq,
                        top_fraction=param.fraction,
                        strategy_name=param.strategy_name,
                        strategy_params=param.strategy_params,
                    ),
                )
                row = {
                    "run_id": run_id,
                    "strategy_name": sanitize_tabular_text(param.strategy_name),
                    "lookback": param.lookback,
                    "rebalance_freq": param.rebalance_freq,
                    "fraction": param.fraction,
                    "status": "success",
                    "error_message": "",
                    "elapsed_seconds": round(time.monotonic() - started, 6),
                    **result.metrics,
                    **result.metadata,
                }
                success_count += 1
            except Exception as exc:
                failed_count += 1
                diag.warning(
                    "single_group_failed",
                    run_id=run_id,
                    lookback=param.lookback,
                    rebalance_freq=param.rebalance_freq,
                    fraction=param.fraction,
                    error_type=type(exc).__name__,
                )
                row = build_failed_sweep_row(run_id, param, exc, time.monotonic() - started)
                if not cfg.continue_on_error:
                    rows.append(row)
                    raise
            rows.append(_normalize_sweep_row(row))
        status = "degraded" if failed_count else "success"
        diag.end(status, success_count=success_count, failed_count=failed_count)
        return SweepResult(rows=rows, success_count=success_count, failed_count=failed_count)
    except Exception as exc:
        diag.error(exc)
        raise


def build_failed_sweep_row(run_id: str, param: SweepParameter, exc: Exception, elapsed_seconds: float) -> dict[str, Any]:
    """构建固定 schema 的失败扫描行。"""

    return _normalize_sweep_row(
        {
            "run_id": run_id,
            "strategy_name": param.strategy_name,
            "lookback": param.lookback,
            "rebalance_freq": param.rebalance_freq,
            "fraction": param.fraction,
            "status": "failed",
            "error_message": sanitize_tabular_text(f"{type(exc).__name__}: {exc}"),
            "elapsed_seconds": round(elapsed_seconds, 6),
        }
    )


def write_sweep_csv(result: SweepResult, output_path: str | Path) -> str:
    return write_rows_csv(result.rows, output_path, list(SWEEP_REPORT_FIELDS))


def _normalize_sweep_row(row: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "cumulative_return": row.get("cumulative_return", row.get("total_return", "")),
        "quality_status": row.get("quality_status", ""),
        "missing_rate": row.get("missing_rate", ""),
        "failed_batch_count": row.get("failed_batch_count", ""),
        "adjustment_policy": row.get("adjustment_policy", ""),
        "available_at_rule": row.get("available_at_rule", ""),
        "is_pit_universe": row.get("is_pit_universe", ""),
    }
    merged = {**aliases, **row}
    return {field: sanitize_tabular_text(merged.get(field, "")) for field in SWEEP_REPORT_FIELDS}


__all__ = (
    "SweepConfig",
    "SweepError",
    "SweepParameter",
    "SweepResult",
    "build_default_grid",
    "build_failed_sweep_row",
    "run_parameter_sweep",
    "sanitize_tabular_text",
    "write_sweep_csv",
)
