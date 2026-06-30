from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from scripts.legacy.cr.cr139_gateb_batch0_preflight import build_batch0_preflight


def test_batch0_preflight_reports_duplicate_decision_and_events_repair(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)

    report = build_batch0_preflight(lake, sample_limit=2)

    assert report["operation_counts"] == {
        "catalog_write": 0,
        "credential_read": 0,
        "current_pointer_publish": 0,
        "lake_write": 0,
        "provider_fetch": 0,
    }
    prices = _dedup(report, "prices")
    assert prices["status"] == "requires_decision"
    assert prices["duplicate_row_over_unique_count"] == 1
    assert prices["duplicate_key_sample"] == [{"symbol": "000001.SZ", "trade_date": "20260102"}]

    events = report["events_repair_preflight"]
    assert events["status"] == "repair_candidate_ready"
    assert "available_at" in events["missing_from_canonical_contract"]
    assert "available_at" in events["repaired_fields"]
    assert events["trade_date_column_present"] is False
    assert events["trade_date_required_by_current_contract"] is False


def test_batch0_preflight_cli_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    out = lake / "batch0.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/legacy/cr/cr139_gateb_batch0_preflight.py",
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


def _dedup(report: dict[str, object], dataset: str) -> dict[str, object]:
    for item in report["dedup_preflight"]:
        if item["dataset"] == dataset:
            return item
    raise AssertionError(dataset)


def _mini_lake(tmp_path: Path) -> Path:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    store = CatalogStore(layout)
    datasets = (
        "adj_factor",
        "liquidity_capacity",
        "market_cap",
        "prices",
        "prices_limit",
        "trade_status",
        "events",
    )
    for dataset in datasets:
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                schema_version=SCHEMA_VERSION,
                published=False,
                pit_status=None,
                lineage_checksum=None,
                latest_manifest_run_id="run-a",
                quality_status="unknown",
                readiness_status=None,
                canonical_path=f"canonical/{dataset}/{SCHEMA_VERSION}",
            )
        )
        root = layout.canonical_dataset_root(dataset) / "run_id=run-a"
        root.mkdir(parents=True, exist_ok=True)
        _frame_for(dataset).to_parquet(root / "part.parquet", index=False)
    return lake


def _frame_for(dataset: str) -> pd.DataFrame:
    if dataset == "events":
        return pd.DataFrame(
            {
                "symbol": ["000001.SZ"],
                "event_type": ["disclosure"],
                "event_date": ["2026-01-02"],
            }
        )
    return pd.DataFrame(
        {
            "symbol": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "trade_date": ["20260102", "20260102", "20260103"],
            "value": [1.0, 2.0, 3.0],
        }
    )
