---
handoff_id: "META-QA-CR016-S01-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-016"
story_id: "CR016-S01-simulation-account-order-enable-gate"
wave_id: "CR016-W1-SIMULATION-OPS-GATES-CP7"
status: "completed"
created_at: "2026-05-28T10:07:43+08:00"
updated_at: "2026-05-28T10:14:24+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c57-6aac-7762-98e4-c5cc22d583e2"
  thread_id: "019e6c57-6aac-7762-98e4-c5cc22d583e2"
  agent_name: "qa-jin the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T10:08:54+08:00"
  completed_at: "2026-05-28T10:09:54+08:00"
  closed_at: "2026-05-28T10:14:24+08:00"
---

# META-QA CR016-S01 CP7 Verification Handoff

## Task

Verify `CR016-S01-simulation-account-order-enable-gate` after CP6 PASS.

This is an offline contract verification only. Do not execute or authorize any simulation run, QMT / MiniQMT operation, real order, cancel, account query, credential read, broker lake write, provider fetch, lake write, publish, or dependency change.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR016-S01-IMPLEMENT-2026-05-28.md` | completed |
| S01 CP6 | `process/checks/CP6-CR016-S01-simulation-account-order-enable-gate-CODING-DONE.md` | PASS |
| S01 Story | `process/stories/CR016-S01-simulation-account-order-enable-gate.md` | ready-for-verification |
| S01 LLD | `process/stories/CR016-S01-simulation-account-order-enable-gate-LLD.md` | confirmed |
| 上游 CP7 | `process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md` | PASS |

## Verification Scope

Read / execute:

- `trading/stage_gate.py`
- `trading/qmt_adapter.py`
- `docs/QMT-TRADING-RUNBOOK.md`
- `tests/test_cr016_simulation_order_enable_gate.py`
- `tests/test_cr015_qmt_adapter_contract.py`
- `process/checks/CP6-CR016-S01-simulation-account-order-enable-gate-CODING-DONE.md`
- `process/handoffs/META-DEV-CR016-S01-IMPLEMENT-2026-05-28.md`
- `process/stories/CR016-S01-simulation-account-order-enable-gate.md`
- `process/stories/CR016-S01-simulation-account-order-enable-gate-LLD.md`

Write only:

- `process/checks/CP7-CR016-S01-simulation-account-order-enable-gate-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence and completed dev handoff lifecycle. |
| Tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_simulation_order_enable_gate.py tests/test_cr015_qmt_adapter_contract.py`. |
| Stage order | Verify `shadow -> simulation -> live_readonly -> small_live -> scale_up` is fixed and stage skips are blocked. |
| Evidence gate | Verify missing CR015 verified, runbook, CR017 boundary, reconciliation policy, or kill switch readiness returns blocked. |
| Authorization gate | Verify missing per-run authorization fields return `authorization_required_missing`; complete summary can pass `shadow -> simulation`. |
| Adapter precheck | Verify blocked gate result stops before adapter / broker path and keeps adapter/order/cancel/account/credential counters at 0. |
| Scale-up guard | Verify CR017 not verified keeps scale_up allowed count at 0. |
| Runbook boundary | Verify runbook says pass result / runbook is not real simulation authorization. |
| Safety counters | Confirm QMT/order/cancel/account/credential/lake/provider/publish/dependency/simulation/live/adapter block/scale-up counters are 0. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters, and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR016-S02/S03/S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, real broker lake roots, or real positions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, current pointer publish, simulation run, live_readonly, small_live, or scale_up activation.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`live_activation=0`、`adapter_call_on_block=0`、`scale_up_allowed_without_cr017=0`。
