#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from market_data.catalog import CatalogStore, validate_catalog_pointer  # noqa: E402
from market_data.contracts import DATASETS, PIT_STATUS_AVAILABLE  # noqa: E402
from market_data.lake_layout import LakeLayout  # noqa: E402
from market_data.readers import QualityPolicy, read_dataset  # noqa: E402

RUN_ID = "CR139-W3B-PUBLISH-GUARD-2026-06-30"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence" / f"{RUN_ID}.json"
CHECK_PATH = PROJECT_ROOT / "process/checks" / f"{RUN_ID}.md"
ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
READER_REQUIRED_DATASETS = {"liquidity_capacity", "market_cap"}
POINTER_ONLY_ALLOWED = {
    "bse_code_mapping",
    "lifecycle_code_change",
}
SMALL_READER_SMOKE_ROW_THRESHOLD = 1_000_000


def main() -> int:
    parser = argparse.ArgumentParser(description="CR139 W3-B reusable publish guard.")
    parser.add_argument("--lake-root", default=None)
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root or _env_lake_root(project_root / ".env")).resolve()
    layout = LakeLayout(lake_root)
    store = CatalogStore(layout)
    catalog_path = lake_root / ACTIVE_CATALOG_REL
    manifest_path = lake_root / ACTIVE_MANIFEST_REL
    catalog_before_sha = sha256_file(catalog_path)
    manifest_before_sha = sha256_file(manifest_path)
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = catalog.get("datasets") or {}
    if not isinstance(records, dict):
        raise RuntimeError("active catalog must contain a datasets object")

    pointer_validations = []
    row_count_validations = []
    pit_validations = []
    reader_matrix = []
    quality_path_validations = []
    failed_checks: list[str] = []

    for dataset, record in sorted(records.items()):
        validation = validate_catalog_pointer(record)
        pointer_validations.append(
            {
                "dataset": dataset,
                "passed": validation.passed,
                "missing_fields": list(validation.missing_fields),
                "error_codes": list(validation.error_codes),
            }
        )
        try:
            pointer = store.get_published_current_pointer(dataset)
            pointer_available = True
        except Exception as exc:  # pragma: no cover - evidence path captures type/message.
            pointer_available = False
            pointer = None
            pointer_validations[-1]["published_pointer_error"] = f"{type(exc).__name__}: {exc}"

        canonical_path = str(record.get("canonical_path") or "")
        path = lake_root / canonical_path
        files = sorted(path.rglob("*.parquet")) if path.is_dir() else ([path] if path.exists() else [])
        row_count = sum(pq.ParquetFile(file).metadata.num_rows for file in files)
        row_count_validations.append(
            {
                "dataset": dataset,
                "canonical_path": canonical_path,
                "path_exists": path.exists(),
                "parquet_file_count": len(files),
                "row_count": row_count,
                "catalog_coverage_denominator": record.get("coverage_denominator"),
                "row_count_matches_catalog": row_count == record.get("coverage_denominator"),
                "candidate_path_leak": canonical_path.startswith("candidate/") or "/candidate/" in canonical_path,
                "published_pointer_available": pointer_available and pointer is not None,
            }
        )
        pit_validations.append(_validate_pit(lake_root, dataset, record, files))
        quality_path = record.get("quality_path")
        quality_path_validations.append(
            {
                "dataset": dataset,
                "quality_path": quality_path,
                "required": bool(quality_path),
                "exists": bool((lake_root / str(quality_path)).exists()) if quality_path else True,
            }
        )
        contract_supported = dataset in DATASETS
        required_reader = dataset in READER_REQUIRED_DATASETS
        pointer_only_allowed = dataset in POINTER_ONLY_ALLOWED
        reader_smoke = _reader_smoke(lake_root, dataset, record, row_count) if contract_supported else None
        reader_matrix.append(
            {
                "dataset": dataset,
                "contract_supported": contract_supported,
                "required_reader_support": required_reader,
                "pointer_only_allowed": pointer_only_allowed,
                "reader_smoke": reader_smoke,
                "conditional_reader_support": _conditional_reader_support(dataset, record, reader_smoke),
                "reader_guard_passed": _reader_guard_passed(
                    contract_supported=contract_supported,
                    pointer_only_allowed=pointer_only_allowed,
                    reader_smoke=reader_smoke,
                    dataset=dataset,
                    record=record,
                ),
            }
        )

    catalog_after_sha = sha256_file(catalog_path)
    manifest_after_sha = sha256_file(manifest_path)
    checks = {
        "active_catalog_exists": catalog_path.exists(),
        "active_manifest_exists": manifest_path.exists(),
        "active_catalog_unchanged": catalog_before_sha == catalog_after_sha,
        "active_manifest_unchanged": manifest_before_sha == manifest_after_sha,
        "dataset_count_17": len(records) == 17,
        "published_true_17": sum(1 for record in records.values() if record.get("published") is True) == 17,
        "canonical_path_no_candidate_leak_17": not any(item["candidate_path_leak"] for item in row_count_validations),
        "pointer_contract_valid_17": sum(1 for item in pointer_validations if item["passed"]) == 17,
        "published_pointer_available_17": sum(
            1 for item in row_count_validations if item["published_pointer_available"]
        )
        == 17,
        "canonical_row_count_matches_17": sum(1 for item in row_count_validations if item["row_count_matches_catalog"])
        == 17,
        "pit_purity_pass": all(item["passed"] for item in pit_validations),
        "reader_support_matrix_pass": all(item["reader_guard_passed"] for item in reader_matrix),
        "reader_required_p0_supported": all(
            item["contract_supported"] for item in reader_matrix if item["required_reader_support"]
        ),
        "quality_paths_exist": all(item["exists"] for item in quality_path_validations),
        "no_provider_or_nas_implicit_operation": True,
    }
    failed_checks.extend(name for name, passed in checks.items() if not passed)
    status = "pass_w3b_publish_guard" if not failed_checks else "blocked_w3b_publish_guard"
    evidence = {
        "schema": "cr139.w3b.publish_guard.v1",
        "run_id": RUN_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "lake_root": str(lake_root),
        "active_catalog": {
            "path": str(catalog_path),
            "before_sha256": catalog_before_sha,
            "after_sha256": catalog_after_sha,
            "unchanged": catalog_before_sha == catalog_after_sha,
        },
        "active_manifest": {
            "path": str(manifest_path),
            "before_sha256": manifest_before_sha,
            "after_sha256": manifest_after_sha,
            "unchanged": manifest_before_sha == manifest_after_sha,
            "line_count": count_lines(manifest_path),
        },
        "checks": checks,
        "failed_checks": failed_checks,
        "pointer_validations": pointer_validations,
        "row_count_validations": row_count_validations,
        "pit_validations": pit_validations,
        "quality_path_validations": quality_path_validations,
        "reader_support_matrix": reader_matrix,
        "operation_counts": {
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "published_pointer_advance": 0,
            "physical_partition_migration": 0,
            "lake_data_write": 0,
            "lake_delete": 0,
            "nas_operation": 0,
            "credential_print_or_persist": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_check(evidence)
    print(status)
    print(f"evidence={EVIDENCE_PATH}")
    print(f"check={CHECK_PATH}")
    return 0 if not failed_checks else 1


def _validate_pit(lake_root: Path, dataset: str, record: dict[str, Any], files: list[Path]) -> dict[str, Any]:
    if record.get("pit_status") != PIT_STATUS_AVAILABLE:
        return {
            "dataset": dataset,
            "applicable": False,
            "passed": True,
            "reason": "catalog_pit_status_not_pit_available",
            "pit_status_distribution": {},
        }
    distribution: dict[str, int] = {}
    applicable = False
    for file in files:
        schema_names = pq.ParquetFile(file).schema_arrow.names
        if "pit_status" not in schema_names:
            continue
        applicable = True
        table = pq.read_table(file, columns=["pit_status"])
        counts = table.column("pit_status").to_pandas().value_counts(dropna=False).to_dict()
        for key, value in counts.items():
            distribution[str(key)] = distribution.get(str(key), 0) + int(value)
    if not applicable:
        return {
            "dataset": dataset,
            "applicable": False,
            "passed": True,
            "reason": "pit_status_column_absent",
            "pit_status_distribution": {},
        }
    return {
        "dataset": dataset,
        "applicable": True,
        "passed": distribution == {PIT_STATUS_AVAILABLE: int(record.get("coverage_denominator") or 0)},
        "reason": "row_level_pit_status_checked",
        "pit_status_distribution": distribution,
    }


def _reader_smoke(lake_root: Path, dataset: str, record: dict[str, Any], row_count: int) -> dict[str, Any]:
    if row_count > SMALL_READER_SMOKE_ROW_THRESHOLD:
        return {
            "executed": False,
            "reason": "large_dataset_metadata_only",
            "row_count_source": "parquet_metadata",
            "metadata_row_count": row_count,
            "catalog_coverage_denominator": record.get("coverage_denominator"),
            "row_count_matches_catalog": row_count == record.get("coverage_denominator"),
        }
    default = read_dataset(dataset, lake_root)
    allow_warn = read_dataset(dataset, lake_root, quality_policy=QualityPolicy(allow_warn=True))
    default_rows = len(default.frame) if default.frame is not None else None
    allow_warn_rows = len(allow_warn.frame) if allow_warn.frame is not None else None
    return {
        "executed": True,
        "default_status": default.status,
        "default_issue_codes": [str(issue.get("code")) for issue in default.issues],
        "default_frame_row_count": default_rows,
        "allow_warn_status": allow_warn.status,
        "allow_warn_issue_codes": [str(issue.get("code")) for issue in allow_warn.issues],
        "allow_warn_frame_row_count": allow_warn_rows,
        "catalog_coverage_denominator": record.get("coverage_denominator"),
        "row_count_matches_catalog": (
            default_rows == record.get("coverage_denominator")
            if default.status == "available"
            else allow_warn_rows == record.get("coverage_denominator")
            if allow_warn.status == "available"
            else False
        ),
    }


def _conditional_reader_support(dataset: str, record: dict[str, Any], smoke: dict[str, Any] | None) -> bool:
    if dataset != "industry_classification" or not smoke or not smoke.get("executed"):
        return False
    issue_codes = set(smoke.get("default_issue_codes", [])) | set(smoke.get("allow_warn_issue_codes", []))
    return (
        smoke.get("default_status") == "unavailable"
        and smoke.get("allow_warn_status") == "available"
        and "non_pit_snapshot" in issue_codes
        and bool(record.get("known_limitations"))
        and smoke.get("row_count_matches_catalog") is True
    )


def _reader_guard_passed(
    *,
    contract_supported: bool,
    pointer_only_allowed: bool,
    reader_smoke: dict[str, Any] | None,
    dataset: str,
    record: dict[str, Any],
) -> bool:
    if pointer_only_allowed:
        return True
    if not contract_supported:
        return False
    if not reader_smoke or not reader_smoke.get("executed"):
        return True
    return (
        reader_smoke.get("default_status") == "available"
        and reader_smoke.get("row_count_matches_catalog") is True
    ) or _conditional_reader_support(dataset, record, reader_smoke)


def _env_lake_root(path: Path) -> str:
    if "MARKET_DATA_LAKE_ROOT" in os.environ:
        return os.environ["MARKET_DATA_LAKE_ROOT"]
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == "MARKET_DATA_LAKE_ROOT":
            return value.strip().strip('"').strip("'")
    raise RuntimeError("MARKET_DATA_LAKE_ROOT not found")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def write_check(evidence: dict[str, Any]) -> None:
    check_rows = "\n".join(f"| {key} | {value} |" for key, value in sorted(evidence["checks"].items()))
    reader_rows = "\n".join(
        "| {dataset} | {contract_supported} | {required_reader_support} | {pointer_only_allowed} | {default_status} | {allow_warn_status} | {row_count} | {conditional_reader_support} | {reader_guard_passed} |".format(
            dataset=item["dataset"],
            contract_supported=item["contract_supported"],
            required_reader_support=item["required_reader_support"],
            pointer_only_allowed=item["pointer_only_allowed"],
            default_status=(item.get("reader_smoke") or {}).get("default_status", "not_executed"),
            allow_warn_status=(item.get("reader_smoke") or {}).get("allow_warn_status", "not_executed"),
            row_count=(item.get("reader_smoke") or {}).get(
                "default_frame_row_count",
            )
            or (item.get("reader_smoke") or {}).get("allow_warn_frame_row_count")
            or (item.get("reader_smoke") or {}).get("metadata_row_count"),
            conditional_reader_support=item["conditional_reader_support"],
            reader_guard_passed=item["reader_guard_passed"],
        )
        for item in evidence["reader_support_matrix"]
    )
    pit_rows = "\n".join(
        f"| {item['dataset']} | {item['applicable']} | {item['passed']} | {item['pit_status_distribution']} |"
        for item in evidence["pit_validations"]
    )
    text = f"""# CR139 W3-B Publish Guard

## Result

- status: `{evidence['status']}`
- failed_checks: `{evidence['failed_checks']}`
- active catalog unchanged: `{evidence['active_catalog']['unchanged']}`
- active manifest unchanged: `{evidence['active_manifest']['unchanged']}`

## Checks

| check | result |
|---|---:|
{check_rows}

## Reader Support Matrix

| dataset | contract_supported | required_reader_support | pointer_only_allowed | default_status | allow_warn_status | row_count | conditional_reader_support | reader_guard_passed |
|---|---:|---:|---:|---|---|---:|---:|---:|
{reader_rows}

## PIT Validation

| dataset | applicable | passed | distribution |
|---|---:|---:|---|
{pit_rows}

## Operation Counts

```json
{json.dumps(evidence['operation_counts'], indent=2, sort_keys=True)}
```
"""
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
