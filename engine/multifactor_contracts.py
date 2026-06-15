"""CR030-S02 多因子研究合同。

本模块只定义 `FactorSpec` / `FactorRunSpec` 的离线合同、稳定配置哈希
和 fail-closed 校验入口。不导入或运行 Qlib / Alphalens / Zipline / LEAN
等外部运行时，不读取凭据，不触发 provider / lake / publish / QMT 操作。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "multifactor_contracts_v1"
RESEARCH_INPUT_SCHEMA = "research_input_v1"
LEGACY_FACTOR_VERSION = "legacy-experiment-17-21-v1"
FAILURE_POLICY_FAIL_CLOSED = "fail_closed"
INTERNAL_CONTRACT_TRUTH = "project_multifactor_contract"

FACTOR_SPEC_REQUIRED_FIELDS = (
    "factor_id",
    "name",
    "version",
    "direction",
    "input_fields",
    "window",
    "params",
    "preprocessing",
    "universe",
    "availability_policy",
    "data_lineage",
    "blocked_claims",
    "failure_policy",
)

FACTOR_RUN_SPEC_REQUIRED_FIELDS = (
    "run_id",
    "factor_id",
    "factor_version",
    "date_range",
    "dataset_release",
    "benchmark",
    "label_window",
    "cost_config",
    "seed",
    "code_version",
    "config_hash",
    "output_root",
    "permission_counters",
    "failure_policy",
)

LINEAGE_REQUIRED_FIELDS = ("source_dataset", "research_input_schema", "evidence_refs")
DATE_RANGE_REQUIRED_FIELDS = ("start", "end")
EXTERNAL_MAPPING_FIELDS = ("external_mapping_notes", "cross_check_mapping_notes")

FORBIDDEN_OPERATION_COUNTERS = (
    "external_project_clone",
    "external_project_install",
    "external_project_run",
    "source_migration_or_vendor",
    "dependency_change",
    "provider_fetch",
    "lake_write",
    "catalog_publish",
    "reports_overwrite",
    "qmt_operation",
    "simulation_or_live",
    "account_or_order_operation",
    "credential_read",
)

EXTERNAL_PROJECT_MARKERS = (
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
)

EXTERNAL_TRUTH_FIELDS = (
    "source_of_truth",
    "truth_source",
    "internal_truth",
    "provider",
    "provider_uri",
    "runner",
    "runtime",
    "optimizer",
    "qrun",
)

BLOCKED_CLAIMS_DEFAULT = (
    "qmt_ready",
    "simulation_ready",
    "live_ready",
    "production_truth",
    "tradable_evidence",
)

LEGACY_FACTOR_INPUT_FIELDS = {
    "momentum_20d": ("close",),
    "reversal_5d": ("close",),
    "rsi_14": ("close",),
    "macd_diff": ("close",),
    "macd_hist": ("close",),
    "ma_gap_20": ("close",),
    "volatility_20d": ("close",),
    "volume_change_20d": ("volume",),
    "turnover_proxy": ("amount", "volume"),
    "max_drawdown_20d": ("close",),
}

LEGACY_FACTOR_WINDOWS = {
    "momentum_20d": 20,
    "reversal_5d": 5,
    "rsi_14": 14,
    "macd_diff": 26,
    "macd_hist": 26,
    "ma_gap_20": 20,
    "volatility_20d": 20,
    "volume_change_20d": 20,
    "turnover_proxy": 1,
    "max_drawdown_20d": 20,
}


class FactorDirection(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class BlockedReason:
    code: str
    message: str
    field: str = ""
    severity: str = "blocker"
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class PermissionCounters:
    external_project_clone: int = 0
    external_project_install: int = 0
    external_project_run: int = 0
    source_migration_or_vendor: int = 0
    dependency_change: int = 0
    provider_fetch: int = 0
    lake_write: int = 0
    catalog_publish: int = 0
    reports_overwrite: int = 0
    qmt_operation: int = 0
    simulation_or_live: int = 0
    account_or_order_operation: int = 0
    credential_read: int = 0

    def to_dict(self) -> dict[str, int]:
        return dict(asdict(self))


@dataclass(frozen=True, slots=True)
class ContractValidationResult:
    status: str
    blocked_reasons: tuple[BlockedReason, ...] = ()
    object_type: str = ""
    object_id: str = ""
    config_hash: str = ""
    permission_counters: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blocked_reasons": [reason.to_dict() for reason in self.blocked_reasons],
            "object_type": self.object_type,
            "object_id": self.object_id,
            "config_hash": self.config_hash,
            "permission_counters": dict(self.permission_counters),
        }


@dataclass(frozen=True, slots=True)
class ExternalMappingNote:
    external_project: str
    external_object: str
    internal_field: str
    mapping_role: str = "cross_check_only"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class FactorSpec:
    factor_id: str
    name: str
    version: str
    direction: FactorDirection | str
    input_fields: tuple[str, ...]
    window: int | Mapping[str, Any]
    params: Mapping[str, Any]
    preprocessing: Mapping[str, Any]
    universe: str | Mapping[str, Any]
    availability_policy: Mapping[str, Any]
    data_lineage: Mapping[str, Any]
    blocked_claims: tuple[str, ...]
    failure_policy: str = FAILURE_POLICY_FAIL_CLOSED
    auxiliary_requirements: tuple[str, ...] = ()
    neutralization_hint: str = ""
    expected_frequency: str = "daily"
    external_mapping_notes: tuple[ExternalMappingNote | Mapping[str, Any], ...] = ()
    source_of_truth: str = INTERNAL_CONTRACT_TRUTH

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class FactorRunSpec:
    run_id: str
    factor_id: str
    factor_version: str
    date_range: Mapping[str, Any]
    dataset_release: str
    benchmark: Mapping[str, Any] | str
    label_window: Mapping[str, Any]
    cost_config: Mapping[str, Any]
    seed: int
    code_version: str
    config_hash: str
    output_root: str
    permission_counters: PermissionCounters | Mapping[str, Any] = field(default_factory=PermissionCounters)
    failure_policy: str = FAILURE_POLICY_FAIL_CLOSED
    strategy_id: str = ""
    experiment_group: str = ""
    rerun_of: str = ""
    combination_config: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def compute_config_hash(config: Mapping[str, Any] | Any) -> str:
    """基于稳定 JSON 序列化计算配置哈希，字段顺序不影响结果。"""

    payload = _canonical_json(config)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_factor_spec(spec: FactorSpec | Mapping[str, Any] | Any) -> ContractValidationResult:
    data = _as_mapping(spec)
    if data is None:
        return _blocked_result(
            "FactorSpec",
            "",
            _reason("MF_SCHEMA_REQUIRED_FIELD_MISSING", "FactorSpec 必须是 dataclass 或 mapping", field="spec"),
        )

    reasons: list[BlockedReason] = []
    reasons.extend(_required_field_reasons(data, FACTOR_SPEC_REQUIRED_FIELDS))
    reasons.extend(_direction_reasons(data))
    reasons.extend(_lineage_reasons(data.get("data_lineage"), field_prefix="data_lineage"))
    reasons.extend(_external_truth_reasons(data))

    return _validation_result(
        object_type="FactorSpec",
        object_id=str(data.get("factor_id") or ""),
        reasons=reasons,
    )


def validate_factor_run_spec(
    run_spec: FactorRunSpec | Mapping[str, Any] | Any,
    factor_spec: FactorSpec | Mapping[str, Any] | Any,
) -> ContractValidationResult:
    run_data = _as_mapping(run_spec)
    factor_data = _as_mapping(factor_spec)
    if run_data is None:
        return _blocked_result(
            "FactorRunSpec",
            "",
            _reason("MF_SCHEMA_REQUIRED_FIELD_MISSING", "FactorRunSpec 必须是 dataclass 或 mapping", field="run_spec"),
        )
    if factor_data is None:
        return _blocked_result(
            "FactorRunSpec",
            str(run_data.get("run_id") or ""),
            _reason("MF_SCHEMA_REQUIRED_FIELD_MISSING", "factor_spec 必须是 dataclass 或 mapping", field="factor_spec"),
        )

    reasons: list[BlockedReason] = []
    reasons.extend(_required_field_reasons(run_data, FACTOR_RUN_SPEC_REQUIRED_FIELDS))
    reasons.extend(_date_range_reasons(run_data.get("date_range")))
    reasons.extend(_external_truth_reasons(run_data))

    if run_data.get("factor_id") and factor_data.get("factor_id") and run_data["factor_id"] != factor_data["factor_id"]:
        reasons.append(
            _reason(
                "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                "FactorRunSpec.factor_id 必须匹配 FactorSpec.factor_id",
                field="factor_id",
                remediation="使用同一 FactorSpec 构建 run spec。",
            )
        )
    if run_data.get("factor_version") and factor_data.get("version") and run_data["factor_version"] != factor_data["version"]:
        reasons.append(
            _reason(
                "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                "FactorRunSpec.factor_version 必须匹配 FactorSpec.version",
                field="factor_version",
                remediation="使用同一 FactorSpec 版本构建 run spec。",
            )
        )

    counters = _normalise_permission_counters(run_data.get("permission_counters"))
    reasons.extend(_permission_counter_reasons(counters))
    expected_hash = ""
    if _is_blank(run_data.get("config_hash")):
        reasons.append(
            _reason(
                "MF_CONFIG_HASH_MISSING",
                "FactorRunSpec.config_hash 缺失",
                field="config_hash",
                remediation="基于 factor/data/label/cost/combination 配置计算稳定 hash。",
            )
        )
    else:
        expected_hash = compute_config_hash(_factor_run_hash_payload(run_data, factor_data))
        if str(run_data.get("config_hash")) != expected_hash:
            reasons.append(
                _reason(
                    "MF_CONFIG_HASH_MISMATCH",
                    "FactorRunSpec.config_hash 与当前 P0 配置不匹配",
                    field="config_hash",
                    remediation="重新计算 config_hash，并确认没有静默变更配置。",
                )
            )

    return _validation_result(
        object_type="FactorRunSpec",
        object_id=str(run_data.get("run_id") or ""),
        reasons=reasons,
        config_hash=expected_hash,
        permission_counters=counters,
    )


def map_legacy_factor_definition(legacy_definition: Mapping[str, Any] | Any) -> FactorSpec | ContractValidationResult:
    data = _as_mapping(legacy_definition)
    if data is None:
        return _blocked_result(
            "FactorSpec",
            "",
            _reason(
                "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                "legacy factor definition 必须是 dataclass、mapping 或具备属性的对象",
                field="legacy_definition",
            ),
        )

    required = ("name", "experiment", "source", "hypothesis", "stage2_link", "direction_sign", "direction_note")
    reasons = _required_field_reasons(data, required)
    factor_name = str(data.get("name") or "")
    if factor_name and factor_name not in LEGACY_FACTOR_INPUT_FIELDS:
        reasons.append(
            _reason(
                "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                "旧实验因子缺少可追溯 input_fields 映射",
                field="input_fields",
                remediation="在 S02 合同映射表中补齐字段来源，不能用外部对象默认值替代。",
            )
        )

    direction_sign = data.get("direction_sign")
    if not isinstance(direction_sign, int) or direction_sign not in (-1, 0, 1):
        reasons.append(
            _reason(
                "MF_DIRECTION_INVALID",
                "旧实验 direction_sign 必须为 -1、0 或 1",
                field="direction_sign",
                remediation="显式说明因子方向。",
            )
        )
    if reasons:
        return _validation_result("FactorSpec", factor_name, reasons)

    if direction_sign > 0:
        direction = FactorDirection.POSITIVE
    elif direction_sign < 0:
        direction = FactorDirection.NEGATIVE
    else:
        direction = FactorDirection.NEUTRAL

    return FactorSpec(
        factor_id=factor_name,
        name=factor_name,
        version=LEGACY_FACTOR_VERSION,
        direction=direction,
        input_fields=LEGACY_FACTOR_INPUT_FIELDS[factor_name],
        window=LEGACY_FACTOR_WINDOWS[factor_name],
        params={
            "legacy_source": data["source"],
            "hypothesis": data["hypothesis"],
            "direction_note": data["direction_note"],
        },
        preprocessing={
            "legacy_direction_sign": direction_sign,
            "normalization_stage": "raw_to_directional_then_winsorized_zscore",
        },
        universe={"mode": "research_input_v1", "pit_policy": "pit_required"},
        availability_policy={"available_at": "decision_time", "policy": "no_lookahead"},
        data_lineage={
            "source_dataset": RESEARCH_INPUT_SCHEMA,
            "research_input_schema": RESEARCH_INPUT_SCHEMA,
            "legacy_experiment": data["experiment"],
            "legacy_factor_definition": factor_name,
            "evidence_refs": [
                "experiments/run_experiment_17_21_factor_suite.py:FactorDefinition",
                "process/HLD.md#35.7.1",
            ],
        },
        blocked_claims=BLOCKED_CLAIMS_DEFAULT,
        auxiliary_requirements=("pit_universe", "quality_status", "adjustment_policy"),
        external_mapping_notes=(
            ExternalMappingNote(
                external_project="Qlib / Zipline / LEAN",
                external_object="factor config / Pipeline Factor / Alpha Model",
                internal_field="FactorSpec",
                note="仅用于字段 cross-check，不作为 internal truth。",
            ),
        ),
    )


def build_factor_run_hash_payload(
    run_spec: FactorRunSpec | Mapping[str, Any] | Any,
    factor_spec: FactorSpec | Mapping[str, Any] | Any,
) -> dict[str, Any]:
    run_data = _as_mapping(run_spec) or {}
    factor_data = _as_mapping(factor_spec) or {}
    return _factor_run_hash_payload(run_data, factor_data)


def _factor_run_hash_payload(run_data: Mapping[str, Any], factor_data: Mapping[str, Any]) -> dict[str, Any]:
    hash_fields = tuple(field_name for field_name in FACTOR_RUN_SPEC_REQUIRED_FIELDS if field_name != "config_hash")
    run_payload = {key: run_data.get(key) for key in hash_fields if key in run_data}
    if "combination_config" in run_data and not _is_blank(run_data.get("combination_config")):
        run_payload["combination_config"] = run_data["combination_config"]
    return {
        "schema_version": SCHEMA_VERSION,
        "factor": factor_data,
        "run": run_payload,
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(item) for item in value]
    return str(value)


def _as_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return _json_safe(dict(value))
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    slots = getattr(type(value), "__slots__", ())
    if slots:
        return _json_safe({slot: getattr(value, slot) for slot in slots if hasattr(value, slot)})
    return None


def _required_field_reasons(data: Mapping[str, Any], required_fields: Sequence[str]) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for field_name in required_fields:
        if field_name not in data or _is_blank(data.get(field_name)):
            reasons.append(
                _reason(
                    "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                    f"必填字段缺失: {field_name}",
                    field=field_name,
                    remediation="补齐 P0 合同字段后再进入下游。",
                )
            )
    return reasons


def _direction_reasons(data: Mapping[str, Any]) -> list[BlockedReason]:
    direction = data.get("direction")
    if _is_blank(direction):
        return []
    value = direction.value if isinstance(direction, Enum) else str(direction)
    allowed = {item.value for item in FactorDirection}
    if value not in allowed:
        return [
            _reason(
                "MF_DIRECTION_INVALID",
                f"direction 不在允许枚举内: {value}",
                field="direction",
                remediation="使用 positive / negative / neutral / custom，并显式说明含义。",
            )
        ]
    if value == FactorDirection.CUSTOM.value:
        params = data.get("params")
        direction_note = data.get("direction_note")
        if not isinstance(params, Mapping) or _is_blank(params.get("direction_note") or direction_note):
            return [
                _reason(
                    "MF_DIRECTION_INVALID",
                    "custom direction 必须提供 direction_note",
                    field="direction",
                    remediation="补充自定义方向解释，避免评价口径歧义。",
                )
            ]
    return []


def _lineage_reasons(lineage: Any, field_prefix: str) -> list[BlockedReason]:
    if not isinstance(lineage, Mapping) or not lineage:
        return [
            _reason(
                "MF_LINEAGE_MISSING",
                "data_lineage 缺失或不是对象",
                field=field_prefix,
                remediation="补齐 source_dataset、research_input_schema 和 evidence_refs。",
            )
        ]
    reasons: list[BlockedReason] = []
    for field_name in LINEAGE_REQUIRED_FIELDS:
        if field_name not in lineage or _is_blank(lineage.get(field_name)):
            reasons.append(
                _reason(
                    "MF_LINEAGE_MISSING",
                    f"lineage 字段缺失: {field_name}",
                    field=f"{field_prefix}.{field_name}",
                    remediation="补齐 release、run_id、checksum 或 artifact ref 等 lineage 证据。",
                )
            )
    return reasons


def _date_range_reasons(date_range: Any) -> list[BlockedReason]:
    if not isinstance(date_range, Mapping):
        return [
            _reason(
                "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                "date_range 必须包含 start / end",
                field="date_range",
                remediation="补齐研究运行日期区间。",
            )
        ]
    return _required_field_reasons(date_range, DATE_RANGE_REQUIRED_FIELDS)


def _external_truth_reasons(data: Mapping[str, Any], prefix: str = "") -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if key in EXTERNAL_MAPPING_FIELDS:
            reasons.extend(_mapping_note_reasons(value, full_key))
            continue
        if str(key) in EXTERNAL_TRUTH_FIELDS and _contains_external_marker(value):
            reasons.append(
                _reason(
                    "MF_EXTERNAL_RUNTIME_NOT_AUTHORIZED",
                    f"外部对象不得作为 internal truth/provider/runner/optimizer: {full_key}",
                    field=full_key,
                    remediation="只保留 external mapping note，并使用项目自有合同作为 truth。",
                )
            )
        if isinstance(value, Mapping):
            reasons.extend(_external_truth_reasons(value, full_key))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    reasons.extend(_external_truth_reasons(item, f"{full_key}[{index}]"))
    return reasons


def _mapping_note_reasons(value: Any, field_name: str) -> list[BlockedReason]:
    notes = value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else (value,)
    reasons: list[BlockedReason] = []
    for index, note in enumerate(notes):
        note_data = _as_mapping(note)
        if note_data is None:
            reasons.append(
                _reason(
                    "MF_SCHEMA_REQUIRED_FIELD_MISSING",
                    "external mapping note 必须可转换为对象",
                    field=f"{field_name}[{index}]",
                    remediation="使用 cross_check_only note，不传入 runtime 对象。",
                )
            )
            continue
        role = str(note_data.get("mapping_role") or "")
        if role != "cross_check_only":
            reasons.append(
                _reason(
                    "MF_EXTERNAL_RUNTIME_NOT_AUTHORIZED",
                    "外部映射只能是 cross_check_only",
                    field=f"{field_name}[{index}].mapping_role",
                    remediation="不得将外部对象提升为 truth/provider/runner/optimizer。",
                )
            )
    return reasons


def _contains_external_marker(value: Any) -> bool:
    text = _canonical_json(value).lower()
    return any(marker in text for marker in EXTERNAL_PROJECT_MARKERS)


def _normalise_permission_counters(value: Any) -> dict[str, int]:
    data = _as_mapping(value) or {}
    counters: dict[str, int] = {}
    for key in FORBIDDEN_OPERATION_COUNTERS:
        raw_value = data.get(key, 0)
        try:
            counters[key] = int(raw_value)
        except (TypeError, ValueError):
            counters[key] = 1
    return counters


def _permission_counter_reasons(counters: Mapping[str, int]) -> list[BlockedReason]:
    reasons: list[BlockedReason] = []
    for key, count in counters.items():
        if count == 0:
            continue
        if key in {"provider_fetch", "lake_write", "catalog_publish", "credential_read", "reports_overwrite"}:
            code = "MF_PROVIDER_OR_LAKE_NOT_AUTHORIZED"
        elif key in {"qmt_operation", "simulation_or_live", "account_or_order_operation"}:
            code = "MF_QMT_NOT_AUTHORIZED"
        else:
            code = "MF_EXTERNAL_RUNTIME_NOT_AUTHORIZED"
        reasons.append(
            _reason(
                code,
                f"permission counter 非 0: {key}={count}",
                field=f"permission_counters.{key}",
                remediation="保持 no-real-operation 计数为 0；如需真实操作，交由 meta-po 发起独立授权。",
            )
        )
    return reasons


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return len(value) == 0
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) == 0
    return False


def _reason(code: str, message: str, *, field: str = "", remediation: str = "") -> BlockedReason:
    return BlockedReason(code=code, message=message, field=field, remediation=remediation)


def _validation_result(
    object_type: str,
    object_id: str,
    reasons: Sequence[BlockedReason],
    *,
    config_hash: str = "",
    permission_counters: Mapping[str, int] | None = None,
) -> ContractValidationResult:
    return ContractValidationResult(
        status="blocked" if reasons else "pass",
        blocked_reasons=tuple(reasons),
        object_type=object_type,
        object_id=object_id,
        config_hash=config_hash,
        permission_counters=dict(permission_counters or {}),
    )


def _blocked_result(object_type: str, object_id: str, *reasons: BlockedReason) -> ContractValidationResult:
    return _validation_result(object_type, object_id, reasons)
