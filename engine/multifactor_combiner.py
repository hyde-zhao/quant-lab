"""CR030-S05 多因子组合与组合计划合同。

本模块只实现项目自有的离线多因子组合 schema、规则权重 / 轻量线性
组合、fail-closed 输入校验和 portfolio plan draft。它不导入或运行
optimizer / cvxpy / Qlib / vectorbt / broker runtime，不读取凭据，不
触发 provider / lake / publish / QMT / simulation / live。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from enum import Enum
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from engine.factor_evaluation import FactorEvaluationReport
from engine.multifactor_contracts import FORBIDDEN_OPERATION_COUNTERS, PermissionCounters


MULTIFACTOR_COMBINER_SCHEMA = "multifactor_combiner_v1"
MULTIFACTOR_PORTFOLIO_PLAN_SCHEMA = "multifactor_portfolio_plan_v1"
PORTFOLIO_PLAN_DRAFT_SCHEMA = "multifactor_portfolio_plan_draft_v1"

MF_COMBINER_NO_REPORTS = "MF_COMBINER_NO_REPORTS"
MF_COMBINER_REPORT_BLOCKED = "MF_COMBINER_REPORT_BLOCKED"
MF_COMBINER_CLAIM_BOUNDARY_MISSING = "MF_COMBINER_CLAIM_BOUNDARY_MISSING"
MF_COMBINER_BENCHMARK_MISSING = "MF_COMBINER_BENCHMARK_MISSING"
MF_COMBINER_COST_MISSING = "MF_COMBINER_COST_MISSING"
MF_COMBINER_CAPACITY_MISSING = "MF_COMBINER_CAPACITY_MISSING"
MF_COMBINER_EXPOSURE_MISSING = "MF_COMBINER_EXPOSURE_MISSING"
MF_COMBINER_WEIGHTING_POLICY_INVALID = "MF_COMBINER_WEIGHTING_POLICY_INVALID"
MF_COMBINER_WEIGHT_SOURCE_MISSING = "MF_COMBINER_WEIGHT_SOURCE_MISSING"
MF_COMBINER_FORBIDDEN_OPERATION_NONZERO = "MF_COMBINER_FORBIDDEN_OPERATION_NONZERO"
MF_OPTIMIZER_DEFERRED = "MF_OPTIMIZER_DEFERRED"
MF_BROKER_ORDER_FORBIDDEN = "MF_BROKER_ORDER_FORBIDDEN"

PASS_STATUSES = {"pass", "warn", "research_limited"}
BLOCKED_STATUSES = {"blocked", "fail"}
ALLOWED_WEIGHTING_POLICIES = {"rule_weight", "linear_score"}
DEFAULT_NOT_AUTHORIZED_CLAIMS = (
    "production_valid",
    "qmt_ready",
    "simulation_ready",
    "live_ready",
    "tradable_evidence",
)
OPTIMIZER_DEFERRED_MARKERS = (
    "optimizer",
    "cvxpy",
    "enhancedindexing",
    "enhanced_indexing",
    "vectorbt",
    "ml_weighting",
    "machine_learning_weighting",
    "risk_model",
    "risk model",
    "qlib enhanced",
)
BROKER_ORDER_FIELD_MARKERS = (
    "order_submit",
    "order_cancel",
    "broker_execution",
    "broker_order_id",
    "account_query",
    "account_id",
    "qmt_api_call",
    "xtquant_call",
    "miniqmt_call",
    "trade_password",
)


class MultiFactorPlanStatus(str, Enum):
    PASS = "pass"
    RESEARCH_LIMITED = "research_limited"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class MultiFactorBlockedReason:
    code: str
    message: str
    field: str = ""
    severity: str = "blocker"
    remediation: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class MultiFactorClaim:
    claim: str
    status: str
    reason: str
    code: str = ""
    limitation: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class FactorWeight:
    factor_id: str
    report_id: str
    weight: float
    raw_score: float
    policy: str
    reason: str
    source_metric_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class CombinerValidationResult:
    status: str
    accepted_reports: tuple[Mapping[str, Any], ...] = ()
    excluded_reports: tuple[Mapping[str, Any], ...] = ()
    blocked_reasons: tuple[MultiFactorBlockedReason, ...] = ()
    research_limited_reasons: tuple[MultiFactorBlockedReason, ...] = ()
    permission_counters: Mapping[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status in {MultiFactorPlanStatus.PASS.value, MultiFactorPlanStatus.RESEARCH_LIMITED.value}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "accepted_reports": [_report_ref(report) for report in self.accepted_reports],
            "excluded_reports": [_report_ref(report) for report in self.excluded_reports],
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "research_limited_reasons": [reason.to_dict() for reason in self.research_limited_reasons],
            "permission_counters": dict(self.permission_counters),
        }


@dataclass(frozen=True, slots=True)
class BrokerOrderValidationResult:
    status: str
    blocked_reasons: tuple[MultiFactorBlockedReason, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
        }


@dataclass(frozen=True, slots=True)
class MultiFactorCombiner:
    combiner_id: str
    factor_inputs: tuple[Any, ...]
    normalization: Mapping[str, Any]
    winsorization: Mapping[str, Any]
    neutralization: Mapping[str, Any]
    orthogonalization: Mapping[str, Any]
    weighting_policy: Mapping[str, Any] | str
    missing_policy: Mapping[str, Any]
    constraints: Mapping[str, Any]
    rebalance_frequency: str
    turnover_cap: float | Mapping[str, Any]
    cost_config: Mapping[str, Any]
    benchmark: Mapping[str, Any] | str
    freeze_policy: Mapping[str, Any]
    blocked_reason: tuple[MultiFactorBlockedReason, ...] = ()
    capacity: Mapping[str, Any] = field(default_factory=dict)
    optimizer_policy: Mapping[str, Any] = field(default_factory=lambda: {"enabled": False})
    permission_counters: PermissionCounters | Mapping[str, int] = field(default_factory=PermissionCounters)
    schema_version: str = MULTIFACTOR_COMBINER_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class MultiFactorPortfolioPlan:
    plan_id: str
    combiner_id: str
    status: str
    factor_weights: tuple[FactorWeight, ...]
    target_weights: Mapping[str, float]
    target_count: int
    benchmark_deviation: Mapping[str, Any]
    cost_summary: Mapping[str, Any]
    capacity_summary: Mapping[str, Any]
    rebalance_frequency: str
    rebalance_dates: tuple[str, ...]
    turnover_cap: Any
    constraints: Mapping[str, Any]
    freeze_policy: Mapping[str, Any]
    allowed_claims: tuple[MultiFactorClaim, ...]
    blocked_reasons: tuple[MultiFactorBlockedReason, ...]
    blocked_claims: tuple[MultiFactorClaim, ...]
    lineage: Mapping[str, Any]
    weight_sources: Mapping[str, Any]
    limitations: tuple[str, ...]
    draft_handoff: Mapping[str, Any]
    permission_counters: Mapping[str, int] = field(default_factory=dict)
    schema_version: str = MULTIFACTOR_PORTFOLIO_PLAN_SCHEMA
    not_broker_order: bool = True
    qmt_allowed: bool = False
    simulation_allowed: bool = False
    live_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))

    @property
    def production_valid_claim_count(self) -> int:
        return sum(1 for claim in self.allowed_claims if claim.claim in DEFAULT_NOT_AUTHORIZED_CLAIMS)


def build_multifactor_portfolio_plan(
    reports: Sequence[FactorEvaluationReport | Mapping[str, Any] | Any],
    combiner_config: MultiFactorCombiner | Mapping[str, Any],
    constraints: Mapping[str, Any] | None = None,
) -> MultiFactorPortfolioPlan:
    config = _config_mapping(combiner_config)
    merged_constraints = {**_mapping(config.get("constraints")), **_mapping(constraints)}
    validation = validate_combiner_inputs(reports, {**config, "constraints": merged_constraints})
    deferred_reasons = detect_optimizer_deferred_request({**config, "constraints": merged_constraints})
    blocked_reasons = list(validation.blocked_reasons) + list(deferred_reasons)

    if blocked_reasons:
        return _blocked_plan(config, merged_constraints, validation, tuple(blocked_reasons))

    factor_weights = compute_rule_weights(validation.accepted_reports, config.get("weighting_policy") or {})
    constrained_weights, constraint_reasons = apply_portfolio_constraints(factor_weights, merged_constraints)
    all_limited_reasons = tuple(validation.research_limited_reasons) + tuple(constraint_reasons)
    status = (
        MultiFactorPlanStatus.RESEARCH_LIMITED.value
        if all_limited_reasons
        else MultiFactorPlanStatus.PASS.value
    )
    blocked_claims = _blocked_claims(tuple(all_limited_reasons))
    allowed_claims = (
        MultiFactorClaim(
            claim="multifactor_research_plan",
            status="allowed",
            code="MF_COMBINER_RESEARCH_PLAN_ALLOWED",
            reason="仅允许作为项目自有多因子研究和后续 S07 admission 输入，不构成生产、QMT、模拟盘或实盘声明。",
            limitation="后续准入、模拟盘或真实交易必须走独立 CR / per-run authorization。",
            evidence_ref=str(config.get("combiner_id") or "multifactor_combiner"),
        ),
    )
    plan = MultiFactorPortfolioPlan(
        plan_id=_plan_id(config),
        combiner_id=str(config.get("combiner_id") or "multifactor_combiner"),
        status=status,
        factor_weights=tuple(constrained_weights),
        target_weights={weight.factor_id: weight.weight for weight in constrained_weights},
        target_count=int(_number(merged_constraints.get("target_count")) or len(constrained_weights)),
        benchmark_deviation=_benchmark_deviation(config, merged_constraints),
        cost_summary=_cost_summary(config),
        capacity_summary=_capacity_summary(config, merged_constraints),
        rebalance_frequency=str(config.get("rebalance_frequency") or "unspecified"),
        rebalance_dates=tuple(str(item) for item in _sequence(merged_constraints.get("rebalance_dates"))),
        turnover_cap=config.get("turnover_cap"),
        constraints=_json_safe(merged_constraints),
        freeze_policy=_json_safe(_mapping(config.get("freeze_policy"))),
        allowed_claims=allowed_claims,
        blocked_reasons=all_limited_reasons,
        blocked_claims=blocked_claims,
        lineage=_lineage(validation.accepted_reports, config),
        weight_sources=_weight_sources(constrained_weights),
        limitations=_plan_limitations(status),
        draft_handoff={},
        permission_counters=dict(validation.permission_counters),
    )
    draft = to_portfolio_plan_draft(plan)
    return _replace_plan_draft(plan, draft)


def validate_combiner_inputs(
    reports: Sequence[FactorEvaluationReport | Mapping[str, Any] | Any],
    constraints: Mapping[str, Any] | None = None,
) -> CombinerValidationResult:
    cfg = _mapping(constraints)
    merged_constraints = _mapping(cfg.get("constraints"))
    accepted: list[Mapping[str, Any]] = []
    excluded: list[Mapping[str, Any]] = []
    excluded_reasons: list[MultiFactorBlockedReason] = []
    blocked: list[MultiFactorBlockedReason] = []
    limited: list[MultiFactorBlockedReason] = []
    counters = _normalise_permission_counters(cfg.get("permission_counters"))

    for report in reports:
        data = _report_mapping(report)
        counters = _merge_counters(counters, _normalise_permission_counters(data.get("permission_counters")))
        status = str(data.get("status") or "")
        if status in BLOCKED_STATUSES:
            excluded.append(data)
            excluded_reasons.append(
                _reason(
                    MF_COMBINER_REPORT_BLOCKED,
                    f"S04 report 不可进入组合: {data.get('report_id') or data.get('factor_id') or '<unknown>'}",
                    field="reports",
                    severity="warning",
                    evidence_ref=str(data.get("report_id") or ""),
                    remediation="仅使用 pass / warn / research_limited 且声明边界完整的 report。",
                )
            )
            continue
        if status not in PASS_STATUSES:
            excluded.append(data)
            excluded_reasons.append(
                _reason(
                    MF_COMBINER_REPORT_BLOCKED,
                    f"S04 report.status 非法或缺失: {status or '<blank>'}",
                    field="reports.status",
                    severity="warning",
                    evidence_ref=str(data.get("report_id") or ""),
                )
            )
            continue
        if not _has_research_claim(data):
            excluded.append(data)
            excluded_reasons.append(
                _reason(
                    MF_COMBINER_CLAIM_BOUNDARY_MISSING,
                    "S04 report 缺少 single_factor_research_evidence allowed claim，不能进入组合。",
                    field="reports.allowed_claims",
                    severity="warning",
                    evidence_ref=str(data.get("report_id") or ""),
                )
            )
            continue
        accepted.append(data)
        if status == "research_limited":
            limited.append(
                _reason(
                    "MF_COMBINER_INPUT_RESEARCH_LIMITED",
                    "至少一个输入 report 为 research_limited，组合计划不得扩大声明。",
                    field="reports.status",
                    severity="warning",
                    evidence_ref=str(data.get("report_id") or ""),
                )
            )

    if not accepted:
        blocked.extend(excluded_reasons)
        blocked.append(
            _reason(
                MF_COMBINER_NO_REPORTS,
                "没有可组合的 S04 report。",
                field="reports",
                remediation="补充 pass / warn / research_limited report 后再组合。",
            )
        )
    else:
        limited.extend(excluded_reasons)

    if _is_blank(_first_non_blank(cfg.get("benchmark"), merged_constraints.get("benchmark"))):
        blocked.append(
            _reason(
                MF_COMBINER_BENCHMARK_MISSING,
                "benchmark 缺失，不能生成可复核组合计划。",
                field="benchmark",
            )
        )
    if _is_blank(cfg.get("rebalance_frequency")):
        limited.append(
            _reason(
                "MF_COMBINER_REBALANCE_MISSING",
                "rebalance_frequency 缺失，组合计划仅可作为 research_limited 草稿。",
                field="rebalance_frequency",
                severity="warning",
            )
        )
    if _is_blank(cfg.get("turnover_cap")):
        limited.append(
            _reason(
                "MF_COMBINER_TURNOVER_CAP_MISSING",
                "turnover_cap 缺失，组合计划不能声明换手受控。",
                field="turnover_cap",
                severity="warning",
            )
        )
    if _is_blank(cfg.get("cost_config")):
        limited.append(
            _reason(
                MF_COMBINER_COST_MISSING,
                "cost_config 缺失，组合计划不能声明成本后有效。",
                field="cost_config",
                severity="warning",
            )
        )
    if _is_blank(_first_non_blank(cfg.get("capacity"), merged_constraints.get("capacity"))):
        limited.append(
            _reason(
                MF_COMBINER_CAPACITY_MISSING,
                "capacity 约束缺失，组合计划不能声明容量可用。",
                field="capacity",
                severity="warning",
            )
        )
    if _neutralization_enabled(cfg.get("neutralization")) and _is_blank(_first_non_blank(cfg.get("exposure"), merged_constraints.get("exposure"))):
        limited.append(
            _reason(
                MF_COMBINER_EXPOSURE_MISSING,
                "配置要求中性化但缺 exposure evidence，组合计划不能声明中性化或 pure alpha。",
                field="neutralization.exposure",
                severity="warning",
            )
        )

    for name, count in counters.items():
        if count:
            blocked.append(
                _reason(
                    MF_COMBINER_FORBIDDEN_OPERATION_NONZERO,
                    f"forbidden permission counter 非 0: {name}={count}",
                    field=f"permission_counters.{name}",
                    remediation="重置真实操作计数为 0，并确认未触发未授权操作。",
                )
            )

    status = MultiFactorPlanStatus.BLOCKED.value if blocked else (
        MultiFactorPlanStatus.RESEARCH_LIMITED.value if limited else MultiFactorPlanStatus.PASS.value
    )
    return CombinerValidationResult(
        status=status,
        accepted_reports=tuple(accepted),
        excluded_reports=tuple(excluded),
        blocked_reasons=tuple(_dedupe_reasons(blocked)),
        research_limited_reasons=tuple(_dedupe_reasons(limited)),
        permission_counters=counters,
    )


def compute_rule_weights(
    reports: Sequence[FactorEvaluationReport | Mapping[str, Any] | Any],
    weighting_policy: Mapping[str, Any] | str,
) -> tuple[FactorWeight, ...]:
    policy = _weighting_policy_mapping(weighting_policy)
    policy_name = str(policy.get("policy") or policy.get("type") or weighting_policy or "rule_weight")
    if policy_name not in ALLOWED_WEIGHTING_POLICIES:
        raise ValueError(f"{MF_COMBINER_WEIGHTING_POLICY_INVALID}: {policy_name}")

    report_data = tuple(_report_mapping(report) for report in reports)
    if not report_data:
        raise ValueError(f"{MF_COMBINER_NO_REPORTS}: reports")

    if policy_name == "rule_weight":
        raw_scores = _explicit_rule_scores(report_data, policy)
        reason = "规则权重来自 weighting_policy.weights；缺省时使用等权。"
        refs = ("weighting_policy.weights",)
    else:
        raw_scores = _linear_scores(report_data, policy)
        reason = "轻量线性组合来自 ICIR、RankIC、coverage 和 turnover 的标准库计算。"
        refs = ("ICIR", "RankIC", "coverage", "turnover")

    total = sum(max(score, 0.0) for _, score in raw_scores)
    if total <= 0:
        total = float(len(raw_scores))
        raw_scores = tuple((report, 1.0) for report, _ in raw_scores)

    return tuple(
        FactorWeight(
            factor_id=str(report.get("factor_id") or report.get("report_id") or f"factor_{index + 1}"),
            report_id=str(report.get("report_id") or ""),
            weight=max(score, 0.0) / total,
            raw_score=float(score),
            policy=policy_name,
            reason=reason,
            source_metric_refs=refs,
        )
        for index, (report, score) in enumerate(raw_scores)
    )


def apply_portfolio_constraints(
    weights: Sequence[FactorWeight | Mapping[str, Any]],
    constraints: Mapping[str, Any] | None = None,
) -> tuple[tuple[FactorWeight, ...], tuple[MultiFactorBlockedReason, ...]]:
    cfg = _mapping(constraints)
    factor_weights = tuple(_factor_weight(weight) for weight in weights)
    limited: list[MultiFactorBlockedReason] = []
    max_factor_weight = _number(cfg.get("max_factor_weight"))
    constrained = factor_weights
    if max_factor_weight is not None and 0 < max_factor_weight < 1:
        constrained = _cap_and_redistribute(factor_weights, max_factor_weight)
        if any(weight.weight > max_factor_weight + 1e-12 for weight in factor_weights):
            limited.append(
                _reason(
                    "MF_COMBINER_FACTOR_WEIGHT_CAPPED",
                    f"因子权重超过上限，已按 max_factor_weight={max_factor_weight} 约束重分配。",
                    field="constraints.max_factor_weight",
                    severity="warning",
                )
            )
    turnover_cap = _number(cfg.get("turnover_cap"))
    expected_turnover = _number(cfg.get("expected_turnover"))
    if turnover_cap is not None and expected_turnover is not None and expected_turnover > turnover_cap:
        limited.append(
            _reason(
                "MF_COMBINER_TURNOVER_LIMITED",
                f"expected_turnover={expected_turnover} 超过 turnover_cap={turnover_cap}，组合计划仅 research_limited。",
                field="constraints.expected_turnover",
                severity="warning",
            )
        )
    return tuple(constrained), tuple(limited)


def detect_optimizer_deferred_request(config: Mapping[str, Any] | Any) -> tuple[MultiFactorBlockedReason, ...]:
    text_hits = _deferred_hits(config)
    enabled_optimizer = _optimizer_enabled(config)
    if enabled_optimizer and "optimizer" not in text_hits:
        text_hits = tuple(sorted(set(text_hits) | {"optimizer"}))
    return tuple(
        _reason(
            MF_OPTIMIZER_DEFERRED,
            f"P0 不启用 optimizer / ML workflow / external runtime，已转后续 Spike: {hit}",
            field="optimizer_policy",
            remediation="如需优化器、风险模型或外部 runtime，由 meta-po 另起 Spike / CR 并重新授权。",
        )
        for hit in text_hits
    )


def assert_no_broker_order(plan: MultiFactorPortfolioPlan | Mapping[str, Any] | Any) -> BrokerOrderValidationResult:
    payload = plan.to_dict() if isinstance(plan, MultiFactorPortfolioPlan) else _json_safe(plan)
    violations: list[MultiFactorBlockedReason] = []
    for path, value in _walk_items(payload):
        path_key = path.lower().replace("-", "_")
        if any(marker in path_key for marker in BROKER_ORDER_FIELD_MARKERS):
            violations.append(
                _reason(
                    MF_BROKER_ORDER_FORBIDDEN,
                    f"组合计划含 broker/order/account 执行字段: {path}",
                    field=path,
                    remediation="MultiFactorPortfolioPlan 只能是离线组合计划或 S07 admission 输入。",
                )
            )
        if path_key.endswith("not_broker_order") and value is not True:
            violations.append(
                _reason(
                    MF_BROKER_ORDER_FORBIDDEN,
                    "not_broker_order 必须为 true。",
                    field=path,
                )
            )
    return BrokerOrderValidationResult(
        status="blocked" if violations else "pass",
        blocked_reasons=tuple(_dedupe_reasons(violations)),
    )


def to_portfolio_plan_draft(plan: MultiFactorPortfolioPlan | Mapping[str, Any]) -> dict[str, Any]:
    data = plan.to_dict() if isinstance(plan, MultiFactorPortfolioPlan) else _mapping(plan)
    return {
        "schema_version": PORTFOLIO_PLAN_DRAFT_SCHEMA,
        "plan_id": data.get("plan_id"),
        "combiner_id": data.get("combiner_id"),
        "status": data.get("status"),
        "target_weights": _json_safe(data.get("target_weights") or {}),
        "target_count": data.get("target_count"),
        "benchmark_deviation": _json_safe(data.get("benchmark_deviation") or {}),
        "cost_summary": _json_safe(data.get("cost_summary") or {}),
        "capacity_summary": _json_safe(data.get("capacity_summary") or {}),
        "rebalance_frequency": data.get("rebalance_frequency"),
        "freeze_policy": _json_safe(data.get("freeze_policy") or {}),
        "limitations": list(data.get("limitations") or ()),
        "not_broker_order": True,
        "consumer": "CR030-S07-admission-package-or-research-runner",
        "not_authorization": True,
    }


def _blocked_plan(
    config: Mapping[str, Any],
    constraints: Mapping[str, Any],
    validation: CombinerValidationResult,
    blocked_reasons: tuple[MultiFactorBlockedReason, ...],
) -> MultiFactorPortfolioPlan:
    blocked_claims = _blocked_claims(blocked_reasons)
    plan = MultiFactorPortfolioPlan(
        plan_id=_plan_id(config),
        combiner_id=str(config.get("combiner_id") or "multifactor_combiner"),
        status=MultiFactorPlanStatus.BLOCKED.value,
        factor_weights=(),
        target_weights={},
        target_count=0,
        benchmark_deviation=_benchmark_deviation(config, constraints),
        cost_summary=_cost_summary(config),
        capacity_summary=_capacity_summary(config, constraints),
        rebalance_frequency=str(config.get("rebalance_frequency") or "unspecified"),
        rebalance_dates=tuple(str(item) for item in _sequence(constraints.get("rebalance_dates"))),
        turnover_cap=config.get("turnover_cap"),
        constraints=_json_safe(constraints),
        freeze_policy=_json_safe(_mapping(config.get("freeze_policy"))),
        allowed_claims=(),
        blocked_reasons=blocked_reasons,
        blocked_claims=blocked_claims,
        lineage=_lineage(validation.accepted_reports, config),
        weight_sources={},
        limitations=_plan_limitations(MultiFactorPlanStatus.BLOCKED.value),
        draft_handoff={},
        permission_counters=dict(validation.permission_counters),
    )
    return _replace_plan_draft(plan, to_portfolio_plan_draft(plan))


def _replace_plan_draft(plan: MultiFactorPortfolioPlan, draft: Mapping[str, Any]) -> MultiFactorPortfolioPlan:
    data = plan.to_dict()
    data["factor_weights"] = tuple(plan.factor_weights)
    data["allowed_claims"] = tuple(plan.allowed_claims)
    data["blocked_reasons"] = tuple(plan.blocked_reasons)
    data["blocked_claims"] = tuple(plan.blocked_claims)
    data["rebalance_dates"] = tuple(plan.rebalance_dates)
    data["limitations"] = tuple(plan.limitations)
    data["draft_handoff"] = _json_safe(draft)
    return MultiFactorPortfolioPlan(**data)


def _config_mapping(config: MultiFactorCombiner | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(config, MultiFactorCombiner):
        return config.to_dict()
    return _mapping(config)


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return (value,)


def _report_mapping(report: FactorEvaluationReport | Mapping[str, Any] | Any) -> Mapping[str, Any]:
    if isinstance(report, FactorEvaluationReport):
        return report.to_dict()
    data = _mapping(report)
    if data:
        return data
    return {"status": "", "report_id": str(report)}


def _report_ref(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "report_id": report.get("report_id"),
        "factor_id": report.get("factor_id"),
        "status": report.get("status"),
    }


def _has_research_claim(report: Mapping[str, Any]) -> bool:
    for claim in _sequence(report.get("allowed_claims")):
        data = _mapping(claim)
        claim_name = str(data.get("claim") or claim)
        status = str(data.get("status") or "allowed")
        if claim_name == "single_factor_research_evidence" and status == "allowed":
            return True
    return False


def _weighting_policy_mapping(policy: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(policy, str):
        return {"policy": policy}
    return _mapping(policy)


def _explicit_rule_scores(
    reports: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> tuple[tuple[Mapping[str, Any], float], ...]:
    weights = _mapping(policy.get("weights"))
    if not weights:
        return tuple((report, 1.0) for report in reports)
    scored: list[tuple[Mapping[str, Any], float]] = []
    for report in reports:
        factor_id = str(report.get("factor_id") or "")
        report_id = str(report.get("report_id") or "")
        score = _number(weights.get(factor_id))
        if score is None:
            score = _number(weights.get(report_id))
        if score is None:
            score = _number(policy.get("default_weight"))
        if score is None:
            raise ValueError(f"{MF_COMBINER_WEIGHT_SOURCE_MISSING}: {factor_id or report_id}")
        scored.append((report, max(score, 0.0)))
    return tuple(scored)


def _linear_scores(
    reports: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> tuple[tuple[Mapping[str, Any], float], ...]:
    metric_weights = {
        "ICIR": 0.45,
        "RankIC": 0.30,
        "coverage": 0.20,
        "turnover": -0.05,
        **{str(key): float(value) for key, value in _mapping(policy.get("metric_weights")).items() if _number(value) is not None},
    }
    scored: list[tuple[Mapping[str, Any], float]] = []
    for report in reports:
        icir = _metric_number(report.get("ICIR"), ("value", "mean"))
        rank_ic = _metric_number(report.get("RankIC"), ("value", "mean"))
        coverage = _metric_number(report.get("coverage"), ("matched_ratio", "value"))
        turnover = _metric_number(report.get("turnover"), ("value", "mean"))
        score = (
            metric_weights["ICIR"] * abs(icir or 0.0)
            + metric_weights["RankIC"] * abs(rank_ic or 0.0)
            + metric_weights["coverage"] * max(coverage or 0.0, 0.0)
            + metric_weights["turnover"] * max(turnover or 0.0, 0.0)
        )
        scored.append((report, max(score, 0.0)))
    return tuple(scored)


def _factor_weight(value: FactorWeight | Mapping[str, Any]) -> FactorWeight:
    if isinstance(value, FactorWeight):
        return value
    data = _mapping(value)
    return FactorWeight(
        factor_id=str(data.get("factor_id") or ""),
        report_id=str(data.get("report_id") or ""),
        weight=float(data.get("weight") or 0.0),
        raw_score=float(data.get("raw_score") or data.get("weight") or 0.0),
        policy=str(data.get("policy") or "rule_weight"),
        reason=str(data.get("reason") or ""),
        source_metric_refs=tuple(str(item) for item in _sequence(data.get("source_metric_refs"))),
    )


def _cap_and_redistribute(weights: Sequence[FactorWeight], cap: float) -> tuple[FactorWeight, ...]:
    remaining = {weight.factor_id: max(weight.weight, 0.0) for weight in weights}
    capped: dict[str, float] = {}
    while remaining:
        over = {key: value for key, value in remaining.items() if value > cap}
        if not over:
            break
        for key in over:
            capped[key] = cap
            remaining.pop(key)
        leftover = max(1.0 - sum(capped.values()), 0.0)
        total_remaining = sum(remaining.values())
        if total_remaining <= 0:
            break
        remaining = {key: value / total_remaining * leftover for key, value in remaining.items()}
    final = {**remaining, **capped}
    total = sum(final.values())
    if total > 0:
        final = {key: value / total for key, value in final.items()}
    return tuple(
        FactorWeight(
            factor_id=weight.factor_id,
            report_id=weight.report_id,
            weight=final.get(weight.factor_id, 0.0),
            raw_score=weight.raw_score,
            policy=weight.policy,
            reason=weight.reason,
            source_metric_refs=weight.source_metric_refs,
        )
        for weight in weights
    )


def _deferred_hits(value: Any) -> tuple[str, ...]:
    leaf_text = " ".join(_iter_leaf_text(_json_safe(value)))
    normalized = _normalise_text(leaf_text)
    hits = sorted({marker for marker in OPTIMIZER_DEFERRED_MARKERS if marker in normalized})
    return tuple(hits)


def _optimizer_enabled(config: Any) -> bool:
    data = _mapping(config)
    optimizer_policy = _mapping(data.get("optimizer_policy"))
    if optimizer_policy.get("enabled") is True:
        return True
    weighting_policy = _mapping(data.get("weighting_policy"))
    return str(weighting_policy.get("policy") or weighting_policy.get("type") or "") in {"optimizer", "ml_weighting"}


def _benchmark_deviation(config: Mapping[str, Any], constraints: Mapping[str, Any]) -> dict[str, Any]:
    benchmark = _first_non_blank(config.get("benchmark"), constraints.get("benchmark"))
    cap = _first_non_blank(constraints.get("benchmark_deviation_cap"), constraints.get("active_weight_cap"))
    return {
        "status": "pass" if benchmark else "blocked",
        "benchmark": _json_safe(benchmark or {}),
        "deviation_cap": cap,
        "active_weight_claim": "bounded" if benchmark and cap is not None else "not_claimed",
    }


def _cost_summary(config: Mapping[str, Any]) -> dict[str, Any]:
    cost = _mapping(config.get("cost_config"))
    return {
        "status": "pass" if cost else "missing",
        "cost_config": _json_safe(cost),
        "cost_adjusted_claim": "bounded" if cost else "not_claimed",
    }


def _capacity_summary(config: Mapping[str, Any], constraints: Mapping[str, Any]) -> dict[str, Any]:
    capacity = _first_non_blank(config.get("capacity"), constraints.get("capacity"))
    return {
        "status": "pass" if capacity else "missing",
        "capacity": _json_safe(capacity or {}),
        "capacity_claim": "bounded" if capacity else "not_claimed",
    }


def _lineage(reports: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "combiner_id": config.get("combiner_id"),
        "source_reports": [_report_ref(report) for report in reports],
        "freeze_version": _mapping(config.get("freeze_policy")).get("version"),
        "evidence_refs": sorted(
            {
                str(ref)
                for report in reports
                for ref in _sequence(report.get("evidence_refs"))
                if not _is_blank(ref)
            }
        ),
    }


def _weight_sources(weights: Sequence[FactorWeight]) -> dict[str, Any]:
    return {
        weight.factor_id: {
            "report_id": weight.report_id,
            "policy": weight.policy,
            "raw_score": weight.raw_score,
            "reason": weight.reason,
            "source_metric_refs": list(weight.source_metric_refs),
        }
        for weight in weights
    }


def _plan_limitations(status: str) -> tuple[str, ...]:
    base = (
        "not_qmt_ready",
        "not_simulation_ready",
        "not_live_ready",
        "not_broker_order",
        "requires_s07_admission_before_execution_route",
    )
    if status == MultiFactorPlanStatus.RESEARCH_LIMITED.value:
        return base + ("research_limited_constraints_or_inputs",)
    if status == MultiFactorPlanStatus.BLOCKED.value:
        return base + ("blocked_until_reasons_resolved",)
    return base


def _blocked_claims(reasons: Sequence[MultiFactorBlockedReason]) -> tuple[MultiFactorClaim, ...]:
    claims = [
        MultiFactorClaim(
            claim=claim,
            status="blocked",
            code="MF_COMBINER_CLAIM_NOT_AUTHORIZED",
            reason="MultiFactorPortfolioPlan 不构成生产、QMT、模拟盘、实盘或真实可交易证据。",
            limitation="真实运行或交易类能力必须由后续独立 CR / per-run authorization 解锁。",
        )
        for claim in DEFAULT_NOT_AUTHORIZED_CLAIMS
    ]
    for reason in reasons:
        claims.append(
            MultiFactorClaim(
                claim=reason.field or reason.code,
                status="blocked",
                code=reason.code,
                reason=reason.message,
                limitation=reason.remediation,
                evidence_ref=reason.evidence_ref,
            )
        )
    return tuple(_dedupe_claims(claims))


def _normalise_permission_counters(value: Any) -> dict[str, int]:
    if isinstance(value, PermissionCounters):
        raw = value.to_dict()
    else:
        raw = _mapping(value)
    counters = {name: 0 for name in FORBIDDEN_OPERATION_COUNTERS}
    for name in counters:
        raw_value = raw.get(name)
        try:
            counters[name] = int(raw_value or 0)
        except (TypeError, ValueError):
            counters[name] = 1
    return counters


def _merge_counters(left: Mapping[str, int], right: Mapping[str, int]) -> dict[str, int]:
    return {name: int(left.get(name, 0)) + int(right.get(name, 0)) for name in FORBIDDEN_OPERATION_COUNTERS}


def _reason(
    code: str,
    message: str,
    field: str = "",
    severity: str = "blocker",
    remediation: str = "",
    evidence_ref: str = "",
) -> MultiFactorBlockedReason:
    return MultiFactorBlockedReason(
        code=code,
        message=message,
        field=field,
        severity=severity,
        remediation=remediation,
        evidence_ref=evidence_ref,
    )


def _dedupe_reasons(reasons: Sequence[MultiFactorBlockedReason]) -> list[MultiFactorBlockedReason]:
    seen: set[tuple[str, str, str]] = set()
    output: list[MultiFactorBlockedReason] = []
    for reason in reasons:
        key = (reason.code, reason.field, reason.evidence_ref)
        if key not in seen:
            seen.add(key)
            output.append(reason)
    return output


def _dedupe_claims(claims: Sequence[MultiFactorClaim]) -> list[MultiFactorClaim]:
    seen: set[tuple[str, str, str]] = set()
    output: list[MultiFactorClaim] = []
    for claim in claims:
        key = (claim.claim, claim.status, claim.code)
        if key not in seen:
            seen.add(key)
            output.append(claim)
    return output


def _metric_number(metric: Any, keys: Sequence[str]) -> float | None:
    data = _mapping(metric)
    for key in keys:
        value = _number(data.get(key))
        if value is not None and not math.isnan(value):
            return value
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _first_non_blank(*values: Any) -> Any:
    for value in values:
        if not _is_blank(value):
            return value
    return None


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _neutralization_enabled(value: Any) -> bool:
    data = _mapping(value)
    if not data:
        return False
    method = str(data.get("method") or data.get("policy") or "").lower()
    return method not in {"", "disabled", "none", "off"}


def _normalise_text(value: Any) -> str:
    return str(value).lower().replace("-", "_").replace(" ", "_")


def _iter_leaf_text(value: Any) -> tuple[str, ...]:
    if isinstance(value, Mapping):
        return tuple(text for child in value.values() for text in _iter_leaf_text(child))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(text for child in value for text in _iter_leaf_text(child))
    if isinstance(value, (str, int, float, bool)):
        return (str(value),)
    return ()


def _walk_items(value: Any, prefix: str = "") -> tuple[tuple[str, Any], ...]:
    data = _json_safe(value)
    output: list[tuple[str, Any]] = []
    if isinstance(data, Mapping):
        for key, child in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            output.append((path, child))
            output.extend(_walk_items(child, path))
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        for index, child in enumerate(data):
            path = f"{prefix}[{index}]"
            output.append((path, child))
            output.extend(_walk_items(child, path))
    return tuple(output)


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


def _plan_id(config: Mapping[str, Any]) -> str:
    combiner_id = str(config.get("combiner_id") or "multifactor_combiner")
    freeze_version = str(_mapping(config.get("freeze_policy")).get("version") or "unfrozen")
    return f"{combiner_id}:{freeze_version}"


__all__ = [
    "MF_BROKER_ORDER_FORBIDDEN",
    "MF_COMBINER_BENCHMARK_MISSING",
    "MF_COMBINER_CAPACITY_MISSING",
    "MF_COMBINER_CLAIM_BOUNDARY_MISSING",
    "MF_COMBINER_COST_MISSING",
    "MF_COMBINER_EXPOSURE_MISSING",
    "MF_COMBINER_FORBIDDEN_OPERATION_NONZERO",
    "MF_COMBINER_NO_REPORTS",
    "MF_COMBINER_REPORT_BLOCKED",
    "MF_OPTIMIZER_DEFERRED",
    "BrokerOrderValidationResult",
    "CombinerValidationResult",
    "FactorWeight",
    "MultiFactorBlockedReason",
    "MultiFactorClaim",
    "MultiFactorCombiner",
    "MultiFactorPortfolioPlan",
    "MultiFactorPlanStatus",
    "apply_portfolio_constraints",
    "assert_no_broker_order",
    "build_multifactor_portfolio_plan",
    "compute_rule_weights",
    "detect_optimizer_deferred_request",
    "to_portfolio_plan_draft",
    "validate_combiner_inputs",
]
