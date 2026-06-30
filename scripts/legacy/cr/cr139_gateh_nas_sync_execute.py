#!/usr/bin/env python3
"""Execute CR139 Gate H NAS lake sync and verify with post-sync dry-run."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESS_ROOT = PROJECT_ROOT / "process"
LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake")

DRY_RUN_EVIDENCE = PROCESS_ROOT / "evidence" / "CR139-W2-GATEH-NAS-DRY-RUN-2026-06-30.json"
EVIDENCE_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEH-NAS-SYNC-EXECUTION-2026-06-30.json"
INDEX_PATH = PROCESS_ROOT / "evidence" / "CR139-W2-GATEH-NAS-SYNC-EXECUTION.index.json"
CHECK_PATH = PROCESS_ROOT / "checks" / "CR139-W2-GATEH-NAS-SYNC-EXECUTION-2026-06-30.md"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
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
        return {"exists": False, "file_count": 0, "dir_count": 0, "total_size_bytes": 0}
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
    return {"exists": True, "file_count": files, "dir_count": dirs, "total_size_bytes": total_bytes}


def redact(text: str) -> str:
    redacted = text
    redacted = re.sub(r"(?i)(RSYNC_PASSWORD=)[^\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"(?i)(MARKET_DATA_NAS_PASSWORD=)[^\s]+", r"\1<redacted>", redacted)
    redacted = re.sub(r"([A-Za-z0-9_.-]+@)?(?:\d{1,3}\.){3}\d{1,3}::[^\s]+", "<nas-target>", redacted)
    return redacted


def excerpt(text: str, max_lines: int = 80) -> dict[str, Any]:
    lines = text.splitlines()
    return {
        "line_count": len(lines),
        "head": "\n".join(lines[:max_lines]),
        "tail": "\n".join(lines[-max_lines:]) if len(lines) > max_lines else "",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def extract_stats(output: str) -> dict[str, str]:
    allowed = {
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
    }
    stats: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in allowed:
            stats[key] = value.strip()
    return stats


def stat_int(stats: dict[str, str], key: str) -> int | None:
    value = stats.get(key)
    if value is None:
        return None
    match = re.search(r"\d[\d,]*", value)
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def run_sync(execute: bool) -> dict[str, Any]:
    args = ["scripts/sync_data_lake_to_nas.sh", "push", "lake", "--env-file", "/dev/null"]
    if execute:
        args.insert(3, "--execute")
    command = (
        "set -a; . ./.env; set +a; "
        f"export MARKET_DATA_LAKE_ROOT={shlex.quote(str(LAKE_ROOT))}; "
        "export MARKET_DATA_NAS_RSYNC_DELETE=false; "
        + " ".join(shlex.quote(part) for part in args)
    )
    started_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    run = subprocess.run(
        ["bash", "-lc", command],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    completed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    stdout = redact(run.stdout)
    stderr = redact(run.stderr)
    combined = stdout + "\n" + stderr
    return {
        "started_at": started_at,
        "completed_at": completed_at,
        "argv": args,
        "execute": execute,
        "delete": False,
        "returncode": run.returncode,
        "stats": extract_stats(combined),
        "stdout_excerpt": excerpt(stdout),
        "stderr_excerpt": excerpt(stderr),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    dry_run = json.loads(DRY_RUN_EVIDENCE.read_text(encoding="utf-8"))
    started_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    active_catalog = LAKE_ROOT / "catalog" / "catalog.json"
    active_manifest = LAKE_ROOT / "manifest" / "market_data_manifest.jsonl"
    before = {
        "active_catalog_sha256": sha256_file(active_catalog),
        "active_manifest_sha256": sha256_file(active_manifest),
        "lake_tree": tree_summary(LAKE_ROOT),
    }

    execute_result = run_sync(execute=True)
    post_sync_dry_run = run_sync(execute=False) if execute_result["returncode"] == 0 else None

    after = {
        "active_catalog_sha256": sha256_file(active_catalog),
        "active_manifest_sha256": sha256_file(active_manifest),
        "lake_tree": tree_summary(LAKE_ROOT),
    }
    completed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    post_stats = post_sync_dry_run["stats"] if post_sync_dry_run else {}
    checks = {
        "pre_sync_dry_run_passed": dry_run.get("status") == "pass_gate_h_nas_dry_run",
        "execute_returned_zero": execute_result["returncode"] == 0,
        "post_sync_dry_run_returned_zero": bool(post_sync_dry_run and post_sync_dry_run["returncode"] == 0),
        "post_sync_no_deletes": stat_int(post_stats, "Number of deleted files") == 0,
        "post_sync_no_regular_files_remaining": stat_int(post_stats, "Number of regular files transferred") == 0,
        "active_catalog_unchanged": before["active_catalog_sha256"] == after["active_catalog_sha256"],
        "active_manifest_unchanged": before["active_manifest_sha256"] == after["active_manifest_sha256"],
        "local_lake_tree_unchanged": before["lake_tree"] == after["lake_tree"],
        "execute_delete_disabled": execute_result["delete"] is False,
        "post_sync_delete_disabled": bool(post_sync_dry_run and post_sync_dry_run["delete"] is False),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    payload: dict[str, Any] = {
        "schema": "cr139.gateh.nas_sync_execution.v1",
        "status": "pass_gate_h_nas_sync_execution" if not failed_checks else "blocked_gate_h_nas_sync_execution",
        "started_at": started_at,
        "completed_at": completed_at,
        "authorization": {
            "scope": "Gate H NAS sync execution only",
            "direction": "push",
            "dataset_scope": "lake",
            "execute": True,
            "delete": False,
            "research_sync": False,
        },
        "operation_counts": {
            "nas_write_sync": 1 if execute_result["returncode"] == 0 else 0,
            "nas_post_sync_dry_run": 1 if post_sync_dry_run and post_sync_dry_run["returncode"] == 0 else 0,
            "nas_delete": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "runtime_operation": 0,
            "credential_disclosure": 0,
            "git_remote": 0,
        },
        "before": before,
        "after": after,
        "execute_result": execute_result,
        "post_sync_dry_run": post_sync_dry_run,
        "checks": checks,
        "failed_checks": failed_checks,
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

    exec_stats = execute_result["stats"]
    check_lines = [
        "# CR139 W2 Gate H NAS Sync Execution",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence: `{EVIDENCE_PATH}`",
        f"- execute_returncode: `{execute_result['returncode']}`",
        f"- post_sync_dry_run_returncode: `{post_sync_dry_run['returncode'] if post_sync_dry_run else 'not_run'}`",
        f"- active_catalog_before_after: `{before['active_catalog_sha256']}` / `{after['active_catalog_sha256']}`",
        f"- active_manifest_before_after: `{before['active_manifest_sha256']}` / `{after['active_manifest_sha256']}`",
        f"- local_lake_files_before_after: `{before['lake_tree']['file_count']}` / `{after['lake_tree']['file_count']}`",
        f"- local_lake_bytes_before_after: `{before['lake_tree']['total_size_bytes']}` / `{after['lake_tree']['total_size_bytes']}`",
        "",
        "## Boundary",
        "",
        "- direction: push",
        "- scope: lake only",
        "- execute: true for sync, false for post-sync verification dry-run",
        "- delete: false",
        "- no research sync",
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
    check_lines.extend(["", "## Execute RSync Stats", "", "| Field | Value |", "|---|---|"])
    for key, value in exec_stats.items():
        check_lines.append(f"| {key} | {value} |")
    check_lines.extend(["", "## Post-Sync Dry-Run Stats", "", "| Field | Value |", "|---|---|"])
    for key, value in post_stats.items():
        check_lines.append(f"| {key} | {value} |")
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text("\n".join(check_lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": payload["status"], "failed_checks": failed_checks}, sort_keys=True))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
