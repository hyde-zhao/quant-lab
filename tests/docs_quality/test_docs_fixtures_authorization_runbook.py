from __future__ import annotations

import re
from pathlib import Path

import yaml

from trading.runner_control_contracts import FORBIDDEN_OPERATION_COUNTER_FIELDS


PROJECT_ROOT = Path(__file__).parents[2]
MATRIX = PROJECT_ROOT / "process" / "docs" / "quality" / "TEST-MATRIX-CR138.md"
RUNBOOK = PROJECT_ROOT / "docs" / "reference" / "RUNNER-QMT-AUTHORIZATION.md"


def test_cr138_fixture_matrix_covers_all_stories_and_forbidden_operations() -> None:
    content = MATRIX.read_text(encoding="utf-8")

    for index in range(1, 9):
        assert f"CR138-S{index:02d}" in content
    for operation in FORBIDDEN_OPERATION_COUNTER_FIELDS:
        assert f"| {operation} | 0 |" in content
    assert "runtime_authorization gate" in content


def test_cr138_authorization_runbook_template_has_required_fields_and_no_secret_examples() -> None:
    content = RUNBOOK.read_text(encoding="utf-8")
    required_fields = {
        "action_scope",
        "time_window",
        "environment_ref",
        "credential_policy",
        "data_redaction",
        "rollback_plan",
        "audit_ref",
        "allowed_commands",
        "forbidden_commands",
    }

    for field in required_fields:
        assert field in content
    lowered = content.lower()
    forbidden_literals = (
        "password=123",
        "token=abc",
        "secret=abc",
        "account_id=123",
        "-----begin private key-----",
    )
    for literal in forbidden_literals:
        assert literal not in lowered


def test_cr138_docs_do_not_claim_runtime_or_broker_verified() -> None:
    combined = MATRIX.read_text(encoding="utf-8") + "\n" + RUNBOOK.read_text(encoding="utf-8")
    forbidden_claims = (
        r"\bruntime verified\b",
        r"\bqmt verified\b",
        r"\bbroker verified\b",
        r"当前已授权真实",
        r"可以直接提交订单",
    )

    for pattern in forbidden_claims:
        assert re.search(pattern, combined, flags=re.IGNORECASE) is None


def test_runtime_authorization_template_can_be_represented_as_yaml_shape() -> None:
    template = {
        "action_scope": "account_readonly",
        "time_window": "2026-06-24T16:00:00+08:00/2026-06-24T16:15:00+08:00",
        "environment_ref": "env:redacted",
        "credential_policy": "redacted-ref-only",
        "data_redaction": ["account", "token", "raw_orders"],
        "rollback_plan": "stop-gateway-and-discard-fixture",
        "audit_ref": "gate:manual",
        "allowed_commands": ["query-redacted-summary"],
        "forbidden_commands": ["submit", "cancel", "live"],
    }
    rendered = yaml.safe_dump(template, sort_keys=True)
    parsed = yaml.safe_load(rendered)

    assert set(parsed) >= {
        "action_scope",
        "time_window",
        "environment_ref",
        "credential_policy",
        "data_redaction",
        "rollback_plan",
        "audit_ref",
        "allowed_commands",
        "forbidden_commands",
    }
