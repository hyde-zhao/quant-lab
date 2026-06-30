#!/usr/bin/env python
"""CR139 Gate D published pointer advance no-write preview."""

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

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from market_data.catalog import validate_catalog_pointer
from market_data.contracts import CR014_UNIVERSE_SCOPE_ALL_A_SHARE, PIT_STATUS_AVAILABLE


ACTIVE_CATALOG_REL = "catalog/catalog.json"
ACTIVE_MANIFEST_REL = "manifest/market_data_manifest.jsonl"
GATEC2_EXECUTION_REF = "process/evidence/CR139-W2-GATEC2-ACTIVE-CATALOG-MANIFEST-WRITE-EXECUTION-2026-06-29.json"
GATEC2D_CORRECTION_REF = "process/evidence/CR139-W2-GATEC2D-PIT-CATALOG-CORRECTION-WRITE-EXECUTION-2026-06-29.json"
PREVIEW_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29.json"
INDEX_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-PREVIEW.index.json"
AFTER_REF = "process/evidence/CR139-W2-GATED-ACTIVE-CATALOG-AFTER-POINTER-VIRTUAL-2026-06-29.json"
DIFF_REF = "process/evidence/CR139-W2-GATED-POINTER-ADVANCE-VIRTUAL-DIFF-2026-06-29.diff"
CHECK_REF = "process/checks/CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29.md"
GATE_LEDGER_REF = "process/state/GATE-LEDGER.ndjson"
PUBLISH_RUN_ID = "cr139-w2-gated-publish-20260629"


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
    active_catalog_before_text = active_catalog_path.read_text(encoding="utf-8")
    active_catalog_before_sha = sha256_bytes(active_catalog_before_text.encode("utf-8"))
    active_manifest_before_sha = sha256_file(active_manifest_path)
    active_manifest_before_lines = count_lines(active_manifest_path)
    baseline_ref = GATEC2_EXECUTION_REF
    gatec2_execution = read_json(project_root / GATEC2_EXECUTION_REF)
    baseline = gatec2_execution
    correction_path = project_root / GATEC2D_CORRECTION_REF
    if correction_path.exists():
        correction = read_json(correction_path)
        if correction.get("status") == "pass_gate_c2d_pit_catalog_correction_write_verified":
            baseline_ref = GATEC2D_CORRECTION_REF
            baseline = correction

    after_catalog = copy.deepcopy(active_before)
    after_records: dict[str, Any] = after_catalog["datasets"]
    pointer_records: list[dict[str, Any]] = []
    pointer_validations: list[dict[str, Any]] = []
    canonical_object_validations: list[dict[str, Any]] = []
    pit_semantics: list[dict[str, Any]] = []
    blocking_risks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    defaulted_universe_scope = 0
    defaulted_as_of_trade_date = 0
    defaulted_known_limitations = 0

    for dataset, before in sorted(after_records.items()):
        after = copy.deepcopy(before)
        if not after.get("universe_scope"):
            after["universe_scope"] = CR014_UNIVERSE_SCOPE_ALL_A_SHARE
            defaulted_universe_scope += 1
        if not after.get("as_of_trade_date"):
            after["as_of_trade_date"] = after.get("coverage_end") or after.get("end_date")
            defaulted_as_of_trade_date += 1
        if not isinstance(after.get("known_limitations"), list):
            after["known_limitations"] = []
            defaulted_known_limitations += 1
        after["published"] = True
        after["published_at"] = created_at
        after["publish_run_id"] = PUBLISH_RUN_ID
        after["catalog_pointer_path"] = f"{ACTIVE_CATALOG_REL}#datasets/{dataset}"
        after.setdefault("audit_refs", [])
        if PREVIEW_REF not in after["audit_refs"]:
            after["audit_refs"].append(PREVIEW_REF)
        after["updated_at"] = created_at
        after_records[dataset] = after

        validation = validate_catalog_pointer(after)
        pointer_validations.append(
            {
                "dataset": dataset,
                "passed": validation.passed,
                "missing_fields": list(validation.missing_fields),
                "error_codes": list(validation.error_codes),
                "details": [dict(item) for item in validation.details],
            }
        )
        canonical_object_validations.append(validate_canonical_object(lake_root, dataset, after))
        pit_result = inspect_pit_semantics(lake_root, dataset, after)
        pit_semantics.append(pit_result)
        if pit_result["blocks_pointer_advance"]:
            blocking_risks.append(
                {
                    "risk_id": f"D-GATED-PIT-SEMANTICS-{dataset}",
                    "severity": "HIGH",
                    "dataset": dataset,
                    "reason": (
                        "catalog dataset-level pit_status is pit_available, "
                        "but row-level PIT status contains non-pit_available values"
                    ),
                    "pit_status_distribution": pit_result["pit_status_distribution"],
                    "required_decision": (
                        "Before pointer advance, either accept publishing the mixed PIT rows with an explicit "
                        "known limitation, change the dataset-level PIT status to a non-fully-PIT claim, "
                        "or repair/isolate the non-pit_available rows."
                    ),
                }
            )
        pointer_records.append(
            {
                "dataset": dataset,
                "before_published": before.get("published"),
                "after_published": after.get("published"),
                "canonical_path": after.get("canonical_path"),
                "coverage_denominator": after.get("coverage_denominator"),
                "coverage_start": after.get("coverage_start"),
                "coverage_end": after.get("coverage_end"),
                "lineage_checksum": after.get("lineage_checksum"),
                "published_at": after.get("published_at"),
                "universe_scope": after.get("universe_scope"),
                "as_of_trade_date": after.get("as_of_trade_date"),
                "catalog_pointer_path": after.get("catalog_pointer_path"),
                "pit_status": after.get("pit_status"),
            }
        )

    if defaulted_universe_scope:
        warnings.append(
            {
                "warning_id": "D-GATED-DEFAULTED-UNIVERSE-SCOPE",
                "severity": "LOW",
                "count": defaulted_universe_scope,
                "default_value": CR014_UNIVERSE_SCOPE_ALL_A_SHARE,
                "reason": "Gate C-2 catalog lacked universe_scope; Gate D virtual pointer fills the CR014 default.",
            }
        )
    if defaulted_as_of_trade_date:
        warnings.append(
            {
                "warning_id": "D-GATED-DEFAULTED-AS-OF-TRADE-DATE",
                "severity": "LOW",
                "count": defaulted_as_of_trade_date,
                "reason": "Gate C-2 catalog lacked as_of_trade_date; Gate D virtual pointer uses coverage_end/end_date.",
            }
        )
    if defaulted_known_limitations:
        warnings.append(
            {
                "warning_id": "D-GATED-DEFAULTED-KNOWN-LIMITATIONS",
                "severity": "LOW",
                "count": defaulted_known_limitations,
                "reason": "Gate D virtual pointer normalizes known_limitations to an empty list.",
            }
        )

    after_rendered = render_json(after_catalog)
    before_rendered = render_json(active_before)
    diff_text = "\n".join(
        difflib.unified_diff(
            before_rendered.splitlines(),
            after_rendered.splitlines(),
            fromfile=ACTIVE_CATALOG_REL + " (current)",
            tofile=ACTIVE_CATALOG_REL + " (virtual after Gate D pointer advance)",
            lineterm="",
        )
    ) + "\n"

    current_catalog_after_sha = sha256_file(active_catalog_path)
    current_manifest_after_sha = sha256_file(active_manifest_path)
    after_virtual_sha = sha256_bytes(after_rendered.encode("utf-8"))
    checks = {
        "gate_c2_active_catalog_manifest_write_verified": gatec2_execution["status"]
        == "pass_gate_c2_active_catalog_manifest_write_verified",
        "active_catalog_hash_matches_latest_active_metadata_after": active_catalog_before_sha
        == baseline["summary"]["active_catalog_sha256_after"],
        "active_manifest_hash_matches_latest_active_metadata_after": active_manifest_before_sha
        == baseline["summary"]["active_manifest_sha256_after"],
        "dataset_count_17": len(pointer_records) == 17,
        "canonical_objects_exist_17": sum(1 for item in canonical_object_validations if item["exists"]) == 17,
        "canonical_row_counts_match_17": sum(1 for item in canonical_object_validations if item["row_count_matches_catalog"]) == 17,
        "pointer_required_fields_valid_17": sum(1 for item in pointer_validations if item["passed"]) == 17,
        "virtual_after_published_true_17": sum(1 for item in pointer_records if item["after_published"] is True) == 17,
        "active_catalog_file_unchanged": active_catalog_before_sha == current_catalog_after_sha,
        "active_manifest_file_unchanged": active_manifest_before_sha == current_manifest_after_sha,
        "no_write_operation_counts": True,
        "no_blocking_publish_semantics_risk": not blocking_risks,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    status = (
        "pass_ready_for_gate_d_pointer_advance_authorization"
        if not failed_checks
        else "blocked_pointer_advance_preview_requires_decision"
    )
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
    evidence = {
        "schema_version": "cr139.gated.pointer_advance_preview.v1",
        "workflow_id": "CR139-W2-DATA-CONTRACTS",
        "gate": "Gate D",
        "stage": "published_pointer_advance_preview",
        "created_at": created_at,
        "status": status,
        "input_refs": {
            "gate_c2_execution_ref": GATEC2_EXECUTION_REF,
            "latest_active_metadata_baseline_ref": baseline_ref,
            "active_catalog_rel": ACTIVE_CATALOG_REL,
            "active_manifest_rel": ACTIVE_MANIFEST_REL,
        },
        "summary": {
            "dataset_count": len(pointer_records),
            "published_true_after_virtual_count": sum(1 for item in pointer_records if item["after_published"] is True),
            "pointer_validation_pass_count": sum(1 for item in pointer_validations if item["passed"]),
            "canonical_object_exists_count": sum(1 for item in canonical_object_validations if item["exists"]),
            "canonical_row_count_match_count": sum(
                1 for item in canonical_object_validations if item["row_count_matches_catalog"]
            ),
            "blocking_risk_count": len(blocking_risks),
            "warning_count": len(warnings),
            "defaulted_universe_scope_count": defaulted_universe_scope,
            "defaulted_as_of_trade_date_count": defaulted_as_of_trade_date,
            "defaulted_known_limitations_count": defaulted_known_limitations,
            "active_catalog_sha256_before": active_catalog_before_sha,
            "active_catalog_sha256_after_preview": current_catalog_after_sha,
            "active_manifest_sha256_before": active_manifest_before_sha,
            "active_manifest_sha256_after_preview": current_manifest_after_sha,
            "active_manifest_line_count": active_manifest_before_lines,
            "virtual_after_catalog_sha256": after_virtual_sha,
            "virtual_after_ref": AFTER_REF,
            "virtual_diff_ref": DIFF_REF,
        },
        "operation_counts": operation_counts,
        "checks": checks,
        "failed_checks": failed_checks,
        "blocking_risks": blocking_risks,
        "warnings": warnings,
        "pointer_records": pointer_records,
        "pointer_validations": pointer_validations,
        "canonical_object_validations": canonical_object_validations,
        "pit_semantics": pit_semantics,
        "authorization_decision": {
            "real_pointer_advance_allowed_by_preview": not failed_checks,
            "reason": "all checks passed" if not failed_checks else "blocking publish semantics risk requires decision",
        },
        "non_authorized_scope": [
            "active catalog write",
            "active manifest append",
            "provider catalog write",
            "provider-lake-catalog write",
            "published pointer advance execution",
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
        "next_action": (
            "Stop before Gate D execution; resolve PIT publication semantics for blocked datasets."
            if failed_checks
            else "Proceed to Gate D pointer advance execution under explicit authorization."
        ),
    }
    index = {
        "schema_version": "cr139.gated.pointer_advance_preview.index.v1",
        "workflow_id": evidence["workflow_id"],
        "gate": evidence["gate"],
        "created_at": created_at,
        "status": status,
        "preview_ref": PREVIEW_REF,
        "check_ref": CHECK_REF,
        "virtual_after_ref": AFTER_REF,
        "virtual_diff_ref": DIFF_REF,
        "summary": evidence["summary"],
        "operation_counts": operation_counts,
        "failed_checks": failed_checks,
        "blocking_risks": blocking_risks,
    }

    write_json(project_root / PREVIEW_REF, evidence)
    write_json(project_root / INDEX_REF, index)
    write_json(project_root / AFTER_REF, after_catalog)
    write_text(project_root / DIFF_REF, diff_text)
    write_check(project_root / CHECK_REF, evidence)
    append_gate_ledger(project_root / GATE_LEDGER_REF, evidence)
    print(json.dumps({"status": status, "summary": evidence["summary"], "failed_checks": failed_checks}, ensure_ascii=False, indent=2))
    return 0


def validate_canonical_object(lake_root: Path, dataset: str, record: dict[str, Any]) -> dict[str, Any]:
    rel = str(record.get("canonical_path") or "")
    path = lake_root / rel
    result: dict[str, Any] = {
        "dataset": dataset,
        "canonical_path": rel,
        "exists": path.is_file(),
        "uses_cr139_run_id": "run_id=cr139-w2-" in rel,
        "is_canonical_path": rel.startswith("canonical/"),
        "row_count": None,
        "catalog_coverage_denominator": record.get("coverage_denominator"),
        "row_count_matches_catalog": False,
        "sha256": None,
        "size_bytes": None,
    }
    if path.is_file():
        result["row_count"] = int(pq.ParquetFile(path).metadata.num_rows)
        result["row_count_matches_catalog"] = result["row_count"] == record.get("coverage_denominator")
        result["sha256"] = sha256_file(path)
        result["size_bytes"] = path.stat().st_size
    return result


def inspect_pit_semantics(lake_root: Path, dataset: str, record: dict[str, Any]) -> dict[str, Any]:
    rel = str(record.get("canonical_path") or "")
    path = lake_root / rel
    result: dict[str, Any] = {
        "dataset": dataset,
        "catalog_pit_status": record.get("pit_status"),
        "has_row_level_pit_status": False,
        "pit_status_distribution": {},
        "blocks_pointer_advance": False,
        "reason": None,
    }
    if not path.is_file():
        return result
    schema = pq.read_schema(path)
    if "pit_status" not in schema.names:
        return result
    result["has_row_level_pit_status"] = True
    values = pq.read_table(path, columns=["pit_status"]).column("pit_status").to_pandas()
    distribution = {str(key): int(value) for key, value in values.value_counts(dropna=False).to_dict().items()}
    result["pit_status_distribution"] = distribution
    if record.get("pit_status") == PIT_STATUS_AVAILABLE and any(key != PIT_STATUS_AVAILABLE for key in distribution):
        result["blocks_pointer_advance"] = True
        result["reason"] = "dataset-level pit_available claim conflicts with row-level PIT status distribution"
    return result


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def count_lines(path: Path) -> int:
    return path.read_bytes().count(b"\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(payload) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_check(path: Path, evidence: dict[str, Any]) -> None:
    status = "PASS" if not evidence["failed_checks"] else "BLOCKED"
    rows = "\n".join(
        f"| {idx} | `{name}` | {'PASS' if passed else 'FAIL'} | `{PREVIEW_REF}` | {'通过' if passed else '阻断真实 pointer advance'} |"
        for idx, (name, passed) in enumerate(evidence["checks"].items(), start=1)
    )
    pointer_rows = "\n".join(
        f"| {item['dataset']} | {item['before_published']} -> {item['after_published']} | `{item['canonical_path']}` | {item['coverage_denominator']} | `{item['universe_scope']}` | `{item['as_of_trade_date']}` | `{item['pit_status']}` |"
        for item in evidence["pointer_records"]
    )
    risk_rows = "\n".join(
        f"| {item['risk_id']} | {item['severity']} | {item['dataset']} | `{json.dumps(item['pit_status_distribution'], ensure_ascii=False, sort_keys=True)}` | {item['required_decision']} |"
        for item in evidence["blocking_risks"]
    ) or "| 无 | - | - | - | - |"
    warning_rows = "\n".join(
        f"| {item['warning_id']} | {item['severity']} | {item.get('count', '-')} | {item['reason']} |"
        for item in evidence["warnings"]
    ) or "| 无 | - | - | - |"
    summary = evidence["summary"]
    text = f"""---
checkpoint_id: "CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29"
checkpoint_name: "CR139 W2 Gate D Published Pointer Advance No-Write Preview"
type: "runtime_preview_check"
status: "{status}"
owner: "host-orchestrator"
created_at: "{evidence['created_at']}"
checked_at: "{evidence['created_at']}"
target:
  phase: "CR139-W2-DATA-CONTRACTS Gate D"
  story_id: null
  artifacts:
    - "{PREVIEW_REF}"
    - "{INDEX_REF}"
    - "{AFTER_REF}"
    - "{DIFF_REF}"
---

# CR139 W2 Gate D Published Pointer Advance No-Write Preview

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Gate C-2 active catalog/manifest write verified | {'PASS' if evidence['checks']['gate_c2_active_catalog_manifest_write_verified'] else 'FAIL'} | `{GATEC2_EXECUTION_REF}` | active catalog 已指向 CR139 canonical，但 published=false。 |
| Active catalog hash matches latest active metadata after | {'PASS' if evidence['checks']['active_catalog_hash_matches_latest_active_metadata_after'] else 'FAIL'} | `{PREVIEW_REF}` | 确认 preview 基线未漂移。 |
| No write mode | PASS | `{PREVIEW_REF}` | 本 preview 不写 active catalog、manifest、published 目录或 provider catalog。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
{rows}

## Virtual Pointer Records

| Dataset | published | canonical_path | Rows | universe_scope | as_of_trade_date | pit_status |
|---|---|---|---:|---|---|---|
{pointer_rows}

## Blocking Risks

| Risk ID | Severity | Dataset | Row-level PIT distribution | Required decision |
|---|---|---|---|---|
{risk_rows}

## Warnings

| Warning ID | Severity | Count | Reason |
|---|---|---:|---|
{warning_rows}

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| Virtual pointer contract valid | {'PASS' if evidence['checks']['pointer_required_fields_valid_17'] else 'FAIL'} | `{AFTER_REF}` | 17/17 virtual pointer 必填字段可通过合同校验。 |
| Current truth not changed by preview | {'PASS' if evidence['checks']['active_catalog_file_unchanged'] and evidence['checks']['active_manifest_file_unchanged'] else 'FAIL'} | `{PREVIEW_REF}` | active catalog/manifest hash unchanged。 |
| No blocking publish semantics risk | {'PASS' if evidence['checks']['no_blocking_publish_semantics_risk'] else 'FAIL'} | `{PREVIEW_REF}` | 发现 HIGH 风险时不得继续真实 pointer advance。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| Preview evidence | `{PREVIEW_REF}` | {status} | Gate D no-write preview 机器证据。 |
| Evidence index | `{INDEX_REF}` | {status} | 证据索引。 |
| Virtual after catalog | `{AFTER_REF}` | {status} | 未写入 active catalog 的 virtual after。 |
| Virtual diff | `{DIFF_REF}` | {status} | pointer advance diff。 |
| Preview check | `{CHECK_REF}` | {status} | 本文件。 |

## 结论

- 结论：`{status}`
- status：`{evidence['status']}`
- dataset_count：{summary['dataset_count']}
- published_true_after_virtual_count：{summary['published_true_after_virtual_count']}
- pointer_validation_pass_count：{summary['pointer_validation_pass_count']}
- canonical_object_exists_count：{summary['canonical_object_exists_count']}
- canonical_row_count_match_count：{summary['canonical_row_count_match_count']}
- blocking_risk_count：{summary['blocking_risk_count']}
- warning_count：{summary['warning_count']}
- active_catalog_sha256_before：`{summary['active_catalog_sha256_before']}`
- active_catalog_sha256_after_preview：`{summary['active_catalog_sha256_after_preview']}`
- active_manifest_sha256_before：`{summary['active_manifest_sha256_before']}`
- active_manifest_sha256_after_preview：`{summary['active_manifest_sha256_after_preview']}`
- virtual_after_catalog_sha256：`{summary['virtual_after_catalog_sha256']}`
- 阻断项：{', '.join(evidence['failed_checks']) if evidence['failed_checks'] else '无'}
- 下一步：{evidence['next_action']}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_gate_ledger(path: Path, evidence: dict[str, Any]) -> None:
    event = {
        "schema_version": "meta-flow.gate-event.v1",
        "event_type": "published_pointer_advance_preview",
        "event_id": "CR139-W2-GATED-POINTER-ADVANCE-PREVIEW-2026-06-29",
        "workflow_id": evidence["workflow_id"],
        "gate": "Gate D",
        "created_at": evidence["created_at"],
        "status": evidence["status"],
        "artifact_refs": [PREVIEW_REF, INDEX_REF, CHECK_REF, AFTER_REF, DIFF_REF],
        "operation_counts": evidence["operation_counts"],
        "summary": evidence["summary"],
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
