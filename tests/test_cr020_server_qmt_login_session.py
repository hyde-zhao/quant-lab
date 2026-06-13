from __future__ import annotations

import ast
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trading.qmt_gateway_session import (
    QMT_SESSION_REQUIRED_ZERO_COUNTERS,
    QmtCredentialRef,
    QmtLoginAdapter,
    QmtSessionBlockedReason,
    QmtSessionConfig,
    QmtSessionGateResult,
    QmtSessionSnapshot,
    QmtSessionState,
    build_qmt_credential_ref,
    build_qmt_session_config,
    build_qmt_session_diagnostics,
    collect_qmt_session_safety_counters,
    evaluate_qmt_session_ready,
    plan_qmt_login_session,
    require_qmt_session_ready,
)


NOW = datetime(2026, 6, 5, 8, 30, 0, tzinfo=timezone.utc)
SOURCE_PATH = Path("trading/qmt_gateway_session.py")
ENV_EXAMPLE_PATH = Path(".env.example")


def _credential_source(**overrides: object) -> dict[str, object]:
    source: dict[str, object] = {
        "credential_ref": "<qmt-credential-ref-placeholder>",
        "QMT_LOGIN_ACCOUNT": "<qmt-login-account-placeholder>",
        "QMT_LOGIN_PASSWORD": "<qmt-login-password-placeholder>",
        "QMT_ACCOUNT_REF": "<qmt-account-ref-placeholder>",
    }
    source.update(overrides)
    return source


def _ready_snapshot(**overrides: object) -> QmtSessionSnapshot:
    snapshot = QmtSessionSnapshot(
        state=QmtSessionState.READY,
        ready=True,
        blocked_reason=None,
        credential_ref="<qmt-credential-ref-placeholder>",
        started_at=NOW.isoformat(),
        ready_at=NOW.isoformat(),
        expires_at=(NOW + timedelta(seconds=60)).isoformat(),
        runtime_status="fixture-ready",
    )
    return replace(snapshot, **overrides)


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in QMT_SESSION_REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in QMT_SESSION_REQUIRED_ZERO_COUNTERS
    }


class CountingAdapter(QmtLoginAdapter):
    def __init__(self) -> None:
        self.login_calls = 0

    def login(self, config: QmtSessionConfig) -> QmtSessionSnapshot:
        self.login_calls += 1
        return _ready_snapshot(credential_ref=config.credential_ref.credential_ref)

    def check_ready(self) -> QmtSessionSnapshot:
        return _ready_snapshot()

    def logout(self) -> QmtSessionSnapshot | None:
        return QmtSessionSnapshot(
            state=QmtSessionState.BLOCKED,
            ready=False,
            blocked_reason=QmtSessionBlockedReason.SESSION_NOT_READY,
            credential_ref="<qmt-credential-ref-placeholder>",
            runtime_status="fixture-logout",
        )


def test_session_model_fields_and_state_values_are_complete() -> None:
    assert {state.value for state in QmtSessionState} == {
        "not_configured",
        "login_pending",
        "ready",
        "expired",
        "blocked",
        "error",
    }
    assert {field.name for field in fields(QmtCredentialRef)} == {
        "credential_ref",
        "required_keys",
        "missing_keys",
        "redaction_status",
        "leak_count",
        "schema_version",
    }
    assert {field.name for field in fields(QmtSessionConfig)} == {
        "credential_ref",
        "ready_timeout_seconds",
        "session_ttl_seconds",
        "qmt_login_allowed",
        "redaction_required",
        "gateway_runtime_ready",
        "credential_ref_source",
        "schema_version",
    }
    assert {field.name for field in fields(QmtSessionSnapshot)} == {
        "state",
        "ready",
        "blocked_reason",
        "credential_ref",
        "started_at",
        "ready_at",
        "expires_at",
        "runtime_status",
        "counters",
        "redaction_status",
        "leak_count",
        "schema_version",
    }
    assert {field.name for field in fields(QmtSessionGateResult)} == {
        "allowed",
        "state",
        "blocked_reason",
        "endpoint_id",
        "adapter_call_allowed",
        "counters",
        "redaction_status",
        "schema_version",
    }


def test_credential_ref_keeps_only_redacted_reference_and_key_names() -> None:
    raw_account = "123456789012"
    raw_password = "password=fixture-secret"
    credential = build_qmt_credential_ref(
        _credential_source(
            credential_ref="unsafe-runtime-ref",
            QMT_LOGIN_ACCOUNT=raw_account,
            QMT_LOGIN_PASSWORD=raw_password,
        )
    )
    public_payload = credential.to_dict()
    rendered = repr(public_payload)

    assert credential.credential_ref == "[REDACTED]"
    assert credential.configured is True
    assert raw_account not in rendered
    assert raw_password not in rendered
    assert "QMT_LOGIN_ACCOUNT" in public_payload["required_keys"]
    assert public_payload["missing_keys"] == []
    assert credential.leak_count == 0


def test_cp5_fixture_login_not_allowed_never_calls_adapter() -> None:
    adapter = CountingAdapter()
    config = build_qmt_session_config(_credential_source(), qmt_login_allowed=False)
    snapshot = plan_qmt_login_session(config, adapter=adapter, now=NOW)

    assert snapshot.state is QmtSessionState.BLOCKED
    assert snapshot.blocked_reason is QmtSessionBlockedReason.LOGIN_NOT_ALLOWED
    assert snapshot.ready is False
    assert adapter.login_calls == 0
    _assert_zero_counters(snapshot.counters)


def test_not_configured_fails_closed_with_missing_key_names_only() -> None:
    snapshot = plan_qmt_login_session(
        {"QMT_LOGIN_ACCOUNT": "<qmt-login-account-placeholder>"},
        now=NOW,
    )

    assert snapshot.state is QmtSessionState.NOT_CONFIGURED
    assert snapshot.blocked_reason is QmtSessionBlockedReason.CREDENTIAL_NOT_CONFIGURED
    assert snapshot.credential_ref == "[REDACTED]"
    assert snapshot.ready is False
    _assert_zero_counters(snapshot.counters)


def test_expired_snapshot_is_not_ready() -> None:
    expired = _ready_snapshot(expires_at=(NOW - timedelta(seconds=1)).isoformat())
    current = evaluate_qmt_session_ready(expired, now=NOW)

    assert current.state is QmtSessionState.EXPIRED
    assert current.ready is False
    assert current.blocked_reason is QmtSessionBlockedReason.SESSION_EXPIRED


def test_session_not_ready_blocks_query_positions_adapter_call() -> None:
    pending = QmtSessionSnapshot(
        state=QmtSessionState.LOGIN_PENDING,
        ready=False,
        blocked_reason=QmtSessionBlockedReason.SESSION_NOT_READY,
        credential_ref="<qmt-credential-ref-placeholder>",
        runtime_status="fixture-login-pending",
    )
    result = require_qmt_session_ready(pending, endpoint_id="query_positions", now=NOW)

    assert result.allowed is False
    assert result.blocked is True
    assert result.adapter_call_allowed is False
    assert result.blocked_reason is QmtSessionBlockedReason.SESSION_NOT_READY
    assert result.counters["query_positions_adapter_call"] == 0
    _assert_zero_counters(result.counters)


def test_ready_gate_allows_dispatch_but_does_not_call_qmt_api() -> None:
    result = require_qmt_session_ready(_ready_snapshot(), endpoint_id="query_positions", now=NOW)

    assert result.allowed is True
    assert result.adapter_call_allowed is True
    assert result.counters["qmt_api_call"] == 0
    assert result.counters["query_positions_adapter_call"] == 0
    _assert_zero_counters(result.counters)


def test_diagnostics_redacts_sensitive_snapshot_values() -> None:
    snapshot = QmtSessionSnapshot(
        state=QmtSessionState.BLOCKED,
        ready=False,
        blocked_reason=QmtSessionBlockedReason.SESSION_NOT_READY,
        credential_ref="account=123456789012",
        runtime_status="session=fixture-session-token",
    )
    diagnostics = build_qmt_session_diagnostics(snapshot)
    rendered = repr(diagnostics)

    assert diagnostics["redaction_status"] == "pass"
    assert diagnostics["leak_count"] == 0
    assert "123456789012" not in rendered
    assert "fixture-session-token" not in rendered


def test_session_safety_counters_are_normalized_to_zero_by_default() -> None:
    counters = collect_qmt_session_safety_counters()

    _assert_zero_counters(counters)
    assert counters["credential_read"] == 0
    assert counters["qmt_login_call"] == 0
    assert counters["xtquant_import"] == 0
    assert counters["account_write"] == 0
    assert counters["real_order"] == 0


def test_session_source_does_not_import_qmt_runtime_modules() -> None:
    forbidden_import_roots = {
        "xtquant",
        "xttrader",
        "xtdata",
        "qmt",
        "mini_qmt",
        "miniqmt",
        "socket",
        "subprocess",
    }
    imported: set[str] = set()
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert imported.isdisjoint(forbidden_import_roots)


def test_env_example_is_placeholder_only_and_contains_no_real_values() -> None:
    content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    assignments = [
        line
        for line in content.splitlines()
        if line and not line.startswith("#") and "=" in line
    ]

    assert "QMT_CREDENTIAL_REF=<qmt-credential-ref-placeholder>" in content
    assert "QMT_LOGIN_ACCOUNT=<qmt-login-account-placeholder>" in content
    assert "QMT_LOGIN_PASSWORD=<qmt-login-password-placeholder>" in content
    assert "QMT_SESSION_READY_TIMEOUT_SECONDS=<session-ready-timeout-seconds-placeholder>" in content
    for line in assignments:
        value = line.split("=", 1)[1]
        assert value.startswith("<") and value.endswith(">")
    assert "C:\\Users\\" not in content
    assert "/home/" not in content
    assert "123456" not in content
    for line in assignments:
        value = line.split("=", 1)[1].lower()
        assert "password=" not in value
        assert "token=" not in value
        assert "session=" not in value
