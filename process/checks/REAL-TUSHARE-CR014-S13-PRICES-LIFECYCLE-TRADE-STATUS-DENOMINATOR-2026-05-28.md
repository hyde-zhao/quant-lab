---
check_id: "REAL-TUSHARE-CR014-S13-PRICES-LIFECYCLE-TRADE-STATUS-DENOMINATOR-2026-05-28"
type: "real_candidate_quality_revalidation"
status: "PASS_PRICES_LIFECYCLE_TRADE_STATUS_DENOMINATOR_WARN_NON_PIT_PUBLISH_BLOCKED"
owner: "meta-po"
created_at: "2026-05-28T23:17:02+08:00"
checked_at: "2026-05-28T23:17:02+08:00"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
prices_run_id: "run-cr014-s11-full-a-2026-ytd-date-batch-143508"
stock_basic_run_id: "run-cr014-s09-ytd-config-lake-20260528-141907"
trade_status_run_id: "run-cr014-s13-trade-status-missing-2026-ytd-231252"
date_range: "2026-01-01..2026-05-28"
open_trade_dates: 94
lake_root: "<configured-env-lake-root>"
publish_current_pointer: false
duckdb_files_created: 0
---

# REAL Tushare CR014-S13 Prices Lifecycle + Trade Status Denominator

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| S11 全 A prices candidate 已完成 | PASS | `process/checks/REAL-TUSHARE-CR014-S11-FULL-A-2026-YTD-PULL-2026-05-28.md` | `prices` raw / manifest / canonical candidate 已完成。 |
| S12 adj_factor 可用性已闭环 | PASS | `process/checks/REAL-TUSHARE-CR014-S12-ADJ-FACTOR-PRICES-DENOMINATOR-REVALIDATION-2026-05-28.md` | 已观测 `prices` 交易对全部有 `adj_factor`。 |
| lifecycle 输入可读 | PASS | `stock_basic` candidate | `stock_basic` 5524 个 symbol，用于上市 / 退市 lifecycle 分母，不声明 PIT universe。 |
| 用户授权真实抓取 | PASS | 当前会话授权 | 仅针对 lifecycle 后仍缺失的 271 个 symbol 抓取 `trade_status`，不全 A 扫描。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | CLI 支持 `prices` lifecycle denominator | PASS | `market_data/cli.py` | 新增 `--use-stock-basic-lifecycle-denominator` 与 `--stock-basic-run-id`。 |
| 2 | CLI 支持 candidate `trade_status` 剔除不可交易 pair | PASS | `market_data/cli.py` | 新增 `--exclude-trade-status-untradable` 与 `--trade-status-run-id`。 |
| 3 | lifecycle-only 重验 | PASS_WITH_REMAINING_GAP | quality candidate | expected_rows=516024，missing_rows=1138，missing_rate=0.2205%，quality_status=warn。 |
| 4 | 缺口 symbol 精简 | PASS | candidate pair diff | lifecycle 后剩余缺口涉及 271 个 symbol。 |
| 5 | `trade_status` 真实抓取 | PASS | manifest | `run-cr014-s13-trade-status-missing-2026-ytd-231252`，6/6 batch success，raw_rows=25408。 |
| 6 | `trade_status` normalize | PASS | canonical candidate | 6 个 parquet，25408 行，271 个 symbol。 |
| 7 | 不可交易 pair 解释 | PASS | candidate audit | `untradable_pairs=1138`，刚好覆盖 lifecycle 后剩余 `prices` 缺口。 |
| 8 | `prices` lifecycle + trade_status 重验 | PASS_WITH_WARN | quality report | expected_rows=514886，actual_rows=515055，missing_rows=0，missing_rate=0.0。 |
| 9 | 非 PIT 边界 | PASS | quality report | `quality_status=warn`，`warnings=["warn_non_pit_universe"]`，`pit_status=non_pit_disclosed`。 |
| 10 | publish gate | PASS | `read_dataset(prices)` | current read 仍因 `catalog_not_published` 被阻止。 |
| 11 | DuckDB 边界 | PASS | scan | 配置湖 `.duckdb` 文件数为 0。 |

## Revalidation Results

| Step | Denominator Mode | Expected Rows | Actual Rows | Missing Rows | Missing Rate | Quality |
|---|---|---:|---:|---:|---:|---|
| S11 original full-A static symbols | `open_trade_dates_in_requested_range_x_target_symbols` | 519820 | 515055 | 4765 | 0.9167% | warn |
| S13 lifecycle only | `stock_basic_lifecycle_active_trade_date_symbol_pairs` | 516024 | 515055 | 1138 | 0.2205% | warn |
| S13 lifecycle minus trade_status untradable | `stock_basic_lifecycle_minus_trade_status_untradable_pairs` | 514886 | 515055 | 0 | 0.0 | warn |

## Trade Status Candidate Summary

| Field | Value |
|---|---:|
| run_id | `run-cr014-s13-trade-status-missing-2026-ytd-231252` |
| symbol_count | 271 |
| request_count | 6 |
| manifest_success_count | 6 |
| raw_rows | 25408 |
| canonical_rows | 25408 |
| untradable_pairs | 1138 |
| st_pairs | 8529 |

## Boundary / Risk Notes

| 边界 | 状态 | 说明 |
|---|---|---|
| lifecycle denominator | ACCEPTED_FOR_CANDIDATE_GAP_ATTRIBUTION | 解释上市前、退市后或 lifecycle 不活跃导致的非行情缺口；不证明完整 PIT universe。 |
| trade_status denominator | ACCEPTED_FOR_MISSING_PAIR_ATTRIBUTION | 本轮只抓取 lifecycle 后仍缺失的 271 个 symbol，不是全 A 完整 `trade_status` current truth。 |
| prices quality | WARN_NOT_PUBLISHABLE | missing_rows=0，但 `warn_non_pit_universe` 仍存在；不能自动 publish。 |
| current truth | UNCHANGED | `prices` candidate 未发布，current pointer 未更新。 |
| since-inception claim | NOT_CLAIMED | 本轮仅覆盖 `2026-01-01..2026-05-28`，不能表述为 2015 至今或 since-inception。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| `prices` 2026 YTD candidate 缺口归因 | PASS | missing_rows=0 | 生命周期 + 停牌 / 不可交易足以解释本轮静态分母缺口。 |
| `adj_factor` 对 `prices` 可用性 | PASS | S12 | 已观测 price pairs 均有复权因子。 |
| production publish | BLOCKED_BY_NON_PIT | quality warn | 仍需 PIT universe / 完整 claim boundary 决策，不自动发布。 |
| 2015+ 扩展前置 | PASS_FOR_2026_CANDIDATE_SMOKE | 本文件 + S12 | 可以作为扩展前的 2026 数据可用性证据。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CLI denominator 支持 | `market_data/cli.py` | PASS | lifecycle + candidate trade_status exclusion。 |
| validation denominator 报告 | `market_data/validation.py` | PASS | quality CSV 保留 denominator mode。 |
| 回归测试 | `tests/test_cr010_data_lake_publish_and_contracts.py` | PASS | 目标测试 5 passed。 |
| S13 检查记录 | `process/checks/REAL-TUSHARE-CR014-S13-PRICES-LIFECYCLE-TRADE-STATUS-DENOMINATOR-2026-05-28.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS_PRICES_LIFECYCLE_TRADE_STATUS_DENOMINATOR_WARN_NON_PIT_PUBLISH_BLOCKED`
- 已关闭：2026 YTD `prices` candidate 在 lifecycle + targeted trade_status 口径下 missing_rows=0。
- 未关闭：当前仍是 `warn_non_pit_universe`，不允许自动 publish，也不能声明 since-inception。
- 下一步：基于 S12 + S13，用户可决策是否继续拉取 2015 至今，或先把 PIT universe / 完整 `trade_status` current truth 做成 publish 前置。
