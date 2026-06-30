"""CR139 versioned feature/label/artifact layer contracts.

The module builds metadata and path previews only. It does not create
directories, write parquet files, read providers, or change catalog pointers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from market_data.lake_layout import LakeLayout, MarketDataPathError, validate_cr139_run_id


FEATURE_ARTIFACT_SCHEMA_VERSION = "feature_artifact_v1"
FEATURE_STORE_REVIEW_RECOMMENDED = "independent_feature_store_review_recommended"
FEATURE_STORE_IN_LAKE_OK = "in_lake_feature_layer_ok"


@dataclass(frozen=True, slots=True)
class LabelArtifactSpec:
    label_horizon: int
    label_available_at_field: str = "label_available_at"
    target_field: str = "forward_return"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FeatureArtifactSpec:
    feature_set_id: str
    schema_version: str
    artifact_version: str
    as_of_trade_date: str
    run_id: str
    source_view_refs: tuple[str, ...]
    lineage_checksum: str
    feature_columns: tuple[str, ...] = ()
    primary_keys: tuple[str, ...] = ("trade_date", "symbol")
    label_spec: LabelArtifactSpec | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_view_refs"] = list(self.source_view_refs)
        payload["feature_columns"] = list(self.feature_columns)
        payload["primary_keys"] = list(self.primary_keys)
        return payload


@dataclass(frozen=True, slots=True)
class FeatureArtifactValidation:
    passed: bool
    issues: tuple[dict[str, Any], ...] = ()
    safety_counters: Mapping[str, int] = field(default_factory=lambda: feature_artifact_safety_counters())

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [dict(item) for item in self.issues],
            "safety_counters": dict(self.safety_counters),
        }


@dataclass(frozen=True, slots=True)
class FeatureArtifactPlan:
    spec: FeatureArtifactSpec
    artifact_path: str
    schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION
    real_write: bool = False
    source_of_truth: str = "published_view_refs"
    safety_counters: Mapping[str, int] = field(default_factory=lambda: feature_artifact_safety_counters())
    issues: tuple[dict[str, Any], ...] = ()

    @property
    def blocked(self) -> bool:
        return bool(self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_path": self.artifact_path,
            "real_write": self.real_write,
            "source_of_truth": self.source_of_truth,
            "spec": self.spec.to_dict(),
            "safety_counters": dict(self.safety_counters),
            "issues": [dict(item) for item in self.issues],
        }


@dataclass(frozen=True, slots=True)
class FeatureStoreSwitchPolicy:
    status: str
    reasons: tuple[str, ...]
    metrics: Mapping[str, Any]
    threshold: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "metrics": dict(self.metrics),
            "threshold": dict(self.threshold),
        }


def feature_artifact_safety_counters() -> dict[str, int]:
    return {
        "provider_fetch": 0,
        "lake_write": 0,
        "catalog_write": 0,
        "manifest_append": 0,
        "pointer_advance": 0,
        "credential_read": 0,
        "runtime_operation": 0,
        "dependency_change": 0,
    }


def validate_feature_artifact_spec(spec: FeatureArtifactSpec) -> FeatureArtifactValidation:
    issues: list[dict[str, Any]] = []
    required = {
        "feature_set_id": spec.feature_set_id,
        "schema_version": spec.schema_version,
        "artifact_version": spec.artifact_version,
        "as_of_trade_date": spec.as_of_trade_date,
        "run_id": spec.run_id,
        "lineage_checksum": spec.lineage_checksum,
    }
    for field_name, value in required.items():
        if not str(value or "").strip():
            issues.append({"code": "required_field_missing", "field": field_name})
    if not spec.source_view_refs:
        issues.append({"code": "source_view_refs_missing", "field": "source_view_refs"})
    if not spec.feature_columns:
        issues.append({"code": "feature_columns_missing", "field": "feature_columns"})
    if not validate_cr139_run_id(spec.run_id):
        issues.append({"code": "run_id_invalid", "field": "run_id", "value": spec.run_id})
    if spec.label_spec is not None:
        if spec.label_spec.label_horizon <= 0:
            issues.append({"code": "label_horizon_invalid", "field": "label_horizon"})
        if not spec.label_spec.label_available_at_field:
            issues.append({"code": "label_available_at_field_missing", "field": "label_available_at_field"})
    return FeatureArtifactValidation(passed=not issues, issues=tuple(issues))


def build_feature_artifact_plan(
    layout: LakeLayout,
    spec: FeatureArtifactSpec,
) -> FeatureArtifactPlan:
    validation = validate_feature_artifact_spec(spec)
    try:
        path = layout.feature_artifact_path(
            spec.feature_set_id,
            spec.schema_version,
            spec.artifact_version,
            as_of_trade_date=spec.as_of_trade_date,
            run_id=spec.run_id,
        )
        artifact_path = str(path)
        issues = tuple(validation.issues)
    except MarketDataPathError as exc:
        artifact_path = ""
        issues = (*validation.issues, {"code": "artifact_path_invalid", "reason": str(exc)})
    return FeatureArtifactPlan(
        spec=spec,
        artifact_path=artifact_path,
        real_write=False,
        issues=issues,
        safety_counters=validation.safety_counters,
    )


def feature_store_switch_policy(
    metrics: Mapping[str, Any],
    *,
    max_feature_sets: int = 100,
    max_daily_artifacts: int = 1000,
    max_schema_versions: int = 20,
) -> FeatureStoreSwitchPolicy:
    reasons: list[str] = []
    if int(metrics.get("feature_sets", 0)) > max_feature_sets:
        reasons.append("feature_set_count_threshold_exceeded")
    if int(metrics.get("daily_artifacts", 0)) > max_daily_artifacts:
        reasons.append("daily_artifact_count_threshold_exceeded")
    if int(metrics.get("schema_versions", 0)) > max_schema_versions:
        reasons.append("schema_version_count_threshold_exceeded")
    status = FEATURE_STORE_REVIEW_RECOMMENDED if reasons else FEATURE_STORE_IN_LAKE_OK
    return FeatureStoreSwitchPolicy(
        status=status,
        reasons=tuple(reasons),
        metrics=dict(metrics),
        threshold={
            "max_feature_sets": max_feature_sets,
            "max_daily_artifacts": max_daily_artifacts,
            "max_schema_versions": max_schema_versions,
        },
    )


def source_refs_from_mapping(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    refs = []
    for row in rows:
        ref = row.get("source_view_ref") or row.get("view_ref") or row.get("manifest_ref")
        if ref:
            refs.append(str(ref))
    return tuple(refs)


__all__ = [
    "FEATURE_ARTIFACT_SCHEMA_VERSION",
    "FEATURE_STORE_IN_LAKE_OK",
    "FEATURE_STORE_REVIEW_RECOMMENDED",
    "FeatureArtifactPlan",
    "FeatureArtifactSpec",
    "FeatureArtifactValidation",
    "FeatureStoreSwitchPolicy",
    "LabelArtifactSpec",
    "build_feature_artifact_plan",
    "feature_artifact_safety_counters",
    "feature_store_switch_policy",
    "source_refs_from_mapping",
    "validate_feature_artifact_spec",
]
