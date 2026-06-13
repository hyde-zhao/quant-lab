---
story_id: "CR041-S04-position-cash-equity-ledger"
title: "Position / Cash / Equity Ledger"
story_slug: "position-cash-equity-ledger"
lld_version: "1.0"
tier: "L"
status: "confirmed"
confirmed: true
created_by: "meta-po-inline-fallback"
created_at: "2026-06-10T22:48:00+08:00"
confirmed_by: "user"
confirmed_at: "2026-06-10T23:23:00+08:00"
shared_fragments:
  - "process/context/CP3-CR041-DESIGN-CONTEXT.yaml"
feature_design_refs: []
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "cash and position accounting"
    - "T+1 sellable quantity"
    - "equity and reconciliation"
  rationale: "账本输出是模拟盘可信度核心，需要完整设计。"
open_items: 0
---

# LLD: CR041-S04 - Position / Cash / Equity Ledger

## 0. 上游设计依据

| 来源 | 路径 / ID | 被本 LLD 消费的内容 |
|---|---|---|
| S03 LLD | `process/stories/CR041-S03-paper-broker-fill-engine-LLD.md` | `PaperFill`、成本、partial/rejected/expired。 |
| CP2 | `process/checkpoints/CP2-CR041-REQUIREMENTS-BASELINE.md` | 100 股 lot、现金不足、持仓不足、T+1 可卖、raw close 估值。 |
| CP3 context | `process/context/CP3-CR041-DESIGN-CONTEXT.yaml` | Ledger / Equity / Reconciliation 架构。 |

## 1. Goal

创建本地账本设计，根据 `PaperFill` 更新现金、持仓、可卖数量、成本、净值曲线、回撤、换手和 reconciliation summary。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- 买入：成交金额 + 全部成本不得超过可用现金；不足则按 100 股 lot 缩量，仍不足则 rejected。
- 卖出：成交数量不得超过 `sellable_qty`；超过则 partial 或 rejected。
- T+1 可卖：T 日买入数量当日不可卖，T+1 后进入 sellable。
- 现金账本记录交易前现金、交易现金流、费用、交易后现金。
- 持仓账本记录 qty、sellable_qty、average_cost、market_value、unrealized_pnl。
- 净值曲线使用 raw close 估值；缺 raw close fail-closed。
- reconciliation 输出 cash + positions market value 与 equity 的差异，超过容忍度则 blocked。

### 2.2 Non-Functional

- 安全：不读取真实账户，不做 broker reconciliation。
- 可审计：fills、cash ledger、position ledger、equity curve 可通过 run_id 串联。
- 精度：金额计算保留可配置 rounding policy，默认两位小数报告、内部 float/Decimal 策略在实现中统一。

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `engine/paper_simulation.py` | 定义 `PaperAccountState`、`CashLedgerRow`、`PositionLedgerRow`、`EquityCurveRow`、`apply_fills_to_ledger`、`mark_to_market`、`reconcile_equity` | 当前 Story primary owner。 |
| `tests/test_cr041_paper_simulation.py` | 覆盖现金不足、持仓不足、T+1 可卖、raw close 估值、reconciliation | S05 统一落测试。 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 创建 | `engine/paper_simulation.py` | 新增账本数据模型、应用 fill、估值、对账和指标 helper。 |
| 创建 | `tests/test_cr041_paper_simulation.py` | 新增 S04 账本测试。 |

## 5. 数据模型与持久化设计

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `PaperAccountState.cash` | float/Decimal | >=0 | 本地模拟现金。 |
| `Position.qty` | int | >=0 | 持仓总数。 |
| `Position.sellable_qty` | int | >=0 and <= qty | T+1 可卖数量。 |
| `CashLedgerRow` | dataclass | 每笔 fill 一行 | 记录费用和现金流。 |
| `EquityCurveRow.equity` | float | cash + market value | raw close 估值。 |
| `ReconciliationSummary.diff` | float | 容忍度内 | 超限 blocked。 |

无真实账户持久化；S05 负责 artifact 写出。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| `apply_fills_to_ledger(initial_state, fills, valuation_data, config)` | 初始状态、fills、估值数据、配置 | `PaperLedgerResult` | CLI / S05 | 纯本地账本。 |
| `mark_to_market(positions, valuation_rows)` | 持仓、raw close | market value rows | ledger | 缺 raw close blocked。 |
| `reconcile_equity(cash, positions_value, equity)` | 金额 | summary | ledger / tests | 差异超限 blocked。 |
| `roll_sellable_quantities(state, trade_date)` | 状态、日期 | state | ledger | T+1 可卖释放。 |

## 7. 核心处理流程

1. 初始化现金和空持仓，或从本地 paper state fixture 初始化。
2. 按交易日期排序处理 fills。
3. 每个交易日前释放满足 T+1 的 sellable qty。
4. 对 filled/partial fill 执行现金和持仓更新；rejected/expired 只入审计，不改账。
5. 每日用 raw close mark-to-market。
6. 输出 reconciliation summary、turnover、drawdown、cost totals。

## 8. 技术设计细节

- 买入均价：使用含费用成本或不含费用成本需在 config 中固定；推荐 average_cost 使用成交价，成本单独进入 cash/cost report。
- 换手：按成交金额 / 当日 equity 计算，equity 为交易后 mark-to-market。
- 回撤：从 equity curve rolling peak 计算。
- 图示类型选择：状态流转可由测试覆盖，LLD 不补 Mermaid。

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 初始状态只能来自本地配置 / fixture，不读 broker | 测试和静态扫描。 |
| 安全 | reconciliation 是本地账本自检，不连接 broker | 接口无 broker 参数。 |
| 性能 | 日频账本按 fills 线性处理 | 小 fixture 单测。 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| S04-T01 买入扣现金 | filled buy | apply ledger | cash 减少，position 增加 | pytest |
| S04-T02 现金不足缩量 | cash 不足 | apply | partial/rejected，不允许 cash < 0 | pytest |
| S04-T03 T+1 可卖 | T 日买入后当日卖出 | apply | 当日 sellable 不增加，T+1 释放 | pytest |
| S04-T04 raw close 估值 | valuation close 完整 | mark | equity 正确 | pytest |
| S04-T05 缺 close | valuation 缺失 | mark | blocked | pytest |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| CR041-S04-T1 | 创建 | `engine/paper_simulation.py` | 定义 account / position / ledger / equity schema | S04-T01 |
| CR041-S04-T2 | 创建 | `engine/paper_simulation.py` | 实现 fill 应用、现金/持仓不足处理、T+1 sellable | S04-T01..S04-T03 |
| CR041-S04-T3 | 创建 | `engine/paper_simulation.py` | 实现 raw close 估值、回撤、换手、reconciliation | S04-T04、S04-T05 |
| CR041-S04-T4 | 创建 | `tests/test_cr041_paper_simulation.py` | 添加 S04 tests | S04-T01..S04-T05 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | 无阻断澄清项 | 按 CP2 已确认 A 股基础账户规则设计 | 用户已同意 | 账本 / 测试 | CP2 checkpoint | 引入融资融券、多账户或真实 broker 对账时重访。 |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| 金额精度差异 | reconciliation 误报 | 固定 rounding policy 和 tolerance。 |
| 成本是否进 average_cost | 指标口径争议 | 成本单独列报，average_cost 默认不含税费，CP5 中明示。 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| N/A | OPEN | 无 | 无 | N/A |

## 13. 回滚与发布策略

- 发布方式：本地账本模块随 CR041 实现合入。
- 回滚触发条件：现金为负、持仓为负、T+1 可卖错误、reconciliation 超限未阻断。
- 回滚动作：回退 S04 ledger，保留 S01..S03。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [ ] `confirmed=false` 时不进入实现
- [ ] OPEN / Spike 已清点

## 人工确认区

CP5 批次人工确认文件：`process/checkpoints/CP5-CR041-ALL-STORIES-LLD-BATCH.md`。
