---
story_id: "CR016-S01-simulation-account-order-enable-gate"
title: "simulation 阶段 order enable gate"
story_slug: "simulation-account-order-enable-gate"
status: "verified"
priority: "P0"
wave: "CR016-W1-SIMULATION-OPS-GATES"
depends_on:
  - "CR015-S07-docs-and-foundation-runbook-boundary"
  - "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
dependency_type:
  - upstream: "CR015-S07-docs-and-foundation-runbook-boundary"
    type: "runtime"
  - upstream: "CR017-S06-research-qmt-consumer-docs-and-migration-guide"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/stage_gate.py"
    - "tests/test_cr016_simulation_order_enable_gate.py"
  shared:
    - "trading/qmt_adapter.py"
    - "docs/QMT-TRADING-RUNBOOK.md"
  merge_owner: "CR016-S01-simulation-account-order-enable-gate"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker order or cancel call without per-run authorization"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.2"
    - "process/ARCHITECTURE-DECISION.md#ADR-059"
    - "process/ARCHITECTURE-DECISION.md#ADR-060"
    - "process/stories/CR016-S01-simulation-account-order-enable-gate.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  requires_cr015_verified: true
  requires_per_run_authorization: true
  per_run_authorization_scope: "not required for offline gate implementation; required before any real simulation run, QMT call, order/cancel/account operation, broker lake write, or publish"
  reason: "CR015 foundation S01..S07 与 CR017-S06 均已 CP7 PASS / verified；CP5 已 approved；当前无 trading/stage_gate.py、trading/qmt_adapter.py 或 docs/QMT-TRADING-RUNBOOK.md 文件冲突，可进入 stage gate 离线实现。任何 simulation run 或真实 QMT 操作仍需后续 per-run authorization。"
created_at: "2026-05-28"
updated_at: "2026-05-28T10:14:24+08:00"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR016-S01-IMPLEMENT-2026-05-28.md"
  implementation_started_at: "2026-05-28T09:56:41+08:00"
  implementation_completed_at: "2026-05-28T10:03:34+08:00"
  cp6: "process/checks/CP6-CR016-S01-simulation-account-order-enable-gate-CODING-DONE.md"
  test_result: "24 passed in 0.07s"
  implemented_by: "meta-dev/dev-zhang the 2nd"
  agent_id: "019e6c4c-4259-7841-8741-9cc533d26950"
  agent_name: "dev-zhang the 2nd"
validation_gate:
  cp7_result: "process/checks/CP7-CR016-S01-simulation-account-order-enable-gate-VERIFICATION-DONE.md"
  verified_at: "2026-05-28T10:14:24+08:00"
  verified_by: "meta-qa/qa-jin the 2nd"
  agent_id: "019e6c57-6aac-7762-98e4-c5cc22d583e2"
  agent_name: "qa-jin the 2nd"
  test_result: "24 passed in 0.07s"
change_id: "CR-016"
---

# CR016-S01：simulation 阶段 order enable gate

## 目标

定义从 shadow 进入 QMT simulation 的 stage gate、order enable 条件、授权字段、blocked reason 和 safety counters。当前 Story 只做设计与后续 LLD 输入，不授权真实运行。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-112、REQ-113、REQ-114、REQ-115、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.2、§7.4 |
| ADR | ADR-059、ADR-060 |

## 开发上下文（dev_context）

**背景说明**：CR-016 依赖 CR-015 foundation verified。没有 runbook、CR015 mock evidence、授权摘要、对账规则或 CR017 口径声明时，simulation gate 必须 blocked。

**输入文件**：CR015-S07 runbook boundary、CR017-S06 consumer boundary、HLD-QMT-TRADING。

**输出文件**：`trading/stage_gate.py`、`tests/test_cr016_simulation_order_enable_gate.py`；共享 `trading/qmt_adapter.py`、`docs/QMT-TRADING-RUNBOOK.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| evaluate_stage_gate | current_stage、target_stage、evidence refs、authorization summary | gate_status、missing_fields、blocked_reason | 跳阶段 blocked |
| simulation_order_enable | stage gate result、adapter mode | enable / blocked | 无完整授权时真实调用为 0 |
| authorization summary check | mode、strategy、date、capital limit、scope、approver、rollback | pass / missing_fields | 只记录脱敏摘要 |

**设计约束**：不读取凭据；不执行真实发单、撤单或账户写操作；simulation 也必须先通过 gate。

**命名规范**：`stage=shadow|simulation|live_readonly|small_live|scale_up`、`gate_status=pass|blocked|manual_review`。

**平台目标**：QMT activation stage gate。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S07 | runtime | foundation runbook 与 mock evidence 可引用 | dev 必须等待 CR015 verified | foundation 前置 |
| CR017-S06 | contract | 复权消费边界可引用 | scale_up 前需 CR017 verified | 技术 simulation 与生产声明分离 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S01-T1 | 创建 | `trading/stage_gate.py` | 定义 stage gate 状态、授权摘要检查和 order enable gate |
| CR016-S01-T2 | 创建 | `tests/test_cr016_simulation_order_enable_gate.py` | 覆盖跳阶段、缺 runbook、缺授权、CR015 未 verified |
| CR016-S01-T3 | 修改 | `docs/QMT-TRADING-RUNBOOK.md` | 按 LLD 写 simulation 准入清单 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_simulation_order_enable_gate.py`。

**验证方式**：stage gate fixture；不触达真实 broker。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：shadow -> simulation 合法；跳到 live blocked；缺 runbook blocked；缺授权 blocked；真实调用计数为 0。

## 量化验收标准（acceptance_criteria）

- [ ] 5 个 stage 顺序全部可枚举，跳阶段请求 blocked 覆盖率 100%。
- [ ] 缺 CR015 verified、runbook、授权或对账规则时 gate_status=blocked。
- [ ] 无完整授权时 real_order_call、real_cancel_call、account_write_call 均为 0。
- [ ] CR017 未 verified 时 scale_up allowed 次数为 0。

## 阻塞说明

当前为 later-gated：CR015 foundation 未 verified、CR017 未 verified、CP5 未 approved 且无 per-run 授权前，不得实现真实 order enable。
