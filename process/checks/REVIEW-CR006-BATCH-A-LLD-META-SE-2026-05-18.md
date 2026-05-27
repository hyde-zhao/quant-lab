---
artifact: "CR006-BATCH-A LLD"
reviewer: "meta-se"
lane: "lane-architecture"
round: 1
status: "complete"
governance_mode: "review-gated"
reviewed_at: "2026-05-18T23:20:00+08:00"
conclusion: "PASS_WITH_REQUIRED"
blocking_count: 0
required_count: 2
advisory_count: 2
---

# Review Findings

## 1. 审查范围

- 目标对象：
  - `process/stories/CR006-S01-tushare-first-data-acquisition-runbook-LLD.md`
  - `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter-LLD.md`
  - `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md`
  - `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md`
- 审查目标：CR006-BATCH-A 四份 LLD 的架构一致性、接口/数据流/职责边界一致性、对 CR-006 Tushare-first 变更需求、HLD §23、ADR-018 的覆盖，以及 Story 依赖、DAG、文件所有权和 CP5 后实现顺序合理性。
- 审查依据：
  - `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md`
  - `process/HLD.md#23-cr-006-tushare-first-数据方案增量设计`
  - `process/ARCHITECTURE-DECISION.md#adr-018tushare-first-structured-lake-与运行时消费面分离`
  - `process/STORY-BACKLOG.md`
  - `process/DEVELOPMENT-PLAN.yaml`
  - `checkpoints/CP5-CR006-BATCH-A-LLD-BATCH.md`
  - 四份 CP5 自动预检文件

## 2. Findings

### 2.1 总体结论

结论：`PASS_WITH_REQUIRED`。

四份 LLD 在主架构方向上保持一致：S01 将 Tushare acquisition、raw/manifest 审计、canonical/gold lineage 和 no-old-data 边界收敛为数据层前置契约；S02 只让轻量 engine / experiments 消费 canonical/gold 或由其派生的 external `legacy_flat`；S03 将 Backtrader 限定为 explicit optional backend 且只消费 clean feed；S04 将旧 repo `data/` 固化为 `reference-only` 文档与 guardrail 面。四者均覆盖 HLD §23 和 ADR-018 的核心要求：Tushare structured lake 是新事实源，raw/manifest 仅为审计/复现/质量追溯层，轻量回测和 Backtrader runtime 不直接消费 raw/manifest，旧 `data/**` 不作为 fallback、迁移源或覆盖证明。

未发现 BLOCKING 级别的架构矛盾；但发现 2 个 REQUIRED 问题，建议在 CP5 批量人工批准前由 meta-po 路由对应 Story/meta-dev 修订或明确澄清。另有 2 个 ADVISORY 级别的计划/追溯一致性问题，不阻止本批次继续评审，但建议同步清理，避免后续调度和审计混淆。

### 2.2 Findings 明细

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-001 | REQUIRED | `HLD §23.6`, `ADR-018`, `S03 reader contract` | S03 LLD 同时要求 `market_data/readers.py` 暴露 `read_backtrader_clean_feed(...)`、`validate_backtrader_clean_feed(bundle)`，但 §1/§2.2/§9/§10 又写成“不触发/不调用 fetch/backfill/normalize/validate/read”，并在 `T-S03-NO-FETCH-01` 中要求 `fetch/backfill/normalize/validate/read/write 调用次数为 0`。 | “read/validate” 禁令语义过宽，可能把合法的 clean feed reader 和 adapter 内部 validator 也判为 forbidden，导致实现阶段 either 无法调用 reader，或测试误报，进而与 HLD §23.6 “canonical/gold -> Backtrader clean feed” 契约冲突。 | 修订 S03 LLD：把禁令精确化为“不调用数据层 job 的 fetch/backfill/normalize/revalidate/replay/lake write，不读取 raw/manifest/storage path，不触发真实数据湖 I/O”；同时显式允许 `market_data.readers` 的 read-only clean feed contract 和 `engine/backtrader_adapter.py` 的 in-memory `validate_backtrader_clean_feed`。`T-S03-NO-FETCH-01` 应改为 fail-on-call 数据层 job/runtime/storage 写入入口，而不是禁止 S03 clean reader/validator。建议修订对象：`CR006-S03` LLD 与 S03 CP5 自动预检。 | `process/stories/CR006-S03-backtrader-clean-feed-contract-LLD.md:47`, `:68`, `:123`, `:124`, `:219`, `:239` |
| F-002 | REQUIRED | `Story DAG / dependency_type`, `HLD §23.12`, `CP5 batch scheduling` | Story Backlog 的 CR006-BATCH-A 描述为“开发默认按 S01 -> S02 -> S03/S04，S04 可在 S02/S03 契约冻结后收敛”；但 Development Plan 和 S04 LLD frontmatter 将 S04 对 S02/S03 的依赖类型写为 `runtime`，S04 正文又多处称其消费 S02/S03 contract。 | 依赖类型与调度口径不一致。若调度器按 `runtime` 理解，S04 文档/guardrail 可能被错误延后到 S02/S03 实现完成后；若按正文“契约冻结”理解，又与 YAML/frontmatter 不一致，后续 dev_ready 计算和文件所有权门控容易出现分歧。 | meta-po 路由 `CR006-S04` 与计划维护方统一依赖类型：若 S04 只依赖 S02/S03 LLD 合同与边界术语，应把 S04 对 S02/S03 的 dependency_type 调整为 `contract`；若确实需要扫描 S02/S03 已实现源码，应在 S04 LLD §10/§11/§13 明确实现后置条件，并在 Development Plan 中说明 S04 必须晚于 S02/S03 CP6。当前文本更符合 `contract` 依赖。建议修订对象：`process/DEVELOPMENT-PLAN.yaml`、`CR006-S04` Story/LLD，必要时同步 `STORY-BACKLOG.md`。 | `process/STORY-BACKLOG.md:96`, `process/DEVELOPMENT-PLAN.yaml:1242`, `:1249`, `process/stories/CR006-S04-old-data-reference-only-guardrail-LLD.md:27`, `:82`, `:197` |
| F-003 | ADVISORY | `Dependency readiness traceability` | `process/STORY-BACKLOG.md` 阻塞项仍列出 `CR5-BLK-002`、`CR5-BLK-004` 为 OPEN，称 Backtrader 依赖策略和 CR005-S02/S03 quality gate 阻塞 CR005-S06；但 `process/stories/CR005-S06-backtrader-optional-backend.md` 已为 `status: verified`，CR005-S06 LLD 已 `confirmed: true`，且存在 CP6/CP7 完成检查。 | 这不直接推翻 CR006-S03，因为 CR005-S06 Story 和检查文件显示已 verified；但 Backlog 的 OPEN blocker 会削弱 S03 依赖证据的可追溯性，可能让 meta-po 或 reviewer 误判 CR006-S03 的上游依赖仍未满足。 | 建议 meta-po 清理或标注 `CR5-BLK-002`、`CR5-BLK-004`、相关 CR5 open question 为 RESOLVED/SUPERSEDED，并引用 CR005-S06 CP5/CP6/CP7 证据。若这些 OPEN 是有意保留的历史基线，应增加“已被 CR005-S06 verified supersede，不再阻塞 CR006-S03”的说明。 | `process/STORY-BACKLOG.md:153`, `:154`, `:156`, `process/stories/CR005-S06-backtrader-optional-backend.md:5`, `process/stories/CR005-S06-backtrader-optional-backend-LLD.md:8` |
| F-004 | ADVISORY | `Traceability anchors`, `HLD §23` | Development Plan 中 CR006-S02/S03/S04 的 `lld_gate.required_inputs` 使用了 `process/HLD.md#236-集成契约`、`process/HLD.md#2313-gotchas` 等去点号锚点，和文档实际章节 `### 23.6 集成契约`、`### 23.13 Gotchas` 的常见锚点格式不完全一致。 | 锚点不影响 LLD 内容正确性，但会降低 CP5/CP6/CP7 追溯效率；人工或自动链接解析时可能无法跳转到目标章节。 | 建议在下一轮计划清理中统一 HLD §23 锚点格式，例如使用 `process/HLD.md#236-集成契约` 前先验证渲染器实际锚点，或改用章节名文本引用 `process/HLD.md §23.6` / `§23.13`，避免机械链接失效。 | `process/DEVELOPMENT-PLAN.yaml:1157`, `:1216`, `:1266` |

### 2.3 覆盖性核对

| 核对项 | 结论 | 证据 |
|---|---|---|
| CR-006 Tushare-first 事实源 | PASS | S01 §1/§5/§7 冻结 Tushare structured lake、raw/manifest、canonical/gold lineage；S02/S03/S04 均以 canonical/gold/clean feed 作为运行消费面。 |
| HLD §23 raw/manifest audit-only | PASS | S01 明确 raw/manifest 为审计、复现、replay 和质量追溯；S02/S03 禁止 raw/manifest runtime input；S04 文档护栏要求 raw/manifest 不作为回测运行输入。F-001 仅要求收窄 S03 “read/validate”禁令，不改变该结论。 |
| 轻量回测消费边界 | PASS | S02 设计 canonical/gold reader 与 explicit external `legacy_flat`，禁止 repo `data/` 默认 fallback，缺数据返回 typed error / remediation spec。 |
| Backtrader 消费边界 | PASS_WITH_REQUIRED | S03 设计 clean feed、quality/PIT/复权 gate、optional backend 和 no connector/token/raw/manifest；但需修订 F-001 的 reader/validator 禁令措辞。 |
| old data reference-only | PASS_WITH_REQUIRED | S04 设计 README/USER-MANUAL/`.gitignore`/guardrail test 固化 reference-only；但需修订 F-002 的依赖类型，避免调度口径与合同消费口径不一致。 |
| Story DAG 与文件所有权 | PASS_WITH_REQUIRED | S01 -> S02 -> S03 -> S04 的主依赖无环，文件范围基本分离；S02/S03 共享 `market_data/readers.py` 和 `engine/backtest.py`，S03 已要求实现前复核 merge owner/dev_running；S04 dependency_type 需按 F-002 收敛。 |

### 2.4 需 meta-po 路由的 Story / meta-dev

| 路由对象 | 原因 | 建议动作 |
|---|---|---|
| `CR006-S03-backtrader-clean-feed-contract` / 对应 meta-dev | F-001 REQUIRED：reader/validator 允许面与 “read/validate 调用 0 次” 禁令存在语义冲突。 | 要求 meta-dev 修订 S03 LLD 和 CP5 自动预检，精确区分 clean read-only reader / in-memory validator 与 forbidden 数据层 job/runtime/storage 操作。 |
| `CR006-S04-old-data-reference-only-guardrail` / 对应 meta-dev，必要时 meta-se 计划维护 | F-002 REQUIRED：S04 对 S02/S03 的 dependency_type 与正文和 Story Backlog 调度口径不一致。 | 要求修订 S04 LLD/frontmatter 与 Development Plan，统一为 contract 依赖，或明确 runtime 后置条件。 |
| `meta-po` 计划/状态维护 | F-003/F-004 ADVISORY：Backlog 旧 blocker 状态与 CR005-S06 verified 证据不一致；HLD §23 锚点可读性不足。 | 在后续计划清理中更新 blocker 状态、补充 superseded 说明，并校正或规范锚点。 |

## 3. 汇总结论

- blocking_count: 0
- required_count: 2
- advisory_count: 2
- recommended_next_action: `revise-required-findings-and-resubmit`

CR006-BATCH-A 四份 LLD 的架构方向和 CR-006 / HLD §23 / ADR-018 覆盖基本成立。建议不要直接 `approve` 当前 CP5 批次；应由 meta-po 先路由 S03 与 S04 处理两个 REQUIRED findings，完成后再回到 CP5 批量人工确认。

## 4. 待确认项

- `CR006-S03` 是否采用本文建议的精确定义：允许 clean read-only reader 和 adapter 内部 validator，禁止数据层 job/runtime/storage 的 fetch/backfill/normalize/revalidate/replay/lake write 以及 raw/manifest runtime read。
- `CR006-S04` 对 S02/S03 的依赖类型是否统一改为 `contract`；若保留 `runtime`，需要 meta-po 明确 S04 必须晚于 S02/S03 CP6 的调度规则。
