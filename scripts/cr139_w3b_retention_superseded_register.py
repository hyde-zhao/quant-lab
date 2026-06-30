#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
F2_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W2-GATEF2-LEGACY-RETAIN-SUPERSEDED-PLAN-2026-06-30.json"
REGISTER_PATH = PROJECT_ROOT / "process/registers/CR139-W3-LEGACY-SUPERSEDED-REGISTER-2026-06-30.json"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence/CR139-W3B-RETENTION-SUPERSEDED-REGISTER-2026-06-30.json"
CHECK_PATH = PROJECT_ROOT / "process/checks/CR139-W3B-RETENTION-SUPERSEDED-REGISTER-2026-06-30.md"


def main() -> int:
    source = json.loads(F2_EVIDENCE.read_text(encoding="utf-8"))
    records = list(source.get("legacy_retain_superseded_register", []))
    now = datetime.now(timezone.utc).isoformat()
    failed_checks: list[str] = []
    if source.get("status") != "pass_gate_f2_legacy_retain_superseded_plan":
        failed_checks.append("gate_f2_source_not_pass")
    if len(records) != 210:
        failed_checks.append("legacy_record_count_not_210")
    if any(item.get("retention_decision") != "retain" for item in records):
        failed_checks.append("non_retain_decision_present")
    if any(item.get("archive_or_delete_status") != "not_authorized" for item in records):
        failed_checks.append("archive_or_delete_authorized_unexpectedly")
    if any(not item.get("disk", {}).get("exists") for item in records):
        failed_checks.append("legacy_path_missing")

    dataset_counts: dict[str, int] = {}
    for item in records:
        dataset = str(item.get("dataset"))
        dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1

    register = {
        "schema": "cr139.w3.legacy_superseded_register.v1",
        "created_at": now,
        "source_evidence": str(F2_EVIDENCE.relative_to(PROJECT_ROOT)),
        "policy": {
            "default_action": "retain",
            "status": "superseded_not_current_truth",
            "archive_requires": [
                "dependency_proof_zero_or_waived",
                "archive_target_defined",
                "rollback_or_restore_plan_defined",
                "separate_runtime_authorization",
            ],
            "delete_requires": [
                "dependency_proof_zero",
                "archive_or_backup_completed_or_explicitly_waived",
                "exact_manifest_paths_only",
                "separate_delete_authorization",
            ],
        },
        "summary": {
            "legacy_record_count": len(records),
            "dataset_count": len(dataset_counts),
            "total_size_bytes": sum(int(item.get("size_bytes") or 0) for item in records),
            "total_row_count": sum(int(item.get("row_count") or 0) for item in records),
        },
        "dataset_counts": dict(sorted(dataset_counts.items())),
        "records": records,
    }
    REGISTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTER_PATH.write_text(json.dumps(register, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    register_hash = sha256_file(REGISTER_PATH)
    evidence = {
        "schema": "cr139.w3b.retention_superseded_register_check.v1",
        "created_at": now,
        "result": "pass_w3b_retention_superseded_register" if not failed_checks else "fail_w3b_retention_superseded_register",
        "input_refs": {"gate_f2_evidence": str(F2_EVIDENCE.relative_to(PROJECT_ROOT))},
        "deliverables": {
            "register_path": str(REGISTER_PATH.relative_to(PROJECT_ROOT)),
            "register_sha256": register_hash,
        },
        "checks": {
            "gate_f2_source_pass": source.get("status") == "pass_gate_f2_legacy_retain_superseded_plan",
            "legacy_record_count_210": len(records) == 210,
            "all_records_retain": all(item.get("retention_decision") == "retain" for item in records),
            "archive_delete_not_authorized": all(
                item.get("archive_or_delete_status") == "not_authorized" for item in records
            ),
            "legacy_paths_exist": all(item.get("disk", {}).get("exists") for item in records),
        },
        "summary": register["summary"],
        "failed_checks": failed_checks,
        "operation_counts": {
            "lake_delete": 0,
            "lake_archive": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "nas_operation": 0,
            "credential_read": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_check(evidence)
    print(evidence["result"])
    print(f"register={REGISTER_PATH}")
    print(f"evidence={EVIDENCE_PATH}")
    print(f"check={CHECK_PATH}")
    return 0 if not failed_checks else 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_check(evidence: dict[str, Any]) -> None:
    summary = evidence["summary"]
    text = f"""# CR139 W3-B Retention Superseded Register

## Result

- result: `{evidence['result']}`
- register: `{evidence['deliverables']['register_path']}`
- register_sha256: `{evidence['deliverables']['register_sha256']}`

## Summary

| metric | value |
|---|---:|
| legacy_record_count | {summary['legacy_record_count']} |
| dataset_count | {summary['dataset_count']} |
| total_size_bytes | {summary['total_size_bytes']} |
| total_row_count | {summary['total_row_count']} |

## Checks

| check | result |
|---|---:|
| gate_f2_source_pass | {evidence['checks']['gate_f2_source_pass']} |
| legacy_record_count_210 | {evidence['checks']['legacy_record_count_210']} |
| all_records_retain | {evidence['checks']['all_records_retain']} |
| archive_delete_not_authorized | {evidence['checks']['archive_delete_not_authorized']} |
| legacy_paths_exist | {evidence['checks']['legacy_paths_exist']} |

## Operation Counts

```json
{json.dumps(evidence['operation_counts'], indent=2, sort_keys=True)}
```
"""
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
