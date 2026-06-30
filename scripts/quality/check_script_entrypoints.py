#!/usr/bin/env python3
"""Check script entrypoint naming and stable-path coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Sequence


UNSTABLE_ROOT_PATTERNS = (
    re.compile(r"^cr\d+", re.IGNORECASE),
    re.compile(r"^run_cr\d+", re.IGNORECASE),
    re.compile(r"^build_cr\d+", re.IGNORECASE),
    re.compile(r"^check_cr\d+", re.IGNORECASE),
    re.compile(r"^collect_cr\d+", re.IGNORECASE),
    re.compile(r"^chapter\d+", re.IGNORECASE),
    re.compile(r"^run_chapter\d+", re.IGNORECASE),
    re.compile(r"^run_stage\d+", re.IGNORECASE),
)

REQUIRED_STABLE_ENTRYPOINTS = {
    "scripts/data_lake/backfill_market_data.py",
    "scripts/data_lake/backfill_missing_market_data.py",
    "scripts/data_lake/check_market_data_readiness.py",
    "scripts/data_lake/cleanup_price_limit_lifecycle.py",
    "scripts/data_lake/publish_market_data_release.py",
    "scripts/data_lake/repair_market_data.py",
    "scripts/data_lake/run_data_lake_readiness_audit.py",
    "scripts/research/run_anomaly_discovery.py",
    "scripts/research/run_anomaly_research.py",
    "scripts/research/run_factor_empirical_research.py",
    "scripts/research/run_factor_model_validation.py",
    "scripts/research/run_factor_practice.py",
    "scripts/research/run_factor_robustness.py",
    "scripts/research/run_multifactor_strategy_candidates.py",
    "scripts/research/run_multifactor_strategy_research.py",
    "scripts/qmt/build_multifactor_runtime_inputs.py",
    "scripts/qmt/build_runtime_preflight_evidence.py",
    "scripts/qmt/collect_qmt_runtime_smoke_summary.py",
    "scripts/qmt/collect_readonly_smoke_evidence.py",
    "scripts/qmt/run_multifactor_simulation_operator.py",
    "scripts/qmt/run_miniqmt_runtime_validation.ps1",
    "scripts/package_exchange.py",
    "scripts/quality/check_change_tracking_consistency.py",
    "scripts/quality/check_qmt_interface_smoke_package.py",
    "scripts/quality/check_redacted_evidence.py",
    "scripts/quality/check_script_entrypoints.py",
    "scripts/quality/check_simulated_evidence.py",
    "scripts/quality/check_strategy_runner_package.py",
}

ALLOWED_ENGINE_COMPATIBILITY_WRAPPERS: set[str] = set()

ARCHIVED_LEGACY_ENGINE_MODULES = {
    "docs/legacy/archive/engine/chapter3_factor_replication.py",
    "docs/legacy/archive/engine/chapter3_real_data_readiness.py",
    "docs/legacy/archive/engine/chapter4_factor_models.py",
    "docs/legacy/archive/engine/chapter5_anomalies.py",
    "docs/legacy/archive/engine/chapter6_factor_robustness.py",
    "docs/legacy/archive/engine/chapter7_factor_practice.py",
}

ARCHIVED_LEGACY_ENTRYPOINTS = {
    "scripts/legacy/qmt/build_qmt_multifactor_runtime_inputs.py",
    "scripts/legacy/qmt/run_qmt_multifactor_simulation_operator.py",
    "scripts/legacy/cr/build_cr104_runtime_preflight_evidence.py",
    "scripts/legacy/cr/chapter3_real_data_readiness.py",
    "scripts/legacy/cr/check_cr089_qmt_interface_smoke_package.py",
    "scripts/legacy/cr/check_cr091_strategy_runner_package.py",
    "scripts/legacy/cr/check_cr092_simulated_evidence.py",
    "scripts/legacy/cr/check_cr099_redacted_evidence.py",
    "scripts/legacy/cr/check_cr_tracking_consistency.py",
    "scripts/legacy/cr/collect_cr089_qmt_runtime_smoke_summary.py",
    "scripts/legacy/cr/collect_cr099_runner_readonly_smoke.py",
    "scripts/legacy/cr/cr012_limited_window_lake_repair.py",
    "scripts/legacy/cr/cr018_price_limit_lifecycle_cleanup.py",
    "scripts/legacy/cr/cr018_real_backfill_missing_data.py",
    "scripts/legacy/cr/cr018_release_catalog_publish.py",
    "scripts/legacy/cr/cr018_run_production_current_truth_research.py",
    "scripts/legacy/cr/cr034_chapter3_backfill.py",
    "scripts/legacy/cr/cr139_gateb_batch0_duplicate_profile.py",
    "scripts/legacy/cr/cr139_gateb_batch0_preflight.py",
    "scripts/legacy/cr/cr139_gateb_batch2_adj_factor_candidate_write.py",
    "scripts/legacy/cr/cr139_gateb_batch2_events_candidate_write.py",
    "scripts/legacy/cr/cr139_gateb_batch2_remaining_split_planning.py",
    "scripts/legacy/cr/cr139_gateb_batch2_split_candidate_write.py",
    "scripts/legacy/cr/cr139_gatec2_active_catalog_manifest_write.py",
    "scripts/legacy/cr/cr139_gatec2_active_catalog_refresh_preview.py",
    "scripts/legacy/cr/cr139_gated_pit_blocker_resolution.py",
    "scripts/legacy/cr/cr139_gated_pointer_advance_execute.py",
    "scripts/legacy/cr/cr139_gated_pointer_advance_preview.py",
    "scripts/legacy/cr/cr139_gatee_full17_copy_migration.py",
    "scripts/legacy/cr/cr139_gatef1_cleanup_authorization_preflight.py",
    "scripts/legacy/cr/cr139_gatef1_cleanup_execute.py",
    "scripts/legacy/cr/cr139_gatef2_legacy_retain_superseded_plan.py",
    "scripts/legacy/cr/cr139_gateg_provider_catalog_applicability.py",
    "scripts/legacy/cr/cr139_gateh_nas_dry_run.py",
    "scripts/legacy/cr/cr139_gateh_nas_sync_execute.py",
    "scripts/legacy/cr/cr139_w2_cp8_supplemental_validation.py",
    "scripts/legacy/cr/cr139_w3a_config_hygiene.py",
    "scripts/legacy/cr/cr139_w3a_reader_extension_assessment.py",
    "scripts/legacy/cr/cr139_w3a_reader_p0_implementation_verification.py",
    "scripts/legacy/cr/cr139_w3b_publish_guard.py",
    "scripts/legacy/cr/cr139_w3b_retention_superseded_register.py",
    "scripts/legacy/cr/cr139_w3c_recurring_validation.py",
    "scripts/legacy/cr/cr139_w3d_provider_catalog_reevaluation.py",
    "scripts/legacy/cr/cr100_package_exchange.py",
    "scripts/legacy/cr/run_chapter3_empirical.py",
    "scripts/legacy/cr/run_chapter4_factor_models.py",
    "scripts/legacy/cr/run_chapter5_anomalies.py",
    "scripts/legacy/cr/run_chapter6_factor_robustness.py",
    "scripts/legacy/cr/run_chapter7_factor_practice.py",
    "scripts/legacy/cr/run_cr104_qmt_miniqmt_validation.ps1",
    "scripts/legacy/cr/run_stage3_mature_multifactor_research.py",
    "scripts/legacy/research/run_anomaly_discovery.py",
    "scripts/legacy/research/run_multifactor_strategy_candidates.py",
}


def check_script_entrypoints(project_root: Path) -> dict[str, object]:
    scripts_root = project_root / "scripts"
    unstable_root: list[str] = []
    for path in sorted(scripts_root.iterdir()):
        if path.is_dir():
            continue
        if not any(pattern.search(path.name) for pattern in UNSTABLE_ROOT_PATTERNS):
            continue
        unstable_root.append(str(path.relative_to(project_root)))

    missing_stable = [
        item for item in sorted(REQUIRED_STABLE_ENTRYPOINTS) if not (project_root / item).is_file()
    ]
    missing_archived = [
        item for item in sorted(ARCHIVED_LEGACY_ENTRYPOINTS) if not (project_root / item).is_file()
    ]
    missing_archived_engine_modules = [
        item for item in sorted(ARCHIVED_LEGACY_ENGINE_MODULES) if not (project_root / item).is_file()
    ]
    unstable_engine_modules = _unstable_engine_modules(project_root)
    status = (
        "PASS"
        if not unstable_root
        and not missing_stable
        and not missing_archived
        and not missing_archived_engine_modules
        and not unstable_engine_modules
        else "FAIL"
    )
    return {
        "schema_version": "script-entrypoint-naming-check-v1",
        "status": status,
        "unstable_root_entrypoints": unstable_root,
        "unstable_new_root_entrypoints": unstable_root,
        "missing_stable_entrypoints": missing_stable,
        "missing_archived_legacy_entrypoints": missing_archived,
        "missing_archived_engine_modules": missing_archived_engine_modules,
        "archived_legacy_entrypoints": sorted(ARCHIVED_LEGACY_ENTRYPOINTS),
        "archived_legacy_engine_modules": sorted(ARCHIVED_LEGACY_ENGINE_MODULES),
        "unstable_engine_modules": unstable_engine_modules,
    }


def _unstable_engine_modules(project_root: Path) -> list[str]:
    engine_root = project_root / "engine"
    if not engine_root.is_dir():
        return []
    unstable: list[str] = []
    for path in sorted(engine_root.glob("*.py")):
        rel = str(path.relative_to(project_root))
        if rel in ALLOWED_ENGINE_COMPATIBILITY_WRAPPERS:
            continue
        if re.match(r"^(chapter\d+|stage\d+|cr\d+)", path.name, flags=re.IGNORECASE):
            unstable.append(rel)
    return unstable


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check script entrypoint naming and stable-path coverage.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = check_script_entrypoints(Path(args.project_root).resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["status"] == "PASS":
        print("script entrypoint naming check passed")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
