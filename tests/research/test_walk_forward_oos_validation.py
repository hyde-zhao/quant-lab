from __future__ import annotations

from dataclasses import replace

import pytest

from engine.daily_multifactor_baseline_artifact import WalkForwardSplitManifest
from engine.research_production_contracts import EventTimeSemantics, MLCVFoldSpec, MLPurgedEmbargoCVPolicy
from engine.strategy_evidence import EvidenceAvailability
from engine.walk_forward_oos_evidence import (
    AuthorizationMetadata,
    FoldMetricValue,
    LineageBinding,
    MetricPolicy,
    WalkForwardInputStatus,
    adapt_daily_walk_forward_input,
    adapt_ml_walk_forward_input,
    event_walk_forward_applicability,
    validate_walk_forward_oos_input,
)
from tests.research.walk_forward_oos_test_support import evidence_input, temporal_folds


def _codes(validation) -> set[str]:
    return {item.code for item in validation.issues}


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (lambda value: replace(value, folds=value.folds[:-1]), "fold_inventory_mismatch"),
        (lambda value: replace(value, folds=(replace(value.folds[0], oos_start="2020-01-15"), *value.folds[1:])), "temporal_order_invalid"),
        (lambda value: replace(value, leakage_policy=replace(value.leakage_policy, purge_policy_ref="")), "purge_policy_ref_missing"),
        (lambda value: replace(value, leakage_policy=replace(value.leakage_policy, embargo_applied=0)), "embargo_insufficient"),
        (lambda value: replace(value, fold_metrics=(replace(value.fold_metrics[0], value=float("nan")), *value.fold_metrics[1:])), "fold_metric_non_finite"),
        (lambda value: replace(value, lineage=replace(value.lineage, fold_membership_hash="sha256:other")), "lineage_membership_mismatch"),
        (lambda value: replace(value, authorization=replace(value.authorization, ref_class="real-data")), "real_or_external_ref_unauthorized"),
    ],
)
def test_p0_fail_closed_categories(mutate, expected_code: str) -> None:
    result = validate_walk_forward_oos_input(mutate(evidence_input()))
    assert result.status is not WalkForwardInputStatus.VALIDATED
    assert expected_code in _codes(result)
    assert all(item.code and item.field and item.message for item in result.issues)


def test_missing_metric_is_typed_unavailable_and_cannot_pass() -> None:
    value = evidence_input()
    result = validate_walk_forward_oos_input(replace(value, fold_metrics=value.fold_metrics[:-1]))
    assert result.status is WalkForwardInputStatus.TYPED_UNAVAILABLE
    assert "mandatory_fold_metric_missing" in _codes(result)


def test_exact_half_open_purge_and_embargo_boundaries_validate() -> None:
    assert validate_walk_forward_oos_input(evidence_input()).status is WalkForwardInputStatus.VALIDATED


def test_daily_adapter_maps_only_explicit_companion_facts() -> None:
    value = evidence_input()
    legacy = WalkForwardSplitManifest(
        folds=tuple({"fold_id": item.fold_id} for item in value.folds),
        purge_policy_ref="fixture://purge",
        embargo_days=1,
        manifest_ref="fixture://daily-manifest",
    )
    result = adapt_daily_walk_forward_input(
        legacy,
        subject_ref=value.subject_ref,
        temporal_folds=value.folds,
        metric_policies=value.metric_policies,
        fold_metrics=value.fold_metrics,
        lineage=value.lineage,
        authorization=value.authorization,
        split_policy=value.split_policy,
        leakage_policy=value.leakage_policy,
    )
    assert result.passed


def test_ml_adapter_requires_explicit_test_to_oos_mapping() -> None:
    value = evidence_input()
    ml_policy = MLPurgedEmbargoCVPolicy(
        policy_id="ml-cv-v1",
        folds=tuple(
            MLCVFoldSpec(
                fold_id=item.fold_id,
                train_start=item.train_start,
                train_end=item.train_end,
                validation_start=item.validation_start,
                validation_end=item.validation_end,
                test_start=item.oos_start,
                test_end=item.oos_end,
            )
            for item in value.folds
        ),
        purge_window_days=2,
        embargo_days=2,
        label_horizon_days=2,
    )
    passed = adapt_ml_walk_forward_input(
        ml_policy,
        subject_ref="strategy://fixture/ml-v1",
        test_is_oos=True,
        metric_policies=value.metric_policies,
        fold_metrics=value.fold_metrics,
        lineage=replace(value.lineage, lineage_ref="fixture://ml-lineage"),
        authorization=value.authorization,
    )
    unavailable = adapt_ml_walk_forward_input(
        ml_policy,
        subject_ref="strategy://fixture/ml-v1",
        test_is_oos=False,
        metric_policies=value.metric_policies,
        fold_metrics=value.fold_metrics,
        lineage=replace(value.lineage, lineage_ref="fixture://ml-lineage"),
        authorization=value.authorization,
    )
    assert passed.passed
    assert unavailable.status is WalkForwardInputStatus.TYPED_UNAVAILABLE


def test_event_compatibility_is_explicit_na_without_producer_or_feed_access() -> None:
    applicability = event_walk_forward_applicability(
        EventTimeSemantics("2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02")
    )
    assert applicability.availability is EvidenceAvailability.NOT_APPLICABLE_WITH_REASON
    assert applicability.reason_code == "event_fold_semantics_unfrozen"
    assert (applicability.producer_count, applicability.fixture_count, applicability.feed_access_count) == (0, 0, 0)
