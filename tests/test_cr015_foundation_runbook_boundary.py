import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATHS = (
    "docs/QMT-TRADING-RUNBOOK.md",
    "README.md",
    "docs/USER-MANUAL.md",
)


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _combined_docs() -> str:
    return "\n".join(_read(path) for path in DOC_PATHS)


def _count_patterns(text: str, patterns: tuple[str, ...]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.IGNORECASE)) for pattern in patterns)


def test_foundation_runbook_has_required_sections() -> None:
    runbook = _read("docs/QMT-TRADING-RUNBOOK.md")
    required_headings = (
        "## 1. Setup Boundary",
        "## 2. Shadow Run",
        "## 3. Dry-run Plan",
        "## 4. Mock Event",
        "## 5. Handoff to CR016",
    )

    for heading in required_headings:
        assert heading in runbook

    assert "`shadow`" in runbook
    assert "`dry_run`" in runbook
    assert "`mock`" in runbook
    assert "CR016" in runbook


def test_documents_expose_cr015_forbidden_scope_and_cr016_handoff() -> None:
    combined = _combined_docs()
    required_terms = (
        "CR-015",
        "CR-016",
        "shadow",
        "dry_run",
        "mock",
        "simulation",
        "live_readonly",
        "small_live",
        "scale_up",
        "真实 QMT",
        "真实发单",
        "撤单",
        "账户查询",
        "凭据读取",
        "真实 broker lake 写入",
        "真实抓取",
        "真实 lake 写入",
        "publish",
    )

    for term in required_terms:
        assert term in combined

    assert "QMT-TRADING-RUNBOOK.md" in combined
    assert "per-run authorization" in combined
    assert "blocked" in combined


def test_real_trading_supported_claim_count_is_zero() -> None:
    combined = _combined_docs()
    positive_real_trading_claims = (
        r"真实交易已支持",
        r"真实交易已经支持",
        r"支持真实交易",
        r"真实交易可用",
        r"真实交易已开通",
        r"允许真实交易",
        r"真实发单已支持",
        r"支持真实发单",
        r"允许真实发单",
        r"可真实发单",
        r"real trading supported",
        r"real trading is supported",
        r"live trading supported",
        r"real order supported",
        r"live order supported",
    )

    assert _count_patterns(combined, positive_real_trading_claims) == 0


def test_microstructure_allowed_claim_count_is_zero() -> None:
    combined = _combined_docs()
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

    assert _count_patterns(combined, positive_microstructure_claims) == 0


def test_sensitive_value_output_count_is_zero() -> None:
    combined = _combined_docs()
    sensitive_value_patterns = (
        r"\b(?:TUSHARE_TOKEN|JQDATA_USERNAME|JQDATA_PASSWORD|TOKEN|PASSWORD|COOKIE|SESSION|PRIVATE_KEY)\s*=(?!<)(?!\s)[^\s`]+",
        r"\b(?:token|password|cookie|session|private_key)\s*[:=]\s*(?!<)[A-Za-z0-9_./+\-=]{12,}",
        r"(?:资金账号|账户号|account_id)\s*[:=]\s*[0-9]{6,}",
        r"/home/[A-Za-z0-9_.\-/]+",
        r"C:\\\\Users\\\\[A-Za-z0-9_.\-\\\\]+",
        r"AKIA[0-9A-Z]{16}",
    )

    assert _count_patterns(combined, sensitive_value_patterns) == 0


def test_safety_counters_are_documented_as_zero() -> None:
    runbook = _read("docs/QMT-TRADING-RUNBOOK.md")
    required_counters = (
        "qmt_api_call",
        "real_order_call",
        "real_cancel_call",
        "account_query_call",
        "account_write_call",
        "credential_read",
        "real_broker_lake_write",
        "real_lake_write",
        "provider_fetch",
        "publish",
        "dependency_change",
        "simulation_activation",
        "live_activation",
        "real_trading_supported_claim_count",
        "microstructure_allowed_claim_count",
    )

    for counter in required_counters:
        assert f"`{counter}` | `0`" in runbook
