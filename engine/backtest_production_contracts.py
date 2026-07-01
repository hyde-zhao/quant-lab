"""CR148 unified backtest and experiment foundation contracts.

This module is metadata-only. It does not run backtests, read a real lake,
write reports, start simulation/live runtime, call brokers, or mutate catalog
pointers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Mapping

from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS
from engine.reporting import build_backtest_report_row


BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA = "backtest_foundation_asset_map_v1"
BACKTEST_REPORT_PACK_SCHEMA = "backtest_report_pack_v1"
BACKTEST_RUN_SPEC_SCHEMA = "backtest_run_spec_v1"
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


@dataclass(frozen=True, slots=True)
class BacktestRunSpec:
    run_id: str
    experiment_id: str
    strategy_id: str
    dataset_snapshot_ref: str
    signal_set_ref: str
    portfolio_policy_ref: str
    benchmark_ref: str
    cost_model_ref: str
    slippage_model_ref: str
    backtest_engine: str
    frequency: str
    start_date: str
    end_date: str
    as_of: str
    config_hash: str
    code_version: str
    metrics_schema: tuple[str, ...]
    report_pack_ref: str
    scope_guard: Phase3ScopeGuard = field(default_factory=Phase3ScopeGuard)
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = BACKTEST_RUN_SPEC_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "strategy_id": self.strategy_id,
            "dataset_snapshot_ref": self.dataset_snapshot_ref,
            "signal_set_ref": self.signal_set_ref,
            "portfolio_policy_ref": self.portfolio_policy_ref,
            "benchmark_ref": self.benchmark_ref,
            "cost_model_ref": self.cost_model_ref,
            "slippage_model_ref": self.slippage_model_ref,
            "backtest_engine": self.backtest_engine,
            "frequency": self.frequency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "as_of": self.as_of,
            "config_hash": self.config_hash,
            "code_version": self.code_version,
            "metrics_schema": list(self.metrics_schema),
            "report_pack_ref": self.report_pack_ref,
            "scope_guard": self.scope_guard.to_dict(),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BacktestReportPack:
    report_pack_ref: str
    run_id: str
    experiment_id: str
    strategy_id: str
    run_spec_hash: str
    content_hash: str
    metric_names: tuple[str, ...]
    report_rows: tuple[Mapping[str, Any], ...]
    artifact_refs: tuple[str, ...]
    scope_guard: Phase3ScopeGuard = field(default_factory=Phase3ScopeGuard)
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = BACKTEST_REPORT_PACK_SCHEMA

    @property
    def row_count(self) -> int:
        return len(self.report_rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_pack_ref": self.report_pack_ref,
            "run_id": self.run_id,
            "experiment_id": self.experiment_id,
            "strategy_id": self.strategy_id,
            "run_spec_hash": self.run_spec_hash,
            "content_hash": self.content_hash,
            "metric_names": list(self.metric_names),
            "report_rows": [dict(row) for row in self.report_rows],
            "row_count": self.row_count,
            "artifact_refs": list(self.artifact_refs),
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
            maturity="existing_asset_ready_for_report_pack_bridge",
            current_contracts=("metrics", "metadata", "json_ready_row"),
            required_capabilities=("report_pack_schema", "artifact_refs", "checksum_or_metric_stability"),
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


def build_backtest_report_pack(
    *,
    run_spec: BacktestRunSpec | Mapping[str, Any],
    metrics: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
    artifact_refs: tuple[str, ...] | None = None,
) -> BacktestReportPack:
    spec = run_spec if isinstance(run_spec, BacktestRunSpec) else _backtest_run_spec_from_mapping(run_spec)
    metadata_payload = {
        "run_id": spec.run_id,
        "experiment_id": spec.experiment_id,
        "strategy_id": spec.strategy_id,
        "dataset_snapshot_ref": spec.dataset_snapshot_ref,
        "signal_set_ref": spec.signal_set_ref,
        "benchmark_ref": spec.benchmark_ref,
        "cost_model_ref": spec.cost_model_ref,
        "slippage_model_ref": spec.slippage_model_ref,
        "backtest_engine": spec.backtest_engine,
        "frequency": spec.frequency,
        "start_date": spec.start_date,
        "end_date": spec.end_date,
        "as_of": spec.as_of,
        "config_hash": spec.config_hash,
        "code_version": spec.code_version,
        "report_pack_ref": spec.report_pack_ref,
        **dict(metadata or {}),
    }
    row = build_backtest_report_row(dict(metrics), metadata_payload)
    refs = artifact_refs or (f"inline://backtest-report-row/{spec.run_id}",)
    content_payload = {
        "report_pack_ref": spec.report_pack_ref,
        "run_id": spec.run_id,
        "run_spec_hash": spec.config_hash,
        "metric_names": sorted(str(key) for key in metrics.keys()),
        "report_rows": [row],
        "artifact_refs": list(refs),
    }
    return BacktestReportPack(
        report_pack_ref=spec.report_pack_ref,
        run_id=spec.run_id,
        experiment_id=spec.experiment_id,
        strategy_id=spec.strategy_id,
        run_spec_hash=spec.config_hash,
        content_hash=_stable_sha256(content_payload),
        metric_names=tuple(sorted(str(key) for key in metrics.keys())),
        report_rows=(row,),
        artifact_refs=tuple(str(item) for item in refs),
        operation_counts=_zero_operation_counts(),
    )


def validate_backtest_report_pack(pack: BacktestReportPack | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = pack if isinstance(pack, BacktestReportPack) else _backtest_report_pack_from_mapping(pack)
    issues: list[dict[str, Any]] = list(validate_phase3_scope_guard(value.scope_guard))
    for field_name in (
        "report_pack_ref",
        "run_id",
        "experiment_id",
        "strategy_id",
        "run_spec_hash",
        "content_hash",
        "metric_names",
        "report_rows",
        "artifact_refs",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "backtest_report_pack_required_field_missing", "field": field_name})
    if value.row_count != len(value.report_rows) or value.row_count <= 0:
        issues.append({"code": "backtest_report_pack_row_count_invalid", "field": "row_count"})
    if not value.run_spec_hash.startswith("sha256:"):
        issues.append({"code": "backtest_report_pack_run_spec_hash_invalid", "field": "run_spec_hash"})
    if not value.content_hash.startswith("sha256:"):
        issues.append({"code": "backtest_report_pack_content_hash_invalid", "field": "content_hash"})
    mutable_text = " ".join([value.report_pack_ref, *value.artifact_refs]).lower()
    if "latest" in mutable_text or "current" in mutable_text:
        issues.append({"code": "backtest_report_pack_mutable_ref_forbidden", "field": "artifact_refs"})
    for metric in ("total_return", "max_drawdown", "turnover"):
        if metric not in set(value.metric_names):
            issues.append({"code": "backtest_report_pack_metric_required", "metric": metric})
    for key, count in _normalise_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "backtest_report_pack_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def build_backtest_run_spec(
    *,
    run_id: str,
    experiment_id: str,
    strategy_id: str,
    dataset_snapshot_ref: str,
    signal_set_ref: str,
    portfolio_policy_ref: str,
    benchmark_ref: str,
    cost_model_ref: str,
    slippage_model_ref: str,
    start_date: str,
    end_date: str,
    as_of: str,
    code_version: str,
    backtest_config: Mapping[str, Any] | Any | None = None,
    backtest_engine: str = "lightweight",
    frequency: str = "daily",
    metrics_schema: tuple[str, ...] = (
        "total_return",
        "annual_return",
        "max_drawdown",
        "sharpe",
        "turnover",
        "final_nav",
    ),
    report_pack_ref: str = "",
) -> BacktestRunSpec:
    config_payload = _backtest_config_payload(backtest_config)
    fingerprint_payload = {
        "run_id": run_id,
        "experiment_id": experiment_id,
        "strategy_id": strategy_id,
        "dataset_snapshot_ref": dataset_snapshot_ref,
        "signal_set_ref": signal_set_ref,
        "portfolio_policy_ref": portfolio_policy_ref,
        "benchmark_ref": benchmark_ref,
        "cost_model_ref": cost_model_ref,
        "slippage_model_ref": slippage_model_ref,
        "start_date": start_date,
        "end_date": end_date,
        "as_of": as_of,
        "code_version": code_version,
        "backtest_engine": backtest_engine,
        "frequency": frequency,
        "metrics_schema": list(metrics_schema),
        "backtest_config": config_payload,
    }
    config_hash = _stable_sha256(fingerprint_payload)
    return BacktestRunSpec(
        run_id=str(run_id or ""),
        experiment_id=str(experiment_id or ""),
        strategy_id=str(strategy_id or ""),
        dataset_snapshot_ref=str(dataset_snapshot_ref or ""),
        signal_set_ref=str(signal_set_ref or ""),
        portfolio_policy_ref=str(portfolio_policy_ref or ""),
        benchmark_ref=str(benchmark_ref or ""),
        cost_model_ref=str(cost_model_ref or ""),
        slippage_model_ref=str(slippage_model_ref or ""),
        backtest_engine=str(backtest_engine or ""),
        frequency=str(frequency or ""),
        start_date=str(start_date or ""),
        end_date=str(end_date or ""),
        as_of=str(as_of or ""),
        config_hash=config_hash,
        code_version=str(code_version or ""),
        metrics_schema=tuple(str(item) for item in metrics_schema),
        report_pack_ref=str(report_pack_ref or f"report-pack://{run_id}"),
        operation_counts=_zero_operation_counts(),
    )


def validate_backtest_run_spec(spec: BacktestRunSpec | Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    value = spec if isinstance(spec, BacktestRunSpec) else _backtest_run_spec_from_mapping(spec)
    issues: list[dict[str, Any]] = list(validate_phase3_scope_guard(value.scope_guard))
    for field_name in (
        "run_id",
        "experiment_id",
        "strategy_id",
        "dataset_snapshot_ref",
        "signal_set_ref",
        "portfolio_policy_ref",
        "benchmark_ref",
        "cost_model_ref",
        "slippage_model_ref",
        "backtest_engine",
        "frequency",
        "start_date",
        "end_date",
        "as_of",
        "config_hash",
        "code_version",
        "metrics_schema",
        "report_pack_ref",
    ):
        item = getattr(value, field_name)
        if item is None or item == "" or item == ():
            issues.append({"code": "backtest_run_spec_required_field_missing", "field": field_name})
    if value.frequency != "daily":
        issues.append({"code": "backtest_run_spec_frequency_not_phase3_daily", "field": "frequency"})
    if value.backtest_engine not in {"lightweight", "backtrader"}:
        issues.append({"code": "backtest_run_spec_engine_invalid", "field": "backtest_engine"})
    if value.backtest_engine == "backtrader":
        issues.append({"code": "backtest_run_spec_backtrader_deep_integration_deferred", "field": "backtest_engine"})
    mutable_text = " ".join([value.dataset_snapshot_ref, value.signal_set_ref, value.report_pack_ref]).lower()
    if "latest" in mutable_text or "current" in mutable_text:
        issues.append({"code": "backtest_run_spec_mutable_ref_forbidden", "field": "dataset_snapshot_ref"})
    if not value.config_hash.startswith("sha256:"):
        issues.append({"code": "backtest_run_spec_config_hash_invalid", "field": "config_hash"})
    for metric in ("total_return", "max_drawdown", "turnover"):
        if metric not in set(value.metrics_schema):
            issues.append({"code": "backtest_run_spec_metric_required", "metric": metric})
    for key, count in _normalise_operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "backtest_run_spec_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


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


def _backtest_run_spec_from_mapping(data: Mapping[str, Any]) -> BacktestRunSpec:
    return BacktestRunSpec(
        run_id=str(data.get("run_id") or ""),
        experiment_id=str(data.get("experiment_id") or ""),
        strategy_id=str(data.get("strategy_id") or ""),
        dataset_snapshot_ref=str(data.get("dataset_snapshot_ref") or ""),
        signal_set_ref=str(data.get("signal_set_ref") or ""),
        portfolio_policy_ref=str(data.get("portfolio_policy_ref") or ""),
        benchmark_ref=str(data.get("benchmark_ref") or ""),
        cost_model_ref=str(data.get("cost_model_ref") or ""),
        slippage_model_ref=str(data.get("slippage_model_ref") or ""),
        backtest_engine=str(data.get("backtest_engine") or ""),
        frequency=str(data.get("frequency") or ""),
        start_date=str(data.get("start_date") or ""),
        end_date=str(data.get("end_date") or ""),
        as_of=str(data.get("as_of") or ""),
        config_hash=str(data.get("config_hash") or ""),
        code_version=str(data.get("code_version") or ""),
        metrics_schema=tuple(str(item) for item in data.get("metrics_schema") or ()),
        report_pack_ref=str(data.get("report_pack_ref") or ""),
        scope_guard=_phase3_scope_guard_from_mapping(data.get("scope_guard") or {}),
        operation_counts=_normalise_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or BACKTEST_RUN_SPEC_SCHEMA),
    )


def _backtest_report_pack_from_mapping(data: Mapping[str, Any]) -> BacktestReportPack:
    return BacktestReportPack(
        report_pack_ref=str(data.get("report_pack_ref") or ""),
        run_id=str(data.get("run_id") or ""),
        experiment_id=str(data.get("experiment_id") or ""),
        strategy_id=str(data.get("strategy_id") or ""),
        run_spec_hash=str(data.get("run_spec_hash") or ""),
        content_hash=str(data.get("content_hash") or ""),
        metric_names=tuple(str(item) for item in data.get("metric_names") or ()),
        report_rows=tuple(dict(item) for item in data.get("report_rows") or ()),
        artifact_refs=tuple(str(item) for item in data.get("artifact_refs") or ()),
        scope_guard=_phase3_scope_guard_from_mapping(data.get("scope_guard") or {}),
        operation_counts=_normalise_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or BACKTEST_REPORT_PACK_SCHEMA),
    )


def _backtest_config_payload(config: Mapping[str, Any] | Any | None) -> dict[str, Any]:
    if config is None:
        return {}
    if isinstance(config, Mapping):
        return {str(key): _json_ready(value) for key, value in config.items()}
    if hasattr(config, "__dataclass_fields__"):
        return {str(key): _json_ready(value) for key, value in asdict(config).items()}
    return {"repr": repr(config)}


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {str(key): _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


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


def _stable_sha256(payload: Mapping[str, Any]) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


__all__ = [
    "BACKTEST_FOUNDATION_ASSET_MAP_SCHEMA",
    "BACKTEST_REPORT_PACK_SCHEMA",
    "BACKTEST_RUN_SPEC_SCHEMA",
    "PHASE3_SCOPE_GUARD_SCHEMA",
    "BacktestFoundationAsset",
    "BacktestFoundationAssetMap",
    "BacktestFoundationGap",
    "BacktestReportPack",
    "BacktestRunSpec",
    "Phase3ScopeGuard",
    "build_backtest_foundation_asset_map",
    "build_backtest_report_pack",
    "build_backtest_run_spec",
    "validate_backtest_foundation_asset_map",
    "validate_backtest_report_pack",
    "validate_backtest_run_spec",
    "validate_phase3_scope_guard",
]
