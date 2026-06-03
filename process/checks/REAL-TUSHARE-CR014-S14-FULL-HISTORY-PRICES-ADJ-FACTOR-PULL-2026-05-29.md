---
check_id: "REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29"
type: "real_full_history_candidate_pull_and_audit"
status: "PASS_FULL_HISTORY_PRICES_ADJ_FACTOR_CANDIDATE_PULLED_PUBLISH_BLOCKED"
owner: "meta-po"
created_at: "2026-05-29T00:27:18+08:00"
checked_at: "2026-05-29T00:27:18+08:00"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
date_range: "2015-01-01..2026-05-28"
actual_open_date_range: "2015-01-05..2026-05-28"
open_trade_dates: 2768
lake_root: "<configured-env-lake-root>"
publish_current_pointer: false
duckdb_files_created: 0
---

# REAL Tushare CR014-S14 Full-History Prices + Adj Factor Candidate Pull

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 2026 YTD candidate 可用性已证明 | PASS | `process/checks/REAL-TUSHARE-CR014-S11-FULL-A-2026-YTD-PULL-2026-05-28.md`、`process/checks/REAL-TUSHARE-CR014-S12-ADJ-FACTOR-PRICES-DENOMINATOR-REVALIDATION-2026-05-28.md`、`process/checks/REAL-TUSHARE-CR014-S13-PRICES-LIFECYCLE-TRADE-STATUS-DENOMINATOR-2026-05-28.md` | 2026 YTD `prices` / `adj_factor` raw、manifest、canonical candidate 已完成，且已观测 `prices` 交易对均有 `adj_factor`。 |
| 用户批准方案 A | PASS | 当前会话用户原文 `@meta-po 按照方案A，继续执行` | 采用先验证 2026 可用性、再按年度串行扩展 2015 至今的方案。 |
| 数据湖路径已由 `.env` 配置 | PASS | CLI 通过 `--env-file .env` 读取配置 | 文件中不记录真实 token 或真实 lake root。 |
| Publish gate 未授权 | PASS | 本文件边界 | 本轮只写 raw / manifest / canonical candidate 和检查记录，不发布 current pointer。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | 长周期交易日历已可用 | PASS | `run-cr014-s14-trade-calendar-2015-2026-232302` | `trade_calendar` normalize 后覆盖 2015-01-05..2026-05-28，共 2768 个开市日。 |
| 2 | 2015 基线年度分片完成 | PASS | `run-cr014-s14-prices-adj-factor-2015-232405` | 488/488 request success；`prices` 575184 行，`adj_factor` 675358 行。 |
| 3 | 2016-2025 年度分片完成 | PASS | 年度 run_id 表 | 每年按交易日执行 `prices.daily` + `prices.adj_factor`，所有 request 均 success。 |
| 4 | 2026 YTD 纳入总审计 | PASS | `run-cr014-s11-full-a-2026-ytd-date-batch-143508` | 复用已完成的 2026-01-05..2026-05-28 run，不重复拉取。 |
| 5 | raw / manifest 写入成功 | PASS | manifest status counts | 2768 个交易日 x 2 个接口，共 5536 条成功 manifest 记录。 |
| 6 | canonical 标准化成功 | PASS | canonical parquet counts | `prices` 和 `adj_factor` 各 2768 个 run-scoped canonical parquet。 |
| 7 | `prices` 对 `adj_factor` 可用性 | PASS | 年度 pair audit | 2015-2026YTD 每个年度 `missing_adj_for_price_pairs=0`，合计 0。 |
| 8 | 额外 `adj_factor` 交易对边界 | PASS_WITH_NOTE | 年度 pair audit | 合计 511697 个 `adj_factor` pair 不在 `prices` pair 中；它们不阻断“价格交易对可复权”判定，但不能替代行情记录。 |
| 9 | current truth 边界 | PASS | publish count=0 | 未执行 publish，未更新 catalog current pointer。 |
| 10 | DuckDB 边界 | PASS | duckdb_writes=0 | 本轮不创建 `.duckdb`，不引入 DuckDB 事实源。 |
| 11 | candidate read/query smoke | PASS | 只读 parquet query | 跨 2015-2026YTD 查询 `000001.SZ` / `600000.SH` 得到 5504 行，`adjusted_close` 全非空，policy 仅 `qfq`。 |
| 12 | current reader gate | PASS | `read_dataset(prices)` | 未发布状态下正式 reader 返回 `catalog_not_published`，证明 current truth 未被候选数据污染。 |
| 13 | 最小研究 smoke | PASS | 2025 low-volatility factor smoke | 使用 2025 candidate `adjusted_close` 计算 20 日波动率，低波 Top20 和 forward return 均可计算。 |

## Yearly Run Summary

| 年份 | run_id | 开市日 | manifest success | prices rows | adj_factor rows | prices symbols | missing adj pairs |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2015 | `run-cr014-s14-prices-adj-factor-2015-232405` | 244 | 488 | 575184 | 675358 | 2887 | 0 |
| 2016 | `run-cr014-s14-prices-adj-factor-2016-233430` | 244 | 488 | 652864 | 729185 | 3160 | 0 |
| 2017 | `run-cr014-s14-prices-adj-factor-2017-233927` | 244 | 488 | 754372 | 834943 | 3620 | 0 |
| 2018 | `run-cr014-s14-prices-adj-factor-2018-234359` | 243 | 486 | 824535 | 899558 | 3727 | 0 |
| 2019 | `run-cr014-s14-prices-adj-factor-2019-234833` | 244 | 488 | 894177 | 936704 | 3926 | 0 |
| 2020 | `run-cr014-s14-prices-adj-factor-2020-235353` | 243 | 486 | 964131 | 1003301 | 4364 | 0 |
| 2021 | `run-cr014-s14-prices-adj-factor-2021-235843` | 243 | 486 | 1085445 | 1119157 | 4840 | 0 |
| 2022 | `run-cr014-s14-prices-adj-factor-2022-000336` | 242 | 484 | 1179072 | 1208822 | 5182 | 0 |
| 2023 | `run-cr014-s14-prices-adj-factor-2023-000913` | 242 | 484 | 1258734 | 1274480 | 5381 | 0 |
| 2024 | `run-cr014-s14-prices-adj-factor-2024-001432` | 242 | 484 | 1293893 | 1303184 | 5433 | 0 |
| 2025 | `run-cr014-s14-prices-adj-factor-2025-001949` | 243 | 486 | 1313898 | 1321761 | 5500 | 0 |
| 2026 YTD | `run-cr014-s11-full-a-2026-ytd-date-batch-143508` | 94 | 188 | 515055 | 516604 | 5530 | 0 |

## Aggregate Audit

| 指标 | 值 |
|---|---:|
| 年度数 | 12 |
| 开市日合计 | 2768 |
| manifest success 合计 | 5536 |
| `prices` rows 合计 | 11311360 |
| `adj_factor` rows 合计 | 11823057 |
| `prices` unique trade_date/symbol pairs | 11311360 |
| `adj_factor` unique trade_date/symbol pairs | 11823057 |
| price pair 缺失 adj_factor 合计 | 0 |
| adj_factor 额外 pair 合计 | 511697 |
| publish count | 0 |
| duckdb writes | 0 |

## Candidate Read / Query Smoke

| 检查项 | 值 |
|---|---|
| query status | `pass` |
| sample symbols | `000001.SZ`, `600000.SH` |
| query row count | 5504 |
| query date range | `2015-01-05..2026-05-28` |
| candidate years | `2015..2026` |
| adjustment policies | `qfq` |
| non-null adjusted_close | 5504 |
| non-null adjusted returns | 5502 |
| current reader status | `required_missing` |
| current reader issue_codes | `catalog_not_published` |

## Minimal Research Smoke

| 检查项 | 值 |
|---|---:|
| status | `pass` |
| run_id | `run-cr014-s14-prices-adj-factor-2025-001949` |
| input rows | 1313898 |
| date range | `2025-01-02..2025-12-31` |
| symbol count | 5500 |
| adjustment policies | `qfq` |
| non-null 1d returns | 1308398 |
| non-null 20d volatility | 1204130 |
| rebalance date | `2025-12-03` |
| rebalance candidates | 5431 |
| top20 count | 20 |
| evaluation end | `2025-12-31` |
| forward pairs | 20 |
| top20 equal-weight forward return | -0.030161233615864508 |

## Boundary / Risk Notes

| 边界 | 状态 | 说明 |
|---|---|---|
| full-history raw/canonical candidate | COMPLETED | 2015-01-05..2026-05-28 的全 A `prices` / `adj_factor` candidate 已写入并可审计。 |
| production current truth | NOT_CLAIMED | 未 publish current pointer；不能把本轮 candidate 直接称为 production current truth。 |
| PIT universe | NOT_CLOSED | 2015-2025 年度行情已补齐，但完整 PIT universe、退市、ST、停牌、涨跌停和全量 trade_status 仍需独立补强。 |
| 可复权性 | PASS_FOR_OBSERVED_PRICES | 所有已观测 `prices` 交易对均有对应 `adj_factor`，支持后续 qfq/hfq derived view 或收益口径重跑。 |
| extra adj_factor pairs | ACCEPTED_AS_NON_BLOCKING | 额外复权因子 pair 不代表真实可交易行情，后续派生视图应以 `prices` observed pairs 为分母。 |
| publish gate | BLOCKED | 仍需 PIT / quality / claim boundary 决策和 Explicit Publish Gate。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 2015 至今真实抓取与写湖完成 | PASS | 年度 run summary | 已覆盖 2015-01-05..2026-05-28 的开市日。 |
| `prices` / `adj_factor` pair audit 完成 | PASS | Aggregate Audit | `missing_adj_for_price_pairs_total=0`。 |
| current pointer 未变更 | PASS | publish count=0 | 本轮没有进入 publish。 |
| 后续研究可进入候选重跑 | PASS_WITH_BOUNDARY | Boundary / Risk Notes | 可用于 candidate research rerun；严肃 production claim 仍需 PIT / W3 数据补齐。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| raw / manifest 真实写湖 | `<configured-env-lake-root>` | PASS | 路径脱敏；本文件不记录真实 lake root。 |
| canonical candidate | `<configured-env-lake-root>` | PASS | `prices` / `adj_factor` run-scoped canonical parquet。 |
| S14 检查记录 | `process/checks/REAL-TUSHARE-CR014-S14-FULL-HISTORY-PRICES-ADJ-FACTOR-PULL-2026-05-29.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS_FULL_HISTORY_PRICES_ADJ_FACTOR_CANDIDATE_PULLED_PUBLISH_BLOCKED`
- 已完成：2015-01-05 至 2026-05-28 的全 A `prices` / `adj_factor` raw、manifest、canonical candidate 写入和年度审计。
- 可用性：所有已观测 `prices` 交易对均有对应 `adj_factor`，后续可以基于 candidate 做 qfq/hfq 派生视图、收益、低波动和阶段三到五重跑。
- 未完成：本轮不关闭 PIT universe、ST、停牌、涨跌停、指数成分、指数权重、行业市值和完整 trade_status 缺口；不允许自动 publish；不声明 production current truth。
- 下一步：补 PIT universe、全量 `trade_status`、`prices_limit`、指数成分 / 权重等 P0/W3 缺口；如需 publish，必须单独发起 Explicit Publish Gate 决策并接受 non-PIT / W3 风险。
