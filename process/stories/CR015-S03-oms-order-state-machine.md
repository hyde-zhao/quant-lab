---
story_id: "CR015-S03-oms-order-state-machine"
title: "OMS order intent 与订单状态机"
story_slug: "oms-order-state-machine"
status: "verified"
priority: "P0"
wave: "CR015-W2-OMS-RISK-LAKE"
depends_on:
  - "CR015-S02-qmt-broker-adapter-contract"
  - "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
dependency_type:
  - upstream: "CR015-S02-qmt-broker-adapter-contract"
    type: "contract"
  - upstream: "CR017-S01-adjustment-policy-requirements-and-adr-refresh"
    type: "contract"
cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/oms.py"
    - "tests/test_cr015_oms_state_machine.py"
  shared:
    - "trading/qmt_adapter.py"
  merge_owner: "CR015-S03-oms-order-state-machine"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.3"
    - "process/ARCHITECTURE-DECISION.md#ADR-057"
    - "process/stories/CR015-S03-oms-order-state-machine.md"
  status: "approved"
  cp5_batch: "CR015-QMT-FOUNDATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  reason: "CR015-S02 已 CP7 PASS / verified；CR017-S01 已 verified；CP5 已 approved；当前无 dev_running 文件冲突，可进入 OMS 状态机离线实现。"
created_at: "2026-05-28"
updated_at: "2026-05-28T08:25:16+08:00"
coding_gate:
  cp6_status: "PASS"
  cp6_result: "process/checks/CP6-CR015-S03-oms-order-state-machine-CODING-DONE.md"
  implementation_handoff: "process/handoffs/META-DEV-CR015-S03-IMPLEMENT-2026-05-28.md"
  implemented_by: "meta-dev/dev-shi"
  implemented_at: "2026-05-28T08:15:23+08:00"
  agent_id: "019e6be9-9023-7d52-b1f2-9f93acea500a"
  agent_name: "dev-shi"
verification_gate:
  cp7_status: "PASS"
  cp7_result: "process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md"
  verification_handoff: "process/handoffs/META-QA-CR015-S03-CP7-VERIFY-2026-05-28.md"
  verified_by: "meta-qa/qa-lv"
  verified_at: "2026-05-28T08:22:15+08:00"
  agent_id: "019e6bf4-7b26-7801-9b7b-4343b653315a"
  agent_name: "qa-lv"
change_id: "CR-015"
---

# CR015-S03：OMS order intent 与订单状态机

## 目标

实现目标组合到 order intent 的核心状态合同，并覆盖 accepted、partially_filled、filled、cancel_pending、canceled、rejected、failed、unknown、timeout、manual_review、frozen 等状态。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-10 |
| 需求 | REQ-106、REQ-107、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.1、§7.3 |
| ADR | ADR-057 |

## 开发上下文（dev_context）

**背景说明**：OMS 负责意图幂等、状态迁移、manual_review 和冻结状态。unknown / timeout 不得静默成功，撤单失败不得无限自动重试。

**输入文件**：CR015-S02 adapter event 合同、CR017-S01 policy 合同、HLD-QMT-TRADING §7.3。

**输出文件**：`trading/oms.py`、`tests/test_cr015_oms_state_machine.py`；共享 `trading/qmt_adapter.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| create_order_intent | target portfolio、signal_date、target_trade_date、policy metadata | intent、idempotency_key | 缺 research/execution policy blocked |
| apply_broker_event | current state、broker event | next state、transition event | illegal transition fail |
| freeze_orders | trigger reason | frozen state、incident ref | 不直接发真实撤单 |

**设计约束**：状态机只处理本地状态和 mock event；真实 broker reconciliation 由 CR016/CR015-S05 消费，不在本 Story 真实写入。

**命名规范**：`order_intent_id`、`idempotency_key`、`state`、`event_time`、`manual_review_required`、`retry_count`。

**平台目标**：本地 OMS core contract。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S02 | contract | adapter events 可引用 | 状态机消费 adapter mock event | 不直接 broker |
| CR017-S01 | contract | policy enum 可引用 | intent 必填 raw execution policy | 价格边界前置 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR015-S03-T1 | 创建 | `trading/oms.py` | 定义 order intent schema 和状态机 |
| CR015-S03-T2 | 创建 | `tests/test_cr015_oms_state_machine.py` | 覆盖合法迁移、illegal transition、unknown / timeout |
| CR015-S03-T3 | 修改 | `trading/qmt_adapter.py` | 按 LLD 对齐 broker event 枚举 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr015_oms_state_machine.py`。

**验证方式**：状态机 fixture；不真实交易。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：缺 policy blocked；partial fill 合法；timeout -> manual_review；unknown 不终态成功；kill switch -> frozen。

## 量化验收标准（acceptance_criteria）

- [x] HLD §7.3 中的状态和事件覆盖率为 100%。
- [x] unknown / timeout 被标记成功的次数为 0。
- [x] order intent 100% 包含 `research_adjustment_policy` 和 `execution_price_policy=raw`。
- [x] 默认验证 real_order_call、real_cancel_call、account_write_call、credential_read 均为 0。

## 阻塞说明

CP5 前不得实现；真实 broker event 映射需后续受控验证。
