---
handoff_id: "META-DEV-CR007-CR008-PARALLEL-DEV-ANALYSIS-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-dev"
recommended_agent_name: "dev-qin-or-new"
status: "completed"
created_at: "2026-05-21T07:00:40+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
linked_change: "CR-007"
batch_id: "CR007-CR008-INTEGRATION"
wave_id: "CR007-CR008-dev-analysis"
reuse_key: "meta-dev|local_backtest|CR-008||CR007-CR008-dev-analysis"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "spawn_agent"
  agent_id: "019e47a2-893b-7ae1-acfa-9c7d6afb3637"
  agent_name: "dev-xu"
  thread_id: "019e47a2-893b-7ae1-acfa-9c7d6afb3637"
  spawned_at: "reported-by-main-thread; exact spawned_at not provided"
  resumed_at: ""
  completed_at: "reported-by-main-thread; exact completed_at not provided"
  evidence: "主线程已通过 spawn_agent 真实调度 meta-dev/dev-xu，agent_id/thread_id=019e47a2-893b-7ae1-acfa-9c7d6afb3637。meta-dev 已输出 process/checks/CR007-CR008-DEV-CONFLICT-ANALYSIS-2026-05-21.md；未实现代码、未运行测试、未修改 HLD/ADR/Story/Development Plan。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-Dev Handoff: CR007 / CR008 Parallel Development Analysis

## 任务目标

分析 CR007 当前 S02/S03/S04/S05 实现依赖、文件所有权冲突，以及 CR008 设计 / LLD / 实现能否与 CR007 并行。不要实现代码。

## 必读输入

- `process/STATE.md`
- `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/STORY-BACKLOG.md`
- `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md`
- `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md`
- `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md`
- `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md`
- `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md`

## 输出文件

- `process/checks/CR007-CR008-DEV-CONFLICT-ANALYSIS-2026-05-21.md`

## 分析重点

1. CR007-S02 是否仍可立即实现。当前 meta-po 预判：可以，且应与 CR008 设计 lane 并行。
2. CR007-S03 是否可以在 S02 CP6 PASS 后继续，还是必须等待 CR008 的 research dataset / PIT universe 设计结论。
3. CR007-S04 是否必须暂停到 CR008 benchmark 字段隔离和 report metadata 设计完成。
4. CR007-S05 是否必须暂停到 CR008 文档 / legacy report / research metadata 设计完成。
5. CR008-S01..S06 的可能文件范围与 CR007 的冲突：
   - `market_data/readers.py`
   - `market_data/benchmarks.py`
   - `market_data/normalization.py`
   - `market_data/validation.py`
   - `engine/data_loader.py`
   - `engine/research_dataset.py`
   - `experiments/run_experiment_13.py`
   - `experiments/run_experiment_15_factor_framework.py`
   - `README.md`
   - `docs/USER-MANUAL.md`
6. 给出明确 Wave 建议：哪些可并行，哪些必须串行，哪些需要等 CP3/CP4/CP5。

## 禁止事项

- 不实现代码，不修改测试，不创建 CR008 LLD。
- 不修改 HLD、ADR、Story Backlog、Development Plan。
- 不执行 pytest 或真实数据命令。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开、覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 完成标准

- 输出 CR007/CR008 文件冲突表。
- 输出可并行 / 必须串行 / 暂停的 Story 清单。
- 明确 CR007-S02 实现是否可立即由主线程调度。
- 明确 CR008 CP5 前不得实现的门控。
- 给出后续 meta-dev handoff 拆分建议，但不创建实现代码。
