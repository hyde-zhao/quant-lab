from __future__ import annotations

import ast
import socket
from dataclasses import fields
from pathlib import Path

from trading.qmt_gateway_contracts import (
    CapabilitySnapshot,
    ExecutionReport,
    GatewayCommand,
    GatewayHealth,
    RestRouteSpec,
)
from trading.qmt_gateway_config import build_gateway_change_plan, validate_gateway_change_plan
from trading.qmt_gateway_gates import gate_market_subscription, hard_reject_gateway_command
from trading.qmt_gateway_service import GatewayService
from trading.runner_control_contracts import (
    AuditRecord,
    AuthorizationRecord,
    BlockedResult,
    ControlResultStatus,
    NoRealOperationCounters,
    collect_no_real_operation_counters,
    new_audit_record,
    require_scope,
    validate_contract_ids,
)


PROJECT_ROOT = Path(__file__).parents[2]


def _account_auth() -> AuthorizationRecord:
    return AuthorizationRecord(
        scope="account_readonly",
        status="authorized",
        authorization_ref="auth:account-readonly",
    )


def _market_auth() -> AuthorizationRecord:
    return AuthorizationRecord(scope="market_readonly", status="authorized", authorization_ref="auth:market")


def _order_auth() -> AuthorizationRecord:
    return AuthorizationRecord(scope="submit_cancel", status="authorized", authorization_ref="auth:submit")


def test_gateway_service_route_registry_is_rest_only_and_p0_groups_present() -> None:
    service = GatewayService()
    routes = service.route_registry()
    capabilities = service.get_capabilities()
    route_ids = {route.endpoint_id for route in routes}

    assert capabilities.protocols == ("REST",)
    assert capabilities.runtime_authorized is False
    assert {"health", "capabilities", "trading_calendar", "commission", "pnl"} <= route_ids
    assert {"subscription", "gateway_command", "execution_report", "recovery_plan", "change_plan"} <= route_ids
    assert all(route.runtime_authorized is False for route in routes)


def test_health_does_not_authorize_session_or_account_scope() -> None:
    service = GatewayService()
    health = service.get_health(request_id="req-1")
    blocked = service.get_session_status()
    allowed = service.get_session_status(auth=_account_auth())

    assert health.status == "healthy"
    assert health.runtime_authorized is False
    assert blocked.blocked is True
    assert blocked.blocked_reason == "authorization_missing"
    assert blocked.adapter_calls == 0
    assert allowed.session_state == "fixture_ready"
    assert allowed.account_label == "<redacted-account-ref>"


def test_gateway_change_plan_requires_rollback_and_never_allows_apply() -> None:
    rejected = build_gateway_change_plan("diff:fixture")
    ready = build_gateway_change_plan("diff:fixture", rollback_target="rollback:previous")
    validated = validate_gateway_change_plan(ready)

    assert rejected.blocked is True
    assert rejected.blocked_reason == "rollback_target_missing"
    assert ready.status == "dry_run_pass"
    assert ready.apply_allowed is False
    assert ready.restart_allowed is False
    assert validated.apply_allowed is False


def test_gateway_service_change_plan_wrapper_is_dry_run_only() -> None:
    service = GatewayService()
    plan = service.build_gateway_change_plan("diff:fixture", rollback_target="rollback:previous")

    assert plan.status == "dry_run_pass"
    assert plan.apply_allowed is False
    assert plan.restart_allowed is False


def test_gateway_service_instantiation_does_not_bind_port(monkeypatch) -> None:
    calls: list[object] = []

    def _blocked_bind(self: object, address: object) -> None:
        calls.append(address)
        raise AssertionError("GatewayService must not bind ports")

    monkeypatch.setattr(socket.socket, "bind", _blocked_bind)

    service = GatewayService()
    _ = service.get_health()

    assert calls == []


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


def test_cr138_shared_contract_fields_and_zero_counters() -> None:
    assert {field.name for field in fields(AuthorizationRecord)} >= {
        "scope",
        "status",
        "authorization_ref",
        "expires_at",
        "redaction_status",
    }
    assert {field.name for field in fields(AuditRecord)} >= {
        "audit_id",
        "request_id",
        "actor",
        "action",
        "scope",
        "result",
    }
    assert {field.name for field in fields(BlockedResult)} >= {
        "blocked_reason",
        "scope_required",
        "adapter_calls",
        "counters",
    }
    counters = collect_no_real_operation_counters(NoRealOperationCounters())
    assert counters["qmt_operation"] == 0
    assert counters["order_submit"] == 0
    assert counters["nas_access"] == 0
    assert counters["git_remote_write"] == 0


def test_require_scope_fails_closed_and_health_does_not_authorize_order_scope() -> None:
    health = GatewayHealth(status="healthy")
    result = require_scope("submit_cancel", AuthorizationRecord(scope="qmt:health", status="authorized"))

    assert health.healthy is True
    assert health.runtime_authorized is False
    assert result is not None
    assert result.blocked is True
    assert result.scope_required == "submit_cancel"
    assert result.adapter_calls == 0


def test_audit_identity_validation() -> None:
    audit = new_audit_record(
        actor="operator",
        action="preflight",
        scope="runner:control",
        result="blocked",
    )

    assert audit.audit_id.startswith("audit:")
    assert validate_contract_ids({"request_id": audit.request_id}) is None
    missing = validate_contract_ids({"payload_ref": "fixture"})
    assert missing is not None
    assert missing.blocked_reason == "missing_audit_identity"
    assert missing.status is ControlResultStatus.REJECTED


def test_gateway_contracts_are_rest_only_and_runtime_not_authorized() -> None:
    capabilities = CapabilitySnapshot()
    route = RestRouteSpec("health", "GET", "/health", "lifecycle")

    assert capabilities.protocols == ("REST",)
    assert {"SSE", "WebSocket", "gRPC", "FIX"} <= set(capabilities.deferred_protocols)
    assert capabilities.runtime_authorized is False
    assert route.runtime_authorized is False


def test_cr138_runner_and_gateway_contracts_do_not_import_xtquant() -> None:
    for relative in (
        "trading/runner_control_contracts.py",
        "trading/runner_control_plane.py",
        "trading/qmt_gateway_contracts.py",
        "trading/qmt_gateway_service.py",
    ):
        tree = ast.parse((PROJECT_ROOT / relative).read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
        assert "xtquant" not in imported_roots
