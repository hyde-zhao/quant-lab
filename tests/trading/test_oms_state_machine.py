from __future__ import annotations

from datetime import UTC, datetime

import pytest

from market_data.contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_RAW,
)
from trading.oms import (
    BROKER_EVENT_TO_OMS_EVENT,
    OMS_STATE_VALUES,
    OmsErrorCode,
    OmsEvent,
    OmsResultStatus,
    OrderIntent,
    OrderState,
    apply_broker_event,
    apply_risk_result,
    apply_state_event,
    build_idempotency_key,
    create_order_intent,
    freeze_orders,
    is_success_state,
    oms_safety_counters,
)
from trading.qmt_adapter import BrokerEventType, BrokerOrderEvent, MockBrokerScenario
from trading.qmt_environment import AdapterMode, assert_no_real_qmt_operations


NOW = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)


def _target_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 200,
        "target_trade_date": "2026-05-29",
        "signal_date": "2026-05-28",
    }
    row.update(overrides)
    return row


def _policy(**overrides: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "research_adjustment_policy": ADJUSTMENT_POLICY_QFQ,
        "execution_price_policy": ADJUSTMENT_POLICY_RAW,
    }
    metadata.update(overrides)
    return metadata


def _run_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "strategy_id": "strategy-alpha",
        "run_id": "run-cr015-s03",
        "risk_profile_id": "risk-profile-shadow",
    }
    context.update(overrides)
    return context


def _intent() -> OrderIntent:
    result = create_order_intent(_target_row(), _policy(), _run_context(), now=NOW)
    assert result.ok
    assert result.intent is not None
    return result.intent


def _risk_passed_intent() -> OrderIntent:
    result = apply_risk_result(_intent(), {"status": "pass", "reason": "fixture"}, now=NOW)
    assert result.ok
    assert result.intent is not None
    return result.intent


def _accepted_intent() -> OrderIntent:
    result = apply_broker_event(
        _risk_passed_intent(),
        _broker_event(BrokerEventType.ACCEPTED),
        now=NOW,
    )
    assert result.ok
    assert result.intent is not None
    return result.intent


def _broker_event(
    event_type: BrokerEventType,
    *,
    filled_quantity: int = 0,
    remaining_quantity: int = 200,
    reason: str = "",
) -> BrokerOrderEvent:
    return BrokerOrderEvent(
        broker_event_type=event_type,
        intent_id="intent-cr015-s03",
        broker_order_ref=f"mock-intent-cr015-s03-{event_type.value}",
        adapter_mode=AdapterMode.MOCK,
        filled_quantity=filled_quantity,
        remaining_quantity=remaining_quantity,
        reason=reason or f"fixture_{event_type.value}",
        observed_at=NOW,
    )


def _assert_safety_counters_zero(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    expected = {
        "qmt_api_call": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "credential_read": 0,
        "real_broker_lake_write": 0,
        "real_lake_write": 0,
        "provider_fetch": 0,
        "publish": 0,
        "dependency_change": 0,
        "unknown_success_count": 0,
        "timeout_success_count": 0,
    }
    assert {key: current.get(key, 0) for key in expected} == expected
    assert assert_no_real_qmt_operations(
        {
            key: value
            for key, value in current.items()
            if key
            in {
                "real_qmt_process_invocation",
                "qmt_api_call",
                "real_order",
                "real_cancel",
                "account_query",
                "account_write",
                "credential_read",
                "dependency_change",
                "real_broker_lake_write",
            }
        }
    )


def test_create_order_intent_requires_policy_and_raw_execution() -> None:
    created = create_order_intent(_target_row(), _policy(), _run_context(), now=NOW)
    assert created.status is OmsResultStatus.CREATED
    assert created.intent is not None
    assert created.intent.state is OrderState.CREATED
    assert created.intent.research_adjustment_policy == ADJUSTMENT_POLICY_QFQ
    assert created.intent.execution_price_policy == ADJUSTMENT_POLICY_RAW
    assert created.intent.remaining_qty == 200
    _assert_safety_counters_zero(created.safety_counters)

    missing_research = create_order_intent(
        _target_row(),
        {"execution_price_policy": ADJUSTMENT_POLICY_RAW},
        _run_context(),
    )
    assert missing_research.blocked
    assert missing_research.intent is None
    assert missing_research.error is not None
    assert (
        missing_research.error.error_code
        is OmsErrorCode.MISSING_RESEARCH_ADJUSTMENT_POLICY
    )

    missing_execution = create_order_intent(
        _target_row(),
        {"research_adjustment_policy": ADJUSTMENT_POLICY_QFQ},
        _run_context(),
    )
    assert missing_execution.blocked
    assert missing_execution.error is not None
    assert missing_execution.error.error_code is OmsErrorCode.MISSING_EXECUTION_PRICE_POLICY

    non_raw = create_order_intent(
        _target_row(),
        _policy(execution_price_policy=ADJUSTMENT_POLICY_HFQ),
        _run_context(),
    )
    assert non_raw.blocked
    assert non_raw.error is not None
    assert non_raw.error.error_code is OmsErrorCode.NON_RAW_EXECUTION_PRICE_BLOCKED
    _assert_safety_counters_zero(non_raw.safety_counters)


def test_idempotency_key_is_stable_for_same_strategy_run_symbol_side_date_qty() -> None:
    first = create_order_intent(_target_row(), _policy(), _run_context(), now=NOW)
    second = create_order_intent(
        _target_row(signal_date="2026-05-27"),
        _policy(research_adjustment_policy=ADJUSTMENT_POLICY_RAW),
        _run_context(risk_profile_id="other-risk-profile"),
        now=datetime(2026, 5, 28, 10, 0, tzinfo=UTC),
    )
    changed_qty = create_order_intent(
        _target_row(target_qty=300),
        _policy(),
        _run_context(),
        now=NOW,
    )

    assert first.intent is not None
    assert second.intent is not None
    assert changed_qty.intent is not None
    assert first.intent.idempotency_key == second.intent.idempotency_key
    assert first.intent.order_intent_id == second.intent.order_intent_id
    assert first.intent.idempotency_key != changed_qty.intent.idempotency_key
    assert first.intent.idempotency_key == build_idempotency_key(
        {
            "strategy_id": "strategy-alpha",
            "run_id": "run-cr015-s03",
            "symbol": "000001.SZ",
            "side": "buy",
            "target_trade_date": "2026-05-29",
            "target_qty": 200,
        }
    )


def test_state_machine_exposes_required_state_set_and_adapter_mapping() -> None:
    assert set(OMS_STATE_VALUES) == {
        "created",
        "risk_passed",
        "blocked",
        "accepted",
        "partially_filled",
        "filled",
        "cancel_pending",
        "canceled",
        "rejected",
        "failed",
        "timeout",
        "unknown",
        "manual_review",
        "frozen",
    }
    assert BROKER_EVENT_TO_OMS_EVENT[BrokerEventType.ACCEPTED.value] is (
        OmsEvent.ADAPTER_ACCEPTED
    )
    assert BROKER_EVENT_TO_OMS_EVENT[BrokerEventType.CANCEL_CONFIRMED.value] is (
        OmsEvent.CANCEL_CONFIRMED
    )
    assert BROKER_EVENT_TO_OMS_EVENT[BrokerEventType.CANCEL_FAILED.value] is (
        OmsEvent.CANCEL_FAILED
    )
    assert {MockBrokerScenario.TIMEOUT.value, MockBrokerScenario.UNKNOWN.value} <= {
        BrokerEventType.TIMEOUT.value,
        BrokerEventType.UNKNOWN.value,
    }


def test_risk_and_broker_events_cover_accepted_partial_and_filled_flow() -> None:
    risk_pass = apply_risk_result(_intent(), {"status": "pass"}, now=NOW)
    assert risk_pass.ok
    assert risk_pass.intent is not None
    assert risk_pass.intent.state is OrderState.RISK_PASSED

    accepted = apply_broker_event(
        risk_pass.intent,
        _broker_event(BrokerEventType.ACCEPTED),
        now=NOW,
    )
    assert accepted.ok
    assert accepted.intent is not None
    assert accepted.intent.state is OrderState.ACCEPTED

    partial = apply_broker_event(
        accepted.intent,
        _broker_event(
            BrokerEventType.PARTIAL,
            filled_quantity=100,
            remaining_quantity=100,
        ),
        now=NOW,
    )
    assert partial.ok
    assert partial.intent is not None
    assert partial.intent.state is OrderState.PARTIALLY_FILLED
    assert partial.intent.filled_qty == 100
    assert partial.intent.remaining_qty == 100

    filled = apply_broker_event(
        partial.intent,
        _broker_event(
            BrokerEventType.FILLED,
            filled_quantity=200,
            remaining_quantity=0,
        ),
        now=NOW,
    )
    assert filled.ok
    assert filled.intent is not None
    assert filled.intent.state is OrderState.FILLED
    assert filled.intent.filled_qty == 200
    assert filled.intent.remaining_qty == 0
    assert is_success_state(filled.intent.state)


def test_illegal_transition_returns_structured_error_without_state_change() -> None:
    filled = apply_broker_event(
        _accepted_intent(),
        _broker_event(
            BrokerEventType.FILLED,
            filled_quantity=200,
            remaining_quantity=0,
        ),
        now=NOW,
    )
    assert filled.intent is not None

    illegal = apply_broker_event(
        filled.intent,
        _broker_event(
            BrokerEventType.PARTIAL,
            filled_quantity=50,
            remaining_quantity=150,
        ),
        now=NOW,
    )
    assert illegal.status is OmsResultStatus.ERROR
    assert illegal.intent is filled.intent
    assert illegal.error is not None
    assert illegal.error.error_code is OmsErrorCode.ILLEGAL_TRANSITION
    assert illegal.intent.state is OrderState.FILLED
    assert illegal.intent.filled_qty == 200


@pytest.mark.parametrize(
    ("event_type", "expected_state", "counter_key"),
    [
        (BrokerEventType.UNKNOWN, OrderState.UNKNOWN, "unknown_success_count"),
        (BrokerEventType.TIMEOUT, OrderState.TIMEOUT, "timeout_success_count"),
    ],
)
def test_unknown_and_timeout_do_not_become_success_and_require_manual_review(
    event_type: BrokerEventType,
    expected_state: OrderState,
    counter_key: str,
) -> None:
    result = apply_broker_event(_risk_passed_intent(), _broker_event(event_type), now=NOW)
    assert result.ok
    assert result.intent is not None
    assert result.transition_event is not None
    assert result.intent.state is expected_state
    assert result.intent.manual_review_required is True
    assert result.transition_event.manual_review_required is True
    assert not is_success_state(result.intent.state)
    assert result.safety_counters[counter_key] == 0

    review = apply_state_event(result.intent, OmsEvent.REVIEW_REQUIRED, now=NOW)
    assert review.ok
    assert review.intent is not None
    assert review.intent.state is OrderState.MANUAL_REVIEW
    assert review.intent.manual_review_required is True


def test_cancel_confirmed_and_cancel_failed_paths_do_not_call_real_cancel() -> None:
    cancel_pending = apply_state_event(
        _accepted_intent(),
        OmsEvent.CANCEL_REQUESTED,
        reason="operator_cancel",
        now=NOW,
    )
    assert cancel_pending.ok
    assert cancel_pending.intent is not None
    assert cancel_pending.intent.state is OrderState.CANCEL_PENDING

    canceled = apply_broker_event(
        cancel_pending.intent,
        _broker_event(BrokerEventType.CANCEL_CONFIRMED),
        now=NOW,
    )
    assert canceled.ok
    assert canceled.intent is not None
    assert canceled.intent.state is OrderState.CANCELED
    assert is_success_state(canceled.intent.state)
    _assert_safety_counters_zero(canceled.safety_counters)

    failed_pending = apply_state_event(
        _accepted_intent(),
        OmsEvent.CANCEL_REQUESTED,
        reason="operator_cancel",
        now=NOW,
    )
    assert failed_pending.intent is not None
    cancel_failed = apply_broker_event(
        failed_pending.intent,
        _broker_event(BrokerEventType.CANCEL_FAILED),
        now=NOW,
    )
    assert cancel_failed.ok
    assert cancel_failed.intent is not None
    assert cancel_failed.intent.state is OrderState.MANUAL_REVIEW
    assert cancel_failed.intent.manual_review_required is True
    assert not is_success_state(cancel_failed.intent.state)
    assert cancel_failed.safety_counters["real_cancel"] == 0
    _assert_safety_counters_zero(cancel_failed.safety_counters)


def test_risk_blocked_and_failed_state_are_explicit_non_success_states() -> None:
    blocked = apply_risk_result(_intent(), {"status": "blocked", "reason": "cash"}, now=NOW)
    assert blocked.ok
    assert blocked.intent is not None
    assert blocked.intent.state is OrderState.BLOCKED
    assert not is_success_state(blocked.intent.state)

    failed = apply_state_event(_accepted_intent(), OmsEvent.MARK_FAILED, now=NOW)
    assert failed.ok
    assert failed.intent is not None
    assert failed.intent.state is OrderState.FAILED
    assert not is_success_state(failed.intent.state)


def test_freeze_orders_only_updates_local_state_and_incident_ref() -> None:
    created = _intent()
    accepted = _accepted_intent()
    filled = apply_broker_event(
        _accepted_intent(),
        _broker_event(BrokerEventType.FILLED, filled_quantity=200, remaining_quantity=0),
        now=NOW,
    )
    assert filled.intent is not None

    result = freeze_orders(
        [created, accepted, filled.intent],
        "kill_switch_fixture",
        incident_ref="incident-cr015-s03-fixture",
        now=NOW,
    )
    assert result.incident_ref == "incident-cr015-s03-fixture"
    assert [intent.state for intent in result.frozen_intents] == [
        OrderState.FROZEN,
        OrderState.FROZEN,
        OrderState.FILLED,
    ]
    assert all(
        intent.incident_ref == "incident-cr015-s03-fixture"
        for intent in result.frozen_intents
    )
    assert {event.event for event in result.transition_events} == {OmsEvent.FREEZE}
    assert result.safety_counters["real_cancel"] == 0
    _assert_safety_counters_zero(result.safety_counters)


def test_oms_safety_counters_are_zero_for_forbidden_operations() -> None:
    _assert_safety_counters_zero(oms_safety_counters())
