from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Any


KNOWN_SOURCE_RESIDUALS = frozenset(
    {
        "scripts/check_human_gate_decision_brief.py",
        "tests/test_cr118_human_gate_path_alias_checker.py",
        "tests/test_cr119_human_gate_launch_message_checker.py",
    }
)

CURRENT_CR132_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/test_cr132_process_artifact_hygiene.py",
    }
)

CURRENT_CR132_PROCESS_ASSETS = frozenset(
    {
        "changes/CR-132-RESIDUAL-PROCESS-ARTIFACT-HYGIENE-2026-06-23.md",
        "checks/CP6-CR132-PROCESS-ARTIFACT-HYGIENE-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR132-PROCESS-ARTIFACT-HYGIENE-VERIFICATION-DONE.md",
        "checks/CR132-PROCESS-ARTIFACT-HYGIENE-REPORT.json",
        "context/CP6-CR132.context.json",
    }
)

CURRENT_CR133_SOURCE_ASSETS = frozenset(
    {
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/cli.py",
        "trading/strategy_runner/result.py",
        "trading/strategy_runner/run_spec.py",
        "trading/strategy_runner/runner.py",
        "tests/test_cr133_runner_spec_cli.py",
    }
)

CURRENT_CR133_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-132/evidence-index.json",
        "archive/CR-133/evidence-index.json",
        "changes/CR-132-RESIDUAL-PROCESS-ARTIFACT-HYGIENE-2026-06-23.md",
        "changes/CR-133-STRATEGY-RUNNER-CORE-NEXT-SLICE-2026-06-23.md",
        "changes/CR-INDEX.json",
        "changes/summaries/CR-132.summary.json",
        "changes/summaries/CR-133.summary.json",
        "checks/CP6-CR133-RUNNER-SPEC-CLI-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR133-RUNNER-SPEC-CLI-VERIFICATION-DONE.md",
        "context/CP6-CR133.context.json",
        "context/CR133-TO-CR134-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

PROCESS_HISTORY_CR_MIN = 113
PROCESS_HISTORY_CR_MAX = 126


@dataclass(frozen=True, slots=True)
class StatusEntry:
    repo: str
    status: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return {"repo": self.repo, "status": self.status, "path": self.path}


def check_process_artifact_hygiene(
    source_root: Path,
    process_root: Path,
) -> dict[str, Any]:
    source_entries = _git_status(source_root, repo="source")
    process_entries = _git_status(process_root, repo="process")
    classified: dict[str, list[dict[str, str]]] = {
        "artifact_history_residual": [],
        "current_cr132_asset": [],
        "current_cr133_asset": [],
        "source_human_gate_residual": [],
        "ignored": [],
        "unclassified": [],
    }

    for entry in source_entries + process_entries:
        bucket = classify_entry(entry)
        classified[bucket].append(entry.to_dict())

    errors: list[str] = []
    for entry in classified["unclassified"]:
        errors.append(f"unclassified_{entry['repo']}_status:{entry['status']}:{entry['path']}")

    return {
        "schema_version": "cr132-process-artifact-hygiene-check-v1",
        "source_root": source_root.as_posix(),
        "process_root": process_root.as_posix(),
        "passed": not errors,
        "errors": errors,
        "summary": {key: len(value) for key, value in classified.items()},
        "classified": classified,
        "runner_development_gate": {
            "allowed_to_enter_runner_development": not errors,
            "blocking_bucket": "unclassified",
            "known_non_blocking_buckets": [
                "artifact_history_residual",
                "source_human_gate_residual",
            ],
        },
    }


def classify_entry(entry: StatusEntry) -> str:
    if entry.repo == "source":
        if entry.path in CURRENT_CR133_SOURCE_ASSETS:
            return "current_cr133_asset"
        if entry.path in CURRENT_CR132_SOURCE_ASSETS:
            return "current_cr132_asset"
        if entry.path in KNOWN_SOURCE_RESIDUALS:
            return "source_human_gate_residual"
        return "unclassified"

    if entry.repo == "process":
        if entry.path in CURRENT_CR133_PROCESS_ASSETS:
            return "current_cr133_asset"
        if entry.path in CURRENT_CR132_PROCESS_ASSETS:
            return "current_cr132_asset"
        if _is_process_history_residual(entry.path):
            return "artifact_history_residual"
        return "unclassified"

    return "unclassified"


def _is_process_history_residual(path: str) -> bool:
    if path.startswith("changes/"):
        return _has_history_cr(path)
    if path.startswith("checkpoints/"):
        return _has_history_cr(path)
    if path.startswith("checks/"):
        return _has_history_cr(path)
    if path.startswith("context/"):
        return _has_history_cr(path)
    if path.startswith("release/"):
        return _has_history_cr(path)
    if path.startswith("docs/quality/") or path.startswith("docs/release/"):
        return _has_history_cr(path)
    if path.startswith("stories/"):
        return _has_history_cr(path)
    return False


def _has_history_cr(path: str) -> bool:
    return any(PROCESS_HISTORY_CR_MIN <= int(match) <= PROCESS_HISTORY_CR_MAX for match in re.findall(r"CR-?(\d{3})", path))


def _git_status(repo_root: Path, *, repo: str) -> list[StatusEntry]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    )
    entries: list[StatusEntry] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        raw_path = line[3:]
        path = _normalize_status_path(raw_path)
        entries.append(StatusEntry(repo=repo, status=status, path=path))
    return entries


def _normalize_status_path(raw_path: str) -> str:
    if " -> " in raw_path:
        raw_path = raw_path.split(" -> ", 1)[1]
    path = raw_path.strip().strip('"')
    process_prefix = "process/quant-lab/"
    if path.startswith(process_prefix):
        path = path[len(process_prefix) :]
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check CR132 process artifact hygiene before runner development.")
    parser.add_argument("--source-root", default=".")
    parser.add_argument("--process-root", default="process")
    parser.add_argument("--write-report", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_process_artifact_hygiene(Path(args.source_root), Path(args.process_root))
    if args.write_report:
        Path(args.write_report).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["passed"]:
        print("Process artifact hygiene check: OK")
    else:
        print("Process artifact hygiene check: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
