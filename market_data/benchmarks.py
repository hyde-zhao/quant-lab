"""沪深 300 本地 benchmark 只读 resolver。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from .contracts import (
    CONNECTOR_ERROR_TYPES,
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    SOURCE_TUSHARE,
)
from .lake_layout import LakeLayout
from .readers import QualityPolicy, ReaderResult, read_dataset

BENCHMARK_STATUSES = ("available", "unavailable", "required_missing", "quality_failed")
BENCHMARK_KINDS = ("price_index", "total_return_index", "adjusted_index", "policy_unconfirmed")
DEFAULT_INDEX_CODE = "399300.SZ"
PROVIDER_INTERFACE = "index_daily"
DENOMINATOR_MODE_BENCHMARK = "trade_calendar_open_dates"
REPORT_BENCHMARK_KINDS = ("hs300", "proxy_baseline", "hs300_required")
BENCHMARK_POLICY_FIELDS = (
    "benchmark_policy_id",
    "benchmark_kind",
    "hs300_available",
    "hs300_coverage_ratio",
    "proxy_baseline_used",
    "benchmark_missing_reason",
)
_BENCHMARK_POLICY_HS300_FIELDS = frozenset({"hs300_available", "hs300_coverage_ratio"})
AMBIGUOUS_BENCHMARK_FIELDS = frozenset(
    {
        "benchmark_total_return",
        "benchmark_annual_return",
        "benchmark_excess_return",
        "benchmark_excess_annual_return",
        "excess_return",
        "excess_annual_return",
    }
)


@dataclass(frozen=True, slots=True)
class BenchmarkCoverage:
    numerator: int
    denominator: int
    ratio: float
    missing_trade_dates: list[str] = field(default_factory=list)
    gap_reason: str | None = None
    denominator_mode: str = DENOMINATOR_MODE_BENCHMARK
    price_trade_dates_count: int | None = None
    price_overlap_count: int | None = None

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkPolicy:
    benchmark_kind: str = "policy_unconfirmed"
    confirmed: bool = False
    required: bool = False
    quality_threshold: float = 1.0
    allow_warn: bool = False

    @classmethod
    def from_config(
        cls,
        config: Mapping[str, Any] | "BenchmarkPolicy" | None = None,
        *,
        required: bool = False,
    ) -> "BenchmarkPolicy":
        if isinstance(config, BenchmarkPolicy):
            return cls(
                benchmark_kind=config.benchmark_kind,
                confirmed=config.confirmed,
                required=config.required or required,
                quality_threshold=config.quality_threshold,
                allow_warn=config.allow_warn,
            )
        values = dict(config or {})
        benchmark_kind = str(values.get("benchmark_kind") or "policy_unconfirmed")
        if benchmark_kind not in BENCHMARK_KINDS:
            benchmark_kind = "policy_unconfirmed"
        confirmed = bool(values.get("confirmed", False)) and benchmark_kind != "policy_unconfirmed"
        return cls(
            benchmark_kind=benchmark_kind,
            confirmed=confirmed,
            required=bool(values.get("required", required)),
            quality_threshold=float(values.get("quality_threshold", 1.0)),
            allow_warn=bool(values.get("allow_warn", False)),
        )

    def to_quality_policy(self) -> QualityPolicy:
        return QualityPolicy(allow_warn=self.allow_warn, required=self.required)

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NextAction:
    type: str
    owner: str
    allowed_executor: str = "market_data_cli_or_equivalent_job"
    auto_execute: bool = False
    message_code: str = "benchmark_missing"

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RemediationJobSpec:
    dataset: str = DATASET_HS300_INDEX
    target_dataset: str = DATASET_HS300_INDEX
    source: str = SOURCE_TUSHARE
    interface: str = INTERFACE_HS300_INDEX_DAILY
    provider_interface: str = PROVIDER_INTERFACE
    index_code: str = DEFAULT_INDEX_CODE
    start_date: str = ""
    end_date: str = ""
    lake_root: str | None = None
    run_id: str = ""
    batch_id: str = ""
    resume_policy: dict[str, str] = field(default_factory=dict)
    dry_run: bool = True
    raw_path: str | None = None
    manifest_path: str | None = None
    canonical_path: str | None = None
    quality_path: str | None = None
    catalog_path: str | None = None
    gold_path: str | None = None
    error_enum: list[str] = field(default_factory=list)
    reason: str = "benchmark_missing"

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    status: str
    dataset: str
    source: str
    index_code: str
    interface: str
    start_date: str
    end_date: str
    available_start_date: str | None
    available_end_date: str | None
    coverage: BenchmarkCoverage
    quality_status: str
    missing_reason: str | None
    required: bool
    benchmark_kind: str
    next_action: NextAction | None
    remediation_job_spec: RemediationJobSpec | None
    catalog_entry: Any | None
    run_id: str | None
    lineage: dict[str, Any]
    frame: pd.DataFrame | None = field(default=None, repr=False, compare=False)

    @property
    def available(self) -> bool:
        return self.status == "available"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "dataset": self.dataset,
            "source": self.source,
            "index_code": self.index_code,
            "interface": self.interface,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "available_start_date": self.available_start_date,
            "available_end_date": self.available_end_date,
            "coverage": self.coverage.to_metadata(),
            "denominator_mode": self.coverage.denominator_mode,
            "price_overlap": {
                "price_trade_dates_count": self.coverage.price_trade_dates_count,
                "price_overlap_count": self.coverage.price_overlap_count,
            }
            if self.coverage.price_trade_dates_count is not None
            else None,
            "quality_status": self.quality_status,
            "missing_reason": self.missing_reason,
            "required": self.required,
            "benchmark_kind": self.benchmark_kind,
            "next_action": self.next_action.to_metadata() if self.next_action else None,
            "remediation_job_spec": self.remediation_job_spec.to_metadata()
            if self.remediation_job_spec
            else None,
            "catalog_entry": _json_safe(self.catalog_entry),
            "run_id": self.run_id,
            "lineage": _json_safe(self.lineage),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkPolicyResult:
    """CR011-S01 benchmark policy 消费合同。

    该对象只归一化调用方传入的 benchmark/proxy 信息，不读取 lake、不联网、
    不触发 fetch/backfill。`hs300_available` 与 `hs300_coverage_ratio` 是
    policy metadata，不代表 proxy 可写入真实 hs300 指标字段。
    """

    benchmark_policy_id: str
    benchmark_kind: str
    benchmark_status: str
    hs300_available: bool
    hs300_coverage_ratio: float | None
    proxy_baseline_used: bool
    benchmark_missing_reason: str | None
    index_code: str = DEFAULT_INDEX_CODE
    benchmark_source_kind: str | None = None
    quality_status: str | None = None
    readiness_status: str | None = None
    coverage: Mapping[str, Any] | None = None
    benchmark_result: Mapping[str, Any] | None = None
    proxy_baseline: Mapping[str, Any] | None = None
    proxy_metrics: Mapping[str, Any] | None = None
    hs300_metrics: Mapping[str, Any] | None = None
    allowed_claims: tuple[str, ...] = field(default_factory=tuple)
    blocked_claims: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    lineage: Mapping[str, Any] = field(default_factory=dict)
    limitations: tuple[Any, ...] = field(default_factory=tuple)

    def to_metadata(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "benchmark_policy_id": self.benchmark_policy_id,
            "benchmark_kind": self.benchmark_kind,
            "benchmark_status": self.benchmark_status,
            "hs300_available": self.hs300_available,
            "hs300_coverage_ratio": self.hs300_coverage_ratio,
            "proxy_baseline_used": self.proxy_baseline_used,
            "benchmark_missing_reason": self.benchmark_missing_reason,
            "index_code": self.index_code,
            "benchmark_source_kind": self.benchmark_source_kind,
            "quality_status": self.quality_status,
            "readiness_status": self.readiness_status,
            "coverage": _json_safe(self.coverage),
            "allowed_claims": list(self.allowed_claims),
            "blocked_claims": _json_safe(list(self.blocked_claims)),
            "lineage": _json_safe(dict(self.lineage)),
            "known_limitations": _json_safe(list(self.limitations)),
        }
        if self.benchmark_result is not None:
            payload["benchmark_result"] = _json_safe(dict(self.benchmark_result))
        if self.hs300_available:
            if self.benchmark_result is not None:
                payload["hs300_index"] = _json_safe(dict(self.benchmark_result))
            payload.update(_prefixed_metric_payload("hs300", self.hs300_metrics))
        elif self.proxy_baseline_used:
            payload["proxy_baseline"] = _proxy_baseline_metadata(self.proxy_baseline)
            payload.update(_prefixed_metric_payload("proxy", self.proxy_metrics))
        return _strip_disallowed_benchmark_fields(payload, allow_hs300=self.hs300_available)


def build_benchmark_policy_result(
    result: BenchmarkResult | Mapping[str, Any] | None = None,
    *,
    policy_id: str = "hs300_required",
    proxy_baseline_used: bool | None = None,
    proxy_metrics: Mapping[str, Any] | None = None,
    hs300_metrics: Mapping[str, Any] | None = None,
    proxy_baseline: Mapping[str, Any] | None = None,
    allowed_claims: Sequence[str] | None = None,
    blocked_claims: Sequence[Mapping[str, Any]] | None = None,
    limitations: Sequence[Any] | None = None,
) -> BenchmarkPolicyResult:
    """冻结真实 benchmark policy metadata，并隔离 proxy / hs300 字段。"""

    metadata = _benchmark_result_metadata(result)
    status = _benchmark_status_from_metadata(metadata)
    hs300_available = _is_available_hs300_policy_result(result, metadata)
    required = _policy_requires_hs300(policy_id, metadata)
    if not metadata:
        status = "required_missing" if required else "proxy_only"
    resolved_proxy_used = bool(proxy_baseline_used) if proxy_baseline_used is not None else (not hs300_available and not required)
    benchmark_kind = (
        "hs300"
        if hs300_available
        else "proxy_baseline"
        if resolved_proxy_used
        else "hs300_required"
    )
    missing_reason = None if hs300_available else _benchmark_missing_reason_from_metadata(metadata, status, required)
    coverage = _coverage_metadata(metadata)
    coverage_ratio = _coverage_ratio(metadata, coverage, hs300_available)
    source_kind = _benchmark_source_kind(metadata)
    lineage = metadata.get("lineage") if isinstance(metadata.get("lineage"), Mapping) else {}

    resolved_allowed = list(allowed_claims or ())
    if hs300_available and "real_benchmark_research" not in resolved_allowed:
        resolved_allowed.append("real_benchmark_research")

    resolved_blocked = [dict(item) for item in blocked_claims or () if isinstance(item, Mapping)]
    if required and not hs300_available and not any(item.get("claim") == "real_benchmark_research" for item in resolved_blocked):
        resolved_blocked.append(
            {
                "claim": "real_benchmark_research",
                "reason_code": missing_reason or status or "required_missing",
                "dataset": DATASET_HS300_INDEX,
                "severity": "ERROR",
                "details": {
                    "benchmark_status": status,
                    "benchmark_missing_reason": missing_reason,
                    "benchmark_policy_id": policy_id,
                },
            }
        )

    resolved_limitations = list(limitations or ())
    if not hs300_available and resolved_proxy_used:
        resolved_limitations.append(
            {
                "code": "real_benchmark_unavailable_proxy_baseline",
                "benchmark_missing_reason": missing_reason,
                "limitation": "proxy_baseline is not real hs300_index and must not populate hs300_* metrics.",
            }
        )

    return BenchmarkPolicyResult(
        benchmark_policy_id=str(policy_id),
        benchmark_kind=benchmark_kind,
        benchmark_status=status,
        hs300_available=hs300_available,
        hs300_coverage_ratio=coverage_ratio,
        proxy_baseline_used=resolved_proxy_used,
        benchmark_missing_reason=missing_reason,
        index_code=str(metadata.get("index_code") or DEFAULT_INDEX_CODE),
        benchmark_source_kind=source_kind,
        quality_status=_optional_str(metadata.get("quality_status")),
        readiness_status=_optional_str(metadata.get("readiness_status") or metadata.get("dataset_status")),
        coverage=coverage,
        benchmark_result=metadata or None,
        proxy_baseline=proxy_baseline,
        proxy_metrics=proxy_metrics,
        hs300_metrics=hs300_metrics,
        allowed_claims=tuple(resolved_allowed),
        blocked_claims=tuple(resolved_blocked),
        lineage=lineage,
        limitations=tuple(resolved_limitations),
    )


def build_benchmark_field_payload(
    result: BenchmarkResult | None = None,
    proxy_metrics: Mapping[str, Any] | None = None,
    hs300_metrics: Mapping[str, Any] | None = None,
    proxy_baseline: Mapping[str, Any] | None = None,
    *,
    include_proxy_when_hs300_available: bool = False,
) -> dict[str, Any]:
    """构建 proxy / hs300 强隔离的报告字段 payload。

    该 helper 只做字段命名和可见性归一，不读取 lake、不调用 resolver、
    不触发 fetch/backfill。真实 hs300 可用的唯一条件是传入的
    BenchmarkResult 为 available、dataset 为 hs300_index 且 missing_reason 为空。
    """

    benchmark_result = result.to_metadata() if result is not None else None
    real_available = _is_available_hs300_result(result)
    if real_available:
        payload: dict[str, Any] = {
            "benchmark_status": "available",
            "benchmark_kind": "hs300",
            "benchmark_missing_reason": None,
            "missing_reason": None,
            "benchmark_result": benchmark_result,
            "hs300_index": benchmark_result,
        }
        payload.update(_prefixed_metric_payload("hs300", hs300_metrics))
        if include_proxy_when_hs300_available:
            payload["proxy_baseline"] = _proxy_baseline_metadata(proxy_baseline)
            payload.update(_prefixed_metric_payload("proxy", proxy_metrics))
        return _strip_disallowed_benchmark_fields(payload, allow_hs300=True)

    status = result.status if result is not None else "proxy_only"
    reason = (
        result.missing_reason
        if result is not None and result.missing_reason
        else "not_requested"
        if result is None
        else status
    )
    payload = {
        "benchmark_status": status,
        "benchmark_kind": "proxy_baseline",
        "benchmark_missing_reason": reason,
        "missing_reason": reason,
        "proxy_baseline": _proxy_baseline_metadata(proxy_baseline),
    }
    if benchmark_result is not None:
        payload["benchmark_result"] = benchmark_result
    payload.update(_prefixed_metric_payload("proxy", proxy_metrics))
    return _strip_disallowed_benchmark_fields(payload, allow_hs300=False)


def build_next_action(reason: str, required: bool) -> NextAction:
    action_type = "confirm_benchmark_policy" if reason == "policy_unconfirmed" else "run_data_layer_backfill"
    message_code = {
        "policy_unconfirmed": "benchmark_policy_unconfirmed",
        "quality_failed": "benchmark_quality_failed",
        "coverage_gap": "benchmark_required_missing" if required else "benchmark_missing",
        "calendar_missing": "benchmark_calendar_missing",
        "price_benchmark_overlap_missing": "benchmark_price_overlap_missing",
        "missing_dataset": "benchmark_required_missing" if required else "benchmark_missing",
        "canonical_missing": "benchmark_required_missing" if required else "benchmark_missing",
        "lake_root_missing": "benchmark_required_missing" if required else "benchmark_missing",
    }.get(reason, "benchmark_required_missing" if required else "benchmark_missing")
    return NextAction(type=action_type, owner="user", auto_execute=False, message_code=message_code)


def build_hs300_remediation_spec(
    *,
    start_date: str,
    end_date: str,
    lake_root_hint: str | Path | None,
    reason: str,
    index_code: str = DEFAULT_INDEX_CODE,
    run_id: str | None = None,
    batch_id: str | None = None,
) -> RemediationJobSpec:
    lake_root = str(lake_root_hint) if lake_root_hint is not None else None
    layout = LakeLayout(lake_root) if lake_root is not None else None
    resolved_run_id = run_id or f"hs300-{_compact(start_date)}-{_compact(end_date)}"
    resolved_batch_id = batch_id or f"hs300-{_compact(start_date)}-{_compact(end_date)}-b1"
    return RemediationJobSpec(
        index_code=index_code,
        start_date=start_date,
        end_date=end_date,
        lake_root=lake_root,
        run_id=resolved_run_id,
        batch_id=resolved_batch_id,
        resume_policy={
            "success": "skip",
            "failed": "retry",
            "partial_success": "retry",
            "duplicate_manifest": "fail",
        },
        dry_run=True,
        raw_path=str(layout.raw_batch_path(SOURCE_TUSHARE, INTERFACE_HS300_INDEX_DAILY, start_date, resolved_batch_id))
        if layout
        else None,
        manifest_path=str(layout.manifest_path()) if layout else None,
        canonical_path=str(layout.canonical_dataset_root(DATASET_HS300_INDEX)) if layout else None,
        quality_path=str(layout.quality_root / resolved_run_id / f"{DATASET_HS300_INDEX}_quality.csv") if layout else None,
        catalog_path=str(layout.catalog_root / "catalog.json") if layout else None,
        gold_path=str(layout.gold_root / DATASET_HS300_INDEX) if layout else None,
        error_enum=list(dict.fromkeys((*CONNECTOR_ERROR_TYPES, "duplicate_manifest"))),
        reason=reason,
    )


def resolve_hs300_benchmark(
    lake_root: str | Path | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    policy: BenchmarkPolicy | Mapping[str, Any] | None = None,
    *,
    index_code: str = DEFAULT_INDEX_CODE,
    required: bool = False,
    price_trade_dates: Sequence[str] | None = None,
) -> BenchmarkResult:
    if start_date is None or end_date is None:
        raise ValueError("start_date 和 end_date 必须显式传入")
    resolved_policy = BenchmarkPolicy.from_config(policy, required=required)
    if not resolved_policy.confirmed:
        return _non_available_result(
            "required_missing" if resolved_policy.required else "unavailable",
            reason="policy_unconfirmed",
            quality_status="missing",
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
        )

    reader = read_dataset(
        DATASET_HS300_INDEX,
        lake_root,
        filters={"start": start_date, "end": end_date, "index_code": index_code},
        quality_policy=resolved_policy.to_quality_policy(),
        required=resolved_policy.required,
    )
    if not reader.available or reader.frame is None:
        reason = _issue_reason(reader)
        status = "quality_failed" if reader.status == "quality_failed" else ("required_missing" if resolved_policy.required else "unavailable")
        return _non_available_result(
            status,
            reason=reason,
            quality_status=_reader_quality_status(reader),
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
            reader=reader,
        )

    frame = reader.frame.sort_values("trade_date").reset_index(drop=True)
    quality_status = _entry_value(reader.catalog_entry, "quality_status") or "pass"
    coverage = _coverage(lake_root, start_date, end_date, frame)
    if coverage.denominator <= 0 or coverage.missing_trade_dates:
        reason = coverage.gap_reason or "coverage_gap"
        return _non_available_result(
            "required_missing" if resolved_policy.required else "unavailable",
            reason=reason,
            quality_status=quality_status,
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
            reader=reader,
            coverage=coverage,
        )
    coverage = _with_price_overlap(coverage, frame, price_trade_dates, start_date, end_date)
    if (
        price_trade_dates is not None
        and (coverage.price_overlap_count or 0) == 0
    ):
        return _non_available_result(
            "required_missing" if resolved_policy.required else "unavailable",
            reason="price_benchmark_overlap_missing",
            quality_status=quality_status,
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
            reader=reader,
            coverage=BenchmarkCoverage(
                coverage.numerator,
                coverage.denominator,
                coverage.ratio,
                coverage.missing_trade_dates,
                "price_benchmark_overlap_missing",
                coverage.denominator_mode,
                coverage.price_trade_dates_count,
                coverage.price_overlap_count,
            ),
        )
    if not _lineage_available(reader, frame):
        return _non_available_result(
            "quality_failed",
            reason="lineage_unavailable",
            quality_status="fail",
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
            reader=reader,
            coverage=coverage,
        )
    if _frame_benchmark_kind(frame) != resolved_policy.benchmark_kind:
        return _non_available_result(
            "quality_failed",
            reason="policy_mismatch",
            quality_status="fail",
            start_date=start_date,
            end_date=end_date,
            index_code=index_code,
            policy=resolved_policy,
            lake_root=lake_root,
            reader=reader,
            coverage=coverage,
        )

    available_start = str(frame["trade_date"].min())
    available_end = str(frame["trade_date"].max())
    return BenchmarkResult(
        status="available",
        dataset=DATASET_HS300_INDEX,
        source=_source(reader, frame),
        index_code=index_code,
        interface=INTERFACE_HS300_INDEX_DAILY,
        start_date=start_date,
        end_date=end_date,
        available_start_date=available_start,
        available_end_date=available_end,
        coverage=coverage,
        quality_status=quality_status,
        missing_reason=None,
        required=resolved_policy.required,
        benchmark_kind=resolved_policy.benchmark_kind,
        next_action=None,
        remediation_job_spec=None,
        catalog_entry=reader.catalog_entry,
        run_id=_entry_value(reader.catalog_entry, "latest_manifest_run_id") or _first(frame, "source_run_id"),
        lineage=_lineage(reader, frame),
        frame=frame,
    )


def _non_available_result(
    status: str,
    *,
    reason: str,
    quality_status: str,
    start_date: str,
    end_date: str,
    index_code: str,
    policy: BenchmarkPolicy,
    lake_root: str | Path | None,
    reader: ReaderResult | None = None,
    coverage: BenchmarkCoverage | None = None,
) -> BenchmarkResult:
    return BenchmarkResult(
        status=status,
        dataset=DATASET_HS300_INDEX,
        source=_source(reader, None) if reader is not None else "none",
        index_code=index_code,
        interface=INTERFACE_HS300_INDEX_DAILY,
        start_date=start_date,
        end_date=end_date,
        available_start_date=None,
        available_end_date=None,
        coverage=coverage or BenchmarkCoverage(0, 0, 0.0, [], reason),
        quality_status=quality_status,
        missing_reason=reason,
        required=policy.required,
        benchmark_kind=policy.benchmark_kind,
        next_action=build_next_action(reason, policy.required),
        remediation_job_spec=build_hs300_remediation_spec(
            start_date=start_date,
            end_date=end_date,
            lake_root_hint=lake_root,
            reason=reason,
            index_code=index_code,
        ),
        catalog_entry=reader.catalog_entry if reader else None,
        run_id=_entry_value(reader.catalog_entry, "latest_manifest_run_id") if reader and reader.catalog_entry else None,
        lineage=_lineage(reader, None) if reader else {"status": "lineage_unavailable", "reason": reason},
        frame=None,
    )


def _coverage(
    lake_root: str | Path | None,
    start_date: str,
    end_date: str,
    frame: pd.DataFrame,
) -> BenchmarkCoverage:
    open_dates = _open_trade_dates(lake_root, start_date, end_date)
    if not open_dates:
        return BenchmarkCoverage(0, 0, 0.0, [], "calendar_missing")
    available_dates = set(frame["trade_date"].astype(str))
    missing = [trade_date for trade_date in open_dates if trade_date not in available_dates]
    numerator = len(open_dates) - len(missing)
    denominator = len(open_dates)
    ratio = numerator / denominator if denominator else 0.0
    return BenchmarkCoverage(numerator, denominator, ratio, missing, "coverage_gap" if missing else None)


def _with_price_overlap(
    coverage: BenchmarkCoverage,
    frame: pd.DataFrame,
    price_trade_dates: Sequence[str] | None,
    start_date: str,
    end_date: str,
) -> BenchmarkCoverage:
    if price_trade_dates is None:
        return coverage
    prices_dates = sorted(
        {
            str(item)
            for item in price_trade_dates
            if str(start_date) <= str(item) <= str(end_date)
        }
    )
    benchmark_dates = (
        set(frame["trade_date"].astype(str))
        if "trade_date" in frame.columns
        else set()
    )
    overlap_count = len([item for item in prices_dates if item in benchmark_dates])
    return BenchmarkCoverage(
        coverage.numerator,
        coverage.denominator,
        coverage.ratio,
        coverage.missing_trade_dates,
        coverage.gap_reason,
        coverage.denominator_mode,
        len(prices_dates),
        overlap_count,
    )


def _open_trade_dates(lake_root: str | Path | None, start_date: str, end_date: str) -> list[str]:
    result = read_dataset(
        DATASET_TRADE_CALENDAR,
        lake_root,
        filters={"start": start_date, "end": end_date},
        quality_policy=QualityPolicy(allow_warn=True),
    )
    if not result.available or result.frame is None or "trade_date" not in result.frame.columns:
        return []
    frame = result.frame
    if "is_open" in frame.columns:
        frame = frame[frame["is_open"].astype(bool)]
    return sorted(set(frame["trade_date"].astype(str)))


def _issue_reason(reader: ReaderResult) -> str:
    if reader.issues:
        code = str(reader.issues[0].get("code") or reader.status)
        if code == "catalog_missing":
            return "missing_dataset"
        if code == "canonical_missing":
            return "missing_dataset"
        return code
    return reader.status


def _reader_quality_status(reader: ReaderResult) -> str:
    if reader.status == "quality_failed":
        return "fail"
    if reader.catalog_entry is None:
        return "missing"
    return _entry_value(reader.catalog_entry, "quality_status") or "missing"


def _lineage_available(reader: ReaderResult, frame: pd.DataFrame) -> bool:
    if _entry_value(reader.catalog_entry, "latest_manifest_run_id") or _entry_value(reader.catalog_entry, "lineage_raw_checksum"):
        return True
    return bool(_first(frame, "source_run_id") and _first(frame, "lineage_raw_checksum"))


def _lineage(reader: ReaderResult | None, frame: pd.DataFrame | None) -> dict[str, Any]:
    if reader is None:
        return {"status": "lineage_unavailable"}
    manifest_run = _entry_value(reader.catalog_entry, "latest_manifest_run_id")
    source_run = _first(frame, "source_run_id") if frame is not None else None
    checksum = _entry_value(reader.catalog_entry, "lineage_raw_checksum") or (_first(frame, "lineage_raw_checksum") if frame is not None else None)
    if not (manifest_run or source_run or checksum):
        return {"status": "lineage_unavailable"}
    return {
        "manifest_run_id": manifest_run,
        "source_run_id": source_run,
        "lineage_raw_checksum": checksum,
    }


def _source(reader: ReaderResult | None, frame: pd.DataFrame | None) -> str:
    source = _entry_value(reader.catalog_entry, "source") if reader else None
    if source:
        return str(source)
    if frame is not None:
        frame_source = _first(frame, "source")
        if frame_source:
            return str(frame_source)
    return "none"


def _frame_benchmark_kind(frame: pd.DataFrame) -> str:
    if "benchmark_kind" not in frame.columns or frame.empty:
        return "policy_unconfirmed"
    values = {str(value) for value in frame["benchmark_kind"].dropna().unique()}
    if len(values) != 1:
        return "policy_unconfirmed"
    return next(iter(values))


def _first(frame: pd.DataFrame | None, column: str) -> Any | None:
    if frame is None or column not in frame.columns or frame.empty:
        return None
    values = frame[column].dropna()
    return None if values.empty else values.iloc[0]


def _entry_value(entry: Any | None, field_name: str) -> Any | None:
    if entry is None:
        return None
    if isinstance(entry, Mapping):
        return entry.get(field_name)
    return getattr(entry, field_name, None)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _benchmark_result_metadata(result: BenchmarkResult | Mapping[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, BenchmarkResult):
        return result.to_metadata()
    if hasattr(result, "to_metadata") and callable(result.to_metadata):
        raw = result.to_metadata()
        return dict(raw) if isinstance(raw, Mapping) else {}
    if isinstance(result, Mapping):
        return dict(result)
    return {}


def _benchmark_status_from_metadata(metadata: Mapping[str, Any]) -> str:
    return str(metadata.get("benchmark_status") or metadata.get("status") or "required_missing")


def _benchmark_missing_reason_from_metadata(metadata: Mapping[str, Any], status: str, required: bool) -> str:
    value = metadata.get("benchmark_missing_reason") or metadata.get("missing_reason")
    if value:
        return str(value)
    if status and status not in {"available", "proxy_only"}:
        return str(status)
    return "required_missing" if required else "not_requested"


def _policy_requires_hs300(policy_id: str, metadata: Mapping[str, Any]) -> bool:
    if bool(metadata.get("required", False)):
        return True
    return str(policy_id).endswith("_required") or str(policy_id) == "hs300_required"


def _coverage_metadata(metadata: Mapping[str, Any]) -> Mapping[str, Any] | None:
    coverage = metadata.get("coverage")
    return coverage if isinstance(coverage, Mapping) else None


def _coverage_ratio(
    metadata: Mapping[str, Any],
    coverage: Mapping[str, Any] | None,
    hs300_available: bool,
) -> float | None:
    value = metadata.get("hs300_coverage_ratio")
    if value is None and coverage is not None:
        value = coverage.get("ratio")
    if value is None:
        return None if not hs300_available else 1.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _benchmark_source_kind(metadata: Mapping[str, Any]) -> str | None:
    source_kind = metadata.get("benchmark_source_kind")
    if source_kind:
        return str(source_kind)
    benchmark_kind = str(metadata.get("benchmark_kind") or "")
    if benchmark_kind and benchmark_kind not in REPORT_BENCHMARK_KINDS:
        return benchmark_kind
    return None


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _is_available_hs300_policy_result(
    result: BenchmarkResult | Mapping[str, Any] | None,
    metadata: Mapping[str, Any],
) -> bool:
    if _is_available_hs300_result(result if isinstance(result, BenchmarkResult) else None):
        return True
    status = _benchmark_status_from_metadata(metadata)
    missing_reason = metadata.get("benchmark_missing_reason") or metadata.get("missing_reason")
    if status != "available" or missing_reason:
        return False
    dataset = str(metadata.get("dataset") or DATASET_HS300_INDEX)
    return dataset == DATASET_HS300_INDEX


def _is_available_hs300_result(result: BenchmarkResult | None) -> bool:
    return (
        isinstance(result, BenchmarkResult)
        and result.available
        and result.dataset == DATASET_HS300_INDEX
        and result.missing_reason is None
    )


def _proxy_baseline_metadata(proxy_baseline: Mapping[str, Any] | None) -> dict[str, Any]:
    baseline = {
        "name": "proxy_baseline",
        "kind": "same_universe_equal_weight_buy_and_hold",
        "limitations": [
            "proxy baseline only",
            "not real hs300_index",
            "must not populate hs300_* fields",
        ],
    }
    if proxy_baseline:
        baseline.update(_json_safe(proxy_baseline))
    return baseline


def _prefixed_metric_payload(prefix: str, metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    if not metrics:
        return {}
    payload: dict[str, Any] = {}
    for raw_key, value in metrics.items():
        key = str(raw_key)
        target_key = _metric_target_key(prefix, key)
        if target_key is None:
            continue
        payload[target_key] = _json_safe(value)
    return payload


def _metric_target_key(prefix: str, key: str) -> str | None:
    if key.startswith(f"{prefix}_"):
        return key
    if key.startswith("hs300_") or key.startswith("proxy_"):
        return None
    aliases = {
        "benchmark_total_return": "total_return",
        "benchmark_annual_return": "annual_return",
        "benchmark_excess_return": "excess_return",
        "benchmark_excess_annual_return": "excess_annual_return",
        "total_return": "total_return",
        "annual_return": "annual_return",
        "excess_return": "excess_return",
        "excess_annual_return": "excess_annual_return",
        "sharpe": "sharpe",
        "max_drawdown": "max_drawdown",
        "turnover": "turnover",
        "final_value": "final_value",
    }
    if key in aliases:
        return f"{prefix}_{aliases[key]}"
    if key in AMBIGUOUS_BENCHMARK_FIELDS or key.startswith("benchmark_"):
        return None
    return f"{prefix}_{key}"


def _strip_disallowed_benchmark_fields(payload: Mapping[str, Any], *, allow_hs300: bool) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if key in AMBIGUOUS_BENCHMARK_FIELDS:
            continue
        if (
            not allow_hs300
            and key not in _BENCHMARK_POLICY_HS300_FIELDS
            and (key == "hs300_index" or key.startswith("hs300_"))
        ):
            continue
        clean[key] = value
    return clean


def _compact(value: str) -> str:
    return str(value).replace("-", "")


__all__ = [
    "AMBIGUOUS_BENCHMARK_FIELDS",
    "BENCHMARK_KINDS",
    "BENCHMARK_STATUSES",
    "DENOMINATOR_MODE_BENCHMARK",
    "REPORT_BENCHMARK_KINDS",
    "BENCHMARK_POLICY_FIELDS",
    "BenchmarkCoverage",
    "BenchmarkPolicy",
    "BenchmarkPolicyResult",
    "BenchmarkResult",
    "NextAction",
    "RemediationJobSpec",
    "build_benchmark_field_payload",
    "build_benchmark_policy_result",
    "build_hs300_remediation_spec",
    "build_next_action",
    "resolve_hs300_benchmark",
]
