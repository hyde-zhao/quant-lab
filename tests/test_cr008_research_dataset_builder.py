from __future__ import annotations

import ast
from datetime import date
import inspect
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from engine import data_loader
from engine.data_loader import DataContractError, DataQualityGateError, load_research_backtest_data
from engine.research_dataset import (
    GateResult,
    ResearchDataset,
    ResearchDatasetIssue,
    ResearchDatasetRequest,
    ResearchDatasetStatus,
    build_research_dataset,
)
from market_data.benchmarks import (
    BenchmarkCoverage,
    BenchmarkResult,
    NextAction,
    RemediationJobSpec,
)
from market_data.catalog import CatalogEntry
from market_data.contracts import (
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_PRICES,
    DATASET_TRADE_CALENDAR,
    INTERFACE_HS300_INDEX_DAILY,
    SOURCE_TUSHARE,
)
from market_data.readers import ReaderResult, ResearchInputReaderRequest, read_research_inputs


TARGET_FILES = (
    Path("engine/research_dataset.py"),
    Path("engine/data_loader.py"),
    Path("market_data/readers.py"),
)


def test_happy_path_builds_research_dataset_with_metadata(tmp_path: Path) -> None:
    reader, reader_calls = make_reader(
        {
            DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
            DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, universe_frame()),
        }
    )
    benchmark, benchmark_calls = make_benchmark_resolver(make_benchmark_result("available"))

    dataset = build_research_dataset(
        ResearchDatasetRequest(
            lake_root=tmp_path / "lake",
            start_date="2026-01-02",
            end_date="2026-01-05",
            benchmark_policy="hs300_required",
            forward_return_horizon=5,
        ),
        reader=reader,
        benchmark_resolver=benchmark,
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE.value
    assert dataset.gate_result.status == "pass"
    assert dataset.close_df is not None
    assert list(dataset.close_df.columns) == ["AAA", "BBB"]
    assert dataset.calendar == [date(2026, 1, 2), date(2026, 1, 5)]
    assert dataset.universe_symbols == ["AAA", "BBB"]
    assert dataset.metadata["schema_name"] == "research_input_v1"
    assert dataset.metadata["schema_version"] == "research_input_v1"
    assert dataset.metadata["coverage"]["calendar_count"] == 2
    assert dataset.metadata["benchmark_status"] == "available"
    assert dataset.metadata["benchmark_kind"] == "hs300"
    assert dataset.metadata["universe_mode"] == "fixed_snapshot"
    assert dataset.metadata["adjustment_policy"] == "qfq"
    assert dataset.metadata["forward_return_horizon"] == 5
    assert dataset.metadata["quality_status"] == "pass"
    assert dataset.metadata["readiness_status"] == "research_ready"
    assert dataset.metadata["known_limitations"]
    assert dataset.metadata["allowed_claims"]
    assert dataset.remediation_spec["auto_execute"] is False
    assert {call["dataset"] for call in reader_calls} == {
        DATASET_PRICES,
        DATASET_TRADE_CALENDAR,
        DATASET_INDEX_MEMBERS,
    }
    assert benchmark_calls[0]["lake_root"] == tmp_path / "lake"
    assert benchmark_calls[0]["required"] is True


def test_prices_missing_returns_typed_result_and_no_auto_execute(tmp_path: Path) -> None:
    reader, _ = make_reader(
        {
            DATASET_PRICES: ReaderResult(
                status="required_missing",
                issues=[{"code": "canonical_missing", "dataset": DATASET_PRICES}],
                remediation_spec={"action": "run_backfill", "auto_execute": True},
            ),
            DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, universe_frame()),
        }
    )

    dataset = build_research_dataset(
        request(tmp_path),
        reader=reader,
        benchmark_resolver=make_benchmark_resolver(make_benchmark_result("available"))[0],
    )

    assert dataset.status == ResearchDatasetStatus.REQUIRED_MISSING.value
    assert any(issue.dataset == DATASET_PRICES and issue.code == "prices_required_missing" for issue in dataset.issues)
    assert dataset.close_df is None
    assert_all_auto_execute_false(dataset.remediation_spec)
    assert dataset.remediation_spec["actions"]


def test_quality_failed_is_typed_and_blocks_available_status(tmp_path: Path) -> None:
    reader, _ = make_reader(
        {
            DATASET_PRICES: ReaderResult(
                status="quality_failed",
                issues=[{"code": "quality_failed", "dataset": DATASET_PRICES}],
            ),
            DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, universe_frame()),
        }
    )

    dataset = build_research_dataset(
        request(tmp_path),
        reader=reader,
        benchmark_resolver=make_benchmark_resolver(make_benchmark_result("available"))[0],
    )

    assert dataset.status == ResearchDatasetStatus.QUALITY_FAILED.value
    assert dataset.metadata["quality_status"] == "fail"
    assert any(issue.code == "prices_quality_failed" for issue in dataset.issues)


def test_proxy_allowed_benchmark_missing_does_not_populate_hs300_fields(tmp_path: Path) -> None:
    reader, _ = make_reader(
        {
            DATASET_PRICES: available_reader(DATASET_PRICES, prices_frame()),
            DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, universe_frame()),
        }
    )

    dataset = build_research_dataset(
        request(tmp_path, benchmark_policy="proxy_allowed"),
        reader=reader,
        benchmark_resolver=make_benchmark_resolver(make_benchmark_result("required_missing", missing_reason="coverage_gap"))[0],
    )

    assert dataset.status == ResearchDatasetStatus.AVAILABLE_WITH_WARNINGS.value
    assert dataset.metadata["benchmark_status"] == "required_missing"
    assert dataset.metadata["benchmark_kind"] == "proxy_baseline"
    assert dataset.metadata["benchmark_missing_reason"] == "coverage_gap"
    assert "real_hs300_excess_return" not in dataset.allowed_claims
    assert_no_top_level_hs300(dataset.metadata)
    assert_all_auto_execute_false(dataset.remediation_spec)


def test_invalid_lake_root_rejects_env_fallback_and_does_not_call_readers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_secret = "CR008_FAKE_TOKEN_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path / "env-lake"))
    monkeypatch.setenv("TUSHARE_TOKEN", fake_secret)

    def forbidden_reader(*_: Any, **__: Any) -> ReaderResult:
        raise AssertionError("reader must not be called for invalid request")

    def forbidden_benchmark(*_: Any, **__: Any) -> BenchmarkResult:
        raise AssertionError("benchmark resolver must not be called for invalid request")

    missing_root = build_research_dataset(
        ResearchDatasetRequest(lake_root=None, start_date="2026-01-02", end_date="2026-01-05"),
        reader=forbidden_reader,
        benchmark_resolver=forbidden_benchmark,
    )
    old_data_root = build_research_dataset(
        ResearchDatasetRequest(lake_root="data", start_date="2026-01-02", end_date="2026-01-05"),
        reader=forbidden_reader,
        benchmark_resolver=forbidden_benchmark,
    )

    assert missing_root.status == ResearchDatasetStatus.INVALID_REQUEST.value
    assert any(issue.code == "lake_root_required" for issue in missing_root.issues)
    assert old_data_root.status == ResearchDatasetStatus.INVALID_REQUEST.value
    assert any(issue.code == "repo_data_reference_only" for issue in old_data_root.issues)
    combined = json.dumps(
        [missing_root.metadata, old_data_root.metadata, [issue.to_dict() for issue in missing_root.issues]],
        ensure_ascii=False,
        default=str,
    )
    assert fake_secret not in combined
    assert "env-lake" not in combined


def test_read_research_inputs_requires_explicit_lake_root_without_env_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", str(tmp_path / "env-lake"))

    def forbidden_reader(*_: Any, **__: Any) -> ReaderResult:
        raise AssertionError("reader must not be called without explicit lake_root")

    missing = read_research_inputs(ResearchInputReaderRequest(lake_root=None), reader=forbidden_reader)
    repo_data = read_research_inputs(ResearchInputReaderRequest(lake_root="data"), reader=forbidden_reader)

    assert set(missing) == {DATASET_PRICES, DATASET_TRADE_CALENDAR, DATASET_INDEX_MEMBERS}
    assert all(result.status == "required_missing" for result in missing.values())
    assert all(result.issues[0]["code"] == "lake_root_missing" for result in missing.values())
    assert all(result.status == "invalid_request" for result in repo_data.values())
    assert all(result.issues[0]["code"] == "repo_data_reference_only" for result in repo_data.values())
    assert_all_auto_execute_false({dataset: result.remediation_spec for dataset, result in missing.items()})


def test_forbidden_imports_old_report_and_destructive_operations_are_absent_from_builder_path() -> None:
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

    assert not has_forbidden_io_call(Path("engine/research_dataset.py"))
    assert not has_forbidden_io_call(Path("market_data/readers.py"))
    assert not has_destructive_file_call(Path("engine/research_dataset.py"))
    assert not has_destructive_file_call(Path("market_data/readers.py"))

    adapter_source = inspect.getsource(data_loader.load_research_backtest_data)
    assert "reports/data_quality_report.csv" not in adapter_source
    assert 'Path("data")' not in adapter_source
    assert "'data'" not in adapter_source
    assert '"data"' not in adapter_source


def test_data_loader_adapter_is_explicit_and_preserves_default_loader_behavior(tmp_path: Path) -> None:
    close_df = pd.DataFrame({"AAA": [10.0]}, index=[date(2026, 1, 2)])
    available = ResearchDataset(
        status="available",
        close_df=close_df,
        calendar=[date(2026, 1, 2)],
        universe_symbols=["AAA"],
        metadata={"schema_name": "research_input_v1", "quality_status": "pass"},
        gate_result=GateResult(status="pass"),
    )

    def available_builder(req: ResearchDatasetRequest) -> ResearchDataset:
        assert req.lake_root == tmp_path / "lake"
        return available

    loaded = load_research_backtest_data(
        {
            "lake_root": tmp_path / "lake",
            "start_date": "2026-01-02",
            "end_date": "2026-01-02",
        },
        builder=available_builder,
    )

    assert loaded.close_df.equals(close_df)
    assert loaded.universe == ["AAA"]
    assert loaded.calendar == [date(2026, 1, 2)]
    assert loaded.metadata["input_mode"] == "research_dataset_builder"
    assert data_loader.LoaderConfig().input_mode == "legacy_flat"

    quality_failed = ResearchDataset(
        status="quality_failed",
        issues=[ResearchDatasetIssue(code="prices_quality_failed", dataset=DATASET_PRICES, message="fail")],
    )
    missing = ResearchDataset(
        status="required_missing",
        issues=[ResearchDatasetIssue(code="prices_required_missing", dataset=DATASET_PRICES, message="missing")],
    )
    with pytest.raises(DataQualityGateError):
        load_research_backtest_data(request(tmp_path), builder=lambda _: quality_failed)
    with pytest.raises(DataContractError):
        load_research_backtest_data(request(tmp_path), builder=lambda _: missing)


def test_remediation_normalization_handles_reader_and_benchmark_specs(tmp_path: Path) -> None:
    reader, _ = make_reader(
        {
            DATASET_PRICES: ReaderResult(
                status="required_missing",
                issues=[{"code": "canonical_missing"}],
                remediation_spec={"job": {"action": "backfill", "auto_execute": True}},
            ),
            DATASET_TRADE_CALENDAR: available_reader(DATASET_TRADE_CALENDAR, calendar_frame()),
            DATASET_INDEX_MEMBERS: available_reader(DATASET_INDEX_MEMBERS, universe_frame()),
        }
    )
    benchmark_result = make_benchmark_result("required_missing", missing_reason="coverage_gap", required=True)

    dataset = build_research_dataset(
        request(tmp_path, benchmark_policy="hs300_required"),
        reader=reader,
        benchmark_resolver=make_benchmark_resolver(benchmark_result)[0],
    )

    assert dataset.status == ResearchDatasetStatus.REQUIRED_MISSING.value
    assert dataset.remediation_spec["actions"]
    assert_all_auto_execute_false(dataset.remediation_spec)


def request(tmp_path: Path, *, benchmark_policy: str = "hs300_required") -> ResearchDatasetRequest:
    return ResearchDatasetRequest(
        lake_root=tmp_path / "lake",
        start_date="2026-01-02",
        end_date="2026-01-05",
        benchmark_policy=benchmark_policy,
    )


def prices_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2026-01-02",
                "symbol": "AAA",
                "close": 10.0,
                "adjusted_close": 10.0,
                "adjustment_policy": "qfq",
                "source_run_id": "prices-run",
                "lineage_raw_checksum": "prices-checksum",
            },
            {
                "trade_date": "2026-01-02",
                "symbol": "BBB",
                "close": 20.0,
                "adjusted_close": 20.0,
                "adjustment_policy": "qfq",
                "source_run_id": "prices-run",
                "lineage_raw_checksum": "prices-checksum",
            },
            {
                "trade_date": "2026-01-05",
                "symbol": "AAA",
                "close": 10.5,
                "adjusted_close": 10.5,
                "adjustment_policy": "qfq",
                "source_run_id": "prices-run",
                "lineage_raw_checksum": "prices-checksum",
            },
            {
                "trade_date": "2026-01-05",
                "symbol": "BBB",
                "close": 20.5,
                "adjusted_close": 20.5,
                "adjustment_policy": "qfq",
                "source_run_id": "prices-run",
                "lineage_raw_checksum": "prices-checksum",
            },
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


def universe_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "is_member": True},
            {"symbol": "BBB", "is_member": True},
            {"symbol": "CCC", "is_member": False},
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


def make_reader(results: dict[str, ReaderResult]) -> tuple[Any, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    def reader(
        dataset: str,
        lake_root: str | Path | None,
        filters: dict[str, Any] | None = None,
        quality_policy: Any = None,
        *,
        required: bool = False,
    ) -> ReaderResult:
        calls.append(
            {
                "dataset": dataset,
                "lake_root": lake_root,
                "filters": filters,
                "quality_policy": quality_policy,
                "required": required,
            }
        )
        return results[dataset]

    return reader, calls


def make_benchmark_resolver(result: BenchmarkResult) -> tuple[Any, list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []

    def resolver(**kwargs: Any) -> BenchmarkResult:
        calls.append(kwargs)
        return result

    return resolver, calls


def make_benchmark_result(
    status: str,
    *,
    missing_reason: str | None = None,
    required: bool = False,
) -> BenchmarkResult:
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
            numerator=2 if available else 0,
            denominator=2,
            ratio=1.0 if available else 0.0,
            missing_trade_dates=[] if available else ["2026-01-05"],
            gap_reason=reason,
            price_trade_dates_count=2,
            price_overlap_count=2 if available else 0,
        ),
        quality_status="pass" if available else "missing",
        missing_reason=reason,
        required=required,
        benchmark_kind="price_index",
        next_action=None if available else NextAction(type="run_data_layer_backfill", owner="user"),
        remediation_job_spec=None
        if available
        else RemediationJobSpec(
            start_date="2026-01-02",
            end_date="2026-01-05",
            reason=reason or "coverage_gap",
            dry_run=True,
        ),
        catalog_entry=None,
        run_id="benchmark-run" if available else None,
        lineage={"source_run_id": "benchmark-run"} if available else {"status": "lineage_unavailable"},
        frame=None,
    )


def assert_all_auto_execute_false(value: Any) -> None:
    if isinstance(value, dict):
        if "auto_execute" in value:
            assert value["auto_execute"] is False
        for item in value.values():
            assert_all_auto_execute_false(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_all_auto_execute_false(item)


def assert_no_top_level_hs300(payload: dict[str, Any]) -> None:
    assert "hs300_index" not in payload
    assert not any(key.startswith("hs300_") for key in payload)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def has_forbidden_io_call(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    io_calls = {"open", "read_text", "read_bytes", "read_csv", "read_parquet"}
    forbidden_literals = {"reports/data_quality_report.csv", "data"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node.func) not in io_calls:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and str(arg.value) in forbidden_literals:
                return True
    return False


def has_destructive_file_call(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    destructive = {"unlink", "rmdir", "remove", "rmtree"}
    return any(isinstance(node, ast.Call) and call_name(node.func) in destructive for node in ast.walk(tree))


def call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
