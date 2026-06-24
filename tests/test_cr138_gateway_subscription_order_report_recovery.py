from __future__ import annotations

from trading.qmt_gateway_contracts import ExecutionReport, GatewayCommand, GatewayHealth
from trading.qmt_gateway_gates import gate_market_subscription, hard_reject_gateway_command
from trading.qmt_gateway_service import GatewayService
from trading.runner_control_contracts import AuthorizationRecord


def _market_auth() -> AuthorizationRecord:
    return AuthorizationRecord(scope="market_readonly", status="authorized", authorization_ref="auth:market")


def _order_auth() -> AuthorizationRecord:
    return AuthorizationRecord(scope="submit_cancel", status="authorized", authorization_ref="auth:submit")


def test_market_subscription_blocks_without_scope_and_never_calls_adapter() -> None:
    blocked = gate_market_subscription(symbols=("000001.SZ",), period="1m")
    allowed = gate_market_subscription(symbols=("000001.SZ",), period="1m", auth=_market_auth())

    assert blocked.blocked is True
    assert blocked.blocked_reason == "authorization_missing"
    assert blocked.adapter_calls == 0
    assert allowed.state == "registered_fixture_only"
    assert allowed.adapter_calls == 0


def test_gateway_command_hard_rejects_submit_cancel_without_authorization() -> None:
    command = GatewayCommand(
        command_id="cmd-submit",
        command_type="submit",
        scope="submit_cancel",
        order_intent_id="intent:redacted",
    )

    rejected = hard_reject_gateway_command(command)
    accepted = hard_reject_gateway_command(command, auth=_order_auth())

    assert rejected.hard_rejected is True
    assert rejected.blocked_reason == "authorization_missing"
    assert rejected.local_reject is True
    assert rejected.broker_reject is False
    assert rejected.adapter_calls == 0
    assert accepted.status == "accepted_for_fixture_only"
    assert accepted.adapter_calls == 0


def test_gateway_service_subscription_events_are_rest_pull_fixture_only() -> None:
    service = GatewayService()
    subscription = service.register_subscription(
        symbols=("000001.SZ",),
        period="1m",
        auth=_market_auth(),
    )
    events = service.pull_subscription_events(subscription.subscription_id)

    assert subscription.state == "registered_fixture_only"
    assert len(events) == 1
    assert events[0].payload_ref == "market-event-ref:redacted"


def test_execution_report_unknown_requires_manual_takeover_and_recovery_is_manual_only() -> None:
    service = GatewayService()
    report = service.ingest_execution_report(ExecutionReport(report_id="report-1", state="unknown"))
    plan = service.build_recovery_plan(GatewayHealth(status="degraded", degraded_reason="heartbeat_stale"))

    assert report.manual_takeover_required is True
    assert report.broker_order_ref == "<redacted-broker-order-ref>"
    assert plan.manual_action == "manual_review"
    assert plan.auto_retry_allowed is False
    assert plan.auto_unlock_allowed is False
