from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER_PATH = (
    REPO_ROOT
    / "process"
    / "docs"
    / "source-archive"
    / "docs"
    / "CR019-DEFERRED-CAPABILITIES.md"
)
README_PATH = REPO_ROOT / "README.md"

CAPABILITY_IDS = (
    "backtrader_w6",
    "qlib_w7",
    "minute_spike",
    "level2_spike",
)

REQUIRED_FIELDS = (
    "Current status",
    "Non-P0 reason",
    "Trigger conditions",
    "Blocked reason",
    "Required evidence",
    "Next CR / CP entry",
    "Forbidden claims",
    "Revisit condition",
)

REAL_CONFIG_FRAGMENTS = (
    "provider" + "_uri",
    "level2" + " entitlement",
    "Level2" + " entitlement",
    "minute" + " fetch",
    "fetch" + "_minute",
    "qlib" + ".init",
    "D" + ".features",
    "pip" + " install",
    "uv" + " add",
    "poetry" + " add",
    "conda" + " install",
    "backtrader" + "==",
    "qlib" + "==",
)

ENABLED_CLAIM_FRAGMENTS = (
    "enabled" + " by default",
    "default" + " enabled",
    "already" + " enabled",
    "authorized" + " for live",
    "current" + " P0 dependency",
    "当前" + "已启用",
    "默认" + "启用",
    "默认" + "授权",
    "实盘" + "授权",
    "P0 " + "默认依赖",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _entry(register_text: str, capability_id: str) -> str:
    pattern = rf"^### {re.escape(capability_id)}\n(?P<body>.*?)(?=^### |\Z)"
    match = re.search(pattern, register_text, re.MULTILINE | re.DOTALL)
    assert match, f"missing register entry: {capability_id}"
    return match.group("body")


def _trigger_count(entry_text: str) -> int:
    trigger_line = next(
        line for line in entry_text.splitlines() if line.startswith("| Trigger conditions |")
    )
    return len(re.findall(r"\d+\.", trigger_line))


def test_deferred_register_contains_exactly_four_capability_entries() -> None:
    register = _read(REGISTER_PATH)

    assert REGISTER_PATH.exists()
    assert {match.group(1) for match in re.finditer(r"^### ([a-z0-9_]+)$", register, re.MULTILINE)} == set(CAPABILITY_IDS)
    assert "Stage 6 P0 dependency additions | `0`" in register
    assert "QMT C/S bridge dependency additions | `0`" in register


def test_each_entry_has_required_fields_and_at_least_two_triggers() -> None:
    register = _read(REGISTER_PATH)

    for capability_id in CAPABILITY_IDS:
        entry = _entry(register, capability_id)
        for field in REQUIRED_FIELDS:
            assert f"| {field} |" in entry, f"{capability_id} missing {field}"
        assert _trigger_count(entry) >= 2, f"{capability_id} needs at least two triggers"
        assert "blocked" in entry.lower()
        assert "CR" in entry
        assert "CP" in entry


def test_forbidden_claims_and_real_config_patterns_are_absent() -> None:
    combined = "\n".join((_read(REGISTER_PATH), _read(README_PATH), _read(Path(__file__))))
    combined_lower = combined.lower()

    assert "Forbidden claims" in combined
    for fragment in REAL_CONFIG_FRAGMENTS:
        assert fragment.lower() not in combined_lower, fragment


def test_readme_declares_later_gated_non_p0_boundary_without_current_enablement() -> None:
    readme = _read(README_PATH)
    section_match = re.search(
        r"^### CR-019 S09 deferred capability register\n(?P<body>.*?)(?=^### |\Z)",
        readme,
        re.MULTILINE | re.DOTALL,
    )

    assert section_match, "README missing CR-019 S09 section"
    section = section_match.group("body")
    for capability_id in CAPABILITY_IDS:
        assert capability_id in section
    assert "non-P0" in section
    assert "later-gated" in section
    assert "Stage 6 P0 dependency additions | `0`" in section
    assert "QMT C/S bridge dependency additions | `0`" in section

    section_lower = section.lower()
    for fragment in ENABLED_CLAIM_FRAGMENTS:
        assert fragment.lower() not in section_lower, fragment


def test_dependency_and_scope_expansion_counters_stay_zero_in_contract() -> None:
    register = _read(REGISTER_PATH)
    readme = _read(README_PATH)
    combined = "\n".join((register, readme))

    assert "stage6_p0_dependency_additions: 0" in register
    assert "real_operation_permission_claims: 0" in register
    assert combined.count("Stage 6 P0 dependency additions | `0`") >= 2
    assert combined.count("QMT C/S bridge dependency additions | `0`") >= 2
    assert "pyproject.toml" not in register
    assert "uv.lock" not in register
