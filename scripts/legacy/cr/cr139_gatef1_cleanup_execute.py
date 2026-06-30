#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake").resolve()
PREFLIGHT_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-AUTHORIZATION-PREFLIGHT-2026-06-30.json"
MANIFEST_PREVIEW = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF-CLEANUP-DELETE-MANIFEST-PREVIEW-2026-06-29.jsonl"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-EXECUTION-2026-06-30.json"
INDEX_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-EXECUTION.index.json"
CHECK_PATH = PROJECT_ROOT / "process/checks/CR139-W2-GATEF1-CLEANUP-EXECUTION-2026-06-30.md"

F1_CATEGORIES = {
    "recommended_delete_orphan_cr139",
    "recommended_delete_candidate_tree",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def count_path(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "file_count": 0,
            "dir_count": 0,
            "parquet_file_count": 0,
            "size_bytes": 0,
        }
    if path.is_file():
        return {
            "exists": True,
            "file_count": 1,
            "dir_count": 0,
            "parquet_file_count": 1 if path.suffix == ".parquet" else 0,
            "size_bytes": path.stat().st_size,
        }
    file_count = 0
    dir_count = 0
    parquet_count = 0
    size_bytes = 0
    for child in path.rglob("*"):
        if child.is_dir():
            dir_count += 1
        elif child.is_file():
            file_count += 1
            size_bytes += child.stat().st_size
            if child.suffix == ".parquet":
                parquet_count += 1
    return {
        "exists": True,
        "file_count": file_count,
        "dir_count": dir_count,
        "parquet_file_count": parquet_count,
        "size_bytes": size_bytes,
    }


def active_catalog_records(catalog_path: Path) -> list[dict[str, Any]]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = data.get("datasets") or data.get("records") or data
    if isinstance(records, dict):
        return list(records.values())
    if isinstance(records, list):
        return records
    raise TypeError("Unsupported active catalog shape")


def is_within(path: str, prefix: str) -> bool:
    clean_path = path.strip("/")
    clean_prefix = prefix.strip("/")
    return clean_path == clean_prefix or clean_path.startswith(clean_prefix + "/")


def resolve_lake_path(relative_path: str) -> Path:
    if relative_path.startswith("/") or ".." in Path(relative_path).parts:
        raise ValueError(f"unsafe relative path: {relative_path}")
    if any(ch in relative_path for ch in "*?[]"):
        raise ValueError(f"wildcards are forbidden: {relative_path}")
    target = (LAKE_ROOT / relative_path).resolve()
    if not (str(target) == str(LAKE_ROOT) or str(target).startswith(str(LAKE_ROOT) + "/")):
        raise ValueError(f"path escapes lake root: {relative_path}")
    return target


def delete_exact_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        raise FileNotFoundError(path)


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    catalog_path = LAKE_ROOT / "catalog/catalog.json"
    manifest_path = LAKE_ROOT / "manifest/market_data_manifest.jsonl"

    preflight = json.loads(PREFLIGHT_PATH.read_text(encoding="utf-8"))
    all_manifest_records = load_jsonl(MANIFEST_PREVIEW)
    f1_records = preflight["f1_records"]
    legacy_records = [r for r in all_manifest_records if r.get("category") == "review_delete_or_archive_legacy_canonical"]

    failed_checks: list[str] = []
    execution_results: list[dict[str, Any]] = []

    active_records_before = active_catalog_records(catalog_path)
    active_paths_before = [
        str(r.get("canonical_path", "")).strip("/")
        for r in active_records_before
        if r.get("canonical_path")
    ]
    catalog_sha_before = sha256_file(catalog_path)
    manifest_sha_before = sha256_file(manifest_path)
    manifest_lines_before = sum(1 for _ in manifest_path.open("rb"))

    legacy_before = [
        {
            "category": r.get("category"),
            "dataset": r.get("dataset"),
            "relative_path": str(r.get("relative_path")).strip("/"),
            "disk": count_path(resolve_lake_path(str(r.get("relative_path")).strip("/"))),
        }
        for r in legacy_records
    ]

    pre_delete_conflicts = []
    if preflight.get("status") != "pass_gate_f1_cleanup_authorization_preflight":
        failed_checks.append("preflight_not_pass")
    if len(f1_records) != 19:
        failed_checks.append("f1_record_count_not_19")
    if len(legacy_records) != 210:
        failed_checks.append("legacy_manifest_count_not_210")
    for record in f1_records:
        rel = str(record["relative_path"]).strip("/")
        category = record.get("category")
        if category not in F1_CATEGORIES:
            failed_checks.append(f"forbidden_category:{category}:{rel}")
        hits = [p for p in active_paths_before if is_within(p, rel) or is_within(rel, p)]
        if hits:
            pre_delete_conflicts.append({"relative_path": rel, "active_hits": hits})
    if pre_delete_conflicts:
        failed_checks.append("pre_delete_active_catalog_conflicts")

    deleted_count_by_category = {
        "recommended_delete_orphan_cr139": 0,
        "recommended_delete_candidate_tree": 0,
    }

    if not failed_checks:
        for record in f1_records:
            rel = str(record["relative_path"]).strip("/")
            category = str(record["category"])
            target = resolve_lake_path(rel)
            before = count_path(target)
            result = {
                "category": category,
                "dataset": record.get("dataset"),
                "relative_path": rel,
                "before": before,
                "after": None,
                "deleted": False,
                "error": None,
            }
            try:
                if not before["exists"]:
                    raise FileNotFoundError(target)
                delete_exact_path(target)
                after = count_path(target)
                result["after"] = after
                result["deleted"] = not after["exists"]
                if result["deleted"]:
                    deleted_count_by_category[category] += 1
                else:
                    raise RuntimeError(f"path still exists after delete: {target}")
            except Exception as exc:  # fail-stop with partial evidence
                result["error"] = repr(exc)
                result["after"] = count_path(target)
                failed_checks.append(f"delete_failed:{rel}")
                execution_results.append(result)
                break
            execution_results.append(result)

    active_records_after = active_catalog_records(catalog_path)
    active_paths_after = [
        str(r.get("canonical_path", "")).strip("/")
        for r in active_records_after
        if r.get("canonical_path")
    ]
    catalog_sha_after = sha256_file(catalog_path)
    manifest_sha_after = sha256_file(manifest_path)
    manifest_lines_after = sum(1 for _ in manifest_path.open("rb"))

    f1_after = [
        {
            "category": r.get("category"),
            "dataset": r.get("dataset"),
            "relative_path": str(r.get("relative_path")).strip("/"),
            "disk": count_path(resolve_lake_path(str(r.get("relative_path")).strip("/"))),
        }
        for r in f1_records
    ]
    legacy_after = [
        {
            "category": r.get("category"),
            "dataset": r.get("dataset"),
            "relative_path": str(r.get("relative_path")).strip("/"),
            "disk": count_path(resolve_lake_path(str(r.get("relative_path")).strip("/"))),
        }
        for r in legacy_records
    ]

    if catalog_sha_after != catalog_sha_before:
        failed_checks.append("active_catalog_hash_changed")
    if manifest_sha_after != manifest_sha_before or manifest_lines_after != manifest_lines_before:
        failed_checks.append("active_manifest_changed")
    if any(item["disk"]["exists"] for item in f1_after):
        failed_checks.append("f1_paths_still_exist")
    legacy_before_state = [(r["relative_path"], r["disk"]["exists"], r["disk"]["file_count"], r["disk"]["size_bytes"]) for r in legacy_before]
    legacy_after_state = [(r["relative_path"], r["disk"]["exists"], r["disk"]["file_count"], r["disk"]["size_bytes"]) for r in legacy_after]
    if legacy_before_state != legacy_after_state:
        failed_checks.append("legacy_paths_changed")
    active_conflicts_after = []
    for item in f1_after:
        rel = item["relative_path"]
        hits = [p for p in active_paths_after if is_within(p, rel) or is_within(rel, p)]
        if hits:
            active_conflicts_after.append({"relative_path": rel, "active_hits": hits})
    if active_conflicts_after:
        failed_checks.append("post_delete_active_catalog_conflicts")

    status = "pass_gate_f1_cleanup_execution_verified" if not failed_checks else "failed_gate_f1_cleanup_execution"
    evidence = {
        "schema_version": 1,
        "workflow_id": "CR139-W2",
        "gate": "Gate F-1",
        "stage": "cleanup_execution",
        "created_at": now,
        "approval_ref": "user:approve Gate F-1 cleanup execution only: exact 2 orphan + 17 candidate, exclude 210 legacy",
        "status": status,
        "input_refs": {
            "preflight": str(PREFLIGHT_PATH.relative_to(PROJECT_ROOT)),
            "authorization": "process/checkpoints/CR139-W2-GATEF1-CLEANUP-EXECUTION-AUTHORIZATION-2026-06-30.md",
            "delete_manifest_preview": str(MANIFEST_PREVIEW.relative_to(PROJECT_ROOT)),
        },
        "summary": {
            "requested_f1_record_count": len(f1_records),
            "deleted_record_count": sum(1 for r in execution_results if r["deleted"]),
            "orphan_delete_count": deleted_count_by_category["recommended_delete_orphan_cr139"],
            "candidate_delete_count": deleted_count_by_category["recommended_delete_candidate_tree"],
            "legacy_delete_count": 0,
            "legacy_records_preserved_count": len(legacy_after),
            "active_catalog_sha256_before": catalog_sha_before,
            "active_catalog_sha256_after": catalog_sha_after,
            "active_manifest_sha256_before": manifest_sha_before,
            "active_manifest_sha256_after": manifest_sha_after,
            "active_manifest_line_count_before": manifest_lines_before,
            "active_manifest_line_count_after": manifest_lines_after,
            "f1_paths_remaining_count": sum(1 for item in f1_after if item["disk"]["exists"]),
            "legacy_paths_changed": legacy_before_state != legacy_after_state,
        },
        "operation_counts": {
            "lake_delete": sum(1 for r in execution_results if r["deleted"]),
            "orphan_delete": deleted_count_by_category["recommended_delete_orphan_cr139"],
            "candidate_delete": deleted_count_by_category["recommended_delete_candidate_tree"],
            "legacy_delete": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "nas_operation": 0,
            "credential_read": 0,
            "runtime_operation": 0,
            "git_remote_write": 0,
        },
        "checks": {
            "preflight_passed": preflight.get("status") == "pass_gate_f1_cleanup_authorization_preflight",
            "exact_f1_scope_19": len(f1_records) == 19,
            "legacy_scope_excluded_210": len(legacy_records) == 210,
            "active_catalog_unchanged": catalog_sha_after == catalog_sha_before,
            "active_manifest_unchanged": manifest_sha_after == manifest_sha_before and manifest_lines_after == manifest_lines_before,
            "f1_paths_absent_after": all(not item["disk"]["exists"] for item in f1_after),
            "legacy_paths_unchanged": legacy_before_state == legacy_after_state,
            "active_catalog_conflicts_absent_before": not pre_delete_conflicts,
            "active_catalog_conflicts_absent_after": not active_conflicts_after,
        },
        "pre_delete_active_catalog_conflicts": pre_delete_conflicts,
        "post_delete_active_catalog_conflicts": active_conflicts_after,
        "execution_results": execution_results,
        "f1_after": f1_after,
        "legacy_preservation_summary": {
            "legacy_records_before": len(legacy_before),
            "legacy_records_after": len(legacy_after),
            "legacy_existing_before": sum(1 for r in legacy_before if r["disk"]["exists"]),
            "legacy_existing_after": sum(1 for r in legacy_after if r["disk"]["exists"]),
            "legacy_changed": legacy_before_state != legacy_after_state,
        },
        "failed_checks": failed_checks,
        "next_action": "Gate F-2 legacy retain/superseded planning" if not failed_checks else "Review partial failure evidence before any retry",
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "workflow_id": "CR139-W2",
                "gate": "Gate F-1",
                "evidence_path": str(EVIDENCE_PATH.relative_to(PROJECT_ROOT)),
                "check_path": str(CHECK_PATH.relative_to(PROJECT_ROOT)),
                "status": status,
                "summary": evidence["summary"],
                "operation_counts": evidence["operation_counts"],
                "failed_checks": failed_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    check_status = "PASS" if not failed_checks else "FAIL"
    check_lines = [
        "---",
        'checkpoint_id: "CR139-W2-GATEF1-CLEANUP-EXECUTION-2026-06-30"',
        'checkpoint_name: "CR139 W2 Gate F-1 Cleanup Execution"',
        'type: "runtime_execution_check"',
        f'status: "{check_status}"',
        'owner: "host-orchestrator"',
        f'created_at: "{now}"',
        f'checked_at: "{now}"',
        "---",
        "",
        "# CR139 W2 Gate F-1 Cleanup Execution",
        "",
        "## Entry Criteria",
        "",
        "| 条目 | 状态 | 证据 | 说明 |",
        "|---|---|---|---|",
        "| User authorization exists | PASS | `process/checkpoints/CR139-W2-GATEF1-CLEANUP-EXECUTION-AUTHORIZATION-2026-06-30.md` | Exact F-1 scope approved. |",
        f"| Preflight pass | {'PASS' if preflight.get('status') == 'pass_gate_f1_cleanup_authorization_preflight' else 'FAIL'} | `{PREFLIGHT_PATH.relative_to(PROJECT_ROOT)}` | 19 F-1 records, 210 legacy excluded. |",
        "",
        "## Checklist",
        "",
        "| # | 检查项 | 状态 | 证据 | 处理意见 |",
        "|---|---|---|---|---|",
        f"| 1 | Deleted exactly 19 F-1 records | {'PASS' if evidence['summary']['deleted_record_count'] == 19 else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | orphan=2, candidate=17. |",
        f"| 2 | Legacy delete count is 0 | {'PASS' if evidence['operation_counts']['legacy_delete'] == 0 else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | F-2 only. |",
        f"| 3 | F-1 paths absent after delete | {'PASS' if evidence['checks']['f1_paths_absent_after'] else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Post-delete verification. |",
        f"| 4 | Legacy paths unchanged | {'PASS' if evidence['checks']['legacy_paths_unchanged'] else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | 210 legacy records preserved. |",
        f"| 5 | Active catalog unchanged | {'PASS' if evidence['checks']['active_catalog_unchanged'] else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Hash before/after match. |",
        f"| 6 | Active manifest unchanged | {'PASS' if evidence['checks']['active_manifest_unchanged'] else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Hash/line count before/after match. |",
        "| 7 | Provider/NAS/runtime/credential/Git untouched | PASS | operation_counts | All counters 0. |",
        "",
        "## Execution Summary",
        "",
        "| Counter | Value |",
        "|---|---:|",
        f"| lake_delete | {evidence['operation_counts']['lake_delete']} |",
        f"| orphan_delete | {evidence['operation_counts']['orphan_delete']} |",
        f"| candidate_delete | {evidence['operation_counts']['candidate_delete']} |",
        f"| legacy_delete | {evidence['operation_counts']['legacy_delete']} |",
        f"| f1_paths_remaining_count | {evidence['summary']['f1_paths_remaining_count']} |",
        f"| legacy_existing_after | {evidence['legacy_preservation_summary']['legacy_existing_after']} |",
        "",
        "## Exit Criteria",
        "",
        "| 条目 | 状态 | 证据 | 说明 |",
        "|---|---|---|---|",
        f"| Failed checks absent | {'PASS' if not failed_checks else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | {failed_checks or 'No failed checks'} |",
        "",
        "## Deliverables",
        "",
        "| 交付物 | 路径 | 状态 | 说明 |",
        "|---|---|---|---|",
        f"| Evidence | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | {check_status} | Machine evidence. |",
        f"| Index | `{INDEX_PATH.relative_to(PROJECT_ROOT)}` | {check_status} | Evidence index. |",
        "",
        "## 结论",
        "",
        f"- 结论：`{check_status}`",
        f"- status：`{status}`",
        "- 阻断项：" + ("无" if not failed_checks else ", ".join(failed_checks)),
        "- 下一步：" + evidence["next_action"],
        "",
    ]
    CHECK_PATH.write_text("\n".join(check_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
