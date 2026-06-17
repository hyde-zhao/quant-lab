from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest

from trading.kill_switch import (
    CANCEL_PLAN_STATUS_PLANNED_ONLY,
    FREEZE_STATUS_FROZEN,
    RECOVERY_GATE_STATUS_BLOCKED,
    RECOVERY_GATE_STATUS_RECOVERABLE,
    KillSwitchReason,
    KillSwitchRequest,
    build_cancel_plan,
    kill_switch_safety_counters,
    kill_switch_trigger,
    recovery_gate,
    sensitive_raw_value_output_count,
)
from trading.monitoring import (
    HeartbeatDeadlinePolicy,
    HeartbeatErrorCode,
    HeartbeatEvent,
    HeartbeatStatus,
    heartbeat_check,
    monitoring_safety_counters,
)


NOW = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)

REQUIRED_ZERO_COUNTERS = {
    "qmt_api_call",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "credential_read",
    "real_broker_operation",
    "real_broker_lake_write",
    "real_lake_write",
    "provider_fetch",
    "publish",
    "dependency_change",
    "simulation_run",
    "real_snapshot_pull",
    "incident_persisted",
    "cancel_plan_executed",
    "new_order_allowed_after_freeze",
    "sensitive_raw_value_output",
}


def _open_state() -> dict[str, object]:
    return {
        "open_intents": [
            {
                "broker_order_ref": "mock-order-accepted",
                "order_intent_id": "intent-accepted",
                "state": "accepted",
                "symbol": "000001.SZ",
                "account_id": "6222000000000000",
            },
            {
                "order_intent_id": "intent-partial",
                "state": "partially_filled",
                "target_qty": 200,
            },
            {
                "broker_order_ref": "mock-order-filled",
                "order_intent_id": "intent-filled",
                "state": "filled",
            },
        ]
    }


def _assert_zero_counters(counters: object) -> None:
    current = dict(counters)  # type: ignore[arg-type]
    assert {key: current.get(key) for key in REQUIRED_ZERO_COUNTERS} == {
        key: 0 for key in REQUIRED_ZERO_COUNTERS
    }


def _assert_kill_switch_result(result: object) -> None:
    assert result.stop_new_orders is True
    assert result.new_order_allowed is False
    assert result.freeze_status == FREEZE_STATUS_FROZEN
    assert result.cancel_plan_status == CANCEL_PLAN_STATUS_PLANNED_ONLY
    assert result.cancel_plan.plan_status == CANCEL_PLAN_STATUS_PLANNED_ONLY
    assert result.cancel_plan.requires_authorization is True
    assert result.cancel_plan.executed is False
    assert result.cancel_plan.real_cancel_call == 0
    assert result.incident.persisted is False
    assert result.incident.storage_policy == "candidate_only_no_persist"
    assert result.recovery_gate_status == RECOVERY_GATE_STATUS_BLOCKED
    assert result.recovery_gate.new_order_allowed is False
    assert result.safety_counters["real_cancel_call"] == 0
    assert result.safety_counters["new_order_allowed_after_freeze"] == 0
    _assert_zero_counters(result.safety_counters)
    _assert_zero_counters(result.cancel_plan.safety_counters)
    _assert_zero_counters(result.incident.safety_counters)
    _assert_zero_counters(result.recovery_gate.safety_counters)


def test_heartbeat_timeout_generates_incident_and_kill_switch_contract() -> None:
    event = HeartbeatEvent(
        source="fixture-monitor",
        observed_at=NOW + timedelta(seconds=1),
        deadline_at=NOW,
        stage="simulation",
        status_ref="ok",
    )
    heartbeat = heartbeat_check(
        event,
        HeartbeatDeadlinePolicy(deadline_at=NOW, policy_ref="fixture:heartbeat"),
        now=NOW,
    )

    assert heartbeat.status is HeartbeatStatus.FAIL
    assert heartbeat.error_code is HeartbeatErrorCode.HEARTBEAT_TIMEOUT
    assert heartbeat.incident_candidate is not None
    assert heartbeat.incident_candidate.storage_policy == "candidate_only_no_persist"
    _assert_zero_counters(heartbeat.safety_counters)

    result = kill_switch_trigger(
        KillSwitchRequest(
            reason=heartbeat.error_code.value,
            stage="simulation",
            heartbeat_event_ref=heartbeat.incident_candidate.incident_id,
            open_intents_ref="fixture:oms-open-state",
        ),
        _open_state(),
        now=NOW,
    )

    assert result.kill_switch_reason is KillSwitchReason.HEARTBEAT_FAIL
    _assert_kill_switch_result(result)


@pytest.mark.parametrize(
    ("trigger_status", "expected_reason"),
    [
        ("manual_review", KillSwitchReason.RECON_MANUAL_REVIEW),
        ("kill_switch", KillSwitchReason.RECON_KILL_SWITCH),
    ],
)
def test_reconciliation_manual_review_or_kill_switch_triggers_full_contract(
    trigger_status: str,
    expected_reason: KillSwitchReason,
) -> None:
    request = KillSwitchRequest.from_reconciliation_candidate(
        {
            "candidate_id": f"kill-switch-candidate:report-{trigger_status}",
            "source_report_id": f"report:{trigger_status}",
            "trigger_status": trigger_status,
            "owner": "ops",
            "action": "trigger_kill_switch",
        },
        stage="simulation",
        open_intents_ref="fixture:oms-open-state",
    )

    result = kill_switch_trigger(request, _open_state(), now=NOW)

    assert result.kill_switch_reason is expected_reason
    assert result.incident.reason is expected_reason
    _assert_kill_switch_result(result)


@pytest.mark.parametrize(
    ("trigger_request", "expected_reason"),
    [
        (
            KillSwitchRequest(
                reason=KillSwitchReason.MANUAL_TRIGGER,
                stage="simulation",
                manual_trigger_ref="runbook:operator-stop",
                open_intents_ref="fixture:oms-open-state",
            ),
            KillSwitchReason.MANUAL_TRIGGER,
        ),
        (
            KillSwitchRequest(
                reason=KillSwitchReason.RISK_BLOCKED,
                stage="simulation",
                risk_event_ref="risk:block:cash-limit",
                open_intents_ref="fixture:oms-open-state",
            ),
            KillSwitchReason.RISK_BLOCKED,
        ),
    ],
)
def test_manual_trigger_and_risk_blocked_generate_freeze_cancel_incident_recovery(
    trigger_request: KillSwitchRequest,
    expected_reason: KillSwitchReason,
) -> None:
    result = kill_switch_trigger(trigger_request, _open_state(), now=NOW)

    assert result.kill_switch_reason is expected_reason
    assert result.stop_new_orders is True
    assert result.new_order_allowed is False
    assert result.cancel_plan.cancelable_order_refs == (
        "mock-order-accepted",
        "intent-partial",
    )
    _assert_kill_switch_result(result)


def test_cancel_plan_is_planned_only_refs_and_never_executes_cancel() -> None:
    plan = build_cancel_plan(
        _open_state(),
        "simulation",
        owner="ops",
        action="cancel_when_authorized",
        now=NOW,
    )

    assert plan.plan_status == CANCEL_PLAN_STATUS_PLANNED_ONLY
    assert plan.cancelable_order_refs == ("mock-order-accepted", "intent-partial")
    assert plan.requires_authorization is True
    assert plan.executed is False
    assert plan.real_cancel_call == 0
    assert plan.safety_counters["real_cancel_call"] == 0
    assert plan.safety_counters["cancel_plan_executed"] == 0
    assert {tuple(asdict(item).keys()) for item in plan.plan_items} == {
        ("order_ref", "owner", "action")
    }

    rendered = json.dumps(asdict(plan), ensure_ascii=False, sort_keys=True, default=str)
    assert "000001.SZ" not in rendered
    assert "6222000000000000" not in rendered
    _assert_zero_counters(plan.safety_counters)


def test_recovery_gate_requires_reconciliation_pass_and_manual_takeover_recorded() -> None:
    missing_takeover = recovery_gate("pass", "", evidence_ref="fixture:recovery")
    assert missing_takeover.recovery_gate_status == RECOVERY_GATE_STATUS_BLOCKED
    assert missing_takeover.new_order_allowed is False
    assert missing_takeover.missing_conditions == ("manual_takeover_status=recorded",)

    missing_reconciliation = recovery_gate("manual_review", "recorded")
    assert missing_reconciliation.recovery_gate_status == RECOVERY_GATE_STATUS_BLOCKED
    assert missing_reconciliation.new_order_allowed is False
    assert missing_reconciliation.missing_conditions == ("reconciliation_status=pass",)

    recoverable = recovery_gate("pass", "recorded")
    assert recoverable.recovery_gate_status == RECOVERY_GATE_STATUS_RECOVERABLE
    assert recoverable.new_order_allowed is True
    assert recoverable.missing_conditions == ()
    _assert_zero_counters(recoverable.safety_counters)


def test_incident_and_result_redact_sensitive_raw_values() -> None:
    sensitive_values = [
        "fixture-token-value",
        "fixture-password-value",
        "6222000000000000",
        "/home/test-user/private/broker-root",
        "BEGIN PRIVATE KEY",
    ]
    result = kill_switch_trigger(
        KillSwitchRequest(
            reason=KillSwitchReason.MANUAL_TRIGGER,
            stage="simulation",
            manual_trigger_ref=f"token:{sensitive_values[0]}",
            open_intents_ref=sensitive_values[3],
            evidence_refs=(sensitive_values[1], sensitive_values[4]),
            owner="ops",
        ),
        {
            "open_orders": [
                {
                    "broker_order_ref": sensitive_values[2],
                    "state": "accepted",
                }
            ]
        },
        now=NOW,
    )

    assert result.incident.redaction_status == "redacted"
    assert all(ref.startswith("redacted:") or ref.startswith("cancel-plan:") for ref in result.incident.evidence_refs)
    assert result.cancel_plan.cancelable_order_refs[0].startswith("redacted:")
    assert sensitive_raw_value_output_count(result, sensitive_values) == 0
    assert result.safety_counters["sensitive_raw_value_output"] == 0
    _assert_zero_counters(result.safety_counters)


def test_required_safety_counters_remain_zero_for_fixture_only_contracts() -> None:
    _assert_zero_counters(monitoring_safety_counters())
    _assert_zero_counters(kill_switch_safety_counters())
