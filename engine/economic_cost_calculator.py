"""CR-168 S02 的纯 Decimal 经济成本计算器。

此模块不读取任何外部状态，也不导入 evidence producer。它只消费已经通过
S01 校验的规范化值，并在防御性 numeric guard 失败时返回可映射回既有 C3
reason code 的异常。真实 TCA、校准、ADV、capacity 与运行时操作均不属于本模块。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import TYPE_CHECKING, Any

from engine.strategy_evidence import canonical_json_value

if TYPE_CHECKING:
    from engine.economic_cost_evidence import NormalizedEconomicCostInput


DECIMAL_PRECISION = 28


class EconomicCostCalculationError(ValueError):
    """将 numeric guard 明确映射到既有 C3 fail-closed reason code。"""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


@dataclass(frozen=True, slots=True)
class CostBreakdownV1:
    """五分项的 raw Decimal 与最终货币量化结果。"""

    fee: Decimal
    tax: Decimal
    spread: Decimal
    slippage: Decimal
    impact: Decimal
    participation_proxy: Decimal
    impact_rate: Decimal
    raw_total_cost: Decimal
    total_cost: Decimal
    gross_pnl: Decimal
    net_pnl: Decimal
    net_return: Decimal
    currency_minor_unit: Decimal

    def to_dict(self) -> dict[str, Any]:
        """返回仅含 canonical JSON primitive 的 component body。"""

        data = asdict(self)
        return canonical_json_value({key: _decimal_text(value) for key, value in data.items()})


def calculate_cost_breakdown(value: "NormalizedEconomicCostInput") -> CostBreakdownV1:
    """计算固定的五分项与 gross-to-net reconciliation。

    前置条件是 S01 返回 validation-clean input；本函数仍以防御性 guard 阻断
    直接调用时的非法 reference、minor unit 或不可能 numeric 状态。
    """

    gross_candidates = {
        "gross_pnl": value.gross_pnl,
        "gross_return": value.gross_return,
    }
    if all(item is None for item in gross_candidates.values()):
        raise EconomicCostCalculationError(
            "c3_gross_performance_basis_missing",
            "performance",
            "gross_pnl or gross_return is required.",
        )
    _require_optional_finite_values(gross_candidates)

    required = {
        "performance_notional": value.performance_notional,
        "traded_notional": value.traded_notional,
        "sell_notional": value.sell_notional,
        "turnover": value.turnover,
        "fee_rate": value.fee_rate,
        "fee_fixed_amount": value.fee_fixed_amount,
        "tax_rate": value.tax_rate,
        "tax_fixed_amount": value.tax_fixed_amount,
        "effective_spread_rate": value.effective_spread_rate,
        "effective_slippage_rate": value.effective_slippage_rate,
        "impact_coefficient": value.impact_coefficient,
        "static_reference_notional": value.static_reference_notional,
        "currency_minor_unit": value.currency_minor_unit,
    }
    _require_finite_values(required)

    performance_notional = _required_decimal(required, "performance_notional")
    traded_notional = _required_decimal(required, "traded_notional")
    sell_notional = _required_decimal(required, "sell_notional")
    turnover = _required_decimal(required, "turnover")
    fee_rate = _required_decimal(required, "fee_rate")
    fee_fixed_amount = _required_decimal(required, "fee_fixed_amount")
    tax_rate = _required_decimal(required, "tax_rate")
    tax_fixed_amount = _required_decimal(required, "tax_fixed_amount")
    effective_spread_rate = _required_decimal(required, "effective_spread_rate")
    effective_slippage_rate = _required_decimal(required, "effective_slippage_rate")
    impact_coefficient = _required_decimal(required, "impact_coefficient")
    static_reference_notional = _required_decimal(required, "static_reference_notional")
    minor_unit = _required_decimal(required, "currency_minor_unit")

    if performance_notional <= 0:
        raise EconomicCostCalculationError(
            "c3_gross_performance_basis_missing",
            "performance_notional",
            "performance_notional must be positive for gross-to-net reconciliation.",
        )
    if minor_unit <= 0:
        raise EconomicCostCalculationError(
            "c3_unit_price_notional_basis_mismatch",
            "currency_minor_unit",
            "currency_minor_unit must be positive.",
        )
    nonnegative_values = {
        "traded_notional": traded_notional,
        "sell_notional": sell_notional,
        "turnover": turnover,
        "fee_rate": fee_rate,
        "fee_fixed_amount": fee_fixed_amount,
        "tax_rate": tax_rate,
        "tax_fixed_amount": tax_fixed_amount,
        "effective_spread_rate": effective_spread_rate,
        "effective_slippage_rate": effective_slippage_rate,
        "impact_coefficient": impact_coefficient,
    }
    if any(item < 0 for item in nonnegative_values.values()) or static_reference_notional <= 0:
        raise EconomicCostCalculationError(
            "c3_negative_cost_invalid",
            "cost_assumptions",
            "Costs, rates, bases and static reference must be non-negative; static reference must be positive.",
        )

    try:
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            gross_pnl = value.gross_pnl
            if gross_pnl is None:
                gross_return = value.gross_return
                if gross_return is None:
                    raise EconomicCostCalculationError(
                        "c3_gross_performance_basis_missing",
                        "performance",
                        "gross_pnl or gross_return is required.",
                    )
                gross_pnl = gross_return * performance_notional

            participation_proxy = traded_notional / static_reference_notional
            if not participation_proxy.is_finite() or participation_proxy < 0:
                raise EconomicCostCalculationError(
                    "c3_nonfinite_numeric_invalid",
                    "participation_proxy",
                    "participation proxy must be finite and non-negative.",
                )
            impact_rate = impact_coefficient * participation_proxy.sqrt(context)
            fee = traded_notional * fee_rate + fee_fixed_amount
            tax = sell_notional * tax_rate + tax_fixed_amount
            spread = traded_notional * effective_spread_rate
            slippage = traded_notional * effective_slippage_rate
            impact = traded_notional * impact_rate
            raw_total_cost = fee + tax + spread + slippage + impact
            total_cost = raw_total_cost.quantize(minor_unit, rounding=ROUND_HALF_EVEN)
            net_pnl = (gross_pnl - total_cost).quantize(minor_unit, rounding=ROUND_HALF_EVEN)
            net_return = net_pnl / performance_notional
            reconciliation_drift = abs((gross_pnl - total_cost) - net_pnl)
            if reconciliation_drift > minor_unit:
                raise EconomicCostCalculationError(
                    "c3_gross_cost_net_arithmetic_mismatch",
                    "gross_cost_net",
                    "Gross, cost and net values drift by more than one final quantization unit.",
                )
            return CostBreakdownV1(
                fee=fee,
                tax=tax,
                spread=spread,
                slippage=slippage,
                impact=impact,
                participation_proxy=participation_proxy,
                impact_rate=impact_rate,
                raw_total_cost=raw_total_cost,
                total_cost=total_cost,
                gross_pnl=gross_pnl,
                net_pnl=net_pnl,
                net_return=net_return,
                currency_minor_unit=minor_unit,
            )
    except EconomicCostCalculationError:
        raise
    except (InvalidOperation, ValueError) as exc:
        raise EconomicCostCalculationError(
            "c3_nonfinite_numeric_invalid",
            "calculation",
            f"Static Decimal calculation failed: {exc}",
        ) from exc


def _require_finite_values(values: dict[str, Decimal | None]) -> None:
    missing = sorted(name for name, item in values.items() if item is None)
    if missing:
        raise EconomicCostCalculationError(
            "c3_cost_model_version_missing",
            ",".join(missing),
            "Calculator accepts only validation-clean input with all static assumptions present.",
        )
    invalid = sorted(name for name, item in values.items() if item is not None and not item.is_finite())
    if invalid:
        raise EconomicCostCalculationError(
            "c3_nonfinite_numeric_invalid",
            ",".join(invalid),
            "Calculator accepts only finite Decimal values.",
        )


def _require_optional_finite_values(values: dict[str, Decimal | None]) -> None:
    invalid = sorted(name for name, item in values.items() if item is not None and not item.is_finite())
    if invalid:
        raise EconomicCostCalculationError(
            "c3_nonfinite_numeric_invalid",
            ",".join(invalid),
            "Provided gross performance values must be finite Decimal values.",
        )


def _required_decimal(values: dict[str, Decimal | None], name: str) -> Decimal:
    value = values[name]
    if value is None:
        raise AssertionError(f"missing value after _require_finite_values: {name}")
    return value


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


__all__ = [
    "DECIMAL_PRECISION",
    "CostBreakdownV1",
    "EconomicCostCalculationError",
    "calculate_cost_breakdown",
]
