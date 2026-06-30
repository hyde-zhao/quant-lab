from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from engine.factor_portfolio_practice import (
    FORBIDDEN_OPERATION_COUNTS,
    Chapter7Config,
    parse_robustness_admission,
    run_chapter7_analysis,
    validate_chapter7_inputs,
)
from scripts.research.run_factor_practice import assert_robustness_admission_summary_usable, run_chapter7_from_paths
from tests.research.test_factor_models import _panel_and_labels


def _robustness_admission(sample_id: str = "fixture") -> dict[str, object]:
    return {
        "schema_version": "chapter6_robustness_admission_summary_v1",
        "not_authorization": True,
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
        "samples": [
            {
                "sample_id": sample_id,
                "status": "PASS",
                "robustness_admission_summary": [
                    {
                        "asset_type": "factor",
                        "asset_id": "size_total_market_cap",
                        "admission": "baseline",
                        "mean_long_short_return": 0.012,
                        "mean_rank_ic": 0.04,
                        "t_stat": 3.1,
                        "reason": "fixture baseline",
                    },
                    {
                        "asset_type": "factor",
                        "asset_id": "value_bm",
                        "admission": "candidate",
                        "mean_long_short_return": 0.008,
                        "mean_rank_ic": 0.03,
                        "t_stat": 2.2,
                        "reason": "fixture candidate",
                    },
                    {
                        "asset_type": "factor",
                        "asset_id": "momentum_12_1",
                        "admission": "watch",
                        "mean_long_short_return": 0.001,
                        "mean_rank_ic": 0.0,
                        "t_stat": 0.1,
                        "reason": "fixture watch",
                    },
                    {
                        "asset_type": "factor",
                        "asset_id": "investment_asset_growth",
                        "admission": "reject",
                        "mean_long_short_return": -0.003,
                        "mean_rank_ic": -0.01,
                        "t_stat": -1.2,
                        "reason": "fixture reject",
                    },
                ],
            }
        ],
    }


def test_chapter7_analysis_builds_portfolio_practice_outputs() -> None:
    panel, labels = _panel_and_labels(periods=18, symbols=45)

    result = run_chapter7_analysis(
        panel,
        labels,
        _robustness_admission(),
        run_id="run-cr038-fixture",
        sample_id="fixture",
        config=Chapter7Config(top_n=10, min_cross_section=20, max_weight=0.2, capacity_weight_limit=0.25),
    )

    assert result.status == "PASS"
    assert {asset.asset_id for asset in result.allowed_assets} == {"size_total_market_cap", "value_bm"}
    assert {asset.asset_id for asset in result.watch_assets} == {"momentum_12_1"}
    assert {asset.asset_id for asset in result.rejected_assets} == {"investment_asset_growth"}
    assert not result.alpha_scores.empty
    assert not result.optimized_portfolios.empty
    assert set(result.optimized_portfolios["portfolio_id"].unique()) == {"equal_weight_baseline", "risk_adjusted_constrained"}
    assert not result.portfolio_metrics.empty
    assert not result.risk_exposure.empty
    assert not result.performance_attribution.empty
    assert not result.turnover_cost_analysis.empty
    assert not result.capacity_liquidity_analysis.empty
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    assert set(result.turnover_cost_analysis["cost_bps"].unique()) == {0.0, 10.0, 25.0, 50.0}
    assert {"gross_return", "net_return", "turnover", "cost_drag"} <= set(result.turnover_cost_analysis.columns)
    assert {"holding_count", "max_single_name_weight", "capacity_status", "capacity_proxy"} <= set(result.capacity_liquidity_analysis.columns)
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready", "provider_or_lake_publish_ready"} <= {
        item["claim"] for item in result.blocked_claims
    }
    assert all(row["simulation_candidate"] is False for row in result.portfolio_admission_summary)
    assert all(row["not_authorization"] is True for row in result.portfolio_admission_summary)


def test_chapter7_admission_parser_excludes_watch_and_reject_from_allowed_assets() -> None:
    allowed, watch, rejected = parse_robustness_admission(_robustness_admission(), sample_id="fixture")

    assert {item.asset_id for item in allowed} == {"size_total_market_cap", "value_bm"}
    assert {item.asset_id for item in watch} == {"momentum_12_1"}
    assert {item.asset_id for item in rejected} == {"investment_asset_growth"}
    assert pytest.approx(sum(item.weight for item in allowed)) == 1.0


def test_chapter7_validation_rejects_missing_admission_and_label_leakage() -> None:
    panel, labels = _panel_and_labels()
    with pytest.raises(ValueError, match="robustness admission"):
        validate_chapter7_inputs(panel, labels, {})

    leaked = labels.copy()
    leaked["label_available_at"] = leaked["trade_date"].map(lambda value: f"{value}T15:00:00+08:00")
    with pytest.raises(ValueError, match="潜在前视"):
        validate_chapter7_inputs(panel, leaked, _robustness_admission())


def test_chapter7_blocks_when_no_baseline_or_candidate_asset() -> None:
    panel, labels = _panel_and_labels()
    admission = _robustness_admission()
    rows = admission["samples"][0]["robustness_admission_summary"]  # type: ignore[index]
    for row in rows:  # type: ignore[union-attr]
        row["admission"] = "reject"

    with pytest.raises(ValueError, match="baseline/candidate"):
        run_chapter7_analysis(panel, labels, admission, run_id="run-cr038-fixture", sample_id="fixture")


def test_chapter7_runner_writes_artifacts_from_local_paths(tmp_path: Path) -> None:
    panel, labels = _panel_and_labels(periods=18, symbols=45)
    panel_path = tmp_path / "panel.parquet"
    label_root = tmp_path / "label_parts"
    chapter3_report_path = tmp_path / "EMPIRICAL-RUN-REPORT.json"
    admission_path = tmp_path / "ROBUSTNESS-ADMISSION-SUMMARY.json"
    label_root.mkdir()
    panel.to_parquet(panel_path, index=False)
    labels.to_parquet(label_root / "labels_2020.parquet", index=False)
    chapter3_report_path.write_text(json.dumps({"status": "PASS", "limitations": []}), encoding="utf-8")
    admission_path.write_text(json.dumps(_robustness_admission(), ensure_ascii=False), encoding="utf-8")

    result = run_chapter7_from_paths(
        (
            {
                "sample_id": "fixture",
                "panel_path": str(panel_path),
                "label_root": str(label_root),
                "chapter3_report_path": str(chapter3_report_path),
                "robustness_admission_summary_path": str(admission_path),
            },
        ),
        run_id="run-cr038-fixture",
        output_root=tmp_path / "process",
        report_root=tmp_path / "reports",
        min_cross_section=20,
        top_fraction=0.25,
        max_weight=0.2,
    )

    assert result.status == "PASS"
    assert result.artifacts.alpha_scores_path.exists()
    assert result.artifacts.optimized_portfolios_path.exists()
    assert result.artifacts.portfolio_metrics_path.exists()
    assert result.artifacts.risk_exposure_path.exists()
    assert result.artifacts.performance_attribution_path.exists()
    assert result.artifacts.turnover_cost_analysis_path.exists()
    assert result.artifacts.capacity_liquidity_analysis_path.exists()
    assert result.artifacts.portfolio_admission_summary_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.operation_counts == FORBIDDEN_OPERATION_COUNTS
    summary = json.loads(result.artifacts.portfolio_admission_summary_path.read_text(encoding="utf-8"))
    assert summary["schema_version"] == "chapter7_portfolio_admission_payload_v1"
    assert summary["not_authorization"] is True
    assert summary["operation_counts"] == FORBIDDEN_OPERATION_COUNTS
    assert summary["samples"][0]["allowed_assets"]
    assert summary["samples"][0]["rejected_assets_excluded"]
    assert summary["samples"][0]["portfolio_admission_summary"]
    metrics = pd.read_csv(result.artifacts.portfolio_metrics_path)
    costs = pd.read_csv(result.artifacts.turnover_cost_analysis_path)
    capacity = pd.read_csv(result.artifacts.capacity_liquidity_analysis_path)
    assert {"gross_return", "turnover", "cum_gross_return"} <= set(metrics.columns)
    assert {"gross_return", "net_return", "turnover", "cost_bps"} <= set(costs.columns)
    assert {"holding_count", "capacity_status", "capacity_proxy"} <= set(capacity.columns)


def test_chapter7_runner_blocks_nonzero_cr037_operation_counts() -> None:
    summary = _robustness_admission()
    summary["operation_counts"] = {**FORBIDDEN_OPERATION_COUNTS, "provider_fetch": 1}

    with pytest.raises(RuntimeError, match="operation_counts"):
        assert_robustness_admission_summary_usable(summary)
