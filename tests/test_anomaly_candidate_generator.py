from __future__ import annotations

import pandas as pd

from engine.anomaly_candidate_generator import (
    DEFAULT_CONTROLLED_ANOMALY_TEMPLATES,
    build_candidate_matrices_from_panel,
    generate_controlled_anomaly_definitions,
)


def test_controlled_anomaly_generator_skips_missing_fields_and_preserves_prior_logic() -> None:
    definitions = generate_controlled_anomaly_definitions(available_fields=("pb",))

    assert tuple(item.anomaly_id for item in definitions) == ("auto_value_pb_inverse",)
    candidate = definitions[0]
    assert candidate.formula == "-pb"
    assert candidate.hypothesis
    assert candidate.economic_rationale
    assert candidate.prior_logic_ref == "controlled-template:valuation:pb_inverse"


def test_candidate_matrices_are_built_from_declared_templates_only() -> None:
    panel = pd.DataFrame(
        {
            "trade_date": ["2026-01-31"] * 6,
            "symbol": [f"{index:06d}.SZ" for index in range(6)],
            "pb": [6, 5, 4, 3, 2, 1],
            "unknown_profitable_noise": [100, 90, 80, 70, 60, 50],
        }
    )

    matrices = build_candidate_matrices_from_panel(panel)

    assert set(matrices) == {"auto_value_pb_inverse"}
    matrix = matrices["auto_value_pb_inverse"]
    assert matrix.loc["2026-01-31", "000005.SZ"] > matrix.loc["2026-01-31", "000000.SZ"]
    assert all(template.prior_logic_ref for template in DEFAULT_CONTROLLED_ANOMALY_TEMPLATES)
