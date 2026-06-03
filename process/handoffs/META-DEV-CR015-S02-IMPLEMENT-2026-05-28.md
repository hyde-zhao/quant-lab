---
handoff_id: "META-DEV-CR015-S02-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S02-qmt-broker-adapter-contract"
wave_id: "CR015-W1-FOUNDATION-CONTRACTS"
status: "completed"
created_at: "2026-05-28T07:49:53+08:00"
updated_at: "2026-05-28T08:00:07+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bd8-b70c-7970-a1eb-dd71e647e6d0"
  thread_id: "019e6bd8-b70c-7970-a1eb-dd71e647e6d0"
  agent_name: "dev-you"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T07:50:28+08:00"
  completed_at: "2026-05-28T07:57:21+08:00"
  closed_at: "2026-05-28T08:00:07+08:00"
---

# META-DEV CR015-S02 Implementation Handoff

## Task

Implement `CR015-S02-qmt-broker-adapter-contract` after CR015-S01 and CR017-S01 are verified.

This Story may run in parallel with CR017-S04 because the write scopes are disjoint. It must remain shadow / dry-run / mock only, and must not call real QMT, broker APIs, launch GUI, read credentials, create real orders, cancel orders, query accounts, or write a real broker lake.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S01 CP7 | `process/checks/CP7-CR015-S01-qmt-environment-and-interface-spike-VERIFICATION-DONE.md` | PASS |
| CR017-S01 Story | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | verified |
| S02 Story | `process/stories/CR015-S02-qmt-broker-adapter-contract.md` | dev-ready |
| S02 LLD | `process/stories/CR015-S02-qmt-broker-adapter-contract-LLD.md` | confirmed |

## Allowed Write Scope

- `trading/qmt_adapter.py`
- `trading/qmt_transport.py`
- `tests/test_cr015_qmt_adapter_contract.py`
- `process/checks/CP6-CR015-S02-qmt-broker-adapter-contract-CODING-DONE.md`
- Necessary status updates only for the assigned Story card.

## Forbidden Scope

- Do not implement CR015-S03..S07, CR016, or CR017.
- Do not import or call real broker / QMT / XtQuant APIs.
- Do not launch QMT / MiniQMT / GUI apps or any real broker process.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, account write, dependency changes, or current pointer publish.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| Adapter contract | `submit_intent`, `cancel_order`, `build_mock_broker_event`, mode gate, raw execution policy gate, and blocked result implemented. |
| Allowed modes | `shadow`、`dry_run`、`mock` work as offline contract; `simulation`、`live_readonly`、`small_live` are blocked in CR015. |
| Mock events | accepted / partial / filled / rejected / timeout / unknown are covered. |
| Raw execution gate | `execution_price_policy != raw` is blocked; adjusted execution pass count is 0. |
| Tests | Run `uv run --python 3.11 pytest -q tests/test_cr015_qmt_adapter_contract.py`; include integration with S01 transport if changed. |
| CP6 | Write CP6 PASS/BLOCKED file with Agent Dispatch Evidence and safety counters. |
| Safety counters | qmt_api_call=0, real_order=0, real_cancel=0, account_query=0, account_write=0, credential_read=0, real_broker_lake_write=0, real_lake_write=0, provider_fetch=0, publish=0, dependency_change=0. |

## Result

| 条目 | 结果 |
|---|---|
| Agent | `dev-you` / `019e6bd8-b70c-7970-a1eb-dd71e647e6d0` |
| Completion | `completed_at=2026-05-28T07:57:21+08:00`; `closed_at=2026-05-28T08:00:07+08:00` |
| CP6 | `process/checks/CP6-CR015-S02-qmt-broker-adapter-contract-CODING-DONE.md` PASS |
| Story status | `ready-for-verification` |
| Tests | S02 target -> `14 passed in 0.04s`; S01/S02 regression -> `22 passed in 0.05s`; meta-po rerun -> `22 passed in 0.07s`; `py_compile` passed |
| Safety counters | qmt_api_call / real_order / real_cancel / account_query / account_write / credential_read / real_broker_lake_write / real_lake_write / provider_fetch / publish / dependency_change all `0`; adjusted_execution_pass_count `0` |
