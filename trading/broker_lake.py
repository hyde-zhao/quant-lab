"""CR015-S05 的 broker lake schema registry 与 dry-run writer 合同。

本模块只构造内存态 schema、脱敏结果和写入计划，不打开路径、不创建目录、
不写文件，也不读取环境变量、凭据或真实 broker lake root。
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable, Mapping


BROKER_LAKE_SCHEMA_VERSION = "broker_lake_v1"
DEFAULT_RETENTION_POLICY = "3y"
REDACTED_VALUE = "<redacted>"
BLOCKED_TARGET_PREVIEW = "<blocked-target>"


class BrokerLakeEventType(str, Enum):
    """broker lake v1 覆盖的八类对象。"""

    ORDER_INTENT = "order_intent"
    BROKER_ORDER = "broker_order"
    FILL = "fill"
    POSITION = "position"
    ASSET = "asset"
    ERROR = "error"
    RECONCILIATION = "reconciliation"
    INCIDENT = "incident"


class BrokerLakePlanStatus(str, Enum):
    """dry-run write plan 的结构化状态。"""

    PLANNED = "planned"
    BLOCKED = "blocked"


class RedactionStatus(str, Enum):
    """redaction gate 的输出状态。"""

    PASS = "pass"
    REDACTED = "redacted"
    BLOCKED = "blocked"


class BrokerLakeErrorCode(str, Enum):
    """broker lake 合同错误码；不得携带敏感原值。"""

    UNKNOWN_EVENT_TYPE = "unknown_event_type"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    FORBIDDEN_TARGET = "forbidden_target"
    ROOT_LABEL_REQUIRED = "root_label_required"
    ROOT_LABEL_NOT_A_LABEL = "root_label_not_a_label"
    SENSITIVE_VALUE_REDACTED = "sensitive_value_redacted"
    SENSITIVE_VALUE_BLOCKED = "sensitive_value_blocked"


@dataclass(frozen=True, slots=True)
class BrokerLakeSchema:
    """单类 broker lake 对象的 schema contract。"""

    event_type: BrokerLakeEventType
    schema_version: str
    required_fields: tuple[str, ...]
    partition_keys: tuple[str, ...]
    retention_policy: str
    redaction_status: str


@dataclass(frozen=True, slots=True)
class BrokerLakeError:
    """结构化错误；只记录字段、错误码和安全原因。"""

    error_code: BrokerLakeErrorCode
    event_type: str = ""
    field: str = ""
    blocked_reason: str = ""


@dataclass(frozen=True, slots=True)
class RedactionResult:
    """redaction gate 输出，不保留原始 payload。"""

    redaction_status: RedactionStatus
    sanitized_payload: Mapping[str, Any]
    redacted_fields: tuple[str, ...] = ()
    blocked_fields: tuple[str, ...] = ()
    errors: tuple[BrokerLakeError, ...] = ()
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: broker_lake_safety_counters()
    )


@dataclass(frozen=True, slots=True)
class BrokerLakeTargetValidation:
    """broker lake root label / target preview 校验结果。"""

    allowed: bool
    root_label: str
    target_path_preview: str
    error: BrokerLakeError | None = None


@dataclass(frozen=True, slots=True)
class BrokerLakeWritePlan:
    """dry-run write plan；不代表真实写入。"""

    status: BrokerLakePlanStatus
    event_type: str
    root_label: str
    schema_version: str
    partition: Mapping[str, str]
    retention_policy: str
    redaction_status: RedactionStatus
    target_path_preview: str
    real_write: bool = False
    sanitized_event: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[BrokerLakeError, ...] = ()
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: broker_lake_safety_counters()
    )

    @property
    def blocked(self) -> bool:
        return self.status is BrokerLakePlanStatus.BLOCKED


@dataclass(frozen=True, slots=True)
class BrokerLakeAuditChain:
    """CR139 broker lake dry-run audit chain; never represents a real write."""

    status: str
    run_id: str
    strategy_id: str
    order_intent_id: str
    event_plans: tuple[BrokerLakeWritePlan, ...]
    errors: tuple[BrokerLakeError, ...] = ()
    real_write: bool = False
    safety_counters: Mapping[str, int] = field(default_factory=lambda: broker_lake_safety_counters())

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "strategy_id": self.strategy_id,
            "order_intent_id": self.order_intent_id,
            "event_plans": [asdict(plan) for plan in self.event_plans],
            "errors": [asdict(error) for error in self.errors],
            "real_write": self.real_write,
            "safety_counters": dict(self.safety_counters),
        }


BROKER_LAKE_SCHEMAS: Mapping[BrokerLakeEventType, BrokerLakeSchema] = {
    BrokerLakeEventType.ORDER_INTENT: BrokerLakeSchema(
        event_type=BrokerLakeEventType.ORDER_INTENT,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "order_intent_id",
            "strategy_id",
            "run_id",
            "symbol",
            "side",
            "target_qty",
            "target_trade_date",
            "execution_price_policy",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.BROKER_ORDER: BrokerLakeSchema(
        event_type=BrokerLakeEventType.BROKER_ORDER,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "order_intent_id",
            "strategy_id",
            "run_id",
            "broker_order_status",
            "oms_event",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.FILL: BrokerLakeSchema(
        event_type=BrokerLakeEventType.FILL,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "order_intent_id",
            "strategy_id",
            "run_id",
            "symbol",
            "filled_qty",
            "fill_price_policy",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.POSITION: BrokerLakeSchema(
        event_type=BrokerLakeEventType.POSITION,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "strategy_id",
            "run_id",
            "symbol",
            "position_qty",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.ASSET: BrokerLakeSchema(
        event_type=BrokerLakeEventType.ASSET,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "strategy_id",
            "run_id",
            "asset_kind",
            "asset_value",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.ERROR: BrokerLakeSchema(
        event_type=BrokerLakeEventType.ERROR,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "strategy_id",
            "run_id",
            "error_code",
            "error_stage",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.RECONCILIATION: BrokerLakeSchema(
        event_type=BrokerLakeEventType.RECONCILIATION,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "strategy_id",
            "run_id",
            "reconciliation_status",
            "reconciliation_scope",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
    BrokerLakeEventType.INCIDENT: BrokerLakeSchema(
        event_type=BrokerLakeEventType.INCIDENT,
        schema_version=BROKER_LAKE_SCHEMA_VERSION,
        required_fields=(
            "event_type",
            "strategy_id",
            "run_id",
            "incident_id",
            "incident_status",
            "trade_date",
        ),
        partition_keys=("trade_date", "run_id"),
        retention_policy=DEFAULT_RETENTION_POLICY,
        redaction_status="required",
    ),
}

_ROOT_LABEL_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_SENSITIVE_KEY_FRAGMENTS = (
    "token",
    "password",
    "passwd",
    "account",
    "session",
    "cookie",
    "credential",
    "secret",
    "private_key",
    "apikey",
    "api_key",
    "holdings",
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)\b(token|password|passwd|session|cookie|account|secret)\s*[:=]"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]"),
    re.compile(r"(?i)(^|[/\\])\.env($|[./\\])"),
    re.compile(r"(?i)begin [a-z ]*private key"),
    re.compile(r"(?i)^/home/[^/]+/.+"),
    re.compile(r"(?i)^/users/[^/]+/.+"),
    re.compile(r"(?i)^/root/.+"),
    re.compile(r"(?i)^[a-z]:\\users\\[^\\]+\\.+"),
)


def schema_for_event(event_type: BrokerLakeEventType | str) -> BrokerLakeSchema:
    """按事件类型返回 schema；未知类型抛出不含敏感值的结构化异常。"""

    event = _coerce_event_type(event_type)
    if event is None or event not in BROKER_LAKE_SCHEMAS:
        raise ValueError(BrokerLakeErrorCode.UNKNOWN_EVENT_TYPE.value)
    return BROKER_LAKE_SCHEMAS[event]


def build_schema_audit_summary() -> dict[str, object]:
    """返回 schema 覆盖摘要，供测试和后续文档消费。"""

    schemas: dict[str, dict[str, object]] = {}
    for event_type, schema in BROKER_LAKE_SCHEMAS.items():
        schemas[event_type.value] = {
            "schema_version": schema.schema_version,
            "required_fields": schema.required_fields,
            "partition_keys": schema.partition_keys,
            "retention_policy": schema.retention_policy,
            "redaction_status": schema.redaction_status,
        }
    return {
        "schema_version": BROKER_LAKE_SCHEMA_VERSION,
        "event_type_count": len(BROKER_LAKE_SCHEMAS),
        "event_types": tuple(event.value for event in BrokerLakeEventType),
        "schemas": schemas,
    }


def redact_event_payload(event_payload: Mapping[str, Any]) -> RedactionResult:
    """脱敏事件 payload；输出中不保留敏感原值。"""

    sanitized, redacted_fields, blocked_fields, errors = _sanitize_mapping(event_payload)
    if blocked_fields:
        status = RedactionStatus.BLOCKED
    elif redacted_fields:
        status = RedactionStatus.REDACTED
    else:
        status = RedactionStatus.PASS
    return RedactionResult(
        redaction_status=status,
        sanitized_payload=sanitized,
        redacted_fields=tuple(redacted_fields),
        blocked_fields=tuple(blocked_fields),
        errors=tuple(errors),
        safety_counters=broker_lake_safety_counters(),
    )


def validate_broker_lake_target(
    root_label: str,
    target_path: str | None = None,
) -> BrokerLakeTargetValidation:
    """确认 dry-run 只使用 root label，禁止仓库 data/reports 和真实路径。"""

    label = _string_value(root_label)
    if not label:
        return _blocked_target(BrokerLakeErrorCode.ROOT_LABEL_REQUIRED)

    if _looks_sensitive_or_path_like(label) or not _ROOT_LABEL_PATTERN.fullmatch(label):
        return _blocked_target(BrokerLakeErrorCode.ROOT_LABEL_NOT_A_LABEL)

    if target_path is not None and _is_forbidden_target(_string_value(target_path)):
        return _blocked_target(BrokerLakeErrorCode.FORBIDDEN_TARGET, root_label=label)

    return BrokerLakeTargetValidation(
        allowed=True,
        root_label=label,
        target_path_preview=f"<{label}>",
    )


def dry_run_write_plan(
    event_payload: Mapping[str, Any],
    root_label: str,
    retention_policy: str = DEFAULT_RETENTION_POLICY,
) -> BrokerLakeWritePlan:
    """只生成 broker lake 写入计划，不打开路径、不 mkdir、不 write。"""

    raw_event_type = _string_value(event_payload.get("event_type"))
    event_type = _coerce_event_type(raw_event_type)
    redaction = redact_event_payload(event_payload)
    target = validate_broker_lake_target(root_label)
    plan_errors: list[BrokerLakeError] = list(redaction.errors)

    if event_type is None:
        plan_errors.append(
            BrokerLakeError(
                error_code=BrokerLakeErrorCode.UNKNOWN_EVENT_TYPE,
                event_type=_safe_event_type_for_output(raw_event_type),
            )
        )
        return _blocked_write_plan(
            raw_event_type,
            target,
            _safe_retention_policy(retention_policy),
            redaction,
            tuple(plan_errors),
        )

    schema = BROKER_LAKE_SCHEMAS[event_type]
    if target.error is not None:
        plan_errors.append(target.error)

    sanitized = dict(redaction.sanitized_payload)
    missing_fields = tuple(
        field_name
        for field_name in schema.required_fields
        if not _has_required_value(sanitized, field_name)
    )
    for field_name in missing_fields:
        plan_errors.append(
            BrokerLakeError(
                error_code=BrokerLakeErrorCode.MISSING_REQUIRED_FIELD,
                event_type=event_type.value,
                field=field_name,
            )
        )

    partition = _build_partition(sanitized, schema.partition_keys)
    missing_partitions = tuple(
        key for key, value in partition.items() if not _string_value(value)
    )
    for key in missing_partitions:
        plan_errors.append(
            BrokerLakeError(
                error_code=BrokerLakeErrorCode.MISSING_REQUIRED_FIELD,
                event_type=event_type.value,
                field=key,
                blocked_reason="partition_key_missing",
            )
        )

    retention = _safe_retention_policy(retention_policy) or schema.retention_policy
    if target.error is not None or missing_fields or missing_partitions:
        return _blocked_write_plan(
            event_type.value,
            target,
            retention,
            redaction,
            tuple(plan_errors),
            schema_version=schema.schema_version,
            sanitized_event=sanitized,
            partition=partition,
        )

    return BrokerLakeWritePlan(
        status=BrokerLakePlanStatus.PLANNED,
        event_type=event_type.value,
        root_label=target.root_label,
        schema_version=schema.schema_version,
        partition=partition,
        retention_policy=retention,
        redaction_status=redaction.redaction_status,
        target_path_preview=_build_target_preview(
            target.root_label,
            event_type.value,
            partition,
            schema.schema_version,
        ),
        real_write=False,
        sanitized_event=sanitized,
        errors=tuple(plan_errors),
        safety_counters=broker_lake_safety_counters(),
    )


def build_broker_lake_audit_chain(
    event_payloads: Iterable[Mapping[str, Any]],
    *,
    root_label: str,
) -> BrokerLakeAuditChain:
    """Build a CR139 dry-run broker lake audit chain without broker/lake writes."""

    plans = tuple(dry_run_write_plan(payload, root_label=root_label) for payload in event_payloads)
    return validate_broker_lake_audit_chain(plans)


def validate_broker_lake_audit_chain(
    event_plans: Iterable[BrokerLakeWritePlan],
) -> BrokerLakeAuditChain:
    plans = tuple(event_plans)
    errors: list[BrokerLakeError] = []
    run_ids = {_string_value(plan.sanitized_event.get("run_id")) for plan in plans if _string_value(plan.sanitized_event.get("run_id"))}
    strategy_ids = {
        _string_value(plan.sanitized_event.get("strategy_id"))
        for plan in plans
        if _string_value(plan.sanitized_event.get("strategy_id"))
    }
    order_intent_ids = {
        _string_value(plan.sanitized_event.get("order_intent_id"))
        for plan in plans
        if _string_value(plan.sanitized_event.get("order_intent_id"))
    }
    if not plans:
        errors.append(BrokerLakeError(BrokerLakeErrorCode.MISSING_REQUIRED_FIELD, field="event_plans"))
    if len(run_ids) != 1:
        errors.append(BrokerLakeError(BrokerLakeErrorCode.MISSING_REQUIRED_FIELD, field="run_id", blocked_reason="run_id_chain_mismatch"))
    if len(strategy_ids) != 1:
        errors.append(BrokerLakeError(BrokerLakeErrorCode.MISSING_REQUIRED_FIELD, field="strategy_id", blocked_reason="strategy_id_chain_mismatch"))
    if len(order_intent_ids) != 1:
        errors.append(BrokerLakeError(BrokerLakeErrorCode.MISSING_REQUIRED_FIELD, field="order_intent_id", blocked_reason="order_intent_id_chain_mismatch"))
    for plan in plans:
        errors.extend(plan.errors)
        if plan.real_write:
            errors.append(BrokerLakeError(BrokerLakeErrorCode.FORBIDDEN_TARGET, field="real_write", blocked_reason="real_write_forbidden"))
        for counter_name, counter_value in plan.safety_counters.items():
            if int(counter_value) != 0:
                errors.append(
                    BrokerLakeError(
                        BrokerLakeErrorCode.FORBIDDEN_TARGET,
                        field=counter_name,
                        blocked_reason="safety_counter_non_zero",
                    )
                )
    return BrokerLakeAuditChain(
        status="pass" if not errors else "blocked",
        run_id=next(iter(run_ids), ""),
        strategy_id=next(iter(strategy_ids), ""),
        order_intent_id=next(iter(order_intent_ids), ""),
        event_plans=plans,
        errors=tuple(errors),
        real_write=False,
        safety_counters=broker_lake_safety_counters(),
    )


def broker_lake_safety_counters() -> dict[str, int]:
    """返回 CR015-S05 必须保持为 0 的安全计数。"""

    return {
        "qmt_api_call": 0,
        "real_order_call": 0,
        "real_cancel_call": 0,
        "account_query_call": 0,
        "account_write_call": 0,
        "credential_read": 0,
        "real_broker_lake_write": 0,
        "real_lake_write": 0,
        "provider_fetch": 0,
        "publish": 0,
        "dependency_change": 0,
        "open_write_call": 0,
        "sensitive_raw_value_output": 0,
    }


def sensitive_raw_value_output_count(
    rendered: object,
    sensitive_values: Iterable[str],
) -> int:
    """统计敏感原值在结构化输出中的出现次数。"""

    text = _render_for_scan(rendered)
    return sum(text.count(value) for value in sensitive_values if value)


def _blocked_write_plan(
    event_type: str,
    target: BrokerLakeTargetValidation,
    retention_policy: str,
    redaction: RedactionResult,
    errors: tuple[BrokerLakeError, ...],
    *,
    schema_version: str = BROKER_LAKE_SCHEMA_VERSION,
    sanitized_event: Mapping[str, Any] | None = None,
    partition: Mapping[str, str] | None = None,
) -> BrokerLakeWritePlan:
    status = (
        RedactionStatus.BLOCKED
        if redaction.redaction_status is RedactionStatus.BLOCKED
        else redaction.redaction_status
    )
    return BrokerLakeWritePlan(
        status=BrokerLakePlanStatus.BLOCKED,
        event_type=_safe_event_type_for_output(event_type),
        root_label=target.root_label,
        schema_version=schema_version,
        partition=dict(partition or {}),
        retention_policy=retention_policy,
        redaction_status=status,
        target_path_preview=BLOCKED_TARGET_PREVIEW,
        real_write=False,
        sanitized_event=dict(sanitized_event or redaction.sanitized_payload),
        errors=errors,
        safety_counters=broker_lake_safety_counters(),
    )


def _blocked_target(
    error_code: BrokerLakeErrorCode,
    *,
    root_label: str = "<blocked-root-label>",
) -> BrokerLakeTargetValidation:
    return BrokerLakeTargetValidation(
        allowed=False,
        root_label=root_label if _ROOT_LABEL_PATTERN.fullmatch(root_label) else "<blocked-root-label>",
        target_path_preview=BLOCKED_TARGET_PREVIEW,
        error=BrokerLakeError(
            error_code=error_code,
            field="root_label",
            blocked_reason="broker_lake_target_must_be_label_only",
        ),
    )


def _sanitize_mapping(
    payload: Mapping[str, Any],
    *,
    prefix: str = "",
) -> tuple[dict[str, Any], list[str], list[str], list[BrokerLakeError]]:
    sanitized: dict[str, Any] = {}
    redacted_fields: list[str] = []
    blocked_fields: list[str] = []
    errors: list[BrokerLakeError] = []
    for key, value in payload.items():
        field = f"{prefix}.{key}" if prefix else str(key)
        safe_value, field_redacted, field_blocked, field_errors = _sanitize_value(
            field,
            value,
        )
        sanitized[str(key)] = safe_value
        redacted_fields.extend(field_redacted)
        blocked_fields.extend(field_blocked)
        errors.extend(field_errors)
    return sanitized, redacted_fields, blocked_fields, errors


def _sanitize_value(
    field: str,
    value: Any,
) -> tuple[Any, list[str], list[str], list[BrokerLakeError]]:
    key_sensitive = _is_sensitive_key(field)
    if isinstance(value, Mapping):
        sanitized, redacted, blocked, errors = _sanitize_mapping(value, prefix=field)
        if key_sensitive:
            return _redacted_result(field)
        return sanitized, redacted, blocked, errors
    if isinstance(value, (list, tuple)):
        values: list[Any] = []
        redacted: list[str] = []
        blocked: list[str] = []
        errors: list[BrokerLakeError] = []
        for index, item in enumerate(value):
            safe_value, item_redacted, item_blocked, item_errors = _sanitize_value(
                f"{field}[{index}]",
                item,
            )
            values.append(safe_value)
            redacted.extend(item_redacted)
            blocked.extend(item_blocked)
            errors.extend(item_errors)
        if key_sensitive:
            return _redacted_result(field)
        return values, redacted, blocked, errors
    if key_sensitive or _looks_sensitive_string(_string_value(value)):
        return _redacted_result(field)
    return _json_safe_scalar(value), [], [], []


def _redacted_result(
    field: str,
) -> tuple[str, list[str], list[str], list[BrokerLakeError]]:
    return (
        REDACTED_VALUE,
        [field],
        [],
        [
            BrokerLakeError(
                error_code=BrokerLakeErrorCode.SENSITIVE_VALUE_REDACTED,
                field=field,
                blocked_reason="sensitive_value_redacted",
            )
        ],
    )


def _build_partition(
    payload: Mapping[str, Any],
    partition_keys: tuple[str, ...],
) -> dict[str, str]:
    return {
        key: _partition_value(payload, key)
        for key in partition_keys
    }


def _partition_value(payload: Mapping[str, Any], key: str) -> str:
    aliases = {
        "trade_date": ("trade_date", "target_trade_date", "event_date"),
        "run_id": ("run_id",),
    }
    for candidate in aliases.get(key, (key,)):
        value = _string_value(payload.get(candidate))
        if value:
            return value
    return ""


def _has_required_value(payload: Mapping[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    if value in (None, ""):
        return False
    if value == REDACTED_VALUE:
        return True
    return bool(_string_value(value))


def _build_target_preview(
    root_label: str,
    event_type: str,
    partition: Mapping[str, str],
    schema_version: str,
) -> str:
    partition_preview = "::".join(
        f"{key}={_safe_preview_segment(value)}"
        for key, value in partition.items()
    )
    return (
        f"<{root_label}>::event_type={event_type}::"
        f"{partition_preview}::schema_version={schema_version}"
    )


def _safe_preview_segment(value: object) -> str:
    text = _string_value(value)
    if _looks_sensitive_string(text):
        return REDACTED_VALUE
    return text


def _coerce_event_type(value: BrokerLakeEventType | str) -> BrokerLakeEventType | None:
    if isinstance(value, BrokerLakeEventType):
        return value
    try:
        return BrokerLakeEventType(str(value))
    except ValueError:
        return None


def _safe_event_type_for_output(value: object) -> str:
    text = _string_value(value)
    if _looks_sensitive_string(text):
        return REDACTED_VALUE
    return text


def _safe_retention_policy(value: object) -> str:
    text = _string_value(value)
    if not text:
        return DEFAULT_RETENTION_POLICY
    if _looks_sensitive_string(text):
        return REDACTED_VALUE
    return text


def _looks_sensitive_or_path_like(value: str) -> bool:
    return _looks_sensitive_string(value) or _looks_like_path(value) or _is_forbidden_target(value)


def _looks_sensitive_string(value: str) -> bool:
    if not value:
        return False
    return any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS)


def _looks_like_path(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        "/" in lowered
        or "\\" in lowered
        or lowered.startswith(".")
        or lowered.startswith("~")
        or ":" in lowered
    )


def _is_forbidden_target(value: str) -> bool:
    lowered = value.strip().replace("\\", "/").lower()
    cleaned = lowered[2:] if lowered.startswith("./") else lowered
    if cleaned in {"data", "reports"}:
        return True
    if cleaned.startswith("data/") or cleaned.startswith("reports/"):
        return True
    return "/data/" in cleaned or "/reports/" in cleaned


def _is_sensitive_key(field: str) -> bool:
    lowered = field.lower().replace("-", "_")
    return any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS)


def _json_safe_scalar(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value).strip()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def _render_for_scan(rendered: object) -> str:
    if hasattr(rendered, "__dataclass_fields__"):
        rendered = asdict(rendered)
    return json.dumps(rendered, ensure_ascii=False, sort_keys=True, default=str)


__all__ = [
    "BLOCKED_TARGET_PREVIEW",
    "BROKER_LAKE_SCHEMA_VERSION",
    "BROKER_LAKE_SCHEMAS",
    "DEFAULT_RETENTION_POLICY",
    "REDACTED_VALUE",
    "BrokerLakeError",
    "BrokerLakeErrorCode",
    "BrokerLakeAuditChain",
    "BrokerLakeEventType",
    "BrokerLakePlanStatus",
    "BrokerLakeSchema",
    "BrokerLakeTargetValidation",
    "BrokerLakeWritePlan",
    "RedactionResult",
    "RedactionStatus",
    "broker_lake_safety_counters",
    "build_broker_lake_audit_chain",
    "build_schema_audit_summary",
    "dry_run_write_plan",
    "redact_event_payload",
    "schema_for_event",
    "sensitive_raw_value_output_count",
    "validate_broker_lake_audit_chain",
    "validate_broker_lake_target",
]
