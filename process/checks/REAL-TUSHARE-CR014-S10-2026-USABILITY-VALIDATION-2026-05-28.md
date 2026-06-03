---
check_id: "REAL-TUSHARE-CR014-S10-2026-USABILITY-VALIDATION-2026-05-28"
type: "real_data_usability_validation"
status: "PASS_SAMPLE_USABILITY_NOT_PUBLISHABLE_SAMPLE_ONLY"
owner: "meta-po"
created_at: "2026-05-28T22:39:50+08:00"
checked_at: "2026-05-28T22:39:50+08:00"
change_id: "CR-014"
story_id: "CR014-S10-2026-data-usability-validation"
source_run_id: "run-cr014-s09-ytd-config-lake-20260528-141907"
date_range: "2026-01-01..2026-05-28"
lake_root: "<configured-env-lake-root>"
publish_current_pointer: false
duckdb_files_created: 0
---

# REAL Tushare CR014-S10 2026 Sample Usability Validation

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 配置湖 raw/manifest 已写入 | PASS | `process/checks/REAL-TUSHARE-CR014-S09-YTD-CONFIG-LAKE-VERIFY-2026-05-28.md` | 7 个真实 batch，manifest 全 success。 |
| 用户批准推荐验证口径 | PASS | 用户回复“按照推荐的意见进行验证和拉取” | 允许生成 candidate / quality，不 publish，先用 2026 样本验证。 |
| 不 publish | PASS | 本轮未执行 `publish` | 只生成 canonical / quality / catalog candidate-unpublished。 |
| 不泄露凭据 | PASS | 运行方式 | 通过 `uv --env-file .env` 注入 token；未打印、未写文档、未保存 token。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | 修复 validate manifest context | PASS | `market_data/cli.py` | 同一 run_id 多 dataset 时，validate 现在按目标 dataset 过滤 manifest，避免 `prices` 质量报告误取 `stock_basic.snapshot`。 |
| 2 | 定向回归测试 | PASS | `tests/test_cr010_data_lake_publish_and_contracts.py` | 新增 `test_validate_manifest_context_is_scoped_to_target_dataset`。 |
| 3 | normalize `trade_calendar` | PASS | canonical candidate | 148 行，1 个 parquet。 |
| 4 | normalize `stock_basic` | PASS | canonical candidate | 5524 行，1 个 parquet。 |
| 5 | normalize `hs300_index` | PASS | canonical candidate | 94 行，1 个 parquet。 |
| 6 | normalize `adj_factor` 样本 | PASS | canonical candidate | 188 行，2 个 parquet。 |
| 7 | normalize `prices` 样本 | PASS | canonical candidate | 188 行，2 个 parquet。 |
| 8 | validate `trade_calendar` | PASS | quality report | expected_rows=148，actual_rows=148，missing_rate=0。 |
| 9 | validate `hs300_index` | PASS | quality report | expected_rows=94，actual_rows=94，missing_rate=0。 |
| 10 | validate `stock_basic` | PASS | quality report | 快照可用；仍不是 PIT universe。 |
| 11 | validate `adj_factor` 样本 | PASS | quality report | expected_rows=188，actual_rows=188，missing_rate=0。 |
| 12 | validate `prices` 样本 | WARN_ACCEPTED | quality report | expected_rows=188，actual_rows=188，missing_rate=0；warn 原因为 `warn_non_pit_universe`。 |
| 13 | candidate read smoke | PASS | direct canonical read | 5 个 dataset 均能从 canonical candidate 读取。 |
| 14 | 最小研究 smoke | PASS | return / join 计算 | benchmark return 93 条；样本股票 return 186 条；prices-adj_factor join 缺失 0；excess return 186 条。 |
| 15 | published read gate | PASS | `cmd_read` | `trade_calendar`、`hs300_index`、`prices` 均因 `catalog_not_published` 被阻止，符合不 publish 预期。 |
| 16 | DuckDB 边界 | PASS | scan | 配置湖 `.duckdb` 文件数为 0。 |

## Validation Results

| Dataset | Normalize Rows | Validate Status | Expected Rows | Actual Rows | Missing Rate | Catalog Status | Published |
|---|---:|---|---:|---:|---:|---|---|
| `trade_calendar` | 148 | pass | 148 | 148 | 0.0 | candidate_unpublished | false |
| `stock_basic` | 5524 | pass | 148 | 5524 | 0.0 | candidate_unpublished | false |
| `hs300_index` | 94 | pass | 94 | 94 | 0.0 | candidate_unpublished | false |
| `adj_factor` sample | 188 | pass | 188 | 188 | 0.0 | candidate_unpublished | false |
| `prices` sample | 188 | warn | 188 | 188 | 0.0 | candidate_unpublished | false |

## Research Smoke

| 检查 | 结果 |
|---|---:|
| open trade dates | 94 |
| benchmark return non-null | 93 |
| sample stock return non-null | 186 |
| prices-adj_factor join rows | 188 |
| prices-adj_factor missing | 0 |
| adj_factor positive rows | 188 |
| excess return non-null | 186 |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 样本数据可用性 | PASS | normalize / validate / candidate read / research smoke | 2026 样本从 raw 到 candidate 研究输入的闭环可用。 |
| 不可 publish 为 current truth | PASS | 样本仅 2 个股票 | 不应把样本数据发布为生产 current。 |
| 显式 publish gate 保持 | PASS | current read 被 `catalog_not_published` 阻止 | validate PASS/WARN 不会自动 publish。 |
| 进入全 A 拉取 | PASS | 单日全 A 探针已通过 | 允许进入 S11 全 A 2026 YTD 日期批次拉取。 |

## 结论

- 结论：`PASS_SAMPLE_USABILITY_NOT_PUBLISHABLE_SAMPLE_ONLY`
- 已完成：2026 样本数据 raw/manifest -> canonical candidate -> quality -> candidate read -> 最小研究 smoke。
- 已修复：同一 run 多 dataset 的 validate manifest context 误绑定问题，定向回归 `3 passed`。
- 未执行：publish current pointer、DuckDB 写入、旧 `data/**` 迁移。
- 下一步：进入全 A 2026 YTD `prices` / `adj_factor` 日期批次拉取与质量验证。
