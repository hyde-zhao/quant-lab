from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest

import engine.effective_trial_estimator as estimator_module
from engine.effective_trial_estimator import (
    estimate_effective_trial,
    estimate_participation_ratio_exact,
    fraction_free_ldlt_step,
    quantize_and_validate_count,
    select_symmetric_pivot,
    validate_exact_matrix_domain,
)
from engine.effective_trial_evidence import (
    CanonicalNumberToken,
    DEPENDENCY_MATRIX_SCHEMA,
    DependencyMatrixEnvelope,
    EvidenceContractError,
    SealedTrialIdentity,
    build_approved_method_spec,
    canonical_dependency_input_hash,
    canonical_evidence_hash,
    canonical_sealed_identity_hash,
    render_half_even_number_token,
)


def _build_inputs(
    matrix_tokens: tuple[tuple[str, ...], ...],
    *,
    trial_ids: tuple[str, ...] | None = None,
) -> tuple[SealedTrialIdentity, DependencyMatrixEnvelope]:
    ids = trial_ids or tuple(f"trial-{index + 1}" for index in range(len(matrix_tokens)))
    family_ref = "fixture://cr173/family"
    lineage_ref = "fixture://cr173/dependency-input"
    identity = SealedTrialIdentity(
        sealed_family_ref=family_ref,
        sealed_family_hash=canonical_sealed_identity_hash(family_ref, len(ids), ids),
        raw_trial_count=len(ids),
        ordered_trial_ids=ids,
    )
    envelope = DependencyMatrixEnvelope(
        schema_version=DEPENDENCY_MATRIX_SCHEMA,
        ordered_trial_ids=ids,
        matrix_tokens=matrix_tokens,
        input_hash=canonical_dependency_input_hash(
            schema_version=DEPENDENCY_MATRIX_SCHEMA,
            ordered_trial_ids=ids,
            matrix_tokens=matrix_tokens,
            input_lineage_ref=lineage_ref,
            source_mode="declared_exact",
        ),
        input_lineage_ref=lineage_ref,
        source_mode="declared_exact",
    )
    return identity, envelope


def _estimate(matrix_tokens: tuple[tuple[str, ...], ...]):
    identity, envelope = _build_inputs(matrix_tokens)
    return estimate_effective_trial(identity, envelope, build_approved_method_spec())


@pytest.mark.parametrize(
    ("matrix_tokens", "expected_exact", "expected_token", "expected_rank"),
    [
        (
            (
                ("1", "0", "0", "0"),
                ("0", "1", "0", "0"),
                ("0", "0", "1", "0"),
                ("0", "0", "0", "1"),
            ),
            Fraction(4),
            "4",
            4,
        ),
        (
            (
                ("1", "0.5", "0.5", "0.5"),
                ("0.5", "1", "0.5", "0.5"),
                ("0.5", "0.5", "1", "0.5"),
                ("0.5", "0.5", "0.5", "1"),
            ),
            Fraction(16, 7),
            "2.285714285714",
            4,
        ),
        (
            (
                ("1", "1", "1", "1"),
                ("1", "1", "1", "1"),
                ("1", "1", "1", "1"),
                ("1", "1", "1", "1"),
            ),
            Fraction(1),
            "1",
            1,
        ),
        ((("1",),), Fraction(1), "1", 1),
    ],
)
def test_four_analytic_oracles_are_exact_and_present(
    matrix_tokens: tuple[tuple[str, ...], ...],
    expected_exact: Fraction,
    expected_token: str,
    expected_rank: int,
) -> None:
    execution = _estimate(matrix_tokens)

    assert execution.outcome.state == "present"
    assert execution.outcome.reason_code == "ok"
    assert execution.outcome.effective_trial_count == CanonicalNumberToken(expected_token)
    assert execution.exact_count == expected_exact
    assert execution.psd_proof is not None
    assert execution.psd_proof.is_psd is True
    assert execution.psd_proof.rank == expected_rank
    assert 1 <= execution.exact_count <= len(matrix_tokens)
    assert 1 <= Fraction(expected_token) <= len(matrix_tokens)


def test_positive_definite_and_singular_psd_branches_are_exact() -> None:
    positive = validate_exact_matrix_domain(
        (
            (Fraction(1), Fraction(1, 2)),
            (Fraction(1, 2), Fraction(1)),
        ),
        ("a", "b"),
    )
    singular = validate_exact_matrix_domain(
        tuple(tuple(Fraction(1) for _ in range(3)) for _ in range(3)),
        ("a", "b", "c"),
    )

    assert positive.is_valid is True
    assert positive.proof is not None
    assert positive.proof.rank == 2
    assert singular.is_valid is True
    assert singular.proof is not None
    assert singular.proof.rank == 1
    assert singular.proof.branch == "zero_block_psd"


@pytest.mark.parametrize(
    ("tokens", "expected_branch"),
    [
        (
            (
                ("1", "-0.9", "-0.9"),
                ("-0.9", "1", "-0.9"),
                ("-0.9", "-0.9", "1"),
            ),
            "negative_pivot",
        ),
        (
            (
                ("1", "1", "1"),
                ("1", "1", "-1"),
                ("1", "-1", "1"),
            ),
            "zero_pivot_residual_coupling",
        ),
    ],
)
def test_indefinite_oracles_reach_distinct_exact_psd_branches(
    tokens: tuple[tuple[str, ...], ...],
    expected_branch: str,
) -> None:
    fractions = tuple(tuple(Fraction(value) for value in row) for row in tokens)

    assert len(fractions) == 3
    assert all(len(row) == 3 for row in fractions)
    assert all(fractions[index][index] == 1 for index in range(3))
    assert all(-1 <= value <= 1 for row in fractions for value in row)
    assert all(fractions[row][column] == fractions[column][row] for row in range(3) for column in range(3))

    domain = validate_exact_matrix_domain(fractions, ("a", "b", "c"))
    execution = _estimate(tokens)

    assert domain.is_valid is False
    assert domain.proof is not None
    assert domain.proof.branch == expected_branch
    assert execution.outcome.state == "typed_unavailable"
    assert execution.outcome.reason_code == "invalid_dependency_matrix_domain"
    assert execution.outcome.effective_trial_count is None


def test_pivot_comparator_and_fraction_free_step_are_deterministic() -> None:
    matrix = ((2, 0, 0), (0, -2, 0), (0, 0, 2))
    labels = ("b", "a", "c")

    selections = tuple(select_symmetric_pivot(matrix, labels) for _ in range(3))

    assert selections[0].kind == "pivot"
    assert selections[0].index == 0
    assert len(set(selections)) == 1
    assert fraction_free_ldlt_step(
        ((2, 1), (1, 2)),
        pivot_index=0,
        previous_pivot=1,
    ) == ((3,),)


@pytest.mark.parametrize(
    "invalid_token",
    ["NaN", "Inf", "1e-3", "-0", ".5", "01", "1.0", "0.1234567890123", "0.50"],
)
def test_noncanonical_token_is_only_f03(invalid_token: str) -> None:
    identity, envelope = _build_inputs((("1", invalid_token), (invalid_token, "1")))

    execution = estimate_effective_trial(identity, envelope, build_approved_method_spec())

    assert execution.outcome.state == "typed_unavailable"
    assert execution.outcome.reason_code == "unsupported_dependency_representation"
    assert execution.attempt_basis.primary_failure_id == "F03"
    assert execution.attempt_basis.validation_stage == "token_parse"
    assert execution.psd_proof is None


@pytest.mark.parametrize(
    "tokens",
    [
        (("1", "0"),),
        (("1", "0.5"), ("0", "1")),
        (("0.5", "0"), ("0", "1")),
        (("1", "2"), ("2", "1")),
        (("1", "-0.9", "-0.9"), ("-0.9", "1", "-0.9"), ("-0.9", "-0.9", "1")),
    ],
)
def test_finite_exact_domain_failure_is_only_f04(
    tokens: tuple[tuple[str, ...], ...],
) -> None:
    execution = _estimate(tokens)

    assert execution.outcome.state == "typed_unavailable"
    assert execution.outcome.reason_code == "invalid_dependency_matrix_domain"
    assert execution.attempt_basis.primary_failure_id == "F04"
    assert execution.attempt_basis.validation_stage == "matrix_domain"
    assert execution.outcome.effective_trial_count is None


def test_exact_formula_rejects_non_fraction_and_out_of_domain() -> None:
    with pytest.raises(EvidenceContractError):
        estimate_participation_ratio_exact(((1,),))  # type: ignore[arg-type]
    with pytest.raises(EvidenceContractError):
        estimate_participation_ratio_exact(
            ((Fraction(2), Fraction(2)), (Fraction(2), Fraction(2)))
        )


def test_half_even_is_called_once_and_both_invariants_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def tracked_renderer(value: Fraction, *, max_scale: int) -> CanonicalNumberToken:
        nonlocal calls
        calls += 1
        return render_half_even_number_token(value, max_scale=max_scale)

    monkeypatch.setattr(estimator_module, "render_half_even_number_token", tracked_renderer)

    assert quantize_and_validate_count(Fraction(16, 7), trial_count=4).value == "2.285714285714"
    assert calls == 1
    with pytest.raises(EvidenceContractError):
        quantize_and_validate_count(Fraction(9, 10), trial_count=4)

    monkeypatch.setattr(
        estimator_module,
        "render_half_even_number_token",
        lambda value, *, max_scale: CanonicalNumberToken("5"),
    )
    with pytest.raises(EvidenceContractError):
        quantize_and_validate_count(Fraction(4), trial_count=4)


def test_internal_quantizer_failure_maps_to_f08(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        estimator_module,
        "render_half_even_number_token",
        lambda value, *, max_scale: CanonicalNumberToken("5"),
    )
    execution = _estimate(
        (
            ("1", "0", "0", "0"),
            ("0", "1", "0", "0"),
            ("0", "0", "1", "0"),
            ("0", "0", "0", "1"),
        )
    )

    assert execution.outcome.state == "blocked"
    assert execution.outcome.reason_code == "evidence_integrity_mismatch"
    assert execution.attempt_basis.primary_failure_id == "F08"
    assert execution.outcome.effective_trial_count is None


def test_repeat_has_one_exact_result_computation_ref_and_evidence_hash() -> None:
    tokens = (
        ("1", "0.5", "0.5", "0.5"),
        ("0.5", "1", "0.5", "0.5"),
        ("0.5", "0.5", "1", "0.5"),
        ("0.5", "0.5", "0.5", "1"),
    )
    executions = tuple(_estimate(tokens) for _ in range(3))

    assert {item.exact_count for item in executions} == {Fraction(16, 7)}
    assert {item.evidence.effective_trial_computation_ref for item in executions}.__len__() == 1
    assert {canonical_evidence_hash(item.evidence) for item in executions}.__len__() == 1


def test_new_module_has_no_public_dependency_or_disallowed_numeric_path() -> None:
    source = Path(estimator_module.__file__).read_text(encoding="utf-8")
    public_modules = (
        "experiment_family_lineage",
        "experiment_family_lineage_store",
        "strategy_admission_statistical_gate",
        "statistical_evidence",
        "multiple_testing_evidence",
        "overfit_evidence",
        "cross_strategy_reliability_gates",
        "strategy_admission_package",
    )

    assert all(module not in source for module in public_modules)
    assert "import numpy" not in source
    assert "import scipy" not in source
    assert "float(" not in source
    assert "random" not in source
    assert "clamp" not in source
