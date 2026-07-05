"""CR158 strategy type adapter contracts.

This module normalizes static/fixture strategy adapter metadata only. It does
not read event feeds, train models, call providers, access credentials, touch
lake/NAS/runtime adapters, write registries/stores/catalogs, publish, trade, or
execute Git/external-framework operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from engine.serialization import as_mapping, json_safe


STRATEGY_TYPE_ADAPTER_SCHEMA = "strategy_type_adapter_v1"
ADAPTER_TYPED_EVIDENCE_REF_SCHEMA = "adapter_typed_evidence_ref_v1"

STRATEGY_TYPE_EVENT = "event"
STRATEGY_TYPE_ML = "ml"

ADAPTER_STATUS_PASS = "PASS"
ADAPTER_STATUS_FAIL = "FAIL"
ADAPTER_STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
ADAPTER_STATUS_BLOCKED = "BLOCKED"

CORE_REQUIRED_FIELD_GROUPS = (
    "adapter_id",
    "strategy_type",
    "input_refs",
    "output_signal_refs",
    "evidence_refs",
    "blocked_reason_refs",
    "authorization_flags",
    "handoff_refs",
)

CORE_PRIVATE_FIELD_DENYLIST = (
    "event_payload",
    "event_payload_body",
    "event_payload_schema_ref",
    "event_source_ref",
    "event_time_ref",
    "alignment_policy_ref",
    "training_snapshot_ref",
    "feature_set_ref",
    "label_policy_ref",
    "model_artifact",
    "model_artifact_ref",
    "model_binary",
    "validation_report_ref",
    "prediction_signal_ref",
)

EVENT_EXTENSION_REQUIRED_REFS = (
    "event_source_ref",
    "event_time_ref",
    "payload_schema_ref",
    "alignment_policy_ref",
    "signal_output_ref",
)
EVENT_EXTENSION_ML_FIELD_DENYLIST = (
    "training_snapshot_ref",
    "feature_set_ref",
    "label_policy_ref",
    "model_artifact_ref",
    "model_binary",
    "validation_report_ref",
    "prediction_signal_ref",
)

ML_EXTENSION_REQUIRED_REFS = (
    "training_snapshot_ref",
    "feature_set_ref",
    "label_policy_ref",
    "model_artifact_ref",
    "validation_report_ref",
    "prediction_signal_ref",
)
ML_EXTENSION_EVENT_FIELD_DENYLIST = (
    "event_source_ref",
    "event_time_ref",
    "event_payload",
    "event_payload_body",
    "payload_schema_ref",
    "alignment_policy_ref",
    "signal_output_ref",
)

CR158_FORBIDDEN_OPERATION_COUNTERS = tuple(
    dict.fromkeys(
        (
            "real_event_feed",
            "real_event_feed_read",
            "live_event_listener",
            "live_listener_started",
            "real_model_training",
            "real_training",
            "external_model_service_call",
            "provider_fetch",
            "real_lake_read",
            "real_lake_write",
            "nas_access",
            "nas_read",
            "nas_write",
            "nas_sync_or_write",
            "credential_read",
            "env_read",
            "session_read",
            "runtime_operation",
            "runtime_started",
            "qmt_runtime",
            "miniqmt_runtime",
            "xtquant_runtime",
            "gateway_start",
            "simulation_or_live_run",
            "paper_trading_run",
            "broker_access",
            "account_query",
            "real_order",
            "order_submit",
            "order_cancel",
            "trading_operation",
            "event_store_write",
            "feature_store_write",
            "label_store_write",
            "prediction_store_write",
            "model_store_write",
            "model_registry_write",
            "registry_write",
            "catalog_pointer_mutation",
            "publish_operation",
            "production_deployment",
            "external_framework_run",
            "git_remote_write",
        )
    )
)

ADAPTER_NO_RUNTIME_LIMITATIONS = (
    "adapter_pass_not_runtime_ready",
    "fixture_static_metadata_only",
    "no_real_event_feed",
    "no_live_event_listener",
    "no_real_model_training",
    "no_external_model_service",
    "no_real_lake_or_provider_access",
    "no_credential_or_env_read",
    "no_qmt_or_gateway_runtime",
    "no_simulation_paper_live_or_trading",
    "no_broker_order",
    "no_catalog_store_registry_or_publish",
    "no_external_framework_or_git_remote",
)


class AdapterValidationStatus(str, Enum):
    PASS = ADAPTER_STATUS_PASS
    FAIL = ADAPTER_STATUS_FAIL
    NEEDS_REVIEW = ADAPTER_STATUS_NEEDS_REVIEW
    BLOCKED = ADAPTER_STATUS_BLOCKED


@dataclass(frozen=True, slots=True)
class AdapterBlockedReason:
    code: str
    message: str
    source: str
    field: str = ""
    severity: str = "blocker"
    evidence_ref: str = ""
    unlock_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class StrategyTypeAdapterCore:
    adapter_id: str
    strategy_type: str
    input_refs: tuple[Mapping[str, Any] | str, ...]
    output_signal_refs: tuple[Mapping[str, Any] | str, ...]
    evidence_refs: tuple[Mapping[str, Any] | str, ...]
    authorization_flags: Mapping[str, bool] = field(default_factory=dict)
    handoff_refs: tuple[Mapping[str, Any] | str, ...] = ()
    blocked_reason_refs: tuple[Mapping[str, Any] | str, ...] = ()
    schema_version: str = STRATEGY_TYPE_ADAPTER_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "strategy_type": self.strategy_type,
            "input_refs": tuple(_ref_payload(ref) for ref in self.input_refs),
            "output_signal_refs": tuple(_ref_payload(ref) for ref in self.output_signal_refs),
            "evidence_refs": tuple(_ref_payload(ref) for ref in self.evidence_refs),
            "blocked_reason_refs": tuple(_ref_payload(ref) for ref in self.blocked_reason_refs),
            "authorization_flags": dict(json_safe(self.authorization_flags)),
            "handoff_refs": tuple(_ref_payload(ref) for ref in self.handoff_refs),
        }


@dataclass(frozen=True, slots=True)
class AdapterValidationResult:
    adapter_id: str
    strategy_type: str
    status: AdapterValidationStatus | str
    blocked_reasons: tuple[AdapterBlockedReason | Mapping[str, Any], ...] = ()
    needs_review_reasons: tuple[AdapterBlockedReason | Mapping[str, Any], ...] = ()
    evidence_refs: tuple[Mapping[str, Any] | str, ...] = ()
    output_signal_refs: tuple[Mapping[str, Any] | str, ...] = ()
    handoff_refs: tuple[Mapping[str, Any] | str, ...] = ()
    operation_counts: Mapping[str, int] = field(default_factory=dict)
    limitations: tuple[str, ...] = ADAPTER_NO_RUNTIME_LIMITATIONS
    schema_version: str = STRATEGY_TYPE_ADAPTER_SCHEMA

    @property
    def passed(self) -> bool:
        return _status_value(self.status) == ADAPTER_STATUS_PASS

    def to_dict(self) -> dict[str, Any]:
        status = _known_status(self.status)
        return {
            "schema_version": self.schema_version,
            "adapter_id": self.adapter_id,
            "strategy_type": self.strategy_type,
            "status": status,
            "blocked_reasons": tuple(_reason_payload(reason) for reason in self.blocked_reasons),
            "needs_review_reasons": tuple(_reason_payload(reason) for reason in self.needs_review_reasons),
            "evidence_refs": tuple(_ref_payload(ref) for ref in self.evidence_refs),
            "output_signal_refs": tuple(_ref_payload(ref) for ref in self.output_signal_refs),
            "handoff_refs": tuple(_ref_payload(ref) for ref in self.handoff_refs),
            "operation_counts": normalise_adapter_operation_counts(self.operation_counts),
            "limitations": tuple(dict.fromkeys((*ADAPTER_NO_RUNTIME_LIMITATIONS, *self.limitations))),
        }


@dataclass(frozen=True, slots=True)
class EventAdapterExtension:
    event_source_ref: Mapping[str, Any] | str
    event_time_ref: Mapping[str, Any] | str
    payload_schema_ref: Mapping[str, Any] | str
    alignment_policy_ref: Mapping[str, Any] | str
    signal_output_ref: Mapping[str, Any] | str
    blocked_reason_refs: tuple[Mapping[str, Any] | str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_source_ref": _ref_payload(self.event_source_ref),
            "event_time_ref": _ref_payload(self.event_time_ref),
            "payload_schema_ref": _ref_payload(self.payload_schema_ref),
            "alignment_policy_ref": _ref_payload(self.alignment_policy_ref),
            "signal_output_ref": _ref_payload(self.signal_output_ref),
            "blocked_reason_refs": tuple(_ref_payload(ref) for ref in self.blocked_reason_refs),
        }


@dataclass(frozen=True, slots=True)
class MLAdapterExtension:
    training_snapshot_ref: Mapping[str, Any] | str
    feature_set_ref: Mapping[str, Any] | str
    label_policy_ref: Mapping[str, Any] | str
    model_artifact_ref: Mapping[str, Any] | str
    validation_report_ref: Mapping[str, Any] | str
    prediction_signal_ref: Mapping[str, Any] | str
    blocked_reason_refs: tuple[Mapping[str, Any] | str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "training_snapshot_ref": _ref_payload(self.training_snapshot_ref),
            "feature_set_ref": _ref_payload(self.feature_set_ref),
            "label_policy_ref": _ref_payload(self.label_policy_ref),
            "model_artifact_ref": _ref_payload(self.model_artifact_ref),
            "validation_report_ref": _ref_payload(self.validation_report_ref),
            "prediction_signal_ref": _ref_payload(self.prediction_signal_ref),
            "blocked_reason_refs": tuple(_ref_payload(ref) for ref in self.blocked_reason_refs),
        }


@dataclass(frozen=True, slots=True)
class AdapterTypedEvidenceRef:
    ref_id: str
    kind: str
    path_or_id: str
    status: str
    hash: str = ""
    body_copy_count: int = 0
    private_payload_included: bool = False
    description: str = ""
    schema_version: str = ADAPTER_TYPED_EVIDENCE_REF_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return dict(json_safe(asdict(self)))


@dataclass(frozen=True, slots=True)
class AdapterOperationCounterReport:
    operation_counts: Mapping[str, int]
    nonzero_counters: Mapping[str, int]
    blocked_reason_refs: tuple[AdapterBlockedReason | Mapping[str, Any], ...]
    limitations: tuple[str, ...] = ADAPTER_NO_RUNTIME_LIMITATIONS

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_counts": normalise_adapter_operation_counts(self.operation_counts),
            "nonzero_counters": dict(self.nonzero_counters),
            "blocked_reason_refs": tuple(_reason_payload(reason) for reason in self.blocked_reason_refs),
            "limitations": tuple(dict.fromkeys((*ADAPTER_NO_RUNTIME_LIMITATIONS, *self.limitations))),
        }


def zero_adapter_operation_counts() -> dict[str, int]:
    return {key: 0 for key in CR158_FORBIDDEN_OPERATION_COUNTERS}


def normalise_adapter_operation_counts(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(counters or {})
    normalized: dict[str, int] = {}
    for key in CR158_FORBIDDEN_OPERATION_COUNTERS:
        value = source.get(key, 0)
        try:
            normalized[key] = int(value or 0)
        except (TypeError, ValueError):
            normalized[key] = 1
    return normalized


def validate_adapter_operation_counters(counters: Mapping[str, Any] | None = None) -> AdapterValidationResult:
    normalized = normalise_adapter_operation_counts(counters)
    reasons = tuple(
        AdapterBlockedReason(
            code="adapter_forbidden_operation_counter_nonzero",
            message=f"{field} counter must be zero for CR158 fixture/static adapter scope.",
            source="operation_counts",
            field=field,
            unlock_condition="create_separate_runtime_authorization_cr_before_real_operation",
        )
        for field, value in normalized.items()
        if value != 0
    )
    return AdapterValidationResult(
        adapter_id="adapter-operation-counter-report",
        strategy_type="adapter",
        status=ADAPTER_STATUS_BLOCKED if reasons else ADAPTER_STATUS_PASS,
        blocked_reasons=reasons,
        operation_counts=normalized,
    )


def adapter_no_runtime_summary(counters: Mapping[str, Any] | AdapterOperationCounterReport | None = None) -> dict[str, Any]:
    data = counters.to_dict() if isinstance(counters, AdapterOperationCounterReport) else None
    operation_counts = normalise_adapter_operation_counts(
        data.get("operation_counts") if data else counters if isinstance(counters, Mapping) else {}
    )
    nonzero = {key: value for key, value in operation_counts.items() if value != 0}
    reasons = tuple(
        AdapterBlockedReason(
            code="adapter_forbidden_operation_counter_nonzero",
            message=f"{field} counter must be zero for CR158 fixture/static adapter scope.",
            source="operation_counts",
            field=field,
            unlock_condition="create_separate_runtime_authorization_cr_before_real_operation",
        )
        for field in nonzero
    )
    report = AdapterOperationCounterReport(
        operation_counts=operation_counts,
        nonzero_counters=nonzero,
        blocked_reason_refs=reasons,
    )
    payload = report.to_dict()
    payload["status"] = ADAPTER_STATUS_BLOCKED if nonzero else ADAPTER_STATUS_PASS
    payload["nonzero_counter_count"] = len(nonzero)
    return payload


def validate_strategy_type_adapter_core(
    core: StrategyTypeAdapterCore | Mapping[str, Any] | Any,
    extension: Mapping[str, Any] | Any | None = None,
    operation_counts: Mapping[str, Any] | None = None,
) -> AdapterValidationResult:
    core_data = _core_mapping(core)
    extension_data = _mapping(extension)
    reasons: list[AdapterBlockedReason] = []

    for field_name in CORE_REQUIRED_FIELD_GROUPS:
        if field_name not in core_data:
            reasons.append(_missing(field_name, "core", "adapter_core_required_field_missing"))

    adapter_id = str(core_data.get("adapter_id") or "")
    strategy_type = _strategy_type(core_data.get("strategy_type"))
    if not adapter_id:
        reasons.append(_missing("adapter_id", "core", "adapter_core_adapter_id_missing"))
    if strategy_type not in {STRATEGY_TYPE_EVENT, STRATEGY_TYPE_ML}:
        reasons.append(
            AdapterBlockedReason(
                code="adapter_core_strategy_type_invalid",
                message="strategy_type must be event or ml.",
                source="core",
                field="strategy_type",
            )
        )

    for ref_group in ("input_refs", "output_signal_refs", "evidence_refs", "handoff_refs"):
        reasons.extend(_missing_ref_items(core_data.get(ref_group), "core", ref_group))

    flags = _mapping(core_data.get("authorization_flags"))
    for flag_name in ("no_runtime", "no_feed", "no_training", "no_registry", "no_publish"):
        if flags.get(flag_name) is not True:
            reasons.append(
                AdapterBlockedReason(
                    code="adapter_core_authorization_flag_missing",
                    message=f"{flag_name} must be true for CR158 local/static/fixture adapter scope.",
                    source="authorization_flags",
                    field=flag_name,
                )
            )

    for field_name in CORE_PRIVATE_FIELD_DENYLIST:
        if field_name in core_data:
            reasons.append(_private_field(field_name, "core"))
    for field_name in CORE_PRIVATE_FIELD_DENYLIST:
        if field_name in extension_data and field_name not in EVENT_EXTENSION_REQUIRED_REFS + ML_EXTENSION_REQUIRED_REFS:
            reasons.append(_private_field(field_name, "extension"))

    counter_result = validate_adapter_operation_counters(operation_counts or core_data.get("operation_counts"))
    reasons.extend(_reasons_from_result(counter_result))
    status = ADAPTER_STATUS_BLOCKED if reasons else ADAPTER_STATUS_PASS
    return AdapterValidationResult(
        adapter_id=adapter_id,
        strategy_type=strategy_type,
        status=status,
        blocked_reasons=tuple(reasons),
        evidence_refs=_ref_sequence(core_data.get("evidence_refs")),
        output_signal_refs=_ref_sequence(core_data.get("output_signal_refs")),
        handoff_refs=_ref_sequence(core_data.get("handoff_refs")),
        operation_counts=counter_result.operation_counts,
    )


def validate_event_adapter_extension(
    core: StrategyTypeAdapterCore | Mapping[str, Any] | Any,
    extension: EventAdapterExtension | Mapping[str, Any] | Any,
    operation_counts: Mapping[str, Any] | None = None,
) -> AdapterValidationResult:
    core_result = validate_strategy_type_adapter_core(core, operation_counts=operation_counts)
    core_data = _core_mapping(core)
    extension_data = _mapping(extension)
    reasons = list(_reasons_from_result(core_result))
    adapter_id = str(core_data.get("adapter_id") or core_result.adapter_id)

    if _strategy_type(core_data.get("strategy_type")) != STRATEGY_TYPE_EVENT:
        reasons.append(
            AdapterBlockedReason(
                code="event_adapter_wrong_strategy_type",
                message="Event adapter extension requires strategy_type=event.",
                source="core",
                field="strategy_type",
            )
        )
    for field_name in EVENT_EXTENSION_REQUIRED_REFS:
        if not _ref_present(extension_data.get(field_name)):
            reasons.append(_missing(field_name, "event_adapter_extension", "event_adapter_required_ref_missing"))
    for field_name in EVENT_EXTENSION_ML_FIELD_DENYLIST:
        if field_name in extension_data:
            reasons.append(_private_field(field_name, "event_adapter_extension"))

    counter_result = validate_adapter_operation_counters(operation_counts or extension_data.get("operation_counts"))
    reasons.extend(_reasons_from_result(counter_result))
    evidence_refs = tuple(
        _ref_payload(extension_data[field_name])
        for field_name in EVENT_EXTENSION_REQUIRED_REFS
        if _ref_present(extension_data.get(field_name))
    )
    return AdapterValidationResult(
        adapter_id=adapter_id,
        strategy_type=STRATEGY_TYPE_EVENT,
        status=ADAPTER_STATUS_BLOCKED if reasons else ADAPTER_STATUS_PASS,
        blocked_reasons=tuple(_dedupe_reasons(reasons)),
        evidence_refs=evidence_refs,
        output_signal_refs=tuple(_ref_payload(extension_data["signal_output_ref"]) for _ in (0,) if _ref_present(extension_data.get("signal_output_ref"))),
        handoff_refs=core_result.handoff_refs,
        operation_counts=counter_result.operation_counts,
    )


def validate_ml_adapter_extension(
    core: StrategyTypeAdapterCore | Mapping[str, Any] | Any,
    extension: MLAdapterExtension | Mapping[str, Any] | Any,
    operation_counts: Mapping[str, Any] | None = None,
) -> AdapterValidationResult:
    core_result = validate_strategy_type_adapter_core(core, operation_counts=operation_counts)
    core_data = _core_mapping(core)
    extension_data = _mapping(extension)
    reasons = list(_reasons_from_result(core_result))
    adapter_id = str(core_data.get("adapter_id") or core_result.adapter_id)

    if _strategy_type(core_data.get("strategy_type")) != STRATEGY_TYPE_ML:
        reasons.append(
            AdapterBlockedReason(
                code="ml_adapter_wrong_strategy_type",
                message="ML adapter extension requires strategy_type=ml.",
                source="core",
                field="strategy_type",
            )
        )
    for field_name in ML_EXTENSION_REQUIRED_REFS:
        if not _ref_present(extension_data.get(field_name)):
            reasons.append(_missing(field_name, "ml_adapter_extension", "ml_adapter_required_ref_missing"))
    for field_name in ML_EXTENSION_EVENT_FIELD_DENYLIST:
        if field_name in extension_data:
            reasons.append(_private_field(field_name, "ml_adapter_extension"))

    counter_result = validate_adapter_operation_counters(operation_counts or extension_data.get("operation_counts"))
    reasons.extend(_reasons_from_result(counter_result))
    evidence_refs = tuple(
        _ref_payload(extension_data[field_name])
        for field_name in ML_EXTENSION_REQUIRED_REFS
        if _ref_present(extension_data.get(field_name))
    )
    return AdapterValidationResult(
        adapter_id=adapter_id,
        strategy_type=STRATEGY_TYPE_ML,
        status=ADAPTER_STATUS_BLOCKED if reasons else ADAPTER_STATUS_PASS,
        blocked_reasons=tuple(_dedupe_reasons(reasons)),
        evidence_refs=evidence_refs,
        output_signal_refs=tuple(_ref_payload(extension_data["prediction_signal_ref"]) for _ in (0,) if _ref_present(extension_data.get("prediction_signal_ref"))),
        handoff_refs=core_result.handoff_refs,
        operation_counts=counter_result.operation_counts,
    )


def adapter_core_summary(core_or_result: StrategyTypeAdapterCore | AdapterValidationResult | Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(core_or_result, AdapterValidationResult):
        return core_or_result.to_dict()
    data = _core_mapping(core_or_result)
    result = validate_strategy_type_adapter_core(data)
    summary = result.to_dict()
    summary["input_refs"] = tuple(_ref_payload(ref) for ref in _as_tuple(data.get("input_refs")))
    return summary


def event_adapter_summary(
    result_or_core: AdapterValidationResult | Mapping[str, Any] | Any,
    extension: EventAdapterExtension | Mapping[str, Any] | Any | None = None,
) -> dict[str, Any]:
    result = result_or_core if isinstance(result_or_core, AdapterValidationResult) else validate_event_adapter_extension(result_or_core, extension or {})
    payload = result.to_dict()
    payload["adapter_kind"] = "event_adapter"
    return payload


def ml_adapter_summary(
    result_or_core: AdapterValidationResult | Mapping[str, Any] | Any,
    extension: MLAdapterExtension | Mapping[str, Any] | Any | None = None,
) -> dict[str, Any]:
    result = result_or_core if isinstance(result_or_core, AdapterValidationResult) else validate_ml_adapter_extension(result_or_core, extension or {})
    payload = result.to_dict()
    payload["adapter_kind"] = "ml_adapter"
    return payload


def build_adapter_evidence_refs(
    validation_results: Sequence[AdapterValidationResult | Mapping[str, Any] | Any],
) -> tuple[AdapterTypedEvidenceRef, ...]:
    refs: list[AdapterTypedEvidenceRef] = []
    for index, item in enumerate(validation_results, start=1):
        data = item.to_dict() if isinstance(item, AdapterValidationResult) else _mapping(item)
        adapter_id = str(data.get("adapter_id") or f"adapter-{index}")
        strategy_type = str(data.get("strategy_type") or "adapter")
        status = _known_status(data.get("status"))
        for ref_index, ref in enumerate(_as_tuple(data.get("evidence_refs")), start=1):
            ref_payload = _ref_payload(ref)
            path_or_id = _ref_path(ref_payload)
            if not path_or_id:
                continue
            refs.append(
                AdapterTypedEvidenceRef(
                    ref_id=f"{adapter_id}:{strategy_type}:evidence:{ref_index}",
                    kind=f"{strategy_type}_adapter",
                    path_or_id=path_or_id,
                    status=status,
                    hash=str(ref_payload.get("hash") or ref_payload.get("checksum") or ""),
                    body_copy_count=int(ref_payload.get("body_copy_count", 0) or 0),
                    private_payload_included=bool(ref_payload.get("private_payload_included", False)),
                    description=str(ref_payload.get("description") or ""),
                )
            )
    return tuple(refs)


def validate_adapter_evidence_refs(
    refs: Sequence[AdapterTypedEvidenceRef | Mapping[str, Any] | Any],
) -> AdapterValidationResult:
    reasons: list[AdapterBlockedReason] = []
    evidence_refs: list[dict[str, Any]] = []
    for index, ref in enumerate(refs, start=1):
        data = ref.to_dict() if isinstance(ref, AdapterTypedEvidenceRef) else _mapping(ref)
        ref_id = str(data.get("ref_id") or f"ref-{index}")
        if not str(data.get("kind") or ""):
            reasons.append(_missing("kind", ref_id, "adapter_evidence_required_field_missing"))
        if not str(data.get("path_or_id") or ""):
            reasons.append(_missing("path_or_id", ref_id, "adapter_evidence_required_field_missing"))
        if int(data.get("body_copy_count", 0) or 0) != 0:
            reasons.append(
                AdapterBlockedReason(
                    code="adapter_evidence_body_copy_forbidden",
                    message="Adapter evidence refs must not copy payload/report/model body content.",
                    source=ref_id,
                    field="body_copy_count",
                    unlock_condition="store_body_in_separate_artifact_and_reference_it_only",
                )
            )
        if bool(data.get("private_payload_included", False)):
            reasons.append(
                AdapterBlockedReason(
                    code="adapter_evidence_private_payload_forbidden",
                    message="Adapter evidence refs must not include event payloads or model binaries.",
                    source=ref_id,
                    field="private_payload_included",
                    unlock_condition="replace_private_payload_with_artifact_ref",
                )
            )
        evidence_refs.append(data)
    return AdapterValidationResult(
        adapter_id="adapter-evidence-refs",
        strategy_type="adapter",
        status=ADAPTER_STATUS_BLOCKED if reasons else ADAPTER_STATUS_PASS,
        blocked_reasons=tuple(reasons),
        evidence_refs=tuple(evidence_refs),
        operation_counts=zero_adapter_operation_counts(),
    )


def adapter_handoff_summary(
    core: StrategyTypeAdapterCore | Mapping[str, Any] | Any,
    evidence_refs: Sequence[AdapterTypedEvidenceRef | Mapping[str, Any] | Any],
) -> dict[str, Any]:
    core_data = _core_mapping(core)
    validation = validate_strategy_type_adapter_core(core_data)
    evidence_validation = validate_adapter_evidence_refs(evidence_refs)
    evidence_payloads = tuple(
        ref.to_dict() if isinstance(ref, AdapterTypedEvidenceRef) else _mapping(ref)
        for ref in evidence_refs
    )
    status = ADAPTER_STATUS_BLOCKED if not validation.passed or not evidence_validation.passed else ADAPTER_STATUS_PASS
    return {
        "schema_version": STRATEGY_TYPE_ADAPTER_SCHEMA,
        "adapter_id": str(core_data.get("adapter_id") or validation.adapter_id),
        "strategy_type": _strategy_type(core_data.get("strategy_type")),
        "status": status,
        "adapter_status": status,
        "evidence_refs": evidence_payloads,
        "blocked_reason_refs": tuple(
            _reason_payload(reason)
            for reason in (*validation.blocked_reasons, *evidence_validation.blocked_reasons)
        ),
        "handoff_refs": tuple(_ref_payload(ref) for ref in _as_tuple(core_data.get("handoff_refs"))),
        "operation_counts": normalise_adapter_operation_counts(core_data.get("operation_counts")),
        "limitations": ADAPTER_NO_RUNTIME_LIMITATIONS,
    }


def _core_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, StrategyTypeAdapterCore):
        return value.to_dict()
    return _mapping(value)


def _mapping(value: Any) -> dict[str, Any]:
    converted = as_mapping(value, none_as_empty=True)
    return dict(converted or {})


def _as_tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Mapping):
        return (value,)
    return tuple(value) if isinstance(value, Sequence) else (value,)


def _ref_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(json_safe(value))
    if isinstance(value, str):
        return {"ref": value}
    data = _mapping(value)
    return data if data else {"ref": str(value)}


def _ref_path(value: Mapping[str, Any]) -> str:
    for key in ("path_or_id", "ref", "evidence_ref", "gate_ref", "id"):
        candidate = str(value.get(key) or "")
        if candidate:
            return candidate
    return ""


def _ref_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    data = _ref_payload(value)
    return bool(_ref_path(data))


def _ref_sequence(value: Any) -> tuple[dict[str, Any], ...]:
    return tuple(_ref_payload(item) for item in _as_tuple(value) if _ref_present(item))


def _known_status(value: Any) -> str:
    status = _status_value(value)
    return status if status in {ADAPTER_STATUS_PASS, ADAPTER_STATUS_FAIL, ADAPTER_STATUS_NEEDS_REVIEW, ADAPTER_STATUS_BLOCKED} else ADAPTER_STATUS_BLOCKED


def _status_value(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value).upper()
    return str(value or "").upper()


def _strategy_type(value: Any) -> str:
    return str(value or "").strip().lower()


def _missing(field_name: str, source: str, code: str) -> AdapterBlockedReason:
    return AdapterBlockedReason(
        code=code,
        message=f"{field_name} is required for CR158 strategy adapter contract.",
        source=source,
        field=field_name,
    )


def _missing_ref_items(value: Any, source: str, field_name: str) -> tuple[AdapterBlockedReason, ...]:
    refs = _as_tuple(value)
    if not refs:
        return (_missing(field_name, source, "adapter_core_required_ref_group_missing"),)
    return tuple(
        _missing(field_name, source, "adapter_core_required_ref_missing")
        for ref in refs
        if not _ref_present(ref)
    )


def _private_field(field_name: str, source: str) -> AdapterBlockedReason:
    return AdapterBlockedReason(
        code="adapter_private_field_leakage",
        message=f"{field_name} must stay out of this adapter surface.",
        source=source,
        field=field_name,
        unlock_condition="move_private_field_to_typed_extension_or_redesign_at_cp5",
    )


def _reason_payload(value: AdapterBlockedReason | Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(value, AdapterBlockedReason):
        return value.to_dict()
    data = _mapping(value)
    return data if data else {"code": str(value), "message": str(value), "source": "unknown"}


def _reasons_from_result(result: AdapterValidationResult) -> tuple[AdapterBlockedReason, ...]:
    reasons: list[AdapterBlockedReason] = []
    for item in result.blocked_reasons:
        data = _reason_payload(item)
        reasons.append(
            AdapterBlockedReason(
                code=str(data.get("code") or "adapter_blocked"),
                message=str(data.get("message") or data.get("code") or "Adapter validation blocked."),
                source=str(data.get("source") or "adapter"),
                field=str(data.get("field") or ""),
                severity=str(data.get("severity") or "blocker"),
                evidence_ref=str(data.get("evidence_ref") or ""),
                unlock_condition=str(data.get("unlock_condition") or ""),
            )
        )
    return tuple(reasons)


def _dedupe_reasons(reasons: Sequence[AdapterBlockedReason]) -> tuple[AdapterBlockedReason, ...]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[AdapterBlockedReason] = []
    for reason in reasons:
        key = (reason.code, reason.source, reason.field)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(reason)
    return tuple(deduped)


__all__ = [
    "ADAPTER_NO_RUNTIME_LIMITATIONS",
    "ADAPTER_STATUS_BLOCKED",
    "ADAPTER_STATUS_FAIL",
    "ADAPTER_STATUS_NEEDS_REVIEW",
    "ADAPTER_STATUS_PASS",
    "ADAPTER_TYPED_EVIDENCE_REF_SCHEMA",
    "CORE_PRIVATE_FIELD_DENYLIST",
    "CORE_REQUIRED_FIELD_GROUPS",
    "CR158_FORBIDDEN_OPERATION_COUNTERS",
    "EVENT_EXTENSION_REQUIRED_REFS",
    "ML_EXTENSION_REQUIRED_REFS",
    "STRATEGY_TYPE_ADAPTER_SCHEMA",
    "STRATEGY_TYPE_EVENT",
    "STRATEGY_TYPE_ML",
    "AdapterBlockedReason",
    "AdapterOperationCounterReport",
    "AdapterTypedEvidenceRef",
    "AdapterValidationResult",
    "AdapterValidationStatus",
    "EventAdapterExtension",
    "MLAdapterExtension",
    "StrategyTypeAdapterCore",
    "adapter_core_summary",
    "adapter_handoff_summary",
    "adapter_no_runtime_summary",
    "build_adapter_evidence_refs",
    "event_adapter_summary",
    "ml_adapter_summary",
    "normalise_adapter_operation_counts",
    "validate_adapter_evidence_refs",
    "validate_adapter_operation_counters",
    "validate_event_adapter_extension",
    "validate_ml_adapter_extension",
    "validate_strategy_type_adapter_core",
    "zero_adapter_operation_counts",
]
