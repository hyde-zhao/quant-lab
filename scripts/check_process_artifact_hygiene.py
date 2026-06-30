from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Any


KNOWN_SOURCE_RESIDUALS = frozenset(
    {
        "scripts/check_human_gate_decision_brief.py",
        "tests/meta_flow/test_human_gate_contracts.py",
        "tests/meta_flow/test_human_gate_contracts.py",
    }
)

CURRENT_CR132_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
    }
)

CURRENT_GUARDRAIL_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
    }
)

CURRENT_WORKFLOW_SHARED_SOURCE_ASSETS = frozenset(
    {
        ".gitignore",
        "AGENTS.md",
    }
)

CURRENT_WORKFLOW_SHARED_PROCESS_ASSETS = frozenset(
    {
        "STATE.md",
        "USE-CASES.md",
        "REQUIREMENTS.md",
        "baseline/CURRENT-REQUIREMENT-BASELINE.yaml",
        "changes/CR-INDEX.json",
        "changes/CR-INDEX.yaml",
        "changes/CR-091-FOLLOW-UP-TRACKING-2026-06-18.md",
        "changes/CR-098-FOLLOW-UP-TRACKING-2026-06-19.md",
        "docs/design/ARCHITECTURE-DECISION.md",
        "docs/design/BLUEPRINT.md",
        "docs/design/DEPENDENCY-MAP.md",
        "docs/design/DOMAIN-MAP.md",
        "docs/design/HLD.md",
        "docs/design/FEATURE-DESIGN-MATRIX.md",
        "state/CHECKPOINT-LEDGER.ndjson",
        "state/CR-LEDGER.ndjson",
        "state/HANDOFF-LEDGER.ndjson",
        "state/READ-EXPANSION-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR132_PROCESS_ASSETS = frozenset(
    {
        "changes/CR-132-RESIDUAL-PROCESS-ARTIFACT-HYGIENE-2026-06-23.md",
        "checks/CP6-CR132-PROCESS-ARTIFACT-HYGIENE-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR132-PROCESS-ARTIFACT-HYGIENE-VERIFICATION-DONE.md",
        "checks/CR132-PROCESS-ARTIFACT-HYGIENE-REPORT.json",
        "context/CP6-CR132.context.json",
    }
)

CURRENT_CR133_SOURCE_ASSETS = frozenset(
    {
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/cli.py",
        "trading/strategy_runner/result.py",
        "trading/strategy_runner/run_spec.py",
        "trading/strategy_runner/runner.py",
        "tests/runner/test_runner_spec_cli.py",
    }
)

CURRENT_CR133_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-132/evidence-index.json",
        "archive/CR-133/evidence-index.json",
        "changes/CR-132-RESIDUAL-PROCESS-ARTIFACT-HYGIENE-2026-06-23.md",
        "changes/CR-133-STRATEGY-RUNNER-CORE-NEXT-SLICE-2026-06-23.md",
        "changes/CR-INDEX.json",
        "changes/summaries/CR-132.summary.json",
        "changes/summaries/CR-133.summary.json",
        "checks/CP6-CR133-RUNNER-SPEC-CLI-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR133-RUNNER-SPEC-CLI-VERIFICATION-DONE.md",
        "context/CP6-CR133.context.json",
        "context/CR133-TO-CR134-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR134_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
        "tests/runner/test_runner_evidence_index.py",
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/cli.py",
        "trading/strategy_runner/evidence_index.py",
        "trading/strategy_runner/run_spec.py",
        "trading/strategy_runner/runner.py",
    }
)

CURRENT_CR134_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-134/evidence-index.json",
        "changes/CR-134-RUNNER-EVIDENCE-INDEX-INTEGRATION-2026-06-23.md",
        "changes/CR-INDEX.json",
        "changes/CR-INDEX.yaml",
        "changes/summaries/CR-134.summary.json",
        "checks/CP6-CR134-RUNNER-EVIDENCE-INDEX-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR134-RUNNER-EVIDENCE-INDEX-VERIFICATION-DONE.md",
        "context/CP6-CR134.context.json",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR135_PROCESS_ASSETS = frozenset(
    {
        "changes/CR-135-RUNNER-EXECUTION-ARTIFACT-BUNDLE-REPLAY-WORKFLOW-2026-06-23.md",
        "archive/CR-135/evidence-index.json",
        "changes/CR-INDEX.json",
        "changes/CR-INDEX.yaml",
        "changes/summaries/CR-135.summary.json",
        "checkpoints/CP8-CR135-DELIVERY-READINESS.md",
        "checkpoints/CP8-CR135-LAUNCH-MESSAGE.md",
        "checks/CP8-CR135-DELIVERY-READINESS.md",
        "checks/CP6-CR135-RUNNER-ARTIFACT-BUNDLE-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR135-RUNNER-ARTIFACT-BUNDLE-VERIFICATION-DONE.md",
        "context/CP6-CR135.context.json",
        "docs/release/DEPLOY-CHECKLIST-CR135.md",
        "docs/release/FEEDBACK-CR135.md",
        "docs/release/MIGRATION-CR135.md",
        "docs/release/RELEASE-NOTES-CR135.md",
        "docs/release/ROLLBACK-CR135.md",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "release/RELEASE-CONTEXT-CR135.yaml",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR135_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
        "tests/runner/test_runner_artifact_bundle.py",
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/artifact_bundle.py",
        "trading/strategy_runner/cli.py",
        "trading/strategy_runner/result.py",
        "trading/strategy_runner/run_spec.py",
        "trading/strategy_runner/runner.py",
    }
)

CURRENT_CR136_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-136/evidence-index.json",
        "changes/CR-136-RUNNER-BUNDLE-SCHEMA-COMPATIBILITY-VALIDATION-2026-06-23.md",
        "changes/CR-INDEX.json",
        "changes/CR-INDEX.yaml",
        "changes/summaries/CR-136.summary.json",
        "checkpoints/CP8-CR136-DELIVERY-READINESS.md",
        "checkpoints/CP8-CR136-LAUNCH-MESSAGE.md",
        "checks/CP6-CR136-RUNNER-BUNDLE-VALIDATION-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR136-RUNNER-BUNDLE-VALIDATION-VERIFICATION-DONE.md",
        "checks/CP8-CR136-DELIVERY-READINESS.md",
        "context/CP6-CR136.context.json",
        "context/CR136-CLOSURE-TO-CR137-CONTEXT-RESET-HANDOFF-2026-06-23.md",
        "docs/release/DEPLOY-CHECKLIST-CR136.md",
        "docs/release/FEEDBACK-CR136.md",
        "docs/release/MIGRATION-CR136.md",
        "docs/release/RELEASE-NOTES-CR136.md",
        "docs/release/ROLLBACK-CR136.md",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "release/RELEASE-CONTEXT-CR136.yaml",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR136_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
        "tests/runner/test_runner_bundle_validation.py",
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/artifact_bundle.py",
        "trading/strategy_runner/cli.py",
    }
)

CURRENT_CR137_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-137/evidence-index.json",
        "changes/CR-137-OFFLINE-RUNNER-RUN-REGISTRY-2026-06-23.md",
        "changes/CR-INDEX.json",
        "changes/CR-INDEX.yaml",
        "changes/summaries/CR-137.summary.json",
        "checkpoints/CP8-CR137-DELIVERY-READINESS.md",
        "checkpoints/CP8-CR137-LAUNCH-MESSAGE.md",
        "checks/CP6-CR137-RUNNER-RUN-REGISTRY-IMPLEMENTATION-DONE.md",
        "checks/CP7-CR137-RUNNER-RUN-REGISTRY-VERIFICATION-DONE.md",
        "checks/CP8-CR137-DELIVERY-READINESS.md",
        "context/CP6-CR137.context.json",
        "context/CR137-CLOSURE-TO-RUNNER-QMT-USE-CASE-CONTEXT-RESET-HANDOFF-2026-06-24.md",
        "docs/features/strategy-runner-core/DESIGN.md",
        "docs/features/strategy-runner-core/TASKS.md",
        "docs/features/strategy-runner-core/TEST-PLAN.md",
        "docs/release/DEPLOY-CHECKLIST-CR137.md",
        "docs/release/FEEDBACK-CR137.md",
        "docs/release/MIGRATION-CR137.md",
        "docs/release/RELEASE-NOTES-CR137.md",
        "docs/release/ROLLBACK-CR137.md",
        "release/RELEASE-CONTEXT-CR137.yaml",
        "state/CR-LEDGER.ndjson",
        "state/STATE.current.json",
    }
)

CURRENT_CR137_SOURCE_ASSETS = frozenset(
    {
        "scripts/check_process_artifact_hygiene.py",
        "tests/meta_flow/test_process_artifact_hygiene.py",
        "tests/runner/test_runner_run_registry.py",
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/cli.py",
        "trading/strategy_runner/run_registry.py",
        "trading/strategy_runner/run_spec.py",
        "trading/strategy_runner/runner.py",
    }
)

CURRENT_CR138_SOURCE_ASSETS = frozenset(
    {
        "docs/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md",
        "docs/QMT-GATEWAY-INSTALL.md",
        "tests/docs_quality/test_docs_fixtures_authorization_runbook.py",
        "tests/trading/test_qmt_gateway_contracts.py",
        "tests/trading/test_qmt_gateway_contracts.py",
        "tests/trading/test_qmt_gateway_contracts.py",
        "tests/runner/test_control_plane_contracts.py",
        "tests/runner/test_control_plane_contracts.py",
        "tests/runner/test_control_plane_contracts.py",
        "tests/trading/test_qmt_gateway_contracts.py",
        "trading/qmt_gateway_config.py",
        "trading/qmt_gateway_contracts.py",
        "trading/qmt_gateway_gates.py",
        "trading/qmt_gateway_service.py",
        "trading/runner_control_cli.py",
        "trading/runner_control_contracts.py",
        "trading/runner_control_plane.py",
    }
)

CURRENT_CR138_PROCESS_ASSETS = frozenset(
    {
        "DEVELOPMENT-PLAN.yaml",
        "DEVELOPMENT-PLAN-CR138.yaml",
        "STORY-BACKLOG.md",
        "STORY-BACKLOG-CR138.md",
        "STORY-STATUS.md",
        "STORY-STATUS-CR138.md",
        "changes/CR-138-RUNNER-QMT-GATEWAY-OPERATIONAL-USE-CASE-BASELINE-2026-06-24.md",
        "changes/summaries/CR-138.summary.json",
        "checkpoints/CP2-CR138-RUNNER-QMT-OPERATIONAL-USE-CASE-REVIEW.md",
        "checkpoints/CP3-CR138-RUNNER-QMT-HLD-REVIEW.md",
        "checkpoints/CP5-CR138-RUNNER-QMT-OPERATIONAL-CONTROL-LLD-BATCH.md",
        "checkpoints/CP8-CR138-DELIVERY-READINESS.md",
        "checks/CP2-CR138-RUNNER-QMT-OPERATIONAL-USE-CASE-PRECHECK.md",
        "checks/CP2-DISCUSSION-CHECKPOINT.json",
        "checks/CP3-CR138-HLD-CONSISTENCY.md",
        "checks/CP3-DISCUSSION-CHECKPOINT.json",
        "checks/CP4-CR138-STORY-DAG-PARALLEL-SAFETY.md",
        "checks/CP4-CR138-STORY-DAG-PARALLEL-SAFETY.result.json",
        "checks/CP5-CR138-HUMAN-GATE-LAUNCH-MESSAGE.md",
        "checks/CP5-CR138-RUNNER-QMT-OPERATIONAL-CONTROL-LLD-BATCH.result.json",
        "checks/CP5-CR138-S01-shared-contracts-authorization-audit-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S02-runner-plan-preflight-control-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S03-runner-event-signal-rebalance-tracking-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S04-runner-evidence-review-incident-lifecycle-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S05-gateway-lifecycle-health-rest-contract-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S06-gateway-query-calendar-commission-pnl-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S07-gateway-subscription-order-report-recovery-LLD-IMPLEMENTABILITY.md",
        "checks/CP5-CR138-S08-docs-fixtures-cp7-authorization-runbook-LLD-IMPLEMENTABILITY.md",
        "checks/CP6-CR138-RUNNER-QMT-OPERATIONAL-CONTROL-CODING-DONE.md",
        "checks/CP7-CR138-RUNNER-QMT-OPERATIONAL-CONTROL-VERIFICATION-DONE.md",
        "checks/CP8-CR138-DELIVERY-READINESS.md",
        "checks/CR138-FOLLOW-UP-CR-COVERAGE-AUDIT-2026-06-24.md",
        "checks/CR138-PROCESS-ARTIFACT-HYGIENE-GUARDRAIL-2026-06-24.md",
        "checks/CR138-USE-CASE-NORMALIZATION-AUDIT-2026-06-24.md",
        "context/CP2-CR138-RUNNER-QMT-OPERATIONAL-USE-CASE-CONTEXT.yaml",
        "context/CP3-CR138-RUNNER-QMT-HLD-CONTEXT.yaml",
        "context/CP5-CR138-RUNNER-QMT-OPERATIONAL-CONTROL-CONTEXT.yaml",
        "context/CR138-CLOSURE-TO-RUNNER-QMT-NEXT-WORK-CONTEXT-RESET-HANDOFF-2026-06-24.md",
        "discussions/CP2-SCENARIO-DISCUSSION-LOG.md",
        "discussions/CP3-HLD-DISCUSSION-LOG.md",
        "docs/design/ARCHITECTURE-DECISION-RUNNER-QMT-OPERATIONAL-CONTROL-PLANE.md",
        "docs/design/HLD-RUNNER-QMT-OPERATIONAL-CONTROL-PLANE.md",
        "docs/features/qmt-gateway-service-layer/DESIGN.md",
        "docs/features/qmt-gateway-service-layer/TASKS.md",
        "docs/features/qmt-gateway-service-layer/TEST-PLAN.md",
        "docs/features/runner-control-plane/DESIGN.md",
        "docs/features/runner-control-plane/TASKS.md",
        "docs/features/runner-control-plane/TEST-PLAN.md",
        "docs/quality/TEST-MATRIX-CR138.md",
        "docs/quality/VERIFICATION-REPORT-CR138.md",
        "docs/release/DEPLOY-CHECKLIST-CR138.md",
        "docs/release/FEEDBACK-CR138.md",
        "docs/release/MIGRATION-CR138.md",
        "docs/release/RELEASE-NOTES-CR138.md",
        "docs/release/ROLLBACK-CR138.md",
        "evidence/CR138-BATCH.CP7.index.json",
        "release/RELEASE-CONTEXT-CR138.yaml",
        "returns/CR138-BATCH.CP7.return.json",
        "stories/CR138-S01-shared-contracts-authorization-audit-IMPLEMENTATION.md",
        "stories/CR138-S01-shared-contracts-authorization-audit-LLD.md",
        "stories/CR138-S01-shared-contracts-authorization-audit.md",
        "stories/CR138-S02-runner-plan-preflight-control-IMPLEMENTATION.md",
        "stories/CR138-S02-runner-plan-preflight-control-LLD.md",
        "stories/CR138-S02-runner-plan-preflight-control.md",
        "stories/CR138-S03-runner-event-signal-rebalance-tracking-IMPLEMENTATION.md",
        "stories/CR138-S03-runner-event-signal-rebalance-tracking-LLD.md",
        "stories/CR138-S03-runner-event-signal-rebalance-tracking.md",
        "stories/CR138-S04-runner-evidence-review-incident-lifecycle-IMPLEMENTATION.md",
        "stories/CR138-S04-runner-evidence-review-incident-lifecycle-LLD.md",
        "stories/CR138-S04-runner-evidence-review-incident-lifecycle.md",
        "stories/CR138-S05-gateway-lifecycle-health-rest-contract-IMPLEMENTATION.md",
        "stories/CR138-S05-gateway-lifecycle-health-rest-contract-LLD.md",
        "stories/CR138-S05-gateway-lifecycle-health-rest-contract.md",
        "stories/CR138-S06-gateway-query-calendar-commission-pnl-IMPLEMENTATION.md",
        "stories/CR138-S06-gateway-query-calendar-commission-pnl-LLD.md",
        "stories/CR138-S06-gateway-query-calendar-commission-pnl.md",
        "stories/CR138-S07-gateway-subscription-order-report-recovery-IMPLEMENTATION.md",
        "stories/CR138-S07-gateway-subscription-order-recovery-LLD.md",
        "stories/CR138-S07-gateway-subscription-order-report-recovery-LLD.md",
        "stories/CR138-S07-gateway-subscription-order-report-recovery.md",
        "stories/CR138-S08-docs-fixtures-cp7-authorization-runbook-IMPLEMENTATION.md",
        "stories/CR138-S08-docs-fixtures-cp7-authorization-runbook-LLD.md",
        "stories/CR138-S08-docs-fixtures-cp7-authorization-runbook.md",
    }
)

CURRENT_RUNNER_SIMULATION_ENTRY_SOURCE_ASSETS = frozenset(
    {
        "tests/trading/test_linux_client_rest_transport.py",
        "tests/trading/test_runtime_manual_validation.py",
        "tests/runner/test_runner_simulation_activation.py",
        "trading/qmt_client.py",
        "trading/qmt_gateway_contracts.py",
        "trading/qmt_runtime.py",
        "trading/strategy_runner/__init__.py",
        "trading/strategy_runner/simulation_activation.py",
    }
)

CURRENT_RUNNER_SIMULATION_ENTRY_PROCESS_ASSETS = frozenset(
    {
        "checks/RUNNER-MODEL-SIMULATION-LIVE-ENTRY-VERIFICATION-2026-06-24.md",
        "context/RUNNER-MODEL-SIMULATION-LIVE-ENTRY-WORK-PACKAGE-2026-06-24.md",
        "context/RUNNER-SIMULATION-TRADING-MACHINE-SMOKE-HANDOFF-2026-06-24.md",
    }
)

CURRENT_CR089_CLOSURE_PROCESS_ASSETS = frozenset(
    {
        "archive/CR-089/evidence-index.json",
        "changes/CR-089-QMT-INTERFACE-VALIDATION-GATE-2026-06-17.md",
        "changes/summaries/CR-089.summary.json",
        "context/CR089-CLOSURE-TO-CR135-CONTEXT-RESET-HANDOFF-2026-06-23.md",
    }
)

PROCESS_HISTORY_CR_MIN = 113
PROCESS_HISTORY_CR_MAX = 126


@dataclass(frozen=True, slots=True)
class StatusEntry:
    repo: str
    status: str
    path: str

    def to_dict(self) -> dict[str, str]:
        return {"repo": self.repo, "status": self.status, "path": self.path}


def check_process_artifact_hygiene(
    source_root: Path,
    process_root: Path,
) -> dict[str, Any]:
    source_entries = _git_status(source_root, repo="source")
    process_entries = _git_status(process_root, repo="process")
    active_cr_numbers = _load_active_cr_numbers(process_root)
    active_cr_process_paths = _load_active_cr_process_paths(process_root, active_cr_numbers)
    classified: dict[str, list[dict[str, str]]] = {
        "artifact_history_residual": [],
        "current_cr_asset": [],
        "current_cr132_asset": [],
        "current_cr133_asset": [],
        "current_cr134_asset": [],
        "current_cr135_asset": [],
        "current_cr136_asset": [],
        "current_cr137_asset": [],
        "current_runner_simulation_entry_asset": [],
        "current_guardrail_asset": [],
        "current_workflow_shared_asset": [],
        "current_cr089_closure_asset": [],
        "source_human_gate_residual": [],
        "ignored": [],
        "unclassified": [],
    }

    for entry in source_entries + process_entries:
        bucket = classify_entry(
            entry,
            active_cr_numbers=active_cr_numbers,
            active_cr_process_paths=active_cr_process_paths,
        )
        classified[bucket].append(entry.to_dict())

    errors: list[str] = []
    for entry in classified["unclassified"]:
        errors.append(f"unclassified_{entry['repo']}_status:{entry['status']}:{entry['path']}")

    return {
        "schema_version": "cr132-process-artifact-hygiene-check-v1",
        "source_root": source_root.as_posix(),
        "process_root": process_root.as_posix(),
        "passed": not errors,
        "errors": errors,
        "summary": {key: len(value) for key, value in classified.items()},
        "active_cr_numbers": sorted(active_cr_numbers),
        "classified": classified,
        "runner_development_gate": {
            "allowed_to_enter_runner_development": not errors,
            "blocking_bucket": "unclassified",
            "known_non_blocking_buckets": [
                "artifact_history_residual",
                "current_cr_asset",
                "current_runner_simulation_entry_asset",
                "current_guardrail_asset",
                "current_workflow_shared_asset",
                "source_human_gate_residual",
            ],
        },
    }


def classify_entry(
    entry: StatusEntry,
    *,
    active_cr_numbers: frozenset[str] | None = None,
    active_cr_process_paths: frozenset[str] | None = None,
) -> str:
    active_cr_numbers = active_cr_numbers or frozenset()
    active_cr_process_paths = active_cr_process_paths or frozenset()

    if entry.repo == "source":
        if entry.path in CURRENT_WORKFLOW_SHARED_SOURCE_ASSETS:
            return "current_workflow_shared_asset"
        if entry.path in CURRENT_GUARDRAIL_SOURCE_ASSETS:
            return "current_guardrail_asset"
        if entry.path in CURRENT_CR138_SOURCE_ASSETS:
            return "current_cr_asset"
        if entry.path in CURRENT_RUNNER_SIMULATION_ENTRY_SOURCE_ASSETS:
            return "current_runner_simulation_entry_asset"
        if entry.path in CURRENT_CR137_SOURCE_ASSETS:
            return "current_cr137_asset"
        if entry.path in CURRENT_CR136_SOURCE_ASSETS:
            return "current_cr136_asset"
        if entry.path in CURRENT_CR135_SOURCE_ASSETS:
            return "current_cr135_asset"
        if entry.path in CURRENT_CR134_SOURCE_ASSETS:
            return "current_cr134_asset"
        if entry.path in CURRENT_CR133_SOURCE_ASSETS:
            return "current_cr133_asset"
        if entry.path in CURRENT_CR132_SOURCE_ASSETS:
            return "current_cr132_asset"
        if entry.path in KNOWN_SOURCE_RESIDUALS:
            return "source_human_gate_residual"
        return "unclassified"

    if entry.repo == "process":
        if entry.path in CURRENT_WORKFLOW_SHARED_PROCESS_ASSETS:
            return "current_workflow_shared_asset"
        if _is_current_cr_process_asset(entry.path, active_cr_numbers, active_cr_process_paths):
            return "current_cr_asset"
        if entry.path in CURRENT_CR138_PROCESS_ASSETS:
            return "current_cr_asset"
        if entry.path in CURRENT_RUNNER_SIMULATION_ENTRY_PROCESS_ASSETS:
            return "current_runner_simulation_entry_asset"
        if entry.path in CURRENT_CR089_CLOSURE_PROCESS_ASSETS:
            return "current_cr089_closure_asset"
        if entry.path in CURRENT_CR137_PROCESS_ASSETS:
            return "current_cr137_asset"
        if entry.path in CURRENT_CR136_PROCESS_ASSETS:
            return "current_cr136_asset"
        if entry.path in CURRENT_CR135_PROCESS_ASSETS:
            return "current_cr135_asset"
        if entry.path in CURRENT_CR134_PROCESS_ASSETS:
            return "current_cr134_asset"
        if entry.path in CURRENT_CR133_PROCESS_ASSETS:
            return "current_cr133_asset"
        if entry.path in CURRENT_CR132_PROCESS_ASSETS:
            return "current_cr132_asset"
        if _is_process_history_residual(entry.path):
            return "artifact_history_residual"
        return "unclassified"

    return "unclassified"


def _is_process_history_residual(path: str) -> bool:
    if path.startswith("changes/"):
        return _has_history_cr(path)
    if path.startswith("checkpoints/"):
        return _has_history_cr(path)
    if path.startswith("checks/"):
        return _has_history_cr(path)
    if path.startswith("context/"):
        return _has_history_cr(path)
    if path.startswith("release/"):
        return _has_history_cr(path)
    if path.startswith("docs/quality/") or path.startswith("docs/release/"):
        return _has_history_cr(path)
    if path.startswith("stories/"):
        return _has_history_cr(path)
    return False


def _has_history_cr(path: str) -> bool:
    return any(PROCESS_HISTORY_CR_MIN <= int(match) <= PROCESS_HISTORY_CR_MAX for match in re.findall(r"CR-?(\d{3})", path))


def _is_current_cr_process_asset(
    path: str,
    active_cr_numbers: frozenset[str],
    active_cr_process_paths: frozenset[str],
) -> bool:
    if path in active_cr_process_paths:
        return True
    if not active_cr_numbers:
        return False
    return any(re.search(rf"\bCR-?{number}\b", path) for number in active_cr_numbers)


def _load_active_cr_numbers(process_root: Path) -> frozenset[str]:
    active_numbers: set[str] = set()
    index_path = process_root / "changes" / "CR-INDEX.json"
    if index_path.exists():
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        for item in payload.get("items", []):
            status = item.get("status")
            gate_status = item.get("gate_status")
            if status == "active" or gate_status in {"cp2_pending", "cp3_pending", "cp5_pending", "cp8_pending"}:
                number = _extract_cr_number(str(item.get("id", "")))
                if number:
                    active_numbers.add(number)

    state_path = process_root / "state" / "STATE.current.json"
    if state_path.exists():
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        number = _extract_cr_number(str(payload.get("active_change", "")))
        if number:
            active_numbers.add(number)

    return frozenset(active_numbers)


def _load_active_cr_process_paths(process_root: Path, active_cr_numbers: frozenset[str]) -> frozenset[str]:
    if not active_cr_numbers:
        return frozenset()

    paths: set[str] = set()
    index_path = process_root / "changes" / "CR-INDEX.json"
    if not index_path.exists():
        return frozenset()

    payload = json.loads(index_path.read_text(encoding="utf-8"))
    for item in payload.get("items", []):
        number = _extract_cr_number(str(item.get("id", "")))
        if number not in active_cr_numbers:
            continue
        for key in ("full_ref", "summary_ref"):
            normalized = _normalize_process_ref(str(item.get(key, "")))
            if normalized:
                paths.add(normalized)
        for ref in item.get("impact_surface", []):
            normalized = _normalize_process_ref(str(ref))
            if normalized and "." in Path(normalized).name:
                paths.add(normalized)

    return frozenset(paths)


def _extract_cr_number(value: str) -> str | None:
    match = re.search(r"\bCR-?(\d{3})\b", value)
    if not match:
        return None
    return match.group(1)


def _normalize_process_ref(ref: str) -> str:
    path = ref.strip()
    if not path:
        return ""
    process_prefix = "process/"
    if path.startswith(process_prefix):
        path = path[len(process_prefix) :]
    project_prefix = "quant-lab/"
    if path.startswith(project_prefix):
        path = path[len(project_prefix) :]
    return path


def _git_status(repo_root: Path, *, repo: str) -> list[StatusEntry]:
    command = ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"]
    if repo == "process":
        command.extend(["--", "."])
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    entries: list[StatusEntry] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        status = line[:2].strip()
        raw_path = line[3:]
        path = _normalize_status_path(raw_path)
        entries.append(StatusEntry(repo=repo, status=status, path=path))
    return entries


def _normalize_status_path(raw_path: str) -> str:
    if " -> " in raw_path:
        raw_path = raw_path.split(" -> ", 1)[1]
    path = raw_path.strip().strip('"')
    return _normalize_process_ref(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check process artifact hygiene before runner development.")
    parser.add_argument("--source-root", default=".")
    parser.add_argument("--process-root", default="process")
    parser.add_argument("--write-report", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_process_artifact_hygiene(Path(args.source_root), Path(args.process_root))
    if args.write_report:
        Path(args.write_report).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif result["passed"]:
        print("Process artifact hygiene check: OK")
    else:
        print("Process artifact hygiene check: FAIL")
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
