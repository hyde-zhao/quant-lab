---
handoff_id: "META-QA-CR017-S06-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-017"
story_id: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
wave_id: "CR017-W3-CONSUMER-MIGRATION-CP7"
status: "completed"
created_at: "2026-05-28T08:41:25+08:00"
updated_at: "2026-05-28T08:48:50+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c08-720d-77c0-89e4-1d5c8a57a66b"
  thread_id: "019e6c08-720d-77c0-89e4-1d5c8a57a66b"
  agent_name: "qa-hua the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:42:37+08:00"
  completed_at: "2026-05-28T08:45:04+08:00"
  closed_at: "2026-05-28T08:48:50+08:00"
---

# META-QA CR017-S06 CP7 Verification Handoff

## Task

Verify `CR017-S06-research-qmt-consumer-docs-and-migration-guide` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR017-S06-IMPLEMENT-2026-05-28.md` | completed |
| S06 CP6 | `process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md` | PASS |
| S06 Story | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md` | ready-for-verification |
| S06 LLD | `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md` | confirmed |

## Verification Scope

Read / execute:

- `docs/ADJUSTMENT-POLICY-MIGRATION.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `engine/research_dataset.py`
- `tests/test_cr017_research_qmt_consumer_boundary.py`
- CR017 related regression tests listed below
- `process/checks/CP6-CR017-S06-research-qmt-consumer-docs-and-migration-guide-CODING-DONE.md`
- `process/handoffs/META-DEV-CR017-S06-IMPLEMENT-2026-05-28.md`
- `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide.md`
- `process/stories/CR017-S06-research-qmt-consumer-docs-and-migration-guide-LLD.md`

Write only:

- `process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence. |
| Target tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr017_research_qmt_consumer_boundary.py`. |
| Regression tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr017_reader_policy_gates.py tests/test_cr017_adjustment_leakage_gates.py tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_adjustment_policy_contract.py tests/test_cr017_raw_adj_factor_contract.py tests/test_cr017_qfq_hfq_derivation.py`. |
| Consumer matrix | Verify chart, long-horizon research, factor research and QMT order intent are covered. |
| QMT raw-only | Verify non-raw execution allowed count is 0. |
| Blocked claims | Verify CR017 not verified blocks production adjustment governance and scale_up. |
| Docs boundary | Verify legacy qfq preserved, old reports not overwritten, and unsupported execution features are not claimed as supported. |
| Safety scan | Confirm provider_fetch, lake_write, credential_read, current_pointer_publish, real_order_call, real_cancel_call, account_query_call, dependency_change and legacy_qfq_overwrite are all 0. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, docs, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR015 or CR016.
- Do not launch QMT / MiniQMT / GUI apps or import / call real broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, or real positions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, current pointer publish, or legacy qfq overwrite.
