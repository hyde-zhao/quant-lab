from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GATEWAY_DOC = REPO_ROOT / "docs" / "QMT-GATEWAY-INSTALL.md"
RUNBOOK_DOC = REPO_ROOT / "docs" / "QMT-C-S-BRIDGE-RUNBOOK.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing doc: {path}"
    return path.read_text(encoding="utf-8")


def _section(text: str, header: str) -> str:
    pattern = rf"^## {re.escape(header)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    assert match, f"missing section: {header}"
    return match.group("body")


def test_cr020_manual_install_sections_and_runtime_commands_are_present() -> None:
    gateway = _read(GATEWAY_DOC)
    runbook = _read(RUNBOOK_DOC)
    gateway_section = _section(gateway, "CR020 Windows S 端手工安装调试手册")
    runbook_section = _section(runbook, "9. CR020 Manual Install Debug Guide")

    assert "CR020 Contract Summary" in gateway_section
    assert "Authorization Boundary" in gateway_section
    assert "No-Authorization Table" in gateway_section
    assert "CP7 Readonly Evidence Schema" in gateway_section
    assert "uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics" in gateway_section
    assert "uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve" in gateway_section
    assert "uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions" in runbook_section
    assert "QmtClient" in runbook_section
    assert "StdlibQmtRestTransport" in runbook_section
    assert "build_runtime_hmac_provider" in runbook_section


def test_cr020_docs_fix_query_positions_scope_and_endpoint_only() -> None:
    combined = _read(GATEWAY_DOC) + "\n" + _read(RUNBOOK_DOC)

    assert "POST /qmt/account/positions" in combined
    assert "query_positions" in combined
    assert "qmt:positions:read" in combined
    assert "exact scope" in combined
    assert "其他 QMT endpoint" in combined or "非 CR020 白名单 endpoint" in combined
    assert "endpoint_not_supported" in combined


def test_cr020_docs_no_authorization_table_blocks_trading_and_writes() -> None:
    gateway = _read(GATEWAY_DOC)
    runbook = _read(RUNBOOK_DOC)
    gateway_section = _section(gateway, "CR020 Windows S 端手工安装调试手册")
    runbook_section = _section(runbook, "9. CR020 Manual Install Debug Guide")

    for text in (gateway_section, runbook_section):
        assert "not-authorized" in text
        assert "order" in text
        assert "cancel" in text
        assert "account_write" in text or "账户写入" in text
        assert "provider" in text
        assert "lake" in text
        assert "publish" in text
        assert "simulation" in text
        assert "live" in text


def test_cr020_docs_use_placeholders_and_redacted_refs_not_real_credentials() -> None:
    combined = _read(GATEWAY_DOC) + "\n" + _read(RUNBOOK_DOC)
    forbidden_patterns = (
        re.compile(r"QMT_CLIENT_SECRET\s*=\s*(?!<)[^\s`|]+"),
        re.compile(r"QMT_LOGIN_PASSWORD\s*=\s*(?!<)[^\s`|]+"),
        re.compile(r"QMT_ACCOUNT_REF\s*=\s*(?!<)[^\s`|]+"),
        re.compile(r"(?i)-----BEGIN [A-Z ]*PRIVATE\s+KEY-----"),
        re.compile(r"(?i)token\s*=\s*(?!<)[^\s`|]+"),
    )

    assert "<manual-long-random-secret>" in combined
    assert "<same-client-secret-as-windows>" in combined
    assert "[REDACTED]" in combined
    for pattern in forbidden_patterns:
        assert not pattern.search(combined), pattern.pattern


def test_cr020_cp7_evidence_schema_excludes_raw_positions_and_secret_output() -> None:
    runbook = _read(RUNBOOK_DOC)
    section = _section(runbook, "9. CR020 Manual Install Debug Guide")

    assert "CP7 Readonly Evidence Schema" in section
    assert "positions_digest" in section
    assert "position_count" in section
    assert "items_redacted" in section
    assert "raw positions" in section
    assert "禁止提交" in section
    assert "HMAC secret" in section
    assert "raw signature" in section
    assert "未脱敏证券代码" in section
    assert "精确持仓数量" in section
