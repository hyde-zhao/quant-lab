---
handoff_id: "META-QA-CR015-S05-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-015"
story_id: "CR015-S05-broker-lake-schema-and-writer"
wave_id: "CR015-W2-OMS-RISK-LAKE-CP7"
status: "completed"
created_at: "2026-05-28T09:05:07+08:00"
updated_at: "2026-05-28T09:11:25+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c1d-ab63-7130-98a8-ecf802425771"
  thread_id: "019e6c1d-ab63-7130-98a8-ecf802425771"
  agent_name: "qa-kong the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:05:47+08:00"
  completed_at: "2026-05-28T09:07:31+08:00"
  closed_at: "2026-05-28T09:11:25+08:00"
---

# META-QA CR015-S05 CP7 Verification Handoff

## Task

Verify `CR015-S05-broker-lake-schema-and-writer` after CP6 PASS.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Dev handoff | `process/handoffs/META-DEV-CR015-S05-IMPLEMENT-2026-05-28.md` | completed |
| S05 CP6 | `process/checks/CP6-CR015-S05-broker-lake-schema-and-writer-CODING-DONE.md` | PASS |
| S05 Story | `process/stories/CR015-S05-broker-lake-schema-and-writer.md` | ready-for-verification |
| S05 LLD | `process/stories/CR015-S05-broker-lake-schema-and-writer-LLD.md` | confirmed |

## Verification Scope

Read / execute:

- `trading/broker_lake.py`
- `trading/oms.py`
- `tests/test_cr015_broker_lake_schema_writer.py`
- `tests/test_cr015_oms_state_machine.py`
- `tests/test_cr015_pretrade_risk_gate.py`
- `process/checks/CP6-CR015-S05-broker-lake-schema-and-writer-CODING-DONE.md`
- `process/handoffs/META-DEV-CR015-S05-IMPLEMENT-2026-05-28.md`
- `process/stories/CR015-S05-broker-lake-schema-and-writer.md`
- `process/stories/CR015-S05-broker-lake-schema-and-writer-LLD.md`

Write only:

- `process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md`

## Required Verification

| 条目 | 期望 |
|---|---|
| CP6 evidence | CP6 exists, status PASS, with spawn_agent Agent Dispatch Evidence. |
| Tests | Run `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr015_broker_lake_schema_writer.py`. |
| Schema coverage | Verify 8 broker lake event types: order_intent, broker_order, fill, position, asset, error, reconciliation, incident. |
| Schema contract | Verify schema_version, required_fields, partition_keys, retention_policy and redaction_status contract for every event type. |
| Dry-run only | Verify dry_run_write_plan does not open paths, mkdir, write files or real broker lake root; real_write=false. |
| Redaction | Verify token/password/account/session/cookie/.env/private path raw values are redacted or blocked and sensitive_raw_value_output=0. |
| Forbidden targets | Verify repository data/** and reports/** targets are blocked and raw path previews are not leaked. |
| OMS compatibility | Confirm S03 state transition and S04 risk gate semantics were not changed. |
| Safety scan | Confirm all QMT/broker/order/cancel/account/credential/lake/provider/publish/dependency/open-write counters are 0. |
| CP7 | Write CP7 result with Agent Dispatch Evidence, LLD consumption evidence, test results, safety counters and PASS/FAIL conclusion. |

## Forbidden Scope

- Do not modify product code, tests, Story cards, CP6 files, LLD files, handoff files, `DEV-LOG.md`, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, or `delivery/**`.
- Do not implement CR015-S06/S07 or CR016.
- Do not launch QMT / MiniQMT / GUI apps or import / call real broker APIs.
- Do not read credentials, `.env`, tokens, passwords, private keys, cookies, sessions, accounts, holdings, real broker lake roots, or real positions.
- Do not trigger provider fetch, real lake write, real broker lake write, real order, real cancel, account query, dependency changes, current pointer publish, simulation or live activation.
