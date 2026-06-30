from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.anomaly_research import run_chapter5_analysis
from engine.factor_robustness import (
    FORBIDDEN_OPERATION_COUNTS,
    run_chapter6_analysis,
    validate_chapter6_inputs,
)
from scripts.research.run_factor_robustness import (
    assert_chapter5_report_pass,
    run_chapter6_from_paths,
)
from tests.research.test_factor_models import _panel_and_labels
from tests.research.test_anomalies import _model_returns


def _anomaly_panel(panel: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
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
    return result.anomaly_panel.assign(sample_id="fixture")


def test_chapter6_analysis_builds_robustness_outputs() -> None:
    panel, labels = _panel_and_labels(periods=24, symbols=45)
    result = run_chapter6_analysis(
        panel,
        labels,
        _anomaly_panel(panel, labels),
        run_id="run-cr037-fixture",
        sample_id="fixture",
        min_cross_section=20,
        quantiles=5,
        rolling_window=6,
        rolling_min_periods=3,
    )

    assert result.status == "PASS"
    assert "value_bm" in result.asset_ids
    assert "valuation_extreme_spread" in result.asset_ids
    assert not result.robustness_returns.empty
    assert not result.rolling_ic.empty
    assert not result.annual_factor_metrics.empty
    assert not result.market_state_results.empty
    assert not result.decay_report.empty
    assert result.ml_leakage_audit["status"] == "PASS"
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready", "ml_model_ready"} <= {
        item["claim"] for item in result.blocked_claims
    }


def test_chapter6_validation_rejects_missing_factor_and_label_leakage() -> None:
    panel, labels = _panel_and_labels()
    with pytest.raises(ValueError, match="缺少因子"):
        validate_chapter6_inputs(panel[panel["factor_id"] != "value_bm"], labels, pd.DataFrame())

    leaked = labels.copy()
    leaked["label_available_at"] = leaked["trade_date"].map(lambda value: f"{value}T15:00:00+08:00")
    with pytest.raises(ValueError, match="潜在前视"):
        validate_chapter6_inputs(panel, leaked, pd.DataFrame())


def test_chapter6_runner_writes_artifacts_from_local_paths(tmp_path: Path) -> None:
    panel, labels = _panel_and_labels(periods=24, symbols=45)
    anomaly_panel = _anomaly_panel(panel, labels)
    panel_path = tmp_path / "panel.parquet"
    label_root = tmp_path / "label_parts"
    chapter3_report_path = tmp_path / "EMPIRICAL-RUN-REPORT.json"
    chapter4_report_path = tmp_path / "CHAPTER4-RUN-REPORT.json"
    chapter5_report_path = tmp_path / "CHAPTER5-RUN-REPORT.json"
    anomaly_panel_path = tmp_path / "anomaly_panel.parquet"
    label_root.mkdir()
    panel.to_parquet(panel_path, index=False)
    labels.to_parquet(label_root / "labels_2020.parquet", index=False)
    anomaly_panel.to_parquet(anomaly_panel_path, index=False)
    chapter3_report_path.write_text(json.dumps({"status": "PASS", "limitations": []}), encoding="utf-8")
    chapter4_report_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    chapter5_report_path.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")

    result = run_chapter6_from_paths(
        (
            {
                "sample_id": "fixture",
                "panel_path": str(panel_path),
                "label_root": str(label_root),
                "chapter3_report_path": str(chapter3_report_path),
                "chapter4_report_path": str(chapter4_report_path),
                "chapter5_report_path": str(chapter5_report_path),
                "chapter5_anomaly_panel_path": str(anomaly_panel_path),
            },
        ),
        run_id="run-cr037-fixture",
        output_root=tmp_path / "process",
        report_root=tmp_path / "reports",
        guardrails_path=tmp_path / "docs" / "FACTOR-RESEARCH-GUARDRAILS.md",
        min_cross_section=20,
        quantiles=5,
        rolling_window=6,
        rolling_min_periods=3,
    )

    assert result.status == "PASS"
    assert result.artifacts.robustness_returns_path.exists()
    assert result.artifacts.rolling_ic_path.exists()
    assert result.artifacts.annual_factor_metrics_path.exists()
    assert result.artifacts.market_state_results_path.exists()
    assert result.artifacts.decay_report_path.exists()
    assert result.artifacts.ml_leakage_audit_path.exists()
    assert result.artifacts.guardrails_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS


def test_chapter6_runner_blocks_non_pass_chapter5_report(tmp_path: Path) -> None:
    report_path = tmp_path / "CHAPTER5-RUN-REPORT.json"
    report_path.write_text(json.dumps({"status": "BLOCKED"}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="第五章报告状态不是 PASS"):
        assert_chapter5_report_pass(report_path)
