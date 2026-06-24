"""CR019-S07 的 QMT gateway run gate 聚合离线合同。

本模块只消费 fixture / dry-run 的只读 gate result，不读取环境或凭据，
不启动服务、不打开网络连接、不调用 QMT / MiniQMT / XtQuant / broker。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from market_data.contracts import ADJUSTMENT_POLICY_RAW
from trading.kill_switch import read_kill_switch_result
from trading.pretrade_risk import read_pretrade_risk_result
from trading.qmt_auth import QmtAuthResult
from trading.qmt_endpoint_matrix import (
    QmtEndpointCategory,
    QmtEndpointSpec,
    QmtRealOperationKind,
    resolve_endpoint_spec,
)
from trading.qmt_gateway_contracts import (
    GatewayCommand,
    GatewayCommandDecision,
    MarketSubscription,
    QmtBlockedReason,
    QmtGatewayResult,
    build_allowed_result,
    build_blocked_result,
    collect_qmt_gateway_contract_counters,
)
from trading.runner_control_contracts import AuthorizationRecord, build_authorization_record, stable_id
from trading.stage_gate import read_admission_gate_result, read_stage_gate_result


QMT_GATEWAY_GATE_SCHEMA_VERSION = "cr019-s07-qmt-gateway-gates-v1"

BLOCKED_REASON_PRIORITY: tuple[str, ...] = (
    "auth",
    "endpoint_schema",
    "admission_stage",
    "authorization",
    "risk",
    "kill_switch",
    "raw_policy",
    "operation_not_authorized",
)

_RUN_GATE_INPUTS = frozenset(
    {"run_mode", "stage", "risk", "kill_switch", "authorization", "raw_policy"}
)
_ORDER_EXECUTION_KINDS = frozenset(
    {QmtRealOperationKind.ORDER_SUBMIT, QmtRealOperationKind.ORDER_CANCEL}
)
_RAW_EXECUTION_POLICIES = frozenset(
    {ADJUSTMENT_POLICY_RAW, "raw", "broker_raw", "broker_price"}
)
_VALID_AUTHORIZATION_STATUSES = frozenset(
    {"pass", "passed", "valid", "approved", "authorized"}
)
_AUTH_DIRECT_AUTHORIZATION_FIELDS = (
    "adapter_call_allowed",
    "trade_authorized",
    "simulation_authorized",
    "live_authorized",
    "account_authorized",
    "cancel_authorized",
)


@dataclass(frozen=True, slots=True)
class QmtGateContext:
    """Gateway run gate 聚合输入；所有字段都应来自只读合同对象。"""

    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str | None
    auth_result: QmtAuthResult | Mapping[str, object] | None = None
    run_mode: str = "dry_run"
    admission_result: Mapping[str, object] | object | None = None
    stage_gate_result: Mapping[str, object] | object | None = None
    risk_result: Mapping[str, object] | object | None = None
    kill_switch_result: Mapping[str, object] | object | None = None
    authorization_ref: str = ""
    authorization_status: str = ""
    authorization_detail: Mapping[str, object] = field(default_factory=dict)
    execution_price_policy: str = ADJUSTMENT_POLICY_RAW
    request_ref: str = ""


@dataclass(frozen=True, slots=True)
class QmtGateFailure:
    """单个 gate 的失败摘要；主 reason 由固定 priority 选择。"""

    priority: str
    reason: QmtBlockedReason | str
    blocked_by: str
    message: str
    required_evidence: tuple[str, ...] = ()
    detail_code: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "priority": self.priority,
            "reason": _enum_value(self.reason),
            "blocked_by": self.blocked_by,
            "message": self.message,
            "required_evidence": list(self.required_evidence),
            "detail_code": self.detail_code,
        }


@dataclass(frozen=True, slots=True)
class QmtGateDecision:
    """Gateway run gate 聚合输出；不代表真实 QMT 调用已执行。"""

    allowed: bool
    endpoint_id: str
    blocked_reason: QmtBlockedReason | str | None = None
    blocked_by: str = ""
    message: str = ""
    required_evidence: tuple[str, ...] = ()
    suppressed_reasons: tuple[QmtGateFailure, ...] = ()
    counters: Mapping[str, int] = field(
        default_factory=lambda: collect_qmt_gateway_gate_safety_counters()
    )
    auth_caller_identified: bool = False
    hmac_trade_authorization_claim_count: int = 0
    schema_version: str = QMT_GATEWAY_GATE_SCHEMA_VERSION

    @property
    def blocked(self) -> bool:
        return not self.allowed

    @property
    def reason_code(self) -> str:
        return "" if self.blocked_reason is None else _enum_value(self.blocked_reason)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "endpoint_id": self.endpoint_id,
            "blocked_reason": self.reason_code,
            "blocked_by": self.blocked_by,
            "message": self.message,
            "required_evidence": list(self.required_evidence),
            "suppressed_reasons": [
                failure.to_dict() for failure in self.suppressed_reasons
            ],
            "counters": dict(self.counters),
            "auth_caller_identified": self.auth_caller_identified,
            "hmac_trade_authorization_claim_count": (
                self.hmac_trade_authorization_claim_count
            ),
        }


def evaluate_qmt_gateway_gates(context: QmtGateContext) -> QmtGateDecision:
    """按固定 priority 汇总 S05/S06/S01/CR015/CR016 gate。"""

    counters = collect_qmt_gateway_gate_safety_counters()
    auth_view = _auth_result_view(context.auth_result)
    endpoint_id = _context_endpoint_id(context.endpoint_spec)
    auth_failure = _auth_failure(auth_view)
    if auth_failure is not None:
        return _blocked_decision(
            endpoint_id,
            auth_failure,
            (),
            counters,
            auth_caller_identified=bool(auth_view.get("caller_identified")),
            hmac_claim_count=_direct_auth_claim_count(auth_view),
        )

    spec = _resolve_context_endpoint(context.endpoint_spec)
    if spec is None:
        failure = QmtGateFailure(
            priority="endpoint_schema",
            reason=QmtBlockedReason.UNKNOWN_ENDPOINT,
            blocked_by="endpoint_matrix",
            message="endpoint is not present in the S06 QMT endpoint matrix",
            required_evidence=("qmt_endpoint_spec",),
            detail_code="unknown_endpoint",
        )
        return _blocked_decision(
            endpoint_id,
            failure,
            (),
            counters,
            auth_caller_identified=bool(auth_view.get("caller_identified")),
            hmac_claim_count=_direct_auth_claim_count(auth_view),
        )

    scope_failure = _auth_scope_failure(auth_view, spec.required_scope)
    if scope_failure is not None:
        return _blocked_decision(
            spec.endpoint_id,
            scope_failure,
            (),
            counters,
            auth_caller_identified=bool(auth_view.get("caller_identified")),
            hmac_claim_count=_direct_auth_claim_count(auth_view),
        )

    failures: list[QmtGateFailure] = []
    requires_run_gates = _requires_run_gates(spec)
    if requires_run_gates:
        failures.extend(
            _admission_stage_failures(
                context.admission_result,
                context.stage_gate_result,
            )
        )

        authorization = validate_per_run_authorization(
            spec,
            context.authorization_ref,
            authorization_status=context.authorization_status,
            authorization_detail=context.authorization_detail,
        )
        if not bool(authorization["passed"]):
            failures.append(
                QmtGateFailure(
                    priority="authorization",
                    reason=QmtBlockedReason.AUTHORIZATION_MISSING,
                    blocked_by="per_run_authorization",
                    message=str(authorization["message"]),
                    required_evidence=tuple(authorization["required_evidence"]),  # type: ignore[arg-type]
                    detail_code=str(authorization["blocked_reason"]),
                )
            )

    if _requires_risk_gate(spec):
        risk_view = read_pretrade_risk_result(context.risk_result)
        if not bool(risk_view["passed"]):
            failures.append(
                QmtGateFailure(
                    priority="risk",
                    reason=QmtBlockedReason.RISK_GATE_BLOCKED,
                    blocked_by="pretrade_risk",
                    message="pre-trade risk gate is missing or blocked",
                    required_evidence=_as_tuple(risk_view.get("required_evidence")),
                    detail_code=str(risk_view.get("blocked_reason") or "risk_blocked"),
                )
            )

    if _requires_kill_switch_gate(spec):
        kill_view = read_kill_switch_result(context.kill_switch_result)
        if not bool(kill_view["passed"]):
            failures.append(
                QmtGateFailure(
                    priority="kill_switch",
                    reason=QmtBlockedReason.KILL_SWITCH_ACTIVE,
                    blocked_by="kill_switch",
                    message="kill-switch or heartbeat gate is missing, active, or unknown",
                    required_evidence=_as_tuple(kill_view.get("required_evidence")),
                    detail_code=str(
                        kill_view.get("blocked_reason") or "kill_switch_active"
                    ),
                )
            )

    raw_policy = validate_raw_execution_policy(spec, context.execution_price_policy)
    if not bool(raw_policy["passed"]):
        failures.append(
            QmtGateFailure(
                priority="raw_policy",
                reason=QmtBlockedReason.RAW_POLICY_BLOCKED,
                blocked_by="raw_execution_policy",
                message=str(raw_policy["message"]),
                required_evidence=tuple(raw_policy["required_evidence"]),  # type: ignore[arg-type]
                detail_code=str(raw_policy["blocked_reason"]),
            )
        )

    hmac_claim_count = _direct_auth_claim_count(auth_view)
    if hmac_claim_count:
        failures.append(
            QmtGateFailure(
                priority="operation_not_authorized",
                reason=QmtBlockedReason.QMT_OPERATION_NOT_AUTHORIZED,
                blocked_by="auth_result",
                message="HMAC pass cannot authorize account/order/cancel/simulation/live",
                required_evidence=("per_run_authorization", "stage_gate_result"),
                detail_code="hmac_trade_authorization_claim",
            )
        )

    if _requires_operation_authorization_block(spec, requires_run_gates):
        failures.append(
            QmtGateFailure(
                priority="operation_not_authorized",
                reason=QmtBlockedReason.QMT_OPERATION_NOT_AUTHORIZED,
                blocked_by="gateway_runtime_authorization",
                message="visible endpoint still cannot perform real QMT operation offline",
                required_evidence=("explicit_runtime_authorization",),
                detail_code="offline_contract_only",
            )
        )

    if failures:
        primary, suppressed = _prioritize_failures(failures)
        return _blocked_decision(
            spec.endpoint_id,
            primary,
            suppressed,
            counters,
            auth_caller_identified=bool(auth_view.get("caller_identified")),
            hmac_claim_count=hmac_claim_count,
        )

    return QmtGateDecision(
        allowed=True,
        endpoint_id=spec.endpoint_id,
        message="gateway gates passed for fixture-only downstream boundary",
        counters=counters,
        auth_caller_identified=bool(auth_view.get("caller_identified")),
        hmac_trade_authorization_claim_count=hmac_claim_count,
    )


def to_qmt_gateway_result(
    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str | None,
    decision: QmtGateDecision,
) -> QmtGatewayResult:
    """把 S07 gate decision 转换为 S06 `QmtGatewayResult`。"""

    spec = _resolve_context_endpoint(endpoint_spec)
    endpoint_id = spec.endpoint_id if spec is not None else decision.endpoint_id
    if decision.allowed:
        return build_allowed_result(
            endpoint_id,
            {
                "gate_decision": decision.to_dict(),
                "operation_authorized": False,
                "fixture_only": True,
                "real_operation": False,
            },
            counters=decision.counters,
        )
    return build_blocked_result(
        endpoint_id,
        decision.blocked_reason or QmtBlockedReason.QMT_OPERATION_NOT_AUTHORIZED,
        decision.message,
        detail={
            "blocked_by": decision.blocked_by,
            "required_evidence": list(decision.required_evidence),
            "suppressed_reasons": [
                failure.to_dict() for failure in decision.suppressed_reasons
            ],
            "gate_schema_version": decision.schema_version,
            "hmac_trade_authorization_claim_count": (
                decision.hmac_trade_authorization_claim_count
            ),
        },
        counters=decision.counters,
    )


def collect_qmt_gateway_gate_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """返回 S07 禁止操作计数；默认全部为 0。"""

    normalized = collect_qmt_gateway_contract_counters()
    normalized.update(
        {
            "adapter_call": 0,
            "adapter_calls": 0,
            "cancel_order": 0,
            "hmac_trade_authorization_claim": 0,
        }
    )
    if counters is None:
        return normalized
    for key, value in counters.items():
        normalized[str(key)] = int(value)
    return normalized


def validate_per_run_authorization(
    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str,
    authorization_ref: str,
    *,
    authorization_status: str = "",
    authorization_detail: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """校验 per-run authorization 引用；不读取外部授权文件。"""

    spec = _resolve_context_endpoint(endpoint_spec)
    if spec is None or not _requires_authorization_gate(spec):
        return {
            "passed": True,
            "status": "not_required",
            "blocked_reason": "",
            "message": "authorization gate is not required for this endpoint",
            "required_evidence": (),
        }
    if not authorization_ref:
        return {
            "passed": False,
            "status": "missing",
            "blocked_reason": "authorization_missing",
            "message": "per-run authorization reference is required",
            "required_evidence": ("authorization_ref",),
        }

    detail = dict(authorization_detail or {})
    status = _enum_value(authorization_status or detail.get("status")).lower()
    authorized = bool(detail.get("authorized", False))
    if status in _VALID_AUTHORIZATION_STATUSES or authorized:
        return {
            "passed": True,
            "status": status or "authorized",
            "blocked_reason": "",
            "message": "per-run authorization reference is valid",
            "required_evidence": (),
        }
    return {
        "passed": False,
        "status": status or "unknown",
        "blocked_reason": "authorization_invalid",
        "message": "per-run authorization reference is present but not valid",
        "required_evidence": ("authorization_status=valid",),
    }


def validate_raw_execution_policy(
    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str,
    execution_price_policy: str,
) -> dict[str, object]:
    """校验真实执行相关 endpoint 只能使用 raw / broker price。"""

    spec = _resolve_context_endpoint(endpoint_spec)
    if spec is None or not _requires_raw_policy(spec):
        return {
            "passed": True,
            "status": "not_required",
            "blocked_reason": "",
            "message": "raw execution policy is not required",
            "required_evidence": (),
        }
    policy = _enum_value(execution_price_policy).strip().lower()
    if policy in _RAW_EXECUTION_POLICIES:
        return {
            "passed": True,
            "status": "pass",
            "blocked_reason": "",
            "message": "raw execution policy passed",
            "required_evidence": (),
        }
    return {
        "passed": False,
        "status": "blocked",
        "blocked_reason": "raw_policy_blocked",
        "message": "execution endpoint requires raw or broker price policy",
        "required_evidence": ("execution_price_policy=raw",),
    }


def _auth_failure(auth_view: Mapping[str, object]) -> QmtGateFailure | None:
    if not bool(auth_view.get("allowed")):
        raw_reason = str(auth_view.get("blocked_reason") or "")
        reason = (
            QmtBlockedReason.SCOPE_DENIED
            if "scope" in raw_reason
            else QmtBlockedReason.AUTH_BLOCKED
        )
        return QmtGateFailure(
            priority="auth",
            reason=reason,
            blocked_by="hmac_auth",
            message="gateway auth is missing or blocked",
            required_evidence=("qmt_auth_result",),
            detail_code=raw_reason or "auth_blocked",
        )
    return None


def _auth_scope_failure(
    auth_view: Mapping[str, object],
    required_scope: str,
) -> QmtGateFailure | None:
    scopes = set(_as_tuple(auth_view.get("scopes")))
    if scopes and required_scope not in scopes:
        return QmtGateFailure(
            priority="auth",
            reason=QmtBlockedReason.SCOPE_DENIED,
            blocked_by="hmac_scope",
            message="HMAC caller scope does not cover endpoint required scope",
            required_evidence=(f"scope:{required_scope}",),
            detail_code="scope_denied",
        )
    return None


def _admission_stage_failures(
    admission_result: Mapping[str, object] | object | None,
    stage_gate_result: Mapping[str, object] | object | None,
) -> tuple[QmtGateFailure, ...]:
    failures: list[QmtGateFailure] = []
    admission_view = read_admission_gate_result(admission_result)
    if not bool(admission_view["passed"]):
        failures.append(
            QmtGateFailure(
                priority="admission_stage",
                reason=QmtBlockedReason.STAGE_GATE_BLOCKED,
                blocked_by="admission_gate",
                message="stage6 admission gate is missing or blocked",
                required_evidence=_as_tuple(admission_view.get("required_evidence")),
                detail_code=str(
                    admission_view.get("blocked_reason") or "admission_blocked"
                ),
            )
        )

    stage_view = read_stage_gate_result(stage_gate_result)
    if not bool(stage_view["passed"]):
        failures.append(
            QmtGateFailure(
                priority="admission_stage",
                reason=QmtBlockedReason.STAGE_GATE_BLOCKED,
                blocked_by="stage_gate",
                message="CR016 stage gate is missing or blocked",
                required_evidence=_as_tuple(stage_view.get("required_evidence")),
                detail_code=str(stage_view.get("blocked_reason") or "stage_gate_blocked"),
            )
        )
    return tuple(failures)


def _blocked_decision(
    endpoint_id: str,
    primary: QmtGateFailure,
    suppressed: tuple[QmtGateFailure, ...],
    counters: Mapping[str, int],
    *,
    auth_caller_identified: bool,
    hmac_claim_count: int,
) -> QmtGateDecision:
    return QmtGateDecision(
        allowed=False,
        endpoint_id=endpoint_id,
        blocked_reason=primary.reason,
        blocked_by=primary.blocked_by,
        message=primary.message,
        required_evidence=primary.required_evidence,
        suppressed_reasons=suppressed,
        counters=counters,
        auth_caller_identified=auth_caller_identified,
        hmac_trade_authorization_claim_count=hmac_claim_count,
    )


def _prioritize_failures(
    failures: list[QmtGateFailure],
) -> tuple[QmtGateFailure, tuple[QmtGateFailure, ...]]:
    ordered = sorted(
        failures,
        key=lambda item: BLOCKED_REASON_PRIORITY.index(item.priority),
    )
    return ordered[0], tuple(ordered[1:])


def _auth_result_view(
    auth_result: QmtAuthResult | Mapping[str, object] | None,
) -> dict[str, object]:
    if auth_result is None:
        return {
            "allowed": False,
            "blocked_reason": "auth_context_missing",
            "scopes": (),
            "caller_identified": False,
        }
    if isinstance(auth_result, Mapping):
        return {
            "allowed": bool(auth_result.get("allowed", False)),
            "blocked_reason": _enum_value(auth_result.get("blocked_reason")),
            "scopes": _as_tuple(auth_result.get("scopes")),
            "caller_identified": bool(auth_result.get("caller_identified", False)),
            **{
                field_name: bool(auth_result.get(field_name, False))
                for field_name in _AUTH_DIRECT_AUTHORIZATION_FIELDS
            },
        }
    return {
        "allowed": auth_result.allowed,
        "blocked_reason": _enum_value(auth_result.blocked_reason),
        "scopes": tuple(auth_result.scopes),
        "caller_identified": auth_result.caller_identified,
        **{
            field_name: bool(getattr(auth_result, field_name))
            for field_name in _AUTH_DIRECT_AUTHORIZATION_FIELDS
        },
    }


def _direct_auth_claim_count(auth_view: Mapping[str, object]) -> int:
    return sum(1 for field_name in _AUTH_DIRECT_AUTHORIZATION_FIELDS if auth_view.get(field_name))


def _resolve_context_endpoint(
    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str | None,
) -> QmtEndpointSpec | None:
    if isinstance(endpoint_spec, QmtEndpointSpec):
        return endpoint_spec
    if endpoint_spec is None:
        return None
    return resolve_endpoint_spec(endpoint_spec)


def _context_endpoint_id(
    endpoint_spec: QmtEndpointSpec | QmtEndpointCategory | str | None,
) -> str:
    spec = _resolve_context_endpoint(endpoint_spec)
    if spec is not None:
        return spec.endpoint_id
    return _enum_value(endpoint_spec or "unknown")


def _requires_run_gates(spec: QmtEndpointSpec) -> bool:
    return spec.later_gated or bool(set(spec.gate_inputs) & _RUN_GATE_INPUTS)


def _requires_authorization_gate(spec: QmtEndpointSpec) -> bool:
    return spec.later_gated or "authorization" in spec.gate_inputs


def _requires_risk_gate(spec: QmtEndpointSpec) -> bool:
    return spec.real_operation_kind in _ORDER_EXECUTION_KINDS


def _requires_kill_switch_gate(spec: QmtEndpointSpec) -> bool:
    return _requires_run_gates(spec)


def _requires_raw_policy(spec: QmtEndpointSpec) -> bool:
    return "raw_policy" in spec.gate_inputs or spec.real_operation_kind in _ORDER_EXECUTION_KINDS


def _requires_operation_authorization_block(
    spec: QmtEndpointSpec,
    requires_run_gates: bool,
) -> bool:
    return (
        spec.real_operation_kind is not QmtRealOperationKind.NONE
        and not requires_run_gates
    )


def _as_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        text = _enum_value(value)
        return (text,) if text else ()
    if isinstance(value, Mapping):
        return tuple(str(key) for key in value.keys())
    try:
        return tuple(_enum_value(item) for item in value)  # type: ignore[union-attr]
    except TypeError:
        text = _enum_value(value)
        return (text,) if text else ()


def _enum_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def gate_market_subscription(
    *,
    symbols: tuple[str, ...],
    period: str,
    auth: AuthorizationRecord | Mapping[str, object] | None = None,
) -> MarketSubscription:
    """CR138 market subscription gate；未授权时不触发 adapter。"""

    current = build_authorization_record(auth, scope="market_readonly")
    subscription_id = stable_id("subscription", period, ",".join(symbols))
    if not current.authorized or current.scope != "market_readonly":
        return MarketSubscription(
            subscription_id=subscription_id,
            symbols=symbols,
            period=period,
            state="blocked",
            blocked_reason="authorization_missing",
            adapter_calls=0,
        )
    return MarketSubscription(
        subscription_id=subscription_id,
        symbols=symbols,
        period=period,
        state="registered_fixture_only",
        adapter_calls=0,
    )


def hard_reject_gateway_command(
    command: GatewayCommand,
    *,
    auth: AuthorizationRecord | Mapping[str, object] | None = None,
) -> GatewayCommandDecision:
    """CR138 submit/cancel gate；未授权只返回本地 hard_rejected。"""

    current = build_authorization_record(auth, scope=command.scope)
    if command.command_type in {"submit", "cancel", "buy", "sell"}:
        if not current.authorized or current.scope != command.scope:
            return GatewayCommandDecision(
                command_id=command.command_id,
                status="hard_rejected",
                blocked_reason="authorization_missing",
                local_reject=True,
                broker_reject=False,
                adapter_calls=0,
            )
    return GatewayCommandDecision(
        command_id=command.command_id,
        status="accepted_for_fixture_only",
        local_reject=True,
        broker_reject=False,
        adapter_calls=0,
    )
