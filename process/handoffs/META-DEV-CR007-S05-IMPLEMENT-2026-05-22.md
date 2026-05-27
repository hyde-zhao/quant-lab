---
handoff_id: "META-DEV-CR007-S05-IMPLEMENT-2026-05-22"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-he the 2nd"
status: "blocked"
created_at: "2026-05-22T05:26:38+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
linked_change: "CR-008"
batch_id: "CR007-BATCH-A"
wave_id: "CR007-DEV-W5"
story_id: "CR007-S05-data-quality-report-and-doc-guardrail"
reuse_key: "meta-dev|local_backtest|CR-007|CR007-S05-data-quality-report-and-doc-guardrail|CR007-DEV-W5"
dispatch:
  required: true
  status: "blocked"
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".agents/agents/meta-dev.md"
  tool_name: "spawn_agent"
  agent_id: "019e4c70-0aa3-77b2-8d98-415d8b4a19c8"
  agent_name: "dev-he the 2nd"
  thread_id: "019e4c70-0aa3-77b2-8d98-415d8b4a19c8"
  spawned_at: "2026-05-22T05:27:55+08:00"
  resumed_at: ""
  completed_at: "2026-05-22T05:33:16+08:00"
  evidence: "主线程通过 spawn_agent 真实调度 meta-dev/dev-he the 2nd 执行 CR007-S05 离线实现；该线程写入 CP6 BLOCKED 后未返回最终状态，主线程于 2026-05-22T05:47:00+08:00 关闭。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-DEV Handoff: CR007-S05 Implementation

## 目标

实现 `CR007-S05-data-quality-report-and-doc-guardrail` 的离线文档与静态护栏改造，并写入 CP6 编码完成检查结果。

## Entry Gate

- CR007 CP5 batch approved: `checkpoints/CP5-CR007-BATCH-A-LLD-BATCH.md`
- Story LLD confirmed: `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md`
- Upstream CR007-S01 verified: `process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md`
- Upstream CR007-S02 verified: `process/checks/CP7-CR007-S02-benchmark-calendar-backfill-VERIFICATION-DONE.md`
- Upstream CR007-S03 verified: `process/checks/CP7-CR007-S03-index-members-stock-basic-datasets-VERIFICATION-DONE.md`
- Upstream CR007-S04 verified: `process/checks/CP7-CR007-S04-experiment-real-benchmark-consumption-VERIFICATION-DONE.md`
- CR008 priority blocker cleared: `CR008-BATCH-A` all six stories verified, including `process/checks/CP7-CR008-S06-factor-research-auxiliary-data-contract-VERIFICATION-DONE.md`

## 写入范围

- Primary:
  - `tests/test_cr007_quality_report_doc_guardrail.py`
- Shared, only if required by LLD:
  - `README.md`
  - `docs/USER-MANUAL.md`
  - `.gitignore`

## 必须实现

- README / USER-MANUAL 明确旧 `reports/data_quality_report.csv` 是 `legacy quality report` / `legacy old report`。
- README / USER-MANUAL 明确当前质量真相源是 configured lake root 下的 `lake quality/catalog current truth` / `current quality truth`。
- README / USER-MANUAL 明确旧报告和旧 `data/**` 的 `coverage proof forbidden`，不得作为 current quality truth、coverage proof、fixture 或 fallback。
- 文档 coverage proof 字段清单必须覆盖 `dataset`、`start/end`、`denominator`、`run_id/source/interface`、`quality_status`、`catalog/lineage`。
- `.gitignore` 只做缺失补齐；若现有规则已满足，保持 no-op 并在 CP6 记录。
- 新增 S05 静态测试，allowlist 只允许读取 `README.md`、`docs/USER-MANUAL.md`、`.gitignore` 和测试自身；`data/**`、`reports/**`、`.env`、credentials 条目数量必须为 0。
- 测试必须用字符串级 denylist 验证 `reports/data_quality_report.csv`、`data/prices.parquet`、`.env` 等路径被阻断，不打开这些路径。

## 必跑验证

- `uv run --python 3.11 pytest -q tests/test_cr007_quality_report_doc_guardrail.py`
- `uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py tests/test_cr008_research_input_metadata.py tests/test_cr008_quality_adjustment_label_gates.py`
- `uv run --python 3.11 python -m py_compile tests/test_cr007_quality_report_doc_guardrail.py`
- 静态复核 allowlist / denylist / credential sentinel / old data / old report / delivery 边界。

## 禁止范围

- 不联网、不真实 Tushare fetch、不真实 lake read/write。
- 不执行补数、normalize、revalidate、replay、backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开或覆盖旧 `reports/data_quality_report.csv` 内容；只允许在 README / USER-MANUAL / 测试字符串中提及该路径并标记 legacy / forbidden。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。
- 不修改 `engine/**`、`experiments/**`、`market_data/**`、`delivery/**`、HLD、ADR、Development Plan、其他 Story LLD 或 CP5。
- 不修改 CR008 已验证合同；若 S05 文档与 CR008 冲突，以 CR008 为主并停止报告。

## 输出要求

- 写入 `process/checks/CP6-CR007-S05-data-quality-report-and-doc-guardrail-CODING-DONE.md`。
- CP6 必须包含 Entry Criteria、Checklist、Exit Criteria、Deliverables、Agent Dispatch Evidence、安全边界确认、测试命令与结果。
- CP6 必须列出实际修改文件、`.gitignore` 是 no-op 还是补齐、已知限制和 meta-qa 验证入口。
- 若实现发现 LLD 与 S01/S02/S03/S04/CR008 verified contract 冲突，停止并在 CP6 或偏差记录中报告，不自行扩大范围。

## 完成记录

- 完成时间：2026-05-22T05:33:16+08:00
- CP6：`process/checks/CP6-CR007-S05-data-quality-report-and-doc-guardrail-CODING-DONE.md`，结论 `BLOCKED`。
- 已完成：README / USER-MANUAL CR007 legacy quality report 与 lake quality/catalog current truth 文档更新；新增 `tests/test_cr007_quality_report_doc_guardrail.py`；`.gitignore` 复核为 no-op。
- 已通过验证：
  - `uv run --python 3.11 pytest -q tests/test_cr007_quality_report_doc_guardrail.py`：`7 passed in 0.02s`
  - `uv run --python 3.11 python -m py_compile tests/test_cr007_quality_report_doc_guardrail.py`：PASS
- 阻断项：`uv run --python 3.11 pytest -q tests/test_cr006_old_data_reference_guardrail.py tests/test_cr008_research_input_metadata.py tests/test_cr008_quality_adjustment_label_gates.py` 结果 `1 failed, 30 passed in 0.76s`，失败为 `tests/test_cr008_research_input_metadata.py::test_experiment_15_schema_and_report_metadata_allowed_claims_are_conservative`，缺少 `industry, market cap, liquidity and style exposure data are unavailable`。
