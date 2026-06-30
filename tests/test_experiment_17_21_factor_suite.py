from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from experiments.run_experiment_15_factor_framework import load_local_frames
from experiments.run_experiment_17_21_factor_suite import (
    calculate_rsi,
    factor_definitions,
    preprocess_factor_matrices,
    run_factor_suite,
)


def write_factor_suite_dataset(root: Path, *, days: int = 90, symbols: tuple[str, ...] = ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF")) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2024-01-02", periods=days, freq="B").strftime("%Y-%m-%d").tolist()
    rows = []
    for day_index, trade_date in enumerate(dates):
        market_wave = 0.15 * ((day_index % 17) - 8) / 8
        for symbol_index, symbol in enumerate(symbols):
            trend = (symbol_index - 2) * 0.018 * day_index
            cycle = ((day_index + symbol_index * 3) % 11 - 5) * (0.03 + symbol_index * 0.004)
            close = 20.0 + symbol_index * 2.5 + trend + cycle + market_wave
            close = max(close, 1.0)
            volume = 1000.0 + day_index * (8 + symbol_index) + symbol_index * 150.0
            rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "close": close,
                    "available_at": f"{trade_date}T16:00:00+08:00",
                    "adjustment_policy": "qfq",
                    "volume": volume,
                    "amount": volume * close,
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
    pd.DataFrame(rows).to_parquet(data_dir / "prices.parquet", index=False)
    members.to_parquet(data_dir / "index_members.parquet", index=False)
    calendar.to_parquet(data_dir / "trade_calendar.parquet", index=False)


def args_for(root: Path, **overrides) -> Namespace:
    values = {
        "lake_root": str(root / "lake"),
        "as_of": "2024-12-31T23:59:59+08:00",
        "quality_policy": "require_pass",
        "fixture_frames": load_local_frames(root / "data"),
        "output_dir": str(root / "reports" / "experiment_17_21"),
        "start_date": None,
        "end_date": None,
        "factors": [
            "momentum_20d",
            "reversal_5d",
            "rsi_14",
            "macd_diff",
            "macd_hist",
            "ma_gap_20",
            "volatility_20d",
            "volume_change_20d",
            "turnover_proxy",
            "max_drawdown_20d",
        ],
        "horizon": 5,
        "group_count": 3,
        "min_cross_section": 3,
        "winsor_lower": 0.01,
        "winsor_upper": 0.99,
        "rebalance_freq": 10,
        "top_fractions": [0.2],
        "exit_fraction": 0.4,
        "initial_cash": 100_000.0,
        "train_fraction": 0.7,
        "max_symbols": 0,
        "preview_rows": 50,
        "min_model_factors": 2,
        "verbose": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_experiment_17_21_generates_factor_stability_and_strategy_outputs(tmp_path: Path) -> None:
    write_factor_suite_dataset(tmp_path)

    result = run_factor_suite(args_for(tmp_path))

    report = result.report_path.read_text(encoding="utf-8")
    retention = pd.read_csv(result.factor_retention_path)
    strategy = pd.read_csv(result.strategy_summary_path)
    sample_split = pd.read_csv(result.sample_split_path)
    preprocessing = pd.read_csv(result.preprocessing_summary_path)

    assert "实验十七：技术因子对比" in report
    assert "实验二十一：因子策略化回测" in report
    assert {"reversal_5d", "rsi_14", "macd_diff", "macd_hist", "ma_gap_20"}.issubset(set(retention["factor_name"]))
    assert {"volatility_20d", "volume_change_20d", "turnover_proxy", "max_drawdown_20d"}.issubset(set(retention["factor_name"]))
    assert {"ic_mean", "icir", "turnover", "max_abs_correlation", "retained"}.issubset(retention.columns)
    assert set(preprocessing["factor_name"]) == set(retention["factor_name"])
    assert "multifactor" in set(strategy["strategy_name"])
    assert {"annual_return_with_cost", "proxy_annual_return", "proxy_excess_annual_return", "cost_erosion"}.issubset(strategy.columns)
    assert set(sample_split["sample"]) == {"in_sample", "out_of_sample"}
    assert result.benchmark_equity_path.exists()


def test_rsi_direction_is_unified_so_lower_raw_rsi_scores_higher() -> None:
    dates = pd.date_range("2024-01-02", periods=25, freq="B").date
    close = pd.DataFrame(
        {
            "LOW_RSI": [30.0 - index * 0.4 for index in range(25)],
            "HIGH_RSI": [20.0 + index * 0.5 for index in range(25)],
            "MID": [25.0 + ((index % 3) - 1) * 0.05 for index in range(25)],
            "SOFT_LOW": [28.0 - index * 0.1 for index in range(25)],
            "SOFT_HIGH": [22.0 + index * 0.1 for index in range(25)],
        },
        index=dates,
    )
    definition = factor_definitions()["rsi_14"]
    raw = {"rsi_14": calculate_rsi(close, window=14)}

    zscores, summary = preprocess_factor_matrices(
        raw,
        [definition],
        winsor_lower=0.0,
        winsor_upper=1.0,
        min_cross_section=3,
    )

    last_scores = zscores["rsi_14"].iloc[-1]
    assert summary.iloc[0]["direction_sign"] == -1
    assert last_scores["LOW_RSI"] > last_scores["HIGH_RSI"]
