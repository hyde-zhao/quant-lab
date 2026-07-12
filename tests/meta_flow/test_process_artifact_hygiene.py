from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts.check_process_artifact_hygiene import StatusEntry, check_process_artifact_hygiene, classify_entry


def test_cr132_process_artifact_hygiene_current_workspace_passes() -> None:
    result = check_process_artifact_hygiene(Path("."), Path("process"))

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["runner_development_gate"]["allowed_to_enter_runner_development"] is True


def test_cr132_process_history_residuals_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="process", status="??", path="changes/CR-126-EXAMPLE.md"),
        StatusEntry(repo="process", status="??", path="checks/CP7-CR120-EXAMPLE.md"),
        StatusEntry(repo="process", status="??", path="context/CP2-CR113-EXAMPLE.yaml"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR126.md"),
        StatusEntry(repo="process", status="??", path="stories/STORY-CR118-EXAMPLE.md"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"artifact_history_residual"}


def test_cr132_source_human_gate_residuals_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="scripts/check_human_gate_decision_brief.py"),
        StatusEntry(repo="source", status="??", path="tests/meta_flow/test_human_gate_contracts.py"),
        StatusEntry(repo="source", status="??", path="tests/meta_flow/test_human_gate_contracts.py"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"source_human_gate_residual"}


def test_cr132_current_guardrail_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="scripts/check_process_artifact_hygiene.py"),
        StatusEntry(repo="source", status="M", path="tests/meta_flow/test_process_artifact_hygiene.py"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_guardrail_asset"}


def test_cr165_closed_cr164_assets_are_explicitly_classified() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="engine/strategy_admission_statistical_gate.py"),
        StatusEntry(repo="source", status="??", path="engine/multiple_testing_evidence.py"),
        StatusEntry(repo="process", status="??", path="checks/CP7-CR164-S01.result.json"),
        StatusEntry(repo="process", status="??", path="docs/features/statistical-evidence-contract/DESIGN.md"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"closed_cr164_asset"}


def test_cr165_design_archive_moves_are_explicitly_classified() -> None:
    entries = [
        StatusEntry(repo="process", status="D", path="docs/design/HLD-TRIAL-LINEAGE-INSTRUMENTATION.md"),
        StatusEntry(repo="process", status="??", path="archive/design-cr-docs/HLD-TRIAL-LINEAGE-INSTRUMENTATION.md"),
        StatusEntry(repo="process", status="D", path="docs/design/QUANT-RESEARCH-PRODUCTION-ROADMAP.md"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"design_archive_migration_asset"}


def test_cr165_closed_bundle_remains_classified_after_active_state_clears() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="scripts/legacy/cr/check_cr_tracking_consistency.py"),
        StatusEntry(repo="process", status="??", path="checks/CP8-CR165-DELIVERY-READINESS.result.json"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR165.yaml"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"closed_cr165_asset"}


def test_cr132_cr138_current_assets_are_rule_classified_non_blocking() -> None:
    entries = [
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-138-RUNNER-QMT-GATEWAY-OPERATIONAL-USE-CASE-BASELINE-2026-06-24.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-138.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checkpoints/CP3-CR138-RUNNER-QMT-HLD-REVIEW.md",
        ),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP3-CR138-HLD-CONSISTENCY.md",
        ),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CP3-CR138-RUNNER-QMT-HLD-CONTEXT.yaml",
        ),
    ]

    assert {
        classify_entry(entry, active_cr_numbers=frozenset({"138"}))
        for entry in entries
    } == {"current_cr_asset"}


def test_cr132_cr138_source_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="??", path="trading/runner_control_contracts.py"),
        StatusEntry(repo="source", status="??", path="trading/runner_control_plane.py"),
        StatusEntry(repo="source", status="??", path="trading/runner_control_cli.py"),
        StatusEntry(repo="source", status="M", path="trading/qmt_gateway_service.py"),
        StatusEntry(repo="source", status="M", path="trading/qmt_gateway_contracts.py"),
        StatusEntry(repo="source", status="M", path="trading/qmt_gateway_config.py"),
        StatusEntry(repo="source", status="M", path="trading/qmt_gateway_gates.py"),
        StatusEntry(repo="source", status="??", path="docs/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md"),
        StatusEntry(repo="source", status="??", path="docs/QMT-GATEWAY-INSTALL.md"),
        StatusEntry(repo="source", status="??", path="tests/trading/test_qmt_gateway_contracts.py"),
        StatusEntry(repo="source", status="??", path="tests/trading/test_qmt_gateway_contracts.py"),
    ]

    assert {
        classify_entry(entry, active_cr_numbers=frozenset({"138"}))
        for entry in entries
    } == {"current_cr_asset"}


def test_cr132_cr138_function_named_design_assets_use_active_index_refs() -> None:
    entries = [
        StatusEntry(
            repo="process",
            status="??",
            path="docs/design/HLD-RUNNER-QMT-OPERATIONAL-CONTROL-PLANE.md",
        ),
        StatusEntry(
            repo="process",
            status="??",
            path="docs/design/ARCHITECTURE-DECISION-RUNNER-QMT-OPERATIONAL-CONTROL-PLANE.md",
        ),
        StatusEntry(repo="process", status="??", path="checks/CP2-DISCUSSION-CHECKPOINT.json"),
    ]
    active_paths = frozenset(entry.path for entry in entries)

    assert {
        classify_entry(
            entry,
            active_cr_numbers=frozenset({"138"}),
            active_cr_process_paths=active_paths,
        )
        for entry in entries
    } == {"current_cr_asset"}


def test_cr132_cr138_closed_delivery_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="process", status="M", path="STORY-STATUS.md"),
        StatusEntry(repo="process", status="??", path="STORY-STATUS-CR138.md"),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR138-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="checks/CP8-CR138-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR138.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR138.yaml"),
        StatusEntry(repo="process", status="??", path="evidence/CR138-BATCH.CP7.index.json"),
        StatusEntry(repo="process", status="??", path="returns/CR138-BATCH.CP7.return.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR138-CLOSURE-TO-RUNNER-QMT-NEXT-WORK-CONTEXT-RESET-HANDOFF-2026-06-24.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr_asset"}


def test_cr132_shared_workflow_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path=".gitignore"),
        StatusEntry(repo="source", status="M", path="AGENTS.md"),
        StatusEntry(repo="process", status="M", path="STATE.md"),
        StatusEntry(repo="process", status="M", path="USE-CASES.md"),
        StatusEntry(repo="process", status="M", path="changes/CR-INDEX.json"),
        StatusEntry(repo="process", status="M", path="changes/CR-INDEX.yaml"),
        StatusEntry(
            repo="process",
            status="M",
            path="changes/CR-091-FOLLOW-UP-TRACKING-2026-06-18.md",
        ),
        StatusEntry(
            repo="process",
            status="M",
            path="changes/CR-098-FOLLOW-UP-TRACKING-2026-06-19.md",
        ),
        StatusEntry(repo="process", status="M", path="docs/design/BLUEPRINT.md"),
        StatusEntry(repo="process", status="M", path="docs/design/HLD.md"),
        StatusEntry(repo="process", status="M", path="state/STATE.current.json"),
        StatusEntry(repo="process", status="M", path="state/CR-LEDGER.ndjson"),
        StatusEntry(repo="process", status="M", path="state/CHECKPOINT-LEDGER.ndjson"),
        StatusEntry(repo="process", status="M", path="state/HANDOFF-LEDGER.ndjson"),
        StatusEntry(repo="process", status="M", path="state/READ-EXPANSION-LEDGER.ndjson"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_workflow_shared_asset"}


def test_cr132_runner_simulation_entry_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="trading/qmt_client.py"),
        StatusEntry(repo="source", status="M", path="trading/qmt_runtime.py"),
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/__init__.py"),
        StatusEntry(repo="source", status="??", path="trading/strategy_runner/simulation_activation.py"),
        StatusEntry(repo="source", status="M", path="tests/trading/test_linux_client_rest_transport.py"),
        StatusEntry(repo="source", status="M", path="tests/trading/test_runtime_manual_validation.py"),
        StatusEntry(repo="source", status="??", path="tests/runner/test_runner_simulation_activation.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/RUNNER-MODEL-SIMULATION-LIVE-ENTRY-WORK-PACKAGE-2026-06-24.md",
        ),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/RUNNER-MODEL-SIMULATION-LIVE-ENTRY-VERIFICATION-2026-06-24.md",
        ),
        StatusEntry(
            repo="process",
            status="??",
            path="context/RUNNER-SIMULATION-TRADING-MACHINE-SMOKE-HANDOFF-2026-06-24.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {
        "current_runner_simulation_entry_asset"
    }


def test_cr132_cr134_current_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="??", path="trading/strategy_runner/evidence_index.py"),
        StatusEntry(repo="source", status="??", path="tests/runner/test_runner_evidence_index.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-134-RUNNER-EVIDENCE-INDEX-INTEGRATION-2026-06-23.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr134_asset"}


def test_cr132_cr135_start_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="??", path="tests/runner/test_runner_artifact_bundle.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-135-RUNNER-EXECUTION-ARTIFACT-BUNDLE-REPLAY-WORKFLOW-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-135.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP7-CR135-RUNNER-ARTIFACT-BUNDLE-VERIFICATION-DONE.md",
        ),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR135-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR135.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR135.yaml"),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr135_asset"}


def test_cr132_cr136_start_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/artifact_bundle.py"),
        StatusEntry(repo="source", status="??", path="tests/runner/test_runner_bundle_validation.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-136-RUNNER-BUNDLE-SCHEMA-COMPATIBILITY-VALIDATION-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-136.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP7-CR136-RUNNER-BUNDLE-VALIDATION-VERIFICATION-DONE.md",
        ),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR136-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR136.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR136.yaml"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR136-CLOSURE-TO-CR137-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr136_asset"}


def test_cr132_cr137_start_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/run_spec.py"),
        StatusEntry(repo="source", status="M", path="trading/strategy_runner/runner.py"),
        StatusEntry(repo="source", status="??", path="trading/strategy_runner/run_registry.py"),
        StatusEntry(repo="source", status="??", path="tests/runner/test_runner_run_registry.py"),
        StatusEntry(
            repo="process",
            status="??",
            path="changes/CR-137-OFFLINE-RUNNER-RUN-REGISTRY-2026-06-23.md",
        ),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-137.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="checks/CP7-CR137-RUNNER-RUN-REGISTRY-VERIFICATION-DONE.md",
        ),
        StatusEntry(repo="process", status="??", path="checkpoints/CP8-CR137-DELIVERY-READINESS.md"),
        StatusEntry(repo="process", status="??", path="docs/release/RELEASE-NOTES-CR137.md"),
        StatusEntry(repo="process", status="??", path="release/RELEASE-CONTEXT-CR137.yaml"),
        StatusEntry(repo="process", status="??", path="archive/CR-137/evidence-index.json"),
        StatusEntry(repo="process", status="M", path="docs/features/strategy-runner-core/DESIGN.md"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR137-CLOSURE-TO-RUNNER-QMT-USE-CASE-CONTEXT-RESET-HANDOFF-2026-06-24.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr137_asset"}


def test_cr132_cr089_closure_assets_are_classified_non_blocking() -> None:
    entries = [
        StatusEntry(
            repo="process",
            status="M",
            path="changes/CR-089-QMT-INTERFACE-VALIDATION-GATE-2026-06-17.md",
        ),
        StatusEntry(repo="process", status="??", path="archive/CR-089/evidence-index.json"),
        StatusEntry(repo="process", status="??", path="changes/summaries/CR-089.summary.json"),
        StatusEntry(
            repo="process",
            status="??",
            path="context/CR089-CLOSURE-TO-CR135-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        ),
    ]

    assert {classify_entry(entry) for entry in entries} == {"current_cr089_closure_asset"}


def test_cr132_unknown_residual_is_unclassified() -> None:
    assert classify_entry(StatusEntry(repo="source", status="??", path="runner_tmp.txt")) == "unclassified"
    assert classify_entry(StatusEntry(repo="process", status="??", path="changes/CR-999-UNKNOWN.md")) == "unclassified"


def test_cr132_process_artifact_hygiene_cli_json() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_process_artifact_hygiene.py",
            "--source-root",
            ".",
            "--process-root",
            "process",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["schema_version"] == "cr132-process-artifact-hygiene-check-v1"
    assert payload["passed"] is True
