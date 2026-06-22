from __future__ import annotations

import ast
import shutil
from pathlib import Path

import yaml

from scripts.check_cr089_qmt_interface_smoke_package import (
    REQUIRED_CHECKSUM_PATHS,
    REQUIRED_FORBIDDEN_OPERATIONS,
    check_package,
)


PACKAGE_ROOT = Path("packages/qmt_interface_smoke/0.1.0")
CHECKER_PATH = Path("scripts/check_cr089_qmt_interface_smoke_package.py")


def test_cr089_qmt_interface_smoke_package_skeleton_passes() -> None:
    result = check_package(PACKAGE_ROOT)

    assert result.passed is True
    assert result.errors == ()
    assert set(result.checked_files) == REQUIRED_CHECKSUM_PATHS


def test_cr089_manifest_keeps_runtime_and_trade_boundaries_closed() -> None:
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text(encoding="utf-8"))

    assert manifest["runtime_authorized"] is False
    assert manifest["nas_operation_authorized"] is False
    assert manifest["credential_read_authorized"] is False
    assert manifest["account_query_authorized"] is False
    assert manifest["trade_write_authorized"] is False
    assert set(manifest["forbidden_operations"]) >= REQUIRED_FORBIDDEN_OPERATIONS
    assert manifest["readonly_smoke_contract"] == {
        "endpoint_id": "query_positions",
        "method": "POST",
        "path": "/qmt/account/positions",
        "required_scope": "qmt:positions:read",
        "execution_mode": "manual_user_only_after_runtime_authorization",
        "evidence_policy": "redacted_summary_only",
    }


def test_cr089_checker_rejects_missing_forbidden_operation(tmp_path: Path) -> None:
    copied_root = tmp_path / "package"
    shutil.copytree(PACKAGE_ROOT, copied_root)
    manifest_path = copied_root / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["forbidden_operations"] = [
        item for item in manifest["forbidden_operations"] if item != "credential_read"
    ]
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    result = check_package(copied_root)

    assert result.passed is False
    assert any("credential_read" in error for error in result.errors)


def test_cr089_checker_rejects_checksum_drift(tmp_path: Path) -> None:
    copied_root = tmp_path / "package"
    shutil.copytree(PACKAGE_ROOT, copied_root)
    readme_path = copied_root / "README.md"
    readme_path.write_text(
        readme_path.read_text(encoding="utf-8") + "\nchecksum drift fixture\n",
        encoding="utf-8",
    )

    result = check_package(copied_root)

    assert result.passed is False
    assert any("checksum mismatch for README.md" in error for error in result.errors)


def test_cr089_checker_does_not_import_runtime_or_network_modules() -> None:
    tree = ast.parse(CHECKER_PATH.read_text(encoding="utf-8"), filename=str(CHECKER_PATH))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert not (
        imports
        & {
            "dotenv",
            "httpx",
            "requests",
            "socket",
            "subprocess",
            "trading",
            "urllib",
            "xtquant",
        }
    )
