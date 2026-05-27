"""raw 与 manifest 写入/读取工具。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts import (
    MANIFEST_REQUIRED_FIELDS,
    SCHEMA_VERSION,
    TERMINAL_MANIFEST_STATUS_VALUES,
)
from .connectors.protocol import ConnectorRequest, ConnectorResult
from .lake_layout import LakeLayout, ensure_parent_dirs_for_write

SENSITIVE_KEY_PARTS = ("token", "secret", "password", "cookie", "session", "key")


class StorageWriteError(RuntimeError):
    """raw 或 manifest 写入失败。"""


class ManifestCorruptionError(RuntimeError):
    """manifest 损坏或 resume 索引不可判定。"""


class CredentialExposureError(ValueError):
    """即将写入 manifest 的内容包含敏感值。"""


@dataclass(frozen=True, slots=True)
class RawWriteResult:
    path: Path
    relative_path: str
    checksum: str
    row_count: int


def sanitize_params(params: Mapping[str, Any]) -> dict[str, Any]:
    def sanitize(value: Any) -> Any:
        if isinstance(value, Mapping):
            clean: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key)
                if any(part in key_text.lower() for part in SENSITIVE_KEY_PARTS):
                    clean[key_text] = "<redacted>"
                else:
                    clean[key_text] = sanitize(item)
            return clean
        if isinstance(value, (list, tuple)):
            return [sanitize(item) for item in value]
        return value

    return sanitize(dict(params))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_params_hash(params: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(sanitize_params(params)).encode()).hexdigest()


def compute_idempotency_key(
    run_id: str,
    batch_id: str,
    source: str,
    interface: str,
    params_hash: str,
) -> str:
    payload = f"{run_id}|{batch_id}|{source}|{interface}|{params_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _raw_trade_date(request: ConnectorRequest) -> object:
    params = request.params
    if "trade_date" in params:
        return params["trade_date"]
    if "start_date" in params:
        return params["start_date"]
    if "date_range" in params:
        return params["date_range"][0]
    return "1970-01-01"


def _relative_to_root(path: Path, layout: LakeLayout) -> str:
    try:
        return str(path.relative_to(layout.lake_root))
    except ValueError:
        return str(path)


def _resolve_relative(path: str | None, layout: LakeLayout) -> Path | None:
    if not path:
        return None
    raw = Path(path)
    if raw.is_absolute():
        return raw
    return layout.lake_root / raw


class RawWriter:
    def write_atomic(
        self,
        result: ConnectorResult,
        request: ConnectorRequest,
        layout: LakeLayout,
    ) -> RawWriteResult:
        raw_path = layout.raw_run_batch_path(
            request.source,
            request.interface,
            _raw_trade_date(request),
            request.run_id,
            request.batch_id,
        )
        tmp_path = raw_path.with_suffix(raw_path.suffix + ".tmp")
        ensure_parent_dirs_for_write(tmp_path)
        metadata = {
            "_metadata": {
                "schema_version": SCHEMA_VERSION,
                "run_id": request.run_id,
                "batch_id": request.batch_id,
                "source": request.source,
                "interface": request.interface,
                "params": sanitize_params(request.params),
                "params_hash": request.params_hash,
                "row_count": len(result.rows),
                **result.metadata,
            }
        }
        try:
            with tmp_path.open("w", encoding="utf-8") as fh:
                fh.write(json.dumps(metadata, ensure_ascii=False, sort_keys=True) + "\n")
                for row in result.rows:
                    fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            data = tmp_path.read_bytes()
            checksum = hashlib.sha256(data).hexdigest()
            tmp_path.replace(raw_path)
        except OSError as exc:
            raise StorageWriteError(f"raw 写入失败: {tmp_path}") from exc
        return RawWriteResult(
            path=raw_path,
            relative_path=_relative_to_root(raw_path, layout),
            checksum=checksum,
            row_count=len(result.rows),
        )

    def quarantine(
        self,
        raw_path: Path,
        request: ConnectorRequest,
        layout: LakeLayout,
    ) -> Path:
        orphan_path = (
            layout.orphan_raw_root
            / request.run_id
            / f"{request.batch_id}{raw_path.suffix}"
        )
        ensure_parent_dirs_for_write(orphan_path)
        shutil.move(str(raw_path), str(orphan_path))
        return orphan_path


class ManifestWriter:
    def append(self, record: Mapping[str, Any], layout: LakeLayout) -> Path:
        missing = [field for field in MANIFEST_REQUIRED_FIELDS if field not in record]
        if missing:
            raise StorageWriteError(f"manifest 缺少字段: {','.join(missing)}")
        _assert_no_sensitive_values(record)
        manifest_path = layout.manifest_path()
        ensure_parent_dirs_for_write(manifest_path)
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True)
        try:
            with manifest_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as exc:
            raise StorageWriteError(f"manifest 写入失败: {manifest_path}") from exc
        return manifest_path


def _assert_no_sensitive_values(record: Mapping[str, Any]) -> None:
    text = json.dumps(record, ensure_ascii=False, sort_keys=True)
    lowered = text.lower()
    unsafe_literals = ("secret-value", "plain-token", "real-token")
    if any(item in lowered for item in unsafe_literals):
        raise CredentialExposureError("manifest 包含疑似敏感值")
    for env_name in (
        "TUSHARE_TOKEN",
        "TICKFLOW_TOKEN",
        "AKSHARE_TOKEN",
        "JQDATA_USERNAME",
        "JQDATA_PASSWORD",
    ):
        env_value = os.environ.get(env_name)
        if env_value and env_value in text:
            raise CredentialExposureError(f"manifest 包含敏感环境变量值: {env_name}")


def read_manifest_records(layout: LakeLayout) -> list[dict[str, Any]]:
    path = layout.manifest_path()
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestCorruptionError(f"manifest 第 {lineno} 行不是合法 JSON") from exc
            if not isinstance(record, dict):
                raise ManifestCorruptionError(f"manifest 第 {lineno} 行不是对象")
            records.append(record)
    return records


def _verify_raw(record: Mapping[str, Any], layout: LakeLayout) -> None:
    raw_path = _resolve_relative(record.get("raw_path"), layout)
    if raw_path is None or not raw_path.exists():
        raise ManifestCorruptionError("success manifest 指向的 raw 不存在")
    data = raw_path.read_bytes()
    checksum = hashlib.sha256(data).hexdigest()
    if record.get("raw_checksum") and record["raw_checksum"] != checksum:
        raise ManifestCorruptionError("raw checksum 与 manifest 不一致")
    row_count = max(0, len(raw_path.read_text(encoding="utf-8").splitlines()) - 1)
    if record.get("raw_row_count") is not None and record["raw_row_count"] != row_count:
        raise ManifestCorruptionError("raw row_count 与 manifest 不一致")


def verify_manifest_raw(record: Mapping[str, Any], layout: LakeLayout) -> None:
    _verify_raw(record, layout)


def load_manifest_index(
    layout: LakeLayout,
    *,
    verify_raw: bool = True,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in read_manifest_records(layout):
        key = record.get("idempotency_key")
        if not key:
            continue
        grouped.setdefault(str(key), []).append(record)

    index: dict[str, dict[str, Any]] = {}
    for key, records in grouped.items():
        terminal = [
            item
            for item in records
            if item.get("status") in TERMINAL_MANIFEST_STATUS_VALUES
        ]
        if not terminal:
            continue
        success_count = sum(1 for item in terminal if item.get("status") == "success")
        if success_count > 1:
            raise ManifestCorruptionError(f"重复 success manifest: {key}")
        latest = terminal[-1]
        if verify_raw and latest.get("status") == "success":
            _verify_raw(latest, layout)
        index[key] = latest
    return index


__all__ = [
    "CredentialExposureError",
    "ManifestCorruptionError",
    "ManifestWriter",
    "RawWriteResult",
    "RawWriter",
    "StorageWriteError",
    "canonical_json",
    "compute_idempotency_key",
    "compute_params_hash",
    "load_manifest_index",
    "read_manifest_records",
    "sanitize_params",
    "verify_manifest_raw",
]
