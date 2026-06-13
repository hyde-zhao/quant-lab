---
cr_id: "CR045"
release_decision: "READY_WITH_RISK"
created_at: "2026-06-11T23:46:53+08:00"
---

# CR045 Feedback

## Observation Signals

| Signal | Trigger | Route |
|---|---|---|
| Need real Windows bridge health | User requests runtime startup or health against Windows PC | New runtime_authorization gate / future L3 CR |
| Need real readonly fields | User requests cash/position/order/fill/account state | Future L4 readonly probe gate |
| Need submit/cancel/simulation/live | User requests trading or simulation execution | Future L5 CR with risk controls |
| L2 fixture contract mismatch | Tests or downstream adapter report schema mismatch | New fix CR or CP7 rework |
| Global quality traceability gap | Need shared TEST-MATRIX / TEST-STRATEGY | Follow-up quality-system CR |

## Feedback Classification

| Feedback Type | Handling |
|---|---|
| Bug in L2 skeleton | Route to meta-po; create fix CR or CP7 rework depending on severity. |
| Request for L3/L4/L5 runtime | Do not execute directly; require explicit runtime_authorization gate or new CR. |
| Credential handling question | Do not collect credentials; document local Windows-only custody assumptions. |
| Documentation wording issue | Patch runbook/release docs and rerun CR045 scoped static checks. |

## Non-Authorized Feedback

Feedback messages must not contain token, account_id, password, session, cookie, private key, broker payload, order references or account snapshots.
