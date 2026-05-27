---
artifact: "CR-005 hs300_index missing benchmark + Tushare data-layer post-revision QA review"
reviewer: "meta-qa"
lane: "lane-quality"
round: 3
status: "completed"
governance_mode: "review-gated"
created_at: "2026-05-17T18:59:46+08:00"
change_id: "CR-005"
review_mode: true
---

# Review Findings

## 1. 审查范围

- 目标对象：CR-005 第三轮 hs300 / Tushare 正式修订，覆盖 `USE-CASES.md`、`REQUIREMENTS.md`、CR-005、HLD、ADR、Story Backlog、Development Plan、CR005-S01/S03/S04/S06。
- 审查目标：复核第三轮 meta-qa blocking findings 是否已被正式修订关闭，重点检查 structured unavailable/required_missing、显式 Tushare backfill 链路、hs300 quality gate、proxy_baseline 边界、消费层只读分层和 CP5 前测试清单。
- 审查依据：上一轮 `process/checks/REVIEW-CR005-HS300-TUSHARE-META-QA.md`、聚合决策 `process/checks/REVIEW-CR005-HS300-TUSHARE-SUMMARY.md`、本仓库 review gate / meta-qa 质量 lane 规则。
- 写入边界：本文件仅为 QA 复核 findings；未修改 HLD、ADR、Story、Plan、Requirements、Use Cases、STATE 或 CP 检查稿。

## 2. Findings

### 复核结论概览

| 复核重点 | 判定 | 证据摘要 |
|---|---|---|
| `unavailable/required_missing` payload 可操作性 | 基本关闭，仍有 REQUIRED schema 收敛项 | `REQUIREMENTS.md:93-100`、`:227`、CR-005 `:51-56`、HLD `:1054`、`:1061-1100`、S04 `:90-99`、`:137` 已要求 `next_action` / `remediation_job_spec`，并禁止消费层自动执行。 |
| 显式 Tushare fetch/backfill 验收链 | 基本关闭，仍需 CP5 集成测试固化 | UC-07 `:238-245`、CR-005 `:183-187`、HLD `:1104-1111`、Development Plan `:592-608`、S01 `:82-85`、S03 `:118-137`、S04 `:131-145` 已形成 raw/manifest -> canonical/gold -> quality/catalog -> resolver available 的分层链路。 |
| `hs300_index` quality gate | 关闭 | CR-005 `:171-175`、`:186`、HLD `:1123`、`:1136`、S03 `:80-90`、`:120-137` 覆盖 coverage、缺口、重复键、交易日历分母、source lineage、raw checksum 或等价 lineage、quality/catalog 元数据。 |
| `proxy_baseline` 边界 | 未完全关闭 | 主修订已关闭，但 `DEVELOPMENT-PLAN.yaml:547-550` 仍保留“真实基准缺失时结构化提示或降级到既有代理基准”，与 CR-005 新规则冲突。 |
| Data Loader / 实验 / Backtrader typed status | 基本关闭，仍需 LLD 测试显式化 Data Loader 口径 | HLD `:1054`、`:1110`、S04 `:103-107`、S06 `:93-104` 已禁止 fallback / 联网 / 自动补数；但 Data Loader 是“不消费 benchmark”还是“只透传 typed status”需在 LLD 测试中固定。 |
| CP5 前测试清单 | 部分充分，需补一条跨 Story 集成断言 | S01/S03/S04/S06 已分别覆盖 dry-run、quality、resolver status、no-network、proxy 禁止和 Backtrader required_missing；缺少显式 fake backfill 后 resolver 从 missing 变 available 的跨 Story 集成测试条目。 |

### Findings 表

<!-- findings-table -->

| ID | Severity | Rule Ref | Evidence | Impact | Suggestion | Anchor |
|----|----------|----------|----------|--------|------------|--------|
| F-QA-CR005-POST-001 | BLOCKING | `no_silent_proxy_boundary` | CR-005、HLD、ADR 和 CR005-S04 均已要求旧代理只能命名为 `proxy_baseline`，不得填充 `hs300_index`；但 `process/DEVELOPMENT-PLAN.yaml` 的 CR4-W4 完成准则仍写着“真实基准缺失时结构化提示或降级到既有代理基准”。 | 该句仍属于正式 Development Plan 输入，可能让 CP4/CP5 或 STORY-018/CR005-S04 衔接时继续把缺失 hs300 解释成可回退到等权代理 benchmark，直接复活上一轮 blocking finding。 | 在重跑 CP3/CP4 前，将该完成准则改为“真实基准缺失时返回 structured unavailable/required_missing；旧代理如保留只能作为 `proxy_baseline`，不得填充 `hs300_index` 或声明 hs300 相对收益”。该修订应只触及 Development Plan 中旧 CR4-W4 的残留句，不需要重开架构方案。 | `process/DEVELOPMENT-PLAN.yaml:547-550`; `process/changes/CR-005-TUSHARE-5000-DATA-LAYER-REMEDIATION-2026-05-17.md:51-56`; `process/stories/CR005-S04-hs300-local-benchmark.md:103-108` |
| F-QA-CR005-POST-002 | REQUIRED | `cp5_post_backfill_available_test` | UC-07 和 HLD 已描述用户显式执行 backfill 后再次运行消费层应只读更新后的本地数据；S01/S03/S04 的测试分别覆盖 dry-run spec、quality gate 和 available fixture，但没有一个 CP5 前清单条目明确串起 fake Tushare backfill -> raw/manifest -> canonical/gold -> quality/catalog -> resolver available。 | 分层设计可验证，但后续 LLD/实现可能只做单元 fixture，而未证明上一轮要求的数据层显式补齐闭环真的能把 `required_missing` 转成 `available`。 | 在 CP5 LLD 或测试策略中新增一条跨 Story 集成测试：使用 fake Tushare provider 或本地 fixture 显式执行 `hs300_index` backfill job，确认 dry-run 不联网不写湖，显式执行写 raw/manifest，normalization 生成 canonical/gold，quality/catalog 写入 lineage，最后 resolver 从 `required_missing` / `unavailable` 变为 `available`。默认测试仍不得真实联网或需要 token。 | `process/USE-CASES.md:238-245`; `process/HLD.md:1104-1111`; `process/stories/CR005-S01-tushare-connector-real-lake-writer.md:119-134`; `process/stories/CR005-S03-multidataset-quality-catalog-readers.md:118-143`; `process/stories/CR005-S04-hs300-local-benchmark.md:131-145` |
| F-QA-CR005-POST-003 | REQUIRED | `benchmark_result_next_action_schema_consistency` | `REQUIREMENTS.md` 和 CR-005 明确要求缺失时同时携带 `next_action` 与 `remediation_job_spec`；HLD/S04 的字段表主要列出 `remediation_job_spec`，S04 关键验证场景才补充 `next_action.type=run_data_layer_backfill`。 | LLD 作者可能把 `next_action` 当作自由文本展示或可选别名，导致消费方 payload 的机器可解析性不一致。该问题不推翻当前设计，但应在 CP5 前冻结字段表。 | 在 CR005-S04 LLD 中把 `next_action` 列为 `BenchmarkResult` 条件必填字段，至少包含 `type=run_data_layer_backfill`、`target_dataset=hs300_index`、`source=tushare`、date range、dry-run 提示和 runbook/docs ref；`remediation_job_spec` 保持为数据层 job 的机器参数。 | `process/REQUIREMENTS.md:97-100`; `process/REQUIREMENTS.md:227`; `process/HLD.md:1061-1080`; `process/stories/CR005-S04-hs300-local-benchmark.md:86-99`; `process/stories/CR005-S04-hs300-local-benchmark.md:137` |
| F-QA-CR005-POST-004 | RECOMMENDED | `data_loader_benchmark_status_scope` | HLD 把 Data Loader 也列入 Benchmark Consumer；CR005-S04 输出文件不修改 `engine/data_loader.py`，S04/S06 已覆盖实验和 Backtrader，但 Data Loader 对 benchmark status 的最终处理方式未在 Story 测试中单独枚举。 | 如果未来实现者让 Data Loader 临时处理 benchmark 缺失，可能与实验/Backtrader 各自逻辑分叉。当前已有 no-network/no-connector 约束，风险低于 blocking。 | CP5 LLD 中明确 Data Loader 口径：若 Data Loader 不读取 benchmark，则写成“不参与 benchmark fetch/read，只保留本地价格 loader”；若需要披露 benchmark metadata，则只能透传 `BenchmarkResult` typed status，不 fallback、不联网、不读 token。 | `process/HLD.md:1054`; `process/HLD.md:1110`; `process/REQUIREMENTS.md:139-141`; `process/stories/CR005-S04-hs300-local-benchmark.md:103-108` |

### 已关闭的上一轮 blocking 项

| 上一轮问题 | 当前证据 | QA 判定 |
|---|---|---|
| 缺 `next_action` / `remediation_job_spec` | CR-005 `:51-56`、REQ-062 `:227`、HLD `:1054`、`:1082-1100`、S04 `:90-99`、`:137` | 关闭主阻断；保留 F-QA-CR005-POST-003 作为字段表一致性 REQUIRED。 |
| 缺数据层显式 Tushare backfill 作业 | CR-005 `:183-187`、HLD `:1055`、`:1104-1111`、S01 `:82-85`、`:126-133` | 关闭主阻断；保留 F-QA-CR005-POST-002 作为 CP5 集成测试 REQUIRED。 |
| hs300 quality gate 不足 | CR-005 `:171-175`、`:186`、HLD `:1123`、`:1136`、S03 `:80-90`、`:120-137` | 关闭。 |
| 旧路径可能静默代理 | CR-005 `:55-56`、ADR-015 `:292-303`、S04 `:103-108` 已修正，但 Development Plan 残留冲突 | 未完全关闭，见 F-QA-CR005-POST-001。 |
| 消费层可能直接联网或各自 fallback | REQ-064 `:229`、HLD `:1131-1132`、S04 `:145-149`、S06 `:145-152` | 基本关闭；Data Loader 范围建议在 LLD 中显式化。 |
| CP5 前 hs300 专项测试缺失 | S01/S03/S04/S06 已补多数专项测试 | 部分关闭；仍需 post-backfill available 集成断言。 |

## 3. 汇总结论

- blocking_count: 1
- required_count: 2
- recommended_count: 1
- optional_count: 0
- recommended_next_action: `targeted-revision-before-cp3-cp4-rerun`

### 是否可让 meta-po 重跑 CP3/CP4 自动预检

**结论：暂不建议立即重跑。**

CR-005 第三轮修订已经解决了大部分 meta-qa blocking findings，HLD/ADR/CR/Requirements/Use Cases/CR005-S01/S03/S04/S06 的主方向一致，可以作为重跑 CP3/CP4 的基础输入。但 `DEVELOPMENT-PLAN.yaml:547-550` 仍保留“降级到既有代理基准”的旧完成准则，和本轮 `proxy_baseline` 禁止替代 hs300 的规则直接冲突。该项修完后，meta-po 可以重跑 CP3/CP4 自动预检。

### 是否仍需修订

**需要一次小范围修订。**

最低修订范围：

1. 修正 `DEVELOPMENT-PLAN.yaml` 中 CR4-W4 的旧 proxy 句子，明确只能 structured unavailable/required_missing 或显式 `proxy_baseline`，不得作为 hs300 benchmark fallback。
2. 在后续 CP5 LLD / 测试策略中加入 fake backfill 后 resolver available 的跨 Story 集成测试。
3. 在 CR005-S04 LLD 中把 `next_action` 作为 `BenchmarkResult` 条件必填字段冻结，避免字段表和验证场景口径分裂。

## 4. 待确认项

- `CR5-Q2` 仍为 OPEN：沪深 300 使用价格指数、全收益指数或其他口径尚未确认；当前设计正确地阻塞真实 available 最终路径，但不阻塞 unavailable / required_missing 和 dry-run 契约。
- `CR5-Q4` 仍为 OPEN：真实数据 lake root 与 `.gitignore` 策略未确认；不阻塞默认离线测试和 fake backfill 集成测试设计。
