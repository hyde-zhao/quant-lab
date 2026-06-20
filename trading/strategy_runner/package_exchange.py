"""CR100 本地 fake package exchange 合同。

本模块只实现离线 readiness：所有 publish / pull 都要求 exchange root
包含本地 fake marker。没有 marker 时立即 fail closed，避免误触真实 NAS。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Mapping

import yaml

from trading.strategy_runner.package_loader import (
    CR101_MANIFEST_SCHEMA_VERSION,
    DELIVERY_TARGET_QMT_TERMINAL_DIRECT,
    EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY,
    PackageLoaderError,
    select_delivery_target,
    validate_manifest as validate_runner_manifest,
)

EXCHANGE_SCHEMA_VERSION = "cr100-package-exchange-v1"
CR100_MANIFEST_SCHEMA_VERSION = "cr100-strategy-package-manifest-v1"
MANIFEST_SCHEMA_VERSION = CR100_MANIFEST_SCHEMA_VERSION
SUPPORTED_MANIFEST_SCHEMA_VERSIONS = (CR100_MANIFEST_SCHEMA_VERSION, CR101_MANIFEST_SCHEMA_VERSION)
FAKE_EXCHANGE_MARKER = ".cr100_fake_exchange_root"
INDEX_FILE_NAME = "index.yaml"
ACTIVE_POINTER_NAME = "active.json"
REQUIRED_PERMISSION_FALSE_FLAGS = (
    "runtime",
    "submit_cancel",
    "simulation_live",
    "credential_read",
    "nas_read",
    "nas_write",
)
FORBIDDEN_FILE_NAMES = {".env", ".env.local", ".env.production"}
FORBIDDEN_NAME_FRAGMENTS = (
    "secret",
    "credential",
    "token",
    "account",
    "raw_order",
    "raw_orders",
    "raw_position",
    "raw_positions",
    "qmt_log",
)


class PackageExchangeError(ValueError):
    """CR100 exchange fail-closed 错误。"""


@dataclass(frozen=True, slots=True)
class PackageIdentity:
    package_id: str
    package_version: str

    @property
    def cache_key(self) -> str:
        return f"{self.package_id}-{self.package_version}"


@dataclass(frozen=True, slots=True)
class PackageValidation:
    identity: PackageIdentity
    manifest: Mapping[str, Any]
    checked_files: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExchangeOperationResult:
    operation: str
    passed: bool
    package_id: str = ""
    package_version: str = ""
    exchange_root: str = ""
    cache_root: str = ""
    active_pointer: str = ""
    checked_files: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    not_authorization: bool = True
    real_nas_operations: bool = False
    forbidden_operation_counters: Mapping[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EXCHANGE_SCHEMA_VERSION,
            "operation": self.operation,
            "passed": self.passed,
            "package_id": self.package_id,
            "package_version": self.package_version,
            "exchange_root": self.exchange_root,
            "cache_root": self.cache_root,
            "active_pointer": self.active_pointer,
            "checked_files": list(self.checked_files),
            "errors": list(self.errors),
            "not_authorization": self.not_authorization,
            "real_nas_operations": self.real_nas_operations,
            "forbidden_operation_counters": dict(self.forbidden_operation_counters),
        }


def create_fake_exchange_root(exchange_root: str | Path) -> Path:
    root = Path(exchange_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / FAKE_EXCHANGE_MARKER).write_text(
        "CR100 local fake exchange root. Not a NAS mount.\n",
        encoding="utf-8",
    )
    (root / "packages").mkdir(exist_ok=True)
    if not (root / INDEX_FILE_NAME).exists():
        _write_yaml(root / INDEX_FILE_NAME, _empty_index())
    return root


def validate_package(package_root: str | Path) -> PackageValidation:
    root = Path(package_root).resolve()
    if not root.is_dir():
        raise PackageExchangeError("blocked_package_root_missing")
    _reject_symlinks(root)
    _reject_forbidden_file_names(root)
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise PackageExchangeError("blocked_manifest_missing")
    manifest = _as_mapping(_load_yaml(manifest_path), "manifest")
    _validate_manifest_shape(root, manifest)
    checked_files = _verify_manifest_hashes(root, manifest)
    return PackageValidation(
        identity=PackageIdentity(
            package_id=str(manifest["package_id"]),
            package_version=str(manifest["package_version"]),
        ),
        manifest=manifest,
        checked_files=checked_files,
    )


def fake_publish_package(package_root: str | Path, exchange_root: str | Path) -> ExchangeOperationResult:
    try:
        root = _require_fake_exchange_root(exchange_root)
        validation = validate_package(package_root)
        package_target = root / "packages" / validation.identity.package_id / validation.identity.package_version
        if package_target.exists():
            raise PackageExchangeError("blocked_package_version_already_exists")
        _copy_tree_immutable(Path(package_root).resolve(), package_target)
        copied = validate_package(package_target)
        index = _load_index(root)
        packages = list(index.get("packages", []))
        packages.append(
            {
                "package_id": copied.identity.package_id,
                "package_version": copied.identity.package_version,
                "status": "approved",
                "package_path": _relative_posix(root, package_target),
                "checked_files": list(copied.checked_files),
                "not_authorization": True,
            }
        )
        index["packages"] = packages
        _write_yaml(root / INDEX_FILE_NAME, index)
        return ExchangeOperationResult(
            operation="fake_publish",
            passed=True,
            package_id=copied.identity.package_id,
            package_version=copied.identity.package_version,
            exchange_root=str(root),
            checked_files=copied.checked_files,
            forbidden_operation_counters=_zero_forbidden_operation_counters(),
        )
    except Exception as exc:
        return _failed_result("fake_publish", Path(exchange_root).resolve(), exc)


def fake_pull_package(
    exchange_root: str | Path,
    cache_root: str | Path,
    package_id: str,
    package_version: str,
) -> ExchangeOperationResult:
    cache = Path(cache_root).resolve()
    try:
        root = _require_fake_exchange_root(exchange_root)
        package_entry = _find_index_entry(root, package_id, package_version)
        if package_entry.get("status") != "approved":
            raise PackageExchangeError("blocked_package_not_approved")
        source = _resolve_under(root, str(package_entry.get("package_path") or ""))
        validation = validate_package(source)
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / "immutable" / validation.identity.cache_key
        if target.exists():
            raise PackageExchangeError("blocked_cache_package_already_exists")
        _copy_tree_immutable(source, target)
        copied = validate_package(target)
        active_pointer = cache / ACTIVE_POINTER_NAME
        _write_json(
            active_pointer,
            {
                "schema_version": EXCHANGE_SCHEMA_VERSION,
                "package_id": copied.identity.package_id,
                "package_version": copied.identity.package_version,
                "package_path": _relative_posix(cache, target),
                "not_authorization": True,
                "source": "cr100-local-fake-exchange",
            },
        )
        return ExchangeOperationResult(
            operation="fake_pull",
            passed=True,
            package_id=copied.identity.package_id,
            package_version=copied.identity.package_version,
            exchange_root=str(root),
            cache_root=str(cache),
            active_pointer=str(active_pointer),
            checked_files=copied.checked_files,
            forbidden_operation_counters=_zero_forbidden_operation_counters(),
        )
    except Exception as exc:
        return _failed_result("fake_pull", Path(exchange_root).resolve(), exc, cache_root=cache)


def check_exchange(exchange_root: str | Path) -> ExchangeOperationResult:
    try:
        root = _require_fake_exchange_root(exchange_root)
        index = _load_index(root)
        checked: list[str] = []
        for entry in index.get("packages", []):
            if not isinstance(entry, dict):
                raise PackageExchangeError("blocked_index_entry_not_mapping")
            source = _resolve_under(root, str(entry.get("package_path") or ""))
            validation = validate_package(source)
            checked.extend(validation.checked_files)
        return ExchangeOperationResult(
            operation="check_exchange",
            passed=True,
            exchange_root=str(root),
            checked_files=tuple(sorted(set(checked))),
            forbidden_operation_counters=_zero_forbidden_operation_counters(),
        )
    except Exception as exc:
        return _failed_result("check_exchange", Path(exchange_root).resolve(), exc)


def _validate_manifest_shape(root: Path, manifest: Mapping[str, Any]) -> None:
    schema_version = manifest.get("schema_version")
    if schema_version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
        raise PackageExchangeError("blocked_schema_mismatch")
    for key in ("package_id", "package_version", "created_at"):
        if not str(manifest.get(key) or ""):
            raise PackageExchangeError(f"blocked_{key}_missing")
    if schema_version == CR101_MANIFEST_SCHEMA_VERSION:
        _validate_cr101_manifest_shape(root, manifest)
    else:
        _validate_cr100_manifest_shape(root, manifest)
    approval = _as_mapping(manifest.get("approval"), "approval")
    if approval.get("status") != "approved":
        raise PackageExchangeError("blocked_approval_not_approved")
    permissions = _as_mapping(manifest.get("permissions"), "permissions")
    for flag in REQUIRED_PERMISSION_FALSE_FLAGS:
        if permissions.get(flag) is not False:
            raise PackageExchangeError(f"blocked_permission_nonfalse:{flag}")
    forbidden = manifest.get("forbidden_operation_counters")
    if isinstance(forbidden, Mapping) and any(int(value or 0) != 0 for value in forbidden.values()):
        raise PackageExchangeError("blocked_forbidden_operation_nonzero")
    hashes = manifest.get("hashes")
    if not isinstance(hashes, Mapping) or not hashes:
        raise PackageExchangeError("blocked_hashes_missing")


def _validate_cr100_manifest_shape(root: Path, manifest: Mapping[str, Any]) -> None:
    target_platforms = manifest.get("target_platforms")
    if not isinstance(target_platforms, list) or not {"qmt_terminal", "miniqmt_runner"}.issubset(
        set(target_platforms)
    ):
        raise PackageExchangeError("blocked_target_platforms_incomplete")
    entrypoints = _as_mapping(manifest.get("entrypoints"), "entrypoints")
    for target in ("qmt_terminal", "miniqmt_runner"):
        entrypoint = str(entrypoints.get(target) or "")
        if not entrypoint:
            raise PackageExchangeError(f"blocked_entrypoint_missing:{target}")
        _require_file_under(root, entrypoint)


def _validate_cr101_manifest_shape(root: Path, manifest: Mapping[str, Any]) -> None:
    try:
        validate_runner_manifest(manifest)
    except PackageLoaderError as exc:
        raise PackageExchangeError(str(exc)) from exc
    delivery_target = select_delivery_target(manifest)
    if delivery_target.get("target_id") != DELIVERY_TARGET_QMT_TERMINAL_DIRECT:
        raise PackageExchangeError("blocked_delivery_target_not_qmt_terminal_direct")
    _require_file_under(root, str(delivery_target.get("entrypoint") or ""))
    adapters = manifest.get("execution_adapters")
    if not isinstance(adapters, list) or not any(
        isinstance(adapter, Mapping) and adapter.get("adapter_id") == EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY
        for adapter in adapters
    ):
        raise PackageExchangeError("blocked_execution_adapter_missing:miniqmt_gateway_readonly")


def _verify_manifest_hashes(root: Path, manifest: Mapping[str, Any]) -> tuple[str, ...]:
    checked: list[str] = []
    hashes = _as_mapping(manifest.get("hashes"), "hashes")
    for rel_path, expected_value in sorted(hashes.items()):
        expected = str(expected_value)
        if not expected.startswith("sha256:"):
            raise PackageExchangeError(f"blocked_hash_format:{rel_path}")
        path = _require_file_under(root, str(rel_path))
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise PackageExchangeError(f"blocked_sha256_mismatch:{rel_path}")
        checked.append(str(rel_path))
    return tuple(checked)


def _require_fake_exchange_root(exchange_root: str | Path) -> Path:
    root = Path(exchange_root).resolve()
    if not root.is_dir():
        raise PackageExchangeError("blocked_exchange_root_missing")
    if not (root / FAKE_EXCHANGE_MARKER).is_file():
        raise PackageExchangeError("blocked_exchange_root_not_fake")
    return root


def _empty_index() -> dict[str, Any]:
    return {
        "schema_version": EXCHANGE_SCHEMA_VERSION,
        "exchange_type": "local_fake_only",
        "not_authorization": True,
        "packages": [],
    }


def _load_index(root: Path) -> dict[str, Any]:
    path = root / INDEX_FILE_NAME
    if not path.is_file():
        raise PackageExchangeError("blocked_index_missing")
    index = _as_mapping(_load_yaml(path), "index")
    if index.get("schema_version") != EXCHANGE_SCHEMA_VERSION:
        raise PackageExchangeError("blocked_index_schema_mismatch")
    if index.get("exchange_type") != "local_fake_only":
        raise PackageExchangeError("blocked_index_not_local_fake")
    if index.get("not_authorization") is not True:
        raise PackageExchangeError("blocked_index_not_authorization_missing")
    if not isinstance(index.get("packages"), list):
        raise PackageExchangeError("blocked_index_packages_not_list")
    return index


def _find_index_entry(root: Path, package_id: str, package_version: str) -> Mapping[str, Any]:
    index = _load_index(root)
    for entry in index["packages"]:
        if (
            isinstance(entry, dict)
            and entry.get("package_id") == package_id
            and entry.get("package_version") == package_version
        ):
            return entry
    raise PackageExchangeError("blocked_package_not_in_index")


def _copy_tree_immutable(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    _reject_symlinks(target)
    (target / ".immutable").write_text("immutable local fake package copy\n", encoding="utf-8")


def _reject_symlinks(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink():
            raise PackageExchangeError("blocked_symlink_in_package")


def _reject_forbidden_file_names(root: Path) -> None:
    for path in root.rglob("*"):
        lowered = path.name.lower()
        if lowered in FORBIDDEN_FILE_NAMES:
            raise PackageExchangeError("blocked_forbidden_file_name")
        if any(fragment in lowered for fragment in FORBIDDEN_NAME_FRAGMENTS):
            raise PackageExchangeError("blocked_forbidden_file_name")


def _require_file_under(root: Path, rel_path: str) -> Path:
    path = _resolve_under(root, rel_path)
    if not path.is_file():
        raise PackageExchangeError(f"blocked_file_missing:{rel_path}")
    return path


def _resolve_under(root: Path, rel_path: str) -> Path:
    relative = Path(rel_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise PackageExchangeError("blocked_path_escape")
    path = (root / relative).resolve()
    root_resolved = root.resolve()
    if root_resolved not in path.parents and path != root_resolved:
        raise PackageExchangeError("blocked_path_escape")
    return path


def _relative_posix(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(yaml.safe_dump(dict(value), allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PackageExchangeError(f"blocked_{label}_not_mapping")
    return value


def _zero_forbidden_operation_counters() -> dict[str, int]:
    return {
        "nas_access": 0,
        "nas_read": 0,
        "nas_write": 0,
        "nas_publish": 0,
        "nas_pull": 0,
        "credential_read": 0,
        "runtime_start": 0,
        "trade_write": 0,
        "provider_lake_publish": 0,
    }


def _failed_result(
    operation: str,
    exchange_root: Path,
    exc: Exception,
    *,
    cache_root: Path | None = None,
) -> ExchangeOperationResult:
    return ExchangeOperationResult(
        operation=operation,
        passed=False,
        exchange_root=str(exchange_root),
        cache_root="" if cache_root is None else str(cache_root),
        errors=(str(exc),),
        forbidden_operation_counters=_zero_forbidden_operation_counters(),
    )
