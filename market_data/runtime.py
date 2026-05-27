"""connector runtime：限速、重试、熔断、resume 与 manifest 写入。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping

from .connectors.protocol import (
    ConnectorError,
    ConnectorProtocol,
    ConnectorRequest,
    ConnectorResult,
)
from .contracts import SCHEMA_VERSION
from .contracts import (
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    INTERFACE_PRICES_ADJ_FACTOR,
    INTERFACE_PRICES_DAILY,
    INTERFACE_STOCK_BASIC_SNAPSHOT,
    INTERFACE_TRADE_CALENDAR_DAILY,
    SOURCE_TUSHARE,
)
from .lake_layout import LakeLayout
from .storage import (
    ManifestWriter,
    RawWriteResult,
    RawWriter,
    StorageWriteError,
    compute_idempotency_key,
    compute_params_hash,
    load_manifest_index,
    sanitize_params,
    verify_manifest_raw,
)

Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
Jitter = Callable[[], float]


@dataclass(frozen=True, slots=True)
class RuntimePolicy:
    max_retries: int = 2
    throttle_seconds: float = 0.0
    backoff_base_seconds: float = 0.0
    backoff_max_seconds: float = 60.0
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_skipped_status: str = "circuit_open"


@dataclass(frozen=True, slots=True)
class ResumePolicy:
    success: str = "skip"
    failed: str = "retry"
    partial_success: str = "retry"
    duplicate_manifest: str = "fail"


def resume_policy_to_dict(policy: ResumePolicy | None = None) -> dict[str, str]:
    policy = policy or ResumePolicy()
    return {
        "success": policy.success,
        "failed": policy.failed,
        "partial_success": policy.partial_success,
        "duplicate_manifest": policy.duplicate_manifest,
    }


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    run_id: str


CR014_P0_DATASETS: tuple[str, ...] = (
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_STOCK_BASIC,
)

CR014_P0_INTERFACE_BY_DATASET: dict[str, str] = {
    DATASET_PRICES: INTERFACE_PRICES_DAILY,
    DATASET_ADJ_FACTOR: INTERFACE_PRICES_ADJ_FACTOR,
    DATASET_HS300_INDEX: INTERFACE_HS300_INDEX_DAILY,
    DATASET_TRADE_CALENDAR: INTERFACE_TRADE_CALENDAR_DAILY,
    DATASET_INDEX_MEMBERS: INTERFACE_INDEX_MEMBERS_SNAPSHOT,
    DATASET_INDEX_WEIGHTS: INTERFACE_INDEX_WEIGHTS_SNAPSHOT,
    DATASET_STOCK_BASIC: INTERFACE_STOCK_BASIC_SNAPSHOT,
}

CR014_P0_DEFAULT_SOURCE_BY_DATASET: dict[str, str] = {
    dataset: SOURCE_TUSHARE for dataset in CR014_P0_DATASETS
}

AUTHORIZATION_REQUIRED = "authorization_required"
SOURCE_INTERFACE_UNRESOLVED = "source_interface_unresolved"
RUN_NOT_ALLOWED = "run_not_allowed"
DEV_GATE_UNSATISFIED = "dev_gate_unsatisfied"
LIFECYCLE_CONTRACT_REQUIRED = "lifecycle_contract_required"
UNSUPPORTED_P0_DATASET = "unsupported_p0_dataset"


def cr014_zero_permission_counters() -> dict[str, int]:
    """返回 CR014 BATCH-A 允许的零真实操作计数。"""

    counters = dict(CR014_FORBIDDEN_OPERATION_COUNTERS)
    counters.update(
        {
            "provider_fetches": 0,
            "lake_writes": 0,
            "credential_reads": 0,
            "raw_writes": 0,
            "manifest_writes": 0,
            "run_metadata_writes": 0,
            "current_pointer_changes": 0,
            "publish_count": 0,
            "duckdb_writes": 0,
            "legacy_data_reads": 0,
            "legacy_data_lists": 0,
            "legacy_data_copies": 0,
            "legacy_data_deletes": 0,
            "old_report_overwrites": 0,
            "connector_calls": 0,
        }
    )
    return counters


@dataclass(frozen=True, slots=True)
class PipelineError:
    code: str
    message: str
    unblock_conditions: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "unblock_conditions": list(self.unblock_conditions),
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class P0DatasetPlanRequest:
    datasets: tuple[str, ...] = CR014_P0_DATASETS
    start_date: str | None = None
    end_date: str | None = None
    as_of_trade_date: str | None = None
    coverage_denominator_ref: str | None = None
    batch_size: int = 1


@dataclass(frozen=True, slots=True)
class P0DatasetPlan:
    datasets: tuple[str, ...]
    as_of_trade_date: str
    coverage_denominator_ref: str
    batch_list: tuple[dict[str, Any], ...]
    permission_counters: dict[str, int]
    authorization_needed: bool = True
    status: str = "dry_run"
    errors: tuple[PipelineError, ...] = ()
    next_stage: str = "run"
    lifecycle_contract_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "datasets": list(self.datasets),
            "as_of_trade_date": self.as_of_trade_date,
            "coverage_denominator_ref": self.coverage_denominator_ref,
            "batch_list": [dict(item) for item in self.batch_list],
            "permission_counters": dict(self.permission_counters),
            "authorization_needed": self.authorization_needed,
            "next_stage": self.next_stage,
            "lifecycle_contract_required": self.lifecycle_contract_required,
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class DevGate:
    cp5_approved: bool = False
    lld_confirmed: bool = False
    dependencies_satisfied: bool = False
    file_conflict_free: bool = False

    @property
    def satisfied(self) -> bool:
        return (
            self.cp5_approved
            and self.lld_confirmed
            and self.dependencies_satisfied
            and self.file_conflict_free
        )

    def missing_conditions(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.cp5_approved:
            missing.append("cp5_approved")
        if not self.lld_confirmed:
            missing.append("lld_confirmed")
        if not self.dependencies_satisfied:
            missing.append("dependencies_satisfied")
        if not self.file_conflict_free:
            missing.append("file_conflict_free")
        return tuple(missing)


@dataclass(frozen=True, slots=True)
class RunAuthorization:
    authorization_id: str | None = None
    allowed_sources: tuple[str, ...] = ()
    allowed_interfaces: tuple[str, ...] = ()
    approved_by: str | None = None
    scope: dict[str, Any] = field(default_factory=dict)

    @property
    def is_user_authorized(self) -> bool:
        return bool(str(self.authorization_id or "").strip())


@dataclass(frozen=True, slots=True)
class RunGateResult:
    run_allowed: bool
    status: str
    permission_counters: dict[str, int]
    provider_fetches: int = 0
    lake_writes: int = 0
    credential_reads: int = 0
    connector_call_count: int = 0
    errors: tuple[PipelineError, ...] = ()
    next_stage: str = "normalize"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_allowed": self.run_allowed,
            "status": self.status,
            "permission_counters": dict(self.permission_counters),
            "provider_fetches": self.provider_fetches,
            "lake_writes": self.lake_writes,
            "credential_reads": self.credential_reads,
            "connector_call_count": self.connector_call_count,
            "next_stage": self.next_stage,
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class P0RunResult:
    status: str
    run_allowed: bool
    connector_call_count: int
    permission_counters: dict[str, int]
    batch_results: tuple[dict[str, Any], ...] = ()
    errors: tuple[PipelineError, ...] = ()
    next_stage: str = "normalize"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "run_allowed": self.run_allowed,
            "connector_call_count": self.connector_call_count,
            "permission_counters": dict(self.permission_counters),
            "batch_results": [dict(item) for item in self.batch_results],
            "next_stage": self.next_stage,
            "errors": [error.to_dict() for error in self.errors],
        }


def _pipeline_error(
    code: str,
    message: str,
    unblock_conditions: tuple[str, ...],
    **details: Any,
) -> PipelineError:
    return PipelineError(
        code=code,
        message=message,
        unblock_conditions=unblock_conditions,
        details={key: value for key, value in details.items() if value is not None},
    )


def _plan_value(
    request_value: str | None,
    lifecycle_contract: Mapping[str, Any],
    *keys: str,
) -> str:
    if request_value:
        return request_value
    for key in keys:
        value = lifecycle_contract.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def build_p0_plan(
    request: P0DatasetPlanRequest | Mapping[str, Any] | None = None,
    lifecycle_contract: Mapping[str, Any] | None = None,
    catalog_pointer: Mapping[str, Any] | None = None,
) -> P0DatasetPlan:
    """构建 P0 dataset dry-run plan；不抓 provider，不写 lake。"""

    if request is None:
        request = P0DatasetPlanRequest()
    elif isinstance(request, Mapping):
        request = P0DatasetPlanRequest(
            datasets=tuple(request.get("datasets") or CR014_P0_DATASETS),
            start_date=request.get("start_date"),
            end_date=request.get("end_date"),
            as_of_trade_date=request.get("as_of_trade_date"),
            coverage_denominator_ref=request.get("coverage_denominator_ref"),
            batch_size=int(request.get("batch_size") or 1),
        )

    lifecycle_payload = dict(lifecycle_contract or {})
    pointer_payload = dict(catalog_pointer or {})
    requested_datasets = tuple(request.datasets or CR014_P0_DATASETS)
    invalid_datasets = tuple(
        dataset for dataset in requested_datasets if dataset not in CR014_P0_DATASETS
    )
    valid_datasets = tuple(
        dataset for dataset in requested_datasets if dataset in CR014_P0_DATASETS
    )
    as_of_trade_date = _plan_value(
        request.as_of_trade_date,
        lifecycle_payload,
        "as_of_trade_date",
        "current_truth_as_of",
    )
    coverage_denominator_ref = _plan_value(
        request.coverage_denominator_ref,
        lifecycle_payload,
        "coverage_denominator_ref",
        "lifecycle_denominator_ref",
        "denominator_ref",
    )
    if not coverage_denominator_ref:
        pointer_ref = pointer_payload.get("coverage_denominator")
        if pointer_ref is not None:
            coverage_denominator_ref = f"catalog_pointer_denominator:{pointer_ref}"

    errors: list[PipelineError] = []
    if invalid_datasets:
        errors.append(
            _pipeline_error(
                UNSUPPORTED_P0_DATASET,
                "P0 plan 只接受 CR014 七类 dataset",
                ("remove_non_p0_dataset", "route_w3_or_other_dataset_to_separate_story"),
                datasets=list(invalid_datasets),
                allowed=list(CR014_P0_DATASETS),
            )
        )
    if not as_of_trade_date or not coverage_denominator_ref:
        errors.append(
            _pipeline_error(
                LIFECYCLE_CONTRACT_REQUIRED,
                "P0 plan 需要 S01 lifecycle denominator 与最近已闭市交易日合同",
                ("provide_s01_lifecycle_contract", "provide_current_truth_as_of"),
                as_of_trade_date_present=bool(as_of_trade_date),
                coverage_denominator_ref_present=bool(coverage_denominator_ref),
            )
        )

    batch_list: list[dict[str, Any]] = []
    for index, dataset in enumerate(valid_datasets, start=1):
        batch_list.append(
            {
                "dataset": dataset,
                "batch_id": f"p0-{index:02d}",
                "source": CR014_P0_DEFAULT_SOURCE_BY_DATASET[dataset],
                "interface": CR014_P0_INTERFACE_BY_DATASET[dataset],
                "start_date": request.start_date,
                "end_date": request.end_date,
                "dry_run": True,
                "authorization_required": True,
            }
        )

    return P0DatasetPlan(
        datasets=valid_datasets,
        as_of_trade_date=as_of_trade_date,
        coverage_denominator_ref=coverage_denominator_ref,
        batch_list=tuple(batch_list),
        permission_counters=cr014_zero_permission_counters(),
        authorization_needed=True,
        status="dry_run" if not errors else "blocked",
        errors=tuple(errors),
    )


def evaluate_run_gate(
    plan: P0DatasetPlan,
    authorization: RunAuthorization | None = None,
    dev_gate: DevGate | None = None,
) -> RunGateResult:
    """按 exact gate 判断 run 是否可进入真实执行；不调用 connector。"""

    authorization = authorization or RunAuthorization()
    dev_gate = dev_gate or DevGate()
    errors: list[PipelineError] = list(plan.errors)
    if not dev_gate.satisfied:
        errors.append(
            _pipeline_error(
                DEV_GATE_UNSATISFIED,
                "dev_gate 未满足，run 必须 fail-closed",
                (
                    "cp5_approved",
                    "lld_confirmed",
                    "dependencies_satisfied",
                    "file_conflict_free",
                ),
                missing=list(dev_gate.missing_conditions()),
            )
        )
    if not authorization.is_user_authorized:
        errors.append(
            _pipeline_error(
                AUTHORIZATION_REQUIRED,
                "真实 run 需要用户显式 authorization_id",
                ("provide_authorization_id", "record_user_run_scope"),
            )
        )

    required_sources = {
        str(batch["source"]) for batch in plan.batch_list if batch.get("source")
    }
    required_interfaces = {
        str(batch["interface"]) for batch in plan.batch_list if batch.get("interface")
    }
    allowed_sources = set(authorization.allowed_sources)
    allowed_interfaces = set(authorization.allowed_interfaces)
    missing_sources = sorted(required_sources - allowed_sources)
    missing_interfaces = sorted(required_interfaces - allowed_interfaces)
    if missing_sources or missing_interfaces:
        errors.append(
            _pipeline_error(
                SOURCE_INTERFACE_UNRESOLVED,
                "source/interface allowlist 未覆盖本次 P0 run",
                ("add_exact_source_allowlist", "add_exact_interface_allowlist"),
                missing_sources=missing_sources,
                missing_interfaces=missing_interfaces,
            )
        )

    if errors:
        if not any(error.code == RUN_NOT_ALLOWED for error in errors):
            errors.append(
                _pipeline_error(
                    RUN_NOT_ALLOWED,
                    "run gate fail-closed，connector 不会被调用",
                    ("clear_all_run_gate_errors",),
                )
            )
    run_allowed = not errors
    return RunGateResult(
        run_allowed=run_allowed,
        status="allowed" if run_allowed else "blocked",
        permission_counters=cr014_zero_permission_counters(),
        connector_call_count=0,
        errors=tuple(errors),
    )


def run_p0_batches(
    plan: P0DatasetPlan,
    connector: object | None = None,
    *,
    authorization: RunAuthorization | None = None,
    dev_gate: DevGate | None = None,
) -> P0RunResult:
    """S03 只落地 run 合同；本函数不执行 provider fetch 或 lake write。"""

    del connector
    gate = evaluate_run_gate(plan, authorization=authorization, dev_gate=dev_gate)
    if not gate.run_allowed:
        return P0RunResult(
            status="blocked",
            run_allowed=False,
            connector_call_count=0,
            permission_counters=gate.permission_counters,
            errors=gate.errors,
        )
    return P0RunResult(
        status="ready_for_authorized_runner",
        run_allowed=True,
        connector_call_count=0,
        permission_counters=gate.permission_counters,
        batch_results=tuple(
            {
                "dataset": batch["dataset"],
                "batch_id": batch["batch_id"],
                "status": "not_executed_by_s03_contract",
                "raw_writes": 0,
                "manifest_writes": 0,
                "run_metadata_writes": 0,
            }
            for batch in plan.batch_list
        ),
    )


def evaluate_s09_windowed_run_gate(
    *,
    authorization: object | None = None,
    dev_gate: DevGate | None = None,
    cp5_state: Mapping[str, Any] | None = None,
    execution_mode: str = "real",
    allow_fake_provider: bool = False,
):
    """S09 专用 gate facade；默认真实 run 在 real_run_authorized=false 时关闭。"""

    from .windowed_run import evaluate_s09_run_gate

    return evaluate_s09_run_gate(
        dev_gate=dev_gate,
        authorization=authorization,
        cp5_state=cp5_state,
        execution_mode=execution_mode,
        allow_fake_provider=allow_fake_provider,
    )


@dataclass(slots=True)
class CircuitBreakerState:
    status: str = "closed"
    failure_count: int = 0

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    def record_success(self) -> None:
        self.failure_count = 0
        self.status = "closed"

    def record_failure(self, threshold: int) -> None:
        self.failure_count += 1
        if self.failure_count >= threshold:
            self.status = "open"


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    batch_id: str
    idempotency_key: str
    status: str
    attempts: int
    raw_path: str | None = None
    error_type: str | None = None
    manifest_record: dict[str, Any] = field(default_factory=dict)


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _default_sleeper(seconds: float) -> None:
    if seconds > 0:
        import time

        time.sleep(seconds)


def _default_jitter() -> float:
    return 0.0


def _iso(clock: Clock) -> str:
    value = clock()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _prepare_request(
    batch: ConnectorRequest | Mapping[str, Any],
    context: RuntimeContext,
) -> tuple[ConnectorRequest, str]:
    if isinstance(batch, ConnectorRequest):
        request = batch
    else:
        request = ConnectorRequest(
            source=str(batch["source"]),
            interface=str(batch["interface"]),
            params=batch.get("params", {}),
            run_id=str(batch.get("run_id") or context.run_id),
            batch_id=str(batch["batch_id"]),
            params_hash=str(batch.get("params_hash") or ""),
        )
    params_hash = request.params_hash or compute_params_hash(request.params)
    if request.run_id != context.run_id or request.params_hash != params_hash:
        request = replace(request, run_id=context.run_id, params_hash=params_hash)
    idempotency_key = compute_idempotency_key(
        request.run_id,
        request.batch_id,
        request.source,
        request.interface,
        params_hash,
    )
    return request, idempotency_key


def _base_manifest_record(
    request: ConnectorRequest,
    idempotency_key: str,
    *,
    status: str,
    attempts: int,
    requested_at: str,
    started_at: str | None,
    finished_at: str,
    raw: RawWriteResult | None = None,
    error: ConnectorError | None = None,
    success_items: int = 0,
    failed_items: int = 0,
    backoff_seconds: list[float] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": request.run_id,
        "batch_id": request.batch_id,
        "idempotency_key": idempotency_key,
        "source": request.source,
        "interface": request.interface,
        "params": sanitize_params(request.params),
        "params_hash": request.params_hash,
        "requested_at": requested_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "attempts": attempts,
        "status": status,
        "raw_path": raw.relative_path if raw else None,
        "raw_checksum": raw.checksum if raw else None,
        "raw_row_count": raw.row_count if raw else None,
        "canonical_path": None,
        "error_type": error.error_type if error else None,
        "error_message": error.safe_message if error else None,
        "retryable": error.retryable if error else None,
        "success_items": success_items,
        "failed_items": failed_items,
        "backoff_seconds": backoff_seconds or [],
    }


def execute_batches(
    batches: Iterable[ConnectorRequest | Mapping[str, Any]],
    connector: ConnectorProtocol,
    layout: LakeLayout,
    policy: RuntimePolicy | None = None,
    *,
    resume_policy: ResumePolicy | None = None,
    context: RuntimeContext | None = None,
    clock: Clock | None = None,
    sleeper: Sleeper | None = None,
    jitter: Jitter | None = None,
    manifest_writer: ManifestWriter | None = None,
    raw_writer: RawWriter | None = None,
) -> list[BatchExecutionResult]:
    policy = policy or RuntimePolicy()
    resume_policy = resume_policy or ResumePolicy()
    context = context or RuntimeContext(run_id=f"run-{_iso(_default_clock)}")
    clock = clock or _default_clock
    sleeper = sleeper or _default_sleeper
    jitter = jitter or _default_jitter
    manifest_writer = manifest_writer or ManifestWriter()
    raw_writer = raw_writer or RawWriter()
    circuit = CircuitBreakerState()
    manifest_index = load_manifest_index(layout, verify_raw=False)
    results: list[BatchExecutionResult] = []

    for batch in batches:
        request, idempotency_key = _prepare_request(batch, context)
        requested_at = _iso(clock)
        existing = manifest_index.get(idempotency_key)
        if existing and existing.get("status") == "success" and resume_policy.success == "skip":
            verify_manifest_raw(existing, layout)
            results.append(
                BatchExecutionResult(
                    batch_id=request.batch_id,
                    idempotency_key=idempotency_key,
                    status="skipped",
                    attempts=0,
                    raw_path=existing.get("raw_path"),
                    manifest_record=dict(existing),
                )
            )
            continue

        if circuit.is_open:
            finished_at = _iso(clock)
            error = ConnectorError(
                "circuit_open",
                "circuit breaker is open",
                False,
                request.source,
                request.interface,
            )
            record = _base_manifest_record(
                request,
                idempotency_key,
                status=policy.circuit_breaker_skipped_status,
                attempts=0,
                requested_at=requested_at,
                started_at=None,
                finished_at=finished_at,
                error=error,
            )
            manifest_writer.append(record, layout)
            results.append(
                BatchExecutionResult(
                    batch_id=request.batch_id,
                    idempotency_key=idempotency_key,
                    status=policy.circuit_breaker_skipped_status,
                    attempts=0,
                    error_type=error.error_type,
                    manifest_record=record,
                )
            )
            continue

        if policy.throttle_seconds > 0:
            sleeper(policy.throttle_seconds)

        started_at = _iso(clock)
        attempts = 0
        backoffs: list[float] = []
        last_error: ConnectorError | None = None
        result: ConnectorResult | None = None
        for retry_index in range(policy.max_retries + 1):
            attempts += 1
            fetched = connector.fetch(request)
            if isinstance(fetched, ConnectorResult):
                result = fetched
                break
            last_error = fetched
            if not fetched.retryable or retry_index >= policy.max_retries:
                break
            backoff = min(
                policy.backoff_max_seconds,
                policy.backoff_base_seconds * (2**retry_index) + jitter(),
            )
            backoffs.append(backoff)
            if backoff > 0:
                sleeper(backoff)

        if result is None:
            finished_at = _iso(clock)
            assert last_error is not None
            circuit.record_failure(policy.circuit_breaker_failure_threshold)
            record = _base_manifest_record(
                request,
                idempotency_key,
                status="failed",
                attempts=attempts,
                requested_at=requested_at,
                started_at=started_at,
                finished_at=finished_at,
                error=last_error,
                backoff_seconds=backoffs,
            )
            manifest_writer.append(record, layout)
            results.append(
                BatchExecutionResult(
                    batch_id=request.batch_id,
                    idempotency_key=idempotency_key,
                    status="failed",
                    attempts=attempts,
                    error_type=last_error.error_type,
                    manifest_record=record,
                )
            )
            continue

        status = "partial_success" if result.partial_errors else "success"
        raw = raw_writer.write_atomic(result, request, layout)
        finished_at = _iso(clock)
        record = _base_manifest_record(
            request,
            idempotency_key,
            status=status,
            attempts=attempts,
            requested_at=requested_at,
            started_at=started_at,
            finished_at=finished_at,
            raw=raw,
            error=result.partial_errors[0] if result.partial_errors else None,
            success_items=len(result.rows),
            failed_items=len(result.partial_errors),
            backoff_seconds=backoffs,
        )
        try:
            manifest_writer.append(record, layout)
        except StorageWriteError:
            orphan_path = raw_writer.quarantine(raw.path, request, layout)
            orphan_record = {
                **record,
                "status": "orphan_raw",
                "raw_path": str(orphan_path.relative_to(layout.lake_root)),
                "error_type": "storage_error",
                "error_message": "manifest append failed after raw write",
                "retryable": False,
            }
            try:
                manifest_writer.append(orphan_record, layout)
            except StorageWriteError:
                pass
            raise
        circuit.record_success()
        results.append(
            BatchExecutionResult(
                batch_id=request.batch_id,
                idempotency_key=idempotency_key,
                status=status,
                attempts=attempts,
                raw_path=raw.relative_path,
                error_type=result.partial_errors[0].error_type
                if result.partial_errors
                else None,
                manifest_record=record,
            )
        )

    return results


__all__ = [
    "BatchExecutionResult",
    "AUTHORIZATION_REQUIRED",
    "CR014_P0_DATASETS",
    "CR014_P0_DEFAULT_SOURCE_BY_DATASET",
    "CR014_P0_INTERFACE_BY_DATASET",
    "CircuitBreakerState",
    "DEV_GATE_UNSATISFIED",
    "DevGate",
    "LIFECYCLE_CONTRACT_REQUIRED",
    "P0DatasetPlan",
    "P0DatasetPlanRequest",
    "P0RunResult",
    "PipelineError",
    "ResumePolicy",
    "RUN_NOT_ALLOWED",
    "RunAuthorization",
    "RunGateResult",
    "RuntimeContext",
    "RuntimePolicy",
    "SOURCE_INTERFACE_UNRESOLVED",
    "UNSUPPORTED_P0_DATASET",
    "build_p0_plan",
    "cr014_zero_permission_counters",
    "evaluate_run_gate",
    "evaluate_s09_windowed_run_gate",
    "execute_batches",
    "resume_policy_to_dict",
    "run_p0_batches",
]
