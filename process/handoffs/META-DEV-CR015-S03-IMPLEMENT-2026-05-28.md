---
handoff_id: "META-DEV-CR015-S03-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S03-oms-order-state-machine"
wave_id: "CR015-W2-OMS-RISK-LAKE"
status: "completed"
created_at: "2026-05-28T08:08:14+08:00"
updated_at: "2026-05-28T08:18:51+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6be9-9023-7d52-b1f2-9f93acea500a"
  thread_id: "019e6be9-9023-7d52-b1f2-9f93acea500a"
  agent_name: "dev-shi"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:08:55+08:00"
  completed_at: "2026-05-28T08:15:23+08:00"
  closed_at: "2026-05-28T08:18:51+08:00"
---

# META-DEV CR015-S03 Implementation Handoff

## Task

Implement `CR015-S03-oms-order-state-machine` after CR015-S02 and CR017-S01 are verified.

This Story is local OMS state-machine only. It must not call real QMT, broker APIs, launch GUI, read accounts or credentials, create real orders/cancels, write real broker lake facts, or implement CR016 reconciliation / live gates.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S02 CP7 | `process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md` | PASS |
| CR017-S01 Story | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | verified |
| S03 Story | `process/stories/CR015-S03-oms-order-state-machine.md` | dev-ready |
| S03 LLD | `process/stories/CR015-S03-oms-order-state-machine-LLD.md` | confirmed |

## Allowed Write Scope

- `trading/oms.py`
- `trading/qmt_adapter.py`
- `tests/test_cr015_oms_state_machine.py`
- `process/checks/CP6-CR015-S03-oms-order-state-machine-CODING-DONE.md`
- Necessary status updates only for the assigned Story card.

## Forbidden Scope

- Do not implement CR015-S04..S07, CR016, or CR017.
- Do not import or call real broker / QMT / XtQuant APIs.
- Do not launch QMT / MiniQMT / GUI apps or any real broker process.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, or real holdings.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, account write, dependency changes, or current pointer publish.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, or `DEV-LOG.md`.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| Order intent | `create_order_intent()` requires `research_adjustment_policy` and `execution_price_policy=raw`; missing/non-raw inputs are blocked. |
| Idempotency | Same strategy/run/symbol/side/date/qty inputs generate stable `idempotency_key`. |
| State machine | Explicit transition table covers created, risk_passed, blocked, accepted, partially_filled, filled, cancel_pending, canceled, rejected, failed, timeout, unknown, manual_review, frozen. |
| Failure semantics | unknown / timeout / cancel_failed do not become success; manual_review_required is true where appropriate. |
| Freeze | `freeze_orders()` only mutates local state / incident ref and keeps real_cancel=0. |
| Tests | Run `uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py`; if `qmt_adapter.py` changes, also run `uv run --python 3.11 pytest -q tests/test_cr015_qmt_adapter_contract.py tests/test_cr015_oms_state_machine.py`. |
| CP6 | Write CP6 PASS/BLOCKED file with Agent Dispatch Evidence and safety counters. |
| Safety counters | qmt_api_call=0, real_order=0, real_cancel=0, account_query=0, account_write=0, credential_read=0, real_broker_lake_write=0, real_lake_write=0, provider_fetch=0, publish=0, dependency_change=0, unknown_success_count=0, timeout_success_count=0. |

## Result

| 条目 | 结果 |
|---|---|
| Agent | `dev-shi` / `019e6be9-9023-7d52-b1f2-9f93acea500a` |
| Completion | `completed_at=2026-05-28T08:15:23+08:00`; `closed_at=2026-05-28T08:18:51+08:00` |
| CP6 | `process/checks/CP6-CR015-S03-oms-order-state-machine-CODING-DONE.md` PASS |
| Story status | `ready-for-verification` |
| Tests | S03 target -> `11 passed in 0.06s`; S02/S03 regression -> `25 passed in 0.09s`; meta-po rerun -> `25 passed in 0.09s` |
| Safety counters | qmt_api_call / real_order / real_cancel / account_query / account_write / credential_read / real_broker_lake_write / real_lake_write / provider_fetch / publish / dependency_change all `0`; unknown_success_count / timeout_success_count all `0` |
