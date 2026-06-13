---
story_id: "CR041-S05-cli-report-artifacts"
title: "CLI and Report Artifacts"
story_slug: "cli-report-artifacts"
status: "verified-with-risk"
priority: "P0"
wave: "CR041-W3-RUNNER-REPORT"
depends_on:
  - "CR041-S01-strategy-admission-package-reader"
  - "CR041-S02-target-portfolio-order-intent-builder"
  - "CR041-S03-paper-broker-fill-engine"
  - "CR041-S04-position-cash-equity-ledger"
cp5_batch: "CR041-PAPER-SIMULATION-LLD-BATCH-A"
implementation_allowed: true
change_id: "CR-041"
file_ownership:
  primary:
    - "scripts/run_paper_simulation.py"
    - "tests/test_cr041_paper_simulation.py"
  shared:
    - "engine/paper_simulation.py"
  merge_owner: "CR041-S05-cli-report-artifacts"
  forbidden:
    - "provider fetch"
    - "lake write"
    - "catalog publish"
    - "simulation/live run"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "repeatable CLI runner"
    - "report artifact contract"
    - "no-real-operation guardrail"
  rationale: "CLI 和报告是用户实际消费入口，必须在实现前冻结输入、输出和安全计数。"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  implementation_allowed: true
---

# CR041-S05：CLI and Report Artifacts

## 目标

提供可复跑的本地 runner 和报告 artifact 合同，输出 order intents、fills、positions、cash ledger、equity curve、reconciliation 和 forbidden operation counters。该 Story 不做 provider fetch、lake write 或 publish。

## 技术说明

完整设计证据见 `process/stories/CR041-S05-cli-report-artifacts-LLD.md`。CP5 批次确认前不得实现。

## 实现证据

- 实现文件：`engine/paper_simulation.py`、`scripts/run_paper_simulation.py`
- 测试文件：`tests/test_cr041_paper_simulation.py`
- 实现说明：`process/stories/CR041-S05-cli-report-artifacts-IMPLEMENTATION.md`
- CP6：`process/checks/CP6-CR041-S05-cli-report-artifacts-CODING-DONE.md`
- 当前状态：CP7 `PASS_WITH_RISK`，进入 `verified-with-risk`；剩余低风险过程项汇入 CP8。
