from __future__ import annotations

import json
from pathlib import Path

from scripts.qmt.run_multifactor_simulation_operator import main as operator_main
from trading.strategy_runner import (
    allowed_evidence_data_classes,
    build_default_stability_window_definition,
    build_exception_recovery_matrix,
    build_pre_trading_window_checklist,
    operator_signal_rows_from_admission,
    validate_operator_evidence,
    validate_strategy_admission_for_runner,
)


def test_strategy_admission_package_contract_feeds_runner_p1_without_authorization() -> None:
    package = _admission_package()

    result = validate_strategy_admission_for_runner(package)
    rows = operator_signal_rows_from_admission(package)

    assert result.passed is True
    assert result.strategy_id == "strategy_portfolio_alpha"
    assert result.source_run_id == "research-run-fixture"
    assert len(rows) == 2
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True)
    assert "000001.SZ" not in rendered
    assert result.safety_counters["credential_read"] == 0
    assert result.safety_counters["qmt_start"] == 0
    assert result.not_authorization is True


def test_strategy_admission_package_blocks_nonzero_operation_or_authorization_claim() -> None:
    package = _admission_package()
    package["not_simulation_authorization"] = False
    package["operation_counts"]["submit_order"] = 1

    result = validate_strategy_admission_for_runner(package)

    assert result.blocked is True
    assert "authorization_flag_missing:not_simulation_authorization" in result.blocked_reasons
    assert "forbidden_operation_nonzero" in result.blocked_reasons


def test_operator_cli_fixture_mode_writes_redacted_evidence_without_env_or_runtime(tmp_path: Path) -> None:
    spec_path = tmp_path / "operator-spec.json"
    spec_path.write_text(json.dumps(_operator_spec(), ensure_ascii=False), encoding="utf-8")
    output_dir = tmp_path / "evidence"

    exit_code = operator_main(
        [
            "--mode",
            "fixture",
            "--spec-json",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    evidence_path = output_dir / "non-trading-run" / "operator-evidence.json"
    index_path = output_dir / "non-trading-run" / "operator-evidence.index.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert evidence["status"] == "pass"
    assert evidence["runtime_authorization_granted"] is False
    assert evidence["execution"]["status"] == "no_op"
    assert evidence["execution"]["submitted_count"] == 0
    assert validate_operator_evidence(evidence, mode="fixture").passed is True
    assert index["validation"]["status"] == "pass"
    rendered = evidence_path.read_text(encoding="utf-8")
    assert "000001.SZ" not in rendered
    assert "token=abc" not in rendered.lower()
    assert "secret-fixture" not in rendered.lower()


def test_operator_cli_preflight_and_plan_only_modes_do_not_require_env(tmp_path: Path) -> None:
    spec_path = tmp_path / "operator-spec.json"
    spec_path.write_text(json.dumps(_operator_spec(), ensure_ascii=False), encoding="utf-8")

    for mode in ("preflight-only", "plan-only", "reconcile-only"):
        output_dir = tmp_path / mode
        exit_code = operator_main(
            [
                "--mode",
                mode,
                "--spec-json",
                str(spec_path),
                "--output-dir",
                str(output_dir),
            ]
        )
        evidence = json.loads(
            (output_dir / "non-trading-run" / "operator-evidence.json").read_text(encoding="utf-8")
        )
        assert exit_code == 0
        assert evidence["runtime_authorization_granted"] is False
        assert validate_operator_evidence(evidence, mode=mode).passed is True


def test_evidence_schema_blocks_raw_flags_and_lists_allowed_data_classes() -> None:
    payload = _minimal_evidence()
    payload["redaction_policy"]["raw_symbol_saved"] = True
    payload["persistence_policy"]["raw_payload_allowed"] = True

    result = validate_operator_evidence(payload, mode="fixture")
    data_classes = {item["data_class"] for item in allowed_evidence_data_classes()}

    assert result.blocked is True
    assert "raw_symbol_saved" in result.forbidden_flags
    assert "raw_payload_allowed" in result.forbidden_flags
    assert {
        "authorization",
        "position_snapshot",
        "target_portfolio",
        "order_plan",
        "submit_cancel",
        "reconciliation",
    } <= data_classes


def test_non_trading_checklist_exception_matrix_and_stability_window_are_fail_closed() -> None:
    checklist = build_pre_trading_window_checklist()
    matrix = build_exception_recovery_matrix()
    window = build_default_stability_window_definition(required_runs=5, required_trading_days=3)

    assert {item.item_id for item in checklist} >= {
        "authorization_draft_ready",
        "strategy_admission_contract_pass",
        "operator_fixture_pass",
        "evidence_schema_pass",
        "manual_takeover_ready",
    }
    assert {item.item_id for item in matrix} >= {
        "authorization_expired",
        "gateway_health_fail",
        "query_positions_redaction_fail",
        "order_submit_unknown",
        "cancel_unknown",
        "recon_diff",
    }
    assert all(item.fail_closed_action for item in checklist + matrix)
    assert window.required_runs == 5
    assert window.required_trading_days == 3
    assert "unknown_order_unresolved" in window.fail_criteria
    assert window.safety_counters["qmt_api_call"] == 0


def _operator_spec() -> dict[str, object]:
    return {
        "strategy_id": "strategy-alpha",
        "run_id": "non-trading-run",
        "target_trade_date": "2026-06-25",
        "expected_runtime_profile": "cr138-simulation",
        "signal_rows": [{"symbol": "000001.SZ", "score": "0.9", "signal_date": "2026-06-25"}],
        "top_n": 1,
        "capital_base": "10000",
        "current_positions": {"000001.SZ": 0},
        "risk_snapshot": {
            "cash_available": "20000",
            "positions_available": {"000001.SZ": 0},
            "t1_sellable": {"000001.SZ": 0},
            "raw_price_refs": {"000001.SZ": {"price": "10", "evidence_ref": "price-ref"}},
            "evidence_ref": "fixture:risk-snapshot",
        },
        "risk_profile": {
            "risk_profile_id": "risk-profile-simulation",
            "max_single_symbol_notional": "20000",
            "max_portfolio_notional": "20000",
            "lot_size": 100,
        },
    }


def _admission_package() -> dict[str, object]:
    counts = {
        "nas_read": 0,
        "nas_write": 0,
        "nas_list": 0,
        "nas_copy": 0,
        "nas_publish": 0,
        "nas_pull": 0,
        "credential_read": 0,
        "env_file_read": 0,
        "qmt_start": 0,
        "miniqmt_start": 0,
        "xtquant_import": 0,
        "gateway_start": 0,
        "gateway_socket_open": 0,
        "account_raw_query": 0,
        "raw_positions_emit": 0,
        "submit_order": 0,
        "cancel_order": 0,
        "simulation": 0,
        "live": 0,
        "provider_fetch": 0,
        "lake_write": 0,
        "catalog_publish": 0,
    }
    return {
        "schema_version": "multifactor_strategy_admission_package_v1",
        "run_id": "research-run-fixture",
        "target_trade_date": "2026-06-25",
        "not_authorization": True,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "strategy_candidates": [
            {
                "strategy_id": "strategy_portfolio_alpha",
                "admission": "research_baseline",
                "target_symbols": ["000001.SZ", "000002.SZ"],
            }
        ],
        "strategy_scores": [
            {"strategy_id": "strategy_portfolio_alpha", "symbol": "000001.SZ", "alpha_score": 0.91},
            {"strategy_id": "strategy_portfolio_alpha", "symbol": "000002.SZ", "alpha_score": 0.77},
        ],
        "risk_cost_refs": {"risk_cost_summary_ref": "fixture:risk"},
        "operation_counts": counts,
    }


def _minimal_evidence() -> dict[str, object]:
    return {
        "schema_version": "runner-multifactor-simulation-operator-v1",
        "status": "pass",
        "run_id": "run-evidence",
        "authorization_ref": "",
        "runtime_authorization_granted": False,
        "small_live_or_live_authorized": False,
        "pre_positions": {"raw_payload_emitted": False, "redaction_status": "pass"},
        "target": {},
        "order_plan": {},
        "execution": {},
        "post_positions": {"raw_payload_emitted": False, "redaction_status": "pass"},
        "reconciliation": {},
        "stability_window": {},
        "persistence_policy": {
            "raw_payload_allowed": False,
            "broker_lake_write_allowed": False,
            "raw_account_allowed": False,
            "raw_symbol_allowed": False,
            "raw_broker_order_ref_allowed": False,
        },
        "redaction_policy": {
            "raw_payload_saved": False,
            "raw_account_saved": False,
            "raw_symbol_saved": False,
            "raw_broker_order_ref_saved": False,
            "secret_or_token_saved": False,
            "fund_detail_saved": False,
        },
    }
