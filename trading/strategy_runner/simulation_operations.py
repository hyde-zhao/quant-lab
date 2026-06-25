"""非交易窗口可冻结的 simulation 运维合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


SIMULATION_OPERATIONS_SCHEMA_VERSION = "runner-simulation-non-trading-operations-v1"


@dataclass(frozen=True, slots=True)
class SimulationOperationalItem:
    item_id: str
    title: str
    required_evidence: tuple[str, ...]
    fail_closed_action: str

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "required_evidence": list(self.required_evidence),
            "fail_closed_action": self.fail_closed_action,
        }


@dataclass(frozen=True, slots=True)
class SimulationStabilityWindowDefinition:
    window_id: str
    required_runs: int
    required_trading_days: int
    pass_criteria: tuple[str, ...]
    fail_criteria: tuple[str, ...]
    evidence_required: tuple[str, ...]
    schema_version: str = SIMULATION_OPERATIONS_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "window_id": self.window_id,
            "required_runs": self.required_runs,
            "required_trading_days": self.required_trading_days,
            "pass_criteria": list(self.pass_criteria),
            "fail_criteria": list(self.fail_criteria),
            "evidence_required": list(self.evidence_required),
            "safety_counters": dict(self.safety_counters),
            "not_runtime_authorization": True,
        }


def build_pre_trading_window_checklist() -> tuple[SimulationOperationalItem, ...]:
    """交易窗口前必须完成的 checklist；不启动 gateway。"""

    return (
        SimulationOperationalItem(
            "authorization_draft_ready",
            "授权草稿已准备，scope/time window/rollback/forbidden commands 明确。",
            ("authorization_draft_ref",),
            "block_runtime_start",
        ),
        SimulationOperationalItem(
            "strategy_admission_contract_pass",
            "策略准入包通过 runner 输入契约。",
            ("strategy_admission_contract_ref",),
            "block_p1",
        ),
        SimulationOperationalItem(
            "operator_fixture_pass",
            "operator fixture / plan-only / reconciliation-only 至少一种非交易窗口验证通过。",
            ("operator_fixture_evidence_ref",),
            "block_runtime_start",
        ),
        SimulationOperationalItem(
            "evidence_schema_pass",
            "P0-P4 evidence schema 和脱敏检查通过。",
            ("evidence_schema_validation_ref",),
            "block_evidence_publish",
        ),
        SimulationOperationalItem(
            "manual_takeover_ready",
            "manual takeover、kill-switch、日终撤未成和恢复条件已明确。",
            ("manual_takeover_checklist_ref",),
            "block_submit_cancel",
        ),
    )


def build_exception_recovery_matrix() -> tuple[SimulationOperationalItem, ...]:
    """离线异常演练矩阵；所有异常默认 fail closed。"""

    return (
        SimulationOperationalItem("authorization_expired", "授权缺失或过期。", ("authorization_ref",), "stop_runner_and_gateway"),
        SimulationOperationalItem("gateway_health_fail", "gateway health 不通过。", ("gateway_health_ref",), "do_not_enter_p3"),
        SimulationOperationalItem("capabilities_missing", "capabilities 缺少 positions / submit / cancel。", ("capabilities_ref",), "do_not_enter_p3"),
        SimulationOperationalItem("query_positions_redaction_fail", "positions 输出未脱敏。", ("redaction_validation_ref",), "discard_snapshot_and_block"),
        SimulationOperationalItem("risk_gate_blocked", "risk gate blocked。", ("risk_result_ref",), "do_not_submit"),
        SimulationOperationalItem("kill_switch_active", "kill switch 已激活。", ("kill_switch_ref",), "do_not_submit"),
        SimulationOperationalItem("order_submit_unknown", "submit 后状态 unknown。", ("execution_ref",), "manual_takeover"),
        SimulationOperationalItem("cancel_unknown", "cancel 后状态 unknown。", ("execution_ref",), "manual_takeover"),
        SimulationOperationalItem("recon_diff", "P4 对账差异。", ("reconciliation_ref",), "manual_takeover_or_kill_switch_candidate"),
    )


def build_default_stability_window_definition(
    *,
    required_runs: int = 5,
    required_trading_days: int = 3,
) -> SimulationStabilityWindowDefinition:
    """定义 simulation 日常使用前的稳定性窗口。"""

    return SimulationStabilityWindowDefinition(
        window_id="simulation-daily-readiness-window",
        required_runs=max(required_runs, 1),
        required_trading_days=max(required_trading_days, 1),
        pass_criteria=(
            "all_runs_have_authorization_ref",
            "p1_p2_p3_p4_evidence_schema_pass",
            "unknown_order_count_zero",
            "manual_takeover_records_closed",
            "gateway_stop_confirmed",
        ),
        fail_criteria=(
            "authorization_missing_or_expired",
            "raw_payload_or_secret_in_evidence",
            "unknown_order_unresolved",
            "reconciliation_diff_unclosed",
            "gateway_stop_unconfirmed",
        ),
        evidence_required=(
            "authorization_summary",
            "gateway_health_capabilities",
            "redacted_position_snapshot",
            "target_portfolio_summary",
            "order_plan_summary",
            "execution_summary",
            "reconciliation_summary",
            "gateway_stop_record",
        ),
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
