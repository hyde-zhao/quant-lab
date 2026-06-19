from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from trading.strategy_runner.package_exchange import (
    check_exchange,
    create_fake_exchange_root,
    fake_publish_package,
    fake_pull_package,
    validate_package,
)


SCRIPT_PATH = Path("scripts/cr100_package_exchange.py")


def _write_package(root: Path, *, approval_status: str = "approved") -> Path:
    package = root / "qmt_interface_smoke-0.1.0"
    files = {
        "strategy_core/__init__.py": "",
        "strategy_core/strategy.py": "def build_signal():\n    return {'status': 'fixture'}\n",
        "targets/qmt_terminal/entry.py": "from strategy_core.strategy import build_signal\n",
        "targets/miniqmt_runner/entry.py": "from strategy_core.strategy import build_signal\n",
        "validation/expected_capabilities.yaml": "capabilities:\n  - query_positions\n",
        "docs/README.md": "CR100 fixture package for local fake exchange only.\n",
    }
    for rel_path, text in files.items():
        path = package / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    hashed_paths = {
        rel_path: "sha256:" + hashlib.sha256((package / rel_path).read_bytes()).hexdigest()
        for rel_path in files
    }
    manifest = {
        "schema_version": "cr100-strategy-package-manifest-v1",
        "package_id": "qmt_interface_smoke",
        "package_version": "0.1.0",
        "created_at": "2026-06-19T00:00:00+08:00",
        "target_platforms": ["qmt_terminal", "miniqmt_runner"],
        "entrypoints": {
            "qmt_terminal": "targets/qmt_terminal/entry.py",
            "miniqmt_runner": "targets/miniqmt_runner/entry.py",
        },
        "approval": {
            "status": approval_status,
            "approved_by": "user",
            "approved_at": "2026-06-19T00:00:00+08:00",
        },
        "hashes": hashed_paths,
        "permissions": {
            "runtime": False,
            "submit_cancel": False,
            "simulation_live": False,
            "credential_read": False,
            "nas_read": False,
            "nas_write": False,
        },
    }
    (package / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return package


def test_validate_package_accepts_manifest_and_hashes(tmp_path: Path) -> None:
    package = _write_package(tmp_path)

    result = validate_package(package)

    assert result.identity.package_id == "qmt_interface_smoke"
    assert result.identity.package_version == "0.1.0"
    assert "strategy_core/strategy.py" in result.checked_files


def test_fake_publish_pull_and_exchange_check_stay_local(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "source")
    exchange = create_fake_exchange_root(tmp_path / "fake_exchange")
    cache = tmp_path / "cache"

    publish = fake_publish_package(package, exchange)
    exchange_check = check_exchange(exchange)
    pull = fake_pull_package(exchange, cache, "qmt_interface_smoke", "0.1.0")

    assert publish.passed is True
    assert exchange_check.passed is True
    assert pull.passed is True
    active = json.loads((cache / "active.json").read_text(encoding="utf-8"))
    assert active["package_id"] == "qmt_interface_smoke"
    assert active["not_authorization"] is True
    assert (cache / active["package_path"] / ".immutable").is_file()
    assert publish.real_nas_operations is False
    assert pull.forbidden_operation_counters["nas_publish"] == 0
    assert pull.forbidden_operation_counters["nas_pull"] == 0


def test_fake_publish_requires_fake_exchange_marker(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "source")
    unmarked_exchange = tmp_path / "unmarked_exchange"
    unmarked_exchange.mkdir()

    result = fake_publish_package(package, unmarked_exchange)

    assert result.passed is False
    assert result.errors == ("blocked_exchange_root_not_fake",)
    assert result.real_nas_operations is False


def test_validate_package_rejects_checksum_drift(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    (package / "strategy_core/strategy.py").write_text("def build_signal():\n    return {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_sha256_mismatch"):
        validate_package(package)


def test_validate_package_rejects_unapproved_package(tmp_path: Path) -> None:
    package = _write_package(tmp_path, approval_status="pending")

    with pytest.raises(ValueError, match="blocked_approval_not_approved"):
        validate_package(package)


def test_validate_package_rejects_env_or_secret_markers(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    (package / ".env").write_text("SHOULD_NOT_EXIST=1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_forbidden_file_name"):
        validate_package(package)


def test_cli_does_not_import_runtime_network_or_env_modules() -> None:
    tree = ast.parse(SCRIPT_PATH.read_text(encoding="utf-8"), filename=str(SCRIPT_PATH))
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
            "urllib",
            "xtquant",
        }
    )
