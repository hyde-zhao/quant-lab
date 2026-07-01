from __future__ import annotations

from market_data.catalog import CatalogEntry
from market_data.contracts import PIT_STATUS_AVAILABLE, QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE
from market_data.governed_lake import (
    BUSINESS_CONFLICT_DATASETS,
    GOVERNED_LAKE_DATASETS,
    GOVERNED_STATUS_PRODUCTION_READY,
    GOVERNED_STATUS_QUARANTINED,
    GOVERNED_STATUS_RESEARCH_READY,
    PIT_REQUIRED_DATASETS,
    PIT_STATUS_NOT_APPLICABLE,
    PIT_STATUS_UNSUPPORTED_WITH_REASON,
    build_governed_lake_validation_plan,
    build_governed_lake_readiness_matrix,
    validate_governed_lake_validation_plan,
    validate_governed_lake_readiness_matrix,
)


def _catalog_entries(*, omit_pit_for: set[str] | None = None) -> list[CatalogEntry]:
    omit = omit_pit_for or set()
    entries: list[CatalogEntry] = []
    for dataset in GOVERNED_LAKE_DATASETS:
        entries.append(
            CatalogEntry(
                dataset=dataset,
                quality_status=QUALITY_STATUS_PASS,
                dataset_status="available",
                published=True,
                readiness_status=READINESS_STATUS_AVAILABLE,
                pit_status=(
                    None
                    if dataset in omit
                    else PIT_STATUS_AVAILABLE
                    if dataset in PIT_REQUIRED_DATASETS
                    else PIT_STATUS_NOT_APPLICABLE
                ),
                source="fixture",
                source_interface=f"{dataset}.fixture",
                latest_manifest_run_id=f"run-{dataset}",
                canonical_path=f"canonical/{dataset}/1.0/current",
                published_at="2026-07-01T00:00:00+08:00",
            )
        )
    return entries


def test_cr149_governed_lake_matrix_covers_17_datasets_with_default_quarantine_policy() -> None:
    matrix = build_governed_lake_readiness_matrix(_catalog_entries())

    assert matrix.dataset_count == 17
    assert matrix.quarantined_count == len(BUSINESS_CONFLICT_DATASETS)
    assert matrix.production_ready_count == 17 - len(BUSINESS_CONFLICT_DATASETS)
    assert matrix.unsupported_count == 0
    assert {row.dataset for row in matrix.rows} == set(GOVERNED_LAKE_DATASETS)
    assert {row.dataset for row in matrix.rows if row.governed_status == GOVERNED_STATUS_QUARANTINED} == set(
        BUSINESS_CONFLICT_DATASETS
    )
    assert all(row.pit_status in {PIT_STATUS_AVAILABLE, PIT_STATUS_NOT_APPLICABLE} for row in matrix.rows)
    assert all(row.run_registry.ordering_policy == "catalog_current_pointer_order_key" for row in matrix.rows)
    assert all(not row.run_registry.deterministic_fallback_allowed for row in matrix.rows)
    assert all(value == 0 for value in matrix.operation_counts.values())
    assert validate_governed_lake_readiness_matrix(matrix) == ()


def test_cr149_governed_lake_matrix_can_mark_business_conflicts_resolved_without_cleanup() -> None:
    policies = {dataset: "resolved_current_truth" for dataset in BUSINESS_CONFLICT_DATASETS}
    matrix = build_governed_lake_readiness_matrix(_catalog_entries(), conflict_policy_by_dataset=policies)

    assert matrix.quarantined_count == 0
    assert matrix.production_ready_count == 17
    assert {row.conflict_policy for row in matrix.rows if row.dataset in BUSINESS_CONFLICT_DATASETS} == {
        "resolved_current_truth"
    }
    assert validate_governed_lake_readiness_matrix(matrix) == ()


def test_cr149_governed_lake_matrix_blocks_null_pit_and_source_run_id_lexical_ordering() -> None:
    matrix = build_governed_lake_readiness_matrix(_catalog_entries(omit_pit_for={"stock_basic"}))
    payload = matrix.to_dict()
    stock_basic = next(row for row in payload["rows"] if row["dataset"] == "stock_basic")
    stock_basic["run_registry"]["ordering_policy"] = "source_run_id_lexical_desc"
    stock_basic["run_registry"]["deterministic_fallback_allowed"] = True

    row = next(row for row in matrix.rows if row.dataset == "stock_basic")
    assert row.pit_status == PIT_STATUS_UNSUPPORTED_WITH_REASON
    assert row.governed_status == GOVERNED_STATUS_RESEARCH_READY
    codes = {issue["code"] for issue in validate_governed_lake_readiness_matrix(payload)}
    assert "governed_lake_source_run_id_lexical_ordering_forbidden" in codes
    assert "governed_lake_deterministic_fallback_not_production_ordering" in codes


def test_cr149_governed_lake_matrix_blocks_missing_dataset_and_nonzero_operations() -> None:
    matrix = build_governed_lake_readiness_matrix(
        _catalog_entries()[:-1],
        operation_counts={"lake_write": 1, "catalog_pointer_mutation": 1},
    )

    codes = {issue["code"] for issue in validate_governed_lake_readiness_matrix(matrix)}
    assert "governed_lake_dataset_missing" in codes
    assert "governed_lake_operation_counter_nonzero" in codes


def test_cr149_validation_plan_covers_recurring_checks_and_gates_nas_multinode() -> None:
    matrix = build_governed_lake_readiness_matrix(_catalog_entries())
    plan = build_governed_lake_validation_plan(matrix)

    assert plan.task_count == 7
    assert plan.auto_runnable_count == 6
    assert plan.gated_count == 1
    assert validate_governed_lake_validation_plan(plan) == ()

    tasks = {task.task_id: task for task in plan.tasks}
    assert tasks["inventory_catalog_physical_existence"].command_ref.startswith("scripts/data_lake/")
    assert tasks["golden_current_truth_profile"].command_ref == "scripts/data_lake/profile_current_truth.py"
    assert tasks["pit_reader_smoke"].command_ref == "scripts/data_lake/collect_reader_runtime_smoke.py"
    assert tasks["duplicate_profile"].command_ref == "scripts/data_lake/profile_duplicate_keys.py"
    assert tasks["governed_readiness_matrix"].command_ref.startswith("market_data.")
    assert tasks["published_pointer_local_consistency"].requires_human_gate is False
    assert tasks["nas_multinode_pointer_consistency"].requires_human_gate is True
    assert tasks["nas_multinode_pointer_consistency"].execution_mode == "human_gate_required"
    assert all(value == 0 for value in plan.operation_counts.values())


def test_cr149_validation_plan_rejects_legacy_auto_side_effects_and_missing_task() -> None:
    plan = build_governed_lake_validation_plan().to_dict()
    plan["tasks"] = [task for task in plan["tasks"] if task["task_id"] != "duplicate_profile"]
    plan["tasks"][0]["command_ref"] = "scripts/legacy/cr139/old_inventory.py"
    plan["tasks"][0]["side_effects"] = ["lake_write"]
    plan["operation_counts"]["nas_sync_or_write"] = 1

    codes = {issue["code"] for issue in validate_governed_lake_validation_plan(plan)}
    assert "governed_lake_validation_task_missing" in codes
    assert "governed_lake_validation_legacy_script_forbidden" in codes
    assert "governed_lake_validation_unstable_entrypoint" in codes
    assert "governed_lake_validation_auto_task_has_side_effects" in codes
    assert "governed_lake_validation_operation_counter_nonzero" in codes


def test_cr149_validation_plan_rejects_multinode_without_human_gate() -> None:
    plan = build_governed_lake_validation_plan().to_dict()
    multinode = next(task for task in plan["tasks"] if task["task_id"] == "nas_multinode_pointer_consistency")
    multinode["requires_human_gate"] = False
    multinode["execution_mode"] = "read_only_local"
    multinode["command_ref"] = "scripts/data_lake/run_data_lake_readiness_audit.py"

    codes = {issue["code"] for issue in validate_governed_lake_validation_plan(plan)}
    assert "governed_lake_validation_multinode_requires_gate" in codes
