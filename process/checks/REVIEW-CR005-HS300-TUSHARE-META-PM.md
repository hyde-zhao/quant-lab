---
artifact: "CR-005 hs300_index / Tushare benchmark remediation documents"
reviewer: "meta-pm"
lane: "lane-product"
round: 3
status: final
governance_mode: review-gated
created_at: "2026-05-17"
---

# Review Findings

## 1. 审查范围

- 目标对象：`process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md`、`process/USE-CASES.md`、`process/REQUIREMENTS.md`、`process/HLD.md`、`process/STORY-BACKLOG.md`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md`、`process/stories/CR005-S03-multidataset-quality-catalog-readers.md`、`process/stories/CR005-S04-hs300-local-benchmark.md`、`process/stories/CR005-S06-backtrader-optional-backend.md`
- 审查目标：CR-005 第三轮 `lane-product / requirement review`，重点核对本地 `hs300_index` 缺失时消费层结构化不可用、数据层显式 Tushare 补齐、数据准确性、可用性和框架分层独立性。
- 审查依据：用户新增关注点、`AGENTS.md` Review Gate lane-product 职责、CR-005 文档处理决策、已确认 `USE-CASES.md` / `REQUIREMENTS.md` 基线、HLD / Story Plan / Story 卡片。

## 2. Findings

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-001 | BLOCKING | 需求 / 场景变更追溯、lane-product 需求基线一致性 | CR-005 明确判定需求层和场景层均受影响，且需要新增真实数据 dry-run、分批抓取、质量报告、缺口回补、PIT、复权、Backtrader 输入等场景；但文档处理决策只列出 HLD/ADR/Story/Plan/代码，不包含 `USE-CASES.md` 和 `REQUIREMENTS.md`。现有 `USE-CASES.md` 修订记录停在 2026-05-14 v1.3，现有 `REQUIREMENTS.md` 修订记录同样停在 2026-05-14 v1.3，均未形成 CR-005 的场景和需求基线。 | 当前 HLD 与 Story 已写入 CR005-AC，但正式需求基线没有 `hs300_index`、Tushare 写湖、benchmark resolver、`unavailable/required_missing`、Backtrader optional backend 等可追溯需求。第三轮评审无法认定“变更需求已满足”，CP3/CP4 若直接通过会让后续 LLD/验收依赖 CR 文档散落 AC，而不是 confirmed requirements。 | 先按 CR 增量更新 `USE-CASES.md` / `REQUIREMENTS.md` 并追加修订记录，至少新增或修订：数据层显式 Tushare 补齐场景、消费层缺 benchmark 不自动代理场景、真实 `hs300_index` 口径与质量门需求、消费方 no-network/no-connector 约束需求、Backtrader optional backend 边界需求。然后将 CR005-AC-001..014 映射到正式 R-F/R-C/R-NF 条目。 | `process/changes/CR-005...md:90`、`process/changes/CR-005...md:94`、`process/changes/CR-005...md:95`、`process/USE-CASES.md:17`、`process/USE-CASES.md:24`、`process/REQUIREMENTS.md:14`、`process/REQUIREMENTS.md:21` |
| F-002 | REQUIRED | 用户体验 / 可用性：structured unavailable 必须给出 next action | HLD 关键流程只写“实验和轻量回测只读 `hs300_index` 或返回 structured unavailable；不联网、不补数”。CR005-S04 也覆盖 `available/unavailable/required_missing` 和 no-network，但验收只要求 metadata 至少包含 source、status、dataset、quality_status、coverage，未要求包含可执行补齐建议。S05 的“回补 runbook”被放在 CR5-W4 / P1，晚于 CR005-S04 的 P0 本地基准。 | 消费层不静默代理这一点满足，但用户在 `required_missing` 时仍可能只拿到错误状态，不知道应该运行哪个数据层作业、需要哪些参数、拉取哪个 dataset、如何复查 quality。该缺口直接对应用户新增要求“此时需要让数据层调用 Tushare 获取相关数据”。 | 保持 resolver/实验/Backtrader 不联网，但在 structured result 中增加 `next_action` / `recommended_job` / `target_dataset=hs300_index` / `source=tushare` / `interface=hs300_index.daily` 或 exact interface / `date_range` / `lake_root` / `quality_report_path` / `docs_ref`。同时把 `hs300_index` fetch/backfill plan 或 runbook 提升为 CR005-S04 的 P0 验收或 CR005-S05 的前置 P0 子项，确保缺基准时的用户下一步是“运行数据准备层 Tushare fetch/backfill”，而不是消费层自动联网。 | `process/HLD.md:1066`、`process/HLD.md:1078`、`process/stories/CR005-S04-hs300-local-benchmark.md:76`、`process/stories/CR005-S04-hs300-local-benchmark.md:81`、`process/stories/CR005-S04-hs300-local-benchmark.md:116`、`process/STORY-BACKLOG.md:62`、`process/STORY-BACKLOG.md:63` |
| F-003 | REQUIRED | 数据准确性：指数口径、覆盖和缺口解释必须可验收 | HLD dataset 表将 `hs300_index` 候选接口写为 `index_daily(ts_code='399300.SZ')`，字段含 `close/pct_chg/source/source_run_id/available_at`，但同时把“价格指数/全收益/其他口径”列为 OPEN。CR005-S04 也承认真实基准口径仍需确认；CR005-AC-003 仅要求 canonical 覆盖请求区间、缺口进入 quality report。 | 仅有 coverage 不足以保证数据准确性。沪深 300 价格指数、全收益指数或其他复权/收益口径会显著影响相对收益、超额收益和对照报告解释；如果缺口只“进入 quality report”但没有缺口原因、交易日分母、口径字段和可用性判定阈值，消费方可能拿到 nominally available 但语义不可比的 benchmark。 | 在需求/AC/S04 中补充 P0 验收：`benchmark_kind`（price_index / total_return / other）、`index_code`、Tushare source interface、交易日历分母、覆盖起止、missing trade dates、gap reason、是否允许非交易日缺口、quality threshold、`quality_status` 与 `benchmark_status` 的映射。`CR5-Q2` 未解决前只能交付 resolver 与 unavailable 结构；任何 `available` 真实路径必须阻塞到口径决策完成。 | `process/HLD.md:978`、`process/HLD.md:981`、`process/HLD.md:1137`、`process/HLD.md:1138`、`process/stories/CR005-S04-hs300-local-benchmark.md:66`、`process/stories/CR005-S04-hs300-local-benchmark.md:83`、`process/stories/CR005-S04-hs300-local-benchmark.md:124`、`process/changes/CR-005...md:159` |
| F-004 | RECOMMENDED | 分层独立性：明确“数据层调用 Tushare”指 `market_data` 写湖 / 数据准备层，不是消费 Data Loader | CR 文档和 HLD已经明确 Data Loader、实验十/十二、Backtrader 不直接调用 Tushare；S01 禁止修改 `engine/data_loader.py`、`engine/backtest.py`、`experiments/**`、`market_data/readers.py`；S03/S04/S06 均限制 reader/resolver/Backtrader 不导入 connector 或联网。用户新增表述“数据层调用 Tushare”容易被误读为 `engine/data_loader.py` 或 benchmark resolver 在缺失时自动 fetch。 | 架构边界总体合理，但术语不够硬会在 LLD/实现阶段产生误解：有人可能把 next action 做成 resolver 内部自动补数，破坏消费只读边界；也有人可能不敢提供任何补齐入口，导致可用性不足。 | 在 HLD、S04 和后续 REQUIREMENTS 中统一术语：`market_data write-lake / data-prep layer` 才允许显式调用 Tushare；`engine/data_loader.py`、experiments、benchmark resolver、Backtrader 均属于 read-only consumer。`required_missing` 的 next action 只能返回数据准备作业建议，不得在消费调用栈内执行 fetch。 | `process/changes/CR-005...md:31`、`process/changes/CR-005...md:34`、`process/changes/CR-005...md:142`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md:25`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md:84`、`process/stories/CR005-S03-multidataset-quality-catalog-readers.md:86`、`process/stories/CR005-S04-hs300-local-benchmark.md:112`、`process/stories/CR005-S06-backtrader-optional-backend.md:94` |
| F-005 | OBSERVATION | 框架分层独立性 / Backtrader 边界 | HLD 选择 CR5-A，明确 Tushare 写湖、Pandas 数据层 PIT/复权、Backtrader 只读 optional backend；S06 dev_gate 依赖 S02/S03/S04，且禁止读取 token、导入 connector/runtime/storage、生成 PIT、计算复权因子或联网补数。 | 对“Backtrader、实验、Data Loader 是否保持只读消费，不直接联网”的评审结论为基本满足。当前缺口不在分层方向，而在需求基线、缺失时 next action、指数口径和质量 AC 的细化。 | 保留现有后置依赖和 forbidden path；后续 LLD/CP5 继续用静态导入扫描、网络调用计数、凭据扫描和 quality gate fixture 验证。 | `process/HLD.md:957`、`process/HLD.md:973`、`process/HLD.md:974`、`process/HLD.md:1086`、`process/stories/CR005-S06-backtrader-optional-backend.md:10`、`process/stories/CR005-S06-backtrader-optional-backend.md:94`、`process/stories/CR005-S06-backtrader-optional-backend.md:144` |

## 3. 汇总结论

- blocking_count: 1
- required_count: 3
- recommended_count: 1
- observation_count: 1
- recommended_next_action: `revise-and-resubmit`

CR-005 文档在架构方向上基本正确：消费侧缺少 `hs300_index` 时不静默代理，Data Loader / 实验 / Backtrader 也保持只读本地数据、不直接联网。主要问题是产品与需求基线没有吸收 CR-005，导致新增关注点仍停留在 CR/HLD/Story 层；同时 `required_missing` 的用户下一步不够可执行，`hs300_index` 的价格指数 / 全收益口径、覆盖分母和缺口解释没有形成足够强的验收条件。

本轮 `lane-product / requirement review` 结论：**不建议按“已满足变更需求”通过**。建议先完成需求和场景的增量修订，并补强 CR005-S04 / 相关 AC，再提交下一轮评审或让 meta-po 更新 CP3/CP4 审查稿。

## 4. 待确认项

- `CR5-Q2`：`hs300_index` 的真实 benchmark 采用价格指数、全收益指数还是其他口径。
- `hs300_index` 缺失时 structured result 的 next action 字段是否作为 P0 验收项进入 CR005-S04。
- `hs300_index` Tushare fetch/backfill runbook 是并入 CR005-S04，还是把 CR005-S05 的对应部分提升为 CR005-S04 前置 P0 子项。

## Recommendations

- 以 CR-005 为来源，增量更新 `USE-CASES.md`：新增或修订一个“本地 benchmark 缺失后的只读消费与数据准备补齐”场景，明确两条路径：消费层只返回 `unavailable/required_missing`，数据准备层由用户显式触发 Tushare fetch/backfill。
- 增量更新 `REQUIREMENTS.md`：新增正式需求和 AC，覆盖 `hs300_index` 本地基准、Tushare 写湖补齐作业、结构化 next action、指数口径、coverage / quality / gap explanation、consumer no-network/no-connector、Backtrader optional backend 边界。
- 修订 CR005-S04：把 `required_missing` 的输出从“只有状态”升级为“状态 + 可执行补齐建议 + quality/catalog 复查路径”，同时明确 resolver 不执行 fetch。
- 在 CR005-S02/S03/S04 的验收中加入 benchmark quality 细节：交易日历分母、覆盖起止、缺失交易日列表、缺口原因、quality threshold、`benchmark_kind`、`index_code`、source interface、`source_run_id`。
- 保留当前分层隔离策略：Tushare 只存在于 `market_data` 写湖 / 数据准备层；Data Loader、实验、benchmark resolver、Backtrader adapter 均不得直接联网或导入 connector。
