from __future__ import annotations

import socket

from trading.qmt_gateway_config import build_gateway_change_plan, validate_gateway_change_plan
from trading.qmt_gateway_service import GatewayService
from trading.runner_control_contracts import AuthorizationRecord


def _account_auth() -> AuthorizationRecord:
    return AuthorizationRecord(
        scope="account_readonly",
        status="authorized",
        authorization_ref="auth:account-readonly",
    )


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
