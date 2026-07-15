"""CR-169 S05：量化 QAC、fixture 与 Stage2 退出合同。"""

from __future__ import annotations

import ast
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import re

from engine.capacity_liquidity_evidence import (
    C4_REASON_CODES,
    CapacityLiquidityEvidenceInput,
    build_capacity_liquidity_evidence,
)
from engine.strategy_evidence import ComponentCatalogStatus, component_catalog_status
from scripts.check_stage2_exit_contracts import (
    C4_REMEDIATION_ROUTE,
    HISTORICAL_REMEDIATION_ROUTE,
    STAGE2_CONTRACT_IDS,
    build_stage2_exit_verification,
)


ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "capacity_liquidity"
REQUIREMENT_IDS = tuple(f"REQ-CR169-{index:03d}" for index in range(1, 10))
SCENARIO_IDS = (
    "SC-CR169-P01", "SC-CR169-P02",
    *(f"SC-CR169-N{index:02d}" for index in range(1, 11)),
    "SC-CR169-B01", "SC-CR169-B02", "SC-CR169-B03", "SC-CR169-G01", "SC-CR169-E01",
)
QAC_IDS = tuple(f"QAC-CR169-{index:02d}" for index in range(1, 16))


def _daily_fixture() -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / "daily_multifactor_v1.json").read_text(encoding="utf-8"))


def _input(values: dict[str, object]) -> CapacityLiquidityEvidenceInput:
    normalized = dict(values)
    for key in ("lineage_refs", "provenance_refs", "authorization_refs", "limitations"):
        if key in normalized:
            normalized[key] = tuple(normalized[key])
    return CapacityLiquidityEvidenceInput(**normalized)


def test_exact_two_fixture_families_and_daily_expected_values() -> None:
    fixture_files = sorted(FIXTURE_ROOT.glob("*.json"))
    assert [path.name for path in fixture_files] == ["daily_multifactor_v1.json", "multi_strategy_compatibility_v1.json"]
    fixture = _daily_fixture()
    result = build_capacity_liquidity_evidence(_input(fixture["input"]))

    assert result.passed and result.evidence is not None
    expected = fixture["expected"]
    assert result.evidence.breakdown.participation_ratio == Decimal(expected["participation_ratio"])
    assert result.evidence.breakdown.capacity_amount == Decimal(expected["capacity_amount"])
    assert result.evidence.breakdown.liquidity_headroom == Decimal(expected["liquidity_headroom"])
    assert result.evidence.breakdown.within_declared_cap is expected["within_declared_cap"]
    assert 2 + len(result.evidence.liquidity_sizing_refs) == expected["gate4_ref_count"]


def test_multi_strategy_fixture_separates_component_semantics_from_attachment_identity() -> None:
    fixture = json.loads((FIXTURE_ROOT / "multi_strategy_compatibility_v1.json").read_text(encoding="utf-8"))
    body = fixture["common_computational_body"]
    daily = build_capacity_liquidity_evidence(_input({**body, **fixture["attachments"]["daily_multifactor"]}))
    ml = build_capacity_liquidity_evidence(_input({**body, **fixture["attachments"]["ml"]}))

    assert daily.evidence is not None and ml.evidence is not None
    assert {daily.evidence.component_hash, ml.evidence.component_hash} == {daily.evidence.component_hash}
    assert daily.attachment_context != ml.attachment_context
    assert daily.header != ml.header


def test_product_baseline_has_exact_9_requirements_17_scenarios_and_15_qac() -> None:
    requirements = (ROOT / "docs" / "product" / "REQUIREMENTS.md").read_text(encoding="utf-8")
    scenarios = (ROOT / "docs" / "product" / "SCENARIOS.yaml").read_text(encoding="utf-8")
    found_requirements = set(re.findall(r"REQ-CR169-\d{3}", requirements))
    found_scenarios = set(re.findall(r"SC-CR169-[A-Z]\d{2}", scenarios))
    found_qac = set(re.findall(r"QAC-CR169-\d{2}", requirements))

    assert found_requirements == set(REQUIREMENT_IDS)
    assert found_scenarios == set(SCENARIO_IDS)
    assert found_qac == set(QAC_IDS)


def test_exact_twelve_fail_closed_classes_and_single_active_schema() -> None:
    assert len(C4_REASON_CODES) == 12
    assert len(set(C4_REASON_CODES)) == 12
    assert component_catalog_status("capacity_liquidity", "v1") is ComponentCatalogStatus.ACTIVE
    assert component_catalog_status("capacity_liquidity", "v2") is ComponentCatalogStatus.UNKNOWN


def test_ten_runs_produce_one_hash_and_claim_ceiling_remains_false() -> None:
    fixture = _daily_fixture()
    results = [build_capacity_liquidity_evidence(_input(fixture["input"])) for _ in range(10)]
    evidence = [result.evidence for result in results]
    assert all(item is not None for item in evidence)
    assert len({item.component_hash for item in evidence if item is not None}) == 1
    assert all(item.real_adv_available is False for item in evidence if item is not None)
    assert all(item.real_liquidity_available is False for item in evidence if item is not None)
    assert all(item.capacity_ready is False for item in evidence if item is not None)
    assert all(item.alpha_decay_calculator == 0 for item in evidence if item is not None)


def test_capability_registry_missing_uses_explicit_na_reason_and_existing_feature_refs() -> None:
    registry = _daily_fixture()["capability_registry"]
    assert registry["availability"] == "not_applicable_with_reason"
    assert registry["reason"]
    refs = registry["feature_refs"]
    assert len(refs) == 2
    assert all((ROOT / ref).is_file() for ref in refs)


def _entries(status: str = "PASS") -> list[dict[str, object]]:
    return [
        {"contract_id": contract_id, "status": status, "evidence_refs": ["pyproject.toml"], "notes": "unit fixture"}
        for contract_id in STAGE2_CONTRACT_IDS
    ]


def test_stage2_exit_passes_only_for_exact_seven_pass_entries() -> None:
    result = build_stage2_exit_verification(_entries(), project_root=ROOT, checked_at="2026-07-15T00:00:00+00:00")
    assert [item["contract_id"] for item in result["items"]] == list(STAGE2_CONTRACT_IDS)
    assert result["counts"] == {"required": 7, "pass": 7, "fail": 0, "blocked": 0}
    assert result["decision"] == "PASS"
    assert result["stage2_complete"] is True
    assert result["stage3_entry_ready"] is False
    assert result["follow_up_routes"] == []


def test_stage2_historical_and_c4_failures_have_distinct_routes() -> None:
    historical = _entries()
    historical[0] = {"contract_id": STAGE2_CONTRACT_IDS[0], "status": "PASS", "evidence_refs": []}
    historical_result = build_stage2_exit_verification(historical, project_root=ROOT)
    assert historical_result["decision"] == "BLOCKED"
    assert historical_result["blockers"][0]["route"] == HISTORICAL_REMEDIATION_ROUTE

    c4 = _entries()
    c4[-1] = {"contract_id": STAGE2_CONTRACT_IDS[-1], "status": "PASS", "evidence_refs": []}
    c4_result = build_stage2_exit_verification(c4, project_root=ROOT)
    assert c4_result["decision"] == "BLOCKED"
    assert c4_result["blockers"][0]["route"] == C4_REMEDIATION_ROUTE
    assert c4_result["stage3_entry_ready"] is False


def test_stage2_checker_rejects_external_evidence_and_preserves_zero_operations() -> None:
    entries = _entries()
    entries[0] = {"contract_id": STAGE2_CONTRACT_IDS[0], "status": "PASS", "evidence_refs": ["/etc/hosts"]}
    result = build_stage2_exit_verification(entries, project_root=ROOT)
    assert result["items"][0]["status"] == "BLOCKED"
    assert set(result["operation_counts"].values()) == {0}


def test_forbidden_integration_sources_are_not_consumed_by_cr169_modules() -> None:
    projection = (ROOT / "engine" / "capacity_liquidity_gate4_projection.py").read_text(encoding="utf-8")
    evidence = (ROOT / "engine" / "capacity_liquidity_evidence.py").read_text(encoding="utf-8")
    assert "strategy_admission_package" not in projection
    assert "economic_cost_gate4_projection" not in projection
    imported_modules = {
        alias.name
        for node in ast.walk(ast.parse(evidence))
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(ast.parse(evidence))
        if isinstance(node, ast.ImportFrom)
    }
    assert all(not name.startswith(("requests", "httpx", "boto", "tushare", "qmt")) for name in imported_modules)
