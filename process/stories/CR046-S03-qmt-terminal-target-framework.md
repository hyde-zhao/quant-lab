---
story_id: "CR046-S03-qmt-terminal-target-framework"
title: "QMT terminal target 框架"
story_slug: "qmt-terminal-target-framework"
status: "ready-for-verification"
priority: "P0"
wave: "CR046-W2-TARGETS-INSTALL"
depends_on:
  - "CR046-S02-strategy-package-contract-and-schema"
dependency_type:
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  - "docs/features/runtime-authorization-safety/DESIGN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["external-terminal", "security-boundary", "no-runtime"]
  rationale: "QMT terminal target 接近真实交易终端，必须 full-lld 冻结导入步骤、配置和 shadow evidence 边界。"
  waiver_reason: ""
  revisit_condition: "用户授权 QMT terminal shadow / 模拟盘运行验证时。"
  evidence_path: "process/stories/CR046-S03-qmt-terminal-target-framework-LLD.md"
file_ownership:
  primary:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
  shared:
    - "docs/qmt/CR046-VERIFICATION-FRAMEWORK.md"
  merge_owner: "CR046-S03-qmt-terminal-target-framework"
  forbidden:
    - "QMT terminal runtime validation"
    - "account query"
    - "submit/cancel"
lld_gate:
  required_inputs:
    - "CR046-S02-strategy-package-contract-and-schema"
    - "docs/features/runtime-authorization-safety/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR046-S03-qmt-terminal-target-framework-LLD.md"
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

# CR046-S03：QMT terminal target 框架

## 目标

定义 QMT 终端策略入口、配置样例、人工导入步骤、shadow 报告格式和本 CR 不执行终端验证的安全边界。

## 开发上下文（dev_context）

**输入文件**：CR046-S02、FEAT-09 DESIGN、FEAT-07 runtime safety。

**输出文件**：`docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md`、`docs/qmt/CR046-VERIFICATION-FRAMEWORK.md`。

**设计约束**：不得执行 QMT 终端运行、不得查询账户、不得下单或撤单。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR046-S02 | contract | package contract 可读 | package contract 冻结 | terminal target 消费策略包合同 |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 文件影响 | QMT target 设计文档和验证计划 |
| 接口 / 数据 / 权限变化 | 无新增 runtime 权限；仅定义 target contract |
| 异常、失败与回退 | 任何真实运行请求转 runtime_authorization gate |
| 测试入口 | docs guardrail / manual plan review |

## 量化验收标准（acceptance_criteria）

- [ ] QMT terminal target 至少覆盖 entry_file、config_schema、import_steps、shadow_report_schema 4 类字段。
- [ ] QMT terminal target 的 import_steps 必须消费已校验 sha256 的策略包 artifact，并明确人工导入不等于运行授权。
- [ ] 文档明确 CR046 不执行 QMT terminal shadow / 模拟盘运行验证。
- [ ] submit/cancel/account query 授权状态均为 false。

## 阻塞说明

QMT terminal runtime 验证只能在后续独立 CR / runtime authorization gate 中执行。
