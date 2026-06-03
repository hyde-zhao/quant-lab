---
handoff_id: "META-DEV-CR017-S05-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-017"
story_id: "CR017-S05-validation-quality-parity-and-leakage-tests"
wave_id: "CR017-W2-DERIVATION-READERS"
status: "completed"
created_at: "2026-05-28T08:04:33+08:00"
updated_at: "2026-05-28T08:16:00+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6be6-532d-78b1-a61a-39c71140e152"
  thread_id: "019e6be6-532d-78b1-a61a-39c71140e152"
  agent_name: "dev-lv"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:05:20+08:00"
  completed_at: "2026-05-28T08:13:05+08:00"
  closed_at: "2026-05-28T08:16:00+08:00"
---

# META-DEV CR017-S05 Implementation Handoff

## Task

Implement `CR017-S05-validation-quality-parity-and-leakage-tests` after CR017-S02/S03/S04 are verified.

This Story is fixture-only. It must not read real lake data, legacy reports, private paths, credentials, `.env`, or provider data. It must not write real lake data, publish current pointers, overwrite legacy qfq, or touch QMT / broker APIs.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| S02 CP7 | `process/checks/CP7-CR017-S02-raw-prices-and-adj-factor-contract-hardening-VERIFICATION-DONE.md` | PASS |
| S03 CP7 | `process/checks/CP7-CR017-S03-qfq-hfq-derived-view-normalization-VERIFICATION-DONE.md` | PASS |
| S04 CP7 | `process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md` | PASS |
| S05 Story | `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests.md` | dev-ready |
| S05 LLD | `process/stories/CR017-S05-validation-quality-parity-and-leakage-tests-LLD.md` | confirmed |

## Allowed Write Scope

- `tests/test_cr017_adjustment_quality_parity.py`
- `tests/test_cr017_adjustment_leakage_gates.py`
- `market_data/validation.py`
- `market_data/quality.py` (create if absent)
- `process/checks/CP6-CR017-S05-validation-quality-parity-and-leakage-tests-CODING-DONE.md`
- Necessary status updates only for the assigned Story card.

## Forbidden Scope

- Do not implement CR017-S06, CR015, or CR016.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, or sessions.
- Do not read real lake data, legacy qfq data, old report contents, private absolute paths, or provider data.
- Do not trigger provider fetch, real lake write, catalog current pointer publish, dependency changes, or legacy qfq overwrite.
- Do not launch QMT / MiniQMT, import / call broker APIs, or create order / cancel / account paths.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, or `DEV-LOG.md`.

## Completion Criteria

| 条目 | 期望 |
|---|---|
| Quality gate | `adjustment_quality_gate()` returns structured status/reason for pass, required_missing, fail, and warning-not-production-pass cases. |
| Parity check | `check_adjustment_parity()` returns structured mismatch reason; TS-017-01/02 positive and failure scenarios are covered. |
| Leakage guard | `guard_execution_price_leakage()` blocks qfq/hfq/returns_adjusted execution price fields with `execution_requires_raw`. |
| TS matrix | `build_ts017_matrix()` maps TS-017-01..03 to stable scenario ids, each with at least one positive and one failure scenario. |
| Tests | Run `uv run --python 3.11 pytest -q tests/test_cr017_adjustment_quality_parity.py tests/test_cr017_adjustment_leakage_gates.py`. Also run CR017 related regression if shared validation code changes. |
| CP6 | Write CP6 PASS/BLOCKED file with Agent Dispatch Evidence and safety counters. |
| Safety counters | provider_fetch=0, lake_write=0, credential_read=0, current_pointer_publish=0, dependency_change=0, legacy_qfq_overwrite=0, qmt_api_call=0, real_order=0, old_report_read=0, real_lake_read=0. |

## Result

| 条目 | 结果 |
|---|---|
| Agent | `dev-lv` / `019e6be6-532d-78b1-a61a-39c71140e152` |
| Completion | `completed_at=2026-05-28T08:13:05+08:00`; `closed_at=2026-05-28T08:16:00+08:00` |
| CP6 | `process/checks/CP6-CR017-S05-validation-quality-parity-and-leakage-tests-CODING-DONE.md` PASS |
| Story status | `ready-for-verification` |
| Tests | S05 target -> `12 passed in 0.39s`; CR017 regression -> `46 passed in 0.47s`; meta-po rerun -> `46 passed in 0.48s` |
| Safety counters | provider_fetch / lake_write / credential_read / current_pointer_publish / dependency_change / legacy_qfq_overwrite / qmt_api_call / real_order / old_report_read / real_lake_read all `0` |
