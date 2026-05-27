from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from experiments.run_experiment_30_36_stage5 import run_stage5_suite


def write_stage5_dataset(root: Path, *, days: int = 180, symbols: int = 12) -> Path:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2023-01-02", periods=days, freq="B")
    symbol_names = [f"STK{index:03d}" for index in range(symbols)]
    rows = []
    for day_index, trade_date in enumerate(dates):
        market_wave = ((day_index % 31) - 15) * 0.01
        for symbol_index, symbol in enumerate(symbol_names):
            trend = (symbols - symbol_index) * 0.004 * day_index
            cycle = ((day_index + symbol_index * 3) % 19 - 9) * (0.02 + symbol_index * 0.002)
            close = max(3.0, 20.0 + symbol_index * 1.2 + trend + cycle + market_wave)
            volume = 50_000.0 + day_index * (20 + symbol_index) + symbol_index * 1_000.0
            rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": symbol,
                    "close": close,
                    "available_at": trade_date.date().isoformat(),
                    "adjustment_policy": "qfq",
                    "volume": volume,
                    "amount": close * volume,
                    "is_suspended": False,
                }
            )
    members = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "snapshot_date": dates[-1].date().isoformat(),
                "effective_date": dates[0].date().isoformat(),
                "available_at": dates[0].date().isoformat(),
                "is_member": True,
                "is_pit_universe": False,
                "index_code": "UNIT",
            }
            for symbol in symbol_names
        ]
    )
    calendar = pd.DataFrame([{"trade_date": item.date().isoformat(), "is_open": True} for item in dates])
    pd.DataFrame(rows).to_parquet(data_dir / "prices.parquet", index=False)
    members.to_parquet(data_dir / "index_members.parquet", index=False)
    calendar.to_parquet(data_dir / "trade_calendar.parquet", index=False)
    return data_dir


def test_stage5_suite_generates_reports_and_integrated_summary(tmp_path: Path) -> None:
    data_dir = write_stage5_dataset(tmp_path)
    output_root = tmp_path / "reports"
    args = Namespace(
        data_dir=str(data_dir),
        output_root=str(output_root),
        start_date=None,
        end_date=None,
        min_cross_section=3,
        winsor_lower=0.01,
        winsor_upper=0.99,
        rebalance_freq=20,
        top_fractions=[0.25],
        exit_fraction=0.5,
        initial_cash=100_000.0,
        max_symbols=0,
        ml_predictions_path=str(tmp_path / "missing_ml_predictions.parquet"),
        preview_rows=100,
    )

    result = run_stage5_suite(args)

    expected = {
        "experiment_30_report",
        "experiment_31_drawdown",
        "experiment_31_tail",
        "experiment_32_position",
        "experiment_32_constraints",
        "experiment_32_drawdown",
        "experiment_33_turnover",
        "experiment_33_cost",
        "experiment_34_tradability",
        "experiment_34_benchmark_plan",
        "experiment_35_backlog",
        "experiment_35_report",
        "experiment_36_integrated",
        "experiment_36_summary",
    }
    assert expected.issubset(result.report_paths)
    for path in result.report_paths.values():
        assert path.exists()

    baseline = pd.read_csv(output_root / "experiment_30_stage5_baseline_risk" / "baseline_strategy_summary.csv")
    integrated = pd.read_csv(output_root / "experiment_36_stage5_summary" / "integrated_backtest_summary.csv")
    gaps = pd.read_csv(output_root / "experiment_34_tradability_data_gap" / "data_gap_register.csv")

    assert {"proxy_equal_weight_buy_hold", "single_volatility_20d_top25", "stage3_equal_weight_multifactor_top25"}.issubset(set(baseline["strategy_name"]))
    assert "annual_return" in integrated.columns
    assert {"real_benchmark", "industry", "market_cap"}.issubset(set(gaps["field"]))
