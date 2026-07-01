#!/usr/bin/env python3
"""Sync only CR149 current-truth objects from local lake to NAS.

Default mode is dry-run. Real NAS writes require --execute plus an approval id.
The command never deletes NAS files and never pulls or restores local data.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.catalog import CatalogStore


MARKER_RE = re.compile(r"password|token|secret|credential_value", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SyncObject:
    label: str
    relative_path: str
    exists: bool
    size_bytes: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-root", required=True, type=Path)
    parser.add_argument("--env-file", default=".env", type=Path)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--approval-id", default=None)
    parser.add_argument("--evidence-path", required=True, type=Path)
    parser.add_argument("--index-path", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _redact(text: str, redactions: tuple[str, ...]) -> tuple[str, ...]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        for value in redactions:
            if value:
                line = line.replace(value, "<redacted>")
        lines.append(line[:500])
        if len(lines) >= 200:
            break
    return tuple(lines)


def _sync_objects(local_root: Path) -> tuple[SyncObject, ...]:
    entries = sorted(CatalogStore(local_root).list(), key=lambda item: item.dataset)
    objects = [
        SyncObject(
            label="catalog",
            relative_path="catalog/catalog.json",
            exists=(local_root / "catalog/catalog.json").exists(),
            size_bytes=(local_root / "catalog/catalog.json").stat().st_size,
        )
    ]
    for entry in entries:
        if not entry.canonical_path:
            continue
        path = local_root / entry.canonical_path
        objects.append(
            SyncObject(
                label=f"canonical:{entry.dataset}",
                relative_path=entry.canonical_path,
                exists=path.exists(),
                size_bytes=path.stat().st_size if path.exists() else 0,
            )
        )
    return tuple(objects)


def main() -> int:
    args = _parse_args()
    if args.execute and not args.approval_id:
        raise SystemExit("--approval-id is required with --execute")

    env_values = _load_env_file(args.env_file)
    merged_env = dict(os.environ)
    merged_env.update(env_values)
    nas_ip = merged_env.get("MARKET_DATA_NAS_IP", "")
    nas_user = merged_env.get("MARKET_DATA_NAS_USERNAME", "")
    nas_password = merged_env.get("MARKET_DATA_NAS_PASSWORD", "")
    rsync_port = merged_env.get("MARKET_DATA_NAS_RSYNC_PORT", "873")
    rsync_module = merged_env.get("MARKET_DATA_NAS_RSYNC_MODULE", "")
    remote_lake_target = merged_env.get("MARKET_DATA_NAS_RSYNC_LAKE_TARGET") or merged_env.get(
        "MARKET_DATA_NAS_RSYNC_TARGET", "/data-lake"
    )
    if not all((nas_ip, nas_password, rsync_module)):
        raise SystemExit("NAS rsync configuration incomplete")

    objects = _sync_objects(args.local_root)
    missing_local = [item.relative_path for item in objects if not item.exists]
    if missing_local:
        raise SystemExit(f"local current-truth objects missing: {missing_local}")

    remote_base = f"{nas_ip}::{rsync_module}"
    if nas_user:
        remote_base = f"{nas_user}@{remote_base}"
    target = f"{remote_base}/{remote_lake_target.strip('/')}/"
    subprocess_env = dict(os.environ)
    subprocess_env["RSYNC_PASSWORD"] = nas_password
    redactions = tuple(value for value in (nas_password,) if value)

    cmd = [
        "rsync",
        "-aH",
        "--checksum",
        "--relative",
        "--itemize-changes",
        "--out-format=%i %n%L",
    ]
    if not args.execute:
        cmd.append("--dry-run")
    if rsync_port:
        cmd.extend(["--port", rsync_port])
    cmd.extend([item.relative_path for item in objects])
    cmd.append(target)
    completed = subprocess.run(
        cmd,
        cwd=args.local_root,
        check=False,
        capture_output=True,
        text=True,
        env=subprocess_env,
    )
    messages = _redact("\n".join((completed.stdout, completed.stderr)), redactions)
    itemized = tuple(line for line in messages if line and not line.lower().startswith("sent "))
    status = "pass" if completed.returncode == 0 else "blocked"
    total_bytes = sum(item.size_bytes for item in objects)
    payload: dict[str, Any] = {
        "schema_version": "cr149.nas_current_truth_sync.v1",
        "cr_id": "CR-149",
        "created_at": args.created_at,
        "approval_id": args.approval_id,
        "mode": "execute" if args.execute else "dry_run",
        "status": status,
        "scope": "catalog_json_plus_17_catalog_current_canonical_objects",
        "remote_access": {
            "transport": "rsync_daemon",
            "host_label": nas_ip,
            "module_label": rsync_module,
            "lake_target": remote_lake_target,
            "port": rsync_port,
            "material_persisted": False,
        },
        "objects": [asdict(item) for item in objects],
        "summary": {
            "object_count": len(objects),
            "total_bytes": total_bytes,
            "rsync_exit_code": completed.returncode,
            "itemized_change_count": len(itemized),
            "message_count": len(messages),
        },
        "rsync_messages": itemized,
        "operation_counts": {
            "provider_fetch": 0,
            "credential_read": 1,
            "nas_dry_run": 0 if args.execute else 1,
            "nas_sync_or_write": 1 if args.execute else 0,
            "lake_write": 0,
            "catalog_pointer_mutation": 0,
            "business_conflict_cleanup": 0,
            "simulation_or_live": 0,
            "broker_write": 0,
            "restore": 0,
            "delete": 0,
            "git_remote_write": 0,
        },
        "safety": {
            "no_delete_flag": True,
            "pull_or_restore": False,
            "local_source_of_truth": True,
            "catalog_scoped_object_list": True,
        },
        "redaction_scan_passed": None,
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    marker_hits = sorted(set(MARKER_RE.findall(serialized)))
    payload["redaction_scan_passed"] = not marker_hits
    payload["redaction_marker_hit_count"] = len(marker_hits)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.evidence_path.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_path.write_text(serialized, encoding="utf-8")
    index_payload = {
        "schema_version": "evidence_index.v1",
        "cr_id": "CR-149",
        "created_at": args.created_at,
        "status": status,
        "evidence_ref": str(args.evidence_path),
        "summary": payload["summary"],
        "operation_counts": payload["operation_counts"],
    }
    args.index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if marker_hits:
        return 3
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
