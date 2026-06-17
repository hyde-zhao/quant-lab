from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.chapter5_anomalies import (
    DEFAULT_CHAPTER5_ANOMALIES,
    FORBIDDEN_OPERATION_COUNTS,
    run_chapter5_analysis,
    validate_chapter5_inputs,
)
from tests.test_chapter4_factor_models import _panel_and_labels
from scripts.run_chapter5_anomalies import (
    assert_chapter4_report_pass,
    run_chapter5_from_paths,
)


def _model_returns(periods: int = 18) -> pd.DataFrame:
    dates = pd.date_range("2020-01-31", periods=periods, freq="ME").date
    rows: list[dict[str, object]] = []
    for index, trade_date in enumerate(dates):
        for model_id, scale in {
            "seven_factor_full": 0.8,
            "ashare_pricing_candidate": 0.6,
            "ff3_equity_core": 0.4,
        }.items():
            rows.append(
                {
                    "schema_version": "fixture",
                    "trade_date": trade_date.isoformat(),
                    "model_id": model_id,
                    "model_return": 0.01 * scale + 0.001 * np.sin(index),
                    "sample_id": "fixture",
                }
            )
    return pd.DataFrame(rows)


def test_chapter5_analysis_builds_anomaly_panel_returns_and_alpha_tests() -> None:
    panel, labels = _panel_and_labels()
    result = run_chapter5_analysis(
        panel,
        labels,
        _model_returns(),
        run_id="run-cr036-fixture",
        sample_id="fixture",
        min_cross_section=20,
        quantiles=5,
        residual_window=6,
        residual_min_periods=3,
    )

    assert result.status == "PASS"
    assert set(result.anomaly_ids) == {item.anomaly_id for item in DEFAULT_CHAPTER5_ANOMALIES}
    assert not result.anomaly_panel.empty
    assert not result.anomaly_returns.empty
    assert not result.alpha_tests.empty
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready"} <= {
        item["claim"] for item in result.blocked_claims
    }
    assert any(gap["gap_id"] == "CR036-GAP-BOOK-CHAPTER5-SOURCE" for gap in result.gap_register)


def test_chapter5_validation_rejects_missing_factor_and_label_leakage() -> None:
    panel, labels = _panel_and_labels()
    with pytest.raises(ValueError, match="缺少异象必需因子"):
        validate_chapter5_inputs(panel[panel["factor_id"] != "value_bm"], labels, _model_returns())

    leaked = labels.copy()
    leaked["label_available_at"] = leaked["trade_date"].map(lambda value: f"{value}T15:00:00+08:00")
    with pytest.raises(ValueError, match="潜在前视"):
        validate_chapter5_inputs(panel, leaked, _model_returns())


def test_chapter5_runner_writes_artifacts_from_local_paths(tmp_path: Path) -> None:
    panel, labels = _panel_and_labels()
    panel_path = tmp_path / "panel.parquet"
    label_root = tmp_path / "label_parts"
    chapter3_report_path = tmp_path / "EMPIRICAL-RUN-REPORT.json"
    chapter4_report_path = tmp_path / "CHAPTER4-RUN-REPORT.json"
    model_returns_path = tmp_path / "factor_model_returns.parquet"
    label_root.mkdir()
    panel.to_parquet(panel_path, index=False)
    labels.to_parquet(label_root / "labels_2020.parquet", index=False)
    chapter3_report_path.write_text(json.dumps({"status": "PASS", "limitations": []}), encoding="utf-8")
    chapter4_report_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    _model_returns().to_parquet(model_returns_path, index=False)

    result = run_chapter5_from_paths(
        (
            {
                "sample_id": "fixture",
                "panel_path": str(panel_path),
                "label_root": str(label_root),
                "chapter3_report_path": str(chapter3_report_path),
                "chapter4_report_path": str(chapter4_report_path),
                "chapter4_model_returns_path": str(model_returns_path),
            },
        ),
        run_id="run-cr036-fixture",
        output_root=tmp_path / "process",
        report_root=tmp_path / "reports",
        min_cross_section=20,
        quantiles=5,
        residual_window=6,
        residual_min_periods=3,
    )

    assert result.status == "PASS"
    assert result.artifacts.anomaly_panel_path.exists()
    assert result.artifacts.anomaly_returns_path.exists()
    assert result.artifacts.alpha_tests_path.exists()
    assert result.artifacts.gap_register_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS


def test_chapter5_runner_blocks_non_pass_chapter4_report(tmp_path: Path) -> None:
    report_path = tmp_path / "CHAPTER4-RUN-REPORT.json"
    report_path.write_text(json.dumps({"status": "BLOCKED"}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="第四章报告状态不是 PASS"):
        assert_chapter4_report_pass(report_path)
