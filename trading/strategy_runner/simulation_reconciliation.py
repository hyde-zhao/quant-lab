"""多因子模拟运行后的离线对账汇总合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from trading.reconciliation import (
    ReconPhase,
    ReconciliationInput,
    ReconciliationReport,
    ReconciliationStatus,
    ThresholdConfig,
    build_report_candidate,
    reconcile,
    reconciliation_safety_counters,
    to_kill_switch_candidate,
)
from trading.strategy_runner.simulation_activation import SimulationExecutionEngineResult


SIMULATION_RECONCILIATION_SCHEMA_VERSION = "runner-simulation-reconciliation-v1"


@dataclass(frozen=True, slots=True)
class SimulationReconciliationRequest:
    """P4 对账输入；只消费脱敏摘要和 fixture / redacted snapshot refs。"""

    run_id: str
    target_portfolio_ref: str
    pre_positions_digest: str
    post_positions_digest: str
    execution_result: SimulationExecutionEngineResult
    local_state: Mapping[str, object]
    broker_facts: Mapping[str, object]
    broker_lake_facts: Mapping[str, object]
    thresholds: ThresholdConfig | Mapping[str, object]
    input_source: str = "fixture"
    phase: ReconPhase | str = ReconPhase.POST_MARKET
    schema_version: str = SIMULATION_RECONCILIATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SimulationReconciliationResult:
    """P4 对账输出；只保存 digest、计数和脱敏 refs。"""

    status: str
    run_id: str
    drift_bucket: str
    order_intent_count: int
    submitted_count: int
    cancelled_count: int
    rejected_count: int
    unknown_count: int
    unresolved_count: int
    manual_takeover_required: bool
    blocked_reason: str = ""
    report: ReconciliationReport | None = None
    schema_version: str = SIMULATION_RECONCILIATION_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: reconciliation_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "run_id": self.run_id,
            "drift_bucket": self.drift_bucket,
            "order_intent_count": self.order_intent_count,
            "submitted_count": self.submitted_count,
            "cancelled_count": self.cancelled_count,
            "rejected_count": self.rejected_count,
            "unknown_count": self.unknown_count,
            "unresolved_count": self.unresolved_count,
            "manual_takeover_required": self.manual_takeover_required,
            "blocked_reason": self.blocked_reason,
            "reconciliation_report_ref": self.report.report_id if self.report is not None else "",
            "reconciliation_status": self.report.status.value if self.report is not None else "",
            "report_candidate_ref": (
                build_report_candidate(self.report)["candidate_id"]
                if self.report is not None
                else ""
            ),
            "diff_summary": _redacted_diff_summary(self.report),
            "kill_switch_candidate": to_kill_switch_candidate(self.report) if self.report is not None else None,
            "safety_counters": dict(self.safety_counters),
        }


def reconcile_simulation_run(request: SimulationReconciliationRequest) -> SimulationReconciliationResult:
    """对 P3 结果做 post-run 对账；不查询账户、不写报告文件。"""

    missing = [
        name
        for name, value in (
            ("run_id", request.run_id),
            ("target_portfolio_ref", request.target_portfolio_ref),
            ("pre_positions_digest", request.pre_positions_digest),
            ("post_positions_digest", request.post_positions_digest),
        )
        if not value
    ]
    if missing:
        return _blocked(request, "required_field_missing:" + ",".join(missing), report=None)

    report = reconcile(
        ReconciliationInput(
            phase=request.phase,
            local_state_ref=f"local-state:{request.run_id}",
            broker_snapshot_ref=request.post_positions_digest,
            broker_lake_ref=f"broker-lake:{request.run_id}",
            local_state=dict(request.local_state),
            broker_facts=dict(request.broker_facts),
            broker_lake_facts=dict(request.broker_lake_facts),
            thresholds=request.thresholds,
            owner="runner",
            action="none",
            input_source=request.input_source,
            report_label="runner-simulation-reconciliation",
        )
    )
    unresolved = _unresolved_count(request.execution_result)
    if unresolved > 0:
        return _blocked(request, "unresolved_orders_present", report=report)
    if report.status in {
        ReconciliationStatus.REQUIRED_MISSING,
        ReconciliationStatus.MANUAL_REVIEW,
        ReconciliationStatus.KILL_SWITCH,
    }:
        return _blocked(request, "reconciliation_" + report.status.value, report=report)
    return _result(request, status="pass", blocked_reason="", report=report)


def _blocked(
    request: SimulationReconciliationRequest,
    reason: str,
    *,
    report: ReconciliationReport | None,
) -> SimulationReconciliationResult:
    return _result(
        request,
        status="blocked",
        blocked_reason=reason,
        report=report,
        manual_takeover_required=True,
    )


def _result(
    request: SimulationReconciliationRequest,
    *,
    status: str,
    blocked_reason: str,
    report: ReconciliationReport | None,
    manual_takeover_required: bool | None = None,
) -> SimulationReconciliationResult:
    unresolved = _unresolved_count(request.execution_result)
    return SimulationReconciliationResult(
        status=status,
        run_id=request.run_id,
        drift_bucket=_drift_bucket(report),
        order_intent_count=len(request.execution_result.actions),
        submitted_count=request.execution_result.submitted_count,
        cancelled_count=request.execution_result.cancelled_count,
        rejected_count=request.execution_result.rejected_count,
        unknown_count=request.execution_result.unknown_count,
        unresolved_count=unresolved,
        manual_takeover_required=bool(manual_takeover_required)
        if manual_takeover_required is not None
        else request.execution_result.manual_takeover_required,
        blocked_reason=blocked_reason,
        report=report,
    )


def _unresolved_count(execution: SimulationExecutionEngineResult) -> int:
    unresolved_statuses = {"unknown", "blocked"}
    return sum(
        1 for action in execution.actions if action.status in unresolved_statuses
    )


def _drift_bucket(report: ReconciliationReport | None) -> str:
    if report is None:
        return "drift:unknown"
    if report.status is ReconciliationStatus.PASS:
        return "drift:pass"
    if report.status is ReconciliationStatus.WARN:
        return "drift:warn"
    if report.status is ReconciliationStatus.MANUAL_REVIEW:
        return "drift:manual_review"
    if report.status is ReconciliationStatus.KILL_SWITCH:
        return "drift:kill_switch"
    return "drift:required_missing"


def _redacted_diff_summary(report: ReconciliationReport | None) -> list[dict[str, object]]:
    if report is None:
        return []
    return [
        {
            "diff_type": row.diff_type,
            "status": row.status.value,
            "diff_bucket": _diff_value_bucket(row.diff_value),
            "local_value_ref": row.local_value_ref,
            "broker_value_ref": row.broker_value_ref,
            "action": row.action,
        }
        for row in report.diff_rows
    ]


def _diff_value_bucket(value: float) -> str:
    current = abs(float(value))
    if current == 0:
        return "diff:zero"
    if current <= 1:
        return "diff:lte_1"
    if current <= 10:
        return "diff:lte_10"
    return "diff:gt_10"
