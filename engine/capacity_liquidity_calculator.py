"""CR-169 S02 的纯 Decimal static capacity/liquidity calculator。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import TYPE_CHECKING, Any

from engine.strategy_evidence import canonical_json_value

if TYPE_CHECKING:
    from engine.capacity_liquidity_evidence import NormalizedCapacityLiquidityInputV1


DECIMAL_PRECISION = 28


class CapacityLiquidityCalculationError(ValueError):
    """将防御性 numeric guard 映射到既有 C4 reason code。"""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


@dataclass(frozen=True, slots=True)
class CapacityLiquidityBreakdownV1:
    participation_ratio: Decimal
    raw_capacity_amount: Decimal
    capacity_amount: Decimal
    liquidity_headroom: Decimal
    within_declared_cap: bool
    synthetic_adv: Decimal
    requested_notional: Decimal
    turnover_notional: Decimal
    participation_cap: Decimal
    currency_minor_unit: Decimal

    def to_dict(self) -> dict[str, Any]:
        values = asdict(self)
        return canonical_json_value(
            {
                key: value if isinstance(value, bool) else _decimal_text(value)
                for key, value in values.items()
            }
        )


def calculate_capacity_liquidity_breakdown(
    value: "NormalizedCapacityLiquidityInputV1",
) -> CapacityLiquidityBreakdownV1:
    """执行 frozen `static_adv_cap_v1` 公式，不读取或估计任何外部数据。"""

    required = {
        "synthetic_adv": value.synthetic_adv,
        "requested_notional": value.requested_notional,
        "turnover_notional": value.turnover_notional,
        "participation_cap": value.participation_cap,
        "currency_minor_unit": value.currency_minor_unit,
    }
    missing = sorted(name for name, item in required.items() if item is None)
    if missing:
        raise CapacityLiquidityCalculationError(
            "c4_static_liquidity_basis_missing",
            ",".join(missing),
            "Calculator accepts only validation-clean static inputs.",
        )
    invalid = sorted(name for name, item in required.items() if item is not None and not item.is_finite())
    if invalid:
        raise CapacityLiquidityCalculationError(
            "c4_nonfinite_numeric_invalid",
            ",".join(invalid),
            "Calculator accepts only finite Decimal values.",
        )

    synthetic_adv = _required(required, "synthetic_adv")
    requested_notional = _required(required, "requested_notional")
    turnover_notional = _required(required, "turnover_notional")
    participation_cap = _required(required, "participation_cap")
    minor_unit = _required(required, "currency_minor_unit")
    if (
        synthetic_adv <= 0
        or requested_notional < 0
        or turnover_notional < 0
        or not (Decimal("0") < participation_cap <= Decimal("1"))
        or minor_unit <= 0
    ):
        raise CapacityLiquidityCalculationError(
            "c4_negative_or_participation_cap_invalid",
            "static_liquidity",
            "Synthetic ADV/minor unit must be positive, notionals non-negative and cap in (0, 1].",
        )

    try:
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            participation_ratio = requested_notional / synthetic_adv
            raw_capacity_amount = synthetic_adv * participation_cap
            capacity_amount = raw_capacity_amount.quantize(minor_unit, rounding=ROUND_HALF_EVEN)
            liquidity_headroom = (capacity_amount - requested_notional).quantize(
                minor_unit,
                rounding=ROUND_HALF_EVEN,
            )
            if not all(
                item.is_finite()
                for item in (
                    participation_ratio,
                    raw_capacity_amount,
                    capacity_amount,
                    liquidity_headroom,
                )
            ):
                raise CapacityLiquidityCalculationError(
                    "c4_nonfinite_numeric_invalid",
                    "calculation",
                    "Calculated static proxy values must be finite.",
                )
            return CapacityLiquidityBreakdownV1(
                participation_ratio=participation_ratio,
                raw_capacity_amount=raw_capacity_amount,
                capacity_amount=capacity_amount,
                liquidity_headroom=liquidity_headroom,
                within_declared_cap=participation_ratio <= participation_cap,
                synthetic_adv=synthetic_adv,
                requested_notional=requested_notional,
                turnover_notional=turnover_notional,
                participation_cap=participation_cap,
                currency_minor_unit=minor_unit,
            )
    except CapacityLiquidityCalculationError:
        raise
    except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
        raise CapacityLiquidityCalculationError(
            "c4_nonfinite_numeric_invalid",
            "calculation",
            f"Static Decimal calculation failed: {exc}",
        ) from exc


def _required(values: dict[str, Decimal | None], name: str) -> Decimal:
    value = values[name]
    if value is None:
        raise AssertionError(f"missing value after validation: {name}")
    return value


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


__all__ = [
    "DECIMAL_PRECISION",
    "CapacityLiquidityBreakdownV1",
    "CapacityLiquidityCalculationError",
    "calculate_capacity_liquidity_breakdown",
]
