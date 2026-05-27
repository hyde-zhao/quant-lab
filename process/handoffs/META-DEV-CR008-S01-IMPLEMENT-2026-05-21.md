---
handoff_id: "META-DEV-CR008-S01-IMPLEMENT-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-he"
status: "completed"
created_at: "2026-05-21T22:37:51+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-DEV-W1"
story_id: "CR008-S01-research-input-contract-and-report-metadata"
reuse_key: "meta-dev|local_backtest|CR-008|CR008-S01-research-input-contract-and-report-metadata|CR008-DEV-W1"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b00-85e1-7df0-9c4b-6116a5e6b386"
  agent_name: "dev-kong"
  thread_id: "019e4b00-85e1-7df0-9c4b-6116a5e6b386"
  spawned_at: "2026-05-21T22:46:33+08:00"
  resumed_at: ""
  completed_at: "2026-05-21T23:01:54+08:00"
  evidence: "spawn_agent"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR008-S01 Implementation

## 目标

按已批准的 `process/stories/CR008-S01-research-input-contract-and-report-metadata-LLD.md` 离线实现 `research_input_v1` 与报告 metadata 合同，并写入 CP6。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md`
- LLD confirmed: `process/stories/CR008-S01-research-input-contract-and-report-metadata-LLD.md`
- 当前 dev wave: `CR008-DEV-W1`
- 可立即调度：是。首批仅 S01，避免与 S02/S03 在 `experiments/run_experiment_15_factor_framework.py` 和 `engine/research_dataset.py` 上并行冲突。

## 写入范围

- `engine/research_dataset.py`
- `experiments/reporting.py`
- `experiments/run_experiment_14.py`
- `experiments/run_experiment_15_factor_framework.py`
- `tests/test_cr008_research_input_metadata.py`
- `process/checks/CP6-CR008-S01-research-input-contract-and-report-metadata-CODING-DONE.md`

## 禁止范围

- 不修改 `market_data/connectors/**`、`market_data/runtime.py`、`market_data/storage.py`、`delivery/**`、HLD、ADR、Development Plan 或其他 Story LLD/CP5。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 测试与 CP6 要求

- 运行：`uv run --python 3.11 pytest -q tests/test_cr008_research_input_metadata.py`
- 视修改范围运行相关实验报告/benchmark 回归。
- CP6 文件必须包含真实 Agent Dispatch Evidence、安全边界确认、测试命令与结果。

## 完成标准

- S01 targeted tests PASS。
- 旧报告只作为 legacy limitation，不作为 current truth。
- `research_input_v1` 必填 metadata 字段、legacy boundary、no old data/report/credential/forbidden import 均有测试覆盖。
- 完成后 Story 进入 `ready-for-verification`，由 meta-po 创建 CP7 handoff。
