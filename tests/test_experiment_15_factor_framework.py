from __future__ import annotations

from argparse import Namespace
import json
from pathlib import Path

import pandas as pd
import pytest

from experiments.run_experiment_15_factor_framework import FactorFrameworkError, load_local_frames, run_factor_framework


def write_factor_dataset(root: Path, *, days: int = 45, symbols: tuple[str, ...] = ("AAA", "BBB", "CCC")) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2024-01-02", periods=days, freq="B").strftime("%Y-%m-%d").tolist()
    price_rows = []
    for day_index, trade_date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            base = 10.0 + symbol_index * 3.0
            drift = (symbol_index + 1) * 0.05 * day_index
            seasonal = 0.01 * ((day_index + symbol_index) % 3)
            close = base + drift + seasonal
            price_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "close": close,
                    "available_at": f"{trade_date}T16:00:00+08:00",
                    "adjustment_policy": "qfq",
                    "volume": 1000.0 + day_index * 10.0 + symbol_index * 100.0,
                    "amount": close * 1000.0,
                    "is_suspended": False,
                }
            )
    members = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "snapshot_date": dates[-1],
                "effective_date": dates[0],
                "available_at": f"{dates[0]}T16:00:00+08:00",
                "is_member": True,
                "is_pit_universe": False,
                "index_code": "LOCAL",
            }
            for symbol in symbols
        ]
    )
    calendar = pd.DataFrame([{"trade_date": trade_date, "is_open": True} for trade_date in dates])
    pd.DataFrame(price_rows).to_parquet(data_dir / "prices.parquet", index=False)
    members.to_parquet(data_dir / "index_members.parquet", index=False)
    calendar.to_parquet(data_dir / "trade_calendar.parquet", index=False)


def args_for(root: Path, **overrides) -> Namespace:
    values = {
        "lake_root": str(root / "lake"),
        "as_of": "2024-12-31T23:59:59+08:00",
        "quality_policy": "require_pass",
        "fixture_frames": load_local_frames(root / "data"),
        "output_dir": str(root / "reports" / "experiment_15"),
        "start_date": None,
        "end_date": None,
        "factors": ["momentum_5d", "volume_ratio_5d"],
        "strategy_factor": "momentum_5d",
        "rebalance_freq": 5,
        "top_fraction": 0.5,
        "initial_cash": 100_000.0,
        "preview_rows": 20,
    }
    values.update(overrides)
    return Namespace(**values)


def test_experiment_15_generates_factor_panel_schema_and_backtest(tmp_path):
    write_factor_dataset(tmp_path)

    result = run_factor_framework(args_for(tmp_path))

    panel = pd.read_parquet(result.factor_panel_path)
    schema = json.loads(result.factor_schema_path.read_text(encoding="utf-8"))
    summary = pd.read_csv(result.backtest_summary_path).iloc[0].to_dict()
    report = result.report_path.read_text(encoding="utf-8")

    assert panel.columns.tolist() == [
        "date",
        "symbol",
        "factor_name",
        "factor_value",
        "factor_zscore",
        "forward_return_1d",
        "forward_return_5d",
        "forward_return_10d",
        "forward_return_20d",
    ]
    assert set(panel["factor_name"]) == {"momentum_5d", "volume_ratio_5d"}
    assert schema["primary_key"] == ["date", "symbol", "factor_name"]
    assert schema["label_policy"]["horizons"] == [1, 5, 10, 20]
    assert summary["status"] == "success"
    assert summary["signal_count"] > 0
    assert "因子策略回测" in report
    assert "固定快照" in report


def test_experiment_15_forward_return_uses_future_close_without_lookahead_in_factor(tmp_path):
    write_factor_dataset(tmp_path, symbols=("AAA", "BBB"))

    result = run_factor_framework(args_for(tmp_path, factors=["momentum_5d"], strategy_factor="momentum_5d"))

    panel = pd.read_parquet(result.factor_panel_path)
    prices = pd.read_parquet(tmp_path / "data" / "prices.parquet")
    row = panel[(panel["factor_name"] == "momentum_5d") & (panel["symbol"] == "AAA")].iloc[0]
    symbol_prices = prices[prices["symbol"] == "AAA"].sort_values("trade_date").reset_index(drop=True)
    position = symbol_prices.index[symbol_prices["trade_date"] == row["date"]][0]
    expected_factor = symbol_prices.loc[position, "close"] / symbol_prices.loc[position - 5, "close"] - 1.0
    expected_forward = symbol_prices.loc[position + 1, "close"] / symbol_prices.loc[position, "close"] - 1.0

    assert row["factor_value"] == pytest.approx(expected_factor)
    assert row["forward_return_1d"] == pytest.approx(expected_forward)


def test_experiment_15_rejects_missing_volume_without_traceback(tmp_path):
    write_factor_dataset(tmp_path)
    prices_path = tmp_path / "data" / "prices.parquet"
    prices = pd.read_parquet(prices_path).drop(columns=["volume"])
    prices.to_parquet(prices_path, index=False)

    with pytest.raises(FactorFrameworkError, match="prices 缺少必需字段: volume"):
        run_factor_framework(args_for(tmp_path))
