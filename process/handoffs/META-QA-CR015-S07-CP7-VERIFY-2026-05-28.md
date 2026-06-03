---
handoff_id: "META-QA-CR015-S07-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-015"
story_id: "CR015-S07-docs-and-foundation-runbook-boundary"
wave_id: "CR015-W3-SHADOW-RUNBOOK-CP7"
status: "completed"
created_at: "2026-05-28T09:47:32+08:00"
updated_at: "2026-05-28T09:54:11+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c45-42f0-7ad2-a5a0-4754f184eee9"
  thread_id: "019e6c45-42f0-7ad2-a5a0-4754f184eee9"
  agent_name: "qa-zhang the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:49:02+08:00"
  completed_at: "2026-05-28T09:51:39+08:00"
  closed_at: "2026-05-28T09:54:11+08:00"
---

# META-QA CR015-S07 CP7 Verification Handoff

## Task

Verify `CR015-S07-docs-and-foundation-runbook-boundary` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR015-S07-IMPLEMENT-2026-05-28.md` | completed |
| S07 CP6 | `process/checks/CP6-CR015-S07-docs-and-foundation-runbook-boundary-CODING-DONE.md` | PASS |
| S07 Story | `process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md` | ready-for-verification |
| S07 LLD | `process/stories/CR015-S07-docs-and-foundation-runbook-boundary-LLD.md` | confirmed |
| 上游 CP7 | CR015-S01..S06、CR017-S06 CP7 | PASS |

## Verification Scope

Read / execute:

- `docs/QMT-TRADING-RUNBOOK.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `tests/test_cr015_foundation_runbook_boundary.py`
- `process/checks/CP6-CR015-S07-docs-and-foundation-runbook-boundary-CODING-DONE.md`
- `process/handoffs/META-DEV-CR015-S07-IMPLEMENT-2026-05-28.md`
- `process/stories/CR015-S07-docs-and-foundation-runbook-boundary.md`
- `process/stories/CR015-S07-docs-and-foundation-runbook-boundary-LLD.md`

Write only:

- `process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence and completed dev handoff lifecycle. |
| Tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_foundation_runbook_boundary.py`. |
| Runbook coverage | Verify setup, shadow, dry-run, mock, and handoff to CR016 sections exist. |
| Boundary docs | Verify README / USER-MANUAL contain CR015 allowed modes and CR016 prerequisites without granting authority. |
| Forbidden claims | Verify real trading positive support claims count is 0. |
| Microstructure claims | Verify real VWAP / minute / tick / Level2 / order-match allowed claim count is 0. |
| Sensitive output | Verify docs do not expose token/password/cookie/session/private key/account/holdings/private path values. |
| Safety counters | Confirm QMT/order/cancel/account/credential/lake/provider/publish/dependency/simulation/live/claim counters are 0. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters, and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR016 or any simulation/live activation logic.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, real broker lake roots, or real positions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, current pointer publish, simulation, live_readonly, small_live, or scale_up activation.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_activation=0`、`live_activation=0`、`real_trading_supported_claim_count=0`、`microstructure_allowed_claim_count=0`。
