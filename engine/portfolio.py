"""组合会计与 T+1 调仓成交模拟。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import hashlib
import json
import math
from typing import Any, Protocol

import pandas as pd

from engine.diagnostics import start_diagnostic

DEFAULT_COST_GRID_BPS = (0, 5, 10, 20)
CAPACITY_REPORT_REQUIRED_FIELDS = (
    "amount_participation_rate",
    "turnover",
    "holding_count",
    "sample_loss_count",
    "sample_loss_rate",
    "cost_erosion_bps",
    "cost_erosion_ratio",
)
CAPACITY_STRONG_CLAIMS = (
    "capacity_tradable",
    "capacity_supported",
    "liquidity_screened_capacity",
    "tradable_capacity",
    "capacity_analysis",
    "liquidity_controlled",
)
COST_SENSITIVITY_CLAIMS = ("cost_robust", "cost_sensitivity_supported")
UPSTREAM_REAL_CLAIMS = (
    "real_tradable_execution",
    "tradability_screened",
    "tradability_screened_execution",
    "true_fillability",
    "realistic_fillability",
    "real_vwap_execution",
    "vwap_fill_claim",
    "vwap_execution",
    "real_open_execution",
    "open_execution",
    "pure_alpha",
    "style_neutral_ic",
    "risk_model_adjusted_alpha",
    "capacity_size_supported",
)


class PortfolioError(Exception):
    """组合引擎基础异常。"""


class RebalanceIdempotencyError(PortfolioError):
    """重复调仓幂等键。"""


class TradeGate(Protocol):
    def can_execute_trade(self, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
        ...


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.0003
    slippage_rate: float = 0.0002
    sell_tax_rate: float = 0.001
    min_cash: float = 0.0
    max_positions: int | None = None


@dataclass(slots=True)
class PositionRecord:
    symbol: str
    quantity: float
    avg_cost: float
    market_price: float = 0.0
    market_value: float = 0.0
    last_trade_date: date | None = None


@dataclass(slots=True)
class TradeRecord:
    signal_date: date
    execution_date: date
    symbol: str
    side: str
    price: float
    quantity: float
    notional: float
    cost: float
    status: str
    reason: str = ""
    rebalance_key: str = ""


@dataclass(slots=True)
class CostRecord:
    execution_date: date
    symbol: str
    side: str
    commission: float
    slippage: float
    tax: float
    total_cost: float


@dataclass(slots=True)
class DailyPortfolioSnapshot:
    trade_date: date
    cash: float
    position_value: float
    total_value: float
    turnover_amount: float
    holdings: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class PortfolioState:
    cash: float
    positions: dict[str, PositionRecord] = field(default_factory=dict)
    applied_rebalance_keys: set[str] = field(default_factory=set)


@dataclass(slots=True)
class PortfolioResult:
    daily_snapshots: list[DailyPortfolioSnapshot]
    trades: list[TradeRecord]
    costs: list[CostRecord]
    final_state: PortfolioState
    turnover_amount: float
    trade_notional: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RebalanceSignal:
    signal_date: date
    execution_date: date
    target_symbols: list[str]
    params_hash: str = ""


def build_capacity_report(
    trades: list[TradeRecord] | list[dict[str, Any]] | pd.DataFrame | None,
    holdings: list[DailyPortfolioSnapshot] | list[dict[str, Any]] | pd.DataFrame | dict[str, Any] | None,
    liquidity_bundle: dict[str, Any] | None,
    *,
    portfolio_returns: dict[str, Any] | None = None,
    participation_limit: float | None = None,
    cost_sensitivity_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建 CR011-S07 容量报告，只消费调用方显式传入的离线对象。"""

    trade_records = _records_from_any(trades)
    holding_records = _records_from_any(holdings)
    bundle = _as_dict(liquidity_bundle)
    returns = _as_dict(portfolio_returns)
    cost_report = _as_dict(cost_sensitivity_report)

    filled = [row for row in trade_records if str(row.get("status") or "filled") == "filled"]
    unfilled = [row for row in trade_records if str(row.get("status") or "") == "unfilled"]
    trade_notional = sum(_positive_float(row.get("notional")) or 0.0 for row in filled)
    total_cost = sum(_finite_float(row.get("cost")) or 0.0 for row in filled)

    adv = _first_positive(bundle, "adv", "adv20", "average_daily_amount", "average_daily_notional")
    amount = _first_positive(bundle, "amount", "daily_amount", "amount_value", "average_amount")
    denominator = adv or amount
    amount_participation_rate = _safe_ratio(trade_notional, denominator)

    turnover = (
        _finite_float(bundle.get("turnover"))
        if bundle.get("turnover") is not None
        else _finite_float(returns.get("turnover") or returns.get("turnover_with_cost"))
    )
    if turnover is None:
        portfolio_value = _first_positive(returns, "portfolio_value", "initial_cash", "gross_exposure")
        turnover = _safe_ratio(trade_notional, portfolio_value)

    holding_count = _holding_count(holding_records, holdings)
    sample_loss_count = int(len(unfilled) + len(bundle.get("missing_fields") or []))
    sample_count = max(len(trade_records), int(bundle.get("sample_count") or 0), 1)
    sample_loss_rate = sample_loss_count / sample_count

    cost_erosion_bps = _cost_erosion_bps(cost_report, trade_notional, total_cost)
    gross_return = _first_number(returns, "gross_return", "annual_return_no_cost", "total_return_no_cost", "annual_return")
    cost_erosion_ratio = _safe_ratio((cost_erosion_bps or 0.0) / 10000.0, abs(gross_return)) if gross_return not in (None, 0.0) else None

    liquidity_status = str(
        bundle.get("liquidity_capacity_status")
        or bundle.get("status")
        or ("blocked_missing_liquidity" if bundle.get("missing_fields") else "available")
    )
    missing_reasons = [str(item) for item in bundle.get("missing_reasons") or []]
    if not bundle:
        liquidity_status = "blocked_missing_liquidity"
        missing_reasons = ["liquidity_capacity_inputs_missing"]
    elif liquidity_status in {"required_missing", "partial", "missing", "source_unresolved"}:
        liquidity_status = "blocked_missing_liquidity"

    blocked_claims: list[dict[str, Any]] = []
    if liquidity_status != "available":
        blocked_claims.extend(
            _claim_payload(claim, "liquidity_capacity_inputs", "capacity_inputs_missing", "CR011-S07")
            for claim in CAPACITY_STRONG_CLAIMS
        )
    if not trade_records:
        blocked_claims.append(
            _claim_payload("capacity_supported", "portfolio_trades", "capacity_trades_missing", "CR011-S07")
        )

    status = "pass"
    if liquidity_status != "available":
        status = "blocked_missing_liquidity"
    elif not trade_records:
        status = "blocked_missing_trades"
    elif participation_limit is not None and amount_participation_rate is not None and amount_participation_rate > participation_limit:
        status = "warn"

    return _json_safe_dict(
        {
            "capacity_report_status": status,
            "liquidity_capacity_status": liquidity_status,
            "amount_participation_rate": amount_participation_rate,
            "turnover": turnover,
            "holding_count": holding_count,
            "sample_loss_count": sample_loss_count,
            "sample_loss_rate": sample_loss_rate,
            "cost_erosion_bps": cost_erosion_bps,
            "cost_erosion_ratio": cost_erosion_ratio,
            "filled_trade_count": len(filled),
            "unfilled_trade_count": len(unfilled),
            "trade_notional": trade_notional,
            "participation_limit": participation_limit,
            "missing_reasons": missing_reasons,
            "required_fields": list(CAPACITY_REPORT_REQUIRED_FIELDS),
            "blocked_claims": _dedupe_claim_payloads(blocked_claims),
        }
    )


def run_cost_sensitivity_grid(
    strategy_result: dict[str, Any] | None,
    trades: list[TradeRecord] | list[dict[str, Any]] | pd.DataFrame | None = None,
    *,
    cost_grid_bps: list[int] | tuple[int, ...] = DEFAULT_COST_GRID_BPS,
) -> dict[str, Any]:
    """按固定四档成本网格输出成本敏感性报告。"""

    result = _as_dict(strategy_result)
    grid = tuple(int(item) for item in cost_grid_bps)
    unique_grid = tuple(dict.fromkeys(grid))
    gross_return = _first_number(result, "gross_return", "annual_return_no_cost", "total_return_no_cost", "annual_return")
    turnover = _first_number(result, "turnover", "turnover_with_cost")
    if turnover is None:
        turnover = _safe_ratio(_trade_notional_from_records(_records_from_any(trades)), _first_positive(result, "portfolio_value", "initial_cash"))
    turnover = float(turnover or 0.0)

    scenarios: list[dict[str, Any]] = []
    for cost_bps in grid:
        cost_erosion = turnover * cost_bps / 10000.0
        cost_after_return = None if gross_return is None else float(gross_return) - cost_erosion
        scenarios.append(
            {
                "cost_scenario_id": f"cost_{cost_bps}bps",
                "cost_bps": cost_bps,
                "gross_return": gross_return,
                "turnover": turnover,
                "cost_after_return": cost_after_return,
                "cost_erosion": cost_erosion,
                "cost_erosion_bps": cost_erosion * 10000.0,
                "status": "evaluated",
            }
        )

    blocked_claims: list[dict[str, Any]] = []
    if unique_grid != DEFAULT_COST_GRID_BPS:
        reason = "single_cost_point_not_allowed" if len(unique_grid) == 1 else "invalid_cost_grid"
        blocked_claims.extend(
            _claim_payload(claim, "cost_grid_bps", reason, "CR011-S07")
            for claim in COST_SENSITIVITY_CLAIMS
        )
    status = "fail" if blocked_claims else "pass"
    return _json_safe_dict(
        {
            "cost_grid_bps": list(grid),
            "expected_cost_grid_bps": list(DEFAULT_COST_GRID_BPS),
            "cost_sensitivity_status": status,
            "scenario_count": len(scenarios),
            "cost_scenarios": scenarios,
            "blocked_claims": _dedupe_claim_payloads(blocked_claims),
        }
    )


def evaluate_capacity_cost_claims(
    capacity_report: dict[str, Any],
    cost_report: dict[str, Any],
    upstream_claims: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """合并 S03/S04/S06 blocked claims，并判定 S07 容量 / 成本声明。"""

    capacity = _as_dict(capacity_report)
    cost = _as_dict(cost_report)
    upstream_allowed, upstream_blocked = _split_upstream_claims(upstream_claims)
    blocked_claims = [
        *upstream_blocked,
        *[dict(item) for item in capacity.get("blocked_claims") or [] if isinstance(item, dict)],
        *[dict(item) for item in cost.get("blocked_claims") or [] if isinstance(item, dict)],
    ]

    capacity_status = str(capacity.get("capacity_report_status") or capacity.get("liquidity_capacity_status") or "blocked_missing_liquidity")
    cost_status = str(cost.get("cost_sensitivity_status") or "fail")
    if capacity_status != "pass" and not any(item.get("claim") in CAPACITY_STRONG_CLAIMS for item in blocked_claims):
        blocked_claims.extend(
            _claim_payload(claim, "liquidity_capacity_inputs", capacity_status, "CR011-S07")
            for claim in CAPACITY_STRONG_CLAIMS
        )
    if cost_status != "pass" and not any(item.get("claim") in COST_SENSITIVITY_CLAIMS for item in blocked_claims):
        blocked_claims.extend(
            _claim_payload(claim, "cost_grid_bps", "cost_sensitivity_not_passed", "CR011-S07")
            for claim in COST_SENSITIVITY_CLAIMS
        )

    blocked_claims = _dedupe_claim_payloads(blocked_claims)
    blocked_names = {str(item.get("claim") or "") for item in blocked_claims}
    allowed_claims = _ordered_unique([*upstream_allowed, "framework_validation", "exploratory_analysis"])
    if capacity_status == "pass":
        allowed_claims.extend(CAPACITY_STRONG_CLAIMS[:3])
    if cost_status == "pass":
        allowed_claims.extend(COST_SENSITIVITY_CLAIMS)
    allowed_claims = [claim for claim in _ordered_unique(allowed_claims) if claim not in blocked_names and claim not in UPSTREAM_REAL_CLAIMS]

    if any(claim in blocked_names for claim in CAPACITY_STRONG_CLAIMS):
        capacity_cost_status = "blocked_missing_liquidity" if capacity_status == "blocked_missing_liquidity" else "fail"
    elif cost_status != "pass":
        capacity_cost_status = "fail"
    elif capacity_status == "warn":
        capacity_cost_status = "warn"
    else:
        capacity_cost_status = "pass"

    return _json_safe_dict(
        {
            "liquidity_capacity_status": str(capacity.get("liquidity_capacity_status") or capacity_status),
            "capacity_cost_status": capacity_cost_status,
            "cost_sensitivity_status": cost_status,
            "allowed_claims": allowed_claims,
            "blocked_claims": blocked_claims,
            "blocked_capacity_claim_count": sum(1 for item in blocked_claims if item.get("claim") in CAPACITY_STRONG_CLAIMS),
        }
    )


def run_portfolio(
    close_df: pd.DataFrame,
    signal_results: list[RebalanceSignal | dict[str, Any]],
    config: PortfolioConfig | None = None,
    *,
    trade_gate: TradeGate | None = None,
    limit_gate: TradeGate | None = None,
) -> PortfolioResult:
    """执行 T+1 调仓，先卖后买并保持会计恒等式。"""

    cfg = config or PortfolioConfig()
    diag = start_diagnostic(
        "portfolio",
        "STORY-005",
        {
            "rows": len(close_df),
            "symbols": len(close_df.columns),
            "signals": len(signal_results),
            "initial_cash": cfg.initial_cash,
        },
    )
    try:
        state = PortfolioState(cash=float(cfg.initial_cash))
        signals = [_coerce_signal(item) for item in signal_results]
        signals_by_date: dict[date, list[RebalanceSignal]] = {}
        for signal in signals:
            signals_by_date.setdefault(signal.execution_date, []).append(signal)

        trades: list[TradeRecord] = []
        costs: list[CostRecord] = []
        snapshots: list[DailyPortfolioSnapshot] = []
        turnover_amount = 0.0
        for trade_date in close_df.index:
            execution_date = _coerce_date(trade_date)
            _mark_to_market(state, close_df.loc[trade_date])
            for signal in signals_by_date.get(execution_date, []):
                key = rebalance_key(signal)
                if key in state.applied_rebalance_keys:
                    raise RebalanceIdempotencyError(f"重复 rebalance_key: {key}")
                state.applied_rebalance_keys.add(key)
                period_trades, period_costs = apply_rebalance(
                    state,
                    close_df.loc[trade_date],
                    signal,
                    cfg,
                    trade_gate=trade_gate,
                    limit_gate=limit_gate,
                    rebalance_key_value=key,
                )
                trades.extend(period_trades)
                costs.extend(period_costs)
                turnover_amount += sum(trade.notional for trade in period_trades if trade.status == "filled")
                _mark_to_market(state, close_df.loc[trade_date])
            position_value = sum(position.market_value for position in state.positions.values())
            total_value = state.cash + position_value
            snapshots.append(
                DailyPortfolioSnapshot(
                    trade_date=execution_date,
                    cash=state.cash,
                    position_value=position_value,
                    total_value=total_value,
                    turnover_amount=turnover_amount,
                    holdings={symbol: pos.quantity for symbol, pos in state.positions.items() if pos.quantity > 0},
                )
            )
            _assert_accounting_identity(snapshots[-1])
        unfilled = [trade.reason for trade in trades if trade.status == "unfilled"]
        if unfilled:
            diag.warning("unfilled", unfilled_count=len(unfilled), reasons=sorted(set(unfilled)))
        result = PortfolioResult(
            daily_snapshots=snapshots,
            trades=trades,
            costs=costs,
            final_state=state,
            turnover_amount=turnover_amount,
            trade_notional=turnover_amount,
            metadata={"accounting_identity": "validated"},
        )
        diag.end("success", trades=len(trades), snapshots=len(snapshots))
        return result
    except Exception as exc:
        diag.error(exc)
        raise


def apply_rebalance(
    state: PortfolioState,
    prices: pd.Series,
    signal: RebalanceSignal,
    config: PortfolioConfig,
    *,
    trade_gate: TradeGate | None = None,
    limit_gate: TradeGate | None = None,
    rebalance_key_value: str = "",
) -> tuple[list[TradeRecord], list[CostRecord]]:
    targets = set(signal.target_symbols)
    current = set(state.positions)
    trades: list[TradeRecord] = []
    costs: list[CostRecord] = []

    for symbol in sorted(current - targets):
        trade, cost = _sell_all(state, prices, signal, config, symbol, trade_gate, limit_gate, rebalance_key_value)
        trades.append(trade)
        if cost:
            costs.append(cost)

    target_symbols = sorted(targets)
    if config.max_positions is not None:
        target_symbols = target_symbols[: config.max_positions]
    if not target_symbols:
        return trades, costs
    _mark_to_market(state, prices)
    total_value = state.cash + sum(position.market_value for position in state.positions.values())
    target_value = total_value / len(target_symbols)
    buy_orders: list[tuple[str, float, float]] = []
    required_cash = 0.0
    for symbol in target_symbols:
        price = _price_for(prices, symbol)
        if price is None:
            trades.append(_unfilled(signal, symbol, "buy", "missing_execution_price", rebalance_key_value))
            continue
        current_value = state.positions.get(symbol, PositionRecord(symbol, 0, 0)).market_value
        buy_value = max(target_value - current_value, 0.0)
        if buy_value <= 0:
            continue
        total_cost = _trade_cost(buy_value, "buy", config)
        buy_orders.append((symbol, price, buy_value))
        required_cash += buy_value + total_cost.total_cost
    scale = 1.0
    available_cash = max(state.cash - config.min_cash, 0.0)
    if required_cash > available_cash > 0:
        scale = available_cash / required_cash
    elif required_cash > 0 and available_cash <= 0:
        scale = 0.0
    for symbol, price, buy_value in buy_orders:
        scaled_notional = buy_value * scale
        if scaled_notional <= 0:
            trades.append(_unfilled(signal, symbol, "buy", "cash_insufficient", rebalance_key_value))
            continue
        if not _allowed(trade_gate, symbol, signal.execution_date, "buy")[0]:
            allowed, reason = _allowed(trade_gate, symbol, signal.execution_date, "buy")
            trades.append(_unfilled(signal, symbol, "buy", reason if not allowed else "", rebalance_key_value))
            continue
        if not _allowed(limit_gate, symbol, signal.execution_date, "buy")[0]:
            allowed, reason = _allowed(limit_gate, symbol, signal.execution_date, "buy")
            trades.append(_unfilled(signal, symbol, "buy", reason if not allowed else "", rebalance_key_value))
            continue
        cost = _trade_cost(scaled_notional, "buy", config)
        quantity = scaled_notional / price
        state.cash -= scaled_notional + cost.total_cost
        position = state.positions.get(symbol)
        if position is None:
            position = PositionRecord(symbol=symbol, quantity=0.0, avg_cost=0.0)
            state.positions[symbol] = position
        total_quantity = position.quantity + quantity
        position.avg_cost = ((position.quantity * position.avg_cost) + scaled_notional) / total_quantity
        position.quantity = total_quantity
        position.last_trade_date = signal.execution_date
        trades.append(_filled(signal, symbol, "buy", price, quantity, scaled_notional, cost.total_cost, rebalance_key_value))
        costs.append(cost)
    return trades, costs


def rebalance_key(signal: RebalanceSignal) -> str:
    params_hash = signal.params_hash or hashlib.sha256(
        json.dumps(signal.target_symbols, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    return f"{signal.signal_date}|{signal.execution_date}|{params_hash}"


def _sell_all(
    state: PortfolioState,
    prices: pd.Series,
    signal: RebalanceSignal,
    config: PortfolioConfig,
    symbol: str,
    trade_gate: TradeGate | None,
    limit_gate: TradeGate | None,
    key: str,
) -> tuple[TradeRecord, CostRecord | None]:
    position = state.positions[symbol]
    price = _price_for(prices, symbol)
    if price is None:
        return _unfilled(signal, symbol, "sell", "missing_execution_price", key), None
    for gate in (trade_gate, limit_gate):
        allowed, reason = _allowed(gate, symbol, signal.execution_date, "sell")
        if not allowed:
            return _unfilled(signal, symbol, "sell", reason, key), None
    notional = position.quantity * price
    cost = _trade_cost(notional, "sell", config, signal.execution_date, symbol)
    state.cash += notional - cost.total_cost
    del state.positions[symbol]
    return _filled(signal, symbol, "sell", price, position.quantity, notional, cost.total_cost, key), cost


def _trade_cost(notional: float, side: str, config: PortfolioConfig, trade_date: date | None = None, symbol: str = "") -> CostRecord:
    commission = notional * config.commission_rate
    slippage = notional * config.slippage_rate
    tax = notional * config.sell_tax_rate if side == "sell" else 0.0
    return CostRecord(
        execution_date=trade_date or date.min,
        symbol=symbol,
        side=side,
        commission=commission,
        slippage=slippage,
        tax=tax,
        total_cost=commission + slippage + tax,
    )


def _filled(signal: RebalanceSignal, symbol: str, side: str, price: float, quantity: float, notional: float, cost: float, key: str) -> TradeRecord:
    return TradeRecord(signal.signal_date, signal.execution_date, symbol, side, price, quantity, notional, cost, "filled", rebalance_key=key)


def _unfilled(signal: RebalanceSignal, symbol: str, side: str, reason: str, key: str) -> TradeRecord:
    return TradeRecord(signal.signal_date, signal.execution_date, symbol, side, 0.0, 0.0, 0.0, 0.0, "unfilled", reason, key)


def _price_for(prices: pd.Series, symbol: str) -> float | None:
    if symbol not in prices.index or pd.isna(prices[symbol]) or float(prices[symbol]) <= 0:
        return None
    return float(prices[symbol])


def _mark_to_market(state: PortfolioState, prices: pd.Series) -> None:
    for symbol, position in list(state.positions.items()):
        price = _price_for(prices, symbol)
        if price is not None:
            position.market_price = price
            position.market_value = position.quantity * price


def _allowed(gate: TradeGate | None, symbol: str, trade_date: date, side: str) -> tuple[bool, str]:
    if gate is None:
        return True, ""
    return gate.can_execute_trade(symbol, trade_date, side)


def _assert_accounting_identity(snapshot: DailyPortfolioSnapshot) -> None:
    if abs((snapshot.cash + snapshot.position_value) - snapshot.total_value) > 1e-6:
        raise PortfolioError(f"会计恒等式失败: {snapshot.trade_date}")


def _coerce_signal(item: RebalanceSignal | dict[str, Any]) -> RebalanceSignal:
    if isinstance(item, RebalanceSignal):
        return item
    return RebalanceSignal(
        signal_date=_coerce_date(item["signal_date"]),
        execution_date=_coerce_date(item["execution_date"]),
        target_symbols=list(item.get("target_symbols") or []),
        params_hash=str(item.get("params_hash") or ""),
    )


def _coerce_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return pd.to_datetime(value).date()


def _records_from_any(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return [dict(item) for item in value.to_dict(orient="records")]
    if isinstance(value, dict):
        if "rows" in value and isinstance(value["rows"], list):
            return _records_from_any(value["rows"])
        return [dict(value)]
    if isinstance(value, list) or isinstance(value, tuple):
        records: list[dict[str, Any]] = []
        for item in value:
            records.extend(_records_from_any(item))
        return records
    if hasattr(value, "__dataclass_fields__"):
        return [asdict(value)]
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return {}


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _positive_float(value: Any) -> float | None:
    number = _finite_float(value)
    if number is None or number <= 0:
        return None
    return number


def _first_number(values: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        number = _finite_float(values.get(key))
        if number is not None:
            return number
    return None


def _first_positive(values: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        number = _positive_float(values.get(key))
        if number is not None:
            return number
    return None


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return float(numerator) / float(denominator)


def _trade_notional_from_records(records: list[dict[str, Any]]) -> float:
    return sum(_positive_float(row.get("notional")) or 0.0 for row in records if str(row.get("status") or "filled") == "filled")


def _holding_count(records: list[dict[str, Any]], original: Any) -> int:
    if isinstance(original, dict) and "holdings" not in original:
        return sum(1 for value in original.values() if (_finite_float(value) or 0.0) != 0.0)
    counts: list[int] = []
    for row in records:
        holdings = row.get("holdings")
        if isinstance(holdings, dict):
            counts.append(sum(1 for value in holdings.values() if (_finite_float(value) or 0.0) != 0.0))
        elif "holding_count" in row:
            number = _finite_float(row.get("holding_count"))
            if number is not None:
                counts.append(int(number))
    if not counts:
        return 0
    return int(round(sum(counts) / len(counts)))


def _cost_erosion_bps(cost_report: dict[str, Any], trade_notional: float, total_cost: float) -> float | None:
    scenarios = cost_report.get("cost_scenarios") if isinstance(cost_report.get("cost_scenarios"), list) else []
    scenario_values = [
        _finite_float(item.get("cost_erosion_bps"))
        for item in scenarios
        if isinstance(item, dict) and _finite_float(item.get("cost_erosion_bps")) is not None
    ]
    if scenario_values:
        return max(float(item) for item in scenario_values if item is not None)
    if trade_notional > 0 and total_cost > 0:
        return total_cost / trade_notional * 10000.0
    return None


def _claim_payload(claim: str, missing_capability: str, reason: str, source_story: str) -> dict[str, Any]:
    return {
        "claim": claim,
        "missing_capability": missing_capability,
        "reason": reason,
        "severity": "BLOCKING",
        "source_story": source_story,
    }


def _split_upstream_claims(upstream_claims: dict[str, Any] | list[dict[str, Any]] | None) -> tuple[list[str], list[dict[str, Any]]]:
    if upstream_claims is None:
        return [], []
    if isinstance(upstream_claims, dict):
        allowed = [str(item) for item in upstream_claims.get("allowed_claims") or []]
        blocked = [dict(item) for item in upstream_claims.get("blocked_claims") or [] if isinstance(item, dict)]
        return allowed, blocked
    return [], [dict(item) for item in upstream_claims if isinstance(item, dict)]


def _dedupe_claim_payloads(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        claim = str(item.get("claim") or "")
        reason = str(item.get("reason") or item.get("reason_code") or item.get("blocked_reason") or "")
        source_story = str(item.get("source_story") or "")
        key = (claim, reason, source_story)
        if key in seen:
            continue
        seen.add(key)
        output.append(_json_safe_dict(item))
    return output


def _ordered_unique(values: list[str] | tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _json_safe_dict(payload: dict[str, Any]) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, tuple):
            return [convert(item) for item in value]
        if isinstance(value, (date, pd.Timestamp)):
            return value.isoformat()
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, int) or isinstance(value, str) or isinstance(value, bool) or value is None:
            return value
        number = _finite_float(value)
        return number if number is not None else str(value)

    return {str(key): convert(value) for key, value in payload.items()}


__all__ = (
    "CAPACITY_REPORT_REQUIRED_FIELDS",
    "CAPACITY_STRONG_CLAIMS",
    "COST_SENSITIVITY_CLAIMS",
    "CostRecord",
    "DailyPortfolioSnapshot",
    "DEFAULT_COST_GRID_BPS",
    "PortfolioConfig",
    "PortfolioError",
    "PortfolioResult",
    "PortfolioState",
    "PositionRecord",
    "RebalanceIdempotencyError",
    "RebalanceSignal",
    "TradeGate",
    "TradeRecord",
    "apply_rebalance",
    "build_capacity_report",
    "evaluate_capacity_cost_claims",
    "rebalance_key",
    "run_cost_sensitivity_grid",
    "run_portfolio",
)
