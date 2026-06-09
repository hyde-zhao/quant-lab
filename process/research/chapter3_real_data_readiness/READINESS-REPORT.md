# CR-034 第三章真实数据 Readiness Report

- status: `BLOCKED`
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
| `trade_status` | `BLOCKED` | `2015-01-05` | `2026-05-28` | 11575214 | `target_window_not_covered` | 6 |
| `prices_limit` | `BLOCKED` | `2007-01-04` | `2026-05-28` | 31436631 | `target_window_not_covered` | 7 |
| `events` | `BLOCKED` | `2015-12-05` | `2026-05-28` | 323698 | `target_window_not_covered` | 1 |
| `market_cap` | `PASS` | `2000-01-04` | `2026-05-28` | 16898211 | `` | 17 |
| `liquidity_capacity` | `PASS` | `2000-01-04` | `2026-05-28` | 16990776 | `` | 17 |

## Blocking Gates

- hfq_status: `PASS`
- hfq_reason: 已有后复权 canonical dataset。
- financial_pit_status: `PASS_WITH_LIMITATIONS`
- financial_pit_reason: 发现财务候选数据集 financial_pit；仍需逐字段审计 ann_date/report_period/update_flag/revision/as_of。

## Source Limitations

- Tushare 财务接口通常提供公告日/报告期字段；若源端不提供完整 revision/as-of 链，需要在实证报告中降级为公告日 PIT 并显式披露。

## Operation Counts

| operation | count |
|---|---:|
| `catalog_current_pointer_publish` | 0 |
| `credential_read` | 0 |
| `lake_write` | 0 |
| `provider_fetch` | 0 |
| `qmt_operation` | 0 |
| `simulation_or_live_run` | 0 |
