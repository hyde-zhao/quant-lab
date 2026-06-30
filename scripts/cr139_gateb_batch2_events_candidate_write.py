#!/usr/bin/env python
"""CR139 Gate B Batch 2 events split candidate write."""

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

DATASET = "events"
SCHEMA_VERSION = "1.0"
RUN_ID = build_cr139_run_id(
    dataset=DATASET,
    source="legacy_lake",
    as_of_date="2026-06-29",
    purpose="canonical",
)
KEY = ["symbol", "event_type", "event_date", "available_at"]
BUSINESS_COLUMNS = ["payload"]
METADATA_COLUMNS = ["available_at_rule", "source", "source_interface", "source_run_id", "schema_version", "lineage_raw_checksum"]
OUTPUT_COLUMNS = KEY + METADATA_COLUMNS[:1] + BUSINESS_COLUMNS + METADATA_COLUMNS[1:]
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
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args()

    lake_root = Path(args.lake_root).expanduser().resolve()
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    if not validate_cr139_run_id(RUN_ID):
        raise RuntimeError(f"Invalid CR139 run_id: {RUN_ID}")

    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    stamp = "2026-06-29T210500+0800"
    source_root = lake_root / "canonical" / DATASET / SCHEMA_VERSION
    target_root = lake_root / "candidate" / "parquet" / f"dataset={DATASET}" / f"schema_version={SCHEMA_VERSION}" / f"run_id={RUN_ID}"
    quarantine_root = target_root / "quarantine"
    main_path = target_root / "part-events.parquet"
    quarantine_path = quarantine_root / "part-events-conflict-and-superseded.parquet"
    if target_root.exists():
        raise RuntimeError(f"Target candidate root already exists: {target_root}")

    pre_snapshot = snapshot(lake_root, target_root)
    source = read_source(source_root)
    materialized = materialize(source)
    main = materialized["main"]
    quarantine = materialized["quarantine"]
    metrics = duplicate_metrics(main)

    expected = {
        "source": 362_887,
        "main": 350_753,
        "quarantine": 12_134,
        "business_conflict_groups": 774,
        "metadata_only_groups": 10_583,
    }
    if len(source) != expected["source"]:
        raise RuntimeError(f"source row mismatch: {len(source)} != {expected['source']}")
    if len(main) != expected["main"]:
        raise RuntimeError(f"main row mismatch: {len(main)} != {expected['main']}")
    if len(quarantine) != expected["quarantine"]:
        raise RuntimeError(f"quarantine row mismatch: {len(quarantine)} != {expected['quarantine']}")
    if materialized["business_conflict_group_count"] != expected["business_conflict_groups"]:
        raise RuntimeError("business conflict group count mismatch")
    if materialized["metadata_only_group_count"] != expected["metadata_only_groups"]:
        raise RuntimeError("metadata-only group count mismatch")
    if metrics["duplicate_row_over_unique_count"] != 0:
        raise RuntimeError(f"main still has duplicate event keys: {metrics}")

    target_root.mkdir(parents=True, exist_ok=False)
    quarantine_root.mkdir(parents=True, exist_ok=False)
    main.to_parquet(main_path, index=False)
    quarantine.to_parquet(quarantine_path, index=False)

    objects = [
        object_record("main", main_path, lake_root, len(main), "additive_only_events_split_main"),
        object_record("quarantine", quarantine_path, lake_root, len(quarantine), "additive_only_events_business_conflict_and_superseded_quarantine"),
    ]
    post_snapshot = snapshot(lake_root, target_root)
    zero_mutation = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": "events_zero_mutation_proof",
        "created_at": created_at,
        "catalog_hash_unchanged": pre_snapshot["catalog_tree_hash"] == post_snapshot["catalog_tree_hash"],
        "published_tree_hash_unchanged": pre_snapshot["published_tree_hash"] == post_snapshot["published_tree_hash"],
        "canonical_events_tree_hash_unchanged": pre_snapshot["canonical_dataset_tree_hash"] == post_snapshot["canonical_dataset_tree_hash"],
        "catalog_write": 0,
        "current_pointer_publish": 0,
        "physical_partition_migration": 0,
        "result": "pass",
    }
    if not all(zero_mutation[key] for key in ("catalog_hash_unchanged", "published_tree_hash_unchanged", "canonical_events_tree_hash_unchanged")):
        raise RuntimeError(f"zero mutation proof failed: {zero_mutation}")

    manifest = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": "events_object_manifest",
        "created_at": created_at,
        "write_mode": "additive_only_events_split_candidate",
        "dataset": DATASET,
        "run_id": RUN_ID,
        "objects": objects,
        "operation_counts": dict(OPERATION_COUNTS),
    }
    rollback_manifest = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": "events_rollback_manifest",
        "created_at": created_at,
        "rollback_not_authorized": True,
        "allowed_future_rollback_if_authorized": "delete only the two events candidate objects listed here; do not delete legacy/canonical/catalog/published",
        "objects": objects,
    }
    index = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": "batch2_events_candidate_write_execution",
        "created_at": created_at,
        "status": "pass_with_risk_events_candidate_write_verified",
        "authorized_scope": "Gate B Batch 2 events split candidate write only: metadata-only groups resolved, business-conflict groups full quarantine",
        "dataset": DATASET,
        "run_id": RUN_ID,
        "dataset_results_summary": {
            "source_row_count": int(len(source)),
            "main_row_count": int(len(main)),
            "quarantine_row_count": int(len(quarantine)),
            "metadata_only_group_count": int(materialized["metadata_only_group_count"]),
            "business_conflict_group_count": int(materialized["business_conflict_group_count"]),
            "business_conflict_quarantine_row_count": int(materialized["business_conflict_quarantine_row_count"]),
            "metadata_superseded_quarantine_row_count": int(materialized["metadata_superseded_quarantine_row_count"]),
            "main_duplicate_row_over_unique_count": metrics["duplicate_row_over_unique_count"],
        },
        "source_precedence": {
            "rule": "prefer stage3 trade-status event lineage, then stage3 aux, then non-smoke chapter3/CR018 sources, then prod-window, then smoke; business-conflict groups are not selected into main",
            "business_conflict_groups_quarantined": int(materialized["business_conflict_group_count"]),
        },
        "object_count": len(objects),
        "operation_counts": dict(OPERATION_COUNTS),
        "checks": {
            "target_absent_before_write": pre_snapshot["target_exists"] is False,
            "main_rows_expected": len(main) == expected["main"],
            "quarantine_rows_expected": len(quarantine) == expected["quarantine"],
            "metadata_only_groups_expected": materialized["metadata_only_group_count"] == expected["metadata_only_groups"],
            "business_conflict_groups_expected": materialized["business_conflict_group_count"] == expected["business_conflict_groups"],
            "main_has_no_duplicate_keys": metrics["duplicate_row_over_unique_count"] == 0,
            "zero_mutation_pass": zero_mutation["result"] == "pass",
            "rollback_not_authorized": True,
        },
        "failed_checks": [],
        "evidence_refs": {
            "preexecution_snapshot": f"process/evidence/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-PREEXECUTION-SNAPSHOT.json",
            "postexecution_snapshot": f"process/evidence/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-POSTEXECUTION-SNAPSHOT.json",
            "object_manifest": f"process/evidence/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-OBJECT-MANIFEST.json",
            "rollback_manifest": f"process/evidence/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-ROLLBACK-MANIFEST.json",
            "zero_mutation": f"process/evidence/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-ZERO-MUTATION-PROOF.json",
            "execution_check": "process/checks/CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-2026-06-29.md",
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
        "next_gate": "review events write evidence; continue prices schema-normalized write decision",
    }

    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-PREEXECUTION-SNAPSHOT.json", pre_snapshot)
    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-POSTEXECUTION-SNAPSHOT.json", post_snapshot)
    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-OBJECT-MANIFEST.json", manifest)
    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-ROLLBACK-MANIFEST.json", rollback_manifest)
    write_json(evidence_dir / f"CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION-{stamp}-ZERO-MUTATION-PROOF.json", zero_mutation)
    write_json(evidence_dir / "CR139-W2-GATEB-BATCH2-EVENTS-WRITE-EXECUTION.index.json", index)
    return 0


def read_source(source_root: Path) -> pd.DataFrame:
    paths = sorted(source_root.rglob("*.parquet"))
    if not paths:
        raise FileNotFoundError(source_root)
    frames = []
    for path in paths:
        schema = pq.read_schema(path).names
        missing = [col for col in OUTPUT_COLUMNS if col not in schema]
        if missing:
            raise RuntimeError(f"{path} missing columns {missing}")
        frame = pq.read_table(path, columns=OUTPUT_COLUMNS).to_pandas()
        frame["_source_file"] = str(path)
        frame["_source_row_number"] = range(len(frame))
        frames.append(frame)
    return pd.concat(frames, ignore_index=True, copy=False)


def materialize(source: pd.DataFrame) -> dict[str, Any]:
    frame = source.copy()
    frame["_business_hash"] = pd.util.hash_pandas_object(frame[BUSINESS_COLUMNS].astype(str), index=False)
    frame["_metadata_hash"] = pd.util.hash_pandas_object(frame[METADATA_COLUMNS].astype(str), index=False)
    group = frame.groupby(KEY, dropna=False, sort=False)
    frame["_group_size"] = group["_business_hash"].transform("size")
    frame["_business_nunique"] = group["_business_hash"].transform("nunique")
    frame["_metadata_nunique"] = group["_metadata_hash"].transform("nunique")
    frame["_source_priority"] = frame["source_run_id"].astype(str).map(source_priority)
    frame = frame.sort_values([*KEY, "_source_priority", "source_run_id", "_source_file", "_source_row_number"], kind="mergesort")

    non_duplicate = frame[frame["_group_size"] == 1]
    metadata_only = frame[(frame["_group_size"] > 1) & (frame["_business_nunique"] == 1)]
    business_conflict = frame[(frame["_group_size"] > 1) & (frame["_business_nunique"] > 1)]
    metadata_main = metadata_only.drop_duplicates(KEY, keep="first")
    selected_metadata_index = set(metadata_main.index)
    metadata_quarantine = metadata_only[~metadata_only.index.isin(selected_metadata_index)]
    main = pd.concat([non_duplicate, metadata_main], ignore_index=True, copy=False)
    quarantine = pd.concat([metadata_quarantine, business_conflict], ignore_index=True, copy=False)
    return {
        "main": main.loc[:, OUTPUT_COLUMNS].sort_values(KEY, kind="mergesort").reset_index(drop=True),
        "quarantine": quarantine.loc[:, OUTPUT_COLUMNS].sort_values(KEY, kind="mergesort").reset_index(drop=True),
        "metadata_only_group_count": int(len(metadata_main)),
        "business_conflict_group_count": int(business_conflict.groupby(KEY, dropna=False).ngroups),
        "business_conflict_quarantine_row_count": int(len(business_conflict)),
        "metadata_superseded_quarantine_row_count": int(len(metadata_quarantine)),
    }


def source_priority(source_run_id: object) -> tuple[int, str]:
    text = str(source_run_id)
    if text == "run-stage3-data-update-20260530-20260626-trade-status-20260627":
        return (0, text)
    if text == "run-stage3-data-update-20260530-20260626-aux-20260627":
        return (1, text)
    if text == "run-cr034-chapter3-constraints-2000-2019":
        return (2, text)
    if text == "run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529":
        return (3, text)
    if text == "run-cr034-chapter3-w3-2000-2014":
        return (4, text)
    if "prod-window" in text:
        return (5, text)
    if "smoke" in text:
        return (6, text)
    return (7, text)


def duplicate_metrics(frame: pd.DataFrame) -> dict[str, int]:
    counts = frame.groupby(KEY, dropna=False).size()
    return {
        "unique_key_count": int(len(counts)),
        "duplicate_key_group_count": int((counts > 1).sum()),
        "duplicate_row_over_unique_count": int(len(frame) - len(counts)),
    }


def snapshot(lake_root: Path, target_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lake_root": str(lake_root),
        "target_root": str(target_root),
        "target_exists": target_root.exists(),
        "catalog_tree_hash": tree_hash(lake_root / "catalog"),
        "published_tree_hash": tree_hash(lake_root / "published"),
        "canonical_dataset_tree_hash": tree_hash(lake_root / "canonical" / DATASET / SCHEMA_VERSION),
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


def object_record(role: str, path: Path, lake_root: Path, row_count: int, write_mode: str) -> dict[str, Any]:
    return {
        "dataset": DATASET,
        "role": role,
        "relative_path": str(path.relative_to(lake_root)),
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
        "row_count": int(row_count),
        "write_mode": write_mode,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
