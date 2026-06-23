"""Offline strategy runner input contract."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import yaml


RUN_SPEC_SCHEMA_VERSION = "cr128-run-spec-v1"
OFFLINE_MODE = "offline"
SENSITIVE_PATH_PARTS = frozenset({".env", "token", "secret", "credential", "credentials"})
RUN_SPEC_BOOL_FIELDS = frozenset(
    {
        "include_fake_readonly",
        "runtime_authorized",
        "nas_operation_authorized",
        "credential_read_authorized",
        "account_query_authorized",
        "trade_write_authorized",
        "provider_lake_catalog_authorized",
        "qmt_allowed",
        "not_authorization",
    }
)
RUN_SPEC_ALLOWED_FIELDS = frozenset(
    {
        "schema_version",
        "package_root",
        "run_id",
        "output_path",
        "mode",
        *RUN_SPEC_BOOL_FIELDS,
    }
)


class RunSpecError(ValueError):
    """RunSpec 不满足 offline runner 边界。"""


@dataclass(frozen=True, slots=True)
class RunSpec:
    package_root: Path
    run_id: str
    output_path: Path | None = None
    mode: str = OFFLINE_MODE
    include_fake_readonly: bool = True
    runtime_authorized: bool = False
    nas_operation_authorized: bool = False
    credential_read_authorized: bool = False
    account_query_authorized: bool = False
    trade_write_authorized: bool = False
    provider_lake_catalog_authorized: bool = False
    qmt_allowed: bool = False
    not_authorization: bool = True
    schema_version: str = RUN_SPEC_SCHEMA_VERSION

    @classmethod
    def from_package_root(
        cls,
        package_root: str | Path,
        *,
        run_id: str,
        output_path: str | Path | None = None,
    ) -> "RunSpec":
        return cls(
            package_root=Path(package_root),
            run_id=run_id,
            output_path=None if output_path is None else Path(output_path),
        )

    @classmethod
    def from_file(cls, spec_path: str | Path) -> "RunSpec":
        path = Path(spec_path)
        payload = _load_spec_mapping(path)
        return cls.from_mapping(payload, base_dir=path.parent)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any], *, base_dir: Path | None = None) -> "RunSpec":
        unknown_fields = sorted(set(payload).difference(RUN_SPEC_ALLOWED_FIELDS))
        if unknown_fields:
            raise RunSpecError("blocked_run_spec_unknown_fields:" + ",".join(unknown_fields))
        for field_name in RUN_SPEC_BOOL_FIELDS:
            if field_name in payload and not isinstance(payload[field_name], bool):
                raise RunSpecError(f"blocked_run_spec_bool_field_invalid:{field_name}")
        package_root = payload.get("package_root")
        if not isinstance(package_root, str) or not package_root.strip():
            raise RunSpecError("blocked_package_root_missing")
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id.strip():
            raise RunSpecError("blocked_run_id_missing")
        output_path = payload.get("output_path")
        if output_path is not None and not isinstance(output_path, str):
            raise RunSpecError("blocked_output_path_invalid")
        spec = cls(
            package_root=_resolve_spec_path(package_root, base_dir),
            run_id=run_id,
            output_path=None if output_path is None else _resolve_spec_path(output_path, base_dir),
            mode=str(payload.get("mode", OFFLINE_MODE)),
            include_fake_readonly=payload.get("include_fake_readonly", True),
            runtime_authorized=payload.get("runtime_authorized", False),
            nas_operation_authorized=payload.get("nas_operation_authorized", False),
            credential_read_authorized=payload.get("credential_read_authorized", False),
            account_query_authorized=payload.get("account_query_authorized", False),
            trade_write_authorized=payload.get("trade_write_authorized", False),
            provider_lake_catalog_authorized=payload.get("provider_lake_catalog_authorized", False),
            qmt_allowed=payload.get("qmt_allowed", False),
            not_authorization=payload.get("not_authorization", True),
            schema_version=str(payload.get("schema_version", RUN_SPEC_SCHEMA_VERSION)),
        )
        spec.validate()
        return spec

    def validate(self) -> None:
        if self.schema_version != RUN_SPEC_SCHEMA_VERSION:
            raise RunSpecError("blocked_run_spec_schema_mismatch")
        if self.mode != OFFLINE_MODE:
            raise RunSpecError("blocked_non_offline_mode")
        if not self.run_id.strip():
            raise RunSpecError("blocked_run_id_missing")
        if self.not_authorization is not True:
            raise RunSpecError("blocked_not_authorization_missing")
        if self.qmt_allowed is not False:
            raise RunSpecError("blocked_qmt_allowed_true")
        for field_name in (
            "runtime_authorized",
            "nas_operation_authorized",
            "credential_read_authorized",
            "account_query_authorized",
            "trade_write_authorized",
            "provider_lake_catalog_authorized",
        ):
            if getattr(self, field_name) is not False:
                raise RunSpecError(f"blocked_authorization_flag_true:{field_name}")
        _validate_runner_path(self.package_root, "blocked_package_root_sensitive")
        if self.output_path is not None:
            _validate_runner_path(self.output_path, "blocked_output_path_sensitive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "package_root": self.package_root.as_posix(),
            "run_id": self.run_id,
            "output_path": None if self.output_path is None else self.output_path.as_posix(),
            "mode": self.mode,
            "include_fake_readonly": self.include_fake_readonly,
            "runtime_authorized": self.runtime_authorized,
            "nas_operation_authorized": self.nas_operation_authorized,
            "credential_read_authorized": self.credential_read_authorized,
            "account_query_authorized": self.account_query_authorized,
            "trade_write_authorized": self.trade_write_authorized,
            "provider_lake_catalog_authorized": self.provider_lake_catalog_authorized,
            "qmt_allowed": self.qmt_allowed,
            "not_authorization": self.not_authorization,
        }


def _validate_runner_path(path: Path, error_code: str) -> None:
    parts = {part.lower() for part in path.parts}
    if parts.intersection(SENSITIVE_PATH_PARTS):
        raise RunSpecError(error_code)


def _load_spec_mapping(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RunSpecError("blocked_run_spec_file_missing")
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise RunSpecError("blocked_run_spec_file_type")
    if not isinstance(payload, dict):
        raise RunSpecError("blocked_run_spec_not_mapping")
    return payload


def _resolve_spec_path(raw_path: str, base_dir: Path | None) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or base_dir is None:
        return path
    return base_dir / path
