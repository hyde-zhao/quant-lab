from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import SCHEMA_VERSION
from market_data.lake_layout import LakeLayout
from scripts.data_lake.profile_current_truth import build_current_truth_profile


def test_current_truth_profile_follows_catalog_path_not_historical_root(tmp_path: Path) -> None:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    old_path = layout.canonical_dataset_root("prices") / "run_id=run-old" / "part.parquet"
    current_path = layout.canonical_dataset_root("prices") / "run_id=run-current" / "part.parquet"
    old_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ", "000001.SZ"],
            "trade_date": ["20260102", "20260102"],
            "close": [10.0, 11.0],
        }
    ).to_parquet(old_path, index=False)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ"],
            "trade_date": ["20260102"],
            "close": [12.0],
        }
    ).to_parquet(current_path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset="prices",
            schema_version=SCHEMA_VERSION,
            published=True,
            readiness_status="available",
            quality_status="pass",
            latest_manifest_run_id="run-current",
            canonical_path=str(current_path.relative_to(lake)),
        )
    )

    profile = build_current_truth_profile(lake)

    assert profile["summary"]["dataset_count"] == 1
    assert profile["summary"]["duplicate_key_total"] == 0
    assert profile["datasets"][0]["row_count"] == 1
    assert profile["datasets"][0]["canonical_path"] == "canonical/prices/1.0/run_id=run-current/part.parquet"


def test_current_truth_profile_cli_rejects_output_inside_lake_root(tmp_path: Path) -> None:
    lake = tmp_path / "data-lake"
    layout = LakeLayout(lake)
    CatalogStore(layout).upsert(CatalogEntry(dataset="prices", canonical_path="canonical/prices/1.0/current/part.parquet"))
    out = lake / "profile.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data_lake/profile_current_truth.py",
            "--lake-root",
            str(lake),
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "current truth profile output不能位于 lake_root 内" in result.stderr
    assert not out.exists()
