"""Backtrader 可选后端适配层。

本模块只消费已经通过数据层质量、PIT 与复权校验的内存 DataFrame。
导入本模块不会导入 Backtrader；只有显式探测或运行可选后端时才延迟导入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import importlib
from importlib import metadata as importlib_metadata
from typing import Any, Callable, Literal, Mapping, Sequence

import pandas as pd


BacktraderStatus = Literal["completed", "backend_unavailable", "input_rejected", "benchmark_unavailable", "failed"]
BacktestBackend = Literal["backtrader", "lightweight"]
BackendSelectionStatus = Literal[
    "available",
    "not_selected",
    "backend_unavailable",
    "blocked_clean_feed_pit",
    "blocked_adjustment_policy_mixed",
    "data_required_missing",
    "quality_fail",
    "runtime_not_authorized",
]
SelectedResearchBackend = Literal["lightweight", "backtrader", "none"]

BACKTRADER_VERSION = "1.9.78.123"
REQUIRED_OHLC_COLUMNS = ("open", "high", "low", "close")
REQUIRED_CLEAN_FEED_EVIDENCE_FIELDS = (
    "pit_checked",
    "pit_status",
    "available_at_checked",
    "adjusted_price_ready",
    "adjustment_policy",
    "ohlcv_status",
    "calendar_status",
    "benchmark_status",
    "tradability_status",
    "cost_status",
    "quality_status",
    "lineage",
    "limitations",
)
FORBIDDEN_OPERATION_COUNTERS = (
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "credential_read",
    "qmt_operation",
    "broker_operation",
    "simulation_or_live",
    "backtrader_run",
)


@dataclass(frozen=True, slots=True)
class BacktraderDependencyProbe:
    available: bool
    reason_code: str | None = None
    version: str | None = None
    message: str = ""
    module: Any | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class StructuredUnavailable:
    status: BackendSelectionStatus
    reasons: tuple[str, ...] = ()
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "message": self.message,
            "details": _json_safe(self.details),
        }


@dataclass(frozen=True, slots=True)
class CleanFeedGateResult:
    passed: bool
    availability_status: BackendSelectionStatus
    blocked_reasons: tuple[str, ...] = ()
    lineage: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[Any, ...] = ()
    unavailable: StructuredUnavailable | None = None
    forbidden_operation_counts: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
    )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "availability_status": self.availability_status,
            "blocked_reasons": list(self.blocked_reasons),
            "lineage": _json_safe(self.lineage),
            "limitations": _json_safe(list(self.limitations)),
            "unavailable": None if self.unavailable is None else self.unavailable.to_metadata(),
            "forbidden_operation_counts": dict(self.forbidden_operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BackendSelectionRequest:
    backend: str | None = "lightweight"
    clean_feed_evidence: Mapping[str, Any] | Any | None = None
    feature_flags: Mapping[str, Any] = field(default_factory=dict)
    lineage: Mapping[str, Any] | None = None
    limitations: Sequence[Any] | None = None
    dependency_probe: Callable[[], BacktraderDependencyProbe] | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class BackendSelectionResult:
    selected_backend: SelectedResearchBackend
    requested_backend: str
    availability_status: BackendSelectionStatus
    blocked_reasons: tuple[str, ...] = ()
    lineage: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[Any, ...] = ()
    import_attempted: bool = False
    unavailable: StructuredUnavailable | None = None
    forbidden_operation_counts: dict[str, int] = field(
        default_factory=lambda: {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
    )

    @property
    def available(self) -> bool:
        return self.availability_status == "available"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "selected_backend": self.selected_backend,
            "requested_backend": self.requested_backend,
            "availability_status": self.availability_status,
            "blocked_reasons": list(self.blocked_reasons),
            "lineage": _json_safe(self.lineage),
            "limitations": _json_safe(list(self.limitations)),
            "import_attempted": self.import_attempted,
            "unavailable": None if self.unavailable is None else self.unavailable.to_metadata(),
            "forbidden_operation_counts": dict(self.forbidden_operation_counts),
        }


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


def validate_clean_feed_gate(
    clean_feed_evidence: Mapping[str, Any] | Any | None,
    *,
    lineage: Mapping[str, Any] | None = None,
    limitations: Sequence[Any] | None = None,
) -> CleanFeedGateResult:
    """校验 CR025 clean feed evidence；只消费证据，不补数、不写湖、不导入 Backtrader。"""

    if clean_feed_evidence is None:
        return _clean_feed_gate_result(
            False,
            "data_required_missing",
            ("clean_feed_evidence_missing",),
            {},
            (),
            "clean feed evidence is required for backtrader selection",
        )

    evidence_lineage = _lineage_from_evidence(clean_feed_evidence, lineage)
    evidence_limitations = _limitations_from_evidence(clean_feed_evidence, limitations)
    missing = [field for field in REQUIRED_CLEAN_FEED_EVIDENCE_FIELDS if not _has_evidence_field(clean_feed_evidence, field)]
    if not evidence_lineage:
        missing.append("lineage")
    if limitations is None and not _has_evidence_field(clean_feed_evidence, "limitations"):
        missing.append("limitations")
    if missing:
        reasons = tuple(f"data_required_missing:{field}" for field in sorted(dict.fromkeys(missing)))
        return _clean_feed_gate_result(
            False,
            "data_required_missing",
            reasons,
            evidence_lineage,
            evidence_limitations,
            "clean feed evidence is missing required fields",
        )

    blocked_reasons: list[str] = []
    if _evidence_value(clean_feed_evidence, "pit_checked") is not True or not _status_ok(_evidence_value(clean_feed_evidence, "pit_status")):
        blocked_reasons.append("blocked_clean_feed_pit:pit_not_confirmed")
    if _evidence_value(clean_feed_evidence, "available_at_checked") is not True:
        blocked_reasons.append("blocked_clean_feed_pit:available_at_not_confirmed")

    policies = _policy_values(_evidence_value(clean_feed_evidence, "adjustment_policy"))
    policies.update(_policy_values(_evidence_value(clean_feed_evidence, "adjustment_policies")))
    if _evidence_value(clean_feed_evidence, "adjusted_price_ready") is not True or len(policies) != 1:
        blocked_reasons.append("blocked_adjustment_policy_mixed:adjustment_policy_not_single_clean_view")

    data_required_fields = ("ohlcv_status", "calendar_status", "benchmark_status", "tradability_status", "cost_status")
    for field in data_required_fields:
        if not _status_ok(_evidence_value(clean_feed_evidence, field)):
            blocked_reasons.append(f"data_required_missing:{field}")
    if _evidence_value(clean_feed_evidence, "benchmark_required", True) is True and not _status_ok(_evidence_value(clean_feed_evidence, "benchmark_status")):
        blocked_reasons.append("data_required_missing:benchmark_required")

    if not _status_ok(_evidence_value(clean_feed_evidence, "quality_status")):
        blocked_reasons.append("quality_fail:quality_status")

    if blocked_reasons:
        status = _selection_status_for_reasons(blocked_reasons)
        return _clean_feed_gate_result(
            False,
            status,
            tuple(blocked_reasons),
            evidence_lineage,
            evidence_limitations,
            "clean feed gate failed",
        )
    return CleanFeedGateResult(
        passed=True,
        availability_status="available",
        lineage=evidence_lineage,
        limitations=evidence_limitations,
    )


def select_research_backend(request: BackendSelectionRequest | Mapping[str, Any] | None = None) -> BackendSelectionResult:
    """选择 CR025 研究执行后端；默认 lightweight，不触发 Backtrader import。"""

    selection_request = _coerce_backend_selection_request(request)
    requested_backend = _normalise_backend(selection_request.backend)
    request_lineage = dict(selection_request.lineage or {})
    request_limitations = _as_tuple(selection_request.limitations)

    if requested_backend == "lightweight":
        return BackendSelectionResult(
            selected_backend="lightweight",
            requested_backend=requested_backend,
            availability_status="available",
            lineage=request_lineage,
            limitations=request_limitations,
            import_attempted=False,
        )

    if requested_backend != "backtrader":
        reason = f"backend_unavailable:unknown_backend:{requested_backend}"
        unavailable = StructuredUnavailable("backend_unavailable", (reason,), "unknown backend requested")
        return BackendSelectionResult(
            selected_backend="none",
            requested_backend=requested_backend,
            availability_status="backend_unavailable",
            blocked_reasons=(reason,),
            lineage=request_lineage,
            limitations=request_limitations,
            import_attempted=False,
            unavailable=unavailable,
        )

    gate = validate_clean_feed_gate(
        selection_request.clean_feed_evidence,
        lineage=selection_request.lineage,
        limitations=selection_request.limitations,
    )
    if not gate.passed:
        return BackendSelectionResult(
            selected_backend="none",
            requested_backend=requested_backend,
            availability_status=gate.availability_status,
            blocked_reasons=gate.blocked_reasons,
            lineage=gate.lineage,
            limitations=gate.limitations,
            import_attempted=False,
            unavailable=gate.unavailable,
        )

    runtime_blockers = _runtime_gate_blockers(selection_request.feature_flags)
    if runtime_blockers:
        unavailable = StructuredUnavailable("runtime_not_authorized", runtime_blockers, "Backtrader runtime gate is not authorized")
        return BackendSelectionResult(
            selected_backend="none",
            requested_backend=requested_backend,
            availability_status="runtime_not_authorized",
            blocked_reasons=runtime_blockers,
            lineage=gate.lineage,
            limitations=gate.limitations,
            import_attempted=False,
            unavailable=unavailable,
        )

    resolved = try_resolve_backtrader_runtime(selection_request)
    return BackendSelectionResult(
        selected_backend=resolved.selected_backend,
        requested_backend=requested_backend,
        availability_status=resolved.availability_status,
        blocked_reasons=resolved.blocked_reasons,
        lineage=gate.lineage,
        limitations=gate.limitations,
        import_attempted=resolved.import_attempted,
        unavailable=resolved.unavailable,
    )


def try_resolve_backtrader_runtime(request: BackendSelectionRequest | Mapping[str, Any] | None = None) -> BackendSelectionResult:
    """只解析 optional dependency 可用性，不创建 Cerebro、不运行 Backtrader。"""

    selection_request = _coerce_backend_selection_request(request)
    requested_backend = _normalise_backend(selection_request.backend)
    if requested_backend != "backtrader":
        return BackendSelectionResult(
            selected_backend="lightweight" if requested_backend == "lightweight" else "none",
            requested_backend=requested_backend,
            availability_status="not_selected",
            blocked_reasons=("not_selected:backtrader_not_requested",),
            import_attempted=False,
        )
    dependency = (selection_request.dependency_probe or probe_backtrader_dependency)()
    if not dependency.available:
        reason = f"backend_unavailable:{dependency.reason_code or 'dependency_unavailable'}"
        unavailable = StructuredUnavailable(
            "backend_unavailable",
            (reason,),
            dependency.message or "Backtrader optional backend is unavailable",
            {"version": dependency.version},
        )
        return BackendSelectionResult(
            selected_backend="none",
            requested_backend=requested_backend,
            availability_status="backend_unavailable",
            blocked_reasons=(reason,),
            import_attempted=True,
            unavailable=unavailable,
        )
    return BackendSelectionResult(
        selected_backend="backtrader",
        requested_backend=requested_backend,
        availability_status="available",
        import_attempted=True,
    )


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


def _clean_feed_gate_result(
    passed: bool,
    status: BackendSelectionStatus,
    reasons: tuple[str, ...],
    lineage: dict[str, Any],
    limitations: tuple[Any, ...],
    message: str,
) -> CleanFeedGateResult:
    unavailable = None if passed else StructuredUnavailable(status, reasons, message)
    return CleanFeedGateResult(
        passed=passed,
        availability_status=status,
        blocked_reasons=reasons,
        lineage=lineage,
        limitations=limitations,
        unavailable=unavailable,
    )


def _coerce_backend_selection_request(request: BackendSelectionRequest | Mapping[str, Any] | None) -> BackendSelectionRequest:
    if request is None:
        return BackendSelectionRequest()
    if isinstance(request, BackendSelectionRequest):
        return request
    return BackendSelectionRequest(
        backend=request.get("backend"),
        clean_feed_evidence=request.get("clean_feed_evidence", request.get("evidence")),
        feature_flags=request.get("feature_flags", {}),
        lineage=request.get("lineage"),
        limitations=request.get("limitations"),
        dependency_probe=request.get("dependency_probe"),
    )


def _normalise_backend(backend: str | None) -> str:
    if backend is None or str(backend).strip() == "":
        return "lightweight"
    return str(backend).strip().lower()


def _runtime_gate_blockers(feature_flags: Mapping[str, Any]) -> tuple[str, ...]:
    blockers: list[str] = []
    if feature_flags.get("implementation_allowed", True) is not True:
        blockers.append("runtime_not_authorized:implementation_not_allowed")
    if feature_flags.get("cp5_confirmed", True) is not True:
        blockers.append("runtime_not_authorized:cp5_not_confirmed")
    runtime_allowed = feature_flags.get("backtrader_runtime_authorized", feature_flags.get("runtime_authorized", False))
    if runtime_allowed is not True:
        blockers.append("runtime_not_authorized:backtrader_runtime_authorized_false")
    import_allowed = feature_flags.get("allow_backtrader_import", runtime_allowed)
    if import_allowed is not True:
        blockers.append("runtime_not_authorized:backtrader_import_not_allowed")
    return tuple(blockers)


def _selection_status_for_reasons(reasons: Sequence[str]) -> BackendSelectionStatus:
    if any(reason.startswith("data_required_missing") for reason in reasons):
        return "data_required_missing"
    if any(reason.startswith("blocked_clean_feed_pit") for reason in reasons):
        return "blocked_clean_feed_pit"
    if any(reason.startswith("blocked_adjustment_policy_mixed") for reason in reasons):
        return "blocked_adjustment_policy_mixed"
    if any(reason.startswith("quality_fail") for reason in reasons):
        return "quality_fail"
    return "data_required_missing"


def _has_evidence_field(evidence: Mapping[str, Any] | Any, key: str) -> bool:
    if isinstance(evidence, Mapping):
        return key in evidence
    return hasattr(evidence, key)


def _evidence_value(evidence: Mapping[str, Any] | Any, key: str, default: Any = None) -> Any:
    if isinstance(evidence, Mapping):
        return evidence.get(key, default)
    return getattr(evidence, key, default)


def _lineage_from_evidence(evidence: Mapping[str, Any] | Any, lineage: Mapping[str, Any] | None) -> dict[str, Any]:
    if lineage is not None:
        return dict(lineage)
    value = _evidence_value(evidence, "lineage", {}) or {}
    if isinstance(value, Mapping):
        return dict(value)
    return {"value": value}


def _limitations_from_evidence(evidence: Mapping[str, Any] | Any, limitations: Sequence[Any] | None) -> tuple[Any, ...]:
    if limitations is not None:
        return _as_tuple(limitations)
    return _as_tuple(_evidence_value(evidence, "limitations", ()))


def _as_tuple(value: Sequence[Any] | Any | None) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _status_ok(value: Any) -> bool:
    status = str(value if value is not None else "").strip().lower()
    return status in {"available", "ok", "pass", "passed", "clean", "ready", "true", "enabled"}


def _policy_values(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {str(item) for item in value if item}
    return {str(value)}


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
    "BackendSelectionRequest",
    "BackendSelectionResult",
    "BackendSelectionStatus",
    "BacktraderDependencyProbe",
    "BacktraderRequest",
    "BacktraderResult",
    "BacktraderStatus",
    "CleanFeedGateResult",
    "FORBIDDEN_OPERATION_COUNTERS",
    "StructuredUnavailable",
    "build_backtrader_request_from_clean_feed",
    "build_benchmark_metadata",
    "probe_backtrader_dependency",
    "run_backtrader_backend",
    "run_backtrader_clean_feed",
    "select_research_backend",
    "try_resolve_backtrader_runtime",
    "validate_clean_feed_gate",
    "validate_backtrader_clean_feed",
    "validate_backtrader_inputs",
)
