from __future__ import annotations

from trading.runner_control_contracts import SignalEvent
from trading.runner_control_cli import render_batch_ops_summary, render_ops_summary
from trading.runner_control_plane import RunnerControlPlane


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
