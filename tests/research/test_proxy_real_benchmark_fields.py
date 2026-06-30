from __future__ import annotations

import ast
from datetime import date
import json
from pathlib import Path
from typing import Any

import pandas as pd

from experiments.run_strategy_comparison_exp13 import build_comparison_table, proxy_metrics_from_equal_weight
from experiments.run_factor_framework_exp15 import run_factor_backtest
from market_data.benchmarks import BenchmarkCoverage, BenchmarkResult, build_benchmark_field_payload
from market_data.contracts import DATASET_HS300_INDEX, INTERFACE_HS300_INDEX_DAILY, SOURCE_TUSHARE


TARGET_FILES = (
    Path("market_data/benchmarks.py"),
    Path("experiments/run_strategy_comparison_exp13.py"),
    Path("experiments/run_factor_framework_exp15.py"),
)

AMBIGUOUS_TOP_LEVEL_FIELDS = {
    "benchmark_total_return",
    "benchmark_annual_return",
    "benchmark_excess_return",
    "benchmark_excess_annual_return",
    "excess_return",
    "excess_annual_return",
}


def test_real_available_payload_uses_hs300_fields_and_preserves_metadata() -> None:
    result = make_benchmark_result("available")

    payload = build_benchmark_field_payload(
        result,
        proxy_metrics={"benchmark_annual_return": 0.20, "excess_return": 0.12},
        hs300_metrics={"total_return": 0.11, "annual_return": 0.08, "excess_return": 0.03},
    )

    assert payload["benchmark_status"] == "available"
    assert payload["benchmark_kind"] == "hs300"
    assert payload["benchmark_missing_reason"] is None
    assert payload["hs300_total_return"] == 0.11
    assert payload["hs300_annual_return"] == 0.08
    assert payload["hs300_excess_return"] == 0.03
    assert "hs300_index" in payload
    assert "proxy_annual_return" not in payload
    assert payload["benchmark_result"]["coverage"]["denominator_mode"] == "trade_calendar_open_dates"
    assert payload["benchmark_result"]["lineage"]["lineage_raw_checksum"] == "checksum-hs300"
    assert not (AMBIGUOUS_TOP_LEVEL_FIELDS & payload.keys())


def test_proxy_only_payload_never_populates_hs300_or_ambiguous_fields(monkeypatch) -> None:
    monkeypatch.setenv("TUSHARE_TOKEN", "secret-token-value")

    payload = build_benchmark_field_payload(
        None,
        proxy_metrics={
            "benchmark_total_return": 0.18,
            "benchmark_annual_return": 0.12,
            "excess_return": 0.04,
            "excess_annual_return": 0.03,
        },
    )

    assert payload["benchmark_status"] == "proxy_only"
    assert payload["benchmark_kind"] == "proxy_baseline"
    assert payload["benchmark_missing_reason"] == "not_requested"
    assert payload["proxy_total_return"] == 0.18
    assert payload["proxy_annual_return"] == 0.12
    assert payload["proxy_excess_return"] == 0.04
    assert payload["proxy_excess_annual_return"] == 0.03
    assert payload["proxy_baseline"]["kind"] == "same_universe_equal_weight_buy_and_hold"
    assert_no_top_level_hs300(payload)
    assert not (AMBIGUOUS_TOP_LEVEL_FIELDS & payload.keys())
    assert "secret-token-value" not in json.dumps(payload, ensure_ascii=False, default=str)


def test_required_missing_payload_preserves_missing_reason_and_ignores_hs300_metrics() -> None:
    result = make_benchmark_result("required_missing", missing_reason="coverage_gap")

    payload = build_benchmark_field_payload(
        result,
        proxy_metrics={"annual_return": 0.05},
        hs300_metrics={"total_return": 0.09, "annual_return": 0.07},
    )

    assert payload["benchmark_status"] == "required_missing"
    assert payload["benchmark_kind"] == "proxy_baseline"
    assert payload["benchmark_missing_reason"] == "coverage_gap"
    assert payload["proxy_annual_return"] == 0.05
    assert payload["benchmark_result"]["status"] == "required_missing"
    assert payload["benchmark_result"]["missing_reason"] == "coverage_gap"
    assert payload["benchmark_result"]["coverage"]["missing_trade_dates"] == ["2026-01-05"]
    assert payload["benchmark_result"]["quality_status"] == "missing"
    assert payload["benchmark_result"]["lineage"]["status"] == "lineage_unavailable"
    assert_no_top_level_hs300(payload)


def test_experiment_13_comparison_uses_proxy_baseline_field_names() -> None:
    rows = make_strategy_rows()
    comparison = build_comparison_table(
        {"annual_return": 0.03, "total_return": 0.04, "sharpe": 0.8, "max_drawdown": -0.1},
        rows,
        {"momentum": 0.01, "rsi": 0.02, "macd": 0.03},
    )
    payload = build_benchmark_field_payload(
        None,
        proxy_metrics=proxy_metrics_from_equal_weight({"annual_return": 0.03, "total_return": 0.04}),
    )

    assert comparison[0]["proxy_baseline"] == 0.03
    assert comparison[1]["对比维度"] == "proxy_excess_annual_return"
    assert "基准代理（同股票池等权）" not in comparison[0]
    assert payload["proxy_annual_return"] == 0.03
    assert_no_top_level_hs300(payload)
    assert not any(AMBIGUOUS_TOP_LEVEL_FIELDS & row.keys() for row in comparison)


def test_experiment_15_summary_uses_proxy_fields_not_benchmark_or_hs300() -> None:
    close_df = make_close_frame()
    factor_panel = make_factor_panel(close_df)

    result = run_factor_backtest(
        close_df,
        factor_panel,
        strategy_factor="momentum_5d",
        rebalance_freq=5,
        top_fraction=0.5,
        initial_cash=100_000.0,
    )
    summary = result["summary"]

    assert summary["status"] == "success"
    assert summary["benchmark_status"] == "proxy_only"
    assert summary["benchmark_kind"] == "proxy_baseline"
    assert summary["benchmark_missing_reason"] == "not_requested"
    assert "proxy_baseline" in summary
    assert "proxy_annual_return" in summary
    assert "proxy_excess_annual_return" in summary
    assert "benchmark_annual_return" not in summary
    assert "excess_annual_return" not in summary
    assert_no_top_level_hs300(summary)


def test_target_files_do_not_import_forbidden_runtime_or_network_modules() -> None:
    forbidden_exact = {
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
    }
    for source_path in TARGET_FILES:
        imports = imports_for(source_path)
        assert not any(name.startswith("market_data.connectors") for name in imports), source_path
        assert not any(name in forbidden_exact for name in imports), source_path


def test_no_old_data_report_or_credentials_operations_are_present() -> None:
    for source_path in TARGET_FILES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        assert not _calls_env_or_credentials(tree), source_path
        assert not _has_forbidden_old_path_io_call(tree), source_path
        assert not _has_destructive_file_call(tree), source_path


def make_benchmark_result(status: str, missing_reason: str | None = None) -> BenchmarkResult:
    available = status == "available"
    reason = None if available else missing_reason or "coverage_gap"
    coverage = BenchmarkCoverage(
        numerator=2 if available else 1,
        denominator=2,
        ratio=1.0 if available else 0.5,
        missing_trade_dates=[] if available else ["2026-01-05"],
        gap_reason=None if available else reason,
        denominator_mode="trade_calendar_open_dates",
        price_trade_dates_count=2,
        price_overlap_count=2 if available else 1,
    )
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
        coverage=coverage,
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


def make_strategy_rows() -> list[dict[str, Any]]:
    return [
        {
            "strategy_name": "momentum",
            "annual_return_no_cost": 0.10,
            "annual_return_with_cost": 0.08,
            "sharpe": 1.1,
            "max_drawdown": -0.12,
            "win_rate": 0.55,
            "profit_loss_ratio": 1.2,
            "monthly_trade_count": 2.0,
            "cost_erosion": 0.2,
        },
        {
            "strategy_name": "rsi",
            "annual_return_no_cost": 0.07,
            "annual_return_with_cost": 0.06,
            "sharpe": 0.9,
            "max_drawdown": -0.08,
            "win_rate": 0.51,
            "profit_loss_ratio": 1.1,
            "monthly_trade_count": 1.0,
            "cost_erosion": 0.1,
        },
        {
            "strategy_name": "macd",
            "annual_return_no_cost": 0.05,
            "annual_return_with_cost": 0.04,
            "sharpe": 0.7,
            "max_drawdown": -0.10,
            "win_rate": 0.49,
            "profit_loss_ratio": 1.0,
            "monthly_trade_count": 1.5,
            "cost_erosion": 0.2,
        },
    ]


def make_close_frame() -> pd.DataFrame:
    dates = [item.date() for item in pd.bdate_range("2026-01-02", periods=35)]
    return pd.DataFrame(
        {
            "AAA": [10.0 + index * 0.10 for index in range(len(dates))],
            "BBB": [12.0 + index * 0.05 for index in range(len(dates))],
            "CCC": [8.0 + index * 0.08 for index in range(len(dates))],
        },
        index=dates,
    )


def make_factor_panel(close_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, trade_date in enumerate(close_df.index[:-1]):
        for symbol_index, symbol in enumerate(close_df.columns):
            rows.append(
                {
                    "date": trade_date.isoformat() if isinstance(trade_date, date) else str(trade_date),
                    "symbol": symbol,
                    "factor_name": "momentum_5d",
                    "factor_zscore": float(symbol_index - 1 + index / 100.0),
                }
            )
    return pd.DataFrame(rows)


def imports_for(source_path: Path) -> list[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def assert_no_top_level_hs300(payload: dict[str, Any]) -> None:
    assert "hs300_index" not in payload
    assert not any(key.startswith("hs300_") for key in payload)


def _calls_env_or_credentials(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"getenv", "environ"}:
                return True
        if isinstance(node, ast.ImportFrom) and node.module and "dotenv" in node.module:
            return True
    return False


def _has_forbidden_old_path_io_call(tree: ast.AST) -> bool:
    forbidden = {"reports/data_quality_report.csv", "data"}
    io_calls = {"open", "read_text", "read_bytes", "read_csv", "read_parquet"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = _call_name(node.func)
        if func_name not in io_calls:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and str(arg.value) in forbidden:
                return True
    return False


def _has_destructive_file_call(tree: ast.AST) -> bool:
    destructive = {"unlink", "rmdir", "remove", "rmtree"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in destructive:
            return True
    return False


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""
