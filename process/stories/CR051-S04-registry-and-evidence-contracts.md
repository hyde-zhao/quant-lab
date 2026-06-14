---
story_id: "CR051-S04-registry-and-evidence-contracts"
title: "研究 registry 与证据合同"
story_slug: "registry-and-evidence-contracts"
status: "verified"
priority: "P0"
wave: "CR051-W2-HOST-REGISTRY"
depends_on:
  - "CR051-S01-lifecycle-and-taxonomy-framework"
  - "CR051-S02-repository-archive-and-data-lake-governance"
dependency_type:
  - "contract"
  - "manifest-boundary"
cp5_batch: "CR051-STRATEGY-RESEARCH-LIFECYCLE-BATCH-A"
feature_design_refs:
  - "docs/features/strategy-research-lifecycle/DESIGN.md"
  - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["registry-contract", "manifest-schema", "validation-evidence", "guardrail"]
  rationale: "本 Story 定义 RunManifest、ArchiveManifest、ValidationEvidence 和 MigrationInventory 的字段合同，是后续自动校验入口。"
  waiver_reason: ""
  revisit_condition: "新增 manifest schema、registry 存储实现或 guardrail 测试时。"
  evidence_path: "process/stories/CR051-S04-registry-and-evidence-contracts-LLD.md"
file_ownership:
  primary:
    - "docs/research/RESEARCH-REGISTRY-SPEC.md"
  shared:
    - "docs/research/RESEARCH-ARCHIVE-MANIFEST-SPEC.md"
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  merge_owner: "CR051-S04-registry-and-evidence-contracts"
  forbidden:
    - "schema that stores credentials"
    - "runtime verified claim without runtime evidence"
lld_gate:
  required_inputs:
    - "CR051-S01-lifecycle-and-taxonomy-framework"
    - "CR051-S02-repository-archive-and-data-lake-governance"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR051-S04-registry-and-evidence-contracts-LLD.md"
  status: "approved"
implementation_gate:
  evidence_required: true
  evidence_path: "process/stories/CR051-S04-registry-and-evidence-contracts-IMPLEMENTATION.md"
  evidence_type: "implementation-md"
  implementation_objects: ["template-schema", "guardrail-test"]
  test_plan_refs:
    - "docs/features/strategy-research-lifecycle/TEST-PLAN.md"
  local_validation_results:
    - "process/checks/CP6-CR051-S04-registry-and-evidence-contracts-CODING-DONE.md"
  status: "PASS"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR051-S04-registry-and-evidence-contracts-CODING-DONE.md"
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR051-S04-registry-and-evidence-contracts-VERIFICATION-DONE.md"
task_count: 2
created_at: "2026-06-14T08:19:09+08:00"
updated_at: "2026-06-14T09:00:24+08:00"
change_id: "CR-051"
---

# CR051-S04：研究 registry 与证据合同

## 目标

冻结 ResearchRun、ValidationEvidence、ResearchArchiveManifest、ProjectIdentity 和 MigrationInventory 的 registry / manifest 字段、验证规则和 guardrail 入口。

## 开发上下文（dev_context）

**输入文件**：S01 lifecycle、S02 archive governance、FEAT-10 TEST-PLAN。

**输出文件**：`docs/research/RESEARCH-REGISTRY-SPEC.md`。

**设计约束**：registry 合同只保存指针、hash、release ref 和脱敏摘要，不保存凭据、账号、broker facts 或大 artifact。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | DOMAIN-MAP OBJ-37..43、RULE-17..23 |
| 文件影响 | 新增 research registry spec |
| 接口 / 数据 / 权限变化 | 新增 manifest / registry 文档合同；无代码和 runtime |
| 异常、失败与回退 | 字段不足时 blocked，不得静默生成 delivery_candidate |
| 测试入口 | TC-CR051-02、TC-CR051-06、SEC-TC-01、SEC-TC-03 |
| 风险与重访条件 | 后续实现 schema 校验或 registry 存储时重访 |

## 实现摘要

| 项目 | 内容 |
|---|---|
| 实现证据 | `process/stories/CR051-S04-registry-and-evidence-contracts-IMPLEMENTATION.md` |
| CP6 结果 | `process/checks/CP6-CR051-S04-registry-and-evidence-contracts-CODING-DONE.md`，PASS |
| 输出文件 | `docs/research/RESEARCH-REGISTRY-SPEC.md` |
| 剩余风险 | CP7 需验证 registry 不保存凭据、账户、broker facts 原文和 runtime-ready claim |
