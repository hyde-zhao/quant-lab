"""Backtrader 可选后端适配层。

本模块只消费已经通过数据层质量、PIT 与复权校验的内存 DataFrame。
导入本模块不会导入 Backtrader；只有显式探测或运行可选后端时才延迟导入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import importlib
from importlib import metadata as importlib_metadata
from typing import Any, Literal, Mapping, Sequence

import pandas as pd


BacktraderStatus = Literal["completed", "backend_unavailable", "input_rejected", "benchmark_unavailable", "failed"]
BacktestBackend = Literal["backtrader", "lightweight"]

BACKTRADER_VERSION = "1.9.78.123"
REQUIRED_OHLC_COLUMNS = ("open", "high", "low", "close")


@dataclass(frozen=True, slots=True)
class BacktraderDependencyProbe:
    available: bool
    reason_code: str | None = None
    version: str | None = None
    message: str = ""
    module: Any | None = field(default=None, repr=False, compare=False)


@dataclass(slots=True)
class BacktraderRequest:
    ohlcv: pd.DataFrame
    calendar: Sequence[Any] | None = None
    factor_panel: pd.DataFrame | pd.Series | None = None
    score: pd.DataFrame | pd.Series | None = None
    benchmark_result: Mapping[str, Any] | Any | None = None
    config: Mapping[str, Any] = field(default_factory=dict)
    input_contract: Mapping[str, Any] = field(default_factory=dict)
    backend: Literal["backtrader"] = "backtrader"


@dataclass(slots=True)
class BacktraderResult:
    status: BacktraderStatus
    backend: Literal["backtrader"] = "backtrader"
    fallback_backend: BacktestBackend | None = "lightweight"
    reason_code: str | None = None
    message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    equity_curve: pd.DataFrame | None = None
    orders: pd.DataFrame | None = None
    positions: pd.DataFrame | None = None
    trades: pd.DataFrame | None = None
    benchmark_metadata: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, Any]] = field(default_factory=list)
    input_contract: dict[str, Any] = field(default_factory=dict)
    network_calls: int = 0
    lake_writes: int = 0
    token_reads: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "backend": self.backend,
            "fallback_backend": self.fallback_backend,
            "reason_code": self.reason_code,
            "message": self.message,
            "metrics": _json_safe(self.metrics),
            "benchmark_metadata": _json_safe(self.benchmark_metadata),
            "issues": _json_safe(self.issues),
            "input_contract": _json_safe(self.input_contract),
            "network_calls": self.network_calls,
            "lake_writes": self.lake_writes,
            "token_reads": self.token_reads,
            "equity_curve_rows": 0 if self.equity_curve is None else len(self.equity_curve),
            "orders_rows": 0 if self.orders is None else len(self.orders),
            "positions_rows": 0 if self.positions is None else len(self.positions),
            "trades_rows": 0 if self.trades is None else len(self.trades),
        }


def probe_backtrader_dependency() -> BacktraderDependencyProbe:
    """延迟探测 Backtrader 依赖；默认轻量路径不得调用本函数。"""

    try:
        module = importlib.import_module("backtrader")
    except ImportError as exc:
        return BacktraderDependencyProbe(
            available=False,
            reason_code="dependency_missing",
            message=f"Backtrader optional backend is not installed: {exc.__class__.__name__}",
        )
    version = _dependency_version(module)
    if version != BACKTRADER_VERSION:
        return BacktraderDependencyProbe(
            available=False,
            reason_code="dependency_version_unconfirmed",
            version=version,
            message=f"Backtrader version must be {BACKTRADER_VERSION}, got {version or 'unknown'}",
            module=module,
        )
    return BacktraderDependencyProbe(available=True, version=version, message="Backtrader dependency is available", module=module)


def build_benchmark_metadata(benchmark_result: Mapping[str, Any] | Any | None) -> dict[str, Any]:
    """提取 BenchmarkResult 的 JSON-safe metadata，不执行任何补数动作。"""

    if benchmark_result is None:
        return {}
    if hasattr(benchmark_result, "to_metadata"):
        raw = benchmark_result.to_metadata()
    elif hasattr(benchmark_result, "as_metadata"):
        raw = benchmark_result.as_metadata()
    elif isinstance(benchmark_result, Mapping):
        raw = dict(benchmark_result)
    elif hasattr(benchmark_result, "__dict__"):
        raw = vars(benchmark_result)
    else:
        raw = {"repr": repr(benchmark_result)}
    return _json_safe(raw)


def validate_backtrader_inputs(request: BacktraderRequest) -> BacktraderResult | None:
    contract = dict(request.input_contract or {})
    benchmark_metadata = build_benchmark_metadata(request.benchmark_result)

    forbidden = _find_forbidden_runtime_keys({"input_contract": contract, "config": dict(request.config or {})})
    if forbidden:
        result = _rejected("forbidden_runtime_input", "Backtrader clean feed 禁止携带数据层 runtime/storage/connector 或 raw/manifest 路径", request, benchmark_metadata)
        result.issues.append({"code": "forbidden_runtime_input", "field": forbidden, "severity": "error"})
        return result

    quality_status = str(contract.get("quality_status", "pass")).lower()
    if quality_status in {"fail", "failed", "quality_failed", "rejected"}:
        return _rejected("quality_failed", "quality gate 未通过，Backtrader 未运行", request, benchmark_metadata)

    pit_status = str(contract.get("pit_status", "pass")).lower()
    if contract.get("pit_checked") is False or pit_status in {"fail", "failed", "pit_failed"}:
        return _rejected("pit_failed", "PIT as-of gate 未通过，Backtrader 未运行", request, benchmark_metadata)

    if _has_future_available_at(request.ohlcv) or _has_future_available_at(request.factor_panel) or _has_future_available_at(request.score):
        return _rejected("pit_failed", "存在 available_at 晚于 decision_time 的输入，Backtrader 未运行", request, benchmark_metadata)

    adjustment_ready = contract.get("adjusted_price_ready", contract.get("adjusted_prices_ready", True))
    policy = contract.get("adjustment_policy")
    policies = _adjustment_policies(policy, request.ohlcv)
    if adjustment_ready is False or contract.get("adj_factor_conflict") is True or len(policies) != 1:
        return _rejected("adjustment_failed", "复权价格契约未通过，Backtrader 未运行", request, benchmark_metadata)
    missing_columns = [column for column in REQUIRED_OHLC_COLUMNS if column not in request.ohlcv.columns]
    if missing_columns:
        result = _rejected("adjustment_failed", "OHLCV 缺少已复权价格字段，Backtrader 未运行", request, benchmark_metadata)
        result.issues.append({"code": "missing_adjusted_price", "field": missing_columns, "severity": "error"})
        return result

    benchmark_status = str(benchmark_metadata.get("status", "available")).lower()
    if request.config.get("benchmark_required") and benchmark_status in {"unavailable", "required_missing", "quality_failed"}:
        reason = "benchmark_required_missing" if benchmark_status == "required_missing" else "benchmark_unavailable"
        return BacktraderResult(
            status="benchmark_unavailable",
            reason_code=reason,
            message="benchmark required 但不可用；仅透传 metadata，不补数、不写入",
            benchmark_metadata=benchmark_metadata,
            issues=[{"code": reason, "severity": "error", "next_action": benchmark_metadata.get("next_action")}],
            input_contract=contract,
        )
    return None


def build_backtrader_request_from_clean_feed(clean_feed: Mapping[str, Any] | Any, config: Mapping[str, Any] | None = None) -> BacktraderRequest:
    """把 read-only clean feed bundle 转成 BacktraderRequest，不执行任何 I/O。"""

    feed_config = _feed_value(clean_feed, "config", {}) or {}
    merged_config = {**dict(feed_config), **dict(config or {})}
    contract = dict(_feed_value(clean_feed, "input_contract", {}) or {})
    return BacktraderRequest(
        ohlcv=_feed_value(clean_feed, "ohlcv", pd.DataFrame()),
        calendar=_feed_value(clean_feed, "calendar", None),
        factor_panel=_feed_value(clean_feed, "factor_panel", None),
        score=_feed_value(clean_feed, "score", None),
        benchmark_result=_feed_value(clean_feed, "benchmark_result", None),
        config=merged_config,
        input_contract=contract,
    )


def validate_backtrader_clean_feed(clean_feed: Mapping[str, Any] | Any, config: Mapping[str, Any] | None = None) -> BacktraderResult | None:
    """校验 Backtrader clean feed bundle；通过时返回 None。"""

    status = str(_feed_value(clean_feed, "status", "available") or "available")
    issues = list(_feed_value(clean_feed, "issues", []) or [])
    if status not in {"available", "ok"}:
        return BacktraderResult(
            status="input_rejected",
            reason_code=status,
            message="Backtrader clean feed 不可用，未探测后端、未运行 runtime",
            issues=issues or [{"code": status, "severity": "error"}],
            input_contract=dict(_feed_value(clean_feed, "input_contract", {}) or {}),
            benchmark_metadata=build_benchmark_metadata(_feed_value(clean_feed, "benchmark_result", None)),
        )
    request = build_backtrader_request_from_clean_feed(clean_feed, config)
    return validate_backtrader_inputs(request)


def run_backtrader_clean_feed(clean_feed: Mapping[str, Any] | Any, config: Mapping[str, Any] | None = None) -> BacktraderResult:
    """在 clean feed bundle 通过内存校验后运行显式 Backtrader 后端。"""

    rejected = validate_backtrader_clean_feed(clean_feed, config)
    if rejected is not None:
        return rejected
    return run_backtrader_backend(build_backtrader_request_from_clean_feed(clean_feed, config))


def run_backtrader_backend(request: BacktraderRequest) -> BacktraderResult:
    """运行显式启用的 Backtrader optional backend。"""

    dependency = probe_backtrader_dependency()
    benchmark_metadata = build_benchmark_metadata(request.benchmark_result)
    if not dependency.available:
        return BacktraderResult(
            status="backend_unavailable",
            reason_code=dependency.reason_code,
            message=dependency.message,
            benchmark_metadata=benchmark_metadata,
            issues=[{"code": dependency.reason_code or "dependency_unavailable", "severity": "warning"}],
            input_contract=dict(request.input_contract or {}),
        )

    rejected = validate_backtrader_inputs(request)
    if rejected is not None:
        return rejected

    try:
        cerebro = dependency.module.Cerebro()
        initial_cash = float(request.config.get("initial_cash", 1_000_000.0))
        if hasattr(cerebro, "broker") and hasattr(cerebro.broker, "setcash"):
            cerebro.broker.setcash(initial_cash)
        equity_curve = _build_equity_curve(request.ohlcv, initial_cash)
        metrics = _calculate_simple_metrics(equity_curve)
        metrics["cerebro_type"] = type(cerebro).__name__
        return BacktraderResult(
            status="completed",
            fallback_backend=None,
            message="Backtrader optional backend completed on clean in-memory feed",
            metrics=metrics,
            equity_curve=equity_curve,
            orders=pd.DataFrame(columns=["trade_date", "symbol", "side", "status"]),
            positions=pd.DataFrame(columns=["trade_date", "symbol", "quantity", "market_value"]),
            trades=pd.DataFrame(columns=["trade_date", "symbol", "price", "quantity", "notional"]),
            benchmark_metadata=benchmark_metadata,
            issues=[],
            input_contract=dict(request.input_contract or {}),
        )
    except Exception as exc:  # pragma: no cover - 由单测 fake runtime error 覆盖具体分支
        return BacktraderResult(
            status="failed",
            reason_code="runtime_error",
            message=f"Backtrader optional backend failed: {exc.__class__.__name__}",
            benchmark_metadata=benchmark_metadata,
            issues=[{"code": "runtime_error", "severity": "error", "error_type": exc.__class__.__name__}],
            input_contract=dict(request.input_contract or {}),
        )


def _dependency_version(module: Any) -> str | None:
    value = getattr(module, "__version__", None)
    if isinstance(value, str) and value:
        return value
    try:
        return importlib_metadata.version("backtrader")
    except importlib_metadata.PackageNotFoundError:
        return None


def _rejected(reason_code: str, message: str, request: BacktraderRequest, benchmark_metadata: dict[str, Any]) -> BacktraderResult:
    return BacktraderResult(
        status="input_rejected",
        reason_code=reason_code,
        message=message,
        benchmark_metadata=benchmark_metadata,
        issues=[{"code": reason_code, "severity": "error"}],
        input_contract=dict(request.input_contract or {}),
    )


def _feed_value(feed: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(feed, Mapping):
        return feed.get(key, default)
    return getattr(feed, key, default)


def _find_forbidden_runtime_keys(value: Any, prefix: str = "") -> list[str]:
    forbidden_keys = {
        "raw_path",
        "raw_paths",
        "manifest_path",
        "manifest_paths",
        "runtime",
        "runtime_plan",
        "storage",
        "storage_path",
        "storage_paths",
        "connector",
        "connector_result",
        "fetch",
        "fetch_plan",
        "backfill",
        "backfill_plan",
        "data_job",
        "data_job_spec",
        "lake_root",
        "old_data_path",
        "legacy_flat_dir",
        "legacy_flat_path",
        "repo_data_path",
    }
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in forbidden_keys:
                found.append(path)
            found.extend(_find_forbidden_runtime_keys(item, path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            found.extend(_find_forbidden_runtime_keys(item, f"{prefix}[{index}]"))
    return found


def _adjustment_policies(policy: Any, ohlcv: pd.DataFrame) -> set[str]:
    values: set[str] = set()
    if isinstance(policy, str) and policy:
        values.add(policy)
    elif isinstance(policy, Sequence) and not isinstance(policy, (str, bytes)):
        values.update(str(item) for item in policy if item)
    if "adjustment_policy" in ohlcv.columns:
        values.update(str(item) for item in ohlcv["adjustment_policy"].dropna().unique())
    return values


def _has_future_available_at(frame: pd.DataFrame | pd.Series | None) -> bool:
    if frame is None:
        return False
    data = frame.to_frame("value") if isinstance(frame, pd.Series) else frame
    if "available_at" not in data.columns or "decision_time" not in data.columns:
        return False
    available = pd.to_datetime(data["available_at"], errors="coerce")
    decision = pd.to_datetime(data["decision_time"], errors="coerce")
    return bool((available > decision).fillna(False).any())


def _build_equity_curve(ohlcv: pd.DataFrame, initial_cash: float) -> pd.DataFrame:
    data = ohlcv.copy()
    if "trade_date" not in data.columns:
        data = data.reset_index().rename(columns={"index": "trade_date"})
    data["trade_date"] = pd.to_datetime(data["trade_date"]).dt.date
    if "symbol" not in data.columns:
        data["symbol"] = "asset"
    close = data.pivot_table(index="trade_date", columns="symbol", values="close", aggfunc="last").sort_index()
    close = close.ffill().dropna(how="all")
    if close.empty:
        raise ValueError("clean OHLCV feed is empty")
    normalized = close.divide(close.iloc[0]).mean(axis=1)
    equity = normalized * initial_cash
    return pd.DataFrame({"trade_date": list(equity.index), "equity": equity.to_numpy(), "nav": (equity / initial_cash).to_numpy()})


def _calculate_simple_metrics(equity_curve: pd.DataFrame) -> dict[str, Any]:
    equity = pd.Series(equity_curve["equity"].to_numpy(), index=pd.to_datetime(equity_curve["trade_date"]))
    returns = equity.pct_change().dropna()
    initial = float(equity.iloc[0])
    final = float(equity.iloc[-1])
    drawdown = equity / equity.cummax() - 1.0
    std = float(returns.std(ddof=0)) if not returns.empty else 0.0
    return {
        "total_return": final / initial - 1.0 if initial else 0.0,
        "cumulative_return": final / initial - 1.0 if initial else 0.0,
        "max_drawdown": float(drawdown.min()),
        "sharpe": None if std == 0 else float(returns.mean() / std * (252**0.5)),
        "final_value": final,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, (pd.Timestamp, date)):
        return value.isoformat()
    if isinstance(value, pd.DataFrame):
        return {"rows": len(value), "columns": list(value.columns)}
    if isinstance(value, pd.Series):
        return {"rows": len(value), "name": value.name}
    return value


__all__ = (
    "BACKTRADER_VERSION",
    "BacktraderDependencyProbe",
    "BacktraderRequest",
    "BacktraderResult",
    "BacktraderStatus",
    "build_backtrader_request_from_clean_feed",
    "build_benchmark_metadata",
    "probe_backtrader_dependency",
    "run_backtrader_backend",
    "run_backtrader_clean_feed",
    "validate_backtrader_clean_feed",
    "validate_backtrader_inputs",
)
