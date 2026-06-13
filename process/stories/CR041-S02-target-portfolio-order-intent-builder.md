---
story_id: "CR041-S02-target-portfolio-order-intent-builder"
title: "Target Portfolio and Order Intent Builder"
story_slug: "target-portfolio-order-intent-builder"
status: "verified-with-risk"
priority: "P0"
wave: "CR041-W1-PAPER-SIMULATION-FOUNDATION"
depends_on:
  - "CR041-S01-strategy-admission-package-reader"
cp5_batch: "CR041-PAPER-SIMULATION-LLD-BATCH-A"
implementation_allowed: true
change_id: "CR-041"
file_ownership:
  primary:
    - "engine/paper_simulation.py"
  shared:
    - "engine/order_intent_draft.py"
  merge_owner: "CR041-S02-target-portfolio-order-intent-builder"
  forbidden:
    - "broker order payload"
    - "qfq / hfq execution price"
    - "real account field"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "target portfolio to order intent contract"
    - "T close signal and T+1 open execution semantics"
    - "A-share lot and cash precheck boundary"
  rationale: "订单意图是本地模拟成交的输入，不得被误用为真实订单。"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  implementation_allowed: true
---

# CR041-S02：Target Portfolio and Order Intent Builder

## 目标

把 S01 的策略准入视图转成目标组合和本地 `paper_order_intent_v1`，只表达 symbol、side、目标股数或目标权重、信号日、目标交易日和价格策略，不生成任何真实 broker payload。

## 技术说明

完整设计证据见 `process/stories/CR041-S02-target-portfolio-order-intent-builder-LLD.md`。CP5 批次确认前不得实现。

## 实现证据

- 实现文件：`engine/paper_simulation.py`
- 测试文件：`tests/test_cr041_paper_simulation.py`
- 实现说明：`process/stories/CR041-S02-target-portfolio-order-intent-builder-IMPLEMENTATION.md`
- CP6：`process/checks/CP6-CR041-S02-target-portfolio-order-intent-builder-CODING-DONE.md`
- 当前状态：CP7 `PASS_WITH_RISK`，进入 `verified-with-risk`；剩余低风险过程项汇入 CP8。
