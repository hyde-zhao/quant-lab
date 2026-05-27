---
handoff_id: "META-QA-CR008-S04-CP7-VERIFY-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-cao"
status: "completed"
created_at: "2026-05-22T00:40:34+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-VERIFY-W4A"
story_id: "CR008-S04-quality-adjustment-label-window-gates"
reuse_key: "meta-qa|local_backtest|CR-008|CR008-S04-quality-adjustment-label-window-gates|CR008-VERIFY-W4A"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b7a-2332-7ca1-9af7-6f412b686bfa"
  agent_name: "qa-kong the 2nd"
  thread_id: "019e4b7a-2332-7ca1-9af7-6f412b686bfa"
  spawned_at: "2026-05-22T00:59:19+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T01:02:05+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
previous_dispatches:
  - status: "stalled-closed-no-output"
    mode: "spawn_agent"
    platform: "codex"
    tool_name: "spawn_agent"
    agent_role: "meta-qa"
    agent_id: "019e4b69-f2cb-76a0-8483-e8b5715b4818"
    agent_name: "qa-cao the 2nd"
    thread_id: "019e4b69-f2cb-76a0-8483-e8b5715b4818"
    spawned_at: "2026-05-22T00:41:40+08:00"
    closed_at: "2026-05-22T00:58:53+08:00"
    evidence: "主线程等待两轮后无 CP7 文件、无相关 diff；关闭 stalled QA 线程并重新调度。"
---

# META-QA Handoff: CR008-S04 CP7 Verification

## 目标

验证 `CR008-S04-quality-adjustment-label-window-gates` 的离线实现是否满足已批准 LLD、CP6 与安全边界，并写入 CP7 验证结果。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR008-S04-quality-adjustment-label-window-gates-LLD.md`
- CP6 PASS: `process/checks/CP6-CR008-S04-quality-adjustment-label-window-gates-CODING-DONE.md`
- 实现 handoff completed: `process/handoffs/META-DEV-CR008-S04-IMPLEMENT-2026-05-21.md`
- 上游 S03 verified: `process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md`

## 验证范围

- `engine/research_dataset.py`
- `engine/quality.py`
- `tests/test_cr008_quality_adjustment_label_gates.py`
- `process/checks/CP6-CR008-S04-quality-adjustment-label-window-gates-CODING-DONE.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr008_quality_adjustment_label_gates.py`
- `uv run --python 3.11 pytest -q tests/test_cr008_research_dataset_builder.py`
- `uv run --python 3.11 python -m py_compile engine/research_dataset.py engine/quality.py`
- 静态复核 forbidden import / credential / old data / old report / destructive command 边界。
- 复核严肃研究模式下 quality fail/missing、复权缺失/混用/mismatch、label window 不足均结构化失败；探索模式仅允许 label window 截断并写 `label_available_end`、`truncated_sample_count`、`truncated_date_count` 和收紧后的 allowed claims。
- 检查 CP6 的 Agent Dispatch Evidence 是否与 handoff 一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 输出要求

- 写入 `process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若验证 PASS，建议 meta-po 将 S04 推进到 `verified`，并重新计算 CR008-S05 / S06 dev gate。
