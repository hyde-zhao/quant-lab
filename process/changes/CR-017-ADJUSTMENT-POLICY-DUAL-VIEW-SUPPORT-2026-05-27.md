---
cr_id: "CR-017"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "同时支持前复权和后复权会修改数据湖价格事实源、派生视图、reader API、quality gate、研究默认口径和 QMT 执行价格边界，命中架构、数据契约、外部数据口径和多 Story 依赖，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "closed-cp8-approved"
created_at: "2026-05-27T22:33:51+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-27T22:33:51+08:00"
source: "user"
approval_text: "复权方式前复权和后复权都支持，写入了吗？将CR17写入文档，再检查一下CR15，CR16和CR17是否还有缺失的内容。"
linked_issue: ""
implementation_authorization: false
real_fetch_authorization: false
real_lake_write_authorization: false
depends_on: "CR-014"
related_crs:
  - "CR-015"
  - "CR-016"
updated_at: "2026-05-31T21:43:48+08:00"
closed_by: "user"
closed_at: "2026-06-05T23:11:48+08:00"
cp8_manual_status: "approved"
cp8_manual_review: "checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
cp8_auto_check: "process/checks/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
---

# CR-017 复权双视图支持：前复权 / 后复权 / 原始交易价隔离

> 2026-06-05T23:11:48+08:00 关闭记录：用户接受 CP8 推荐方案，CR-017 当前受控离线交付范围关闭。关闭范围包含 raw prices + adj_factor 事实源合同、qfq / hfq 派生视图、reader policy gate、质量与泄漏验证、consumer 文档和 QMT raw-only 边界；不等于 production adjustment governance / scale-up 解禁，不授权真实抓取、真实写湖、publish、QMT、simulation 或 live。

## 变更描述

用户确认当前数据湖后续需要同时支持 **前复权 `qfq`** 和 **后复权 `hfq`**。本 CR 覆盖复权口径从“单一默认 `qfq`”升级为“原始价格事实源 + 复权因子 + 独立派生视图”的数据湖与研究消费契约。

本 CR 的目标：

- `prices_raw` 保留不复权原始日行情，作为交易、QMT 委托、成交对账和价格审计事实。
- `adj_factor` 保留复权因子事实，记录来源、版本、抓取批次、可用时间和生成口径。
- `prices_qfq` 提供前复权派生视图，必须记录 `as_of_trade_date`，避免前复权历史价格漂移不可追溯。
- `prices_hfq` 提供后复权派生视图，主要服务长期收益、波动率、动量和因子研究。
- `returns_adjusted` 或等价收益率视图作为严肃研究的推荐消费入口，降低价格绝对缩放对研究结论的影响。
- 同一研究 run 仍然只能使用一个明确复权口径；双口径支持通过不同 dataset/view id 表达，不允许在同一 frame 中混合。
- QMT 模拟盘 / 实盘执行不得使用复权价作为真实委托价格，必须使用 QMT 或数据湖原始未复权交易价。

本 CR 不授权：

- 立即修改代码实现。
- 真实抓取或写入生产数据湖。
- 发布新的 `current` pointer。
- 使用复权价格直接生成真实委托价、成交价或 broker 对账价。

## 决策记录

| ID | 决策问题 | 推荐方案 | 接受影响 | 不接受影响 |
|---|---|---|---|---|
| ADJ-D1 | 是否将 `prices_raw` + `adj_factor` 作为复权事实源 | 接受 | 原始交易价和复权计算分离，可复现 qfq/hfq；QMT 执行可坚持 raw 价格 | 若继续只存已复权价，无法可靠派生另一口径，也难以做交易对账 |
| ADJ-D2 | 是否将 qfq / hfq 做成独立派生 dataset/view，而不是同表混合 | 接受 | reader、quality gate 和研究 run 可继续单口径校验，避免混用 | 同表混合会增加误读风险，并破坏现有 `adjustment_policy` 一致性门 |
| ADJ-D3 | 是否要求 qfq 必须携带 `as_of_trade_date` | 接受 | 前复权历史重算有锚点，可解释未来分红送转导致的历史价格变化 | 不接受会导致同一历史日期 qfq 价格随时间变化但不可审计 |
| ADJ-D4 | 是否将 hfq / adjusted returns 作为长期因子研究推荐入口 | 接受 | 更适合收益、波动、动量和回撤研究；价格链不因前复权锚点漂移 | 若继续默认 qfq，研究可做但长期历史价格可复现性和解释成本更高 |
| ADJ-D5 | 是否保留 qfq 作为图表和行情软件人工对照入口 | 接受 | 便于与常见行情软件展示对齐 | 不接受会降低人工核对便利性 |
| ADJ-D6 | 是否强制 QMT 执行、委托、成交和对账只使用 raw / broker 价格 | 接受 | 避免把复权价误当真实交易价格 | 不接受会产生错误委托价格、错误成交核算和真实资金风险 |
| ADJ-D7 | 是否将 `adj_factor` 与完整公司行动审计分层声明 | 接受 | 可以声明“使用复权因子”，但不夸大为“完整公司行动链路可审计” | 不接受会继续混淆复权因子和分红送转配股事件审计 |
| ADJ-D8 | 是否要求公式、字段和 provider 解释在 HLD/ADR 阶段冻结后再实现 | 接受 | 避免把 Tushare / 本地数据口径误解固化进代码 | 不接受会增加 qfq/hfq 计算方向错误和历史回测重跑风险 |

## 备选方案与优劣分析

| 决策问题 | 方案 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| 复权事实源 | A. `prices_raw` + `adj_factor` 为事实源，qfq/hfq 派生 | 可同时支持研究、图表、交易和审计；与数据湖 publish gate 兼容 | 需要新增派生视图、质量校验和 reader API | 推荐 |
| 复权事实源 | B. 只存前复权和后复权成品表 | 读取简单 | 原始交易价和因子链路弱，QMT 对账与重算困难 | 不推荐 |
| 复权事实源 | C. DuckDB `.duckdb` 作为复权事实源 | 查询方便，可集中 view registry | 与 CR-014 Parquet/catalog 事实源决策冲突，迁移和发布复杂度高 | 不推荐 |
| qfq/hfq 输出形态 | A. 独立 dataset/view：`prices_qfq`、`prices_hfq`、`returns_adjusted` | 单口径 reader gate 清晰；不破坏现有混用检测 | dataset 数量增加 | 推荐 |
| qfq/hfq 输出形态 | B. 同一个 `prices` 表用 `adjustment_policy` 分区混存 | 存储路径少 | 消费方容易混用；现有校验会频繁冲突 | 不推荐 |
| qfq 生成方式 | A. 每次 qfq 物化记录 `as_of_trade_date` 和输入 snapshot | 可复现、可解释前复权漂移 | 需要额外 metadata 和 catalog 字段 | 推荐 |
| qfq 生成方式 | B. 永远按最新因子覆盖 qfq | 使用简单 | 历史价格会无声变化，不适合研究审计 | 不推荐 |
| 研究默认口径 | A. 因子研究默认 `returns_adjusted` / `hfq`，图表默认 qfq，交易默认 raw | 不同场景边界清楚 | 文档和 CLI 参数更多 | 推荐 |
| 研究默认口径 | B. 继续统一默认 qfq | 保持旧习惯 | 长历史研究和复现解释成本高；与后复权需求不一致 | 不推荐 |
| 实施顺序 | A. 先 HLD/ADR/Story/CP5，再实现 normalize/reader/validate | 符合门控，减少数据口径返工 | 不能立刻使用 hfq | 推荐 |
| 实施顺序 | B. 先在代码中快速加 `hfq` 参数 | 见效快 | 公式、as-of、quality 和 QMT 边界未冻结，容易污染数据湖 | 不推荐 |

## 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| 默认复权口径 | 当前 ADR 和文档仍写明默认研究口径为 `qfq` | `process/ARCHITECTURE-DECISION.md`、`README.md`、`docs/USER-MANUAL.md` |
| 抓取层 | `prices` 与 `adj_factor` 当前默认或写入 `adjustment_policy=qfq` | `market_data/cli.py` |
| Normalize 层 | 当前只生成一组 `adjusted_open/high/low/close` 和一个 `adjustment_policy` | `market_data/normalization.py` |
| Validate / Reader 层 | 当前对同一数据集执行单一复权口径一致性校验，混合 policy 会被拒绝 | `market_data/validation.py`、`market_data/readers.py` |
| 数据湖架构 | CR-014 已确认 Parquet/catalog 为事实源，DuckDB 只读 | `process/changes/CR-014-A-SHARE-SINCE-INCEPTION-PRODUCTION-DATA-LAKE-2026-05-26.md` |
| QMT 方向 | CR-015/CR-016 已创建，但尚未显式写入研究复权口径与交易原始价格隔离 | `process/changes/CR-015-*.md`、`process/changes/CR-016-*.md` |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有研究 / 数据湖 / QMT 场景保留；追加复权双视图和交易原始价格隔离场景 | `## 修订记录` | pending |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有 `qfq` 默认需求保留为历史基线；追加 raw/qfq/hfq/returns_adjusted 需求 | `## 修订记录` | pending |
| `process/HLD-DATA-LAKE.md` | 原文档更新 | CR-014 数据湖架构保留；追加复权派生层 companion 设计 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 当前研究与数据湖架构保留；追加复权双视图对研究和 QMT 的影响 | `## 修订记录` | pending |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | ADR-003 默认 `qfq` 保留为历史决策；新增或修订 ADR，将默认单口径升级为场景化口径 | `## 修订记录` | pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 保留；追加 CR017 Story | `## 修订记录` | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave 保留；新增 CR017 adjustment policy wave | frontmatter / waves | pending |
| `process/TEST-STRATEGY.md` | 原文档更新 | 既有数据湖和研究测试保留；追加 qfq/hfq parity、as-of、混用阻断和 QMT raw 价格测试矩阵 | `## CR-017` 增量章节 | pending |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 当前 `qfq` 说明保留为历史口径；追加 qfq/hfq/raw/returns_adjusted 使用指南 | 相关状态章节 | pending |
| `process/changes/CR-015-*.md` | 原文档更新 | QMT foundation 基线保留；追加执行价格必须 raw、信号可记录研究复权口径 | 本 CR 交叉引用 | approved-for-intake |
| `process/changes/CR-016-*.md` | 原文档更新 | QMT activation 基线保留；追加 CR017 对真实策略激活和绩效声明的前置关系 | 本 CR 交叉引用 | approved-for-intake |
| `market_data/**` / `engine/**` / `tests/**` | 待 LLD 后更新 | 当前单 qfq 实现保留；CP5 后按 Story 增量改造 | 不适用 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| ADR-003 默认 `qfq` | 场景化复权策略 ADR | 历史决策保留 + 新 ADR 覆盖默认消费策略 | `qfq` 不再是所有研究的唯一推荐口径，而是图表和人工核对默认口径。 |
| `prices` 单一 `adjustment_policy` | `prices_raw` / `prices_qfq` / `prices_hfq` / `returns_adjusted` | 原文保留 + 新 dataset/view | 旧 `prices` 可作为迁移期兼容入口，但严肃研究必须显式选择 view。 |
| `adjusted_*` 单套字段 | 派生视图内单口径 `adjusted_*` | 原文保留 + 分视图承载 | 每个 view 内仍保持单一 policy，避免同表混用。 |
| CR-014 Parquet/catalog 事实源 | 复权派生视图 catalog/publish gate | 原文保留 + 新派生链路 | DuckDB 仍只读，不成为复权事实源。 |
| CR-015 / CR-016 QMT 交易接入 | QMT raw execution price boundary | 原文保留 + 交叉依赖 | 研究可用 qfq/hfq，真实委托和成交必须 raw/broker price。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、复权、研究入口、QMT 执行边界 | true | 新增 raw/qfq/hfq/returns_adjusted、as-of、lineage、混用阻断和 QMT raw 执行需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 复权派生、图表核对、研究回测、QMT 下单前校验 | true | 新增 qfq/hfq 生成、单 run 口径一致、qfq as-of 漂移、交易 raw 价格测试场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | CR014 数据湖、CR015/CR016 QMT、HLD、ADR、Story、LLD | true | 回退到 requirement-clarification；CP3/CP4/CP5 后才能实现。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 真实数据湖写入、current pointer 发布、QMT 委托价格 | true | 本 CR 不授权真实抓取、写湖、发布或发单；执行价必须保持 raw。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、TEST-STRATEGY、研究报告 metadata | true | 更新复权使用指南、口径披露、blocked claims 和回归测试集。 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - `prices_raw`、`adj_factor`、`prices_qfq`、`prices_hfq`、`returns_adjusted` 的 dataset/view 边界。
  - qfq/hfq 公式、provider 字段解释和 `as_of_trade_date` 语义。
  - 研究默认口径、图表默认口径和 QMT 执行口径。
  - 单 run 复权口径一致性 gate 与双视图共存方式。
  - 旧 `qfq` 数据和报告的迁移 / 兼容声明。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 复权双视图会影响数据契约、研究结果和交易价格边界。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 修改数据湖事实源与派生层边界，并影响 QMT 委托价格安全。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 Tushare 数据解释、market_data、engine、docs、tests 和 QMT CR。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先冻结公式、schema、reader 和 publish gate。 |
| 是否保持 fast-lane | false | 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A`
- 批次范围来源：CR-017 影响分析 / 后续 HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR017-S01-adjustment-policy-requirements-and-adr-refresh`
  - `CR017-S02-raw-prices-and-adj-factor-contract-hardening`
  - `CR017-S03-qfq-hfq-derived-view-normalization`
  - `CR017-S04-reader-api-and-policy-gates`
  - `CR017-S05-validation-quality-parity-and-leakage-tests`
  - `CR017-S06-research-qmt-consumer-docs-and-migration-guide`
- 批次人工确认稿：`checkpoints/CP5-CR017-ADJUSTMENT-DUAL-VIEW-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CR-017 CP2 需求确认通过。
  - [ ] CR-017 CP3 HLD / ADR 通过，并冻结 qfq/hfq 公式和 provider 字段解释。
  - [ ] CR-017 CP4 Story Plan 通过。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 任一真实数据湖写入、current pointer 发布或历史数据迁移必须另有显式授权。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记范围 | 用户请求、CR-014/015/016 | 本 CR、STATE 更新、缺口检查 | CR 已登记 | 等待需求澄清 |
| 2 | `meta-pm` | 澄清复权双视图和消费场景 | 本 CR、现有 qfq 文档、QMT CR | USE-CASES / REQUIREMENTS 增量 | CP1 / CP2 | 交 meta-se |
| 3 | `meta-se` | 输出 HLD / ADR / Story Plan | 需求增量、数据湖和 QMT 边界 | HLD、ADR、Story Backlog、Development Plan | CP3 / CP4 | 交 meta-dev |
| 4 | `meta-dev` | 输出 LLD 批次 | HLD / Story Plan / ADR | CR017 LLD、CP5 自动预检 | CP5 | 进入实现 |
| 5 | `meta-dev` / `meta-qa` | 实现和验证双视图 | CP5 approved | normalize/readers/validation/tests/docs 变更、CP6/CP7 | 禁止无授权真实写湖 | 交 meta-doc |
| 6 | `meta-doc` | 刷新用户文档 | 验证结果 | README、USER-MANUAL、migration guide | 文档自检 | 交 CP8 |
| 7 | `meta-po` | 终验并关闭 | CP6/CP7/文档结果 | CP8 审查稿 | CP8 approved | 关闭 CR 或回退 |

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

- 审批结论：`closed-cp8-approved`
- [ ] 自动批准（低风险）
- [x] 用户已于 2026-06-05T23:11:48+08:00 接受 CP8 推荐关闭方案
- [ ] 待人工审批（高风险）

当前禁止事项：

- 未授权修改代码实现、引入依赖或改写现有数据。
- 未授权真实抓取、真实写湖或发布 `current` pointer。
- 未授权把现有 `qfq` 数据批量重算、覆盖或迁移。
- 未授权把复权价作为 QMT 委托价、成交价或 broker 对账价。
- 未授权声明完整公司行动链路可审计；在公司行动数据补齐前，只能声明使用了复权因子。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 上游 CR | CR-014 | 生产级数据湖事实源、catalog、publish gate 和 DuckDB 只读边界。 |
| 关联 CR | CR-015 | QMT foundation 需要记录研究复权口径与 raw 执行价格边界。 |
| 关联 CR | CR-016 | QMT 模拟盘 / 实盘激活需要把 CR017 作为真实策略口径和绩效声明前置。 |
| 代码基线 | `market_data/cli.py`、`market_data/normalization.py`、`market_data/validation.py`、`market_data/readers.py` | 当前单一复权口径实现影响范围。 |
