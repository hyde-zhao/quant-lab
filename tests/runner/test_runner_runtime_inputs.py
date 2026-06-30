from __future__ import annotations

import json
from pathlib import Path

from trading.strategy_runner.runtime_inputs import build_runtime_inputs, write_runtime_inputs


def test_runtime_inputs_remap_formal_fixture_package_to_private_runtime_symbols(
    tmp_path: Path,
) -> None:
    base_spec = _base_spec()
    admission = _admission_package()
    overlay = {
        "schema_version": "runner-multifactor-runtime-overlay-v1",
        "symbol_map": {
            "INSTRUMENT_FIXTURE_A": "000001.SZ",
            "INSTRUMENT_FIXTURE_B": "000002.SZ",
        },
        "current_positions": {"000001.SZ": 0, "000002.SZ": 0},
        "risk_snapshot": {
            "cash_available": "20000",
            "positions_available": {"000001.SZ": 0, "000002.SZ": 0},
            "t1_sellable": {"000001.SZ": 0, "000002.SZ": 0},
            "raw_price_refs": {
                "000001.SZ": {"price": "10", "evidence_ref": "private:price-a"},
                "000002.SZ": {"price": "20", "evidence_ref": "private:price-b"},
            },
            "source_kind": "sanitized_snapshot",
            "evidence_ref": "process/evidence/readonly-r3.json",
        },
        "stability_evidence_refs": [
            "process/evidence/runtime-pass-1/operator-evidence.index.json",
            "process/evidence/runtime-pass-2/operator-evidence.index.json",
        ],
    }

    inputs = build_runtime_inputs(
        base_spec=base_spec,
        admission_package=admission,
        overlay=overlay,
        readonly_evidence_ref="process/evidence/readonly-r3.json",
        run_id="runner-qmt-simulation-multifactor-r3",
        authorization_ref="runtime-auth-r3",
        expected_runtime_profile="cr138-simulation",
    )
    spec_path, admission_path = write_runtime_inputs(
        inputs,
        output_dir=tmp_path,
        run_id="runner-qmt-simulation-multifactor-r3",
    )

    rendered = spec_path.read_text(encoding="utf-8") + admission_path.read_text(
        encoding="utf-8"
    )
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    runtime_admission = json.loads(admission_path.read_text(encoding="utf-8"))

    assert "INSTRUMENT_FIXTURE" not in rendered
    assert spec["current_positions"] == {"000001.SZ": 0, "000002.SZ": 0}
    assert spec["risk_snapshot"]["raw_price_refs"]["000001.SZ"]["price"] == "10"
    assert spec["strategy_admission_package"]["strategy_scores"][0]["symbol"] == "000001.SZ"
    assert runtime_admission["strategy_candidates"][0]["target_symbols"] == [
        "000001.SZ",
        "000002.SZ",
    ]
    assert spec["stability_evidence_refs"] == [
        "process/evidence/runtime-pass-1/operator-evidence.index.json",
        "process/evidence/runtime-pass-2/operator-evidence.index.json",
    ]
    assert inputs.to_summary()["raw_symbols_printed"] is False


def test_runtime_inputs_fail_when_symbol_map_leaves_fixture_symbol() -> None:
    overlay = {
        "symbol_map": {
            "INSTRUMENT_FIXTURE_A": "000001.SZ",
            "INSTRUMENT_FIXTURE_B": "INSTRUMENT_FIXTURE_B",
        }
    }

    try:
        build_runtime_inputs(
            base_spec=_base_spec(),
            admission_package=_admission_package(),
            overlay=overlay,
            readonly_evidence_ref="process/evidence/readonly-r3.json",
            run_id="runner-qmt-simulation-multifactor-r3",
            authorization_ref="runtime-auth-r3",
            expected_runtime_profile="cr138-simulation",
        )
    except ValueError as exc:
        assert "runtime_symbol_unmapped" in str(exc)
    else:  # pragma: no cover - explicit failure path for readability
        raise AssertionError("fixture symbol must be blocked")


def _base_spec() -> dict[str, object]:
    return {
        "schema_version": "runner-multifactor-simulation-operator-v1",
        "strategy_id": "strategy_runner_multifactor_formal_fixture",
        "run_id": "runner-qmt-simulation-multifactor-formal-non-trading",
        "target_trade_date": "2026-06-26",
        "authorization_ref": "",
        "expected_runtime_profile": "cr138-simulation",
        "top_n": 1,
        "weighting": "equal",
        "capital_base": "10000",
        "current_positions": {"INSTRUMENT_FIXTURE_A": 0, "INSTRUMENT_FIXTURE_B": 0},
        "risk_snapshot": {
            "cash_available": "20000",
            "positions_available": {
                "INSTRUMENT_FIXTURE_A": 0,
                "INSTRUMENT_FIXTURE_B": 0,
            },
            "t1_sellable": {
                "INSTRUMENT_FIXTURE_A": 0,
                "INSTRUMENT_FIXTURE_B": 0,
            },
            "raw_price_refs": {
                "INSTRUMENT_FIXTURE_A": {"price": "10", "evidence_ref": "fixture:a"},
                "INSTRUMENT_FIXTURE_B": {"price": "20", "evidence_ref": "fixture:b"},
            },
            "source_kind": "sanitized_snapshot",
            "evidence_ref": "fixture:risk-snapshot",
        },
        "risk_profile": {
            "risk_profile_id": "risk-profile-runner-qmt-simulation-formal-fixture",
            "max_single_symbol_notional": "20000",
            "max_portfolio_notional": "20000",
            "lot_size": 100,
        },
        "cancel_submitted_after_submit": True,
    }


def _admission_package() -> dict[str, object]:
    return {
        "schema_version": "multifactor_strategy_admission_package_v1",
        "run_id": "research-run-runner-qmt-simulation-multifactor-formal",
        "target_trade_date": "2026-06-26",
        "signal_date": "2026-06-26",
        "not_authorization": True,
        "not_qmt_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "operation_counts": {
            "provider_fetch": 0,
            "lake_write": 0,
            "catalog_publish": 0,
            "qmt_operation": 0,
            "simulation": 0,
            "live": 0,
            "credential_read": 0,
            "account_raw_query": 0,
            "raw_positions_emit": 0,
            "gateway_start": 0,
            "gateway_socket_open": 0,
            "qmt_start": 0,
            "miniqmt_start": 0,
            "cancel_order": 0,
            "nas_read": 0,
            "nas_write": 0,
            "nas_list": 0,
            "nas_copy": 0,
            "nas_pull": 0,
            "nas_publish": 0,
        },
        "risk_cost_refs": {"risk_profile_ref": "fixture:risk"},
        "strategy_candidates": [
            {
                "strategy_id": "strategy_runner_multifactor_formal_fixture",
                "admission": "pass",
                "target_symbols": ["INSTRUMENT_FIXTURE_A", "INSTRUMENT_FIXTURE_B"],
            }
        ],
        "strategy_scores": [
            {
                "strategy_id": "strategy_runner_multifactor_formal_fixture",
                "symbol": "INSTRUMENT_FIXTURE_A",
                "alpha_score": "0.8",
            },
            {
                "strategy_id": "strategy_runner_multifactor_formal_fixture",
                "symbol": "INSTRUMENT_FIXTURE_B",
                "alpha_score": "0.2",
            },
        ],
    }
