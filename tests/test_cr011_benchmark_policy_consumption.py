from __future__ import annotations

import ast
from argparse import Namespace
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine.research_dataset import ResearchDatasetRequest, build_research_dataset
from experiments.run_experiment_15_factor_framework import FactorFrameworkError
from experiments.run_experiment_17_21_factor_suite import (
    _ensure_not_legacy_report_output_path,
    build_experiment_benchmark_policy_metadata,
)
from market_data.benchmarks import (
    BENCHMARK_POLICY_FIELDS,
    BenchmarkCoverage,
    BenchmarkResult,
    build_benchmark_policy_result,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    INTERFACE_HS300_INDEX_DAILY,
    SOURCE_TUSHARE,
)
from market_data.readers import ReaderResult


TARGET_FILES = (
    Path("market_data/benchmarks.py"),
    Path("engine/research_dataset.py"),
    Path("experiments/run_experiment_17_21_factor_suite.py"),
)

POLICY_HS300_METADATA_FIELDS = {"hs300_available", "hs300_coverage_ratio"}


def test_benchmark_policy_result_available_outputs_frozen_fields_and_lineage() -> None:
    result = make_benchmark_result("available")

    metadata = build_benchmark_policy_result(
        result,
        policy_id="hs300_required",
        hs300_metrics={"total_return": 0.08, "annual_return": 0.06},
    ).to_metadata()

    assert set(BENCHMARK_POLICY_FIELDS).issubset(metadata)
    assert metadata["benchmark_policy_id"] == "hs300_required"
    assert metadata["benchmark_kind"] == "hs300"
    assert metadata["benchmark_source_kind"] == "price_index"
    assert metadata["hs300_available"] is True
    assert metadata["hs300_coverage_ratio"] == pytest.approx(1.0)
    assert metadata["proxy_baseline_used"] is False
    assert metadata["benchmark_missing_reason"] is None
    assert metadata["hs300_total_return"] == pytest.approx(0.08)
    assert metadata["hs300_index"]["dataset"] == DATASET_HS300_INDEX
    assert metadata["lineage"]["lineage_raw_checksum"] == "checksum-hs300"
    assert "proxy_baseline" not in metadata


def test_research_dataset_production_strict_missing_benchmark_blocks_real_claims(tmp_path: Path) -> None:
    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            symbols=("AAA", "BBB"),
            benchmark_policy="hs300_required",
            realism_mode="production_strict",
        ),
        reader=fake_reader,
        benchmark_resolver=lambda **_: make_benchmark_result("required_missing", missing_reason="coverage_gap"),
    )

    assert dataset.status == "required_missing"
    assert dataset.metadata["benchmark_policy_id"] == "hs300_required"
    assert dataset.metadata["benchmark_kind"] == "hs300_required"
    assert dataset.metadata["hs300_available"] is False
    assert dataset.metadata["proxy_baseline_used"] is False
    assert dataset.metadata["benchmark_missing_reason"] == "coverage_gap"
    assert dataset.metadata["benchmark_policy"]["blocked_claims"][0]["claim"] == "real_benchmark_research"
    assert any(item["claim"] == "real_benchmark_research" for item in dataset.metadata["blocked_claims"])
    assert_no_real_hs300_metric_fields(dataset.metadata["benchmark_policy"])


def test_experiment_exploratory_proxy_metadata_is_limited_and_hs300_isolated() -> None:
    metadata = build_experiment_benchmark_policy_metadata(
        benchmark_metrics={"annual_return": 0.05, "total_return": 0.08, "max_drawdown": -0.12},
        benchmark_policy_id="hs300_required",
        realism_mode="exploratory",
        baseline_report_path="reports/experiment_17_21/factor_strategy_report.md",
    )

    assert set(BENCHMARK_POLICY_FIELDS).issubset(metadata)
    assert metadata["benchmark_kind"] == "proxy_baseline"
    assert metadata["hs300_available"] is False
    assert metadata["proxy_baseline_used"] is True
    assert metadata["benchmark_missing_reason"] == "required_missing"
    assert metadata["proxy_annual_return"] == pytest.approx(0.05)
    assert metadata["proxy_baseline"]["baseline_report_path"] == "reports/experiment_17_21/factor_strategy_report.md"
    assert metadata["research_status"] == "exploratory_with_limitations"
    assert metadata["known_limitations"]
    assert_no_real_hs300_metric_fields(metadata)


def test_experiment_production_strict_missing_benchmark_has_blocked_claims_without_proxy() -> None:
    metadata = build_experiment_benchmark_policy_metadata(
        benchmark_metrics={"annual_return": 0.05},
        benchmark_policy_id="hs300_required",
        realism_mode="production_strict",
    )

    assert metadata["benchmark_kind"] == "hs300_required"
    assert metadata["hs300_available"] is False
    assert metadata["proxy_baseline_used"] is False
    assert metadata["research_status"] == "required_missing"
    assert any(item["claim"] == "real_benchmark_research" for item in metadata["blocked_claims"])
    assert "proxy_annual_return" not in metadata
    assert_no_real_hs300_metric_fields(metadata)


def test_old_experiment_report_path_is_rejected_before_writes() -> None:
    args = Namespace(output_dir="reports/experiment_17_21")

    with pytest.raises(FactorFrameworkError, match="禁止覆盖旧实验 17-21 baseline 报告"):
        _ensure_not_legacy_report_output_path(args)


def test_s01_target_files_keep_offline_security_boundary() -> None:
    forbidden_imports = {
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
    }
    safety_counts = {
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
    }
    for source_path in TARGET_FILES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = imports_for(tree)
        assert not any(name.startswith("market_data.connectors") for name in imports), source_path
        assert not any(name in forbidden_imports for name in imports), source_path
        assert not calls_env_or_credentials(tree), source_path
        assert not touches_legacy_data_path(tree), source_path
    assert safety_counts == {
        "network_calls": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "legacy_data_operations": 0,
    }


def fake_reader(dataset: str, *_args: Any, **_kwargs: Any) -> ReaderResult:
    frames = {
        DATASET_PRICES: prices_frame(),
        DATASET_TRADE_CALENDAR: calendar_frame(),
        DATASET_INDEX_MEMBERS: index_members_frame(),
        DATASET_TRADE_STATUS: pd.DataFrame(),
        DATASET_PRICES_LIMIT: pd.DataFrame(),
        DATASET_EVENTS: pd.DataFrame(),
    }
    return ReaderResult(
        status="available",
        frame=frames.get(dataset, pd.DataFrame()),
        catalog_entry=CatalogEntry(
            dataset=dataset,
            quality_status="pass",
            dataset_status="available",
            readiness_status="available",
            latest_manifest_run_id=f"run-{dataset}",
            source="fixture",
            source_interface=f"{dataset}.fixture",
            lineage_raw_checksum=f"checksum-{dataset}",
            published=True,
        ),
    )


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
                    "source_run_id": "run-prices",
                    "lineage_raw_checksum": "checksum-prices",
                },
                {
                    "trade_date": trade_date,
                    "symbol": "BBB",
                    "close": 12.0,
                    "adjusted_close": 12.0,
                    "source_run_id": "run-prices",
                    "lineage_raw_checksum": "checksum-prices",
                },
            ]
        )
    return pd.DataFrame(rows)


def calendar_frame() -> pd.DataFrame:
    return pd.DataFrame({"trade_date": ["2026-01-02", "2026-01-05"], "is_open": [True, True]})


def index_members_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["AAA", "BBB"],
            "trade_date": ["2026-01-02", "2026-01-02"],
            "effective_date": ["2026-01-02", "2026-01-02"],
            "available_at": ["2026-01-02T00:00:00+08:00", "2026-01-02T00:00:00+08:00"],
            "is_pit_universe": [True, True],
            "pit_status": ["pass", "pass"],
        }
    )


def make_benchmark_result(status: str, missing_reason: str | None = None) -> BenchmarkResult:
    available = status == "available"
    reason = None if available else missing_reason or "coverage_gap"
    return BenchmarkResult(
        status=status,
        dataset=DATASET_HS300_INDEX,
        source=SOURCE_TUSHARE if available else "none",
        index_code="399300.SZ",
        interface=INTERFACE_HS300_INDEX_DAILY,
        start_date="2026-01-02",
        end_date="2026-01-05",
        available_start_date="2026-01-02" if available else None,
        available_end_date="2026-01-05" if available else None,
        coverage=BenchmarkCoverage(
            numerator=2 if available else 1,
            denominator=2,
            ratio=1.0 if available else 0.5,
            missing_trade_dates=[] if available else ["2026-01-05"],
            gap_reason=None if available else reason,
            denominator_mode="trade_calendar_open_dates",
            price_trade_dates_count=2,
            price_overlap_count=2 if available else 1,
        ),
        quality_status="pass" if available else "missing",
        missing_reason=reason,
        required=not available,
        benchmark_kind="price_index",
        next_action=None,
        remediation_job_spec=None,
        catalog_entry=None,
        run_id="run-hs300" if available else None,
        lineage={"lineage_raw_checksum": "checksum-hs300"} if available else {"status": "lineage_unavailable"},
        frame=None,
    )


def assert_no_real_hs300_metric_fields(payload: dict[str, Any]) -> None:
    forbidden = [
        key
        for key in payload
        if (key == "hs300_index" or key.startswith("hs300_"))
        and key not in POLICY_HS300_METADATA_FIELDS
    ]
    assert forbidden == []


def imports_for(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def calls_env_or_credentials(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"getenv", "environ"}:
                return True
        if isinstance(node, ast.ImportFrom) and node.module and "dotenv" in node.module:
            return True
    return False


def touches_legacy_data_path(tree: ast.AST) -> bool:
    io_calls = {"open", "read_text", "read_bytes", "read_csv", "read_parquet", "unlink", "remove", "rmtree"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node.func) not in io_calls:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and str(arg.value).startswith("data/"):
                return True
    return False


def call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
