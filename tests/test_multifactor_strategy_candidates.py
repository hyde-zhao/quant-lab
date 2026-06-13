from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from engine.multifactor_strategy_candidates import FORBIDDEN_OPERATION_COUNTS, run_strategy_research
from scripts.run_multifactor_strategy_candidates import run_strategy_candidates_from_paths


def _portfolio_payload(simulation_candidate: bool = False) -> dict[str, object]:
    row = {
        "schema_version": "chapter7_portfolio_admission_summary_v1",
        "run_id": "run-cr038-fixture",
        "portfolio_id": "equal_weight_baseline",
        "admission": "research_candidate",
        "simulation_candidate": simulation_candidate,
        "gross_mean_return": 0.02,
        "net_mean_return_25bps": 0.018,
        "mean_turnover": 0.4,
        "max_drawdown_proxy": -0.12,
        "capacity_evidence": "proxy_available",
        "not_authorization": True,
        "allowed_assets": [{"asset_type": "factor", "asset_id": "value_bm", "admission": "baseline", "weight": 1.0}],
        "watch_assets_policy": [{"asset_type": "factor", "asset_id": "momentum_12_1", "admission": "watch", "weight": 0.2}],
        "rejected_assets_excluded": [{"asset_type": "factor", "asset_id": "market_beta_252", "admission": "reject", "weight": 0.1}],
    }
    return {
        "schema_version": "chapter7_portfolio_admission_payload_v1",
        "not_authorization": True,
        "blocked_claims": [],
        "samples": [
            {
                "sample_id": "fixture",
                "status": "PASS",
                "allowed_assets": row["allowed_assets"],
                "watch_assets_policy": row["watch_assets_policy"],
                "rejected_assets_excluded": row["rejected_assets_excluded"],
                "portfolio_admission_summary": [row],
            }
        ],
        "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
    }


def _upstream_summaries() -> dict[str, dict[str, object]]:
    return {
        "cr035_model_admission": {
            "schema_version": "chapter4_model_admission_summary_v1",
            "not_authorization": True,
            "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
            "samples": [{"sample_id": "fixture", "status": "PASS", "model_admission_summary": []}],
        },
        "cr036_anomaly_admission": {
            "schema_version": "chapter5_anomaly_admission_summary_v1",
            "not_authorization": True,
            "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
            "samples": [{"sample_id": "fixture", "status": "PASS", "anomaly_admission_summary": [], "gap_register": []}],
        },
        "cr037_robustness_admission": {
            "schema_version": "chapter6_robustness_admission_summary_v1",
            "not_authorization": True,
            "operation_counts": dict(FORBIDDEN_OPERATION_COUNTS),
            "samples": [{"sample_id": "fixture", "status": "PASS", "robustness_admission_summary": []}],
        },
    }


def _frames() -> dict[str, pd.DataFrame]:
    dates = ["2014-12-31", "2016-12-30", "2021-12-31"]
    samples = ["in_sample_2000_2019", "in_sample_2000_2019", "observation_2020_2026_ytd"]
    metrics = pd.DataFrame(
        {
            "schema_version": ["chapter7_portfolio_metrics_v1"] * 3,
            "trade_date": dates,
            "portfolio_id": ["equal_weight_baseline"] * 3,
            "gross_return": [0.04, 0.03, 0.02],
            "turnover": [0.5, 0.3, 0.2],
            "holding_count": [20, 20, 20],
            "max_weight": [0.05, 0.05, 0.05],
            "missing_return_count": [0, 0, 0],
            "cum_gross_return": [0.04, 0.0712, 0.0926],
            "sample_id": samples,
        }
    )
    costs = pd.DataFrame(
        {
            "schema_version": ["chapter7_turnover_cost_analysis_v1"] * 3,
            "trade_date": dates,
            "portfolio_id": ["equal_weight_baseline"] * 3,
            "cost_bps": [25.0, 25.0, 25.0],
            "gross_return": [0.04, 0.03, 0.02],
            "turnover": [0.5, 0.3, 0.2],
            "cost_drag": [0.00125, 0.00075, 0.0005],
            "net_return": [0.03875, 0.02925, 0.0195],
            "cum_net_return": [0.03875, 0.0691, 0.0899],
            "sample_id": samples,
        }
    )
    capacity = pd.DataFrame(
        {
            "schema_version": ["chapter7_capacity_liquidity_analysis_v1"] * 3,
            "trade_date": dates,
            "portfolio_id": ["equal_weight_baseline"] * 3,
            "holding_count": [20, 20, 20],
            "max_single_name_weight": [0.05, 0.05, 0.05],
            "low_liquidity_proxy_weight": [0.0, 0.01, 0.02],
            "small_cap_proxy_weight": [0.1, 0.1, 0.1],
            "capacity_status": ["PASS", "PASS", "PASS"],
            "capacity_proxy": ["fixture"] * 3,
            "sample_id": samples,
        }
    )
    risk = pd.DataFrame(
        {
            "schema_version": ["chapter7_risk_exposure_v1"] * 3,
            "trade_date": dates,
            "portfolio_id": ["equal_weight_baseline"] * 3,
            "risk_factor": ["value_bm"] * 3,
            "weighted_exposure": [0.2, 0.1, -0.1],
            "absolute_exposure": [0.2, 0.1, 0.1],
            "missing_exposure_count": [0, 0, 0],
            "sample_id": samples,
        }
    )
    attribution = pd.DataFrame(
        {
            "schema_version": ["chapter7_performance_attribution_v1"] * 3,
            "trade_date": dates,
            "portfolio_id": ["equal_weight_baseline"] * 3,
            "risk_factor": ["value_bm"] * 3,
            "weighted_exposure": [0.2, 0.1, -0.1],
            "attribution_proxy": [0.004, 0.002, -0.001],
            "method": ["fixture"] * 3,
            "sample_id": samples,
        }
    )
    scores = pd.DataFrame(
        {
            "schema_version": ["chapter7_alpha_scores_v1"] * 3,
            "run_id": ["run-cr038-fixture"] * 3,
            "sample_id": samples,
            "trade_date": dates,
            "symbol": ["000001.SZ", "000002.SZ", "000003.SZ"],
            "alpha_score": [1.0, 0.8, 0.6],
            "source_admission": ["value_bm"] * 3,
        }
    )
    return {
        "portfolio_metrics": metrics,
        "turnover_cost_analysis": costs,
        "capacity_liquidity_analysis": capacity,
        "risk_exposure": risk,
        "performance_attribution": attribution,
        "alpha_scores": scores,
    }


def test_cr039_research_blocks_runtime_claims_when_cr038_is_not_simulation_candidate() -> None:
    frames = _frames()

    result = run_strategy_research(
        run_id="run-cr039-fixture",
        upstream_research_summaries=_upstream_summaries(),
        portfolio_admission_payload=_portfolio_payload(simulation_candidate=False),
        input_refs={"fixture": "local"},
        **frames,
    )

    assert result.status == "PASS"
    assert result.strategy_candidates
    assert {item.admission for item in result.strategy_candidates} == {"research_baseline"}
    assert all(item.simulation_candidate is False for item in result.strategy_candidates)
    assert result.admission_package["not_authorization"] is True
    assert result.admission_package["not_simulation_authorization"] is True
    assert result.admission_package["operation_counts"] == FORBIDDEN_OPERATION_COUNTS
    assert {"in_sample_2000_2014", "validation_2015_2019", "out_of_sample_2020_2026_ytd"} <= set(result.risk_cost_summary["evaluation_window"])
    assert {"simulation_ready", "qmt_ready", "live_ready"} <= {item["claim"] for item in result.admission_package["blocked_claims"]}


def test_cr039_blocks_nonzero_upstream_operation_counts() -> None:
    payload = _portfolio_payload()
    payload["operation_counts"] = {**FORBIDDEN_OPERATION_COUNTS, "provider_fetch": 1}

    with pytest.raises(RuntimeError, match="operation_counts"):
        run_strategy_research(
            run_id="run-cr039-fixture",
            upstream_research_summaries=_upstream_summaries(),
            portfolio_admission_payload=payload,
            input_refs={},
            **_frames(),
        )


def test_cr039_blocks_missing_operation_count_fields_in_upstream_summary() -> None:
    upstream = _upstream_summaries()
    counts = dict(FORBIDDEN_OPERATION_COUNTS)
    counts.pop("simulation_or_live")
    upstream["cr035_model_admission"]["operation_counts"] = counts

    with pytest.raises(RuntimeError, match="字段必须与 FORBIDDEN_OPERATION_COUNTERS 完全一致"):
        run_strategy_research(
            run_id="run-cr039-fixture",
            upstream_research_summaries=upstream,
            portfolio_admission_payload=_portfolio_payload(),
            input_refs={},
            **_frames(),
        )


def test_cr039_missing_cost_or_capacity_evidence_is_blocked_missing_evidence() -> None:
    frames = _frames()
    frames["capacity_liquidity_analysis"] = pd.DataFrame()

    result = run_strategy_research(
        run_id="run-cr039-fixture",
        upstream_research_summaries=_upstream_summaries(),
        portfolio_admission_payload=_portfolio_payload(),
        input_refs={"fixture": "local"},
        **frames,
    )

    assert result.status == "BLOCKED"
    assert result.admission_package["overall_admission"] == "blocked_missing_evidence"
    assert result.admission_package["blocked_reasons"][0]["code"] == "CR039_BLOCKED_MISSING_EVIDENCE"
    assert result.admission_package["operation_counts"] == FORBIDDEN_OPERATION_COUNTS


def test_cr039_runner_writes_artifacts_from_local_cr038_paths(tmp_path: Path) -> None:
    frames = _frames()
    chapter7_report_root = tmp_path / "reports" / "chapter7_factor_practice"
    chapter7_process_root = tmp_path / "process" / "chapter7_factor_practice"
    cr038_run_id = "run-cr038-fixture"
    report_dir = chapter7_report_root / cr038_run_id
    process_dir = chapter7_process_root / cr038_run_id
    report_dir.mkdir(parents=True)
    process_dir.mkdir(parents=True)

    frames["alpha_scores"].to_parquet(report_dir / "alpha_scores.parquet", index=False)
    frames["portfolio_metrics"].to_csv(report_dir / "portfolio_metrics.csv", index=False)
    frames["turnover_cost_analysis"].to_csv(report_dir / "turnover_cost_analysis.csv", index=False)
    frames["capacity_liquidity_analysis"].to_csv(report_dir / "capacity_liquidity_analysis.csv", index=False)
    frames["risk_exposure"].to_csv(report_dir / "risk_exposure.csv", index=False)
    frames["performance_attribution"].to_csv(report_dir / "performance_attribution.csv", index=False)
    (process_dir / "PORTFOLIO-ADMISSION-SUMMARY.json").write_text(
        json.dumps(_portfolio_payload(), ensure_ascii=False),
        encoding="utf-8",
    )
    upstream = _upstream_summaries()
    cr035_path = tmp_path / "MODEL-ADMISSION-SUMMARY.json"
    cr036_path = tmp_path / "ANOMALY-ADMISSION-SUMMARY.json"
    cr037_path = tmp_path / "ROBUSTNESS-ADMISSION-SUMMARY.json"
    cr035_path.write_text(json.dumps(upstream["cr035_model_admission"], ensure_ascii=False), encoding="utf-8")
    cr036_path.write_text(json.dumps(upstream["cr036_anomaly_admission"], ensure_ascii=False), encoding="utf-8")
    cr037_path.write_text(json.dumps(upstream["cr037_robustness_admission"], ensure_ascii=False), encoding="utf-8")

    result = run_strategy_candidates_from_paths(
        run_id="run-cr039-fixture",
        output_root=tmp_path / "process" / "cr039",
        report_root=tmp_path / "reports" / "cr039",
        cr038_run_id=cr038_run_id,
        cr035_model_admission_summary=cr035_path,
        cr036_anomaly_admission_summary=cr036_path,
        cr037_robustness_admission_summary=cr037_path,
        chapter7_report_root=chapter7_report_root,
        chapter7_process_root=chapter7_process_root,
    )

    assert result.status == "PASS"
    assert result.artifacts.strategy_scores_path.exists()
    assert result.artifacts.backtest_results_path.exists()
    assert result.artifacts.factor_contribution_path.exists()
    assert result.artifacts.risk_cost_summary_path.exists()
    assert result.artifacts.report_md_path.exists()
    assert result.artifacts.admission_package_path.exists()
    package = json.loads(result.artifacts.admission_package_path.read_text(encoding="utf-8"))
    assert package["schema_version"] == "multifactor_strategy_admission_package_v1"
    assert package["not_qmt_authorization"] is True
    assert package["not_simulation_authorization"] is True
    assert all(item["simulation_candidate"] is False for item in package["strategy_candidates"])
