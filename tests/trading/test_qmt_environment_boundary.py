from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from trading.qmt_environment import (
    AdapterMode,
    EnvironmentCapability,
    EnvironmentErrorCode,
    EnvironmentStatus,
    NodeRole,
    QMT_FORBIDDEN_OPERATION_COUNTERS,
    assert_no_real_qmt_operations,
    evaluate_environment_boundary,
    scan_forbidden_broker_imports,
)
from trading.qmt_transport import (
    TransportErrorCode,
    TransportStatus,
    build_transport_payload,
    timeout_ack,
    unknown_ack,
    validate_payload_metadata,
)


def _valid_metadata(now: datetime | None = None) -> dict[str, str]:
    current = now or datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    return {
        "run_id": "run-cr015-s01-fixture",
        "strategy_id": "strategy-alpha",
        "payload_id": "payload-001",
        "payload_checksum": "sha256:fixture-checksum",
        "signature_ref": "signature-ref:fixture",
        "created_at": current.isoformat(),
        "expires_at": (current + timedelta(minutes=5)).isoformat(),
        "node_role": "research",
        "adapter_mode": "shadow",
    }


def test_qmt_environment_enums_cover_hld_contract() -> None:
    assert {role.value for role in NodeRole} == {"research", "trading"}
    assert {mode.value for mode in AdapterMode} == {
        "shadow",
        "dry_run",
        "mock",
        "simulation",
        "live_readonly",
        "small_live",
    }
    assert {status.value for status in EnvironmentStatus} == {
        "unsupported",
        "research_only",
        "trading_node_required",
        "mock_ready",
        "blocked",
    }
    assert {capability.value for capability in EnvironmentCapability} >= {
        "research_payload",
        "signed_file_drop",
        "mock_adapter",
        "trading_node_required",
        "real_qmt_forbidden",
    }
    assert {status.value for status in TransportStatus} == {
        "accepted",
        "rejected",
        "timeout",
        "unknown",
    }
    assert {error.value for error in TransportErrorCode} >= {
        "invalid_signature",
        "expired_payload",
        "mode_not_authorized",
        "credential_access_blocked",
        "real_qmt_blocked",
    }


def test_research_and_trading_nodes_are_offline_contract_only() -> None:
    research = evaluate_environment_boundary(NodeRole.RESEARCH, AdapterMode.SHADOW)
    assert research.status is EnvironmentStatus.RESEARCH_ONLY
    assert EnvironmentCapability.RESEARCH_PAYLOAD in research.capabilities
    assert EnvironmentCapability.SIGNED_FILE_DROP in research.capabilities
    assert research.error_code is None
    assert assert_no_real_qmt_operations(research.counters)

    trading = evaluate_environment_boundary("trading", "mock", qmt_available=True)
    assert trading.status is EnvironmentStatus.MOCK_READY
    assert EnvironmentCapability.MOCK_ADAPTER in trading.capabilities
    assert trading.error_code is None
    assert assert_no_real_qmt_operations(trading.counters)


def test_real_adapter_modes_are_recognized_but_blocked() -> None:
    research_live = evaluate_environment_boundary("research", "live_readonly")
    assert research_live.status is EnvironmentStatus.TRADING_NODE_REQUIRED
    assert research_live.error_code is EnvironmentErrorCode.MODE_NOT_AUTHORIZED
    assert EnvironmentCapability.REAL_QMT_FORBIDDEN in research_live.capabilities

    trading_simulation = evaluate_environment_boundary(
        "trading",
        "simulation",
        qmt_available=True,
    )
    assert trading_simulation.status is EnvironmentStatus.BLOCKED
    assert trading_simulation.error_code is EnvironmentErrorCode.REAL_QMT_BLOCKED
    assert assert_no_real_qmt_operations(trading_simulation.counters)


def test_transport_payload_accepts_only_desensitized_metadata() -> None:
    now = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    result = build_transport_payload(_valid_metadata(now), now=now)
    assert result.accepted is True
    assert result.payload is not None
    assert result.ack.status is TransportStatus.ACCEPTED
    assert result.sanitized_metadata == {
        "run_id": "run-cr015-s01-fixture",
        "strategy_id": "strategy-alpha",
        "payload_id": "payload-001",
        "payload_checksum": "sha256:fixture-checksum",
        "signature_ref": "signature-ref:fixture",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "node_role": "research",
        "adapter_mode": "shadow",
    }
    combined = " ".join(result.sanitized_metadata.values()).lower()
    for sensitive in ("token", "password", "cookie", "session", "account"):
        assert sensitive not in combined
    assert assert_no_real_qmt_operations(result.ack.counters)


def test_transport_payload_rejects_sensitive_unknown_expired_and_real_mode() -> None:
    now = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    sensitive = _valid_metadata(now) | {"token": "token=should-not-leak"}
    sensitive_result = build_transport_payload(sensitive, now=now)
    assert sensitive_result.accepted is False
    assert sensitive_result.ack.error_code is TransportErrorCode.CREDENTIAL_ACCESS_BLOCKED
    assert "should-not-leak" not in sensitive_result.ack.message

    unknown = _valid_metadata(now) | {"free_text": "not allowed"}
    unknown_result = build_transport_payload(unknown, now=now)
    assert unknown_result.accepted is False
    assert unknown_result.ack.error_code is TransportErrorCode.UNKNOWN_FIELD

    real_mode = _valid_metadata(now) | {"adapter_mode": "simulation"}
    real_mode_result = build_transport_payload(real_mode, now=now)
    assert real_mode_result.accepted is False
    assert real_mode_result.ack.error_code is TransportErrorCode.MODE_NOT_AUTHORIZED

    expired_metadata = _valid_metadata(now)
    expired_metadata["expires_at"] = (now - timedelta(seconds=1)).isoformat()
    expired = build_transport_payload(expired_metadata, now=now)
    assert expired.accepted is False
    assert expired.ack.error_code is TransportErrorCode.EXPIRED_PAYLOAD

    missing_signature_metadata = _valid_metadata(now)
    missing_signature_metadata["signature_ref"] = ""
    missing_signature = build_transport_payload(missing_signature_metadata, now=now)
    assert missing_signature.accepted is False
    assert missing_signature.ack.error_code is TransportErrorCode.MISSING_REQUIRED_FIELD


def test_validate_payload_metadata_and_ack_statuses_cover_error_paths() -> None:
    now = datetime(2026, 5, 28, 9, 30, tzinfo=UTC)
    result = build_transport_payload(_valid_metadata(now), now=now)
    assert result.payload is not None

    accepted = validate_payload_metadata(result.payload, now=now)
    assert accepted.status is TransportStatus.ACCEPTED
    assert accepted.error_code is None

    timeout = timeout_ack("payload-001", observed_at=now)
    assert timeout.status is TransportStatus.TIMEOUT
    assert timeout.payload_id == "payload-001"
    assert assert_no_real_qmt_operations(timeout.counters)

    unknown = unknown_ack("payload-001", observed_at=now)
    assert unknown.status is TransportStatus.UNKNOWN
    assert unknown.payload_id == "payload-001"
    assert assert_no_real_qmt_operations(unknown.counters)


def test_forbidden_broker_import_scan_detects_direct_imports_without_credentials(
    tmp_path: Path,
) -> None:
    unsafe_source = tmp_path / "unsafe_strategy.py"
    unsafe_source.write_text(
        "\n".join(
            [
                "from xtquant import xttrader",
                "def submit(trader):",
                "    return trader.order_stock('000001.SZ', 100, 10.0)",
            ]
        ),
        encoding="utf-8",
    )
    safe_source = tmp_path / "safe_strategy.py"
    safe_source.write_text(
        "\n".join(
            [
                "def build_intent(symbol, quantity):",
                "    return {'symbol': symbol, 'quantity': quantity}",
            ]
        ),
        encoding="utf-8",
    )

    unsafe = scan_forbidden_broker_imports([unsafe_source])
    assert unsafe.passed is False
    assert unsafe.violation_count == 2
    assert {violation.kind for violation in unsafe.violations} == {
        "from_import",
        "direct_call",
    }
    assert assert_no_real_qmt_operations(unsafe.counters)

    safe = scan_forbidden_broker_imports([safe_source, tmp_path / ".env"])
    assert safe.passed is False
    assert safe.violation_count == 1
    assert safe.violations[0].kind == "credential_path_rejected"
    assert assert_no_real_qmt_operations(safe.counters)


def test_cr015_s01_forbidden_real_operation_counters_remain_zero() -> None:
    expected = {
        "real_qmt_process_invocation": 0,
        "qmt_api_call": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "credential_read": 0,
        "dependency_change": 0,
        "real_broker_lake_write": 0,
    }
    assert dict(QMT_FORBIDDEN_OPERATION_COUNTERS) == expected
    assert assert_no_real_qmt_operations(QMT_FORBIDDEN_OPERATION_COUNTERS)
