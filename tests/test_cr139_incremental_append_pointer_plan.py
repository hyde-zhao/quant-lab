from market_data.incremental import AffectedPartition, build_incremental_append_plan
from market_data.publish import build_pointer_advance_plan


def test_incremental_append_plan_and_pointer_plan_are_non_executing():
    current_pointer = {
        "dataset": "prices",
        "schema_version": "1.0",
        "latest_manifest_run_id": "run-old",
        "coverage_end": "2026-01-30",
    }
    append_plan = build_incremental_append_plan(
        current_pointer=current_pointer,
        source_run_id="run-source",
        target_run_id="run-target",
        affected_partitions=(
            AffectedPartition(
                dataset="prices",
                schema_version="1.0",
                trade_date="2026-01-31",
            ),
        ),
    )
    pointer_plan = build_pointer_advance_plan(
        dataset="prices",
        from_run_id="run-old",
        to_run_id="run-target",
        manifest_ref="manifest/ref.jsonl",
        lineage_checksum="sha256:lineage",
        approval_id="approval-record-only",
    )

    assert append_plan.status == "planned"
    assert append_plan.execute_allowed is False
    assert append_plan.lake_write_count == 0
    assert pointer_plan.status == "planned"
    assert pointer_plan.execute_allowed is False
    assert pointer_plan.current_pointer_publish_count == 0
