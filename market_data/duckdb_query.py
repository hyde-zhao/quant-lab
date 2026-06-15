"""CR014 DuckDB 只读 query / audit 边界合同。"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .catalog import validate_catalog_pointer

READ_MODE_PUBLISHED_CURRENT_TRUTH = "published_current_truth"
READ_MODE_CANDIDATE_AUDIT = "candidate_audit"
READ_MODE_FALLBACK = "fallback"

DUCKDB_DEPENDENCY_UNAVAILABLE = "duckdb_dependency_unavailable"
READONLY_OPEN_FAILED = "readonly_open_failed"
FORBIDDEN_SQL = "forbidden_sql"
SQL_TEMPLATE_NOT_ALLOWED = "sql_template_not_allowed"
CATALOG_POINTER_MISSING = "catalog_pointer_missing"
CATALOG_POINTER_INCOMPLETE = "catalog_pointer_incomplete"
PUBLISHED_PATH_MISSING = "published_path_missing"
CANDIDATE_PATH_REJECTED = "candidate_path_rejected"
READ_MODE_INVALID = "read_mode_invalid"

CLAIM_EFFECT_EVIDENCE_ONLY = "evidence_only"
SOURCE_OF_TRUTH_CATALOG_POINTER = "catalog_current_pointer"
SOURCE_OF_TRUTH_CANDIDATE_AUDIT = "candidate_audit_evidence"
ENGINE_DUCKDB = "duckdb"
ENGINE_FALLBACK = "fallback_pandas_pyarrow"

DEFAULT_SQL_TEMPLATES: dict[str, str] = {
    "row_count": "SELECT COUNT(*) AS row_count FROM read_parquet({source_path})",
    "projection_scan": "SELECT {columns} FROM read_parquet({source_path}) {where_clause}",
    "audit_profile": "SELECT COUNT(*) AS row_count FROM read_parquet({source_path})",
}

_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b("
    r"CREATE|INSERT|UPDATE|DELETE|COPY|EXPORT|ATTACH|INSTALL|LOAD|PRAGMA|"
    r"DROP|ALTER|TRUNCATE|MERGE|VACUUM|CALL"
    r")\b",
    re.IGNORECASE,
)
_READONLY_SQL_PATTERN = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)
_GLOB_PATTERN = re.compile(r"[*?\[]")


class DuckDBReadOnlyOpenError(RuntimeError):
    """DuckDB 只读打开失败；调用方必须进入 fallback，不得改用写模式。"""


class ReadOnlyDuckDBAdapter(Protocol):
    """可注入 DuckDB adapter；本模块不把 DuckDB 作为硬依赖。"""

    def execute_readonly(self, request: "ReadOnlyQueryRequest") -> Any:
        """以只读方式执行请求；失败时抛出 DuckDBReadOnlyOpenError。"""


@dataclass(frozen=True, slots=True)
class PermissionCounters:
    provider_fetches: int = 0
    lake_writes: int = 0
    credential_reads: int = 0
    dependency_changes: int = 0
    duckdb_writes: int = 0
    publish_count: int = 0
    source_of_truth_updates: int = 0
    current_pointer_changes: int = 0
    legacy_data_operations: int = 0
    old_report_overwrites: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DuckDBBoundaryError:
    code: str
    message: str
    mode: str | None = None
    path: str | None = None
    sql_template_id: str | None = None
    details: tuple[dict[str, Any], ...] = ()
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "mode": self.mode,
            "path": self.path,
            "sql_template_id": self.sql_template_id,
            "details": [dict(item) for item in self.details],
            "permission_counters": self.permission_counters.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ReadOnlyQueryPolicy:
    sql_templates: Mapping[str, str] = field(default_factory=lambda: DEFAULT_SQL_TEMPLATES)
    duckdb_dependency_approved: bool = False
    allowed_published_paths: tuple[str | Path, ...] = ()
    candidate_audit_paths: tuple[str | Path, ...] = ()
    require_candidate_path_allowlist: bool = True
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)


@dataclass(frozen=True, slots=True)
class ReadOnlyQueryRequest:
    mode: str
    dataset: str
    sql_template_id: str
    source_path: str
    source_of_truth: str
    projections: tuple[str, ...] = ()
    partition_filters: Mapping[str, Any] = field(default_factory=dict)
    catalog_pointer: Mapping[str, Any] | None = None
    candidate_path: str | None = None
    manifest_refs: tuple[Mapping[str, Any] | str, ...] = ()
    rendered_sql: str = ""
    claim_effect: str = CLAIM_EFFECT_EVIDENCE_ONLY
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "dataset": self.dataset,
            "sql_template_id": self.sql_template_id,
            "source_path": self.source_path,
            "source_of_truth": self.source_of_truth,
            "projections": list(self.projections),
            "partition_filters": dict(self.partition_filters),
            "catalog_pointer": dict(self.catalog_pointer or {}),
            "candidate_path": self.candidate_path,
            "manifest_refs": [dict(item) if isinstance(item, Mapping) else item for item in self.manifest_refs],
            "rendered_sql": self.rendered_sql,
            "claim_effect": self.claim_effect,
            "permission_counters": self.permission_counters.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FallbackSelection:
    engine: str
    reason_code: str | None = None
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "reason_code": self.reason_code,
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class ReadOnlyQueryResult:
    ok: bool
    request: ReadOnlyQueryRequest
    engine: str
    rows: tuple[Mapping[str, Any], ...] = ()
    fallback_reason: str | None = None
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)
    claim_effect: str = CLAIM_EFFECT_EVIDENCE_ONLY

    @property
    def publish_count(self) -> int:
        return self.permission_counters.publish_count

    @property
    def source_of_truth_updates(self) -> int:
        return self.permission_counters.source_of_truth_updates

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "request": self.request.to_dict(),
            "engine": self.engine,
            "rows": [dict(row) for row in self.rows],
            "row_count": len(self.rows),
            "fallback_reason": self.fallback_reason,
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
            "permission_counters": self.permission_counters.to_dict(),
            "publish_count": self.publish_count,
            "source_of_truth_updates": self.source_of_truth_updates,
            "claim_effect": self.claim_effect,
        }


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _normalise_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _has_glob(path: str | Path) -> bool:
    return bool(_GLOB_PATTERN.search(str(path)))


def _path_in_allowlist(path: str | Path, allowed_paths: Sequence[str | Path]) -> bool:
    if not allowed_paths:
        return True
    target = _normalise_path(path)
    return target in {_normalise_path(item) for item in allowed_paths}


def validate_sql_template(
    sql_template_id: str,
    policy: ReadOnlyQueryPolicy | None = None,
) -> str | DuckDBBoundaryError:
    effective_policy = policy or ReadOnlyQueryPolicy()
    template = effective_policy.sql_templates.get(sql_template_id)
    if template is None:
        return DuckDBBoundaryError(
            code=SQL_TEMPLATE_NOT_ALLOWED,
            message="SQL template 不在白名单中",
            sql_template_id=sql_template_id,
        )
    if _FORBIDDEN_SQL_PATTERN.search(template) or not _READONLY_SQL_PATTERN.match(template):
        return DuckDBBoundaryError(
            code=FORBIDDEN_SQL,
            message="SQL template 包含写操作或非 SELECT 形态",
            sql_template_id=sql_template_id,
            details=({"template": template},),
        )
    return template


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _render_sql(
    template: str,
    *,
    source_path: str | Path,
    projections: Sequence[str],
    partition_filters: Mapping[str, Any],
) -> str:
    columns = ", ".join(projections) if projections else "*"
    if partition_filters:
        clauses = [f"{key} = {_sql_literal(str(value))}" for key, value in sorted(partition_filters.items())]
        where_clause = "WHERE " + " AND ".join(clauses)
    else:
        where_clause = ""
    return template.format(
        source_path=_sql_literal(source_path),
        columns=columns,
        where_clause=where_clause,
    ).strip()


def build_readonly_query_request(
    *,
    mode: str,
    dataset: str,
    sql_template_id: str,
    catalog_pointer: Any = None,
    candidate_path: str | Path | None = None,
    manifest_refs: Sequence[Mapping[str, Any] | str] = (),
    projections: Sequence[str] = (),
    partition_filters: Mapping[str, Any] | None = None,
    policy: ReadOnlyQueryPolicy | None = None,
) -> ReadOnlyQueryRequest | DuckDBBoundaryError:
    """构建只读查询请求；失败时返回结构化错误，不访问真实数据。"""

    effective_policy = policy or ReadOnlyQueryPolicy()
    template = validate_sql_template(sql_template_id, effective_policy)
    if isinstance(template, DuckDBBoundaryError):
        return template

    filters = dict(partition_filters or {})
    if mode == READ_MODE_PUBLISHED_CURRENT_TRUTH:
        pointer_payload = _payload(catalog_pointer)
        if not pointer_payload:
            return DuckDBBoundaryError(
                code=CATALOG_POINTER_MISSING,
                message="published 模式必须提供 catalog current pointer",
                mode=mode,
                sql_template_id=sql_template_id,
            )
        pointer_validation = validate_catalog_pointer(pointer_payload)
        if not pointer_validation.passed:
            return DuckDBBoundaryError(
                code=CATALOG_POINTER_INCOMPLETE,
                message="catalog current pointer 字段不完整",
                mode=mode,
                sql_template_id=sql_template_id,
                details=tuple(pointer_validation.details),
            )
        published_path = pointer_payload.get("published_path") or pointer_payload.get("canonical_path")
        if not published_path:
            return DuckDBBoundaryError(
                code=PUBLISHED_PATH_MISSING,
                message="catalog current pointer 缺少 published_path/canonical_path",
                mode=mode,
                sql_template_id=sql_template_id,
                details=({"required": ["published_path", "canonical_path"]},),
            )
        if _has_glob(published_path) or not _path_in_allowlist(
            published_path,
            effective_policy.allowed_published_paths,
        ):
            return DuckDBBoundaryError(
                code=CANDIDATE_PATH_REJECTED,
                message="published path 不在只读白名单中或包含 glob",
                mode=mode,
                path=str(published_path),
                sql_template_id=sql_template_id,
            )
        rendered_sql = _render_sql(
            str(template),
            source_path=published_path,
            projections=projections,
            partition_filters=filters,
        )
        return ReadOnlyQueryRequest(
            mode=mode,
            dataset=dataset,
            sql_template_id=sql_template_id,
            source_path=str(published_path),
            source_of_truth=SOURCE_OF_TRUTH_CATALOG_POINTER,
            projections=tuple(projections),
            partition_filters=filters,
            catalog_pointer=pointer_payload,
            manifest_refs=tuple(manifest_refs),
            rendered_sql=rendered_sql,
            permission_counters=effective_policy.permission_counters,
        )

    if mode == READ_MODE_CANDIDATE_AUDIT:
        if candidate_path is None or not str(candidate_path).strip():
            return DuckDBBoundaryError(
                code=CANDIDATE_PATH_REJECTED,
                message="candidate audit 模式必须提供受控 candidate path",
                mode=mode,
                sql_template_id=sql_template_id,
            )
        if _has_glob(candidate_path):
            return DuckDBBoundaryError(
                code=CANDIDATE_PATH_REJECTED,
                message="candidate audit path 禁止 glob",
                mode=mode,
                path=str(candidate_path),
                sql_template_id=sql_template_id,
            )
        if effective_policy.require_candidate_path_allowlist and not effective_policy.candidate_audit_paths:
            return DuckDBBoundaryError(
                code=CANDIDATE_PATH_REJECTED,
                message="candidate audit path 必须由 policy 显式白名单控制",
                mode=mode,
                path=str(candidate_path),
                sql_template_id=sql_template_id,
            )
        if not _path_in_allowlist(candidate_path, effective_policy.candidate_audit_paths):
            return DuckDBBoundaryError(
                code=CANDIDATE_PATH_REJECTED,
                message="candidate audit path 不在白名单中",
                mode=mode,
                path=str(candidate_path),
                sql_template_id=sql_template_id,
            )
        rendered_sql = _render_sql(
            str(template),
            source_path=candidate_path,
            projections=projections,
            partition_filters=filters,
        )
        return ReadOnlyQueryRequest(
            mode=mode,
            dataset=dataset,
            sql_template_id=sql_template_id,
            source_path=str(candidate_path),
            source_of_truth=SOURCE_OF_TRUTH_CANDIDATE_AUDIT,
            projections=tuple(projections),
            partition_filters=filters,
            candidate_path=str(candidate_path),
            manifest_refs=tuple(manifest_refs),
            rendered_sql=rendered_sql,
            permission_counters=effective_policy.permission_counters,
        )

    return DuckDBBoundaryError(
        code=READ_MODE_INVALID,
        message="未知 DuckDB read-only mode",
        mode=mode,
        sql_template_id=sql_template_id,
        details=(
            {"allowed": [READ_MODE_PUBLISHED_CURRENT_TRUTH, READ_MODE_CANDIDATE_AUDIT, READ_MODE_FALLBACK]},
        ),
    )


def select_fallback_policy(
    policy: ReadOnlyQueryPolicy | None = None,
    adapter: ReadOnlyDuckDBAdapter | None = None,
) -> FallbackSelection:
    """选择执行引擎；默认无 DuckDB 依赖授权，进入 fallback。"""

    effective_policy = policy or ReadOnlyQueryPolicy()
    if not effective_policy.duckdb_dependency_approved or adapter is None:
        return FallbackSelection(
            engine=ENGINE_FALLBACK,
            reason_code=DUCKDB_DEPENDENCY_UNAVAILABLE,
            details=({"duckdb_dependency_change": effective_policy.permission_counters.dependency_changes},),
        )
    return FallbackSelection(engine=ENGINE_DUCKDB)


def _normalise_rows(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        rows = value.get("rows")
        if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)):
            return tuple(dict(item) for item in rows if isinstance(item, Mapping))
        return (dict(value),)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(dict(item) for item in value if isinstance(item, Mapping))
    return ()


def run_readonly_query(
    request: ReadOnlyQueryRequest,
    *,
    policy: ReadOnlyQueryPolicy | None = None,
    adapter: ReadOnlyDuckDBAdapter | None = None,
    fallback_rows: Sequence[Mapping[str, Any]] = (),
) -> ReadOnlyQueryResult:
    """运行只读查询合同；DuckDB 不可用或只读打开失败时输出 fallback 结果。"""

    selection = select_fallback_policy(policy, adapter)
    if selection.engine == ENGINE_FALLBACK:
        return ReadOnlyQueryResult(
            ok=True,
            request=request,
            engine=ENGINE_FALLBACK,
            rows=tuple(dict(row) for row in fallback_rows),
            fallback_reason=selection.reason_code,
            details=selection.details,
            permission_counters=request.permission_counters,
        )
    try:
        rows = _normalise_rows(adapter.execute_readonly(request) if adapter else None)
    except DuckDBReadOnlyOpenError as exc:
        return ReadOnlyQueryResult(
            ok=True,
            request=request,
            engine=ENGINE_FALLBACK,
            rows=tuple(dict(row) for row in fallback_rows),
            fallback_reason=READONLY_OPEN_FAILED,
            error_codes=(READONLY_OPEN_FAILED,),
            details=({"reason": str(exc)},),
            permission_counters=request.permission_counters,
        )
    return ReadOnlyQueryResult(
        ok=True,
        request=request,
        engine=ENGINE_DUCKDB,
        rows=rows,
        permission_counters=request.permission_counters,
    )


def run_published_current_truth_query(
    request: ReadOnlyQueryRequest,
    *,
    policy: ReadOnlyQueryPolicy | None = None,
    adapter: ReadOnlyDuckDBAdapter | None = None,
    fallback_rows: Sequence[Mapping[str, Any]] = (),
) -> ReadOnlyQueryResult | DuckDBBoundaryError:
    if request.mode != READ_MODE_PUBLISHED_CURRENT_TRUTH:
        return DuckDBBoundaryError(
            code=READ_MODE_INVALID,
            message="run_published_current_truth_query 仅接受 published_current_truth 请求",
            mode=request.mode,
            sql_template_id=request.sql_template_id,
        )
    return run_readonly_query(request, policy=policy, adapter=adapter, fallback_rows=fallback_rows)


def run_candidate_audit_query(
    request: ReadOnlyQueryRequest,
    *,
    policy: ReadOnlyQueryPolicy | None = None,
    adapter: ReadOnlyDuckDBAdapter | None = None,
    fallback_rows: Sequence[Mapping[str, Any]] = (),
) -> ReadOnlyQueryResult | DuckDBBoundaryError:
    if request.mode != READ_MODE_CANDIDATE_AUDIT:
        return DuckDBBoundaryError(
            code=READ_MODE_INVALID,
            message="run_candidate_audit_query 仅接受 candidate_audit 请求",
            mode=request.mode,
            sql_template_id=request.sql_template_id,
        )
    return run_readonly_query(request, policy=policy, adapter=adapter, fallback_rows=fallback_rows)


__all__ = [
    "CATALOG_POINTER_INCOMPLETE",
    "CATALOG_POINTER_MISSING",
    "CANDIDATE_PATH_REJECTED",
    "CLAIM_EFFECT_EVIDENCE_ONLY",
    "DEFAULT_SQL_TEMPLATES",
    "DUCKDB_DEPENDENCY_UNAVAILABLE",
    "DuckDBBoundaryError",
    "DuckDBReadOnlyOpenError",
    "ENGINE_DUCKDB",
    "ENGINE_FALLBACK",
    "FORBIDDEN_SQL",
    "FallbackSelection",
    "PUBLISHED_PATH_MISSING",
    "PermissionCounters",
    "READONLY_OPEN_FAILED",
    "READ_MODE_CANDIDATE_AUDIT",
    "READ_MODE_FALLBACK",
    "READ_MODE_INVALID",
    "READ_MODE_PUBLISHED_CURRENT_TRUTH",
    "ReadOnlyDuckDBAdapter",
    "ReadOnlyQueryPolicy",
    "ReadOnlyQueryRequest",
    "ReadOnlyQueryResult",
    "SQL_TEMPLATE_NOT_ALLOWED",
    "SOURCE_OF_TRUTH_CANDIDATE_AUDIT",
    "SOURCE_OF_TRUTH_CATALOG_POINTER",
    "build_readonly_query_request",
    "run_candidate_audit_query",
    "run_published_current_truth_query",
    "run_readonly_query",
    "select_fallback_policy",
    "validate_sql_template",
]
