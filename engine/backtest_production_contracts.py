"""CR148 unified backtest and experiment foundation contracts.

This module is metadata-only. It does not run backtests, read a real lake,
write reports, start simulation/live runtime, call brokers, or mutate catalog
pointers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS


BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA = "backtest_foundation_asset_map_v1"
PHASE3_SCOPE_GUARD_SCHEMA = "phase3_scope_guard_v1"
STATUS_PASS = "pass"
STATUS_BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class BacktestFoundationGap:
    gap_id: str
    severity: str
    description: str
    phase: str
    gate_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BacktestFoundationAsset:
    asset_id: str
    layer: str
    module: str
    object_names: tuple[str, ...]
    role: str
    maturity: str
    current_contracts: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    downstream_phase: str = "Phase 3"
    gaps: tuple[BacktestFoundationGap, ...] = ()

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
            "downstream_phase": self.downstream_phase,
            "gaps": [gap.to_dict() for gap in self.gaps],
        }


@dataclass(frozen=True, slots=True)
class Phase3ScopeGuard:
    baseline_scope: str = "daily_multifactor_baseline_only"
    phase3_exit_strategy_families: tuple[str, ...] = ("multifactor",)
    deferred_strategy_families: tuple[str, ...] = ("machine_learning", "event_driven")
    deferred_runtime_capabilities: tuple[str, ...] = (
        "minute_data",
        "level2_data",
        "qlib_deep_integration",
        "backtrader_deep_integration",
        "simulation_live_or_trading",
        "broker_write",
    )
    nas_scope: str = "metadata_contract_only_no_nas_sync"
    schema_version: str = PHASE3_SCOPE_GUARD_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "baseline_scope": self.baseline_scope,
            "phase3_exit_strategy_families": list(self.phase3_exit_strategy_families),
            "deferred_strategy_families": list(self.deferred_strategy_families),
            "deferred_runtime_capabilities": list(self.deferred_runtime_capabilities),
            "nas_scope": self.nas_scope,
        }


@dataclass(frozen=True, slots=True)
class BacktestFoundationAssetMap:
    assets: tuple[BacktestFoundationAsset, ...]
    scope_guard: Phase3ScopeGuard
    operation_counts: Mapping[str, int]
    schema_version: str = BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA

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
            "scope_guard": self.scope_guard.to_dict(),
            "operation_counts": dict(self.operation_counts),
        }


def build_backtest_foundation_asset_map() -> BacktestFoundationAssetMap:
    assets = (
        BacktestFoundationAsset(
            asset_id="lightweight_backtest_engine",
            layer="backtest_engine",
            module="engine.backtest",
            object_names=(
                "BacktestConfig",
                "BacktestResult",
                "run_backtest",
                "run_backtest_from_loaded_data",
                "run_backtest_with_backend",
            ),
            role="Existing lightweight daily backtest orchestrator and optional backend wrapper.",
            maturity="existing_runtime_asset_needs_metadata_foundation_bridge",
            current_contracts=("schedule", "portfolio_result", "metrics", "execution_policy_metadata"),
            required_capabilities=("backtest_run_spec", "experiment_link", "report_pack_ref"),
            gaps=(
                BacktestFoundationGap(
                    gap_id="backtest_run_spec_missing",
                    severity="medium",
                    description="Backtest execution has config and metadata, but not yet a stable metadata-only BacktestRunSpec.",
                    phase="Phase 3",
                ),
            ),
        ),
        BacktestFoundationAsset(
            asset_id="mature_multifactor_framework",
            layer="strategy_research_framework",
            module="engine.mature_multifactor_framework",
            object_names=(
                "StrategyTypeAdapterContract",
                "SignalSet",
                "ResearchEvidenceIndex",
                "PortfolioRiskPolicy",
                "Stage3ResearchRunManifest",
            ),
            role="Existing mature multifactor research contracts for daily baseline research handoff.",
            maturity="existing_contract_ready_for_phase3_bridge",
            current_contracts=("strategy_family", "signal_set", "research_evidence_index", "portfolio_risk_policy"),
            required_capabilities=("daily_multifactor_baseline", "stage3_manifest", "typed_unavailable_boundaries"),
        ),
        BacktestFoundationAsset(
            asset_id="experiment_manifest_registry",
            layer="experiment_registry",
            module="engine.research_manifest",
            object_names=("ExperimentManifest", "ResearchReportCatalog", "ExperimentManifestClosure"),
            role="Existing experiment/report registry with internal truth-source and admission readiness contracts.",
            maturity="existing_contract_ready_for_phase3_bridge",
            current_contracts=("config_hash", "dataset_release", "factor_versions", "report_paths", "allowed_blocked_claims"),
            required_capabilities=("experiment_id", "metrics_ref", "backtest_report_ref", "code_version"),
        ),
        BacktestFoundationAsset(
            asset_id="strategy_admission_package",
            layer="promotion_gate",
            module="engine.strategy_admission_package",
            object_names=("StrategyAdmissionPackage", "OrderIntentDraftRef", "NotAuthorizedCounters"),
            role="Existing offline admission package that blocks runtime, broker and QMT claims by default.",
            maturity="downstream_phase_existing_contract",
            current_contracts=("manifest_ref", "catalog_ref", "stage6_gate_summary", "not_authorized_counters"),
            required_capabilities=("promotion_gate_inputs", "runtime_claim_blocking", "no_broker_write"),
            downstream_phase="Phase 4/5",
        ),
        BacktestFoundationAsset(
            asset_id="backtest_report_row",
            layer="report_pack",
            module="engine.reporting",
            object_names=("build_backtest_report_row",),
            role="Existing report row builder for stable backtest result summaries.",
            maturity="existing_asset_needs_report_pack_contract",
            current_contracts=("metrics", "metadata", "json_ready_row"),
            required_capabilities=("report_pack_schema", "artifact_refs", "checksum_or_metric_stability"),
            gaps=(
                BacktestFoundationGap(
                    gap_id="report_pack_contract_missing",
                    severity="medium",
                    description="Backtest report rows exist, but Phase 3 still needs a formal report pack contract.",
                    phase="Phase 3",
                ),
            ),
        ),
        BacktestFoundationAsset(
            asset_id="portfolio_and_metrics_core",
            layer="portfolio_metrics",
            module="engine.portfolio|engine.metrics",
            object_names=("run_portfolio", "calculate_metrics", "PortfolioConfig", "PortfolioResult"),
            role="Existing portfolio path and metrics core consumed by the lightweight backtest engine.",
            maturity="existing_runtime_asset_needs_metadata_refs",
            current_contracts=("portfolio_result", "equity_curve", "drawdown", "returns_metrics"),
            required_capabilities=("cost_fields", "risk_metrics", "attribution_refs"),
            gaps=(
                BacktestFoundationGap(
                    gap_id="cost_risk_attribution_contract_missing",
                    severity="medium",
                    description="Portfolio and metrics exist, but Phase 3 needs explicit cost, risk and attribution metadata coverage.",
                    phase="Phase 3",
                ),
            ),
        ),
    )
    return BacktestFoundationAssetMap(
        assets=assets,
        scope_guard=Phase3ScopeGuard(),
        operation_counts=_zero_operation_counts(),
    )


def validate_phase3_scope_guard(scope_guard: Phase3ScopeGuard | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    guard = scope_guard if isinstance(scope_guard, Phase3ScopeGuard) else _phase3_scope_guard_from_mapping(scope_guard)
    issues: list[dict[str, Any]] = []
    if guard.baseline_scope != "daily_multifactor_baseline_only":
        issues.append({"code": "phase3_scope_baseline_invalid", "field": "baseline_scope"})
    if tuple(guard.phase3_exit_strategy_families) != ("multifactor",):
        issues.append(
            {
                "code": "phase3_exit_strategy_family_scope_invalid",
                "expected": ["multifactor"],
                "actual": list(guard.phase3_exit_strategy_families),
            }
        )
    for family in ("machine_learning", "event_driven"):
        if family not in set(guard.deferred_strategy_families):
            issues.append({"code": "phase3_deferred_strategy_family_missing", "family": family})
    if guard.nas_scope != "metadata_contract_only_no_nas_sync":
        issues.append({"code": "phase3_nas_scope_invalid", "field": "nas_scope"})
    for capability in ("simulation_live_or_trading", "broker_write"):
        if capability not in set(guard.deferred_runtime_capabilities):
            issues.append({"code": "phase3_deferred_runtime_capability_missing", "capability": capability})
    return tuple(issues)


def validate_backtest_foundation_asset_map(asset_map: BacktestFoundationAssetMap | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = asset_map if isinstance(asset_map, BacktestFoundationAssetMap) else _asset_map_from_mapping(asset_map)
    issues: list[dict[str, Any]] = list(validate_phase3_scope_guard(value.scope_guard))
    seen: set[str] = set()
    for asset in value.assets:
        if not asset.asset_id:
            issues.append({"code": "backtest_asset_id_missing"})
        if asset.asset_id in seen:
            issues.append({"code": "backtest_asset_id_duplicate", "asset_id": asset.asset_id})
        seen.add(asset.asset_id)
        for field_name in ("layer", "module", "role", "maturity"):
            if not str(getattr(asset, field_name) or "").strip():
                issues.append({"code": "backtest_asset_required_field_missing", "asset_id": asset.asset_id, "field": field_name})
        if not asset.object_names:
            issues.append({"code": "backtest_asset_object_names_missing", "asset_id": asset.asset_id})
        if not asset.required_capabilities:
            issues.append({"code": "backtest_asset_required_capabilities_missing", "asset_id": asset.asset_id})
    for key, count in _normalise_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "backtest_asset_map_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def _asset_map_from_mapping(data: Mapping[str, Any]) -> BacktestFoundationAssetMap:
    return BacktestFoundationAssetMap(
        assets=tuple(_asset_from_mapping(item) for item in data.get("assets") or ()),
        scope_guard=_phase3_scope_guard_from_mapping(data.get("scope_guard") or {}),
        operation_counts=_normalise_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA),
    )


def _asset_from_mapping(data: Mapping[str, Any]) -> BacktestFoundationAsset:
    return BacktestFoundationAsset(
        asset_id=str(data.get("asset_id") or ""),
        layer=str(data.get("layer") or ""),
        module=str(data.get("module") or ""),
        object_names=tuple(str(item) for item in data.get("object_names") or ()),
        role=str(data.get("role") or ""),
        maturity=str(data.get("maturity") or ""),
        current_contracts=tuple(str(item) for item in data.get("current_contracts") or ()),
        required_capabilities=tuple(str(item) for item in data.get("required_capabilities") or ()),
        downstream_phase=str(data.get("downstream_phase") or "Phase 3"),
        gaps=tuple(_gap_from_mapping(item) for item in data.get("gaps") or ()),
    )


def _gap_from_mapping(data: Mapping[str, Any]) -> BacktestFoundationGap:
    return BacktestFoundationGap(
        gap_id=str(data.get("gap_id") or ""),
        severity=str(data.get("severity") or ""),
        description=str(data.get("description") or ""),
        phase=str(data.get("phase") or ""),
        gate_required=bool(data.get("gate_required", False)),
    )


def _phase3_scope_guard_from_mapping(data: Mapping[str, Any]) -> Phase3ScopeGuard:
    return Phase3ScopeGuard(
        baseline_scope=str(data.get("baseline_scope") or ""),
        phase3_exit_strategy_families=tuple(str(item) for item in data.get("phase3_exit_strategy_families") or ()),
        deferred_strategy_families=tuple(str(item) for item in data.get("deferred_strategy_families") or ()),
        deferred_runtime_capabilities=tuple(str(item) for item in data.get("deferred_runtime_capabilities") or ()),
        nas_scope=str(data.get("nas_scope") or ""),
        schema_version=str(data.get("schema_version") or PHASE3_SCOPE_GUARD_SCHEMA),
    )


def _zero_operation_counts() -> dict[str, int]:
    return {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}


def _normalise_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    return {key: int(source.get(key, 0) or 0) for key in FORBIDDEN_OPERATION_COUNTERS}


__all__ = [
    "BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA",
    "PHASE3_SCOPE_GUARD_SCHEMA",
    "BacktestFoundationAsset",
    "BacktestFoundationAssetMap",
    "BacktestFoundationGap",
    "Phase3ScopeGuard",
    "build_backtest_foundation_asset_map",
    "validate_backtest_foundation_asset_map",
    "validate_phase3_scope_guard",
]
