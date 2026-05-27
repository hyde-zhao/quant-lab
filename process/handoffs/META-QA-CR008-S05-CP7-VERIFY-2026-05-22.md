---
handoff_id: "META-QA-CR008-S05-CP7-VERIFY-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-wei the 2nd"
status: "completed"
created_at: "2026-05-22T01:51:59+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-VERIFY-W5"
story_id: "CR008-S05-pit-universe-consumption-contract"
reuse_key: "meta-qa|local_backtest|CR-008|CR008-S05-pit-universe-consumption-contract|CR008-VERIFY-W5"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4bac-11fc-7f23-86fb-e307a6004ba6"
  agent_name: "qa-wei the 2nd"
  thread_id: "019e4bac-11fc-7f23-86fb-e307a6004ba6"
  spawned_at: "2026-05-22T01:53:54+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T04:26:11+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-qa/qa-wei the 2nd 执行 CR008-S05 CP7 验证；CP7 已由子 agent 写入并 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-QA Handoff: CR008-S05 CP7 Verification

## 目标

验证 `CR008-S05-pit-universe-consumption-contract` 的离线实现是否满足已批准 LLD、CP6 与 CR008 优先安全边界，并写入 CP7 验证结果。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR008-S05-pit-universe-consumption-contract-LLD.md`
- CP6 PASS: `process/checks/CP6-CR008-S05-pit-universe-consumption-contract-CODING-DONE.md`
- 实现 handoff completed: `process/handoffs/META-DEV-CR008-S05-IMPLEMENT-2026-05-21.md`
- 上游 CR007-S03 verified: `process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md`
- 上游 CR008-S03 verified: `process/checks/CP7-CR008-S03-research-dataset-builder-VERIFICATION-DONE.md`
- 上游 CR008-S04 verified: `process/checks/CP7-CR008-S04-quality-adjustment-label-window-gates-VERIFICATION-DONE.md`

## 验证范围

- `engine/universe.py`
- `engine/research_dataset.py`
- `market_data/readers.py`
- `tests/test_cr008_pit_universe_contract.py`
- `process/checks/CP6-CR008-S05-pit-universe-consumption-contract-CODING-DONE.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr008_pit_universe_contract.py`
- `uv run --python 3.11 pytest -q tests/test_cr008_research_dataset_builder.py tests/test_cr008_quality_adjustment_label_gates.py`
- `uv run --python 3.11 python -m py_compile engine/universe.py engine/research_dataset.py market_data/readers.py tests/test_cr008_pit_universe_contract.py`
- 静态复核 forbidden import / credential / old data / old report / destructive command 边界。
- 复核 PIT available、PIT required but unavailable、fixed snapshot warning、`index_weights` 不替代 `index_members`、`quality_status=pass` 不等于 PIT available。
- 检查 CP6 的 Agent Dispatch Evidence 是否与实现 handoff 一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不执行补数、normalize、revalidate、replay、backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取或覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。
- 不修改 `delivery/**`、HLD、ADR、Development Plan、其他 Story LLD 或 CP5。

## 输出要求

- 写入 `process/checks/CP7-CR008-S05-pit-universe-consumption-contract-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若验证 PASS，建议 meta-po 将 S05 推进到 `verified`，并重新计算 CR008-S06 dev gate。
