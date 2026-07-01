from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_data.catalog import CatalogEntry, CatalogStore, build_production_readiness_report
from market_data.contracts import (
    CANONICAL_EVENTS_COLUMNS,
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    READINESS_STATUS_AVAILABLE,
)
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset


def test_events_without_explicit_available_at_fail_fast(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_EVENTS) / "run_id=run-events" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "symbol": "000001.SZ",
                "event_type": "earnings",
                "event_date": "2026-01-02",
                "source_interface": "events.confirmed",
                "source_run_id": "run-events",
            }
        ]
    ).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_EVENTS,
            quality_status="pass",
            dataset_status="available",
            published=True,
            source="fixture",
            source_interface="events.confirmed",
            latest_manifest_run_id="run-events",
            canonical_path=str(path.parent.relative_to(tmp_path)),
            readiness_status=READINESS_STATUS_AVAILABLE,
        )
    )

    result = read_dataset(DATASET_EVENTS, tmp_path, required=True)

    assert result.status == "required_missing"
    assert {issue["code"] for issue in result.issues} >= {
        "w3_required_fields_missing",
        "available_at_missing",
    }
    assert result.remediation_spec["auto_execute"] is False


def test_empty_events_with_frozen_source_interface_is_available(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_EVENTS) / "run_id=run-events" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=CANONICAL_EVENTS_COLUMNS).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_EVENTS,
            quality_status="pass",
            dataset_status="available",
            published=True,
            source="jqdata",
            source_interface="events.disclosure",
            latest_manifest_run_id="run-events",
            canonical_path=str(path.parent.relative_to(tmp_path)),
            readiness_status=READINESS_STATUS_AVAILABLE,
            available_at_rule="daily_close_fact",
        )
    )

    result = read_dataset(DATASET_EVENTS, tmp_path, required=True)

    assert result.status == "available"
    assert result.frame is not None
    assert result.frame.empty


def test_w3_missing_contracts_block_production_strict_even_when_p0_is_published(tmp_path: Path) -> None:
    store = CatalogStore(tmp_path)
    for dataset in (
        DATASET_PRICES,
        DATASET_ADJ_FACTOR,
        DATASET_HS300_INDEX,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
    ):
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                quality_status="pass",
                dataset_status="available",
                published=True,
                readiness_status=READINESS_STATUS_AVAILABLE,
                pit_status=PIT_STATUS_AVAILABLE if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS} else "not_applicable",
                available_at_rule="daily_close_fact",
                source="fixture",
                source_interface=f"{dataset}.fixture",
                latest_manifest_run_id=f"run-{dataset}",
            )
        )

    strict = build_production_readiness_report(tmp_path, realism_mode="production_strict")
    exploratory = build_production_readiness_report(tmp_path, realism_mode="exploratory")

    assert strict["status"] == "fail"
    assert {item["dataset"] for item in strict["blockers"]} >= {
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    }
    assert {
        "real_tradable_execution",
        "realistic_fillability",
        "event_timing_research",
    } <= set(strict["blocked_claims"])
    assert exploratory["status"] == "warn"
    assert "exploratory_analysis" in exploratory["allowed_claims"]


def test_trade_status_and_prices_limit_do_not_default_to_available(tmp_path: Path) -> None:
    trade_status = read_dataset(DATASET_TRADE_STATUS, tmp_path, required=True)
    prices_limit = read_dataset(DATASET_PRICES_LIMIT, tmp_path, required=True)

    assert trade_status.status == "required_missing"
    assert prices_limit.status == "required_missing"
    assert trade_status.issues[0]["code"] == "catalog_missing"
    assert prices_limit.issues[0]["code"] == "catalog_missing"
    assert trade_status.remediation_spec["auto_execute"] is False
    assert prices_limit.remediation_spec["auto_execute"] is False


def test_reader_does_not_rglob_historical_when_catalog_path_is_missing(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    historical_path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-old" / "part.parquet"
    historical_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ"],
            "trade_date": ["20260102"],
            "source_run_id": ["run-old"],
            "close": [10.0],
        }
    ).to_parquet(historical_path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            published=True,
            readiness_status=READINESS_STATUS_AVAILABLE,
            latest_manifest_run_id="run-current",
            canonical_path="canonical/prices/1.0/run_id=run-current",
        )
    )

    result = read_dataset(DATASET_PRICES, tmp_path, required=True)

    assert result.status == "required_missing"
    assert result.issues[0]["code"] == "canonical_missing"
    assert result.frame is None


def test_reader_does_not_read_unpublished_catalog_entry(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-a" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ"],
            "trade_date": ["20260102"],
            "source_run_id": ["run-a"],
            "close": [10.0],
        }
    ).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            published=False,
            readiness_status=READINESS_STATUS_AVAILABLE,
            latest_manifest_run_id="run-a",
            canonical_path=str(path.parent.relative_to(tmp_path)),
        )
    )

    result = read_dataset(DATASET_PRICES, tmp_path, required=True)

    assert result.status == "required_missing"
    assert result.issues[0]["code"] == "catalog_not_published"
    assert result.frame is None


def test_reader_blocks_duplicate_keys_when_catalog_run_id_is_missing(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-a" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ", "000001.SZ"],
            "trade_date": ["20260102", "20260102"],
            "source_run_id": ["run-a", "run-b"],
            "close": [10.0, 11.0],
        }
    ).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            published=True,
            readiness_status=READINESS_STATUS_AVAILABLE,
            latest_manifest_run_id=None,
            canonical_path=str(path.parent.relative_to(tmp_path)),
        )
    )

    result = read_dataset(DATASET_PRICES, tmp_path, required=True)

    assert result.status == "required_missing"
    assert result.issues[0]["code"] == "catalog_run_id_missing_for_duplicate_dedup"
    assert result.remediation_spec["auto_execute"] is False


def test_reader_blocks_duplicate_keys_when_catalog_run_id_is_not_in_sources(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-a" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["000001.SZ", "000001.SZ"],
            "trade_date": ["20260102", "20260102"],
            "source_run_id": ["run-a", "run-b"],
            "close": [10.0, 11.0],
        }
    ).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            quality_status="pass",
            dataset_status="available",
            published=True,
            readiness_status=READINESS_STATUS_AVAILABLE,
            latest_manifest_run_id="run-current",
            canonical_path=str(path.parent.relative_to(tmp_path)),
        )
    )

    result = read_dataset(DATASET_PRICES, tmp_path, required=True)

    assert result.status == "required_missing"
    assert result.issues[0]["code"] == "catalog_run_id_not_found_for_duplicate_dedup"
    assert result.issues[0]["latest_manifest_run_id"] == "run-current"
    assert result.remediation_spec["auto_execute"] is False


def test_production_strict_passes_when_p0_and_w3_are_published_with_pit(tmp_path: Path) -> None:
    store = CatalogStore(tmp_path)
    for dataset in (
        DATASET_PRICES,
        DATASET_ADJ_FACTOR,
        DATASET_HS300_INDEX,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_MEMBERS,
        DATASET_INDEX_WEIGHTS,
        DATASET_STOCK_BASIC,
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    ):
        store.upsert(
            CatalogEntry(
                dataset=dataset,
                quality_status="pass",
                dataset_status="available",
                published=True,
                readiness_status=READINESS_STATUS_AVAILABLE,
                pit_status=(
                    PIT_STATUS_AVAILABLE
                    if dataset in {DATASET_INDEX_MEMBERS, DATASET_INDEX_WEIGHTS, DATASET_STOCK_BASIC}
                    else "not_applicable"
                ),
                available_at_rule="daily_close_fact",
                source="fixture",
                source_interface=f"{dataset}.fixture",
                latest_manifest_run_id=f"run-{dataset}",
            )
        )

    strict = build_production_readiness_report(tmp_path, realism_mode="production_strict")

    assert strict["status"] == "pass"
    assert strict["blockers"] == []
    assert strict["allowed_claims"] == ["production_strict_research"]
