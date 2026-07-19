"""CR-172 S05：trace、claim ceiling、deferred boundary 与零操作 QAC。"""

from __future__ import annotations

import ast
from dataclasses import fields
from datetime import timedelta
from pathlib import Path
import re

from engine.path_i_governance import (
    LEGACY_RUN_LOGICAL_ROOT_TEMPLATE,
    NEW_RUN_LOGICAL_ROOT_TEMPLATE,
    RUN_PATH_DELIVERY_STATUS,
    EmpiricalRInputsV1,
    EmpiricalRStateV1,
    PathIClaimCeilingV1,
    RunPathIntentV1,
    RunPathModeV1,
    SignalBatchBoundaryV1,
    SignatureKeySlotV1,
    ValidityWindowSlotV1,
    classify_empirical_r,
    decide_run_path,
    enforce_path_i_claim_ceiling,
    validate_signal_batch_boundary,
)
from tests.fixtures.cr172_path_i.path_i_fixture import load_fixture, parse_time


ROOT = Path(__file__).resolve().parents[2]
S05_TESTS = (
    ROOT / "tests/research/test_cr172_path_i_integration.py",
    ROOT / "tests/research/test_cr172_path_i_authorization.py",
    ROOT / "tests/research/test_cr172_path_i_claim_regression.py",
)
FIXTURE_HELPER = ROOT / "tests/fixtures/cr172_path_i/path_i_fixture.py"


def test_traceability_is_exact_and_total() -> None:
    fixture = load_fixture()
    requirements = fixture["requirements"]
    scenarios = fixture["scenarios"]
    outcomes = fixture["outcomes"]
    covered_requirements = {
        requirement
        for scenario in scenarios
        for requirement in scenario["requirements"]
    }
    covered_outcomes = {
        outcome for scenario in scenarios for outcome in scenario["outcomes"]
    }
    collected_test_names = {
        match.group(1)
        for path in S05_TESTS
        for match in re.finditer(
            r"^def (test_[A-Za-z0-9_]+)\(",
            path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    }

    assert len(requirements) == len(set(requirements)) == 15
    assert len(scenarios) == len({scenario["id"] for scenario in scenarios}) == 27
    assert len(outcomes) == len(set(outcomes)) == 11
    assert covered_requirements == set(requirements)
    assert covered_outcomes == set(outcomes)
    assert {scenario["test"] for scenario in scenarios} == collected_test_names
    assert len(collected_test_names) == 27

    scenarios_by_id = {scenario["id"]: scenario for scenario in scenarios}
    expected_semantic_bindings = {
        "SC-CR172-006": {
            "test": "test_partial_lineage_never_advances_selection",
            "requirements": ["REQ-CR172-006"],
        },
        "SC-CR172-021": {
            "test": "test_req013_is_contract_ready_only",
            "requirements": ["REQ-CR172-013"],
        },
    }
    semantic_mismatches = [
        scenario_id
        for scenario_id, expected_binding in expected_semantic_bindings.items()
        if scenarios_by_id[scenario_id]["test"] != expected_binding["test"]
        or scenarios_by_id[scenario_id]["requirements"]
        != expected_binding["requirements"]
    ]
    assert semantic_mismatches == []


def test_req013_is_contract_ready_only() -> None:
    oracle = load_fixture()["req013"]
    decision = decide_run_path(
        RunPathIntentV1(
            mode=RunPathModeV1.NEW_SEMANTIC_ROOT,
            logical_root=NEW_RUN_LOGICAL_ROOT_TEMPLATE,
            requested_operation="contract",
        )
    )
    legacy = decide_run_path(
        RunPathIntentV1(
            mode=RunPathModeV1.LEGACY_READ_ONLY,
            logical_root=LEGACY_RUN_LOGICAL_ROOT_TEMPLATE,
            requested_operation="read",
        )
    )

    assert decision.writable is False
    assert legacy.writable is False
    assert decision.delivery_status == RUN_PATH_DELIVERY_STATUS
    assert legacy.delivery_status == RUN_PATH_DELIVERY_STATUS
    assert RUN_PATH_DELIVERY_STATUS == "contract_ready/runtime_enforcement_deferred"
    assert oracle == {
        "contract_ready": 1,
        "runtime_path_enforcement": 0,
        "default_switch": 0,
        "runtime_delivered": 0,
        "future_prerequisite": 1,
    }


def test_five_high_order_claims_remain_false() -> None:
    fixture = load_fixture()
    claim = enforce_path_i_claim_ceiling(PathIClaimCeilingV1(path_i_design_ready=True))
    values = {
        "stage3_entry_ready": claim.stage3_entry_ready,
        "c1_computable": claim.c1_computable,
        "real_data_authorized": claim.real_data_authorized,
        "multi_trial_runtime_authorized": claim.multi_trial_runtime_authorized,
        "signal_transport_authorized": claim.signal_transport_authorized,
    }

    assert values == fixture["high_order_claims"]
    assert sum(values.values()) == 0


def test_signal_is_only_an_eight_slot_boundary() -> None:
    fixture = load_fixture()
    start = parse_time(fixture["times"]["evaluated_at"])
    boundary = SignalBatchBoundaryV1(
        schema_version="signal-batch-boundary.v1",
        batch_id="batch-cr172-fixture-001",
        strategy_id="strategy-cr172-fixture-001",
        strategy_package_hash="sha256:" + "2" * 64,
        content_sha256="sha256:" + "3" * 64,
        signature_key=SignatureKeySlotV1(
            signature="fixture-signature",
            key_id="fixture-key-id",
        ),
        validity_window=ValidityWindowSlotV1(
            valid_from=start,
            valid_until=start + timedelta(minutes=5),
        ),
        sequence_no=1,
    )

    assert validate_signal_batch_boundary(boundary) is boundary
    assert len(fields(SignalBatchBoundaryV1)) == 8


def test_deferred_capabilities_have_no_runtime_surface() -> None:
    fixture = load_fixture()
    deferred = fixture["deferred"]
    forbidden_runtime_symbols = {
        "SignalTransport",
        "SignalMailbox",
        "FuV2Runtime",
        "PublicC1Projection",
        "LegacyMigrator",
        "RealPathIRuntimeAdapter",
    }
    imported_engine_symbols = set()
    for path in (*S05_TESTS, FIXTURE_HELPER):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_engine_symbols.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and (node.module or "").startswith("engine")
            for alias in node.names
        )

    assert set(deferred.values()) == {0}
    assert imported_engine_symbols.isdisjoint(forbidden_runtime_symbols)


def test_zero_real_operation_ledger_is_exact() -> None:
    operations = load_fixture()["real_operations"]

    assert len(operations) == 6
    assert sum(item["authorized"] for item in operations.values()) == 0
    assert sum(item["executed"] for item in operations.values()) == 0
    assert all(set(item) == {"authorized", "executed"} for item in operations.values())


def test_empirical_r_stays_typed_unavailable_without_real_source() -> None:
    disposition = classify_empirical_r(
        EmpiricalRInputsV1(
            declared_fixture_matrix=False,
            source_available=False,
            sealed_provenance_complete=False,
            alignment_complete=False,
            method_version_ref="FU-CR173-001-deferred",
            method_hash_valid=False,
            compute_decision=None,
            integrity_conflict=False,
            unapproved_repair=False,
            independently_verified=False,
        )
    )

    assert disposition.state is EmpiricalRStateV1.TYPED_UNAVAILABLE
    assert disposition.positive_effective_count is False
    assert disposition.c1_computable is False
    assert disposition.computation_authorization_ref == ""


def test_s05_imports_no_runner_lineage_or_real_adapter() -> None:
    forbidden_modules = {
        "engine.mature_multifactor_research",
        "engine.experiment_family_lineage",
        "engine.effective_trial_evidence",
        "engine.effective_trial_estimator",
        "subprocess",
        "socket",
        "requests",
    }
    imported_modules = set()
    for path in (*S05_TESTS, FIXTURE_HELPER):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

    assert imported_modules.isdisjoint(forbidden_modules)
