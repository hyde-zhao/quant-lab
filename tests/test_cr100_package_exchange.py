from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from trading.strategy_runner.package_loader import (
    CR101_MANIFEST_SCHEMA_VERSION,
    DELIVERY_TARGET_QMT_TERMINAL_DIRECT,
    EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY,
    LEGACY_MINIQMT_RUNNER_TARGET,
)
from trading.strategy_runner.package_exchange import (
    check_exchange,
    create_fake_exchange_root,
    fake_publish_package,
    fake_pull_package,
    validate_package,
)


SCRIPT_PATH = Path("scripts/package_exchange.py")


def _write_package(root: Path, *, approval_status: str = "approved") -> Path:
    package = root / "qmt_interface_smoke-0.1.0"
    files = {
        "strategy_core/__init__.py": "",
        "strategy_core/strategy.py": "def build_signal():\n    return {'status': 'fixture'}\n",
        "targets/qmt_terminal_direct/entry.py": "from strategy_core.strategy import build_signal\n",
        "payload/admission.json": json.dumps(
            {
                "schema_version": "multifactor_strategy_admission_package_v1",
                "run_id": "cr101-package-exchange-fixture",
                "target_trade_date": "2026-06-20",
                "strategy_candidates": [{"strategy_id": "fixture_alpha", "admission": "pass"}],
                "input_refs": {"fixture": "local-only"},
                "not_authorization": True,
            },
            sort_keys=True,
        ),
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
        "schema_version": CR101_MANIFEST_SCHEMA_VERSION,
        "package_id": "qmt_interface_smoke",
        "package_version": "0.1.0",
        "created_at": "2026-06-19T00:00:00+08:00",
        "adapter_type": "strategy_package",
        "payload_path": "payload/admission.json",
        "not_authorization": True,
        "runtime_authorized": False,
        "nas_operation_authorized": False,
        "credential_read_authorized": False,
        "account_query_authorized": False,
        "trade_write_authorized": False,
        "delivery_targets": [
            {
                "target_id": DELIVERY_TARGET_QMT_TERMINAL_DIRECT,
                "implemented": True,
                "entrypoint": "targets/qmt_terminal_direct/entry.py",
            },
            {
                "target_id": "goldminer_future",
                "implemented": False,
                "entrypoint": "targets/goldminer_future/entry.py",
            },
        ],
        "execution_adapters": [
            {
                "adapter_id": EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY,
                "capabilities": ["readonly", "health", "capabilities", "query_positions"],
            }
        ],
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
        "forbidden_operations": {
            "nas_read": 0,
            "nas_write": 0,
            "credential_read": 0,
            "qmt_start": 0,
            "submit_order": 0,
            "cancel_order": 0,
            "simulation": 0,
            "live": 0,
            "catalog_publish": 0,
        },
        "forbidden_operation_counters": {
            "nas_access": 0,
            "nas_read": 0,
            "nas_write": 0,
            "nas_publish": 0,
            "nas_pull": 0,
            "credential_read": 0,
            "runtime_start": 0,
            "trade_write": 0,
            "provider_lake_publish": 0,
        },
        "checksums": {
            "payload/admission.json": hashlib.sha256((package / "payload/admission.json").read_bytes()).hexdigest(),
        },
    }
    (package / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return package


def _load_manifest(package: Path) -> dict[str, object]:
    return yaml.safe_load((package / "manifest.yaml").read_text(encoding="utf-8"))


def _write_manifest(package: Path, manifest: dict[str, object]) -> None:
    (package / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def test_validate_package_accepts_manifest_and_hashes(tmp_path: Path) -> None:
    package = _write_package(tmp_path)

    result = validate_package(package)

    assert result.identity.package_id == "qmt_interface_smoke"
    assert result.identity.package_version == "0.1.0"
    assert "strategy_core/strategy.py" in result.checked_files
    assert "targets/qmt_terminal_direct/entry.py" in result.checked_files


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


def test_cr101_package_checker_rejects_legacy_miniqmt_runner_delivery_target(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    manifest["delivery_targets"] = [
        {
            "target_id": LEGACY_MINIQMT_RUNNER_TARGET,
            "implemented": True,
            "entrypoint": "targets/miniqmt_runner/entry.py",
        }
    ]
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_legacy_miniqmt_runner_delivery_target"):
        validate_package(package)


def test_cr101_package_checker_rejects_missing_target(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    manifest["delivery_targets"] = []
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_delivery_targets_missing"):
        validate_package(package)


def test_cr101_package_checker_rejects_missing_adapter(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    manifest["execution_adapters"] = []
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_execution_adapters_missing"):
        validate_package(package)


def test_cr101_package_checker_rejects_permission_nonfalse(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    permissions = dict(manifest["permissions"])  # type: ignore[arg-type]
    permissions["runtime"] = True
    manifest["permissions"] = permissions
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_permission_nonfalse:runtime"):
        validate_package(package)


def test_cr101_package_checker_rejects_path_escape(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    targets = list(manifest["delivery_targets"])  # type: ignore[arg-type]
    target = dict(targets[0])
    target["entrypoint"] = "../escape.py"
    targets[0] = target
    manifest["delivery_targets"] = targets
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_path_escape"):
        validate_package(package)


def test_cr101_package_checker_rejects_sensitive_filename(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    (package / "evidence" / "raw_positions.json").parent.mkdir(parents=True, exist_ok=True)
    (package / "evidence" / "raw_positions.json").write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_forbidden_file_name"):
        validate_package(package)


def test_cr101_package_checker_rejects_forbidden_counter(tmp_path: Path) -> None:
    package = _write_package(tmp_path)
    manifest = _load_manifest(package)
    counters = dict(manifest["forbidden_operation_counters"])  # type: ignore[arg-type]
    counters["nas_read"] = 1
    manifest["forbidden_operation_counters"] = counters
    _write_manifest(package, manifest)

    with pytest.raises(ValueError, match="blocked_forbidden_operation_nonzero"):
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
