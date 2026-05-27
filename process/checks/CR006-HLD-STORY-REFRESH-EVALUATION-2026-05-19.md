---
artifact: "CR006 HLD / Story Refresh Evaluation"
reviewer: "meta-se"
lane: "lane-architecture"
status: "completed"
created_at: "2026-05-19"
classification: "minor_doc_fix_before_cp5"
hld_refresh_required: false
story_replan_required: false
cp3_rerun_required: false
cp4_rerun_required: false
cp5_should_remain_unapproved: true
implementation_allowed: false
---

# CR006 HLD / Story Refresh Evaluation

## 1. 结论

结论分级：`minor_doc_fix_before_cp5`。

当前 CR-006 HLD、ADR-018、CR006-S01..S04 Story / LLD 已经在架构语义上明确区分三层：

1. acquisition / raw-manifest audit：Tushare 显式数据层 job 写 raw 与 manifest，raw/manifest 只用于采集审计、断点续传、复现、replay 和质量追溯。
2. normalization / quality / catalog / gold：从 raw/manifest 派生 canonical/gold，经过 schema、PIT、复权和 quality gate，catalog 暴露 coverage、quality_status 和 lineage。
3. runtime reader / adapter / feed：轻量 engine 消费 canonical/gold reader 或显式派生的 external `legacy_flat`；Backtrader 消费 quality-gated clean OHLCV/factor/score feed；二者都不直接读取 raw/manifest、token、connector/runtime/storage 或旧 repo `data/`。

这些内容足以作为实现方向和 LLD 输入，不需要刷新 HLD/ADR 并重跑 CP3，也不需要新增、拆分或重制 Story 并重跑 CP4/CP5。

但是，用户追问的数据存储格式和对外接口问题是有效的可读性缺口：HLD §23 已定义层级职责、目录示意和集成契约，但没有在 CR-006 局部集中列出 raw、manifest、canonical、quality、catalog、gold、external `legacy_flat` 的 `format`、`partition/layout`、`primary key`、`required columns`、`lineage fields`、运行时消费方和禁止消费方。相关事实散落在 HLD §21.4、§22.4/§22.6、ADR-011/013/014/018 和 S01/S02/S03 LLD 中。建议在 CP5 人工确认前由 meta-po 路由一个小幅文档澄清动作，生成或补充“数据分层、存储格式与对外接口契约”汇总说明；不改变架构决策、Story 边界、文件所有权、依赖图或 dev_gate。

## 2. 审查范围

本次只读取并核验以下过程文档，不修改 HLD、ADR、Story Backlog、Development Plan、LLD 或代码：

| 类型 | 路径 | 核验重点 |
|---|---|---|
| HLD | `process/HLD.md` | §23 CR-006 Tushare-first 数据方案，必要时对照 §21/§22 数据湖契约 |
| ADR | `process/ARCHITECTURE-DECISION.md` | ADR-018，必要时对照 ADR-011/013/014/016/017 |
| Story Plan | `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml` | CR006-S01..S04、CR006-BATCH-A DAG、文件所有权、门控 |
| LLD | `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md` | acquisition/runbook、raw/manifest、canonical/gold lineage |
| LLD | `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md` | lightweight canonical/gold reader、optional `legacy_flat`、typed error |
| LLD | `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md` | Backtrader clean feed、read-only reader、in-memory validator |
| LLD | `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md` | old repo `data/` reference-only 文档与 guardrail |
| Checkpoint | `process/checks/REVIEW-CR006-BATCH-A-LLD-POST-FIX-2026-05-18.md`、`checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` | 当前 CP5 post-fix 状态、未批准实现 |

安全边界：本次未读取、列出、迁移、复制、比对或删除真实 `data/**`；未读取 `.env`、Tushare token、NAS 凭据或真实私有路径；未执行 Tushare 抓取、真实 lake read/write、normalize、revalidate 或 replay job。

## 3. Evidence

### 3.1 分层边界已经成立

| 证据 | 说明 | 结论 |
|---|---|---|
| HLD §23.1 | 目标写明 raw/manifest 只属于采集审计/复现/质量追溯层，轻量回测消费 canonical/gold 或 external `legacy_flat`，Backtrader 消费 clean feed，旧 `data/` reference-only。 | 三层职责在 HLD 目标层已明确。 |
| HLD §23.3 | 推荐架构总览列出 Tushare Acquisition Job、Normalization / Quality / Catalog、Lightweight Engine Adapter、Backtrader Clean Feed Adapter、Old Data Reference Guardrail。 | 模块边界与依赖方向清晰。 |
| HLD §23.4 | raw、manifest、canonical、quality、catalog、gold、external `legacy_flat`、repo `data/` 均有职责边界和运行时消费方说明。 | 数据层级语义清楚，但字段/格式汇总不够集中。 |
| HLD §23.6 | 集成契约覆盖 Tushare job -> raw/manifest、raw/manifest -> canonical/gold、canonical/gold -> lightweight engine、canonical/gold -> Backtrader clean feed、old data guardrail。 | 对外接口方向、调用时机、输入输出和失败策略已在 HLD 层给出。 |
| ADR-018 | 决策明确 structured lake 承载 raw/manifest/canonical/quality/catalog/gold；raw/manifest 为审计层；runtime 消费 canonical/gold 或 clean feed；旧 `data/` reference-only。 | 架构决策与 HLD §23 一致。 |
| S01 LLD §2/§5/§6/§10/§14 | 冻结 acquisition/runbook、`TushareFirstRunSpec`、ManifestRecord、CanonicalGoldLineage、QualityCatalogStatus、raw/manifest audit-only 和 canonical/gold lineage。 | 采集层到事实数据面的 LLD 输入可执行。 |
| S02 LLD §1/§5/§6/§10/§14 | P0 为 canonical/gold reader；optional `legacy_flat` 默认不交付且只可从 canonical/gold 派生；定义 `LightweightInputRequest` / `LightweightInputResult`、typed errors 和测试。 | 轻量 engine 对外消费接口可执行。 |
| S03 LLD §1/§5/§6/§10/§14 | 定义 Backtrader clean feed bundle、read-only clean feed reader、in-memory validator、forbidden boundary 和 typed statuses。 | Backtrader feed contract 可执行。 |
| S04 LLD §1/§5/§6/§10/§14 | 定义文档与 guardrail 合同：旧 `data/` 不作为 fallback、迁移源、复制源、覆盖证明或测试前提。 | old data reference-only 边界可验证。 |

判断：当前设计已经回答“是否区分数据获取层、数据清洗层、对外接口层”。从实现输入角度，不需要重新制定 HLD 架构或 Story DAG。

### 3.2 数据存储格式存在可读性缺口，但不是架构缺口

| 数据对象 | 当前已有事实 | 是否足够实现 | 缺口性质 |
|---|---|---:|---|
| raw | HLD §21.4 给出 raw 路径形态；HLD §23.4/§23.6 定义 raw 为 Tushare 原始响应审计和 replay 输入；S01 LLD 定义 raw checksum、raw_row_count、write_raw / ManifestWriter 交互。 | 是 | CR-006 §23 未集中说明 raw artifact 推荐格式或 extension，仅依赖既有 storage/LLD。 |
| manifest | HLD §21.4、ADR-011 给出 manifest JSONL 和最小字段；HLD §23.4/§23.6 定义 manifest run、source/interface、params、attempts、status、raw_path、canonical_path、lineage；S01 LLD 补充 manifest_run_id、source_interface、raw_checksum、raw_row_count、status。 | 是 | CR-006 §23 未集中列 `format=jsonl`、append-only/idempotency、主键或唯一键口径。 |
| canonical | HLD §21.4 定义 canonical parquet 路径、最小 prices schema；HLD §22.4 定义 Tushare P0 dataset 字段；ADR-011/014 定义 canonical parquet 与 dataset schema；S01/S02 继承。 | 是 | CR-006 §23 只写“统一 schema、类型、主键、available_at、复权字段和 source lineage”，未在 §23 局部列 dataset required columns / key columns。 |
| quality | HLD §21.4、ADR-011/014 定义 quality records / CSV、coverage、字段缺失、重复、异常、PIT/复权 gate；S01/S02/S03 都以 quality gate 作为阻断条件。 | 是 | CR-006 §23 未集中列 quality record format、required fields 和 status enum。 |
| catalog | HLD §21.4、ADR-011 定义 catalog JSON 或 parquet，至少 dataset、schema_version、coverage、quality_status、latest_manifest_run_id；S01 LLD 补充 latest_manifest_run_id、quality_path、source/interface/run lineage。 | 是 | CR-006 §23 未集中列 catalog format 与 discovery fields。 |
| gold | HLD §22.4/§22.6 定义 clean OHLCV/factor/score/benchmark 相关字段和 PIT/复权 gate；HLD §23.4 将 gold 定义为研究/回测稳定面；S02/S03 定义消费接口。 | 是 | CR-006 §23 未集中列 gold dataset 的 format、partition/key、required columns。 |
| external `legacy_flat` | HLD §23.4、§23.6、S02 LLD 定义它仅为 optional 兼容面，从 canonical/gold 派生，外置目录显式传入，带 lineage，不等于旧 repo `data/`。 | 是 | 物理路径 OPEN，且不得记录真实值；这是有意开放，不阻塞当前设计。 |

判断：数据格式不是未定义，而是“定义散落”。如果用户需要在 CP5 前一眼看懂存储契约，应补一张汇总表；该表应派生自已确认的 HLD/ADR/LLD，不新增字段事实。

### 3.3 Story 覆盖充分，不需要重制

| Story | 当前覆盖 | 对用户问题的响应 | 是否需要新增/拆分 |
|---|---|---|---|
| CR006-S01 | Tushare-first acquisition/runbook、raw/manifest audit-only、canonical/gold lineage、quality/catalog handoff、no-old-data 采集边界。 | 覆盖“数据获取层”和 raw/manifest/canonical/gold lineage。 | 不需要。 |
| CR006-S02 | canonical/gold 到轻量 engine reader、optional external `legacy_flat`、typed errors、no repo `data/` fallback、no raw/manifest runtime input。 | 覆盖“轻量引擎对外接口”和 optional flat 兼容面。 | 不需要。 |
| CR006-S03 | Backtrader clean feed bundle、read-only clean feed reader、in-memory validator、quality/PIT/复权 evidence、typed statuses。 | 覆盖“Backtrader 对外接口”和 clean feed contract。 | 不需要。 |
| CR006-S04 | README/USER-MANUAL/.gitignore/guardrail，统一旧 `data/` reference-only、raw/manifest audit-only、canonical/gold runtime surface 术语。 | 覆盖“用户可读说明与误用护栏”。 | 不需要；可承接小幅文档澄清。 |

判断：当前问题不引入新功能、文件所有权或依赖关系。无需新增 Story、拆分 Story、重排 Wave 或重跑 CP4。若 meta-po 认为必须把汇总表固化到正式交付面，优先路由到 S04 文档/guardrail 口径或 CP5 审查说明，而不是新增 S05。

## 4. Findings

| ID | Severity | Evidence | Impact | Recommendation | Checkpoint Impact |
|---|---|---|---|---|---|
| F-CR006-EVAL-001 | 轻微 / CP5 前建议处理 | HLD §23.4 有对象职责和目录示意，但未集中列出 raw/manifest/canonical/quality/catalog/gold/external `legacy_flat` 的 format、layout/partition、primary key、required columns、lineage fields；这些信息分散在 HLD §21.4、§22.4/§22.6、ADR-011/014/018 和 S01/S02/S03 LLD。 | 用户和人工审查人需要跨多处拼接数据存储格式，容易误以为格式或接口未定义。 | 在 CP5 前补一份汇总说明，建议标题为“数据分层、存储格式与对外接口契约”。内容只汇总已有事实，不新增架构决策。 | 不需要 CP3/CP4；建议 CP5 approve 前由 meta-po 确认该说明已纳入审查上下文。 |
| F-CR006-EVAL-002 | 轻微 / 非阻断 | `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` 与 post-fix 聚合均为 `ready_for_user_review`；`process/DEVELOPMENT-PLAN.yaml` 的 CR006-BATCH-A wave status 仍显示 `cp5-required-fixes-pending`。 | 计划状态显示可能让审查人误判 CP5 当前入口；但 Story DAG、依赖、文件所有权未变化。 | 由 meta-po 在后续状态维护中做行政同步即可，不属于 Story replan，不应触发 CP4 重跑。 | 不阻断本次架构结论；若用户选择继续 CP5，可在 meta-po 回填时同步。 |

## 5. 推荐动作

1. 不刷新 HLD/ADR，不重跑 CP3。
2. 不刷新 Story Backlog / Development Plan 的 Story 边界、DAG、文件所有权或并行策略，不重跑 CP4。
3. 不把 CR006-BATCH-A 当前 CP5 回退为全面 `changes_requested`，但在用户当前问题关闭前，不建议直接 `approve` CP5。
4. 建议 meta-po 路由一个 CP5 前小幅文档澄清：
   - 首选：在 `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md` 的审查上下文或相邻 `process/checks/` 说明中加入“数据分层、存储格式与对外接口契约”汇总表。
   - 可选：若用户坚持 HLD 正文必须自包含，则只在 HLD §23 追加一个非决策性“契约汇总表”，内容引用 §21/§22/ADR/LLD 既有事实；该路径会修改 HLD，是否需要重新 CP3 应由 meta-po 按变更治理判定。但从架构角度，本次不建议走 HLD refresh。
   - 可选：若用户坚持 LLD 自包含更强，可在 S01/S02/S03 LLD 各自补一张 cross-reference 表，并重新跑对应 CP5 自动预检；不需要 CP4。
5. 汇总表建议字段：
   - `layer`：acquisition/raw-manifest audit、normalization-quality-catalog-gold、runtime adapter/feed、old data reference-only。
   - `object`：raw、manifest、canonical、quality、catalog、gold、external `legacy_flat`、Backtrader clean feed。
   - `format`：raw artifact、manifest JSONL、canonical/gold parquet、quality CSV/record、catalog JSON/parquet、in-memory feed bundle、optional external flat parquet。
   - `layout / partition`：占位外部 root、dataset/schema_version/date/run_id 等已定义或待 LLD/实现读取现有代码后冻结的口径。
   - `primary key / uniqueness`：manifest run/batch/idempotency key；dataset date+symbol/index_code 等来自 §22.4/LLD 的 exact schema；quality/catalog latest run lineage。
   - `required columns / fields`：只列 HLD §21.4、§22.4、ADR-011/014、S01/S02/S03 LLD 已有字段。
   - `lineage fields`：source、source_interface、source_run_id/run_id、manifest_run_id、schema_version、raw checksum 或 structured missing。
   - `allowed consumers` 与 `forbidden consumers`：normalization/replay、reader/adapter/feed、lightweight engine、Backtrader、old `data/` reference-only 禁令。
   - `typed errors`：required_missing、quality_failed、lineage_missing、pit_failed、adjustment_policy_mismatch、backend_unavailable、interface_not_allowed 等已有错误。

## 6. 是否阻断当前 CP5

当前 CP5 已处于 `ready_for_user_review`，但用户提出的问题本身属于 CP5 人工审查前的合理澄清项。因此建议：

| 问题 | 判断 |
|---|---|
| 是否需要把 CP5 从 `ready_for_user_review` 回退到 `changes_requested` | 不需要全面回退。 |
| 是否建议用户现在直接 `approve` CP5 | 不建议。先由 meta-po 路由轻量澄清，或用户明确接受“相关契约分散在 HLD/ADR/LLD 中，无需补表”后再 approve。 |
| 是否授权实现 | 否。`implementation_allowed` 必须保持 `false`，CP5 未人工批准前不得实现。 |
| 是否需要重新跑 CP5 自动预检 | 只有修改 LLD 或 CP5 审查稿时才需要由 meta-po 判定；若只新增 process/checks 解释性汇总，一般不需要重跑 Story 级 CP5。 |

## 7. 风险

| 风险 | 级别 | 说明 | 缓解 |
|---|---|---|---|
| 用户误以为 raw/manifest 可直接喂回测 | 高 | HLD/ADR/LLD 已禁止，但缺少一张汇总表会降低可读性。 | 在 CP5 前汇总 allowed / forbidden consumers。 |
| 实现者只看 S02/S03 而忽略 S01 lineage | 中 | reader/feed 可能缺少 manifest_run_id、raw checksum 或 quality_status。 | 汇总表明确 lineage fields，S02/S03 实现前复核 S01 contract。 |
| external `legacy_flat` 被误解为旧 repo `data/` | 中 | 当前 HLD/LLD 已说明 optional + derived + external，但用户提问说明仍可能混淆。 | 汇总表将 `legacy_flat` 与 repo `data/` 分行对比。 |
| 为补清晰度过度刷新 HLD/Story | 中 | 若把散点说明误判为架构缺口，可能触发不必要 CP3/CP4 重跑。 | 限定为文档澄清，不改变 Story DAG/文件所有权/dev_gate。 |
| Development Plan wave 状态文案滞后 | 低 | 可能与 CP5 post-fix ready 状态不一致。 | 由 meta-po 后续状态维护同步，不作为 Story replan。 |

## 8. 路由建议

需要 meta-po 路由下游修订：是，但仅限 CP5 前小幅文档澄清或审查上下文补充。

建议路由：

| 路由对象 | 建议动作 | 是否改变设计 |
|---|---|---|
| meta-po | 先把本评估报告加入 CP5 人工审查上下文，提示用户结论分级为 `minor_doc_fix_before_cp5`。 | 否 |
| meta-se | 如用户要求正式补表，由 meta-se 起草“数据分层、存储格式与对外接口契约”汇总，内容只引用现有 HLD/ADR/LLD。 | 否 |
| meta-dev | 仅当决定修改 S01/S02/S03 LLD 时，由对应 Story owner 补 cross-reference 表并重跑相应 CP5 自动预检。 | 否 |
| meta-qa | 若补表进入 CP5 审查上下文，可复核 forbidden consumers、no real data、no credential exposure 是否仍一致。 | 否 |

不建议路由：

- 不建议创建新 Story。
- 不建议拆分 CR006-S01..S04。
- 不建议重制 Story Backlog 或 Development Plan。
- 不建议刷新 ADR-018。
- 不建议在当前 CP5 未获用户批准前进入实现。

## 9. Final Decision Matrix

| 评估项 | 结论 |
|---|---|
| HLD 是否已明确区分 acquisition/raw-manifest audit、normalization-quality-catalog-gold、runtime reader/adapter/feed 三层 | 是，足以作为架构输入。 |
| HLD 对数据存储格式是否足够明确 | 架构事实足够，CR-006 局部汇总不足；建议 CP5 前补汇总说明。 |
| S01/S02/S03/S04 是否覆盖该问题 | 是，四个 Story 覆盖完整，不需新增或拆分。 |
| 是否需要刷新 HLD/ADR 并重跑 CP3 | 不需要。 |
| 是否需要刷新 Story Backlog / Development Plan 并重跑 CP4 | 不需要；最多做状态文案行政同步。 |
| 是否需要让 CP5 从 ready_for_user_review 回退到 changes_requested | 不需要全面回退；但建议先关闭用户澄清项再 approve。 |
| 是否阻断当前 CP5 approve | 是，作为人工审查前澄清阻断；不是架构/Story 重做阻断。 |
| 是否允许实现 | 否。 |

