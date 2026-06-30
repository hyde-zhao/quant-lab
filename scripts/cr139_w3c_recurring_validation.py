#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLISH_GUARD = PROJECT_ROOT / "scripts/cr139_w3b_publish_guard.py"
PUBLISH_GUARD_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W3B-PUBLISH-GUARD-2026-06-30.json"
RETENTION_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W3B-RETENTION-SUPERSEDED-REGISTER-2026-06-30.json"
RETENTION_REGISTER = PROJECT_ROOT / "process/registers/CR139-W3-LEGACY-SUPERSEDED-REGISTER-2026-06-30.json"
GATEH_SYNC_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W2-GATEH-NAS-SYNC-EXECUTION-2026-06-30.json"
GATEG_EVIDENCE = PROJECT_ROOT / "process/evidence/CR139-W2-GATEG-PROVIDER-CATALOG-APPLICABILITY-2026-06-30.json"
EVIDENCE_PATH = PROJECT_ROOT / "process/evidence/CR139-W3C-RECURRING-VALIDATION-2026-06-30.json"
CHECK_PATH = PROJECT_ROOT / "process/checks/CR139-W3C-RECURRING-VALIDATION-2026-06-30.md"


def main() -> int:
    guard_run = subprocess.run(
        [sys.executable, str(PUBLISH_GUARD)],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    publish_guard = load_json(PUBLISH_GUARD_EVIDENCE)
    retention = load_json(RETENTION_EVIDENCE)
    register = load_json(RETENTION_REGISTER)
    gateh = load_json(GATEH_SYNC_EVIDENCE)
    gateg = load_json(GATEG_EVIDENCE)

    reader_matrix = publish_guard.get("reader_support_matrix", [])
    supported_count = sum(1 for item in reader_matrix if item.get("contract_supported"))
    pointer_only = [item["dataset"] for item in reader_matrix if item.get("pointer_only_allowed")]
    conditional_readers = [item["dataset"] for item in reader_matrix if item.get("conditional_reader_support")]
    failed_checks: list[str] = []
    checks = {
        "publish_guard_subprocess_exit_zero": guard_run.returncode == 0,
        "publish_guard_pass": publish_guard.get("status") == "pass_w3b_publish_guard",
        "retention_register_pass": retention.get("result") == "pass_w3b_retention_superseded_register",
        "retention_register_record_count_210": register.get("summary", {}).get("legacy_record_count") == 210,
        "reader_supported_count_15": supported_count == 15,
        "pointer_only_waiver_count_2": len(pointer_only) == 2,
        "gateh_post_sync_dry_run_verified": gateh.get("status") == "pass_gate_h_nas_sync_execution",
        "provider_catalog_deferred": gateg.get("status") == "deferred_no_production_provider_catalog_consumer"
        and gateg.get("decision", {}).get("gate_g_provider_catalog") == "deferred",
    }
    failed_checks.extend(name for name, passed in checks.items() if not passed)
    status = "pass_w3c_recurring_validation" if not failed_checks else "blocked_w3c_recurring_validation"
    evidence = {
        "schema": "cr139.w3c.recurring_validation.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "checks": checks,
        "failed_checks": failed_checks,
        "guard_run": {
            "command": f"{sys.executable} {PUBLISH_GUARD.relative_to(PROJECT_ROOT)}",
            "returncode": guard_run.returncode,
            "stdout": guard_run.stdout.strip().splitlines(),
            "stderr": guard_run.stderr.strip().splitlines(),
        },
        "reader_support_summary": {
            "contract_supported_count": supported_count,
            "pointer_only_waivers": pointer_only,
            "conditional_reader_support": conditional_readers,
            "pointer_only_waiver_rationale": {
                "bse_code_mapping": "small mapping/governance table; no confirmed read_dataset consumer",
                "lifecycle_code_change": "small lifecycle mapping/governance table; no confirmed read_dataset consumer",
            },
        },
        "recurring_pack": {
            "local_command": "uv run --python 3.11 scripts/cr139_w3c_recurring_validation.py",
            "publish_guard_command": "uv run --python 3.11 scripts/cr139_w3b_publish_guard.py",
            "nas_dry_run_command": "uv run --python 3.11 scripts/cr139_gateh_nas_dry_run.py",
            "nas_dry_run_policy": "separate runtime authorization before each external NAS touch unless standing approval is explicitly granted",
            "provider_catalog_policy": "deferred until production provider catalog consumer is confirmed",
        },
        "input_refs": {
            "publish_guard_evidence": str(PUBLISH_GUARD_EVIDENCE.relative_to(PROJECT_ROOT)),
            "retention_evidence": str(RETENTION_EVIDENCE.relative_to(PROJECT_ROOT)),
            "retention_register": str(RETENTION_REGISTER.relative_to(PROJECT_ROOT)),
            "gateh_sync_evidence": str(GATEH_SYNC_EVIDENCE.relative_to(PROJECT_ROOT)),
            "gateg_evidence": str(GATEG_EVIDENCE.relative_to(PROJECT_ROOT)),
        },
        "operation_counts": {
            "lake_write": 0,
            "lake_delete": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "nas_operation": 0,
            "credential_print_or_persist": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_check(evidence)
    print(status)
    print(f"evidence={EVIDENCE_PATH}")
    print(f"check={CHECK_PATH}")
    return 0 if not failed_checks else 1


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_check(evidence: dict[str, Any]) -> None:
    check_rows = "\n".join(f"| {key} | {value} |" for key, value in sorted(evidence["checks"].items()))
    text = f"""# CR139 W3-C Recurring Validation

## Result

- status: `{evidence['status']}`
- failed_checks: `{evidence['failed_checks']}`
- local command: `{evidence['recurring_pack']['local_command']}`

## Checks

| check | result |
|---|---:|
{check_rows}

## Reader Support

- contract_supported_count: `{evidence['reader_support_summary']['contract_supported_count']}`
- pointer_only_waivers: `{evidence['reader_support_summary']['pointer_only_waivers']}`
- conditional_reader_support: `{evidence['reader_support_summary']['conditional_reader_support']}`

## Recurring Pack

- publish guard: `{evidence['recurring_pack']['publish_guard_command']}`
- NAS dry-run: `{evidence['recurring_pack']['nas_dry_run_command']}`
- NAS policy: {evidence['recurring_pack']['nas_dry_run_policy']}
- provider policy: {evidence['recurring_pack']['provider_catalog_policy']}

## Operation Counts

```json
{json.dumps(evidence['operation_counts'], indent=2, sort_keys=True)}
```
"""
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
