"""CR042 broker-neutral adapter 合同。

本模块只定义离线 adapter 合同和 paper fixture adapter，不导入或调用真实
broker、掘金、QMT、网络、账户或凭据接口。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.paper_simulation import (
    PaperBrokerConfig,
    apply_fills_to_ledger,
    simulate_fills,
    zero_forbidden_operation_counts,
)


BROKER_ADAPTER_CAPABILITY_SCHEMA_VERSION = "broker_adapter_capability_v1"
BROKER_CASH_SNAPSHOT_SCHEMA_VERSION = "broker_cash_snapshot_v1"
BROKER_POSITION_SNAPSHOT_SCHEMA_VERSION = "broker_position_snapshot_v1"
BROKER_ORDER_REQUEST_SCHEMA_VERSION = "broker_order_request_v1"
BROKER_FILL_EVENT_SCHEMA_VERSION = "broker_fill_event_v1"
BROKER_ADAPTER_RESULT_SCHEMA_VERSION = "broker_adapter_result_v1"
BROKER_ADAPTER_ERROR_SCHEMA_VERSION = "broker_adapter_error_v1"
CR044_REDACTION_SUMMARY_SCHEMA_VERSION = "cr044_redaction_summary_v1"
CR044_GOLDMINER_ADMISSION_SCHEMA_VERSION = "cr044_goldminer_admission_v1"
CR044_READONLY_MAPPING_SCHEMA_VERSION = "cr044_readonly_mapping_v1"
CR044_RECONCILIATION_EVIDENCE_SCHEMA_VERSION = "cr044_reconciliation_evidence_v1"

PAPER_ADAPTER_KIND = "paper_fixture"
GOLDMINER_STUB_ADAPTER_KIND = "goldminer_stub"

FORBIDDEN_ADAPTER_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            *zero_forbidden_operation_counts().keys(),
            "real_broker_call",
            "real_order_call",
            "real_cancel_call",
            "real_account_query",
            "real_position_query",
            "real_cash_query",
            "credential_read",
            "goldminer_import_or_call",
            "gmtrade_import_or_call",
        )
    )
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
    "broker_order_id",
    "client_order_id",
    "entrust_no",
    "order_id",
    "execution_id",
    "execution_ref",
)


class BrokerAdapterError(Exception):
    """broker-neutral adapter 基础异常。"""


class BrokerAdapterValidationError(BrokerAdapterError):
    """adapter 输入或合同校验失败。"""


class BrokerAdapterResultStatus(str, Enum):
    PASS = "pass"
    BLOCKED = "blocked"


class BrokerAdapterBlockedReason(str, Enum):
    SENSITIVE_MATERIAL_PRESENT = "sensitive_material_present"
    FORBIDDEN_OPERATION_NONZERO = "forbidden_operation_nonzero"
    NON_RAW_EXECUTION_PRICE_POLICY = "non_raw_execution_price_policy"
    UNSUPPORTED_ADAPTER_OPERATION = "unsupported_adapter_operation"
    GOLDMINER_SPIKE_REQUIRED = "goldminer_spike_required"
    GOLDMINER_NOT_AUTHORIZED = "goldminer_not_authorized"
    GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED = "goldminer_readonly_query_not_authorized"
    GOLDMINER_SUBMIT_CANCEL_NOT_AUTHORIZED = "goldminer_submit_cancel_not_authorized"
    GLOBAL_KILL_SWITCH_DISABLED = "global_kill_switch_disabled"
    PER_RUN_AUTHORIZATION_MISSING = "per_run_authorization_missing"
    OPERATION_NOT_WHITELISTED = "operation_not_whitelisted"
    UNKNOWN_BROKER_FIELD = "unknown_broker_field"
    MISMATCH_REQUIRES_MANUAL_REVIEW = "mismatch_requires_manual_review"


class CR044AuthorizationLayer(str, Enum):
    L1_FORMAL_CR_ORCHESTRATION = "L1_formal_cr_orchestration"
    L2_OFFLINE_ENGINEERING_FIXTURE_ONLY = "L2_offline_engineering_fixture_only"
    L3_CREDENTIAL_ACCOUNT_PERMISSION = "L3_credential_account_permission"
    L4_READONLY_QUERY = "L4_readonly_query"
    L5_SUBMIT_CANCEL_RECONCILE_RUNTIME = "L5_submit_cancel_reconcile_runtime"


class CR044GoldminerCapabilityState(str, Enum):
    SDK_STATIC_CANDIDATE = "sdk_static_candidate"
    OFFLINE_DESIGN_READY = "offline_design_ready"
    CREDENTIAL_REQUIRED = "credential_required"
    READONLY_AUTHORIZED_FOR_RUN = "readonly_authorized_for_run"
    SUBMIT_CANCEL_AUTHORIZED_FOR_RUN = "submit_cancel_authorized_for_run"
    BLOCKED_NO_AUTHORIZATION = "blocked_no_authorization"


class CR044ReadonlyMappingStatus(str, Enum):
    STATIC_CANDIDATE = "static_candidate"
    FIXTURE_ONLY = "fixture_only"
    UNKNOWN_BROKER_FIELD = "unknown_broker_field"
    BLOCKED_NO_AUTHORIZATION = "blocked_no_authorization"
    REDACTED_SENSITIVE_FIELD = "redacted_sensitive_field"


class CR044ReconciliationStatus(str, Enum):
    MATCHED_FIXTURE = "matched_fixture"
    BLOCKED_NO_AUTHORIZATION = "blocked_no_authorization"
    UNKNOWN_BROKER_FIELD = "unknown_broker_field"
    MISMATCH_REQUIRES_MANUAL_REVIEW = "mismatch_requires_manual_review"


class CR044DiscrepancyCode(str, Enum):
    FIELD_MISSING = "field_missing"
    FIELD_UNKNOWN = "field_unknown"
    FIXTURE_MISMATCH = "fixture_mismatch"
    OPERATION_COUNT_NONZERO = "operation_count_nonzero"
    SENSITIVE_MATERIAL_PRESENT = "sensitive_material_present"
    RUNTIME_NOT_AUTHORIZED = "runtime_not_authorized"


CR044_AUTHORIZATION_LAYERS: tuple[dict[str, Any], ...] = (
    {
        "layer": CR044AuthorizationLayer.L1_FORMAL_CR_ORCHESTRATION.value,
        "status": "authorized_current_scope",
        "allowed_actions": ("formal_cr_orchestration",),
    },
    {
        "layer": CR044AuthorizationLayer.L2_OFFLINE_ENGINEERING_FIXTURE_ONLY.value,
        "status": "authorized_current_scope",
        "allowed_actions": (
            "offline_design",
            "fixture_only_test",
            "static_artifact_scan",
            "redacted_evidence_build",
        ),
    },
    {
        "layer": CR044AuthorizationLayer.L3_CREDENTIAL_ACCOUNT_PERMISSION.value,
        "status": "not_authorized",
        "allowed_actions": (),
    },
    {
        "layer": CR044AuthorizationLayer.L4_READONLY_QUERY.value,
        "status": "not_authorized",
        "allowed_actions": (),
    },
    {
        "layer": CR044AuthorizationLayer.L5_SUBMIT_CANCEL_RECONCILE_RUNTIME.value,
        "status": "not_authorized",
        "allowed_actions": (),
    },
)

CR044_NOT_AUTHORIZED_ACTIONS = (
    "credential_read",
    "login",
    "connect",
    "account_query",
    "cash_query",
    "position_query",
    "order_query",
    "fill_query",
    "order_submit",
    "order_cancel",
    "simulation_runtime",
    "live_runtime",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
)

CR044_GOLDMINER_CAPABILITY_STATES = tuple(state.value for state in CR044GoldminerCapabilityState)

CR044_GOLDMINER_KILL_SWITCH_STATE: Mapping[str, Any] = {
    "global_hard_switch_enabled": False,
    "per_run_authorization_id": "",
    "operation_whitelist": (),
    "max_real_operation_counts": zero_forbidden_operation_counts(),
}

CR044_GOLDMINER_READONLY_FIELD_MAPPING: tuple[dict[str, Any], ...] = (
    {
        "query_type": "cash_query",
        "internal_field": "cash",
        "broker_candidate_field": "cash",
        "mapping_status": CR044ReadonlyMappingStatus.STATIC_CANDIDATE.value,
        "source": "cr043_static_candidate",
        "confidence": "low_until_runtime_probe",
        "redaction_required": False,
    },
    {
        "query_type": "cash_query",
        "internal_field": "available_cash",
        "broker_candidate_field": "available",
        "mapping_status": CR044ReadonlyMappingStatus.UNKNOWN_BROKER_FIELD.value,
        "source": "cr043_static_candidate",
        "confidence": "unknown_until_l4_authorization",
        "redaction_required": False,
    },
    {
        "query_type": "position_query",
        "internal_field": "symbol",
        "broker_candidate_field": "symbol",
        "mapping_status": CR044ReadonlyMappingStatus.STATIC_CANDIDATE.value,
        "source": "cr043_static_candidate",
        "confidence": "low_until_runtime_probe",
        "redaction_required": False,
    },
    {
        "query_type": "position_query",
        "internal_field": "sellable_qty",
        "broker_candidate_field": "available_volume",
        "mapping_status": CR044ReadonlyMappingStatus.UNKNOWN_BROKER_FIELD.value,
        "source": "cr043_static_candidate",
        "confidence": "unknown_until_l4_authorization",
        "redaction_required": False,
    },
    {
        "query_type": "order_query",
        "internal_field": "adapter_order_ref",
        "broker_candidate_field": "order_id",
        "mapping_status": CR044ReadonlyMappingStatus.REDACTED_SENSITIVE_FIELD.value,
        "source": "cr043_static_candidate",
        "confidence": "sensitive_identifier",
        "redaction_required": True,
    },
    {
        "query_type": "fill_query",
        "internal_field": "adapter_fill_ref",
        "broker_candidate_field": "execution_id",
        "mapping_status": CR044ReadonlyMappingStatus.REDACTED_SENSITIVE_FIELD.value,
        "source": "cr043_static_candidate",
        "confidence": "sensitive_identifier",
        "redaction_required": True,
    },
)


@dataclass(frozen=True, slots=True)
class CR044GoldminerAdmissionDecision:
    action: str
    allowed: bool
    capability_state: str
    blocked_reasons: tuple[str, ...]
    authorization_layer: str = CR044AuthorizationLayer.L2_OFFLINE_ENGINEERING_FIXTURE_ONLY.value
    schema_version: str = CR044_GOLDMINER_ADMISSION_SCHEMA_VERSION
    adapter_kind: str = GOLDMINER_STUB_ADAPTER_KIND
    real_broker_enabled: bool = False
    simulation_ready: bool = False
    live_ready: bool = False
    not_authorization: bool = True
    not_authorized_actions: tuple[str, ...] = CR044_NOT_AUTHORIZED_ACTIONS
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())
    redaction_summary: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_kind": self.adapter_kind,
            "action": self.action,
            "allowed": self.allowed,
            "authorization_layer": self.authorization_layer,
            "capability_state": self.capability_state,
            "blocked_reasons": list(self.blocked_reasons),
            "real_broker_enabled": self.real_broker_enabled,
            "simulation_ready": self.simulation_ready,
            "live_ready": self.live_ready,
            "not_authorization": self.not_authorization,
            "not_authorized_actions": list(self.not_authorized_actions),
            "operation_counts": dict(self.operation_counts),
            "redaction_summary": dict(self.redaction_summary),
        }


@dataclass(frozen=True, slots=True)
class CR044ReconciliationEvidence:
    source: str
    status: str
    blocked_reasons: tuple[str, ...] = ()
    mapping_status_summary: Mapping[str, int] = field(default_factory=dict)
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())
    redaction_summary: Mapping[str, Any] = field(default_factory=dict)
    discrepancies: tuple[str, ...] = ()
    manual_review_required: bool = False
    schema_version: str = CR044_RECONCILIATION_EVIDENCE_SCHEMA_VERSION
    not_authorization: bool = True
    simulation_ready: bool = False
    live_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source": self.source,
            "status": self.status,
            "blocked_reasons": list(self.blocked_reasons),
            "mapping_status_summary": dict(self.mapping_status_summary),
            "operation_counts": dict(self.operation_counts),
            "redaction_summary": dict(self.redaction_summary),
            "discrepancies": list(self.discrepancies),
            "manual_review_required": self.manual_review_required,
            "not_authorization": self.not_authorization,
            "simulation_ready": self.simulation_ready,
            "live_ready": self.live_ready,
        }


@dataclass(frozen=True, slots=True)
class BrokerAdapterViolation:
    code: str
    message: str
    severity: str = "blocker"
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BrokerAdapterValidation:
    passed: bool
    violations: tuple[BrokerAdapterViolation, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

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
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerAdapterCapability:
    adapter_kind: str
    schema_version: str = BROKER_ADAPTER_CAPABILITY_SCHEMA_VERSION
    can_query_cash: bool = True
    can_query_positions: bool = True
    can_submit_order_intents: bool = True
    can_cancel_orders: bool = False
    can_stream_quotes: bool = False
    requires_credentials: bool = False
    real_broker_enabled: bool = False
    simulation_ready: bool = False
    live_ready: bool = False
    supported_execution_price_policies: tuple[str, ...] = ("raw_open",)
    supported_order_types: tuple[str, ...] = ("paper_open_fill",)
    not_authorization: bool = True
    blocked_reasons: tuple[str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_kind": self.adapter_kind,
            "can_query_cash": self.can_query_cash,
            "can_query_positions": self.can_query_positions,
            "can_submit_order_intents": self.can_submit_order_intents,
            "can_cancel_orders": self.can_cancel_orders,
            "can_stream_quotes": self.can_stream_quotes,
            "requires_credentials": self.requires_credentials,
            "real_broker_enabled": self.real_broker_enabled,
            "simulation_ready": self.simulation_ready,
            "live_ready": self.live_ready,
            "supported_execution_price_policies": list(self.supported_execution_price_policies),
            "supported_order_types": list(self.supported_order_types),
            "not_authorization": self.not_authorization,
            "blocked_reasons": list(self.blocked_reasons),
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerCashSnapshot:
    cash: float
    available_cash: float | None = None
    currency: str = "CNY"
    as_of: str = ""
    source: str = PAPER_ADAPTER_KIND
    schema_version: str = BROKER_CASH_SNAPSHOT_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        available = self.cash if self.available_cash is None else self.available_cash
        return {
            "schema_version": self.schema_version,
            "cash": round(float(self.cash), 6),
            "available_cash": round(float(available), 6),
            "currency": self.currency,
            "as_of": self.as_of,
            "source": self.source,
            "not_authorization": self.not_authorization,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerPositionSnapshot:
    symbol: str
    quantity: int = 0
    sellable_qty: int = 0
    average_cost: float = 0.0
    market_value: float = 0.0
    as_of: str = ""
    source: str = PAPER_ADAPTER_KIND
    schema_version: str = BROKER_POSITION_SNAPSHOT_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "quantity": int(self.quantity),
            "sellable_qty": int(self.sellable_qty),
            "average_cost": round(float(self.average_cost), 6),
            "market_value": round(float(self.market_value), 6),
            "as_of": self.as_of,
            "source": self.source,
            "not_authorization": self.not_authorization,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerOrderRequest:
    request_id: str
    symbol: str
    side: str
    quantity: int
    target_trade_date: str
    strategy_id: str = ""
    source_intent_ref: str = ""
    execution_price_policy: str = "raw_open"
    order_type: str = "paper_open_fill"
    schema_version: str = BROKER_ORDER_REQUEST_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "source_intent_ref": self.source_intent_ref,
            "strategy_id": self.strategy_id,
            "target_trade_date": self.target_trade_date,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": int(self.quantity),
            "execution_price_policy": self.execution_price_policy,
            "order_type": self.order_type,
            "not_authorization": self.not_authorization,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerFillEvent:
    adapter_order_ref: str
    symbol: str
    side: str
    requested_qty: int
    filled_qty: int
    status: str
    trade_date: str
    exec_price: float | None
    costs: Mapping[str, float]
    reason_code: str = ""
    schema_version: str = BROKER_FILL_EVENT_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_order_ref": self.adapter_order_ref,
            "symbol": self.symbol,
            "side": self.side,
            "requested_qty": int(self.requested_qty),
            "filled_qty": int(self.filled_qty),
            "unfilled_qty": max(0, int(self.requested_qty) - int(self.filled_qty)),
            "status": self.status,
            "trade_date": self.trade_date,
            "exec_price": self.exec_price,
            "costs": dict(self.costs),
            "reason_code": self.reason_code,
            "not_authorization": self.not_authorization,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerAdapterErrorEvent:
    code: str
    message: str
    source: str = ""
    retryable: bool = False
    schema_version: str = BROKER_ADAPTER_ERROR_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "code": self.code,
            "message": self.message,
            "source": self.source,
            "retryable": self.retryable,
            "not_authorization": self.not_authorization,
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class BrokerAdapterResult:
    adapter_kind: str
    capability: BrokerAdapterCapability
    status: BrokerAdapterResultStatus | str = BrokerAdapterResultStatus.PASS
    order_requests: tuple[BrokerOrderRequest, ...] = ()
    fills: tuple[BrokerFillEvent, ...] = ()
    cash_snapshot: BrokerCashSnapshot | None = None
    positions: tuple[BrokerPositionSnapshot, ...] = ()
    errors: tuple[BrokerAdapterErrorEvent, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    schema_version: str = BROKER_ADAPTER_RESULT_SCHEMA_VERSION
    not_authorization: bool = True
    operation_counts: Mapping[str, int] = field(default_factory=lambda: zero_adapter_operation_counts())

    @property
    def passed(self) -> bool:
        return _status_value(self.status) == BrokerAdapterResultStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_kind": self.adapter_kind,
            "status": _status_value(self.status),
            "passed": self.passed,
            "capability": self.capability.to_dict(),
            "order_requests": [request.to_dict() for request in self.order_requests],
            "fills": [fill.to_dict() for fill in self.fills],
            "cash_snapshot": None if self.cash_snapshot is None else self.cash_snapshot.to_dict(),
            "positions": [position.to_dict() for position in self.positions],
            "errors": [error.to_dict() for error in self.errors],
            "blocked_reasons": list(self.blocked_reasons),
            "not_authorization": self.not_authorization,
            "simulation_ready": False,
            "live_ready": False,
            "operation_counts": dict(self.operation_counts),
        }


class BrokerAdapter:
    """broker-neutral adapter 最小接口。"""

    def capabilities(self) -> BrokerAdapterCapability:
        raise NotImplementedError

    def query_cash(self) -> BrokerCashSnapshot:
        raise NotImplementedError

    def query_positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        raise NotImplementedError

    def submit_order_intents(self, order_intents: Sequence[Mapping[str, Any] | Any]) -> BrokerAdapterResult:
        raise NotImplementedError

    def cancel_order(self, adapter_order_ref: str, reason: str = "") -> BrokerAdapterResult:
        del adapter_order_ref, reason
        return blocked_adapter_result(
            self.capabilities(),
            BrokerAdapterBlockedReason.UNSUPPORTED_ADAPTER_OPERATION.value,
            "cancel_order is not supported by this adapter",
        )


@dataclass(slots=True)
class PaperBrokerAdapter(BrokerAdapter):
    """把 CR041 paper fill engine 暴露为 broker-neutral adapter。"""

    initial_cash: float
    positions: Mapping[str, Any] = field(default_factory=dict)
    market_data: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    config: PaperBrokerConfig | Mapping[str, Any] | None = None
    as_of: str = ""
    adapter_kind: str = PAPER_ADAPTER_KIND

    def capabilities(self) -> BrokerAdapterCapability:
        return BrokerAdapterCapability(adapter_kind=self.adapter_kind)

    def query_cash(self) -> BrokerCashSnapshot:
        return BrokerCashSnapshot(cash=float(self.initial_cash), as_of=self.as_of, source=self.adapter_kind)

    def query_positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        return tuple(
            _position_snapshot_from_mapping(symbol, value, as_of=self.as_of, source=self.adapter_kind)
            for symbol, value in sorted(self.positions.items())
        )

    def submit_order_intents(self, order_intents: Sequence[Mapping[str, Any] | Any]) -> BrokerAdapterResult:
        validation = validate_order_intent_batch(order_intents)
        capability = self.capabilities()
        if not validation.passed:
            return BrokerAdapterResult(
                adapter_kind=self.adapter_kind,
                capability=capability,
                status=BrokerAdapterResultStatus.BLOCKED,
                blocked_reasons=validation.blocked_reasons,
                errors=tuple(
                    normalize_adapter_error(violation.code, violation.message, source=violation.field)
                    for violation in validation.violations
                ),
                operation_counts=validation.operation_counts,
            )
        raw_fills = simulate_fills(
            order_intents,
            self.market_data,
            self.config,
            cash_snapshot={"cash": self.initial_cash},
            position_snapshot=self.positions,
        )
        ledger = apply_fills_to_ledger(
            {"cash": self.initial_cash, "positions": self.positions},
            raw_fills,
            self.market_data,
        )
        fill_events = tuple(
            broker_fill_event_from_paper_fill(fill, index=index)
            for index, fill in enumerate(raw_fills)
        )
        order_requests = tuple(
            broker_order_request_from_intent(intent, index=index)
            for index, intent in enumerate(order_intents)
        )
        final_state = ledger.final_state.to_dict()
        cash_snapshot = BrokerCashSnapshot(
            cash=float(final_state["cash"]),
            as_of=self.as_of or _last_trade_date(self.market_data),
            source=self.adapter_kind,
        )
        position_rows = {
            str(row.get("symbol", "")): row
            for row in ledger.positions
            if isinstance(row, Mapping)
        }
        positions = tuple(
            _position_snapshot_from_mapping(
                symbol,
                value,
                as_of=self.as_of or _last_trade_date(self.market_data),
                source=self.adapter_kind,
                market_value=float(position_rows.get(symbol, {}).get("market_value", 0.0) or 0.0),
            )
            for symbol, value in sorted(final_state["positions"].items())
        )
        status = BrokerAdapterResultStatus.PASS if ledger.status == "pass" else BrokerAdapterResultStatus.BLOCKED
        return BrokerAdapterResult(
            adapter_kind=self.adapter_kind,
            capability=capability,
            status=status,
            order_requests=order_requests,
            fills=fill_events,
            cash_snapshot=cash_snapshot,
            positions=positions,
            blocked_reasons=tuple(ledger.blocked_reasons),
        )


def cr044_authorization_layers() -> tuple[dict[str, Any], ...]:
    return tuple(dict(layer) for layer in CR044_AUTHORIZATION_LAYERS)


def cr044_not_authorized_actions() -> tuple[str, ...]:
    return tuple(CR044_NOT_AUTHORIZED_ACTIONS)


def detect_sensitive_field_paths(payload: Mapping[str, Any] | Sequence[Any] | Any) -> tuple[str, ...]:
    return tuple(sorted(_sensitive_fields(payload)))


def redact_sensitive_payload(payload: Mapping[str, Any] | Sequence[Any] | Any) -> dict[str, Any]:
    sensitive_paths = detect_sensitive_field_paths(payload)
    return {
        "schema_version": CR044_REDACTION_SUMMARY_SCHEMA_VERSION,
        "status": "redacted" if sensitive_paths else "clean",
        "redacted_count": len(sensitive_paths),
        "fields": [
            {
                "field_path": field_path,
                "rule_id": "sensitive_field_name",
                "present": True,
                "value": "REDACTED",
            }
            for field_path in sensitive_paths
        ],
    }


def goldminer_readonly_candidate_mapping(query_type: str = "") -> tuple[dict[str, Any], ...]:
    rows = CR044_GOLDMINER_READONLY_FIELD_MAPPING
    if query_type:
        rows = tuple(row for row in rows if row["query_type"] == query_type)
    return tuple(
        {
            "schema_version": CR044_READONLY_MAPPING_SCHEMA_VERSION,
            **dict(row),
        }
        for row in rows
    )


def evaluate_goldminer_admission(
    action: str,
    *,
    payload: Mapping[str, Any] | Sequence[Any] | Any | None = None,
    operation_counts: Mapping[str, Any] | None = None,
    authorization_layer: str = CR044AuthorizationLayer.L2_OFFLINE_ENGINEERING_FIXTURE_ONLY.value,
    kill_switch_state: Mapping[str, Any] | None = None,
) -> CR044GoldminerAdmissionDecision:
    action_value = str(action)
    counts = _normalise_operation_counts(operation_counts or {})
    redaction_summary = redact_sensitive_payload({} if payload is None else payload)
    blocked_reasons: list[str] = []

    if action_value in CR044_NOT_AUTHORIZED_ACTIONS:
        blocked_reasons.append(f"{action_value}_not_authorized")
    if str(authorization_layer) not in {
        CR044AuthorizationLayer.L1_FORMAL_CR_ORCHESTRATION.value,
        CR044AuthorizationLayer.L2_OFFLINE_ENGINEERING_FIXTURE_ONLY.value,
    }:
        blocked_reasons.append(BrokerAdapterBlockedReason.GOLDMINER_NOT_AUTHORIZED.value)
    if redaction_summary["redacted_count"]:
        blocked_reasons.append(BrokerAdapterBlockedReason.SENSITIVE_MATERIAL_PRESENT.value)
    if any(int(value) != 0 for value in counts.values()):
        blocked_reasons.append(BrokerAdapterBlockedReason.FORBIDDEN_OPERATION_NONZERO.value)

    if action_value in {"order_submit", "order_cancel"}:
        switch = dict(CR044_GOLDMINER_KILL_SWITCH_STATE)
        if kill_switch_state:
            switch.update(dict(kill_switch_state))
        if not bool(switch.get("global_hard_switch_enabled", False)):
            blocked_reasons.append(BrokerAdapterBlockedReason.GLOBAL_KILL_SWITCH_DISABLED.value)
        if not str(switch.get("per_run_authorization_id", "")):
            blocked_reasons.append(BrokerAdapterBlockedReason.PER_RUN_AUTHORIZATION_MISSING.value)
        whitelist = tuple(str(item) for item in switch.get("operation_whitelist", ()))
        if action_value not in whitelist:
            blocked_reasons.append(BrokerAdapterBlockedReason.OPERATION_NOT_WHITELISTED.value)

    if not blocked_reasons:
        blocked_reasons.append(BrokerAdapterBlockedReason.GOLDMINER_NOT_AUTHORIZED.value)

    return CR044GoldminerAdmissionDecision(
        action=action_value,
        allowed=False,
        authorization_layer=str(authorization_layer),
        capability_state=CR044GoldminerCapabilityState.BLOCKED_NO_AUTHORIZATION.value,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        operation_counts=counts,
        redaction_summary=redaction_summary,
    )


def blocked_goldminer_result(
    action: str,
    reason: str = BrokerAdapterBlockedReason.GOLDMINER_NOT_AUTHORIZED.value,
) -> BrokerAdapterResult:
    del action
    return blocked_adapter_result(
        GoldminerStubBrokerAdapter().capabilities(),
        reason,
        "Goldminer runtime operation is not authorized in CR044 L2 fixture-only scope",
    )


def build_goldminer_reconciliation_evidence(
    result: BrokerAdapterResult | Mapping[str, Any] | None = None,
    *,
    mapping: Sequence[Mapping[str, Any]] | None = None,
    payload: Mapping[str, Any] | Sequence[Any] | Any | None = None,
    discrepancies: Sequence[str] = (),
) -> CR044ReconciliationEvidence:
    result_payload = {} if result is None else _json_mapping(result)
    mapping_rows = tuple(mapping) if mapping is not None else goldminer_readonly_candidate_mapping()
    counts = _normalise_operation_counts(result_payload.get("operation_counts", {}))
    redaction_summary = redact_sensitive_payload({} if payload is None else payload)
    blocked_reasons = tuple(str(item) for item in result_payload.get("blocked_reasons", ()))

    mapping_status_summary: dict[str, int] = {}
    for row in mapping_rows:
        status = str(row.get("mapping_status", CR044ReadonlyMappingStatus.UNKNOWN_BROKER_FIELD.value))
        mapping_status_summary[status] = mapping_status_summary.get(status, 0) + 1

    evidence_discrepancies = list(str(item) for item in discrepancies)
    if mapping_status_summary.get(CR044ReadonlyMappingStatus.UNKNOWN_BROKER_FIELD.value, 0):
        evidence_discrepancies.append(CR044DiscrepancyCode.FIELD_UNKNOWN.value)
    if redaction_summary["redacted_count"]:
        evidence_discrepancies.append(CR044DiscrepancyCode.SENSITIVE_MATERIAL_PRESENT.value)
    if any(int(value) != 0 for value in counts.values()):
        evidence_discrepancies.append(CR044DiscrepancyCode.OPERATION_COUNT_NONZERO.value)

    if blocked_reasons:
        status = CR044ReconciliationStatus.BLOCKED_NO_AUTHORIZATION.value
        evidence_discrepancies.append(CR044DiscrepancyCode.RUNTIME_NOT_AUTHORIZED.value)
    elif evidence_discrepancies:
        status = CR044ReconciliationStatus.UNKNOWN_BROKER_FIELD.value
    else:
        status = CR044ReconciliationStatus.MATCHED_FIXTURE.value

    manual_review_required = bool(evidence_discrepancies)
    if CR044DiscrepancyCode.FIXTURE_MISMATCH.value in evidence_discrepancies:
        status = CR044ReconciliationStatus.MISMATCH_REQUIRES_MANUAL_REVIEW.value
        manual_review_required = True

    return CR044ReconciliationEvidence(
        source="blocked_goldminer_stub" if blocked_reasons else "fixture_only",
        status=status,
        blocked_reasons=blocked_reasons,
        mapping_status_summary=mapping_status_summary,
        operation_counts=counts,
        redaction_summary=redaction_summary,
        discrepancies=tuple(dict.fromkeys(evidence_discrepancies)),
        manual_review_required=manual_review_required,
    )


class GoldminerStubBrokerAdapter(BrokerAdapter):
    """掘金 fixture/stub；CR044 下继续 blocked-first，不触发真实 runtime。"""

    def capabilities(self) -> BrokerAdapterCapability:
        return BrokerAdapterCapability(
            adapter_kind=GOLDMINER_STUB_ADAPTER_KIND,
            can_query_cash=False,
            can_query_positions=False,
            can_submit_order_intents=False,
            can_cancel_orders=False,
            supported_execution_price_policies=(),
            supported_order_types=(),
            blocked_reasons=(BrokerAdapterBlockedReason.GOLDMINER_SPIKE_REQUIRED.value,),
        )

    def cr044_admission_state(self, action: str = "goldminer_capability") -> CR044GoldminerAdmissionDecision:
        return evaluate_goldminer_admission(action)

    def cr044_reconciliation_evidence(self) -> CR044ReconciliationEvidence:
        return build_goldminer_reconciliation_evidence(self.submit_order_intents(()))

    def query_cash(self) -> BrokerCashSnapshot:
        raise BrokerAdapterValidationError(BrokerAdapterBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED.value)

    def query_positions(self) -> tuple[BrokerPositionSnapshot, ...]:
        raise BrokerAdapterValidationError(BrokerAdapterBlockedReason.GOLDMINER_READONLY_QUERY_NOT_AUTHORIZED.value)

    def submit_order_intents(self, order_intents: Sequence[Mapping[str, Any] | Any]) -> BrokerAdapterResult:
        del order_intents
        return blocked_adapter_result(
            self.capabilities(),
            BrokerAdapterBlockedReason.GOLDMINER_SPIKE_REQUIRED.value,
            "Goldminer adapter requires CR043 Spike before any runtime operation",
        )

    def cancel_order(self, adapter_order_ref: str, reason: str = "") -> BrokerAdapterResult:
        del adapter_order_ref, reason
        return blocked_adapter_result(
            self.capabilities(),
            BrokerAdapterBlockedReason.GOLDMINER_SUBMIT_CANCEL_NOT_AUTHORIZED.value,
            "Goldminer cancel is not authorized in CR044 L2 fixture-only scope",
        )


def zero_adapter_operation_counts() -> dict[str, int]:
    return {name: 0 for name in FORBIDDEN_ADAPTER_OPERATION_COUNTERS}


def validate_order_intent_batch(order_intents: Sequence[Mapping[str, Any] | Any]) -> BrokerAdapterValidation:
    violations: list[BrokerAdapterViolation] = []
    operation_counts = zero_adapter_operation_counts()
    for index, intent in enumerate(order_intents):
        payload = _to_mapping(intent)
        for field_name in sorted(_sensitive_fields(payload)):
            violations.append(
                BrokerAdapterViolation(
                    code=BrokerAdapterBlockedReason.SENSITIVE_MATERIAL_PRESENT.value,
                    message=f"sensitive field present: {field_name}",
                    field=f"order_intents[{index}].{field_name}",
                )
            )
        counts = _normalise_operation_counts(
            payload.get("operation_counts", payload.get("operation_counters", {}))
        )
        for key, value in counts.items():
            operation_counts[key] = max(int(operation_counts.get(key, 0)), int(value))
            if int(value) != 0:
                violations.append(
                    BrokerAdapterViolation(
                        code=BrokerAdapterBlockedReason.FORBIDDEN_OPERATION_NONZERO.value,
                        message=f"{key} count must be zero",
                        field=f"order_intents[{index}].operation_counts.{key}",
                    )
                )
        policy = str(payload.get("execution_price_policy", "raw_open"))
        if policy not in {"", "raw_open"}:
            violations.append(
                BrokerAdapterViolation(
                    code=BrokerAdapterBlockedReason.NON_RAW_EXECUTION_PRICE_POLICY.value,
                    message=f"unsupported execution price policy: {policy}",
                    field=f"order_intents[{index}].execution_price_policy",
                )
            )
    return BrokerAdapterValidation(
        passed=not violations,
        violations=tuple(violations),
        operation_counts=operation_counts,
    )


def broker_order_request_from_intent(intent: Mapping[str, Any] | Any, index: int = 0) -> BrokerOrderRequest:
    payload = _to_mapping(intent)
    symbol = str(payload.get("symbol", ""))
    return BrokerOrderRequest(
        request_id=str(payload.get("request_id") or payload.get("intent_id") or f"adapter-request-{index:06d}"),
        source_intent_ref=str(payload.get("source_row_id") or payload.get("intent_id") or index),
        strategy_id=str(payload.get("strategy_id", "")),
        target_trade_date=str(payload.get("target_trade_date", "")),
        symbol=symbol,
        side=str(payload.get("side", "")),
        quantity=int(float(payload.get("target_qty", payload.get("quantity", payload.get("qty", 0))) or 0)),
        execution_price_policy=str(payload.get("execution_price_policy", "raw_open")),
    )


def broker_fill_event_from_paper_fill(fill: Mapping[str, Any] | Any, index: int = 0) -> BrokerFillEvent:
    payload = _to_mapping(fill)
    return BrokerFillEvent(
        adapter_order_ref=str(payload.get("adapter_order_ref") or f"paper-fill-{index:06d}"),
        symbol=str(payload.get("symbol", "")),
        side=str(payload.get("side", "")),
        requested_qty=int(float(payload.get("requested_qty", 0) or 0)),
        filled_qty=int(float(payload.get("filled_qty", 0) or 0)),
        status=str(payload.get("status", "")),
        trade_date=str(payload.get("trade_date", "")),
        exec_price=_optional_float(payload.get("exec_price")),
        costs=_float_mapping(payload.get("costs", {})),
        reason_code=str(payload.get("reason_code", payload.get("reason", ""))),
    )


def normalize_adapter_error(
    code: str | BrokerAdapterBlockedReason,
    message: str = "",
    *,
    source: str = "",
    retryable: bool = False,
) -> BrokerAdapterErrorEvent:
    code_value = code.value if isinstance(code, BrokerAdapterBlockedReason) else str(code)
    return BrokerAdapterErrorEvent(
        code=code_value,
        message=message or code_value,
        source=source,
        retryable=retryable,
    )


def blocked_adapter_result(
    capability: BrokerAdapterCapability,
    code: str,
    message: str,
) -> BrokerAdapterResult:
    error = normalize_adapter_error(code, message, source=capability.adapter_kind)
    return BrokerAdapterResult(
        adapter_kind=capability.adapter_kind,
        capability=capability,
        status=BrokerAdapterResultStatus.BLOCKED,
        errors=(error,),
        blocked_reasons=(code,),
    )


def _position_snapshot_from_mapping(
    symbol: str,
    value: Mapping[str, Any] | Any,
    *,
    as_of: str,
    source: str,
    market_value: float = 0.0,
) -> BrokerPositionSnapshot:
    payload = _to_mapping(value)
    return BrokerPositionSnapshot(
        symbol=str(payload.get("symbol", symbol)),
        quantity=int(float(payload.get("quantity", payload.get("qty", 0)) or 0)),
        sellable_qty=int(float(payload.get("sellable_qty", payload.get("quantity", payload.get("qty", 0))) or 0)),
        average_cost=float(payload.get("average_cost", 0.0) or 0.0),
        market_value=market_value,
        as_of=as_of,
        source=source,
    )


def _normalise_operation_counts(raw: Any) -> dict[str, int]:
    counts = zero_adapter_operation_counts()
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            try:
                counts[str(key)] = int(value)
            except (TypeError, ValueError):
                counts[str(key)] = 1
    return counts


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


def _to_mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        mapped = to_dict()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise BrokerAdapterValidationError(f"unsupported mapping value: {type(value).__name__}")


def _json_mapping(value: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        mapped = to_dict()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    return {}


def _float_mapping(raw: Any) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    result: dict[str, float] = {}
    for key, value in raw.items():
        try:
            result[str(key)] = round(float(value), 6)
        except (TypeError, ValueError):
            result[str(key)] = 0.0
    return result


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _status_value(status: BrokerAdapterResultStatus | str) -> str:
    return status.value if isinstance(status, BrokerAdapterResultStatus) else str(status)


def _last_trade_date(market_data: Sequence[Mapping[str, Any]]) -> str:
    trade_dates = sorted(str(row.get("trade_date", "")) for row in market_data if row.get("trade_date"))
    return trade_dates[-1] if trade_dates else ""
