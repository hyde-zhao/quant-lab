"""CR015-S06 的 target portfolio -> order intent shadow pipeline。

本模块只编排 fixture / shadow / dry-run / mock 合同，不读取真实账户、不调用
QMT / broker API、不创建目录、不写 broker lake 或研究 lake。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from enum import Enum
from typing import Any, Mapping, Sequence

from market_data.contracts import ADJUSTMENT_POLICY_RAW, ADJUSTMENT_POLICY_VALUES
from trading.broker_lake import BrokerLakeWritePlan, dry_run_write_plan
from trading.oms import (
    OmsResult,
    OrderIntent,
    StateTransitionEvent,
    apply_broker_event,
    apply_risk_result,
    create_order_intent,
    order_intent_to_broker_lake_event,
    state_transition_to_broker_lake_event,
)
from trading.pretrade_risk import (
    PretradeRiskBatchResult,
    PretradeRiskResult,
    RawPriceRef,
    RiskInputSnapshot,
    RiskProfile,
    evaluate_many,
)
from trading.qmt_adapter import (
    AdapterRequest,
    AdapterResult,
    BrokerOrderEvent,
    MockBrokerScenario,
    submit_intent,
)
from trading.qmt_environment import AdapterMode


ALLOWED_SHADOW_MODES = frozenset({"shadow", "dry_run", "mock"})
BLOCKED_ACTIVATION_MODES = frozenset(
    {"simulation", "live_readonly", "small_live", "scale_up"}
)
REQUIRED_POLICY_FIELDS = (
    "research_adjustment_policy",
    "view_id",
    "source_run_id",
    "quality_status",
    "execution_price_policy",
)
DEFAULT_BROKER_LAKE_ROOT_LABEL = "BROKER_LAKE_ROOT"


@dataclass(frozen=True, slots=True)
class FixtureSnapshots:
    """shadow pipeline 可消费的 fixture / 脱敏 snapshot 合同。"""

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
class ModeValidationResult:
    """shadow_run mode allowlist 校验结果。"""

    passed: bool
    mode: str
    blocked_reason: str = ""


@dataclass(frozen=True, slots=True)
class PolicyMetadataValidation:
    """研究口径与执行价 metadata gate 输出。"""

    passed: bool
    metadata: Mapping[str, object]
    missing_fields: tuple[str, ...] = ()
    blocked_reason: str = ""
    non_raw_execution_pass_count: int = 0


@dataclass(frozen=True, slots=True)
class ShadowRunInput:
    """shadow_run 的结构化输入。"""

    target_portfolio: Sequence[Mapping[str, object]]
    policy_metadata: Mapping[str, object]
    fixture_snapshots: FixtureSnapshots | Mapping[str, object]
    run_context: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ShadowRunResult:
    """S06 shadow pipeline 的结构化输出。"""

    status: str
    shadow_run_id: str
    mode: str
    policy_metadata: Mapping[str, object]
    intents: tuple[OrderIntent, ...]
    risk_results: tuple[PretradeRiskResult, ...]
    risk_batch_result: PretradeRiskBatchResult | None
    adapter_results: tuple[AdapterResult, ...]
    broker_events: tuple[BrokerOrderEvent, ...]
    state_transitions: tuple[StateTransitionEvent, ...]
    dry_run_plans: tuple[BrokerLakeWritePlan, ...]
    blocked_reasons: tuple[str, ...]
    audit_summary: Mapping[str, object]
    safety_counters: Mapping[str, int]
    adapter_call_count: int = 0

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"


def shadow_run(
    target_portfolio: Sequence[Mapping[str, object]] | ShadowRunInput,
    policy_metadata: Mapping[str, object] | None = None,
    fixture_snapshots: FixtureSnapshots | Mapping[str, object] | None = None,
    run_context: Mapping[str, object] | None = None,
    *,
    now: datetime | None = None,
) -> ShadowRunResult:
    """执行 target portfolio 到 order intent 的离线 shadow 编排。"""

    run_input = _coerce_shadow_run_input(
        target_portfolio,
        policy_metadata,
        fixture_snapshots,
        run_context,
    )
    context = dict(run_input.run_context)
    observed_at = _observed_at(now)
    mode = _string_value(context.get("mode") or context.get("adapter_mode") or "mock")
    shadow_run_id = _shadow_run_id(context, observed_at)
    root_label = _string_value(
        context.get("broker_lake_root_label") or DEFAULT_BROKER_LAKE_ROOT_LABEL
    )

    safety_counters = build_safety_counters()
    blocked_reasons: list[str] = []
    dry_run_plans: list[BrokerLakeWritePlan] = []

    mode_gate = validate_shadow_mode(mode)
    if not mode_gate.passed:
        blocked_reasons.append(mode_gate.blocked_reason)
        dry_run_plans.append(
            _build_error_dry_run_plan(
                context,
                root_label,
                "mode_gate",
                mode_gate.blocked_reason,
            )
        )
        return _finalize_result(
            status="blocked",
            shadow_run_id=shadow_run_id,
            mode=mode_gate.mode,
            policy_metadata=dict(run_input.policy_metadata),
            intents=(),
            risk_results=(),
            risk_batch_result=None,
            adapter_results=(),
            broker_events=(),
            state_transitions=(),
            dry_run_plans=tuple(dry_run_plans),
            blocked_reasons=tuple(blocked_reasons),
            safety_counters=safety_counters,
            adapter_call_count=0,
        )

    policy_gate = validate_policy_metadata(run_input.policy_metadata)
    if not policy_gate.passed:
        if policy_gate.blocked_reason:
            blocked_reasons.append(policy_gate.blocked_reason)
        dry_run_plans.append(
            _build_error_dry_run_plan(
                context,
                root_label,
                "policy_metadata_gate",
                policy_gate.blocked_reason or "policy_metadata_blocked",
            )
        )
        return _finalize_result(
            status="blocked",
            shadow_run_id=shadow_run_id,
            mode=mode_gate.mode,
            policy_metadata=policy_gate.metadata,
            intents=(),
            risk_results=(),
            risk_batch_result=None,
            adapter_results=(),
            broker_events=(),
            state_transitions=(),
            dry_run_plans=tuple(dry_run_plans),
            blocked_reasons=tuple(blocked_reasons),
            safety_counters=safety_counters,
            adapter_call_count=0,
        )

    snapshots = _coerce_fixture_snapshots(run_input.fixture_snapshots)
    normalized_targets = tuple(
        _normalize_target_row(row, context, snapshots)
        for row in run_input.target_portfolio
    )
    creation_results = build_target_order_intents(
        normalized_targets,
        policy_gate.metadata,
        context,
        now=observed_at,
    )
    created_intents = tuple(result.intent for result in creation_results if result.intent is not None)
    creation_errors = tuple(result for result in creation_results if result.intent is None)
    if creation_errors:
        blocked_reasons.extend(_oms_blocked_reason(result) for result in creation_errors)
        for result in creation_errors:
            dry_run_plans.append(
                _build_error_dry_run_plan(
                    context,
                    root_label,
                    "order_intent",
                    _oms_blocked_reason(result),
                )
            )

    risk_batch_result: PretradeRiskBatchResult | None = None
    risk_results: tuple[PretradeRiskResult, ...] = ()
    if created_intents:
        risk_batch_result = evaluate_many(
            created_intents,
            _risk_snapshot_from_fixture(snapshots),
            _risk_profile_from_context(context),
        )
        risk_results = risk_batch_result.results

    final_intents: list[OrderIntent] = []
    state_transitions: list[StateTransitionEvent] = []
    adapter_results: list[AdapterResult] = []
    broker_events: list[BrokerOrderEvent] = []
    adapter_call_count = 0

    for intent, risk_result in zip(created_intents, risk_results, strict=True):
        risk_applied = apply_risk_result(intent, risk_result, now=observed_at)
        current_intent = risk_applied.intent or intent
        if risk_applied.transition_event is not None:
            state_transitions.append(risk_applied.transition_event)
        if risk_result.blocked:
            blocked_reasons.extend(
                reason for reason in (risk_result.blocked_reason.split(",") if risk_result.blocked_reason else ())
                if reason
            )
            final_intents.append(current_intent)
            dry_run_plans.extend(
                _broker_lake_plans_for_intent(
                    current_intent,
                    root_label,
                    risk_applied.transition_event,
                )
            )
            continue

        adapter_request = _adapter_request_for_intent(
            current_intent,
            mode_gate.mode,
            risk_result,
            snapshots,
            context,
        )
        adapter_result = submit_intent(adapter_request, now=observed_at)
        adapter_call_count += 1
        adapter_results.append(adapter_result)
        if adapter_result.blocked:
            blocked_reasons.append(adapter_result.blocked_reason.value if adapter_result.blocked_reason else "adapter_blocked")
            final_intents.append(current_intent)
            dry_run_plans.extend(
                _broker_lake_plans_for_intent(
                    current_intent,
                    root_label,
                    risk_applied.transition_event,
                )
            )
            continue

        if adapter_result.broker_event is not None:
            broker_events.append(adapter_result.broker_event)
            broker_applied = apply_broker_event(
                current_intent,
                adapter_result.broker_event,
                now=observed_at,
            )
            if broker_applied.transition_event is not None:
                state_transitions.append(broker_applied.transition_event)
            if broker_applied.ok and broker_applied.intent is not None:
                current_intent = broker_applied.intent
            elif broker_applied.error is not None:
                blocked_reasons.append(broker_applied.error.error_code.value)

        final_intents.append(current_intent)
        dry_run_plans.extend(
            _broker_lake_plans_for_intent(
                current_intent,
                root_label,
                *(
                    transition
                    for transition in state_transitions
                    if transition.intent_id == current_intent.order_intent_id
                ),
            )
        )

    status = "blocked" if blocked_reasons else "pass"
    return _finalize_result(
        status=status,
        shadow_run_id=shadow_run_id,
        mode=mode_gate.mode,
        policy_metadata=policy_gate.metadata,
        intents=tuple(final_intents),
        risk_results=risk_results,
        risk_batch_result=risk_batch_result,
        adapter_results=tuple(adapter_results),
        broker_events=tuple(broker_events),
        state_transitions=tuple(state_transitions),
        dry_run_plans=tuple(dry_run_plans),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        safety_counters=safety_counters,
        adapter_call_count=adapter_call_count,
    )


def validate_shadow_mode(mode: str | AdapterMode) -> ModeValidationResult:
    """只允许 shadow / dry_run / mock；simulation/live/scale_up 一律 blocked。"""

    value = _string_value(mode)
    if value in ALLOWED_SHADOW_MODES:
        return ModeValidationResult(passed=True, mode=value)
    reason = (
        "activation_not_authorized"
        if value in BLOCKED_ACTIVATION_MODES
        else "mode_not_authorized"
    )
    return ModeValidationResult(passed=False, mode=value, blocked_reason=reason)


def validate_policy_metadata(
    policy_metadata: Mapping[str, object],
) -> PolicyMetadataValidation:
    """校验 CR017 -> QMT handoff metadata，执行价只能是 raw。"""

    metadata = {key: policy_metadata.get(key, "") for key in REQUIRED_POLICY_FIELDS}
    missing = tuple(key for key, value in metadata.items() if not _string_value(value))
    if missing:
        return PolicyMetadataValidation(
            passed=False,
            metadata=metadata,
            missing_fields=missing,
            blocked_reason="policy_metadata_required_missing",
        )

    research_policy = _string_value(metadata["research_adjustment_policy"])
    if research_policy not in ADJUSTMENT_POLICY_VALUES:
        return PolicyMetadataValidation(
            passed=False,
            metadata=metadata,
            blocked_reason="research_adjustment_policy_unknown",
        )

    execution_policy = _string_value(metadata["execution_price_policy"])
    if execution_policy != ADJUSTMENT_POLICY_RAW:
        return PolicyMetadataValidation(
            passed=False,
            metadata=metadata,
            blocked_reason="non_raw_execution_price_blocked",
            non_raw_execution_pass_count=0,
        )

    normalized = dict(policy_metadata)
    normalized.update(metadata)
    normalized["adjusted_execution_price_pass_count"] = 0
    normalized["non_raw_execution_pass_count"] = 0
    return PolicyMetadataValidation(
        passed=True,
        metadata=normalized,
        non_raw_execution_pass_count=0,
    )


def build_target_order_intents(
    target_portfolio: Sequence[Mapping[str, object]],
    policy_metadata: Mapping[str, object],
    run_context: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> tuple[OmsResult, ...]:
    """把目标组合逐条转换为 S03 order intent 创建结果。"""

    context = dict(run_context)
    context.setdefault("strategy_id", _first_non_empty_from_rows(target_portfolio, "strategy_id"))
    context.setdefault("run_id", _first_non_empty_from_rows(target_portfolio, "run_id"))
    context.setdefault("risk_profile_id", _string_value(context.get("risk_profile_id")) or "risk-profile-shadow")
    return tuple(
        create_order_intent(row, policy_metadata, context, now=now)
        for row in target_portfolio
    )


def build_safety_counters() -> dict[str, int]:
    """返回 S06 必须保持为 0 的真实操作与门控安全计数。"""

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
        "adapter_calls_on_block": 0,
        "non_raw_execution_pass_count": 0,
        "activation_mode_pass_count": 0,
        "real_qmt_process_invocation": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "open_write_call": 0,
        "sensitive_raw_value_output": 0,
        "adjusted_execution_price_pass_count": 0,
    }


def build_audit_summary(result: ShadowRunResult) -> dict[str, object]:
    """生成脱敏审计摘要，供 CP6 / S07 runbook 消费。"""

    return {
        "shadow_run_id": result.shadow_run_id,
        "mode": result.mode,
        "status": result.status,
        "intent_count": len(result.intents),
        "risk_result_count": len(result.risk_results),
        "risk_pass_count": sum(1 for item in result.risk_results if item.passed),
        "risk_blocked_count": sum(1 for item in result.risk_results if item.blocked),
        "adapter_calls": result.adapter_call_count,
        "mock_broker_event_count": len(result.broker_events),
        "state_transition_count": len(result.state_transitions),
        "broker_lake_dry_run_plan_count": len(result.dry_run_plans),
        "real_broker_lake_write": result.safety_counters.get("real_broker_lake_write", 0),
        "blocked_reasons": list(result.blocked_reasons),
        "non_raw_execution_pass_count": result.safety_counters.get(
            "non_raw_execution_pass_count",
            0,
        ),
        "activation_mode_pass_count": result.safety_counters.get(
            "activation_mode_pass_count",
            0,
        ),
    }


def _coerce_shadow_run_input(
    target_portfolio: Sequence[Mapping[str, object]] | ShadowRunInput,
    policy_metadata: Mapping[str, object] | None,
    fixture_snapshots: FixtureSnapshots | Mapping[str, object] | None,
    run_context: Mapping[str, object] | None,
) -> ShadowRunInput:
    if isinstance(target_portfolio, ShadowRunInput):
        return target_portfolio
    return ShadowRunInput(
        target_portfolio=target_portfolio,
        policy_metadata=dict(policy_metadata or {}),
        fixture_snapshots=fixture_snapshots or FixtureSnapshots(),
        run_context=dict(run_context or {}),
    )


def _coerce_fixture_snapshots(
    fixture_snapshots: FixtureSnapshots | Mapping[str, object],
) -> FixtureSnapshots:
    if isinstance(fixture_snapshots, FixtureSnapshots):
        return fixture_snapshots
    return FixtureSnapshots(
        cash_available=fixture_snapshots.get("cash_available", fixture_snapshots.get("cash", 0)),
        positions_available=dict(fixture_snapshots.get("positions_available", fixture_snapshots.get("positions", {}))),
        t1_sellable=dict(fixture_snapshots.get("t1_sellable", fixture_snapshots.get("sellable", {}))),
        raw_price_refs=dict(fixture_snapshots.get("raw_price_refs", fixture_snapshots.get("raw_prices", {}))),
        existing_intent_keys=frozenset(fixture_snapshots.get("existing_intent_keys", ())),
        portfolio_current_notional=fixture_snapshots.get("portfolio_current_notional", 0),
        source_kind=_string_value(fixture_snapshots.get("source_kind")) or "fixture",
        cash_available_ref=_string_value(fixture_snapshots.get("cash_available_ref")),
        position_available_ref=_string_value(fixture_snapshots.get("position_available_ref")),
        evidence_ref=_string_value(fixture_snapshots.get("evidence_ref")),
    )


def _risk_snapshot_from_fixture(snapshots: FixtureSnapshots) -> RiskInputSnapshot:
    return RiskInputSnapshot(
        cash_available=snapshots.cash_available,
        positions_available=snapshots.positions_available,
        t1_sellable=snapshots.t1_sellable,
        raw_price_refs=snapshots.raw_price_refs,
        existing_intent_keys=snapshots.existing_intent_keys,
        portfolio_current_notional=snapshots.portfolio_current_notional,
        source_kind=snapshots.source_kind,
        cash_available_ref=snapshots.cash_available_ref,
        position_available_ref=snapshots.position_available_ref,
        evidence_ref=snapshots.evidence_ref,
    )


def _risk_profile_from_context(run_context: Mapping[str, object]) -> RiskProfile:
    return RiskProfile(
        risk_profile_id=_string_value(run_context.get("risk_profile_id")) or "risk-profile-shadow",
        max_single_symbol_notional=run_context.get("max_single_symbol_notional", Decimal("1000000000")),
        max_portfolio_notional=run_context.get("max_portfolio_notional", Decimal("1000000000")),
        price_deviation_limit_pct=run_context.get("price_deviation_limit_pct", Decimal("0.20")),
        fee_buffer_pct=run_context.get("fee_buffer_pct", Decimal("0")),
        lot_size=int(run_context.get("lot_size", 100) or 100),
        evidence_ref=_string_value(run_context.get("risk_profile_evidence_ref")),
    )


def _normalize_target_row(
    target_row: Mapping[str, object],
    run_context: Mapping[str, object],
    snapshots: FixtureSnapshots,
) -> dict[str, object]:
    row = dict(_mapping_from_object(target_row))
    if not _string_value(row.get("strategy_id")) and run_context.get("strategy_id"):
        row["strategy_id"] = run_context["strategy_id"]
    if not _string_value(row.get("run_id")) and run_context.get("run_id"):
        row["run_id"] = run_context["run_id"]
    if not _string_value(row.get("target_trade_date")) and run_context.get("target_trade_date"):
        row["target_trade_date"] = run_context["target_trade_date"]
    if not _string_value(row.get("signal_date")) and run_context.get("signal_date"):
        row["signal_date"] = run_context["signal_date"]

    target_qty = _int_value(row.get("target_qty") or row.get("quantity") or row.get("qty"))
    if target_qty:
        row["target_qty"] = abs(target_qty)
        row.setdefault("side", "sell" if target_qty < 0 else "buy")
        return row

    if row.get("target_weight") is None:
        row.setdefault("target_qty", 0)
        row.setdefault("side", _string_value(row.get("side")) or "buy")
        return row

    symbol = _string_value(row.get("symbol"))
    price = _raw_price_for_symbol(snapshots, symbol)
    total_value = _portfolio_total_value(snapshots)
    desired_qty = int(
        ((total_value * _decimal_value(row.get("target_weight"))) / price).to_integral_value(rounding=ROUND_FLOOR)
    ) if price > 0 else 0
    current_qty = int(snapshots.positions_available.get(symbol, 0))
    delta_qty = desired_qty - current_qty
    row["target_qty"] = abs(delta_qty)
    row["side"] = "sell" if delta_qty < 0 else "buy"
    return row


def _portfolio_total_value(snapshots: FixtureSnapshots) -> Decimal:
    total = _decimal_value(snapshots.cash_available)
    for symbol, quantity in snapshots.positions_available.items():
        total += Decimal(int(quantity)) * _raw_price_for_symbol(snapshots, symbol)
    return total


def _raw_price_for_symbol(snapshots: FixtureSnapshots, symbol: str) -> Decimal:
    raw_ref = snapshots.raw_price_refs.get(symbol) or snapshots.raw_price_refs.get("*")
    if isinstance(raw_ref, RawPriceRef):
        return _decimal_value(raw_ref.price)
    if isinstance(raw_ref, Mapping):
        return _decimal_value(raw_ref.get("price", raw_ref.get("raw_price", 0)))
    return _decimal_value(raw_ref)


def _adapter_request_for_intent(
    intent: OrderIntent,
    mode: str,
    risk_result: PretradeRiskResult,
    snapshots: FixtureSnapshots,
    run_context: Mapping[str, object],
) -> AdapterRequest:
    return AdapterRequest(
        intent_id=intent.order_intent_id,
        adapter_mode=mode,
        execution_price_policy=intent.execution_price_policy,
        risk_status=risk_result.status,
        side=intent.side,
        symbol=intent.symbol,
        quantity=intent.target_qty,
        order_price=float(_raw_price_for_symbol(snapshots, intent.symbol)),
        strategy_id=intent.strategy_id,
        run_id=intent.run_id,
        mock_scenario=_string_value(run_context.get("mock_scenario")) or MockBrokerScenario.ACCEPTED,
        evidence_ref=risk_result.evidence_ref,
    )


def _broker_lake_plans_for_intent(
    intent: OrderIntent,
    root_label: str,
    *transition_events: StateTransitionEvent | None,
) -> tuple[BrokerLakeWritePlan, ...]:
    plans = [dry_run_write_plan(order_intent_to_broker_lake_event(intent), root_label=root_label)]
    for transition_event in transition_events:
        if transition_event is None:
            continue
        plans.append(
            dry_run_write_plan(
                state_transition_to_broker_lake_event(intent, transition_event),
                root_label=root_label,
            )
        )
    return tuple(plans)


def _build_error_dry_run_plan(
    run_context: Mapping[str, object],
    root_label: str,
    stage: str,
    error_code: str,
) -> BrokerLakeWritePlan:
    trade_date = _string_value(
        run_context.get("target_trade_date")
        or run_context.get("trade_date")
        or run_context.get("signal_date")
    )
    payload = {
        "event_type": "error",
        "strategy_id": _string_value(run_context.get("strategy_id")) or "unknown-strategy",
        "run_id": _string_value(run_context.get("run_id")) or "unknown-run",
        "error_code": error_code,
        "error_stage": stage,
        "trade_date": trade_date or "unknown-trade-date",
    }
    return dry_run_write_plan(payload, root_label=root_label)


def _finalize_result(
    *,
    status: str,
    shadow_run_id: str,
    mode: str,
    policy_metadata: Mapping[str, object],
    intents: tuple[OrderIntent, ...],
    risk_results: tuple[PretradeRiskResult, ...],
    risk_batch_result: PretradeRiskBatchResult | None,
    adapter_results: tuple[AdapterResult, ...],
    broker_events: tuple[BrokerOrderEvent, ...],
    state_transitions: tuple[StateTransitionEvent, ...],
    dry_run_plans: tuple[BrokerLakeWritePlan, ...],
    blocked_reasons: tuple[str, ...],
    safety_counters: Mapping[str, int],
    adapter_call_count: int,
) -> ShadowRunResult:
    result = ShadowRunResult(
        status=status,
        shadow_run_id=shadow_run_id,
        mode=mode,
        policy_metadata=policy_metadata,
        intents=intents,
        risk_results=risk_results,
        risk_batch_result=risk_batch_result,
        adapter_results=adapter_results,
        broker_events=broker_events,
        state_transitions=state_transitions,
        dry_run_plans=dry_run_plans,
        blocked_reasons=blocked_reasons,
        audit_summary={},
        safety_counters=dict(safety_counters),
        adapter_call_count=adapter_call_count,
    )
    return ShadowRunResult(
        status=result.status,
        shadow_run_id=result.shadow_run_id,
        mode=result.mode,
        policy_metadata=result.policy_metadata,
        intents=result.intents,
        risk_results=result.risk_results,
        risk_batch_result=result.risk_batch_result,
        adapter_results=result.adapter_results,
        broker_events=result.broker_events,
        state_transitions=result.state_transitions,
        dry_run_plans=result.dry_run_plans,
        blocked_reasons=result.blocked_reasons,
        audit_summary=build_audit_summary(result),
        safety_counters=result.safety_counters,
        adapter_call_count=result.adapter_call_count,
    )


def _oms_blocked_reason(result: OmsResult) -> str:
    if result.error is None:
        return "order_intent_blocked"
    return result.error.error_code.value


def _shadow_run_id(run_context: Mapping[str, object], observed_at: datetime) -> str:
    return _string_value(run_context.get("shadow_run_id")) or (
        f"shadow-{_string_value(run_context.get('run_id')) or observed_at.strftime('%Y%m%d%H%M%S')}"
    )


def _first_non_empty_from_rows(rows: Sequence[Mapping[str, object]], key: str) -> str:
    for row in rows:
        value = _string_value(row.get(key))
        if value:
            return value
    return ""


def _mapping_from_object(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    if is_dataclass(value):
        return asdict(value)
    return {
        key: getattr(value, key)
        for key in dir(value)
        if not key.startswith("_") and not callable(getattr(value, key))
    }


def _first_non_empty(*values: object) -> str:
    for value in values:
        text = _string_value(value)
        if text:
            return text
    return ""


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value).strip()
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


def _observed_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = [
    "ALLOWED_SHADOW_MODES",
    "BLOCKED_ACTIVATION_MODES",
    "DEFAULT_BROKER_LAKE_ROOT_LABEL",
    "FixtureSnapshots",
    "ModeValidationResult",
    "PolicyMetadataValidation",
    "REQUIRED_POLICY_FIELDS",
    "ShadowRunInput",
    "ShadowRunResult",
    "build_audit_summary",
    "build_safety_counters",
    "build_target_order_intents",
    "shadow_run",
    "validate_policy_metadata",
    "validate_shadow_mode",
]
