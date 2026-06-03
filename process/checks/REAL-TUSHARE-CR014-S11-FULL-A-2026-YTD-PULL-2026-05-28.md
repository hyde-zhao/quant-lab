---
check_id: "REAL-TUSHARE-CR014-S11-FULL-A-2026-YTD-PULL-2026-05-28"
type: "real_full_a_pull_validation"
status: "RAW_MANIFEST_PULL_PASS_CANONICAL_PASS_QUALITY_GAP"
owner: "meta-po"
created_at: "2026-05-28T22:39:50+08:00"
checked_at: "2026-05-28T22:39:50+08:00"
change_id: "CR-014"
story_id: "CR014-S11-full-a-2026-ytd-prices-adj-factor-pull"
probe_run_id: "run-cr014-s11-full-a-date-probe-20260105-143422"
full_a_run_id: "run-cr014-s11-full-a-2026-ytd-date-batch-143508"
date_range: "2026-01-01..2026-05-28"
open_trade_dates: 94
lake_root: "<configured-env-lake-root>"
publish_current_pointer: false
duckdb_files_created: 0
---

# REAL Tushare CR014-S11 Full-A 2026 YTD Pull

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| S10 样本可用性验证通过 | PASS | `process/checks/REAL-TUSHARE-CR014-S10-2026-USABILITY-VALIDATION-2026-05-28.md` | 样本链路可 normalize / validate / candidate read。 |
| 单日全 A 探针 | PASS | `run-cr014-s11-full-a-date-probe-20260105-143422` | `2026-01-05` 全 A `prices` 5457 行，`adj_factor` 5475 行。 |
| 用户批准拉取 | PASS | 用户回复“按照推荐的意见进行验证和拉取” | 本轮拉取仅写 raw/manifest/canonical/quality candidate，不 publish。 |
| 不泄露凭据 | PASS | 运行方式 | token 只通过 `.env` 注入运行时。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 说明 |
|---|---|---|---|---|
| 1 | 交易日列表 | PASS | 2026 calendar candidate | open trade dates = 94。 |
| 2 | 全 A `prices` 日期批次拉取 | PASS | manifest | 94/94 batch success，raw rows = 515055。 |
| 3 | 全 A `adj_factor` 日期批次拉取 | PASS | manifest | 94/94 batch success，raw rows = 516604。 |
| 4 | manifest 记录 | PASS | manifest | 本 run 188 条 manifest，全 success。 |
| 5 | normalize `prices` | PASS | canonical candidate | 94 个 parquet，515055 行。 |
| 6 | normalize `adj_factor` | PASS | canonical candidate | 94 个 parquet，516604 行。 |
| 7 | `prices` quality | WARN_ACCEPTED | quality report | expected_rows=519820，actual_rows=515055，missing_rows=4765，missing_rate=0.9167%，warn。 |
| 8 | `adj_factor` quality | FAIL_EXPECTED_GAP | quality report | expected_rows=520384，actual_rows=516604，missing_rows=3780，missing_rate=0.7264%，issue=`coverage_gap`。 |
| 9 | prices-adj_factor join | PASS | candidate join smoke | 515055 price rows 全部匹配 adj_factor，join missing=0。 |
| 10 | return smoke | PASS | candidate calculation | 5530 个 price symbols，94 个交易日，非空 stock return 509525 条。 |
| 11 | publish gate | PASS | `cmd_read` | `prices` current read 因 `catalog_not_published` 被阻止。 |
| 12 | DuckDB 边界 | PASS | scan | 配置湖 `.duckdb` 文件数为 0。 |

## Pull Results

| Interface | Batches | Status | Raw Rows |
|---|---:|---|---:|
| `prices.daily` | 94 | success | 515055 |
| `prices.adj_factor` | 94 | success | 516604 |
| total | 188 | success | 1031659 |

## Candidate / Quality Results

| Dataset | Canonical Paths | Rows | Quality Status | Expected Rows | Missing Rows | Missing Rate | Published |
|---|---:|---:|---|---:|---:|---:|---|
| `prices` | 94 | 515055 | warn | 519820 | 4765 | 0.9167% | false |
| `adj_factor` | 94 | 516604 | fail | 520384 | 3780 | 0.7264% | false |

## Gap Analysis

| Gap | 影响 | 结论 |
|---|---|---|
| `prices` / `adj_factor` 使用实际出现 symbol × open dates 做分母 | 晚上市、退市、停牌、不可交易状态会被误算为缺失 | 当前 full-A quality 不能作为 publish 依据 |
| PIT universe 缺失 | 无法区分当日不存在、已退市、停牌、真实缺失 | 需要接入历史成分、上市退市、停牌/ST/交易状态后重验 |
| `adj_factor` generic coverage threshold 为 1.0 | 0.7264% coverage gap 被标记为 fail | 在 PIT denominator 之前不应 publish |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| 2026 YTD 全 A raw/manifest 拉取 | PASS | 188/188 success | 真实拉取已完成。 |
| 2026 YTD 全 A canonical candidate | PASS | prices/adj_factor 各 94 个 parquet | normalize 成功。 |
| 质量可发布 | FAIL_EXPECTED_GAP | adj_factor quality fail | 缺 PIT/tradability denominator，不允许 publish。 |
| 研究 smoke | PASS_WITH_GAP | returns / join 可计算 | 可用于 QA/探索，不可作为生产 current truth。 |

## 结论

- 结论：`RAW_MANIFEST_PULL_PASS_CANONICAL_PASS_QUALITY_GAP`
- 已完成：2026 YTD 全 A `prices` 与 `adj_factor` 的真实 raw/manifest 拉取和 canonical candidate 生成。
- 不允许 publish：`adj_factor` quality fail，`prices` warn；核心原因是 PIT universe / 交易状态 denominator 缺失，而不是 raw 写湖失败。
- 下一步：补 `trade_status` / 上市退市 / PIT universe denominator 后，对 full-A 2026 candidate 重新 validate；通过后再考虑 publish 或扩展到 2015 至今。
