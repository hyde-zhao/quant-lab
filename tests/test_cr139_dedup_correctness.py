from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_PRICES,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset


def test_s29_dedup_standard_returns_zero_duplicate_natural_keys(tmp_path: Path) -> None:
    # STD-S29-DEDUP-01/02: read-layer output is unique and deterministic.
    lake = _lake_with_duplicate_price_runs(tmp_path)

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert result.frame is not None
    assert _duplicate_key_count(result.frame) == 0
    assert result.frame[["symbol", "trade_date", "close", "source_run_id"]].to_dict("records") == [
        {
            "symbol": "000001",
            "trade_date": "20260102",
            "close": 12.0,
            "source_run_id": "run-cr139-s29-current",
        },
        {
            "symbol": "000002",
            "trade_date": "20260102",
            "close": 20.0,
            "source_run_id": "run-cr139-s29-current",
        },
    ]


def _lake_with_duplicate_price_runs(tmp_path: Path) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    root = layout.canonical_dataset_root(DATASET_PRICES, SCHEMA_VERSION)
    rows_by_run = {
        "run-cr139-s29-old": [
            {"symbol": "000001", "trade_date": "20260102", "close": 10.0, "source_run_id": "run-cr139-s29-old"},
            {"symbol": "000002", "trade_date": "20260102", "close": 19.0, "source_run_id": "run-cr139-s29-old"},
        ],
        "run-cr139-s29-current": [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 12.0,
                "source_run_id": "run-cr139-s29-current",
            },
            {
                "symbol": "000002",
                "trade_date": "20260102",
                "close": 20.0,
                "source_run_id": "run-cr139-s29-current",
            },
        ],
    }
    for run_id, rows in rows_by_run.items():
        run_root = root / f"run_id={run_id}"
        run_root.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(run_root / "part.parquet", index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            schema_version=SCHEMA_VERSION,
            start_date="20260102",
            end_date="20260102",
            quality_status=QUALITY_STATUS_PASS,
            dataset_status="available",
            latest_manifest_run_id="run-cr139-s29-current",
            source="fixture",
            source_interface="fixture.prices.daily",
            canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}",
            published=True,
            published_at="2026-06-30T10:45:00+08:00",
            readiness_status=READINESS_STATUS_AVAILABLE,
            coverage_denominator=2,
            coverage_ratio=1.0,
            coverage_start="20260102",
            coverage_end="20260102",
            lineage_checksum="lineage-fixture",
            as_of_trade_date="20260102",
        )
    )
    return lake


def _duplicate_key_count(frame: pd.DataFrame) -> int:
    return int(frame.groupby(["symbol", "trade_date"], dropna=False).size().gt(1).sum())
