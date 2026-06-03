import pandas as pd

from engine.research_dataset import evaluate_adjustment_gate
from market_data.adjustment_readers import (
    GATE_STATUS_BLOCKED,
    GATE_STATUS_PASS,
    READER_REQUIRED_METADATA_FIELDS,
    RESEARCH_ADJUSTMENT_POLICY_MISSING,
    RESEARCH_ADJUSTMENT_POLICY_MIXED,
    UNPUBLISHED_CANDIDATE_BLOCKED,
    build_qmt_policy_handoff,
    read_adjusted_view,
    single_policy_gate,
    zero_operation_counts,
)


def _adjusted_frame(*policies: str) -> pd.DataFrame:
    rows = []
    for index, policy in enumerate(policies or ("qfq",), start=1):
        trade_date = f"2026-01-0{index}"
        rows.append(
            {
                "view_id": "prices_qfq" if policy == "qfq" else "prices_hfq",
                "trade_date": trade_date,
                "symbol": "000001.SZ",
                "research_adjustment_policy": policy,
                "adjusted_close": 10.0 + index,
                "source_run_id": "run-cr017-s04",
                "quality_status": "pass",
            }
        )
    return pd.DataFrame(rows)


def test_reader_requires_explicit_policy() -> None:
    result = read_adjusted_view(
        "prices_qfq",
        frame=_adjusted_frame("qfq"),
        source_run_id="run-cr017-s04",
    )

    assert result.available is False
    assert result.status == GATE_STATUS_BLOCKED
    assert result.issues[0]["code"] == RESEARCH_ADJUSTMENT_POLICY_MISSING
    assert result.metadata.single_policy_gate_status == GATE_STATUS_BLOCKED
    assert result.operation_counts == zero_operation_counts()


def test_mixed_policy_blocks() -> None:
    frame = _adjusted_frame("qfq", "hfq")

    gate = single_policy_gate(frame, "qfq")
    reader_result = read_adjusted_view("prices_qfq", policy="qfq", frame=frame)
    dataset_gate = evaluate_adjustment_gate(frame, "qfq", {})

    assert gate.status == GATE_STATUS_BLOCKED
    assert gate.blocked_reason == RESEARCH_ADJUSTMENT_POLICY_MIXED
    assert reader_result.status == GATE_STATUS_BLOCKED
    assert reader_result.issues[0]["code"] == RESEARCH_ADJUSTMENT_POLICY_MIXED
    assert dataset_gate["metadata"]["single_policy_gate_status"] == GATE_STATUS_BLOCKED
    assert {issue.code for issue in dataset_gate["issues"]} == {"adjustment_policy_mixed"}


def test_reader_metadata_contains_required_fields() -> None:
    result = read_adjusted_view(
        "prices_qfq",
        policy="qfq",
        frame=_adjusted_frame("qfq"),
        source_run_id="run-cr017-s04",
    )

    metadata = result.to_metadata()
    assert result.available is True
    assert {field for field in READER_REQUIRED_METADATA_FIELDS if field in metadata} == set(
        READER_REQUIRED_METADATA_FIELDS
    )
    assert metadata["policy"] == "qfq"
    assert metadata["research_adjustment_policy"] == "qfq"
    assert metadata["view_id"] == "prices_qfq"
    assert metadata["source_run_id"] == "run-cr017-s04"
    assert metadata["quality_status"] == "pass"
    assert metadata["single_policy_gate_status"] == GATE_STATUS_PASS
    assert result.frame is not None
    assert result.frame.attrs["single_policy_gate_status"] == GATE_STATUS_PASS


def test_unpublished_candidate_blocks() -> None:
    result = read_adjusted_view(
        "prices_qfq",
        policy="qfq",
        frame=_adjusted_frame("qfq"),
        source_run_id="run-cr017-s04",
        candidate_published=False,
    )

    assert result.status == GATE_STATUS_BLOCKED
    assert result.issues[0]["code"] == UNPUBLISHED_CANDIDATE_BLOCKED
    assert result.metadata.single_policy_gate_status == GATE_STATUS_BLOCKED
    assert result.frame is None


def test_qmt_handoff_uses_raw_execution_policy() -> None:
    handoff = build_qmt_policy_handoff(
        "qfq",
        {"view_id": "prices_raw", "trade_date": "2026-01-02", "symbol": "000001.SZ"},
        view_id="prices_qfq",
        source_run_id="run-cr017-s04",
    )
    payload = handoff.to_dict()

    assert handoff.passed is True
    assert payload["research_adjustment_policy"] == "qfq"
    assert payload["execution_price_policy"] == "raw"
    assert payload["raw_price_ref"] == "prices_raw:2026-01-02:000001.SZ"
    assert payload["adjusted_execution_price_pass_count"] == 0
    assert "adjusted_execution_price" not in payload
    assert "adjusted_price" not in payload
    assert payload["operation_counts"] == zero_operation_counts()
