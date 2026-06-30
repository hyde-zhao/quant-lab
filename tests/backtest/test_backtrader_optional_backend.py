from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import engine.backtrader_adapter as adapter
from engine.backtest import BacktestConfig, BacktestError, run_backtest, run_backtest_with_backend, select_backtest_backend
from engine.backtrader_adapter import BacktraderRequest, run_backtrader_backend


def _clean_ohlcv() -> pd.DataFrame:
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    return pd.DataFrame(
        {
            "trade_date": list(dates) * 2,
            "symbol": ["A", "A", "A", "B", "B", "B"],
            "open": [10.0, 10.5, 11.0, 20.0, 19.5, 20.5],
            "high": [10.5, 11.0, 11.5, 20.5, 20.0, 21.0],
            "low": [9.8, 10.2, 10.8, 19.8, 19.0, 20.0],
            "close": [10.0, 11.0, 12.0, 20.0, 19.0, 21.0],
            "adjustment_policy": ["qfq"] * 6,
        }
    )


def _request(**overrides) -> BacktraderRequest:
    values = {
        "ohlcv": _clean_ohlcv(),
        "calendar": ["2020-01-02", "2020-01-03", "2020-01-06"],
        "benchmark_result": {"status": "available", "dataset": "hs300_index"},
        "config": {"initial_cash": 1000.0, "benchmark_required": False},
        "input_contract": {
            "quality_status": "pass",
            "pit_checked": True,
            "pit_status": "pass",
            "adjusted_price_ready": True,
            "adjustment_policy": "qfq",
            "source_dataset": "reader-clean-feed",
        },
    }
    values.update(overrides)
    return BacktraderRequest(**values)


def _install_fake_backtrader(monkeypatch, *, version: str = adapter.BACKTRADER_VERSION, fail: bool = False) -> None:
    real_import_module = importlib.import_module

    class FakeBroker:
        def __init__(self) -> None:
            self.cash = None

        def setcash(self, cash: float) -> None:
            self.cash = cash

    class FakeCerebro:
        def __init__(self) -> None:
            if fail:
                raise RuntimeError("fake failure")
            self.broker = FakeBroker()

    fake_module = SimpleNamespace(__version__=version, Cerebro=FakeCerebro)

    def fake_import(name: str):
        if name == "backtrader":
            return fake_module
        return real_import_module(name)

    monkeypatch.setattr(adapter.importlib, "import_module", fake_import)


def test_default_lightweight_path_does_not_import_backtrader(monkeypatch):
    sys.modules.pop("backtrader", None)
    calls: list[str] = []
    real_import_module = importlib.import_module

    def spy_import(name: str, package: str | None = None):
        calls.append(name)
        if name == "backtrader":
            raise AssertionError("default lightweight path must not import backtrader")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", spy_import)
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=12)]
    close_df = pd.DataFrame({"A": range(10, 22), "B": range(20, 8, -1)}, index=idx)

    direct = run_backtest(close_df, BacktestConfig(lookback_days=3, rebalance_freq=3, top_fraction=0.5))
    wrapped = run_backtest_with_backend(close_df, BacktestConfig(lookback_days=3, rebalance_freq=3, top_fraction=0.5))

    assert direct.metrics == wrapped.metrics
    assert "backtrader" not in calls
    assert "backtrader" not in sys.modules


def test_dependency_missing_degrades_to_backend_unavailable(monkeypatch):
    real_import_module = importlib.import_module

    def missing_import(name: str):
        if name == "backtrader":
            raise ImportError("missing optional backend")
        return real_import_module(name)

    monkeypatch.setattr(adapter.importlib, "import_module", missing_import)

    result = run_backtrader_backend(_request())

    assert result.status == "backend_unavailable"
    assert result.reason_code == "dependency_missing"
    assert result.fallback_backend == "lightweight"
    assert result.network_calls == result.lake_writes == result.token_reads == 0


def test_selector_is_explicit_and_unknown_backend_fails():
    assert select_backtest_backend(None) == "lightweight"
    assert select_backtest_backend("backtrader") == "backtrader"
    with pytest.raises(BacktestError, match="unknown_backend"):
        select_backtest_backend("rqalpha")


def test_explicit_backtrader_wrapper_requires_clean_request():
    idx = [item.date() for item in pd.bdate_range("2020-01-01", periods=12)]
    close_df = pd.DataFrame({"A": range(10, 22), "B": range(20, 8, -1)}, index=idx)

    result = run_backtest_with_backend(close_df, backend="backtrader")

    assert result.status == "input_rejected"
    assert result.reason_code == "missing_backtrader_request"


def test_forbidden_imports_token_network_and_write_boundaries(tmp_path, monkeypatch):
    source_paths = [Path("engine/backtrader_adapter.py"), Path("engine/backtest.py")]
    forbidden_imports = {
        "market_data.connectors",
        "market_data.runtime",
        "market_data.storage",
        "requests",
        "urllib",
        "socket",
        "httpx",
        "aiohttp",
        "tushare",
    }
    for path in source_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not [name for name in imports if any(name == item or name.startswith(f"{item}.") for item in forbidden_imports)]

    adapter_source = Path("engine/backtrader_adapter.py").read_text(encoding="utf-8")
    assert "TUSHARE_TOKEN" not in adapter_source
    assert "os.environ" not in adapter_source
    assert "getenv" not in adapter_source

    monkeypatch.setenv("TUSHARE_TOKEN", "sentinel-secret")
    _install_fake_backtrader(monkeypatch)
    before = sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*"))
    result = run_backtrader_backend(_request())
    after = sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*"))

    assert result.status == "completed"
    assert before == after
    assert "sentinel-secret" not in str(result.to_metadata())


@pytest.mark.parametrize(
    ("contract_patch", "reason_code"),
    [
        ({"quality_status": "fail"}, "quality_failed"),
        ({"pit_checked": False}, "pit_failed"),
        ({"pit_status": "fail"}, "pit_failed"),
        ({"adjusted_price_ready": False}, "adjustment_failed"),
        ({"adj_factor_conflict": True}, "adjustment_failed"),
        ({"adjustment_policy": ["qfq", "hfq"]}, "adjustment_failed"),
    ],
)
def test_quality_pit_and_adjustment_failures_block_before_runtime(monkeypatch, contract_patch, reason_code):
    _install_fake_backtrader(monkeypatch, fail=True)
    contract = dict(_request().input_contract)
    contract.update(contract_patch)

    result = run_backtrader_backend(_request(input_contract=contract))

    assert result.status == "input_rejected"
    assert result.reason_code == reason_code
    assert result.metrics == {}


def test_available_at_after_decision_time_blocks_before_runtime(monkeypatch):
    _install_fake_backtrader(monkeypatch, fail=True)
    score = pd.DataFrame(
        {
            "symbol": ["A"],
            "score": [1.0],
            "available_at": ["2020-01-04"],
            "decision_time": ["2020-01-03"],
        }
    )

    result = run_backtrader_backend(_request(score=score))

    assert result.status == "input_rejected"
    assert result.reason_code == "pit_failed"


def test_missing_adjusted_ohlcv_columns_blocks_before_runtime(monkeypatch):
    _install_fake_backtrader(monkeypatch, fail=True)
    ohlcv = _clean_ohlcv().drop(columns=["open"])

    result = run_backtrader_backend(_request(ohlcv=ohlcv))

    assert result.status == "input_rejected"
    assert result.reason_code == "adjustment_failed"
    assert result.issues[-1]["code"] == "missing_adjusted_price"


def test_benchmark_required_missing_only_passes_metadata(monkeypatch):
    _install_fake_backtrader(monkeypatch, fail=True)
    benchmark = {
        "status": "required_missing",
        "missing_reason": "missing_dataset",
        "next_action": "run explicit hs300 backfill job",
        "remediation_job_spec": {"dataset": "hs300_index", "mode": "dry_run"},
        "proxy_baseline": {"name": "legacy_proxy"},
    }

    result = run_backtrader_backend(_request(benchmark_result=benchmark, config={"benchmark_required": True}))

    assert result.status == "benchmark_unavailable"
    assert result.reason_code == "benchmark_required_missing"
    assert result.benchmark_metadata["remediation_job_spec"]["dataset"] == "hs300_index"
    assert result.benchmark_metadata["proxy_baseline"]["name"] == "legacy_proxy"
    assert "hs300_relative_return" not in result.metrics
    assert result.network_calls == result.lake_writes == result.token_reads == 0


def test_fake_backtrader_smoke_completed_path(monkeypatch):
    _install_fake_backtrader(monkeypatch)

    result = run_backtrader_backend(_request())

    assert result.status == "completed"
    assert result.reason_code is None
    assert result.metrics["cerebro_type"] == "FakeCerebro"
    assert result.equity_curve is not None
    assert list(result.equity_curve.columns) == ["trade_date", "equity", "nav"]
    assert result.to_metadata()["equity_curve_rows"] == 3


def test_result_metadata_schema_is_stable(monkeypatch):
    _install_fake_backtrader(monkeypatch)

    metadata = run_backtrader_backend(_request()).to_metadata()

    expected = {
        "status",
        "backend",
        "fallback_backend",
        "reason_code",
        "message",
        "metrics",
        "benchmark_metadata",
        "issues",
        "input_contract",
        "network_calls",
        "lake_writes",
        "token_reads",
        "equity_curve_rows",
        "orders_rows",
        "positions_rows",
        "trades_rows",
    }
    assert expected <= set(metadata)
    assert metadata["network_calls"] == metadata["lake_writes"] == metadata["token_reads"] == 0
