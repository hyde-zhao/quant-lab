#!/usr/bin/env python
"""Stable data-lake duplicate-key profiling entrypoint.

The profiler is read-only. It scans canonical parquet files and writes JSON
evidence outside the protected lake root. It does not mutate lake objects,
catalog metadata, pointers, or physical partitions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.contracts import DATASET_EVENTS
from market_data.lake_layout import LakeLayout, MarketDataPathError, ensure_path_outside_root

DEDUP_DATASETS: tuple[str, ...] = (
    "adj_factor",
    "liquidity_capacity",
    "market_cap",
    "prices",
    "prices_limit",
    "trade_status",
)
SYMBOL_TRADE_DATE_KEY = ("symbol", "trade_date")
EVENTS_PRIMARY_KEY = ("symbol", "event_type", "event_date", "available_at")
PROFILE_COLUMNS = ("source_run_id", "available_at", "lineage_raw_checksum")
FORBIDDEN_OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "credential_read": 0,
}


def build_duplicate_profile(
    lake_root: str | Path,
    *,
    datasets: Sequence[str] = DEDUP_DATASETS,
    include_events: bool = True,
    sample_limit: int = 20,
    sample_rows_per_key: int = 50,
) -> dict[str, Any]:
    layout = LakeLayout(lake_root)
    dataset_profiles = [
        _profile_dataset(
            layout,
            dataset,
            key=SYMBOL_TRADE_DATE_KEY,
            sample_limit=sample_limit,
            sample_rows_per_key=sample_rows_per_key,
        )
        for dataset in datasets
    ]
    if include_events:
        dataset_profiles.append(
            _profile_dataset(
                layout,
                DATASET_EVENTS,
                key=EVENTS_PRIMARY_KEY,
                sample_limit=sample_limit,
                sample_rows_per_key=sample_rows_per_key,
            )
        )
    return {
        "schema_version": 1,
        "workflow_id": "data-lake-production-governance",
        "gate": "duplicate-key-profile",
        "mode": "duplicate_profile_read_only",
        "lake_root_label": Path(lake_root).name,
        "profile_scope": {
            "global": [
                "row_count",
                "unique_key_count",
                "duplicate_key_group_count",
                "duplicate_rows_in_duplicate_groups",
                "duplicate_row_over_unique_count",
                "metadata conflict counts for source_run_id/available_at/lineage_raw_checksum when present",
            ],
            "sample_limited": [
                "field_conflict_top for metadata columns",
                "sample_exact_duplicate_row_over_unique_count when full-row sampling is explicitly enabled",
                "sample rows per duplicate key when full-row sampling is explicitly enabled",
            ],
        },
        "dataset_profiles": dataset_profiles,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
        "forbidden_operations_executed": [],
    }


def _profile_dataset(
    layout: LakeLayout,
    dataset: str,
    *,
    key: tuple[str, ...],
    sample_limit: int,
    sample_rows_per_key: int,
) -> dict[str, Any]:
    paths = _canonical_paths(layout, dataset)
    if not paths:
        return {
            "dataset": dataset,
            "status": "blocked",
            "primary_key": list(key),
            "issue_codes": ["physical_parquet_missing"],
        }
    columns = _columns_present(paths)
    missing_key = [column for column in key if column not in columns]
    if missing_key:
        return {
            "dataset": dataset,
            "status": "blocked",
            "primary_key": list(key),
            "columns_present": columns,
            "issue_codes": [f"primary_key_missing:{','.join(missing_key)}"],
        }

    profile_columns = tuple(column for column in PROFILE_COLUMNS if column in columns and column not in key)
    read_columns = tuple(dict.fromkeys((*key, *profile_columns)))
    frame = _read_columns(paths, read_columns)
    key_counts = (
        frame.groupby(list(key), dropna=False)
        .size()
        .rename("row_count")
        .reset_index()
        .sort_values("row_count", ascending=False)
        .reset_index(drop=True)
    )
    duplicate_keys = key_counts[key_counts["row_count"] > 1].reset_index(drop=True)
    duplicate_mask = frame.duplicated(list(key), keep=False)
    duplicate_rows = frame.loc[duplicate_mask].copy()
    sample_keys = duplicate_keys.head(sample_limit)
    sample_rows = (
        _sample_full_rows(paths, key, sample_keys, sample_rows_per_key)
        if sample_rows_per_key > 0
        else pd.DataFrame()
    )
    metadata_conflicts = _metadata_conflict_counts(duplicate_rows, key, profile_columns)
    field_conflict_top = _metadata_field_conflict_top(metadata_conflicts)
    sample_field_conflict_top = _field_conflict_top(sample_rows, key) if not sample_rows.empty else []
    recommendation = _recommendation(
        duplicate_key_group_count=int(len(duplicate_keys)),
        metadata_conflicts=metadata_conflicts,
        field_conflict_top=field_conflict_top,
    )

    return {
        "dataset": dataset,
        "status": "requires_decision" if len(duplicate_keys) else "pass",
        "primary_key": list(key),
        "columns_present": columns,
        "parquet_file_count": len(paths),
        "row_count": int(len(frame)),
        "unique_key_count": int(len(key_counts)),
        "duplicate_key_group_count": int(len(duplicate_keys)),
        "duplicate_rows_in_duplicate_groups": int(len(duplicate_rows)),
        "duplicate_row_over_unique_count": int(len(frame) - len(key_counts)),
        "metadata_conflict_counts": metadata_conflicts,
        "duplicate_rows_top_source_run_id": _top_values(duplicate_rows, "source_run_id"),
        "duplicate_rows_top_available_at": _top_values(duplicate_rows, "available_at"),
        "duplicate_key_sample": _records(sample_keys.head(sample_limit)),
        "sample_rows_per_key_limit": sample_rows_per_key,
        "sample_duplicate_row_count": int(len(sample_rows)),
        "sample_exact_duplicate_row_over_unique_count": _sample_exact_duplicate_over_unique(sample_rows),
        "metadata_field_conflict_top": field_conflict_top,
        "sample_full_row_field_conflict_top": sample_field_conflict_top,
        "recommended_next_decision": recommendation,
    }


def _recommendation(
    *,
    duplicate_key_group_count: int,
    metadata_conflicts: Mapping[str, int],
    field_conflict_top: Sequence[Mapping[str, Any]],
) -> str:
    if duplicate_key_group_count == 0:
        return "write_allowed_after_standard_gate_b_checks"
    if any(value > 0 for value in metadata_conflicts.values()):
        return "requires_dataset_specific_keep_drop_or_quarantine_rule"
    if field_conflict_top:
        return "requires_sample_conflict_review_before_dedup"
    return "candidate_for_deterministic_dedup_after_owner_approval"


def _metadata_conflict_counts(
    duplicate_rows: pd.DataFrame,
    key: tuple[str, ...],
    profile_columns: Sequence[str],
) -> dict[str, int]:
    if duplicate_rows.empty:
        return {column: 0 for column in profile_columns}
    grouped = duplicate_rows.groupby(list(key), dropna=False)
    results: dict[str, int] = {}
    for column in profile_columns:
        values = grouped[column].nunique(dropna=False)
        results[f"{column}_conflicting_key_count"] = int((values > 1).sum())
    return results


def _metadata_field_conflict_top(metadata_conflicts: Mapping[str, int]) -> list[dict[str, Any]]:
    rows = []
    for key, value in metadata_conflicts.items():
        if not key.endswith("_conflicting_key_count"):
            continue
        field = key.removesuffix("_conflicting_key_count")
        if value > 0:
            rows.append({"field": field, "conflicting_key_count": int(value)})
    return sorted(rows, key=lambda item: item["conflicting_key_count"], reverse=True)


def _top_values(frame: pd.DataFrame, column: str, *, limit: int = 10) -> list[dict[str, Any]]:
    if column not in frame.columns or frame.empty:
        return []
    counts = frame[column].fillna("<null>").astype(str).value_counts(dropna=False).head(limit)
    return [{"value": str(index), "row_count": int(value)} for index, value in counts.items()]


def _sample_full_rows(
    paths: Sequence[Path],
    key: tuple[str, ...],
    sample_keys: pd.DataFrame,
    sample_rows_per_key: int,
) -> pd.DataFrame:
    if sample_keys.empty:
        return pd.DataFrame()
    wanted = {tuple(str(row[column]) for column in key): 0 for _, row in sample_keys.iterrows()}
    frames: list[pd.DataFrame] = []
    for path in paths:
        if all(count >= sample_rows_per_key for count in wanted.values()):
            break
        table = pq.read_table(path)
        frame = table.to_pandas()
        if not set(key).issubset(frame.columns):
            continue
        key_series = frame[list(key)].astype(str).apply(tuple, axis=1)
        mask = key_series.isin(wanted)
        if not bool(mask.any()):
            continue
        subset = frame.loc[mask].copy()
        limited_parts: list[pd.DataFrame] = []
        subset_key_series = subset[list(key)].astype(str).apply(tuple, axis=1)
        for key_value, group in subset.groupby(subset_key_series, sort=False):
            remaining = sample_rows_per_key - wanted.get(key_value, 0)
            if remaining <= 0:
                continue
            part = group.head(remaining)
            wanted[key_value] = wanted.get(key_value, 0) + len(part)
            limited_parts.append(part)
        if limited_parts:
            frames.append(pd.concat(limited_parts, ignore_index=True))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _field_conflict_top(
    sample_rows: pd.DataFrame,
    key: tuple[str, ...],
    *,
    columns: Sequence[str] | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if sample_rows.empty:
        return []
    conflicts: Counter[str] = Counter()
    key_columns = list(key)
    target_columns = list(columns) if columns is not None else list(sample_rows.columns)
    sample_key_series = sample_rows[key_columns].astype(str).apply(tuple, axis=1)
    for _, group in sample_rows.groupby(sample_key_series, sort=False):
        for column in target_columns:
            if column in key_columns or column not in sample_rows.columns:
                continue
            if group[column].nunique(dropna=False) > 1:
                conflicts[column] += 1
    return [{"field": field, "sample_conflicting_key_count": int(count)} for field, count in conflicts.most_common(limit)]


def _sample_exact_duplicate_over_unique(sample_rows: pd.DataFrame) -> int:
    if sample_rows.empty:
        return 0
    return int(len(sample_rows) - len(sample_rows.drop_duplicates()))


def _canonical_paths(layout: LakeLayout, dataset: str) -> list[Path]:
    root = layout.canonical_dataset_root(dataset)
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _columns_present(paths: Sequence[Path]) -> list[str]:
    columns: set[str] = set()
    for path in paths:
        columns.update(pq.ParquetFile(path).schema_arrow.names)
    return sorted(columns)


def _read_columns(paths: Sequence[Path], columns: Sequence[str]) -> pd.DataFrame:
    frames = [pq.read_table(path, columns=list(columns)).to_pandas() for path in paths]
    if not frames:
        return pd.DataFrame(columns=list(columns))
    return pd.concat(frames, ignore_index=True)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = frame.to_dict("records")
    return [{key: _json_value(value) for key, value in item.items()} for item in records]


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Build stable duplicate profile evidence.")
    parser.add_argument("--lake-root", default=None, help="Market data lake root. Defaults to MARKET_DATA_LAKE_ROOT.")
    parser.add_argument("--out", required=True, help="Output path outside lake_root for JSON evidence.")
    parser.add_argument("--datasets", default=",".join(DEDUP_DATASETS), help="Comma-separated duplicate-key datasets to profile.")
    parser.add_argument("--skip-events", action="store_true", help="Do not include events primary-key profile in this output.")
    parser.add_argument("--sample-limit", type=int, default=20, help="Maximum duplicate keys sampled per dataset.")
    parser.add_argument("--sample-rows-per-key", type=int, default=0, help="Maximum full rows sampled per duplicate key; default 0 disables full-row sampling.")
    args = parser.parse_args()

    lake_root = args.lake_root or os.getenv("MARKET_DATA_LAKE_ROOT")
    if not lake_root:
        parser.error("--lake-root is required when MARKET_DATA_LAKE_ROOT is not set")
    try:
        out_path = ensure_path_outside_root(args.out, lake_root)
    except MarketDataPathError as exc:
        parser.error(str(exc))

    report = build_duplicate_profile(
        lake_root,
        datasets=tuple(item.strip() for item in args.datasets.split(",") if item.strip()),
        include_events=not args.skip_events,
        sample_limit=max(args.sample_limit, 0),
        sample_rows_per_key=max(args.sample_rows_per_key, 0),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
