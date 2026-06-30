from __future__ import annotations

from dataclasses import replace

from engine.research_manifest import (
    ExperimentSplitPolicy,
    ModelArtifactRef,
    PublishedDatasetSnapshotRef,
    build_experiment_manifest_closure,
)
from engine.training_snapshot_contract import (
    STATUS_BLOCKED,
    STATUS_PASS,
    TrainingSnapshotSpec,
    build_training_snapshot_spec,
    validate_training_snapshot_cutoff,
)


def test_training_snapshot_cutoff_passes_for_published_snapshot_before_as_of() -> None:
    spec = build_training_snapshot_spec(
        closure=_closure(),
        feature_schema_hash="sha256:feature-schema",
        lineage_refs=("process/stories/CR139-S16-training-snapshot-cutoff-LLD.md",),
    )
    result = validate_training_snapshot_cutoff(spec)

    assert isinstance(spec, TrainingSnapshotSpec)
    assert result.status == STATUS_PASS
    assert result.passed
    assert spec.published_only is True
    assert spec.training_cutoff == "2024-01-15T23:59:59+08:00"
    assert all(value == 0 for value in result.operation_counts.values())


def test_training_snapshot_cutoff_blocks_mutable_latest_refs() -> None:
    spec = replace(_spec(), snapshot_id="latest", published_path="lake/published/prices/current/manifest.json")
    result = validate_training_snapshot_cutoff(spec)

    assert result.status == STATUS_BLOCKED
    assert "mutable_snapshot_ref_forbidden" in {issue["code"] for issue in result.issues}


def test_training_snapshot_cutoff_blocks_cutoff_after_as_of() -> None:
    spec = replace(_spec(), training_cutoff="2024-02-02T00:00:00+08:00")
    result = validate_training_snapshot_cutoff(spec)

    assert result.status == STATUS_BLOCKED
    assert "training_cutoff_after_as_of" in {issue["code"] for issue in result.issues}


def test_training_snapshot_cutoff_blocks_missing_required_fields_and_nonzero_counters() -> None:
    spec = replace(_spec(), content_hash="", permission_counters={"provider_fetch": 1})
    result = validate_training_snapshot_cutoff(spec)

    codes = {issue["code"] for issue in result.issues}
    assert result.status == STATUS_BLOCKED
    assert "training_snapshot_required_field_missing" in codes
    assert "permission_counter_nonzero" in codes


def _spec() -> TrainingSnapshotSpec:
    return build_training_snapshot_spec(
        closure=_closure(),
        feature_schema_hash="sha256:feature-schema",
        lineage_refs=("process/stories/CR139-S16-training-snapshot-cutoff-LLD.md",),
    )


def _closure():
    return build_experiment_manifest_closure(
        closure_id="closure-cr139-s16-fixture",
        run_id="run-cr139-s16-fixture",
        published_dataset_snapshot=PublishedDatasetSnapshotRef(
            snapshot_id="published-prices-2024-01-31",
            dataset="prices",
            published_path="lake/published/prices/snapshot-2024-01-31/manifest.json",
            as_of_trade_date="2024-01-31",
            as_of_timestamp="2024-02-01T16:00:00+08:00",
            lineage_checksum="sha256:lineage",
            content_hash="sha256:dataset",
            primary_keys=("trade_date", "symbol"),
        ),
        split_policy=ExperimentSplitPolicy(
            split_id="walk-forward-primary",
            train_start="2023-01-01",
            train_end="2023-12-31",
            validation_start="2024-01-02",
            validation_end="2024-01-15",
            test_start="2024-01-22",
            test_end="2024-01-31",
            cutoff_date="2024-01-15T23:59:59+08:00",
            embargo_days=5,
            label_horizon_days=20,
        ),
        model_artifact=ModelArtifactRef(
            model_id="stage4-tree-fixture",
            artifact_path="reports/research_catalog/v1/stage4/model.json",
            artifact_hash="sha256:model",
            dataset_snapshot_hash="sha256:dataset",
            feature_artifact_refs=("features://feature-set/v1/artifact-001",),
        ),
        feature_artifact_refs=("features://feature-set/v1/artifact-001",),
        lineage_refs=("process/stories/CR139-S12-experiment-manifest-closure-LLD.md",),
    )
