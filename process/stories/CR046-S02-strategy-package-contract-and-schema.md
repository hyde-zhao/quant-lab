---
story_id: "CR046-S02-strategy-package-contract-and-schema"
title: "策略包合同、目录结构与 schema"
story_slug: "strategy-package-contract-and-schema"
status: "ready-for-verification"
priority: "P0"
wave: "CR046-W1-ARCHITECTURE-CONTRACT"
depends_on:
  - "CR046-S01-dual-target-strategy-architecture"
dependency_type:
  - "contract"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  - "docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons: ["schema", "contract", "validation"]
  rationale: "策略包 manifest、目录和 schema 是 CR047 具体策略交付的合同前置。"
  waiver_reason: ""
  revisit_condition: "策略包 layout_version 或 target 列表变化时。"
  evidence_path: "process/stories/CR046-S02-strategy-package-contract-and-schema-LLD.md"
file_ownership:
  primary:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
  shared:
    - "docs/qmt/CR046-VERIFICATION-FRAMEWORK.md"
  merge_owner: "CR046-S02-strategy-package-contract-and-schema"
  forbidden:
    - "concrete strategy code"
    - "runtime secrets"
lld_gate:
  required_inputs:
    - "CR046-S01-dual-target-strategy-architecture"
    - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR046-S02-strategy-package-contract-and-schema-LLD.md"
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

# CR046-S02：策略包合同、目录结构与 schema

## 目标

定义 CR046 策略包的目录、manifest、schema 版本、target 列表、docs bundle 和 validation suite，使后续 CR047 能按统一合同交付首个策略。

## 开发上下文（dev_context）

**输入文件**：CR046-S01、FEAT-09 DESIGN / TEST-PLAN。

**输出文件**：`docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md`、`docs/qmt/CR046-VERIFICATION-FRAMEWORK.md`。

**设计约束**：只定义合同，不产生可交易策略包，不包含真实账号或凭据。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR046-S01 | contract | S01 LLD 或合同草案可读 | S01 合同冻结 | 依赖 StrategyCoreContract |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR046-S02-T1 | 设计 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 定义 `strategy_core/`、`targets/`、`validation/`、`docs/`、`manifest.yaml` |
| CR046-S02-T2 | 设计 | 同上 | 定义 manifest 字段和 layout_version |
| CR046-S02-T3 | 设计 | `docs/qmt/CR046-VERIFICATION-FRAMEWORK.md` | 定义 schema validation 输入输出 |
| CR046-S02-T4 | 校验 | 同上 | 定义缺字段 fail-closed 行为 |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 文件影响 | 新增 / 修改 CR046 策略框架和验证框架文档 |
| 接口 / 数据 / 权限变化 | 新增 StrategyPackageContract schema；无 runtime 权限 |
| 测试入口 | schema fixture / docs review |

## 量化验收标准（acceptance_criteria）

- [ ] 策略包目录至少包含 6 个顶层对象：`strategy_core`、`targets/qmt_terminal`、`targets/miniqmt_runner`、`validation`、`docs`、`manifest.yaml`。
- [ ] manifest 至少覆盖 package_id、layout_version、targets、validation_suite、authorization_boundary 5 类字段。
- [ ] 策略包 artifact 合同至少覆盖 zip 文件名、sha256 校验、manifest 入口、人工/受控 transfer_channel、QMT terminal manual_import_steps 5 类字段。
- [ ] 缺必填字段时行为为 blocked。

## 阻塞说明

具体策略文件、真实交易配置和运行结果不属于本 Story。
