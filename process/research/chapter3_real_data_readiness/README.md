# CR-034 第三章真实数据 Readiness

## 目标

本目录记录第三章多因子复刻从离线 fixture 能力进入真实数据 lake 的 readiness、补数和实证门控。

## 当前结论

- 最新 readiness：`PASS`
- 已补齐或确认可用：`prices`、`adj_factor`、`prices_hfq`、`trade_calendar`、`stock_basic`、`market_cap`、`liquidity_capacity`、`trade_status`、`prices_limit`、`events`、`financial_pit`
- 原阻断项已处理：`trade_status`、`prices_limit`、`events/ST` 已由 CR-034 历史约束派生 run 覆盖 2000-2019 目标窗口。
- 财务 PIT 状态：`PASS`。已补 `income + balancesheet + fina_indicator` 合并候选表，并生成 audited `financial_pit`，包含 `ann_date/report_period/update_flag/revision_as_of/revision_sequence/pit_policy`。Tushare 未提供独立 vendor ingestion timestamp，本轮以公告日 PIT 满足第三章 no-lookahead 因子构造。
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
| 2000-2019 历史约束派生 | `run-cr034-chapter3-constraints-2000-2019` | trade_status、prices_limit、events、audited financial_pit |

## 后续门控

第三章真实数据 readiness 已通过。下一步门控是执行 2000-2019 全样本实证复跑并生成 `EMPIRICAL-RUN-REPORT.md`；在实证报告完成前，不应声明“第三章真实实证复刻完成”。
