from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import yaml

from trading.strategy_runner import (
    RunSpec,
    append_run_registry_from_bundle,
    inspect_run_registry_entry,
    read_run_registry,
    run_strategy_package,
    run_strategy_package_from_path,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr137_run_spec_accepts_run_registry_output_path(tmp_path: Path) -> None:
    spec = RunSpec.from_mapping(
        {
            "schema_version": "cr128-run-spec-v1",
            "package_root": PACKAGE_ROOT.resolve().as_posix(),
            "run_id": "cr137-spec",
            "bundle_output_path": "bundle",
            "run_registry_output_path": "runner-runs.index.json",
            "mode": "offline",
            "not_authorization": True,
        },
        base_dir=tmp_path,
    )

    assert spec.bundle_output_path == tmp_path / "bundle"
    assert spec.run_registry_output_path == tmp_path / "runner-runs.index.json"
    assert spec.to_dict()["run_registry_output_path"].endswith("runner-runs.index.json")


def test_cr137_run_spec_requires_bundle_output_for_registry(tmp_path: Path) -> None:
    try:
        RunSpec.from_mapping(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr137-missing-bundle",
                "run_registry_output_path": "runner-runs.index.json",
                "mode": "offline",
                "not_authorization": True,
            },
            base_dir=tmp_path,
        )
    except ValueError as exc:
        assert str(exc) == "blocked_run_registry_requires_bundle_output"
    else:
        raise AssertionError("registry output without bundle output must fail closed")


def test_cr137_runner_appends_pass_bundle_entry_to_registry(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    registry_path = tmp_path / "runner-runs.index.json"

    result = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr137-pass-registry",
        bundle_output_path=bundle_dir,
        run_registry_output_path=registry_path,
    )

    assert result.passed
    registry = read_run_registry(registry_path)
    assert registry["schema_version"] == "cr137-run-registry-v1"
    assert registry["entry_count"] == 1
    assert registry["not_authorization"] is True
    assert registry["qmt_allowed"] is False
    entry = registry["entries"][0]
    assert entry["schema_version"] == "cr137-run-registry-entry-v1"
    assert entry["run_id"] == "cr137-pass-registry"
    assert entry["status"] == "pass"
    assert entry["passed"] is True
    assert entry["bundle_path"] == bundle_dir.as_posix()
    assert entry["manifest_sha256"]
    assert entry["package_id"] == "strategy-package-cr091-fixture-0.1.0"
    assert entry["not_authorization"] is True
    assert entry["qmt_allowed"] is False
    assert all(value == 0 for value in entry["forbidden_operation_counters"].values())
    assert "target_portfolio" not in json.dumps(registry, ensure_ascii=False)
    assert "order_intents" not in json.dumps(registry, ensure_ascii=False)


def test_cr137_runner_appends_blocked_diagnostic_without_pass_bundle(tmp_path: Path) -> None:
    registry_path = tmp_path / "runner-runs.index.json"
    bundle_dir = tmp_path / "blocked-bundle"
    missing_package = tmp_path / "missing-package"

    result = run_strategy_package(
        RunSpec.from_package_root(
            missing_package,
            run_id="cr137-blocked-diagnostic",
            bundle_output_path=bundle_dir,
            run_registry_output_path=registry_path,
        )
    )

    assert result.status == "blocked"
    assert not bundle_dir.exists()
    entry = read_run_registry(registry_path)["entries"][0]
    assert entry["run_id"] == "cr137-blocked-diagnostic"
    assert entry["status"] == "blocked"
    assert entry["passed"] is False
    assert entry["bundle_path"] == ""
    assert entry["manifest_sha256"] == ""
    assert entry["blocked_reasons"] == ["blocked_manifest_missing"]
    assert entry["not_authorization"] is True
    assert entry["qmt_allowed"] is False


def test_cr137_registry_append_bundle_and_inspect_api(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    registry_path = tmp_path / "runner-runs.index.json"
    result = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr137-api-append",
        bundle_output_path=bundle_dir,
    )
    assert result.passed

    registry = append_run_registry_from_bundle(registry_path, bundle_dir)
    entry = inspect_run_registry_entry(registry_path, "cr137-api-append")

    assert registry["entry_count"] == 1
    assert entry["run_id"] == "cr137-api-append"
    assert entry["passed"] is True
    assert entry["bundle_path"] == bundle_dir.as_posix()


def test_cr137_registry_rejects_sensitive_registry_path(tmp_path: Path) -> None:
    sensitive_registry = tmp_path / "token" / "runner-runs.index.json"

    try:
        read_run_registry(sensitive_registry)
    except ValueError as exc:
        assert str(exc) == "blocked_run_registry_path_sensitive"
    else:
        raise AssertionError("registry paths containing sensitive segments must fail closed")


def test_cr137_cli_run_list_inspect_and_append_registry(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    bundle_dir = tmp_path / "cli-bundle"
    registry_path = tmp_path / "runner-runs.index.json"
    appended_registry_path = tmp_path / "runner-runs-appended.index.json"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr137-cli-registry",
                "mode": "offline",
                "not_authorization": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    run_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--spec",
            str(spec_path),
            "--bundle-output",
            str(bundle_dir),
            "--registry-output",
            str(registry_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    list_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--list-registry",
            str(registry_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    inspect_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--inspect-registry",
            str(registry_path),
            "--run-id",
            "cr137-cli-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    append_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--append-registry-bundle",
            str(bundle_dir),
            "--registry-output",
            str(appended_registry_path),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(run_completed.stdout)["passed"] is True
    list_payload = json.loads(list_completed.stdout)
    inspect_payload = json.loads(inspect_completed.stdout)
    append_payload = json.loads(append_completed.stdout)
    assert list_payload["entry_count"] == 1
    assert list_payload["entries"][0]["run_id"] == "cr137-cli-registry"
    assert inspect_payload["run_id"] == "cr137-cli-registry"
    assert inspect_payload["passed"] is True
    assert append_payload["entry_count"] == 1
    assert append_payload["entries"][0]["manifest_sha256"]
