"""CR139 remediation inventory scanner.

This module is intentionally read-only: it reads catalog metadata and
canonical parquet files, then emits an offline inventory report.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import pyarrow.parquet as pq

from .catalog import CatalogEntry, CatalogStore
from .lake_layout import LakeLayout

INVENTORY_SCHEMA_VERSION = "inventory_v1"
INVENTORY_TOOL_VERSION = "cr139-s01-v0.1"
SYMBOL_TRADE_DATE_KEY = ("symbol", "trade_date")

FORBIDDEN_OPERATION_COUNTS: dict[str, int] = {
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_write": 0,
    "current_pointer_publish": 0,
    "credential_read": 0,
}


@dataclass(frozen=True, slots=True)
class DuplicateKeyResult:
    key_schema: str
    key_check_applicable: bool
    duplicate_key_count: int = 0
    unique_key_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    dataset: str
    schema_version: str
    registered: bool
    published: bool
    published_at: str | None
    pit_status: str | None
    lineage_checksum_present: bool
    lineage_checksum_value: str | None
    latest_manifest_run_id: str | None
    quality_status: str | None
    readiness_status: str | None
    canonical_path_catalog: str | None
    physical_path_exists: bool
    physical_canonical_root: str | None
    row_count: int
    partition_count: int
    source_run_ids: list[str] = field(default_factory=list)
    coverage_start: str | None = None
    coverage_end: str | None = None
    key_schema: str = "unknown"
    key_check_applicable: bool = False
    duplicate_key_count: int = 0
    unique_key_count: int = 0
    columns_present: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class InventoryReport:
    tool_version: str
    schema_version: str
    scanned_at: str
    lake_root_label: str
    catalog_dataset_count: int
    inventory_entry_count: int
    summary: dict[str, Any]
    entries: list[InventoryEntry]
    operation_counts: dict[str, int] = field(default_factory=lambda: dict(FORBIDDEN_OPERATION_COUNTS))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["entries"] = [entry.to_dict() for entry in self.entries]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def build_inventory(
    lake_root: str | Path,
    *,
    dataset: str | None = None,
    scanned_at: str | None = None,
) -> InventoryReport:
    layout = LakeLayout(lake_root)
    store = CatalogStore(layout)
    catalog_entries = sorted(store.list(dataset=dataset), key=lambda item: item.dataset)
    entries = [scan_dataset(entry.dataset, layout, entry) for entry in catalog_entries]
    return InventoryReport(
        tool_version=INVENTORY_TOOL_VERSION,
        schema_version=INVENTORY_SCHEMA_VERSION,
        scanned_at=scanned_at or _now_iso(),
        lake_root_label=_redact_path(layout.lake_root),
        catalog_dataset_count=len(catalog_entries),
        inventory_entry_count=len(entries),
        summary=_build_summary(entries),
        entries=entries,
    )


def scan_dataset(dataset: str, layout: LakeLayout, entry: CatalogEntry) -> InventoryEntry:
    root = layout.canonical_dataset_root(dataset, entry.schema_version)
    parquet_paths = _canonical_paths(root)
    columns_present = _columns_present(parquet_paths)
    row_count = _row_count(parquet_paths)
    source_run_ids = _source_run_ids(parquet_paths)
    coverage_start, coverage_end = _coverage_range(parquet_paths, columns_present)
    duplicate = compute_duplicate_keys(parquet_paths, SYMBOL_TRADE_DATE_KEY, columns_present=columns_present)
    return InventoryEntry(
        dataset=dataset,
        schema_version=entry.schema_version,
        registered=True,
        published=entry.published,
        published_at=entry.published_at,
        pit_status=entry.pit_status,
        lineage_checksum_present=bool(entry.lineage_checksum),
        lineage_checksum_value=entry.lineage_checksum,
        latest_manifest_run_id=entry.latest_manifest_run_id,
        quality_status=entry.quality_status,
        readiness_status=entry.readiness_status,
        canonical_path_catalog=entry.canonical_path,
        physical_path_exists=root.exists() and bool(parquet_paths),
        physical_canonical_root=_relative_to_lake(root, layout.lake_root) if root.exists() else None,
        row_count=row_count,
        partition_count=len(source_run_ids),
        source_run_ids=source_run_ids,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        key_schema=duplicate.key_schema,
        key_check_applicable=duplicate.key_check_applicable,
        duplicate_key_count=duplicate.duplicate_key_count,
        unique_key_count=duplicate.unique_key_count,
        columns_present=columns_present,
    )


def compute_duplicate_keys(
    parquet_paths: Sequence[Path],
    key: tuple[str, ...] = SYMBOL_TRADE_DATE_KEY,
    *,
    columns_present: Sequence[str] | None = None,
) -> DuplicateKeyResult:
    available_columns = set(columns_present if columns_present is not None else _columns_present(parquet_paths))
    key_schema = f"({','.join(key)})"
    if not parquet_paths or not set(key).issubset(available_columns):
        inferred = key_schema if set(key).issubset(available_columns) else "unknown"
        return DuplicateKeyResult(key_schema=inferred, key_check_applicable=False)

    frames = []
    for path in parquet_paths:
        table = pq.read_table(path, columns=list(key))
        frames.append(table.to_pandas())
    if not frames:
        return DuplicateKeyResult(key_schema=key_schema, key_check_applicable=True)

    import pandas as pd

    frame = pd.concat(frames, ignore_index=True)
    unique_key_count = int(frame.drop_duplicates(list(key)).shape[0])
    duplicate_key_count = int(len(frame) - unique_key_count)
    return DuplicateKeyResult(
        key_schema=key_schema,
        key_check_applicable=True,
        duplicate_key_count=duplicate_key_count,
        unique_key_count=unique_key_count,
    )


def format_summary(report: InventoryReport) -> str:
    rows = [
        "dataset\trows\tcoverage\tdup_keys\tpublished\tpit\tlineage",
    ]
    for entry in report.entries:
        coverage = f"{entry.coverage_start or '-'}..{entry.coverage_end or '-'}"
        rows.append(
            "\t".join(
                [
                    entry.dataset,
                    str(entry.row_count),
                    coverage,
                    str(entry.duplicate_key_count),
                    str(entry.published).lower(),
                    entry.pit_status or "null",
                    "present" if entry.lineage_checksum_present else "absent",
                ]
            )
        )
    return "\n".join(rows) + "\n"


def _canonical_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.parquet") if ".tmp" not in path.name)


def _row_count(paths: Sequence[Path]) -> int:
    total = 0
    for path in paths:
        total += int(pq.ParquetFile(path).metadata.num_rows)
    return total


def _columns_present(paths: Sequence[Path]) -> list[str]:
    columns: set[str] = set()
    for path in paths:
        columns.update(pq.ParquetFile(path).schema_arrow.names)
    return sorted(columns)


def _coverage_range(paths: Sequence[Path], columns_present: Sequence[str]) -> tuple[str | None, str | None]:
    if "trade_date" not in set(columns_present):
        return None, None
    values: list[str] = []
    for path in paths:
        table = pq.read_table(path, columns=["trade_date"])
        for value in table.column("trade_date").to_pylist():
            if value is not None:
                values.append(str(value)[:10].replace("-", ""))
    if not values:
        return None, None
    return min(values), max(values)


def _source_run_ids(paths: Sequence[Path]) -> list[str]:
    values: set[str] = set()
    for path in paths:
        for part in path.parts:
            if part.startswith("run_id="):
                values.add(part.split("=", 1)[1])
    return sorted(values)


def _build_summary(entries: Sequence[InventoryEntry]) -> dict[str, Any]:
    pit_distribution: dict[str, int] = {}
    for entry in entries:
        key = entry.pit_status if entry.pit_status is not None else "null"
        pit_distribution[key] = pit_distribution.get(key, 0) + 1
    return {
        "published_true_count": sum(1 for entry in entries if entry.published),
        "published_false_count": sum(1 for entry in entries if not entry.published),
        "lineage_checksum_present_count": sum(1 for entry in entries if entry.lineage_checksum_present),
        "lineage_checksum_absent_count": sum(1 for entry in entries if not entry.lineage_checksum_present),
        "pit_status_distribution": dict(sorted(pit_distribution.items())),
        "duplicate_key_total": sum(entry.duplicate_key_count for entry in entries),
        "physical_missing_count": sum(1 for entry in entries if not entry.physical_path_exists),
    }


def _relative_to_lake(path: Path, lake_root: Path) -> str:
    try:
        return str(path.relative_to(lake_root))
    except ValueError:
        return _redact_path(path)


def _redact_path(path: Path) -> str:
    return path.name or "."


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
