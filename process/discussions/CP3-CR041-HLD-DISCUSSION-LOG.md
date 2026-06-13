---
cr_id: CR-041
discussion_id: CP3-CR041-HLD-DISCUSSION
status: approved
owner: meta-po
created_at: 2026-06-10T23:05:00+08:00
approved_by: user
approved_at: 2026-06-10T23:05:00+08:00
---

# CP3 CR041 架构讨论日志

## 候选架构

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. 日频 realistic paper simulation（L2-minus） | 覆盖主要交易约束、成本、成交和账户规则；不需要外部权限；可本地复跑 | 不模拟分钟/tick/盘口排队 | `engine/paper_simulation.py`、runner、fixtures、reports | 推荐且已获用户同意 | 当需要盘口级或真实仿真账户时切到后续 CR043/CR044 或 minute/tick Spike。 |
| B. 简单日频 paper trading | 实现快 | 忽略成本、涨跌停、停牌、容量，结果偏乐观 | 同 A 但验收弱 | 不推荐 | 仅可作为测试 fixture。 |
| C. 盘口级 / 真实账户级仿真 | 更接近真实成交 | 需要 minute/tick/Level2、SDK、账号或外部权限 | 数据、权限、安全、运行授权 | 不进 CR041 | 未来单独 Spike。 |

## 推荐架构

```text
StrategyAdmissionPackageReader
  -> TargetPortfolioBuilder
  -> OrderIntentBuilder
  -> PaperBrokerFillEngine
  -> PositionCashLedger
  -> EquityCurveReporter
  -> ReconciliationReporter
```

## 关键设计约束

| 主题 | 决策 |
|---|---|
| 时钟 | T 日收盘后出信号，T+1 第一个开市日执行。 |
| 价格 | raw open 成交，raw close 估值；qfq/hfq 不得作为执行价。 |
| 成本 | commission、min commission、stamp duty、transfer fee、fixed bps slippage。 |
| 约束 | trade_calendar、trade_status、prices_limit、raw OHLCV 缺失时 fail-closed。 |
| 成交 | participation cap + partial fill；无盘口排队。 |
| 账户 | 100 股 lot、现金不足、持仓不足、T+1 可卖。 |
| artifact | order_intents、fills、rejected_fills、positions、cash_ledger、equity_curve、turnover_cost、reconciliation、summary。 |

## 不授权边界

CR041 不授权 broker / QMT / MiniQMT / XtQuant / 掘金 / Backtrader runtime / 账户查询 / 凭据读取 / 下单 / 撤单 / simulation/live。
