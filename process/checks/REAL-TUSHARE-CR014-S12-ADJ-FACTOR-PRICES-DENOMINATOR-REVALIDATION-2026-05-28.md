---
check_id: "REAL-TUSHARE-CR014-S12-ADJ-FACTOR-PRICES-DENOMINATOR-REVALIDATION-2026-05-28"
type: "real_candidate_quality_revalidation"
status: "PASS_ADJ_FACTOR_OBSERVED_PRICE_DENOMINATOR_PUBLISH_BLOCKED"
owner: "meta-po"
created_at: "2026-05-28T22:56:17+08:00"
checked_at: "2026-05-28T22:56:17+08:00"
change_id: "CR-014"
story_id: "CR014-S09-windowed-real-fetch-lake-write-run"
full_a_run_id: "run-cr014-s11-full-a-2026-ytd-date-batch-143508"
date_range: "2026-01-01..2026-05-28"
open_trade_dates: 94
lake_root: "<configured-env-lake-root>"
publish_current_pointer: false
duckdb_files_created: 0
---

# REAL Tushare CR014-S12 Adj Factor Prices Denominator Revalidation

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| S11 全 A raw / manifest / canonical candidate 已完成 | PASS | `process/checks/REAL-TUSHARE-CR014-S11-FULL-A-2026-YTD-PULL-2026-05-28.md` | 2026 YTD `prices` / `adj_factor` 188/188 batch success。 |
| S11 join smoke 显示价格行全部匹配复权因子 | PASS | S11 `prices-adj_factor join` | `price rows=515055`，`price_adj_missing=0`。 |
| QA 侧向检查完成 | PASS | `meta-qa` agent `019e6f10-8f62-7052-bba0-7d9278cbe3ac` | QA 确认该口径适合验证“已观测 price rows 可复权”，但不能替代 PIT/full-A denominator。 |
| 不泄露凭据 | PASS | 运行方式 | `.env` 仅用于运行时注入；本检查不记录 token 和真实 lake root。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | CLI 增加 `adj_factor` observed prices denominator | PASS | `market_data/cli.py` | 新增 `--use-prices-denominator`，仅允许 `dataset=adj_factor`，从同一 `run_id` 的 canonical `prices` 生成 expected pairs。 |
| 2 | validation 不允许额外行掩盖缺失 pair | PASS | `market_data/validation.py` | expected-pair 模式下 coverage numerator 使用 `expected_pairs ∩ actual_pairs`，而不是总行数。 |
| 3 | 回归测试 | PASS | `tests/test_cr010_data_lake_publish_and_contracts.py` | 覆盖 observed prices denominator pass、extra rows 不能掩盖 missing pair、trade_status denominator 和 manifest scoped 行为。 |
| 4 | 测试执行 | PASS | `pytest` | 5 个目标测试通过；`py_compile` 通过。 |
| 5 | 真实 candidate 重验 | PASS | quality report | `adj_factor` 在 `prices_observed_trade_date_symbol_pairs` denominator 下 `quality_status=pass`。 |
| 6 | 价格交易对复权完整性 | PASS | candidate pair audit | `price_observed_pairs=515055`，`adj_factor_pairs=516604`，`price_adj_missing=0`，`adj_factor_extra_pairs=1549`。 |
| 7 | 复权因子数值有效性 | PASS | candidate pair audit | `adj_factor_null=0`，`adj_factor_non_positive=0`。 |
| 8 | publish gate | PASS | `read_dataset` | `prices` 和 `adj_factor` current read 均因 `catalog_not_published` 被阻止。 |
| 9 | DuckDB 边界 | PASS | scan | 配置湖 `.duckdb` 文件数为 0。 |

## Revalidation Result

| Field | Value |
|---|---|
| dataset | `adj_factor` |
| run_id | `run-cr014-s11-full-a-2026-ytd-date-batch-143508` |
| denominator_mode | `prices_observed_trade_date_symbol_pairs` |
| quality_status | `pass` |
| dataset_status | `available` |
| expected_rows | `515055` |
| actual_rows | `516604` |
| missing_rows | `0` |
| missing_rate | `0.0` |
| issue_count | `0` |
| warnings | `[]` |
| source_interface | `prices.adj_factor` |
| catalog_status | `candidate_unpublished` |

## Boundary / Risk Notes

| 边界 | 状态 | 说明 |
|---|---|---|
| observed price denominator | ACCEPTED_FOR_ADJ_FACTOR_USABILITY | 只证明已抓到的 `prices` 行都有可用复权因子。 |
| full-A coverage | NOT_CLAIMED | 该口径继承 `prices` 缺口，不能发现价格本身缺失的股票 / 日期。 |
| production publish | BLOCKED | `prices` 仍为 warn，PIT universe / tradability denominator 未闭环；本轮没有 publish 授权。 |
| current truth | UNCHANGED | candidate 仍未发布，current pointer 未更新。 |
| since-inception claim | NOT_CLAIMED | 本轮窗口仅为 `2026-01-01..2026-05-28`，不能表述为 2015 至今或 since-inception。 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| `adj_factor` 对已观测 `prices` 的复权可用性 | PASS | `price_adj_missing=0` | 可以支持 2026 YTD candidate 级复权研究 smoke。 |
| 质量报告口径明确 | PASS | `denominator_mode=prices_observed_trade_date_symbol_pairs` | 不再把该结果误读为 full-A × open trade dates coverage。 |
| 发布边界保持 | PASS | `catalog_not_published` | 未更新 current pointer。 |
| 后续生产缺口明确 | PASS_WITH_OPEN_GAP | PIT / tradability denominator | 下一步仍应补 `trade_status`、上市/退市、ST/停牌、PIT universe，再重验 `prices`。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CLI denominator 支持 | `market_data/cli.py` | PASS | `--use-prices-denominator`。 |
| validation expected-pair 修正 | `market_data/validation.py` | PASS | 防止 extra rows 掩盖缺失 expected pair。 |
| 回归测试 | `tests/test_cr010_data_lake_publish_and_contracts.py` | PASS | 目标测试通过。 |
| S12 检查记录 | `process/checks/REAL-TUSHARE-CR014-S12-ADJ-FACTOR-PRICES-DENOMINATOR-REVALIDATION-2026-05-28.md` | PASS | 本文件。 |

## 结论

- 结论：`PASS_ADJ_FACTOR_OBSERVED_PRICE_DENOMINATOR_PUBLISH_BLOCKED`
- 已关闭：S11 中 `adj_factor` 因使用全市场 open dates × symbols 分母造成的 candidate 可用性误判；按 `prices` 已观测交易对重验为 `pass`。
- 未关闭：`prices` 自身仍未满足生产 publish 证据链；PIT / tradability denominator 仍是下一步阻断项。
- 下一步：实现低成本的 `trade_status` / lifecycle denominator 方案，重验 `prices`，再决定是否 publish 2026 candidate 或扩展到 2015 至今。
