from __future__ import annotations

import builtins
from dataclasses import fields
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

import pytest

import trading.qmt_redaction as qmt_redaction
from trading.qmt_auth import (
    CR020_QMT_AUTH_SCHEMA_VERSION,
    DEFAULT_HMAC_CLOCK_SKEW_SECONDS,
    FIXTURE_PAIRING_CODE,
    PairingApproval,
    QMT_QUERY_POSITIONS_REQUIRED_SCOPE,
    QmtAllowlistDecision,
    QmtAuthAdmissionDecision,
    QmtAuthBlockedReason,
    QmtAuthConfig,
    QmtHmacHeaderBuildResult,
    QmtHmacHeaderProvider,
    QmtNonceReplayStore,
    QmtRequestSourceContext,
    QmtScopeDecision,
    approve_pairing_request,
    build_qmt_hmac_request_headers,
    build_qmt_request_source_context,
    collect_qmt_auth_safety_counters,
    complete_pairing,
    create_pairing_request,
    evaluate_qmt_auth_admission,
    stable_qmt_auth_hash,
    validate_no_auth_runtime_mode,
    validate_qmt_allowlist,
)
from trading.qmt_endpoint_matrix import get_endpoint_spec
from trading.qmt_gateway_config import GatewayAllowlist
from trading.qmt_redaction import (
    REDACTED_VALUE,
    RedactionReport,
    redact_qmt_diagnostics_payload,
    redact_qmt_error_payload,
    redact_qmt_response_payload,
    scan_for_qmt_sensitive_leaks,
    scan_qmt_auth_redaction_leaks,
)


NOW = datetime(2026, 6, 5, 8, 30, 0, tzinfo=timezone.utc)
CLIENT_ID = "client-cr020-s04-fixture"
SECRET = "fixture-only-cr020-s04-secret"
PAIRING_CODE = FIXTURE_PAIRING_CODE
BODY = b'{"request":"positions"}'
METHOD = "POST"
PATH = "/qmt/account/positions"
ENDPOINT_ID = "query_positions"

REQUIRED_ZERO_COUNTERS = {
    "adapter_call",
    "dependency_change",
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
    "gateway_start",
    "service_start",
    "service_bind",
    "transport_send",
    "network_call",
    "socket_open",
    "http_client_call",
    "gateway_socket_open",
    "raw_fallback",
    "redaction_fallback_to_raw",
}


def _approval_config(
    *,
    scopes: tuple[str, ...] = (QMT_QUERY_POSITIONS_REQUIRED_SCOPE,),
    secret: str | None = SECRET,
) -> tuple[PairingApproval, QmtAuthConfig]:
    request = create_pairing_request(
        client_name="cr020-s04-client",
        source_context={
            "source_ip_hash": "fixture-source-hash",
            "machine_fingerprint_hash": "fixture-machine-hash",
        },
        now=NOW,
        request_id="pairing-request-cr020-s04",
    )
    approval = approve_pairing_request(
        request,
        scopes=scopes,
        now=NOW,
        client_id=CLIENT_ID,
        secret_ref="<runtime-secret-ref>",
        pairing_code=PAIRING_CODE,
    )
    secrets = {CLIENT_ID: secret} if secret is not None else {}
    return approval, QmtAuthConfig(approvals={CLIENT_ID: approval}, client_secrets=secrets)


def _headers(
    *,
    secret: str = SECRET,
    timestamp: datetime = NOW,
    nonce: str = "nonce-cr020-s04-001",
    signature_override: str | None = None,
) -> dict[str, str]:
    result = build_qmt_hmac_request_headers(
        client_id=CLIENT_ID,
        secret=secret,
        method=METHOD,
        path=PATH,
        body=BODY,
        required_scope=QMT_QUERY_POSITIONS_REQUIRED_SCOPE,
        timestamp=str(int(timestamp.timestamp())),
        nonce=nonce,
        granted_scopes=(QMT_QUERY_POSITIONS_REQUIRED_SCOPE,),
    )
    headers = dict(result.headers)
    if signature_override is not None:
        headers["X-QMT-Signature"] = signature_override
    return headers


def _source(ip: str = "127.0.0.1") -> QmtRequestSourceContext:
    return build_qmt_request_source_context(
        {
            "source_ip": ip,
            "machine_fingerprint_hash": "fixture-machine-hash",
        }
    )


def _allowlist(source: str = "127.0.0.1/32") -> GatewayAllowlist:
    return GatewayAllowlist(sources=(source,), required=True)


def _admission(
    *,
    config: QmtAuthConfig | None = None,
    headers: dict[str, str] | None = None,
    source: QmtRequestSourceContext | None = None,
    allowlist: GatewayAllowlist | None = None,
    nonce_store: QmtNonceReplayStore | None = None,
    now: datetime = NOW,
) -> QmtAuthAdmissionDecision:
    _approval, default_config = _approval_config()
    return evaluate_qmt_auth_admission(
        request_source=source or _source(),
        method=METHOD,
        path=PATH,
        body=BODY,
        headers=headers if headers is not None else _headers(),
        config=config or default_config,
        allowlist=allowlist or _allowlist(),
        endpoint_id=ENDPOINT_ID,
        now=now,
        nonce_store=nonce_store,
    )


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _assert_blocked(
    decision: QmtAuthAdmissionDecision,
    reason: QmtAuthBlockedReason,
) -> None:
    assert decision.accepted is False
    assert decision.blocked is True
    assert decision.blocked_reason is reason
    assert decision.reason_code == reason.value
    assert decision.adapter_call_allowed is False
    assert decision.qmt_api_call_allowed is False
    assert decision.trade_authorized is False
    assert decision.account_write_authorized is False
    assert decision.simulation_authorized is False
    assert decision.live_authorized is False
    _assert_zero_counters(decision.counters)


def test_cr020_auth_models_pairing_public_view_and_source_context_do_not_leak() -> None:
    approval, _config = _approval_config()
    paired = complete_pairing(approval, pairing_code=PAIRING_CODE, now=NOW)
    source_context = _source()

    assert CR020_QMT_AUTH_SCHEMA_VERSION == "cr020-s04-hmac-pairing-allowlist-scope-v1"
    assert {field.name for field in fields(QmtRequestSourceContext)} == {
        "source_ip",
        "source_ref",
        "source_ip_hash",
        "machine_fingerprint_hash",
        "provided_by",
        "is_public_source",
        "counters",
    }
    assert {field.name for field in fields(QmtAllowlistDecision)} == {
        "allowed",
        "status",
        "blocked_reason",
        "source_ref",
        "source_ip_hash",
        "matched_source_ref",
        "counters",
    }
    assert {field.name for field in fields(QmtScopeDecision)} == {
        "allowed",
        "status",
        "required_scope",
        "granted_scopes",
        "endpoint_id",
        "blocked_reason",
        "counters",
    }
    assert {field.name for field in fields(QmtHmacHeaderBuildResult)} == {
        "accepted",
        "status",
        "headers",
        "required_scope",
        "client_id_hash",
        "nonce_ref",
        "signature_ref",
        "blocked_reason",
        "counters",
    }

    public_payload = {
        "approval": approval.to_public_dict(),
        "pairing": paired.to_dict(),
        "source": source_context.to_dict(),
    }
    assert SECRET not in repr(public_payload)
    assert PAIRING_CODE not in repr(public_payload)
    assert "127.0.0.1" not in repr(public_payload)
    assert public_payload["approval"]["secret_ref"] == REDACTED_VALUE
    assert scan_for_qmt_sensitive_leaks(public_payload).leak_count == 0
    _assert_zero_counters(source_context.counters)


def test_allowlist_exact_pass_mismatch_missing_and_public_source_fail_closed() -> None:
    allowed = validate_qmt_allowlist(_source("127.0.0.1"), _allowlist("127.0.0.1/32"))
    missing = validate_qmt_allowlist(None, _allowlist())
    mismatch = validate_qmt_allowlist(_source("10.10.0.5"), _allowlist("127.0.0.1/32"))
    public_source = validate_qmt_allowlist(_source("8.8.8.8"), _allowlist("8.8.8.8/32"))

    assert allowed.allowed is True
    assert allowed.matched_source_ref == "127.0.0.1/32"
    assert allowed.source_ip_hash == stable_qmt_auth_hash("127.0.0.1")
    assert missing.blocked_reason is QmtAuthBlockedReason.AUTH_SOURCE_MISSING
    assert mismatch.blocked_reason is QmtAuthBlockedReason.AUTH_ALLOWLIST_MISMATCH
    assert public_source.blocked_reason is QmtAuthBlockedReason.AUTH_PUBLIC_SOURCE_FORBIDDEN
    for decision in (allowed, missing, mismatch, public_source):
        _assert_zero_counters(decision.counters)


@pytest.mark.parametrize(
    ("headers", "config", "reason"),
    (
        ({}, None, QmtAuthBlockedReason.AUTH_HEADER_MISSING),
        (
            _headers(signature_override="bad-fixture-signature"),
            None,
            QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
        ),
        (
            _headers(
                timestamp=NOW
                - timedelta(seconds=DEFAULT_HMAC_CLOCK_SKEW_SECONDS + 1)
            ),
            None,
            QmtAuthBlockedReason.AUTH_TIMESTAMP_SKEW,
        ),
        (
            _headers(),
            _approval_config(secret=None)[1],
            QmtAuthBlockedReason.AUTH_SECRET_UNAVAILABLE,
        ),
    ),
)
def test_hmac_missing_mismatch_expired_and_secret_unavailable_block_admission(
    headers: dict[str, str],
    config: QmtAuthConfig | None,
    reason: QmtAuthBlockedReason,
) -> None:
    decision = _admission(headers=headers, config=config)

    _assert_blocked(decision, reason)
    if decision.hmac_result is not None:
        assert decision.hmac_result.adapter_call_allowed is False


def test_nonce_replay_store_blocks_second_use_and_allows_after_ttl_expiry() -> None:
    store = QmtNonceReplayStore(ttl_seconds=10, max_entries=16)
    headers = _headers(nonce="nonce-replay-cr020-s04")

    first = _admission(headers=headers, nonce_store=store)
    replay = _admission(headers=headers, nonce_store=store)
    after_ttl = _admission(
        headers=headers,
        nonce_store=store,
        now=NOW + timedelta(seconds=11),
    )

    assert first.accepted is True
    _assert_blocked(replay, QmtAuthBlockedReason.AUTH_NONCE_REPLAY)
    assert after_ttl.accepted is True
    assert store.size == 1
    _assert_zero_counters(first.counters)
    _assert_zero_counters(after_ttl.counters)


def test_scope_insufficient_blocks_query_positions_before_dispatcher() -> None:
    _approval, config = _approval_config(scopes=("qmt:health",))

    decision = _admission(config=config, headers=_headers(nonce="nonce-scope-denied"))

    _assert_blocked(decision, QmtAuthBlockedReason.AUTH_SCOPE_DENIED)
    assert decision.required_scope == QMT_QUERY_POSITIONS_REQUIRED_SCOPE
    assert decision.scope_decision is not None
    assert decision.scope_decision.allowed is False


def test_hmac_pass_identifies_caller_but_does_not_authorize_qmt_or_trading() -> None:
    decision = _admission(headers=_headers(nonce="nonce-hmac-pass"))

    assert decision.accepted is True
    assert decision.status == "accepted_for_next_gate"
    assert decision.hmac_result is not None
    assert decision.hmac_result.allowed is True
    assert decision.hmac_result.caller_identified is True
    assert decision.adapter_call_allowed is False
    assert decision.qmt_api_call_allowed is False
    assert decision.trade_authorized is False
    assert decision.account_write_authorized is False
    assert decision.simulation_authorized is False
    assert decision.live_authorized is False
    assert decision.hmac_result.trade_authorized is False
    assert decision.hmac_result.account_authorized is False
    assert decision.hmac_result.adapter_call_allowed is False
    _assert_zero_counters(decision.counters)
    _assert_zero_counters(decision.hmac_result.counters)


def test_s03_compatible_header_provider_uses_only_explicit_inputs_and_redacted_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_open(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("provider 不得读取任何文件")

    class GuardedEnv(dict[str, str]):
        def __getitem__(self, key: str) -> str:
            raise AssertionError(f"provider 不得读取环境变量: {key}")

        def get(self, key: str, default: object = None) -> object:
            raise AssertionError(f"provider 不得读取环境变量: {key}")

    monkeypatch.setattr(builtins, "open", forbidden_open)
    monkeypatch.setattr(Path, "read_text", forbidden_open)
    monkeypatch.setattr(os, "environ", GuardedEnv())

    provider = QmtHmacHeaderProvider(
        client_id=CLIENT_ID,
        secret=SECRET,
        scopes=(QMT_QUERY_POSITIONS_REQUIRED_SCOPE,),
        clock=lambda: NOW,
        nonce_provider=lambda: "nonce-provider-cr020-s04",
    )
    result = provider.build_result(
        {
            "method": METHOD,
            "path": PATH,
            "body": BODY,
            "required_scope": QMT_QUERY_POSITIONS_REQUIRED_SCOPE,
        }
    )
    headers = provider.build_headers(
        {
            "method": METHOD,
            "path": PATH,
            "body": BODY,
            "required_scope": QMT_QUERY_POSITIONS_REQUIRED_SCOPE,
        }
    )

    assert result.accepted is True
    assert headers["X-QMT-Client-Id"] == CLIENT_ID
    assert headers["X-QMT-Signature"]
    assert SECRET not in repr(result.to_dict())
    assert headers["X-QMT-Signature"] not in repr(result.to_dict())
    assert "nonce-provider-cr020-s04" not in repr(result.to_dict())
    assert SECRET not in repr(provider.diagnostics())
    assert scan_for_qmt_sensitive_leaks(result.to_dict()).leak_count == 0
    assert scan_for_qmt_sensitive_leaks(provider.diagnostics()).leak_count == 0


def test_response_error_and_diagnostics_redaction_gate_blocks_sensitive_output() -> None:
    raw_payload = {
        "account_id": "123456789012",
        "secret": SECRET,
        "token": "fixture-token-cr020-s04",
        "session": "fixture-session-cr020-s04",
        "signature": "raw-signature-cr020-s04",
        "credential_ref": "raw-credential-ref-cr020-s04",
        "message": (
            "account=123456789012 token=fixture-token-cr020-s04 "
            "session=fixture-session-cr020-s04 signature=raw-signature-cr020-s04 "
            "path=C:\\Users\\Fixture\\.env"
        ),
    }

    decisions = (
        redact_qmt_response_payload(raw_payload),
        redact_qmt_error_payload(raw_payload),
        redact_qmt_diagnostics_payload(raw_payload),
    )

    for decision in decisions:
        assert decision.accepted is True
        assert decision.redaction_status == "pass"
        assert decision.leak_count == 0
        assert decision.raw_fallback_allowed is False
        assert scan_qmt_auth_redaction_leaks(decision.to_dict()).accepted is True
        rendered = repr(decision.to_dict())
        for forbidden in (
            SECRET,
            "123456789012",
            "fixture-token-cr020-s04",
            "fixture-session-cr020-s04",
            "raw-signature-cr020-s04",
            "raw-credential-ref-cr020-s04",
            "C:\\Users\\Fixture\\.env",
        ):
            assert forbidden not in rendered


def test_redaction_failure_blocks_raw_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_payload = {"secret": SECRET, "message": f"secret={SECRET}"}

    def failed_scan(_payload: object) -> RedactionReport:
        return RedactionReport(
            leak_count=1,
            redaction_status="failed",
            matched_categories=("secret",),
        )

    monkeypatch.setattr(qmt_redaction, "scan_for_qmt_sensitive_leaks", failed_scan)

    decision = qmt_redaction.redact_qmt_response_payload(raw_payload)

    assert decision.accepted is False
    assert decision.blocked is True
    assert decision.redaction_status == "failed"
    assert decision.blocked_reason == "redaction_failed"
    assert decision.raw_fallback_allowed is False
    assert SECRET not in repr(decision.to_dict())


def test_no_auth_default_is_blocked_even_for_fixture_runtime() -> None:
    blocked = validate_no_auth_runtime_mode(
        QmtAuthConfig(auth_mode="no_auth"),
        runtime_context="fixture_test",
    )
    explicit_fixture = validate_no_auth_runtime_mode(
        QmtAuthConfig(auth_mode="no_auth", allow_no_auth_fixture=True),
        runtime_context="fixture_test",
    )

    assert blocked.blocked_reason is QmtAuthBlockedReason.AUTH_NO_AUTH_NOT_ALLOWED
    assert blocked.allowed is False
    assert explicit_fixture.allowed is True
    assert explicit_fixture.adapter_call_allowed is False
    assert explicit_fixture.trade_authorized is False
    _assert_zero_counters(blocked.counters)
    _assert_zero_counters(explicit_fixture.counters)


def test_endpoint_matrix_query_positions_scope_is_exact_and_later_gated() -> None:
    spec = get_endpoint_spec("query_positions")

    assert spec.endpoint_id == "query_positions"
    assert spec.method == METHOD
    assert spec.path == PATH
    assert spec.client_method == "query_positions"
    assert spec.required_scope == QMT_QUERY_POSITIONS_REQUIRED_SCOPE
    assert spec.later_gated is True


def test_s04_public_helpers_keep_no_real_operation_counters_zero() -> None:
    counters = collect_qmt_auth_safety_counters()
    auth_source = Path("trading/qmt_auth.py").read_text(encoding="utf-8")
    redaction_source = Path("trading/qmt_redaction.py").read_text(encoding="utf-8")

    _assert_zero_counters(counters)
    assert "import xtquant" not in auth_source.lower()
    assert "from xtquant" not in auth_source.lower()
    assert "import xtquant" not in redaction_source.lower()
    assert "from xtquant" not in redaction_source.lower()
    assert "socket.socket" not in auth_source
    assert "socket.socket" not in redaction_source
    assert ".env" not in repr(_source().to_dict())
