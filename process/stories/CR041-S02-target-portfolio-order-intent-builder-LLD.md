---
story_id: "CR041-S02-target-portfolio-order-intent-builder"
title: "Target Portfolio and Order Intent Builder"
story_slug: "target-portfolio-order-intent-builder"
lld_version: "1.0"
tier: "M"
status: "confirmed"
confirmed: true
created_by: "meta-po-inline-fallback"
created_at: "2026-06-10T22:48:00+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-10T23:23:00+08:00"
shared_fragments:
  - "process/context/CP3-CR041-DESIGN-CONTEXT.yaml"
  - "engine/order_intent_draft.py"
feature_design_refs: []
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "target portfolio contract"
    - "local order intent boundary"
    - "T+1 execution clock"
  rationale: "本 Story 决定本地模拟成交输入，不得生成真实订单或 broker payload。"
open_items: 1
---

# LLD: CR041-S02 - Target Portfolio and Order Intent Builder

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| S01 LLD | `process/stories/CR041-S01-strategy-admission-package-reader-LLD.md` | `PaperSimulationAdmissionView`。 |
| CP3 context | `process/context/CP3-CR041-DESIGN-CONTEXT.yaml` | T close signal、T+1 open execution、raw price policy。 |
| CR025 draft | `engine/order_intent_draft.py` | 既有 `order_intent_draft_v1` 的 no-broker / raw execution boundary。 |

## 1. Goal

创建目标组合和本地订单意图构建设计，把 S01 admission view 以及目标权重/目标股数转换为 `paper_order_intent_v1`，供 S03 本地撮合使用。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 支持目标权重和目标股数两类输入；至少一个存在，否则 fail-closed。
- 计算 `signal_date` 与 `target_trade_date`：T 日收盘后信号，T+1 第一个开市日执行。
- 生成 side：目标股数/权重高于当前持仓为 buy，低于当前持仓为 sell，等于则 no-op。
- 对 A 股 lot 做预处理：买入向下取整到 100 股，卖出不得超过可卖数量。
- 输出字段含 symbol、side、target_qty、target_weight、estimated_price_policy、execution_price_policy=raw、valuation_price_policy=raw_close。
- 不生成 broker order id、account id、委托编号或真实订单字段。

### 2.2 Non-Functional

- 可重复：同一输入生成稳定 intent id。
- 安全：intent 必须 `not_authorization=true`，并继承 forbidden counters 全 0。
- 可解释：每条 intent 保留 reason、source_run_id、data_lineage_ref 和 limitations。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `engine/paper_simulation.py` | 定义 `PaperOrderIntent`、target portfolio adapter、lot rounding、trade date resolver | 当前 Story primary owner。 |
| `engine/order_intent_draft.py` | 可选只读复用常量和 forbidden counter 语义 | 不改既有 CR025 行为，必要新增 adapter 需保持兼容。 |
| `tests/test_cr041_paper_simulation.py` | 覆盖目标权重/股数、lot、T+1、raw policy、no broker 字段 | S05 统一落测试。 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `engine/paper_simulation.py` | 新增 `PaperOrderIntent`、`TargetPortfolioRow`、`build_order_intents`、`resolve_target_trade_date`。 |
| 修改 | `engine/order_intent_draft.py` | 仅在需要时增加 CR041 可复用 helper；不得改变 `order_intent_draft_v1` 校验语义。 |
| 创建 | `tests/test_cr041_paper_simulation.py` | 新增 S02 intent 构建测试。 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `PaperOrderIntent.schema_version` | str | `paper_order_intent_v1` | CR041 内部 intent。 |
| `intent_id` | str | 稳定 hash | 基于 run_id、symbol、date、target。 |
| `signal_date` | str | 必填 | 信号生成日。 |
| `target_trade_date` | str | 必填 | 下一个开市日。 |
| `symbol` | str | 必填 | 股票代码。 |
| `side` | Literal | buy/sell/noop/rejected | 本地模拟方向。 |
| `target_qty` | int | 100 股 lot 后数量 | 可为 0 no-op。 |
| `execution_price_policy` | str | 必须 raw_open | 不允许 qfq/hfq。 |
| `not_authorization` | bool | true | 非真实订单。 |

无持久化变更；S05 负责把 intent 序列化为 artifact。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `build_order_intents(admission_view, target_portfolio, calendar, current_positions=None)` | S01 view、目标组合、交易日历、可选当前持仓 | `list[PaperOrderIntent]` | S03 / CLI | 缺交易日历 fail-closed。 |
| `resolve_target_trade_date(signal_date, calendar)` | 日期、交易日历 | 日期 | builder | 返回 T+1 第一个 open day。 |
| `apply_lot_and_sellable_rules(row, position)` | 目标行、当前持仓 | 调整后数量和 reason | builder / tests | 买入 100 股 lot，卖出不超过可卖。 |

## 7. 核心处理流程

1. 接收 S01 admission view，确认 validation passed。
2. 解析目标组合行；缺 symbol 或目标数量/权重时 rejected。
3. 用 trade calendar 计算 `target_trade_date`。
4. 计算目标数量，应用 100 股 lot 和卖出可用约束。
5. 生成 `paper_order_intent_v1`；全部 counters 为 0。

## 8. 技术设计细节

- 关键算法：目标权重转股数只在有估值价格和初始权益时执行；否则该行 rejected，避免臆造数量。
- 复权边界：`execution_price_policy` 固定 `raw_open`；若输入声明 qfq/hfq 执行价则 fail-closed。
- 兼容性处理：可通过 adapter 消费 CR025 draft 字段名，但输出 schema 独立为 CR041 内部 `paper_order_intent_v1`。
- 图示类型选择：流程短，无需 Mermaid。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 不输出 account/order/broker 字段 | 测试扫描 intent keys。 |
| 安全 | qfq/hfq 执行价阻断 | 单测构造错误 policy。 |
| 性能 | 对目标组合 O(n) 处理 | fixture 多 symbol 测试。 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| S02-T01 权重生成 intent | admission passed，目标权重、价格、权益存在 | build intents | buy/sell intent，T+1 raw open | pytest |
| S02-T02 lot 规则 | 买入 155 股 | build | 调整为 100 股 | pytest |
| S02-T03 卖出超可卖 | 可卖 100，目标卖 300 | build | partial/rejected reason | pytest |
| S02-T04 缺 calendar | 无交易日历 | build | blocked | pytest |
| S02-T05 broker 字段污染 | 输入含 account_id | build | blocked | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR041-S02-T1 | 创建 | `engine/paper_simulation.py` | 定义 `PaperOrderIntent` 和 target row adapter | S02-T01 |
| CR041-S02-T2 | 创建 | `engine/paper_simulation.py` | 实现交易日解析、lot、sellable 规则 | S02-T02..S02-T04 |
| CR041-S02-T3 | 创建 | `engine/paper_simulation.py` | 实现 broker 字段污染扫描和 raw policy guard | S02-T05 |
| CR041-S02-T4 | 创建 | `tests/test_cr041_paper_simulation.py` | 添加 S02 测试 | S02-T01..S02-T05 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| O-CR041-S02-01 | CR039 package 当前不直接提供逐日目标组合 artifact，S02 第一版如何取目标组合？ | 推荐：S05 CLI 第一版接受显式 target portfolio fixture/path；CR039 package 只提供策略准入，不臆造目标持仓。备选：从 CR038 alpha_scores 推导目标组合。 | 转非阻断 OPEN，CP5 请用户接受该实现取舍。 | CLI / 测试 / 报告 | CR039 package `input_refs` 只含上游 artifact refs。 | 若用户要求直接从 CR038 artifact 生成目标组合，另起增强 Story 或在 CR041 实现前补充 adapter。 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 目标权重转股数需要权益和价格 | 可能无法从 CR039 自动生成交易 | CLI 显式要求初始资金和 target portfolio 输入；缺失 fail-closed。 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| O-CR041-S02-01 | OPEN | 目标组合来源第一版采用显式输入，不从 CR039 自动臆造 | CP5 决策接受或要求修改 | meta-po / user |

## 13. 回滚与发布策略

- 发布方式：随 CR041 实现合入本地模块；不触发真实订单。
- 回滚触发条件：intent 输出真实 broker 字段、交易日错误、qfq/hfq 执行价放行。
- 回滚动作：回退 S02 builder，保留 S01 reader。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [ ] OPEN 已纳入 CP5 Decision Brief
- [ ] `confirmed=false` 时不进入实现

## 人工确认区

CP5 批次人工确认文件：`process/checkpoints/CP5-CR041-ALL-STORIES-LLD-BATCH.md`。
