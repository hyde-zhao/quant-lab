"""数据准备编排层：批次规划、节流重试、raw 缓存与 manifest 记录。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
import hashlib
import json
from pathlib import Path
import random
import re
import time
from typing import Any, Callable

import yaml

from engine.akshare_adapter import AdapterError, AdapterProtocol, AdapterResult, AkshareAdapter
from engine.contracts import DATA_PREP_CONFIG_KEYS
from engine.manifest import ManifestStore, ManifestWriteError, ensure_parent_dir, utc_now_ms
from engine.source_registry import SourceRegistryError, validate_exact_source_interface


SCHEMA_VERSION = "1.0"
NON_DETERMINISTIC_PARAM_KEYS = {
    "run_id",
    "requested_at",
    "request_started_at",
    "request_finished_at",
    "completed_at",
    "manifest_written_at",
    "force_refresh",
}


class DataPrepError(Exception):
    """数据准备基础异常。"""


class DataPrepConfigError(DataPrepError):
    """配置读取或校验失败。"""


class RawCacheWriteError(DataPrepError):
    """raw 缓存写入失败。"""


class DataPrepSourceRegistryError(DataPrepError):
    """source/interface 注册表校验失败。"""


@dataclass(slots=True)
class DataPrepConfig:
    request_interval_seconds: float = 2
    batch_size: int = 50
    max_concurrency: int = 1
    max_retries: int = 3
    backoff_policy: str = "exponential_jitter"
    backoff_base_seconds: float = 2
    backoff_max_seconds: float = 60
    recent_trade_days_backfill: int = 5
    raw_cache_retention: str = "keep_forever"
    raw_cache_path_pattern: str = (
        "data/raw/{source}/{interface}/{yyyymmdd}/{batch_id}.{ext}"
    )


@dataclass(slots=True)
class DataPrepRequest:
    source: str
    interface: str
    params: dict[str, Any] = field(default_factory=dict)
    symbols: list[str] = field(default_factory=list)
    date_range: dict[str, str] = field(default_factory=dict)
    batch_size: int | None = None
    force_refresh: bool = False


@dataclass(slots=True)
class BatchSpec:
    source: str
    interface: str
    request_params: dict[str, Any]
    items: tuple[str, ...]
    date_range: dict[str, str]
    batch_id: str
    partition_date: str
    range_key: str
    schema_version: str = SCHEMA_VERSION


@dataclass(slots=True)
class BatchExecutionResult:
    status: str
    attempts: int
    retry_events: list[dict[str, Any]]
    request_started_at: str = ""
    request_finished_at: str = ""
    adapter_result: AdapterResult | None = None
    adapter_error: AdapterError | None = None


@dataclass(slots=True)
class DataPrepRunSummary:
    run_id: str
    total_batches: int
    planned_batches: int
    success_count: int
    partial_success_count: int
    failed_count: int
    skipped_count: int
    manifest_path: str
    raw_paths: list[str]
    statuses: dict[str, str]


class ThrottleState:
    def __init__(self) -> None:
        self.last_request_started: float | None = None


def load_data_prep_config(config_path: str | Path) -> DataPrepConfig:
    """安全读取并校验数据准备配置。"""

    path = Path(config_path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except OSError as exc:
        raise DataPrepConfigError(f"配置读取失败: {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise DataPrepConfigError(f"配置必须是 YAML object: {path}")

    unknown = sorted(set(raw) - set(DATA_PREP_CONFIG_KEYS))
    missing = sorted(set(DATA_PREP_CONFIG_KEYS) - set(raw))
    if unknown:
        raise DataPrepConfigError(f"配置包含未知键: {', '.join(unknown)}")
    if missing:
        raise DataPrepConfigError(f"配置缺少键: {', '.join(missing)}")

    config = DataPrepConfig(**raw)
    _validate_config(config)
    return config


def plan_batches(
    source: str,
    interface: str,
    params: dict[str, Any] | None = None,
    symbols: list[str] | tuple[str, ...] | None = None,
    date_range: dict[str, str] | None = None,
    batch_size: int = 50,
) -> list[BatchSpec]:
    """按 canonical 输入生成稳定批次和可复现 batch_id。"""

    if batch_size <= 0:
        raise DataPrepConfigError(f"batch_size 必须为正数: {batch_size}")
    if not source or not interface:
        raise DataPrepConfigError("source 和 interface 必须为非空字符串")
    try:
        validate_exact_source_interface(source, interface, params or {})
    except SourceRegistryError as exc:
        raise DataPrepSourceRegistryError(str(exc)) from exc

    clean_params = _canonicalize(params or {})
    clean_dates = _normalize_date_range(date_range or {})
    clean_symbols = tuple(sorted({str(symbol) for symbol in symbols or [] if str(symbol)}))
    chunks = _chunk_items(clean_symbols, batch_size) if clean_symbols else [()]

    batches: list[BatchSpec] = []
    for chunk in chunks:
        items = chunk or _single_items(clean_dates)
        request_params = _request_params_for_batch(clean_params, chunk, clean_dates)
        range_key = _range_key(chunk, clean_dates)
        partition_date = _partition_date(clean_params, clean_dates)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "source": source,
            "interface": interface,
            "request_params": request_params,
            "items": list(items),
            "date_range": clean_dates,
        }
        digest16 = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        batch_id = ".".join(
            [
                _safe_id_part(source),
                _safe_id_part(interface),
                _safe_id_part(range_key),
                digest16,
            ]
        )
        batches.append(
            BatchSpec(
                source=source,
                interface=interface,
                request_params=request_params,
                items=items,
                date_range=clean_dates,
                batch_id=batch_id,
                partition_date=partition_date,
                range_key=range_key,
            )
        )
    return batches


def filter_resumable_batches(
    batches: list[BatchSpec],
    manifest_store: ManifestStore,
    force_refresh: bool,
    recent_trade_days_backfill: int,
) -> tuple[list[BatchSpec], list[BatchSpec]]:
    """基于 manifest 最新 success 状态过滤可跳过批次。"""

    if force_refresh:
        return batches, []
    latest = manifest_store.latest_by_batch_id()
    recent_partitions = _recent_partitions(batches, recent_trade_days_backfill)
    runnable: list[BatchSpec] = []
    skipped: list[BatchSpec] = []
    for batch in batches:
        latest_record = latest.get(batch.batch_id)
        is_success = bool(latest_record and latest_record.get("status") == "success")
        is_recent_backfill = _is_recent_backfill_partition(
            batch.partition_date,
            recent_trade_days_backfill,
        ) or batch.partition_date in recent_partitions
        if is_success and not is_recent_backfill:
            skipped.append(batch)
        else:
            runnable.append(batch)
    return runnable, skipped


def run_batch_with_retry(
    batch: BatchSpec,
    adapter: AdapterProtocol,
    config: DataPrepConfig,
    throttle_state: ThrottleState | None = None,
    *,
    now_func: Callable[[], datetime] | None = None,
    sleep_func: Callable[[float], None] | None = None,
    monotonic_func: Callable[[], float] | None = None,
    jitter_func: Callable[[float, float], float] | None = None,
) -> BatchExecutionResult:
    """执行单批请求，最多 1 次初始请求 + max_retries 次重试。"""

    state = throttle_state or ThrottleState()
    now = now_func or (lambda: datetime.now(UTC))
    sleeper = sleep_func or time.sleep
    monotonic = monotonic_func or time.monotonic
    jitter = jitter_func or random.uniform
    retry_events: list[dict[str, Any]] = []
    last_started_at = ""
    last_finished_at = ""

    for attempt_index in range(config.max_retries + 1):
        _wait_for_request_slot(config.request_interval_seconds, state, sleeper, monotonic)
        state.last_request_started = monotonic()
        last_started_at = _format_utc_ms(now())
        try:
            result = adapter.fetch(batch.interface, dict(batch.request_params))
        except Exception as exc:
            result = AdapterError(
                error_type=type(exc).__name__,
                error_message=str(exc),
                retryable=True,
            )
        last_finished_at = _format_utc_ms(now())

        if isinstance(result, AdapterResult) and result.ok:
            status = "partial_success" if result.partial_success else "success"
            return BatchExecutionResult(
                status=status,
                attempts=attempt_index + 1,
                retry_events=retry_events,
                request_started_at=last_started_at,
                request_finished_at=last_finished_at,
                adapter_result=result,
            )
        if getattr(result, "ok", False):
            adapter_result = AdapterResult(
                data=getattr(result, "data", result),
                success_items=list(getattr(result, "success_items", []) or []),
                failed_items=list(getattr(result, "failed_items", []) or []),
                metadata=dict(getattr(result, "metadata", {}) or {}),
            )
            status = "partial_success" if adapter_result.partial_success else "success"
            return BatchExecutionResult(
                status=status,
                attempts=attempt_index + 1,
                retry_events=retry_events,
                request_started_at=last_started_at,
                request_finished_at=last_finished_at,
                adapter_result=adapter_result,
            )

        error = _coerce_adapter_error(result)
        should_retry = error.retryable and attempt_index < config.max_retries
        wait_seconds = (
            compute_backoff_seconds(config, attempt_index, jitter)
            if should_retry
            else 0
        )
        retry_events.append(
            {
                "attempt": attempt_index + 1,
                "failed_at": last_finished_at,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "wait_seconds": wait_seconds,
            }
        )
        if not should_retry:
            return BatchExecutionResult(
                status="failed",
                attempts=attempt_index + 1,
                retry_events=retry_events,
                request_started_at=last_started_at,
                request_finished_at=last_finished_at,
                adapter_error=error,
            )
        sleeper(wait_seconds)

    return BatchExecutionResult(
        status="failed",
        attempts=config.max_retries + 1,
        retry_events=retry_events,
        request_started_at=last_started_at,
        request_finished_at=last_finished_at,
        adapter_error=AdapterError(
            error_type="RetryExhausted",
            error_message="重试耗尽",
            retryable=False,
        ),
    )


def compute_backoff_seconds(
    config: DataPrepConfig,
    attempt_index: int,
    jitter_func: Callable[[float, float], float] | None = None,
) -> float:
    """计算 exponential_jitter 退避等待秒数。"""

    if config.backoff_policy != "exponential_jitter":
        raise DataPrepConfigError(f"不支持的退避策略: {config.backoff_policy}")
    raw_wait = min(
        float(config.backoff_max_seconds),
        float(config.backoff_base_seconds) * (2 ** attempt_index),
    )
    jitter_high = min(float(config.backoff_base_seconds), raw_wait * 0.1)
    jitter = (jitter_func or random.uniform)(0, jitter_high)
    return min(float(config.backoff_max_seconds), raw_wait + jitter)


def write_raw_cache(
    batch: BatchSpec,
    adapter_result: AdapterResult,
    raw_root: str | Path,
    run_id: str,
    *,
    now_func: Callable[[], datetime] | None = None,
) -> str:
    """写入 raw JSONL：第一行 metadata，后续 data/payload 行。"""

    raw_path = (
        Path(raw_root)
        / batch.source
        / batch.interface
        / batch.partition_date
        / f"{batch.batch_id}.jsonl"
    )
    now = now_func or (lambda: datetime.now(UTC))
    try:
        ensure_parent_dir(raw_path)
        metadata = {
            "_record_type": "batch_metadata",
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "batch_id": batch.batch_id,
            "source": batch.source,
            "interface": batch.interface,
            "request_params": batch.request_params,
            "created_at": _format_utc_ms(now()),
        }
        with raw_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            for row in _raw_rows(adapter_result.data):
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
    except ManifestWriteError as exc:
        raise RawCacheWriteError(str(exc)) from exc
    except OSError as exc:
        raise RawCacheWriteError(f"raw 缓存写入失败: {raw_path}: {exc}") from exc
    except TypeError as exc:
        raise RawCacheWriteError(f"raw 响应不可 JSON 序列化: {exc}") from exc
    return str(raw_path)


def run_data_prep(
    request: DataPrepRequest | dict[str, Any],
    config_path: str | Path = "config/data_prep.yaml",
    manifest_path: str | Path = "data/manifests/data_prep_manifest.jsonl",
    raw_root: str | Path = "data/raw",
    adapter: AdapterProtocol | None = None,
    *,
    now_func: Callable[[], datetime] | None = None,
    sleep_func: Callable[[float], None] | None = None,
    monotonic_func: Callable[[], float] | None = None,
    jitter_func: Callable[[float, float], float] | None = None,
) -> DataPrepRunSummary:
    """显式运行数据准备；测试应注入 fake adapter 和临时目录。"""

    config = load_data_prep_config(config_path)
    req = _coerce_request(request)
    batch_size = req.batch_size or config.batch_size
    if batch_size > config.batch_size:
        raise DataPrepConfigError(
            f"单批规模不得超过配置 batch_size={config.batch_size}: {batch_size}"
        )
    batches = plan_batches(
        req.source,
        req.interface,
        req.params,
        req.symbols,
        req.date_range,
        batch_size,
    )
    store = ManifestStore(manifest_path)
    runnable, skipped = filter_resumable_batches(
        batches,
        store,
        req.force_refresh,
        config.recent_trade_days_backfill,
    )
    effective_adapter = adapter or AkshareAdapter()
    run_id = _make_run_id(req, now_func)
    statuses: dict[str, str] = {}
    raw_paths: list[str] = []
    counters = {
        "success": 0,
        "partial_success": 0,
        "failed": 0,
        "skipped": 0,
    }

    for batch in skipped:
        record = _manifest_record(
            batch,
            run_id,
            "skipped",
            attempts=0,
            completed_at=utc_now_ms(),
        )
        store.append(record)
        counters["skipped"] += 1
        statuses[batch.batch_id] = "skipped"

    throttle_state = ThrottleState()
    for batch in runnable:
        store.append(_manifest_record(batch, run_id, "running", attempts=0))
        result = run_batch_with_retry(
            batch,
            effective_adapter,
            config,
            throttle_state,
            now_func=now_func,
            sleep_func=sleep_func,
            monotonic_func=monotonic_func,
            jitter_func=jitter_func,
        )
        raw_path = ""
        error_type = ""
        error_message = ""
        success_items: list[Any] = []
        failed_items: list[Any] = []
        final_status = result.status
        if result.adapter_result is not None:
            success_items = result.adapter_result.success_items or list(batch.items)
            failed_items = result.adapter_result.failed_items
            try:
                raw_path = write_raw_cache(
                    batch,
                    result.adapter_result,
                    raw_root,
                    run_id,
                    now_func=now_func,
                )
                raw_paths.append(raw_path)
            except RawCacheWriteError as exc:
                final_status = "failed"
                error_type = "RawCacheWriteError"
                error_message = str(exc)
        elif result.adapter_error is not None:
            error_type = result.adapter_error.error_type
            error_message = result.adapter_error.error_message
            failed_items = list(batch.items)

        terminal_record = _manifest_record(
            batch,
            run_id,
            final_status,
            requested_at=result.request_started_at,
            request_started_at=result.request_started_at,
            request_finished_at=result.request_finished_at,
            completed_at=utc_now_ms(),
            attempts=result.attempts,
            retry_events=result.retry_events,
            raw_path=raw_path,
            success_items=success_items,
            failed_items=failed_items,
            error_type=error_type,
            error_message=error_message,
        )
        store.append(terminal_record)
        counters[final_status] += 1
        statuses[batch.batch_id] = final_status

    return DataPrepRunSummary(
        run_id=run_id,
        total_batches=len(batches),
        planned_batches=len(runnable),
        success_count=counters["success"],
        partial_success_count=counters["partial_success"],
        failed_count=counters["failed"],
        skipped_count=counters["skipped"],
        manifest_path=str(manifest_path),
        raw_paths=raw_paths,
        statuses=statuses,
    )


def _validate_config(config: DataPrepConfig) -> None:
    checks = {
        "request_interval_seconds": config.request_interval_seconds > 0,
        "batch_size": config.batch_size > 0,
        "max_concurrency": config.max_concurrency == 1,
        "max_retries": config.max_retries >= 0,
        "backoff_base_seconds": config.backoff_base_seconds > 0,
        "backoff_max_seconds": config.backoff_max_seconds > 0,
        "recent_trade_days_backfill": config.recent_trade_days_backfill >= 0,
    }
    for key, ok in checks.items():
        if not ok:
            raise DataPrepConfigError(f"配置值非法: {key}={getattr(config, key)!r}")
    if config.backoff_policy != "exponential_jitter":
        raise DataPrepConfigError(
            f"配置值非法: backoff_policy={config.backoff_policy!r}"
        )
    if config.raw_cache_retention != "keep_forever":
        raise DataPrepConfigError(
            f"配置值非法: raw_cache_retention={config.raw_cache_retention!r}"
        )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _canonicalize(value[key])
            for key in sorted(value)
            if value[key] is not None and key not in NON_DETERMINISTIC_PARAM_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value if item is not None]
    return value


def _normalize_date_range(date_range: dict[str, str]) -> dict[str, str]:
    if not date_range:
        return {}
    normalized = {
        key: str(value)
        for key, value in sorted(date_range.items())
        if value is not None
    }
    if set(normalized) - {"start", "end"}:
        raise DataPrepConfigError("date_range 只允许 start/end")
    return normalized


def _chunk_items(items: tuple[str, ...], batch_size: int) -> list[tuple[str, ...]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def _single_items(date_range: dict[str, str]) -> tuple[str, ...]:
    if date_range:
        return (f"{date_range.get('start', '')}:{date_range.get('end', '')}",)
    return ("single",)


def _request_params_for_batch(
    params: dict[str, Any],
    symbols: tuple[str, ...],
    date_range: dict[str, str],
) -> dict[str, Any]:
    request_params = dict(params)
    if symbols:
        request_params["symbols"] = list(symbols)
    if date_range:
        request_params["date_range"] = dict(date_range)
    return _canonicalize(request_params)


def _range_key(symbols: tuple[str, ...], date_range: dict[str, str]) -> str:
    if symbols:
        return f"symbols-{symbols[0]}-{symbols[-1]}"
    if date_range:
        return f"dates-{date_range.get('start', '')}-{date_range.get('end', '')}"
    return "single"


def _partition_date(params: dict[str, Any], date_range: dict[str, str]) -> str:
    if date_range.get("start"):
        return _compact_date(date_range["start"])
    for key in ("trade_date", "snapshot_date", "requested_for"):
        value = params.get(key)
        if value:
            return _compact_date(str(value))
    return "00000000"


def _compact_date(value: str) -> str:
    compact = re.sub(r"[^0-9]", "", value)
    return compact[:8] if len(compact) >= 8 else "00000000"


def _safe_id_part(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_\\-]+", "-", str(value)).strip("-")
    return safe or "na"


def _recent_partitions(batches: list[BatchSpec], recent_count: int) -> set[str]:
    if recent_count <= 0:
        return set()
    candidates = [
        batch.partition_date
        for batch in batches
        if _is_recent_backfill_partition(batch.partition_date, recent_count)
    ]
    partitions = sorted(
        {batch.partition_date for batch in batches if batch.partition_date != "00000000"}
    )
    return set(partitions[-recent_count:]).intersection(candidates)


def _is_recent_backfill_partition(partition_date: str, recent_count: int) -> bool:
    if recent_count <= 0 or partition_date == "00000000":
        return False
    try:
        parsed = date.fromisoformat(
            f"{partition_date[:4]}-{partition_date[4:6]}-{partition_date[6:8]}"
        )
    except ValueError:
        return False
    # 没有交易日历时采用自然日近似窗口。乘以 3 保守覆盖周末和节假日，
    # 但不会把明显历史区间误判为最近回补批次。
    return 0 <= (date.today() - parsed).days <= recent_count * 3


def _wait_for_request_slot(
    interval_seconds: float,
    state: ThrottleState,
    sleep_func: Callable[[float], None],
    monotonic_func: Callable[[], float],
) -> None:
    if state.last_request_started is None:
        return
    elapsed = monotonic_func() - state.last_request_started
    remaining = interval_seconds - elapsed
    if remaining > 0:
        sleep_func(remaining)


def _coerce_adapter_error(value: Any) -> AdapterError:
    if isinstance(value, AdapterError):
        return value
    error_type = getattr(value, "error_type", type(value).__name__)
    error_message = getattr(value, "error_message", str(value))
    retryable = bool(getattr(value, "retryable", True))
    return AdapterError(error_type=error_type, error_message=error_message, retryable=retryable)


def _raw_rows(data: Any) -> list[dict[str, Any]]:
    if hasattr(data, "to_dict"):
        try:
            records = data.to_dict(orient="records")
            if isinstance(records, list):
                return [
                    {"_record_type": "data", **record}
                    if isinstance(record, dict)
                    else {"_record_type": "data", "value": record}
                    for record in records
                ]
        except TypeError:
            pass
    if isinstance(data, list):
        return [
            {"_record_type": "data", **item}
            if isinstance(item, dict)
            else {"_record_type": "data", "value": item}
            for item in data
        ]
    if isinstance(data, dict):
        return [{"_record_type": "payload", "payload": data}]
    return [{"_record_type": "payload", "payload": data}]


def _make_run_id(
    request: DataPrepRequest,
    now_func: Callable[[], datetime] | None,
) -> str:
    now = now_func() if now_func is not None else datetime.now(UTC)
    stamp = _format_utc_ms(now).replace("-", "").replace(":", "").replace(".", "")
    stamp = stamp.replace("Z", "Z")
    payload = json.dumps(
        {
            "source": request.source,
            "interface": request.interface,
            "params": _canonicalize(request.params),
            "symbols": sorted(request.symbols),
            "date_range": _normalize_date_range(request.date_range),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    digest8 = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    return f"dataprep-{stamp}-{digest8}"


def _coerce_request(request: DataPrepRequest | dict[str, Any]) -> DataPrepRequest:
    if isinstance(request, DataPrepRequest):
        return request
    if not isinstance(request, dict):
        raise DataPrepConfigError("request 必须是 DataPrepRequest 或 dict")
    return DataPrepRequest(
        source=str(request["source"]),
        interface=str(request["interface"]),
        params=dict(request.get("params") or {}),
        symbols=list(request.get("symbols") or []),
        date_range=dict(request.get("date_range") or {}),
        batch_size=request.get("batch_size"),
        force_refresh=bool(request.get("force_refresh", False)),
    )


def _manifest_record(
    batch: BatchSpec,
    run_id: str,
    status: str,
    *,
    requested_at: str = "",
    request_started_at: str = "",
    request_finished_at: str = "",
    completed_at: str = "",
    attempts: int = 0,
    retry_events: list[dict[str, Any]] | None = None,
    raw_path: str = "",
    success_items: list[Any] | None = None,
    failed_items: list[Any] | None = None,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    date_start = batch.date_range.get("start", "")
    date_end = batch.date_range.get("end", "")
    symbol_range = list(batch.items) if batch.range_key.startswith("symbols-") else []
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "batch_id": batch.batch_id,
        "source": batch.source,
        "interface": batch.interface,
        "request_params": batch.request_params,
        "symbol_range": symbol_range,
        "date_range": batch.date_range,
        "requested_at": requested_at,
        "request_started_at": request_started_at or requested_at,
        "request_finished_at": request_finished_at,
        "completed_at": completed_at,
        "manifest_written_at": utc_now_ms(),
        "attempts": attempts,
        "retry_events": retry_events or [],
        "raw_path": raw_path,
        "standardized_output_path": None,
        "coverage_start": date_start,
        "coverage_end": date_end,
        "success_items": success_items or [],
        "failed_items": failed_items or [],
        "error_type": error_type,
        "error_message": error_message,
        "status": status,
    }


def _format_utc_ms(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


__all__ = (
    "BatchExecutionResult",
    "BatchSpec",
    "DataPrepConfig",
    "DataPrepConfigError",
    "DataPrepError",
    "DataPrepRequest",
    "DataPrepSourceRegistryError",
    "DataPrepRunSummary",
    "RawCacheWriteError",
    "ThrottleState",
    "compute_backoff_seconds",
    "filter_resumable_batches",
    "load_data_prep_config",
    "plan_batches",
    "run_batch_with_retry",
    "run_data_prep",
    "write_raw_cache",
)
