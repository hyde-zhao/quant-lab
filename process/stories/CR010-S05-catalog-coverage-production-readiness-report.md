---
story_id: "CR010-S05-catalog-coverage-production-readiness-report"
title: "catalog coverage 与 production readiness report"
story_slug: "catalog-coverage-production-readiness-report"
status: "verified"
priority: "P0"
wave: "CR010-DL-BATCH-A"
depends_on:
  - "CR010-S02-prices-adj-factor-history-backfill-loop"
  - "CR010-S03-hs300-index-trade-calendar-backfill-loop"
  - "CR010-S04-index-members-weights-stock-basic-readiness"
dependency_contracts:
  - upstream: "CR010-S02-prices-adj-factor-history-backfill-loop"
    type: "runtime"
    required: "prices/adj_factor metadata 与 validation 输出已冻结"
  - upstream: "CR010-S03-hs300-index-trade-calendar-backfill-loop"
    type: "runtime"
    required: "hs300_index/trade_calendar coverage 与 resolver policy 已冻结"
  - upstream: "CR010-S04-index-members-weights-stock-basic-readiness"
    type: "runtime"
    required: "membership/weights/stock_basic readiness 与 PIT policy 已冻结"
file_ownership:
  primary:
    - "market_data/catalog.py"
    - "market_data/readers.py"
    - "market_data/validation.py"
    - "tests/test_cr010_data_lake_publish_and_contracts.py"
  shared:
    - "market_data/cli.py"
    - "engine/research_dataset.py"
  forbidden:
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
lld_gate:
  status: "approved"
  cp5_batch: "CR010-DL-BATCH-A"
  lld_path: "process/stories/CR010-S05-catalog-coverage-production-readiness-report-LLD.md"
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
  cp6_checkpoint: "process/checks/CP6-CR010-S05-catalog-coverage-production-readiness-report-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR010-S05-catalog-coverage-production-readiness-report-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T15:30:00+08:00"
---

# CR010-S05：catalog coverage 与 production readiness report

## 目标

输出 catalog coverage report 与 production readiness report，把当前 published catalog 的 dataset/date range/source/interface/quality/readiness/PIT/known limitations 明确为 current truth，同时披露外置 lake 当前只含 `prices` 与 `hs300_index` 的事实不能代表完整 P0 数据湖。

## 映射

| 类型 | 映射 |
|---|---|
| CR | CR-010 current truth、production readiness、实验消费边界 |
| HLD | `process/HLD-DATA-LAKE.md` §5、§6、§8 |
| ADR | ADR-031、ADR-034、ADR-035 |

## 验收标准

- coverage report 列出 P0 七个 dataset 的 publish 状态、date range、quality/readiness/PIT 状态和 limitations。
- production strict 对缺 PIT、缺真实 benchmark、缺 W3、缺复权、quality fail 返回阻断。
- exploratory 可读取 warn，但必须输出 limitation 和 blocked_claims。
- 报告不把本地 `data/**` 或 legacy `reports/data_quality_report.csv` 当作 production current truth。

## 安全边界

只读取传入 tmp lake / fixture catalog；真实 `/mnt/ugreen-data-lake` 只能在用户另行授权的 smoke 中读取，不在本批次默认执行。
