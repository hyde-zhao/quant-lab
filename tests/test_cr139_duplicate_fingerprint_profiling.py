from __future__ import annotations

import hashlib
import inspect
from pathlib import Path

import pandas as pd

from market_data import readers
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import DATASET_PRICES, SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from market_data.remediation_inventory import build_inventory
from market_data.readers import profile_duplicate_fingerprints


def test_profile_duplicate_fingerprints_detects_overlap(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake)

    assert report.total_partitions_scanned == 3
    assert report.duplicate_key_count == 1
    duplicate = report.duplicate_keys[0]
    assert duplicate["key"] == {"symbol": "000001", "trade_date": "20260101"}
    assert duplicate["run_ids"] == ["run-1", "run-2"]
    assert duplicate["source_run_ids"] == ["run-1", "run-2"]


def test_profile_no_duplicates(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path, overlap=False)
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake)
    assert report.duplicate_key_count == 0
    assert report.duplicate_keys == []


def test_source_run_id_mismatch_is_flagged(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path, mismatch=True)
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake)
    mismatches = [row for row in report.partition_run_map if row["mismatch"]]
    assert mismatches
    assert {row["mismatch"] for row in mismatches} == {"source_run_id_path_mismatch"}


def test_profile_is_readonly_and_safety_counters_zero(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    before = _tree_hash(lake)
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake)
    after = _tree_hash(lake)
    assert before == after
    assert report.safety_counters == {
        "lake_write": 0,
        "provider_fetch": 0,
        "credential_read": 0,
        "physical_partition_migration": 0,
    }


def test_profile_cross_checks_s01_inventory(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    inventory = build_inventory(lake, scanned_at="2026-06-28T20:40:58+08:00")
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake, inventory_report=inventory)
    assert report.cross_check_with_inventory == {
        "inventory_duplicate_keys": 1,
        "profile_duplicate_keys": 1,
        "diff": 0,
        "diff_reason": "matched",
    }


def test_profile_38_partition_scale(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    _register_prices(layout)
    for index in range(38):
        _write_prices(
            layout,
            f"run-{index:02d}",
            pd.DataFrame(
                {
                    "symbol": [f"{index:06d}"],
                    "trade_date": ["20260101"],
                    "source_run_id": [f"run-{index:02d}"],
                    "close": [float(index)],
                }
            ),
        )
    report = profile_duplicate_fingerprints(DATASET_PRICES, lake)
    assert report.total_partitions_scanned == 38
    assert report.duplicate_key_count == 0


def test_profile_does_not_use_read_dataset_or_mutate_read_path_functions() -> None:
    source = inspect.getsource(readers.profile_duplicate_fingerprints)
    assert "read_dataset(" not in source
    assert "read_canonical(" not in source
    assert "_read_paths(" not in source
    assert "_filter_frame(" not in source


def test_report_is_json_serializable(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    payload = profile_duplicate_fingerprints(DATASET_PRICES, lake).to_dict()
    assert payload["dataset"] == DATASET_PRICES
    assert payload["duplicate_key_count"] == 1


def _mini_lake(tmp_path: Path, *, overlap: bool = True, mismatch: bool = False) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    _register_prices(layout)
    if overlap:
        frames = {
            "run-1": pd.DataFrame(
                {
                    "symbol": ["000001"],
                    "trade_date": ["20260101"],
                    "source_run_id": ["run-x" if mismatch else "run-1"],
                    "close": [1.0],
                }
            ),
            "run-2": pd.DataFrame(
                {
                    "symbol": ["000001"],
                    "trade_date": ["20260101"],
                    "source_run_id": ["run-2"],
                    "close": [1.1],
                }
            ),
            "run-3": pd.DataFrame(
                {
                    "symbol": ["000002"],
                    "trade_date": ["20260102"],
                    "source_run_id": ["run-3"],
                    "close": [2.0],
                }
            ),
        }
    else:
        frames = {
            f"run-{index}": pd.DataFrame(
                {
                    "symbol": [f"00000{index}"],
                    "trade_date": [f"2026010{index}"],
                    "source_run_id": [f"run-{index}"],
                    "close": [float(index)],
                }
            )
            for index in range(1, 4)
        }
    for run_id, frame in frames.items():
        _write_prices(layout, run_id, frame)
    return lake


def _register_prices(layout: LakeLayout) -> None:
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            schema_version=SCHEMA_VERSION,
            published=False,
            latest_manifest_run_id="run-1",
            quality_status="unknown",
            canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}",
        )
    )


def _write_prices(layout: LakeLayout, run_id: str, frame: pd.DataFrame) -> None:
    root = layout.canonical_dataset_root(DATASET_PRICES) / f"run_id={run_id}"
    root.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(root / "part.parquet", index=False)


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(f"{path.relative_to(root)}:{hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
