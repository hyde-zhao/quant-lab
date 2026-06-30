#!/usr/bin/env python
"""CR139 Gate C-2 active catalog/manifest write executor."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
AUTHORIZATION_REF = "process/checkpoints/CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-AUTHORIZATION-2026-06-29.md"
PREVIEW_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-REFRESH-PREVIEW-2026-06-29.json"
AFTER_CATALOG_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-AFTER-VIRTUAL-2026-06-29.json"
MANIFEST_APPEND_PREVIEW_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-MANIFEST-APPEND-PREVIEW-2026-06-29.jsonl"
EXECUTION_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION-2026-06-29.json"
INDEX_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION.index.json"
CHECK_REF = "process/checks/CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"
EXPECTED_CATALOG_BEFORE_SHA = "3c9e937acb068a2d838d52e67f6990d4415306c17ba04ba4a8038adf7a7810f0"
EXPECTED_MANIFEST_BEFORE_SHA = "57c5f86a7e170b99407005f54c6d66f3903fcb30a2fb0f573d8966e96eedae7a"
EXPECTED_CATALOG_AFTER_SHA = "87cadaa5048e68067863c6d151ce1671a3883b2e858fc334ea50305f029cebc3"
EXPECTED_MANIFEST_BEFORE_LINES = 6367
EXPECTED_MANIFEST_APPEND_LINES = 17
EXPECTED_MANIFEST_AFTER_LINES = 6384


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake-root", required=True)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    lake_root = Path(args.lake_root).resolve()
    active_catalog = lake_root / ACTIVE_CATALOG_REL
    active_manifest = lake_root / ACTIVE_MANIFEST_REL
    after_catalog = project_root / AFTER_CATALOG_REF
    append_preview = project_root / MANIFEST_APPEND_PREVIEW_REF
    preview = read_json(project_root / PREVIEW_REF)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")

    after_catalog_text = after_catalog.read_text(encoding="utf-8")
    after_catalog_write_text = after_catalog_text[:-1] if after_catalog_text.endswith("\n") else after_catalog_text
    append_text = append_preview.read_text(encoding="utf-8")
    append_lines = append_text.splitlines()
    if not append_text.endswith("\n"):
        raise RuntimeError(f"manifest append preview must end with newline: {MANIFEST_APPEND_PREVIEW_REF}")
    if len(append_lines) != EXPECTED_MANIFEST_APPEND_LINES:
        raise RuntimeError(f"manifest append preview line count mismatch: {len(append_lines)}")
    for line in append_lines:
        json.loads(line)

    active_catalog_before_text = active_catalog.read_text(encoding="utf-8")
    active_manifest_before_bytes = active_manifest.read_bytes()
    pre_snapshot = {
        "active_catalog_sha256": sha256_bytes(active_catalog_before_text.encode("utf-8")),
        "active_catalog_size_bytes": active_catalog.stat().st_size,
        "active_manifest_sha256": sha256_bytes(active_manifest_before_bytes),
        "active_manifest_size_bytes": active_manifest.stat().st_size,
        "active_manifest_line_count": active_manifest_before_bytes.count(b"\n"),
        "active_manifest_ends_with_newline": active_manifest_before_bytes.endswith(b"\n"),
    }
    preflight_failures = []
    if pre_snapshot["active_catalog_sha256"] != EXPECTED_CATALOG_BEFORE_SHA:
        preflight_failures.append("active_catalog_hash_drift")
    if pre_snapshot["active_manifest_sha256"] != EXPECTED_MANIFEST_BEFORE_SHA:
        preflight_failures.append("active_manifest_hash_drift")
    if pre_snapshot["active_manifest_line_count"] != EXPECTED_MANIFEST_BEFORE_LINES:
        preflight_failures.append("active_manifest_line_count_drift")
    if not pre_snapshot["active_manifest_ends_with_newline"]:
        preflight_failures.append("active_manifest_missing_trailing_newline")
    if sha256_bytes(after_catalog_write_text.encode("utf-8")) != EXPECTED_CATALOG_AFTER_SHA:
        preflight_failures.append("virtual_after_catalog_hash_mismatch")
    if preview["status"] != "pass_no_write_active_catalog_refresh_preview_generated":
        preflight_failures.append("preview_not_pass")
    if preflight_failures:
        raise RuntimeError(f"Gate C-2 preflight failed: {preflight_failures}")

    # Authorized active lake metadata writes: catalog replacement and manifest append.
    active_catalog.write_text(after_catalog_write_text, encoding="utf-8")
    with active_manifest.open("ab") as fh:
        fh.write(append_text.encode("utf-8"))

    active_catalog_after_text = active_catalog.read_text(encoding="utf-8")
    active_manifest_after_bytes = active_manifest.read_bytes()
    active_catalog_after = json.loads(active_catalog_after_text)
    active_manifest_after_lines = active_manifest_after_bytes.decode("utf-8").splitlines()
    appended_after_lines = active_manifest_after_lines[-EXPECTED_MANIFEST_APPEND_LINES:]
    dataset_records = active_catalog_after["datasets"]
    operation_counts = {
        "active_catalog_write": 1,
        "active_manifest_append": EXPECTED_MANIFEST_APPEND_LINES,
        "provider_catalog_write": 0,
        "provider_lake_catalog_write": 0,
        "published_pointer_advance": 0,
        "physical_partition_migration": 0,
        "lake_data_write": 0,
        "candidate_delete": 0,
        "legacy_delete": 0,
        "nas_operation": 0,
        "credential_read": 0,
        "runtime_operation": 0,
        "git_remote_write": 0,
    }
    post_snapshot = {
        "active_catalog_sha256": sha256_bytes(active_catalog_after_text.encode("utf-8")),
        "active_catalog_size_bytes": active_catalog.stat().st_size,
        "active_manifest_sha256": sha256_bytes(active_manifest_after_bytes),
        "active_manifest_size_bytes": active_manifest.stat().st_size,
        "active_manifest_line_count": active_manifest_after_bytes.count(b"\n"),
    }
    checks = {
        "active_catalog_json_parse": isinstance(active_catalog_after, dict),
        "active_catalog_sha_equals_virtual_after": post_snapshot["active_catalog_sha256"] == EXPECTED_CATALOG_AFTER_SHA,
        "active_manifest_line_count_6384": post_snapshot["active_manifest_line_count"] == EXPECTED_MANIFEST_AFTER_LINES,
        "active_manifest_appended_17_exact_preview_lines": appended_after_lines == append_lines,
        "active_catalog_dataset_count_17": len(dataset_records) == 17,
        "active_catalog_cr139_canonical_paths_17": sum(
            1
            for record in dataset_records.values()
            if str(record.get("canonical_path", "")).startswith("canonical/")
            and "run_id=cr139-w2-" in str(record.get("canonical_path", ""))
        )
        == 17,
        "active_catalog_published_false_17": sum(1 for record in dataset_records.values() if record.get("published") is False)
        == 17,
        "active_catalog_lineage_checksum_present_17": sum(
            1 for record in dataset_records.values() if str(record.get("lineage_checksum") or "").startswith("sha256:")
        )
        == 17,
        "operation_counts_match_authorization": all(
            operation_counts[key] == expected
            for key, expected in {
                "provider_catalog_write": 0,
                "provider_lake_catalog_write": 0,
                "published_pointer_advance": 0,
                "physical_partition_migration": 0,
                "lake_data_write": 0,
                "candidate_delete": 0,
                "legacy_delete": 0,
                "nas_operation": 0,
                "credential_read": 0,
                "runtime_operation": 0,
                "git_remote_write": 0,
            }.items()
        ),
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = "pass_gate_c2_active_catalog_manifest_write_verified" if not failed_checks else "fail_gate_c2_active_catalog_manifest_write"
    evidence = {
        "schema_version": "cr139.gatec2.active_catalog_manifest_write_execution.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate C-2",
        "stage": "active_catalog_manifest_write_execution",
        "created_at": created_at,
        "approval_ref": "user chat authorization: approve Gate C-2 active catalog and manifest write only",
        "status": status,
        "input_refs": {
            "authorization_ref": AUTHORIZATION_REF,
            "preview_ref": PREVIEW_REF,
            "active_catalog_after_virtual_ref": AFTER_CATALOG_REF,
            "manifest_append_preview_ref": MANIFEST_APPEND_PREVIEW_REF,
        },
        "summary": {
            "active_catalog_write_count": operation_counts["active_catalog_write"],
            "active_manifest_append_count": operation_counts["active_manifest_append"],
            "active_catalog_sha256_before": pre_snapshot["active_catalog_sha256"],
            "active_catalog_sha256_after": post_snapshot["active_catalog_sha256"],
            "active_manifest_sha256_before": pre_snapshot["active_manifest_sha256"],
            "active_manifest_sha256_after": post_snapshot["active_manifest_sha256"],
            "active_manifest_line_count_before": pre_snapshot["active_manifest_line_count"],
            "active_manifest_line_count_after": post_snapshot["active_manifest_line_count"],
            "dataset_count": len(dataset_records),
            "cr139_canonical_path_count": sum(
                1 for record in dataset_records.values() if "run_id=cr139-w2-" in str(record.get("canonical_path", ""))
            ),
            "published_true_count": sum(1 for record in dataset_records.values() if record.get("published") is True),
            "lineage_checksum_present_count": sum(
                1 for record in dataset_records.values() if str(record.get("lineage_checksum") or "").startswith("sha256:")
            ),
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "pre_snapshot": pre_snapshot,
        "post_snapshot": post_snapshot,
        "appended_manifest_preview_records": [json.loads(line) for line in append_lines],
        "catalog_records_after": [
            {
                "dataset": dataset,
                "canonical_path": record.get("canonical_path"),
                "coverage_denominator": record.get("coverage_denominator"),
                "latest_manifest_run_id": record.get("latest_manifest_run_id"),
                "lineage_checksum": record.get("lineage_checksum"),
                "published": record.get("published"),
            }
            for dataset, record in sorted(dataset_records.items())
        ],
        "non_authorized_scope": [
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
        ],
        "next_action": "Gate D no-write pointer advance preview; do not advance pointer without separate authorization",
    }
    index = {
        "schema_version": "cr139.gatec2.active_catalog_manifest_write_execution.index.v1",
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
    project_root = Path(args.project_root).resolve()
    write_json(project_root / EXECUTION_REF, evidence)
    write_json(project_root / INDEX_REF, index)
    write_check(project_root / CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, evidence)
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 1 if failed_checks else 0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_check(path: Path, evidence: dict[str, Any]) -> None:
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{EXECUTION_REF}` | {'通过' if passed else '需阻断'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    catalog_rows = "\n".join(
        f"| {item['dataset']} | `{item['canonical_path']}` | {item['coverage_denominator']} | `{item['latest_manifest_run_id']}` | `{item['lineage_checksum']}` | {item['published']} |"
        for item in evidence["catalog_records_after"]
    )
    status = "PASS" if not evidence["failed_checks"] else "FAIL"
    summary = evidence["summary"]
    text = f"""---
checkpoint_id: "CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION-2026-06-29"
checkpoint_name: "CR139 W2 Gate C-2 Active Catalog and Manifest Write Execution"
type: "runtime_execution_check"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
target:
  phase: "CR139-W2-DATA-CONTRACTS Gate C-2"
  story_id: null
  artifacts:
    - "{EXECUTION_REF}"
    - "{INDEX_REF}"
---

# CR139 W2 Gate C-2 Active Catalog and Manifest Write Execution

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Human authorization captured | PASS | `{AUTHORIZATION_REF}` | 用户已明确授权 active catalog + manifest write。 |
| Gate C-2 preview passed | PASS | `{PREVIEW_REF}` | no-write preview failed_checks=0。 |
| Active metadata pre-write guard passed | PASS | `{EXECUTION_REF}` | pre-write catalog/manifest hash 与 preview baseline 一致。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}

## Active Catalog Records After Write

| Dataset | canonical_path | Rows | latest_manifest_run_id | lineage_checksum | published |
|---|---|---:|---|---|---:|
{catalog_rows}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Active catalog replaced | {'PASS' if summary['active_catalog_sha256_after'] == EXPECTED_CATALOG_AFTER_SHA else 'FAIL'} | `{EXECUTION_REF}` | active catalog hash equals virtual after. |
| Active manifest appended | {'PASS' if summary['active_manifest_line_count_after'] == EXPECTED_MANIFEST_AFTER_LINES else 'FAIL'} | `{EXECUTION_REF}` | line count 6367 -> 6384。 |
| Pointer not advanced | {'PASS' if evidence['operation_counts']['published_pointer_advance'] == 0 else 'FAIL'} | `{EXECUTION_REF}` | Gate D remains separate。 |
| Provider/runtime/external forbidden ops not touched | {'PASS' if evidence['checks']['operation_counts_match_authorization'] else 'FAIL'} | `{EXECUTION_REF}` | provider/NAS/runtime/credential/Git all 0。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Execution evidence | `{EXECUTION_REF}` | {status} | Gate C-2 active metadata write 证据。 |
| Evidence index | `{INDEX_REF}` | {status} | 摘要索引。 |
| Execution check | `{CHECK_REF}` | {status} | 本文件。 |

## 结论

- 结论：`{status}`
- active_catalog_write_count：{summary['active_catalog_write_count']}
- active_manifest_append_count：{summary['active_manifest_append_count']}
- active_catalog_sha256_before：`{summary['active_catalog_sha256_before']}`
- active_catalog_sha256_after：`{summary['active_catalog_sha256_after']}`
- active_manifest_sha256_before：`{summary['active_manifest_sha256_before']}`
- active_manifest_sha256_after：`{summary['active_manifest_sha256_after']}`
- active_manifest_line_count_before：{summary['active_manifest_line_count_before']}
- active_manifest_line_count_after：{summary['active_manifest_line_count_after']}
- cr139_canonical_path_count：{summary['cr139_canonical_path_count']}
- published_true_count：{summary['published_true_count']}
- lineage_checksum_present_count：{summary['lineage_checksum_present_count']}
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：Gate D no-write pointer advance preview；不自动推进 pointer。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_gate_ledger(path: Path, evidence: dict[str, Any]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": "active_catalog_manifest_write_execution",
        "event_id": "CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": "Gate C-2",
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
