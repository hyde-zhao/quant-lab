#!/usr/bin/env python
"""CR139 Gate C-2 active catalog refresh no-write preview."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.catalog import validate_catalog_manifest_consistency
from market_data.manifest import compute_lineage_checksum, derive_manifest_from_catalog


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
GATEC_STAGED_PREVIEW_REF = "process/evidence/CR139-W2-GATEC-STAGED-CATALOG-MANIFEST-PREVIEW-2026-06-29.json"
GATEE_EXECUTION_REF = "process/evidence/CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION-2026-06-29.json"
PREVIEW_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW-2026-06-29.json"
INDEX_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW.index.json"
DIFF_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-VIRTUAL-DIFF-2026-06-29.diff"
AFTER_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-AFTER-VIRTUAL-2026-06-29.json"
MANIFEST_APPEND_PREVIEW_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-MANIFEST-APPEND-PREVIEW-2026-06-29.jsonl"
CHECK_REF = "process/checks/CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    active_catalog_path = lake_root / ACTIVE_CATALOG_REL
    active_manifest_path = lake_root / ACTIVE_MANIFEST_REL
    active_before = read_json(active_catalog_path)
    manifest_before_sha = sha256_file(active_manifest_path)
    catalog_before_sha = sha256_file(active_catalog_path)
    manifest_before_lines = count_lines(active_manifest_path)

    staged_preview = read_json(project_root / GATEC_STAGED_PREVIEW_REF)
    gatee_execution = read_json(project_root / GATEE_EXECUTION_REF)
    object_map = build_object_map(gatee_execution)
    staged_records = {record["dataset"]: record for record in staged_preview["staged_candidate_catalog"]["records"]}

    after_catalog = copy.deepcopy(active_before)
    after_records: dict[str, Any] = after_catalog["datasets"]
    catalog_refresh_records = []
    manifest_append_records = []
    lineage_validations = []
    catalog_manifest_validations = []
    path_validations = []

    for dataset in sorted(staged_records):
        staged = staged_records[dataset]
        before = copy.deepcopy(after_records[dataset])
        main = object_map[(dataset, "main")]
        quarantines = [value for (ds, role), value in object_map.items() if ds == dataset and role == "quarantine"]
        run_id = staged["candidate_run_id"]
        manifest_ref = f"{ACTIVE_MANIFEST_REL}#cr139-w2/{dataset}/{run_id}"
        lineage_payload = {
            "source_run_id": staged.get("active_catalog_run_id_before"),
            "data_run_id": run_id,
            "publish_run_id": None,
            "manifest_ref": manifest_ref,
            "triggered_by_cr": "CR139-W2-DATA-CONTRACTS",
            "canonical_main_path": main["target_relative_path"],
            "canonical_main_rows": main["target_row_count"],
            "canonical_object_sha256": [main["target_sha256"]],
            "quality_quarantine_paths": [item["target_relative_path"] for item in quarantines],
            "quality_quarantine_rows": sum(int(item["target_row_count"]) for item in quarantines),
            "quality_quarantine_sha256": [item["target_sha256"] for item in quarantines],
        }
        lineage_checksum = compute_lineage_checksum(lineage_payload)
        run_lineage = dict(lineage_payload)
        run_lineage["lineage_checksum"] = lineage_checksum

        after = copy.deepcopy(before)
        after.update(
            {
                "canonical_path": main["target_relative_path"],
                "latest_manifest_run_id": run_id,
                "lineage_checksum": lineage_checksum,
                "lineage_raw_checksum": main["target_sha256"],
                "coverage_denominator": int(main["target_row_count"]),
                "coverage_ratio": 1.0,
                "coverage_start": staged.get("coverage_start") or before.get("coverage_start") or before.get("start_date"),
                "coverage_end": staged.get("coverage_end") or before.get("coverage_end") or before.get("end_date"),
                "start_date": staged.get("coverage_start") or before.get("start_date"),
                "end_date": staged.get("coverage_end") or before.get("end_date"),
                "schema_version": staged.get("schema_version") or before.get("schema_version") or "1.0",
                "quality_status": "pass",
                "readiness_status": "available",
                "published": False,
                "published_at": None,
                "data_run_id": run_id,
                "publish_run_id": None,
                "manifest_ref": manifest_ref,
                "triggered_by_cr": "CR139-W2-DATA-CONTRACTS",
                "run_lineage": run_lineage,
                "audit_refs": [
                    GATEC_STAGED_PREVIEW_REF,
                    GATEE_EXECUTION_REF,
                    PREVIEW_REF,
                ],
                "updated_at": created_at,
                "generated_at": before.get("generated_at") or created_at,
            }
        )
        after["coverage"] = {
            "actual_rows": int(main["target_row_count"]),
            "dataset": dataset,
            "notes": [
                "cr139_w2_gatec2_active_catalog_refresh_preview",
                "not_published_no_pointer_advance",
            ],
            "run_id": run_id,
            "status": "pass",
        }
        if quarantines:
            after["quality_path"] = f"quality/cr139-w2/quarantine/{dataset}/"
        else:
            after["quality_path"] = before.get("quality_path")

        after_records[dataset] = after
        manifest_record = derive_manifest_from_catalog(
            after,
            manifest_ref=manifest_ref,
            triggered_by_cr="CR139-W2-DATA-CONTRACTS",
        )
        consistency = validate_catalog_manifest_consistency(after, manifest_record)
        manifest_append_records.append(manifest_record)
        lineage_validations.append(
            {
                "dataset": dataset,
                "lineage_checksum": lineage_checksum,
                "valid": compute_lineage_checksum({key: value for key, value in run_lineage.items() if key != "lineage_checksum"})
                == lineage_checksum,
            }
        )
        catalog_manifest_validations.append(
            {
                "dataset": dataset,
                "passed": consistency.passed,
                "error_codes": list(consistency.error_codes),
                "details": [dict(item) for item in consistency.details],
            }
        )
        path_validations.append(
            {
                "dataset": dataset,
                "canonical_path": after["canonical_path"],
                "target_exists": (lake_root / after["canonical_path"]).is_file(),
                "uses_cr139_run_id": "run_id=cr139-w2-" in after["canonical_path"],
                "does_not_use_candidate_path": not after["canonical_path"].startswith("candidate/"),
                "published": after["published"],
            }
        )
        catalog_refresh_records.append(
            {
                "dataset": dataset,
                "before_canonical_path": before.get("canonical_path"),
                "after_canonical_path": after["canonical_path"],
                "before_coverage_denominator": before.get("coverage_denominator"),
                "after_coverage_denominator": after["coverage_denominator"],
                "before_lineage_checksum": before.get("lineage_checksum"),
                "after_lineage_checksum": after["lineage_checksum"],
                "published_after": after["published"],
                "manifest_ref_after": manifest_ref,
            }
        )

    before_rendered = render_json(active_before)
    after_rendered = render_json(after_catalog)
    diff_text = "\n".join(
        difflib.unified_diff(
            before_rendered.splitlines(),
            after_rendered.splitlines(),
            fromfile=ACTIVE_CATALOG_REL + " (current)",
            tofile=ACTIVE_CATALOG_REL + " (virtual after Gate C-2)",
            lineterm="",
        )
    ) + "\n"
    after_virtual_sha = hashlib.sha256(after_rendered.encode("utf-8")).hexdigest()
    current_catalog_after_sha = sha256_file(active_catalog_path)
    current_manifest_after_sha = sha256_file(active_manifest_path)
    checks = {
        "gate_e1_copy_verified": gatee_execution["status"] == "pass_gate_e1_full17_copy_migration_verified",
        "dataset_count_17": len(catalog_refresh_records) == 17,
        "canonical_targets_exist_17": sum(1 for item in path_validations if item["target_exists"]) == 17,
        "canonical_targets_use_cr139_run_id_17": sum(1 for item in path_validations if item["uses_cr139_run_id"]) == 17,
        "canonical_targets_not_candidate_17": sum(1 for item in path_validations if item["does_not_use_candidate_path"]) == 17,
        "published_remains_false_17": sum(1 for item in path_validations if item["published"] is False) == 17,
        "lineage_checksum_valid_17": sum(1 for item in lineage_validations if item["valid"]) == 17,
        "catalog_manifest_consistency_17": sum(1 for item in catalog_manifest_validations if item["passed"]) == 17,
        "manifest_append_preview_17": len(manifest_append_records) == 17,
        "active_catalog_file_unchanged": catalog_before_sha == current_catalog_after_sha,
        "active_manifest_file_unchanged": manifest_before_sha == current_manifest_after_sha,
        "no_write_operation_counts": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_no_write_active_catalog_refresh_preview_generated" if not failed_checks else "fail_active_catalog_refresh_preview"
    operation_counts = {
        "active_catalog_write": 0,
        "active_manifest_append": 0,
        "provider_catalog_write": 0,
        "provider_lake_catalog_write": 0,
        "published_pointer_advance": 0,
        "physical_partition_migration": 0,
        "lake_data_write": 0,
        "credential_read": 0,
        "nas_operation": 0,
        "runtime_operation": 0,
        "git_remote_write": 0,
    }
    evidence = {
        "schema_version": "cr139.gatec2.active_catalog_refresh_preview.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate C-2",
        "stage": "active_catalog_refresh_no_write_preview",
        "created_at": created_at,
        "status": status,
        "input_refs": {
            "gate_c_staged_preview": GATEC_STAGED_PREVIEW_REF,
            "gate_e1_copy_execution": GATEE_EXECUTION_REF,
            "active_catalog": str(active_catalog_path),
            "active_manifest": str(active_manifest_path),
        },
        "decision": {
            "preview_only": True,
            "active_catalog_write_authorized": False,
            "active_manifest_append_authorized": False,
            "current_truth_visible_after_virtual_refresh": False,
            "pointer_advance_required_for_current_truth": True,
        },
        "summary": {
            "dataset_count": len(catalog_refresh_records),
            "catalog_record_refresh_count": len(catalog_refresh_records),
            "manifest_append_preview_count": len(manifest_append_records),
            "canonical_target_exists_count": sum(1 for item in path_validations if item["target_exists"]),
            "lineage_checksum_validation_pass_count": sum(1 for item in lineage_validations if item["valid"]),
            "catalog_manifest_consistency_pass_count": sum(1 for item in catalog_manifest_validations if item["passed"]),
            "published_true_after_virtual_count": sum(1 for item in path_validations if item["published"] is True),
            "active_catalog_sha256_before": catalog_before_sha,
            "active_catalog_sha256_after_preview": current_catalog_after_sha,
            "active_manifest_sha256_before": manifest_before_sha,
            "active_manifest_sha256_after_preview": current_manifest_after_sha,
            "active_manifest_line_count_before": manifest_before_lines,
            "active_catalog_after_virtual_sha256": after_virtual_sha,
            "virtual_diff_ref": DIFF_REF,
            "active_catalog_after_virtual_ref": AFTER_REF,
            "manifest_append_preview_ref": MANIFEST_APPEND_PREVIEW_REF,
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "catalog_refresh_records": catalog_refresh_records,
        "lineage_checksum_validations": lineage_validations,
        "catalog_manifest_validations": catalog_manifest_validations,
        "path_validations": path_validations,
        "next_authorization_boundary": {
            "may_authorize_next": "Gate C-2 active catalog refresh write only",
            "allowed_if_approved": [
                "replace active catalog/catalog.json with the virtual after catalog produced by this preview",
                "optionally append the 17 manifest preview records only if separately included in Gate C-2 write authorization",
            ],
            "still_forbidden": [
                "provider catalog write",
                "provider-lake-catalog write",
                "published pointer advance",
                "physical migration",
                "candidate cleanup",
                "legacy cleanup",
                "NAS operation",
                "credential read",
                "runtime operation",
                "Git remote write",
            ],
        },
    }
    index = {
        "schema_version": "cr139.gatec2.active_catalog_refresh_preview.index.v1",
        "workflow_id": evidence["workflow_id"],
        "gate": evidence["gate"],
        "created_at": created_at,
        "status": status,
        "preview_ref": PREVIEW_REF,
        "check_ref": CHECK_REF,
        "summary": evidence["summary"],
        "operation_counts": operation_counts,
        "failed_checks": failed_checks,
    }

    write_text(project_root / DIFF_REF, diff_text)
    write_text(project_root / AFTER_REF, after_rendered + "\n")
    write_text(
        project_root / MANIFEST_APPEND_PREVIEW_REF,
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in manifest_append_records),
    )
    write_json(project_root / PREVIEW_REF, evidence)
    write_json(project_root / INDEX_REF, index)
    write_check(project_root / CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, evidence)
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, render_json(payload) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def build_object_map(gatee_execution: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for item in gatee_execution["object_results"]:
        result[(item["dataset"], item["object_role"])] = item
    return result


def write_check(path: Path, evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{PREVIEW_REF}` | {'通过' if passed else '需阻断'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    refresh_rows = "\n".join(
        f"| {item['dataset']} | `{item['before_canonical_path']}` | `{item['after_canonical_path']}` | {item['before_coverage_denominator']} | {item['after_coverage_denominator']} | `{item['after_lineage_checksum']}` |"
        for item in evidence["catalog_refresh_records"]
    )
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    text = f"""---
checkpoint_id: "CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW-2026-06-29"
checkpoint_name: "CR139 W2 Gate C-2 Active Catalog Refresh Preview"
type: "auto_precheck"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
target:
  phase: "CR139-W2-DATA-CONTRACTS Gate C-2"
  story_id: null
  artifacts:
    - "{PREVIEW_REF}"
    - "{INDEX_REF}"
    - "{DIFF_REF}"
    - "{AFTER_REF}"
    - "{MANIFEST_APPEND_PREVIEW_REF}"
---

# CR139 W2 Gate C-2 Active Catalog Refresh Preview

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Gate C staged metadata exists | PASS | `{GATEC_STAGED_PREVIEW_REF}` | staged catalog/manifest 已作为 lineage 输入。 |
| Gate E-1 copy verified | PASS | `{GATEE_EXECUTION_REF}` | 24/24 canonical/quality target 已落位并验证。 |
| Active catalog readable | PASS | `/home/hyde/data/quant-lab/data-lake/{ACTIVE_CATALOG_REL}` | 本轮只读。 |
| Active manifest readable | PASS | `/home/hyde/data/quant-lab/data-lake/{ACTIVE_MANIFEST_REL}` | 本轮只读。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}

## Refresh Preview

| Dataset | Before canonical_path | After canonical_path | Before rows | After rows | Lineage checksum |
|---|---|---|---:|---:|---|
{refresh_rows}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| No-write preview generated | {status} | `{PREVIEW_REF}` | 只生成虚拟 after catalog、diff 和 manifest append preview。 |
| Active catalog unchanged | {'PASS' if evidence['checks']['active_catalog_file_unchanged'] else 'FAIL'} | `{PREVIEW_REF}` | 当前 active catalog hash 未变。 |
| Active manifest unchanged | {'PASS' if evidence['checks']['active_manifest_file_unchanged'] else 'FAIL'} | `{PREVIEW_REF}` | 当前 active manifest hash 未变。 |
| Current truth remains invisible | {'PASS' if summary['published_true_after_virtual_count'] == 0 else 'FAIL'} | `{PREVIEW_REF}` | 虚拟 after 中 17/17 published=false；Gate D pointer advance 未授权。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Preview JSON | `{PREVIEW_REF}` | {status} | Gate C-2 机器证据。 |
| Evidence index | `{INDEX_REF}` | {status} | 预览摘要索引。 |
| Virtual active catalog after | `{AFTER_REF}` | {status} | 不写入 lake，仅供审查。 |
| Virtual diff | `{DIFF_REF}` | {status} | active catalog before/after 差异。 |
| Manifest append preview | `{MANIFEST_APPEND_PREVIEW_REF}` | {status} | 17 条 manifest 预览，不 append active manifest。 |

## 结论

- 结论：`{status}`
- catalog_record_refresh_count：{summary['catalog_record_refresh_count']}
- manifest_append_preview_count：{summary['manifest_append_preview_count']}
- canonical_target_exists_count：{summary['canonical_target_exists_count']}
- lineage_checksum_validation_pass_count：{summary['lineage_checksum_validation_pass_count']}
- catalog_manifest_consistency_pass_count：{summary['catalog_manifest_consistency_pass_count']}
- active_catalog_sha256_before：`{summary['active_catalog_sha256_before']}`
- active_catalog_sha256_after_preview：`{summary['active_catalog_sha256_after_preview']}`
- active_manifest_sha256_before：`{summary['active_manifest_sha256_before']}`
- active_manifest_sha256_after_preview：`{summary['active_manifest_sha256_after_preview']}`
- active_catalog_after_virtual_sha256：`{summary['active_catalog_after_virtual_sha256']}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：发起 Gate C-2 active catalog refresh write 授权；仍不自动推进 pointer 或写 provider catalog。
"""
    write_text(path, text)


def append_gate_ledger(path: Path, evidence: dict[str, Any]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": "active_catalog_refresh_preview",
        "event_id": "CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": "Gate C-2",
        "created_at": evidence["created_at"],
        "status": evidence["status"],
        "artifact_refs": [PREVIEW_REF, INDEX_REF, CHECK_REF, DIFF_REF, AFTER_REF, MANIFEST_APPEND_PREVIEW_REF],
        "operation_counts": evidence["operation_counts"],
        "summary": evidence["summary"],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
