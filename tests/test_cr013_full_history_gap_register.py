from __future__ import annotations

import csv
from pathlib import Path


REPORT_DIR = Path("tests/fixtures/cr013/data_lake_readiness_2020_2024_cr013")
GAP_REGISTER = REPORT_DIR / "full_history_gap_register.csv"
GAP_SUMMARY = REPORT_DIR / "full_history_gap_summary.md"

EXPECTED_DATASETS = {
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
}


def _rows() -> list[dict[str, str]]:
    with GAP_REGISTER.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_full_history_gap_register_has_exact_ten_formal_datasets() -> None:
    rows = _rows()

    assert {row["dataset"] for row in rows} == EXPECTED_DATASETS
    assert len(rows) == 10
    for row in rows:
        assert row["final_status"] == "limited_window_only"
        assert "target_window_not_covered" in row["issue_code"]
        assert row["issue_category"] == "data_gap"
        assert row["remediation"]
        assert row["evidence_path"]
        assert row["target_window_covered"] == "False"
        assert row["old_baseline_preserved"] == "True"


def test_full_history_summary_blocks_2020_2024_claim_and_preserves_old_evidence() -> None:
    summary = GAP_SUMMARY.read_text(encoding="utf-8")

    assert "supported_window | `2025-02-11..2026-02-18`" in summary
    assert "blocked_window | `2020-01-01..2024-12-31`" in summary
    assert "full_history_status | `research_limited_only`" in summary
    assert "allowed_full_history_production_strict_claim_count" in summary
    assert '"allowed_full_history_production_strict_claim_count": 0' in summary
    assert "old_baseline_preserved | `true`" in summary
    assert "reports/data_lake_readiness_2020_2024/readiness_summary.md" in summary


def test_full_history_forbidden_operation_counters_are_zero() -> None:
    summary = GAP_SUMMARY.read_text(encoding="utf-8")

    for counter in (
        "provider_fetches",
        "lake_writes",
        "credential_reads",
        "legacy_data_reads",
        "old_report_overwrites",
    ):
        assert f"| {counter} | 0 |" in summary
