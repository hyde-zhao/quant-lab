from __future__ import annotations

from pathlib import Path

from scripts.quality.check_change_tracking_consistency import (
    audit_history_active_changes,
    check_project,
    main,
    normalize_status,
    tracking_summary_lines,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _frontmatter(cr_id: str, status: str, extra: str = "") -> str:
    return f"""---
cr_id: "{cr_id}"
status: "{status}"
{extra}---

# {cr_id}
"""


def _index_text(active_change: str = "CR-093") -> str:
    return f"""active_crs:
- id: {active_change}
  status: active-formal-cr
  formal_cr_path: process/changes/CR-093-LEDGER-HYGIENE-CR019-CR025-TRACKING-CLEANUP-2026-06-18.md
closed_crs:
- id: CR-020
  status: closed-formal-cr
- id: CR-025
  status: closed-formal-cr
- id: CR-029
  status: closed-formal-cr
- id: CR-030
  status: closed-formal-cr
- id: CR-040
  status: closed-formal-cr
- id: CR-041
  status: closed-formal-cr
- id: CR-043
  status: closed-formal-cr
- id: CR-044
  status: closed-formal-cr
- id: CR-045
  status: closed-formal-cr
- id: CR-046
  status: closed-formal-cr
- id: "CR-025"
  status: closed-formal-cr
cancelled_crs:
- id: "CR-021"
  status: cancelled-formal-cr
- id: "CR-022"
  status: cancelled-formal-cr
- id: "CR-023"
  status: cancelled-formal-cr
- id: "CR-024"
  status: cancelled-formal-cr
follow_up_candidates:
- id: "CR-026"
  status: follow-up-candidate
spike_candidates:
- id: "CR-027"
  status: spike-candidate
- id: "CR-028"
  status: spike-candidate
stale_status_conflicts:
- id: STALE-CR019-ACTIVE-CHANGE
  status: "resolved"
  formal_cr_path: process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md
- id: SYNC-CR029-RELATED-ACTIVE
  status: "resolved-closed"
"""


def _state_text(active_change: str = "CR-093", history_active: str = "CR-025") -> str:
    return f"""---
active_change: "{active_change}"
---

cr_tracking:
  active_crs:
  - id: {active_change}
    status: active-formal-cr
    formal_cr_path: process/changes/CR-093-LEDGER-HYGIENE-CR019-CR025-TRACKING-CLEANUP-2026-06-18.md
  closed_crs:
  - id: CR-020
    status: closed-formal-cr
  - id: CR-025
    status: closed-formal-cr
  - id: CR-029
    status: closed-formal-cr
  - id: CR-030
    status: closed-formal-cr
  - id: CR-040
    status: closed-formal-cr
  - id: CR-041
    status: closed-formal-cr
  - id: CR-043
    status: closed-formal-cr
  - id: CR-044
    status: closed-formal-cr
  - id: CR-045
    status: closed-formal-cr
  - id: CR-046
    status: closed-formal-cr
  - id: "CR-025"
    status: closed-formal-cr
  cancelled_crs:
  - id: "CR-021"
    status: cancelled-formal-cr
  - id: "CR-022"
    status: cancelled-formal-cr
  - id: "CR-023"
    status: cancelled-formal-cr
  - id: "CR-024"
    status: cancelled-formal-cr
  follow_up_candidates:
  - id: "CR-026"
    status: follow-up-candidate
  spike_candidates:
  - id: "CR-027"
    status: spike-candidate
  - id: "CR-028"
    status: spike-candidate
  stale_status_conflicts:
  - id: STALE-CR019-ACTIVE-CHANGE
    status: "resolved"
    formal_cr_path: process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md
  - id: SYNC-CR029-RELATED-ACTIVE
    status: "resolved-closed"

history:
- active_change: {history_active}
"""


def _tracking_text() -> str:
    return """---
tracking_id: "CR-019-FOLLOW-UP-TRACKING"
---

# CR-019 Follow-up Tracking

## Related Formal CR

| CR | 状态 | 来源决策 | 正式 CR 路径 | 与本台账关系 | 当前结论 / 下一步 |
|---|---|---|---|---|---|
| CR-025 | closed | `D-CP8-CR019-05` | `process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md` | closed | closed |
| CR-020 | closed-current-delivery | `D-CP8-CR019-02` | `process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md` | closed | closed |
| CR-030 | closed-cp8-approved | `D-CP8-CR019-05` | `process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md` | closed | closed |
| CR-040 | closed-current-delivery | `USER-20260610-NO-MINIQMT-GOLDMINER-ROUTE` | `process/changes/CR-040-QMT-ROUTE-DELETION-BACKTRADER-PAPER-SIM-GOLDMINER-ADAPTER-2026-06-10.md` | closed | closed |
| CR-041 | closed-current-delivery | `USER-20260610-ACCEPT-CR039-START-CR041` | `process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md` | closed | closed |
| CR-043 | closed-spike-complete | `USER-20260611-START-CR043` | `process/changes/CR-043-GOLDMINER-ADAPTER-SPIKE-2026-06-11.md` | closed | closed |
| CR-044 | closed-current-delivery | `USER-20260611-START-CR044` | `process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md` | closed | closed |
| CR-045 | closed-current-delivery | `USER-20260611-START-CR045` | `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | closed | closed |
| CR-046 | closed-current-delivery | `USER-20260613-START-CR046` | `process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md` | closed | closed |

| 候选 CR | 名称 | 状态 | 类型 |
|---|---|---|---|
| CR-021 | QMT simulation 账号接入准入 | cancelled-user-deleted | CR |
| CR-022 | Live-readonly 准入 | cancelled-user-deleted | CR |
| CR-023 | Small-live 准入 | cancelled-user-deleted | CR |
| CR-024 | Scale-up 准入 | cancelled-user-deleted | CR |
| CR-026 | qlib_w7 | candidate | CR |
| CR-027 | minute_spike | spike_candidate | Spike |
| CR-028 | level2_spike | spike_candidate | Spike |

## Stale Status Conflicts

| 冲突 ID | 状态 | 证据 | 处理方式 |
|---|---|---|---|
| STALE-CR019-ACTIVE-CHANGE | resolved | old active_change | audit only |
| SYNC-CR029-RELATED-ACTIVE | resolved-closed | CR-029 | audit only |
"""


def _write_project(tmp_path: Path, *, active_change: str = "CR-093") -> Path:
    root = tmp_path
    _write(root / "process/STATE.md", _state_text(active_change=active_change))
    _write(root / "process/changes/CR-INDEX.yaml", _index_text(active_change=active_change))
    _write(root / "process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md", _tracking_text())
    _write(
        root / "process/changes/CR-019-STAGE6-MULTIFACTOR-SIMULATION-ARCHITECTURE-2026-05-30.md",
        _frontmatter("CR-019", "closed"),
    )
    _write(
        root / "process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md",
        _frontmatter("CR-020", "closed-current-delivery", 'parent_cr: "CR-019"\nsource_decision_id: "D-CP8-CR019-02"\n'),
    )
    _write(
        root / "process/changes/CR-025-BACKTRADER-OPTIONAL-EXECUTION-BACKEND-HARDENING-2026-05-31.md",
        _frontmatter("CR-025", "closed", 'parent_cr: "CR-019"\nsource_decision_id: "D-CP8-CR019-05"\n'),
    )
    _write(
        root / "process/changes/CR-029-STAGE6-DATA-LAKE-ADMISSION-BENCHMARK-REAL-RUN-2026-05-31.md",
        _frontmatter("CR-029", "closed", 'parent_cr: "CR-019"\nsource_decision_id: "D-CP8-CR019-02"\n'),
    )
    _write(
        root / "process/changes/CR-030-MULTIFACTOR-RESEARCH-FRAMEWORK-REFERENCE-AND-RESEARCH-LOOP-STANDARDIZATION-2026-06-02.md",
        _frontmatter(
            "CR-030",
            "closed-cp8-approved",
            'parent_cr: "CR-019"\nsource_decision_id: "D-CP8-CR019-05"\npredecessor_cr: "CR-025"\n',
        ),
    )
    _write(
        root / "process/changes/CR-040-QMT-ROUTE-DELETION-BACKTRADER-PAPER-SIM-GOLDMINER-ADAPTER-2026-06-10.md",
        _frontmatter("CR-040", "closed-current-delivery", 'parent_cr: "CR-019"\nsource_decision_id: "USER-20260610-NO-MINIQMT-GOLDMINER-ROUTE"\n'),
    )
    _write(
        root / "process/changes/CR-041-API-LESS-PAPER-SIMULATION-RUNNER-2026-06-10.md",
        _frontmatter("CR-041", "closed-current-delivery", 'parent_cr: "CR-040"\nsource_decision_id: "USER-20260610-ACCEPT-CR039-START-CR041"\n'),
    )
    _write(
        root / "process/changes/CR-043-GOLDMINER-ADAPTER-SPIKE-2026-06-11.md",
        _frontmatter("CR-043", "closed-spike-complete", 'parent_cr: "CR-042"\nsource_decision_id: "USER-20260611-START-CR043"\n'),
    )
    _write(
        root / "process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md",
        _frontmatter("CR-044", "closed-current-delivery", 'parent_cr: "CR-043"\nsource_decision_id: "USER-20260611-START-CR044"\n'),
    )
    _write(
        root / "process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md",
        _frontmatter("CR-045", "closed-current-delivery", 'parent_cr: "CR-044"\nsource_decision_id: "USER-20260611-START-CR045"\n'),
    )
    _write(
        root / "process/changes/CR-046-TERMINAL-NATIVE-SIMULATION-STRATEGY-EXPORT-2026-06-13.md",
        _frontmatter("CR-046", "closed-current-delivery"),
    )
    _write(
        root / "process/changes/CR-093-LEDGER-HYGIENE-CR019-CR025-TRACKING-CLEANUP-2026-06-18.md",
        _frontmatter("CR-093", "active" if active_change == "CR-093" else "closed-current-delivery"),
    )
    _write(
        root / "process/changes/CR-094-WARNING-CLEANUP-STRICT-WARNINGS-READINESS-2026-06-19.md",
        _frontmatter("CR-094", "active" if active_change == "CR-094" else "closed-current-delivery"),
    )
    _write(
        root / "process/changes/CR-095-STANDALONE-CHECKER-CLI-OUTPUT-CONVERGENCE-2026-06-19.md",
        _frontmatter("CR-095", "active" if active_change == "CR-095" else "closed-current-delivery"),
    )
    _write(
        root / "process/changes/CR-096-USER-PROVIDED-SIMULATED-EVIDENCE-CHECKER-RUN-2026-06-19.md",
        _frontmatter("CR-096", "active" if active_change == "CR-096" else "closed-current-delivery"),
    )
    return root


def test_normalize_status_groups_formal_and_tracking_equivalents() -> None:
    assert normalize_status("closed-current-delivery") == "closed"
    assert normalize_status("closed-spike-complete") == "closed"
    assert normalize_status("closed-cp8-approved") == "closed"
    assert normalize_status("cancelled-user-deleted") == "cancelled"
    assert normalize_status("active-cp5-review-pending") == "active"


def test_audit_history_active_change_is_warning_only() -> None:
    warnings = audit_history_active_changes(_state_text(history_active="CR-025"), "CR-093")

    assert warnings == ["audit-history active_change=CR-025 ignored as non-current text"]


def test_cr093_active_project_ignores_nested_cr025_history_and_status_equivalents(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-093")

    assert check_project(root) == []


def test_current_active_change_to_closed_formal_cr_still_fails(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-025")

    failures = check_project(root)

    assert any("顶层 active_change 指向非 active formal CR: CR-025" in failure for failure in failures)


def test_cr094_active_project_is_allowed(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-094")

    assert check_project(root) == []


def test_cr095_active_project_is_allowed(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-095")

    assert check_project(root) == []


def test_cr096_active_project_is_allowed(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-096")

    assert check_project(root) == []


def test_empty_single_quoted_active_change_is_allowed_after_close(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="")
    state_path = root / "process/STATE.md"
    state_path.write_text(state_path.read_text(encoding="utf-8").replace('active_change: ""', "active_change: ''"), encoding="utf-8")

    assert check_project(root) == []


def test_tracking_summary_lines_match_main_cli_shape(tmp_path: Path) -> None:
    root = _write_project(tmp_path, active_change="CR-095")

    assert tracking_summary_lines(root) == [
        "CR tracking summary",
        "- active formal CRs: CR-095",
        "- blocked formal CRs: none",
        "- follow-up candidates: CR-026",
        "- spike candidates: CR-027, CR-028",
    ]


def test_main_prints_summary_before_pass(tmp_path: Path, capsys) -> None:
    root = _write_project(tmp_path, active_change="CR-095")

    assert main(["--project-root", str(root)]) == 0

    output = capsys.readouterr().out.splitlines()
    assert output[:5] == [
        "CR tracking summary",
        "- active formal CRs: CR-095",
        "- blocked formal CRs: none",
        "- follow-up candidates: CR-026",
        "- spike candidates: CR-027, CR-028",
    ]
    assert output[-1] == "CR tracking consistency: PASS"
