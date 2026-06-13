---
cr_id: "CR045"
release_decision: "READY_WITH_RISK"
created_at: "2026-06-11T23:46:53+08:00"
---

# CR045 Deploy Checklist

## Scope

This checklist covers repository-level delivery only. There is no installer, package publication, runtime service, broker connection or data publish in CR045.

## Pre-Delivery Checks

| Check | Status | Evidence |
|---|---|---|
| CP5 approved | PASS | `process/checkpoints/CP5-CR045-BRIDGE-BATCH-A-LLD-BATCH.md` |
| CP6 coding done | PASS | `process/checks/CP6-CR045-BRIDGE-BATCH-A-CODING-DONE.md` |
| CP7 verified | PASS_WITH_RISK | `process/checks/CP7-CR045-BRIDGE-BATCH-A-VERIFICATION-DONE.md` |
| Target tests | PASS | `docs/quality/TEST-REPORT-CR045.md` |
| Review findings | PASS | `docs/quality/REVIEW-CR045.md` |
| Runbook present | PASS | `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` |

## Commands To Recheck

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py tests/test_cr045_goldminer_bridge_client.py tests/test_cr045_goldminer_readonly_probe.py tests/test_cr045_goldminer_no_operation_static.py
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python -m py_compile engine/goldminer_bridge_contract.py engine/goldminer_bridge_client.py engine/goldminer_bridge_probe.py
git diff --check
```

## Runtime Checks

| Runtime Action | Status |
|---|---|
| Start Windows bridge runtime | not-authorized |
| Login/connect Goldminer | not-authorized |
| Query account/cash/position/order/fill | not-authorized |
| Submit/cancel order | not-authorized |
| Run simulation/live | not-authorized |
| Provider fetch/lake write/catalog publish | not-authorized |

## Delivery Decision

Repository delivery is ready with risk. Real runtime delivery is not authorized.
