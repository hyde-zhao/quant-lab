"""CR-173 S03：golden、failure、完整性与恢复契约验证。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

import engine.effective_trial_estimator as estimator_module
from engine.effective_trial_evidence import (
    ATTEMPT_BASIS_SCHEMA,
    EVIDENCE_SCHEMA,
    AttemptAuditLog,
    CanonicalNumberToken,
    DependencyMatrixEnvelope,
    EffectiveTrialEvidence,
    EffectiveTrialMethodSpec,
    EvidenceContractError,
    EvidenceStatus,
    FrozenMapping,
    SealedTrialIdentity,
    build_approved_method_spec,
    build_attempt_audit,
    build_effective_trial_evidence,
    build_failure_attempt_basis,
    canonical_bytes,
    canonical_component_digest,
    canonical_dependency_input_hash,
    canonical_evidence_bytes,
    canonical_evidence_hash,
    canonical_sealed_identity_hash,
)


FIXTURE_PATH = (
    Path(__file__).parents[1]
    / "fixtures"
    / "effective_trial"
    / "golden_vectors_v1.json"
)
FIXTURE_SCHEMA = "quant-lab.effective-trial-golden-vectors.v1"
RUN_REF = "cr173-s03-fixture-run-v1"
ZERO_HASH = "sha256:" + "0" * 64


def _plain(value: Any) -> Any:
    if isinstance(value, CanonicalNumberToken):
        return value.value
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


def _load_fixture() -> dict[str, Any]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["fixture_schema_version"] == FIXTURE_SCHEMA
    assert payload["canonical_domain"] == "synthetic-declared-exact-only"
    assert len(payload["cases"]) == 6
    assert {case["case_id"] for case in payload["cases"]} == {
        f"GV-ET-{index:02d}" for index in range(1, 7)
    }
    return payload


def _split_case(case: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = {
        key: deepcopy(value)
        for key, value in case.items()
        if not key.startswith("expected_")
    }
    expected = {
        key: deepcopy(value)
        for key, value in case.items()
        if key.startswith("expected_")
    }
    assert set(raw).isdisjoint(expected)
    return raw, expected


def _components(
    raw: Mapping[str, Any],
) -> tuple[SealedTrialIdentity, DependencyMatrixEnvelope, EffectiveTrialMethodSpec]:
    trial_ids = tuple(raw["ordered_trial_ids"])
    identity = SealedTrialIdentity(
        sealed_family_ref=raw["sealed_family_ref"],
        sealed_family_hash=raw["sealed_family_hash"],
        raw_trial_count=raw["raw_trial_count"],
        ordered_trial_ids=trial_ids,
    )
    input_hash = raw["input_hash"]
    if raw["integrity_injection"] == "input_hash_mismatch":
        input_hash = ZERO_HASH
    dependency = DependencyMatrixEnvelope(
        schema_version=raw["schema_version"],
        ordered_trial_ids=trial_ids,
        matrix_tokens=tuple(tuple(row) for row in raw["matrix_tokens"]),
        input_hash=input_hash,
        input_lineage_ref=raw["input_lineage_ref"],
        source_mode=raw["source_mode"],
    )
    return identity, dependency, build_approved_method_spec()


def _execute_raw(
    raw: Mapping[str, Any],
    *,
    attempt_ordinal: int,
) -> tuple[estimator_module.ExactEstimatorExecution, Any]:
    identity, dependency, method = _components(raw)
    execution = estimator_module.estimate_effective_trial(identity, dependency, method)
    audit = build_attempt_audit(
        verification_run_ref=RUN_REF,
        synthetic_case_id=raw["case_id"],
        attempt_ordinal=attempt_ordinal,
        evidence=execution.evidence,
    )
    return execution, audit


def _assert_fixture_oracle(
    execution: estimator_module.ExactEstimatorExecution,
    expected: Mapping[str, Any],
) -> None:
    outcome = execution.outcome
    assert outcome.state == expected["expected_state"]
    assert outcome.reason_code == expected["expected_reason"]
    actual_count = None if outcome.effective_trial_count is None else outcome.effective_trial_count.value
    assert actual_count == expected["expected_count_token"]
    oracle = expected.get("expected_basis_oracle")
    if oracle is not None:
        assert _plain(execution.attempt_basis.as_mapping()) == oracle


def _base_raw() -> dict[str, Any]:
    case = _load_fixture()["cases"][0]
    return _split_case(case)[0]


def _raw_with_matrix(tokens: list[list[str]]) -> dict[str, Any]:
    raw = _base_raw()
    raw["ordered_trial_ids"] = ["synthetic-trial-01", "synthetic-trial-02"]
    raw["raw_trial_count"] = 2
    raw["matrix_tokens"] = tokens
    raw["sealed_family_ref"] = "synthetic-family-failure"
    raw["input_lineage_ref"] = "synthetic-lineage-failure"
    raw["sealed_family_hash"] = canonical_sealed_identity_hash(
        raw["sealed_family_ref"], raw["raw_trial_count"], raw["ordered_trial_ids"]
    )
    raw["input_hash"] = canonical_dependency_input_hash(
        schema_version=raw["schema_version"],
        ordered_trial_ids=raw["ordered_trial_ids"],
        matrix_tokens=raw["matrix_tokens"],
        input_lineage_ref=raw["input_lineage_ref"],
        source_mode=raw["source_mode"],
    )
    raw["integrity_injection"] = "none"
    return raw


def _failure_execution(
    failure_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> estimator_module.ExactEstimatorExecution:
    raw = _raw_with_matrix([["1", "0"], ["0", "1"]])
    identity, dependency, method = _components(raw)
    if failure_id == "F01":
        identity = None
    elif failure_id == "F02":
        dependency = None
    elif failure_id == "F03":
        raw = _raw_with_matrix([["1", "NaN"], ["NaN", "1"]])
        identity, dependency, method = _components(raw)
    elif failure_id == "F04":
        raw = _raw_with_matrix([["1", "1"], ["1", "-1"]])
        identity, dependency, method = _components(raw)
    elif failure_id == "F05":
        method = None
    elif failure_id == "F06":
        dependency = DependencyMatrixEnvelope(
            schema_version=dependency.schema_version,
            ordered_trial_ids=dependency.ordered_trial_ids,
            matrix_tokens=dependency.matrix_tokens,
            input_hash=ZERO_HASH,
            input_lineage_ref=dependency.input_lineage_ref,
            source_mode=dependency.source_mode,
        )
    elif failure_id == "F07":
        method = EffectiveTrialMethodSpec(
            method_id=method.method_id,
            method_version=method.method_version,
            method_hash=ZERO_HASH,
            canonical_spec_descriptor=method.canonical_spec_descriptor,
        )
    elif failure_id == "F08":
        def _raise_invariant(*args: Any, **kwargs: Any) -> CanonicalNumberToken:
            raise EvidenceContractError("S03 注入 evidence invariant mismatch")

        monkeypatch.setattr(estimator_module, "quantize_and_validate_count", _raise_invariant)
    else:  # pragma: no cover - 参数集由测试自身冻结
        raise AssertionError(f"未知 failure: {failure_id}")
    execution = estimator_module.estimate_effective_trial(identity, dependency, method)
    if failure_id != "F08":
        return execution
    attempted_digest = canonical_component_digest(
        FrozenMapping(
            {
                "attempted_evidence_state": "invariant_mismatch",
                "source": "S03-F08-injection",
            }
        )
    )
    finalized_basis = build_failure_attempt_basis(
        execution.validation,
        attempted_evidence_digest=attempted_digest,
    )
    finalized_evidence = build_effective_trial_evidence(
        attempt_basis=finalized_basis,
        method_spec=method,
        input_lineage_ref=dependency.input_lineage_ref,
    )
    return estimator_module.ExactEstimatorExecution(
        validation=execution.validation,
        outcome=execution.outcome,
        attempt_basis=finalized_basis,
        evidence=finalized_evidence,
        exact_count=None,
        psd_proof=execution.psd_proof,
    )


def _assert_trusted_serialized_evidence(
    candidate: Mapping[str, Any],
    trusted: EffectiveTrialEvidence,
) -> None:
    canonical_evidence_bytes(candidate)
    if canonical_bytes(candidate) != canonical_evidence_bytes(trusted):
        raise EvidenceContractError("serialized evidence 与 trusted builder output 不一致")


def test_fixture_schema_and_raw_expected_views_are_isolated() -> None:
    payload = _load_fixture()
    assert payload["method"]["method_hash"] == build_approved_method_spec().method_hash
    for case in payload["cases"]:
        raw, expected = _split_case(case)
        assert raw["repeat_count"] == 3
        assert raw["source_mode"] == "declared_exact"
        assert raw["raw_trial_count"] == len(raw["ordered_trial_ids"])
        assert raw["sealed_family_hash"] == canonical_sealed_identity_hash(
            raw["sealed_family_ref"], raw["raw_trial_count"], raw["ordered_trial_ids"]
        )
        assert raw["input_hash"] == canonical_dependency_input_hash(
            schema_version=raw["schema_version"],
            ordered_trial_ids=raw["ordered_trial_ids"],
            matrix_tokens=raw["matrix_tokens"],
            input_lineage_ref=raw["input_lineage_ref"],
            source_mode=raw["source_mode"],
        )
        serialized = json.dumps(raw, sort_keys=True)
        assert "strategy" not in serialized.lower()
        assert "real" not in serialized.lower()
        assert set(expected) >= {
            "expected_state",
            "expected_reason",
            "expected_count_token",
        }


@pytest.mark.parametrize("case_index", range(6))
def test_golden_vectors_repeat_three_with_one_stable_result_and_three_audits(
    case_index: int,
) -> None:
    case = _load_fixture()["cases"][case_index]
    raw, expected = _split_case(case)
    returned = [_execute_raw(raw, attempt_ordinal=index) for index in range(1, 4)]
    executions = [item[0] for item in returned]
    audits = [item[1] for item in returned]

    for execution in executions:
        _assert_fixture_oracle(execution, expected)
        assert set(execution.attempt_basis.presence_bitmap) == {
            "sealed_identity",
            "dependency_matrix",
            "method_spec",
        }
        assert set(execution.evidence.as_mapping()) == set(EVIDENCE_SCHEMA)
    assert len({item.evidence.effective_trial_computation_ref for item in executions}) == 1
    assert len({canonical_evidence_hash(item.evidence) for item in executions}) == 1
    assert len({item.attempt_audit_ref for item in audits}) == 3
    assert all(
        audit.effective_trial_computation_ref
        == executions[0].evidence.effective_trial_computation_ref
        and audit.canonical_evidence_hash == canonical_evidence_hash(executions[0].evidence)
        for audit in audits
    )
    assert AttemptAuditLog().append(audits[0]).append(audits[1]).append(audits[2]).entries == tuple(audits)


@pytest.mark.parametrize("failure_id", [f"F{index:02d}" for index in range(1, 9)])
def test_failure_matrix_returns_complete_fail_closed_basis(
    failure_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = _failure_execution(failure_id, monkeypatch)
    basis = execution.attempt_basis
    assert execution.outcome.state != "present"
    assert execution.outcome.effective_trial_count is None
    assert basis.primary_failure_id == failure_id
    assert basis.basis_schema == ATTEMPT_BASIS_SCHEMA
    assert len(basis.as_mapping()) == 7
    assert len(basis.presence_bitmap) == 3
    assert "attempted_evidence" not in basis.presence_bitmap
    assert set(basis.component_snapshot_digests) == {
        "sealed_identity",
        "dependency_matrix",
        "method_spec",
        "attempted_evidence",
    }
    assert set(basis.validated_refs) == {"input_lineage_ref", "method_hash"}
    oracle_by_id = {
        item["failure_id"]: item
        for item in _load_fixture()["failure_basis_oracles"]
    }
    if oracle_by_id:
        assert _plain(basis.as_mapping()) == oracle_by_id[failure_id]["expected_basis_oracle"]


def test_noncanonical_token_stops_before_matrix_domain_and_estimator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _load_fixture()["cases"][4]
    raw, _ = _split_case(case)
    calls = 0
    original = estimator_module.validate_exact_matrix_domain

    def _counted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(estimator_module, "validate_exact_matrix_domain", _counted)
    execution, _ = _execute_raw(raw, attempt_ordinal=1)
    assert execution.validation.failure_id == "F03"
    assert execution.exact_count is None
    assert calls == 0


@pytest.mark.parametrize("field_name", EVIDENCE_SCHEMA)
def test_each_of_seven_evidence_fields_is_required(field_name: str) -> None:
    execution, _ = _execute_raw(_base_raw(), attempt_ordinal=1)
    candidate = dict(execution.evidence.as_mapping())
    del candidate[field_name]
    with pytest.raises(EvidenceContractError):
        canonical_evidence_bytes(candidate)


def test_evidence_mutation_orphan_and_forgery_are_rejected() -> None:
    raw = _base_raw()
    execution, _ = _execute_raw(raw, attempt_ordinal=1)
    trusted = execution.evidence
    identity, dependency, method = _components(raw)
    assert identity and dependency

    with pytest.raises(EvidenceContractError):
        build_effective_trial_evidence(
            attempt_basis=execution.attempt_basis,
            method_spec=method,
            input_lineage_ref="synthetic-lineage-orphan",
        )
    forged_method = EffectiveTrialMethodSpec(
        method_id=method.method_id,
        method_version=method.method_version,
        method_hash=ZERO_HASH,
        canonical_spec_descriptor=method.canonical_spec_descriptor,
    )
    with pytest.raises(EvidenceContractError):
        build_effective_trial_evidence(
            attempt_basis=execution.attempt_basis,
            method_spec=forged_method,
            input_lineage_ref=dependency.input_lineage_ref,
        )

    for mutation in (
        {"effective_trial_count": None},
        {"effective_trial_count_status": EvidenceStatus("blocked", "evidence_integrity_mismatch")},
        {"effective_trial_computation_ref": ZERO_HASH},
        {"effective_trial_method_hash": ZERO_HASH},
    ):
        candidate = dict(trusted.as_mapping())
        candidate.update(mutation)
        with pytest.raises(EvidenceContractError):
            _assert_trusted_serialized_evidence(candidate, trusted)

    candidate = dict(trusted.as_mapping())
    candidate["effective_trial_count"] = CanonicalNumberToken("3")
    assert canonical_evidence_hash(candidate) != canonical_evidence_hash(trusted)
    with pytest.raises(EvidenceContractError):
        _assert_trusted_serialized_evidence(candidate, trusted)


def test_f08_attempted_evidence_digest_is_only_in_snapshot_not_presence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution = _failure_execution("F08", monkeypatch)
    assert execution.attempt_basis.component_snapshot_digests["attempted_evidence"] is not None
    assert len(execution.attempt_basis.presence_bitmap) == 3
    assert "attempted_evidence" not in execution.attempt_basis.presence_bitmap


def test_append_only_recovery_keeps_failure_and_links_new_success() -> None:
    raw_a = _raw_with_matrix([["1", "0"], ["0", "1"]])
    raw_a["integrity_injection"] = "input_hash_mismatch"
    failure, audit_a = _execute_raw(raw_a, attempt_ordinal=1)
    raw_b = dict(raw_a)
    raw_b["integrity_injection"] = "none"
    success = estimator_module.estimate_effective_trial(*_components(raw_b))
    audit_b = build_attempt_audit(
        verification_run_ref=RUN_REF,
        synthetic_case_id=raw_a["case_id"],
        attempt_ordinal=2,
        evidence=success.evidence,
        parent_attempt_audit_ref=audit_a.attempt_audit_ref,
        supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
    )
    log_a = AttemptAuditLog().append(audit_a)
    log_b = log_a.append(audit_b)
    assert log_a.entries == (audit_a,)
    assert log_b.entries == (audit_a, audit_b)
    assert failure.evidence.effective_trial_computation_ref != success.evidence.effective_trial_computation_ref
    assert canonical_evidence_hash(failure.evidence) != canonical_evidence_hash(success.evidence)
    assert audit_b.parent_attempt_audit_ref == audit_a.attempt_audit_ref
    assert audit_b.supersedes_attempt_audit_ref == audit_a.attempt_audit_ref


def test_same_failure_repeat_keeps_stable_evidence_and_appends_distinct_audit() -> None:
    raw = _raw_with_matrix([["1", "0"], ["0", "1"]])
    raw["integrity_injection"] = "input_hash_mismatch"
    first, audit_1 = _execute_raw(raw, attempt_ordinal=1)
    second, audit_2 = _execute_raw(raw, attempt_ordinal=2)
    log = AttemptAuditLog().append(audit_1).append(audit_2)
    assert first.attempt_basis == second.attempt_basis
    assert canonical_evidence_hash(first.evidence) == canonical_evidence_hash(second.evidence)
    assert audit_1.attempt_audit_ref != audit_2.attempt_audit_ref
    assert log.entries == (audit_1, audit_2)


def test_standalone_claim_ceiling_remains_false_for_public_activation() -> None:
    capabilities = {
        "standalone_evidence": True,
        "public_effective_trial_count_populatable": False,
        "c1_computable": False,
        "public_projection": False,
        "competing_gate": False,
        "admission_ready": False,
        "stage3_ready": False,
        "cr172_auto_resume": False,
        "cr172_auto_close": False,
    }
    assert sum(value is True for value in capabilities.values()) == 1
    assert capabilities["standalone_evidence"] is True
    assert all(
        capabilities[name] is False
        for name in capabilities
        if name != "standalone_evidence"
    )
