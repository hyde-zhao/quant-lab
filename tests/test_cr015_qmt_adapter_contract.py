from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from market_data.contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
)
from trading.qmt_adapter import (
    AdapterBlockedReason,
    AdapterRequest,
    AdapterResultStatus,
    BrokerEventType,
    CancelOrderRequest,
    MockBrokerScenario,
    adapter_safety_counters,
    build_mock_broker_event,
    cancel_order,
    submit_intent,
)
from trading.qmt_environment import (
    AdapterMode,
    assert_no_real_qmt_operations,
    scan_forbidden_broker_imports,
)
from trading.qmt_transport import (
    ADAPTER_FACING_TRANSPORT_ERROR_CODES,
    ADAPTER_PAYLOAD_METADATA_FIELDS,
    TransportErrorCode,
    build_transport_payload,
)


def _valid_metadata(now: datetime | None = None) -> dict[str, str]:
    current = now or datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    return {
        "run_id": "run-cr015-s02-fixture",
        "strategy_id": "strategy-alpha",
        "payload_id": "payload-s02-001",
        "payload_checksum": "sha256:fixture-checksum",
        "signature_ref": "signature-ref:fixture",
        "created_at": current.isoformat(),
        "expires_at": (current + timedelta(minutes=5)).isoformat(),
        "node_role": "trading",
        "adapter_mode": "mock",
    }


def _request(
    mode: AdapterMode | str = AdapterMode.MOCK,
    *,
    policy: str = "raw",
    risk_status: str = "pass",
    scenario: MockBrokerScenario | str = MockBrokerScenario.ACCEPTED,
) -> AdapterRequest:
    return AdapterRequest(
        intent_id="intent-cr015-s02-001",
        adapter_mode=mode,
        execution_price_policy=policy,
        risk_status=risk_status,
        side="buy",
        symbol="000001.SZ",
        quantity=200,
        order_price=10.25,
        strategy_id="strategy-alpha",
        run_id="run-cr015-s02-fixture",
        mock_scenario=scenario,
        evidence_ref="fixture:evidence",
    )


def _assert_safety_counters_zero(counters: dict[str, int] | object) -> None:
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


def test_cr015_allowed_modes_do_not_touch_real_api() -> None:
    shadow = submit_intent(_request(AdapterMode.SHADOW))
    assert shadow.status is AdapterResultStatus.SHADOW_ACCEPTED
    assert shadow.broker_event is None
    assert shadow.dry_run_plan["broker_api_call"] is False
    _assert_safety_counters_zero(shadow.safety_counters)

    dry_run = submit_intent(_request("dry_run"))
    assert dry_run.status is AdapterResultStatus.DRY_RUN_PLANNED
    assert dry_run.dry_run_plan["real_order"] is False
    _assert_safety_counters_zero(dry_run.safety_counters)

    mock = submit_intent(_request("mock", scenario=MockBrokerScenario.FILLED))
    assert mock.status is AdapterResultStatus.MOCK_EVENT_GENERATED
    assert mock.broker_event is not None
    assert mock.broker_event.broker_event_type is BrokerEventType.FILLED
    assert mock.broker_event.broker_order_ref == "mock-intent-cr015-s02-001-filled"
    _assert_safety_counters_zero(mock.safety_counters)
    _assert_safety_counters_zero(mock.broker_event.safety_counters)


@pytest.mark.parametrize("mode", ["simulation", "live_readonly", "small_live"])
def test_cr015_real_adapter_modes_are_blocked(mode: str) -> None:
    result = submit_intent(_request(mode))
    assert result.status is AdapterResultStatus.BLOCKED
    assert result.blocked_reason is AdapterBlockedReason.MODE_NOT_AUTHORIZED
    assert result.detail_code == mode
    assert result.safety_counters["adapter_calls"] == 0
    _assert_safety_counters_zero(result.safety_counters)


@pytest.mark.parametrize(
    "policy",
    [
        ADJUSTMENT_POLICY_QFQ,
        ADJUSTMENT_POLICY_HFQ,
        ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
        "close_proxy",
    ],
)
def test_non_raw_execution_policy_is_blocked_and_adjusted_pass_count_is_zero(
    policy: str,
) -> None:
    result = submit_intent(_request(policy=policy))
    assert result.status is AdapterResultStatus.BLOCKED
    assert result.blocked_reason is AdapterBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED
    assert result.detail_code == policy
    assert result.safety_counters["adjusted_execution_pass_count"] == 0
    assert result.safety_counters["adapter_calls"] == 0
    _assert_safety_counters_zero(result.safety_counters)


def test_risk_not_passed_blocks_before_adapter_call() -> None:
    result = submit_intent(_request(risk_status="blocked"))
    assert result.status is AdapterResultStatus.BLOCKED
    assert result.blocked_reason is AdapterBlockedReason.RISK_NOT_PASSED
    assert result.safety_counters["adapter_calls"] == 0
    assert result.broker_event is None
    _assert_safety_counters_zero(result.safety_counters)


def test_mock_broker_event_factory_covers_required_scenarios() -> None:
    events = {
        scenario.value: build_mock_broker_event(scenario, _request(scenario=scenario))
        for scenario in MockBrokerScenario
    }
    assert set(events) == {
        "accepted",
        "partial",
        "filled",
        "rejected",
        "timeout",
        "unknown",
    }
    assert {event.broker_event_type.value for event in events.values()} == {
        "accepted",
        "partial",
        "filled",
        "rejected",
        "timeout",
        "unknown",
    }
    assert events["partial"].filled_quantity == 100
    assert events["partial"].remaining_quantity == 100
    assert events["filled"].filled_quantity == 200
    assert events["filled"].remaining_quantity == 0
    assert all(event.broker_order_ref.startswith("mock-") for event in events.values())
    for event in events.values():
        _assert_safety_counters_zero(event.safety_counters)


def test_cancel_order_is_dry_run_or_blocked_without_real_cancel() -> None:
    planned = cancel_order(
        CancelOrderRequest(
            intent_id="intent-cr015-s02-001",
            broker_order_ref="mock-intent-cr015-s02-001-accepted",
            adapter_mode="dry_run",
            current_oms_state="accepted",
            cancel_reason="fixture-timeout",
        )
    )
    assert planned.status is AdapterResultStatus.DRY_RUN_PLANNED
    assert planned.dry_run_plan["action"] == "cancel"
    assert planned.dry_run_plan["real_cancel"] is False
    _assert_safety_counters_zero(planned.safety_counters)

    blocked = cancel_order(
        CancelOrderRequest(
            intent_id="intent-cr015-s02-001",
            broker_order_ref="broker-real-ref-not-used",
            adapter_mode="simulation",
        )
    )
    assert blocked.status is AdapterResultStatus.BLOCKED
    assert blocked.blocked_reason is AdapterBlockedReason.MODE_NOT_AUTHORIZED
    assert blocked.safety_counters["real_cancel"] == 0
    _assert_safety_counters_zero(blocked.safety_counters)


def test_transport_payload_integration_keeps_s01_contract_and_adapter_metadata_boundary(
) -> None:
    now = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    build_result = build_transport_payload(_valid_metadata(now), now=now)
    assert build_result.accepted is True
    assert build_result.payload is not None

    request = AdapterRequest(
        intent_id="intent-cr015-s02-transport",
        adapter_mode=AdapterMode.MOCK,
        execution_price_policy="raw",
        risk_status="pass",
        quantity=100,
        transport_payload=build_result.payload,
    )
    result = submit_intent(request, now=now)
    assert result.status is AdapterResultStatus.MOCK_EVENT_GENERATED
    _assert_safety_counters_zero(result.safety_counters)

    assert {
        "intent_id",
        "risk_status",
        "execution_price_policy",
        "broker_event_type",
    } <= ADAPTER_PAYLOAD_METADATA_FIELDS
    assert (
        TransportErrorCode.MODE_NOT_AUTHORIZED
        in ADAPTER_FACING_TRANSPORT_ERROR_CODES
    )


def test_qmt_adapter_source_has_no_forbidden_broker_import_or_call() -> None:
    scan = scan_forbidden_broker_imports([Path("trading/qmt_adapter.py")])
    assert scan.passed is True
    assert scan.violation_count == 0
    _assert_safety_counters_zero(scan.counters)


def test_cr015_s02_forbidden_real_operation_counters_remain_zero() -> None:
    _assert_safety_counters_zero(adapter_safety_counters())
