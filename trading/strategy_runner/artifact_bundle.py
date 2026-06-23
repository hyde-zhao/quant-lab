"""Offline runner artifact bundle contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from trading.strategy_runner.evidence import assert_redacted
from trading.strategy_runner.evidence_index import RUN_EVIDENCE_INDEX_SCHEMA_VERSION, write_run_evidence_index
from trading.strategy_runner.result import RunResult, read_run_result, write_run_result
from trading.strategy_runner.run_spec import RUN_SPEC_SCHEMA_VERSION, RunSpec


RUN_ARTIFACT_BUNDLE_SCHEMA_VERSION = "cr135-run-artifact-bundle-v1"
RUN_RESULT_BUNDLE_NAME = "run-result.json"
RUN_EVIDENCE_INDEX_BUNDLE_NAME = "runner-evidence.index.json"
RUN_SPEC_SNAPSHOT_BUNDLE_NAME = "run-spec.snapshot.json"
RUN_ARTIFACT_MANIFEST_BUNDLE_NAME = "manifest.json"
RUN_ARTIFACT_REQUIRED_PAYLOAD_FILES = (
    RUN_RESULT_BUNDLE_NAME,
    RUN_EVIDENCE_INDEX_BUNDLE_NAME,
    RUN_SPEC_SNAPSHOT_BUNDLE_NAME,
)


@dataclass(frozen=True, slots=True)
class RunArtifactBundle:
    bundle_dir: Path
    manifest: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.manifest)


def write_run_artifact_bundle(
    bundle_dir: str | Path,
    *,
    spec: RunSpec,
    result: RunResult,
) -> RunArtifactBundle:
    if not result.passed:
        raise ValueError("blocked_artifact_bundle_requires_pass_result")
    if result.not_authorization is not True or result.qmt_allowed is not False:
        raise ValueError("blocked_artifact_bundle_authorization_boundary")
    if any(value != 0 for value in result.forbidden_operation_counters.values()):
        raise ValueError("blocked_artifact_bundle_forbidden_operations")

    output_dir = Path(bundle_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_result_path = output_dir / RUN_RESULT_BUNDLE_NAME
    evidence_index_path = output_dir / RUN_EVIDENCE_INDEX_BUNDLE_NAME
    spec_snapshot_path = output_dir / RUN_SPEC_SNAPSHOT_BUNDLE_NAME

    write_run_result(run_result_path, result)
    write_run_evidence_index(evidence_index_path, result, run_result_path=RUN_RESULT_BUNDLE_NAME)
    spec_snapshot_path.write_text(
        json.dumps(spec.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = _build_manifest(
        output_dir,
        result=result,
        file_names=(
            RUN_RESULT_BUNDLE_NAME,
            RUN_EVIDENCE_INDEX_BUNDLE_NAME,
            RUN_SPEC_SNAPSHOT_BUNDLE_NAME,
        ),
    )
    assert_redacted(manifest)
    (output_dir / RUN_ARTIFACT_MANIFEST_BUNDLE_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return RunArtifactBundle(bundle_dir=output_dir, manifest=manifest)


def inspect_run_artifact_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    return validate_run_artifact_bundle(bundle_dir)


def replay_run_artifact_bundle(bundle_dir: str | Path) -> RunResult:
    validate_run_artifact_bundle(bundle_dir)
    return read_run_result(Path(bundle_dir) / RUN_RESULT_BUNDLE_NAME)


def validate_run_artifact_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    manifest = _read_json_mapping(
        bundle_path / RUN_ARTIFACT_MANIFEST_BUNDLE_NAME,
        "blocked_artifact_bundle_manifest_not_mapping",
    )
    if manifest.get("schema_version") != RUN_ARTIFACT_BUNDLE_SCHEMA_VERSION:
        raise ValueError("blocked_artifact_bundle_schema_mismatch")
    if manifest.get("status") != "pass" or manifest.get("passed") is not True:
        raise ValueError("blocked_artifact_bundle_manifest_status_mismatch")
    _validate_authorization_boundary(manifest, "blocked_artifact_bundle_manifest_authorization_boundary")

    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ValueError("blocked_artifact_bundle_files_not_mapping")
    expected_files = set(RUN_ARTIFACT_REQUIRED_PAYLOAD_FILES)
    actual_files = set(str(key) for key in files)
    if actual_files != expected_files:
        missing = sorted(expected_files.difference(actual_files))
        extra = sorted(actual_files.difference(expected_files))
        details = ",".join([*(f"missing:{item}" for item in missing), *(f"extra:{item}" for item in extra)])
        raise ValueError("blocked_artifact_bundle_file_set_mismatch:" + details)
    for file_name in RUN_ARTIFACT_REQUIRED_PAYLOAD_FILES:
        file_ref = files[file_name]
        if not isinstance(file_ref, dict):
            raise ValueError(f"blocked_artifact_bundle_file_ref_not_mapping:{file_name}")
        _validate_file_ref(bundle_path, file_name, file_ref)

    result = read_run_result(bundle_path / RUN_RESULT_BUNDLE_NAME)
    result_payload = result.to_dict()
    evidence_index = _read_json_mapping(
        bundle_path / RUN_EVIDENCE_INDEX_BUNDLE_NAME,
        "blocked_artifact_bundle_evidence_index_not_mapping",
    )
    spec_snapshot = _read_json_mapping(
        bundle_path / RUN_SPEC_SNAPSHOT_BUNDLE_NAME,
        "blocked_artifact_bundle_spec_snapshot_not_mapping",
    )

    if evidence_index.get("schema_version") != RUN_EVIDENCE_INDEX_SCHEMA_VERSION:
        raise ValueError("blocked_artifact_bundle_evidence_index_schema_mismatch")
    if spec_snapshot.get("schema_version") != RUN_SPEC_SCHEMA_VERSION:
        raise ValueError("blocked_artifact_bundle_spec_snapshot_schema_mismatch")
    _validate_authorization_boundary(result_payload, "blocked_artifact_bundle_result_authorization_boundary")
    _validate_authorization_boundary(evidence_index, "blocked_artifact_bundle_evidence_authorization_boundary")
    _validate_authorization_boundary(spec_snapshot, "blocked_artifact_bundle_spec_authorization_boundary")
    _validate_consistency(manifest, result_payload, evidence_index)
    assert_redacted(manifest)
    return manifest


def _build_manifest(
    bundle_dir: Path,
    *,
    result: RunResult,
    file_names: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "schema_version": RUN_ARTIFACT_BUNDLE_SCHEMA_VERSION,
        "run_id": result.run_id,
        "status": result.status,
        "passed": result.passed,
        "package_id": result.package_id,
        "files": {file_name: _file_ref(bundle_dir / file_name) for file_name in file_names},
        "forbidden_operation_counters": dict(result.forbidden_operation_counters),
        "qmt_allowed": result.qmt_allowed,
        "not_authorization": result.not_authorization,
    }


def _validate_file_ref(bundle_dir: Path, expected_name: str, file_ref: dict[str, Any]) -> None:
    ref_path = file_ref.get("path")
    if ref_path != expected_name or Path(str(ref_path)).name != expected_name:
        raise ValueError(f"blocked_artifact_bundle_file_ref_path_mismatch:{expected_name}")
    path = bundle_dir / expected_name
    if not path.is_file():
        raise ValueError(f"blocked_artifact_bundle_file_missing:{expected_name}")
    expected_bytes = file_ref.get("bytes")
    if not isinstance(expected_bytes, int) or expected_bytes <= 0:
        raise ValueError(f"blocked_artifact_bundle_file_ref_bytes_invalid:{expected_name}")
    actual_bytes = path.stat().st_size
    if actual_bytes != expected_bytes:
        raise ValueError(f"blocked_artifact_bundle_file_size_mismatch:{expected_name}")
    expected_sha = file_ref.get("sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError(f"blocked_artifact_bundle_file_ref_sha_invalid:{expected_name}")
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(f"blocked_artifact_bundle_file_sha_mismatch:{expected_name}")


def _validate_authorization_boundary(payload: dict[str, Any], error_code: str) -> None:
    if payload.get("not_authorization") is not True or payload.get("qmt_allowed") is not False:
        raise ValueError(error_code)
    counters = payload.get("forbidden_operation_counters")
    if counters is not None:
        if not isinstance(counters, dict):
            raise ValueError(error_code)
        if any(value != 0 for value in counters.values()):
            raise ValueError(error_code)


def _validate_consistency(
    manifest: dict[str, Any],
    result_payload: dict[str, Any],
    evidence_index: dict[str, Any],
) -> None:
    for key in ("run_id", "status", "passed", "package_id"):
        if manifest.get(key) != result_payload.get(key):
            raise ValueError(f"blocked_artifact_bundle_manifest_result_mismatch:{key}")
        if manifest.get(key) != evidence_index.get(key):
            raise ValueError(f"blocked_artifact_bundle_manifest_evidence_mismatch:{key}")
    if evidence_index.get("run_result_ref") != RUN_RESULT_BUNDLE_NAME:
        raise ValueError("blocked_artifact_bundle_evidence_run_result_ref_mismatch")
    for key in ("forbidden_operation_counters", "qmt_allowed", "not_authorization"):
        if manifest.get(key) != result_payload.get(key):
            raise ValueError(f"blocked_artifact_bundle_boundary_result_mismatch:{key}")
        if manifest.get(key) != evidence_index.get(key):
            raise ValueError(f"blocked_artifact_bundle_boundary_evidence_mismatch:{key}")


def _read_json_mapping(path: Path, error_code: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"blocked_artifact_bundle_file_missing:{path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(error_code)
    return payload


def _file_ref(path: Path) -> dict[str, Any]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
