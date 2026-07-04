from __future__ import annotations

import json

from engine.daily_multifactor_baseline_artifact import (
    ArtifactStatus,
    DailyMultifactorBaselineArtifact,
    GateDecision,
    HistoricalBacktestRef,
    MetricTolerance,
    ReadonlyDataProvenance,
    RerunMetricSnapshot,
    ValidationMetrics,
    WalkForwardSplitManifest,
    artifact_to_json_dict,
    build_claim_boundary,
    build_provenance_summary,
    build_release_wording,
    build_validation_summary,
    compare_rerun_metrics,
    compose_admission_package,
    derive_paper_candidate,
    downgrade_to_fixture_static,
    rerun_allows_candidate,
    validate_baseline_artifact,
    validate_readonly_provenance,
    validate_release_wording,
    validate_split_manifest,
    validation_allows_admission,
)


def _artifact(**overrides: object) -> DailyMultifactorBaselineArtifact:
    base: dict[str, object] = {
        "strategy_id": "dmf-baseline-v1",
        "universe_ref": "lake://current-truth/universe/csi800/asof-2026-07-04",
        "factor_specs": (
            {"factor_id": "momentum_20d", "weight": 0.4, "version_ref": "factor://momentum_20d/v1"},
            {"factor_id": "value_ep", "weight": 0.3, "version_ref": "factor://value_ep/v1"},
            {"factor_id": "quality_roe", "weight": 0.3, "version_ref": "factor://quality_roe/v1"},
        ),
        "signal_spec": {
            "ranking": "cross_sectional_rank",
            "standardization": "zscore",
            "lag_policy": "t_plus_1",
        },
        "portfolio_policy": {
            "rebalance": "daily",
            "weighting": "rank_weighted",
            "cost_ref": "policy://cost/stock-a-share-v1",
            "slippage_ref": "policy://slippage/stock-a-share-v1",
        },
        "validation_refs": {
            "historical_backtest_ref": "run://cr155/baseline/backtest/a",
            "walk_forward_ref": "run://cr155/baseline/wf/a",
        },
        "admission_refs": {
            "statistical_gate_ref": "gate://cr151/statistical/pass",
            "reliability_gate_ref": "gate://cr154/reliability/pass",
        },
        "rerun_refs": {
            "run_a": "run://cr155/rerun/a",
            "run_b": "run://cr155/rerun/b",
        },
        "claim_boundary": build_claim_boundary("dmf-baseline-v1"),
        "evidence_refs": ("fixture://cr155/artifact",),
    }
    base.update(overrides)
    return DailyMultifactorBaselineArtifact(**base)  # type: ignore[arg-type]


def _provenance(**overrides: object) -> ReadonlyDataProvenance:
    base: dict[str, object] = {
        "input_refs": (
            "lake://current-truth/prices/daily/asof-2026-07-04",
            "lake://current-truth/factors/daily/asof-2026-07-04",
        ),
        "read_scope": {"purpose": "CR155 historical/OOS validation", "date_range": "2018-01-01..2026-06-30"},
        "operation_counts": {
            "credential_read": 0,
            "env_read": 0,
            "real_lake_write": 0,
            "catalog_pointer_mutation": 0,
            "nas_operation": 0,
            "provider_fetch": 0,
            "runtime_operation": 0,
            "trading_operation": 0,
            "broker_operation": 0,
            "external_framework_run": 0,
            "store_write": 0,
            "registry_write": 0,
            "publish_operation": 0,
        },
        "evidence_refs": ("fixture://cr155/provenance",),
    }
    base.update(overrides)
    return ReadonlyDataProvenance(**base)  # type: ignore[arg-type]


def _backtest(**overrides: object) -> HistoricalBacktestRef:
    base = {
        "run_ref": "run://cr155/backtest/a",
        "report_ref": "report://cr155/backtest/a",
        "cost_ref": "report://cr155/backtest/a/cost",
        "risk_ref": "report://cr155/backtest/a/risk",
        "evidence_refs": ("fixture://cr155/backtest",),
    }
    base.update(overrides)
    return HistoricalBacktestRef(**base)


def _split(**overrides: object) -> WalkForwardSplitManifest:
    base = {
        "folds": (
            {
                "fold_id": "wf-001",
                "train_start": "2018-01-01",
                "train_end": "2020-12-31",
                "test_start": "2021-01-01",
                "test_end": "2021-12-31",
                "metrics_ref": "metrics://cr155/wf-001",
            },
            {
                "fold_id": "wf-002",
                "train_start": "2019-01-01",
                "train_end": "2021-12-31",
                "test_start": "2022-01-01",
                "test_end": "2022-12-31",
                "metrics_ref": "metrics://cr155/wf-002",
            },
        ),
        "purge_policy_ref": "policy://purge/5d",
        "embargo_days": 5,
        "manifest_ref": "manifest://cr155/walk-forward",
        "evidence_refs": ("fixture://cr155/walk-forward",),
    }
    base.update(overrides)
    return WalkForwardSplitManifest(**base)


def _metrics(**overrides: object) -> ValidationMetrics:
    base = {
        "total_return": 0.126,
        "max_drawdown": -0.082,
        "turnover": 2.41,
        "cost": 0.013,
        "capacity_liquidity_summary": "capacity n/a-with-reason; liquidity median ADV coverage fixture",
        "evidence_refs": ("fixture://cr155/metrics",),
    }
    base.update(overrides)
    return ValidationMetrics(**base)


def _validation_summary(**metric_overrides: object):
    return build_validation_summary(_artifact(), _provenance(), _backtest(), _split(), _metrics(**metric_overrides))


def test_cr155_s01_complete_artifact_validates_and_serializes_deterministically() -> None:
    artifact = _artifact()

    result = validate_baseline_artifact(artifact, require_rerun_refs=True)
    first = artifact_to_json_dict(artifact)
    second = artifact_to_json_dict(artifact)

    assert result.status is ArtifactStatus.PASS
    assert result.passed is True
    assert first == second
    assert json.dumps(first, sort_keys=True)


def test_cr155_s01_missing_universe_or_overclaim_blocks_artifact() -> None:
    missing = validate_baseline_artifact(_artifact(universe_ref=""))
    overclaim = validate_baseline_artifact(_artifact(claim_boundary=("paper-ready daily multifactor strategy",)))

    assert missing.status is ArtifactStatus.BLOCKED
    assert "artifact_required_field_missing" in {issue.code for issue in missing.issues}
    assert overclaim.status is ArtifactStatus.BLOCKED
    assert "overclaim_wording_detected" in {issue.code for issue in overclaim.issues}


def test_cr155_s02_readonly_provenance_passes_with_zero_counters_and_blocks_forbidden_operations() -> None:
    safe = validate_readonly_provenance(_provenance())
    unsafe = validate_readonly_provenance(
        _provenance(operation_counts={"credential_read": 1, "real_lake_write": 1})
    )
    summary = build_provenance_summary(_provenance())

    assert safe.status is ArtifactStatus.PASS
    assert unsafe.status is ArtifactStatus.BLOCKED
    assert "readonly_provenance_forbidden_operation" in {issue.code for issue in unsafe.issues}
    assert summary["claim_allowed"] is True


def test_cr155_s02_fixture_static_fallback_preserves_audit_and_blocks_real_data_claim() -> None:
    fallback = downgrade_to_fixture_static("readonly provenance unavailable in fixture test")
    result = validate_readonly_provenance(fallback)
    summary = build_provenance_summary(fallback)

    assert result.status is ArtifactStatus.NEEDS_REVIEW
    assert summary["fallback_mode"] == "fixture_static"
    assert summary["claim_allowed"] is False


def test_cr155_s03_split_manifest_and_validation_summary_pass_for_complete_refs() -> None:
    split_result = validate_split_manifest(_split())
    summary = _validation_summary()
    allowed, reasons = validation_allows_admission(summary)

    assert split_result.status is ArtifactStatus.PASS
    assert summary.status is ArtifactStatus.PASS
    assert summary.real_data_claim_allowed is True
    assert allowed is True
    assert reasons == ()


def test_cr155_s03_missing_split_or_cost_blocks_validation() -> None:
    bad_split = validate_split_manifest(_split(folds=()))
    bad_summary = _validation_summary(cost="not-a-number")
    allowed, reasons = validation_allows_admission(bad_summary)

    assert bad_split.status is ArtifactStatus.BLOCKED
    assert bad_summary.status is ArtifactStatus.BLOCKED
    assert allowed is False
    assert reasons == ("validation_status_blocked_blocks_admission",)


def test_cr155_s04_admission_package_composes_pass_and_candidate_true() -> None:
    package = compose_admission_package(
        _artifact(),
        _validation_summary(),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr151/stat",), gate_ref="gate://cr151/stat"),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr154/reliability",), gate_ref="gate://cr154/reliability"),
    )
    candidate, reasons = derive_paper_candidate(package)

    assert package.package_status is ArtifactStatus.PASS
    assert package.paper_candidate is True
    assert candidate is True
    assert reasons == ("all_mandatory_gates_passed",)
    assert "does not authorize live trading" in package.non_authorization


def test_cr155_s04_admission_missing_or_nonpass_gate_fails_closed() -> None:
    missing_stat = compose_admission_package(
        _artifact(),
        _validation_summary(),
        None,
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr154/reliability",), gate_ref="gate://cr154/reliability"),
    )
    reliability_fail = compose_admission_package(
        _artifact(),
        _validation_summary(),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr151/stat",), gate_ref="gate://cr151/stat"),
        GateDecision(ArtifactStatus.FAIL, reasons=("capacity_impact_failed",), evidence_refs=("fixture://cr154/fail",), gate_ref="gate://cr154/fail"),
    )
    needs_review = compose_admission_package(
        _artifact(),
        _validation_summary(),
        GateDecision(ArtifactStatus.NEEDS_REVIEW, reasons=("statistical_gate_needs_review",), evidence_refs=("fixture://cr151/review",), gate_ref="gate://cr151/review"),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr154/reliability",), gate_ref="gate://cr154/reliability"),
    )

    assert missing_stat.package_status is ArtifactStatus.BLOCKED
    assert missing_stat.paper_candidate is False
    assert "statistical_gate_missing" in missing_stat.blockers
    assert reliability_fail.package_status is ArtifactStatus.FAIL
    assert reliability_fail.paper_candidate is False
    assert needs_review.package_status is ArtifactStatus.NEEDS_REVIEW
    assert needs_review.paper_candidate is False


def test_cr155_s05_identical_reruns_pass_and_allow_candidate() -> None:
    metrics = {
        "total_return": 0.126,
        "max_drawdown": -0.082,
        "turnover": 2.41,
        "cost": 0.013,
        "capacity_liquidity_summary": "capacity fixture summary",
    }

    report = compare_rerun_metrics(
        RerunMetricSnapshot("run://cr155/rerun/a", metrics, ArtifactStatus.PASS),
        RerunMetricSnapshot("run://cr155/rerun/b", dict(metrics), ArtifactStatus.PASS),
        MetricTolerance(numeric_tolerance=0.0),
    )
    allowed, reasons = rerun_allows_candidate(report)

    assert report.status is ArtifactStatus.PASS
    assert allowed is True
    assert reasons == ()


def test_cr155_s05_metric_or_status_drift_blocks_candidate() -> None:
    first = {
        "total_return": 0.126,
        "max_drawdown": -0.082,
        "turnover": 2.41,
        "cost": 0.013,
        "capacity_liquidity_summary": "capacity fixture summary",
    }
    second = dict(first)
    second["max_drawdown"] = -0.09

    numeric_drift = compare_rerun_metrics(
        RerunMetricSnapshot("run://cr155/rerun/a", first, ArtifactStatus.PASS),
        RerunMetricSnapshot("run://cr155/rerun/b", second, ArtifactStatus.PASS),
    )
    status_drift = compare_rerun_metrics(
        RerunMetricSnapshot("run://cr155/rerun/a", first, ArtifactStatus.PASS),
        RerunMetricSnapshot("run://cr155/rerun/b", first, ArtifactStatus.NEEDS_REVIEW),
    )

    assert numeric_drift.status is ArtifactStatus.NEEDS_REVIEW
    assert rerun_allows_candidate(numeric_drift)[0] is False
    assert status_drift.status is ArtifactStatus.FAIL
    assert rerun_allows_candidate(status_drift)[0] is False


def test_cr155_s05_release_wording_is_research_only_and_overclaim_is_blocked() -> None:
    package = compose_admission_package(
        _artifact(),
        _validation_summary(),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr151/stat",), gate_ref="gate://cr151/stat"),
        GateDecision(ArtifactStatus.PASS, evidence_refs=("fixture://cr154/reliability",), gate_ref="gate://cr154/reliability"),
    )
    report = compare_rerun_metrics(
        RerunMetricSnapshot(
            "run://cr155/rerun/a",
            {
                "total_return": 0.126,
                "max_drawdown": -0.082,
                "turnover": 2.41,
                "cost": 0.013,
                "capacity_liquidity_summary": "capacity fixture summary",
            },
            ArtifactStatus.PASS,
        ),
        RerunMetricSnapshot(
            "run://cr155/rerun/b",
            {
                "total_return": 0.126,
                "max_drawdown": -0.082,
                "turnover": 2.41,
                "cost": 0.013,
                "capacity_liquidity_summary": "capacity fixture summary",
            },
            ArtifactStatus.PASS,
        ),
    )

    safe_wording = validate_release_wording(build_release_wording(_artifact(), package, report))
    unsafe_wording = validate_release_wording(["This is a live-ready strategy."])

    assert safe_wording.status is ArtifactStatus.PASS
    assert unsafe_wording.status is ArtifactStatus.BLOCKED
    assert "overclaim_wording_detected" in {issue.code for issue in unsafe_wording.issues}
