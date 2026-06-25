"""CR091 strategy runner 的离线目标组合合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import hashlib
import math
from typing import Any, Mapping


TARGET_PORTFOLIO_SCHEMA_VERSION = "cr091-target-portfolio-snapshot-v1"
MULTIFACTOR_TARGET_PORTFOLIO_SCHEMA_VERSION = "runner-multifactor-target-portfolio-v1"


class TargetPortfolioValidationError(ValueError):
    """目标组合合同不满足 CR091 fail-closed 约束。"""


@dataclass(frozen=True, slots=True)
class MultifactorSignalRow:
    """多因子排序输入；只在内存中保留原始 symbol。"""

    symbol: str
    score: Decimal | int | float | str
    signal_date: str
    factor_refs: Mapping[str, Any] = field(default_factory=dict)
    eligible: bool = True

    def score_decimal(self) -> Decimal:
        value = _decimal_value(self.score)
        if value is None or not math.isfinite(float(value)):
            raise TargetPortfolioValidationError("signal score 必须是有限数值")
        return value

    @property
    def instrument_ref(self) -> str:
        return _stable_ref(self.symbol, "instrument")


@dataclass(frozen=True, slots=True)
class MultifactorTargetPortfolioResult:
    """P1 多因子目标组合生成结果；不代表交易授权。"""

    status: str
    snapshot: TargetPortfolioSnapshot | None = None
    blocked_reason: str = ""
    selected_count: int = 0
    rejected_count: int = 0
    schema_version: str = MULTIFACTOR_TARGET_PORTFOLIO_SCHEMA_VERSION
    safety_counters: Mapping[str, int] = field(default_factory=lambda: _zero_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "generated"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "selected_count": self.selected_count,
            "rejected_count": self.rejected_count,
            "target_portfolio": self.snapshot.to_redacted_dict() if self.snapshot is not None else None,
            "safety_counters": dict(self.safety_counters),
        }


@dataclass(frozen=True, slots=True)
class TargetPortfolioSnapshot:
    """broker-neutral 的目标组合快照，不代表交易授权。"""

    strategy_id: str
    source_run_id: str
    target_trade_date: str
    target_symbols: tuple[str, ...]
    target_weights: Mapping[str, float]
    score_refs: Mapping[str, Any] = field(default_factory=dict)
    risk_cost_refs: Mapping[str, Any] = field(default_factory=dict)
    lineage_refs: Mapping[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    schema_version: str = TARGET_PORTFOLIO_SCHEMA_VERSION
    not_authorization: bool = True

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise TargetPortfolioValidationError("strategy_id 不能为空")
        if not self.source_run_id:
            raise TargetPortfolioValidationError("source_run_id 不能为空")
        if not self.target_trade_date:
            raise TargetPortfolioValidationError("target_trade_date 不能为空")
        if not self.target_symbols:
            raise TargetPortfolioValidationError("target_symbols 不能为空")
        missing_weights = set(self.target_symbols) - set(self.target_weights)
        if missing_weights:
            raise TargetPortfolioValidationError(
                "target_weights 缺少标的: " + ",".join(sorted(missing_weights))
            )
        if abs(sum(float(self.target_weights[symbol]) for symbol in self.target_symbols) - 1.0) > 1e-6:
            raise TargetPortfolioValidationError("target_weights 必须合计为 1.0")
        if self.not_authorization is not True:
            raise TargetPortfolioValidationError("TargetPortfolioSnapshot 必须声明 not_authorization=true")

    @property
    def target_portfolio_id(self) -> str:
        return f"cr091-target:{self.strategy_id}:{self.source_run_id}"

    def rows(self) -> list[dict[str, Any]]:
        return [
            {
                "target_portfolio_id": self.target_portfolio_id,
                "strategy_id": self.strategy_id,
                "source_run_id": self.source_run_id,
                "run_id": self.source_run_id,
                "target_trade_date": self.target_trade_date,
                "signal_date": self.target_trade_date,
                "symbol": symbol,
                "side": "buy",
                "target_weight": float(self.target_weights[symbol]),
                "data_lineage_ref": dict(self.lineage_refs),
                "limitations": list(self.limitations),
                "execution_price_policy": "raw",
                "raw_execution_policy_status": "pass",
                "qmt_allowed": False,
                "not_authorization": True,
                "reason": "cr091-offline-target-portfolio",
            }
            for symbol in self.target_symbols
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "source_run_id": self.source_run_id,
            "target_trade_date": self.target_trade_date,
            "target_portfolio_id": self.target_portfolio_id,
            "target_symbols": list(self.target_symbols),
            "target_weights": {symbol: float(self.target_weights[symbol]) for symbol in self.target_symbols},
            "score_refs": dict(self.score_refs),
            "risk_cost_refs": dict(self.risk_cost_refs),
            "lineage_refs": dict(self.lineage_refs),
            "limitations": list(self.limitations),
            "not_authorization": self.not_authorization,
        }

    def redacted_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "target_portfolio_id": self.target_portfolio_id,
                "strategy_id": self.strategy_id,
                "source_run_id": self.source_run_id,
                "run_id": self.source_run_id,
                "target_trade_date": self.target_trade_date,
                "signal_date": self.target_trade_date,
                "instrument_ref": _stable_ref(symbol, "instrument"),
                "side": "buy",
                "target_weight": float(self.target_weights[symbol]),
                "data_lineage_ref": dict(self.lineage_refs),
                "limitations": list(self.limitations),
                "execution_price_policy": "raw",
                "raw_execution_policy_status": "pass",
                "qmt_allowed": False,
                "not_authorization": True,
                "reason": "runner-multifactor-offline-target-portfolio",
            }
            for symbol in self.target_symbols
        ]

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "source_run_id": self.source_run_id,
            "target_trade_date": self.target_trade_date,
            "target_portfolio_id": self.target_portfolio_id,
            "target_instruments": [
                _stable_ref(symbol, "instrument") for symbol in self.target_symbols
            ],
            "target_weights": {
                _stable_ref(symbol, "instrument"): float(self.target_weights[symbol])
                for symbol in self.target_symbols
            },
            "score_refs": dict(self.score_refs),
            "risk_cost_refs": dict(self.risk_cost_refs),
            "lineage_refs": dict(self.lineage_refs),
            "limitations": list(self.limitations),
            "rows": self.redacted_rows(),
            "not_authorization": self.not_authorization,
        }


def equal_weight_snapshot(
    *,
    strategy_id: str,
    source_run_id: str,
    target_trade_date: str,
    target_symbols: tuple[str, ...],
    score_refs: Mapping[str, Any] | None = None,
    risk_cost_refs: Mapping[str, Any] | None = None,
    lineage_refs: Mapping[str, Any] | None = None,
    limitations: tuple[str, ...] = (),
) -> TargetPortfolioSnapshot:
    """为 legacy 策略构造等权目标组合。"""

    if not target_symbols:
        raise TargetPortfolioValidationError("target_symbols 不能为空")
    weight = 1.0 / len(target_symbols)
    return TargetPortfolioSnapshot(
        strategy_id=strategy_id,
        source_run_id=source_run_id,
        target_trade_date=target_trade_date,
        target_symbols=target_symbols,
        target_weights={symbol: weight for symbol in target_symbols},
        score_refs=score_refs or {},
        risk_cost_refs=risk_cost_refs or {},
        lineage_refs=lineage_refs or {},
        limitations=limitations,
    )


def build_multifactor_target_portfolio(
    *,
    strategy_id: str,
    source_run_id: str,
    target_trade_date: str,
    signal_rows: tuple[MultifactorSignalRow | Mapping[str, Any], ...],
    top_n: int,
    weighting: str = "equal",
    max_weight: Decimal | int | float | str | None = None,
    universe_symbols: tuple[str, ...] = (),
    score_refs: Mapping[str, Any] | None = None,
    risk_cost_refs: Mapping[str, Any] | None = None,
    lineage_refs: Mapping[str, Any] | None = None,
    limitations: tuple[str, ...] = (),
) -> MultifactorTargetPortfolioResult:
    """只生成多因子目标组合，不授权下单、不触达 QMT runtime。"""

    if not strategy_id or not source_run_id or not target_trade_date:
        return _blocked_result("required_field_missing")
    if top_n <= 0:
        return _blocked_result("top_n_invalid")
    if not signal_rows:
        return _blocked_result("signal_rows_empty")
    if weighting not in {"equal", "score"}:
        return _blocked_result("unsupported_weighting")
    universe = set(universe_symbols)
    normalized: list[MultifactorSignalRow] = []
    rejected_count = 0
    seen_symbols: set[str] = set()
    try:
        for raw in signal_rows:
            row = _signal_row(raw)
            if not row.symbol or not row.signal_date:
                rejected_count += 1
                continue
            if row.symbol in seen_symbols:
                rejected_count += 1
                continue
            if universe and row.symbol not in universe:
                rejected_count += 1
                continue
            if not row.eligible:
                rejected_count += 1
                continue
            row.score_decimal()
            seen_symbols.add(row.symbol)
            normalized.append(row)
    except (InvalidOperation, TargetPortfolioValidationError, ValueError):
        return _blocked_result("invalid_signal_row")
    if not normalized:
        return _blocked_result("no_eligible_signal")
    selected = tuple(
        sorted(normalized, key=lambda item: item.score_decimal(), reverse=True)[:top_n]
    )
    try:
        weights = _target_weights(selected, weighting=weighting, max_weight=max_weight)
    except TargetPortfolioValidationError as exc:
        return _blocked_result(str(exc) or "target_weighting_failed")
    try:
        snapshot = TargetPortfolioSnapshot(
            strategy_id=strategy_id,
            source_run_id=source_run_id,
            target_trade_date=target_trade_date,
            target_symbols=tuple(row.symbol for row in selected),
            target_weights=weights,
            score_refs=score_refs or {},
            risk_cost_refs=risk_cost_refs or {},
            lineage_refs=lineage_refs or {},
            limitations=limitations + ("not_order_authorization", "qmt_runtime_not_touched"),
            schema_version=MULTIFACTOR_TARGET_PORTFOLIO_SCHEMA_VERSION,
            not_authorization=True,
        )
    except TargetPortfolioValidationError as exc:
        return _blocked_result(str(exc) or "target_portfolio_validation_failed")
    return MultifactorTargetPortfolioResult(
        status="generated",
        snapshot=snapshot,
        selected_count=len(selected),
        rejected_count=rejected_count + max(len(normalized) - len(selected), 0),
    )


def _signal_row(raw: MultifactorSignalRow | Mapping[str, Any]) -> MultifactorSignalRow:
    if isinstance(raw, MultifactorSignalRow):
        return raw
    return MultifactorSignalRow(
        symbol=str(raw.get("symbol") or ""),
        score=raw.get("score", raw.get("composite_score", "")),
        signal_date=str(raw.get("signal_date") or ""),
        factor_refs=dict(raw.get("factor_refs") or {}),
        eligible=bool(raw.get("eligible", True)),
    )


def _target_weights(
    selected: tuple[MultifactorSignalRow, ...],
    *,
    weighting: str,
    max_weight: Decimal | int | float | str | None,
) -> dict[str, float]:
    if not selected:
        raise TargetPortfolioValidationError("selected signals 不能为空")
    cap = _decimal_value(max_weight) if max_weight is not None else None
    if cap is not None and (cap <= 0 or cap > 1):
        raise TargetPortfolioValidationError("max_weight 必须在 (0, 1] 范围内")
    if cap is not None and cap * len(selected) < Decimal("1"):
        raise TargetPortfolioValidationError("max_weight 无法覆盖 100% 权重")
    if weighting == "equal":
        weights = {row.symbol: Decimal("1") / Decimal(len(selected)) for row in selected}
    else:
        positive_scores = {row.symbol: max(row.score_decimal(), Decimal("0")) for row in selected}
        total = sum(positive_scores.values(), Decimal("0"))
        if total <= 0:
            raise TargetPortfolioValidationError("score weighting 需要正分数")
        weights = {symbol: score / total for symbol, score in positive_scores.items()}
    if cap is not None:
        weights = _apply_weight_cap(weights, cap)
    return _normalize_weights(weights)


def _apply_weight_cap(weights: Mapping[str, Decimal], cap: Decimal) -> dict[str, Decimal]:
    capped = {symbol: min(weight, cap) for symbol, weight in weights.items()}
    remaining = Decimal("1") - sum(capped.values(), Decimal("0"))
    if remaining < Decimal("-0.0000001"):
        raise TargetPortfolioValidationError("max_weight 应用后权重超限")
    while remaining > Decimal("0.0000001"):
        candidates = {
            symbol: weights[symbol]
            for symbol, current in capped.items()
            if current < cap
        }
        if not candidates:
            raise TargetPortfolioValidationError("max_weight 应用后无法归一化")
        total_base = sum(candidates.values(), Decimal("0"))
        if total_base <= 0:
            increment = remaining / Decimal(len(candidates))
            for symbol in candidates:
                capped[symbol] = min(cap, capped[symbol] + increment)
        else:
            for symbol, base in candidates.items():
                capped[symbol] = min(cap, capped[symbol] + remaining * (base / total_base))
        next_remaining = Decimal("1") - sum(capped.values(), Decimal("0"))
        if next_remaining >= remaining:
            raise TargetPortfolioValidationError("max_weight 应用后无法收敛")
        remaining = next_remaining
    return capped


def _normalize_weights(weights: Mapping[str, Decimal]) -> dict[str, float]:
    total = sum(weights.values(), Decimal("0"))
    if total <= 0:
        raise TargetPortfolioValidationError("target_weights 合计必须大于 0")
    normalized = {symbol: weight / total for symbol, weight in weights.items()}
    rounded = {
        symbol: value.quantize(Decimal("0.0000000001"), rounding=ROUND_DOWN)
        for symbol, value in normalized.items()
    }
    delta = Decimal("1") - sum(rounded.values(), Decimal("0"))
    first_symbol = next(iter(rounded))
    rounded[first_symbol] = rounded[first_symbol] + delta
    return {symbol: float(value) for symbol, value in rounded.items()}


def _blocked_result(reason: str) -> MultifactorTargetPortfolioResult:
    return MultifactorTargetPortfolioResult(status="blocked", blocked_reason=reason)


def _decimal_value(value: Decimal | int | float | str | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


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
