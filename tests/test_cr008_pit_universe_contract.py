from __future__ import annotations

import ast
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.research_dataset import ResearchDatasetRequest, ResearchDatasetStatus, build_research_dataset
from engine.universe import (
    SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE,
    UniverseRequest,
    resolve_universe,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
)
from market_data.readers import ReaderResult


TARGET_FILES = (
    Path("engine/universe.py"),
    Path("engine/research_dataset.py"),
    Path("market_data/readers.py"),
)


def test_pit_available_resolution_marks_pit_universe() -> None:
    result = resolve_universe(
        UniverseRequest(
            index_code="399300.SZ",
            start_date="2026-01-02",
            end_date="2026-01-05",
            analysis_mode="research",
            universe_mode="pit_required",
            decision_calendar=("2026-01-02", "2026-01-05"),
        ),
        index_members_result=available_reader(DATASET_INDEX_MEMBERS, pit_members_frame()),
    )

    assert result.status == "available"
    assert result.metadata.universe_mode == "pit"
    assert result.metadata.is_pit_universe is True
    assert result.metadata.pit_status == "pit_available"
    assert result.metadata.readiness_status == "available"
    assert result.metadata.survivorship_bias_note == ""
    assert result.symbols == ["AAA", "BBB"]
    assert result.members is not None
    assert set(result.members["trade_date"]) == {date(2026, 1, 2), date(2026, 1, 5)}


def test_pit_required_missing_fails_and_index_weights_do_not_substitute() -> None:
    result = resolve_universe(
        UniverseRequest(
            index_code="399300.SZ",
            start_date="2026-01-02",
            end_date="2026-01-05",
            analysis_mode="research",
            universe_mode="pit_required",
        ),
        index_members_result=ReaderResult(
            status="required_missing",
            issues=[{"code": "catalog_missing", "dataset": DATASET_INDEX_MEMBERS}],
        ),
        index_weights_result=available_reader(DATASET_INDEX_WEIGHTS, index_weights_frame()),
    )

    codes = issue_codes(result)
    assert result.status == "required_missing"
    assert result.metadata.is_pit_universe is False
    assert result.metadata.universe_mode == "missing"
    assert "index_weights_not_members" in codes
    assert "pit_universe_required_missing" in codes
    assert result.allowed_claims == []


def test_fixed_snapshot_writes_survivorship_warning_and_never_marks_pit() -> None:
    result = resolve_universe(
        UniverseRequest(
            index_code="399300.SZ",
            start_date="2026-01-02",
            end_date="2026-01-05",
            analysis_mode="exploratory",
            universe_mode="fixed_snapshot",
            symbols=("AAA", "BBB"),
        )
    )

    assert result.status == "available_with_warnings"
    assert result.metadata.universe_mode == "fixed_snapshot"
    assert result.metadata.is_pit_universe is False
    assert result.metadata.pit_status == "non_pit_snapshot"
    assert result.metadata.survivorship_bias_note == SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE
    assert any(item.get("code") == "fixed_snapshot_survivorship_bias" for item in result.known_limitations)
    assert "pit_universe_research" not in result.allowed_claims


def test_quality_pass_does_not_prove_pit_available() -> None:
    frame = pit_members_frame().drop(columns=["available_at"]).assign(pit_status="pit_incomplete")
    result = resolve_universe(
        UniverseRequest(
            index_code="399300.SZ",
            start_date="2026-01-02",
            end_date="2026-01-05",
            analysis_mode="research",
            universe_mode="pit_required",
            decision_calendar=("2026-01-02", "2026-01-05"),
        ),
        index_members_result=available_reader(DATASET_INDEX_MEMBERS, frame),
    )

    assert result.status == "gate_failed"
    assert result.metadata.is_pit_universe is False
    assert result.metadata.pit_status == "pit_incomplete"
    assert "quality_pass_not_pit_available" in issue_codes(result)
    assert "pit_universe_required_missing" in issue_codes(result)


def test_stock_basic_current_snapshot_does_not_prove_pit_universe() -> None:
    result = resolve_universe(
        UniverseRequest(
            index_code="399300.SZ",
            start_date="2026-01-02",
            end_date="2026-01-05",
            analysis_mode="research",
            universe_mode="pit_required",
        ),
        index_members_result=ReaderResult(status="required_missing"),
        stock_basic_result=available_reader(
            DATASET_STOCK_BASIC,
            pd.DataFrame([{"symbol": "AAA", "name": "A Corp", "list_date": "2020-01-01"}]),
        ),
    )

    assert result.metadata.is_pit_universe is False
    assert "stock_basic_not_pit_universe" in issue_codes(result)
    assert "pit_universe_required_missing" in issue_codes(result)


def test_build_research_dataset_merges_pit_universe_metadata(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit_required",
            analysis_mode="research",
            benchmark_policy="proxy_allowed",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, pit_members_frame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE.value
    assert dataset.gate_result.status == "pass"
    assert dataset.metadata["universe"]["universe_mode"] == "pit"
    assert dataset.metadata["universe"]["is_pit_universe"] is True
    assert dataset.metadata["universe"]["pit_status"] == "pit_available"
    assert dataset.metadata["universe"]["readiness_status"] == "available"
    assert dataset.metadata["universe"]["survivorship_bias_note"] == ""
    assert dataset.metadata["is_pit_universe"] is True
    assert "pit_universe_research" in dataset.allowed_claims


def test_build_research_dataset_merges_fixed_snapshot_disclosure_without_pit_claim(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="fixed_snapshot",
            analysis_mode="research",
            benchmark_policy="proxy_allowed",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, fixed_members_frame()),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE.value
    assert dataset.metadata["universe"]["universe_mode"] == "fixed_snapshot"
    assert dataset.metadata["universe"]["is_pit_universe"] is False
    assert dataset.metadata["universe"]["survivorship_bias_note"] == SURVIVORSHIP_BIAS_FIXED_SNAPSHOT_NOTE
    assert any(item.get("code") == "fixed_snapshot_survivorship_bias" for item in dict_limitations(dataset))
    assert "fixed_snapshot_exploration" in dataset.allowed_claims
    assert "pit_universe_research" not in dataset.allowed_claims
    assert "research_input_contract_available" not in dataset.allowed_claims


def test_read_index_universe_exposes_quality_pass_not_pit_available(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import market_data.readers as readers

    def fake_read_dataset(*_: Any, **__: Any) -> ReaderResult:
        return available_reader(DATASET_INDEX_MEMBERS, fixed_members_frame())

    monkeypatch.setattr(readers, "read_dataset", fake_read_dataset)

    result = readers.read_index_universe(tmp_path / "lake", pit_required=True)

    codes = {issue["code"] for issue in result.issues}
    assert result.status == "unavailable"
    assert "quality_pass_not_pit_available" in codes
    assert "pit_universe_not_available" in codes
    assert result.remediation_spec["not_substituted_by"] == DATASET_INDEX_WEIGHTS
    assert result.remediation_spec["auto_execute"] is False


def test_s05_forbidden_imports_old_report_credentials_and_secret_leakage_are_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_secret = "CR008_S05_FAKE_TOKEN_SHOULD_NOT_APPEAR"
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
        assert "reports/data_quality_report.csv" not in source
        assert "TUSHARE_TOKEN" not in source

    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            universe_mode="pit_required",
            analysis_mode="research",
            benchmark_policy="proxy_allowed",
            forward_return_horizon=2,
        ),
        reader=make_reader(
            {
                DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
                DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
                DATASET_INDEX_MEMBERS: ReaderResult(status="required_missing"),
            }
        ),
        benchmark_resolver=lambda **_: {"benchmark_status": "available", "benchmark_kind": "hs300"},
    )

    combined = json.dumps(
        [dataset.metadata, [issue.to_dict() for issue in dataset.issues], dataset.known_limitations],
        ensure_ascii=False,
        default=str,
    )
    assert fake_secret not in combined
    assert dataset.available is False


def pit_members_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "symbol": "AAA",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "is_member": True,
                "is_pit_universe": True,
                "pit_status": "pit_available",
                "readiness_status": "available",
            },
            {
                "trade_date": "2026-01-02",
                "index_code": "399300.SZ",
                "symbol": "BBB",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "is_member": True,
                "is_pit_universe": True,
                "pit_status": "pit_available",
                "readiness_status": "available",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "symbol": "AAA",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "is_member": True,
                "is_pit_universe": True,
                "pit_status": "pit_available",
                "readiness_status": "available",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "symbol": "BBB",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "is_member": True,
                "is_pit_universe": True,
                "pit_status": "pit_available",
                "readiness_status": "available",
            },
            {
                "trade_date": "2026-01-05",
                "index_code": "399300.SZ",
                "symbol": "CCC",
                "effective_date": "2025-12-31",
                "available_at": "2026-01-01",
                "is_member": False,
                "is_pit_universe": True,
                "pit_status": "pit_available",
                "readiness_status": "available",
            },
        ]
    )


def fixed_members_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"index_code": "399300.SZ", "symbol": "AAA", "is_member": True},
            {"index_code": "399300.SZ", "symbol": "BBB", "is_member": True},
        ]
    )


def index_weights_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "AAA", "weight": 0.5},
            {"trade_date": "2026-01-02", "index_code": "399300.SZ", "con_code": "BBB", "weight": 0.5},
        ]
    )


def prices_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "symbol": "AAA", "close": 10.0, "adjusted_close": 10.0, "adjustment_policy": "qfq"},
            {"trade_date": "2026-01-02", "symbol": "BBB", "close": 20.0, "adjusted_close": 20.0, "adjustment_policy": "qfq"},
            {"trade_date": "2026-01-05", "symbol": "AAA", "close": 10.5, "adjusted_close": 10.5, "adjustment_policy": "qfq"},
            {"trade_date": "2026-01-05", "symbol": "BBB", "close": 20.5, "adjusted_close": 20.5, "adjustment_policy": "qfq"},
        ]
    )


def calendar_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_date": "2026-01-02", "is_open": True},
            {"trade_date": "2026-01-03", "is_open": False},
            {"trade_date": "2026-01-05", "is_open": True},
        ]
    )


def available_reader(dataset: str, frame: pd.DataFrame) -> ReaderResult:
    return ReaderResult(
        status="available",
        frame=frame,
        catalog_entry=CatalogEntry(
            dataset=dataset,
            start_date="2026-01-02",
            end_date="2026-01-05",
            quality_status="pass",
            dataset_status="available",
            latest_manifest_run_id=f"{dataset}-manifest",
            source="fixture",
            source_interface=f"{dataset}.fixture",
            lineage_raw_checksum=f"{dataset}-checksum",
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


def issue_codes(result: Any) -> set[str]:
    return {issue.code for issue in result.issues}


def dict_limitations(dataset: Any) -> list[dict[str, Any]]:
    return [item for item in dataset.known_limitations if isinstance(item, dict)]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules
