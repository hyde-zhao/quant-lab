#!/usr/bin/env python
"""CR139 Gate B Batch 2 remaining split planning.

Read-only planner for adj_factor, prices, prices_limit, events, and
trade_status. It classifies duplicate-key groups into exact-copy,
metadata-only, and business-conflict buckets without writing lake objects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.lake_layout import ensure_path_outside_root

DATASETS: tuple[str, ...] = (
    "adj_factor",
    "prices",
    "prices_limit",
    "events",
    "trade_status",
)
SYMBOL_TRADE_DATE_KEY = ("symbol", "trade_date")
EVENTS_PRIMARY_KEY = ("symbol", "event_type", "event_date", "available_at")
METADATA_COLUMNS = {
    "source",
    "source_interface",
    "source_run_id",
    "available_at",
    "available_at_rule",
    "schema_version",
    "lineage_raw_checksum",
    "lineage_checksum",
    "pit_status",
}
HELPER_COLUMNS = {
    "_source_file",
    "_source_row_number",
    "_cr139_source_file",
    "_cr139_source_row_number",
}
OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 0,
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
    parser.add_argument("--out", required=True)
    parser.add_argument("--index-out", required=True)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument("--max-source-pairs", type=int, default=12)
    args = parser.parse_args()

    lake_root = Path(args.lake_root).expanduser().resolve()
    out = ensure_path_outside_root(args.out, lake_root, label="split planning output")
    index_out = ensure_path_outside_root(args.index_out, lake_root, label="split planning index output")
    out.parent.mkdir(parents=True, exist_ok=True)
    index_out.parent.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    dataset_results = []
    for dataset in DATASETS:
        dataset_results.append(
            profile_dataset(
                lake_root=lake_root,
                dataset=dataset,
                sample_limit=args.sample_limit,
                max_source_pairs=args.max_source_pairs,
            )
        )

    totals = {
        "dataset_count": len(dataset_results),
        "source_row_count": sum(item["source_row_count"] for item in dataset_results),
        "duplicate_key_group_count": sum(item["duplicate_key_group_count"] for item in dataset_results),
        "duplicate_rows_in_groups": sum(item["duplicate_rows_in_groups"] for item in dataset_results),
        "duplicate_row_over_unique_count": sum(item["duplicate_row_over_unique_count"] for item in dataset_results),
        "exact_copy_group_count": sum(item["split_buckets"]["exact_copy"]["group_count"] for item in dataset_results),
        "metadata_only_group_count": sum(item["split_buckets"]["metadata_only"]["group_count"] for item in dataset_results),
        "business_conflict_group_count": sum(item["split_buckets"]["business_conflict"]["group_count"] for item in dataset_results),
    }
    totals["planned_main_row_count_if_recommended_actions_approved"] = sum(
        item["planned_candidate_shape"]["main_row_count"] for item in dataset_results
    )
    totals["planned_quarantine_row_count_if_recommended_actions_approved"] = sum(
        item["planned_candidate_shape"]["quarantine_row_count"] for item in dataset_results
    )
    totals["planned_dropped_exact_duplicate_row_count"] = sum(
        item["planned_candidate_shape"]["dropped_exact_duplicate_row_count"] for item in dataset_results
    )

    report = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": "batch2_remaining_consolidated_read_only_split_planning",
        "created_at": created_at,
        "status": "pass_with_risk_split_planning_complete_write_decisions_required",
        "mode": "read_only_split_planning_no_lake_write",
        "authorized_scope": (
            "authorize Gate B Batch 2 remaining datasets consolidated read-only split planning only "
            "for adj_factor, prices, prices_limit, events, trade_status; no lake write"
        ),
        "lake_root": str(lake_root),
        "datasets": list(DATASETS),
        "operation_counts": dict(OPERATION_COUNTS),
        "classification_method": {
            "key": "dataset-specific duplicate key",
            "exact_copy": "duplicate-key group where business hash and metadata hash both have one distinct value",
            "metadata_only": "duplicate-key group where business hash has one distinct value and metadata hash has more than one distinct value",
            "business_conflict": "duplicate-key group where business hash has more than one distinct value",
            "hash_note": "Hashes use pandas 64-bit row fingerprints for routing. Future write gates must materialize exact rows and verify pre/post-write content.",
        },
        "totals": totals,
        "dataset_results": dataset_results,
        "non_authorized_scope": [
            "lake write",
            "candidate object delete",
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
            "rollback",
        ],
        "next_gate": "review split planning; authorize one or more explicit per-dataset candidate writes only after decisions are accepted",
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index = {
        "schema_version": 1,
        "cr_id": "CR-139",
        "workflow_id": "CR139-STRATEGY-DATA-FOUNDATION",
        "gate": "Gate B",
        "stage": report["stage"],
        "created_at": created_at,
        "status": report["status"],
        "mode": report["mode"],
        "authorized_scope": report["authorized_scope"],
        "datasets": list(DATASETS),
        "totals": totals,
        "dataset_summary": [
            {
                "dataset": item["dataset"],
                "source_row_count": item["source_row_count"],
                "duplicate_key_group_count": item["duplicate_key_group_count"],
                "exact_copy_groups": item["split_buckets"]["exact_copy"]["group_count"],
                "metadata_only_groups": item["split_buckets"]["metadata_only"]["group_count"],
                "business_conflict_groups": item["split_buckets"]["business_conflict"]["group_count"],
                "recommended_write_mode": item["recommended_write_mode"],
                "readiness_verdict": item["readiness_verdict"],
                "decision_required": item["decision_required"],
                "schema_normalization_required": item["schema_normalization_required"],
            }
            for item in dataset_results
        ],
        "operation_counts": dict(OPERATION_COUNTS),
        "evidence_refs": {
            "detail": str(out),
            "index": str(index_out),
        },
        "non_authorized_scope": report["non_authorized_scope"],
    }
    index_out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def profile_dataset(
    *,
    lake_root: Path,
    dataset: str,
    sample_limit: int,
    max_source_pairs: int,
) -> dict[str, Any]:
    key = EVENTS_PRIMARY_KEY if dataset == "events" else SYMBOL_TRADE_DATE_KEY
    dataset_root = lake_root / "canonical" / dataset / "1.0"
    paths = sorted(dataset_root.rglob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No parquet files found for {dataset}: {dataset_root}")

    all_columns = columns_present(paths)
    missing_key = [column for column in key if column not in all_columns]
    if missing_key:
        raise ValueError(f"{dataset} missing key columns: {missing_key}")
    metadata_cols = [column for column in all_columns if column in METADATA_COLUMNS and column not in key]
    business_cols = [
        column
        for column in all_columns
        if column not in key and column not in metadata_cols and column not in HELPER_COLUMNS
    ]
    source_cols = [column for column in ("source_run_id", "source", "source_interface", "lineage_raw_checksum") if column in all_columns]

    rows = []
    run_id_counter: Counter[str] = Counter()
    duplicate_run_id_counter: Counter[str] = Counter()
    file_schema_counter: Counter[tuple[str, ...]] = Counter()
    row_count = 0

    read_columns = tuple(dict.fromkeys((*key, *metadata_cols, *business_cols, *source_cols)))
    frames = []
    for path in paths:
        schema_names = pq.read_schema(path).names
        file_schema_counter[tuple(schema_names)] += 1
        table = pq.read_table(path, columns=[column for column in read_columns if column in schema_names])
        frame = table.to_pandas()
        for column in read_columns:
            if column not in frame.columns:
                frame[column] = pd.NA
        frame = frame.loc[:, list(read_columns)]
        frame["_business_hash"] = pd.util.hash_pandas_object(frame[business_cols], index=False) if business_cols else 0
        frame["_metadata_hash"] = pd.util.hash_pandas_object(frame[metadata_cols], index=False) if metadata_cols else 0
        if "source_run_id" in frame.columns:
            run_id_counter.update(frame["source_run_id"].fillna("<null>").astype(str).value_counts(dropna=False).to_dict())
        row_count += len(frame)
        frames.append(frame[[*key, *source_cols, "_business_hash", "_metadata_hash"]])

    compact = pd.concat(frames, ignore_index=True, copy=False)
    del frames

    group = compact.groupby(list(key), dropna=False, sort=False)
    group_size = group.size()
    duplicate_group_sizes = group_size[group_size > 1]
    duplicate_key_group_count = int(len(duplicate_group_sizes))
    duplicate_rows_in_groups = int(duplicate_group_sizes.sum())
    duplicate_row_over_unique_count = int(row_count - len(group_size))

    duplicate_index = duplicate_group_sizes.index
    business_nunique = group["_business_hash"].nunique(dropna=False).reindex(duplicate_index)
    metadata_nunique = group["_metadata_hash"].nunique(dropna=False).reindex(duplicate_index)

    exact_mask = (business_nunique == 1) & (metadata_nunique == 1)
    metadata_only_mask = (business_nunique == 1) & (metadata_nunique > 1)
    business_conflict_mask = business_nunique > 1

    bucket_stats = {
        "exact_copy": bucket_from_mask(duplicate_group_sizes, exact_mask),
        "metadata_only": bucket_from_mask(duplicate_group_sizes, metadata_only_mask),
        "business_conflict": bucket_from_mask(duplicate_group_sizes, business_conflict_mask),
    }

    duplicate_mask = compact.duplicated(list(key), keep=False)
    if "source_run_id" in compact.columns:
        duplicate_run_id_counter.update(
            compact.loc[duplicate_mask, "source_run_id"]
            .fillna("<null>")
            .astype(str)
            .value_counts(dropna=False)
            .to_dict()
        )

    source_pair_top, samples = sample_duplicate_groups(
        compact,
        key=list(key),
        group_sizes=duplicate_group_sizes,
        exact_groups=duplicate_group_sizes[exact_mask].index,
        metadata_only_groups=duplicate_group_sizes[metadata_only_mask].index,
        limit=sample_limit,
        max_source_pairs=max_source_pairs,
    )

    planned_shape = plan_candidate_shape(
        row_count=row_count,
        duplicate_rows_in_groups=duplicate_rows_in_groups,
        bucket_stats=bucket_stats,
    )
    recommended_write_mode, verdict, decision_required = recommendation_for(dataset, bucket_stats)

    return {
        "dataset": dataset,
        "canonical_root": str(dataset_root),
        "parquet_file_count": len(paths),
        "source_row_count": int(row_count),
        "primary_key": list(key),
        "columns_present": all_columns,
        "business_columns": business_cols,
        "metadata_columns": metadata_cols,
        "schema_variant_count": len(file_schema_counter),
        "schema_normalization_required": dataset == "prices" and len(file_schema_counter) > 1,
        "top_source_run_ids": [
            {"source_run_id": value, "row_count": int(count)}
            for value, count in run_id_counter.most_common(10)
        ],
        "duplicate_rows_top_source_run_ids": [
            {"source_run_id": value, "duplicate_row_count": int(count)}
            for value, count in duplicate_run_id_counter.most_common(10)
        ],
        "duplicate_key_group_count": duplicate_key_group_count,
        "duplicate_rows_in_groups": duplicate_rows_in_groups,
        "duplicate_row_over_unique_count": duplicate_row_over_unique_count,
        "split_buckets": bucket_stats,
        "source_run_id_set_top": source_pair_top,
        "planned_candidate_shape": planned_shape,
        "recommended_write_mode": recommended_write_mode,
        "readiness_verdict": verdict,
        "decision_required": decision_required,
        "recommended_sort_key": [
            "business columns equality check first",
            "source_run_id precedence when approved",
            "_source_file ASC",
            "_source_row_number ASC",
        ],
        "sample_duplicate_groups": samples,
    }


def columns_present(paths: Sequence[Path]) -> list[str]:
    ordered: list[str] = []
    seen = set()
    for path in paths:
        for column in pq.read_schema(path).names:
            if column not in seen:
                ordered.append(column)
                seen.add(column)
    return ordered


def bucket_from_mask(sizes: pd.Series, mask: pd.Series) -> dict[str, int]:
    selected = sizes[mask]
    row_count = int(selected.sum()) if len(selected) else 0
    group_count = int(len(selected))
    return {
        "group_count": group_count,
        "row_count": row_count,
        "row_over_unique_count": int(row_count - group_count),
    }


def sample_duplicate_groups(
    frame: pd.DataFrame,
    *,
    key: list[str],
    group_sizes: pd.Series,
    exact_groups: Iterable[Any],
    metadata_only_groups: Iterable[Any],
    limit: int,
    max_source_pairs: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    exact_set = set(exact_groups)
    metadata_only_set = set(metadata_only_groups)
    source_pair_counter: Counter[tuple[str, ...]] = Counter()
    samples: list[dict[str, Any]] = []
    for group_values, row_count in group_sizes.head(max(limit, max_source_pairs)).items():
        if not isinstance(group_values, tuple):
            group_values = (group_values,)
        mask = pd.Series(True, index=frame.index)
        for column, value in zip(key, group_values):
            if pd.isna(value):
                mask &= frame[column].isna()
            else:
                mask &= frame[column].eq(value)
        rows = frame.loc[mask]
        group_key: Any = group_values[0] if len(group_values) == 1 else group_values
        if group_key in exact_set:
            group_class = "exact_copy"
        elif group_key in metadata_only_set:
            group_class = "metadata_only"
        else:
            group_class = "business_conflict"
        if "source_run_id" in rows.columns:
            source_pair_counter[tuple(sorted(str(value) for value in rows["source_run_id"].fillna("<null>").unique()))] += 1
        if len(samples) >= limit:
            continue
        item = {
            "key": {column: scalar_to_json(value) for column, value in zip(key, group_values)},
            "row_count": int(row_count),
            "group_class": group_class,
        }
        if "source_run_id" in rows.columns:
            item["source_run_ids"] = sorted(str(value) for value in rows["source_run_id"].fillna("<null>").unique())
        samples.append(item)
    source_pair_top = [
        {
            "source_run_id_set": list(pair),
            "sample_duplicate_key_group_count": int(count),
            "note": "sample-limited source_run_id combination; full routing uses bucket counts, not this sample count",
        }
        for pair, count in source_pair_counter.most_common(max_source_pairs)
    ]
    return source_pair_top, samples


def plan_candidate_shape(
    *,
    row_count: int,
    duplicate_rows_in_groups: int,
    bucket_stats: dict[str, dict[str, int]],
) -> dict[str, int]:
    non_duplicate_rows = row_count - duplicate_rows_in_groups
    exact = bucket_stats["exact_copy"]
    metadata_only = bucket_stats["metadata_only"]
    business_conflict = bucket_stats["business_conflict"]
    return {
        "non_duplicate_row_count": int(non_duplicate_rows),
        "main_row_count": int(non_duplicate_rows + exact["group_count"] + metadata_only["group_count"]),
        "quarantine_row_count": int((metadata_only["row_count"] - metadata_only["group_count"]) + business_conflict["row_count"]),
        "dropped_exact_duplicate_row_count": int(exact["row_count"] - exact["group_count"]),
        "business_conflict_groups_without_main_row": int(business_conflict["group_count"]),
    }


def recommendation_for(dataset: str, bucket_stats: dict[str, dict[str, int]]) -> tuple[str, str, list[str]]:
    exact = bucket_stats["exact_copy"]["group_count"]
    metadata = bucket_stats["metadata_only"]["group_count"]
    business = bucket_stats["business_conflict"]["group_count"]
    decisions: list[str] = []
    if exact:
        decisions.append("approve exact-copy dedup drop policy")
    if metadata:
        decisions.append("approve source_run_id precedence for metadata-only groups")
    if business:
        decisions.append("approve full-group quarantine or semantic resolution for business-conflict groups")
    if dataset == "prices":
        decisions.append("approve prices schema normalization policy before write")
    if dataset == "events":
        mode = "primary-key-conflict quarantine planning"
    elif business:
        mode = "split exact-dedup plus metadata resolution plus business-conflict quarantine planning"
    elif metadata:
        mode = "metadata-only resolved candidate planning"
    else:
        mode = "exact-dedup candidate planning"
    return mode, "blocked_until_dataset_write_decisions_approved", decisions


def scalar_to_json(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
