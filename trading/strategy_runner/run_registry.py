"""Offline runner run registry contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from trading.strategy_runner.artifact_bundle import (
    RUN_ARTIFACT_MANIFEST_BUNDLE_NAME,
    validate_run_artifact_bundle,
)
from trading.strategy_runner.evidence import assert_redacted
from trading.strategy_runner.result import RunResult


RUN_REGISTRY_SCHEMA_VERSION = "cr137-run-registry-v1"
RUN_REGISTRY_ENTRY_SCHEMA_VERSION = "cr137-run-registry-entry-v1"
SENSITIVE_PATH_PARTS = frozenset({".env", "token", "secret", "credential", "credentials"})


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class RunRegistryEntry:
    run_id: str
    status: str
    passed: bool
    package_id: str
    bundle_path: str = ""
    manifest_sha256: str = ""
    blocked_reasons: tuple[str, ...] = ()
    forbidden_operation_counters: Mapping[str, int] = field(default_factory=dict)
    qmt_allowed: bool = False
    not_authorization: bool = True
    created_at: str = field(default_factory=_utc_now)
    schema_version: str = RUN_REGISTRY_ENTRY_SCHEMA_VERSION

    @classmethod
    def from_bundle(cls, bundle_dir: str | Path) -> "RunRegistryEntry":
        bundle_path = Path(bundle_dir)
        _validate_registry_path(bundle_path, "blocked_run_registry_bundle_path_sensitive")
        manifest = validate_run_artifact_bundle(bundle_path)
        return cls(
            run_id=str(manifest["run_id"]),
            status=str(manifest["status"]),
            passed=bool(manifest["passed"]),
            package_id=str(manifest["package_id"]),
            bundle_path=bundle_path.as_posix(),
            manifest_sha256=_sha256_file(bundle_path / RUN_ARTIFACT_MANIFEST_BUNDLE_NAME),
            forbidden_operation_counters=dict(manifest.get("forbidden_operation_counters") or {}),
            qmt_allowed=bool(manifest.get("qmt_allowed", False)),
            not_authorization=bool(manifest.get("not_authorization", True)),
        )

    @classmethod
    def from_blocked_result(cls, result: RunResult) -> "RunRegistryEntry":
        if result.passed:
            raise ValueError("blocked_run_registry_diagnostic_requires_blocked_result")
        return cls(
            run_id=result.run_id,
            status=result.status,
            passed=False,
            package_id=result.package_id,
            blocked_reasons=tuple(result.blocked_reasons),
            forbidden_operation_counters=dict(result.forbidden_operation_counters),
            qmt_allowed=result.qmt_allowed,
            not_authorization=result.not_authorization,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RunRegistryEntry":
        if payload.get("schema_version") != RUN_REGISTRY_ENTRY_SCHEMA_VERSION:
            raise ValueError("blocked_run_registry_entry_schema_mismatch")
        return cls(
            run_id=str(payload.get("run_id") or ""),
            status=str(payload.get("status") or ""),
            passed=bool(payload.get("passed", False)),
            package_id=str(payload.get("package_id") or ""),
            bundle_path=str(payload.get("bundle_path") or ""),
            manifest_sha256=str(payload.get("manifest_sha256") or ""),
            blocked_reasons=tuple(str(item) for item in payload.get("blocked_reasons") or ()),
            forbidden_operation_counters={
                str(key): int(value or 0)
                for key, value in dict(payload.get("forbidden_operation_counters") or {}).items()
            },
            qmt_allowed=bool(payload.get("qmt_allowed", False)),
            not_authorization=bool(payload.get("not_authorization", True)),
            created_at=str(payload.get("created_at") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "run_id": self.run_id,
            "status": self.status,
            "passed": self.passed,
            "package_id": self.package_id,
            "bundle_path": self.bundle_path,
            "manifest_sha256": self.manifest_sha256,
            "blocked_reasons": list(self.blocked_reasons),
            "forbidden_operation_counters": dict(self.forbidden_operation_counters),
            "qmt_allowed": self.qmt_allowed,
            "not_authorization": self.not_authorization,
        }


def append_run_registry_entry(path: str | Path, entry: RunRegistryEntry) -> dict[str, Any]:
    _validate_entry(entry)
    registry_path = Path(path)
    _validate_registry_path(registry_path, "blocked_run_registry_path_sensitive")
    payload = _read_registry_payload(registry_path)
    entries = list(payload["entries"])
    entries.append(entry.to_dict())
    now = _utc_now()
    payload = {
        "schema_version": RUN_REGISTRY_SCHEMA_VERSION,
        "created_at": payload.get("created_at") or now,
        "updated_at": now,
        "entry_count": len(entries),
        "not_authorization": True,
        "qmt_allowed": False,
        "entries": entries,
    }
    assert_redacted(payload)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def append_run_registry_from_bundle(path: str | Path, bundle_dir: str | Path) -> dict[str, Any]:
    return append_run_registry_entry(path, RunRegistryEntry.from_bundle(bundle_dir))


def append_run_registry_from_result(
    path: str | Path,
    result: RunResult,
    *,
    bundle_dir: str | Path | None = None,
) -> dict[str, Any]:
    if result.passed:
        if bundle_dir is None:
            raise ValueError("blocked_run_registry_pass_entry_requires_bundle")
        return append_run_registry_from_bundle(path, bundle_dir)
    return append_run_registry_entry(path, RunRegistryEntry.from_blocked_result(result))


def read_run_registry(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    _validate_registry_path(registry_path, "blocked_run_registry_path_sensitive")
    payload = _read_registry_payload(registry_path)
    return {
        "schema_version": payload["schema_version"],
        "created_at": payload.get("created_at", ""),
        "updated_at": payload.get("updated_at", ""),
        "entry_count": len(payload["entries"]),
        "not_authorization": True,
        "qmt_allowed": False,
        "entries": payload["entries"],
    }


def inspect_run_registry_entry(path: str | Path, run_id: str) -> dict[str, Any]:
    matches = [entry for entry in read_run_registry(path)["entries"] if entry.get("run_id") == run_id]
    if not matches:
        raise ValueError("blocked_run_registry_entry_missing:" + run_id)
    return dict(matches[-1])


def _read_registry_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_registry_payload()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("blocked_run_registry_not_mapping")
    if payload.get("schema_version") != RUN_REGISTRY_SCHEMA_VERSION:
        raise ValueError("blocked_run_registry_schema_mismatch")
    if payload.get("not_authorization") is not True or payload.get("qmt_allowed") is not False:
        raise ValueError("blocked_run_registry_authorization_boundary")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("blocked_run_registry_entries_not_list")
    normalized_entries = [RunRegistryEntry.from_dict(entry).to_dict() for entry in entries]
    return {
        **payload,
        "entries": normalized_entries,
    }


def _empty_registry_payload() -> dict[str, Any]:
    return {
        "schema_version": RUN_REGISTRY_SCHEMA_VERSION,
        "created_at": "",
        "updated_at": "",
        "entry_count": 0,
        "not_authorization": True,
        "qmt_allowed": False,
        "entries": [],
    }


def _validate_entry(entry: RunRegistryEntry) -> None:
    if not entry.run_id.strip():
        raise ValueError("blocked_run_registry_run_id_missing")
    if entry.not_authorization is not True or entry.qmt_allowed is not False:
        raise ValueError("blocked_run_registry_entry_authorization_boundary")
    if any(value != 0 for value in entry.forbidden_operation_counters.values()):
        raise ValueError("blocked_run_registry_entry_forbidden_operations")
    if entry.passed:
        if entry.status != "pass":
            raise ValueError("blocked_run_registry_pass_status_mismatch")
        if not entry.bundle_path or not entry.manifest_sha256:
            raise ValueError("blocked_run_registry_pass_entry_requires_bundle")
    elif entry.bundle_path or entry.manifest_sha256:
        raise ValueError("blocked_run_registry_blocked_entry_must_not_link_pass_bundle")
    assert_redacted(entry.to_dict())


def _validate_registry_path(path: Path, error_code: str) -> None:
    parts = {part.lower() for part in path.parts}
    if parts.intersection(SENSITIVE_PATH_PARTS):
        raise ValueError(error_code)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
