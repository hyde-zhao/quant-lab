---
cr_id: "CR-015"
status: "closed"
impact_level: "high"
workflow_mode_before: "standard"
workflow_mode_after_change: "standard"
fast_lane_upgrade_reason: "QMT 接入引入外部交易接口、Windows 交易节点、broker adapter、OMS、订单状态机、pre-trade risk、broker lake、凭据和审计边界，命中架构、安全、权限、外部接口和多 Story 依赖，必须走 standard。"
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
updated_at: "2026-05-31T21:43:48+08:00"
closed_by: "user"
closed_at: "2026-06-05T23:11:48+08:00"
cp8_manual_status: "approved"
cp8_manual_review: "checkpoints/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
cp8_auto_check: "process/checks/CP8-CR015-CR016-CR017-DELIVERY-READINESS.md"
---

# CR-015 QMT 交易接入基础：Adapter / OMS / Risk / Broker Lake

> 2026-06-05T23:11:48+08:00 关闭记录：用户接受 CP8 推荐方案，CR-015 当前受控离线交付范围关闭。关闭范围仅包含 QMT foundation 的环境边界、adapter 合同、OMS、pre-trade risk、broker lake dry-run writer、shadow order intent 与 runbook；不授权真实 QMT / broker、发单、撤单、账户查询、凭据读取、真实抓取、真实写湖、broker lake 写入、publish、simulation、live_readonly、small_live 或 scale_up。

## 变更描述

用户确认后续会使用 QMT 接口进行模拟盘和实盘，并接受 QMT 决策表中的推荐方案。本 CR 覆盖 **无真实发单的交易接入基础建设**：

- 采用 XtQuant 外部 Python API 作为 QMT 接入主路径。
- 交易服务部署在 Windows + QMT / MiniQMT 节点；当前 Linux / local_backtest 项目继续承担研究、数据湖、信号和审计职责。
- 策略层不得直接调用 QMT 下单接口，必须通过 OMS + QMT adapter。
- 初期只支持普通股票现金账户，不支持信用、多资产、期货、期权。
- 建立本地订单状态机、broker lake、pre-trade risk gate、策略目标组合到订单意图的转换合同。
- 默认只允许 shadow / dry-run / mock adapter；本 CR 不授权真实 `order_stock`、`cancel_order_stock` 或任何真实账户写操作。

## 决策记录

| ID | 决策问题 | 采纳方案 | 影响 |
|---|---|---|---|
| QMT-D1 | QMT 接入方式 | XtQuant 外部 Python API | 保持研究系统与交易节点解耦；需要 adapter 和连接管理。 |
| QMT-D2 | 交易服务部署 | Windows QMT 交易节点 + 当前项目研究/数据湖节点 | 符合 xttrader 运行约束；需要跨节点通信。 |
| QMT-D3 | 策略是否可直接下单 | 不允许，必须经 OMS + adapter | 降低误下单、重复下单和绕过风控风险。 |
| QMT-D5 | 初期账户范围 | 普通股票现金账户 | 降低风控复杂度；信用和多资产延后。 |
| QMT-D6 | 订单状态机 | 必须本地实现 | 支持部分成交、撤单、失败、unknown 和重试审计。 |
| QMT-D7 | broker lake | 必须建立 | 订单、成交、持仓、资产、错误和对账结果可复盘。 |
| QMT-D8 | pre-trade risk | 硬阻断 | 风控失败时不得调用 QMT adapter。 |
| QMT-D9 | 目标权重转订单 | 严格处理 100 股、现金、T+1、可用持仓 | 减少研究目标和真实可执行订单的偏离。 |
| QMT-D11 | 信号与下单数据源 | 数据湖生成信号，QMT 实时数据做下单前校验 | 兼顾可复现和实时可交易状态。 |
| QMT-D14 | 凭据管理 | 交易节点本地配置 / 凭据管理，日志脱敏 | 仓库不保存实盘账户敏感信息。 |
| QMT-D23 | 研究复权口径与交易价格口径 | 信号记录研究 `adjustment_policy`；订单、成交、对账只使用 raw / broker price | 避免把 qfq/hfq 复权价误当真实委托价格；依赖 CR-017 完成双口径数据契约。 |

## 备选方案与优劣摘要

| 决策组 | 方案 | 优点 | 缺点 | 推荐 |
|---|---|---|---|---|
| QMT 接入架构 | XtQuant 外部 API + OMS + adapter | 研究系统和交易节点解耦；风控、审计和 mock 测试可落地 | 需要 adapter、连接管理和跨节点运行约束 | 推荐 |
| QMT 接入架构 | 策略直接调用 QMT API | 实现短 | 风控和审计容易被绕过，重复下单和误下单风险高 | 不推荐 |
| QMT 接入架构 | 直接迁移到完整第三方交易平台 | 交易能力完整 | 会打散当前数据湖、研究和审计资产，迁移成本高 | 暂不采用 |
| 初期账户范围 | 只支持普通股票现金账户 | 风控边界清楚，适合先做模拟盘和小资金实盘 | 信用、多资产能力后置 | 推荐 |
| 初期账户范围 | 一次性支持信用、多资产、期货期权 | 覆盖面广 | 订单规则、保证金、风控和对账复杂度显著上升 | 不推荐 |
| broker lake | 独立外置 broker lake | 交易事实与研究数据湖分层；凭据和账户数据不入仓库 | 需要新增 root、schema 和保留策略 | 推荐 |
| broker lake | 只依赖 QMT 本地日志 | 初期简单 | 不可控、不可复盘，难以做策略级对账 | 不推荐 |
| pre-trade risk | 硬阻断 | 风控失败时不触达 broker API | 可能错过交易机会 | 推荐 |
| pre-trade risk | warn-only | 不影响成交 | 实盘风险不可接受 | 不推荐 |
| 价格口径 | 研究复权口径与交易 raw 价格隔离 | 防止复权价误用于真实下单；与 CR-017 兼容 | order intent 需要多记录 metadata | 推荐 |
| 价格口径 | 直接复用研究 feed 价格下单 | 实现简单 | qfq/hfq 价格不是真实交易价格，可能产生严重实盘错误 | 禁止 |

## 当前基线

| 基线 | 当前事实 | 证据 |
|---|---|---|
| 项目定位 | 当前项目是本地研究回测层，不是完整交易系统 | `README.md` 项目定位 |
| 执行价边界 | 真实 VWAP、分钟、逐笔、盘口、撮合执行价当前保持 blocked | `README.md` CR-013 声明边界 |
| 组合层能力 | 已支持 T 日收盘后信号、T+1 或之后成交、成本、现金和未成交记录 | `engine/portfolio.py`、`README.md` |
| 数据湖事实源 | 真实行情和数据湖 root 外置，`.env` 和真实数据不入库 | `.gitignore`、CR-005 / CR-014 决策 |
| 复权口径 | 当前代码仍以单一 `qfq` 为默认研究口径；QMT 执行必须等待 CR-017 明确 raw/qfq/hfq 边界 | CR-017 |
| QMT 代码 | 当前仓库没有 QMT / xtquant adapter、OMS、broker lake 或真实交易节点 | `rg QMT/qmt/xtquant` 仅命中文档讨论 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `process/USE-CASES.md` | 原文档更新 | 既有研究 / 数据湖场景保留；追加 QMT shadow trading 和交易接入场景 | `## 修订记录` | pending |
| `process/REQUIREMENTS.md` | 原文档更新 | 既有研究需求保留；追加 QMT adapter、OMS、broker lake、risk gate、凭据边界需求 | `## 修订记录` | pending |
| `process/HLD.md` | 原文档更新 | 当前研究架构保留；追加交易接入 companion 架构 | `## 修订记录` | pending |
| `process/ARCHITECTURE-DECISION.md` | 原文档更新 | 既有 ADR 保留；追加 XtQuant 外部 API、Windows 交易节点、OMS 隔离和 broker lake ADR | `## 修订记录` | pending |
| `process/STORY-BACKLOG.md` | 原文档更新 | 既有 Story 保留；追加 CR015 Story | `## 修订记录` | pending |
| `process/DEVELOPMENT-PLAN.yaml` | 原文档更新 | 既有 Wave 保留；新增 CR015 QMT foundation wave | frontmatter / waves | pending |
| `process/TEST-STRATEGY.md` | 原文档更新 | 既有研究 / 数据湖测试保留；追加 QMT mock adapter、状态机、风控、broker lake 测试矩阵 | `## CR-015` 增量章节 | pending |
| `README.md` / `docs/USER-MANUAL.md` | 原文档更新 | 当前“非实盘系统”定位保留；新增 QMT 接入边界和未授权声明 | 相关状态章节 | pending |
| `pyproject.toml` / `uv.lock` | 待 LLD 后更新 | 当前依赖基线保留；仅 CP5 批准后引入 QMT 相关可选依赖或 stub | 不适用 | pending |
| `engine/**` / `market_data/**` / `tests/**` | 待 LLD 后更新 | 当前研究和数据湖代码保留；新增交易边界模块 | 不适用 | pending |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| `README.md` 研究回测定位 | QMT trading foundation 场景 | 原文保留 + 新 CR 扩展 | 当前项目仍不是直接实盘主干；QMT 通过独立 adapter / OMS 边界接入。 |
| `engine.portfolio` 回测成交 | OMS / order intent / broker order | 原文保留 + 新对象 | 回测成交不等同真实委托；真实委托必须有独立状态机和 broker lake。 |
| CR-013 execution blocked claims | QMT pre-trade / broker lake | 原文保留 + 分层解除 | QMT 接入不自动解除真实 VWAP / minute / order-match blocked claim。 |
| `MARKET_DATA_LAKE_ROOT` 外置数据湖 | `BROKER_LAKE_ROOT` 或等价外置 broker lake | 原文保留 + 新外置 root | 真实交易事实不写仓库 `data/**` 或 `reports/**`。 |
| 单一 `qfq` 研究口径 | CR-017 raw/qfq/hfq 分层口径 | 原文保留 + 新 CR 扩展 | OMS 的 order intent 必须记录研究口径，但真实委托、成交和对账只允许 raw / broker price。 |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `REQUIREMENTS.md`、交易接入需求、实盘安全边界 | true | 新增 QMT adapter、OMS、broker lake、risk gate、凭据脱敏、shadow-only 默认需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | shadow trading、mock QMT、订单状态机、风控阻断、broker lake 审计 | true | 新增无真实下单的 adapter contract、状态机、订单意图和风控测试场景。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | HLD、ADR、Story Backlog、Development Plan、LLD 批次 | true | 回退到 requirement-clarification；CP3/CP4/CP5 后才能实现。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | QMT 交易接口、账户凭据、Windows 节点、broker lake | true | 本 CR 不授权真实下单；所有实盘凭据和账户信息不得入库或输出日志。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、USER-MANUAL、TEST-STRATEGY、后续 runbook | true | 需要新增 QMT 接入说明、限制、操作边界和测试策略。 |

## 回退决策

- 影响范围：全局。
- 回退到阶段：`requirement-clarification`。
- 需要重新确认的对象：
  - QMT 外部 API 与交易节点部署边界。
  - OMS / adapter / strategy / data lake 的调用方向。
  - broker lake schema、root 配置和保留策略。
  - pre-trade risk 硬阻断清单。
  - 凭据、账户、日志脱敏和审计边界。

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | false | 这是交易系统接入基础，不是轻量文档变更。 |
| 修改架构、权限、安全边界或平台安装路径 | true | 涉及 Windows 交易节点、账户凭据、QMT adapter 和 broker lake。 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | true | 涉及 XtQuant API、OMS、risk、storage、docs、tests 多模块。 |
| 需要 HLD / LLD 才能解释影响 | true | 必须先冻结交易架构和接口合同。 |
| 是否保持 fast-lane | false | 保持 standard。 |

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：true
- batch_id：`CR015-QMT-FOUNDATION-BATCH-A`
- 批次范围来源：CR-015 影响分析 / 后续 HLD / CP3 / CP4
- 批次内候选 Story：
  - `CR015-S01-qmt-environment-and-interface-spike`
  - `CR015-S02-qmt-broker-adapter-contract`
  - `CR015-S03-oms-order-state-machine`
  - `CR015-S04-pretrade-risk-gate`
  - `CR015-S05-broker-lake-schema-and-writer`
  - `CR015-S06-target-portfolio-to-order-intent-shadow-mode`
  - `CR015-S07-docs-and-foundation-runbook-boundary`
- 批次人工确认稿：`checkpoints/CP5-CR015-QMT-FOUNDATION-BATCH-A-LLD-BATCH.md`
- 开发启动条件：
  - [ ] CR-015 CP2 需求确认通过。
  - [ ] CR-015 CP3 HLD / ADR 通过。
  - [ ] CR-015 CP4 Story Plan 通过。
  - [ ] 批次内全部 Story LLD 已输出。
  - [ ] 批次内全部 Story CP5 自动预检已通过。
  - [ ] 批次 CP5 人工确认结论为 `approved`。
  - [ ] QMT order intent schema 已显式区分 `research_adjustment_policy` 与 `execution_price_policy=raw`。
  - [ ] 任一真实 QMT API 调用、账户查询或 broker lake 写入都必须有单独授权；真实发单必须走 CR-016。

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并登记范围 | 用户确认、QMT 决策表 | 本 CR、STATE 更新 | CR 已登记 | 等待需求澄清 |
| 2 | `meta-pm` | 澄清 QMT foundation 场景 | 本 CR、README、现有 requirements | USE-CASES / REQUIREMENTS 增量 | CP1 / CP2 | 交 meta-se |
| 3 | `meta-se` | 输出 HLD / ADR / Story Plan | 需求增量、QMT 官方接口约束 | HLD、ADR、Story Backlog、Development Plan | CP3 / CP4 | 交 meta-dev |
| 4 | `meta-dev` | 输出 LLD 批次 | HLD / Story Plan / ADR | CR015 LLD、CP5 自动预检 | CP5 | 进入实现 |
| 5 | `meta-dev` / `meta-qa` | 实现和验证 foundation | CP5 approved | mock adapter、OMS、risk、broker lake、CP6/CP7 | 禁止真实发单 | 交 meta-doc |
| 6 | `meta-doc` | 刷新文档 | 实现和验证结果 | README、USER-MANUAL、runbook 边界 | 文档自检 | 交 CP8 |
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

- 未授权真实 `order_stock`、`order_stock_async`、`cancel_order_stock` 或任何真实账户写操作。
- 未授权读取、打印、记录或保存 QMT 账户凭据、资金账号、session、cookie 或交易密码。
- 未授权把 broker lake 写入仓库 `data/**`、`reports/**` 或 Git。
- 未授权解除 CR-013 的真实 VWAP、minute、tick、level2、order-match blocked claim。
- 未授权引入 QMT 相关依赖；依赖变更必须等 CP5。
- 未授权把 qfq/hfq 复权价作为真实 QMT 委托价、成交价或 broker 对账价。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| 上游决策 | QMT-D1..D15 | 用户已接受推荐方案，作为本 CR 输入。 |
| 下游 CR | CR-016 | 模拟盘 / 实盘发单激活、对账、监控、kill switch 和资金放大。 |
| 关联 CR | CR-017 | 复权双视图、研究口径和 QMT raw 执行价格隔离。 |
| 本地提交 | `2aeba1d` | 当前代码基线快照，先于本 CR 创建。 |
