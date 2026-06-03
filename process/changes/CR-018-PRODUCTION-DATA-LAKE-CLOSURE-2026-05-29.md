---
cr_id: "CR-018"
status: "verified-current-truth-cr029-accepted-s09-later-gated-pending-close"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "用户将最高优先级从 QMT simulation 调整为先完成数据湖 production current truth，命中数据湖完成定义、PIT / W3 数据补齐、外部 provider、真实 lake 写入、catalog publish、rollback、研究重跑和 QMT 后置门控，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "verified-current-truth-cr029-accepted-s09-later-gated-pending-close"
created_at: "2026-05-29T06:42:36+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-29T06:42:36+08:00"
source: "user"
approval_text: "@meta-po 批准D1到D6按照你推荐的方案推进。你可以推进项目了。"
linked_issue: ""
updated_at: "2026-05-31T21:43:48+08:00"
---

# CR-018 数据湖生产级闭环优先级重排与 current truth 收敛

## 变更描述

用户明确批准 D1 到 D6 的推荐方案，并将后续最高优先级调整为：**先把数据湖推进到 production current truth，再进入 QMT 模拟盘**。

本 CR 承接 CR-014 S14 的真实数据湖 candidate 成果，并把 CR-015 / CR-016 / CR-017 的 QMT simulation / live_readonly / small_live / scale_up 继续后置。CR-018 的核心目标是把当前数据湖从“2015 至今 `prices` / `adj_factor` candidate 可用”推进到“可审计、可回滚、可研究重跑、可被正式 reader 消费的 production current truth”。

### 已批准决策

| 决策 ID | 用户批准的推荐方案 | 影响 |
|---|---|---|
| D1 | 最高优先级切换为数据湖 production current truth，QMT simulation 后置 | 后续推进以数据湖 P0/P1 缺口为主线；CR016 simulation/live 解禁不再抢占优先级。 |
| D2 | 新建 `CR018-PRODUCTION-DATA-LAKE-CLOSURE` 承接 CR014 S14 后续生产化 | CR014 保留为 since-inception 架构与 candidate 执行证据；CR018 聚焦生产闭环。 |
| D3 | production current truth 必须先补 PIT / W3 / benchmark / quality，再走 Explicit Publish Gate | 不直接 publish 当前 `prices` / `adj_factor` candidate。 |
| D4 | 真实抓取采用限速窗口化串行，代码 / LLD / 验证 / 文档可并行 | 降低 provider 限流、半失败和审计链断裂风险。 |
| D5 | QMT simulation 必须等数据湖 publish + 研究重跑通过后再启动 | 当前 QMT 只保留 foundation / runbook 受控离线成果，不解禁真实运行。 |
| D6 | 数据湖 publish 后必须先重跑研究，再进入 QMT simulation | 避免把在代理数据下成立、但被 PIT/W3/benchmark 推翻的策略接入交易链路。 |

### 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| CR-014 S14 `prices` / `adj_factor` candidate | 已完成 2015-01-05 至 2026-05-28 全 A `prices` / `adj_factor` raw、manifest、canonical candidate；2768 个开市日、5536 条成功 manifest、`prices` 11311360 行、`adj_factor` 11823057 行，已观测 `prices` 交易对缺失 `adj_factor` 数为 0 | `process/checks/REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29.md` |
| current truth | 未 publish；正式 reader 仍因 `catalog_not_published` 阻断 | CR014 S14 检查记录 |
| DuckDB | 未写 `.duckdb`，未引入 DuckDB 依赖 | CR014 S14 检查记录 |
| PIT / W3 缺口 | PIT universe、退市、ST、停牌、涨跌停、全量 `trade_status`、指数成分 / 权重、行业 / 市值 / 风格、流动性仍未生产闭环 | CR014 S14 Boundary / Risk Notes |
| QMT foundation | CR015/CR016/CR017 受控离线范围已完成，CP8 自动预检 PASS；CR016-S05/S06 later-gated | `checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md`、`process/STORY-STATUS.md` |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 保留 UC-09 全 A since-inception 数据湖场景和 UC-10..UC-12 QMT 场景；新增 CR018 production closure 场景，说明 QMT 后置 | `## 修订记录` | approved |
| `process/REQUIREMENTS.md` | 原文档更新 | 保留 REQ-088..REQ-122；新增 production current truth 收敛、PIT/W3/benchmark、publish/rollback、研究重跑和 QMT 后置需求 | `## 修订记录` | approved |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | 保留 CR014 架构和 S14 candidate 事实；新增 CR018 production closure companion 设计 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 主 HLD 保留研究消费与 QMT 边界；新增“数据湖优先于 QMT simulation”的治理同步 | `## 修订记录` | pending |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 保留 ADR-048..061；新增 CR018 current truth / publish / rollback / QMT 后置 ADR | `## 修订记录` | pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | 保留 CR014/CR015/CR016/CR017 Story；新增 CR018 数据湖生产闭环 Story | `## 修订记录` | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 保留已完成 / pending 批次；新增 CR018 Wave 并将 QMT simulation 解禁置于数据湖后置依赖 | YAML waves / history | pending |
| `process/TEST-STRATEGY.md` | 原文档更新 | 保留 CR014/CR015/CR016/CR017 测试策略；新增 CR018 production current truth、publish/rollback、研究重跑验证策略 | `## CR-018` 增量章节 | pending |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 修正 CR013 已关闭事实；新增 CR018 数据湖优先级和 QMT 后置边界 | 验证状态与限制章节 | pending |
| `market_data/**` / `experiments/**` / `tests/**` | 待 HLD / LLD 后更新 | 保留当前 CR014 candidate、CR017 复权双视图和 CR010/011/012/013 基线 | 不适用 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-014 S14 `prices` / `adj_factor` full-history candidate | CR-018 production current truth closure | 原文保留 + 新 CR 承接 | S14 是生产闭环输入，不等于 current truth；CR018 定义如何补齐 PIT/W3/benchmark 后 publish。 |
| CR-014 Explicit Publish Gate | CR-018 dataset-group publish / rollback gate | 原文保留 + 细化 | CR018 需要把 publish 粒度、rollback smoke 和 current pointer 读写验证落为准入条件。 |
| CR-011 生产级因子研究数据补齐 | CR-018 publish 后研究重跑 | 原文保留 + 扩展 | CR011 已定义研究 gate，CR018 要求以生产 current truth 重跑阶段三到阶段五。 |
| CR-015 / CR-016 / CR-017 QMT foundation 与 staged activation | CR-018 QMT 后置门控 | 原文保留 + 新依赖 | CR018 不推翻 QMT foundation，只阻断 simulation/live 解禁直到数据湖 publish 与研究重跑通过。 |
| CR-013 claim boundary | CR-018 production closure release criteria | 原文保留 + 解除条件 | CR013 的 blocked / unsupported 声明只有在 CR018 对应数据与审计通过后才能解除。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、production current truth 定义、QMT 后置条件 | true | 新增 CR018 需求，明确 current truth 完成定义、PIT/W3/benchmark、publish/rollback、研究重跑和 QMT simulation 后置。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `USE-CASES.md`、数据湖负责人 / 研究审计者 / QMT 运行负责人场景 | true | 新增 production closure 场景，覆盖 candidate -> publish -> research rerun -> QMT admission。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `DEVELOPMENT-PLAN.yaml`、Story DAG、CR015/016 后置依赖 | true | 回退到 requirement-clarification；先由 meta-pm 补需求，再由 meta-se 设计 HLD / ADR / Story Plan。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 外部 provider、真实 lake 写入、catalog publish、QMT simulation | true | 本 CR 创建与需求 / 设计阶段不授权真实抓取、写湖、publish、凭据读取或 QMT simulation；真实执行必须后续 CP5 + per-run 授权。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、TEST-STRATEGY、readiness reports、研究报告 | true | 后续刷新文档、质量报告、publish readiness、rollback 证据和研究重跑报告。 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - production current truth 的准入标准和 dataset group。
  - PIT universe、交易状态、涨跌停、benchmark、指数成分 / 权重、行业市值和流动性数据的 P0/P1 优先级。
  - publish 粒度、rollback 策略和 current pointer 审计字段。
  - 研究重跑通过标准。
  - QMT simulation 解禁条件。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及生产数据湖完成定义和真实数据闭环。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 涉及 provider、lake、catalog publish、rollback、QMT 后置。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 `market_data`、research experiments、QMT stage gate 多模块依赖。 |
| 需要 HLD / LLD 才能解释影响 | true | 需冻结 dataset group、publish gate、quality gate 和研究重跑链路。 |
| 是否保持 fast-lane | false | 必须 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR018-PRODUCTION-DATA-LAKE-CLOSURE-BATCH-A`
- 批次范围来源：CR018 影响分析 / HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR018-S01-production-current-truth-definition-and-dataset-groups`
  - `CR018-S02-pit-universe-lifecycle-st-trade-status-price-limit-backfill`
  - `CR018-S03-real-benchmark-index-components-weights-backfill`
  - `CR018-S04-industry-market-cap-liquidity-and-exposure-data`
  - `CR018-S05-adjustment-dual-view-quality-and-qfq-hfq-publish-readiness`
  - `CR018-S06-production-quality-readiness-audit-and-rollback-gate`
  - `CR018-S07-explicit-publish-gate-and-current-reader-smoke`
  - `CR018-S08-production-current-truth-research-rerun`
  - `CR018-S09-qmt-simulation-admission-boundary-after-data-lake`
- 批次人工确认稿：`checkpoints/CP5-CR018-PRODUCTION-DATA-LAKE-CLOSURE-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CP2 需求基线通过。
  - [ ] CP3 HLD / ADR 通过。
  - [ ] CP4 Story DAG / parallel safety 通过。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 若执行真实 provider fetch / lake write / current pointer publish / QMT simulation，必须有单独、明确、可审计的用户授权。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR018 并记录 D1-D6 批准 | 用户批准文本、CR014 S14 事实、CR015/016/017 CP8 pending | 本 CR、STATE 更新、meta-pm handoff | CR 已登记 | 等待 meta-pm 场景 / 需求增量 |
| 2 | `meta-pm` | 刷新 USE-CASES / REQUIREMENTS 增量建议 | 本 CR、UC-09、REQ-088..122、CR014 S14 检查记录 | UC/REQ 增量建议、CP2 Decision Brief 输入 | 不执行真实数据操作 | 交回 meta-po |
| 3 | `meta-po` | 回填需求增量并发起 CP2 | meta-pm 输出、正式文档 | CP1/CP2 自动预检与 CP2 人工稿 | 用户 CP2 approve | 进入 HLD |
| 4 | `meta-se` | 输出 CR018 HLD / ADR / Story Plan | CP2 approved、CR018 | HLD / ADR / Story Backlog / Development Plan / CP3 / CP4 | 用户 CP3 approve | 进入 LLD |
| 5 | `meta-dev` | 输出 CR018 全量 LLD | CP3/CP4 approved、Story Plan | LLD、CP5 自动预检 | 用户 CP5 approve | 进入实现 |
| 6 | `meta-dev` / `meta-qa` | 按 Wave 实现与验证 | CP5 approved、授权边界 | CP6 / CP7、质量报告、publish / rollback / research rerun 证据 | CP7 PASS | documentation |
| 7 | `meta-doc` / `meta-po` | 文档收敛和 CP8 | 验证结果、状态、文档 | README / USER-MANUAL / TEST-STRATEGY、CP8 | 用户 CP8 approve | 关闭 CR018 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：不适用
- 授权原文：
- 授权时间：
- 回填要求：必须等待用户 CP8 人工确认。

## 处理结论

- 审批结论：`verified-current-truth-cr029-accepted-s09-later-gated-pending-close`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险，但用户已批准进入需求 / 设计推进；真实执行和 publish 仍需后续门控）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| CR | CR-014 | CR018 承接 CR014 S14 full-history `prices` / `adj_factor` candidate。 |
| CR | CR-015 / CR-016 / CR-017 | QMT foundation / simulation / adjustment 进入后置依赖。 |
| 检查记录 | `process/checks/REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29.md` | CR018 的数据湖 candidate 输入事实。 |
| 人工检查点 | `checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md` | QMT 受控离线交付仍 pending，不等于 simulation 授权。 |
