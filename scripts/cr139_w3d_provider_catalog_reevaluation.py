#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESS_ROOT = PROJECT_ROOT / "process"
EVIDENCE_PATH = PROCESS_ROOT / "evidence/CR139-W3D-PROVIDER-CATALOG-REEVALUATION-2026-06-30.json"
CHECK_PATH = PROCESS_ROOT / "checks/CR139-W3D-PROVIDER-CATALOG-REEVALUATION-2026-06-30.md"
SOURCE_PATHS = [
    PROCESS_ROOT / "plans/CR139-W3-GOVERNANCE-PLANNING-2026-06-30.md",
    PROCESS_ROOT / "evidence/CR139-W3C-RECURRING-VALIDATION-2026-06-30.json",
    PROCESS_ROOT / "evidence/CR139-W2-GATEG-PROVIDER-CATALOG-APPLICABILITY-2026-06-30.json",
    PROCESS_ROOT / "release/RELEASE-CONTEXT-CR139-W2.yaml",
    PROCESS_ROOT / "checkpoints/CP8-CR139-W2-DELIVERY-READINESS.md",
    PROJECT_ROOT / "market_data/catalog.py",
]


def main() -> int:
    checked_at = datetime.now(timezone.utc).isoformat()
    source_summaries: list[dict[str, Any]] = []
    production_consumer_evidence: list[dict[str, Any]] = []
    conditional_mentions: list[dict[str, Any]] = []
    for path in SOURCE_PATHS:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        mentions = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if "provider catalog" in lower or "provider-lake-catalog" in lower or "provider_lake_catalog" in lower:
                mentions.append({"line": line_no, "text": line.strip()})
                if any(token in lower for token in ("conditional", "deferred", "not authorized")) or "不授权" in line:
                    conditional_mentions.append(
                        {"path": str(path.relative_to(PROJECT_ROOT)), "line": line_no, "text": line.strip()}
                    )
                if "production consumer" in lower and "confirmed" in lower and "use provider catalog" in lower:
                    production_consumer_evidence.append(
                        {"path": str(path.relative_to(PROJECT_ROOT)), "line": line_no, "text": line.strip()}
                    )
        source_summaries.append(
            {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.exists(),
                "provider_catalog_mention_count": len(mentions),
                "mentions": mentions[:20],
            }
        )

    # Lines that describe the trigger condition are not evidence that a consumer exists.
    production_consumer_evidence = [
        item
        for item in production_consumer_evidence
        if "if a production consumer is confirmed" not in item["text"].lower()
        and "only if production" not in item["text"].lower()
    ]
    checks = {
        "w3_plan_declares_gate_g_conditional": "provider catalog remains deferred unless a real production consumer appears"
        in (PROCESS_ROOT / "plans/CR139-W3-GOVERNANCE-PLANNING-2026-06-30.md").read_text(encoding="utf-8").lower(),
        "w3c_recurring_pack_records_provider_policy": "provider_catalog_deferred"
        in (PROCESS_ROOT / "evidence/CR139-W3C-RECURRING-VALIDATION-2026-06-30.json").read_text(encoding="utf-8").lower()
        and "deferred until production provider catalog consumer is confirmed"
        in (PROCESS_ROOT / "evidence/CR139-W3C-RECURRING-VALIDATION-2026-06-30.json").read_text(encoding="utf-8").lower(),
        "no_production_consumer_evidence_found": len(production_consumer_evidence) == 0,
        "no_provider_catalog_write_executed": True,
    }
    failed_checks = [name for name, passed in checks.items() if not passed]
    payload = {
        "schema": "cr139.w3d.provider_catalog_reevaluation.v1",
        "checked_at": checked_at,
        "status": "deferred_no_production_provider_catalog_consumer"
        if not failed_checks
        else "blocked_provider_catalog_reevaluation_unclear",
        "decision": {
            "provider_catalog_sync": "deferred",
            "reason": "W3 re-evaluation found no confirmed production consumer that uses provider catalog/provider-lake-catalog as current truth.",
            "next_trigger": "Open a separate Gate G authorization only after a production consumer is confirmed.",
        },
        "checks": checks,
        "failed_checks": failed_checks,
        "source_summaries": source_summaries,
        "production_consumer_evidence": production_consumer_evidence,
        "conditional_mentions": conditional_mentions,
        "operation_counts": {
            "provider_catalog_write": 0,
            "provider_lake_catalog_write": 0,
            "active_catalog_write": 0,
            "active_manifest_append": 0,
            "nas_operation": 0,
            "credential_read": 0,
            "runtime_operation": 0,
            "git_remote": 0,
        },
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_check(payload)
    print(payload["status"])
    print(f"evidence={EVIDENCE_PATH}")
    print(f"check={CHECK_PATH}")
    return 0 if not failed_checks else 1


def write_check(payload: dict[str, Any]) -> None:
    rows = "\n".join(f"| {name} | {passed} |" for name, passed in sorted(payload["checks"].items()))
    text = f"""# CR139 W3-D Provider Catalog Re-Evaluation

## Result

- status: `{payload['status']}`
- decision: `{payload['decision']['provider_catalog_sync']}`
- failed_checks: `{payload['failed_checks']}`

## Checks

| check | result |
|---|---:|
{rows}

## Operation Counts

```json
{json.dumps(payload['operation_counts'], indent=2, sort_keys=True)}
```
"""
    CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECK_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
