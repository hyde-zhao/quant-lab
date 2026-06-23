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
