"""多因子目标组合到模拟订单计划的离线合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
import hashlib
from typing import Any, Mapping

from market_data.contracts import ADJUSTMENT_POLICY_RAW
from trading.oms import OrderIntent, create_order_intent
from trading.pretrade_risk import (
    PretradeRiskBatchResult,
    RiskInputSnapshot,
    RiskProfile,
    evaluate_many,
)


SIMULATION_ORDER_PLAN_SCHEMA_VERSION = "runner-simulation-order-plan-v1"


@dataclass(frozen=True, slots=True)
class SimulationOrderPlanRequest:
    """P2 订单计划输入；只生成计划，不触达 QMT runtime。"""

    strategy_id: str
    run_id: str
    target_trade_date: str
    target_rows: tuple[Mapping[str, object], ...]
    capital_base: Decimal | int | float | str
    risk_snapshot: RiskInputSnapshot
    risk_profile: RiskProfile
    current_positions: Mapping[str, int] = field(default_factory=dict)
    max_turnover_notional: Decimal | int | float | str | None = None
    lot_size: int = 100
    schema_version: str = SIMULATION_ORDER_PLAN_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SimulationOrderPlanItem:
    """单条计划委托；内部持有 OrderIntent，输出时必须脱敏。"""

    intent: OrderIntent
    instrument_ref: str
    side: str
    quantity: int
    price: Decimal
    price_ref: str
    notional_bucket: str
    risk_status: str = "pending"
    blocked_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "order_intent_id": self.intent.order_intent_id,
            "instrument_ref": self.instrument_ref,
            "side": self.side,
            "quantity_bucket": _quantity_bucket(self.quantity),
            "price_ref": self.price_ref,
            "notional_bucket": self.notional_bucket,
            "risk_status": self.risk_status,
            "blocked_reason": self.blocked_reason,
            "qmt_allowed": False,
            "not_authorization": True,
        }


@dataclass(frozen=True, slots=True)
class SimulationOrderPlanResult:
    """P2 订单计划结果；不包含原始证券代码、账户或 broker ref。"""

    status: str
    run_id: str
    orders: tuple[SimulationOrderPlanItem, ...] = ()
    blocked_reason: str = ""
    risk_result: PretradeRiskBatchResult | None = None
    schema_version: str = SIMULATION_ORDER_PLAN_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "generated"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def order_intents(self) -> tuple[OrderIntent, ...]:
        return tuple(item.intent for item in self.orders)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "run_id": self.run_id,
            "blocked_reason": self.blocked_reason,
            "order_count": len(self.orders),
            "orders": [item.to_dict() for item in self.orders],
            "risk_profile_id": self.risk_result.risk_profile_id if self.risk_result else "",
            "safety_counters": dict(self.safety_counters),
        }


def build_simulation_order_plan(request: SimulationOrderPlanRequest) -> SimulationOrderPlanResult:
    """把目标组合转换为 buy/sell intent 计划；不提交、不撤单。"""

    missing = [
        name
        for name, value in (
            ("strategy_id", request.strategy_id),
            ("run_id", request.run_id),
            ("target_trade_date", request.target_trade_date),
        )
        if not value
    ]
    if missing:
        return _blocked(request.run_id, "required_field_missing:" + ",".join(missing))
    if not request.target_rows:
        return _blocked(request.run_id, "target_rows_empty")
    try:
        planned = tuple(_build_plan_item(row, request) for row in request.target_rows)
    except (ValueError, TypeError, ArithmeticError):
        return _blocked(request.run_id, "order_plan_input_invalid")
    orders = tuple(item for item in planned if item is not None)
    if _turnover_blocked(orders, request):
        return _blocked(request.run_id, "turnover_limit_exceeded")
    if not orders:
        return SimulationOrderPlanResult(status="generated", run_id=request.run_id)
    risk = evaluate_many(tuple(item.intent for item in orders), request.risk_snapshot, request.risk_profile)
    if not risk.passed:
        risk_by_intent = {result.intent_id: result for result in risk.results}
        blocked_orders = tuple(
            SimulationOrderPlanItem(
                intent=item.intent,
                instrument_ref=item.instrument_ref,
                side=item.side,
                quantity=item.quantity,
                price=item.price,
                price_ref=item.price_ref,
                notional_bucket=item.notional_bucket,
                risk_status=risk_by_intent[item.intent.order_intent_id].status,
                blocked_reason=risk_by_intent[item.intent.order_intent_id].blocked_reason,
            )
            for item in orders
        )
        return SimulationOrderPlanResult(
            status="blocked",
            run_id=request.run_id,
            orders=blocked_orders,
            blocked_reason="pretrade_risk_blocked",
            risk_result=risk,
        )
    passed_orders = tuple(
        SimulationOrderPlanItem(
            intent=item.intent,
            instrument_ref=item.instrument_ref,
            side=item.side,
            quantity=item.quantity,
            price=item.price,
            price_ref=item.price_ref,
            notional_bucket=item.notional_bucket,
            risk_status="pass",
        )
        for item in orders
    )
    return SimulationOrderPlanResult(
        status="generated",
        run_id=request.run_id,
        orders=passed_orders,
        risk_result=risk,
    )


def _build_plan_item(
    row: Mapping[str, object],
    request: SimulationOrderPlanRequest,
) -> SimulationOrderPlanItem | None:
    symbol = str(row.get("symbol") or "")
    if not symbol:
        raise ValueError("target row missing symbol")
    price = _price_for_symbol(request.risk_snapshot, symbol)
    if price <= 0:
        raise ValueError("raw price missing")
    target_qty = _target_quantity(row, request, price)
    current_qty = int(request.current_positions.get(symbol, request.risk_snapshot.positions_available.get(symbol, 0)))
    delta = target_qty - current_qty
    lot_size = max(int(request.lot_size or request.risk_profile.lot_size or 100), 1)
    order_qty = abs(delta) // lot_size * lot_size
    if order_qty <= 0:
        return None
    side = "buy" if delta > 0 else "sell"
    created = create_order_intent(
        {
            "strategy_id": request.strategy_id,
            "run_id": request.run_id,
            "symbol": symbol,
            "side": side,
            "target_trade_date": request.target_trade_date,
            "target_qty": order_qty,
            "signal_date": str(row.get("signal_date") or request.target_trade_date),
        },
        {"research_adjustment_policy": ADJUSTMENT_POLICY_RAW, "execution_price_policy": ADJUSTMENT_POLICY_RAW},
        {"risk_profile_id": request.risk_profile.risk_profile_id},
    )
    if not created.ok or created.intent is None:
        raise ValueError("order intent creation failed")
    return SimulationOrderPlanItem(
        intent=created.intent,
        instrument_ref=_stable_ref(symbol, "instrument"),
        side=side,
        quantity=order_qty,
        price=price,
        price_ref=_stable_ref(str(price), "price"),
        notional_bucket=_notional_bucket(Decimal(order_qty) * price),
    )


def _target_quantity(
    row: Mapping[str, object],
    request: SimulationOrderPlanRequest,
    price: Decimal,
) -> int:
    if row.get("target_qty") is not None:
        qty = max(int(row["target_qty"]), 0)
    else:
        weight = Decimal(str(row.get("target_weight") or 0))
        capital = Decimal(str(request.capital_base))
        if weight < 0 or capital <= 0:
            raise ValueError("invalid target weight or capital")
        qty = int((capital * weight / price).to_integral_value(rounding=ROUND_DOWN))
    lot_size = max(int(request.lot_size or request.risk_profile.lot_size or 100), 1)
    return qty // lot_size * lot_size


def _turnover_blocked(
    orders: tuple[SimulationOrderPlanItem, ...],
    request: SimulationOrderPlanRequest,
) -> bool:
    if request.max_turnover_notional is None:
        return False
    limit = Decimal(str(request.max_turnover_notional))
    if limit <= 0:
        return True
    total = sum(
        Decimal(item.quantity) * _price_for_symbol(request.risk_snapshot, item.intent.symbol)
        for item in orders
    )
    return total > limit


def _price_for_symbol(snapshot: RiskInputSnapshot, symbol: str) -> Decimal:
    ref = snapshot.raw_price_refs.get(symbol)
    if ref is None:
        return Decimal("0")
    if isinstance(ref, Mapping):
        return Decimal(str(ref.get("price") or 0))
    return Decimal(str(getattr(ref, "price", 0) or 0))


def _notional_bucket(value: Decimal) -> str:
    if value <= 0:
        return "notional:zero"
    if value < Decimal("10000"):
        return "notional:lt_10k"
    if value < Decimal("100000"):
        return "notional:10k_100k"
    return "notional:gte_100k"


def _quantity_bucket(value: int) -> str:
    if value <= 0:
        return "qty:zero"
    if value < 1000:
        return "qty:lt_1k"
    if value < 10000:
        return "qty:1k_10k"
    return "qty:gte_10k"


def _blocked(run_id: str, reason: str) -> SimulationOrderPlanResult:
    return SimulationOrderPlanResult(status="blocked", run_id=run_id, blocked_reason=reason)


def _stable_ref(value: str, prefix: str) -> str:
    return prefix + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _zero_safety_counters() -> dict[str, int]:
    return {
        "credential_read": 0,
        "qmt_operation": 0,
        "qmt_api_call": 0,
        "real_order": 0,
        "real_cancel": 0,
        "account_query": 0,
        "account_write": 0,
        "provider_fetch": 0,
        "lake_write": 0,
        "publish": 0,
        "simulation_or_live_run": 0,
    }
