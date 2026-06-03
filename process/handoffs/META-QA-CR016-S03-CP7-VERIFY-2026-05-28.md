---
handoff_id: "META-QA-CR016-S03-CP7-VERIFY-2026-05-28"
from: "meta-po"
to: "meta-qa"
change_id: "CR-016"
story_id: "CR016-S03-monitoring-heartbeat-and-kill-switch"
wave_id: "CR016-W1-SIMULATION-OPS-GATES-CP7"
status: "completed"
created_at: "2026-05-28T10:51:44+08:00"
updated_at: "2026-05-28T11:00:54+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c80-3ba9-76f3-878c-b577f342cca4"
  thread_id: "019e6c80-3ba9-76f3-878c-b577f342cca4"
  agent_name: "qa-wei the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T10:53:30+08:00"
  completed_at: "2026-05-28T10:57:35+08:00"
  closed_at: "2026-05-28T11:00:54+08:00"
---

# META-QA CR016-S03 CP7 Verification Handoff

## Task

Verify `CR016-S03-monitoring-heartbeat-and-kill-switch` after CP6 PASS. This is a fixture-only / mock-only contract verification. It must not authorize or execute real cancels, real orders, real account queries, real broker operations, broker lake writes, incident persistence, provider fetches, lake writes, publish, simulation runs, live runs, credential reads, or dependency changes.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| Story | `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch.md` | ready-for-verification |
| LLD | `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S03-monitoring-heartbeat-and-kill-switch-LLD-IMPLEMENTABILITY.md` | PASS |
| CP5 人工确认 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| CP6 | `process/checks/CP6-CR016-S03-monitoring-heartbeat-and-kill-switch-CODING-DONE.md` | PASS |
| Implementation handoff | `process/handoffs/META-DEV-CR016-S03-IMPLEMENT-2026-05-28.md` | completed |

## Allowed Write Scope

- `process/checks/CP7-CR016-S03-monitoring-heartbeat-and-kill-switch-VERIFICATION-DONE.md`

Do not update Story status to `verified`; meta-po will do that after CP7 evidence is reviewed.

## Required Verification

| TASK-ID | 要求 |
|---|---|
| CR016-S03-QA1 | 校验 CP6、Story、LLD、CP5、handoff lifecycle 和 Agent Dispatch Evidence 一致。 |
| CR016-S03-QA2 | 运行指定回归命令并记录结果。 |
| CR016-S03-QA3 | 验证 heartbeat fail、reconciliation `manual_review|kill_switch`、manual trigger、risk blocked、planned-only cancel plan、freeze 后新单 blocked、recovery gate、敏感值脱敏。 |
| CR016-S03-QA4 | 验证真实操作计数全部为 0，尤其 `real_cancel_call`、`real_broker_operation`、`incident_persisted`、`cancel_plan_executed`、`new_order_allowed_after_freeze`。 |
| CR016-S03-QA5 | 扫描本 Story 相关文件，确认没有 QMT / MiniQMT / XtQuant / broker API 调用、凭据读取、真实写 lake、publish、依赖变更、incident 持久化或真实撤单执行。 |
| CR016-S03-QA6 | 写入 CP7，包含 Agent Dispatch Evidence、测试结果、安全计数、阻断项和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_monitoring_kill_switch.py tests/test_cr015_qmt_adapter_contract.py tests/test_cr015_oms_state_machine.py tests/test_cr016_reconciliation_service_reports.py tests/test_cr016_simulation_order_enable_gate.py
```

## Forbidden Scope

- Do not modify source code, tests, docs, `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, persist incidents to a real broker lake, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.

## Safety Counters Required In CP7

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_operation=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`real_snapshot_pull=0`、`incident_persisted=0`、`cancel_plan_executed=0`、`new_order_allowed_after_freeze=0`、`sensitive_raw_value_output=0`。
