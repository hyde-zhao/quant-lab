"""CR091 strategy runner 的 adapter 注册与离线分发。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping, Protocol

from engine.order_intent_draft import (
    OrderIntentDraftResult,
    build_order_intent_draft,
    zero_forbidden_operation_counts,
)
from trading.strategy_runner.target_portfolio import (
    TargetPortfolioSnapshot,
    equal_weight_snapshot,
)


MULTIFACTOR_SCHEMA = "multifactor_strategy_admission_package_v1"
LEGACY_SCHEMA = "legacy_strategy_result_v1"
PACKAGE_PAYLOAD_SCHEMA = "cr091-strategy-package-payload-v1"
DELIVERY_TARGET_QMT_TERMINAL_DIRECT = "qmt_terminal_direct"
EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY = "miniqmt_gateway_readonly"
READONLY_EXECUTION_CAPABILITIES = frozenset({"readonly", "health", "capabilities", "query_positions"})
ORDER_WRITE_EXECUTION_CAPABILITIES = frozenset(
    {"submit_order", "cancel_order", "buy", "sell", "order_write", "simulation", "live"}
)
PACKAGE_AUTHORIZATION_FALSE_FLAGS: tuple[str, ...] = (
    "runtime_authorized",
    "nas_operation_authorized",
    "credential_read_authorized",
    "account_query_authorized",
    "trade_write_authorized",
)


CR091_FORBIDDEN_OPERATION_COUNTERS: tuple[str, ...] = (
    "nas_read",
    "nas_write",
    "nas_list",
    "nas_copy",
    "nas_publish",
    "nas_pull",
    "credential_read",
    "env_file_read",
    "qmt_start",
    "miniqmt_start",
    "xtquant_import",
    "gateway_start",
    "gateway_socket_open",
    "account_raw_query",
    "raw_positions_emit",
    "submit_order",
    "cancel_order",
    "simulation",
    "live",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
)


def zero_cr091_operation_counters() -> dict[str, int]:
    return {name: 0 for name in CR091_FORBIDDEN_OPERATION_COUNTERS}


@dataclass(frozen=True, slots=True)
class AdapterResult:
    status: str
    strategy_id: str
    target_portfolio: TargetPortfolioSnapshot | None = None
    order_intents: tuple[OrderIntentDraftResult, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    operation_counters: Mapping[str, int] = field(default_factory=zero_cr091_operation_counters)
    delivery_target_id: str = ""
    execution_adapter_id: str = ""
    execution_adapter_capabilities: tuple[str, ...] = ()
    not_authorization: bool = True

    @property
    def passed(self) -> bool:
        return self.status == "pass" and self.target_portfolio is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "strategy_id": self.strategy_id,
            "target_portfolio": None if self.target_portfolio is None else self.target_portfolio.to_dict(),
            "order_intents": [item.to_dict() for item in self.order_intents],
            "blocked_reasons": list(self.blocked_reasons),
            "operation_counters": dict(self.operation_counters),
            "delivery_target_id": self.delivery_target_id,
            "execution_adapter_id": self.execution_adapter_id,
            "execution_adapter_capabilities": list(self.execution_adapter_capabilities),
            "not_authorization": self.not_authorization,
        }


class StrategyAdapter(Protocol):
    adapter_type: str
    input_schema: str

    def supports(self, payload: Mapping[str, object]) -> bool:
        ...

    def adapt(self, payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
        ...


class AdapterRegistry:
    """按注册顺序分发 adapter；未知输入 fail closed。"""

    def __init__(self, adapters: tuple[StrategyAdapter, ...] | None = None) -> None:
        self._adapters: list[StrategyAdapter] = list(adapters or default_adapters())

    def register(self, adapter: StrategyAdapter) -> None:
        self._adapters.append(adapter)

    def dispatch(self, payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
        for adapter in self._adapters:
            if adapter.supports(payload):
                return adapter.adapt(payload, run_id=run_id)
        return blocked_result("unknown", ("blocked_adapter_contract", "unknown_adapter_type"))


class MultifactorAdmissionAdapter:
    adapter_type = "multifactor_admission"
    input_schema = MULTIFACTOR_SCHEMA

    def supports(self, payload: Mapping[str, object]) -> bool:
        return payload.get("schema_version") == self.input_schema

    def adapt(self, payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
        reasons = common_payload_blocks(payload)
        if not _operation_counts_zero(payload.get("operation_counts")):
            reasons.append("blocked_forbidden_operation_nonzero")
        candidates = [item for item in _as_list(payload.get("strategy_candidates")) if isinstance(item, Mapping)]
        admitted = [
            item
            for item in candidates
            if str(item.get("admission", "")).lower() in {"research_baseline", "watch", "pass"}
        ]
        if not admitted:
            reasons.append("blocked_no_pass_or_watch_candidate")
        if not _has_risk_cost_refs(payload):
            reasons.append("blocked_missing_risk_cost_refs")
        if reasons:
            return blocked_result(self.adapter_type, tuple(reasons))

        candidate = admitted[0]
        strategy_id = str(candidate.get("strategy_id") or f"strategy-{run_id}")
        symbols = _candidate_symbols(payload, candidate)
        if not symbols:
            return blocked_result(self.adapter_type, ("blocked_empty_targets",))
        snapshot = equal_weight_snapshot(
            strategy_id=strategy_id,
            source_run_id=str(payload.get("run_id") or run_id),
            target_trade_date=str(payload.get("target_trade_date") or payload.get("signal_date") or "offline-fixture-date"),
            target_symbols=tuple(symbols),
            score_refs={"source": "multifactor_strategy_scores", "strategy_id": strategy_id},
            risk_cost_refs=_risk_cost_refs(payload, candidate),
            lineage_refs={"input_refs": dict(_as_mapping(payload.get("input_refs")))},
            limitations=("offline_fixture_only", "not_qmt_authorization"),
        )
        return build_pass_result(self.adapter_type, strategy_id, snapshot, run_id=run_id)


class LegacyStrategyResultAdapter:
    adapter_type = "legacy_strategy_result"
    input_schema = LEGACY_SCHEMA

    def supports(self, payload: Mapping[str, object]) -> bool:
        return payload.get("schema_version") in {self.input_schema, "StrategyResult"} or (
            "strategy_name" in payload and "target_symbols" in payload and "scores" in payload
        )

    def adapt(self, payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
        reasons = common_payload_blocks(payload)
        symbols = tuple(str(item) for item in _as_list(payload.get("target_symbols")) if str(item))
        scores = _as_mapping(payload.get("scores"))
        if not symbols:
            reasons.append("blocked_empty_targets")
        if not scores:
            reasons.append("blocked_missing_scores")
        if not payload.get("signal_date"):
            reasons.append("blocked_missing_signal_date")
        if reasons:
            return blocked_result(self.adapter_type, tuple(reasons))
        strategy_id = str(payload.get("strategy_id") or payload.get("strategy_name") or "legacy_strategy")
        snapshot = equal_weight_snapshot(
            strategy_id=strategy_id,
            source_run_id=str(payload.get("run_id") or run_id),
            target_trade_date=str(payload.get("target_trade_date") or payload.get("signal_date")),
            target_symbols=symbols,
            score_refs={"scores": dict(scores)},
            risk_cost_refs={"source": "legacy_strategy_result", "risk_cost_status": "not_provided"},
            lineage_refs={"strategy_result": "offline_fixture"},
            limitations=("offline_fixture_only", "not_qmt_authorization"),
        )
        return build_pass_result(self.adapter_type, strategy_id, snapshot, run_id=run_id)


class StrategyPackageAdapter:
    adapter_type = "strategy_package"
    input_schema = PACKAGE_PAYLOAD_SCHEMA

    def supports(self, payload: Mapping[str, object]) -> bool:
        return payload.get("schema_version") == self.input_schema

    def adapt(self, payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
        reasons = common_payload_blocks(payload)
        if not payload.get("adapter_type"):
            reasons.append("blocked_missing_adapter_type")
        delivery_target_id = str(payload.get("delivery_target_id") or "")
        execution_adapter_id = str(payload.get("execution_adapter_id") or "")
        execution_adapter_capabilities = tuple(str(item) for item in _as_list(payload.get("execution_adapter_capabilities")))
        if delivery_target_id != DELIVERY_TARGET_QMT_TERMINAL_DIRECT:
            reasons.append("blocked_delivery_target_contract")
        if execution_adapter_id != EXECUTION_ADAPTER_MINIQMT_GATEWAY_READONLY:
            reasons.append("blocked_execution_adapter_contract")
        if not execution_adapter_capabilities:
            reasons.append("blocked_execution_adapter_capabilities_missing")
        if any(capability in ORDER_WRITE_EXECUTION_CAPABILITIES for capability in execution_adapter_capabilities):
            reasons.append("blocked_execution_adapter_order_write_capability")
        if any(capability not in READONLY_EXECUTION_CAPABILITIES for capability in execution_adapter_capabilities):
            reasons.append("blocked_execution_adapter_unknown_capability")
        if payload.get("manifest_checksum_verified") is not True:
            reasons.append("blocked_checksum_mismatch")
        if any(payload.get(flag) is not False for flag in PACKAGE_AUTHORIZATION_FALSE_FLAGS):
            reasons.append("blocked_manifest_flags_nonfalse")
        if reasons:
            return _with_execution_boundary(
                blocked_result(self.adapter_type, tuple(reasons)),
                delivery_target_id=delivery_target_id,
                execution_adapter_id=execution_adapter_id,
                execution_adapter_capabilities=execution_adapter_capabilities,
            )
        inner = _as_mapping(payload.get("strategy_payload"))
        if not inner:
            return _with_execution_boundary(
                blocked_result(self.adapter_type, ("blocked_missing_strategy_payload",)),
                delivery_target_id=delivery_target_id,
                execution_adapter_id=execution_adapter_id,
                execution_adapter_capabilities=execution_adapter_capabilities,
            )
        registry = AdapterRegistry((MultifactorAdmissionAdapter(), LegacyStrategyResultAdapter()))
        return _with_execution_boundary(
            registry.dispatch(inner, run_id=run_id),
            delivery_target_id=delivery_target_id,
            execution_adapter_id=execution_adapter_id,
            execution_adapter_capabilities=execution_adapter_capabilities,
        )


def default_adapters() -> tuple[StrategyAdapter, ...]:
    return (MultifactorAdmissionAdapter(), LegacyStrategyResultAdapter(), StrategyPackageAdapter())


def adapt_strategy_payload(payload: Mapping[str, object], *, run_id: str) -> AdapterResult:
    return AdapterRegistry().dispatch(payload, run_id=run_id)


def build_pass_result(
    adapter_type: str,
    strategy_id: str,
    snapshot: TargetPortfolioSnapshot,
    *,
    run_id: str,
) -> AdapterResult:
    order_intents = tuple(
        build_order_intent_draft(
            row,
            {"artifact_id": f"cr091-semantic-diff:{strategy_id}:{row['symbol']}", "lineage": snapshot.lineage_refs},
            {
                "run_id": run_id,
                "source_run_id": snapshot.source_run_id,
                "strategy_id": strategy_id,
                "target_portfolio_id": snapshot.target_portfolio_id,
                "limitations": snapshot.limitations,
                "execution_price_policy": "raw",
                "raw_execution_policy_status": "pass",
                "research_adjustment_policy": "research_only_no_execution_adjustment",
                "cost_config_ref": "cr091-offline-cost-config",
                "data_lineage_ref": snapshot.lineage_refs,
                "operation_counters": zero_forbidden_operation_counts(),
            },
        )
        for row in snapshot.rows()
    )
    failed = [reason for result in order_intents for reason in result.blocked_reasons]
    if failed:
        return blocked_result(adapter_type, tuple(sorted(set(failed))), strategy_id=strategy_id)
    return AdapterResult(
        status="pass",
        strategy_id=strategy_id,
        target_portfolio=snapshot,
        order_intents=order_intents,
        operation_counters=zero_cr091_operation_counters(),
    )


def blocked_result(
    adapter_type: str,
    reasons: tuple[str, ...],
    *,
    strategy_id: str = "",
) -> AdapterResult:
    return AdapterResult(
        status="blocked",
        strategy_id=strategy_id or adapter_type,
        blocked_reasons=tuple(sorted(set(reasons))),
        operation_counters=zero_cr091_operation_counters(),
    )


def _with_execution_boundary(
    result: AdapterResult,
    *,
    delivery_target_id: str,
    execution_adapter_id: str,
    execution_adapter_capabilities: tuple[str, ...],
) -> AdapterResult:
    return replace(
        result,
        delivery_target_id=delivery_target_id,
        execution_adapter_id=execution_adapter_id,
        execution_adapter_capabilities=execution_adapter_capabilities,
    )


def common_payload_blocks(payload: Mapping[str, object]) -> list[str]:
    reasons: list[str] = []
    if payload.get("not_authorization") is not True:
        reasons.append("blocked_not_authorization_missing")
    if payload.get("qmt_allowed") is True:
        reasons.append("blocked_qmt_allowed_true")
    return reasons


def _operation_counts_zero(value: object) -> bool:
    if not isinstance(value, Mapping):
        return True
    return all(int(count or 0) == 0 for count in value.values())


def _has_risk_cost_refs(payload: Mapping[str, object]) -> bool:
    return bool(payload.get("risk_cost_refs") or payload.get("risk_cost_summary") or payload.get("input_refs"))


def _risk_cost_refs(payload: Mapping[str, object], candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "source": "multifactor_risk_cost_summary",
        "strategy_id": candidate.get("strategy_id", ""),
        "refs": dict(_as_mapping(payload.get("risk_cost_refs") or payload.get("input_refs"))),
    }


def _candidate_symbols(payload: Mapping[str, object], candidate: Mapping[str, object]) -> list[str]:
    if isinstance(candidate.get("target_symbols"), list):
        return [str(item) for item in candidate["target_symbols"] if str(item)]
    target_symbols = payload.get("target_symbols")
    if isinstance(target_symbols, list):
        return [str(item) for item in target_symbols if str(item)]
    scores = _as_list(payload.get("strategy_scores"))
    strategy_id = str(candidate.get("strategy_id") or "")
    out: list[str] = []
    for row in scores:
        if isinstance(row, Mapping) and str(row.get("strategy_id") or strategy_id) == strategy_id and row.get("symbol"):
            out.append(str(row["symbol"]))
    return sorted(set(out))


def _as_list(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else []


def _as_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
