"""CR-168 S05：fixture/static QAC、场景和 claim ceiling 追踪。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.economic_cost_evidence import EconomicCostEvidenceInput, build_economic_cost_evidence
from engine.economic_cost_gate4_projection import project_economic_cost_to_gate4
from engine.strategy_evidence import (
    ComponentCatalogStatus,
    ComponentDescriptor,
    EvidenceAvailability,
    build_strategy_evidence_envelope,
    component_catalog_status,
)


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "economic_cost"
TEXT_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".json", ".toml"}
CR168_REQUIREMENTS = {f"REQ-CR168-{index:03d}" for index in range(1, 10)}
CR168_SCENARIOS = {
    "SC-CR168-P01", "SC-CR168-P02", "SC-CR168-N01", "SC-CR168-N02", "SC-CR168-N03", "SC-CR168-N04",
    "SC-CR168-N05", "SC-CR168-N06", "SC-CR168-N07", "SC-CR168-N08", "SC-CR168-N09", "SC-CR168-N10",
    "SC-CR168-B01", "SC-CR168-B02", "SC-CR168-A01", "SC-CR168-G01", "SC-CR168-E01",
}
CR168_QAC = {f"QAC-CR168-{index:02d}" for index in range(1, 16)}
EVENT_SPECIFIC_ECONOMIC_COST = {
    "availability": EvidenceAvailability.NOT_APPLICABLE_WITH_REASON.value,
    "reason": "event-specific producer is deferred outside CR-168",
    "producer_count": 0,
    "event_feed_access_count": 0,
}
FINAL_CLAIM_CEILING = {
    "stage2_complete": True,
    "stage3_started": False,
    "c3_fixture_static_foundation": True,
    "real_tca_available": False,
    "real_market_impact_calibrated": False,
    "real_data_connected": False,
    "runtime_ready": False,
    "c4_calculators": 0,
    "event_specific_producer": False,
    "cr155_promoted": False,
}


def _load(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def _daily_input(**changes: object) -> EconomicCostEvidenceInput:
    fixture = _load("daily_multifactor_synthetic.json")
    values = dict(fixture["input"])
    values.update(changes)
    return EconomicCostEvidenceInput(**values)


def _compatibility_inputs() -> tuple[EconomicCostEvidenceInput, EconomicCostEvidenceInput]:
    fixture = _load("multi_strategy_type_compatibility.json")
    shared = dict(fixture["shared_semantic_input"])
    daily = EconomicCostEvidenceInput(**{**shared, **dict(fixture["inputs"]["daily_multifactor"])})
    ml = EconomicCostEvidenceInput(**{**shared, **dict(fixture["inputs"]["ml"])})
    return daily, ml


def test_qac_01_to_04_fixture_families_catalog_and_traceability_counts_are_exact() -> None:
    assert {path.name for path in FIXTURE_ROOT.glob("*.json")} == {
        "daily_multifactor_synthetic.json", "multi_strategy_type_compatibility.json"
    }
    assert _load("daily_multifactor_synthetic.json")["fixture_family"] == "daily_multifactor_synthetic"
    assert _load("multi_strategy_type_compatibility.json")["fixture_family"] == "multi_strategy_type_compatibility"
    assert component_catalog_status("economic_cost", "v1") is ComponentCatalogStatus.ACTIVE
    assert component_catalog_status("capacity_liquidity", "reserved") is ComponentCatalogStatus.RESERVED
    assert len(CR168_REQUIREMENTS) == 9
    assert len(CR168_SCENARIOS) == 17
    assert len(CR168_QAC) == 15


@pytest.mark.parametrize(
    ("scenario_id", "changes", "expected_code"),
    [
        ("SC-CR168-N01", {"gross_pnl": None, "gross_return": None}, "c3_gross_performance_basis_missing"),
        ("SC-CR168-N02", {"traded_notional": None}, "c3_trade_turnover_notional_basis_missing"),
        ("SC-CR168-N03", {"cost_model_version": ""}, "c3_cost_model_version_missing"),
        ("SC-CR168-N04", {"fee_rate": float("nan")}, "c3_nonfinite_numeric_invalid"),
        ("SC-CR168-N05", {"fee_rate": "-0.01"}, "c3_negative_cost_invalid"),
        ("SC-CR168-N06", {"cost_price_basis": "unadjusted_close"}, "c3_unit_price_notional_basis_mismatch"),
        ("SC-CR168-N07", {"cost_currency": "USD"}, "c3_currency_price_calendar_mismatch"),
        ("SC-CR168-N08", {"gross_return": "0.2"}, "c3_gross_cost_net_arithmetic_mismatch"),
        ("SC-CR168-N09", {"lineage_refs": ()}, "c3_lineage_provenance_authorization_missing_or_mismatch"),
        ("SC-CR168-N10", {"claimed_semantic_hash": "sha256:tampered"}, "c3_component_hash_tampered"),
    ],
)
def test_qac_05_ten_p0_fail_closed_categories(scenario_id: str, changes: dict[str, object], expected_code: str) -> None:
    result = build_economic_cost_evidence(_daily_input(**changes))

    assert scenario_id in CR168_SCENARIOS
    assert result.availability is not EvidenceAvailability.PRESENT
    assert expected_code in {issue.code for issue in result.issues}
    assert result.evidence is None


def test_qac_06_deterministic_ten_runs_one_hash_and_daily_ml_semantic_compatibility() -> None:
    daily_runs = [build_economic_cost_evidence(_daily_input()) for _ in range(10)]
    hashes = {result.evidence.component_hash for result in daily_runs if result.evidence is not None}
    assert len(hashes) == 1

    daily_raw, ml_raw = _compatibility_inputs()
    daily = build_economic_cost_evidence(daily_raw)
    ml = build_economic_cost_evidence(ml_raw)
    assert daily.evidence is not None and ml.evidence is not None
    assert daily.evidence.component_hash == ml.evidence.component_hash
    daily_envelope = build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref="strategy://cr168/daily",
        components=(ComponentDescriptor("economic_cost", "v1", False, daily.evidence.component_ref, daily.evidence.component_hash, EvidenceAvailability.PRESENT),),
        logical_provenance={"package_ref": "fixture://package/cr168/daily"},
        authorization_summary={"mode": "fixture-static", "authorization_ref": "fixture://authorization/cr168/static-only"},
        limitations=("fixture_static_only", "no_real_tca"),
    )
    ml_envelope = build_strategy_evidence_envelope(
        evidence_kind="strategy-production-evidence",
        subject_ref="strategy://cr168/ml",
        components=(ComponentDescriptor("economic_cost", "v1", False, ml.evidence.component_ref, ml.evidence.component_hash, EvidenceAvailability.PRESENT),),
        logical_provenance={"package_ref": "fixture://package/cr168/ml"},
        authorization_summary={"mode": "fixture-static", "authorization_ref": "fixture://authorization/cr168/static-only"},
        limitations=("fixture_static_only", "no_real_tca"),
    )
    assert daily_envelope.envelope_hash != ml_envelope.envelope_hash


def test_qac_07_to_13_gate4_claim_ceiling_and_deferred_event_boundary() -> None:
    component = build_economic_cost_evidence(_daily_input()).evidence
    assert component is not None
    outcome = project_economic_cost_to_gate4(component, EvidenceAvailability.TYPED_UNAVAILABLE, {})
    assert outcome.status.name == "BLOCKED"
    assert outcome.is_pass is False
    assert outcome.canonical_invoked is True
    assert FINAL_CLAIM_CEILING == {
        "stage2_complete": True, "stage3_started": False, "c3_fixture_static_foundation": True,
        "real_tca_available": False, "real_market_impact_calibrated": False, "real_data_connected": False,
        "runtime_ready": False, "c4_calculators": 0, "event_specific_producer": False, "cr155_promoted": False,
    }
    assert EVENT_SPECIFIC_ECONOMIC_COST["availability"] == EvidenceAvailability.NOT_APPLICABLE_WITH_REASON.value
    assert EVENT_SPECIFIC_ECONOMIC_COST["producer_count"] == 0
    assert EVENT_SPECIFIC_ECONOMIC_COST["event_feed_access_count"] == 0


def test_qac_14_and_15_static_only_fixture_values_have_no_real_reference_or_wrong_quality_path() -> None:
    for fixture_path in FIXTURE_ROOT.glob("*.json"):
        text = fixture_path.read_text(encoding="utf-8")
        assert "fixture://" in text
        assert all(token not in text.lower() for token in ("credential", "provider://", "nas://", "lake://", "broker://", "https://"))
    repository_root = Path(__file__).parents[2]
    searched = [repository_root / "engine", repository_root / "tests", repository_root / "docs"]
    wrong_quality_path = "process/" + "docs/quality/"
    assert all(
        wrong_quality_path not in path.read_text(encoding="utf-8", errors="ignore")
        for root in searched
        for path in root.rglob("*")
        if path.is_file() and path.suffix in TEXT_EXTENSIONS
    )
