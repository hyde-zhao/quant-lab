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
    "LeakagePolicy",
    "RESEARCH_DATASET_SPEC_SCHEMA",
    "RESEARCH_PRODUCTION_AUDIT_SCHEMA",
    "ResearchDatasetSpec",
    "ResearchProductionAudit",
    "audit_research_production_contract",
    "research_dataset_request_from_spec",
    "research_dataset_spec_fingerprint",
    "research_dataset_spec_from_mapping",
    "validate_research_dataset_spec",
]
