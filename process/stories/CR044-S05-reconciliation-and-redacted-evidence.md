---
story_id: "CR044-S05"
title: "Reconciliation and Redacted Evidence"
story_slug: "reconciliation-and-redacted-evidence"
status: "ready-for-verification"
priority: "P0"
wave: "W4"
implementation_allowed: true
implementation_allowed_until: "L2 blocked-first / fixture-only only; no L3+ runtime"
depends_on:
  - "CR044-S03"
  - "CR044-S04"
dependency_contracts:
  - upstream_story: "CR044-S03"
    type: "contract"
    required_for: "readonly field mapping and redaction"
  - upstream_story: "CR044-S04"
    type: "contract"
    required_for: "submit/cancel and kill switch blocked semantics"
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-recon"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "data-model"
    - "external-interface"
    - "security"
    - "audit"
    - "rollback"
  rationale: "对账证据和 redaction 直接影响 CP7/CP8 风险结论，且必须禁止自动补单/撤单。"
  waiver_reason: ""
  revisit_condition: "若需要保存真实 broker payload 或使用真实成交作为 fixture，必须回退安全决策。"
  evidence_path: "process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR044-S05-reconciliation-and-redacted-evidence.md"
    - "process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md"
  shared:
    - "engine/broker_adapter.py"
    - "tests/test_cr044_goldminer_admission_guard.py"
  merge_owner: "CR044-S02"
  forbidden:
    - ".env"
    - ".env.*"
    - "tests/test_cr042_broker_adapter_contract.py"
lld_gate:
  required_inputs:
    - "CR044-S03 design evidence"
    - "CR044-S04 design evidence"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md"
  status: "ready-for-review"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR044-S05 Reconciliation and Redacted Evidence

## 目标

设计 L2 离线对账合同和 redacted evidence 结构，使 CR044 能证明 blocked-first 行为、字段 UNKNOWN 状态、差异分类和 no-real-operation 结果，而不保存真实 broker payload。

## 开发上下文（dev_context）

- 输入文件：S03/S04 设计证据、CR041 paper ledger 经验、CR042 adapter result 合同、CP3 handoff 风险表。
- 输出文件：`process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md`。
- 接口约定：定义 reconciliation status：`matched_fixture`、`blocked_no_authorization`、`unknown_broker_field`、`mismatch_requires_manual_review`。
- 设计约束：不得拉取真实成交；不得用真实 broker payload 作为长期 fixture；对账失败不得自动补单或撤单。
- 平台目标：fixture-only；证据路径只保存 redacted structure。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S05-T1 | 设计 | `CR044-S05-...-LLD.md` | 定义 offline reconciliation schema 和 redacted evidence shape。 |
| CR044-S05-T2 | 设计 | `CR044-S05-...-LLD.md` | 定义 discrepancy taxonomy 和人工审查路由。 |
| CR044-S05-T3 | 设计 | `CR044-S05-...-LLD.md` | 定义禁止自动补单/撤单和 artifact scan 要求。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR044-S03 | contract | 需要 readonly mapping | CP5 approved + S03 confirmed | cash/position/order/fill 结构来源。 |
| CR044-S04 | contract | 需要 submit/cancel blocked semantics | CP5 approved + S04 confirmed | 对账差异不得触发未授权动作。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | 后续 CR044 guard tests、artifact scan、CR042 regression |
| 关键验证场景 | fixture matched；blocked_no_authorization；unknown_broker_field；mismatch_requires_manual_review；redacted evidence no sensitive value。 |
| 禁止验证方式 | 不查询真实成交、不拉取 broker payload、不 provider_fetch、不 lake_write、不 catalog_publish。 |
| CP7 关注点 | 证据可审计但不含真实账号、真实订单号、真实成交号、session/cookie/token。 |

## 量化验收标准（acceptance_criteria）

- [ ] reconciliation status 至少覆盖 4 类：matched_fixture、blocked_no_authorization、unknown_broker_field、mismatch_requires_manual_review。
- [ ] redacted evidence 至少包含 schema_version、source、status、blocked_reasons、operation_counts、redaction_summary。
- [ ] 真实 broker payload 不得作为 fixture 保存；只允许合成 fixture 或脱敏结构。
- [ ] 差异处理只能路由人工审查，不自动补单、不自动撤单。
- [ ] provider_fetch、lake_write、catalog_publish operation count 必须保持 0。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

真实 broker reconciliation 被 L4/L5 未授权阻塞；L2 只做离线合同。
