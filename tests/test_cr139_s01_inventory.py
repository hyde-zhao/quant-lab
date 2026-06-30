from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from market_data.remediation_inventory import build_inventory, compute_duplicate_keys


DATASETS_17 = [
    "prices",
    "adj_factor",
    "hs300_index",
    "index_members",
    "index_weights",
    "trade_calendar",
    "stock_basic",
    "trade_status",
    "prices_limit",
    "events",
    "financial_pit",
    "market_cap",
    "industry",
    "benchmark",
    "feature_panel",
    "label_window",
    "broker_facts",
]


def test_inventory_cli_outputs_17_dataset_report(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    result = subprocess.run(
        [sys.executable, "scripts/lake_inventory.py", "--lake-root", str(lake)],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["catalog_dataset_count"] == 17
    assert payload["inventory_entry_count"] == 17
    assert {entry["dataset"] for entry in payload["entries"]} == set(DATASETS_17)


def test_inventory_entries_have_required_fields_and_baseline_counts(tmp_path: Path) -> None:
    report = build_inventory(_mini_lake(tmp_path), scanned_at="2026-06-28T20:00:18+08:00")
    required_fields = {
        "dataset",
        "schema_version",
        "registered",
        "published",
        "published_at",
        "pit_status",
        "lineage_checksum_present",
        "lineage_checksum_value",
        "latest_manifest_run_id",
        "quality_status",
        "readiness_status",
        "canonical_path_catalog",
        "physical_path_exists",
        "physical_canonical_root",
        "row_count",
        "partition_count",
        "source_run_ids",
        "coverage_start",
        "coverage_end",
        "key_schema",
        "key_check_applicable",
        "duplicate_key_count",
        "unique_key_count",
        "columns_present",
    }
    for entry in report.to_dict()["entries"]:
        assert required_fields.issubset(entry)
    assert report.summary["published_false_count"] == 17
    assert report.summary["lineage_checksum_absent_count"] == 17
    assert report.summary["pit_status_distribution"] == {"null": 14, "pit_available": 3}


def test_duplicate_key_count_matches_known_fixture(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    prices = _entry(report=build_inventory(lake), dataset="prices")
    assert prices.duplicate_key_count == 3
    assert prices.unique_key_count == 3

    layout = LakeLayout(lake)
    paths = sorted(layout.canonical_dataset_root("prices").rglob("*.parquet"))
    duplicate = compute_duplicate_keys(paths, ("symbol", "trade_date"), columns_present=["symbol", "trade_date"])
    assert duplicate.duplicate_key_count == 3
    assert duplicate.unique_key_count == 3


def test_missing_physical_dataset_keeps_catalog_coverage(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path, missing_dataset="broker_facts")
    report = build_inventory(lake)
    broker = _entry(report=report, dataset="broker_facts")
    assert report.inventory_entry_count == 17
    assert broker.physical_path_exists is False
    assert broker.row_count == 0
    assert report.summary["physical_missing_count"] == 1


def test_inventory_is_deterministic_except_scanned_at(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    first = build_inventory(lake).to_dict()
    second = build_inventory(lake).to_dict()
    first.pop("scanned_at")
    second.pop("scanned_at")
    assert first == second


def test_inventory_is_readonly_for_catalog(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    catalog_path = LakeLayout(lake).catalog_root / "catalog.json"
    before = _sha256(catalog_path)
    report = build_inventory(lake)
    after = _sha256(catalog_path)
    assert before == after
    assert report.operation_counts == {
        "provider_fetch": 0,
        "lake_write": 0,
        "catalog_write": 0,
        "current_pointer_publish": 0,
        "credential_read": 0,
    }


def test_build_inventory_returns_json_serializable_dataclass(tmp_path: Path) -> None:
    report = build_inventory(_mini_lake(tmp_path))
    payload = report.to_dict()
    assert payload["schema_version"] == "inventory_v1"
    assert json.loads(report.to_json())["inventory_entry_count"] == 17


def test_summary_format_is_human_readable(tmp_path: Path) -> None:
    out = tmp_path / "inventory.tsv"
    lake = _mini_lake(tmp_path)
    subprocess.run(
        [
            sys.executable,
            "scripts/lake_inventory.py",
            "--lake-root",
            str(lake),
            "--format",
            "summary",
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )
    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "dataset\trows\tcoverage\tdup_keys\tpublished\tpit\tlineage"
    assert "prices\t6\t20260101..20260103\t3\tfalse\tpit_available\tabsent" in text


def test_inventory_cli_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    out = lake / "inventory-report.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/lake_inventory.py",
            "--lake-root",
            str(lake),
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "输出路径不能位于 lake_root 内" in result.stderr
    assert not out.exists()


def _mini_lake(tmp_path: Path, *, missing_dataset: str | None = None) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    store = CatalogStore(layout)
    for index, dataset in enumerate(DATASETS_17):
        pit_status = "pit_available" if index < 3 else None
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                schema_version=SCHEMA_VERSION,
                published=False,
                pit_status=pit_status,
                lineage_checksum=None,
                latest_manifest_run_id="run-a",
                quality_status="unknown",
                readiness_status=None,
                canonical_path=f"canonical/{dataset}/{SCHEMA_VERSION}",
            )
        )
        if dataset != missing_dataset:
            frame = _frame_for(dataset)
            root = layout.canonical_dataset_root(dataset) / "run_id=run-a"
            root.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(root / "part.parquet", index=False)
    return lake


def _frame_for(dataset: str) -> pd.DataFrame:
    if dataset == "prices":
        return pd.DataFrame(
            {
                "symbol": ["000001", "000001", "000002", "000002", "000003", "000003"],
                "trade_date": ["20260101", "20260101", "20260102", "20260102", "20260103", "20260103"],
                "close": [1.0, 1.1, 2.0, 2.1, 3.0, 3.1],
            }
        )
    if dataset == "trade_calendar":
        return pd.DataFrame({"calendar_date": ["20260101"], "is_open": [True]})
    return pd.DataFrame(
        {
            "symbol": ["000001", "000002"],
            "trade_date": ["20260101", "20260102"],
            "value": [1.0, 2.0],
        }
    )


def _entry(*, report, dataset: str):
    for entry in report.entries:
        if entry.dataset == dataset:
            return entry
    raise AssertionError(dataset)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
