---
handoff_id: "META-QA-CR016-S02-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-016"
story_id: "CR016-S02-reconciliation-service-and-reports"
wave_id: "CR016-W1-SIMULATION-OPS-GATES-CP7"
status: "completed"
created_at: "2026-05-28T10:28:33+08:00"
updated_at: "2026-05-28T10:37:45+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c6b-0c7e-7183-988f-251715d88a47"
  thread_id: "019e6c6b-0c7e-7183-988f-251715d88a47"
  agent_name: "qa-cao the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T10:30:23+08:00"
  completed_at: "2026-05-28T10:32:35+08:00"
  closed_at: "2026-05-28T10:37:45+08:00"
---

# META-QA CR016-S02 CP7 Verification Handoff

## Task

Verify `CR016-S02-reconciliation-service-and-reports` after CP6 PASS. This is a fixture-only / mock-only contract verification. It must not authorize or execute real account queries, real broker snapshot pulls, real broker lake writes, old report overwrites, real orders, cancels, simulation runs, live runs, provider fetches, lake writes, publish, credential reads, or dependency changes.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR016-S02-reconciliation-service-and-reports.md` | ready-for-verification |
| LLD | `process/stories/CR016-S02-reconciliation-service-and-reports-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S02-reconciliation-service-and-reports-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 人工确认 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| CP6 | `process/checks/CP6-CR016-S02-reconciliation-service-and-reports-CODING-DONE.md` | PASS |
| Implementation handoff | `process/handoffs/META-DEV-CR016-S02-IMPLEMENT-2026-05-28.md` | completed |

## Allowed Write Scope

- `process/checks/CP7-CR016-S02-reconciliation-service-and-reports-VERIFICATION-DONE.md`

Do not update Story status to `verified`; meta-po will do that after CP7 evidence is reviewed.

## Required Verification

| TASK-ID | 要求 |
|---|---|
| CR016-S02-QA1 | 校验 CP6、Story、LLD、CP5、handoff lifecycle 和 Agent Dispatch Evidence 一致。 |
| CR016-S02-QA2 | 运行指定回归命令并记录结果。 |
| CR016-S02-QA3 | 验证三阶段、阈值状态、required_missing、manual_review、kill_switch、report candidate 不写文件、敏感值不输出。 |
| CR016-S02-QA4 | 验证真实操作计数全部为 0，尤其 `account_query_call`、`real_snapshot_pull`、`real_broker_lake_write`、`old_report_overwrite`、`simulation_run`。 |
| CR016-S02-QA5 | 扫描本 Story 相关文件，确认没有 QMT / MiniQMT / XtQuant / broker API 调用、凭据读取、真实写 lake、publish、依赖变更或 `reports/**` 覆盖。 |
| CR016-S02-QA6 | 写入 CP7，包含 Agent Dispatch Evidence、测试结果、安全计数、阻断项和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_reconciliation_service_reports.py tests/test_cr015_oms_state_machine.py tests/test_cr015_broker_lake_schema_writer.py tests/test_cr016_simulation_order_enable_gate.py
```

## Forbidden Scope

- Do not modify source code, tests, docs, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S03/S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`real_snapshot_pull=0`、`old_report_overwrite=0`、`continue_order_allowed_after_threshold_breach=0`、`sensitive_raw_value_output=0`。
