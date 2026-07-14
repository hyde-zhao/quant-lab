"""CR-168 的 fixture/static C3 经济成本输入合同与校验。

本模块只处理调用方显式传入的值对象；不会读取文件、环境、凭据、数据湖、
provider 或 registry，也不会执行运行时或交易操作。计算五个成本分项和
构造 present evidence 属于 S02，故本模块在 S01 只提供其所需的纯合同、
规范化、校验和 subject-neutral semantic hash。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping

from engine.economic_cost_calculator import (
    CostBreakdownV1,
    EconomicCostCalculationError,
    calculate_cost_breakdown,
)
from engine.strategy_evidence import EvidenceAvailability, canonical_hash, canonical_json_value


ECONOMIC_COST_COMPONENT_TYPE = "economic_cost"
ECONOMIC_COST_COMPONENT_SCHEMA_VERSION = "v1"
ECONOMIC_COST_INPUT_HASH_DOMAIN = "quant-lab.economic-cost-input.v1"
ECONOMIC_COST_COMPONENT_HASH_DOMAIN = "quant-lab.economic-cost-component.v1"


class EconomicCostIssueEffect(str, Enum):
    """输入问题对 producer availability 的确定性影响。"""

    TYPED_UNAVAILABLE = EvidenceAvailability.TYPED_UNAVAILABLE.value
    BLOCKED = EvidenceAvailability.BLOCKED.value


@dataclass(frozen=True, slots=True)
class EconomicCostIssue:
    """不可变、可排序的 C3 输入问题。"""

    code: str
    field: str
    message: str
    effect: EconomicCostIssueEffect

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "effect": self.effect.value,
        }


@dataclass(frozen=True, slots=True)
class EconomicCostEvidenceInput:
    """显式的九字段族 raw typed input；不接受任意 mapping passthrough。"""

    # family 1: attachment identity，绝不进入 component semantic hash。
    manifest_ref: str = ""
    run_ref: str = ""
    strategy_ref: str = ""
    package_ref: str = ""
    # family 2: gross/pre-cost performance basis。
    gross_pnl: Decimal | int | str | float | None = None
    gross_return: Decimal | int | str | float | None = None
    performance_notional: Decimal | int | str | float | None = None
    # family 3: trade / position-change / turnover / notional basis。
    traded_notional: Decimal | int | str | float | None = None
    sell_notional: Decimal | int | str | float | None = None
    turnover: Decimal | int | str | float | None = None
    # families 4-7: fee / tax / spread / slippage assumptions。
    cost_model_version: str = ""
    fee_rate: Decimal | int | str | float | None = None
    fee_fixed_amount: Decimal | int | str | float | None = "0"
    tax_rate: Decimal | int | str | float | None = None
    tax_fixed_amount: Decimal | int | str | float | None = "0"
    effective_spread_rate: Decimal | int | str | float | None = None
    effective_slippage_rate: Decimal | int | str | float | None = None
    # family 8: static square-root impact assumption。
    impact_model_family: str = "square_root"
    impact_model_version: str = ""
    impact_model_ref: str = ""
    impact_coefficient: Decimal | int | str | float | None = None
    static_reference_notional: Decimal | int | str | float | None = None
    # family 9: units, temporal basis, lineage/provenance/authorization。
    currency: str = ""
    currency_minor_unit: Decimal | int | str | float | None = None
    calendar: str = ""
    price_basis: str = ""
    notional_basis: str = ""
    cost_currency: str = ""
    cost_calendar: str = ""
    cost_price_basis: str = ""
    cost_notional_basis: str = ""
    lineage_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    authorization_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    cost_underestimation_status: str = "PASS"
    no_real_tca_claim: bool = True
    # 可选的调用方声明值仅用于篡改检测；producer 自己不会信任它。
    claimed_semantic_hash: str = ""
    schema_version: str = ECONOMIC_COST_COMPONENT_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class EconomicCostAttachmentContext:
    """只在 envelope attachment 层使用的 family 1 identity。"""

    manifest_ref: str
    run_ref: str
    strategy_ref: str
    package_ref: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NormalizedEconomicCostInput:
    """normalizer 输出；无法规范化的数值保留为 None 并由 validator fail-closed。"""

    gross_pnl: Decimal | None
    gross_return: Decimal | None
    performance_notional: Decimal | None
    traded_notional: Decimal | None
    sell_notional: Decimal | None
    turnover: Decimal | None
    fee_rate: Decimal | None
    fee_fixed_amount: Decimal | None
    tax_rate: Decimal | None
    tax_fixed_amount: Decimal | None
    effective_spread_rate: Decimal | None
    effective_slippage_rate: Decimal | None
    impact_coefficient: Decimal | None
    static_reference_notional: Decimal | None
    currency_minor_unit: Decimal | None
    cost_model_version: str
    impact_model_family: str
    impact_model_version: str
    impact_model_ref: str
    currency: str
    calendar: str
    price_basis: str
    notional_basis: str
    cost_currency: str
    cost_calendar: str
    cost_price_basis: str
    cost_notional_basis: str
    lineage_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    authorization_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    cost_underestimation_status: str
    no_real_tca_claim: bool
    claimed_semantic_hash: str
    schema_version: str
    normalization_invalid_fields: tuple[str, ...] = ()

    def semantic_projection(self) -> dict[str, Any]:
        """返回 families 2-9 的稳定 JSON 子集，不含 attachment identity。"""

        return {
            "component_type": ECONOMIC_COST_COMPONENT_TYPE,
            "schema_version": self.schema_version,
            "performance": {
                "gross_pnl": _decimal_text(self.gross_pnl),
                "gross_return": _decimal_text(self.gross_return),
                "performance_notional": _decimal_text(self.performance_notional),
            },
            "trade": {
                "traded_notional": _decimal_text(self.traded_notional),
                "sell_notional": _decimal_text(self.sell_notional),
                "turnover": _decimal_text(self.turnover),
            },
            "fee": {
                "model_version": self.cost_model_version,
                "rate": _decimal_text(self.fee_rate),
                "fixed_amount": _decimal_text(self.fee_fixed_amount),
            },
            "tax": {
                "model_version": self.cost_model_version,
                "rate": _decimal_text(self.tax_rate),
                "fixed_amount": _decimal_text(self.tax_fixed_amount),
            },
            "spread": {"model_version": self.cost_model_version, "effective_rate": _decimal_text(self.effective_spread_rate)},
            "slippage": {"model_version": self.cost_model_version, "effective_rate": _decimal_text(self.effective_slippage_rate)},
            "impact": {
                "model_family": self.impact_model_family,
                "model_version": self.impact_model_version,
                "model_ref": self.impact_model_ref,
                "coefficient": _decimal_text(self.impact_coefficient),
                "static_reference_notional": _decimal_text(self.static_reference_notional),
            },
            "unit_and_lineage": {
                "currency": self.currency,
                "currency_minor_unit": _decimal_text(self.currency_minor_unit),
                "calendar": self.calendar,
                "price_basis": self.price_basis,
                "notional_basis": self.notional_basis,
                "lineage_refs": list(self.lineage_refs),
                "provenance_refs": list(self.provenance_refs),
                "authorization_refs": list(self.authorization_refs),
                "limitations": list(self.limitations),
                "cost_underestimation_status": self.cost_underestimation_status,
                "no_real_tca_claim": self.no_real_tca_claim,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """提供安全 JSON 值，防止 Decimal 或 tuple 绕过 canonical serializer。"""

        return canonical_json_value(self.semantic_projection())


@dataclass(frozen=True, slots=True)
class EconomicCostValidation:
    """validator 的 availability 与按 N01..N10 稳定排序的问题列表。"""

    availability: EvidenceAvailability
    issues: tuple[EconomicCostIssue, ...] = ()

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT

    def to_dict(self) -> dict[str, Any]:
        return {"availability": self.availability.value, "issues": [item.to_dict() for item in self.issues]}


@dataclass(frozen=True, slots=True)
class EconomicCostValidationResult:
    """S01 到 S02 的唯一 typed 三元交接对象。"""

    normalized_input: NormalizedEconomicCostInput
    attachment_context: EconomicCostAttachmentContext
    issues: tuple[EconomicCostIssue, ...]

    @property
    def availability(self) -> EvidenceAvailability:
        if any(item.effect is EconomicCostIssueEffect.BLOCKED for item in self.issues):
            return EvidenceAvailability.BLOCKED
        if self.issues:
            return EvidenceAvailability.TYPED_UNAVAILABLE
        return EvidenceAvailability.PRESENT


@dataclass(frozen=True, slots=True)
class EconomicCostEvidenceV1:
    """S02 产出的 subject-neutral C3 typed component；尚未 attach 到 envelope。"""

    component_type: str
    component_schema_version: str
    semantic_input_hash: str
    component_hash: str
    component_ref: str
    breakdown: CostBreakdownV1
    impact_model_family: str
    impact_model_ref: str
    cost_underestimation_status: str
    no_real_tca_claim: bool
    limitations: tuple[str, ...]
    availability: EvidenceAvailability = EvidenceAvailability.PRESENT

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "component_type": self.component_type,
            "component_schema_version": self.component_schema_version,
            "semantic_input_hash": self.semantic_input_hash,
            "breakdown": self.breakdown.to_dict(),
            "impact_model_family": self.impact_model_family,
            "impact_model_ref": self.impact_model_ref,
            "cost_underestimation_status": self.cost_underestimation_status,
            "no_real_tca_claim": self.no_real_tca_claim,
            "limitations": list(self.limitations),
            "availability": self.availability.value,
        }

    def to_dict(self) -> dict[str, Any]:
        data = self.unsigned_dict()
        data.update({"component_hash": self.component_hash, "component_ref": self.component_ref})
        return canonical_json_value(data)


@dataclass(frozen=True, slots=True)
class EconomicCostBuildResult:
    """唯一 public producer entry 的 typed outcome，不允许调用方跳过 S01。"""

    availability: EvidenceAvailability
    evidence: EconomicCostEvidenceV1 | None
    issues: tuple[EconomicCostIssue, ...]
    attachment_context: EconomicCostAttachmentContext
    calculator_invocations: int

    @property
    def passed(self) -> bool:
        return self.availability is EvidenceAvailability.PRESENT and self.evidence is not None

    def to_dict(self) -> dict[str, Any]:
        return canonical_json_value(
            {
                "availability": self.availability.value,
                "evidence": None if self.evidence is None else self.evidence.to_dict(),
                "issues": [issue.to_dict() for issue in self.issues],
                "attachment_context": self.attachment_context.to_dict(),
                "calculator_invocations": self.calculator_invocations,
            }
        )


def normalize_economic_cost_input(
    raw: EconomicCostEvidenceInput,
) -> tuple[NormalizedEconomicCostInput, EconomicCostAttachmentContext]:
    """规范化 typed input；所有数值格式失败延后给 validator 形成 N04。"""

    if not isinstance(raw, EconomicCostEvidenceInput):
        raise TypeError("raw must be EconomicCostEvidenceInput")
    invalid_fields: list[str] = []

    def decimal_field(name: str, value: Any) -> Decimal | None:
        result, invalid = _normalize_decimal(value)
        if invalid:
            invalid_fields.append(name)
        return result

    attachment = EconomicCostAttachmentContext(
        manifest_ref=_clean_text(raw.manifest_ref),
        run_ref=_clean_text(raw.run_ref),
        strategy_ref=_clean_text(raw.strategy_ref),
        package_ref=_clean_text(raw.package_ref),
    )
    normalized = NormalizedEconomicCostInput(
        gross_pnl=decimal_field("gross_pnl", raw.gross_pnl),
        gross_return=decimal_field("gross_return", raw.gross_return),
        performance_notional=decimal_field("performance_notional", raw.performance_notional),
        traded_notional=decimal_field("traded_notional", raw.traded_notional),
        sell_notional=decimal_field("sell_notional", raw.sell_notional),
        turnover=decimal_field("turnover", raw.turnover),
        fee_rate=decimal_field("fee_rate", raw.fee_rate),
        fee_fixed_amount=decimal_field("fee_fixed_amount", raw.fee_fixed_amount),
        tax_rate=decimal_field("tax_rate", raw.tax_rate),
        tax_fixed_amount=decimal_field("tax_fixed_amount", raw.tax_fixed_amount),
        effective_spread_rate=decimal_field("effective_spread_rate", raw.effective_spread_rate),
        effective_slippage_rate=decimal_field("effective_slippage_rate", raw.effective_slippage_rate),
        impact_coefficient=decimal_field("impact_coefficient", raw.impact_coefficient),
        static_reference_notional=decimal_field("static_reference_notional", raw.static_reference_notional),
        currency_minor_unit=decimal_field("currency_minor_unit", raw.currency_minor_unit),
        cost_model_version=_clean_text(raw.cost_model_version),
        impact_model_family=_clean_text(raw.impact_model_family),
        impact_model_version=_clean_text(raw.impact_model_version),
        impact_model_ref=_clean_text(raw.impact_model_ref),
        currency=_clean_text(raw.currency),
        calendar=_clean_text(raw.calendar),
        price_basis=_clean_text(raw.price_basis),
        notional_basis=_clean_text(raw.notional_basis),
        cost_currency=_clean_text(raw.cost_currency),
        cost_calendar=_clean_text(raw.cost_calendar),
        cost_price_basis=_clean_text(raw.cost_price_basis),
        cost_notional_basis=_clean_text(raw.cost_notional_basis),
        lineage_refs=_clean_refs(raw.lineage_refs),
        provenance_refs=_clean_refs(raw.provenance_refs),
        authorization_refs=_clean_refs(raw.authorization_refs),
        limitations=_clean_refs(raw.limitations),
        cost_underestimation_status=_clean_text(raw.cost_underestimation_status),
        no_real_tca_claim=raw.no_real_tca_claim is True,
        claimed_semantic_hash=_clean_text(raw.claimed_semantic_hash),
        schema_version=_clean_text(raw.schema_version),
        normalization_invalid_fields=tuple(sorted(set(invalid_fields))),
    )
    return normalized, attachment


def validate_economic_cost_input(value: NormalizedEconomicCostInput) -> EconomicCostValidation:
    """按 N01..N10 产出最少且稳定的 fail-closed 问题集合。"""

    if not isinstance(value, NormalizedEconomicCostInput):
        raise TypeError("value must be NormalizedEconomicCostInput")
    issues: list[EconomicCostIssue] = []
    # N01：gross/pre-cost performance basis。
    if (value.gross_pnl is None and value.gross_return is None) or not _positive(value.performance_notional):
        issues.append(_issue("c3_gross_performance_basis_missing", "performance", "Gross PnL or return and positive performance notional are required.", EconomicCostIssueEffect.TYPED_UNAVAILABLE))
    # N02：trade/turnover/notional basis。
    if value.traded_notional is None or value.sell_notional is None or value.turnover is None:
        issues.append(_issue("c3_trade_turnover_notional_basis_missing", "trade", "Trade, sell and turnover/notional basis are required.", EconomicCostIssueEffect.TYPED_UNAVAILABLE))
    # N03：v1 static model/version 与每个可计算分项的显式静态参数。
    # S02 只能消费 validation-clean input，因此不得把 None 形式的 rate /
    # coefficient / reference 留给 calculator 以异常或隐式默认值处理。
    required_static_assumptions = (
        value.fee_rate,
        value.fee_fixed_amount,
        value.tax_rate,
        value.tax_fixed_amount,
        value.effective_spread_rate,
        value.effective_slippage_rate,
        value.impact_coefficient,
        value.static_reference_notional,
    )
    if (
        not value.cost_model_version
        or value.impact_model_family != "square_root"
        or not value.impact_model_version
        or not value.impact_model_ref
        or any(item is None for item in required_static_assumptions)
    ):
        issues.append(
            _issue(
                "c3_cost_model_version_missing",
                "cost_model",
                "v1 requires explicit cost and square-root impact model/version/ref and all static itemized-cost assumptions.",
                EconomicCostIssueEffect.TYPED_UNAVAILABLE,
            )
        )
    # N04：拒绝 binary float、NaN、Infinity、不可解析字符串。
    if value.normalization_invalid_fields:
        issues.append(_issue("c3_nonfinite_numeric_invalid", ",".join(value.normalization_invalid_fields), "Only finite Decimal-compatible integer, Decimal or decimal-string values are accepted.", EconomicCostIssueEffect.BLOCKED))
    # N05：成本 rates/fixed amounts 与静态 reference 不允许负。
    cost_values = (
        value.traded_notional,
        value.sell_notional,
        value.turnover,
        value.fee_rate,
        value.fee_fixed_amount,
        value.tax_rate,
        value.tax_fixed_amount,
        value.effective_spread_rate,
        value.effective_slippage_rate,
        value.impact_coefficient,
        value.static_reference_notional,
    )
    if any(item is not None and item < 0 for item in cost_values):
        issues.append(_issue("c3_negative_cost_invalid", "cost_assumptions", "Cost assumptions, trade notionals and static reference must be non-negative.", EconomicCostIssueEffect.BLOCKED))
    # N06：单位、price 与 notional basis。
    if (
        not value.currency
        or not _positive(value.currency_minor_unit)
        or not value.price_basis
        or not value.notional_basis
        or (value.cost_price_basis and value.cost_price_basis != value.price_basis)
        or (value.cost_notional_basis and value.cost_notional_basis != value.notional_basis)
    ):
        issues.append(_issue("c3_unit_price_notional_basis_mismatch", "unit_price_notional_basis", "Currency/minor unit and price/notional bases must be explicit and consistent.", EconomicCostIssueEffect.BLOCKED))
    # N07：没有静态 conversion 契约的跨币种/跨 calendar 混用不允许。
    if (
        not value.calendar
        or (value.cost_currency and value.cost_currency != value.currency)
        or (value.cost_calendar and value.cost_calendar != value.calendar)
    ):
        issues.append(_issue("c3_currency_price_calendar_mismatch", "currency_calendar", "Currency and calendar must not mix across fields without an explicit supported conversion contract.", EconomicCostIssueEffect.BLOCKED))
    # N08：只校验调用方同时给出可交叉验证的静态算术声明。
    if (
        value.gross_pnl is not None
        and value.gross_return is not None
        and value.performance_notional is not None
        and value.gross_pnl != value.gross_return * value.performance_notional
    ):
        issues.append(_issue("c3_gross_cost_net_arithmetic_mismatch", "gross_performance", "Declared gross PnL and gross return do not reconcile to performance notional.", EconomicCostIssueEffect.BLOCKED))
    # N09：lineage/provenance/auth refs 只作 opaque strings，但三族均不可省略。
    if not value.lineage_refs or not value.provenance_refs or not value.authorization_refs:
        issues.append(_issue("c3_lineage_provenance_authorization_missing_or_mismatch", "lineage_provenance_authorization", "Lineage, provenance and authorization refs are all required opaque values.", EconomicCostIssueEffect.TYPED_UNAVAILABLE))
    if not value.no_real_tca_claim or value.cost_underestimation_status != "PASS":
        issues.append(_issue("c3_lineage_provenance_authorization_missing_or_mismatch", "authorization_claim", "v1 requires no_real_tca_claim=true and cost_underestimation_status=PASS for a present path.", EconomicCostIssueEffect.BLOCKED))
    # N10：只有其它输入可 canonicalize 时才比较调用方声明 hash。
    if value.claimed_semantic_hash and not value.normalization_invalid_fields:
        try:
            if value.claimed_semantic_hash != economic_cost_semantic_hash(value):
                issues.append(_issue("c3_component_hash_tampered", "claimed_semantic_hash", "Claimed semantic hash does not match canonical input semantics.", EconomicCostIssueEffect.BLOCKED))
        except (TypeError, ValueError):
            issues.append(_issue("c3_component_hash_tampered", "claimed_semantic_hash", "Semantic hash cannot be canonicalized.", EconomicCostIssueEffect.BLOCKED))
    ordered = _ordered_issues(issues)
    if any(item.effect is EconomicCostIssueEffect.BLOCKED for item in ordered):
        return EconomicCostValidation(EvidenceAvailability.BLOCKED, ordered)
    if ordered:
        return EconomicCostValidation(EvidenceAvailability.TYPED_UNAVAILABLE, ordered)
    return EconomicCostValidation(EvidenceAvailability.PRESENT)


def prepare_economic_cost_validation(raw: EconomicCostEvidenceInput) -> EconomicCostValidationResult:
    """组装 S01 typed 三元；S02 producer 必须消费这个精确形态。"""

    normalized, attachment = normalize_economic_cost_input(raw)
    validation = validate_economic_cost_input(normalized)
    return EconomicCostValidationResult(normalized, attachment, validation.issues)


def build_economic_cost_evidence(raw: EconomicCostEvidenceInput) -> EconomicCostBuildResult:
    """唯一 public producer entry：normalize→validate→short-circuit→calculate→produce。"""

    prepared = prepare_economic_cost_validation(raw)
    if prepared.issues:
        return EconomicCostBuildResult(
            availability=prepared.availability,
            evidence=None,
            issues=prepared.issues,
            attachment_context=prepared.attachment_context,
            calculator_invocations=0,
        )
    try:
        breakdown = calculate_cost_breakdown(prepared.normalized_input)
    except EconomicCostCalculationError as exc:
        issue = _issue(exc.code, exc.field, exc.message, EconomicCostIssueEffect.BLOCKED)
        return EconomicCostBuildResult(
            availability=EvidenceAvailability.BLOCKED,
            evidence=None,
            issues=(issue,),
            attachment_context=prepared.attachment_context,
            calculator_invocations=1,
        )

    semantic_input_hash = economic_cost_semantic_hash(prepared.normalized_input)
    limitations = tuple(sorted(set(prepared.normalized_input.limitations) | {"fixture_static_only", "no_real_tca"}))
    provisional = EconomicCostEvidenceV1(
        component_type=ECONOMIC_COST_COMPONENT_TYPE,
        component_schema_version=ECONOMIC_COST_COMPONENT_SCHEMA_VERSION,
        semantic_input_hash=semantic_input_hash,
        component_hash="",
        component_ref="",
        breakdown=breakdown,
        impact_model_family=prepared.normalized_input.impact_model_family,
        impact_model_ref=prepared.normalized_input.impact_model_ref,
        cost_underestimation_status=prepared.normalized_input.cost_underestimation_status,
        no_real_tca_claim=prepared.normalized_input.no_real_tca_claim,
        limitations=limitations,
    )
    component_hash = economic_cost_component_hash(provisional)
    evidence = EconomicCostEvidenceV1(
        component_type=provisional.component_type,
        component_schema_version=provisional.component_schema_version,
        semantic_input_hash=provisional.semantic_input_hash,
        component_hash=component_hash,
        component_ref=f"fixture://economic-cost/v1/{component_hash.removeprefix('sha256:')}",
        breakdown=provisional.breakdown,
        impact_model_family=provisional.impact_model_family,
        impact_model_ref=provisional.impact_model_ref,
        cost_underestimation_status=provisional.cost_underestimation_status,
        no_real_tca_claim=provisional.no_real_tca_claim,
        limitations=provisional.limitations,
    )
    return EconomicCostBuildResult(
        availability=EvidenceAvailability.PRESENT,
        evidence=evidence,
        issues=(),
        attachment_context=prepared.attachment_context,
        calculator_invocations=1,
    )


def economic_cost_semantic_hash(value: NormalizedEconomicCostInput) -> str:
    """计算 families 2-9 的 subject-neutral input semantic hash。"""

    if not isinstance(value, NormalizedEconomicCostInput):
        raise TypeError("value must be NormalizedEconomicCostInput")
    return canonical_hash(value.semantic_projection(), domain=ECONOMIC_COST_INPUT_HASH_DOMAIN)


def economic_cost_component_hash(evidence: EconomicCostEvidenceV1) -> str:
    """计算 component body 的 domain-separated hash；attachment identity 永不参与。"""

    if not isinstance(evidence, EconomicCostEvidenceV1):
        raise TypeError("evidence must be EconomicCostEvidenceV1")
    return canonical_hash(evidence.unsigned_dict(), domain=ECONOMIC_COST_COMPONENT_HASH_DOMAIN)


def validate_economic_cost_evidence(evidence: EconomicCostEvidenceV1) -> EconomicCostValidation:
    """独立校验 present component 的 immutable schema 与 canonical identity。"""

    issues: list[EconomicCostIssue] = []
    if evidence.component_type != ECONOMIC_COST_COMPONENT_TYPE or evidence.component_schema_version != ECONOMIC_COST_COMPONENT_SCHEMA_VERSION:
        issues.append(_issue("c3_component_hash_tampered", "component_schema", "Unexpected economic-cost component identity.", EconomicCostIssueEffect.BLOCKED))
    if evidence.availability is not EvidenceAvailability.PRESENT:
        issues.append(_issue("c3_component_hash_tampered", "availability", "A present C3 component must carry present availability.", EconomicCostIssueEffect.BLOCKED))
    if evidence.impact_model_family != "square_root" or not evidence.impact_model_ref:
        issues.append(_issue("c3_cost_model_version_missing", "impact_model", "v1 present component requires square_root model and ref.", EconomicCostIssueEffect.BLOCKED))
    if evidence.cost_underestimation_status != "PASS" or not evidence.no_real_tca_claim:
        issues.append(_issue("c3_lineage_provenance_authorization_missing_or_mismatch", "claim_boundary", "v1 present component requires static-only claim boundary.", EconomicCostIssueEffect.BLOCKED))
    if evidence.component_hash != economic_cost_component_hash(evidence):
        issues.append(_issue("c3_component_hash_tampered", "component_hash", "Component hash does not match canonical body.", EconomicCostIssueEffect.BLOCKED))
    ordered = _ordered_issues(issues)
    if ordered:
        return EconomicCostValidation(EvidenceAvailability.BLOCKED, ordered)
    return EconomicCostValidation(EvidenceAvailability.PRESENT)


def validate_economic_cost_semantic_hash(value: NormalizedEconomicCostInput, claimed_hash: str) -> EconomicCostValidation:
    """独立验证 semantic hash，供 evidence self-validation 与篡改测试使用。"""

    if not _clean_text(claimed_hash) or claimed_hash != economic_cost_semantic_hash(value):
        return EconomicCostValidation(
            EvidenceAvailability.BLOCKED,
            (_issue("c3_component_hash_tampered", "claimed_semantic_hash", "Semantic hash mismatch.", EconomicCostIssueEffect.BLOCKED),),
        )
    return EconomicCostValidation(EvidenceAvailability.PRESENT)


def _normalize_decimal(value: Any) -> tuple[Decimal | None, bool]:
    """只接受非 float 的有限 Decimal 语义，保留 None 表示缺失。"""

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
    normalized = value.normalize()
    return format(normalized, "f")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_refs(values: Any) -> tuple[str, ...]:
    if isinstance(values, str):
        values = (values,)
    if not isinstance(values, (tuple, list)):
        return ()
    return tuple(sorted({text for item in values if (text := _clean_text(item))}))


def _positive(value: Decimal | None) -> bool:
    return value is not None and value > 0


def _issue(code: str, field: str, message: str, effect: EconomicCostIssueEffect) -> EconomicCostIssue:
    return EconomicCostIssue(code=code, field=field, message=message, effect=effect)


_ISSUE_ORDER = {
    "c3_gross_performance_basis_missing": 1,
    "c3_trade_turnover_notional_basis_missing": 2,
    "c3_cost_model_version_missing": 3,
    "c3_nonfinite_numeric_invalid": 4,
    "c3_negative_cost_invalid": 5,
    "c3_unit_price_notional_basis_mismatch": 6,
    "c3_currency_price_calendar_mismatch": 7,
    "c3_gross_cost_net_arithmetic_mismatch": 8,
    "c3_lineage_provenance_authorization_missing_or_mismatch": 9,
    "c3_component_hash_tampered": 10,
}


def _ordered_issues(issues: list[EconomicCostIssue]) -> tuple[EconomicCostIssue, ...]:
    # 同 code 的多个来源按 field 稳定排序，确保 fixture 重跑顺序不漂移。
    return tuple(sorted(issues, key=lambda item: (_ISSUE_ORDER[item.code], item.field, item.message)))


__all__ = [
    "ECONOMIC_COST_COMPONENT_HASH_DOMAIN",
    "ECONOMIC_COST_COMPONENT_SCHEMA_VERSION",
    "ECONOMIC_COST_COMPONENT_TYPE",
    "ECONOMIC_COST_INPUT_HASH_DOMAIN",
    "EconomicCostAttachmentContext",
    "EconomicCostBuildResult",
    "EconomicCostEvidenceInput",
    "EconomicCostEvidenceV1",
    "EconomicCostIssue",
    "EconomicCostIssueEffect",
    "EconomicCostValidation",
    "EconomicCostValidationResult",
    "NormalizedEconomicCostInput",
    "build_economic_cost_evidence",
    "economic_cost_component_hash",
    "economic_cost_semantic_hash",
    "normalize_economic_cost_input",
    "prepare_economic_cost_validation",
    "validate_economic_cost_input",
    "validate_economic_cost_evidence",
    "validate_economic_cost_semantic_hash",
]
