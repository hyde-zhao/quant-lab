"""Offline strategy runner input contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_SPEC_SCHEMA_VERSION = "cr128-run-spec-v1"
OFFLINE_MODE = "offline"
SENSITIVE_PATH_PARTS = frozenset({".env", "token", "secret", "credential", "credentials"})


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
