"""CR015-S03 的本地 OMS order intent 与状态机合同。

本模块只维护内存态订单意图、状态迁移和安全计数，不触达真实 QMT、
broker API、账户、凭据、lake 写入或发布流程。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from enum import Enum
from typing import Mapping, Sequence

from market_data.contracts import ADJUSTMENT_POLICY_RAW, ADJUSTMENT_POLICY_VALUES
from trading.qmt_adapter import BrokerEventType, BrokerOrderEvent, adapter_safety_counters


class OrderState(str, Enum):
    """OMS 显式订单状态集合。"""

    CREATED = "created"
    RISK_PASSED = "risk_passed"
    BLOCKED = "blocked"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_PENDING = "cancel_pending"
    CANCELED = "canceled"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
    MANUAL_REVIEW = "manual_review"
    FROZEN = "frozen"


class OmsEvent(str, Enum):
    """OMS 状态机事件。"""

    RISK_PASS = "risk_pass"
    RISK_BLOCKED = "risk_blocked"
    ADAPTER_ACCEPTED = "adapter_accepted"
    PARTIAL_FILL = "partial_fill"
    FILL_COMPLETE = "fill_complete"
    CANCEL_REQUESTED = "cancel_requested"
    CANCEL_CONFIRMED = "cancel_confirmed"
    CANCEL_FAILED = "cancel_failed"
    REJECT = "reject"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
    REVIEW_REQUIRED = "review_required"
    MARK_FAILED = "mark_failed"
    FREEZE = "freeze"


class OmsResultStatus(str, Enum):
    """OMS 接口返回状态。"""

    CREATED = "created"
    APPLIED = "applied"
    BLOCKED = "blocked"
    ERROR = "error"


class OmsErrorCode(str, Enum):
    """OMS 结构化错误码。"""

    MISSING_RESEARCH_ADJUSTMENT_POLICY = "missing_research_adjustment_policy"
    MISSING_EXECUTION_PRICE_POLICY = "missing_execution_price_policy"
    NON_RAW_EXECUTION_PRICE_BLOCKED = "non_raw_execution_price_blocked"
    UNSUPPORTED_RESEARCH_ADJUSTMENT_POLICY = (
        "unsupported_research_adjustment_policy"
    )
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_TARGET_QTY = "invalid_target_qty"
    ILLEGAL_TRANSITION = "illegal_transition"
    UNSUPPORTED_BROKER_EVENT = "unsupported_broker_event"


OMS_STATE_VALUES: tuple[str, ...] = tuple(state.value for state in OrderState)
SUCCESS_TERMINAL_STATES = frozenset(
    {
        OrderState.FILLED,
        OrderState.CANCELED,
    }
)
TERMINAL_STATES = frozenset(
    {
        OrderState.FILLED,
        OrderState.CANCELED,
        OrderState.REJECTED,
        OrderState.FAILED,
        OrderState.BLOCKED,
    }
)
MANUAL_REVIEW_STATES = frozenset(
    {
        OrderState.UNKNOWN,
        OrderState.TIMEOUT,
        OrderState.MANUAL_REVIEW,
    }
)

STATE_TRANSITIONS: Mapping[tuple[OrderState, OmsEvent], OrderState] = {
    (OrderState.CREATED, OmsEvent.RISK_PASS): OrderState.RISK_PASSED,
    (OrderState.CREATED, OmsEvent.RISK_BLOCKED): OrderState.BLOCKED,
    (OrderState.CREATED, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.RISK_PASSED, OmsEvent.ADAPTER_ACCEPTED): OrderState.ACCEPTED,
    (OrderState.RISK_PASSED, OmsEvent.REJECT): OrderState.REJECTED,
    (OrderState.RISK_PASSED, OmsEvent.TIMEOUT): OrderState.TIMEOUT,
    (OrderState.RISK_PASSED, OmsEvent.UNKNOWN): OrderState.UNKNOWN,
    (OrderState.RISK_PASSED, OmsEvent.CANCEL_REQUESTED): OrderState.CANCEL_PENDING,
    (OrderState.RISK_PASSED, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.RISK_PASSED, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.ACCEPTED, OmsEvent.PARTIAL_FILL): OrderState.PARTIALLY_FILLED,
    (OrderState.ACCEPTED, OmsEvent.FILL_COMPLETE): OrderState.FILLED,
    (OrderState.ACCEPTED, OmsEvent.CANCEL_REQUESTED): OrderState.CANCEL_PENDING,
    (OrderState.ACCEPTED, OmsEvent.REJECT): OrderState.REJECTED,
    (OrderState.ACCEPTED, OmsEvent.TIMEOUT): OrderState.TIMEOUT,
    (OrderState.ACCEPTED, OmsEvent.UNKNOWN): OrderState.UNKNOWN,
    (OrderState.ACCEPTED, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.ACCEPTED, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.PARTIALLY_FILLED, OmsEvent.PARTIAL_FILL): (
        OrderState.PARTIALLY_FILLED
    ),
    (OrderState.PARTIALLY_FILLED, OmsEvent.FILL_COMPLETE): OrderState.FILLED,
    (OrderState.PARTIALLY_FILLED, OmsEvent.CANCEL_REQUESTED): (
        OrderState.CANCEL_PENDING
    ),
    (OrderState.PARTIALLY_FILLED, OmsEvent.REJECT): OrderState.REJECTED,
    (OrderState.PARTIALLY_FILLED, OmsEvent.TIMEOUT): OrderState.TIMEOUT,
    (OrderState.PARTIALLY_FILLED, OmsEvent.UNKNOWN): OrderState.UNKNOWN,
    (OrderState.PARTIALLY_FILLED, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.PARTIALLY_FILLED, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.CANCEL_PENDING, OmsEvent.CANCEL_CONFIRMED): OrderState.CANCELED,
    (OrderState.CANCEL_PENDING, OmsEvent.CANCEL_FAILED): OrderState.MANUAL_REVIEW,
    (OrderState.CANCEL_PENDING, OmsEvent.TIMEOUT): OrderState.TIMEOUT,
    (OrderState.CANCEL_PENDING, OmsEvent.UNKNOWN): OrderState.UNKNOWN,
    (OrderState.CANCEL_PENDING, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.CANCEL_PENDING, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.TIMEOUT, OmsEvent.REVIEW_REQUIRED): OrderState.MANUAL_REVIEW,
    (OrderState.TIMEOUT, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.TIMEOUT, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.UNKNOWN, OmsEvent.REVIEW_REQUIRED): OrderState.MANUAL_REVIEW,
    (OrderState.UNKNOWN, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.UNKNOWN, OmsEvent.FREEZE): OrderState.FROZEN,
    (OrderState.MANUAL_REVIEW, OmsEvent.MARK_FAILED): OrderState.FAILED,
    (OrderState.MANUAL_REVIEW, OmsEvent.FREEZE): OrderState.FROZEN,
}

BROKER_EVENT_TO_OMS_EVENT: Mapping[str, OmsEvent] = {
    BrokerEventType.ACCEPTED.value: OmsEvent.ADAPTER_ACCEPTED,
    BrokerEventType.PARTIAL.value: OmsEvent.PARTIAL_FILL,
    BrokerEventType.FILLED.value: OmsEvent.FILL_COMPLETE,
    BrokerEventType.CANCEL_CONFIRMED.value: OmsEvent.CANCEL_CONFIRMED,
    BrokerEventType.CANCEL_FAILED.value: OmsEvent.CANCEL_FAILED,
    BrokerEventType.REJECTED.value: OmsEvent.REJECT,
    BrokerEventType.TIMEOUT.value: OmsEvent.TIMEOUT,
    BrokerEventType.UNKNOWN.value: OmsEvent.UNKNOWN,
    "canceled": OmsEvent.CANCEL_CONFIRMED,
    "cancel_failed": OmsEvent.CANCEL_FAILED,
}


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """本地订单意图合同。"""

    order_intent_id: str
    strategy_id: str
    run_id: str
    symbol: str
    side: str
    target_qty: int
    target_trade_date: str
    research_adjustment_policy: str
    execution_price_policy: str
    idempotency_key: str
    risk_profile_id: str = ""
    signal_date: str = ""
    state: OrderState = OrderState.CREATED
    manual_review_required: bool = False
    retry_count: int = 0
    filled_qty: int = 0
    remaining_qty: int = 0
    broker_order_ref: str = ""
    incident_ref: str = ""
    last_event: str = ""
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class StateTransitionEvent:
    """状态迁移审计事件，供后续 dry-run / broker lake 合同消费。"""

    intent_id: str
    from_state: OrderState
    to_state: OrderState
    event: OmsEvent
    reason: str
    event_time: datetime
    manual_review_required: bool = False
    broker_order_ref: str = ""
    safety_counters: Mapping[str, int] = field(default_factory=lambda: oms_safety_counters())


@dataclass(frozen=True, slots=True)
class OmsError:
    """OMS 结构化错误。"""

    error_code: OmsErrorCode
    message: str
    intent_id: str = ""
    detail_code: str = ""


@dataclass(frozen=True, slots=True)
class OmsResult:
    """OMS 单入口返回值。"""

    status: OmsResultStatus
    intent: OrderIntent | None
    transition_event: StateTransitionEvent | None = None
    error: OmsError | None = None
    safety_counters: Mapping[str, int] = field(default_factory=lambda: oms_safety_counters())

    @property
    def ok(self) -> bool:
        return self.status in {OmsResultStatus.CREATED, OmsResultStatus.APPLIED}

    @property
    def blocked(self) -> bool:
        return self.status is OmsResultStatus.BLOCKED


@dataclass(frozen=True, slots=True)
class FreezeOrdersResult:
    """本地冻结结果；不代表真实 broker 撤单。"""

    frozen_intents: tuple[OrderIntent, ...]
    incident_ref: str
    transition_events: tuple[StateTransitionEvent, ...]
    safety_counters: Mapping[str, int] = field(default_factory=lambda: oms_safety_counters())


def oms_safety_counters() -> dict[str, int]:
    """返回 CR015-S03 必须保持为 0 的真实操作和异常成功计数。"""

    counters = adapter_safety_counters()
    counters.update(
        {
            "unknown_success_count": 0,
            "timeout_success_count": 0,
        }
    )
    return counters


def build_idempotency_key(intent_fields: Mapping[str, object]) -> str:
    """基于稳定字段生成幂等键。"""

    payload = {
        "strategy_id": _string_value(intent_fields.get("strategy_id")),
        "run_id": _string_value(intent_fields.get("run_id")),
        "symbol": _string_value(intent_fields.get("symbol")),
        "side": _string_value(intent_fields.get("side")).lower(),
        "target_trade_date": _date_value(intent_fields.get("target_trade_date")),
        "target_qty": _int_value(intent_fields.get("target_qty")),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def create_order_intent(
    target_row: Mapping[str, object],
    policy_metadata: Mapping[str, object] | None = None,
    run_context: Mapping[str, object] | None = None,
    *,
    now: datetime | None = None,
) -> OmsResult:
    """创建本地 order intent；policy 缺失或执行价非 raw 时返回 blocked。"""

    policy_metadata = policy_metadata or {}
    run_context = run_context or {}
    observed_at = _observed_at(now)

    research_policy = _first_string(
        policy_metadata,
        target_row,
        run_context,
        key="research_adjustment_policy",
    )
    if not research_policy:
        return _blocked_creation_result(
            OmsErrorCode.MISSING_RESEARCH_ADJUSTMENT_POLICY,
            "research_adjustment_policy is required",
        )
    if research_policy not in ADJUSTMENT_POLICY_VALUES:
        return _blocked_creation_result(
            OmsErrorCode.UNSUPPORTED_RESEARCH_ADJUSTMENT_POLICY,
            "research_adjustment_policy is not supported",
            detail_code=research_policy,
        )

    execution_policy = _first_string(
        policy_metadata,
        target_row,
        run_context,
        key="execution_price_policy",
    )
    if not execution_policy:
        return _blocked_creation_result(
            OmsErrorCode.MISSING_EXECUTION_PRICE_POLICY,
            "execution_price_policy is required",
        )
    if execution_policy != ADJUSTMENT_POLICY_RAW:
        return _blocked_creation_result(
            OmsErrorCode.NON_RAW_EXECUTION_PRICE_BLOCKED,
            "execution_price_policy must be raw",
            detail_code=execution_policy,
        )

    required = {
        "strategy_id": _first_string(run_context, target_row, key="strategy_id"),
        "run_id": _first_string(run_context, target_row, key="run_id"),
        "symbol": _first_string(target_row, run_context, key="symbol"),
        "side": _first_string(target_row, run_context, key="side").lower(),
        "target_trade_date": _first_date(
            target_row,
            run_context,
            keys=("target_trade_date", "trade_date"),
        ),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        return _blocked_creation_result(
            OmsErrorCode.MISSING_REQUIRED_FIELD,
            "required order intent field is missing",
            detail_code=",".join(missing),
        )

    qty = _first_int(target_row, run_context, keys=("target_qty", "quantity", "qty"))
    if qty <= 0:
        return _blocked_creation_result(
            OmsErrorCode.INVALID_TARGET_QTY,
            "target_qty must be positive",
            detail_code=str(qty),
        )

    idempotency_fields = {
        **required,
        "target_qty": qty,
    }
    idempotency_key = build_idempotency_key(idempotency_fields)
    order_intent_id = _first_string(target_row, run_context, key="order_intent_id")
    if not order_intent_id:
        order_intent_id = f"intent-{idempotency_key[:16]}"

    intent = OrderIntent(
        order_intent_id=order_intent_id,
        strategy_id=required["strategy_id"],
        run_id=required["run_id"],
        symbol=required["symbol"],
        side=required["side"],
        target_qty=qty,
        target_trade_date=required["target_trade_date"],
        research_adjustment_policy=research_policy,
        execution_price_policy=execution_policy,
        idempotency_key=idempotency_key,
        risk_profile_id=_first_string(run_context, target_row, key="risk_profile_id"),
        signal_date=_first_date(target_row, run_context, keys=("signal_date",)),
        remaining_qty=qty,
        updated_at=observed_at,
    )
    return OmsResult(
        status=OmsResultStatus.CREATED,
        intent=intent,
        safety_counters=oms_safety_counters(),
    )


def apply_risk_result(
    intent: OrderIntent,
    risk_result: object,
    *,
    now: datetime | None = None,
) -> OmsResult:
    """消费 S04 风控结果；失败时仅本地 blocked，不触达 adapter。"""

    passed, reason = _risk_result_value(risk_result)
    event = OmsEvent.RISK_PASS if passed else OmsEvent.RISK_BLOCKED
    return apply_state_event(intent, event, reason=reason, now=now)


def apply_broker_event(
    intent: OrderIntent,
    broker_event: BrokerOrderEvent | Mapping[str, object] | str,
    *,
    now: datetime | None = None,
) -> OmsResult:
    """消费 S02 mock broker event 并推进本地状态。"""

    event_value = _broker_event_value(broker_event)
    oms_event = BROKER_EVENT_TO_OMS_EVENT.get(event_value)
    if oms_event is None:
        return _transition_error(
            intent,
            OmsErrorCode.UNSUPPORTED_BROKER_EVENT,
            "broker event is not supported by OMS",
            detail_code=event_value,
        )

    return apply_state_event(
        intent,
        oms_event,
        reason=_broker_reason(broker_event),
        now=now,
        broker_order_ref=_broker_order_ref(broker_event),
        filled_quantity=_broker_int_value(broker_event, "filled_quantity"),
        remaining_quantity=_broker_int_value(broker_event, "remaining_quantity"),
    )


def apply_state_event(
    intent: OrderIntent,
    event: OmsEvent | str,
    *,
    reason: str = "",
    now: datetime | None = None,
    broker_order_ref: str = "",
    filled_quantity: int | None = None,
    remaining_quantity: int | None = None,
    incident_ref: str = "",
) -> OmsResult:
    """按显式状态表推进状态；非法迁移返回 error 且不修改 intent。"""

    oms_event = _coerce_oms_event(event)
    if oms_event is None:
        return _transition_error(
            intent,
            OmsErrorCode.ILLEGAL_TRANSITION,
            "OMS event is not supported",
            detail_code=str(event),
        )

    next_state = STATE_TRANSITIONS.get((intent.state, oms_event))
    if next_state is None:
        return _transition_error(
            intent,
            OmsErrorCode.ILLEGAL_TRANSITION,
            "OMS state transition is not allowed",
            detail_code=f"{intent.state.value}->{oms_event.value}",
        )

    manual_review_required = (
        intent.manual_review_required
        or next_state in MANUAL_REVIEW_STATES
        or oms_event is OmsEvent.CANCEL_FAILED
    )
    updated = replace(
        intent,
        state=next_state,
        manual_review_required=manual_review_required,
        filled_qty=_next_filled_qty(intent, next_state, filled_quantity),
        remaining_qty=_next_remaining_qty(intent, next_state, remaining_quantity),
        broker_order_ref=broker_order_ref or intent.broker_order_ref,
        incident_ref=incident_ref or intent.incident_ref,
        last_event=oms_event.value,
        updated_at=_observed_at(now),
    )
    transition = StateTransitionEvent(
        intent_id=intent.order_intent_id,
        from_state=intent.state,
        to_state=next_state,
        event=oms_event,
        reason=reason or oms_event.value,
        event_time=_observed_at(now),
        manual_review_required=manual_review_required,
        broker_order_ref=updated.broker_order_ref,
        safety_counters=oms_safety_counters(),
    )
    return OmsResult(
        status=OmsResultStatus.APPLIED,
        intent=updated,
        transition_event=transition,
        safety_counters=oms_safety_counters(),
    )


def freeze_orders(
    intents: Sequence[OrderIntent],
    trigger_reason: str,
    *,
    incident_ref: str | None = None,
    now: datetime | None = None,
) -> FreezeOrdersResult:
    """只冻结本地 OMS 状态，不生成真实 broker 撤单。"""

    observed_at = _observed_at(now)
    incident = incident_ref or _build_incident_ref(trigger_reason, observed_at)
    frozen: list[OrderIntent] = []
    events: list[StateTransitionEvent] = []
    for intent in intents:
        if intent.state in TERMINAL_STATES:
            frozen.append(replace(intent, incident_ref=incident, updated_at=observed_at))
            continue
        result = apply_state_event(
            intent,
            OmsEvent.FREEZE,
            reason=trigger_reason,
            now=observed_at,
            incident_ref=incident,
        )
        if result.ok and result.intent is not None and result.transition_event is not None:
            frozen.append(result.intent)
            events.append(result.transition_event)
        else:
            frozen.append(replace(intent, incident_ref=incident, updated_at=observed_at))
    return FreezeOrdersResult(
        frozen_intents=tuple(frozen),
        incident_ref=incident,
        transition_events=tuple(events),
        safety_counters=oms_safety_counters(),
    )


def order_intent_to_broker_lake_event(intent: OrderIntent) -> dict[str, object]:
    """输出 S05 broker lake 可消费的 order_intent 事件字典。"""

    return {
        "event_type": "order_intent",
        "order_intent_id": intent.order_intent_id,
        "strategy_id": intent.strategy_id,
        "run_id": intent.run_id,
        "symbol": intent.symbol,
        "side": intent.side,
        "target_qty": intent.target_qty,
        "target_trade_date": intent.target_trade_date,
        "signal_date": intent.signal_date,
        "research_adjustment_policy": intent.research_adjustment_policy,
        "execution_price_policy": intent.execution_price_policy,
        "risk_profile_id": intent.risk_profile_id,
        "idempotency_key": intent.idempotency_key,
        "order_state": intent.state.value,
        "last_event": intent.last_event,
        "updated_at": intent.updated_at.isoformat() if intent.updated_at else "",
    }


def state_transition_to_broker_lake_event(
    intent: OrderIntent,
    transition_event: StateTransitionEvent,
) -> dict[str, object]:
    """输出 S05 broker lake 可消费的 OMS transition 事件字典。"""

    return {
        "event_type": "broker_order",
        "order_intent_id": intent.order_intent_id,
        "strategy_id": intent.strategy_id,
        "run_id": intent.run_id,
        "symbol": intent.symbol,
        "broker_order_status": transition_event.to_state.value,
        "oms_event": transition_event.event.value,
        "from_state": transition_event.from_state.value,
        "to_state": transition_event.to_state.value,
        "transition_reason": transition_event.reason,
        "trade_date": intent.target_trade_date,
        "event_time": transition_event.event_time.isoformat(),
        "manual_review_required": transition_event.manual_review_required,
        "broker_order_ref": transition_event.broker_order_ref,
        "filled_qty": intent.filled_qty,
        "remaining_qty": intent.remaining_qty,
    }


def is_success_state(state: OrderState | str) -> bool:
    """判断是否属于成功终态；unknown / timeout 永远不是成功。"""

    current = _coerce_state(state)
    return current in SUCCESS_TERMINAL_STATES


def requires_manual_review(state: OrderState | str) -> bool:
    """判断状态是否必须人工复核。"""

    current = _coerce_state(state)
    return current in MANUAL_REVIEW_STATES


def _blocked_creation_result(
    error_code: OmsErrorCode,
    message: str,
    *,
    detail_code: str = "",
) -> OmsResult:
    return OmsResult(
        status=OmsResultStatus.BLOCKED,
        intent=None,
        error=OmsError(error_code=error_code, message=message, detail_code=detail_code),
        safety_counters=oms_safety_counters(),
    )


def _transition_error(
    intent: OrderIntent,
    error_code: OmsErrorCode,
    message: str,
    *,
    detail_code: str = "",
) -> OmsResult:
    return OmsResult(
        status=OmsResultStatus.ERROR,
        intent=intent,
        error=OmsError(
            error_code=error_code,
            message=message,
            intent_id=intent.order_intent_id,
            detail_code=detail_code,
        ),
        safety_counters=oms_safety_counters(),
    )


def _risk_result_value(risk_result: object) -> tuple[bool, str]:
    if isinstance(risk_result, bool):
        return risk_result, "risk_pass" if risk_result else "risk_blocked"
    if isinstance(risk_result, str):
        lowered = risk_result.lower()
        return lowered in {"pass", "passed", "risk_passed"}, lowered
    if not isinstance(risk_result, Mapping):
        passed_attr = getattr(risk_result, "passed", None)
        if isinstance(passed_attr, bool):
            reason = _string_value(getattr(risk_result, "blocked_reason", ""))
            status = _string_value(getattr(risk_result, "status", ""))
            return passed_attr, reason or status or "risk_pass"
        status_attr = _string_value(getattr(risk_result, "status", "")).lower()
        if status_attr:
            return status_attr in {"pass", "passed", "risk_passed"}, status_attr
        return False, "risk_result_invalid"
    status = _string_value(risk_result.get("status")).lower()
    passed = status in {"pass", "passed", "risk_passed"}
    reason = _string_value(risk_result.get("reason")) or status
    return passed, reason


def _next_filled_qty(
    intent: OrderIntent,
    next_state: OrderState,
    filled_quantity: int | None,
) -> int:
    if next_state is OrderState.FILLED:
        return intent.target_qty
    if filled_quantity is None:
        return intent.filled_qty
    return min(max(filled_quantity, 0), intent.target_qty)


def _next_remaining_qty(
    intent: OrderIntent,
    next_state: OrderState,
    remaining_quantity: int | None,
) -> int:
    if next_state is OrderState.FILLED:
        return 0
    if remaining_quantity is None:
        return max(intent.target_qty - intent.filled_qty, 0)
    return min(max(remaining_quantity, 0), intent.target_qty)


def _build_incident_ref(trigger_reason: str, observed_at: datetime) -> str:
    payload = f"{trigger_reason}|{observed_at.isoformat()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"incident-{digest[:16]}"


def _broker_event_value(broker_event: BrokerOrderEvent | Mapping[str, object] | str) -> str:
    if isinstance(broker_event, str):
        return broker_event
    raw_value: object
    if isinstance(broker_event, Mapping):
        raw_value = broker_event.get("broker_event_type", broker_event.get("event_type", ""))
    else:
        raw_value = broker_event.broker_event_type
    return _enum_or_string(raw_value)


def _broker_reason(broker_event: BrokerOrderEvent | Mapping[str, object] | str) -> str:
    if isinstance(broker_event, str):
        return broker_event
    if isinstance(broker_event, Mapping):
        return _string_value(broker_event.get("reason"))
    return broker_event.reason


def _broker_order_ref(broker_event: BrokerOrderEvent | Mapping[str, object] | str) -> str:
    if isinstance(broker_event, str):
        return ""
    if isinstance(broker_event, Mapping):
        return _string_value(broker_event.get("broker_order_ref"))
    return broker_event.broker_order_ref


def _broker_int_value(
    broker_event: BrokerOrderEvent | Mapping[str, object] | str,
    key: str,
) -> int | None:
    if isinstance(broker_event, str):
        return None
    raw_value: object
    if isinstance(broker_event, Mapping):
        raw_value = broker_event.get(key)
    else:
        raw_value = getattr(broker_event, key)
    if raw_value is None:
        return None
    return _int_value(raw_value)


def _first_string(*sources: Mapping[str, object], key: str) -> str:
    for source in sources:
        value = _string_value(source.get(key))
        if value:
            return value
    return ""


def _first_date(
    *sources: Mapping[str, object],
    keys: Sequence[str],
) -> str:
    for source in sources:
        for key in keys:
            value = _date_value(source.get(key))
            if value:
                return value
    return ""


def _first_int(
    *sources: Mapping[str, object],
    keys: Sequence[str],
) -> int:
    for source in sources:
        for key in keys:
            value = source.get(key)
            if value is not None and str(value) != "":
                return _int_value(value)
    return 0


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value).strip()


def _date_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _enum_or_string(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _coerce_oms_event(value: OmsEvent | str) -> OmsEvent | None:
    if isinstance(value, OmsEvent):
        return value
    try:
        return OmsEvent(str(value))
    except ValueError:
        return None


def _coerce_state(value: OrderState | str) -> OrderState | None:
    if isinstance(value, OrderState):
        return value
    try:
        return OrderState(str(value))
    except ValueError:
        return None


def _observed_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "BROKER_EVENT_TO_OMS_EVENT",
    "MANUAL_REVIEW_STATES",
    "OMS_STATE_VALUES",
    "STATE_TRANSITIONS",
    "SUCCESS_TERMINAL_STATES",
    "TERMINAL_STATES",
    "FreezeOrdersResult",
    "OmsError",
    "OmsErrorCode",
    "OmsEvent",
    "OmsResult",
    "OmsResultStatus",
    "OrderIntent",
    "OrderState",
    "StateTransitionEvent",
    "apply_broker_event",
    "apply_risk_result",
    "apply_state_event",
    "build_idempotency_key",
    "create_order_intent",
    "freeze_orders",
    "is_success_state",
    "oms_safety_counters",
    "order_intent_to_broker_lake_event",
    "requires_manual_review",
    "state_transition_to_broker_lake_event",
]
