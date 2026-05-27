---
handoff_id: "META-DEV-CR008-S05-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-shi"
status: "completed"
created_at: "2026-05-21T22:37:51+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W4B"
story_id: "CR008-S05-pit-universe-consumption-contract"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S05-pit-universe-consumption-contract|CR008-DEV-W4B"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b9e-e3e8-7260-93dc-e64fb31e40b1"
  agent_name: "dev-qin the 2nd"
  thread_id: "019e4b9e-e3e8-7260-93dc-e64fb31e40b1"
  spawned_at: "2026-05-22T01:39:29+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T01:49:22+08:00"
  evidence: "CR007-S03 CP7 PASS 后，主线程通过 spawn_agent 真实调度 meta-dev/dev-qin the 2nd 执行 CR008-S05 离线实现；CP6 已由子 agent 写入并 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S05 Implementation

## 目标

按已批准的 `process/stories/CR008-S05-pit-universe-consumption-contract-LLD.md` 离线实现 PIT / fixed universe 消费合同，并写入 CP6。

## Entry Gate

- `CR008-S03` 已 CP7 PASS，`CR008-S04` 已 CP7 PASS。
- `CR007-S03-index-members-stock-basic-datasets` 已完成离线实现与 CP7 验证；S05 消费其 readiness / PIT contract，且当前无并行 dev/qa 抢占 `market_data/readers.py`。
- CR008 优先于 CR007 冲突；本次仅解锁 CR007-S03 作为 S05 必要前置，不启动 CR007-S04/S05。

## 写入范围

- `engine/universe.py`
- `engine/research_dataset.py`
- `market_data/readers.py`
- `tests/test_cr008_pit_universe_contract.py`
- `process/checks/CP6-CR008-S05-pit-universe-consumption-contract-CODING-DONE.md`

## 禁止范围

- 不修改 connector/runtime/storage、`data/**`、旧 `reports/data_quality_report.csv`、凭据、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不联网、不真实 Tushare fetch、不真实 lake read/write，不执行补数或 replay job。

## 测试与 CP6 要求

- 运行：`uv run --python 3.11 pytest -q tests/test_cr008_pit_universe_contract.py`
- 运行 S03/S04 相关回归。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- PIT / fixed snapshot 明确区分；fixed snapshot 必须写 survivorship warning。
- 严肃研究要求 PIT 时，不可用必须 fail，不得伪装 PIT。
