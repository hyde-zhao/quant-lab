---
cr_id: "CR-014"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "目标从窗口级 readiness 扩大为 A 股自存在 / 上市日起至今的生产级全历史数据湖，命中需求重定义、数据源权限、外部接口、lake 存储布局、catalog current truth、DuckDB 技术选型、全量回补和多 Story 依赖，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "approved"
created_at: "2026-05-26T22:16:42+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-26T22:24:02+08:00"
source: "user"
approval_text: "process/changes/CR-014-A-SHARE-SINCE-INCEPTION-PRODUCTION-DATA-LAKE-2026-05-26.md  @meta-po 组织分析和实现这个CR"
linked_issue: ""
closed_by: "user"
closed_at: "2026-05-31T21:43:48+08:00"
close_reason: "CR014 Batch-A CP8 已 approved；S09 真实数据湖执行证据已拆分为后续真实运行 / CR018 / CR029 链路，当前 CR014 since-inception 架构与 Batch-A 交付关闭。"
---

# CR-014 A 股自存在日起至今生产级全历史数据湖与 DuckDB 查询层评估

## 变更描述

用户将数据湖目标明确为 **生产级全历史数据湖**，且全历史范围不是 `2020-01-01..2024-12-31`，而是 **A 股证券从实际存在 / 上市日起至当前交易日** 的可审计 current truth。用户同时要求评估是否需要引入 DuckDB。

本 CR 将 CR-010、CR-012、CR-013 的窗口级成果升级为新的结构性目标：

- 从 `2025-02-11..2026-02-18` limited-window research readiness，升级到 A 股 since-inception-to-present production current truth 目标。
- 从固定 10 个 dataset 的窗口级 pass / blocked 声明，升级到全市场、全生命周期、可持续增量刷新和可回滚的数据湖能力。
- 从 pandas / pyarrow 主导的本地读取与审计，升级到 **Parquet lake + catalog/manifest source of truth + DuckDB read-only query/audit engine** 的候选架构评估。
- 当前只创建 CR 和影响分析，不批准 provider fetch、真实 lake 写入、凭据读取、旧 `data/**` 操作或旧报告覆盖。

### 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| CR-010 limited window 生产化 | `2025-02-11..2026-02-18` 内 10 个 dataset 曾达到 limited-window `production_strict_research` | `process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md` |
| CR-012 readiness 口径修正 | limited-window 10 dataset 最终 `production_strict_target_window_pass`，但不得外推 | `process/changes/CR-012-LIMITED-WINDOW-READINESS-AUDIT-CORRECTION-2026-05-24.md` |
| CR-013 claim boundary | `2020-01-01..2024-12-31` 仍 `research_limited_only`，真实 VWAP / minute / tick / level2 / order-match blocked | `process/changes/CR-013-UNSUPPORTED-DATA-CLAIM-BOUNDARY-2026-05-24.md` |
| 当前代码依赖 | `pyproject.toml` 尚未引入 DuckDB；现有 lake 以 `raw/manifest/canonical/gold/quality/catalog` 分层为事实基线 | `pyproject.toml`、`market_data/lake_layout.py` |

### DuckDB 初始评估结论

| 问题 | 初始结论 | 依据 |
|---|---|---|
| 是否需要 DuckDB | 需要，但应作为查询 / 审计 / 特征抽取引擎 | 全历史 A 股覆盖、PIT join、coverage audit、W3 gate、feature extraction 不适合长期全量 pandas 扫描 |
| 是否用 DuckDB `.duckdb` 文件替代 Parquet lake | 不建议 | 当前项目已有外置 Parquet lake + catalog/manifest；DuckDB 原生库文件在 NAS / 多进程写入场景需谨慎 |
| 推荐定位 | `Parquet lake as source of truth` + `DuckDB read-only query/audit engine` | DuckDB 官方支持 Parquet 多文件读取、projection/filter pushdown、Hive partitioning；并发写 native DB 有约束 |
| 是否立即引入依赖 | 待 HLD / CP3 决策 | 需先冻结存储布局、分区策略、catalog current pointer 和 DuckDB 只读边界 |

官方参考：

- DuckDB Parquet 读写与 pushdown：`https://duckdb.org/docs/lts/data/parquet/overview`
- DuckDB Hive partitioning 与 partition filter pushdown：`https://duckdb.org/docs/current/data/partitioning/hive_partitioning.html`
- DuckDB concurrency 与多进程写入约束：`https://duckdb.org/docs/current/connect/concurrency.html`

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有 limited-window / 研究场景保留；追加 A 股 since-inception production data lake 场景 | `## 修订记录` | pending |
| `process/REQUIREMENTS.md` | 原文档更新 | REQ-083..087 和既有数据湖需求保留；追加全 A 全历史、DuckDB 查询层、持续 current truth、增量刷新需求 | `## 修订记录` | pending |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | CR-010/012/013 章节保留为窗口级基线；追加 CR-014 生产级全历史 companion 设计 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 主 HLD 只同步研究消费契约影响，不下沉生产链路细节 | `## 修订记录` | pending |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | ADR-044..047 保留；追加 DuckDB 角色、Parquet lake source-of-truth、全历史分区、catalog current pointer 决策 | `## 修订记录` | pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | CR010/CR013 Story 保留；追加 CR014 Story 和 Wave | `## 修订记录` | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave 保留；新增 CR014 HLD / LLD / implementation waves | frontmatter / waves | pending |
| `process/TEST-STRATEGY.md` | 原文档更新 | CR-010/012/013 测试策略保留；追加全历史 coverage、DuckDB parity、incremental refresh、claim boundary 验证矩阵 | `## CR-014` 增量章节 | pending |
| `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` | 原文档更新 | 现有 `2020-2024` roadmap 作为被 CR-014 扩展的历史基线保留 | `## 修订记录` 或文首变更记录 | pending |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | limited-window 和 CR-013 blocked 声明保留；新增 CR-014 目标、DuckDB 角色和未授权边界 | 相关状态章节 | pending |
| `pyproject.toml` / `uv.lock` | 待 HLD 决策后更新 | 当前 pandas/pyarrow 依赖作为旧基线；仅在 CP3/CP5 批准 DuckDB 后修改 | 不适用 | pending |
| `market_data/**` / `experiments/**` / `tests/**` | 待 LLD 后更新 | 现有 lake layout、catalog、reader、audit 逻辑保留；按 Story 增量实现 | 不适用 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-010 limited-window data lake productionization | CR-014 A 股 since-inception production lake | 原文保留 + 新 CR 扩展 | CR-010 证明有限窗口可运行，不证明全历史或持续 current truth |
| CR-012 limited-window readiness audit | CR-014 rolling full-history readiness audit | 原文保留 + 新审计策略 | CR-012 的 PIT / available_at / denominator 口径继续复用，但目标窗口改为自存在日起至今 |
| CR-013 full-history / unsupported claim boundary | CR-014 full-history remediation and release program | 原文保留 + 新 roadmap | CR-013 只声明 blocked / roadmap-only；CR-014 才定义如何解除 blocked |
| `raw/manifest/canonical/gold/quality/catalog` lake 分层 | DuckDB read-only query/audit engine | 原文保留 + 增量模块 | DuckDB 不替代事实存储；只读取 Parquet / catalog 生成审计和 gold 输出 |
| JSON catalog current pointer | 版本化 current pointer / DuckDB view registry | 原文保留 + 候选增强 | 是否引入 DuckDB view registry 或 SQL manifest 需 HLD 决策 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、数据湖目标定义、全历史范围、DuckDB 角色 | true | 新增 A 股 since-inception-to-present production lake、持续 current truth、全市场 lifecycle、DuckDB 查询层、增量刷新与审计需求 |
| 场景层 | 是否改变测试矩阵覆盖范围 | full-history audit、PIT universe、W3 gate、DuckDB parity、gold feature extraction | true | 新增全 A coverage、上市 / 退市生命周期、source conflict、incremental refresh、DuckDB vs pandas 对账、read-only query boundary 测试场景 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | HLD-DATA-LAKE、ADR、Story Backlog、Development Plan、LLD 批次 | true | 回退到 requirement-clarification；先由 meta-pm 澄清范围，再由 meta-se 输出 HLD/ADR，CP3 后拆 Story |
| 安全层 | 是否引入新的高风险动作或权限要求 | provider fetch、JQData/Tushare 凭据、真实 lake 写入、旧 `data/**`、DuckDB native DB / NAS 文件锁 | true | 本 CR 创建时不授权真实数据操作；HLD 必须定义 read-only DuckDB 边界、凭据脱敏、NAS 并发与写入锁风险 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、TEST-STRATEGY、readiness reports、DuckDB docs、CR roadmap | true | 后续需要刷新文档、生成新 CP3/CP4/CP5/CP6/CP7/CP8，并保留旧窗口报告只读基线 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - A 股全历史范围：上市日起、存在日起、退市股、代码变更、北交所 / 科创 / 创业板覆盖边界。
  - 正式 dataset 分层：P0 current truth、W3 交易约束、研究增强、真实执行价 / 微观结构数据。
  - DuckDB 角色：只读 query/audit engine、是否允许持久 `.duckdb` cache、是否需要 DuckLake / PostgreSQL catalog 进入备选。
  - 存储布局：Parquet partition keys、run_id 与 trade date 双维度、catalog current pointer、gold 输出策略。
  - 权限：provider fetch、lake write、credential read、旧 `data/**` 对账、旧报告覆盖均需单独授权。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 这是数据湖目标、架构、权限和存储布局重定义 |
| 修改架构、权限、安全边界或平台安装路径 | true | 涉及外置 lake、NAS、DuckDB、provider 凭据、真实写湖和权限门控 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 Tushare/JQData/source registry、catalog/readers/audit/experiments 多模块 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先冻结 HLD/ADR、Story DAG、分区和 DuckDB 技术选型 |
| 是否保持 fast-lane | false | 保持 standard |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR014-FULL-HISTORY-LAKE-BATCH-A`
- 批次范围来源：CR-014 影响分析 / 后续 HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR014-S01-a-share-universe-lifecycle-contract`
  - `CR014-S02-full-history-parquet-layout-and-catalog-current-pointer`
  - `CR014-S03-duckdb-readonly-query-audit-engine-spike`
  - `CR014-S04-p0-full-history-backfill-plan-run-publish-contract`
  - `CR014-S05-full-history-readiness-audit-and-duckdb-pandas-parity`
  - `CR014-S06-execution-vwap-minute-data-contract-decision`
  - `CR014-S07-incremental-refresh-replay-ops-and-retention`
  - `CR014-S08-docs-claim-boundary-and-user-runbook-refresh`
- 批次人工确认稿：`checkpoints/CP5-CR014-FULL-HISTORY-LAKE-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [ ] 用户批准本 CR 进入 requirement clarification / HLD。
  - [ ] meta-pm 完成全历史范围和用户场景澄清。
  - [ ] meta-se 完成 HLD-DATA-LAKE / ADR / Story Plan 并通过 CP3 / CP4。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 若执行真实 provider fetch / lake write / credential read，必须有单独、明确、可审计的用户授权。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并等待审批 | 用户目标、现有 CR-010/012/013、DuckDB 初评 | 本 CR、STATE 更新 | CR 已登记 | 等待用户 approve / 修改 / reject |
| 2 | `meta-pm` | 澄清 A 股全历史范围与成功标准 | 本 CR、README、USER-MANUAL、现有 reports | USE-CASES / REQUIREMENTS 增量 | CP1 / CP2 或本 CR 需求确认 | 交 meta-se |
| 3 | `meta-se` | 输出 HLD / ADR / Story Plan | 需求增量、现有 HLD-DATA-LAKE、DuckDB 官方契约 | HLD-DATA-LAKE 增量、ADR、Story Backlog、Development Plan | CP3 / CP4 | 交 meta-dev LLD |
| 4 | `meta-dev` | 输出 LLD 批次 | HLD / Story Plan / ADR | CR014 全量 LLD、CP5 自动预检 | CP5 人工确认 | 进入实现 |
| 5 | `meta-dev` / `meta-qa` | 分 Wave 实现和验证 | CP5 approved、权限门控 | 代码、测试、reports、CP6、CP7 | CP6 / CP7 | 交文档 |
| 6 | `meta-doc` | 刷新用户文档与 runbook | 验证结果、reports、CR | README、USER-MANUAL、TEST-STRATEGY | 文档收敛 | 交 CP8 |
| 7 | `meta-po` | 终验并关闭 | CP6/CP7/文档结果 | CP8 自动预检与人工审查稿 | CP8 approved | 关闭 CR 或回退 |

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：CP8
- 自动通过条件：
  - [ ] 自动预检结论为 `PASS`
  - [ ] 无 `BLOCKING`
  - [ ] 无 `REQUIRED`
  - [ ] 授权动作明确包含关闭 CR 和 / 或推进 `delivered`
- 授权原文：
- 授权时间：
- 回填要求：若生效，人工审查稿必须标注 `approval_source=user-preauthorized`

## 处理结论

- 审批结论：`closed`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] CP8 已 approved；当前关闭 CR014 Batch-A / since-inception 架构交付，S09 / publish / QMT 仍按后续 CR 门控推进

当前禁止事项：

- 未批准真实 provider fetch。
- 未批准真实 lake 写入。
- 未批准读取、打印、记录或保存 `.env`、token、JQData 用户名 / 密码、NAS 凭据。
- 未批准读取、列出、迁移、复制、比对或删除旧 `data/**`。
- 未批准覆盖旧 `reports/data_lake_readiness_2020_2024/*`、`reports/data_lake_readiness_limited_2025_2026/*` 或其他旧报告证据。
- 未批准修改 `pyproject.toml` / `uv.lock` 引入 DuckDB；该动作必须等 CP3 / CP5 明确批准。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 变更 | `process/changes/CR-010-REALISTIC-PRODUCTION-DATA-LAKE-2026-05-22.md` | limited-window 数据湖生产化基线 |
| 变更 | `process/changes/CR-012-LIMITED-WINDOW-READINESS-AUDIT-CORRECTION-2026-05-24.md` | limited-window readiness 口径修正 |
| 变更 | `process/changes/CR-013-UNSUPPORTED-DATA-CLAIM-BOUNDARY-2026-05-24.md` | full-history / unsupported claim boundary |
| HLD | `process/HLD-DATA-LAKE.md` | 数据湖 companion HLD，后续 CR-014 主要设计承载文档 |
| 代码 | `market_data/lake_layout.py` | 当前 raw / manifest / canonical / gold / quality / catalog 分层 |
| 代码 | `market_data/catalog.py` | 当前 JSON catalog current truth 与 readiness summary |
| 代码 | `market_data/readers.py` | 当前 pandas / parquet reader 与 fail-fast 入口 |
| 文档 | `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` | 现有 2020-2024 roadmap，需被 CR-014 扩展 |
| 外部参考 | DuckDB Parquet docs | `https://duckdb.org/docs/lts/data/parquet/overview` |
| 外部参考 | DuckDB Hive partitioning docs | `https://duckdb.org/docs/current/data/partitioning/hive_partitioning.html` |
| 外部参考 | DuckDB concurrency docs | `https://duckdb.org/docs/current/connect/concurrency.html` |
