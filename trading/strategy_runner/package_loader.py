"""CR091 strategy package manifest / checksum 离线读取。"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from trading.strategy_runner.adapters import zero_cr091_operation_counters


CR091_MANIFEST_SCHEMA_VERSION = "cr091-strategy-runner-package-manifest-v1"
CR101_MANIFEST_SCHEMA_VERSION = "cr101-strategy-runner-package-manifest-v1"
MANIFEST_SCHEMA_VERSION = CR091_MANIFEST_SCHEMA_VERSION
SUPPORTED_MANIFEST_SCHEMA_VERSIONS = (CR091_MANIFEST_SCHEMA_VERSION, CR101_MANIFEST_SCHEMA_VERSION)
DELIVERY_TARGET_QMT_TERMINAL_DIRECT = "qmt_terminal_direct"
LEGACY_MINIQMT_RUNNER_TARGET = "miniqmt_runner"
FUTURE_DELIVERY_TARGETS = frozenset({"goldminer_future", "generic_python_future"})
EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY = "miniqmt_gateway_readonly"
READONLY_EXECUTION_CAPABILITIES = frozenset({"readonly", "health", "capabilities", "query_positions"})
ORDER_WRITE_CAPABILITIES = frozenset({"submit_order", "cancel_order", "buy", "sell", "order_write", "simulation", "live"})
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
        delivery_target = select_delivery_target(self.manifest)
        execution_adapter = select_execution_adapter(self.manifest)
        return {
            "schema_version": "cr091-strategy-package-payload-v1",
            "adapter_type": self.manifest.get("adapter_type"),
            "delivery_target_id": delivery_target.get("target_id"),
            "execution_adapter_id": execution_adapter.get("adapter_id"),
            "execution_adapter_capabilities": tuple(execution_adapter.get("capabilities", ())),
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
    schema_version = manifest.get("schema_version")
    if schema_version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
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
    if schema_version == CR101_MANIFEST_SCHEMA_VERSION:
        validate_cr101_target_adapter_contract(manifest)


def validate_cr101_target_adapter_contract(manifest: Mapping[str, Any]) -> None:
    delivery_target = select_delivery_target(manifest)
    _validate_relative_path(str(delivery_target.get("entrypoint") or ""), "blocked_delivery_target_entrypoint_missing")
    select_execution_adapter(manifest)


def select_delivery_target(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if manifest.get("schema_version") != CR101_MANIFEST_SCHEMA_VERSION:
        return {
            "target_id": str(manifest.get("delivery_target_id") or DELIVERY_TARGET_QMT_TERMINAL_DIRECT),
            "implemented": True,
            "entrypoint": str(manifest.get("entrypoint") or ""),
        }
    targets = manifest.get("delivery_targets")
    if not isinstance(targets, list) or not targets:
        raise PackageLoaderError("blocked_delivery_targets_missing")
    normalized = [_as_mapping(item, "delivery_target") for item in targets]
    for target in normalized:
        target_id = str(target.get("target_id") or "")
        if target_id == LEGACY_MINIQMT_RUNNER_TARGET:
            raise PackageLoaderError("blocked_legacy_miniqmt_runner_delivery_target")
        if target_id in FUTURE_DELIVERY_TARGETS and target.get("implemented") is True:
            raise PackageLoaderError(f"blocked_future_target_implemented:{target_id}")
    implemented = [target for target in normalized if target.get("implemented") is True]
    if len(implemented) != 1:
        raise PackageLoaderError("blocked_delivery_target_implemented_count")
    target = implemented[0]
    if target.get("target_id") != DELIVERY_TARGET_QMT_TERMINAL_DIRECT:
        raise PackageLoaderError("blocked_delivery_target_not_qmt_terminal_direct")
    return target


def select_execution_adapter(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if manifest.get("schema_version") != CR101_MANIFEST_SCHEMA_VERSION:
        return {
            "adapter_id": str(manifest.get("execution_adapter_id") or EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY),
            "capabilities": ("readonly",),
        }
    adapters = manifest.get("execution_adapters")
    if not isinstance(adapters, list) or not adapters:
        raise PackageLoaderError("blocked_execution_adapters_missing")
    normalized = [_as_mapping(item, "execution_adapter") for item in adapters]
    for adapter in normalized:
        capabilities = tuple(str(item) for item in _as_list(adapter.get("capabilities")))
        if any(capability in ORDER_WRITE_CAPABILITIES for capability in capabilities):
            raise PackageLoaderError("blocked_execution_adapter_order_write_capability")
        if any(capability not in READONLY_EXECUTION_CAPABILITIES for capability in capabilities):
            raise PackageLoaderError("blocked_execution_adapter_unknown_capability")
    for adapter in normalized:
        if adapter.get("adapter_id") == EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY:
            capabilities = set(str(item) for item in _as_list(adapter.get("capabilities")))
            if not capabilities or not capabilities <= READONLY_EXECUTION_CAPABILITIES:
                raise PackageLoaderError("blocked_execution_adapter_capabilities_invalid")
            return adapter
    raise PackageLoaderError("blocked_execution_adapter_missing:miniqmt_gateway_readonly")


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
    _validate_relative_path(rel_path, "blocked_path_escape")
    path = (root / rel_path).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise PackageLoaderError("blocked_path_escape")
    return path


def _validate_relative_path(rel_path: str, missing_code: str) -> None:
    if not rel_path:
        raise PackageLoaderError(missing_code)
    if rel_path.startswith("/") or ".." in Path(rel_path).parts:
        raise PackageLoaderError("blocked_path_escape")


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PackageLoaderError(f"blocked_{label}_not_mapping")
    return value


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
