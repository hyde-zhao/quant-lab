from __future__ import annotations

from engine.factor_library import (
    DEFAULT_EQUITY_CORE_FACTOR_IDS,
    equity_core_factor_definition_map,
    equity_core_factor_definitions,
    to_factor_spec,
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
