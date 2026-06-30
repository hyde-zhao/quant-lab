from __future__ import annotations

"""Dedup contracts tests.

Provenance is machine tracked in tests/PROVENANCE.yaml.
"""


# --- Merged from tests/data_lake/test_dedup_contracts.py ---

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

# --- Merged from tests/data_lake/test_dedup_contracts.py ---

import hashlib
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
from market_data.readers import read_canonical, read_dataset


def test_read_dataset_deduplicates_prices_by_catalog_current_run(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "trade_date": "20260102", "close": 10.0, "source_run_id": "run-cr139-s07-001"},
                {"symbol": "000002", "trade_date": "20260102", "close": 20.0, "source_run_id": "run-cr139-s07-001"},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "trade_date": "20260102", "close": 11.0, "source_run_id": "run-cr139-s07-002"},
            ],
            "run-cr139-s07-003": [
                {"symbol": "000001", "trade_date": "20260102", "close": 12.0, "source_run_id": "run-cr139-s07-003"},
            ],
        },
        latest_manifest_run_id="run-cr139-s07-003",
    )

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert result.frame is not None
    assert _duplicate_key_count(result.frame) == 0
    kept = result.frame[result.frame["symbol"] == "000001"].iloc[0]
    assert kept["source_run_id"] == "run-cr139-s07-003"
    assert kept["close"] == 12.0


def test_read_dataset_uses_deterministic_run_id_fallback_when_catalog_current_missing(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "trade_date": "20260102", "close": 10.0, "source_run_id": "run-cr139-s07-001"},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "trade_date": "20260102", "close": 11.0, "source_run_id": "run-cr139-s07-002"},
            ],
        },
        latest_manifest_run_id=None,
    )

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert result.frame is not None
    assert _duplicate_key_count(result.frame) == 0
    assert result.frame.iloc[0]["source_run_id"] == "run-cr139-s07-002"
    assert any(issue["code"] == "catalog_run_id_missing" for issue in result.issues)


def test_read_dataset_falls_back_to_partition_run_when_source_run_id_missing(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "trade_date": "20260102", "close": 10.0},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "trade_date": "20260102", "close": 11.0},
            ],
        },
        latest_manifest_run_id="run-cr139-s07-002",
    )

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert result.frame is not None
    assert len(result.frame) == 1
    assert result.frame.iloc[0]["close"] == 11.0
    assert any(issue["code"] == "source_run_id_missing" for issue in result.issues)
    assert "_cr139_partition_run_id" not in result.frame.columns


def test_read_dataset_degrades_without_dedup_keys(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "close": 10.0, "source_run_id": "run-cr139-s07-001"},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "close": 11.0, "source_run_id": "run-cr139-s07-002"},
            ],
        },
        latest_manifest_run_id="run-cr139-s07-002",
    )

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert result.frame is not None
    assert len(result.frame) == 2
    assert any(issue["code"] == "dedup_keys_missing" for issue in result.issues)
    assert "_cr139_partition_run_id" not in result.frame.columns


def test_read_layer_dedup_does_not_migrate_physical_partitions(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "trade_date": "20260102", "close": 10.0, "source_run_id": "run-cr139-s07-001"},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "trade_date": "20260102", "close": 11.0, "source_run_id": "run-cr139-s07-002"},
            ],
        },
        latest_manifest_run_id="run-cr139-s07-002",
    )
    before_dirs = _run_dirs(lake)
    before_hash = _tree_hash(lake)

    result = read_dataset(DATASET_PRICES, lake)

    assert result.status == "available"
    assert _run_dirs(lake) == before_dirs
    assert _tree_hash(lake) == before_hash


def test_read_canonical_reuses_read_layer_dedup(tmp_path: Path) -> None:
    lake = _lake_with_runs(
        tmp_path,
        {
            "run-cr139-s07-001": [
                {"symbol": "000001", "trade_date": "20260102", "close": 10.0, "source_run_id": "run-cr139-s07-001"},
            ],
            "run-cr139-s07-002": [
                {"symbol": "000001", "trade_date": "20260102", "close": 11.0, "source_run_id": "run-cr139-s07-002"},
            ],
        },
        latest_manifest_run_id="run-cr139-s07-002",
    )

    frame = read_canonical(DATASET_PRICES, lake)

    assert _duplicate_key_count(frame) == 0
    assert len(frame) == 1
    assert frame.iloc[0]["source_run_id"] == "run-cr139-s07-002"


def _lake_with_runs(
    tmp_path: Path,
    runs: dict[str, list[dict[str, object]]],
    *,
    latest_manifest_run_id: str | None,
) -> Path:
    lake = tmp_path / "lake"
    layout = LakeLayout(lake)
    root = layout.canonical_dataset_root(DATASET_PRICES, SCHEMA_VERSION)
    for run_id, rows in runs.items():
        run_root = root / f"run_id={run_id}"
        run_root.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(run_root / "part.parquet", index=False)
    CatalogStore(layout).upsert(_entry(latest_manifest_run_id=latest_manifest_run_id))
    return lake


def _entry(*, latest_manifest_run_id: str | None) -> CatalogEntry:
    return CatalogEntry(
        dataset=DATASET_PRICES,
        schema_version=SCHEMA_VERSION,
        start_date="20260102",
        end_date="20260102",
        coverage={"rows": 2},
        quality_status=QUALITY_STATUS_PASS,
        dataset_status="available",
        latest_manifest_run_id=latest_manifest_run_id,
        source="fixture",
        source_interface="fixture.prices.daily",
        canonical_path=f"canonical/{DATASET_PRICES}/{SCHEMA_VERSION}",
        published=True,
        published_at="2026-06-28T22:10:00+08:00",
        readiness_status=READINESS_STATUS_AVAILABLE,
        coverage_denominator=2,
        coverage_ratio=1.0,
        coverage_start="20260102",
        coverage_end="20260102",
        lineage_checksum="lineage-fixture",
        as_of_trade_date="20260102",
    )


def _duplicate_key_count(frame: pd.DataFrame) -> int:
    return int(frame.groupby(["symbol", "trade_date"], dropna=False).size().gt(1).sum())


def _run_dirs(lake: Path) -> list[str]:
    root = LakeLayout(lake).canonical_dataset_root(DATASET_PRICES, SCHEMA_VERSION)
    return sorted(path.name for path in root.iterdir() if path.is_dir() and path.name.startswith("run_id="))


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(f"{path.relative_to(root)}:{hashlib.sha256(path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()

# --- Merged from tests/data_lake/test_dedup_contracts.py ---
import pandas as pd
import pytest

from market_data.normalization import (
    CanonicalDeduplicationError,
    validate_canonical_write_dedup,
)


def test_write_dedup_fail_closed_on_duplicate_key():
    frame = pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.0},
            {"trade_date": "2026-01-02", "symbol": "000001.SZ", "close": 10.1},
        ]
    )

    with pytest.raises(CanonicalDeduplicationError):
        validate_canonical_write_dedup(
            frame,
            dataset="prices",
            primary_key=("trade_date", "symbol"),
            policy="fail_on_duplicate",
        )


def test_write_dedup_can_be_deterministic_when_policy_explicit():
    frame = pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.0,
                "source_run_id": "run_a",
            },
            {
                "trade_date": "2026-01-02",
                "symbol": "000001.SZ",
                "close": 10.1,
                "source_run_id": "run_b",
            },
        ]
    )

    result = validate_canonical_write_dedup(
        frame,
        dataset="prices",
        primary_key=("trade_date", "symbol"),
        policy="deduplicate_deterministic",
    )

    assert result.passed
    assert result.dropped_count == 1
    assert result.frame.loc[0, "source_run_id"] == "run_b"
