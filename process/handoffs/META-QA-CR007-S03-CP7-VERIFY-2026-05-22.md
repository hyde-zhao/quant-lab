---
handoff_id: "META-QA-CR007-S03-CP7-VERIFY-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-kong"
status: "completed"
created_at: "2026-05-22T01:31:09+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-VERIFY-W3-CR008-UNLOCK"
story_id: "CR007-S03-index-members-stock-basic-datasets"
reuse_key: "meta-qa|local_backtest|CR-007|CR007-S03-index-members-stock-basic-datasets|CR007-VERIFY-W3-CR008-UNLOCK"
dispatch:
  required: true
  status: "completed"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".agents/agents/meta-qa.md"
  tool_name: "spawn_agent"
  agent_id: "019e4b9a-46a8-7a12-93eb-544ab1dea396"
  agent_name: "qa-shi the 2nd"
  thread_id: "019e4b9a-46a8-7a12-93eb-544ab1dea396"
  spawned_at: "2026-05-22T01:34:25+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T01:36:18+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-qa/qa-shi the 2nd 执行 CR007-S03 CP7 验证；CP7 已写入并 PASS。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-QA Handoff: CR007-S03 CP7 Verification

## 目标

验证 `CR007-S03-index-members-stock-basic-datasets` 的离线实现是否满足已批准 LLD、CP6 与 CR008-S05 解锁所需的 readiness/PIT 合同，并写入 CP7 验证结果。

## Entry Gate

- CP5 batch approved: `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md`
- Story status: `process/stories/CR007-S03-index-members-stock-basic-datasets.md` status=`ready-for-verification`
- CP6 PASS: `process/checks/CP6-CR007-S03-index-members-stock-basic-datasets-CODING-DONE.md`
- DEV handoff completed: `process/handoffs/META-DEV-CR007-S03-IMPLEMENT-2026-05-22.md`
- CR008 upstream context: `CR008-S03` and `CR008-S04` already CP7 PASS; `CR008-S05` remains blocked until this CP7 PASS.

## 验证范围

- `market_data/contracts.py`
- `market_data/source_registry.py`
- `market_data/connectors/tushare.py`
- `market_data/normalization.py`
- `market_data/validation.py`
- `market_data/readers.py`
- `tests/test_cr007_index_members_stock_basic_datasets.py`
- `process/checks/CP6-CR007-S03-index-members-stock-basic-datasets-CODING-DONE.md`

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr007_index_members_stock_basic_datasets.py`
- `uv run --python 3.11 pytest -q tests/test_market_data_multidataset_quality_readers.py tests/test_market_data_normalization_validation_readers.py tests/test_market_data_tushare_datasets.py tests/test_market_data_tushare_connector.py`
- 静态复核 reader / validation 不导入 connector/runtime/storage，不触发 fetch/backfill，不把 `index_weights` 替代 `index_members`。
- 复核 PIT 不完整、future availability、fixed / non-PIT snapshot 都不能声明 PIT available。
- 复核 CP6 Agent Dispatch Evidence 与 DEV handoff replacement dispatch 一致。

## 禁止范围

- 不修改业务实现文件，除非发现验证阻塞需要在 CP7 中报告，不直接修复。
- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不执行 normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开或覆盖旧 `reports/data_quality_report.csv`。
- 不读取、打印或记录 `.env`、Tushare token、NAS 凭据或真实私有路径。
- 不启动 CR008-S05/S06 或 CR007-S04/S05。

## 输出要求

- 写入 `process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md`。
- CP7 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- 若验证 PASS，建议 meta-po 将 CR007-S03 推进到 `verified`，并重新计算 CR008-S05 dev gate。
