# CR-034 第三章真实数据 Readiness Report

- status: `PASS`
- target_window: `2000-01-01`..`2019-12-31`
- lake_root: `/mnt/ugreen-data-lake`
- catalog_current_pointer_publish: `0`
- qmt_operation: `0`
- simulation_or_live_run: `0`

## Dataset Coverage

| dataset | status | aggregate_start | aggregate_end | rows | missing_reason | run_count |
|---|---|---|---|---:|---|---:|
| `prices` | `PASS` | `2000-01-04` | `2026-05-28` | 28542018 | `` | 37 |
| `adj_factor` | `PASS` | `2000-01-04` | `2026-05-28` | 29865789 | `` | 36 |
| `trade_calendar` | `PASS` | `2000-01-01` | `2026-05-29` | 10924 | `` | 25 |
| `stock_basic` | `PASS` | `1990-12-01` | `2026-05-28` | 49309 | `` | 12 |
| `trade_status` | `PASS` | `2000-01-04` | `2026-05-28` | 21465195 | `` | 8 |
| `prices_limit` | `PASS` | `2000-01-04` | `2026-05-28` | 40817179 | `` | 9 |
| `events` | `PASS` | `1990-12-01` | `2026-06-09` | 354073 | `` | 3 |
| `market_cap` | `PASS` | `2000-01-04` | `2026-05-28` | 16898211 | `` | 17 |
| `liquidity_capacity` | `PASS` | `2000-01-04` | `2026-05-28` | 16990776 | `` | 17 |

## Blocking Gates

- hfq_status: `PASS`
- hfq_reason: 已有后复权 canonical dataset。
- financial_pit_status: `PASS`
- financial_pit_reason: financial_pit 已在目标窗口首月调仓日前可用并覆盖到窗口结束，且包含 ann_date/report_period/update_flag/revision_as_of 等 PIT 审计字段。

## Source Limitations

- 财务 PIT 采用公告日 available_at 和 revision_as_of 审计字段；Tushare 未提供独立 vendor ingestion timestamp，本轮以公告日 PIT 满足第三章 no-lookahead 因子构造。

## Operation Counts

| operation | count |
|---|---:|
| `catalog_current_pointer_publish` | 0 |
| `credential_read` | 0 |
| `lake_write` | 0 |
| `provider_fetch` | 0 |
| `qmt_operation` | 0 |
| `simulation_or_live_run` | 0 |
