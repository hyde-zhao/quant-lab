---
story_id: "CR016-S03-monitoring-heartbeat-and-kill-switch"
title: "monitoring heartbeat 与 kill switch"
story_slug: "monitoring-heartbeat-and-kill-switch"
status: "verified"
priority: "P0"
wave: "CR016-W1-SIMULATION-OPS-GATES"
depends_on:
  - "CR015-S02-qmt-broker-adapter-contract"
  - "CR015-S03-oms-order-state-machine"
  - "CR016-S02-reconciliation-service-and-reports"
dependency_type:
  - upstream: "CR015-S02-qmt-broker-adapter-contract"
    type: "runtime"
  - upstream: "CR015-S03-oms-order-state-machine"
    type: "runtime"
  - upstream: "CR016-S02-reconciliation-service-and-reports"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/monitoring.py"
    - "trading/kill_switch.py"
    - "tests/test_cr016_monitoring_kill_switch.py"
  shared:
    - "trading/oms.py"
    - "trading/qmt_adapter.py"
  merge_owner: "CR016-S03-monitoring-heartbeat-and-kill-switch"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation without authorization"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#7.2"
    - "process/HLD-QMT-TRADING.md#8"
    - "process/ARCHITECTURE-DECISION.md#ADR-060"
    - "process/stories/CR016-S03-monitoring-heartbeat-and-kill-switch.md"
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
  per_run_authorization_scope: "not required for offline monitoring / kill switch contract implementation; required before any real cancel/order/account query, broker operation, simulation/live run, or incident persistence to real broker lake"
  reason: "CR015-S02/S03 与 CR016-S02 均已 CP7 PASS / verified；CP5 已 approved；当前无 trading/monitoring.py、trading/kill_switch.py、trading/oms.py 或 trading/qmt_adapter.py 文件冲突，可进入 fixture-only monitoring / kill switch contract 实现。真实撤单、真实 broker 操作和 simulation/live run 仍需后续 per-run authorization。"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR016-S03-IMPLEMENT-2026-05-28.md"
  started_at: "2026-05-28T10:40:29+08:00"
  implemented_by: "meta-dev/dev-xu the 2nd"
  agent_id: "019e6c74-54ef-7cb2-ac70-163c253c785a"
  agent_name: "dev-xu the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
validation_gate:
  cp7_result: "process/checks/CP7-CR016-S03-monitoring-heartbeat-and-kill-switch-VERIFICATION-DONE.md"
  status: "PASS"
  verified_at: "2026-05-28T11:00:54+08:00"
  verified_by: "meta-qa/qa-wei the 2nd"
  agent_id: "019e6c80-3ba9-76f3-878c-b577f342cca4"
  agent_name: "qa-wei the 2nd"
  test_result: "54 passed in 0.19s"
  security_risk_count: 0
  safety_counters_zero: true
created_at: "2026-05-28"
updated_at: "2026-05-28T11:00:54+08:00"
change_id: "CR-016"
---

# CR016-S03：monitoring heartbeat 与 kill switch

## 目标

定义 heartbeat、风险异常、对账差异和人工触发时的 kill switch 行为：停止新单、撤可撤单、冻结策略、记录 incident 和恢复条件。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-117、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §7.2、§8、§9 |
| ADR | ADR-060 |

## 开发上下文（dev_context）

**背景说明**：kill switch 是真实运行前的硬门控。CR-016 的 monitoring 先以 fixture / mock event 验证，不直接操作真实 broker。

**输入文件**：CR015-S02 adapter contract、CR015-S03 OMS state、CR016-S02 reconciliation result。

**输出文件**：`trading/monitoring.py`、`trading/kill_switch.py`、`tests/test_cr016_monitoring_kill_switch.py`；共享 `trading/oms.py`、`trading/qmt_adapter.py`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| heartbeat_check | heartbeat event、deadline | pass / fail | fail triggers incident candidate |
| kill_switch_trigger | reason、open intents、stage | freeze result、cancel plan、incident | cancel plan 不等于真实撤单 |
| recovery_gate | recon pass、manual takeover record | recoverable / blocked | 缺接管记录 blocked |

**设计约束**：CR-016 当前不执行真实撤单；撤可撤单只生成 plan，真实动作需要 per-run 授权和 stage gate。

**命名规范**：`kill_switch_reason`、`freeze_status`、`cancel_plan_status`、`manual_takeover_status`、`recovery_gate_status`。

**平台目标**：QMT ops safety service。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S02/S03 | runtime | adapter / OMS 合同可引用 | dev 等 CR015 verified | 生成 freeze / cancel plan |
| CR016-S02 | contract | recon threshold 输出可引用 | 同批可设计，开发默认串行 | 差异触发 kill switch |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S03-T1 | 创建 | `trading/monitoring.py` | 定义 heartbeat 检查和异常事件 |
| CR016-S03-T2 | 创建 | `trading/kill_switch.py` | 定义 freeze、cancel plan、incident、recovery gate |
| CR016-S03-T3 | 创建 | `tests/test_cr016_monitoring_kill_switch.py` | 覆盖 heartbeat fail、manual trigger、recon diff、recovery |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_monitoring_kill_switch.py`。

**验证方式**：fixture / mock event；不真实撤单。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：heartbeat fail 触发 freeze；recon diff 超阈值触发 manual_review；kill switch 停止新单；恢复需 recon pass + manual takeover。

## 量化验收标准（acceptance_criteria）

- [x] kill switch 行为覆盖 stop_new_orders、cancel_plan、freeze_strategy、incident、recovery_gate 5 类输出。
- [x] kill switch 触发后新单 allowed 次数为 0。
- [x] 无授权时真实撤单调用次数为 0。
- [x] incident event 不包含敏感值。

## 阻塞说明

当前为 later-gated：真实 cancel 或 live monitoring 必须后续授权；CP5 前不得实现。
