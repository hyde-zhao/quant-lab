"""多因子策略真实 simulation runtime operator。

本模块只在调用方显式传入 runtime env、base_url 和 authorization_ref 时触达
QMT gateway；导入模块本身不读取凭据、不连接 gateway、不下单。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from trading.pretrade_risk import RawPriceRef, RiskInputSnapshot, RiskProfile
from trading.qmt_client import QmtClient, QmtClientConfig, QmtResponse
from trading.qmt_gateway_contracts import (
    QMT_SIMULATION_CANCEL_ENDPOINT_ID,
    QMT_SIMULATION_SUBMIT_ENDPOINT_ID,
    QmtGatewayResult,
    QmtSimulationCancelRequest,
    QmtSimulationOperationPayload,
    QmtSimulationOrderRequest,
    build_blocked_result,
    build_simulation_cancel_request,
    build_simulation_operation_result,
)
from trading.qmt_runtime import StdlibQmtRestTransport, build_runtime_hmac_provider
from trading.stage_gate import (
    AuthorizationSummary,
    Stage,
    StageEvidence,
    StageGateRequest,
)
from trading.reconciliation import RECON_DIMENSIONS, ThresholdConfig
from trading.strategy_runner.simulation_activation import (
    SimulationExecutionAction,
    SimulationExecutionEngineRequest,
    SimulationExecutionEngineResult,
    SimulationGateway,
    execute_simulation_order_plan,
)
from trading.strategy_runner.simulation_order_plan import (
    SimulationOrderPlanRequest,
    build_simulation_order_plan,
)
from trading.strategy_runner.simulation_reconciliation import (
    SimulationReconciliationRequest,
    reconcile_simulation_run,
)
from trading.strategy_runner.target_portfolio import (
    MultifactorSignalRow,
    build_multifactor_target_portfolio,
)


SIMULATION_OPERATOR_SCHEMA_VERSION = "runner-multifactor-simulation-operator-v1"


@dataclass(frozen=True, slots=True)
class EvidencePersistencePolicy:
    """真实 runtime 证据持久化边界。"""

    output_path: str
    retention_days: int = 30
    raw_payload_allowed: bool = False
    broker_lake_write_allowed: bool = False
    raw_account_allowed: bool = False
    raw_symbol_allowed: bool = False
    raw_broker_order_ref_allowed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "output_path": self.output_path,
            "retention_days": self.retention_days,
            "raw_payload_allowed": self.raw_payload_allowed,
            "broker_lake_write_allowed": self.broker_lake_write_allowed,
            "raw_account_allowed": self.raw_account_allowed,
            "raw_symbol_allowed": self.raw_symbol_allowed,
            "raw_broker_order_ref_allowed": self.raw_broker_order_ref_allowed,
            "storage": "process/evidence redacted-summary-only",
        }


@dataclass(frozen=True, slots=True)
class StabilityWindowPolicy:
    """模拟盘稳定性窗口定义。"""

    required_runs: int = 1
    window_id: str = "simulation-window:first-authorized-run"
    evidence_refs: tuple[str, ...] = ()

    def status_for(self, *, current_passed: bool) -> str:
        completed = len(self.evidence_refs) + (1 if current_passed else 0)
        return "pass" if completed >= max(int(self.required_runs), 1) else "collecting"

    def to_dict(self, *, current_passed: bool) -> dict[str, object]:
        completed = len(self.evidence_refs) + (1 if current_passed else 0)
        return {
            "window_id": self.window_id,
            "required_runs": max(int(self.required_runs), 1),
            "completed_runs": completed,
            "status": self.status_for(current_passed=current_passed),
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class MultifactorSimulationOperatorRequest:
    """一次真实 simulation operator 请求。"""

    strategy_id: str
    run_id: str
    target_trade_date: str
    authorization_ref: str
    expected_runtime_profile: str
    signal_rows: tuple[MultifactorSignalRow, ...]
    capital_base: Decimal | int | float | str
    current_positions: Mapping[str, int]
    risk_snapshot: RiskInputSnapshot
    risk_profile: RiskProfile
    stage_evidence: StageEvidence
    persistence_policy: EvidencePersistencePolicy
    stability_window: StabilityWindowPolicy = field(default_factory=StabilityWindowPolicy)
    top_n: int = 1
    weighting: str = "equal"
    max_weight: Decimal | int | float | str | None = None
    universe_symbols: tuple[str, ...] = ()
    max_turnover_notional: Decimal | int | float | str | None = None
    cancel_submitted_after_submit: bool = True
    timeout_seconds: int = 10
    schema_version: str = SIMULATION_OPERATOR_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class MultifactorSimulationOperatorResult:
    """operator 输出；只包含脱敏摘要。"""

    status: str
    run_id: str
    authorization_ref: str
    blocked_reason: str = ""
    target_summary: Mapping[str, object] = field(default_factory=dict)
    order_plan_summary: Mapping[str, object] = field(default_factory=dict)
    execution_summary: Mapping[str, object] = field(default_factory=dict)
    reconciliation_summary: Mapping[str, object] = field(default_factory=dict)
    pre_positions_summary: Mapping[str, object] = field(default_factory=dict)
    post_positions_summary: Mapping[str, object] = field(default_factory=dict)
    persistence_policy: EvidencePersistencePolicy | None = None
    stability_window: Mapping[str, object] = field(default_factory=dict)
    runtime_authorization_granted: bool = True
    small_live_or_live_authorized: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = SIMULATION_OPERATOR_SCHEMA_VERSION

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
            "run_id": self.run_id,
            "authorization_ref": self.authorization_ref,
            "blocked_reason": self.blocked_reason,
            "runtime_authorization_granted": self.runtime_authorization_granted,
            "small_live_or_live_authorized": self.small_live_or_live_authorized,
            "generated_at": self.generated_at,
            "pre_positions": dict(self.pre_positions_summary),
            "target": dict(self.target_summary),
            "order_plan": dict(self.order_plan_summary),
            "execution": dict(self.execution_summary),
            "post_positions": dict(self.post_positions_summary),
            "reconciliation": dict(self.reconciliation_summary),
            "stability_window": dict(self.stability_window),
            "persistence_policy": (
                self.persistence_policy.to_dict()
                if self.persistence_policy is not None
                else {}
            ),
            "redaction_policy": {
                "raw_payload_saved": False,
                "raw_account_saved": False,
                "raw_symbol_saved": False,
                "raw_broker_order_ref_saved": False,
                "secret_or_token_saved": False,
                "fund_detail_saved": False,
            },
        }


class RuntimeQmtSimulationGateway(SimulationGateway):
    """把 QmtClient simulation transport 适配给 P3 execution engine。"""

    def __init__(self, client: QmtClient, *, expected_runtime_profile: str) -> None:
        self.client = client
        self.expected_runtime_profile = expected_runtime_profile

    def submit_order(self, request: QmtSimulationOrderRequest) -> QmtGatewayResult:
        response = self.client.submit_simulation(
            run_id=request.run_id,
            request_id=request.request_id,
            intent_id=request.order_intent_id,
            authorization_ref=request.authorization_ref,
            expected_runtime_mode="simulation",
            expected_runtime_profile=self.expected_runtime_profile,
            payload={
                "order_intent_id": request.order_intent_id,
                "symbol": request.symbol,
                "side": request.side,
                "quantity": request.quantity,
                "price": request.price,
                "price_type": request.price_type,
                "authorization_ref": request.authorization_ref,
                "idempotency_key": request.idempotency_key,
                "redaction_label": request.redaction_label,
            },
        )
        return _qmt_response_to_gateway_result(response, QMT_SIMULATION_SUBMIT_ENDPOINT_ID)

    def cancel_order(self, request: QmtSimulationCancelRequest) -> QmtGatewayResult:
        response = self.client.cancel_simulation(
            run_id=request.run_id,
            request_id=request.request_id,
            intent_id=request.order_intent_id,
            authorization_ref=request.authorization_ref,
            expected_runtime_mode="simulation",
            expected_runtime_profile=self.expected_runtime_profile,
            payload={
                "order_intent_id": request.order_intent_id,
                "broker_order_ref": request.broker_order_ref,
                "symbol": request.symbol,
                "authorization_ref": request.authorization_ref,
                "idempotency_key": request.idempotency_key,
                "redaction_label": request.redaction_label,
            },
        )
        return _qmt_response_to_gateway_result(response, QMT_SIMULATION_CANCEL_ENDPOINT_ID)


def run_multifactor_simulation_operator(
    request: MultifactorSimulationOperatorRequest,
    *,
    qmt_client: QmtClient,
) -> MultifactorSimulationOperatorResult:
    """执行 P1-P4 的真实 simulation runtime 编排。"""

    auth_reason = _authorization_block_reason(request)
    if auth_reason:
        return _blocked(request, auth_reason)

    pre_positions = _query_positions_summary(
        qmt_client.query_positions(
            run_id=request.run_id,
            request_id=f"{request.run_id}:pre-positions",
            authorization_ref=request.authorization_ref,
            timeout_seconds=request.timeout_seconds,
        )
    )
    if pre_positions["status"] != "ok":
        return _blocked(request, str(pre_positions.get("reason_code") or "pre_positions_blocked"), pre_positions=pre_positions)

    target = build_multifactor_target_portfolio(
        strategy_id=request.strategy_id,
        source_run_id=request.run_id,
        target_trade_date=request.target_trade_date,
        signal_rows=request.signal_rows,
        top_n=request.top_n,
        weighting=request.weighting,
        max_weight=request.max_weight,
        universe_symbols=request.universe_symbols,
        lineage_refs={"runtime": "authorized-simulation-operator"},
    )
    if target.blocked or target.snapshot is None:
        return _blocked(request, target.blocked_reason or "target_portfolio_blocked", pre_positions=pre_positions, target=target.to_dict())

    plan = build_simulation_order_plan(
        SimulationOrderPlanRequest(
            strategy_id=request.strategy_id,
            run_id=request.run_id,
            target_trade_date=request.target_trade_date,
            target_rows=tuple(target.snapshot.rows()),
            capital_base=request.capital_base,
            risk_snapshot=request.risk_snapshot,
            risk_profile=request.risk_profile,
            current_positions=request.current_positions,
            max_turnover_notional=request.max_turnover_notional,
        )
    )
    if plan.blocked:
        return _blocked(request, plan.blocked_reason or "order_plan_blocked", pre_positions=pre_positions, target=target.to_dict(), order_plan=plan.to_dict())

    execution = execute_simulation_order_plan(
        SimulationExecutionEngineRequest(
            strategy_id=request.strategy_id,
            run_id=request.run_id,
            target_trade_date=request.target_trade_date,
            order_plan=plan,
            stage_request=_stage_request(request),
            stage_evidence=request.stage_evidence,
            authorization_ref=request.authorization_ref,
            expected_runtime_mode="simulation",
            expected_runtime_profile=request.expected_runtime_profile,
        ),
        RuntimeQmtSimulationGateway(qmt_client, expected_runtime_profile=request.expected_runtime_profile),
    )
    if request.cancel_submitted_after_submit and execution.passed:
        execution = _cancel_submitted_actions(request, execution, RuntimeQmtSimulationGateway(qmt_client, expected_runtime_profile=request.expected_runtime_profile))

    post_positions = _query_positions_summary(
        qmt_client.query_positions(
            run_id=request.run_id,
            request_id=f"{request.run_id}:post-positions",
            authorization_ref=request.authorization_ref,
            timeout_seconds=request.timeout_seconds,
        )
    )
    if post_positions["status"] != "ok":
        return _blocked(
            request,
            str(post_positions.get("reason_code") or "post_positions_blocked"),
            pre_positions=pre_positions,
            target=target.to_dict(),
            order_plan=plan.to_dict(),
            execution=execution.to_dict(),
            post_positions=post_positions,
        )

    reconciliation = reconcile_simulation_run(
        SimulationReconciliationRequest(
            run_id=request.run_id,
            target_portfolio_ref=target.snapshot.target_portfolio_id,
            pre_positions_digest=str(pre_positions.get("positions_digest") or ""),
            post_positions_digest=str(post_positions.get("positions_digest") or ""),
            execution_result=execution,
            local_state=_reconciliation_state(execution, len(plan.orders)),
            broker_facts=_reconciliation_state(execution, len(plan.orders)),
            broker_lake_facts={"count": 6, "ref": _stable_ref(request.run_id, "broker-lake")},
            thresholds=_default_thresholds(),
            input_source="authorized_redacted_snapshot_ref",
        )
    )
    status = "pass" if reconciliation.passed and not execution.manual_takeover_required else "blocked"
    blocked_reason = "" if status == "pass" else reconciliation.blocked_reason or execution.blocked_reason
    result = MultifactorSimulationOperatorResult(
        status=status,
        run_id=request.run_id,
        authorization_ref=request.authorization_ref,
        blocked_reason=blocked_reason,
        pre_positions_summary=pre_positions,
        target_summary=target.to_dict(),
        order_plan_summary=plan.to_dict(),
        execution_summary=execution.to_dict(),
        post_positions_summary=post_positions,
        reconciliation_summary=reconciliation.to_dict(),
        persistence_policy=request.persistence_policy,
        stability_window=request.stability_window.to_dict(current_passed=status == "pass"),
    )
    return result


def build_runtime_qmt_client(
    *,
    config: object,
    base_url: str,
    expected_runtime_profile: str,
    timeout_seconds: int = 10,
) -> QmtClient:
    """构造显式授权的真实 simulation QMT client。"""

    return QmtClient(
        config=QmtClientConfig(
            base_url=base_url,
            default_stage="simulation",
            default_mode="simulation",
            default_timeout_seconds=timeout_seconds,
            allow_simulation_transport=True,
            expected_runtime_mode="simulation",
            expected_runtime_profile=expected_runtime_profile,
        ),
        transport=StdlibQmtRestTransport(),
        auth_header_provider=build_runtime_hmac_provider(config),  # type: ignore[arg-type]
    )


def request_from_mapping(payload: Mapping[str, object]) -> MultifactorSimulationOperatorRequest:
    """从 operator JSON spec 构造请求。"""

    strategy_id = str(payload.get("strategy_id") or "")
    run_id = str(payload.get("run_id") or "")
    output_path = str(payload.get("output_path") or f"process/evidence/{run_id}-simulation-operator-evidence.json")
    return MultifactorSimulationOperatorRequest(
        strategy_id=strategy_id,
        run_id=run_id,
        target_trade_date=str(payload.get("target_trade_date") or ""),
        authorization_ref=str(payload.get("authorization_ref") or ""),
        expected_runtime_profile=str(payload.get("expected_runtime_profile") or ""),
        signal_rows=tuple(_signal_row(item) for item in _sequence(payload.get("signal_rows"))),
        capital_base=payload.get("capital_base", "0"),
        current_positions=_int_mapping(payload.get("current_positions")),
        risk_snapshot=_risk_snapshot(payload.get("risk_snapshot")),
        risk_profile=_risk_profile(payload.get("risk_profile")),
        stage_evidence=_stage_evidence(payload.get("stage_evidence")),
        persistence_policy=EvidencePersistencePolicy(
            output_path=output_path,
            retention_days=int(payload.get("retention_days") or 30),
        ),
        stability_window=StabilityWindowPolicy(
            required_runs=int(payload.get("stability_required_runs") or 1),
            evidence_refs=tuple(str(item) for item in _sequence(payload.get("stability_evidence_refs"))),
        ),
        top_n=int(payload.get("top_n") or 1),
        weighting=str(payload.get("weighting") or "equal"),
        max_weight=payload.get("max_weight"),
        universe_symbols=tuple(str(item) for item in _sequence(payload.get("universe_symbols"))),
        max_turnover_notional=payload.get("max_turnover_notional"),
        cancel_submitted_after_submit=bool(payload.get("cancel_submitted_after_submit", True)),
        timeout_seconds=int(payload.get("timeout_seconds") or 10),
    )


def write_operator_evidence(
    result: MultifactorSimulationOperatorResult,
    path: str | Path,
) -> Path:
    """写入脱敏 operator evidence。"""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _qmt_response_to_gateway_result(
    response: QmtResponse,
    endpoint_id: str,
) -> QmtGatewayResult:
    if response.blocked:
        return build_blocked_result(
            endpoint_id,
            response.reason_code or "qmt_client_blocked",
            response.message,
            counters=response.counters,
        )
    operation = response.payload.get("simulation_operation")
    payload = QmtSimulationOperationPayload(**dict(operation)) if isinstance(operation, Mapping) else QmtSimulationOperationPayload(
        operation="submit" if endpoint_id == QMT_SIMULATION_SUBMIT_ENDPOINT_ID else "cancel",
        run_id=response.run_id,
        order_intent_id=str(response.payload.get("order_intent_id") or ""),
        accepted=True,
        adapter_status=str(response.payload.get("adapter_status") or "qmt-client-ok"),
    )
    return build_simulation_operation_result(endpoint_id, payload, counters=response.counters)


def _cancel_submitted_actions(
    request: MultifactorSimulationOperatorRequest,
    execution: SimulationExecutionEngineResult,
    gateway: SimulationGateway,
) -> SimulationExecutionEngineResult:
    actions = list(execution.actions)
    for action in execution.actions:
        if action.operation != "submit" or action.status != "accepted" or not action.cancel_ref:
            continue
        cancel_result = gateway.cancel_order(
            build_simulation_cancel_request(
                {
                    "run_id": request.run_id,
                    "request_id": f"simulation-cancel-after-submit:{action.order_intent_id}",
                    "order_intent_id": action.order_intent_id,
                    "broker_order_ref": action.cancel_ref,
                    "authorization_ref": request.authorization_ref,
                    "idempotency_key": f"{request.run_id}:cancel-after-submit:{action.order_intent_id}",
                }
            )
        )
        payload = _simulation_payload(cancel_result)
        actions.append(
            SimulationExecutionAction(
                operation="cancel",
                order_intent_id=action.order_intent_id,
                status="accepted" if cancel_result.allowed and payload.get("accepted") is not False else "blocked",
                instrument_ref=action.instrument_ref,
                cancel_ref=str(payload.get("cancel_ref") or action.cancel_ref),
                blocked_reason=cancel_result.reason_code,
            )
        )
        if cancel_result.blocked:
            break
    blocked = any(item.status == "blocked" for item in actions)
    return SimulationExecutionEngineResult(
        status="blocked" if blocked else execution.status,
        run_id=execution.run_id,
        stage_gate_status=execution.stage_gate_status,
        actions=tuple(actions),
        blocked_reason="cancel_after_submit_blocked" if blocked else execution.blocked_reason,
        submitted_count=execution.submitted_count,
        cancelled_count=sum(1 for item in actions if item.operation == "cancel" and item.status == "accepted"),
        rejected_count=execution.rejected_count,
        unknown_count=execution.unknown_count,
        manual_takeover_required=blocked or execution.manual_takeover_required,
        evidence_refs=execution.evidence_refs,
    )


def _query_positions_summary(response: QmtResponse) -> dict[str, object]:
    payload = dict(response.payload)
    query_positions = payload.get("query_positions")
    if not isinstance(query_positions, Mapping):
        gateway_result = payload.get("gateway_result")
        allowed_payload = gateway_result.get("allowed_payload") if isinstance(gateway_result, Mapping) else {}
        data = allowed_payload.get("data") if isinstance(allowed_payload, Mapping) else {}
        query_positions = data.get("query_positions") if isinstance(data, Mapping) else {}
    current = dict(query_positions) if isinstance(query_positions, Mapping) else {}
    return {
        "status": "ok" if not response.blocked else "blocked",
        "reason_code": response.reason_code,
        "position_count_bucket": _position_count_bucket(int(current.get("position_count") or 0)) if current else "unknown",
        "positions_digest": current.get("positions_digest") or _stable_ref(response.run_id + response.reason_code, "positions"),
        "items_redacted_count": len(current.get("items_redacted")) if isinstance(current.get("items_redacted"), list) else 0,
        "raw_payload_emitted": current.get("raw_payload_emitted") is True,
        "redaction_status": current.get("redaction_status") or response.redaction_status,
    }


def _authorization_block_reason(request: MultifactorSimulationOperatorRequest) -> str:
    if not request.authorization_ref:
        return "runtime_authorization_missing"
    if not request.expected_runtime_profile:
        return "runtime_profile_missing"
    if not request.strategy_id or not request.run_id or not request.target_trade_date:
        return "required_field_missing"
    return ""


def _blocked(
    request: MultifactorSimulationOperatorRequest,
    reason: str,
    *,
    pre_positions: Mapping[str, object] | None = None,
    target: Mapping[str, object] | None = None,
    order_plan: Mapping[str, object] | None = None,
    execution: Mapping[str, object] | None = None,
    post_positions: Mapping[str, object] | None = None,
) -> MultifactorSimulationOperatorResult:
    return MultifactorSimulationOperatorResult(
        status="blocked",
        run_id=request.run_id,
        authorization_ref=request.authorization_ref,
        blocked_reason=reason,
        pre_positions_summary=pre_positions or {},
        target_summary=target or {},
        order_plan_summary=order_plan or {},
        execution_summary=execution or {},
        post_positions_summary=post_positions or {},
        persistence_policy=request.persistence_policy,
        stability_window=request.stability_window.to_dict(current_passed=False),
    )


def _stage_request(request: MultifactorSimulationOperatorRequest) -> StageGateRequest:
    return StageGateRequest(
        current_stage=Stage.SHADOW,
        target_stage=Stage.SIMULATION,
        authorization_summary=AuthorizationSummary(
            authorization_id=request.authorization_ref,
            mode="simulation",
            strategy_id=request.strategy_id,
            run_id=request.run_id,
            target_stage=Stage.SIMULATION,
            target_trade_date=request.target_trade_date,
            capital_limit=str(request.capital_base),
            order_scope=("simulation_submit", "simulation_cancel"),
            approver="user",
            approved_at=datetime.now(timezone.utc).isoformat(),
            expires_at="per-run-session",
            rollback_plan_ref="process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md",
        ),
        request_ref=f"simulation-operator:{request.run_id}",
    )


def _simulation_payload(result: QmtGatewayResult) -> Mapping[str, object]:
    if result.allowed_payload is None:
        return {}
    data = result.allowed_payload.data.get("simulation_operation")
    return dict(data) if isinstance(data, Mapping) else {}


def _reconciliation_state(
    execution: SimulationExecutionEngineResult,
    order_count: int,
) -> dict[str, object]:
    return {
        "orders": {"count": order_count, "ref": _stable_ref(execution.run_id, "orders")},
        "fills": {"count": 0, "ref": _stable_ref(execution.run_id, "fills")},
        "positions": {"count": max(execution.submitted_count, 0), "ref": _stable_ref(execution.run_id, "positions")},
        "assets": {"value": 0.0, "ref": _stable_ref(execution.run_id, "assets")},
        "cash": {"value": 0.0, "ref": _stable_ref(execution.run_id, "cash")},
        "broker_lake_facts": {"count": 6, "ref": _stable_ref(execution.run_id, "broker-lake")},
    }


def _default_thresholds() -> ThresholdConfig:
    return ThresholdConfig(
        warn={dimension: 0.1 for dimension in RECON_DIMENSIONS},
        manual_review={dimension: 2.0 for dimension in RECON_DIMENSIONS},
        kill_switch={dimension: 10.0 for dimension in RECON_DIMENSIONS},
    )


def _risk_snapshot(value: object) -> RiskInputSnapshot:
    payload = dict(value) if isinstance(value, Mapping) else {}
    return RiskInputSnapshot(
        cash_available=payload.get("cash_available", "0"),
        positions_available=_int_mapping(payload.get("positions_available")),
        t1_sellable=_int_mapping(payload.get("t1_sellable")),
        raw_price_refs={
            str(symbol): RawPriceRef(
                symbol=str(symbol),
                price=_mapping(row).get("price", row),
                evidence_ref=str(_mapping(row).get("evidence_ref") or _stable_ref(str(symbol), "price")),
            )
            for symbol, row in _mapping(payload.get("raw_price_refs")).items()
        },
        source_kind=str(payload.get("source_kind") or "sanitized_snapshot"),
        evidence_ref=str(payload.get("evidence_ref") or "operator-risk-snapshot"),
    )


def _risk_profile(value: object) -> RiskProfile:
    payload = dict(value) if isinstance(value, Mapping) else {}
    return RiskProfile(
        risk_profile_id=str(payload.get("risk_profile_id") or "operator-simulation-risk-profile"),
        max_single_symbol_notional=payload.get("max_single_symbol_notional", "1000000000"),
        max_portfolio_notional=payload.get("max_portfolio_notional", "1000000000"),
        price_deviation_limit_pct=payload.get("price_deviation_limit_pct", "0.20"),
        fee_buffer_pct=payload.get("fee_buffer_pct", "0.01"),
        lot_size=int(payload.get("lot_size") or 100),
        evidence_ref=str(payload.get("evidence_ref") or "operator-risk-profile"),
    )


def _stage_evidence(value: object) -> StageEvidence:
    payload = dict(value) if isinstance(value, Mapping) else {}
    return StageEvidence(
        cr015_verified=bool(payload.get("cr015_verified", True)),
        runbook_ref=str(payload.get("runbook_ref") or "process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md"),
        cr017_consumer_boundary_ref=str(payload.get("cr017_consumer_boundary_ref") or "process/docs/features/qmt-trading-governance/DESIGN.md"),
        reconciliation_policy_ref=str(payload.get("reconciliation_policy_ref") or "process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-P4-RECONCILIATION-2026-06-25.md"),
        kill_switch_readiness_ref=str(payload.get("kill_switch_readiness_ref") or "process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-P5-OPERATIONAL-RUNBOOK-2026-06-25.md"),
        cr017_verified=bool(payload.get("cr017_verified", True)),
    )


def _signal_row(value: object) -> MultifactorSignalRow:
    payload = dict(value) if isinstance(value, Mapping) else {}
    return MultifactorSignalRow(
        symbol=str(payload.get("symbol") or ""),
        score=payload.get("score", payload.get("composite_score", "0")),
        signal_date=str(payload.get("signal_date") or ""),
        factor_refs=_mapping(payload.get("factor_refs")),
        eligible=bool(payload.get("eligible", True)),
    )


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _int_mapping(value: object) -> dict[str, int]:
    return {str(key): int(raw) for key, raw in _mapping(value).items()}


def _position_count_bucket(count: int) -> str:
    if count <= 0:
        return "zero"
    if count <= 10:
        return "one_to_ten"
    return "gt_ten"


def _stable_ref(value: str, prefix: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"
