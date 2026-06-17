from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd

from engine.research_dataset import ResearchDatasetRequest, build_research_dataset
from engine.universe import SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
)
from market_data.readers import ReaderResult, read_stock_lifecycle


TARGET_FILES = (
    Path("market_data/readers.py"),
    Path("engine/research_dataset.py"),
)


def test_production_strict_pit_and_lifecycle_passes_with_alias_mode(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, pit_members_frame(pit_status="pass")),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, stock_lifecycle_frame()),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == "available"
    assert dataset.gate_result.status == "pass"
    assert dataset.metadata["universe"]["universe_mode"] == "pit"
    assert dataset.metadata["universe"]["is_pit_universe"] is True
    assert dataset.metadata["universe"]["pit_status"] in {"pass", "pit_available"}
    assert dataset.metadata["universe"]["as_of_join_violation_count"] == 0
    assert dataset.metadata["lifecycle"]["lifecycle_status"] == "pass"
    assert dataset.metadata["lifecycle_status"] == "pass"
    assert dataset.metadata["as_of_join_violation_count"] == 0
    assert {"pit_universe_research", "survivorship_bias_controlled"} <= set(dataset.allowed_claims)
    assert dataset.blocked_claims == []


def test_fixed_snapshot_and_explicit_symbols_are_exploratory_only(tmp_path: Path) -> None:
    exploratory = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="fixed_snapshot",
            realism_mode="exploratory",
            symbols=("AAA", "BBB"),
            benchmark_policy="proxy_allowed",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    strict = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="fixed_snapshot",
            realism_mode="production_strict",
            symbols=("AAA", "BBB"),
            benchmark_policy="hs300_required",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: ReaderResult(status="required_missing"),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, stock_lifecycle_frame()),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert exploratory.available is True
    assert exploratory.metadata["universe"]["is_pit_universe"] is False
    assert exploratory.metadata["survivorship_bias_note"] == SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE
    assert "fixed_snapshot_exploration" in exploratory.allowed_claims
    assert "pit_universe_research" not in exploratory.allowed_claims

    assert strict.available is False
    assert strict.metadata["universe"]["is_pit_universe"] is False
    assert strict.metadata["survivorship_bias_note"] == SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE
    assert any(item["claim"] == "pit_universe_research" for item in strict.blocked_claims)


def test_weights_and_stock_basic_alone_do_not_prove_pit_universe(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="required",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: ReaderResult(
                    status="required_missing",
                    issues=[{"code": "catalog_missing", "dataset": DATASET_INDEX_MEMBERS}],
                ),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, stock_lifecycle_frame()),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    codes = issue_codes(dataset)
    blocked_reasons = {item["reason_code"] for item in dataset.blocked_claims}
    assert dataset.available is False
    assert "index_weights_not_members" in codes
    assert "stock_basic_not_pit_universe" in codes
    assert {"index_weights_not_members", "stock_basic_not_pit_universe"} <= blocked_reasons
    assert dataset.metadata["universe"]["is_pit_universe"] is False


def test_as_of_violation_blocks_production_strict_lifecycle_gate(tmp_path: Path) -> None:
    future_lifecycle = stock_lifecycle_frame(available_at="2026-01-06")
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit_required",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, pit_members_frame()),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, future_lifecycle),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == "gate_failed"
    assert dataset.metadata["as_of_join_violation_count"] == 2
    assert dataset.metadata["lifecycle"]["lifecycle_status"] == "as_of_join_violation"
    assert "as_of_join_violation" in issue_codes(dataset)
    assert "survivorship_bias_controlled" not in dataset.allowed_claims


def test_lifecycle_missing_blocks_production_strict(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit_required",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, pit_members_frame()),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(
                    DATASET_STOCK_BASIC,
                    stock_lifecycle_frame().drop(columns=["list_date"]),
                ),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == "required_missing"
    assert dataset.metadata["lifecycle"]["lifecycle_status"] == "lifecycle_missing"
    assert "lifecycle_missing" in issue_codes(dataset)
    assert any(item["claim"] == "survivorship_bias_controlled" for item in dataset.blocked_claims)


def test_stock_lifecycle_source_unresolved_fails_fast(tmp_path: Path) -> None:
    result = read_stock_lifecycle(
        tmp_path / "lake",
        required=True,
        reader=lambda *_args, **_kwargs: available_reader(
            DATASET_STOCK_BASIC,
            stock_lifecycle_frame(source_interface="UNRESOLVED"),
            source_interface="UNRESOLVED",
        ),
    )

    assert result.status == "required_missing"
    assert {issue["code"] for issue in result.issues} >= {"source_unresolved"}
    assert result.remediation_spec["reason"] == "source_unresolved"
    assert result.remediation_spec["auto_execute"] is False


def test_s02_forbidden_boundaries_are_static_and_no_secret_leakage(tmp_path: Path, monkeypatch) -> None:
    fake_secret = "CR011_S02_FAKE_TOKEN_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("TUSHARE_TOKEN", fake_secret)
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
    }
    for path in TARGET_FILES:
        imports = imported_modules(path)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imports for forbidden in forbidden_modules)
        source = path.read_text(encoding="utf-8")
        assert "reports/experiment_17_21/factor_strategy_report.md" not in source
        assert "TUSHARE_TOKEN" not in source

    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit_required",
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, pit_members_frame()),
                DATASET_INDEX_WEIGHTS: available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
                DATASET_STOCK_BASIC: available_reader(DATASET_STOCK_BASIC, stock_lifecycle_frame()),
                DATASET_TRADE_STATUS: available_reader(DATASET_TRADE_STATUS, pd.DataFrame()),
                DATASET_PRICES_LIMIT: available_reader(DATASET_PRICES_LIMIT, pd.DataFrame()),
                DATASET_EVENTS: available_reader(DATASET_EVENTS, pd.DataFrame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )
    combined = json.dumps([dataset.metadata, [issue.to_dict() for issue in dataset.issues]], ensure_ascii=False, default=str)
    assert fake_secret not in combined
    assert dataset.metadata.get("network_calls", 0) == 0
    assert dataset.metadata.get("lake_writes", 0) == 0
    assert dataset.metadata.get("credential_reads", 0) == 0
    assert dataset.metadata.get("legacy_data_operations", 0) == 0


def prices_frame() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date in ("2026-01-02", "2026-01-05"):
        rows.extend(
            [
                {
                    "trade_date": trade_date,
                    "symbol": "AAA",
                    "close": 10.0,
                    "adjusted_close": 10.0,
                    "adj_factor": 1.0,
                    "adjustment_policy": "qfq",
                    "source_run_id": "run-prices",
                    "lineage_raw_checksum": "checksum-prices",
                },
                {
                    "trade_date": trade_date,
                    "symbol": "BBB",
                    "close": 20.0,
                    "adjusted_close": 20.0,
                    "adj_factor": 1.0,
                    "adjustment_policy": "qfq",
                    "source_run_id": "run-prices",
                    "lineage_raw_checksum": "checksum-prices",
                },
            ]
        )
    return pd.DataFrame(rows)


def calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "is_open": True},
            {"trade_date": "2026-01-03", "is_open": False},
            {"trade_date": "2026-01-05", "is_open": True},
        ]
    )


def pit_members_frame(*, pit_status: str = "pit_available", available_at: str = "2026-01-01") -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade_date in ("2026-01-02", "2026-01-05"):
        for symbol in ("AAA", "BBB"):
            rows.append(
                {
                    "trade_date": trade_date,
                    "index_code": "399300.SZ",
                    "symbol": symbol,
                    "effective_date": "2025-12-31",
                    "available_at": available_at,
                    "is_member": True,
                    "is_pit_universe": True,
                    "pit_status": pit_status,
                    "readiness_status": "available",
                    "source_interface": "index_members.fixture",
                }
            )
    return pd.DataFrame(rows)


def index_weights_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "AAA", "weight": 0.5},
            {"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "BBB", "weight": 0.5},
        ]
    )


def stock_lifecycle_frame(
    *,
    available_at: str = "2026-01-01",
    list_status: str = "L",
    source_interface: str = "stock_basic.fixture",
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "list_date": "2020-01-01",
                "delist_date": None,
                "list_status": list_status,
                "available_at": available_at,
                "readiness_status": "available",
                "pit_status": "pit_available",
                "source_interface": source_interface,
            },
            {
                "symbol": "BBB",
                "list_date": "2020-01-01",
                "delist_date": None,
                "list_status": list_status,
                "available_at": available_at,
                "readiness_status": "available",
                "pit_status": "pit_available",
                "source_interface": source_interface,
            },
        ]
    )


def available_reader(
    dataset: str,
    frame: pd.DataFrame,
    *,
    source_interface: str | None = None,
) -> ReaderResult:
    return ReaderResult(
        status="available",
        frame=frame,
        catalog_entry=CatalogEntry(
            dataset=dataset,
            start_date="2026-01-02",
            end_date="2026-01-05",
            quality_status="pass",
            dataset_status="available",
            readiness_status="available",
            latest_manifest_run_id=f"run-{dataset}",
            source="fixture",
            source_interface=source_interface or f"{dataset}.fixture",
            lineage_raw_checksum=f"checksum-{dataset}",
            published=True,
        ),
    )


def make_reader(results: dict[str, ReaderResult]) -> Any:
    def reader(
        dataset: str,
        lake_root: str | Path | None,
        filters: dict[str, Any] | None = None,
        quality_policy: Any = None,
        *,
        required: bool = False,
    ) -> ReaderResult:
        del lake_root, filters, quality_policy, required
        return results[dataset]

    return reader


def issue_codes(dataset: Any) -> set[str]:
    return {issue.code for issue in dataset.issues}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
