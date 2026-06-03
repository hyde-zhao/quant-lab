---
handoff_id: "META-DEV-CR015-S04-IMPLEMENT-2026-05-28"
from: "meta-po"
to: "meta-dev"
change_id: "CR-015"
story_id: "CR015-S04-pretrade-risk-gate"
wave_id: "CR015-W2-OMS-RISK-LAKE"
status: "completed"
created_at: "2026-05-28T08:25:16+08:00"
updated_at: "2026-05-28T08:40:12+08:00"
dispatch:
  mode: "spawn_agent"
  agent_id: "019e6bfc-34e1-7c93-9358-1b97db2cb08a"
  thread_id: "019e6bfc-34e1-7c93-9358-1b97db2cb08a"
  agent_name: "dev-shi the 2nd"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-05-28T08:29:17+08:00"
  completed_at: "2026-05-28T08:36:38+08:00"
  closed_at: "2026-05-28T08:40:12+08:00"
---

# META-DEV CR015-S04 Implementation Handoff

## Task

Implement `CR015-S04-pretrade-risk-gate` after CR015-S03, CR017-S02 and CR017-S04 verification.

## Inputs

| 类型 | 路径 | 状态 |
|---|---|---|
| CP5 人工审查 | `checkpoints/CP5-CR015-CR016-CR017-ALL-STORIES-LLD-BATCH.md` | approved |
| Story | `process/stories/CR015-S04-pretrade-risk-gate.md` | dev-ready |
| LLD | `process/stories/CR015-S04-pretrade-risk-gate-LLD.md` | confirmed |
| CP5 自动预检 | `process/checks/CP5-CR015-S04-pretrade-risk-gate-LLD-IMPLEMENTABILITY.md` | PASS |
| 上游 CP7 | `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md`、`process/checks/CP7-CR017-S04-reader-api-and-policy-gates-VERIFICATION-DONE.md` | PASS |

## Allowed Write Scope

- `trading/pretrade_risk.py`
- `trading/oms.py`
- `tests/test_cr015_pretrade_risk_gate.py`
- `process/checks/CP6-CR015-S04-pretrade-risk-gate-CODING-DONE.md`
- `process/stories/CR015-S04-pretrade-risk-gate.md`

## Required Implementation

| TASK-ID | 要求 |
|---|---|
| CR015-S04-T1 | 创建九类 ADR-058 风控规则、fixture / 脱敏 snapshot 输入、risk profile、blocked result 和 adapter_calls=0 hard block 合同。 |
| CR015-S04-T2 | 覆盖现金、100 股整手、T+1 可卖、可用持仓、价格口径、重复 intent、单票限额、组合限额、异常价格。 |
| CR015-S04-T3 | 在 `trading/oms.py` 仅做 S04 需要的 risk result 接入，不改变 S03 状态迁移语义。 |
| CR015-S04-T4 | 创建离线测试，证明任一风控失败 adapter_calls=0，非 raw/qfq/hfq execution blocked，真实账户查询/凭据/真实发单计数为 0。 |
| CR015-S04-T5 | 写入 CP6，包含 Agent Dispatch Evidence、测试结果、LLD consumption、safety counters 和 PASS/FAIL 结论。 |

## Verification Command

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py tests/test_cr015_pretrade_risk_gate.py
```

## Forbidden Scope

- Do not modify `trading/broker_lake.py` or `tests/test_cr015_broker_lake_schema_writer.py`; CR015-S05 is serialized because it also shares `trading/oms.py`.
- Do not modify `pyproject.toml`, `uv.lock`, `data/**`, `reports/**`, `delivery/**`, `DEV-LOG.md`, credentials, tokens, or secret values.
- Do not launch QMT / MiniQMT / GUI apps or call broker APIs.
- Do not read `.env`, token, password, cookie, session, account, holdings, or private key files.
- Do not run provider fetch, real lake write, real broker lake write, current pointer publish, real order, real cancel, account query, dependency change, or simulation/live activation.
- Do not implement CR015-S05/S06/S07 or CR016.

## Safety Counters Required In CP6

`qmt_api_call=0`、`real_order_call=0`、`real_cancel_call=0`、`account_query_call=0`、`account_write_call=0`、`credential_read=0`、`real_broker_lake_write=0`、`real_lake_write=0`、`provider_fetch=0`、`publish=0`、`dependency_change=0`、`adapter_calls_on_block=0`。
