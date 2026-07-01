"""CR147 research production foundation contracts.

This module is deliberately metadata-only. It does not read a real lake, write
feature artifacts, fetch providers, touch NAS, run QMT, or start trading.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
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
            gaps=(
                ResearchProductionGap(
                    gap_id="research_dataset_snapshot_registry_missing",
                    severity="medium",
                    description="Dataset outputs need a registry entry with content hash, feature versions and label versions.",
                    phase="Phase 2",
                ),
            ),
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
            gaps=(
                ResearchProductionGap(
                    gap_id="feature_available_at_policy_not_enforced_by_builder",
                    severity="medium",
                    description="Feature metadata exposes enough fields for PIT policy, but dataset building must enforce available_at <= decision_time.",
                    phase="Phase 2",
                ),
            ),
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
    payload = json.dumps(value.to_dict(), sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


__all__ = [
    "ASSET_MAP_SCHEMA",
    "LeakagePolicy",
    "RESEARCH_DATASET_SPEC_SCHEMA",
    "RESEARCH_PRODUCTION_AUDIT_SCHEMA",
    "ResearchProductionAsset",
    "ResearchProductionAssetMap",
    "ResearchDatasetSpec",
    "ResearchProductionGap",
    "ResearchProductionAudit",
    "audit_research_production_contract",
    "build_research_production_asset_map",
    "research_dataset_request_from_spec",
    "research_dataset_spec_fingerprint",
    "research_dataset_spec_from_mapping",
    "validate_research_production_asset_map",
    "validate_research_dataset_spec",
]
