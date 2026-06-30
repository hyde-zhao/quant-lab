from __future__ import annotations

import ast
from argparse import Namespace
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import pytest

from engine.research_dataset import (
    LEGACY_REPORT_POLICY,
    RESEARCH_INPUT_REQUIRED_FIELDS,
    RESEARCH_INPUT_SCHEMA_NAME,
    ResearchInputMetadataError,
    benchmark_metadata_from_result,
    build_research_input_metadata,
    metadata_to_dict,
    validate_research_input_metadata,
)
from engine.research_reporting import legacy_report_limitation, render_research_input_metadata_section
import experiments.run_data_benchmark_audit_exp14 as experiment_14
import experiments.run_factor_framework_exp15 as experiment_15


TARGET_FILES = [
    Path("engine/research_dataset.py"),
    Path("engine/research_reporting.py"),
    Path("experiments/run_data_benchmark_audit_exp14.py"),
    Path("experiments/run_factor_framework_exp15.py"),
]


def complete_payload() -> dict[str, Any]:
    return {
        "report_kind": "unit_test_report",
        "source_run_id": "unit-test-run",
        "coverage_start": "2020-01-01",
        "coverage_end": "2020-12-31",
        "benchmark": {
            "benchmark_status": "available",
            "benchmark_kind": "hs300_index",
            "missing_reason": "",
            "denominator_mode": "trade_calendar_open_dates",
            "coverage": {"ratio": 1.0, "denominator_mode": "trade_calendar_open_dates"},
            "quality_status": "pass",
            "lineage": {"manifest_run_id": "benchmark-manifest"},
        },
        "universe": {
            "universe_mode": "fixed_snapshot",
            "is_pit_universe": False,
            "pit_status": "unavailable",
            "survivorship_bias_note": "fixed snapshot disclosed",
        },
        "adjustment_policy": "qfq",
        "label_window": {
            "forward_return_horizon": 20,
            "label_available_end": "2020-12-01",
            "label_status": "available",
        },
        "quality": {
            "quality_status": "pass",
            "readiness_status": "research_ready",
        },
        "known_limitations": ["fixed snapshot disclosed"],
        "allowed_claims": ["framework_validation", "raw_factor_performance"],
        "legacy_report_policy": LEGACY_REPORT_POLICY,
    }


def test_required_fields_export_and_payload_is_not_mutated() -> None:
    payload = complete_payload()
    original = deepcopy(payload)

    metadata = build_research_input_metadata(payload)
    exported = metadata_to_dict(metadata)

    assert payload == original
    assert exported["schema_name"] == RESEARCH_INPUT_SCHEMA_NAME
    assert RESEARCH_INPUT_REQUIRED_FIELDS <= set(exported)
    assert exported["benchmark_status"] == "available"
    assert exported["universe_mode"] == "fixed_snapshot"
    assert exported["label_available_end"] == "2020-12-01"
    assert exported["legacy_report_policy"] == LEGACY_REPORT_POLICY
    assert validate_research_input_metadata(metadata) == []


@pytest.mark.parametrize(
    ("mutator", "missing_field"),
    [
        (lambda payload: payload["benchmark"].pop("benchmark_status"), "benchmark_status"),
        (lambda payload: payload["universe"].pop("universe_mode"), "universe_mode"),
        (lambda payload: payload["label_window"].pop("label_available_end"), "label_available_end"),
        (lambda payload: payload.__setitem__("known_limitations", []), "known_limitations"),
        (lambda payload: payload.pop("allowed_claims"), "allowed_claims"),
    ],
)
def test_missing_required_fields_fail(mutator: Any, missing_field: str) -> None:
    payload = complete_payload()
    mutator(payload)

    with pytest.raises(ResearchInputMetadataError) as exc_info:
        build_research_input_metadata(payload)

    issues = exc_info.value.issues
    assert any(issue.code == "missing_required_fields" and issue.field == missing_field for issue in issues)


def test_lineage_and_legacy_policy_fail_closed() -> None:
    payload = complete_payload()
    payload.pop("source_run_id")
    payload["legacy_report_policy"] = "current_truth"

    with pytest.raises(ResearchInputMetadataError) as exc_info:
        build_research_input_metadata(payload)

    codes = {issue.code for issue in exc_info.value.issues}
    assert "lineage_missing" in codes
    assert "legacy_report_current_truth_attempt" in codes


def test_benchmark_result_metadata_mapping_preserves_cr007_fields() -> None:
    class FakeBenchmarkResult:
        def to_metadata(self) -> dict[str, Any]:
            return {
                "status": "available",
                "dataset": "hs300_index",
                "index_code": "000300.SH",
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "coverage": {"ratio": 1.0, "denominator_mode": "trade_calendar_open_dates"},
                "quality_status": "pass",
                "missing_reason": "",
                "lineage": {"manifest_run_id": "bench-manifest"},
                "denominator_mode": "trade_calendar_open_dates",
                "price_overlap": {"status": "pass"},
            }

    mapped = benchmark_metadata_from_result(FakeBenchmarkResult())
    payload = complete_payload()
    payload["benchmark"] = mapped
    metadata = metadata_to_dict(build_research_input_metadata(payload))

    assert mapped["benchmark_status"] == "available"
    assert mapped["denominator_mode"] == "trade_calendar_open_dates"
    assert metadata["benchmark"]["dataset"] == "hs300_index"
    assert metadata["benchmark"]["price_overlap"]["status"] == "pass"


def test_legacy_report_limitation_does_not_read_old_report(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_file_access(*_: Any, **__: Any) -> Any:
        raise AssertionError("legacy report content must not be read")

    monkeypatch.setattr(Path, "exists", forbidden_file_access)
    monkeypatch.setattr(Path, "open", forbidden_file_access)
    monkeypatch.setattr(Path, "read_text", forbidden_file_access)

    legacy_path = Path("reports/data_quality_report.csv")
    limitation = legacy_report_limitation(legacy_path, "legacy_quality_report")
    assert experiment_14.load_quality_report(legacy_path) == []
    checks, issues = experiment_14.inspect_phase_report(Path("reports/experiment_13/backtest_report.md"), "2020-12-31")

    payload = complete_payload()
    payload["known_limitations"] = [limitation]
    section = render_research_input_metadata_section(payload)

    assert checks["legacy_report_policy"] == LEGACY_REPORT_POLICY
    assert issues
    assert "legacy_only_not_current_truth" in section
    assert "not_current_truth" in section
    assert "reports/data_quality_report.csv" in section


def test_experiment_cli_data_dir_must_be_explicit(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["run_data_benchmark_audit_exp14.py"])
    with pytest.raises(SystemExit):
        experiment_14.parse_args()
    assert "--data-dir" in capsys.readouterr().err

    monkeypatch.setattr(sys, "argv", ["run_factor_framework_exp15.py"])
    with pytest.raises(SystemExit):
        experiment_15.parse_args()
    assert "--data-dir" in capsys.readouterr().err

    with pytest.raises(ValueError, match="--data-dir"):
        experiment_14.require_explicit_data_dir(Namespace(data_dir=None))
    with pytest.raises(experiment_15.FactorFrameworkError, match="--data-dir"):
        experiment_15.require_explicit_data_dir(Namespace(data_dir=""))


def test_experiment_sources_do_not_default_to_old_data_or_read_legacy_reports() -> None:
    experiment_14_source = Path("experiments/run_data_benchmark_audit_exp14.py").read_text(encoding="utf-8")
    experiment_15_source = Path("experiments/run_factor_framework_exp15.py").read_text(encoding="utf-8")

    assert 'default="data"' not in experiment_14_source
    assert "default='data'" not in experiment_14_source
    assert 'default="data"' not in experiment_15_source
    assert "default='data'" not in experiment_15_source

    quality_source = ast.get_source_segment(experiment_14_source, _function_node(experiment_14_source, "load_quality_report")) or ""
    phase_source = ast.get_source_segment(experiment_14_source, _function_node(experiment_14_source, "inspect_phase_report")) or ""
    legacy_report_source = quality_source + "\n" + phase_source

    assert ".open(" not in legacy_report_source
    assert ".read_text(" not in legacy_report_source
    assert ".exists(" not in legacy_report_source


def test_metadata_text_sanitizes_formula_prefixes_and_does_not_expose_env(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_secret = "CR008_FAKE_TOKEN_SHOULD_NOT_APPEAR"
    monkeypatch.setenv("TUSHARE_TOKEN", fake_secret)
    payload = complete_payload()
    payload["known_limitations"] = ["=cmd", "+SUM(A1:A2)", "@risk", "token=SHOULD_BE_REDACTED"]

    section = render_research_input_metadata_section(payload)
    exported = metadata_to_dict(build_research_input_metadata(payload))

    assert "'=cmd" in section
    assert "'+SUM(A1:A2)" in section
    assert "'@risk" in section
    assert fake_secret not in section
    assert fake_secret not in str(exported)
    assert "SHOULD_BE_REDACTED" not in section


def test_experiment_14_report_contains_research_input_metadata_without_legacy_current_truth() -> None:
    args = Namespace(
        data_dir="tmp-fixture",
        quality_report="reports/data_quality_report.csv",
        phase_two_report="reports/experiment_13/backtest_report.md",
        forward_return_horizon=20,
        benchmark_kind="price_index",
    )
    summaries = [
        experiment_14.DatasetSummary(
            dataset="prices",
            status="available",
            rows=10,
            start_date="2020-01-01",
            end_date="2020-12-31",
            symbol_count=2,
            trade_day_count=10,
            notes="adjustment_policy=qfq",
        ),
        experiment_14.DatasetSummary(dataset="index_members", status="available", symbol_count=2),
        experiment_14.DatasetSummary(dataset="trade_calendar", status="available", trade_day_count=10),
    ]
    label_window = {
        "horizon": 20,
        "coverage_start": "2020-01-01",
        "coverage_end": "2020-12-31",
        "label_usable_end": "2020-12-01",
        "status": "available",
    }
    metadata = experiment_14.build_experiment_14_research_input_metadata(
        status="PASS",
        summaries=summaries,
        label_window=label_window,
        universe_summary={"status": "available", "is_pit_universe": False, "symbol_count": 2},
        benchmark_summary={"status": "proxy_or_unconfirmed", "benchmark_kind": "price_index", "message": "proxy only"},
        args=args,
    )
    report = experiment_14.render_report(
        status="PASS",
        summaries=summaries,
        quality_rows=[],
        label_window=label_window,
        universe_summary={"status": "available", "is_pit_universe": False, "symbol_count": 2},
        benchmark_summary={"status": "proxy_or_unconfirmed", "benchmark_kind": "price_index", "message": "proxy only"},
        report_checks={"path": str(args.phase_two_report), "status": LEGACY_REPORT_POLICY},
        issues=[],
        args=args,
        research_input_metadata=metadata,
    )

    assert "## Research Input Metadata" in report
    assert "research_input_v1" in report
    assert "legacy_only_not_current_truth" in report
    assert "not_coverage_proof" in report


def test_experiment_15_schema_and_report_metadata_allowed_claims_are_conservative() -> None:
    calendar = [date(2020, 1, 1) + timedelta(days=index) for index in range(35)]
    close_df = pd.DataFrame({"000001.SZ": [10.0 + index for index in range(35)]}, index=calendar)
    args = Namespace(data_dir="tmp-fixture", strategy_factor="momentum_20d")
    specs = experiment_15.parse_factor_specs(["momentum_20d"])

    schema = experiment_15.build_factor_schema(specs, args, close_df, ["000001.SZ"], calendar)
    metadata = schema["research_input_metadata"]
    report = experiment_15.render_report(
        args=args,
        schema=schema,
        coverages=[
            experiment_15.FactorCoverage(
                factor_name="momentum_20d",
                row_count=10,
                date_count=10,
                symbol_count=1,
                start_date="2020-01-21",
                end_date="2020-02-04",
                zscore_null_count=0,
            )
        ],
        backtest_summary={"status": "skipped", "strategy_factor": "momentum_20d", "signal_count": 0},
        paths={
            "panel": Path("tmp-fixture/factor_panel.parquet"),
            "preview": Path("tmp-fixture/factor_panel_preview.csv"),
            "schema": Path("tmp-fixture/factor_schema.json"),
            "summary": Path("tmp-fixture/factor_backtest_summary.csv"),
            "trades": Path("tmp-fixture/factor_strategy_trades.csv"),
            "equity": Path("tmp-fixture/factor_strategy_equity_curve.csv"),
        },
    )

    assert metadata["schema_name"] == RESEARCH_INPUT_SCHEMA_NAME
    assert metadata["benchmark_status"] == "proxy_only"
    assert metadata["universe_mode"] == "fixed_snapshot"
    assert metadata["label_available_end"] == "2020-01-15"
    forbidden_claims = {"industry_neutral", "size_neutral", "pure_alpha", "tradable_capacity"}
    assert forbidden_claims.isdisjoint(set(metadata["allowed_claims"]))
    assert "## Research Input Metadata" in report
    assert "industry, market cap, liquidity and style exposure data are unavailable" in report


def test_no_connector_runtime_storage_imports_or_credentials_in_target_files() -> None:
    forbidden_modules = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
    }
    forbidden_strings = {
        ".env",
        "TUSHARE_TOKEN",
        "NAS_PASSWORD",
        "NAS_TOKEN",
    }

    for path in TARGET_FILES:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(module == forbidden or module.startswith(forbidden + ".") for module in imported for forbidden in forbidden_modules)
        assert not any(token in source for token in forbidden_strings)


def _function_node(source: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function not found: {name}")
