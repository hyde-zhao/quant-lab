"""CR138 Runner control plane 本地实现。

该实现只生成计划、预检、状态和证据摘要，不启动 runtime、不连接 gateway、
不调用 QMT / MiniQMT / XtQuant、不读取账户或凭据。
"""

from __future__ import annotations

from dataclasses import replace
from typing import Mapping, Sequence

from trading.runner_control_contracts import (
    AuthorizationRecord,
    BatchOpsSummary,
    BatchPreflightResult,
    ControlResultStatus,
    IncidentRecord,
    OpsSummary,
    OrderIntentDraft,
    PreflightResult,
    RebalancePlan,
    ReviewSummary,
    RunEvidence,
    RunPlan,
    RunPlanBatch,
    RunState,
    RunStateValue,
    RunnerCommand,
    RunnerCommandResult,
    SignalEvent,
    StrategyChangePlan,
    build_authorization_record,
    collect_no_real_operation_counters,
    new_audit_record,
    require_scope,
    stable_id,
)


class RunnerControlPlane:
    """内存态 Runner 控制面。"""

    def __init__(self) -> None:
        self._seen_commands: dict[str, str] = {}
        self._seen_events: set[str] = set()
        self.run_states: dict[str, RunState] = {}

    def build_run_plan(self, request: Mapping[str, object]) -> RunPlan:
        strategy_id = str(request.get("strategy_id") or "")
        target_date = str(request.get("target_date") or request.get("trade_date") or "")
        run_id = str(request.get("run_id") or stable_id("run", strategy_id, target_date))
        audit = new_audit_record(
            actor=str(request.get("actor") or "operator"),
            action="build_run_plan",
            scope="runner:plan",
            result="accepted",
            request_id=str(request.get("request_id") or ""),
        )
        plan = RunPlan(
            run_id=run_id,
            strategy_id=strategy_id,
            strategy_version=str(request.get("strategy_version") or ""),
            data_release_ref=str(request.get("data_release_ref") or ""),
            target_date=target_date,
            mode_request=str(request.get("mode_request") or "dry_run_review"),
            authorization_ref=str(request.get("authorization_ref") or ""),
            request_id=audit.request_id,
            audit_id=audit.audit_id,
        )
        self.run_states.setdefault(
            run_id,
            RunState(run_id=run_id, state=RunStateValue.PLANNED, audit_id=audit.audit_id),
        )
        return plan

    def build_run_plan_batch(
        self,
        requests: Sequence[Mapping[str, object]],
        *,
        batch_id: str = "",
        local_registry_ref: str = "",
    ) -> RunPlanBatch:
        plans = tuple(self.build_run_plan(request) for request in requests)
        current_batch_id = batch_id or stable_id("batch", *(plan.run_id for plan in plans))
        return RunPlanBatch(
            batch_id=current_batch_id,
            plans=plans,
            batch_policy="fail_closed",
            aggregate_status="planned",
            local_registry_ref=local_registry_ref,
        )

    def run_preflight(
        self,
        plan: RunPlan,
        *,
        gateway_health: Mapping[str, object] | object | None = None,
        auth: AuthorizationRecord | Mapping[str, object] | None = None,
        risk_prerequisites_passed: bool = True,
    ) -> PreflightResult:
        blocked: list[str] = []
        if not plan.strategy_id:
            blocked.append("strategy_missing")
        if not plan.data_release_ref:
            blocked.append("data_release_missing")

        health_status = _field_value(gateway_health, "status") or _field_value(gateway_health, "state")
        healthy = _field_bool(gateway_health, "healthy", default=health_status in {"healthy", "ready"})
        if health_status in {"degraded", "unhealthy", "unavailable", "stale"}:
            blocked.append("gateway_unavailable")
        elif gateway_health is not None and not healthy:
            blocked.append("gateway_unavailable")

        current_auth = build_authorization_record(auth, scope="runner:control")
        auth_block = require_scope("runner:control", current_auth, request_id=plan.request_id, audit_id=plan.audit_id)
        if auth_block is not None:
            blocked.append(auth_block.blocked_reason)
        if not risk_prerequisites_passed:
            blocked.append("risk_gate_blocked")

        status = ControlResultStatus.PASS if not blocked else ControlResultStatus.BLOCKED
        if blocked == ["gateway_unavailable"]:
            status = ControlResultStatus.MANUAL_REVIEW
        result = PreflightResult(
            run_id=plan.run_id,
            status=status,
            blocked_reasons=tuple(dict.fromkeys(blocked)),
            gateway_health_ref=str(_field_value(gateway_health, "capabilities_ref") or health_status),
            auth_status=current_auth.status if isinstance(current_auth.status, str) else current_auth.status.value,
            audit_id=plan.audit_id,
            adapter_calls=0,
            counters=collect_no_real_operation_counters(),
        )
        if result.blocked:
            self.run_states[plan.run_id] = RunState(
                run_id=plan.run_id,
                state=RunStateValue.BLOCKED,
                gateway_status=health_status,
                blocked_reasons=result.blocked_reasons,
                audit_id=plan.audit_id,
            )
        return result

    def run_batch_preflight(
        self,
        batch: RunPlanBatch,
        *,
        gateway_health: Mapping[str, object] | object | None = None,
        auth: AuthorizationRecord | Mapping[str, object] | None = None,
    ) -> BatchPreflightResult:
        results = tuple(
            self.run_preflight(plan, gateway_health=gateway_health, auth=auth)
            for plan in batch.plans
        )
        reasons = tuple(
            dict.fromkeys(reason for result in results for reason in result.blocked_reasons)
        )
        aggregate = "pass" if all(result.passed for result in results) else "blocked"
        return BatchPreflightResult(
            batch_id=batch.batch_id,
            per_run_results=results,
            aggregate_status=aggregate,
            aggregate_blocked_reasons=reasons,
            adapter_calls=0,
            counters=collect_no_real_operation_counters(),
        )

    def submit_runner_command(
        self,
        command: RunnerCommand,
        *,
        auth: AuthorizationRecord | Mapping[str, object] | None = None,
    ) -> RunnerCommandResult:
        if command.idempotency_key in self._seen_commands:
            return RunnerCommandResult(
                command_id=command.command_id,
                run_id=command.run_id,
                status=ControlResultStatus.DUPLICATE,
                audit_id=command.audit_id,
                duplicate_of=self._seen_commands[command.idempotency_key],
            )
        auth_block = require_scope(command.scope_required, auth, request_id=command.request_id, audit_id=command.audit_id)
        if auth_block is not None:
            return RunnerCommandResult(
                command_id=command.command_id,
                run_id=command.run_id,
                status=ControlResultStatus.BLOCKED,
                blocked_reason=auth_block.blocked_reason,
                audit_id=command.audit_id,
                adapter_calls=0,
            )
        self._seen_commands[command.idempotency_key] = command.command_id
        return RunnerCommandResult(
            command_id=command.command_id,
            run_id=command.run_id,
            status=ControlResultStatus.ACCEPTED,
            audit_id=command.audit_id,
            adapter_calls=0,
        )

    def ingest_signal_event(self, event: SignalEvent) -> dict[str, object]:
        identity = event.event_id or event.idempotency_key
        if not identity:
            return {"status": "rejected", "blocked_reason": "missing_event_identity", "adapter_calls": 0}
        if identity in self._seen_events:
            return {"status": "duplicate", "event_id": event.event_id, "adapter_calls": 0}
        self._seen_events.add(identity)
        self.run_states[event.run_id] = RunState(
            run_id=event.run_id,
            state=RunStateValue.RUNNING,
            latest_report_state="signal_received",
            audit_id=event.audit_id,
        )
        return {"status": "accepted", "event_id": event.event_id, "adapter_calls": 0}

    def build_rebalance_intent(
        self,
        *,
        run_id: str,
        target_summary: str,
        current_summary_ref: str,
        risk_status: str,
        symbols: Sequence[str] = (),
    ) -> RebalancePlan:
        if risk_status != "pass":
            return RebalancePlan(
                run_id=run_id,
                status="manual_review",
                target_summary=target_summary,
                current_summary_ref=current_summary_ref,
                risk_status=risk_status,
                blocked_reasons=("risk_gate_blocked",),
            )
        drafts = tuple(
            OrderIntentDraft(
                intent_id=stable_id("intent-draft", run_id, symbol),
                run_id=run_id,
                side="target",
                qty_policy="rebalance_to_target",
                symbol_ref=f"symbol-ref:{index}",
            )
            for index, symbol in enumerate(symbols)
        )
        return RebalancePlan(
            run_id=run_id,
            status="draft_only",
            target_summary=target_summary,
            current_summary_ref=current_summary_ref,
            risk_status=risk_status,
            order_intent_drafts=drafts,
        )

    def update_run_state(
        self,
        run_id: str,
        *,
        gateway_status: str = "",
        report_state: str = "",
        blocked_reasons: Sequence[str] = (),
    ) -> RunState:
        state = RunStateValue.RUNNING
        reasons = tuple(blocked_reasons)
        if gateway_status in {"degraded", "unhealthy", "unavailable"}:
            state = RunStateValue.DEGRADED
        if report_state in {"unknown", "stale"}:
            state = RunStateValue.MANUAL_TAKEOVER
            reasons = tuple(dict.fromkeys((*reasons, f"report_{report_state}")))
        current = RunState(
            run_id=run_id,
            state=state,
            gateway_status=gateway_status,
            latest_report_state=report_state,
            blocked_reasons=reasons,
        )
        self.run_states[run_id] = current
        return current

    def build_ops_summary(self, run_id: str) -> OpsSummary:
        state = self.run_states.get(run_id, RunState(run_id=run_id, state=RunStateValue.PLANNED))
        next_action = "none"
        if state.state in {RunStateValue.DEGRADED, RunStateValue.MANUAL_TAKEOVER, RunStateValue.BLOCKED}:
            next_action = "manual_review"
        return OpsSummary(
            run_id=run_id,
            state=state.state.value if isinstance(state.state, RunStateValue) else str(state.state),
            gateway_status=state.gateway_status,
            latest_report_state=state.latest_report_state,
            blocked_reasons=state.blocked_reasons,
            next_manual_action=next_action,
            no_real_operation_counters=collect_no_real_operation_counters(),
        )

    def build_batch_ops_summary(
        self,
        batch: RunPlanBatch,
        *,
        latest_local_registry_ref: str = "",
    ) -> BatchOpsSummary:
        counts: dict[str, int] = {}
        blocked_refs: list[str] = []
        for plan in batch.plans:
            summary = self.build_ops_summary(plan.run_id)
            counts[summary.state] = counts.get(summary.state, 0) + 1
            if summary.blocked_reasons:
                blocked_refs.append(plan.run_id)
        return BatchOpsSummary(
            batch_id=batch.batch_id,
            run_count=len(batch.plans),
            status_counts=counts,
            blocked_run_refs=tuple(blocked_refs),
            latest_local_registry_ref=latest_local_registry_ref or batch.local_registry_ref,
            no_real_operation_counters=collect_no_real_operation_counters(),
        )

    def query_run_evidence(
        self,
        run_id: str,
        *,
        evidence_refs: Sequence[str],
        audit_ids: Sequence[str] = (),
    ) -> RunEvidence | BlockedResultLike:
        if any("raw" in ref.lower() for ref in evidence_refs):
            return BlockedResultLike("blocked", "sensitive_evidence")
        return RunEvidence(
            run_id=run_id,
            evidence_refs=tuple(evidence_refs),
            audit_ids=tuple(audit_ids),
            redaction_status="redacted",
        )

    def build_review_summary(
        self,
        run_id: str,
        *,
        period: str,
        metrics_summary: Mapping[str, object],
        incidents: Sequence[str] = (),
    ) -> ReviewSummary:
        follow_ups = tuple(f"follow-up:{item}" for item in incidents if item)
        return ReviewSummary(
            run_id=run_id,
            period=period,
            metrics_summary=metrics_summary,
            incidents=tuple(incidents),
            follow_up_candidates=follow_ups,
        )

    def record_incident(
        self,
        run_id: str,
        *,
        severity: str,
        state: str,
        recovery_plan_ref: str,
    ) -> IncidentRecord:
        incident = IncidentRecord(
            incident_id=stable_id("incident", run_id, severity, state, recovery_plan_ref),
            run_id=run_id,
            severity=severity,
            state=state,
            recovery_plan_ref=recovery_plan_ref,
        )
        current = self.run_states.get(run_id, RunState(run_id=run_id, state=RunStateValue.MANUAL_TAKEOVER))
        self.run_states[run_id] = replace(
            current,
            incident_refs=tuple(dict.fromkeys((*current.incident_refs, incident.incident_id))),
        )
        return incident

    def propose_strategy_change(
        self,
        *,
        change_type: str,
        diff_ref: str,
        rollback_target: str = "",
    ) -> StrategyChangePlan:
        if not rollback_target:
            return StrategyChangePlan(
                change_id=stable_id("strategy-change", change_type, diff_ref),
                change_type=change_type,
                diff_ref=diff_ref,
                rollback_target="",
                status="blocked",
                blocked_reason="rollback_target_missing",
                apply_allowed=False,
            )
        return StrategyChangePlan(
            change_id=stable_id("strategy-change", change_type, diff_ref, rollback_target),
            change_type=change_type,
            diff_ref=diff_ref,
            rollback_target=rollback_target,
            status="dry_run_ready",
            apply_allowed=False,
        )


class BlockedResultLike:
    def __init__(self, status: str, blocked_reason: str) -> None:
        self.status = status
        self.blocked_reason = blocked_reason
        self.adapter_calls = 0

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "adapter_calls": self.adapter_calls,
            "counters": collect_no_real_operation_counters(),
        }


def _field_value(source: Mapping[str, object] | object | None, key: str) -> str:
    if source is None:
        return ""
    if isinstance(source, Mapping):
        return str(source.get(key) or "")
    value = getattr(source, key, "")
    if hasattr(value, "value"):
        return str(value.value)
    return str(value or "")


def _field_bool(source: Mapping[str, object] | object | None, key: str, *, default: bool = False) -> bool:
    if source is None:
        return default
    if isinstance(source, Mapping):
        return bool(source.get(key, default))
    return bool(getattr(source, key, default))
