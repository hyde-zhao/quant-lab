---
cr_id: "CR-016"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "QMT 模拟盘 / 实盘激活涉及真实 broker API 发单、撤单、账户查询、对账、监控、kill switch、人工审批、小资金实盘和资金放大，命中高风险权限、外部接口、安全边界和运行治理，必须走 standard。"
rollback_to: "requirement-clarification"
approval_result: "closed-cp8-approved"
created_at: "2026-05-27T22:22:05+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-27T22:22:05+08:00"
source: "user"
approval_text: "同意你推荐的方案，将当前代码提供一个本地commit后，将新需求形成一个或者多个CR"
linked_issue: ""
implementation_authorization: false
real_order_authorization: false
depends_on: "CR-015"
updated_at: "2026-05-31T21:43:48+08:00"
closed_by: "user"
closed_at: "2026-06-05T23:11:48+08:00"
cp8_manual_status: "approved"
cp8_manual_review: "checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
cp8_auto_check: "process/checks/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
---

# CR-016 QMT 模拟盘 / 实盘激活与运行治理

> 2026-06-05T23:11:48+08:00 关闭记录：用户接受 CP8 推荐方案，CR-016 当前受控离线交付范围关闭。关闭范围仅包含 simulation gate、reconciliation、monitoring / kill switch、runbook / approval gate、incident playbook 和 S07 文档；CR016-S05 live_readonly / small_live 与 CR016-S06 scale_up 继续 later-gated、未实现、未验证。关闭不授权真实 QMT / broker、发单、撤单、账户查询、凭据读取、真实抓取、真实写湖、broker lake 写入、publish、simulation、live_readonly、small_live 或 scale_up。

## 变更描述

用户确认后续会使用 QMT 接口进行模拟盘和实盘，并接受推荐的阶段推进路线。本 CR 覆盖 **真实 QMT 发单激活前后的运行治理**，依赖 CR-015 的 adapter / OMS / risk / broker lake 基础。

本 CR 的目标不是立即发真实订单，而是定义从 shadow 到模拟盘、实盘只读、小资金实盘和资金放大的门控：

- `shadow -> QMT 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金`。
- T 日收盘后生成信号，T+1 使用限价 / 保护价执行。
- 盘前、盘中、盘后对账。
- 人工审批、kill switch、暂停 / 恢复 / 手工接管。
- 模拟盘前必须有 runbook。
- 非沪深 300 benchmark、行业 / 市值 / 风格暴露、分钟 / tick / level2 / VWAP、实验注册、资金放大和 PIT 财务数据作为资金放大或生产级声明门槛分层处理。

## 决策记录

| ID | 决策问题 | 采纳方案 | 影响 |
|---|---|---|---|
| QMT-D4 | 推进顺序 | shadow -> 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金 | 每一步都有验收和回滚，不直接从研究进入实盘。 |
| QMT-D10 | 默认执行策略 | T 日收盘后信号，T+1 限价 / 保护价执行 | 成交率可能下降，但能控制追单和滑点风险。 |
| QMT-D12 | 对账频率 | 盘前、盘中、盘后对账 | 及时发现账户、持仓、委托和成交差异。 |
| QMT-D13 | 人工审批与 kill switch | 必须具备 | 支持停止新单、撤可撤单、冻结策略和人工接管。 |
| QMT-D15 | runbook | 模拟盘前必须完成 | 异常处理、审批点和恢复路径可执行。 |
| QMT-D16 | 非沪深 300 benchmark | 不阻断技术模拟盘，阻断真实超额 / 指数增强声明 | 可先验证交易链路；研究结论仍受限。 |
| QMT-D17 | 行业 / 市值 / 风格暴露 | 不阻断小规模模拟盘，阻断扩大资金和独立 alpha 声明 | 交易验证与研究成熟度解耦。 |
| QMT-D18 | 分钟 / tick / level2 / VWAP | 初期不强制，真实执行声明保持 blocked | 降低初期复杂度，但不能声明真实 VWAP / 撮合能力。 |
| QMT-D19 | 初期组合构建 | 等权 / 权重上限 / 换手上限 / 现金安全垫 | 简单可审计；完整优化器后置。 |
| QMT-D20 | 实验注册 | 模拟盘前冻结策略版本、参数和成功 / 失败标准 | 防止边跑边改导致结果不可解释。 |
| QMT-D21 | PIT 财务 / 基本面 | 当前量价主线不强制，使用前再补 | 聚焦交易链路；基本面策略后置。 |
| QMT-D22 | 资金放大 | 阶段放大 | 避免模拟盘通过后一次性扩大资金。 |
| QMT-D24 | 复权口径准入 | 真实策略激活前必须声明研究复权口径，交易执行必须使用 raw / broker price | CR-017 未完成前，可做技术链路模拟，但不得把结果声明为已完成复权口径治理的生产策略。 |

## 备选方案与优劣摘要

| 决策组 | 方案 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| 激活路径 | shadow -> 模拟盘 -> 实盘只读 -> 小资金实盘 -> 放大资金 | 每一步有验收、回滚和责任边界 | 周期更长 | 推荐 |
| 激活路径 | 模拟盘通过后直接实盘 | 速度快 | 缺少只读核对、小资金风险隔离和异常演练 | 不推荐 |
| 激活路径 | 长期只做 shadow / 模拟盘 | 风险最低 | 无法验证真实账户、成交、对账和运行压力 | 仅作降级 |
| 执行策略 | T 日收盘后信号，T+1 限价 / 保护价 | 避免使用未形成数据，控制追单和滑点 | 成交率可能下降 | 推荐 |
| 执行策略 | T 日盘中即时信号即时下单 | 更及时 | 当前分钟/tick/level2 和执行模型不足，容易未来数据或可成交性错误 | 不推荐 |
| 对账 | 盘前、盘中、盘后对账 | 能及时发现持仓、委托、成交和资金差异 | 运维成本较高 | 推荐 |
| 对账 | 只做盘后对账 | 实现简单 | 盘中错误发现太晚 | 不推荐 |
| kill switch | 必须具备停止新单、撤可撤单、冻结策略、人工接管 | 实盘风险可控 | 需要更多运行状态和权限设计 | 推荐 |
| kill switch | 只靠人工停止程序 | 简单 | 事故时不稳定、不可审计 | 不推荐 |
| 复权准入 | CR-017 完成后才允许生产策略声明复权口径治理完成 | 研究信号、绩效和交易价格边界清楚 | 会延后生产级声明 | 推荐 |
| 复权准入 | 不等待 CR-017，沿用 qfq 默认 | 推进快 | 无法支持后复权研究，也容易混淆复权价和交易价 | 不推荐 |

## 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| CR-015 | QMT foundation 尚未实现，本 CR 依赖其 adapter / OMS / risk / broker lake | `process/changes/CR-015-QMT-TRADING-FOUNDATION-2026-05-27.md` |
| 实盘边界 | 当前项目不是完整实盘交易系统 | `README.md` 项目定位 |
| 执行价边界 | 真实 VWAP / minute / tick / level2 / order-match 当前 blocked | `README.md`、`docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` |
| 研究数据 | 全历史 production strict 仍受 CR-014 / S09 后续全量抓取和 publish gate 约束 | `process/STATE.md`、CR-014 |
| 复权口径 | 前复权 / 后复权 / 原始交易价隔离尚需 CR-017；未完成前不得声明生产策略已完成复权口径治理 | CR-017 |
| 操作流程 | 尚无 QMT 模拟盘 / 实盘 runbook、kill switch、对账和资金放大准入 | 当前仓库无 QMT 运行治理文档 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有研究 / 数据湖场景保留；追加模拟盘、实盘只读、小资金实盘和资金放大场景 | `## 修订记录` | pending |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有需求保留；追加 runbook、对账、kill switch、审批、资金放大和生产级声明门槛需求 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 研究架构保留；追加交易运行治理 companion 设计 | `## 修订记录` | pending |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 既有 ADR 保留；追加阶段激活、kill switch、对账、资金放大 ADR | `## 修订记录` | pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 保留；追加 CR016 Story | `## 修订记录` | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave 保留；新增 CR016 activation / ops wave | frontmatter / waves | pending |
| `process/TEST-STRATEGY.md` | 原文档更新 | 既有测试策略保留；追加模拟盘、对账、kill switch、runbook 和资金放大测试矩阵 | `## CR-016` 增量章节 | pending |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 当前限制声明保留；新增 QMT 激活条件、运行手册和实盘禁止事项 | 相关状态章节 | pending |
| `docs/DATA-LAKE-FULL-HISTORY-BACKFILL-ROADMAP.md` | 原文档更新 | CR-013 / CR-014 blocked 声明保留；追加 QMT 执行数据和真实执行 claim 解除条件 | `## 修订记录` | pending |
| `engine/**` / `market_data/**` / `tests/**` | 待 LLD 后更新 | 当前代码保留；新增模拟盘 / 实盘治理模块 | 不适用 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| CR-013 blocked execution claims | QMT activation gate | 原文保留 + 条件解除 | QMT 发单能力不自动解除真实 VWAP / 微观结构 blocked claim。 |
| CR-014 full-history data lake | QMT live signal data readiness | 原文保留 + 依赖声明 | 全历史 production strict 未完成时，只能限制模拟盘 / 小资金范围和声明口径。 |
| CR-015 broker foundation | CR-016 simulation / live activation | CR-015 作为前置 | 没有 adapter / OMS / broker lake / risk gate，不得进入 CR-016 真实发单。 |
| CR-017 adjustment dual-view | QMT production strategy activation gate | CR-017 作为口径前置 | 没有 raw/qfq/hfq 和研究/交易价格隔离，不得声明生产策略复权口径治理完成。 |
| 现有回测报告 | 实盘运行报告 / reconciliation report | 原文保留 + 新报告 | 回测收益不等同模拟盘或实盘收益。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、模拟盘 / 实盘运行需求 | true | 新增 runbook、审批、kill switch、reconciliation、资金放大、实验注册和生产级声明门槛。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | simulation、live-readonly、small-live、monitoring、kill switch、scale-up | true | 新增模拟盘 / 实盘运行验收场景和失败路径。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | CR015 前置、HLD、ADR、Story Backlog、Development Plan | true | 本 CR 依赖 CR-015；必须在 CR-015 CP7 通过后才能进入真实发单激活。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 真实 broker 发单、撤单、账户查询、凭据、实盘资金 | true | 默认不授权；每次真实发单必须有模式、账户、日期、策略、金额上限和审批证据。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、runbook、monitoring docs、测试策略 | true | 新增模拟盘 / 实盘 runbook、故障处理、暂停恢复和资金放大文档。 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - 模拟盘账户和实盘账户边界。
  - 策略版本、参数冻结和调仓日历。
  - 订单价格策略、超时撤单和失败重试规则。
  - 对账差异阈值和处理责任。
  - kill switch 行为：停止新单、撤可撤单、冻结策略、人工接管。
  - 小资金实盘和资金放大的量化门槛。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 涉及真实交易运行和资金风险。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 涉及真实账户、交易权限、审批和 Windows QMT 节点。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 依赖 CR-015 adapter / OMS / broker lake，并新增 ops / monitoring / docs。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须冻结激活路径和运行治理。 |
| 是否保持 fast-lane | false | 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR016-QMT-ACTIVATION-BATCH-A`
- 批次范围来源：CR-016 影响分析 / CR-015 验证结果 / 后续 HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR016-S01-simulation-account-order-enable-gate`
  - `CR016-S02-reconciliation-service-and-reports`
  - `CR016-S03-monitoring-heartbeat-and-kill-switch`
  - `CR016-S04-simulation-live-runbook-and-approval-gates`
  - `CR016-S05-live-readonly-and-small-live-admission`
  - `CR016-S06-scale-up-and-research-maturity-gates`
  - `CR016-S07-docs-user-manual-and-incident-playbooks`
- 批次人工确认稿：`checkpoints/CP5-CR016-QMT-ACTIVATION-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CR-015 foundation Story 已通过 CP7，且 adapter / OMS / risk / broker lake 可用。
  - [ ] CR-016 CP2 需求确认通过。
  - [ ] CR-016 CP3 HLD / ADR 通过。
  - [ ] CR-016 CP4 Story Plan 通过。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] 涉及真实策略激活、绩效归因或生产级声明时，CR-017 至少已完成口径设计并明确研究复权口径与交易 raw 价格隔离；资金放大前必须完成对应实现和验证。
  - [ ] 每次真实 QMT 发单必须另有 per-run 显式授权，覆盖账户、模式、策略、日期、资金上限和回滚策略。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记依赖 | 用户确认、CR-015 | 本 CR、STATE 更新 | CR 已登记 | 等待 CR-015 foundation |
| 2 | `meta-pm` | 澄清模拟盘 / 实盘场景 | 本 CR、CR-015、用户目标 | USE-CASES / REQUIREMENTS 增量 | CP1 / CP2 | 交 meta-se |
| 3 | `meta-se` | 输出 HLD / ADR / Story Plan | 需求增量、CR015 设计和验证结果 | HLD、ADR、Story Backlog、Development Plan | CP3 / CP4 | 交 meta-dev |
| 4 | `meta-dev` | 输出 LLD 批次 | HLD / Story Plan / ADR | CR016 LLD、CP5 自动预检 | CP5 | 进入实现 |
| 5 | `meta-dev` / `meta-qa` | 实现和验证 activation / ops | CP5 approved、per-run 授权边界 | 对账、monitoring、runbook、CP6/CP7 | 禁止无授权真实发单 | 交 meta-doc |
| 6 | `meta-doc` | 刷新用户文档和 incident playbook | 验证结果 | README、USER-MANUAL、runbook | 文档自检 | 交 CP8 |
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
- [x] 用户已于 2026-06-05T23:11:48+08:00 接受 CP8 推荐关闭方案；CR016-S05/S06 仍为 later-gated，未实现、未验证
- [ ] 待人工审批（高风险）

当前禁止事项：

- 未授权任何真实模拟盘 / 实盘订单提交、撤单或账户写操作。
- 未授权读取、打印、记录或保存 QMT 账户凭据、资金账号、session、cookie 或交易密码。
- 未授权把模拟盘或实盘 broker lake 写入仓库 `data/**`、`reports/**` 或 Git。
- 未授权解除真实 VWAP、minute、tick、level2、order-match blocked claim。
- 未授权跳过 CR-015 foundation、CP2/CP3/CP4/CP5/CP6/CP7/CP8 门控。
- 未授权用未声明复权口径的研究结果作为模拟盘 / 实盘准入依据。
- 未授权把 qfq/hfq 复权价作为真实 QMT 委托价、成交价或 broker 对账价。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 上游 CR | CR-015 | QMT adapter / OMS / risk / broker lake foundation。 |
| 关联 CR | CR-017 | 复权双视图、研究口径和 QMT raw 执行价格隔离；生产策略声明与资金放大前置。 |
| 上游决策 | QMT-D4、QMT-D10、QMT-D12、QMT-D13、QMT-D15..D22 | 用户已接受推荐方案，作为本 CR 输入。 |
| 本地提交 | `2aeba1d` | 当前代码基线快照，先于本 CR 创建。 |
