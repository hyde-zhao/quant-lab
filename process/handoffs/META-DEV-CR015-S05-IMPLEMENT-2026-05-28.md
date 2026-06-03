---
handoff_id: "META-DEV-CR015-S05-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S05-broker-lake-schema-and-writer"
wave_id: "CR015-W2-OMS-RISK-LAKE"
status: "completed"
created_at: "2026-05-28T08:52:35+08:00"
updated_at: "2026-05-28T09:04:29+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6c12-451b-73e0-9621-09c8750e6b81"
  thread_id: "019e6c12-451b-73e0-9621-09c8750e6b81"
  agent_name: "dev-he the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:53:21+08:00"
  completed_at: "2026-05-28T09:01:08+08:00"
  closed_at: "2026-05-28T09:04:29+08:00"
---

# META-DEV CR015-S05 Implementation Handoff

## Task

Implement `CR015-S05-broker-lake-schema-and-writer` after CR015-S03/S04 verification.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR015-S05-broker-lake-schema-and-writer.md` | dev-ready |
| LLD | `process/stories/CR015-S05-broker-lake-schema-and-writer-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR015-S05-broker-lake-schema-and-writer-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/broker_lake.py`
- `trading/oms.py`
- `tests/test_cr015_broker_lake_schema_writer.py`
- `process/checks/CP6-CR015-S05-broker-lake-schema-and-writer-CODING-DONE.md`
- `process/stories/CR015-S05-broker-lake-schema-and-writer.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR015-S05-T1 | 创建 broker lake schema registry，覆盖 `order_intent`、`broker_order`、`fill`、`position`、`asset`、`error`、`reconciliation`、`incident` 八类对象。 |
| CR015-S05-T2 | 创建 redaction gate，敏感字段和敏感值必须 blocked 或脱敏；敏感原值输出次数为 0。 |
| CR015-S05-T3 | 创建 `dry_run_write_plan()`，只输出 root label、schema_version、partition、retention_policy、redaction_status，不打开真实路径、不写文件。 |
| CR015-S05-T4 | 禁止写入仓库 `data/**` / `reports/**` 和真实 broker lake root；真实 broker lake write 必须保持 0。 |
| CR015-S05-T5 | 在 `trading/oms.py` 仅增加 S05 需要的 intent / transition event dict 输出，不改变 S03/S04 状态机和风控语义。 |
| CR015-S05-T6 | 写入 CP6，包含 Agent Dispatch Evidence、测试结果、LLD consumption、safety counters 和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py tests/test_cr015_broker_lake_schema_writer.py
```

## Forbidden Scope

- Do not modify `trading/pretrade_risk.py` or `tests/test_cr015_pretrade_risk_gate.py` unless absolutely necessary for compatibility; prefer preserving S04 unchanged and prove via regression.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key files, or real broker lake root values.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, simulation/live activation, CR015-S06/S07, or CR016.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`open_write_call=0`、`sensitive_raw_value_output=0`。
