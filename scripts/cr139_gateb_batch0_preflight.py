#!/usr/bin/env python
"""CR139 Gate B Batch 0 read-only preflight evidence.

This script reads canonical parquet files and writes an evidence report outside
the protected lake root. It does not create, modify, delete, publish, or migrate
lake objects.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.catalog import CatalogStore
from market_data.contracts import CANONICAL_EVENTS_COLUMNS, DATASET_EVENTS
from market_data.lake_layout import LakeLayout, MarketDataPathError, ensure_path_outside_root
from market_data.normalization import CanonicalSchemaError, repair_events_schema

DEDUP_PREFLIGHT_DATASETS: tuple[str, ...] = (
    "adj_factor",
    "liquidity_capacity",
    "market_cap",
    "prices",
    "prices_limit",
    "trade_status",
)
SYMBOL_TRADE_DATE_KEY = ("symbol", "trade_date")
FORBIDDEN_OPERATION_COUNTS = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "credential_read": 0,
}


@dataclass(frozen=True, slots=True)
class DedupPreflight:
    dataset: str
    status: str
    primary_key: tuple[str, ...]
    row_count: int = 0
    unique_key_count: int = 0
    duplicate_row_over_unique_count: int = 0
    duplicate_key_sample: tuple[dict[str, Any], ...] = ()
    parquet_file_count: int = 0
    issue_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["primary_key"] = list(self.primary_key)
        payload["duplicate_key_sample"] = [dict(item) for item in self.duplicate_key_sample]
        payload["issue_codes"] = list(self.issue_codes)
        return payload


@dataclass(frozen=True, slots=True)
class EventsRepairPreflight:
    dataset: str
    status: str
    row_count: int = 0
    columns_present: tuple[str, ...] = ()
    canonical_columns: tuple[str, ...] = CANONICAL_EVENTS_COLUMNS
    missing_from_canonical_contract: tuple[str, ...] = ()
    extra_columns: tuple[str, ...] = ()
    repaired_fields: tuple[str, ...] = ()
    defaulted_fields: tuple[str, ...] = ()
    trade_date_column_present: bool = False
    trade_date_required_by_current_contract: bool = False
    issue_codes: tuple[str, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "columns_present",
            "canonical_columns",
            "missing_from_canonical_contract",
            "extra_columns",
            "repaired_fields",
            "defaulted_fields",
            "issue_codes",
        ):
            payload[key] = list(payload[key])
        return payload


def build_batch0_preflight(lake_root: str | Path, *, sample_limit: int = 20) -> dict[str, Any]:
    layout = LakeLayout(lake_root)
    store = CatalogStore(layout)
    dedup_results = [
        _dedup_preflight(layout, dataset, sample_limit=sample_limit)
        for dataset in DEDUP_PREFLIGHT_DATASETS
    ]
    events_result = _events_repair_preflight(layout)
    return {
        "schema_version": 1,
        "cr_id": "CR-139",
        "batch_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate B",
        "batch": "Batch 0",
        "mode": "preflight_only",
        "lake_root_label": Path(lake_root).name,
        "catalog_dataset_count": len(store.list()),
        "dedup_preflight": [item.to_dict() for item in dedup_results],
        "events_repair_preflight": events_result.to_dict(),
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
        "write_authorization_required_for_next_batches": True,
        "forbidden_operations_executed": [],
    }


def _dedup_preflight(layout: LakeLayout, dataset: str, *, sample_limit: int) -> DedupPreflight:
    paths = _canonical_paths(layout, dataset)
    if not paths:
        return DedupPreflight(
            dataset=dataset,
            status="blocked",
            primary_key=SYMBOL_TRADE_DATE_KEY,
            issue_codes=("physical_parquet_missing",),
        )
    columns = _columns_present(paths)
    missing = [column for column in SYMBOL_TRADE_DATE_KEY if column not in columns]
    if missing:
        return DedupPreflight(
            dataset=dataset,
            status="blocked",
            primary_key=SYMBOL_TRADE_DATE_KEY,
            parquet_file_count=len(paths),
            issue_codes=(f"dedup_key_missing:{','.join(missing)}",),
        )
    frame = _read_columns(paths, SYMBOL_TRADE_DATE_KEY)
    row_count = int(len(frame))
    unique_key_count = int(frame.drop_duplicates(list(SYMBOL_TRADE_DATE_KEY)).shape[0])
    duplicate_count = row_count - unique_key_count
    duplicate_sample = _duplicate_key_sample(frame, SYMBOL_TRADE_DATE_KEY, sample_limit)
    status = "requires_decision" if duplicate_count else "pass"
    issues = ("duplicate_key_decision_required",) if duplicate_count else ()
    return DedupPreflight(
        dataset=dataset,
        status=status,
        primary_key=SYMBOL_TRADE_DATE_KEY,
        row_count=row_count,
        unique_key_count=unique_key_count,
        duplicate_row_over_unique_count=duplicate_count,
        duplicate_key_sample=tuple(duplicate_sample),
        parquet_file_count=len(paths),
        issue_codes=issues,
    )


def _events_repair_preflight(layout: LakeLayout) -> EventsRepairPreflight:
    paths = _canonical_paths(layout, DATASET_EVENTS)
    if not paths:
        return EventsRepairPreflight(
            dataset=DATASET_EVENTS,
            status="blocked",
            issue_codes=("physical_parquet_missing",),
        )
    columns = tuple(_columns_present(paths))
    missing_contract = tuple(column for column in CANONICAL_EVENTS_COLUMNS if column not in columns)
    extra_columns = tuple(column for column in columns if column not in CANONICAL_EVENTS_COLUMNS)
    row_count = 0
    try:
        frame = _read_columns(paths, columns)
        row_count = int(len(frame))
        defaults = _events_defaults(frame)
        repaired = repair_events_schema(frame, **defaults)
        status = "pass" if not missing_contract else "repair_candidate_ready"
        issue_codes = tuple(f"missing_canonical_column:{column}" for column in missing_contract)
        return EventsRepairPreflight(
            dataset=DATASET_EVENTS,
            status=status,
            row_count=row_count,
            columns_present=columns,
            missing_from_canonical_contract=missing_contract,
            extra_columns=extra_columns,
            repaired_fields=repaired.repaired_fields,
            defaulted_fields=repaired.defaulted_fields,
            trade_date_column_present="trade_date" in columns,
            trade_date_required_by_current_contract="trade_date" in CANONICAL_EVENTS_COLUMNS,
            issue_codes=issue_codes,
        )
    except (CanonicalSchemaError, ValueError) as exc:
        return EventsRepairPreflight(
            dataset=DATASET_EVENTS,
            status="blocked",
            row_count=row_count,
            columns_present=columns,
            missing_from_canonical_contract=missing_contract,
            extra_columns=extra_columns,
            trade_date_column_present="trade_date" in columns,
            trade_date_required_by_current_contract="trade_date" in CANONICAL_EVENTS_COLUMNS,
            issue_codes=("events_repair_failed",),
            error=str(exc),
        )


def _events_defaults(frame: pd.DataFrame) -> dict[str, str]:
    def first_value(column: str, fallback: str) -> str:
        if column not in frame.columns:
            return fallback
        series = frame[column].dropna()
        if series.empty:
            return fallback
        value = str(series.iloc[0])
        return value if value else fallback

    return {
        "source": first_value("source", "unknown"),
        "source_interface": first_value("source_interface", "events"),
        "source_run_id": first_value("source_run_id", "cr139-w2-events-preflight"),
        "lineage_raw_checksum": first_value("lineage_raw_checksum", ""),
    }


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


def _duplicate_key_sample(
    frame: pd.DataFrame,
    key: tuple[str, ...],
    sample_limit: int,
) -> list[dict[str, Any]]:
    duplicate_mask = frame.duplicated(list(key), keep=False)
    if not bool(duplicate_mask.any()):
        return []
    sample = frame.loc[duplicate_mask, list(key)].drop_duplicates().head(sample_limit)
    return sample.to_dict("records")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CR139 Gate B Batch 0 read-only preflight evidence.")
    parser.add_argument("--lake-root", default=None, help="Market data lake root. Defaults to MARKET_DATA_LAKE_ROOT.")
    parser.add_argument("--out", required=True, help="Output path outside lake_root for JSON evidence.")
    parser.add_argument("--sample-limit", type=int, default=20, help="Maximum duplicate key samples per dataset.")
    args = parser.parse_args()

    lake_root = args.lake_root or os.getenv("MARKET_DATA_LAKE_ROOT")
    if not lake_root:
        parser.error("--lake-root is required when MARKET_DATA_LAKE_ROOT is not set")
    try:
        out_path = ensure_path_outside_root(args.out, lake_root)
    except MarketDataPathError as exc:
        parser.error(str(exc))

    report = build_batch0_preflight(lake_root, sample_limit=max(args.sample_limit, 0))
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
