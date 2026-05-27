---
handoff_id: "META-DEV-CR008-S01-CP7-BLOCKER-FIX-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-lv"
status: "completed"
created_at: "2026-05-21T23:09:03+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-FIX-W1"
story_id: "CR008-S01-research-input-contract-and-report-metadata"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S01-research-input-contract-and-report-metadata|CR008-FIX-W1"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b15-1ae2-7bd0-bc9b-976b5819d511"
  agent_name: "dev-lv"
  thread_id: "019e4b15-1ae2-7bd0-bc9b-976b5819d511"
  spawned_at: "2026-05-21T23:09:03+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T23:17:09+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S01 CP7 Blocker Fix

## 目标

修复 `process/checks/CP7-CR008-S01-research-input-contract-and-report-metadata-VERIFICATION-DONE.md` 中的 `CP7-F01` 与 `CP7-F02`，并写入 CP6 blocker-fix 检查结果。

## 修复范围

- `experiments/run_experiment_14.py`
- `experiments/run_experiment_15_factor_framework.py`
- `tests/test_cr008_research_input_metadata.py`
- 必要时相关既有实验 14/15 测试文件中只更新显式 `data_dir` 入参断言。
- `process/checks/CP6-CR008-S01-CP7-BLOCKER-FIX-CODING-DONE.md`

## 必须修复

- `--data-dir` 默认值不得再是 `data`；未显式传入时 fail fast，不读取仓库旧 `data/**`。
- 旧质量报告和旧阶段报告只能作为 legacy path / limitation metadata，不允许再通过 opt-in 读取内容。
- 定向测试必须覆盖上述边界。

## 禁止范围

- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。
