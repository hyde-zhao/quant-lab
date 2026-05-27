---
artifact: "CR-005 HLD/ADR/Story Plan hs300_index + Tushare remediation review"
reviewer: "meta-se"
lane: "lane-architecture"
round: 3
status: final
governance_mode: review-gated
created_at: "2026-05-17"
---

# Review Findings

## 1. 审查范围

- 目标对象：`process/HLD.md` §22、`process/ARCHITECTURE-DECISION.md` ADR-013..017、`process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、CR005-S01/S03/S04/S06 Story 卡片、CR-005 变更单、CP3/CP4 预检与人工审查稿。
- 审查目标：评审“本地 `hs300_index` benchmark 缺失时消费方返回 structured `unavailable` / `required_missing`，但数据层需通过显式 Tushare fetch/backfill job 获取并写湖”的架构表达、分层边界、数据准确性和门控完整性。
- 审查依据：`AGENTS.md` Design Review 规则 1/3/5/12、ADR-001/009/013/015/017、CR-005 验收口径、用户本轮新增关注点。

## 2. Findings

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-001 | 严重 | `AGENTS.md` 规则 3/5/12；ADR-013；ADR-015 | HLD 将 `fetch` 定义为显式 Tushare 调用路径，且 `benchmark/read` 定义为只读 `hs300_index` 或 structured unavailable、不联网不补数；ADR-015 和 CR005-S04 同样禁止静默代理/运行时联网。但这些文档没有把 `required_missing` 明确映射为“生成可审计的显式 Tushare `hs300_index` backfill job spec，由数据层 CLI/job 单独执行并写湖”。CR005-S01 只描述通用 fetch/dry-run，CR005-S04 只描述 resolver 缺失状态。 | 当前文档能阻止消费层静默代理，但不能保证数据可用性闭环。实现方可能只交付 unavailable 状态而没有 hs300 回补入口；也可能误把“数据层调用 Tushare”理解为 resolver/实验入口自动联网，破坏离线主路径。建议阻断 CP3/CP4 本轮直接通过，直到 HLD/ADR/Story Plan 补齐该两步契约；同时阻断 CR005-S04/S05 CP5。 | 在 HLD §22.6/§22.7/§22.8、ADR-015、CR005-S01、CR005-S04、CR005-S05 和 CP3/CP4 checklist 中新增明确契约：1. consumer/resolver 只返回 `available` / `unavailable` / `required_missing`，并可携带 `remediation_job_spec` 或等价字段；2. 该 spec 只描述 `target_dataset=hs300_index`、`source=tushare`、`interface=hs300_index.daily` 或 exact 值、`ts_code/index_code=399300.SZ`、date range、lake root、quality policy、dry_run=true 默认，不自动执行；3. 用户显式运行数据层 fetch/backfill job 后，才由 connector/runtime/storage/normalization/validation/catalog 写湖；4. consumer 不 import connector/runtime/storage，不触发网络。 | `process/HLD.md:1060`、`process/HLD.md:1066`、`process/ARCHITECTURE-DECISION.md:290`、`process/stories/CR005-S01-tushare-connector-real-lake-writer.md:73`、`process/stories/CR005-S04-hs300-local-benchmark.md:76` |
| F-002 | 严重 | `AGENTS.md` 规则 2/3/5；数据准确性 / 可用性 | HLD 的 `hs300_index` 最小字段为 `trade_date`、`index_code`、`close`、`pct_chg`、`source`、`source_run_id`、`available_at`；CR005-S02 Story 又把 `hs300_index` 必需字段降为 `close`、`source`、`source_run_id`、`available_at`；CR005-S04 的 metadata 验收只要求 source/status/dataset/quality_status/coverage 5 个字段。CR5-Q2 仍 OPEN，尚未确定价格指数/全收益指数/其他口径。 | `hs300_index` 的 available 路径存在准确性和可解释性不足：同一 dataset 在 HLD 与 Story 字段下限不一致；coverage 无明确分母、缺口列表、交易日历对齐和阈值；benchmark return 的计算口径、指数代码、source interface、schema_version、run lineage、quality policy 未形成强契约。会阻断 CR005-S04 available 真实路径和 Backtrader/实验相对指标可信度；不阻断先交付 structured unavailable。 | 修订 HLD §22.4、ADR-015、CR005-S02/S03/S04：统一 `hs300_index` schema 下限，至少包含 `trade_date`、`index_code`、`close`、`pct_chg` 或可重算 return 的 `pre_close`、`source`、`source_interface`、`source_run_id`、`schema_version`、`available_at`、`adjustment_or_index_policy` / 口径说明；quality/catalog 至少记录 requested_range、available_range、coverage_denominator、missing_trade_dates、duplicate key count、quality_status、thresholds、latest_manifest_run_id；resolver metadata 至少输出 source/status/dataset/index_code/interface/quality_status/coverage/missing_dates/benchmark_policy。CR5-Q2 未关闭前，`available` 真值路径不得进入 CP5 实现，只允许 unavailable 契约和 fixture。 | `process/HLD.md:981`、`process/stories/CR005-S02-tushare-dataset-schema-normalization.md:78`、`process/stories/CR005-S04-hs300-local-benchmark.md:116`、`process/HLD.md:1138` |
| F-003 | 一般 | `AGENTS.md` 规则 5/11/12；CP5 门控 | HLD 建议 CP5 B 批为 `CR005-S03/S04`，但 Story/Plan 又要求 CR005-S04 依赖 CR005-S03 reader/quality contract frozen 或 verified。`DEVELOPMENT-PLAN.yaml` 中 CR005-S04 的 `dev_gate` 只有布尔字段，没有列出 `hs300_index` fetch/backfill job contract、reader quality verified、benchmark status schema frozen 等 required_contracts；CR005-S06 的 required_contracts 也未包含 CR005-S04 benchmark resolver 质量契约，只在 `depends_on` 中列出。 | CP5 批次与 dev_gate 的机器可执行条件不够明确。LLD 可同批评审，但开发必须串行依赖 S03/S04 契约，否则 S04/S06 可能在 benchmark resolver、quality/catalog 或 backfill job 仍未冻结时进入实现。建议不阻断 CP3；若 F-001/F-002 修订后重跑 CP4，应同步修订；未修订前阻断 CR005-S04/S06 CP5 开发门控。 | 在 `DEVELOPMENT-PLAN.yaml` 和 CR005-S04/S06 Story frontmatter 中增加 required_contracts：`CR005-S03 hs300_index reader + quality/catalog verified`、`CR005-S01/S02 explicit hs300_index fetch/backfill job spec frozen`、`benchmark status schema available/unavailable/required_missing frozen`、`CR5-Q2 resolved or available path disabled`。CP5 批次可保留 B=LLD 同批，但需写明 `CR005-S04 dev` 等待 `CR005-S03 verified/contract frozen`；或拆为 B1=S03、B2=S04。 | `process/HLD.md:1133`、`process/DEVELOPMENT-PLAN.yaml:782`、`process/DEVELOPMENT-PLAN.yaml:831`、`process/DEVELOPMENT-PLAN.yaml:960`、`process/stories/CR005-S04-hs300-local-benchmark.md:38`、`process/stories/CR005-S06-backtrader-optional-backend.md:50` |
| F-004 | 轻微 | `AGENTS.md` 规则 3/5；人工门控可审查性 | CP3 人工审查稿已询问“本地 `hs300_index` benchmark 缺失时 structured unavailable / required_missing，不静默代理”，但未询问“是否接受 unavailable 只产生显式 backfill remediation spec，不自动联网；数据层 backfill job 由用户显式触发”。CP4 人工审查稿也未单列 CR005-S04 的 backfill job / resolver 状态契约。 | 人工确认时用户可能只批准“不静默代理”，但没有显式批准“缺失状态如何驱动 Tushare 数据层回补”。这会让后续 CP5 对“自动联网是否允许”的解释空间变大。该项不单独阻断 CP3/CP4，但应随 F-001 一并修订检查点。 | 在 CP3 checklist 新增一项：是否接受 consumer 返回 structured status + remediation spec、不自动联网；在 CP4 checklist 新增一项：是否接受 CR005-S04/S05/S01 的 backfill job 边界、输出字段和 dev_gate。 | `checkpoints/CP3-CR005-HLD-REVIEW.md:52`、`checkpoints/CP4-CR005-STORY-PLAN-REVIEW.md:55` |

## 3. 汇总结论

- blocking_count: 2
- required_count: 1
- optional_count: 1
- recommended_next_action: `revise-and-resubmit`

架构主方向是正确的：connector/runtime/storage/normalization/validation/readers/benchmarks/Backtrader 的分层总体清楚，且“消费方不静默代理、不自动联网”和“Tushare 只进写湖链路”并不矛盾。兼容方式必须被写成两步契约：消费方只返回 structured missing；数据层只在用户显式执行 fetch/backfill job 时调用 Tushare 并写入本地湖。

当前文档尚未把这两个动作之间的机器可执行交接写清楚，也没有把 `hs300_index` available 路径的数据准确性字段、coverage/catalog/quality/resolver metadata 和 CP5 dev_gate 收敛到足够严格。因此建议本轮 CP3/CP4 不直接批准，需由 meta-po 路由修订 HLD §22、ADR-015、CR005-S01/S04/S05、`DEVELOPMENT-PLAN.yaml` 和 CP3/CP4 审查稿后重跑自动预检。即使 CP3/CP4 被人工风险接受，CR005-S04/S06 的 CP5 也必须保持阻断，直到上述 required contracts 冻结。

## 4. 待确认项

- `CR5-Q2`：`hs300_index` benchmark 采用价格指数、全收益指数或其他口径。未确认前，真实 available 路径应禁用或只允许 fixture；structured `unavailable` / `required_missing` 契约可以先设计。
- 是否接受 `required_missing` 响应携带只读 `remediation_job_spec`，由用户显式执行数据层 job，而不是由 resolver/实验/Backtrader 自动触发。
