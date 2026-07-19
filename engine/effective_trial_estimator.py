"""CR-173 的纯离线 exact-rational effective-trial estimator。

本模块只消费 ``effective_trial_evidence`` 已验证的声明式精确输入，不读取真实
数据、不执行 I/O，也不接入 public C1。参与率的语义仅为二阶相关结构有效维度。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import lcm
from typing import Final, Literal, Sequence

from engine.effective_trial_evidence import (
    CanonicalNumberToken,
    ContractValidation,
    DependencyMatrixEnvelope,
    EffectiveTrialAttemptBasisV1,
    EffectiveTrialEvidence,
    EffectiveTrialMethodSpec,
    EvidenceContractError,
    FrozenMapping,
    SealedTrialIdentity,
    ValidatedContractBundle,
    ValidationOutcome,
    build_attempt_basis_v1,
    build_effective_trial_evidence,
    build_failure_attempt_basis,
    failure_outcome,
    present_outcome,
    render_half_even_number_token,
    validate_contract_bundle,
)

_F04: Final[str] = "F04"
_F08: Final[str] = "F08"


@dataclass(frozen=True, slots=True)
class PivotStep:
    """一次确定性对称主元选择的审计摘要。"""

    label: str
    pivot: int
    branch: str


@dataclass(frozen=True, slots=True)
class PivotSelection:
    """主元选择结果；三类分支互斥。"""

    kind: Literal["pivot", "zero_block", "zero_coupling"]
    index: int | None


@dataclass(frozen=True, slots=True)
class ExactPSDProof:
    """精确 PSD 判定结果及稳定的主元轨迹。"""

    is_psd: bool
    rank: int
    branch: str
    pivot_trace: tuple[PivotStep, ...]


@dataclass(frozen=True, slots=True)
class MatrixDomainValidation:
    """有限 exact-rational matrix domain 的验证结果。"""

    is_valid: bool
    reason: str
    proof: ExactPSDProof | None


@dataclass(frozen=True, slots=True)
class ExactEstimatorExecution:
    """一次 estimator 执行的 standalone 结果。"""

    validation: ContractValidation
    outcome: ValidationOutcome
    attempt_basis: EffectiveTrialAttemptBasisV1
    evidence: EffectiveTrialEvidence
    exact_count: Fraction | None
    psd_proof: ExactPSDProof | None


def validate_raw_token_contract(
    sealed_identity: SealedTrialIdentity | None,
    dependency_matrix: DependencyMatrixEnvelope | None,
    method_spec: EffectiveTrialMethodSpec | None,
) -> ContractValidation:
    """复用 S01 的 F01/F02/F03/F05/F06/F07 合同验证。"""

    return validate_contract_bundle(sealed_identity, dependency_matrix, method_spec)


def normalize_dependency_input(
    sealed_identity: SealedTrialIdentity | None,
    dependency_matrix: DependencyMatrixEnvelope | None,
    method_spec: EffectiveTrialMethodSpec | None,
) -> ContractValidation:
    """返回仅含有限 ``Fraction`` matrix 的已验证合同。"""

    return validate_raw_token_contract(sealed_identity, dependency_matrix, method_spec)


def select_symmetric_pivot(
    matrix: Sequence[Sequence[int]],
    labels: Sequence[str],
) -> PivotSelection:
    """按 abs 降序、signed 降序、label 升序选择唯一对称主元。"""

    size = len(matrix)
    if size != len(labels) or any(len(row) != size for row in matrix):
        raise EvidenceContractError("residual matrix 与 labels 维度不一致")
    candidates = [index for index in range(size) if matrix[index][index] != 0]
    if candidates:
        selected = min(
            candidates,
            key=lambda index: (
                -abs(matrix[index][index]),
                -matrix[index][index],
                labels[index],
            ),
        )
        return PivotSelection("pivot", selected)
    has_coupling = any(
        matrix[row][column] != 0
        for row in range(size)
        for column in range(row + 1, size)
    )
    return PivotSelection("zero_coupling" if has_coupling else "zero_block", None)


def fraction_free_ldlt_step(
    matrix: Sequence[Sequence[int]],
    *,
    pivot_index: int,
    previous_pivot: int,
) -> tuple[tuple[int, ...], ...]:
    """执行一次 Bareiss 风格的 exact symmetric ``LDLᵀ`` 消元。"""

    size = len(matrix)
    if size < 1 or any(len(row) != size for row in matrix):
        raise EvidenceContractError("fraction-free step 需要非空方阵")
    if not 0 <= pivot_index < size:
        raise EvidenceContractError("pivot index 越界")
    if previous_pivot <= 0:
        raise EvidenceContractError("previous pivot 必须为正整数")

    order = (pivot_index,) + tuple(index for index in range(size) if index != pivot_index)
    permuted = tuple(tuple(matrix[row][column] for column in order) for row in order)
    pivot = permuted[0][0]
    if pivot <= 0:
        raise EvidenceContractError("fraction-free step 只接受正主元")

    reduced: list[list[int]] = []
    for row in range(1, size):
        reduced_row: list[int] = []
        for column in range(1, size):
            numerator = (
                pivot * permuted[row][column]
                - permuted[row][0] * permuted[column][0]
            )
            quotient, remainder = divmod(numerator, previous_pivot)
            if remainder != 0:
                raise EvidenceContractError("fraction-free exact division invariant 失败")
            reduced_row.append(quotient)
        reduced.append(reduced_row)
    result = tuple(tuple(row) for row in reduced)
    if any(result[row][column] != result[column][row] for row in range(len(result)) for column in range(len(result))):
        raise EvidenceContractError("fraction-free residual 非对称")
    return result


def _integer_scaled_matrix(matrix: Sequence[Sequence[Fraction]]) -> tuple[tuple[int, ...], ...]:
    denominator = 1
    for row in matrix:
        for value in row:
            denominator = lcm(denominator, value.denominator)
    return tuple(
        tuple(value.numerator * (denominator // value.denominator) for value in row)
        for row in matrix
    )


def _prove_exact_psd(
    matrix: Sequence[Sequence[Fraction]],
    labels: Sequence[str],
) -> ExactPSDProof:
    residual = _integer_scaled_matrix(matrix)
    remaining_labels = tuple(labels)
    previous_pivot = 1
    rank = 0
    trace: list[PivotStep] = []

    while residual:
        selection = select_symmetric_pivot(residual, remaining_labels)
        if selection.kind == "zero_block":
            return ExactPSDProof(True, rank, "zero_block_psd", tuple(trace))
        if selection.kind == "zero_coupling":
            return ExactPSDProof(False, rank, "zero_pivot_residual_coupling", tuple(trace))
        assert selection.index is not None
        index = selection.index
        pivot = residual[index][index]
        label = remaining_labels[index]
        if pivot < 0:
            trace.append(PivotStep(label, pivot, "negative_pivot"))
            return ExactPSDProof(False, rank, "negative_pivot", tuple(trace))
        trace.append(PivotStep(label, pivot, "positive_pivot"))
        next_residual = fraction_free_ldlt_step(
            residual,
            pivot_index=index,
            previous_pivot=previous_pivot,
        )
        previous_pivot = pivot
        residual = next_residual
        remaining_labels = tuple(
            remaining_labels[item]
            for item in range(len(remaining_labels))
            if item != index
        )
        rank += 1

    return ExactPSDProof(True, rank, "positive_definite", tuple(trace))


def validate_exact_matrix_domain(
    matrix: Sequence[Sequence[Fraction]],
    ordered_trial_ids: Sequence[str],
) -> MatrixDomainValidation:
    """验证 shape/symmetry/diag/range/PSD，失败统一属于 F04。"""

    labels = tuple(ordered_trial_ids)
    rows = tuple(tuple(row) for row in matrix)
    size = len(labels)
    if size < 1 or len(rows) != size or any(len(row) != size for row in rows):
        return MatrixDomainValidation(False, "shape", None)
    if any(not isinstance(value, Fraction) for row in rows for value in row):
        return MatrixDomainValidation(False, "non_exact_value", None)
    if len(set(labels)) != size or labels != tuple(sorted(labels)):
        return MatrixDomainValidation(False, "labels", None)
    if any(rows[row][column] != rows[column][row] for row in range(size) for column in range(size)):
        return MatrixDomainValidation(False, "symmetry", None)
    if any(rows[index][index] != 1 for index in range(size)):
        return MatrixDomainValidation(False, "unit_diagonal", None)
    if any(value < -1 or value > 1 for row in rows for value in row):
        return MatrixDomainValidation(False, "range", None)
    try:
        proof = _prove_exact_psd(rows, labels)
    except EvidenceContractError:
        raise
    if not proof.is_psd:
        return MatrixDomainValidation(False, proof.branch, proof)
    return MatrixDomainValidation(True, "ok", proof)


def estimate_participation_ratio_exact(
    matrix: Sequence[Sequence[Fraction]],
) -> Fraction:
    """计算 exact ``n² / ΣRij²`` 并执行未舍入范围 invariant。"""

    rows = tuple(tuple(row) for row in matrix)
    size = len(rows)
    if size < 1 or any(len(row) != size for row in rows):
        raise EvidenceContractError("participation ratio 需要非空方阵")
    if any(not isinstance(value, Fraction) for row in rows for value in row):
        raise EvidenceContractError("participation ratio 只接受 Fraction")
    denominator = sum((value * value for row in rows for value in row), Fraction())
    if denominator <= 0:
        raise EvidenceContractError("participation ratio denominator 非正")
    result = Fraction(size * size, 1) / denominator
    if result < 1 or result > size:
        raise EvidenceContractError("未舍入 participation ratio 越界")
    return result


def quantize_and_validate_count(
    exact_count: Fraction,
    *,
    trial_count: int,
) -> CanonicalNumberToken:
    """在 evidence 边界只舍入一次，并执行舍入后范围 invariant。"""

    if not isinstance(exact_count, Fraction):
        raise EvidenceContractError("count quantizer 只接受 Fraction")
    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise EvidenceContractError("trial_count 必须为正整数")
    if exact_count < 1 or exact_count > trial_count:
        raise EvidenceContractError("舍入前 count 越界")
    token = render_half_even_number_token(exact_count, max_scale=12)
    rendered = Fraction(token.value)
    if rendered < 1 or rendered > trial_count:
        raise EvidenceContractError("舍入后 count 越界")
    return token


def _failure_validation(
    base: ContractValidation,
    failure_id: Literal["F04", "F08"],
) -> ContractValidation:
    return ContractValidation(
        bundle=None,
        failure_id=failure_id,
        outcome=failure_outcome(failure_id),
        validation_stage="matrix_domain" if failure_id == _F04 else "evidence",
        presence_bitmap=base.presence_bitmap,
        component_snapshot_digests=base.component_snapshot_digests,
        validated_refs=base.validated_refs,
    )


def _build_failure_execution(
    validation: ContractValidation,
    *,
    proof: ExactPSDProof | None = None,
) -> ExactEstimatorExecution:
    assert validation.outcome is not None
    basis = build_failure_attempt_basis(validation)
    method_hash = validation.validated_refs["method_hash"]
    lineage_ref = validation.validated_refs["input_lineage_ref"]
    method = None
    if validation.bundle is not None and method_hash is not None:
        method = validation.bundle.method_spec
    evidence = build_effective_trial_evidence(
        attempt_basis=basis,
        method_spec=method,
        input_lineage_ref=lineage_ref,
    )
    return ExactEstimatorExecution(
        validation=validation,
        outcome=validation.outcome,
        attempt_basis=basis,
        evidence=evidence,
        exact_count=None,
        psd_proof=proof,
    )


def _failure_from_valid_bundle(
    base: ContractValidation,
    failure_id: Literal["F04", "F08"],
    *,
    proof: ExactPSDProof | None = None,
) -> ExactEstimatorExecution:
    assert base.bundle is not None
    failed = _failure_validation(base, failure_id)
    basis = build_failure_attempt_basis(failed)
    evidence = build_effective_trial_evidence(
        attempt_basis=basis,
        method_spec=base.bundle.method_spec,
        input_lineage_ref=base.bundle.dependency_matrix.input_lineage_ref,
    )
    return ExactEstimatorExecution(
        validation=failed,
        outcome=failed.outcome,
        attempt_basis=basis,
        evidence=evidence,
        exact_count=None,
        psd_proof=proof,
    )


def estimate_effective_trial(
    sealed_identity: SealedTrialIdentity | None,
    dependency_matrix: DependencyMatrixEnvelope | None,
    method_spec: EffectiveTrialMethodSpec | None,
) -> ExactEstimatorExecution:
    """执行固定 precedence 的纯离线 standalone estimation。"""

    validation = normalize_dependency_input(sealed_identity, dependency_matrix, method_spec)
    if not validation.is_valid:
        return _build_failure_execution(validation)
    bundle: ValidatedContractBundle = validation.bundle
    domain = validate_exact_matrix_domain(
        bundle.parsed_matrix,
        bundle.sealed_identity.ordered_trial_ids,
    )
    if not domain.is_valid:
        return _failure_from_valid_bundle(validation, _F04, proof=domain.proof)

    try:
        exact_count = estimate_participation_ratio_exact(bundle.parsed_matrix)
        token = quantize_and_validate_count(
            exact_count,
            trial_count=bundle.sealed_identity.raw_trial_count,
        )
    except EvidenceContractError:
        return _failure_from_valid_bundle(validation, _F08, proof=domain.proof)

    outcome = present_outcome(token)
    basis = build_attempt_basis_v1(
        validation_stage="evidence",
        presence_bitmap=validation.presence_bitmap,
        component_snapshot_digests=validation.component_snapshot_digests,
        validated_refs=validation.validated_refs,
        primary_failure_id="none",
        outcome=outcome,
    )
    evidence = build_effective_trial_evidence(
        attempt_basis=basis,
        method_spec=bundle.method_spec,
        input_lineage_ref=bundle.dependency_matrix.input_lineage_ref,
    )
    return ExactEstimatorExecution(
        validation=validation,
        outcome=outcome,
        attempt_basis=basis,
        evidence=evidence,
        exact_count=exact_count,
        psd_proof=domain.proof,
    )


__all__ = [
    "ExactEstimatorExecution",
    "ExactPSDProof",
    "MatrixDomainValidation",
    "PivotSelection",
    "PivotStep",
    "estimate_effective_trial",
    "estimate_participation_ratio_exact",
    "fraction_free_ldlt_step",
    "normalize_dependency_input",
    "quantize_and_validate_count",
    "select_symmetric_pivot",
    "validate_exact_matrix_domain",
    "validate_raw_token_contract",
]
