"""模型盘到模拟盘的受控激活入口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
import hashlib
from typing import Callable, Mapping, Protocol, Sequence

from market_data.contracts import ADJUSTMENT_POLICY_RAW
from trading.oms import OrderIntent, create_order_intent
from trading.pretrade_risk import (
    PretradeRiskBatchResult,
    RiskInputSnapshot,
    RiskProfile,
    evaluate_many,
)
from trading.qmt_gateway_contracts import (
    QMT_SIMULATION_CANCEL_ENDPOINT_ID,
    QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
    QmtGatewayResult,
    QmtSimulationCancelRequest,
    QmtSimulationOrderRequest,
    build_blocked_result,
    build_simulation_cancel_request,
    build_simulation_order_request,
)
from trading.stage_gate import (
    StageEvidence,
    StageGateRequest,
    StageGateResult,
    evaluate_stage_gate,
)
from trading.strategy_runner.simulation_order_plan import SimulationOrderPlanResult


SIMULATION_ACTIVATION_SCHEMA_VERSION = "simulation-activation-v1"
SIMULATION_EXECUTION_ENGINE_SCHEMA_VERSION = "simulation-execution-engine-v1"


class SimulationGateway(Protocol):
    """已授权 simulation gateway 的最小提交接口。"""

    def submit_order(self, request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        ...

    def cancel_order(self, request: QmtSimulationCancelRequest) -> QmtGatewayResult:
        ...


@dataclass(frozen=True, slots=True)
class SimulationActivationRequest:
    """一次从目标组合进入模拟账户的激活请求。"""

    strategy_id: str
    run_id: str
    target_trade_date: str
    target_rows: tuple[Mapping[str, object], ...]
    capital_base: Decimal | int | float | str
    risk_snapshot: RiskInputSnapshot
    risk_profile: RiskProfile
    stage_request: StageGateRequest
    stage_evidence: StageEvidence
    authorization_ref: str
    lot_size: int = 100
    schema_version: str = SIMULATION_ACTIVATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SimulationOrderActivation:
    """单个目标持仓转委托后的脱敏状态。"""

    order_intent_id: str
    symbol_ref: str
    target_qty: int
    risk_status: str
    gateway_status: str
    blocked_reason: str = ""
    broker_order_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "order_intent_id": self.order_intent_id,
            "symbol_ref": self.symbol_ref,
            "target_qty": self.target_qty,
            "risk_status": self.risk_status,
            "gateway_status": self.gateway_status,
            "blocked_reason": self.blocked_reason,
            "broker_order_ref": self.broker_order_ref,
        }


@dataclass(frozen=True, slots=True)
class SimulationActivationResult:
    """模型盘 / 模拟盘入口激活结果。"""

    status: str
    run_id: str
    stage_gate_status: str
    submitted_count: int = 0
    blocked_reason: str = ""
    orders: tuple[SimulationOrderActivation, ...] = ()
    risk_result: PretradeRiskBatchResult | None = None
    stage_gate_result: StageGateResult | None = None
    schema_version: str = SIMULATION_ACTIVATION_SCHEMA_VERSION
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == "submitted"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "run_id": self.run_id,
            "stage_gate_status": self.stage_gate_status,
            "submitted_count": self.submitted_count,
            "blocked_reason": self.blocked_reason,
            "orders": [order.to_dict() for order in self.orders],
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class SimulationOpenOrderRef:
    """P3 执行引擎可撤订单输入；输出时只暴露脱敏 ref。"""

    order_intent_id: str
    broker_order_ref: str
    symbol: str = ""
    status: str = "accepted"


@dataclass(frozen=True, slots=True)
class SimulationExecutionEngineRequest:
    """P3 模拟执行引擎请求；只允许 simulation runtime 身份。"""

    strategy_id: str
    run_id: str
    target_trade_date: str
    order_plan: SimulationOrderPlanResult
    stage_request: StageGateRequest
    stage_evidence: StageEvidence
    authorization_ref: str
    expected_runtime_mode: str
    expected_runtime_profile: str
    cancel_open_orders: tuple[SimulationOpenOrderRef | Mapping[str, object], ...] = ()
    submit_enabled: bool = True
    cancel_enabled: bool = True
    throttle_batch_size: int = 10
    schema_version: str = SIMULATION_EXECUTION_ENGINE_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SimulationExecutionAction:
    """单个 submit/cancel 的脱敏执行状态。"""

    operation: str
    order_intent_id: str
    status: str
    instrument_ref: str = ""
    broker_order_ref: str = ""
    cancel_ref: str = ""
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "order_intent_id": self.order_intent_id,
            "status": self.status,
            "instrument_ref": self.instrument_ref,
            "broker_order_ref": self.broker_order_ref,
            "cancel_ref": self.cancel_ref,
            "blocked_reason": self.blocked_reason,
        }


@dataclass(frozen=True, slots=True)
class SimulationExecutionEngineResult:
    """P3 模拟执行引擎结果；异常时停止并要求人工接管。"""

    status: str
    run_id: str
    stage_gate_status: str
    actions: tuple[SimulationExecutionAction, ...] = ()
    blocked_reason: str = ""
    submitted_count: int = 0
    cancelled_count: int = 0
    rejected_count: int = 0
    unknown_count: int = 0
    manual_takeover_required: bool = False
    schema_version: str = SIMULATION_EXECUTION_ENGINE_SCHEMA_VERSION
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status in {"executed", "no_op"}

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "run_id": self.run_id,
            "stage_gate_status": self.stage_gate_status,
            "blocked_reason": self.blocked_reason,
            "submitted_count": self.submitted_count,
            "cancelled_count": self.cancelled_count,
            "rejected_count": self.rejected_count,
            "unknown_count": self.unknown_count,
            "manual_takeover_required": self.manual_takeover_required,
            "actions": [action.to_dict() for action in self.actions],
            "evidence_refs": list(self.evidence_refs),
        }


def activate_simulation_orders(
    request: SimulationActivationRequest,
    gateway: SimulationGateway,
) -> SimulationActivationResult:
    """执行模型盘进入模拟账户的提交链路。"""

    gate = evaluate_stage_gate(request.stage_request, request.stage_evidence)
    if not gate.passed:
        return SimulationActivationResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason=_enum_value(gate.blocked_reason) or "stage_gate_blocked",
            stage_gate_result=gate,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )

    intents = tuple(_build_order_intent(row, request) for row in request.target_rows)
    if any(intent is None for intent in intents):
        return SimulationActivationResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason="order_intent_creation_blocked",
            stage_gate_result=gate,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )
    order_intents = tuple(intent for intent in intents if intent is not None)
    risk = evaluate_many(order_intents, request.risk_snapshot, request.risk_profile)
    if not risk.passed:
        orders = tuple(
            SimulationOrderActivation(
                order_intent_id=result.intent_id,
                symbol_ref="symbol:redacted",
                target_qty=0,
                risk_status=result.status,
                gateway_status="not_submitted",
                blocked_reason=result.blocked_reason,
            )
            for result in risk.results
        )
        return SimulationActivationResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason="pretrade_risk_blocked",
            orders=orders,
            risk_result=risk,
            stage_gate_result=gate,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )

    activations: list[SimulationOrderActivation] = []
    for intent in order_intents:
        gateway_result = gateway.submit_order(
            build_simulation_order_request(
                {
                    "run_id": request.run_id,
                    "request_id": f"simulation-submit:{intent.order_intent_id}",
                    "order_intent_id": intent.order_intent_id,
                    "symbol": intent.symbol,
                    "side": intent.side,
                    "quantity": intent.target_qty,
                    "price": _price_for_symbol(request.risk_snapshot, intent.symbol),
                    "authorization_ref": request.authorization_ref,
                    "idempotency_key": intent.idempotency_key,
                }
            )
        )
        payload = _simulation_payload(gateway_result)
        activations.append(
            SimulationOrderActivation(
                order_intent_id=intent.order_intent_id,
                symbol_ref=_symbol_ref(intent.symbol),
                target_qty=intent.target_qty,
                risk_status="pass",
                gateway_status="allowed" if gateway_result.allowed else "blocked",
                blocked_reason=gateway_result.reason_code,
                broker_order_ref=str(payload.get("broker_order_ref") or ""),
            )
        )
        if gateway_result.blocked:
            return SimulationActivationResult(
                status="blocked",
                run_id=request.run_id,
                stage_gate_status=str(gate.gate_status.value),
                submitted_count=sum(1 for item in activations if item.gateway_status == "allowed"),
                blocked_reason=gateway_result.reason_code or "gateway_blocked",
                orders=tuple(activations),
                risk_result=risk,
                stage_gate_result=gate,
                evidence_refs=_stage_evidence_refs(request.stage_evidence),
            )

    return SimulationActivationResult(
        status="submitted",
        run_id=request.run_id,
        stage_gate_status=str(gate.gate_status.value),
        submitted_count=len(activations),
        orders=tuple(activations),
        risk_result=risk,
        stage_gate_result=gate,
        evidence_refs=_stage_evidence_refs(request.stage_evidence),
    )


def execute_simulation_order_plan(
    request: SimulationExecutionEngineRequest,
    gateway: SimulationGateway,
) -> SimulationExecutionEngineResult:
    """执行 P2 生成的模拟订单计划；只使用调用方传入的 simulation gateway。"""

    runtime_reason = _runtime_identity_block_reason(request)
    if runtime_reason:
        return SimulationExecutionEngineResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status="not_evaluated",
            blocked_reason=runtime_reason,
            manual_takeover_required=True,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )
    gate = evaluate_stage_gate(request.stage_request, request.stage_evidence)
    if not gate.passed:
        return SimulationExecutionEngineResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason=_enum_value(gate.blocked_reason) or "stage_gate_blocked",
            manual_takeover_required=True,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )
    if request.order_plan.blocked:
        return SimulationExecutionEngineResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason=request.order_plan.blocked_reason or "order_plan_blocked",
            manual_takeover_required=True,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )

    actions: list[SimulationExecutionAction] = []
    if request.cancel_open_orders and not request.cancel_enabled:
        return SimulationExecutionEngineResult(
            status="blocked",
            run_id=request.run_id,
            stage_gate_status=str(gate.gate_status.value),
            blocked_reason="cancel_disabled",
            manual_takeover_required=True,
            evidence_refs=_stage_evidence_refs(request.stage_evidence),
        )
    for open_order in request.cancel_open_orders:
        action = _cancel_open_order(request, gateway, _open_order(open_order))
        actions.append(action)
        if action.status != "accepted":
            return _execution_stopped(request, gate_status=str(gate.gate_status.value), actions=tuple(actions), reason=action.blocked_reason or action.status)

    if request.order_plan.orders and not request.submit_enabled:
        return _execution_stopped(
            request,
            gate_status=str(gate.gate_status.value),
            actions=tuple(actions),
            reason="submit_disabled",
        )
    for index, item in enumerate(request.order_plan.orders, start=1):
        if index > max(int(request.throttle_batch_size), 1):
            return _execution_stopped(
                request,
                gate_status=str(gate.gate_status.value),
                actions=tuple(actions),
                reason="throttle_batch_size_exceeded",
            )
        action = _submit_plan_item(request, gateway, item)
        actions.append(action)
        if action.status != "accepted":
            return _execution_stopped(request, gate_status=str(gate.gate_status.value), actions=tuple(actions), reason=action.blocked_reason or action.status)

    return _execution_result(
        request,
        gate_status=str(gate.gate_status.value),
        actions=tuple(actions),
        status="executed" if actions else "no_op",
        blocked_reason="",
        manual_takeover_required=False,
    )


class FunctionSimulationGateway:
    """把普通函数适配成 SimulationGateway。"""

    def __init__(
        self,
        submit: Callable[[QmtSimulationOrderRequest], QmtGatewayResult],
        cancel: Callable[[QmtSimulationCancelRequest], QmtGatewayResult] | None = None,
    ) -> None:
        self._submit = submit
        self._cancel = cancel

    def submit_order(self, request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        return self._submit(request)

    def cancel_order(self, request: QmtSimulationCancelRequest) -> QmtGatewayResult:
        if self._cancel is None:
            return build_blocked_result(QMT_SIMULATION_CANCEL_ENDPOINT_ID, "simulation_cancel_gateway_missing")
        return self._cancel(request)


def blocked_simulation_gateway(reason: str = "simulation_gateway_missing") -> FunctionSimulationGateway:
    """构造默认 fail-closed gateway。"""

    return FunctionSimulationGateway(
        lambda request: build_blocked_result(QMT_SIMULATION_SUBMIT_ENDPOINT_ID, reason),
        lambda request: build_blocked_result(QMT_SIMULATION_CANCEL_ENDPOINT_ID, reason),
    )


def _cancel_open_order(
    request: SimulationExecutionEngineRequest,
    gateway: SimulationGateway,
    open_order: SimulationOpenOrderRef,
) -> SimulationExecutionAction:
    gateway_result = gateway.cancel_order(
        build_simulation_cancel_request(
            {
                "run_id": request.run_id,
                "request_id": f"simulation-cancel:{open_order.order_intent_id}",
                "order_intent_id": open_order.order_intent_id,
                "broker_order_ref": open_order.broker_order_ref,
                "symbol": open_order.symbol,
                "authorization_ref": request.authorization_ref,
                "idempotency_key": f"{request.run_id}:cancel:{open_order.order_intent_id}",
            }
        )
    )
    payload = _simulation_payload(gateway_result)
    return SimulationExecutionAction(
        operation="cancel",
        order_intent_id=open_order.order_intent_id,
        status=_gateway_action_status(gateway_result, payload),
        instrument_ref=_symbol_ref(open_order.symbol) if open_order.symbol else "",
        broker_order_ref=str(payload.get("broker_order_ref") or ""),
        cancel_ref=str(payload.get("cancel_ref") or ""),
        blocked_reason=gateway_result.reason_code,
    )


def _submit_plan_item(
    request: SimulationExecutionEngineRequest,
    gateway: SimulationGateway,
    item: object,
) -> SimulationExecutionAction:
    intent = getattr(item, "intent")
    gateway_result = gateway.submit_order(
        build_simulation_order_request(
            {
                "run_id": request.run_id,
                "request_id": f"simulation-submit:{intent.order_intent_id}",
                "order_intent_id": intent.order_intent_id,
                "symbol": intent.symbol,
                "side": intent.side,
                "quantity": intent.target_qty,
                "price": getattr(item, "price", 0),
                "authorization_ref": request.authorization_ref,
                "idempotency_key": intent.idempotency_key,
            }
        )
    )
    payload = _simulation_payload(gateway_result)
    return SimulationExecutionAction(
        operation="submit",
        order_intent_id=intent.order_intent_id,
        status=_gateway_action_status(gateway_result, payload),
        instrument_ref=_symbol_ref(intent.symbol),
        broker_order_ref=str(payload.get("broker_order_ref") or ""),
        cancel_ref=str(payload.get("cancel_ref") or ""),
        blocked_reason=gateway_result.reason_code,
    )


def _build_order_intent(
    row: Mapping[str, object],
    request: SimulationActivationRequest,
) -> OrderIntent | None:
    symbol = str(row.get("symbol") or "")
    if not symbol:
        return None
    qty = _target_quantity(row, request)
    result = create_order_intent(
        {
            "strategy_id": request.strategy_id,
            "run_id": request.run_id,
            "symbol": symbol,
            "side": str(row.get("side") or "buy"),
            "target_trade_date": request.target_trade_date,
            "target_qty": qty,
            "signal_date": str(row.get("signal_date") or request.target_trade_date),
        },
        {"research_adjustment_policy": ADJUSTMENT_POLICY_RAW, "execution_price_policy": ADJUSTMENT_POLICY_RAW},
        {"risk_profile_id": request.risk_profile.risk_profile_id},
    )
    return result.intent if result.ok and result.intent is not None else None


def _target_quantity(row: Mapping[str, object], request: SimulationActivationRequest) -> int:
    if row.get("target_qty") is not None:
        return max(int(row["target_qty"]), 0)
    symbol = str(row.get("symbol") or "")
    price = Decimal(str(_price_for_symbol(request.risk_snapshot, symbol)))
    weight = Decimal(str(row.get("target_weight") or 0))
    capital = Decimal(str(request.capital_base))
    if price <= 0 or weight <= 0 or capital <= 0:
        return 0
    raw_qty = (capital * weight / price).to_integral_value(rounding=ROUND_DOWN)
    lot_size = max(int(request.lot_size), 1)
    return int(raw_qty) // lot_size * lot_size


def _open_order(raw: SimulationOpenOrderRef | Mapping[str, object]) -> SimulationOpenOrderRef:
    if isinstance(raw, SimulationOpenOrderRef):
        return raw
    return SimulationOpenOrderRef(
        order_intent_id=str(raw.get("order_intent_id") or ""),
        broker_order_ref=str(raw.get("broker_order_ref") or raw.get("cancel_ref") or ""),
        symbol=str(raw.get("symbol") or ""),
        status=str(raw.get("status") or "accepted"),
    )


def _runtime_identity_block_reason(request: SimulationExecutionEngineRequest) -> str:
    if request.expected_runtime_mode != "simulation":
        return "runtime_profile_mismatch"
    if not request.expected_runtime_profile:
        return "runtime_profile_missing"
    return ""


def _gateway_action_status(
    gateway_result: QmtGatewayResult,
    payload: Mapping[str, object],
) -> str:
    status = str(payload.get("adapter_status") or "")
    if gateway_result.blocked:
        return "blocked"
    if "unknown" in status.lower():
        return "unknown"
    if payload.get("accepted") is False:
        return "rejected"
    return "accepted"


def _execution_stopped(
    request: SimulationExecutionEngineRequest,
    *,
    gate_status: str,
    actions: tuple[SimulationExecutionAction, ...],
    reason: str,
) -> SimulationExecutionEngineResult:
    return _execution_result(
        request,
        gate_status=gate_status,
        actions=actions,
        status="blocked",
        blocked_reason=reason,
        manual_takeover_required=True,
    )


def _execution_result(
    request: SimulationExecutionEngineRequest,
    *,
    gate_status: str,
    actions: tuple[SimulationExecutionAction, ...],
    status: str,
    blocked_reason: str,
    manual_takeover_required: bool,
) -> SimulationExecutionEngineResult:
    return SimulationExecutionEngineResult(
        status=status,
        run_id=request.run_id,
        stage_gate_status=gate_status,
        actions=actions,
        blocked_reason=blocked_reason,
        submitted_count=sum(1 for item in actions if item.operation == "submit" and item.status == "accepted"),
        cancelled_count=sum(1 for item in actions if item.operation == "cancel" and item.status == "accepted"),
        rejected_count=sum(1 for item in actions if item.status == "rejected"),
        unknown_count=sum(1 for item in actions if item.status == "unknown"),
        manual_takeover_required=manual_takeover_required,
        evidence_refs=_stage_evidence_refs(request.stage_evidence),
    )


def _price_for_symbol(snapshot: RiskInputSnapshot, symbol: str) -> float:
    ref = snapshot.raw_price_refs.get(symbol)
    if ref is None:
        return 0.0
    if isinstance(ref, Mapping):
        return float(ref.get("price") or 0)
    return float(getattr(ref, "price", 0) or 0)


def _simulation_payload(result: QmtGatewayResult) -> Mapping[str, object]:
    if result.allowed_payload is None:
        return {}
    data = dict(result.allowed_payload.data)
    payload = data.get("simulation_operation")
    return payload if isinstance(payload, Mapping) else {}


def _symbol_ref(symbol: str) -> str:
    return "symbol:" + hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:16]


def _stage_evidence_refs(evidence: StageEvidence) -> tuple[str, ...]:
    return tuple(
        item
        for item in (
            evidence.runbook_ref,
            evidence.cr017_consumer_boundary_ref,
            evidence.reconciliation_policy_ref,
            evidence.kill_switch_readiness_ref,
        )
        if item
    )


def _enum_value(value: object) -> str:
    if value is None:
        return ""
    return str(value.value if hasattr(value, "value") else value)
