"""单次本地回测编排。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

import pandas as pd

from engine.diagnostics import start_diagnostic
from engine.metrics import calculate_metrics
from engine.portfolio import PortfolioConfig, PortfolioResult, RebalanceSignal, run_portfolio
from engine.research_dataset import (
    ExecutionPolicyRequest,
    ExecutionPolicyResult,
    resolve_execution_price_policy,
)
from market_data.readers import ReaderResult
from strategies.base import StrategyInput, run_strategy


class BacktestError(Exception):
    """回测编排错误。"""


BacktestBackend = Literal["lightweight", "backtrader"]
_POLICY_MISSING = object()


@dataclass(frozen=True, slots=True)
class RebalanceScheduleItem:
    signal_date: date
    execution_date: date


@dataclass(slots=True)
class BacktestConfig:
    lookback_days: int = 20
    rebalance_freq: int = 5
    top_fraction: float = 0.1
    strategy_name: str = "momentum"
    strategy_params: dict[str, Any] = field(default_factory=dict)
    portfolio_config: PortfolioConfig = field(default_factory=PortfolioConfig)


@dataclass(slots=True)
class BacktestResult:
    config: BacktestConfig
    schedule: list[RebalanceScheduleItem]
    portfolio_result: PortfolioResult
    metrics: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ExecutionPolicyConfig:
    policy: str = "close_proxy"
    realism_mode: str = "production_strict"
    degradation_reason: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionPriceFrameResult:
    price_frame: pd.DataFrame
    policy_result: ExecutionPolicyResult
    metadata: dict[str, Any]
    issues: list[dict[str, Any]] = field(default_factory=list)


def build_rebalance_schedule(
    calendar: list[date] | pd.Index,
    lookback_days: int,
    rebalance_freq: int,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> list[RebalanceScheduleItem]:
    """warm-up 后每 `rebalance_freq` 个开市日生成信号，执行日为下一开市日。"""

    if lookback_days <= 0 or rebalance_freq <= 0:
        raise BacktestError("lookback_days 与 rebalance_freq 必须为正数")
    dates = [_to_date(item) for item in calendar]
    if start_date is not None:
        dates = [item for item in dates if item >= _to_date(start_date)]
    if end_date is not None:
        dates = [item for item in dates if item <= _to_date(end_date)]
    dates = sorted(dict.fromkeys(dates))
    schedule: list[RebalanceScheduleItem] = []
    index = lookback_days
    while index < len(dates):
        signal_date = dates[index]
        if index + 1 >= len(dates):
            break
        execution_date = dates[index + 1]
        schedule.append(RebalanceScheduleItem(signal_date, execution_date))
        index += rebalance_freq
    return schedule


def run_backtest(
    close_df: pd.DataFrame,
    config: BacktestConfig | None = None,
    *,
    metadata: dict[str, Any] | None = None,
    execution_policy: ExecutionPolicyConfig | dict[str, Any] | str | None = None,
    execution_feed: pd.DataFrame | ReaderResult | None = None,
    tradability_matrix: Any | None = None,
) -> BacktestResult:
    """运行动量信号、T+1 组合成交与指标计算。"""

    cfg = config or BacktestConfig()
    source_metadata = dict(metadata or {})
    diag = start_diagnostic(
        "backtest",
        "STORY-006",
        {
            "rows": len(close_df),
            "symbols": len(close_df.columns),
            "lookback_days": cfg.lookback_days,
            "rebalance_freq": cfg.rebalance_freq,
            "top_fraction": cfg.top_fraction,
            "strategy_name": cfg.strategy_name,
        },
    )
    try:
        schedule = build_rebalance_schedule(
            list(close_df.index),
            cfg.lookback_days,
            cfg.rebalance_freq,
            close_df.index.min(),
            close_df.index.max(),
        )
        if not schedule:
            diag.warning("skipped_no_execution_date", calendar_rows=len(close_df))
            raise BacktestError("调仓 schedule 为空")
        signals: list[RebalanceSignal] = []
        current_targets: list[str] = []
        for item in schedule:
            params = {
                "lookback_days": cfg.lookback_days,
                "top_fraction": cfg.top_fraction,
                "fraction": cfg.top_fraction,
                "current_holdings": current_targets,
                **cfg.strategy_params,
            }
            signal = run_strategy(cfg.strategy_name, StrategyInput(close_df, item.signal_date, params))
            if signal.warnings:
                diag.warning("quality_warn", strategy_warnings=signal.warnings)
            current_targets = list(signal.target_symbols)
            signals.append(
                RebalanceSignal(
                    signal_date=item.signal_date,
                    execution_date=item.execution_date,
                    target_symbols=signal.target_symbols,
                )
            )
        portfolio_prices = close_df
        execution_metadata = _legacy_execution_metadata()
        execution_issues: list[dict[str, Any]] = []
        if execution_policy is not None or execution_feed is not None:
            policy_config = _coerce_execution_policy_config(execution_policy, source_metadata)
            frame_result = build_execution_price_frame(
                _execution_feed_frame_from_input(execution_feed),
                policy_config,
                tradability_matrix=tradability_matrix,
            )
            portfolio_prices = _align_execution_price_frame(close_df, frame_result.price_frame)
            execution_metadata = frame_result.metadata
            execution_issues = frame_result.issues

        portfolio_result = run_portfolio(portfolio_prices, signals, cfg.portfolio_config)
        metrics = calculate_metrics(portfolio_result)
        result_metadata = {
            "strategy_name": cfg.strategy_name,
            "signal_time_rule": "close_after_available_at",
            "execution_time_rule": "next_open_day_close_proxy",
            **source_metadata,
            "execution": execution_metadata,
            "execution_price_policy": execution_metadata.get("execution_price_policy"),
            "execution_availability_status": execution_metadata.get("execution_availability_status"),
            "execution_degradation_reason": execution_metadata.get("execution_degradation_reason"),
            "blocked_claims": execution_metadata.get("blocked_claims", source_metadata.get("blocked_claims", [])),
            "known_limitations": execution_metadata.get("known_limitations", source_metadata.get("known_limitations", [])),
            "execution_issues": execution_issues,
        }
        diag.end("success", schedule_count=len(schedule), signal_count=len(signals))
        return BacktestResult(cfg, schedule, portfolio_result, metrics, result_metadata)
    except Exception as exc:
        diag.error(exc)
        raise


def run_backtest_from_loaded_data(
    loaded_data: Any,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """从已通过 data_loader 门禁的数据对象运行轻量回测。"""

    close_df = getattr(loaded_data, "close_df", None)
    metadata = dict(getattr(loaded_data, "metadata", {}) or {})
    if close_df is None or getattr(close_df, "empty", True):
        raise BacktestError("lightweight_input_unavailable: close_df_empty")
    if metadata.get("input_mode") == "legacy_flat" and not metadata.get("legacy_flat_enabled", False):
        raise BacktestError("legacy_flat_disabled")
    execution_metadata = metadata.get("execution") if isinstance(metadata.get("execution"), dict) else {}
    execution_policy = getattr(loaded_data, "execution_policy", None)
    if execution_policy is None:
        execution_policy = metadata.get("execution_price_policy") or execution_metadata.get("execution_price_policy")
    execution_feed = getattr(loaded_data, "execution_feed", None)
    if execution_feed is None:
        execution_feed = metadata.get("execution_feed")
    tradability_matrix = getattr(loaded_data, "tradability_matrix", None)
    if tradability_matrix is None:
        tradability_matrix = metadata.get("tradability_matrix")
    return run_backtest(
        close_df,
        config,
        metadata=metadata,
        execution_policy=execution_policy,
        execution_feed=execution_feed,
        tradability_matrix=tradability_matrix,
    )


def select_backtest_backend(backend: str | None = None) -> BacktestBackend:
    """选择回测后端；默认保持轻量主路径。"""

    selected = backend or "lightweight"
    if selected not in {"lightweight", "backtrader"}:
        raise BacktestError(f"unknown_backend: {selected}")
    return selected  # type: ignore[return-value]


def run_backtest_with_backend(
    close_df: pd.DataFrame,
    config: BacktestConfig | None = None,
    *,
    metadata: dict[str, Any] | None = None,
    backend: str | None = "lightweight",
    backtrader_request: Any | None = None,
    backtrader_clean_feed: Any | None = None,
) -> BacktestResult | Any:
    """显式后端 wrapper；未指定时完全复用现有轻量回测。"""

    selected = select_backtest_backend(backend)
    if selected == "lightweight":
        return run_backtest(close_df, config, metadata=metadata)

    from engine.backtrader_adapter import (
        BacktraderResult,
        build_backtrader_request_from_clean_feed,
        run_backtrader_backend,
        validate_backtrader_clean_feed,
    )

    if backtrader_request is None and backtrader_clean_feed is not None:
        rejected = validate_backtrader_clean_feed(backtrader_clean_feed)
        if rejected is not None:
            return rejected
        backtrader_request = build_backtrader_request_from_clean_feed(backtrader_clean_feed)

    if backtrader_request is None:
        return BacktraderResult(
            status="input_rejected",
            reason_code="missing_backtrader_request",
            message="backend=backtrader 需要显式传入已清洗的 BacktraderRequest",
            input_contract={},
        )
    return run_backtrader_backend(backtrader_request)


def _to_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def build_execution_price_frame(
    feed_frame: pd.DataFrame,
    policy_config: ExecutionPolicyConfig | dict[str, Any] | str,
    *,
    tradability_matrix: Any | None = None,
) -> ExecutionPriceFrameResult:
    """把 long-form execution feed 转为组合引擎可消费的价格矩阵。"""

    cfg = _coerce_execution_policy_config(policy_config, {})
    if feed_frame is None or getattr(feed_frame, "empty", True):
        feed_result = ReaderResult(
            status="required_missing",
            frame=None,
            issues=[{"code": "execution_feed_missing"}],
            remediation_spec={"auto_execute": False, "dry_run_default": True},
        )
    else:
        feed_result = ReaderResult(status="available", frame=feed_frame.copy())
    policy_result = resolve_execution_price_policy(
        ExecutionPolicyRequest(
            policy=cfg.policy,
            realism_mode=cfg.realism_mode,
            degradation_reason=cfg.degradation_reason,
        ),
        feed_result,
        tradability_matrix=tradability_matrix,
    )
    row_frame = policy_result.to_frame()
    if row_frame.empty:
        price_frame = pd.DataFrame()
    else:
        row_frame["_trade_date"] = pd.to_datetime(row_frame["trade_date"], errors="coerce").dt.date
        price_frame = row_frame.pivot(index="_trade_date", columns="symbol", values="execution_price").sort_index()
        price_frame.index.name = None
    issues = [dict(row) for row in policy_result.rows if row.get("unfilled_reason")]
    metadata = policy_result.to_metadata()
    metadata["execution_price_frame_rows"] = int(len(price_frame))
    metadata["execution_price_frame_columns"] = list(price_frame.columns)
    return ExecutionPriceFrameResult(price_frame=price_frame, policy_result=policy_result, metadata=metadata, issues=issues)


def _coerce_execution_policy_config(
    value: ExecutionPolicyConfig | dict[str, Any] | str | None,
    metadata: dict[str, Any],
) -> ExecutionPolicyConfig:
    if isinstance(value, ExecutionPolicyConfig):
        return value
    if isinstance(value, str):
        return ExecutionPolicyConfig(policy=value)
    source = dict(value or {})
    execution = metadata.get("execution") if isinstance(metadata.get("execution"), dict) else {}
    policy_value = _explicit_policy_value(source, execution, metadata)
    return ExecutionPolicyConfig(
        policy="close_proxy" if policy_value is _POLICY_MISSING else "" if policy_value is None else str(policy_value),
        realism_mode=str(source.get("realism_mode") or execution.get("realism_mode") or metadata.get("realism_mode") or "production_strict"),
        degradation_reason=str(source.get("degradation_reason") or source.get("execution_degradation_reason") or execution.get("execution_degradation_reason") or ""),
    )


def _explicit_policy_value(*sources: dict[str, Any]) -> Any:
    for source in sources:
        if "policy" in source:
            return source["policy"]
        if "execution_price_policy" in source:
            return source["execution_price_policy"]
    return _POLICY_MISSING


def _execution_feed_frame_from_input(value: pd.DataFrame | ReaderResult | None) -> pd.DataFrame:
    if isinstance(value, ReaderResult):
        return value.frame.copy() if value.frame is not None else pd.DataFrame()
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame()


def _align_execution_price_frame(close_df: pd.DataFrame, execution_frame: pd.DataFrame) -> pd.DataFrame:
    if execution_frame.empty:
        return pd.DataFrame(index=close_df.index, columns=close_df.columns, dtype=float)
    aligned = execution_frame.reindex(index=[_to_date(item) for item in close_df.index], columns=close_df.columns)
    aligned.index = close_df.index
    return aligned


def _legacy_execution_metadata() -> dict[str, Any]:
    return {
        "execution_price_policy": "close_proxy",
        "execution_availability_status": "available_with_warnings",
        "execution_degradation_reason": "legacy_next_open_day_close_proxy",
        "vwap_or_proxy": "proxy",
        "close_substitution_count": 0,
        "missing_price_fill_count": 0,
        "blocked_claims": [
            {"claim": "real_vwap_execution", "reason_code": "legacy_close_proxy"},
            {"claim": "vwap_fill_claim", "reason_code": "legacy_close_proxy"},
            {"claim": "real_open_execution", "reason_code": "legacy_close_proxy"},
            {"claim": "real_tradable_execution", "reason_code": "legacy_close_proxy"},
        ],
        "known_limitations": [
            {
                "code": "legacy_close_proxy_execution",
                "reason_code": "legacy_next_open_day_close_proxy",
            }
        ],
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
    }


__all__ = (
    "BacktestConfig",
    "BacktestError",
    "ExecutionPolicyConfig",
    "ExecutionPriceFrameResult",
    "BacktestResult",
    "BacktestBackend",
    "RebalanceScheduleItem",
    "build_execution_price_frame",
    "build_rebalance_schedule",
    "run_backtest",
    "run_backtest_from_loaded_data",
    "run_backtest_with_backend",
    "select_backtest_backend",
)
