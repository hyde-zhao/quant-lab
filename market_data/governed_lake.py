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
GOVERNED_LAKE_VALIDATION_PLAN_SCHEMA = "governed_lake_validation_plan_v1"
GOVERNED_LAKE_CONFLICT_POLICY_SCHEMA = "governed_lake_conflict_policy_v1"
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
VALIDATION_TASK_REQUIRED_IDS = (
    "inventory_catalog_physical_existence",
    "golden_current_truth_profile",
    "pit_reader_smoke",
    "duplicate_profile",
    "governed_readiness_matrix",
    "published_pointer_local_consistency",
    "nas_multinode_pointer_consistency",
)
VALIDATION_TASK_CADENCES = ("per_write", "daily", "weekly", "monthly", "on_demand", "gated")
VALIDATION_TASK_EXECUTION_MODES = (
    "metadata_only",
    "read_only_local",
    "dry_run_only",
    "human_gate_required",
)
STABLE_ENTRYPOINT_PREFIXES = ("scripts/data_lake/", "market_data.")
CONFLICT_POLICY_DATASETS = (
    DATASET_ADJ_FACTOR,
    DATASET_PRICES,
    DATASET_PRICES_LIMIT,
    DATASET_EVENTS,
    DATASET_TRADE_STATUS,
)
CONFLICT_CLASS_EXACT_OR_METADATA = "exact_or_metadata_only"
CONFLICT_CLASS_BUSINESS_CONFLICT = "business_conflict"
CONFLICT_CLASS_NO_DUPLICATE_PRESSURE = "no_duplicate_pressure"
CONFLICT_ACTION_METADATA_PRECEDENCE_GATE = "metadata_precedence_or_exact_dedup_requires_gate"
CONFLICT_ACTION_FULL_GROUP_QUARANTINE = "full_group_quarantine"
CONFLICT_ACTION_NO_ACTION = "no_action"


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


@dataclass(frozen=True, slots=True)
class GovernedLakeValidationTask:
    task_id: str
    category: str
    command_ref: str
    cadence: str
    execution_mode: str
    dataset_scope: str
    requires_human_gate: bool = False
    expected_artifact: str = ""
    side_effects: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "category": self.category,
            "command_ref": self.command_ref,
            "cadence": self.cadence,
            "execution_mode": self.execution_mode,
            "dataset_scope": self.dataset_scope,
            "requires_human_gate": self.requires_human_gate,
            "expected_artifact": self.expected_artifact,
            "side_effects": list(self.side_effects),
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class GovernedLakeValidationPlan:
    tasks: tuple[GovernedLakeValidationTask, ...]
    operation_counts: Mapping[str, int]
    schema_version: str = GOVERNED_LAKE_VALIDATION_PLAN_SCHEMA

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def auto_runnable_count(self) -> int:
        return sum(1 for task in self.tasks if not task.requires_human_gate)

    @property
    def gated_count(self) -> int:
        return sum(1 for task in self.tasks if task.requires_human_gate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_count": self.task_count,
            "auto_runnable_count": self.auto_runnable_count,
            "gated_count": self.gated_count,
            "tasks": [task.to_dict() for task in self.tasks],
            "operation_counts": dict(self.operation_counts),
        }


@dataclass(frozen=True, slots=True)
class GovernedLakeConflictPolicyRow:
    dataset: str
    source_row_count: int
    duplicate_key_group_count: int
    exact_copy_group_count: int
    metadata_only_group_count: int
    business_conflict_group_count: int
    conflict_classification: str
    default_action: str
    schema_normalization_required: bool = False
    write_authorization_required: bool = True
    semantic_selection_authorized: bool = False
    cleanup_authorized: bool = False
    decision_required: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "source_row_count": self.source_row_count,
            "duplicate_key_group_count": self.duplicate_key_group_count,
            "exact_copy_group_count": self.exact_copy_group_count,
            "metadata_only_group_count": self.metadata_only_group_count,
            "business_conflict_group_count": self.business_conflict_group_count,
            "conflict_classification": self.conflict_classification,
            "default_action": self.default_action,
            "schema_normalization_required": self.schema_normalization_required,
            "write_authorization_required": self.write_authorization_required,
            "semantic_selection_authorized": self.semantic_selection_authorized,
            "cleanup_authorized": self.cleanup_authorized,
            "decision_required": list(self.decision_required),
        }


@dataclass(frozen=True, slots=True)
class GovernedLakeConflictPolicy:
    rows: tuple[GovernedLakeConflictPolicyRow, ...]
    operation_counts: Mapping[str, int]
    schema_version: str = GOVERNED_LAKE_CONFLICT_POLICY_SCHEMA

    @property
    def dataset_count(self) -> int:
        return len(self.rows)

    @property
    def business_conflict_dataset_count(self) -> int:
        return sum(1 for row in self.rows if row.business_conflict_group_count > 0)

    @property
    def business_conflict_group_count(self) -> int:
        return sum(row.business_conflict_group_count for row in self.rows)

    @property
    def business_conflict_groups_classified_count(self) -> int:
        return sum(
            row.business_conflict_group_count
            for row in self.rows
            if row.business_conflict_group_count > 0
            and row.conflict_classification == CONFLICT_CLASS_BUSINESS_CONFLICT
            and row.default_action == CONFLICT_ACTION_FULL_GROUP_QUARANTINE
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_count": self.dataset_count,
            "business_conflict_dataset_count": self.business_conflict_dataset_count,
            "business_conflict_group_count": self.business_conflict_group_count,
            "business_conflict_groups_classified_count": self.business_conflict_groups_classified_count,
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


def build_governed_lake_validation_plan(
    readiness_matrix: GovernedLakeReadinessMatrix | Mapping[str, Any] | None = None,
    *,
    operation_counts: Mapping[str, Any] | None = None,
) -> GovernedLakeValidationPlan:
    matrix = None
    if readiness_matrix is not None:
        matrix = (
            readiness_matrix
            if isinstance(readiness_matrix, GovernedLakeReadinessMatrix)
            else _matrix_from_mapping(readiness_matrix)
        )
    dataset_scope = _dataset_scope(matrix)
    tasks = (
        GovernedLakeValidationTask(
            task_id="inventory_catalog_physical_existence",
            category="inventory",
            command_ref="scripts/data_lake/run_data_lake_readiness_audit.py",
            cadence="daily",
            execution_mode="read_only_local",
            dataset_scope=dataset_scope,
            expected_artifact="inventory physical_missing_count and catalog coverage summary",
            notes="Read-only lake inventory; no catalog or parquet mutation.",
        ),
        GovernedLakeValidationTask(
            task_id="golden_current_truth_profile",
            category="golden_baseline",
            command_ref="scripts/data_lake/profile_current_truth.py",
            cadence="per_write",
            execution_mode="read_only_local",
            dataset_scope=dataset_scope,
            expected_artifact="row count and checksum profile for current truth",
            notes="Must compare with prior baseline before accepting a content-neutral migration.",
        ),
        GovernedLakeValidationTask(
            task_id="pit_reader_smoke",
            category="pit_reader",
            command_ref="scripts/data_lake/collect_reader_runtime_smoke.py",
            cadence="daily",
            execution_mode="read_only_local",
            dataset_scope=dataset_scope,
            expected_artifact="PIT/panel/current reader smoke evidence",
            notes="Reader-only runtime smoke; no provider, broker, NAS sync or write.",
        ),
        GovernedLakeValidationTask(
            task_id="duplicate_profile",
            category="duplicate_profile",
            command_ref="scripts/data_lake/profile_duplicate_keys.py",
            cadence="weekly",
            execution_mode="read_only_local",
            dataset_scope="business-conflict datasets plus current-truth exact-copy candidates",
            expected_artifact="duplicate key group and metadata conflict profile",
            notes="Classifies conflict pressure; does not select survivor rows.",
        ),
        GovernedLakeValidationTask(
            task_id="governed_readiness_matrix",
            category="readiness_matrix",
            command_ref="market_data.governed_lake.build_governed_lake_readiness_matrix",
            cadence="per_write",
            execution_mode="metadata_only",
            dataset_scope=dataset_scope,
            expected_artifact=GOVERNED_LAKE_READINESS_SCHEMA,
            notes="Metadata-only status/PIT/run-registry bridge.",
        ),
        GovernedLakeValidationTask(
            task_id="published_pointer_local_consistency",
            category="published_pointer",
            command_ref="market_data.catalog.CatalogStore.get_published_current_pointer",
            cadence="per_write",
            execution_mode="read_only_local",
            dataset_scope=dataset_scope,
            expected_artifact="17/17 local published pointer run_id/checksum/current path consistency",
            notes="Local catalog/pointer read; pointer mutation remains out of scope.",
        ),
        GovernedLakeValidationTask(
            task_id="nas_multinode_pointer_consistency",
            category="multi_node_consistency",
            command_ref="human_gate_required:nas_shared_read_consistency_check",
            cadence="gated",
            execution_mode="human_gate_required",
            dataset_scope=dataset_scope,
            requires_human_gate=True,
            expected_artifact="at least two nodes read identical published pointer run_id/checksum",
            notes="Requires explicit NAS/shared-node authorization; no implicit credential read or sync.",
        ),
    )
    return GovernedLakeValidationPlan(tasks=tasks, operation_counts=_operation_counts(operation_counts))


def build_governed_lake_conflict_policy(
    duplicate_split_summary: Mapping[str, Any],
    *,
    expected_datasets: Sequence[str] = CONFLICT_POLICY_DATASETS,
    operation_counts: Mapping[str, Any] | None = None,
) -> GovernedLakeConflictPolicy:
    dataset_rows = {
        str(item.get("dataset") or ""): dict(item)
        for item in duplicate_split_summary.get("dataset_summary") or ()
        if isinstance(item, Mapping)
    }
    rows = tuple(_conflict_policy_row(str(dataset), dataset_rows.get(str(dataset), {})) for dataset in expected_datasets)
    return GovernedLakeConflictPolicy(rows=rows, operation_counts=_operation_counts(operation_counts))


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


def validate_governed_lake_conflict_policy(
    policy: GovernedLakeConflictPolicy | Mapping[str, Any],
    *,
    expected_datasets: Sequence[str] = CONFLICT_POLICY_DATASETS,
    expected_business_conflict_group_count: int | None = None,
) -> tuple[dict[str, Any], ...]:
    value = policy if isinstance(policy, GovernedLakeConflictPolicy) else _conflict_policy_from_mapping(policy)
    issues: list[dict[str, Any]] = []
    expected = tuple(str(item) for item in expected_datasets)
    actual = tuple(row.dataset for row in value.rows)
    if len(actual) != len(set(actual)):
        issues.append({"code": "governed_lake_conflict_policy_dataset_duplicate"})
    for dataset in expected:
        if dataset not in actual:
            issues.append({"code": "governed_lake_conflict_policy_dataset_missing", "dataset": dataset})
    if expected_business_conflict_group_count is not None:
        if value.business_conflict_group_count != int(expected_business_conflict_group_count):
            issues.append(
                {
                    "code": "governed_lake_conflict_policy_total_mismatch",
                    "expected": int(expected_business_conflict_group_count),
                    "actual": value.business_conflict_group_count,
                }
            )
    if value.business_conflict_group_count != value.business_conflict_groups_classified_count:
        issues.append(
            {
                "code": "governed_lake_business_conflict_groups_not_fully_classified",
                "business_conflict_group_count": value.business_conflict_group_count,
                "classified_count": value.business_conflict_groups_classified_count,
            }
        )
    for row in value.rows:
        if row.business_conflict_group_count > 0:
            if row.conflict_classification != CONFLICT_CLASS_BUSINESS_CONFLICT:
                issues.append({"code": "governed_lake_business_conflict_classification_missing", "dataset": row.dataset})
            if row.default_action != CONFLICT_ACTION_FULL_GROUP_QUARANTINE:
                issues.append({"code": "governed_lake_business_conflict_quarantine_missing", "dataset": row.dataset})
            if row.semantic_selection_authorized:
                issues.append({"code": "governed_lake_business_conflict_semantic_selection_forbidden", "dataset": row.dataset})
            if row.cleanup_authorized:
                issues.append({"code": "governed_lake_business_conflict_cleanup_forbidden", "dataset": row.dataset})
        if row.dataset == DATASET_PRICES and row.schema_normalization_required:
            if "approve prices schema normalization policy before write" not in row.decision_required:
                issues.append({"code": "governed_lake_prices_schema_policy_gate_missing", "dataset": row.dataset})
        if row.business_conflict_group_count == 0 and row.conflict_classification == CONFLICT_CLASS_BUSINESS_CONFLICT:
            issues.append({"code": "governed_lake_zero_conflict_dataset_misclassified", "dataset": row.dataset})
    for key, count in _operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "governed_lake_conflict_policy_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def validate_governed_lake_validation_plan(
    plan: GovernedLakeValidationPlan | Mapping[str, Any],
    *,
    required_task_ids: Sequence[str] = VALIDATION_TASK_REQUIRED_IDS,
) -> tuple[dict[str, Any], ...]:
    value = plan if isinstance(plan, GovernedLakeValidationPlan) else _validation_plan_from_mapping(plan)
    issues: list[dict[str, Any]] = []
    actual = tuple(task.task_id for task in value.tasks)
    if len(actual) != len(set(actual)):
        issues.append({"code": "governed_lake_validation_task_duplicate"})
    for task_id in tuple(str(item) for item in required_task_ids):
        if task_id not in actual:
            issues.append({"code": "governed_lake_validation_task_missing", "task_id": task_id})
    for task in value.tasks:
        if task.cadence not in VALIDATION_TASK_CADENCES:
            issues.append({"code": "governed_lake_validation_cadence_invalid", "task_id": task.task_id})
        if task.execution_mode not in VALIDATION_TASK_EXECUTION_MODES:
            issues.append({"code": "governed_lake_validation_execution_mode_invalid", "task_id": task.task_id})
        if "scripts/legacy/" in task.command_ref or task.command_ref.startswith("scripts/legacy"):
            issues.append({"code": "governed_lake_validation_legacy_script_forbidden", "task_id": task.task_id})
        if not task.requires_human_gate and not _is_stable_entrypoint(task.command_ref):
            issues.append({"code": "governed_lake_validation_unstable_entrypoint", "task_id": task.task_id})
        if not task.requires_human_gate and task.side_effects:
            issues.append({"code": "governed_lake_validation_auto_task_has_side_effects", "task_id": task.task_id})
        if task.requires_human_gate and task.execution_mode != "human_gate_required":
            issues.append({"code": "governed_lake_validation_gate_mode_mismatch", "task_id": task.task_id})
        if task.category == "multi_node_consistency" and not task.requires_human_gate:
            issues.append({"code": "governed_lake_validation_multinode_requires_gate", "task_id": task.task_id})
    for key, count in _operation_counts(value.operation_counts).items():
        if count != 0:
            issues.append({"code": "governed_lake_validation_operation_counter_nonzero", "field": key, "value": count})
    return tuple(issues)


def _conflict_policy_row(dataset: str, source: Mapping[str, Any]) -> GovernedLakeConflictPolicyRow:
    source_row_count = int(source.get("source_row_count") or 0)
    duplicate_key_group_count = int(source.get("duplicate_key_group_count") or 0)
    exact_copy_group_count = int(source.get("exact_copy_groups") or source.get("exact_copy_group_count") or 0)
    metadata_only_group_count = int(source.get("metadata_only_groups") or source.get("metadata_only_group_count") or 0)
    business_conflict_group_count = int(
        source.get("business_conflict_groups") or source.get("business_conflict_group_count") or 0
    )
    if business_conflict_group_count > 0:
        conflict_classification = CONFLICT_CLASS_BUSINESS_CONFLICT
        default_action = CONFLICT_ACTION_FULL_GROUP_QUARANTINE
        decisions = (
            "approve exact-copy dedup drop policy",
            "approve source_run_id precedence for metadata-only groups",
            "approve full-group quarantine or semantic resolution for business-conflict groups",
        )
    elif duplicate_key_group_count > 0:
        conflict_classification = CONFLICT_CLASS_EXACT_OR_METADATA
        default_action = CONFLICT_ACTION_METADATA_PRECEDENCE_GATE
        decisions = (
            "approve exact-copy dedup drop policy",
            "approve source_run_id precedence for metadata-only groups",
        )
    else:
        conflict_classification = CONFLICT_CLASS_NO_DUPLICATE_PRESSURE
        default_action = CONFLICT_ACTION_NO_ACTION
        decisions = ()
    schema_normalization_required = bool(source.get("schema_normalization_required", False))
    if dataset == DATASET_PRICES and schema_normalization_required:
        decisions = (*decisions, "approve prices schema normalization policy before write")
    return GovernedLakeConflictPolicyRow(
        dataset=dataset,
        source_row_count=source_row_count,
        duplicate_key_group_count=duplicate_key_group_count,
        exact_copy_group_count=exact_copy_group_count,
        metadata_only_group_count=metadata_only_group_count,
        business_conflict_group_count=business_conflict_group_count,
        conflict_classification=conflict_classification,
        default_action=default_action,
        schema_normalization_required=schema_normalization_required,
        write_authorization_required=bool(decisions),
        semantic_selection_authorized=False,
        cleanup_authorized=False,
        decision_required=decisions,
    )


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


def _dataset_scope(matrix: GovernedLakeReadinessMatrix | None) -> str:
    if matrix is None:
        return f"{len(GOVERNED_LAKE_DATASETS)}/{len(GOVERNED_LAKE_DATASETS)} governed catalog datasets"
    return f"{matrix.dataset_count}/{len(GOVERNED_LAKE_DATASETS)} governed catalog datasets"


def _is_stable_entrypoint(command_ref: str) -> bool:
    value = str(command_ref)
    return value.startswith(STABLE_ENTRYPOINT_PREFIXES)


def _matrix_from_mapping(data: Mapping[str, Any]) -> GovernedLakeReadinessMatrix:
    return GovernedLakeReadinessMatrix(
        rows=tuple(_row_from_mapping(item) for item in data.get("rows") or ()),
        operation_counts=_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or GOVERNED_LAKE_READINESS_SCHEMA),
    )


def _validation_plan_from_mapping(data: Mapping[str, Any]) -> GovernedLakeValidationPlan:
    return GovernedLakeValidationPlan(
        tasks=tuple(_validation_task_from_mapping(item) for item in data.get("tasks") or ()),
        operation_counts=_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or GOVERNED_LAKE_VALIDATION_PLAN_SCHEMA),
    )


def _conflict_policy_from_mapping(data: Mapping[str, Any]) -> GovernedLakeConflictPolicy:
    return GovernedLakeConflictPolicy(
        rows=tuple(_conflict_policy_row_from_mapping(item) for item in data.get("rows") or ()),
        operation_counts=_operation_counts(data.get("operation_counts")),
        schema_version=str(data.get("schema_version") or GOVERNED_LAKE_CONFLICT_POLICY_SCHEMA),
    )


def _conflict_policy_row_from_mapping(data: Mapping[str, Any]) -> GovernedLakeConflictPolicyRow:
    return GovernedLakeConflictPolicyRow(
        dataset=str(data.get("dataset") or ""),
        source_row_count=int(data.get("source_row_count") or 0),
        duplicate_key_group_count=int(data.get("duplicate_key_group_count") or 0),
        exact_copy_group_count=int(data.get("exact_copy_group_count") or 0),
        metadata_only_group_count=int(data.get("metadata_only_group_count") or 0),
        business_conflict_group_count=int(data.get("business_conflict_group_count") or 0),
        conflict_classification=str(data.get("conflict_classification") or ""),
        default_action=str(data.get("default_action") or ""),
        schema_normalization_required=bool(data.get("schema_normalization_required", False)),
        write_authorization_required=bool(data.get("write_authorization_required", False)),
        semantic_selection_authorized=bool(data.get("semantic_selection_authorized", False)),
        cleanup_authorized=bool(data.get("cleanup_authorized", False)),
        decision_required=tuple(str(item) for item in data.get("decision_required") or ()),
    )


def _validation_task_from_mapping(data: Mapping[str, Any]) -> GovernedLakeValidationTask:
    return GovernedLakeValidationTask(
        task_id=str(data.get("task_id") or ""),
        category=str(data.get("category") or ""),
        command_ref=str(data.get("command_ref") or ""),
        cadence=str(data.get("cadence") or ""),
        execution_mode=str(data.get("execution_mode") or ""),
        dataset_scope=str(data.get("dataset_scope") or ""),
        requires_human_gate=bool(data.get("requires_human_gate", False)),
        expected_artifact=str(data.get("expected_artifact") or ""),
        side_effects=tuple(str(item) for item in data.get("side_effects") or ()),
        notes=str(data.get("notes") or ""),
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
    "CONFLICT_ACTION_FULL_GROUP_QUARANTINE",
    "CONFLICT_ACTION_METADATA_PRECEDENCE_GATE",
    "CONFLICT_ACTION_NO_ACTION",
    "CONFLICT_CLASS_BUSINESS_CONFLICT",
    "CONFLICT_CLASS_EXACT_OR_METADATA",
    "CONFLICT_CLASS_NO_DUPLICATE_PRESSURE",
    "CONFLICT_POLICY_DATASETS",
    "GOVERNED_LAKE_DATASETS",
    "GOVERNED_LAKE_CONFLICT_POLICY_SCHEMA",
    "GOVERNED_LAKE_READINESS_SCHEMA",
    "GOVERNED_LAKE_VALIDATION_PLAN_SCHEMA",
    "GOVERNED_STATUS_PRODUCTION_READY",
    "GOVERNED_STATUS_QUARANTINED",
    "GOVERNED_STATUS_RESEARCH_READY",
    "GOVERNED_STATUS_UNSUPPORTED",
    "GovernedLakeDatasetReadiness",
    "GovernedLakeConflictPolicy",
    "GovernedLakeConflictPolicyRow",
    "GovernedLakeReadinessMatrix",
    "GovernedLakeValidationPlan",
    "GovernedLakeValidationTask",
    "GovernedRunRegistryRow",
    "PIT_REQUIRED_DATASETS",
    "PIT_STATUS_NOT_APPLICABLE",
    "PIT_STATUS_UNSUPPORTED_WITH_REASON",
    "ZERO_OPERATION_COUNTERS",
    "build_governed_lake_conflict_policy",
    "build_governed_lake_validation_plan",
    "build_governed_lake_readiness_matrix",
    "validate_governed_lake_conflict_policy",
    "validate_governed_lake_readiness_matrix",
    "validate_governed_lake_validation_plan",
]
