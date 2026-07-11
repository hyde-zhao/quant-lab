from __future__ import annotations

import json

from engine.admission_contracts import AdmissionStatus
from engine.experiment_family_lineage import (
    ExperimentFamilyManifest,
    FamilyLineageValidationResult,
    LineageAvailability,
    ValidationStatus,
)
from engine.strategy_admission_package import (
    attach_statistical_gate_to_admission_package,
    map_statistical_gate_status_to_admission_status,
)
from engine.strategy_admission_statistical_gate import (
    BacktestOverfitRiskReport,
    MultipleTestingReport,
    RobustFactorStatisticsReport,
    StatisticalGateStatus,
    ValidationBoundFamilyEvidence,
    WalkForwardValidationPlan,
    default_statistical_gate_thresholds,
    evaluate_strategy_admission_statistical_gate,
    validate_multiple_testing_report,
    validate_walk_forward_plan,
)


def _multiple_testing_report() -> MultipleTestingReport:
    return MultipleTestingReport(
        family_id="cr151-factor-family",
        candidate_count=3,
        raw_p_values=(0.01, 0.04, 0.2),
        adjusted_p_values=(0.03, 0.04, 0.2),
        alpha=0.05,
        method="BH",
        rejected_count=2,
        report_ref="artifact://cr151/multiple-testing.json",
    )


def _robust_report(sample_count: int = 64) -> RobustFactorStatisticsReport:
    return RobustFactorStatisticsReport(
        metric_id="rank_ic",
        sample_count=sample_count,
        ic_mean=0.035,
        rank_ic_mean=0.042,
        robust_t_stat=2.4,
        p_value=0.02,
        autocorrelation_lags=(1, 5, 10),
        report_ref="artifact://cr151/robust-stats.json",
    )


def _walk_forward_plan(passed: tuple[bool, ...] = (True, True, True)) -> WalkForwardValidationPlan:
    return WalkForwardValidationPlan(
        folds=len(passed),
        train_window="504d",
        validation_window="126d",
        oos_window="63d",
        embargo_days=5,
        fold_metrics=tuple({"fold_id": index + 1, "passed": value} for index, value in enumerate(passed)),
        report_ref="artifact://cr151/walk-forward.json",
    )


def _overfit_report() -> BacktestOverfitRiskReport:
    return BacktestOverfitRiskReport(
        trial_count=12,
        pbo=0.12,
        dsr=0.45,
        observed_sharpe=1.25,
        skew=0.1,
        kurtosis=3.1,
        sample_length=756,
        report_ref="artifact://cr151/overfit-risk.json",
    )


def _trusted_family_lineage() -> ValidationBoundFamilyEvidence:
    manifest = ExperimentFamilyManifest(
        schema_version=1,
        family_id="cr151-factor-family",
        manifest_version=1,
        spec_ref="fixture://cr151/lineage/spec",
        events_ref="fixture://cr151/lineage/events",
        sealed_event_count=12,
        sealed_last_sequence=12,
        raw_trial_count=12,
        trial_ids=tuple(f"trial-{index:02d}" for index in range(12)),
        seal_hash="sha256:cr151-trusted-lineage",
        sealed_at="2026-07-11T00:00:00Z",
    )
    validation = FamilyLineageValidationResult(
        schema_version=1,
        validation_id="validation-cr151-trusted-lineage",
        target_ref="fixture://cr151/lineage/manifest-v1",
        target_hash=manifest.seal_hash,
        availability=LineageAvailability.PRESENT,
        validation_status=ValidationStatus.PASS,
        recomputed_raw_trial_count=manifest.raw_trial_count,
        declared_raw_trial_count=manifest.raw_trial_count,
    )
    return ValidationBoundFamilyEvidence(manifest, validation)


def test_cr151_contracts_are_json_serializable_and_deterministic() -> None:
    report = _multiple_testing_report()

    assert report.to_dict() == report.to_dict()
    assert report.to_dict()["family_id"] == "cr151-factor-family"
    json.dumps(report.to_dict(), sort_keys=True)


def test_cr151_walk_forward_validation_blocks_missing_oos_folds() -> None:
    issues = validate_walk_forward_plan(
        WalkForwardValidationPlan(
            folds=0,
            train_window="",
            validation_window="126d",
            oos_window="",
            embargo_days=0,
            fold_metrics=(),
        )
    )

    assert {issue.code for issue in issues} >= {
        "statistical_walk_forward_folds_invalid",
        "statistical_walk_forward_fold_metrics_missing",
    }


def test_cr151_multiple_testing_validation_blocks_inconsistent_counts() -> None:
    issues = validate_multiple_testing_report(
        MultipleTestingReport(
            family_id="cr151-factor-family",
            candidate_count=3,
            raw_p_values=(0.01,),
            adjusted_p_values=(0.02,),
            alpha=0.05,
            method="BH",
            rejected_count=4,
        )
    )

    assert {issue.code for issue in issues} >= {
        "statistical_multiple_testing_raw_p_value_count_mismatch",
        "statistical_multiple_testing_adjusted_p_value_count_mismatch",
        "statistical_multiple_testing_rejected_count_exceeds_candidates",
    }


def test_cr151_evaluator_blocks_inconsistent_multiple_testing_counts() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=MultipleTestingReport(
            family_id="cr151-factor-family",
            candidate_count=3,
            raw_p_values=(0.01,),
            adjusted_p_values=(0.02,),
            alpha=0.05,
            method="BH",
            rejected_count=1,
        ),
        robust_statistics_report=_robust_report(),
        walk_forward_plan=_walk_forward_plan(),
        overfit_risk_report=_overfit_report(),
    )

    assert gate.status is StatisticalGateStatus.BLOCKED
    assert {reason.code for reason in gate.blocked_reasons} >= {
        "statistical_multiple_testing_raw_p_value_count_mismatch",
        "statistical_multiple_testing_adjusted_p_value_count_mismatch",
    }


def test_cr151_evaluator_returns_pass_for_complete_fixture() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=_multiple_testing_report(),
        robust_statistics_report=_robust_report(),
        walk_forward_plan=_walk_forward_plan(),
        overfit_risk_report=_overfit_report(),
        statistical_gate_ref="artifact://cr151/statistical-gate.json",
        family_lineage_projection=_trusted_family_lineage(),
    )

    assert gate.status is StatisticalGateStatus.PASS
    assert gate.blocked_reasons == ()
    assert "artifact://cr151/walk-forward.json" in gate.report_refs
    assert gate.to_dict()["status"] == "PASS"


def test_cr151_evaluator_blocks_missing_mandatory_report_before_thresholds() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=_multiple_testing_report(),
        robust_statistics_report=_robust_report(),
        walk_forward_plan=None,
        overfit_risk_report=_overfit_report(),
        operation_counts={"credential_read": 1},
    )

    assert gate.status is StatisticalGateStatus.BLOCKED
    assert {reason.field for reason in gate.blocked_reasons} >= {"walk_forward_plan", "credential_read"}


def test_cr151_evaluator_fails_hard_thresholds() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=MultipleTestingReport(
            family_id="cr151-factor-family",
            candidate_count=3,
            raw_p_values=(0.4, 0.5, 0.6),
            adjusted_p_values=(0.4, 0.5, 0.6),
            alpha=0.05,
            method="BH",
            rejected_count=0,
        ),
        robust_statistics_report=_robust_report(),
        walk_forward_plan=_walk_forward_plan((True, False, False)),
        overfit_risk_report=_overfit_report(),
        family_lineage_projection=_trusted_family_lineage(),
    )

    assert gate.status is StatisticalGateStatus.FAIL
    assert {reason.code for reason in gate.blocked_reasons} >= {
        "statistical_gate_fdr_no_rejections",
        "statistical_gate_oos_pass_rate_below_threshold",
    }


def test_cr151_evaluator_needs_review_for_small_but_present_sample() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=_multiple_testing_report(),
        robust_statistics_report=_robust_report(sample_count=20),
        walk_forward_plan=_walk_forward_plan(),
        overfit_risk_report=_overfit_report(),
        family_lineage_projection=_trusted_family_lineage(),
    )

    assert gate.status is StatisticalGateStatus.NEEDS_REVIEW
    assert gate.needs_review_reasons[0].code == "statistical_gate_sample_count_below_review_threshold"
    assert default_statistical_gate_thresholds().min_oos_pass_rate == 0.67


def test_cr151_complete_threshold_fixture_without_lineage_is_blocked() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=_multiple_testing_report(),
        robust_statistics_report=_robust_report(),
        walk_forward_plan=_walk_forward_plan(),
        overfit_risk_report=_overfit_report(),
    )

    assert gate.status is StatisticalGateStatus.BLOCKED
    assert gate.family_lineage_projection["availability"] == "typed_unavailable"
    assert "statistical_gate_family_lineage_blocked" in {
        reason.code for reason in gate.blocked_reasons
    }


def test_cr151_statistical_status_maps_to_existing_admission_status() -> None:
    assert map_statistical_gate_status_to_admission_status("PASS") is AdmissionStatus.PASS
    assert map_statistical_gate_status_to_admission_status("FAIL") is AdmissionStatus.FAIL
    assert map_statistical_gate_status_to_admission_status("NEEDS_REVIEW") is AdmissionStatus.WARN
    assert map_statistical_gate_status_to_admission_status("BLOCKED") is AdmissionStatus.BLOCKED


def test_cr151_attach_statistical_gate_preserves_original_status_and_runtime_flags() -> None:
    package = {
        "package_id": "strategy-admission:cr151:fixture",
        "admission_status": "pass",
        "evidence_refs": ("artifact://existing/admission.json",),
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }

    attached = attach_statistical_gate_to_admission_package(
        package,
        {
            "status": "NEEDS_REVIEW",
            "statistical_gate_ref": "artifact://cr151/statistical-gate.json",
            "report_refs": ("artifact://cr151/robust-stats.json",),
        },
    )

    assert attached["admission_status"] == "warn"
    assert attached["statistical_gate_summary"]["status"] == "NEEDS_REVIEW"
    assert attached["not_qmt_authorization"] is True
    assert "artifact://cr151/statistical-gate.json" in attached["evidence_refs"]
    assert "artifact://cr151/robust-stats.json" in attached["evidence_refs"]
