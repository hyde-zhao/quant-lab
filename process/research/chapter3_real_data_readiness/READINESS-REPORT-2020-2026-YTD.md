# CR-034 第三章 2020-2026 YTD 数据与实证 Readiness

- status: `PASS`
- target_window: `2020-01-01`..`2026-05-28`
- scope: 第三章 7 因子真实研究输入，覆盖 2020-2025 全年和 2026 年截至本地 lake 可用日 2026-05-28
- not_authorization: 不构成 production-valid、QMT-ready、simulation-ready、live-ready 或 broker order 授权

## 数据覆盖

| 数据集 | 状态 | 覆盖 / run 证据 |
|---|---|---|
| prices | PASS | `run-cr014-s14-prices-adj-factor-2020*` 至 `2025*`，以及 `run-cr014-s11-full-a-2026-ytd-date-batch-143508`；覆盖到 `2026-05-28` |
| adj_factor | PASS | 同 prices，覆盖到 `2026-05-28` |
| prices_hfq | PASS | runner 按 raw prices + adj_factor 后复权重建 |
| trade_calendar | PASS | `run-cr014-s14-trade-calendar-2015-2026-232302` 等 canonical 覆盖到 `2026-05-29` |
| stock_basic / 生命周期 | PASS | canonical `stock_basic` 覆盖到 `2026-05-28`，退市日前历史样本按生命周期控制 |
| market_cap | PASS | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` 覆盖到 `2026-05-28` |
| liquidity_capacity | PASS | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` 覆盖到 `2026-05-28` |
| trade_status | PASS | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` 和 `run-cr014-s13-trade-status-missing-2026-ytd-231252` 覆盖到 `2026-05-28` |
| prices_limit | PASS | `run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529` 和 `run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529` 覆盖到 `2026-05-28` |
| financial_pit | PASS | `run-cr034-financial-pit-2020-2026-ytd-20260610-symbols_01` 至 `symbols_08` raw 分批完成；`run-cr034-financial-pit-2020-2026-ytd-20260610-audited` 写入 156,483 行 audited PIT，覆盖公告日 `2020-01-03`..`2026-05-21`，包含 `revision_as_of/revision_sequence/pit_policy` |

## 实证结果

| run_id | status | factor_panel_rows | label_rows | rebalance_count | max_rss_gb | memory_status |
|---|---|---:|---:|---:|---:|---|
| `run-chapter3-empirical-2020-2026-ytd` | PASS | 2,019,002 | 371,877 | 76 | 5.549709 | pass |

## 年度 part

| 年份 | panel_rows | label_rows |
|---:|---:|---:|
| 2020 | 132,494 | 47,315 |
| 2021 | 294,629 | 53,464 |
| 2022 | 334,461 | 58,308 |
| 2023 | 357,954 | 62,378 |
| 2024 | 378,889 | 63,952 |
| 2025 | 389,906 | 64,670 |
| 2026 YTD | 130,669 | 21,790 |

## 安全边界

- `catalog_current_pointer_publish=0`
- `qmt_operation=0`
- `simulation_or_live_run=0`
- 实证 runner：`credential_read=0`、`provider_fetch=0`、`lake_write=0`
- 财务 PIT 补数读取本地 `.env` 中的 Tushare token；未输出 token，未写入 Git、报告、日志或 memory。

## 结论

2020-2026 YTD 已按第三章数据口径完成可追溯处理：后复权、PIT 财务、交易状态、涨跌停、ST / 生命周期、市值、流动性和月度标签均已进入正式实证产物。该结论仅允许作为后续多因子研究输入。
