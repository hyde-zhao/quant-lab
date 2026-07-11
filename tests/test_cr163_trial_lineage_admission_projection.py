from __future__ import annotations

import pytest

from engine.cross_strategy_reliability_gates import (
    GATE_IDS,
    ReliabilityGateStatus,
    evaluate_gate1_statistical_reliability,
)
from engine.experiment_family_lineage import (
    ExperimentFamilyManifest,
    FamilyEvidenceProjection,
    FamilyLineageValidationResult,
    LineageAvailability,
    ValidationStatus,
)
from engine.daily_multifactor_baseline_artifact import (
    ArtifactStatus,
    BaselineValidationSummary,
    DailyMultifactorBaselineArtifact,
    GateDecision,
    build_claim_boundary,
    compose_admission_package,
    derive_paper_candidate,
)
from engine.strategy_admission_package import attach_family_lineage_to_admission_package
from engine.strategy_admission_statistical_gate import (
    BacktestOverfitRiskReport,
    MultipleTestingReport,
    RobustFactorStatisticsReport,
    StatisticalGateStatus,
    ValidationBoundFamilyEvidence,
    WalkForwardValidationPlan,
    consume_family_lineage_projection,
    evaluate_strategy_admission_statistical_gate,
)


def _present() -> ValidationBoundFamilyEvidence:
    trial_ids = tuple(f"trial-{index:02d}" for index in range(12))
    manifest = ExperimentFamilyManifest(
        schema_version=1,
        family_id="family-cr163",
        manifest_version=1,
        spec_ref="fixture://cr163/family/spec",
        events_ref="fixture://cr163/family/events",
        sealed_event_count=12,
        sealed_last_sequence=12,
        raw_trial_count=12,
        trial_ids=trial_ids,
        seal_hash="sha256:cr163-sealed-validation-bound",
        sealed_at="2026-07-11T00:00:00Z",
    )
    validation = FamilyLineageValidationResult(
        schema_version=1,
        validation_id="validation-cr163-fixture",
        target_ref="fixture://cr163/family/manifest-v1",
        target_hash=manifest.seal_hash,
        availability=LineageAvailability.PRESENT,
        validation_status=ValidationStatus.PASS,
        recomputed_raw_trial_count=12,
        declared_raw_trial_count=12,
    )
    return ValidationBoundFamilyEvidence(manifest, validation)


def _reports(trial_count: int = 12) -> dict[str, object]:
    return {
        "multiple_testing_report": MultipleTestingReport(
            family_id="family-cr163",
            candidate_count=1,
            raw_p_values=(0.01,),
            adjusted_p_values=(0.01,),
            alpha=0.05,
            method="BH",
            rejected_count=1,
            report_ref="fixture://cr163/multiple",
        ),
        "robust_statistics_report": RobustFactorStatisticsReport(
            metric_id="rank_ic",
            sample_count=64,
            ic_mean=0.03,
            rank_ic_mean=0.04,
            robust_t_stat=2.5,
            p_value=0.01,
            autocorrelation_lags=(1,),
            report_ref="fixture://cr163/robust",
        ),
        "walk_forward_plan": WalkForwardValidationPlan(
            folds=1,
            train_window="504d",
            validation_window="126d",
            oos_window="63d",
            embargo_days=5,
            fold_metrics=({"fold_id": 1, "passed": True},),
            report_ref="fixture://cr163/walk-forward",
        ),
        "overfit_risk_report": BacktestOverfitRiskReport(
            trial_count=trial_count,
            pbo=0.1,
            dsr=0.4,
            observed_sharpe=1.2,
            skew=0.0,
            kurtosis=3.0,
            sample_length=756,
            report_ref="fixture://cr163/overfit",
        ),
    }


def _package(status: str = "pass") -> dict[str, object]:
    return {
        "package_id": "cr163-fixture",
        "admission_status": status,
        "evidence_refs": (),
        "blocked_reasons": (),
        "limitations": (),
        "not_authorized_counters": {},
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }


def _lineage_tuple(payload: dict[str, object]) -> tuple[object, object, object]:
    return payload["target_ref"], payload["target_hash"], payload["raw_trial_count"]


def test_cr163_same_validation_bound_projection_reaches_all_three_consumers() -> None:
    projection = _present()
    statistical = evaluate_strategy_admission_statistical_gate(
        **_reports(), family_lineage_projection=projection
    )
    reliability = evaluate_gate1_statistical_reliability(
        {"pbo_or_cscv_refs": ("fixture://pbo",)},
        family_lineage_projection=projection,
    )
    package = attach_family_lineage_to_admission_package(_package(), projection)

    projections = (
        statistical.to_dict()["family_lineage_projection"],
        reliability.to_dict()["family_lineage_projection"],
        package["family_lineage_projection"],
    )
    assert projections[0] == projections[1] == projections[2]
    assert [_lineage_tuple(item) for item in projections] == [
        (
            "fixture://cr163/family/manifest-v1",
            "sha256:cr163-sealed-validation-bound",
            12,
        )
    ] * 3
    assert statistical.status is StatisticalGateStatus.PASS
    assert reliability.status is ReliabilityGateStatus.BLOCKED
    assert package["admission_status"] == "pass"


@pytest.mark.parametrize(
    "reason",
    (
        "seal_check_failed",
        "completeness_check_failed",
        "target_binding_failed",
        "raw_trial_count_mismatch",
        "seal_hash_mismatch",
    ),
)
def test_cr163_failed_upstream_validation_never_becomes_present(reason: str) -> None:
    blocked = FamilyEvidenceProjection(
        availability=LineageAvailability.BLOCKED,
        target_ref="fixture://cr163/blocked",
        target_hash="sha256:blocked",
        blocked_reasons=(reason,),
    )
    consumed = consume_family_lineage_projection(blocked)
    package = attach_family_lineage_to_admission_package(_package(), blocked)

    assert consumed["availability"] == "blocked"
    assert consumed["raw_trial_count"] is None
    assert package["admission_status"] == "blocked"


def test_cr163_missing_native_lineage_is_typed_unavailable_and_claims_stay_closed() -> None:
    statistical = evaluate_strategy_admission_statistical_gate(**_reports())
    reliability = evaluate_gate1_statistical_reliability({}, family_lineage_projection=None)
    package = attach_family_lineage_to_admission_package(_package(), None)

    for item in (
        statistical.to_dict()["family_lineage_projection"],
        reliability.to_dict()["family_lineage_projection"],
        package["family_lineage_projection"],
    ):
        assert item["availability"] == "typed_unavailable"
        assert item["effective_trial_count_availability"] == "typed_unavailable"
        assert item["effective_trial_count"] is None
        assert item["effective_ref"] == ""
        assert item["effective_method"] == ""
        assert item["c1_input_status"] == "input_blocked"
    assert statistical.status is StatisticalGateStatus.BLOCKED
    assert reliability.status is ReliabilityGateStatus.BLOCKED
    assert package["admission_status"] == "blocked"


def test_cr163_manual_count_is_reconciliation_only_and_mismatch_blocks() -> None:
    matching = evaluate_strategy_admission_statistical_gate(
        **_reports(12), family_lineage_projection=_present()
    )
    mismatch = evaluate_strategy_admission_statistical_gate(
        **_reports(11), family_lineage_projection=_present()
    )

    assert matching.family_lineage_reconciliation["status"] == "match"
    assert matching.status is StatisticalGateStatus.PASS
    assert mismatch.family_lineage_reconciliation["status"] == "mismatch"
    assert mismatch.family_lineage_projection == matching.family_lineage_projection
    assert mismatch.family_lineage_projection["availability"] == "present"
    assert mismatch.status is StatisticalGateStatus.BLOCKED


def test_cr163_manual_reconciliation_absent_is_consumer_local() -> None:
    gate = evaluate_strategy_admission_statistical_gate(
        multiple_testing_report=_reports()["multiple_testing_report"],
        robust_statistics_report=_reports()["robust_statistics_report"],
        walk_forward_plan=_reports()["walk_forward_plan"],
        overfit_risk_report=None,
        family_lineage_projection=_present(),
    )

    assert gate.family_lineage_reconciliation == {
        "status": "absent",
        "manual_trial_count": None,
        "validated_raw_trial_count": 12,
    }
    assert "manual_reconciliation" not in gate.family_lineage_projection


@pytest.mark.parametrize(
    "forged",
    (
        {
            "availability": "present",
            "target_ref": "fixture://forged/ref",
            "target_hash": "sha256:forged",
            "raw_trial_count": 999,
            "c1_input_status": "raw_input_ready",
        },
        {
            "availability": "present",
            "target_ref": "fixture://forged/ref",
            "target_hash": "sha256:forged",
            "raw_trial_count": 12,
            "effective_trial_count": 12,
            "effective_ref": "fixture://forged/effective",
            "effective_method": "raw_equals_effective",
            "c1_input_status": "raw_input_ready",
        },
        {"availability": "unknown", "target_ref": "fixture://forged/ref"},
        {"availability": "present", "raw_trial_count": 12},
    ),
)
def test_cr163_untrusted_serialized_projection_is_blocked_across_all_consumers(
    forged: dict[str, object],
) -> None:
    statistical = evaluate_strategy_admission_statistical_gate(
        **_reports(), family_lineage_projection=forged
    )
    reliability = evaluate_gate1_statistical_reliability(
        {}, family_lineage_projection=forged
    )
    package = attach_family_lineage_to_admission_package(_package(), forged)

    projections = (
        statistical.to_dict()["family_lineage_projection"],
        reliability.to_dict()["family_lineage_projection"],
        package["family_lineage_projection"],
    )
    assert projections[0] == projections[1] == projections[2]
    assert all(item["availability"] == "blocked" for item in projections)
    assert all(item["raw_trial_count"] is None for item in projections)
    assert statistical.status is StatisticalGateStatus.BLOCKED
    assert reliability.status is ReliabilityGateStatus.BLOCKED
    assert package["admission_status"] == "blocked"


def test_cr163_bare_present_dto_without_validation_binding_is_blocked() -> None:
    bare = FamilyEvidenceProjection(
        availability=LineageAvailability.PRESENT,
        target_ref="fixture://forged/ref",
        target_hash="sha256:forged",
        raw_trial_count=999,
    )

    consumed = consume_family_lineage_projection(bare)
    assert consumed["availability"] == "blocked"
    assert consumed["raw_trial_count"] is None
    assert "family_lineage_projection_malformed" in consumed["blocked_reasons"]


@pytest.mark.parametrize("initial", ("pass", "warn", "fail", "blocked"))
def test_cr163_package_status_only_worsens_and_runtime_flags_do_not_change(initial: str) -> None:
    present = attach_family_lineage_to_admission_package(_package(initial), _present())
    unavailable = attach_family_lineage_to_admission_package(_package(initial), None)

    assert present["admission_status"] == initial
    assert unavailable["admission_status"] == "blocked"
    for field_name in (
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
    ):
        assert present[field_name] is True
        assert unavailable[field_name] is True


def test_cr163_cr155_stays_blocked_without_native_ledger_and_no_gate_is_added() -> None:
    artifact = DailyMultifactorBaselineArtifact(
        strategy_id="cr155-daily-multifactor",
        universe_ref="fixture://cr155/universe",
        factor_specs=({"factor_id": "momentum", "weight": 1.0, "version_ref": "fixture://factor/v1"},),
        signal_spec={"ranking": "rank", "standardization": "zscore", "lag_policy": "t_plus_1"},
        portfolio_policy={"rebalance": "daily", "weighting": "equal", "cost_ref": "fixture://cost", "slippage_ref": "fixture://slippage"},
        validation_refs={"historical_backtest_ref": "fixture://backtest", "walk_forward_ref": "fixture://wf"},
        admission_refs={"statistical_gate_ref": "fixture://stat", "reliability_gate_ref": "fixture://reliability"},
        claim_boundary=build_claim_boundary("cr155-daily-multifactor"),
        rerun_refs={"run_a": "fixture://run/a", "run_b": "fixture://run/b"},
        evidence_refs=("fixture://cr155/artifact",),
    )
    validation = BaselineValidationSummary(
        status=ArtifactStatus.PASS,
        artifact_status=ArtifactStatus.PASS,
        provenance_status=ArtifactStatus.PASS,
        split_manifest_status=ArtifactStatus.PASS,
        historical_backtest_ref={"run_ref": "fixture://backtest"},
        split_manifest={"manifest_ref": "fixture://wf"},
        metrics={"total_return": 0.1},
        real_data_claim_allowed=True,
        evidence_refs=("fixture://cr155/validation",),
    )
    cr155 = compose_admission_package(
        artifact,
        validation,
        GateDecision(ArtifactStatus.PASS, gate_ref="fixture://stat"),
        GateDecision(ArtifactStatus.PASS, gate_ref="fixture://reliability"),
    )
    assert cr155.package_status is ArtifactStatus.PASS
    assert cr155.paper_candidate is True

    attached = attach_family_lineage_to_admission_package(cr155, None)
    candidate, _ = derive_paper_candidate(attached)

    assert attached["package_status"] == "BLOCKED"
    assert attached["paper_candidate"] is False
    assert candidate is False
    assert attached.get("historical_backfill_count", 0) == 0
    assert len(GATE_IDS) == 6
    assert all("lineage" not in gate_id for gate_id in GATE_IDS)
    assert all(value == 0 for value in attached.get("not_authorized_counters", {}).values())
