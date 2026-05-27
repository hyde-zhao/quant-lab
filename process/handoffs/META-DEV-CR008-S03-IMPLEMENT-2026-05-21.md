---
handoff_id: "META-DEV-CR008-S03-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-yang"
status: "completed"
created_at: "2026-05-21T22:37:51+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W3"
story_id: "CR008-S03-research-dataset-builder"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S03-research-dataset-builder|CR008-DEV-W3"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b3c-b66b-7de0-8e8b-cc57c61779e0"
  agent_name: "dev-xu"
  thread_id: "019e4b3c-b66b-7de0-8e8b-cc57c61779e0"
  spawned_at: "2026-05-21T23:52:14+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T00:07:17+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S03 Implementation

## 目标

按已批准的 `process/stories/CR008-S03-research-dataset-builder-LLD.md` 离线实现只读 `research_dataset_builder`，并写入 CP6。

## Entry Gate

- `CR008-S01` CP7 PASS 并已收敛为 verified。
- `CR008-S02` CP7 PASS 并已收敛为 verified。
- `CR008-BATCH-A` CP5 批次人工审查已 approved。
- 不与 S01/S04/S05/S06 并行修改 `engine/research_dataset.py`。

## 写入范围

- `engine/research_dataset.py`
- `engine/data_loader.py`
- `market_data/readers.py`
- `tests/test_cr008_research_dataset_builder.py`
- `process/checks/CP6-CR008-S03-research-dataset-builder-CODING-DONE.md`

## 禁止范围

- 不修改 connector/runtime/storage、`data/**`、旧 `reports/data_quality_report.csv`、凭据、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不触发 fetch/backfill/normalize/revalidate/replay job，不做真实 lake read/write。

## 测试与 CP6 要求

- 运行：`uv run --python 3.11 pytest -q tests/test_cr008_research_dataset_builder.py`
- 运行 S01/S02 相关回归，确认 metadata 与 benchmark 字段未回退。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- builder 只读消费 `market_data.readers` 与 benchmark resolver。
- missing / quality / policy failure 返回 typed result 与 `auto_execute=false` remediation。
- 网络、真实抓取、真实 lake、旧 data/report、凭据操作次数为 0。
