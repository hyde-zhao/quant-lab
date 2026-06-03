from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from trading.qmt_gateway_config import (
    GATEWAY_REQUIRED_REDACTION_FIELDS,
    GatewayAllowlist,
    GatewayBindConfig,
    GatewayConfig,
    GatewayFirewallPolicy,
    HeartbeatPolicy,
    RedactionPolicy,
    build_gateway_config,
    collect_gateway_safety_counters,
    validate_gateway_security,
)
from trading.qmt_gateway_service import (
    HEARTBEAT_FAILED_REASON,
    SERVICE_START_FORBIDDEN_REASON,
    GatewayLifecycleState,
    build_gateway_command_spec,
    build_heartbeat_summary,
    plan_gateway_lifecycle,
    service_start_forbidden,
)


S04_SOURCE_PATHS = (
    Path("trading/qmt_gateway_config.py"),
    Path("trading/qmt_gateway_service.py"),
)

REQUIRED_ZERO_COUNTERS = {
    "dependency_change",
    "service_start",
    "service_start_count",
    "service_bind",
    "port_bind_count",
    "credential_read",
    "qmt_operation",
    "qmt_api_call",
    "xtquant_import",
    "real_order",
    "real_cancel",
    "account_query",
    "account_write",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "current_pointer_publish",
    "simulation_or_live_run",
    "http_client_call",
    "gateway_socket_open",
    "public_exposure_allowed_count",
}


def _safe_config(**overrides: object) -> GatewayConfig:
    source = {
        "config_path": "<config-path>",
        "bind": {
            "bind_host": "127.0.0.1",
            "port": 18765,
            "public_exposure_allowed": False,
            "wsl_access_host": "<windows-host>",
        },
        "firewall": {
            "required": True,
            "enabled": True,
            "inbound_rule_present": True,
            "rule_name": "qmt-gateway-local-only",
        },
        "allowlist": {"sources": ("127.0.0.1/32", "192.168.56.1/32")},
        "heartbeat": {
            "interval_seconds": 10,
            "stale_after_seconds": 30,
            "unhealthy_after_missed": 3,
        },
        "redaction": {"redacted_fields": GATEWAY_REQUIRED_REDACTION_FIELDS},
        "auth_mode": "pairing_hmac",
    }
    source.update(overrides)
    return build_gateway_config(source)


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def test_gateway_config_field_coverage_is_complete() -> None:
    config = _safe_config()
    validation = validate_gateway_security(config)
    command = build_gateway_command_spec(config)

    assert {field.name for field in fields(GatewayBindConfig)} == {
        "bind_host",
        "port",
        "public_exposure_allowed",
        "wsl_access_host",
    }
    assert {field.name for field in fields(GatewayFirewallPolicy)} == {
        "required",
        "enabled",
        "inbound_rule_present",
        "rule_name",
        "profile",
    }
    assert {field.name for field in fields(GatewayAllowlist)} == {
        "sources",
        "required",
        "description",
    }
    assert {field.name for field in fields(HeartbeatPolicy)} == {
        "interval_seconds",
        "stale_after_seconds",
        "unhealthy_after_missed",
        "expected_schema_version",
    }
    assert {field.name for field in fields(RedactionPolicy)} == {
        "redacted_fields",
        "required_fields",
        "redaction_status",
    }
    assert validation.accepted is True
    assert validation.status == "ready_to_start"
    assert command.config_path == "<config-path>"
    assert command.bind_host == "127.0.0.1"
    assert command.port == 18765
    assert command.auth_mode == "pairing_hmac"
    assert command.service_start_allowed is False
    assert command.port_bind_allowed is False
    _assert_zero_counters(validation.counters)


def test_public_exposure_defaults_to_blocked_and_allowed_count_is_zero() -> None:
    for host in ("0.0.0.0", "8.8.8.8"):
        config = _safe_config(bind={"bind_host": host, "port": 18765})
        validation = validate_gateway_security(config)

        assert validation.accepted is False
        assert validation.primary_reason == "public_bind_forbidden"
        assert validation.public_exposure_allowed_count == 0
        _assert_zero_counters(validation.counters)

    explicit = _safe_config(
        bind={
            "bind_host": "127.0.0.1",
            "port": 18765,
            "public_exposure_allowed": True,
        }
    )
    explicit_validation = validate_gateway_security(explicit)
    assert "public_exposure_not_authorized" in explicit_validation.reasons
    assert explicit_validation.public_exposure_allowed_count == 0


def test_allowlist_firewall_and_redaction_fail_closed() -> None:
    allowlist_validation = validate_gateway_security(
        _safe_config(allowlist={"sources": ()})
    )
    assert allowlist_validation.accepted is False
    assert allowlist_validation.primary_reason == "allowlist_missing"

    firewall_validation = validate_gateway_security(
        _safe_config(firewall={"required": True, "enabled": False})
    )
    assert firewall_validation.accepted is False
    assert firewall_validation.primary_reason == "firewall_policy_missing"

    redaction_validation = validate_gateway_security(
        _safe_config(redaction={"redacted_fields": ("token", "session")})
    )
    assert redaction_validation.accepted is False
    assert "redaction_policy_incomplete" in redaction_validation.reasons
    assert "account" in redaction_validation.missing_redaction_fields


def test_start_transition_returns_forbidden_and_never_updates_counters() -> None:
    config = _safe_config()
    plan = plan_gateway_lifecycle(config, requested_transition="start")
    guarded = service_start_forbidden(config)

    for current in (plan, guarded):
        assert current.allowed is False
        assert current.blocked is True
        assert current.blocked_reason == SERVICE_START_FORBIDDEN_REASON
        assert current.next_state is GatewayLifecycleState.CONFIGURED
        assert current.command_spec is not None
        assert current.command_spec.dry_run_only is True
        _assert_zero_counters(current.counters)
        assert current.counters["service_start_count"] == 0
        assert current.counters["port_bind_count"] == 0
        assert current.counters["qmt_api_call"] == 0


def test_safe_config_produces_ready_to_start_plan_only() -> None:
    plan = plan_gateway_lifecycle(_safe_config(), requested_transition="plan")

    assert plan.allowed is True
    assert plan.blocked is False
    assert plan.next_state is GatewayLifecycleState.READY_TO_START
    assert plan.actions == ("validate_config", "publish_plan_only")
    assert plan.command_spec is not None
    assert plan.command_spec.arguments[:4] == (
        "qmt-gateway",
        "serve",
        "--config",
        "<config-path>",
    )
    _assert_zero_counters(plan.counters)


def test_heartbeat_unhealthy_fails_closed_without_qmt_api_call() -> None:
    summary = build_heartbeat_summary(
        {
            "healthy": False,
            "last_seen_at": "2026-05-30T20:00:00+08:00",
            "latency_ms": 999,
            "schema_version": "fixture-heartbeat-v1",
            "gateway_version": "fixture-gateway",
        }
    )

    assert summary.healthy is False
    assert summary.state is GatewayLifecycleState.UNHEALTHY
    assert summary.blocked_reason == HEARTBEAT_FAILED_REASON
    assert summary.redaction_status == "redacted"
    _assert_zero_counters(summary.counters)
    assert summary.counters["qmt_api_call"] == 0


def test_install_doc_uses_placeholders_and_contains_no_sensitive_literals() -> None:
    content = Path("docs/QMT-GATEWAY-INSTALL.md").read_text(encoding="utf-8")
    lowered = content.lower()

    for placeholder in ("<windows-host>", "<port>", "<config-path>"):
        assert placeholder in content
    for forbidden in ("secret", "token", "account", "password", ".env"):
        assert forbidden not in lowered
    assert "不得启动真实服务" in content
    assert "不得写入真实凭据" in content


def test_gateway_sources_do_not_import_service_network_or_qmt_runtime_modules() -> None:
    forbidden_import_roots = {
        "fastapi",
        "uvicorn",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "subprocess",
        "xtquant",
        "xttrader",
        "xtdata",
    }
    imports: list[str] = []
    for path in S04_SOURCE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)
    _assert_zero_counters(collect_gateway_safety_counters())


def test_forbidden_operation_counters_are_all_zero() -> None:
    counters = collect_gateway_safety_counters()

    _assert_zero_counters(counters)
    assert counters["dependency_change"] == 0
    assert counters["credential_read"] == 0
    assert counters["qmt_api_call"] == 0
    assert counters["real_order"] == 0
    assert counters["real_cancel"] == 0
    assert counters["account_query"] == 0
    assert counters["provider_fetch"] == 0
    assert counters["lake_write"] == 0
    assert counters["publish"] == 0
    assert counters["simulation_or_live_run"] == 0
