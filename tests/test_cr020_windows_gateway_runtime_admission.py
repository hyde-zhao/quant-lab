from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from trading.qmt_gateway_cli import (
    TYPER_DEPENDENCY_MISSING_REASON,
    GatewayTyperAdapterResult,
    build_gateway_cli_command_matrix,
    build_gateway_cli_result,
    probe_gateway_typer_adapter,
)
from trading.qmt_gateway_config import (
    GATEWAY_REQUIRED_REDACTION_FIELDS,
    GatewayRuntimeAdmissionConfig,
    GatewayRuntimeFlags,
    build_gateway_config,
    build_gateway_runtime_admission_config,
    build_gateway_runtime_flags,
    collect_gateway_runtime_counters,
    validate_gateway_security,
)
from trading.qmt_gateway_service import (
    GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION,
    IMPLEMENTATION_NOT_ALLOWED_REASON,
    PORT_BIND_FORBIDDEN_REASON,
    RUNTIME_AUTHORIZATION_MISSING_REASON,
    SERVICE_START_FORBIDDEN_REASON,
    GatewayRuntimeAdmissionStatus,
    build_gateway_runtime_diagnostics,
    build_gateway_runtime_health_summary,
    evaluate_gateway_runtime_admission,
    plan_gateway_runtime_action,
)


SOURCE_PATHS = (
    Path("trading/qmt_gateway_cli.py"),
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
    "public_bind_allowed_count",
}


def _safe_config(**overrides: object) -> dict[str, object]:
    source: dict[str, object] = {
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
    return source


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def test_runtime_flags_and_admission_config_fields_are_complete() -> None:
    flags = build_gateway_runtime_flags()
    config = build_gateway_runtime_admission_config(_safe_config())

    assert {field.name for field in fields(GatewayRuntimeFlags)} == {
        "implementation_allowed",
        "dependency_change_allowed",
        "service_start_allowed",
        "port_bind_allowed",
        "credential_read_allowed",
        "qmt_operation_allowed",
        "runtime_authorization_ref",
        "dry_run_only",
        "public_bind_allowed_count",
        "schema_version",
    }
    assert {field.name for field in fields(GatewayRuntimeAdmissionConfig)} == {
        "gateway",
        "flags",
        "counters",
        "schema_version",
    }
    assert flags.implementation_allowed is False
    assert flags.service_start_allowed is False
    assert flags.port_bind_allowed is False
    assert flags.credential_read_allowed is False
    assert flags.qmt_operation_allowed is False
    assert flags.public_bind_allowed_count == 0
    assert config.schema_version == GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION
    _assert_zero_counters(config.counters)


def test_default_runtime_admission_fails_closed_before_run_gate() -> None:
    decision = evaluate_gateway_runtime_admission(_safe_config(), requested_action="admission")

    assert decision.accepted is False
    assert decision.status is GatewayRuntimeAdmissionStatus.BLOCKED_PRE_CP5
    assert decision.blocked_reason == IMPLEMENTATION_NOT_ALLOWED_REASON
    assert decision.config_validation is not None
    assert decision.config_validation.accepted is True
    assert decision.command_spec is not None
    _assert_zero_counters(decision.counters)


def test_start_serve_and_bind_are_blocked_without_side_effect_counters() -> None:
    serve = plan_gateway_runtime_action("serve", _safe_config())
    bind = plan_gateway_runtime_action("bind", _safe_config())

    assert serve.accepted is False
    assert serve.blocked_reason == SERVICE_START_FORBIDDEN_REASON
    assert bind.accepted is False
    assert bind.blocked_reason == PORT_BIND_FORBIDDEN_REASON
    for decision in (serve, bind):
        _assert_zero_counters(decision.counters)
        assert decision.counters["service_start_count"] == 0
        assert decision.counters["port_bind_count"] == 0
        assert decision.counters["qmt_api_call"] == 0


def test_runtime_authorization_ref_is_required_after_gates_are_opened() -> None:
    flags = build_gateway_runtime_flags(
        {
            "implementation_allowed": True,
            "service_start_allowed": True,
            "port_bind_allowed": True,
        }
    )
    decision = plan_gateway_runtime_action("serve", _safe_config(), flags=flags)

    assert decision.accepted is False
    assert decision.status is GatewayRuntimeAdmissionStatus.BLOCKED_RUNTIME_AUTHORIZATION
    assert decision.blocked_reason == RUNTIME_AUTHORIZATION_MISSING_REASON
    _assert_zero_counters(decision.counters)


def test_public_bind_remains_blocked_and_public_bind_count_is_zero() -> None:
    config = build_gateway_config(
        _safe_config(bind={"bind_host": "0.0.0.0", "port": 18765})
    )
    validation = validate_gateway_security(config)
    decision = evaluate_gateway_runtime_admission(config)

    assert validation.accepted is False
    assert validation.primary_reason == "public_bind_forbidden"
    assert decision.status is GatewayRuntimeAdmissionStatus.BLOCKED_CONFIG
    assert decision.blocked_reason == "public_bind_forbidden"
    assert decision.counters["public_bind_allowed_count"] == 0
    _assert_zero_counters(decision.counters)


def test_cli_command_matrix_and_structured_result_are_static_contracts() -> None:
    matrix = build_gateway_cli_command_matrix()
    commands = {spec.command: spec for spec in matrix}
    result = build_gateway_cli_result("admission", _safe_config())

    assert set(commands) == {
        "admission",
        "plan",
        "serve",
        "stop",
        "health",
        "diagnostics",
    }
    assert commands["serve"].requires_runtime_authorization is True
    assert commands["health"].dry_run_only is True
    assert result["command"] == "admission"
    assert result["schema_version"] == GATEWAY_RUNTIME_ADMISSION_SCHEMA_VERSION
    _assert_zero_counters(result["counters"])


def test_typer_missing_fails_closed_without_import_time_dependency() -> None:
    def missing_importer(_name: str) -> object:
        raise ImportError("fixture no typer")

    result = probe_gateway_typer_adapter(importer=missing_importer)

    assert isinstance(result, GatewayTyperAdapterResult)
    assert result.available is False
    assert result.blocked is True
    assert result.error_code == TYPER_DEPENDENCY_MISSING_REASON
    assert len(result.commands) == 6
    _assert_zero_counters(result.counters)


def test_health_and_diagnostics_do_not_probe_network_or_qmt() -> None:
    health = build_gateway_runtime_health_summary(
        {"healthy": False, "blocked_reason": "fixture-unhealthy"},
        config=_safe_config(),
    )
    diagnostics = build_gateway_runtime_diagnostics(_safe_config())

    for payload in (health, diagnostics):
        _assert_zero_counters(payload["counters"])
        assert payload["counters"]["gateway_socket_open"] == 0
        assert payload["counters"]["http_client_call"] == 0
        assert payload["counters"]["qmt_api_call"] == 0


def test_gateway_runtime_sources_do_not_import_runtime_or_network_modules() -> None:
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
    }
    imported: set[str] = set()
    for path in SOURCE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

    assert imported.isdisjoint(forbidden_import_roots)
    _assert_zero_counters(collect_gateway_runtime_counters())
