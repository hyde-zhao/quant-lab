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
    "CR-020",
    "CR-021",
    "CR-022",
    "CR-023",
    "CR-024",
    "CR-026",
)
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

    state_text = read_text(state_path)
    index_text = read_text(index_path)
    tracking_text = read_text(tracking_path)
    cr019_text = read_text(cr019_path)
    cr025_text = read_text(cr025_path)
    cr029_text = read_text(cr029_path)
    cr030_text = read_text(cr030_path)

    require(bool(state_text), f"缺少状态文件: {state_path}", failures)
    require(bool(index_text), f"缺少 CR 索引: {index_path}", failures)
    require(bool(tracking_text), f"缺少 CR-019 follow-up 台账: {tracking_path}", failures)
    require(bool(cr019_text), f"缺少 CR-019 正式 CR: {cr019_path}", failures)
    require(bool(cr025_text), f"缺少 CR-025 正式 CR: {cr025_path}", failures)
    require(bool(cr029_text), f"缺少 CR-029 正式 CR: {cr029_path}", failures)
    require(bool(cr030_text), f"缺少 CR-030 正式 CR: {cr030_path}", failures)

    if not all((state_text, index_text, tracking_text, cr019_text, cr025_text, cr029_text, cr030_text)):
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

    for item_id in ("CR-025", "CR-029", "CR-030", *REQUIRED_CANDIDATES, *REQUIRED_SPIKES):
        require(item_id in index_text, f"CR-INDEX.yaml 缺少 {item_id}", failures)
        require(item_id in state_text, f"STATE.md cr_tracking 缺少 {item_id}", failures)

    require('id: "CR-025"' in index_text, "CR-INDEX.yaml 缺少 CR-025 标准项", failures)
    require("CR-025" in tracking_text, "CR-019 follow-up 台账缺少 CR-025", failures)
    if cr025_is_active:
        require('active_change: "CR-025"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-025", failures)
    if cr025_is_closed:
        require("closed_crs:" in state_text, "STATE.md cr_tracking 缺少 closed_crs", failures)
        require("closed_crs:" in index_text, "CR-INDEX.yaml 缺少 closed_crs", failures)
        if cr030_is_active:
            require('active_change: "CR-030"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-030", failures)
        else:
            require('active_change: ""' in state_text or 'active_change: "none"' in state_text, "STATE.md 顶层 active_change 未在 CR-025 关闭后清空", failures)
        require("| CR-025 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-025 标记为 closed", failures)
    if cr030_is_active:
        require('active_change: "CR-030"' in state_text, "STATE.md 顶层 active_change 未切换到 CR-030", failures)
        require('status: "active-formal-cr"' in index_text, "CR-INDEX.yaml 顶层未标记 active-formal-cr", failures)
        require('status: "active-formal-cr"' in state_text, "STATE.md cr_tracking 未标记 active-formal-cr", failures)
        require("active_crs:" in state_text, "STATE.md cr_tracking 缺少 active_crs", failures)
        require("active_crs:" in index_text, "CR-INDEX.yaml 缺少 active_crs", failures)
        require("active-cp2-intake" in tracking_text, "CR-019 follow-up 台账未记录 CR-030 active-cp2-intake", failures)
        require("| CR-030 | active |" in tracking_text, "CR-019 follow-up 台账未将 CR-030 标记为 active formal CR", failures)
    if cr030_is_closed:
        require("| CR-030 | closed |" in tracking_text, "CR-019 follow-up 台账未将 CR-030 标记为 closed", failures)

    for item_id in REQUIRED_CANDIDATES:
        require(f'id: "{item_id}"' in index_text, f"CR-INDEX.yaml 缺少 candidate 标准项 {item_id}", failures)
        require(item_id in tracking_text, f"CR-019 follow-up 台账缺少 candidate {item_id}", failures)

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
