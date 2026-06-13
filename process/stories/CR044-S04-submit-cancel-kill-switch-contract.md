---
story_id: "CR044-S04"
title: "Submit Cancel Kill Switch Contract"
story_slug: "submit-cancel-kill-switch-contract"
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
    required_for: "runtime authorization and sensitive action list"
  - upstream_story: "CR044-S02"
    type: "contract"
    required_for: "admission gate and capability state"
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-kill"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "security"
    - "external-interface"
    - "rollback"
    - "runtime_authorization"
  rationale: "submit/cancel 与 kill switch 涉及真实交易副作用和回退边界，必须完整 LLD。"
  waiver_reason: ""
  revisit_condition: "任何真实 submit/cancel 诉求必须先获得 L5 单次授权和订单白名单。"
  evidence_path: "process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR044-S04-submit-cancel-kill-switch-contract.md"
    - "process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md"
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
  design_evidence_path: "process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md"
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

# CR044-S04 Submit Cancel Kill Switch Contract

## 目标

设计 submit/cancel 在 CR044 中的双层 kill switch、动作白名单、operation counter 和 blocked-first 合同，确保 L2 不可能产生真实订单副作用。

## 开发上下文（dev_context）

- 输入文件：S01/S02 设计证据、`engine/broker_adapter.py`、CR042 合同测试、CP3 DQ-04/05。
- 输出文件：`process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md`。
- 接口约定：定义 global hard switch、per-run switch、operation-level whitelist、submit/cancel blocked reasons、max_real_operation_counts。
- 设计约束：L2 不能 submit/cancel；不能写 `simulation_ready=true`；不能新增 retry 真实操作。
- 平台目标：fixture-only；后续只验证 blocked result 和 operation_counts。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S04-T1 | 设计 | `CR044-S04-...-LLD.md` | 定义 global/per-run/operation-level kill switch 合同。 |
| CR044-S04-T2 | 设计 | `CR044-S04-...-LLD.md` | 定义 submit/cancel whitelist 和 blocked result shape。 |
| CR044-S04-T3 | 设计 | `CR044-S04-...-LLD.md` | 定义 L5 授权前后禁止自动重试、补单、撤单的边界。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR044-S01 | contract | 需要 runtime authorization list | CP5 approved + S01 confirmed | 确定 submit/cancel 未授权。 |
| CR044-S02 | contract | 需要 gate state | CP5 approved + S02 confirmed | 所有动作先经过 admission gate。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | 后续 CR044 guard tests；CR042 adapter contract regression |
| 关键验证场景 | default hard-off；missing per-run switch；action not whitelisted；operation count nonzero；all return blocked。 |
| 禁止验证方式 | 不提交订单、不撤单、不启动仿真、不连接 broker。 |
| CP7 关注点 | no retry；no automatic cancel after mismatch；真实 submit/cancel counters 为 0。 |

## 量化验收标准（acceptance_criteria）

- [ ] kill switch 至少包含 global hard switch、per-run switch、operation-level whitelist 三层。
- [ ] 缺失、过期、动作不匹配或 disabled 状态都必须 blocked。
- [ ] L5 未授权时 submit/cancel operation count 必须为 0。
- [ ] 对账失败不得自动补单；撤单必须由 L5 run manifest 明确授权，否则 blocked。
- [ ] 后续任何测试只能使用 fixture order intent，不得产生真实 broker order ref。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

真实 submit/cancel 被 L5 未授权阻塞；本 Story 只规划合同和 fixture-only 验证。
