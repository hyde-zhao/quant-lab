from __future__ import annotations

from trading.qmt_gateway_service import GatewayService
from trading.runner_control_contracts import AuthorizationRecord


def _account_auth() -> AuthorizationRecord:
    return AuthorizationRecord(
        scope="account_readonly",
        status="authorized",
        authorization_ref="auth:account-readonly",
    )


def test_trading_calendar_uses_local_reference_and_never_infers_missing_days() -> None:
    service = GatewayService(calendar_source={"XSHG:2026-06": ["2026-06-24", "2026-06-25"]})

    available = service.query_trading_calendar("XSHG", "2026-06")
    missing = service.query_trading_calendar("XSHE", "2026-06")

    assert available.status == "available"
    assert available.source == "local_reference"
    assert available.trading_days == ("2026-06-24", "2026-06-25")
    assert missing.status == "unavailable"
    assert missing.trading_days == ()
    assert missing.unavailable_reason == "local_calendar_missing"


def test_commission_schedule_and_cost_estimate_are_source_tagged_not_broker_fact() -> None:
    service = GatewayService()

    schedule = service.query_commission_schedule(
        instrument_type="stock",
        configured_rate=0.0003,
        min_fee=5,
    )
    estimate = service.estimate_cost(
        order_intent_ref="intent:redacted",
        notional=10000,
        schedule=schedule,
    )

    assert schedule.source == "configured"
    assert estimate.source == "estimated"
    assert estimate.schedule_source == "configured"
    assert estimate.broker_fact is False
    assert estimate.estimated_fee == 5


def test_broker_confirmed_commission_requires_account_readonly_authorization() -> None:
    service = GatewayService()

    unauthorized = service.query_commission_schedule(
        instrument_type="stock",
        broker_confirmed=True,
    )
    authorized = service.query_commission_schedule(
        instrument_type="stock",
        broker_confirmed=True,
        auth=_account_auth(),
    )

    assert unauthorized.source == "configured"
    assert unauthorized.authorization_ref == ""
    assert authorized.source == "broker_confirmed"
    assert authorized.authorization_ref == "auth:account-readonly"


def test_pnl_query_blocks_without_account_auth_and_reports_unsupported_with_reason() -> None:
    service = GatewayService()

    blocked = service.query_pnl_snapshot(period="2026-06")
    unsupported = service.query_pnl_snapshot(period="2026-06", auth=_account_auth(), supported=False)
    available = service.query_pnl_snapshot(period="2026-06", auth=_account_auth())
    returns = service.query_return_summary(period="2026-06", pnl=available)

    assert blocked.blocked is True
    assert blocked.blocked_reason == "authorization_missing"
    assert blocked.adapter_calls == 0
    assert unsupported.status == "unavailable_with_reason"
    assert unsupported.blocked_reason == "unsupported_by_adapter"
    assert available.redaction_status == "redacted"
    assert "redacted" in available.realized_summary
    assert returns.source == "estimated"
