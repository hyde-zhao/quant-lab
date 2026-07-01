from __future__ import annotations

from market_data.catalog import CatalogEntry
from market_data.contracts import PIT_STATUS_AVAILABLE, QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE
from market_data.governed_lake import (
    BUSINESS_CONFLICT_DATASETS,
    CONFLICT_ACTION_FULL_GROUP_QUARANTINE,
    CONFLICT_ACTION_METADATA_PRECEDENCE_GATE,
    CONFLICT_CLASS_BUSINESS_CONFLICT,
    CONFLICT_CLASS_EXACT_OR_METADATA,
    CONFLICT_POLICY_DATASETS,
    GOVERNED_LAKE_DATASETS,
    GOVERNED_STATUS_PRODUCTION_READY,
    GOVERNED_STATUS_QUARANTINED,
    GOVERNED_STATUS_RESEARCH_READY,
    PIT_REQUIRED_DATASETS,
    PIT_STATUS_NOT_APPLICABLE,
    PIT_STATUS_UNSUPPORTED_WITH_REASON,
    build_governed_lake_conflict_policy,
    build_governed_lake_validation_plan,
    build_governed_lake_readiness_matrix,
    validate_governed_lake_conflict_policy,
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


def test_cr149_conflict_policy_classifies_all_business_conflicts_as_quarantine() -> None:
    policy = build_governed_lake_conflict_policy(_duplicate_split_summary())

    assert policy.dataset_count == len(CONFLICT_POLICY_DATASETS)
    assert policy.business_conflict_dataset_count == 4
    assert policy.business_conflict_group_count == 4_272_624
    assert policy.business_conflict_groups_classified_count == 4_272_624
    assert validate_governed_lake_conflict_policy(
        policy,
        expected_business_conflict_group_count=4_272_624,
    ) == ()

    rows = {row.dataset: row for row in policy.rows}
    assert rows["adj_factor"].business_conflict_group_count == 0
    assert rows["adj_factor"].conflict_classification == CONFLICT_CLASS_EXACT_OR_METADATA
    assert rows["adj_factor"].default_action == CONFLICT_ACTION_METADATA_PRECEDENCE_GATE
    for dataset in BUSINESS_CONFLICT_DATASETS:
        assert rows[dataset].conflict_classification == CONFLICT_CLASS_BUSINESS_CONFLICT
        assert rows[dataset].default_action == CONFLICT_ACTION_FULL_GROUP_QUARANTINE
        assert rows[dataset].semantic_selection_authorized is False
        assert rows[dataset].cleanup_authorized is False
        assert rows[dataset].write_authorization_required is True
    assert "approve prices schema normalization policy before write" in rows["prices"].decision_required


def test_cr149_conflict_policy_rejects_semantic_selection_and_unclassified_groups() -> None:
    policy = build_governed_lake_conflict_policy(_duplicate_split_summary()).to_dict()
    prices = next(row for row in policy["rows"] if row["dataset"] == "prices")
    prices["semantic_selection_authorized"] = True
    prices["default_action"] = "semantic_select_latest"
    trade_status = next(row for row in policy["rows"] if row["dataset"] == "trade_status")
    trade_status["conflict_classification"] = "unknown"
    policy["operation_counts"]["business_conflict_cleanup"] = 1

    codes = {
        issue["code"]
        for issue in validate_governed_lake_conflict_policy(
            policy,
            expected_business_conflict_group_count=4_272_624,
        )
    }
    assert "governed_lake_business_conflict_groups_not_fully_classified" in codes
    assert "governed_lake_business_conflict_quarantine_missing" in codes
    assert "governed_lake_business_conflict_semantic_selection_forbidden" in codes
    assert "governed_lake_business_conflict_classification_missing" in codes
    assert "governed_lake_conflict_policy_operation_counter_nonzero" in codes


def test_cr149_conflict_policy_rejects_total_mismatch_and_missing_prices_schema_gate() -> None:
    policy = build_governed_lake_conflict_policy(_duplicate_split_summary()).to_dict()
    prices = next(row for row in policy["rows"] if row["dataset"] == "prices")
    prices["decision_required"] = [
        item
        for item in prices["decision_required"]
        if item != "approve prices schema normalization policy before write"
    ]

    codes = {
        issue["code"]
        for issue in validate_governed_lake_conflict_policy(
            policy,
            expected_business_conflict_group_count=4_272_625,
        )
    }
    assert "governed_lake_conflict_policy_total_mismatch" in codes
    assert "governed_lake_prices_schema_policy_gate_missing" in codes


def _duplicate_split_summary() -> dict[str, object]:
    return {
        "dataset_summary": [
            {
                "dataset": "adj_factor",
                "source_row_count": 47_876_790,
                "duplicate_key_group_count": 17_905_960,
                "exact_copy_groups": 17_824_108,
                "metadata_only_groups": 81_852,
                "business_conflict_groups": 0,
                "schema_normalization_required": False,
            },
            {
                "dataset": "prices",
                "source_row_count": 45_660_430,
                "duplicate_key_group_count": 17_093_658,
                "exact_copy_groups": 17_011_870,
                "metadata_only_groups": 1_830,
                "business_conflict_groups": 79_958,
                "schema_normalization_required": True,
            },
            {
                "dataset": "prices_limit",
                "source_row_count": 60_172_542,
                "duplicate_key_group_count": 19_709_804,
                "exact_copy_groups": 12_264_009,
                "metadata_only_groups": 6_946_008,
                "business_conflict_groups": 499_787,
                "schema_normalization_required": False,
            },
            {
                "dataset": "events",
                "source_row_count": 713_640,
                "duplicate_key_group_count": 351_527,
                "exact_copy_groups": 340_170,
                "metadata_only_groups": 10_583,
                "business_conflict_groups": 774,
                "schema_normalization_required": False,
            },
            {
                "dataset": "trade_status",
                "source_row_count": 35_527_310,
                "duplicate_key_group_count": 17_649_508,
                "exact_copy_groups": 13_887_316,
                "metadata_only_groups": 70_087,
                "business_conflict_groups": 3_692_105,
                "schema_normalization_required": False,
            },
        ]
    }
