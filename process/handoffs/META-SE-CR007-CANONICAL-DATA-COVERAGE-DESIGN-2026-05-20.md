---
handoff_id: "META-SE-CR007-CANONICAL-DATA-COVERAGE-DESIGN-2026-05-20"
from_agent: "meta-po"
to_agent: "meta-se"
status: "completed"
created_at: "2026-05-20T07:14:10+08:00"
workflow_id: "local_backtest"
change_id: "CR-007"
story_id: ""
wave_id: "CR007-solution-design"
context_scope:
  - "process/STATE.md"
  - "process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md"
  - "process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md"
  - "process/HLD.md"
  - "process/ARCHITECTURE-DECISION.md"
  - "process/STORY-BACKLOG.md"
  - "process/DEVELOPMENT-PLAN.yaml"
dispatch:
  required: true
  mode: "spawn_agent"
  platform: "codex"
  agent_role: "meta-se"
  agent_path: ".agents/agents/meta-se.md"
  tool_name: "spawn_agent"
  agent_id: "019e4289-1ac2-7f21-8183-7dc41e972350"
  agent_name: "se-han"
  thread_id: "019e4289-1ac2-7f21-8183-7dc41e972350"
  spawned_at: "2026-05-20T07:45:00+08:00"
  resumed_at: ""
  completed_at: "2026-05-20T07:45:00+08:00"
  evidence: "主线程回报已通过 Codex spawn_agent 真实调度 meta-se/se-han 执行本 handoff，agent_id/thread_id=019e4289-1ac2-7f21-8183-7dc41e972350，status=completed。meta-se 已完成 CR-007 HLD/ADR/Story Plan/Development Plan/Story cards/CP3/CP4 检查点草稿。"
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# META-SE Handoff：CR-007 Canonical 数据覆盖与真实 Benchmark 设计刷新

## 目标

请由 `meta-se` 基于 CR-007 完成 `solution-design` 回退后的设计刷新评估，并在需要时修订正式设计与计划对象，使 CR-007 能进入 CP3 / CP4 / CR007-BATCH-A 全量 LLD 门控。

CR-007 是高影响结构性变更，承接 CR-006 已验证的 Tushare-first structured lake 和 canonical/gold 消费路径，目标是补齐 canonical 数据湖长期覆盖、真实沪深300 benchmark、交易日历、指数成分/权重、stock_basic、实验十三真实 benchmark 消费和旧质量报告收敛。

## 必读最小上下文

| 路径 | 用途 |
|---|---|
| `process/STATE.md` | 当前 active_change、CR-006 已 verified 但 pending close、CR-007 路由阻塞状态、子 agent 生命周期规则。 |
| `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md` | 本 CR 的五维影响分析、文档处理决策、推荐 Story、LLD 批次和安全边界。 |
| `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` | CR-007 继承的 Tushare-first / canonical_gold / old data reference-only 决策背景。 |
| `process/HLD.md` | 需要评估并可能追加 CR-007 章节、修订记录、风险与 CP3 输入。 |
| `process/ARCHITECTURE-DECISION.md` | 需要评估并可能新增或修订长周期 backfill、dataset readiness、benchmark policy、PIT / 非 PIT 边界、旧报告处理 ADR。 |
| `process/STORY-BACKLOG.md` | 需要评估并可能新增 CR007-S01..S05、依赖、文件所有权和验收标准。 |
| `process/DEVELOPMENT-PLAN.yaml` | 需要评估并可能新增 CR007-BATCH-A Wave、DAG、dev_gate、并行策略和验证顺序。 |

## 不得加载 / 不得触碰

- 不读取、打印或记录 `.env`、Tushare token、NAS 用户名、NAS 密码或其他凭据。
- 不执行真实 Tushare 抓取、真实外部网络请求或真实 `/mnt/ugreen-data-lake` 大规模写入。
- 不读取、列出、迁移、复制、比对或删除旧 `data/**`；不得把旧 `data/**` 当作 fallback、迁移源、覆盖证明或 fixture。
- 不修改业务代码、测试、README、USER-MANUAL、Story LLD 或 checkpoint；本任务只覆盖 HLD/ADR/Story Plan/Development Plan 的设计刷新评估与必要修订。
- 不把 2025 小窗口 `prices` 或 2024 四天 `hs300_index` 声明为 2015-2025 / 2015-2020 覆盖证明。

## 需要产出

1. 设计刷新评估：
   - 输出 CR-007 是否需要修订 HLD / ADR / Story Backlog / Development Plan 的判定。
   - 若任一对象需要修订，直接在对应正式文档追加修订记录和 CR-007 增量内容。
   - 若某对象不需修订，写明不修订理由和证据。

2. HLD / ADR 刷新重点：
   - 长周期 `prices` backfill 规划、分批 / resume / coverage 校验。
   - `hs300_index` 与 `trade_calendar` 同区间 coverage、真实 benchmark policy。
   - `index_members`、`index_weights`、`stock_basic` 的 dataset readiness 与 PIT / 非 PIT 边界。
   - 实验十三真实沪深300 benchmark 消费与代理 benchmark fallback / 对照命名。
   - 旧 `reports/data_quality_report.csv` 作为 legacy 旧报告，不再作为 canonical lake 当前质量真相源。

3. Story / Development Plan 刷新：
   - 建议批次固定为 `CR007-BATCH-A`。
   - 推荐 Story：
     - `CR007-S01-prices-long-horizon-backfill-planner`
     - `CR007-S02-benchmark-calendar-backfill`
     - `CR007-S03-index-members-stock-basic-datasets`
     - `CR007-S04-experiment-real-benchmark-consumption`
     - `CR007-S05-data-quality-report-and-doc-guardrail`
   - 明确 Wave、DAG、依赖类型、文件所有权、dev_gate、允许并行和必须串行的文件冲突。
   - 明确 CR007-BATCH-A 的全量 LLD 设计批次边界：五份 LLD 与 CP5 自动预检全部完成并统一人工确认前不得实现。

4. 自动预检建议：
   - 产出或更新 `process/checks/CP3-CR007-HLD-PRECHECK.md`。
   - 产出或更新 `process/checks/CP4-CR007-STORY-PLAN-PRECHECK.md`。
   - 如果存在 BLOCKING / REQUIRED，说明需要返工的对象，不得要求 meta-po 发起人工确认。

## 调度状态

本 handoff 已由主线程声明通过平台真实 `spawn_agent` 调度 `meta-se/se-han` 执行完成。平台调度证据已由 meta-po 回填到 frontmatter。

## Completion Evidence

| 字段 | 内容 |
|---|---|
| completed_at | 2026-05-20T07:45:00+08:00 |
| executed_by | meta-se |
| dispatch_mode | spawn_agent；agent_id/thread_id=`019e4289-1ac2-7f21-8183-7dc41e972350`；agent_name=`se-han` |
| modified_design | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` |
| new_story_cards | `process/stories/CR007-S01-prices-long-horizon-backfill-planner.md`、`process/stories/CR007-S02-benchmark-calendar-backfill.md`、`process/stories/CR007-S03-index-members-stock-basic-datasets.md`、`process/stories/CR007-S04-experiment-real-benchmark-consumption.md`、`process/stories/CR007-S05-data-quality-report-and-doc-guardrail.md` |
| checks | `process/checks/CP3-CR007-HLD-PRECHECK.md`、`process/checks/CP4-CR007-STORY-PLAN-PRECHECK.md` |
| manual_checkpoints | `checkpoints/CP3-CR007-HLD-REVIEW.md`、`checkpoints/CP4-CR007-STORY-PLAN-REVIEW.md` |
| conclusion | CP3/CP4 自动预检 PASS；需 meta-po 发起 CP3/CP4 人工确认；确认前不得进入 CR007-BATCH-A LLD |
| safety | 未执行真实 Tushare 抓取；未写入 `/mnt/ugreen-data-lake`；未读取 `.env`、凭据或旧 `data/**` |
