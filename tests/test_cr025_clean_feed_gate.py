from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pandas as pd

import engine.backtrader_adapter as adapter
from engine.backtest import run_backtest_with_backend
from engine.backtrader_adapter import BackendSelectionRequest, select_research_backend, validate_clean_feed_gate


def _clean_evidence(**overrides):
    evidence = {
        "pit_checked": True,
        "pit_status": "pass",
        "available_at_checked": True,
        "adjusted_price_ready": True,
        "adjustment_policy": "qfq",
        "ohlcv_status": "available",
        "calendar_status": "available",
        "benchmark_status": "available",
        "benchmark_required": True,
        "tradability_status": "available",
        "cost_status": "available",
        "quality_status": "pass",
        "lineage": {"source_run_id": "run-clean", "dataset": "clean-feed-fixture"},
        "limitations": [{"code": "fixture_only"}],
    }
    evidence.update(overrides)
    return evidence


def _no_import(_name: str, _package: str | None = None):
    raise AssertionError("Backtrader import must not be attempted")


def test_default_lightweight_selector_does_not_import_backtrader(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)

    result = select_research_backend()

    assert result.selected_backend == "lightweight"
    assert result.availability_status == "available"
    assert result.import_attempted is False
    assert result.blocked_reasons == ()
    assert set(result.forbidden_operation_counts) == set(adapter.FORBIDDEN_OPERATION_COUNTERS)
    assert all(value == 0 for value in result.forbidden_operation_counts.values())


def test_clean_feed_pit_or_available_at_failure_blocks_before_import(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)
    request = BackendSelectionRequest(
        backend="backtrader",
        clean_feed_evidence=_clean_evidence(available_at_checked=False),
        feature_flags={"backtrader_runtime_authorized": True, "allow_backtrader_import": True},
    )

    result = select_research_backend(request)

    assert result.selected_backend == "none"
    assert result.availability_status == "blocked_clean_feed_pit"
    assert "blocked_clean_feed_pit:available_at_not_confirmed" in result.blocked_reasons
    assert result.import_attempted is False
    assert result.unavailable is not None


def test_adjustment_policy_mixed_blocks_before_import(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)
    request = BackendSelectionRequest(
        backend="backtrader",
        clean_feed_evidence=_clean_evidence(adjustment_policy=["qfq", "raw"]),
        feature_flags={"backtrader_runtime_authorized": True, "allow_backtrader_import": True},
    )

    result = select_research_backend(request)

    assert result.availability_status == "blocked_adjustment_policy_mixed"
    assert "blocked_adjustment_policy_mixed:adjustment_policy_not_single_clean_view" in result.blocked_reasons
    assert result.import_attempted is False


def test_missing_required_evidence_is_structured_unavailable():
    evidence = _clean_evidence()
    evidence.pop("benchmark_status")

    gate = validate_clean_feed_gate(evidence)

    assert gate.passed is False
    assert gate.availability_status == "data_required_missing"
    assert "data_required_missing:benchmark_status" in gate.blocked_reasons
    assert gate.unavailable is not None
    assert all(value == 0 for value in gate.forbidden_operation_counts.values())


def test_quality_failure_is_structured_and_keeps_safety_counts_zero(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)
    request = BackendSelectionRequest(
        backend="backtrader",
        clean_feed_evidence=_clean_evidence(quality_status="fail"),
        feature_flags={"backtrader_runtime_authorized": True, "allow_backtrader_import": True},
    )

    result = select_research_backend(request)
    metadata = result.to_metadata()

    assert result.availability_status == "quality_fail"
    assert "quality_fail:quality_status" in result.blocked_reasons
    assert result.import_attempted is False
    assert metadata["forbidden_operation_counts"]["provider_fetch"] == 0
    assert metadata["forbidden_operation_counts"]["backtrader_run"] == 0


def test_runtime_gate_not_authorized_blocks_without_import(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)
    request = BackendSelectionRequest(backend="backtrader", clean_feed_evidence=_clean_evidence())

    result = select_research_backend(request)

    assert result.selected_backend == "none"
    assert result.availability_status == "runtime_not_authorized"
    assert "runtime_not_authorized:backtrader_runtime_authorized_false" in result.blocked_reasons
    assert result.import_attempted is False


def test_dependency_missing_returns_backend_unavailable_without_bare_exception(monkeypatch):
    real_import_module = importlib.import_module

    def missing_import(name: str):
        if name == "backtrader":
            raise ImportError("missing optional backend")
        return real_import_module(name)

    monkeypatch.setattr(adapter.importlib, "import_module", missing_import)
    request = BackendSelectionRequest(
        backend="backtrader",
        clean_feed_evidence=_clean_evidence(),
        feature_flags={"backtrader_runtime_authorized": True, "allow_backtrader_import": True},
    )

    result = select_research_backend(request)

    assert result.selected_backend == "none"
    assert result.availability_status == "backend_unavailable"
    assert result.blocked_reasons == ("backend_unavailable:dependency_missing",)
    assert result.import_attempted is True
    assert result.unavailable is not None


def test_backtest_wrapper_returns_selector_block_without_runtime_import(monkeypatch):
    monkeypatch.setattr(adapter.importlib, "import_module", _no_import)
    close_df = pd.DataFrame(
        {"A": range(10, 22), "B": range(20, 8, -1)},
        index=[item.date() for item in pd.bdate_range("2020-01-01", periods=12)],
    )
    request = BackendSelectionRequest(
        backend="backtrader",
        clean_feed_evidence=_clean_evidence(pit_checked=False),
        feature_flags={"backtrader_runtime_authorized": True, "allow_backtrader_import": True},
    )

    result = run_backtest_with_backend(close_df, backend="backtrader", backend_selection_request=request)

    assert result.availability_status == "blocked_clean_feed_pit"
    assert result.import_attempted is False


def test_cr025_static_forbidden_imports_and_no_backtrader_source_reference():
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
    assert "/home/hyde/download/backtrader" not in adapter_source
    assert "TUSHARE_TOKEN" not in adapter_source
    assert "os.environ" not in adapter_source
