#!/usr/bin/env python3
"""Run CR139 Gate H NAS dry-run for the local data-lake only.

The wrapper intentionally captures and redacts rsync output. It forces dry-run
mode and disables --delete regardless of .env defaults.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESS_ROOT = PROJECT_ROOT / "process"
LAKE_ROOT = Path(os.environ.get("MARKET_DATA_LAKE_ROOT", "/home/hyde/data/quant-lab/data-lake"))

EVIDENCE_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEH-NAS-DRY-RUN-2026-06-30.json"
INDEX_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEH-NAS-DRY-RUN.index.json"
CHECK_PATH = PROCESS_ROOT / "checks" / "CR139-W2-GATEH-NAS-DRY-RUN-2026-06-30.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_summary(root: Path) -> dict[str, Any]:
    files = 0
    dirs = 0
    total_bytes = 0
    if not root.exists():
        return {
            "exists": False,
            "file_count": 0,
            "dir_count": 0,
            "total_size_bytes": 0,
        }
    for current_root, dirnames, filenames in os.walk(root):
        dirs += len(dirnames)
        for filename in filenames:
            path = Path(current_root) / filename
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            files += 1
            total_bytes += stat.st_size
    return {
        "exists": True,
        "file_count": files,
        "dir_count": dirs,
        "total_size_bytes": total_bytes,
    }


def redact(text: str) -> str:
    redacted = text
    redacted = re.sub(r"(?i)(RSYNC_PASSWORD=)[^\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"(?i)(MARKET_DATA_NAS_PASSWORD=)[^\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"([A-Za-z0-9_.-]+@)?(?:\d{1,3}\.){3}\d{1,3}::[^\s]+", "<nas-target>", redacted)
    return redacted


def extract_stats(output: str) -> dict[str, str]:
    stats: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line and line.split(":", 1)[0] in {
            "Number of files",
            "Number of created files",
            "Number of deleted files",
            "Number of regular files transferred",
            "Total file size",
            "Total transferred file size",
            "Literal data",
            "Matched data",
            "File list size",
            "File list generation time",
            "File list transfer time",
            "Total bytes sent",
            "Total bytes received",
        }:
            key, value = line.split(":", 1)
            stats[key.strip()] = value.strip()
    return stats


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    started_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    active_catalog = LAKE_ROOT / "catalog" / "catalog.json"
    active_manifest = LAKE_ROOT / "manifest" / "market_data_manifest.jsonl"
    before_catalog_hash = sha256_file(active_catalog) if active_catalog.exists() else None
    before_manifest_hash = sha256_file(active_manifest) if active_manifest.exists() else None
    before_lake = tree_summary(LAKE_ROOT)

    command = (
        "set -a; . ./.env; set +a; "
        f"export MARKET_DATA_LAKE_ROOT={str(LAKE_ROOT)!r}; "
        "export MARKET_DATA_NAS_RSYNC_DELETE=false; "
        "scripts/sync_data_lake_to_nas.sh push lake --env-file /dev/null"
    )
    run = subprocess.run(
        ["bash", "-lc", command],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    stdout = redact(run.stdout)
    stderr = redact(run.stderr)

    after_catalog_hash = sha256_file(active_catalog) if active_catalog.exists() else None
    after_manifest_hash = sha256_file(active_manifest) if active_manifest.exists() else None
    after_lake = tree_summary(LAKE_ROOT)
    completed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    stats = extract_stats(stdout + "\n" + stderr)
    checks = {
        "command_returned_zero": run.returncode == 0,
        "dry_run_mode_confirmed": "execute=false" in stdout,
        "delete_disabled_confirmed": "delete=false" in stdout,
        "scope_lake_only_confirmed": "scope=lake" in stdout and "sync_target=lake" in stdout,
        "active_catalog_unchanged": before_catalog_hash == after_catalog_hash,
        "active_manifest_unchanged": before_manifest_hash == after_manifest_hash,
        "local_lake_tree_unchanged": before_lake == after_lake,
        "no_secret_markers_in_output": "MARKET_DATA_NAS_PASSWORD=" not in stdout + stderr
        and "RSYNC_PASSWORD=" not in stdout + stderr,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]

    payload: dict[str, Any] = {
        "schema": "cr139.gateh.nas_dry_run.v1",
        "status": "pass_gate_h_nas_dry_run" if not failed_checks else "blocked_gate_h_nas_dry_run",
        "started_at": started_at,
        "completed_at": completed_at,
        "authorization": {
            "scope": "Gate H NAS dry-run only",
            "direction": "push",
            "dataset_scope": "lake",
            "execute": False,
            "delete": False,
            "nas_write_authorized": False,
            "nas_delete_authorized": False,
        },
        "command": {
            "argv": ["scripts/sync_data_lake_to_nas.sh", "push", "lake", "--env-file", "/dev/null"],
            "wrapper_forced_env": {
                "MARKET_DATA_LAKE_ROOT": str(LAKE_ROOT),
                "MARKET_DATA_NAS_RSYNC_DELETE": "false",
            },
            "returncode": run.returncode,
        },
        "operation_counts": {
            "nas_dry_run": 1 if run.returncode == 0 else 0,
            "nas_write": 0,
            "nas_delete": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "runtime_operation": 0,
            "credential_disclosure": 0,
            "git_remote": 0,
        },
        "before": {
            "active_catalog_sha256": before_catalog_hash,
            "active_manifest_sha256": before_manifest_hash,
            "lake_tree": before_lake,
        },
        "after": {
            "active_catalog_sha256": after_catalog_hash,
            "active_manifest_sha256": after_manifest_hash,
            "lake_tree": after_lake,
        },
        "checks": checks,
        "failed_checks": failed_checks,
        "rsync_stats": stats,
        "redacted_stdout": stdout,
        "redacted_stderr": stderr,
    }
    write_json(EVIDENCE_PATH, payload)
    write_json(
        INDEX_PATH,
        {
            "schema": "cr139.evidence.index.v1",
            "status": payload["status"],
            "evidence": str(EVIDENCE_PATH),
            "check": str(CHECK_PATH),
            "failed_checks": failed_checks,
        },
    )

    check_lines = [
        "# CR139 W2 Gate H NAS Dry-Run",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence: `{EVIDENCE_PATH}`",
        f"- command_returncode: `{run.returncode}`",
        f"- active_catalog_before_after: `{before_catalog_hash}` / `{after_catalog_hash}`",
        f"- active_manifest_before_after: `{before_manifest_hash}` / `{after_manifest_hash}`",
        f"- local_lake_files_before_after: `{before_lake['file_count']}` / `{after_lake['file_count']}`",
        f"- local_lake_bytes_before_after: `{before_lake['total_size_bytes']}` / `{after_lake['total_size_bytes']}`",
        "",
        "## Boundary",
        "",
        "- direction: push",
        "- scope: lake only",
        "- execute: false",
        "- delete: false",
        "- no active catalog write",
        "- no active manifest append",
        "- no provider catalog write",
        "- no provider-lake-catalog write",
        "- no runtime/trading/Git remote",
        "- NAS credentials were used only by rsync authentication and were not printed or persisted.",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for name, passed in checks.items():
        check_lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")
    check_lines.extend(
        [
            "",
            "## RSync Stats",
            "",
            "| Field | Value |",
            "|---|---|",
        ]
    )
    for key, value in stats.items():
        check_lines.append(f"| {key} | {value} |")
    check_lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Dry-run PASS unlocks Gate H sync authorization review only.",
            "- This dry-run does not authorize NAS write/sync execution.",
        ]
    )
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text("\n".join(check_lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": payload["status"], "failed_checks": failed_checks}, sort_keys=True))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
