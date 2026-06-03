---
handoff_id: "META-QA-CR015-S04-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-015"
story_id: "CR015-S04-pretrade-risk-gate"
wave_id: "CR015-W2-OMS-RISK-LAKE-CP7"
status: "completed"
created_at: "2026-05-28T08:41:25+08:00"
updated_at: "2026-05-28T08:48:50+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c08-71c1-7f22-b5ce-80726a751f30"
  thread_id: "019e6c08-71c1-7f22-b5ce-80726a751f30"
  agent_name: "qa-yan the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:42:37+08:00"
  completed_at: "2026-05-28T08:45:18+08:00"
  closed_at: "2026-05-28T08:48:18+08:00"
---

# META-QA CR015-S04 CP7 Verification Handoff

## Task

Verify `CR015-S04-pretrade-risk-gate` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR015-S04-IMPLEMENT-2026-05-28.md` | completed |
| S04 CP6 | `process/checks/CP6-CR015-S04-pretrade-risk-gate-CODING-DONE.md` | PASS |
| S04 Story | `process/stories/CR015-S04-pretrade-risk-gate.md` | ready-for-verification |
| S04 LLD | `process/stories/CR015-S04-pretrade-risk-gate-LLD.md` | confirmed |

## Verification Scope

Read / execute:

- `trading/pretrade_risk.py`
- `trading/oms.py`
- `tests/test_cr015_pretrade_risk_gate.py`
- `tests/test_cr015_oms_state_machine.py`
- `process/checks/CP6-CR015-S04-pretrade-risk-gate-CODING-DONE.md`
- `process/handoffs/META-DEV-CR015-S04-IMPLEMENT-2026-05-28.md`
- `process/stories/CR015-S04-pretrade-risk-gate.md`
- `process/stories/CR015-S04-pretrade-risk-gate-LLD.md`

Write only:

- `process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence. |
| Tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py`. |
| Rule coverage | Verify cash, lot size, T+1 sellable, available position, price policy, duplicate intent, single-symbol limit, portfolio limit and abnormal price. |
| Hard block | Any failed rule must return adapter_calls=0 and structured rule_id / blocked reason / intent id / risk profile evidence. |
| Raw-only | Non-raw/qfq/hfq execution must be blocked. |
| OMS compatibility | Confirm S03 state transition semantics were not changed. |
| Safety scan | Confirm no QMT/MiniQMT process, no broker API call, no real order/cancel/account query/account write, no credential read, no broker lake write, no lake write, no provider fetch, no dependency change and no publish. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR015-S05/S06/S07 or CR016.
- Do not launch QMT / MiniQMT / GUI apps or import / call real broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, or real positions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, or current pointer publish.
