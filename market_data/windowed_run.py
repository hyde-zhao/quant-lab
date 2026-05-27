"""CR014-S09 windowed run 合同层。

本模块只提供授权、窗口计划、fake provider 测试执行、failure/resume/rollback
metadata 与 summary 合同。真实 provider fetch、真实 lake 写入、publish、
retention execute 和 DuckDB 均不在默认路径执行。
"""

from __future__ import annotations

import hashlib
import json
import re
from calendar import monthrange
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

from .contracts import SCHEMA_VERSION
from .lake_layout import (
    LakeLayout,
    ensure_parent_dirs_for_write,
    ensure_s09_lake_root_allowed,
)
from .manifest import build_s09_window_manifest_record

S09_DEFAULT_PILOT_START = "2026-01-01"
S09_DEFAULT_PILOT_END = "2026-05-26"

S09_CP5_NOT_APPROVED = "s09_cp5_not_approved"
S09_LLD_NOT_CONFIRMED = "s09_lld_not_confirmed"
S09_DEPENDENCIES_NOT_VERIFIED = "s09_dependencies_not_verified"
S09_FILE_CONFLICT = "s09_file_conflict"
S09_IMPLEMENTATION_NOT_ALLOWED = "implementation_not_allowed"
S09_REAL_RUN_NOT_AUTHORIZED = "real_run_not_authorized"
S09_AUTHORIZATION_REQUIRED = "authorization_required"
S09_RESUME_CONFLICT = "resume_conflict"
S09_ROLLBACK_REQUIRES_AUTHORIZATION = "rollback_requires_authorization"
S09_PROVIDER_ERROR = "provider_error"
S09_RAW_WRITE_FAILED = "raw_write_failed"
S09_MANIFEST_WRITE_FAILED = "manifest_write_failed"

S09_REQUIRED_AUTH_FIELDS: tuple[str, ...] = (
    "authorization_id",
    "datasets",
    "date_range",
    "source_interface_allowlist",
    "lake_root",
    "window_policy",
    "resume_policy",
    "rollback_policy",
    "credential_source_policy",
)

S09_FORBIDDEN_COUNTER_KEYS: tuple[str, ...] = (
    "provider_fetch",
    "provider_fetches",
    "lake_write",
    "lake_writes",
    "credential_read",
    "credential_reads",
    "current_pointer_changes",
    "publish_count",
    "catalog_current_pointer_publish",
    "retention_execute",
    "retention_execute_count",
    "duckdb_open",
    "duckdb_opens",
    "duckdb_write",
    "duckdb_writes",
    "duckdb_dependency_change",
    "duckdb_files_created",
    "old_data_read",
    "old_data_reads",
    "old_report_overwrite",
    "old_report_overwrites",
)


def s09_zero_forbidden_counters() -> dict[str, int]:
    """返回 S09 实现阶段必须保持为 0 的真实副作用计数。"""

    return {key: 0 for key in S09_FORBIDDEN_COUNTER_KEYS}


def _to_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").date()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return date.fromisoformat(text[:10])
    raise ValueError(f"日期格式不合法: {text}")


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _clean_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip())
    return token.strip("-") or "unknown"


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"不支持的对象类型: {type(value)!r}")


def _split_text_items(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, Iterable):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),) if str(value).strip() else ()


@dataclass(frozen=True, slots=True)
class S09Error:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class DateRange:
    start_date: str
    end_date: str

    def __post_init__(self) -> None:
        start = _to_date(self.start_date)
        end = _to_date(self.end_date)
        if start > end:
            raise ValueError("start_date 不能晚于 end_date")
        object.__setattr__(self, "start_date", start.isoformat())
        object.__setattr__(self, "end_date", end.isoformat())

    @property
    def start(self) -> date:
        return _to_date(self.start_date)

    @property
    def end(self) -> date:
        return _to_date(self.end_date)

    def to_dict(self) -> dict[str, str]:
        return {"start_date": self.start_date, "end_date": self.end_date}


@dataclass(frozen=True, slots=True)
class SourceInterface:
    source: str
    interface: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", str(self.source).strip())
        object.__setattr__(self, "interface", str(self.interface).strip())
        if not self.source or not self.interface:
            raise ValueError("source/interface 不能为空")

    def to_dict(self) -> dict[str, str]:
        return {"source": self.source, "interface": self.interface}


@dataclass(frozen=True, slots=True)
class WindowPolicy:
    policy_type: str = "month"
    trading_day_chunk_size: int = 20
    calendar_chunk_days: int | None = None
    rate_limit_per_minute: int | None = None
    max_retries: int = 0
    stop_on_error: bool = False

    def __post_init__(self) -> None:
        normalized = str(self.policy_type).strip().lower().replace("_", "-")
        aliases = {
            "monthly": "month",
            "quarterly": "quarter",
            "yearly": "year",
            "trading-day": "trading-day-chunk",
            "trading_days": "trading-day-chunk",
            "trading-day-chunk": "trading-day-chunk",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"year", "quarter", "month", "trading-day-chunk"}:
            raise ValueError(f"不支持的 window policy: {self.policy_type}")
        object.__setattr__(self, "policy_type", normalized)
        if self.trading_day_chunk_size <= 0:
            raise ValueError("trading_day_chunk_size 必须大于 0")
        if self.calendar_chunk_days is not None and self.calendar_chunk_days <= 0:
            raise ValueError("calendar_chunk_days 必须大于 0")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class S09ResumePolicy:
    skip_success: bool = True
    retry_failed: bool = True
    conflict_strategy: str = "fail_closed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RollbackPolicy:
    mode: str = "preview_only"
    execute_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CredentialSourcePolicy:
    policy_type: str = "env"
    env_var_names: tuple[str, ...] = ()
    redact_values: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "env_var_names", tuple(self.env_var_names))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunAuthorization:
    authorization_id: str
    datasets: tuple[str, ...]
    date_range: DateRange
    source_interface_allowlist: tuple[SourceInterface, ...]
    lake_root: Path
    window_policy: WindowPolicy
    resume_policy: S09ResumePolicy
    rollback_policy: RollbackPolicy
    credential_source_policy: CredentialSourcePolicy
    approved_by: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "authorization_id", str(self.authorization_id).strip())
        object.__setattr__(self, "datasets", tuple(_split_text_items(self.datasets)))
        object.__setattr__(self, "lake_root", Path(self.lake_root))
        object.__setattr__(
            self,
            "source_interface_allowlist",
            tuple(self.source_interface_allowlist),
        )

    @property
    def lake_root_label(self) -> str:
        return "<configured-lake-root>"

    @property
    def lake_root_fingerprint(self) -> str:
        return hashlib.sha256(str(self.lake_root).encode("utf-8")).hexdigest()[:16]

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "datasets": list(self.datasets),
            "date_range": self.date_range.to_dict(),
            "source_interface_allowlist": [
                item.to_dict() for item in self.source_interface_allowlist
            ],
            "lake_root_label": self.lake_root_label,
            "lake_root_fingerprint": self.lake_root_fingerprint,
            "window_policy": self.window_policy.to_dict(),
            "resume_policy": self.resume_policy.to_dict(),
            "rollback_policy": self.rollback_policy.to_dict(),
            "credential_source_policy": self.credential_source_policy.to_dict(),
            "approved_by": self.approved_by,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationBuildResult:
    authorization: RunAuthorization | None
    missing_fields: tuple[str, ...]
    errors: tuple[S09Error, ...]
    permission_counters: dict[str, int] = field(default_factory=s09_zero_forbidden_counters)

    @property
    def ok(self) -> bool:
        return self.authorization is not None and not self.missing_fields and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "authorization": self.authorization.to_safe_dict()
            if self.authorization is not None
            else None,
            "missing_fields": list(self.missing_fields),
            "errors": [error.to_dict() for error in self.errors],
            "permission_counters": dict(self.permission_counters),
        }


@dataclass(frozen=True, slots=True)
class S09GateContext:
    cp5_approved: bool = False
    lld_confirmed: bool = False
    dependencies_satisfied: bool = False
    file_conflict_free: bool = False
    implementation_allowed: bool = False
    real_run_authorized: bool = False
    execution_mode: str = "real"
    allow_fake_provider: bool = False


@dataclass(frozen=True, slots=True)
class S09RunGateResult:
    run_allowed: bool
    status: str
    execution_mode: str
    real_run_authorized: bool
    permission_counters: dict[str, int]
    errors: tuple[S09Error, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_allowed": self.run_allowed,
            "status": self.status,
            "execution_mode": self.execution_mode,
            "real_run_authorized": self.real_run_authorized,
            "permission_counters": dict(self.permission_counters),
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class WindowPlan:
    dataset: str
    source: str
    source_interface: str
    window_id: str
    run_id: str
    start_date: str
    end_date: str
    request_fingerprint: str
    resume_token: str
    status: str = "planned"
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class WindowedRunPlan:
    authorization_id: str | None
    windows: tuple[WindowPlan, ...]
    status: str
    permission_counters: dict[str, int]
    authorization_needed: bool = False
    errors: tuple[S09Error, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "status": self.status,
            "authorization_needed": self.authorization_needed,
            "windows": [window.to_dict() for window in self.windows],
            "permission_counters": dict(self.permission_counters),
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class WindowRunRecord:
    window_id: str
    run_id: str
    dataset: str
    source: str
    source_interface: str
    start_date: str
    end_date: str
    status: str
    attempt: int
    request_fingerprint: str
    resume_token: str
    raw_refs: tuple[str, ...] = ()
    manifest_ref: str | None = None
    run_metadata_ref: str | None = None
    raw_checksum: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retryable: bool = False
    permission_counters: dict[str, int] = field(default_factory=s09_zero_forbidden_counters)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["raw_refs"] = list(self.raw_refs)
        return payload


@dataclass(frozen=True, slots=True)
class WindowedRunSummary:
    status: str
    authorization_id: str | None
    windows_total: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    conflict_count: int
    records: tuple[WindowRunRecord, ...]
    permission_counters: dict[str, int]
    errors: tuple[S09Error, ...] = ()
    fake_provider_calls: int = 0
    tmp_path_write_count: int = 0
    raw_write_count: int = 0
    manifest_write_count: int = 0
    run_metadata_write_count: int = 0
    current_pointer_changes: int = 0
    publish_count: int = 0
    retention_execute_count: int = 0
    duckdb_open_count: int = 0
    duckdb_write_count: int = 0
    duckdb_dependency_change: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "authorization_id": self.authorization_id,
            "windows_total": self.windows_total,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "conflict_count": self.conflict_count,
            "records": [record.to_dict() for record in self.records],
            "permission_counters": dict(self.permission_counters),
            "errors": [error.to_dict() for error in self.errors],
            "fake_provider_calls": self.fake_provider_calls,
            "tmp_path_write_count": self.tmp_path_write_count,
            "raw_write_count": self.raw_write_count,
            "manifest_write_count": self.manifest_write_count,
            "run_metadata_write_count": self.run_metadata_write_count,
            "current_pointer_changes": self.current_pointer_changes,
            "publish_count": self.publish_count,
            "retention_execute_count": self.retention_execute_count,
            "duckdb_open_count": self.duckdb_open_count,
            "duckdb_write_count": self.duckdb_write_count,
            "duckdb_dependency_change": self.duckdb_dependency_change,
        }


@dataclass(frozen=True, slots=True)
class ResumePlanResult:
    status: str
    run_allowed: bool
    windows_to_run: tuple[WindowPlan, ...]
    skipped_windows: tuple[str, ...]
    conflicts: tuple[dict[str, Any], ...]
    permission_counters: dict[str, int] = field(default_factory=s09_zero_forbidden_counters)
    errors: tuple[S09Error, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "run_allowed": self.run_allowed,
            "windows_to_run": [window.to_dict() for window in self.windows_to_run],
            "skipped_windows": list(self.skipped_windows),
            "conflicts": [dict(item) for item in self.conflicts],
            "permission_counters": dict(self.permission_counters),
            "errors": [error.to_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class RollbackPreview:
    status: str
    execute_authorized: bool
    actions: tuple[dict[str, Any], ...]
    permission_counters: dict[str, int] = field(default_factory=s09_zero_forbidden_counters)
    errors: tuple[S09Error, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "execute_authorized": self.execute_authorized,
            "actions": [dict(action) for action in self.actions],
            "permission_counters": dict(self.permission_counters),
            "errors": [error.to_dict() for error in self.errors],
        }


class WindowProvider(Protocol):
    def fetch(self, window: WindowPlan) -> Mapping[str, Any]:
        """返回单个 window 的 provider payload。"""


class WindowWriter(Protocol):
    raw_write_count: int
    manifest_write_count: int
    run_metadata_write_count: int
    tmp_path_write_count: int

    def write_success(
        self,
        window: WindowPlan,
        authorization: RunAuthorization,
        payload: Mapping[str, Any],
        checksum: str,
    ) -> tuple[str, str, str]:
        """写成功 window 的 raw / manifest / metadata 测试产物。"""

    def write_failure(
        self,
        window: WindowPlan,
        authorization: RunAuthorization,
        error: S09Error,
    ) -> tuple[str, str]:
        """写失败 window 的 manifest / metadata 测试产物。"""


class WindowProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class FakeWindowProvider:
    """仅供测试使用的 provider，不读取凭据、不联网。"""

    def __init__(
        self,
        payload_by_window: Mapping[str, Mapping[str, Any]] | None = None,
        failures: Mapping[str, str | WindowProviderError] | None = None,
    ) -> None:
        self.payload_by_window = dict(payload_by_window or {})
        self.failures = dict(failures or {})
        self.call_count = 0

    def fetch(self, window: WindowPlan) -> Mapping[str, Any]:
        self.call_count += 1
        failure = self.failures.get(window.window_id)
        if failure is not None:
            if isinstance(failure, WindowProviderError):
                raise failure
            raise WindowProviderError(S09_PROVIDER_ERROR, str(failure), retryable=True)
        return self.payload_by_window.get(
            window.window_id,
            {
                "dataset": window.dataset,
                "window_id": window.window_id,
                "start_date": window.start_date,
                "end_date": window.end_date,
                "rows": [],
            },
        )


class TmpPathWindowWriter:
    """写入显式 lake_root 的 fake-run writer；测试中应传入 tmp_path。"""

    def __init__(self, lake_root: str | Path) -> None:
        self.lake_root = ensure_s09_lake_root_allowed(lake_root)
        self.layout = LakeLayout(self.lake_root)
        self.raw_write_count = 0
        self.manifest_write_count = 0
        self.run_metadata_write_count = 0
        self.tmp_path_write_count = 0

    def _write_json(self, path: Path, payload: Mapping[str, Any]) -> str:
        ensure_parent_dirs_for_write(path)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
            encoding="utf-8",
        )
        self.tmp_path_write_count += 1
        return str(path)

    def write_success(
        self,
        window: WindowPlan,
        authorization: RunAuthorization,
        payload: Mapping[str, Any],
        checksum: str,
    ) -> tuple[str, str, str]:
        raw_path = self.layout.s09_window_raw_path(
            dataset=window.dataset,
            source=window.source,
            interface=window.source_interface,
            run_id=window.run_id,
            window_id=window.window_id,
        )
        manifest_path = self.layout.s09_window_manifest_path(
            dataset=window.dataset,
            run_id=window.run_id,
            window_id=window.window_id,
        )
        metadata_path = self.layout.s09_window_metadata_path(
            dataset=window.dataset,
            run_id=window.run_id,
            window_id=window.window_id,
        )
        raw_ref = self._write_json(
            raw_path,
            {
                "schema_version": SCHEMA_VERSION,
                "authorization_id": authorization.authorization_id,
                "window": window.to_dict(),
                "payload": dict(payload),
            },
        )
        self.raw_write_count += 1
        manifest_payload = build_s09_window_manifest_record(
            window=window.to_dict(),
            authorization=authorization.to_safe_dict(),
            status="succeeded",
            raw_checksum=checksum,
            raw_refs=(raw_ref,),
            failure=None,
        )
        manifest_ref = self._write_json(manifest_path, manifest_payload)
        self.manifest_write_count += 1
        metadata_ref = self._write_json(
            metadata_path,
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "s09_window_run_metadata",
                "status": "succeeded",
                "window": window.to_dict(),
                "authorization": authorization.to_safe_dict(),
                "raw_checksum": checksum,
                "permission_counters": s09_zero_forbidden_counters(),
            },
        )
        self.run_metadata_write_count += 1
        return raw_ref, manifest_ref, metadata_ref

    def write_failure(
        self,
        window: WindowPlan,
        authorization: RunAuthorization,
        error: S09Error,
    ) -> tuple[str, str]:
        manifest_path = self.layout.s09_window_manifest_path(
            dataset=window.dataset,
            run_id=window.run_id,
            window_id=window.window_id,
        )
        metadata_path = self.layout.s09_window_metadata_path(
            dataset=window.dataset,
            run_id=window.run_id,
            window_id=window.window_id,
        )
        failure = error.to_dict()
        manifest_payload = build_s09_window_manifest_record(
            window=window.to_dict(),
            authorization=authorization.to_safe_dict(),
            status="failed",
            raw_checksum=None,
            raw_refs=(),
            failure=failure,
        )
        manifest_ref = self._write_json(manifest_path, manifest_payload)
        self.manifest_write_count += 1
        metadata_ref = self._write_json(
            metadata_path,
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "s09_window_run_metadata",
                "status": "failed",
                "window": window.to_dict(),
                "authorization": authorization.to_safe_dict(),
                "failure": failure,
                "permission_counters": s09_zero_forbidden_counters(),
            },
        )
        self.run_metadata_write_count += 1
        return manifest_ref, metadata_ref


def default_s09_pilot_date_range() -> DateRange:
    return DateRange(S09_DEFAULT_PILOT_START, S09_DEFAULT_PILOT_END)


def _coerce_date_range(value: Any, raw: Mapping[str, Any]) -> DateRange | None:
    if isinstance(value, DateRange):
        return value
    if isinstance(value, Mapping):
        start = value.get("start_date") or value.get("start")
        end = value.get("end_date") or value.get("end")
    elif isinstance(value, Sequence) and not isinstance(value, str) and len(value) >= 2:
        start, end = value[0], value[1]
    else:
        start = raw.get("start_date")
        end = raw.get("end_date")
    if not start or not end:
        return None
    return DateRange(str(start), str(end))


def _coerce_source_interfaces(value: Any, raw: Mapping[str, Any]) -> tuple[SourceInterface, ...]:
    if value is None:
        source = raw.get("source")
        interface = raw.get("interface") or raw.get("source_interface")
        if source and interface:
            return (SourceInterface(str(source), str(interface)),)
        return ()
    items: list[SourceInterface] = []
    raw_items = value if isinstance(value, Iterable) and not isinstance(value, str) else [value]
    for item in raw_items:
        if isinstance(item, SourceInterface):
            items.append(item)
        elif isinstance(item, Mapping):
            items.append(
                SourceInterface(
                    str(item.get("source") or ""),
                    str(item.get("interface") or item.get("source_interface") or ""),
                )
            )
        else:
            text = str(item)
            if ":" in text:
                source, interface = text.split(":", 1)
            elif "/" in text:
                source, interface = text.split("/", 1)
            else:
                source = str(raw.get("source") or "")
                interface = text
            items.append(SourceInterface(source, interface))
    return tuple(items)


def _coerce_window_policy(value: Any) -> WindowPolicy | None:
    if isinstance(value, WindowPolicy):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return WindowPolicy(policy_type=value)
    payload = _as_dict(value)
    return WindowPolicy(
        policy_type=str(payload.get("policy_type") or payload.get("type") or "month"),
        trading_day_chunk_size=int(payload.get("trading_day_chunk_size") or payload.get("chunk_size") or 20),
        calendar_chunk_days=payload.get("calendar_chunk_days"),
        rate_limit_per_minute=payload.get("rate_limit_per_minute"),
        max_retries=int(payload.get("max_retries") or 0),
        stop_on_error=bool(payload.get("stop_on_error", False)),
    )


def _coerce_resume_policy(value: Any) -> S09ResumePolicy | None:
    if isinstance(value, S09ResumePolicy):
        return value
    if value is None:
        return None
    payload = _as_dict(value)
    return S09ResumePolicy(
        skip_success=bool(payload.get("skip_success", True)),
        retry_failed=bool(payload.get("retry_failed", True)),
        conflict_strategy=str(payload.get("conflict_strategy") or "fail_closed"),
    )


def _coerce_rollback_policy(value: Any) -> RollbackPolicy | None:
    if isinstance(value, RollbackPolicy):
        return value
    if value is None:
        return None
    payload = _as_dict(value)
    return RollbackPolicy(
        mode=str(payload.get("mode") or "preview_only"),
        execute_authorized=bool(payload.get("execute_authorized", False)),
    )


def _coerce_credential_policy(value: Any) -> CredentialSourcePolicy | None:
    if isinstance(value, CredentialSourcePolicy):
        return value
    if value is None:
        return None
    payload = _as_dict(value)
    env_vars = payload.get("env_var_names") or payload.get("env_vars") or payload.get("env_var")
    return CredentialSourcePolicy(
        policy_type=str(payload.get("policy_type") or payload.get("type") or "env"),
        env_var_names=_split_text_items(env_vars),
        redact_values=bool(payload.get("redact_values", True)),
    )


def build_s09_authorization(raw_input: Mapping[str, Any] | RunAuthorization | None) -> AuthorizationBuildResult:
    """构建 S09 per-run 授权；只诊断字段，不读取凭据、不执行副作用。"""

    if isinstance(raw_input, RunAuthorization):
        missing = []
        if not raw_input.authorization_id:
            missing.append("authorization_id")
        if not raw_input.datasets:
            missing.append("datasets")
        if not raw_input.source_interface_allowlist:
            missing.append("source_interface_allowlist")
        if not str(raw_input.lake_root):
            missing.append("lake_root")
        return AuthorizationBuildResult(
            authorization=raw_input if not missing else None,
            missing_fields=tuple(missing),
            errors=(
                (
                    S09Error(
                        S09_AUTHORIZATION_REQUIRED,
                        "S09 per-run 授权字段不完整，真实执行 fail-closed",
                        {"missing_fields": list(missing)},
                    ),
                )
                if missing
                else ()
            ),
        )

    raw = dict(raw_input or {})
    authorization = None

    missing: list[str] = []
    errors: list[S09Error] = []

    try:
        authorization_id = str(raw.get("authorization_id") or "").strip()
        if not authorization_id:
            missing.append("authorization_id")

        datasets = _split_text_items(raw.get("datasets") or raw.get("dataset"))
        if not datasets:
            missing.append("datasets")

        date_range = _coerce_date_range(raw.get("date_range"), raw)
        if date_range is None:
            missing.append("date_range")

        allowlist = _coerce_source_interfaces(
            raw.get("source_interface_allowlist")
            or raw.get("allowed_source_interfaces")
            or raw.get("allowlist"),
            raw,
        )
        if not allowlist:
            missing.append("source_interface_allowlist")

        lake_root_value = raw.get("lake_root")
        if not lake_root_value:
            missing.append("lake_root")
            lake_root = None
        else:
            lake_root = ensure_s09_lake_root_allowed(lake_root_value)

        window_policy = _coerce_window_policy(raw.get("window_policy"))
        if window_policy is None:
            missing.append("window_policy")

        resume_policy = _coerce_resume_policy(raw.get("resume_policy"))
        if resume_policy is None:
            missing.append("resume_policy")

        rollback_policy = _coerce_rollback_policy(raw.get("rollback_policy"))
        if rollback_policy is None:
            missing.append("rollback_policy")

        credential_policy = _coerce_credential_policy(raw.get("credential_source_policy"))
        if credential_policy is None:
            missing.append("credential_source_policy")

        if not missing and not errors and authorization is None:
            authorization = RunAuthorization(
                authorization_id=authorization_id,
                datasets=datasets,
                date_range=date_range,  # type: ignore[arg-type]
                source_interface_allowlist=allowlist,
                lake_root=lake_root,  # type: ignore[arg-type]
                window_policy=window_policy,  # type: ignore[arg-type]
                resume_policy=resume_policy,  # type: ignore[arg-type]
                rollback_policy=rollback_policy,  # type: ignore[arg-type]
                credential_source_policy=credential_policy,  # type: ignore[arg-type]
                approved_by=raw.get("approved_by"),
            )
    except Exception as exc:  # noqa: BLE001 - 合同层需要把解析异常结构化暴露
        errors.append(S09Error(S09_AUTHORIZATION_REQUIRED, str(exc)))
        authorization = None

    if missing:
        errors.append(
            S09Error(
                S09_AUTHORIZATION_REQUIRED,
                "S09 per-run 授权字段不完整，真实执行 fail-closed",
                {"missing_fields": list(dict.fromkeys(missing))},
            )
        )
        authorization = None

    return AuthorizationBuildResult(
        authorization=authorization,
        missing_fields=tuple(dict.fromkeys(missing)),
        errors=tuple(errors),
    )


def _context_bool(source: Any, name: str, default: bool = False) -> bool:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return bool(source.get(name, default))
    return bool(getattr(source, name, default))


def evaluate_s09_run_gate(
    dev_gate: Any | None = None,
    authorization: RunAuthorization | AuthorizationBuildResult | Mapping[str, Any] | None = None,
    cp5_state: Mapping[str, Any] | None = None,
    *,
    execution_mode: str = "real",
    allow_fake_provider: bool = False,
) -> S09RunGateResult:
    """S09 run gate；缺任一门控或真实授权时 fail-closed。"""

    state = dict(cp5_state or {})
    context = S09GateContext(
        cp5_approved=_context_bool(dev_gate, "cp5_approved", state.get("cp5_approved", False)),
        lld_confirmed=_context_bool(dev_gate, "lld_confirmed", state.get("lld_confirmed", False)),
        dependencies_satisfied=_context_bool(
            dev_gate,
            "dependencies_satisfied",
            state.get("dependencies_satisfied", False),
        ),
        file_conflict_free=_context_bool(
            dev_gate,
            "file_conflict_free",
            state.get("file_conflict_free", False),
        ),
        implementation_allowed=bool(state.get("implementation_allowed", False)),
        real_run_authorized=bool(state.get("real_run_authorized", False)),
        execution_mode=execution_mode,
        allow_fake_provider=allow_fake_provider,
    )
    if hasattr(dev_gate, "satisfied") and bool(getattr(dev_gate, "satisfied")):
        context = S09GateContext(
            cp5_approved=True,
            lld_confirmed=True,
            dependencies_satisfied=True,
            file_conflict_free=True,
            implementation_allowed=context.implementation_allowed,
            real_run_authorized=context.real_run_authorized,
            execution_mode=context.execution_mode,
            allow_fake_provider=context.allow_fake_provider,
        )

    errors: list[S09Error] = []
    if not context.cp5_approved:
        errors.append(S09Error(S09_CP5_NOT_APPROVED, "S09 CP5 未 approved"))
    if not context.lld_confirmed:
        errors.append(S09Error(S09_LLD_NOT_CONFIRMED, "S09 LLD 未 confirmed"))
    if not context.dependencies_satisfied:
        errors.append(S09Error(S09_DEPENDENCIES_NOT_VERIFIED, "S01..S08 依赖未全部 verified"))
    if not context.file_conflict_free:
        errors.append(S09Error(S09_FILE_CONFLICT, "S09 文件所有权存在冲突"))
    if not context.implementation_allowed:
        errors.append(S09Error(S09_IMPLEMENTATION_NOT_ALLOWED, "S09 implementation_allowed=false"))

    if isinstance(authorization, AuthorizationBuildResult):
        auth_result = authorization
    else:
        auth_result = build_s09_authorization(authorization)
    errors.extend(auth_result.errors)

    mode = execution_mode.strip().lower()
    fake_allowed = mode == "fake" and allow_fake_provider
    if mode == "real" and not context.real_run_authorized:
        errors.append(
            S09Error(
                S09_REAL_RUN_NOT_AUTHORIZED,
                "real_run_authorized=false，真实 provider/lake/credential 路径关闭",
            )
        )
    elif mode != "real" and not fake_allowed:
        errors.append(
            S09Error(
                S09_REAL_RUN_NOT_AUTHORIZED,
                "只有显式 allow_fake_provider 的 fake 模式允许测试执行",
            )
        )

    run_allowed = not errors
    return S09RunGateResult(
        run_allowed=run_allowed,
        status="allowed" if run_allowed else "blocked",
        execution_mode=mode,
        real_run_authorized=context.real_run_authorized,
        permission_counters=s09_zero_forbidden_counters(),
        errors=tuple(errors),
    )


def _month_end(value: date) -> date:
    return value.replace(day=monthrange(value.year, value.month)[1])


def _quarter_end(value: date) -> date:
    end_month = ((value.month - 1) // 3 + 1) * 3
    return date(value.year, end_month, monthrange(value.year, end_month)[1])


def _calendar_windows(date_range: DateRange, policy: WindowPolicy) -> list[tuple[date, date]]:
    cursor = date_range.start
    end = date_range.end
    windows: list[tuple[date, date]] = []
    while cursor <= end:
        if policy.policy_type == "month":
            window_end = min(_month_end(cursor), end)
        elif policy.policy_type == "quarter":
            window_end = min(_quarter_end(cursor), end)
        elif policy.policy_type == "year":
            window_end = min(date(cursor.year, 12, 31), end)
        elif policy.calendar_chunk_days:
            window_end = min(cursor + timedelta(days=policy.calendar_chunk_days - 1), end)
        else:
            window_end = min(cursor + timedelta(days=policy.trading_day_chunk_size - 1), end)
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def _trading_day_windows(
    date_range: DateRange,
    policy: WindowPolicy,
    trading_days: Sequence[str | date],
) -> list[tuple[date, date]]:
    days = [
        _to_date(item)
        for item in trading_days
        if date_range.start <= _to_date(item) <= date_range.end
    ]
    if not days:
        return _calendar_windows(date_range, policy)
    windows: list[tuple[date, date]] = []
    size = policy.trading_day_chunk_size
    for index in range(0, len(days), size):
        chunk = days[index : index + size]
        windows.append((chunk[0], chunk[-1]))
    return windows


def _request_fingerprint(
    authorization: RunAuthorization,
    *,
    dataset: str,
    source_interface: SourceInterface,
    start_date: str,
    end_date: str,
) -> str:
    return _hash_payload(
        {
            "schema_version": SCHEMA_VERSION,
            "authorization_id": authorization.authorization_id,
            "dataset": dataset,
            "source": source_interface.source,
            "source_interface": source_interface.interface,
            "start_date": start_date,
            "end_date": end_date,
            "lake_root_fingerprint": authorization.lake_root_fingerprint,
            "window_policy": authorization.window_policy.to_dict(),
            "credential_source_policy": authorization.credential_source_policy.to_dict(),
        }
    )


def _resume_token(fingerprint: str, attempt: int) -> str:
    return hashlib.sha256(f"{fingerprint}:{attempt}".encode("utf-8")).hexdigest()


def plan_windowed_run(
    authorization: RunAuthorization | AuthorizationBuildResult | Mapping[str, Any] | None,
    *,
    trading_days: Sequence[str | date] = (),
    existing_manifest_index: Mapping[str, Any] | None = None,
) -> WindowedRunPlan:
    """按授权窗口生成 S09 plan；不抓 provider、不写 lake。"""

    del existing_manifest_index
    auth_result = (
        authorization
        if isinstance(authorization, AuthorizationBuildResult)
        else build_s09_authorization(authorization)
    )
    if not auth_result.ok or auth_result.authorization is None:
        return WindowedRunPlan(
            authorization_id=None,
            windows=(),
            status="blocked",
            permission_counters=s09_zero_forbidden_counters(),
            authorization_needed=True,
            errors=auth_result.errors,
        )

    auth = auth_result.authorization
    if auth.window_policy.policy_type == "trading-day-chunk":
        date_windows = _trading_day_windows(auth.date_range, auth.window_policy, trading_days)
    else:
        date_windows = _calendar_windows(auth.date_range, auth.window_policy)

    windows: list[WindowPlan] = []
    for dataset in auth.datasets:
        for source_interface in auth.source_interface_allowlist:
            for index, (start, end) in enumerate(date_windows, start=1):
                start_text = start.isoformat()
                end_text = end.isoformat()
                window_id = (
                    f"{_clean_token(dataset)}-"
                    f"{start_text.replace('-', '')}-{end_text.replace('-', '')}-"
                    f"{auth.window_policy.policy_type}-{index:03d}"
                )
                run_id = f"{_clean_token(auth.authorization_id)}-{window_id}"
                fingerprint = _request_fingerprint(
                    auth,
                    dataset=dataset,
                    source_interface=source_interface,
                    start_date=start_text,
                    end_date=end_text,
                )
                windows.append(
                    WindowPlan(
                        dataset=dataset,
                        source=source_interface.source,
                        source_interface=source_interface.interface,
                        window_id=window_id,
                        run_id=run_id,
                        start_date=start_text,
                        end_date=end_text,
                        request_fingerprint=fingerprint,
                        resume_token=_resume_token(fingerprint, 1),
                    )
                )
    return WindowedRunPlan(
        authorization_id=auth.authorization_id,
        windows=tuple(windows),
        status="planned",
        permission_counters=s09_zero_forbidden_counters(),
    )


def _payload_checksum(payload: Mapping[str, Any]) -> str:
    return _hash_payload({"payload": dict(payload)})


def record_window_failure(
    window: WindowPlan,
    error: S09Error,
    *,
    retryable: bool = True,
    manifest_ref: str | None = None,
    run_metadata_ref: str | None = None,
) -> WindowRunRecord:
    return WindowRunRecord(
        window_id=window.window_id,
        run_id=window.run_id,
        dataset=window.dataset,
        source=window.source,
        source_interface=window.source_interface,
        start_date=window.start_date,
        end_date=window.end_date,
        status="failed",
        attempt=window.attempt,
        request_fingerprint=window.request_fingerprint,
        resume_token=window.resume_token,
        manifest_ref=manifest_ref,
        run_metadata_ref=run_metadata_ref,
        error_code=error.code,
        error_message=error.message,
        retryable=retryable,
        permission_counters=s09_zero_forbidden_counters(),
    )


def execute_windowed_run(
    plan: WindowedRunPlan,
    authorization: RunAuthorization | AuthorizationBuildResult | Mapping[str, Any],
    *,
    provider: WindowProvider,
    writer: WindowWriter,
    gate_result: S09RunGateResult | None = None,
) -> WindowedRunSummary:
    """执行 fake provider / tmp_path window run；真实执行必须由 gate 另行授权。"""

    if gate_result is None:
        return WindowedRunSummary(
            status="blocked",
            authorization_id=plan.authorization_id,
            windows_total=len(plan.windows),
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            conflict_count=0,
            records=(),
            permission_counters=s09_zero_forbidden_counters(),
            errors=(
                S09Error(
                    S09_REAL_RUN_NOT_AUTHORIZED,
                    "缺少 S09 run gate 结果，provider/lake 执行 fail-closed",
                ),
            ),
        )

    auth_result = (
        authorization
        if isinstance(authorization, AuthorizationBuildResult)
        else build_s09_authorization(authorization)
    )
    if not auth_result.ok or auth_result.authorization is None:
        return WindowedRunSummary(
            status="blocked",
            authorization_id=None,
            windows_total=len(plan.windows),
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            conflict_count=0,
            records=(),
            permission_counters=s09_zero_forbidden_counters(),
            errors=auth_result.errors,
        )
    if plan.status != "planned":
        return WindowedRunSummary(
            status="blocked",
            authorization_id=auth_result.authorization.authorization_id,
            windows_total=len(plan.windows),
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            conflict_count=0,
            records=(),
            permission_counters=s09_zero_forbidden_counters(),
            errors=plan.errors,
        )
    if gate_result is not None and not gate_result.run_allowed:
        return WindowedRunSummary(
            status="blocked",
            authorization_id=auth_result.authorization.authorization_id,
            windows_total=len(plan.windows),
            succeeded_count=0,
            failed_count=0,
            skipped_count=0,
            conflict_count=0,
            records=(),
            permission_counters=s09_zero_forbidden_counters(),
            errors=gate_result.errors,
        )

    auth = auth_result.authorization
    records: list[WindowRunRecord] = []
    errors: list[S09Error] = []
    for window in plan.windows:
        try:
            payload = provider.fetch(window)
            checksum = _payload_checksum(payload)
            raw_ref, manifest_ref, metadata_ref = writer.write_success(
                window,
                auth,
                payload,
                checksum,
            )
            records.append(
                WindowRunRecord(
                    window_id=window.window_id,
                    run_id=window.run_id,
                    dataset=window.dataset,
                    source=window.source,
                    source_interface=window.source_interface,
                    start_date=window.start_date,
                    end_date=window.end_date,
                    status="succeeded",
                    attempt=window.attempt,
                    request_fingerprint=window.request_fingerprint,
                    resume_token=window.resume_token,
                    raw_refs=(raw_ref,),
                    manifest_ref=manifest_ref,
                    run_metadata_ref=metadata_ref,
                    raw_checksum=checksum,
                    permission_counters=s09_zero_forbidden_counters(),
                )
            )
        except WindowProviderError as exc:
            error = S09Error(exc.code, str(exc), {"window_id": window.window_id})
            manifest_ref, metadata_ref = writer.write_failure(window, auth, error)
            records.append(
                record_window_failure(
                    window,
                    error,
                    retryable=exc.retryable,
                    manifest_ref=manifest_ref,
                    run_metadata_ref=metadata_ref,
                )
            )
            errors.append(error)
            if auth.window_policy.stop_on_error:
                break
        except Exception as exc:  # noqa: BLE001 - writer/provider 异常需要转为窗口失败
            error = S09Error(S09_RAW_WRITE_FAILED, str(exc), {"window_id": window.window_id})
            try:
                manifest_ref, metadata_ref = writer.write_failure(window, auth, error)
            except Exception:  # noqa: BLE001
                manifest_ref, metadata_ref = None, None
            records.append(
                record_window_failure(
                    window,
                    error,
                    retryable=False,
                    manifest_ref=manifest_ref,
                    run_metadata_ref=metadata_ref,
                )
            )
            errors.append(error)
            if auth.window_policy.stop_on_error:
                break

    succeeded = sum(1 for record in records if record.status == "succeeded")
    failed = sum(1 for record in records if record.status == "failed")
    return WindowedRunSummary(
        status="succeeded" if failed == 0 else "partial_failed",
        authorization_id=auth.authorization_id,
        windows_total=len(plan.windows),
        succeeded_count=succeeded,
        failed_count=failed,
        skipped_count=0,
        conflict_count=0,
        records=tuple(records),
        permission_counters=s09_zero_forbidden_counters(),
        errors=tuple(errors),
        fake_provider_calls=getattr(provider, "call_count", len(records)),
        tmp_path_write_count=getattr(writer, "tmp_path_write_count", 0),
        raw_write_count=getattr(writer, "raw_write_count", 0),
        manifest_write_count=getattr(writer, "manifest_write_count", 0),
        run_metadata_write_count=getattr(writer, "run_metadata_write_count", 0),
    )


def resume_windowed_run(
    previous_summary: WindowedRunSummary | Mapping[str, Any],
    authorization: RunAuthorization | AuthorizationBuildResult | Mapping[str, Any],
    *,
    trading_days: Sequence[str | date] = (),
) -> ResumePlanResult:
    """根据 request fingerprint 精确判断可恢复窗口。"""

    auth_result = (
        authorization
        if isinstance(authorization, AuthorizationBuildResult)
        else build_s09_authorization(authorization)
    )
    if not auth_result.ok or auth_result.authorization is None:
        return ResumePlanResult(
            status="blocked",
            run_allowed=False,
            windows_to_run=(),
            skipped_windows=(),
            conflicts=(),
            errors=auth_result.errors,
        )
    plan = plan_windowed_run(auth_result.authorization, trading_days=trading_days)
    if isinstance(previous_summary, WindowedRunSummary):
        records = previous_summary.records
    else:
        records = tuple(
            WindowRunRecord(**record)
            for record in previous_summary.get("records", [])
            if isinstance(record, Mapping)
        )
    previous_by_window = {record.window_id: record for record in records}
    conflicts: list[dict[str, Any]] = []
    skipped: list[str] = []
    windows_to_run: list[WindowPlan] = []
    for window in plan.windows:
        previous = previous_by_window.get(window.window_id)
        if previous is None:
            windows_to_run.append(window)
            continue
        if previous.request_fingerprint != window.request_fingerprint:
            conflicts.append(
                {
                    "window_id": window.window_id,
                    "previous_fingerprint": previous.request_fingerprint,
                    "current_fingerprint": window.request_fingerprint,
                }
            )
            continue
        if previous.status == "succeeded" and auth_result.authorization.resume_policy.skip_success:
            skipped.append(window.window_id)
        elif previous.status == "failed" and auth_result.authorization.resume_policy.retry_failed:
            windows_to_run.append(window)
        else:
            skipped.append(window.window_id)

    if conflicts:
        return ResumePlanResult(
            status=S09_RESUME_CONFLICT,
            run_allowed=False,
            windows_to_run=(),
            skipped_windows=tuple(skipped),
            conflicts=tuple(conflicts),
            errors=(
                S09Error(
                    S09_RESUME_CONFLICT,
                    "resume request fingerprint 不一致，必须 fail-closed",
                    {"conflict_count": len(conflicts)},
                ),
            ),
        )
    return ResumePlanResult(
        status="planned",
        run_allowed=True,
        windows_to_run=tuple(windows_to_run),
        skipped_windows=tuple(skipped),
        conflicts=(),
    )


def rollback_windowed_run(
    summary: WindowedRunSummary,
    *,
    execute: bool = False,
    execute_authorized: bool = False,
) -> RollbackPreview:
    """默认只生成 rollback preview，不删除、不归档、不迁移文件。"""

    actions: list[dict[str, Any]] = []
    for record in summary.records:
        for raw_ref in record.raw_refs:
            actions.append(
                {
                    "action": "preview_remove_raw_ref",
                    "window_id": record.window_id,
                    "target_ref": raw_ref,
                    "execute": False,
                }
            )
        if record.manifest_ref:
            actions.append(
                {
                    "action": "preview_mark_manifest_ref",
                    "window_id": record.window_id,
                    "target_ref": record.manifest_ref,
                    "execute": False,
                }
            )
        if record.run_metadata_ref:
            actions.append(
                {
                    "action": "preview_mark_run_metadata_ref",
                    "window_id": record.window_id,
                    "target_ref": record.run_metadata_ref,
                    "execute": False,
                }
            )
    errors: tuple[S09Error, ...] = ()
    status = "preview"
    if execute and not execute_authorized:
        status = "blocked"
        errors = (
            S09Error(
                S09_ROLLBACK_REQUIRES_AUTHORIZATION,
                "rollback execute 需要额外授权；当前只允许 preview",
            ),
        )
    return RollbackPreview(
        status=status,
        execute_authorized=execute_authorized,
        actions=tuple(actions),
        errors=errors,
    )


__all__ = [
    "AuthorizationBuildResult",
    "CredentialSourcePolicy",
    "DateRange",
    "FakeWindowProvider",
    "RollbackPolicy",
    "RollbackPreview",
    "RunAuthorization",
    "S09_DEFAULT_PILOT_END",
    "S09_DEFAULT_PILOT_START",
    "S09Error",
    "S09GateContext",
    "S09ResumePolicy",
    "S09RunGateResult",
    "SourceInterface",
    "TmpPathWindowWriter",
    "WindowPlan",
    "WindowPolicy",
    "WindowProviderError",
    "WindowRunRecord",
    "WindowedRunPlan",
    "WindowedRunSummary",
    "build_s09_authorization",
    "default_s09_pilot_date_range",
    "evaluate_s09_run_gate",
    "execute_windowed_run",
    "plan_windowed_run",
    "record_window_failure",
    "resume_windowed_run",
    "rollback_windowed_run",
    "s09_zero_forbidden_counters",
]
