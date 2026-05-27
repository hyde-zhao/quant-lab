---
handoff_id: "META-DEV-CR008-S04-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-qin"
status: "completed"
created_at: "2026-05-21T22:37:51+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W4A"
story_id: "CR008-S04-quality-adjustment-label-window-gates"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S04-quality-adjustment-label-window-gates|CR008-DEV-W4A"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b63-d14a-7012-b9c7-6145194f5e12"
  agent_name: "dev-shi the 2nd"
  thread_id: "019e4b63-d14a-7012-b9c7-6145194f5e12"
  spawned_at: "2026-05-22T00:34:57+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T00:40:34+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
previous_dispatches:
  - status: "stalled-closed-no-output"
    mode: "spawn_agent"
    platform: "codex"
    tool_name: "spawn_agent"
    agent_role: "meta-dev"
    agent_id: "019e4b51-bd69-7d63-ae69-69bd49288bbe"
    agent_name: "dev-zhang the 2nd"
    thread_id: "019e4b51-bd69-7d63-ae69-69bd49288bbe"
    spawned_at: "2026-05-22T00:15:12+08:00"
    closed_at: "2026-05-22T00:34:25+08:00"
    evidence: "主线程等待两轮后无 CP6、无目标文件 diff；关闭 stalled 线程并重新调度。"
---

# META-DEV Handoff: CR008-S04 Implementation

## 目标

按已批准的 `process/stories/CR008-S04-quality-adjustment-label-window-gates-LLD.md` 离线实现 quality / adjustment / label window gate，并写入 CP6。

## Entry Gate

- `CR008-S03` CP7 PASS 并已收敛为 verified。
- `CR008-BATCH-A` CP5 批次人工审查已 approved。
- 不与 S05 并行，二者共享 `engine/research_dataset.py` gate aggregation。

## 写入范围

- `engine/research_dataset.py`
- `engine/quality.py`
- `tests/test_cr008_quality_adjustment_label_gates.py`
- `process/checks/CP6-CR008-S04-quality-adjustment-label-window-gates-CODING-DONE.md`

## 禁止范围

- 不修改 connector/runtime/storage、`data/**`、旧 `reports/data_quality_report.csv`、凭据、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。

## 测试与 CP6 要求

- 运行：`uv run --python 3.11 pytest -q tests/test_cr008_quality_adjustment_label_gates.py`
- 运行 S03 builder 回归。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- quality fail、复权混用/缺失/mismatch、label window 不足均结构化处理。
- 严肃研究 fail，探索模式只允许显式截断并写 metadata。
