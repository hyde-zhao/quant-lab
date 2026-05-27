---
story_id: "CR010-S02-prices-adj-factor-history-backfill-loop"
title: "prices + adj_factor 历史回补闭环"
story_slug: "prices-adj-factor-history-backfill-loop"
status: "verified"
priority: "P0"
wave: "CR010-DL-BATCH-A"
depends_on: ["CR010-S01-multidataset-plan-run-publish-cli-contract"]
dependency_contracts:
  - upstream: "CR010-S01-multidataset-plan-run-publish-cli-contract"
    type: "contract"
    required: "CLI lifecycle、publish gate、catalog metadata 合同已冻结"
file_ownership:
  primary:
    - "market_data/contracts.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "tests/test_market_data_multidataset_quality_readers.py"
  shared:
    - "market_data/readers.py"
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
  lld_path: "process/stories/CR010-S02-prices-adj-factor-history-backfill-loop-LLD.md"
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
  cp6_checkpoint: "process/checks/CP6-CR010-S02-prices-adj-factor-history-backfill-loop-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR010-S02-prices-adj-factor-history-backfill-loop-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T15:30:00+08:00"
---

# CR010-S02：prices + adj_factor 历史回补闭环

## 目标

把 `prices` 与 `adj_factor` 建成可离线验证的成对 dataset 闭环，冻结 qfq 复权字段、`available_at_rule=daily_close_fact`、OHLC/重复键/coverage/adjustment consistency 校验与 catalog metadata。

## 映射

| 类型 | 映射 |
|---|---|
| CR | CR-010 P0 dataset readiness |
| HLD | `process/HLD-DATA-LAKE.md` §4.1、§4.3、§5 |
| ADR | ADR-032、ADR-034 |

## 验收标准

- `prices` canonical 含 OHLCV、amount、source lineage、`available_at`、`available_at_rule`、adjusted price policy。
- `adj_factor` 独立 canonical，字段含 `adj_factor`、`adjustment_policy`、source lineage 和可用时点。
- `prices` 与 `adj_factor` 缺口、重复 key、复权冲突和 OHLC 异常均可被 validate 捕获。
- publish metadata 暴露 date range、run_id、lineage checksum、quality/readiness/pit status 和 known limitations。

## 安全边界

仅使用 fixture/tmp lake；不从真实 provider 或旧 `data/**` 推导 coverage，不把 legacy report 当作 current truth。
