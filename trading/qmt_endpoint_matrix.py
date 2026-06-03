"""CR019-S06 的完整 QMT endpoint matrix 离线合同。

本模块只冻结 endpoint 元数据、门控输入和默认 blocked case，
不读取环境、不启动 gateway、不调用 QMT / MiniQMT / XtQuant。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from trading.qmt_gateway_contracts import QmtBlockedReason


QMT_ENDPOINT_MATRIX_SCHEMA_VERSION = "cr019-s06-qmt-endpoint-matrix-v1"

HLD_ENDPOINT_CATEGORIES: tuple[str, ...] = (
    "health / heartbeat",
    "capabilities",
    "intent validate",
    "dry-run / mock",
    "market query",
    "account snapshot",
    "positions",
    "orders / trades",
    "simulation submit",
    "simulation cancel",
    "live-readonly",
    "live submit / cancel",
    "reconciliation",
    "kill-switch",
)


class QmtEndpointCategory(str, Enum):
    """C/S 侧共享的 endpoint 类别。"""

    HEALTH = "health"
    CAPABILITIES = "capabilities"
    VALIDATE_INTENT = "validate_intent"
    DRY_RUN = "dry_run"
    MARKET_QUERY = "market_query"
    ACCOUNT_QUERY = "account_query"
    POSITIONS = "positions"
    ORDERS = "orders"
    TRADES = "trades"
    SIMULATION_SUBMIT = "simulation_submit"
    SIMULATION_CANCEL = "simulation_cancel"
    LIVE_READONLY = "live_readonly"
    LIVE_SUBMIT = "live_submit"
    LIVE_CANCEL = "live_cancel"
    RECONCILIATION = "reconciliation"
    KILL_SWITCH = "kill_switch"


class QmtEndpointVisibility(str, Enum):
    """Endpoint 默认可见性；可见不等于操作授权。"""

    VISIBLE = "visible"
    LATER_GATED = "later_gated"


class QmtRealOperationKind(str, Enum):
    """Endpoint 若被真实转发时的操作类别。"""

    NONE = "none"
    MARKET_QUERY = "market_query"
    ACCOUNT_QUERY = "account_query"
    ORDER_READ = "order_read"
    ORDER_SUBMIT = "order_submit"
    ORDER_CANCEL = "order_cancel"
    RECONCILIATION = "reconciliation"
    KILL_SWITCH = "kill_switch"


@dataclass(frozen=True, slots=True)
class QmtEndpointBlockedCase:
    """每类 endpoint 至少一个 typed blocked result case。"""

    reason: QmtBlockedReason
    message: str
    detail_code: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "reason": self.reason.value,
            "message": self.message,
            "detail_code": self.detail_code,
        }


@dataclass(frozen=True, slots=True)
class QmtEndpointSpec:
    """完整 endpoint spec；client 与 gateway 只能消费该矩阵。"""

    endpoint_id: str
    category: QmtEndpointCategory
    hld_category: str
    method: str
    path: str
    client_method: str
    required_scope: str
    gate_inputs: tuple[str, ...]
    real_operation_kind: QmtRealOperationKind
    default_visibility: QmtEndpointVisibility
    blocked_reason: QmtBlockedReason
    blocked_cases: tuple[QmtEndpointBlockedCase, ...]
    schema_version: str = QMT_ENDPOINT_MATRIX_SCHEMA_VERSION

    @property
    def later_gated(self) -> bool:
        return self.default_visibility is QmtEndpointVisibility.LATER_GATED

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "endpoint_id": self.endpoint_id,
            "category": self.category.value,
            "hld_category": self.hld_category,
            "method": self.method,
            "path": self.path,
            "client_method": self.client_method,
            "required_scope": self.required_scope,
            "gate_inputs": list(self.gate_inputs),
            "real_operation_kind": self.real_operation_kind.value,
            "default_visibility": self.default_visibility.value,
            "blocked_reason": self.blocked_reason.value,
            "blocked_cases": [case.to_dict() for case in self.blocked_cases],
        }


_NO_REAL_QMT = ("no_real_qmt_operation",)
_AUTH_SCOPE = ("auth_scope",)
_RUN_GATE = (
    "run_mode",
    "stage",
    "risk",
    "kill_switch",
    "authorization",
    "raw_policy",
)


QMT_ENDPOINT_SPECS: tuple[QmtEndpointSpec, ...] = (
    QmtEndpointSpec(
        endpoint_id="health",
        category=QmtEndpointCategory.HEALTH,
        hld_category="health / heartbeat",
        method="GET",
        path="/qmt/health",
        client_method="health",
        required_scope="qmt:health",
        gate_inputs=_NO_REAL_QMT,
        real_operation_kind=QmtRealOperationKind.NONE,
        default_visibility=QmtEndpointVisibility.VISIBLE,
        blocked_reason=QmtBlockedReason.TRANSPORT_UNAVAILABLE,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.TRANSPORT_UNAVAILABLE,
                "gateway heartbeat unavailable; no QMT operation is attempted",
                "heartbeat_unavailable",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="capabilities",
        category=QmtEndpointCategory.CAPABILITIES,
        hld_category="capabilities",
        method="GET",
        path="/qmt/capabilities",
        client_method="capabilities",
        required_scope="qmt:capabilities",
        gate_inputs=_NO_REAL_QMT,
        real_operation_kind=QmtRealOperationKind.NONE,
        default_visibility=QmtEndpointVisibility.VISIBLE,
        blocked_reason=QmtBlockedReason.TRANSPORT_UNAVAILABLE,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.TRANSPORT_UNAVAILABLE,
                "capability visibility is available as contract data only",
                "capabilities_contract_only",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="validate_intent",
        category=QmtEndpointCategory.VALIDATE_INTENT,
        hld_category="intent validate",
        method="POST",
        path="/qmt/intents/validate",
        client_method="validate_intent",
        required_scope="qmt:intent:validate",
        gate_inputs=("schema", "raw_policy") + _NO_REAL_QMT,
        real_operation_kind=QmtRealOperationKind.NONE,
        default_visibility=QmtEndpointVisibility.VISIBLE,
        blocked_reason=QmtBlockedReason.VALIDATION_BLOCKED,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.VALIDATION_BLOCKED,
                "intent schema or raw execution policy is invalid",
                "intent_validation_failed",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="dry_run",
        category=QmtEndpointCategory.DRY_RUN,
        hld_category="dry-run / mock",
        method="POST",
        path="/qmt/intents/dry-run",
        client_method="dry_run",
        required_scope="qmt:intent:dry_run",
        gate_inputs=("adapter_mode", "raw_policy") + _NO_REAL_QMT,
        real_operation_kind=QmtRealOperationKind.NONE,
        default_visibility=QmtEndpointVisibility.VISIBLE,
        blocked_reason=QmtBlockedReason.RAW_POLICY_BLOCKED,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.RAW_POLICY_BLOCKED,
                "dry-run request is blocked by raw execution policy",
                "dry_run_policy_blocked",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="query_market",
        category=QmtEndpointCategory.MARKET_QUERY,
        hld_category="market query",
        method="POST",
        path="/qmt/market/query",
        client_method="query_market",
        required_scope="qmt:market:read",
        gate_inputs=("source_policy", "no_research_lake_write") + _AUTH_SCOPE,
        real_operation_kind=QmtRealOperationKind.MARKET_QUERY,
        default_visibility=QmtEndpointVisibility.VISIBLE,
        blocked_reason=QmtBlockedReason.TRANSPORT_UNAVAILABLE,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.TRANSPORT_UNAVAILABLE,
                "market query transport is unavailable in offline contract mode",
                "market_transport_unavailable",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="query_account",
        category=QmtEndpointCategory.ACCOUNT_QUERY,
        hld_category="account snapshot",
        method="POST",
        path="/qmt/account/snapshot",
        client_method="query_account",
        required_scope="qmt:account:read",
        gate_inputs=("redaction",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ACCOUNT_QUERY,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "account snapshot requires live-readonly stage and per-run authorization",
                "account_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="query_positions",
        category=QmtEndpointCategory.POSITIONS,
        hld_category="positions",
        method="POST",
        path="/qmt/account/positions",
        client_method="query_positions",
        required_scope="qmt:positions:read",
        gate_inputs=("redaction",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ACCOUNT_QUERY,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "position query requires authorization and redaction gate",
                "positions_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="query_orders",
        category=QmtEndpointCategory.ORDERS,
        hld_category="orders / trades",
        method="POST",
        path="/qmt/orders/query",
        client_method="query_orders",
        required_scope="qmt:orders:read",
        gate_inputs=("reconciliation_context",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_READ,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "order query requires reconciliation context and authorization",
                "orders_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="query_trades",
        category=QmtEndpointCategory.TRADES,
        hld_category="orders / trades",
        method="POST",
        path="/qmt/trades/query",
        client_method="query_trades",
        required_scope="qmt:trades:read",
        gate_inputs=("reconciliation_context",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_READ,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "trade query requires reconciliation context and authorization",
                "trades_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="submit_simulation",
        category=QmtEndpointCategory.SIMULATION_SUBMIT,
        hld_category="simulation submit",
        method="POST",
        path="/qmt/simulation/orders",
        client_method="submit_simulation",
        required_scope="qmt:simulation:submit",
        gate_inputs=_AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_SUBMIT,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "simulation order submit requires stage, risk, kill-switch and authorization gates",
                "simulation_submit_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="cancel_simulation",
        category=QmtEndpointCategory.SIMULATION_CANCEL,
        hld_category="simulation cancel",
        method="POST",
        path="/qmt/simulation/orders/cancel",
        client_method="cancel_simulation",
        required_scope="qmt:simulation:cancel",
        gate_inputs=("cancel_policy",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_CANCEL,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "simulation cancel requires cancel policy and authorization",
                "simulation_cancel_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="live_readonly_snapshot",
        category=QmtEndpointCategory.LIVE_READONLY,
        hld_category="live-readonly",
        method="POST",
        path="/qmt/live/readonly/snapshot",
        client_method="live_readonly_snapshot",
        required_scope="qmt:live:readonly",
        gate_inputs=("redaction",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ACCOUNT_QUERY,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "live-readonly snapshot requires stage and per-run authorization",
                "live_readonly_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="submit_live",
        category=QmtEndpointCategory.LIVE_SUBMIT,
        hld_category="live submit / cancel",
        method="POST",
        path="/qmt/live/orders",
        client_method="submit_live",
        required_scope="qmt:live:submit",
        gate_inputs=_AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_SUBMIT,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "live order submit requires small-live or scale-up gates and authorization",
                "live_submit_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="cancel_live",
        category=QmtEndpointCategory.LIVE_CANCEL,
        hld_category="live submit / cancel",
        method="POST",
        path="/qmt/live/orders/cancel",
        client_method="cancel_live",
        required_scope="qmt:live:cancel",
        gate_inputs=("cancel_policy",) + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.ORDER_CANCEL,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "live order cancel requires cancel policy and authorization",
                "live_cancel_authorization_missing",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="reconcile",
        category=QmtEndpointCategory.RECONCILIATION,
        hld_category="reconciliation",
        method="POST",
        path="/qmt/reconciliation",
        client_method="reconcile",
        required_scope="qmt:reconciliation",
        gate_inputs=("redaction", "broker_lake_write_forbidden") + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.RECONCILIATION,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.BROKER_LAKE_WRITE_FORBIDDEN,
                "reconciliation contract cannot write broker lake in this Story",
                "broker_lake_write_forbidden",
            ),
        ),
    ),
    QmtEndpointSpec(
        endpoint_id="kill_switch",
        category=QmtEndpointCategory.KILL_SWITCH,
        hld_category="kill-switch",
        method="POST",
        path="/qmt/kill-switch",
        client_method="kill_switch",
        required_scope="qmt:kill_switch",
        gate_inputs=("operator_authorization", "kill_switch_policy") + _AUTH_SCOPE + _RUN_GATE,
        real_operation_kind=QmtRealOperationKind.KILL_SWITCH,
        default_visibility=QmtEndpointVisibility.LATER_GATED,
        blocked_reason=QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
        blocked_cases=(
            QmtEndpointBlockedCase(
                QmtBlockedReason.PER_RUN_AUTHORIZATION_MISSING,
                "kill-switch endpoint requires authorized operator evidence",
                "kill_switch_authorization_missing",
            ),
        ),
    ),
)

_SPEC_BY_ENDPOINT_ID = {spec.endpoint_id: spec for spec in QMT_ENDPOINT_SPECS}
_SPEC_BY_CATEGORY = {spec.category: spec for spec in QMT_ENDPOINT_SPECS}

LATER_GATED_ENDPOINTS = frozenset(
    spec.category for spec in QMT_ENDPOINT_SPECS if spec.later_gated
)
ACCOUNT_LIKE_ENDPOINTS = frozenset(
    {
        QmtEndpointCategory.ACCOUNT_QUERY,
        QmtEndpointCategory.POSITIONS,
        QmtEndpointCategory.ORDERS,
        QmtEndpointCategory.TRADES,
        QmtEndpointCategory.LIVE_READONLY,
    }
)
REAL_OPERATION_ENDPOINTS = frozenset(
    spec.category
    for spec in QMT_ENDPOINT_SPECS
    if spec.real_operation_kind
    in {
        QmtRealOperationKind.ORDER_SUBMIT,
        QmtRealOperationKind.ORDER_CANCEL,
    }
)


def iter_endpoint_specs() -> tuple[QmtEndpointSpec, ...]:
    """返回稳定 endpoint 矩阵。"""

    return QMT_ENDPOINT_SPECS


def iter_hld_categories() -> tuple[str, ...]:
    """返回 HLD §33.11 的 14 个覆盖类别。"""

    return HLD_ENDPOINT_CATEGORIES


def get_endpoint_spec(endpoint: QmtEndpointCategory | str) -> QmtEndpointSpec:
    """按 endpoint id 或 category 取 spec；未知 endpoint 抛出 KeyError。"""

    spec = resolve_endpoint_spec(endpoint)
    if spec is None:
        raise KeyError(str(endpoint))
    return spec


def resolve_endpoint_spec(endpoint: QmtEndpointCategory | str) -> QmtEndpointSpec | None:
    """按 endpoint id 或 category 解析 spec。"""

    category = _coerce_category(endpoint)
    if category is not None:
        return _SPEC_BY_CATEGORY.get(category)
    return _SPEC_BY_ENDPOINT_ID.get(str(endpoint))


def endpoint_specs_by_hld_category() -> dict[str, tuple[QmtEndpointSpec, ...]]:
    """按 HLD 覆盖类别分组 endpoint spec。"""

    grouped: dict[str, list[QmtEndpointSpec]] = {
        category: [] for category in HLD_ENDPOINT_CATEGORIES
    }
    for spec in QMT_ENDPOINT_SPECS:
        grouped.setdefault(spec.hld_category, []).append(spec)
    return {key: tuple(value) for key, value in grouped.items()}


def build_capabilities_payload(
    specs: Iterable[QmtEndpointSpec] | None = None,
) -> dict[str, object]:
    """构造不授权真实操作的 capabilities payload。"""

    current_specs = tuple(specs or QMT_ENDPOINT_SPECS)
    return {
        "schema_version": QMT_ENDPOINT_MATRIX_SCHEMA_VERSION,
        "endpoint_categories": list(HLD_ENDPOINT_CATEGORIES),
        "endpoint_ids": [spec.endpoint_id for spec in current_specs],
        "endpoints": [spec.to_dict() for spec in current_specs],
        "operation_authorized": False,
        "account_authorized": False,
        "order_authorized": False,
        "cancel_authorized": False,
        "simulation_authorized": False,
        "live_authorized": False,
        "fixture_only": True,
        "real_operation": False,
    }


def _coerce_category(value: QmtEndpointCategory | str) -> QmtEndpointCategory | None:
    try:
        return value if isinstance(value, QmtEndpointCategory) else QmtEndpointCategory(str(value))
    except ValueError:
        return None
