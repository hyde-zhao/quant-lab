from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import engine.backtrader_adapter as adapter
import market_data.readers as readers
from engine.backtest import run_backtest_with_backend
from engine.backtrader_adapter import (
    BacktraderRequest,
    build_backtrader_request_from_clean_feed,
    run_backtrader_clean_feed,
    validate_backtrader_clean_feed,
)
from market_data.contracts import DATASET_PRICES
from market_data.readers import (
    BacktraderCleanFeedBundle,
    BacktraderCleanFeedRequest,
    ReaderResult,
    read_backtrader_clean_feed,
)


def _canonical_prices() -> pd.DataFrame:
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    return pd.DataFrame(
        {
            "trade_date": list(dates) * 2,
            "symbol": ["A", "A", "A", "B", "B", "B"],
            "open": [9.8, 10.3, 10.8, 19.8, 19.3, 20.3],
            "high": [10.8, 11.3, 11.8, 20.8, 20.3, 21.3],
            "low": [9.6, 10.1, 10.6, 19.6, 19.1, 20.1],
            "close": [10.0, 11.0, 12.0, 20.0, 19.0, 21.0],
            "adjusted_open": [10.0, 10.5, 11.0, 20.0, 19.5, 20.5],
            "adjusted_high": [10.5, 11.0, 11.5, 20.5, 20.0, 21.0],
            "adjusted_low": [9.8, 10.2, 10.8, 19.8, 19.0, 20.0],
            "adjusted_close": [10.2, 11.2, 12.2, 20.2, 19.2, 21.2],
            "volume": [100, 110, 120, 200, 190, 210],
            "available_at": list(dates) * 2,
            "decision_time": list(dates) * 2,
            "adjustment_policy": ["qfq"] * 6,
            "source_run_id": ["run-clean"] * 6,
            "lineage_raw_checksum": ["checksum-clean"] * 6,
            "schema_version": ["v1"] * 6,
            "source": ["fixture"] * 6,
            "source_interface": ["unit-test"] * 6,
        }
    )


def _install_fake_backtrader(monkeypatch, *, version: str = adapter.BACKTRADER_VERSION, fail: bool = False) -> None:
    real_import_module = importlib.import_module

    class FakeBroker:
        def setcash(self, cash: float) -> None:
            self.cash = cash

    class FakeCerebro:
        def __init__(self) -> None:
            if fail:
                raise RuntimeError("runtime should not be reached")
            self.broker = FakeBroker()

    fake_module = SimpleNamespace(__version__=version, Cerebro=FakeCerebro)

    def fake_import(name: str):
        if name == "backtrader":
            return fake_module
        return real_import_module(name)

    monkeypatch.setattr(adapter.importlib, "import_module", fake_import)


def test_read_backtrader_clean_feed_returns_in_memory_bundle(monkeypatch, tmp_path):
    calls: list[dict[str, object]] = []

    def fake_read_dataset(dataset, lake_root, filters=None, quality_policy=None, required=False):
        calls.append({"dataset": dataset, "lake_root": lake_root, "filters": filters, "required": required})
        return ReaderResult(status="available", frame=_canonical_prices())

    monkeypatch.setattr(readers, "read_dataset", fake_read_dataset)

    bundle = read_backtrader_clean_feed(
        BacktraderCleanFeedRequest(
            lake_root=tmp_path,
            start_date="2020-01-02",
            end_date="2020-01-06",
            symbols=("A",),
            benchmark_result={"status": "available"},
        )
    )

    assert bundle.status == "available"
    assert bundle.ohlcv is not None
    assert list(bundle.ohlcv.columns[:6]) == ["trade_date", "symbol", "open", "high", "low", "close"]
    assert bundle.ohlcv.loc[0, "open"] == 10.0
    assert bundle.input_contract["quality_status"] == "pass"
    assert bundle.input_contract["pit_checked"] is True
    assert bundle.input_contract["adjusted_price_ready"] is True
    assert bundle.lineage["source_run_id"] == "run-clean"
    assert calls == [
        {
            "dataset": DATASET_PRICES,
            "lake_root": tmp_path,
            "filters": {"start_date": "2020-01-02", "end_date": "2020-01-06", "symbols": ("A",)},
            "required": True,
        }
    ]
    assert validate_backtrader_clean_feed(bundle) is None


def test_clean_feed_can_run_through_explicit_backtrader_wrapper(monkeypatch):
    _install_fake_backtrader(monkeypatch)
    bundle = BacktraderCleanFeedBundle(
        status="available",
        ohlcv=_canonical_prices().rename(
            columns={
                "adjusted_open": "bt_open",
                "adjusted_high": "bt_high",
                "adjusted_low": "bt_low",
                "adjusted_close": "bt_close",
            }
        )[["trade_date", "symbol", "open", "high", "low", "close", "adjustment_policy"]],
        calendar=["2020-01-02", "2020-01-03", "2020-01-06"],
        benchmark_result={"status": "available"},
        input_contract={
            "quality_status": "pass",
            "pit_checked": True,
            "pit_status": "pass",
            "adjusted_price_ready": True,
            "adjustment_policy": "qfq",
        },
    )

    direct = run_backtrader_clean_feed(bundle, config={"initial_cash": 1000.0})
    wrapped = run_backtest_with_backend(pd.DataFrame(), backend="backtrader", backtrader_clean_feed=bundle)

    assert direct.status == "completed"
    assert wrapped.status == "completed"
    assert direct.network_calls == direct.lake_writes == direct.token_reads == 0


def test_reader_without_explicit_lake_root_does_not_read_env_or_dataset(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_LAKE_ROOT", "sentinel-secret")
    monkeypatch.setattr(readers.os, "getenv", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("env must not be read")))
    monkeypatch.setattr(readers, "read_dataset", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("dataset must not be read")))

    bundle = read_backtrader_clean_feed(BacktraderCleanFeedRequest())

    assert bundle.status == "required_missing"
    assert bundle.issues == [{"code": "lake_root_required", "dataset": DATASET_PRICES}]
    assert "sentinel-secret" not in str(bundle)


def test_quality_failure_rejects_before_backtrader_runtime(monkeypatch, tmp_path):
    def fake_read_dataset(*_args, **_kwargs):
        return ReaderResult(status="quality_failed", issues=[{"code": "quality_failed", "dataset": DATASET_PRICES}])

    monkeypatch.setattr(readers, "read_dataset", fake_read_dataset)
    monkeypatch.setattr(adapter.importlib, "import_module", lambda name: (_ for _ in ()).throw(AssertionError(f"{name} must not be imported")))

    bundle = read_backtrader_clean_feed(BacktraderCleanFeedRequest(lake_root=tmp_path))
    result = run_backtrader_clean_feed(bundle)

    assert bundle.status == "quality_failed"
    assert result.status == "input_rejected"
    assert result.reason_code == "quality_failed"
    assert result.metrics == {}


def test_forbidden_runtime_raw_manifest_or_storage_inputs_are_rejected():
    clean = _canonical_prices()[["trade_date", "symbol", "open", "high", "low", "close", "adjustment_policy"]]
    request = BacktraderRequest(
        ohlcv=clean,
        input_contract={
            "quality_status": "pass",
            "pit_checked": True,
            "pit_status": "pass",
            "adjusted_price_ready": True,
            "adjustment_policy": "qfq",
            "raw_path": "data/raw/prices.parquet",
        },
    )
    rejected = adapter.validate_backtrader_inputs(request)

    assert rejected is not None
    assert rejected.status == "input_rejected"
    assert rejected.reason_code == "forbidden_runtime_input"
    assert "input_contract.raw_path" in rejected.issues[-1]["field"]


def test_adapter_builds_request_without_lake_io_or_dependency_probe(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", lambda name: (_ for _ in ()).throw(AssertionError(f"{name} must not be imported")))
    clean = _canonical_prices()[["trade_date", "symbol", "open", "high", "low", "close", "adjustment_policy"]]
    bundle = BacktraderCleanFeedBundle(
        status="available",
        ohlcv=clean,
        input_contract={
            "quality_status": "pass",
            "pit_checked": True,
            "pit_status": "pass",
            "adjusted_price_ready": True,
            "adjustment_policy": "qfq",
        },
    )

    request = build_backtrader_request_from_clean_feed(bundle)

    assert request.ohlcv.equals(clean)
    assert validate_backtrader_clean_feed(bundle) is None


def test_s03_no_fetch_connector_runtime_storage_imports_and_no_writes(monkeypatch, tmp_path):
    source_paths = [Path("engine/backtrader_adapter.py"), Path("engine/backtest.py"), Path("market_data/readers.py")]
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

    def fake_read_dataset(*_args, **_kwargs):
        return ReaderResult(status="available", frame=_canonical_prices())

    monkeypatch.setattr(readers, "read_dataset", fake_read_dataset)
    before = sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*"))
    bundle = read_backtrader_clean_feed(BacktraderCleanFeedRequest(lake_root=tmp_path))
    after = sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*"))

    assert bundle.status == "available"
    assert before == after
