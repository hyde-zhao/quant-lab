---
handoff_id: "META-DEV-CR016-S01-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-016"
story_id: "CR016-S01-simulation-account-order-enable-gate"
wave_id: "CR016-W1-SIMULATION-OPS-GATES"
status: "completed"
created_at: "2026-05-28T09:55:42+08:00"
updated_at: "2026-05-28T10:07:43+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c4c-4259-7841-8741-9cc533d26950"
  thread_id: "019e6c4c-4259-7841-8741-9cc533d26950"
  agent_name: "dev-zhang the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:56:41+08:00"
  completed_at: "2026-05-28T10:03:34+08:00"
  closed_at: "2026-05-28T10:07:43+08:00"
---

# META-DEV CR016-S01 Implementation Handoff

## Task

Implement `CR016-S01-simulation-account-order-enable-gate` after CR015 foundation and CR017-S06 verification.

This Story creates an offline stage gate contract only. It does not authorize or execute any simulation run, QMT / MiniQMT operation, real order, cancel, account query, credential read, broker lake write, provider fetch, lake write, publish, or dependency change.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR016-S01-simulation-account-order-enable-gate.md` | dev-ready |
| LLD | `process/stories/CR016-S01-simulation-account-order-enable-gate-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR016-S01-simulation-account-order-enable-gate-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S07-docs-and-foundation-runbook-boundary-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/stage_gate.py`
- `trading/qmt_adapter.py`
- `docs/QMT-TRADING-RUNBOOK.md`
- `tests/test_cr016_simulation_order_enable_gate.py`
- `process/checks/CP6-CR016-S01-simulation-account-order-enable-gate-CODING-DONE.md`
- `process/stories/CR016-S01-simulation-account-order-enable-gate.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR016-S01-T1 | 创建 `trading/stage_gate.py`，定义 `Stage`、`StageGateRequest`、`AuthorizationSummary`、`StageEvidence`、`StageGateResult`、`evaluate_stage_gate()`、`simulation_order_enable()`、`validate_authorization_summary()`。 |
| CR016-S01-T2 | 固定阶段顺序 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，跳阶段 100% blocked，blocked reason 使用稳定枚举。 |
| CR016-S01-T3 | simulation gate 必须校验 CR015 verified、runbook ref、CR017 consumer boundary ref、reconciliation policy ref、kill switch readiness ref 和 per-run authorization summary。 |
| CR016-S01-T4 | per-run authorization 必需字段覆盖 `authorization_id`、`mode`、`strategy_id`、`run_id`、`target_stage`、`target_trade_date`、`capital_limit`、`order_scope`、`approver`、`approved_at`、`expires_at`、`rollback_plan_ref`；字段缺失时 blocked。 |
| CR016-S01-T5 | `simulation_order_enable()` 只能消费 gate result，gate 不通过时 adapter/order/cancel/account/credential/lake/provider/publish/dependency 相关计数全部保持 0。 |
| CR016-S01-T6 | 如修改 `trading/qmt_adapter.py`，只能新增 gate result 前置检查入口，不得导入或调用真实 QMT / XtQuant / broker API，不得改变 CR015 shadow/dry-run/mock 行为。 |
| CR016-S01-T7 | 更新 `docs/QMT-TRADING-RUNBOOK.md`，补充 simulation 准入 checklist、per-run authorization 字段和“runbook 不等于授权”。 |
| CR016-S01-T8 | 创建 `tests/test_cr016_simulation_order_enable_gate.py` 覆盖合法 `shadow -> simulation`、跳阶段、缺授权、CR015 未 verified、缺 runbook/recon/kill switch、blocked adapter 前置、CR017 未 verified 时 scale_up blocked。 |
| CR016-S01-T9 | 写入 CP6，包含 Agent Dispatch Evidence、LLD consumption、测试结果、安全计数和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr016_simulation_order_enable_gate.py tests/test_cr015_qmt_adapter_contract.py
```

If `trading/qmt_adapter.py` is not modified, still run the same command to prove adapter compatibility.

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not implement CR016-S02/S03/S04/S05/S06/S07.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, real positions, or real broker lake roots.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, simulation run, live_readonly, small_live, scale_up, or any activation side effect.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`simulation_run=0`、`live_activation=0`、`adapter_call_on_block=0`、`scale_up_allowed_without_cr017=0`。
