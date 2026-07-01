#!/usr/bin/env python
"""Collect read-only data lake reader smoke evidence from stable APIs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.catalog import CatalogStore
from market_data.contracts import DATASETS
from market_data.lake_layout import LakeLayout
from market_data.readers import QualityPolicy, read_dataset


OPERATION_COUNTS = {
    "catalog_write": 0,
    "credential_read": 0,
    "current_pointer_publish": 0,
    "git_remote_write": 0,
    "lake_write": 0,
    "legacy_delete_or_archive": 0,
    "nas_operation": 0,
    "physical_partition_migration": 0,
    "provider_fetch": 0,
    "runtime_operation": 0,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect read-only current-layout reader smoke evidence.")
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--created-at", required=True)
    args = parser.parse_args()

    lake_root = Path(args.lake_root)
    layout = LakeLayout(lake_root)
    catalog = CatalogStore(layout)
    catalog_payload = json.loads((lake_root / "catalog" / "catalog.json").read_text())
    dataset_names = sorted(catalog_payload.get("datasets", {}))
    supported = set(DATASETS)

    catalog_checks: list[dict[str, Any]] = []
    reader_checks: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for dataset in dataset_names:
        entry = catalog.get(dataset)
        canonical_path = str(entry.canonical_path or "")
        physical_path = lake_root / canonical_path
        uses_current_layout = "/current/" in canonical_path or canonical_path.endswith("/current")
        exists = physical_path.exists()
        catalog_check = {
            "dataset": dataset,
            "canonical_path": canonical_path,
            "exists": exists,
            "published": bool(entry.published),
            "quality_status": entry.quality_status,
            "readiness_status": entry.readiness_status,
            "uses_current_layout": uses_current_layout,
        }
        catalog_checks.append(catalog_check)
        if not exists or not uses_current_layout:
            failures.append({"dataset": dataset, "code": "catalog_current_path_invalid", **catalog_check})

        if dataset not in supported:
            reader_checks.append(
                {
                    "dataset": dataset,
                    "executed": False,
                    "reason": "dataset_not_in_reader_contract",
                    "catalog_path_smoke_only": True,
                }
            )
            continue

        result = read_dataset(dataset, lake_root=lake_root, required=True)
        effective_result = result
        allow_warn_status = None
        allow_warn_row_count = None
        allow_warn_issue_codes: list[str] = []
        default_issue_codes = [str(issue.get("code")) for issue in result.issues]
        conditional_reader_support = (
            dataset == "industry_classification"
            and result.status == "unavailable"
            and {"readiness_not_available", "non_pit_snapshot"}.issubset(set(default_issue_codes))
        )
        if conditional_reader_support:
            allow_warn_result = read_dataset(
                dataset,
                lake_root=lake_root,
                required=True,
                quality_policy=QualityPolicy(allow_warn=True),
            )
            allow_warn_status = allow_warn_result.status
            allow_warn_row_count = len(allow_warn_result.frame) if allow_warn_result.frame is not None else None
            allow_warn_issue_codes = [str(issue.get("code")) for issue in allow_warn_result.issues]
            if allow_warn_result.status == "available":
                effective_result = allow_warn_result

        row_count = len(effective_result.frame) if effective_result.frame is not None else None
        reader_check = {
            "dataset": dataset,
            "executed": True,
            "status": effective_result.status,
            "default_status": result.status,
            "available": effective_result.available,
            "row_count": row_count,
            "default_issue_codes": default_issue_codes,
            "issue_codes": [str(issue.get("code")) for issue in effective_result.issues],
            "allow_warn_status": allow_warn_status,
            "allow_warn_row_count": allow_warn_row_count,
            "allow_warn_issue_codes": allow_warn_issue_codes,
            "conditional_reader_support": conditional_reader_support and effective_result.available,
            "catalog_path": str(effective_result.catalog_entry.canonical_path)
            if effective_result.catalog_entry
            else canonical_path,
            "uses_current_layout": (
                effective_result.catalog_entry is not None
                and (
                    "/current/" in str(effective_result.catalog_entry.canonical_path)
                    or str(effective_result.catalog_entry.canonical_path).endswith("/current")
                )
            ),
        }
        reader_checks.append(reader_check)
        if effective_result.status != "available" or not reader_check["uses_current_layout"]:
            failures.append({"dataset": dataset, "code": "reader_smoke_failed", **reader_check})

    payload = {
        "schema_version": "cr146.reader_runtime_smoke.v2",
        "created_at": args.created_at,
        "lake_root": str(lake_root),
        "status": "pass" if not failures else "fail",
        "summary": {
            "catalog_dataset_count": len(catalog_checks),
            "catalog_current_path_count": sum(1 for item in catalog_checks if item["uses_current_layout"]),
            "catalog_physical_exists_count": sum(1 for item in catalog_checks if item["exists"]),
            "reader_executed_count": sum(1 for item in reader_checks if item["executed"]),
            "reader_available_count": sum(
                1 for item in reader_checks if item.get("executed") and item.get("status") == "available"
            ),
            "reader_skipped_count": sum(1 for item in reader_checks if not item["executed"]),
            "failure_count": len(failures),
        },
        "catalog_checks": catalog_checks,
        "reader_checks": reader_checks,
        "failures": failures,
        "operation_counts": dict(OPERATION_COUNTS),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": payload["status"], **payload["summary"]}, indent=2, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
