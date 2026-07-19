"""CR-173 的离线 effective-trial 证据合同与规范化边界。

本模块只处理显式传入的 repository-local 值。它不包含 I/O、public C1
projection、估计器算法或任何运行时集成。
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
import re
from typing import Any, Final


EVIDENCE_SCHEMA: Final[tuple[str, ...]] = (
    "effective_trial_count",
    "effective_trial_count_status",
    "effective_trial_method",
    "effective_trial_method_version",
    "effective_trial_method_hash",
    "effective_trial_input_lineage_ref",
    "effective_trial_computation_ref",
)
ATTEMPT_BASIS_SCHEMA: Final[str] = "quant-lab.effective-trial-attempt-basis.v1"
DEPENDENCY_MATRIX_SCHEMA: Final[str] = "quant-lab.dependency-matrix.v1"
SOURCE_MODE_DECLARED_EXACT: Final[str] = "declared_exact"
METHOD_ID: Final[str] = "spectral_participation_ratio"
METHOD_VERSION: Final[str] = "1.0.0"

_COMPUTATION_DOMAIN: Final[str] = "quant-lab.effective-trial-computation.v1"
_EVIDENCE_DOMAIN: Final[str] = (
    "quant-lab.effective-trial-evidence.spectral-participation-ratio.v1"
)
_AUDIT_DOMAIN: Final[str] = "quant-lab.effective-trial-attempt-audit.v1"
_COMPONENT_DOMAIN: Final[str] = "quant-lab.effective-trial-component-snapshot.v1"
_SEALED_IDENTITY_DOMAIN: Final[str] = "quant-lab.sealed-trial-identity.v1"
_DEPENDENCY_INPUT_DOMAIN: Final[str] = "quant-lab.dependency-matrix-input.v1"
_METHOD_SPEC_DOMAIN: Final[str] = "quant-lab.effective-trial-method-spec.v1"

_SHA256_REF = re.compile(r"sha256:[0-9a-f]{64}\Z")
_DIAGNOSTIC_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
_VALIDATION_STAGES: Final[frozenset[str]] = frozenset(
    {"construction", "token_parse", "method", "integrity", "matrix_domain", "evidence"}
)
_PRESENCE_KEYS: Final[tuple[str, ...]] = (
    "sealed_identity",
    "dependency_matrix",
    "method_spec",
)
_SNAPSHOT_KEYS: Final[tuple[str, ...]] = (
    "sealed_identity",
    "dependency_matrix",
    "method_spec",
    "attempted_evidence",
)
_VALIDATED_REF_KEYS: Final[tuple[str, ...]] = ("input_lineage_ref", "method_hash")
_OUTCOME_KEYS: Final[tuple[str, ...]] = ("state", "reason_code", "effective_trial_count")


class EvidenceContractError(ValueError):
    """证据合同被违反。"""


class CanonicalizationError(EvidenceContractError):
    """值不属于受限 canonical serialization 域。"""


class FrozenMapping(Mapping[str, Any]):
    """按 Unicode key 排序且不可变的字符串键映射。"""

    __slots__ = ("_items", "_dict")

    def __init__(self, value: Mapping[str, Any] | Sequence[tuple[str, Any]]) -> None:
        raw_items = value.items() if isinstance(value, Mapping) else value
        collected: list[tuple[str, Any]] = []
        seen: set[str] = set()
        for key, item in raw_items:
            if not isinstance(key, str):
                raise CanonicalizationError("canonical mapping 的 key 必须是 str")
            if key in seen:
                raise CanonicalizationError(f"canonical mapping 含重复 key: {key}")
            seen.add(key)
            collected.append((key, _freeze_value(item)))
        collected.sort(key=lambda pair: pair[0])
        self._items = tuple(collected)
        self._dict = dict(self._items)

    def __getitem__(self, key: str) -> Any:
        return self._dict[key]

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"FrozenMapping({dict(self._items)!r})"


def _freeze_value(value: Any) -> Any:
    if isinstance(value, FrozenMapping):
        return value
    if isinstance(value, Mapping):
        return FrozenMapping(value)
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class CanonicalDecimal:
    coefficient: int
    scale: int

    def __post_init__(self) -> None:
        if isinstance(self.coefficient, bool) or not isinstance(self.coefficient, int):
            raise CanonicalizationError("coefficient 必须是 int")
        if isinstance(self.scale, bool) or not isinstance(self.scale, int):
            raise CanonicalizationError("scale 必须是 int")
        if not 0 <= self.scale <= 12:
            raise CanonicalizationError("scale 必须位于 [0, 12]")

    @property
    def fraction(self) -> Fraction:
        return Fraction(self.coefficient, 10**self.scale)


@dataclass(frozen=True, slots=True)
class CanonicalNumberToken:
    value: str

    def __post_init__(self) -> None:
        validate_canonical_decimal_token(self.value)

    def __str__(self) -> str:
        return self.value


def validate_canonical_decimal_token(token: str, *, max_scale: int = 12) -> CanonicalDecimal:
    """解析不经过 binary float 的 canonical 十进制 token。"""

    if not isinstance(token, str):
        raise CanonicalizationError("numeric token 必须是 str")
    if isinstance(max_scale, bool) or not isinstance(max_scale, int) or not 0 <= max_scale <= 12:
        raise CanonicalizationError("max_scale 必须是 [0, 12] 内的 int")

    negative = token.startswith("-")
    unsigned = token[1:] if negative else token
    if not unsigned:
        raise CanonicalizationError("numeric token 为空")
    if unsigned.count(".") > 1:
        raise CanonicalizationError("numeric token 含多个小数点")

    integer_part, dot, fractional_part = unsigned.partition(".")
    if not integer_part.isascii() or not integer_part.isdigit():
        raise CanonicalizationError("numeric token 必须是普通十进制")
    if len(integer_part) > 1 and integer_part.startswith("0"):
        raise CanonicalizationError("numeric token 不得含前导零")
    if dot:
        if (
            not fractional_part
            or not fractional_part.isascii()
            or not fractional_part.isdigit()
            or len(fractional_part) > max_scale
            or fractional_part.endswith("0")
        ):
            raise CanonicalizationError("小数部分不是 canonical 表示")
    if negative and integer_part == "0" and (not dot or set(fractional_part) <= {"0"}):
        raise CanonicalizationError("不允许负零")
    if not dot and negative and integer_part == "0":
        raise CanonicalizationError("不允许负零")

    digits = integer_part + fractional_part
    coefficient = int(digits)
    if negative:
        coefficient = -coefficient
    return CanonicalDecimal(coefficient=coefficient, scale=len(fractional_part))


def render_half_even_number_token(value: Fraction, *, max_scale: int = 12) -> CanonicalNumberToken:
    """将 exact Fraction 一次 round-half-even 后渲染为 canonical number token。"""

    if not isinstance(value, Fraction):
        raise CanonicalizationError("renderer 只接受 Fraction")
    if isinstance(max_scale, bool) or not isinstance(max_scale, int) or not 0 <= max_scale <= 12:
        raise CanonicalizationError("max_scale 必须是 [0, 12] 内的 int")

    factor = 10**max_scale
    sign = -1 if value < 0 else 1
    numerator = abs(value.numerator) * factor
    quotient, remainder = divmod(numerator, value.denominator)
    doubled = remainder * 2
    if doubled > value.denominator or (doubled == value.denominator and quotient % 2 == 1):
        quotient += 1
    coefficient = sign * quotient
    scale = max_scale
    while scale and coefficient % 10 == 0:
        coefficient //= 10
        scale -= 1

    absolute = str(abs(coefficient)).rjust(scale + 1, "0")
    if scale:
        rendered = f"{absolute[:-scale]}.{absolute[-scale:]}"
    else:
        rendered = absolute
    if coefficient < 0:
        rendered = f"-{rendered}"
    return CanonicalNumberToken(rendered)


def _canonical_json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def canonical_bytes(value: Any) -> bytes:
    """编码受限 canonical JSON；number token 保持 JSON number，不变成字符串。"""

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, CanonicalNumberToken):
            validate_canonical_decimal_token(item.value)
            return item.value
        if isinstance(item, int) and not isinstance(item, bool):
            return str(item)
        if isinstance(item, str):
            return _canonical_json_string(item)
        if isinstance(item, Mapping):
            pairs: list[str] = []
            for key in sorted(item.keys()):
                if not isinstance(key, str):
                    raise CanonicalizationError("canonical mapping 的 key 必须是 str")
                pairs.append(f"{_canonical_json_string(key)}:{encode(item[key])}")
            return "{" + ",".join(pairs) + "}"
        if isinstance(item, (tuple, list)):
            return "[" + ",".join(encode(child) for child in item) + "]"
        raise CanonicalizationError(f"不支持的 canonical 类型: {type(item).__name__}")

    return encode(value).encode("utf-8")


def _domain_hash(domain: str, payload: bytes) -> str:
    domain_bytes = domain.encode("utf-8")
    digest = hashlib.sha256(
        len(domain_bytes).to_bytes(4, "big")
        + domain_bytes
        + len(payload).to_bytes(8, "big")
        + payload
    ).hexdigest()
    return f"sha256:{digest}"


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise EvidenceContractError(f"{field_name} 必须是 non-empty str")


def _require_hash_ref(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_REF.fullmatch(value) is None:
        raise EvidenceContractError(f"{field_name} 必须是 sha256 ref")


@dataclass(frozen=True, slots=True)
class SealedTrialIdentity:
    sealed_family_ref: str
    sealed_family_hash: str
    raw_trial_count: int
    ordered_trial_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordered_trial_ids", tuple(self.ordered_trial_ids))

    def snapshot(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "ordered_trial_ids": self.ordered_trial_ids,
                "raw_trial_count": self.raw_trial_count,
                "sealed_family_hash": self.sealed_family_hash,
                "sealed_family_ref": self.sealed_family_ref,
            }
        )


@dataclass(frozen=True, slots=True)
class DependencyMatrixEnvelope:
    schema_version: str
    ordered_trial_ids: tuple[str, ...]
    matrix_tokens: tuple[tuple[str, ...], ...]
    input_hash: str
    input_lineage_ref: str
    source_mode: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordered_trial_ids", tuple(self.ordered_trial_ids))
        object.__setattr__(
            self,
            "matrix_tokens",
            tuple(tuple(row) for row in self.matrix_tokens),
        )

    def snapshot(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "input_hash": self.input_hash,
                "input_lineage_ref": self.input_lineage_ref,
                "matrix_tokens": self.matrix_tokens,
                "ordered_trial_ids": self.ordered_trial_ids,
                "schema_version": self.schema_version,
                "source_mode": self.source_mode,
            }
        )


@dataclass(frozen=True, slots=True)
class EffectiveTrialMethodSpec:
    method_id: str
    method_version: str
    method_hash: str
    canonical_spec_descriptor: FrozenMapping

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_spec_descriptor",
            FrozenMapping(self.canonical_spec_descriptor),
        )

    def snapshot(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "canonical_spec_descriptor": self.canonical_spec_descriptor,
                "method_hash": self.method_hash,
                "method_id": self.method_id,
                "method_version": self.method_version,
            }
        )


@dataclass(frozen=True, slots=True)
class EvidenceStatus:
    state: str
    reason_code: str

    def __post_init__(self) -> None:
        expected = REASON_TO_STATE.get(self.reason_code)
        if expected is None or self.state != expected:
            raise EvidenceContractError("state/reason_code 组合非法")

    def as_mapping(self) -> FrozenMapping:
        return FrozenMapping({"state": self.state, "reason_code": self.reason_code})


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    state: str
    reason_code: str
    effective_trial_count: CanonicalNumberToken | None

    def __post_init__(self) -> None:
        EvidenceStatus(self.state, self.reason_code)
        if self.state == "present":
            if not isinstance(self.effective_trial_count, CanonicalNumberToken):
                raise EvidenceContractError("present outcome 必须携带 canonical count")
        elif self.effective_trial_count is not None:
            raise EvidenceContractError("非 present outcome 的 count 必须为 null")

    def as_mapping(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "state": self.state,
                "reason_code": self.reason_code,
                "effective_trial_count": self.effective_trial_count,
            }
        )


@dataclass(frozen=True, slots=True)
class FailureDefinition:
    failure_id: str
    reason_code: str
    state: str
    validation_stage: str


FAILURE_DEFINITIONS: Final[tuple[FailureDefinition, ...]] = (
    FailureDefinition("F01", "missing_sealed_identity", "typed_unavailable", "construction"),
    FailureDefinition("F02", "missing_dependency_matrix", "typed_unavailable", "construction"),
    FailureDefinition(
        "F03", "unsupported_dependency_representation", "typed_unavailable", "token_parse"
    ),
    FailureDefinition("F05", "missing_method_spec", "typed_unavailable", "method"),
    FailureDefinition("F06", "identity_or_input_integrity_mismatch", "blocked", "integrity"),
    FailureDefinition("F07", "method_spec_mismatch", "blocked", "method"),
    FailureDefinition("F04", "invalid_dependency_matrix_domain", "typed_unavailable", "matrix_domain"),
    FailureDefinition("F08", "evidence_integrity_mismatch", "blocked", "evidence"),
)
FAILURE_BY_ID: Final[dict[str, FailureDefinition]] = {
    definition.failure_id: definition for definition in FAILURE_DEFINITIONS
}
REASON_TO_STATE: Final[dict[str, str]] = {
    "ok": "present",
    **{definition.reason_code: definition.state for definition in FAILURE_DEFINITIONS},
}


def failure_outcome(failure_id: str) -> ValidationOutcome:
    try:
        definition = FAILURE_BY_ID[failure_id]
    except KeyError as exc:
        raise EvidenceContractError(f"未知 failure ID: {failure_id}") from exc
    return ValidationOutcome(definition.state, definition.reason_code, None)


def present_outcome(count: CanonicalNumberToken | str) -> ValidationOutcome:
    token = count if isinstance(count, CanonicalNumberToken) else CanonicalNumberToken(count)
    return ValidationOutcome("present", "ok", token)


def approved_method_descriptor() -> FrozenMapping:
    """返回 v1 method hash 覆盖的完整 immutable descriptor。"""

    return FrozenMapping(
        {
            "attempt_basis_schema": ATTEMPT_BASIS_SCHEMA,
            "canonical_serialization": "restricted-json-unicode-key-order-domain-length-prefix-v1",
            "effective_trial_evidence_schema": EVIDENCE_SCHEMA,
            "failure_precedence": tuple(item.failure_id for item in FAILURE_DEFINITIONS),
            "failure_reasons": tuple(item.reason_code for item in FAILURE_DEFINITIONS),
            "formula": "n_squared_over_sum_all_matrix_entries_squared",
            "input_numeric_grammar": "canonical-base10-max-scale-12-no-exponent-no-negative-zero",
            "method_id": METHOD_ID,
            "method_version": METHOD_VERSION,
            "output_range": ("1", "n"),
            "output_rounding": "single-round-half-even-max-scale-12-then-range-recheck",
            "psd_rule": "deterministic-lexicographic-symmetric-pivot-fraction-free-exact-ldlt-no-tolerance",
            "stable_computation_ref": "domain-hash-of-canonical-attempt-basis-v1",
        }
    )


def canonical_method_spec_hash(descriptor: Mapping[str, Any]) -> str:
    return _domain_hash(_METHOD_SPEC_DOMAIN, canonical_bytes(descriptor))


def build_approved_method_spec() -> EffectiveTrialMethodSpec:
    descriptor = approved_method_descriptor()
    return EffectiveTrialMethodSpec(
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        method_hash=canonical_method_spec_hash(descriptor),
        canonical_spec_descriptor=descriptor,
    )


def canonical_sealed_identity_hash(
    sealed_family_ref: str,
    raw_trial_count: int,
    ordered_trial_ids: Sequence[str],
) -> str:
    payload = FrozenMapping(
        {
            "sealed_family_ref": sealed_family_ref,
            "raw_trial_count": raw_trial_count,
            "ordered_trial_ids": tuple(ordered_trial_ids),
        }
    )
    return _domain_hash(_SEALED_IDENTITY_DOMAIN, canonical_bytes(payload))


def canonical_dependency_input_hash(
    *,
    schema_version: str,
    ordered_trial_ids: Sequence[str],
    matrix_tokens: Sequence[Sequence[str]],
    input_lineage_ref: str,
    source_mode: str,
) -> str:
    payload = FrozenMapping(
        {
            "schema_version": schema_version,
            "ordered_trial_ids": tuple(ordered_trial_ids),
            "matrix_tokens": tuple(tuple(row) for row in matrix_tokens),
            "input_lineage_ref": input_lineage_ref,
            "source_mode": source_mode,
        }
    )
    return _domain_hash(_DEPENDENCY_INPUT_DOMAIN, canonical_bytes(payload))


def canonical_component_digest(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, SealedTrialIdentity):
        value = value.snapshot()
    elif isinstance(value, DependencyMatrixEnvelope):
        value = value.snapshot()
    elif isinstance(value, EffectiveTrialMethodSpec):
        value = value.snapshot()
    elif isinstance(value, EffectiveTrialEvidence):
        value = value.as_mapping()
    return _domain_hash(_COMPONENT_DOMAIN, canonical_bytes(value))


def _safe_component_digest(
    value: Any,
    *,
    component_name: str,
    failure_id: str | None,
) -> str | None:
    """为被拒绝且不可规范化的输入生成不含原值的确定性快照。"""

    if value is None:
        return None
    try:
        return canonical_component_digest(value)
    except (EvidenceContractError, TypeError):
        rejected_marker = FrozenMapping(
            {
                "component_name": component_name,
                "failure_id": failure_id or "unclassified",
                "snapshot_state": "rejected_non_canonical",
            }
        )
        return canonical_component_digest(rejected_marker)


@dataclass(frozen=True, slots=True)
class ValidatedContractBundle:
    sealed_identity: SealedTrialIdentity
    dependency_matrix: DependencyMatrixEnvelope
    method_spec: EffectiveTrialMethodSpec
    parsed_matrix: tuple[tuple[Fraction, ...], ...]


@dataclass(frozen=True, slots=True)
class ContractValidation:
    bundle: ValidatedContractBundle | None
    failure_id: str | None
    outcome: ValidationOutcome | None
    validation_stage: str
    presence_bitmap: FrozenMapping
    component_snapshot_digests: FrozenMapping
    validated_refs: FrozenMapping

    @property
    def is_valid(self) -> bool:
        return self.bundle is not None and self.failure_id is None


def _validation_result(
    *,
    identity: SealedTrialIdentity | None,
    dependency: DependencyMatrixEnvelope | None,
    method: EffectiveTrialMethodSpec | None,
    failure_id: str | None,
    parsed_matrix: tuple[tuple[Fraction, ...], ...] | None = None,
) -> ContractValidation:
    presence = FrozenMapping(
        {
            "sealed_identity": identity is not None,
            "dependency_matrix": dependency is not None,
            "method_spec": method is not None,
        }
    )
    snapshots = FrozenMapping(
        {
            "sealed_identity": _safe_component_digest(
                identity,
                component_name="sealed_identity",
                failure_id=failure_id,
            ),
            "dependency_matrix": _safe_component_digest(
                dependency,
                component_name="dependency_matrix",
                failure_id=failure_id,
            ),
            "method_spec": _safe_component_digest(
                method,
                component_name="method_spec",
                failure_id=failure_id,
            ),
            "attempted_evidence": None,
        }
    )
    # validated_refs 只保留已经跨过对应完整性门的片段；原始/冲突内容只进 digest。
    input_ref = None
    if (
        dependency is not None
        and dependency.input_lineage_ref
        and failure_id in {None, "F04", "F07", "F08"}
    ):
        input_ref = dependency.input_lineage_ref
    method_hash = None
    if (
        method is not None
        and method.method_hash
        and failure_id in {None, "F04", "F08"}
    ):
        method_hash = method.method_hash
    validated_refs = FrozenMapping(
        {"input_lineage_ref": input_ref, "method_hash": method_hash}
    )
    if failure_id is not None:
        definition = FAILURE_BY_ID[failure_id]
        return ContractValidation(
            bundle=None,
            failure_id=failure_id,
            outcome=failure_outcome(failure_id),
            validation_stage=definition.validation_stage,
            presence_bitmap=presence,
            component_snapshot_digests=snapshots,
            validated_refs=validated_refs,
        )
    assert identity is not None and dependency is not None and method is not None
    assert parsed_matrix is not None
    return ContractValidation(
        bundle=ValidatedContractBundle(identity, dependency, method, parsed_matrix),
        failure_id=None,
        outcome=None,
        validation_stage="matrix_domain",
        presence_bitmap=presence,
        component_snapshot_digests=snapshots,
        validated_refs=validated_refs,
    )


def validate_contract_bundle(
    sealed_identity: SealedTrialIdentity | None,
    dependency_matrix: DependencyMatrixEnvelope | None,
    method_spec: EffectiveTrialMethodSpec | None,
) -> ContractValidation:
    """按 F01/F02/F03/F05/F06/F07 顺序验证进入 S02 前的合同。

    F04 的 matrix-domain/PSD 判断由 S02 exact estimator 执行，F08 由 evidence
    边界执行；本函数不会抢占这两个 owner。
    """

    if sealed_identity is None or any(
        (
            not isinstance(sealed_identity.sealed_family_ref, str),
            not sealed_identity.sealed_family_ref,
            not isinstance(sealed_identity.sealed_family_hash, str),
            not sealed_identity.sealed_family_hash,
            isinstance(sealed_identity.raw_trial_count, bool),
            not isinstance(sealed_identity.raw_trial_count, int),
            sealed_identity.raw_trial_count < 1,
            not sealed_identity.ordered_trial_ids,
        )
    ):
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F01",
        )
    if dependency_matrix is None or any(
        (
            not isinstance(dependency_matrix.schema_version, str),
            not dependency_matrix.schema_version,
            not dependency_matrix.ordered_trial_ids,
            not dependency_matrix.matrix_tokens,
            not isinstance(dependency_matrix.input_hash, str),
            not dependency_matrix.input_hash,
            not isinstance(dependency_matrix.input_lineage_ref, str),
            not dependency_matrix.input_lineage_ref,
            not isinstance(dependency_matrix.source_mode, str),
            not dependency_matrix.source_mode,
        )
    ):
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F02",
        )

    parsed_rows: list[tuple[Fraction, ...]] = []
    representation_invalid = (
        dependency_matrix.schema_version != DEPENDENCY_MATRIX_SCHEMA
        or dependency_matrix.source_mode != SOURCE_MODE_DECLARED_EXACT
    )
    if not representation_invalid:
        try:
            for row in dependency_matrix.matrix_tokens:
                if not row:
                    raise CanonicalizationError("matrix row 为空")
                parsed_rows.append(
                    tuple(validate_canonical_decimal_token(token).fraction for token in row)
                )
        except (CanonicalizationError, TypeError):
            representation_invalid = True
    if representation_invalid:
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F03",
        )

    if method_spec is None or any(
        (
            not isinstance(method_spec.method_id, str),
            not method_spec.method_id,
            not isinstance(method_spec.method_version, str),
            not method_spec.method_version,
            not isinstance(method_spec.method_hash, str),
            not method_spec.method_hash,
            not method_spec.canonical_spec_descriptor,
        )
    ):
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F05",
        )

    ids = sealed_identity.ordered_trial_ids
    identity_ids_valid = all(isinstance(item, str) and bool(item) for item in ids)
    dependency_ids_valid = all(
        isinstance(item, str) and bool(item)
        for item in dependency_matrix.ordered_trial_ids
    )
    # 不可信 identifier 必须先完成 typed gate，之后才能进入 canonical hash/set/sort。
    if not identity_ids_valid or not dependency_ids_valid:
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F06",
        )

    expected_identity_hash = canonical_sealed_identity_hash(
        sealed_identity.sealed_family_ref,
        sealed_identity.raw_trial_count,
        sealed_identity.ordered_trial_ids,
    )
    expected_input_hash = canonical_dependency_input_hash(
        schema_version=dependency_matrix.schema_version,
        ordered_trial_ids=dependency_matrix.ordered_trial_ids,
        matrix_tokens=dependency_matrix.matrix_tokens,
        input_lineage_ref=dependency_matrix.input_lineage_ref,
        source_mode=dependency_matrix.source_mode,
    )
    integrity_invalid = any(
        (
            _SHA256_REF.fullmatch(sealed_identity.sealed_family_hash) is None,
            _SHA256_REF.fullmatch(dependency_matrix.input_hash) is None,
            sealed_identity.sealed_family_hash != expected_identity_hash,
            dependency_matrix.input_hash != expected_input_hash,
            len(ids) != sealed_identity.raw_trial_count,
            len(set(ids)) != len(ids),
            ids != tuple(sorted(ids)),
            dependency_matrix.ordered_trial_ids != ids,
        )
    )
    if integrity_invalid:
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F06",
        )

    approved_descriptor = approved_method_descriptor()
    method_invalid = any(
        (
            method_spec.method_id != METHOD_ID,
            method_spec.method_version != METHOD_VERSION,
            method_spec.canonical_spec_descriptor != approved_descriptor,
            method_spec.method_hash != canonical_method_spec_hash(method_spec.canonical_spec_descriptor),
        )
    )
    if method_invalid:
        return _validation_result(
            identity=sealed_identity,
            dependency=dependency_matrix,
            method=method_spec,
            failure_id="F07",
        )

    return _validation_result(
        identity=sealed_identity,
        dependency=dependency_matrix,
        method=method_spec,
        failure_id=None,
        parsed_matrix=tuple(parsed_rows),
    )


@dataclass(frozen=True, slots=True)
class EffectiveTrialAttemptBasisV1:
    basis_schema: str
    validation_stage: str
    presence_bitmap: FrozenMapping
    component_snapshot_digests: FrozenMapping
    validated_refs: FrozenMapping
    primary_failure_id: str
    outcome: FrozenMapping

    def __post_init__(self) -> None:
        object.__setattr__(self, "presence_bitmap", FrozenMapping(self.presence_bitmap))
        object.__setattr__(
            self,
            "component_snapshot_digests",
            FrozenMapping(self.component_snapshot_digests),
        )
        object.__setattr__(self, "validated_refs", FrozenMapping(self.validated_refs))
        object.__setattr__(self, "outcome", FrozenMapping(self.outcome))
        _validate_attempt_basis(self)

    def as_mapping(self) -> FrozenMapping:
        return FrozenMapping({field.name: getattr(self, field.name) for field in fields(self)})


def _require_exact_keys(mapping: Mapping[str, Any], expected: tuple[str, ...], name: str) -> None:
    if set(mapping) != set(expected) or len(mapping) != len(expected):
        raise EvidenceContractError(f"{name} 必须精确包含 {len(expected)} 个键")


def _validate_attempt_basis(basis: EffectiveTrialAttemptBasisV1) -> None:
    if basis.basis_schema != ATTEMPT_BASIS_SCHEMA:
        raise EvidenceContractError("attempt basis schema 非 v1")
    if basis.validation_stage not in _VALIDATION_STAGES:
        raise EvidenceContractError("validation_stage 非法")
    _require_exact_keys(basis.presence_bitmap, _PRESENCE_KEYS, "presence_bitmap")
    if any(not isinstance(value, bool) for value in basis.presence_bitmap.values()):
        raise EvidenceContractError("presence_bitmap 值必须是 bool")
    _require_exact_keys(basis.component_snapshot_digests, _SNAPSHOT_KEYS, "snapshot digests")
    for value in basis.component_snapshot_digests.values():
        if value is not None:
            _require_hash_ref(value, "component snapshot digest")
    _require_exact_keys(basis.validated_refs, _VALIDATED_REF_KEYS, "validated_refs")
    for key, value in basis.validated_refs.items():
        if value is not None:
            if key == "method_hash":
                _require_hash_ref(value, key)
            else:
                _require_non_empty(value, key)
    _require_exact_keys(basis.outcome, _OUTCOME_KEYS, "outcome")
    outcome = ValidationOutcome(
        state=basis.outcome["state"],
        reason_code=basis.outcome["reason_code"],
        effective_trial_count=basis.outcome["effective_trial_count"],
    )
    if basis.primary_failure_id == "none":
        if outcome.state != "present" or basis.validation_stage != "evidence":
            raise EvidenceContractError("成功 basis 必须是 evidence/present/ok")
    else:
        definition = FAILURE_BY_ID.get(basis.primary_failure_id)
        if definition is None:
            raise EvidenceContractError("primary_failure_id 非法")
        if (
            outcome.state != definition.state
            or outcome.reason_code != definition.reason_code
            or basis.validation_stage != definition.validation_stage
        ):
            raise EvidenceContractError("failure ID、stage 与 outcome 不一致")


def build_attempt_basis_v1(
    *,
    validation_stage: str,
    presence_bitmap: Mapping[str, bool],
    component_snapshot_digests: Mapping[str, str | None],
    validated_refs: Mapping[str, str | None],
    primary_failure_id: str,
    outcome: ValidationOutcome,
) -> EffectiveTrialAttemptBasisV1:
    return EffectiveTrialAttemptBasisV1(
        basis_schema=ATTEMPT_BASIS_SCHEMA,
        validation_stage=validation_stage,
        presence_bitmap=FrozenMapping(presence_bitmap),
        component_snapshot_digests=FrozenMapping(component_snapshot_digests),
        validated_refs=FrozenMapping(validated_refs),
        primary_failure_id=primary_failure_id,
        outcome=outcome.as_mapping(),
    )


def build_failure_attempt_basis(
    validation: ContractValidation,
    *,
    attempted_evidence_digest: str | None = None,
) -> EffectiveTrialAttemptBasisV1:
    if validation.failure_id is None or validation.outcome is None:
        raise EvidenceContractError("只有失败 validation 可直接生成 failure basis")
    snapshots = dict(validation.component_snapshot_digests)
    snapshots["attempted_evidence"] = attempted_evidence_digest
    return build_attempt_basis_v1(
        validation_stage=validation.validation_stage,
        presence_bitmap=validation.presence_bitmap,
        component_snapshot_digests=snapshots,
        validated_refs=validation.validated_refs,
        primary_failure_id=validation.failure_id,
        outcome=validation.outcome,
    )


def build_computation_identity(basis: EffectiveTrialAttemptBasisV1) -> str:
    if not isinstance(basis, EffectiveTrialAttemptBasisV1):
        raise EvidenceContractError("computation identity 只接受 v1 attempt basis")
    return _domain_hash(_COMPUTATION_DOMAIN, canonical_bytes(basis.as_mapping()))


@dataclass(frozen=True, slots=True)
class EffectiveTrialEvidence:
    effective_trial_count: CanonicalNumberToken | None
    effective_trial_count_status: EvidenceStatus
    effective_trial_method: str | None
    effective_trial_method_version: str | None
    effective_trial_method_hash: str | None
    effective_trial_input_lineage_ref: str | None
    effective_trial_computation_ref: str

    def __post_init__(self) -> None:
        _validate_evidence_values(self.as_mapping())

    def as_mapping(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "effective_trial_count": self.effective_trial_count,
                "effective_trial_count_status": self.effective_trial_count_status.as_mapping(),
                "effective_trial_method": self.effective_trial_method,
                "effective_trial_method_version": self.effective_trial_method_version,
                "effective_trial_method_hash": self.effective_trial_method_hash,
                "effective_trial_input_lineage_ref": self.effective_trial_input_lineage_ref,
                "effective_trial_computation_ref": self.effective_trial_computation_ref,
            }
        )


def _validate_evidence_values(mapping: Mapping[str, Any]) -> None:
    _require_exact_keys(mapping, EVIDENCE_SCHEMA, "effective evidence")
    status_value = mapping["effective_trial_count_status"]
    if isinstance(status_value, EvidenceStatus):
        status = status_value
    elif isinstance(status_value, Mapping):
        _require_exact_keys(status_value, ("state", "reason_code"), "evidence status")
        status = EvidenceStatus(status_value["state"], status_value["reason_code"])
    else:
        raise EvidenceContractError("evidence status 类型非法")
    count = mapping["effective_trial_count"]
    if status.state == "present":
        if not isinstance(count, CanonicalNumberToken):
            raise EvidenceContractError("present evidence 必须携带 canonical count")
        for key in (
            "effective_trial_method",
            "effective_trial_method_version",
            "effective_trial_method_hash",
            "effective_trial_input_lineage_ref",
        ):
            _require_non_empty(mapping[key], key)
        _require_hash_ref(mapping["effective_trial_method_hash"], "effective_trial_method_hash")
    elif count is not None:
        raise EvidenceContractError("非 present evidence 的 count 必须为 null")
    for key in (
        "effective_trial_method",
        "effective_trial_method_version",
        "effective_trial_method_hash",
        "effective_trial_input_lineage_ref",
    ):
        if mapping[key] is not None:
            _require_non_empty(mapping[key], key)
    if mapping["effective_trial_method_hash"] is not None:
        _require_hash_ref(mapping["effective_trial_method_hash"], "effective_trial_method_hash")
    _require_hash_ref(mapping["effective_trial_computation_ref"], "effective_trial_computation_ref")


def build_effective_trial_evidence(
    *,
    attempt_basis: EffectiveTrialAttemptBasisV1,
    method_spec: EffectiveTrialMethodSpec | None,
    input_lineage_ref: str | None,
) -> EffectiveTrialEvidence:
    outcome = ValidationOutcome(
        state=attempt_basis.outcome["state"],
        reason_code=attempt_basis.outcome["reason_code"],
        effective_trial_count=attempt_basis.outcome["effective_trial_count"],
    )
    validated_method_hash = attempt_basis.validated_refs["method_hash"]
    validated_lineage = attempt_basis.validated_refs["input_lineage_ref"]
    if method_spec is not None:
        approved_descriptor = approved_method_descriptor()
        approved_hash = canonical_method_spec_hash(approved_descriptor)
        if (
            method_spec.method_id != METHOD_ID
            or method_spec.method_version != METHOD_VERSION
            or method_spec.canonical_spec_descriptor != approved_descriptor
            or method_spec.method_hash != approved_hash
            or method_spec.method_hash != canonical_method_spec_hash(method_spec.canonical_spec_descriptor)
            or validated_method_hash != method_spec.method_hash
        ):
            raise EvidenceContractError("method spec 未通过 attempt-basis trust binding")
    elif validated_method_hash is not None:
        raise EvidenceContractError("validated method ref 存在但 method spec 缺失")
    if input_lineage_ref != validated_lineage:
        raise EvidenceContractError("input lineage 未通过 attempt-basis trust binding")
    if outcome.state == "present" and (method_spec is None or input_lineage_ref is None):
        raise EvidenceContractError("present evidence 缺少已验证 method/input")

    return EffectiveTrialEvidence(
        effective_trial_count=outcome.effective_trial_count,
        effective_trial_count_status=EvidenceStatus(outcome.state, outcome.reason_code),
        effective_trial_method=method_spec.method_id if method_spec is not None else None,
        effective_trial_method_version=method_spec.method_version if method_spec is not None else None,
        effective_trial_method_hash=method_spec.method_hash if method_spec is not None else None,
        effective_trial_input_lineage_ref=input_lineage_ref,
        effective_trial_computation_ref=build_computation_identity(attempt_basis),
    )


def canonical_evidence_bytes(evidence: EffectiveTrialEvidence | Mapping[str, Any]) -> bytes:
    mapping = evidence.as_mapping() if isinstance(evidence, EffectiveTrialEvidence) else evidence
    if not isinstance(mapping, Mapping):
        raise EvidenceContractError("evidence 必须是 EffectiveTrialEvidence 或 mapping")
    _validate_evidence_values(mapping)
    return canonical_bytes(mapping)


def canonical_evidence_hash(evidence: EffectiveTrialEvidence | Mapping[str, Any]) -> str:
    return _domain_hash(_EVIDENCE_DOMAIN, canonical_evidence_bytes(evidence))


@dataclass(frozen=True, slots=True)
class ComputationAttemptAudit:
    attempt_audit_ref: str
    verification_run_ref: str
    synthetic_case_id: str
    attempt_ordinal: int
    effective_trial_computation_ref: str
    canonical_evidence_hash: str
    state: str
    reason_code: str
    parent_attempt_audit_ref: str | None
    supersedes_attempt_audit_ref: str | None
    diagnostic_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "diagnostic_codes", tuple(self.diagnostic_codes))
        _require_hash_ref(self.attempt_audit_ref, "attempt_audit_ref")
        _require_non_empty(self.verification_run_ref, "verification_run_ref")
        _require_non_empty(self.synthetic_case_id, "synthetic_case_id")
        if (
            isinstance(self.attempt_ordinal, bool)
            or not isinstance(self.attempt_ordinal, int)
            or self.attempt_ordinal < 1
        ):
            raise EvidenceContractError("attempt_ordinal 必须是正整数")
        _require_hash_ref(self.effective_trial_computation_ref, "computation ref")
        _require_hash_ref(self.canonical_evidence_hash, "evidence hash")
        EvidenceStatus(self.state, self.reason_code)
        if (self.parent_attempt_audit_ref is None) != (
            self.supersedes_attempt_audit_ref is None
        ):
            raise EvidenceContractError("parent/supersedes 必须同时存在或同时为空")
        if (
            self.parent_attempt_audit_ref is not None
            and self.parent_attempt_audit_ref != self.supersedes_attempt_audit_ref
        ):
            raise EvidenceContractError("parent/supersedes 必须指向同一旧 attempt")
        for value in (self.parent_attempt_audit_ref, self.supersedes_attempt_audit_ref):
            if value is not None:
                _require_hash_ref(value, "audit recovery ref")
        if len(set(self.diagnostic_codes)) != len(self.diagnostic_codes):
            raise EvidenceContractError("diagnostic_codes 不得重复")
        if any(_DIAGNOSTIC_CODE.fullmatch(code) is None for code in self.diagnostic_codes):
            raise EvidenceContractError("diagnostic_codes 只能使用安全枚举")
        _validate_attempt_audit_identity(self)

    def identity_mapping(self) -> FrozenMapping:
        return FrozenMapping(
            {
                "verification_run_ref": self.verification_run_ref,
                "synthetic_case_id": self.synthetic_case_id,
                "attempt_ordinal": self.attempt_ordinal,
                "effective_trial_computation_ref": self.effective_trial_computation_ref,
                "canonical_evidence_hash": self.canonical_evidence_hash,
                "parent_attempt_audit_ref": self.parent_attempt_audit_ref,
                "supersedes_attempt_audit_ref": self.supersedes_attempt_audit_ref,
            }
        )


def _attempt_audit_ref(identity: Mapping[str, Any]) -> str:
    return _domain_hash(_AUDIT_DOMAIN, canonical_bytes(identity))


def _validate_attempt_audit_identity(entry: ComputationAttemptAudit) -> None:
    expected_ref = _attempt_audit_ref(entry.identity_mapping())
    if entry.attempt_audit_ref != expected_ref:
        raise EvidenceContractError("audit ref 与 content-addressed identity 不一致")


def build_attempt_audit(
    *,
    verification_run_ref: str,
    synthetic_case_id: str,
    attempt_ordinal: int,
    evidence: EffectiveTrialEvidence,
    parent_attempt_audit_ref: str | None = None,
    supersedes_attempt_audit_ref: str | None = None,
    diagnostic_codes: Sequence[str] = (),
) -> ComputationAttemptAudit:
    status = evidence.effective_trial_count_status
    identity = FrozenMapping(
        {
            "verification_run_ref": verification_run_ref,
            "synthetic_case_id": synthetic_case_id,
            "attempt_ordinal": attempt_ordinal,
            "effective_trial_computation_ref": evidence.effective_trial_computation_ref,
            "canonical_evidence_hash": canonical_evidence_hash(evidence),
            "parent_attempt_audit_ref": parent_attempt_audit_ref,
            "supersedes_attempt_audit_ref": supersedes_attempt_audit_ref,
        }
    )
    audit_ref = _attempt_audit_ref(identity)
    return ComputationAttemptAudit(
        attempt_audit_ref=audit_ref,
        verification_run_ref=verification_run_ref,
        synthetic_case_id=synthetic_case_id,
        attempt_ordinal=attempt_ordinal,
        effective_trial_computation_ref=evidence.effective_trial_computation_ref,
        canonical_evidence_hash=canonical_evidence_hash(evidence),
        state=status.state,
        reason_code=status.reason_code,
        parent_attempt_audit_ref=parent_attempt_audit_ref,
        supersedes_attempt_audit_ref=supersedes_attempt_audit_ref,
        diagnostic_codes=tuple(diagnostic_codes),
    )


def _validate_audit_sequence(entries: tuple[ComputationAttemptAudit, ...]) -> None:
    seen_by_ref: dict[str, ComputationAttemptAudit] = {}
    seen_keys: set[tuple[str, str, int]] = set()
    superseded_refs: set[str] = set()
    for entry in entries:
        if not isinstance(entry, ComputationAttemptAudit):
            raise EvidenceContractError("audit log 只接受 ComputationAttemptAudit")
        # 即使对象来自绕过 dataclass 构造器的反序列化，接纳边界也必须独立复算。
        _validate_attempt_audit_identity(entry)
        key = (entry.verification_run_ref, entry.synthetic_case_id, entry.attempt_ordinal)
        if entry.attempt_audit_ref in seen_by_ref or key in seen_keys:
            raise EvidenceContractError("append-only audit log 含重复 identity")
        recovery_ref = entry.parent_attempt_audit_ref
        if recovery_ref is not None:
            target = seen_by_ref.get(recovery_ref)
            if target is None:
                raise EvidenceContractError("recovery audit 不得包含 orphan/forward ref")
            if (
                target.verification_run_ref != entry.verification_run_ref
                or target.synthetic_case_id != entry.synthetic_case_id
            ):
                raise EvidenceContractError("recovery audit 必须保持同一 run/case 链")
            if recovery_ref in superseded_refs:
                raise EvidenceContractError("recovery audit 不得从已 supersede 的 attempt 分叉")
            superseded_refs.add(recovery_ref)
        seen_by_ref[entry.attempt_audit_ref] = entry
        seen_keys.add(key)


@dataclass(frozen=True, slots=True)
class AttemptAuditLog:
    """不可覆盖的 repository-local in-memory audit collection。"""

    entries: tuple[ComputationAttemptAudit, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        _validate_audit_sequence(self.entries)

    def append(self, entry: ComputationAttemptAudit) -> "AttemptAuditLog":
        candidate = self.entries + (entry,)
        _validate_audit_sequence(candidate)
        return AttemptAuditLog(candidate)


__all__ = [
    "ATTEMPT_BASIS_SCHEMA",
    "AttemptAuditLog",
    "CanonicalDecimal",
    "CanonicalNumberToken",
    "CanonicalizationError",
    "ComputationAttemptAudit",
    "ContractValidation",
    "DEPENDENCY_MATRIX_SCHEMA",
    "DependencyMatrixEnvelope",
    "EVIDENCE_SCHEMA",
    "EffectiveTrialAttemptBasisV1",
    "EffectiveTrialEvidence",
    "EffectiveTrialMethodSpec",
    "EvidenceContractError",
    "EvidenceStatus",
    "FAILURE_BY_ID",
    "FAILURE_DEFINITIONS",
    "FrozenMapping",
    "METHOD_ID",
    "METHOD_VERSION",
    "SOURCE_MODE_DECLARED_EXACT",
    "SealedTrialIdentity",
    "ValidatedContractBundle",
    "ValidationOutcome",
    "approved_method_descriptor",
    "build_approved_method_spec",
    "build_attempt_audit",
    "build_attempt_basis_v1",
    "build_computation_identity",
    "build_effective_trial_evidence",
    "build_failure_attempt_basis",
    "canonical_bytes",
    "canonical_component_digest",
    "canonical_dependency_input_hash",
    "canonical_evidence_bytes",
    "canonical_evidence_hash",
    "canonical_method_spec_hash",
    "canonical_sealed_identity_hash",
    "failure_outcome",
    "present_outcome",
    "render_half_even_number_token",
    "validate_canonical_decimal_token",
    "validate_contract_bundle",
]
