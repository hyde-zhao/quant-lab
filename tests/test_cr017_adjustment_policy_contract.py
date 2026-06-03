from pathlib import Path

from market_data.adjustment_policy import (
    EXECUTION_REQUIRES_RAW,
    UNKNOWN_POLICY,
    AdjustmentPolicy,
    ConsumerCategory,
    build_legacy_qfq_migration_summary,
    evaluate_consumer_policy,
    normalize_adjustment_policy,
    render_policy_matrix,
    zero_operation_counts,
)


def test_policy_ids_cover_four_classes() -> None:
    assert {policy.value for policy in AdjustmentPolicy} == {
        "raw",
        "qfq",
        "hfq",
        "returns_adjusted",
    }

    matrix = render_policy_matrix()
    assert {decision.policy_id for decision in matrix} == {
        "raw",
        "qfq",
        "hfq",
        "returns_adjusted",
    }


def test_unknown_policy_blocks_with_structured_reason() -> None:
    result = normalize_adjustment_policy("forward_adjusted")

    assert result.allowed is False
    assert result.blocked_reason == UNKNOWN_POLICY
    assert result.operation_counts == zero_operation_counts()


def test_qmt_execution_requires_raw() -> None:
    decisions = {
        policy.value: evaluate_consumer_policy(ConsumerCategory.QMT_EXECUTION, policy)
        for policy in AdjustmentPolicy
    }

    assert decisions["raw"].allowed is True
    assert {
        policy_id
        for policy_id, decision in decisions.items()
        if policy_id != "raw" and decision.allowed
    } == set()
    assert {
        decision.blocked_reason
        for policy_id, decision in decisions.items()
        if policy_id != "raw"
    } == {EXECUTION_REQUIRES_RAW}


def test_migration_summary_preserves_legacy_qfq() -> None:
    summary = build_legacy_qfq_migration_summary("legacy://qfq-baseline/cr010")

    assert summary.legacy_qfq_baseline_preserved is True
    assert summary.view_id == "prices_qfq"
    assert summary.compatibility_entry == "legacy_qfq_readonly"
    assert summary.single_policy_gate_status == "single_policy_gate_required"
    assert "覆盖" in summary.forbidden_overwrite_note
    assert summary.operation_counts == zero_operation_counts()


def test_migration_document_contains_required_statement() -> None:
    text = Path("docs/ADJUSTMENT-POLICY-MIGRATION.md").read_text(encoding="utf-8")

    assert "`legacy_qfq_baseline_preserved` | `true`" in text
    assert "legacy_qfq_readonly" in text
    assert "legacy_qfq_overwrite | 0" in text
    assert "QMT execution consumers may use only `raw`" in text


def test_s01_operation_counts_are_zero() -> None:
    assert zero_operation_counts() == {
        "provider_fetch": 0,
        "lake_write": 0,
        "credential_read": 0,
        "current_pointer_publish": 0,
        "dependency_change": 0,
        "legacy_qfq_overwrite": 0,
    }
