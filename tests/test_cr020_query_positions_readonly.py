from __future__ import annotations

from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
import json
from typing import Mapping

from trading.qmt_auth import QmtAuthAdmissionDecision
from trading.qmt_endpoint_matrix import (
    CR020_READONLY_ENDPOINT_MATRIX_SCHEMA_VERSION,
    build_cr020_blocked_endpoint_matrix,
    get_cr020_query_positions_spec,
    is_cr020_readonly_endpoint_allowed,
)
from trading.qmt_gateway_contracts import (
    CR020_QUERY_POSITIONS_ENDPOINT_ID,
    CR020_QUERY_POSITIONS_PATH,
    CR020_QUERY_POSITIONS_SCHEMA_VERSION,
    CR020_QUERY_POSITIONS_SCOPE,
    QMT_QUERY_POSITIONS_COUNTER_FIELDS,
    QmtGatewayResultStatus,
    QmtQueryPositionsPayload,
    QmtQueryPositionsRequest,
    QmtRedactedPositionRecord,
    build_query_positions_request,
    collect_query_positions_safety_counters,
    redact_query_positions_payload,
)
from trading.qmt_gateway_service import (
    ADAPTER_UNAVAILABLE_REASON,
    TRANSPORT_TIMEOUT_REASON,
    dispatch_qmt_gateway_endpoint,
    handle_query_positions,
)
from trading.qmt_gateway_session import (
    QmtSessionBlockedReason,
    QmtSessionSnapshot,
    QmtSessionState,
)


NOW = datetime.now(tz=timezone.utc)

REQUIRED_ZERO_COUNTERS = set(QMT_QUERY_POSITIONS_COUNTER_FIELDS) - {
    "query_positions_read_attempt",
    "readonly_positions_adapter_call",
}


def _ready_session(**overrides: object) -> QmtSessionSnapshot:
    snapshot = QmtSessionSnapshot(
        state=QmtSessionState.READY,
        ready=True,
        credential_ref="<qmt-credential-ref-placeholder>",
        started_at=NOW.isoformat(),
        ready_at=NOW.isoformat(),
        expires_at=(NOW + timedelta(minutes=5)).isoformat(),
        runtime_status="fixture-ready",
    )
    return replace(snapshot, **overrides)


def _auth(
    *,
    accepted: bool = True,
    required_scope: str = CR020_QUERY_POSITIONS_SCOPE,
    blocked_reason: object | None = None,
) -> QmtAuthAdmissionDecision:
    return QmtAuthAdmissionDecision(
        accepted=accepted,
        status="accepted_for_next_gate" if accepted else "blocked",
        blocked_reason=blocked_reason,  # type: ignore[arg-type]
        endpoint_id=CR020_QUERY_POSITIONS_ENDPOINT_ID,
        required_scope=required_scope,
        redaction_status="pass",
    )


class _PositionsAdapter:
    def __init__(self, payload: Mapping[str, object] | None = None) -> None:
        self.payload = payload or {
            "positions": [
                {
                    "account_id": "123456789012",
                    "stock_code": "000001.SZ",
                    "volume": 1234,
                    "market_value": 56789.12,
                }
            ]
        }
        self.calls: list[QmtQueryPositionsRequest] = []

    def query_positions(
        self,
        request: QmtQueryPositionsRequest,
        session_snapshot: QmtSessionSnapshot,
    ) -> Mapping[str, object]:
        self.calls.append(request)
        assert session_snapshot.ready is True
        return self.payload


class _TimeoutAdapter:
    def query_positions(
        self,
        request: QmtQueryPositionsRequest,
        session_snapshot: QmtSessionSnapshot,
    ) -> Mapping[str, object]:
        raise TimeoutError("fixture timeout")


def _assert_forbidden_counters_zero(counters: Mapping[str, int]) -> None:
    current = dict(counters)
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def test_cr020_query_positions_models_and_endpoint_overlay_are_exact() -> None:
    spec = get_cr020_query_positions_spec()
    matrix = build_cr020_blocked_endpoint_matrix()

    assert CR020_QUERY_POSITIONS_SCHEMA_VERSION == (
        "cr020-s05-query-positions-readonly-v1"
    )
    assert {field.name for field in fields(QmtQueryPositionsRequest)} == {
        "run_id",
        "request_id",
        "redaction_label",
        "include_empty",
        "max_positions",
        "filter_ref",
        "payload",
        "schema_version",
    }
    assert {field.name for field in fields(QmtRedactedPositionRecord)} == {
        "position_ref",
        "instrument_ref",
        "side_ref",
        "quantity_bucket",
        "value_bucket",
        "schema_version",
    }
    assert {field.name for field in fields(QmtQueryPositionsPayload)} == {
        "position_count",
        "positions_digest",
        "items_redacted",
        "redaction_status",
        "raw_payload_emitted",
        "schema_version",
    }
    assert spec.endpoint_id == "query_positions"
    assert spec.method == "POST"
    assert spec.path == CR020_QUERY_POSITIONS_PATH
    assert spec.required_scope == CR020_QUERY_POSITIONS_SCOPE
    assert is_cr020_readonly_endpoint_allowed("query_positions", "qmt:positions:read")
    assert not is_cr020_readonly_endpoint_allowed("query_account", "qmt:account:read")
    assert not is_cr020_readonly_endpoint_allowed("query_positions", "qmt:account:read")
    assert matrix["query_positions"]["schema_version"] == (
        CR020_READONLY_ENDPOINT_MATRIX_SCHEMA_VERSION
    )
    assert matrix["query_positions"]["cr020_readonly_allowed"] is True
    blocked = {
        endpoint_id
        for endpoint_id, row in matrix.items()
        if endpoint_id != "query_positions" and row["blocked"] is True
    }
    assert {"query_account", "query_orders", "submit_live", "cancel_live"} <= blocked


def test_query_positions_success_calls_adapter_once_and_redacts_raw_positions() -> None:
    adapter = _PositionsAdapter()
    request = build_query_positions_request(
        {
            "run_id": "run-cr020-s05",
            "request_id": "request-cr020-s05",
            "filter_ref": "filter:fixture",
            "max_positions": 20,
        }
    )

    result = handle_query_positions(
        request,
        session_snapshot=_ready_session(),
        auth_admission=_auth(),
        adapter=adapter,
    )
    payload = result.to_dict()
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    query_payload = result.allowed_payload.data["query_positions"]  # type: ignore[union-attr]

    assert result.status is QmtGatewayResultStatus.ALLOWED
    assert result.allowed is True
    assert len(adapter.calls) == 1
    assert query_payload["position_count"] == 1  # type: ignore[index]
    assert query_payload["redaction_status"] == "pass"  # type: ignore[index]
    assert query_payload["raw_payload_emitted"] is False  # type: ignore[index]
    assert "123456789012" not in rendered
    assert "000001.SZ" not in rendered
    assert '"volume": 1234' not in rendered
    assert result.counters["readonly_positions_adapter_call"] == 1
    assert result.counters["query_positions_read_attempt"] == 1
    _assert_forbidden_counters_zero(result.counters)


def test_query_positions_fail_closed_before_adapter_for_auth_session_and_redaction() -> None:
    adapter = _PositionsAdapter()

    auth_blocked = handle_query_positions(
        {"run_id": "run-auth-blocked"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(accepted=False),
        adapter=adapter,
    )
    assert auth_blocked.blocked is True
    assert auth_blocked.reason_code == "auth_failed"
    assert adapter.calls == []

    session_blocked = handle_query_positions(
        {"run_id": "run-session-blocked"},
        session_snapshot=_ready_session(
            state=QmtSessionState.LOGIN_PENDING,
            ready=False,
            blocked_reason=QmtSessionBlockedReason.SESSION_NOT_READY,
        ),
        auth_admission=_auth(),
        adapter=adapter,
    )
    assert session_blocked.blocked is True
    assert session_blocked.reason_code == QmtSessionBlockedReason.SESSION_NOT_READY.value
    assert adapter.calls == []

    redaction_blocked = handle_query_positions(
        {"run_id": "run-redaction-blocked"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(),
        adapter=adapter,
        redaction_preflight={"accepted": False, "redaction_status": "failed"},
    )
    assert redaction_blocked.blocked is True
    assert redaction_blocked.reason_code == "redaction_failed"
    assert adapter.calls == []
    for result in (auth_blocked, session_blocked, redaction_blocked):
        _assert_forbidden_counters_zero(result.counters)


def test_query_positions_blocks_wrong_scope_endpoint_and_adapter_failure() -> None:
    adapter = _PositionsAdapter()

    wrong_scope = handle_query_positions(
        {"run_id": "run-wrong-scope"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(required_scope="qmt:account:read"),
        adapter=adapter,
    )
    assert wrong_scope.blocked is True
    assert wrong_scope.reason_code == "scope_denied"
    assert adapter.calls == []

    wrong_endpoint = dispatch_qmt_gateway_endpoint(
        "query_orders",
        {"run_id": "run-wrong-endpoint"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(),
        adapter=adapter,
    )
    assert wrong_endpoint.blocked is True
    assert wrong_endpoint.reason_code == "endpoint_not_supported"
    assert adapter.calls == []

    adapter_missing = handle_query_positions(
        {"run_id": "run-no-adapter"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(),
        adapter=None,
    )
    assert adapter_missing.blocked is True
    assert adapter_missing.reason_code == ADAPTER_UNAVAILABLE_REASON

    timeout = handle_query_positions(
        {"run_id": "run-timeout"},
        session_snapshot=_ready_session(),
        auth_admission=_auth(),
        adapter=_TimeoutAdapter(),
    )
    assert timeout.blocked is True
    assert timeout.reason_code == TRANSPORT_TIMEOUT_REASON


def test_redact_query_positions_payload_keeps_only_digest_refs_and_buckets() -> None:
    redacted = redact_query_positions_payload(
        {
            "positions": [
                {
                    "account_no": "1234567890123456",
                    "symbol": "600000.SH",
                    "quantity": 10,
                    "market_value": 9000,
                },
                {
                    "account_no": "1234567890123456",
                    "symbol": "000002.SZ",
                    "quantity": 120000,
                    "market_value": 2500000,
                },
            ]
        }
    )
    rendered = json.dumps(redacted.to_dict(), ensure_ascii=False, sort_keys=True)

    assert redacted.position_count == 2
    assert redacted.positions_digest.startswith("positions:")
    assert redacted.items_redacted[0].quantity_bucket == "1-100"
    assert redacted.items_redacted[1].quantity_bucket == "10000+"
    assert "1234567890123456" not in rendered
    assert "600000.SH" not in rendered
    assert "000002.SZ" not in rendered
    assert '"quantity": 10' not in rendered
    assert collect_query_positions_safety_counters()["raw_positions_emit"] == 0
