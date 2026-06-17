from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine import order_intent_draft as draft_contract
from engine.order_intent_draft import (
    FORBIDDEN_OPERATION_COUNTERS,
    LATER_GATED_CONSUMER,
    REQUIRED_DRAFT_FIELDS,
    SCHEMA_VERSION,
    OrderIntentDraftValidationError,
    assert_no_qmt_side_effects,
    build_order_intent_draft,
    to_later_gated_handoff,
    validate_order_intent_draft,
    zero_forbidden_operation_counts,
)
from engine.semantic_diff import build_semantic_diff, zero_forbidden_operation_counts as semantic_zero_counts


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _target_row(**overrides):
    result = {
        "target_portfolio_id": "target-portfolio-cr025-fixture",
        "strategy_id": "strategy-cr025-fixture",
        "run_id": "run-cr025-draft",
        "signal_date": "2026-06-01",
        "target_trade_date": "2026-06-02",
        "symbol": "000001.SZ",
        "side": "buy",
        "target_qty": 200,
        "target_weight": "0.10",
        "estimated_price_policy": "research_close_estimate",
        "research_adjustment_policy": "qfq",
        "cost_config_ref": "cost-config:fixture",
        "reason": "semantic-diff-rebalance-fixture",
    }
    result.update(overrides)
    return result


def _semantic_diff_artifact(**config_overrides):
    baseline = {
        "run_id": "run-cr025-draft",
        "lineage": {"release_id": "release-fixture", "source_run_id": "run-cr025-draft"},
        "metrics": {"final_value": 1_000_000.0, "total_return": 0.01},
        "fills": [{"trade_date": "2026-06-02", "symbol": "000001.SZ", "price": 10.0, "quantity": 200}],
    }
    reference = {
        "run_id": "run-cr025-reference",
        "lineage": {"source": "reference-fixture"},
        "metrics": {"final_value": 999_900.0, "total_return": 0.0099},
        "fills": [{"trade_date": "2026-06-02", "symbol": "000001.SZ", "price": 10.01, "quantity": 200}],
    }
    selection = {
        "selected_backend": "backtrader",
        "availability_status": "available",
        "lineage": {"selector": "fixture"},
        "limitations": [{"code": "fixture_only"}],
        "forbidden_operation_counts": semantic_zero_counts(),
    }
    config = {
        "generated_at": "2026-06-02T08:30:00+08:00",
        "source_run_id": "run-cr025-draft",
        "lineage": {"quality_evidence_ref": "quality:fixture"},
        "limitations": [{"code": "research_comparison_only"}],
    }
    config.update(config_overrides)
    return build_semantic_diff(baseline, reference, selection, config)


def _policy(**overrides):
    result = {
        "source_run_id": "run-cr025-draft",
        "semantic_diff_artifact_id": "semantic-diff:run-cr025-draft",
        "execution_price_policy": "raw",
        "raw_execution_policy_status": "pass",
        "pretrade_required": True,
        "operation_counters": zero_forbidden_operation_counts(),
    }
    result.update(overrides)
    return result


def _valid_result():
    return build_order_intent_draft(
        [_target_row()],
        _semantic_diff_artifact(),
        _policy(),
    )


def test_t_s03_01_builds_valid_draft_from_semantic_diff_and_target_portfolio() -> None:
    result = _valid_result()

    assert result.status == "draft"
    assert result.passed is True
    assert result.draft is not None
    payload = result.draft.to_dict()
    validation = validate_order_intent_draft(result.draft)

    assert validation.passed is True
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["semantic_diff_artifact_id"] == "semantic-diff:run-cr025-draft"
    assert payload["qmt_allowed"] is False
    assert payload["not_authorization"] is True
    assert payload["execution_price_policy"] == "raw"
    assert payload["consumer"] == LATER_GATED_CONSUMER
    assert result.handoff is not None


def test_t_s03_02_non_raw_execution_price_policy_hard_blocks_without_handoff() -> None:
    result = build_order_intent_draft(
        [_target_row()],
        _semantic_diff_artifact(),
        _policy(execution_price_policy="qfq"),
    )

    assert result.status == "blocked"
    assert result.draft is None
    assert result.handoff is None
    assert "non_raw_execution_price_policy" in result.blocked_reasons
    assert "raw_execution_policy_blocked" in result.blocked_reasons
    assert all(value == 0 for value in result.operation_counters.values())
    with pytest.raises(OrderIntentDraftValidationError):
        to_later_gated_handoff(result)


def test_t_s03_03_required_fields_have_full_schema_coverage() -> None:
    result = _valid_result()
    assert result.draft is not None

    payload = result.draft.to_dict()
    validation = validate_order_intent_draft(payload)

    assert validation.passed is True
    assert validation.required_field_coverage == 1.0
    assert set(REQUIRED_DRAFT_FIELDS).issubset(payload)
    assert validation.missing_required_fields == ()
    for field_name in (
        "draft_id",
        "source_run_id",
        "target_portfolio_id",
        "semantic_diff_artifact_id",
        "data_lineage_ref",
        "limitations",
        "raw_execution_policy_status",
        "pretrade_required",
        "operation_counters",
    ):
        assert field_name in payload


@pytest.mark.parametrize(
    ("semantic_override", "expected_reason"),
    [
        ({"lineage": {}}, "missing_lineage"),
        ({"limitations": None}, "missing_limitations"),
    ],
)
def test_t_s03_04_missing_lineage_or_limitations_fail_closed(semantic_override, expected_reason) -> None:
    semantic = _semantic_diff_artifact().to_dict()
    metadata = dict(semantic["metadata"])
    if "lineage" in semantic_override:
        metadata["lineage"] = semantic_override["lineage"]
        semantic["metadata"] = metadata
    if "limitations" in semantic_override:
        semantic.pop("limitations", None)
        semantic["availability"] = {
            key: value
            for key, value in semantic["availability"].items()
            if key != "limitations"
        }

    result = build_order_intent_draft([_target_row()], semantic, _policy())

    assert result.status == "blocked"
    assert result.draft is None
    assert result.handoff is None
    assert expected_reason in result.blocked_reasons


def test_t_s03_05_later_gated_handoff_never_authorizes_qmt() -> None:
    result = _valid_result()

    handoff = to_later_gated_handoff(result)

    assert handoff["consumer"] == LATER_GATED_CONSUMER
    assert handoff["handoff_status"] == "later-gated"
    assert handoff["not_authorization"] is True
    assert handoff["qmt_allowed"] is False
    assert handoff["requires_independent_authorization"] is True
    assert handoff["required_follow_up"] == ["CR-020", "CR-021", "CR-022", "CR-023", "CR-024"]
    assert "order_submit" in handoff["does_not_authorize"]


def test_t_s03_06_forbidden_operation_counters_cover_required_surface_and_remain_zero() -> None:
    valid = _valid_result()
    blocked = build_order_intent_draft(
        [_target_row()],
        _semantic_diff_artifact(),
        _policy(execution_price_policy="hfq"),
    )

    assert set(valid.operation_counters) == set(FORBIDDEN_OPERATION_COUNTERS)
    assert set(assert_no_qmt_side_effects(valid)) == set(FORBIDDEN_OPERATION_COUNTERS)
    assert all(value == 0 for value in assert_no_qmt_side_effects(valid).values())
    assert all(value == 0 for value in assert_no_qmt_side_effects(blocked).values())

    payload = valid.draft.to_dict()  # type: ignore[union-attr]
    payload["operation_counters"]["order_submit"] = 1
    validation = validate_order_intent_draft(payload)

    assert validation.passed is False
    assert any(violation.code == "forbidden_operation_nonzero" for violation in validation.violations)


def test_t_s03_07_module_static_import_boundary_excludes_qmt_broker_and_backtrader_runtime() -> None:
    tree = ast.parse((PROJECT_ROOT / "engine" / "order_intent_draft.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    forbidden_import_roots = {
        "backtrader",
        "xtquant",
        "qmt",
        "miniqmt",
        "broker",
        "trading",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
    }
    assert not [
        name
        for name in imports
        if any(name == item or name.startswith(f"{item}.") for item in forbidden_import_roots)
    ]


def test_t_s03_08_draft_rejects_credentials_sessions_and_real_account_ids() -> None:
    result = _valid_result()
    assert result.draft is not None
    payload = result.draft.to_dict()
    assert validate_order_intent_draft(payload).passed is True

    payload["account_id"] = "real-account-should-not-appear"
    payload["data_lineage_ref"] = {"release_id": "release-fixture", "session": "session-should-not-appear"}
    validation = validate_order_intent_draft(payload)

    assert validation.passed is False
    assert any(violation.code == "sensitive_material_present" for violation in validation.violations)


def test_qmt_allowed_true_input_is_blocked_and_not_rewritten_into_authorization() -> None:
    result = build_order_intent_draft(
        [_target_row(qmt_allowed=True)],
        _semantic_diff_artifact(),
        _policy(),
    )

    assert result.status == "blocked"
    assert result.draft is None
    assert "qmt_not_authorized" in result.blocked_reasons
    assert result.handoff is None


def test_order_intent_draft_public_contract_exports_expected_interfaces() -> None:
    for name in (
        "build_order_intent_draft",
        "validate_order_intent_draft",
        "block_order_intent",
        "to_later_gated_handoff",
        "assert_no_qmt_side_effects",
    ):
        assert name in draft_contract.__all__
