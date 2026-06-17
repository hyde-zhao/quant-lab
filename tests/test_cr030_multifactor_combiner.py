from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.multifactor_combiner import (
    MF_BROKER_ORDER_FORBIDDEN,
    MF_COMBINER_BENCHMARK_MISSING,
    MF_COMBINER_CAPACITY_MISSING,
    MF_COMBINER_COST_MISSING,
    MF_COMBINER_EXPOSURE_MISSING,
    MF_COMBINER_FORBIDDEN_OPERATION_NONZERO,
    MF_COMBINER_REPORT_BLOCKED,
    MF_OPTIMIZER_DEFERRED,
    MultiFactorCombiner,
    apply_portfolio_constraints,
    assert_no_broker_order,
    build_multifactor_portfolio_plan,
    compute_rule_weights,
    detect_optimizer_deferred_request,
    to_portfolio_plan_draft,
    validate_combiner_inputs,
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


def _allowed_claim() -> dict[str, str]:
    return {
        "claim": "single_factor_research_evidence",
        "status": "allowed",
        "reason": "fixture evidence for CR030-S05",
    }


def _report(
    factor_id: str,
    report_id: str,
    *,
    status: str = "pass",
    icir: float = 1.0,
    rank_ic: float = 0.1,
    coverage: float = 1.0,
    turnover: float = 0.2,
    allowed_claims: list[dict[str, str]] | None = None,
    permission_counters: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "report_id": report_id,
        "run_id": f"run-{report_id}",
        "factor_id": factor_id,
        "factor_version": "v1",
        "dataset_release": "research_input_v1_fixture_release",
        "status": status,
        "ICIR": {"status": "pass", "value": icir},
        "RankIC": {"status": "pass", "mean": rank_ic},
        "coverage": {"status": "pass", "matched_ratio": coverage},
        "turnover": {"status": "pass", "value": turnover},
        "cost_sensitivity": {"status": "pass"},
        "exposure_summary": {"status": "pass"},
        "allowed_claims": allowed_claims if allowed_claims is not None else [_allowed_claim()],
        "blocked_claims": [
            {"claim": "qmt_ready", "status": "blocked", "code": "not_authorized"},
            {"claim": "simulation_ready", "status": "blocked", "code": "not_authorized"},
            {"claim": "live_ready", "status": "blocked", "code": "not_authorized"},
        ],
        "evidence_refs": [f"fixture://{report_id}"],
        "permission_counters": permission_counters or dict(FORBIDDEN_COUNTERS),
    }


def _config(**overrides: object) -> MultiFactorCombiner:
    base = {
        "combiner_id": "combo-cr030-s05-fixture",
        "factor_inputs": (),
        "normalization": {"method": "zscore", "scope": "cross_section"},
        "winsorization": {"method": "quantile", "limits": [0.01, 0.99]},
        "neutralization": {"method": "disabled", "reason": "P0 fixture no exposure neutralization"},
        "orthogonalization": {"method": "disabled", "reason": "P0 fixture no orthogonalization"},
        "weighting_policy": {
            "policy": "rule_weight",
            "weights": {"momentum_20d": 0.7, "reversal_5d": 0.3},
        },
        "missing_policy": {"missing_report": "exclude_with_reason", "critical_constraint": "fail_closed"},
        "constraints": {
            "max_factor_weight": 0.8,
            "target_count": 20,
            "benchmark_deviation_cap": 0.1,
            "capacity": {"max_daily_participation": 0.05},
            "exposure": {"style_beta": "observed"},
            "rebalance_dates": ["2024-01-31"],
        },
        "rebalance_frequency": "monthly",
        "turnover_cap": 0.35,
        "cost_config": {"commission_bps": 3, "slippage_bps": 5},
        "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
        "freeze_policy": {"version": "freeze-cr030-s05-v1", "change_policy": "cp5_or_cr_required"},
        "capacity": {"max_daily_participation": 0.05},
        "optimizer_policy": {"enabled": False},
        "permission_counters": dict(FORBIDDEN_COUNTERS),
    }
    base.update(overrides)
    return MultiFactorCombiner(**base)


def _reason_codes(items: object) -> set[str]:
    return {getattr(item, "code", "") for item in items}


def test_ts_s05_01_rule_weight_combiner_builds_traceable_portfolio_plan() -> None:
    reports = [
        _report("momentum_20d", "report-momentum"),
        _report("reversal_5d", "report-reversal"),
    ]
    plan = build_multifactor_portfolio_plan(reports, _config())

    assert plan.status == "pass"
    assert plan.schema_version == "multifactor_portfolio_plan_v1"
    assert plan.target_weights == pytest.approx({"momentum_20d": 0.7, "reversal_5d": 0.3})
    assert plan.target_count == 20
    assert plan.benchmark_deviation["status"] == "pass"
    assert plan.cost_summary["status"] == "pass"
    assert plan.capacity_summary["status"] == "pass"
    assert {weight.factor_id for weight in plan.factor_weights} == {"momentum_20d", "reversal_5d"}
    assert plan.weight_sources["momentum_20d"]["policy"] == "rule_weight"
    assert {claim.claim for claim in plan.allowed_claims} == {"multifactor_research_plan"}
    assert {"qmt_ready", "simulation_ready", "live_ready"} <= {claim.claim for claim in plan.blocked_claims}
    assert plan.production_valid_claim_count == 0
    assert plan.not_broker_order is True
    assert assert_no_broker_order(plan).passed
    assert plan.draft_handoff["schema_version"] == "multifactor_portfolio_plan_draft_v1"
    assert plan.draft_handoff["not_authorization"] is True
    json.dumps(plan.to_dict(), sort_keys=True)


def test_ts_s05_02_linear_score_and_constraints_are_lightweight_and_bounded() -> None:
    reports = [
        _report("strong_factor", "report-strong", icir=2.0, rank_ic=0.2, coverage=1.0, turnover=0.05),
        _report("weak_factor", "report-weak", icir=0.1, rank_ic=0.02, coverage=0.5, turnover=0.4),
    ]
    weights = compute_rule_weights(reports, {"policy": "linear_score"})
    constrained, reasons = apply_portfolio_constraints(weights, {"max_factor_weight": 0.6})

    assert weights[0].weight > weights[1].weight
    assert max(weight.weight for weight in constrained) <= 0.6 + 1e-12
    assert sum(weight.weight for weight in constrained) == pytest.approx(1.0)
    assert {reason.code for reason in reasons} == {"MF_COMBINER_FACTOR_WEIGHT_CAPPED"}

    plan = build_multifactor_portfolio_plan(
        reports,
        _config(
            weighting_policy={"policy": "linear_score"},
            constraints={
                "max_factor_weight": 0.6,
                "target_count": 10,
                "benchmark_deviation_cap": 0.1,
                "capacity": {"max_daily_participation": 0.05},
            },
        ),
    )

    assert plan.status == "research_limited"
    assert max(plan.target_weights.values()) <= 0.6 + 1e-12
    assert "MF_COMBINER_FACTOR_WEIGHT_CAPPED" in _reason_codes(plan.blocked_reasons)


def test_ts_s05_03_blocked_or_claim_missing_reports_are_excluded_without_expanding_claims() -> None:
    reports = [
        _report("momentum_20d", "report-momentum"),
        _report("blocked_factor", "report-blocked", status="blocked"),
        _report("missing_claim_factor", "report-missing-claim", allowed_claims=[]),
    ]
    validation = validate_combiner_inputs(reports, _config().to_dict())
    plan = build_multifactor_portfolio_plan(reports, _config())

    assert validation.status == "research_limited"
    assert len(validation.accepted_reports) == 1
    assert {report["factor_id"] for report in validation.excluded_reports} == {
        "blocked_factor",
        "missing_claim_factor",
    }
    assert MF_COMBINER_REPORT_BLOCKED in _reason_codes(validation.research_limited_reasons)
    assert plan.status == "research_limited"
    assert plan.target_weights == pytest.approx({"momentum_20d": 1.0})
    assert plan.production_valid_claim_count == 0


def test_ts_s05_04_missing_cost_capacity_exposure_and_benchmark_fail_closed_or_research_limited() -> None:
    reports = [_report("momentum_20d", "report-momentum")]
    limited_plan = build_multifactor_portfolio_plan(
        reports,
        _config(
            cost_config={},
            capacity={},
            neutralization={"method": "industry_style", "evidence_required": True},
            constraints={
                "max_factor_weight": 1.0,
                "target_count": 5,
                "benchmark_deviation_cap": 0.1,
            },
        ),
    )
    blocked_plan = build_multifactor_portfolio_plan(
        reports,
        _config(benchmark={}, constraints={"max_factor_weight": 1.0, "target_count": 5}),
    )

    assert limited_plan.status == "research_limited"
    assert {
        MF_COMBINER_COST_MISSING,
        MF_COMBINER_CAPACITY_MISSING,
        MF_COMBINER_EXPOSURE_MISSING,
    } <= _reason_codes(limited_plan.blocked_reasons)
    assert limited_plan.cost_summary["status"] == "missing"
    assert limited_plan.capacity_summary["status"] == "missing"

    assert blocked_plan.status == "blocked"
    assert MF_COMBINER_BENCHMARK_MISSING in _reason_codes(blocked_plan.blocked_reasons)
    assert blocked_plan.target_weights == {}


def test_ts_s05_05_optimizer_and_external_runtime_requests_are_deferred_without_dependency_use() -> None:
    reports = [_report("momentum_20d", "report-momentum")]
    config = _config(
        weighting_policy={"policy": "rule_weight", "weights": {"momentum_20d": 1.0}},
        optimizer_policy={"enabled": True, "engine": "cvxpy EnhancedIndexing vectorbt ML_weighting"},
    )
    reasons = detect_optimizer_deferred_request(config.to_dict())
    plan = build_multifactor_portfolio_plan(reports, config)
    source = Path("engine/multifactor_combiner.py").read_text(encoding="utf-8").lower()

    assert MF_OPTIMIZER_DEFERRED in _reason_codes(reasons)
    assert plan.status == "blocked"
    assert MF_OPTIMIZER_DEFERRED in _reason_codes(plan.blocked_reasons)
    assert "import cvxpy" not in source
    assert "import qlib" not in source
    assert "import vectorbt" not in source
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "requests." not in source
    assert "urllib" not in source
    assert ".env" not in source


def test_ts_s05_06_no_broker_order_boundary_and_forbidden_operation_counters_are_zero() -> None:
    reports = [_report("momentum_20d", "report-momentum")]
    plan = build_multifactor_portfolio_plan(reports, _config(weighting_policy={"policy": "rule_weight"}))
    draft = to_portfolio_plan_draft(plan)
    bad_payload = {**draft, "order_submit": True}

    assert dict(plan.permission_counters) == FORBIDDEN_COUNTERS
    assert all(value == 0 for value in plan.permission_counters.values())
    assert assert_no_broker_order(plan).status == "pass"
    assert assert_no_broker_order(draft).status == "pass"
    bad_result = assert_no_broker_order(bad_payload)
    assert bad_result.status == "blocked"
    assert MF_BROKER_ORDER_FORBIDDEN in _reason_codes(bad_result.blocked_reasons)

    nonzero = dict(FORBIDDEN_COUNTERS)
    nonzero["qmt_operation"] = 1
    validation = validate_combiner_inputs(
        [_report("momentum_20d", "report-momentum", permission_counters=nonzero)],
        _config().to_dict(),
    )
    assert validation.status == "blocked"
    assert MF_COMBINER_FORBIDDEN_OPERATION_NONZERO in _reason_codes(validation.blocked_reasons)
