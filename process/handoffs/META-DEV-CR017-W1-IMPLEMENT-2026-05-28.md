---
handoff_id: "META-DEV-CR017-W1-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-017"
story_id: "CR017-S01-adjustment-policy-requirements-and-adr-refresh, CR017-S02-raw-prices-and-adj-factor-contract-hardening"
wave_id: "CR017-W1-ADJUSTMENT-CONTRACTS"
status: "completed"
created_at: "2026-05-28T07:03:27+08:00"
updated_at: "2026-05-28T07:19:51+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bb1-f913-7582-96c8-68737021cf85"
  thread_id: "019e6bb1-f913-7582-96c8-68737021cf85"
  agent_name: "dev-he"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T07:08:12+08:00"
  completed_at: "2026-05-28T07:14:01+08:00"
  closed_at: "2026-05-28T07:19:51+08:00"
---

# META-DEV CR017-W1 Implementation Handoff

## Task

Implement CR017-W1 after CP5 approval:

- `CR017-S01-adjustment-policy-requirements-and-adr-refresh`
- `CR017-S02-raw-prices-and-adj-factor-contract-hardening`

S01 and S02 must be implemented serially inside this handoff because they share `market_data/contracts.py` and S02 consumes S01 policy contracts.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S01 Story | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh.md` | dev-ready |
| S01 LLD | `process/stories/CR017-S01-adjustment-policy-requirements-and-adr-refresh-LLD.md` | confirmed |
| S02 Story | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening.md` | dev-ready |
| S02 LLD | `process/stories/CR017-S02-raw-prices-and-adj-factor-contract-hardening-LLD.md` | confirmed |

## Allowed Write Scope

- `market_data/adjustment_policy.py`
- `market_data/adjustment_contracts.py`
- `market_data/contracts.py`
- `market_data/validation.py`
- `docs/ADJUSTMENT-POLICY-MIGRATION.md`
- `tests/test_cr017_adjustment_policy_contract.py`
- `tests/test_cr017_raw_adj_factor_contract.py`
- `process/checks/CP6-CR017-S01-adjustment-policy-requirements-and-adr-refresh-CODING-DONE.md`
- `process/checks/CP6-CR017-S02-raw-prices-and-adj-factor-contract-hardening-CODING-DONE.md`
- Necessary status updates only for the two assigned Story cards.

## Forbidden Scope

- Do not implement CR017-S03..S06, CR015, or CR016.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not trigger provider fetch, real lake write, catalog current pointer publish, dependency changes, or legacy qfq overwrite.
- Do not modify `pyproject.toml`, `uv.lock`, `market_data/connectors/**`, `market_data/runtime.py`, `data/**`, `reports/**`, or `delivery/**`.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| S01 implementation | Policy enum, consumer matrix, QMT raw-only decision, migration summary, and tests implemented. |
| S02 implementation | Raw price / adj_factor contract, required field sets, lineage validation, provider factor direction guard, and tests implemented. |
| Tests | Run S01/S02 targeted tests and any small affected import/contract regression. |
| CP6 | Write one CP6 PASS/BLOCKED file per Story with Agent Dispatch Evidence and real-operation counters. |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0. |

## Result

| 项 | 结果 |
|---|---|
| Result | PASS |
| CP6 S01 | `process/checks/CP6-CR017-S01-adjustment-policy-requirements-and-adr-refresh-CODING-DONE.md` |
| CP6 S02 | `process/checks/CP6-CR017-S02-raw-prices-and-adj-factor-contract-hardening-CODING-DONE.md` |
| Dev agent tests | `21 passed` |
| Meta-po rerun | `21 passed in 0.36s` |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0 |
