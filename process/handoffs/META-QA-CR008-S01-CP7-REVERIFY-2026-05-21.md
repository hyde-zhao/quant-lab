---
handoff_id: "META-QA-CR008-S01-CP7-REVERIFY-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-hua"
status: "completed"
created_at: "2026-05-21T23:17:09+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-REVERIFY-W1"
story_id: "CR008-S01-research-input-contract-and-report-metadata"
reuse_key: "meta-qa|local_backtest|CR-008|CR008-S01-research-input-contract-and-report-metadata|CR008-REVERIFY-W1"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b1d-3d78-77c1-b4d0-b25b458370ea"
  agent_name: "qa-hua"
  thread_id: "019e4b1d-3d78-77c1-b4d0-b25b458370ea"
  spawned_at: "2026-05-21T23:17:09+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T23:23:48+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-QA Handoff: CR008-S01 CP7 Reverification

## 目标

重验 `CR008-S01-research-input-contract-and-report-metadata`，确认原 CP7 阻塞项 `CP7-F01` 与 `CP7-F02` 已由 blocker fix 修复，并写入更新后的 CP7 验证结果。

## Entry Gate

- 原 CP7 FAIL: `process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`
- Blocker fix CP6 PASS: `process/checks/CP6-CR008-S01-CP7-BLOCKER-FIX-CODING-DONE.md`
- Blocker fix handoff completed: `process/handoffs/META-DEV-CR008-S01-CP7-BLOCKER-FIX-2026-05-21.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr008_research_input_metadata.py tests/test_experiment_14_data_and_benchmark.py tests/test_experiment_15_factor_framework.py`
- 静态复核：
  - 两个实验脚本无 `default="data"` / `default='data'` / `use-legacy-quality-report` / `use-legacy-phase-report`。
  - `experiments/run_experiment_14.py` 无 `.open(` / `.read_text(`。
  - 两个实验脚本无 `data/` 字符串命中。
- 检查 CP6 blocker-fix 的 Agent Dispatch Evidence 是否与 blocker-fix handoff 一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 输出要求

- 更新或重写 `process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若重验 PASS，建议 meta-po 将 S01 推进到 `verified`，并重新计算 CR008-S02 dev gate。
