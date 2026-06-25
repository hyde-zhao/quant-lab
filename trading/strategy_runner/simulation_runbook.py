"""模拟盘多因子策略运营 runbook 的离线 readiness 合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


SIMULATION_RUNBOOK_SCHEMA_VERSION = "runner-simulation-operational-runbook-v1"
RUNBOOK_REQUIRED_STEP_IDS: tuple[str, ...] = (
    "pre_market_check",
    "gateway_health",
    "runtime_profile_check",
    "target_portfolio_generation",
    "order_plan_review",
    "simulation_submit_cancel",
    "reconciliation",
    "exception_recovery",
    "eod_cancel_unfinished",
)


@dataclass(frozen=True, slots=True)
class SimulationRunbookStep:
    """单个 runbook 步骤。"""

    step_id: str
    title: str
    evidence_ref: str
    status: str = "pass"
    required: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "evidence_ref": self.evidence_ref,
            "status": self.status,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class SimulationOperationalRunbook:
    """P5 runbook readiness 输出；不构成 runtime 授权。"""

    status: str
    runbook_ref: str
    steps: tuple[SimulationRunbookStep, ...]
    blocked_reason: str = ""
    manual_takeover_actions: tuple[str, ...] = ()
    schema_version: str = SIMULATION_RUNBOOK_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())
    not_runtime_authorization: bool = True

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
            "runbook_ref": self.runbook_ref,
            "blocked_reason": self.blocked_reason,
            "steps": [step.to_dict() for step in self.steps],
            "manual_takeover_actions": list(self.manual_takeover_actions),
            "not_runtime_authorization": self.not_runtime_authorization,
            "safety_counters": dict(self.safety_counters),
        }


def build_simulation_operational_runbook(
    *,
    runbook_ref: str,
    steps: tuple[SimulationRunbookStep | Mapping[str, object], ...],
) -> SimulationOperationalRunbook:
    """检查 P5 runbook 是否覆盖模拟盘长期运行必需步骤。"""

    normalized = tuple(_step(step) for step in steps)
    if not runbook_ref:
        return _blocked(runbook_ref, normalized, "runbook_ref_missing")
    missing = tuple(
        step_id
        for step_id in RUNBOOK_REQUIRED_STEP_IDS
        if not any(step.step_id == step_id and step.required for step in normalized)
    )
    if missing:
        return _blocked(runbook_ref, normalized, "missing_required_steps:" + ",".join(missing))
    failed = tuple(step.step_id for step in normalized if step.required and step.status != "pass")
    if failed:
        return _blocked(runbook_ref, normalized, "required_step_not_pass:" + ",".join(failed))
    missing_evidence = tuple(step.step_id for step in normalized if step.required and not step.evidence_ref)
    if missing_evidence:
        return _blocked(runbook_ref, normalized, "missing_step_evidence:" + ",".join(missing_evidence))
    return SimulationOperationalRunbook(
        status="pass",
        runbook_ref=runbook_ref,
        steps=normalized,
        manual_takeover_actions=(
            "stop_new_orders",
            "cancel_unfinished_when_authorized",
            "record_manual_takeover",
            "rerun_reconciliation_before_resume",
        ),
    )


def _step(raw: SimulationRunbookStep | Mapping[str, object]) -> SimulationRunbookStep:
    if isinstance(raw, SimulationRunbookStep):
        return raw
    return SimulationRunbookStep(
        step_id=str(raw.get("step_id") or ""),
        title=str(raw.get("title") or raw.get("step_id") or ""),
        evidence_ref=str(raw.get("evidence_ref") or ""),
        status=str(raw.get("status") or "pass"),
        required=bool(raw.get("required", True)),
    )


def _blocked(
    runbook_ref: str,
    steps: tuple[SimulationRunbookStep, ...],
    reason: str,
) -> SimulationOperationalRunbook:
    return SimulationOperationalRunbook(
        status="blocked",
        runbook_ref=runbook_ref,
        steps=steps,
        blocked_reason=reason,
    )


def _zero_safety_counters() -> dict[str, int]:
    return {
        "credential_read": 0,
        "qmt_operation": 0,
        "qmt_api_call": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "provider_fetch": 0,
        "lake_write": 0,
        "publish": 0,
        "simulation_or_live_run": 0,
    }
