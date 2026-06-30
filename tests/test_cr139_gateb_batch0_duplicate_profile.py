from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from scripts.legacy.cr.cr139_gateb_batch0_duplicate_profile import build_duplicate_profile


def test_duplicate_profile_reports_metadata_and_sample_conflicts(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)

    report = build_duplicate_profile(lake, sample_limit=2, sample_rows_per_key=10)

    assert report["operation_counts"] == {
        "catalog_write": 0,
        "credential_read": 0,
        "current_pointer_publish": 0,
        "lake_write": 0,
        "provider_fetch": 0,
    }
    prices = _profile(report, "prices")
    assert prices["status"] == "requires_decision"
    assert prices["duplicate_key_group_count"] == 1
    assert prices["duplicate_rows_in_duplicate_groups"] == 2
    assert prices["duplicate_row_over_unique_count"] == 1
    assert prices["metadata_conflict_counts"]["source_run_id_conflicting_key_count"] == 1
    assert "value" in {item["field"] for item in prices["sample_full_row_field_conflict_top"]}
    assert "source_run_id" in {item["field"] for item in prices["metadata_field_conflict_top"]}

    events = _profile(report, "events")
    assert events["status"] == "requires_decision"
    assert events["primary_key"] == ["symbol", "event_type", "event_date", "available_at"]
    assert events["duplicate_key_group_count"] == 1


def test_duplicate_profile_cli_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = _mini_lake(tmp_path)
    out = lake / "profile.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/legacy/cr/cr139_gateb_batch0_duplicate_profile.py",
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


def _profile(report: dict[str, object], dataset: str) -> dict[str, object]:
    for item in report["dataset_profiles"]:
        if item["dataset"] == dataset:
            return item
    raise AssertionError(dataset)


def _mini_lake(tmp_path: Path) -> Path:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    store = CatalogStore(layout)
    for dataset in (
        "adj_factor",
        "liquidity_capacity",
        "market_cap",
        "prices",
        "prices_limit",
        "trade_status",
        "events",
    ):
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
                "symbol": ["000001.SZ", "000001.SZ", "000002.SZ"],
                "event_type": ["disclosure", "disclosure", "disclosure"],
                "event_date": ["2026-01-02", "2026-01-02", "2026-01-03"],
                "available_at": ["2026-01-02T09:20:00+08:00", "2026-01-02T09:20:00+08:00", "2026-01-03T09:20:00+08:00"],
                "payload": ["a", "b", "c"],
            }
        )
    return pd.DataFrame(
        {
            "symbol": ["000001.SZ", "000001.SZ", "000002.SZ"],
            "trade_date": ["20260102", "20260102", "20260103"],
            "source_run_id": ["run-a", "run-b", "run-a"],
            "available_at": ["2026-01-02T16:00:00+08:00", "2026-01-02T16:01:00+08:00", "2026-01-03T16:00:00+08:00"],
            "lineage_raw_checksum": ["sha256:a", "sha256:b", "sha256:c"],
            "value": [1.0, 2.0, 3.0],
        }
    )
