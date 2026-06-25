"""StrategyAdmissionPackage 到 runner P1 的非交易窗口输入契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from trading.strategy_runner.adapters import MULTIFACTOR_SCHEMA, zero_cr091_operation_counters
from trading.strategy_runner.target_portfolio import MultifactorSignalRow


RUNNER_ADMISSION_CONTRACT_SCHEMA_VERSION = "runner-strategy-admission-contract-v1"
SAFE_ADMISSION_STATUSES = frozenset({"research_baseline", "watch", "pass"})
AUTHORIZATION_FALSE_FLAGS: tuple[str, ...] = (
    "not_authorization",
    "not_qmt_authorization",
    "not_simulation_authorization",
    "not_live_authorization",
    "not_broker_order",
)


@dataclass(frozen=True, slots=True)
class RunnerAdmissionContractResult:
    """准入包到 runner 输入的结构化检查结果。"""

    status: str
    strategy_id: str = ""
    source_run_id: str = ""
    target_trade_date: str = ""
    signal_rows: tuple[MultifactorSignalRow, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    schema_version: str = RUNNER_ADMISSION_CONTRACT_SCHEMA_VERSION
    not_authorization: bool = True
    safety_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.passed,
            "blocked": self.blocked,
            "strategy_id": self.strategy_id,
            "source_run_id": self.source_run_id,
            "target_trade_date": self.target_trade_date,
            "signal_count": len(self.signal_rows),
            "signal_instrument_refs": [row.instrument_ref for row in self.signal_rows],
            "blocked_reasons": list(self.blocked_reasons),
            "not_authorization": self.not_authorization,
            "safety_counters": dict(self.safety_counters),
        }


def validate_strategy_admission_for_runner(
    payload: Mapping[str, object],
) -> RunnerAdmissionContractResult:
    """检查 StrategyAdmissionPackage 是否可作为 runner P1 输入。"""

    reasons: list[str] = []
    if payload.get("schema_version") != MULTIFACTOR_SCHEMA:
        reasons.append("schema_version_mismatch")
    for flag in AUTHORIZATION_FALSE_FLAGS:
        if payload.get(flag) is not True:
            reasons.append("authorization_flag_missing:" + flag)
    if str(payload.get("run_id") or "") == "":
        reasons.append("run_id_missing")
    if str(payload.get("target_trade_date") or "") == "":
        reasons.append("target_trade_date_missing")
    if not _operation_counts_zero(payload.get("operation_counts")):
        reasons.append("forbidden_operation_nonzero")
    if not isinstance(payload.get("risk_cost_refs"), Mapping) or not payload.get("risk_cost_refs"):
        reasons.append("risk_cost_refs_missing")

    candidate = _first_admitted_candidate(payload)
    if candidate is None:
        reasons.append("admitted_candidate_missing")
    strategy_id = str(candidate.get("strategy_id") or "") if candidate is not None else ""
    if candidate is not None and not _candidate_symbols(candidate):
        reasons.append("candidate_targets_missing")
    rows = _signal_rows(payload, candidate) if candidate is not None else ()
    if candidate is not None and not rows:
        reasons.append("strategy_scores_missing")
    if reasons:
        return RunnerAdmissionContractResult(
            status="blocked",
            strategy_id=strategy_id,
            source_run_id=str(payload.get("run_id") or ""),
            target_trade_date=str(payload.get("target_trade_date") or ""),
            blocked_reasons=tuple(reasons),
        )
    return RunnerAdmissionContractResult(
        status="pass",
        strategy_id=strategy_id,
        source_run_id=str(payload.get("run_id") or ""),
        target_trade_date=str(payload.get("target_trade_date") or ""),
        signal_rows=rows,
    )


def operator_signal_rows_from_admission(
    payload: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """把通过检查的准入包转换为 operator spec 的 signal_rows。"""

    result = validate_strategy_admission_for_runner(payload)
    if not result.passed:
        raise ValueError("blocked_strategy_admission_contract:" + ",".join(result.blocked_reasons))
    return tuple(
        {
            "symbol": row.symbol,
            "score": str(row.score),
            "signal_date": row.signal_date,
            "factor_refs": dict(row.factor_refs),
            "eligible": row.eligible,
        }
        for row in result.signal_rows
    )


def _first_admitted_candidate(payload: Mapping[str, object]) -> Mapping[str, object] | None:
    for item in _sequence(payload.get("strategy_candidates")):
        if not isinstance(item, Mapping):
            continue
        if str(item.get("admission") or "").lower() in SAFE_ADMISSION_STATUSES:
            return item
    return None


def _signal_rows(
    payload: Mapping[str, object],
    candidate: Mapping[str, object] | None,
) -> tuple[MultifactorSignalRow, ...]:
    if candidate is None:
        return ()
    strategy_id = str(candidate.get("strategy_id") or "")
    target_symbols = set(_candidate_symbols(candidate))
    rows: list[MultifactorSignalRow] = []
    for item in _sequence(payload.get("strategy_scores")):
        if not isinstance(item, Mapping):
            continue
        if str(item.get("strategy_id") or "") != strategy_id:
            continue
        symbol = str(item.get("symbol") or "")
        if symbol not in target_symbols:
            continue
        score = item.get("alpha_score", item.get("score", item.get("composite_score", "")))
        rows.append(
            MultifactorSignalRow(
                symbol=symbol,
                score=score,
                signal_date=str(payload.get("signal_date") or payload.get("target_trade_date") or ""),
                factor_refs={"strategy_admission_package": str(payload.get("run_id") or "")},
                eligible=True,
            )
        )
    return tuple(rows)


def _candidate_symbols(candidate: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(str(item) for item in _sequence(candidate.get("target_symbols")) if str(item))


def _operation_counts_zero(value: object) -> bool:
    expected = zero_cr091_operation_counters()
    if not isinstance(value, Mapping):
        return False
    return all(int(value.get(key, 0)) == 0 for key in expected)


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()
