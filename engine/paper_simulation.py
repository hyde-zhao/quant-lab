"""CR041 本地离线 paper simulation 核心合同。

本模块只处理本地 JSON / 内存对象，不连接 broker，不读取凭据，不拉取
provider，也不写入 market-data lake 或 catalog。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


ADMISSION_SCHEMA_VERSION = "multifactor_strategy_admission_package_v1"
ORDER_INTENT_SCHEMA_VERSION = "paper_order_intent_v1"
FILL_SCHEMA_VERSION = "paper_fill_v1"
LEDGER_SCHEMA_VERSION = "paper_ledger_v1"
RUN_RESULT_SCHEMA_VERSION = "paper_simulation_run_result_v1"
RAW_OPEN_EXECUTION_POLICY = "raw_open"

FORBIDDEN_OPERATION_COUNTERS = (
    "account_or_order_operation",
    "broker_connection",
    "broker_lake_write",
    "catalog_publish",
    "credential_read",
    "dependency_change",
    "external_quote_subscription",
    "lake_write",
    "miniqmt_operation",
    "order_cancel",
    "order_submit",
    "provider_fetch",
    "qmt_operation",
    "real_broker_operation",
    "reports_overwrite",
    "simulation_or_live",
    "simulation_or_live_authorization",
    "account_query",
    "xtquant_import_or_call",
)

SENSITIVE_FIELD_PATTERNS = (
    "token",
    "secret",
    "password",
    "passwd",
    "cookie",
    "session",
    "private_key",
    "account_id",
    "broker_account",
    "real_account",
    "trade_password",
    "credential",
)

OPEN_TRADE_STATUSES = {"open", "trading", "trade", "normal"}


class PaperSimulationError(Exception):
    """paper simulation 基础异常。"""


class PaperSimulationValidationError(PaperSimulationError):
    """输入或合同校验失败。"""


def zero_forbidden_operation_counts() -> dict[str, int]:
    return {name: 0 for name in FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class PaperSimulationViolation:
    code: str
    message: str
    severity: str = "blocker"
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PaperSimulationValidation:
    passed: bool
    violations: tuple[PaperSimulationViolation, ...] = ()
    forbidden_operation_counts: Mapping[str, int] = field(
        default_factory=zero_forbidden_operation_counts
    )

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        return tuple(
            f"{violation.code}:{violation.field}" if violation.field else violation.code
            for violation in self.violations
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.passed else "blocked",
            "passed": self.passed,
            "violations": [violation.to_dict() for violation in self.violations],
            "blocked_reasons": list(self.blocked_reasons),
            "forbidden_operation_counts": dict(self.forbidden_operation_counts),
            "operation_counts": dict(self.forbidden_operation_counts),
        }


@dataclass(frozen=True, slots=True)
class PaperSimulationAdmissionView:
    strategy_id: str
    run_id: str
    source_run_id: str
    source_portfolio_id: str
    source_path: str
    package_hash: str
    schema_version: str
    package_schema_version: str
    status: str
    overall_admission: str
    simulation_candidate: bool
    not_authorization: bool
    not_simulation_authorization: bool
    not_live_authorization: bool
    not_broker_order: bool
    blocked_claims: tuple[Mapping[str, Any], ...]
    allowed_claims: tuple[Mapping[str, Any], ...]
    input_refs: Mapping[str, Any]
    operation_counts: Mapping[str, int]
    candidate: Mapping[str, Any]
    validation: PaperSimulationValidation

    def to_dict(self) -> dict[str, Any]:
        source_portfolio_id = str(self.candidate.get("source_portfolio_id", ""))
        return {
            "schema_version": "paper_simulation_admission_view_v1",
            "package_schema_version": self.package_schema_version,
            "strategy_id": self.strategy_id,
            "run_id": self.run_id,
            "source_run_id": self.source_run_id,
            "source_portfolio_id": self.source_portfolio_id or source_portfolio_id,
            "source_path": self.source_path,
            "package_hash": self.package_hash,
            "status": self.status,
            "admission_status": "pass" if self.validation.passed else "blocked",
            "overall_admission": self.overall_admission,
            "simulation_candidate": self.simulation_candidate,
            "not_authorization": self.not_authorization,
            "not_simulation_authorization": self.not_simulation_authorization,
            "not_live_authorization": self.not_live_authorization,
            "not_broker_order": self.not_broker_order,
            "blocked_claims": _json_safe(list(self.blocked_claims)),
            "allowed_claims": _json_safe(list(self.allowed_claims)),
            "input_refs": _json_safe(dict(self.input_refs)),
            "operation_counts": dict(self.operation_counts),
            "candidate": _json_safe(dict(self.candidate)),
            "validation": self.validation.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PaperOrderIntent:
    schema_version: str
    strategy_id: str
    signal_date: str
    target_trade_date: str
    symbol: str
    side: str
    target_qty: int
    execution_price_policy: str = RAW_OPEN_EXECUTION_POLICY
    not_authorization: bool = True
    reason: str = ""
    target_weight: float | None = None
    source_row_id: str = ""
    blocked_reasons: tuple[str, ...] = ()
    operation_counters: Mapping[str, int] = field(default_factory=zero_forbidden_operation_counts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "signal_date": self.signal_date,
            "target_trade_date": self.target_trade_date,
            "symbol": self.symbol,
            "side": self.side,
            "target_qty": self.target_qty,
            "execution_price_policy": self.execution_price_policy,
            "valuation_price_policy": "raw_close",
            "not_authorization": self.not_authorization,
            "reason": self.reason,
            "target_weight": self.target_weight,
            "source_row_id": self.source_row_id,
            "blocked_reasons": list(self.blocked_reasons),
            "operation_counters": dict(self.operation_counters),
            "operation_counts": dict(self.operation_counters),
        }


@dataclass(frozen=True, slots=True)
class PaperOrderIntentBuildResult:
    status: str
    intents: tuple[PaperOrderIntent, ...] = ()
    blocked_reasons: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "blocked_reasons": list(self.blocked_reasons),
            "intents": [intent.to_dict() for intent in self.intents],
        }


@dataclass(frozen=True, slots=True, init=False)
class PaperBrokerConfig:
    commission_bps: float = 3.0
    min_commission: float = 5.0
    stamp_tax_bps: float = 10.0
    transfer_fee_bps: float = 0.1
    slippage_bps: float = 5.0
    max_participation_rate: float = 0.10

    def __init__(
        self,
        commission_bps: float | None = None,
        min_commission: float = 5.0,
        stamp_tax_bps: float | None = None,
        transfer_fee_bps: float | None = None,
        slippage_bps: float | None = None,
        max_participation_rate: float = 0.10,
        fixed_slippage_bps: float | None = None,
        commission_rate: float | None = None,
        stamp_duty_rate: float | None = None,
        transfer_fee_rate: float | None = None,
    ) -> None:
        if commission_bps is None:
            commission_bps = 3.0 if commission_rate is None else float(commission_rate) * 10_000
        if stamp_tax_bps is None:
            stamp_tax_bps = 10.0 if stamp_duty_rate is None else float(stamp_duty_rate) * 10_000
        if transfer_fee_bps is None:
            transfer_fee_bps = 0.1 if transfer_fee_rate is None else float(transfer_fee_rate) * 10_000
        if slippage_bps is None:
            slippage_bps = 5.0 if fixed_slippage_bps is None else float(fixed_slippage_bps)
        object.__setattr__(self, "commission_bps", float(commission_bps))
        object.__setattr__(self, "min_commission", float(min_commission))
        object.__setattr__(self, "stamp_tax_bps", float(stamp_tax_bps))
        object.__setattr__(self, "transfer_fee_bps", float(transfer_fee_bps))
        object.__setattr__(self, "slippage_bps", float(slippage_bps))
        object.__setattr__(self, "max_participation_rate", float(max_participation_rate))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PaperFill:
    schema_version: str
    trade_date: str
    symbol: str
    side: str
    requested_qty: int
    filled_qty: int
    status: str
    exec_price: float | None
    costs: Mapping[str, float]
    reason: str = ""
    not_authorization: bool = True
    operation_counters: Mapping[str, int] = field(default_factory=zero_forbidden_operation_counts)

    @property
    def gross_amount(self) -> float:
        if self.exec_price is None:
            return 0.0
        return round(self.filled_qty * self.exec_price, 6)

    @property
    def total_cost(self) -> float:
        if "total" in self.costs:
            return round(float(self.costs["total"]), 6)
        return round(sum(float(value) for value in self.costs.values()), 6)

    def to_dict(self) -> dict[str, Any]:
        unfilled_qty = max(0, self.requested_qty - self.filled_qty)
        return {
            "schema_version": self.schema_version,
            "trade_date": self.trade_date,
            "symbol": self.symbol,
            "side": self.side,
            "requested_qty": self.requested_qty,
            "filled_qty": self.filled_qty,
            "unfilled_qty": unfilled_qty,
            "status": self.status,
            "exec_price": self.exec_price,
            "gross_amount": self.gross_amount,
            "costs": dict(self.costs),
            "total_cost": self.total_cost,
            "reason": self.reason,
            "reason_code": self.reason,
            "not_authorization": self.not_authorization,
            "operation_counters": dict(self.operation_counters),
            "operation_counts": dict(self.operation_counters),
        }


@dataclass(frozen=True, slots=True)
class PaperPosition:
    symbol: str
    quantity: int = 0
    sellable_qty: int = 0
    average_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PaperAccountState:
    cash: float
    positions: Mapping[str, PaperPosition | Mapping[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cash": round(float(self.cash), 6),
            "positions": {
                symbol: _position_from_any(position).to_dict()
                for symbol, position in self.positions.items()
            },
        }


@dataclass(frozen=True, slots=True)
class PaperLedgerResult:
    schema_version: str
    final_state: PaperAccountState
    fills: tuple[PaperFill, ...]
    positions: tuple[Mapping[str, Any], ...]
    position_ledger: tuple[Mapping[str, Any], ...]
    cash_ledger: tuple[Mapping[str, Any], ...]
    equity_curve: tuple[Mapping[str, Any], ...]
    reconciliation: Mapping[str, Any]
    cost_totals: Mapping[str, float]
    turnover: float
    max_drawdown: float
    status: str = "pass"
    blocked_reasons: tuple[str, ...] = ()
    not_authorization: bool = True
    operation_counters: Mapping[str, int] = field(default_factory=zero_forbidden_operation_counts)

    def to_dict(self) -> dict[str, Any]:
        ending_cash = self.final_state.cash
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "passed": self.status == "pass",
            "blocked_reasons": list(self.blocked_reasons),
            "final_state": self.final_state.to_dict(),
            "cash": {"ending_cash": round(ending_cash, 6)},
            "fills": [fill.to_dict() for fill in self.fills],
            "positions": _json_safe(list(self.positions)),
            "position_ledger": _json_safe(list(self.position_ledger)),
            "cash_ledger": _json_safe(list(self.cash_ledger)),
            "equity_curve": _json_safe(list(self.equity_curve)),
            "reconciliation": _json_safe(dict(self.reconciliation)),
            "cost_totals": dict(self.cost_totals),
            "turnover": self.turnover,
            "max_drawdown": self.max_drawdown,
            "not_authorization": self.not_authorization,
            "operation_counters": dict(self.operation_counters),
        }


@dataclass(frozen=True, slots=True)
class PaperSimulationRunResult:
    schema_version: str
    run_id: str
    admission_view: PaperSimulationAdmissionView
    order_intents: tuple[PaperOrderIntent, ...]
    fills: tuple[PaperFill, ...]
    ledger: PaperLedgerResult
    artifact_paths: Mapping[str, str] = field(default_factory=dict)
    status: str = "pass"
    passed: bool = True
    not_authorization: bool = True
    simulation_ready: bool = False
    live_ready: bool = False
    operation_counters: Mapping[str, int] = field(default_factory=zero_forbidden_operation_counts)

    def to_dict(self) -> dict[str, Any]:
        ledger_payload = self.ledger.to_dict()
        return {
            "schema_version": self.schema_version,
            "status": "pass",
            "passed": True,
            "run_id": self.run_id,
            "admission_view": self.admission_view.to_dict(),
            "order_intents": [intent.to_dict() for intent in self.order_intents],
            "fills": [fill.to_dict() for fill in self.fills],
            "positions": ledger_payload["positions"],
            "cash_ledger": ledger_payload["cash_ledger"],
            "equity_curve": ledger_payload["equity_curve"],
            "reconciliation": ledger_payload["reconciliation"],
            "cost_totals": ledger_payload["cost_totals"],
            "artifact_paths": dict(self.artifact_paths),
            "not_authorization": self.not_authorization,
            "simulation_ready": self.simulation_ready,
            "live_ready": self.live_ready,
            "forbidden_operation_counters": dict(self.operation_counters),
            "operation_counts": dict(self.operation_counters),
        }


def load_strategy_admission_package(path: str | Path) -> dict[str, Any]:
    package_path = Path(path)
    with package_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise PaperSimulationValidationError("strategy admission package must be a JSON object")
    payload["_source_path"] = str(package_path)
    payload["_package_hash"] = _sha256_json(payload, exclude_keys={"_source_path", "_package_hash"})
    return payload


def validate_strategy_admission_package(
    payload: Mapping[str, Any], expected_strategy_id: str | None = None
) -> PaperSimulationValidation:
    violations: list[PaperSimulationViolation] = []
    if payload.get("schema_version") != ADMISSION_SCHEMA_VERSION:
        violations.append(_violation("unknown_schema_version", "unsupported admission package schema"))
    if payload.get("status") != "PASS":
        violations.append(_violation("package_not_passed", "admission package status must be PASS", "status"))
    if payload.get("overall_admission") != "research_baseline":
        violations.append(_violation("not_research_baseline", "overall admission must stay research_baseline"))
    for flag in (
        "not_authorization",
        "not_broker_order",
        "not_live_authorization",
        "not_qmt_authorization",
        "not_simulation_authorization",
    ):
        if payload.get(flag) is not True:
            violations.append(_violation("authorization_flag_missing", f"{flag} must be true", flag))
    operation_counts = _normalise_operation_counts(payload.get("operation_counts", {}))
    violations.extend(_forbidden_counter_violations(operation_counts))
    violations.extend(_sensitive_field_violations(payload))
    allowed_claims = payload.get("allowed_claims", [])
    if isinstance(allowed_claims, list):
        for claim in allowed_claims:
            if not isinstance(claim, Mapping):
                continue
            claim_name = str(claim.get("claim", "")).lower()
            if claim.get("status") == "allowed" and any(
                blocked in claim_name
                for blocked in ("simulation_ready", "live_ready", "broker_order_ready", "qmt_ready")
            ):
                violations.append(_violation(f"unsafe_allowed_claim:{claim_name}", claim_name, "allowed_claims"))
    candidates = payload.get("strategy_candidates")
    if not isinstance(candidates, list) or not candidates:
        violations.append(_violation("missing_strategy_candidates", "strategy_candidates must be non-empty"))
    else:
        candidate = _find_strategy_candidate(candidates, expected_strategy_id)
        if candidate is None:
            violations.append(_violation("strategy_candidate_not_found", "expected strategy candidate not found"))
        else:
            if candidate.get("admission") != "research_baseline":
                violations.append(_violation("candidate_not_research_baseline", "candidate admission must be research_baseline"))
            if candidate.get("simulation_candidate") is not False:
                violations.append(_violation("candidate_simulation_candidate", "candidate must not be simulation_candidate"))
    return PaperSimulationValidation(
        passed=not violations,
        violations=tuple(violations),
        forbidden_operation_counts=operation_counts,
    )


def assert_no_forbidden_operations(operation_counts: Mapping[str, Any]) -> None:
    violations = _forbidden_counter_violations(_normalise_operation_counts(operation_counts))
    if violations:
        reason = ", ".join(violation.code for violation in violations)
        raise PaperSimulationValidationError(f"forbidden operations detected: {reason}")


def build_admission_view(
    payload: Mapping[str, Any],
    source_path: str | Path = "",
    expected_strategy_id: str | None = None,
) -> PaperSimulationAdmissionView:
    validation = validate_strategy_admission_package(payload, expected_strategy_id)
    if not validation.passed:
        raise PaperSimulationValidationError("; ".join(validation.blocked_reasons))
    candidates = payload.get("strategy_candidates", [])
    candidate = _find_strategy_candidate(candidates, expected_strategy_id)
    if not isinstance(candidate, Mapping):
        raise PaperSimulationValidationError("strategy candidate not found")
    source_path_value = str(source_path or payload.get("_source_path", ""))
    return PaperSimulationAdmissionView(
        strategy_id=str(candidate.get("strategy_id", expected_strategy_id or "")),
        run_id=str(payload.get("run_id", "")),
        source_run_id=str(payload.get("run_id", "")),
        source_portfolio_id=str(candidate.get("source_portfolio_id", "")),
        source_path=source_path_value,
        package_hash=str(payload.get("_package_hash") or _sha256_json(payload)),
        schema_version="paper_simulation_admission_view_v1",
        package_schema_version=str(payload.get("schema_version", "")),
        status=str(payload.get("status", "")),
        overall_admission=str(payload.get("overall_admission", "")),
        simulation_candidate=bool(candidate.get("simulation_candidate")),
        not_authorization=bool(payload.get("not_authorization")),
        not_simulation_authorization=bool(payload.get("not_simulation_authorization", True)),
        not_live_authorization=bool(payload.get("not_live_authorization", True)),
        not_broker_order=bool(payload.get("not_broker_order", True)),
        blocked_claims=tuple(_mapping_items(payload.get("blocked_claims", []))),
        allowed_claims=tuple(_mapping_items(payload.get("allowed_claims", []))),
        input_refs=_input_refs_from_any(payload.get("input_refs", {})),
        operation_counts=_normalise_operation_counts(payload.get("operation_counts", {})),
        candidate=dict(candidate),
        validation=validation,
    )


def resolve_target_trade_date(signal_date: str, calendar: Sequence[Any]) -> str:
    signal = _to_date(signal_date)
    open_dates = sorted(_calendar_open_dates(calendar))
    for trade_date in open_dates:
        if trade_date > signal:
            return trade_date.isoformat()
    raise PaperSimulationValidationError("missing_target_trade_date")


def apply_lot_and_sellable_rules(
    row: Mapping[str, Any], position: Mapping[str, Any] | PaperPosition | None = None
) -> tuple[int, str]:
    raw_qty = int(float(row.get("target_qty", row.get("quantity", row.get("qty", 0))) or 0))
    side = str(row.get("side", "")).lower()
    if raw_qty <= 0:
        return 0, "zero_or_missing_quantity"
    rounded = _round_down_lot(raw_qty)
    if side == "sell":
        sellable = _position_from_any(position or {}).sellable_qty
        if sellable <= 0:
            return 0, "no_sellable_quantity"
        adjusted = min(rounded, _round_down_lot(sellable))
        if adjusted < rounded:
            return adjusted, "sellable_quantity_capped"
    if rounded != raw_qty:
        return rounded, "lot_rounded"
    return rounded, "ok"


def build_order_intents(
    admission_view: PaperSimulationAdmissionView | Mapping[str, Any],
    target_portfolio: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    calendar: Sequence[Any],
    current_positions: Mapping[str, Any] | None = None,
) -> list[PaperOrderIntent] | PaperOrderIntentBuildResult:
    view = _admission_view_from_any(admission_view)
    if not view.validation.passed:
        raise PaperSimulationValidationError("admission_view_not_passed")
    if not calendar:
        raise PaperSimulationValidationError("missing_calendar")
    portfolio_policy = ""
    if isinstance(target_portfolio, Mapping):
        portfolio_policy = str(target_portfolio.get("estimated_price_policy", "")).lower()
    if portfolio_policy in {"qfq", "hfq"}:
        return PaperOrderIntentBuildResult(status="blocked", blocked_reasons=("non_raw_estimated_price_policy",))
    rows = _target_rows(target_portfolio)
    defaults = target_portfolio if isinstance(target_portfolio, Mapping) else {}
    signal_date = str(defaults.get("signal_date") or rows[0].get("signal_date", "")) if rows else ""
    if not signal_date:
        raise PaperSimulationValidationError("missing_signal_date")
    target_trade_date = str(defaults.get("target_trade_date") or resolve_target_trade_date(signal_date, calendar))
    initial_equity = _optional_float(defaults.get("initial_equity", defaults.get("initial_cash")))
    positions = current_positions or defaults.get("current_positions", {}) or {}
    intents: list[PaperOrderIntent] = []
    hard_block_reasons: list[str] = []
    for index, row in enumerate(rows):
        if _contains_sensitive_key(row):
            hard_block_reasons.append("sensitive_material_present")
            continue
        if str(row.get("execution_price_policy", RAW_OPEN_EXECUTION_POLICY)) not in {
            "",
            RAW_OPEN_EXECUTION_POLICY,
        }:
            hard_block_reasons.append("non_raw_execution_price_policy")
            continue
        symbol = str(row.get("symbol", "")).strip()
        if not symbol:
            hard_block_reasons.append("missing_symbol")
            continue
        current_position = _position_from_any(positions.get(symbol, {})) if isinstance(positions, Mapping) else PaperPosition(symbol)
        side, desired_delta, reason, weight = _desired_delta(row, current_position, initial_equity)
        if side == "rejected":
            hard_block_reasons.append(reason)
            continue
        if desired_delta <= 0:
            intents.append(
                PaperOrderIntent(
                    schema_version=ORDER_INTENT_SCHEMA_VERSION,
                    strategy_id=view.strategy_id,
                    signal_date=signal_date,
                    target_trade_date=target_trade_date,
                    symbol=symbol,
                    side="noop" if side != "rejected" else "rejected",
                    target_qty=0,
                    reason=reason,
                    target_weight=weight,
                    source_row_id=str(row.get("row_id", index)),
                    blocked_reasons=(reason,) if side == "rejected" else (),
                )
            )
            continue
        qty, lot_reason = apply_lot_and_sellable_rules({"target_qty": desired_delta, "side": side}, current_position)
        if qty <= 0:
            intents.append(
                PaperOrderIntent(
                    schema_version=ORDER_INTENT_SCHEMA_VERSION,
                    strategy_id=view.strategy_id,
                    signal_date=signal_date,
                    target_trade_date=target_trade_date,
                    symbol=symbol,
                    side="rejected",
                    target_qty=0,
                    reason=lot_reason,
                    target_weight=weight,
                    source_row_id=str(row.get("row_id", index)),
                    blocked_reasons=(lot_reason,),
                )
            )
            continue
        intents.append(
            PaperOrderIntent(
                schema_version=ORDER_INTENT_SCHEMA_VERSION,
                strategy_id=view.strategy_id,
                signal_date=signal_date,
                target_trade_date=target_trade_date,
                symbol=symbol,
                side=side,
                target_qty=qty,
                reason=lot_reason if lot_reason != "ok" else reason,
                target_weight=weight,
                source_row_id=str(row.get("row_id", index)),
            )
        )
    if hard_block_reasons:
        return PaperOrderIntentBuildResult(
            status="blocked",
            intents=tuple(intents),
            blocked_reasons=tuple(sorted(set(hard_block_reasons))),
        )
    return intents


def check_tradeability(
    intent: PaperOrderIntent | Mapping[str, Any], market_row: Mapping[str, Any] | None
) -> tuple[bool, str]:
    if not market_row:
        return False, "missing_market_row"
    missing = [
        field_name
        for field_name in ("raw_open", "raw_close", "volume", "up_limit", "down_limit")
        if _market_value(market_row, field_name) is None
    ]
    if missing:
        return False, "missing_market_fields:" + ",".join(missing)
    status = str(market_row.get("trade_status", market_row.get("status", ""))).lower()
    if status not in OPEN_TRADE_STATUSES:
        return False, "suspended_or_not_tradable_status"
    side = str(_field(intent, "side")).lower()
    raw_open = float(_market_value(market_row, "raw_open"))
    up_limit = float(_market_value(market_row, "up_limit"))
    down_limit = float(_market_value(market_row, "down_limit"))
    if side == "buy" and raw_open >= up_limit:
        return False, "limit_up_buy_blocked"
    if side == "sell" and raw_open <= down_limit:
        return False, "limit_down_sell_blocked"
    return True, "ok"


def calculate_costs(side: str, qty: int, exec_price: float, config: PaperBrokerConfig | Mapping[str, Any]) -> dict[str, float]:
    cfg = _broker_config_from_any(config)
    notional = max(qty, 0) * max(exec_price, 0.0)
    if notional <= 0:
        return {"commission": 0.0, "stamp_duty": 0.0, "stamp_tax": 0.0, "transfer_fee": 0.0, "total": 0.0}
    commission = max(cfg.min_commission, notional * cfg.commission_bps / 10_000)
    stamp_tax = notional * cfg.stamp_tax_bps / 10_000 if side == "sell" else 0.0
    transfer_fee = notional * cfg.transfer_fee_bps / 10_000
    total = commission + stamp_tax + transfer_fee
    return {
        "commission": round(commission, 6),
        "stamp_duty": round(stamp_tax, 6),
        "stamp_tax": round(stamp_tax, 6),
        "transfer_fee": round(transfer_fee, 6),
        "total": round(total, 6),
    }


def apply_participation_cap(qty: int, volume: float, rate: float) -> tuple[int, str]:
    if qty <= 0:
        return 0, "zero_quantity"
    if volume <= 0 or rate <= 0:
        return 0, "no_volume_capacity"
    capped = _round_down_lot(int(volume * rate))
    if capped <= 0:
        return 0, "participation_cap_below_lot"
    adjusted = min(qty, capped)
    if adjusted < qty:
        return adjusted, "participation_cap_partial"
    return adjusted, "ok"


def simulate_fills(
    order_intents: Sequence[PaperOrderIntent | Mapping[str, Any]],
    market_data: Sequence[Mapping[str, Any]],
    config: PaperBrokerConfig | Mapping[str, Any] | None = None,
    cash_snapshot: float | Mapping[str, Any] | None = None,
    position_snapshot: Mapping[str, Any] | None = None,
) -> list[PaperFill]:
    del cash_snapshot, position_snapshot
    cfg = _broker_config_from_any(config or {})
    if not 0 < cfg.max_participation_rate <= 1:
        raise PaperSimulationValidationError("invalid_max_participation_rate")
    market_index = _market_index(market_data)
    fills: list[PaperFill] = []
    for raw_intent in order_intents:
        intent = _intent_from_any(raw_intent)
        if intent.side in {"noop", "rejected"} or intent.target_qty <= 0:
            fills.append(_blocked_fill(intent, intent.side if intent.side == "rejected" else "expired", intent.reason or "no_executable_quantity"))
            continue
        key = (intent.target_trade_date, intent.symbol)
        market_row = market_index.get(key)
        tradable, reason = check_tradeability(intent, market_row)
        if not tradable:
            fills.append(_blocked_fill(intent, "rejected", reason))
            continue
        assert market_row is not None
        capped_qty, cap_reason = apply_participation_cap(
            intent.target_qty,
            float(_market_value(market_row, "volume") or 0.0),
            cfg.max_participation_rate,
        )
        if capped_qty <= 0:
            fills.append(_blocked_fill(intent, "expired", cap_reason))
            continue
        raw_open = float(_market_value(market_row, "raw_open"))
        slip = cfg.slippage_bps / 10_000
        exec_price = raw_open * (1 + slip if intent.side == "buy" else 1 - slip)
        costs = calculate_costs(intent.side, capped_qty, exec_price, cfg)
        status = "filled" if capped_qty == intent.target_qty else "partial"
        fills.append(
            PaperFill(
                schema_version=FILL_SCHEMA_VERSION,
                trade_date=intent.target_trade_date,
                symbol=intent.symbol,
                side=intent.side,
                requested_qty=intent.target_qty,
                filled_qty=capped_qty,
                status=status,
                exec_price=round(exec_price, 6),
                costs=costs,
                reason="ok" if cap_reason == "ok" else cap_reason,
            )
        )
    return fills


def mark_to_market(
    positions: Mapping[str, PaperPosition | Mapping[str, Any]],
    valuation_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    valuation_by_symbol = {str(row.get("symbol")): row for row in valuation_rows}
    rows: list[dict[str, Any]] = []
    for symbol, position_value in positions.items():
        position = _position_from_any(position_value)
        if position.quantity == 0:
            continue
        row = valuation_by_symbol.get(symbol)
        close_value = _market_value(row or {}, "raw_close")
        if close_value is None:
            raise PaperSimulationValidationError(f"missing_raw_close:{symbol}")
        raw_close = float(close_value)
        market_value = round(position.quantity * raw_close, 6)
        rows.append(
            {
                "symbol": symbol,
                "quantity": position.quantity,
                "sellable_qty": position.sellable_qty,
                "average_cost": position.average_cost,
                "raw_close": raw_close,
                "market_value": market_value,
            }
        )
    return rows


def reconcile_equity(cash: float, positions_value: float, equity: float, tolerance: float = 0.01) -> dict[str, Any]:
    expected = round(cash + positions_value, 6)
    diff = round(equity - expected, 6)
    return {
        "status": "pass" if abs(diff) <= tolerance else "blocked",
        "cash": round(cash, 6),
        "positions_value": round(positions_value, 6),
        "equity": round(equity, 6),
        "expected_equity": expected,
        "diff": diff,
        "tolerance": tolerance,
        "not_authorization": True,
    }


def roll_sellable_quantities(
    state: PaperAccountState | Mapping[str, Any],
    trade_date: str | None = None,
) -> PaperAccountState:
    del trade_date
    account = _account_state_from_any(state)
    rolled = {
        symbol: PaperPosition(
            symbol=symbol,
            quantity=position.quantity,
            sellable_qty=position.quantity,
            average_cost=position.average_cost,
        )
        for symbol, position in _positions_from_state(account).items()
    }
    return PaperAccountState(cash=account.cash, positions=rolled)


def apply_fills_to_ledger(
    initial_state: PaperAccountState | Mapping[str, Any] | float,
    fills: Sequence[PaperFill | Mapping[str, Any]],
    valuation_data: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any] | None = None,
) -> PaperLedgerResult:
    del config
    state = _account_state_from_any(initial_state)
    cash = float(state.cash)
    positions = _positions_from_state(state)
    cash_ledger: list[dict[str, Any]] = []
    position_ledger: list[dict[str, Any]] = []
    accepted_fills: list[PaperFill] = []
    sorted_fills = sorted((_fill_from_any(fill) for fill in fills), key=lambda item: (item.trade_date, item.symbol))
    valuation_index = _valuation_by_date(valuation_data)
    all_dates = sorted(set(valuation_index) | {fill.trade_date for fill in sorted_fills})
    equity_curve: list[dict[str, Any]] = []
    cost_totals = {"commission": 0.0, "stamp_duty": 0.0, "stamp_tax": 0.0, "transfer_fee": 0.0, "total": 0.0}
    turnover_notional = 0.0
    last_reconciliation: dict[str, Any] = reconcile_equity(cash, 0.0, cash)
    blocked_reasons: list[str] = []
    for current_date in all_dates:
        positions = _positions_from_state(roll_sellable_quantities(PaperAccountState(cash, positions), current_date))
        for fill in [item for item in sorted_fills if item.trade_date == current_date]:
            if fill.status not in {"filled", "partial"} or fill.filled_qty <= 0 or fill.exec_price is None:
                accepted_fills.append(fill)
                cash_ledger.append(_cash_ledger_row(current_date, fill, cash, cash, "audit_only"))
                continue
            before_cash = cash
            notional = fill.gross_amount
            total_cost = fill.total_cost
            if fill.side == "buy":
                affordable_qty = fill.filled_qty
                if notional + total_cost > cash:
                    affordable_qty = _affordable_lot(cash, fill.exec_price, fill.costs)
                if affordable_qty <= 0:
                    rejected = _replace_fill(fill, filled_qty=0, status="rejected", reason="insufficient_cash")
                    accepted_fills.append(rejected)
                    cash_ledger.append(_cash_ledger_row(current_date, rejected, cash, cash, "insufficient_cash"))
                    continue
                if affordable_qty < fill.filled_qty:
                    fill = _replace_fill(fill, filled_qty=affordable_qty, status="partial", reason="insufficient_cash_partial")
                    notional = fill.gross_amount
                    total_cost = fill.total_cost
                cash = round(cash - notional - total_cost, 6)
                positions[fill.symbol] = _buy_position(positions.get(fill.symbol), fill)
            elif fill.side == "sell":
                position = positions.get(fill.symbol, PaperPosition(symbol=fill.symbol))
                sell_qty = min(fill.filled_qty, position.sellable_qty)
                if sell_qty <= 0:
                    rejected = _replace_fill(fill, filled_qty=0, status="rejected", reason="no_sellable_quantity")
                    accepted_fills.append(rejected)
                    cash_ledger.append(_cash_ledger_row(current_date, rejected, cash, cash, "no_sellable_quantity"))
                    continue
                if sell_qty < fill.filled_qty:
                    fill = _replace_fill(fill, filled_qty=sell_qty, status="partial", reason="sellable_quantity_capped")
                    notional = fill.gross_amount
                    total_cost = fill.total_cost
                cash = round(cash + notional - total_cost, 6)
                positions[fill.symbol] = _sell_position(position, fill)
            for key in cost_totals:
                cost_totals[key] = round(cost_totals[key] + float(fill.costs.get(key, 0.0)), 6)
            turnover_notional = round(turnover_notional + fill.gross_amount, 6)
            accepted_fills.append(fill)
            cash_ledger.append(_cash_ledger_row(current_date, fill, before_cash, cash, "applied"))
        valuation_rows = valuation_index.get(current_date, [])
        try:
            position_rows = mark_to_market(positions, valuation_rows) if valuation_rows else []
        except PaperSimulationValidationError as exc:
            blocked_reasons.append(str(exc))
            position_rows = [
                {
                    "symbol": symbol,
                    "quantity": position.quantity,
                    "qty": position.quantity,
                    "sellable_qty": position.sellable_qty,
                    "average_cost": position.average_cost,
                    "market_value": 0.0,
                    "blocked_reason": str(exc),
                }
                for symbol, position in positions.items()
                if position.quantity != 0
            ]
        for row in position_rows:
            position_ledger.append({"trade_date": current_date, **row})
        positions_value = round(sum(float(row["market_value"]) for row in position_rows), 6)
        equity = round(cash + positions_value, 6)
        last_reconciliation = reconcile_equity(cash, positions_value, equity)
        equity_curve.append(
            {
                "trade_date": current_date,
                "cash": round(cash, 6),
                "positions_value": positions_value,
                "equity": equity,
                "reconciliation_status": last_reconciliation["status"],
            }
        )
    final_positions = [
        {**position.to_dict(), "symbol": symbol}
        for symbol, position in sorted(positions.items())
        if position.quantity != 0
    ]
    max_drawdown = _max_drawdown([float(row["equity"]) for row in equity_curve])
    final_equity = float(equity_curve[-1]["equity"]) if equity_curve else cash
    turnover = round(turnover_notional / final_equity, 6) if final_equity else 0.0
    return PaperLedgerResult(
        schema_version=LEDGER_SCHEMA_VERSION,
        final_state=PaperAccountState(cash=cash, positions=positions),
        fills=tuple(accepted_fills),
        positions=tuple(final_positions),
        position_ledger=tuple(position_ledger),
        cash_ledger=tuple(cash_ledger),
        equity_curve=tuple(equity_curve),
        reconciliation=last_reconciliation,
        cost_totals=cost_totals,
        turnover=turnover,
        max_drawdown=max_drawdown,
        status="blocked" if blocked_reasons or last_reconciliation["status"] == "blocked" else "pass",
        blocked_reasons=tuple(blocked_reasons),
    )


def run_paper_simulation(config: Mapping[str, Any]) -> PaperSimulationRunResult:
    package_path = (
        config.get("strategy_package_path")
        or config.get("admission_package_path")
        or config.get("admission_package")
    )
    target_path = config.get("target_portfolio_path") or config.get("target_portfolio")
    market_path = config.get("market_data_path") or config.get("market_data")
    if not package_path or not target_path or not market_path:
        raise PaperSimulationValidationError("missing_input_path")
    run_id = str(config.get("run_id") or f"paper-simulation-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    try:
        package_payload = load_strategy_admission_package(package_path)
        expected_strategy_id = config.get("expected_strategy_id") or config.get("strategy_id")
        admission_view = build_admission_view(package_payload, package_path, expected_strategy_id)
    except PaperSimulationValidationError as exc:
        return _blocked_run_result(run_id, str(exc))
    target_payload = _read_json_file(target_path)
    market_payload = _read_json_file(market_path)
    market_rows = _market_rows(market_payload)
    calendar = config.get("trade_calendar")
    if calendar is None:
        calendar = target_payload.get("calendar") if isinstance(target_payload, Mapping) else None
    if not calendar:
        calendar = _calendar_from_market_rows(market_rows)
    target_payload = dict(target_payload) if isinstance(target_payload, Mapping) else {"rows": target_payload}
    target_payload.setdefault("initial_cash", config.get("initial_cash"))
    target_payload.setdefault("initial_equity", config.get("initial_cash"))
    initial_state = config.get("initial_state", {})
    current_positions = config.get("current_positions")
    if current_positions is None and isinstance(initial_state, Mapping):
        current_positions = initial_state.get("positions")
    initial_cash = float(
        config.get(
            "initial_cash",
            initial_state.get("cash", target_payload.get("initial_cash", 1_000_000.0))
            if isinstance(initial_state, Mapping)
            else target_payload.get("initial_cash", 1_000_000.0),
        )
    )
    intent_result = build_order_intents(
        admission_view,
        target_payload,
        calendar,
        current_positions=current_positions,
    )
    if isinstance(intent_result, PaperOrderIntentBuildResult):
        return _blocked_run_result(run_id, " ".join(intent_result.blocked_reasons))
    order_intents = intent_result
    broker_config = _broker_config_from_any(config.get("broker_config", config.get("cost_config", config)))
    fills = simulate_fills(order_intents, market_rows, broker_config)
    ledger = apply_fills_to_ledger(initial_cash, fills, market_rows)
    result = PaperSimulationRunResult(
        schema_version=RUN_RESULT_SCHEMA_VERSION,
        run_id=run_id,
        admission_view=admission_view,
        order_intents=tuple(order_intents),
        fills=tuple(fills),
        ledger=ledger,
    )
    output_root = config.get("output_root")
    if output_root:
        paths = write_paper_simulation_artifacts(result, output_root, overwrite=bool(config.get("overwrite", False)))
        result = PaperSimulationRunResult(
            schema_version=result.schema_version,
            run_id=result.run_id,
            admission_view=result.admission_view,
            order_intents=result.order_intents,
            fills=result.fills,
            ledger=result.ledger,
            artifact_paths=paths,
            operation_counters=result.operation_counters,
        )
    return result


def write_paper_simulation_artifacts(
    result: PaperSimulationRunResult | Mapping[str, Any],
    output_root: str | Path,
    overwrite: bool = False,
) -> dict[str, str]:
    payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
    output_path = Path(output_root) / str(payload.get("run_id", "paper-simulation-run"))
    if output_path.exists() and any(output_path.iterdir()) and not overwrite:
        raise PaperSimulationValidationError("output_dir_exists")
    output_path.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "paper_simulation_summary": _summary_payload(payload),
        "order_intents": payload.get("order_intents", []),
        "fills": payload.get("fills", []),
        "positions": payload.get("positions", []),
        "cash_ledger": payload.get("cash_ledger", []),
        "equity_curve": payload.get("equity_curve", []),
        "reconciliation": payload.get("reconciliation", {}),
        "forbidden_operation_counters": payload.get("forbidden_operation_counters", zero_forbidden_operation_counts()),
        "run_manifest": _run_manifest_payload(payload),
        "PAPER-SIMULATION-REPORT": payload,
    }
    path_map: dict[str, str] = {}
    for name, artifact in artifacts.items():
        artifact_path = output_path / f"{name}.json"
        with artifact_path.open("w", encoding="utf-8") as handle:
            json.dump(_json_safe(artifact), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        path_map[name] = str(artifact_path)
    report_md = output_path / "PAPER-SIMULATION-REPORT.md"
    report_md.write_text(_report_markdown(payload), encoding="utf-8")
    path_map["PAPER-SIMULATION-REPORT.md"] = str(report_md)
    return path_map


def _violation(code: str, message: str, field: str = "") -> PaperSimulationViolation:
    return PaperSimulationViolation(code=code, message=message, field=field)


def _sha256_json(payload: Mapping[str, Any], exclude_keys: set[str] | None = None) -> str:
    exclude = exclude_keys or set()
    filtered = {key: value for key, value in payload.items() if key not in exclude}
    blob = json.dumps(_json_safe(filtered), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _normalise_operation_counts(raw: Any) -> dict[str, int]:
    counts = zero_forbidden_operation_counts()
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            try:
                counts[str(key)] = int(value)
            except (TypeError, ValueError):
                counts[str(key)] = 1
    return counts


def _forbidden_counter_violations(counts: Mapping[str, int]) -> list[PaperSimulationViolation]:
    return [
        _violation(f"forbidden_operation_nonzero:{name}", f"{name} count must be zero", name)
        for name, value in counts.items()
        if int(value) != 0
    ]


def _sensitive_field_violations(payload: Any) -> list[PaperSimulationViolation]:
    return [
        _violation("sensitive_material_present", f"sensitive field present: {field}", field)
        for field in sorted(_sensitive_fields(payload))
    ]


def _sensitive_fields(payload: Any, prefix: str = "") -> set[str]:
    fields: set[str] = set()
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if any(pattern in key_text.lower() for pattern in SENSITIVE_FIELD_PATTERNS):
                fields.add(path)
            fields.update(_sensitive_fields(value, path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            fields.update(_sensitive_fields(value, f"{prefix}[{index}]"))
    return fields


def _contains_sensitive_key(payload: Any) -> bool:
    return bool(_sensitive_fields(payload))


def _find_strategy_candidate(candidates: Any, expected_strategy_id: str | None) -> Mapping[str, Any] | None:
    if not isinstance(candidates, list):
        return None
    if expected_strategy_id:
        for candidate in candidates:
            if isinstance(candidate, Mapping) and candidate.get("strategy_id") == expected_strategy_id:
                return candidate
        return None
    for candidate in candidates:
        if isinstance(candidate, Mapping):
            return candidate
    return None


def _mapping_items(raw: Any) -> list[Mapping[str, Any]]:
    return [dict(item) for item in raw if isinstance(item, Mapping)] if isinstance(raw, list) else []


def _input_refs_from_any(raw: Any) -> Mapping[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    if isinstance(raw, list):
        return {f"ref_{index}": value for index, value in enumerate(raw)}
    return {}


def _to_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _calendar_open_dates(calendar: Sequence[Any]) -> list[date]:
    if isinstance(calendar, Mapping):
        raw_dates = calendar.get("open_dates", calendar.get("calendar", []))
        if isinstance(raw_dates, Sequence) and not isinstance(raw_dates, (str, bytes)):
            return _calendar_open_dates(raw_dates)
    dates: list[date] = []
    for row in calendar:
        if isinstance(row, str):
            dates.append(_to_date(row))
        elif isinstance(row, Mapping):
            is_open = row.get("is_open", row.get("open", True))
            status = str(row.get("trade_status", row.get("status", "open"))).lower()
            if is_open and status in OPEN_TRADE_STATUSES:
                raw_date = row.get("trade_date", row.get("date"))
                if raw_date:
                    dates.append(_to_date(str(raw_date)))
    return dates


def _round_down_lot(quantity: int) -> int:
    return max(0, int(quantity) // 100 * 100)


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _target_rows(target_portfolio: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if isinstance(target_portfolio, Mapping):
        rows = target_portfolio.get("rows", target_portfolio.get("targets", target_portfolio.get("target_portfolio", [])))
    else:
        rows = target_portfolio
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise PaperSimulationValidationError("target_portfolio_rows_missing")
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _admission_view_from_any(value: PaperSimulationAdmissionView | Mapping[str, Any]) -> PaperSimulationAdmissionView:
    if isinstance(value, PaperSimulationAdmissionView):
        return value
    validation_raw = value.get("validation", {}) if isinstance(value, Mapping) else {}
    validation = PaperSimulationValidation(
        passed=bool(validation_raw.get("passed", value.get("validation_passed", True))),
        forbidden_operation_counts=_normalise_operation_counts(value.get("operation_counts", {})),
    )
    return PaperSimulationAdmissionView(
        strategy_id=str(value.get("strategy_id", "")),
        run_id=str(value.get("run_id", "")),
        source_run_id=str(value.get("source_run_id", value.get("run_id", ""))),
        source_portfolio_id=str(value.get("source_portfolio_id", "")),
        source_path=str(value.get("source_path", "")),
        package_hash=str(value.get("package_hash", "")),
        schema_version=str(value.get("schema_version", "")),
        package_schema_version=str(value.get("package_schema_version", "")),
        status=str(value.get("status", "")),
        overall_admission=str(value.get("overall_admission", "")),
        simulation_candidate=bool(value.get("simulation_candidate", False)),
        not_authorization=bool(value.get("not_authorization", True)),
        not_simulation_authorization=bool(value.get("not_simulation_authorization", True)),
        not_live_authorization=bool(value.get("not_live_authorization", True)),
        not_broker_order=bool(value.get("not_broker_order", True)),
        blocked_claims=tuple(_mapping_items(value.get("blocked_claims", []))),
        allowed_claims=tuple(_mapping_items(value.get("allowed_claims", []))),
        input_refs=dict(value.get("input_refs", {})) if isinstance(value.get("input_refs", {}), Mapping) else {},
        operation_counts=_normalise_operation_counts(value.get("operation_counts", {})),
        candidate=dict(value.get("candidate", {})) if isinstance(value.get("candidate", {}), Mapping) else {},
        validation=validation,
    )


def _rejected_intent(
    view: PaperSimulationAdmissionView,
    signal_date: str,
    target_trade_date: str,
    row: Mapping[str, Any],
    reason: str,
    index: int,
) -> PaperOrderIntent:
    return PaperOrderIntent(
        schema_version=ORDER_INTENT_SCHEMA_VERSION,
        strategy_id=view.strategy_id,
        signal_date=signal_date,
        target_trade_date=target_trade_date,
        symbol=str(row.get("symbol", "")),
        side="rejected",
        target_qty=0,
        reason=reason,
        source_row_id=str(row.get("row_id", index)),
        blocked_reasons=(reason,),
    )


def _desired_delta(
    row: Mapping[str, Any],
    current_position: PaperPosition,
    initial_equity: float | None,
) -> tuple[str, int, str, float | None]:
    side = str(row.get("side", "")).lower()
    target_weight = _optional_float(row.get("target_weight", row.get("weight")))
    if "target_qty" in row or "quantity" in row or "qty" in row:
        target_qty = int(float(row.get("target_qty", row.get("quantity", row.get("qty", 0))) or 0))
    elif target_weight is not None:
        price = _optional_float(row.get("price", row.get("reference_price", row.get("estimated_price", row.get("raw_close")))))
        if initial_equity is None or price is None or price <= 0:
            return "rejected", 0, "missing_equity_or_price_for_weight", target_weight
        target_qty = _round_down_lot(int(initial_equity * target_weight / price))
    else:
        return "rejected", 0, "missing_target_quantity_or_weight", target_weight
    if side not in {"buy", "sell"}:
        delta = target_qty - current_position.quantity
        if delta > 0:
            return "buy", delta, "target_position_delta", target_weight
        if delta < 0:
            return "sell", abs(delta), "target_position_delta", target_weight
        return "noop", 0, "already_at_target", target_weight
    return side, abs(target_qty), "explicit_side", target_weight


def _broker_config_from_any(value: PaperBrokerConfig | Mapping[str, Any]) -> PaperBrokerConfig:
    if isinstance(value, PaperBrokerConfig):
        return value
    return PaperBrokerConfig(
        commission_bps=(
            float(value["commission_bps"])
            if "commission_bps" in value
            else None
        ),
        min_commission=float(value.get("min_commission", 5.0)),
        stamp_tax_bps=(
            float(value["stamp_tax_bps"])
            if "stamp_tax_bps" in value
            else None
        ),
        transfer_fee_bps=(
            float(value["transfer_fee_bps"])
            if "transfer_fee_bps" in value
            else None
        ),
        slippage_bps=(
            float(value["slippage_bps"])
            if "slippage_bps" in value
            else None
        ),
        max_participation_rate=float(value.get("max_participation_rate", 0.10)),
        fixed_slippage_bps=_optional_float(value.get("fixed_slippage_bps")),
        commission_rate=_optional_float(value.get("commission_rate")),
        stamp_duty_rate=_optional_float(value.get("stamp_duty_rate")),
        transfer_fee_rate=_optional_float(value.get("transfer_fee_rate")),
    )


def _market_value(row: Mapping[str, Any], canonical: str) -> Any:
    aliases = {
        "raw_open": ("raw_open", "open", "open_price"),
        "raw_close": ("raw_close", "close", "close_price"),
        "volume": ("volume", "vol"),
        "up_limit": ("up_limit", "limit_up"),
        "down_limit": ("down_limit", "limit_down"),
    }
    for key in aliases.get(canonical, (canonical,)):
        if key in row:
            return row[key]
    return None


def _field(value: Any, name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name)


def _market_index(market_data: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in market_data:
        trade_date = str(row.get("trade_date", row.get("date", "")))[:10]
        symbol = str(row.get("symbol", ""))
        if trade_date and symbol:
            result[(trade_date, symbol)] = row
    return result


def _intent_from_any(value: PaperOrderIntent | Mapping[str, Any]) -> PaperOrderIntent:
    if isinstance(value, PaperOrderIntent):
        return value
    return PaperOrderIntent(
        schema_version=str(value.get("schema_version", ORDER_INTENT_SCHEMA_VERSION)),
        strategy_id=str(value.get("strategy_id", "")),
        signal_date=str(value.get("signal_date", "")),
        target_trade_date=str(value.get("target_trade_date", "")),
        symbol=str(value.get("symbol", "")),
        side=str(value.get("side", "")),
        target_qty=int(value.get("target_qty", 0) or 0),
        execution_price_policy=str(value.get("execution_price_policy", RAW_OPEN_EXECUTION_POLICY)),
        not_authorization=bool(value.get("not_authorization", True)),
        reason=str(value.get("reason", "")),
        target_weight=_optional_float(value.get("target_weight")),
        source_row_id=str(value.get("source_row_id", "")),
        blocked_reasons=tuple(value.get("blocked_reasons", ()) or ()),
        operation_counters=_normalise_operation_counts(value.get("operation_counters", {})),
    )


def _blocked_fill(intent: PaperOrderIntent, status: str, reason: str) -> PaperFill:
    return PaperFill(
        schema_version=FILL_SCHEMA_VERSION,
        trade_date=intent.target_trade_date,
        symbol=intent.symbol,
        side=intent.side,
        requested_qty=intent.target_qty,
        filled_qty=0,
        status=status,
        exec_price=None,
        costs=calculate_costs(intent.side, 0, 0.0, PaperBrokerConfig()),
        reason=reason,
    )


def _position_from_any(value: PaperPosition | Mapping[str, Any]) -> PaperPosition:
    if isinstance(value, PaperPosition):
        return value
    return PaperPosition(
        symbol=str(value.get("symbol", "")),
        quantity=int(value.get("quantity", value.get("qty", 0)) or 0),
        sellable_qty=int(value.get("sellable_qty", value.get("sellable", value.get("quantity", 0))) or 0),
        average_cost=float(value.get("average_cost", value.get("avg_cost", 0.0)) or 0.0),
    )


def _account_state_from_any(value: PaperAccountState | Mapping[str, Any] | float) -> PaperAccountState:
    if isinstance(value, PaperAccountState):
        return value
    if isinstance(value, Mapping):
        return PaperAccountState(
            cash=float(value.get("cash", value.get("initial_cash", 0.0)) or 0.0),
            positions=value.get("positions", {}) if isinstance(value.get("positions", {}), Mapping) else {},
        )
    return PaperAccountState(cash=float(value), positions={})


def _positions_from_state(state: PaperAccountState) -> dict[str, PaperPosition]:
    return {
        symbol: _position_from_any(position)
        for symbol, position in state.positions.items()
    }


def _fill_from_any(value: PaperFill | Mapping[str, Any]) -> PaperFill:
    if isinstance(value, PaperFill):
        return value
    return PaperFill(
        schema_version=str(value.get("schema_version", FILL_SCHEMA_VERSION)),
        trade_date=str(value.get("trade_date", "")),
        symbol=str(value.get("symbol", "")),
        side=str(value.get("side", "")),
        requested_qty=int(value.get("requested_qty", 0) or 0),
        filled_qty=int(value.get("filled_qty", 0) or 0),
        status=str(value.get("status", "")),
        exec_price=_optional_float(value.get("exec_price")),
        costs=dict(value.get("costs", {})) if isinstance(value.get("costs", {}), Mapping) else {},
        reason=str(value.get("reason", "")),
        not_authorization=bool(value.get("not_authorization", True)),
        operation_counters=_normalise_operation_counts(value.get("operation_counters", {})),
    )


def _valuation_by_date(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    result: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        trade_date = str(row.get("trade_date", row.get("date", "")))[:10]
        if trade_date:
            result.setdefault(trade_date, []).append(row)
    return result


def _replace_fill(fill: PaperFill, **updates: Any) -> PaperFill:
    payload = fill.to_dict()
    payload.update(updates)
    if "filled_qty" in updates or "exec_price" in updates:
        qty = int(payload.get("filled_qty", 0) or 0)
        price = float(payload.get("exec_price", 0.0) or 0.0)
        payload["costs"] = calculate_costs(str(payload.get("side", "")), qty, price, PaperBrokerConfig())
    return _fill_from_any(payload)


def _affordable_lot(cash: float, price: float, costs: Mapping[str, float]) -> int:
    if price <= 0:
        return 0
    estimated_unit_cost = price * (1 + float(costs.get("total", 0.0)) / max(price, 1.0) / 100)
    max_qty = int(cash / max(estimated_unit_cost, price))
    return _round_down_lot(max_qty)


def _buy_position(position: PaperPosition | None, fill: PaperFill) -> PaperPosition:
    current = position or PaperPosition(symbol=fill.symbol)
    new_qty = current.quantity + fill.filled_qty
    average_cost = (
        (current.average_cost * current.quantity + float(fill.exec_price or 0.0) * fill.filled_qty) / new_qty
        if new_qty
        else 0.0
    )
    return PaperPosition(
        symbol=fill.symbol,
        quantity=new_qty,
        sellable_qty=current.sellable_qty,
        average_cost=round(average_cost, 6),
    )


def _sell_position(position: PaperPosition, fill: PaperFill) -> PaperPosition:
    new_qty = max(0, position.quantity - fill.filled_qty)
    new_sellable = max(0, position.sellable_qty - fill.filled_qty)
    return PaperPosition(
        symbol=position.symbol,
        quantity=new_qty,
        sellable_qty=new_sellable,
        average_cost=position.average_cost if new_qty else 0.0,
    )


def _cash_ledger_row(
    trade_date: str,
    fill: PaperFill,
    before_cash: float,
    after_cash: float,
    status: str,
) -> dict[str, Any]:
    return {
        "trade_date": trade_date,
        "symbol": fill.symbol,
        "side": fill.side,
        "status": status,
        "fill_status": fill.status,
        "filled_qty": fill.filled_qty,
        "exec_price": fill.exec_price,
        "gross_amount": fill.gross_amount,
        "total_cost": fill.total_cost,
        "cash_before": round(before_cash, 6),
        "cash_after": round(after_cash, 6),
        "reason": fill.reason,
    }


def _max_drawdown(values: Sequence[float]) -> float:
    peak = None
    max_dd = 0.0
    for value in values:
        peak = value if peak is None else max(peak, value)
        if peak:
            max_dd = min(max_dd, value / peak - 1)
    return round(max_dd, 6)


def _read_json_file(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _market_rows(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        rows = payload.get("rows", payload.get("market_data", []))
    else:
        rows = payload
    if not isinstance(rows, list):
        raise PaperSimulationValidationError("market_data_rows_missing")
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _calendar_from_market_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    calendar: list[dict[str, Any]] = []
    for row in rows:
        trade_date = str(row.get("trade_date", row.get("date", "")))[:10]
        if trade_date and trade_date not in seen:
            seen.add(trade_date)
            calendar.append({"trade_date": trade_date, "is_open": True, "trade_status": "open"})
    return sorted(calendar, key=lambda item: item["trade_date"])


def _summary_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "run_id": payload.get("run_id"),
        "not_authorization": True,
        "simulation_ready": False,
        "live_ready": False,
        "order_intent_count": len(payload.get("order_intents", [])),
        "fill_count": len(payload.get("fills", [])),
        "reconciliation": payload.get("reconciliation", {}),
        "cost_totals": payload.get("cost_totals", {}),
        "forbidden_operation_counters": payload.get("forbidden_operation_counters", zero_forbidden_operation_counts()),
        "operation_counts": payload.get("operation_counts", zero_forbidden_operation_counts()),
    }


def _run_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "paper_simulation_run_manifest_v1",
        "run_id": payload.get("run_id"),
        "not_authorization": True,
        "not_simulation_authorization": True,
        "not_live_authorization": True,
        "not_broker_order": True,
        "simulation_ready": False,
        "live_ready": False,
        "operation_counts": payload.get("operation_counts", zero_forbidden_operation_counts()),
        "artifact_schema_version": payload.get("schema_version"),
    }


def _report_markdown(payload: Mapping[str, Any]) -> str:
    summary = _summary_payload(payload)
    return "\n".join(
        [
            "# PAPER SIMULATION REPORT",
            "",
            f"- run_id: {summary.get('run_id')}",
            "- not_authorization: true",
            "- simulation_ready: false",
            "- live_ready: false",
            f"- order_intent_count: {summary.get('order_intent_count')}",
            f"- fill_count: {summary.get('fill_count')}",
            "",
        ]
    )


def _blocked_run_result(run_id: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": RUN_RESULT_SCHEMA_VERSION,
        "status": "blocked",
        "passed": False,
        "run_id": run_id,
        "blocked_reasons": [reason],
        "not_authorization": True,
        "simulation_ready": False,
        "live_ready": False,
        "forbidden_operation_counters": zero_forbidden_operation_counts(),
        "operation_counts": zero_forbidden_operation_counts(),
    }


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
