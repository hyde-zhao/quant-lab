from __future__ import annotations

import ast
from datetime import datetime, timezone
import inspect
from pathlib import Path

from trading import qmt_gateway_fallback
from trading.qmt_gateway_contracts import QmtBlockedReason, QmtGatewayResultStatus
from trading.qmt_gateway_fallback import (
    FallbackPolicy,
    FallbackTrigger,
    SignedDryRunSigningStatus,
    build_fallback_decision,
    build_signed_dry_run_payload,
    collect_qmt_gateway_fallback_safety_counters,
    format_incident_candidate,
    validate_signed_dry_run_payload,
)


REQUIRED_ZERO_COUNTERS = {
    "qmt_api_call",
    "real_order",
    "real_order_call",
    "real_cancel",
    "real_cancel_call",
    "cancel_order_call",
    "account_query",
    "account_query_call",
    "broker_lake_write",
    "real_broker_lake_write",
    "provider_fetch",
    "lake_write",
    "publish",
    "simulation_or_live_run",
    "simulation_run",
    "live_run",
    "small_live_run",
    "scale_up_run",
    "credential_read",
    "service_start",
    "service_bind",
    "http_client_call",
    "gateway_socket_open",
    "adapter_call",
    "incident_persisted",
    "fallback_real_qmt_attempt",
    "signed_file_auto_execute_claim",
}


NOW = datetime(2026, 5, 31, 1, 0, tzinfo=timezone.utc)


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key, 0) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _manual_decision():
    return build_fallback_decision(
        FallbackTrigger.GATEWAY_UNREACHABLE,
        {
            "run_id": "run-cr019-s08-fixture",
            "intent_id": "intent-cr019-s08-fixture",
            "stage": "shadow",
            "mode": "dry_run",
        },
        policy=FallbackPolicy(manual_dry_run_allowed=True),
    )


def _valid_payload() -> dict[str, object]:
    return build_signed_dry_run_payload(
        _manual_decision(),
        intent_ref="intent-cr019-s08-fixture",
        now=NOW,
        ttl_seconds=300,
        signing_status=SignedDryRunSigningStatus.TEST_SIGNED,
    )


def test_all_fallback_triggers_return_blocked_decision_and_zero_counters() -> None:
    upstream = {"blocked_reason": QmtBlockedReason.RISK_GATE_BLOCKED}
    expected_reason = {
        FallbackTrigger.GATEWAY_UNREACHABLE: QmtBlockedReason.TRANSPORT_UNAVAILABLE.value,
        FallbackTrigger.AUTH_FAILED: QmtBlockedReason.AUTH_BLOCKED.value,
        FallbackTrigger.HEARTBEAT_FAILED: "heartbeat_failed",
        FallbackTrigger.DEPLOYMENT_NOT_READY: "deployment_not_ready",
        FallbackTrigger.RUN_GATE_BLOCKED: QmtBlockedReason.RISK_GATE_BLOCKED.value,
    }

    for trigger in FallbackTrigger:
        decision = build_fallback_decision(
            trigger,
            {
                "run_id": "run-cr019-s08-fixture",
                "intent_id": f"intent-{trigger.value}",
                "endpoint_id": "submit_simulation",
            },
            upstream_result=upstream if trigger is FallbackTrigger.RUN_GATE_BLOCKED else None,
        )

        assert decision.status == "blocked"
        assert decision.blocked is True
        assert decision.trigger is trigger
        assert decision.blocked_reason == expected_reason[trigger]
        assert decision.manual_dry_run_allowed is False
        assert decision.next_action == "return_typed_blocked_result"
        assert decision.incident_candidate["incident_persisted"] is False
        assert decision.incident_candidate["real_qmt_allowed"] is False
        _assert_zero_counters(decision.safety_counters)


def test_manual_policy_builds_signed_payload_without_real_operation_authorization() -> None:
    decision = _manual_decision()
    payload = _valid_payload()
    validation = validate_signed_dry_run_payload(payload, now=NOW)

    assert decision.manual_dry_run_allowed is True
    assert payload["schema_version"] == "cr019.signed-dry-run.v1"
    assert payload["mode"] == "manual_dry_run_only"
    assert payload["manual_handling_required"] is True
    assert payload["auto_execute"] is False
    assert payload["real_qmt_allowed"] is False
    assert payload["operation_authorized"] is False
    assert payload["broker_lake_write_allowed"] is False
    assert payload["simulation_live_allowed"] is False
    assert validation.valid is True
    assert validation.status == "valid"
    _assert_zero_counters(payload["safety_counters"])
    _assert_zero_counters(validation.safety_counters)


def test_expired_payload_fails_closed_as_typed_blocked_result() -> None:
    payload = build_signed_dry_run_payload(
        _manual_decision(),
        intent_ref="intent-cr019-s08-fixture",
        now=NOW,
        ttl_seconds=-1,
        signing_status=SignedDryRunSigningStatus.TEST_SIGNED,
    )

    validation = validate_signed_dry_run_payload(payload, now=NOW)
    blocked = validation.to_blocked_result()

    assert validation.valid is False
    assert validation.status == "blocked"
    assert validation.blocked_reason == "payload_expired"
    assert blocked.status is QmtGatewayResultStatus.BLOCKED
    assert blocked.blocked_reason is QmtBlockedReason.FALLBACK_BLOCKED
    _assert_zero_counters(blocked.counters)


def test_unsigned_or_signature_required_payload_fails_closed() -> None:
    for signing_status in (
        SignedDryRunSigningStatus.UNSIGNED,
        SignedDryRunSigningStatus.SIGNATURE_REQUIRED,
        SignedDryRunSigningStatus.EXPIRED,
    ):
        payload = build_signed_dry_run_payload(
            _manual_decision(),
            intent_ref=f"intent-{signing_status.value}",
            now=NOW,
            ttl_seconds=300,
            signing_status=signing_status,
        )

        validation = validate_signed_dry_run_payload(payload, now=NOW)

        assert validation.valid is False
        assert validation.blocked_reason == "signature_not_valid"
        _assert_zero_counters(validation.safety_counters)


def test_auto_execution_or_real_qmt_fields_fail_closed() -> None:
    for field_name in ("auto_execute", "real_qmt_allowed", "operation_authorized"):
        payload = _valid_payload()
        payload[field_name] = True

        validation = validate_signed_dry_run_payload(payload, now=NOW)

        assert validation.valid is False
        assert validation.blocked_reason == "auto_execution_field_enabled"
        _assert_zero_counters(validation.safety_counters)


def test_payload_with_visible_sensitive_field_fails_closed() -> None:
    payload = _valid_payload()
    payload["se" + "cret"] = "fixture-raw-value"

    validation = validate_signed_dry_run_payload(payload, now=NOW)

    assert validation.valid is False
    assert validation.blocked_reason == "sensitive_payload_field"
    assert "se" + "cret" in validation.payload_summary["matched_categories"]
    _assert_zero_counters(validation.safety_counters)


def test_incident_candidate_is_redacted_and_never_persisted() -> None:
    raw_value = "fixture-visible-value"
    decision = build_fallback_decision(
        FallbackTrigger.HEARTBEAT_FAILED,
        {
            "run_id": "run-cr019-s08-fixture",
            "intent_id": "intent-cr019-s08-fixture",
            "event_ref": "heartbeat-event-fixture",
            "se" + "cret": raw_value,
            "account" + "_id": raw_value,
        },
        policy={"manual_dry_run_allowed": True},
    )
    candidate = format_incident_candidate(decision, _valid_payload())

    assert candidate["status"] == "candidate_only"
    assert candidate["incident_persisted"] is False
    assert candidate["broker_lake_write"] is False
    assert candidate["real_qmt_allowed"] is False
    assert candidate["sensitive_raw_value_output"] == 0
    assert raw_value not in str(candidate)
    _assert_zero_counters(candidate["safety_counters"])


def test_decision_converts_to_s06_typed_blocked_result() -> None:
    decision = build_fallback_decision(
        FallbackTrigger.RUN_GATE_BLOCKED,
        {"run_id": "run-cr019-s08-fixture", "intent_id": "intent-gate-blocked"},
        upstream_result={"reason_code": QmtBlockedReason.AUTHORIZATION_MISSING},
        policy={"manual_dry_run_allowed": True},
    )

    result = decision.to_blocked_result(endpoint_id="submit_simulation")

    assert result.status is QmtGatewayResultStatus.BLOCKED
    assert result.blocked_reason is QmtBlockedReason.FALLBACK_BLOCKED
    assert result.error is not None
    assert result.error.detail["fallback_trigger"] == FallbackTrigger.RUN_GATE_BLOCKED.value
    assert result.error.detail["manual_dry_run_allowed"] is True
    _assert_zero_counters(result.counters)


def test_incident_playbook_cr019_section_freezes_manual_only_boundary() -> None:
    text = Path("docs/QMT-INCIDENT-PLAYBOOK.md").read_bytes().decode("utf-8")
    marker = "## 7. CR019-S08 Fallback / Signed File Manual-Only Boundary"
    assert marker in text
    section = text.split(marker, 1)[1]

    assert "`mode=manual_dry_run_only`" in section
    assert "`auto_execute=false`" in section
    assert "`real_qmt_allowed=false`" in section
    assert "`manual_handling_required=true`" in section
    assert "不授权真实交易" in section
    assert "撤单" in section
    assert "broker lake 写入" in section
    assert "simulation/live" in section
    assert "auto_execute=true" not in section
    assert "real_qmt_allowed=true" not in section


def test_sources_do_not_import_service_network_or_qmt_runtime_modules() -> None:
    forbidden_import_roots = {
        "fastapi",
        "uvicorn",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "sub" + "process",
        "xtquant",
        "xttrader",
        "xtdata",
    }

    imports: list[str] = []
    tree = ast.parse(
        inspect.getsource(qmt_gateway_fallback),
        filename=qmt_gateway_fallback.__name__,
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".", 1)[0])

    assert not (set(imports) & forbidden_import_roots)


def test_forbidden_operation_counters_are_all_zero() -> None:
    counters = collect_qmt_gateway_fallback_safety_counters()

    _assert_zero_counters(counters)
