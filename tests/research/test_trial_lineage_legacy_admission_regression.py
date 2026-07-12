from __future__ import annotations

import pytest

from engine.cross_strategy_reliability_gates import GATE_IDS
from engine.daily_multifactor_baseline_artifact import (
    ArtifactStatus,
    BaselineValidationSummary,
    DailyMultifactorBaselineArtifact,
    GateDecision,
    build_claim_boundary,
    compose_admission_package,
    derive_paper_candidate,
)
from engine.strategy_admission_package import attach_family_lineage_to_admission_package


def _synthetic_cr155_dict() -> dict[str, object]:
    return {
        "package_id": "synthetic-cr155",
        "package_status": "PASS",
        "admission_status": "pass",
        "paper_candidate": True,
        "evidence_refs": (), "blocked_reasons": (), "limitations": (),
        "not_authorized_counters": {},
        "not_qmt_authorization": True, "not_simulation_authorization": True,
        "not_live_authorization": True, "not_broker_order": True,
    }


def _actual_cr155_contract_object():
    artifact = DailyMultifactorBaselineArtifact(
        strategy_id="cr155-daily-multifactor",
        universe_ref="fixture://cr155/universe",
        factor_specs=({"factor_id": "momentum", "weight": 1.0, "version_ref": "fixture://factor/v1"},),
        signal_spec={"ranking": "rank", "standardization": "zscore", "lag_policy": "t_plus_1"},
        portfolio_policy={
            "rebalance": "daily", "weighting": "equal", "cost_ref": "fixture://cost",
            "slippage_ref": "fixture://slippage",
        },
        validation_refs={"historical_backtest_ref": "fixture://backtest", "walk_forward_ref": "fixture://wf"},
        admission_refs={"statistical_gate_ref": "fixture://stat", "reliability_gate_ref": "fixture://reliability"},
        claim_boundary=build_claim_boundary("cr155-daily-multifactor"),
        rerun_refs={"run_a": "fixture://run/a", "run_b": "fixture://run/b"},
        evidence_refs=("fixture://cr155/artifact",),
    )
    validation = BaselineValidationSummary(
        status=ArtifactStatus.PASS,
        artifact_status=ArtifactStatus.PASS,
        provenance_status=ArtifactStatus.PASS,
        split_manifest_status=ArtifactStatus.PASS,
        historical_backtest_ref={"run_ref": "fixture://backtest"},
        split_manifest={"manifest_ref": "fixture://wf"},
        metrics={"total_return": 0.1},
        real_data_claim_allowed=True,
        evidence_refs=("fixture://cr155/validation",),
    )
    return compose_admission_package(
        artifact,
        validation,
        GateDecision(ArtifactStatus.PASS, gate_ref="fixture://stat"),
        GateDecision(ArtifactStatus.PASS, gate_ref="fixture://reliability"),
    )


@pytest.mark.parametrize("package_factory", (_synthetic_cr155_dict, _actual_cr155_contract_object))
def test_actual_and_synthetic_cr155_without_native_ledger_stay_blocked(package_factory) -> None:
    attached = attach_family_lineage_to_admission_package(package_factory(), None)
    candidate, _ = derive_paper_candidate(attached)
    projection = attached["family_lineage_projection"]

    assert attached.get("package_status", attached.get("admission_status")).lower() == "blocked"
    assert attached["paper_candidate"] is False
    assert candidate is False
    assert projection["availability"] == "typed_unavailable"
    assert projection["raw_trial_count"] is None
    assert projection["effective_trial_count_availability"] == "typed_unavailable"
    assert projection["effective_trial_count"] is None
    assert projection["effective_ref"] == projection["effective_method"] == ""
    assert projection["c1_input_status"] == "input_blocked"
    assert attached.get("historical_backfill_count", 0) == 0
    assert attached.get("historical_family_reconstruction_count", 0) == 0
    assert attached.get("historical_trial_reconstruction_count", 0) == 0
    assert all(value == 0 for value in attached.get("not_authorized_counters", {}).values())
    assert all(attached[field] is True for field in (
        "not_qmt_authorization", "not_simulation_authorization", "not_live_authorization", "not_broker_order"
    ))


def test_cr155_lineage_does_not_add_gate_or_runtime_statistical_claim() -> None:
    attached = attach_family_lineage_to_admission_package(_actual_cr155_contract_object(), None)
    projection = attached["family_lineage_projection"]
    assert len(GATE_IDS) == 6
    assert all("lineage" not in gate_id.lower() for gate_id in GATE_IDS)
    assert projection["effective_trial_count"] is None
    assert projection["c1_input_status"] == "input_blocked"
    assert attached["paper_candidate"] is False
    assert attached["not_simulation_authorization"] is True
    assert attached["not_live_authorization"] is True
    assert attached["not_broker_order"] is True
