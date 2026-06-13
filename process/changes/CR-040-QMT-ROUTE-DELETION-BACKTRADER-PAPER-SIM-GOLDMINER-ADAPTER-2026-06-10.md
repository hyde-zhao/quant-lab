---
cr_id: CR-040
title: 删除 QMT 路线并转向 Backtrader 参考的本地 Paper Simulation 与掘金量化接口候选路线
status: closed-current-delivery
created_at: 2026-06-10
created_by: codex
owner: meta-po
source: user
change_type: modify-delete-add
impact_level: high
workflow_mode_after_change: standard
activation_policy: "activated by user request after MiniQMT permission proved unavailable"
parent_cr: CR-019
source_decision_id: USER-20260610-NO-MINIQMT-GOLDMINER-ROUTE
related_changes:
  - CR-020
  - CR-021
  - CR-022
  - CR-023
  - CR-024
  - CR-025
  - CR-039
external_reference:
  local_backtrader: "/home/hyde/download/backtrader"
  goldminer_docs_quickstart: "https://www.myquant.cn/docs2/sdk/python/%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B.html"
  goldminer_faq: "https://www.myquant.cn/docs2/faq/"
---

# CR-040 删除 QMT 路线并转向 Backtrader 参考的本地 Paper Simulation 与掘金量化接口候选路线

## 背景与用户决策

用户确认无法获取 MiniQMT 权限，因此原 QMT / MiniQMT / XtQuant 路线不再继续推进。用户要求：

1. 参考 `/home/hyde/download/backtrader`。
2. 完成新的 CR 路线写作。
3. 后续考虑转向掘金量化接口。
4. 将 QMT 相关 CR 全部标记为删除，不再做。

本 CR 不物理删除历史 CR 文件，而是将仍在 active / candidate 的 QMT 路线标记为 `deleted-by-user` / `cancelled-user-deleted`，保留历史审计、设计证据和关闭 / 取消理由。

## 当前基线

| 对象 | 当前事实 | 处理 |
|---|---|---|
| CR-039 | 已完成策略研究候选，最终候选 `strategy_equal_weight_baseline`，准入 `research_baseline`，`simulation_candidate=false` | 保留为策略输入，不授权运行 |
| CR-020 | QMT Windows Gateway 只读接口 CR，CP6 / fixture-static CP7 已 PASS，但卡在 MiniQMT 权限 | 按用户决策标记删除，不再等待权限 |
| CR-021 | QMT simulation 账号接入候选 | 标记删除，不启动 |
| CR-022 | Live-readonly 候选 | 标记删除，不启动 |
| CR-023 | Small-live 候选 | 标记删除，不启动 |
| CR-024 | Scale-up 候选 | 标记删除，不启动 |
| CR-025 | Backtrader optional / execution semantic alignment 已关闭 | 作为本路线的语义参考输入，不复制源码 |

## Backtrader 参考结论

本地 Backtrader 参考目录：`/home/hyde/download/backtrader`。

| 参考对象 | 观察 | 本项目采用方式 |
|---|---|---|
| `README.rst` | Backtrader 是 Python live trading / backtesting platform，支持 data feed、broker simulation、commission、slippage、volume filling、analyzers、orders、positions 等能力 | 作为事件驱动回测 / paper simulation 语义参考 |
| `backtrader/order.py` | 订单对象区分创建数据与执行数据，并记录 execution bits、size、price、commission、pnl、position size / price | 借鉴为本项目 `OrderIntent` / `SimOrder` / `Fill` / `ExecutionBit` 合同 |
| `backtrader/broker.py` | Broker 抽象含 cash/value/position/submit/cancel/buy/sell 等接口 | 借鉴为本项目 `BrokerAdapter` / `PaperBroker` / `GoldminerBrokerAdapter` 分层 |
| `backtrader/position.py` | Position 维护 size、price、opened、closed，支持更新和复制 | 借鉴为本项目 `PositionLedger` 和 reconciliation 输入 |
| `backtrader/strategy.py` | Strategy 以数据 feed、broker、order notification、trade/analyzer 组织事件流 | 借鉴为策略执行 loop 和事件回放，不迁移源码 |

License / no-copy 边界沿用 CR-025 / CR-030：不复制 Backtrader 源码，不迁移 GPL 实现，不把 Backtrader 变成默认主路径；只做语义和测试场景借鉴。

## 外部接口事实约束：掘金量化

当前只建立候选路线，不在本 CR 中接入掘金 SDK。基于 2026-06-10 对官方文档搜索结果的初步核对：

| 来源 | 初步事实 | 处理 |
|---|---|---|
| 掘金量化 Python SDK 快速开始 | 策略形态包含 `init`、`subscribe`、`on_bar`、执行策略等事件式入口 | 后续 Goldminer adapter CR 必须以官方文档和终端实测重新确认 |
| 掘金量化 FAQ | 搜索摘要显示 `gmtrade SDK` 面向仿真和实盘交易，可下单、撤单、查询资金、持仓、委托成交等 | 本 CR 不授权安装、登录、下单或连接；后续另起 adapter 准入 CR |

上述仅为路线规划输入，不是项目内已验证接口合同。

## 五维度影响分析

| 维度 | 影响 | 结论 |
|---|---|---|
| 需求层 | 删除 QMT / MiniQMT / XtQuant 路线，新增 API-less paper simulation 与 Goldminer adapter 候选路线 | high impact，需要标准流程 |
| 场景层 | 从 QMT gateway / simulation / live 阶段门控，转为本地 paper simulation -> broker-neutral adapter -> 掘金候选 adapter | 需要新增场景和验证矩阵 |
| 计划层 | CR020-024 不再推进；后续优先 CR041 paper simulation，再视需要 CR042 Goldminer adapter spike / admission | 需要同步 STATE / CR-INDEX / CR-019 tracking |
| 安全层 | 移除 QMT 真实接口和 MiniQMT 权限等待；Goldminer 后续仍涉及账户、订单、凭据和仿真 / 实盘风险 | 当前不授权任何真实 broker 连接 |
| 交付层 | 新增路线 CR；更新 CR tracking；后续实现会新增 paper broker、ledger、order/fill/equity artifacts | 本 CR 仅路线和状态变更，不实现代码 |

## 文档处理决策

| 文档 | 处理方式 | 旧基线保留 |
|---|---|---|
| `process/changes/CR-020-*.md` | 原文档更新 | 保留全部历史 CP2-CP7 证据，追加删除记录 |
| `process/changes/CR-019-FOLLOW-UP-TRACKING-2026-05-31.md` | 原文档更新 | 保留旧 QMT 路线基线，追加用户删除决策和新路线 |
| `process/STATE.md` | 原文档更新 | 保留历史 CR020 状态与决策队列，tracking 视图移除 active CR020 |
| `process/changes/CR-INDEX.yaml` | 原文档更新 | 保留 CR020-024 索引，状态标记为 deleted / cancelled |
| `scripts/check_cr_tracking_consistency.py` | 原文档更新 | 更新状态守卫，允许 CR020 deleted-by-user 作为合法终态 |
| `docs/QMT-GATEWAY-INSTALL.md` / `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | 暂不更新 | 保留历史手册，不作为后续路线入口 |

## 新路线规划

### Phase 1：CR041 API-less Paper Simulation Runner

目标：在不连接任何 broker 的情况下，把 CR039 `strategy_equal_weight_baseline` 推进到可执行订单意图、模拟成交、持仓账本和净值曲线。

| 能力 | 输出 |
|---|---|
| StrategyAdmissionPackage consumer | 读取 CR039 准入包，只允许 `research_baseline` 输入 |
| Target portfolio generator | 生成目标权重 / 目标股数 |
| Order intent builder | 输出 `order_intents.csv/json`，不是真实订单 |
| Paper broker | 本地撮合、手续费、滑点、涨跌停 / 停牌 / 成交量限制 |
| Position ledger | `positions.csv`、cash、holding、平均成本 |
| Fill ledger | `fills.csv`、partial fill、rejected fill、skip reason |
| Equity report | `equity_curve.csv`、drawdown、turnover、cost、capacity |
| Reconciliation | target vs filled vs position 差异 |

边界：不连接 QMT、不连接掘金、不读取账户、不下单、不撤单、不读取凭据。

### Phase 2：CR042 Broker-Neutral Adapter Contract

目标：抽象 broker 接口，为未来掘金或其他平台做 adapter，而不是把策略绑定到单一 API。

候选接口：

```text
BrokerAdapter
  - capabilities()
  - query_cash()
  - query_positions()
  - query_orders()
  - query_fills()
  - submit_order_intent()
  - cancel_order()
  - normalize_error()
```

第一版可以只实现 `PaperBrokerAdapter`，Goldminer adapter 只写合同与 fixture。

### Phase 3：CR043 Goldminer / 掘金量化 Adapter Spike

目标：在官方文档、SDK、终端和账号权限确认后，做掘金 adapter 可行性 Spike。

必须先决条件：

- 官方 Python SDK / gmtrade SDK 文档重新核对。
- 明确仿真账号和实盘账号边界。
- 明确 token / 登录 / 环境变量 / 终端依赖。
- 明确是否允许查询资金、持仓、委托、成交。
- 明确是否允许仿真下单、撤单。
- 明确脱敏日志、kill switch、per-run authorization。

本 CR 不授权安装、登录、读取账号、下单、撤单或连接掘金终端。

### Phase 4：CR044 Goldminer Simulation Admission

目标：只有在 CR043 Spike PASS 后，才进入掘金仿真交易准入。

必须重新走 CP2 / CP3 / CP5 / CP6 / CP7 / CP8，且逐 run 授权。

## QMT 路线删除范围

| CR | 处理状态 | 说明 |
|---|---|---|
| CR-020 | `deleted-by-user` | 不再等待 MiniQMT；不再做 QMT gateway 实机验证 |
| CR-021 | `cancelled-user-deleted` | 不启动 QMT simulation |
| CR-022 | `cancelled-user-deleted` | 不启动 QMT live-readonly |
| CR-023 | `cancelled-user-deleted` | 不启动 QMT small-live |
| CR-024 | `cancelled-user-deleted` | 不启动 QMT scale-up |

历史已关闭 CR-015 / CR-016 / CR-017 / CR-019 / CR-025 / CR-030 中的 QMT 设计证据作为归档保留，不物理删除；后续不得把这些历史 QMT 设计当作 active 路线。

## Non-Goals

- 不物理删除历史 CR、Story、LLD、CP 或 QMT 代码文件。
- 不实现 paper simulation 代码。
- 不安装或运行 Backtrader。
- 不复制 `/home/hyde/download/backtrader` 源码。
- 不安装、登录或连接掘金量化。
- 不读取任何 broker 凭据。
- 不做真实仿真 / 实盘下单、撤单、账户查询。
- 不声明 CR039 策略 simulation-ready 或 live-ready。

## 验收标准

- [x] CR020-024 在 STATE / CR-INDEX / CR-019 tracking 中均不再是 active / candidate。
- [x] CR020 正式 CR frontmatter 标为 `deleted-by-user`，并追加删除记录。
- [x] 新路线 CR 明确 Backtrader no-copy 参考、paper simulation、BrokerAdapter 和 Goldminer adapter 阶段。
- [x] `scripts/check_cr_tracking_consistency.py` 能接受 CR020 deleted-by-user 状态并 PASS。
- [x] 不新增任何真实 broker 运行授权。
- [x] 不新增依赖、不安装 Backtrader、不安装掘金 SDK。

## 当前阶段结论

`closed-current-delivery`。本 CR 已完成路线和状态变更写作，并补齐 CP2 / CP3 / CP4 证据：

- `process/checks/CP2-CR040-REQUIREMENTS-BASELINE.md`
- `process/checkpoints/CP2-CR040-REQUIREMENTS-BASELINE.md`
- `process/checks/CP3-CR040-HLD-CONSISTENCY.md`
- `process/checkpoints/CP3-CR040-HLD-REVIEW.md`
- `process/checks/CP4-CR040-STORY-DAG-PARALLEL-SAFETY.md`

用户已于 2026-06-10 回复“同意”，CP2 / CP3 人工审查按 `approved` 回填：

- `process/checkpoints/CP2-CR040-REQUIREMENTS-BASELINE.md`
- `process/checkpoints/CP3-CR040-HLD-REVIEW.md`

CR040 关闭不授权任何 broker、Backtrader、掘金、QMT、账户、凭据、下单、撤单或 simulation/live 运行。后续可启动 CR041 实现 API-less Paper Simulation Runner；CR041 必须创建独立正式 CR 并重新走门禁。
