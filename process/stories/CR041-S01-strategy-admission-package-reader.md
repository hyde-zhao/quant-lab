---
story_id: "CR041-S01-strategy-admission-package-reader"
title: "StrategyAdmissionPackage Reader"
story_slug: "strategy-admission-package-reader"
status: "verified-with-risk"
priority: "P0"
wave: "CR041-W1-PAPER-SIMULATION-FOUNDATION"
depends_on: []
cp5_batch: "CR041-PAPER-SIMULATION-LLD-BATCH-A"
implementation_allowed: true
change_id: "CR-041"
file_ownership:
  primary:
    - "engine/paper_simulation.py"
  shared: []
  merge_owner: "CR041-S01-strategy-admission-package-reader"
  forbidden:
    - "broker connection"
    - "Backtrader runtime"
    - "QMT / MiniQMT / XtQuant / Goldminer call"
    - "credential read"
    - "order submit or cancel"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "research-to-simulation boundary"
    - "fail-closed admission validation"
    - "no-real-operation guardrail"
  rationale: "CR039 package 是 CR041 的唯一策略输入边界，必须完整校验后才能构建本地模拟目标。"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  implementation_allowed: true
---

# CR041-S01：StrategyAdmissionPackage Reader

## 目标

只读消费 CR039 `STRATEGY-ADMISSION-PACKAGE.json`，校验 `research_baseline`、`simulation_candidate=false`、blocked claims 和 forbidden operation counters，输出本地 paper simulation 可消费的策略准入视图。该 Story 不把 CR039 输出升级为 simulation-ready 或 live-ready。

## 技术说明

完整设计证据见 `process/stories/CR041-S01-strategy-admission-package-reader-LLD.md`。CP5 批次确认前不得实现。

## 实现证据

- 实现文件：`engine/paper_simulation.py`
- 测试文件：`tests/test_cr041_paper_simulation.py`
- 实现说明：`process/stories/CR041-S01-strategy-admission-package-reader-IMPLEMENTATION.md`
- CP6：`process/checks/CP6-CR041-S01-strategy-admission-package-reader-CODING-DONE.md`
- 当前状态：CP7 `PASS_WITH_RISK`，进入 `verified-with-risk`；剩余低风险过程项汇入 CP8。
