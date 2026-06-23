from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.check_process_artifact_hygiene import StatusEntry, check_process_artifact_hygiene, classify_entry


def test_cr132_process_artifact_hygiene_current_workspace_passes() -> None:
    result = check_process_artifact_hygiene(Path("."), Path("process"))

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["runner_development_gate"]["allowed_to_enter_runner_development"] is True


def test_cr132_process_history_residuals_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="process", status="??", path="changes/CR-126-EXAMPLE.md"),
        StatusEntry(repo="process", status="??", path="checks/CP7-CR120-EXAMPLE.md"),
        StatusEntry(repo="process", status="??", path="context/CP2-CR113-EXAMPLE.yaml"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR126.md"),
        StatusEntry(repo="process", status="??", path="stories/STORY-CR118-EXAMPLE.md"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"artifact_history_residual"}


def test_cr132_source_human_gate_residuals_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="scripts/check_human_gate_decision_brief.py"),
        StatusEntry(repo="source", status="??", path="tests/test_cr118_human_gate_path_alias_checker.py"),
        StatusEntry(repo="source", status="??", path="tests/test_cr119_human_gate_launch_message_checker.py"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"source_human_gate_residual"}


def test_cr132_cr134_current_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="??", path="trading/strategy_runner/evidence_index.py"),
        StatusEntry(repo="source", status="??", path="tests/test_cr134_runner_evidence_index.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-134-RUNNER-EVIDENCE-INDEX-INTEGRATION-2026-06-23.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr134_asset"}


def test_cr132_cr135_start_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="??", path="tests/test_cr135_runner_artifact_bundle.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-135-RUNNER-EXECUTION-ARTIFACT-BUNDLE-REPLAY-WORKFLOW-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-135.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP7-CR135-RUNNER-ARTIFACT-BUNDLE-VERIFICATION-DONE.md",
        ),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR135-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR135.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR135.yaml"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr135_asset"}


def test_cr132_cr136_start_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/artifact_bundle.py"),
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/cli.py"),
        StatusEntry(repo="source", status="??", path="tests/test_cr136_runner_bundle_validation.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-136-RUNNER-BUNDLE-SCHEMA-COMPATIBILITY-VALIDATION-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-136.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP7-CR136-RUNNER-BUNDLE-VALIDATION-VERIFICATION-DONE.md",
        ),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR136-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR136.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR136.yaml"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR136-CLOSURE-TO-CR137-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="M", path="docs/features/strategy-runner-core/DESIGN.md"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr136_asset"}


def test_cr132_cr089_closure_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(
            repo="process",
            status="M",
            path="changes/CR-089-QMT-INTERFACE-VALIDATION-GATE-2026-06-17.md",
        ),
        StatusEntry(repo="process", status="??", path="archive/CR-089/evidence-index.json"),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-089.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR089-CLOSURE-TO-CR135-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr089_closure_asset"}


def test_cr132_unknown_residual_is_unclassified() -> None:
    assert classify_entry(StatusEntry(repo="source", status="??", path="runner_tmp.txt")) == "unclassified"
    assert classify_entry(StatusEntry(repo="process", status="??", path="changes/CR-999-UNKNOWN.md")) == "unclassified"


def test_cr132_process_artifact_hygiene_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_process_artifact_hygiene.py",
            "--source-root",
            ".",
            "--process-root",
            "process",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "cr132-process-artifact-hygiene-check-v1"
    assert payload["passed"] is True
