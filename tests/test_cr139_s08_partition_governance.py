from __future__ import annotations

from pathlib import Path

import pytest

from market_data.cli import _canonical_paths_for_run, _catalog_canonical_path
from market_data.contracts import DATASET_PRICES, SCHEMA_VERSION
from market_data.lake_layout import LakeLayout, MarketDataPathError
from market_data.normalization import _canonical_current_path, _canonical_path


def _assert_no_run_id_segment(path: Path) -> None:
    assert not any(part.startswith("run_id=") for part in path.parts)


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fixture", encoding="utf-8")
    return path


def test_current_and_archive_roots_do_not_use_run_id(tmp_path):
    layout = LakeLayout(tmp_path)

    current = layout.canonical_current_root(DATASET_PRICES)
    archive = layout.canonical_archive_root(DATASET_PRICES)

    assert current == tmp_path / "canonical" / DATASET_PRICES / SCHEMA_VERSION / "current"
    assert archive == tmp_path / "canonical" / DATASET_PRICES / SCHEMA_VERSION / "archive"
    _assert_no_run_id_segment(current)
    _assert_no_run_id_segment(archive)
    assert not current.exists()
    assert not archive.exists()


def test_current_and_archive_partition_paths_validate_segments(tmp_path):
    layout = LakeLayout(tmp_path)

    current = layout.canonical_current_partition_path(
        DATASET_PRICES,
        trade_date="2026-01-02",
        exchange="SSE",
        board="main",
    )
    archive = layout.canonical_archive_partition_path(
        DATASET_PRICES,
        partition_date="20260102",
        exchange="SZSE",
    )

    assert current == (
        tmp_path
        / "canonical"
        / DATASET_PRICES
        / SCHEMA_VERSION
        / "current"
        / "trade_date=20260102"
        / "exchange=SSE"
        / "board=main"
    )
    assert archive == (
        tmp_path
        / "canonical"
        / DATASET_PRICES
        / SCHEMA_VERSION
        / "archive"
        / "trade_date=20260102"
        / "exchange=SZSE"
    )
    _assert_no_run_id_segment(current)
    _assert_no_run_id_segment(archive)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"trade_date": "2026/01/02"},
        {"exchange": ""},
        {"exchange": "S/SE"},
        {"board": "main*"},
    ],
)
def test_partition_path_rejects_unsafe_segments(tmp_path, kwargs):
    layout = LakeLayout(tmp_path)

    with pytest.raises(MarketDataPathError):
        layout.canonical_current_partition_path(DATASET_PRICES, **kwargs)


def test_normalization_current_path_default_contract_and_legacy_compatibility(tmp_path):
    layout = LakeLayout(tmp_path)

    current = _canonical_current_path(layout, DATASET_PRICES, "b1")
    legacy = _canonical_path(layout, DATASET_PRICES, "run-cr139-s08", "b1")

    assert current == (
        tmp_path
        / "canonical"
        / DATASET_PRICES
        / SCHEMA_VERSION
        / "current"
        / "part-b1.parquet"
    )
    assert legacy == (
        tmp_path
        / "canonical"
        / DATASET_PRICES
        / SCHEMA_VERSION
        / "run_id=run-cr139-s08"
        / "part-b1.parquet"
    )
    _assert_no_run_id_segment(current)
    assert any(part == "run_id=run-cr139-s08" for part in legacy.parts)


def test_cli_prefers_current_paths_over_legacy_run_id(tmp_path):
    layout = LakeLayout(tmp_path)
    current = _touch(layout.canonical_current_root(DATASET_PRICES) / "part-current.parquet")
    legacy = _touch(
        layout.canonical_dataset_root(DATASET_PRICES)
        / "run_id=run-cr139-s08"
        / "part-legacy.parquet"
    )

    paths = _canonical_paths_for_run(layout, DATASET_PRICES, "run-cr139-s08")
    catalog_path = _catalog_canonical_path(layout, DATASET_PRICES, paths, "run-cr139-s08")

    assert paths == [current]
    assert catalog_path == current
    assert legacy.exists()


def test_cli_falls_back_to_legacy_run_id_paths_without_migration(tmp_path):
    layout = LakeLayout(tmp_path)
    run_root = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr139-s08"
    first = _touch(run_root / "part-a.parquet")
    second = _touch(run_root / "part-b.parquet")

    paths = _canonical_paths_for_run(layout, DATASET_PRICES, "run-cr139-s08")
    catalog_path = _catalog_canonical_path(layout, DATASET_PRICES, paths, "run-cr139-s08")

    assert paths == [first, second]
    assert catalog_path == run_root
    assert run_root.exists()
    assert first.exists()
    assert second.exists()


def test_s08_mock_contract_keeps_run_id_in_metadata_not_path(tmp_path):
    layout = LakeLayout(tmp_path)
    current = _canonical_current_path(layout, DATASET_PRICES, "b1")
    catalog_entry = {
        "dataset": DATASET_PRICES,
        "canonical_path": str(current),
        "triggered_by_cr": "CR-139",
    }
    manifest_lineage = {
        "run_id": "run-cr139-s08",
        "canonical_path": str(current),
    }

    assert catalog_entry["triggered_by_cr"] == "CR-139"
    assert manifest_lineage["run_id"] == "run-cr139-s08"
    _assert_no_run_id_segment(Path(catalog_entry["canonical_path"]))
    _assert_no_run_id_segment(Path(manifest_lineage["canonical_path"]))
