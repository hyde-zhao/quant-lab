---
story_id: "CR041-S03-paper-broker-fill-engine"
title: "PaperBroker Fill Engine"
story_slug: "paper-broker-fill-engine"
status: "verified-with-risk"
priority: "P0"
wave: "CR041-W2-FILL-LEDGER"
depends_on:
  - "CR041-S01-strategy-admission-package-reader"
  - "CR041-S02-target-portfolio-order-intent-builder"
cp5_batch: "CR041-PAPER-SIMULATION-LLD-BATCH-A"
implementation_allowed: true
change_id: "CR-041"
file_ownership:
  primary:
    - "engine/paper_simulation.py"
  shared: []
  merge_owner: "CR041-S03-paper-broker-fill-engine"
  forbidden:
    - "market order submission"
    - "external quote subscription"
    - "minute / tick / Level2 dependency"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "local fill model"
    - "cost and slippage"
    - "limit up/down, suspension and partial fill"
  rationale: "成交模型决定模拟盘真实度和风险边界，必须先完成 CP5 设计确认。"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  implementation_allowed: true
---

# CR041-S03：PaperBroker Fill Engine

## 目标

在本地日频数据上模拟成交：T+1 raw open 执行、fixed bps 滑点、手续费税费、涨跌停/停牌/成交量参与率约束和 partial fill / rejected / expired 状态。该 Story 不连接任何 broker。

## 技术说明

完整设计证据见 `process/stories/CR041-S03-paper-broker-fill-engine-LLD.md`。CP5 批次确认前不得实现。

## 实现证据

- 实现文件：`engine/paper_simulation.py`
- 测试文件：`tests/test_cr041_paper_simulation.py`
- 实现说明：`process/stories/CR041-S03-paper-broker-fill-engine-IMPLEMENTATION.md`
- CP6：`process/checks/CP6-CR041-S03-paper-broker-fill-engine-CODING-DONE.md`
- 当前状态：CP7 `PASS_WITH_RISK`，进入 `verified-with-risk`；剩余低风险过程项汇入 CP8。
