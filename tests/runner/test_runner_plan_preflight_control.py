from __future__ import annotations

from trading.runner_control_contracts import (
    AuthorizationRecord,
    ControlResultStatus,
    RunnerCommand,
)
from trading.runner_control_plane import RunnerControlPlane
from trading.runner_control_cli import render_preflight


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
