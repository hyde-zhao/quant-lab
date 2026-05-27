---
check_id: "CR007-CR008-DEV-CONFLICT-ANALYSIS-2026-05-21"
status: "COMPLETED-WITH-HOLDS"
checked_at: "2026-05-21T08:10:00+08:00"
agent_role: "meta-dev"
change_id: "CR-008"
linked_change: "CR-007"
handoff: "process/handoffs/META-DEV-CR007-CR008-PARALLEL-DEV-ANALYSIS-2026-05-21.md"
output_scope: "development conflict and parallelism analysis only"
implementation_executed: false
tests_executed: false
network_used: false
old_data_operations_executed: false
old_quality_report_read_or_overwritten: false
credentials_read_or_printed: false
---

# CR007 / CR008 开发冲突与并行性分析

## 1. 结论摘要

| 结论项 | 判定 | 说明 |
|---|---|---|
| `CR007-S02-benchmark-calendar-backfill` 是否仍可立即实现 | 可以 | `process/STATE.md.parallel_execution.dev_ready` 显示 S02 为唯一 `ready-for-dispatch`，`dev_running=[]`，S01 CP6/CP7 均 PASS 且 verified；CR008 当前只允许 solution-design / 分析 lane，不允许实现。 |
| S02 可否与 CR008 并行 | 可以，但只与 CR008 设计 / 分析并行 | S02 可与 CR008 meta-se solution-design、meta-dev 冲突分析、meta-qa 验证策略并行；不得与任何 CR008 代码实现并行，因为 CR008 CP5 前 `implementation_allowed=false`。 |
| `CR007-S03-index-members-stock-basic-datasets` | 暂停到 S02 CP6 PASS 且 CR008 设计影响结论明确 | S03 原本等待 S02 CP6 + 共享文件冲突清理。CR008 又要求 research dataset / PIT universe 口径优先，因此 S03 不能只凭 S02 CP6 立即启动；还需 CR008 design impact 明确 S03 readiness/PIT 合同是否要修订。 |
| `CR007-S04-experiment-real-benchmark-consumption` | 暂停 / hold | S04 与 CR008 的 proxy/real benchmark 字段隔离、实验报告 metadata、`run_experiment_13.py` 范围直接重叠；CR008 冲突优先，S04 不应提前实现。 |
| `CR007-S05-data-quality-report-and-doc-guardrail` | 暂停 / hold | S05 与 CR008 的 legacy report、current quality truth、research metadata 和 README / USER-MANUAL 文档口径重叠；CR008 设计结论前不应提前写文档。 |
| CR008 实现门控 | CP5 前全部禁止 | CR008 必须先完成 HLD/ADR/Story/Development Plan 刷新与 CP3/CP4，再完成 S01..S06 全量 LLD、Story 级 CP5 自动预检和 CP5 批次人工确认，之后才可按 Story dev_gate 和文件所有权启动实现。 |

## 2. 已读取输入与边界确认

已读取 handoff 指定输入：

| 输入 | 读取结论 |
|---|---|
| `process/STATE.md` | CR007 处于 story-execution；S01 verified；S02 dev_ready；S03/S04/S05 blocked/hold；CR008 为 `intake-accepted-parallel-design-routing`。 |
| `process/checks/CR007-CR008-INTEGRATED-INTAKE-ROUTING-2026-05-21.md` | meta-po 路由结论为：CR007-S02 可继续；CR008 不得实现；S04/S05 暂缓。 |
| `process/changes/CR-007-CANONICAL-DATA-COVERAGE-BACKFILL-AND-BENCHMARK-2026-05-20.md` | CR007 CP3/CP4/CP5 已 approved；S01 verified；S02 dev_ready；真实抓取 / lake 写入 / 旧数据 / 旧报告 / 凭据均未授权。 |
| `process/changes/CR-008-RESEARCH-DATA-LAYER-HARDENING-2026-05-20.md` | CR008 已受理但未获 CP3/CP4/CP5；冲突时以 CR008 为主；建议继续 S02，S03 等 S02 CP6 与 CR008 影响分析。 |
| `process/DEVELOPMENT-PLAN.yaml` | CR007 默认 S01 -> S02 -> S03 -> S04 -> S05；S02/S03 因共享 `normalization.py` / `validation.py` / `readers.py` 默认不得并行开发。 |
| `process/STORY-BACKLOG.md` | CR007-S02/S03/S04/S05 的范围、依赖、验收与非范围已确认；CR008 尚未进入正式 Story Plan。 |
| S02/S03/S04/S05 LLD | 四份 LLD 均 `confirmed=true`、`implementation_allowed=true`，但实现仍受 Wave、依赖、CR008 冲突和文件所有权门控限制。 |
| `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md` | S02 handoff 明确 S02 dev_gate 已满足，可直接离线实现；同时禁止与 S03 并行开发。 |

安全边界确认：

- 未实现代码，未修改测试，未创建 CR008 LLD。
- 未修改 `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`。
- 未执行 pytest、真实数据命令、Tushare 抓取、lake read/write、normalize/revalidate/replay/backfill job。
- 未读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未读取、打开或覆盖旧 `reports/data_quality_report.csv`。
- 未读取、打印或记录 `.env`、token、NAS 凭据或真实私有路径。

## 3. CR007 当前 Story 判定

| Story | 当前事实 | 是否可调度 | 需要等待的门控 | 判定 |
|---|---|---:|---|---|
| `CR007-S02-benchmark-calendar-backfill` | CP5 approved；S01 CP6/CP7 PASS；`dev_ready`；`dev_running=[]`；允许文件为 `market_data/cli.py`、`normalization.py`、`validation.py`、`catalog.py`、`readers.py`、`benchmarks.py` 和 S02 测试/CP6 | 是 | 只允许离线实现；不得真实抓取、写 lake、读旧 data/report/凭据；不得与 S03 或任何 CR008 实现并行 | 立即调度既有 S02 handoff，推荐复用 `dev-zhang` 线程。 |
| `CR007-S03-index-members-stock-basic-datasets` | LLD confirmed；但 blocked by S02；共享 `market_data/normalization.py`、`validation.py`、`readers.py`；CR008 需要 PIT universe / research dataset 口径 | 否 | S02 CP6 PASS；S02/S03 文件冲突清理；CR008 design impact 明确 research dataset / PIT universe 合同是否需要修订 | 暂停。若 CR008 CP3/CP4 结论不改变 S03 合同，可在 S02 CP6 后进入 dev_ready；若改变，必须先修订 S03 LLD/CP5 或由 CR008 Story 接管。 |
| `CR007-S04-experiment-real-benchmark-consumption` | LLD confirmed；依赖 S02/S03；primary `experiments/run_experiment_13.py`，shared `market_data/benchmarks.py`、实验十/十二 | 否 | S02/S03 contract frozen；CR008 benchmark 字段隔离、report metadata 设计完成；冲突优先级以 CR008 为主 | 暂停。建议等 CR008 CP3/CP4 + 相关 LLD 明确后，决定 S04 是修订实现、缩小范围还是被 CR008-S02/S01 部分替代。 |
| `CR007-S05-data-quality-report-and-doc-guardrail` | LLD confirmed；依赖 S01/S02/S03/S04；shared `README.md`、`docs/USER-MANUAL.md`、`.gitignore` | 否 | S04 CP6 PASS；CR008 legacy report / research metadata / 文档口径设计完成 | 暂停。建议等 CR008 文档与 metadata 合同冻结后再启动，避免 README / USER-MANUAL 返工和口径冲突。 |

## 4. CR008 S01..S06 与 CR007 的 Story 级冲突表

| CR008 Story | CR008 可能文件范围 | 与 CR007 的冲突对象 | 冲突等级 | 并行性判定 |
|---|---|---|---|---|
| `CR008-S01-research-input-contract-and-report-metadata` | `experiments/**`、`engine/reporting.py`、测试；后续可能影响报告 metadata 文档 | `CR007-S04` 的实验十三报告输出；`CR007-S05` 的 README / USER-MANUAL 文档口径 | 中-高 | LLD 可在 CR008 CP3/CP4 后起草；实现必须等 CR008 CP5。若落到 `experiments/run_experiment_13.py` 或文档，必须与 S04/S05 串行。 |
| `CR008-S02-proxy-real-benchmark-field-separation` | `experiments/run_experiment_06_07.py`、`experiments/run_experiment_13.py`、相关测试；可能消费 `market_data/benchmarks.py` metadata | `CR007-S04` primary `run_experiment_13.py`；`CR007-S02/S04` shared `market_data/benchmarks.py` | 高 | 不得与 CR007-S04 并行实现。CR008 优先，建议先由 CR008 设计冻结 proxy/hs300 字段，再决定 S04 是否修订或缩小。 |
| `CR008-S03-research-dataset-builder` | `engine/research_dataset.py`、`engine/data_loader.py`、测试；只读消费 `market_data/readers.py` / benchmark contract | 文件上与 CR007-S02/S03/S04/S05 不直接重叠，但运行合同依赖 S02 benchmark/calendar 与 S03 readiness/PIT | 中 | 设计可并行。实现需 CR008 CP5，且至少等待 S02 contract frozen；若要求 PIT universe，需等待 S03 合同冻结或 CR008 自行接管 PIT 合同。 |
| `CR008-S04-quality-adjustment-label-window-gates` | `engine/research_dataset.py`、`engine/quality.py`、测试；可能引用 validation/readiness 语义 | 与 CR007 无主要文件重叠，但依赖 S02/S03 的 quality/readiness/benchmark 语义；与 CR008-S03/S06 共享 `engine/research_dataset.py` | 中 | CR008 内部需与 S03/S06 串行或明确 merge owner。实现必须 CP5 后，且不得提前改 `market_data/validation.py` 侵占 CR007-S02/S03。 |
| `CR008-S05-pit-universe-consumption-contract` | `market_data/readers.py`、`engine/universe.py`、测试 | `CR007-S02` shared `market_data/readers.py`；`CR007-S03` shared `market_data/readers.py` 与 PIT/readiness 语义 | 高 | 不得与 S02/S03 并行实现。应等待 S02 CP6、S03 合同冻结；若 CR008 改变 PIT 口径，优先回改 S03 LLD/实现计划。 |
| `CR008-S06-factor-research-auxiliary-data-contract` | `engine/research_dataset.py`、`market_data/readers.py`、`experiments/run_experiment_15_factor_framework.py`、测试 | `CR007-S03` shared `market_data/readers.py`；CR007 无 `run_experiment_15` 文件所有权，但文档/metadata 可能与 S05 重叠 | 中-高 | CR008 CP5 后才可实现；`market_data/readers.py` 部分必须等 S02/S03 清理；`engine/research_dataset.py` 部分需与 CR008-S03/S04 串行。 |

## 5. 用户指定文件粒度冲突矩阵

| 文件 / 范围 | CR007 涉及 Story | CR008 可能涉及 Story | 冲突等级 | 调度决策 |
|---|---|---|---|---|
| `market_data/readers.py` | S02、S03 | S05、S06，S03/S04 可能消费 | 高 | S02 可先做；S03 等 S02 CP6 + CR008 impact；CR008-S05/S06 实现必须在 CR008 CP5 后且不得与 S02/S03 并行。 |
| `market_data/benchmarks.py` | S02、S04 | S02 可能消费或扩展 metadata；S03 可能消费 | 高 | S02 先冻结 resolver / coverage contract；S04 等 CR008 字段隔离设计；CR008 实现前需确认不重写 S02 合同。 |
| `market_data/normalization.py` | S02、S03 | CR008 不应默认修改；如为 gate 扩展需纳入 CR008 Story Plan | 中-高 | 当前归 CR007-S02/S03 串行处理；CR008 CP5 前不得改，CP5 后若需要修改必须避开 S02/S03 running。 |
| `market_data/validation.py` | S02、S03 | CR008-S04 可能想引用 quality gate，但推荐落在 `engine/research_dataset.py` / `engine/quality.py` | 中-高 | 不建议 CR008 直接写该文件，除非 CP3/CP4/CP5 明确把 validation 合同纳入 CR008 且与 CR007 串行。 |
| `engine/data_loader.py` | CR007-S02/S03/S04/S05 均不写 | CR008-S03 | 低文件冲突 / 中合同依赖 | 文件上可独立，但实现仍需 CR008 CP5 和 S02/S03 数据合同输入；不得回退旧 `data/**`。 |
| `engine/research_dataset.py` | CR007 不写 | CR008-S03、S04、S06 | CR008 内部高 | CR008 内部必须串行或指定单一 merge owner；CP5 前不得创建。 |
| `experiments/run_experiment_13.py` | S04 primary | CR008-S01/S02 | 高 | S04 暂停；CR008 设计优先冻结字段。实现时 S04 与 CR008-S02 不得并行。 |
| `experiments/run_experiment_15_factor_framework.py` | CR007 不写 | CR008-S06 | 低文件冲突 / 中合同依赖 | 可作为 CR008 后段 Story；需等待 `research_dataset.py` 和 auxiliary data contract 冻结。 |
| `README.md` | S05 shared | CR008 文档 / metadata 说明可能涉及 | 高 | S05 暂停；CR008 设计后再统一口径，避免 legacy report/current truth 重复返工。 |
| `docs/USER-MANUAL.md` | S05 shared | CR008 文档 / metadata 说明可能涉及 | 高 | 与 README 同步暂停；后续由文档/guardrail Story 串行实现。 |

## 6. Wave / Story 并行建议

### 6.1 当前可并行

| Lane | 状态 | 条件 |
|---|---|---|
| `CR007-S02` 离线实现 | 可立即调度 | 复用 `process/handoffs/META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md`；不得与 S03 或 CR008 实现并行。 |
| `CR008` solution-design | 可并行 | 只允许 meta-se 做 HLD/ADR/Story/Development Plan 影响分析与 CP3/CP4 材料；本分析不修改这些文件。 |
| `CR007/CR008` dev conflict analysis | 已完成本文件 | 仅输出 `process/checks/CR007-CR008-DEV-CONFLICT-ANALYSIS-2026-05-21.md`。 |
| `CR007/CR008` merged validation strategy | 可并行 | 只允许 meta-qa 产出验证策略，不执行真实数据或旧报告操作。 |

### 6.2 必须串行

| 串行链路 | 原因 |
|---|---|
| `CR007-S02` -> `CR007-S03` | 共享 `market_data/normalization.py`、`validation.py`、`readers.py`；S03 还需 S02 benchmark/calendar contract。 |
| `CR007-S03` -> `CR007-S04` | S04 消费 S02 benchmark 与 S03 dataset readiness / PIT 语义。 |
| `CR007-S04` -> `CR007-S05` | S05 文档必须引用实验 benchmark 和 legacy/current truth 口径，不应先写。 |
| `CR007-S04` <-> `CR008-S02` | 均涉及 `experiments/run_experiment_13.py` 和 proxy/hs300 benchmark 字段，不得并行。 |
| `CR007-S05` <-> CR008 文档 / metadata Story | README / USER-MANUAL 口径重叠，不得并行。 |
| `CR008-S03` / `CR008-S04` / `CR008-S06` | 均可能写 `engine/research_dataset.py`，CR008 内部需串行或明确文件 merge owner。 |
| `CR008-S05` / `CR008-S06` 与 `CR007-S02/S03` | 共享 `market_data/readers.py`，且依赖 readiness / PIT 合同。 |

### 6.3 暂停清单

| Story / Wave | 暂停原因 | 恢复条件 |
|---|---|---|
| `CR007-S03` / `CR007-DEV-W3` | S02 CP6 未完成；与 CR008 PIT / research dataset 口径相关 | S02 CP6 PASS；文件冲突清理；CR008 design impact 明确 S03 合同不需修订，或修订后重新通过必要门控。 |
| `CR007-S04` / `CR007-DEV-W4` | 与 CR008 benchmark 字段隔离和 report metadata 高度重叠 | CR008 CP3/CP4 设计结论和相关 LLD 确认；若冲突，以 CR008 修订 S04 或接管对应范围。 |
| `CR007-S05` / `CR007-DEV-W5` | 与 CR008 legacy report、current quality truth、文档和 research metadata 重叠 | CR008 文档/metadata 合同冻结；S04 或 CR008 benchmark/report Story 完成必要合同。 |
| `CR008-S01..S06` 实现 | CR008 尚未完成 CP3/CP4/CP5 | CP3/CP4 approved；六份 LLD + CP5 自动预检 PASS；CP5 批次人工 approved；逐 Story dev_gate 和文件所有权通过。 |

## 7. CR008 CP5 前不得实现的门控

CR008 当前 `implementation_allowed=false`。下列条件全部满足前，不得创建或修改 CR008 业务产物、测试、README / USER-MANUAL、`engine/**`、`market_data/**`、`experiments/**`：

1. CR008 HLD / ADR / Story Backlog / Development Plan 影响分析完成，并经 CP3 / CP4 人工确认。
2. CR008-S01..S06 Story 卡片范围、依赖类型、文件所有权、dev_gate 完整。
3. CR008-BATCH-A 六份 LLD 全量输出。
4. 六份 LLD 的 Story 级 CP5 自动预检均为 PASS。
5. `checkpoints/CP5-CR008-BATCH-A-LLD-BATCH.md` 经用户人工确认为 approved。
6. 当前 Story 的 LLD frontmatter `confirmed=true`、`implementation_allowed=true`。
7. 当前 Story 依赖满足：`contract` 依赖需接口冻结；`runtime` 依赖默认等待上游 verified；`file-conflict` 依赖默认串行。
8. `process/STATE.md.parallel_execution.dev_running` 中不存在 primary/shared 文件冲突。
9. 安全授权未放宽：仍不得真实 Tushare 抓取、真实 lake 写入、读旧 `data/**`、读旧 `reports/data_quality_report.csv` 或读凭据。

## 8. 后续 meta-dev handoff 拆分建议

| 建议 handoff | 触发条件 | 写入范围建议 | 串并行说明 |
|---|---|---|---|
| 复用 `META-DEV-CR007-BATCH-A-DEV-W2-S02-2026-05-20.md` | 立即 | 仅 S02 允许文件：`market_data/cli.py`、`normalization.py`、`validation.py`、`catalog.py`、`readers.py`、`benchmarks.py`、S02 测试、S02 CP6 | 可与 CR008 设计 lane 并行；不得与 S03 或 CR008 实现并行。 |
| 新建 / 更新 `CR007-S03` 实现 handoff | S02 CP6 PASS，且 CR008 design impact 判定 S03 合同可继续或已完成修订 | `market_data/contracts.py`、`source_registry.py`、`connectors/tushare.py`、`normalization.py`、`validation.py`、`readers.py`、S03 测试、S03 CP6 | 单 Story handoff；不得与 CR008-S05/S06 或任何 readers 写入并行。 |
| 暂缓 `CR007-S04` 实现 handoff | CR008 benchmark 字段隔离 / report metadata 设计完成前不得发起 | `experiments/run_experiment_13.py`、实验十/十二、`market_data/benchmarks.py`、S04 测试 | 建议由 meta-po 在 CR008 CP3/CP4 后判断：修订 S04 LLD、缩小 S04，或让 CR008-S02 优先实现同文件。 |
| 暂缓 `CR007-S05` 实现 handoff | CR008 legacy report / research metadata / 文档口径设计完成前不得发起 | `README.md`、`docs/USER-MANUAL.md`、`.gitignore`、S05 guardrail 测试 | 建议与 CR008 文档 Story 串行，避免 README / USER-MANUAL 冲突。 |
| CR008 LLD handoff 批次 | CR008 CP3/CP4 approved 后 | S01..S06 各自 LLD 和 CP5 自动预检 | 可按 `max_parallel_lld=3` 分轮写 LLD；但 CP5 必须等六份 LLD 全量确认。 |
| CR008 implementation handoff: S01 / S02 | CR008 CP5 approved 后 | 每个 Story 独立 handoff；涉及 `experiments/**` / report metadata / benchmark field separation | 与 CR007-S04 文件冲突，必须串行；冲突时 CR008 为主。 |
| CR008 implementation handoff: S03 / S04 / S06 | CR008 CP5 approved 后 | 每个 Story 独立 handoff；`engine/research_dataset.py` 只能同时由一个 Story 写入 | CR008 内部串行或由 meta-po 指定 merge owner；不得一个 meta-dev 线程跨 Story 混写。 |
| CR008 implementation handoff: S05 / S06 readers 部分 | CR008 CP5 approved，且 CR007-S02/S03 readers 合同清理后 | 每个 Story 独立 handoff；`market_data/readers.py` 写入需独占 | 与 CR007-S02/S03 必须串行。 |

## 9. 最终交付结论

- `CR007-S02` 仍可立即实现，且推荐继续由主线程复用 `dev-zhang` 执行既有 S02 handoff。
- `CR007-S03` 暂停到 S02 CP6 PASS 且 CR008 research dataset / PIT universe 设计影响结论明确；不建议仅凭 S02 CP6 直接开工。
- `CR007-S04` 与 `CR007-S05` 均暂停，等待 CR008 设计影响结论；二者最容易因 benchmark/report/docs 口径被 CR008 覆盖或修订。
- CR008 当前只允许设计、LLD 准备前置分析和验证策略分析；CP5 批次人工确认前不得实现任何 CR008 代码、测试或文档产物。
- 后续 meta-dev 调度应保持单 Story 独立 handoff；对 `market_data/readers.py`、`market_data/benchmarks.py`、`experiments/run_experiment_13.py`、`engine/research_dataset.py`、README / USER-MANUAL 等共享文件采用串行写入和明确 merge owner。
