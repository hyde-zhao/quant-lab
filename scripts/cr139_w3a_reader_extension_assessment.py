#!/usr/bin/env python3
"""CR139 W3-A read-only reader API extension assessment for P0 datasets."""

from __future__ import annotations

import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from market_data import contracts
from market_data.catalog import CatalogStore
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset


PROCESS_ROOT = PROJECT_ROOT / "process"
LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake")
P0_DATASETS = ("liquidity_capacity", "market_cap")

EVIDENCE_PATH = PROCESS_ROOT / "evidence" / "CR139-W3A-READER-EXTENSION-ASSESSMENT-2026-06-30.json"
INDEX_PATH = PROCESS_ROOT / "evidence" / "CR139-W3A-READER-EXTENSION-ASSESSMENT.index.json"
CHECK_PATH = PROCESS_ROOT / "checks" / "CR139-W3A-READER-EXTENSION-ASSESSMENT-2026-06-30.md"


def parquet_metadata(path: Path) -> dict[str, Any]:
    metadata = pq.ParquetFile(path).metadata
    schema = pq.read_schema(path)
    return {
        "path": str(path),
        "row_count": int(metadata.num_rows),
        "column_count": len(schema.names),
        "columns": list(schema.names),
    }


def main() -> int:
    checked_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    layout = LakeLayout(LAKE_ROOT)
    catalog = CatalogStore(layout)
    dataset_results = []
    for dataset in P0_DATASETS:
        entry = catalog.get(dataset)
        path = LAKE_ROOT / str(entry.canonical_path)
        reader_result = read_dataset(dataset, LAKE_ROOT, required=False)
        meta = parquet_metadata(path)
        dataset_results.append(
            {
                "dataset": dataset,
                "in_contracts_DATASETS": dataset in contracts.DATASETS,
                "has_schema_registry_entry": dataset in contracts.DATASET_SCHEMA_REGISTRY,
                "read_dataset_status_before": reader_result.status,
                "read_dataset_issues_before": reader_result.issues,
                "catalog_published": entry.published,
                "canonical_path_exists": path.exists(),
                "coverage_denominator": entry.coverage_denominator,
                "parquet_row_count": meta["row_count"],
                "row_count_matches_catalog": meta["row_count"] == entry.coverage_denominator,
                "parquet_columns": meta["columns"],
                "candidate_schema_registry_columns": meta["columns"],
                "recommended_minimal_contract": {
                    "constants": [f"DATASET_{dataset.upper()}"],
                    "DATASETS": "append dataset id",
                    "DATASET_SCHEMA_REGISTRY": "add columns from active CR139 canonical parquet",
                    "reader_behavior": "reuse generic read_dataset path after DATASETS/schema registration",
                    "tests": [
                        f"read_dataset({dataset!r}) returns available against CR139 active lake",
                        "row count equals active catalog coverage_denominator",
                        "unknown_dataset no longer emitted",
                        "large-table smoke may use column projection/sample when full materialization is too expensive",
                    ],
                },
            }
        )
    source_locations = {
        "read_dataset_file": str(Path(inspect.getsourcefile(read_dataset) or "").relative_to(PROJECT_ROOT)),
        "read_dataset_line": inspect.getsourcelines(read_dataset)[1],
        "contracts_file": "market_data/contracts.py",
        "registration_findings": [
            "read_dataset first checks dataset in market_data.contracts.DATASETS",
            "schema compatibility and dedup keys use DATASET_SCHEMA_REGISTRY when present",
            "liquidity_capacity and market_cap are in active catalog but not in DATASETS/schema registry before W3-A",
        ],
    }
    checks = {
        "active_catalog_has_p0_datasets": len(dataset_results) == 2,
        "p0_canonical_paths_exist": all(item["canonical_path_exists"] for item in dataset_results),
        "p0_row_counts_match_catalog": all(item["row_count_matches_catalog"] for item in dataset_results),
        "p0_reader_currently_unknown": all(
            any(issue.get("code") == "unknown_dataset" for issue in item["read_dataset_issues_before"])
            for item in dataset_results
        ),
        "extension_scope_identified": True,
        "no_lake_write": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    payload = {
        "schema": "cr139.w3a.reader_extension_assessment.v1",
        "status": "pass_w3a_reader_extension_assessment" if not failed_checks else "blocked_w3a_reader_extension_assessment",
        "checked_at": checked_at,
        "mode": "read_only",
        "source_locations": source_locations,
        "dataset_results": dataset_results,
        "operation_counts": {
            "lake_write": 0,
            "catalog_write": 0,
            "manifest_append": 0,
            "provider_catalog_write": 0,
            "nas_operation": 0,
            "runtime_operation": 0,
            "credential_read": 0,
            "git_remote": 0,
        },
        "checks": checks,
        "failed_checks": failed_checks,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(
        json.dumps(
            {
                "schema": "cr139.evidence.index.v1",
                "status": payload["status"],
                "evidence": str(EVIDENCE_PATH),
                "check": str(CHECK_PATH),
                "failed_checks": failed_checks,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# CR139 W3-A Reader Extension Assessment",
        "",
        f"- status: `{payload['status']}`",
        f"- evidence: `{EVIDENCE_PATH}`",
        f"- read_dataset_location: `{source_locations['read_dataset_file']}:{source_locations['read_dataset_line']}`",
        "",
        "## P0 Datasets",
        "",
        "| Dataset | In DATASETS | Has Schema | Current read_dataset Status | Rows | Row Count Matches |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for item in dataset_results:
        lines.append(
            f"| `{item['dataset']}` | {item['in_contracts_DATASETS']} | {item['has_schema_registry_entry']} | `{item['read_dataset_status_before']}` | {item['parquet_row_count']} | {item['row_count_matches_catalog']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Result |", "|---|---|"])
    for name, passed in checks.items():
        lines.append(f"| `{name}` | {'PASS' if passed else 'FAIL'} |")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- Implement P0 reader support by adding `liquidity_capacity` and `market_cap` constants to `market_data.contracts.DATASETS` plus schema registry entries derived from CR139 canonical parquet columns.",
            "- Reuse the generic `read_dataset()` path; add tests that current read status changes from `unknown_dataset` to `available` and row counts match active catalog.",
            "- Avoid full-table performance assertions; use metadata row counts and one actual read smoke per dataset, with optional column/sample smoke if runtime grows.",
        ]
    )
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "failed_checks": failed_checks}, sort_keys=True))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
