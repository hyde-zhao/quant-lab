"""CR010 数据湖备份、校验与恢复核心逻辑。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from .lake_layout import LakeLayout, ensure_parent_dirs_for_write

PathLike = str | Path

LAKE_ROOT_ENV = "MARKET_DATA_LAKE_ROOT"
ARCHIVE_ROOT_ENV = "MARKET_DATA_LAKE_ARCHIVE_ROOT"
BACKUP_ROOT_ENV = "MARKET_DATA_LAKE_BACKUP_ROOT"
RESTORE_ROOT_ENV = "MARKET_DATA_LAKE_RESTORE_ROOT"

LAKE_ROOT_LABEL = "<configured-lake-root>"
ARCHIVE_ROOT_LABEL = "<configured-archive-root>"
BACKUP_ROOT_LABEL = "<configured-backup-root>"
RESTORE_ROOT_LABEL = "<configured-restore-root>"

DATA_LAYERS = ("raw", "canonical", "gold", "quality")
ALWAYS_INCLUDED_LAYERS = ("manifest", "catalog")
SENSITIVE_PARTS = (".env", "token", "secret", "credential", "password")


class BackupRestoreError(RuntimeError):
    """备份或恢复边界错误。"""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": str(self), "details": self.details}


@dataclass(frozen=True, slots=True)
class BackupRestoreRoots:
    """四类数据湖根目录解析结果。

    路径值只供内部文件操作使用，公开报告必须使用 label。
    """

    lake_root: Path | None = None
    archive_root: Path | None = None
    backup_root: Path | None = None
    restore_root: Path | None = None

    def public_labels(self) -> dict[str, str | None]:
        return {
            "lake_root": LAKE_ROOT_LABEL if self.lake_root is not None else None,
            "archive_root": ARCHIVE_ROOT_LABEL if self.archive_root is not None else None,
            "backup_root": BACKUP_ROOT_LABEL if self.backup_root is not None else None,
            "restore_root": RESTORE_ROOT_LABEL if self.restore_root is not None else None,
        }


@dataclass(frozen=True, slots=True)
class BackupRequest:
    """备份计划、执行、校验和报告请求。"""

    release_id: str = "manual"
    run_id: str | None = None
    dataset: str | None = None
    lake_root: PathLike | None = None
    archive_root: PathLike | None = None
    backup_root: PathLike | None = None
    restore_root: PathLike | None = None
    include_raw: bool = True
    include_canonical: bool = True
    include_gold: bool = True
    include_quality: bool = True
    execute: bool = False


@dataclass(frozen=True, slots=True)
class RestoreRequest:
    """恢复计划、执行和 drill 请求。"""

    release_id: str = "manual"
    run_id: str | None = None
    dataset: str | None = None
    lake_root: PathLike | None = None
    archive_root: PathLike | None = None
    backup_root: PathLike | None = None
    restore_root: PathLike | None = None
    include_raw: bool = True
    include_canonical: bool = True
    include_gold: bool = True
    include_quality: bool = True
    execute: bool = False


@dataclass(frozen=True, slots=True)
class RetentionRequest:
    """保留策略预检请求；当前只生成计划，不删除文件。"""

    lake_root: PathLike | None = None
    run_id: str | None = None
    dataset: str | None = None
    execute: bool = False


@dataclass(frozen=True, slots=True)
class _SourceFile:
    relative_path: str
    path: Path = field(repr=False, compare=False)
    layer: str
    bytes: int
    checksum: str = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class _CopyEntry:
    relative_path: str
    source_root_label: str
    target_root_label: str
    target_relative_path: str
    bytes: int
    checksum_status: str
    action: str
    source_path: Path = field(repr=False, compare=False)
    target_path: Path = field(repr=False, compare=False)
    checksum: str = field(repr=False, compare=False)

    def public_dict(self) -> dict[str, Any]:
        return {
            "source_root_label": self.source_root_label,
            "target_root_label": self.target_root_label,
            "relative_path": self.relative_path,
            "target_relative_path": self.target_relative_path,
            "bytes": self.bytes,
            "checksum_status": self.checksum_status,
            "action": self.action,
        }


def resolve_roots(
    *,
    lake_root: PathLike | None = None,
    archive_root: PathLike | None = None,
    backup_root: PathLike | None = None,
    restore_root: PathLike | None = None,
    require_lake: bool = False,
    require_backup: bool = False,
    require_restore: bool = False,
) -> BackupRestoreRoots:
    """按显式参数优先、环境变量其次解析根目录。"""

    roots = BackupRestoreRoots(
        lake_root=_path_from(explicit=lake_root, env_name=LAKE_ROOT_ENV),
        archive_root=_path_from(explicit=archive_root, env_name=ARCHIVE_ROOT_ENV),
        backup_root=_path_from(explicit=backup_root, env_name=BACKUP_ROOT_ENV),
        restore_root=_path_from(explicit=restore_root, env_name=RESTORE_ROOT_ENV),
    )
    if require_lake and roots.lake_root is None:
        raise BackupRestoreError("lake_root_missing", "lake root 未配置")
    if require_backup and _backup_base_root(roots) is None:
        raise BackupRestoreError("backup_root_missing", "backup/archive root 未配置")
    if require_restore and roots.restore_root is None:
        raise BackupRestoreError("restore_root_missing", "restore root 未配置")
    if roots.lake_root is not None and roots.restore_root is not None:
        _raise_if_same_root(roots.lake_root, roots.restore_root)
    return roots


def backup_plan(request: BackupRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """生成备份计划；只读源文件，不创建备份目录。"""

    spec = _backup_request(request, **kwargs)
    roots = _roots_for_backup(spec)
    sources = _select_lake_files(spec, roots)
    target_root, target_label = _backup_target(roots, spec.release_id)
    entries = _copy_entries(
        sources,
        target_root=target_root,
        target_root_label=target_label,
        target_relative_prefix=f"{spec.release_id}/files",
        source_root_label=LAKE_ROOT_LABEL,
        execute=False,
        copied_action="would_copy",
        same_action="skip",
        fail_on_mismatch=False,
    )
    return _operation_payload("backup-plan", spec, roots, entries, ok=True, execute=False)


def backup_run(request: BackupRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """执行或 dry-run 备份；只有 execute=True 才复制文件。"""

    spec = _backup_request(request, **kwargs)
    roots = _roots_for_backup(spec)
    sources = _select_lake_files(spec, roots)
    target_root, target_label = _backup_target(roots, spec.release_id)
    entries = _copy_entries(
        sources,
        target_root=target_root,
        target_root_label=target_label,
        target_relative_prefix=f"{spec.release_id}/files",
        source_root_label=LAKE_ROOT_LABEL,
        execute=spec.execute,
        copied_action="copy" if spec.execute else "would_copy",
        same_action="skip",
        fail_on_mismatch=True,
    )
    _execute_copies(entries, execute=spec.execute, copied_status="copied")
    return _operation_payload("backup-run", spec, roots, entries, ok=True, execute=spec.execute)


def backup_verify(request: BackupRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """对比 lake 源文件与备份副本 checksum，不覆盖任何文件。"""

    spec = _backup_request(request, **kwargs)
    roots = _roots_for_backup(spec)
    sources = _select_lake_files(spec, roots)
    target_root, target_label = _backup_target(roots, spec.release_id)
    entries = _copy_entries(
        sources,
        target_root=target_root,
        target_root_label=target_label,
        target_relative_prefix=f"{spec.release_id}/files",
        source_root_label=LAKE_ROOT_LABEL,
        execute=False,
        copied_action="missing",
        same_action="verified",
        fail_on_mismatch=False,
    )
    ok = all(entry.checksum_status == "same" for entry in entries)
    return _operation_payload("backup-verify", spec, roots, entries, ok=ok, execute=False)


def backup_report(request: BackupRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """汇总某个 release 的备份内容；不读取 lake 源数据。"""

    spec = _backup_request(request, **kwargs)
    roots = resolve_roots(
        lake_root=spec.lake_root,
        archive_root=spec.archive_root,
        backup_root=spec.backup_root,
        restore_root=spec.restore_root,
        require_backup=True,
    )
    backup_root, label = _backup_target(roots, spec.release_id)
    sources = _select_backup_files(spec, backup_root)
    entries = [
        _CopyEntry(
            relative_path=item.relative_path,
            source_root_label=label,
            target_root_label=label,
            target_relative_path=f"{spec.release_id}/files/{item.relative_path}",
            bytes=item.bytes,
            checksum_status="computed",
            action="report",
            source_path=item.path,
            target_path=item.path,
            checksum=item.checksum,
        )
        for item in sources
    ]
    return _operation_payload("backup-report", spec, roots, entries, ok=True, execute=False)


def restore_plan(request: RestoreRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """生成恢复计划；只读备份，不创建恢复目录。"""

    spec = _restore_request(request, **kwargs)
    roots = _roots_for_restore(spec)
    sources = _select_backup_files(spec, _backup_target(roots, spec.release_id)[0])
    entries = _restore_entries(sources, roots, spec, execute=False, fail_on_mismatch=False)
    return _operation_payload("restore-plan", spec, roots, entries, ok=True, execute=False)


def restore_run(request: RestoreRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """执行或 dry-run 恢复；只有 execute=True 才复制到 restore root。"""

    spec = _restore_request(request, **kwargs)
    roots = _roots_for_restore(spec)
    sources = _select_backup_files(spec, _backup_target(roots, spec.release_id)[0])
    entries = _restore_entries(sources, roots, spec, execute=spec.execute, fail_on_mismatch=True)
    _execute_copies(entries, execute=spec.execute, copied_status="restored")
    return _operation_payload("restore-run", spec, roots, entries, ok=True, execute=spec.execute)


def restore_drill(request: RestoreRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """在临时 restore root 中执行恢复演练，并返回只读三段结果。"""

    spec = _restore_request(request, **kwargs)
    roots = resolve_roots(
        lake_root=spec.lake_root,
        archive_root=spec.archive_root,
        backup_root=spec.backup_root,
        restore_root=None,
        require_backup=True,
    )
    with tempfile.TemporaryDirectory(prefix="market-data-restore-drill-") as temp_dir:
        drill_spec = replace(spec, restore_root=Path(temp_dir), execute=True)
        restored = restore_run(drill_spec)
        restored_count = int(restored["summary"]["file_count"])
        restored_bytes = int(restored["summary"]["bytes"])
        read_result = {
            "status": "available" if restored_count else "empty",
            "root_label": RESTORE_ROOT_LABEL,
            "file_count": restored_count,
            "bytes": restored_bytes,
        }
        revalidate_result = {
            "status": "pass" if bool(restored["ok"]) else "fail",
            "root_label": RESTORE_ROOT_LABEL,
            "file_count": restored_count,
            "bytes": restored_bytes,
            "checksum_status": dict(restored["summary"]["checksum_status"]),
        }
    replay_result = {
        "status": "offline_planned",
        "network_calls": 0,
        "auto_execute": False,
        "root_label": RESTORE_ROOT_LABEL,
    }
    return {
        "ok": read_result["status"] == "available" and revalidate_result["status"] == "pass",
        "command": "restore-drill",
        "dry_run": False,
        "execute": True,
        "release_id": _clean_identifier(spec.release_id, "release_id"),
        "run_id": spec.run_id,
        "dataset": spec.dataset,
        "roots": roots.public_labels() | {"restore_root": RESTORE_ROOT_LABEL},
        "read": read_result,
        "revalidate": revalidate_result,
        "replay": replay_result,
        "summary": {
            "file_count": read_result["file_count"],
            "bytes": read_result["bytes"],
            "network_calls": replay_result["network_calls"],
            "auto_execute": replay_result["auto_execute"],
        },
    }


def retention_plan(request: RetentionRequest | Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """生成清理前保留策略计划。

    S16 当前只做保护判定，不执行删除：published run、candidate catalog 和
    failed / partial / orphan manifest 全部保留；任何 execute 请求都会先经过
    保护检查，存在非 eligible 对象时 fail fast。
    """

    spec = _retention_request(request, **kwargs)
    roots = resolve_roots(lake_root=spec.lake_root, require_lake=True)
    if roots.lake_root is None:
        raise BackupRestoreError("lake_root_missing", "lake root 未配置")
    layout = LakeLayout(roots.lake_root)
    rows: list[dict[str, Any]] = []
    rows.extend(_retention_catalog_rows(layout, spec))
    rows.extend(_retention_manifest_rows(layout, spec))
    if not rows:
        rows.append(
            {
                "object_type": "scope",
                "dataset": spec.dataset,
                "run_id": spec.run_id,
                "decision": "no_matching_objects",
                "cleanup_allowed": False,
                "reason": "未找到匹配 catalog 或 manifest；不会执行删除",
            }
        )
    protected = [row for row in rows if not bool(row.get("cleanup_allowed", False))]
    if spec.execute and protected:
        raise BackupRestoreError(
            "retention_protected_run",
            "保留策略发现受保护对象，已拒绝清理",
            details={
                "protected_count": len(protected),
                "decisions": sorted({str(row.get("decision")) for row in protected}),
            },
        )
    return {
        "ok": True,
        "command": "retention-plan",
        "dry_run": not spec.execute,
        "execute": spec.execute,
        "dataset": spec.dataset,
        "run_id": spec.run_id,
        "roots": roots.public_labels(),
        "summary": {
            "object_count": len(rows),
            "protected_count": len(protected),
            "cleanup_candidate_count": len(rows) - len(protected),
            "cleanup_allowed": not protected,
        },
        "rows": rows,
    }


def _backup_request(
    request: BackupRequest | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> BackupRequest:
    if request is None:
        return BackupRequest(**kwargs)
    if isinstance(request, BackupRequest):
        return replace(request, **kwargs) if kwargs else request
    return BackupRequest(**{**dict(request), **kwargs})


def _restore_request(
    request: RestoreRequest | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RestoreRequest:
    if request is None:
        return RestoreRequest(**kwargs)
    if isinstance(request, RestoreRequest):
        return replace(request, **kwargs) if kwargs else request
    return RestoreRequest(**{**dict(request), **kwargs})


def _retention_request(
    request: RetentionRequest | Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RetentionRequest:
    if request is None:
        return RetentionRequest(**kwargs)
    if isinstance(request, RetentionRequest):
        return replace(request, **kwargs) if kwargs else request
    return RetentionRequest(**{**dict(request), **kwargs})


def _path_from(*, explicit: PathLike | None, env_name: str) -> Path | None:
    if explicit is not None:
        return Path(explicit)
    env_value = os.getenv(env_name)
    return Path(env_value) if env_value else None


def _roots_for_backup(spec: BackupRequest) -> BackupRestoreRoots:
    return resolve_roots(
        lake_root=spec.lake_root,
        archive_root=spec.archive_root,
        backup_root=spec.backup_root,
        restore_root=spec.restore_root,
        require_lake=True,
        require_backup=True,
    )


def _roots_for_restore(spec: RestoreRequest) -> BackupRestoreRoots:
    return resolve_roots(
        lake_root=spec.lake_root,
        archive_root=spec.archive_root,
        backup_root=spec.backup_root,
        restore_root=spec.restore_root,
        require_lake=True,
        require_backup=True,
        require_restore=True,
    )


def _backup_base_root(roots: BackupRestoreRoots) -> Path | None:
    return roots.backup_root or roots.archive_root


def _backup_target(roots: BackupRestoreRoots, release_id: str) -> tuple[Path, str]:
    base = _backup_base_root(roots)
    if base is None:
        raise BackupRestoreError("backup_root_missing", "backup/archive root 未配置")
    label = BACKUP_ROOT_LABEL if roots.backup_root is not None else ARCHIVE_ROOT_LABEL
    return base / _clean_identifier(release_id, "release_id") / "files", label


def _raise_if_same_root(lake_root: Path, restore_root: Path) -> None:
    if _resolved(lake_root) == _resolved(restore_root):
        raise BackupRestoreError(
            "restore_root_conflict",
            "restore root 与 lake root 指向同一路径，已拒绝恢复",
            details={"lake_root": LAKE_ROOT_LABEL, "restore_root": RESTORE_ROOT_LABEL},
        )


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _clean_identifier(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise BackupRestoreError("invalid_identifier", f"{field_name} 不能为空")
    if text in {".", ".."} or "/" in text or "\\" in text or "\x00" in text:
        raise BackupRestoreError(
            "invalid_identifier",
            f"{field_name} 不能包含路径分隔符或特殊路径片段",
            details={field_name: "<redacted>"},
        )
    return text


def _selected_layers(spec: BackupRequest | RestoreRequest) -> tuple[str, ...]:
    layers: list[str] = []
    if spec.include_raw:
        layers.append("raw")
    layers.extend(ALWAYS_INCLUDED_LAYERS)
    if spec.include_canonical:
        layers.append("canonical")
    if spec.include_gold:
        layers.append("gold")
    if spec.include_quality:
        layers.append("quality")
    return tuple(dict.fromkeys(layers))


def _select_lake_files(spec: BackupRequest, roots: BackupRestoreRoots) -> list[_SourceFile]:
    if roots.lake_root is None:
        raise BackupRestoreError("lake_root_missing", "lake root 未配置")
    lake_root = roots.lake_root
    layout = LakeLayout(lake_root)
    selected_layers = _selected_layers(spec)
    raw_allowlist = _manifest_raw_allowlist(layout, spec)
    files: list[_SourceFile] = []
    for layer in selected_layers:
        layer_root = lake_root / layer
        if not layer_root.exists():
            continue
        for path in _iter_safe_files(layer_root):
            relative_path = _relative_to(path, lake_root)
            if _is_sensitive_relative(relative_path):
                continue
            if not _matches_scope(Path(relative_path), spec, raw_allowlist=raw_allowlist):
                continue
            files.append(
                _SourceFile(
                    relative_path=relative_path,
                    path=path,
                    layer=layer,
                    bytes=path.stat().st_size,
                    checksum=_sha256(path),
                )
            )
    return _dedupe_sources(files)


def _select_backup_files(spec: BackupRequest | RestoreRequest, backup_files_root: Path) -> list[_SourceFile]:
    if not backup_files_root.exists():
        return []
    files: list[_SourceFile] = []
    for path in _iter_safe_files(backup_files_root):
        relative_path = _relative_to(path, backup_files_root)
        if _is_sensitive_relative(relative_path):
            continue
        relative = Path(relative_path)
        if not _matches_scope(relative, spec, raw_allowlist=None):
            continue
        layer = relative.parts[0] if relative.parts else ""
        if layer not in _selected_layers(spec):
            continue
        files.append(
            _SourceFile(
                relative_path=relative_path,
                path=path,
                layer=layer,
                bytes=path.stat().st_size,
                checksum=_sha256(path),
            )
        )
    return _dedupe_sources(files)


def _manifest_raw_allowlist(layout: LakeLayout, spec: BackupRequest) -> set[str] | None:
    if not (spec.dataset or spec.run_id):
        return None
    manifest_root = layout.manifest_root
    if not manifest_root.exists():
        return set()
    allowed: set[str] = set()
    for manifest_path in _iter_safe_files(manifest_root):
        relative = _relative_to(manifest_path, layout.lake_root)
        if _is_sensitive_relative(relative):
            continue
        for record in _iter_manifest_records(manifest_path):
            if not _record_matches_scope(record, spec):
                continue
            raw_path = record.get("raw_path")
            if isinstance(raw_path, str):
                allowed_relative = _record_relative_path(raw_path, layout.lake_root)
                if allowed_relative is not None:
                    allowed.add(allowed_relative)
    return allowed


def _iter_manifest_records(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record
        return
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            yield payload
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield item


def _record_matches_scope(record: Mapping[str, Any], spec: BackupRequest) -> bool:
    if spec.run_id is not None and str(record.get("run_id")) != str(spec.run_id):
        return False
    if spec.dataset is None:
        return True
    dataset = record.get("dataset")
    params = record.get("params")
    if dataset is None and isinstance(params, Mapping):
        dataset = params.get("target_dataset") or params.get("dataset")
    if dataset is None:
        interface = str(record.get("interface") or "")
        dataset = interface.split(".", 1)[0] if interface else None
    return str(dataset) == str(spec.dataset)


def _retention_catalog_rows(layout: LakeLayout, spec: RetentionRequest) -> list[dict[str, Any]]:
    catalog_path = layout.catalog_root / "catalog.json"
    if not catalog_path.exists():
        return []
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [
            {
                "object_type": "catalog",
                "relative_path": "catalog/catalog.json",
                "decision": "retain_invalid_catalog_for_manual_review",
                "cleanup_allowed": False,
                "reason": "catalog JSON 不合法，禁止自动清理",
            }
        ]
    datasets = payload.get("datasets") if isinstance(payload, Mapping) else {}
    if not isinstance(datasets, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    for dataset, item in datasets.items():
        if spec.dataset is not None and str(dataset) != str(spec.dataset):
            continue
        if not isinstance(item, Mapping):
            continue
        run_id = item.get("latest_manifest_run_id")
        if spec.run_id is not None and str(run_id) != str(spec.run_id):
            continue
        published = bool(item.get("published", True))
        rows.append(
            {
                "object_type": "catalog",
                "dataset": str(dataset),
                "run_id": run_id,
                "relative_path": "catalog/catalog.json",
                "decision": "protect_published_run" if published else "retain_candidate_run",
                "cleanup_allowed": False,
                "reason": "published catalog 受保护" if published else "candidate_unpublished 需保留以便审计",
            }
        )
    return rows


def _retention_manifest_rows(layout: LakeLayout, spec: RetentionRequest) -> list[dict[str, Any]]:
    manifest_root = layout.manifest_root
    if not manifest_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for manifest_path in _iter_safe_files(manifest_root):
        relative_path = _relative_to(manifest_path, layout.lake_root)
        if _is_sensitive_relative(relative_path):
            continue
        for record in _iter_manifest_records(manifest_path):
            if not _retention_record_matches_scope(record, spec):
                continue
            status = str(record.get("status") or "unknown")
            dataset = _dataset_from_record(record)
            run_id = record.get("run_id")
            failed_like = status in {"failed", "partial_success", "circuit_open", "orphan_raw"}
            rows.append(
                {
                    "object_type": "manifest_record",
                    "dataset": dataset,
                    "run_id": run_id,
                    "status": status,
                    "relative_path": relative_path,
                    "decision": "retain_failed_or_candidate_run" if failed_like else "requires_backup_verify_before_cleanup",
                    "cleanup_allowed": False,
                    "reason": "失败或候选 run 必须保留" if failed_like else "成功 run 清理前必须先完成备份校验与人工确认",
                }
            )
    return rows


def _retention_record_matches_scope(record: Mapping[str, Any], spec: RetentionRequest) -> bool:
    if spec.run_id is not None and str(record.get("run_id")) != str(spec.run_id):
        return False
    if spec.dataset is None:
        return True
    return _dataset_from_record(record) == str(spec.dataset)


def _dataset_from_record(record: Mapping[str, Any]) -> str | None:
    dataset = record.get("dataset")
    params = record.get("params")
    if dataset is None and isinstance(params, Mapping):
        dataset = params.get("target_dataset") or params.get("dataset")
    if dataset is None:
        interface = str(record.get("interface") or "")
        dataset = interface.split(".", 1)[0] if interface else None
    return None if dataset is None else str(dataset)


def _record_relative_path(value: str, lake_root: Path) -> str | None:
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(lake_root).as_posix()
        except ValueError:
            return None
    return candidate.as_posix()


def _matches_scope(
    relative: Path,
    spec: BackupRequest | RestoreRequest,
    *,
    raw_allowlist: set[str] | None,
) -> bool:
    parts = relative.parts
    if not parts:
        return False
    layer = parts[0]
    if layer in ALWAYS_INCLUDED_LAYERS:
        return True
    if layer not in DATA_LAYERS:
        return False
    if layer == "raw":
        if raw_allowlist is not None:
            return relative.as_posix() in raw_allowlist
        if spec.run_id is not None and not _path_has_run_id(relative, spec.run_id):
            return False
        return True
    if spec.dataset is not None and not _path_has_dataset(relative, spec.dataset):
        return False
    if spec.run_id is not None and not _path_has_run_id(relative, spec.run_id):
        return False
    return True


def _path_has_dataset(relative: Path, dataset: str) -> bool:
    parts = relative.parts
    return len(parts) > 1 and parts[1] == str(dataset)


def _path_has_run_id(relative: Path, run_id: str) -> bool:
    expected = str(run_id)
    return any(part == expected or part == f"run_id={expected}" for part in relative.parts)


def _iter_safe_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            path.relative_to(root)
        except ValueError:
            continue
        yield path


def _is_sensitive_relative(relative_path: str) -> bool:
    parts = Path(relative_path).parts
    for part in parts:
        lower = part.lower()
        if lower == ".env" or lower.startswith(".env."):
            return True
        if any(marker in lower for marker in SENSITIVE_PARTS if marker != ".env"):
            return True
    return False


def _relative_to(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise BackupRestoreError(
            "path_escape",
            "文件路径不在允许的 root 内",
            details={"root_label": LAKE_ROOT_LABEL},
        ) from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dedupe_sources(files: Iterable[_SourceFile]) -> list[_SourceFile]:
    by_relative: dict[str, _SourceFile] = {}
    for item in files:
        by_relative.setdefault(item.relative_path, item)
    return [by_relative[key] for key in sorted(by_relative)]


def _copy_entries(
    sources: Iterable[_SourceFile],
    *,
    target_root: Path,
    target_root_label: str,
    target_relative_prefix: str,
    source_root_label: str,
    execute: bool,
    copied_action: str,
    same_action: str,
    fail_on_mismatch: bool,
) -> list[_CopyEntry]:
    entries: list[_CopyEntry] = []
    mismatch_paths: list[str] = []
    clean_prefix = target_relative_prefix.strip("/")
    for source in sources:
        target_path = target_root / source.relative_path
        target_relative_path = f"{clean_prefix}/{source.relative_path}" if clean_prefix else source.relative_path
        if target_path.exists():
            target_checksum = _sha256(target_path)
            if target_checksum == source.checksum:
                checksum_status = "same"
                action = same_action
            else:
                checksum_status = "mismatch"
                action = "fail"
                mismatch_paths.append(source.relative_path)
        else:
            checksum_status = "missing"
            action = copied_action if execute else copied_action
        entries.append(
            _CopyEntry(
                relative_path=source.relative_path,
                source_root_label=source_root_label,
                target_root_label=target_root_label,
                target_relative_path=target_relative_path,
                bytes=source.bytes,
                checksum_status=checksum_status,
                action=action,
                source_path=source.path,
                target_path=target_path,
                checksum=source.checksum,
            )
        )
    if fail_on_mismatch and mismatch_paths:
        raise BackupRestoreError(
            "checksum_mismatch",
            "checksum mismatch，已拒绝覆盖目标文件",
            details={"relative_paths": mismatch_paths},
        )
    return entries


def _restore_entries(
    sources: Iterable[_SourceFile],
    roots: BackupRestoreRoots,
    spec: RestoreRequest,
    *,
    execute: bool,
    fail_on_mismatch: bool,
) -> list[_CopyEntry]:
    if roots.restore_root is None:
        raise BackupRestoreError("restore_root_missing", "restore root 未配置")
    return _copy_entries(
        sources,
        target_root=roots.restore_root,
        target_root_label=RESTORE_ROOT_LABEL,
        target_relative_prefix="",
        source_root_label=BACKUP_ROOT_LABEL if roots.backup_root is not None else ARCHIVE_ROOT_LABEL,
        execute=execute,
        copied_action="restore" if execute else "would_restore",
        same_action="skip",
        fail_on_mismatch=fail_on_mismatch,
    )


def _execute_copies(entries: list[_CopyEntry], *, execute: bool, copied_status: str) -> None:
    if not execute:
        return
    for entry in entries:
        if entry.checksum_status == "same":
            continue
        ensure_parent_dirs_for_write(entry.target_path)
        shutil.copy2(entry.source_path, entry.target_path)
        if _sha256(entry.target_path) != entry.checksum:
            raise BackupRestoreError(
                "copy_checksum_mismatch",
                "复制后 checksum 校验失败",
                details={"relative_path": entry.relative_path},
            )
    for index, entry in enumerate(entries):
        if entry.checksum_status != "same":
            entries[index] = replace(entry, checksum_status="same", action=copied_status)


def _operation_payload(
    command: str,
    spec: BackupRequest | RestoreRequest,
    roots: BackupRestoreRoots,
    entries: list[_CopyEntry],
    *,
    ok: bool,
    execute: bool,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "command": command,
        "dry_run": not execute,
        "execute": execute,
        "release_id": _clean_identifier(spec.release_id, "release_id"),
        "run_id": spec.run_id,
        "dataset": spec.dataset,
        "include_layers": {
            "raw": spec.include_raw,
            "canonical": spec.include_canonical,
            "gold": spec.include_gold,
            "quality": spec.include_quality,
            "manifest": True,
            "catalog": True,
        },
        "roots": roots.public_labels(),
        "summary": _summary(entries),
        "files": [entry.public_dict() for entry in entries],
    }


def _summary(entries: list[_CopyEntry]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    actions: dict[str, int] = {}
    for entry in entries:
        statuses[entry.checksum_status] = statuses.get(entry.checksum_status, 0) + 1
        actions[entry.action] = actions.get(entry.action, 0) + 1
    return {
        "file_count": len(entries),
        "bytes": sum(entry.bytes for entry in entries),
        "checksum_status": statuses,
        "actions": actions,
    }


__all__ = [
    "ARCHIVE_ROOT_ENV",
    "BACKUP_ROOT_ENV",
    "LAKE_ROOT_ENV",
    "RESTORE_ROOT_ENV",
    "BackupRequest",
    "BackupRestoreError",
    "BackupRestoreRoots",
    "RestoreRequest",
    "RetentionRequest",
    "backup_plan",
    "backup_report",
    "backup_run",
    "backup_verify",
    "retention_plan",
    "resolve_roots",
    "restore_drill",
    "restore_plan",
    "restore_run",
]
