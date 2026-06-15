"""CR015-S04 的 pre-trade hard risk gate 离线合同。

本模块只消费 fixture / 脱敏 snapshot contract，不查询真实账户、真实持仓、
真实 QMT 客户端或凭据。任一规则失败时，返回 hard blocked result，且
adapter_calls 保持为 0。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Mapping, Sequence

from market_data.contracts import ADJUSTMENT_POLICY_RAW


ALLOWED_SNAPSHOT_SOURCE_KINDS = frozenset(
    {
        "fixture",
        "sanitized_snapshot",
        "desensitized_snapshot",
        "mock",
    }
)


class RiskRuleId(str, Enum):
    """ADR-058 九类 pre-trade hard risk 规则。"""

    CASH = "cash"
    LOT_SIZE = "lot_size"
    T1_SELLABLE = "t1_sellable"
    POSITION_AVAILABLE = "position_available"
    PRICE_POLICY = "price_policy"
    DUPLICATE_INTENT = "duplicate_intent"
    SINGLE_SYMBOL_LIMIT = "single_symbol_limit"
    PORTFOLIO_LIMIT = "portfolio_limit"
    ABNORMAL_PRICE = "abnormal_price"


class RiskBlockedReason(str, Enum):
    """风控阻断原因；所有失败都必须在 adapter 前 hard block。"""

    REQUIRED_MISSING = "required_missing"
    UNSUPPORTED_SNAPSHOT_SOURCE = "unsupported_snapshot_source"
    CASH_INSUFFICIENT = "cash_insufficient"
    LOT_SIZE_INVALID = "lot_size_invalid"
    T1_NOT_SELLABLE = "t1_not_sellable"
    POSITION_INSUFFICIENT = "position_insufficient"
    NON_RAW_EXECUTION_PRICE_BLOCKED = "non_raw_execution_price_blocked"
    RAW_PRICE_UNAVAILABLE = "raw_price_unavailable"
    DUPLICATE_INTENT = "duplicate_intent"
    SINGLE_SYMBOL_LIMIT_EXCEEDED = "single_symbol_limit_exceeded"
    PORTFOLIO_LIMIT_EXCEEDED = "portfolio_limit_exceeded"
    ABNORMAL_PRICE = "abnormal_price"


@dataclass(frozen=True, slots=True)
class RiskProfile:
    """run profile / trading config 的脱敏风险配置。"""

    risk_profile_id: str
    max_single_symbol_notional: Decimal | int | float | str = Decimal("1000000000")
    max_portfolio_notional: Decimal | int | float | str = Decimal("1000000000")
    price_deviation_limit_pct: Decimal | int | float | str = Decimal("0.20")
    fee_buffer_pct: Decimal | int | float | str = Decimal("0")
    lot_size: int = 100
    evidence_ref: str = ""


@dataclass(frozen=True, slots=True)
class RawPriceRef:
    """执行价使用的 raw / broker price 脱敏引用。"""

    symbol: str
    price: Decimal | int | float | str
    price_policy: str = ADJUSTMENT_POLICY_RAW
    status: str = "available"
    reference_price: Decimal | int | float | str | None = None
    evidence_ref: str = ""
    source_ref: str = ""


@dataclass(frozen=True, slots=True)
class RiskInputSnapshot:
    """风控输入 snapshot；只允许 fixture / 脱敏来源。"""

    cash_available: Decimal | int | float | str = Decimal("0")
    positions_available: Mapping[str, int] = field(default_factory=dict)
    t1_sellable: Mapping[str, int] = field(default_factory=dict)
    raw_price_refs: Mapping[str, RawPriceRef | Mapping[str, object] | object] = field(
        default_factory=dict
    )
    existing_intent_keys: frozenset[str] = field(default_factory=frozenset)
    portfolio_current_notional: Decimal | int | float | str = Decimal("0")
    source_kind: str = "fixture"
    cash_available_ref: str = ""
    position_available_ref: str = ""
    evidence_ref: str = ""


@dataclass(frozen=True, slots=True)
class RiskRuleResult:
    """单条风控规则的结构化结果。"""

    rule_id: RiskRuleId
    passed: bool
    intent_id: str
    risk_profile_id: str
    blocked_reason: str = ""
    evidence_ref: str = ""
    details: Mapping[str, object] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return not self.passed


@dataclass(frozen=True, slots=True)
class PretradeRiskResult:
    """单个 order intent 的 pre-trade risk gate 输出。"""

    intent_id: str
    risk_profile_id: str
    passed: bool
    rule_results: tuple[RiskRuleResult, ...]
    evidence_ref: str = ""
    adapter_calls: int = 0
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: pretrade_risk_safety_counters()
    )

    @property
    def status(self) -> str:
        return "pass" if self.passed else "blocked"

    @property
    def blocked(self) -> bool:
        return not self.passed

    @property
    def blocked_rules(self) -> tuple[RiskRuleResult, ...]:
        return tuple(result for result in self.rule_results if result.blocked)

    @property
    def blocked_reason(self) -> str:
        return ",".join(result.blocked_reason for result in self.blocked_rules)

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(result.rule_id.value for result in self.blocked_rules)

    def to_oms_risk_result(self) -> dict[str, object]:
        """返回 `trading.oms.apply_risk_result` 可消费的最小映射。"""

        return {
            "status": self.status,
            "reason": self.blocked_reason or self.status,
            "intent_id": self.intent_id,
            "risk_profile_id": self.risk_profile_id,
            "rule_ids": self.rule_ids,
            "adapter_calls": self.adapter_calls,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True, slots=True)
class PretradeRiskBatchResult:
    """多 intent 风控结果；组合限额在批次视角统一计算。"""

    results: tuple[PretradeRiskResult, ...]
    risk_profile_id: str
    adapter_calls: int = 0
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: pretrade_risk_safety_counters()
    )

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def blocked_rules(self) -> tuple[RiskRuleResult, ...]:
        return tuple(rule for result in self.results for rule in result.blocked_rules)


def pretrade_risk_safety_counters() -> dict[str, int]:
    """返回 CR015-S04 必须保持为 0 的真实操作计数。"""

    return {
        "qmt_api_call": 0,
        "real_order_call": 0,
        "real_cancel_call": 0,
        "account_query_call": 0,
        "account_write_call": 0,
        "credential_read": 0,
        "real_broker_lake_write": 0,
        "real_lake_write": 0,
        "provider_fetch": 0,
        "publish": 0,
        "dependency_change": 0,
        "adapter_calls": 0,
        "adapter_calls_on_block": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
    }


def evaluate_intent(
    intent: object,
    snapshot: RiskInputSnapshot,
    risk_profile: RiskProfile,
) -> PretradeRiskResult:
    """执行 ADR-058 九类规则；任一失败都返回 blocked。"""

    intent_id = _intent_id(intent)
    risk_profile_id = risk_profile.risk_profile_id or _intent_value(
        intent,
        "risk_profile_id",
    )
    evidence_ref = _first_non_empty(
        snapshot.evidence_ref,
        risk_profile.evidence_ref,
        f"risk-evidence:{risk_profile_id}:{intent_id}",
    )
    price_ref = _raw_price_ref_for_symbol(snapshot, _symbol(intent))
    notional = _intent_notional(intent, price_ref)
    rule_results = (
        _cash_rule(intent, snapshot, risk_profile, price_ref, notional, evidence_ref),
        _lot_size_rule(intent, risk_profile, evidence_ref),
        _t1_sellable_rule(intent, snapshot, evidence_ref),
        _position_available_rule(intent, snapshot, evidence_ref),
        validate_execution_price_policy(
            intent,
            price_ref,
            risk_profile_id=risk_profile_id,
            evidence_ref=evidence_ref,
            source_kind=snapshot.source_kind,
        ),
        detect_duplicate_intent(
            intent,
            snapshot.existing_intent_keys,
            risk_profile_id=risk_profile_id,
            evidence_ref=evidence_ref,
        ),
        _single_symbol_limit_rule(intent, risk_profile, notional, evidence_ref),
        _portfolio_limit_rule(intent, snapshot, risk_profile, notional, evidence_ref),
        _abnormal_price_rule(intent, risk_profile, price_ref, evidence_ref),
    )
    passed = all(result.passed for result in rule_results)
    return PretradeRiskResult(
        intent_id=intent_id,
        risk_profile_id=risk_profile_id,
        passed=passed,
        rule_results=rule_results,
        evidence_ref=evidence_ref,
        adapter_calls=0,
        safety_counters=pretrade_risk_safety_counters(),
    )


def evaluate_many(
    intents: Sequence[object],
    snapshot: RiskInputSnapshot,
    risk_profile: RiskProfile,
) -> PretradeRiskBatchResult:
    """批量评估 intent，并在组合层面统一检查总 notional。"""

    intent_list = tuple(intents)
    notionals = tuple(
        _intent_notional(intent, _raw_price_ref_for_symbol(snapshot, _symbol(intent)))
        for intent in intent_list
    )
    total_candidate_notional = sum(notionals, Decimal("0"))
    seen_keys = set(snapshot.existing_intent_keys)
    results: list[PretradeRiskResult] = []
    for intent, notional in zip(intent_list, notionals, strict=True):
        per_intent_snapshot = replace(
            snapshot,
            existing_intent_keys=frozenset(seen_keys),
            portfolio_current_notional=(
                _decimal_value(snapshot.portfolio_current_notional)
                + total_candidate_notional
                - notional
            ),
        )
        results.append(evaluate_intent(intent, per_intent_snapshot, risk_profile))
        key = _duplicate_key(intent)
        if key:
            seen_keys.add(key)
        idempotency_key = _intent_value(intent, "idempotency_key")
        if idempotency_key:
            seen_keys.add(idempotency_key)
    return PretradeRiskBatchResult(
        results=tuple(results),
        risk_profile_id=risk_profile.risk_profile_id,
        adapter_calls=0,
        safety_counters=pretrade_risk_safety_counters(),
    )


def detect_duplicate_intent(
    intent: object,
    existing_keys: frozenset[str] | set[str] | Sequence[str],
    *,
    risk_profile_id: str = "",
    evidence_ref: str = "",
) -> RiskRuleResult:
    """用 run_id + idempotency_key 执行重复 intent hard block。"""

    key = _duplicate_key(intent)
    idempotency_key = _intent_value(intent, "idempotency_key")
    if not key or not idempotency_key:
        return _blocked_rule(
            RiskRuleId.DUPLICATE_INTENT,
            intent,
            risk_profile_id,
            RiskBlockedReason.REQUIRED_MISSING,
            evidence_ref,
            {"missing": "run_id/idempotency_key"},
        )
    existing = set(existing_keys)
    if key in existing or idempotency_key in existing:
        return _blocked_rule(
            RiskRuleId.DUPLICATE_INTENT,
            intent,
            risk_profile_id,
            RiskBlockedReason.DUPLICATE_INTENT,
            evidence_ref,
            {"duplicate_key": key},
        )
    return _passed_rule(
        RiskRuleId.DUPLICATE_INTENT,
        intent,
        risk_profile_id,
        evidence_ref,
        {"duplicate_key": key},
    )


def validate_execution_price_policy(
    intent: object,
    raw_price_ref: RawPriceRef | Mapping[str, object] | object,
    *,
    risk_profile_id: str = "",
    evidence_ref: str = "",
    source_kind: str = "fixture",
) -> RiskRuleResult:
    """执行价口径只允许 exact raw；qfq/hfq 或非脱敏来源必须阻断。"""

    price_ref = _coerce_raw_price_ref(raw_price_ref, _symbol(intent))
    if source_kind not in ALLOWED_SNAPSHOT_SOURCE_KINDS:
        return _blocked_rule(
            RiskRuleId.PRICE_POLICY,
            intent,
            risk_profile_id,
            RiskBlockedReason.UNSUPPORTED_SNAPSHOT_SOURCE,
            evidence_ref,
            {"source_kind": source_kind},
        )
    execution_policy = _intent_value(intent, "execution_price_policy")
    if execution_policy != ADJUSTMENT_POLICY_RAW:
        return _blocked_rule(
            RiskRuleId.PRICE_POLICY,
            intent,
            risk_profile_id,
            RiskBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED,
            evidence_ref,
            {"execution_price_policy": execution_policy},
        )
    price_policy = _string_value(price_ref.price_policy)
    if price_policy != ADJUSTMENT_POLICY_RAW:
        return _blocked_rule(
            RiskRuleId.PRICE_POLICY,
            intent,
            risk_profile_id,
            RiskBlockedReason.NON_RAW_EXECUTION_PRICE_BLOCKED,
            evidence_ref,
            {"price_policy": price_policy},
        )
    if _string_value(price_ref.status) != "available":
        return _blocked_rule(
            RiskRuleId.PRICE_POLICY,
            intent,
            risk_profile_id,
            RiskBlockedReason.RAW_PRICE_UNAVAILABLE,
            evidence_ref,
            {"price_status": price_ref.status},
        )
    return _passed_rule(
        RiskRuleId.PRICE_POLICY,
        intent,
        risk_profile_id,
        evidence_ref,
        {
            "execution_price_policy": execution_policy,
            "price_policy": price_policy,
        },
    )


def build_blocked_result(
    intent: object,
    rule_results: Sequence[RiskRuleResult],
    *,
    risk_profile_id: str = "",
    evidence_ref: str = "",
) -> PretradeRiskResult:
    """按标准结构汇总 blocked result，供测试或调用方复用。"""

    normalized = tuple(rule_results)
    passed = all(result.passed for result in normalized)
    return PretradeRiskResult(
        intent_id=_intent_id(intent),
        risk_profile_id=risk_profile_id or _intent_value(intent, "risk_profile_id"),
        passed=passed,
        rule_results=normalized,
        evidence_ref=evidence_ref,
        adapter_calls=0,
        safety_counters=pretrade_risk_safety_counters(),
    )


def read_pretrade_risk_result(
    risk_context: PretradeRiskResult | PretradeRiskBatchResult | Mapping[str, object] | None,
) -> dict[str, object]:
    """把 CR015 pre-trade risk result 归一化为只读 gate view。"""

    if risk_context is None:
        return {
            "gate_name": "pretrade_risk",
            "passed": False,
            "status": "missing",
            "blocked_reason": RiskBlockedReason.REQUIRED_MISSING.value,
            "blocked_rules": (),
            "required_evidence": ("pretrade_risk_result",),
            "adapter_calls": 0,
            "safety_counters": pretrade_risk_safety_counters(),
        }

    if isinstance(risk_context, PretradeRiskBatchResult):
        blocked_rules = tuple(
            rule.blocked_reason for rule in risk_context.blocked_rules if rule.blocked_reason
        )
        counters = dict(risk_context.safety_counters)
        passed = risk_context.passed
        adapter_calls = int(risk_context.adapter_calls)
        risk_profile_id = risk_context.risk_profile_id
    elif isinstance(risk_context, PretradeRiskResult):
        blocked_rules = tuple(
            rule.blocked_reason for rule in risk_context.blocked_rules if rule.blocked_reason
        )
        counters = dict(risk_context.safety_counters)
        passed = risk_context.passed
        adapter_calls = int(risk_context.adapter_calls)
        risk_profile_id = risk_context.risk_profile_id
    else:
        blocked_rules = tuple(
            _string_value(item)
            for item in (
                risk_context.get("blocked_rules")
                or risk_context.get("rule_ids")
                or ()
            )
            if _string_value(item)
        )
        counters = dict(risk_context.get("safety_counters") or pretrade_risk_safety_counters())
        status = _string_value(risk_context.get("status"))
        passed = bool(risk_context.get("passed", status == "pass"))
        adapter_calls = int(risk_context.get("adapter_calls", 0) or 0)
        risk_profile_id = _string_value(risk_context.get("risk_profile_id"))

    nonzero_counters = tuple(
        key for key, value in counters.items() if int(value) != 0
    )
    if adapter_calls or nonzero_counters:
        passed = False
    blocked_reason = ""
    if adapter_calls or nonzero_counters:
        blocked_reason = "real_operation_forbidden"
    elif blocked_rules:
        blocked_reason = blocked_rules[0]
    elif not passed:
        blocked_reason = RiskBlockedReason.REQUIRED_MISSING.value

    return {
        "gate_name": "pretrade_risk",
        "passed": passed and not blocked_reason,
        "status": "pass" if passed and not blocked_reason else "blocked",
        "blocked_reason": blocked_reason,
        "blocked_rules": blocked_rules,
        "risk_profile_id": risk_profile_id,
        "required_evidence": () if passed and not blocked_reason else ("pretrade_risk_pass",),
        "adapter_calls": adapter_calls,
        "safety_counters": counters,
    }


def _cash_rule(
    intent: object,
    snapshot: RiskInputSnapshot,
    risk_profile: RiskProfile,
    price_ref: RawPriceRef,
    notional: Decimal,
    evidence_ref: str,
) -> RiskRuleResult:
    risk_profile_id = risk_profile.risk_profile_id
    if _side(intent) != "buy":
        return _passed_rule(RiskRuleId.CASH, intent, risk_profile_id, evidence_ref)
    cash_available = _decimal_value(snapshot.cash_available)
    fee_buffer = _decimal_value(risk_profile.fee_buffer_pct)
    required_cash = notional * (Decimal("1") + fee_buffer)
    if not _raw_price_is_available(price_ref) or cash_available < required_cash:
        return _blocked_rule(
            RiskRuleId.CASH,
            intent,
            risk_profile_id,
            RiskBlockedReason.CASH_INSUFFICIENT,
            evidence_ref,
            {
                "cash_available": str(cash_available),
                "required_cash": str(required_cash),
                "cash_available_ref": snapshot.cash_available_ref,
            },
        )
    return _passed_rule(
        RiskRuleId.CASH,
        intent,
        risk_profile_id,
        evidence_ref,
        {
            "cash_available": str(cash_available),
            "required_cash": str(required_cash),
        },
    )


def _lot_size_rule(
    intent: object,
    risk_profile: RiskProfile,
    evidence_ref: str,
) -> RiskRuleResult:
    qty = _target_qty(intent)
    lot_size = int(risk_profile.lot_size or 100)
    if qty <= 0 or lot_size <= 0 or qty % lot_size != 0:
        return _blocked_rule(
            RiskRuleId.LOT_SIZE,
            intent,
            risk_profile.risk_profile_id,
            RiskBlockedReason.LOT_SIZE_INVALID,
            evidence_ref,
            {"target_qty": qty, "lot_size": lot_size},
        )
    return _passed_rule(
        RiskRuleId.LOT_SIZE,
        intent,
        risk_profile.risk_profile_id,
        evidence_ref,
        {"target_qty": qty, "lot_size": lot_size},
    )


def _t1_sellable_rule(
    intent: object,
    snapshot: RiskInputSnapshot,
    evidence_ref: str,
) -> RiskRuleResult:
    if _side(intent) != "sell":
        return _passed_rule(
            RiskRuleId.T1_SELLABLE,
            intent,
            _intent_value(intent, "risk_profile_id"),
            evidence_ref,
        )
    sellable = int(snapshot.t1_sellable.get(_symbol(intent), 0))
    qty = _target_qty(intent)
    if sellable < qty:
        return _blocked_rule(
            RiskRuleId.T1_SELLABLE,
            intent,
            _intent_value(intent, "risk_profile_id"),
            RiskBlockedReason.T1_NOT_SELLABLE,
            evidence_ref,
            {
                "t1_sellable_qty": sellable,
                "target_qty": qty,
                "position_available_ref": snapshot.position_available_ref,
            },
        )
    return _passed_rule(
        RiskRuleId.T1_SELLABLE,
        intent,
        _intent_value(intent, "risk_profile_id"),
        evidence_ref,
        {"t1_sellable_qty": sellable, "target_qty": qty},
    )


def _position_available_rule(
    intent: object,
    snapshot: RiskInputSnapshot,
    evidence_ref: str,
) -> RiskRuleResult:
    if _side(intent) != "sell":
        return _passed_rule(
            RiskRuleId.POSITION_AVAILABLE,
            intent,
            _intent_value(intent, "risk_profile_id"),
            evidence_ref,
        )
    available = int(snapshot.positions_available.get(_symbol(intent), 0))
    qty = _target_qty(intent)
    if available < qty:
        return _blocked_rule(
            RiskRuleId.POSITION_AVAILABLE,
            intent,
            _intent_value(intent, "risk_profile_id"),
            RiskBlockedReason.POSITION_INSUFFICIENT,
            evidence_ref,
            {
                "position_available_qty": available,
                "target_qty": qty,
                "position_available_ref": snapshot.position_available_ref,
            },
        )
    return _passed_rule(
        RiskRuleId.POSITION_AVAILABLE,
        intent,
        _intent_value(intent, "risk_profile_id"),
        evidence_ref,
        {"position_available_qty": available, "target_qty": qty},
    )


def _single_symbol_limit_rule(
    intent: object,
    risk_profile: RiskProfile,
    notional: Decimal,
    evidence_ref: str,
) -> RiskRuleResult:
    limit = _decimal_value(risk_profile.max_single_symbol_notional)
    if limit >= 0 and notional > limit:
        return _blocked_rule(
            RiskRuleId.SINGLE_SYMBOL_LIMIT,
            intent,
            risk_profile.risk_profile_id,
            RiskBlockedReason.SINGLE_SYMBOL_LIMIT_EXCEEDED,
            evidence_ref,
            {"notional": str(notional), "limit": str(limit)},
        )
    return _passed_rule(
        RiskRuleId.SINGLE_SYMBOL_LIMIT,
        intent,
        risk_profile.risk_profile_id,
        evidence_ref,
        {"notional": str(notional), "limit": str(limit)},
    )


def _portfolio_limit_rule(
    intent: object,
    snapshot: RiskInputSnapshot,
    risk_profile: RiskProfile,
    notional: Decimal,
    evidence_ref: str,
) -> RiskRuleResult:
    limit = _decimal_value(risk_profile.max_portfolio_notional)
    total_notional = _decimal_value(snapshot.portfolio_current_notional) + notional
    if limit >= 0 and total_notional > limit:
        return _blocked_rule(
            RiskRuleId.PORTFOLIO_LIMIT,
            intent,
            risk_profile.risk_profile_id,
            RiskBlockedReason.PORTFOLIO_LIMIT_EXCEEDED,
            evidence_ref,
            {"portfolio_notional": str(total_notional), "limit": str(limit)},
        )
    return _passed_rule(
        RiskRuleId.PORTFOLIO_LIMIT,
        intent,
        risk_profile.risk_profile_id,
        evidence_ref,
        {"portfolio_notional": str(total_notional), "limit": str(limit)},
    )


def _abnormal_price_rule(
    intent: object,
    risk_profile: RiskProfile,
    price_ref: RawPriceRef,
    evidence_ref: str,
) -> RiskRuleResult:
    price = _decimal_value(price_ref.price)
    reference_price = _decimal_value(price_ref.reference_price)
    limit = _decimal_value(risk_profile.price_deviation_limit_pct)
    if price <= 0:
        return _blocked_rule(
            RiskRuleId.ABNORMAL_PRICE,
            intent,
            risk_profile.risk_profile_id,
            RiskBlockedReason.ABNORMAL_PRICE,
            evidence_ref,
            {"price": str(price), "reference_price": str(reference_price)},
        )
    if reference_price > 0:
        deviation = abs(price - reference_price) / reference_price
        if deviation > limit:
            return _blocked_rule(
                RiskRuleId.ABNORMAL_PRICE,
                intent,
                risk_profile.risk_profile_id,
                RiskBlockedReason.ABNORMAL_PRICE,
                evidence_ref,
                {
                    "price": str(price),
                    "reference_price": str(reference_price),
                    "deviation": str(deviation),
                    "limit": str(limit),
                },
            )
    return _passed_rule(
        RiskRuleId.ABNORMAL_PRICE,
        intent,
        risk_profile.risk_profile_id,
        evidence_ref,
        {"price": str(price), "reference_price": str(reference_price)},
    )


def _passed_rule(
    rule_id: RiskRuleId,
    intent: object,
    risk_profile_id: str,
    evidence_ref: str,
    details: Mapping[str, object] | None = None,
) -> RiskRuleResult:
    return RiskRuleResult(
        rule_id=rule_id,
        passed=True,
        intent_id=_intent_id(intent),
        risk_profile_id=risk_profile_id or _intent_value(intent, "risk_profile_id"),
        evidence_ref=evidence_ref,
        details=details or {},
    )


def _blocked_rule(
    rule_id: RiskRuleId,
    intent: object,
    risk_profile_id: str,
    blocked_reason: RiskBlockedReason,
    evidence_ref: str,
    details: Mapping[str, object] | None = None,
) -> RiskRuleResult:
    return RiskRuleResult(
        rule_id=rule_id,
        passed=False,
        intent_id=_intent_id(intent),
        risk_profile_id=risk_profile_id or _intent_value(intent, "risk_profile_id"),
        blocked_reason=blocked_reason.value,
        evidence_ref=evidence_ref,
        details=details or {},
    )


def _raw_price_ref_for_symbol(snapshot: RiskInputSnapshot, symbol: str) -> RawPriceRef:
    raw_ref = snapshot.raw_price_refs.get(symbol)
    if raw_ref is None:
        raw_ref = snapshot.raw_price_refs.get("*")
    return _coerce_raw_price_ref(raw_ref, symbol)


def _coerce_raw_price_ref(
    raw_price_ref: RawPriceRef | Mapping[str, object] | object,
    symbol: str,
) -> RawPriceRef:
    if isinstance(raw_price_ref, RawPriceRef):
        return raw_price_ref
    if isinstance(raw_price_ref, Mapping):
        return RawPriceRef(
            symbol=_string_value(raw_price_ref.get("symbol")) or symbol,
            price=raw_price_ref.get("price", raw_price_ref.get("raw_price", 0)),
            price_policy=_string_value(
                raw_price_ref.get(
                    "price_policy",
                    raw_price_ref.get("execution_price_policy", ADJUSTMENT_POLICY_RAW),
                )
            ),
            status=_string_value(raw_price_ref.get("status")) or "available",
            reference_price=raw_price_ref.get("reference_price"),
            evidence_ref=_string_value(raw_price_ref.get("evidence_ref")),
            source_ref=_string_value(raw_price_ref.get("source_ref")),
        )
    if raw_price_ref is None:
        return RawPriceRef(
            symbol=symbol,
            price=Decimal("0"),
            status="missing",
            evidence_ref="missing_raw_price_ref",
        )
    return RawPriceRef(symbol=symbol, price=raw_price_ref)


def _raw_price_is_available(price_ref: RawPriceRef) -> bool:
    return (
        _string_value(price_ref.status) == "available"
        and _string_value(price_ref.price_policy) == ADJUSTMENT_POLICY_RAW
        and _decimal_value(price_ref.price) > 0
    )


def _intent_notional(intent: object, price_ref: RawPriceRef) -> Decimal:
    return Decimal(_target_qty(intent)) * _decimal_value(price_ref.price)


def _duplicate_key(intent: object) -> str:
    run_id = _intent_value(intent, "run_id")
    idempotency_key = _intent_value(intent, "idempotency_key")
    if not run_id or not idempotency_key:
        return ""
    return f"{run_id}:{idempotency_key}"


def _intent_id(intent: object) -> str:
    return _first_non_empty(
        _intent_value(intent, "order_intent_id"),
        _intent_value(intent, "intent_id"),
    )


def _symbol(intent: object) -> str:
    return _intent_value(intent, "symbol")


def _side(intent: object) -> str:
    return _intent_value(intent, "side").lower()


def _target_qty(intent: object) -> int:
    return _int_value(_intent_value(intent, "target_qty") or _intent_value(intent, "quantity"))


def _intent_value(intent: object, key: str) -> str:
    if isinstance(intent, Mapping):
        return _string_value(intent.get(key))
    return _string_value(getattr(intent, key, ""))


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value).strip()


def _int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _decimal_value(value: object) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")
    if not decimal_value.is_finite():
        return Decimal("0")
    return decimal_value


__all__ = [
    "ALLOWED_SNAPSHOT_SOURCE_KINDS",
    "PretradeRiskBatchResult",
    "PretradeRiskResult",
    "RawPriceRef",
    "RiskBlockedReason",
    "RiskInputSnapshot",
    "RiskProfile",
    "RiskRuleId",
    "RiskRuleResult",
    "build_blocked_result",
    "detect_duplicate_intent",
    "evaluate_intent",
    "evaluate_many",
    "pretrade_risk_safety_counters",
    "read_pretrade_risk_result",
    "validate_execution_price_policy",
]
