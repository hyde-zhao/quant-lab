from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.factor_evaluation import (
    MF_REPORT_ARTIFACT_PATH_FORBIDDEN,
    MF_REPORT_ARTIFACT_EXISTS,
    MF_REPORT_CLAIM_UNSUPPORTED,
    MF_REPORT_COST_MISSING,
    MF_REPORT_EXPOSURE_MISSING,
    FactorEvaluationReport,
    build_factor_evaluation_report,
    classify_factor_report_claims,
    resolve_factor_evaluation_report_paths,
    write_factor_evaluation_artifacts,
)
from engine.factor_panel_contracts import (
    MF_AVAILABLE_AT_VIOLATION,
    FactorPanelContract,
    LabelWindowSpec,
    combine_panel_label_gate,
    validate_factor_panel,
    validate_label_window,
)
from engine.multifactor_contracts import FactorRunSpec, PermissionCounters, compute_config_hash


FORBIDDEN_COUNTERS = {
    "external_project_clone": 0,
    "external_project_install": 0,
    "external_project_run": 0,
    "source_migration_or_vendor": 0,
    "dependency_change": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_publish": 0,
    "reports_overwrite": 0,
    "qmt_operation": 0,
    "simulation_or_live": 0,
    "account_or_order_operation": 0,
    "credential_read": 0,
}


def _lineage() -> dict[str, object]:
    return {
        "source_dataset": "research_input_v1",
        "research_input_schema": "research_input_v1",
        "dataset_release": "fixture-release",
        "evidence_refs": ["tests/fixtures/cr030_s04_factor_evaluation"],
    }


def _run_spec() -> FactorRunSpec:
    base = {
        "run_id": "run-cr030-s04-fixture",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "date_range": {"start": "2024-01-01", "end": "2024-01-03"},
        "dataset_release": "research_input_v1_fixture_release",
        "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
        "label_window": {
            "horizon": 1,
            "return_kind": "forward_return",
            "adjustment_policy": "qfq",
        },
        "cost_config": {"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5},
        "seed": 42,
        "code_version": "cr030-s04-fixture",
        "config_hash": "",
        "output_root": "reports/cr030_s04_fixture",
        "permission_counters": PermissionCounters(),
        "failure_policy": "fail_closed",
        "strategy_id": "strategy-cr030-s04-fixture",
        "experiment_group": "cr030-s04",
        "combination_config": {"weighting_policy": "single_factor"},
    }
    base["config_hash"] = compute_config_hash({key: value for key, value in base.items() if key != "config_hash"})
    return FactorRunSpec(**base)


def _panel_row(trade_date: str, symbol: str, value: float) -> FactorPanelContract:
    return FactorPanelContract(
        trade_date=trade_date,
        symbol=symbol,
        factor_id="momentum_20d",
        factor_version="v1",
        raw_value=value,
        directional_value=value,
        winsorized_value=value,
        zscore_value=value,
        available_at=f"{trade_date}T08:30:00",
        decision_time=f"{trade_date}T09:30:00",
        source_dataset="research_input_v1_fixture_release",
        quality_status="pass",
        preprocessing_metadata={"adjustment_policy": "qfq", "winsorize": [0.01, 0.99], "zscore": True},
        data_lineage=_lineage(),
    )


def _label_row(trade_date: str, symbol: str, value: float) -> dict[str, object]:
    label = LabelWindowSpec(
        label_id="forward_return_1d",
        trade_date=trade_date,
        symbol=symbol,
        decision_time=f"{trade_date}T09:30:00",
        label_window_start=f"{trade_date}T10:00:00",
        label_window_end=f"{trade_date}T15:00:00",
        label_available_at=f"{trade_date}T16:00:00",
        return_kind="forward_return",
        adjustment_policy="qfq",
        cost_policy="research_cost_v1",
        benchmark_policy="hs300_required",
        data_lineage=_lineage(),
    ).to_dict()
    label["forward_return"] = value
    return label


def _panel_fixture() -> list[FactorPanelContract]:
    return [
        _panel_row("2024-01-02", "000001.SZ", 0.10),
        _panel_row("2024-01-02", "000002.SZ", 0.20),
        _panel_row("2024-01-02", "000003.SZ", 0.30),
        _panel_row("2024-01-03", "000001.SZ", 0.15),
        _panel_row("2024-01-03", "000002.SZ", 0.05),
        _panel_row("2024-01-03", "000003.SZ", 0.35),
    ]


def _label_fixture() -> list[dict[str, object]]:
    return [
        _label_row("2024-01-02", "000001.SZ", 0.01),
        _label_row("2024-01-02", "000002.SZ", 0.02),
        _label_row("2024-01-02", "000003.SZ", 0.04),
        _label_row("2024-01-03", "000001.SZ", 0.02),
        _label_row("2024-01-03", "000002.SZ", -0.01),
        _label_row("2024-01-03", "000003.SZ", 0.03),
    ]


def _evaluation_config(**overrides: object) -> dict[str, object]:
    base = {
        "run_id": "run-cr030-s04-fixture",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "dataset_release": "research_input_v1_fixture_release",
        "label_window": {"horizon": 1, "return_kind": "forward_return", "adjustment_policy": "qfq"},
        "evaluation_window": {"start": "2024-01-02", "end": "2024-01-03"},
        "rolling_window": 2,
        "quantiles": 3,
        "permission_counters": PermissionCounters(),
        "evidence_refs": ["fixture://cr030-s04/full-input"],
    }
    base.update(overrides)
    return base


def _cost() -> dict[str, object]:
    return {"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5}


def _exposure() -> list[dict[str, object]]:
    return [
        {"symbol": "000001.SZ", "industry": "bank", "market_cap": 100.0, "style_beta": 0.8},
        {"symbol": "000002.SZ", "industry": "real_estate", "market_cap": 80.0, "style_beta": 1.1},
        {"symbol": "000003.SZ", "industry": "industrial", "market_cap": 120.0, "style_beta": 0.9},
    ]


def _production_claim_count(report: FactorEvaluationReport) -> int:
    return report.production_valid_claim_count


def test_ts_s04_01_complete_input_builds_full_factor_evaluation_report() -> None:
    report = build_factor_evaluation_report(
        _panel_fixture(),
        _label_fixture(),
        benchmark={"benchmark_id": "hs300", "policy": "hs300_required"},
        cost=_cost(),
        exposure=_exposure(),
        evaluation_config=_evaluation_config(),
    )

    assert report.status == "pass"
    assert report.coverage["observations"] == 6
    assert report.IC["status"] == "pass"
    assert report.RankIC["status"] == "pass"
    assert report.ICIR["status"] in {"pass", "warn"}
    assert report.quantile_returns["status"] == "pass"
    assert report.long_short_returns["status"] == "pass"
    assert report.turnover["status"] in {"pass", "warn"}
    assert report.cost_sensitivity["status"] == "pass"
    assert report.exposure_summary["status"] == "pass"
    assert "2024" in report.annual_breakdown
    assert report.rolling_breakdown["status"] == "pass"
    assert {claim.claim for claim in report.allowed_claims} == {"single_factor_research_evidence"}
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready"} <= {
        claim.claim for claim in report.blocked_claims
    }
    assert _production_claim_count(report) == 0
    json.dumps(report.to_dict(), sort_keys=True)


def test_ts_s04_02_s03_gate_fail_outputs_blocked_and_zero_production_claims() -> None:
    bad_panel = _panel_row("2024-01-02", "000001.SZ", 0.10).to_dict()
    bad_panel["available_at"] = "2024-01-02T10:00:00"
    panel_result = validate_factor_panel(bad_panel, _run_spec())
    label_result = validate_label_window(_label_row("2024-01-02", "000001.SZ", 0.01), _run_spec())
    gate_result = combine_panel_label_gate(panel_result, label_result)

    report = build_factor_evaluation_report(
        [bad_panel],
        [_label_row("2024-01-02", "000001.SZ", 0.01)],
        cost=_cost(),
        exposure=_exposure(),
        evaluation_config=_evaluation_config(gate_result=gate_result),
    )

    assert report.status == "blocked"
    assert report.allowed_claims == ()
    assert _production_claim_count(report) == 0
    assert MF_AVAILABLE_AT_VIOLATION in {claim.code for claim in report.blocked_claims}
    assert {"production_valid", "qmt_ready", "simulation_ready", "live_ready"} <= {
        claim.claim for claim in report.blocked_claims
    }


def test_ts_s04_03_missing_exposure_or_cost_is_research_limited_with_blocked_claims() -> None:
    missing_cost = build_factor_evaluation_report(
        _panel_fixture(),
        _label_fixture(),
        benchmark={"benchmark_id": "hs300"},
        cost=None,
        exposure=_exposure(),
        evaluation_config=_evaluation_config(),
    )
    missing_exposure = build_factor_evaluation_report(
        _panel_fixture(),
        _label_fixture(),
        benchmark={"benchmark_id": "hs300"},
        cost=_cost(),
        exposure=None,
        evaluation_config=_evaluation_config(),
    )

    assert missing_cost.status == "research_limited"
    assert MF_REPORT_COST_MISSING in {claim.code for claim in missing_cost.blocked_claims}
    assert _production_claim_count(missing_cost) == 0
    assert missing_exposure.status == "research_limited"
    assert MF_REPORT_EXPOSURE_MISSING in {claim.code for claim in missing_exposure.blocked_claims}
    assert _production_claim_count(missing_exposure) == 0


def test_ts_s04_04_single_full_sample_metric_cannot_create_production_claim() -> None:
    report = {
        "status": "pass",
        "IC": {"value": 0.12, "status": "pass"},
        "long_short_returns": {"value": 0.03, "status": "pass"},
        "annual_breakdown": {},
        "rolling_breakdown": {"series": []},
        "cost_sensitivity": {"status": "pass"},
        "exposure_summary": {"status": "pass"},
        "allowed_claims": [{"claim": "production-valid by single full sample IC"}],
        "blocked_claims": [],
        "evidence_refs": ["fixture://single-full-sample"],
    }

    allowed, blocked = classify_factor_report_claims(report)

    assert all("production" not in claim.claim and "ready" not in claim.claim for claim in allowed)
    assert MF_REPORT_CLAIM_UNSUPPORTED in {claim.code for claim in blocked}
    assert "production_valid_from_single_full_sample_metric" in {claim.claim for claim in blocked}
    assert {"production-valid by single full sample IC", "qmt_ready", "simulation_ready", "live_ready"} <= {
        claim.claim for claim in blocked
    }


def test_ts_s04_05_artifact_paths_are_versioned_and_do_not_overwrite_old_reports(tmp_path: Path) -> None:
    old_report = tmp_path / "reports" / "experiment_17_21" / "summary.md"
    old_report.parent.mkdir(parents=True)
    old_report.write_text("old report must stay unchanged", encoding="utf-8")

    report = build_factor_evaluation_report(
        _panel_fixture(),
        _label_fixture(),
        benchmark={"benchmark_id": "hs300"},
        cost=_cost(),
        exposure=_exposure(),
        evaluation_config=_evaluation_config(report_id="report-cr030-s04-fixture"),
    )
    paths = resolve_factor_evaluation_report_paths(report.report_id, tmp_path)
    write_result = write_factor_evaluation_artifacts(report, paths)

    assert write_result.status == "pass"
    assert "/reports/factor_evaluation/v1/" in paths.json_path.as_posix()
    assert paths.json_path.exists()
    assert paths.metrics_csv_path.exists()
    assert paths.markdown_path.exists()
    assert old_report.read_text(encoding="utf-8") == "old report must stay unchanged"

    second_write = write_factor_evaluation_artifacts(report, paths)
    assert second_write.status == "blocked"
    assert MF_REPORT_ARTIFACT_EXISTS in {reason.code for reason in second_write.blocked_reasons}

    with pytest.raises(ValueError, match=MF_REPORT_ARTIFACT_PATH_FORBIDDEN):
        resolve_factor_evaluation_report_paths(report.report_id, tmp_path / "reports" / "experiment_17_21")


def test_ts_s04_06_forbidden_operation_counters_and_runtime_import_boundary_are_zero() -> None:
    report = build_factor_evaluation_report(
        _panel_fixture(),
        _label_fixture(),
        benchmark={"benchmark_id": "hs300"},
        cost=_cost(),
        exposure=_exposure(),
        evaluation_config=_evaluation_config(permission_counters=FORBIDDEN_COUNTERS),
    )
    source = Path("engine/factor_evaluation.py").read_text(encoding="utf-8").lower()

    assert dict(report.permission_counters) == FORBIDDEN_COUNTERS
    assert all(value == 0 for value in report.permission_counters.values())
    assert "alphalens" in source
    assert "import alphalens" not in source
    assert "qlib" in source
    assert "import qlib" not in source
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "requests." not in source
    assert "urllib" not in source
    assert ".env" not in source
