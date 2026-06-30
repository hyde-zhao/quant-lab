from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from engine.goldminer_bridge_contract import BridgeBlockedReason
from engine.goldminer_bridge_probe import (
    build_readonly_probe_request,
    evaluate_readonly_probe_request,
    readonly_probe_forbidden_fields,
    readonly_probe_kinds,
)


def test_readonly_probe_request_schema_is_skeleton_only() -> None:
    request = build_readonly_probe_request(
        "cash_skeleton",
        client_context={"client_name": "cr045-fixture"},
    )

    assert request.action == "readonly_probe_skeleton"
    assert request.probe_kind == "cash_skeleton"
    assert request.contains_sensitive_material is False
    assert "token" not in request.client_context


def test_l4_missing_authorization_blocks_even_allowed_skeleton_kind() -> None:
    response = evaluate_readonly_probe_request(build_readonly_probe_request("position_skeleton")).to_dict()

    assert response["status"] == "blocked"
    assert response["reason"] == BridgeBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value
    assert response["real_readonly_verified"] is False
    assert response["not_authorization"] is True
    assert response["data"] == {}
    assert all(count == 0 for count in response["operation_counts"].values())


def test_real_readonly_query_kinds_are_blocked() -> None:
    for probe_kind in ("cash_query", "position_query", "order_query", "fill_query", "account_state_query"):
        response = evaluate_readonly_probe_request(build_readonly_probe_request(probe_kind)).to_dict()
        assert response["status"] == "blocked"
        assert response["reason"] == BridgeBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED.value
        assert response["real_readonly_verified"] is False


def test_non_allowlist_action_and_sensitive_material_are_blocked() -> None:
    request = build_readonly_probe_request("cash_skeleton")
    wrong_action = replace(request, action="cash_query")
    sensitive = build_readonly_probe_request(
        "cash_skeleton",
        client_context={"account_id": "REDACTED"},
        contains_sensitive_material=True,
    )

    assert evaluate_readonly_probe_request(wrong_action).reason == BridgeBlockedReason.OPERATION_NOT_WHITELISTED.value
    sensitive_response = evaluate_readonly_probe_request(sensitive).to_dict()
    assert sensitive_response["reason"] == BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT.value
    assert sensitive_response["redaction_summary"]["category_counts"] == {"account_id": 1}


def test_probe_kinds_and_forbidden_fields_cover_contract_surface() -> None:
    assert set(readonly_probe_kinds()) == {
        "account_state_skeleton",
        "cash_skeleton",
        "position_skeleton",
        "order_skeleton",
        "fill_skeleton",
    }
    assert {
        "token",
        "account_id",
        "session",
        "cash",
        "position",
        "order",
        "fill",
    } <= set(readonly_probe_forbidden_fields())


def test_probe_module_has_no_real_sdk_network_or_broker_calls() -> None:
    source_path = Path("engine/goldminer_bridge_probe.py")
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
    assert calls.isdisjoint({"login", "connect", "query", "submit", "cancel", "open"})
