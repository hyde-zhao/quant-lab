from __future__ import annotations

import inspect
from pathlib import Path

import pandas as pd

from market_data import readers
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import (
    DATASET_PRICES,
    PIT_STATUS_AVAILABLE,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_AVAILABLE,
    SCHEMA_VERSION,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import ReaderResult, read_panel_as_of


def test_read_panel_as_of_filters_future_rows_and_keeps_latest_per_symbol() -> None:
    result = read_panel_as_of(
        "market_cap",
        as_of="2026-01-05",
        reader=_fixture_reader(
            pd.DataFrame(
                {
                    "symbol": ["000001", "000001", "000001", "000002"],
                    "trade_date": ["20260101", "20260102", "20260103", "20260103"],
                    "market_cap": [10.0, 11.0, 12.0, 20.0],
                    "available_at": ["2026-01-02", "2026-01-04", "2026-01-06", "2026-01-06"],
                    "pit_status": [PIT_STATUS_AVAILABLE] * 4,
                }
            )
        ),
    )

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame[["symbol", "market_cap"]].to_dict("records") == [
        {"symbol": "000001", "market_cap": 11.0}
    ]


def test_read_panel_as_of_requires_available_at() -> None:
    result = read_panel_as_of(
        "market_cap",
        as_of="2026-01-05",
        reader=_fixture_reader(pd.DataFrame({"symbol": ["000001"], "market_cap": [10.0]})),
    )

    assert result.status == "required_missing"
    assert result.issues[-1]["code"] == "pit_as_of_required_column_missing"
    assert result.issues[-1]["columns"] == ["available_at"]


def test_read_panel_as_of_returns_required_missing_when_no_rows_available() -> None:
    result = read_panel_as_of(
        "market_cap",
        as_of="2026-01-05",
        reader=_fixture_reader(
            pd.DataFrame(
                {
                    "symbol": ["000001"],
                    "market_cap": [10.0],
                    "available_at": ["2026-01-06"],
                }
            )
        ),
    )

    assert result.status == "required_missing"
    assert result.frame is not None
    assert result.frame.empty
    assert result.issues[-1]["code"] == "pit_as_of_no_available_rows"


def test_read_panel_as_of_inherits_published_gate_from_read_dataset(tmp_path: Path) -> None:
    lake = _lake_with_prices(tmp_path, published=False)

    blocked = read_panel_as_of(DATASET_PRICES, lake, as_of="2026-01-05")

    assert blocked.status == "unavailable"
    assert blocked.issues[0]["code"] == "catalog_not_published"

    _write_catalog(lake, published=True)
    available = read_panel_as_of(DATASET_PRICES, lake, as_of="2026-01-05")

    assert available.status == "available"
    assert available.frame is not None
    assert available.frame[["symbol", "close"]].to_dict("records") == [
        {"symbol": "000001", "close": 11.0}
    ]


def test_read_panel_as_of_does_not_write_catalog_or_call_catalog_store() -> None:
    source = inspect.getsource(readers.read_panel_as_of)

    assert "CatalogStore" not in source
    assert ".upsert(" not in source
    assert "write_text(" not in source


def _fixture_reader(frame: pd.DataFrame):
    def _reader(
        dataset: str,
        lake_root: str | Path | None = None,
        filters=None,
        quality_policy=None,
        required: bool = True,
    ) -> ReaderResult:
        del dataset, lake_root, filters, quality_policy, required
        return ReaderResult(status="available", frame=frame.copy())

    return _reader


def _lake_with_prices(tmp_path: Path, *, published: bool) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    root = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr139-s05"
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001", "000001", "000002"],
            "trade_date": ["20260101", "20260102", "20260103"],
            "source_run_id": ["run-cr139-s05"] * 3,
            "close": [10.0, 11.0, 20.0],
            "available_at": ["2026-01-02", "2026-01-04", "2026-01-06"],
            "pit_status": [PIT_STATUS_AVAILABLE] * 3,
        }
    ).to_parquet(root / "part.parquet", index=False)
    _write_catalog(lake, published=published)
    return lake


def _write_catalog(lake: Path, *, published: bool) -> None:
    CatalogStore(LakeLayout(lake)).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            schema_version=SCHEMA_VERSION,
            start_date="20260101",
            end_date="20260103",
            quality_status=QUALITY_STATUS_PASS,
            dataset_status="available",
            latest_manifest_run_id="run-cr139-s05",
            source="fixture",
            source_interface="fixture.prices.daily",
            canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}/run_id=run-cr139-s05",
            published=published,
            published_at="2026-06-28T21:22:52+08:00" if published else None,
            readiness_status=READINESS_STATUS_AVAILABLE,
            pit_status=PIT_STATUS_AVAILABLE,
            coverage_denominator=3,
            coverage_ratio=1.0,
            coverage_start="20260101",
            coverage_end="20260103",
            lineage_checksum="lineage-fixture",
            universe_scope="fixture",
            as_of_trade_date="20260103",
        )
    )
