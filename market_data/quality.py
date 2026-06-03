"""CR017 复权质量辅助检查。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

ADJUSTMENT_JUMP_STATUS_PASS = "pass"
ADJUSTMENT_JUMP_STATUS_FAIL = "fail"

UNEXPLAINED_ADJUSTMENT_JUMP = "unexplained_adjustment_jump"


@dataclass(frozen=True, slots=True)
class AdjustmentJumpCheckResult:
    status: str
    passed: bool
    reason_code: str = ""
    field: str = ""
    observed_jump_ratio: float | None = None
    threshold: float = 0.5
    explained: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "reason_code": self.reason_code,
            "field": self.field,
            "observed_jump_ratio": self.observed_jump_ratio,
            "threshold": self.threshold,
            "explained": self.explained,
        }


def check_unexplained_adjustment_jump(
    metadata: Mapping[str, Any] | None,
    *,
    threshold: float = 0.5,
) -> AdjustmentJumpCheckResult:
    """检查复权因子跳变是否有显式解释；只消费调用方传入的 fixture metadata。"""

    payload = dict(metadata or {})
    observed = _observed_jump_ratio(payload)
    explained = _has_adjustment_explanation(payload)
    if observed is None or explained or abs(observed) <= threshold:
        return AdjustmentJumpCheckResult(
            status=ADJUSTMENT_JUMP_STATUS_PASS,
            passed=True,
            observed_jump_ratio=observed,
            threshold=threshold,
            explained=explained,
        )
    return AdjustmentJumpCheckResult(
        status=ADJUSTMENT_JUMP_STATUS_FAIL,
        passed=False,
        reason_code=UNEXPLAINED_ADJUSTMENT_JUMP,
        field="adjustment_jump_ratio",
        observed_jump_ratio=observed,
        threshold=threshold,
        explained=False,
    )


def _observed_jump_ratio(payload: Mapping[str, Any]) -> float | None:
    explicit = _to_float(payload.get("adjustment_jump_ratio"))
    if explicit is not None:
        return explicit

    previous = _to_float(
        payload.get("previous_adj_factor")
        if "previous_adj_factor" in payload
        else payload.get("previous_factor")
    )
    current = _to_float(
        payload.get("adj_factor")
        if "adj_factor" in payload
        else payload.get("current_adj_factor")
    )
    if previous is None or current is None or previous <= 0:
        return None
    return (current / previous) - 1.0


def _has_adjustment_explanation(payload: Mapping[str, Any]) -> bool:
    for key in (
        "adjustment_jump_explained",
        "corporate_action_explained",
    ):
        value = payload.get(key)
        if isinstance(value, bool):
            if value:
                return True
        elif str(value or "").strip().lower() in {"1", "true", "yes", "y"}:
            return True
    return any(
        str(payload.get(key) or "").strip()
        for key in (
            "adjustment_event_id",
            "corporate_action_id",
            "adjustment_explanation_code",
            "jump_explanation_code",
        )
    )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


__all__ = [
    "ADJUSTMENT_JUMP_STATUS_FAIL",
    "ADJUSTMENT_JUMP_STATUS_PASS",
    "UNEXPLAINED_ADJUSTMENT_JUMP",
    "AdjustmentJumpCheckResult",
    "check_unexplained_adjustment_jump",
]
