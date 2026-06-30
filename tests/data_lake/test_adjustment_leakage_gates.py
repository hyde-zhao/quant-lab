from market_data.validation import (
    ADJUSTMENT_GATE_STATUS_FAIL,
    ADJUSTMENT_GATE_STATUS_PASS,
    ADJUSTMENT_LEAKAGE_STATUS_BLOCKED,
    CR017_EXECUTION_REQUIRES_RAW,
    CR017_MIXED_ADJUSTMENT_POLICY,
    CR017_REASON_REQUIRED_MISSING,
    CR017_S05_REASON_CODES,
    build_ts017_matrix,
    check_adjustment_parity,
    guard_execution_price_leakage,
)


def test_ts017_03_raw_execution_price_passes() -> None:
    result = guard_execution_price_leakage(
        {
            "view_id": "prices_raw",
            "execution_price_policy": "raw",
            "execution_price": 10.25,
            "raw_price_ref": "prices_raw:2026-01-02:000001.SZ",
        }
    )

    assert result.status == ADJUSTMENT_GATE_STATUS_PASS
    assert result.passed is True
    assert result.reason_code == ""
    assert result.policy == "raw"
    assert result.operation_counts["qmt_api_call"] == 0
    assert result.operation_counts["real_order"] == 0


def test_ts017_03_adjusted_execution_price_fails() -> None:
    result = guard_execution_price_leakage(
        {
            "view_id": "prices_qfq",
            "policy": "qfq",
            "field_name": "execution_price",
            "execution_price": 10.25,
        }
    )

    assert result.status == ADJUSTMENT_LEAKAGE_STATUS_BLOCKED
    assert result.passed is False
    assert result.reason_code == CR017_EXECUTION_REQUIRES_RAW
    assert result.blocked_reason == CR017_EXECUTION_REQUIRES_RAW
    assert result.field_name == "execution_price"


def test_ts017_03_adjusted_price_ref_fails() -> None:
    result = guard_execution_price_leakage(
        {
            "execution_price_policy": "raw",
            "execution_price_ref": "prices_hfq:2026-01-02:000001.SZ:adjusted_close",
        }
    )

    assert result.status == ADJUSTMENT_LEAKAGE_STATUS_BLOCKED
    assert result.reason_code == CR017_EXECUTION_REQUIRES_RAW
    assert result.field_name == "execution_price_ref"


def test_ts017_03_mixed_policy_fails_with_structured_reason() -> None:
    actual = [
        {
            "trade_date": "2026-01-02",
            "symbol": "000001.SZ",
            "view_id": "returns_adjusted",
            "research_adjustment_policy": "qfq",
            "adjusted_return": 0.10,
        },
        {
            "trade_date": "2026-01-03",
            "symbol": "000001.SZ",
            "view_id": "returns_adjusted",
            "research_adjustment_policy": "hfq",
            "adjusted_return": 0.11,
        },
    ]

    result = check_adjustment_parity(
        actual,
        actual,
        value_fields=("adjusted_return",),
        view_id="returns_adjusted",
    )

    assert result.status == ADJUSTMENT_GATE_STATUS_FAIL
    assert result.passed is False
    assert result.reason_code == CR017_MIXED_ADJUSTMENT_POLICY
    assert result.mismatch_reason == {
        "code": CR017_MIXED_ADJUSTMENT_POLICY,
        "policies_seen": ["hfq", "qfq"],
    }


def test_ts017_matrix_has_positive_and_failure_for_each_ts() -> None:
    matrix = build_ts017_matrix()

    assert set(matrix) == {"TS-017-01", "TS-017-02", "TS-017-03"}
    for ts_id, scenarios in matrix.items():
        kinds = {item["kind"] for item in scenarios}
        scenario_ids = {item["scenario_id"] for item in scenarios}
        assert {"positive", "failure"} <= kinds
        assert all(item.startswith(ts_id) for item in scenario_ids)

    assert CR017_REASON_REQUIRED_MISSING in CR017_S05_REASON_CODES
    assert CR017_MIXED_ADJUSTMENT_POLICY in CR017_S05_REASON_CODES
    assert CR017_EXECUTION_REQUIRES_RAW in CR017_S05_REASON_CODES
