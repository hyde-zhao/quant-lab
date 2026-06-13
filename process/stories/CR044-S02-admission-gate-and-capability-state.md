---
story_id: "CR044-S02"
title: "Admission Gate and Capability State"
story_slug: "admission-gate-and-capability-state"
status: "ready-for-verification"
priority: "P0"
wave: "W2"
implementation_allowed: true
implementation_allowed_until: "L2 blocked-first / fixture-only only; no L3+ runtime"
depends_on:
  - "CR044-S01"
dependency_contracts:
  - upstream_story: "CR044-S01"
    type: "contract"
    required_for: "authorization layers, sensitive field policy, not-authorized actions"
feature_design_refs:
  - "docs/design/FEATURE-DESIGN-MATRIX-CR044.md#feat-cr044-gate"
lld_policy:
  required_level: "full-lld"
  trigger_reasons:
    - "cross-module-contract"
    - "data-model"
    - "rollback"
    - "shared-story-boundary"
  rationale: "admission gate 和 capability state 决定所有 Goldminer blocked-first 行为，必须完整设计。"
  waiver_reason: ""
  revisit_condition: "若任何产物需要把 simulation_ready/live_ready 置 true，回退 CP3 或发起新 CR。"
  evidence_path: "process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md"
file_ownership:
  primary:
    - "process/stories/CR044-S02-admission-gate-and-capability-state.md"
    - "process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md"
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
    - "engine/broker_adapter.py"
    - "tests/test_cr042_broker_adapter_contract.py"
  design_evidence_type: "full-lld"
  design_evidence_path: "process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md"
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

# CR044-S02 Admission Gate and Capability State

## 目标

设计 blocked-first Goldminer admission gate 和 capability state，使 `GoldminerStubBrokerAdapter` 在未授权状态下继续返回 blocked，并保持 `simulation_ready=false`、`live_ready=false`、`not_authorization=true`。

## 开发上下文（dev_context）

- 输入文件：S01 设计证据、`engine/broker_adapter.py`、`tests/test_cr042_broker_adapter_contract.py`、CP3 checkpoint。
- 输出文件：`process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md`；后续 CP5 通过后才允许修改 `engine/broker_adapter.py` 和新增 CR044 guard tests。
- 接口约定：定义 capability states：`sdk_static_candidate`、`offline_design_ready`、`credential_required`、`readonly_authorized_for_run`、`submit_cancel_authorized_for_run`、`blocked_no_authorization`；任何状态默认不提升为 simulation/live ready。
- 设计约束：当前唯一 Goldminer 运行态对象仍是 `GoldminerStubBrokerAdapter`；L2 禁止真实 SDK import/call。
- 平台目标：Python 3.11 fixture-only；不新增真实 broker 依赖。
- AI 可执行任务清单：

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR044-S02-T1 | 设计 | `CR044-S02-...-LLD.md` | 定义 admission gate 输入、输出、blocked reason 和 capability state。 |
| CR044-S02-T2 | 设计 | `CR044-S02-...-LLD.md` | 映射现有 `BrokerAdapterCapability` / `BrokerAdapterResult` 字段，保持 simulation/live false。 |
| CR044-S02-T3 | 设计 | `CR044-S02-...-LLD.md` | 定义后续 fixture 测试和静态 import 禁止规则。 |

## 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR044-S01 | contract | 可基于 S01 设计证据起草 | CP5 approved + S01 contract confirmed | S01 提供授权和敏感字段合同。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | static-only + fixture-only |
| 验证入口 | 后续 CR044 guard tests + CR042 regression tests |
| 关键验证场景 | default denied；missing authorization denied；kill switch absent denied；capability keeps `real_broker_enabled=false`、`simulation_ready=false`、`live_ready=false`。 |
| 禁止验证方式 | 不导入 `gm` / `gmtrade`，不连接、不登录、不查询、不下单。 |
| CP7 关注点 | forbidden operation counters 全 0；`BrokerAdapterResult.to_dict()` 不泄漏敏感字段。 |

## 量化验收标准（acceptance_criteria）

- [ ] capability state 至少覆盖 6 个状态，并明确哪些状态仅为静态/离线设计状态。
- [ ] 未授权时所有 Goldminer query/submit/cancel 路径结果为 blocked 或抛出受控 validation error，不执行 runtime。
- [ ] `simulation_ready` 和 `live_ready` 在 L2 设计及后续 fixture 中均为 false。
- [ ] forbidden import/call 列表包含 `gm`、`gmtrade`、login、connect、query_account、submit_order、cancel_order 等高风险项。
- [ ] `engine/broker_adapter.py` 为 shared 文件，merge_owner 为 CR044-S02；CP5 前不得修改。
- [ ] `implementation_allowed=false until CP5 approved` 保持成立。

## 阻塞说明

无 L2 设计阻塞；真实 runtime 因 L3+ 未授权保持 blocked。
