from __future__ import annotations

from dataclasses import replace

from engine.walk_forward_oos_evidence import (
    AuthorizationMetadata,
    FoldManifest,
    FoldMetricValue,
    LineageBinding,
    MetricPolicy,
    PurgeEmbargoPolicy,
    SplitPolicy,
    TemporalFold,
    WalkForwardEvidenceInput,
    fold_membership_hash,
    produce_walk_forward_oos_evidence,
    validate_walk_forward_oos_input,
)


def temporal_folds() -> tuple[TemporalFold, ...]:
    return (
        TemporalFold("f01", "2020-01-01", "2020-02-01", "2020-02-01", "2020-03-01", "2020-03-01", "2020-04-01"),
        TemporalFold("f02", "2020-01-01", "2020-03-01", "2020-03-01", "2020-04-01", "2020-04-01", "2020-05-01"),
        TemporalFold("f03", "2020-01-01", "2020-04-01", "2020-04-01", "2020-05-01", "2020-05-01", "2020-06-01"),
    )


def evidence_input(values: tuple[float, ...] = (1.0, 0.8, 0.6)) -> WalkForwardEvidenceInput:
    folds = temporal_folds()
    ids = tuple(item.fold_id for item in folds)
    membership = fold_membership_hash(ids)
    return WalkForwardEvidenceInput(
        subject_ref="strategy://fixture/daily-multifactor-v1",
        manifest=FoldManifest(
            manifest_id="wf-manifest-v1",
            manifest_ref="fixture://cr166/wf-manifest-v1",
            manifest_hash="sha256:fixture-manifest",
            declared_fold_count=3,
            ordered_fold_ids=ids,
            membership_hash=membership,
        ),
        split_policy=SplitPolicy(
            policy_id="expanding-v1",
            strategy_kind="daily-multifactor",
            mode="expanding-walk-forward",
            window_unit="days",
            policy_ref="fixture://cr166/split-policy-v1",
            schema_version="split_policy_v1",
        ),
        folds=folds,
        leakage_policy=PurgeEmbargoPolicy(
            overlap_applicability="overlapping-label-window",
            unit="days",
            label_or_window_horizon=2,
            purge_required=2,
            purge_applied=2,
            embargo_required=1,
            embargo_applied=1,
            purge_policy_ref="fixture://cr166/purge-v1",
            embargo_policy_ref="fixture://cr166/embargo-v1",
        ),
        metric_policies=(MetricPolicy("oos_score", "gte", 0.5),),
        fold_metrics=tuple(FoldMetricValue(fold.fold_id, "oos_score", value) for fold, value in zip(folds, values, strict=True)),
        lineage=LineageBinding(
            lineage_ref="fixture://cr166/lineage-v1",
            lineage_hash="sha256:fixture-lineage",
            fold_membership_hash=membership,
            source_refs=("fixture://cr166/source-v1",),
            source_hashes=("sha256:fixture-source",),
        ),
        authorization=AuthorizationMetadata(
            validation_mode="fixture-static",
            ref_class="fixture",
            operation_counts={
                "credential_read": 0,
                "real_lake_read": 0,
                "provider_fetch": 0,
                "runtime_call": 0,
                "broker_access": 0,
                "external_framework_run": 0,
            },
        ),
    )


def passing_component():
    value = evidence_input()
    return produce_walk_forward_oos_evidence(validate_walk_forward_oos_input(value)).component


def with_input(value: WalkForwardEvidenceInput, **changes):
    return replace(value, **changes)
