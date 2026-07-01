from __future__ import annotations

import ast
import argparse
from pathlib import Path

import pandas as pd
import pytest

from engine.backtest import BacktestConfig, run_backtest_from_loaded_data
from engine.data_loader import DataContractError, DataQualityGateError, LoaderConfig, load_backtest_data
from market_data.cli import cmd_publish, cmd_validate
from market_data.catalog import CatalogEntry, CatalogStore
from market_data.contracts import DATASET_PRICES, INTERFACE_PRICES_DAILY, SOURCE_TUSHARE
from market_data.lake_layout import LakeLayout
from market_data.readers import LightweightInputRequest, read_lightweight_input


def _prices_frame(policy: str = "qfq") -> pd.DataFrame:
    rows = []
    for offset, trade_date in enumerate(pd.bdate_range("2026-01-02", periods=6)):
        for symbol, base in (("000001.SZ", 10.0), ("000002.SZ", 20.0)):
            close = base + offset
            rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "open": close - 0.2,
                    "high": close + 0.3,
                    "low": close - 0.4,
                    "close": close,
                    "adj_factor": 2.0,
                    "adjusted_open": (close - 0.2) * 2,
                    "adjusted_high": (close + 0.3) * 2,
                    "adjusted_low": (close - 0.4) * 2,
                    "adjusted_close": close * 2,
                    "adjustment_policy": policy,
                    "source": SOURCE_TUSHARE,
                    "source_interface": INTERFACE_PRICES_DAILY,
                    "source_run_id": "run-cr006-s02",
                    "schema_version": "1.0",
                    "available_at": f"{trade_date.date().isoformat()}T16:00:00+08:00",
                    "available_at_rule": "daily_close_fact",
                    "lineage_raw_checksum": "checksum-cr006-s02",
                }
            )
    return pd.DataFrame(rows)


def _write_prices_lake(tmp_path: Path, *, quality_status: str = "pass", frame: pd.DataFrame | None = None) -> Path:
    layout = LakeLayout(tmp_path)
    path = layout.canonical_dataset_root(DATASET_PRICES) / "run_id=run-cr006-s02" / "part.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    (frame if frame is not None else _prices_frame()).to_parquet(path, index=False)
    CatalogStore(layout).upsert(
        CatalogEntry(
            dataset=DATASET_PRICES,
            start_date="2026-01-02",
            end_date="2026-01-09",
            quality_status=quality_status,
            dataset_status="available" if quality_status != "fail" else "quality_failed",
            latest_manifest_run_id="run-cr006-s02",
            source=SOURCE_TUSHARE,
            source_interface=INTERFACE_PRICES_DAILY,
            lineage_raw_checksum="checksum-cr006-s02",
            canonical_path=str(path.relative_to(tmp_path)),
        )
    )
    return path


def test_canonical_gold_ok_feeds_data_loader_and_backtest(tmp_path: Path) -> None:
    _write_prices_lake(tmp_path)

    result = read_lightweight_input(
        LightweightInputRequest(
            lake_root=tmp_path,
            start_date="2026-01-02",
            end_date="2026-01-09",
            quality_policy="require_pass",
        )
    )

    assert result.status == "ok"
    assert result.close_df is not None
    assert result.universe == ["000001.SZ", "000002.SZ"]
    assert result.metadata["input_mode"] == "canonical_gold"
    assert result.metadata["manifest_run_id"] == "run-cr006-s02"

    loaded = load_backtest_data(
        LoaderConfig(
            input_mode="canonical_gold",
            market_data_lake_root=tmp_path,
            start_date="2026-01-02",
            end_date="2026-01-09",
        )
    )
    backtest = run_backtest_from_loaded_data(
        loaded,
        BacktestConfig(lookback_days=2, rebalance_freq=1, top_fraction=0.5),
    )
    assert backtest.schedule
    assert backtest.metadata["input_mode"] == "canonical_gold"


def test_validate_catalog_without_canonical_path_fails_closed_even_with_multipart_history(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    frame = _prices_frame()
    for symbol, part in frame.groupby("symbol"):
        path = layout.canonical_dataset_root(DATASET_PRICES) / f"run_id=run-{symbol}" / "part.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        part.to_parquet(path, index=False)

    open_dates = sorted(str(item)[:10] for item in frame["trade_date"].unique())
    cmd_validate(
        argparse.Namespace(
            lake_root=tmp_path,
            dataset=DATASET_PRICES,
            symbols="000001.SZ,000002.SZ",
            index_code=None,
            start_date=open_dates[0],
            end_date=open_dates[-1],
            run_id="run-cr006-multipart",
            open_trade_dates=",".join(open_dates),
            prices_missing_rate_pass=0.0,
            prices_missing_rate_warn=0.05,
            prices_missing_rate_fail=0.2,
        )
    )

    entry = CatalogStore(layout).get(DATASET_PRICES)
    assert entry.canonical_path is None
    cmd_publish(argparse.Namespace(lake_root=tmp_path, dataset=DATASET_PRICES, allow_warn=True))
    result = read_lightweight_input(
        LightweightInputRequest(
            lake_root=tmp_path,
            start_date=open_dates[0],
            end_date=open_dates[-1],
            quality_policy="allow_warn",
        )
    )
    assert result.status == "required_missing"
    assert result.issues == [{"code": "canonical_missing", "dataset": DATASET_PRICES}]
    assert result.close_df is None


def test_quality_fail_and_missing_canonical_are_structured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_prices_lake(tmp_path / "quality-fail", quality_status="fail")

    with pytest.raises(DataQualityGateError, match="quality_failed"):
        load_backtest_data(
            LoaderConfig(
                input_mode="canonical_gold",
                market_data_lake_root=tmp_path / "quality-fail",
                start_date="2026-01-02",
                end_date="2026-01-09",
            )
        )

    monkeypatch.delenv("MARKET_DATA_LAKE_ROOT", raising=False)
    missing = read_lightweight_input(LightweightInputRequest(lake_root=None))
    assert missing.status == "required_missing"
    assert missing.remediation_job_spec["auto_execute"] is False


def test_repo_data_default_and_legacy_flat_are_not_p0_fallbacks() -> None:
    with pytest.raises(DataContractError, match="reference-only"):
        load_backtest_data(LoaderConfig(start_date="2026-01-02", end_date="2026-01-09"))

    disabled = read_lightweight_input(LightweightInputRequest(input_mode="legacy_flat"))
    assert disabled.status == "invalid_request"
    assert disabled.issues == [{"code": "legacy_flat_disabled", "dataset": DATASET_PRICES}]

    repo_data = read_lightweight_input(
        LightweightInputRequest(
            input_mode="legacy_flat",
            legacy_flat_enabled=True,
            legacy_flat_dir="data",
        )
    )
    assert repo_data.status == "invalid_request"
    assert repo_data.issues[0]["code"] == "repo_data_reference_only"


def test_raw_manifest_connectors_runtime_and_credentials_are_not_runtime_dependencies() -> None:
    for path in (
        "market_data/readers.py",
        "engine/data_loader.py",
        "engine/backtest.py",
    ):
        source = Path(path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name.startswith("market_data.connectors") for name in imports)
        assert "market_data.runtime" not in imports
        assert "market_data.storage" not in imports
        assert ".env" not in source
        assert "TUSHARE_TOKEN" not in source
