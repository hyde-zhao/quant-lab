"""CR091 strategy package manifest / checksum 离线读取。"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from trading.strategy_runner.adapters import zero_cr091_operation_counters


MANIFEST_SCHEMA_VERSION = "cr091-strategy-runner-package-manifest-v1"
REQUIRED_FALSE_FLAGS = (
    "runtime_authorized",
    "nas_operation_authorized",
    "credential_read_authorized",
    "account_query_authorized",
    "trade_write_authorized",
)


class PackageLoaderError(ValueError):
    """package intake fail-closed 错误。"""


@dataclass(frozen=True, slots=True)
class StrategyPackage:
    package_root: Path
    manifest: Mapping[str, Any]
    payload: Mapping[str, Any]
    checksum_errors: tuple[str, ...] = ()
    operation_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)

    @property
    def package_id(self) -> str:
        return str(self.manifest.get("package_id", ""))

    def to_adapter_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "cr091-strategy-package-payload-v1",
            "adapter_type": self.manifest.get("adapter_type"),
            "manifest_checksum_verified": not self.checksum_errors,
            "runtime_authorized": self.manifest.get("runtime_authorized"),
            "nas_operation_authorized": self.manifest.get("nas_operation_authorized"),
            "credential_read_authorized": self.manifest.get("credential_read_authorized"),
            "account_query_authorized": self.manifest.get("account_query_authorized"),
            "trade_write_authorized": self.manifest.get("trade_write_authorized"),
            "not_authorization": True,
            "strategy_payload": dict(self.payload),
        }


def load_strategy_package(package_root: str | Path) -> StrategyPackage:
    root = Path(package_root)
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        raise PackageLoaderError("blocked_manifest_missing")
    manifest = _as_mapping(_load_yaml(manifest_path), "manifest")
    validate_manifest(manifest)
    checksum_errors = verify_checksums(root, manifest)
    if checksum_errors:
        raise PackageLoaderError("blocked_checksum_mismatch:" + ",".join(checksum_errors))
    payload_rel = str(manifest.get("payload_path") or "")
    if not payload_rel:
        raise PackageLoaderError("blocked_payload_path_missing")
    payload_path = _resolve_under(root, payload_rel)
    payload = _as_mapping(_load_json(payload_path), "payload")
    return StrategyPackage(root, manifest, payload, checksum_errors=())


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise PackageLoaderError("blocked_schema_mismatch")
    if not manifest.get("package_id"):
        raise PackageLoaderError("blocked_package_id_missing")
    if not manifest.get("adapter_type"):
        raise PackageLoaderError("blocked_adapter_type_missing")
    if not manifest.get("payload_path"):
        raise PackageLoaderError("blocked_payload_path_missing")
    if manifest.get("not_authorization") is not True:
        raise PackageLoaderError("blocked_not_authorization_missing")
    for flag in REQUIRED_FALSE_FLAGS:
        if manifest.get(flag) is not False:
            raise PackageLoaderError(f"blocked_manifest_flag_nonfalse:{flag}")
    forbidden = manifest.get("forbidden_operations")
    if not isinstance(forbidden, dict) or any(int(value or 0) != 0 for value in forbidden.values()):
        raise PackageLoaderError("blocked_forbidden_operation_nonzero")


def verify_checksums(package_root: Path, manifest: Mapping[str, Any]) -> tuple[str, ...]:
    checksums = manifest.get("checksums")
    if not isinstance(checksums, Mapping) or not checksums:
        return ("checksums_missing",)
    errors: list[str] = []
    payload_path = str(manifest.get("payload_path") or "")
    if payload_path not in {str(path) for path in checksums}:
        errors.append(f"{payload_path or 'payload_path'}:checksum_missing")
    for rel_path, expected in checksums.items():
        path = _resolve_under(package_root, str(rel_path))
        if not path.is_file():
            errors.append(f"{rel_path}:missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != str(expected):
            errors.append(f"{rel_path}:sha256_mismatch")
    return tuple(errors)


def _resolve_under(root: Path, rel_path: str) -> Path:
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        raise PackageLoaderError("blocked_path_escape")
    path = (root / rel_path).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise PackageLoaderError("blocked_path_escape")
    return path


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PackageLoaderError(f"blocked_{label}_not_mapping")
    return value
