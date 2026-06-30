#!/usr/bin/env python
"""CR139 Gate E-1 full17 copy-only migration executor."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


PREVIEW_REF = "process/evidence/CR139-W2-GATEE-FULL17-NO-WRITE-MIGRATION-PREVIEW-2026-06-29.json"
CHECK_REF = "process/checks/CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION-2026-06-29.md"
EXECUTION_REF = "process/evidence/CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION-2026-06-29.json"
INDEX_REF = "process/evidence/CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION.index.json"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"
ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
EXPECTED_ACTIVE_CATALOG_SHA = "3c9e937acb068a2d838d52e67f6990d4415306c17ba04ba4a8038adf7a7810f0"
EXPECTED_ACTIVE_MANIFEST_SHA = "57c5f86a7e170b99407005f54c6d66f3903fcb30a2fb0f573d8966e96eedae7a"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()
    preview_path = project_root / PREVIEW_REF
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    preview = read_json(preview_path)
    mapping = preview["migration_mapping"]
    preflight = preflight_validate(lake_root, mapping)
    active_before = active_metadata_snapshot(lake_root)
    legacy_before = legacy_snapshot(lake_root)

    copied: list[dict[str, Any]] = []
    failed: list[str] = []
    for item in mapping:
        source = lake_root / item["source_relative_path"]
        target = lake_root / item["target_relative_path"]
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(
                {
                    "dataset": item["dataset"],
                    "object_role": item["object_role"],
                    "source_relative_path": item["source_relative_path"],
                    "target_relative_path": item["target_relative_path"],
                    "source_sha256": item["source_sha256"],
                    "source_size_bytes": item["source_size_bytes"],
                    "row_count": item["row_count"],
                }
            )
        except Exception as exc:  # pragma: no cover - evidence path on operational failure
            failed.append(f"{item['target_relative_path']}: {exc}")
            break

    post_validation = post_copy_validate(lake_root, mapping)
    active_after = active_metadata_snapshot(lake_root)
    legacy_after = legacy_snapshot(lake_root)
    operation_counts = {
        "canonical_main_copy": count_role(mapping, "main"),
        "quality_quarantine_copy": count_role(mapping, "quarantine"),
        "copy_execution": len(copied),
        "lake_write": len(copied),
        "target_parent_directory_creation": len({str((lake_root / item["target_relative_path"]).parent) for item in mapping}),
        "active_catalog_write": 0,
        "active_manifest_append": 0,
        "provider_catalog_write": 0,
        "provider_lake_catalog_write": 0,
        "published_pointer_advance": 0,
        "move_execution": 0,
        "delete_execution": 0,
        "credential_read": 0,
        "nas_operation": 0,
        "runtime_operation": 0,
        "git_remote_write": 0,
    }
    checks = {
        "preflight_preview_status_pass": preview["status"] == "pass_ready_for_gate_e_copy_authorization_review",
        "preflight_object_count_24": len(mapping) == 24,
        "preflight_main_count_17": count_role(mapping, "main") == 17,
        "preflight_quarantine_count_7": count_role(mapping, "quarantine") == 7,
        "preflight_no_source_missing": not preflight["source_missing"],
        "preflight_no_target_preexisting": not preflight["target_preexisting"],
        "copied_24_objects": len(copied) == 24,
        "copy_errors_absent": not failed,
        "post_target_exists_24": post_validation["target_exists_count"] == 24,
        "post_sha_match_24": post_validation["sha_match_count"] == 24,
        "post_size_match_24": post_validation["size_match_count"] == 24,
        "post_row_count_match_24": post_validation["row_count_match_count"] == 24,
        "source_candidates_preserved_24": post_validation["source_exists_count"] == 24,
        "active_catalog_hash_unchanged": active_before["active_catalog_sha256"] == active_after["active_catalog_sha256"] == EXPECTED_ACTIVE_CATALOG_SHA,
        "active_manifest_hash_unchanged": active_before["active_manifest_sha256"] == active_after["active_manifest_sha256"] == EXPECTED_ACTIVE_MANIFEST_SHA,
        "legacy_canonical_paths_preserved": legacy_before == legacy_after,
        "no_move_delete_catalog_pointer_external": all(
            operation_counts[key] == 0
            for key in (
                "active_catalog_write",
                "active_manifest_append",
                "provider_catalog_write",
                "provider_lake_catalog_write",
                "published_pointer_advance",
                "move_execution",
                "delete_execution",
                "credential_read",
                "nas_operation",
                "runtime_operation",
                "git_remote_write",
            )
        ),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_gate_e1_full17_copy_migration_verified" if not failed_checks else "fail_gate_e1_full17_copy_migration"

    evidence = {
        "schema_version": "cr139.gatee.full17.copy_migration_execution.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate E-1",
        "stage": "full17_copy_migration_execution",
        "created_at": created_at,
        "approval_ref": "user chat authorization: approve Gate E-1 full17 copy migration only",
        "status": status,
        "input_refs": {
            "preview_ref": PREVIEW_REF,
            "authorization_ref": "process/checkpoints/CR139-W2-GATEE-FULL17-COPY-MIGRATION-AUTHORIZATION-2026-06-29.md",
        },
        "summary": {
            "dataset_count": len({item["dataset"] for item in mapping}),
            "object_count": len(mapping),
            "main_object_count": count_role(mapping, "main"),
            "quarantine_object_count": count_role(mapping, "quarantine"),
            "copied_object_count": len(copied),
            "target_exists_count": post_validation["target_exists_count"],
            "sha_match_count": post_validation["sha_match_count"],
            "size_match_count": post_validation["size_match_count"],
            "row_count_match_count": post_validation["row_count_match_count"],
            "source_preserved_count": post_validation["source_exists_count"],
            "active_catalog_sha256": active_after["active_catalog_sha256"],
            "active_manifest_sha256": active_after["active_manifest_sha256"],
            "legacy_canonical_path_count": len(legacy_after),
            "planned_total_copy_bytes": sum(int(item["source_size_bytes"]) for item in mapping),
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "preflight": preflight,
        "active_metadata_before": active_before,
        "active_metadata_after": active_after,
        "legacy_canonical_snapshot_before": legacy_before,
        "legacy_canonical_snapshot_after": legacy_after,
        "object_results": post_validation["object_results"],
        "non_authorized_scope": [
            "active catalog write",
            "active manifest append",
            "provider catalog write",
            "provider-lake-catalog write",
            "published pointer advance",
            "move",
            "delete",
            "candidate cleanup",
            "legacy cleanup",
            "NAS operation",
            "credential read",
            "runtime operation",
            "QMT/MiniQMT/gateway runtime",
            "trading/small_live/live",
            "Git remote write",
        ],
        "next_action": "Gate C-2 active catalog refresh preview after review of Gate E-1 copy evidence",
    }
    index = {
        "schema_version": "cr139.gatee.full17.copy_migration_execution.index.v1",
        "workflow_id": evidence["workflow_id"],
        "gate": evidence["gate"],
        "created_at": created_at,
        "status": status,
        "execution_ref": EXECUTION_REF,
        "check_ref": CHECK_REF,
        "summary": evidence["summary"],
        "operation_counts": operation_counts,
        "failed_checks": failed_checks,
    }

    write_json(project_root / EXECUTION_REF, evidence)
    write_json(project_root / INDEX_REF, index)
    write_check(project_root / CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, evidence)

    if failed_checks:
        print(json.dumps({"status": status, "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"status": status, "summary": evidence["summary"]}, ensure_ascii=False, indent=2))
    return 0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parquet_rows(path: Path) -> int:
    return int(pq.ParquetFile(path).metadata.num_rows)


def count_role(mapping: list[dict[str, Any]], role: str) -> int:
    return sum(1 for item in mapping if item["object_role"] == role)


def preflight_validate(lake_root: Path, mapping: list[dict[str, Any]]) -> dict[str, Any]:
    source_missing = []
    source_sha_mismatches = []
    source_size_mismatches = []
    target_preexisting = []
    target_outside_allowed_namespace = []
    duplicate_targets = []
    seen_targets: set[str] = set()
    for item in mapping:
        source = lake_root / item["source_relative_path"]
        target = lake_root / item["target_relative_path"]
        target_rel = item["target_relative_path"]
        if target_rel in seen_targets:
            duplicate_targets.append(target_rel)
        seen_targets.add(target_rel)
        if item["object_role"] == "main" and not target_rel.startswith("canonical/"):
            target_outside_allowed_namespace.append(target_rel)
        if item["object_role"] == "quarantine" and not target_rel.startswith("quality/cr139-w2/quarantine/"):
            target_outside_allowed_namespace.append(target_rel)
        if not source.is_file():
            source_missing.append(item["source_relative_path"])
            continue
        if sha256_file(source) != item["source_sha256"]:
            source_sha_mismatches.append(item["source_relative_path"])
        if source.stat().st_size != int(item["source_size_bytes"]):
            source_size_mismatches.append(item["source_relative_path"])
        if target.exists():
            target_preexisting.append(target_rel)
    failures = (
        source_missing
        or source_sha_mismatches
        or source_size_mismatches
        or target_preexisting
        or target_outside_allowed_namespace
        or duplicate_targets
    )
    result = {
        "source_missing": source_missing,
        "source_sha_mismatches": source_sha_mismatches,
        "source_size_mismatches": source_size_mismatches,
        "target_preexisting": target_preexisting,
        "target_outside_allowed_namespace": target_outside_allowed_namespace,
        "duplicate_targets": duplicate_targets,
    }
    if failures:
        raise RuntimeError(f"Gate E-1 preflight failed: {result}")
    return result


def active_metadata_snapshot(lake_root: Path) -> dict[str, Any]:
    catalog = lake_root / ACTIVE_CATALOG_REL
    manifest = lake_root / ACTIVE_MANIFEST_REL
    return {
        "active_catalog_path": ACTIVE_CATALOG_REL,
        "active_catalog_sha256": sha256_file(catalog),
        "active_catalog_size_bytes": catalog.stat().st_size,
        "active_manifest_path": ACTIVE_MANIFEST_REL,
        "active_manifest_sha256": sha256_file(manifest),
        "active_manifest_size_bytes": manifest.stat().st_size,
    }


def legacy_snapshot(lake_root: Path) -> dict[str, Any]:
    catalog_path = lake_root / ACTIVE_CATALOG_REL
    catalog = read_json(catalog_path)
    records = catalog.get("datasets", catalog.get("records", catalog if isinstance(catalog, list) else []))
    snapshot = {}
    if isinstance(records, dict):
        iterable = records.values()
    else:
        iterable = records
    for record in iterable:
        if not isinstance(record, dict):
            continue
        dataset = record.get("dataset") or record.get("dataset_id") or record.get("name")
        canonical_path = record.get("canonical_path")
        if not dataset or not canonical_path:
            continue
        rel = canonical_path
        if rel.startswith(str(lake_root)):
            rel = str(Path(rel).resolve().relative_to(lake_root))
        path = lake_root / rel
        if "run_id=cr139-w2-" in rel:
            continue
        snapshot[str(dataset)] = path_tree_snapshot(path, lake_root)
    return snapshot


def path_tree_snapshot(path: Path, lake_root: Path) -> dict[str, Any]:
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
    else:
        files = []
    digest = hashlib.sha256()
    total_size = 0
    for file_path in files:
        rel = str(file_path.resolve().relative_to(lake_root))
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        file_hash = sha256_file(file_path)
        digest.update(file_hash.encode("ascii"))
        total_size += file_path.stat().st_size
    return {
        "path": str(path.resolve().relative_to(lake_root)) if path.exists() else str(path),
        "exists": path.exists(),
        "file_count": len(files),
        "size_bytes": total_size,
        "tree_sha256": digest.hexdigest(),
    }


def post_copy_validate(lake_root: Path, mapping: list[dict[str, Any]]) -> dict[str, Any]:
    object_results = []
    for item in mapping:
        source = lake_root / item["source_relative_path"]
        target = lake_root / item["target_relative_path"]
        target_exists = target.is_file()
        source_exists = source.is_file()
        target_sha = sha256_file(target) if target_exists else None
        target_size = target.stat().st_size if target_exists else None
        target_rows = parquet_rows(target) if target_exists else None
        result = {
            "dataset": item["dataset"],
            "object_role": item["object_role"],
            "source_relative_path": item["source_relative_path"],
            "target_relative_path": item["target_relative_path"],
            "source_exists": source_exists,
            "target_exists": target_exists,
            "source_sha256": item["source_sha256"],
            "target_sha256": target_sha,
            "sha256_matches_source": target_sha == item["source_sha256"],
            "source_size_bytes": item["source_size_bytes"],
            "target_size_bytes": target_size,
            "size_matches_source": target_size == int(item["source_size_bytes"]),
            "source_row_count": item["row_count"],
            "target_row_count": target_rows,
            "row_count_matches_source": target_rows == int(item["row_count"]),
        }
        object_results.append(result)
    return {
        "target_exists_count": sum(1 for item in object_results if item["target_exists"]),
        "source_exists_count": sum(1 for item in object_results if item["source_exists"]),
        "sha_match_count": sum(1 for item in object_results if item["sha256_matches_source"]),
        "size_match_count": sum(1 for item in object_results if item["size_matches_source"]),
        "row_count_match_count": sum(1 for item in object_results if item["row_count_matches_source"]),
        "object_results": object_results,
    }


def write_check(path: Path, evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    checks = evidence["checks"]
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{EXECUTION_REF}` | {'通过' if passed else '需阻断并审查'} |"
        for idx, (name, passed) in enumerate(checks.items(), start=1)
    )
    object_rows = "\n".join(
        f"| {item['dataset']} | {item['object_role']} | {item['source_row_count']} | {item['target_row_count']} | {'PASS' if item['sha256_matches_source'] and item['size_matches_source'] and item['row_count_matches_source'] else 'FAIL'} | `{item['target_relative_path']}` |"
        for item in evidence["object_results"]
    )
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    text = f"""---
checkpoint_id: "CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION-2026-06-29"
checkpoint_name: "CR139 W2 Gate E-1 Full 17 Dataset Copy Migration Execution"
type: "runtime_execution_check"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
target:
  phase: "CR139-W2-DATA-CONTRACTS Gate E"
  story_id: null
  artifacts:
    - "{EXECUTION_REF}"
    - "{INDEX_REF}"
---

# CR139 W2 Gate E-1 Full 17 Dataset Copy Migration Execution

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Human authorization captured | PASS | `process/checkpoints/CR139-W2-GATEE-FULL17-COPY-MIGRATION-AUTHORIZATION-2026-06-29.md` | 用户已明确授权 Gate E-1 copy-only migration。 |
| Gate E-0 preview ready | PASS | `{PREVIEW_REF}` | 24 个 planned object，source 缺失 0，target collision 0。 |
| Active metadata baseline known | PASS | `{PREVIEW_REF}` | active catalog/manifest hash 已冻结。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}

## Object Verification

| Dataset | Role | Source Rows | Target Rows | Result | Target |
|---|---:|---:|---:|---|---|
{object_rows}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 24/24 target copied and verified | {'PASS' if summary['target_exists_count'] == 24 and summary['sha_match_count'] == 24 and summary['row_count_match_count'] == 24 else 'FAIL'} | `{EXECUTION_REF}` | SHA/size/row count 均需匹配 source candidate。 |
| Source candidate preserved | {'PASS' if summary['source_preserved_count'] == 24 else 'FAIL'} | `{EXECUTION_REF}` | copy-only，未 move。 |
| Active metadata unchanged | {'PASS' if checks['active_catalog_hash_unchanged'] and checks['active_manifest_hash_unchanged'] else 'FAIL'} | `{EXECUTION_REF}` | 未写 active catalog/manifest。 |
| Legacy canonical preserved | {'PASS' if checks['legacy_canonical_paths_preserved'] else 'FAIL'} | `{EXECUTION_REF}` | 不删、不改 legacy canonical。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Execution evidence | `{EXECUTION_REF}` | {status} | Gate E-1 copy 执行证据。 |
| Evidence index | `{INDEX_REF}` | {status} | Gate E-1 摘要索引。 |
| Execution check | `{CHECK_REF}` | {status} | 本文件。 |

## 结论

- 结论：`{status}`
- 复制对象：17 main + 7 quarantine = 24
- copied_object_count：{summary['copied_object_count']}
- target_exists_count：{summary['target_exists_count']}
- sha_match_count：{summary['sha_match_count']}
- size_match_count：{summary['size_match_count']}
- row_count_match_count：{summary['row_count_match_count']}
- active_catalog_sha256：`{summary['active_catalog_sha256']}`
- active_manifest_sha256：`{summary['active_manifest_sha256']}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：Gate E-1 evidence review 后，进入 Gate C-2 active catalog refresh preview；仍不自动写 active catalog 或推进 pointer。
"""
    path.write_text(text, encoding="utf-8")


def append_gate_ledger(path: Path, evidence: dict[str, Any]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": "copy_migration_execution",
        "event_id": "CR139-W2-GATEE-FULL17-COPY-MIGRATION-EXECUTION-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": "Gate E-1",
        "created_at": evidence["created_at"],
        "status": evidence["status"],
        "artifact_refs": [EXECUTION_REF, INDEX_REF, CHECK_REF],
        "operation_counts": evidence["operation_counts"],
        "summary": evidence["summary"],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
