from __future__ import annotations

import pandas as pd

from engine.factor_model_validation import load_policy_cycle_config, policy_cycle_coverage


def test_builtin_policy_cycle_config_is_parseable_and_scoped_to_research() -> None:
    cycles = load_policy_cycle_config()

    assert not cycles.empty
    assert {"cycle_id", "name", "start", "end", "policy_type", "market", "source_ref"} <= set(cycles.columns)
    assert set(cycles["schema_version"]) == {"policy_cycle_config_v1"}


def test_policy_cycle_coverage_exposes_future_data_lake_dataset_candidates() -> None:
    joined = pd.DataFrame(
        {
            "trade_date": ["2024-01-02", "2024-02-02", "2024-03-04"],
            "symbol": ["000001.SZ", "000002.SZ", "000003.SZ"],
            "factor_id": ["momentum_20d"] * 3,
            "factor_value": [1.0, 2.0, 3.0],
            "forward_return": [0.01, 0.02, 0.03],
        }
    )

    result = policy_cycle_coverage(joined, None, {})

    assert result["status"] == "pass"
    assert result["coverage_ratio"] == 1.0
    assert result["data_lake_dataset_candidates"] == ("policy_cycle_events", "macro_policy_regime")
