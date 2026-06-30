from __future__ import annotations

import pandas as pd

from engine.factor_model_validation import (
    STATUS_BLOCKED,
    STATUS_PASS,
    load_policy_cycle_config,
    policy_cycle_shortability_gate,
)


def test_builtin_policy_cycle_config_has_version_and_release_closure() -> None:
    cycles = load_policy_cycle_config()

    assert not cycles.empty
    assert {"version", "release_id", "schema_version"} <= set(cycles.columns)
    assert cycles["version"].astype(str).str.len().gt(0).all()
    assert cycles["release_id"].astype(str).str.len().gt(0).all()
    assert set(cycles["schema_version"]) == {"policy_cycle_config_v1"}


def test_policy_cycle_shortability_gate_passes_with_release_and_shortable_universe() -> None:
    result = policy_cycle_shortability_gate(
        _joined(),
        _cycles(),
        _tradability(shortable=[True, True, False, True]),
        {"strategy_type": "long_short", "min_shortable_ratio": 0.5},
    )

    assert result["status"] == STATUS_PASS
    assert result["policy_cycle_coverage"]["coverage_ratio"] == 1.0
    assert result["short_feasibility"]["shortable_ratio"] == 0.75
    assert result["missing_release_count"] == 0
    assert result["missing_version_count"] == 0
    assert all(value == 0 for value in result["operation_counts"].values())


def test_policy_cycle_shortability_gate_blocks_missing_release_metadata() -> None:
    cycles = _cycles()
    cycles.loc[0, "release_id"] = ""
    result = policy_cycle_shortability_gate(
        _joined(),
        cycles,
        _tradability(shortable=[True, True, True, True]),
        {"strategy_type": "long_short"},
    )

    assert result["status"] == STATUS_BLOCKED
    assert result["missing_release_count"] == 1


def test_policy_cycle_shortability_gate_blocks_insufficient_shortable_universe() -> None:
    result = policy_cycle_shortability_gate(
        _joined(),
        _cycles(),
        _tradability(shortable=[True, False, False, False]),
        {"strategy_type": "long_short", "min_shortable_ratio": 0.5},
    )

    assert result["status"] == STATUS_BLOCKED
    assert result["short_feasibility"]["status"] == STATUS_BLOCKED


def _joined() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "trade_date": ["2024-01-02", "2024-02-02", "2024-03-04", "2024-04-08"],
            "symbol": ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ"],
            "factor_id": ["momentum_20d"] * 4,
            "factor_value": [1.0, 2.0, 3.0, 4.0],
            "forward_return": [0.01, 0.02, 0.03, 0.04],
        }
    )


def _cycles() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "cycle_id": "market_support_2024",
                "version": "v1",
                "release_id": "policy-cycle-release-2026-06-30",
                "name": "Market support",
                "start": "2024-01-01",
                "end": "2024-12-31",
                "policy_type": "capital_market_support",
                "market": "CN_A",
                "source_ref": "fixture://policy-cycle",
                "schema_version": "policy_cycle_config_v1",
            }
        ]
    )


def _tradability(*, shortable: list[bool]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": [f"00000{index}.SZ" for index in range(1, len(shortable) + 1)],
            "shortable": shortable,
        }
    )
