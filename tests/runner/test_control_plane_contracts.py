from __future__ import annotations

from trading.runner_control_contracts import (
    AuthorizationRecord,
    ControlResultStatus,
    RunnerCommand,
    SignalEvent,
)
from trading.runner_control_plane import RunnerControlPlane
from trading.runner_control_cli import render_batch_ops_summary, render_ops_summary, render_preflight


def _auth() -> AuthorizationRecord:
    return AuthorizationRecord(
        scope="runner:control",
        status="authorized",
        authorization_ref="auth:fixture",
    )


def test_build_run_plan_and_batch_preflight() -> None:
    control = RunnerControlPlane()
    batch = control.build_run_plan_batch(
        [
            {
                "strategy_id": "s1",
                "target_date": "2026-06-24",
                "data_release_ref": "data:fixture",
            },
            {
                "strategy_id": "s2",
                "target_date": "2026-06-24",
                "data_release_ref": "data:fixture",
            },
        ],
        batch_id="batch-cr138",
        local_registry_ref="registry:cr137",
    )
    result = control.run_batch_preflight(
        batch,
        gateway_health={"status": "healthy", "healthy": True},
        auth=_auth(),
    )

    assert batch.batch_id == "batch-cr138"
    assert len(batch.plans) == 2
    assert result.aggregate_status == "pass"
    assert all(item.adapter_calls == 0 for item in result.per_run_results)
    assert result.counters["qmt_operation"] == 0


def test_preflight_blocks_missing_authorization_and_missing_data_without_adapter_call() -> None:
    control = RunnerControlPlane()
    plan = control.build_run_plan({"strategy_id": "s1", "target_date": "2026-06-24"})

    result = control.run_preflight(plan, gateway_health={"status": "healthy"})
    text = render_preflight(result)

    assert result.blocked is True
    assert result.adapter_calls == 0
    assert set(result.blocked_reasons) == {"data_release_missing", "authorization_missing"}
    assert "adapter_calls=0" in text


def test_gateway_degraded_preflight_enters_manual_review() -> None:
    control = RunnerControlPlane()
    plan = control.build_run_plan(
        {
            "strategy_id": "s1",
            "target_date": "2026-06-24",
            "data_release_ref": "data:fixture",
        }
    )

    result = control.run_preflight(plan, gateway_health={"status": "degraded"}, auth=_auth())

    assert result.status is ControlResultStatus.MANUAL_REVIEW
    assert result.adapter_calls == 0
    assert result.blocked_reasons == ("gateway_unavailable",)


def test_runner_command_is_idempotent_and_scope_gated() -> None:
    control = RunnerControlPlane()
    command = RunnerCommand(
        command_id="cmd-1",
        run_id="run-1",
        command_type="start",
        idempotency_key="idem-1",
    )

    blocked = control.submit_runner_command(command)
    first = control.submit_runner_command(command, auth=_auth())
    duplicate = control.submit_runner_command(command, auth=_auth())

    assert blocked.status is ControlResultStatus.BLOCKED
    assert blocked.blocked_reason == "authorization_missing"
    assert first.status is ControlResultStatus.ACCEPTED
    assert duplicate.status is ControlResultStatus.DUPLICATE
    assert duplicate.duplicate_of == "cmd-1"


def test_signal_event_idempotency_and_run_state_tracking() -> None:
    control = RunnerControlPlane()
    event = SignalEvent(event_id="event-1", run_id="run-1", payload_ref="payload:redacted")

    accepted = control.ingest_signal_event(event)
    duplicate = control.ingest_signal_event(event)
    summary = control.build_ops_summary("run-1")

    assert accepted["status"] == "accepted"
    assert duplicate["status"] == "duplicate"
    assert summary.state == "running"
    assert "run_id=run-1" in render_ops_summary(summary)


def test_rebalance_risk_fail_produces_manual_review_without_order_submit() -> None:
    control = RunnerControlPlane()

    plan = control.build_rebalance_intent(
        run_id="run-1",
        target_summary="target:redacted",
        current_summary_ref="current:redacted",
        risk_status="blocked",
        symbols=("000001.SZ",),
    )

    assert plan.status == "manual_review"
    assert plan.order_intent_drafts == ()
    assert plan.blocked_reasons == ("risk_gate_blocked",)


def test_rebalance_pass_creates_order_intent_draft_only() -> None:
    control = RunnerControlPlane()

    plan = control.build_rebalance_intent(
        run_id="run-1",
        target_summary="target:redacted",
        current_summary_ref="current:redacted",
        risk_status="pass",
        symbols=("000001.SZ", "000002.SZ"),
    )

    assert plan.status == "draft_only"
    assert len(plan.order_intent_drafts) == 2
    assert all(draft.submit_allowed is False for draft in plan.order_intent_drafts)
    assert all(draft.cancel_allowed is False for draft in plan.order_intent_drafts)


def test_stale_report_enters_manual_takeover_and_batch_summary_stays_local() -> None:
    control = RunnerControlPlane()
    batch = control.build_run_plan_batch(
        [
            {"run_id": "run-1", "strategy_id": "s1", "target_date": "2026-06-24"},
            {"run_id": "run-2", "strategy_id": "s2", "target_date": "2026-06-24"},
        ],
        batch_id="batch-1",
    )

    state = control.update_run_state("run-1", gateway_status="healthy", report_state="stale")
    summary = control.build_ops_summary("run-1")
    batch_summary = control.build_batch_ops_summary(batch, latest_local_registry_ref="registry:redacted")

    assert state.state == "manual_takeover"
    assert summary.next_manual_action == "manual_review"
    assert summary.no_real_operation_counters["order_submit"] == 0
    assert batch_summary.latest_local_registry_ref == "registry:redacted"
    assert "batch_id=batch-1" in render_batch_ops_summary(batch_summary)


def test_run_evidence_blocks_raw_refs_and_allows_redacted_refs_only() -> None:
    control = RunnerControlPlane()

    blocked = control.query_run_evidence("run-1", evidence_refs=("raw:broker-log",))
    indexed = control.query_run_evidence("run-1", evidence_refs=("evidence:redacted",), audit_ids=("audit:1",))

    assert blocked.blocked is True
    assert blocked.blocked_reason == "sensitive_evidence"
    assert indexed.status == "indexed"
    assert indexed.redaction_status == "redacted"
    assert indexed.evidence_refs == ("evidence:redacted",)


def test_review_summary_links_unresolved_incidents_to_follow_up_candidates() -> None:
    control = RunnerControlPlane()
    incident = control.record_incident(
        "run-1",
        severity="high",
        state="unresolved",
        recovery_plan_ref="recovery:redacted",
    )
    summary = control.build_review_summary(
        "run-1",
        period="2026-06",
        metrics_summary={"return_summary_ref": "return:redacted"},
        incidents=(incident.incident_id,),
    )

    assert incident.incident_id.startswith("incident:")
    assert summary.incidents == (incident.incident_id,)
    assert summary.follow_up_candidates == (f"follow-up:{incident.incident_id}",)
    assert summary.redaction_status == "redacted"


def test_strategy_change_plan_requires_rollback_target_and_never_applies() -> None:
    control = RunnerControlPlane()

    blocked = control.propose_strategy_change(
        change_type="parameter_update",
        diff_ref="diff:redacted",
    )
    ready = control.propose_strategy_change(
        change_type="parameter_update",
        diff_ref="diff:redacted",
        rollback_target="strategy:previous",
    )

    assert blocked.status == "blocked"
    assert blocked.blocked_reason == "rollback_target_missing"
    assert blocked.apply_allowed is False
    assert ready.status == "dry_run_ready"
    assert ready.apply_allowed is False
