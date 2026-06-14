---
status: "implemented-cp6"
version: "1.0"
change_id: "CR-051"
story_id: "CR051-S01-lifecycle-and-taxonomy-framework"
owner: "host-orchestrator"
implemented_at: "2026-06-14T09:00:24+08:00"
canonical_project_name: "quant-lab"
legacy_project_alias: "local_backtest"
---

# Strategy Taxonomy

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-14 | host-orchestrator | 初版策略 taxonomy，定义策略族、数据依赖、执行依赖、风险类别和后续扩展规则 |

## 目标

本文定义 quant-lab 首版策略分类。taxonomy 用于描述研究对象和后续 CR 路线，不改变生命周期主状态机，不授权真实运行。

## 字段合同

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `strategy_family` | enum | 是 | 策略族主分类 |
| `sub_family` | string | 否 | 细分类型 |
| `timeframe` | enum | 是 | daily、intraday、tick、multi_horizon |
| `data_dependency` | list | 是 | market_data、event_data、fundamental、alternative、broker_facts 等 |
| `execution_dependency` | enum | 是 | none、paper、package_consumer、broker_runtime、high_frequency_runtime |
| `risk_class` | enum | 是 | low、medium、high、experimental |
| `claim_boundary` | list | 是 | 允许声明和禁止声明 |
| `follow_up_cr` | string | 否 | 后续 CR 或 Spike |
| `extension_owner` | string | 是 | 扩展责任方 |

## 首版策略族

| strategy_family | 典型对象 | timeframe | data_dependency | execution_dependency | risk_class | follow_up_cr |
|---|---|---|---|---|---|---|
| `multifactor` | 单因子评价、多因子组合、增强指数 | daily / multi_horizon | market_data、factor_panel、benchmark | paper / package_consumer | medium | CR052 |
| `event_driven` | 财报、公告、指数调整、公司行动 | daily / intraday | event_data、market_data | paper / package_consumer | high | CR053 |
| `timing` | 市场择时、风险开关、仓位调节 | daily / multi_horizon | market_data、macro_optional | paper / package_consumer | medium | CR056 |
| `technical` | 动量、RSI、MACD、趋势跟踪 | daily / intraday | market_data | paper / package_consumer | medium | CR056 |
| `statistical_arbitrage` | 配对、价差、均值回复 | intraday / multi_horizon | market_data、borrow_optional | broker_runtime | high | future CR |
| `machine_learning` | 监督学习、排序模型、walk-forward | daily / multi_horizon | factor_panel、label_window、model_registry | paper / package_consumer | experimental | CR054 Spike |
| `portfolio_optimization` | 组合优化、风险预算、增强指数 | daily / multi_horizon | benchmark、risk_model_optional、market_data | paper / package_consumer | medium | CR052 / CR056 |
| `tick_high_frequency_spike` | tick、盘口、微观结构、做市 Spike | tick / intraday | tick、level2、order_book | high_frequency_runtime | experimental | future Spike |

## 扩展规则

1. 新增策略族时，只追加 taxonomy entry，不修改 `docs/research/LIFECYCLE.md` 主状态机。
2. 新策略族必须声明 `data_dependency`、`execution_dependency`、`risk_class` 和 `claim_boundary`。
3. 任何 `broker_runtime`、`high_frequency_runtime`、simulation 或 live claim 必须另起 CR，并经过 runtime authorization。
4. `machine_learning` 首次进入时默认 Spike，不默认增加新依赖或模型 registry 实现。
5. `tick_high_frequency_spike` 默认 blocked，必须先完成 source/interface、license、成本和运行授权设计。

## Claim Boundary

| execution_dependency | CR051 默认允许声明 | CR051 默认禁止声明 |
|---|---|---|
| `none` | taxonomy / research-only | runtime-ready |
| `paper` | paper_candidate 条件 | live-ready / broker verified |
| `package_consumer` | delivery_candidate 条件 | QMT-ready / MiniQMT-ready |
| `broker_runtime` | blocked claim only | simulation-ready / live-ready |
| `high_frequency_runtime` | blocked claim only | tick-runtime-ready / live-ready |

## 后续 CR 路线

| 顺序 | 目标 | 说明 |
|---|---|---|
| 1 | CR052 多因子完整证明周期 | 用 `multifactor` 验证 idea -> delivery_candidate 全链路 |
| 2 | CR053 事件型研究流程 | 在生命周期稳定后扩展 event_data |
| 3 | CR054 ML 策略研究协议 Spike | 先验证 walk-forward、model registry、drift，不默认实现 |
| 4 | CR055 research consumption bridge | 对接 StrategyAdmissionPackage / StrategyCoreContract |
| 5 | CR056 feedback loop | 建立 post-run attribution、rework、retirement 回流 |

