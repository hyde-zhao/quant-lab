from __future__ import annotations

import json
from dataclasses import replace

from engine.research_manifest import (
    CR139_S29_CORRECTNESS_STANDARD_REF,
    MF_CR139_S29_STANDARD_MISSING,
    MF_CR139_SNAPSHOT_MISMATCH,
    MF_FORBIDDEN_TRUTH_SOURCE,
    MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED,
    MF_SCHEMA_REQUIRED_FIELD_MISSING,
    ExperimentManifestClosure,
    ExperimentSplitPolicy,
    ModelArtifactRef,
    PublishedDatasetSnapshotRef,
    build_experiment_manifest_closure,
    validate_experiment_manifest_closure,
)


def test_cr139_manifest_closure_records_snapshot_split_model_and_s29_standard() -> None:
    closure = _closure()
    result = validate_experiment_manifest_closure(closure)
    payload = closure.to_dict()

    assert isinstance(closure, ExperimentManifestClosure)
    assert result.passed
    assert payload["published_dataset_snapshot"]["snapshot_id"] == "published-prices-2024-01-31"
    assert payload["published_dataset_snapshot"]["as_of_timestamp"] == "2024-02-01T16:00:00+08:00"
    assert payload["split_policy"]["cutoff_date"] == "2024-01-15"
    assert payload["split_policy"]["embargo_days"] == 5
    assert payload["split_policy"]["label_horizon_days"] == 20
    assert payload["model_artifact"]["artifact_hash"] == "sha256:model"
    assert payload["model_artifact"]["dataset_snapshot_hash"] == payload["published_dataset_snapshot"]["content_hash"]
    assert payload["s29_correctness_standard_ref"] == CR139_S29_CORRECTNESS_STANDARD_REF
    assert all(value == 0 for value in result.permission_counters.values())
    json.dumps(payload, sort_keys=True)


def test_cr139_manifest_closure_fails_when_s29_standard_is_missing() -> None:
    closure = _closure(s29_correctness_standard_ref="")
    result = validate_experiment_manifest_closure(closure)

    assert not result.passed
    assert MF_CR139_S29_STANDARD_MISSING in {reason.code for reason in result.blocked_reasons}


def test_cr139_manifest_closure_fails_when_model_hash_references_different_snapshot() -> None:
    closure = _closure(model_artifact=replace(_model(), dataset_snapshot_hash="sha256:other"))
    result = validate_experiment_manifest_closure(closure)

    assert not result.passed
    assert MF_CR139_SNAPSHOT_MISMATCH in {reason.code for reason in result.blocked_reasons}


def test_cr139_manifest_closure_requires_snapshot_split_and_model_p0_fields() -> None:
    closure = _closure(
        published_dataset_snapshot=replace(_snapshot(), content_hash=""),
        split_policy=replace(_split(), label_horizon_days=0),
        model_artifact=replace(_model(), artifact_hash=""),
    )
    result = validate_experiment_manifest_closure(closure)

    assert not result.passed
    codes = {reason.code for reason in result.blocked_reasons}
    assert MF_SCHEMA_REQUIRED_FIELD_MISSING in codes


def test_cr139_manifest_closure_blocks_forbidden_truth_and_nonzero_permissions() -> None:
    closure = _closure(
        model_artifact=replace(_model(), artifact_path="mlflow://run/model.pkl"),
        permission_counters={"lake_write": 1},
    )
    result = validate_experiment_manifest_closure(closure)

    assert not result.passed
    codes = {reason.code for reason in result.blocked_reasons}
    assert MF_FORBIDDEN_TRUTH_SOURCE in codes
    assert MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED in codes


def _closure(**overrides: object) -> ExperimentManifestClosure:
    values = {
        "closure_id": "closure-cr139-fixture",
        "run_id": "run-cr139-fixture",
        "published_dataset_snapshot": _snapshot(),
        "split_policy": _split(),
        "model_artifact": _model(),
        "feature_artifact_refs": ("features://feature-set/v1/artifact-001", "labels://label-set/v1/artifact-001"),
        "lineage_refs": ("process/stories/CR139-S29-pit-dedup-correctness-standard-LLD.md", "process/stories/CR139-S12-experiment-manifest-closure-LLD.md"),
        "metadata": {"correctness_standard": "S29 PIT/dedup"},
    }
    values.update(overrides)
    return build_experiment_manifest_closure(**values)


def _snapshot() -> PublishedDatasetSnapshotRef:
    return PublishedDatasetSnapshotRef(
        snapshot_id="published-prices-2024-01-31",
        dataset="prices",
        published_path="lake/published/prices/snapshot-2024-01-31/manifest.json",
        as_of_trade_date="2024-01-31",
        as_of_timestamp="2024-02-01T16:00:00+08:00",
        lineage_checksum="sha256:lineage",
        content_hash="sha256:dataset",
        primary_keys=("trade_date", "symbol"),
        duplicate_policy="fail_closed",
    )


def _split() -> ExperimentSplitPolicy:
    return ExperimentSplitPolicy(
        split_id="walk-forward-primary",
        train_start="2023-01-01",
        train_end="2023-12-31",
        validation_start="2024-01-02",
        validation_end="2024-01-15",
        test_start="2024-01-22",
        test_end="2024-01-31",
        cutoff_date="2024-01-15",
        embargo_days=5,
        label_horizon_days=20,
    )


def _model() -> ModelArtifactRef:
    return ModelArtifactRef(
        model_id="stage4-tree-fixture",
        artifact_path="reports/research_catalog/v1/stage4/model.json",
        artifact_hash="sha256:model",
        dataset_snapshot_hash="sha256:dataset",
        feature_artifact_refs=("features://feature-set/v1/artifact-001",),
    )
