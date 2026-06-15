"""CR014-S05 full-history readiness matrix 与 gap register 合同。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Mapping, Sequence

from .catalog import validate_catalog_pointer
from .contracts import (
    CR014_CLAIM_FULL_A_SINCE_INCEPTION,
    CR014_COVERAGE_START_POLICY_SECURITY_INCEPTION,
    CR014_FORBIDDEN_OPERATION_COUNTERS,
    CR014_REQUIRED_MISSING_LIFECYCLE,
    CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_PRICES,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_PASS,
    READINESS_STATUS_PIT_INCOMPLETE,
    READINESS_STATUS_QUALITY_FAILED,
    READINESS_STATUS_REQUIRED_MISSING,
)
from .manifest import validate_manifest_record

CR014_S05_P0_DATASETS: tuple[str, ...] = (
    DATASET_PRICES,
    DATASET_ADJ_FACTOR,
    DATASET_HS300_INDEX,
    DATASET_TRADE_CALENDAR,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_STOCK_BASIC,
)

GAP_P0_DATASET_MISSING = "p0_dataset_missing"
GAP_LIFECYCLE_REQUIRED_MISSING = CR014_REQUIRED_MISSING_LIFECYCLE
GAP_CATALOG_POINTER_MISSING = "catalog_pointer_missing"
GAP_CATALOG_POINTER_INCOMPLETE = "catalog_pointer_incomplete"
GAP_MANIFEST_INCOMPLETE = "manifest_incomplete"
GAP_QUALITY_FAILED = "quality_failed"
GAP_READINESS_NOT_AVAILABLE = "readiness_not_available"
GAP_PIT_INCOMPLETE = "pit_incomplete"
GAP_CANDIDATE_UNPUBLISHED = "candidate_unpublished"
GAP_AUDIT_EVIDENCE_REQUIRED = "audit_evidence_required"
GAP_PERMISSION_COUNTER_VIOLATION = "permission_counter_violation"

PUBLISH_STATUS_PUBLISHED = "published"
PUBLISH_STATUS_CANDIDATE_UNPUBLISHED = "candidate_unpublished"
PUBLISH_STATUS_MISSING_REQUIRED = "missing_required"

READINESS_SOURCE_S01_LIFECYCLE = "s01_lifecycle_current_truth_denominator"
EVIDENCE_REF_IN_MEMORY = "in_memory_fixture"

REQUIRED_ZERO_COUNTERS: tuple[str, ...] = (
    "provider_fetch",
    "lake_write",
    "credential_read",
    "old_report_overwrite",
)

PLURAL_COUNTER_ALIASES: dict[str, str] = {
    "provider_fetches": "provider_fetch",
    "lake_writes": "lake_write",
    "credential_reads": "credential_read",
    "old_report_overwrites": "old_report_overwrite",
}


@dataclass(frozen=True, slots=True)
class ReadinessMatrixRow:
    dataset: str
    window: dict[str, Any]
    universe_scope: str
    denominator_ref: str
    denominator_source: str
    catalog_pointer_ref: str | None
    manifest_ref: str | None
    candidate_ref: str | None
    audit_evidence_path: str | None
    quality_status: str
    readiness_status: str
    publish_status: str
    as_of_trade_date: str
    evidence_paths: tuple[str, ...] = ()
    gap_codes: tuple[str, ...] = ()
    run_id: str | None = None
    source_interface: str | None = None

    @property
    def p0_gate_passed(self) -> bool:
        return not self.gap_codes and self.publish_status == PUBLISH_STATUS_PUBLISHED

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "window": dict(self.window),
            "universe_scope": self.universe_scope,
            "denominator_ref": self.denominator_ref,
            "denominator_source": self.denominator_source,
            "catalog_pointer_ref": self.catalog_pointer_ref,
            "manifest_ref": self.manifest_ref,
            "candidate_ref": self.candidate_ref,
            "audit_evidence_path": self.audit_evidence_path,
            "quality_status": self.quality_status,
            "readiness_status": self.readiness_status,
            "publish_status": self.publish_status,
            "as_of_trade_date": self.as_of_trade_date,
            "evidence_paths": list(self.evidence_paths),
            "gap_codes": list(self.gap_codes),
            "p0_gate_passed": self.p0_gate_passed,
            "run_id": self.run_id,
            "source_interface": self.source_interface,
        }


@dataclass(frozen=True, slots=True)
class ReadinessMatrix:
    rows: tuple[ReadinessMatrixRow, ...]
    as_of_trade_date: str
    denominator_ref: str
    denominator_source: str
    permission_counters: dict[str, int]
    legacy_baseline_refs: tuple[str, ...] = ()

    @property
    def p0_gate_passed(self) -> bool:
        return bool(self.rows) and all(row.p0_gate_passed for row in self.rows)

    @property
    def datasets(self) -> tuple[str, ...]:
        return tuple(row.dataset for row in self.rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": [row.to_dict() for row in self.rows],
            "as_of_trade_date": self.as_of_trade_date,
            "denominator_ref": self.denominator_ref,
            "denominator_source": self.denominator_source,
            "permission_counters": dict(self.permission_counters),
            "legacy_baseline_refs": list(self.legacy_baseline_refs),
            "p0_gate_passed": self.p0_gate_passed,
        }


@dataclass(frozen=True, slots=True)
class GapRegisterRow:
    dataset: str
    gap_code: str
    evidence_path: str
    remediation: str
    release_condition: str
    claim: str = CR014_CLAIM_FULL_A_SINCE_INCEPTION
    severity: str = "P0"
    window: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "gap_code": self.gap_code,
            "evidence_path": self.evidence_path,
            "remediation": self.remediation,
            "release_condition": self.release_condition,
            "claim": self.claim,
            "severity": self.severity,
            "window": dict(self.window),
            "details": dict(self.details),
        }


@dataclass(frozen=True, slots=True)
class GapRegister:
    rows: tuple[GapRegisterRow, ...]
    permission_counters: dict[str, int]
    legacy_baseline_refs: tuple[str, ...] = ()

    @property
    def has_p0_gap(self) -> bool:
        return bool(self.rows)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": [row.to_dict() for row in self.rows],
            "permission_counters": dict(self.permission_counters),
            "legacy_baseline_refs": list(self.legacy_baseline_refs),
            "has_p0_gap": self.has_p0_gap,
        }


def _payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return dict(to_dict())
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _index_by_dataset(items: Any) -> dict[str, dict[str, Any]]:
    if items is None:
        return {}
    if isinstance(items, Mapping):
        if "dataset" not in items:
            indexed: dict[str, dict[str, Any]] = {}
            for key, value in items.items():
                payload = _payload(value)
                payload.setdefault("dataset", str(key))
                indexed[str(payload["dataset"])] = payload
            return indexed
        payload = _payload(items)
        dataset = payload.get("dataset")
        return {str(dataset): payload} if dataset else {}
    indexed = {}
    for item in items:
        payload = _payload(item)
        dataset = payload.get("dataset")
        if dataset:
            indexed[str(dataset)] = payload
    return indexed


def _normalise_permission_counters(counters: Mapping[str, Any] | None = None) -> dict[str, int]:
    normalised = {key: int(value) for key, value in CR014_FORBIDDEN_OPERATION_COUNTERS.items()}
    normalised.update({key: 0 for key in PLURAL_COUNTER_ALIASES})
    for key in REQUIRED_ZERO_COUNTERS:
        normalised.setdefault(key, 0)
    raw_counters = dict(counters or {})
    for key, value in raw_counters.items():
        try:
            counter = int(value)
        except (TypeError, ValueError):
            counter = 1
        normalised[str(key)] = counter
        alias = PLURAL_COUNTER_ALIASES.get(str(key))
        if alias and alias not in raw_counters:
            normalised[alias] = counter
    for plural, singular in PLURAL_COUNTER_ALIASES.items():
        if singular in raw_counters:
            normalised[plural] = normalised[singular]
        elif plural in raw_counters:
            normalised[singular] = normalised[plural]
        elif singular in normalised and plural not in normalised:
            normalised[plural] = normalised[singular]
    return normalised


def _counter_violations(counters: Mapping[str, int]) -> tuple[str, ...]:
    checked = (
        *REQUIRED_ZERO_COUNTERS,
        "legacy_data_operation",
        "duckdb_dependency_change",
        "duckdb_write",
        "catalog_current_pointer_publish",
        "s09_real_execution",
    )
    return tuple(key for key in checked if int(counters.get(key, 0)) != 0)


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def _lifecycle_denominator_ref(lifecycle_denominator: Mapping[str, Any]) -> str:
    return _first_text(
        lifecycle_denominator,
        "lifecycle_denominator_ref",
        "coverage_denominator_ref",
        "denominator_ref",
    )


def _as_of_trade_date(
    explicit: str | None,
    lifecycle_denominator: Mapping[str, Any],
    catalog_pointers: Mapping[str, Mapping[str, Any]],
) -> str:
    if explicit:
        return explicit
    value = _first_text(lifecycle_denominator, "as_of_trade_date", "current_truth_as_of")
    if value:
        return value
    for pointer in catalog_pointers.values():
        value = _first_text(pointer, "as_of_trade_date")
        if value:
            return value
    return "required_missing"


def _manifest_ref(payload: Mapping[str, Any]) -> str:
    return _first_text(payload, "manifest_ref", "latest_manifest_run_id", "run_id")


def _candidate_ref(payload: Mapping[str, Any]) -> str:
    return _first_text(payload, "candidate_path", "candidate_ref", "input_ref", "run_id")


def _catalog_ref(payload: Mapping[str, Any]) -> str:
    return _first_text(
        payload,
        "catalog_pointer_path",
        "published_path",
        "canonical_path",
        "latest_manifest_run_id",
    )


def _evidence_path(payload: Mapping[str, Any]) -> str:
    return _first_text(
        payload,
        "evidence_path",
        "candidate_audit_path",
        "audit_evidence_path",
        "input_ref",
        "run_id",
    )


def _publish_status(pointer: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    explicit = _first_text(pointer, "publish_status", "status")
    if explicit == PUBLISH_STATUS_PUBLISHED:
        return PUBLISH_STATUS_PUBLISHED
    if pointer and pointer.get("published", True) is not False:
        return PUBLISH_STATUS_PUBLISHED
    if candidate:
        return PUBLISH_STATUS_CANDIDATE_UNPUBLISHED
    return PUBLISH_STATUS_MISSING_REQUIRED


def _quality_status(pointer: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    return _first_text(pointer, "quality_status") or _first_text(candidate, "quality_status") or READINESS_STATUS_REQUIRED_MISSING


def _readiness_status(pointer: Mapping[str, Any], candidate: Mapping[str, Any]) -> str:
    return _first_text(pointer, "readiness_status") or _first_text(candidate, "readiness_status") or READINESS_STATUS_REQUIRED_MISSING


def _source_interface(pointer: Mapping[str, Any], candidate: Mapping[str, Any], manifest: Mapping[str, Any]) -> str | None:
    value = _first_text(pointer, "source_interface") or _first_text(candidate, "source_interface")
    return value or _first_text(manifest, "source_interface") or None


def _gap_remediation(gap_code: str) -> tuple[str, str]:
    mapping = {
        GAP_P0_DATASET_MISSING: (
            "produce_p0_dataset_candidate_and_publish_pointer",
            "dataset has manifest, quality pass, readiness available, evidence path, and explicit publish pointer",
        ),
        GAP_LIFECYCLE_REQUIRED_MISSING: (
            "provide_s01_lifecycle_denominator_ref",
            "S01 lifecycle/current-truth denominator ref is present and verified",
        ),
        GAP_CATALOG_POINTER_MISSING: (
            "publish_candidate_through_explicit_publish_gate",
            "S02 catalog current pointer is present for the dataset",
        ),
        GAP_CATALOG_POINTER_INCOMPLETE: (
            "complete_catalog_pointer_required_fields",
            "catalog pointer passes CR014 required field validation",
        ),
        GAP_MANIFEST_INCOMPLETE: (
            "complete_append_only_manifest_record",
            "manifest record passes CR014 manifest completeness validation",
        ),
        GAP_QUALITY_FAILED: (
            "rerun_quality_until_policy_passes",
            "quality_status is pass or accepted warn policy is documented",
        ),
        GAP_READINESS_NOT_AVAILABLE: (
            "resolve_readiness_status_before_production_claim",
            "readiness_status is available for the dataset and window",
        ),
        GAP_PIT_INCOMPLETE: (
            "provide_pit_contract_fields_for_pit_dataset",
            "PIT readiness is available for lifecycle-sensitive dataset",
        ),
        GAP_CANDIDATE_UNPUBLISHED: (
            "call_explicit_publish_gate_with_publish_intent",
            "candidate audit evidence has been explicitly published to current truth",
        ),
        GAP_AUDIT_EVIDENCE_REQUIRED: (
            "provide_s04_audit_or_fallback_evidence_ref",
            "readiness row contains an evidence_path or catalog/manifest evidence ref",
        ),
        GAP_PERMISSION_COUNTER_VIOLATION: (
            "reset_forbidden_operation_counters_and_rerun_offline",
            "provider_fetch, lake_write, credential_read and old_report_overwrite counters are all 0",
        ),
    }
    return mapping.get(gap_code, ("resolve_gap_before_claim", "gap is no longer present"))


def _evidence_or_missing(row: ReadinessMatrixRow, gap_code: str) -> str:
    for value in (
        row.audit_evidence_path,
        row.catalog_pointer_ref,
        row.manifest_ref,
        row.candidate_ref,
        *row.evidence_paths,
    ):
        if value:
            return str(value)
    return f"missing://{row.dataset}/{gap_code}"


def _row_gap_codes(
    *,
    dataset: str,
    denominator_ref: str,
    pointer: Mapping[str, Any],
    manifest: Mapping[str, Any],
    candidate: Mapping[str, Any],
    audit_evidence: Mapping[str, Any],
    quality_status: str,
    readiness_status: str,
    publish_status: str,
    counters: Mapping[str, int],
) -> tuple[str, ...]:
    codes: list[str] = []
    if not denominator_ref:
        codes.append(GAP_LIFECYCLE_REQUIRED_MISSING)
    if not pointer and not manifest and not candidate:
        codes.append(GAP_P0_DATASET_MISSING)
    if not pointer:
        codes.append(GAP_CATALOG_POINTER_MISSING)
    elif not validate_catalog_pointer(pointer).passed:
        codes.append(GAP_CATALOG_POINTER_INCOMPLETE)
    if manifest and not validate_manifest_record(manifest).passed:
        codes.append(GAP_MANIFEST_INCOMPLETE)
    if quality_status == QUALITY_STATUS_FAIL:
        codes.append(GAP_QUALITY_FAILED)
    if readiness_status in {
        READINESS_STATUS_REQUIRED_MISSING,
        READINESS_STATUS_QUALITY_FAILED,
    }:
        codes.append(GAP_READINESS_NOT_AVAILABLE)
    if readiness_status == READINESS_STATUS_PIT_INCOMPLETE:
        codes.append(GAP_PIT_INCOMPLETE)
    if publish_status == PUBLISH_STATUS_CANDIDATE_UNPUBLISHED:
        codes.append(GAP_CANDIDATE_UNPUBLISHED)
    if not any((_catalog_ref(pointer), _manifest_ref(manifest), _candidate_ref(candidate), _evidence_path(audit_evidence))):
        codes.append(GAP_AUDIT_EVIDENCE_REQUIRED)
    if _counter_violations(counters):
        codes.append(GAP_PERMISSION_COUNTER_VIOLATION)
    return tuple(dict.fromkeys(codes))


def build_readiness_matrix(
    *,
    lifecycle_denominator: Mapping[str, Any] | None,
    catalog_pointers: Any = None,
    manifest_refs: Any = None,
    quality_candidates: Any = None,
    audit_evidence_refs: Any = None,
    datasets: Sequence[str] = CR014_S05_P0_DATASETS,
    as_of_trade_date: str | None = None,
    legacy_baseline_refs: Sequence[str] = (),
    permission_counters: Mapping[str, Any] | None = None,
) -> ReadinessMatrix:
    """构建 readiness matrix；只消费传入合同对象，不推断全历史分母。"""

    lifecycle_payload = dict(lifecycle_denominator or {})
    pointers = _index_by_dataset(catalog_pointers)
    manifests = _index_by_dataset(manifest_refs)
    candidates = _index_by_dataset(quality_candidates)
    evidence = _index_by_dataset(audit_evidence_refs)
    counters = _normalise_permission_counters(permission_counters)
    denominator_ref = _lifecycle_denominator_ref(lifecycle_payload)
    effective_as_of = _as_of_trade_date(as_of_trade_date, lifecycle_payload, pointers)
    rows: list[ReadinessMatrixRow] = []

    for dataset in tuple(datasets):
        pointer = pointers.get(dataset, {})
        manifest = manifests.get(dataset, {})
        candidate = candidates.get(dataset, {})
        audit_evidence = evidence.get(dataset, {})
        quality_status = _quality_status(pointer, candidate)
        readiness_status = _readiness_status(pointer, candidate)
        publish_status = _publish_status(pointer, candidate)
        catalog_pointer_ref = _catalog_ref(pointer) or None
        manifest_ref = _manifest_ref(manifest) or _manifest_ref(pointer) or None
        candidate_ref = _candidate_ref(candidate) or None
        audit_evidence_path = _evidence_path(audit_evidence) or None
        evidence_paths = tuple(
            item
            for item in (
                catalog_pointer_ref,
                manifest_ref,
                candidate_ref,
                audit_evidence_path,
            )
            if item
        )
        window = {
            "coverage_start_policy": CR014_COVERAGE_START_POLICY_SECURITY_INCEPTION,
            "coverage_start": _first_text(pointer, "coverage_start") or None,
            "coverage_end": _first_text(pointer, "coverage_end") or effective_as_of,
            "as_of_trade_date": effective_as_of,
        }
        gap_codes = _row_gap_codes(
            dataset=dataset,
            denominator_ref=denominator_ref,
            pointer=pointer,
            manifest=manifest,
            candidate=candidate,
            audit_evidence=audit_evidence,
            quality_status=quality_status,
            readiness_status=readiness_status,
            publish_status=publish_status,
            counters=counters,
        )
        rows.append(
            ReadinessMatrixRow(
                dataset=dataset,
                window=window,
                universe_scope=_first_text(pointer, "universe_scope") or CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
                denominator_ref=denominator_ref,
                denominator_source=READINESS_SOURCE_S01_LIFECYCLE,
                catalog_pointer_ref=catalog_pointer_ref,
                manifest_ref=manifest_ref,
                candidate_ref=candidate_ref,
                audit_evidence_path=audit_evidence_path,
                quality_status=quality_status,
                readiness_status=readiness_status,
                publish_status=publish_status,
                as_of_trade_date=effective_as_of,
                evidence_paths=evidence_paths,
                gap_codes=gap_codes,
                run_id=_first_text(manifest, "run_id") or _first_text(pointer, "latest_manifest_run_id") or None,
                source_interface=_source_interface(pointer, candidate, manifest),
            )
        )

    return ReadinessMatrix(
        rows=tuple(rows),
        as_of_trade_date=effective_as_of,
        denominator_ref=denominator_ref,
        denominator_source=READINESS_SOURCE_S01_LIFECYCLE,
        permission_counters=counters,
        legacy_baseline_refs=tuple(str(item) for item in legacy_baseline_refs),
    )


def build_gap_register(matrix: ReadinessMatrix | Mapping[str, Any]) -> GapRegister:
    """将 readiness matrix 的 P0 缺口转为结构化 gap register。"""

    if isinstance(matrix, ReadinessMatrix):
        rows = matrix.rows
        counters = matrix.permission_counters
        legacy_refs = matrix.legacy_baseline_refs
    else:
        matrix_payload = dict(matrix)
        rows = tuple(
            ReadinessMatrixRow(
                dataset=str(row["dataset"]),
                window=dict(row.get("window") or {}),
                universe_scope=str(row.get("universe_scope") or CR014_UNIVERSE_SCOPE_ALL_A_SHARE),
                denominator_ref=str(row.get("denominator_ref") or ""),
                denominator_source=str(row.get("denominator_source") or READINESS_SOURCE_S01_LIFECYCLE),
                catalog_pointer_ref=row.get("catalog_pointer_ref"),
                manifest_ref=row.get("manifest_ref"),
                candidate_ref=row.get("candidate_ref"),
                audit_evidence_path=row.get("audit_evidence_path"),
                quality_status=str(row.get("quality_status") or READINESS_STATUS_REQUIRED_MISSING),
                readiness_status=str(row.get("readiness_status") or READINESS_STATUS_REQUIRED_MISSING),
                publish_status=str(row.get("publish_status") or PUBLISH_STATUS_MISSING_REQUIRED),
                as_of_trade_date=str(row.get("as_of_trade_date") or "required_missing"),
                evidence_paths=tuple(str(item) for item in row.get("evidence_paths", ())),
                gap_codes=tuple(str(item) for item in row.get("gap_codes", ())),
                run_id=row.get("run_id"),
                source_interface=row.get("source_interface"),
            )
            for row in matrix_payload.get("rows", ())
        )
        counters = _normalise_permission_counters(matrix_payload.get("permission_counters"))
        legacy_refs = tuple(str(item) for item in matrix_payload.get("legacy_baseline_refs", ()))

    gap_rows: list[GapRegisterRow] = []
    for row in rows:
        for gap_code in row.gap_codes:
            remediation, release_condition = _gap_remediation(gap_code)
            gap_rows.append(
                GapRegisterRow(
                    dataset=row.dataset,
                    gap_code=gap_code,
                    evidence_path=_evidence_or_missing(row, gap_code),
                    remediation=remediation,
                    release_condition=release_condition,
                    window=dict(row.window),
                    details={
                        "quality_status": row.quality_status,
                        "readiness_status": row.readiness_status,
                        "publish_status": row.publish_status,
                        "as_of_trade_date": row.as_of_trade_date,
                    },
                )
            )
    return GapRegister(
        rows=tuple(gap_rows),
        permission_counters=dict(counters),
        legacy_baseline_refs=legacy_refs,
    )


def merge_audit_evidence(
    readiness_inputs: Mapping[str, Any] | None,
    audit_evidence: Any,
) -> tuple[dict[str, Any], ...]:
    """归一化 S04 evidence refs；evidence 只作引用，不改变 current truth。"""

    del readiness_inputs
    evidence_by_dataset = _index_by_dataset(audit_evidence)
    merged: list[dict[str, Any]] = []
    for dataset, payload in sorted(evidence_by_dataset.items()):
        merged.append(
            {
                "dataset": dataset,
                "evidence_path": _evidence_path(payload) or EVIDENCE_REF_IN_MEMORY,
                "parity_status": _first_text(payload, "parity_status") or QUALITY_STATUS_PASS,
                "candidate_unpublished": bool(payload.get("candidate_unpublished", True)),
                "claim_effect": _first_text(payload, "claim_effect") or "evidence_only",
                "publish_count": int(payload.get("publish_count") or 0),
                "current_pointer_changes": int(payload.get("current_pointer_changes") or 0),
            }
        )
    return tuple(merged)


__all__ = [
    "CR014_S05_P0_DATASETS",
    "EVIDENCE_REF_IN_MEMORY",
    "GAP_AUDIT_EVIDENCE_REQUIRED",
    "GAP_CANDIDATE_UNPUBLISHED",
    "GAP_CATALOG_POINTER_INCOMPLETE",
    "GAP_CATALOG_POINTER_MISSING",
    "GAP_LIFECYCLE_REQUIRED_MISSING",
    "GAP_MANIFEST_INCOMPLETE",
    "GAP_P0_DATASET_MISSING",
    "GAP_PERMISSION_COUNTER_VIOLATION",
    "GAP_PIT_INCOMPLETE",
    "GAP_QUALITY_FAILED",
    "GAP_READINESS_NOT_AVAILABLE",
    "GapRegister",
    "GapRegisterRow",
    "PUBLISH_STATUS_CANDIDATE_UNPUBLISHED",
    "PUBLISH_STATUS_MISSING_REQUIRED",
    "PUBLISH_STATUS_PUBLISHED",
    "READINESS_SOURCE_S01_LIFECYCLE",
    "ReadinessMatrix",
    "ReadinessMatrixRow",
    "build_gap_register",
    "build_readiness_matrix",
    "merge_audit_evidence",
]
