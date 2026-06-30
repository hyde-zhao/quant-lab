from pathlib import Path

from market_data.features import (
    FEATURE_STORE_REVIEW_RECOMMENDED,
    FeatureArtifactSpec,
    LabelArtifactSpec,
    build_feature_artifact_plan,
    feature_store_switch_policy,
    validate_feature_artifact_spec,
)
from market_data.lake_layout import LakeLayout, build_cr139_run_id


def _run_id() -> str:
    return build_cr139_run_id(
        dataset="alpha_features",
        source="panel",
        as_of_date="2026-05-26",
        purpose="features",
    )


def _spec(**overrides: object) -> FeatureArtifactSpec:
    payload = {
        "feature_set_id": "alpha_core",
        "schema_version": "v1",
        "artifact_version": "release_20260526",
        "as_of_trade_date": "2026-05-26",
        "run_id": _run_id(),
        "source_view_refs": ("published://prices/v1", "published://trade_calendar/v1"),
        "lineage_checksum": "lineage-fixture",
        "feature_columns": ("momentum_20d", "volatility_20d"),
        "label_spec": LabelArtifactSpec(label_horizon=20),
    }
    payload.update(overrides)
    return FeatureArtifactSpec(**payload)  # type: ignore[arg-type]


def test_s11_feature_artifact_plan_uses_versioned_features_path_without_write(tmp_path: Path) -> None:
    layout = LakeLayout(tmp_path)
    plan = build_feature_artifact_plan(layout, _spec())

    assert not plan.blocked
    assert plan.real_write is False
    assert "features/feature_set=alpha_core/schema_version=v1" in plan.artifact_path
    assert "artifact_version=release_20260526/as_of_trade_date=20260526" in plan.artifact_path
    assert f"run_id={_run_id()}" in plan.artifact_path
    assert plan.spec.label_spec is not None
    assert plan.spec.label_spec.label_available_at_field == "label_available_at"
    assert all(value == 0 for value in plan.safety_counters.values())
    assert not list(tmp_path.rglob("*.parquet"))


def test_s11_feature_artifact_validation_blocks_missing_lineage_and_refs() -> None:
    validation = validate_feature_artifact_spec(
        _spec(source_view_refs=(), lineage_checksum="", feature_columns=())
    )

    assert validation.passed is False
    assert {issue["code"] for issue in validation.issues} >= {
        "required_field_missing",
        "source_view_refs_missing",
        "feature_columns_missing",
    }
    assert all(value == 0 for value in validation.safety_counters.values())


def test_s11_feature_artifact_validation_keeps_label_guard_contract() -> None:
    validation = validate_feature_artifact_spec(_spec(label_spec=LabelArtifactSpec(label_horizon=5)))

    assert validation.passed is True


def test_s11_feature_store_switch_policy_records_def_139_01_review_condition() -> None:
    policy = feature_store_switch_policy(
        {"feature_sets": 101, "daily_artifacts": 1001, "schema_versions": 21}
    )

    assert policy.status == FEATURE_STORE_REVIEW_RECOMMENDED
    assert set(policy.reasons) == {
        "feature_set_count_threshold_exceeded",
        "daily_artifact_count_threshold_exceeded",
        "schema_version_count_threshold_exceeded",
    }
