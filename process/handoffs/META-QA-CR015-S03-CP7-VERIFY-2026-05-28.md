---
handoff_id: "META-QA-CR015-S03-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-015"
story_id: "CR015-S03-oms-order-state-machine"
wave_id: "CR015-W2-OMS-RISK-LAKE-CP7"
status: "completed"
created_at: "2026-05-28T08:20:12+08:00"
updated_at: "2026-05-28T08:25:16+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bf4-7b26-7801-9b7b-4343b653315a"
  thread_id: "019e6bf4-7b26-7801-9b7b-4343b653315a"
  agent_name: "qa-lv"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:20:48+08:00"
  completed_at: "2026-05-28T08:22:15+08:00"
  closed_at: "2026-05-28T08:25:16+08:00"
---

# META-QA CR015-S03 CP7 Verification Handoff

## Task

Verify `CR015-S03-oms-order-state-machine` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR015-S03-IMPLEMENT-2026-05-28.md` | completed |
| S03 CP6 | `process/checks/CP6-CR015-S03-oms-order-state-machine-CODING-DONE.md` | PASS |
| S03 Story | `process/stories/CR015-S03-oms-order-state-machine.md` | ready-for-verification |
| S03 LLD | `process/stories/CR015-S03-oms-order-state-machine-LLD.md` | confirmed |

## Verification Scope

Read / execute:

- `trading/oms.py`
- `trading/qmt_adapter.py`
- `tests/test_cr015_oms_state_machine.py`
- `tests/test_cr015_qmt_adapter_contract.py`
- `process/checks/CP6-CR015-S03-oms-order-state-machine-CODING-DONE.md`
- `process/stories/CR015-S03-oms-order-state-machine.md`
- `process/stories/CR015-S03-oms-order-state-machine-LLD.md`

Write only:

- `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with Agent Dispatch Evidence. |
| Tests | Run `uv run --python 3.11 pytest -q tests/test_cr015_qmt_adapter_contract.py tests/test_cr015_oms_state_machine.py`. |
| Contract behavior | Verify policy/raw gate, stable idempotency, explicit state set, legal/illegal transitions, unknown/timeout/cancel_failed not success, manual_review required, freeze_orders local-only. |
| Safety scan | Confirm no QMT/MiniQMT process, no broker API call, no real order/cancel/account query/account write, no credential read, no broker lake write, no lake write, no provider fetch, no dependency change, no publish. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters, and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, docs, Story cards, CP6 files, LLD files, or `DEV-LOG.md`.
- Do not implement CR015-S04..S07, CR016, or CR017.
- Do not launch QMT / MiniQMT / GUI apps or import / call real broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, or real holdings.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, or current pointer publish.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
