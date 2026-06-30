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
from market_data.readiness import GAP_PIT_INCOMPLETE, GAP_READINESS_NOT_AVAILABLE


def test_s28_pre_read_readiness_gate_blocks_before_physical_read(tmp_path: Path) -> None:
    lake = _lake_with_catalog(tmp_path)

    result = read_dataset(
        DATASET_PRICES,
        lake,
        required=True,
        pre_read_readiness_gate=_readiness_matrix([GAP_READINESS_NOT_AVAILABLE]),
    )

    assert result.status == "required_missing"
    assert [issue["code"] for issue in result.issues] == [
        "pre_read_readiness_blocked",
        GAP_READINESS_NOT_AVAILABLE,
    ]
    assert result.remediation_spec["action"] == "resolve_readiness_before_read"


def test_s28_pre_read_readiness_gate_blocks_pit_incomplete(tmp_path: Path) -> None:
    lake = _lake_with_catalog(tmp_path)

    result = read_dataset(
        DATASET_PRICES,
        lake,
        required=False,
        pre_read_readiness_gate=_readiness_matrix([GAP_PIT_INCOMPLETE]),
    )

    assert result.status == "unavailable"
    assert "pit_incomplete" in {issue["code"] for issue in result.issues}


def test_s28_pre_read_readiness_gate_passes_and_reader_continues(tmp_path: Path) -> None:
    lake = _lake_with_catalog(tmp_path)
    _write_prices(lake)

    result = read_dataset(DATASET_PRICES, lake, pre_read_readiness_gate=_readiness_matrix([]))

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame[["symbol", "trade_date", "close"]].to_dict("records") == [
        {"symbol": "000001", "trade_date": "20260102", "close": 10.0}
    ]


def _readiness_matrix(gap_codes: list[str]) -> dict[str, object]:
    return {
        "rows": [
            {
                "dataset": DATASET_PRICES,
                "gap_codes": gap_codes,
                "readiness_status": "available" if not gap_codes else "required_missing",
                "publish_status": "published",
                "pit_status": "available" if GAP_PIT_INCOMPLETE not in gap_codes else "pit_incomplete",
            }
        ]
    }


def _lake_with_catalog(tmp_path: Path) -> Path:
    lake = tmp_path / "lake"
    CatalogStore(LakeLayout(lake)).upsert(_entry())
    return lake


def _write_prices(lake: Path) -> None:
    root = LakeLayout(lake).canonical_dataset_root(DATASET_PRICES, SCHEMA_VERSION) / "run_id=run-cr139-s28-data"
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 10.0,
                "source_run_id": "run-cr139-s28-data",
                "readiness_status": READINESS_STATUS_AVAILABLE,
            }
        ]
    ).to_parquet(root / "part.parquet", index=False)


def _entry() -> CatalogEntry:
    return CatalogEntry(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        start_date="20260102",
        end_date="20260102",
        quality_status=QUALITY_STATUS_PASS,
        dataset_status="available",
        latest_manifest_run_id="run-cr139-s28-data",
        source="fixture",
        source_interface="fixture.prices.daily",
        canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}",
        published=True,
        published_at="2026-06-30T11:55:00+08:00",
        readiness_status=READINESS_STATUS_AVAILABLE,
        coverage_denominator=1,
        coverage_ratio=1.0,
        coverage_start="20260102",
        coverage_end="20260102",
        lineage_checksum="lineage-fixture",
        as_of_trade_date="20260102",
    )
