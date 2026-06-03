---
handoff_id: "META-DEV-CR016-S04-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-016"
story_id: "CR016-S04-simulation-live-runbook-and-approval-gates"
wave_id: "CR016-W1-SIMULATION-OPS-GATES"
status: "completed"
created_at: "2026-05-28T11:02:31+08:00"
updated_at: "2026-05-28T11:14:39+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c89-715f-7472-8b69-e20d1e9e4aa0"
  thread_id: "019e6c89-715f-7472-8b69-e20d1e9e4aa0"
  agent_name: "dev-qin the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T11:03:33+08:00"
  completed_at: "2026-05-28T11:10:12+08:00"
  closed_at: "2026-05-28T11:14:39+08:00"
---

# META-DEV CR016-S04 Implementation Handoff

## Task

Implement `CR016-S04-simulation-live-runbook-and-approval-gates` after CR016-S01/S02/S03 verification.

This Story creates the simulation/live runbook, per-run approval gate contract, rollback/recovery matrix, and static document tests. It does not authorize or execute simulation, live_readonly, small_live, scale_up, real broker operations, real orders, cancels, account queries, provider fetches, lake writes, publish, credential reads, or dependency changes.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR016-S04-simulation-live-runbook-and-approval-gates.md` | dev-ready |
| LLD | `process/stories/CR016-S04-simulation-live-runbook-and-approval-gates-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S04-simulation-live-runbook-and-approval-gates-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR016-S01-simulation-account-order-enable-gate-VERIFICATION-DONE.md`、`process/checks/CP7-CR016-S02-reconciliation-service-and-reports-VERIFICATION-DONE.md`、`process/checks/CP7-CR016-S03-monitoring-heartbeat-and-kill-switch-VERIFICATION-DONE.md` | PASS |
| Foundation runbook | `docs/QMT-TRADING-RUNBOOK.md` | existing CR015 foundation boundary |

## Allowed Write Scope

- `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`
- `tests/test_cr016_runbook_approval_gates.py`
- `docs/QMT-TRADING-RUNBOOK.md`
- `README.md`
- `docs/USER-MANUAL.md`
- `process/checks/CP6-CR016-S04-simulation-live-runbook-and-approval-gates-CODING-DONE.md`
- `process/stories/CR016-S04-simulation-live-runbook-and-approval-gates.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR016-S04-T1 | 创建 `docs/QMT-SIMULATION-LIVE-RUNBOOK.md`，覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复、回滚 7 类 P0 章节。 |
| CR016-S04-T2 | 文档必须声明：runbook、CP5、CP6/CP7 或 Story 状态均不自动授权真实 simulation/live/small_live/scale_up 或真实 broker 操作。 |
| CR016-S04-T3 | 写入 per-run authorization 字段表，字段至少包括 `authorization_id`、`mode`、`strategy_id`、`run_id`、`stage`、`capital_limit`、`order_scope`、`approver`、`approved_at`、`expires_at`、`rollback_plan_ref`。 |
| CR016-S04-T4 | 写入 rollback / recovery matrix，覆盖 incident type、stage、owner、action、rollback target、recovery gate。 |
| CR016-S04-T5 | 更新 `docs/QMT-TRADING-RUNBOOK.md` 增加 CR016 activation runbook 链接、simulation 准入入口和 CR015/CR016 边界。 |
| CR016-S04-T6 | 更新 `README.md` 与 `docs/USER-MANUAL.md` 增加用户入口、阶段边界和默认不授权声明。 |
| CR016-S04-T7 | 创建 `tests/test_cr016_runbook_approval_gates.py`，覆盖 7 类章节、缺 P0 章节 fail、approval 字段 100%、rollback matrix、禁止默认授权、敏感值扫描。 |
| CR016-S04-T8 | 写入 CP6，包含 Agent Dispatch Evidence、LLD consumption、测试结果、安全计数和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_runbook_approval_gates.py tests/test_cr015_foundation_runbook_boundary.py tests/test_cr016_monitoring_kill_switch.py tests/test_cr016_reconciliation_service_reports.py tests/test_cr016_simulation_order_enable_gate.py
```

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, persist incidents to a real broker lake, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.
- Do not add text that implies runbook completion, CP5, CP6, CP7, Story verified, or document presence automatically authorizes real operations.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_operation=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`live_run=0`、`small_live_run=0`、`scale_up_run=0`、`real_snapshot_pull=0`、`incident_persisted=0`、`default_real_operation_authorization_claim=0`、`sensitive_raw_value_output=0`。
