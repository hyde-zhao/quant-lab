---
handoff_id: "META-DEV-CR017-S04-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-017"
story_id: "CR017-S04-reader-api-and-policy-gates"
wave_id: "CR017-W2-DERIVATION-READERS"
status: "completed"
created_at: "2026-05-28T07:41:26+08:00"
updated_at: "2026-05-28T07:56:05+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bd3-3af1-7d23-b48a-1b7a70d06ab2"
  thread_id: "019e6bd3-3af1-7d23-b48a-1b7a70d06ab2"
  agent_name: "dev-yang"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T07:44:29+08:00"
  completed_at: "2026-05-28T07:54:04+08:00"
  closed_at: "2026-05-28T07:56:05+08:00"
---

# META-DEV CR017-S04 Implementation Handoff

## Task

Implement `CR017-S04-reader-api-and-policy-gates` after CR017-S03 CP7 PASS / verified.

This Story may run in parallel with CR015-S01 CP7 because the write scopes are disjoint. It must not trigger provider fetch, lake write, current pointer publish, dependency changes, credential reads, or QMT operations.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S03 CP7 | `process/checks/CP7-CR017-S03-qfq-hfq-derived-view-normalization-VERIFICATION-DONE.md` | PASS |
| S04 Story | `process/stories/CR017-S04-reader-api-and-policy-gates.md` | dev-ready |
| S04 LLD | `process/stories/CR017-S04-reader-api-and-policy-gates-LLD.md` | confirmed |

## Allowed Write Scope

- `market_data/adjustment_readers.py`
- `market_data/readers.py`
- `engine/research_dataset.py`
- `tests/test_cr017_reader_policy_gates.py`
- `process/checks/CP6-CR017-S04-reader-api-and-policy-gates-CODING-DONE.md`
- Necessary status updates only for the assigned Story card.

## Forbidden Scope

- Do not implement CR017-S05/S06, CR015, or CR016.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not trigger provider fetch, real lake write, catalog current pointer publish, dependency changes, or legacy qfq overwrite.
- Do not launch QMT / MiniQMT, import / call broker APIs, or create order / cancel / account paths.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| Reader API | Explicit `research_adjustment_policy` reader API implemented with metadata containing policy, view_id, source_run_id, quality_status, and single_policy_gate_status. |
| Single-policy gate | Missing policy and mixed policy are blocked 100%. |
| QMT handoff | QMT handoff carries research metadata only and `execution_price_policy=raw`; adjusted execution price pass count is 0. |
| Tests | Offline tests cover missing policy, mixed policy, metadata, unpublished candidate, and QMT raw handoff. |
| CP6 | Write CP6 PASS/BLOCKED file with Agent Dispatch Evidence and safety counters. |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0, qmt_api_call=0, real_order=0. |

## Result

| 条目 | 结果 |
|---|---|
| Agent | `dev-yang` / `019e6bd3-3af1-7d23-b48a-1b7a70d06ab2` |
| Completion | `completed_at=2026-05-28T07:54:04+08:00`; `closed_at=2026-05-28T07:56:05+08:00` |
| CP6 | `process/checks/CP6-CR017-S04-reader-api-and-policy-gates-CODING-DONE.md` PASS |
| Story status | `ready-for-verification` |
| Tests | `uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py` -> `5 passed in 0.34s`; CR017 related regression -> `34 passed in 0.45s`; meta-po rerun -> `34 passed in 0.42s` |
| Safety counters | provider_fetch / lake_write / credential_read / current_pointer_publish / dependency_change / legacy_qfq_overwrite / qmt_api_call / real_order all `0` |
| Scope note | `DEV-LOG.md` was updated by meta-dev outside this handoff's Allowed Write Scope; meta-po did not revert it and will route the deviation to CP7 for non-functional review. |
