# CR-034 第三章真实数据 Readiness

## 目标

本目录记录第三章多因子复刻从离线 fixture 能力进入真实数据 lake 的 readiness、补数和实证门控。

## 当前结论

- 最新 readiness：`BLOCKED`
- 已补齐或确认可用：`prices`、`adj_factor`、`prices_hfq`、`trade_calendar`、`stock_basic`、`market_cap`、`liquidity_capacity`、`financial_pit`
- 仍阻断严格复刻：`trade_status` 在 2000-2014 缺少 canonical 覆盖，`prices_limit` 的 Tushare `stk_limit` 源覆盖从 2007 起，`events/ST` 源覆盖不足 2000-2014。
- 财务 PIT 状态：`PASS_WITH_LIMITATIONS`。已补 `income + balancesheet + fina_indicator` 合并候选表，但 Tushare 源端没有完整 revision/as-of 链，当前只能按公告日 PIT 降级使用。
- 安全边界：所有补数均写 run-scoped canonical candidate / quality summary，`catalog_current_pointer_publish=0`，`qmt_operation=0`，`simulation_or_live_run=0`。

## 产物

| 文件 | 说明 |
|---|---|
| `READINESS-REPORT.md` | 真实 lake readiness Markdown 报告 |
| `READINESS-REPORT.json` | 机器可读 readiness 报告 |

## 真实补数 run-id

| 范围 | run_id | 数据集 |
|---|---|---|
| 2000-01-04..2000-01-05 smoke | `run-cr034-chapter3-smoke-20000104-20000105` | prices、adj_factor、prices_hfq、market_cap、liquidity、trade_calendar |
| 2000 | `run-cr034-chapter3-backfill-2000` | prices、adj_factor、prices_hfq、market_cap、liquidity、trade_calendar |
| 2001-2014 | `run-cr034-chapter3-backfill-<year>` | prices、adj_factor、prices_hfq、market_cap、liquidity、trade_calendar |
| 2000-2014 W3 | `run-cr034-chapter3-w3-2000-2014` | prices_limit、events；trade_status 未形成 2000-2014 canonical 输出 |
| 2000-2019 财务 smoke | `run-cr034-financial-pit-smoke-000001` | financial_pit |
| 2000-2019 财务全量 | `run-cr034-financial-pit-2000-2019` | financial_pit |

## 后续门控

严格第三章全样本实证仍需处理 W3/ST/停牌限制。可选路径：

1. 引入能覆盖 2000-2014 的历史 ST / 停牌 / 涨跌停替代源或 Tushare 其他接口。
2. 对 2000-2006 涨跌停采用价格行为推断，并在报告中标记为 `PASS_WITH_LIMITATIONS`。
3. 对 2000-2014 ST / 停牌缺口接受限制，只运行不依赖 ST/停牌剔除的研究切片。

默认不应在当前 readiness 为 `BLOCKED` 时声明“第三章严格真实复刻完成”。
