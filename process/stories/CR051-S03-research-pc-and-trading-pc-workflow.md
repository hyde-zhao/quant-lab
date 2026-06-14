---
story_id: "CR051-S03-research-pc-and-trading-pc-workflow"
title: "研究主机与交易主机工作流边界"
story_slug: "research-pc-and-trading-pc-workflow"
status: "verified"
priority: "P0"
wave: "CR051-W2-HOST-REGISTRY"
depends_on:
  - "CR051-S02-repository-archive-and-data-lake-governance"
  - "CR051-S06-project-identity-rename-and-legacy-alias"
dependency_type:
  - "contract"
  - "alias-policy"
cp5_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
feature_design_refs:
  - "docs/features/strategy-research-lifecycle/DESIGN.md"
  - "docs/features/strategy-research-lifecycle/TASKS.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["host-workflow", "package-consumer-boundary", "migration-safety"]
  rationale: "本 Story 决定研究主机、NAS、交易主机之间的职责和文件流，影响迁移和交易环境安全。"
  waiver_reason: ""
  revisit_condition: "交易主机开始消费 package、MiniQMT runner 安装或实际迁移启动时。"
  evidence_path: "process/stories/CR051-S03-research-pc-and-trading-pc-workflow-LLD.md"
file_ownership:
  primary:
    - "docs/research/HOST-WORKFLOW.md"
  shared:
    - "docs/research/ARCHIVE-GOVERNANCE.md"
    - "docs/research/PROJECT-IDENTITY-MIGRATION.md"
  merge_owner: "CR051-S03-research-pc-and-trading-pc-workflow"
  forbidden:
    - "trading PC as research archive host"
    - "MiniQMT connection"
    - "runtime execution"
lld_gate:
  required_inputs:
    - "CR051-S02-repository-archive-and-data-lake-governance"
    - "CR051-S06-project-identity-rename-and-legacy-alias"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR051-S03-research-pc-and-trading-pc-workflow-LLD.md"
  status: "approved"
implementation_gate:
  evidence_required: true
  evidence_path: "process/stories/CR051-S03-research-pc-and-trading-pc-workflow-IMPLEMENTATION.md"
  evidence_type: "implementation-md"
  implementation_objects: ["docs-handoff", "migration-plan"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results:
    - "process/checks/CP6-CR051-S03-research-pc-and-trading-pc-workflow-CODING-DONE.md"
  status: "PASS"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR051-S03-research-pc-and-trading-pc-workflow-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR051-S03-research-pc-and-trading-pc-workflow-VERIFICATION-DONE.md"
task_count: 1
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T09:00:24+08:00"
change_id: "CR-051"
---

# CR051-S03：研究主机与交易主机工作流边界

## 目标

冻结主力研究主机、NAS 热 / 温 / 冷层、交易主机之间的职责、文件流、package exchange 和不授权边界。

## 开发上下文（dev_context）

**输入文件**：S02 archive governance、S06 identity alias policy、HLD-CR051 硬件事实。

**输出文件**：`docs/research/HOST-WORKFLOW.md`。

**设计约束**：交易主机只消费已校验 package，不做研究开发、不挂 full research archive、不触发 QMT / MiniQMT runtime。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | DQ-CP3-CR051-02/03、FEAT-10 DESIGN |
| 文件影响 | 新增 host workflow 文档 |
| 接口 / 数据 / 权限变化 | 无真实主机操作；仅定义职责合同 |
| 异常、失败与回退 | 若用户要求交易主机承载研究环境，需回退 CP3 重新决策 |
| 测试入口 | TC-CR051-03、SEC-TC-05 |
| 风险与重访条件 | CR049 MiniQMT 或后续 package consumer CR 启动时重访 |

## 实现摘要

| 项目 | 内容 |
|---|---|
| 实现证据 | `process/stories/CR051-S03-research-pc-and-trading-pc-workflow-IMPLEMENTATION.md` |
| CP6 结果 | `process/checks/CP6-CR051-S03-research-pc-and-trading-pc-workflow-CODING-DONE.md`，PASS |
| 输出文件 | `docs/research/HOST-WORKFLOW.md` |
| 剩余风险 | CP7 需验证交易主机仅 package consumer、无 transfer/import/runtime 措辞 |
