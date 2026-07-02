from __future__ import annotations

from engine.admission_contracts import AdmissionStatus
from engine.ml_strategy_admission_gate import (
    MLAdmissionGateStatus,
    evaluate_ml_strategy_admission_gate,
)
from engine.research_manifest import (
    MLModelArtifactMetadata,
    MLPredictionArtifactMetadata,
    ModelArtifactRef,
    validate_ml_model_artifact_metadata,
    validate_ml_prediction_artifact_metadata,
)
from engine.research_production_contracts import (
    MLCVFoldSpec,
    MLLabelPolicySpec,
    MLPITFeatureMatrixContract,
    MLPurgedEmbargoCVPolicy,
    ResearchDatasetSpec,
    validate_ml_label_policy_spec,
    validate_ml_pit_feature_matrix_contract,
    validate_ml_purged_embargo_cv_policy,
)
from engine.strategy_admission_package import (
    attach_ml_gate_to_admission_package,
    map_ml_gate_status_to_admission_status,
)
from engine.training_snapshot_contract import (
    TrainingSnapshotSpec,
    build_ml_training_snapshot_metadata,
    validate_ml_training_snapshot_metadata,
)


def _dataset_spec() -> ResearchDatasetSpec:
    return ResearchDatasetSpec(
        spec_id="research-dataset-ml-20260702",
        universe="csi300",
        start_date="2020-01-01",
        end_date="2026-07-01",
        as_of="2026-07-02",
        features=("momentum_20d", "volatility_20d"),
        labels=("forward_return_20d",),
        output_snapshot_id="snapshot-ml-20260702-v1",
        feature_artifact_refs=("ml_feature_matrix_v1",),
        label_artifact_refs=("forward_return_20d",),
    )


def _pit_matrix() -> MLPITFeatureMatrixContract:
    return MLPITFeatureMatrixContract(
        matrix_id="ml_feature_matrix_v1",
        research_dataset_spec_id="research-dataset-ml-20260702",
        entity_id_field="symbol",
        decision_time_field="decision_time",
        feature_available_at_field="feature_available_at",
        feature_columns=("momentum_20d", "volatility_20d"),
        primary_keys=("trade_date", "symbol"),
        as_of="2026-07-02",
        lineage_refs=("research-dataset-ml-20260702",),
    )


def _label_policy(label_method: str = "fixed_window") -> MLLabelPolicySpec:
    return MLLabelPolicySpec(
        policy_id=f"label-policy-{label_method}",
        label_method=label_method,
        label_field="forward_return_20d",
        decision_time_field="decision_time",
        label_available_at_field="label_available_at",
        label_horizon_days=20,
        triple_barrier_spec={"upper": 0.05, "lower": -0.03} if label_method == "triple_barrier" else {},
        meta_labeling_config={"primary_model_ref": "model://primary"} if label_method == "meta_label" else {},
    )


def _cv_policy() -> MLPurgedEmbargoCVPolicy:
    return MLPurgedEmbargoCVPolicy(
        policy_id="purged-embargo-cv-v1",
        purge_window_days=20,
        embargo_days=5,
        label_horizon_days=20,
        folds=(
            MLCVFoldSpec(
                fold_id="fold-1",
                train_start="2020-01-01",
                train_end="2021-12-31",
                validation_start="2022-01-10",
                validation_end="2022-06-30",
            ),
        ),
    )


def _training_snapshot() -> TrainingSnapshotSpec:
    return TrainingSnapshotSpec(
        snapshot_id="snapshot-ml-20260702-v1",
        published_path="published://fixture/ml/snapshot-ml-20260702-v1",
        content_hash="sha256:dataset",
        as_of="2026-07-02T00:00:00+08:00",
        training_cutoff="2026-07-01T00:00:00+08:00",
        split_policy_id="purged-embargo-cv-v1",
        feature_schema_hash="sha256:feature-schema",
        lineage_refs=("ml_feature_matrix_v1", "label-policy-fixed_window", "purged-embargo-cv-v1"),
    )


def _model_metadata() -> MLModelArtifactMetadata:
    return MLModelArtifactMetadata(
        model_id="model-ml-fixture-v1",
        model_artifact_ref=ModelArtifactRef(
            model_id="model-ml-fixture-v1",
            artifact_path="artifact://fixture/model-ml-fixture-v1",
            artifact_hash="sha256:model",
            dataset_snapshot_hash="sha256:dataset",
            feature_artifact_refs=("ml_feature_matrix_v1",),
        ),
        training_snapshot_id="snapshot-ml-20260702-v1",
        pit_feature_matrix_id="ml_feature_matrix_v1",
        label_policy_id="label-policy-fixed_window",
        cv_policy_id="purged-embargo-cv-v1",
        feature_schema_hash="sha256:feature-schema",
        lineage_refs=("snapshot-ml-20260702-v1", "ml_feature_matrix_v1"),
    )


def _prediction_metadata() -> MLPredictionArtifactMetadata:
    return MLPredictionArtifactMetadata(
        prediction_id="prediction-ml-fixture-v1",
        model_id="model-ml-fixture-v1",
        prediction_timestamp_field="prediction_timestamp",
        decision_time_field="decision_time",
        entity_id_field="symbol",
        prediction_columns=("score", "rank"),
        source_feature_matrix_id="ml_feature_matrix_v1",
        lineage_refs=("model-ml-fixture-v1", "ml_feature_matrix_v1"),
    )


def _complete_evidence(label_policy: MLLabelPolicySpec | None = None) -> dict[str, object]:
    policy = label_policy or _label_policy()
    training_metadata = build_ml_training_snapshot_metadata(
        _training_snapshot(),
        pit_feature_matrix_id="ml_feature_matrix_v1",
        label_policy_id=policy.policy_id,
        cv_policy_id="purged-embargo-cv-v1",
    )
    return {
        "pit_feature_matrix": {**_pit_matrix().to_dict(), "issues": validate_ml_pit_feature_matrix_contract(_pit_matrix(), spec=_dataset_spec())},
        "label_policy": {**policy.to_dict(), "issues": validate_ml_label_policy_spec(policy)},
        "cv_policy": {**_cv_policy().to_dict(), "issues": validate_ml_purged_embargo_cv_policy(_cv_policy())},
        "training_metadata": {**training_metadata.to_dict(), "issues": validate_ml_training_snapshot_metadata(training_metadata)},
        "model_metadata": {**_model_metadata().to_dict(), "issues": validate_ml_model_artifact_metadata(_model_metadata())},
        "prediction_metadata": {**_prediction_metadata().to_dict(), "issues": validate_ml_prediction_artifact_metadata(_prediction_metadata())},
    }


def test_cr152_fixed_window_contracts_pass_static_fixture() -> None:
    assert validate_ml_pit_feature_matrix_contract(_pit_matrix(), spec=_dataset_spec()) == ()
    assert validate_ml_label_policy_spec(_label_policy()) == ()
    assert validate_ml_purged_embargo_cv_policy(_cv_policy()) == ()

    gate = evaluate_ml_strategy_admission_gate(_complete_evidence(), gate_ref="artifact://cr152/ml-gate.json")

    assert gate.status is MLAdmissionGateStatus.PASS
    assert gate.gate_present is True
    assert gate.gate_required is True
    assert gate.to_dict()["gate_status"] == "PASS"
    assert all(value == 0 for value in gate.operation_counts.values())


def test_cr152_reserved_label_methods_are_blocked_not_needs_review() -> None:
    issues = validate_ml_label_policy_spec(_label_policy("triple_barrier"))

    assert {issue["code"] for issue in issues} >= {"ml_label_method_not_implemented"}

    gate = evaluate_ml_strategy_admission_gate(_complete_evidence(_label_policy("triple_barrier")))

    assert gate.status is MLAdmissionGateStatus.BLOCKED
    assert {reason.code for reason in gate.blocked_reasons} >= {"ml_label_method_not_implemented"}


def test_cr152_purged_embargo_cv_blocks_overlap_and_short_gap() -> None:
    bad = MLPurgedEmbargoCVPolicy(
        policy_id="bad-cv",
        purge_window_days=1,
        embargo_days=5,
        label_horizon_days=20,
        folds=(
            MLCVFoldSpec(
                fold_id="fold-1",
                train_start="2020-01-01",
                train_end="2021-12-31",
                validation_start="2022-01-02",
                validation_end="2022-06-30",
            ),
        ),
    )

    codes = {issue["code"] for issue in validate_ml_purged_embargo_cv_policy(bad)}

    assert "ml_cv_purge_window_below_label_horizon" in codes
    assert "ml_cv_embargo_gap_too_small" in codes


def test_cr152_metadata_contracts_are_metadata_only_and_block_forbidden_counters() -> None:
    training_metadata = build_ml_training_snapshot_metadata(
        _training_snapshot(),
        pit_feature_matrix_id="ml_feature_matrix_v1",
        label_policy_id="label-policy-fixed_window",
        cv_policy_id="purged-embargo-cv-v1",
    )
    model_payload = _model_metadata().to_dict()
    prediction_payload = _prediction_metadata().to_dict()
    model_payload["operation_counts"] = {"model_registry_write": 1}
    prediction_payload["operation_counts"] = {"prediction_store_write": 1}
    prediction_payload["metadata_only"] = False

    assert validate_ml_training_snapshot_metadata(training_metadata) == ()
    assert {issue["code"] for issue in validate_ml_model_artifact_metadata(model_payload)} >= {
        "ml_model_artifact_operation_counter_nonzero"
    }
    assert {issue["code"] for issue in validate_ml_prediction_artifact_metadata(prediction_payload)} >= {
        "ml_prediction_artifact_metadata_only_required",
        "ml_prediction_artifact_operation_counter_nonzero",
    }


def test_cr152_ml_gate_adapter_preserves_runtime_authorization_flags() -> None:
    package = {
        "package_id": "strategy-admission:cr152:fixture",
        "admission_status": "pass",
        "evidence_refs": ("artifact://existing/admission.json",),
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }
    gate = evaluate_ml_strategy_admission_gate(
        _complete_evidence(_label_policy("meta_label")),
        operation_counts={"model_registry_write": 1},
        gate_ref="artifact://cr152/ml-gate.json",
    )

    attached = attach_ml_gate_to_admission_package(package, gate.to_dict())

    assert map_ml_gate_status_to_admission_status("BLOCKED") is AdmissionStatus.BLOCKED
    assert any(reason["field"] == "model_registry_write" for reason in attached["ml_gate_summary"]["blocked_reasons"])
    assert attached["admission_status"] == "blocked"
    assert attached["gate_present"] is True
    assert attached["gate_required"] is True
    assert attached["gate_status"] == "BLOCKED"
    assert attached["not_qmt_authorization"] is True
    assert attached["not_simulation_authorization"] is True
    assert "artifact://cr152/ml-gate.json" in attached["evidence_refs"]
