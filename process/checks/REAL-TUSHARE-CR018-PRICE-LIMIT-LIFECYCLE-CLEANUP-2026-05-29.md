# REAL Tushare CR018 Price Limit Lifecycle Cleanup

| 字段 | 值 |
|---|---|
| 日期 | 2026-05-29 |
| run_id | `run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529` |
| lake root | `/mnt/ugreen-data-lake` |
| 范围 | `2015-01-01`..`2026-05-28` |
| 真实 provider | Tushare |
| 凭据处理 | 从 `.env` 读取；未输出、未写入、未记录 token |
| QMT 操作 | `0` |
| current pointer publish | `0` |
| 结论 | `prices_limit` 生命周期 / 代码变更清理 PASS；仍为 candidate，未发布 current truth |

## 执行命令

```bash
uv run --env-file .env --group tushare --python 3.11 python scripts/cr018_price_limit_lifecycle_cleanup.py \
  --start 2015-01-01 \
  --end 2026-05-28 \
  --run-id run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529 \
  --sleep-seconds 0
```

## 写入数据

| dataset | 行数 | 说明 |
|---|---:|---|
| `bse_code_mapping` | 248 | Tushare `bse_mapping` 北交所新旧代码映射 |
| `lifecycle_code_change` | 250 | 248 条 BJ 映射 + 2 条深市代码变更清理规则 |
| `prices_limit_code_change_fixes` | 1,129 | 深市 code-change 补齐行 |
| `prices_limit_coverage_exclusions` | 91,018 | 不应计入涨跌停覆盖率分母的记录 |
| `prices_limit` | 13,649,823 | 新的清理后 candidate run |

输出路径：

```text
/mnt/ugreen-data-lake/canonical/bse_code_mapping/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/part-bse-code-mapping.parquet
/mnt/ugreen-data-lake/canonical/lifecycle_code_change/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/part-lifecycle-code-change.parquet
/mnt/ugreen-data-lake/canonical/prices_limit/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/
/mnt/ugreen-data-lake/canonical/prices_limit_code_change_fixes/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/part-prices-limit-code-change-fixes.parquet
/mnt/ugreen-data-lake/canonical/prices_limit_coverage_exclusions/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/part-prices-limit-coverage-exclusions.parquet
/mnt/ugreen-data-lake/quality/run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/cr018_price_limit_lifecycle_cleanup_summary.json
/mnt/ugreen-data-lake/quality/run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529/cr018_price_limit_lifecycle_cleanup_validation.json
```

## 清理规则

| 规则 | 处理 |
|---|---|
| BJ 北交所开市前 / 个股北交所有效起始日前 | 从 `prices_limit` 覆盖率分母排除，原因 `before_bse_effective_start` |
| `000043.SZ -> 001914.SZ` | `2019-12-16` 前用 `000043.SZ` 查询 `stk_limit`，映射回 `001914.SZ` |
| `001872.SZ -> 000022.SZ` provider 边界 | `2018-12-19`..`2018-12-20` 用 `001872.SZ` 查询结果映射回 `000022.SZ` |
| 科创板首日无涨跌幅限制 | 从分母排除，原因 `star_market_first_trading_day_no_price_limit` |

## 验证结果

```json
{
  "price_pair_total": 11311360,
  "cleaned_limit_pairs_total": 13649823,
  "raw_missing_after_code_change_fixes": 91018,
  "excluded_missing_pairs": 91018,
  "adjusted_denominator": 11220342,
  "unresolved_missing_pairs": 0,
  "coverage_ratio_after_cleanup": 1.0,
  "exclusion_reason_counts": {
    "before_bse_effective_start": 91017,
    "star_market_first_trading_day_no_price_limit": 1
  },
  "status": "pass"
}
```

深市 code-change 补齐明细：

| symbol | source_symbol | 行数 | 日期范围 |
|---|---|---:|---|
| `001914.SZ` | `000043.SZ` | 1,127 | `2015-01-05`..`2019-12-13` |
| `000022.SZ` | `001872.SZ` | 2 | `2018-12-19`..`2018-12-20` |

## Catalog 状态

`prices_limit` catalog 已指向新的 cleanup candidate：

```json
{
  "published": false,
  "quality_status": "pass",
  "dataset_status": "available",
  "latest_manifest_run_id": "run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529",
  "canonical_path": "canonical/prices_limit/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529",
  "coverage_denominator": 11220342,
  "coverage_ratio": 1.0,
  "source_interface": "cr018_price_limit_lifecycle_cleanup"
}
```

## 回归验证

```bash
uv run --python 3.11 python -m py_compile scripts/cr018_price_limit_lifecycle_cleanup.py
uv run --python 3.11 pytest -q tests/test_market_data_tushare_datasets.py tests/test_cr018_pit_tradability_readiness.py tests/test_cr018_benchmark_group_readiness.py tests/test_cr018_p1_auxiliary_claim_boundary.py
uv run --python 3.11 -m market_data.cli report-readiness --lake-root /mnt/ugreen-data-lake --realism-mode production_strict
```

结果：

| 检查 | 结果 |
|---|---|
| `py_compile` | PASS |
| 目标 pytest | `31 passed` |
| `report-readiness` | FAIL |

`report-readiness` 仍然 FAIL 的原因不是 `prices_limit` 覆盖率缺口，而是生产发布门尚未完成：

| blocker | 说明 |
|---|---|
| `dataset_not_published` | `prices`、`adj_factor`、`hs300_index`、`trade_calendar`、`index_members`、`index_weights`、`stock_basic`、`trade_status`、`prices_limit`、`events` 仍为 candidate |
| `quality_warn_blocked` | `prices` catalog 仍为 `warn_non_pit_universe` |
| `events_available_at_missing` | `events` catalog entry 缺少发布级 `available_at_rule` |
| W3 current truth blockers | `trade_status`、`prices_limit`、`events` 未发布 current truth |

## 后续动作

1. 将 `prices` / `adj_factor` catalog 指向 2015-2026 全历史 run，而不是 2026 YTD run。
2. 修复 `events` catalog 的 `available_at_rule` 元数据。
3. 对全部 P0/W3 dataset 执行 release-level publish readiness audit。
4. 通过 Explicit Publish Gate 后再发布 current pointer。
