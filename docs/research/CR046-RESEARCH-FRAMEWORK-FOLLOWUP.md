---
status: "implemented-cp6"
version: "1.1"
change_id: "CR-046"
owner: "host-orchestrator"
follow_up_cr: "CR051-candidate"
implementation_authorized: false
cp6_implemented_at: "2026-06-14T00:16:26+08:00"
---

# CR046 研究框架反向完善合同

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | host-orchestrator | 初版研究框架 follow-up 合同，定义 CR051 需要补齐的研究输出字段 |
| 1.1 | 2026-06-14 | host-orchestrator | CP6 状态收敛：确认本文作为 CR051 follow-up 契约资产实现；不修改研究框架代码 |

## 目标

CR046 不修改研究框架代码。本文只定义 CR051 需要消费的交易交付合同，使后续研究策略天然产出 QMT / MiniQMT 双目标交付所需字段。

## CR051 需要补齐的研究输出

| 字段组 | 必需字段 | 用途 |
|---|---|---|
| strategy metadata | strategy_id、version、research_source、universe、rebalance_frequency | 生成 StrategyCoreContract |
| target portfolio | symbol、target_weight / target_position、effective_date、cash_policy | QMT / MiniQMT target 映射 |
| order intents | intent_id、symbol、side、quantity_or_weight、reason、risk_tag | 后续策略包和 shadow 验证 |
| risk assumptions | max_position、turnover_limit、liquidity_limit、stop_condition | 风控和授权边界 |
| cost assumptions | commission、slippage、impact、capacity | 回测 / 模拟一致性 |
| validation evidence | schema_pass、static_guardrail、fixture_result、research_report | CP7 / CP8 证据 |

## 关键边界

| 对象 | 不是 |
|---|---|
| StrategyAdmissionPackage | 不是 QMT-ready |
| OrderIntentDraft | 不是真实订单 |
| fixture pass | 不是 runtime verified |
| research candidate | 不是 trade-ready |

## 后续 CR051 启动条件

- CR046 CP8 关闭为 framework-ready。
- StrategyCoreContract 和 StrategyValidationEvidence 已定稿。
- 用户确认需要把研究框架输出升级到双目标交付合同。
- 不在 CR051 默认授权 QMT / MiniQMT runtime、账户查询、submit/cancel 或 simulation/live。

## 验证方式

CR051 应通过 schema tests、fixture tests、文档 guardrail 和 admission package 回归证明研究输出满足 CR046 合同。任何真实运行仍需独立 runtime authorization。
