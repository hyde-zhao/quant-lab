"""CR015-S02 的 QMT broker adapter 离线合同。

本模块只生成 shadow / dry-run / mock 结果，不导入或调用真实 QMT、
MiniQMT、XtQuant 或 broker API。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Mapping

from market_data.contracts import ADJUSTMENT_POLICY_RAW

from trading.qmt_environment import (
    AdapterMode,
    CR015_ALLOWED_ADAPTER_MODES,
    ForbiddenOperationCounters,
)
from trading.qmt_transport import (
    TransportAck,
    TransportPayload,
    TransportStatus,
    validate_payload_metadata,
)


PASSED_RISK_STATUS = "pass"


class AdapterResultStatus(str, Enum):
    """CR015-S02 adapter 合同输出状态。"""

    BLOCKED = "blocked"
    SHADOW_ACCEPTED = "shadow_accepted"
    DRY_RUN_PLANNED = "dry_run_planned"
    MOCK_EVENT_GENERATED = "mock_event_generated"


class AdapterBlockedReason(str, Enum):
    """adapter 以结构化方式暴露的阻断原因。"""

    MODE_NOT_AUTHORIZED = "mode_not_authorized"
    RISK_NOT_PASSED = "risk_not_passed"
    NON_RAW_EXECUTION_PRICE_BLOCKED = "non_raw_execution_price_blocked"
    TRANSPORT_PAYLOAD_REJECTED = "transport_payload_rejected"
    STAGE_GATE_BLOCKED = "stage_gate_blocked"


class BrokerEventType(str, Enum):
    """mock broker event 类型，供后续 OMS 状态机消费。"""

    ACCEPTED = "accepted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCEL_CONFIRMED = "cancel_confirmed"
    CANCEL_FAILED = "cancel_failed"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class MockBrokerScenario(str, Enum):
    """离线 mock broker event fixture 场景。"""

    ACCEPTED = "accepted"
    PARTIAL = "partial"
    FILLED = "filled"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AdapterRequest:
    """OMS / shadow pipeline 传入 adapter 的最小订单意图合同。"""

    intent_id: str
    adapter_mode: AdapterMode | str
    execution_price_policy: str | Enum = ADJUSTMENT_POLICY_RAW
    risk_status: str = PASSED_RISK_STATUS
    side: str = "buy"
    symbol: str = ""
    quantity: int = 0
    order_price: float | None = None
    strategy_id: str = ""
    run_id: str = ""
    transport_payload: TransportPayload | None = None
    mock_scenario: MockBrokerScenario | str = MockBrokerScenario.ACCEPTED
    evidence_ref: str = ""


@dataclass(frozen=True, slots=True)
class CancelOrderRequest:
    """CR015 阶段的撤单合同；不会触达真实撤单 API。"""

    intent_id: str
    broker_order_ref: str
    adapter_mode: AdapterMode | str
    current_oms_state: str = ""
    cancel_reason: str = ""
    evidence_ref: str = ""


@dataclass(frozen=True, slots=True)
class BrokerOrderEvent:
    """mock broker event 的脱敏结构。"""

    broker_event_type: BrokerEventType
    intent_id: str
    broker_order_ref: str
    adapter_mode: AdapterMode
    filled_quantity: int = 0
    remaining_quantity: int = 0
    reason: str = ""
    observed_at: datetime | None = None
    raw_event_ref: str = ""
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: adapter_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """submit / cancel 合同返回值。"""

    status: AdapterResultStatus
    intent_id: str
    adapter_mode: AdapterMode | None
    blocked_reason: AdapterBlockedReason | None = None
    detail_code: str = ""
    evidence_ref: str = ""
    dry_run_plan: Mapping[str, object] = field(default_factory=dict)
    broker_event: BrokerOrderEvent | None = None
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: adapter_safety_counters()
    )
    transport_ack: TransportAck | None = None

    @property
    def blocked(self) -> bool:
        return self.status is AdapterResultStatus.BLOCKED


def adapter_safety_counters() -> dict[str, int]:
    """返回 CR015-S02 必须保持为 0 的真实操作计数。"""

    counters = ForbiddenOperationCounters().to_dict()
    counters.update(
        {
            "real_lake_write": 0,
            "provider_fetch": 0,
            "publish": 0,
            "adapter_calls": 0,
            "real_order_call": 0,
            "real_cancel_call": 0,
            "account_query_call": 0,
            "account_write_call": 0,
            "simulation_run": 0,
            "live_activation": 0,
            "adapter_call_on_block": 0,
            "scale_up_allowed_without_cr017": 0,
            "adjusted_execution_pass_count": 0,
        }
    )
    return counters


def validate_adapter_mode(
    adapter_mode: AdapterMode | str,
) -> AdapterBlockedReason | None:
    """CR015 只允许 shadow / dry_run / mock，其他模式一律阻断。"""

    mode = _coerce_adapter_mode(adapter_mode)
    if mode is None or mode not in CR015_ALLOWED_ADAPTER_MODES:
        return AdapterBlockedReason.MODE_NOT_AUTHORIZED
    return None


def assert_raw_execution_policy(
    execution_price_policy: str | Enum,
) -> AdapterBlockedReason | None:
    """只有 exact `raw` 可作为 QMT 执行价口径。"""

    if _policy_value(execution_price_policy) != ADJUSTMENT_POLICY_RAW:
        return AdapterBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED
    return None


def precheck_stage_gate_result(
    gate_result: object,
    adapter_mode: AdapterMode | str,
    *,
    intent_id: str = "",
    evidence_ref: str = "",
) -> AdapterResult | None:
    """消费 CR016 stage gate result；blocked 时不进入 adapter 后续路径。"""

    if _stage_gate_value(gate_result, "gate_status") == "pass":
        return None

    blocked_reason = _stage_gate_value(gate_result, "blocked_reason")
    return blocked_result(
        intent_id,
        adapter_mode,
        AdapterBlockedReason.STAGE_GATE_BLOCKED,
        detail_code=blocked_reason or "stage_gate_blocked",
        evidence_ref=evidence_ref or _stage_gate_value(gate_result, "evidence_ref"),
    )


def submit_intent(
    request: AdapterRequest,
    *,
    now: datetime | None = None,
) -> AdapterResult:
    """提交 risk-passed intent 的离线 adapter 合同。"""

    observed_at = _observed_at(now)
    mode = _coerce_adapter_mode(request.adapter_mode)

    if request.risk_status != PASSED_RISK_STATUS:
        return blocked_result(
            request.intent_id,
            mode,
            AdapterBlockedReason.RISK_NOT_PASSED,
            detail_code=request.risk_status,
            evidence_ref=request.evidence_ref,
        )

    mode_block = validate_adapter_mode(request.adapter_mode)
    if mode_block is not None:
        return blocked_result(
            request.intent_id,
            mode,
            mode_block,
            detail_code=_adapter_mode_value(request.adapter_mode),
            evidence_ref=request.evidence_ref,
        )

    policy_block = assert_raw_execution_policy(request.execution_price_policy)
    if policy_block is not None:
        return blocked_result(
            request.intent_id,
            mode,
            policy_block,
            detail_code=_policy_value(request.execution_price_policy),
            evidence_ref=request.evidence_ref,
        )

    if request.transport_payload is not None:
        transport_ack = validate_payload_metadata(
            request.transport_payload,
            now=observed_at,
        )
        if transport_ack.status is not TransportStatus.ACCEPTED:
            return blocked_result(
                request.intent_id,
                mode,
                AdapterBlockedReason.TRANSPORT_PAYLOAD_REJECTED,
                detail_code=(
                    transport_ack.error_code.value
                    if transport_ack.error_code is not None
                    else transport_ack.status.value
                ),
                evidence_ref=request.evidence_ref,
                transport_ack=transport_ack,
            )

    if mode is AdapterMode.MOCK:
        event = build_mock_broker_event(
            request.mock_scenario,
            request,
            observed_at=observed_at,
        )
        return AdapterResult(
            status=AdapterResultStatus.MOCK_EVENT_GENERATED,
            intent_id=request.intent_id,
            adapter_mode=mode,
            broker_event=event,
            evidence_ref=request.evidence_ref,
        )

    plan = _build_offline_plan(
        "submit",
        request.intent_id,
        mode,
        side=request.side,
        symbol=request.symbol,
        quantity=request.quantity,
        order_price=request.order_price,
        execution_price_policy=_policy_value(request.execution_price_policy),
        observed_at=observed_at,
    )
    return AdapterResult(
        status=(
            AdapterResultStatus.SHADOW_ACCEPTED
            if mode is AdapterMode.SHADOW
            else AdapterResultStatus.DRY_RUN_PLANNED
        ),
        intent_id=request.intent_id,
        adapter_mode=mode,
        dry_run_plan=plan,
        evidence_ref=request.evidence_ref,
    )


def cancel_order(
    request: CancelOrderRequest,
    *,
    now: datetime | None = None,
) -> AdapterResult:
    """生成离线撤单计划；CR015 不调用真实 cancel。"""

    observed_at = _observed_at(now)
    mode = _coerce_adapter_mode(request.adapter_mode)
    mode_block = validate_adapter_mode(request.adapter_mode)
    if mode_block is not None:
        return blocked_result(
            request.intent_id,
            mode,
            mode_block,
            detail_code=_adapter_mode_value(request.adapter_mode),
            evidence_ref=request.evidence_ref,
        )

    plan = _build_offline_plan(
        "cancel",
        request.intent_id,
        mode,
        broker_order_ref=request.broker_order_ref,
        current_oms_state=request.current_oms_state,
        cancel_reason=request.cancel_reason,
        observed_at=observed_at,
    )
    return AdapterResult(
        status=AdapterResultStatus.DRY_RUN_PLANNED,
        intent_id=request.intent_id,
        adapter_mode=mode,
        dry_run_plan=plan,
        evidence_ref=request.evidence_ref,
    )


def blocked_result(
    intent_id: str,
    adapter_mode: AdapterMode | str | None,
    blocked_reason: AdapterBlockedReason,
    *,
    detail_code: str = "",
    evidence_ref: str = "",
    transport_ack: TransportAck | None = None,
) -> AdapterResult:
    """构造带安全计数的标准 blocked result。"""

    mode = _coerce_adapter_mode(adapter_mode) if adapter_mode is not None else None
    return AdapterResult(
        status=AdapterResultStatus.BLOCKED,
        intent_id=intent_id,
        adapter_mode=mode,
        blocked_reason=blocked_reason,
        detail_code=detail_code,
        evidence_ref=evidence_ref,
        safety_counters=adapter_safety_counters(),
        transport_ack=transport_ack,
    )


def build_mock_broker_event(
    scenario: MockBrokerScenario | str,
    intent: AdapterRequest | Mapping[str, object],
    *,
    observed_at: datetime | None = None,
) -> BrokerOrderEvent:
    """按 fixture 场景生成 mock broker event。"""

    mock_scenario = _coerce_mock_scenario(scenario)
    intent_id = _intent_value(intent, "intent_id", "unknown-intent")
    mode = _coerce_adapter_mode(_intent_value(intent, "adapter_mode", AdapterMode.MOCK))
    adapter_mode = mode if mode is not None else AdapterMode.MOCK
    quantity = max(_int_value(_intent_value(intent, "quantity", 0)), 0)

    filled_quantity = 0
    remaining_quantity = quantity
    reason = ""
    if mock_scenario is MockBrokerScenario.PARTIAL:
        filled_quantity = max(1, quantity // 2) if quantity else 0
        remaining_quantity = max(quantity - filled_quantity, 0)
        reason = "mock_partial_fill"
    elif mock_scenario is MockBrokerScenario.FILLED:
        filled_quantity = quantity
        remaining_quantity = 0
        reason = "mock_filled"
    elif mock_scenario is MockBrokerScenario.REJECTED:
        reason = "mock_rejected"
    elif mock_scenario is MockBrokerScenario.TIMEOUT:
        reason = "mock_timeout"
    elif mock_scenario is MockBrokerScenario.UNKNOWN:
        reason = "mock_unknown"
    else:
        reason = "mock_accepted"

    return BrokerOrderEvent(
        broker_event_type=BrokerEventType(mock_scenario.value),
        intent_id=str(intent_id),
        broker_order_ref=f"mock-{intent_id}-{mock_scenario.value}",
        adapter_mode=adapter_mode,
        filled_quantity=filled_quantity,
        remaining_quantity=remaining_quantity,
        reason=reason,
        observed_at=_observed_at(observed_at),
        raw_event_ref=f"fixture:{mock_scenario.value}",
        safety_counters=adapter_safety_counters(),
    )


def _build_offline_plan(
    action: str,
    intent_id: str,
    adapter_mode: AdapterMode | None,
    *,
    observed_at: datetime,
    **metadata: object,
) -> dict[str, object]:
    return {
        "action": action,
        "intent_id": intent_id,
        "adapter_mode": adapter_mode.value if adapter_mode is not None else "",
        "broker_api_call": False,
        "real_order": False,
        "real_cancel": False,
        "observed_at": observed_at.isoformat(),
        **metadata,
    }


def _coerce_adapter_mode(value: AdapterMode | str | None) -> AdapterMode | None:
    if isinstance(value, AdapterMode):
        return value
    try:
        return AdapterMode(str(value))
    except ValueError:
        return None


def _coerce_mock_scenario(value: MockBrokerScenario | str) -> MockBrokerScenario:
    if isinstance(value, MockBrokerScenario):
        return value
    try:
        return MockBrokerScenario(str(value))
    except ValueError:
        return MockBrokerScenario.UNKNOWN


def _adapter_mode_value(value: AdapterMode | str) -> str:
    return value.value if isinstance(value, AdapterMode) else str(value)


def _policy_value(value: str | Enum) -> str:
    return str(value.value if isinstance(value, Enum) else value)


def _intent_value(
    intent: AdapterRequest | Mapping[str, object],
    key: str,
    default: object,
) -> object:
    if isinstance(intent, Mapping):
        return intent.get(key, default)
    return getattr(intent, key, default)


def _int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _observed_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _stage_gate_value(gate_result: object, key: str) -> str:
    if isinstance(gate_result, Mapping):
        value = gate_result.get(key, "")
    else:
        value = getattr(gate_result, key, "")
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
