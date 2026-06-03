---
handoff_id: "META-DEV-CR016-S02-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-016"
story_id: "CR016-S02-reconciliation-service-and-reports"
wave_id: "CR016-W1-SIMULATION-OPS-GATES"
status: "completed"
created_at: "2026-05-28T10:15:45+08:00"
updated_at: "2026-05-28T10:28:33+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c5e-da6a-71c2-a7ef-71f49245c2e7"
  thread_id: "019e6c5e-da6a-71c2-a7ef-71f49245c2e7"
  agent_name: "dev-yang the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T10:18:52+08:00"
  completed_at: "2026-05-28T10:24:30+08:00"
  closed_at: "2026-05-28T10:28:33+08:00"
---

# META-DEV CR016-S02 Implementation Handoff

## Task

Implement `CR016-S02-reconciliation-service-and-reports` after CR015-S03/S05 and CR016-S01 verification.

This Story creates fixture-only reconciliation contracts and versioned report candidates. It does not authorize or execute real account queries, real broker snapshot pulls, real broker lake writes, old report overwrites, real orders, cancels, simulation runs, live runs, provider fetches, lake writes, publish, or dependency changes.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR016-S02-reconciliation-service-and-reports.md` | dev-ready |
| LLD | `process/stories/CR016-S02-reconciliation-service-and-reports-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S02-reconciliation-service-and-reports-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md`、`process/checks/CP7-CR016-S01-simulation-account-order-enable-gate-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/reconciliation.py`
- `trading/broker_lake.py`
- `trading/oms.py`
- `tests/test_cr016_reconciliation_service_reports.py`
- `process/checks/CP6-CR016-S02-reconciliation-service-and-reports-CODING-DONE.md`
- `process/stories/CR016-S02-reconciliation-service-and-reports.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR016-S02-T1 | 创建 `trading/reconciliation.py`，定义 `ReconPhase`、`ReconciliationInput`、`DiffRow`、`ThresholdConfig`、`ReconciliationReport`、`reconcile()`、`evaluate_thresholds()`、`build_report_candidate()`、`to_kill_switch_candidate()`。 |
| CR016-S02-T2 | 支持 `pre_market`、`intraday`、`post_market` 三阶段；输入只接受 fixture / mock facts / 后续授权脱敏 snapshot ref，不主动查询真实账户。 |
| CR016-S02-T3 | 对账维度覆盖委托、成交、持仓、资产、现金和 broker lake facts；report 字段覆盖 `report_id`、`schema_version`、`phase`、`broker_snapshot_ref`、`local_state_ref`、`broker_lake_ref`、`diff_rows`、`thresholds`、`owner`、`action`、`status`、`redaction_status`。 |
| CR016-S02-T4 | 阈值结果映射为 `pass|warn|manual_review|kill_switch|required_missing`；任何 required_missing / manual_review / kill_switch 必须 `new_order_allowed=false`，继续下单 allowed 次数为 0。 |
| CR016-S02-T5 | 缺 broker facts 或缺阈值时返回稳定错误枚举：`broker_facts_required_missing` / `threshold_required_missing`，不得主动查询真实账户。 |
| CR016-S02-T6 | 报告必须是 versioned candidate，不覆盖 `reports/**` 旧基线，不写文件；如需要路径字段只能使用 label / ref / candidate id。 |
| CR016-S02-T7 | 如修改 `trading/broker_lake.py` / `trading/oms.py`，只新增只读 facts / snapshot contract helper，不改变 S03/S05 已验证状态机、schema、dry-run writer 行为。 |
| CR016-S02-T8 | 创建 `tests/test_cr016_reconciliation_service_reports.py` 覆盖三阶段、阈值、manual_review、kill_switch、缺 facts、缺 thresholds、report candidate 不覆盖、敏感字段和真实操作计数为 0。 |
| CR016-S02-T9 | 写入 CP6，包含 Agent Dispatch Evidence、LLD consumption、测试结果、安全计数和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_reconciliation_service_reports.py tests/test_cr015_oms_state_machine.py tests/test_cr015_broker_lake_schema_writer.py tests/test_cr016_simulation_order_enable_gate.py
```

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S03/S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not query a real account, pull real broker snapshots, write real broker lake data, overwrite old reports, run provider fetch, write real lake data, publish current pointer, place real orders, cancel real orders, run simulation, live_readonly, small_live, scale_up, or any activation side effect.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`real_snapshot_pull=0`、`old_report_overwrite=0`、`continue_order_allowed_after_threshold_breach=0`、`sensitive_raw_value_output=0`。
