---
cr_id: CR-041
discussion_id: CP2-CR041-SCENARIO-DISCUSSION
status: approved
owner: meta-po
created_at: 2026-06-10T23:05:00+08:00
approved_by: user
approved_at: 2026-06-10T23:05:00+08:00
---

# CP2 CR041 场景讨论日志

## 背景

用户询问本地模拟如何模拟、交易时间、手续费、滑点、涨跌停和股价来源，并进一步要求“达到真实的模拟交易，包括成本和成交情况”。meta-po 解释 CR041 第一版应定义为“日频 realistic paper simulation（L2-minus）”，覆盖真实日频数据约束、交易成本、成交约束和账户规则，但不承诺分钟 / tick / Level2 / 盘口排队 / 真实仿真账户撮合。

用户回复“同意”，接受推荐方案。

## Scenario Gray Areas

| 问题 ID | 问题 | 推荐方案 | 用户结论 | 影响 |
|---|---|---|---|---|
| SGQ-CR041-01 | CR041 是否追求真实交易所撮合级别？ | 否；定义为日频 realistic paper simulation（L2-minus）。 | 同意 | CR041 不引入 minute/tick/Level2，不连接 broker。 |
| SGQ-CR041-02 | 成交时点和价格口径如何冻结？ | T 日收盘出信号，T+1 raw open 成交，raw close 估值。 | 同意 | 避免未来函数，禁止复权价成交。 |
| SGQ-CR041-03 | 成本与成交约束是否纳入第一版？ | 纳入费用、滑点、涨跌停、停牌、成交量上限、partial fill、A 股基础账户规则。 | 同意 | 输出更接近真实模拟交易的 fill / reject / ledger artifact。 |
| SGQ-CR041-04 | 是否授权外部 broker 或真实仿真？ | 不授权。 | 同意 | CR041 只做本地离线 runner。 |

## 冻结场景

| 场景 ID | 场景 | 预期 |
|---|---|---|
| SC-CR041-01 | 正常 T+1 raw open 成交 | 生成 fill，扣费用，更新现金和持仓。 |
| SC-CR041-02 | 买入涨停 | 生成 rejected_fill，原因 `rejected_limit_up_buy`。 |
| SC-CR041-03 | 卖出跌停 | 生成 rejected_fill，原因 `rejected_limit_down_sell`。 |
| SC-CR041-04 | 停牌 / 不可交易 | 生成 rejected_fill，原因 `rejected_not_tradable`。 |
| SC-CR041-05 | 成交量不足 | 生成 partial fill 或 rejected，记录 participation cap。 |
| SC-CR041-06 | 现金不足 / 持仓不足 | 拒单或缩量成交，并写入 reconciliation。 |
| SC-CR041-07 | 缺 trade_status / prices_limit / raw price | fail-closed，不得默认成交。 |

## 不授权项

| 项目 | 状态 |
|---|---|
| broker / QMT / MiniQMT / XtQuant / 掘金连接 | not-authorized |
| Backtrader 默认 runtime / 依赖变更 | not-authorized |
| 账户、委托、成交、持仓查询 | not-authorized |
| 下单、撤单、simulation/live 运行 | not-authorized |
| 凭据、token、cookie、session 读取 | not-authorized |
