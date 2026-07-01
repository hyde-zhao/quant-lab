#!/usr/bin/env python
"""Profile catalog current truth only.

This read-only command follows catalog canonical_path entries. It does not scan
all historical run_id partitions unless the catalog explicitly points there.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_data.lake_layout import LakeLayout, ensure_path_outside_root

SYMBOL_TRADE_DATE_KEY = ("symbol", "trade_date")
EVENTS_PRIMARY_KEY = ("symbol", "event_type", "event_date", "available_at")
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


def build_current_truth_profile(lake_root: str | Path) -> dict[str, Any]:
    root = Path(lake_root).expanduser().resolve()
    layout = LakeLayout(root)
    catalog_path = layout.catalog_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    datasets = catalog.get("datasets", {})
    if not isinstance(datasets, Mapping):
        raise ValueError(f"catalog datasets must be a mapping: {catalog_path}")
    results = [_profile_dataset(root, str(dataset), entry) for dataset, entry in sorted(datasets.items()) if isinstance(entry, Mapping)]
    return {
        "schema_version": "current-truth-profile-v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "catalog_current_truth_read_only",
        "lake_root": str(root),
        "catalog_path": str(catalog_path),
        "summary": {
            "dataset_count": len(results),
            "published_dataset_count": sum(1 for item in results if item["published"]),
            "source_missing_count": sum(1 for item in results if item["source_status"] == "missing"),
            "duplicate_key_total": sum(item["duplicate_key_count"] for item in results),
            "duplicate_dataset_count": sum(1 for item in results if item["duplicate_key_count"] > 0),
            "row_count_total": sum(item["row_count"] for item in results),
        },
        "datasets": results,
        "operation_counts": dict(OPERATION_COUNTS),
    }


def _profile_dataset(root: Path, dataset: str, entry: Mapping[str, Any]) -> dict[str, Any]:
    source_value = entry.get("canonical_path")
    source = (root / str(source_value)).resolve() if source_value else None
    paths = _parquet_paths(source) if source is not None and source.exists() else []
    columns = _columns_present(paths)
    key = EVENTS_PRIMARY_KEY if dataset == "events" else SYMBOL_TRADE_DATE_KEY
    missing_key = [column for column in key if column not in columns]
    row_count = sum(pq.ParquetFile(path).metadata.num_rows for path in paths)
    duplicate_key_count = 0
    unique_key_count = None
    if paths and not missing_key and set(key).issubset(columns):
        frame = _read_columns(paths, key)
        key_counts = frame.groupby(list(key), dropna=False).size()
        duplicate_key_count = int((key_counts > 1).sum())
        unique_key_count = int(len(key_counts))
    return {
        "dataset": dataset,
        "published": bool(entry.get("published")),
        "readiness_status": entry.get("readiness_status"),
        "quality_status": entry.get("quality_status"),
        "pit_status": entry.get("pit_status"),
        "canonical_path": str(source_value) if source_value else None,
        "source_status": "present" if paths else "missing",
        "parquet_file_count": len(paths),
        "row_count": int(row_count),
        "columns_present": columns,
        "key_schema": list(key),
        "missing_key_columns": missing_key,
        "unique_key_count": unique_key_count,
        "duplicate_key_count": duplicate_key_count,
        "latest_manifest_run_id": entry.get("latest_manifest_run_id"),
        "lineage_checksum": entry.get("lineage_checksum"),
    }


def _parquet_paths(path: Path) -> list[Path]:
    if path.is_file() and path.suffix == ".parquet":
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*.parquet") if ".tmp" not in item.name)
    return []


def _columns_present(paths: Sequence[Path]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        for column in pq.read_schema(path).names:
            if column not in seen:
                seen.add(column)
                ordered.append(column)
    return ordered


def _read_columns(paths: Sequence[Path], columns: Sequence[str]) -> pd.DataFrame:
    frames = [pq.read_table(path, columns=list(columns)).to_pandas() for path in paths]
    if not frames:
        return pd.DataFrame(columns=list(columns))
    return pd.concat(frames, ignore_index=True, copy=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile catalog current truth only.")
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    lake_root = Path(args.lake_root).expanduser().resolve()
    out = ensure_path_outside_root(args.out, lake_root, label="current truth profile output")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(build_current_truth_profile(lake_root), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
