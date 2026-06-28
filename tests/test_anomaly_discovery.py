from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.anomaly_admission import build_anomaly_admission_decisions
from engine.anomaly_discovery import (
    FORBIDDEN_OPERATION_COUNTS,
    run_anomaly_discovery,
    validate_anomaly_discovery_inputs,
    write_anomaly_discovery_outputs,
)
from engine.anomaly_multiple_testing import apply_multiple_testing_control
from engine.factor_registry import anomaly_candidate_catalog_entries, filter_factor_catalog_entries
from engine.mature_multifactor_research import build_admitted_anomaly_factor_specs


def _feature_panel(periods: int = 12, symbols: int = 60) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    dates = pd.date_range("2024-01-31", periods=periods, freq="ME")
    for date_index, trade_date in enumerate(dates):
        date_noise = 0.0004 * np.sin(date_index)
        for symbol_index in range(symbols):
            rank = symbol_index / (symbols - 1)
            pb = 6.0 - 5.0 * rank
            forward_return = 0.002 + 0.018 * rank + date_noise
            rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "symbol": f"{symbol_index:06d}.SZ",
                    "pb": pb,
                    "forward_return": forward_return,
                    "available_at": f"{trade_date.date().isoformat()}T16:30:00+08:00",
                    "label_available_at": f"{(trade_date + pd.Timedelta(days=30)).date().isoformat()}T16:30:00+08:00",
                }
            )
    return pd.DataFrame(rows)


def _model_returns(periods: int = 12) -> pd.DataFrame:
    dates = pd.date_range("2024-01-31", periods=periods, freq="ME")
    rows: list[dict[str, object]] = []
    for index, trade_date in enumerate(dates):
        for model_id in ("seven_factor_full", "ashare_pricing_candidate", "ff3_equity_core"):
            rows.append(
                {
                    "trade_date": trade_date.date().isoformat(),
                    "model_id": model_id,
                    "model_return": 0.0001 * np.cos(index),
                }
            )
    return pd.DataFrame(rows)


def test_anomaly_discovery_runs_controlled_batch_and_admits_stage3_candidate() -> None:
    result = run_anomaly_discovery(
        _feature_panel(),
        _model_returns(),
        run_id="anomaly-discovery-unit",
        sample_id="fixture",
        min_cross_section=20,
    )

    assert result.status == "PASS"
    assert result.candidate_count == 1
    assert result.tested_candidate_count == 1
    assert result.admitted_stage3_candidate_count == 1
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    report = result.anomaly_research_reports[0]
    assert report["multiple_testing"]["candidate_count"] == 1
    assert report["multiple_testing"]["multiple_testing_pass"] is True
    decision = result.anomaly_admission_decisions[0]
    assert decision["admission_status"] == "stage3_candidate"
    assert decision["factor_id"] == "auto_value_pb_inverse"


def test_multiple_testing_blocks_stage3_candidate_when_adjusted_significance_fails() -> None:
    reports = apply_multiple_testing_control(
        (
            {
                "anomaly_id": "weak_candidate",
                "decision": "factor_catalog_candidate",
                "mean_long_short_return": 0.02,
                "sorting_t_stat": 3.01,
            },
            {
                "anomaly_id": "other_candidate",
                "decision": "watch_needs_robustness_review",
                "mean_long_short_return": 0.01,
                "sorting_t_stat": 0.2,
            },
        ),
        alpha=0.001,
    )

    decisions = build_anomaly_admission_decisions(reports)

    assert decisions[0].admission_status == "factor_catalog_candidate"
    assert "multiple_testing_control_not_passed" in decisions[0].blocked_reasons


def test_anomaly_discovery_outputs_dynamic_factor_catalog_and_stage3_specs(tmp_path: Path) -> None:
    result = run_anomaly_discovery(
        _feature_panel(),
        _model_returns(),
        run_id="anomaly-discovery-unit",
        sample_id="fixture",
        min_cross_section=20,
    )
    paths = write_anomaly_discovery_outputs(result, tmp_path)

    assert Path(paths["run_report"]).exists()
    candidates = json.loads(Path(paths["anomaly_candidates"]).read_text(encoding="utf-8"))
    decisions = json.loads(Path(paths["anomaly_admission_decisions"]).read_text(encoding="utf-8"))
    extra_entries = anomaly_candidate_catalog_entries(candidates=candidates, decisions=decisions)
    queried = filter_factor_catalog_entries(factor_id="auto_value_pb_inverse", extra_entries=extra_entries)
    specs = build_admitted_anomaly_factor_specs(
        "stage3-candidate-unit",
        {},
        anomaly_candidates=candidates,
        anomaly_admission_decisions=decisions,
    )

    assert queried[0].family == "anomaly_discovery_candidate"
    assert queried[0].status == "calculable"
    assert "stage3_candidate" in queried[0].used_by
    assert "auto_value_pb_inverse" in {spec.factor_id for spec in specs}


def test_anomaly_discovery_validation_rejects_label_leakage() -> None:
    leaked = _feature_panel()
    leaked["label_available_at"] = leaked["available_at"]

    try:
        validate_anomaly_discovery_inputs(leaked, _model_returns())
    except ValueError as exc:
        assert "潜在前视" in str(exc)
    else:
        raise AssertionError("expected label leakage validation failure")
