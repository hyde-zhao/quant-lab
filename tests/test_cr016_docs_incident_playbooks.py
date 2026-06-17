import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK_PATH = "docs/QMT-INCIDENT-PLAYBOOK.md"
RUNBOOK_PATH = "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
DOC_PATHS = (
    PLAYBOOK_PATH,
    RUNBOOK_PATH,
    "README.md",
    "docs/USER-MANUAL.md",
)

STAGES = (
    "shadow",
    "simulation",
    "live_readonly",
    "small_live",
    "scale_up",
)

INCIDENT_TYPES = (
    "heartbeat_fail",
    "risk_blocked",
    "recon_diff",
    "manual_trigger",
    "recovery_required",
)

INCIDENT_COLUMNS = (
    "incident type",
    "trigger",
    "immediate action",
    "owner",
    "evidence required",
    "recovery gate",
    "rollback target",
)

REQUIRED_ZERO_COUNTERS = (
    "qmt_api_call",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "credential_read",
    "real_broker_operation",
    "real_broker_lake_write",
    "real_lake_write",
    "provider_fetch",
    "publish",
    "simulation_run",
    "live_run",
    "small_live_run",
    "scale_up_run",
    "real_snapshot_pull",
    "incident_persisted",
    "default_real_operation_authorization_claim",
    "unsupported_execution_claim_unblocked",
    "sensitive_raw_value_output",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _combined_docs() -> str:
    return "\n".join(_read(path) for path in DOC_PATHS)


def _count_patterns(text: str, patterns: tuple[str, ...]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    next_heading = re.search(r"\n## ", text[start + len(heading) :])
    if next_heading is None:
        return text[start:]
    end = start + len(heading) + next_heading.start()
    return text[start:end]


def _markdown_table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _table_by_heading(text: str, heading: str) -> tuple[tuple[str, ...], list[list[str]]]:
    rows = _markdown_table_rows(_section(text, heading))
    assert rows
    return tuple(cell.lower() for cell in rows[0]), rows[1:]


def test_incident_playbook_covers_required_stages() -> None:
    playbook = _read(PLAYBOOK_PATH)
    combined = _combined_docs()

    for stage in STAGES:
        assert f"`{stage}`" in playbook
        assert f"`{stage}`" in combined

    stage_header, stage_rows = _table_by_heading(playbook, "## 1. Stage Coverage")
    assert stage_header == (
        "stage",
        "incident handling scope",
        "recovery owner",
        "rollback target",
        "default operation status",
    )
    assert {row[0] for row in stage_rows} == set(STAGES)


def test_incident_playbook_covers_required_incident_types_and_columns() -> None:
    playbook = _read(PLAYBOOK_PATH)
    incident_header, incident_rows = _table_by_heading(playbook, "## 2. Incident Playbook")

    assert incident_header == INCIDENT_COLUMNS
    incidents = {row[0] for row in incident_rows}
    assert incidents == set(INCIDENT_TYPES)

    for row in incident_rows:
        assert len(row) == len(INCIDENT_COLUMNS)
        assert all(cell for cell in row)
        assert row[3] in {"research_owner", "trading_node_owner", "approver"}
        assert row[5]
        assert row[6] in {
            "shadow_only",
            "simulation_blocked",
            "live_readonly_blocked",
            "small_live_blocked",
            "scale_up_blocked",
        }


def test_recovery_gate_requires_manual_takeover_record() -> None:
    playbook = _read(PLAYBOOK_PATH)
    runbook = _read(RUNBOOK_PATH)
    recovery_section = _section(playbook, "## 4. Recovery Gate")

    assert "manual_takeover_record" in recovery_section
    assert "`manual_takeover_record=recorded`" in runbook
    assert "reconciliation_status" in recovery_section
    assert "kill_switch_state" in recovery_section
    assert "authorization_status" in recovery_section
    assert "rollback_target" in recovery_section

    _, recovery_rows = _table_by_heading(playbook, "## 4. Recovery Gate")
    required_conditions = {row[0] for row in recovery_rows}
    assert {
        "reconciliation_status",
        "manual_takeover_record",
        "kill_switch_state",
        "authorization_status",
        "rollback_target",
    } <= required_conditions


def test_readme_user_manual_and_runbook_link_incident_playbook() -> None:
    combined = _combined_docs()
    required_terms = (
        "QMT-INCIDENT-PLAYBOOK.md",
        "QMT Incident Playbook",
        "heartbeat_fail",
        "risk_blocked",
        "recon_diff",
        "manual_trigger",
        "recovery_required",
        "trigger、immediate action、owner、evidence required、recovery gate 和 rollback target",
    )

    for term in required_terms:
        assert term in combined


def test_default_real_operation_authorization_claim_count_is_zero() -> None:
    combined = _combined_docs()
    required_boundary_terms = (
        "均不自动授权",
        "文档合同不自动授权真实运行",
        "`default_real_operation_authorization_claim` | `0`",
    )
    forbidden_default_authorization_claims = (
        r"(?<!不)自动授权",
        r"默认授权\s*(?:simulation|live|small_live|scale_up|真实\s*broker)",
        r"(?:runbook|incident playbook|CP5|CP6|CP7|Story verified|document presence)\s+is\s+a\s+standing\s+approval",
        r"(?:runbook|incident playbook|CP5|CP6|CP7|Story verified)\s+authorizes\s+(?:simulation|live|broker)",
        r"文档存在\s*即\s*授权",
    )

    for term in required_boundary_terms:
        assert term in combined
    assert _count_patterns(combined, forbidden_default_authorization_claims) == 0


def test_unsupported_execution_claims_remain_blocked() -> None:
    combined = _combined_docs()
    playbook = _read(PLAYBOOK_PATH)
    required_claims = (
        "real_vwap_execution",
        "minute_execution",
        "tick_execution",
        "Level2_execution",
        "order_match_execution",
        "`unsupported_execution_claim_unblocked` | `0`",
    )
    positive_microstructure_claims = (
        r"真实\s*VWAP\s*已支持",
        r"真实\s*VWAP\s*可用",
        r"允许真实\s*VWAP",
        r"支持真实\s*VWAP",
        r"real\s+VWAP\s+supported",
        r"real\s+VWAP\s+execution\s+allowed",
        r"minute\s+execution\s+supported",
        r"minute\s+execution\s+allowed",
        r"tick\s+execution\s+supported",
        r"tick\s+execution\s+allowed",
        r"Level2\s+execution\s+supported",
        r"Level2\s+execution\s+allowed",
        r"order-match\s+execution\s+supported",
        r"order-match\s+execution\s+allowed",
        r"微观结构.*已支持",
        r"微观结构.*可用",
    )

    for claim in required_claims:
        assert claim in playbook
    assert "blocked / unsupported" in playbook
    assert _count_patterns(combined, positive_microstructure_claims) == 0


def test_safety_counters_are_documented_as_zero() -> None:
    playbook = _read(PLAYBOOK_PATH)

    for counter in REQUIRED_ZERO_COUNTERS:
        assert f"`{counter}` | `0`" in playbook


def test_sensitive_raw_value_output_count_is_zero() -> None:
    combined = _combined_docs()
    sensitive_value_patterns = (
        r"\b(?:TUSHARE_TOKEN|JQDATA_USERNAME|JQDATA_PASSWORD|TOKEN|PASSWORD|COOKIE|SESSION|PRIVATE_KEY|BROKER_LAKE_ROOT)\s*=(?!<)(?!\s)[^\s`]+",
        r"\b(?:token|password|cookie|session|private_key)\s*[:=]\s*(?!<)[A-Za-z0-9_./+\-=]{12,}",
        r"(?:资金账号|账户号|account_id)\s*[:=]\s*[0-9]{6,}",
        r"/home/[A-Za-z0-9_.\-/]+",
        r"C:\\\\Users\\\\[A-Za-z0-9_.\-\\\\]+",
        r"AKIA[0-9A-Z]{16}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )

    assert _count_patterns(combined, sensitive_value_patterns) == 0
