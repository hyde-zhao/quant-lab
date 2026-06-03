---
handoff_id: "META-QA-CR025-S03-CP7-VERIFY-2026-06-02"
from: "meta-po"
to: "meta-qa"
change_id: "CR-025"
story_id: "CR025-S03-order-intent-draft-qmt-boundary"
wave_id: "CR025-W3-ORDER-INTENT-QMT"
status: "completed-closed"
created_at: "2026-06-02T08:40:15+08:00"
updated_at: "2026-06-02T08:50:30+08:00"
---

# META-QA Handoff: CR025-S03 CP7 Verification

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-qa` |
| agent_name | `qa-shi` |
| agent_id | `019e85c8-c788-7e83-b1bb-4b6c5a635306` |
| thread_id | `019e85c8-c788-7e83-b1bb-4b6c5a635306` |
| spawned_at | `2026-06-02T08:43:31+08:00` |
| completed_at | `2026-06-02T08:46:28+08:00` |
| closed_at | `2026-06-02T08:50:30+08:00` |

## Scope

对 `CR025-S03-order-intent-draft-qmt-boundary` 执行独立 CP7 验证。S03 已 CP6 PASS，当前 `ready-for-verification`。

## Inputs

- `process/stories/CR025-S03-order-intent-draft-qmt-boundary.md`
- `process/stories/CR025-S03-order-intent-draft-qmt-boundary-LLD.md`
- `process/checks/CP6-CR025-S03-order-intent-draft-qmt-boundary-CODING-DONE.md`
- `engine/order_intent_draft.py`
- `tests/test_cr025_order_intent_draft_contract.py`
- `engine/semantic_diff.py`
- `tests/test_cr025_semantic_diff_contract.py`
- `process/checks/CP7-CR025-S02-semantic-diff-schema-artifact-VERIFICATION-DONE.md`
- `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`
- `process/checks/CP7-CR015-S06-target-portfolio-to-order-intent-shadow-mode-VERIFICATION-DONE.md`
- `process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md`
- `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md`

## Allowed Write Scope

- `process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md`

## Required Verification

- Run S03 fixture-only test: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py`.
- Run CR025 current regression: `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_order_intent_draft_contract.py tests/test_cr025_semantic_diff_contract.py tests/test_cr025_clean_feed_gate.py tests/test_cr025_backtrader_no_copy_guardrail.py`.
- Run py_compile for S03 files with temp pycache.
- Run diff whitespace check for S03 implementation and CP7 file.
- Verify `pyproject.toml` / `uv.lock`, `trading/oms.py`, and `trading/pretrade_risk.py` are not modified.
- Verify no Backtrader runtime import/run, no Backtrader source read/copy/migration, no provider fetch, lake write, catalog publish, credential read, QMT / MiniQMT / XtQuant, broker, order/cancel/account, service start, simulation/live, or multifactor research framework implementation occurred.
- Verify `order_intent_draft_v1` keeps `qmt_allowed=false`, `not_authorization=true`, `consumer=CR-020..CR-024 later-gated`, non-raw execution price hard block, missing lineage / limitations fail closed, and forbidden-operation counters all 0.

## Not Authorized

- Modify source code, tests, docs, Story cards, STATE, STORY-STATUS, DEVELOPMENT-PLAN, CR index or dependency files.
- Modify `pyproject.toml` / `uv.lock` or install dependencies.
- Modify `trading/oms.py` or `trading/pretrade_risk.py`.
- Run Backtrader backend / samples / tests or use `/home/hyde/download/backtrader/**` as runtime input.
- Read, copy, trim, rewrite or source-level migrate Backtrader GPLv3 source.
- Trigger provider fetch, lake write, catalog publish, QMT / MiniQMT / XtQuant, broker, simulation/live, account query, order/cancel, credential read or service start.
- Claim production truth, simulation-ready, QMT admission pass, factor tear sheet, IC / RankIC report, strategy admission package or completed multifactor research framework.
- Implement FactorSpec, FactorRunSpec, IC / RankIC, 分层收益、多因子组合、实验追踪、策略准入包, or integrate Qlib / Alphalens / vnpy.alpha.

## Expected Output

- `process/checks/CP7-CR025-S03-order-intent-draft-qmt-boundary-VERIFICATION-DONE.md`
- CP7 result must include Entry Criteria, Checklist, Exit Criteria, Deliverables, Agent Dispatch Evidence, test commands, order-intent boundary assessment, forbidden-operation counters and final PASS / FAIL.
- If any check fails, do not mark Story verified; report the blocker and recommended rollback / fix route.
