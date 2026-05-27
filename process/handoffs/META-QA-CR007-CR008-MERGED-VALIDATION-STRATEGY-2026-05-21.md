---
handoff_id: "META-QA-CR007-CR008-MERGED-VALIDATION-STRATEGY-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-qa"
recommended_agent_name: "qa-wei-or-new"
status: "completed"
created_at: "2026-05-21T07:00:40+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
linked_change: "CR-007"
batch_id: "CR007-CR008-INTEGRATION"
wave_id: "CR007-CR008-validation-strategy"
reuse_key: "meta-qa|local_backtest|CR-008||CR007-CR008-validation-strategy"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-qa"
  agent_path: ".codex/agents/meta-qa.toml"
  tool_name: "spawn_agent"
  agent_id: "019e47a2-8982-7b21-8f1d-887428449462"
  agent_name: "qa-zhang"
  thread_id: "019e47a2-8982-7b21-8f1d-887428449462"
  spawned_at: "reported-by-main-thread; exact spawned_at not provided"
  resumed_at: ""
  completed_at: "reported-by-main-thread; exact completed_at not provided"
  evidence: "主线程已通过 spawn_agent 真实调度 meta-qa/qa-zhang，agent_id/thread_id=019e47a2-8982-7b21-8f1d-887428449462。meta-qa 已输出 process/checks/CR007-CR008-VALIDATION-STRATEGY-2026-05-21.md；策略文件不批准 CP5/CP6/CP7，不运行测试。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-QA Handoff: CR007 / CR008 Merged Validation Strategy

## 任务目标

分析 CR007 与 CR008 合并后的验证策略、最小回归集、安全边界和 CP7 / CP5 前置质量门控。不要实现代码，不运行测试。

## 必读输入

- `process/STATE.md`
- `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md`
- `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md`
- `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md`
- `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md`
- `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md`
- `process/checks/CP6-CR007-S01-prices-long-horizon-backfill-planner-CODING-DONE.md`
- `process/checks/CP7-CR007-S01-prices-long-horizon-backfill-planner-VERIFICATION-DONE.md`

## 输出文件

- `process/checks/CR007-CR008-VALIDATION-STRATEGY-2026-05-21.md`

## 必须覆盖

1. CR007-S02 CP6/CP7 的最小验证集。
2. CR007-S03/S04/S05 在 CR008 介入后的新增验证关注点。
3. CR008-S01..S06 的 CP5 自动预检重点与后续 CP7 验证重点。
4. 合并回归最小集：market_data readers / benchmark / validation / experiment 13 / experiment 15 / docs guardrail。
5. 安全边界：no network、no credential、no old data、no legacy report read、no real lake write。
6. CR008 冲突以 CR008 为主时，QA 如何判定 CR007 旧口径需要返工。

## 禁止事项

- 不运行测试，不修改代码，不修改文档。
- 不批准 CP3/CP4/CP5/CP7。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开、覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 完成标准

- 输出验证策略与最小回归矩阵。
- 标明哪些验证可在 CR007-S02 后立即执行，哪些必须等待 CR008 CP5/实现。
- 标明 BLOCKING / REQUIRED / ADVISORY 风险分级。
- 输出建议的 CP7 handoff 拆分方式，但不创建 CP7 文件。
