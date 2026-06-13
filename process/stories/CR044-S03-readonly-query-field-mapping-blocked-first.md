---
story_id: "CR044-S03"
title: "Readonly Query Field Mapping Blocked-First"
story_slug: "readonly-query-field-mapping-blocked-first"
status: "ready-for-verification"
priority: "P0"
wave: "W3"
implementation_allowed: true
implementation_allowed_until: "L2 blocked-first / fixture-only only; no L3+ runtime"
depends_on:
  - "CR044-S01"
  - "CR044-S02"
dependency_contracts:
  - upstream_story: "CR044-S01"
    type: "contract"
    required_for: "security and redaction policy"
  - upstream_story: "CR044-S02"
    type: "contract"
    required_for: "admission gate and capability state"
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-readonly"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "external-interface"
    - "data-model"
    - "security"
    - "permission"
  rationale: "cash/position/order/fill 字段映射属于外部 broker 只读接口，必须 blocked-first 并完整设计 UNKNOWN 字段处理。"
  waiver_reason: ""
  revisit_condition: "用户逐 run 授权 L4 readonly query 后，新增 runtime probe 设计，不复用 L2 fixture 作为真实证据。"
  evidence_path: "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first.md"
    - "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md"
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
    - "CR044-S01 design evidence"
    - "CR044-S02 design evidence"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md"
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

# CR044-S03 Readonly Query Field Mapping Blocked-First

## 目标

设计 cash、position、order、fill 只读查询字段映射的 blocked-first 合同：L2 只允许静态候选字段和合成 fixture，不允许真实账户查询。

## 开发上下文（dev_context）

- 输入文件：S01/S02 设计证据、CR043 interface mapping 摘要、`engine/broker_adapter.py`、CR042 合同测试。
- 输出文件：`process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md`。
- 接口约定：字段映射必须区分 `candidate_mapping`、`unknown_broker_field`、`blocked_no_authorization`、`redacted_sensitive_field`。
- 设计约束：不能执行 account/cash/position/order/fill query；不能保存真实 broker payload；不能把静态候选字段当作已验证字段。
- 平台目标：fixture-only；后续测试只构造合成 payload。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S03-T1 | 设计 | `CR044-S03-...-LLD.md` | 定义 cash/position/order/fill candidate field mapping 和 UNKNOWN 状态。 |
| CR044-S03-T2 | 设计 | `CR044-S03-...-LLD.md` | 定义 readonly blocked result 和 redaction 规则。 |
| CR044-S03-T3 | 设计 | `CR044-S03-...-LLD.md` | 定义 L4 逐 run 授权后如何新增只读探针，而非在本 Story 执行。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR044-S01 | contract | 需要 redaction policy | CP5 approved + S01 confirmed | 敏感字段和证据输出边界。 |
| CR044-S02 | contract | 需要 admission gate state | CP5 approved + S02 confirmed | 查询必须先过 gate。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | 后续 CR044 guard tests；CR042 adapter contract regression |
| 关键验证场景 | L4 未授权时 cash/position/order/fill query blocked；candidate mapping 不提升为真实验证；敏感字段 redacted。 |
| 禁止验证方式 | 不查询真实资金、持仓、委托、成交、账户状态。 |
| CP7 关注点 | UNKNOWN 字段有状态，不吞掉；operation_counts 对 readonly runtime 始终为 0。 |

## 量化验收标准（acceptance_criteria）

- [ ] 字段映射至少覆盖 cash、available_cash、position quantity/sellable_qty/average_cost、order status、fill quantity/price/time 的候选类别。
- [ ] 每个候选字段必须标注来源为 static candidate / fixture / unknown，不得标注 real-verified。
- [ ] L4 未授权时 readonly query 必须 blocked，真实 query operation count 为 0。
- [ ] 敏感账户字段和 broker order ref 字段必须 redacted 或 blocked，不保存原始值。
- [ ] S03 不修改 CR042 测试文件；新增测试只能在后续 CP5/CP6 后写 CR044 scoped 测试。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

真实只读字段验证被 L4 未授权阻塞；这不阻塞 L2 field mapping 设计。
