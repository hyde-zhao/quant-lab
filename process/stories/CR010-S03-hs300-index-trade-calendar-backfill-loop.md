---
story_id: "CR010-S03-hs300-index-trade-calendar-backfill-loop"
title: "hs300_index + trade_calendar 历史回补闭环"
story_slug: "hs300-index-trade-calendar-backfill-loop"
status: "verified"
priority: "P0"
wave: "CR010-DL-BATCH-A"
depends_on: ["CR010-S01-multidataset-plan-run-publish-cli-contract", "CR007-S02-benchmark-calendar-backfill"]
dependency_contracts:
  - upstream: "CR010-S01-multidataset-plan-run-publish-cli-contract"
    type: "contract"
    required: "publish/read/revalidate/replay 生命周期已冻结"
  - upstream: "CR007-S02-benchmark-calendar-backfill"
    type: "contract"
    required: "benchmark resolver 与 calendar coverage 语义已冻结"
file_ownership:
  primary:
    - "market_data/contracts.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
    - "tests/test_market_data_normalization_validation_readers.py"
  shared:
    - "market_data/catalog.py"
    - "market_data/cli.py"
  forbidden:
    - "engine/**"
    - "experiments/**"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
lld_gate:
  status: "approved"
  cp5_batch: "CR010-DL-BATCH-A"
  lld_path: "process/stories/CR010-S03-hs300-index-trade-calendar-backfill-loop-LLD.md"
dev_gate:
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  safety_boundary: "offline-only; no real source, no real lake write, no credentials"
created_at: "2026-05-22T15:13:28+08:00"
updated_at: "2026-05-22T15:13:28+08:00"
source_hld: "process/HLD-DATA-LAKE.md"
source_adr: "process/ARCHITECTURE-DECISION.md"
change_id: "CR-010"
execution:
  cp6_status: "PASS"
  cp6_checkpoint: "process/checks/CP6-CR010-S03-hs300-index-trade-calendar-backfill-loop-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR010-S03-hs300-index-trade-calendar-backfill-loop-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T15:30:00+08:00"
---

# CR010-S03：hs300_index + trade_calendar 历史回补闭环

## 目标

建立 `hs300_index` 与 `trade_calendar` 的离线生产闭环，确保 benchmark resolver 只读取真实发布的 `hs300_index`，`trade_calendar` 作为 coverage denominator 的 open dates 来源，禁止用 proxy 填充真实沪深 300 字段。

## 映射

| 类型 | 映射 |
|---|---|
| CR | CR-010 P0 dataset readiness、benchmark/current truth |
| HLD | `process/HLD-DATA-LAKE.md` §4.1、§5、§7 |
| ADR | ADR-031、ADR-032、ADR-034 |

## 验收标准

- `hs300_index` 字段含 `index_code`、OHLC、`pre_close`、`pct_chg`、volume/amount、source lineage、`available_at_rule=daily_close_fact`。
- `trade_calendar` 字段含 `exchange`、`is_open`、`pretrade_date`、source lineage、`available_at_rule`。
- coverage denominator 使用 `trade_calendar.is_open=true`，不得用自然日覆盖率代替。
- 缺真实 `hs300_index` 时 resolver 返回 `required_missing` 或 proxy separation，不静默补 proxy。

## 安全边界

不运行真实 benchmark 回补；不读取旧数据证明 calendar coverage；不触发 consumer backfill。
