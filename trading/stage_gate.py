"""CR016-S01 的 simulation 阶段准入 gate 离线合同。

本模块只做内存结构校验，不读取凭据、不启动 QMT / MiniQMT、不调用
XtQuant / broker API，也不执行任何 simulation run 或真实交易操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class Stage(str, Enum):
    """CR016 固定阶段顺序。"""

    SHADOW = "shadow"
    SIMULATION = "simulation"
    LIVE_READONLY = "live_readonly"
    SMALL_LIVE = "small_live"
    SCALE_UP = "scale_up"


class GateStatus(str, Enum):
    """stage gate 输出状态。"""

    PASS = "pass"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"


class StageGateBlockedReason(str, Enum):
    """稳定 blocked reason 枚举，供 runbook、adapter 和 CP7 断言。"""

    STAGE_SKIP_BLOCKED = "stage_skip_blocked"
    UNSUPPORTED_STAGE = "unsupported_stage"
    CR015_NOT_VERIFIED = "cr015_not_verified"
    RUNBOOK_REQUIRED_MISSING = "runbook_required_missing"
    CR017_CONSUMER_BOUNDARY_REQUIRED_MISSING = (
        "cr017_consumer_boundary_required_missing"
    )
    RECONCILIATION_POLICY_MISSING = "reconciliation_policy_missing"
    KILL_SWITCH_READINESS_MISSING = "kill_switch_readiness_missing"
    AUTHORIZATION_REQUIRED_MISSING = "authorization_required_missing"
    CR017_SCALE_UP_NOT_VERIFIED = "cr017_scale_up_not_verified"
    REAL_OPERATION_NOT_AUTHORIZED = "real_operation_not_authorized"


STAGE_ORDER: tuple[Stage, ...] = (
    Stage.SHADOW,
    Stage.SIMULATION,
    Stage.LIVE_READONLY,
    Stage.SMALL_LIVE,
    Stage.SCALE_UP,
)

REQUIRED_AUTHORIZATION_FIELDS: tuple[str, ...] = (
    "authorization_id",
    "mode",
    "strategy_id",
    "run_id",
    "target_stage",
    "target_trade_date",
    "capital_limit",
    "order_scope",
    "approver",
    "approved_at",
    "expires_at",
    "rollback_plan_ref",
)

ZERO_OPERATION_COUNTERS: Mapping[str, int] = {
    "qmt_api_call": 0,
    "real_order_call": 0,
    "real_cancel_call": 0,
    "account_query_call": 0,
    "account_write_call": 0,
    "credential_read": 0,
    "real_broker_lake_write": 0,
    "real_lake_write": 0,
    "provider_fetch": 0,
    "publish": 0,
    "dependency_change": 0,
    "simulation_run": 0,
    "live_activation": 0,
    "adapter_call_on_block": 0,
    "scale_up_allowed_without_cr017": 0,
    # 兼容 CR015 既有 adapter counter 命名。
    "real_order": 0,
    "real_cancel": 0,
    "account_query": 0,
    "account_write": 0,
    "adapter_calls": 0,
    "simulation_activation": 0,
}


@dataclass(frozen=True, slots=True)
class AuthorizationSummary:
    """per-run 授权的脱敏摘要；不得包含账号、密码、session 或 token。"""

    authorization_id: str = ""
    mode: str = ""
    strategy_id: str = ""
    run_id: str = ""
    target_stage: Stage | str = ""
    target_trade_date: str = ""
    capital_limit: int | float | str | None = None
    order_scope: tuple[str, ...] | str = ()
    approver: str = ""
    approved_at: str = ""
    expires_at: str = ""
    rollback_plan_ref: str = ""


@dataclass(frozen=True, slots=True)
class StageEvidence:
    """stage gate 只消费脱敏证据引用，不读取真实账户或 broker 文件。"""

    cr015_verified: bool = False
    runbook_ref: str = ""
    cr017_consumer_boundary_ref: str = ""
    reconciliation_policy_ref: str = ""
    kill_switch_readiness_ref: str = ""
    cr017_verified: bool = False


@dataclass(frozen=True, slots=True)
class StageGateRequest:
    """一次 stage gate 评估请求。"""

    current_stage: Stage | str
    target_stage: Stage | str
    authorization_summary: AuthorizationSummary | Mapping[str, object] | None = None
    request_ref: str = ""


@dataclass(frozen=True, slots=True)
class StageGateResult:
    """stage gate 结构化输出，供 adapter 前置检查和 CP7 消费。"""

    gate_status: GateStatus
    current_stage: Stage | None
    target_stage: Stage | None
    blocked_reason: StageGateBlockedReason | None = None
    missing_fields: tuple[str, ...] = ()
    next_required_action: str = ""
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: stage_gate_safety_counters()
    )
    evidence_refs: Mapping[str, str] = field(default_factory=dict)
    authorization_id: str = ""

    @property
    def passed(self) -> bool:
        return self.gate_status is GateStatus.PASS


@dataclass(frozen=True, slots=True)
class SimulationOrderEnableResult:
    """`simulation_order_enable` 的离线消费结果。"""

    enabled: bool
    gate_status: GateStatus
    adapter_mode: str
    blocked_reason: StageGateBlockedReason | None = None
    detail_code: str = ""
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: stage_gate_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class AdmissionStageGateEvidence:
    """CR019 admission 只读 evidence ref，不改变 CR016 stage gate 语义。"""

    admission_package_ref: str
    admission_status: str
    blocked_reasons: tuple[str, ...] = ()


def stage_gate_safety_counters(**overrides: int) -> dict[str, int]:
    """返回 CR016-S01 要求保持为 0 的安全计数。"""

    counters = dict(ZERO_OPERATION_COUNTERS)
    counters.update({key: int(value) for key, value in overrides.items()})
    return counters


def evaluate_stage_gate(
    request: StageGateRequest | Mapping[str, object],
    evidence: StageEvidence | Mapping[str, object] | None = None,
) -> StageGateResult:
    """评估固定阶段推进请求；任何缺失前置项都返回 blocked。"""

    current_stage = _coerce_stage(_read_value(request, "current_stage"))
    target_stage = _coerce_stage(_read_value(request, "target_stage"))
    if current_stage is None or target_stage is None:
        missing_fields = tuple(
            field_name
            for field_name, value in (
                ("current_stage", current_stage),
                ("target_stage", target_stage),
            )
            if value is None
        )
        return _blocked_result(
            current_stage,
            target_stage,
            StageGateBlockedReason.UNSUPPORTED_STAGE,
            missing_fields=missing_fields,
            next_required_action="use_supported_stage_enum",
        )

    if _stage_distance(current_stage, target_stage) != 1:
        return _blocked_result(
            current_stage,
            target_stage,
            StageGateBlockedReason.STAGE_SKIP_BLOCKED,
            next_required_action="request_exact_next_stage",
        )

    current_evidence = _coerce_evidence(
        evidence if evidence is not None else _read_value(request, "evidence")
    )
    if not current_evidence.cr015_verified:
        return _blocked_result(
            current_stage,
            target_stage,
            StageGateBlockedReason.CR015_NOT_VERIFIED,
            missing_fields=("cr015_verified",),
            next_required_action="wait_for_cr015_foundation_cp7_pass",
            evidence_refs=_evidence_refs(current_evidence),
        )

    evidence_missing, evidence_reason = _missing_evidence(current_evidence)
    if evidence_missing:
        return _blocked_result(
            current_stage,
            target_stage,
            evidence_reason,
            missing_fields=evidence_missing,
            next_required_action="complete_stage_gate_evidence_refs",
            evidence_refs=_evidence_refs(current_evidence),
        )

    authorization_summary = _read_value(request, "authorization_summary")
    missing_auth_fields = validate_authorization_summary(
        authorization_summary,
        target_stage,
    )
    if missing_auth_fields:
        return _blocked_result(
            current_stage,
            target_stage,
            StageGateBlockedReason.AUTHORIZATION_REQUIRED_MISSING,
            missing_fields=missing_auth_fields,
            next_required_action="provide_per_run_authorization_summary",
            evidence_refs=_evidence_refs(current_evidence),
        )

    if target_stage is Stage.SCALE_UP and not current_evidence.cr017_verified:
        return _blocked_result(
            current_stage,
            target_stage,
            StageGateBlockedReason.CR017_SCALE_UP_NOT_VERIFIED,
            missing_fields=("cr017_verified",),
            next_required_action="wait_for_cr017_verified_before_scale_up",
            evidence_refs=_evidence_refs(current_evidence),
        )

    auth = _coerce_authorization_summary(authorization_summary)
    return StageGateResult(
        gate_status=GateStatus.PASS,
        current_stage=current_stage,
        target_stage=target_stage,
        next_required_action="consume_gate_result_only_no_activation_side_effect",
        safety_counters=stage_gate_safety_counters(),
        evidence_refs=_evidence_refs(current_evidence),
        authorization_id=auth.authorization_id if auth is not None else "",
    )


def simulation_order_enable(
    gate_result: StageGateResult | Mapping[str, object],
    adapter_mode: str | Enum,
) -> SimulationOrderEnableResult:
    """只消费 gate result 判断是否通过 simulation order enable 前置门。"""

    gate_status = _coerce_gate_status(_read_value(gate_result, "gate_status"))
    blocked_reason = _coerce_blocked_reason(
        _read_value(gate_result, "blocked_reason")
    )
    mode = _enum_value(adapter_mode)

    if gate_status is not GateStatus.PASS:
        return SimulationOrderEnableResult(
            enabled=False,
            gate_status=gate_status,
            adapter_mode=mode,
            blocked_reason=blocked_reason
            or StageGateBlockedReason.REAL_OPERATION_NOT_AUTHORIZED,
            detail_code=_enum_value(blocked_reason) or gate_status.value,
            safety_counters=stage_gate_safety_counters(),
        )

    if mode != Stage.SIMULATION.value:
        return SimulationOrderEnableResult(
            enabled=False,
            gate_status=gate_status,
            adapter_mode=mode,
            blocked_reason=StageGateBlockedReason.REAL_OPERATION_NOT_AUTHORIZED,
            detail_code=mode,
            safety_counters=stage_gate_safety_counters(),
        )

    return SimulationOrderEnableResult(
        enabled=True,
        gate_status=gate_status,
        adapter_mode=mode,
        safety_counters=stage_gate_safety_counters(),
    )


def validate_authorization_summary(
    summary: AuthorizationSummary | Mapping[str, object] | None,
    target_stage: Stage | str,
) -> tuple[str, ...]:
    """返回缺失的 per-run 授权字段；空 tuple 表示字段齐备。"""

    authorization = _coerce_authorization_summary(summary)
    if authorization is None:
        return REQUIRED_AUTHORIZATION_FIELDS

    values = {
        field_name: _read_value(authorization, field_name)
        for field_name in REQUIRED_AUTHORIZATION_FIELDS
    }
    missing_fields = [
        field_name
        for field_name, value in values.items()
        if not _field_present(value)
    ]

    target = _coerce_stage(target_stage)
    authorized_target = _coerce_stage(authorization.target_stage)
    if target is not None and authorized_target is not None and target != authorized_target:
        missing_fields.append("target_stage")

    return tuple(dict.fromkeys(missing_fields))


def attach_admission_ref_to_stage_gate(
    stage_gate_context: StageGateResult | Mapping[str, object],
    admission_package_ref: str,
    admission_status: str | Enum,
    blocked_reasons: Iterable[str | Enum] | None = None,
) -> dict[str, object]:
    """追加 CR019 admission evidence ref，返回只读 view，不修改原 gate 对象。"""

    view = _stage_gate_context_view(stage_gate_context)
    evidence_refs = dict(view.get("evidence_refs") or {})
    evidence_refs["stage6_admission_package_ref"] = admission_package_ref
    view["evidence_refs"] = evidence_refs
    view["admission_evidence_ref"] = admission_package_ref
    view["stage6_admission"] = {
        "admission_package_ref": admission_package_ref,
        "admission_status": _enum_value(admission_status),
        "blocked_reasons": tuple(
            _enum_value(reason) for reason in (blocked_reasons or ())
        ),
    }
    return view


def summarize_admission_blocked_reasons(
    admission_package: Mapping[str, object] | object,
) -> tuple[str, ...]:
    """从 admission package / dict 中提取稳定 blocked reason 汇总。"""

    blocked_claims = _read_value(admission_package, "blocked_claims", ()) or ()
    reasons: list[str] = []
    for claim in blocked_claims:
        reason = _read_value(claim, "reason_code", "")
        if reason:
            reasons.append(_enum_value(reason))
    return tuple(dict.fromkeys(reasons))


def read_admission_gate_result(
    admission_context: Mapping[str, object] | object | None,
) -> dict[str, object]:
    """把 CR019 admission package 归一化为只读 gate view。"""

    if admission_context is None:
        return {
            "gate_name": "admission_gate",
            "passed": False,
            "status": "missing",
            "blocked_reason": "admission_context_missing",
            "required_evidence": ("admission_package_ref",),
            "evidence_refs": {},
            "safety_counters": stage_gate_safety_counters(),
        }

    nested = _read_value(admission_context, "stage6_admission", None)
    status = _enum_value(
        _read_value(
            nested,
            "admission_status",
            _read_value(admission_context, "admission_status", ""),
        )
    )
    blocked_reasons = tuple(
        _enum_value(reason)
        for reason in (
            _read_value(nested, "blocked_reasons", ())
            or summarize_admission_blocked_reasons(admission_context)
        )
        if _enum_value(reason)
    )
    missing_evidence = tuple(
        _enum_value(item)
        for item in (_read_value(admission_context, "missing_evidence", ()) or ())
        if _enum_value(item)
    )
    counters = _read_value(
        admission_context,
        "permission_counters",
        _read_value(admission_context, "safety_counters", stage_gate_safety_counters()),
    )
    nonzero_counters = tuple(
        key for key, value in dict(counters).items() if int(value) != 0
    )
    passed = status == "pass" and not blocked_reasons and not nonzero_counters
    blocked_reason = ""
    if nonzero_counters:
        blocked_reason = "real_operation_forbidden"
    elif blocked_reasons:
        blocked_reason = blocked_reasons[0]
    elif not passed:
        blocked_reason = status or "admission_blocked"
    return {
        "gate_name": "admission_gate",
        "passed": passed,
        "status": status or "unknown",
        "blocked_reason": blocked_reason,
        "blocked_reasons": blocked_reasons,
        "required_evidence": missing_evidence,
        "evidence_refs": {
            "admission_package_ref": _enum_value(
                _read_value(
                    nested,
                    "admission_package_ref",
                    _read_value(admission_context, "admission_package_ref", ""),
                )
            ),
            "stage_gate_ref": _enum_value(
                _read_value(admission_context, "stage_gate_ref", "")
            ),
        },
        "safety_counters": dict(counters),
    }


def read_stage_gate_result(
    stage_context: StageGateResult | Mapping[str, object] | None,
) -> dict[str, object]:
    """把 CR016 stage gate result 归一化为只读 gate view。"""

    if stage_context is None:
        return {
            "gate_name": "stage_gate",
            "passed": False,
            "status": "missing",
            "blocked_reason": StageGateBlockedReason.REAL_OPERATION_NOT_AUTHORIZED.value,
            "required_evidence": ("stage_gate_result",),
            "evidence_refs": {},
            "safety_counters": stage_gate_safety_counters(),
        }

    view = _stage_gate_context_view(stage_context)
    status = _enum_value(view.get("gate_status") or view.get("status"))
    blocked_reason = _enum_value(view.get("blocked_reason"))
    missing_fields = tuple(
        _enum_value(item) for item in (view.get("missing_fields") or ()) if _enum_value(item)
    )
    passed = status == GateStatus.PASS.value or bool(view.get("passed", False))
    counters = dict(view.get("safety_counters") or stage_gate_safety_counters())
    nonzero_counters = tuple(
        key for key, value in counters.items() if int(value) != 0
    )
    if nonzero_counters:
        passed = False
        blocked_reason = "real_operation_forbidden"
    return {
        "gate_name": "stage_gate",
        "passed": passed and not blocked_reason,
        "status": status or "unknown",
        "blocked_reason": blocked_reason,
        "required_evidence": missing_fields,
        "evidence_refs": dict(view.get("evidence_refs") or {}),
        "authorization_id": _enum_value(view.get("authorization_id")),
        "safety_counters": counters,
    }


def _blocked_result(
    current_stage: Stage | None,
    target_stage: Stage | None,
    blocked_reason: StageGateBlockedReason,
    *,
    missing_fields: tuple[str, ...] = (),
    next_required_action: str = "",
    evidence_refs: Mapping[str, str] | None = None,
) -> StageGateResult:
    return StageGateResult(
        gate_status=GateStatus.BLOCKED,
        current_stage=current_stage,
        target_stage=target_stage,
        blocked_reason=blocked_reason,
        missing_fields=missing_fields,
        next_required_action=next_required_action,
        safety_counters=stage_gate_safety_counters(),
        evidence_refs=evidence_refs or {},
    )


def _missing_evidence(
    evidence: StageEvidence,
) -> tuple[tuple[str, ...], StageGateBlockedReason]:
    checks: tuple[tuple[str, StageGateBlockedReason, object], ...] = (
        (
            "runbook_ref",
            StageGateBlockedReason.RUNBOOK_REQUIRED_MISSING,
            evidence.runbook_ref,
        ),
        (
            "cr017_consumer_boundary_ref",
            StageGateBlockedReason.CR017_CONSUMER_BOUNDARY_REQUIRED_MISSING,
            evidence.cr017_consumer_boundary_ref,
        ),
        (
            "reconciliation_policy_ref",
            StageGateBlockedReason.RECONCILIATION_POLICY_MISSING,
            evidence.reconciliation_policy_ref,
        ),
        (
            "kill_switch_readiness_ref",
            StageGateBlockedReason.KILL_SWITCH_READINESS_MISSING,
            evidence.kill_switch_readiness_ref,
        ),
    )
    missing = tuple(field_name for field_name, _, value in checks if not value)
    reason = next(
        (
            reason
            for field_name, reason, value in checks
            if field_name in missing and not value
        ),
        StageGateBlockedReason.RUNBOOK_REQUIRED_MISSING,
    )
    return missing, reason


def _evidence_refs(evidence: StageEvidence) -> dict[str, str]:
    return {
        "runbook_ref": evidence.runbook_ref,
        "cr017_consumer_boundary_ref": evidence.cr017_consumer_boundary_ref,
        "reconciliation_policy_ref": evidence.reconciliation_policy_ref,
        "kill_switch_readiness_ref": evidence.kill_switch_readiness_ref,
    }


def _stage_distance(current_stage: Stage, target_stage: Stage) -> int:
    return STAGE_ORDER.index(target_stage) - STAGE_ORDER.index(current_stage)


def _coerce_stage(value: Stage | str | object) -> Stage | None:
    if isinstance(value, Stage):
        return value
    if isinstance(value, Enum):
        value = value.value
    try:
        return Stage(str(value))
    except ValueError:
        return None


def _coerce_gate_status(value: GateStatus | str | object) -> GateStatus:
    if isinstance(value, GateStatus):
        return value
    if isinstance(value, Enum):
        value = value.value
    try:
        return GateStatus(str(value))
    except ValueError:
        return GateStatus.BLOCKED


def _coerce_blocked_reason(
    value: StageGateBlockedReason | str | object,
) -> StageGateBlockedReason | None:
    if value is None:
        return None
    if isinstance(value, StageGateBlockedReason):
        return value
    if isinstance(value, Enum):
        value = value.value
    try:
        return StageGateBlockedReason(str(value))
    except ValueError:
        return StageGateBlockedReason.REAL_OPERATION_NOT_AUTHORIZED


def _coerce_evidence(
    value: StageEvidence | Mapping[str, object] | object,
) -> StageEvidence:
    if isinstance(value, StageEvidence):
        return value
    if isinstance(value, Mapping):
        return StageEvidence(
            cr015_verified=bool(value.get("cr015_verified", False)),
            runbook_ref=str(value.get("runbook_ref", "")),
            cr017_consumer_boundary_ref=str(
                value.get("cr017_consumer_boundary_ref", "")
            ),
            reconciliation_policy_ref=str(
                value.get("reconciliation_policy_ref", "")
            ),
            kill_switch_readiness_ref=str(
                value.get("kill_switch_readiness_ref", "")
            ),
            cr017_verified=bool(value.get("cr017_verified", False)),
        )
    return StageEvidence()


def _coerce_authorization_summary(
    summary: AuthorizationSummary | Mapping[str, object] | None,
) -> AuthorizationSummary | None:
    if summary is None:
        return None
    if isinstance(summary, AuthorizationSummary):
        return summary
    if isinstance(summary, Mapping):
        values = {
            field_name: summary.get(field_name)
            for field_name in REQUIRED_AUTHORIZATION_FIELDS
        }
        return AuthorizationSummary(
            authorization_id=str(values["authorization_id"] or ""),
            mode=str(values["mode"] or ""),
            strategy_id=str(values["strategy_id"] or ""),
            run_id=str(values["run_id"] or ""),
            target_stage=values["target_stage"] or "",
            target_trade_date=str(values["target_trade_date"] or ""),
            capital_limit=values["capital_limit"],
            order_scope=values["order_scope"] or (),
            approver=str(values["approver"] or ""),
            approved_at=str(values["approved_at"] or ""),
            expires_at=str(values["expires_at"] or ""),
            rollback_plan_ref=str(values["rollback_plan_ref"] or ""),
        )
    return None


def _field_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (tuple, list, set, frozenset, dict)):
        return bool(value)
    return True


def _read_value(source: object, key: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _stage_gate_context_view(
    stage_gate_context: StageGateResult | Mapping[str, object],
) -> dict[str, object]:
    if isinstance(stage_gate_context, Mapping):
        return dict(stage_gate_context)
    return {
        "gate_status": stage_gate_context.gate_status,
        "current_stage": stage_gate_context.current_stage,
        "target_stage": stage_gate_context.target_stage,
        "blocked_reason": stage_gate_context.blocked_reason,
        "missing_fields": stage_gate_context.missing_fields,
        "next_required_action": stage_gate_context.next_required_action,
        "safety_counters": stage_gate_context.safety_counters,
        "evidence_refs": dict(stage_gate_context.evidence_refs),
        "authorization_id": stage_gate_context.authorization_id,
    }


def _enum_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
