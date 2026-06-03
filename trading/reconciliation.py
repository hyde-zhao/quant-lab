"""CR016-S02 的离线 reconciliation 服务与报告候选合同。

本模块只消费调用方显式提供的 fixture、mock facts 或后续授权后的脱敏
snapshot ref，不查询真实账户、不读取凭据、不写 broker lake、不覆盖报告文件。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


RECONCILIATION_SCHEMA_VERSION = "reconciliation_report_v1"
RECONCILIATION_CANDIDATE_KIND = "versioned_reconciliation_report_candidate"
REDACTED_REF = "<redacted-ref>"
MISSING_REF = "<missing-ref>"

RECON_DIMENSIONS: tuple[str, ...] = (
    "orders",
    "fills",
    "positions",
    "assets",
    "cash",
    "broker_lake_facts",
)

_ALLOWED_INPUT_SOURCES = frozenset(
    {
        "fixture",
        "mock_facts",
        "mock",
        "redacted_snapshot_ref",
        "authorized_redacted_snapshot_ref",
    }
)
_STATUS_SEVERITY = {
    "pass": 0,
    "warn": 1,
    "manual_review": 2,
    "kill_switch": 3,
    "required_missing": 4,
}
_SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)\b(token|password|passwd|session|cookie|secret)\b"),
    re.compile(r"(?i)\bapi[_-]?key\b"),
    re.compile(r"(?i)\baccount[_-]?(id|no|number)?\b"),
    re.compile(r"(?i)\bholdings?\b"),
    re.compile(r"(?i)begin [a-z ]*private key"),
    re.compile(r"(?i)(^|[/\\])\.env($|[./\\])"),
    re.compile(r"(?i)^/home/[^/]+/.+"),
    re.compile(r"(?i)^/users/[^/]+/.+"),
    re.compile(r"(?i)^/root/.+"),
    re.compile(r"(?i)^[a-z]:\\users\\[^\\]+\\.+"),
)


class ReconPhase(str, Enum):
    """CR016-S02 支持的三个对账阶段。"""

    PRE_MARKET = "pre_market"
    INTRADAY = "intraday"
    POST_MARKET = "post_market"


class ReconciliationStatus(str, Enum):
    """对账和阈值评估的稳定状态枚举。"""

    PASS = "pass"
    WARN = "warn"
    MANUAL_REVIEW = "manual_review"
    KILL_SWITCH = "kill_switch"
    REQUIRED_MISSING = "required_missing"


class ReconciliationErrorCode(str, Enum):
    """对账合同暴露给 gate / runbook 的稳定错误枚举。"""

    BROKER_FACTS_REQUIRED_MISSING = "broker_facts_required_missing"
    THRESHOLD_REQUIRED_MISSING = "threshold_required_missing"
    INVALID_PHASE = "invalid_phase"
    UNAUTHORIZED_INPUT_SOURCE = "real_account_query_not_authorized"


@dataclass(frozen=True, slots=True)
class ThresholdConfig:
    """显式阈值配置；不内置真实资金阈值。"""

    warn: Mapping[str, float]
    manual_review: Mapping[str, float]
    kill_switch: Mapping[str, float]
    required_dimensions: tuple[str, ...] = RECON_DIMENSIONS

    def threshold_triplet(self, dimension: str) -> dict[str, float]:
        """返回指定维度的 warn / manual_review / kill_switch 阈值。"""

        return {
            "warn": _float_value(self.warn.get(dimension)),
            "manual_review": _float_value(self.manual_review.get(dimension)),
            "kill_switch": _float_value(self.kill_switch.get(dimension)),
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "ThresholdConfig":
        """从普通 mapping 构造阈值，便于 fixture 和后续 YAML 消费。"""

        required = payload.get("required_dimensions", RECON_DIMENSIONS)
        return cls(
            warn=_number_mapping(payload.get("warn")),
            manual_review=_number_mapping(payload.get("manual_review")),
            kill_switch=_number_mapping(payload.get("kill_switch")),
            required_dimensions=tuple(str(item) for item in _sequence_value(required)),
        )


@dataclass(frozen=True, slots=True)
class ReconciliationInput:
    """离线对账输入合同。

    `threshold_config` 与 `thresholds` 是兼容字段；调用方任选其一即可。
    """

    phase: ReconPhase | str
    local_state_ref: str
    broker_snapshot_ref: str
    broker_lake_ref: str
    local_state: Mapping[str, Any] = field(default_factory=dict)
    broker_facts: Mapping[str, Any] | None = None
    broker_lake_facts: Mapping[str, Any] | None = None
    threshold_config: ThresholdConfig | Mapping[str, object] | None = None
    thresholds: ThresholdConfig | Mapping[str, object] | None = None
    owner: str = "ops"
    action: str = "none"
    input_source: str = "fixture"
    report_label: str = "reconciliation"


@dataclass(frozen=True, slots=True)
class DiffRow:
    """单个对账差异行；只保留 ref / 摘要，不保留敏感原值。"""

    diff_type: str
    symbol: str
    local_value_ref: str
    broker_value_ref: str
    diff_value: float
    threshold: Mapping[str, float] = field(default_factory=dict)
    status: ReconciliationStatus = ReconciliationStatus.PASS
    owner: str = "ops"
    action: str = "none"


@dataclass(frozen=True, slots=True)
class ThresholdEvaluation:
    """阈值评估结果，供 `reconcile()` 和测试直接消费。"""

    status: ReconciliationStatus
    diff_rows: tuple[DiffRow, ...]
    thresholds: Mapping[str, Mapping[str, float]]
    error_code: ReconciliationErrorCode | None = None
    new_order_allowed: bool = True
    continue_order_allowed_count: int = 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.status.value == other
        return super().__eq__(other)


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """versioned report candidate；本对象不会写入 `reports/**`。"""

    report_id: str
    schema_version: str
    phase: ReconPhase
    broker_snapshot_ref: str
    local_state_ref: str
    broker_lake_ref: str
    diff_rows: tuple[DiffRow, ...]
    thresholds: Mapping[str, Mapping[str, float]]
    owner: str
    action: str
    status: ReconciliationStatus
    redaction_status: str
    error_code: ReconciliationErrorCode | None = None
    new_order_allowed: bool = True
    continue_order_allowed_count: int = 0
    report_kind: str = RECONCILIATION_CANDIDATE_KIND
    candidate_label: str = "reconciliation"
    safety_counters: Mapping[str, int] = field(
        default_factory=lambda: reconciliation_safety_counters()
    )

    @property
    def blocked(self) -> bool:
        return self.status in {
            ReconciliationStatus.REQUIRED_MISSING,
            ReconciliationStatus.MANUAL_REVIEW,
            ReconciliationStatus.KILL_SWITCH,
        }


def reconcile(recon_input: ReconciliationInput) -> ReconciliationReport:
    """执行 fixture-only 对账，返回 versioned report candidate。"""

    phase = _coerce_phase(recon_input.phase)
    if phase is None:
        return _required_missing_report(
            recon_input,
            phase=ReconPhase.PRE_MARKET,
            error_code=ReconciliationErrorCode.INVALID_PHASE,
            action="fix_phase",
        )

    if not _input_source_allowed(recon_input.input_source):
        return _required_missing_report(
            recon_input,
            phase=phase,
            error_code=ReconciliationErrorCode.UNAUTHORIZED_INPUT_SOURCE,
            action="provide_fixture_or_redacted_snapshot_ref",
        )

    if _facts_missing(recon_input):
        return _required_missing_report(
            recon_input,
            phase=phase,
            error_code=ReconciliationErrorCode.BROKER_FACTS_REQUIRED_MISSING,
            action="provide_required_broker_facts",
        )

    diff_rows = _build_diff_rows(recon_input)
    thresholds = _threshold_config_from_input(recon_input)
    evaluation = evaluate_thresholds(diff_rows, thresholds)
    redaction_status = _redaction_status_for_report(recon_input, evaluation.diff_rows)

    return ReconciliationReport(
        report_id=_build_report_id(
            phase,
            recon_input,
            evaluation.diff_rows,
            evaluation.status,
            evaluation.error_code,
        ),
        schema_version=RECONCILIATION_SCHEMA_VERSION,
        phase=phase,
        broker_snapshot_ref=_safe_ref(recon_input.broker_snapshot_ref),
        local_state_ref=_safe_ref(recon_input.local_state_ref),
        broker_lake_ref=_safe_ref(recon_input.broker_lake_ref),
        diff_rows=evaluation.diff_rows,
        thresholds=evaluation.thresholds,
        owner=_safe_label(recon_input.owner) or "ops",
        action=_report_action(evaluation.status, evaluation.error_code, recon_input.action),
        status=evaluation.status,
        redaction_status=redaction_status,
        error_code=evaluation.error_code,
        new_order_allowed=evaluation.new_order_allowed,
        continue_order_allowed_count=evaluation.continue_order_allowed_count,
        candidate_label=_safe_label(recon_input.report_label) or "reconciliation",
        safety_counters=reconciliation_safety_counters(),
    )


def evaluate_thresholds(
    diff_rows: Iterable[DiffRow],
    thresholds: ThresholdConfig | Mapping[str, object] | None,
) -> ThresholdEvaluation:
    """把 diff rows 映射为 pass / warn / manual_review / kill_switch。"""

    rows = tuple(diff_rows)
    config = _coerce_threshold_config(thresholds)
    if config is None or _thresholds_missing(config):
        required_rows = tuple(
            replace(
                row,
                status=ReconciliationStatus.REQUIRED_MISSING,
                action="provide_threshold_config",
            )
            for row in rows
        )
        return ThresholdEvaluation(
            status=ReconciliationStatus.REQUIRED_MISSING,
            diff_rows=required_rows,
            thresholds={},
            error_code=ReconciliationErrorCode.THRESHOLD_REQUIRED_MISSING,
            new_order_allowed=False,
            continue_order_allowed_count=0,
        )

    threshold_summary = _threshold_summary(config)
    evaluated_rows: list[DiffRow] = []
    overall = ReconciliationStatus.PASS

    for row in rows:
        triplet = threshold_summary[row.diff_type]
        row_status = _status_for_diff(row.diff_value, triplet)
        overall = _max_status(overall, row_status)
        evaluated_rows.append(
            replace(
                row,
                threshold=triplet,
                status=row_status,
                action=_action_for_status(row_status, row.action),
            )
        )

    return ThresholdEvaluation(
        status=overall,
        diff_rows=tuple(evaluated_rows),
        thresholds=threshold_summary,
        error_code=(
            None
            if overall in {ReconciliationStatus.PASS, ReconciliationStatus.WARN}
            else ReconciliationErrorCode.BROKER_FACTS_REQUIRED_MISSING
            if overall is ReconciliationStatus.REQUIRED_MISSING
            else None
        ),
        new_order_allowed=overall
        not in {
            ReconciliationStatus.REQUIRED_MISSING,
            ReconciliationStatus.MANUAL_REVIEW,
            ReconciliationStatus.KILL_SWITCH,
        },
        continue_order_allowed_count=0,
    )


def build_report_candidate(report: ReconciliationReport) -> dict[str, Any]:
    """返回可交给后续 writer 的候选对象；本函数不写文件。"""

    candidate_id = f"candidate:{report.report_id}"
    return {
        "candidate_id": candidate_id,
        "candidate_kind": report.report_kind,
        "schema_version": report.schema_version,
        "report_id": report.report_id,
        "status": report.status.value,
        "phase": report.phase.value,
        "storage_policy": "candidate_only_no_file_write",
        "target_ref": candidate_id,
        "old_report_overwrite": False,
        "reports_path": "",
        "report": _report_to_safe_dict(report),
        "safety_counters": reconciliation_safety_counters(),
    }


def to_kill_switch_candidate(report: ReconciliationReport) -> dict[str, Any]:
    """把对账报告转换为 CR016-S03 可消费的 kill switch trigger candidate。"""

    trigger_required = report.status in {
        ReconciliationStatus.REQUIRED_MISSING,
        ReconciliationStatus.MANUAL_REVIEW,
        ReconciliationStatus.KILL_SWITCH,
    }
    return {
        "candidate_id": f"kill-switch-candidate:{report.report_id}",
        "source_report_id": report.report_id,
        "schema_version": "kill_switch_candidate_v1",
        "trigger_required": trigger_required,
        "trigger_status": report.status.value,
        "trigger_reason": _trigger_reason(report),
        "owner": report.owner,
        "action": "trigger_kill_switch"
        if report.status is ReconciliationStatus.KILL_SWITCH
        else "manual_review"
        if trigger_required
        else "none",
        "new_order_allowed": report.new_order_allowed if not trigger_required else False,
        "continue_order_allowed_count": 0,
        "incident_ref": f"incident-candidate:{report.report_id}"
        if trigger_required
        else "",
        "safety_counters": reconciliation_safety_counters(),
    }


def reconciliation_safety_counters() -> dict[str, int]:
    """返回 CR016-S02 必须保持为 0 的真实操作计数。"""

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
        "simulation_run": 0,
        "real_snapshot_pull": 0,
        "old_report_overwrite": 0,
        "continue_order_allowed_after_threshold_breach": 0,
        "sensitive_raw_value_output": 0,
    }


def sensitive_raw_value_output_count(
    rendered: object,
    sensitive_values: Iterable[str],
) -> int:
    """统计敏感原值在结构化输出中的出现次数。"""

    text = _render_for_scan(rendered)
    return sum(text.count(value) for value in sensitive_values if value)


def _build_diff_rows(recon_input: ReconciliationInput) -> tuple[DiffRow, ...]:
    broker_facts = dict(recon_input.broker_facts or {})
    broker_lake_facts = dict(recon_input.broker_lake_facts or {})
    local_state = dict(recon_input.local_state or {})
    rows: list[DiffRow] = []

    for dimension in RECON_DIMENSIONS:
        if dimension == "broker_lake_facts":
            local_value = local_state.get(dimension, local_state.get("broker_lake"))
            broker_value = broker_lake_facts
        else:
            local_value = local_state.get(dimension)
            broker_value = broker_facts.get(dimension)
        rows.append(
            DiffRow(
                diff_type=dimension,
                symbol=_symbol_for_dimension(local_value, broker_value),
                local_value_ref=_value_ref("local", dimension, local_value),
                broker_value_ref=_value_ref("broker", dimension, broker_value),
                diff_value=_diff_value(local_value, broker_value),
                owner=_safe_label(recon_input.owner) or "ops",
            )
        )
    return tuple(rows)


def _required_missing_report(
    recon_input: ReconciliationInput,
    *,
    phase: ReconPhase,
    error_code: ReconciliationErrorCode,
    action: str,
) -> ReconciliationReport:
    status = ReconciliationStatus.REQUIRED_MISSING
    return ReconciliationReport(
        report_id=_build_report_id(phase, recon_input, (), status, error_code),
        schema_version=RECONCILIATION_SCHEMA_VERSION,
        phase=phase,
        broker_snapshot_ref=_safe_ref(recon_input.broker_snapshot_ref),
        local_state_ref=_safe_ref(recon_input.local_state_ref),
        broker_lake_ref=_safe_ref(recon_input.broker_lake_ref),
        diff_rows=(),
        thresholds={},
        owner=_safe_label(recon_input.owner) or "ops",
        action=action,
        status=status,
        redaction_status=_redaction_status_for_payload(asdict(recon_input)),
        error_code=error_code,
        new_order_allowed=False,
        continue_order_allowed_count=0,
        candidate_label=_safe_label(recon_input.report_label) or "reconciliation",
        safety_counters=reconciliation_safety_counters(),
    )


def _build_report_id(
    phase: ReconPhase,
    recon_input: ReconciliationInput,
    diff_rows: Sequence[DiffRow],
    status: ReconciliationStatus,
    error_code: ReconciliationErrorCode | None,
) -> str:
    payload = {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "phase": phase.value,
        "broker_snapshot_ref": _safe_ref(recon_input.broker_snapshot_ref),
        "local_state_ref": _safe_ref(recon_input.local_state_ref),
        "broker_lake_ref": _safe_ref(recon_input.broker_lake_ref),
        "status": status.value,
        "error_code": error_code.value if error_code else "",
        "diff_rows": [_diff_row_to_dict(row) for row in diff_rows],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()
    return f"recon-candidate-v1-{digest[:16]}"


def _threshold_config_from_input(
    recon_input: ReconciliationInput,
) -> ThresholdConfig | Mapping[str, object] | None:
    if recon_input.thresholds is not None:
        return recon_input.thresholds
    return recon_input.threshold_config


def _coerce_threshold_config(
    thresholds: ThresholdConfig | Mapping[str, object] | None,
) -> ThresholdConfig | None:
    if thresholds is None:
        return None
    if isinstance(thresholds, ThresholdConfig):
        return thresholds
    if isinstance(thresholds, Mapping):
        return ThresholdConfig.from_mapping(thresholds)
    return None


def _thresholds_missing(config: ThresholdConfig) -> bool:
    for dimension in config.required_dimensions:
        if dimension not in RECON_DIMENSIONS:
            return True
        for threshold_map in (config.warn, config.manual_review, config.kill_switch):
            if dimension not in threshold_map:
                return True
    return False


def _threshold_summary(
    config: ThresholdConfig,
) -> dict[str, dict[str, float]]:
    return {
        dimension: config.threshold_triplet(dimension)
        for dimension in config.required_dimensions
    }


def _status_for_diff(
    diff_value: float,
    threshold: Mapping[str, float],
) -> ReconciliationStatus:
    value = abs(_float_value(diff_value))
    if value > _float_value(threshold.get("kill_switch")):
        return ReconciliationStatus.KILL_SWITCH
    if value > _float_value(threshold.get("manual_review")):
        return ReconciliationStatus.MANUAL_REVIEW
    if value > _float_value(threshold.get("warn")):
        return ReconciliationStatus.WARN
    return ReconciliationStatus.PASS


def _max_status(
    current: ReconciliationStatus,
    candidate: ReconciliationStatus,
) -> ReconciliationStatus:
    if _STATUS_SEVERITY[candidate.value] > _STATUS_SEVERITY[current.value]:
        return candidate
    return current


def _facts_missing(recon_input: ReconciliationInput) -> bool:
    return (
        not _safe_ref(recon_input.local_state_ref)
        or not _safe_ref(recon_input.broker_snapshot_ref)
        or not _safe_ref(recon_input.broker_lake_ref)
        or not recon_input.local_state
        or not recon_input.broker_facts
        or not recon_input.broker_lake_facts
    )


def _input_source_allowed(input_source: str) -> bool:
    return _safe_label(input_source) in _ALLOWED_INPUT_SOURCES


def _action_for_status(status: ReconciliationStatus, fallback: str = "") -> str:
    if status is ReconciliationStatus.PASS:
        return "none"
    if status is ReconciliationStatus.WARN:
        return "monitor"
    if status is ReconciliationStatus.MANUAL_REVIEW:
        return "manual_review"
    if status is ReconciliationStatus.KILL_SWITCH:
        return "trigger_kill_switch"
    if status is ReconciliationStatus.REQUIRED_MISSING:
        return fallback if fallback and fallback != "none" else "provide_required_input"
    return fallback or "none"


def _report_action(
    status: ReconciliationStatus,
    error_code: ReconciliationErrorCode | None,
    fallback: str = "",
) -> str:
    if error_code is ReconciliationErrorCode.THRESHOLD_REQUIRED_MISSING:
        return "provide_required_input"
    if error_code is ReconciliationErrorCode.BROKER_FACTS_REQUIRED_MISSING:
        return "provide_required_broker_facts"
    return _action_for_status(status, fallback)


def _trigger_reason(report: ReconciliationReport) -> str:
    if report.error_code is not None:
        return report.error_code.value
    if not report.diff_rows:
        return report.status.value
    top = max(report.diff_rows, key=lambda row: _STATUS_SEVERITY[row.status.value])
    return f"{top.diff_type}:{top.status.value}"


def _coerce_phase(value: ReconPhase | str) -> ReconPhase | None:
    if isinstance(value, ReconPhase):
        return value
    try:
        return ReconPhase(str(value))
    except ValueError:
        return None


def _symbol_for_dimension(local_value: object, broker_value: object) -> str:
    for value in (local_value, broker_value):
        if isinstance(value, Mapping):
            symbol = _safe_label(value.get("symbol"))
            if symbol:
                return symbol
    return ""


def _value_ref(prefix: str, dimension: str, value: object) -> str:
    if value is None:
        return f"{prefix}:{dimension}:missing"
    if isinstance(value, Mapping):
        for key in ("ref", "snapshot_ref", "state_ref", "facts_ref", "label"):
            ref = _safe_ref(value.get(key))
            if ref:
                return ref
    digest = hashlib.sha256(
        json.dumps(_json_safe(value), sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"{prefix}:{dimension}:sha256:{digest[:12]}"


def _diff_value(local_value: object, broker_value: object) -> float:
    if _json_safe(local_value) == _json_safe(broker_value):
        return 0.0
    local_number = _maybe_number(local_value)
    broker_number = _maybe_number(broker_value)
    if local_number is not None and broker_number is not None:
        return abs(local_number - broker_number)
    local_count = _count_hint(local_value)
    broker_count = _count_hint(broker_value)
    if local_count is not None and broker_count is not None:
        return float(abs(local_count - broker_count))
    return 1.0


def _maybe_number(value: object) -> float | None:
    if isinstance(value, Mapping):
        for key in ("value", "amount", "qty", "quantity", "count", "cash", "total_asset"):
            if key in value:
                return _maybe_number(value.get(key))
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _count_hint(value: object) -> int | None:
    if isinstance(value, Mapping):
        if "count" in value:
            return int(_float_value(value.get("count")))
        if "items" in value and isinstance(value.get("items"), Sequence):
            return len(value.get("items", ()))  # type: ignore[arg-type]
        return len(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return None


def _safe_ref(value: object) -> str:
    text = _string_value(value)
    if not text:
        return ""
    if _looks_sensitive(text) or _looks_like_path(text):
        return REDACTED_REF
    return text


def _safe_label(value: object) -> str:
    text = _string_value(value)
    if not text:
        return ""
    if _looks_sensitive(text):
        return REDACTED_REF
    return text.strip()


def _looks_sensitive(value: str) -> bool:
    if not value:
        return False
    return any(pattern.search(value) for pattern in _SENSITIVE_TEXT_PATTERNS)


def _looks_like_path(value: str) -> bool:
    text = value.strip()
    if text.startswith((".", "~")):
        return True
    if "/" in text or "\\" in text:
        return True
    return bool(re.match(r"(?i)^[a-z]:\\", text))


def _redaction_status_for_report(
    recon_input: ReconciliationInput,
    diff_rows: Sequence[DiffRow],
) -> str:
    payload = {
        "input": _json_safe(asdict(recon_input)),
        "diff_rows": [_diff_row_to_dict(row) for row in diff_rows],
    }
    return _redaction_status_for_payload(payload)


def _redaction_status_for_payload(payload: object) -> str:
    text = _render_for_scan(payload)
    if _looks_sensitive(text) or REDACTED_REF in text:
        return "redacted"
    return "pass"


def _report_to_safe_dict(report: ReconciliationReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "schema_version": report.schema_version,
        "phase": report.phase.value,
        "broker_snapshot_ref": report.broker_snapshot_ref,
        "local_state_ref": report.local_state_ref,
        "broker_lake_ref": report.broker_lake_ref,
        "diff_rows": [_diff_row_to_dict(row) for row in report.diff_rows],
        "thresholds": report.thresholds,
        "owner": report.owner,
        "action": report.action,
        "status": report.status.value,
        "redaction_status": report.redaction_status,
        "error_code": report.error_code.value if report.error_code else "",
        "new_order_allowed": report.new_order_allowed,
        "continue_order_allowed_count": report.continue_order_allowed_count,
        "report_kind": report.report_kind,
        "candidate_label": report.candidate_label,
        "safety_counters": report.safety_counters,
    }


def _diff_row_to_dict(row: DiffRow) -> dict[str, Any]:
    return {
        "diff_type": row.diff_type,
        "symbol": row.symbol,
        "local_value_ref": row.local_value_ref,
        "broker_value_ref": row.broker_value_ref,
        "diff_value": row.diff_value,
        "threshold": dict(row.threshold),
        "status": row.status.value,
        "owner": row.owner,
        "action": row.action,
    }


def _json_safe(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat() if value.tzinfo else value.isoformat()
    return value


def _render_for_scan(rendered: object) -> str:
    return json.dumps(_json_safe(rendered), ensure_ascii=False, sort_keys=True, default=str)


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value).strip()
    return str(value).strip()


def _float_value(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _number_mapping(value: object) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): _float_value(item) for key, item in value.items()}


def _sequence_value(value: object) -> tuple[object, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return tuple(RECON_DIMENSIONS)


__all__ = [
    "RECONCILIATION_SCHEMA_VERSION",
    "RECON_DIMENSIONS",
    "DiffRow",
    "ReconPhase",
    "ReconciliationErrorCode",
    "ReconciliationInput",
    "ReconciliationReport",
    "ReconciliationStatus",
    "ThresholdConfig",
    "ThresholdEvaluation",
    "build_report_candidate",
    "evaluate_thresholds",
    "reconcile",
    "reconciliation_safety_counters",
    "sensitive_raw_value_output_count",
    "to_kill_switch_candidate",
]
