from __future__ import annotations

from pathlib import Path

import pytest

from engine.research_dataset import (
    attach_execution_claim_metadata,
    read_execution_price_audit,
    resolve_execution_claim_boundary,
)


AUDIT_PATH = Path("reports/data_lake_readiness_2020_2024/execution_price_audit.csv")
BOUNDARY_REPORT = Path("reports/data_lake_readiness_2020_2024_cr013/execution_claim_boundary.md")


def test_execution_audit_resolves_real_vwap_and_fill_as_blocked() -> None:
    audit = read_execution_price_audit(AUDIT_PATH)
    boundary = resolve_execution_claim_boundary(audit, requested_claims=["close_proxy", "real_vwap_execution"])

    assert audit["execution_price_status"] == "required_missing"
    assert audit["true_vwap_available_count"] == 0
    assert "real_vwap_execution" in boundary["blocked_claims"]
    assert "vwap_fill_claim" in boundary["blocked_claims"]
    assert boundary["real_vwap_allowed_claim_count"] == 0
    assert boundary["vwap_fill_allowed_claim_count"] == 0
    assert boundary["minute_execution_allowed_claim_count"] == 0
    assert "close_proxy_research_degradation" in boundary["research_degradation_claims"]
    assert "real_vwap_execution" not in boundary["allowed_claims"]


def test_amount_volume_derived_vwap_attempt_is_not_allowed() -> None:
    audit = read_execution_price_audit(AUDIT_PATH)
    boundary = resolve_execution_claim_boundary(audit, requested_claims=["amount_volume_derived_vwap"])

    assert boundary["derived_vwap_allowed_claim_count"] == 0
    assert boundary["errors"][0]["code"] == "derived_vwap_claim_attempt"
    with pytest.raises(ValueError, match="derived_vwap_claim_attempt"):
        resolve_execution_claim_boundary(
            audit,
            requested_claims=["derived_vwap_from_amount_volume"],
            fail_on_derived_vwap=True,
        )


def test_execution_claim_metadata_and_report_preserve_boundaries() -> None:
    audit = read_execution_price_audit(AUDIT_PATH)
    boundary = resolve_execution_claim_boundary(audit, requested_claims=["framework_validation", "real_vwap_execution"])
    metadata = attach_execution_claim_metadata(
        {"allowed_claims": ["framework_validation", "real_vwap_execution"], "blocked_claims": [], "known_limitations": []},
        boundary,
    )
    report = BOUNDARY_REPORT.read_text(encoding="utf-8")

    assert "real_vwap_execution" not in metadata["allowed_claims"]
    assert any(item["claim"] == "real_vwap_execution" for item in metadata["blocked_claims"])
    assert "Execution / VWAP Claim Boundary" in report
    assert "true_vwap_available_count | `0`" in report
    assert "amount/volume` 不得派生为真实 VWAP" in report
    for counter in ("provider_fetches", "lake_writes", "credential_reads", "legacy_data_reads", "old_report_overwrites"):
        assert f"| {counter} | 0 |" in report

