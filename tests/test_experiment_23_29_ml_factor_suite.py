from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from experiments.run_experiment_23_29_ml_factor_suite import run_stage4_suite


def write_stage4_dataset(root: Path, *, days: int = 260, symbols: int = 10) -> Path:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2023-01-02", periods=days, freq="B")
    symbol_names = [f"STK{index:03d}" for index in range(symbols)]
    rows = []
    for day_index, trade_date in enumerate(dates):
        market_cycle = ((day_index % 23) - 11) * 0.015
        for symbol_index, symbol in enumerate(symbol_names):
            trend = (symbol_index - symbols / 2) * 0.006 * day_index
            reversal_wave = ((day_index + symbol_index * 2) % 17 - 8) * (0.025 + symbol_index * 0.002)
            close = max(5.0, 30.0 + symbol_index * 1.5 + trend + reversal_wave + market_cycle)
            volume = 20_000.0 + day_index * (20 + symbol_index) + symbol_index * 500.0
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


def test_stage4_suite_generates_expected_reports_with_bounded_concurrency(tmp_path: Path) -> None:
    data_dir = write_stage4_dataset(tmp_path)
    output_root = tmp_path / "reports"
    args = Namespace(
        data_dir=str(data_dir),
        output_root=str(output_root),
        start_date=None,
        end_date=None,
        horizon=20,
        group_count=3,
        min_cross_section=3,
        rebalance_freq=20,
        top_fractions=[0.2],
        exit_fraction=0.4,
        initial_cash=100_000.0,
        max_symbols=0,
        max_workers=1,
        model_threads=1,
        param_scan_limit=1,
        lgbm_estimators=12,
        early_stopping_rounds=3,
        permutation_repeats=1,
        random_state=7,
        verbose=False,
    )

    result = run_stage4_suite(args)

    expected_reports = {
        "experiment_23_volatility_audit/volatility_baseline_audit_report.md",
        "experiment_24_ml_dataset_and_labels/leakage_audit.md",
        "experiment_25_ml_baselines/baseline_model_report.md",
        "experiment_26_tree_model_features/tree_model_report.md",
        "experiment_27_feature_importance/feature_importance_report.md",
        "experiment_28_walk_forward/walk_forward_report.md",
        "experiment_29_ml_strategy_and_summary/stage4_summary.md",
    }
    assert expected_reports == {str(path.relative_to(output_root)) for path in result.report_paths.values()}

    dataset = pd.read_parquet(output_root / "experiment_24_ml_dataset_and_labels" / "ml_factor_dataset.parquet")
    assert not dataset.duplicated(subset=["date", "symbol"]).any()
    assert {"volatility_20d", "rsi_14", "max_drawdown_20d", "reversal_5d", "forward_return_20d", "top_quantile_20d"}.issubset(dataset.columns)

    audit = pd.read_csv(output_root / "experiment_24_ml_dataset_and_labels" / "purge_embargo_audit.csv")
    assert audit["purge_pass"].fillna(False).all()
    assert audit["embargo_pass"].fillna(False).all()
