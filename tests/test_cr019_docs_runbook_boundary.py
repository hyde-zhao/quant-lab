from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = REPO_ROOT / "docs" / "QMT-C-S-BRIDGE-RUNBOOK.md"
README_PATH = REPO_ROOT / "README.md"
USER_MANUAL_PATH = REPO_ROOT / "docs" / "USER-MANUAL.md"
SIM_LIVE_RUNBOOK_PATH = REPO_ROOT / "docs" / "QMT-SIMULATION-LIVE-RUNBOOK.md"
INCIDENT_PLAYBOOK_PATH = REPO_ROOT / "docs" / "QMT-INCIDENT-PLAYBOOK.md"
TEST_PATH = Path(__file__)

TARGET_PATHS = (
    RUNBOOK_PATH,
    README_PATH,
    USER_MANUAL_PATH,
    SIM_LIVE_RUNBOOK_PATH,
    INCIDENT_PLAYBOOK_PATH,
    TEST_PATH,
)

DQ_IDS = tuple(f"CP3-CR019-DQ-0{index}" for index in range(1, 8))
STORY_IDS = tuple(f"CR019-S{index:02d}" for index in range(1, 11))
NO_REAL_OPERATION_CATEGORIES = (
    "dependency change",
    "service start",
    "credential read",
    "QMT / MiniQMT / XtQuant",
    "provider fetch",
    "lake / broker lake",
    "publish",
    "simulation/live",
)

REAL_VALUE_PATTERNS = (
    re.compile(r"(?i)(?<![A-Z_])" + r"token\s*=\s*(?!<)[^\s`|]+"),
    re.compile(r"(?i)(?<![A-Z_])" + r"password\s*=\s*(?!<)[^\s`|]+"),
    re.compile(r"(?i)(?<![A-Z_])" + r"se" + r"cret\s*=\s*(?!<)[^\s`|]+"),
    re.compile(r"(?i)" + r"account" + r"_id\s*=\s*[0-9]+"),
    re.compile(r"(?i)" + r"-----BEGIN [A-Z ]*" + "PRIVATE" + r"\s+KEY-----"),
)

def _phrase(*parts: str) -> str:
    return "".join(parts)


MISLEADING_PERMISSION_FRAGMENTS = (
    _phrase("run", "book authorizes real ", "trade"),
    _phrase("run", "book authorizes real ", "operation"),
    _phrase("story ", "verified authorizes"),
    _phrase("cp", "5 authorizes ", "real"),
    _phrase("cp", "6 authorizes ", "real"),
    _phrase("cp", "7 authorizes ", "real"),
    _phrase("默认", "授权"),
    _phrase("实盘", "授权"),
    _phrase("已", "授权", "真实"),
)


def _read(path: Path) -> str:
    assert path.exists(), f"missing target file: {path}"
    return path.read_text(encoding="utf-8")


def _combined_text() -> str:
    return "\n".join(_read(path) for path in TARGET_PATHS)


def _section(text: str, header: str) -> str:
    pattern = rf"^## {re.escape(header)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    assert match, f"missing section: {header}"
    return match.group("body")


def test_runbook_declares_authorization_boundary_without_real_permission() -> None:
    runbook = _read(RUNBOOK_PATH)
    boundary = _section(runbook, "1. Authorization Boundary")

    assert "Story `verified`" in boundary
    assert "CP5" in boundary and "CP6" in boundary and "CP7" in boundary
    assert "不是交易许可" in boundary
    assert "per-run authorization" in boundary
    assert "HMAC / pairing" in boundary
    assert "Endpoint visible" in boundary
    assert "Fallback / signed file candidate" in boundary
    assert "真实交易" in boundary
    assert "broker lake" in boundary


def test_cp3_decision_boundary_covers_all_seven_decisions() -> None:
    runbook = _read(RUNBOOK_PATH)
    decision_section = _section(runbook, "2. CP3 Decision Boundary")

    assert "Accepted recommendation" in decision_section
    assert "User impact" in decision_section
    assert "Not authorization" in decision_section
    for decision_id in DQ_IDS:
        assert decision_section.count(decision_id) == 1, decision_id


def test_story_boundary_covers_all_ten_cr019_stories() -> None:
    runbook = _read(RUNBOOK_PATH)
    story_section = _section(runbook, "3. CR019 Story Boundary")

    for story_id in STORY_IDS:
        assert story_section.count(story_id) >= 1, story_id
    assert story_section.count("process/checks/CP7-CR019-S0") >= 9
    assert "process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md" in story_section
    assert "Forbidden operation" in story_section
    assert "Verification entry" in story_section


def test_no_real_operation_table_covers_required_eight_categories() -> None:
    runbook = _read(RUNBOOK_PATH)
    no_real_section = _section(runbook, "4. No-Real-Operation Boundary")

    for category in NO_REAL_OPERATION_CATEGORIES:
        assert f"| {category} | `0` |" in no_real_section, category
    assert no_real_section.count("| `0` |") >= len(NO_REAL_OPERATION_CATEGORIES)


def test_shared_docs_have_cr019_s10_boundary_addenda() -> None:
    readme = _read(README_PATH)
    user_manual = _read(USER_MANUAL_PATH)
    sim_live_runbook = _read(SIM_LIVE_RUNBOOK_PATH)
    incident_playbook = _read(INCIDENT_PLAYBOOK_PATH)

    assert "### CR-019 S10 QMT CS bridge runbook 边界" in readme
    assert "[docs/QMT-C-S-BRIDGE-RUNBOOK.md](docs/QMT-C-S-BRIDGE-RUNBOOK.md)" in readme
    assert "#### CR-019 QMT CS bridge runbook 与用户边界" in user_manual
    assert "[QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md)" in user_manual
    assert "## CR019-S10 Bridge Boundary Addendum" in sim_live_runbook
    assert "## 8. CR019-S10 Documentation Boundary Addendum" in incident_playbook

    for text in (readme, user_manual, sim_live_runbook, incident_playbook):
        assert "QMT C/S bridge" in text
        assert "per-run authorization" in text
        assert "No-real-operation" in text or "no-real-operation" in text


def test_sensitive_real_value_examples_are_absent_from_target_docs_and_test() -> None:
    combined = _combined_text()

    for pattern in REAL_VALUE_PATTERNS:
        assert not pattern.search(combined), pattern.pattern


def test_misleading_real_permission_semantics_are_absent() -> None:
    combined_lower = _combined_text().lower()

    for fragment in MISLEADING_PERMISSION_FRAGMENTS:
        assert fragment.lower() not in combined_lower, fragment


def test_real_operation_counters_are_documented_as_zero() -> None:
    runbook = _read(RUNBOOK_PATH)
    verification_section = _section(runbook, "8. Verification Contract")
    combined = _combined_text()

    assert "Real operation count | `0`" in verification_section
    for category in NO_REAL_OPERATION_CATEGORIES:
        assert category in runbook
    assert "dependency_change" in combined
    assert "credential_read" in combined
    assert "provider_fetch" in combined
    assert "publish" in combined
    assert "simulation_run" in combined
