from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pandas as pd

from experiments.run_data_benchmark_audit_exp14 import run_audit


def write_dataset(root: Path, *, days: int = 6) -> None:
    data_dir = root / "data"
    data_dir.mkdir(parents=True)
    dates = pd.date_range("2024-01-02", periods=days, freq="B").strftime("%Y-%m-%d").tolist()
    prices = pd.DataFrame(
        [
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "close": 10.0 + day_index + symbol_index,
                "available_at": f"{trade_date}T16:00:00+08:00",
                "adjustment_policy": "qfq",
                "volume": 1000.0,
                "amount": 10000.0,
                "is_suspended": False,
            }
            for day_index, trade_date in enumerate(dates)
            for symbol_index, symbol in enumerate(("000001.SZ", "600519.SH"))
        ]
    )
    index_members = pd.DataFrame(
        [
            {
                "symbol": symbol,
                "snapshot_date": dates[-1],
                "effective_date": dates[-1],
                "available_at": f"{dates[-1]}T16:00:00+08:00",
                "is_member": True,
                "is_pit_universe": False,
                "index_code": "LOCAL",
            }
            for symbol in ("000001.SZ", "600519.SH")
        ]
    )
    calendar = pd.DataFrame([{"trade_date": trade_date, "is_open": True} for trade_date in dates])
    prices.to_parquet(data_dir / "prices.parquet", index=False)
    index_members.to_parquet(data_dir / "index_members.parquet", index=False)
    calendar.to_parquet(data_dir / "trade_calendar.parquet", index=False)


def write_quality_report(root: Path, *, end_date: str = "2024-01-09") -> Path:
    path = root / "reports" / "data_quality_report.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "dataset": dataset,
            "coverage_start": "2024-01-02",
            "coverage_end": end_date,
            "missing_rate": "0.0",
            "duplicate_record_count": "0",
            "abnormal_price_count": "0",
            "quality_status": "pass",
            "adjustment_policy": "qfq" if dataset in {"prices", "overall"} else "",
            "is_pit_universe": "False",
        }
        for dataset in ("prices", "index_members", "trade_calendar", "overall")
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def write_phase_report(root: Path, text: str) -> Path:
    path = root / "reports" / "experiment_13" / "backtest_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def args_for(root: Path, *, horizon: int = 2, phase_report: Path | None = None) -> Namespace:
    return Namespace(
        data_dir=str(root / "data"),
        quality_report=str(root / "reports" / "data_quality_report.csv"),
        phase_two_report=str(phase_report or root / "reports" / "experiment_13" / "backtest_report.md"),
        output_dir=str(root / "reports" / "experiment_14"),
        forward_return_horizon=horizon,
        market_data_lake_root=None,
        benchmark_kind="price_index",
        benchmark_confirmed=False,
        benchmark_unconfirmed=False,
    )


def test_experiment_14_generates_report_with_core_disclosures(tmp_path):
    write_dataset(tmp_path, days=6)
    write_quality_report(tmp_path)
    write_phase_report(
        tmp_path,
        "回测区间：2024-01-02 至 2024-01-09。\n"
        "当前没有沪深300指数行情文件；基准代理使用同股票池等权。\n"
        "股票池为固定快照，存在幸存者偏差。\n",
    )

    report_path = run_audit(args_for(tmp_path, horizon=2))

    text = report_path.read_text(encoding="utf-8")
    assert "审计状态：**WARN**" in text
    assert "2024-01-02" in text
    assert "2024-01-05" in text
    assert "adjustment_policy=qfq" in text
    assert "固定快照池" in text
    assert "PIT 池" in text
    assert "代理基准" in text
    assert "幸存者偏差" in text


def test_experiment_14_fails_when_forward_horizon_exceeds_calendar(tmp_path):
    write_dataset(tmp_path, days=3)
    write_quality_report(tmp_path, end_date="2024-01-04")
    write_phase_report(tmp_path, "基准代理使用同股票池等权。股票池为固定快照。")

    report_path = run_audit(args_for(tmp_path, horizon=5))

    text = report_path.read_text(encoding="utf-8")
    assert "审计状态：**FAIL**" in text
    assert "不足以支持 5 日未来收益计算" in text


def test_experiment_14_marks_phase_report_date_out_of_current_coverage(tmp_path):
    write_dataset(tmp_path, days=4)
    write_quality_report(tmp_path, end_date="2024-01-05")
    write_phase_report(
        tmp_path,
        "回测区间：2025-01-02 至 2025-05-07。基准代理使用同股票池等权。股票池为固定快照。",
    )

    report_path = run_audit(args_for(tmp_path, horizon=1))

    text = report_path.read_text(encoding="utf-8")
    assert "阶段二报告仅作为 legacy 限制记录，不读取内容" in text
    assert "legacy_only_not_current_truth" in text
    assert "2025-05-07" not in text


def test_experiment_14_reports_missing_prices_without_traceback(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pd.DataFrame([{"symbol": "000001.SZ", "is_pit_universe": False}]).to_parquet(data_dir / "index_members.parquet", index=False)
    pd.DataFrame([{"trade_date": "2024-01-02", "is_open": True}]).to_parquet(data_dir / "trade_calendar.parquet", index=False)
    write_quality_report(tmp_path, end_date="2024-01-02")
    write_phase_report(tmp_path, "基准代理使用同股票池等权。股票池为固定快照。")

    report_path = run_audit(args_for(tmp_path, horizon=1))

    text = report_path.read_text(encoding="utf-8")
    assert "审计状态：**FAIL**" in text
    assert "缺少标准 parquet" in text
    assert "Traceback" not in text
