from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from engine.effective_trial_evidence import (
    ATTEMPT_BASIS_SCHEMA,
    AttemptAuditLog,
    CanonicalNumberToken,
    CanonicalizationError,
    DEPENDENCY_MATRIX_SCHEMA,
    DependencyMatrixEnvelope,
    EVIDENCE_SCHEMA,
    EffectiveTrialAttemptBasisV1,
    EffectiveTrialEvidence,
    EffectiveTrialMethodSpec,
    EvidenceContractError,
    FAILURE_BY_ID,
    FAILURE_DEFINITIONS,
    FrozenMapping,
    METHOD_ID,
    METHOD_VERSION,
    SOURCE_MODE_DECLARED_EXACT,
    SealedTrialIdentity,
    approved_method_descriptor,
    build_approved_method_spec,
    build_attempt_audit,
    build_attempt_basis_v1,
    build_computation_identity,
    build_effective_trial_evidence,
    build_failure_attempt_basis,
    canonical_bytes,
    canonical_component_digest,
    canonical_dependency_input_hash,
    canonical_evidence_bytes,
    canonical_evidence_hash,
    canonical_method_spec_hash,
    canonical_sealed_identity_hash,
    failure_outcome,
    present_outcome,
    render_half_even_number_token,
    validate_canonical_decimal_token,
    validate_contract_bundle,
)


def _valid_contracts() -> tuple[
    SealedTrialIdentity,
    DependencyMatrixEnvelope,
    EffectiveTrialMethodSpec,
]:
    trial_ids = ("trial-001", "trial-002")
    identity = SealedTrialIdentity(
        sealed_family_ref="fixture:sealed-family-001",
        sealed_family_hash=canonical_sealed_identity_hash(
            "fixture:sealed-family-001", 2, trial_ids
        ),
        raw_trial_count=2,
        ordered_trial_ids=trial_ids,
    )
    matrix_tokens = (("1", "0.5"), ("0.5", "1"))
    dependency = DependencyMatrixEnvelope(
        schema_version=DEPENDENCY_MATRIX_SCHEMA,
        ordered_trial_ids=trial_ids,
        matrix_tokens=matrix_tokens,
        input_hash=canonical_dependency_input_hash(
            schema_version=DEPENDENCY_MATRIX_SCHEMA,
            ordered_trial_ids=trial_ids,
            matrix_tokens=matrix_tokens,
            input_lineage_ref="fixture:dependency-input-001",
            source_mode=SOURCE_MODE_DECLARED_EXACT,
        ),
        input_lineage_ref="fixture:dependency-input-001",
        source_mode=SOURCE_MODE_DECLARED_EXACT,
    )
    return identity, dependency, build_approved_method_spec()


def _success_basis(
    count: str = "1.6",
    *,
    snapshot_suffix: str = "base",
) -> tuple[EffectiveTrialAttemptBasisV1, EffectiveTrialMethodSpec, str]:
    identity, dependency, method = _valid_contracts()
    basis = build_attempt_basis_v1(
        validation_stage="evidence",
        presence_bitmap={
            "sealed_identity": True,
            "dependency_matrix": True,
            "method_spec": True,
        },
        component_snapshot_digests={
            "sealed_identity": canonical_component_digest(identity),
            "dependency_matrix": canonical_component_digest(
                FrozenMapping(
                    {
                        "snapshot": dependency.snapshot(),
                        "suffix": snapshot_suffix,
                    }
                )
            ),
            "method_spec": canonical_component_digest(method),
            "attempted_evidence": None,
        },
        validated_refs={
            "input_lineage_ref": dependency.input_lineage_ref,
            "method_hash": method.method_hash,
        },
        primary_failure_id="none",
        outcome=present_outcome(count),
    )
    return basis, method, dependency.input_lineage_ref


def _failure_basis(failure_id: str) -> EffectiveTrialAttemptBasisV1:
    definition = FAILURE_BY_ID[failure_id]
    return build_attempt_basis_v1(
        validation_stage=definition.validation_stage,
        presence_bitmap={
            "sealed_identity": False,
            "dependency_matrix": False,
            "method_spec": False,
        },
        component_snapshot_digests={
            "sealed_identity": None,
            "dependency_matrix": None,
            "method_spec": None,
            "attempted_evidence": (
                canonical_component_digest({"forged": "fixture"})
                if failure_id == "F08"
                else None
            ),
        },
        validated_refs={"input_lineage_ref": None, "method_hash": None},
        primary_failure_id=failure_id,
        outcome=failure_outcome(failure_id),
    )


def _evidence_for_basis(
    basis: EffectiveTrialAttemptBasisV1,
    method: EffectiveTrialMethodSpec | None = None,
    lineage: str | None = None,
) -> EffectiveTrialEvidence:
    return build_effective_trial_evidence(
        attempt_basis=basis,
        method_spec=method,
        input_lineage_ref=lineage,
    )


def test_four_core_contracts_and_nested_values_are_immutable() -> None:
    identity, dependency, method = _valid_contracts()
    basis, _, lineage = _success_basis()
    evidence = _evidence_for_basis(basis, method, lineage)

    with pytest.raises(FrozenInstanceError):
        identity.raw_trial_count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        dependency.source_mode = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        method.method_version = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        evidence.effective_trial_count = None  # type: ignore[misc]
    with pytest.raises(TypeError):
        method.canonical_spec_descriptor["formula"] = "other"  # type: ignore[index]


def test_validate_contract_bundle_success_and_exact_parsed_matrix() -> None:
    identity, dependency, method = _valid_contracts()
    result = validate_contract_bundle(identity, dependency, method)

    assert result.is_valid
    assert result.failure_id is None
    assert result.bundle is not None
    assert result.bundle.parsed_matrix == (
        (Fraction(1), Fraction(1, 2)),
        (Fraction(1, 2), Fraction(1)),
    )
    assert result.validated_refs == {
        "input_lineage_ref": dependency.input_lineage_ref,
        "method_hash": method.method_hash,
    }


def test_contract_validation_precedence_is_fail_closed() -> None:
    identity, dependency, method = _valid_contracts()

    assert validate_contract_bundle(None, None, None).failure_id == "F01"
    assert validate_contract_bundle(identity, None, None).failure_id == "F02"

    invalid_token_dependency = replace(
        dependency,
        matrix_tokens=(("1", "NaN"), ("0.5", "1")),
    )
    assert validate_contract_bundle(identity, invalid_token_dependency, None).failure_id == "F03"
    assert validate_contract_bundle(identity, dependency, None).failure_id == "F05"

    identity_mismatch = replace(identity, ordered_trial_ids=("trial-002", "trial-001"))
    assert validate_contract_bundle(identity_mismatch, dependency, method).failure_id == "F06"

    bad_descriptor = FrozenMapping(
        {**dict(approved_method_descriptor()), "formula": "raw_trial_count"}
    )
    bad_method = EffectiveTrialMethodSpec(
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        method_hash=canonical_method_spec_hash(bad_descriptor),
        canonical_spec_descriptor=bad_descriptor,
    )
    assert validate_contract_bundle(identity, dependency, bad_method).failure_id == "F07"


def test_present_evidence_has_exactly_seven_top_level_fields() -> None:
    basis, method, lineage = _success_basis()
    evidence = _evidence_for_basis(basis, method, lineage)

    assert tuple(evidence.as_mapping()) == tuple(sorted(EVIDENCE_SCHEMA))
    assert set(evidence.as_mapping()) == set(EVIDENCE_SCHEMA)
    assert len(evidence.as_mapping()) == 7
    assert evidence.effective_trial_count == CanonicalNumberToken("1.6")
    assert evidence.effective_trial_count_status.state == "present"
    assert evidence.effective_trial_computation_ref == build_computation_identity(basis)
    assert "raw_trial_count" not in evidence.as_mapping()


@pytest.mark.parametrize("missing_key", EVIDENCE_SCHEMA)
def test_each_missing_evidence_field_is_rejected(missing_key: str) -> None:
    basis, method, lineage = _success_basis()
    evidence = _evidence_for_basis(basis, method, lineage)
    malformed = dict(evidence.as_mapping())
    del malformed[missing_key]

    with pytest.raises(EvidenceContractError):
        canonical_evidence_bytes(malformed)


@pytest.mark.parametrize("definition", FAILURE_DEFINITIONS, ids=lambda item: item.failure_id)
def test_f01_f08_have_stable_state_reason_and_complete_basis(definition: object) -> None:
    failure_id = definition.failure_id  # type: ignore[attr-defined]
    basis = _failure_basis(failure_id)
    evidence = _evidence_for_basis(basis)

    assert set(basis.as_mapping()) == {
        "basis_schema",
        "validation_stage",
        "presence_bitmap",
        "component_snapshot_digests",
        "validated_refs",
        "primary_failure_id",
        "outcome",
    }
    assert basis.basis_schema == ATTEMPT_BASIS_SCHEMA
    assert basis.primary_failure_id == failure_id
    assert evidence.effective_trial_count is None
    assert evidence.effective_trial_count_status.state == definition.state  # type: ignore[attr-defined]
    assert evidence.effective_trial_count_status.reason_code == definition.reason_code  # type: ignore[attr-defined]
    assert evidence.effective_trial_computation_ref.startswith("sha256:")


def test_failure_basis_from_contract_validation_preserves_all_seven_basis_keys() -> None:
    identity, dependency, _ = _valid_contracts()
    result = validate_contract_bundle(identity, dependency, None)
    basis = build_failure_attempt_basis(result)

    assert len(basis.as_mapping()) == 7
    assert basis.primary_failure_id == "F05"
    assert set(basis.presence_bitmap) == {
        "sealed_identity",
        "dependency_matrix",
        "method_spec",
    }


def test_attempt_basis_signature_rejects_run_case_ordinal_and_audit_fields() -> None:
    definition = FAILURE_BY_ID["F01"]
    kwargs = {
        "validation_stage": definition.validation_stage,
        "presence_bitmap": {
            "sealed_identity": False,
            "dependency_matrix": False,
            "method_spec": False,
        },
        "component_snapshot_digests": {
            "sealed_identity": None,
            "dependency_matrix": None,
            "method_spec": None,
            "attempted_evidence": None,
        },
        "validated_refs": {"input_lineage_ref": None, "method_hash": None},
        "primary_failure_id": "F01",
        "outcome": failure_outcome("F01"),
    }
    for forbidden in (
        "verification_run_ref",
        "synthetic_case_id",
        "attempt_ordinal",
        "time",
        "worker",
        "random",
        "attempt_audit_ref",
    ):
        with pytest.raises(TypeError):
            build_attempt_basis_v1(**kwargs, **{forbidden: "forbidden"})  # type: ignore[arg-type]


@pytest.mark.parametrize("token", ["0", "1", "-1", "0.5", "-0.5"])
def test_canonical_decimal_positive_grammar(token: str) -> None:
    parsed = validate_canonical_decimal_token(token)
    assert isinstance(parsed.fraction, Fraction)


@pytest.mark.parametrize(
    "token",
    [
        "NaN",
        "Inf",
        "-Inf",
        "1e2",
        "-0",
        ".5",
        "01",
        "1.0",
        "0.50",
        "0.1234567890123",
        "+1",
        "",
    ],
)
def test_non_canonical_decimal_is_rejected_before_exact_domain(token: str) -> None:
    with pytest.raises(CanonicalizationError):
        validate_canonical_decimal_token(token)


def test_half_even_renderer_uses_exact_fraction_once() -> None:
    assert render_half_even_number_token(Fraction(5, 2), max_scale=0).value == "2"
    assert render_half_even_number_token(Fraction(7, 2), max_scale=0).value == "4"
    assert render_half_even_number_token(Fraction(16, 7)).value == "2.285714285714"
    assert render_half_even_number_token(Fraction(-1, 2), max_scale=0).value == "0"
    with pytest.raises(CanonicalizationError):
        render_half_even_number_token(0.5)  # type: ignore[arg-type]


def test_canonical_serializer_orders_keys_keeps_utf8_and_rejects_float_decimal() -> None:
    first = {"中": "值", "a": CanonicalNumberToken("0.5"), "b": 2}
    second = {"b": 2, "a": CanonicalNumberToken("0.5"), "中": "值"}
    expected = b'{"a":0.5,"b":2,"\xe4\xb8\xad":"\xe5\x80\xbc"}'

    assert canonical_bytes(first) == expected
    assert canonical_bytes(second) == expected
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"value": 0.5})
    with pytest.raises(CanonicalizationError):
        canonical_bytes({"value": Decimal("0.5")})


def test_same_basis_has_one_computation_and_hash_but_three_external_audits() -> None:
    basis, method, lineage = _success_basis()
    evidences = [_evidence_for_basis(basis, method, lineage) for _ in range(3)]
    audits = [
        build_attempt_audit(
            verification_run_ref="fixture-run-001",
            synthetic_case_id="fixture-case-001",
            attempt_ordinal=ordinal,
            evidence=evidence,
        )
        for ordinal, evidence in enumerate(evidences, start=1)
    ]

    assert len({item.effective_trial_computation_ref for item in evidences}) == 1
    assert len({canonical_evidence_hash(item) for item in evidences}) == 1
    assert len({item.attempt_audit_ref for item in audits}) == 3
    assert all("attempt_audit_ref" not in item.as_mapping() for item in evidences)


def test_append_only_recovery_keeps_a_and_adds_new_b_chain() -> None:
    basis_a = _failure_basis("F03")
    evidence_a = _evidence_for_basis(basis_a)
    audit_a = build_attempt_audit(
        verification_run_ref="fixture-run-recovery",
        synthetic_case_id="fixture-case-recovery",
        attempt_ordinal=1,
        evidence=evidence_a,
        diagnostic_codes=("TOKEN_UNSUPPORTED",),
    )
    log_a = AttemptAuditLog().append(audit_a)

    basis_b, method, lineage = _success_basis(snapshot_suffix="repaired")
    evidence_b = _evidence_for_basis(basis_b, method, lineage)
    audit_b = build_attempt_audit(
        verification_run_ref="fixture-run-recovery",
        synthetic_case_id="fixture-case-recovery",
        attempt_ordinal=2,
        evidence=evidence_b,
        parent_attempt_audit_ref=audit_a.attempt_audit_ref,
        supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
        diagnostic_codes=("INPUT_REPAIRED",),
    )
    log_b = log_a.append(audit_b)

    assert len(log_a.entries) == 1
    assert len(log_b.entries) == 2
    assert log_b.entries[0] == audit_a
    assert evidence_a.effective_trial_computation_ref != evidence_b.effective_trial_computation_ref
    assert canonical_evidence_hash(evidence_a) != canonical_evidence_hash(evidence_b)
    assert audit_b.parent_attempt_audit_ref == audit_a.attempt_audit_ref
    assert audit_b.supersedes_attempt_audit_ref == audit_a.attempt_audit_ref
    with pytest.raises(EvidenceContractError):
        log_b.append(audit_b)


def test_forged_or_orphan_references_are_rejected() -> None:
    basis, method, lineage = _success_basis()
    with pytest.raises(EvidenceContractError):
        _evidence_for_basis(basis, method, "fixture:orphan")

    evidence = _evidence_for_basis(basis, method, lineage)
    forged = dict(evidence.as_mapping())
    forged["effective_trial_computation_ref"] = "sha256:forged"
    with pytest.raises(EvidenceContractError):
        canonical_evidence_bytes(forged)


def test_method_hash_changes_when_normative_descriptor_changes() -> None:
    descriptor = approved_method_descriptor()
    changed = FrozenMapping({**dict(descriptor), "formula": "other"})

    assert canonical_method_spec_hash(descriptor) != canonical_method_spec_hash(changed)


def test_unapproved_but_self_consistent_method_cannot_build_evidence() -> None:
    basis, _, lineage = _success_basis()
    descriptor = FrozenMapping(
        {**dict(approved_method_descriptor()), "formula": "unapproved_formula"}
    )
    method = EffectiveTrialMethodSpec(
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        method_hash=canonical_method_spec_hash(descriptor),
        canonical_spec_descriptor=descriptor,
    )
    adversarial_basis = replace(
        basis,
        validated_refs=FrozenMapping(
            {"input_lineage_ref": lineage, "method_hash": method.method_hash}
        ),
    )

    with pytest.raises(EvidenceContractError):
        _evidence_for_basis(adversarial_basis, method, lineage)


def test_wrong_runtime_identifier_types_map_to_stable_failures() -> None:
    _, dependency, method = _valid_contracts()
    trial_ids = ("trial-001", "trial-002")
    wrong_family_ref = 42
    identity = SealedTrialIdentity(
        sealed_family_ref=wrong_family_ref,  # type: ignore[arg-type]
        sealed_family_hash=canonical_sealed_identity_hash(
            wrong_family_ref, 2, trial_ids  # type: ignore[arg-type]
        ),
        raw_trial_count=2,
        ordered_trial_ids=trial_ids,
    )
    assert validate_contract_bundle(identity, dependency, method).failure_id == "F01"

    valid_identity, _, _ = _valid_contracts()
    wrong_lineage = 99
    wrong_lineage_dependency = replace(
        dependency,
        input_lineage_ref=wrong_lineage,  # type: ignore[arg-type]
        input_hash=canonical_dependency_input_hash(
            schema_version=dependency.schema_version,
            ordered_trial_ids=dependency.ordered_trial_ids,
            matrix_tokens=dependency.matrix_tokens,
            input_lineage_ref=wrong_lineage,  # type: ignore[arg-type]
            source_mode=dependency.source_mode,
        ),
    )
    assert (
        validate_contract_bundle(valid_identity, wrong_lineage_dependency, method).failure_id
        == "F02"
    )


@pytest.mark.parametrize(
    "trial_ids",
    [
        (1, 2),
        ("", "trial-002"),
        ("trial-001", 2),
    ],
    ids=("int-ids", "empty-id", "mixed-ids"),
)
def test_wrong_or_empty_trial_identifiers_map_to_f06(
    trial_ids: tuple[object, object],
) -> None:
    family_ref = "fixture:adversarial-family"
    identity = SealedTrialIdentity(
        sealed_family_ref=family_ref,
        sealed_family_hash=canonical_sealed_identity_hash(
            family_ref, 2, trial_ids  # type: ignore[arg-type]
        ),
        raw_trial_count=2,
        ordered_trial_ids=trial_ids,  # type: ignore[arg-type]
    )
    matrix_tokens = (("1", "0.5"), ("0.5", "1"))
    dependency = DependencyMatrixEnvelope(
        schema_version=DEPENDENCY_MATRIX_SCHEMA,
        ordered_trial_ids=trial_ids,  # type: ignore[arg-type]
        matrix_tokens=matrix_tokens,
        input_hash=canonical_dependency_input_hash(
            schema_version=DEPENDENCY_MATRIX_SCHEMA,
            ordered_trial_ids=trial_ids,  # type: ignore[arg-type]
            matrix_tokens=matrix_tokens,
            input_lineage_ref="fixture:adversarial-input",
            source_mode=SOURCE_MODE_DECLARED_EXACT,
        ),
        input_lineage_ref="fixture:adversarial-input",
        source_mode=SOURCE_MODE_DECLARED_EXACT,
    )

    assert validate_contract_bundle(identity, dependency, build_approved_method_spec()).failure_id == "F06"


@pytest.mark.parametrize(
    ("mutated_component", "expected_failure"),
    [
        ("family-bytes", "F01"),
        ("family-bytearray", "F01"),
        ("trial-bytes", "F06"),
        ("lineage-bytes", "F02"),
    ],
)
def test_noncanonical_identifier_values_fail_closed_without_serializer_escape(
    mutated_component: str,
    expected_failure: str,
) -> None:
    identity, dependency, method = _valid_contracts()
    placeholder_hash = "sha256:" + "0" * 64

    if mutated_component.startswith("family-"):
        invalid_family_ref = (
            b"fixture:sealed-family-001"
            if mutated_component == "family-bytes"
            else bytearray(b"fixture:sealed-family-001")
        )
        identity = replace(
            identity,
            sealed_family_ref=invalid_family_ref,  # type: ignore[arg-type]
            sealed_family_hash=placeholder_hash,
        )
    elif mutated_component == "trial-bytes":
        invalid_trial_ids = (b"trial-001", "trial-002")
        identity = replace(
            identity,
            ordered_trial_ids=invalid_trial_ids,  # type: ignore[arg-type]
            sealed_family_hash=placeholder_hash,
        )
        dependency = replace(
            dependency,
            ordered_trial_ids=invalid_trial_ids,  # type: ignore[arg-type]
            input_hash=placeholder_hash,
        )
    else:
        dependency = replace(
            dependency,
            input_lineage_ref=b"fixture:dependency-input-001",  # type: ignore[arg-type]
            input_hash=placeholder_hash,
        )

    result = validate_contract_bundle(identity, dependency, method)

    assert result.failure_id == expected_failure
    assert result.outcome == failure_outcome(expected_failure)
    assert set(result.component_snapshot_digests) == {
        "sealed_identity",
        "dependency_matrix",
        "method_spec",
        "attempted_evidence",
    }


def _root_audit(ordinal: int = 1):
    basis = _failure_basis("F03")
    evidence = _evidence_for_basis(basis)
    return build_attempt_audit(
        verification_run_ref="fixture-run-adversarial-recovery",
        synthetic_case_id="fixture-case-adversarial-recovery",
        attempt_ordinal=ordinal,
        evidence=evidence,
    )


def test_split_parent_and_supersedes_recovery_is_rejected() -> None:
    audit_a = _root_audit(1)
    audit_b = _root_audit(2)
    log = AttemptAuditLog().append(audit_a).append(audit_b)
    basis, method, lineage = _success_basis(snapshot_suffix="split-recovery")
    evidence = _evidence_for_basis(basis, method, lineage)

    with pytest.raises(EvidenceContractError):
        split = build_attempt_audit(
            verification_run_ref="fixture-run-adversarial-recovery",
            synthetic_case_id="fixture-case-adversarial-recovery",
            attempt_ordinal=3,
            evidence=evidence,
            parent_attempt_audit_ref=audit_a.attempt_audit_ref,
            supersedes_attempt_audit_ref=audit_b.attempt_audit_ref,
        )
        log.append(split)


def test_initial_orphan_and_forward_reference_are_rejected() -> None:
    audit_a = _root_audit(1)
    basis, method, lineage = _success_basis(snapshot_suffix="orphan-recovery")
    evidence = _evidence_for_basis(basis, method, lineage)
    audit_b = build_attempt_audit(
        verification_run_ref="fixture-run-adversarial-recovery",
        synthetic_case_id="fixture-case-adversarial-recovery",
        attempt_ordinal=2,
        evidence=evidence,
        parent_attempt_audit_ref=audit_a.attempt_audit_ref,
        supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
    )

    with pytest.raises(EvidenceContractError):
        AttemptAuditLog((audit_b,))
    with pytest.raises(EvidenceContractError):
        AttemptAuditLog((audit_b, audit_a))


def test_recovery_chain_cannot_branch_from_already_superseded_attempt() -> None:
    audit_a = _root_audit(1)
    basis_b, method, lineage = _success_basis(snapshot_suffix="recovery-b")
    evidence_b = _evidence_for_basis(basis_b, method, lineage)
    audit_b = build_attempt_audit(
        verification_run_ref="fixture-run-adversarial-recovery",
        synthetic_case_id="fixture-case-adversarial-recovery",
        attempt_ordinal=2,
        evidence=evidence_b,
        parent_attempt_audit_ref=audit_a.attempt_audit_ref,
        supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
    )
    log = AttemptAuditLog().append(audit_a).append(audit_b)
    basis_c, method_c, lineage_c = _success_basis(snapshot_suffix="recovery-c")
    evidence_c = _evidence_for_basis(basis_c, method_c, lineage_c)
    audit_c = build_attempt_audit(
        verification_run_ref="fixture-run-adversarial-recovery",
        synthetic_case_id="fixture-case-adversarial-recovery",
        attempt_ordinal=3,
        evidence=evidence_c,
        parent_attempt_audit_ref=audit_a.attempt_audit_ref,
        supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
    )

    with pytest.raises(EvidenceContractError):
        log.append(audit_c)


@pytest.mark.parametrize("target", ["root", "recovery"])
def test_audit_log_recomputes_and_rejects_forged_content_addressed_ref(
    target: str,
) -> None:
    audit_a = _root_audit(1)
    entries = [audit_a]
    forged_entry = audit_a
    if target == "recovery":
        basis_b, method, lineage = _success_basis(snapshot_suffix="forged-audit-ref")
        evidence_b = _evidence_for_basis(basis_b, method, lineage)
        forged_entry = build_attempt_audit(
            verification_run_ref="fixture-run-adversarial-recovery",
            synthetic_case_id="fixture-case-adversarial-recovery",
            attempt_ordinal=2,
            evidence=evidence_b,
            parent_attempt_audit_ref=audit_a.attempt_audit_ref,
            supersedes_attempt_audit_ref=audit_a.attempt_audit_ref,
        )
        entries.append(forged_entry)

    # 模拟绕过 dataclass 构造器的反序列化/篡改，日志边界必须独立复算 identity。
    object.__setattr__(forged_entry, "attempt_audit_ref", "sha256:" + "f" * 64)

    with pytest.raises(EvidenceContractError, match="content-addressed identity"):
        AttemptAuditLog(tuple(entries))


def test_audit_constructor_recomputes_content_addressed_ref() -> None:
    audit = _root_audit(1)

    with pytest.raises(EvidenceContractError, match="content-addressed identity"):
        replace(audit, attempt_audit_ref="sha256:" + "e" * 64)


def test_new_module_has_no_strategy_or_public_dependency_edge() -> None:
    source_path = Path("engine/effective_trial_evidence.py")
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(module)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    forbidden_public_modules = {
        "experiment_family_lineage",
        "experiment_family_lineage_store",
        "strategy_admission_statistical_gate",
        "statistical_evidence",
        "multiple_testing_evidence",
        "overfit_evidence",
        "cross_strategy_reliability_gates",
        "strategy_admission_package",
    }
    contract_field_names = {
        field.name
        for contract in (
            SealedTrialIdentity,
            DependencyMatrixEnvelope,
            EffectiveTrialMethodSpec,
            EffectiveTrialEvidence,
        )
        for field in fields(contract)
    }

    assert imports.isdisjoint(forbidden_public_modules)
    assert "strategy_id" not in contract_field_names
    assert "strategy_name" not in contract_field_names
    assert "raw_trial_count" not in {field.name for field in fields(EffectiveTrialEvidence)}
