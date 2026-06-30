from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from engine.research_dataset import ResearchDatasetRequest, build_research_dataset
from engine.research_reporting import build_experiment_realism_matrix
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    READINESS_STATUS_AVAILABLE,
)
from market_data.readers import ReaderResult


def test_production_strict_research_metadata_blocks_missing_w3_inputs(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-03",
            universe_mode="pit_required",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=1,
        ),
        reader=_reader_without_w3,
        benchmark_resolver=lambda **_: {"status": "available", "benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == "required_missing"
    blocked = {item["claim"] for item in dataset.blocked_claims}
    assert {
        "real_tradable_execution",
        "realistic_fillability",
        "event_timing_research",
    } <= blocked
    assert dataset.metadata["realism_mode"] == "production_strict"
    assert dataset.metadata["readiness"]["pit"]["is_pit_universe"] is True
    assert set(dataset.metadata["readiness"]["w3"]) == {
        DATASET_TRADE_STATUS,
        DATASET_PRICES_LIMIT,
        DATASET_EVENTS,
    }
    assert dataset.metadata["blocked_claims"]


def test_experiment_realism_matrix_has_sixteen_rows_and_marks_experiment_11_na() -> None:
    metadata = {
        "schema_name": "research_input_v1",
        "report_kind": "experiment_smoke",
        "coverage_start": "2026-01-02",
        "coverage_end": "2026-01-03",
        "benchmark": {"benchmark_status": "required_missing"},
        "benchmark_status": "required_missing",
        "universe": {"universe_mode": "fixed_snapshot", "is_pit_universe": False},
        "universe_mode": "fixed_snapshot",
        "adjustment_policy": "qfq",
        "label_window": {"forward_return_horizon": 1, "label_available_end": "2026-01-03"},
        "quality": {"quality_status": "warn", "readiness_status": "warn"},
        "quality_status": "warn",
        "readiness_status": "warn",
        "realism_mode": "production_strict",
        "lineage": {"manifest_run_id": "run-fixture"},
        "known_limitations": [{"code": "fixture_only"}],
        "allowed_claims": ["framework_validation"],
        "blocked_claims": [{"claim": "production_strict_research", "reason_code": "fixture_only"}],
    }

    matrix = build_experiment_realism_matrix(metadata)

    assert matrix["experiment_count"] == 16
    assert matrix["network_calls"] == 0
    assert matrix["auto_backfill"] is False
    exp11 = [row for row in matrix["rows"] if row["experiment_id"] == "11"][0]
    assert exp11["status"] == "n/a"
    assert exp11["entrypoint"] == "N/A"
    assert any(item.get("code") == "experiment_entrypoint_not_available" for item in exp11["known_limitations"])
    assert all(row["network_calls"] == 0 and row["auto_backfill"] is False for row in matrix["rows"])


def _reader_without_w3(dataset, *_args, **_kwargs) -> ReaderResult:
    if dataset == DATASET_PRICES:
        return ReaderResult(
            status="available",
            frame=pd.DataFrame(
                {
                    "trade_date": ["2026-01-02", "2026-01-03"],
                    "symbol": ["AAA", "AAA"],
                    "close": [10.0, 11.0],
                    "adjusted_close": [10.0, 11.0],
                    "adj_factor": [1.0, 1.0],
                    "adjustment_policy": ["qfq", "qfq"],
                    "source_run_id": ["run-prices", "run-prices"],
                    "lineage_raw_checksum": ["checksum", "checksum"],
                }
            ),
            catalog_entry=CatalogEntry(
                dataset=DATASET_PRICES,
                quality_status="pass",
                published=True,
                latest_manifest_run_id="run-prices",
                readiness_status=READINESS_STATUS_AVAILABLE,
            ),
        )
    if dataset == DATASET_TRADE_CALENDAR:
        return ReaderResult(
            status="available",
            frame=pd.DataFrame(
                {
                    "trade_date": ["2026-01-02", "2026-01-03"],
                    "is_open": [True, True],
                }
            ),
            catalog_entry=CatalogEntry(dataset=DATASET_TRADE_CALENDAR, quality_status="pass", published=True),
        )
    if dataset == DATASET_INDEX_MEMBERS:
        return ReaderResult(
            status="available",
            frame=pd.DataFrame(
                {
                    "trade_date": ["2026-01-02", "2026-01-03"],
                    "index_code": ["399300.SZ", "399300.SZ"],
                    "symbol": ["AAA", "AAA"],
                    "effective_date": [date(2026, 1, 1), date(2026, 1, 1)],
                    "available_at": [date(2026, 1, 1), date(2026, 1, 1)],
                    "is_member": [True, True],
                    "is_pit_universe": [True, True],
                    "pit_status": [PIT_STATUS_AVAILABLE, PIT_STATUS_AVAILABLE],
                    "readiness_status": [READINESS_STATUS_AVAILABLE, READINESS_STATUS_AVAILABLE],
                }
            ),
            catalog_entry=CatalogEntry(
                dataset=DATASET_INDEX_MEMBERS,
                quality_status="pass",
                published=True,
                readiness_status=READINESS_STATUS_AVAILABLE,
                pit_status=PIT_STATUS_AVAILABLE,
            ),
        )
    return ReaderResult(
        status="required_missing",
        issues=[{"code": "w3_source_unresolved", "dataset": dataset}],
        remediation_spec={"auto_execute": False},
    )
