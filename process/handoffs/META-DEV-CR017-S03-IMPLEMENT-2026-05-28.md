---
handoff_id: "META-DEV-CR017-S03-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-017"
story_id: "CR017-S03-qfq-hfq-derived-view-normalization"
wave_id: "CR017-W2-DERIVATION-READERS"
status: "completed"
created_at: "2026-05-28T07:26:01+08:00"
updated_at: "2026-05-28T07:35:49+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bc3-c576-7a22-acd1-69031710d48a"
  thread_id: "019e6bc3-c576-7a22-acd1-69031710d48a"
  agent_name: "dev-zhang"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T07:27:36+08:00"
  completed_at: "2026-05-28T07:34:45+08:00"
  closed_at: "2026-05-28T07:35:49+08:00"
---

# META-DEV CR017-S03 Implementation Handoff

## Task

Implement `CR017-S03-qfq-hfq-derived-view-normalization` after CR017-S02 CP7 PASS.

This Story must implement only offline candidate derivation for qfq / hfq / returns_adjusted. It must not write lake data, publish catalog current pointer, overwrite legacy qfq, read credentials, or trigger provider fetch.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S02 CP7 | `process/checks/CP7-CR017-S02-raw-prices-and-adj-factor-contract-hardening-VERIFICATION-DONE.md` | PASS |
| S03 Story | `process/stories/CR017-S03-qfq-hfq-derived-view-normalization.md` | dev-ready |
| S03 LLD | `process/stories/CR017-S03-qfq-hfq-derived-view-normalization-LLD.md` | confirmed |

## Allowed Write Scope

- `market_data/adjustment_derivation.py`
- `market_data/normalization.py`
- `market_data/contracts.py`
- `tests/test_cr017_qfq_hfq_derivation.py`
- `process/checks/CP6-CR017-S03-qfq-hfq-derived-view-normalization-CODING-DONE.md`
- Necessary status updates only for `process/stories/CR017-S03-qfq-hfq-derived-view-normalization.md`.

## Forbidden Scope

- Do not implement CR017-S04..S06, CR015, or CR016.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not trigger provider fetch, real lake write, catalog current pointer publish, dependency changes, or legacy qfq overwrite.
- Do not modify `pyproject.toml`, `uv.lock`, `market_data/connectors/**`, `market_data/runtime.py`, `data/**`, `reports/**`, or `delivery/**`.
- Do not introduce adjusted prices into any QMT execution price field.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| qfq derivation | `as_of_trade_date` and `input_snapshot_id` required; deterministic lineage. |
| hfq derivation | base date / base policy must be traceable. |
| returns_adjusted | rejects mixed adjustment policy inputs. |
| candidate-only | no lake writes and no current pointer publish. |
| Tests | Run S03 targeted tests plus CR017 S01/S02 regression. |
| CP6 | Write CP6 PASS/BLOCKED with Agent Dispatch Evidence, test results, and safety counters. |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0. |

## Result

| 项 | 结果 |
|---|---|
| Result | PASS |
| CP6 | `process/checks/CP6-CR017-S03-qfq-hfq-derived-view-normalization-CODING-DONE.md` |
| Dev agent tests | S03 targeted `8 passed`; S01/S02 regression `14 passed`; combined contract regression `29 passed` |
| Meta-po rerun | `29 passed in 0.40s` |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0 |
