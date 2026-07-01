from __future__ import annotations

from engine.research_production_contracts import (
    LeakagePolicy,
    ResearchDatasetSpec,
    audit_research_production_contract,
    research_dataset_request_from_spec,
    research_dataset_spec_fingerprint,
    validate_research_dataset_spec,
)
from engine.training_snapshot_contract import TrainingSnapshotSpec
from market_data.features import FeatureArtifactSpec, LabelArtifactSpec
from market_data.lake_layout import build_cr139_run_id


def _run_id() -> str:
    return build_cr139_run_id(
        dataset="alpha_features",
        source="panel",
        as_of_date="2026-05-28",
        purpose="features",
    )


def _spec(**overrides: object) -> ResearchDatasetSpec:
    payload = {
        "spec_id": "research-dataset-alpha-core-20260528",
        "universe": "csi300",
        "start_date": "2020-01-01",
        "end_date": "2026-05-28",
        "as_of": "2026-05-28",
        "features": ("momentum_20d", "volatility_20d"),
        "labels": ("forward_return_20d",),
        "feature_artifact_refs": ("alpha_core",),
        "label_artifact_refs": ("forward_return_20d",),
        "output_snapshot_id": "snapshot-alpha-core-20260528-v1",
        "tradability_filters": {"require_tradable": True},
    }
    payload.update(overrides)
    return ResearchDatasetSpec(**payload)  # type: ignore[arg-type]


def _feature_artifact(**overrides: object) -> FeatureArtifactSpec:
    payload = {
        "feature_set_id": "alpha_core",
        "schema_version": "v1",
        "artifact_version": "release_20260528",
        "as_of_trade_date": "2026-05-28",
        "run_id": _run_id(),
        "source_view_refs": ("published://prices/1.0", "published://trade_status/1.0"),
        "lineage_checksum": "sha256:feature-fixture",
        "feature_columns": ("momentum_20d", "volatility_20d"),
        "primary_keys": ("trade_date", "symbol"),
        "label_spec": LabelArtifactSpec(label_horizon=20),
    }
    payload.update(overrides)
    return FeatureArtifactSpec(**payload)  # type: ignore[arg-type]


def _training_snapshot(**overrides: object) -> TrainingSnapshotSpec:
    payload = {
        "snapshot_id": "snapshot-alpha-core-20260528-v1",
        "published_path": "published://research-datasets/alpha-core/20260528/v1",
        "content_hash": "sha256:dataset-fixture",
        "as_of": "2026-05-28T15:00:00+08:00",
        "training_cutoff": "2026-05-28T00:00:00+08:00",
        "split_policy_id": "walk-forward-2020-2026-v1",
        "feature_schema_hash": "sha256:feature-schema",
        "lineage_refs": ("published://prices/1.0", "feature://alpha_core/v1"),
    }
    payload.update(overrides)
    return TrainingSnapshotSpec(**payload)  # type: ignore[arg-type]


def test_cr147_research_production_contract_audit_passes_without_runtime_side_effects() -> None:
    audit = audit_research_production_contract(
        _spec(),
        feature_artifacts=(_feature_artifact(),),
        training_snapshot=_training_snapshot(),
    )

    assert audit.passed
    assert audit.status == "pass"
    assert audit.issues == ()
    assert audit.research_dataset_request["universe"] == "csi300"
    assert audit.research_dataset_request["forward_return_horizon"] == 20
    assert audit.asset_refs["existing_contracts"] == [
        "engine.research_dataset.ResearchDatasetRequest",
        "market_data.features.artifacts.FeatureArtifactSpec",
        "engine.training_snapshot_contract.TrainingSnapshotSpec",
        "engine.research_manifest.ExperimentManifestClosure",
    ]
    assert all(value == 0 for value in audit.operation_counts.values())


def test_cr147_research_dataset_spec_fingerprint_is_stable() -> None:
    first = research_dataset_spec_fingerprint(_spec())
    second = research_dataset_spec_fingerprint(_spec())

    assert first == second
    assert first.startswith("sha256:")


def test_cr147_research_dataset_request_maps_existing_builder_contract() -> None:
    request = research_dataset_request_from_spec(
        _spec(leakage_policy=LeakagePolicy(label_horizon_days=5))
    )

    assert request.universe == "csi300"
    assert request.start_date == "2020-01-01"
    assert request.end_date == "2026-05-28"
    assert request.forward_return_horizon == 5
    assert request.report_kind == "research_dataset_spec"


def test_cr147_audit_accepts_mapping_feature_artifact_with_label_mapping() -> None:
    audit = audit_research_production_contract(
        _spec(),
        feature_artifacts=(_feature_artifact().to_dict(),),
    )

    assert audit.passed
    assert audit.asset_refs["feature_artifacts"] == ["alpha_core"]
    assert audit.issues == ()


def test_cr147_research_dataset_spec_blocks_mutable_or_non_pit_sources() -> None:
    issues = validate_research_dataset_spec(
        _spec(
            source_of_truth="canonical_latest_files",
            output_snapshot_id="current",
            leakage_policy=LeakagePolicy(require_feature_available_before_decision=False),
        )
    )

    codes = {issue["code"] for issue in issues}
    assert {
        "research_dataset_spec_source_of_truth_forbidden",
        "mutable_output_snapshot_id_forbidden",
        "leakage_policy_feature_decision_gate_required",
    }.issubset(codes)


def test_cr147_audit_blocks_feature_artifact_key_mismatch_and_bad_snapshot() -> None:
    audit = audit_research_production_contract(
        _spec(),
        feature_artifacts=(_feature_artifact(primary_keys=("symbol",)),),
        training_snapshot=_training_snapshot(training_cutoff="2026-05-29T00:00:00+08:00"),
    )

    codes = {issue["code"] for issue in audit.issues}
    assert audit.status == "blocked"
    assert "feature_artifact_primary_keys_mismatch" in codes
    assert "training_cutoff_after_as_of" in codes
