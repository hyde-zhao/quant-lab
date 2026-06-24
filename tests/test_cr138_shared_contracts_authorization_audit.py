from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from trading.runner_control_contracts import (
    AuthorizationRecord,
    AuditRecord,
    BlockedResult,
    ControlResultStatus,
    NoRealOperationCounters,
    collect_no_real_operation_counters,
    new_audit_record,
    require_scope,
    validate_contract_ids,
)
from trading.qmt_gateway_contracts import CapabilitySnapshot, GatewayHealth, RestRouteSpec


PROJECT_ROOT = Path(__file__).parents[1]


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
