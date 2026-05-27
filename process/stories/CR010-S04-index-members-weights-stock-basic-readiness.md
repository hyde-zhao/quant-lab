---
story_id: "CR010-S04-index-members-weights-stock-basic-readiness"
title: "index_members/index_weights/stock_basic readiness 强化"
story_slug: "index-members-weights-stock-basic-readiness"
status: "verified"
priority: "P0"
wave: "CR010-DL-BATCH-A"
depends_on: ["CR010-S01-multidataset-plan-run-publish-cli-contract", "CR007-S03-index-members-stock-basic-datasets"]
dependency_contracts:
  - upstream: "CR010-S01-multidataset-plan-run-publish-cli-contract"
    type: "contract"
    required: "catalog publish metadata 与 quality policy 已冻结"
  - upstream: "CR007-S03-index-members-stock-basic-datasets"
    type: "contract"
    required: "index_members / index_weights / stock_basic 基础 dataset 合同已冻结"
file_ownership:
  primary:
    - "market_data/contracts.py"
    - "market_data/normalization.py"
    - "market_data/validation.py"
    - "market_data/readers.py"
    - "tests/test_market_data_multidataset_quality_readers.py"
  shared:
    - "market_data/catalog.py"
    - "engine/universe.py"
  forbidden:
    - "experiments/**"
    - "data/**"
    - "reports/**"
    - ".env"
    - "credentials"
lld_gate:
  status: "approved"
  cp5_batch: "CR010-DL-BATCH-A"
  lld_path: "process/stories/CR010-S04-index-members-weights-stock-basic-readiness-LLD.md"
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
  cp6_checkpoint: "process/checks/CP6-CR010-S04-index-members-weights-stock-basic-readiness-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_checkpoint: "process/checks/CP7-CR010-S04-index-members-weights-stock-basic-readiness-VERIFICATION-DONE.md"
  verified_at: "2026-05-22T15:30:00+08:00"
---

# CR010-S04：index_members/index_weights/stock_basic readiness 强化

## 目标

强化 `index_members`、`index_weights`、`stock_basic` 的 readiness/PIT 状态，明确三者不可互相替代：`index_members` 才能证明成分集合，`index_weights` 不是完整 membership，`stock_basic` 只辅助，不证明 PIT universe。

## 映射

| 类型 | 映射 |
|---|---|
| CR | CR-010 P0 dataset readiness、PIT limitation disclosure |
| HLD | `process/HLD-DATA-LAKE.md` §4.1、§5、§7 |
| ADR | ADR-031、ADR-033、ADR-034 |

## 验收标准

- 缺 `available_at`、`available_date` 或 `effective_date` 时不得标记 PIT available。
- `index_weights` 缺完整 membership proof 时标记 `pit_incomplete/non_pit_snapshot`。
- `stock_basic` 只能输出辅助状态，不能替代历史成分股 universe。
- reader / report 暴露 readiness_status、pit_status、known_limitations。

## 安全边界

不读取旧 `data/**` 或真实 lake 判断 PIT；未确认 source/interface 前只能报告 limitation 或 required_missing。
