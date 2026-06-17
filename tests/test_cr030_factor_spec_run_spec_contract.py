from __future__ import annotations

import json

from engine.multifactor_contracts import (
    BLOCKED_CLAIMS_DEFAULT,
    ContractValidationResult,
    FactorDirection,
    FactorRunSpec,
    FactorSpec,
    PermissionCounters,
    build_factor_run_hash_payload,
    compute_config_hash,
    map_legacy_factor_definition,
    validate_factor_run_spec,
    validate_factor_spec,
)


def _reason_codes(result: ContractValidationResult) -> set[str]:
    return {reason.code for reason in result.blocked_reasons}


def _valid_factor_spec() -> FactorSpec:
    return FactorSpec(
        factor_id="momentum_20d",
        name="Momentum 20D",
        version="v1",
        direction=FactorDirection.POSITIVE,
        input_fields=("close",),
        window=20,
        params={"lookback": 20},
        preprocessing={"winsorize": [0.01, 0.99], "zscore": True},
        universe={"mode": "research_input_v1", "pit_policy": "pit_required"},
        availability_policy={"available_at": "decision_time", "policy": "no_lookahead"},
        data_lineage={
            "source_dataset": "research_input_v1",
            "research_input_schema": "research_input_v1",
            "evidence_refs": ["experiments/run_experiment_17_21_factor_suite.py:FactorDefinition"],
        },
        blocked_claims=BLOCKED_CLAIMS_DEFAULT,
        failure_policy="fail_closed",
        auxiliary_requirements=("pit_universe", "quality_status"),
        external_mapping_notes=(
            {
                "external_project": "Qlib",
                "external_object": "Alpha158 feature config",
                "internal_field": "FactorSpec",
                "mapping_role": "cross_check_only",
            },
        ),
    )


def _run_spec_with_hash(factor_spec: FactorSpec, **overrides: object) -> FactorRunSpec:
    base = {
        "run_id": "run-cr030-s02-fixture",
        "factor_id": factor_spec.factor_id,
        "factor_version": factor_spec.version,
        "date_range": {"start": "2019-01-01", "end": "2024-12-31"},
        "dataset_release": "research_input_v1_fixture_release",
        "benchmark": {"benchmark_id": "hs300", "policy": "hs300_required"},
        "label_window": {"horizon": 20, "return_kind": "forward_return"},
        "cost_config": {"commission_bps": 3, "slippage_bps": 5},
        "seed": 42,
        "code_version": "cr030-s02-fixture",
        "config_hash": "",
        "output_root": "reports/cr030_s02_fixture",
        "permission_counters": PermissionCounters(),
        "failure_policy": "fail_closed",
        "combination_config": {"weighting_policy": "single_factor"},
    }
    base.update(overrides)
    hash_payload = build_factor_run_hash_payload(base, factor_spec)
    base["config_hash"] = compute_config_hash(hash_payload)
    return FactorRunSpec(**base)


def test_ts_s02_01_valid_factor_spec_and_run_spec_are_json_serializable() -> None:
    factor_spec = _valid_factor_spec()
    run_spec = _run_spec_with_hash(factor_spec)

    spec_result = validate_factor_spec(factor_spec)
    run_result = validate_factor_run_spec(run_spec, factor_spec)

    assert spec_result.status == "pass"
    assert spec_result.blocked_reasons == ()
    assert run_result.status == "pass"
    assert run_result.blocked_reasons == ()
    json.dumps(factor_spec.to_dict(), sort_keys=True)
    json.dumps(run_spec.to_dict(), sort_keys=True)
    json.dumps(spec_result.to_dict(), sort_keys=True)
    json.dumps(run_result.to_dict(), sort_keys=True)


def test_ts_s02_02_missing_fields_direction_lineage_and_release_fail_closed() -> None:
    missing_direction = _valid_factor_spec().to_dict()
    missing_direction.pop("direction")
    result = validate_factor_spec(missing_direction)
    assert result.status == "blocked"
    assert "MF_SCHEMA_REQUIRED_FIELD_MISSING" in _reason_codes(result)

    missing_lineage = _valid_factor_spec().to_dict()
    missing_lineage["data_lineage"] = {"source_dataset": "research_input_v1"}
    result = validate_factor_spec(missing_lineage)
    assert result.status == "blocked"
    assert "MF_LINEAGE_MISSING" in _reason_codes(result)

    bad_direction = _valid_factor_spec().to_dict()
    bad_direction["direction"] = "external_default"
    result = validate_factor_spec(bad_direction)
    assert result.status == "blocked"
    assert "MF_DIRECTION_INVALID" in _reason_codes(result)

    factor_spec = _valid_factor_spec()
    missing_release = _run_spec_with_hash(factor_spec).to_dict()
    missing_release["dataset_release"] = ""
    missing_release["config_hash"] = compute_config_hash(build_factor_run_hash_payload(missing_release, factor_spec))
    result = validate_factor_run_spec(missing_release, factor_spec)
    assert result.status == "blocked"
    assert "MF_SCHEMA_REQUIRED_FIELD_MISSING" in _reason_codes(result)


def test_ts_s02_03_config_hash_is_stable_and_detects_p0_changes() -> None:
    config_a = {
        "factor": {"factor_id": "momentum_20d", "version": "v1"},
        "data": {"dataset_release": "release-a", "date_range": {"start": "2019-01-01", "end": "2024-12-31"}},
        "label": {"horizon": 20},
        "cost": {"commission_bps": 3},
        "combination": {"weighting_policy": "single_factor"},
    }
    config_b = {
        "combination": {"weighting_policy": "single_factor"},
        "cost": {"commission_bps": 3},
        "label": {"horizon": 20},
        "data": {"date_range": {"end": "2024-12-31", "start": "2019-01-01"}, "dataset_release": "release-a"},
        "factor": {"version": "v1", "factor_id": "momentum_20d"},
    }
    config_changed = {
        **config_a,
        "cost": {"commission_bps": 5},
    }

    assert compute_config_hash(config_a) == compute_config_hash(config_b)
    assert compute_config_hash(config_a) != compute_config_hash(config_changed)

    factor_spec = _valid_factor_spec()
    run_spec = _run_spec_with_hash(factor_spec)
    tampered = run_spec.to_dict()
    tampered["cost_config"] = {"commission_bps": 99, "slippage_bps": 5}
    result = validate_factor_run_spec(tampered, factor_spec)
    assert result.status == "blocked"
    assert "MF_CONFIG_HASH_MISMATCH" in _reason_codes(result)

    missing_hash = run_spec.to_dict()
    missing_hash["config_hash"] = ""
    result = validate_factor_run_spec(missing_hash, factor_spec)
    assert result.status == "blocked"
    assert "MF_CONFIG_HASH_MISSING" in _reason_codes(result)


def test_ts_s02_04_external_objects_remain_cross_check_only_and_runtime_is_blocked() -> None:
    factor_spec = _valid_factor_spec().to_dict()
    factor_spec["source_of_truth"] = "Qlib Alpha158"
    result = validate_factor_spec(factor_spec)
    assert result.status == "blocked"
    assert "MF_EXTERNAL_RUNTIME_NOT_AUTHORIZED" in _reason_codes(result)

    cross_check_only = _valid_factor_spec().to_dict()
    cross_check_only["external_mapping_notes"] = [
        {
            "external_project": "Zipline Reloaded",
            "external_object": "Pipeline Factor",
            "internal_field": "input_fields",
            "mapping_role": "cross_check_only",
        }
    ]
    result = validate_factor_spec(cross_check_only)
    assert result.status == "pass"

    run_spec = _run_spec_with_hash(_valid_factor_spec()).to_dict()
    run_spec["provider"] = "Qlib provider_uri"
    run_spec["runner"] = "qrun"
    run_spec["optimizer"] = "vectorbt Portfolio optimizer"
    run_spec["permission_counters"] = {
        "external_project_run": 1,
        "provider_fetch": 1,
        "qmt_operation": 1,
        "credential_read": 1,
    }
    run_spec["config_hash"] = compute_config_hash(build_factor_run_hash_payload(run_spec, _valid_factor_spec()))

    result = validate_factor_run_spec(run_spec, _valid_factor_spec())
    assert result.status == "blocked"
    assert {
        "MF_EXTERNAL_RUNTIME_NOT_AUTHORIZED",
        "MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED",
        "MF_QMT_NOT_AUTHORIZED",
    } <= _reason_codes(result)
    assert result.permission_counters["external_project_run"] == 1
    assert result.permission_counters["provider_fetch"] == 1
    assert result.permission_counters["qmt_operation"] == 1
    assert result.permission_counters["credential_read"] == 1


def test_ts_s02_05_legacy_factor_definition_mapping_preserves_internal_truth() -> None:
    legacy = {
        "name": "rsi_14",
        "experiment": "experiment_17",
        "source": "14 日 RSI",
        "hypothesis": "低 RSI 可能超跌",
        "stage2_link": "实验七",
        "direction_sign": -1,
        "direction_note": "原始 RSI 越低越看多，预处理阶段乘以 -1 统一方向",
    }

    mapped = map_legacy_factor_definition(legacy)

    assert isinstance(mapped, FactorSpec)
    assert mapped.factor_id == "rsi_14"
    assert mapped.direction == FactorDirection.NEGATIVE
    assert mapped.source_of_truth == "project_multifactor_contract"
    assert mapped.data_lineage["source_dataset"] == "research_input_v1"
    assert mapped.external_mapping_notes[0].mapping_role == "cross_check_only"
    assert validate_factor_spec(mapped).status == "pass"

    unsupported = dict(legacy)
    unsupported["name"] = "unknown_external_alpha"
    result = map_legacy_factor_definition(unsupported)
    assert isinstance(result, ContractValidationResult)
    assert result.status == "blocked"
    assert "MF_SCHEMA_REQUIRED_FIELD_MISSING" in _reason_codes(result)
