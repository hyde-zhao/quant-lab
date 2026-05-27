from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from experiments.run_experiment_16_momentum_factor import run_momentum_factor_validation


def write_momentum_dataset(root: Path, *, inject_missing_close: bool = False) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2024-01-02", periods=90, freq="B").strftime("%Y-%m-%d").tolist()
    symbols = ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF")
    price_rows = []
    for day_index, trade_date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            growth = 0.0005 + symbol_index * 0.0006
            close = 10.0 * ((1.0 + growth) ** day_index) + symbol_index
            if inject_missing_close and symbol == "CCC" and day_index == 40:
                close = None
            price_rows.append(
                {
                    "trade_date": trade_date,
                    "symbol": symbol,
                    "close": close,
                    "available_at": f"{trade_date}T16:00:00+08:00",
                    "adjustment_policy": "qfq",
                    "volume": 1000.0 + day_index * 5.0 + symbol_index * 20.0,
                    "amount": (close or 0.0) * 1000.0,
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
        "data_dir": str(root / "data"),
        "output_dir": str(root / "reports" / "experiment_16"),
        "start_date": None,
        "end_date": None,
        "factors": ["momentum_5d", "momentum_20d"],
        "group_count": 3,
        "min_cross_section": 3,
        "preview_rows": 20,
    }
    values.update(overrides)
    return Namespace(**values)


def test_experiment_16_generates_ic_group_spread_and_report(tmp_path):
    write_momentum_dataset(tmp_path)

    result = run_momentum_factor_validation(args_for(tmp_path))

    report = result.report_path.read_text(encoding="utf-8")
    ic_summary = pd.read_csv(result.ic_summary_path)
    group_returns = pd.read_csv(result.group_returns_path)
    top_bottom = pd.read_csv(result.top_bottom_path)

    row = ic_summary[(ic_summary["factor_name"] == "momentum_5d") & (ic_summary["horizon"] == "1d")].iloc[0]
    spread = top_bottom[(top_bottom["factor_name"] == "momentum_5d") & (top_bottom["horizon"] == "1d")].iloc[0]

    assert "实验十六：动量因子有效性检验报告" in report
    assert "IC / Rank IC / ICIR 汇总" in report
    assert row["ic_mean"] > 0
    assert row["rank_ic_mean"] > 0
    assert spread["top_bottom_mean"] > 0
    assert set(group_returns[group_returns["factor_name"] == "momentum_5d"]["group"]) == {1, 2, 3}


def test_experiment_16_reports_missing_close_coverage(tmp_path):
    write_momentum_dataset(tmp_path, inject_missing_close=True)

    result = run_momentum_factor_validation(args_for(tmp_path, factors=["momentum_5d"]))

    coverage = pd.read_csv(result.data_coverage_path)
    report = result.report_path.read_text(encoding="utf-8")
    close_null = coverage[(coverage["scope"] == "source_prices") & (coverage["item"] == "close_null")].iloc[0]
    matrix_cells = coverage[(coverage["scope"] == "price_matrix") & (coverage["item"] == "close_matrix_cells")].iloc[0]

    assert close_null["missing_count"] == 1
    assert matrix_cells["missing_count"] == 1
    assert "存在数据缺失或覆盖不足" in report
