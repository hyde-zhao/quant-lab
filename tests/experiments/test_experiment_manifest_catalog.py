from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from engine.multifactor_contracts import FactorRunSpec, PermissionCounters, compute_config_hash
from engine.research_manifest import (
    MF_ADMISSION_NOT_READY,
    MF_CONFIG_HASH_MISSING,
    MF_FORBIDDEN_TRUTH_SOURCE,
    MF_LINEAGE_MISSING,
    MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED,
    MF_REPORT_ARTIFACT_EXISTS,
    MF_REPORT_ARTIFACT_PATH_FORBIDDEN,
    ExperimentManifest,
    ResearchClaim,
    assert_manifest_ready_for_admission,
    build_experiment_manifest,
    build_research_report_catalog_entry,
    compute_experiment_config_hash,
    query_research_report_catalog,
    resolve_research_catalog_paths,
    validate_experiment_manifest,
    write_research_catalog_artifacts,
)


FORBIDDEN_COUNTERS = {
    "external_project_clone": 0,
    "external_project_install": 0,
    "external_project_run": 0,
    "source_migration_or_vendor": 0,
    "dependency_change": 0,
    "provider_fetch": 0,
    "lake_write": 0,
    "catalog_publish": 0,
    "reports_overwrite": 0,
    "qmt_operation": 0,
    "simulation_or_live": 0,
    "account_or_order_operation": 0,
    "credential_read": 0,
}


def _run_spec(**overrides: object) -> FactorRunSpec:
    base = {
        "run_id": "run-cr030-s06-fixture",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "date_range": {"start": "2024-01-01", "end": "2024-01-05"},
        "dataset_release": "research_input_v1_fixture_release",
        "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
        "label_window": {"horizon": 1, "return_kind": "forward_return", "adjustment_policy": "qfq"},
        "cost_config": {"cost_policy": "research_cost_v1", "commission_bps": 3, "slippage_bps": 5},
        "seed": 42,
        "code_version": "cr030-s06-fixture",
        "config_hash": "",
        "output_root": "reports/cr030_s06_fixture",
        "permission_counters": PermissionCounters(),
        "failure_policy": "fail_closed",
        "strategy_id": "strategy-cr030-s06-fixture",
        "experiment_group": "cr030-s06",
        "combination_config": {"weighting_policy": "rule_weighted", "weights": {"momentum_20d": 1.0}},
    }
    base.update(overrides)
    if not base["config_hash"]:
        base["config_hash"] = compute_config_hash({key: value for key, value in base.items() if key != "config_hash"})
    return FactorRunSpec(**base)


def _report_ref(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "report_id": "report-cr030-s04-fixture",
        "run_id": "run-cr030-s06-fixture",
        "factor_id": "momentum_20d",
        "factor_version": "v1",
        "artifact_paths": {
            "json": "reports/factor_evaluation/v1/report-cr030-s04-fixture/report.json",
            "csv": "reports/factor_evaluation/v1/report-cr030-s04-fixture/metrics.csv",
            "markdown": "reports/factor_evaluation/v1/report-cr030-s04-fixture/report.md",
        },
        "allowed_claims": [
            {
                "claim": "single_factor_research_evidence",
                "status": "allowed",
                "reason": "仅作为项目自有多因子研究输入证据。",
                "evidence_ref": "fixture://cr030-s04/full-input",
                "code": "MF_REPORT_RESEARCH_EVIDENCE_ALLOWED",
                "limitation": "需与组合、manifest/catalog 和 Stage6 gate 证据共同使用。",
            }
        ],
        "blocked_claims": [
            {
                "claim": "qmt_ready",
                "status": "blocked",
                "reason": "CR030-S04/S06 不授权 QMT-ready 声明。",
                "evidence_ref": "fixture://cr030-s04/full-input",
                "code": "MF_REPORT_CLAIM_UNSUPPORTED",
                "limitation": "真实 QMT / simulation / live 需后续独立 CR 与 per-run authorization。",
            },
            {
                "claim": "simulation_ready",
                "status": "blocked",
                "reason": "CR030-S04/S06 不授权 simulation-ready 声明。",
                "evidence_ref": "fixture://cr030-s04/full-input",
                "code": "MF_REPORT_CLAIM_UNSUPPORTED",
                "limitation": "真实模拟盘运行需后续独立 CR。",
            },
        ],
        "limitations": ["不构成 production truth、QMT-ready、simulation-ready 或 live-ready。"],
        "evidence_refs": ["fixture://cr030-s04/full-input"],
    }
    base.update(overrides)
    return base


def _metadata(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "report_id": "report-cr030-s04-fixture",
        "evidence_refs": ["process/HLD.md#35.6", "process/ARCHITECTURE-DECISION.md#ADR-084"],
        "limitations": ["catalog 是研究报告索引，不是 publish current pointer。"],
        "permission_counters": FORBIDDEN_COUNTERS,
    }
    base.update(overrides)
    return base


def test_ts_s06_01_complete_manifest_and_catalog_are_admission_ready() -> None:
    run_spec = _run_spec()
    manifest = build_experiment_manifest(run_spec, [_report_ref()], metadata=_metadata())
    manifest_result = validate_experiment_manifest(manifest)
    entry = build_research_report_catalog_entry(manifest, manifest.report_paths, created_at="2026-06-03T00:00:00Z")
    admission_result = assert_manifest_ready_for_admission(manifest, entry)

    assert isinstance(manifest, ExperimentManifest)
    assert manifest_result.passed
    assert admission_result.passed
    assert entry.admission_candidate is True
    assert entry.status == "pass"
    assert set(manifest.to_dict()) >= {
        "run_id",
        "strategy_id",
        "config_hash",
        "dataset_release",
        "factor_versions",
        "label_window",
        "benchmark",
        "cost_config",
        "evaluation_window",
        "seed",
        "code_version",
        "report_paths",
        "allowed_claims",
        "blocked_claims",
        "limitations",
        "evidence_refs",
    }
    assert manifest.config_hash == run_spec.config_hash
    assert {claim.claim for claim in manifest.allowed_claims} == {"single_factor_research_evidence"}
    assert {"qmt_ready", "simulation_ready"} <= {claim.claim for claim in manifest.blocked_claims}
    json.dumps(manifest.to_dict(), sort_keys=True)
    json.dumps(entry.to_dict(), sort_keys=True)


def test_ts_s06_02_config_hash_is_deterministic_and_missing_p0_blocks_admission() -> None:
    payload_a = {
        "factor_versions": [{"factor_id": "momentum_20d", "version": "v1"}],
        "dataset_release": "research_input_v1_fixture_release",
        "label_window": {"horizon": 1, "return_kind": "forward_return"},
        "cost_config": {"slippage_bps": 5, "commission_bps": 3},
        "combination_config": {"weights": {"momentum_20d": 1.0}},
        "code_version": "cr030-s06-fixture",
    }
    payload_b = {
        "code_version": "cr030-s06-fixture",
        "combination_config": {"weights": {"momentum_20d": 1.0}},
        "cost_config": {"commission_bps": 3, "slippage_bps": 5},
        "label_window": {"return_kind": "forward_return", "horizon": 1},
        "dataset_release": "research_input_v1_fixture_release",
        "factor_versions": [{"version": "v1", "factor_id": "momentum_20d"}],
    }
    assert compute_experiment_config_hash(payload_a) == compute_experiment_config_hash(payload_b)
    assert compute_experiment_config_hash(payload_a) != compute_experiment_config_hash({**payload_a, "code_version": "changed"})

    missing_hash_run_spec = _run_spec(config_hash="").to_dict()
    missing_hash_run_spec["config_hash"] = ""
    manifest = build_experiment_manifest(missing_hash_run_spec, [_report_ref()], metadata=_metadata())
    entry = build_research_report_catalog_entry(manifest)
    admission = assert_manifest_ready_for_admission(manifest, entry)

    assert not validate_experiment_manifest(manifest).passed
    assert entry.admission_candidate is False
    assert not admission.passed
    assert MF_CONFIG_HASH_MISSING in {reason.code for reason in admission.blocked_reasons}
    assert MF_ADMISSION_NOT_READY in {reason.code for reason in admission.blocked_reasons}

    missing_release_run_spec = _run_spec().to_dict()
    missing_release_run_spec["dataset_release"] = ""
    missing_release_manifest = build_experiment_manifest(missing_release_run_spec, [_report_ref()], metadata=_metadata())
    missing_release_result = assert_manifest_ready_for_admission(
        missing_release_manifest,
        build_research_report_catalog_entry(missing_release_manifest),
    )
    assert MF_LINEAGE_MISSING in {reason.code for reason in missing_release_result.blocked_reasons}


def test_ts_s06_03_catalog_query_returns_exact_report_refs_and_claims() -> None:
    manifest = build_experiment_manifest(_run_spec(), [_report_ref()], metadata=_metadata())
    entry = build_research_report_catalog_entry(manifest, created_at="2026-06-03T00:00:00Z")
    catalog = [entry]

    assert query_research_report_catalog(catalog, {"run_id": "run-cr030-s06-fixture"}) == (entry,)
    assert query_research_report_catalog(catalog, {"report_id": "report-cr030-s04-fixture"}) == (entry,)
    assert query_research_report_catalog(catalog, {"factor_id": "momentum_20d"}) == (entry,)
    assert query_research_report_catalog(catalog, {"strategy_id": "strategy-cr030-s06-fixture"}) == (entry,)
    assert query_research_report_catalog(catalog, {"factor_id": "unknown"}) == ()
    assert entry.artifact_paths == manifest.report_paths
    assert {claim.claim for claim in entry.allowed_claims} == {"single_factor_research_evidence"}


def test_ts_s06_04_catalog_artifact_writer_is_versioned_and_never_overwrites_old_reports(tmp_path: Path) -> None:
    old_report = tmp_path / "reports" / "experiment_17_21" / "factor_strategy_report.md"
    old_report.parent.mkdir(parents=True)
    old_report.write_text("old report must stay unchanged", encoding="utf-8")

    manifest = build_experiment_manifest(_run_spec(), [_report_ref()], metadata=_metadata())
    entry = build_research_report_catalog_entry(manifest, created_at="2026-06-03T00:00:00Z")
    paths = resolve_research_catalog_paths(entry.catalog_entry_id, tmp_path)
    write_result = write_research_catalog_artifacts(entry, paths)

    assert write_result.status == "pass"
    assert "/reports/research_catalog/v1/" in paths.json_path.as_posix()
    assert paths.json_path.exists()
    assert paths.csv_path.exists()
    assert paths.markdown_path.exists()
    assert old_report.read_text(encoding="utf-8") == "old report must stay unchanged"

    second_write = write_research_catalog_artifacts(entry, paths)
    assert second_write.status == "blocked"
    assert MF_REPORT_ARTIFACT_EXISTS in {reason.code for reason in second_write.blocked_reasons}

    with pytest.raises(ValueError, match=MF_REPORT_ARTIFACT_PATH_FORBIDDEN):
        resolve_research_catalog_paths(entry.catalog_entry_id, tmp_path / "reports" / "experiment_17_21")


def test_ts_s06_05_mlflow_pickle_or_production_truth_claims_fail_closed() -> None:
    manifest = build_experiment_manifest(
        _run_spec(),
        [
            _report_ref(
                artifact_paths={
                    "json": "mlflow://run/report.json",
                    "pickle": "reports/factor_evaluation/v1/report-cr030-s04-fixture/report.pkl",
                }
            )
        ],
        metadata=_metadata(),
    )
    result = validate_experiment_manifest(manifest)
    assert not result.passed
    assert MF_FORBIDDEN_TRUTH_SOURCE in {reason.code for reason in result.blocked_reasons}

    bad_claim = ResearchClaim(
        claim="qmt-ready production truth",
        status="allowed",
        reason="bad fixture",
        evidence_ref="fixture://bad-claim",
    )
    bad_manifest = replace(manifest, report_paths=("reports/factor_evaluation/v1/report/report.json",), allowed_claims=(bad_claim,))
    bad_result = assert_manifest_ready_for_admission(bad_manifest, build_research_report_catalog_entry(bad_manifest))
    assert not bad_result.passed
    assert MF_ADMISSION_NOT_READY in {reason.code for reason in bad_result.blocked_reasons}


def test_ts_s06_06_forbidden_operation_counters_block_nonzero_publish_or_lake() -> None:
    manifest = build_experiment_manifest(_run_spec(), [_report_ref()], metadata=_metadata())
    assert all(value == 0 for value in manifest.permission_counters.values())
    assert validate_experiment_manifest(manifest).passed

    counters = dict(FORBIDDEN_COUNTERS)
    counters["catalog_publish"] = 1
    blocked_manifest = build_experiment_manifest(
        _run_spec(permission_counters=counters),
        [_report_ref()],
        metadata=_metadata(permission_counters=counters),
    )
    result = validate_experiment_manifest(blocked_manifest)
    assert not result.passed
    assert MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED in {reason.code for reason in result.blocked_reasons}
