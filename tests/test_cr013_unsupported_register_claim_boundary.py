from __future__ import annotations

from pathlib import Path

import pytest

from engine.research_dataset import read_execution_price_audit, resolve_execution_claim_boundary
from experiments.reporting import (
    attach_report_claim_boundary,
    build_claim_boundary_summary,
    read_unsupported_data_register,
    render_cr013_claim_boundary_summary,
)


REGISTER_PATH = Path("reports/data_lake_readiness_limited_2025_2026/unsupported_data_register.csv")
SUMMARY_PATH = Path("reports/data_lake_readiness_2020_2024_cr013/unsupported_claim_boundary_summary.md")
README_PATH = Path("README.md")
USER_MANUAL_PATH = Path("docs/USER-MANUAL.md")

EXPECTED_ITEMS = {
    "industry_classification",
    "market_cap",
    "style_exposure_beta_size_value_quality",
    "capacity_inputs_turnover_adv_constraints",
    "corporate_actions_full",
    "non_hs300_benchmark",
    "minute_tick_level2_order_match",
    "microstructure_impact_cost",
    "real_vwap_execution",
}


def test_unsupported_register_exact_rows_and_excluded_denominator() -> None:
    rows = read_unsupported_data_register(REGISTER_PATH)

    assert {row["data_item"] for row in rows} == EXPECTED_ITEMS
    assert len(rows) == 9
    assert {row["pass_denominator"] for row in rows} == {"excluded"}
    assert all(row["reason"] for row in rows)


def test_claim_boundary_summary_merges_s01_s02_and_excludes_denominator() -> None:
    rows = read_unsupported_data_register(REGISTER_PATH)
    audit = read_execution_price_audit("reports/data_lake_readiness_2020_2024/execution_price_audit.csv")
    execution_boundary = resolve_execution_claim_boundary(audit)
    summary = build_claim_boundary_summary(
        rows,
        {
            "supported_window": "2025-02-11..2026-02-18",
            "blocked_window": "2020-01-01..2024-12-31",
            "full_history_status": "research_limited_only",
        },
        execution_boundary,
    )
    metadata = attach_report_claim_boundary({"allowed_claims": ["framework_validation"]}, summary)
    rendered = render_cr013_claim_boundary_summary(summary)

    assert summary["supported_window"] == "2025-02-11..2026-02-18"
    assert summary["blocked_window"] == "2020-01-01..2024-12-31"
    assert summary["pass_denominator_policy"]["excluded_in_formal_pass_denominator_count"] == 0
    assert "real_vwap_execution" in summary["blocked_claims"]
    assert metadata["old_baseline_preserved"] is True
    assert "CR-013 Claim Boundary Summary" in rendered


def test_unsupported_register_missing_field_fails(tmp_path: Path) -> None:
    bad_register = tmp_path / "unsupported_data_register.csv"
    bad_register.write_text("data_item,status,pass_denominator\nindustry_classification,research_contract_only,excluded\n")

    with pytest.raises(ValueError, match="unsupported_register_missing_field"):
        read_unsupported_data_register(bad_register)


def test_docs_and_report_show_supported_research_only_unsupported_blocked_boundaries() -> None:
    summary = SUMMARY_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    manual = USER_MANUAL_PATH.read_text(encoding="utf-8")

    for text in (summary, readme, manual):
        assert "2025-02-11..2026-02-18" in text
        assert "2020-01-01..2024-12-31" in text
        assert "research_only" in text or "research-only" in text
        assert "unsupported" in text
        assert "blocked" in text
        assert "real_vwap_execution" in text
    assert "excluded_in_formal_pass_denominator_count" in summary
    assert '"unsupported_data_item_count": 9' in summary
    for counter in ("provider_fetches", "lake_writes", "credential_reads", "legacy_data_reads", "old_report_overwrites"):
        assert f"| {counter} | 0 |" in summary

