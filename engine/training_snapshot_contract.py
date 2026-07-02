"""CR139 training snapshot cutoff contracts.

This module defines static/fixture validation helpers only. It never reads a
real lake, publishes catalog pointers, starts runtime, or writes artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.serialization import json_safe
from engine.research_manifest import ExperimentManifestClosure


TRAINING_SNAPSHOT_SCHEMA = "cr139_training_snapshot_cutoff_v1"
ML_TRAINING_SNAPSHOT_METADATA_SCHEMA = "ml_training_snapshot_metadata_v1"
STATUS_PASS = "pass"
STATUS_BLOCKED = "blocked"
CR152_ML_FORBIDDEN_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            *FORBIDDEN_OPERATION_COUNTERS,
            "real_model_training",
            "real_data_validation",
            "feature_store_write",
            "label_store_write",
            "model_store_write",
            "model_registry_write",
            "prediction_store_write",
            "catalog_pointer_mutation",
        )
    )
)


@dataclass(frozen=True, slots=True)
class TrainingSnapshotSpec:
    snapshot_id: str
    published_path: str
    content_hash: str
    as_of: str
    training_cutoff: str
    split_policy_id: str
    feature_schema_hash: str
    lineage_refs: tuple[str, ...]
    published_only: bool = True
    source_of_truth: str = "published_dataset_snapshot"
    permission_counters: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = TRAINING_SNAPSHOT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class TrainingSnapshotValidation:
    status: str
    issues: tuple[Mapping[str, Any], ...]
    operation_counts: Mapping[str, int]
    spec: TrainingSnapshotSpec

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "issues": [dict(item) for item in self.issues],
            "operation_counts": dict(self.operation_counts),
            "spec": self.spec.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class MLTrainingSnapshotMetadata:
    training_snapshot_id: str
    pit_feature_matrix_id: str
    label_policy_id: str
    cv_policy_id: str
    feature_schema_hash: str
    lineage_refs: tuple[str, ...]
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = ML_TRAINING_SNAPSHOT_METADATA_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


def build_training_snapshot_spec(
    *,
    closure: ExperimentManifestClosure | Mapping[str, Any],
    feature_schema_hash: str,
    lineage_refs: Sequence[str],
) -> TrainingSnapshotSpec:
    data = closure.to_dict() if hasattr(closure, "to_dict") else dict(closure)
    snapshot = dict(data.get("published_dataset_snapshot") or {})
    split = dict(data.get("split_policy") or {})
    return TrainingSnapshotSpec(
        snapshot_id=str(snapshot.get("snapshot_id") or ""),
        published_path=str(snapshot.get("published_path") or ""),
        content_hash=str(snapshot.get("content_hash") or ""),
        as_of=str(snapshot.get("as_of_timestamp") or ""),
        training_cutoff=str(split.get("cutoff_date") or ""),
        split_policy_id=str(split.get("split_id") or ""),
        feature_schema_hash=str(feature_schema_hash or ""),
        lineage_refs=tuple(str(item) for item in lineage_refs),
        permission_counters=_zero_permission_counters(),
    )


def build_ml_training_snapshot_metadata(
    snapshot: TrainingSnapshotSpec | Mapping[str, Any],
    *,
    pit_feature_matrix_id: str,
    label_policy_id: str,
    cv_policy_id: str,
) -> MLTrainingSnapshotMetadata:
    value = snapshot if isinstance(snapshot, TrainingSnapshotSpec) else _spec_from_mapping(snapshot)
    return MLTrainingSnapshotMetadata(
        training_snapshot_id=value.snapshot_id,
        pit_feature_matrix_id=str(pit_feature_matrix_id or ""),
        label_policy_id=str(label_policy_id or ""),
        cv_policy_id=str(cv_policy_id or ""),
        feature_schema_hash=value.feature_schema_hash,
        lineage_refs=value.lineage_refs,
        operation_counts=_zero_ml_permission_counters(),
    )


def validate_training_snapshot_cutoff(spec: TrainingSnapshotSpec | Mapping[str, Any]) -> TrainingSnapshotValidation:
    value = spec if isinstance(spec, TrainingSnapshotSpec) else _spec_from_mapping(spec)
    issues: list[dict[str, Any]] = []
    for field_name in ("snapshot_id", "published_path", "content_hash", "as_of", "training_cutoff", "split_policy_id", "feature_schema_hash", "lineage_refs"):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "training_snapshot_required_field_missing", "field": field_name})
    mutable_text = " ".join([value.snapshot_id, value.published_path, value.source_of_truth]).lower()
    if "latest" in mutable_text or "current" in mutable_text:
        issues.append({"code": "mutable_snapshot_ref_forbidden", "field": "snapshot_id"})
    if value.published_only is not True:
        issues.append({"code": "published_only_required", "field": "published_only"})
    cutoff = pd.to_datetime(value.training_cutoff, errors="coerce", utc=True)
    as_of = pd.to_datetime(value.as_of, errors="coerce", utc=True)
    if pd.isna(cutoff) or pd.isna(as_of):
        issues.append({"code": "training_cutoff_or_as_of_unparseable", "field": "training_cutoff"})
    elif cutoff > as_of:
        issues.append({"code": "training_cutoff_after_as_of", "field": "training_cutoff"})
    counters = _normalise_counters(value.permission_counters)
    issues.extend({"code": "permission_counter_nonzero", "field": key, "value": val} for key, val in counters.items() if val != 0)
    return TrainingSnapshotValidation(
        status=STATUS_PASS if not issues else STATUS_BLOCKED,
        issues=tuple(issues),
        operation_counts=counters,
        spec=value,
    )


def validate_ml_training_snapshot_metadata(metadata: MLTrainingSnapshotMetadata | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = metadata if isinstance(metadata, MLTrainingSnapshotMetadata) else _ml_metadata_from_mapping(metadata)
    issues: list[dict[str, Any]] = []
    for field_name in (
        "training_snapshot_id",
        "pit_feature_matrix_id",
        "label_policy_id",
        "cv_policy_id",
        "feature_schema_hash",
        "lineage_refs",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "ml_training_snapshot_metadata_required_field_missing", "field": field_name})
    if not value.feature_schema_hash.startswith("sha256:"):
        issues.append({"code": "ml_training_snapshot_feature_schema_hash_invalid", "field": "feature_schema_hash"})
    counters = _normalise_ml_counters(value.operation_counts)
    issues.extend({"code": "ml_training_snapshot_operation_counter_nonzero", "field": key, "value": val} for key, val in counters.items() if val != 0)
    return tuple(issues)


def _spec_from_mapping(data: Mapping[str, Any]) -> TrainingSnapshotSpec:
    return TrainingSnapshotSpec(
        snapshot_id=str(data.get("snapshot_id") or ""),
        published_path=str(data.get("published_path") or ""),
        content_hash=str(data.get("content_hash") or ""),
        as_of=str(data.get("as_of") or ""),
        training_cutoff=str(data.get("training_cutoff") or ""),
        split_policy_id=str(data.get("split_policy_id") or ""),
        feature_schema_hash=str(data.get("feature_schema_hash") or ""),
        lineage_refs=tuple(str(item) for item in data.get("lineage_refs") or ()),
        published_only=bool(data.get("published_only", True)),
        source_of_truth=str(data.get("source_of_truth") or "published_dataset_snapshot"),
        permission_counters=_normalise_counters(data.get("permission_counters")),
    )


def _ml_metadata_from_mapping(data: Mapping[str, Any]) -> MLTrainingSnapshotMetadata:
    return MLTrainingSnapshotMetadata(
        training_snapshot_id=str(data.get("training_snapshot_id") or ""),
        pit_feature_matrix_id=str(data.get("pit_feature_matrix_id") or ""),
        label_policy_id=str(data.get("label_policy_id") or ""),
        cv_policy_id=str(data.get("cv_policy_id") or ""),
        feature_schema_hash=str(data.get("feature_schema_hash") or ""),
        lineage_refs=tuple(str(item) for item in data.get("lineage_refs") or ()),
        operation_counts=_normalise_ml_counters(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or ML_TRAINING_SNAPSHOT_METADATA_SCHEMA),
    )


def _normalise_counters(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in FORBIDDEN_OPERATION_COUNTERS}


def _normalise_ml_counters(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in CR152_ML_FORBIDDEN_OPERATION_COUNTERS}


def _zero_permission_counters() -> dict[str, int]:
    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


def _zero_ml_permission_counters() -> dict[str, int]:
    return {key: 0 for key in CR152_ML_FORBIDDEN_OPERATION_COUNTERS}


__all__ = [
    "ML_TRAINING_SNAPSHOT_METADATA_SCHEMA",
    "MLTrainingSnapshotMetadata",
    "CR152_ML_FORBIDDEN_OPERATION_COUNTERS",
    "TRAINING_SNAPSHOT_SCHEMA",
    "TrainingSnapshotSpec",
    "TrainingSnapshotValidation",
    "build_ml_training_snapshot_metadata",
    "build_training_snapshot_spec",
    "validate_ml_training_snapshot_metadata",
    "validate_training_snapshot_cutoff",
]
