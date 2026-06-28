"""CR019-S01 阶段六 admission gate 与 package 离线合同。

本模块只处理脱敏 evidence 引用和内存结构，不读取凭据、不调用 QMT /
MiniQMT / XtQuant、不执行 provider fetch、不写 lake / broker lake、不 publish，
也不启动 simulation 或 live run。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence

from engine.admission_contracts import AdmissionStatus, GateStatus


class Stage6GateId(str, Enum):
    """阶段六固定 10 类 P0 gate。"""

    DATA_QUALITY = "data_quality"
    FACTOR_QUALITY = "factor_quality"
    PORTFOLIO_CONSTRUCTION = "portfolio_construction"
    TRADABILITY = "tradability"
    COST_MODEL = "cost_model"
    BENCHMARK_EXCESS = "benchmark_excess"
    ROBUSTNESS = "robustness"
    ABLATION = "ablation"
    FREEZE_INTEGRITY = "freeze_integrity"
    PRESIM_AND_5DAY_DRY_RUN = "presim_and_5day_dry_run"


REQUIRED_STAGE6_GATE_IDS: tuple[Stage6GateId, ...] = (
    Stage6GateId.DATA_QUALITY,
    Stage6GateId.FACTOR_QUALITY,
    Stage6GateId.PORTFOLIO_CONSTRUCTION,
    Stage6GateId.TRADABILITY,
    Stage6GateId.COST_MODEL,
    Stage6GateId.BENCHMARK_EXCESS,
    Stage6GateId.ROBUSTNESS,
    Stage6GateId.ABLATION,
    Stage6GateId.FREEZE_INTEGRITY,
    Stage6GateId.PRESIM_AND_5DAY_DRY_RUN,
)

FORBIDDEN_OPERATION_COUNTERS: tuple[str, ...] = (
    "qmt_api_call",
    "provider_fetch",
    "lake_write",
    "broker_lake_write",
    "publish",
    "simulation_or_live_run",
    "credential_read",
    "real_order_call",
    "real_cancel_call",
    "account_query_call",
    "account_write_call",
    "service_start",
    "dependency_change",
    "xtquant_import",
)

OLD_FAILED_STRATEGY_CLAIM_ID = "simulation_ready"


@dataclass(frozen=True, slots=True)
class GateResult:
    """单个 P0 gate 的 JSON-ready 合同结果。"""

    gate_id: Stage6GateId | str
    status: GateStatus | str
    evidence_ref: str
    reason_code: str = ""
    unlock_condition: str = ""
    missing_fields: tuple[str, ...] = ()
    source_ref: str = ""
    priority: str = "P0"


@dataclass(frozen=True, slots=True)
class BlockedClaim:
    """Admission blocked claim；只记录原因和解除条件，不授权真实操作。"""

    claim_id: str
    reason_code: str
    evidence_ref: str
    unlock_condition: str
    source_gate_id: str = ""
    severity: str = "P0"


@dataclass(frozen=True, slots=True)
class AdmissionPackage:
    """阶段六 admission package 的稳定输出结构。"""

    run_id: str
    strategy_id: str
    research_rerun_ref: str
    gate_matrix: tuple[GateResult, ...]
    benchmark_ref: str
    dry_run_5day_ref: str
    pre_sim_ref: str
    stage_gate_ref: str
    admission_status: AdmissionStatus | str
    blocked_claims: tuple[BlockedClaim, ...] = ()
    missing_evidence: tuple[str, ...] = ()
    unlock_conditions: tuple[str, ...] = ()
    next_review_trigger: str = ""
    permission_counters: Mapping[str, int] = field(
        default_factory=lambda: collect_admission_safety_counters()
    )
    old_failed_strategy_simulation_ready_count: int = 0


def collect_admission_safety_counters(
    counters: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """归一化 admission 禁止操作计数；未传入时全部为 0。"""

    normalized = {key: 0 for key in FORBIDDEN_OPERATION_COUNTERS}
    if counters:
        for key, value in counters.items():
            normalized[str(key)] = int(value)
    return normalized


def build_stage6_gate_matrix(
    strategy_id: str,
    experiment_evidence: Mapping[str | Stage6GateId, object],
    research_rerun_summary: Mapping[str, object] | None = None,
    benchmark_evidence_ref: str = "",
    dry_run_evidence_refs: Sequence[str] | None = None,
    pre_sim_ref: str = "",
    stage_gate_ref: str = "",
) -> tuple[GateResult, ...]:
    """按固定 10 类 P0 gate 构造 gate matrix，缺失字段 fail closed。"""

    dry_run_refs = tuple(ref for ref in (dry_run_evidence_refs or ()) if ref)
    results: list[GateResult] = []
    for gate_id in REQUIRED_STAGE6_GATE_IDS:
        raw_gate = _lookup_gate_evidence(experiment_evidence, gate_id)
        result = _coerce_gate_result(strategy_id, gate_id, raw_gate)

        if gate_id is Stage6GateId.BENCHMARK_EXCESS and not benchmark_evidence_ref:
            result = _blocked_gate(
                gate_id,
                "benchmark_evidence_missing",
                "provide_multi_benchmark_and_primary_benchmark_evidence",
                missing_fields=("benchmark_evidence_ref",),
            )

        if gate_id is Stage6GateId.PRESIM_AND_5DAY_DRY_RUN:
            missing_fields: list[str] = []
            if not pre_sim_ref:
                missing_fields.append("pre_sim_ref")
            if len(dry_run_refs) < 5:
                missing_fields.append("dry_run_evidence_refs")
            if missing_fields:
                result = _blocked_gate(
                    gate_id,
                    "dry_run_5day_missing",
                    "provide_pre_sim_ref_and_5_consecutive_real_trading_day_dry_run_refs",
                    missing_fields=tuple(missing_fields),
                )
            elif not result.evidence_ref:
                evidence_ref = f"{pre_sim_ref}|{','.join(dry_run_refs)}"
                result = GateResult(
                    gate_id=gate_id,
                    status=GateStatus.PASS,
                    evidence_ref=evidence_ref,
                    source_ref=_source_ref_for_gate(gate_id),
                )

        results.append(result)

    rerun_status = str((research_rerun_summary or {}).get("status", "")).lower()
    if rerun_status in {"fail", "failed", "blocked"}:
        return tuple(
            result
            if result.gate_id is not Stage6GateId.DATA_QUALITY
            else _blocked_gate(
                Stage6GateId.DATA_QUALITY,
                "research_rerun_failed",
                "rerun_on_published_current_truth_until_passed",
                evidence_ref=str(
                    (research_rerun_summary or {}).get("evidence_ref", "")
                ),
            )
            for result in results
        )

    return tuple(results)


def evaluate_stage6_admission(
    gate_matrix: Iterable[GateResult | Mapping[str, object]],
    old_strategy_evidence: Mapping[str, object] | None = None,
    stage_gate_context: Mapping[str, object] | None = None,
    *,
    run_id: str = "",
    strategy_id: str = "",
    research_rerun_ref: str = "",
    benchmark_ref: str = "",
    dry_run_5day_ref: str = "",
    pre_sim_ref: str = "",
    permission_counters: Mapping[str, int] | None = None,
) -> AdmissionPackage:
    """汇总 gate matrix，任一 P0 失败或旧失败策略 ready 请求均 blocked。"""

    gates = tuple(_coerce_gate_result_from_input(item) for item in gate_matrix)
    counters = collect_admission_safety_counters(permission_counters)
    blocked_claims: list[BlockedClaim] = []
    missing_evidence: list[str] = []
    unlock_conditions: list[str] = []
    seen_gate_ids: set[Stage6GateId] = set()

    for gate in gates:
        gate_id = _coerce_gate_id(gate.gate_id)
        gate_status = _coerce_gate_status(gate.status)
        if gate_id is None:
            blocked_claims.append(
                BlockedClaim(
                    claim_id="stage6_admission_gate",
                    reason_code="unknown_gate_id",
                    evidence_ref=gate.evidence_ref,
                    unlock_condition="use_exact_stage6_gate_id",
                    source_gate_id=str(gate.gate_id),
                )
            )
            continue

        seen_gate_ids.add(gate_id)
        if gate_status is not GateStatus.PASS:
            reason_code = gate.reason_code or "p0_gate_failed"
            unlock_condition = gate.unlock_condition or _default_unlock_condition(
                reason_code
            )
            blocked_claims.append(
                BlockedClaim(
                    claim_id=f"stage6_{gate_id.value}",
                    reason_code=reason_code,
                    evidence_ref=gate.evidence_ref,
                    unlock_condition=unlock_condition,
                    source_gate_id=gate_id.value,
                )
            )
            missing_evidence.extend(gate.missing_fields)
            unlock_conditions.append(unlock_condition)

    for missing_gate in REQUIRED_STAGE6_GATE_IDS:
        if missing_gate not in seen_gate_ids:
            missing_evidence.append(missing_gate.value)
            blocked_claims.append(
                BlockedClaim(
                    claim_id=f"stage6_{missing_gate.value}",
                    reason_code="missing_required_gate",
                    evidence_ref="",
                    unlock_condition="provide_all_10_p0_stage6_gate_results",
                    source_gate_id=missing_gate.value,
                )
            )
            unlock_conditions.append("provide_all_10_p0_stage6_gate_results")

    stage_gate_ref = str((stage_gate_context or {}).get("stage_gate_ref", ""))
    if not stage_gate_ref:
        missing_evidence.append("stage_gate_ref")
        blocked_claims.append(
            BlockedClaim(
                claim_id="stage_gate_ref",
                reason_code="stage_gate_ref_missing",
                evidence_ref="",
                unlock_condition="provide_readonly_cr016_stage_gate_ref",
            )
        )
        unlock_conditions.append("provide_readonly_cr016_stage_gate_ref")

    if _old_strategy_failed_ready_requested(old_strategy_evidence):
        evidence_ref = str((old_strategy_evidence or {}).get("evidence_ref", ""))
        blocked_claims.append(
            BlockedClaim(
                claim_id=OLD_FAILED_STRATEGY_CLAIM_ID,
                reason_code="old_strategy_failed_rerun",
                evidence_ref=evidence_ref,
                unlock_condition="replace_old_failed_strategy_with_new_stage6_candidate_and_rerun_until_passed",
            )
        )
        unlock_conditions.append(
            "replace_old_failed_strategy_with_new_stage6_candidate_and_rerun_until_passed"
        )

    nonzero_counters = tuple(
        key for key, value in counters.items() if key in FORBIDDEN_OPERATION_COUNTERS and value
    )
    if nonzero_counters:
        blocked_claims.append(
            BlockedClaim(
                claim_id="real_operation",
                reason_code="real_operation_forbidden",
                evidence_ref="permission_counters",
                unlock_condition="reset_forbidden_operation_counters_to_zero_and_request_explicit_authorization",
            )
        )
        missing_evidence.extend(nonzero_counters)
        unlock_conditions.append(
            "reset_forbidden_operation_counters_to_zero_and_request_explicit_authorization"
        )

    status = AdmissionStatus.BLOCKED if blocked_claims else AdmissionStatus.PASS
    return AdmissionPackage(
        run_id=run_id,
        strategy_id=strategy_id,
        research_rerun_ref=research_rerun_ref,
        gate_matrix=gates,
        benchmark_ref=benchmark_ref,
        dry_run_5day_ref=dry_run_5day_ref,
        pre_sim_ref=pre_sim_ref,
        stage_gate_ref=stage_gate_ref,
        admission_status=status,
        blocked_claims=tuple(blocked_claims),
        missing_evidence=tuple(dict.fromkeys(missing_evidence)),
        unlock_conditions=tuple(dict.fromkeys(unlock_conditions)),
        next_review_trigger=_next_review_trigger(status),
        permission_counters=counters,
        old_failed_strategy_simulation_ready_count=0,
    )


def serialize_admission_package(package: AdmissionPackage) -> dict[str, object]:
    """把 admission package 转为 JSON-ready dict，不写任何真实文件。"""

    return {
        "run_id": package.run_id,
        "strategy_id": package.strategy_id,
        "research_rerun_ref": package.research_rerun_ref,
        "gate_matrix": [
            {
                "gate_id": _enum_value(gate.gate_id),
                "status": _enum_value(gate.status),
                "evidence_ref": gate.evidence_ref,
                "reason_code": gate.reason_code,
                "unlock_condition": gate.unlock_condition,
                "missing_fields": list(gate.missing_fields),
                "source_ref": gate.source_ref,
                "priority": gate.priority,
            }
            for gate in package.gate_matrix
        ],
        "benchmark_ref": package.benchmark_ref,
        "dry_run_5day_ref": package.dry_run_5day_ref,
        "pre_sim_ref": package.pre_sim_ref,
        "stage_gate_ref": package.stage_gate_ref,
        "admission_status": _enum_value(package.admission_status),
        "blocked_claims": [
            {
                "claim_id": claim.claim_id,
                "reason_code": claim.reason_code,
                "evidence_ref": claim.evidence_ref,
                "unlock_condition": claim.unlock_condition,
                "source_gate_id": claim.source_gate_id,
                "severity": claim.severity,
            }
            for claim in package.blocked_claims
        ],
        "missing_evidence": list(package.missing_evidence),
        "unlock_conditions": list(package.unlock_conditions),
        "next_review_trigger": package.next_review_trigger,
        "permission_counters": dict(package.permission_counters),
        "old_failed_strategy_simulation_ready_count": (
            package.old_failed_strategy_simulation_ready_count
        ),
    }


def _lookup_gate_evidence(
    evidence: Mapping[str | Stage6GateId, object],
    gate_id: Stage6GateId,
) -> object:
    if gate_id in evidence:
        return evidence[gate_id]
    return evidence.get(gate_id.value)


def _coerce_gate_result(
    strategy_id: str,
    gate_id: Stage6GateId,
    raw_gate: object,
) -> GateResult:
    if raw_gate is None:
        return _blocked_gate(
            gate_id,
            "missing_required_gate",
            "provide_stage6_gate_evidence_ref",
            missing_fields=(gate_id.value,),
        )
    if isinstance(raw_gate, GateResult):
        return raw_gate
    if isinstance(raw_gate, Mapping):
        status = _coerce_gate_status(raw_gate.get("status", GateStatus.PASS))
        evidence_ref = str(raw_gate.get("evidence_ref") or raw_gate.get("ref") or "")
        if status is GateStatus.PASS and not evidence_ref:
            return _blocked_gate(
                gate_id,
                "missing_required_gate",
                "provide_stage6_gate_evidence_ref",
                missing_fields=("evidence_ref",),
            )
        return GateResult(
            gate_id=gate_id,
            status=status,
            evidence_ref=evidence_ref,
            reason_code=str(raw_gate.get("reason_code") or ""),
            unlock_condition=str(raw_gate.get("unlock_condition") or ""),
            missing_fields=tuple(raw_gate.get("missing_fields") or ()),
            source_ref=str(raw_gate.get("source_ref") or _source_ref_for_gate(gate_id)),
            priority=str(raw_gate.get("priority") or "P0"),
        )
    if isinstance(raw_gate, bool):
        if raw_gate:
            return GateResult(
                gate_id=gate_id,
                status=GateStatus.PASS,
                evidence_ref=f"fixture:{strategy_id}:{gate_id.value}",
                source_ref=_source_ref_for_gate(gate_id),
            )
        return _blocked_gate(
            gate_id,
            "p0_gate_failed",
            _default_unlock_condition("p0_gate_failed"),
        )
    evidence_ref = str(raw_gate)
    if evidence_ref:
        return GateResult(
            gate_id=gate_id,
            status=GateStatus.PASS,
            evidence_ref=evidence_ref,
            source_ref=_source_ref_for_gate(gate_id),
        )
    return _blocked_gate(
        gate_id,
        "missing_required_gate",
        "provide_stage6_gate_evidence_ref",
        missing_fields=("evidence_ref",),
    )


def _coerce_gate_result_from_input(
    raw_gate: GateResult | Mapping[str, object],
) -> GateResult:
    if isinstance(raw_gate, GateResult):
        return raw_gate
    return GateResult(
        gate_id=raw_gate.get("gate_id", ""),
        status=raw_gate.get("status", GateStatus.NOT_EVALUATED),
        evidence_ref=str(raw_gate.get("evidence_ref", "")),
        reason_code=str(raw_gate.get("reason_code", "")),
        unlock_condition=str(raw_gate.get("unlock_condition", "")),
        missing_fields=tuple(raw_gate.get("missing_fields") or ()),
        source_ref=str(raw_gate.get("source_ref", "")),
        priority=str(raw_gate.get("priority", "P0")),
    )


def _blocked_gate(
    gate_id: Stage6GateId,
    reason_code: str,
    unlock_condition: str,
    *,
    evidence_ref: str = "",
    missing_fields: tuple[str, ...] = (),
) -> GateResult:
    return GateResult(
        gate_id=gate_id,
        status=GateStatus.BLOCKED,
        evidence_ref=evidence_ref,
        reason_code=reason_code,
        unlock_condition=unlock_condition,
        missing_fields=missing_fields,
        source_ref=_source_ref_for_gate(gate_id),
    )


def _coerce_gate_id(value: Stage6GateId | str | object) -> Stage6GateId | None:
    if isinstance(value, Stage6GateId):
        return value
    if isinstance(value, Enum):
        value = value.value
    try:
        return Stage6GateId(str(value))
    except ValueError:
        return None


def _coerce_gate_status(value: GateStatus | str | object) -> GateStatus:
    if isinstance(value, GateStatus):
        return value
    if isinstance(value, Enum):
        value = value.value
    try:
        return GateStatus(str(value))
    except ValueError:
        return GateStatus.NOT_EVALUATED


def _old_strategy_failed_ready_requested(
    evidence: Mapping[str, object] | None,
) -> bool:
    if not evidence:
        return False
    status = str(
        evidence.get("rerun_status")
        or evidence.get("production_rerun_status")
        or evidence.get("status")
        or ""
    ).lower()
    requested_claims = {
        str(claim)
        for claim in evidence.get("requested_claims", ())
    }
    claim_id = str(evidence.get("claim_id", ""))
    ready_requested = (
        OLD_FAILED_STRATEGY_CLAIM_ID in requested_claims
        or claim_id == OLD_FAILED_STRATEGY_CLAIM_ID
        or bool(evidence.get("attempted_simulation_ready"))
    )
    if status in {"fail", "failed", "blocked"}:
        return True
    return ready_requested


def _default_unlock_condition(reason_code: str) -> str:
    return {
        "p0_gate_failed": "fix_failed_p0_gate_and_rerun_stage6_admission",
        "missing_required_gate": "provide_all_required_stage6_gate_evidence",
        "dry_run_5day_missing": "provide_5_consecutive_real_trading_day_dry_run_refs",
        "old_strategy_failed_rerun": "do_not_package_old_failed_strategy_as_ready",
        "unknown_gate_id": "use_exact_stage6_gate_id",
    }.get(reason_code, "resolve_blocked_claim_before_next_review")


def _source_ref_for_gate(gate_id: Stage6GateId) -> str:
    return f"CR019-S01:{gate_id.value}:HLD-33.1:ADR-067"


def _next_review_trigger(status: AdmissionStatus) -> str:
    if status is AdmissionStatus.PASS:
        return "submit_to_cr016_stage_gate_and_per_run_authorization_review"
    return "resolve_blocked_claims_and_rebuild_stage6_admission_package"


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
