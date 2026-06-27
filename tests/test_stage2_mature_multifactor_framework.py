from __future__ import annotations

import json
from pathlib import Path

from engine.mature_multifactor_framework import (
    MF_STAGE2_NO_LAKE_VIOLATION,
    MF_STAGE2_REQUIRED_FIELD_MISSING,
    MATURE_ADMISSION_SUPPORT_SCHEMA,
    SIGNAL_SET_SCHEMA,
    STAGE2_DATA_REQUIREMENTS,
    STAGE2_MATURE_FRAMEWORK_BUNDLE_SCHEMA,
    STAGE3_REQUIRED_EVIDENCE,
    STAGE3_RESEARCH_MACHINE_HANDOFF_SCHEMA,
    STRATEGY_CANDIDATE_SCHEMA,
    StrategyFamily,
    build_mature_admission_support_from_cr030_cr039_outputs,
    build_multifactor_strategy_type_adapter,
    build_project_strategy_candidate_from_cr039,
    build_stage3_research_machine_handoff,
    build_stage2_mature_admission_support,
    build_stage2_portfolio_risk_policy,
    build_stage2_research_evidence_index,
    build_stage2_signal_set,
    validate_project_strategy_candidate,
    validate_stage3_research_machine_handoff,
    validate_stage2_no_lake,
    validate_strategy_type_adapter,
)
from engine.multifactor_contracts import (
    BLOCKED_CLAIMS_DEFAULT,
    FactorDirection,
    FactorSpec,
    PermissionCounters,
)


def _fixture() -> dict[str, object]:
    path = Path("tests/fixtures/stage2_multifactor_framework/mature_multifactor_stage2_fixture.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _factor_spec() -> FactorSpec:
    return FactorSpec(
        factor_id="momentum_20d",
        name="Momentum 20D",
        version="stage2-v1",
        direction=FactorDirection.POSITIVE,
        input_fields=("close",),
        window=20,
        params={"lookback": 20},
        preprocessing={"winsorize": [0.01, 0.99], "zscore": True, "neutralize": "stage3_optional"},
        universe={"mode": "stage3_pit_required", "stage2_fixture": True},
        availability_policy={"available_at": "decision_time", "policy": "no_lookahead"},
        data_lineage={
            "source_dataset": "typed_unavailable:stage3_data_release",
            "research_input_schema": "research_input_v1",
            "evidence_refs": ["fixture://stage2/factor-spec/momentum_20d"],
        },
        blocked_claims=BLOCKED_CLAIMS_DEFAULT,
        failure_policy="fail_closed",
        auxiliary_requirements=("pit_universe", "quality_status", "industry_style_exposure"),
    )


def _stage2_objects() -> dict[str, object]:
    fixture = _fixture()
    return {
        "fixture": fixture,
        "adapter": build_multifactor_strategy_type_adapter(),
        "signal_set": build_stage2_signal_set(
            strategy_id=str(fixture["strategy_id"]),
            trade_date=str(fixture["trade_date"]),
            universe_ref=str(fixture["universe_ref"]),
            scores=fixture["scores"],  # type: ignore[arg-type]
            lineage_ref=str(fixture["lineage_ref"]),
            evidence_refs=fixture["evidence_refs"],  # type: ignore[arg-type]
        ),
        "evidence_index": build_stage2_research_evidence_index(
            index_id="stage2-evidence-index-fixture",
            run_manifest_ref="fixture://stage2/run-manifest-placeholder",
            metric_refs=fixture["metric_refs"],  # type: ignore[arg-type]
        ),
        "risk_policy": build_stage2_portfolio_risk_policy(
            policy_id="stage2-risk-policy-fixture",
            top_n=50,
            max_weight=0.03,
            turnover_limit=0.25,
        ),
    }


def test_stage2_01_builds_no_lake_framework_ready_mature_admission_support() -> None:
    fixture = _fixture()
    adapter = build_multifactor_strategy_type_adapter()
    signal_set = build_stage2_signal_set(
        strategy_id=str(fixture["strategy_id"]),
        trade_date=str(fixture["trade_date"]),
        universe_ref=str(fixture["universe_ref"]),
        scores=fixture["scores"],  # type: ignore[arg-type]
        lineage_ref=str(fixture["lineage_ref"]),
        evidence_refs=fixture["evidence_refs"],  # type: ignore[arg-type]
    )
    evidence_index = build_stage2_research_evidence_index(
        index_id="stage2-evidence-index-fixture",
        run_manifest_ref="fixture://stage2/run-manifest-placeholder",
        metric_refs=fixture["metric_refs"],  # type: ignore[arg-type]
    )
    risk_policy = build_stage2_portfolio_risk_policy(
        policy_id="stage2-risk-policy-fixture",
        top_n=50,
        max_weight=0.03,
        turnover_limit=0.25,
    )

    support = build_stage2_mature_admission_support(
        strategy_id=str(fixture["strategy_id"]),
        adapter=adapter,
        factor_specs=(_factor_spec(),),
        signal_set=signal_set,
        evidence_index=evidence_index,
        risk_policy=risk_policy,
    )
    payload = support.to_dict()

    assert signal_set.schema_version == SIGNAL_SET_SCHEMA
    assert support.schema_version == MATURE_ADMISSION_SUPPORT_SCHEMA
    assert support.status == "stage2_framework_ready"
    assert support.stage2_no_lake is True
    assert support.not_runtime_authorization is True
    assert support.not_simulation_authorization is True
    assert support.not_live_authorization is True
    assert support.blocked_reasons == ()
    assert {item.required_stage for item in support.typed_unavailable} == {"Stage 3"}
    assert "pit_universe" in support.stage3_data_requirements
    assert "stage2_no_lake_framework_support_only" in support.limitations
    assert payload["adapter_ref"]["adapter_id"] == "adapter:multifactor:stage2"
    json.dumps(payload, sort_keys=True)


def test_stage2_02_typed_unavailable_is_structured_for_real_data_gaps() -> None:
    signal_set = build_stage2_signal_set(
        strategy_id="stage2-mf",
        trade_date="2026-06-26",
        universe_ref="typed_unavailable:stage3_pit_universe",
        scores={"000300.SH": 0.1},
        lineage_ref="fixture://stage2/lineage",
        evidence_refs=("fixture://stage2/signal",),
    )
    evidence_index = build_stage2_research_evidence_index(
        index_id="stage2-index",
        run_manifest_ref="fixture://stage2/manifest",
    )

    assert signal_set.typed_unavailable[0].code == "stage3_pit_universe_required"
    assert "pit_universe" in signal_set.typed_unavailable[0].missing_inputs
    assert evidence_index.typed_unavailable[0].code == "stage3_real_data_lineage_required"
    assert "data_release_ref" in evidence_index.typed_unavailable[0].missing_inputs
    assert evidence_index.not_data_lake_write is True
    assert evidence_index.not_catalog_publish is True


def test_stage2_03_no_lake_boundary_blocks_provider_lake_qmt_runtime_and_credentials() -> None:
    result = validate_stage2_no_lake(
        PermissionCounters(
            provider_fetch=1,
            lake_write=1,
            catalog_publish=1,
            qmt_operation=1,
            simulation_or_live=1,
            credential_read=1,
        )
    )

    assert result.status == "blocked"
    assert {reason.code for reason in result.blocked_reasons} == {MF_STAGE2_NO_LAKE_VIOLATION}
    assert {
        "permission_counters.provider_fetch",
        "permission_counters.lake_write",
        "permission_counters.catalog_publish",
        "permission_counters.qmt_operation",
        "permission_counters.simulation_or_live",
        "permission_counters.credential_read",
    } <= {reason.field for reason in result.blocked_reasons}


def test_stage2_04_adapter_contract_prevents_event_or_ml_direct_bypass() -> None:
    adapter = build_multifactor_strategy_type_adapter().to_dict()
    adapter["strategy_family"] = StrategyFamily.MACHINE_LEARNING.value
    adapter["output_contract"] = {"signal_set": "signal_set_v1"}
    result = validate_strategy_type_adapter(adapter)

    assert result.status == "blocked"
    assert MF_STAGE2_REQUIRED_FIELD_MISSING in {reason.code for reason in result.blocked_reasons}
    assert "strategy_family" in {reason.field for reason in result.blocked_reasons}
    assert {
        "output_contract.strategy_candidate",
        "output_contract.research_evidence_index",
        "output_contract.mature_admission_support",
    } <= {reason.field for reason in result.blocked_reasons}


def test_stage2_05_forbidden_runtime_imports_are_absent() -> None:
    source = Path("engine/mature_multifactor_framework.py").read_text(encoding="utf-8").lower()

    assert "import xtquant" not in source
    assert "from xtquant" not in source
    assert "requests." not in source
    assert "urllib" not in source
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "popen" not in source
    assert "git clone" not in source
    assert "pip install" not in source
    assert "uv add" not in source
    assert ".env" not in source


def test_stage2_06_cr039_candidate_unifies_to_project_strategy_candidate() -> None:
    objects = _stage2_objects()
    fixture = objects["fixture"]  # type: ignore[assignment]
    candidate = build_project_strategy_candidate_from_cr039(
        cr039_candidate=fixture["cr039_candidate"],  # type: ignore[index]
        signal_set=objects["signal_set"],  # type: ignore[arg-type]
        evidence_index=objects["evidence_index"],  # type: ignore[arg-type]
        risk_policy=objects["risk_policy"],  # type: ignore[arg-type]
        source_run_id="run-cr039-stage2-fixture",
        source_admission_package_ref="fixture://cr039/admission-package",
    )
    payload = candidate.to_dict()

    assert candidate.schema_version == STRATEGY_CANDIDATE_SCHEMA
    assert candidate.strategy_family == StrategyFamily.MULTIFACTOR
    assert candidate.admission == "research_baseline"
    assert candidate.research_status == "stage2_research_candidate_ready"
    assert candidate.source_contract["schema_version"] == "multifactor_strategy_admission_package_v1"
    assert candidate.source_contract["cr030_bridge_schema_version"] == "strategy_admission_package_v1"
    assert candidate.signal_set_ref["schema_version"] == SIGNAL_SET_SCHEMA
    assert candidate.evidence_index_ref["schema_version"] == "research_evidence_index_v1"
    assert candidate.portfolio_risk_policy_ref["schema_version"] == "portfolio_risk_policy_v1"
    assert candidate.not_runtime_authorization is True
    assert candidate.not_simulation_authorization is True
    assert candidate.not_live_authorization is True
    assert validate_project_strategy_candidate(candidate).passed
    json.dumps(payload, sort_keys=True)


def test_stage2_07_builds_bundle_from_cr030_cr039_outputs() -> None:
    objects = _stage2_objects()
    fixture = objects["fixture"]  # type: ignore[assignment]
    bundle = build_mature_admission_support_from_cr030_cr039_outputs(
        strategy_id=str(fixture["strategy_id"]),  # type: ignore[index]
        factor_specs=(_factor_spec(),),
        cr039_candidate=fixture["cr039_candidate"],  # type: ignore[index]
        signal_set=objects["signal_set"],  # type: ignore[arg-type]
        evidence_index=objects["evidence_index"],  # type: ignore[arg-type]
        risk_policy=objects["risk_policy"],  # type: ignore[arg-type]
        adapter=objects["adapter"],  # type: ignore[arg-type]
        cr030_admission_package_ref="fixture://cr030/strategy-admission-package",
        cr039_run_id="run-cr039-stage2-fixture",
        cr039_admission_package_ref="fixture://cr039/admission-package",
    )
    payload = bundle.to_dict()

    assert bundle.schema_version == STAGE2_MATURE_FRAMEWORK_BUNDLE_SCHEMA
    assert bundle.status == "stage2_to_stage3_handoff_ready"
    assert bundle.stage2_no_lake is True
    assert bundle.not_runtime_authorization is True
    assert bundle.cr030_refs["schema_version"] == "strategy_admission_package_v1"
    assert bundle.cr039_refs["schema_version"] == "multifactor_strategy_admission_package_v1"
    assert payload["mature_admission_support"]["schema_version"] == MATURE_ADMISSION_SUPPORT_SCHEMA
    assert payload["strategy_candidate"]["schema_version"] == STRATEGY_CANDIDATE_SCHEMA
    assert payload["stage3_research_machine_handoff"]["schema_version"] == STAGE3_RESEARCH_MACHINE_HANDOFF_SCHEMA
    assert payload["stage3_research_machine_handoff"]["status"] == "ready_for_stage3_research_machine"
    json.dumps(payload, sort_keys=True)


def test_stage2_08_stage3_handoff_lists_research_machine_inputs_and_evidence() -> None:
    objects = _stage2_objects()
    fixture = objects["fixture"]  # type: ignore[assignment]
    support = build_stage2_mature_admission_support(
        strategy_id=str(fixture["strategy_id"]),  # type: ignore[index]
        adapter=objects["adapter"],  # type: ignore[arg-type]
        factor_specs=(_factor_spec(),),
        signal_set=objects["signal_set"],  # type: ignore[arg-type]
        evidence_index=objects["evidence_index"],  # type: ignore[arg-type]
        risk_policy=objects["risk_policy"],  # type: ignore[arg-type]
    )
    candidate = build_project_strategy_candidate_from_cr039(
        cr039_candidate=fixture["cr039_candidate"],  # type: ignore[index]
        signal_set=objects["signal_set"],  # type: ignore[arg-type]
        evidence_index=objects["evidence_index"],  # type: ignore[arg-type]
        risk_policy=objects["risk_policy"],  # type: ignore[arg-type]
    )

    handoff = build_stage3_research_machine_handoff(
        strategy_id=str(fixture["strategy_id"]),  # type: ignore[index]
        mature_admission_support=support,
        strategy_candidate=candidate,
        evidence_index=objects["evidence_index"],  # type: ignore[arg-type]
        risk_policy=objects["risk_policy"],  # type: ignore[arg-type]
    )
    payload = handoff.to_dict()

    assert handoff.schema_version == STAGE3_RESEARCH_MACHINE_HANDOFF_SCHEMA
    assert handoff.status == "ready_for_stage3_research_machine"
    assert set(STAGE2_DATA_REQUIREMENTS) <= set(handoff.required_inputs)
    assert set(STAGE3_REQUIRED_EVIDENCE) <= set(handoff.required_evidence)
    assert "factor_panel_ref" in handoff.required_evidence
    assert "label_window_ref" in handoff.required_evidence
    assert "mature_strategy_admission_package_ref" in handoff.required_evidence
    assert "runner_offline_preflight_ref" in handoff.required_evidence
    assert payload["data_lake_requirements"]["environment"] == "research_machine"
    assert payload["execution_boundary"]["not_gateway_or_qmt_operation"] is True
    assert payload["execution_boundary"]["not_order_generation"] is True
    assert validate_stage3_research_machine_handoff(handoff).passed
    json.dumps(payload, sort_keys=True)
