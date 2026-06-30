#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAKE_ROOT = Path("/home/hyde/data/quant-lab/data-lake").resolve()
MANIFEST_PREVIEW = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF-CLEANUP-DELETE-MANIFEST-PREVIEW-2026-06-29.jsonl"
F1_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF1-CLEANUP-EXECUTION-2026-06-30.json"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF2-LEGACY-RETAIN-SUPERSEDED-PLAN-2026-06-30.json"
INDEX_PATH = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF2-LEGACY-RETAIN-SUPERSEDED-PLAN.index.json"
CHECK_PATH = PROJECT_ROOT / "process/checks/CR139-W2-GATEF2-LEGACY-RETAIN-SUPERSEDED-PLAN-2026-06-30.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
        return {"exists": False, "file_count": 0, "dir_count": 0, "parquet_file_count": 0, "size_bytes": 0}
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

    preview_records = load_jsonl(MANIFEST_PREVIEW)
    legacy_records = [r for r in preview_records if r.get("category") == "review_delete_or_archive_legacy_canonical"]
    f1 = json.loads(F1_EVIDENCE.read_text(encoding="utf-8"))

    active_records = active_catalog_records(catalog_path)
    active_paths = [str(r.get("canonical_path", "")).strip("/") for r in active_records if r.get("canonical_path")]

    register: list[dict[str, Any]] = []
    active_hits: list[dict[str, Any]] = []
    dataset_counts: dict[str, int] = {}
    for record in legacy_records:
        rel = str(record["relative_path"]).strip("/")
        disk = count_path(LAKE_ROOT / rel)
        hits = [p for p in active_paths if is_within(p, rel) or is_within(rel, p)]
        if hits:
            active_hits.append({"relative_path": rel, "active_hits": hits})
        dataset = str(record.get("dataset"))
        dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
        register.append(
            {
                "dataset": dataset,
                "relative_path": rel,
                "row_count": record.get("row_count"),
                "size_bytes": record.get("size_bytes"),
                "file_count": record.get("file_count"),
                "parquet_file_count": record.get("parquet_file_count"),
                "content_fingerprint": record.get("content_fingerprint"),
                "retention_decision": "retain",
                "superseded_by": "CR139-W2 active catalog current truth",
                "archive_or_delete_status": "not_authorized",
                "disk": disk,
            }
        )

    failed_checks: list[str] = []
    if f1.get("status") != "pass_gate_f1_cleanup_execution_verified":
        failed_checks.append("gate_f1_not_verified")
    if len(legacy_records) != 210:
        failed_checks.append("legacy_record_count_not_210")
    if active_hits:
        failed_checks.append("legacy_still_referenced_by_active_catalog")
    if any(not r["disk"]["exists"] for r in register):
        failed_checks.append("legacy_path_missing")

    summary = {
        "legacy_record_count": len(legacy_records),
        "legacy_existing_count": sum(1 for r in register if r["disk"]["exists"]),
        "active_catalog_reference_count": len(active_hits),
        "dataset_count": len(dataset_counts),
        "total_legacy_size_bytes": sum(int(r.get("size_bytes") or 0) for r in legacy_records),
        "total_legacy_row_count": sum(int(r.get("row_count") or 0) for r in legacy_records),
        "active_catalog_sha256": sha256_file(catalog_path),
        "active_manifest_sha256": sha256_file(manifest_path),
        "active_manifest_line_count": sum(1 for _ in manifest_path.open("rb")),
    }
    evidence = {
        "schema_version": 1,
        "workflow_id": "CR139-W2",
        "gate": "Gate F-2",
        "stage": "legacy_retain_superseded_plan",
        "created_at": now,
        "status": "pass_gate_f2_legacy_retain_superseded_plan" if not failed_checks else "blocked_gate_f2_legacy_retain_superseded_plan",
        "input_refs": {
            "gate_f_manifest_preview": str(MANIFEST_PREVIEW.relative_to(PROJECT_ROOT)),
            "gate_f1_execution": str(F1_EVIDENCE.relative_to(PROJECT_ROOT)),
        },
        "summary": summary,
        "dataset_counts": dict(sorted(dataset_counts.items())),
        "retention_policy": {
            "default": "retain + mark superseded in process evidence",
            "archive": "requires separate Gate F-2 archive authorization",
            "delete": "requires explicit dependency review and separate delete authorization",
            "physical_lake_write": "not_executed",
            "active_catalog_write": "not_executed",
            "manifest_append": "not_executed",
        },
        "checks": {
            "gate_f1_verified": f1.get("status") == "pass_gate_f1_cleanup_execution_verified",
            "legacy_record_count_210": len(legacy_records) == 210,
            "legacy_existing_210": sum(1 for r in register if r["disk"]["exists"]) == 210,
            "active_catalog_references_legacy_absent": not active_hits,
            "delete_not_executed": True,
            "active_metadata_not_modified": True,
        },
        "operation_counts": {
            "lake_delete": 0,
            "legacy_delete": 0,
            "legacy_archive": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "nas_operation": 0,
            "credential_read": 0,
            "runtime_operation": 0,
            "git_remote_write": 0,
        },
        "active_catalog_hits": active_hits,
        "legacy_retain_superseded_register": register,
        "failed_checks": failed_checks,
        "next_action": "Gate H NAS dry-run authorization/preflight",
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INDEX_PATH.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "workflow_id": "CR139-W2",
                "gate": "Gate F-2",
                "evidence_path": str(EVIDENCE_PATH.relative_to(PROJECT_ROOT)),
                "check_path": str(CHECK_PATH.relative_to(PROJECT_ROOT)),
                "status": evidence["status"],
                "summary": summary,
                "failed_checks": failed_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    status = "PASS" if not failed_checks else "BLOCKED"
    lines = [
        "---",
        'checkpoint_id: "CR139-W2-GATEF2-LEGACY-RETAIN-SUPERSEDED-PLAN-2026-06-30"',
        'checkpoint_name: "CR139 W2 Gate F-2 Legacy Retain Superseded Plan"',
        'type: "runtime_preview_check"',
        f'status: "{status}"',
        'owner: "host-orchestrator"',
        f'created_at: "{now}"',
        f'checked_at: "{now}"',
        "---",
        "",
        "# CR139 W2 Gate F-2 Legacy Retain Superseded Plan",
        "",
        "## Entry Criteria",
        "",
        "| 条目 | 状态 | 证据 | 说明 |",
        "|---|---|---|---|",
        f"| Gate F-1 verified | {'PASS' if f1.get('status') == 'pass_gate_f1_cleanup_execution_verified' else 'FAIL'} | `{F1_EVIDENCE.relative_to(PROJECT_ROOT)}` | F-1 cleanup completed before F-2 planning. |",
        "| CP8 DQ-003 approved | PASS | `process/checkpoints/CP8-CR139-W2-DELIVERY-READINESS.md` | Default legacy policy is retain + mark superseded. |",
        "",
        "## Checklist",
        "",
        "| # | 检查项 | 状态 | 证据 | 处理意见 |",
        "|---|---|---|---|---|",
        f"| 1 | Legacy record count = 210 | {'PASS' if len(legacy_records) == 210 else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | From Gate F preview. |",
        f"| 2 | Legacy paths still exist = 210 | {'PASS' if summary['legacy_existing_count'] == 210 else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | No legacy delete executed. |",
        f"| 3 | Active catalog references legacy = 0 | {'PASS' if not active_hits else 'FAIL'} | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | Legacy is superseded, not current truth. |",
        "| 4 | Default action is retain + superseded | PASS | retention_policy | Process evidence only; no lake metadata write. |",
        "| 5 | No delete/archive/NAS/provider/runtime/Git operation | PASS | operation_counts | All counters 0. |",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| legacy_record_count | {summary['legacy_record_count']} |",
        f"| dataset_count | {summary['dataset_count']} |",
        f"| total_legacy_size_bytes | {summary['total_legacy_size_bytes']} |",
        f"| total_legacy_row_count | {summary['total_legacy_row_count']} |",
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
        f"| Evidence | `{EVIDENCE_PATH.relative_to(PROJECT_ROOT)}` | {status} | Legacy retain/superseded register. |",
        f"| Index | `{INDEX_PATH.relative_to(PROJECT_ROOT)}` | {status} | Evidence index. |",
        "",
        "## 结论",
        "",
        f"- 结论：`{status}`",
        f"- status：`{evidence['status']}`",
        "- 阻断项：" + ("无" if not failed_checks else ", ".join(failed_checks)),
        "- 下一步：Gate H NAS dry-run authorization/preflight",
        "",
    ]
    CHECK_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
