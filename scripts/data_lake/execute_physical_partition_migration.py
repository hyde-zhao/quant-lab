#!/usr/bin/env python
"""Execute an approved copy-first physical partition migration.

Default mode is dry-run. Real copying and catalog updates require explicit
flags plus an approval id. The command never deletes legacy paths or syncs NAS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.lake_layout import ensure_path_outside_root

ZERO_COUNTS = {
    "provider_fetch": 0,
    "credential_read": 0,
    "nas_operation": 0,
    "runtime_operation": 0,
    "git_remote_write": 0,
    "legacy_delete_or_archive": 0,
}


def execute_physical_partition_migration(
    *,
    plan_path: str | Path,
    out_path: str | Path,
    approval_id: str | None = None,
    created_at: str | None = None,
    execute_copy: bool = False,
    update_catalog: bool = False,
    datasets: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> dict[str, Any]:
    plan_file = Path(plan_path).expanduser().resolve()
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    lake_root = Path(plan["lake_root"]).expanduser().resolve()
    out = ensure_path_outside_root(out_path, lake_root, label="physical migration execution output")
    if (execute_copy or update_catalog) and not str(approval_id or "").strip():
        raise ValueError("approval_id is required when execute_copy or update_catalog is enabled")
    if (execute_copy or update_catalog) and not str(created_at or "").strip():
        raise ValueError("created_at is required when execute_copy or update_catalog is enabled")
    effective_created_at = str(created_at or "1970-01-01T00:00:00+00:00")

    catalog_path = Path(plan["catalog_path"]).expanduser().resolve()
    catalog_before = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    copied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    verifications: list[dict[str, Any]] = []
    selected_datasets = _normalize_dataset_filter(datasets)
    plan_datasets = {str(item.get("dataset") or "") for item in plan.get("datasets", [])}
    unknown_datasets = sorted(selected_datasets - plan_datasets) if selected_datasets else []
    for dataset in unknown_datasets:
        errors.append({"dataset": dataset, "reason": "dataset_not_found_in_plan"})

    for item in plan.get("datasets", []):
        dataset_name = str(item.get("dataset") or "")
        if selected_datasets and dataset_name not in selected_datasets:
            skipped.append({"dataset": dataset_name, "reason": "dataset_filter_not_selected"})
            continue
        if item.get("planned_action") != "copy_first_to_current":
            skipped.append({"dataset": item.get("dataset"), "reason": "no_copy_needed"})
            continue
        source = Path(item["source_abs_path"]).expanduser().resolve()
        target = Path(item["target_abs_path"]).expanduser().resolve()
        try:
            source.relative_to(lake_root)
            target.relative_to(lake_root)
        except ValueError as exc:
            errors.append({"dataset": item.get("dataset"), "reason": "path_outside_lake_root", "error": str(exc)})
            continue
        if not source.exists():
            errors.append({"dataset": item.get("dataset"), "reason": "source_missing", "source": str(source)})
            continue
        target_preexisted = target.exists()
        if execute_copy:
            try:
                if target_preexisted:
                    skipped.append({"dataset": item.get("dataset"), "reason": "target_exists_verify_before_reuse", "target": str(target)})
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if source.is_file():
                        shutil.copy2(source, target)
                    elif source.is_dir():
                        shutil.copytree(source, target)
                    else:
                        errors.append({"dataset": item.get("dataset"), "reason": "unsupported_source_type", "source": str(source)})
                        continue
            except Exception as exc:
                errors.append({"dataset": item.get("dataset"), "reason": "copy_failed", "source": str(source), "target": str(target), "error": f"{type(exc).__name__}: {exc}"})
                continue
            verification = _verify_copy(source, target, dataset=str(item.get("dataset") or ""))
            verifications.append(verification)
            if not verification["passed"]:
                errors.append({"dataset": item.get("dataset"), "reason": "post_copy_verify_failed", "verification": verification})
                continue
        elif update_catalog:
            verification = _verify_copy(source, target, dataset=str(item.get("dataset") or ""))
            verifications.append(verification)
            if not verification["passed"]:
                errors.append({"dataset": item.get("dataset"), "reason": "pre_catalog_switch_verify_failed", "verification": verification})
                continue
        copied.append(
            {
                "dataset": item.get("dataset"),
                "source": str(source),
                "target": str(target),
                "executed": bool(execute_copy),
                "bytes": int(item.get("source_size_bytes") or 0),
                "file_count": int(item.get("source_file_count") or 0),
                "target_preexisted": target_preexisted,
            }
        )

    catalog_updates: list[dict[str, Any]] = []
    if update_catalog and not errors:
        catalog_after = json.loads(json.dumps(catalog_before))
        datasets = catalog_after.setdefault("datasets", {})
        for item in plan.get("datasets", []):
            dataset = item.get("dataset")
            if selected_datasets and str(dataset or "") not in selected_datasets:
                continue
            if item.get("catalog_pointer_update_required") and dataset in datasets:
                before = datasets[dataset].get("canonical_path")
                after = item["rollback_pointer"]["canonical_path_after"]
                datasets[dataset]["canonical_path"] = after
                datasets[dataset]["updated_at"] = effective_created_at
                catalog_updates.append({"dataset": dataset, "before": before, "after": after})
        tmp = catalog_path.with_name(catalog_path.name + ".tmp")
        tmp.write_text(json.dumps(catalog_after, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(catalog_path)

    copy_write_count = sum(1 for item in copied if item["executed"] and not item["target_preexisted"])
    result = {
        "schema_version": "physical-partition-migration-execution-v1",
        "created_at": effective_created_at,
        "mode": "execute" if execute_copy or update_catalog else "dry_run",
        "approval_id": approval_id,
        "dataset_filter": sorted(selected_datasets) if selected_datasets else [],
        "plan_path": str(plan_file),
        "lake_root": str(lake_root),
        "status": "failed" if errors else "pass",
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
        "post_copy_verifications": verifications,
        "catalog_updates": catalog_updates,
        "operation_counts": {
            **ZERO_COUNTS,
            "lake_write": copy_write_count,
            "physical_partition_migration": copy_write_count,
            "catalog_write": 1 if update_catalog and catalog_updates else 0,
            "current_pointer_publish": len(catalog_updates) if update_catalog else 0,
        },
        "legacy_cleanup_executed": False,
        "nas_sync_executed": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _normalize_dataset_filter(datasets: str | list[str] | tuple[str, ...] | set[str] | None) -> set[str]:
    if datasets is None:
        return set()
    if isinstance(datasets, str):
        raw_values = datasets.split(",")
    else:
        raw_values = []
        for value in datasets:
            raw_values.extend(str(value).split(","))
    return {value.strip() for value in raw_values if value.strip()}


def _verify_copy(source: Path, target: Path, *, dataset: str) -> dict[str, Any]:
    if not target.exists():
        return {
            "dataset": dataset,
            "passed": False,
            "source": str(source),
            "target": str(target),
            "reason": "target_missing",
        }
    if source.is_file() and target.is_file():
        source_size = source.stat().st_size
        target_size = target.stat().st_size
        source_sha256 = _sha256_file(source)
        target_sha256 = _sha256_file(target)
        parquet_ok, parquet_error = _parquet_readable(target)
        return {
            "dataset": dataset,
            "passed": source_size == target_size and source_sha256 == target_sha256 and parquet_ok,
            "source": str(source),
            "target": str(target),
            "source_size_bytes": source_size,
            "target_size_bytes": target_size,
            "source_sha256": source_sha256,
            "target_sha256": target_sha256,
            "parquet_readable": parquet_ok,
            "parquet_error": parquet_error,
        }
    if source.is_dir() and target.is_dir():
        source_files = sorted(path for path in source.rglob("*") if path.is_file())
        target_files = sorted(path for path in target.rglob("*") if path.is_file())
        source_rel = [path.relative_to(source).as_posix() for path in source_files]
        target_rel = [path.relative_to(target).as_posix() for path in target_files]
        file_checks = []
        for rel in source_rel:
            source_file = source / rel
            target_file = target / rel
            if not target_file.exists():
                file_checks.append({"path": rel, "passed": False, "reason": "target_file_missing"})
                continue
            source_size = source_file.stat().st_size
            target_size = target_file.stat().st_size
            source_sha256 = _sha256_file(source_file)
            target_sha256 = _sha256_file(target_file)
            parquet_ok, parquet_error = _parquet_readable(target_file) if target_file.suffix == ".parquet" else (True, None)
            file_checks.append(
                {
                    "path": rel,
                    "passed": source_size == target_size and source_sha256 == target_sha256 and parquet_ok,
                    "source_size_bytes": source_size,
                    "target_size_bytes": target_size,
                    "source_sha256": source_sha256,
                    "target_sha256": target_sha256,
                    "parquet_readable": parquet_ok,
                    "parquet_error": parquet_error,
                }
            )
        return {
            "dataset": dataset,
            "passed": source_rel == target_rel and all(item["passed"] for item in file_checks),
            "source": str(source),
            "target": str(target),
            "source_file_count": len(source_files),
            "target_file_count": len(target_files),
            "source_files": source_rel,
            "target_files": target_rel,
            "file_checks": file_checks,
        }
    return {
        "dataset": dataset,
        "passed": False,
        "source": str(source),
        "target": str(target),
        "reason": "source_target_type_mismatch",
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parquet_readable(path: Path) -> tuple[bool, str | None]:
    if path.suffix != ".parquet":
        return True, None
    try:
        pq.ParquetFile(path).metadata
    except Exception as exc:  # pragma: no cover - defensive corruption path
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute approved copy-first physical partition migration.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--approval-id")
    parser.add_argument("--created-at")
    parser.add_argument("--execute-copy", action="store_true")
    parser.add_argument("--update-catalog", action="store_true")
    parser.add_argument(
        "--datasets",
        action="append",
        help="Optional comma-separated dataset filter. May be repeated.",
    )
    args = parser.parse_args()
    try:
        result = execute_physical_partition_migration(
            plan_path=args.plan,
            out_path=args.out,
            approval_id=args.approval_id,
            created_at=args.created_at,
            execute_copy=args.execute_copy,
            update_catalog=args.update_catalog,
            datasets=args.datasets,
        )
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
