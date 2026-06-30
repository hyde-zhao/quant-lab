from __future__ import annotations

from engine.factor_library import (
    DEFAULT_EQUITY_CORE_FACTOR_IDS,
    OWNERSHIP_ENGINE_CORE,
    OWNERSHIP_EXPERIMENT_LOCAL,
    OWNERSHIP_FUTURE_PRODUCTION_CANDIDATE,
    OWNERSHIP_RESEARCH_CANDIDATE,
    EquityFactorDefinition,
    build_equity_factor_library,
    classify_equity_factor_ownership,
    equity_core_factor_definition_map,
    equity_core_factor_definitions,
    factor_ownership_matrix,
    to_factor_specs,
    to_factor_spec,
    validate_equity_factor_library,
)
from engine.multifactor_contracts import validate_factor_spec


def test_equity_core_factor_library_uses_generic_factor_ids() -> None:
    definitions = equity_core_factor_definitions()
    factor_ids = {definition.factor_id for definition in definitions}

    assert set(DEFAULT_EQUITY_CORE_FACTOR_IDS) == factor_ids
    assert all(not factor_id.startswith("chapter3") for factor_id in factor_ids)
    assert all(
        any(ref.startswith("book:factor_investing:chapter3:") for ref in definition.source_refs)
        for definition in definitions
    )


def test_equity_core_factor_definitions_export_cr030_factor_spec() -> None:
    definitions = equity_core_factor_definition_map()

    spec = to_factor_spec(definitions["value_bm"])
    validation = validate_factor_spec(spec)

    assert spec.factor_id == "value_bm"
    assert spec.data_lineage["source_of_truth"] == "project_factor_library"
    assert spec.params["source_refs"] == ("book:factor_investing:chapter3:3.4",)
    assert validation.passed


def test_equity_factor_library_supports_long_term_custom_definitions() -> None:
    custom = EquityFactorDefinition(
        factor_id="quality_gross_profit_assets",
        name="毛利资产质量因子",
        category="quality",
        raw_variable="gross_profit / total_assets",
        direction="positive",
        input_fields=("financials.gross_profit_ttm", "financials.total_assets"),
        formula="gross_profit_ttm / total_assets",
        default_window=1,
        source_refs=("internal:research:quality_factor:v1",),
    )

    library = build_equity_factor_library([custom])
    issues = validate_equity_factor_library(library)
    specs = to_factor_specs({"quality_gross_profit_assets": library["quality_gross_profit_assets"]})

    assert "quality_gross_profit_assets" in library
    assert issues == {}
    assert specs[0].factor_id == "quality_gross_profit_assets"
    assert validate_factor_spec(specs[0]).passed


def test_equity_factor_library_rejects_chapter_namespace_for_factor_id() -> None:
    invalid = EquityFactorDefinition(
        factor_id="chapter3_quality",
        name="错误命名因子",
        category="quality",
        raw_variable="quality",
        direction="positive",
        input_fields=("x",),
        formula="x",
        default_window=1,
        source_refs=("internal:test",),
    )

    issues = validate_equity_factor_library([invalid])

    assert "factor_id 不得使用书籍章节作为命名空间" in issues["chapter3_quality"]


def test_factor_ownership_keeps_experiment_dynamic_factors_out_of_core() -> None:
    decisions = {
        item.factor_id: item
        for item in factor_ownership_matrix(
            [
                "value_bm",
                "momentum_20d",
                "volume_ratio_20d",
                "volatility_20d",
                "rsi_14",
                "unknown_alpha",
            ]
        )
    }

    assert decisions["value_bm"].ownership == OWNERSHIP_ENGINE_CORE
    assert decisions["value_bm"].calculator_available is True
    assert decisions["momentum_20d"].ownership == OWNERSHIP_EXPERIMENT_LOCAL
    assert decisions["volume_ratio_20d"].ownership == OWNERSHIP_EXPERIMENT_LOCAL
    assert decisions["volatility_20d"].ownership == OWNERSHIP_EXPERIMENT_LOCAL
    assert decisions["rsi_14"].ownership == OWNERSHIP_EXPERIMENT_LOCAL
    assert decisions["unknown_alpha"].ownership == OWNERSHIP_RESEARCH_CANDIDATE


def test_core_factor_requires_engine_calculator_before_core_ownership() -> None:
    decision = classify_equity_factor_ownership("value_bm", calculator_ids=("market_beta_252",))

    assert decision.ownership == OWNERSHIP_FUTURE_PRODUCTION_CANDIDATE
    assert decision.calculator_available is False
    assert "缺少 engine calculator" in decision.reason
