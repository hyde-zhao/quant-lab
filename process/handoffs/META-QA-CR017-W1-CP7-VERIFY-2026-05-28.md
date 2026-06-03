---
handoff_id: "META-QA-CR017-W1-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-017"
story_id: "CR017-S01-adjustment-policy-requirements-and-adr-refresh, CR017-S02-raw-prices-and-adj-factor-contract-hardening"
wave_id: "CR017-W1-ADJUSTMENT-CONTRACTS"
status: "completed"
created_at: "2026-05-28T07:19:51+08:00"
updated_at: "2026-05-28T07:26:01+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bbd-714e-7621-ad55-06e96e061d35"
  thread_id: "019e6bbd-714e-7621-ad55-06e96e061d35"
  agent_name: "qa-kong"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T07:20:41+08:00"
  completed_at: "2026-05-28T07:22:33+08:00"
  closed_at: "2026-05-28T07:26:01+08:00"
---

# META-QA CR017-W1 CP7 Verification Handoff

## Task

Verify CR017-W1 after CP6:

- `CR017-S01-adjustment-policy-requirements-and-adr-refresh`
- `CR017-S02-raw-prices-and-adj-factor-contract-hardening`

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR017-W1-IMPLEMENT-2026-05-28.md` | completed |
| S01 CP6 | `process/checks/CP6-CR017-S01-adjustment-policy-requirements-and-adr-refresh-CODING-DONE.md` | PASS |
| S02 CP6 | `process/checks/CP6-CR017-S02-raw-prices-and-adj-factor-contract-hardening-CODING-DONE.md` | PASS |
| S01 Story | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | ready-for-verification |
| S02 Story | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening.md` | ready-for-verification |

## Verification Scope

Read / execute:

- `market_data/adjustment_policy.py`
- `market_data/adjustment_contracts.py`
- `market_data/contracts.py`
- `market_data/validation.py`
- `docs/ADJUSTMENT-POLICY-MIGRATION.md`
- `tests/test_cr017_adjustment_policy_contract.py`
- `tests/test_cr017_raw_adj_factor_contract.py`
- `tests/test_market_data_contracts.py`

Write only:

- `process/checks/CP7-CR017-S01-adjustment-policy-requirements-and-adr-refresh-VERIFICATION-DONE.md`
- `process/checks/CP7-CR017-S02-raw-prices-and-adj-factor-contract-hardening-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | Two CP6 files exist, status PASS, with Agent Dispatch Evidence. |
| Tests | Run `uv run --python 3.11 pytest -q tests/test_cr017_adjustment_policy_contract.py tests/test_cr017_raw_adj_factor_contract.py tests/test_market_data_contracts.py`. |
| Contract behavior | Verify exact policy ids, unknown policy fail-fast, QMT raw-only, raw/factor required fields, lineage, factor direction, invalid raw OHLC, derived view isolation. |
| Safety scan | Confirm no `.env` / credential read, no provider fetch, no lake write, no dependency change, no publish, no legacy qfq overwrite. |
| CP7 | Write one CP7 result per Story, with Agent Dispatch Evidence, test results, safety counters, and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, docs, Story cards, CP6 files, or LLD files.
- Do not implement CR017-S03..S06, CR015, or CR016.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not trigger provider fetch, real lake write, catalog current pointer publish, dependency changes, or legacy qfq overwrite.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.

## Result

| 项 | 结果 |
|---|---|
| Result | PASS |
| CP7 S01 | `process/checks/CP7-CR017-S01-adjustment-policy-requirements-and-adr-refresh-VERIFICATION-DONE.md` |
| CP7 S02 | `process/checks/CP7-CR017-S02-raw-prices-and-adj-factor-contract-hardening-VERIFICATION-DONE.md` |
| Tests | `21 passed in 0.39s` |
| Blocking issues | 0 |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0 |
