"""CR014 DuckDB 只读审计与 parity evidence 合同。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .duckdb_query import (
    CLAIM_EFFECT_EVIDENCE_ONLY,
    DUCKDB_DEPENDENCY_UNAVAILABLE,
    ENGINE_FALLBACK,
    READ_MODE_CANDIDATE_AUDIT,
    DuckDBBoundaryError,
    PermissionCounters,
    ReadOnlyQueryRequest,
    ReadOnlyQueryResult,
    run_readonly_query,
)

PARITY_PASS = "pass"
PARITY_MISMATCH = "mismatch"
PARITY_BLOCKED = "blocked"
PARITY_MISMATCH_ERROR = "parity_mismatch"
SIDE_EFFECT_DETECTED = "source_of_truth_side_effect_detected"


@dataclass(frozen=True, slots=True)
class AuditSummary:
    row_count: int
    checksum: str
    key_set: tuple[str, ...] = ()
    null_profile: Mapping[str, int] = field(default_factory=dict)
    aggregates: Mapping[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_count": self.row_count,
            "checksum": self.checksum,
            "key_set": list(self.key_set),
            "null_profile": dict(self.null_profile),
            "aggregates": dict(self.aggregates),
        }


@dataclass(frozen=True, slots=True)
class ReadOnlyAuditEvidence:
    run_id: str
    dataset: str
    mode: str
    input_ref: str
    engine: str
    row_count: int
    checksum: str
    parity_status: str = PARITY_PASS
    fallback_reason: str | None = None
    evidence_path: str | None = None
    source_of_truth: str = ""
    candidate_unpublished: bool = False
    claim_effect: str = CLAIM_EFFECT_EVIDENCE_ONLY
    publish_count: int = 0
    source_of_truth_updates: int = 0
    current_pointer_changes: int = 0
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()
    summary: AuditSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset": self.dataset,
            "mode": self.mode,
            "input_ref": self.input_ref,
            "engine": self.engine,
            "row_count": self.row_count,
            "checksum": self.checksum,
            "parity_status": self.parity_status,
            "fallback_reason": self.fallback_reason,
            "evidence_path": self.evidence_path,
            "source_of_truth": self.source_of_truth,
            "candidate_unpublished": self.candidate_unpublished,
            "claim_effect": self.claim_effect,
            "publish_count": self.publish_count,
            "source_of_truth_updates": self.source_of_truth_updates,
            "current_pointer_changes": self.current_pointer_changes,
            "permission_counters": self.permission_counters.to_dict(),
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
            "summary": self.summary.to_dict() if self.summary else None,
        }


@dataclass(frozen=True, slots=True)
class ParityEvidence:
    run_id: str
    dataset: str
    mode: str
    parity_status: str
    duckdb_summary: AuditSummary
    fallback_summary: AuditSummary
    mismatch_fields: tuple[str, ...] = ()
    claim_effect: str = CLAIM_EFFECT_EVIDENCE_ONLY
    publish_count: int = 0
    source_of_truth_updates: int = 0
    current_pointer_changes: int = 0
    permission_counters: PermissionCounters = field(default_factory=PermissionCounters)
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset": self.dataset,
            "mode": self.mode,
            "parity_status": self.parity_status,
            "duckdb_summary": self.duckdb_summary.to_dict(),
            "fallback_summary": self.fallback_summary.to_dict(),
            "mismatch_fields": list(self.mismatch_fields),
            "claim_effect": self.claim_effect,
            "publish_count": self.publish_count,
            "source_of_truth_updates": self.source_of_truth_updates,
            "current_pointer_changes": self.current_pointer_changes,
            "permission_counters": self.permission_counters.to_dict(),
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


@dataclass(frozen=True, slots=True)
class SideEffectCheck:
    passed: bool
    counters: Mapping[str, int]
    error_codes: tuple[str, ...] = ()
    details: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "counters": dict(self.counters),
            "error_codes": list(self.error_codes),
            "details": [dict(item) for item in self.details],
        }


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        return value
    except TypeError:
        return str(value)


def _normalise_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {str(key): _json_safe(value) for key, value in sorted(dict(row).items())}
        for row in rows
    )


def audit_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    key_fields: Sequence[str] = (),
) -> AuditSummary:
    normalised = _normalise_rows(rows)
    encoded = json.dumps(normalised, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    fields = sorted({key for row in normalised for key in row})
    null_profile = {
        field_name: sum(1 for row in normalised if row.get(field_name) is None)
        for field_name in fields
    }
    aggregates: dict[str, float] = {}
    for field_name in fields:
        values = [
            value
            for row in normalised
            for key, value in row.items()
            if key == field_name and isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        if values:
            aggregates[f"sum:{field_name}"] = float(sum(values))
    key_set: tuple[str, ...] = ()
    if key_fields:
        key_set = tuple(
            sorted(
                "|".join(str(row.get(field_name, "")) for field_name in key_fields)
                for row in normalised
            )
        )
    return AuditSummary(
        row_count=len(normalised),
        checksum=checksum,
        key_set=key_set,
        null_profile=null_profile,
        aggregates=aggregates,
    )


def run_fallback_audit(
    request: ReadOnlyQueryRequest,
    *,
    rows: Sequence[Mapping[str, Any]] = (),
    reason: str = DUCKDB_DEPENDENCY_UNAVAILABLE,
    run_id: str = "cr014-s04-fallback-audit",
    evidence_path: str | None = None,
) -> ReadOnlyAuditEvidence:
    summary = audit_rows(rows)
    return ReadOnlyAuditEvidence(
        run_id=run_id,
        dataset=request.dataset,
        mode=request.mode,
        input_ref=request.source_path,
        engine=ENGINE_FALLBACK,
        row_count=summary.row_count,
        checksum=summary.checksum,
        fallback_reason=reason,
        evidence_path=evidence_path,
        source_of_truth=request.source_of_truth,
        candidate_unpublished=request.mode == READ_MODE_CANDIDATE_AUDIT,
        permission_counters=request.permission_counters,
        details=({"fallback_reason": reason},),
        summary=summary,
    )


def evidence_from_query_result(
    result: ReadOnlyQueryResult,
    *,
    run_id: str = "cr014-s04-readonly-audit",
    evidence_path: str | None = None,
) -> ReadOnlyAuditEvidence:
    summary = audit_rows(result.rows)
    return ReadOnlyAuditEvidence(
        run_id=run_id,
        dataset=result.request.dataset,
        mode=result.request.mode,
        input_ref=result.request.source_path,
        engine=result.engine,
        row_count=summary.row_count,
        checksum=summary.checksum,
        fallback_reason=result.fallback_reason,
        evidence_path=evidence_path,
        source_of_truth=result.request.source_of_truth,
        candidate_unpublished=result.request.mode == READ_MODE_CANDIDATE_AUDIT,
        permission_counters=result.permission_counters,
        error_codes=result.error_codes,
        details=result.details,
        summary=summary,
    )


def run_readonly_audit(
    request: ReadOnlyQueryRequest,
    *,
    policy: Any = None,
    adapter: Any = None,
    fallback_rows: Sequence[Mapping[str, Any]] = (),
    run_id: str = "cr014-s04-readonly-audit",
) -> ReadOnlyAuditEvidence:
    result = run_readonly_query(
        request,
        policy=policy,
        adapter=adapter,
        fallback_rows=fallback_rows,
    )
    return evidence_from_query_result(result, run_id=run_id)


def _summary_from_evidence_or_rows(value: ReadOnlyAuditEvidence | Sequence[Mapping[str, Any]]) -> AuditSummary:
    if isinstance(value, ReadOnlyAuditEvidence):
        return value.summary or AuditSummary(row_count=value.row_count, checksum=value.checksum)
    return audit_rows(value)


def compare_duckdb_with_pandas_pyarrow(
    request: ReadOnlyQueryRequest | DuckDBBoundaryError,
    *,
    duckdb_rows: Sequence[Mapping[str, Any]] = (),
    fallback_rows: Sequence[Mapping[str, Any]] = (),
    key_fields: Sequence[str] = (),
    run_id: str = "cr014-s04-parity",
) -> ParityEvidence:
    if isinstance(request, DuckDBBoundaryError):
        empty = audit_rows(())
        return ParityEvidence(
            run_id=run_id,
            dataset="",
            mode=request.mode or "",
            parity_status=PARITY_BLOCKED,
            duckdb_summary=empty,
            fallback_summary=empty,
            error_codes=(request.code,),
            details=request.details,
        )
    duckdb_summary = audit_rows(duckdb_rows, key_fields=key_fields)
    fallback_summary = audit_rows(fallback_rows, key_fields=key_fields)
    mismatch_fields = tuple(
        field_name
        for field_name in ("row_count", "checksum", "key_set", "null_profile", "aggregates")
        if getattr(duckdb_summary, field_name) != getattr(fallback_summary, field_name)
    )
    parity_status = PARITY_PASS if not mismatch_fields else PARITY_MISMATCH
    error_codes = () if parity_status == PARITY_PASS else (PARITY_MISMATCH_ERROR,)
    return ParityEvidence(
        run_id=run_id,
        dataset=request.dataset,
        mode=request.mode,
        parity_status=parity_status,
        duckdb_summary=duckdb_summary,
        fallback_summary=fallback_summary,
        mismatch_fields=mismatch_fields,
        permission_counters=request.permission_counters,
        error_codes=error_codes,
        details=(
            {
                "claim_effect": CLAIM_EFFECT_EVIDENCE_ONLY,
                "publish_count": 0,
                "source_of_truth_updates": 0,
            },
        ),
    )


def compare_parity_evidence(
    duckdb_evidence: ReadOnlyAuditEvidence,
    fallback_evidence: ReadOnlyAuditEvidence,
    *,
    run_id: str = "cr014-s04-parity",
) -> ParityEvidence:
    duckdb_summary = _summary_from_evidence_or_rows(duckdb_evidence)
    fallback_summary = _summary_from_evidence_or_rows(fallback_evidence)
    mismatch_fields = tuple(
        field_name
        for field_name in ("row_count", "checksum", "key_set", "null_profile", "aggregates")
        if getattr(duckdb_summary, field_name) != getattr(fallback_summary, field_name)
    )
    return ParityEvidence(
        run_id=run_id,
        dataset=duckdb_evidence.dataset,
        mode=duckdb_evidence.mode,
        parity_status=PARITY_PASS if not mismatch_fields else PARITY_MISMATCH,
        duckdb_summary=duckdb_summary,
        fallback_summary=fallback_summary,
        mismatch_fields=mismatch_fields,
        permission_counters=duckdb_evidence.permission_counters,
        error_codes=() if not mismatch_fields else (PARITY_MISMATCH_ERROR,),
    )


def _counters_from_object(value: Any) -> dict[str, int]:
    counters: dict[str, int] = {}
    permission_counters = getattr(value, "permission_counters", None)
    if isinstance(permission_counters, PermissionCounters):
        counters.update(permission_counters.to_dict())
    elif isinstance(permission_counters, Mapping):
        counters.update({str(key): int(counter) for key, counter in permission_counters.items()})
    for field_name in (
        "publish_count",
        "source_of_truth_updates",
        "current_pointer_changes",
        "provider_fetches",
        "lake_writes",
        "credential_reads",
        "dependency_changes",
        "duckdb_writes",
    ):
        if hasattr(value, field_name):
            counters[field_name] = int(getattr(value, field_name))
    return counters


def assert_no_source_of_truth_side_effects(*evidence_items: Any) -> SideEffectCheck:
    totals: dict[str, int] = {
        "provider_fetches": 0,
        "lake_writes": 0,
        "credential_reads": 0,
        "dependency_changes": 0,
        "duckdb_writes": 0,
        "publish_count": 0,
        "source_of_truth_updates": 0,
        "current_pointer_changes": 0,
        "legacy_data_operations": 0,
        "old_report_overwrites": 0,
    }
    for item in evidence_items:
        for key, value in _counters_from_object(item).items():
            if key in totals:
                totals[key] += int(value)
    non_zero = {key: value for key, value in totals.items() if value != 0}
    if non_zero:
        return SideEffectCheck(
            passed=False,
            counters=totals,
            error_codes=(SIDE_EFFECT_DETECTED,),
            details=({"non_zero": non_zero},),
        )
    return SideEffectCheck(passed=True, counters=totals)


__all__ = [
    "AuditSummary",
    "PARITY_BLOCKED",
    "PARITY_MISMATCH",
    "PARITY_MISMATCH_ERROR",
    "PARITY_PASS",
    "ParityEvidence",
    "ReadOnlyAuditEvidence",
    "SIDE_EFFECT_DETECTED",
    "SideEffectCheck",
    "assert_no_source_of_truth_side_effects",
    "audit_rows",
    "compare_duckdb_with_pandas_pyarrow",
    "compare_parity_evidence",
    "evidence_from_query_result",
    "run_fallback_audit",
    "run_readonly_audit",
]
