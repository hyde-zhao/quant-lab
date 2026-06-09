# CR-034 第三章真实数据 Readiness

## 目标

本目录记录第三章多因子复刻从离线 fixture 能力进入真实数据 lake 的 readiness、补数和实证门控。

## 当前结论

- 最新 readiness：`PASS`
- 最新真实实证：`PASS`。`run-chapter3-empirical-2000-2019` 已生成 2000-2019 全样本因子面板、单因子评价和多因子研究准入摘要。
- 已补齐或确认可用：`prices`、`adj_factor`、`prices_hfq`、`trade_calendar`、`stock_basic`、`market_cap`、`liquidity_capacity`、`trade_status`、`prices_limit`、`events`、`financial_pit`
- 原阻断项已处理：`trade_status`、`prices_limit`、`events/ST` 已由 CR-034 历史约束派生 run 覆盖 2000-2019 目标窗口。
- 财务 PIT 状态：`PASS`。已补 `income + balancesheet + fina_indicator` 合并候选表，并生成 audited `financial_pit`，包含 `ann_date/report_period/update_flag/revision_as_of/revision_sequence/pit_policy`。Tushare 未提供独立 vendor ingestion timestamp，本轮以公告日 PIT 满足第三章 no-lookahead 因子构造。
- 安全边界：所有补数均写 run-scoped canonical candidate / quality summary；实证 runner 只读本地 lake，`credential_read=0`、`provider_fetch=0`、`lake_write=0`、`catalog_current_pointer_publish=0`、`qmt_operation=0`、`simulation_or_live_run=0`。
- 资源边界：2000-2019 实证使用 `chunked` 分年分块模式，默认 `--max-memory-gb 16`；正式报告观测最大 RSS 约 2.15GB，`memory_status=pass`。

## 产物

| 文件 | 说明 |
|---|---|
| `READINESS-REPORT.md` | 真实 lake readiness Markdown 报告 |
| `READINESS-REPORT.json` | 机器可读 readiness 报告 |
| `../chapter3_empirical/run-chapter3-empirical-2000-2019/EMPIRICAL-RUN-REPORT.md` | 2000-2019 真实实证 Markdown 报告 |
| `../../../reports/chapter3_factor_panel/run-chapter3-empirical-2000-2019/factor_panel.parquet` | 第三章 7 因子月度长表面板 |

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

## 实证 run-id

| 范围 | run_id | 产物 |
|---|---|---|
| 2000-2019 | `run-chapter3-empirical-2000-2019` | 7 因子月度面板、单因子指标、相关矩阵、多因子研究准入摘要 |

## 后续门控

第三章真实数据 readiness 和 2000-2019 全样本实证均已通过，可作为后续多因子研究输入。该结论仍只覆盖 research candidate / admission 输入，不构成 production-valid、QMT-ready、simulation-ready、live-ready 或 broker order 授权。
