---
handoff_id: "META-DEV-CR025-S02-IMPLEMENT-2026-06-02"
from: "meta-po"
to: "meta-dev"
change_id: "CR-025"
story_id: "CR025-S02-semantic-diff-schema-artifact"
wave_id: "CR025-W2-SEMANTIC-DIFF"
status: "completed-closed"
created_at: "2026-06-02T07:55:45+08:00"
updated_at: "2026-06-02T08:12:05+08:00"
---

# META-DEV Handoff: CR025-S02 Implementation

## Dispatch

| 字段 | 值 |
|---|---|
| mode | `spawn_agent` |
| tool_name | `multi_agent_v1.spawn_agent` |
| agent_role | `meta-dev` |
| agent_name | `dev-zhu` |
| agent_id | `019e85a1-acd8-76f3-96bd-1102eb15f256` |
| thread_id | `019e85a1-acd8-76f3-96bd-1102eb15f256` |
| spawned_at | `2026-06-02T08:00:30+08:00` |
| completed_at | `2026-06-02T08:08:31+08:00` |
| closed_at | `2026-06-02T08:12:05+08:00` |

## Scope

实现 `CR025-S02-semantic-diff-schema-artifact`，只允许受控离线 / fixture / 静态合同实现。S01 与 S04 已 CP7 PASS 并 verified，S02 dev gate 已满足。

## Inputs

- `process/stories/CR025-S02-semantic-diff-schema-artifact.md`
- `process/stories/CR025-S02-semantic-diff-schema-artifact-LLD.md`
- `process/checks/CP5-CR025-S02-semantic-diff-schema-artifact-LLD-IMPLEMENTABILITY.md`
- `process/checks/CP7-CR025-S01-clean-feed-gate-backend-selector-VERIFICATION-DONE.md`
- `process/checks/CP7-CR025-S04-backtrader-module-reference-no-copy-guardrail-VERIFICATION-DONE.md`
- `engine/backtrader_adapter.py`
- `engine/backtest.py`
- `docs/CR025-BACKTRADER-MODULE-REFERENCE.md`
- `checkpoints/CP5-CR025-RESEARCH-EXECUTION-SEMANTIC-ALIGNMENT-BATCH-A-LLD-BATCH.md`

## Allowed Write Scope

- `engine/semantic_diff.py`
- `reports/semantic_diff/**`
- `tests/test_cr025_semantic_diff_contract.py`
- `process/checks/CP6-CR025-S02-semantic-diff-schema-artifact-CODING-DONE.md`

## Implementation Requirements

- Create a clean-room semantic diff schema and builder; do not copy or migrate Backtrader internals.
- Preserve baseline and reference tracks separately; Backtrader-style reference must never overwrite lightweight baseline.
- Support reference unavailable as a valid artifact state with blocked reasons and limitations.
- Include metadata, availability, fills, cash/cost, portfolio, performance, timeline, explanation, qmt_relevance and limitations field groups.
- Keep artifact output local to `reports/semantic_diff/**`; do not write lake, broker lake or catalog current pointers.
- Add fixture-only tests for schema coverage, unavailable reference, baseline/reference separation, claim guard, path guard and forbidden-operation counters.
- Generate CP6 with Entry Criteria, Checklist, Exit Criteria, Deliverables, Agent Dispatch Evidence, test commands, forbidden-operation counters and final PASS / FAIL.

## Recommended Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr025_semantic_diff_contract.py`
- `PYTHONPYCACHEPREFIX=/tmp/cr025-s02-pycompile uv run --python 3.11 python -m py_compile engine/semantic_diff.py tests/test_cr025_semantic_diff_contract.py`
- `git diff --check -- engine/semantic_diff.py reports/semantic_diff tests/test_cr025_semantic_diff_contract.py process/checks/CP6-CR025-S02-semantic-diff-schema-artifact-CODING-DONE.md`
- `git diff --name-only -- pyproject.toml uv.lock`

## Not Authorized

- Modify `pyproject.toml` / `uv.lock` or install dependencies.
- Modify `engine/backtest.py` or `engine/backtrader_adapter.py` unless a blocking mismatch is found; if a mismatch is found, stop and report instead of changing shared files.
- Run Backtrader backend / samples / tests or use `/home/hyde/download/backtrader/**` as runtime input.
- Read, copy, trim, rewrite or source-level migrate Backtrader GPLv3 source.
- Trigger provider fetch, lake write, catalog publish, QMT / MiniQMT / XtQuant, broker, simulation/live, account query, order/cancel, credential read or service start.
- Claim production truth, simulation-ready, QMT admission pass, factor tear sheet, IC / RankIC report, strategy admission package or completed multifactor research framework.
- Implement FactorSpec, FactorRunSpec, IC / RankIC, 分层收益、多因子组合、实验追踪、策略准入包, or integrate Qlib / Alphalens / vnpy.alpha.

## Expected Output

- S02 implementation patch.
- S02 fixture-only tests.
- S02 CP6 coding done check file.
- Final response listing changed files, commands run, PASS / FAIL result and forbidden-operation counters.
