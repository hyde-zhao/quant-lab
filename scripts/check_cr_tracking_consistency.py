"""检查 CR tracking 索引、STATE 与 CR-019 follow-up 台账的一致性。

该脚本只做静态文本检查，不读取凭据、不访问数据湖、不执行真实 provider、
publish、QMT 或交易操作。它使用标准库实现，避免给工作流引入新依赖。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_CANDIDATES = (
    "CR-026",
)
REQUIRED_CANCELLED_QMT_CRS = ("CR-021", "CR-022", "CR-023", "CR-024")
REQUIRED_SPIKES = ("CR-027", "CR-028")
CR025_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
}
CR025_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
}
CR030_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
}
CR030_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
}
CR020_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
    "active-manual-validation-pending",
}
CR020_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
}
CR020_CANCELLED_STATUSES = {
    "deleted-by-user",
    "cancelled-user-deleted",
    "cancelled",
}
CR040_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
}
CR040_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
}
CR041_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
    "active-cp6-pass-ready-for-verification",
    "active-cp7-pass-with-risk-pending-cp8",
    "active-cp8-review-pending",
}
CR041_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
}
CR043_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-spike-running",
    "active-spike-review-pending",
    "active-story-execution",
}
CR043_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
    "closed-spike-complete",
}
CR044_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
    "active-cp6-pass-ready-for-verification",
    "active-cp7-pass-with-risk-pending-cp8",
    "active-cp8-review-pending",
}
CR044_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
    "closed-offline-admission-design-ready",
    "closed-blocked-by-account-permission",
    "closed-not-recommended",
}
CR045_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp2-review-pending",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
    "active-cp6-pass-ready-for-verification",
    "active-cp7-pass-with-risk-pending-cp8",
    "active-cp8-review-pending",
}
CR045_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
    "closed-readonly-bridge-skeleton-ready",
    "closed-blocked-by-runtime-authorization",
    "closed-not-recommended",
}
CR046_ACTIVE_STATUSES = {
    "active-cp2-intake",
    "active-cp2-review-pending",
    "active-cp3-hld",
    "active-cp3-hld-running",
    "active-cp3-review-pending",
    "active-cp4-story-planning-running",
    "active-cp4-pass-pending-lld",
    "active-cp5-lld-running",
    "active-cp5-review-pending",
    "active-story-execution",
    "active-cp6-pass-ready-for-verification",
    "active-cp7-pass-with-risk-pending-cp8",
    "active-cp8-review-pending",
}
CR046_CLOSED_STATUSES = {
    "closed",
    "closed-cp8-approved",
    "closed-current-delivery",
    "closed-framework-ready",
    "closed-blocked-by-runtime-authorization",
    "closed-not-recommended",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*\"?([^\"\n]+)\"?\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def check_project(project_root: Path) -> list[str]:
    failures: list[str] = []
    state_path = project_root / "process/STATE.md"
    index_path = project_root / "process/changes/CR-INDEX.yaml"
    tracking_path = project_root / "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md"
    cr019_path = project_root / "process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md"
    cr025_path = project_root / "process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md"
    cr029_path = project_root / "process/changes/CR-029-STAGE6-DATA-LAKE-ADMISSION-BENCHMARK-REAL-RUN-2026-05-31.md"
    cr030_path = project_root / "process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md"
    cr020_path = project_root / "process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md"
    cr040_path = project_root / "process/changes/CR-040-QMT-ROUTE-DELETION-BACKTRADER-PAPER-SIM-GOLDMINER-ADAPTER-2026-06-10.md"
    cr041_path = project_root / "process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md"
    cr043_path = project_root / "process/changes/CR-043-GOLDMINER-ADAPTER-SPIKE-2026-06-11.md"
    cr044_path = project_root / "process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md"
    cr045_path = project_root / "process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md"
    cr046_path = project_root / "process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md"

    state_text = read_text(state_path)
    index_text = read_text(index_path)
    tracking_text = read_text(tracking_path)
    cr019_text = read_text(cr019_path)
    cr025_text = read_text(cr025_path)
    cr029_text = read_text(cr029_path)
    cr030_text = read_text(cr030_path)
    cr020_text = read_text(cr020_path)
    cr040_text = read_text(cr040_path)
    cr041_text = read_text(cr041_path)
    cr043_text = read_text(cr043_path)
    cr044_text = read_text(cr044_path)
    cr045_text = read_text(cr045_path)
    cr046_text = read_text(cr046_path)

    require(bool(state_text), f"缺少状态文件: {state_path}", failures)
    require(bool(index_text), f"缺少 CR 索引: {index_path}", failures)
    require(bool(tracking_text), f"缺少 CR-019 follow-up 台账: {tracking_path}", failures)
    require(bool(cr019_text), f"缺少 CR-019 正式 CR: {cr019_path}", failures)
    require(bool(cr025_text), f"缺少 CR-025 正式 CR: {cr025_path}", failures)
    require(bool(cr029_text), f"缺少 CR-029 正式 CR: {cr029_path}", failures)
    require(bool(cr030_text), f"缺少 CR-030 正式 CR: {cr030_path}", failures)
    require(bool(cr020_text), f"缺少 CR-020 正式 CR: {cr020_path}", failures)
    require(bool(cr040_text), f"缺少 CR-040 正式 CR: {cr040_path}", failures)
    require(bool(cr041_text), f"缺少 CR-041 正式 CR: {cr041_path}", failures)
    require(bool(cr043_text), f"缺少 CR-043 正式 CR: {cr043_path}", failures)
    require(bool(cr044_text), f"缺少 CR-044 正式 CR: {cr044_path}", failures)
    require(bool(cr045_text), f"缺少 CR-045 正式 CR: {cr045_path}", failures)
    require(bool(cr046_text), f"缺少 CR-046 正式 CR: {cr046_path}", failures)

    if not all((state_text, index_text, tracking_text, cr019_text, cr025_text, cr029_text, cr030_text, cr020_text, cr040_text, cr041_text, cr043_text, cr044_text, cr045_text, cr046_text)):
        return failures

    require("cr_tracking:" in state_text, "STATE.md 缺少 cr_tracking 块", failures)
    require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
    require("follow_up_candidates:" in state_text, "STATE.md cr_tracking 缺少 follow_up_candidates", failures)
    require("spike_candidates:" in state_text, "STATE.md cr_tracking 缺少 spike_candidates", failures)
    require("stale_status_conflicts:" in state_text, "STATE.md cr_tracking 缺少 stale_status_conflicts", failures)

    require(frontmatter_value(cr019_text, "status") == "closed", "CR-019 正式 CR 未标记 closed", failures)
    cr025_status = frontmatter_value(cr025_text, "status")
    cr025_is_active = cr025_status in CR025_ACTIVE_STATUSES
    cr025_is_closed = cr025_status in CR025_CLOSED_STATUSES
    require(
        cr025_is_active or cr025_is_closed,
        (
            "CR-025 正式 CR 状态不在允许集合: "
            f"active={sorted(CR025_ACTIVE_STATUSES)}, closed={sorted(CR025_CLOSED_STATUSES)}; actual={cr025_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr025_text, "parent_cr") == "CR-019", "CR-025 缺少 parent_cr=CR-019", failures)
    require(
        frontmatter_value(cr025_text, "source_decision_id") == "D-CP8-CR019-05",
        "CR-025 缺少 source_decision_id=D-CP8-CR019-05",
        failures,
    )
    require(frontmatter_value(cr029_text, "status") == "closed", "CR-029 正式 CR 未标记 closed", failures)
    require(frontmatter_value(cr029_text, "parent_cr") == "CR-019", "CR-029 缺少 parent_cr=CR-019", failures)
    require(
        frontmatter_value(cr029_text, "source_decision_id") == "D-CP8-CR019-02",
        "CR-029 缺少 source_decision_id=D-CP8-CR019-02",
        failures,
    )
    cr030_status = frontmatter_value(cr030_text, "status")
    cr030_is_active = cr030_status in CR030_ACTIVE_STATUSES
    cr030_is_closed = cr030_status in CR030_CLOSED_STATUSES
    require(
        cr030_is_active or cr030_is_closed,
        (
            "CR-030 正式 CR 状态不在允许集合: "
            f"active={sorted(CR030_ACTIVE_STATUSES)}, closed={sorted(CR030_CLOSED_STATUSES)}; actual={cr030_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr030_text, "parent_cr") == "CR-019", "CR-030 缺少 parent_cr=CR-019", failures)
    require(
        frontmatter_value(cr030_text, "source_decision_id") == "D-CP8-CR019-05",
        "CR-030 缺少 source_decision_id=D-CP8-CR019-05",
        failures,
    )
    require("predecessor_cr: \"CR-025\"" in cr030_text, "CR-030 缺少 predecessor_cr=CR-025", failures)
    cr020_status = frontmatter_value(cr020_text, "status")
    cr020_is_active = cr020_status in CR020_ACTIVE_STATUSES
    cr020_is_closed = cr020_status in CR020_CLOSED_STATUSES
    cr020_is_cancelled = cr020_status in CR020_CANCELLED_STATUSES
    require(
        cr020_is_active or cr020_is_closed or cr020_is_cancelled,
        (
            "CR-020 正式 CR 状态不在允许集合: "
            f"active={sorted(CR020_ACTIVE_STATUSES)}, closed={sorted(CR020_CLOSED_STATUSES)}, "
            f"cancelled={sorted(CR020_CANCELLED_STATUSES)}; actual={cr020_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr020_text, "parent_cr") == "CR-019", "CR-020 缺少 parent_cr=CR-019", failures)
    require(
        frontmatter_value(cr020_text, "source_decision_id") == "D-CP8-CR019-02",
        "CR-020 缺少 source_decision_id=D-CP8-CR019-02",
        failures,
    )
    cr040_status = frontmatter_value(cr040_text, "status")
    cr040_is_active = cr040_status in CR040_ACTIVE_STATUSES
    cr040_is_closed = cr040_status in CR040_CLOSED_STATUSES
    require(
        cr040_is_active or cr040_is_closed,
        (
            "CR-040 正式 CR 状态不在允许集合: "
            f"active={sorted(CR040_ACTIVE_STATUSES)}, closed={sorted(CR040_CLOSED_STATUSES)}; actual={cr040_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr040_text, "parent_cr") == "CR-019", "CR-040 缺少 parent_cr=CR-019", failures)
    require(
        frontmatter_value(cr040_text, "source_decision_id") == "USER-20260610-NO-MINIQMT-GOLDMINER-ROUTE",
        "CR-040 缺少 source_decision_id=USER-20260610-NO-MINIQMT-GOLDMINER-ROUTE",
        failures,
    )
    cr041_status = frontmatter_value(cr041_text, "status")
    cr041_is_active = cr041_status in CR041_ACTIVE_STATUSES
    cr041_is_closed = cr041_status in CR041_CLOSED_STATUSES
    require(
        cr041_is_active or cr041_is_closed,
        (
            "CR-041 正式 CR 状态不在允许集合: "
            f"active={sorted(CR041_ACTIVE_STATUSES)}, closed={sorted(CR041_CLOSED_STATUSES)}; actual={cr041_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr041_text, "parent_cr") == "CR-040", "CR-041 缺少 parent_cr=CR-040", failures)
    require(
        frontmatter_value(cr041_text, "source_decision_id") == "USER-20260610-ACCEPT-CR039-START-CR041",
        "CR-041 缺少 source_decision_id=USER-20260610-ACCEPT-CR039-START-CR041",
        failures,
    )
    cr043_status = frontmatter_value(cr043_text, "status")
    cr043_is_active = cr043_status in CR043_ACTIVE_STATUSES
    cr043_is_closed = cr043_status in CR043_CLOSED_STATUSES
    require(
        cr043_is_active or cr043_is_closed,
        (
            "CR-043 正式 CR 状态不在允许集合: "
            f"active={sorted(CR043_ACTIVE_STATUSES)}, closed={sorted(CR043_CLOSED_STATUSES)}; actual={cr043_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr043_text, "parent_cr") == "CR-042", "CR-043 缺少 parent_cr=CR-042", failures)
    require(
        frontmatter_value(cr043_text, "source_decision_id") == "USER-20260611-START-CR043",
        "CR-043 缺少 source_decision_id=USER-20260611-START-CR043",
        failures,
    )
    cr044_status = frontmatter_value(cr044_text, "status")
    cr044_is_active = cr044_status in CR044_ACTIVE_STATUSES
    cr044_is_closed = cr044_status in CR044_CLOSED_STATUSES
    require(
        cr044_is_active or cr044_is_closed,
        (
            "CR-044 正式 CR 状态不在允许集合: "
            f"active={sorted(CR044_ACTIVE_STATUSES)}, closed={sorted(CR044_CLOSED_STATUSES)}; actual={cr044_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr044_text, "parent_cr") == "CR-043", "CR-044 缺少 parent_cr=CR-043", failures)
    require(
        frontmatter_value(cr044_text, "source_decision_id") == "USER-20260611-START-CR044",
        "CR-044 缺少 source_decision_id=USER-20260611-START-CR044",
        failures,
    )
    cr045_status = frontmatter_value(cr045_text, "status")
    cr045_is_active = cr045_status in CR045_ACTIVE_STATUSES
    cr045_is_closed = cr045_status in CR045_CLOSED_STATUSES
    require(
        cr045_is_active or cr045_is_closed,
        (
            "CR-045 正式 CR 状态不在允许集合: "
            f"active={sorted(CR045_ACTIVE_STATUSES)}, closed={sorted(CR045_CLOSED_STATUSES)}; actual={cr045_status!r}"
        ),
        failures,
    )
    require(frontmatter_value(cr045_text, "parent_cr") == "CR-044", "CR-045 缺少 parent_cr=CR-044", failures)
    require(
        frontmatter_value(cr045_text, "source_decision_id") == "USER-20260611-START-CR045",
        "CR-045 缺少 source_decision_id=USER-20260611-START-CR045",
        failures,
    )
    cr046_status = frontmatter_value(cr046_text, "status")
    cr046_is_active = cr046_status in CR046_ACTIVE_STATUSES
    cr046_is_closed = cr046_status in CR046_CLOSED_STATUSES
    require(
        cr046_is_active or cr046_is_closed,
        (
            "CR-046 正式 CR 状态不在允许集合: "
            f"active={sorted(CR046_ACTIVE_STATUSES)}, closed={sorted(CR046_CLOSED_STATUSES)}; actual={cr046_status!r}"
        ),
        failures,
    )

    for item_id in ("CR-025", "CR-029", "CR-030", "CR-040", "CR-041", "CR-043", "CR-044", "CR-045", "CR-046", "CR-020", *REQUIRED_CANDIDATES, *REQUIRED_CANCELLED_QMT_CRS, *REQUIRED_SPIKES):
        require(item_id in index_text, f"CR-INDEX.yaml 缺少 {item_id}", failures)
        require(item_id in state_text, f"STATE.md cr_tracking 缺少 {item_id}", failures)

    require('id: "CR-025"' in index_text, "CR-INDEX.yaml 缺少 CR-025 标准项", failures)
    require("CR-025" in tracking_text, "CR-019 follow-up 台账缺少 CR-025", failures)
    if cr025_is_active:
        require('active_change: "CR-025"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-025", failures)
    if cr025_is_closed:
        require("closed_crs:" in state_text, "STATE.md cr_tracking 缺少 closed_crs", failures)
        require("closed_crs:" in index_text, "CR-INDEX.yaml 缺少 closed_crs", failures)
        if cr046_is_active:
            require('active_change: "CR-046"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-046", failures)
        elif cr045_is_active:
            require('active_change: "CR-045"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-045", failures)
        elif cr040_is_active:
            require('active_change: "CR-040"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-040", failures)
        elif cr044_is_active:
            require('active_change: "CR-044"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-044", failures)
        elif cr043_is_active:
            require('active_change: "CR-043"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-043", failures)
        elif cr041_is_active:
            require('active_change: "CR-041"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-041", failures)
        elif cr030_is_active:
            require('active_change: "CR-030"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-030", failures)
        elif cr020_is_active:
            require('active_change: "CR-020"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-020", failures)
        else:
            require('active_change: ""' in state_text or 'active_change: "none"' in state_text, "STATE.md 顶层 active_change 未在 CR-025 关闭后清空", failures)
        require("| CR-025 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-025 标记为 closed", failures)
    if cr030_is_active:
        require('active_change: "CR-030"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-030", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr030_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-030 当前 active 状态: {cr030_status}", failures)
        require("| CR-030 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-030 标记为 active formal CR", failures)
    if cr030_is_closed:
        require("| CR-030 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-030 标记为 closed", failures)
    if cr040_is_active:
        require('active_change: "CR-040"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-040", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr040_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-040 当前 active 状态: {cr040_status}", failures)
        require("| CR-040 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-040 标记为 active formal CR", failures)
    if cr040_is_closed:
        require("| CR-040 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-040 标记为 closed", failures)
    if cr041_is_active:
        require('active_change: "CR-041"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-041", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr041_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-041 当前 active 状态: {cr041_status}", failures)
        require("| CR-041 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-041 标记为 active formal CR", failures)
    if cr041_is_closed:
        require("| CR-041 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-041 标记为 closed", failures)
    if cr043_is_active:
        require('active_change: "CR-043"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-043", failures)
        require('status: active-formal-cr' in index_text or 'status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: active-formal-cr' in state_text or 'status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr043_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-043 当前 active 状态: {cr043_status}", failures)
        require("| CR-043 |" in tracking_text and "| active |" in tracking_text, "CR-019 follow-up 台账未将 CR-043 标记为 active formal Spike", failures)
    if cr043_is_closed:
        require("| CR-043 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-043 标记为 closed", failures)
    if cr044_is_active:
        require('active_change: "CR-044"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-044", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr044_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-044 当前 active 状态: {cr044_status}", failures)
        require("| CR-044 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-044 标记为 active formal CR", failures)
    if cr044_is_closed:
        require("| CR-044 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-044 标记为 closed", failures)
    if cr045_is_active:
        require('active_change: "CR-045"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-045", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr045_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-045 当前 active 状态: {cr045_status}", failures)
        require("| CR-045 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-045 标记为 active formal CR", failures)
    if cr045_is_closed:
        require("| CR-045 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-045 标记为 closed", failures)
    if cr046_is_active:
        require('active_change: "CR-046"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-046", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr046_status in index_text, f"CR-INDEX.yaml 未记录 CR-046 当前 active 状态: {cr046_status}", failures)
        require("CR-046-FOLLOW-UP-TRACKING-2026-06-13.md" in state_text, "STATE.md 缺少 CR-046 follow-up tracking 路径", failures)
        require("CR-046-FOLLOW-UP-TRACKING-2026-06-13.md" in index_text, "CR-INDEX.yaml 缺少 CR-046 follow-up tracking 路径", failures)
    if cr046_is_closed:
        require("closed_crs:" in state_text, "STATE.md cr_tracking 缺少 closed_crs", failures)
        require("closed_crs:" in index_text, "CR-INDEX.yaml 缺少 closed_crs", failures)
    if cr020_is_active:
        require('active_change: "CR-020"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-020", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require(cr020_status in tracking_text, f"CR-019 follow-up 台账未记录 CR-020 当前 active 状态: {cr020_status}", failures)
        require("| CR-020 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-020 标记为 active formal CR", failures)
    if cr020_is_closed:
        require("| CR-020 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-020 标记为 closed", failures)
    if cr020_is_cancelled:
        require("cancelled_crs:" in state_text, "STATE.md cr_tracking 缺少 cancelled_crs", failures)
        require("cancelled_crs:" in index_text, "CR-INDEX.yaml 缺少 cancelled_crs", failures)
        require("| CR-020 | deleted-by-user |" in tracking_text, "CR-019 follow-up 台账未将 CR-020 标记为 deleted-by-user", failures)

    for item_id in REQUIRED_CANDIDATES:
        require(f'id: "{item_id}"' in index_text, f"CR-INDEX.yaml 缺少 candidate 标准项 {item_id}", failures)
        require(item_id in tracking_text, f"CR-019 follow-up 台账缺少 candidate {item_id}", failures)

    for item_id in REQUIRED_CANCELLED_QMT_CRS:
        require(f'id: "{item_id}"' in index_text, f"CR-INDEX.yaml 缺少 cancelled QMT 标准项 {item_id}", failures)
        require(item_id in tracking_text, f"CR-019 follow-up 台账缺少 cancelled QMT {item_id}", failures)
        require(f"| {item_id} |" in tracking_text and "cancelled-user-deleted" in tracking_text, f"CR-019 follow-up 台账未将 {item_id} 标记为 cancelled-user-deleted", failures)

    for item_id in REQUIRED_SPIKES:
        require(f'id: "{item_id}"' in index_text, f"CR-INDEX.yaml 缺少 spike 标准项 {item_id}", failures)
        require(item_id in tracking_text, f"CR-019 follow-up 台账缺少 spike {item_id}", failures)

    require("Related Formal CR" in tracking_text, "CR-019 follow-up 台账缺少 Related Formal CR 小节", failures)
    require("CR-029" in tracking_text, "CR-019 follow-up 台账未关联 CR-029", failures)
    require("STALE-CR019-ACTIVE-CHANGE" in state_text, "STATE.md 缺少 STALE-CR019-ACTIVE-CHANGE 审计记录", failures)
    require("STALE-CR019-ACTIVE-CHANGE" in index_text, "CR-INDEX.yaml 缺少 STALE-CR019-ACTIVE-CHANGE 审计记录", failures)
    require('status: "resolved"' in state_text, "STATE.md 未将 STALE-CR019-ACTIVE-CHANGE 标记 resolved", failures)
    require('status: "resolved"' in index_text, "CR-INDEX.yaml 未将 STALE-CR019-ACTIVE-CHANGE 标记 resolved", failures)
    require("SYNC-CR029-RELATED-ACTIVE" in state_text, "STATE.md 缺少 SYNC-CR029-RELATED-ACTIVE 记录", failures)
    require("SYNC-CR029-RELATED-ACTIVE" in index_text, "CR-INDEX.yaml 缺少 SYNC-CR029-RELATED-ACTIVE 记录", failures)

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查 CR tracking 标准信息是否完整")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    failures = check_project(project_root)
    if failures:
        print("CR tracking consistency: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("CR tracking consistency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
