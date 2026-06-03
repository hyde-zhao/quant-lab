---
handoff_id: "META-QA-CR025-W1-CP7-VERIFY-2026-06-02"
from: "meta-po"
to: "meta-qa"
change_id: "CR-025"
batch_id: "CR025-W1-FEED-GOVERNANCE-CP7"
story_ids:
  - "CR025-S01-clean-feed-gate-backend-selector"
  - "CR025-S04-backtrader-module-reference-no-copy-guardrail"
wave_id: "CR025-W1-FEED-GOVERNANCE"
status: "completed-closed"
created_at: "2026-06-02T07:49:36+08:00"
updated_at: "2026-06-02T07:55:45+08:00"
---

# META-QA Handoff: CR025-W1 CP7 Verification

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-qa` |
| agent_name | `qa-kong` |
| agent_id | `019e8598-7e2d-7113-b2a4-732b3a2bf28c` |
| thread_id | `019e8598-7e2d-7113-b2a4-732b3a2bf28c` |
| spawned_at | `2026-06-02T07:50:33+08:00` |
| completed_at | `2026-06-02T07:52:12+08:00` |
| closed_at | `2026-06-02T07:55:45+08:00` |

## Scope

对 `CR025-W1-FEED-GOVERNANCE` 中已 CP6 PASS 的两个 Story 执行独立 CP7 验证：

- `CR025-S01-clean-feed-gate-backend-selector`
- `CR025-S04-backtrader-module-reference-no-copy-guardrail`

## Inputs

- `process/stories/CR025-S01-clean-feed-gate-backend-selector.md`
- `process/stories/CR025-S01-clean-feed-gate-backend-selector-LLD.md`
- `process/checks/CP6-CR025-S01-clean-feed-gate-backend-selector-CODING-DONE.md`
- `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail.md`
- `process/stories/CR025-S04-backtrader-module-reference-no-copy-guardrail-LLD.md`
- `process/checks/CP6-CR025-S04-backtrader-module-reference-no-copy-guardrail-CODING-DONE.md`
- `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`
- `tests/test_cr025_clean_feed_gate.py`
- `tests/test_cr025_backtrader_no_copy_guardrail.py`
- `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md`

## Allowed Write Scope

- `process/checks/CP7-CR025-S01-clean-feed-gate-backend-selector-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S04-backtrader-module-reference-no-copy-guardrail-VERIFICATION-DONE.md`

## Required Verification

- Run S01 fixture-only tests: `uv run --python 3.11 pytest -q tests/test_cr025_clean_feed_gate.py`.
- Run S04 static guardrail tests: `uv run --python 3.11 pytest -q tests/test_cr025_backtrader_no_copy_guardrail.py`.
- Run py_compile for S01/S04 touched Python files, using a temp pycache location.
- Run diff whitespace check for S01/S04 implementation, tests, docs and CP7 files.
- Verify `pyproject.toml` / `uv.lock` are not modified.
- Verify no Backtrader runtime import/run is required by default lightweight path.
- Verify no vendored Backtrader source, samples, tests or datas were introduced.
- Verify no provider fetch, lake write, catalog publish, credential read, QMT / MiniQMT / XtQuant, broker, simulation/live, or multifactor research framework implementation occurred.

## Not Authorized

- Modify source code, tests, docs, Story cards, STATE, STORY-STATUS, DEVELOPMENT-PLAN, CR index or dependency files.
- Modify `pyproject.toml` / `uv.lock` or install dependencies.
- Run Backtrader backend / samples / tests or use `/home/hyde/download/backtrader/**` as runtime input.
- Read, copy, trim, rewrite or source-level migrate Backtrader GPLv3 source.
- Trigger provider fetch, lake write, catalog publish, QMT / MiniQMT / XtQuant, broker, simulation/live, account query, order/cancel, credential read or service start.
- Implement FactorSpec, FactorRunSpec, IC / RankIC, 分层收益、多因子组合、实验追踪、策略准入包, or integrate Qlib / Alphalens / vnpy.alpha.

## Expected Output

- Two CP7 verification result files under `process/checks/`.
- Each CP7 result must include Entry Criteria, Checklist, Exit Criteria, Deliverables, Agent Dispatch Evidence, test commands, forbidden-operation counters and final PASS / FAIL.
- If any check fails, do not mark Story verified; report the blocker and recommended rollback / fix route.
