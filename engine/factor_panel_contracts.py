"""CR030-S03 因子面板与标签窗口防泄漏合同。

本模块只定义离线合同和 fail-closed gate。不读取凭据，不触发 provider /
lake / publish / QMT / simulation / live 操作，也不把外部 PIT 或 label truth
提升为项目事实源。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time
from typing import Any, Mapping, Sequence

from engine.admission_contracts import GateStatus
from engine.multifactor_contracts import (
    FAILURE_POLICY_FAIL_CLOSED,
    FORBIDDEN_OPERATION_COUNTERS,
    FactorRunSpec,
    PermissionCounters,
)
from engine.serialization import (
    as_mapping as _shared_as_mapping,
    is_blank as _shared_is_blank,
    json_safe as _shared_json_safe,
    normalise_permission_counters,
)


PANEL_CONTRACT_SCHEMA = "factor_panel_contract_v1"
LABEL_WINDOW_SCHEMA = "label_window_spec_v1"

MF_AVAILABLE_AT_VIOLATION = "MF_AVAILABLE_AT_VIOLATION"
MF_LABEL_OVERLAP_RISK = "MF_LABEL_OVERLAP_RISK"
MF_LINEAGE_MISSING = "MF_LINEAGE_MISSING"
MF_ADJUSTMENT_POLICY_MIXED = "MF_ADJUSTMENT_POLICY_MIXED"
MF_PANEL_LAYER_INCOMPLETE = "MF_PANEL_LAYER_INCOMPLETE"
MF_QUALITY_GATE_FAILED = "MF_QUALITY_GATE_FAILED"
MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN = "MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN"
MF_FORBIDDEN_PERMISSION_COUNTER = "MF_FORBIDDEN_PERMISSION_COUNTER"
MF_SCHEMA_REQUIRED_FIELD_MISSING = "MF_SCHEMA_REQUIRED_FIELD_MISSING"

PANEL_LAYER_FIELDS = ("raw_value", "directional_value", "winsorized_value", "zscore_value")
PANEL_LINEAGE_REQUIRED_FIELDS = ("source_dataset", "research_input_schema", "evidence_refs")
LABEL_LINEAGE_REQUIRED_FIELDS = ("source_dataset", "research_input_schema", "evidence_refs")
PASS_QUALITY_STATUSES = {"pass", "passed", "ok", "valid"}
EXTERNAL_TRUTH_MARKERS = (
    "qlib",
    "alphalens",
    "zipline",
    "lean",
    "quantconnect",
    "vectorbt",
    "pybroker",
    "rqalpha",
    "vn.py",
    "vnpy",
    "backtrader",
    "external truth",
    "external_label_truth",
    "external_pit_truth",
    "provider_uri",
    "qrun",
)


@dataclass(frozen=True, slots=True)
class BlockedReason:
    code: str
    message: str
    object_id: str = ""
    field: str = ""
    evidence_ref: str = ""
    severity: str = "blocker"
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class DownstreamPolicy:
    evaluation: bool = True
    combo: bool = True
    admission: bool = True

    @classmethod
    def blocked(cls) -> "DownstreamPolicy":
        return cls(evaluation=False, combo=False, admission=False)

    def to_dict(self) -> dict[str, bool]:
        return {"evaluation": self.evaluation, "combo": self.combo, "admission": self.admission}


@dataclass(frozen=True, slots=True)
class PanelGateResult:
    status: str
    blocked_reasons: tuple[BlockedReason, ...] = ()
    downstream_allowed: DownstreamPolicy = field(default_factory=DownstreamPolicy)
    object_type: str = ""
    object_id: str = ""
    permission_counters: dict[str, int] = field(default_factory=dict)
    failure_policy: str = FAILURE_POLICY_FAIL_CLOSED

    @property
    def passed(self) -> bool:
        return self.status == GateStatus.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "downstream_allowed": self.downstream_allowed.to_dict(),
            "object_type": self.object_type,
            "object_id": self.object_id,
            "permission_counters": dict(self.permission_counters),
            "failure_policy": self.failure_policy,
        }


@dataclass(frozen=True, slots=True)
class FactorPanelContract:
    trade_date: str | date
    symbol: str
    factor_id: str
    factor_version: str
    raw_value: Any
    directional_value: Any
    winsorized_value: Any
    zscore_value: Any
    available_at: str | datetime
    decision_time: str | datetime
    source_dataset: str
    quality_status: str
    preprocessing_metadata: Mapping[str, Any]
    data_lineage: Mapping[str, Any]
    schema_version: str = PANEL_CONTRACT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class LabelWindowSpec:
    label_id: str
    trade_date: str | date
    symbol: str
    decision_time: str | datetime
    label_window_start: str | datetime
    label_window_end: str | datetime
    label_available_at: str | datetime
    return_kind: str
    adjustment_policy: str
    cost_policy: str | Mapping[str, Any]
    benchmark_policy: str | Mapping[str, Any]
    data_lineage: Mapping[str, Any]
    schema_version: str = LABEL_WINDOW_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def validate_factor_panel(
    panel: FactorPanelContract | Mapping[str, Any] | Any,
    run_spec: FactorRunSpec | Mapping[str, Any] | Any,
) -> PanelGateResult:
    panel_data = _as_mapping(panel)
    run_data = _as_mapping(run_spec)
    if panel_data is None:
        return _blocked_result(
            "FactorPanelContract",
            "",
            _reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "FactorPanelContract 必须是 dataclass 或 mapping", field="panel"),
        )
    if run_data is None:
        return _blocked_result(
            "FactorPanelContract",
            _panel_object_id(panel_data),
            _reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "FactorRunSpec 必须是 dataclass 或 mapping", field="run_spec"),
        )

    object_id = _panel_object_id(panel_data)
    reasons: list[BlockedReason] = []
    counters = _normalise_permission_counters(run_data.get("permission_counters"))
    reasons.extend(_permission_counter_reasons(counters, object_id))
    reasons.extend(_required_field_reasons(panel_data, _panel_required_fields(), object_id))
    reasons.extend(_panel_layer_reasons(panel_data, object_id))
    reasons.extend(_available_at_reasons(panel_data, object_id))
    reasons.extend(_lineage_reasons(panel_data.get("data_lineage"), PANEL_LINEAGE_REQUIRED_FIELDS, "data_lineage", object_id))
    reasons.extend(_quality_reasons(panel_data, object_id))
    reasons.extend(_panel_adjustment_policy_reasons(panel_data, run_data, object_id))
    reasons.extend(_external_truth_reasons(panel_data, object_id))

    return _gate_result("FactorPanelContract", object_id, reasons, counters)


def validate_label_window(
    label_spec: LabelWindowSpec | Mapping[str, Any] | Any,
    run_spec: FactorRunSpec | Mapping[str, Any] | Any,
) -> PanelGateResult:
    label_data = _as_mapping(label_spec)
    run_data = _as_mapping(run_spec)
    if label_data is None:
        return _blocked_result(
            "LabelWindowSpec",
            "",
            _reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "LabelWindowSpec 必须是 dataclass 或 mapping", field="label_spec"),
        )
    if run_data is None:
        return _blocked_result(
            "LabelWindowSpec",
            _label_object_id(label_data),
            _reason(MF_SCHEMA_REQUIRED_FIELD_MISSING, "FactorRunSpec 必须是 dataclass 或 mapping", field="run_spec"),
        )

    object_id = _label_object_id(label_data)
    reasons: list[BlockedReason] = []
    counters = _normalise_permission_counters(run_data.get("permission_counters"))
    reasons.extend(_permission_counter_reasons(counters, object_id))
    reasons.extend(_required_field_reasons(label_data, _label_required_fields(), object_id))
    reasons.extend(_label_window_reasons(label_data, object_id))
    reasons.extend(_lineage_reasons(label_data.get("data_lineage"), LABEL_LINEAGE_REQUIRED_FIELDS, "data_lineage", object_id))
    reasons.extend(_label_policy_reasons(label_data, run_data, object_id))
    reasons.extend(_external_truth_reasons(label_data, object_id))

    return _gate_result("LabelWindowSpec", object_id, reasons, counters)


def combine_panel_label_gate(panel_result: PanelGateResult, label_result: PanelGateResult) -> PanelGateResult:
    reasons = tuple(panel_result.blocked_reasons) + tuple(label_result.blocked_reasons)
    counters = _merge_counters(panel_result.permission_counters, label_result.permission_counters)
    object_id = "|".join(item for item in (panel_result.object_id, label_result.object_id) if item)
    return _gate_result("PanelLabelGate", object_id, reasons, counters)


def assert_no_external_pit_label_truth(source: Mapping[str, Any] | str | Any) -> PanelGateResult:
    source_data = _as_mapping(source)
    source_payload: Any = source_data if source_data is not None else source
    object_id = ""
    if isinstance(source_data, Mapping):
        object_id = str(source_data.get("source_id") or source_data.get("name") or "")
    if _contains_external_truth_marker(source_payload):
        return _blocked_result(
            "ExternalTruthSource",
            object_id,
            _reason(
                MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN,
                "外部 PIT / label truth 不得接管项目内部 gate",
                object_id=object_id,
                field="source",
                remediation="仅保留外部项目 cross-check note，使用项目自有 panel / label 合同作为 truth。",
            ),
        )
    return _gate_result("ExternalTruthSource", object_id, (), {})


def to_blocked_claims(gate_result: PanelGateResult) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for reason in gate_result.blocked_reasons:
        claims.append(
            {
                "claim": "multifactor_downstream_blocked",
                "code": reason.code,
                "object_id": reason.object_id or gate_result.object_id,
                "field": reason.field,
                "evidence_ref": reason.evidence_ref,
                "message": reason.message,
                "downstream_allowed": gate_result.downstream_allowed.to_dict(),
                "remediation": reason.remediation,
            }
        )
    return claims


def _panel_required_fields() -> tuple[str, ...]:
    return (
        "trade_date",
        "symbol",
        "factor_id",
        "factor_version",
        "available_at",
        "decision_time",
        "source_dataset",
        "quality_status",
        "preprocessing_metadata",
        "data_lineage",
    )


def _label_required_fields() -> tuple[str, ...]:
    return (
        "label_id",
        "trade_date",
        "symbol",
        "decision_time",
        "label_window_start",
        "label_window_end",
        "label_available_at",
        "return_kind",
        "adjustment_policy",
        "cost_policy",
        "benchmark_policy",
        "data_lineage",
    )


def _panel_layer_reasons(data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for field_name in PANEL_LAYER_FIELDS:
        if field_name not in data or _is_blank(data.get(field_name)):
            reasons.append(
                _reason(
                    MF_PANEL_LAYER_INCOMPLETE,
                    f"因子面板层缺失: {field_name}",
                    object_id=object_id,
                    field=field_name,
                    remediation="补齐 raw / directional / winsorized / zscore 四层后再进入评价。",
                )
            )
    return reasons


def _available_at_reasons(data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    available_at = _to_datetime(data.get("available_at"))
    decision_time = _to_datetime(data.get("decision_time"))
    if available_at is None or decision_time is None:
        return [
            _reason(
                MF_AVAILABLE_AT_VIOLATION,
                "available_at 或 decision_time 缺失 / 不可解析",
                object_id=object_id,
                field="available_at",
                remediation="为每行 panel 提供可解析的 available_at 和 decision_time。",
            )
        ]
    if available_at > decision_time:
        return [
            _reason(
                MF_AVAILABLE_AT_VIOLATION,
                "available_at 晚于 decision_time，存在前视风险",
                object_id=object_id,
                field="available_at",
                evidence_ref=f"available_at={available_at.isoformat()} decision_time={decision_time.isoformat()}",
                remediation="只使用 decision_time 前已可用的因子值。",
            )
        ]
    return []


def _label_window_reasons(data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    decision_time = _to_datetime(data.get("decision_time"))
    window_start = _to_datetime(data.get("label_window_start"))
    window_end = _to_datetime(data.get("label_window_end"))
    label_available_at = _to_datetime(data.get("label_available_at"))
    if None in (decision_time, window_start, window_end, label_available_at):
        return [
            _reason(
                MF_LABEL_OVERLAP_RISK,
                "label window 时间字段缺失 / 不可解析",
                object_id=object_id,
                field="label_window",
                remediation="补齐 decision_time、label_window_start、label_window_end 和 label_available_at。",
            )
        ]
    if window_start <= decision_time:
        return [
            _reason(
                MF_LABEL_OVERLAP_RISK,
                "label_window_start 未晚于 decision_time，存在 label overlap",
                object_id=object_id,
                field="label_window_start",
                evidence_ref=f"start={window_start.isoformat()} decision={decision_time.isoformat()}",
                remediation="使用严格晚于 decision_time 的 forward label window。",
            )
        ]
    if window_end < window_start:
        return [
            _reason(
                MF_LABEL_OVERLAP_RISK,
                "label_window_end 早于 label_window_start",
                object_id=object_id,
                field="label_window_end",
                remediation="修正 label window 起止顺序。",
            )
        ]
    if label_available_at < window_end:
        return [
            _reason(
                MF_LABEL_OVERLAP_RISK,
                "label_available_at 早于 label_window_end，标签可用时点不可证明",
                object_id=object_id,
                field="label_available_at",
                evidence_ref=f"available={label_available_at.isoformat()} end={window_end.isoformat()}",
                remediation="仅在 label window 完成后暴露标签结果。",
            )
        ]
    return []


def _lineage_reasons(lineage: Any, required_fields: Sequence[str], field_prefix: str, object_id: str) -> list[BlockedReason]:
    if not isinstance(lineage, Mapping) or not lineage:
        return [
            _reason(
                MF_LINEAGE_MISSING,
                "data_lineage 缺失或不是对象",
                object_id=object_id,
                field=field_prefix,
                remediation="补齐 source_dataset、research_input_schema 和 evidence_refs。",
            )
        ]
    reasons: list[BlockedReason] = []
    for field_name in required_fields:
        if field_name not in lineage or _is_blank(lineage.get(field_name)):
            reasons.append(
                _reason(
                    MF_LINEAGE_MISSING,
                    f"lineage 字段缺失: {field_name}",
                    object_id=object_id,
                    field=f"{field_prefix}.{field_name}",
                    remediation="补齐 release、run_id、checksum 或 artifact ref 等 lineage 证据。",
                )
            )
    return reasons


def _quality_reasons(data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    quality_status = str(data.get("quality_status") or "").strip().lower()
    if quality_status not in PASS_QUALITY_STATUSES:
        return [
            _reason(
                MF_QUALITY_GATE_FAILED,
                f"quality_status 未通过: {data.get('quality_status')}",
                object_id=object_id,
                field="quality_status",
                remediation="仅允许 quality status 为 pass / passed / ok / valid 的面板进入下游。",
            )
        ]
    return []


def _panel_adjustment_policy_reasons(panel_data: Mapping[str, Any], run_data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    metadata = panel_data.get("preprocessing_metadata")
    if not isinstance(metadata, Mapping):
        return [
            _reason(
                MF_SCHEMA_REQUIRED_FIELD_MISSING,
                "preprocessing_metadata 必须是对象",
                object_id=object_id,
                field="preprocessing_metadata",
                remediation="补齐预处理、复权、标准化和 winsorization 元数据。",
            )
        ]
    policy = _normalise_policy_value(metadata.get("adjustment_policy"))
    policy_set = metadata.get("adjustment_policy_set") or metadata.get("adjustment_policies")
    if _has_multiple_values(policy_set):
        return [
            _reason(
                MF_ADJUSTMENT_POLICY_MIXED,
                "同一 panel 元数据包含多个复权口径",
                object_id=object_id,
                field="preprocessing_metadata.adjustment_policy_set",
                remediation="同一 run 只能使用一个明确的复权口径。",
            )
        ]
    expected = _normalise_policy_value(_nested_get(run_data, ("label_window", "adjustment_policy")))
    if policy and expected and policy != expected:
        return [
            _reason(
                MF_ADJUSTMENT_POLICY_MIXED,
                "panel adjustment_policy 与 run label_window adjustment_policy 不一致",
                object_id=object_id,
                field="preprocessing_metadata.adjustment_policy",
                evidence_ref=f"panel={policy} run={expected}",
                remediation="统一 FactorRunSpec、panel 和 label 的复权口径。",
            )
        ]
    return []


def _label_policy_reasons(label_data: Mapping[str, Any], run_data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    label_window = run_data.get("label_window") if isinstance(run_data.get("label_window"), Mapping) else {}
    expected_adjustment = _normalise_policy_value(label_window.get("adjustment_policy"))
    actual_adjustment = _normalise_policy_value(label_data.get("adjustment_policy"))
    if expected_adjustment and actual_adjustment and expected_adjustment != actual_adjustment:
        reasons.append(
            _reason(
                MF_ADJUSTMENT_POLICY_MIXED,
                "label adjustment_policy 与 FactorRunSpec.label_window 不一致",
                object_id=object_id,
                field="adjustment_policy",
                evidence_ref=f"label={actual_adjustment} run={expected_adjustment}",
                remediation="统一 run spec 与 label window 的复权口径。",
            )
        )

    expected_return = _normalise_policy_value(label_window.get("return_kind"))
    actual_return = _normalise_policy_value(label_data.get("return_kind"))
    if expected_return and actual_return and expected_return != actual_return:
        reasons.append(
            _reason(
                MF_ADJUSTMENT_POLICY_MIXED,
                "label return_kind 与 FactorRunSpec.label_window 不一致",
                object_id=object_id,
                field="return_kind",
                evidence_ref=f"label={actual_return} run={expected_return}",
                remediation="统一 run spec 与 label window 的收益口径。",
            )
        )

    expected_cost = _normalise_policy_value(_nested_get(run_data, ("cost_config", "cost_policy")) or run_data.get("cost_config"))
    actual_cost = _normalise_policy_value(label_data.get("cost_policy"))
    if expected_cost and actual_cost and expected_cost != actual_cost:
        reasons.append(
            _reason(
                MF_ADJUSTMENT_POLICY_MIXED,
                "label cost_policy 与 FactorRunSpec.cost_config 不一致",
                object_id=object_id,
                field="cost_policy",
                evidence_ref=f"label={actual_cost} run={expected_cost}",
                remediation="统一成本口径后再进入评价。",
            )
        )
    return reasons


def _external_truth_reasons(data: Mapping[str, Any], object_id: str) -> list[BlockedReason]:
    if _contains_external_truth_marker(data):
        return [
            _reason(
                MF_EXTERNAL_PIT_LABEL_TRUTH_FORBIDDEN,
                "检测到外部 PIT / label truth 标记",
                object_id=object_id,
                field="source",
                remediation="外部项目只能作为 cross-check，不得接管内部 truth。",
            )
        ]
    return []


def _permission_counter_reasons(counters: Mapping[str, int], object_id: str) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for key, count in counters.items():
        if count == 0:
            continue
        reasons.append(
            _reason(
                MF_FORBIDDEN_PERMISSION_COUNTER,
                f"forbidden permission counter 非 0: {key}={count}",
                object_id=object_id,
                field=f"permission_counters.{key}",
                remediation="保持 CR-030 no-real-operation 计数为 0；真实操作必须另走授权。",
            )
        )
    return reasons


def _required_field_reasons(data: Mapping[str, Any], required_fields: Sequence[str], object_id: str) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for field_name in required_fields:
        if field_name not in data or _is_blank(data.get(field_name)):
            reasons.append(
                _reason(
                    MF_SCHEMA_REQUIRED_FIELD_MISSING,
                    f"必填字段缺失: {field_name}",
                    object_id=object_id,
                    field=field_name,
                    remediation="补齐 P0 合同字段后再进入下游。",
                )
            )
    return reasons


def _gate_result(
    object_type: str,
    object_id: str,
    reasons: Sequence[BlockedReason],
    counters: Mapping[str, int] | None = None,
) -> PanelGateResult:
    status = GateStatus.BLOCKED.value if reasons else GateStatus.PASS.value
    return PanelGateResult(
        status=status,
        blocked_reasons=tuple(reasons),
        downstream_allowed=DownstreamPolicy.blocked() if reasons else DownstreamPolicy(),
        object_type=object_type,
        object_id=object_id,
        permission_counters=dict(counters or {}),
    )


def _blocked_result(object_type: str, object_id: str, *reasons: BlockedReason) -> PanelGateResult:
    return _gate_result(object_type, object_id, reasons, {})


def _reason(
    code: str,
    message: str,
    *,
    object_id: str = "",
    field: str = "",
    evidence_ref: str = "",
    remediation: str = "",
) -> BlockedReason:
    return BlockedReason(
        code=code,
        message=message,
        object_id=object_id,
        field=field,
        evidence_ref=evidence_ref,
        remediation=remediation,
    )


def _panel_object_id(data: Mapping[str, Any]) -> str:
    return "|".join(str(data.get(key) or "") for key in ("trade_date", "symbol", "factor_id", "factor_version"))


def _label_object_id(data: Mapping[str, Any]) -> str:
    return "|".join(str(data.get(key) or "") for key in ("trade_date", "symbol", "label_id"))


def _normalise_permission_counters(value: Any) -> dict[str, int]:
    return normalise_permission_counters(value, FORBIDDEN_OPERATION_COUNTERS)


def _merge_counters(*counter_sets: Mapping[str, int]) -> dict[str, int]:
    merged = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
    for counters in counter_sets:
        for key, count in counters.items():
            merged[key] = merged.get(key, 0) + int(count)
    return merged


def _contains_external_truth_marker(value: Any) -> bool:
    text = str(_json_safe(value)).lower()
    return any(marker in text for marker in EXTERNAL_TRUTH_MARKERS)


def _normalise_policy_value(value: Any) -> str:
    if _is_blank(value):
        return ""
    if isinstance(value, Mapping):
        return str(value.get("policy") or value.get("name") or _json_safe(value)).strip().lower()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "|".join(str(item).strip().lower() for item in value)
    return str(value).strip().lower()


def _has_multiple_values(value: Any) -> bool:
    if _is_blank(value):
        return False
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace("|", ",").split(",") if part.strip()]
        return len(set(parts)) > 1
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len({str(item).strip().lower() for item in value if not _is_blank(item)}) > 1
    return False


def _nested_get(data: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str) and value.strip():
        raw = value.strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.combine(date.fromisoformat(raw), time.min)
            except ValueError:
                return None
    return None


def _as_mapping(value: Any) -> dict[str, Any] | None:
    return _shared_as_mapping(value)


def _json_safe(value: Any) -> Any:
    return _shared_json_safe(value)


def _is_blank(value: Any) -> bool:
    return _shared_is_blank(value)
