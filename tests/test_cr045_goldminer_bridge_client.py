from __future__ import annotations

import ast
from pathlib import Path

from engine.goldminer_bridge_client import (
    build_bridge_client_request,
    fixture_transport,
    network_precheck,
    parse_bridge_response,
)
from engine.goldminer_bridge_contract import BridgeBlockedReason, zero_forbidden_operation_counts


def test_request_builder_accepts_only_l2_allowlist_actions() -> None:
    for action in ("health", "capabilities", "readonly_probe_skeleton"):
        request = build_bridge_client_request(action, client_context={"client_name": "cr045-fixture"})
        assert request.blocked is False
        assert request.action == action

    blocked = build_bridge_client_request("cash_query")
    assert blocked.blocked is True
    assert blocked.reason == BridgeBlockedReason.OPERATION_NOT_WHITELISTED.value
    assert blocked.payload == {}


def test_fixture_transport_returns_health_and_capabilities_without_real_runtime() -> None:
    health = fixture_transport(build_bridge_client_request("health")).to_dict()
    capabilities = fixture_transport(build_bridge_client_request("capabilities")).to_dict()

    assert health["status"] == "blocked"
    assert health["payload"]["runtime_started"] is False
    assert health["payload"]["not_authorization"] is True
    assert capabilities["payload"]["real_broker_enabled"] is False
    assert capabilities["payload"]["readonly_probe_ready"] is False
    assert capabilities["payload"]["simulation_ready"] is False
    assert capabilities["payload"]["live_ready"] is False
    assert all(count == 0 for count in health["operation_counts"].values())
    assert all(count == 0 for count in capabilities["operation_counts"].values())


def test_network_precheck_is_declarative_and_does_not_attempt_connection() -> None:
    precheck = network_precheck().to_dict()

    assert precheck["runtime_reachable"] is False
    assert precheck["runtime_start_attempted"] is False
    assert precheck["real_connection_attempted"] is False
    assert precheck["not_authorization"] is True
    assert precheck["operation_counts"] == zero_forbidden_operation_counts()


def test_parser_blocks_sensitive_field_names_without_returning_values() -> None:
    parsed = parse_bridge_response({"status": "fixture", "token": "do-not-return"})

    assert parsed.status == "blocked"
    assert parsed.reason == BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT.value
    assert parsed.payload == {}
    assert parsed.redaction_summary["redacted_value"] == "REDACTED"
    assert parsed.redaction_summary["category_counts"] == {"token": 1}


def test_readonly_skeleton_transport_is_blocked_first() -> None:
    response = fixture_transport(build_bridge_client_request("readonly_probe_skeleton")).to_dict()

    assert response["status"] == "blocked"
    assert response["payload"]["real_readonly_verified"] is False
    assert response["payload"]["data"] == {}
    assert all(count == 0 for count in response["operation_counts"].values())


def test_client_module_has_no_network_process_or_sdk_imports() -> None:
    source_path = Path("engine/goldminer_bridge_client.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")])
    }
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert imports.isdisjoint({"gm", "gmtrade", "socket", "requests", "urllib", "subprocess", "http"})
    assert calls.isdisjoint({"open", "connect", "request", "urlopen", "run", "Popen"})
