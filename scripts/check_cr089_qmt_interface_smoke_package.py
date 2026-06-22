from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml


REQUIRED_FILES = (
    "manifest.yaml",
    "README.md",
    "targets/qmt_terminal/README.md",
    "targets/miniqmt_runner/README.md",
    "validation/offline-intake-checklist.md",
    "evidence/redacted-smoke-result-template.yaml",
    "checksums/SHA256SUMS",
)

REQUIRED_ALLOWED_OFFLINE_CHECKS = {
    "package_layout",
    "manifest_schema",
    "sha256_text_files",
    "target_docs_presence",
    "redaction_template_presence",
}

REQUIRED_FORBIDDEN_OPERATIONS = {
    "nas_read",
    "nas_write",
    "nas_list",
    "nas_copy",
    "nas_publish",
    "nas_pull",
    "credential_read",
    "env_file_read",
    "qmt_start",
    "miniqmt_start",
    "xtquant_import",
    "gateway_start",
    "account_raw_query",
    "raw_positions_emit",
    "submit_order",
    "cancel_order",
    "simulation",
    "live",
}

REQUIRED_CHECKSUM_PATHS = {
    "manifest.yaml",
    "README.md",
    "targets/qmt_terminal/README.md",
    "targets/miniqmt_runner/README.md",
    "validation/offline-intake-checklist.md",
    "evidence/redacted-smoke-result-template.yaml",
}

REQUIRED_FALSE_FLAGS = (
    "runtime_authorized",
    "nas_operation_authorized",
    "credential_read_authorized",
    "account_query_authorized",
    "trade_write_authorized",
)


@dataclass(frozen=True)
class PackageCheckResult:
    package_root: str
    passed: bool
    checked_files: tuple[str, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "package_root": self.package_root,
            "passed": self.passed,
            "checked_files": list(self.checked_files),
            "errors": list(self.errors),
        }


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: YAML parse failed: {exc}") from exc


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _as_string_set(value: Any, label: str) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings")
    return set(value)


def _validate_manifest(package_root: Path, errors: list[str]) -> None:
    try:
        manifest = _as_mapping(_load_yaml(package_root / "manifest.yaml"), "manifest")
    except ValueError as exc:
        errors.append(str(exc))
        return

    expected_values = {
        "schema_version": "cr089-strategy-package-manifest-v1",
        "package_id": "strategy-package-qmt_interface_smoke-0.1.0",
        "strategy_id": "qmt_interface_smoke",
        "version": "0.1.0",
        "change_id": "CR-089",
        "parent_cr": "CR-046",
        "approval_scope": "cp2-cp3-cp5-readiness-only",
    }
    for key, expected in expected_values.items():
        actual = manifest.get(key)
        if str(actual) != expected:
            errors.append(f"manifest.{key} expected {expected!r}, got {actual!r}")

    for key in REQUIRED_FALSE_FLAGS:
        if manifest.get(key) is not False:
            errors.append(f"manifest.{key} must be false")

    try:
        allowed_checks = _as_string_set(
            manifest.get("allowed_offline_checks"), "manifest.allowed_offline_checks"
        )
    except ValueError as exc:
        errors.append(str(exc))
    else:
        missing = REQUIRED_ALLOWED_OFFLINE_CHECKS - allowed_checks
        if missing:
            errors.append(
                "manifest.allowed_offline_checks missing: "
                + ", ".join(sorted(missing))
            )

    try:
        forbidden_operations = _as_string_set(
            manifest.get("forbidden_operations"), "manifest.forbidden_operations"
        )
    except ValueError as exc:
        errors.append(str(exc))
    else:
        missing = REQUIRED_FORBIDDEN_OPERATIONS - forbidden_operations
        if missing:
            errors.append(
                "manifest.forbidden_operations missing: "
                + ", ".join(sorted(missing))
            )

    targets = manifest.get("targets")
    if not isinstance(targets, list):
        errors.append("manifest.targets must be a list")
    else:
        target_by_id = {
            item.get("id"): item for item in targets if isinstance(item, dict)
        }
        for target_id, rel_path in {
            "qmt_terminal": "targets/qmt_terminal/README.md",
            "miniqmt_runner": "targets/miniqmt_runner/README.md",
        }.items():
            target = target_by_id.get(target_id)
            if not isinstance(target, dict):
                errors.append(f"manifest.targets missing {target_id}")
                continue
            if target.get("path") != rel_path:
                errors.append(f"manifest.targets[{target_id}].path must be {rel_path}")
            if target.get("runtime_required") is not True:
                errors.append(f"manifest.targets[{target_id}].runtime_required must be true")
            if target.get("runtime_authorized") is not False:
                errors.append(f"manifest.targets[{target_id}].runtime_authorized must be false")

    readonly_contract = _as_mapping(
        manifest.get("readonly_smoke_contract", {}), "manifest.readonly_smoke_contract"
    )
    if readonly_contract.get("endpoint_id") != "query_positions":
        errors.append("manifest.readonly_smoke_contract.endpoint_id must be query_positions")
    if readonly_contract.get("path") != "/qmt/account/positions":
        errors.append("manifest.readonly_smoke_contract.path must be /qmt/account/positions")
    if readonly_contract.get("required_scope") != "qmt:positions:read":
        errors.append("manifest.readonly_smoke_contract.required_scope must be qmt:positions:read")
    if readonly_contract.get("execution_mode") != "manual_user_only_after_runtime_authorization":
        errors.append("manifest.readonly_smoke_contract.execution_mode is not fail-closed")

    artifacts = _as_mapping(manifest.get("artifacts", {}), "manifest.artifacts")
    if artifacts.get("zip_status") != "not_built":
        errors.append("manifest.artifacts.zip_status must remain not_built for skeleton")

    checksums = _as_mapping(manifest.get("checksums", {}), "manifest.checksums")
    if checksums.get("file") != "checksums/SHA256SUMS":
        errors.append("manifest.checksums.file must be checksums/SHA256SUMS")

    evidence_template = manifest.get("evidence_template")
    if evidence_template != "evidence/redacted-smoke-result-template.yaml":
        errors.append("manifest.evidence_template must point to redacted template")


def _validate_evidence_template(package_root: Path, errors: list[str]) -> None:
    try:
        template = _as_mapping(
            _load_yaml(package_root / "evidence/redacted-smoke-result-template.yaml"),
            "evidence template",
        )
    except ValueError as exc:
        errors.append(str(exc))
        return

    if template.get("schema_version") != "cr089-redacted-smoke-result-template-v1":
        errors.append("evidence template schema_version mismatch")
    if template.get("runtime_authorization_status") != "not_authorized_by_package":
        errors.append("evidence template must not imply runtime authorization")

    smoke = _as_mapping(template.get("readonly_smoke", {}), "readonly_smoke")
    expected_false = (
        "raw_payload_included",
        "raw_account_output_included",
        "trade_write_attempted",
    )
    for key in expected_false:
        if smoke.get(key) is not False:
            errors.append(f"readonly_smoke.{key} must be false")
    if smoke.get("endpoint_id") != "query_positions":
        errors.append("readonly_smoke.endpoint_id must be query_positions")
    if smoke.get("required_scope") != "qmt:positions:read":
        errors.append("readonly_smoke.required_scope must be qmt:positions:read")


def _parse_sha256sums(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"{path}:{line_number}: expected '<sha256>  <relative-path>'")
        digest, rel_path = parts
        rel_path = rel_path.strip()
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"{path}:{line_number}: invalid sha256 digest")
        relative = Path(rel_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{path}:{line_number}: checksum path must be relative")
        if rel_path in entries:
            raise ValueError(f"{path}:{line_number}: duplicate checksum path {rel_path}")
        entries[rel_path] = digest
    return entries


def _validate_checksums(package_root: Path, errors: list[str]) -> tuple[str, ...]:
    checksum_path = package_root / "checksums/SHA256SUMS"
    try:
        entries = _parse_sha256sums(checksum_path)
    except ValueError as exc:
        errors.append(str(exc))
        return ()

    missing = REQUIRED_CHECKSUM_PATHS - set(entries)
    if missing:
        errors.append("checksums missing required paths: " + ", ".join(sorted(missing)))

    checked: list[str] = []
    for rel_path, expected_digest in sorted(entries.items()):
        path = package_root / rel_path
        if not path.is_file():
            errors.append(f"checksum target missing: {rel_path}")
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            errors.append(
                f"checksum mismatch for {rel_path}: expected {expected_digest}, got {actual_digest}"
            )
        checked.append(rel_path)
    return tuple(checked)


def check_package(package_root: Path) -> PackageCheckResult:
    package_root = package_root.resolve()
    errors: list[str] = []

    if not package_root.exists():
        errors.append(f"package root does not exist: {package_root}")
        return PackageCheckResult(str(package_root), False, (), tuple(errors))
    if not package_root.is_dir():
        errors.append(f"package root is not a directory: {package_root}")
        return PackageCheckResult(str(package_root), False, (), tuple(errors))

    for rel_path in REQUIRED_FILES:
        if not (package_root / rel_path).is_file():
            errors.append(f"missing required file: {rel_path}")

    if not errors:
        _validate_manifest(package_root, errors)
        _validate_evidence_template(package_root, errors)
        checked_files = _validate_checksums(package_root, errors)
    else:
        checked_files = ()

    return PackageCheckResult(
        package_root=str(package_root),
        passed=not errors,
        checked_files=checked_files,
        errors=tuple(errors),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check CR089 qmt_interface_smoke offline package skeleton."
    )
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("packages/qmt_interface_smoke/0.1.0"),
        help="Local package root to inspect. This checker performs file-only validation.",
    )
    args = parser.parse_args(argv)

    result = check_package(args.package_root)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
