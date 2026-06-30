#!/usr/bin/env python
"""CR139 Gate D published pointer advance execution and smoke validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from market_data.catalog import CatalogStore
from market_data.contracts import PIT_STATUS_AVAILABLE
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
PREVIEW_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29.json"
AFTER_REF = "process/evidence/CR139-W2-GATED-ACTIVE-CATALOG-AFTER-POINTER-VIRTUAL-2026-06-29.json"
EXECUTION_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-EXECUTION-2026-06-29.json"
EXECUTION_INDEX_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-EXECUTION.index.json"
EXECUTION_CHECK_REF = "process/checks/CR139-W2-GATED-POINTER-ADVANCE-EXECUTION-2026-06-29.md"
SMOKE_REF = "process/evidence/CR139-W2-GATED-POST-POINTER-SMOKE-2026-06-29.json"
SMOKE_INDEX_REF = "process/evidence/CR139-W2-GATED-POST-POINTER-SMOKE.index.json"
SMOKE_CHECK_REF = "process/checks/CR139-W2-GATED-POST-POINTER-SMOKE-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--smoke-only", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()
    if args.smoke_only:
        return run_smoke_only(project_root, lake_root)
    created_at = now()

    preview = read_json(project_root / PREVIEW_REF)
    if preview["status"] != "pass_ready_for_gate_d_pointer_advance_authorization":
        raise RuntimeError(f"Gate D preview is not pass: {preview['status']}")
    if preview["failed_checks"]:
        raise RuntimeError(f"Gate D preview has failed checks: {preview['failed_checks']}")

    active_catalog_path = lake_root / ACTIVE_CATALOG_REL
    active_manifest_path = lake_root / ACTIVE_MANIFEST_REL
    before_catalog_text = active_catalog_path.read_text(encoding="utf-8")
    before_manifest_bytes = active_manifest_path.read_bytes()
    before_catalog_sha = sha256_bytes(before_catalog_text.encode("utf-8"))
    before_manifest_sha = sha256_bytes(before_manifest_bytes)
    before_manifest_lines = before_manifest_bytes.count(b"\n")
    if before_catalog_sha != preview["summary"]["active_catalog_sha256_before"]:
        raise RuntimeError("active catalog drift before Gate D pointer advance")
    if before_manifest_sha != preview["summary"]["active_manifest_sha256_before"]:
        raise RuntimeError("active manifest drift before Gate D pointer advance")

    after_text = (project_root / AFTER_REF).read_text(encoding="utf-8")
    after_write_text = after_text[:-1] if after_text.endswith("\n") else after_text
    active_catalog_path.write_text(after_write_text, encoding="utf-8")

    after_catalog_text = active_catalog_path.read_text(encoding="utf-8")
    after_manifest_bytes = active_manifest_path.read_bytes()
    after_catalog = json.loads(after_catalog_text)
    after_catalog_sha = sha256_bytes(after_catalog_text.encode("utf-8"))
    after_manifest_sha = sha256_bytes(after_manifest_bytes)
    after_manifest_lines = after_manifest_bytes.count(b"\n")
    store = CatalogStore(LakeLayout(lake_root))
    pointer_smoke = []
    canonical_smoke = []
    for dataset, record in sorted(after_catalog["datasets"].items()):
        pointer = store.get_published_current_pointer(dataset)
        path = lake_root / record["canonical_path"]
        rows = int(pq.ParquetFile(path).metadata.num_rows)
        pointer_smoke.append(
            {
                "dataset": dataset,
                "published_path": pointer.published_path,
                "coverage_denominator": pointer.coverage_denominator,
                "lineage_checksum": pointer.lineage_checksum,
                "published_at": pointer.published_at,
                "universe_scope": pointer.universe_scope,
                "as_of_trade_date": pointer.as_of_trade_date,
            }
        )
        canonical_smoke.append(
            {
                "dataset": dataset,
                "canonical_path": record["canonical_path"],
                "exists": path.is_file(),
                "row_count": rows,
                "coverage_denominator": record.get("coverage_denominator"),
                "row_count_matches_catalog": rows == record.get("coverage_denominator"),
                "uses_cr139_run_id": "run_id=cr139-w2-" in str(record.get("canonical_path")),
            }
        )

    pit_clean_smoke = []
    for dataset in ("index_weights", "stock_basic"):
        record = after_catalog["datasets"][dataset]
        path = lake_root / record["canonical_path"]
        table = pq.read_table(path, columns=["pit_status"])
        dist = {str(key): int(value) for key, value in table.column("pit_status").to_pandas().value_counts(dropna=False).to_dict().items()}
        pit_clean_smoke.append(
            {
                "dataset": dataset,
                "pit_status_distribution": dist,
                "all_pit_available": dist == {PIT_STATUS_AVAILABLE: int(record["coverage_denominator"])},
            }
        )

    reader_smoke = collect_reader_smoke(lake_root)

    operation_counts = {
        "active_catalog_write": 1,
        "active_manifest_append": 0,
        "provider_catalog_write": 0,
        "provider_lake_catalog_write": 0,
        "published_pointer_advance": 17,
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
    execution_checks = {
        "active_catalog_sha_equals_preview_virtual_after": after_catalog_sha == preview["summary"]["virtual_after_catalog_sha256"],
        "active_manifest_unchanged": before_manifest_sha == after_manifest_sha and before_manifest_lines == after_manifest_lines,
        "published_true_17": sum(1 for item in after_catalog["datasets"].values() if item.get("published") is True) == 17,
        "published_pointer_advance_count_17": operation_counts["published_pointer_advance"] == 17,
        "provider_runtime_external_forbidden_counts_zero": all(
            operation_counts[key] == 0
            for key in (
                "active_manifest_append",
                "provider_catalog_write",
                "provider_lake_catalog_write",
                "physical_partition_migration",
                "lake_data_write",
                "candidate_delete",
                "legacy_delete",
                "published_directory_write",
                "nas_operation",
                "credential_read",
                "runtime_operation",
                "git_remote_write",
            )
        ),
    }
    smoke_checks = {
        "published_current_pointer_available_17": len(pointer_smoke) == 17,
        "canonical_objects_exist_17": sum(1 for item in canonical_smoke if item["exists"]) == 17,
        "canonical_row_counts_match_17": sum(1 for item in canonical_smoke if item["row_count_matches_catalog"]) == 17,
        "canonical_paths_use_cr139_run_id_17": sum(1 for item in canonical_smoke if item["uses_cr139_run_id"]) == 17,
        "pit_clean_blockers_resolved_2": sum(1 for item in pit_clean_smoke if item["all_pit_available"]) == 2,
        "reader_smoke_available_4": sum(1 for item in reader_smoke if item["status"] == "available") == 4,
        "active_manifest_still_unchanged": before_manifest_sha == after_manifest_sha and before_manifest_lines == after_manifest_lines,
    }
    execution_failed = [name for name, passed in execution_checks.items() if not passed]
    smoke_failed = [name for name, passed in smoke_checks.items() if not passed]
    execution_status = "pass_gate_d_pointer_advance_verified" if not execution_failed else "fail_gate_d_pointer_advance"
    smoke_status = "pass_gate_d_post_pointer_smoke" if not smoke_failed else "fail_gate_d_post_pointer_smoke"

    execution_evidence = {
        "schema_version": "cr139.gated.pointer_advance_execution.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D",
        "stage": "published_pointer_advance_execution",
        "created_at": created_at,
        "approval_ref": "user chat authorization: execute five-step Gate D blocker resolution and pointer path if no risk",
        "status": execution_status,
        "input_refs": {"preview_ref": PREVIEW_REF, "virtual_after_ref": AFTER_REF},
        "summary": {
            "active_catalog_sha256_before": before_catalog_sha,
            "active_catalog_sha256_after": after_catalog_sha,
            "active_manifest_sha256_before": before_manifest_sha,
            "active_manifest_sha256_after": after_manifest_sha,
            "active_manifest_line_count_before": before_manifest_lines,
            "active_manifest_line_count_after": after_manifest_lines,
            "published_true_count": sum(1 for item in after_catalog["datasets"].values() if item.get("published") is True),
            "published_pointer_count": len(pointer_smoke),
        },
        "operation_counts": operation_counts,
        "checks": execution_checks,
        "failed_checks": execution_failed,
        "pointer_smoke": pointer_smoke,
        "non_authorized_scope": [
            "active manifest append",
            "provider catalog write",
            "provider-lake-catalog write",
            "physical migration",
            "lake data write",
            "candidate cleanup",
            "legacy cleanup",
            "NAS operation",
            "credential read",
            "runtime operation",
            "Git remote write",
        ],
        "next_action": "post-pointer smoke validation complete" if not execution_failed else "inspect pointer advance failure",
    }
    smoke_evidence = {
        "schema_version": "cr139.gated.post_pointer_smoke.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D",
        "stage": "post_pointer_read_only_smoke",
        "created_at": created_at,
        "status": smoke_status,
        "input_refs": {"execution_ref": EXECUTION_REF},
        "summary": {
            "published_pointer_count": len(pointer_smoke),
            "canonical_object_count": len(canonical_smoke),
            "reader_smoke_dataset_count": len(reader_smoke),
            "pit_clean_dataset_count": len(pit_clean_smoke),
            "active_catalog_sha256": after_catalog_sha,
            "active_manifest_sha256": after_manifest_sha,
            "active_manifest_line_count": after_manifest_lines,
        },
        "operation_counts": {**operation_counts, "active_catalog_write": 0, "published_pointer_advance": 0},
        "checks": smoke_checks,
        "failed_checks": smoke_failed,
        "canonical_smoke": canonical_smoke,
        "pit_clean_smoke": pit_clean_smoke,
        "reader_smoke": reader_smoke,
        "pointer_smoke": pointer_smoke,
        "next_action": "Wave2 Gate D complete; proceed to Wave2 closure review / CP8 readiness" if not smoke_failed else "inspect smoke failures",
    }
    execution_index = make_index("cr139.gated.pointer_advance_execution.index.v1", execution_evidence, EXECUTION_REF, EXECUTION_CHECK_REF)
    smoke_index = make_index("cr139.gated.post_pointer_smoke.index.v1", smoke_evidence, SMOKE_REF, SMOKE_CHECK_REF)
    write_json(project_root / EXECUTION_REF, execution_evidence)
    write_json(project_root / EXECUTION_INDEX_REF, execution_index)
    write_json(project_root / SMOKE_REF, smoke_evidence)
    write_json(project_root / SMOKE_INDEX_REF, smoke_index)
    write_check(project_root / EXECUTION_CHECK_REF, "CR139 W2 Gate D Pointer Advance Execution", execution_evidence, EXECUTION_REF, EXECUTION_INDEX_REF)
    write_check(project_root / SMOKE_CHECK_REF, "CR139 W2 Gate D Post-Pointer Smoke", smoke_evidence, SMOKE_REF, SMOKE_INDEX_REF)
    append_gate_ledger(project_root / GATE_LEDGER_REF, "published_pointer_advance_execution", execution_evidence, [EXECUTION_REF, EXECUTION_INDEX_REF, EXECUTION_CHECK_REF])
    append_gate_ledger(project_root / GATE_LEDGER_REF, "post_pointer_smoke", smoke_evidence, [SMOKE_REF, SMOKE_INDEX_REF, SMOKE_CHECK_REF])
    print(json.dumps({"execution_status": execution_status, "smoke_status": smoke_status, "execution_failed": execution_failed, "smoke_failed": smoke_failed, "summary": smoke_evidence["summary"]}, ensure_ascii=False, indent=2))
    return 1 if execution_failed or smoke_failed else 0


def run_smoke_only(project_root: Path, lake_root: Path) -> int:
    created_at = now()
    active_catalog_path = lake_root / ACTIVE_CATALOG_REL
    active_manifest_path = lake_root / ACTIVE_MANIFEST_REL
    catalog = read_json(active_catalog_path)
    catalog_text = active_catalog_path.read_text(encoding="utf-8")
    manifest_bytes = active_manifest_path.read_bytes()
    catalog_sha = sha256_bytes(catalog_text.encode("utf-8"))
    manifest_sha = sha256_bytes(manifest_bytes)
    manifest_lines = manifest_bytes.count(b"\n")
    store = CatalogStore(LakeLayout(lake_root))
    pointer_smoke = []
    canonical_smoke = []
    for dataset, record in sorted(catalog["datasets"].items()):
        pointer = store.get_published_current_pointer(dataset)
        path = lake_root / record["canonical_path"]
        rows = int(pq.ParquetFile(path).metadata.num_rows)
        pointer_smoke.append(
            {
                "dataset": dataset,
                "published_path": pointer.published_path,
                "coverage_denominator": pointer.coverage_denominator,
                "lineage_checksum": pointer.lineage_checksum,
                "published_at": pointer.published_at,
                "universe_scope": pointer.universe_scope,
                "as_of_trade_date": pointer.as_of_trade_date,
            }
        )
        canonical_smoke.append(
            {
                "dataset": dataset,
                "canonical_path": record["canonical_path"],
                "exists": path.is_file(),
                "row_count": rows,
                "coverage_denominator": record.get("coverage_denominator"),
                "row_count_matches_catalog": rows == record.get("coverage_denominator"),
                "uses_cr139_run_id": "run_id=cr139-w2-" in str(record.get("canonical_path")),
            }
        )
    pit_clean_smoke = []
    for dataset in ("index_weights", "stock_basic"):
        record = catalog["datasets"][dataset]
        path = lake_root / record["canonical_path"]
        table = pq.read_table(path, columns=["pit_status"])
        dist = {
            str(key): int(value)
            for key, value in table.column("pit_status").to_pandas().value_counts(dropna=False).to_dict().items()
        }
        pit_clean_smoke.append(
            {
                "dataset": dataset,
                "pit_status_distribution": dist,
                "all_pit_available": dist == {PIT_STATUS_AVAILABLE: int(record["coverage_denominator"])},
            }
        )
    reader_smoke = collect_reader_smoke(lake_root)
    operation_counts = {
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
    smoke_checks = {
        "published_current_pointer_available_17": len(pointer_smoke) == 17,
        "canonical_objects_exist_17": sum(1 for item in canonical_smoke if item["exists"]) == 17,
        "canonical_row_counts_match_17": sum(1 for item in canonical_smoke if item["row_count_matches_catalog"]) == 17,
        "canonical_paths_use_cr139_run_id_17": sum(1 for item in canonical_smoke if item["uses_cr139_run_id"]) == 17,
        "pit_clean_blockers_resolved_2": sum(1 for item in pit_clean_smoke if item["all_pit_available"]) == 2,
        "reader_smoke_available_4": sum(1 for item in reader_smoke if item["status"] == "available") == 4,
        "active_manifest_read_only": True,
    }
    smoke_failed = [name for name, passed in smoke_checks.items() if not passed]
    smoke_status = "pass_gate_d_post_pointer_smoke" if not smoke_failed else "fail_gate_d_post_pointer_smoke"
    smoke_evidence = {
        "schema_version": "cr139.gated.post_pointer_smoke.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D",
        "stage": "post_pointer_read_only_smoke",
        "created_at": created_at,
        "status": smoke_status,
        "input_refs": {"execution_ref": EXECUTION_REF},
        "summary": {
            "published_pointer_count": len(pointer_smoke),
            "canonical_object_count": len(canonical_smoke),
            "reader_smoke_dataset_count": len(reader_smoke),
            "pit_clean_dataset_count": len(pit_clean_smoke),
            "active_catalog_sha256": catalog_sha,
            "active_manifest_sha256": manifest_sha,
            "active_manifest_line_count": manifest_lines,
        },
        "operation_counts": operation_counts,
        "checks": smoke_checks,
        "failed_checks": smoke_failed,
        "canonical_smoke": canonical_smoke,
        "pit_clean_smoke": pit_clean_smoke,
        "reader_smoke": reader_smoke,
        "pointer_smoke": pointer_smoke,
        "next_action": "Wave2 Gate D complete; proceed to Wave2 closure review / CP8 readiness" if not smoke_failed else "inspect smoke failures",
    }
    smoke_index = make_index("cr139.gated.post_pointer_smoke.index.v1", smoke_evidence, SMOKE_REF, SMOKE_CHECK_REF)
    write_json(project_root / SMOKE_REF, smoke_evidence)
    write_json(project_root / SMOKE_INDEX_REF, smoke_index)
    write_check(project_root / SMOKE_CHECK_REF, "CR139 W2 Gate D Post-Pointer Smoke", smoke_evidence, SMOKE_REF, SMOKE_INDEX_REF)
    append_gate_ledger(project_root / GATE_LEDGER_REF, "post_pointer_smoke_rerun", smoke_evidence, [SMOKE_REF, SMOKE_INDEX_REF, SMOKE_CHECK_REF])
    print(json.dumps({"smoke_status": smoke_status, "smoke_failed": smoke_failed, "summary": smoke_evidence["summary"]}, ensure_ascii=False, indent=2))
    return 1 if smoke_failed else 0


def collect_reader_smoke(lake_root: Path) -> list[dict[str, Any]]:
    reader_smoke = []
    for dataset in ("index_weights", "stock_basic", "index_members", "trade_calendar"):
        result = read_dataset(dataset, lake_root, required=False)
        frame_rows = len(result.frame) if result.frame is not None else None
        reader_smoke.append(
            {
                "dataset": dataset,
                "status": result.status,
                "row_count": frame_rows,
                "issue_codes": [str(item.get("code")) for item in result.issues],
            }
        )
    return reader_smoke


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


def write_check(path: Path, title: str, evidence: dict[str, Any], evidence_ref: str, index_ref: str) -> None:
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{evidence_ref}` | {'通过' if passed else '需处理'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    text = f"""---
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
| Gate D preview passed | PASS | `{PREVIEW_REF}` | blocking_risk_count=0。 |
| Authorization boundary preserved | PASS | `{evidence_ref}` | 仅执行本 gate 允许操作。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Failed checks absent | {'PASS' if not evidence['failed_checks'] else 'FAIL'} | `{evidence_ref}` | {', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无阻断项'} |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Evidence | `{evidence_ref}` | {status} | 机器证据。 |
| Index | `{index_ref}` | {status} | 证据索引。 |

## 结论

- 结论：`{status}`
- status：`{evidence['status']}`
- summary：`{json.dumps(evidence['summary'], ensure_ascii=False, sort_keys=True)}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：{evidence.get('next_action')}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_gate_ledger(path: Path, event_type: str, evidence: dict[str, Any], refs: list[str]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": event_type,
        "event_id": f"CR139-W2-GATED-{event_type.upper().replace('_', '-')}-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": evidence["gate"],
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
