"""CR030-S07 策略准入证据包合同。

本模块只汇总项目自有多因子研究、组合计划、manifest/catalog、Stage6
gate 和 `order_intent_draft_v1` 草稿引用。它不导入或调用真实交易运行时，
不启动 gateway，不生成可提交订单，不读取凭据，也不写 broker lake。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from engine.admission_contracts import AdmissionStatus
from engine.order_intent_draft import SCHEMA_VERSION as ORDER_INTENT_DRAFT_SCHEMA_VERSION
from engine.research_manifest import (
    CATALOG_P0_FIELDS,
    MANIFEST_P0_FIELDS,
    assert_manifest_ready_for_admission,
)
from engine.serialization import (
    as_mapping as _shared_as_mapping,
    is_blank as _shared_is_blank,
    json_safe as _shared_json_safe,
)


STRATEGY_ADMISSION_PACKAGE_SCHEMA = "strategy_admission_package_v1"
ORDER_INTENT_DRAFT_REF_SCHEMA = "order_intent_draft_ref_v1"

MF_ADMISSION_REQUIRED_FIELD_MISSING = "MF_ADMISSION_REQUIRED_FIELD_MISSING"
MF_ADMISSION_STAGE6_P0_GATE_FAILED = "MF_ADMISSION_STAGE6_P0_GATE_FAILED"
MF_ADMISSION_MANIFEST_NOT_READY = "MF_ADMISSION_MANIFEST_NOT_READY"
MF_ADMISSION_CATALOG_NOT_READY = "MF_ADMISSION_CATALOG_NOT_READY"
MF_ADMISSION_QMT_CR_NOT_AUTHORIZED = "MF_ADMISSION_QMT_CR_NOT_AUTHORIZED"
MF_ADMISSION_ORDER_DRAFT_ONLY = "MF_ADMISSION_ORDER_DRAFT_ONLY"
MF_ADMISSION_REAL_OPERATION_NOT_AUTHORIZED = "MF_ADMISSION_REAL_OPERATION_NOT_AUTHORIZED"
MF_ADMISSION_CREDENTIAL_READ_FORBIDDEN = "MF_ADMISSION_CREDENTIAL_READ_FORBIDDEN"
MF_ADMISSION_RUNTIME_NOT_AUTHORIZED = "MF_ADMISSION_RUNTIME_NOT_AUTHORIZED"
MF_ADMISSION_STATISTICAL_GATE_BLOCKED = "MF_ADMISSION_STATISTICAL_GATE_BLOCKED"
MF_ADMISSION_ML_GATE_BLOCKED = "MF_ADMISSION_ML_GATE_BLOCKED"
MF_ADMISSION_EVENT_GATE_BLOCKED = "MF_ADMISSION_EVENT_GATE_BLOCKED"
MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED = "MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED"
MF_ADMISSION_FAMILY_LINEAGE_BLOCKED = "MF_ADMISSION_FAMILY_LINEAGE_BLOCKED"
MF_ADMISSION_COMPUTABLE_STATISTICAL_EVIDENCE_BLOCKED = "MF_ADMISSION_COMPUTABLE_STATISTICAL_EVIDENCE_BLOCKED"
MF_ADMISSION_WALK_FORWARD_OOS_EVIDENCE_BLOCKED = "MF_ADMISSION_WALK_FORWARD_OOS_EVIDENCE_BLOCKED"

NOT_AUTHORIZED_COUNTER_FIELDS = (
    "qmt_api_call",
    "mini_qmt_call",
    "xtquant_call",
    "gateway_start",
    "real_order",
    "order_cancel",
    "account_query",
    "broker_lake_write",
    "simulation_or_live_run",
    "credential_read",
)

NOT_AUTHORIZED_CLAIMS = (
    "qmt_ready",
    "simulation_ready",
    "live_ready",
    "production_truth",
    "tradable_evidence",
    "broker_order_ready",
)

FOLLOW_UP_ROUTE = ("CR-020", "CR-021", "CR-022", "CR-023", "CR-024")


@dataclass(frozen=True, slots=True)
class AdmissionBlockedReason:
    code: str
    message: str
    source: str
    severity: str = "blocker"
    unlock_condition: str = ""
    evidence_ref: str = ""
    field: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class AdmissionClaim:
    claim: str
    status: str
    reason: str
    code: str = ""
    limitation: str = ""
    evidence_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class NotAuthorizedCounters:
    qmt_api_call: int = 0
    mini_qmt_call: int = 0
    xtquant_call: int = 0
    gateway_start: int = 0
    real_order: int = 0
    order_cancel: int = 0
    account_query: int = 0
    broker_lake_write: int = 0
    simulation_or_live_run: int = 0
    credential_read: int = 0

    def to_dict(self) -> dict[str, int]:
        return {key: int(value) for key, value in asdict(self).items()}


@dataclass(frozen=True, slots=True)
class OrderIntentDraftRef:
    draft_id: str
    schema_version: str
    path_or_ref: str
    limitations: tuple[str, ...]
    ref_schema_version: str = ORDER_INTENT_DRAFT_REF_SCHEMA
    draft_only: bool = True
    not_authorization: bool = True
    consumer: str = "CR-020..CR-024 later-gated"
    required_follow_up: tuple[str, ...] = FOLLOW_UP_ROUTE
    operation_counters: Mapping[str, int] = field(default_factory=lambda: zero_not_authorized_counters().to_dict())

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class StrategyAdmissionPackage:
    package_id: str
    strategy_id: str
    run_id: str
    admission_status: AdmissionStatus | str
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[AdmissionBlockedReason, ...]
    unlock_conditions: tuple[str, ...]
    stage6_gate_summary: Mapping[str, Any]
    portfolio_plan_ref: Mapping[str, Any]
    manifest_ref: Mapping[str, Any]
    catalog_ref: Mapping[str, Any]
    order_intent_draft_ref: OrderIntentDraftRef | Mapping[str, Any]
    not_authorized_counters: NotAuthorizedCounters | Mapping[str, int]
    allowed_claims: tuple[AdmissionClaim, ...]
    blocked_claims: tuple[AdmissionClaim, ...]
    limitations: tuple[str, ...]
    pre_sim_strategy_preparation: Mapping[str, Any]
    schema_version: str = STRATEGY_ADMISSION_PACKAGE_SCHEMA
    not_qmt_authorization: bool = True
    not_simulation_authorization: bool = True
    not_live_authorization: bool = True
    not_broker_order: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["admission_status"] = _enum_value(self.admission_status)
        data["blocked_reasons"] = [reason.to_dict() for reason in self.blocked_reasons]
        data["allowed_claims"] = [claim.to_dict() for claim in self.allowed_claims]
        data["blocked_claims"] = [claim.to_dict() for claim in self.blocked_claims]
        if isinstance(self.order_intent_draft_ref, OrderIntentDraftRef):
            data["order_intent_draft_ref"] = self.order_intent_draft_ref.to_dict()
        if isinstance(self.not_authorized_counters, NotAuthorizedCounters):
            data["not_authorized_counters"] = self.not_authorized_counters.to_dict()
        return _json_safe(data)


def zero_not_authorized_counters() -> NotAuthorizedCounters:
    return NotAuthorizedCounters()


def build_strategy_admission_package(
    portfolio_plan: Mapping[str, Any] | Any,
    manifest: Mapping[str, Any] | Any,
    catalog_entry: Mapping[str, Any] | Any,
    stage6_gate: Mapping[str, Any] | Any,
    order_intent_draft_ref: Mapping[str, Any] | Any,
    qmt_authorization: Mapping[str, Any] | Any | None = None,
    *,
    counters: NotAuthorizedCounters | Mapping[str, int] | None = None,
    requested_runtime_claims: Sequence[str] | None = None,
    research_status: str = AdmissionStatus.PASS.value,
) -> StrategyAdmissionPackage:
    """构建离线准入证据包；CR-030 默认因真实运行未授权而 fail closed。"""

    normalized_counters = _normalize_counters(counters)
    blocked_reasons = list(
        validate_admission_inputs(
            portfolio_plan,
            manifest,
            catalog_entry,
            stage6_gate,
            order_intent_draft_ref,
        )
    )
    blocked_reasons.extend(assert_no_real_operation(normalized_counters))

    requested_claim_reasons = _requested_runtime_claim_reasons(requested_runtime_claims or ())
    blocked_reasons.extend(requested_claim_reasons)

    if not _has_independent_qmt_authorization(qmt_authorization):
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_QMT_CR_NOT_AUTHORIZED,
                message="CR-030 只允许形成策略准备证据包；真实运行路线必须由 CR-020..CR-024 单独授权。",
                source="qmt_route",
                unlock_condition="complete_independent_CR020_CR024_authorization_before_runtime_use",
                evidence_ref="checkpoints/CP5-CR030-MULTIFACTOR-RESEARCH-LOOP-BATCH-A-LLD-BATCH.md",
            )
        )

    draft_ref = make_order_intent_draft_ref(order_intent_draft_ref)
    if not draft_ref.draft_id:
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_REQUIRED_FIELD_MISSING,
                message="order_intent_draft_v1 草稿引用缺少 draft_id。",
                source="order_intent_draft_ref",
                field="draft_id",
                unlock_condition="provide_order_intent_draft_v1_draft_id",
            )
        )

    status = determine_admission_status(blocked_reasons, research_status)
    stage6_summary = summarize_stage6_gate(stage6_gate)
    manifest_data = _as_mapping(manifest)
    catalog_data = _as_mapping(catalog_entry)
    plan_data = _as_mapping(portfolio_plan)
    evidence_refs = _collect_evidence_refs(plan_data, manifest_data, catalog_data, stage6_summary, draft_ref)

    package = StrategyAdmissionPackage(
        package_id=_package_id(plan_data, manifest_data, catalog_data),
        strategy_id=_first_non_empty(
            manifest_data.get("strategy_id"),
            catalog_data.get("strategy_id"),
            plan_data.get("strategy_id"),
            "strategy-unknown",
        ),
        run_id=_first_non_empty(
            manifest_data.get("run_id"),
            catalog_data.get("run_id"),
            plan_data.get("run_id"),
            "run-unknown",
        ),
        admission_status=status,
        evidence_refs=evidence_refs,
        blocked_reasons=tuple(_dedupe_reasons(blocked_reasons)),
        unlock_conditions=_unlock_conditions(blocked_reasons),
        stage6_gate_summary=stage6_summary,
        portfolio_plan_ref=_portfolio_plan_ref(plan_data),
        manifest_ref=_manifest_ref(manifest_data),
        catalog_ref=_catalog_ref(catalog_data),
        order_intent_draft_ref=draft_ref,
        not_authorized_counters=normalized_counters,
        allowed_claims=_allowed_claims(evidence_refs, status),
        blocked_claims=_blocked_claims(blocked_reasons),
        limitations=_limitations(status),
        pre_sim_strategy_preparation=_pre_sim_strategy_preparation(status, blocked_reasons, evidence_refs),
    )
    return package


def validate_admission_inputs(
    portfolio_plan: Mapping[str, Any] | Any,
    manifest: Mapping[str, Any] | Any,
    catalog_entry: Mapping[str, Any] | Any,
    stage6_gate: Mapping[str, Any] | Any,
    order_intent_draft_ref: Mapping[str, Any] | Any,
) -> tuple[AdmissionBlockedReason, ...]:
    reasons: list[AdmissionBlockedReason] = []
    plan_data = _as_mapping(portfolio_plan)
    manifest_data = _as_mapping(manifest)
    catalog_data = _as_mapping(catalog_entry)
    draft_data = _as_mapping(order_intent_draft_ref)

    reasons.extend(_required_reasons("portfolio_plan", plan_data, ("plan_id", "status", "factor_weights", "target_weights")))
    if plan_data and str(plan_data.get("status", "")).lower() in {"blocked", "fail", "failed"}:
        reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_REQUIRED_FIELD_MISSING,
                message="portfolio plan 未达到可进入策略准入包的研究状态。",
                source="portfolio_plan",
                field="status",
                unlock_condition="rebuild_multifactor_portfolio_plan_until_not_blocked",
                evidence_ref=str(plan_data.get("plan_id") or ""),
            )
        )

    manifest_readiness = assert_manifest_ready_for_admission(manifest_data, catalog_data)
    if not manifest_readiness.passed:
        for reason in manifest_readiness.blocked_reasons:
            code = MF_ADMISSION_CATALOG_NOT_READY if "catalog" in str(getattr(reason, "field", "")).lower() else MF_ADMISSION_MANIFEST_NOT_READY
            reasons.append(
                AdmissionBlockedReason(
                    code=code,
                    message=str(getattr(reason, "message", "manifest/catalog 未达到 admission readiness")),
                    source="manifest_catalog",
                    field=str(getattr(reason, "field", "")),
                    unlock_condition=str(getattr(reason, "remediation", "")) or "complete_manifest_and_catalog_P0_fields",
                    evidence_ref=str(getattr(reason, "evidence_ref", "")),
                )
            )

    reasons.extend(_required_reasons("manifest", manifest_data, MANIFEST_P0_FIELDS))
    reasons.extend(_required_reasons("catalog_entry", catalog_data, CATALOG_P0_FIELDS))

    stage6_summary = summarize_stage6_gate(stage6_gate)
    if not stage6_summary["passed"]:
        reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_STAGE6_P0_GATE_FAILED,
                message="Stage6 P0 gate 未全部通过，策略准入包必须保持 blocked。",
                source="stage6_gate",
                unlock_condition="fix_failed_p0_gate_and_rerun_stage6_admission",
                evidence_ref=str(stage6_summary.get("stage_gate_ref") or ""),
            )
        )

    if draft_data.get("schema_version") != ORDER_INTENT_DRAFT_SCHEMA_VERSION:
        reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_ORDER_DRAFT_ONLY,
                message="order intent handoff 只能引用 order_intent_draft_v1 草稿。",
                source="order_intent_draft_ref",
                field="schema_version",
                unlock_condition="provide_order_intent_draft_v1_reference",
            )
        )
    for field_name in ("draft_id", "limitations"):
        if _is_blank(draft_data.get(field_name)):
            reasons.append(
                AdmissionBlockedReason(
                    code=MF_ADMISSION_REQUIRED_FIELD_MISSING,
                    message=f"order intent draft ref 缺少 {field_name}。",
                    source="order_intent_draft_ref",
                    field=field_name,
                    unlock_condition="provide_draft_ref_without_broker_payload",
                )
            )
    return tuple(_dedupe_reasons(reasons))


def assert_no_real_operation(
    counters: NotAuthorizedCounters | Mapping[str, int] | None,
) -> tuple[AdmissionBlockedReason, ...]:
    normalized = _normalize_counters(counters).to_dict()
    reasons: list[AdmissionBlockedReason] = []
    for name, value in normalized.items():
        if int(value) == 0:
            continue
        code = (
            MF_ADMISSION_CREDENTIAL_READ_FORBIDDEN
            if name == "credential_read"
            else MF_ADMISSION_REAL_OPERATION_NOT_AUTHORIZED
        )
        reasons.append(
            AdmissionBlockedReason(
                code=code,
                message=f"{name} 计数必须为 0。",
                source="not_authorized_counters",
                field=name,
                unlock_condition="reset_forbidden_operation_counter_to_zero_and_start_independent_authorization",
            )
        )
    return tuple(reasons)


def summarize_stage6_gate(stage6_gate: Mapping[str, Any] | Any) -> dict[str, Any]:
    data = _as_mapping(stage6_gate)
    nested = _as_mapping(data.get("stage6_admission"))
    status = _first_non_empty(
        nested.get("admission_status"),
        data.get("admission_status"),
        data.get("status"),
        data.get("gate_status"),
    ).lower()
    gate_matrix = _as_sequence(data.get("gate_matrix"))
    blocked_claims = _as_sequence(data.get("blocked_claims")) or _as_sequence(nested.get("blocked_reasons"))
    missing_evidence = tuple(str(item) for item in _as_sequence(data.get("missing_evidence")) if str(item))
    non_pass_gates = tuple(
        str(_as_mapping(gate).get("gate_id") or _as_mapping(gate).get("name") or index)
        for index, gate in enumerate(gate_matrix)
        if str(_as_mapping(gate).get("status", "pass")).lower() != "pass"
    )
    blocked_reason_codes = tuple(
        _first_non_empty(_as_mapping(claim).get("reason_code"), _as_mapping(claim).get("code"), claim)
        for claim in blocked_claims
    )
    passed = status == "pass" and not blocked_reason_codes and not missing_evidence and not non_pass_gates
    return {
        "status": status or "missing",
        "passed": passed,
        "blocked_reason_codes": tuple(item for item in blocked_reason_codes if item),
        "missing_evidence": missing_evidence,
        "non_pass_gates": non_pass_gates,
        "stage_gate_ref": _first_non_empty(
            data.get("stage_gate_ref"),
            data.get("admission_package_ref"),
            nested.get("admission_package_ref"),
        ),
        "evidence_refs": tuple(
            str(item)
            for item in _as_sequence(data.get("evidence_refs"))
            if str(item)
        ),
    }


def make_order_intent_draft_ref(
    draft: Mapping[str, Any] | Any,
) -> OrderIntentDraftRef:
    data = _as_mapping(draft)
    if "draft" in data and isinstance(data["draft"], Mapping):
        data = _as_mapping(data["draft"])
    handoff = _as_mapping(draft).get("handoff")
    handoff_data = _as_mapping(handoff)
    source_ref = _as_mapping(draft).get("source_ref")
    source_ref_data = _as_mapping(source_ref)
    return OrderIntentDraftRef(
        draft_id=_first_non_empty(data.get("draft_id"), handoff_data.get("draft_id")),
        schema_version=_first_non_empty(data.get("schema_version"), ORDER_INTENT_DRAFT_SCHEMA_VERSION),
        path_or_ref=_first_non_empty(
            data.get("path_or_ref"),
            data.get("ref"),
            data.get("draft_ref"),
            source_ref_data.get("target_portfolio_id"),
            data.get("draft_id"),
        ),
        limitations=tuple(str(item) for item in _as_sequence(data.get("limitations")) if str(item)),
        consumer=_first_non_empty(handoff_data.get("consumer"), data.get("consumer"), "CR-020..CR-024 later-gated"),
        operation_counters=_normalize_counters(
            data.get("operation_counters") or handoff_data.get("operation_counters")
        ).to_dict(),
    )


def determine_admission_status(
    blocked_reasons: Sequence[AdmissionBlockedReason],
    research_status: str | AdmissionStatus = AdmissionStatus.PASS.value,
) -> AdmissionStatus:
    if any(reason.severity == "blocker" for reason in blocked_reasons):
        return AdmissionStatus.BLOCKED
    normalized = _enum_value(research_status).lower()
    if normalized == AdmissionStatus.FAIL.value:
        return AdmissionStatus.FAIL
    if normalized in {AdmissionStatus.WARN.value, "research_limited"}:
        return AdmissionStatus.WARN
    return AdmissionStatus.PASS


def to_jsonable_admission_package(package: StrategyAdmissionPackage | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(package, StrategyAdmissionPackage):
        return package.to_dict()
    return _json_safe(dict(package))


def map_statistical_gate_status_to_admission_status(status: Any) -> AdmissionStatus:
    normalized = _enum_value(status).strip().upper()
    if normalized == "PASS":
        return AdmissionStatus.PASS
    if normalized == "FAIL":
        return AdmissionStatus.FAIL
    if normalized == "NEEDS_REVIEW":
        return AdmissionStatus.WARN
    if normalized == "BLOCKED":
        return AdmissionStatus.BLOCKED
    return AdmissionStatus.BLOCKED


def map_ml_gate_status_to_admission_status(status: Any) -> AdmissionStatus:
    normalized = _enum_value(status).strip().upper()
    if normalized == "PASS":
        return AdmissionStatus.PASS
    if normalized == "FAIL":
        return AdmissionStatus.FAIL
    if normalized == "NEEDS_REVIEW":
        return AdmissionStatus.WARN
    if normalized == "BLOCKED":
        return AdmissionStatus.BLOCKED
    return AdmissionStatus.BLOCKED


def map_event_gate_status_to_admission_status(status: Any) -> AdmissionStatus:
    normalized = _enum_value(status).strip().upper()
    if normalized == "PASS":
        return AdmissionStatus.PASS
    if normalized == "FAIL":
        return AdmissionStatus.FAIL
    if normalized == "NEEDS_REVIEW":
        return AdmissionStatus.WARN
    if normalized == "BLOCKED":
        return AdmissionStatus.BLOCKED
    return AdmissionStatus.BLOCKED


def map_cross_strategy_reliability_status_to_admission_status(status: Any) -> AdmissionStatus:
    normalized = _enum_value(status).strip().upper()
    if normalized == "PASS":
        return AdmissionStatus.PASS
    if normalized == "FAIL":
        return AdmissionStatus.FAIL
    if normalized == "NEEDS_REVIEW":
        return AdmissionStatus.WARN
    if normalized == "BLOCKED":
        return AdmissionStatus.BLOCKED
    return AdmissionStatus.BLOCKED


def attach_statistical_gate_to_admission_package(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    statistical_gate_summary: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """Attach CR151 statistical gate evidence without changing runtime auth flags."""

    payload = to_jsonable_admission_package(package)
    summary = _as_mapping(statistical_gate_summary)
    mapped_status = map_statistical_gate_status_to_admission_status(summary.get("status"))
    current_status = _admission_status_from_value(payload.get("admission_status"))
    payload["admission_status"] = _worse_admission_status(current_status, mapped_status).value
    payload["statistical_gate_summary"] = _json_safe(summary)

    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    for ref in _statistical_gate_refs(summary):
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))

    if mapped_status is not AdmissionStatus.PASS:
        blocked_reasons = list(_as_sequence(payload.get("blocked_reasons")))
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_STATISTICAL_GATE_BLOCKED,
                message="CR151 statistical admission gate is not PASS.",
                source="statistical_gate_summary",
                field="status",
                unlock_condition="provide_passing_CR151_statistical_gate_or_route_review",
                evidence_ref=";".join(_statistical_gate_refs(summary)),
            ).to_dict()
        )
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(blocked_reasons))
        unlock_conditions = list(_as_sequence(payload.get("unlock_conditions")))
        unlock_conditions.append("provide_passing_CR151_statistical_gate_or_route_review")
        payload["unlock_conditions"] = tuple(dict.fromkeys(str(item) for item in unlock_conditions if str(item)))
    return _json_safe(payload)


def attach_family_lineage_to_admission_package(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    family_lineage_projection: Mapping[str, Any] | Any | None,
) -> dict[str, Any]:
    """Attach CR163 lineage to the existing package; this is not a new gate."""

    from engine.strategy_admission_statistical_gate import consume_family_lineage_projection

    if isinstance(package, StrategyAdmissionPackage) or isinstance(package, Mapping):
        payload = to_jsonable_admission_package(package)
    else:
        to_dict = getattr(package, "to_dict", None)
        payload = _json_safe(to_dict()) if callable(to_dict) else {}
    lineage = consume_family_lineage_projection(family_lineage_projection)
    payload["family_lineage_projection"] = lineage
    is_cr155_package = "package_status" in payload and "paper_candidate" in payload
    status_field = "package_status" if is_cr155_package else "admission_status"
    current_status = _admission_status_from_value(payload.get(status_field))
    lineage_status = AdmissionStatus.PASS if lineage["availability"] == "present" else AdmissionStatus.BLOCKED
    combined_status = _worse_admission_status(current_status, lineage_status)
    payload[status_field] = combined_status.value.upper() if is_cr155_package else combined_status.value
    if is_cr155_package and combined_status is not AdmissionStatus.PASS:
        payload["paper_candidate"] = False

    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    if lineage["availability"] == "present" and lineage["target_ref"] not in evidence_refs:
        evidence_refs.append(lineage["target_ref"])
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))

    limitations = list(_as_sequence(payload.get("limitations")))
    limitations.extend(("raw_lineage_input_only", "effective_trial_count_unavailable", "c1_non_computable"))
    payload["limitations"] = tuple(dict.fromkeys(str(item) for item in limitations if str(item)))
    if lineage_status is AdmissionStatus.BLOCKED:
        blocked_reasons = list(_as_sequence(payload.get("blocked_reasons")))
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_FAMILY_LINEAGE_BLOCKED,
                message="Native sealed and validated family lineage is unavailable or blocked.",
                source="family_lineage_projection",
                field="availability",
                unlock_condition="provide_matching_sealed_family_lineage_validation",
                evidence_ref=str(lineage.get("target_ref") or ""),
            ).to_dict()
        )
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(blocked_reasons))
    for field_name in (
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
    ):
        payload[field_name] = bool(payload.get(field_name, True))
    return _json_safe(payload)


def attach_computable_statistical_evidence(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    summary: Any,
) -> dict[str, Any]:
    """Attach trusted CR164 summary using worst-state merge; never authorize runtime."""

    from engine.statistical_evidence import EvidenceStatus, StatisticalEvidenceSummary, project_summary

    payload = to_jsonable_admission_package(package)
    trusted = isinstance(summary, StatisticalEvidenceSummary)
    if trusted:
        projection = project_summary(summary, consumer_id="strategy-admission-package")
        mapped = {
            EvidenceStatus.PASS: AdmissionStatus.PASS,
            EvidenceStatus.FAIL: AdmissionStatus.FAIL,
            EvidenceStatus.TYPED_UNAVAILABLE: AdmissionStatus.BLOCKED,
            EvidenceStatus.BLOCKED: AdmissionStatus.BLOCKED,
        }[summary.status]
    else:
        projection = {
            "schema_version": "statistical_evidence_v1",
            "consumer_id": "strategy-admission-package",
            "status": EvidenceStatus.BLOCKED.value,
            "reason_codes": ["statistical_summary_untrusted_or_unavailable"],
            "effective_trial_count": None,
            "effective_trial_count_ref": "",
            "effective_trial_count_method": "",
            "effective_trial_count_availability": EvidenceStatus.TYPED_UNAVAILABLE.value,
        }
        mapped = AdmissionStatus.BLOCKED
    status_field = "package_status" if "package_status" in payload and "paper_candidate" in payload else "admission_status"
    current = _admission_status_from_value(payload.get(status_field))
    combined = _worse_admission_status(current, mapped)
    payload[status_field] = combined.value.upper() if status_field == "package_status" else combined.value
    if status_field == "package_status" and combined is not AdmissionStatus.PASS:
        payload["paper_candidate"] = False
    payload["computable_statistical_evidence"] = projection
    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    for ref in _as_sequence(projection.get("method_evidence_refs")):
        if str(ref) and str(ref) not in evidence_refs:
            evidence_refs.append(str(ref))
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))
    limitations = list(_as_sequence(payload.get("limitations")))
    limitations.extend(("effective_trial_count_unavailable", "statistical_evidence_not_runtime_authorization"))
    payload["limitations"] = tuple(dict.fromkeys(str(item) for item in limitations if str(item)))
    if mapped is not AdmissionStatus.PASS:
        reasons = list(_as_sequence(payload.get("blocked_reasons")))
        reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_COMPUTABLE_STATISTICAL_EVIDENCE_BLOCKED,
                message="CR164 computable statistical evidence is not fully PASS.",
                source="computable_statistical_evidence",
                field="status",
                unlock_condition="provide_all_mandatory_validated_CR164_method_evidence",
                evidence_ref=str(projection.get("summary_hash") or ""),
            ).to_dict()
        )
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(reasons))
    return _json_safe(payload)


def attach_walk_forward_oos_evidence(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    component: Any,
) -> dict[str, Any]:
    """Attach trusted CR166 C2 evidence using worst-state merge only.

    This is an evidence projection, not a new gate and never a runtime,
    paper, live, broker, or real-data authorization.
    """

    from engine.strategy_evidence import EvidenceAvailability
    from engine.walk_forward_oos_evidence import WalkForwardOOSComponent, WalkForwardOutcome
    from engine.walk_forward_oos_projections import component_projection_identity

    payload = to_jsonable_admission_package(package)
    trusted = isinstance(component, WalkForwardOOSComponent)
    identity = component_projection_identity(component) if trusted else {
        "component_ref": "",
        "component_hash": "",
        "availability": EvidenceAvailability.BLOCKED.value,
        "outcome": "",
        "reason_codes": ("component_untrusted_or_unavailable",),
    }
    if identity["availability"] != EvidenceAvailability.PRESENT.value:
        mapped = AdmissionStatus.BLOCKED
    elif component.outcome is WalkForwardOutcome.FAIL:
        mapped = AdmissionStatus.FAIL
    elif component.outcome is WalkForwardOutcome.NEEDS_REVIEW:
        mapped = AdmissionStatus.WARN
    else:
        mapped = AdmissionStatus.PASS

    status_field = "package_status" if "package_status" in payload and "paper_candidate" in payload else "admission_status"
    current = _admission_status_from_value(payload.get(status_field))
    combined = _worse_admission_status(current, mapped)
    payload[status_field] = combined.value.upper() if status_field == "package_status" else combined.value
    if status_field == "package_status" and combined is not AdmissionStatus.PASS:
        payload["paper_candidate"] = False
    payload["walk_forward_oos_evidence"] = identity

    refs = list(_as_sequence(payload.get("evidence_refs")))
    if identity["component_ref"] and identity["component_ref"] not in refs:
        refs.append(identity["component_ref"])
    payload["evidence_refs"] = tuple(str(item) for item in refs if str(item))
    limitations = list(_as_sequence(payload.get("limitations")))
    limitations.extend(("walk_forward_oos_fixture_static_only", "not_real_oos_evidence", "walk_forward_oos_not_runtime_authorization"))
    payload["limitations"] = tuple(dict.fromkeys(str(item) for item in limitations if str(item)))
    if mapped is not AdmissionStatus.PASS:
        reasons = list(_as_sequence(payload.get("blocked_reasons")))
        reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_WALK_FORWARD_OOS_EVIDENCE_BLOCKED,
                message="CR166 Walk-forward/OOS evidence is not fully present and PASS.",
                source="walk_forward_oos_evidence",
                field="availability",
                unlock_condition="provide_self_validated_walk_forward_oos_evidence_under_authorized_scope",
                evidence_ref=str(identity["component_ref"] or identity["component_hash"]),
            ).to_dict()
        )
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(reasons))
    for field_name in (
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
    ):
        payload[field_name] = bool(payload.get(field_name, True))
    return _json_safe(payload)


def attach_event_gate_to_admission_package(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    event_gate_summary: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """Attach CR153 event gate evidence without changing runtime auth flags."""

    payload = to_jsonable_admission_package(package)
    summary = _as_mapping(event_gate_summary)
    status_value = summary.get("gate_status") or summary.get("status") or "BLOCKED"
    mapped_status = map_event_gate_status_to_admission_status(status_value)
    current_status = _admission_status_from_value(payload.get("admission_status"))
    payload["admission_status"] = _worse_admission_status(current_status, mapped_status).value
    payload["event_gate_summary"] = _json_safe(summary)
    payload["event_gate_present"] = bool(summary.get("gate_present", bool(summary)))
    payload["event_gate_required"] = bool(summary.get("gate_required", True))
    payload["event_gate_status"] = _enum_value(status_value).strip().upper() if summary else "BLOCKED"
    payload["event_gate_ref"] = _first_non_empty(summary.get("gate_ref"), payload.get("event_gate_ref"))
    payload["event_gate_blocked_reasons"] = tuple(_as_sequence(summary.get("blocked_reasons")))

    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    for ref in _event_gate_refs(summary):
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))

    limitations = list(_as_sequence(payload.get("limitations")))
    limitations.extend(_as_sequence(summary.get("limitations")))
    limitations.extend(
        (
            "event_gate_pass_not_runtime_ready",
            "no_real_event_feed",
            "no_live_event_listener",
            "no_qmt_runtime",
            "no_simulation_or_live_authorization",
            "no_broker_order",
            "no_trading_authorization",
            "no_event_store_or_registry_publication",
        )
    )
    payload["limitations"] = tuple(dict.fromkeys(str(item) for item in limitations if str(item)))

    blocked_claims = list(_as_sequence(payload.get("blocked_claims")))
    blocked_claims.append(
        AdmissionClaim(
            claim="event_gate_pass_not_runtime_ready",
            status="blocked",
            code=MF_ADMISSION_EVENT_GATE_BLOCKED,
            reason="CR153 event gate PASS only covers static evidence semantics.",
            limitation="Not feed, runtime, simulation, paper, live, broker or trading readiness.",
            evidence_ref=";".join(_event_gate_refs(summary)),
        ).to_dict()
    )
    payload["blocked_claims"] = tuple(_dedupe_claim_payloads(blocked_claims))

    if mapped_status is not AdmissionStatus.PASS:
        blocked_reasons = list(_as_sequence(payload.get("blocked_reasons")))
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_EVENT_GATE_BLOCKED,
                message="CR153 event admission gate is not PASS.",
                source="event_gate_summary",
                field="gate_status",
                unlock_condition="provide_passing_CR153_event_gate_or_route_review",
                evidence_ref=";".join(_event_gate_refs(summary)),
            ).to_dict()
        )
        blocked_reasons.extend(_as_sequence(summary.get("blocked_reasons")))
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(blocked_reasons))
        unlock_conditions = list(_as_sequence(payload.get("unlock_conditions")))
        unlock_conditions.append("provide_passing_CR153_event_gate_or_route_review")
        payload["unlock_conditions"] = tuple(dict.fromkeys(str(item) for item in unlock_conditions if str(item)))

    for field_name in (
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
    ):
        payload[field_name] = bool(payload.get(field_name, True))
    return _json_safe(payload)


def attach_cross_strategy_reliability_to_admission_package(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    cross_strategy_reliability_summary: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """Attach CR154 reliability gate evidence without changing runtime auth flags."""

    payload = to_jsonable_admission_package(package)
    summary = _as_mapping(cross_strategy_reliability_summary)
    status_value = summary.get("gate_status") or summary.get("status") or "BLOCKED"
    mapped_status = map_cross_strategy_reliability_status_to_admission_status(status_value)
    current_status = _admission_status_from_value(payload.get("admission_status"))
    payload["admission_status"] = _worse_admission_status(current_status, mapped_status).value
    payload["cross_strategy_reliability_summary"] = _json_safe(summary)
    payload["cross_strategy_reliability_present"] = bool(summary.get("gate_present", bool(summary)))
    payload["cross_strategy_reliability_required"] = bool(summary.get("gate_required", True))
    payload["cross_strategy_reliability_status"] = _enum_value(status_value).strip().upper() if summary else "BLOCKED"
    payload["cross_strategy_reliability_ref"] = _first_non_empty(
        summary.get("cross_strategy_reliability_ref"),
        summary.get("gate_ref"),
        payload.get("cross_strategy_reliability_ref"),
    )
    payload["cross_strategy_reliability_blocked_reasons"] = tuple(_as_sequence(summary.get("blocked_reasons")))

    refs = _cross_strategy_reliability_refs(summary)
    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    for ref in refs:
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))

    limitations = list(_as_sequence(payload.get("limitations")))
    limitations.extend(_as_sequence(summary.get("limitations")))
    limitations.extend(
        (
            "cross_strategy_reliability_pass_not_runtime_ready",
            "no_real_lake_or_provider_validation",
            "no_paper_trading_authorization",
            "no_simulation_or_live_authorization",
            "no_qmt_runtime",
            "no_broker_order",
            "no_trading_authorization",
            "no_runtime_or_registry_publication",
        )
    )
    payload["limitations"] = tuple(dict.fromkeys(str(item) for item in limitations if str(item)))

    blocked_claims = list(_as_sequence(payload.get("blocked_claims")))
    blocked_claims.append(
        AdmissionClaim(
            claim="cross_strategy_reliability_pass_not_runtime_ready",
            status="blocked",
            code=MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED,
            reason="CR154 cross-strategy reliability gate PASS only covers local/static/fixture reliability evidence.",
            limitation="Not paper, simulation, live, broker, trading, runtime, registry, production, true TCA or real data readiness.",
            evidence_ref=";".join(refs),
        ).to_dict()
    )
    blocked_claims.extend(_as_sequence(summary.get("blocked_claims")))
    payload["blocked_claims"] = tuple(_dedupe_claim_payloads(blocked_claims))

    if mapped_status is not AdmissionStatus.PASS:
        blocked_reasons = list(_as_sequence(payload.get("blocked_reasons")))
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_CROSS_STRATEGY_RELIABILITY_BLOCKED,
                message="CR154 cross-strategy reliability gate is not PASS.",
                source="cross_strategy_reliability_summary",
                field="gate_status",
                unlock_condition="provide_passing_cross_strategy_reliability_gate_or_route_review",
                evidence_ref=";".join(refs),
            ).to_dict()
        )
        blocked_reasons.extend(_as_sequence(summary.get("blocked_reasons")))
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(blocked_reasons))
        unlock_conditions = list(_as_sequence(payload.get("unlock_conditions")))
        unlock_conditions.append("provide_passing_cross_strategy_reliability_gate_or_route_review")
        payload["unlock_conditions"] = tuple(dict.fromkeys(str(item) for item in unlock_conditions if str(item)))

    for field_name in (
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
    ):
        payload[field_name] = bool(payload.get(field_name, True))
    return _json_safe(payload)


def attach_ml_gate_to_admission_package(
    package: StrategyAdmissionPackage | Mapping[str, Any],
    ml_gate_summary: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """Attach CR152 ML gate evidence without changing runtime authorization flags."""

    payload = to_jsonable_admission_package(package)
    summary = _as_mapping(ml_gate_summary)
    status_value = summary.get("gate_status") or summary.get("status")
    mapped_status = map_ml_gate_status_to_admission_status(status_value)
    current_status = _admission_status_from_value(payload.get("admission_status"))
    payload["admission_status"] = _worse_admission_status(current_status, mapped_status).value
    payload["ml_gate_summary"] = _json_safe(summary)
    payload["gate_present"] = bool(summary.get("gate_present", True))
    payload["gate_required"] = bool(summary.get("gate_required", True))
    payload["gate_status"] = _enum_value(status_value or "BLOCKED")
    payload["gate_ref"] = _first_non_empty(summary.get("gate_ref"), payload.get("gate_ref"))

    evidence_refs = list(_as_sequence(payload.get("evidence_refs")))
    for ref in _ml_gate_refs(summary):
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    payload["evidence_refs"] = tuple(str(item) for item in evidence_refs if str(item))

    blocked_reasons_payload = tuple(_as_sequence(summary.get("blocked_reasons")))
    if mapped_status is not AdmissionStatus.PASS:
        blocked_reasons = list(_as_sequence(payload.get("blocked_reasons")))
        blocked_reasons.append(
            AdmissionBlockedReason(
                code=MF_ADMISSION_ML_GATE_BLOCKED,
                message="CR152 ML admission gate is not PASS.",
                source="ml_gate_summary",
                field="gate_status",
                unlock_condition="provide_passing_CR152_ml_gate_or_route_review",
                evidence_ref=";".join(_ml_gate_refs(summary)),
            ).to_dict()
        )
        blocked_reasons.extend(blocked_reasons_payload)
        payload["blocked_reasons"] = tuple(_dedupe_reason_payloads(blocked_reasons))
        unlock_conditions = list(_as_sequence(payload.get("unlock_conditions")))
        unlock_conditions.append("provide_passing_CR152_ml_gate_or_route_review")
        payload["unlock_conditions"] = tuple(dict.fromkeys(str(item) for item in unlock_conditions if str(item)))
    return _json_safe(payload)


def _normalize_counters(counters: NotAuthorizedCounters | Mapping[str, int] | None) -> NotAuthorizedCounters:
    if counters is None:
        return zero_not_authorized_counters()
    if isinstance(counters, NotAuthorizedCounters):
        return counters
    data = _as_mapping(counters)
    return NotAuthorizedCounters(
        **{field_name: int(data.get(field_name, 0) or 0) for field_name in NOT_AUTHORIZED_COUNTER_FIELDS}
    )


def _has_independent_qmt_authorization(qmt_authorization: Mapping[str, Any] | Any | None) -> bool:
    data = _as_mapping(qmt_authorization)
    if not data:
        return False
    route = str(data.get("authorization_route") or data.get("scope") or "")
    counters = _normalize_counters(data.get("not_authorized_counters") or data.get("operation_counters"))
    return (
        bool(data.get("independent_cr_authorized"))
        and route in {"CR-020..CR-024", "cr020-cr024", "qmt-route"}
        and not assert_no_real_operation(counters)
    )


def _requested_runtime_claim_reasons(requested_claims: Sequence[str]) -> tuple[AdmissionBlockedReason, ...]:
    reasons: list[AdmissionBlockedReason] = []
    for claim in requested_claims:
        normalized = str(claim).strip().lower()
        if normalized in NOT_AUTHORIZED_CLAIMS or normalized in {"simulation", "live", "qmt", "broker_order"}:
            reasons.append(
                AdmissionBlockedReason(
                    code=MF_ADMISSION_RUNTIME_NOT_AUTHORIZED,
                    message=f"{claim} 不属于 CR-030 授权范围。",
                    source="requested_runtime_claims",
                    field=normalized,
                    unlock_condition="route_runtime_request_to_CR020_CR024",
                )
            )
    return tuple(reasons)


def _portfolio_plan_ref(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": data.get("schema_version") or "multifactor_portfolio_plan_v1",
        "plan_id": data.get("plan_id") or "",
        "combiner_id": data.get("combiner_id") or "",
        "status": data.get("status") or "",
        "not_broker_order": data.get("not_broker_order", True),
        "evidence_ref": data.get("plan_id") or data.get("combiner_id") or "",
    }


def _manifest_ref(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": data.get("schema_version") or "experiment_manifest_v1",
        "run_id": data.get("run_id") or "",
        "strategy_id": data.get("strategy_id") or "",
        "config_hash": data.get("config_hash") or "",
        "dataset_release": data.get("dataset_release") or "",
        "evidence_refs": tuple(str(item) for item in _as_sequence(data.get("evidence_refs")) if str(item)),
    }


def _catalog_ref(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": data.get("schema_version") or "research_report_catalog_v1",
        "catalog_entry_id": data.get("catalog_entry_id") or "",
        "report_id": data.get("report_id") or "",
        "run_id": data.get("run_id") or "",
        "admission_candidate": data.get("admission_candidate", False),
        "artifact_paths": tuple(str(item) for item in _as_sequence(data.get("artifact_paths")) if str(item)),
    }


def _allowed_claims(evidence_refs: Sequence[str], status: AdmissionStatus) -> tuple[AdmissionClaim, ...]:
    return (
        AdmissionClaim(
            claim="multifactor_research_and_local_backtest_evidence",
            status="allowed",
            code="MF_ADMISSION_RESEARCH_EVIDENCE_ALLOWED",
            reason="允许作为项目自有多因子研究、本地回测和策略准备审查证据。",
            limitation="不得解释为真实运行授权、生产事实或可交易证据。",
            evidence_ref=";".join(evidence_refs[:5]),
        ),
        AdmissionClaim(
            claim="pre_sim_strategy_preparation_package",
            status="allowed" if status is AdmissionStatus.BLOCKED else "allowed",
            code="MF_ADMISSION_PRE_SIM_PREPARATION_PACKAGE",
            reason="表示策略准备材料已被结构化汇总，供后续独立路线审查。",
            limitation="真实模拟盘路线必须另行授权并重新过 gate。",
            evidence_ref="strategy_admission_package",
        ),
    )


def _blocked_claims(blocked_reasons: Sequence[AdmissionBlockedReason]) -> tuple[AdmissionClaim, ...]:
    claims = [
        AdmissionClaim(
            claim=claim,
            status="blocked",
            code=MF_ADMISSION_QMT_CR_NOT_AUTHORIZED,
            reason="CR-030 不授权该声明。",
            limitation="需要 CR-020..CR-024 独立授权和 per-run gate。",
            evidence_ref="CP5-CR030",
        )
        for claim in NOT_AUTHORIZED_CLAIMS
    ]
    for reason in blocked_reasons:
        claims.append(
            AdmissionClaim(
                claim=f"blocked:{reason.source}",
                status="blocked",
                code=reason.code,
                reason=reason.message,
                limitation=reason.unlock_condition,
                evidence_ref=reason.evidence_ref,
            )
        )
    return tuple(_dedupe_claims(claims))


def _limitations(status: AdmissionStatus) -> tuple[str, ...]:
    base = (
        "only_project_multifactor_research_and_local_backtest_evidence",
        "not_qmt_authorization",
        "not_simulation_authorization",
        "not_live_authorization",
        "not_broker_order",
        "no_gateway_start",
        "no_account_or_order_operation",
        "no_broker_lake_write",
        "no_credential_read",
        "order_intent_draft_ref_only",
    )
    if status is AdmissionStatus.BLOCKED:
        return base + ("runtime_route_requires_CR020_CR024",)
    return base


def _pre_sim_strategy_preparation(
    status: AdmissionStatus,
    blocked_reasons: Sequence[AdmissionBlockedReason],
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    evidence_blockers = tuple(
        reason.code
        for reason in blocked_reasons
        if reason.code
        not in {
            MF_ADMISSION_QMT_CR_NOT_AUTHORIZED,
            MF_ADMISSION_RUNTIME_NOT_AUTHORIZED,
            MF_ADMISSION_ORDER_DRAFT_ONLY,
        }
    )
    return {
        "status": "evidence_package_complete_for_follow_up_review" if not evidence_blockers else "blocked_missing_required_evidence",
        "admission_status": status.value,
        "evidence_refs": tuple(evidence_refs),
        "not_authorization": True,
        "requires_follow_up": FOLLOW_UP_ROUTE,
        "evidence_blockers": evidence_blockers,
    }


def _collect_evidence_refs(
    plan: Mapping[str, Any],
    manifest: Mapping[str, Any],
    catalog: Mapping[str, Any],
    stage6_summary: Mapping[str, Any],
    draft_ref: OrderIntentDraftRef,
) -> tuple[str, ...]:
    refs: list[str] = []
    refs.extend(str(item) for item in _as_sequence(plan.get("evidence_refs")) if str(item))
    refs.extend(str(item) for item in _as_sequence(manifest.get("evidence_refs")) if str(item))
    refs.extend(str(item) for item in _as_sequence(catalog.get("evidence_refs")) if str(item))
    refs.extend(str(item) for item in _as_sequence(stage6_summary.get("evidence_refs")) if str(item))
    refs.extend(
        item
        for item in (
            str(plan.get("plan_id") or ""),
            str(manifest.get("run_id") or ""),
            str(catalog.get("catalog_entry_id") or ""),
            str(stage6_summary.get("stage_gate_ref") or ""),
            draft_ref.path_or_ref,
        )
        if item
    )
    return tuple(dict.fromkeys(refs))


def _package_id(plan: Mapping[str, Any], manifest: Mapping[str, Any], catalog: Mapping[str, Any]) -> str:
    run_id = _first_non_empty(manifest.get("run_id"), catalog.get("run_id"), "run-unknown")
    plan_id = _first_non_empty(plan.get("plan_id"), "plan-unknown")
    return f"strategy-admission:{run_id}:{plan_id}"


def _required_reasons(source: str, data: Mapping[str, Any], fields: Sequence[str]) -> tuple[AdmissionBlockedReason, ...]:
    return tuple(
        AdmissionBlockedReason(
            code=MF_ADMISSION_REQUIRED_FIELD_MISSING,
            message=f"{source}.{field_name} 缺失。",
            source=source,
            field=field_name,
            unlock_condition=f"provide_{source}_{field_name}",
        )
        for field_name in fields
        if _is_blank(data.get(field_name))
    )


def _unlock_conditions(reasons: Sequence[AdmissionBlockedReason]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(reason.unlock_condition for reason in reasons if reason.unlock_condition))


def _dedupe_reasons(reasons: Sequence[AdmissionBlockedReason]) -> tuple[AdmissionBlockedReason, ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[AdmissionBlockedReason] = []
    for reason in reasons:
        key = (reason.code, reason.source, reason.field)
        if key in seen:
            continue
        seen.add(key)
        result.append(reason)
    return tuple(result)


def _dedupe_claims(claims: Sequence[AdmissionClaim]) -> tuple[AdmissionClaim, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[AdmissionClaim] = []
    for claim in claims:
        key = (claim.claim, claim.code)
        if key in seen:
            continue
        seen.add(key)
        result.append(claim)
    return tuple(result)


def _dedupe_reason_payloads(reasons: Sequence[Any]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, Any]] = []
    for reason in reasons:
        data = _as_mapping(reason)
        key = (str(data.get("code") or ""), str(data.get("source") or ""), str(data.get("field") or ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(data)
    return tuple(result)


def _dedupe_claim_payloads(claims: Sequence[Any]) -> tuple[dict[str, Any], ...]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for claim in claims:
        data = _as_mapping(claim)
        key = (str(data.get("claim") or ""), str(data.get("code") or ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(data)
    return tuple(result)


def _statistical_gate_refs(summary: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("statistical_gate_ref", "gate_ref", "ref", "evidence_ref"):
        value = str(summary.get(field_name) or "")
        if value:
            refs.append(value)
    refs.extend(str(item) for item in _as_sequence(summary.get("report_refs")) if str(item))
    return tuple(dict.fromkeys(refs))


def _ml_gate_refs(summary: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("ml_gate_ref", "gate_ref", "ref", "evidence_ref"):
        value = str(summary.get(field_name) or "")
        if value:
            refs.append(value)
    refs.extend(str(item) for item in _as_sequence(summary.get("evidence_refs")) if str(item))
    return tuple(dict.fromkeys(refs))


def _event_gate_refs(summary: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in ("event_gate_ref", "gate_ref", "ref", "evidence_ref"):
        value = str(summary.get(field_name) or "")
        if value:
            refs.append(value)
    refs.extend(str(item) for item in _as_sequence(summary.get("evidence_refs")) if str(item))
    return tuple(dict.fromkeys(refs))


def _cross_strategy_reliability_refs(summary: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for field_name in (
        "cross_strategy_reliability_ref",
        "cross_strategy_reliability_gate_ref",
        "gate_ref",
        "ref",
        "evidence_ref",
    ):
        value = str(summary.get(field_name) or "")
        if value:
            refs.append(value)
    refs.extend(str(item) for item in _as_sequence(summary.get("evidence_refs")) if str(item))
    refs.extend(str(item) for item in _as_sequence(summary.get("report_refs")) if str(item))
    return tuple(dict.fromkeys(refs))


def _admission_status_from_value(value: Any) -> AdmissionStatus:
    normalized = _enum_value(value).strip().lower()
    for status in AdmissionStatus:
        if normalized == status.value:
            return status
    return AdmissionStatus.BLOCKED


def _worse_admission_status(left: AdmissionStatus, right: AdmissionStatus) -> AdmissionStatus:
    priority = {
        AdmissionStatus.PASS: 0,
        AdmissionStatus.WARN: 1,
        AdmissionStatus.FAIL: 2,
        AdmissionStatus.BLOCKED: 3,
    }
    return left if priority[left] >= priority[right] else right


def _as_mapping(value: Any) -> dict[str, Any]:
    return _shared_as_mapping(value, none_as_empty=True) or {}


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


def _is_blank(value: Any) -> bool:
    return _shared_is_blank(value)


def _first_non_empty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        if hasattr(value, "value"):
            value = value.value
        if isinstance(value, str):
            if value.strip():
                return value.strip()
            continue
        if value != "":
            return str(value)
    return ""


def _enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _json_safe(value: Any) -> Any:
    return _shared_json_safe(value)
