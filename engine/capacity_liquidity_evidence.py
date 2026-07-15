"""CR-169 的 fixture/static-only C4 容量与流动性证据合同。

本模块只处理调用方显式传入的不可变值对象。所有引用均为 opaque string，
不会读取文件、环境、凭据、provider、NAS、数据湖或外部运行时。S01 只负责
规范化、校验、13 字段关联头以及 component semantic hash；实际计算与 producer
编排由 S02 实现。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any

from engine.capacity_liquidity_calculator import (
    CapacityLiquidityBreakdownV1,
    CapacityLiquidityCalculationError,
    calculate_capacity_liquidity_breakdown,
)
from engine.strategy_evidence import EvidenceAvailability, canonical_hash, canonical_json_value


CAPACITY_LIQUIDITY_COMPONENT_TYPE = "capacity_liquidity"
CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION = "v1"
CAPACITY_LIQUIDITY_INPUT_HASH_DOMAIN = "quant-lab.capacity-liquidity-input.v1"
CAPACITY_LIQUIDITY_COMPONENT_HASH_DOMAIN = "quant-lab.capacity-liquidity-component.v1"
CAPACITY_LIQUIDITY_REF_HASH_DOMAIN = "quant-lab.capacity-liquidity-ref.v1"
CAPACITY_LIQUIDITY_METHOD = "static_adv_cap_v1"

CORRELATION_HEADER_FIELDS = (
    "manifest_ref",
    "run_ref",
    "strategy_ref",
    "package_ref",
    "price_basis",
    "notional_basis",
    "currency",
    "calendar",
    "as_of",
    "horizon_start",
    "horizon_end",
    "lineage_context_ref",
    "authorization_context_ref",
)

C4_REASON_CODES = (
    "c4_identity_binding_missing",
    "c4_static_liquidity_basis_missing",
    "c4_proxy_model_version_missing",
    "c4_nonfinite_numeric_invalid",
    "c4_negative_or_participation_cap_invalid",
    "c4_unit_currency_basis_mismatch",
    "c4_calendar_temporal_mismatch",
    "c4_c3_c4_correlation_header_mismatch",
    "c4_lineage_provenance_authorization_missing_or_mismatch",
    "c4_component_or_envelope_hash_tampered",
    "c4_gate4_ref_not_typed_present",
    "c4_projection_reason_escape_or_postcondition_violation",
)


class CapacityLiquidityIssueEffect(str, Enum):
    """输入问题对 producer availability 的确定性影响。"""

    TYPED_UNAVAILABLE = EvidenceAvailability.TYPED_UNAVAILABLE.value
    BLOCKED = EvidenceAvailability.BLOCKED.value


@dataclass(frozen=True, slots=True)
class CapacityLiquidityIssue:
    """不可变、按 N01..N12 稳定排序的 C4 问题。"""

    code: str
    field: str
    message: str
    effect: CapacityLiquidityIssueEffect

    def __post_init__(self) -> None:
        if self.code not in C4_REASON_CODES:
            raise ValueError(f"unknown C4 reason code: {self.code}")

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "effect": self.effect.value,
        }


@dataclass(frozen=True, slots=True)
class C3C4CorrelationHeaderV1:
    """C3/C4 join 的精确 13 字段静态 header。"""

    manifest_ref: str
    run_ref: str
    strategy_ref: str
    package_ref: str
    price_basis: str
    notional_basis: str
    currency: str
    calendar: str
    as_of: str
    horizon_start: str
    horizon_end: str
    lineage_context_ref: str
    authorization_context_ref: str

    def to_dict(self) -> dict[str, str]:
        data = asdict(self)
        if tuple(data) != CORRELATION_HEADER_FIELDS:
            raise AssertionError("C3C4CorrelationHeaderV1 field order drifted")
        return data


@dataclass(frozen=True, slots=True)
class CapacityLiquidityAttachmentContext:
    """只参与 envelope binding、不进入 component semantic hash 的 identity。"""

    manifest_ref: str
    run_ref: str
    strategy_ref: str
    package_ref: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CapacityLiquidityEvidenceInput:
    """C4 v1 的显式 synthetic/static typed input。"""

    # attachment identity；排除于 component semantic hash。
    manifest_ref: str = ""
    run_ref: str = ""
    strategy_ref: str = ""
    package_ref: str = ""
    # correlation/basis/temporal header。
    price_basis: str = ""
    notional_basis: str = ""
    currency: str = ""
    calendar: str = ""
    as_of: str = ""
    horizon_start: str = ""
    horizon_end: str = ""
    lineage_context_ref: str = ""
    authorization_context_ref: str = ""
    # synthetic/static calculation body。
    synthetic_adv: Decimal | int | str | float | None = None
    requested_notional: Decimal | int | str | float | None = None
    turnover_notional: Decimal | int | str | float | None = None
    participation_cap: Decimal | int | str | float | None = None
    currency_minor_unit: Decimal | int | str | float | None = None
    method: str = CAPACITY_LIQUIDITY_METHOD
    model_version: str = ""
    # 可选交叉声明；若给出必须与主 basis 完全一致，不支持隐式转换。
    liquidity_currency: str = ""
    liquidity_calendar: str = ""
    liquidity_price_basis: str = ""
    liquidity_notional_basis: str = ""
    lineage_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    authorization_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    no_real_adv_claim: bool = True
    no_real_liquidity_claim: bool = True
    no_capacity_ready_claim: bool = True
    claimed_semantic_hash: str = ""
    schema_version: str = CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class NormalizedCapacityLiquidityInputV1:
    """规范化后的 subject-neutral computational body。"""

    synthetic_adv: Decimal | None
    requested_notional: Decimal | None
    turnover_notional: Decimal | None
    participation_cap: Decimal | None
    currency_minor_unit: Decimal | None
    method: str
    model_version: str
    price_basis: str
    notional_basis: str
    currency: str
    calendar: str
    as_of: str
    horizon_start: str
    horizon_end: str
    lineage_context_ref: str
    authorization_context_ref: str
    liquidity_currency: str
    liquidity_calendar: str
    liquidity_price_basis: str
    liquidity_notional_basis: str
    lineage_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    authorization_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    no_real_adv_claim: bool
    no_real_liquidity_claim: bool
    no_capacity_ready_claim: bool
    claimed_semantic_hash: str
    schema_version: str
    normalization_invalid_fields: tuple[str, ...] = ()

    def semantic_projection(self) -> dict[str, Any]:
        """返回 component hash 输入域；四个 attachment identity 不在其中。"""

        return {
            "component_type": CAPACITY_LIQUIDITY_COMPONENT_TYPE,
            "schema_version": self.schema_version,
            "method": {"family": self.method, "version": self.model_version},
            "static_liquidity": {
                "synthetic_adv": _decimal_text(self.synthetic_adv),
                "requested_notional": _decimal_text(self.requested_notional),
                "turnover_notional": _decimal_text(self.turnover_notional),
                "participation_cap": _decimal_text(self.participation_cap),
            },
            "basis": {
                "price_basis": self.price_basis,
                "notional_basis": self.notional_basis,
                "currency": self.currency,
                "currency_minor_unit": _decimal_text(self.currency_minor_unit),
                "calendar": self.calendar,
            },
            "temporal": {
                "as_of": self.as_of,
                "horizon_start": self.horizon_start,
                "horizon_end": self.horizon_end,
            },
            "audit": {
                "lineage_context_ref": self.lineage_context_ref,
                "authorization_context_ref": self.authorization_context_ref,
                "lineage_refs": list(self.lineage_refs),
                "provenance_refs": list(self.provenance_refs),
                "authorization_refs": list(self.authorization_refs),
                "limitations": list(self.limitations),
                "no_real_adv_claim": self.no_real_adv_claim,
                "no_real_liquidity_claim": self.no_real_liquidity_claim,
                "no_capacity_ready_claim": self.no_capacity_ready_claim,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(self.semantic_projection())


@dataclass(frozen=True, slots=True)
class CapacityLiquidityValidation:
    availability: EvidenceAvailability
    issues: tuple[CapacityLiquidityIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "availability": self.availability.value,
            "issues": [item.to_dict() for item in self.issues],
        }


@dataclass(frozen=True, slots=True)
class CapacityLiquidityValidationResult:
    """S01 到 S02 的唯一 typed 四元交接。"""

    normalized_input: NormalizedCapacityLiquidityInputV1
    attachment_context: CapacityLiquidityAttachmentContext
    header: C3C4CorrelationHeaderV1
    issues: tuple[CapacityLiquidityIssue, ...]

    @property
    def availability(self) -> EvidenceAvailability:
        if any(item.effect is CapacityLiquidityIssueEffect.BLOCKED for item in self.issues):
            return EvidenceAvailability.BLOCKED
        if self.issues:
            return EvidenceAvailability.TYPED_UNAVAILABLE
        return EvidenceAvailability.PRESENT


@dataclass(frozen=True, slots=True)
class CapacityLiquidityRefPayloadV1:
    """三个 Gate4 logical ref 的 content-addressed payload。"""

    kind: str
    method: str
    model_version: str
    semantic_input_hash: str
    value: dict[str, Any]
    basis: dict[str, Any]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(
            {
                "kind": self.kind,
                "method": self.method,
                "model_version": self.model_version,
                "semantic_input_hash": self.semantic_input_hash,
                "value": self.value,
                "basis": self.basis,
                "limitations": list(self.limitations),
            }
        )

    @property
    def ref(self) -> str:
        return canonical_hash(self.to_dict(), domain=CAPACITY_LIQUIDITY_REF_HASH_DOMAIN)


@dataclass(frozen=True, slots=True)
class CapacityLiquidityEvidenceV1:
    """subject-neutral C4 typed component；S03 才负责 attach 到 envelope。"""

    component_type: str
    component_schema_version: str
    semantic_input_hash: str
    component_hash: str
    component_ref: str
    breakdown: CapacityLiquidityBreakdownV1
    adv_participation_ref: str
    capacity_dollars_ref: str
    liquidity_sizing_refs: tuple[str, ...]
    ref_payloads: tuple[CapacityLiquidityRefPayloadV1, ...]
    limitations: tuple[str, ...]
    real_adv_available: bool = False
    real_liquidity_available: bool = False
    capacity_ready: bool = False
    alpha_decay_calculator: int = 0
    availability: EvidenceAvailability = EvidenceAvailability.PRESENT

    def unsigned_dict(self) -> dict[str, Any]:
        return canonical_json_value(
            {
                "component_type": self.component_type,
                "component_schema_version": self.component_schema_version,
                "semantic_input_hash": self.semantic_input_hash,
                "breakdown": self.breakdown.to_dict(),
                "adv_participation_ref": self.adv_participation_ref,
                "capacity_dollars_ref": self.capacity_dollars_ref,
                "liquidity_sizing_refs": list(self.liquidity_sizing_refs),
                "ref_payloads": [item.to_dict() for item in self.ref_payloads],
                "limitations": list(self.limitations),
                "real_adv_available": self.real_adv_available,
                "real_liquidity_available": self.real_liquidity_available,
                "capacity_ready": self.capacity_ready,
                "alpha_decay_calculator": self.alpha_decay_calculator,
                "availability": self.availability.value,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        data = self.unsigned_dict()
        data.update({"component_hash": self.component_hash, "component_ref": self.component_ref})
        return canonical_json_value(data)


@dataclass(frozen=True, slots=True)
class CapacityLiquidityBuildResult:
    availability: EvidenceAvailability
    evidence: CapacityLiquidityEvidenceV1 | None
    issues: tuple[CapacityLiquidityIssue, ...]
    attachment_context: CapacityLiquidityAttachmentContext
    header: C3C4CorrelationHeaderV1
    calculator_invocations: int

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT and self.evidence is not None

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(
            {
                "availability": self.availability.value,
                "evidence": None if self.evidence is None else self.evidence.to_dict(),
                "issues": [item.to_dict() for item in self.issues],
                "attachment_context": self.attachment_context.to_dict(),
                "header": self.header.to_dict(),
                "calculator_invocations": self.calculator_invocations,
            }
        )


def normalize_capacity_liquidity_input(
    raw: CapacityLiquidityEvidenceInput,
) -> tuple[NormalizedCapacityLiquidityInputV1, CapacityLiquidityAttachmentContext, C3C4CorrelationHeaderV1]:
    """规范化 typed input；解析失败被记录并由 N04 fail-closed。"""

    if not isinstance(raw, CapacityLiquidityEvidenceInput):
        raise TypeError("raw must be CapacityLiquidityEvidenceInput")
    invalid_fields: list[str] = []

    def decimal_field(name: str, value: Any) -> Decimal | None:
        result, invalid = _normalize_decimal(value)
        if invalid:
            invalid_fields.append(name)
        return result

    attachment = CapacityLiquidityAttachmentContext(
        manifest_ref=_clean_text(raw.manifest_ref),
        run_ref=_clean_text(raw.run_ref),
        strategy_ref=_clean_text(raw.strategy_ref),
        package_ref=_clean_text(raw.package_ref),
    )
    header = C3C4CorrelationHeaderV1(
        manifest_ref=attachment.manifest_ref,
        run_ref=attachment.run_ref,
        strategy_ref=attachment.strategy_ref,
        package_ref=attachment.package_ref,
        price_basis=_clean_text(raw.price_basis),
        notional_basis=_clean_text(raw.notional_basis),
        currency=_clean_text(raw.currency),
        calendar=_clean_text(raw.calendar),
        as_of=_clean_text(raw.as_of),
        horizon_start=_clean_text(raw.horizon_start),
        horizon_end=_clean_text(raw.horizon_end),
        lineage_context_ref=_clean_text(raw.lineage_context_ref),
        authorization_context_ref=_clean_text(raw.authorization_context_ref),
    )
    normalized = NormalizedCapacityLiquidityInputV1(
        synthetic_adv=decimal_field("synthetic_adv", raw.synthetic_adv),
        requested_notional=decimal_field("requested_notional", raw.requested_notional),
        turnover_notional=decimal_field("turnover_notional", raw.turnover_notional),
        participation_cap=decimal_field("participation_cap", raw.participation_cap),
        currency_minor_unit=decimal_field("currency_minor_unit", raw.currency_minor_unit),
        method=_clean_text(raw.method),
        model_version=_clean_text(raw.model_version),
        price_basis=header.price_basis,
        notional_basis=header.notional_basis,
        currency=header.currency,
        calendar=header.calendar,
        as_of=header.as_of,
        horizon_start=header.horizon_start,
        horizon_end=header.horizon_end,
        lineage_context_ref=header.lineage_context_ref,
        authorization_context_ref=header.authorization_context_ref,
        liquidity_currency=_clean_text(raw.liquidity_currency),
        liquidity_calendar=_clean_text(raw.liquidity_calendar),
        liquidity_price_basis=_clean_text(raw.liquidity_price_basis),
        liquidity_notional_basis=_clean_text(raw.liquidity_notional_basis),
        lineage_refs=_clean_refs(raw.lineage_refs),
        provenance_refs=_clean_refs(raw.provenance_refs),
        authorization_refs=_clean_refs(raw.authorization_refs),
        limitations=_clean_refs(raw.limitations),
        no_real_adv_claim=raw.no_real_adv_claim is True,
        no_real_liquidity_claim=raw.no_real_liquidity_claim is True,
        no_capacity_ready_claim=raw.no_capacity_ready_claim is True,
        claimed_semantic_hash=_clean_text(raw.claimed_semantic_hash),
        schema_version=_clean_text(raw.schema_version),
        normalization_invalid_fields=tuple(sorted(set(invalid_fields))),
    )
    return normalized, attachment, header


def validate_capacity_liquidity_input(
    value: NormalizedCapacityLiquidityInputV1,
    *,
    attachment_context: CapacityLiquidityAttachmentContext | None = None,
    header: C3C4CorrelationHeaderV1 | None = None,
) -> CapacityLiquidityValidation:
    """按 N01..N10 校验 producer 输入；N11/N12 由 S04 共用同一枚举。"""

    if not isinstance(value, NormalizedCapacityLiquidityInputV1):
        raise TypeError("value must be NormalizedCapacityLiquidityInputV1")
    issues: list[CapacityLiquidityIssue] = []
    if attachment_context is not None and any(not item for item in attachment_context.to_dict().values()):
        issues.append(_issue("c4_identity_binding_missing", "attachment_identity", "All four attachment identity refs are required.", CapacityLiquidityIssueEffect.TYPED_UNAVAILABLE))
    static_values = (value.synthetic_adv, value.requested_notional, value.turnover_notional, value.participation_cap)
    if any(item is None for item in static_values):
        issues.append(_issue("c4_static_liquidity_basis_missing", "static_liquidity", "Synthetic ADV, requested/turnover notional and participation cap are required.", CapacityLiquidityIssueEffect.TYPED_UNAVAILABLE))
    if value.method != CAPACITY_LIQUIDITY_METHOD or not value.model_version or value.schema_version != CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION:
        issues.append(_issue("c4_proxy_model_version_missing", "method_version", "v1 requires static_adv_cap_v1 with an explicit model version.", CapacityLiquidityIssueEffect.TYPED_UNAVAILABLE))
    if value.normalization_invalid_fields:
        issues.append(_issue("c4_nonfinite_numeric_invalid", ",".join(value.normalization_invalid_fields), "Only finite Decimal-compatible integer, Decimal or decimal-string values are accepted.", CapacityLiquidityIssueEffect.BLOCKED))
    if (
        (value.synthetic_adv is not None and value.synthetic_adv <= 0)
        or (value.requested_notional is not None and value.requested_notional < 0)
        or (value.turnover_notional is not None and value.turnover_notional < 0)
        or (value.participation_cap is not None and not (Decimal("0") < value.participation_cap <= Decimal("1")))
    ):
        issues.append(_issue("c4_negative_or_participation_cap_invalid", "static_liquidity", "Synthetic ADV must be positive, notionals non-negative and participation cap in (0, 1].", CapacityLiquidityIssueEffect.BLOCKED))
    if (
        not value.currency
        or value.currency_minor_unit is None
        or value.currency_minor_unit <= 0
        or not value.price_basis
        or not value.notional_basis
        or (value.liquidity_currency and value.liquidity_currency != value.currency)
        or (value.liquidity_price_basis and value.liquidity_price_basis != value.price_basis)
        or (value.liquidity_notional_basis and value.liquidity_notional_basis != value.notional_basis)
    ):
        issues.append(_issue("c4_unit_currency_basis_mismatch", "unit_currency_basis", "Currency/minor unit and price/notional bases must be explicit and consistent.", CapacityLiquidityIssueEffect.BLOCKED))
    if (
        not value.calendar
        or (value.liquidity_calendar and value.liquidity_calendar != value.calendar)
        or not _valid_temporal_order(value.horizon_start, value.horizon_end, value.as_of)
    ):
        issues.append(_issue("c4_calendar_temporal_mismatch", "calendar_temporal", "Calendar and horizon_start <= horizon_end <= as_of must be explicit and consistent.", CapacityLiquidityIssueEffect.BLOCKED))
    if header is not None:
        header_issues = _validate_single_header(header)
        issues.extend(header_issues)
    if (
        not value.lineage_context_ref
        or not value.authorization_context_ref
        or not value.lineage_refs
        or not value.provenance_refs
        or not value.authorization_refs
    ):
        issues.append(_issue("c4_lineage_provenance_authorization_missing_or_mismatch", "lineage_provenance_authorization", "Lineage, provenance and authorization contexts/refs are required.", CapacityLiquidityIssueEffect.TYPED_UNAVAILABLE))
    if not value.no_real_adv_claim or not value.no_real_liquidity_claim or not value.no_capacity_ready_claim:
        issues.append(_issue("c4_lineage_provenance_authorization_missing_or_mismatch", "claim_boundary", "v1 requires all no-real/no-ready claim boundaries.", CapacityLiquidityIssueEffect.BLOCKED))
    if value.claimed_semantic_hash and not value.normalization_invalid_fields:
        try:
            if value.claimed_semantic_hash != capacity_liquidity_semantic_hash(value):
                issues.append(_issue("c4_component_or_envelope_hash_tampered", "claimed_semantic_hash", "Claimed semantic hash does not match canonical input semantics.", CapacityLiquidityIssueEffect.BLOCKED))
        except (TypeError, ValueError):
            issues.append(_issue("c4_component_or_envelope_hash_tampered", "claimed_semantic_hash", "Semantic hash cannot be canonicalized.", CapacityLiquidityIssueEffect.BLOCKED))
    return _validation_from_issues(issues)


def prepare_capacity_liquidity_validation(raw: CapacityLiquidityEvidenceInput) -> CapacityLiquidityValidationResult:
    """组装 S01 typed 四元；S02 必须先消费此结果并 short-circuit issues。"""

    normalized, attachment, header = normalize_capacity_liquidity_input(raw)
    # 单个 producer 输入的缺失字段由 N01/N06/N07/N09 精确归类；N08 只在
    # 显式 C3/C4 join 时产生，避免同一 identity 缺失被升级成不同原因。
    validation = validate_capacity_liquidity_input(normalized, attachment_context=attachment)
    return CapacityLiquidityValidationResult(normalized, attachment, header, validation.issues)


def build_capacity_liquidity_evidence(raw: CapacityLiquidityEvidenceInput) -> CapacityLiquidityBuildResult:
    """唯一 public producer：normalize→validate→short-circuit→calculate→produce。"""

    prepared = prepare_capacity_liquidity_validation(raw)
    if prepared.issues:
        return CapacityLiquidityBuildResult(
            availability=prepared.availability,
            evidence=None,
            issues=prepared.issues,
            attachment_context=prepared.attachment_context,
            header=prepared.header,
            calculator_invocations=0,
        )
    try:
        breakdown = calculate_capacity_liquidity_breakdown(prepared.normalized_input)
    except CapacityLiquidityCalculationError as exc:
        issue = _issue(exc.code, exc.field, exc.message, CapacityLiquidityIssueEffect.BLOCKED)
        return CapacityLiquidityBuildResult(
            availability=EvidenceAvailability.BLOCKED,
            evidence=None,
            issues=(issue,),
            attachment_context=prepared.attachment_context,
            header=prepared.header,
            calculator_invocations=1,
        )
    if not breakdown.within_declared_cap:
        issue = _issue(
            "c4_negative_or_participation_cap_invalid",
            "participation_ratio",
            "Requested notional exceeds the declared conservative fixture participation cap.",
            CapacityLiquidityIssueEffect.BLOCKED,
        )
        return CapacityLiquidityBuildResult(
            availability=EvidenceAvailability.BLOCKED,
            evidence=None,
            issues=(issue,),
            attachment_context=prepared.attachment_context,
            header=prepared.header,
            calculator_invocations=1,
        )

    semantic_input_hash = capacity_liquidity_semantic_hash(prepared.normalized_input)
    limitations = tuple(
        sorted(
            set(prepared.normalized_input.limitations)
            | {"fixture_static_only", "no_real_adv", "no_real_liquidity", "not_capacity_ready"}
        )
    )
    basis = {
        "currency": prepared.normalized_input.currency,
        "currency_minor_unit": _decimal_text(prepared.normalized_input.currency_minor_unit),
        "price_basis": prepared.normalized_input.price_basis,
        "notional_basis": prepared.normalized_input.notional_basis,
        "calendar": prepared.normalized_input.calendar,
        "as_of": prepared.normalized_input.as_of,
        "horizon_start": prepared.normalized_input.horizon_start,
        "horizon_end": prepared.normalized_input.horizon_end,
    }
    common = {
        "method": prepared.normalized_input.method,
        "model_version": prepared.normalized_input.model_version,
        "semantic_input_hash": semantic_input_hash,
        "basis": basis,
        "limitations": limitations,
    }
    participation_payload = CapacityLiquidityRefPayloadV1(
        kind="adv_participation",
        value={
            "participation_ratio": _decimal_text(breakdown.participation_ratio),
            "requested_notional": _decimal_text(breakdown.requested_notional),
            "synthetic_adv": _decimal_text(breakdown.synthetic_adv),
        },
        **common,
    )
    capacity_payload = CapacityLiquidityRefPayloadV1(
        kind="capacity_dollars",
        value={
            "capacity_amount": _decimal_text(breakdown.capacity_amount),
            "raw_capacity_amount": _decimal_text(breakdown.raw_capacity_amount),
            "declared_currency": prepared.normalized_input.currency,
        },
        **common,
    )
    sizing_payload = CapacityLiquidityRefPayloadV1(
        kind="liquidity_sizing",
        value={
            "requested_notional": _decimal_text(breakdown.requested_notional),
            "capacity_amount": _decimal_text(breakdown.capacity_amount),
            "liquidity_headroom": _decimal_text(breakdown.liquidity_headroom),
            "within_declared_cap": breakdown.within_declared_cap,
        },
        **common,
    )
    payloads = (participation_payload, capacity_payload, sizing_payload)
    provisional = CapacityLiquidityEvidenceV1(
        component_type=CAPACITY_LIQUIDITY_COMPONENT_TYPE,
        component_schema_version=CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION,
        semantic_input_hash=semantic_input_hash,
        component_hash="",
        component_ref="",
        breakdown=breakdown,
        adv_participation_ref=participation_payload.ref,
        capacity_dollars_ref=capacity_payload.ref,
        liquidity_sizing_refs=(sizing_payload.ref,),
        ref_payloads=payloads,
        limitations=limitations,
    )
    component_hash = capacity_liquidity_component_hash(provisional)
    evidence = CapacityLiquidityEvidenceV1(
        component_type=provisional.component_type,
        component_schema_version=provisional.component_schema_version,
        semantic_input_hash=provisional.semantic_input_hash,
        component_hash=component_hash,
        component_ref=f"fixture://capacity-liquidity/v1/{component_hash.removeprefix('sha256:')}",
        breakdown=provisional.breakdown,
        adv_participation_ref=provisional.adv_participation_ref,
        capacity_dollars_ref=provisional.capacity_dollars_ref,
        liquidity_sizing_refs=provisional.liquidity_sizing_refs,
        ref_payloads=provisional.ref_payloads,
        limitations=provisional.limitations,
    )
    self_validation = validate_capacity_liquidity_evidence(evidence)
    if not self_validation.passed:
        return CapacityLiquidityBuildResult(
            availability=EvidenceAvailability.BLOCKED,
            evidence=None,
            issues=self_validation.issues,
            attachment_context=prepared.attachment_context,
            header=prepared.header,
            calculator_invocations=1,
        )
    return CapacityLiquidityBuildResult(
        availability=EvidenceAvailability.PRESENT,
        evidence=evidence,
        issues=(),
        attachment_context=prepared.attachment_context,
        header=prepared.header,
        calculator_invocations=1,
    )


def capacity_liquidity_component_hash(evidence: CapacityLiquidityEvidenceV1) -> str:
    if not isinstance(evidence, CapacityLiquidityEvidenceV1):
        raise TypeError("evidence must be CapacityLiquidityEvidenceV1")
    return canonical_hash(evidence.unsigned_dict(), domain=CAPACITY_LIQUIDITY_COMPONENT_HASH_DOMAIN)


def validate_capacity_liquidity_evidence(
    evidence: CapacityLiquidityEvidenceV1,
) -> CapacityLiquidityValidation:
    """独立校验 present C4 component 的 schema、refs、claims 与 canonical identity。"""

    if not isinstance(evidence, CapacityLiquidityEvidenceV1):
        raise TypeError("evidence must be CapacityLiquidityEvidenceV1")
    issues: list[CapacityLiquidityIssue] = []
    if (
        evidence.component_type != CAPACITY_LIQUIDITY_COMPONENT_TYPE
        or evidence.component_schema_version != CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION
        or evidence.availability is not EvidenceAvailability.PRESENT
    ):
        issues.append(_issue("c4_component_or_envelope_hash_tampered", "component_identity", "Unexpected C4 component identity or availability.", CapacityLiquidityIssueEffect.BLOCKED))
    refs = (
        evidence.adv_participation_ref,
        evidence.capacity_dollars_ref,
        *evidence.liquidity_sizing_refs,
    )
    if not evidence.adv_participation_ref or not evidence.capacity_dollars_ref or len(evidence.liquidity_sizing_refs) != 1 or any(not ref for ref in refs):
        issues.append(_issue("c4_gate4_ref_not_typed_present", "gate4_refs", "Present C4 evidence requires exactly 3/3 typed logical refs.", CapacityLiquidityIssueEffect.BLOCKED))
    payload_refs = tuple(item.ref for item in evidence.ref_payloads)
    if len(payload_refs) != 3 or payload_refs != refs:
        issues.append(_issue("c4_component_or_envelope_hash_tampered", "ref_payloads", "Logical refs do not match content-addressed payloads.", CapacityLiquidityIssueEffect.BLOCKED))
    if (
        evidence.real_adv_available
        or evidence.real_liquidity_available
        or evidence.capacity_ready
        or evidence.alpha_decay_calculator != 0
        or not evidence.breakdown.within_declared_cap
    ):
        issues.append(_issue("c4_lineage_provenance_authorization_missing_or_mismatch", "claim_boundary", "C4 v1 must remain fixture/static-only, within cap and alpha-decay free.", CapacityLiquidityIssueEffect.BLOCKED))
    if evidence.component_hash != capacity_liquidity_component_hash(evidence):
        issues.append(_issue("c4_component_or_envelope_hash_tampered", "component_hash", "Component hash does not match canonical body.", CapacityLiquidityIssueEffect.BLOCKED))
    return _validation_from_issues(issues)


def validate_c3_c4_correlation_headers(
    c3_header: C3C4CorrelationHeaderV1,
    c4_header: C3C4CorrelationHeaderV1,
) -> CapacityLiquidityValidation:
    """对 13 个字段做 exact match；任何缺失、时序错误或 mismatch 均 BLOCKED。"""

    if not isinstance(c3_header, C3C4CorrelationHeaderV1) or not isinstance(c4_header, C3C4CorrelationHeaderV1):
        raise TypeError("both headers must be C3C4CorrelationHeaderV1")
    issues = list(_validate_single_header(c3_header)) + list(_validate_single_header(c4_header))
    for field_name in CORRELATION_HEADER_FIELDS:
        if getattr(c3_header, field_name) != getattr(c4_header, field_name):
            issues.append(_issue("c4_c3_c4_correlation_header_mismatch", field_name, f"C3/C4 correlation header mismatch: {field_name}.", CapacityLiquidityIssueEffect.BLOCKED))
    return _validation_from_issues(issues)


def capacity_liquidity_semantic_hash(value: NormalizedCapacityLiquidityInputV1) -> str:
    if not isinstance(value, NormalizedCapacityLiquidityInputV1):
        raise TypeError("value must be NormalizedCapacityLiquidityInputV1")
    return canonical_hash(value.semantic_projection(), domain=CAPACITY_LIQUIDITY_INPUT_HASH_DOMAIN)


def validate_capacity_liquidity_semantic_hash(
    value: NormalizedCapacityLiquidityInputV1,
    claimed_hash: str,
) -> CapacityLiquidityValidation:
    if not _clean_text(claimed_hash) or claimed_hash != capacity_liquidity_semantic_hash(value):
        return _validation_from_issues(
            [_issue("c4_component_or_envelope_hash_tampered", "claimed_semantic_hash", "Semantic hash mismatch.", CapacityLiquidityIssueEffect.BLOCKED)]
        )
    return CapacityLiquidityValidation(EvidenceAvailability.PRESENT)


def _validate_single_header(header: C3C4CorrelationHeaderV1) -> tuple[CapacityLiquidityIssue, ...]:
    data = header.to_dict()
    issues: list[CapacityLiquidityIssue] = []
    for field_name in CORRELATION_HEADER_FIELDS:
        if not _clean_text(data[field_name]):
            issues.append(_issue("c4_c3_c4_correlation_header_mismatch", field_name, f"Correlation header field is required: {field_name}.", CapacityLiquidityIssueEffect.BLOCKED))
    if not _valid_temporal_order(header.horizon_start, header.horizon_end, header.as_of):
        issues.append(_issue("c4_c3_c4_correlation_header_mismatch", "temporal", "Correlation header requires horizon_start <= horizon_end <= as_of.", CapacityLiquidityIssueEffect.BLOCKED))
    return _ordered_issues(issues)


def _normalize_decimal(value: Any) -> tuple[Decimal | None, bool]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, False
    if isinstance(value, bool) or isinstance(value, float):
        return None, True
    if not isinstance(value, (Decimal, int, str)):
        return None, True
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None, True
    if not result.is_finite():
        return None, True
    return result, False


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_refs(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = (values,)
    if not isinstance(values, (tuple, list)):
        return ()
    return tuple(sorted({text for item in values if (text := _clean_text(item))}))


def _valid_temporal_order(horizon_start: str, horizon_end: str, as_of: str) -> bool:
    try:
        start = date.fromisoformat(horizon_start)
        end = date.fromisoformat(horizon_end)
        observed = date.fromisoformat(as_of)
    except (TypeError, ValueError):
        return False
    return start <= end <= observed


def _issue(code: str, field: str, message: str, effect: CapacityLiquidityIssueEffect) -> CapacityLiquidityIssue:
    return CapacityLiquidityIssue(code=code, field=field, message=message, effect=effect)


_ISSUE_ORDER = {code: index for index, code in enumerate(C4_REASON_CODES, start=1)}


def _ordered_issues(issues: list[CapacityLiquidityIssue]) -> tuple[CapacityLiquidityIssue, ...]:
    return tuple(sorted(issues, key=lambda item: (_ISSUE_ORDER[item.code], item.field, item.message)))


def _validation_from_issues(issues: list[CapacityLiquidityIssue]) -> CapacityLiquidityValidation:
    ordered = _ordered_issues(issues)
    if any(item.effect is CapacityLiquidityIssueEffect.BLOCKED for item in ordered):
        return CapacityLiquidityValidation(EvidenceAvailability.BLOCKED, ordered)
    if ordered:
        return CapacityLiquidityValidation(EvidenceAvailability.TYPED_UNAVAILABLE, ordered)
    return CapacityLiquidityValidation(EvidenceAvailability.PRESENT)


__all__ = [
    "CAPACITY_LIQUIDITY_COMPONENT_HASH_DOMAIN",
    "CAPACITY_LIQUIDITY_COMPONENT_SCHEMA_VERSION",
    "CAPACITY_LIQUIDITY_COMPONENT_TYPE",
    "CAPACITY_LIQUIDITY_INPUT_HASH_DOMAIN",
    "CAPACITY_LIQUIDITY_REF_HASH_DOMAIN",
    "CAPACITY_LIQUIDITY_METHOD",
    "C4_REASON_CODES",
    "CORRELATION_HEADER_FIELDS",
    "C3C4CorrelationHeaderV1",
    "CapacityLiquidityAttachmentContext",
    "CapacityLiquidityBuildResult",
    "CapacityLiquidityEvidenceInput",
    "CapacityLiquidityEvidenceV1",
    "CapacityLiquidityIssue",
    "CapacityLiquidityIssueEffect",
    "CapacityLiquidityValidation",
    "CapacityLiquidityValidationResult",
    "CapacityLiquidityRefPayloadV1",
    "NormalizedCapacityLiquidityInputV1",
    "build_capacity_liquidity_evidence",
    "capacity_liquidity_component_hash",
    "capacity_liquidity_semantic_hash",
    "normalize_capacity_liquidity_input",
    "prepare_capacity_liquidity_validation",
    "validate_c3_c4_correlation_headers",
    "validate_capacity_liquidity_input",
    "validate_capacity_liquidity_evidence",
    "validate_capacity_liquidity_semantic_hash",
]
