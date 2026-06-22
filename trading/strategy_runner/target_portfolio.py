"""CR091 strategy runner 的离线目标组合合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


TARGET_PORTFOLIO_SCHEMA_VERSION = "cr091-target-portfolio-snapshot-v1"


class TargetPortfolioValidationError(ValueError):
    """目标组合合同不满足 CR091 fail-closed 约束。"""


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
