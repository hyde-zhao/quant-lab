from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from trading.strategy_runner import (
    replay_run_artifact_bundle,
    run_strategy_package_from_path,
    validate_run_artifact_bundle,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "cr091_strategy_runner"
PACKAGE_ROOT = FIXTURE_ROOT / "cr091_strategy_package"


def test_cr136_validates_complete_bundle_contract(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)

    manifest = validate_run_artifact_bundle(bundle_dir)

    assert manifest["schema_version"] == "cr135-run-artifact-bundle-v1"
    assert manifest["run_id"] == "cr136-bundle"
    assert manifest["status"] == "pass"
    assert manifest["passed"] is True
    assert manifest["not_authorization"] is True
    assert manifest["qmt_allowed"] is False
    assert set(manifest["files"]) == {
        "run-result.json",
        "runner-evidence.index.json",
        "run-spec.snapshot.json",
    }


def test_cr136_replay_fails_closed_when_bundle_file_is_missing(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    (bundle_dir / "run-result.json").unlink()

    with pytest.raises(ValueError, match="blocked_artifact_bundle_file_missing:run-result.json"):
        replay_run_artifact_bundle(bundle_dir)


def test_cr136_validation_fails_closed_on_file_hash_mismatch(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    run_result_path = bundle_dir / "run-result.json"
    payload = run_result_path.read_text(encoding="utf-8")
    run_result_path.write_text(payload.replace("cr136-bundle", "cr136-tamper"), encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_artifact_bundle_file_sha_mismatch:run-result.json"):
        validate_run_artifact_bundle(bundle_dir)


def test_cr136_validation_fails_closed_on_schema_mismatch(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "future-bundle-schema"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_artifact_bundle_schema_mismatch"):
        validate_run_artifact_bundle(bundle_dir)


def test_cr136_validation_fails_closed_on_consistency_mismatch(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    evidence_path = bundle_dir / "runner-evidence.index.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["status"] = "blocked"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    _refresh_manifest_file_ref(bundle_dir, "runner-evidence.index.json")

    with pytest.raises(ValueError, match="blocked_artifact_bundle_manifest_evidence_mismatch:status"):
        validate_run_artifact_bundle(bundle_dir)


def test_cr136_validation_fails_closed_on_authorization_boundary_mismatch(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["qmt_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    with pytest.raises(ValueError, match="blocked_artifact_bundle_manifest_authorization_boundary"):
        validate_run_artifact_bundle(bundle_dir)


def test_cr136_cli_validates_bundle_and_reports_blocked_json(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path)
    valid_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--validate-bundle",
            str(bundle_dir),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(valid_completed.stdout)
    assert payload["run_id"] == "cr136-bundle"
    assert payload["passed"] is True

    (bundle_dir / "run-result.json").unlink()
    invalid_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trading.strategy_runner.cli",
            "--validate-bundle",
            str(bundle_dir),
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    blocked_payload = json.loads(invalid_completed.stdout)
    assert invalid_completed.returncode == 1
    assert blocked_payload["status"] == "blocked"
    assert blocked_payload["blocked_reasons"] == [
        "blocked_artifact_bundle_file_missing:run-result.json"
    ]


def _write_bundle(tmp_path: Path) -> Path:
    bundle_dir = tmp_path / "bundle"
    result = run_strategy_package_from_path(
        PACKAGE_ROOT,
        run_id="cr136-bundle",
        bundle_output_path=bundle_dir,
    )
    assert result.passed
    return bundle_dir


def _refresh_manifest_file_ref(bundle_dir: Path, file_name: str) -> None:
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    target = bundle_dir / file_name
    manifest["files"][file_name] = {
        "path": file_name,
        "bytes": target.stat().st_size,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")
