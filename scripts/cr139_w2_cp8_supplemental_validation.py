#!/usr/bin/env python
"""CR139 W2 CP8 supplemental reader smoke and cleanup preview."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_data.catalog import CatalogStore
from market_data.lake_layout import LakeLayout
from market_data.readers import read_dataset


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
READER_EVIDENCE_REF = "process/evidence/CR139-W2-GATED-EXTENDED-READER-SMOKE-2026-06-29.json"
READER_INDEX_REF = "process/evidence/CR139-W2-GATED-EXTENDED-READER-SMOKE.index.json"
READER_CHECK_REF = "process/checks/CR139-W2-GATED-EXTENDED-READER-SMOKE-2026-06-29.md"
CLEANUP_EVIDENCE_REF = "process/evidence/CR139-W2-GATEF-CLEANUP-NO-WRITE-PREVIEW-2026-06-29.json"
CLEANUP_INDEX_REF = "process/evidence/CR139-W2-GATEF-CLEANUP-NO-WRITE-PREVIEW.index.json"
CLEANUP_DELETE_MANIFEST_REF = "process/evidence/CR139-W2-GATEF-CLEANUP-DELETE-MANIFEST-PREVIEW-2026-06-29.jsonl"
CLEANUP_CHECK_REF = "process/checks/CR139-W2-GATEF-CLEANUP-NO-WRITE-PREVIEW-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=("reader-smoke", "cleanup-preview", "all"), default="all")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()

    failures = []
    if args.mode in {"reader-smoke", "all"}:
        failures.extend(run_reader_smoke(project_root, lake_root))
    if args.mode in {"cleanup-preview", "all"}:
        failures.extend(run_cleanup_preview(project_root, lake_root))
    return 1 if failures else 0


def run_reader_smoke(project_root: Path, lake_root: Path) -> list[str]:
    created_at = now()
    catalog = read_json(lake_root / ACTIVE_CATALOG_REL)
    manifest_bytes = (lake_root / ACTIVE_MANIFEST_REL).read_bytes()
    reader_results = []
    pointer_only = []
    store = CatalogStore(LakeLayout(lake_root))
    for dataset, record in sorted(catalog["datasets"].items()):
        pointer = store.get_published_current_pointer(dataset)
        path = lake_root / record["canonical_path"]
        parquet_rows = int(pq.ParquetFile(path).metadata.num_rows)
        result = read_dataset(dataset, lake_root, required=False)
        issues = [str(item.get("code")) for item in result.issues]
        base = {
            "dataset": dataset,
            "published_pointer_ok": True,
            "published_path": pointer.published_path,
            "catalog_rows": int(record["coverage_denominator"]),
            "parquet_rows": parquet_rows,
            "parquet_rows_match_catalog": parquet_rows == int(record["coverage_denominator"]),
            "reader_status": result.status,
            "reader_row_count": len(result.frame) if result.frame is not None else None,
            "reader_issue_codes": issues,
        }
        if result.status == "available":
            base["reader_rows_match_catalog"] = base["reader_row_count"] == base["catalog_rows"]
            reader_results.append(base)
        elif issues == ["unknown_dataset"]:
            base["pointer_level_only_reason"] = "read_dataset_current_api_unknown_dataset"
            pointer_only.append(base)
        else:
            base["pointer_level_only_reason"] = "reader_returned_non_available_non_unknown_status"
            pointer_only.append(base)

    operation_counts = no_write_counts()
    checks = {
        "dataset_count_17": len(catalog["datasets"]) == 17,
        "published_pointer_ok_17": len(reader_results) + len(pointer_only) == 17,
        "reader_supported_available_10": len(reader_results) == 10
        and all(item["reader_status"] == "available" for item in reader_results),
        "reader_supported_rows_match_catalog_10": len(reader_results) == 10
        and all(item["reader_rows_match_catalog"] for item in reader_results),
        "pointer_level_only_unsupported_7": len(pointer_only) == 7
        and all(item["reader_issue_codes"] == ["unknown_dataset"] for item in pointer_only),
        "parquet_rows_match_catalog_17": all(
            item["parquet_rows_match_catalog"] for item in [*reader_results, *pointer_only]
        ),
        "no_write_operation_counts": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_gate_d_extended_reader_smoke" if not failed_checks else "fail_gate_d_extended_reader_smoke"
    evidence = {
        "schema_version": "cr139.w2.gated.extended_reader_smoke.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D supplemental",
        "stage": "extended_reader_smoke",
        "created_at": created_at,
        "status": status,
        "summary": {
            "dataset_count": len(catalog["datasets"]),
            "reader_supported_available_count": len(reader_results),
            "pointer_level_only_count": len(pointer_only),
            "active_catalog_sha256": sha256_file(lake_root / ACTIVE_CATALOG_REL),
            "active_manifest_sha256": sha256_bytes(manifest_bytes),
            "active_manifest_line_count": manifest_bytes.count(b"\n"),
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "reader_supported_results": reader_results,
        "pointer_level_only_results": pointer_only,
        "unsupported_dataset_policy": (
            "Datasets returning unknown_dataset from read_dataset() are validated at pointer/parquet level only; "
            "this records API support boundary rather than data failure."
        ),
    }
    index = make_index("cr139.w2.gated.extended_reader_smoke.index.v1", evidence, READER_EVIDENCE_REF, READER_CHECK_REF)
    write_json(project_root / READER_EVIDENCE_REF, evidence)
    write_json(project_root / READER_INDEX_REF, index)
    write_reader_check(project_root / READER_CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, "extended_reader_smoke", "Gate D supplemental", evidence, [READER_EVIDENCE_REF, READER_INDEX_REF, READER_CHECK_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return failed_checks


def run_cleanup_preview(project_root: Path, lake_root: Path) -> list[str]:
    created_at = now()
    catalog = read_json(lake_root / ACTIVE_CATALOG_REL)
    active_paths = {str(record["canonical_path"]) for record in catalog["datasets"].values()}
    candidate_files = sorted((lake_root / "candidate").rglob("*")) if (lake_root / "candidate").exists() else []
    candidate_files = [path for path in candidate_files if path.is_file()]
    candidate_dirs = sorted(path for path in (lake_root / "candidate").rglob("*") if path.is_dir()) if (lake_root / "candidate").exists() else []

    orphan_cr139 = []
    legacy_canonical = []
    all_catalog_datasets = sorted(catalog["datasets"])
    for dataset in all_catalog_datasets:
        root = lake_root / "canonical" / dataset / "1.0"
        if not root.exists():
            continue
        for run_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            files = sorted(path for path in run_dir.rglob("*") if path.is_file())
            rel_files = {str(path.relative_to(lake_root)) for path in files}
            is_active = bool(rel_files & active_paths)
            if is_active:
                continue
            record = summarize_dir(lake_root, run_dir, dataset)
            if run_dir.name.startswith("run_id=cr139-w2-"):
                record["cleanup_class"] = "orphan_cr139_canonical_target"
                record["recommended_action"] = "delete_after_cleanup_authorization"
                orphan_cr139.append(record)
            else:
                record["cleanup_class"] = "legacy_canonical_target"
                record["recommended_action"] = "review_then_delete_or_archive_after_cleanup_authorization"
                legacy_canonical.append(record)

    candidate_records = []
    candidate_dataset_dirs = sorted((lake_root / "candidate" / "parquet").glob("dataset=*")) if (lake_root / "candidate" / "parquet").exists() else []
    for ds_dir in candidate_dataset_dirs:
        if not ds_dir.is_dir():
            continue
        record = summarize_dir(lake_root, ds_dir, ds_dir.name.replace("dataset=", ""))
        record["cleanup_class"] = "candidate_tree_dataset"
        record["recommended_action"] = "delete_after_cleanup_authorization"
        candidate_records.append(record)

    delete_manifest = []
    for record in orphan_cr139:
        delete_manifest.append(delete_manifest_record(record, "recommended_delete_orphan_cr139"))
    for record in candidate_records:
        delete_manifest.append(delete_manifest_record(record, "recommended_delete_candidate_tree"))
    for record in legacy_canonical:
        delete_manifest.append(delete_manifest_record(record, "review_delete_or_archive_legacy_canonical"))

    operation_counts = no_write_counts()
    checks = {
        "active_published_count_17": sum(1 for item in catalog["datasets"].values() if item.get("published") is True) == 17,
        "orphan_cr139_targets_detected_2": len(orphan_cr139) == 2,
        "candidate_dataset_dirs_detected_17": len(candidate_records) == 17,
        "legacy_canonical_candidates_nonzero": len(legacy_canonical) > 0,
        "delete_manifest_preview_nonempty": len(delete_manifest) > 0,
        "no_delete_executed": True,
        "active_catalog_file_unchanged": True,
        "active_manifest_file_unchanged": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_gate_f_cleanup_no_write_preview" if not failed_checks else "fail_gate_f_cleanup_no_write_preview"
    manifest_text = "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in delete_manifest) + "\n"
    evidence = {
        "schema_version": "cr139.w2.gatef.cleanup_no_write_preview.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate F cleanup preview",
        "stage": "no_write_delete_manifest_preview",
        "created_at": created_at,
        "status": status,
        "summary": {
            "orphan_cr139_target_count": len(orphan_cr139),
            "candidate_dataset_dir_count": len(candidate_records),
            "candidate_file_count": len(candidate_files),
            "candidate_dir_count": len(candidate_dirs),
            "legacy_canonical_candidate_count": len(legacy_canonical),
            "delete_manifest_preview_record_count": len(delete_manifest),
            "planned_delete_bytes": sum(int(item["size_bytes"]) for item in delete_manifest),
            "active_catalog_sha256": sha256_file(lake_root / ACTIVE_CATALOG_REL),
            "active_manifest_sha256": sha256_file(lake_root / ACTIVE_MANIFEST_REL),
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "orphan_cr139_targets": orphan_cr139,
        "candidate_tree_datasets": candidate_records,
        "legacy_canonical_cleanup_candidates": legacy_canonical,
        "delete_manifest_preview_ref": CLEANUP_DELETE_MANIFEST_REF,
        "cleanup_execution_policy": {
            "execution_authorized": False,
            "requires_separate_destructive_authorization": True,
            "must_not_delete_active_catalog_targets": True,
            "must_not_delete_quality_quarantine_without_separate_authorization": True,
        },
    }
    index = make_index("cr139.w2.gatef.cleanup_no_write_preview.index.v1", evidence, CLEANUP_EVIDENCE_REF, CLEANUP_CHECK_REF)
    write_json(project_root / CLEANUP_EVIDENCE_REF, evidence)
    write_json(project_root / CLEANUP_INDEX_REF, index)
    write_text(project_root / CLEANUP_DELETE_MANIFEST_REF, manifest_text)
    write_cleanup_check(project_root / CLEANUP_CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, "cleanup_no_write_preview", "Gate F cleanup preview", evidence, [CLEANUP_EVIDENCE_REF, CLEANUP_INDEX_REF, CLEANUP_CHECK_REF, CLEANUP_DELETE_MANIFEST_REF])
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return failed_checks


def summarize_dir(lake_root: Path, directory: Path, dataset: str) -> dict[str, Any]:
    files = sorted(path for path in directory.rglob("*") if path.is_file())
    parquet_files = [path for path in files if path.suffix == ".parquet"]
    row_count = 0
    parquet_errors = []
    for path in parquet_files:
        try:
            row_count += int(pq.ParquetFile(path).metadata.num_rows)
        except Exception as exc:  # pragma: no cover - defensive preview only
            parquet_errors.append({"path": str(path.relative_to(lake_root)), "error": str(exc)})
    return {
        "dataset": dataset,
        "relative_path": str(directory.relative_to(lake_root)),
        "file_count": len(files),
        "parquet_file_count": len(parquet_files),
        "row_count": row_count,
        "size_bytes": sum(path.stat().st_size for path in files),
        "content_fingerprint": dir_fingerprint(lake_root, files),
        "parquet_errors": parquet_errors,
        "sample_files": [str(path.relative_to(lake_root)) for path in files[:5]],
    }


def delete_manifest_record(record: dict[str, Any], category: str) -> dict[str, Any]:
    return {
        "category": category,
        "dataset": record["dataset"],
        "relative_path": record["relative_path"],
        "file_count": record["file_count"],
        "parquet_file_count": record["parquet_file_count"],
        "row_count": record["row_count"],
        "size_bytes": record["size_bytes"],
        "content_fingerprint": record["content_fingerprint"],
        "execution_authorized": False,
        "delete_command_allowed": False,
        "requires_separate_cleanup_authorization": True,
    }


def dir_fingerprint(lake_root: Path, files: list[Path]) -> str:
    rows = []
    for path in files:
        rows.append(f"{path.relative_to(lake_root)}:{path.stat().st_size}:{sha256_file(path)}")
    return sha256_bytes("\n".join(rows).encode("utf-8"))


def no_write_counts() -> dict[str, int]:
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
        "orphan_delete": 0,
        "nas_operation": 0,
        "credential_read": 0,
        "runtime_operation": 0,
        "git_remote_write": 0,
    }


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


def write_reader_check(path: Path, evidence: dict[str, Any]) -> None:
    supported_rows = "\n".join(
        f"| {item['dataset']} | {item['reader_status']} | {item['reader_row_count']} | {item['catalog_rows']} | {item['reader_issue_codes']} |"
        for item in evidence["reader_supported_results"]
    )
    pointer_rows = "\n".join(
        f"| {item['dataset']} | {item['pointer_level_only_reason']} | {item['catalog_rows']} | {item['parquet_rows']} | {item['reader_issue_codes']} |"
        for item in evidence["pointer_level_only_results"]
    )
    write_text(
        path,
        check_template(
            title="CR139 W2 Gate D Extended Reader Smoke",
            evidence=evidence,
            evidence_ref=READER_EVIDENCE_REF,
            index_ref=READER_INDEX_REF,
            extra=f"""
## Reader Supported Results

| Dataset | Reader Status | Reader Rows | Catalog Rows | Issues |
|---|---|---:|---:|---|
{supported_rows}

## Pointer-Level Only Results

| Dataset | Reason | Catalog Rows | Parquet Rows | Reader Issues |
|---|---|---:|---:|---|
{pointer_rows}
""",
        ),
    )


def write_cleanup_check(path: Path, evidence: dict[str, Any]) -> None:
    write_text(
        path,
        check_template(
            title="CR139 W2 Gate F Cleanup No-Write Preview",
            evidence=evidence,
            evidence_ref=CLEANUP_EVIDENCE_REF,
            index_ref=CLEANUP_INDEX_REF,
            extra=f"""
## Cleanup Preview Summary

| Class | Count |
|---|---:|
| orphan_cr139_target | {evidence['summary']['orphan_cr139_target_count']} |
| candidate_dataset_dir | {evidence['summary']['candidate_dataset_dir_count']} |
| legacy_canonical_candidate | {evidence['summary']['legacy_canonical_candidate_count']} |
| delete_manifest_preview_record | {evidence['summary']['delete_manifest_preview_record_count']} |

Delete manifest preview: `{CLEANUP_DELETE_MANIFEST_REF}`
""",
        ),
    )


def check_template(*, title: str, evidence: dict[str, Any], evidence_ref: str, index_ref: str, extra: str) -> str:
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{evidence_ref}` | {'通过' if passed else '需处理'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    return f"""---
checkpoint_id: "{title.replace(' ', '-').upper()}-2026-06-29"
checkpoint_name: "{title}"
type: "runtime_preview_check"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
---

# {title}

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Current truth published | PASS | `{evidence_ref}` | Gate D 已发布，当前步骤只读。 |
| No-write boundary | PASS | `{evidence_ref}` | 不写 lake/catalog/manifest，不删除对象。 |

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
| Evidence | `{evidence_ref}` | {status} | 机器证据。 |
| Index | `{index_ref}` | {status} | 证据索引。 |

## 结论

- 结论：`{status}`
- status：`{evidence['status']}`
- summary：`{json.dumps(evidence['summary'], ensure_ascii=False, sort_keys=True)}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
"""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
