"""CR017 复权口径与消费边界合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from .contracts import (
    ADJUSTMENT_POLICY_HFQ,
    ADJUSTMENT_POLICY_QFQ,
    ADJUSTMENT_POLICY_RAW,
    ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
    ADJUSTMENT_POLICY_VALUES,
    CR017_FORBIDDEN_OPERATION_COUNTERS,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_RETURNS_ADJUSTED,
    CR018_FORBIDDEN_OPERATION_COUNTERS,
)

UNKNOWN_POLICY = "unknown_policy"
UNKNOWN_CONSUMER_CATEGORY = "unknown_consumer_category"
EXECUTION_REQUIRES_RAW = "execution_requires_raw"
LEGACY_QFQ_BASELINE_REQUIRED = "legacy_qfq_baseline_required"
CR018_ADJUSTMENT_READINESS_BLOCKED = "adjustment_readiness_blocked"
CR018_LEGACY_QFQ_BASELINE_OVERWRITE_BLOCKED = "legacy_qfq_baseline_overwrite_blocked"
CR018_ADJUSTMENT_REQUIRED_VIEW_IDS: tuple[str, ...] = (
    CR017_VIEW_PRICES_RAW,
    CR017_VIEW_ADJ_FACTOR,
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)
CR018_ADJUSTMENT_DERIVED_VIEW_IDS: tuple[str, ...] = (
    CR017_VIEW_PRICES_QFQ,
    CR017_VIEW_PRICES_HFQ,
    CR017_VIEW_RETURNS_ADJUSTED,
)


class AdjustmentPolicy(str, Enum):
    RAW = ADJUSTMENT_POLICY_RAW
    QFQ = ADJUSTMENT_POLICY_QFQ
    HFQ = ADJUSTMENT_POLICY_HFQ
    RETURNS_ADJUSTED = ADJUSTMENT_POLICY_RETURNS_ADJUSTED


class ConsumerCategory(str, Enum):
    CHART = "chart"
    LONG_HORIZON_RESEARCH = "long_horizon_research"
    FACTOR_RESEARCH = "factor_research"
    QMT_EXECUTION = "qmt_execution"
    MIGRATION = "migration"


POLICY_DISPLAY_LABELS: Mapping[AdjustmentPolicy, str] = {
    AdjustmentPolicy.RAW: "raw 未复权交易价",
    AdjustmentPolicy.QFQ: "qfq 前复权研究价",
    AdjustmentPolicy.HFQ: "hfq 后复权研究价",
    AdjustmentPolicy.RETURNS_ADJUSTED: "returns_adjusted 复权收益",
}

CONSUMER_ALLOWED_POLICIES: Mapping[ConsumerCategory, tuple[AdjustmentPolicy, ...]] = {
    ConsumerCategory.CHART: (
        AdjustmentPolicy.RAW,
        AdjustmentPolicy.QFQ,
        AdjustmentPolicy.HFQ,
        AdjustmentPolicy.RETURNS_ADJUSTED,
    ),
    ConsumerCategory.LONG_HORIZON_RESEARCH: (
        AdjustmentPolicy.QFQ,
        AdjustmentPolicy.HFQ,
        AdjustmentPolicy.RETURNS_ADJUSTED,
    ),
    ConsumerCategory.FACTOR_RESEARCH: (
        AdjustmentPolicy.QFQ,
        AdjustmentPolicy.HFQ,
        AdjustmentPolicy.RETURNS_ADJUSTED,
    ),
    ConsumerCategory.QMT_EXECUTION: (AdjustmentPolicy.RAW,),
    ConsumerCategory.MIGRATION: (
        AdjustmentPolicy.RAW,
        AdjustmentPolicy.QFQ,
        AdjustmentPolicy.HFQ,
        AdjustmentPolicy.RETURNS_ADJUSTED,
    ),
}


def zero_operation_counts() -> dict[str, int]:
    return dict(CR017_FORBIDDEN_OPERATION_COUNTERS)


def cr018_adjustment_operation_counts() -> dict[str, int]:
    counts = dict(CR018_FORBIDDEN_OPERATION_COUNTERS)
    counts["legacy_qfq_overwrite"] = 0
    counts["qmt_adjusted_execution_allowed"] = 0
    return counts


@dataclass(frozen=True, slots=True)
class PolicyNormalizationResult:
    allowed: bool
    policy: AdjustmentPolicy | None
    policy_id: str
    blocked_reason: str = ""
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "blocked_reason": self.blocked_reason,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    policy_id: str
    consumer_category: str
    display_label: str = ""
    blocked_reason: str = ""
    warning_reason: str = ""
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "policy_id": self.policy_id,
            "consumer_category": self.consumer_category,
            "display_label": self.display_label,
            "blocked_reason": self.blocked_reason,
            "warning_reason": self.warning_reason,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class MigrationSummary:
    legacy_qfq_baseline_preserved: bool
    legacy_qfq_baseline_ref: str
    view_id: str
    compatibility_entry: str
    single_policy_gate_status: str
    forbidden_overwrite_note: str
    migration_status: str = "summary_only"
    blocked_reason: str = ""
    legacy_qfq_baseline_overwrite_count: int = 0
    operation_counts: dict[str, int] = field(default_factory=zero_operation_counts)

    def to_dict(self) -> dict[str, object]:
        return {
            "legacy_qfq_baseline_preserved": self.legacy_qfq_baseline_preserved,
            "legacy_qfq_baseline_ref": self.legacy_qfq_baseline_ref,
            "view_id": self.view_id,
            "compatibility_entry": self.compatibility_entry,
            "single_policy_gate_status": self.single_policy_gate_status,
            "forbidden_overwrite_note": self.forbidden_overwrite_note,
            "migration_status": self.migration_status,
            "blocked_reason": self.blocked_reason,
            "legacy_qfq_baseline_overwrite_count": int(self.legacy_qfq_baseline_overwrite_count),
            "operation_counts": dict(self.operation_counts),
        }


def normalize_adjustment_policy(policy: str | AdjustmentPolicy) -> PolicyNormalizationResult:
    if isinstance(policy, AdjustmentPolicy):
        return PolicyNormalizationResult(allowed=True, policy=policy, policy_id=policy.value)
    if policy in ADJUSTMENT_POLICY_VALUES:
        normalized = AdjustmentPolicy(policy)
        return PolicyNormalizationResult(
            allowed=True,
            policy=normalized,
            policy_id=normalized.value,
        )
    return PolicyNormalizationResult(
        allowed=False,
        policy=None,
        policy_id=str(policy),
        blocked_reason=UNKNOWN_POLICY,
    )


def _normalize_consumer(consumer: str | ConsumerCategory) -> ConsumerCategory | None:
    if isinstance(consumer, ConsumerCategory):
        return consumer
    if consumer in {item.value for item in ConsumerCategory}:
        return ConsumerCategory(consumer)
    return None


def evaluate_consumer_policy(
    consumer: str | ConsumerCategory,
    policy: str | AdjustmentPolicy,
) -> PolicyDecision:
    category = _normalize_consumer(consumer)
    normalized = normalize_adjustment_policy(policy)
    category_value = consumer.value if isinstance(consumer, ConsumerCategory) else str(consumer)
    if category is None:
        return PolicyDecision(
            allowed=False,
            policy_id=normalized.policy_id,
            consumer_category=category_value,
            blocked_reason=UNKNOWN_CONSUMER_CATEGORY,
        )
    if not normalized.allowed or normalized.policy is None:
        return PolicyDecision(
            allowed=False,
            policy_id=normalized.policy_id,
            consumer_category=category.value,
            blocked_reason=normalized.blocked_reason,
        )
    allowed_policies = CONSUMER_ALLOWED_POLICIES[category]
    if normalized.policy not in allowed_policies:
        return PolicyDecision(
            allowed=False,
            policy_id=normalized.policy_id,
            consumer_category=category.value,
            display_label=POLICY_DISPLAY_LABELS[normalized.policy],
            blocked_reason=EXECUTION_REQUIRES_RAW
            if category == ConsumerCategory.QMT_EXECUTION
            else "consumer_policy_not_allowed",
        )
    return PolicyDecision(
        allowed=True,
        policy_id=normalized.policy_id,
        consumer_category=category.value,
        display_label=POLICY_DISPLAY_LABELS[normalized.policy],
    )


def render_policy_matrix(
    consumers: tuple[ConsumerCategory, ...] | None = None,
) -> tuple[PolicyDecision, ...]:
    consumer_values = consumers or tuple(ConsumerCategory)
    return tuple(
        evaluate_consumer_policy(consumer, policy)
        for consumer in consumer_values
        for policy in AdjustmentPolicy
    )


def build_legacy_qfq_migration_summary(
    legacy_qfq_baseline_ref: str | None,
) -> MigrationSummary:
    ref = str(legacy_qfq_baseline_ref or "")
    if not ref:
        return MigrationSummary(
            legacy_qfq_baseline_preserved=False,
            legacy_qfq_baseline_ref="",
            view_id=CR017_VIEW_PRICES_QFQ,
            compatibility_entry="legacy_qfq_readonly",
            single_policy_gate_status="required_missing",
            forbidden_overwrite_note="旧 qfq 基线缺少逻辑引用；不得扫描真实私有路径或覆盖旧报告。",
            blocked_reason=LEGACY_QFQ_BASELINE_REQUIRED,
        )
    return MigrationSummary(
        legacy_qfq_baseline_preserved=True,
        legacy_qfq_baseline_ref=ref,
        view_id=CR017_VIEW_PRICES_QFQ,
        compatibility_entry="legacy_qfq_readonly",
        single_policy_gate_status="single_policy_gate_required",
        forbidden_overwrite_note="旧 qfq 数据和旧报告只读保留；CR017 不执行覆盖、重算或 current pointer 发布。",
    )


def build_cr018_adjustment_publish_policy_metadata(
    release_id: str,
    *,
    readiness: Mapping[str, object] | object | None = None,
    legacy_qfq_baseline_ref: str | None = None,
) -> dict[str, object]:
    """构造 CR018-S05 复权 publish readiness policy metadata。

    该 helper 只组合调用方传入的 readiness / legacy metadata，不访问
    provider、lake、catalog current pointer、凭据或 QMT。
    """

    readiness_payload = _metadata_payload(readiness)
    migration = build_legacy_qfq_migration_summary(legacy_qfq_baseline_ref)
    operation_counts = cr018_adjustment_operation_counts()
    readiness_passed = bool(
        readiness_payload.get("passed")
        or readiness_payload.get("publish_allowed")
        or readiness_payload.get("production_publish_allowed_count") == 1
    )
    blocked_reason = _first_blocked_reason(readiness_payload)
    if not readiness_passed and not blocked_reason:
        blocked_reason = CR018_ADJUSTMENT_READINESS_BLOCKED
    if migration.blocked_reason:
        blocked_reason = migration.blocked_reason

    return {
        "schema_name": "cr018_adjustment_publish_policy_v1",
        "release_id": str(release_id),
        "required_view_ids": list(CR018_ADJUSTMENT_REQUIRED_VIEW_IDS),
        "derived_view_ids": list(CR018_ADJUSTMENT_DERIVED_VIEW_IDS),
        "research_adjustment_policies": [
            ADJUSTMENT_POLICY_QFQ,
            ADJUSTMENT_POLICY_HFQ,
            ADJUSTMENT_POLICY_RETURNS_ADJUSTED,
        ],
        "qmt_execution_price_policy": ADJUSTMENT_POLICY_RAW,
        "qmt_adjusted_execution_allowed_count": 0,
        "legacy_qfq_baseline_preserved": migration.legacy_qfq_baseline_preserved,
        "legacy_qfq_baseline_ref": migration.legacy_qfq_baseline_ref,
        "legacy_qfq_baseline_overwrite_count": 0,
        "legacy_qfq_compatibility_entry": migration.compatibility_entry,
        "publish_allowed": bool(readiness_passed and migration.legacy_qfq_baseline_preserved and not blocked_reason),
        "blocked_reason": blocked_reason,
        "operation_counts": operation_counts,
    }


def _first_blocked_reason(payload: Mapping[str, object]) -> str:
    for key in ("blocked_reason", "reason_code"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    for key in ("blocked_reasons", "issues"):
        rows = payload.get(key)
        if isinstance(rows, list | tuple):
            for item in rows:
                if isinstance(item, Mapping):
                    reason = str(item.get("reason_code") or item.get("code") or item.get("blocked_reason") or "").strip()
                    if reason:
                        return reason
    return ""


def _metadata_payload(value: Mapping[str, object] | object | None) -> dict[str, object]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


__all__ = [
    "ADJUSTMENT_POLICY_VALUES",
    "CONSUMER_ALLOWED_POLICIES",
    "CR018_ADJUSTMENT_DERIVED_VIEW_IDS",
    "CR018_ADJUSTMENT_READINESS_BLOCKED",
    "CR018_ADJUSTMENT_REQUIRED_VIEW_IDS",
    "CR018_LEGACY_QFQ_BASELINE_OVERWRITE_BLOCKED",
    "EXECUTION_REQUIRES_RAW",
    "LEGACY_QFQ_BASELINE_REQUIRED",
    "POLICY_DISPLAY_LABELS",
    "UNKNOWN_CONSUMER_CATEGORY",
    "UNKNOWN_POLICY",
    "AdjustmentPolicy",
    "ConsumerCategory",
    "MigrationSummary",
    "PolicyDecision",
    "PolicyNormalizationResult",
    "build_legacy_qfq_migration_summary",
    "build_cr018_adjustment_publish_policy_metadata",
    "cr018_adjustment_operation_counts",
    "evaluate_consumer_policy",
    "normalize_adjustment_policy",
    "render_policy_matrix",
    "zero_operation_counts",
]
