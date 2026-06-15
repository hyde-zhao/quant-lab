"""CR014 append-only manifest record 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Mapping

from .contracts import (
    QUALITY_STATUS_VALUES,
    READINESS_STATUS_VALUES,
    SCHEMA_VERSION,
)

CR014_MANIFEST_REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "dataset",
    "source",
    "source_interface",
    "schema_hash",
    "row_count",
    "quality_status",
    "readiness_status",
    "lineage_checksum",
    "lifecycle_denominator_ref",
    "candidate_path",
)

MANIFEST_INCOMPLETE = "manifest_incomplete"
MANIFEST_ROW_COUNT_INVALID = "manifest_row_count_invalid"
MANIFEST_QUALITY_STATUS_INVALID = "manifest_quality_status_invalid"
MANIFEST_READINESS_STATUS_INVALID = "manifest_readiness_status_invalid"

CR014_S09_WINDOW_MANIFEST_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "record_type",
    "authorization_id",
    "run_id",
    "window_id",
    "dataset",
    "source",
    "source_interface",
    "start_date",
    "end_date",
    "status",
    "attempt",
    "request_fingerprint",
    "resume_token",
    "permission_counters",
)

S09_WINDOW_MANIFEST_INCOMPLETE = "s09_window_manifest_incomplete"


@dataclass(frozen=True, slots=True)
class ManifestRecord:
    """CR014 manifest 单条 append-only 记录，不负责文件写入。"""

    run_id: str
    dataset: str
    source: str
    source_interface: str
    schema_hash: str
    row_count: int
    quality_status: str
    readiness_status: str
    lineage_checksum: str
    lifecycle_denominator_ref: str
    candidate_path: str
    schema_version: str = SCHEMA_VERSION
    partition: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ManifestCompletenessResult:
    passed: bool
    publish_allowed: bool
    missing_fields: tuple[str, ...] = ()
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()
    required_fields: tuple[str, ...] = CR014_MANIFEST_REQUIRED_FIELDS

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_mapping(record: ManifestRecord | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if is_dataclass(record):
        return asdict(record)
    raise TypeError(f"不支持的 manifest record 类型: {type(record)!r}")


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def validate_manifest_record(
    record: ManifestRecord | Mapping[str, Any],
) -> ManifestCompletenessResult:
    """校验 manifest record 完整性；不读取或写入 manifest 文件。"""

    payload = _as_mapping(record)
    missing = tuple(
        field
        for field in CR014_MANIFEST_REQUIRED_FIELDS
        if field not in payload or _is_missing_value(payload[field])
    )
    error_codes: list[str] = []
    details: list[dict[str, Any]] = []
    if missing:
        error_codes.append(MANIFEST_INCOMPLETE)
        details.append({"code": MANIFEST_INCOMPLETE, "missing_fields": list(missing)})

    row_count = payload.get("row_count")
    if row_count is not None:
        if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0:
            error_codes.append(MANIFEST_ROW_COUNT_INVALID)
            details.append({"code": MANIFEST_ROW_COUNT_INVALID, "row_count": row_count})

    quality_status = payload.get("quality_status")
    if quality_status is not None and quality_status not in QUALITY_STATUS_VALUES:
        error_codes.append(MANIFEST_QUALITY_STATUS_INVALID)
        details.append(
            {
                "code": MANIFEST_QUALITY_STATUS_INVALID,
                "quality_status": quality_status,
                "allowed": list(QUALITY_STATUS_VALUES),
            }
        )

    readiness_status = payload.get("readiness_status")
    if readiness_status is not None and readiness_status not in READINESS_STATUS_VALUES:
        error_codes.append(MANIFEST_READINESS_STATUS_INVALID)
        details.append(
            {
                "code": MANIFEST_READINESS_STATUS_INVALID,
                "readiness_status": readiness_status,
                "allowed": list(READINESS_STATUS_VALUES),
            }
        )

    passed = not error_codes
    return ManifestCompletenessResult(
        passed=passed,
        publish_allowed=passed,
        missing_fields=missing,
        error_codes=tuple(dict.fromkeys(error_codes)),
        details=tuple(details),
    )


def build_s09_window_manifest_record(
    *,
    window: Mapping[str, Any],
    authorization: Mapping[str, Any],
    status: str,
    raw_checksum: str | None,
    raw_refs: tuple[str, ...] = (),
    failure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """构建 S09 window raw/manifest/run metadata 记录；不写 current pointer。"""

    permission_counters = {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "current_pointer_changes": 0,
        "publish_count": 0,
        "catalog_current_pointer_publish": 0,
        "retention_execute": 0,
        "retention_execute_count": 0,
        "duckdb_open": 0,
        "duckdb_write": 0,
        "duckdb_dependency_change": 0,
        "duckdb_files_created": 0,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "cr014_s09_window_manifest",
        "authorization_id": authorization.get("authorization_id"),
        "run_id": window.get("run_id"),
        "window_id": window.get("window_id"),
        "dataset": window.get("dataset"),
        "source": window.get("source"),
        "source_interface": window.get("source_interface"),
        "start_date": window.get("start_date"),
        "end_date": window.get("end_date"),
        "status": status,
        "attempt": window.get("attempt", 1),
        "request_fingerprint": window.get("request_fingerprint"),
        "resume_token": window.get("resume_token"),
        "raw_checksum": raw_checksum,
        "raw_refs": list(raw_refs),
        "failure": dict(failure or {}),
        "permission_counters": permission_counters,
        "current_pointer_changes": 0,
        "publish_count": 0,
        "retention_execute_count": 0,
        "duckdb_open_count": 0,
        "duckdb_write_count": 0,
        "duckdb_dependency_change": 0,
        "credential_source_policy": dict(authorization.get("credential_source_policy") or {}),
        "lake_root_label": authorization.get("lake_root_label"),
        "lake_root_fingerprint": authorization.get("lake_root_fingerprint"),
    }


def validate_s09_window_manifest_record(
    record: Mapping[str, Any],
) -> ManifestCompletenessResult:
    """校验 S09 window manifest 合同；publish_allowed 永远为 False。"""

    payload = dict(record)
    missing = tuple(
        field
        for field in CR014_S09_WINDOW_MANIFEST_REQUIRED_FIELDS
        if field not in payload or _is_missing_value(payload[field])
    )
    details: list[dict[str, Any]] = []
    error_codes: list[str] = []
    if missing:
        error_codes.append(S09_WINDOW_MANIFEST_INCOMPLETE)
        details.append(
            {
                "code": S09_WINDOW_MANIFEST_INCOMPLETE,
                "missing_fields": list(missing),
            }
        )
    passed = not error_codes
    return ManifestCompletenessResult(
        passed=passed,
        publish_allowed=False,
        missing_fields=missing,
        error_codes=tuple(error_codes),
        details=tuple(details),
        required_fields=CR014_S09_WINDOW_MANIFEST_REQUIRED_FIELDS,
    )


__all__ = [
    "CR014_MANIFEST_REQUIRED_FIELDS",
    "CR014_S09_WINDOW_MANIFEST_REQUIRED_FIELDS",
    "MANIFEST_INCOMPLETE",
    "MANIFEST_QUALITY_STATUS_INVALID",
    "MANIFEST_READINESS_STATUS_INVALID",
    "MANIFEST_ROW_COUNT_INVALID",
    "S09_WINDOW_MANIFEST_INCOMPLETE",
    "ManifestCompletenessResult",
    "ManifestRecord",
    "build_s09_window_manifest_record",
    "validate_manifest_record",
    "validate_s09_window_manifest_record",
]
