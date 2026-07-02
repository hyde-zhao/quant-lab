"""CR147 research production foundation contracts.

This module is deliberately metadata-only. It does not read a real lake, write
feature artifacts, fetch providers, touch NAS, run QMT, or start trading.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
import hashlib
import json
from typing import Any, Mapping, Sequence

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.research_dataset import ResearchDatasetRequest
from engine.training_snapshot_contract import TrainingSnapshotSpec, validate_training_snapshot_cutoff
from market_data.features.artifacts import FeatureArtifactSpec, LabelArtifactSpec, validate_feature_artifact_spec


RESEARCH_DATASET_SPEC_SCHEMA = "research_dataset_spec_v1"
RESEARCH_PRODUCTION_AUDIT_SCHEMA = "research_production_foundation_audit_v1"
STATUS_PASS = "pass"
STATUS_BLOCKED = "blocked"
ASSET_MAP_SCHEMA = "research_production_asset_map_v1"
ML_PIT_FEATURE_MATRIX_SCHEMA = "ml_pit_feature_matrix_contract_v1"
ML_LABEL_POLICY_SCHEMA = "ml_label_policy_v1"
ML_PURGED_EMBARGO_CV_SCHEMA = "ml_purged_embargo_cv_policy_v1"
ML_LABEL_METHOD_FIXED_WINDOW = "fixed_window"
ML_LABEL_METHOD_TRIPLE_BARRIER = "triple_barrier"
ML_LABEL_METHOD_META_LABEL = "meta_label"
ML_SUPPORTED_LABEL_METHODS = (ML_LABEL_METHOD_FIXED_WINDOW,)
ML_RESERVED_LABEL_METHODS = (ML_LABEL_METHOD_TRIPLE_BARRIER, ML_LABEL_METHOD_META_LABEL)
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
class LeakagePolicy:
    decision_time_field: str = "decision_time"
    feature_available_at_field: str = "available_at"
    label_available_at_field: str = "label_available_at"
    label_horizon_days: int = 20
    require_feature_available_before_decision: bool = True
    require_label_after_decision: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResearchDatasetSpec:
    spec_id: str
    universe: str
    start_date: str
    end_date: str
    as_of: str
    features: tuple[str, ...]
    labels: tuple[str, ...]
    output_snapshot_id: str
    feature_artifact_refs: tuple[str, ...] = ()
    label_artifact_refs: tuple[str, ...] = ()
    event_filters: Mapping[str, Any] = field(default_factory=dict)
    tradability_filters: Mapping[str, Any] = field(default_factory=dict)
    rebalance_calendar: str = "trade_calendar"
    primary_keys: tuple[str, ...] = ("trade_date", "symbol")
    source_of_truth: str = "published_current_truth"
    leakage_policy: LeakagePolicy = field(default_factory=LeakagePolicy)
    schema_version: str = RESEARCH_DATASET_SPEC_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["features"] = list(self.features)
        payload["labels"] = list(self.labels)
        payload["feature_artifact_refs"] = list(self.feature_artifact_refs)
        payload["label_artifact_refs"] = list(self.label_artifact_refs)
        payload["primary_keys"] = list(self.primary_keys)
        payload["leakage_policy"] = self.leakage_policy.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ResearchDatasetSnapshotSpec:
    snapshot_id: str
    research_dataset_spec_id: str
    content_hash: str
    as_of: str
    universe: str
    feature_artifact_refs: tuple[str, ...]
    label_artifact_refs: tuple[str, ...]
    source_snapshot_refs: tuple[str, ...]
    primary_keys: tuple[str, ...]
    lineage_refs: tuple[str, ...]
    output_ref: str
    source_of_truth: str = "research_dataset_spec_snapshot"
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = "research_dataset_snapshot_spec_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "research_dataset_spec_id": self.research_dataset_spec_id,
            "content_hash": self.content_hash,
            "as_of": self.as_of,
            "universe": self.universe,
            "feature_artifact_refs": list(self.feature_artifact_refs),
            "label_artifact_refs": list(self.label_artifact_refs),
            "source_snapshot_refs": list(self.source_snapshot_refs),
            "primary_keys": list(self.primary_keys),
            "lineage_refs": list(self.lineage_refs),
            "output_ref": self.output_ref,
            "source_of_truth": self.source_of_truth,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class FeatureAvailabilityContract:
    feature_set_id: str
    decision_time_field: str
    feature_available_at_field: str
    label_available_at_field: str
    label_horizon_days: int
    primary_keys: tuple[str, ...]
    required_columns: tuple[str, ...]
    enforcement_ref: str = "engine.factor_model_validation.label_cutoff_gate"
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = "feature_availability_contract_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "feature_set_id": self.feature_set_id,
            "decision_time_field": self.decision_time_field,
            "feature_available_at_field": self.feature_available_at_field,
            "label_available_at_field": self.label_available_at_field,
            "label_horizon_days": self.label_horizon_days,
            "primary_keys": list(self.primary_keys),
            "required_columns": list(self.required_columns),
            "enforcement_ref": self.enforcement_ref,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class MLPITFeatureMatrixContract:
    matrix_id: str
    research_dataset_spec_id: str
    entity_id_field: str
    decision_time_field: str
    feature_available_at_field: str
    feature_columns: tuple[str, ...]
    primary_keys: tuple[str, ...]
    as_of: str
    lineage_refs: tuple[str, ...]
    source_snapshot_refs: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = ML_PIT_FEATURE_MATRIX_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["feature_columns"] = list(self.feature_columns)
        payload["primary_keys"] = list(self.primary_keys)
        payload["lineage_refs"] = list(self.lineage_refs)
        payload["source_snapshot_refs"] = list(self.source_snapshot_refs)
        payload["operation_counts"] = dict(self.operation_counts)
        return payload


@dataclass(frozen=True, slots=True)
class MLLabelPolicySpec:
    policy_id: str
    label_method: str
    label_field: str
    decision_time_field: str
    label_available_at_field: str
    label_horizon_days: int
    leakage_guard_ref: str = "engine.research_production_contracts.validate_ml_label_policy_spec"
    triple_barrier_spec: Mapping[str, Any] = field(default_factory=dict)
    meta_labeling_config: Mapping[str, Any] = field(default_factory=dict)
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = ML_LABEL_POLICY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["triple_barrier_spec"] = dict(self.triple_barrier_spec)
        payload["meta_labeling_config"] = dict(self.meta_labeling_config)
        payload["operation_counts"] = dict(self.operation_counts)
        return payload


@dataclass(frozen=True, slots=True)
class MLCVFoldSpec:
    fold_id: str
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str = ""
    test_end: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MLPurgedEmbargoCVPolicy:
    policy_id: str
    folds: tuple[MLCVFoldSpec, ...]
    purge_window_days: int
    embargo_days: int
    label_horizon_days: int
    decision_time_field: str = "decision_time"
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = ML_PURGED_EMBARGO_CV_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_id": self.policy_id,
            "folds": [fold.to_dict() for fold in self.folds],
            "purge_window_days": self.purge_window_days,
            "embargo_days": self.embargo_days,
            "label_horizon_days": self.label_horizon_days,
            "decision_time_field": self.decision_time_field,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class ResearchProductionAudit:
    status: str
    spec: ResearchDatasetSpec
    spec_fingerprint: str
    research_dataset_request: Mapping[str, Any]
    issues: tuple[Mapping[str, Any], ...]
    operation_counts: Mapping[str, int]
    asset_refs: Mapping[str, Any]
    schema_version: str = RESEARCH_PRODUCTION_AUDIT_SCHEMA

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "spec": self.spec.to_dict(),
            "spec_fingerprint": self.spec_fingerprint,
            "research_dataset_request": dict(self.research_dataset_request),
            "issues": [dict(item) for item in self.issues],
            "operation_counts": dict(self.operation_counts),
            "asset_refs": dict(self.asset_refs),
        }


@dataclass(frozen=True, slots=True)
class ResearchProductionGap:
    gap_id: str
    severity: str
    description: str
    phase: str
    gate_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ResearchProductionAsset:
    asset_id: str
    layer: str
    module: str
    object_names: tuple[str, ...]
    role: str
    maturity: str
    current_contracts: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    gaps: tuple[ResearchProductionGap, ...] = ()
    downstream_phase: str = "Phase 2"

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "layer": self.layer,
            "module": self.module,
            "object_names": list(self.object_names),
            "role": self.role,
            "maturity": self.maturity,
            "current_contracts": list(self.current_contracts),
            "required_capabilities": list(self.required_capabilities),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "downstream_phase": self.downstream_phase,
        }


@dataclass(frozen=True, slots=True)
class ResearchProductionAssetMap:
    assets: tuple[ResearchProductionAsset, ...]
    operation_counts: Mapping[str, int]
    schema_version: str = ASSET_MAP_SCHEMA

    @property
    def gap_count(self) -> int:
        return sum(len(asset.gaps) for asset in self.assets)

    @property
    def gate_required_gap_count(self) -> int:
        return sum(1 for asset in self.assets for gap in asset.gaps if gap.gate_required)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "assets": [asset.to_dict() for asset in self.assets],
            "asset_count": len(self.assets),
            "gap_count": self.gap_count,
            "gate_required_gap_count": self.gate_required_gap_count,
            "operation_counts": dict(self.operation_counts),
        }


def validate_research_dataset_spec(spec: ResearchDatasetSpec | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
    issues: list[dict[str, Any]] = []
    for field_name in ("spec_id", "universe", "start_date", "end_date", "as_of", "output_snapshot_id"):
        if not str(getattr(value, field_name) or "").strip():
            issues.append({"code": "research_dataset_spec_required_field_missing", "field": field_name})
    if not value.features:
        issues.append({"code": "research_dataset_spec_features_missing", "field": "features"})
    if not value.labels:
        issues.append({"code": "research_dataset_spec_labels_missing", "field": "labels"})
    if not value.primary_keys:
        issues.append({"code": "research_dataset_spec_primary_keys_missing", "field": "primary_keys"})
    if "raw" in value.source_of_truth or "canonical" in value.source_of_truth:
        issues.append({"code": "research_dataset_spec_source_of_truth_forbidden", "field": "source_of_truth"})
    if "latest" in value.output_snapshot_id.lower() or "current" in value.output_snapshot_id.lower():
        issues.append({"code": "mutable_output_snapshot_id_forbidden", "field": "output_snapshot_id"})
    issues.extend(_date_order_issues(value))
    issues.extend(_leakage_policy_issues(value.leakage_policy))
    return tuple(issues)


def research_dataset_request_from_spec(spec: ResearchDatasetSpec) -> ResearchDatasetRequest:
    return ResearchDatasetRequest(
        start_date=spec.start_date,
        end_date=spec.end_date,
        universe=spec.universe,
        forward_return_horizon=spec.leakage_policy.label_horizon_days,
        analysis_mode="research",
        report_kind="research_dataset_spec",
    )


def build_research_dataset_snapshot_spec(
    spec: ResearchDatasetSpec | Mapping[str, Any],
    *,
    feature_artifacts: Sequence[FeatureArtifactSpec | Mapping[str, Any]] = (),
    source_snapshot_refs: Sequence[str] = (),
) -> ResearchDatasetSnapshotSpec:
    value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
    feature_refs = _feature_refs_from_inputs(value, feature_artifacts)
    label_refs = tuple(value.label_artifact_refs or value.labels)
    lineage_refs = tuple(dict.fromkeys((*source_snapshot_refs, *feature_refs, *label_refs)))
    content_payload = {
        "spec": value.to_dict(),
        "feature_artifact_refs": list(feature_refs),
        "label_artifact_refs": list(label_refs),
        "source_snapshot_refs": [str(item) for item in source_snapshot_refs],
    }
    content_hash = _stable_sha256(content_payload)
    return ResearchDatasetSnapshotSpec(
        snapshot_id=value.output_snapshot_id,
        research_dataset_spec_id=value.spec_id,
        content_hash=content_hash,
        as_of=value.as_of,
        universe=value.universe,
        feature_artifact_refs=feature_refs,
        label_artifact_refs=label_refs,
        source_snapshot_refs=tuple(str(item) for item in source_snapshot_refs),
        primary_keys=value.primary_keys,
        lineage_refs=lineage_refs,
        output_ref=f"research-dataset-snapshot://{value.output_snapshot_id}",
        operation_counts=_zero_operation_counts(),
    )


def build_feature_availability_contract(
    spec: ResearchDatasetSpec | Mapping[str, Any],
    feature_artifact: FeatureArtifactSpec | Mapping[str, Any],
) -> FeatureAvailabilityContract:
    value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
    artifact = feature_artifact if isinstance(feature_artifact, FeatureArtifactSpec) else _feature_artifact_from_mapping(feature_artifact)
    policy = value.leakage_policy
    required_columns = tuple(
        dict.fromkeys(
            (
                *value.primary_keys,
                policy.decision_time_field,
                policy.feature_available_at_field,
                policy.label_available_at_field,
                *artifact.feature_columns,
            )
        )
    )
    return FeatureAvailabilityContract(
        feature_set_id=artifact.feature_set_id,
        decision_time_field=policy.decision_time_field,
        feature_available_at_field=policy.feature_available_at_field,
        label_available_at_field=policy.label_available_at_field,
        label_horizon_days=policy.label_horizon_days,
        primary_keys=value.primary_keys,
        required_columns=required_columns,
        operation_counts=_zero_operation_counts(),
    )


def validate_feature_availability_contract(
    contract: FeatureAvailabilityContract | Mapping[str, Any],
    *,
    spec: ResearchDatasetSpec | Mapping[str, Any] | None = None,
    feature_artifact: FeatureArtifactSpec | Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    value = contract if isinstance(contract, FeatureAvailabilityContract) else _feature_availability_contract_from_mapping(contract)
    issues: list[dict[str, Any]] = []
    for field_name in (
        "feature_set_id",
        "decision_time_field",
        "feature_available_at_field",
        "label_available_at_field",
        "primary_keys",
        "required_columns",
        "enforcement_ref",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "feature_availability_required_field_missing", "field": field_name})
    if value.label_horizon_days <= 0:
        issues.append({"code": "feature_availability_label_horizon_invalid", "field": "label_horizon_days"})
    required = {
        *value.primary_keys,
        value.decision_time_field,
        value.feature_available_at_field,
        value.label_available_at_field,
    }
    missing_columns = sorted(required - set(value.required_columns))
    if missing_columns:
        issues.append({"code": "feature_availability_required_columns_missing", "missing_columns": missing_columns})
    if value.enforcement_ref != "engine.factor_model_validation.label_cutoff_gate":
        issues.append({"code": "feature_availability_enforcement_ref_invalid", "field": "enforcement_ref"})
    for key, count in _normalise_ml_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "feature_availability_operation_counter_nonzero", "field": key, "value": count})
    if spec is not None:
        spec_value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
        if value.feature_set_id not in set(spec_value.feature_artifact_refs):
            issues.append(
                {
                    "code": "feature_availability_feature_ref_not_in_spec",
                    "feature_set_id": value.feature_set_id,
                    "expected_refs": list(spec_value.feature_artifact_refs),
                }
            )
        if value.label_horizon_days != spec_value.leakage_policy.label_horizon_days:
            issues.append(
                {
                    "code": "feature_availability_label_horizon_mismatch",
                    "expected": spec_value.leakage_policy.label_horizon_days,
                    "actual": value.label_horizon_days,
                }
            )
    if feature_artifact is not None:
        artifact = feature_artifact if isinstance(feature_artifact, FeatureArtifactSpec) else _feature_artifact_from_mapping(feature_artifact)
        if value.feature_set_id != artifact.feature_set_id:
            issues.append(
                {
                    "code": "feature_availability_artifact_id_mismatch",
                    "expected": artifact.feature_set_id,
                    "actual": value.feature_set_id,
                }
            )
        missing_features = sorted(set(artifact.feature_columns) - set(value.required_columns))
        if missing_features:
            issues.append({"code": "feature_availability_feature_columns_missing", "missing_columns": missing_features})
    return tuple(issues)


def validate_research_dataset_snapshot_spec(
    snapshot: ResearchDatasetSnapshotSpec | Mapping[str, Any],
    *,
    spec: ResearchDatasetSpec | Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    value = snapshot if isinstance(snapshot, ResearchDatasetSnapshotSpec) else _snapshot_spec_from_mapping(snapshot)
    issues: list[dict[str, Any]] = []
    for field_name in (
        "snapshot_id",
        "research_dataset_spec_id",
        "content_hash",
        "as_of",
        "universe",
        "feature_artifact_refs",
        "label_artifact_refs",
        "primary_keys",
        "lineage_refs",
        "output_ref",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "research_dataset_snapshot_required_field_missing", "field": field_name})
    mutable_text = " ".join([value.snapshot_id, value.output_ref, value.source_of_truth]).lower()
    if "latest" in mutable_text or "current" in mutable_text:
        issues.append({"code": "mutable_research_dataset_snapshot_ref_forbidden", "field": "snapshot_id"})
    if not value.content_hash.startswith("sha256:"):
        issues.append({"code": "research_dataset_snapshot_content_hash_invalid", "field": "content_hash"})
    if value.source_of_truth != "research_dataset_spec_snapshot":
        issues.append({"code": "research_dataset_snapshot_source_of_truth_invalid", "field": "source_of_truth"})
    for key, count in _normalise_ml_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "research_dataset_snapshot_operation_counter_nonzero", "field": key, "value": count})
    if spec is not None:
        spec_value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
        if value.snapshot_id != spec_value.output_snapshot_id:
            issues.append(
                {
                    "code": "research_dataset_snapshot_id_mismatch",
                    "field": "snapshot_id",
                    "expected": spec_value.output_snapshot_id,
                    "actual": value.snapshot_id,
                }
            )
        if value.research_dataset_spec_id != spec_value.spec_id:
            issues.append(
                {
                    "code": "research_dataset_snapshot_spec_id_mismatch",
                    "field": "research_dataset_spec_id",
                    "expected": spec_value.spec_id,
                    "actual": value.research_dataset_spec_id,
                }
            )
        if tuple(value.primary_keys) != tuple(spec_value.primary_keys):
            issues.append(
                {
                    "code": "research_dataset_snapshot_primary_keys_mismatch",
                    "expected": list(spec_value.primary_keys),
                    "actual": list(value.primary_keys),
                }
            )
        if not set(spec_value.feature_artifact_refs).issubset(set(value.feature_artifact_refs)):
            issues.append(
                {
                    "code": "research_dataset_snapshot_feature_refs_missing",
                    "expected": list(spec_value.feature_artifact_refs),
                    "actual": list(value.feature_artifact_refs),
                }
            )
        if not set(spec_value.label_artifact_refs).issubset(set(value.label_artifact_refs)):
            issues.append(
                {
                    "code": "research_dataset_snapshot_label_refs_missing",
                    "expected": list(spec_value.label_artifact_refs),
                    "actual": list(value.label_artifact_refs),
                }
            )
    return tuple(issues)


def validate_ml_pit_feature_matrix_contract(
    contract: MLPITFeatureMatrixContract | Mapping[str, Any],
    *,
    spec: ResearchDatasetSpec | Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    value = contract if isinstance(contract, MLPITFeatureMatrixContract) else _ml_pit_feature_matrix_from_mapping(contract)
    issues: list[dict[str, Any]] = []
    for field_name in (
        "matrix_id",
        "research_dataset_spec_id",
        "entity_id_field",
        "decision_time_field",
        "feature_available_at_field",
        "feature_columns",
        "primary_keys",
        "as_of",
        "lineage_refs",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "ml_pit_feature_matrix_required_field_missing", "field": field_name})
    if value.decision_time_field == value.feature_available_at_field:
        issues.append({"code": "ml_pit_feature_available_field_not_distinct", "field": "feature_available_at_field"})
    for key, count in _normalise_ml_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "ml_pit_feature_matrix_operation_counter_nonzero", "field": key, "value": count})
    if spec is not None:
        spec_value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
        if value.research_dataset_spec_id != spec_value.spec_id:
            issues.append(
                {
                    "code": "ml_pit_feature_matrix_dataset_spec_id_mismatch",
                    "expected": spec_value.spec_id,
                    "actual": value.research_dataset_spec_id,
                }
            )
        if not set(value.feature_columns).issubset(set(spec_value.features)):
            issues.append(
                {
                    "code": "ml_pit_feature_matrix_feature_not_in_dataset_spec",
                    "expected": list(spec_value.features),
                    "actual": list(value.feature_columns),
                }
            )
        if tuple(value.primary_keys) != tuple(spec_value.primary_keys):
            issues.append(
                {
                    "code": "ml_pit_feature_matrix_primary_keys_mismatch",
                    "expected": list(spec_value.primary_keys),
                    "actual": list(value.primary_keys),
                }
            )
    return tuple(issues)


def validate_ml_label_policy_spec(policy: MLLabelPolicySpec | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = policy if isinstance(policy, MLLabelPolicySpec) else _ml_label_policy_from_mapping(policy)
    issues: list[dict[str, Any]] = []
    for field_name in ("policy_id", "label_method", "label_field", "decision_time_field", "label_available_at_field", "leakage_guard_ref"):
        item = getattr(value, field_name)
        if item is None or item == "":
            issues.append({"code": "ml_label_policy_required_field_missing", "field": field_name})
    if value.label_horizon_days <= 0:
        issues.append({"code": "ml_label_policy_horizon_invalid", "field": "label_horizon_days"})
    method = value.label_method.strip().lower()
    if method in ML_RESERVED_LABEL_METHODS:
        issues.append(
            {
                "code": "ml_label_method_not_implemented",
                "field": "label_method",
                "label_method": method,
                "status": "BLOCKED",
            }
        )
    elif method not in ML_SUPPORTED_LABEL_METHODS:
        issues.append({"code": "ml_label_method_unknown", "field": "label_method", "label_method": method})
    if value.decision_time_field == value.label_available_at_field:
        issues.append({"code": "ml_label_available_field_not_distinct", "field": "label_available_at_field"})
    if method == ML_LABEL_METHOD_TRIPLE_BARRIER and not value.triple_barrier_spec:
        issues.append({"code": "ml_triple_barrier_spec_reserved_slot_missing", "field": "triple_barrier_spec"})
    if method == ML_LABEL_METHOD_META_LABEL and not value.meta_labeling_config:
        issues.append({"code": "ml_meta_labeling_config_reserved_slot_missing", "field": "meta_labeling_config"})
    for key, count in _normalise_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "ml_label_policy_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def validate_ml_purged_embargo_cv_policy(policy: MLPurgedEmbargoCVPolicy | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = policy if isinstance(policy, MLPurgedEmbargoCVPolicy) else _ml_cv_policy_from_mapping(policy)
    issues: list[dict[str, Any]] = []
    if not value.policy_id:
        issues.append({"code": "ml_cv_policy_required_field_missing", "field": "policy_id"})
    if not value.folds:
        issues.append({"code": "ml_cv_folds_missing", "field": "folds"})
    if value.purge_window_days < value.label_horizon_days:
        issues.append(
            {
                "code": "ml_cv_purge_window_below_label_horizon",
                "field": "purge_window_days",
                "expected_at_least": value.label_horizon_days,
                "actual": value.purge_window_days,
            }
        )
    if value.embargo_days < 0:
        issues.append({"code": "ml_cv_embargo_days_negative", "field": "embargo_days"})
    if value.label_horizon_days <= 0:
        issues.append({"code": "ml_cv_label_horizon_invalid", "field": "label_horizon_days"})
    for index, fold in enumerate(value.folds):
        issues.extend(_ml_cv_fold_issues(fold, index=index, embargo_days=value.embargo_days))
    for key, count in _normalise_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "ml_cv_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def audit_research_production_contract(
    spec: ResearchDatasetSpec | Mapping[str, Any],
    *,
    feature_artifacts: Sequence[FeatureArtifactSpec | Mapping[str, Any]] = (),
    training_snapshot: TrainingSnapshotSpec | Mapping[str, Any] | None = None,
) -> ResearchProductionAudit:
    value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
    issues: list[dict[str, Any]] = list(validate_research_dataset_spec(value))
    feature_refs: list[str] = []
    for index, feature_artifact in enumerate(feature_artifacts):
        artifact = feature_artifact if isinstance(feature_artifact, FeatureArtifactSpec) else _feature_artifact_from_mapping(feature_artifact)
        validation = validate_feature_artifact_spec(artifact)
        feature_refs.append(artifact.feature_set_id)
        for issue in validation.issues:
            issues.append({"code": "feature_artifact_invalid", "index": index, **dict(issue)})
        if tuple(artifact.primary_keys) != tuple(value.primary_keys):
            issues.append(
                {
                    "code": "feature_artifact_primary_keys_mismatch",
                    "index": index,
                    "expected": list(value.primary_keys),
                    "actual": list(artifact.primary_keys),
                }
            )
    if feature_artifacts and not set(value.feature_artifact_refs).issubset(set(feature_refs)):
        issues.append(
            {
                "code": "feature_artifact_ref_missing",
                "field": "feature_artifact_refs",
                "expected": list(value.feature_artifact_refs),
                "available": feature_refs,
            }
        )

    training_ref = None
    if training_snapshot is not None:
        snapshot_validation = validate_training_snapshot_cutoff(training_snapshot)
        training_ref = snapshot_validation.spec.snapshot_id
        for issue in snapshot_validation.issues:
            issues.append({"code": "training_snapshot_invalid", **dict(issue)})
        training_cutoff_date = _parse_date(snapshot_validation.spec.training_cutoff)
        spec_as_of_date = _parse_date(value.as_of)
        if (
            training_cutoff_date is not None
            and spec_as_of_date is not None
            and training_cutoff_date > spec_as_of_date
        ):
            issues.append(
                {
                    "code": "training_snapshot_cutoff_after_spec_as_of",
                    "training_cutoff": snapshot_validation.spec.training_cutoff,
                    "as_of": value.as_of,
                }
            )

    request = research_dataset_request_from_spec(value)
    request_payload = {
        "start_date": str(request.start_date),
        "end_date": str(request.end_date),
        "universe": request.universe,
        "forward_return_horizon": request.forward_return_horizon,
        "analysis_mode": request.analysis_mode,
        "report_kind": request.report_kind,
    }
    return ResearchProductionAudit(
        status=STATUS_PASS if not issues else STATUS_BLOCKED,
        spec=value,
        spec_fingerprint=research_dataset_spec_fingerprint(value),
        research_dataset_request=request_payload,
        issues=tuple(issues),
        operation_counts=_zero_operation_counts(),
        asset_refs={
            "feature_artifacts": feature_refs,
            "training_snapshot": training_ref,
            "existing_contracts": [
                "engine.research_dataset.ResearchDatasetRequest",
                "market_data.features.artifacts.FeatureArtifactSpec",
                "engine.training_snapshot_contract.TrainingSnapshotSpec",
                "engine.research_manifest.ExperimentManifestClosure",
            ],
        },
    )


def build_research_production_asset_map() -> ResearchProductionAssetMap:
    assets = (
        ResearchProductionAsset(
            asset_id="research_dataset_builder",
            layer="research_dataset",
            module="engine.research_dataset",
            object_names=("ResearchDatasetRequest", "build_research_dataset"),
            role="PIT-safe research dataset request and fixture builder entry point.",
            maturity="existing_contract_needs_production_metadata_bridge",
            current_contracts=("date_window", "universe", "forward_return_horizon", "research_report_kind"),
            required_capabilities=("snapshot_metadata", "stable_replay_checksum", "feature_label_lineage"),
        ),
        ResearchProductionAsset(
            asset_id="feature_label_artifact_contracts",
            layer="feature_label_store",
            module="market_data.features.artifacts",
            object_names=("FeatureArtifactSpec", "LabelArtifactSpec", "FeatureStoreSwitchPolicy"),
            role="Versioned feature and label metadata contract for in-lake feature artifacts.",
            maturity="existing_contract_ready_for_phase2_bridge",
            current_contracts=("feature_set_id", "artifact_version", "as_of_trade_date", "source_view_refs", "lineage_checksum"),
            required_capabilities=("available_at_policy", "primary_key_alignment", "feature_store_switch_gate"),
        ),
        ResearchProductionAsset(
            asset_id="training_snapshot_contract",
            layer="experiment_snapshot",
            module="engine.training_snapshot_contract",
            object_names=("TrainingSnapshotSpec", "validate_training_snapshot_cutoff"),
            role="Training snapshot metadata and cutoff validation.",
            maturity="existing_contract_ready_for_phase2_bridge",
            current_contracts=("published_path", "content_hash", "as_of", "training_cutoff", "split_policy_id"),
            required_capabilities=("cutoff_validation", "published_only_source", "lineage_refs"),
        ),
        ResearchProductionAsset(
            asset_id="experiment_manifest_registry",
            layer="experiment_registry",
            module="engine.research_manifest",
            object_names=("ExperimentManifest", "ResearchReportCatalog", "ExperimentManifestClosure"),
            role="Experiment and report manifest registry with internal truth-source policy.",
            maturity="existing_contract_ready_for_phase2_bridge",
            current_contracts=("config_hash", "dataset_release", "factor_versions", "report_paths", "allowed_blocked_claims"),
            required_capabilities=("experiment_lineage", "report_catalog", "admission_evidence_refs"),
        ),
        ResearchProductionAsset(
            asset_id="factor_model_validation_leakage_gate",
            layer="feature_label_leakage_gate",
            module="engine.factor_model_validation",
            object_names=("label_cutoff_gate", "data_bias_audit"),
            role="Existing row-level leakage and label cutoff validation entry points for later runtime sample validation.",
            maturity="existing_validation_asset_referenced_by_phase2_contract",
            current_contracts=("available_at", "label_available_at", "cutoff_time", "label_horizon_days"),
            required_capabilities=("label_cutoff_gate", "data_bias_audit", "operation_counts_zero"),
        ),
        ResearchProductionAsset(
            asset_id="strategy_admission_package",
            layer="promotion_gate",
            module="engine.strategy_admission_package",
            object_names=("StrategyAdmissionPackage", "OrderIntentDraftRef"),
            role="Offline promotion/admission package; explicitly not runtime or broker authorization.",
            maturity="downstream_phase_existing_contract",
            current_contracts=("manifest_ref", "catalog_ref", "stage6_gate_summary", "not_authorized_counters"),
            required_capabilities=("promotion_gate_inputs", "runtime_claim_blocking", "order_draft_ref_only"),
            downstream_phase="Phase 4/5",
        ),
        ResearchProductionAsset(
            asset_id="strategy_readiness_admission",
            layer="promotion_gate",
            module="engine.strategy_readiness_admission",
            object_names=("AdmissionPackage", "GateResult", "Stage6GateId"),
            role="Stage6 P0 gate matrix for later strategy promotion.",
            maturity="downstream_phase_existing_contract",
            current_contracts=("10_p0_gates", "blocked_claims", "permission_counters"),
            required_capabilities=("gate_matrix", "missing_evidence_fail_closed", "forbidden_operation_counters"),
            downstream_phase="Phase 4/5",
        ),
        ResearchProductionAsset(
            asset_id="cr147_contract_bridge",
            layer="research_production_foundation",
            module="engine.research_production_contracts",
            object_names=("ResearchDatasetSpec", "ResearchProductionAudit", "ResearchProductionAssetMap"),
            role="CR147 bridge that ties existing assets into a metadata-only research production foundation.",
            maturity="new_phase2_contract_bridge",
            current_contracts=("leakage_policy", "source_of_truth_guard", "snapshot_id_guard", "operation_counts_zero"),
            required_capabilities=("asset_map", "contract_audit", "stable_fingerprint"),
        ),
    )
    return ResearchProductionAssetMap(assets=assets, operation_counts=_zero_operation_counts())


def validate_research_production_asset_map(asset_map: ResearchProductionAssetMap) -> tuple[dict[str, Any], ...]:
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for asset in asset_map.assets:
        if not asset.asset_id:
            issues.append({"code": "asset_id_missing"})
        if asset.asset_id in seen:
            issues.append({"code": "asset_id_duplicate", "asset_id": asset.asset_id})
        seen.add(asset.asset_id)
        for field_name in ("layer", "module", "role", "maturity"):
            if not str(getattr(asset, field_name) or "").strip():
                issues.append({"code": "asset_required_field_missing", "asset_id": asset.asset_id, "field": field_name})
        if not asset.object_names:
            issues.append({"code": "asset_object_names_missing", "asset_id": asset.asset_id})
        if not asset.required_capabilities:
            issues.append({"code": "asset_required_capabilities_missing", "asset_id": asset.asset_id})
    issues.extend(
        {"code": "asset_map_operation_counter_nonzero", "field": key, "value": value}
        for key, value in asset_map.operation_counts.items()
        if int(value) != 0
    )
    return tuple(issues)


def research_dataset_spec_fingerprint(spec: ResearchDatasetSpec | Mapping[str, Any]) -> str:
    value = spec if isinstance(spec, ResearchDatasetSpec) else research_dataset_spec_from_mapping(spec)
    return _stable_sha256(value.to_dict())


def research_dataset_spec_from_mapping(data: Mapping[str, Any]) -> ResearchDatasetSpec:
    leakage = data.get("leakage_policy") or {}
    leakage_policy = leakage if isinstance(leakage, LeakagePolicy) else LeakagePolicy(**dict(leakage))
    return ResearchDatasetSpec(
        spec_id=str(data.get("spec_id") or ""),
        universe=str(data.get("universe") or ""),
        start_date=str(data.get("start_date") or ""),
        end_date=str(data.get("end_date") or ""),
        as_of=str(data.get("as_of") or ""),
        features=tuple(str(item) for item in data.get("features") or ()),
        labels=tuple(str(item) for item in data.get("labels") or ()),
        output_snapshot_id=str(data.get("output_snapshot_id") or ""),
        feature_artifact_refs=tuple(str(item) for item in data.get("feature_artifact_refs") or ()),
        label_artifact_refs=tuple(str(item) for item in data.get("label_artifact_refs") or ()),
        event_filters=dict(data.get("event_filters") or {}),
        tradability_filters=dict(data.get("tradability_filters") or {}),
        rebalance_calendar=str(data.get("rebalance_calendar") or "trade_calendar"),
        primary_keys=tuple(str(item) for item in data.get("primary_keys") or ("trade_date", "symbol")),
        source_of_truth=str(data.get("source_of_truth") or "published_current_truth"),
        leakage_policy=leakage_policy,
        schema_version=str(data.get("schema_version") or RESEARCH_DATASET_SPEC_SCHEMA),
    )


def _feature_artifact_from_mapping(data: Mapping[str, Any]) -> FeatureArtifactSpec:
    label = data.get("label_spec")
    label_spec = label if isinstance(label, LabelArtifactSpec) or label is None else LabelArtifactSpec(**dict(label))
    return FeatureArtifactSpec(
        feature_set_id=str(data.get("feature_set_id") or ""),
        schema_version=str(data.get("schema_version") or ""),
        artifact_version=str(data.get("artifact_version") or ""),
        as_of_trade_date=str(data.get("as_of_trade_date") or ""),
        run_id=str(data.get("run_id") or ""),
        source_view_refs=tuple(str(item) for item in data.get("source_view_refs") or ()),
        lineage_checksum=str(data.get("lineage_checksum") or ""),
        feature_columns=tuple(str(item) for item in data.get("feature_columns") or ()),
        primary_keys=tuple(str(item) for item in data.get("primary_keys") or ("trade_date", "symbol")),
        label_spec=label_spec,
    )


def _feature_refs_from_inputs(
    spec: ResearchDatasetSpec,
    feature_artifacts: Sequence[FeatureArtifactSpec | Mapping[str, Any]],
) -> tuple[str, ...]:
    if not feature_artifacts:
        return tuple(spec.feature_artifact_refs)
    refs = []
    for artifact in feature_artifacts:
        value = artifact if isinstance(artifact, FeatureArtifactSpec) else _feature_artifact_from_mapping(artifact)
        refs.append(value.feature_set_id)
    return tuple(dict.fromkeys((*spec.feature_artifact_refs, *refs)))


def _snapshot_spec_from_mapping(data: Mapping[str, Any]) -> ResearchDatasetSnapshotSpec:
    return ResearchDatasetSnapshotSpec(
        snapshot_id=str(data.get("snapshot_id") or ""),
        research_dataset_spec_id=str(data.get("research_dataset_spec_id") or ""),
        content_hash=str(data.get("content_hash") or ""),
        as_of=str(data.get("as_of") or ""),
        universe=str(data.get("universe") or ""),
        feature_artifact_refs=tuple(str(item) for item in data.get("feature_artifact_refs") or ()),
        label_artifact_refs=tuple(str(item) for item in data.get("label_artifact_refs") or ()),
        source_snapshot_refs=tuple(str(item) for item in data.get("source_snapshot_refs") or ()),
        primary_keys=tuple(str(item) for item in data.get("primary_keys") or ()),
        lineage_refs=tuple(str(item) for item in data.get("lineage_refs") or ()),
        output_ref=str(data.get("output_ref") or ""),
        source_of_truth=str(data.get("source_of_truth") or "research_dataset_spec_snapshot"),
        operation_counts=_normalise_ml_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or "research_dataset_snapshot_spec_v1"),
    )


def _feature_availability_contract_from_mapping(data: Mapping[str, Any]) -> FeatureAvailabilityContract:
    return FeatureAvailabilityContract(
        feature_set_id=str(data.get("feature_set_id") or ""),
        decision_time_field=str(data.get("decision_time_field") or ""),
        feature_available_at_field=str(data.get("feature_available_at_field") or ""),
        label_available_at_field=str(data.get("label_available_at_field") or ""),
        label_horizon_days=int(data.get("label_horizon_days", 0) or 0),
        primary_keys=tuple(str(item) for item in data.get("primary_keys") or ()),
        required_columns=tuple(str(item) for item in data.get("required_columns") or ()),
        enforcement_ref=str(data.get("enforcement_ref") or ""),
        operation_counts=_normalise_ml_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or "feature_availability_contract_v1"),
    )


def _ml_pit_feature_matrix_from_mapping(data: Mapping[str, Any]) -> MLPITFeatureMatrixContract:
    return MLPITFeatureMatrixContract(
        matrix_id=str(data.get("matrix_id") or ""),
        research_dataset_spec_id=str(data.get("research_dataset_spec_id") or ""),
        entity_id_field=str(data.get("entity_id_field") or ""),
        decision_time_field=str(data.get("decision_time_field") or ""),
        feature_available_at_field=str(data.get("feature_available_at_field") or ""),
        feature_columns=tuple(str(item) for item in data.get("feature_columns") or ()),
        primary_keys=tuple(str(item) for item in data.get("primary_keys") or ()),
        as_of=str(data.get("as_of") or ""),
        lineage_refs=tuple(str(item) for item in data.get("lineage_refs") or ()),
        source_snapshot_refs=tuple(str(item) for item in data.get("source_snapshot_refs") or ()),
        operation_counts=_normalise_ml_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or ML_PIT_FEATURE_MATRIX_SCHEMA),
    )


def _ml_label_policy_from_mapping(data: Mapping[str, Any]) -> MLLabelPolicySpec:
    return MLLabelPolicySpec(
        policy_id=str(data.get("policy_id") or ""),
        label_method=str(data.get("label_method") or ""),
        label_field=str(data.get("label_field") or ""),
        decision_time_field=str(data.get("decision_time_field") or ""),
        label_available_at_field=str(data.get("label_available_at_field") or ""),
        label_horizon_days=int(data.get("label_horizon_days", 0) or 0),
        leakage_guard_ref=str(data.get("leakage_guard_ref") or "engine.research_production_contracts.validate_ml_label_policy_spec"),
        triple_barrier_spec=dict(data.get("triple_barrier_spec") or {}),
        meta_labeling_config=dict(data.get("meta_labeling_config") or {}),
        operation_counts=_normalise_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or ML_LABEL_POLICY_SCHEMA),
    )


def _ml_cv_policy_from_mapping(data: Mapping[str, Any]) -> MLPurgedEmbargoCVPolicy:
    return MLPurgedEmbargoCVPolicy(
        policy_id=str(data.get("policy_id") or ""),
        folds=tuple(_ml_cv_fold_from_mapping(item) for item in data.get("folds") or ()),
        purge_window_days=int(data.get("purge_window_days", 0) or 0),
        embargo_days=int(data.get("embargo_days", 0) or 0),
        label_horizon_days=int(data.get("label_horizon_days", 0) or 0),
        decision_time_field=str(data.get("decision_time_field") or "decision_time"),
        operation_counts=_normalise_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or ML_PURGED_EMBARGO_CV_SCHEMA),
    )


def _ml_cv_fold_from_mapping(data: Mapping[str, Any]) -> MLCVFoldSpec:
    return MLCVFoldSpec(
        fold_id=str(data.get("fold_id") or ""),
        train_start=str(data.get("train_start") or ""),
        train_end=str(data.get("train_end") or ""),
        validation_start=str(data.get("validation_start") or ""),
        validation_end=str(data.get("validation_end") or ""),
        test_start=str(data.get("test_start") or ""),
        test_end=str(data.get("test_end") or ""),
    )


def _ml_cv_fold_issues(fold: MLCVFoldSpec, *, index: int, embargo_days: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field_name in ("fold_id", "train_start", "train_end", "validation_start", "validation_end"):
        if not str(getattr(fold, field_name) or ""):
            issues.append({"code": "ml_cv_fold_required_field_missing", "fold_index": index, "field": field_name})
    parsed = {name: _parse_date(getattr(fold, name)) for name in ("train_start", "train_end", "validation_start", "validation_end")}
    if any(value is None for value in parsed.values()):
        issues.append({"code": "ml_cv_fold_date_unparseable", "fold_index": index})
        return issues
    if parsed["train_start"] > parsed["train_end"]:  # type: ignore[operator]
        issues.append({"code": "ml_cv_fold_train_start_after_end", "fold_index": index})
    if parsed["validation_start"] > parsed["validation_end"]:  # type: ignore[operator]
        issues.append({"code": "ml_cv_fold_validation_start_after_end", "fold_index": index})
    if parsed["train_end"] >= parsed["validation_start"]:  # type: ignore[operator]
        issues.append({"code": "ml_cv_train_validation_overlap", "fold_index": index})
    min_validation_start = parsed["train_end"] + timedelta(days=embargo_days)  # type: ignore[operator]
    if parsed["validation_start"] < min_validation_start:  # type: ignore[operator]
        issues.append(
            {
                "code": "ml_cv_embargo_gap_too_small",
                "fold_index": index,
                "expected_validation_start_at_or_after": min_validation_start.isoformat(),
                "actual_validation_start": fold.validation_start,
            }
        )
    return issues


def _date_order_issues(spec: ResearchDatasetSpec) -> list[dict[str, Any]]:
    parsed = {name: _parse_date(getattr(spec, name)) for name in ("start_date", "end_date", "as_of")}
    issues = [
        {"code": "research_dataset_spec_date_unparseable", "field": name}
        for name, value in parsed.items()
        if value is None
    ]
    if issues:
        return issues
    if parsed["start_date"] > parsed["end_date"]:  # type: ignore[operator]
        issues.append({"code": "research_dataset_spec_start_after_end", "field": "start_date"})
    if parsed["end_date"] > parsed["as_of"]:  # type: ignore[operator]
        issues.append({"code": "research_dataset_spec_end_after_as_of", "field": "as_of"})
    return issues


def _leakage_policy_issues(policy: LeakagePolicy) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for field_name in ("decision_time_field", "feature_available_at_field", "label_available_at_field"):
        if not str(getattr(policy, field_name) or "").strip():
            issues.append({"code": "leakage_policy_required_field_missing", "field": field_name})
    if policy.label_horizon_days <= 0:
        issues.append({"code": "leakage_policy_label_horizon_invalid", "field": "label_horizon_days"})
    if policy.require_feature_available_before_decision is not True:
        issues.append({"code": "leakage_policy_feature_decision_gate_required", "field": "require_feature_available_before_decision"})
    if policy.require_label_after_decision is not True:
        issues.append({"code": "leakage_policy_label_window_gate_required", "field": "require_label_after_decision"})
    return issues


def _parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(str(value), "%Y%m%d").date()
        except ValueError:
            return None


def _zero_operation_counts() -> dict[str, int]:
    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


def _normalise_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in FORBIDDEN_OPERATION_COUNTERS}


def _normalise_ml_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in CR152_ML_FORBIDDEN_OPERATION_COUNTERS}


def _stable_sha256(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


__all__ = [
    "ASSET_MAP_SCHEMA",
    "FeatureAvailabilityContract",
    "LeakagePolicy",
    "MLCVFoldSpec",
    "MLLabelPolicySpec",
    "MLPITFeatureMatrixContract",
    "MLPurgedEmbargoCVPolicy",
    "CR152_ML_FORBIDDEN_OPERATION_COUNTERS",
    "ML_LABEL_METHOD_FIXED_WINDOW",
    "ML_LABEL_METHOD_META_LABEL",
    "ML_LABEL_METHOD_TRIPLE_BARRIER",
    "RESEARCH_DATASET_SPEC_SCHEMA",
    "RESEARCH_PRODUCTION_AUDIT_SCHEMA",
    "ResearchProductionAsset",
    "ResearchProductionAssetMap",
    "ResearchDatasetSnapshotSpec",
    "ResearchDatasetSpec",
    "ResearchProductionGap",
    "ResearchProductionAudit",
    "audit_research_production_contract",
    "build_feature_availability_contract",
    "build_research_production_asset_map",
    "build_research_dataset_snapshot_spec",
    "research_dataset_request_from_spec",
    "research_dataset_spec_fingerprint",
    "research_dataset_spec_from_mapping",
    "validate_research_production_asset_map",
    "validate_feature_availability_contract",
    "validate_ml_label_policy_spec",
    "validate_ml_pit_feature_matrix_contract",
    "validate_ml_purged_embargo_cv_policy",
    "validate_research_dataset_snapshot_spec",
    "validate_research_dataset_spec",
]
