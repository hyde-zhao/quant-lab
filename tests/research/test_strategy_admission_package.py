from __future__ import annotations

import json
from pathlib import Path

from engine.strategy_admission_package import (
    MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED,
    MF_ADMISSION_CREDENTIAL_READ_FORBIDDEN,
    MF_ADMISSION_MANIFEST_NOT_READY,
    MF_ADMISSION_ORDER_DRAFT_ONLY,
    MF_ADMISSION_QMT_CR_NOT_AUTHORIZED,
    MF_ADMISSION_REAL_OPERATION_NOT_AUTHORIZED,
    MF_ADMISSION_REQUIRED_FIELD_MISSING,
    MF_ADMISSION_RUNTIME_NOT_AUTHORIZED,
    MF_ADMISSION_STAGE6_P0_GATE_FAILED,
    AdmissionStatus,
    NotAuthorizedCounters,
    assert_no_real_operation,
    attach_cross_strategy_reliability_to_admission_package,
    build_strategy_admission_package,
    determine_admission_status,
    map_cross_strategy_reliability_status_to_admission_status,
    make_order_intent_draft_ref,
    to_jsonable_admission_package,
    validate_admission_inputs,
    zero_not_authorized_counters,
)


def _portfolio_plan(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "multifactor_portfolio_plan_v1",
        "plan_id": "plan-cr030-s07-fixture",
        "combiner_id": "combo-cr030-s07-fixture",
        "run_id": "run-cr030-s07-fixture",
        "strategy_id": "strategy-cr030-s07-fixture",
        "status": "pass",
        "factor_weights": [{"factor_id": "momentum_20d", "weight": 1.0}],
        "target_weights": {"momentum_20d": 1.0},
        "not_broker_order": True,
        "evidence_refs": ["fixture://portfolio-plan"],
        "permission_counters": {
            "qmt_operation": 0,
            "simulation_or_live": 0,
            "account_or_order_operation": 0,
            "credential_read": 0,
        },
    }
    base.update(overrides)
    return base


def _manifest(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "experiment_manifest_v1",
        "run_id": "run-cr030-s07-fixture",
        "strategy_id": "strategy-cr030-s07-fixture",
        "config_hash": "hash-cr030-s07-fixture",
        "dataset_release": "research_input_v1_fixture_release",
        "factor_versions": [{"factor_id": "momentum_20d", "version": "v1"}],
        "label_window": {"horizon": 1, "return_kind": "forward_return", "adjustment_policy": "qfq"},
        "benchmark": {"benchmark_id": "hs300"},
        "cost_config": {"commission_bps": 3, "slippage_bps": 5},
        "evaluation_window": {"start": "2024-01-01", "end": "2024-01-31"},
        "seed": 42,
        "code_version": "cr030-s07-fixture",
        "report_paths": ["reports/factor_evaluation/v1/report-cr030-s07/report.json"],
        "allowed_claims": [
            {
                "claim": "multifactor_research_evidence",
                "status": "allowed",
                "reason": "fixture",
            }
        ],
        "blocked_claims": [
            {
                "claim": "qmt_ready",
                "status": "blocked",
                "reason": "not authorized",
            },
            {
                "claim": "simulation_ready",
                "status": "blocked",
                "reason": "not authorized",
            },
        ],
        "limitations": ["研究证据不代表真实运行授权。"],
        "evidence_refs": ["fixture://manifest"],
        "permission_counters": {
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
        },
    }
    base.update(overrides)
    return base


def _catalog(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "research_report_catalog_v1",
        "catalog_entry_id": "run-cr030-s07-fixture-report-cr030-s07",
        "report_id": "report-cr030-s07",
        "run_id": "run-cr030-s07-fixture",
        "strategy_id": "strategy-cr030-s07-fixture",
        "factor_ids": ["momentum_20d"],
        "artifact_paths": ["reports/factor_evaluation/v1/report-cr030-s07/report.json"],
        "created_at": "2026-06-03T00:00:00Z",
        "source_lineage": {
            "manifest_schema_version": "experiment_manifest_v1",
            "config_hash": "hash-cr030-s07-fixture",
            "dataset_release": "research_input_v1_fixture_release",
        },
        "status": "pass",
        "admission_candidate": True,
        "allowed_claims": [
            {
                "claim": "multifactor_research_evidence",
                "status": "allowed",
                "reason": "fixture",
            }
        ],
        "blocked_claims": [
            {
                "claim": "live_ready",
                "status": "blocked",
                "reason": "not authorized",
            }
        ],
        "limitations": ["catalog 是研究索引，不是 current pointer。"],
        "evidence_refs": ["fixture://catalog"],
    }
    base.update(overrides)
    return base


def _stage6_gate(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "admission_status": "pass",
        "stage_gate_ref": "fixture://stage6-pass",
        "gate_matrix": [
            {"gate_id": "data_quality", "status": "pass", "evidence_ref": "fixture://stage6/data_quality"},
            {"gate_id": "factor_quality", "status": "pass", "evidence_ref": "fixture://stage6/factor_quality"},
        ],
        "blocked_claims": [],
        "missing_evidence": [],
        "evidence_refs": ["fixture://stage6"],
    }
    base.update(overrides)
    return base


def _draft_ref(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "order_intent_draft_v1",
        "draft_id": "draft-cr030-s07-fixture",
        "path_or_ref": "fixture://order-intent-draft/draft-cr030-s07",
        "limitations": ["draft only", "not authorization", "later gated"],
        "operation_counters": zero_not_authorized_counters().to_dict(),
    }
    base.update(overrides)
    return base


def _reason_codes(items: object) -> set[str]:
    return {getattr(item, "code", "") for item in items}


def test_ts_s07_01_complete_research_evidence_builds_pre_sim_preparation_package_but_blocks_without_qmt_cr() -> None:
    package = build_strategy_admission_package(
        _portfolio_plan(),
        _manifest(),
        _catalog(),
        _stage6_gate(),
        _draft_ref(),
    )
    payload = package.to_dict()

    assert package.admission_status is AdmissionStatus.BLOCKED
    assert MF_ADMISSION_QMT_CR_NOT_AUTHORIZED in _reason_codes(package.blocked_reasons)
    assert package.pre_sim_strategy_preparation["status"] == "evidence_package_complete_for_follow_up_review"
    assert package.pre_sim_strategy_preparation["not_authorization"] is True
    assert package.pre_sim_strategy_preparation["requires_follow_up"] == ("CR-020", "CR-021", "CR-022", "CR-023", "CR-024")
    assert {claim.claim for claim in package.allowed_claims} >= {
        "multifactor_research_and_local_backtest_evidence",
        "pre_sim_strategy_preparation_package",
    }
    assert {"qmt_ready", "simulation_ready", "live_ready"} <= {claim.claim for claim in package.blocked_claims}
    assert package.not_authorized_counters.to_dict() == zero_not_authorized_counters().to_dict()
    assert payload["not_qmt_authorization"] is True
    assert payload["not_simulation_authorization"] is True
    assert payload["not_live_authorization"] is True
    json.dumps(to_jsonable_admission_package(package), sort_keys=True)


def test_ts_s07_02_status_enum_and_research_status_mapping_cover_pass_warn_fail_blocked() -> None:
    assert {status.value for status in AdmissionStatus} == {"pass", "warn", "fail", "blocked"}
    assert determine_admission_status((), "pass") is AdmissionStatus.PASS
    assert determine_admission_status((), "warn") is AdmissionStatus.WARN
    assert determine_admission_status((), "research_limited") is AdmissionStatus.WARN
    assert determine_admission_status((), "fail") is AdmissionStatus.FAIL

    blocked = validate_admission_inputs(
        _portfolio_plan(status="blocked"),
        _manifest(),
        _catalog(),
        _stage6_gate(),
        _draft_ref(),
    )
    assert determine_admission_status(blocked, "pass") is AdmissionStatus.BLOCKED


def test_ts_s07_03_stage6_p0_gate_fail_blocks_admission() -> None:
    stage6_gate = _stage6_gate(
        admission_status="blocked",
        blocked_claims=[
            {
                "claim_id": "stage6_factor_quality",
                "reason_code": "p0_gate_failed",
                "evidence_ref": "fixture://stage6/fail",
            }
        ],
        gate_matrix=[
            {"gate_id": "factor_quality", "status": "blocked", "evidence_ref": "fixture://stage6/fail"}
        ],
    )

    package = build_strategy_admission_package(
        _portfolio_plan(),
        _manifest(),
        _catalog(),
        stage6_gate,
        _draft_ref(),
    )

    assert package.admission_status is AdmissionStatus.BLOCKED
    assert package.stage6_gate_summary["passed"] is False
    assert MF_ADMISSION_STAGE6_P0_GATE_FAILED in _reason_codes(package.blocked_reasons)
    assert "blocked_missing_required_evidence" == package.pre_sim_strategy_preparation["status"]


def test_ts_s07_04_missing_manifest_or_catalog_p0_fields_never_enters_unblocked_admission() -> None:
    missing_manifest = _manifest(config_hash="", dataset_release="")
    missing_catalog = _catalog(admission_candidate=False, artifact_paths=[])
    reasons = validate_admission_inputs(
        _portfolio_plan(),
        missing_manifest,
        missing_catalog,
        _stage6_gate(),
        _draft_ref(),
    )
    package = build_strategy_admission_package(
        _portfolio_plan(),
        missing_manifest,
        missing_catalog,
        _stage6_gate(),
        _draft_ref(),
    )

    assert package.admission_status is AdmissionStatus.BLOCKED
    assert {MF_ADMISSION_MANIFEST_NOT_READY, MF_ADMISSION_REQUIRED_FIELD_MISSING} <= _reason_codes(reasons)
    assert MF_ADMISSION_MANIFEST_NOT_READY in _reason_codes(package.blocked_reasons)
    assert package.pre_sim_strategy_preparation["status"] == "blocked_missing_required_evidence"


def test_ts_s07_05_order_intent_draft_ref_is_draft_only_and_never_broker_payload() -> None:
    draft_ref = make_order_intent_draft_ref(
        {
            "schema_version": "order_intent_draft_v1",
            "draft_id": "draft-only-fixture",
            "path_or_ref": "fixture://draft-only-fixture",
            "limitations": ["later gated", "not authorization"],
            "symbol": "SH600000",
            "side": "buy",
            "target_qty": 100,
        }
    )
    package = build_strategy_admission_package(
        _portfolio_plan(),
        _manifest(),
        _catalog(),
        _stage6_gate(),
        draft_ref.to_dict(),
    )
    ref_payload = package.order_intent_draft_ref.to_dict()

    assert ref_payload["schema_version"] == "order_intent_draft_v1"
    assert ref_payload["draft_only"] is True
    assert ref_payload["not_authorization"] is True
    assert ref_payload["operation_counters"] == zero_not_authorized_counters().to_dict()
    assert "symbol" not in ref_payload
    assert "side" not in ref_payload
    assert "target_qty" not in ref_payload

    bad_reasons = validate_admission_inputs(
        _portfolio_plan(),
        _manifest(),
        _catalog(),
        _stage6_gate(),
        _draft_ref(schema_version="broker_order_v1"),
    )
    assert MF_ADMISSION_ORDER_DRAFT_ONLY in _reason_codes(bad_reasons)


def test_ts_s07_06_forbidden_counters_and_runtime_requests_are_structured_blocked_reasons() -> None:
    nonzero = NotAuthorizedCounters(qmt_api_call=1, real_order=1, credential_read=1)
    reasons = assert_no_real_operation(nonzero)
    package = build_strategy_admission_package(
        _portfolio_plan(),
        _manifest(),
        _catalog(),
        _stage6_gate(),
        _draft_ref(),
        counters=nonzero,
        requested_runtime_claims=("simulation", "live_ready"),
    )

    assert {MF_ADMISSION_REAL_OPERATION_NOT_AUTHORIZED, MF_ADMISSION_CREDENTIAL_READ_FORBIDDEN} <= _reason_codes(reasons)
    assert MF_ADMISSION_RUNTIME_NOT_AUTHORIZED in _reason_codes(package.blocked_reasons)
    assert package.not_authorized_counters.qmt_api_call == 1
    assert package.not_authorized_counters.real_order == 1
    assert package.not_authorized_counters.credential_read == 1
    assert package.admission_status is AdmissionStatus.BLOCKED


def test_ts_s07_07_forbidden_imports_and_misleading_enablement_strings_are_absent() -> None:
    source = Path("engine/strategy_admission_package.py").read_text(encoding="utf-8")
    lowered = source.lower()

    assert "import xtquant" not in lowered
    assert "from xtquant" not in lowered
    assert "subprocess" not in lowered
    assert "os.system" not in lowered
    assert "popen" not in lowered
    assert "requests." not in lowered
    assert "urllib" not in lowered
    assert "git clone" not in lowered
    assert "pip install" not in lowered
    assert "uv add" not in lowered
    assert "uv sync" not in lowered
    assert ".env" not in lowered
    assert "qmt-ready" not in lowered
    assert "simulation-ready" not in lowered
    assert "live-ready" not in lowered


def _pass_package_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "strategy_admission_package_v1",
        "package_id": "strategy-admission:cr154-fixture",
        "strategy_id": "strategy-cr154-fixture",
        "run_id": "run-cr154-fixture",
        "admission_status": "pass",
        "evidence_refs": ("fixture://existing",),
        "blocked_reasons": (),
        "unlock_conditions": (),
        "blocked_claims": (),
        "limitations": ("existing_limitation",),
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
    }
    payload.update(overrides)
    return payload


def test_cr154_cross_strategy_reliability_status_mapping_and_pass_attachment_preserves_runtime_boundaries() -> None:
    assert map_cross_strategy_reliability_status_to_admission_status("PASS") is AdmissionStatus.PASS
    assert map_cross_strategy_reliability_status_to_admission_status("FAIL") is AdmissionStatus.FAIL
    assert map_cross_strategy_reliability_status_to_admission_status("NEEDS_REVIEW") is AdmissionStatus.WARN
    assert map_cross_strategy_reliability_status_to_admission_status("BLOCKED") is AdmissionStatus.BLOCKED
    assert map_cross_strategy_reliability_status_to_admission_status("unknown") is AdmissionStatus.BLOCKED

    payload = attach_cross_strategy_reliability_to_admission_package(
        _pass_package_payload(
            blocked_claims=(
                {
                    "claim": "existing_runtime_claim",
                    "status": "blocked",
                    "code": "EXISTING",
                    "reason": "existing",
                },
            )
        ),
        {
            "status": "PASS",
            "gate_status": "PASS",
            "gate_ref": "fixture://cr154/cross-strategy",
            "evidence_refs": ("fixture://cr154/gate1", "fixture://cr154/gate6"),
            "limitations": ("local_static_fixture_only",),
        },
    )

    assert payload["admission_status"] == AdmissionStatus.PASS.value
    assert payload["cross_strategy_reliability_status"] == "PASS"
    assert payload["cross_strategy_reliability_ref"] == "fixture://cr154/cross-strategy"
    assert {"fixture://existing", "fixture://cr154/cross-strategy", "fixture://cr154/gate1", "fixture://cr154/gate6"} <= set(
        payload["evidence_refs"]
    )
    assert payload["not_qmt_authorization"] is True
    assert payload["not_simulation_authorization"] is True
    assert payload["not_live_authorization"] is True
    assert payload["not_broker_order"] is True
    assert "cross_strategy_reliability_pass_not_runtime_ready" in payload["limitations"]
    assert "no_trading_authorization" in payload["limitations"]
    assert {"existing_runtime_claim", "cross_strategy_reliability_pass_not_runtime_ready"} <= {
        claim["claim"] for claim in payload["blocked_claims"]
    }


def test_cr154_cross_strategy_reliability_blocked_attachment_degrades_and_preserves_adjacent_gate_fields() -> None:
    package = _pass_package_payload(
        statistical_gate_summary={"status": "PASS"},
        ml_gate_summary={"gate_status": "PASS"},
        event_gate_summary={"gate_status": "PASS"},
        gate_status="PASS",
        gate_ref="fixture://legacy/generic",
    )

    payload = attach_cross_strategy_reliability_to_admission_package(
        package,
        {
            "gate_status": "BLOCKED",
            "gate_ref": "fixture://cr154/blocked",
            "blocked_reasons": (
                {
                    "code": "CR154_BLOCKED",
                    "source": "cross_strategy_reliability_gate",
                    "field": "gate_1_statistical",
                    "message": "blocked fixture",
                },
            ),
            "blocked_claims": (
                {
                    "claim": "production_reliability",
                    "status": "blocked",
                    "code": "CR154_BLOCKED",
                    "reason": "blocked fixture",
                },
            ),
        },
    )

    assert payload["admission_status"] == AdmissionStatus.BLOCKED.value
    assert payload["statistical_gate_summary"] == {"status": "PASS"}
    assert payload["ml_gate_summary"] == {"gate_status": "PASS"}
    assert payload["event_gate_summary"] == {"gate_status": "PASS"}
    assert payload["gate_status"] == "PASS"
    assert payload["gate_ref"] == "fixture://legacy/generic"
    assert payload["cross_strategy_reliability_status"] == "BLOCKED"
    assert MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED in {
        reason["code"] for reason in payload["blocked_reasons"]
    }
    assert "provide_passing_cross_strategy_reliability_gate_or_route_review" in payload["unlock_conditions"]
