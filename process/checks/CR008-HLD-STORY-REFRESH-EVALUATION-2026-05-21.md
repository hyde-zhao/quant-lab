---
check_id: "CR008-HLD-STORY-REFRESH-EVALUATION-2026-05-21"
status: "REFRESH-REQUIRED-SAFE-FOR-DESIGN"
checked_at: "2026-05-21T07:07:41+08:00"
agent_role: "meta-se"
workflow_id: "local_backtest"
change_id: "CR-008"
linked_change: "CR-007"
rollback_to: "solution-design"
priority_rule: "CR008-over-CR007-on-conflict"
implementation_allowed: false
source_handoff: "process/handoffs/META-SE-CR008-RESEARCH-DATA-LAYER-DESIGN-2026-05-21.md"
---

# CR008 HLD / Story 刷新评估

## 结论

CR008 应正式刷新 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md` 和 `process/DEVELOPMENT-PLAN.yaml`，并生成 CR008 专属 CP3 / CP4 自动预检和人工审查稿。

评估结论为 `REFRESH-REQUIRED-SAFE-FOR-DESIGN`，原因如下：

- CR008 是 high impact 结构性变更，`rollback_to=solution-design`，已由 meta-po 正式受理为 `intake-accepted-parallel-design-routing`。
- CR008 不替代 CR007。CR007 继续承担 canonical 数据生产侧补齐；CR008 收敛研究消费侧合同、报告字段语义、准入门禁和因子研究辅助数据缺失披露。
- CR007/CR008 冲突时以 CR008 为主。CR007-S02 可并行离线实现；CR007-S03 需等待 S02 CP6 与文件冲突清理；CR007-S04/S05 必须等 CR008 设计影响结论与 CP3/CP4 人工确认后再决定是否修订或继续。
- 本轮仅允许设计刷新、CP3/CP4 自动预检和人工审查稿；CR008 未完成 CP3/CP4、全量 LLD 与 CP5 批次人工确认前，`implementation_allowed=false`。

## 必读输入覆盖

| 输入 | 读取结论 | 对本评估的作用 |
|---|---|---|
| `process/STATE.md` | 已读取 CR007/CR008 intake、parallel_execution、dev_ready 与 hold 信息 | 确认 CR007-S02 dev_ready、CR008 并行 solution-design、CR008 不得实现 |
| `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md` | 已读取 | 确认冲突矩阵、并行调度判断和禁止动作 |
| `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md` | 已读取 | 确认 CR007 数据生产侧边界、五 Story、CP3/CP4/CP5 状态和安全授权 |
| `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md` | 已读取 | 确认研究级数据层目标、六 Story 草案、最终方案建议和数据缺口 |
| `process/HLD.md` | 已读取 frontmatter、拆分判定、§24 CR007 增量和 ADR 候选 | 确认 CR008 应追加为 §25，不新建 companion HLD |
| `process/ARCHITECTURE-DECISION.md` | 已读取 frontmatter、ADR-019..023 与确认点 | 确认需要新增 ADR-024..029 |
| `process/STORY-BACKLOG.md` | 已读取修订记录、CR007 Story、Wave、DAG、阻塞项 | 确认需要新增 CR008-S01..S06、Wave、DAG 和阻塞项 |
| `process/DEVELOPMENT-PLAN.yaml` | 已读取 CR007-BATCH-A wave、dependency_graph 与 parallel_policy | 确认需要新增 `CR008-BATCH-A` wave、CR008 policy、nodes/edges |
| `process/stories/CR007-S02-benchmark-calendar-backfill-LLD.md` | 已读取 | 确认 S02 可并行实现，且是 CR008 真实 benchmark 字段隔离的上游合同 |
| `process/stories/CR007-S03-index-members-stock-basic-datasets-LLD.md` | 已读取 | 确认 S03 提供 PIT/readiness 基础，但需受 CR008 PIT/fixed universe gate 约束 |
| `process/stories/CR007-S04-experiment-real-benchmark-consumption-LLD.md` | 已读取 | 确认 S04 与 CR008 proxy/real benchmark 字段隔离直接重叠，需 hold |
| `process/stories/CR007-S05-data-quality-report-and-doc-guardrail-LLD.md` | 已读取 | 确认 S05 与 CR008 research metadata、legacy report 和文档口径重叠，需 hold |

## 必须回答的问题

| 问题 | 结论 | 处理动作 |
|---|---|---|
| CR008 是否应与 CR007 并行推进，还是暂停 CR007 后切换 | 并行推进，但只并行 CR008 设计；CR007-S02 可继续离线实现 | `CR007-S02` 保持 dev_ready；CR008 走 CP3/CP4/CP5；CR007-S04/S05 继续 hold |
| CR008 六个建议 Story 是否合理 | 合理，保留六个 Story，不合并；执行顺序重排为合同先行、builder 中段、gate 与消费扩展后置 | 新增 `CR008-BATCH-A`，全量 LLD 统一确认；S01/S02 可先起草 LLD，S03 依赖 S01/S02，S04/S05 依赖 S03，S06 依赖 S03/S04/S05 |
| CR008 对 CR007-S02/S03/S04/S05 的影响 | S02 可并行；S03 需支撑 CR008 PIT/readiness；S04/S05 必须在 CR008 CP3/CP4 结论后修订或继续 | 在 Story Plan 中标注 S02 upstream contract、S03 contract dependency、S04/S05 hold-for-CR008-impact |
| 是否需要新增 ADR | 需要 | 新增 ADR-024 至 ADR-029，覆盖 `research_input_v1`、proxy/real benchmark 字段隔离、builder 只读边界、PIT/fixed 声明、质量/复权/label window gate、因子辅助数据降级语义 |
| CP3/CP4 人工确认稿如何表达合并边界 | CP3 审查 HLD/ADR 是否接受 CR008 为研究消费侧优先口径；CP4 审查 `CR008-BATCH-A` 六 Story、CR007 交互、全量 LLD 批次和 dev gate | 生成 `checkpoints/CP3-CR008-HLD-REVIEW.md` 与 `checkpoints/CP4-CR008-STORY-PLAN-REVIEW.md`，状态保持 `pending` |

## CR007 / CR008 影响矩阵

| CR007 Story | 当前事实 | CR008 影响 | 设计结论 |
|---|---|---|---|
| `CR007-S02-benchmark-calendar-backfill` | `dev_ready`，LLD confirmed，负责 `hs300_index` + `trade_calendar` 同区间 coverage gate | 为 CR008-S02 的真实 benchmark 字段隔离提供上游合同；不直接修改实验报告 | 可并行离线实现；不得因 CR008 暂停 |
| `CR007-S03-index-members-stock-basic-datasets` | blocked by S02 CP6 与共享文件冲突；负责 `index_members` / `index_weights` / `stock_basic` readiness | CR008-S05 会消费并收紧 PIT / fixed universe 语义，要求不得伪装 PIT | 暂不实现；等 S02 CP6 和 CR008 CP3/CP4 后复核 dev gate |
| `CR007-S04-experiment-real-benchmark-consumption` | blocked / hold；负责实验十三真实 benchmark 消费 | 与 CR008-S01/S02 报告 metadata、proxy/real benchmark 字段拆分重叠 | 继续 hold；CR008 设计确认后修订或在 LLD 中追加字段隔离要求 |
| `CR007-S05-data-quality-report-and-doc-guardrail` | blocked / hold；负责 legacy quality report 与文档护栏 | 与 CR008-S01/S04/S06 的 research metadata、quality gate、文档口径重叠 | 继续 hold；CR008 CP4 后统一修订文档/guardrail 范围 |

## Story 拆分判断

保留 CR008 草案六 Story：

| Story | 结论 | 理由 |
|---|---|---|
| `CR008-S01-research-input-contract-and-report-metadata` | 保留 | 先冻结 `research_input_v1` 和新报告强制 metadata，是其余 Story 的共同合同 |
| `CR008-S02-proxy-real-benchmark-field-separation` | 保留 | 直接解决 CR007-S04 与 CR008 的核心冲突；依赖 S02 benchmark/calendar contract |
| `CR008-S03-research-dataset-builder` | 保留 | 统一研究入口的实现边界独立，需消费 S01/S02 合同 |
| `CR008-S04-quality-adjustment-label-window-gates` | 保留 | 质量、复权、未来收益标签窗口是准入 gate，需在 builder 上收敛 |
| `CR008-S05-pit-universe-consumption-contract` | 保留 | PIT/fixed universe 与幸存者偏差披露独立于 benchmark 字段 |
| `CR008-S06-factor-research-auxiliary-data-contract` | 保留 | 实验十五和未来因子研究辅助数据缺口广，作为 P1 合同 Story 后置 |

不建议新增第七个 Story。文档说明和 legacy report 文字收敛归入 S01/S06 的报告 metadata 与辅助数据合同；CR007-S05 后续如继续实现，需要按 CR008 决策修订。

## 刷新范围

| 对象 | 处理方式 | 说明 |
|---|---|---|
| `process/HLD.md` | 原文档更新 | 追加 §25 CR008 研究级数据层口径硬化增量设计；保留旧 HLD / CR007 基线 |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 新增 ADR-024..029；保留 ADR-019..023 |
| `process/STORY-BACKLOG.md` | 原文档更新 | 新增 CR008-S01..S06、`CR008-BATCH-A`、DAG、阻塞项和待确认问题 |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 新增 CR008 wave、policy、nodes/edges；`implementation_allowed=false` |
| `process/stories/CR008-S*.md` | 新增 | 生成六张自给自足 Story 卡片，供 CP4 审查后进入全量 LLD 批次 |
| `process/checks/CP3-CR008-HLD-PRECHECK.md` | 新增 | 自动预检结果，结论预计 PASS，仍需人工确认 |
| `process/checks/CP4-CR008-STORY-PLAN-PRECHECK.md` | 新增 | 自动预检结果，结论预计 PASS，仍需人工确认 |
| `checkpoints/CP3-CR008-HLD-REVIEW.md` | 新增 | 人工审查稿，状态 `pending` |
| `checkpoints/CP4-CR008-STORY-PLAN-REVIEW.md` | 新增 | 人工审查稿，状态 `pending` |

## 门控与禁止事项

- CR008 `rollback_to=solution-design`，因此必须先完成 CP3 / CP4 人工确认。
- CP4 通过后，meta-po 才能组织 `CR008-BATCH-A` 全量 LLD。六个目标 Story 的 LLD 和 CP5 自动预检必须全部完成后，才能统一发起 CP5 人工确认。
- CP5 人工确认前，不得实现 CR008 任一 Story。
- 本评估未执行测试、未运行验证、未读取旧 `data/**`、未读取旧 `reports/data_quality_report.csv`、未联网、未读取凭据。

## Agent Dispatch Evidence

| 项 | 状态 | 说明 |
|---|---|---|
| handoff dispatch | spawn_agent | 主线程已真实调度 `meta-se/se-wei`，agent_id/thread_id=`019e47a2-88e9-7791-aa1e-a40b2945a4e7`；handoff 已由 meta-po 回填为 completed |
| 本轮执行 | completed by meta-se/se-wei | 已输出本评估、HLD/ADR/Story Backlog/Development Plan 刷新、六张 CR008 Story 卡、CP3/CP4 自动预检和 pending 人工审查稿 |
| 下游门控 | pending meta-po | CP3/CP4 人工确认必须由 meta-po 发起并回填，不由 meta-se 批准 |
