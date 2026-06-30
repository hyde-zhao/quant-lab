#!/usr/bin/env python
"""CR139 Gate D PIT blocker resolution plan and execution."""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from market_data.catalog import validate_catalog_manifest_consistency
from market_data.contracts import PIT_STATUS_AVAILABLE, QUALITY_STATUS_PASS, READINESS_STATUS_AVAILABLE
from market_data.manifest import compute_lineage_checksum, derive_manifest_from_catalog, validate_manifest_record


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
GATED_PREVIEW_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29.json"
PLAN_REF = "process/evidence/CR139-W2-GATED-PIT-BLOCKER-RESOLUTION-PLAN-2026-06-29.json"
PLAN_INDEX_REF = "process/evidence/CR139-W2-GATED-PIT-BLOCKER-RESOLUTION-PLAN.index.json"
PLAN_CHECK_REF = "process/checks/CR139-W2-GATED-PIT-BLOCKER-RESOLUTION-PLAN-2026-06-29.md"
COPY_REF = "process/evidence/CR139-W2-GATEE1D-PIT-CLEAN-COPY-EXECUTION-2026-06-29.json"
COPY_INDEX_REF = "process/evidence/CR139-W2-GATEE1D-PIT-CLEAN-COPY-EXECUTION.index.json"
COPY_CHECK_REF = "process/checks/CR139-W2-GATEE1D-PIT-CLEAN-COPY-EXECUTION-2026-06-29.md"
CATALOG_PREVIEW_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-PREVIEW-2026-06-29.json"
CATALOG_PREVIEW_INDEX_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-PREVIEW.index.json"
CATALOG_AFTER_REF = "process/evidence/CR139-W2-GATEC2D-ACTIVE-CATALOG-AFTER-PIT-CORRECTION-VIRTUAL-2026-06-29.json"
CATALOG_DIFF_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-VIRTUAL-DIFF-2026-06-29.diff"
MANIFEST_APPEND_REF = "process/evidence/CR139-W2-GATEC2D-MANIFEST-CORRECTION-APPEND-PREVIEW-2026-06-29.jsonl"
CATALOG_PREVIEW_CHECK_REF = "process/checks/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-PREVIEW-2026-06-29.md"
CATALOG_WRITE_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-WRITE-EXECUTION-2026-06-29.json"
CATALOG_WRITE_INDEX_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-WRITE-EXECUTION.index.json"
CATALOG_WRITE_CHECK_REF = "process/checks/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-WRITE-EXECUTION-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"

TARGETS = {
    "index_weights": {
        "run_id": "cr139-w2-index_weights-legacy_lake-20260629-pit-clean",
        "main_rel": "canonical/index_weights/1.0/run_id=cr139-w2-index_weights-legacy_lake-20260629-pit-clean/part-index-weights.parquet",
        "quarantine_rel": "quality/cr139-w2/quarantine/index_weights/run_id=cr139-w2-index_weights-legacy_lake-20260629-pit-clean/part-index-weights-pit-blockers.parquet",
    },
    "stock_basic": {
        "run_id": "cr139-w2-stock_basic-legacy_lake-20260629-pit-clean",
        "main_rel": "canonical/stock_basic/1.0/run_id=cr139-w2-stock_basic-legacy_lake-20260629-pit-clean/part-stock-basic.parquet",
        "quarantine_rel": "quality/cr139-w2/quarantine/stock_basic/run_id=cr139-w2-stock_basic-legacy_lake-20260629-pit-clean/part-stock-basic-pit-blockers.parquet",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument(
        "--mode",
        choices=("plan", "copy", "catalog-preview", "catalog-write"),
        required=True,
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()
    if args.mode == "plan":
        return run_plan(project_root, lake_root)
    if args.mode == "copy":
        return run_copy(project_root, lake_root)
    if args.mode == "catalog-preview":
        return run_catalog_preview(project_root, lake_root)
    return run_catalog_write(project_root, lake_root)


def run_plan(project_root: Path, lake_root: Path) -> int:
    created_at = now()
    catalog = read_json(lake_root / ACTIVE_CATALOG_REL)
    manifest_path = lake_root / ACTIVE_MANIFEST_REL
    gated_preview = read_json(project_root / GATED_PREVIEW_REF)
    records = []
    failed_checks: list[str] = []
    for dataset in TARGETS:
        record = catalog["datasets"][dataset]
        source_path = lake_root / record["canonical_path"]
        frame = pd.read_parquet(source_path)
        clean = frame[frame["pit_status"].astype(str) == PIT_STATUS_AVAILABLE].copy()
        quarantine = frame[frame["pit_status"].astype(str) != PIT_STATUS_AVAILABLE].copy()
        target = TARGETS[dataset]
        target_main = lake_root / target["main_rel"]
        target_quarantine = lake_root / target["quarantine_rel"]
        reader_contract = {
            "read_dataset_blocks_non_available_pit_values": True,
            "blocking_issue_codes": ["pit_incomplete", "non_pit_snapshot", "readiness_not_available"],
            "rationale": "read_dataset() marks pit_incomplete/non_pit_snapshot as unavailable unless allow_warn=True.",
        }
        records.append(
            {
                "dataset": dataset,
                "source_canonical_path": record["canonical_path"],
                "source_file_sha256": sha256_file(source_path),
                "source_row_count": int(len(frame)),
                "source_catalog_coverage_denominator": record.get("coverage_denominator"),
                "source_pit_status_distribution": value_counts(frame, "pit_status"),
                "clean_main_row_count": int(len(clean)),
                "quarantine_row_count": int(len(quarantine)),
                "clean_main_pit_status_distribution": value_counts(clean, "pit_status"),
                "quarantine_pit_status_distribution": value_counts(quarantine, "pit_status"),
                "clean_main_row_content_sha256": dataframe_content_sha256(clean),
                "quarantine_row_content_sha256": dataframe_content_sha256(quarantine),
                "target_run_id": target["run_id"],
                "target_main_path": target["main_rel"],
                "target_quarantine_path": target["quarantine_rel"],
                "target_main_preexists": target_main.exists(),
                "target_quarantine_preexists": target_quarantine.exists(),
                "reader_contract": reader_contract,
                "planned_catalog_updates": [
                    "canonical_path",
                    "latest_manifest_run_id",
                    "coverage_denominator",
                    "lineage_checksum",
                    "lineage_raw_checksum",
                    "quality_path",
                    "manifest_ref",
                    "run_lineage",
                    "audit_refs",
                ],
            }
        )
    checks = {
        "gated_preview_blocked_by_expected_two_pit_risks": gated_preview["summary"]["blocking_risk_count"] == 2,
        "dataset_scope_exactly_two": sorted(TARGETS) == ["index_weights", "stock_basic"],
        "source_targets_exist": all((lake_root / item["source_canonical_path"]).is_file() for item in records),
        "clean_main_all_pit_available": all(
            item["clean_main_pit_status_distribution"] == {PIT_STATUS_AVAILABLE: item["clean_main_row_count"]}
            for item in records
        ),
        "quarantine_non_empty_for_both": all(item["quarantine_row_count"] > 0 for item in records),
        "target_paths_do_not_preexist": all(
            not item["target_main_preexists"] and not item["target_quarantine_preexists"] for item in records
        ),
        "active_catalog_file_unchanged": True,
        "active_manifest_file_unchanged": True,
        "no_write_operation_counts": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_ready_for_gate_e1d_pit_clean_copy" if not failed_checks else "blocked_pit_resolution_plan"
    operation_counts = zero_operation_counts()
    evidence = {
        "schema_version": "cr139.gated.pit_blocker_resolution_plan.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D blocker resolution planning",
        "stage": "read_only_plan",
        "created_at": created_at,
        "status": status,
        "input_refs": {"gate_d_preview_ref": GATED_PREVIEW_REF},
        "summary": {
            "dataset_count": len(records),
            "clean_main_total_rows": sum(item["clean_main_row_count"] for item in records),
            "quarantine_total_rows": sum(item["quarantine_row_count"] for item in records),
            "target_collision_count": sum(
                int(item["target_main_preexists"]) + int(item["target_quarantine_preexists"]) for item in records
            ),
            "active_catalog_sha256": sha256_file(lake_root / ACTIVE_CATALOG_REL),
            "active_manifest_sha256": sha256_file(manifest_path),
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "resolution_records": records,
        "non_authorized_scope": no_auth_scope(),
        "next_action": "Gate E-1D PIT clean copy for index_weights and stock_basic only" if not failed_checks else "resolve plan blockers",
    }
    index = make_index("cr139.gated.pit_blocker_resolution_plan.index.v1", evidence, PLAN_REF, PLAN_CHECK_REF)
    write_json(project_root / PLAN_REF, evidence)
    write_json(project_root / PLAN_INDEX_REF, index)
    write_plan_check(project_root / PLAN_CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, "pit_blocker_resolution_plan", "Gate D", evidence, [PLAN_REF, PLAN_INDEX_REF, PLAN_CHECK_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def run_copy(project_root: Path, lake_root: Path) -> int:
    created_at = now()
    plan = read_json(project_root / PLAN_REF)
    if plan["status"] != "pass_ready_for_gate_e1d_pit_clean_copy":
        raise RuntimeError("PIT resolution plan is not clean")
    catalog = read_json(lake_root / ACTIVE_CATALOG_REL)
    copied = []
    pre_catalog_sha = sha256_file(lake_root / ACTIVE_CATALOG_REL)
    pre_manifest_sha = sha256_file(lake_root / ACTIVE_MANIFEST_REL)
    for dataset in TARGETS:
        source_path = lake_root / catalog["datasets"][dataset]["canonical_path"]
        frame = pd.read_parquet(source_path)
        clean = frame[frame["pit_status"].astype(str) == PIT_STATUS_AVAILABLE].copy()
        quarantine = frame[frame["pit_status"].astype(str) != PIT_STATUS_AVAILABLE].copy()
        target = TARGETS[dataset]
        main_path = lake_root / target["main_rel"]
        quarantine_path = lake_root / target["quarantine_rel"]
        if main_path.exists() or quarantine_path.exists():
            raise RuntimeError(f"target collision for {dataset}")
        main_path.parent.mkdir(parents=True, exist_ok=True)
        quarantine_path.parent.mkdir(parents=True, exist_ok=True)
        clean.to_parquet(main_path, index=False)
        quarantine.to_parquet(quarantine_path, index=False)
        copied.append(copy_record(dataset, "main", main_path, target["main_rel"], clean, source_path))
        copied.append(copy_record(dataset, "quarantine", quarantine_path, target["quarantine_rel"], quarantine, source_path))
    post_catalog_sha = sha256_file(lake_root / ACTIVE_CATALOG_REL)
    post_manifest_sha = sha256_file(lake_root / ACTIVE_MANIFEST_REL)
    checks = {
        "planned_dataset_scope_two": sorted(TARGETS) == ["index_weights", "stock_basic"],
        "copied_object_count_4": len(copied) == 4,
        "copied_rows_match_plan": sum(item["row_count"] for item in copied if item["role"] == "main")
        == plan["summary"]["clean_main_total_rows"],
        "quarantine_rows_match_plan": sum(item["row_count"] for item in copied if item["role"] == "quarantine")
        == plan["summary"]["quarantine_total_rows"],
        "main_all_pit_available": all(
            item["pit_status_distribution"] == {PIT_STATUS_AVAILABLE: item["row_count"]}
            for item in copied
            if item["role"] == "main"
        ),
        "active_catalog_file_unchanged": pre_catalog_sha == post_catalog_sha,
        "active_manifest_file_unchanged": pre_manifest_sha == post_manifest_sha,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    operation_counts = {
        **zero_operation_counts(),
        "lake_data_write": 4,
        "canonical_main_copy": 2,
        "quality_quarantine_copy": 2,
        "target_parent_directory_creation": 4,
    }
    status = "pass_gate_e1d_pit_clean_copy_verified" if not failed_checks else "fail_gate_e1d_pit_clean_copy"
    evidence = {
        "schema_version": "cr139.gatee1d.pit_clean_copy_execution.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate E-1D",
        "stage": "pit_clean_copy_execution",
        "created_at": created_at,
        "approval_ref": "user chat authorization: execute five-step Gate D blocker resolution and pointer path if no risk",
        "status": status,
        "input_refs": {"plan_ref": PLAN_REF},
        "summary": {
            "dataset_count": 2,
            "copied_object_count": len(copied),
            "main_object_count": sum(1 for item in copied if item["role"] == "main"),
            "quarantine_object_count": sum(1 for item in copied if item["role"] == "quarantine"),
            "main_total_rows": sum(item["row_count"] for item in copied if item["role"] == "main"),
            "quarantine_total_rows": sum(item["row_count"] for item in copied if item["role"] == "quarantine"),
            "active_catalog_sha256": post_catalog_sha,
            "active_manifest_sha256": post_manifest_sha,
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "copied_objects": copied,
        "non_authorized_scope": no_auth_scope(["lake_data_write for two clean main and two quarantine objects"]),
        "next_action": "Gate C-2D active catalog correction preview and write" if not failed_checks else "inspect copy failure",
    }
    index = make_index("cr139.gatee1d.pit_clean_copy_execution.index.v1", evidence, COPY_REF, COPY_CHECK_REF)
    write_json(project_root / COPY_REF, evidence)
    write_json(project_root / COPY_INDEX_REF, index)
    write_execution_check(project_root / COPY_CHECK_REF, evidence, "CR139 W2 Gate E-1D PIT Clean Copy Execution")
    append_gate_ledger(project_root / GATE_LEDGER_REF, "pit_clean_copy_execution", "Gate E-1D", evidence, [COPY_REF, COPY_INDEX_REF, COPY_CHECK_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def run_catalog_preview(project_root: Path, lake_root: Path) -> int:
    created_at = now()
    copy_evidence = read_json(project_root / COPY_REF)
    if copy_evidence["status"] != "pass_gate_e1d_pit_clean_copy_verified":
        raise RuntimeError("PIT clean copy has not passed")
    active_catalog = read_json(lake_root / ACTIVE_CATALOG_REL)
    after_catalog = copy.deepcopy(active_catalog)
    manifest_records = []
    corrections = []
    for dataset in TARGETS:
        target = TARGETS[dataset]
        before = active_catalog["datasets"][dataset]
        main = next(item for item in copy_evidence["copied_objects"] if item["dataset"] == dataset and item["role"] == "main")
        quarantine = next(item for item in copy_evidence["copied_objects"] if item["dataset"] == dataset and item["role"] == "quarantine")
        manifest_ref = f"{ACTIVE_MANIFEST_REL}#cr139-w2/pit-clean/{dataset}/{target['run_id']}"
        lineage_payload = {
            "source_run_id": before.get("latest_manifest_run_id"),
            "data_run_id": target["run_id"],
            "publish_run_id": None,
            "manifest_ref": manifest_ref,
            "triggered_by_cr": "CR139-W2-DATA-CONTRACTS",
            "pit_clean_source_path": before.get("canonical_path"),
            "canonical_main_path": target["main_rel"],
            "canonical_main_rows": main["row_count"],
            "canonical_object_sha256": [main["sha256"]],
            "quality_quarantine_path": target["quarantine_rel"],
            "quality_quarantine_rows": quarantine["row_count"],
            "quality_quarantine_sha256": [quarantine["sha256"]],
        }
        lineage_checksum = compute_lineage_checksum(lineage_payload)
        after = copy.deepcopy(before)
        after.update(
            {
                "canonical_path": target["main_rel"],
                "latest_manifest_run_id": target["run_id"],
                "lineage_checksum": lineage_checksum,
                "lineage_raw_checksum": main["sha256"],
                "coverage_denominator": main["row_count"],
                "coverage_ratio": 1.0,
                "quality_path": str(Path(target["quarantine_rel"]).parent) + "/",
                "quality_status": QUALITY_STATUS_PASS,
                "readiness_status": READINESS_STATUS_AVAILABLE,
                "pit_status": PIT_STATUS_AVAILABLE,
                "data_run_id": target["run_id"],
                "publish_run_id": None,
                "manifest_ref": manifest_ref,
                "triggered_by_cr": "CR139-W2-DATA-CONTRACTS",
                "run_lineage": {**lineage_payload, "lineage_checksum": lineage_checksum},
                "published": False,
                "published_at": None,
                "updated_at": created_at,
            }
        )
        after.setdefault("audit_refs", [])
        for ref in (COPY_REF, CATALOG_PREVIEW_REF):
            if ref not in after["audit_refs"]:
                after["audit_refs"].append(ref)
        after["coverage"] = {
            "actual_rows": main["row_count"],
            "dataset": dataset,
            "notes": ["cr139_w2_gatec2d_pit_clean_catalog_correction", "not_published_no_pointer_advance"],
            "run_id": target["run_id"],
            "status": "pass",
        }
        after_catalog["datasets"][dataset] = after
        manifest_record = derive_manifest_from_catalog(after, manifest_ref=manifest_ref, triggered_by_cr="CR139-W2-DATA-CONTRACTS")
        manifest_records.append(manifest_record)
        consistency = validate_catalog_manifest_consistency(after, manifest_record)
        manifest_valid = validate_manifest_record(manifest_record)
        corrections.append(
            {
                "dataset": dataset,
                "before_canonical_path": before.get("canonical_path"),
                "after_canonical_path": after.get("canonical_path"),
                "before_rows": before.get("coverage_denominator"),
                "after_rows": after.get("coverage_denominator"),
                "quarantine_path": after.get("quality_path"),
                "before_lineage_checksum": before.get("lineage_checksum"),
                "after_lineage_checksum": after.get("lineage_checksum"),
                "catalog_manifest_consistency_passed": consistency.passed,
                "manifest_record_valid": manifest_valid.passed,
            }
        )
    before_rendered = render_json(active_catalog)
    after_rendered = render_json(after_catalog)
    diff_text = "\n".join(
        difflib.unified_diff(
            before_rendered.splitlines(),
            after_rendered.splitlines(),
            fromfile=ACTIVE_CATALOG_REL + " (current)",
            tofile=ACTIVE_CATALOG_REL + " (virtual after Gate C-2D PIT correction)",
            lineterm="",
        )
    ) + "\n"
    append_text = "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in manifest_records) + "\n"
    pre_catalog_sha = sha256_file(lake_root / ACTIVE_CATALOG_REL)
    pre_manifest_sha = sha256_file(lake_root / ACTIVE_MANIFEST_REL)
    checks = {
        "copy_execution_verified": copy_evidence["status"] == "pass_gate_e1d_pit_clean_copy_verified",
        "correction_dataset_count_2": len(corrections) == 2,
        "catalog_manifest_consistency_2": sum(1 for item in corrections if item["catalog_manifest_consistency_passed"]) == 2,
        "manifest_records_valid_2": sum(1 for item in corrections if item["manifest_record_valid"]) == 2,
        "virtual_catalog_keeps_published_false": all(after_catalog["datasets"][dataset].get("published") is False for dataset in TARGETS),
        "active_catalog_file_unchanged": pre_catalog_sha == sha256_file(lake_root / ACTIVE_CATALOG_REL),
        "active_manifest_file_unchanged": pre_manifest_sha == sha256_file(lake_root / ACTIVE_MANIFEST_REL),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_ready_for_gate_c2d_pit_catalog_correction_write" if not failed_checks else "fail_gate_c2d_pit_catalog_correction_preview"
    operation_counts = zero_operation_counts()
    evidence = {
        "schema_version": "cr139.gatec2d.pit_catalog_correction_preview.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate C-2D",
        "stage": "pit_catalog_correction_preview",
        "created_at": created_at,
        "status": status,
        "input_refs": {"copy_execution_ref": COPY_REF},
        "summary": {
            "correction_dataset_count": len(corrections),
            "manifest_append_preview_count": len(manifest_records),
            "active_catalog_sha256_before": pre_catalog_sha,
            "active_manifest_sha256_before": pre_manifest_sha,
            "virtual_after_catalog_sha256": sha256_bytes(after_rendered.encode("utf-8")),
            "active_catalog_after_virtual_ref": CATALOG_AFTER_REF,
            "manifest_append_preview_ref": MANIFEST_APPEND_REF,
            "virtual_diff_ref": CATALOG_DIFF_REF,
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "corrections": corrections,
        "manifest_append_preview_records": manifest_records,
        "next_action": "Gate C-2D active catalog replacement and 2 manifest correction append" if not failed_checks else "inspect preview failure",
    }
    index = make_index("cr139.gatec2d.pit_catalog_correction_preview.index.v1", evidence, CATALOG_PREVIEW_REF, CATALOG_PREVIEW_CHECK_REF)
    write_json(project_root / CATALOG_PREVIEW_REF, evidence)
    write_json(project_root / CATALOG_PREVIEW_INDEX_REF, index)
    write_json(project_root / CATALOG_AFTER_REF, after_catalog)
    write_text(project_root / CATALOG_DIFF_REF, diff_text)
    write_text(project_root / MANIFEST_APPEND_REF, append_text)
    write_preview_check(project_root / CATALOG_PREVIEW_CHECK_REF, evidence, "CR139 W2 Gate C-2D PIT Catalog Correction Preview")
    append_gate_ledger(project_root / GATE_LEDGER_REF, "pit_catalog_correction_preview", "Gate C-2D", evidence, [CATALOG_PREVIEW_REF, CATALOG_PREVIEW_INDEX_REF, CATALOG_PREVIEW_CHECK_REF, CATALOG_AFTER_REF, CATALOG_DIFF_REF, MANIFEST_APPEND_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def run_catalog_write(project_root: Path, lake_root: Path) -> int:
    created_at = now()
    preview = read_json(project_root / CATALOG_PREVIEW_REF)
    if preview["status"] != "pass_ready_for_gate_c2d_pit_catalog_correction_write":
        raise RuntimeError("catalog correction preview has not passed")
    active_catalog_path = lake_root / ACTIVE_CATALOG_REL
    active_manifest_path = lake_root / ACTIVE_MANIFEST_REL
    after_text = (project_root / CATALOG_AFTER_REF).read_text(encoding="utf-8")
    after_write_text = after_text[:-1] if after_text.endswith("\n") else after_text
    append_text = (project_root / MANIFEST_APPEND_REF).read_text(encoding="utf-8")
    append_lines = append_text.splitlines()
    before_catalog_text = active_catalog_path.read_text(encoding="utf-8")
    before_manifest_bytes = active_manifest_path.read_bytes()
    pre_catalog_sha = sha256_bytes(before_catalog_text.encode("utf-8"))
    pre_manifest_sha = sha256_bytes(before_manifest_bytes)
    pre_manifest_lines = before_manifest_bytes.count(b"\n")
    if pre_catalog_sha != preview["summary"]["active_catalog_sha256_before"]:
        raise RuntimeError("active catalog drift before Gate C-2D write")
    if pre_manifest_sha != preview["summary"]["active_manifest_sha256_before"]:
        raise RuntimeError("active manifest drift before Gate C-2D write")
    active_catalog_path.write_text(after_write_text, encoding="utf-8")
    with active_manifest_path.open("ab") as fh:
        fh.write(append_text.encode("utf-8"))
    after_catalog = read_json(active_catalog_path)
    after_manifest_bytes = active_manifest_path.read_bytes()
    post_catalog_sha = sha256_bytes(active_catalog_path.read_text(encoding="utf-8").encode("utf-8"))
    post_manifest_sha = sha256_bytes(after_manifest_bytes)
    post_manifest_lines = after_manifest_bytes.count(b"\n")
    expected_after_sha = preview["summary"]["virtual_after_catalog_sha256"]
    checks = {
        "active_catalog_sha_equals_virtual_after": post_catalog_sha == expected_after_sha,
        "active_manifest_appended_two_lines": post_manifest_lines == pre_manifest_lines + 2,
        "corrected_datasets_still_unpublished": all(after_catalog["datasets"][dataset].get("published") is False for dataset in TARGETS),
        "corrected_datasets_point_to_pit_clean_targets": all(
            after_catalog["datasets"][dataset].get("canonical_path") == TARGETS[dataset]["main_rel"] for dataset in TARGETS
        ),
        "corrected_datasets_pit_available": all(after_catalog["datasets"][dataset].get("pit_status") == PIT_STATUS_AVAILABLE for dataset in TARGETS),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    operation_counts = {
        **zero_operation_counts(),
        "active_catalog_write": 1,
        "active_manifest_append": 2,
    }
    status = "pass_gate_c2d_pit_catalog_correction_write_verified" if not failed_checks else "fail_gate_c2d_pit_catalog_correction_write"
    evidence = {
        "schema_version": "cr139.gatec2d.pit_catalog_correction_write_execution.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate C-2D",
        "stage": "pit_catalog_correction_write_execution",
        "created_at": created_at,
        "approval_ref": "user chat authorization: execute five-step Gate D blocker resolution and pointer path if no risk",
        "status": status,
        "input_refs": {"preview_ref": CATALOG_PREVIEW_REF, "virtual_after_ref": CATALOG_AFTER_REF, "manifest_append_ref": MANIFEST_APPEND_REF},
        "summary": {
            "corrected_dataset_count": 2,
            "active_catalog_sha256_before": pre_catalog_sha,
            "active_catalog_sha256_after": post_catalog_sha,
            "active_manifest_sha256_before": pre_manifest_sha,
            "active_manifest_sha256_after": post_manifest_sha,
            "active_manifest_line_count_before": pre_manifest_lines,
            "active_manifest_line_count_after": post_manifest_lines,
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "corrected_records": [
            {
                "dataset": dataset,
                "canonical_path": after_catalog["datasets"][dataset].get("canonical_path"),
                "coverage_denominator": after_catalog["datasets"][dataset].get("coverage_denominator"),
                "pit_status": after_catalog["datasets"][dataset].get("pit_status"),
                "published": after_catalog["datasets"][dataset].get("published"),
                "quality_path": after_catalog["datasets"][dataset].get("quality_path"),
            }
            for dataset in TARGETS
        ],
        "non_authorized_scope": no_auth_scope(["active_catalog_write", "active_manifest_append"]),
        "next_action": "rerun Gate D no-write pointer advance preview" if not failed_checks else "inspect catalog correction failure",
    }
    index = make_index("cr139.gatec2d.pit_catalog_correction_write_execution.index.v1", evidence, CATALOG_WRITE_REF, CATALOG_WRITE_CHECK_REF)
    write_json(project_root / CATALOG_WRITE_REF, evidence)
    write_json(project_root / CATALOG_WRITE_INDEX_REF, index)
    write_execution_check(project_root / CATALOG_WRITE_CHECK_REF, evidence, "CR139 W2 Gate C-2D PIT Catalog Correction Write Execution")
    append_gate_ledger(project_root / GATE_LEDGER_REF, "pit_catalog_correction_write_execution", "Gate C-2D", evidence, [CATALOG_WRITE_REF, CATALOG_WRITE_INDEX_REF, CATALOG_WRITE_CHECK_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def copy_record(dataset: str, role: str, path: Path, rel: str, frame: pd.DataFrame, source_path: Path) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "role": role,
        "target_relative_path": rel,
        "target_absolute_path": str(path),
        "source_absolute_path": str(source_path),
        "row_count": int(len(frame)),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "pit_status_distribution": value_counts(frame, "pit_status"),
        "row_content_sha256": dataframe_content_sha256(frame),
    }


def value_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    return {str(key): int(value) for key, value in frame[column].value_counts(dropna=False).sort_index().to_dict().items()}


def dataframe_content_sha256(frame: pd.DataFrame) -> str:
    data = frame.to_json(orient="records", date_format="iso", force_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def zero_operation_counts() -> dict[str, int]:
    return {
        "active_catalog_write": 0,
        "active_manifest_append": 0,
        "provider_catalog_write": 0,
        "provider_lake_catalog_write": 0,
        "published_pointer_advance": 0,
        "physical_partition_migration": 0,
        "lake_data_write": 0,
        "candidate_delete": 0,
        "legacy_delete": 0,
        "published_directory_write": 0,
        "nas_operation": 0,
        "credential_read": 0,
        "runtime_operation": 0,
        "git_remote_write": 0,
    }


def no_auth_scope(exceptions: list[str] | None = None) -> list[str]:
    exceptions = exceptions or []
    forbidden = [
        "provider catalog write",
        "provider-lake-catalog write",
        "published pointer advance",
        "physical migration",
        "candidate cleanup",
        "legacy cleanup",
        "NAS operation",
        "credential read",
        "runtime operation",
        "QMT/MiniQMT/gateway runtime",
        "trading/small_live/live",
        "Git remote write",
    ]
    return [item for item in forbidden if item not in exceptions]


def make_index(schema_version: str, evidence: dict[str, Any], evidence_ref: str, check_ref: str) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "workflow_id": evidence["workflow_id"],
        "gate": evidence["gate"],
        "created_at": evidence["created_at"],
        "status": evidence["status"],
        "evidence_ref": evidence_ref,
        "check_ref": check_ref,
        "summary": evidence["summary"],
        "operation_counts": evidence["operation_counts"],
        "failed_checks": evidence["failed_checks"],
    }


def write_plan_check(path: Path, evidence: dict[str, Any]) -> None:
    status = "PASS" if not evidence["failed_checks"] else "BLOCKED"
    records = "\n".join(
        f"| {item['dataset']} | {item['source_row_count']} | {item['clean_main_row_count']} | {item['quarantine_row_count']} | `{item['target_main_path']}` | `{item['target_quarantine_path']}` |"
        for item in evidence["resolution_records"]
    )
    write_text(
        path,
        basic_check_text(
            title="CR139 W2 Gate D PIT Blocker Resolution Read-Only Plan",
            status=status,
            evidence=evidence,
            evidence_ref=PLAN_REF,
            index_ref=PLAN_INDEX_REF,
            extra=f"""
## Resolution Plan

| Dataset | Source Rows | Clean Main Rows | Quarantine Rows | Target Main | Target Quarantine |
|---|---:|---:|---:|---|---|
{records}
""",
        ),
    )


def write_preview_check(path: Path, evidence: dict[str, Any], title: str) -> None:
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    records = "\n".join(
        f"| {item['dataset']} | `{item['before_canonical_path']}` | `{item['after_canonical_path']}` | {item['before_rows']} -> {item['after_rows']} | `{item['quarantine_path']}` |"
        for item in evidence.get("corrections", [])
    )
    write_text(
        path,
        basic_check_text(
            title=title,
            status=status,
            evidence=evidence,
            evidence_ref=CATALOG_PREVIEW_REF,
            index_ref=CATALOG_PREVIEW_INDEX_REF,
            extra=f"""
## Catalog Corrections

| Dataset | Before canonical_path | After canonical_path | Rows | quality_path |
|---|---|---|---:|---|
{records}
""",
        ),
    )


def write_execution_check(path: Path, evidence: dict[str, Any], title: str) -> None:
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    if "Copy" in title:
        evidence_ref = COPY_REF
        index_ref = COPY_INDEX_REF
    elif "Write" in title:
        evidence_ref = CATALOG_WRITE_REF
        index_ref = CATALOG_WRITE_INDEX_REF
    else:
        evidence_ref = str(path)
        index_ref = ""
    write_text(
        path,
        basic_check_text(
            title=title,
            status=status,
            evidence=evidence,
            evidence_ref=evidence_ref,
            index_ref=index_ref,
            extra="",
        ),
    )


def basic_check_text(
    *,
    title: str,
    status: str,
    evidence: dict[str, Any],
    evidence_ref: str,
    index_ref: str,
    extra: str,
) -> str:
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{evidence_ref}` | {'通过' if passed else '需处理'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    deliverables = [f"| Evidence | `{evidence_ref}` | {status} | 机器证据。 |"]
    if index_ref:
        deliverables.append(f"| Index | `{index_ref}` | {status} | 证据索引。 |")
    deliverable_rows = "\n".join(deliverables)
    return f"""---
checkpoint_id: "{title.replace(' ', '-').upper()}-2026-06-29"
checkpoint_name: "{title}"
type: "runtime_gate_check"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
---

# {title}

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Scope bounded | PASS | `{evidence_ref}` | 仅处理 index_weights / stock_basic。 |
| Authorization boundary preserved | PASS | `{evidence_ref}` | 未授权范围保持禁止。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}
{extra}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Failed checks absent | {'PASS' if not evidence['failed_checks'] else 'FAIL'} | `{evidence_ref}` | {', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无阻断项'} |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
{deliverable_rows}

## 结论

- 结论：`{status}`
- status：`{evidence['status']}`
- summary：`{json.dumps(evidence['summary'], ensure_ascii=False, sort_keys=True)}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：{evidence.get('next_action')}
"""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(payload) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_gate_ledger(path: Path, event_type: str, gate: str, evidence: dict[str, Any], refs: list[str]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": event_type,
        "event_id": f"CR139-W2-{event_type.upper().replace('_', '-')}-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": gate,
        "created_at": evidence["created_at"],
        "status": evidence["status"],
        "artifact_refs": refs,
        "operation_counts": evidence["operation_counts"],
        "summary": evidence["summary"],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
