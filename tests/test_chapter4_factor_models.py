from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from engine.chapter4_factor_models import (
    DEFAULT_CHAPTER4_MODELS,
    FORBIDDEN_OPERATION_COUNTS,
    run_chapter4_analysis,
    validate_chapter4_inputs,
)
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS
from scripts.run_chapter4_factor_models import (
    assert_chapter3_report_pass,
    read_label_parts,
    run_chapter4_from_paths,
)


def _panel_and_labels(periods: int = 18, symbols: int = 40) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2020-01-31", periods=periods, freq="ME").date
    symbol_list = [f"{index + 1:06d}.SZ" for index in range(symbols)]
    panel_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    for date_index, trade_date in enumerate(dates):
        day = trade_date.isoformat()
        next_day = (pd.Timestamp(trade_date) + pd.offsets.MonthEnd(1)).date().isoformat()
        for symbol_index, symbol in enumerate(symbol_list):
            base = (symbol_index - symbols / 2) / symbols
            factor_values = {
                "market_beta_252": 0.1 * np.sin(symbol_index),
                "size_total_market_cap": -base,
                "value_bm": base * 0.8,
                "momentum_12_1": base * 0.5 + date_index * 0.01,
                "profitability_roe_ttm": base * 0.6,
                "investment_asset_growth": -base * 0.4,
                "abnormal_turnover_21_252": -base * 0.3,
            }
            for factor_id, zscore in factor_values.items():
                panel_rows.append(
                    {
                        "trade_date": day,
                        "symbol": symbol,
                        "factor_id": factor_id,
                        "zscore_value": float(zscore),
                        "available_at": f"{day}T16:30:00+08:00",
                        "run_id": "run-chapter3-fixture",
                        "data_lineage": "fixture",
                    }
                )
            label_rows.append(
                {
                    "trade_date": day,
                    "symbol": symbol,
                    "forward_return": 0.01 + 0.03 * base + 0.01 * factor_values["value_bm"] - 0.005 * date_index / periods,
                    "label_available_at": f"{next_day}T16:30:00+08:00",
                }
            )
    return pd.DataFrame(panel_rows), pd.DataFrame(label_rows)


def test_chapter4_analysis_builds_pricing_and_model_outputs() -> None:
    panel, labels = _panel_and_labels()

    result = run_chapter4_analysis(
        panel,
        labels,
        run_id="run-cr035-fixture",
        sample_id="fixture",
        min_cross_section=20,
        quantiles=5,
    )

    assert result.status == "PASS"
    assert set(result.factor_ids) == set(DEFAULT_EQUITY_CORE_FACTOR_IDS)
    assert set(result.model_ids) == {model.model_id for model in DEFAULT_CHAPTER4_MODELS}
    assert not result.fama_macbeth_results.empty
    assert not result.factor_model_returns.empty
    assert not result.model_comparison.empty
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready"} <= {
        item["claim"] for item in result.blocked_claims
    }


def test_chapter4_validation_rejects_missing_factor_and_label_leakage() -> None:
    panel, labels = _panel_and_labels()
    missing = panel[panel["factor_id"] != "value_bm"].copy()
    with pytest.raises(ValueError, match="缺少因子"):
        validate_chapter4_inputs(missing, labels)

    leaked = labels.copy()
    leaked["label_available_at"] = leaked["trade_date"].map(lambda value: f"{value}T15:00:00+08:00")
    with pytest.raises(ValueError, match="潜在前视"):
        validate_chapter4_inputs(panel, leaked)


def test_chapter4_runner_writes_artifacts_from_local_paths(tmp_path: Path) -> None:
    panel, labels = _panel_and_labels()
    panel_path = tmp_path / "panel.parquet"
    label_root = tmp_path / "label_parts"
    report_path = tmp_path / "EMPIRICAL-RUN-REPORT.json"
    label_root.mkdir()
    panel.to_parquet(panel_path, index=False)
    labels.to_parquet(label_root / "labels_2020.parquet", index=False)
    report_path.write_text(json.dumps({"status": "PASS", "limitations": []}), encoding="utf-8")

    result = run_chapter4_from_paths(
        (
            {
                "sample_id": "fixture",
                "panel_path": str(panel_path),
                "label_root": str(label_root),
                "report_path": str(report_path),
            },
        ),
        run_id="run-cr035-fixture",
        output_root=tmp_path / "process",
        report_root=tmp_path / "reports",
        min_cross_section=20,
        quantiles=5,
    )

    assert result.status == "PASS"
    assert result.artifacts.fama_macbeth_results_path.exists()
    assert result.artifacts.factor_model_returns_path.exists()
    assert result.artifacts.model_comparison_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    assert len(read_label_parts(label_root)) == len(labels)


def test_chapter4_runner_blocks_non_pass_or_limited_chapter3_report(tmp_path: Path) -> None:
    report_path = tmp_path / "EMPIRICAL-RUN-REPORT.json"
    report_path.write_text(json.dumps({"status": "PASS", "limitations": ["limited"]}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="limitations"):
        assert_chapter3_report_pass(report_path)

    assert_chapter3_report_pass(report_path, allow_limitations=True)
