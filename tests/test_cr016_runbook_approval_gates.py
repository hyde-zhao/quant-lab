import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
DOC_PATHS = (
    RUNBOOK_PATH,
    "docs/QMT-TRADING-RUNBOOK.md",
    "README.md",
    "docs/USER-MANUAL.md",
)

P0_HEADINGS = (
    "## P0-1 启动 / Start Gate",
    "## P0-2 审批 / Per-run Approval Gate",
    "## P0-3 异常处理 / Exception Handling",
    "## P0-4 对账 / Reconciliation",
    "## P0-5 Kill Switch",
    "## P0-6 暂停 / 恢复",
    "## P0-7 回滚 / Rollback",
)

REQUIRED_AUTHORIZATION_FIELDS = (
    "authorization_id",
    "mode",
    "strategy_id",
    "run_id",
    "stage",
    "capital_limit",
    "order_scope",
    "approver",
    "approved_at",
    "expires_at",
    "rollback_plan_ref",
)

ROLLBACK_COLUMNS = (
    "incident type",
    "stage",
    "owner",
    "action",
    "rollback target",
    "recovery gate",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _combined_docs() -> str:
    return "\n".join(_read(path) for path in DOC_PATHS)


def _count_patterns(text: str, patterns: tuple[str, ...]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def _runbook_readiness(text: str) -> dict[str, object]:
    missing = tuple(heading for heading in P0_HEADINGS if heading not in text)
    return {
        "runbook_status": "fail" if missing else "pass",
        "missing_sections": missing,
    }


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
        if set(cells) == {"---"}:
            continue
        rows.append(cells)
    return rows


def test_runbook_has_seven_p0_sections() -> None:
    runbook = _read(RUNBOOK_PATH)

    readiness = _runbook_readiness(runbook)
    assert readiness["runbook_status"] == "pass"
    assert readiness["missing_sections"] == ()
    for heading in P0_HEADINGS:
        assert heading in runbook


def test_missing_p0_section_returns_fail_status() -> None:
    runbook = _read(RUNBOOK_PATH)
    broken_runbook = runbook.replace("## P0-5 Kill Switch", "## Kill Switch", 1)

    readiness = _runbook_readiness(broken_runbook)
    assert readiness["runbook_status"] == "fail"
    assert readiness["missing_sections"] == ("## P0-5 Kill Switch",)


def test_approval_gate_required_fields_have_full_coverage() -> None:
    runbook = _read(RUNBOOK_PATH)
    approval_section = _section(runbook, "## P0-2 审批 / Per-run Approval Gate")
    found_fields = {
        field
        for field in REQUIRED_AUTHORIZATION_FIELDS
        if f"| `{field}` |" in approval_section
    }

    assert found_fields == set(REQUIRED_AUTHORIZATION_FIELDS)
    assert len(found_fields) / len(REQUIRED_AUTHORIZATION_FIELDS) == 1.0


def test_rollback_recovery_matrix_has_required_columns_and_rows() -> None:
    runbook = _read(RUNBOOK_PATH)
    matrix_section = _section(runbook, "## Rollback / Recovery Matrix")
    rows = _markdown_table_rows(matrix_section)

    assert rows
    header = tuple(cell.lower() for cell in rows[0])
    assert header == ROLLBACK_COLUMNS

    data_rows = rows[1:]
    incident_types = {row[0] for row in data_rows}
    assert {
        "authorization_missing_or_expired",
        "heartbeat_missed",
        "reconciliation_threshold_breach",
        "broker_ack_error",
        "kill_switch_triggered",
        "manual_stop_request",
        "cr017_or_maturity_boundary_missing",
    } <= incident_types

    for row in data_rows:
        assert len(row) == len(ROLLBACK_COLUMNS)
        assert row[2] in {"research_owner", "trading_node_owner", "approver"}
        assert row[3]
        assert row[4].endswith("_blocked")
        assert row[5]


def test_default_authorization_claim_count_is_zero() -> None:
    combined = _combined_docs()
    required_boundary_terms = (
        "均不自动授权 `simulation`、`live`、`small_live`、`scale_up`",
        "`default_real_operation_authorization_claim` | `0`",
        "文档合同不自动授权真实运行",
    )
    forbidden_default_authorization_claims = (
        r"(?<!不)自动授权",
        r"默认授权\s*(?:simulation|live|small_live|scale_up|真实\s*broker)",
        r"(?:runbook|CP5|CP6/CP7|Story verified|document presence)\s+is\s+a\s+standing\s+approval",
        r"(?:runbook|CP5|CP6/CP7|Story verified)\s+authorizes\s+(?:simulation|live|broker)",
        r"文档存在\s*即\s*授权",
    )

    for term in required_boundary_terms:
        assert term in combined
    assert _count_patterns(combined, forbidden_default_authorization_claims) == 0


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
