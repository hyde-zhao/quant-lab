from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from trading.strategy_runner import (
    RunSpec,
    inspect_run_artifact_bundle,
    replay_run_artifact_bundle,
    run_strategy_package,
    run_strategy_package_from_path,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr135_run_spec_accepts_bundle_output_path(tmp_path: Path) -> None:
    spec = RunSpec.from_mapping(
        {
            "schema_version": "cr128-run-spec-v1",
            "package_root": PACKAGE_ROOT.resolve().as_posix(),
            "run_id": "cr135-spec",
            "bundle_output_path": "bundle",
            "mode": "offline",
            "not_authorization": True,
        },
        base_dir=tmp_path,
    )

    assert spec.bundle_output_path == tmp_path / "bundle"
    assert spec.to_dict()["bundle_output_path"].endswith("bundle")


def test_cr135_runner_writes_artifact_bundle_for_pass_run(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "run-bundle"

    result = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr135-pass-bundle",
        bundle_output_path=bundle_dir,
    )

    assert result.passed
    expected_files = {
        "run-result.json",
        "runner-evidence.index.json",
        "run-spec.snapshot.json",
        "manifest.json",
    }
    assert {path.name for path in bundle_dir.iterdir()} == expected_files

    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "cr135-run-artifact-bundle-v1"
    assert manifest["run_id"] == "cr135-pass-bundle"
    assert manifest["status"] == "pass"
    assert manifest["passed"] is True
    assert manifest["not_authorization"] is True
    assert manifest["qmt_allowed"] is False
    assert all(value == 0 for value in manifest["forbidden_operation_counters"].values())
    assert set(manifest["files"]) == expected_files - {"manifest.json"}
    assert all(item["sha256"] for item in manifest["files"].values())
    assert all(item["bytes"] > 0 for item in manifest["files"].values())

    run_result = json.loads((bundle_dir / "run-result.json").read_text(encoding="utf-8"))
    evidence_index = json.loads((bundle_dir / "runner-evidence.index.json").read_text(encoding="utf-8"))
    spec_snapshot = json.loads((bundle_dir / "run-spec.snapshot.json").read_text(encoding="utf-8"))
    assert run_result["run_id"] == "cr135-pass-bundle"
    assert evidence_index["run_result_ref"] == "run-result.json"
    assert spec_snapshot["bundle_output_path"] == bundle_dir.as_posix()


def test_cr135_bundle_inspect_and_replay_do_not_rerun_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle_dir = tmp_path / "run-bundle"
    original = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr135-replay",
        bundle_output_path=bundle_dir,
    )
    assert original.passed

    def forbidden_loader(*args: object, **kwargs: object) -> object:
        raise AssertionError("bundle replay must not load strategy packages")

    monkeypatch.setattr("trading.strategy_runner.runner.load_strategy_package", forbidden_loader)

    inspected = inspect_run_artifact_bundle(bundle_dir)
    replayed = replay_run_artifact_bundle(bundle_dir)

    assert inspected["run_id"] == "cr135-replay"
    assert inspected["files"]["run-result.json"]["path"] == "run-result.json"
    assert replayed.run_id == original.run_id
    assert replayed.passed is True
    assert replayed.target_count == original.target_count
    assert replayed.not_authorization is True
    assert replayed.qmt_allowed is False


def test_cr135_runner_does_not_write_pass_bundle_for_blocked_run(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "blocked-bundle"
    spec = RunSpec(
        package_root=PACKAGE_ROOT,
        run_id="cr135-blocked-bundle",
        bundle_output_path=bundle_dir,
        runtime_authorized=True,
    )

    result = run_strategy_package(spec)

    assert result.status == "blocked"
    assert not bundle_dir.exists()


def test_cr135_cli_writes_and_inspects_bundle(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    bundle_dir = tmp_path / "cli-bundle"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr135-cli-bundle",
                "mode": "offline",
                "not_authorization": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--spec",
            str(spec_path),
            "--bundle-output",
            str(bundle_dir),
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
            "--inspect-bundle",
            str(bundle_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    run_payload = json.loads(completed.stdout)
    inspect_payload = json.loads(inspect_completed.stdout)
    assert run_payload["passed"] is True
    assert inspect_payload["schema_version"] == "cr135-run-artifact-bundle-v1"
    assert inspect_payload["run_id"] == "cr135-cli-bundle"
    assert inspect_payload["not_authorization"] is True
    assert inspect_payload["qmt_allowed"] is False


def test_cr135_cli_does_not_write_bundle_for_blocked_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "run-spec.yaml"
    bundle_dir = tmp_path / "blocked-cli-bundle"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "cr128-run-spec-v1",
                "package_root": PACKAGE_ROOT.resolve().as_posix(),
                "run_id": "cr135-cli-blocked",
                "runtime_authorized": True,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--spec",
            str(spec_path),
            "--bundle-output",
            str(bundle_dir),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert payload["status"] == "blocked"
    assert not bundle_dir.exists()
