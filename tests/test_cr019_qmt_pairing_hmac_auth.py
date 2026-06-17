from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timedelta, timezone

import pytest

from trading.qmt_auth import (
    DEFAULT_HMAC_CLOCK_SKEW_SECONDS,
    DEFAULT_NONCE_TTL_SECONDS,
    DEFAULT_PAIRING_CODE_TTL_SECONDS,
    DEFAULT_PAIRING_REQUEST_TTL_SECONDS,
    FIXTURE_PAIRING_CODE,
    PairingApproval,
    PairingRequest,
    QmtAuthBlockedReason,
    QmtAuthConfig,
    QmtAuthResult,
    QmtHmacHeaders,
    TRADING_AUTHORIZATION_SCOPES,
    approve_pairing_request,
    build_qmt_hmac_signature,
    collect_qmt_auth_safety_counters,
    complete_pairing,
    create_pairing_request,
    list_pending_pairing_requests,
    validate_auth_mode,
    validate_hmac_request,
)
from trading.qmt_gateway_config import (
    DEFAULT_AUTH_MODE,
    GatewayAuthConfig,
    build_gateway_config,
    validate_gateway_security,
)
from trading.qmt_redaction import (
    REDACTED_VALUE,
    redact_qmt_mapping,
    redact_qmt_text,
    scan_for_qmt_sensitive_leaks,
)


NOW = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
CLIENT_ID = "client-s05-fixture"
FIXTURE_SECRET = "fixture-only-secret-s05"
FIXTURE_TOKEN = "fixture-only-token-s05"
FIXTURE_ACCOUNT = "123456789012"
FIXTURE_SESSION = "fixture-only-session-s05"
FIXTURE_COOKIE = "fixture-only-cookie-s05"
FIXTURE_TRADE_PASSWORD = "fixture-only-trade-password-s05"
FIXTURE_PRIVATE_PATH = "C:\\Users\\Fixture\\.env"

REQUIRED_ZERO_COUNTERS = {
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
    "service_start",
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
}


def _pairing_fixture(
    *,
    scopes: tuple[str, ...] = ("health", "market"),
    approved_at: datetime = NOW,
    code_ttl_seconds: int = DEFAULT_PAIRING_CODE_TTL_SECONDS,
) -> tuple[PairingRequest, PairingApproval, QmtAuthConfig]:
    request = create_pairing_request(
        client_name="fixture-client",
        source_context={
            "source_ip_hash": "fixture-source-ip-hash",
            "machine_fingerprint_hash": "fixture-machine-hash",
        },
        now=NOW,
        request_id="pairing-request-s05",
    )
    approval = approve_pairing_request(
        request,
        scopes=scopes,
        now=approved_at,
        client_id=CLIENT_ID,
        secret_ref="<runtime-secret-ref>",
        pairing_code=FIXTURE_PAIRING_CODE,
        code_ttl_seconds=code_ttl_seconds,
    )
    config = QmtAuthConfig(
        approvals={CLIENT_ID: approval},
        client_secrets={CLIENT_ID: FIXTURE_SECRET},
    )
    return request, approval, config


def _headers(
    *,
    secret: str = FIXTURE_SECRET,
    method: str = "POST",
    path: str = "/fixture",
    body: bytes | str = b"{}",
    timestamp: int | None = None,
    nonce: str = "nonce-s05-001",
    signature: str | None = None,
) -> dict[str, str]:
    resolved_timestamp = str(timestamp if timestamp is not None else int(NOW.timestamp()))
    resolved_signature = signature or build_qmt_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        body=body,
        timestamp=resolved_timestamp,
        nonce=nonce,
    )
    return {
        "X-QMT-Client-Id": CLIENT_ID,
        "X-QMT-Timestamp": resolved_timestamp,
        "X-QMT-Nonce": nonce,
        "X-QMT-Signature": resolved_signature,
    }


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _assert_blocked(result: QmtAuthResult, reason: QmtAuthBlockedReason) -> None:
    assert result.allowed is False
    assert result.blocked is True
    assert result.blocked_reason is reason
    assert result.reason_code == reason.value
    assert result.adapter_call_allowed is False
    assert result.trade_authorized is False
    _assert_zero_counters(result.counters)


def test_pairing_models_and_four_step_contract_have_full_field_coverage() -> None:
    request, approval, _config = _pairing_fixture()
    pending = list_pending_pairing_requests([request], now=NOW)
    completed = complete_pairing(
        approval,
        pairing_code=FIXTURE_PAIRING_CODE,
        now=NOW,
    )

    assert {field.name for field in fields(PairingRequest)} == {
        "request_id",
        "client_name",
        "source_ip_hash",
        "machine_fingerprint_hash",
        "created_at",
        "expires_at",
        "status",
    }
    assert {field.name for field in fields(PairingApproval)} == {
        "request_id",
        "client_id",
        "client_id_hash",
        "secret_ref",
        "scopes",
        "approved_at",
        "code_expires_at",
        "pairing_code_hash",
        "status",
    }
    assert {field.name for field in fields(QmtHmacHeaders)} == {
        "client_id",
        "timestamp",
        "nonce",
        "signature",
    }
    assert {field.name for field in fields(QmtAuthConfig)} == {
        "auth_mode",
        "pairing_request_ttl_seconds",
        "pairing_code_ttl_seconds",
        "hmac_clock_skew_seconds",
        "nonce_ttl_seconds",
        "approvals",
        "client_secrets",
        "allow_no_auth_debug",
        "allow_no_auth_fixture",
        "allow_no_auth_temporary",
    }
    assert {field.name for field in fields(QmtAuthResult)} == {
        "allowed",
        "status",
        "blocked_reason",
        "client_id_hash",
        "scopes",
        "required_scope",
        "caller_identified",
        "adapter_call_allowed",
        "trade_authorized",
        "simulation_authorized",
        "live_authorized",
        "account_authorized",
        "cancel_authorized",
        "counters",
    }

    assert pending == (request.to_public_dict(),)
    assert approval.to_public_dict()["pairing_code_status"] == "redacted"
    assert approval.to_public_dict()["secret_ref"] == REDACTED_VALUE
    assert completed.allowed is True
    assert completed.caller_identified is True
    assert completed.trade_authorized is False
    assert completed.adapter_call_allowed is False
    _assert_zero_counters(completed.counters)


def test_pair_list_approve_and_complete_public_outputs_do_not_leak_sensitive_values() -> None:
    request, approval, _config = _pairing_fixture()
    public_payloads = (
        list_pending_pairing_requests([request], now=NOW),
        approval.to_public_dict(),
        complete_pairing(approval, pairing_code=FIXTURE_PAIRING_CODE, now=NOW).to_dict(),
    )
    combined = repr(public_payloads)

    for forbidden in (FIXTURE_SECRET, FIXTURE_PAIRING_CODE, FIXTURE_TOKEN):
        assert forbidden not in combined
    for payload in public_payloads:
        assert scan_for_qmt_sensitive_leaks(payload).leak_count == 0


@pytest.mark.parametrize(
    ("headers", "required_scope", "reason"),
    (
        (
            lambda: _headers(
                timestamp=int(
                    (NOW - timedelta(seconds=DEFAULT_HMAC_CLOCK_SKEW_SECONDS + 1)).timestamp()
                )
            ),
            "health",
            QmtAuthBlockedReason.AUTH_TIMESTAMP_SKEW,
        ),
        (
            lambda: _headers(signature="bad-fixture-signature"),
            "health",
            QmtAuthBlockedReason.AUTH_SIGNATURE_MISMATCH,
        ),
        (
            lambda: _headers(),
            "account",
            QmtAuthBlockedReason.AUTH_SCOPE_DENIED,
        ),
    ),
)
def test_hmac_hard_blocks_timestamp_scope_and_signature_failures(
    headers: object,
    required_scope: str,
    reason: QmtAuthBlockedReason,
) -> None:
    _request, _approval, config = _pairing_fixture()

    result = validate_hmac_request(
        method="POST",
        path="/fixture",
        body=b"{}",
        headers=headers(),
        required_scope=required_scope,
        config=config,
        now=NOW,
        used_nonce_store=set(),
    )

    _assert_blocked(result, reason)


def test_hmac_hard_blocks_nonce_replay_client_not_approved_and_pairing_code_expiry(
) -> None:
    _request, approval, config = _pairing_fixture()
    nonce_store: set[str] = set()

    first = validate_hmac_request(
        method="POST",
        path="/fixture",
        body=b"{}",
        headers=_headers(nonce="nonce-replay-fixture"),
        required_scope="health",
        config=config,
        now=NOW,
        used_nonce_store=nonce_store,
    )
    replay = validate_hmac_request(
        method="POST",
        path="/fixture",
        body=b"{}",
        headers=_headers(nonce="nonce-replay-fixture"),
        required_scope="health",
        config=config,
        now=NOW,
        used_nonce_store=nonce_store,
    )
    not_approved = validate_hmac_request(
        method="POST",
        path="/fixture",
        body=b"{}",
        headers=_headers(nonce="nonce-unapproved-fixture"),
        required_scope="health",
        config=QmtAuthConfig(client_secrets={CLIENT_ID: FIXTURE_SECRET}),
        now=NOW,
        used_nonce_store=set(),
    )
    expired_approval = approve_pairing_request(
        create_pairing_request(
            client_name="fixture-client",
            source_context={
                "source_ip_hash": "fixture-source-ip-hash",
                "machine_fingerprint_hash": "fixture-machine-hash",
            },
            now=NOW - timedelta(seconds=60),
            request_id="pairing-request-expired-s05",
        ),
        scopes=("health",),
        now=NOW - timedelta(seconds=10),
        client_id=CLIENT_ID,
        secret_ref="<runtime-secret-ref>",
        pairing_code=FIXTURE_PAIRING_CODE,
        code_ttl_seconds=1,
    )
    expired_complete = complete_pairing(
        expired_approval,
        pairing_code=FIXTURE_PAIRING_CODE,
        now=NOW,
    )

    assert first.allowed is True
    assert first.trade_authorized is False
    _assert_blocked(replay, QmtAuthBlockedReason.AUTH_NONCE_REPLAY)
    _assert_blocked(not_approved, QmtAuthBlockedReason.AUTH_CLIENT_NOT_APPROVED)
    _assert_blocked(expired_complete, QmtAuthBlockedReason.AUTH_PAIRING_EXPIRED)
    assert approval.client_id == CLIENT_ID


def test_hmac_pass_identifies_caller_but_never_authorizes_trading_scopes() -> None:
    scopes = tuple(sorted(TRADING_AUTHORIZATION_SCOPES | {"health"}))
    _request, _approval, config = _pairing_fixture(scopes=scopes)

    for index, scope in enumerate(sorted(TRADING_AUTHORIZATION_SCOPES)):
        result = validate_hmac_request(
            method="POST",
            path=f"/{scope}",
            body=b"{}",
            headers=_headers(path=f"/{scope}", nonce=f"nonce-trading-{index}"),
            required_scope=scope,
            config=config,
            now=NOW,
            used_nonce_store=set(),
        )

        assert result.allowed is True
        assert result.caller_identified is True
        assert result.required_scope == scope
        assert result.trade_authorized is False
        assert result.simulation_authorized is False
        assert result.live_authorized is False
        assert result.account_authorized is False
        assert result.cancel_authorized is False
        assert result.adapter_call_allowed is False
        _assert_zero_counters(result.counters)


def test_no_auth_defaults_to_blocked_and_only_explicit_fixture_modes_pass_auth_mode(
) -> None:
    default_result = validate_auth_mode(
        QmtAuthConfig(auth_mode="no_auth"),
        runtime_context="fixture_test",
    )
    fixture_result = validate_auth_mode(
        QmtAuthConfig(auth_mode="no_auth", allow_no_auth_fixture=True),
        runtime_context="fixture_test",
    )
    debug_result = validate_auth_mode(
        QmtAuthConfig(auth_mode="no-auth", allow_no_auth_debug=True),
        runtime_context="local_debug",
    )
    temporary_result = validate_auth_mode(
        QmtAuthConfig(auth_mode="no_auth", allow_no_auth_temporary=True),
        runtime_context="explicit_temporary",
    )
    gateway_default = build_gateway_config()
    gateway_no_auth_blocked = validate_gateway_security(
        build_gateway_config({"auth": {"auth_mode": "no_auth"}})
    )
    gateway_no_auth_fixture = validate_gateway_security(
        build_gateway_config(
            {"auth": {"auth_mode": "no_auth", "allow_no_auth_fixture": True}}
        )
    )

    _assert_blocked(default_result, QmtAuthBlockedReason.AUTH_NO_AUTH_NOT_ALLOWED)
    for result in (fixture_result, debug_result, temporary_result):
        assert result.allowed is True
        assert result.trade_authorized is False
        assert result.adapter_call_allowed is False
        _assert_zero_counters(result.counters)

    assert gateway_default.auth_mode == DEFAULT_AUTH_MODE
    assert gateway_default.auth.pairing_request_ttl_seconds == 600
    assert gateway_default.auth.pairing_code_ttl_seconds == 300
    assert gateway_default.auth.hmac_clock_skew_seconds == 300
    assert gateway_default.auth.nonce_ttl_seconds == 600
    assert gateway_no_auth_blocked.accepted is False
    assert "auth_no_auth_not_allowed" in gateway_no_auth_blocked.reasons
    assert gateway_no_auth_fixture.accepted is True


def test_gateway_auth_config_defaults_and_ttl_contract_are_frozen() -> None:
    config = build_gateway_config(
        {
            "auth": {
                "auth_mode": "pairing_hmac",
                "pairing_request_ttl_seconds": 600,
                "pairing_code_ttl_seconds": 300,
                "hmac_clock_skew_seconds": 300,
                "nonce_ttl_seconds": 600,
            }
        }
    )
    invalid_ttl = validate_gateway_security(
        build_gateway_config({"auth": {"nonce_ttl_seconds": 0}})
    )

    assert {field.name for field in fields(GatewayAuthConfig)} == {
        "auth_mode",
        "pairing_request_ttl_seconds",
        "pairing_code_ttl_seconds",
        "hmac_clock_skew_seconds",
        "nonce_ttl_seconds",
        "allow_no_auth_debug",
        "allow_no_auth_fixture",
        "allow_no_auth_temporary",
    }
    assert config.auth.to_dict() == {
        "auth_mode": "pairing_hmac",
        "pairing_request_ttl_seconds": DEFAULT_PAIRING_REQUEST_TTL_SECONDS,
        "pairing_code_ttl_seconds": DEFAULT_PAIRING_CODE_TTL_SECONDS,
        "hmac_clock_skew_seconds": DEFAULT_HMAC_CLOCK_SKEW_SECONDS,
        "nonce_ttl_seconds": DEFAULT_NONCE_TTL_SECONDS,
        "allow_no_auth_debug": False,
        "allow_no_auth_fixture": False,
        "allow_no_auth_temporary": False,
    }
    assert invalid_ttl.accepted is False
    assert "auth_ttl_invalid" in invalid_ttl.reasons


def test_structured_and_text_redaction_remove_all_qmt_sensitive_values() -> None:
    raw_mapping = {
        "secret": FIXTURE_SECRET,
        "pairing_code": FIXTURE_PAIRING_CODE,
        "token": FIXTURE_TOKEN,
        "account": FIXTURE_ACCOUNT,
        "session": FIXTURE_SESSION,
        "cookie": FIXTURE_COOKIE,
        "trade_password": FIXTURE_TRADE_PASSWORD,
        "dotenv": ".env",
        "private_path": FIXTURE_PRIVATE_PATH,
        "nested": {
            "message": (
                f"token={FIXTURE_TOKEN} account={FIXTURE_ACCOUNT} "
                f"session={FIXTURE_SESSION}"
            )
        },
    }
    raw_text = (
        f"secret={FIXTURE_SECRET} pairing_code={FIXTURE_PAIRING_CODE} "
        f"token={FIXTURE_TOKEN} account={FIXTURE_ACCOUNT} "
        f"session={FIXTURE_SESSION} cookie={FIXTURE_COOKIE} "
        f"trade_password={FIXTURE_TRADE_PASSWORD} dotenv=.env "
        f"path={FIXTURE_PRIVATE_PATH}"
    )

    redacted_mapping, mapping_report = redact_qmt_mapping(raw_mapping)
    redacted_text, text_report = redact_qmt_text(raw_text)

    assert mapping_report.leak_count == 0
    assert mapping_report.redaction_status == "pass"
    assert text_report.leak_count == 0
    assert text_report.redaction_status == "pass"
    assert scan_for_qmt_sensitive_leaks(redacted_mapping).leak_count == 0
    assert scan_for_qmt_sensitive_leaks(redacted_text).leak_count == 0
    for forbidden in (
        FIXTURE_SECRET,
        FIXTURE_PAIRING_CODE,
        FIXTURE_TOKEN,
        FIXTURE_ACCOUNT,
        FIXTURE_SESSION,
        FIXTURE_COOKIE,
        FIXTURE_TRADE_PASSWORD,
        FIXTURE_PRIVATE_PATH,
    ):
        assert forbidden not in repr(redacted_mapping)
        assert forbidden not in redacted_text


def test_forbidden_operation_counters_are_all_zero() -> None:
    counters = collect_qmt_auth_safety_counters()

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
