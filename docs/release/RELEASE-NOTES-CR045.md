---
cr_id: "CR045"
release_decision: "READY_WITH_RISK"
release_artifact_profile: "compact"
created_at: "2026-06-11T23:46:53+08:00"
---

# CR045 Release Notes

## Release Summary

CR045 delivers a local, audited L2 Goldminer Windows Bridge skeleton. It adds fixture-only contracts for health, capabilities, WSL/Linux client calls, readonly probe blocked-first behavior, redaction, no-operation validation, and a user runbook.

This release is `READY_WITH_RISK`: the L2 skeleton is verified, but real Windows runtime, real readonly account data, and trading/simulation operations remain not authorized and unverified.

## User-Visible Changes

| Area | Change |
|---|---|
| Bridge contract | Adds `engine/goldminer_bridge_contract.py` with L2 schema, false capability flags, allowlist, blocked reasons, sensitive field categories and zero operation counters. |
| WSL/Linux client | Adds `engine/goldminer_bridge_client.py` with fixture transport and declarative network precheck. |
| Readonly skeleton | Adds `engine/goldminer_bridge_probe.py`; L4 missing authorization and real query kinds are blocked-first. |
| Safety tests | Adds CR045 tests for fixture behavior, no SDK/runtime import, no network/process calls, no-operation counters and runbook wording. |
| Runbook | Adds `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` with L2 scope, not-authorized items and future L3/L4/L5 gates. |

## Quality Summary

| Evidence | Result |
|---|---|
| CP6 | PASS |
| CP7 | PASS_WITH_RISK |
| Target pytest | `24 passed` |
| `py_compile` | PASS |
| `git diff --check` | PASS |
| Findings | none-found |

## Known Risks

| Risk ID | Status | Summary |
|---|---|---|
| CR045-R1 | accepted-current-scope | L3 Windows bridge runtime is not authorized; real health, process, port and SDK availability are not verified. |
| CR045-R2 | accepted-current-scope | L4 readonly probe is not authorized; real cash, position, order, fill and account state fields are not verified. |
| CR045-R3 | accepted-current-scope | L5 submit/cancel/simulation/live is not authorized; simulation/live ready must remain false. |
| CR045-R4 | accepted-current-scope | Global TEST-MATRIX / TEST-STRATEGY are absent; CR045 scoped TEST-PLAN and reports are used as equivalent traceability for this CR. |

## Not Authorized

CP8 approval will not authorize credential reads, Windows bridge runtime startup, Goldminer login/connect, account/cash/position/order/fill queries, order submit/cancel, simulation/live, provider fetch, lake write or catalog publish.

## Rollback

Rollback is file-level removal of CR045 L2 skeleton assets and scoped reports. No runtime state, migration or external system state is changed by this release.
