---
handoff_id: "META-DEV-CR016-S03-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-016"
story_id: "CR016-S03-monitoring-heartbeat-and-kill-switch"
wave_id: "CR016-W1-SIMULATION-OPS-GATES"
status: "completed"
created_at: "2026-05-28T10:39:32+08:00"
updated_at: "2026-05-28T10:51:44+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c74-54ef-7cb2-ac70-163c253c785a"
  thread_id: "019e6c74-54ef-7cb2-ac70-163c253c785a"
  agent_name: "dev-xu the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T10:40:29+08:00"
  completed_at: "2026-05-28T10:48:35+08:00"
  closed_at: "2026-05-28T10:51:44+08:00"
---

# META-DEV CR016-S03 Implementation Handoff

## Task

Implement `CR016-S03-monitoring-heartbeat-and-kill-switch` after CR015-S02/S03 and CR016-S02 verification.

This Story creates fixture-only monitoring heartbeat, kill switch, cancel plan, incident candidate, and recovery gate contracts. It does not authorize or execute real cancels, real orders, real account queries, real broker operations, broker lake writes, incident persistence, provider fetches, lake writes, publish, simulation runs, live runs, credential reads, or dependency changes.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch.md` | dev-ready |
| LLD | `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S03-monitoring-heartbeat-and-kill-switch-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR016-S02-reconciliation-service-and-reports-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/monitoring.py`
- `trading/kill_switch.py`
- `trading/oms.py`
- `trading/qmt_adapter.py`
- `tests/test_cr016_monitoring_kill_switch.py`
- `process/checks/CP6-CR016-S03-monitoring-heartbeat-and-kill-switch-CODING-DONE.md`
- `process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR016-S03-T1 | 创建 `trading/monitoring.py`，定义 heartbeat event、deadline policy、heartbeat status、incident candidate 和 `heartbeat_check()`。 |
| CR016-S03-T2 | 创建 `trading/kill_switch.py`，定义 `KillSwitchReason`、`KillSwitchRequest`、`CancelPlan`、`IncidentCandidate`、`KillSwitchResult`、`build_cancel_plan()`、`kill_switch_trigger()`、`recovery_gate()`。 |
| CR016-S03-T3 | heartbeat 失败、reconciliation `manual_review|kill_switch`、manual trigger、risk blocked 均能触发 `stop_new_orders=true`、`freeze_status=frozen`、`cancel_plan_status=planned_only`、incident candidate 和 recovery gate。 |
| CR016-S03-T4 | cancel plan 只输出 refs / owner / action，不执行真实撤单；`requires_authorization=true`，`real_cancel_call=0`。 |
| CR016-S03-T5 | recovery gate 必须同时要求 `reconciliation_status=pass` 和 `manual_takeover_status=recorded`，缺任一项返回 blocked。 |
| CR016-S03-T6 | incident / result 不输出账号、token、password、cookie、session、private key、真实 broker root 或真实持仓等敏感原值。 |
| CR016-S03-T7 | 如修改 `trading/oms.py` / `trading/qmt_adapter.py`，只能新增只读 open state / cancel plan 前置合同，不改变 CR015-S02/S03 已验证行为，不调用真实 QMT / broker API。 |
| CR016-S03-T8 | 创建 `tests/test_cr016_monitoring_kill_switch.py` 覆盖 heartbeat fail、recon diff、cancel plan planned-only、manual trigger、freeze 后新单 blocked、recovery 缺人工接管 blocked、incident 敏感值扫描、真实操作计数全 0。 |
| CR016-S03-T9 | 写入 CP6，包含 Agent Dispatch Evidence、LLD consumption、测试结果、安全计数和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_monitoring_kill_switch.py tests/test_cr015_qmt_adapter_contract.py tests/test_cr015_oms_state_machine.py tests/test_cr016_reconciliation_service_reports.py tests/test_cr016_simulation_order_enable_gate.py
```

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, persist incidents to a real broker lake, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_operation=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`real_snapshot_pull=0`、`incident_persisted=0`、`cancel_plan_executed=0`、`new_order_allowed_after_freeze=0`、`sensitive_raw_value_output=0`。
