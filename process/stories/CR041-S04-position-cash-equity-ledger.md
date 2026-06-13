---
story_id: "CR041-S04-position-cash-equity-ledger"
title: "Position / Cash / Equity Ledger"
story_slug: "position-cash-equity-ledger"
status: "verified-with-risk"
priority: "P0"
wave: "CR041-W2-FILL-LEDGER"
depends_on:
  - "CR041-S01-strategy-admission-package-reader"
  - "CR041-S02-target-portfolio-order-intent-builder"
  - "CR041-S03-paper-broker-fill-engine"
cp5_batch: "CR041-PAPER-SIMULATION-LLD-BATCH-A"
implementation_allowed: true
change_id: "CR-041"
file_ownership:
  primary:
    - "engine/paper_simulation.py"
  shared: []
  merge_owner: "CR041-S04-position-cash-equity-ledger"
  forbidden:
    - "real account query"
    - "broker reconciliation"
    - "broker lake write"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "cash and position accounting"
    - "T+1 sellable quantity"
    - "equity curve and reconciliation"
  rationale: "账本是模拟结果可信度核心，必须覆盖现金、持仓、净值和对账失败路径。"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  implementation_allowed: true
---

# CR041-S04：Position / Cash / Equity Ledger

## 目标

根据 S03 的本地 fill 更新现金、持仓、可卖数量、成本、净值曲线、回撤、换手和对账摘要。该 Story 的账本只服务本地 paper simulation，不读取真实账户。

## 技术说明

完整设计证据见 `process/stories/CR041-S04-position-cash-equity-ledger-LLD.md`。CP5 批次确认前不得实现。

## 实现证据

- 实现文件：`engine/paper_simulation.py`
- 测试文件：`tests/test_cr041_paper_simulation.py`
- 实现说明：`process/stories/CR041-S04-position-cash-equity-ledger-IMPLEMENTATION.md`
- CP6：`process/checks/CP6-CR041-S04-position-cash-equity-ledger-CODING-DONE.md`
- 当前状态：CP7 `PASS_WITH_RISK`，进入 `verified-with-risk`；剩余低风险过程项汇入 CP8。
