# REAL Tushare CR018 Release Publish

| 字段 | 值 |
|---|---|
| 日期 | 2026-05-29 |
| lake root | `/mnt/ugreen-data-lake` |
| release_id | `release-cr018-production-current-truth-20150101-20260528-20260529` |
| release_run_id | `run-cr018-release-full-history-20150101-20260528-20260529` |
| approval_id | `user-approved-cr018-production-current-truth-20260529` |
| 操作范围 | 修正 full-history catalog metadata、生成 release audit、显式发布 10 个核心 dataset current pointer |
| provider fetch | `0` |
| QMT 操作 | `0` |
| `.env` / token | 本步骤未读取凭据；未输出、未写入、未记录 token |
| 结论 | CR018 production strict 数据湖发布 PASS；10 个核心 dataset 均为 `published/pass/available` |

## 执行命令

```bash
uv run --python 3.11 python -m py_compile scripts/cr018_release_catalog_publish.py

uv run --python 3.11 python scripts/cr018_release_catalog_publish.py \
  --lake-root /mnt/ugreen-data-lake \
  --approval-id user-approved-cr018-production-current-truth-20260529 \
  --approved-by user \
  --operator codex \
  --execute-publish
```

## 发布结果

| 检查 | 结果 |
|---|---|
| `explicit_publish_gate.status` | `allowed` |
| `explicit_publish_gate.allowed` | `true` |
| `published_count` | `10` |
| `current_pointer_publish_count` | `10` |
| `catalog_current_pointer_publish_count` | `10` |
| `post_publish_readiness_status` | `pass` |
| `post_publish_blockers` | `[]` |

发布证据输出：

```text
/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/cr018_release_publish_readiness_audit.json
/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/cr018_explicit_publish_gate_decision.json
/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/cr018_release_publish_execution.json
/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/cr018_post_publish_readiness.json
/mnt/ugreen-data-lake/quality/run-cr018-release-full-history-20150101-20260528-20260529/cr018_release_publish_summary.json
```

## 核心 Dataset Current Pointer

| dataset | canonical_path | coverage_denominator | quality |
|---|---|---:|---|
| `prices` | `canonical/prices/1.0/run_id=run-cr018-release-full-history-20150101-20260528-20260529` | 11,311,360 | `pass` |
| `adj_factor` | `canonical/adj_factor/1.0/run_id=run-cr018-release-full-history-20150101-20260528-20260529` | 11,823,057 | `pass` |
| `hs300_index` | `canonical/hs300_index/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-benchmark-index-daily.parquet` | 11,072 | `pass` |
| `trade_calendar` | `canonical/trade_calendar/1.0/run_id=run-cr014-s14-trade-calendar-2015-2026-232302` | 2,768 | `pass` |
| `index_members` | `canonical/index_members/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-benchmark-index-members.parquet` | 276,600 | `pass` |
| `index_weights` | `canonical/index_weights/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-benchmark-index-weights.parquet` | 276,600 | `pass` |
| `stock_basic` | `canonical/stock_basic/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-stock-basic-lifecycle.parquet` | 5,850 | `pass` |
| `trade_status` | `canonical/trade_status/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-trade-status-2015.parquet` | 11,311,360 | `pass` |
| `prices_limit` | `canonical/prices_limit/1.0/run_id=run-cr018-price-limit-lifecycle-cleanup-20150101-20260528-20260529` | 11,220,342 | `pass` |
| `events` | `canonical/events/1.0/run_id=run-cr018-missing-data-backfill-20150101-20260528-p0p1-20260529/part-events-stock-st.parquet` | 323,698 | `pass` |

## Release Staging

`prices` 和 `adj_factor` 已从 full-history yearly runs 聚合到 release-scoped canonical run：

| dataset | 文件数 | 行数 | hardlink | copy | exists |
|---|---:|---:|---:|---:|---:|
| `prices` | 2,768 | 11,311,360 | 2,768 | 0 | 0 |
| `adj_factor` | 2,768 | 11,823,057 | 2,768 | 0 | 0 |

`prices` / `adj_factor` 的 source runs：

```text
run-cr014-s14-prices-adj-factor-2015-232405
run-cr014-s14-prices-adj-factor-2016-233430
run-cr014-s14-prices-adj-factor-2017-233927
run-cr014-s14-prices-adj-factor-2018-234359
run-cr014-s14-prices-adj-factor-2019-234833
run-cr014-s14-prices-adj-factor-2020-235353
run-cr014-s14-prices-adj-factor-2021-235843
run-cr014-s14-prices-adj-factor-2022-000336
run-cr014-s14-prices-adj-factor-2023-000913
run-cr014-s14-prices-adj-factor-2024-001432
run-cr014-s14-prices-adj-factor-2025-001949
run-cr014-s11-full-a-2026-ytd-date-batch-143508
```

## 独立复验

```bash
uv run --python 3.11 python -m market_data.cli report-readiness \
  --lake-root /mnt/ugreen-data-lake \
  --realism-mode production_strict

uv run --python 3.11 pytest -q \
  tests/test_cr018_publish_current_reader_smoke.py \
  tests/test_cr018_readiness_rollback_gate.py \
  tests/test_cr014_catalog_publish_gate.py

uv run --python 3.11 python -m market_data.cli read \
  --lake-root /mnt/ugreen-data-lake \
  --dataset prices \
  --start-date 2019-12-16 \
  --end-date 2019-12-16 \
  --symbols 001914.SZ \
  --limit 3
```

结果：

| 检查 | 结果 |
|---|---|
| `report-readiness --realism-mode production_strict` | PASS，`status=pass`，`blockers=[]`，`candidate_unpublished_count=0`，`published_count=10` |
| 目标 pytest | `18 passed in 0.52s` |
| current reader smoke | PASS，`dataset=prices`，`symbol=001914.SZ`，`trade_date=2019-12-16`，`row_count=1` |

current reader smoke 样例要点：

```json
{
  "dataset": "prices",
  "symbol": "001914.SZ",
  "trade_date": "2019-12-16",
  "adjustment_policy": "qfq",
  "source_run_id": "run-cr014-s14-prices-adj-factor-2019-234833",
  "available_at_rule": "daily_close_fact",
  "row_count": 1
}
```

## Claim 边界

`report-readiness` 当前允许：

```json
["production_strict_research"]
```

`production_current_truth` 在 CLI `blocked_claims` 中仍作为更强的持续生产声明保留边界；本次发布已经完成的是 release-scoped current pointer 完整发布，后续严肃回测应以 `production_strict_research` claim 和本 release current truth 作为输入。

## 已消除的问题

| 旧问题 | 本次处理 |
|---|---|
| `prices` / `adj_factor` catalog 仍指向 2026 YTD | 改为 release full-history run，范围 `2015-01-01`..`2026-05-28` |
| `trade_calendar` catalog 仍指向 YTD | 改为 `run-cr014-s14-trade-calendar-2015-2026-232302` |
| `events.available_at_rule` 缺失 | 写入 `tushare_stock_st_09:20` |
| 核心 dataset 未 published | 10 个核心 dataset 全部通过 Explicit Publish Gate 并发布 |
| `prices_limit` lifecycle/code-change 缺口 | 使用 cleanup run，覆盖率口径 PASS |

## 下一步建议

1. 使用 release current truth 重跑阶段三到阶段五核心研究，输出 production rerun 报告。
2. 将回测读取入口默认切到 published current reader，禁止继续使用旧 proxy / candidate 输入。
3. 在研究结论 PASS 后，再讨论 QMT simulation admission；当前 QMT 操作计数保持 `0`。
