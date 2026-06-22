from __future__ import annotations

from pathlib import Path

from engine.research_paths import RESEARCH_REPORT_ROOT


ROADMAP_DOC = Path("process/docs/source-archive/docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md")
ROADMAP_REPORT = RESEARCH_REPORT_ROOT / "data_lake_readiness_2020_2024_cr013" / "backfill_roadmap.md"

FORMAL_DATASETS = (
    "prices",
    "adj_factor",
    "hs300_index",
    "trade_calendar",
    "index_members",
    "index_weights",
    "stock_basic",
    "trade_status",
    "prices_limit",
    "events",
)


def test_backfill_roadmap_lists_full_history_and_vwap_release_criteria() -> None:
    doc = ROADMAP_DOC.read_text(encoding="utf-8")
    report = ROADMAP_REPORT.read_text(encoding="utf-8")

    for dataset in FORMAL_DATASETS:
        assert f"`{dataset}`" in doc
    assert "2020-01-01..2024-12-31" in doc
    assert "readiness pass" in doc
    assert "new readiness audit pass" in report
    assert "old_baseline_preserved=true" in doc
    assert "old_baseline_preserved | `true`" in report
    assert "vwap_status=available" in doc
    assert "execution audit pass" in doc
    assert "vwap_release_criteria" in report


def test_backfill_roadmap_current_real_operations_are_not_authorized() -> None:
    text = ROADMAP_DOC.read_text(encoding="utf-8") + "\n" + ROADMAP_REPORT.read_text(encoding="utf-8")

    for operation in ("provider_fetch", "lake_write", "credential_read", "legacy_data_read", "old_report_overwrite"):
        assert operation in text
        assert "not_authorized" in text
    assert "`authorized`" not in text
    assert "| `authorized` |" not in text


def test_backfill_roadmap_contains_no_direct_execution_commands_or_secret_prompts() -> None:
    text = ROADMAP_DOC.read_text(encoding="utf-8") + "\n" + ROADMAP_REPORT.read_text(encoding="utf-8")
    forbidden_fragments = (
        "uv run",
        "python -m market_data.cli",
        "--execute",
        "TUSHARE_TOKEN=",
        "MARKET_DATA_LAKE_ROOT=",
        "/mnt/ugreen-data-lake",
    )

    for fragment in forbidden_fragments:
        assert fragment not in text


def test_backfill_roadmap_forbidden_operation_counters_are_zero() -> None:
    report = ROADMAP_REPORT.read_text(encoding="utf-8")

    for counter in ("provider_fetches", "lake_writes", "credential_reads", "legacy_data_reads", "old_report_overwrites"):
        assert f"| {counter} | 0 |" in report
