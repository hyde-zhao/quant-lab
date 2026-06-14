---
story_id: "CR051-S01-lifecycle-and-taxonomy-framework"
title: "策略研究生命周期与 taxonomy 框架"
story_slug: "lifecycle-and-taxonomy-framework"
status: "verified"
priority: "P0"
wave: "CR051-W1-LIFECYCLE-ARCHIVE-IDENTITY"
depends_on: []
dependency_type: []
cp5_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
feature_design_refs:
  - "docs/features/strategy-research-lifecycle/DESIGN.md"
  - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["lifecycle", "taxonomy", "cross-feature", "claim-boundary"]
  rationale: "本 Story 冻结策略从 idea 到 delivery_candidate 的主状态机和 taxonomy，是 CR052..CR056 的共同入口。"
  waiver_reason: ""
  revisit_condition: "启动 CR052 多因子完整证明周期或新增策略族时。"
  evidence_path: "process/stories/CR051-S01-lifecycle-and-taxonomy-framework-LLD.md"
file_ownership:
  primary:
    - "docs/research/LIFECYCLE.md"
    - "docs/research/STRATEGY-TAXONOMY.md"
  shared:
    - "docs/features/strategy-research-lifecycle/DESIGN.md"
    - "docs/features/strategy-research-lifecycle/TASKS.md"
  merge_owner: "CR051-S01-lifecycle-and-taxonomy-framework"
  forbidden:
    - "concrete strategy implementation"
    - "runtime authorization"
    - "QMT / MiniQMT operation"
lld_gate:
  required_inputs:
    - "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
    - "docs/design/FEATURE-DESIGN-MATRIX.md"
    - "docs/features/strategy-research-lifecycle/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR051-S01-lifecycle-and-taxonomy-framework-LLD.md"
  status: "approved"
implementation_gate:
  evidence_required: true
  evidence_path: "process/stories/CR051-S01-lifecycle-and-taxonomy-framework-IMPLEMENTATION.md"
  evidence_type: "implementation-md"
  implementation_objects: ["docs-handoff", "template-schema"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results:
    - "process/checks/CP6-CR051-S01-lifecycle-and-taxonomy-framework-CODING-DONE.md"
  status: "PASS"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR051-S01-lifecycle-and-taxonomy-framework-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR051-S01-lifecycle-and-taxonomy-framework-VERIFICATION-DONE.md"
task_count: 2
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T09:00:24+08:00"
change_id: "CR-051"
---

# CR051-S01：策略研究生命周期与 taxonomy 框架

## 目标

冻结 InformationSource、StrategyIdea、ResearchProject、ResearchProtocol、ResearchRun、ValidationEvidence 和 delivery_candidate 的生命周期、taxonomy 与 claim boundary。

## 开发上下文（dev_context）

**输入文件**：`docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md`、`docs/features/strategy-research-lifecycle/DESIGN.md`。

**输出文件**：`docs/research/LIFECYCLE.md`、`docs/research/STRATEGY-TAXONOMY.md`。

**设计约束**：不得实现具体策略，不得声明 runtime verified，不得启动 QMT / MiniQMT / provider / lake / publish。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR051、FEAT-10 DESIGN / TEST-PLAN、DOMAIN-MAP SM-13 |
| 文件影响 | 新增生命周期和 taxonomy 文档 |
| 接口 / 数据 / 权限变化 | 新增研究 lifecycle 文档契约；无 runtime 权限变化 |
| 异常、失败与回退 | 若 delivery_candidate 被误读为 trade-ready，回退修改 claim boundary |
| 测试入口 | TC-CR051-01、TC-CR051-06 |
| 风险与重访条件 | 后续 CR052 启动时重访 taxonomy 字段 |

## 实现摘要

| 项目 | 内容 |
|---|---|
| 实现证据 | `process/stories/CR051-S01-lifecycle-and-taxonomy-framework-IMPLEMENTATION.md` |
| CP6 结果 | `process/checks/CP6-CR051-S01-lifecycle-and-taxonomy-framework-CODING-DONE.md`，PASS |
| 输出文件 | `docs/research/LIFECYCLE.md`、`docs/research/STRATEGY-TAXONOMY.md` |
| 剩余风险 | CP7 需验证 delivery/runtime/trade-ready claim boundary |
