---
handoff_id: "META-DEV-CR008-S06-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-xu the 2nd"
status: "completed"
created_at: "2026-05-21T22:37:51+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W6"
story_id: "CR008-S06-factor-research-auxiliary-data-contract"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S06-factor-research-auxiliary-data-contract|CR008-DEV-W6"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4c3c-329d-78c3-acbc-722cdac3d1af"
  agent_name: "dev-xu the 2nd"
  thread_id: "019e4c3c-329d-78c3-acbc-722cdac3d1af"
  spawned_at: "2026-05-22T04:31:18+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T04:41:52+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-dev/dev-xu the 2nd 执行 CR008-S06 离线实现；CP6 已由子 agent 写入并 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S06 Implementation

## 目标

按已批准的 `process/stories/CR008-S06-factor-research-auxiliary-data-contract-LLD.md` 离线实现因子研究辅助数据 availability / allowed claims 合同，并写入 CP6。

## Entry Gate

- `CR008-S03`、`CR008-S04` 与 `CR008-S05` 均已 CP7 PASS；PIT/fixed universe 合同已冻结。
- 不与 S01/S02/S03/S04/S05 并行修改 `engine/research_dataset.py`、`market_data/readers.py` 或 `experiments/run_experiment_15_factor_framework.py`。

## 写入范围

- `engine/research_dataset.py`
- `market_data/readers.py`
- `experiments/run_experiment_15_factor_framework.py`
- `tests/test_cr008_factor_auxiliary_data_contract.py`
- `process/checks/CP6-CR008-S06-factor-research-auxiliary-data-contract-CODING-DONE.md`

## 禁止范围

- 不修改 connector/runtime/storage、`data/**`、旧 `reports/data_quality_report.csv`、凭据、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不联网、不真实 Tushare fetch、不真实 lake read/write，不新增真实行业/市值/风格暴露数据生产。

## 测试与 CP6 要求

- 运行：`uv run --python 3.11 pytest -q tests/test_cr008_factor_auxiliary_data_contract.py`
- 运行 S03/S04/S05 与 experiment 15 相关回归。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- 缺行业、市值、可交易性、风格暴露、复权审计或容量数据时，对应严肃 claims 输出次数为 0。
- `known_limitations` 和 `blocked_claims` 原因覆盖 100%。
