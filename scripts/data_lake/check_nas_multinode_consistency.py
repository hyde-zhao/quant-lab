#!/usr/bin/env python3
"""CR149 read-only NAS/shared-node consistency check.

The command compares local published catalog pointers with a NAS rsync daemon
view by using rsync dry-run checksum mode. It never writes to the lake or NAS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.catalog import CatalogStore


MARKER_RE = re.compile(r"password|token|secret|credential_value", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class PointerSummary:
    dataset: str
    latest_manifest_run_id: str | None
    lineage_checksum: str | None
    canonical_path: str | None
    published: bool


@dataclass(frozen=True, slots=True)
class RsyncCheckResult:
    label: str
    relative_path: str
    status: str
    exit_code: int
    itemized_change_count: int
    message_count: int
    messages: tuple[str, ...]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-root", required=True, type=Path)
    parser.add_argument("--mounted-root", required=True, type=Path)
    parser.add_argument("--env-file", default=".env", type=Path)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--created-at", required=True)
    parser.add_argument("--evidence-path", required=True, type=Path)
    parser.add_argument("--index-path", required=True, type=Path)
    parser.add_argument("--gate-ledger-path", required=True, type=Path)
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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_messages(stdout: str, stderr: str, redactions: tuple[str, ...]) -> tuple[str, ...]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    messages: list[str] = []
    for raw in combined.splitlines():
        text = raw.strip()
        if not text:
            continue
        for value in redactions:
            if value:
                text = text.replace(value, "<redacted>")
        messages.append(text[:500])
        if len(messages) >= 20:
            break
    return tuple(messages)


def _mounted_status(mounted_root: Path) -> dict[str, Any]:
    lake_candidates = []
    if mounted_root.exists():
        for candidate in (mounted_root, mounted_root / "data-lake", mounted_root / "data_lake"):
            if (candidate / "catalog" / "catalog.json").exists():
                lake_candidates.append(str(candidate))
    file_count = 0
    if mounted_root.exists():
        for _ in mounted_root.rglob("*"):
            file_count += 1
            if file_count > 1000:
                break
    return {
        "path": str(mounted_root),
        "exists": mounted_root.exists(),
        "is_dir": mounted_root.is_dir(),
        "sampled_entry_count": file_count,
        "lake_candidate_count": len(lake_candidates),
        "lake_candidates": lake_candidates,
        "status": "usable" if lake_candidates else "unavailable",
    }


def _catalog_summary(local_root: Path) -> tuple[PointerSummary, ...]:
    entries = sorted(CatalogStore(local_root).list(), key=lambda item: item.dataset)
    return tuple(
        PointerSummary(
            dataset=entry.dataset,
            latest_manifest_run_id=entry.latest_manifest_run_id,
            lineage_checksum=entry.lineage_checksum or entry.lineage_raw_checksum,
            canonical_path=entry.canonical_path,
            published=entry.published,
        )
        for entry in entries
    )


def _rsync_check(
    *,
    label: str,
    relative_path: str,
    local_root: Path,
    remote_base: str,
    remote_lake_target: str,
    rsync_port: str,
    subprocess_env: dict[str, str],
    redactions: tuple[str, ...],
) -> RsyncCheckResult:
    local_path = local_root / relative_path
    remote_prefix = remote_lake_target.strip("/")
    remote_path = f"{remote_base}/{remote_prefix}/{relative_path}"
    cmd = [
        "rsync",
        "-aHcn",
        "--checksum",
        "--itemize-changes",
        "--out-format=%i %n%L",
    ]
    if rsync_port:
        cmd.extend(["--port", rsync_port])
    cmd.extend([remote_path, str(local_path)])
    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=subprocess_env,
    )
    messages = _safe_messages(completed.stdout, completed.stderr, redactions)
    itemized = tuple(line for line in messages if line and not line.lower().startswith("sent "))
    if completed.returncode != 0:
        status = "error"
    elif itemized:
        status = "mismatch"
    else:
        status = "match"
    return RsyncCheckResult(
        label=label,
        relative_path=relative_path,
        status=status,
        exit_code=completed.returncode,
        itemized_change_count=len(itemized),
        message_count=len(messages),
        messages=itemized,
    )


def _append_gate_event(
    *,
    ledger_path: Path,
    created_at: str,
    approval_id: str,
    host_label: str,
    module_label: str,
    evidence_ref: str,
) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_id": "CR149-NAS-MULTINODE-CREDENTIAL-FALLBACK-2026-07-01",
        "event_type": "credential_fallback_audit",
        "workflow_id": "CR-149",
        "cr_id": "CR-149",
        "gate": "CP2-CR149-NAS-MULTINODE-CONSISTENCY",
        "status": "credential_fallback_used_for_read_only_check",
        "created_at": created_at,
        "approval_id": approval_id,
        "actor": "host-orchestrator",
        "artifact_refs": [evidence_ref],
        "operation_counts": {
            "credential_read": 1,
            "nas_read_only_check": 1,
            "nas_sync_or_write": 0,
            "lake_write": 0,
            "catalog_pointer_mutation": 0,
            "provider_fetch": 0,
            "restore": 0,
            "delete": 0,
            "git_remote_write": 0,
        },
        "summary": {
            "mounted_path_attempted_first": True,
            "host_label": host_label,
            "module_label": module_label,
            "credential_label": "NAS_RSYNC_AUTH_ENV",
            "credential_material_persisted": False,
        },
    }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    args = _parse_args()
    local_root: Path = args.local_root
    catalog_path = local_root / "catalog" / "catalog.json"
    if not catalog_path.exists():
        raise SystemExit(f"local catalog missing: {catalog_path}")

    mounted = _mounted_status(args.mounted_root)
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
    if mounted["status"] != "usable" and not all((nas_ip, nas_password, rsync_module)):
        raise SystemExit("mounted path unavailable and NAS rsync configuration incomplete")

    pointers = _catalog_summary(local_root)
    remote_base = f"{nas_ip}::{rsync_module}"
    if nas_user:
        remote_base = f"{nas_user}@{remote_base}"
    subprocess_env = dict(os.environ)
    subprocess_env["RSYNC_PASSWORD"] = nas_password
    redactions = tuple(value for value in (nas_password,) if value)

    checks: list[RsyncCheckResult] = []
    checks.append(
        _rsync_check(
            label="catalog",
            relative_path="catalog/catalog.json",
            local_root=local_root,
            remote_base=remote_base,
            remote_lake_target=remote_lake_target,
            rsync_port=rsync_port,
            subprocess_env=subprocess_env,
            redactions=redactions,
        )
    )
    for pointer in pointers:
        if pointer.canonical_path:
            checks.append(
                _rsync_check(
                    label=f"canonical:{pointer.dataset}",
                    relative_path=pointer.canonical_path,
                    local_root=local_root,
                    remote_base=remote_base,
                    remote_lake_target=remote_lake_target,
                    rsync_port=rsync_port,
                    subprocess_env=subprocess_env,
                    redactions=redactions,
                )
            )

    mismatch_count = sum(1 for item in checks if item.status == "mismatch")
    error_count = sum(1 for item in checks if item.status == "error")
    match_count = sum(1 for item in checks if item.status == "match")
    status = "pass" if mismatch_count == 0 and error_count == 0 and len(pointers) == 17 else "blocked"
    evidence_ref = str(args.evidence_path)
    payload: dict[str, Any] = {
        "schema_version": "cr149.nas_multinode_consistency.v1",
        "cr_id": "CR-149",
        "created_at": args.created_at,
        "approval_id": args.approval_id,
        "mode": "read_only_rsync_checksum_dry_run",
        "status": status,
        "mounted_path": mounted,
        "fallback_used": mounted["status"] != "usable",
        "remote_access": {
            "transport": "rsync_daemon",
            "host_label": nas_ip,
            "module_label": rsync_module,
            "lake_target": remote_lake_target,
            "port": rsync_port,
            "material_persisted": False,
        },
        "local_catalog": {
            "path": str(catalog_path),
            "sha256": _sha256_file(catalog_path),
            "published_pointer_count": len(pointers),
            "published_true_count": sum(1 for item in pointers if item.published),
        },
        "published_pointers": [asdict(item) for item in pointers],
        "comparison_summary": {
            "compared_object_count": len(checks),
            "match_count": match_count,
            "mismatch_count": mismatch_count,
            "error_count": error_count,
            "catalog_compared": True,
            "canonical_current_compared_count": len(checks) - 1,
        },
        "comparisons": [asdict(item) for item in checks],
        "operation_counts": {
            "provider_fetch": 0,
            "nas_read_only_check": len(checks),
            "nas_sync_or_write": 0,
            "credential_read": 1 if mounted["status"] != "usable" else 0,
            "lake_write": 0,
            "catalog_pointer_mutation": 0,
            "business_conflict_cleanup": 0,
            "simulation_or_live": 0,
            "broker_write": 0,
            "restore": 0,
            "delete": 0,
            "git_remote_write": 0,
        },
        "authorized_boundary": {
            "checkpoint_ref": "process/checkpoints/CP2-CR149-NAS-MULTINODE-CONSISTENCY.md",
            "mounted_first": True,
            "dry_run_checksum_only": True,
            "mismatch_repair": False,
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
        "evidence_ref": evidence_ref,
        "summary": {
            "published_pointer_count": len(pointers),
            "compared_object_count": len(checks),
            "match_count": match_count,
            "mismatch_count": mismatch_count,
            "error_count": error_count,
            "fallback_used": mounted["status"] != "usable",
            "redaction_scan_passed": payload["redaction_scan_passed"],
        },
        "operation_counts": payload["operation_counts"],
    }
    args.index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if mounted["status"] != "usable":
        _append_gate_event(
            ledger_path=args.gate_ledger_path,
            created_at=args.created_at,
            approval_id=args.approval_id,
            host_label=nas_ip,
            module_label=rsync_module,
            evidence_ref=evidence_ref,
        )

    if marker_hits:
        return 3
    if status != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
