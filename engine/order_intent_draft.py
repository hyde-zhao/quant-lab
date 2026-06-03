"""CR025-S03 的离线 order intent draft 合同。

本模块只构建可审计的 `order_intent_draft_v1` 草案，不导入或调用真实
QMT / MiniQMT / XtQuant / broker / Backtrader 运行时，也不读凭据、不写湖。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, date, datetime
import hashlib
import json
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "order_intent_draft_v1"
RAW_EXECUTION_PRICE_POLICY = "raw"
LATER_GATED_CONSUMER = "CR-020..CR-024 later-gated"

REQUIRED_DRAFT_FIELDS = (
    "schema_version",
    "draft_id",
    "source_run_id",
    "created_at",
    "strategy_id",
    "run_id",
    "signal_date",
    "target_trade_date",
    "target_portfolio_id",
    "semantic_diff_artifact_id",
    "data_lineage_ref",
    "limitations",
    "symbol",
    "side",
    "estimated_price_policy",
    "execution_price_policy",
    "research_adjustment_policy",
    "cost_config_ref",
    "reason",
    "raw_execution_policy_status",
    "pretrade_required",
    "qmt_allowed",
    "blocked_reasons",
    "consumer",
    "not_authorization",
    "operation_counters",
)

FORBIDDEN_OPERATION_COUNTERS = (
    "qmt_api_call",
    "miniqmt_call",
    "xtquant_import_or_call",
    "order_submit",
    "order_cancel",
    "account_query",
    "broker_lake_write",
    "service_start",
    "credential_read",
    "dependency_change",
    "backtrader_run",
    "backtrader_source_copy",
    "multifactor_research_framework_implementation",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "simulation_or_live",
    "qlib_alphalens_vnpyalpha_integration",
)

BLOCKED_REASON_CODES = (
    "unknown_schema_version",
    "missing_source_run_id",
    "missing_semantic_diff_artifact",
    "missing_target_portfolio",
    "missing_target_quantity_or_weight",
    "missing_lineage",
    "missing_limitations",
    "non_raw_execution_price_policy",
    "raw_execution_policy_blocked",
    "qmt_not_authorized",
    "forbidden_operation_nonzero",
    "sensitive_material_present",
)

_SENSITIVE_FIELD_PATTERNS = (
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


class OrderIntentDraftError(Exception):
    """order intent draft 基础异常。"""


class OrderIntentDraftValidationError(OrderIntentDraftError):
    """draft 未通过 schema / handoff 校验。"""


class OrderIntentSideEffectError(OrderIntentDraftError):
    """发现真实操作计数非 0。"""


@dataclass(frozen=True, slots=True)
class OrderIntentDraftViolation:
    code: str
    message: str
    severity: str = "blocker"
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "field": self.field,
        }


@dataclass(frozen=True, slots=True)
class OrderIntentDraftValidation:
    passed: bool
    violations: tuple[OrderIntentDraftViolation, ...] = ()
    missing_required_fields: tuple[str, ...] = ()
    required_field_coverage: float = 0.0
    forbidden_operation_counts: Mapping[str, int] = field(
        default_factory=lambda: zero_forbidden_operation_counts()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": [violation.to_dict() for violation in self.violations],
            "missing_required_fields": list(self.missing_required_fields),
            "required_field_coverage": self.required_field_coverage,
            "forbidden_operation_counts": dict(self.forbidden_operation_counts),
        }


@dataclass(frozen=True, slots=True)
class OrderIntentDraftV1:
    schema_version: str
    draft_id: str
    source_run_id: str
    created_at: str
    strategy_id: str
    run_id: str
    signal_date: str
    target_trade_date: str
    target_portfolio_id: str
    semantic_diff_artifact_id: str
    data_lineage_ref: Any
    limitations: tuple[Any, ...]
    symbol: str
    side: str
    target_qty: int | None
    target_weight: Any = None
    estimated_price_policy: str = ""
    execution_price_policy: str = RAW_EXECUTION_PRICE_POLICY
    research_adjustment_policy: str = ""
    cost_config_ref: str = ""
    reason: str = ""
    raw_execution_policy_status: str = "pass"
    pretrade_required: bool = True
    qmt_allowed: bool = False
    blocked_reasons: tuple[str, ...] = ()
    consumer: str = LATER_GATED_CONSUMER
    not_authorization: bool = True
    operation_counters: Mapping[str, int] = field(
        default_factory=lambda: zero_forbidden_operation_counts()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "draft_id": self.draft_id,
            "source_run_id": self.source_run_id,
            "created_at": self.created_at,
            "strategy_id": self.strategy_id,
            "run_id": self.run_id,
            "signal_date": self.signal_date,
            "target_trade_date": self.target_trade_date,
            "target_portfolio_id": self.target_portfolio_id,
            "semantic_diff_artifact_id": self.semantic_diff_artifact_id,
            "data_lineage_ref": _json_safe(self.data_lineage_ref),
            "limitations": _json_safe(list(self.limitations)),
            "symbol": self.symbol,
            "side": self.side,
            "target_qty": self.target_qty,
            "target_weight": _json_safe(self.target_weight),
            "estimated_price_policy": self.estimated_price_policy,
            "execution_price_policy": self.execution_price_policy,
            "research_adjustment_policy": self.research_adjustment_policy,
            "cost_config_ref": self.cost_config_ref,
            "reason": self.reason,
            "raw_execution_policy_status": self.raw_execution_policy_status,
            "pretrade_required": self.pretrade_required,
            "qmt_allowed": self.qmt_allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "consumer": self.consumer,
            "not_authorization": self.not_authorization,
            "operation_counters": dict(self.operation_counters),
        }


@dataclass(frozen=True, slots=True)
class OrderIntentDraftResult:
    status: str
    draft: OrderIntentDraftV1 | None = None
    blocked_reasons: tuple[str, ...] = ()
    source_ref: Mapping[str, Any] = field(default_factory=dict)
    validation: OrderIntentDraftValidation | None = None
    operation_counters: Mapping[str, int] = field(
        default_factory=lambda: zero_forbidden_operation_counts()
    )
    handoff: Mapping[str, Any] | None = None

    @property
    def passed(self) -> bool:
        return self.status == "draft" and self.draft is not None

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "draft": None if self.draft is None else self.draft.to_dict(),
            "blocked_reasons": list(self.blocked_reasons),
            "source_ref": _json_safe(dict(self.source_ref)),
            "validation": None if self.validation is None else self.validation.to_dict(),
            "operation_counters": dict(self.operation_counters),
            "handoff": None if self.handoff is None else _json_safe(dict(self.handoff)),
        }


def zero_forbidden_operation_counts() -> dict[str, int]:
    """返回 CR025-S03 必须保持为 0 的禁止操作计数。"""

    return {name: 0 for name in FORBIDDEN_OPERATION_COUNTERS}


def build_order_intent_draft(
    target_portfolio: Mapping[str, Any] | Sequence[Mapping[str, Any]] | Any,
    semantic_diff: Mapping[str, Any] | Any,
    policy_context: Mapping[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> OrderIntentDraftResult:
    """构建离线 order intent draft；任一执行边界失败时 fail closed。"""

    context = _mapping_from(policy_context)
    target = _first_target_row(target_portfolio)
    semantic = _mapping_from(semantic_diff)
    metadata = _mapping_from(semantic.get("metadata"))
    availability = _mapping_from(semantic.get("availability"))
    explanation = _mapping_from(semantic.get("explanation"))
    observed_at = _observed_at(now)

    source_run_id = _first_non_empty(
        context.get("source_run_id"),
        target.get("source_run_id"),
        target.get("run_id"),
        metadata.get("source_run_id"),
    )
    run_id = _first_non_empty(context.get("run_id"), target.get("run_id"), source_run_id)
    strategy_id = _first_non_empty(context.get("strategy_id"), target.get("strategy_id"))
    target_portfolio_id = _first_non_empty(
        context.get("target_portfolio_id"),
        target.get("target_portfolio_id"),
        target.get("portfolio_id"),
        f"target-portfolio:{run_id}" if run_id else "",
    )
    semantic_diff_artifact_id = _first_non_empty(
        context.get("semantic_diff_artifact_id"),
        semantic.get("semantic_diff_artifact_id"),
        semantic.get("artifact_id"),
        metadata.get("semantic_diff_artifact_id"),
        metadata.get("artifact_id"),
        f"semantic-diff:{metadata.get('source_run_id')}" if metadata.get("source_run_id") else "",
    )
    lineage = _first_present(
        context.get("data_lineage_ref"),
        target.get("data_lineage_ref"),
        target.get("lineage"),
        metadata.get("lineage"),
    )
    limitations_present, limitations_value = _first_present_with_flag(
        context,
        target,
        semantic,
        availability,
        key="limitations",
    )
    limitations = tuple(_as_sequence(limitations_value)) if limitations_present else ()

    execution_policy = _first_non_empty(
        context.get("execution_price_policy"),
        target.get("execution_price_policy"),
    )
    raw_policy_status = _first_non_empty(
        context.get("raw_execution_policy_status"),
        "pass" if execution_policy == RAW_EXECUTION_PRICE_POLICY else "blocked",
    )
    requested_qmt_allowed = any(
        _bool_value(source.get("qmt_allowed"))
        for source in (context, target, semantic, metadata)
        if "qmt_allowed" in source
    )
    input_counter_violations = _input_counter_violations(context, target, semantic, metadata)

    pre_blocked_reasons: list[str] = []
    if not source_run_id:
        pre_blocked_reasons.append("missing_source_run_id")
    if not target_portfolio_id:
        pre_blocked_reasons.append("missing_target_portfolio")
    if not semantic_diff_artifact_id:
        pre_blocked_reasons.append("missing_semantic_diff_artifact")
    if _is_missing_lineage(lineage):
        pre_blocked_reasons.append("missing_lineage")
    if not limitations_present:
        pre_blocked_reasons.append("missing_limitations")
    if execution_policy != RAW_EXECUTION_PRICE_POLICY:
        pre_blocked_reasons.append("non_raw_execution_price_policy")
        pre_blocked_reasons.append("raw_execution_policy_blocked")
    if raw_policy_status != "pass":
        pre_blocked_reasons.append("raw_execution_policy_blocked")
    if requested_qmt_allowed:
        pre_blocked_reasons.append("qmt_not_authorized")
    pre_blocked_reasons.extend(input_counter_violations)

    source_ref = {
        "target_portfolio_id": target_portfolio_id,
        "semantic_diff_artifact_id": semantic_diff_artifact_id,
        "source_run_id": source_run_id,
    }
    if pre_blocked_reasons:
        return block_order_intent(pre_blocked_reasons, source_ref=source_ref)

    draft = OrderIntentDraftV1(
        schema_version=SCHEMA_VERSION,
        draft_id=_first_non_empty(
            context.get("draft_id"),
            target.get("draft_id"),
            _stable_draft_id(strategy_id, run_id, target, semantic_diff_artifact_id),
        ),
        source_run_id=source_run_id,
        created_at=_first_non_empty(context.get("created_at"), observed_at.isoformat()),
        strategy_id=strategy_id,
        run_id=run_id,
        signal_date=_first_non_empty(
            context.get("signal_date"),
            target.get("signal_date"),
        ),
        target_trade_date=_first_non_empty(
            context.get("target_trade_date"),
            target.get("target_trade_date"),
            target.get("trade_date"),
        ),
        target_portfolio_id=target_portfolio_id,
        semantic_diff_artifact_id=semantic_diff_artifact_id,
        data_lineage_ref=lineage,
        limitations=limitations,
        symbol=_first_non_empty(context.get("symbol"), target.get("symbol")),
        side=_first_non_empty(context.get("side"), target.get("side")).lower(),
        target_qty=_int_or_none(
            _first_present(target.get("target_qty"), target.get("quantity"), target.get("qty"))
        ),
        target_weight=_first_present(target.get("target_weight"), context.get("target_weight")),
        estimated_price_policy=_first_non_empty(
            context.get("estimated_price_policy"),
            target.get("estimated_price_policy"),
            "research_estimate",
        ),
        execution_price_policy=execution_policy,
        research_adjustment_policy=_first_non_empty(
            context.get("research_adjustment_policy"),
            target.get("research_adjustment_policy"),
        ),
        cost_config_ref=_first_non_empty(context.get("cost_config_ref"), target.get("cost_config_ref")),
        reason=_first_non_empty(
            context.get("reason"),
            target.get("reason"),
            ",".join(str(item) for item in _as_sequence(explanation.get("diff_reason"))),
        ),
        raw_execution_policy_status=raw_policy_status,
        pretrade_required=_bool_value(context.get("pretrade_required", True), default=True),
        qmt_allowed=False,
        blocked_reasons=(),
        consumer=LATER_GATED_CONSUMER,
        not_authorization=True,
        operation_counters=zero_forbidden_operation_counts(),
    )
    validation = validate_order_intent_draft(draft)
    if not validation.passed:
        return block_order_intent(
            tuple(violation.code for violation in validation.violations),
            source_ref=source_ref,
            validation=validation,
        )
    handoff = to_later_gated_handoff(draft)
    return OrderIntentDraftResult(
        status="draft",
        draft=draft,
        blocked_reasons=(),
        source_ref=source_ref,
        validation=validation,
        operation_counters=zero_forbidden_operation_counts(),
        handoff=handoff,
    )


def validate_order_intent_draft(
    payload: OrderIntentDraftV1 | OrderIntentDraftResult | Mapping[str, Any],
) -> OrderIntentDraftValidation:
    """校验 draft schema、raw policy、QMT later-gated 边界和零计数。"""

    data = _draft_payload(payload)
    violations: list[OrderIntentDraftViolation] = []
    missing_required = tuple(
        field_name
        for field_name in REQUIRED_DRAFT_FIELDS
        if field_name not in data or _is_missing_required_value(data.get(field_name))
    )
    for field_name in missing_required:
        violations.append(
            OrderIntentDraftViolation(
                "missing_required_field",
                f"{field_name} is required",
                field=field_name,
            )
        )

    if data.get("schema_version") != SCHEMA_VERSION:
        violations.append(
            OrderIntentDraftViolation(
                "unknown_schema_version",
                "schema_version must be order_intent_draft_v1",
                field="schema_version",
            )
        )
    if _is_missing_lineage(data.get("data_lineage_ref")):
        violations.append(
            OrderIntentDraftViolation(
                "missing_lineage",
                "data_lineage_ref is required",
                field="data_lineage_ref",
            )
        )
    if "limitations" not in data or data.get("limitations") is None:
        violations.append(
            OrderIntentDraftViolation(
                "missing_limitations",
                "limitations field is required",
                field="limitations",
            )
        )
    if not _has_quantity_or_weight(data):
        violations.append(
            OrderIntentDraftViolation(
                "missing_target_quantity_or_weight",
                "target_qty or target_weight is required",
                field="target_qty/target_weight",
            )
        )
    if str(data.get("execution_price_policy", "")) != RAW_EXECUTION_PRICE_POLICY:
        violations.append(
            OrderIntentDraftViolation(
                "non_raw_execution_price_policy",
                "execution_price_policy must be raw",
                field="execution_price_policy",
            )
        )
    if str(data.get("raw_execution_policy_status", "")) != "pass":
        violations.append(
            OrderIntentDraftViolation(
                "raw_execution_policy_blocked",
                "raw_execution_policy_status must be pass",
                field="raw_execution_policy_status",
            )
        )
    if data.get("qmt_allowed") is not False:
        violations.append(
            OrderIntentDraftViolation(
                "qmt_not_authorized",
                "qmt_allowed must remain false",
                field="qmt_allowed",
            )
        )
    if data.get("not_authorization") is not True:
        violations.append(
            OrderIntentDraftViolation(
                "qmt_not_authorized",
                "not_authorization must remain true",
                field="not_authorization",
            )
        )
    if data.get("consumer") != LATER_GATED_CONSUMER:
        violations.append(
            OrderIntentDraftViolation(
                "consumer_not_later_gated",
                "consumer must be CR-020..CR-024 later-gated",
                field="consumer",
            )
        )
    if data.get("pretrade_required") is not True:
        violations.append(
            OrderIntentDraftViolation(
                "pretrade_required_missing",
                "pretrade_required must remain true",
                field="pretrade_required",
            )
        )
    blocked_reasons = _as_sequence(data.get("blocked_reasons"))
    if blocked_reasons:
        violations.append(
            OrderIntentDraftViolation(
                "blocked_reasons_present",
                "valid draft must not carry blocked_reasons",
                field="blocked_reasons",
            )
        )

    counters = _normalize_forbidden_counters(data.get("operation_counters"))
    missing_counters = [
        name
        for name in FORBIDDEN_OPERATION_COUNTERS
        if name not in _mapping_from(data.get("operation_counters"))
    ]
    for name in missing_counters:
        violations.append(
            OrderIntentDraftViolation(
                "forbidden_operation_counter_missing",
                f"{name} counter is required",
                field=f"operation_counters.{name}",
            )
        )
    for name, value in counters.items():
        if value != 0:
            violations.append(
                OrderIntentDraftViolation(
                    "forbidden_operation_nonzero",
                    f"{name} count must be 0",
                    field=f"operation_counters.{name}",
                )
            )

    for field_path in _scan_sensitive_material(data):
        violations.append(
            OrderIntentDraftViolation(
                "sensitive_material_present",
                "draft must not contain credentials, sessions, private keys or real account ids",
                field=field_path,
            )
        )

    coverage = (len(REQUIRED_DRAFT_FIELDS) - len(missing_required)) / len(REQUIRED_DRAFT_FIELDS)
    return OrderIntentDraftValidation(
        passed=not violations,
        violations=tuple(violations),
        missing_required_fields=missing_required,
        required_field_coverage=coverage,
        forbidden_operation_counts=counters,
    )


def block_order_intent(
    reason: str | Sequence[str],
    source_ref: Mapping[str, Any] | None = None,
    counters: Mapping[str, int] | None = None,
    validation: OrderIntentDraftValidation | None = None,
) -> OrderIntentDraftResult:
    """返回 fail-closed blocked result；不会生成 handoff。"""

    reasons = tuple(str(item) for item in _as_sequence(reason) if str(item).strip())
    return OrderIntentDraftResult(
        status="blocked",
        draft=None,
        blocked_reasons=reasons or ("blocked",),
        source_ref={} if source_ref is None else _json_safe(dict(source_ref)),
        validation=validation,
        operation_counters=zero_forbidden_operation_counts()
        if counters is None
        else _normalize_forbidden_counters(counters),
        handoff=None,
    )


def to_later_gated_handoff(
    draft: OrderIntentDraftV1 | OrderIntentDraftResult | Mapping[str, Any],
) -> dict[str, Any]:
    """生成 CR-020..CR-024 later-gated handoff，不代表任何运行授权。"""

    if isinstance(draft, OrderIntentDraftResult):
        if draft.draft is None:
            raise OrderIntentDraftValidationError("blocked result cannot generate later-gated handoff")
        payload = draft.draft.to_dict()
    else:
        payload = _draft_payload(draft)

    validation = validate_order_intent_draft(payload)
    if not validation.passed:
        raise OrderIntentDraftValidationError(
            json.dumps(validation.to_dict(), ensure_ascii=False, sort_keys=True)
        )
    assert_no_qmt_side_effects(payload)
    return {
        "schema_version": SCHEMA_VERSION,
        "draft_id": payload["draft_id"],
        "consumer": LATER_GATED_CONSUMER,
        "handoff_status": "later-gated",
        "not_authorization": True,
        "qmt_allowed": False,
        "requires_independent_authorization": True,
        "requires_pretrade": True,
        "required_follow_up": ["CR-020", "CR-021", "CR-022", "CR-023", "CR-024"],
        "does_not_authorize": [
            "qmt_api_call",
            "order_submit",
            "order_cancel",
            "account_query",
            "broker_lake_write",
            "service_start",
        ],
        "operation_counters": zero_forbidden_operation_counts(),
    }


def assert_no_qmt_side_effects(
    result_or_payload: OrderIntentDraftResult | OrderIntentDraftV1 | Mapping[str, Any],
) -> dict[str, int]:
    """断言 QMT / broker / dependency / Backtrader / 多因子等计数全为 0。"""

    if isinstance(result_or_payload, OrderIntentDraftResult):
        counters = dict(result_or_payload.operation_counters)
        if result_or_payload.draft is not None:
            counters.update(_normalize_forbidden_counters(result_or_payload.draft.operation_counters))
    else:
        counters = _normalize_forbidden_counters(_draft_payload(result_or_payload).get("operation_counters"))

    nonzero = {name: value for name, value in counters.items() if value != 0}
    if nonzero:
        raise OrderIntentSideEffectError(
            json.dumps(nonzero, ensure_ascii=False, sort_keys=True)
        )
    return counters


def _draft_payload(
    payload: OrderIntentDraftV1 | OrderIntentDraftResult | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(payload, OrderIntentDraftV1):
        return payload.to_dict()
    if isinstance(payload, OrderIntentDraftResult):
        return {} if payload.draft is None else payload.draft.to_dict()
    data = _mapping_from(payload)
    if "draft" in data and isinstance(data["draft"], Mapping):
        return dict(data["draft"])
    return dict(data)


def _first_target_row(
    target_portfolio: Mapping[str, Any] | Sequence[Mapping[str, Any]] | Any,
) -> dict[str, Any]:
    if isinstance(target_portfolio, Mapping):
        return _json_safe(dict(target_portfolio))
    if isinstance(target_portfolio, Sequence) and not isinstance(target_portfolio, (str, bytes)):
        for item in target_portfolio:
            return _mapping_from(item)
        return {}
    return _mapping_from(target_portfolio)


def _mapping_from(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _mapping_from(value.to_dict())
    if is_dataclass(value):
        return _json_safe(asdict(value))
    return {}


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip():
                return value.strip()
            continue
        if value != "":
            return str(value)
    return ""


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _first_present_with_flag(
    *sources: Mapping[str, Any],
    key: str,
) -> tuple[bool, Any]:
    for source in sources:
        if key in source:
            return True, source[key]
    return False, None


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _has_quantity_or_weight(data: Mapping[str, Any]) -> bool:
    return not _is_missing_scalar(data.get("target_qty")) or not _is_missing_scalar(
        data.get("target_weight")
    )


def _is_missing_required_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    return False


def _is_missing_scalar(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _is_missing_lineage(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence):
        return len(value) == 0
    return False


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _normalize_forbidden_counters(value: Any) -> dict[str, int]:
    raw = _mapping_from(value)
    counters = zero_forbidden_operation_counts()
    for name in FORBIDDEN_OPERATION_COUNTERS:
        if name in raw:
            counters[name] = int(raw.get(name) or 0)
    return counters


def _input_counter_violations(*sources: Mapping[str, Any]) -> list[str]:
    violations: list[str] = []
    for source in sources:
        for key in ("operation_counters", "forbidden_operation_counts", "safety_counters"):
            counters = _mapping_from(source.get(key))
            for name, value in counters.items():
                if name in FORBIDDEN_OPERATION_COUNTERS and int(value or 0) != 0:
                    violations.append(f"forbidden_operation_nonzero:{name}")
    return sorted(dict.fromkeys(violations))


def _scan_sensitive_material(value: Any, path: str = "") -> tuple[str, ...]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}" if path else key_text
            if current_path in {
                "operation_counters",
                "forbidden_operation_counts",
                "safety_counters",
            }:
                continue
            lower_key = key_text.lower()
            if any(pattern in lower_key for pattern in _SENSITIVE_FIELD_PATTERNS):
                findings.append(current_path)
                continue
            findings.extend(_scan_sensitive_material(item, current_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            findings.extend(_scan_sensitive_material(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        lower_value = value.lower()
        if any(pattern in lower_value for pattern in _SENSITIVE_FIELD_PATTERNS):
            findings.append(path or "<value>")
    return tuple(findings)


def _stable_draft_id(
    strategy_id: str,
    run_id: str,
    target: Mapping[str, Any],
    semantic_diff_artifact_id: str,
) -> str:
    payload = {
        "strategy_id": strategy_id,
        "run_id": run_id,
        "symbol": _first_non_empty(target.get("symbol")),
        "side": _first_non_empty(target.get("side")).lower(),
        "target_qty": _first_present(target.get("target_qty"), target.get("quantity"), target.get("qty")),
        "target_weight": target.get("target_weight"),
        "target_trade_date": _first_non_empty(target.get("target_trade_date"), target.get("trade_date")),
        "semantic_diff_artifact_id": semantic_diff_artifact_id,
    }
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"draft-{digest}"


def _observed_at(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC).replace(microsecond=0)
    if now.tzinfo is None:
        return now.replace(tzinfo=UTC).replace(microsecond=0)
    return now.astimezone(UTC).replace(microsecond=0)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


__all__ = (
    "BLOCKED_REASON_CODES",
    "FORBIDDEN_OPERATION_COUNTERS",
    "LATER_GATED_CONSUMER",
    "RAW_EXECUTION_PRICE_POLICY",
    "REQUIRED_DRAFT_FIELDS",
    "SCHEMA_VERSION",
    "OrderIntentDraftError",
    "OrderIntentDraftResult",
    "OrderIntentDraftV1",
    "OrderIntentDraftValidation",
    "OrderIntentDraftValidationError",
    "OrderIntentDraftViolation",
    "OrderIntentSideEffectError",
    "assert_no_qmt_side_effects",
    "block_order_intent",
    "build_order_intent_draft",
    "to_later_gated_handoff",
    "validate_order_intent_draft",
    "zero_forbidden_operation_counts",
)
