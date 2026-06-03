---
handoff_id: "META-DEV-CR015-S06-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S06-target-portfolio-to-order-intent-shadow-mode"
wave_id: "CR015-W3-SHADOW-RUNBOOK"
status: "completed"
created_at: "2026-05-28T09:12:34+08:00"
updated_at: "2026-05-28T09:24:30+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c24-a307-73a2-9354-2039863031f9"
  thread_id: "019e6c24-a307-73a2-9354-2039863031f9"
  agent_name: "dev-you the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T09:13:25+08:00"
  completed_at: "2026-05-28T09:20:54+08:00"
  closed_at: "2026-05-28T09:24:30+08:00"
---

# META-DEV CR015-S06 Implementation Handoff

## Task

Implement `CR015-S06-target-portfolio-to-order-intent-shadow-mode` after CR015-S03/S04/S05 and CR017-S04 verification.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md` | dev-ready |
| LLD | `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR015-S06-target-portfolio-to-order-intent-shadow-mode-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/shadow_pipeline.py`
- `trading/oms.py`
- `trading/pretrade_risk.py`
- `trading/broker_lake.py`
- `tests/test_cr015_shadow_order_intent_pipeline.py`
- `process/checks/CP6-CR015-S06-target-portfolio-to-order-intent-shadow-mode-CODING-DONE.md`
- `process/stories/CR015-S06-target-portfolio-to-order-intent-shadow-mode.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR015-S06-T1 | 创建 `shadow_run()` 编排，将 target portfolio + policy metadata + fixture snapshots 串联为 order intent、risk result、mock event/state transition、broker lake dry-run plan 四类结果。 |
| CR015-S06-T2 | 输入 mode 仅允许 shadow / dry_run / mock；simulation/live_readonly/small_live/scale_up 必须 blocked。 |
| CR015-S06-T3 | policy metadata 必须包含 research policy、view/source/quality 和 `execution_price_policy=raw`；非 raw policy 通过次数为 0。 |
| CR015-S06-T4 | risk fail 时 `adapter_calls=0`，不得生成 mock broker event；仍输出 blocked audit summary 和 dry-run audit evidence。 |
| CR015-S06-T5 | broker lake 只输出 dry-run plan，`real_broker_lake_write=0`，不得写文件或真实 root。 |
| CR015-S06-T6 | 尽量复用 S03/S04/S05 合同；若修改共享文件，只做 result shape / summary helper，对 S03/S04/S05 回归必须通过。 |
| CR015-S06-T7 | 写入 CP6，包含 Agent Dispatch Evidence、测试结果、LLD consumption、safety counters 和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr015_broker_lake_schema_writer.py tests/test_cr015_shadow_order_intent_pipeline.py
```

## Forbidden Scope

- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, real account snapshots, or real broker lake roots.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, simulation/live activation, CR015-S07, or CR016.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`adapter_calls_on_block=0`、`non_raw_execution_pass_count=0`、`activation_mode_pass_count=0`。
