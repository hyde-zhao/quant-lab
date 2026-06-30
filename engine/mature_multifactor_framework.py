"""Stage 2 多因子研究框架升级合同。

本模块只提供 no-lake 的成熟多因子策略生产准备合同：策略类型适配、
SignalSet、ResearchEvidenceIndex、PortfolioRiskPolicy 和 mature admission
support。它不连接数据湖、不读取 provider、不 publish catalog、不启动 QMT /
gateway / simulation / live，也不读取凭据。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.multifactor_contracts import (
    FORBIDDEN_OPERATION_COUNTERS,
    FactorSpec,
    PermissionCounters,
    validate_factor_spec,
)


STAGE2_FRAMEWORK_SCHEMA = "mature_multifactor_framework_stage2_v1"
STRATEGY_TYPE_ADAPTER_SCHEMA = "strategy_type_adapter_contract_v1"
SIGNAL_SET_SCHEMA = "signal_set_v1"
RESEARCH_EVIDENCE_INDEX_SCHEMA = "research_evidence_index_v1"
PORTFOLIO_RISK_POLICY_SCHEMA = "portfolio_risk_policy_v1"
MATURE_ADMISSION_SUPPORT_SCHEMA = "mature_strategy_admission_support_stage2_v1"
TYPED_UNAVAILABLE_SCHEMA = "typed_unavailable_v1"
STRATEGY_CANDIDATE_SCHEMA = "strategy_candidate_v1"
STAGE2_MATURE_FRAMEWORK_BUNDLE_SCHEMA = "stage2_mature_framework_bundle_v1"
STAGE3_RESEARCH_MACHINE_HANDOFF_SCHEMA = "stage3_research_machine_handoff_v1"
STAGE3_RESEARCH_RUN_MANIFEST_SCHEMA = "stage3_research_run_manifest_v1"
STAGE3_MATURE_RESEARCH_PACKAGE_SCHEMA = "stage3_mature_research_package_v1"
CR030_STRATEGY_ADMISSION_PACKAGE_SCHEMA = "strategy_admission_package_v1"
CR039_STRATEGY_ADMISSION_PACKAGE_SCHEMA = "multifactor_strategy_admission_package_v1"
CR039_STRATEGY_CANDIDATE_REF_SCHEMA = "cr039_strategy_candidate_ref_v1"

STAGE2_NO_LAKE = "stage2_no_lake"
STAGE3_DATA_LAKE_REQUIRED = "stage3_data_lake_required"

MF_STAGE2_REQUIRED_FIELD_MISSING = "MF_STAGE2_REQUIRED_FIELD_MISSING"
MF_STAGE2_NO_LAKE_VIOLATION = "MF_STAGE2_NO_LAKE_VIOLATION"
MF_STAGE2_FACTOR_SPEC_BLOCKED = "MF_STAGE2_FACTOR_SPEC_BLOCKED"
MF_STAGE2_SIGNAL_SET_INVALID = "MF_STAGE2_SIGNAL_SET_INVALID"
MF_STAGE2_EVIDENCE_INDEX_INCOMPLETE = "MF_STAGE2_EVIDENCE_INDEX_INCOMPLETE"
MF_STAGE2_RISK_POLICY_INVALID = "MF_STAGE2_RISK_POLICY_INVALID"
MF_STAGE2_STRATEGY_CANDIDATE_INVALID = "MF_STAGE2_STRATEGY_CANDIDATE_INVALID"
MF_STAGE2_CR039_OUTPUT_INVALID = "MF_STAGE2_CR039_OUTPUT_INVALID"
MF_STAGE3_HANDOFF_INVALID = "MF_STAGE3_HANDOFF_INVALID"
MF_STAGE3_RUN_MANIFEST_INVALID = "MF_STAGE3_RUN_MANIFEST_INVALID"
MF_STAGE3_RESEARCH_PACKAGE_INVALID = "MF_STAGE3_RESEARCH_PACKAGE_INVALID"

STAGE2_DATA_REQUIREMENTS = (
    "data_release_ref",
    "pit_universe",
    "listing_delisting",
    "st_filter",
    "suspension_filter",
    "limit_up_down_filter",
    "liquidity_filter",
    "industry_classification",
    "market_cap",
    "style_exposure",
    "benchmark",
    "fee_slippage_model",
)

STAGE2_FORBIDDEN_COUNTERS = FORBIDDEN_OPERATION_COUNTERS

STAGE3_REQUIRED_EVIDENCE = (
    "data_release_ref",
    "run_manifest_ref",
    "factor_panel_ref",
    "label_window_ref",
    "ic_rankic_ref",
    "layered_returns_ref",
    "turnover_ref",
    "exposure_ref",
    "factor_model_validation_report_ref",
    "portfolio_version_ref",
    "risk_policy_version_ref",
    "mature_strategy_admission_package_ref",
    "runner_offline_preflight_ref",
)

STAGE3_RUN_MANIFEST_REQUIRED_FIELDS = (
    "run_id",
    "strategy_id",
    "config_hash",
    "data_release_ref",
    "factor_versions",
    "code_version",
    "seed",
    "date_range",
)

STAGE3_FORBIDDEN_CLAIMS = (
    "qmt_ready",
    "simulation_ready",
    "live_ready",
    "small_live_ready",
    "runtime_authorized",
)


class StrategyFamily(str, Enum):
    MULTIFACTOR = "multifactor"
    EVENT = "event"
    MACHINE_LEARNING = "machine_learning"
    RULE_BASED = "rule_based"


@dataclass(frozen=True, slots=True)
class Stage2BlockedReason:
    code: str
    message: str
    field: str = ""
    severity: str = "blocker"
    remediation: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class TypedUnavailable:
    code: str
    message: str
    missing_inputs: tuple[str, ...]
    required_stage: str = "Stage 3"
    remediation: str = ""
    severity: str = "blocking_until_stage3"
    schema_version: str = TYPED_UNAVAILABLE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class Stage2ValidationResult:
    status: str
    blocked_reasons: tuple[Stage2BlockedReason, ...] = ()
    typed_unavailable: tuple[TypedUnavailable, ...] = ()
    object_type: str = ""
    object_id: str = ""
    permission_counters: Mapping[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status in {"pass", "stage2_ready", "stage2_ready_with_typed_unavailable"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "typed_unavailable": [item.to_dict() for item in self.typed_unavailable],
            "object_type": self.object_type,
            "object_id": self.object_id,
            "permission_counters": dict(self.permission_counters),
        }


@dataclass(frozen=True, slots=True)
class StrategyTypeAdapterContract:
    adapter_id: str
    strategy_family: StrategyFamily | str
    input_contract: Mapping[str, Any]
    output_contract: Mapping[str, Any]
    evidence_required: tuple[str, ...]
    unsupported_reason: str = ""
    schema_version: str = STRATEGY_TYPE_ADAPTER_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["strategy_family"] = _enum_value(self.strategy_family)
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class SignalSet:
    signal_set_id: str
    strategy_family: StrategyFamily | str
    trade_date: str
    universe_ref: str
    signal_schema: Mapping[str, Any]
    signals: tuple[Mapping[str, Any], ...]
    available_at: str
    lineage_ref: str
    evidence_refs: tuple[str, ...]
    typed_unavailable: tuple[TypedUnavailable, ...] = ()
    schema_version: str = SIGNAL_SET_SCHEMA
    not_order: bool = True
    not_runtime_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["strategy_family"] = _enum_value(self.strategy_family)
        data["typed_unavailable"] = [item.to_dict() for item in self.typed_unavailable]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class ResearchEvidenceIndex:
    index_id: str
    data_release_ref: str
    run_manifest_ref: str
    metric_refs: Mapping[str, str]
    lineage_refs: Mapping[str, str]
    limitations: tuple[str, ...]
    typed_unavailable: tuple[TypedUnavailable, ...] = ()
    schema_version: str = RESEARCH_EVIDENCE_INDEX_SCHEMA
    not_catalog_publish: bool = True
    not_data_lake_write: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["typed_unavailable"] = [item.to_dict() for item in self.typed_unavailable]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class PortfolioRiskPolicy:
    policy_id: str
    top_n: int
    max_weight: float
    turnover_limit: float
    industry_limit: Mapping[str, Any]
    style_limit: Mapping[str, Any]
    capacity_assumption: Mapping[str, Any]
    fee_slippage_ref: str
    stop_conditions: tuple[str, ...]
    version: str = "stage2-v1"
    effective_from: str = "2026-06-30"
    release_id: str = "config-facts-cr139-v1"
    universe_policy_ref: str = "config_facts/universe_policy/all_a_share/config-facts-cr139-v1"
    delisting_policy: str = "exclude_delisted"
    st_policy: str = "exclude_st"
    schema_version: str = PORTFOLIO_RISK_POLICY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class MatureAdmissionSupport:
    package_id: str
    strategy_id: str
    status: str
    adapter_ref: Mapping[str, Any]
    signal_set_ref: Mapping[str, Any]
    evidence_index_ref: Mapping[str, Any]
    portfolio_risk_policy_ref: Mapping[str, Any]
    factor_spec_refs: tuple[Mapping[str, Any], ...]
    stage3_data_requirements: tuple[str, ...]
    typed_unavailable: tuple[TypedUnavailable, ...]
    blocked_reasons: tuple[Stage2BlockedReason, ...]
    limitations: tuple[str, ...]
    permission_counters: Mapping[str, int]
    schema_version: str = MATURE_ADMISSION_SUPPORT_SCHEMA
    stage2_no_lake: bool = True
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["typed_unavailable"] = [item.to_dict() for item in self.typed_unavailable]
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class StrategyCandidate:
    candidate_id: str
    strategy_id: str
    strategy_family: StrategyFamily | str
    admission: str
    research_status: str
    source_contract: Mapping[str, Any]
    source_candidate_ref: Mapping[str, Any]
    signal_set_ref: Mapping[str, Any]
    evidence_index_ref: Mapping[str, Any]
    portfolio_risk_policy_ref: Mapping[str, Any]
    metrics_summary: Mapping[str, Any]
    typed_unavailable: tuple[TypedUnavailable, ...]
    blocked_reasons: tuple[Stage2BlockedReason, ...]
    limitations: tuple[str, ...]
    schema_version: str = STRATEGY_CANDIDATE_SCHEMA
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True
    not_broker_order: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["strategy_family"] = _enum_value(self.strategy_family)
        data["typed_unavailable"] = [item.to_dict() for item in self.typed_unavailable]
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class Stage3ResearchMachineHandoff:
    handoff_id: str
    strategy_id: str
    status: str
    stage2_support_ref: Mapping[str, Any]
    strategy_candidate_ref: Mapping[str, Any]
    required_inputs: tuple[str, ...]
    required_evidence: tuple[str, ...]
    data_lake_requirements: Mapping[str, Any]
    execution_boundary: Mapping[str, Any]
    blocked_until: tuple[str, ...]
    validation_plan: tuple[str, ...]
    blocked_reasons: tuple[Stage2BlockedReason, ...]
    schema_version: str = STAGE3_RESEARCH_MACHINE_HANDOFF_SCHEMA
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class Stage3ResearchRunManifest:
    run_id: str
    strategy_id: str
    config_hash: str
    data_release_ref: str
    factor_versions: Mapping[str, str]
    code_version: str
    seed: int
    date_range: Mapping[str, str]
    created_at: str
    evidence_refs: Mapping[str, str]
    schema_version: str = STAGE3_RESEARCH_RUN_MANIFEST_SCHEMA
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class Stage3MatureResearchPackage:
    package_id: str
    strategy_id: str
    status: str
    run_manifest: Stage3ResearchRunManifest | Mapping[str, Any]
    input_refs: Mapping[str, str]
    evidence_refs: Mapping[str, str]
    signal_set: SignalSet | Mapping[str, Any]
    strategy_candidate: StrategyCandidate | Mapping[str, Any]
    research_evidence_index: ResearchEvidenceIndex | Mapping[str, Any]
    portfolio_risk_policy: PortfolioRiskPolicy | Mapping[str, Any]
    factor_model_validation_report_ref: str
    mature_strategy_admission_package_ref: str
    runner_offline_preflight_ref: str
    observation_plan_ref: str
    blocked_claims: tuple[str, ...]
    unlock_conditions: tuple[str, ...]
    blocked_reasons: tuple[Stage2BlockedReason, ...]
    schema_version: str = STAGE3_MATURE_RESEARCH_PACKAGE_SCHEMA
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True
    not_gateway_or_qmt_operation: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["run_manifest"] = _object_to_dict(self.run_manifest)
        data["signal_set"] = _object_to_dict(self.signal_set)
        data["strategy_candidate"] = _object_to_dict(self.strategy_candidate)
        data["research_evidence_index"] = _object_to_dict(self.research_evidence_index)
        data["portfolio_risk_policy"] = _object_to_dict(self.portfolio_risk_policy)
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        return _json_safe(data)


@dataclass(frozen=True, slots=True)
class Stage2MatureFrameworkBundle:
    bundle_id: str
    strategy_id: str
    status: str
    mature_admission_support: MatureAdmissionSupport | Mapping[str, Any]
    strategy_candidate: StrategyCandidate | Mapping[str, Any]
    stage3_research_machine_handoff: Stage3ResearchMachineHandoff | Mapping[str, Any]
    cr030_refs: Mapping[str, Any]
    cr039_refs: Mapping[str, Any]
    blocked_reasons: tuple[Stage2BlockedReason, ...]
    schema_version: str = STAGE2_MATURE_FRAMEWORK_BUNDLE_SCHEMA
    stage2_no_lake: bool = True
    not_runtime_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["mature_admission_support"] = _object_to_dict(self.mature_admission_support)
        data["strategy_candidate"] = _object_to_dict(self.strategy_candidate)
        data["stage3_research_machine_handoff"] = _object_to_dict(self.stage3_research_machine_handoff)
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        return _json_safe(data)


def build_multifactor_strategy_type_adapter() -> StrategyTypeAdapterContract:
    return StrategyTypeAdapterContract(
        adapter_id="adapter:multifactor:stage2",
        strategy_family=StrategyFamily.MULTIFACTOR,
        input_contract={
            "factor_specs": "tuple[FactorSpec]",
            "factor_run_specs": "tuple[FactorRunSpec]",
            "factor_panel": "FactorPanelContract",
            "label_window": "LabelWindowSpec",
            "evaluation_reports": "tuple[FactorEvaluationReport]",
            "portfolio_plan": "MultiFactorPortfolioPlan",
        },
        output_contract={
            "signal_set": SIGNAL_SET_SCHEMA,
            "strategy_candidate": STRATEGY_CANDIDATE_SCHEMA,
            "research_evidence_index": RESEARCH_EVIDENCE_INDEX_SCHEMA,
            "mature_admission_support": MATURE_ADMISSION_SUPPORT_SCHEMA,
        },
        evidence_required=(
            "factor_spec_refs",
            "factor_panel_ref",
            "label_window_ref",
            "ic_rankic_ref",
            "layered_returns_ref",
            "turnover_ref",
            "exposure_ref",
            "portfolio_risk_policy_ref",
        ),
    )


def build_stage2_signal_set(
    *,
    strategy_id: str,
    trade_date: str,
    universe_ref: str,
    scores: Mapping[str, float],
    lineage_ref: str,
    evidence_refs: Sequence[str],
    available_at: str = "decision_time",
) -> SignalSet:
    unavailable: tuple[TypedUnavailable, ...] = ()
    if not universe_ref or universe_ref.startswith("typed_unavailable:"):
        unavailable = (
            typed_unavailable(
                "stage3_pit_universe_required",
                "Stage 2 不连接数据湖，真实 PIT universe 只能在 Stage 3 补齐。",
                ("pit_universe",),
            ),
        )
    signals = tuple(
        {
            "symbol": str(symbol),
            "score": float(score),
            "direction": "long",
            "confidence": "stage2_fixture",
            "available_at": available_at,
        }
        for symbol, score in sorted(scores.items(), key=lambda item: str(item[0]))
    )
    return SignalSet(
        signal_set_id=_stable_id("signal-set", strategy_id, trade_date, universe_ref, scores),
        strategy_family=StrategyFamily.MULTIFACTOR,
        trade_date=trade_date,
        universe_ref=universe_ref,
        signal_schema={
            "score_field": "score",
            "direction_field": "direction",
            "available_at_field": "available_at",
            "stage": "Stage 2",
        },
        signals=signals,
        available_at=available_at,
        lineage_ref=lineage_ref,
        evidence_refs=tuple(str(ref) for ref in evidence_refs if str(ref)),
        typed_unavailable=unavailable,
    )


def build_stage2_research_evidence_index(
    *,
    index_id: str,
    run_manifest_ref: str,
    metric_refs: Mapping[str, str] | None = None,
    lineage_refs: Mapping[str, str] | None = None,
    data_release_ref: str = "",
) -> ResearchEvidenceIndex:
    metric_data = dict(metric_refs or {})
    lineage_data = dict(lineage_refs or {})
    unavailable: list[TypedUnavailable] = []
    missing = [name for name in STAGE2_DATA_REQUIREMENTS if not _has_ref(name, data_release_ref, metric_data, lineage_data)]
    if missing:
        unavailable.append(
            typed_unavailable(
                "stage3_real_data_lineage_required",
                "Stage 2 只冻结证据索引合同；真实数据 release、PIT universe 和 lineage 在 Stage 3 由研究机补齐。",
                tuple(missing),
            )
        )
    return ResearchEvidenceIndex(
        index_id=index_id,
        data_release_ref=data_release_ref or "typed_unavailable:stage3_data_release_ref",
        run_manifest_ref=run_manifest_ref,
        metric_refs=metric_data,
        lineage_refs=lineage_data,
        limitations=(
            "stage2_framework_contract_only",
            "not_data_lake_current_truth",
            "not_catalog_publish",
            "not_runtime_authorization",
        ),
        typed_unavailable=tuple(unavailable),
    )


def build_stage2_portfolio_risk_policy(
    *,
    policy_id: str,
    top_n: int,
    max_weight: float,
    turnover_limit: float,
    industry_limit: Mapping[str, Any] | None = None,
    style_limit: Mapping[str, Any] | None = None,
    capacity_assumption: Mapping[str, Any] | None = None,
    fee_slippage_ref: str = "typed_unavailable:stage3_fee_slippage_model",
    stop_conditions: Sequence[str] | None = None,
) -> PortfolioRiskPolicy:
    return PortfolioRiskPolicy(
        policy_id=policy_id,
        top_n=int(top_n),
        max_weight=float(max_weight),
        turnover_limit=float(turnover_limit),
        industry_limit=dict(industry_limit or {"mode": "stage3_required", "max_industry_weight": "typed_unavailable"}),
        style_limit=dict(style_limit or {"mode": "stage3_required", "style_exposure": "typed_unavailable"}),
        capacity_assumption=dict(
            capacity_assumption
            or {"mode": "stage3_required", "max_participation_rate": "typed_unavailable"}
        ),
        fee_slippage_ref=fee_slippage_ref,
        stop_conditions=tuple(
            stop_conditions
            or (
                "data_quality_failed",
                "risk_policy_failed",
                "gateway_identity_mismatch",
                "reconciliation_unresolved",
                "unknown_order_status",
                "manual_takeover_required",
            )
        ),
    )


def build_stage2_mature_admission_support(
    *,
    strategy_id: str,
    adapter: StrategyTypeAdapterContract | Mapping[str, Any],
    factor_specs: Sequence[FactorSpec | Mapping[str, Any]],
    signal_set: SignalSet | Mapping[str, Any],
    evidence_index: ResearchEvidenceIndex | Mapping[str, Any],
    risk_policy: PortfolioRiskPolicy | Mapping[str, Any],
    permission_counters: PermissionCounters | Mapping[str, int] | None = None,
) -> MatureAdmissionSupport:
    counters = _normalize_permission_counters(permission_counters)
    blocked: list[Stage2BlockedReason] = []
    typed: list[TypedUnavailable] = []

    blocked.extend(validate_stage2_no_lake(counters).blocked_reasons)
    blocked.extend(validate_strategy_type_adapter(adapter).blocked_reasons)

    for index, spec in enumerate(factor_specs):
        result = validate_factor_spec(spec)
        if not result.passed:
            blocked.append(
                Stage2BlockedReason(
                    code=MF_STAGE2_FACTOR_SPEC_BLOCKED,
                    message="FactorSpec 未通过 Stage 2 合同校验。",
                    field=f"factor_specs[{index}]",
                    remediation="补齐 FactorSpec 输入字段、available_at、lineage 和 blocked claims。",
                )
            )

    signal_validation = validate_signal_set(signal_set)
    evidence_validation = validate_research_evidence_index(evidence_index)
    risk_validation = validate_portfolio_risk_policy(risk_policy)
    blocked.extend(signal_validation.blocked_reasons)
    blocked.extend(evidence_validation.blocked_reasons)
    blocked.extend(risk_validation.blocked_reasons)
    typed.extend(signal_validation.typed_unavailable)
    typed.extend(evidence_validation.typed_unavailable)
    typed.extend(risk_validation.typed_unavailable)

    status = "blocked" if blocked else "stage2_framework_ready"
    adapter_data = _as_mapping(adapter)
    signal_data = _as_mapping(signal_set)
    evidence_data = _as_mapping(evidence_index)
    risk_data = _as_mapping(risk_policy)

    return MatureAdmissionSupport(
        package_id=_stable_id("mature-admission-support", strategy_id, signal_data.get("signal_set_id"), evidence_data.get("index_id")),
        strategy_id=strategy_id,
        status=status,
        adapter_ref=_ref(adapter_data, "adapter_id", STRATEGY_TYPE_ADAPTER_SCHEMA),
        signal_set_ref=_ref(signal_data, "signal_set_id", SIGNAL_SET_SCHEMA),
        evidence_index_ref=_ref(evidence_data, "index_id", RESEARCH_EVIDENCE_INDEX_SCHEMA),
        portfolio_risk_policy_ref=_ref(risk_data, "policy_id", PORTFOLIO_RISK_POLICY_SCHEMA),
        factor_spec_refs=tuple(_factor_spec_ref(spec) for spec in factor_specs),
        stage3_data_requirements=STAGE2_DATA_REQUIREMENTS,
        typed_unavailable=tuple(_dedupe_typed(typed)),
        blocked_reasons=tuple(_dedupe_reasons(blocked)),
        limitations=(
            "stage2_no_lake_framework_support_only",
            "not_mature_strategy_production",
            "not_simulation_authorization",
            "not_live_authorization",
            "stage3_must_provide_real_data_lineage_before_runtime",
        ),
        permission_counters=counters,
    )


def build_project_strategy_candidate_from_cr039(
    *,
    cr039_candidate: Mapping[str, Any] | Any,
    signal_set: SignalSet | Mapping[str, Any],
    evidence_index: ResearchEvidenceIndex | Mapping[str, Any],
    risk_policy: PortfolioRiskPolicy | Mapping[str, Any],
    source_run_id: str = "",
    source_admission_package_ref: str = "",
) -> StrategyCandidate:
    candidate_data = _as_mapping(cr039_candidate)
    signal_data = _as_mapping(signal_set)
    evidence_data = _as_mapping(evidence_index)
    risk_data = _as_mapping(risk_policy)
    blocked: list[Stage2BlockedReason] = []
    typed: list[TypedUnavailable] = []

    blocked.extend(
        _required_reasons(
            candidate_data,
            ("strategy_id", "source_portfolio_id", "admission", "evidence_status"),
            code=MF_STAGE2_CR039_OUTPUT_INVALID,
        )
    )
    admission = str(candidate_data.get("admission") or "")
    if admission and admission not in {"research_baseline", "watch", "blocked"}:
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE2_CR039_OUTPUT_INVALID,
                message="CR039 StrategyCandidate.admission 不在项目级候选允许集合内。",
                field="cr039_candidate.admission",
                remediation="CR039 候选必须先归一为 research_baseline / watch / blocked。",
            )
        )
    for validation in (
        validate_signal_set(signal_set),
        validate_research_evidence_index(evidence_index),
        validate_portfolio_risk_policy(risk_policy),
    ):
        blocked.extend(validation.blocked_reasons)
        typed.extend(validation.typed_unavailable)

    strategy_id = str(candidate_data.get("strategy_id") or signal_data.get("signal_set_id") or "")
    source_portfolio_id = str(candidate_data.get("source_portfolio_id") or "")
    research_status = "stage2_research_candidate_ready"
    if blocked:
        research_status = "blocked"
    elif admission == "watch":
        research_status = "stage2_watch_candidate"

    return StrategyCandidate(
        candidate_id=_stable_id(
            "strategy-candidate",
            strategy_id,
            source_portfolio_id,
            signal_data.get("signal_set_id"),
            evidence_data.get("index_id"),
        ),
        strategy_id=strategy_id,
        strategy_family=StrategyFamily.MULTIFACTOR,
        admission=admission or "blocked",
        research_status=research_status,
        source_contract={
            "source": "CR039",
            "schema_version": CR039_STRATEGY_ADMISSION_PACKAGE_SCHEMA,
            "source_run_id": source_run_id,
            "source_admission_package_ref": source_admission_package_ref,
            "cr030_bridge_schema_version": CR030_STRATEGY_ADMISSION_PACKAGE_SCHEMA,
        },
        source_candidate_ref={
            "schema_version": CR039_STRATEGY_CANDIDATE_REF_SCHEMA,
            "strategy_id": strategy_id,
            "source_portfolio_id": source_portfolio_id,
            "admission": admission,
            "evidence_status": str(candidate_data.get("evidence_status") or ""),
        },
        signal_set_ref=_ref(signal_data, "signal_set_id", SIGNAL_SET_SCHEMA),
        evidence_index_ref=_ref(evidence_data, "index_id", RESEARCH_EVIDENCE_INDEX_SCHEMA),
        portfolio_risk_policy_ref=_ref(risk_data, "policy_id", PORTFOLIO_RISK_POLICY_SCHEMA),
        metrics_summary={
            "mean_net_return_25bps": _optional_float(candidate_data.get("mean_net_return_25bps")),
            "mean_turnover": _optional_float(candidate_data.get("mean_turnover")),
            "max_drawdown_proxy": _optional_float(candidate_data.get("max_drawdown_proxy")),
            "capacity_evidence": str(candidate_data.get("capacity_evidence") or ""),
            "simulation_candidate": bool(candidate_data.get("simulation_candidate") is True),
            "reason": str(candidate_data.get("reason") or ""),
        },
        typed_unavailable=tuple(_dedupe_typed(typed)),
        blocked_reasons=tuple(_dedupe_reasons(blocked)),
        limitations=(
            "project_level_candidate_contract_only",
            "derived_from_cr039_research_candidate",
            "not_simulation_candidate_without_follow_up_runtime_gate",
            "not_qmt_ready",
        ),
    )


def build_stage3_research_machine_handoff(
    *,
    strategy_id: str,
    mature_admission_support: MatureAdmissionSupport | Mapping[str, Any],
    strategy_candidate: StrategyCandidate | Mapping[str, Any],
    evidence_index: ResearchEvidenceIndex | Mapping[str, Any],
    risk_policy: PortfolioRiskPolicy | Mapping[str, Any],
) -> Stage3ResearchMachineHandoff:
    support_data = _as_mapping(mature_admission_support)
    candidate_data = _as_mapping(strategy_candidate)
    evidence_data = _as_mapping(evidence_index)
    risk_data = _as_mapping(risk_policy)
    blocked = []
    blocked.extend(_reasons_from_payload(support_data.get("blocked_reasons")))
    blocked.extend(_reasons_from_payload(candidate_data.get("blocked_reasons")))
    missing = [
        item
        for item in ("package_id",)
        if _is_blank(support_data.get(item))
    ]
    for field_name in missing:
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_HANDOFF_INVALID,
                message=f"Stage 3 handoff 缺少成熟准入支撑字段: {field_name}",
                field=f"mature_admission_support.{field_name}",
            )
        )
    if _is_blank(candidate_data.get("candidate_id")):
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_HANDOFF_INVALID,
                message="Stage 3 handoff 缺少项目级 StrategyCandidate。",
                field="strategy_candidate.candidate_id",
            )
        )

    return Stage3ResearchMachineHandoff(
        handoff_id=_stable_id(
            "stage3-research-machine-handoff",
            strategy_id,
            support_data.get("package_id"),
            candidate_data.get("candidate_id"),
        ),
        strategy_id=strategy_id,
        status="blocked" if blocked else "ready_for_stage3_research_machine",
        stage2_support_ref=_ref(support_data, "package_id", MATURE_ADMISSION_SUPPORT_SCHEMA),
        strategy_candidate_ref=_ref(candidate_data, "candidate_id", STRATEGY_CANDIDATE_SCHEMA),
        required_inputs=STAGE2_DATA_REQUIREMENTS,
        required_evidence=STAGE3_REQUIRED_EVIDENCE,
        data_lake_requirements={
            "stage": "Stage 3",
            "required": True,
            "environment": "research_machine",
            "must_be_point_in_time": True,
            "must_record_lineage": True,
            "data_release_ref": evidence_data.get("data_release_ref") or "required",
            "risk_policy_ref": risk_data.get("policy_id") or "required",
        },
        execution_boundary={
            "stage2_no_lake_complete": True,
            "stage3_may_connect_data_lake_after_user_execution_on_research_machine": True,
            "not_runtime_authorization": True,
            "not_simulation_authorization": True,
            "not_live_authorization": True,
            "not_gateway_or_qmt_operation": True,
            "not_order_generation": True,
        },
        blocked_until=(
            "stage3_real_data_evidence_complete",
            "mature_strategy_admission_package_reviewed",
            "simulation_runtime_authorization_requested_separately",
        ),
        validation_plan=(
            "validate_pit_universe_and_security_lifecycle",
            "validate_factor_panel_and_label_window_no_leakage",
            "validate_ic_rankic_layered_returns_turnover_exposure",
            "validate_portfolio_risk_policy_and_capacity",
            "validate_signal_portfolio_risk_versions_are_traceable",
            "build_mature_strategy_admission_package_before_any_runtime",
        ),
        blocked_reasons=tuple(_dedupe_reasons(blocked)),
    )


def build_stage3_research_run_manifest(
    *,
    run_id: str,
    strategy_id: str,
    data_release_ref: str,
    factor_versions: Mapping[str, str],
    code_version: str,
    seed: int,
    date_range: Mapping[str, str],
    config_hash: str = "",
    config: Mapping[str, Any] | None = None,
    created_at: str = "",
    evidence_refs: Mapping[str, str] | None = None,
) -> Stage3ResearchRunManifest:
    resolved_config_hash = config_hash
    if not resolved_config_hash and config:
        resolved_config_hash = hashlib.sha256(
            json.dumps(_json_safe(config), ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
    return Stage3ResearchRunManifest(
        run_id=run_id,
        strategy_id=strategy_id,
        config_hash=resolved_config_hash,
        data_release_ref=data_release_ref,
        factor_versions=dict(factor_versions),
        code_version=code_version,
        seed=int(seed),
        date_range=dict(date_range),
        created_at=created_at,
        evidence_refs=dict(evidence_refs or {}),
    )


def build_stage3_mature_research_package(
    *,
    strategy_id: str,
    run_manifest: Stage3ResearchRunManifest | Mapping[str, Any],
    input_refs: Mapping[str, str],
    evidence_refs: Mapping[str, str],
    signal_set: SignalSet | Mapping[str, Any],
    strategy_candidate: StrategyCandidate | Mapping[str, Any],
    research_evidence_index: ResearchEvidenceIndex | Mapping[str, Any],
    portfolio_risk_policy: PortfolioRiskPolicy | Mapping[str, Any],
    mature_strategy_admission_package_ref: str,
    runner_offline_preflight_ref: str,
    observation_plan_ref: str,
    factor_model_validation_report_ref: str = "",
    blocked_claims: Sequence[str] | None = None,
    unlock_conditions: Sequence[str] | None = None,
) -> Stage3MatureResearchPackage:
    manifest_data = _as_mapping(run_manifest)
    evidence_index_data = _as_mapping(research_evidence_index)
    blocked: list[Stage2BlockedReason] = []

    for validation in (
        validate_stage3_research_run_manifest(run_manifest),
        validate_signal_set(signal_set),
        validate_project_strategy_candidate(strategy_candidate),
        validate_research_evidence_index(research_evidence_index),
        validate_portfolio_risk_policy(portfolio_risk_policy),
    ):
        blocked.extend(validation.blocked_reasons)

    input_data = {str(key): str(value) for key, value in input_refs.items()}
    evidence_data = {str(key): str(value) for key, value in evidence_refs.items()}
    for name in STAGE2_DATA_REQUIREMENTS:
        if not _is_real_ref(input_data.get(name)):
            blocked.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 mature research package 缺少真实 P0 输入引用: {name}",
                    field=f"input_refs.{name}",
                    remediation="在研究机填入真实数据 release / PIT / 过滤 / 暴露 / 成本等 artifact ref。",
                )
            )
    for name in STAGE3_REQUIRED_EVIDENCE:
        if not _is_real_ref(evidence_data.get(name)):
            blocked.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 mature research package 缺少真实 evidence 引用: {name}",
                    field=f"evidence_refs.{name}",
                    remediation="补齐 run manifest、factor panel、label、评价、组合、风控和 runner preflight evidence ref。",
                )
            )

    manifest_release = str(manifest_data.get("data_release_ref") or "")
    index_release = str(evidence_index_data.get("data_release_ref") or "")
    if _is_real_ref(manifest_release) and _is_real_ref(index_release) and manifest_release != index_release:
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                message="run manifest 与 ResearchEvidenceIndex 的 data_release_ref 不一致。",
                field="data_release_ref",
                remediation="使用同一个冻结 data release / snapshot 作为准入包真相源。",
            )
        )

    package_claims = tuple(str(item) for item in (blocked_claims or STAGE3_FORBIDDEN_CLAIMS) if str(item))
    for claim in STAGE3_FORBIDDEN_CLAIMS:
        if claim not in package_claims:
            blocked.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 package 必须显式阻断未授权声明: {claim}",
                    field=f"blocked_claims.{claim}",
                    remediation="Stage 3 只能输出研究准入证据；runtime / simulation / live 需后续单独门禁。",
                )
            )

    validation_ref = factor_model_validation_report_ref or evidence_data.get("factor_model_validation_report_ref", "")
    if not _is_real_ref(validation_ref):
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                message="Stage 3 package 缺少 factor model validation report ref。",
                field="factor_model_validation_report_ref",
                remediation="补齐高级因子模型验证报告，或记录经批准的 waiver。",
            )
        )
    if not _is_real_ref(mature_strategy_admission_package_ref):
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                message="Stage 3 package 缺少 mature strategy admission package ref。",
                field="mature_strategy_admission_package_ref",
            )
        )
    if not _is_real_ref(runner_offline_preflight_ref):
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                message="Stage 3 package 缺少 runner offline preflight ref。",
                field="runner_offline_preflight_ref",
            )
        )
    if not _is_real_ref(observation_plan_ref):
        blocked.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                message="Stage 3 package 缺少 Stage 4 observation plan ref。",
                field="observation_plan_ref",
            )
        )

    deduped = tuple(_dedupe_reasons(blocked))
    return Stage3MatureResearchPackage(
        package_id=_stable_id(
            "stage3-mature-research-package",
            strategy_id,
            manifest_data.get("run_id"),
            manifest_data.get("config_hash"),
            manifest_data.get("data_release_ref"),
        ),
        strategy_id=strategy_id,
        status="blocked" if deduped else "stage3_research_ready_for_stage4_review",
        run_manifest=run_manifest,
        input_refs=input_data,
        evidence_refs=evidence_data,
        signal_set=signal_set,
        strategy_candidate=strategy_candidate,
        research_evidence_index=research_evidence_index,
        portfolio_risk_policy=portfolio_risk_policy,
        factor_model_validation_report_ref=validation_ref,
        mature_strategy_admission_package_ref=mature_strategy_admission_package_ref,
        runner_offline_preflight_ref=runner_offline_preflight_ref,
        observation_plan_ref=observation_plan_ref,
        blocked_claims=package_claims,
        unlock_conditions=tuple(
            str(item)
            for item in (
                unlock_conditions
                or (
                    "stage4_simulation_runtime_authorization",
                    "gateway_identity_revalidated",
                    "stage4_observation_gate_approved",
                    "independent_live_switch_cr_for_small_live_or_live",
                )
            )
            if str(item)
        ),
        blocked_reasons=deduped,
    )


def build_mature_admission_support_from_cr030_cr039_outputs(
    *,
    strategy_id: str,
    factor_specs: Sequence[FactorSpec | Mapping[str, Any]],
    cr039_candidate: Mapping[str, Any] | Any,
    signal_set: SignalSet | Mapping[str, Any],
    evidence_index: ResearchEvidenceIndex | Mapping[str, Any],
    risk_policy: PortfolioRiskPolicy | Mapping[str, Any],
    adapter: StrategyTypeAdapterContract | Mapping[str, Any] | None = None,
    cr030_admission_package_ref: str = "",
    cr039_run_id: str = "",
    cr039_admission_package_ref: str = "",
    permission_counters: PermissionCounters | Mapping[str, int] | None = None,
) -> Stage2MatureFrameworkBundle:
    selected_adapter = adapter or build_multifactor_strategy_type_adapter()
    support = build_stage2_mature_admission_support(
        strategy_id=strategy_id,
        adapter=selected_adapter,
        factor_specs=factor_specs,
        signal_set=signal_set,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
        permission_counters=permission_counters,
    )
    candidate = build_project_strategy_candidate_from_cr039(
        cr039_candidate=cr039_candidate,
        signal_set=signal_set,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
        source_run_id=cr039_run_id,
        source_admission_package_ref=cr039_admission_package_ref,
    )
    handoff = build_stage3_research_machine_handoff(
        strategy_id=strategy_id,
        mature_admission_support=support,
        strategy_candidate=candidate,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
    )
    blocked = tuple(_dedupe_reasons((*support.blocked_reasons, *candidate.blocked_reasons, *handoff.blocked_reasons)))

    return Stage2MatureFrameworkBundle(
        bundle_id=_stable_id("stage2-mature-framework-bundle", strategy_id, support.package_id, candidate.candidate_id),
        strategy_id=strategy_id,
        status="blocked" if blocked else "stage2_to_stage3_handoff_ready",
        mature_admission_support=support,
        strategy_candidate=candidate,
        stage3_research_machine_handoff=handoff,
        cr030_refs={
            "schema_version": CR030_STRATEGY_ADMISSION_PACKAGE_SCHEMA,
            "strategy_admission_package_ref": cr030_admission_package_ref,
            "role": "research_to_execution_boundary",
        },
        cr039_refs={
            "schema_version": CR039_STRATEGY_ADMISSION_PACKAGE_SCHEMA,
            "run_id": cr039_run_id,
            "strategy_admission_package_ref": cr039_admission_package_ref,
            "role": "strategy_candidate_research_result",
        },
        blocked_reasons=blocked,
    )


def validate_project_strategy_candidate(candidate: StrategyCandidate | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(candidate)
    reasons = _required_reasons(
        data,
        (
            "candidate_id",
            "strategy_id",
            "strategy_family",
            "admission",
            "research_status",
            "source_contract",
            "source_candidate_ref",
            "signal_set_ref",
            "evidence_index_ref",
            "portfolio_risk_policy_ref",
        ),
        code=MF_STAGE2_STRATEGY_CANDIDATE_INVALID,
    )
    if data.get("schema_version") not in {"", STRATEGY_CANDIDATE_SCHEMA}:
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE2_STRATEGY_CANDIDATE_INVALID,
                message="StrategyCandidate.schema_version 不匹配项目级合同。",
                field="schema_version",
            )
        )
    typed = tuple(_typed_from_payload(data.get("typed_unavailable")))
    return _validation("StrategyCandidate", str(data.get("candidate_id") or ""), reasons, typed_unavailable=typed)


def validate_stage3_research_machine_handoff(handoff: Stage3ResearchMachineHandoff | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(handoff)
    reasons = _required_reasons(
        data,
        (
            "handoff_id",
            "strategy_id",
            "stage2_support_ref",
            "strategy_candidate_ref",
            "required_inputs",
            "required_evidence",
            "data_lake_requirements",
            "execution_boundary",
            "blocked_until",
            "validation_plan",
        ),
        code=MF_STAGE3_HANDOFF_INVALID,
    )
    required_inputs = set(_sequence(data.get("required_inputs")))
    for item in sorted(set(STAGE2_DATA_REQUIREMENTS) - required_inputs):
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE3_HANDOFF_INVALID,
                message=f"Stage 3 handoff 缺少 required input: {item}",
                field=f"required_inputs.{item}",
            )
        )
    required_evidence = set(_sequence(data.get("required_evidence")))
    for item in sorted(set(STAGE3_REQUIRED_EVIDENCE) - required_evidence):
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE3_HANDOFF_INVALID,
                message=f"Stage 3 handoff 缺少 required evidence: {item}",
                field=f"required_evidence.{item}",
            )
        )
    return _validation("Stage3ResearchMachineHandoff", str(data.get("handoff_id") or ""), reasons)


def validate_stage3_research_run_manifest(
    manifest: Stage3ResearchRunManifest | Mapping[str, Any],
) -> Stage2ValidationResult:
    data = _as_mapping(manifest)
    reasons = _required_reasons(
        data,
        STAGE3_RUN_MANIFEST_REQUIRED_FIELDS,
        code=MF_STAGE3_RUN_MANIFEST_INVALID,
    )
    if not _is_real_ref(data.get("data_release_ref")):
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RUN_MANIFEST_INVALID,
                message="Stage 3 run manifest 必须引用真实冻结 data_release_ref。",
                field="data_release_ref",
                remediation="不要使用 current pointer 或 typed unavailable 作为唯一真相。",
            )
        )
    if not _as_mapping(data.get("factor_versions")):
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE3_RUN_MANIFEST_INVALID,
                message="Stage 3 run manifest 必须记录 factor_versions。",
                field="factor_versions",
            )
        )
    date_range = _as_mapping(data.get("date_range"))
    for field_name in ("start", "end"):
        if _is_blank(date_range.get(field_name)):
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RUN_MANIFEST_INVALID,
                    message=f"Stage 3 run manifest.date_range 缺少 {field_name}。",
                    field=f"date_range.{field_name}",
                )
            )
    return _validation("Stage3ResearchRunManifest", str(data.get("run_id") or ""), reasons)


def validate_stage3_mature_research_package(
    package: Stage3MatureResearchPackage | Mapping[str, Any],
) -> Stage2ValidationResult:
    data = _as_mapping(package)
    reasons = _required_reasons(
        data,
        (
            "package_id",
            "strategy_id",
            "run_manifest",
            "input_refs",
            "evidence_refs",
            "signal_set",
            "strategy_candidate",
            "research_evidence_index",
            "portfolio_risk_policy",
            "factor_model_validation_report_ref",
            "mature_strategy_admission_package_ref",
            "runner_offline_preflight_ref",
            "observation_plan_ref",
            "blocked_claims",
            "unlock_conditions",
        ),
        code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
    )
    reasons.extend(validate_stage3_research_run_manifest(_as_mapping(data.get("run_manifest"))).blocked_reasons)
    reasons.extend(validate_signal_set(_as_mapping(data.get("signal_set"))).blocked_reasons)
    reasons.extend(validate_project_strategy_candidate(_as_mapping(data.get("strategy_candidate"))).blocked_reasons)
    reasons.extend(validate_research_evidence_index(_as_mapping(data.get("research_evidence_index"))).blocked_reasons)
    reasons.extend(validate_portfolio_risk_policy(_as_mapping(data.get("portfolio_risk_policy"))).blocked_reasons)

    input_refs = {str(key): str(value) for key, value in _as_mapping(data.get("input_refs")).items()}
    evidence_refs = {str(key): str(value) for key, value in _as_mapping(data.get("evidence_refs")).items()}
    for name in STAGE2_DATA_REQUIREMENTS:
        if not _is_real_ref(input_refs.get(name)):
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 package input_refs 缺少真实引用: {name}",
                    field=f"input_refs.{name}",
                )
            )
    for name in STAGE3_REQUIRED_EVIDENCE:
        if not _is_real_ref(evidence_refs.get(name)):
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 package evidence_refs 缺少真实引用: {name}",
                    field=f"evidence_refs.{name}",
                )
            )
    blocked_claims = set(str(item) for item in _sequence(data.get("blocked_claims")))
    for claim in STAGE3_FORBIDDEN_CLAIMS:
        if claim not in blocked_claims:
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 package 未阻断未授权声明: {claim}",
                    field=f"blocked_claims.{claim}",
                )
            )
    for field_name in ("factor_model_validation_report_ref", "mature_strategy_admission_package_ref", "runner_offline_preflight_ref", "observation_plan_ref"):
        if not _is_real_ref(data.get(field_name)):
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE3_RESEARCH_PACKAGE_INVALID,
                    message=f"Stage 3 package 缺少真实引用: {field_name}",
                    field=field_name,
                )
            )
    reasons.extend(_reasons_from_payload(data.get("blocked_reasons")))
    return _validation("Stage3MatureResearchPackage", str(data.get("package_id") or ""), reasons)


def validate_stage2_no_lake(counters: PermissionCounters | Mapping[str, int] | None) -> Stage2ValidationResult:
    normalized = _normalize_permission_counters(counters)
    reasons = tuple(
        Stage2BlockedReason(
            code=MF_STAGE2_NO_LAKE_VIOLATION,
            message=f"Stage 2 no-lake 边界要求 {name}=0。",
            field=f"permission_counters.{name}",
            remediation="Stage 2 只能使用 fixture/schema/static/typed unavailable；真实数据湖操作推迟到 Stage 3。",
        )
        for name, value in normalized.items()
        if int(value or 0) != 0
    )
    return Stage2ValidationResult(
        status="blocked" if reasons else "pass",
        blocked_reasons=reasons,
        object_type="Stage2NoLakeBoundary",
        object_id=STAGE2_NO_LAKE,
        permission_counters=normalized,
    )


def validate_strategy_type_adapter(adapter: StrategyTypeAdapterContract | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(adapter)
    reasons = _required_reasons(data, ("adapter_id", "strategy_family", "input_contract", "output_contract", "evidence_required"))
    if data.get("strategy_family") != StrategyFamily.MULTIFACTOR.value:
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE2_REQUIRED_FIELD_MISSING,
                message="Stage 2 当前只实现 multifactor adapter。",
                field="strategy_family",
                remediation="事件型、机器学习和规则型策略需后续 CR 扩展 adapter。",
            )
        )
    output_contract = data.get("output_contract")
    if isinstance(output_contract, Mapping):
        required_outputs = {"signal_set", "strategy_candidate", "research_evidence_index", "mature_admission_support"}
        missing = sorted(required_outputs - set(output_contract))
        for field_name in missing:
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE2_REQUIRED_FIELD_MISSING,
                    message=f"adapter output_contract 缺少 {field_name}。",
                    field=f"output_contract.{field_name}",
                )
            )
    return _validation("StrategyTypeAdapterContract", str(data.get("adapter_id") or ""), reasons)


def validate_signal_set(signal_set: SignalSet | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(signal_set)
    reasons = _required_reasons(
        data,
        ("signal_set_id", "strategy_family", "trade_date", "universe_ref", "signal_schema", "signals", "available_at", "lineage_ref"),
        code=MF_STAGE2_SIGNAL_SET_INVALID,
    )
    if data.get("strategy_family") != StrategyFamily.MULTIFACTOR.value:
        reasons.append(
            Stage2BlockedReason(
                code=MF_STAGE2_SIGNAL_SET_INVALID,
                message="SignalSet.strategy_family 必须是 multifactor。",
                field="strategy_family",
            )
        )
    typed = tuple(_typed_from_payload(data.get("typed_unavailable")))
    return _validation("SignalSet", str(data.get("signal_set_id") or ""), reasons, typed_unavailable=typed)


def validate_research_evidence_index(index: ResearchEvidenceIndex | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(index)
    reasons = _required_reasons(
        data,
        ("index_id", "data_release_ref", "run_manifest_ref", "limitations"),
        code=MF_STAGE2_EVIDENCE_INDEX_INCOMPLETE,
    )
    for field_name in ("metric_refs", "lineage_refs"):
        if field_name not in data:
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE2_EVIDENCE_INDEX_INCOMPLETE,
                    message=f"必填字段缺失: {field_name}",
                    field=field_name,
                    remediation="Stage 2 允许空映射，但字段必须存在；真实 refs 缺口用 typed unavailable 表达。",
                )
            )
    typed = tuple(_typed_from_payload(data.get("typed_unavailable")))
    return _validation("ResearchEvidenceIndex", str(data.get("index_id") or ""), reasons, typed_unavailable=typed)


def validate_portfolio_risk_policy(policy: PortfolioRiskPolicy | Mapping[str, Any]) -> Stage2ValidationResult:
    data = _as_mapping(policy)
    reasons = _required_reasons(
        data,
        (
            "policy_id",
            "top_n",
            "max_weight",
            "turnover_limit",
            "industry_limit",
            "style_limit",
            "capacity_assumption",
            "fee_slippage_ref",
            "stop_conditions",
            "version",
            "effective_from",
            "release_id",
            "universe_policy_ref",
            "delisting_policy",
            "st_policy",
        ),
        code=MF_STAGE2_RISK_POLICY_INVALID,
    )
    for field_name in ("top_n", "max_weight", "turnover_limit"):
        if field_name in data and not _positive_number(data.get(field_name)):
            reasons.append(
                Stage2BlockedReason(
                    code=MF_STAGE2_RISK_POLICY_INVALID,
                    message=f"{field_name} 必须为正数。",
                    field=field_name,
                )
            )
    return _validation("PortfolioRiskPolicy", str(data.get("policy_id") or ""), reasons)


def typed_unavailable(
    code: str,
    message: str,
    missing_inputs: Sequence[str],
    *,
    remediation: str = "进入 Stage 3 后在研究机连接数据湖并记录 release / lineage / evidence index。",
) -> TypedUnavailable:
    return TypedUnavailable(
        code=code,
        message=message,
        missing_inputs=tuple(str(item) for item in missing_inputs if str(item)),
        remediation=remediation,
    )


def _validation(
    object_type: str,
    object_id: str,
    reasons: Sequence[Stage2BlockedReason],
    *,
    typed_unavailable: Sequence[TypedUnavailable] = (),
) -> Stage2ValidationResult:
    return Stage2ValidationResult(
        status="blocked" if reasons else ("stage2_ready_with_typed_unavailable" if typed_unavailable else "pass"),
        blocked_reasons=tuple(_dedupe_reasons(reasons)),
        typed_unavailable=tuple(_dedupe_typed(typed_unavailable)),
        object_type=object_type,
        object_id=object_id,
        permission_counters={key: 0 for key in STAGE2_FORBIDDEN_COUNTERS},
    )


def _required_reasons(
    data: Mapping[str, Any],
    required_fields: Sequence[str],
    *,
    code: str = MF_STAGE2_REQUIRED_FIELD_MISSING,
) -> list[Stage2BlockedReason]:
    reasons: list[Stage2BlockedReason] = []
    for field_name in required_fields:
        if field_name not in data or _is_blank(data.get(field_name)):
            reasons.append(
                Stage2BlockedReason(
                    code=code,
                    message=f"必填字段缺失: {field_name}",
                    field=field_name,
                    remediation="补齐 Stage 2 框架合同字段后再进入下游。",
                )
            )
    return reasons


def _normalize_permission_counters(counters: PermissionCounters | Mapping[str, int] | None) -> dict[str, int]:
    if counters is None:
        return {key: 0 for key in STAGE2_FORBIDDEN_COUNTERS}
    data = _as_mapping(counters)
    return {key: int(data.get(key, 0) or 0) for key in STAGE2_FORBIDDEN_COUNTERS}


def _factor_spec_ref(spec: FactorSpec | Mapping[str, Any]) -> dict[str, Any]:
    data = _as_mapping(spec)
    return {
        "schema_version": "factor_spec_ref_v1",
        "factor_id": str(data.get("factor_id") or ""),
        "version": str(data.get("version") or ""),
        "input_fields": tuple(str(item) for item in _sequence(data.get("input_fields"))),
        "available_at": _as_mapping(data.get("availability_policy")).get("available_at", ""),
        "lineage_ref": _as_mapping(data.get("data_lineage")).get("source_dataset", ""),
    }


def _object_to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    return _as_mapping(value)


def _reasons_from_payload(value: Any) -> list[Stage2BlockedReason]:
    result: list[Stage2BlockedReason] = []
    for item in _sequence(value):
        if isinstance(item, Stage2BlockedReason):
            result.append(item)
            continue
        data = _as_mapping(item)
        if not data:
            continue
        result.append(
            Stage2BlockedReason(
                code=str(data.get("code") or ""),
                message=str(data.get("message") or ""),
                field=str(data.get("field") or ""),
                severity=str(data.get("severity") or "blocker"),
                remediation=str(data.get("remediation") or ""),
                evidence_ref=str(data.get("evidence_ref") or ""),
            )
        )
    return result


def _ref(data: Mapping[str, Any], id_field: str, schema_version: str) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        id_field: str(data.get(id_field) or ""),
        "evidence_ref": str(data.get(id_field) or ""),
    }


def _has_ref(name: str, data_release_ref: str, metric_refs: Mapping[str, str], lineage_refs: Mapping[str, str]) -> bool:
    if name == "data_release_ref":
        return bool(data_release_ref)
    return bool(metric_refs.get(name) or lineage_refs.get(name))


def _typed_from_payload(value: Any) -> list[TypedUnavailable]:
    items = _sequence(value)
    result: list[TypedUnavailable] = []
    for item in items:
        if isinstance(item, TypedUnavailable):
            result.append(item)
            continue
        data = _as_mapping(item)
        if not data:
            continue
        result.append(
            TypedUnavailable(
                code=str(data.get("code") or ""),
                message=str(data.get("message") or ""),
                missing_inputs=tuple(str(part) for part in _sequence(data.get("missing_inputs"))),
                required_stage=str(data.get("required_stage") or "Stage 3"),
                remediation=str(data.get("remediation") or ""),
                severity=str(data.get("severity") or "blocking_until_stage3"),
            )
        )
    return result


def _dedupe_reasons(reasons: Sequence[Stage2BlockedReason]) -> tuple[Stage2BlockedReason, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[Stage2BlockedReason] = []
    for reason in reasons:
        key = (reason.code, reason.field)
        if key in seen:
            continue
        seen.add(key)
        result.append(reason)
    return tuple(result)


def _dedupe_typed(items: Sequence[TypedUnavailable]) -> tuple[TypedUnavailable, ...]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    result: list[TypedUnavailable] = []
    for item in items:
        key = (item.code, item.missing_inputs)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def _stable_id(prefix: str, *parts: Any) -> str:
    payload = json.dumps(_json_safe(parts), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{prefix}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    slots = getattr(type(value), "__slots__", ())
    if slots:
        return _json_safe({slot: getattr(value, slot) for slot in slots if hasattr(value, slot)})
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return not value
    return False


def _is_real_ref(value: Any) -> bool:
    if _is_blank(value):
        return False
    text = str(value).strip()
    return not (
        text == "required"
        or text.startswith("typed_unavailable:")
        or text.startswith("fixture://stage2/")
        or text.startswith("placeholder:")
    )


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return str(value)
