from __future__ import annotations

from market_data.benchmarks import BenchmarkDefinition, list_required_benchmarks
from trading.qmt_gateway_contracts import CommissionSchedule
from trading.qmt_gateway_service import GatewayService
from engine.mature_multifactor_framework import (
    build_stage2_portfolio_risk_policy,
    validate_portfolio_risk_policy,
)


def test_s17_benchmark_definitions_include_versioned_risk_free_curve_contract() -> None:
    definitions = list_required_benchmarks()

    assert definitions
    for definition in definitions:
        payload = definition.to_dict()
        assert payload["version"] == "benchmark-config-v1"
        assert payload["effective_from"] == "2026-06-30"
        assert payload["release_id"] == "config-facts-cr139-v1"
        assert payload["risk_free_curve_ref"].startswith("config_facts/risk_free_curve/")


def test_s17_custom_benchmark_definition_preserves_version_metadata() -> None:
    definition = BenchmarkDefinition(
        benchmark_id="custom",
        display_name="Custom Benchmark",
        index_code="000000.SH",
        provider_symbol="custom_provider",
        version="benchmark-config-v2",
        effective_from="2026-07-01",
        release_id="config-facts-release-002",
        risk_free_curve_ref="config_facts/risk_free_curve/custom/release-002",
    )

    payload = definition.to_dict()

    assert payload["version"] == "benchmark-config-v2"
    assert payload["effective_from"] == "2026-07-01"
    assert payload["release_id"] == "config-facts-release-002"
    assert payload["risk_free_curve_ref"] == "config_facts/risk_free_curve/custom/release-002"


def test_s18_commission_schedule_includes_version_fee_and_slippage_contract() -> None:
    schedule = CommissionSchedule(
        instrument_type="stock",
        rate=0.0003,
        min_fee=5.0,
        source="configured",
        slippage_bps=8.0,
        stamp_duty_rate=0.001,
        transfer_fee_rate=0.00001,
    )

    payload = schedule.to_dict()

    assert payload["version"] == "commission-config-v1"
    assert payload["effective_from"] == "2026-06-30"
    assert payload["release_id"] == "config-facts-cr139-v1"
    assert payload["slippage_bps"] == 8.0
    assert payload["stamp_duty_rate"] == 0.001
    assert payload["transfer_fee_rate"] == 0.00001


def test_s18_gateway_commission_query_remains_contract_only_and_versioned() -> None:
    schedule = GatewayService().query_commission_schedule(instrument_type="stock")

    assert schedule.source == "configured"
    assert schedule.authorization_ref == ""
    assert schedule.to_dict()["release_id"] == "config-facts-cr139-v1"


def test_s19_portfolio_risk_policy_builder_includes_versioned_universe_contract() -> None:
    policy = build_stage2_portfolio_risk_policy(
        policy_id="stage2-risk-policy-v1",
        top_n=80,
        max_weight=0.025,
        turnover_limit=0.2,
    )
    payload = policy.to_dict()

    assert payload["version"] == "stage2-v1"
    assert payload["effective_from"] == "2026-06-30"
    assert payload["release_id"] == "config-facts-cr139-v1"
    assert payload["universe_policy_ref"].startswith("config_facts/universe_policy/")
    assert payload["delisting_policy"] == "exclude_delisted"
    assert payload["st_policy"] == "exclude_st"
    assert validate_portfolio_risk_policy(policy).passed is True


def test_s19_portfolio_risk_policy_validation_blocks_missing_version_metadata() -> None:
    result = validate_portfolio_risk_policy(
        {
            "policy_id": "missing-version-policy",
            "top_n": 80,
            "max_weight": 0.025,
            "turnover_limit": 0.2,
            "industry_limit": {},
            "style_limit": {},
            "capacity_assumption": {},
            "fee_slippage_ref": "config_facts/commission/stock/config-facts-cr139-v1",
            "stop_conditions": ["risk_policy_failed"],
        }
    )

    assert result.passed is False
    assert {"version", "effective_from", "release_id"} <= {reason.field for reason in result.blocked_reasons}
