"""Governed production-lake readiness contracts.

This module is metadata-only. It does not scan parquet files, write catalog
pointers, sync NAS, fetch providers, or perform runtime/trading operations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Mapping, Sequence

from .contracts import (
    DATASET_ADJ_FACTOR,
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_INDUSTRY_CLASSIFICATION,
    DATASET_LIQUIDITY_CAPACITY,
    DATASET_MARKET_CAP,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES,
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
    PIT_STATUS_AVAILABLE,
    QUALITY_STATUS_FAIL,
    QUALITY_STATUS_PASS,
    QUALITY_STATUS_WARN,
    READINESS_STATUS_AVAILABLE,
)


GOVERNED_LAKE_READINESS_SCHEMA = "governed_lake_readiness_matrix_v1"
GOVERNED_LAKE_DATASETS: tuple[str, ...] = (
    DATASET_ADJ_FACTOR,
    "bse_code_mapping",
    DATASET_EVENTS,
    DATASET_HS300_INDEX,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_INDUSTRY_CLASSIFICATION,
    "lifecycle_code_change",
    DATASET_LIQUIDITY_CAPACITY,
    DATASET_MARKET_CAP,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_PRICES_LIMIT_CODE_CHANGE_FIXES,
    DATASET_PRICES_LIMIT_COVERAGE_EXCLUSIONS,
    DATASET_STOCK_BASIC,
    DATASET_TRADE_CALENDAR,
    DATASET_TRADE_STATUS,
)
GOVERNED_STATUS_PRODUCTION_READY = "production_ready"
GOVERNED_STATUS_RESEARCH_READY = "research_ready"
GOVERNED_STATUS_QUARANTINED = "quarantined"
GOVERNED_STATUS_UNSUPPORTED = "unsupported"
GOVERNED_STATUS_VALUES = (
    GOVERNED_STATUS_PRODUCTION_READY,
    GOVERNED_STATUS_RESEARCH_READY,
    GOVERNED_STATUS_QUARANTINED,
    GOVERNED_STATUS_UNSUPPORTED,
)
PIT_STATUS_NOT_APPLICABLE = "not_applicable"
PIT_STATUS_UNSUPPORTED_WITH_REASON = "unsupported-with-reason"
BUSINESS_CONFLICT_DATASETS = (
    DATASET_EVENTS,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_TRADE_STATUS,
)
PIT_REQUIRED_DATASETS = (
    DATASET_EVENTS,
    DATASET_INDEX_MEMBERS,
    DATASET_INDEX_WEIGHTS,
    DATASET_INDUSTRY_CLASSIFICATION,
    DATASET_STOCK_BASIC,
)
ZERO_OPERATION_COUNTERS = {
    "provider_fetch": 0,
    "nas_sync_or_write": 0,
    "credential_read": 0,
    "lake_write": 0,
    "catalog_pointer_mutation": 0,
    "business_conflict_cleanup": 0,
    "simulation_or_live": 0,
    "broker_write": 0,
}


@dataclass(frozen=True, slots=True)
class GovernedRunRegistryRow:
    dataset: str
    run_id: str
    ordering_policy: str
    order_key: str
    source: str = "catalog_current_pointer"
    deterministic_fallback_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GovernedLakeDatasetReadiness:
    dataset: str
    governed_status: str
    publish_status: str
    readiness_status: str
    quality_status: str
    pit_status: str
    conflict_policy: str
    catalog_current_path: str
    run_registry: GovernedRunRegistryRow
    issues: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "governed_status": self.governed_status,
            "publish_status": self.publish_status,
            "readiness_status": self.readiness_status,
            "quality_status": self.quality_status,
            "pit_status": self.pit_status,
            "conflict_policy": self.conflict_policy,
            "catalog_current_path": self.catalog_current_path,
            "run_registry": self.run_registry.to_dict(),
            "issues": [dict(item) for item in self.issues],
        }


@dataclass(frozen=True, slots=True)
class GovernedLakeReadinessMatrix:
    rows: tuple[GovernedLakeDatasetReadiness, ...]
    operation_counts: Mapping[str, int]
    schema_version: str = GOVERNED_LAKE_READINESS_SCHEMA

    @property
    def dataset_count(self) -> int:
        return len(self.rows)

    @property
    def production_ready_count(self) -> int:
        return sum(1 for row in self.rows if row.governed_status == GOVERNED_STATUS_PRODUCTION_READY)

    @property
    def quarantined_count(self) -> int:
        return sum(1 for row in self.rows if row.governed_status == GOVERNED_STATUS_QUARANTINED)

    @property
    def unsupported_count(self) -> int:
        return sum(1 for row in self.rows if row.governed_status == GOVERNED_STATUS_UNSUPPORTED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_count": self.dataset_count,
            "production_ready_count": self.production_ready_count,
            "quarantined_count": self.quarantined_count,
            "unsupported_count": self.unsupported_count,
            "rows": [row.to_dict() for row in self.rows],
            "operation_counts": dict(self.operation_counts),
        }


def build_governed_lake_readiness_matrix(
    catalog_entries: Sequence[Mapping[str, Any] | object],
    *,
    expected_datasets: Sequence[str] = GOVERNED_LAKE_DATASETS,
    conflict_policy_by_dataset: Mapping[str, str] | None = None,
    operation_counts: Mapping[str, Any] | None = None,
) -> GovernedLakeReadinessMatrix:
    entries = {_payload(entry).get("dataset", ""): _payload(entry) for entry in catalog_entries}
    policies = {str(key): str(value) for key, value in dict(conflict_policy_by_dataset or {}).items()}
    rows = tuple(
        _readiness_row(str(dataset), entries.get(str(dataset), {}), policies)
        for dataset in tuple(expected_datasets)
    )
    return GovernedLakeReadinessMatrix(rows=rows, operation_counts=_operation_counts(operation_counts))


def validate_governed_lake_readiness_matrix(
    matrix: GovernedLakeReadinessMatrix | Mapping[str, Any],
    *,
    expected_datasets: Sequence[str] = GOVERNED_LAKE_DATASETS,
) -> tuple[dict[str, Any], ...]:
    value = matrix if isinstance(matrix, GovernedLakeReadinessMatrix) else _matrix_from_mapping(matrix)
    issues: list[dict[str, Any]] = []
    expected = tuple(str(item) for item in expected_datasets)
    actual = tuple(row.dataset for row in value.rows)
    if len(actual) != len(set(actual)):
        issues.append({"code": "governed_lake_dataset_duplicate"})
    for dataset in expected:
        if dataset not in actual:
            issues.append({"code": "governed_lake_dataset_missing", "dataset": dataset})
    for row in value.rows:
        if row.governed_status not in GOVERNED_STATUS_VALUES:
            issues.append({"code": "governed_lake_status_invalid", "dataset": row.dataset})
        if row.pit_status in {"", "null", "unknown"}:
            issues.append({"code": "governed_lake_pit_status_unclassified", "dataset": row.dataset})
        if not row.run_registry.run_id and row.governed_status != GOVERNED_STATUS_UNSUPPORTED:
            issues.append({"code": "governed_lake_run_registry_missing", "dataset": row.dataset})
        if row.run_registry.ordering_policy == "source_run_id_lexical_desc":
            issues.append({"code": "governed_lake_source_run_id_lexical_ordering_forbidden", "dataset": row.dataset})
        if row.run_registry.deterministic_fallback_allowed:
            issues.append({"code": "governed_lake_deterministic_fallback_not_production_ordering", "dataset": row.dataset})
        if row.governed_status == GOVERNED_STATUS_QUARANTINED and row.conflict_policy == "none":
            issues.append({"code": "governed_lake_quarantine_policy_missing", "dataset": row.dataset})
        if any(item.get("code") == "catalog_entry_missing" for item in row.issues):
            issues.append({"code": "governed_lake_dataset_missing", "dataset": row.dataset})
    for key, count in _operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "governed_lake_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def _readiness_row(
    dataset: str,
    entry: Mapping[str, Any],
    conflict_policy_by_dataset: Mapping[str, str],
) -> GovernedLakeDatasetReadiness:
    issues: list[dict[str, Any]] = []
    if not entry:
        return _unsupported_row(dataset, "catalog_entry_missing")

    published = bool(entry.get("published", True))
    publish_status = "published" if published else "unpublished"
    quality_status = str(entry.get("quality_status") or "unknown")
    readiness_status = str(entry.get("readiness_status") or "unknown")
    pit_status = _normalise_pit_status(dataset, entry)
    conflict_policy = _conflict_policy(dataset, conflict_policy_by_dataset)
    run_registry = _run_registry_row(dataset, entry)
    if not run_registry.run_id:
        issues.append({"code": "run_id_missing", "dataset": dataset})
    if not str(entry.get("canonical_path") or "").strip():
        issues.append({"code": "catalog_current_path_missing", "dataset": dataset})
    if pit_status == PIT_STATUS_UNSUPPORTED_WITH_REASON:
        issues.append({"code": "pit_status_unsupported", "dataset": dataset})

    if not published or quality_status == QUALITY_STATUS_FAIL:
        governed_status = GOVERNED_STATUS_UNSUPPORTED
    elif dataset in BUSINESS_CONFLICT_DATASETS and conflict_policy in {"quarantine_default", "semantic_rule_required"}:
        governed_status = GOVERNED_STATUS_QUARANTINED
    elif pit_status == PIT_STATUS_UNSUPPORTED_WITH_REASON:
        governed_status = GOVERNED_STATUS_RESEARCH_READY
    elif readiness_status == READINESS_STATUS_AVAILABLE and quality_status in {QUALITY_STATUS_PASS, QUALITY_STATUS_WARN}:
        governed_status = GOVERNED_STATUS_PRODUCTION_READY
    else:
        governed_status = GOVERNED_STATUS_RESEARCH_READY

    return GovernedLakeDatasetReadiness(
        dataset=dataset,
        governed_status=governed_status,
        publish_status=publish_status,
        readiness_status=readiness_status,
        quality_status=quality_status,
        pit_status=pit_status,
        conflict_policy=conflict_policy,
        catalog_current_path=str(entry.get("canonical_path") or ""),
        run_registry=run_registry,
        issues=tuple(issues),
    )


def _unsupported_row(dataset: str, reason: str) -> GovernedLakeDatasetReadiness:
    return GovernedLakeDatasetReadiness(
        dataset=dataset,
        governed_status=GOVERNED_STATUS_UNSUPPORTED,
        publish_status="missing",
        readiness_status="missing",
        quality_status="missing",
        pit_status=PIT_STATUS_UNSUPPORTED_WITH_REASON,
        conflict_policy="none",
        catalog_current_path="",
        run_registry=GovernedRunRegistryRow(dataset=dataset, run_id="", ordering_policy="missing", order_key=""),
        issues=({"code": reason, "dataset": dataset},),
    )


def _normalise_pit_status(dataset: str, entry: Mapping[str, Any]) -> str:
    pit_status = str(entry.get("pit_status") or "").strip()
    if pit_status:
        if pit_status == PIT_STATUS_AVAILABLE:
            return PIT_STATUS_AVAILABLE
        if pit_status == PIT_STATUS_NOT_APPLICABLE:
            return PIT_STATUS_NOT_APPLICABLE
        return PIT_STATUS_UNSUPPORTED_WITH_REASON
    if dataset in PIT_REQUIRED_DATASETS:
        return PIT_STATUS_UNSUPPORTED_WITH_REASON
    return PIT_STATUS_NOT_APPLICABLE


def _conflict_policy(dataset: str, policies: Mapping[str, str]) -> str:
    if dataset in policies:
        return str(policies[dataset])
    if dataset in BUSINESS_CONFLICT_DATASETS:
        return "quarantine_default"
    return "none"


def _run_registry_row(dataset: str, entry: Mapping[str, Any]) -> GovernedRunRegistryRow:
    run_id = str(
        entry.get("latest_manifest_run_id")
        or entry.get("data_run_id")
        or entry.get("publish_run_id")
        or ""
    )
    order_key = str(
        entry.get("published_at")
        or entry.get("updated_at")
        or entry.get("generated_at")
        or run_id
    )
    return GovernedRunRegistryRow(
        dataset=dataset,
        run_id=run_id,
        ordering_policy="catalog_current_pointer_order_key",
        order_key=order_key,
    )


def _payload(value: Mapping[str, Any] | object) -> dict[str, Any]:
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


def _operation_counts(values: Mapping[str, Any] | None = None) -> dict[str, int]:
    source = dict(values or {})
    counts = dict(ZERO_OPERATION_COUNTERS)
    for key, value in source.items():
        counts[str(key)] = int(value or 0)
    return counts


def _matrix_from_mapping(data: Mapping[str, Any]) -> GovernedLakeReadinessMatrix:
    return GovernedLakeReadinessMatrix(
        rows=tuple(_row_from_mapping(item) for item in data.get("rows") or ()),
        operation_counts=_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or GOVERNED_LAKE_READINESS_SCHEMA),
    )


def _row_from_mapping(data: Mapping[str, Any]) -> GovernedLakeDatasetReadiness:
    run_registry = data.get("run_registry") or {}
    return GovernedLakeDatasetReadiness(
        dataset=str(data.get("dataset") or ""),
        governed_status=str(data.get("governed_status") or ""),
        publish_status=str(data.get("publish_status") or ""),
        readiness_status=str(data.get("readiness_status") or ""),
        quality_status=str(data.get("quality_status") or ""),
        pit_status=str(data.get("pit_status") or ""),
        conflict_policy=str(data.get("conflict_policy") or "none"),
        catalog_current_path=str(data.get("catalog_current_path") or ""),
        run_registry=GovernedRunRegistryRow(
            dataset=str(run_registry.get("dataset") or data.get("dataset") or ""),
            run_id=str(run_registry.get("run_id") or ""),
            ordering_policy=str(run_registry.get("ordering_policy") or ""),
            order_key=str(run_registry.get("order_key") or ""),
            source=str(run_registry.get("source") or "catalog_current_pointer"),
            deterministic_fallback_allowed=bool(run_registry.get("deterministic_fallback_allowed", False)),
        ),
        issues=tuple(dict(item) for item in data.get("issues") or ()),
    )


__all__ = [
    "BUSINESS_CONFLICT_DATASETS",
    "GOVERNED_LAKE_DATASETS",
    "GOVERNED_LAKE_READINESS_SCHEMA",
    "GOVERNED_STATUS_PRODUCTION_READY",
    "GOVERNED_STATUS_QUARANTINED",
    "GOVERNED_STATUS_RESEARCH_READY",
    "GOVERNED_STATUS_UNSUPPORTED",
    "GovernedLakeDatasetReadiness",
    "GovernedLakeReadinessMatrix",
    "GovernedRunRegistryRow",
    "PIT_REQUIRED_DATASETS",
    "PIT_STATUS_NOT_APPLICABLE",
    "PIT_STATUS_UNSUPPORTED_WITH_REASON",
    "ZERO_OPERATION_COUNTERS",
    "build_governed_lake_readiness_matrix",
    "validate_governed_lake_readiness_matrix",
]
