from __future__ import annotations

import pandas as pd

from engine.factor_model_validation import STATUS_BLOCKED, STATUS_PASS, label_cutoff_gate, offline_online_feature_consistency
from engine.factor_robustness import build_offline_online_consistency_gate


def test_label_cutoff_gate_passes_when_label_is_available_after_feature_before_cutoff() -> None:
    result = label_cutoff_gate(
        _features(),
        _labels(),
        cutoff_time="2024-01-31T23:59:59+08:00",
        label_horizon_days=5,
        split_policy_ref="closure://split-policy-primary",
    )

    assert result["status"] == STATUS_PASS
    assert result["leakage_count"] == 0
    assert result["cutoff_violation_count"] == 0
    assert all(value == 0 for value in result["operation_counts"].values())


def test_label_cutoff_gate_blocks_when_label_available_before_feature() -> None:
    labels = _labels(label_available_at="2024-01-02T09:00:00+08:00")
    result = label_cutoff_gate(
        _features(),
        labels,
        cutoff_time="2024-01-31T23:59:59+08:00",
        label_horizon_days=5,
        split_policy_ref="closure://split-policy-primary",
    )

    assert result["status"] == STATUS_BLOCKED
    assert result["leakage_count"] == 1


def test_label_cutoff_gate_blocks_when_availability_exceeds_cutoff() -> None:
    result = label_cutoff_gate(
        _features(),
        _labels(label_available_at="2024-02-01T16:00:00+08:00"),
        cutoff_time="2024-01-31T23:59:59+08:00",
        label_horizon_days=5,
        split_policy_ref="closure://split-policy-primary",
    )

    assert result["status"] == STATUS_BLOCKED
    assert result["cutoff_violation_count"] == 1


def test_offline_online_consistency_passes_for_same_schema_and_values() -> None:
    result = offline_online_feature_consistency(_feature_values(), _feature_values(), feature_columns=("momentum_5d", "volatility_5d"))

    assert result["status"] == STATUS_PASS
    assert result["value_mismatch_count"] == 0
    assert result["feature_columns"] == ["momentum_5d", "volatility_5d"]
    assert all(value == 0 for value in result["operation_counts"].values())


def test_offline_online_consistency_blocks_schema_or_value_mismatch() -> None:
    schema_mismatch = offline_online_feature_consistency(
        _feature_values(),
        _feature_values().drop(columns=["volatility_5d"]),
        feature_columns=("momentum_5d", "volatility_5d"),
    )
    value_mismatch = offline_online_feature_consistency(
        _feature_values(),
        _feature_values(momentum=0.99),
        feature_columns=("momentum_5d", "volatility_5d"),
    )

    assert schema_mismatch["status"] == STATUS_BLOCKED
    assert "volatility_5d" in schema_mismatch["missing_online_features"]
    assert value_mismatch["status"] == STATUS_BLOCKED
    assert value_mismatch["value_mismatch_count"] == 1


def test_robustness_wrapper_marks_consistency_gate_without_real_operations() -> None:
    result = build_offline_online_consistency_gate(_feature_values(), _feature_values(), feature_columns=("momentum_5d",))

    assert result["status"] == STATUS_PASS
    assert result["robustness_gate"] == "offline_online_feature_consistency"
    assert all(value == 0 for value in result["operation_counts"].values())


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-01-02",
                "symbol": "AAA",
                "available_at": "2024-01-02T16:00:00+08:00",
                "momentum_5d": 0.12,
            }
        ]
    )


def _labels(label_available_at: str = "2024-01-08T16:00:00+08:00") -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-01-02",
                "symbol": "AAA",
                "label_available_at": label_available_at,
                "label_return": 0.03,
            }
        ]
    )


def _feature_values(momentum: float = 0.12) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "trade_date": "2024-01-02",
                "symbol": "AAA",
                "momentum_5d": momentum,
                "volatility_5d": 0.08,
                "available_at": "2024-01-02T16:00:00+08:00",
            }
        ]
    )
