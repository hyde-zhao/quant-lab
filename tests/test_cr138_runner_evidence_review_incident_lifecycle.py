from __future__ import annotations

from trading.runner_control_plane import RunnerControlPlane


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
