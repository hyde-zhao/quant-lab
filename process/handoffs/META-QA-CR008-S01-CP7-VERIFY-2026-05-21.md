---
handoff_id: "META-QA-CR008-S01-CP7-VERIFY-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-jin"
status: "completed"
created_at: "2026-05-21T23:02:26+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-VERIFY-W1"
story_id: "CR008-S01-research-input-contract-and-report-metadata"
reuse_key: "meta-qa|local_backtest|CR-008|CR008-S01-research-input-contract-and-report-metadata|CR008-VERIFY-W1"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b10-5146-7e23-80b1-e35749f5e3df"
  agent_name: "qa-wei"
  thread_id: "019e4b10-5146-7e23-80b1-e35749f5e3df"
  spawned_at: "2026-05-21T23:02:26+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T23:09:03+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-QA Handoff: CR008-S01 CP7 Verification

## 目标

验证 `CR008-S01-research-input-contract-and-report-metadata` 的离线实现是否满足已批准 LLD、CP6 与安全边界，并写入 CP7 验证结果。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR008-S01-research-input-contract-and-report-metadata-LLD.md`
- CP6 PASS: `process/checks/CP6-CR008-S01-research-input-contract-and-report-metadata-CODING-DONE.md`
- 实现 handoff completed: `process/handoffs/META-DEV-CR008-S01-IMPLEMENT-2026-05-21.md`

## 验证范围

- `engine/research_dataset.py`
- `experiments/reporting.py`
- `experiments/run_experiment_14.py`
- `experiments/run_experiment_15_factor_framework.py`
- `tests/test_cr008_research_input_metadata.py`
- `process/checks/CP6-CR008-S01-research-input-contract-and-report-metadata-CODING-DONE.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr008_research_input_metadata.py`
- 静态复核 forbidden import / credential / old data / old report 边界。
- 检查 CP6 的 Agent Dispatch Evidence 是否与 handoff 一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 输出要求

- 写入 `process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若验证 PASS，建议 meta-po 将 S01 推进到 `verified`，并重新计算 CR008-S02 dev gate。
