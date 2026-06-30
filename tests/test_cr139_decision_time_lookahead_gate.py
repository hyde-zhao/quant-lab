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


def test_s25_decision_time_gate_allows_available_rows(tmp_path: Path) -> None:
    lake = _lake_with_prices(
        tmp_path,
        [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 10.0,
                "source_run_id": "run-cr139-s25-data",
                "available_at": "2026-01-02T15:10:00+08:00",
                "readiness_status": READINESS_STATUS_AVAILABLE,
            }
        ],
    )

    result = read_dataset(DATASET_PRICES, lake, decision_time="2026-01-02T15:30:00+08:00")

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame[["symbol", "close"]].to_dict("records") == [{"symbol": "000001", "close": 10.0}]


def test_s25_decision_time_gate_blocks_future_available_at(tmp_path: Path) -> None:
    lake = _lake_with_prices(
        tmp_path,
        [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 10.0,
                "source_run_id": "run-cr139-s25-data",
                "available_at": "2026-01-02T15:45:00+08:00",
                "readiness_status": READINESS_STATUS_AVAILABLE,
            }
        ],
    )

    result = read_dataset(DATASET_PRICES, lake, required=True, decision_time="2026-01-02T15:30:00+08:00")

    assert result.status == "required_missing"
    assert result.frame is None
    assert result.issues[-1]["code"] == "decision_time_lookahead_blocked"
    assert result.issues[-1]["future_row_count"] == 1
    assert result.remediation_spec["action"] == "use_data_available_at_or_before_decision_time"


def test_s25_decision_time_gate_requires_available_at_column(tmp_path: Path) -> None:
    lake = _lake_with_prices(
        tmp_path,
        [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 10.0,
                "source_run_id": "run-cr139-s25-data",
                "readiness_status": READINESS_STATUS_AVAILABLE,
            }
        ],
    )

    result = read_dataset(DATASET_PRICES, lake, required=True, decision_time="2026-01-02T15:30:00+08:00")

    assert result.status == "required_missing"
    assert result.issues[-1]["code"] == "decision_time_available_at_missing"
    assert result.remediation_spec["action"] == "provide_explicit_available_at"


def test_s25_decision_time_gate_blocks_invalid_decision_time(tmp_path: Path) -> None:
    lake = _lake_with_prices(
        tmp_path,
        [
            {
                "symbol": "000001",
                "trade_date": "20260102",
                "close": 10.0,
                "source_run_id": "run-cr139-s25-data",
                "available_at": "2026-01-02T15:10:00+08:00",
                "readiness_status": READINESS_STATUS_AVAILABLE,
            }
        ],
    )

    result = read_dataset(DATASET_PRICES, lake, required=True, decision_time="not-a-time")

    assert result.status == "required_missing"
    assert result.issues[-1]["code"] == "decision_time_unparseable"
    assert result.remediation_spec["action"] == "fix_decision_time"


def _lake_with_prices(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    root = layout.canonical_dataset_root(DATASET_PRICES, SCHEMA_VERSION) / "run_id=run-cr139-s25-data"
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(root / "part.parquet", index=False)
    CatalogStore(layout).upsert(_entry())
    return lake


def _entry() -> CatalogEntry:
    return CatalogEntry(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        start_date="20260102",
        end_date="20260102",
        quality_status=QUALITY_STATUS_PASS,
        dataset_status="available",
        latest_manifest_run_id="run-cr139-s25-data",
        source="fixture",
        source_interface="fixture.prices.daily",
        canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}",
        published=True,
        published_at="2026-06-30T13:25:00+08:00",
        readiness_status=READINESS_STATUS_AVAILABLE,
        coverage_denominator=1,
        coverage_ratio=1.0,
        coverage_start="20260102",
        coverage_end="20260102",
        lineage_checksum="lineage-fixture",
        as_of_trade_date="20260102",
    )
