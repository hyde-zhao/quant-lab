from __future__ import annotations

import ast
from pathlib import Path

from engine.goldminer_bridge_contract import (
    ALLOWED_L2_ACTIONS,
    FORBIDDEN_OPERATION_COUNTERS,
    NOT_AUTHORIZED_ACTIONS,
    SENSITIVE_FIELD_CATEGORIES,
    BridgeBlockedReason,
    allowed_l2_actions,
    build_blocked_payload,
    build_bridge_capabilities,
    build_bridge_health,
    classify_sensitive_field_name,
    forbidden_operation_counter_names,
    zero_forbidden_operation_counts,
)


def test_health_schema_is_l2_blocked_fixture() -> None:
    health = build_bridge_health().to_dict()

    assert health["schema_version"] == "cr045.l2.v1"
    assert health["status"] == "blocked"
    assert health["runtime_started"] is False
    assert health["not_authorization"] is True
    assert health["reason"] == BridgeBlockedReason.WINDOWS_BRIDGE_RUNTIME_NOT_AUTHORIZED.value
    assert set(health["operation_counts"]) == set(FORBIDDEN_OPERATION_COUNTERS)
    assert all(count == 0 for count in health["operation_counts"].values())


def test_capabilities_keep_all_real_flags_false() -> None:
    capabilities = build_bridge_capabilities().to_dict()

    assert capabilities["real_broker_enabled"] is False
    assert capabilities["readonly_probe_ready"] is False
    assert capabilities["simulation_ready"] is False
    assert capabilities["live_ready"] is False
    assert tuple(capabilities["allowed_actions"]) == ALLOWED_L2_ACTIONS
    assert set(capabilities["not_authorized_actions"]) >= set(NOT_AUTHORIZED_ACTIONS)
    assert all(count == 0 for count in capabilities["operation_counts"].values())


def test_l2_allowlist_contains_only_three_skeleton_actions() -> None:
    assert allowed_l2_actions() == (
        "health",
        "capabilities",
        "readonly_probe_skeleton",
    )


def test_sensitive_field_classification_outputs_category_only() -> None:
    for category in SENSITIVE_FIELD_CATEGORIES:
        assert classify_sensitive_field_name(category) == category

    blocked = build_blocked_payload(
        action="cash_query",
        reason=BridgeBlockedReason.SENSITIVE_MATERIAL_PRESENT,
        field_names=("token", "account_id", "ordinary_field"),
    )

    assert blocked["status"] == "blocked"
    assert blocked["redaction_summary"]["redacted_value"] == "REDACTED"
    assert blocked["redaction_summary"]["category_counts"] == {"token": 1, "account_id": 1}


def test_forbidden_counter_surface_is_complete_and_zero() -> None:
    required = {
        "real_broker_call",
        "real_order_call",
        "real_cancel_call",
        "real_account_query",
        "real_position_query",
        "real_cash_query",
        "credential_read",
        "goldminer_import_or_call",
        "gmtrade_import_or_call",
        "provider_fetch",
        "lake_write",
        "catalog_publish",
        "simulation_runtime_start",
        "live_runtime_start",
    }

    assert required <= set(forbidden_operation_counter_names())
    assert zero_forbidden_operation_counts() == {
        name: 0 for name in forbidden_operation_counter_names()
    }


def test_contract_module_has_no_real_sdk_import_or_runtime_call() -> None:
    source_path = Path("engine/goldminer_bridge_contract.py")
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

    assert imports.isdisjoint({"gm", "gmtrade", "socket", "requests", "urllib", "subprocess"})
    assert calls.isdisjoint({"login", "connect", "query", "submit", "cancel"})
