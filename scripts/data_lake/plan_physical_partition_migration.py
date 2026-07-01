#!/usr/bin/env python
"""Plan a copy-first physical partition migration for the market data lake.

This command is read-only. It does not copy data, publish catalog pointers,
delete legacy paths, sync NAS, or read credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.lake_layout import LakeLayout, ensure_path_outside_root, legacy_run_id_path_detected

OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "physical_partition_migration": 0,
    "legacy_delete_or_archive": 0,
    "credential_read": 0,
    "nas_operation": 0,
    "runtime_operation": 0,
    "git_remote_write": 0,
}


def build_physical_migration_plan(lake_root: str | Path) -> dict[str, Any]:
    root = Path(lake_root).expanduser().resolve()
    layout = LakeLayout(root)
    catalog_path = layout.catalog_root / "catalog.json"
    catalog = _load_catalog(catalog_path)
    datasets = catalog.get("datasets", {})
    if not isinstance(datasets, Mapping):
        raise ValueError(f"catalog datasets must be a mapping: {catalog_path}")

    entries = []
    for dataset, entry in sorted(datasets.items()):
        if not isinstance(entry, Mapping):
            continue
        entries.append(_plan_dataset(root, str(dataset), entry))

    summary = {
        "catalog_dataset_count": len(entries),
        "published_dataset_count": sum(1 for item in entries if item["published"]),
        "source_missing_count": sum(1 for item in entries if item["source_status"] == "missing"),
        "already_current_layout_count": sum(1 for item in entries if item["layout_status"] == "already_current"),
        "legacy_run_id_layout_count": sum(1 for item in entries if item["layout_status"] == "legacy_run_id"),
        "copy_first_candidate_count": sum(1 for item in entries if item["planned_action"] == "copy_first_to_current"),
        "pointer_update_candidate_count": sum(1 for item in entries if item["catalog_pointer_update_required"]),
        "legacy_delete_candidate_count": 0,
    }
    return {
        "schema_version": "physical-partition-migration-plan-v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "read_only_plan_no_lake_write",
        "lake_root": str(root),
        "catalog_path": str(catalog_path),
        "summary": summary,
        "datasets": entries,
        "operation_counts": dict(OPERATION_COUNTS),
        "gate_policy": {
            "no_gate_required_for": [
                "read-only catalog scan",
                "source existence check",
                "copy-first target planning",
                "rollback metadata generation",
            ],
            "human_gate_required_for": [
                "executing physical copy into canonical current layout",
                "updating catalog canonical_path or published/current pointer",
                "moving legacy current to archive",
                "deleting or archiving legacy run_id paths",
                "NAS sync or restore drill",
                "semantic selection for business-conflict duplicate groups",
            ],
            "rollback_strategy": "copy-first; keep all legacy run_id paths; rollback by reverting catalog/published pointers before any cleanup",
        },
        "backup_policy": {
            "full_second_backup_required": False,
            "required_before_execution": [
                "verify existing NAS backup or user-provided backup snapshot remains protected",
                "freeze current catalog/catalog.json",
                "freeze manifest/market_data_manifest.jsonl",
                "freeze current inventory and golden baseline",
                "record catalog rollback map for every pointer update candidate",
            ],
        },
    }


def _plan_dataset(root: Path, dataset: str, entry: Mapping[str, Any]) -> dict[str, Any]:
    schema_version = str(entry.get("schema_version") or "1.0")
    canonical_path_value = entry.get("canonical_path")
    source = (root / str(canonical_path_value)).resolve() if canonical_path_value else None
    current_root = root / "canonical" / dataset / schema_version / "current"
    source_exists = bool(source and source.exists())
    source_is_file = bool(source and source.is_file())
    source_is_dir = bool(source and source.is_dir())
    target = current_root / source.name if source_is_file and source is not None else current_root
    layout_status = "missing"
    if source is not None and _is_relative_to(source, current_root):
        layout_status = "already_current"
    elif source is not None and legacy_run_id_path_detected(source):
        layout_status = "legacy_run_id"
    elif source is not None:
        layout_status = "non_current_non_run_id"

    planned_action = "none"
    catalog_pointer_update_required = False
    if not source_exists:
        planned_action = "blocked_source_missing"
    elif layout_status == "already_current":
        planned_action = "none"
    else:
        planned_action = "copy_first_to_current"
        catalog_pointer_update_required = True

    return {
        "dataset": dataset,
        "schema_version": schema_version,
        "published": bool(entry.get("published")),
        "readiness_status": entry.get("readiness_status"),
        "pit_status": entry.get("pit_status"),
        "quality_status": entry.get("quality_status"),
        "source_canonical_path": str(canonical_path_value) if canonical_path_value else None,
        "source_abs_path": str(source) if source is not None else None,
        "source_status": "present" if source_exists else "missing",
        "source_type": "file" if source_is_file else "directory" if source_is_dir else "unknown",
        "source_size_bytes": _path_size(source) if source_exists and source is not None else None,
        "source_file_count": _file_count(source) if source_exists and source is not None else 0,
        "layout_status": layout_status,
        "target_current_path": str(target.relative_to(root)),
        "target_abs_path": str(target),
        "target_exists": target.exists(),
        "planned_action": planned_action,
        "catalog_pointer_update_required": catalog_pointer_update_required,
        "rollback_pointer": {
            "dataset": dataset,
            "catalog_pointer_path": entry.get("catalog_pointer_path"),
            "canonical_path_before": canonical_path_value,
            "canonical_path_after": str(target.relative_to(root)) if catalog_pointer_update_required else canonical_path_value,
            "lineage_checksum_before": entry.get("lineage_checksum"),
            "latest_manifest_run_id_before": entry.get("latest_manifest_run_id"),
            "data_run_id_before": entry.get("data_run_id"),
            "publish_run_id_before": entry.get("publish_run_id"),
        },
        "execution_gate_required": planned_action != "none",
        "cleanup_gate_required": False,
    }


def _load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"catalog root must be a JSON object: {path}")
    return payload


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _file_count(path: Path) -> int:
    if path.is_file():
        return 1
    return sum(1 for item in path.rglob("*") if item.is_file())


def _path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan copy-first physical partition migration.")
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    lake_root = Path(args.lake_root).expanduser().resolve()
    out = ensure_path_outside_root(args.out, lake_root, label="physical migration plan output")
    out.parent.mkdir(parents=True, exist_ok=True)
    plan = build_physical_migration_plan(lake_root)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
