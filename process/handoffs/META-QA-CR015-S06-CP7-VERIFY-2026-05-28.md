---
handoff_id: "META-QA-CR015-S06-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-015"
story_id: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
wave_id: "CR015-W3-SHADOW-RUNBOOK-CP7"
status: "completed"
created_at: "2026-05-28T09:25:05+08:00"
updated_at: "2026-05-28T09:32:40+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c30-47c4-7972-86ff-2f9a24a743bf"
  thread_id: "019e6c30-47c4-7972-86ff-2f9a24a743bf"
  agent_name: "qa-lv the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:26:07+08:00"
  completed_at: "2026-05-28T09:28:48+08:00"
  closed_at: "2026-05-28T09:32:40+08:00"
---

# META-QA CR015-S06 CP7 Verification Handoff

## Task

Verify `CR015-S06-target-portfolio-to-order-intent-shadow-mode` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR015-S06-IMPLEMENT-2026-05-28.md` | completed |
| S06 CP6 | `process/checks/CP6-CR015-S06-target-portfolio-to-order-intent-shadow-mode-CODING-DONE.md` | PASS |
| S06 Story | `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md` | ready-for-verification |
| S06 LLD | `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD.md` | confirmed |
| 上游 CP7 | `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md` | PASS |

## Verification Scope

Read / execute:

- `trading/shadow_pipeline.py`
- `trading/oms.py`
- `trading/pretrade_risk.py`
- `trading/broker_lake.py`
- `tests/test_cr015_shadow_order_intent_pipeline.py`
- `tests/test_cr015_oms_state_machine.py`
- `tests/test_cr015_pretrade_risk_gate.py`
- `tests/test_cr015_broker_lake_schema_writer.py`
- `process/checks/CP6-CR015-S06-target-portfolio-to-order-intent-shadow-mode-CODING-DONE.md`
- `process/handoffs/META-DEV-CR015-S06-IMPLEMENT-2026-05-28.md`
- `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md`
- `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD.md`

Write only:

- `process/checks/CP7-CR015-S06-target-portfolio-to-order-intent-shadow-mode-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence and completed dev handoff lifecycle. |
| Tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr015_broker_lake_schema_writer.py tests/test_cr015_shadow_order_intent_pipeline.py`. |
| Four artifacts | Verify `shadow_run()` outputs order intents, risk results / transitions, mock broker events where allowed, and broker lake dry-run plans. |
| Mode gate | Verify only `shadow` / `dry_run` / `mock` pass; `simulation` / `live_readonly` / `small_live` / `scale_up` are blocked with `activation_mode_pass_count=0`. |
| Raw execution policy | Verify policy metadata requires `execution_price_policy=raw`; non-raw execution policy is blocked with `non_raw_execution_pass_count=0`. |
| Risk blocked path | Verify risk fail does not call adapter, does not generate mock broker event, and keeps `adapter_calls_on_block=0`. |
| Broker lake dry-run only | Verify broker lake plan does not open paths, mkdir, write files, or touch real broker lake root; `real_broker_lake_write=0`. |
| Upstream compatibility | Confirm S03 OMS, S04 pre-trade risk, and S05 broker lake semantics did not regress. |
| Safety scan | Confirm all QMT/broker/order/cancel/account/credential/lake/provider/publish/dependency/activation/non-raw counters are 0. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters, and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR015-S07 or CR016.
- Do not launch QMT / MiniQMT / GUI apps or import / call real broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, real broker lake roots, real positions, or real account snapshots.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, current pointer publish, simulation, live_readonly, small_live, or scale_up activation.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`adapter_calls_on_block=0`、`non_raw_execution_pass_count=0`、`activation_mode_pass_count=0`。
