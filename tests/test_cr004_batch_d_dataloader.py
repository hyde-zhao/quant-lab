from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from engine.contracts import STANDARD_PARQUET_FILES
from engine.data_loader import DataContractError, DataQualityGateError, LoaderConfig, load_backtest_data


def _write_loader_fixture(
    root: Path,
    *,
    quality_status: str = "pass",
    dataset_status: str = "available",
    include_required_quality_fields: bool = True,
) -> tuple[Path, Path]:
    data_dir = root / "data"
    reports_dir = root / "reports"
    (data_dir / "manifests").mkdir(parents=True)
    reports_dir.mkdir()
    prices = pd.DataFrame(
        {
            "trade_date": ["2020-01-02", "2020-01-03"],
            "symbol": ["000001", "000001"],
            "close": [10.0, 11.0],
            "adjustment_policy": ["qfq", "qfq"],
        }
    )
    members = pd.DataFrame({"symbol": ["000001"], "is_pit_universe": [False]})
    calendar = pd.DataFrame({"trade_date": ["2020-01-02", "2020-01-03"], "is_open": [True, True]})
    for dataset, frame in {"prices": prices, "index_members": members, "trade_calendar": calendar}.items():
        frame.to_parquet(data_dir / STANDARD_PARQUET_FILES[dataset], index=False)
    (data_dir / "manifests" / "data_prep_manifest.jsonl").write_text(
        '{"run_id":"run-cr004-batch-d","status":"success"}\n',
        encoding="utf-8",
    )
    if include_required_quality_fields:
        quality_text = (
            "dataset,quality_status,fetch_status,dataset_status,missing_rate,failed_batch_count,"
            "manifest_run_id,coverage_denominator,denominator_mode,thresholds_json,input_config_hash,"
            "last_successful_update_at,data_freshness_trade_days,data_freshness_calendar_days\n"
            f"overall,{quality_status},success,{dataset_status},0,0,run-cr004-batch-d,2,"
            'open_trade_dates_in_requested_range_x_target_symbols,"{}",hash-cr004,2020-01-03,0,0\n'
        )
    else:
        quality_text = "dataset,quality_status,manifest_run_id\noverall,pass,run-cr004-batch-d\n"
    (reports_dir / "data_quality_report.csv").write_text(quality_text, encoding="utf-8")
    return data_dir, reports_dir


def _config(data_dir: Path, reports_dir: Path, **overrides: object) -> LoaderConfig:
    values = {
        "data_dir": data_dir,
        "manifest_path": data_dir / "manifests" / "data_prep_manifest.jsonl",
        "quality_report_path": reports_dir / "data_quality_report.csv",
        "start_date": "2020-01-02",
        "end_date": "2020-01-03",
    }
    values.update(overrides)
    return LoaderConfig(**values)


def test_default_quality_policy_rejects_warn_and_allow_warn_discloses_metadata(tmp_path: Path) -> None:
    data_dir, reports_dir = _write_loader_fixture(tmp_path, quality_status="warn", dataset_status="warn")

    with pytest.raises(DataQualityGateError, match="默认策略拒绝启动"):
        load_backtest_data(_config(data_dir, reports_dir))

    loaded = load_backtest_data(_config(data_dir, reports_dir, quality_policy="allow_warn"))

    assert loaded.metadata["quality_status"] == "warn"
    assert loaded.metadata["dataset_status"] == "warn"
    assert loaded.metadata["allow_warn"] is True
    assert loaded.metadata["quality_decision_reason"] == "quality_warn_allowed_explicitly"
    assert "warn_minor_missing_rate" in loaded.metadata["warnings"]
    assert "warn_non_pit_universe" in loaded.metadata["warnings"]


def test_dataset_status_fail_is_never_released_by_allow_warn(tmp_path: Path) -> None:
    data_dir, reports_dir = _write_loader_fixture(tmp_path, quality_status="warn", dataset_status="fail")

    with pytest.raises(DataQualityGateError, match="dataset_status=fail"):
        load_backtest_data(_config(data_dir, reports_dir, quality_policy="allow_warn"))


def test_missing_required_quality_fields_fail_fast(tmp_path: Path) -> None:
    data_dir, reports_dir = _write_loader_fixture(tmp_path, include_required_quality_fields=False)

    with pytest.raises(DataQualityGateError, match="fetch_status"):
        load_backtest_data(_config(data_dir, reports_dir))


def test_markdown_quality_report_is_human_only(tmp_path: Path) -> None:
    data_dir, reports_dir = _write_loader_fixture(tmp_path)
    markdown = reports_dir / "data_quality_report.md"
    markdown.write_text("| dataset | quality_status |\n|---|---|\n| overall | pass |\n", encoding="utf-8")

    with pytest.raises(DataQualityGateError, match="Markdown"):
        load_backtest_data(_config(data_dir, reports_dir, quality_report_path=markdown))


def test_manifest_missing_fails_before_quality_fallback(tmp_path: Path) -> None:
    data_dir, reports_dir = _write_loader_fixture(tmp_path)
    (data_dir / "manifests" / "data_prep_manifest.jsonl").unlink()

    with pytest.raises(DataContractError, match="缺少 manifest"):
        load_backtest_data(_config(data_dir, reports_dir))
