---
handoff_id: "META-SE-CR008-RESEARCH-DATA-LAYER-DESIGN-2026-05-21"
from_agent: "meta-po"
from_agent_name: "po-sun"
to_agent: "meta-se"
recommended_agent_name: "se-han-or-new"
status: "completed"
created_at: "2026-05-21T07:00:40+08:00"
workflow_id: "local_backtest"
change_id: "CR-008"
linked_change: "CR-007"
batch_id: "CR008-BATCH-A"
wave_id: "CR008-solution-design"
reuse_key: "meta-se|local_backtest|CR-008||CR008-solution-design"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".codex/agents/meta-se.toml"
  tool_name: "spawn_agent"
  agent_id: "019e47a2-88e9-7791-aa1e-a40b2945a4e7"
  agent_name: "se-wei"
  thread_id: "019e47a2-88e9-7791-aa1e-a40b2945a4e7"
  spawned_at: "reported-by-main-thread; exact spawned_at not provided"
  resumed_at: ""
  completed_at: "reported-by-main-thread; exact completed_at not provided"
  evidence: "主线程已通过 spawn_agent 真实调度 meta-se/se-wei，agent_id/thread_id=019e47a2-88e9-7791-aa1e-a40b2945a4e7。meta-se 已完成 CR008 设计刷新、CP3/CP4 自动预检和人工审查稿生成；人工稿仍为 pending，未批准 CP3/CP4，未进入 LLD 或实现。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-SE Handoff: CR008 Research Data Layer Design Impact

## 任务目标

正式分析并刷新 `CR-008：研究级数据层口径硬化` 对 HLD、ADR、Story Backlog 和 Development Plan 的影响。CR008 与 CR007 冲突时，以 CR008 的研究级数据口径为主；但不得无门控地进入实现。

## 必读输入

- `process/STATE.md`
- `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md`
- `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md`
- `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md`
- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md`
- `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md`
- `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md`
- `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md`

## 输出要求

优先输出：

- `process/checks/CR008-HLD-STORY-REFRESH-EVALUATION-2026-05-21.md`

若确认需要正式刷新设计，并且不违反当前门控，可同步更新：

- `process/HLD.md`
- `process/ARCHITECTURE-DECISION.md`
- `process/STORY-BACKLOG.md`
- `process/DEVELOPMENT-PLAN.yaml`
- `process/checks/CP3-CR008-HLD-PRECHECK.md`
- `process/checks/CP4-CR008-STORY-PLAN-PRECHECK.md`
- `checkpoints/CP3-CR008-HLD-REVIEW.md`
- `checkpoints/CP4-CR008-STORY-PLAN-REVIEW.md`

若不能安全刷新，必须只产出待刷新清单，并说明阻塞原因，不得伪造 CP3/CP4。

## 必须回答的问题

1. CR008 是否应与 CR007 并行推进，还是暂停 CR007 后切换？当前 meta-po 预判为：CR007-S02 可并行实现，CR008 先并行设计。
2. CR008 的六个建议 Story 是否合理，是否需要拆分、合并或重排？
3. CR008 对 CR007-S02/S03/S04/S05 的影响是什么？哪些 CR007 Story 必须因 CR008 优先级而暂停或修订？
4. CR008 是否需要新增 ADR，例如 `research_input_v1` 唯一研究入口、proxy/real benchmark 字段隔离、PIT/fixed universe 声明、label window gate、复权 gate？
5. CP3/CP4 人工确认稿应如何表达 CR008 与 CR007 的合并边界？

## 禁止事项

- 不实现代码，不修改测试，不执行测试。
- 不批准 CP3/CP4/CP5。
- 不创建 CR008 LLD，不进入 CP6/CP7。
- 不执行真实 Tushare 抓取、真实 lake read/write、normalize/revalidate/replay/backfill job。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 不读取、打开、覆盖旧 `reports/data_quality_report.csv` 内容。
- 不读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 完成标准

- 明确 CR008 的 `rollback_to`、设计刷新范围、CP3/CP4 门控和 CR007/CR008 优先级。
- 明确可并行与必须串行的 Story / Wave。
- 若刷新 HLD/ADR/Story/Development Plan，则生成对应 CP3/CP4 自动预检和人工审查稿。
- 在输出中记录 Agent Dispatch Evidence；本 handoff 已由 meta-po 根据主线程回报回填为 completed，CP3/CP4 人工稿仍为 pending。
