---
story_id: "CR046-S05-verification-framework-and-evidence-model"
title: "验证框架与证据模型"
story_slug: "verification-framework-and-evidence-model"
status: "ready-for-verification"
priority: "P0"
wave: "CR046-W3-VALIDATION-GATES"
depends_on:
  - "CR046-S01-dual-target-strategy-architecture"
  - "CR046-S02-strategy-package-contract-and-schema"
  - "CR046-S03-qmt-terminal-target-framework"
  - "CR046-S04-miniqmt-runner-install-and-runtime-boundary"
dependency_type:
  - "contract"
  - "contract"
  - "contract"
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md"
  - "docs/features/runtime-authorization-safety/DESIGN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["validation", "evidence-model", "safety-claim"]
  rationale: "验证框架决定 CR046 能声明什么，必须 full-lld 防止 design/static/fixture 被误读为 runtime verified。"
  waiver_reason: ""
  revisit_condition: "后续新增 runtime verified 证据类型时。"
  evidence_path: "process/stories/CR046-S05-verification-framework-and-evidence-model-LLD.md"
file_ownership:
  primary:
    - "docs/qmt/CR046-VERIFICATION-FRAMEWORK.md"
  shared:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
    - "docs/qmt/CR046-MINIQMT-RUNNER-INSTALL-DESIGN.md"
  merge_owner: "CR046-S05-verification-framework-and-evidence-model"
  forbidden:
    - "runtime verified claim"
    - "real terminal validation"
    - "real runner connection"
lld_gate:
  required_inputs:
    - "CR046-S01-dual-target-strategy-architecture"
    - "CR046-S02-strategy-package-contract-and-schema"
    - "CR046-S03-qmt-terminal-target-framework"
    - "CR046-S04-miniqmt-runner-install-and-runtime-boundary"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR046-S05-verification-framework-and-evidence-model-LLD.md"
  status: "confirmed"
dev_gate:
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
task_count: 4
created_at: "2026-06-13T22:57:34+08:00"
updated_at: "2026-06-14T00:16:26+08:00"
change_id: "CR-046"
---

# CR046-S05：验证框架与证据模型

## 目标

定义 CR046 可产出的 schema/static/fixture/dry-run plan/manual plan 证据，并明确这些证据不等于 QMT / MiniQMT runtime verified。

## 开发上下文（dev_context）

**输入文件**：CR046-S01..S04、FEAT-09 TEST-PLAN、FEAT-07 safety。

**输出文件**：`docs/qmt/CR046-VERIFICATION-FRAMEWORK.md`。

**设计约束**：不得执行真实终端验证，不得连接 MiniQMT，不得声明 runtime verified。

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 文件影响 | 新增验证框架文档 |
| 接口 / 数据 / 权限变化 | 新增 StrategyValidationEvidence 证据分级；无 runtime |
| 测试入口 | docs guardrail、schema/static/fixture plan |

## 量化验收标准（acceptance_criteria）

- [ ] 证据层级至少包含 schema、static guardrail、fixture dry-run、QMT terminal shadow plan、MiniQMT install dry-run plan、runtime verified 6 类。
- [ ] CR046 明确 runtime verified 为 unavailable / not-authorized。
- [ ] 每个 target 至少有 1 个验证入口和 1 个失败路径。

## 阻塞说明

任何 runtime verified 声明必须后置真实运行 CR。
