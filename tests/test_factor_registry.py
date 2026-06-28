from __future__ import annotations

from engine.factor_calculators import core_equity_factor_calculators
from engine.factor_library import DEFAULT_EQUITY_CORE_FACTOR_IDS
from engine.factor_registry import (
    CHAPTER5_ANOMALY_PROXY_FACTOR_IDS,
    STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS,
    FactorAvailabilityStatus,
    factor_catalog_entries,
    validate_factor_catalog,
)


def test_factor_catalog_has_unique_valid_entries() -> None:
    entries = factor_catalog_entries()
    factor_ids = [entry.factor_id for entry in entries]

    assert len(factor_ids) == len(set(factor_ids))
    assert validate_factor_catalog(entries) == {}


def test_factor_catalog_covers_core_stage3_and_chapter5_proxy_factors() -> None:
    factor_ids = {entry.factor_id for entry in factor_catalog_entries()}

    assert set(DEFAULT_EQUITY_CORE_FACTOR_IDS) <= factor_ids
    assert set(STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS) <= factor_ids
    assert set(CHAPTER5_ANOMALY_PROXY_FACTOR_IDS) <= factor_ids


def test_stage3_active_factors_are_marked_for_stage3_consumer() -> None:
    stage3_entries = [
        entry
        for entry in factor_catalog_entries()
        if entry.status == FactorAvailabilityStatus.STAGE3_ACTIVE.value
    ]

    assert {entry.factor_id for entry in stage3_entries} == set(STAGE3_MATURE_MULTIFACTOR_FACTOR_IDS)
    assert all("stage3_mature_multifactor" in entry.used_by for entry in stage3_entries)


def test_calculable_factors_have_core_or_runner_local_calculator_status() -> None:
    core_calculators = core_equity_factor_calculators()
    checked_statuses = {
        FactorAvailabilityStatus.CALCULABLE.value,
        FactorAvailabilityStatus.STAGE3_ACTIVE.value,
    }

    for entry in factor_catalog_entries():
        if entry.status not in checked_statuses:
            continue
        has_core_calculator = entry.factor_id in core_calculators
        has_runner_local_calculator = entry.calculator_status.startswith("runner_local:")
        assert has_core_calculator or has_runner_local_calculator, entry.factor_id


def test_proxy_only_factors_reference_sources_and_requirements() -> None:
    proxy_entries = [
        entry
        for entry in factor_catalog_entries()
        if entry.status == FactorAvailabilityStatus.PROXY_ONLY.value
    ]

    assert {entry.factor_id for entry in proxy_entries} == set(CHAPTER5_ANOMALY_PROXY_FACTOR_IDS)
    assert all(entry.source_refs for entry in proxy_entries)
    assert all(entry.required_factor_ids or entry.notes for entry in proxy_entries)
