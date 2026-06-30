#!/usr/bin/env python
"""CR139 Gate B Batch 2 split candidate writer for remaining large datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.lake_layout import build_cr139_run_id, validate_cr139_run_id

SCHEMA_VERSION = "1.0"
KEY = ["symbol", "trade_date"]
METADATA_COLUMNS = {
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
}
EXPECTED = {
    "prices": {
        "source": 28_646_730,
        "main": 17_013_700,
        "quarantine": 401_628,
        "dropped": 11_231_402,
        "metadata_groups": 1_830,
        "business_groups": 79_958,
        "schema_policy": "union_schema_null_fill",
    },
    "prices_limit": {
        "source": 40_962_525,
        "main": 19_210_017,
        "quarantine": 11_841_929,
        "dropped": 9_910_579,
        "metadata_groups": 6_946_008,
        "business_groups": 499_787,
        "schema_policy": "single_schema",
    },
    "trade_status": {
        "source": 21_569_907,
        "main": 13_957_403,
        "quarantine": 7_612_504,
        "dropped": 0,
        "metadata_groups": 70_087,
        "business_groups": 3_692_105,
        "schema_policy": "single_schema",
    },
}
OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 2,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "physical_partition_migration": 0,
    "credential_read": 0,
    "nas_operation": 0,
    "runtime_operation": 0,
    "git_remote_write": 0,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=sorted(EXPECTED))
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()

    dataset = args.dataset
    expected = EXPECTED[dataset]
    lake_root = Path(args.lake_root).expanduser().resolve()
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    run_id = build_cr139_run_id(
        dataset=dataset,
        source="legacy_lake",
        as_of_date="2026-06-29",
        purpose="canonical",
    )
    if not validate_cr139_run_id(run_id):
        raise RuntimeError(f"Invalid CR139 run_id: {run_id}")

    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    stamp = stamp_for(dataset)
    source_root = lake_root / "canonical" / dataset / SCHEMA_VERSION
    target_root = lake_root / "candidate" / "parquet" / f"dataset={dataset}" / f"schema_version={SCHEMA_VERSION}" / f"run_id={run_id}"
    quarantine_root = target_root / "quarantine"
    main_path = target_root / f"part-{dataset.replace('_', '-')}.parquet"
    quarantine_path = quarantine_root / f"part-{dataset.replace('_', '-')}-conflict-and-superseded.parquet"
    if target_root.exists():
        raise RuntimeError(f"Target candidate root already exists: {target_root}")

    pre_snapshot = snapshot(lake_root, target_root, dataset)
    source, schema_info = read_source(source_root)
    materialized = materialize(dataset, source)
    main_frame = materialized["main"]
    quarantine_frame = materialized["quarantine"]
    metrics = duplicate_metrics(main_frame)

    assert_expected(dataset, expected, source, main_frame, quarantine_frame, materialized, metrics)

    target_root.mkdir(parents=True, exist_ok=False)
    quarantine_root.mkdir(parents=True, exist_ok=False)
    main_frame.to_parquet(main_path, index=False)
    quarantine_frame.to_parquet(quarantine_path, index=False)

    objects = [
        object_record(dataset, "main", main_path, lake_root, len(main_frame), "additive_only_split_main"),
        object_record(
            dataset,
            "quarantine",
            quarantine_path,
            lake_root,
            len(quarantine_frame),
            "additive_only_business_conflict_and_superseded_quarantine",
        ),
    ]
    post_snapshot = snapshot(lake_root, target_root, dataset)
    zero_mutation = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": f"{dataset}_zero_mutation_proof",
        "created_at": created_at,
        "catalog_hash_unchanged": pre_snapshot["catalog_tree_hash"] == post_snapshot["catalog_tree_hash"],
        "published_tree_hash_unchanged": pre_snapshot["published_tree_hash"] == post_snapshot["published_tree_hash"],
        "canonical_dataset_tree_hash_unchanged": pre_snapshot["canonical_dataset_tree_hash"] == post_snapshot["canonical_dataset_tree_hash"],
        "catalog_write": 0,
        "current_pointer_publish": 0,
        "physical_partition_migration": 0,
        "result": "pass",
    }
    if not all(
        zero_mutation[key]
        for key in ("catalog_hash_unchanged", "published_tree_hash_unchanged", "canonical_dataset_tree_hash_unchanged")
    ):
        raise RuntimeError(f"zero mutation proof failed: {zero_mutation}")

    manifest = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": f"{dataset}_object_manifest",
        "created_at": created_at,
        "write_mode": "additive_only_split_candidate",
        "dataset": dataset,
        "run_id": run_id,
        "objects": objects,
        "operation_counts": dict(OPERATION_COUNTS),
    }
    rollback_manifest = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": f"{dataset}_rollback_manifest",
        "created_at": created_at,
        "rollback_not_authorized": True,
        "allowed_future_rollback_if_authorized": f"delete only the two {dataset} candidate objects listed here; do not delete legacy/canonical/catalog/published",
        "objects": objects,
    }
    summary = {
        "source_row_count": int(len(source)),
        "main_row_count": int(len(main_frame)),
        "quarantine_row_count": int(len(quarantine_frame)),
        "dropped_exact_duplicate_row_count": int(materialized["dropped_exact_duplicate_row_count"]),
        "metadata_only_group_count": int(materialized["metadata_only_group_count"]),
        "business_conflict_group_count": int(materialized["business_conflict_group_count"]),
        "business_conflict_quarantine_row_count": int(materialized["business_conflict_quarantine_row_count"]),
        "metadata_superseded_quarantine_row_count": int(materialized["metadata_superseded_quarantine_row_count"]),
        "main_duplicate_row_over_unique_count": metrics["duplicate_row_over_unique_count"],
        "accounted_row_count": int(
            len(main_frame) + len(quarantine_frame) + materialized["dropped_exact_duplicate_row_count"]
        ),
    }
    index = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": f"batch2_{dataset}_candidate_write_execution",
        "created_at": created_at,
        "status": f"pass_with_risk_{dataset}_candidate_write_verified",
        "authorized_scope": f"Gate B Batch 2 {dataset} split candidate write only; exact-copy dedup, metadata-only resolved, business-conflict full quarantine",
        "dataset": dataset,
        "run_id": run_id,
        "schema_policy": expected["schema_policy"],
        "schema_info": schema_info,
        "dataset_results_summary": summary,
        "source_precedence": {
            "rule": precedence_rule(dataset),
            "business_conflict_groups_quarantined": int(materialized["business_conflict_group_count"]),
        },
        "object_count": len(objects),
        "operation_counts": dict(OPERATION_COUNTS),
        "checks": {
            "target_absent_before_write": pre_snapshot["target_exists"] is False,
            "source_rows_expected": len(source) == expected["source"],
            "main_rows_expected": len(main_frame) == expected["main"],
            "quarantine_rows_expected": len(quarantine_frame) == expected["quarantine"],
            "dropped_exact_duplicates_expected": materialized["dropped_exact_duplicate_row_count"] == expected["dropped"],
            "metadata_only_groups_expected": materialized["metadata_only_group_count"] == expected["metadata_groups"],
            "business_conflict_groups_expected": materialized["business_conflict_group_count"] == expected["business_groups"],
            "main_has_no_duplicate_keys": metrics["duplicate_row_over_unique_count"] == 0,
            "zero_mutation_pass": zero_mutation["result"] == "pass",
            "rollback_not_authorized": True,
        },
        "failed_checks": [],
        "evidence_refs": {
            "preexecution_snapshot": f"process/evidence/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}-PREEXECUTION-SNAPSHOT.json",
            "postexecution_snapshot": f"process/evidence/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}-POSTEXECUTION-SNAPSHOT.json",
            "object_manifest": f"process/evidence/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}-OBJECT-MANIFEST.json",
            "rollback_manifest": f"process/evidence/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}-ROLLBACK-MANIFEST.json",
            "zero_mutation": f"process/evidence/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}-ZERO-MUTATION-PROOF.json",
            "execution_check": f"process/checks/CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-2026-06-29.md",
        },
        "non_authorized_scope": [
            "all other datasets",
            "catalog write",
            "provider catalog write",
            "provider-lake-catalog write",
            "published pointer advance",
            "physical partition migration",
            "credential read",
            "NAS operation",
            "runtime operation",
            "QMT/MiniQMT/gateway runtime",
            "trading/small_live/live",
            "Git remote write",
            "legacy deletion",
            "rollback deletion",
        ],
        "next_gate": next_gate(dataset),
    }

    prefix = evidence_dir / f"CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION-{stamp}"
    write_json(Path(f"{prefix}-PREEXECUTION-SNAPSHOT.json"), pre_snapshot)
    write_json(Path(f"{prefix}-POSTEXECUTION-SNAPSHOT.json"), post_snapshot)
    write_json(Path(f"{prefix}-OBJECT-MANIFEST.json"), manifest)
    write_json(Path(f"{prefix}-ROLLBACK-MANIFEST.json"), rollback_manifest)
    write_json(Path(f"{prefix}-ZERO-MUTATION-PROOF.json"), zero_mutation)
    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-{dataset.upper()}-WRITE-EXECUTION.index.json", index)
    return 0


def read_source(source_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    paths = sorted(source_root.rglob("*.parquet"))
    if not paths:
        raise FileNotFoundError(source_root)
    union_columns: list[str] = []
    schema_counts: dict[tuple[str, ...], int] = {}
    for path in paths:
        columns = tuple(pq.read_schema(path).names)
        schema_counts[columns] = schema_counts.get(columns, 0) + 1
        for column in columns:
            if column not in union_columns:
                union_columns.append(column)
    frames = []
    for path in paths:
        present = pq.read_schema(path).names
        frame = pq.read_table(path, columns=present).to_pandas()
        for column in union_columns:
            if column not in frame.columns:
                frame[column] = pd.NA
        frame = frame.loc[:, union_columns]
        frame["_source_file"] = str(path)
        frame["_source_row_number"] = range(len(frame))
        frames.append(frame)
    schema_info = {
        "schema_variant_count": len(schema_counts),
        "union_columns": union_columns,
        "schema_variants": [
            {
                "file_count": count,
                "columns": list(columns),
                "missing_from_union": [column for column in union_columns if column not in columns],
            }
            for columns, count in schema_counts.items()
        ],
    }
    return pd.concat(frames, ignore_index=True, copy=False), schema_info


def materialize(dataset: str, source: pd.DataFrame) -> dict[str, Any]:
    business_columns = [
        column
        for column in source.columns
        if column not in set(KEY) | METADATA_COLUMNS | {"_source_file", "_source_row_number"}
    ]
    output_columns = [column for column in source.columns if column not in {"_source_file", "_source_row_number"}]
    frame = source.copy()
    frame["_business_hash"] = pd.util.hash_pandas_object(frame[business_columns].astype(str), index=False)
    metadata_columns = [column for column in frame.columns if column in METADATA_COLUMNS]
    frame["_metadata_hash"] = pd.util.hash_pandas_object(frame[metadata_columns].astype(str), index=False)
    group = frame.groupby(KEY, dropna=False, sort=False)
    frame["_group_size"] = group["_business_hash"].transform("size")
    frame["_business_nunique"] = group["_business_hash"].transform("nunique")
    frame["_metadata_nunique"] = group["_metadata_hash"].transform("nunique")
    frame["_source_priority"] = frame["source_run_id"].astype(str).map(lambda value: source_priority(dataset, value))
    frame = frame.sort_values([*KEY, "_source_priority", "source_run_id", "_source_file", "_source_row_number"], kind="mergesort")

    non_duplicate = frame[frame["_group_size"] == 1]
    exact_duplicate = frame[(frame["_group_size"] > 1) & (frame["_business_nunique"] == 1) & (frame["_metadata_nunique"] == 1)]
    metadata_only = frame[(frame["_group_size"] > 1) & (frame["_business_nunique"] == 1) & (frame["_metadata_nunique"] > 1)]
    business_conflict = frame[(frame["_group_size"] > 1) & (frame["_business_nunique"] > 1)]
    exact_main = exact_duplicate.drop_duplicates(KEY, keep="first")
    metadata_main = metadata_only.drop_duplicates(KEY, keep="first")
    selected_metadata_index = set(metadata_main.index)
    metadata_quarantine = metadata_only[~metadata_only.index.isin(selected_metadata_index)]
    main_frame = pd.concat([non_duplicate, exact_main, metadata_main], ignore_index=True, copy=False)
    quarantine_frame = pd.concat([metadata_quarantine, business_conflict], ignore_index=True, copy=False)
    return {
        "main": main_frame.loc[:, output_columns].sort_values(KEY, kind="mergesort").reset_index(drop=True),
        "quarantine": quarantine_frame.loc[:, output_columns].sort_values(KEY, kind="mergesort").reset_index(drop=True),
        "dropped_exact_duplicate_row_count": int(len(exact_duplicate) - len(exact_main)),
        "metadata_only_group_count": int(len(metadata_main)),
        "business_conflict_group_count": int(business_conflict.groupby(KEY, dropna=False).ngroups),
        "business_conflict_quarantine_row_count": int(len(business_conflict)),
        "metadata_superseded_quarantine_row_count": int(len(metadata_quarantine)),
    }


def source_priority(dataset: str, source_run_id: object) -> tuple[int, str]:
    text = str(source_run_id)
    if dataset == "prices":
        prefixes = [
            "run-stage3-data-update-20260530-20260626-prices-20260627",
            "run-cr018-release-full-history-20150101-20260528-20260529",
            "run-cr014-s14-prices-adj-factor-",
            "cr010-prod-window-20250211-20260218-prices-adj-tushare",
            "cr006-momentum-symbols-realrun",
        ]
    elif dataset == "prices_limit":
        prefixes = [
            "run-stage3-data-update-20260530-20260626-aux-20260627",
            "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529",
            "run-cr034-chapter3-constraints-2000-2019",
            "run-cr034-chapter3-w3-2000-2014",
            "cr010-tushare-only-window-20250211-20260218-prices-limit",
            "cr010-prod-window-20250211-20260218-prices-limit-jqdata",
        ]
    else:
        prefixes = [
            "run-stage3-data-update-20260530-20260626-trade-status-20260627",
            "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529",
            "run-cr034-chapter3-constraints-2000-2019",
            "cr010-tushare-only-window-20250211-20260218-trade-status",
            "cr010-prod-window-20250211-20260218-trade-status-jqdata",
        ]
    for index, prefix in enumerate(prefixes):
        if text.startswith(prefix):
            return (index, text)
    if "smoke" in text:
        return (90, text)
    return (80, text)


def precedence_rule(dataset: str) -> str:
    if dataset == "prices":
        return "prefer stage3 prices lineage, then CR018 full-history, then CR014 S14 prices/adj-factor lineage; business-conflict groups are fully quarantined"
    if dataset == "prices_limit":
        return "prefer stage3 aux/prices_limit lineage, then CR018 backfill, then chapter3 constraints; business-conflict groups are fully quarantined"
    return "prefer stage3 trade-status lineage, then CR018 backfill, then chapter3 constraints; business-conflict groups are fully quarantined"


def next_gate(dataset: str) -> str:
    if dataset == "prices":
        return "review prices write evidence; continue prices_limit single-dataset write"
    if dataset == "prices_limit":
        return "review prices_limit write evidence; continue trade_status single-dataset write"
    return "review trade_status write evidence; Gate B candidate writes complete pending integrated review"


def assert_expected(
    dataset: str,
    expected: dict[str, Any],
    source: pd.DataFrame,
    main_frame: pd.DataFrame,
    quarantine_frame: pd.DataFrame,
    materialized: dict[str, Any],
    metrics: dict[str, int],
) -> None:
    checks = {
        "source": len(source) == expected["source"],
        "main": len(main_frame) == expected["main"],
        "quarantine": len(quarantine_frame) == expected["quarantine"],
        "dropped": materialized["dropped_exact_duplicate_row_count"] == expected["dropped"],
        "metadata_groups": materialized["metadata_only_group_count"] == expected["metadata_groups"],
        "business_groups": materialized["business_conflict_group_count"] == expected["business_groups"],
        "main_duplicates": metrics["duplicate_row_over_unique_count"] == 0,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        details = {
            "source": len(source),
            "main": len(main_frame),
            "quarantine": len(quarantine_frame),
            "dropped": materialized["dropped_exact_duplicate_row_count"],
            "metadata_groups": materialized["metadata_only_group_count"],
            "business_groups": materialized["business_conflict_group_count"],
            "main_duplicate_row_over_unique": metrics["duplicate_row_over_unique_count"],
        }
        raise RuntimeError(f"{dataset} expected checks failed {failed}: {details}")


def duplicate_metrics(frame: pd.DataFrame) -> dict[str, int]:
    counts = frame.groupby(KEY, dropna=False).size()
    return {
        "unique_key_count": int(len(counts)),
        "duplicate_key_group_count": int((counts > 1).sum()),
        "duplicate_row_over_unique_count": int(len(frame) - len(counts)),
    }


def snapshot(lake_root: Path, target_root: Path, dataset: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lake_root": str(lake_root),
        "target_root": str(target_root),
        "target_exists": target_root.exists(),
        "catalog_tree_hash": tree_hash(lake_root / "catalog"),
        "published_tree_hash": tree_hash(lake_root / "published"),
        "canonical_dataset_tree_hash": tree_hash(lake_root / "canonical" / dataset / SCHEMA_VERSION),
    }


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.exists():
        digest.update(b"<missing>")
        return digest.hexdigest()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(str(path.stat().st_size).encode())
        digest.update(file_sha256(path).encode())
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def object_record(dataset: str, role: str, path: Path, lake_root: Path, row_count: int, write_mode: str) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "role": role,
        "relative_path": str(path.relative_to(lake_root)),
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
        "row_count": int(row_count),
        "write_mode": write_mode,
    }


def stamp_for(dataset: str) -> str:
    return {
        "prices": "2026-06-29T212000+0800",
        "prices_limit": "2026-06-29T213000+0800",
        "trade_status": "2026-06-29T214000+0800",
    }[dataset]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
