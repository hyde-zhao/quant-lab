---
story_id: "CR051-S02-repository-archive-and-data-lake-governance"
title: "仓库、研究归档与数据湖边界治理"
story_slug: "repository-archive-and-data-lake-governance"
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
  trigger_reasons: ["archive-governance", "storage-tiering", "migration", "safety-boundary"]
  rationale: "本 Story 涉及 Git、research archive、market data lake、broker lake 和 NAS 冷热分层，必须 full-lld 冻结安全边界。"
  waiver_reason: ""
  revisit_condition: "启动真实 archive migration、NAS 操作或数据湖发布改造时。"
  evidence_path: "process/stories/CR051-S02-repository-archive-and-data-lake-governance-LLD.md"
file_ownership:
  primary:
    - "docs/research/ARCHIVE-GOVERNANCE.md"
    - "docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md"
  shared:
    - "docs/features/strategy-research-lifecycle/DESIGN.md"
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  merge_owner: "CR051-S02-repository-archive-and-data-lake-governance"
  forbidden:
    - "NAS scan / mount / copy / delete / migration"
    - "raw market data in Git"
    - "broker facts in research archive"
lld_gate:
  required_inputs:
    - "docs/design/HLD-CR051-STRATEGY-RESEARCH-LIFECYCLE-FRAMEWORK.md"
    - "docs/design/DEPENDENCY-MAP.md"
    - "docs/features/strategy-research-lifecycle/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR051-S02-repository-archive-and-data-lake-governance-LLD.md"
  status: "approved"
implementation_gate:
  evidence_required: true
  evidence_path: "process/stories/CR051-S02-repository-archive-and-data-lake-governance-IMPLEMENTATION.md"
  evidence_type: "implementation-md"
  implementation_objects: ["docs-handoff", "guardrail-test"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results:
    - "process/checks/CP6-CR051-S02-repository-archive-and-data-lake-governance-CODING-DONE.md"
  status: "PASS"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR051-S02-repository-archive-and-data-lake-governance-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR051-S02-repository-archive-and-data-lake-governance-VERIFICATION-DONE.md"
task_count: 2
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T09:00:24+08:00"
change_id: "CR-051"
---

# CR051-S02：仓库、研究归档与数据湖边界治理

## 目标

冻结一个主 Git 仓库、外部 research archive、market data lake、broker archive 和当前硬件冷热分层的职责边界。

## 开发上下文（dev_context）

**输入文件**：HLD-CR051、BLUEPRINT FEAT-10、DEPENDENCY-MAP FD-17..23。

**输出文件**：`docs/research/ARCHIVE-GOVERNANCE.md`、`docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md`。

**设计约束**：CP5 前不得访问 NAS、不得写真实 archive、不得写 lake、不得发布 catalog。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR051、DQ-CP3-CR051-02、FEAT-10 DESIGN |
| 文件影响 | 新增 archive governance 和 archive manifest spec |
| 接口 / 数据 / 权限变化 | 只新增文档合同；真实 archive root 操作未授权 |
| 异常、失败与回退 | 若计划需要真实扫描或搬迁，转入独立 runtime_authorization / migration gate |
| 测试入口 | TC-CR051-02、TC-CR051-03、SEC-TC-01、SEC-TC-02 |
| 风险与重访条件 | 真实 NAS 迁移或 market data lake publish 改造时重访 |

## 实现摘要

| 项目 | 内容 |
|---|---|
| 实现证据 | `process/stories/CR051-S02-repository-archive-and-data-lake-governance-IMPLEMENTATION.md` |
| CP6 结果 | `process/checks/CP6-CR051-S02-repository-archive-and-data-lake-governance-CODING-DONE.md`，PASS |
| 输出文件 | `docs/research/ARCHIVE-GOVERNANCE.md`、`docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md` |
| 剩余风险 | CP7 需验证 Git / archive / lake / broker facts 边界和未授权操作计数 |
