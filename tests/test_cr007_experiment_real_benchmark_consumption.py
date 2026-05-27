from __future__ import annotations

import ast
from datetime import date
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

import experiments.run_experiment_13 as experiment_13
from experiments.run_experiment_10 import apply_benchmark_metadata_experiment_10
from experiments.run_experiment_12 import apply_benchmark_metadata_experiment_12
from market_data.benchmarks import BenchmarkCoverage, BenchmarkResult


TARGET_FILES = (
    Path("experiments/run_experiment_13.py"),
    Path("experiments/run_experiment_10.py"),
    Path("experiments/run_experiment_12.py"),
    Path("market_data/benchmarks.py"),
)


def test_real_available_uses_hs300_metrics_equity_and_metadata() -> None:
    close_df = make_close_frame()
    result = make_benchmark_result("available", close_df.index)

    payload = experiment_13.build_experiment_13_benchmark(
        close_df,
        100_000.0,
        result,
        require_benchmark=False,
    )
    field_payload = payload["field_payload"]

    assert payload["benchmark"]["name"] == "hs300_index"
    assert payload["comparison_column"] == "hs300_index"
    assert payload["equity_filename"] == "hs300_benchmark_equity_curve.csv"
    assert field_payload["benchmark_status"] == "available"
    assert field_payload["benchmark_kind"] == "hs300"
    assert field_payload["hs300_index"]["dataset"] == "hs300_index"
    assert len(field_payload["hs300_index"]) >= 8
    assert field_payload["hs300_total_return"] == pytest.approx(0.03)
    assert "proxy_baseline" not in field_payload
    assert not any(key.startswith("proxy_") for key in field_payload)
    assert payload["benchmark"]["equity"]["total_value"].iloc[-1] == pytest.approx(103_000.0)

    metadata = experiment_13.apply_benchmark_metadata_experiment_13(
        result,
        {"initial_cash": 100_000.0},
        field_payload=field_payload,
    )
    assert metadata["benchmark_dataset"] == "hs300_index"
    assert metadata["hs300_relative_return_enabled"] is True
    assert "hs300_index" in metadata


def test_main_writes_real_hs300_outputs_without_proxy_file(tmp_path, monkeypatch) -> None:
    close_df = make_close_frame()
    result = make_benchmark_result("available", close_df.index)
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        experiment_13,
        "load_experiment_backtest_data",
        lambda _args, _start, _end: (SimpleNamespace(close_df=close_df, metadata={}), "2026-01-02", "2026-01-07"),
    )
    monkeypatch.setattr(experiment_13, "resolve_benchmark_for_experiment_13", lambda **_kwargs: result)
    monkeypatch.setattr(experiment_13, "run_strategy_comparisons", lambda *_args: fake_strategy_results())
    monkeypatch.setattr(experiment_13, "load_decay_by_strategy", lambda _path: {"momentum": 0.01, "rsi": 0.02, "macd": 0.03})
    monkeypatch.setattr(experiment_13, "load_market_segment_rows", lambda _path: [])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_experiment_13.py",
            "--output-dir",
            str(output_dir),
            "--market-data-lake-root",
            str(tmp_path / "lake"),
            "--benchmark-kind",
            "price_index",
        ],
    )

    experiment_13.main()

    metadata = json.loads((output_dir / "benchmark_metadata.json").read_text(encoding="utf-8"))
    comparison = (output_dir / "cross_strategy_comparison.csv").read_text(encoding="utf-8")
    report = (output_dir / "backtest_report.md").read_text(encoding="utf-8")

    assert (output_dir / "hs300_benchmark_equity_curve.csv").exists()
    assert not (output_dir / "benchmark_proxy_equity_curve.csv").exists()
    assert metadata["benchmark_status"] == "available"
    assert "hs300_index" in metadata
    assert "proxy_baseline" not in metadata
    assert "hs300_index" in comparison
    assert "proxy_baseline" not in comparison
    assert "已使用真实 `hs300_index` benchmark" in report


def test_required_missing_fails_fast_with_status_and_reason() -> None:
    close_df = make_close_frame()
    missing = make_benchmark_result("required_missing", close_df.index, missing_reason="coverage_gap")

    with pytest.raises(experiment_13.BenchmarkUnavailableError) as exc_info:
        experiment_13.build_experiment_13_benchmark(
            close_df,
            100_000.0,
            missing,
            require_benchmark=True,
        )

    message = str(exc_info.value)
    assert "status=required_missing" in message
    assert "missing_reason=coverage_gap" in message


def test_required_without_lake_root_returns_typed_missing_without_resolver(monkeypatch) -> None:
    monkeypatch.setattr(
        experiment_13,
        "resolve_hs300_benchmark",
        lambda **_kwargs: pytest.fail("no-lake required path must not call resolver"),
    )

    result = experiment_13.resolve_benchmark_for_experiment_13(
        lake_root=None,
        start_date="2026-01-02",
        end_date="2026-01-07",
        benchmark_kind="price_index",
        required=True,
    )

    assert result is not None
    assert result.status == "required_missing"
    assert result.missing_reason == "lake_root_missing"


def test_optional_missing_uses_proxy_baseline_without_hs300_fields() -> None:
    close_df = make_close_frame()
    missing = make_benchmark_result("unavailable", close_df.index, missing_reason="policy_unconfirmed")

    payload = experiment_13.build_experiment_13_benchmark(
        close_df,
        100_000.0,
        missing,
        require_benchmark=False,
    )
    field_payload = payload["field_payload"]

    assert payload["benchmark"]["name"] == "proxy_baseline"
    assert payload["comparison_column"] == "proxy_baseline"
    assert payload["equity_filename"] == "benchmark_proxy_equity_curve.csv"
    assert field_payload["benchmark_status"] == "unavailable"
    assert field_payload["benchmark_kind"] == "proxy_baseline"
    assert field_payload["benchmark_missing_reason"] == "policy_unconfirmed"
    assert field_payload["proxy_baseline"]["status"] == "used"
    assert_no_hs300_fields(field_payload)

    comparison = experiment_13.build_comparison_table(
        payload["benchmark"]["metrics"],
        fake_strategy_results()[0],
        {"momentum": 0.01, "rsi": 0.02, "macd": 0.03},
    )
    assert comparison[0]["proxy_baseline"] == payload["benchmark"]["metrics"]["annual_return"]
    assert comparison[1]["对比维度"] == "proxy_excess_annual_return"
    assert not any("hs300_index" in row for row in comparison)


def test_experiment_10_and_12_missing_metadata_semantics_match_s04() -> None:
    close_df = make_close_frame()
    available = make_benchmark_result("available", close_df.index)
    missing = make_benchmark_result("unavailable", close_df.index, missing_reason="price_benchmark_overlap_missing")

    exp10_available = apply_benchmark_metadata_experiment_10(available, {})
    exp10_missing = apply_benchmark_metadata_experiment_10(missing, {})
    exp12_missing = apply_benchmark_metadata_experiment_12(missing, {"proxy_baseline": {"name": "legacy_proxy"}})

    assert exp10_available["benchmark_dataset"] == "hs300_index"
    assert exp10_available["benchmark_kind"] == "hs300"
    assert exp10_available["benchmark_relative_return_enabled"] is True
    assert exp10_available["hs300_index"]["status"] == "available"

    for metadata in (exp10_missing, exp12_missing):
        assert metadata["benchmark_dataset"] == "proxy_baseline"
        assert metadata["benchmark_kind"] == "proxy_baseline"
        assert metadata["benchmark_status"] == "unavailable"
        assert metadata["benchmark_missing_reason"] == "price_benchmark_overlap_missing"
        assert "hs300_index" not in metadata
    assert exp10_missing["benchmark_relative_return_enabled"] is False
    assert exp12_missing["hs300_relative_return_enabled"] is False
    assert exp12_missing["proxy_baseline"] == {"name": "legacy_proxy"}


def test_static_boundaries_no_forbidden_imports_credentials_old_data_report_or_jobs() -> None:
    for source_path in TARGET_FILES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imports = _imports_for(tree)
        assert not any(name.startswith("market_data.connectors") for name in imports), source_path
        assert not any(name in FORBIDDEN_IMPORTS for name in imports), source_path
        assert not _calls_env_or_credentials(tree), source_path
        assert not _has_forbidden_old_path_io_call(tree), source_path
        assert not _has_destructive_file_call(tree), source_path
        assert not _has_data_job_call(tree), source_path


def make_close_frame() -> pd.DataFrame:
    dates = [item.date() for item in pd.bdate_range("2026-01-02", periods=4)]
    return pd.DataFrame(
        {
            "sz000001": [10.0, 10.2, 10.4, 10.6],
            "sh600519": [20.0, 19.8, 20.1, 20.5],
            "sz000858": [12.0, 12.2, 12.4, 12.6],
            "sh600276": [30.0, 30.5, 30.8, 31.0],
            "sz000725": [5.0, 5.1, 5.2, 5.3],
        },
        index=dates,
    )


def make_benchmark_result(
    status: str,
    price_index: pd.Index,
    *,
    missing_reason: str | None = None,
) -> BenchmarkResult:
    available = status == "available"
    dates = [str(item) for item in price_index]
    reason = None if available else missing_reason or "coverage_gap"
    frame = pd.DataFrame(
        {
            "trade_date": dates,
            "close": [4000.0, 4040.0, 4080.0, 4120.0],
            "benchmark_kind": ["price_index"] * len(dates),
            "source": ["tushare"] * len(dates),
            "source_run_id": ["run-hs300"] * len(dates),
            "lineage_raw_checksum": ["checksum-hs300"] * len(dates),
        }
    )
    coverage = BenchmarkCoverage(
        numerator=len(dates) if available else len(dates) - 1,
        denominator=len(dates),
        ratio=1.0 if available else 0.75,
        missing_trade_dates=[] if available else [dates[-1]],
        gap_reason=None if available else reason,
        denominator_mode="trade_calendar_open_dates",
        price_trade_dates_count=len(dates),
        price_overlap_count=len(dates) if available else len(dates) - 1,
    )
    return BenchmarkResult(
        status=status,
        dataset="hs300_index",
        source="tushare" if available else "none",
        index_code="399300.SZ",
        interface="hs300_index.daily",
        start_date=dates[0],
        end_date=dates[-1],
        available_start_date=dates[0] if available else None,
        available_end_date=dates[-1] if available else None,
        coverage=coverage,
        quality_status="pass" if available else "missing",
        missing_reason=reason,
        required=status == "required_missing",
        benchmark_kind="price_index",
        next_action=None,
        remediation_job_spec=None,
        catalog_entry=None,
        run_id="run-hs300" if available else None,
        lineage={"lineage_raw_checksum": "checksum-hs300"} if available else {"status": "lineage_unavailable"},
        frame=frame if available else None,
    )


def fake_strategy_results() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cost_result = SimpleNamespace(portfolio_result=SimpleNamespace(trades=[]))
    rows = [
        {
            "strategy_name": "momentum",
            "annual_return_no_cost": 0.12,
            "annual_return_with_cost": 0.10,
            "sharpe": 1.2,
            "max_drawdown": -0.10,
            "win_rate": 0.55,
            "profit_loss_ratio": 1.4,
            "monthly_trade_count": 2.0,
            "cost_erosion": 0.16,
            "cost_result": cost_result,
        },
        {
            "strategy_name": "rsi",
            "annual_return_no_cost": 0.08,
            "annual_return_with_cost": 0.07,
            "sharpe": 1.0,
            "max_drawdown": -0.08,
            "win_rate": 0.51,
            "profit_loss_ratio": 1.1,
            "monthly_trade_count": 1.5,
            "cost_erosion": 0.12,
            "cost_result": cost_result,
        },
        {
            "strategy_name": "macd",
            "annual_return_no_cost": 0.06,
            "annual_return_with_cost": 0.05,
            "sharpe": 0.8,
            "max_drawdown": -0.09,
            "win_rate": 0.49,
            "profit_loss_ratio": 1.0,
            "monthly_trade_count": 1.0,
            "cost_erosion": 0.10,
            "cost_result": cost_result,
        },
    ]
    diagnostics = [
        {
            "strategy_name": row["strategy_name"],
            "annual_return_no_cost": row["annual_return_no_cost"],
            "annual_return_with_cost": row["annual_return_with_cost"],
            "sharpe": row["sharpe"],
            "max_drawdown": row["max_drawdown"],
            "win_rate": row["win_rate"],
            "profit_loss_ratio": row["profit_loss_ratio"],
            "monthly_trade_count": row["monthly_trade_count"],
            "filled_trade_count": 0,
            "turnover": 0.0,
            "cost_erosion": row["cost_erosion"],
        }
        for row in rows
    ]
    return rows, diagnostics


FORBIDDEN_IMPORTS = {
    "market_data.runtime",
    "market_data.storage",
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
    "socket",
    "subprocess",
}


def assert_no_hs300_fields(payload: dict[str, Any]) -> None:
    assert "hs300_index" not in payload
    assert not any(key.startswith("hs300_") for key in payload)


def _imports_for(tree: ast.AST) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _calls_env_or_credentials(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in {"getenv", "environ", "load_dotenv"}:
            return True
        if isinstance(node, ast.ImportFrom) and node.module and "dotenv" in node.module:
            return True
    return False


def _has_forbidden_old_path_io_call(tree: ast.AST) -> bool:
    io_calls = {"open", "read_text", "read_bytes", "read_csv", "read_parquet"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node.func) not in io_calls:
            continue
        if any(_literal_contains_forbidden_path(arg) for arg in node.args):
            return True
    return False


def _literal_contains_forbidden_path(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    return node.value == "data" or node.value == "reports/data_quality_report.csv"


def _has_destructive_file_call(tree: ast.AST) -> bool:
    destructive = {"unlink", "rmdir", "remove", "rmtree", "system"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in destructive:
            return True
    return False


def _has_data_job_call(tree: ast.AST) -> bool:
    data_jobs = {"fetch", "backfill", "replay", "normalize", "revalidate", "run_data_layer", "run_backfill"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in data_jobs:
            return True
    return False


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
