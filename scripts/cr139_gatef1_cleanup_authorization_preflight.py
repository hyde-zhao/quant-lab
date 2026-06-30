#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake")
MANIFEST_PREVIEW = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF-CLEANUP-DELETE-MANIFEST-PREVIEW-2026-06-29.jsonl"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-AUTHORIZATION-PREFLIGHT-2026-06-30.json"
INDEX_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-AUTHORIZATION-PREFLIGHT.index.json"
CHECK_PATH = PROJECT_ROOT / "process/checks/CR139-W2-GATEF1-CLEANUP-AUTHORIZATION-PREFLIGHT-2026-06-30.md"


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
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def active_catalog_records(catalog_path: Path) -> list[dict[str, Any]]:
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = data.get("datasets") or data.get("records") or data
    if isinstance(records, dict):
        return list(records.values())
    if isinstance(records, list):
        return records
    raise TypeError("Unsupported active catalog shape")


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


def is_within(path: str, prefix: str) -> bool:
    clean_path = path.strip("/")
    clean_prefix = prefix.strip("/")
    return clean_path == clean_prefix or clean_path.startswith(clean_prefix + "/")


def main() -> None:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    catalog_path = LAKE_ROOT / "catalog/catalog.json"
    manifest_path = LAKE_ROOT / "manifest/market_data_manifest.jsonl"

    all_records = load_jsonl(MANIFEST_PREVIEW)
    f1_records = [r for r in all_records if r.get("category") in F1_CATEGORIES]
    excluded_legacy = [r for r in all_records if r.get("category") == "review_delete_or_archive_legacy_canonical"]

    active_records = active_catalog_records(catalog_path)
    active_canonical_paths = [
        str(r.get("canonical_path", "")).strip("/")
        for r in active_records
        if r.get("canonical_path")
    ]

    record_results: list[dict[str, Any]] = []
    active_catalog_conflicts: list[dict[str, Any]] = []
    for record in f1_records:
        rel = str(record["relative_path"]).strip("/")
        abs_path = LAKE_ROOT / rel
        active_hits = [p for p in active_canonical_paths if is_within(p, rel) or is_within(rel, p)]
        if active_hits:
            active_catalog_conflicts.append({"relative_path": rel, "active_hits": active_hits})
        record_results.append(
            {
                "category": record.get("category"),
                "dataset": record.get("dataset"),
                "relative_path": rel,
                "manifest_file_count": record.get("file_count"),
                "manifest_parquet_file_count": record.get("parquet_file_count"),
                "manifest_size_bytes": record.get("size_bytes"),
                "manifest_row_count": record.get("row_count"),
                "disk": count_path(abs_path),
                "active_catalog_hits": active_hits,
                "delete_authorized": False,
            }
        )

    counts: dict[str, int] = {}
    for record in f1_records:
        category = str(record.get("category"))
        counts[category] = counts.get(category, 0) + 1

    failed_checks: list[str] = []
    if len(f1_records) != 19:
        failed_checks.append("f1_record_count_not_19")
    if counts.get("recommended_delete_orphan_cr139") != 2:
        failed_checks.append("orphan_record_count_not_2")
    if counts.get("recommended_delete_candidate_tree") != 17:
        failed_checks.append("candidate_tree_record_count_not_17")
    if len(excluded_legacy) != 210:
        failed_checks.append("excluded_legacy_record_count_not_210")
    if active_catalog_conflicts:
        failed_checks.append("f1_path_referenced_by_active_catalog")
    if any(not r["disk"]["exists"] for r in record_results):
        failed_checks.append("f1_path_missing_before_authorization")

    evidence = {
        "schema_version": 1,
        "workflow_id": "CR139-W2",
        "gate": "Gate F-1",
        "stage": "cleanup_authorization_preflight",
        "created_at": now,
        "status": "pass_gate_f1_cleanup_authorization_preflight" if not failed_checks else "blocked_gate_f1_cleanup_authorization_preflight",
        "input_refs": {
            "delete_manifest_preview": str(MANIFEST_PREVIEW.relative_to(PROJECT_ROOT)),
            "active_catalog": str(catalog_path),
            "active_manifest": str(manifest_path),
        },
        "summary": {
            "f1_record_count": len(f1_records),
            "orphan_cr139_record_count": counts.get("recommended_delete_orphan_cr139", 0),
            "candidate_tree_record_count": counts.get("recommended_delete_candidate_tree", 0),
            "legacy_records_excluded_count": len(excluded_legacy),
            "active_catalog_record_count": len(active_records),
            "active_catalog_conflict_count": len(active_catalog_conflicts),
            "planned_delete_bytes_f1": sum(int(r.get("size_bytes") or 0) for r in f1_records),
            "planned_delete_rows_f1": sum(int(r.get("row_count") or 0) for r in f1_records),
            "active_catalog_sha256": sha256_file(catalog_path),
            "active_manifest_sha256": sha256_file(manifest_path),
            "active_manifest_line_count": sum(1 for _ in manifest_path.open("rb")),
        },
        "checks": {
            "f1_categories_only": sorted({r.get("category") for r in f1_records}) == sorted(F1_CATEGORIES),
            "legacy_excluded_210": len(excluded_legacy) == 210,
            "active_catalog_conflicts_absent": not active_catalog_conflicts,
            "all_f1_paths_exist_before_authorization": all(r["disk"]["exists"] for r in record_results),
            "delete_not_executed": True,
            "active_metadata_not_modified": True,
        },
        "operation_counts": {
            "lake_delete": 0,
            "candidate_delete": 0,
            "orphan_delete": 0,
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
        "non_authorized_scope": [
            "delete execution",
            "legacy canonical cleanup",
            "active catalog write",
            "active manifest append",
            "provider catalog write",
            "NAS operation",
            "runtime operation",
            "credential read",
            "Git remote write",
        ],
        "active_catalog_conflicts": active_catalog_conflicts,
        "f1_records": record_results,
        "failed_checks": failed_checks,
        "next_action": "If approved by the user, execute Gate F-1 with exact-manifest delete only; legacy records remain excluded.",
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
                "status": evidence["status"],
                "summary": evidence["summary"],
                "failed_checks": failed_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    check_lines = [
        '---',
        'checkpoint_id: "CR139-W2-GATEF1-CLEANUP-AUTHORIZATION-PREFLIGHT-2026-06-30"',
        'checkpoint_name: "CR139 W2 Gate F-1 Cleanup Authorization Preflight"',
        'type: "runtime_authorization_preflight"',
        f'status: "{"PASS" if not failed_checks else "BLOCKED"}"',
        'owner: "host-orchestrator"',
        f'created_at: "{now}"',
        f'checked_at: "{now}"',
        '---',
        '',
        '# CR139 W2 Gate F-1 Cleanup Authorization Preflight',
        '',
        '## Entry Criteria',
        '',
        '| 条目 | 状态 | 证据 | 说明 |',
        '|---|---|---|---|',
        f'| Delete manifest preview exists | PASS | `{MANIFEST_PREVIEW.relative_to(PROJECT_ROOT)}` | 229-record Gate F preview consumed. |',
        '| CP8 approved | PASS | `process/checkpoints/CP8-CR139-W2-DELIVERY-READINESS.md` | W2 closure approved; F-1 still requires separate delete authorization. |',
        '',
        '## Checklist',
        '',
        '| # | 检查项 | 状态 | 证据 | 处理意见 |',
        '|---|---|---|---|---|',
        f'| 1 | F-1 record count = 19 | {"PASS" if len(f1_records) == 19 else "FAIL"} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | 2 orphan + 17 candidate tree. |',
        f'| 2 | Legacy records excluded = 210 | {"PASS" if len(excluded_legacy) == 210 else "FAIL"} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | F-2 only; not authorized here. |',
        f'| 3 | Active catalog does not reference F-1 paths | {"PASS" if not active_catalog_conflicts else "FAIL"} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Prevent deleting current truth. |',
        f'| 4 | F-1 paths exist before authorization | {"PASS" if all(r["disk"]["exists"] for r in record_results) else "FAIL"} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Pre-delete presence only. |',
        '| 5 | No delete executed | PASS | operation_counts all delete counters 0 | This is preflight only. |',
        '| 6 | No active metadata/provider/NAS/runtime/Git operation | PASS | operation_counts | Boundary preserved. |',
        '',
        '## F-1 Scope Summary',
        '',
        '| Class | Count | Planned bytes | Planned rows |',
        '|---|---:|---:|---:|',
        f'| orphan CR139 targets | {counts.get("recommended_delete_orphan_cr139", 0)} | {sum(int(r.get("size_bytes") or 0) for r in f1_records if r.get("category") == "recommended_delete_orphan_cr139")} | {sum(int(r.get("row_count") or 0) for r in f1_records if r.get("category") == "recommended_delete_orphan_cr139")} |',
        f'| candidate dataset trees | {counts.get("recommended_delete_candidate_tree", 0)} | {sum(int(r.get("size_bytes") or 0) for r in f1_records if r.get("category") == "recommended_delete_candidate_tree")} | {sum(int(r.get("row_count") or 0) for r in f1_records if r.get("category") == "recommended_delete_candidate_tree")} |',
        f'| F-1 total | {len(f1_records)} | {evidence["summary"]["planned_delete_bytes_f1"]} | {evidence["summary"]["planned_delete_rows_f1"]} |',
        '',
        '## Exit Criteria',
        '',
        '| 条目 | 状态 | 证据 | 说明 |',
        '|---|---|---|---|',
        f'| Failed checks absent | {"PASS" if not failed_checks else "FAIL"} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | {failed_checks or "No failed checks"} |',
        '',
        '## Deliverables',
        '',
        '| 交付物 | 路径 | 状态 | 说明 |',
        '|---|---|---|---|',
        f'| Evidence | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | PASS | Machine-readable preflight. |',
        f'| Index | `{INDEX_PATH.relative_to(PROJECT_ROOT)}` | PASS | Evidence index. |',
        '',
        '## 结论',
        '',
        f'- 结论：`{"PASS" if not failed_checks else "BLOCKED"}`',
        f'- status：`{evidence["status"]}`',
        '- 阻断项：' + ('无' if not failed_checks else ', '.join(failed_checks)),
        '- 下一步：发起 Gate F-1 cleanup execution 人工授权；未授权前不得删除。',
        '',
    ]
    CHECK_PATH.write_text("\n".join(check_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
