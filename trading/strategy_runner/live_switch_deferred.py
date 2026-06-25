"""模拟盘到实盘切换的暂缓场景包合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


LIVE_SWITCH_DEFERRED_SCHEMA_VERSION = "runner-live-switch-deferred-scenario-pack-v1"


@dataclass(frozen=True, slots=True)
class LiveSwitchDecisionItem:
    """P6 后续必须人工决策的问题；当前不授权实现。"""

    decision_id: str
    question: str
    recommendation: str
    risk: str
    status: str = "deferred"

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "question": self.question,
            "recommendation": self.recommendation,
            "risk": self.risk,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class LiveSwitchDeferredScenarioPack:
    """P6 暂缓场景包；只记录后续讨论输入。"""

    status: str
    target_id: str
    scenario_refs: tuple[str, ...]
    decision_items: tuple[LiveSwitchDecisionItem, ...]
    blocked_reason: str = ""
    schema_version: str = LIVE_SWITCH_DEFERRED_SCHEMA_VERSION
    not_implementation: bool = True
    live_runtime_authorization_granted: bool = False
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "recorded"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "target_id": self.target_id,
            "scenario_refs": list(self.scenario_refs),
            "decision_items": [item.to_dict() for item in self.decision_items],
            "blocked_reason": self.blocked_reason,
            "not_implementation": self.not_implementation,
            "live_runtime_authorization_granted": self.live_runtime_authorization_granted,
            "safety_counters": dict(self.safety_counters),
        }


def build_deferred_live_switch_scenario_pack(
    *,
    target_id: str = "DEFERRED-SIMULATION-TO-LIVE-SWITCH",
    simulation_readiness_ref: str,
) -> LiveSwitchDeferredScenarioPack:
    """生成 P6 暂缓 live switch 场景包，不实现 live / small_live。"""

    if not simulation_readiness_ref:
        return LiveSwitchDeferredScenarioPack(
            status="blocked",
            target_id=target_id,
            scenario_refs=(),
            decision_items=(),
            blocked_reason="simulation_readiness_ref_missing",
        )
    return LiveSwitchDeferredScenarioPack(
        status="recorded",
        target_id=target_id,
        scenario_refs=(
            simulation_readiness_ref,
            "scenario:manual-approval-live-switch",
            "scenario:simulation-stability-window",
            "scenario:small-live-limited-scope",
            "scenario:kill-switch-and-cancel-only-rollback",
        ),
        decision_items=(
            LiveSwitchDecisionItem(
                "DQ-LIVE-001",
                "实盘切换使用独立 live gateway profile 还是复用 simulation gateway?",
                "使用独立 live gateway profile、独立端口和独立 env。",
                "复用 profile 可能导致 simulation runner 误连 live gateway。",
            ),
            LiveSwitchDecisionItem(
                "DQ-LIVE-002",
                "触发实盘切换需要什么稳定窗口和人工审批?",
                "要求连续模拟盘成功、reconciliation 通过、unresolved orders 为 0 后再人工审批。",
                "缺少稳定窗口会把未验证链路暴露给真实资金。",
            ),
            LiveSwitchDecisionItem(
                "DQ-LIVE-003",
                "首个 live 范围是 small_live 还是 full live?",
                "仅允许 small_live，且设置标的、方向、数量和金额上限。",
                "full live 初始范围过大，回滚和事故面不可控。",
            ),
            LiveSwitchDecisionItem(
                "DQ-LIVE-004",
                "live evidence 可以保存哪些内容?",
                "只保存脱敏摘要、计数、digest、refs 和风险接受记录。",
                "保存账号、资金、标的或订单原文会扩大敏感数据面。",
            ),
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
        "small_live_or_live_run": 0,
    }
