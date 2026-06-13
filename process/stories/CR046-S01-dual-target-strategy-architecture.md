---
story_id: "CR046-S01-dual-target-strategy-architecture"
title: "双目标策略交付架构与 FEAT-09 边界"
story_slug: "dual-target-strategy-architecture"
status: "ready-for-verification"
priority: "P0"
wave: "CR046-W1-ARCHITECTURE-CONTRACT"
depends_on: []
dependency_type: []
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
feature_design_refs:
  - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  - "docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "architecture"
    - "cross-feature"
    - "security-boundary"
  rationale: "FEAT-09 是 CR046 的新共享 Feature，承接 QMT terminal 与 MiniQMT runner 双目标合同，需 full-lld 冻结边界。"
  waiver_reason: ""
  revisit_condition: "若后续降级为 QMT-only 或放弃 MiniQMT，需重开 CR / CP3。"
  evidence_path: "process/stories/CR046-S01-dual-target-strategy-architecture-LLD.md"
file_ownership:
  primary:
    - "docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md"
  shared:
    - "docs/design/FEATURE-DESIGN-MATRIX.md"
    - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  merge_owner: "CR046-S01-dual-target-strategy-architecture"
  forbidden:
    - "strategy implementation"
    - "QMT / MiniQMT runtime call"
    - "submit/cancel"
    - "credential read"
lld_gate:
  required_inputs:
    - "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
    - "docs/design/ARCHITECTURE-DECISION-CR046.md"
    - "docs/design/FEATURE-DESIGN-MATRIX.md"
    - "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR046-S01-dual-target-strategy-architecture-LLD.md"
  status: "confirmed"
implementation_gate:
  evidence_required: true
  evidence_path: ""
  evidence_type: "implementation-md"
  implementation_objects: ["docs-handoff", "contract-schema"]
  test_plan_refs:
    - "docs/features/qmt-miniqmt-dual-target-framework/TEST-PLAN.md"
  local_validation_results: []
  status: "not-started"
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

# CR046-S01：双目标策略交付架构与 FEAT-09 边界

## 目标

冻结 FEAT-09 的模块边界、StrategyCoreContract、target adapter 调用方向和 no-real-operation 约束，作为后续 CR046 Story 的共享设计输入。

## 开发上下文（dev_context）

**输入文件**：`docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md`、`docs/design/ARCHITECTURE-DECISION-CR046.md`、`docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md`。

**输出文件**：`docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md`。

**设计约束**：本 Story 只设计框架，不交付具体策略、不运行 QMT、不连接 MiniQMT、不读取凭据、不 submit/cancel。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| 无 | N/A | CP3 approved | CP5 批量确认后才可实现 | 架构合同为本批次起点 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 当前 Story |
| shared | `docs/design/FEATURE-DESIGN-MATRIX.md`、FEAT-09 设计文件 | 仅 CP4/CP5 维护 |
| forbidden | 代码实现、QMT/MiniQMT 调用、凭据、submit/cancel | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR046-S01-T1 | 设计 | `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` | 定义 FEAT-09 架构图和对象边界 |
| CR046-S01-T2 | 设计 | 同上 | 定义 StrategyCoreContract |
| CR046-S01-T3 | 设计 | 同上 | 定义 target adapter 调用方向 |
| CR046-S01-T4 | 校验 | 同上 | 写入不授权项和后续 CR gate |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | full-lld |
| 设计依据 | HLD-CR046、ADR-CR046、FEAT-09 DESIGN |
| 文件影响 | 新增 `docs/qmt/CR046-DUAL-TARGET-STRATEGY-FRAMEWORK.md` |
| 接口 / 数据 / 权限变化 | 只定义合同，不新增 runtime 权限 |
| 异常、失败与回退 | 若需要真实运行，回退到 runtime_authorization gate |
| 测试入口 | FEAT-09 TEST-PLAN |
| 风险与重访条件 | MiniQMT 路线放弃或 QMT-only 时重访 |

## 量化验收标准（acceptance_criteria）

- [ ] StrategyCoreContract 至少覆盖 input、target_portfolio、order_intent、risk_assumption、evidence_required 5 类字段。
- [ ] target adapter 边界覆盖 QMT terminal 与 MiniQMT runner 2 个目标。
- [ ] 不授权项数量 >= 10，且包含 submit/cancel、credential_read、MiniQMT connection。

## 阻塞说明

CP5 全量设计证据确认前不得实现。真实运行、连接和交易操作均保持 blocked。
