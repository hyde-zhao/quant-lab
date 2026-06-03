---
story_id: "CR016-S04-simulation-live-runbook-and-approval-gates"
title: "simulation / live runbook 与审批门"
story_slug: "simulation-live-runbook-and-approval-gates"
status: "verified"
priority: "P0"
wave: "CR016-W1-SIMULATION-OPS-GATES"
depends_on:
  - "CR016-S01-simulation-account-order-enable-gate"
  - "CR016-S02-reconciliation-service-and-reports"
  - "CR016-S03-monitoring-heartbeat-and-kill-switch"
dependency_type:
  - upstream: "CR016-S01-simulation-account-order-enable-gate"
    type: "contract"
  - upstream: "CR016-S02-reconciliation-service-and-reports"
    type: "contract"
  - upstream: "CR016-S03-monitoring-heartbeat-and-kill-switch"
    type: "contract"
cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
    - "tests/test_cr016_runbook_approval_gates.py"
  shared:
    - "docs/QMT-TRADING-RUNBOOK.md"
    - "README.md"
    - "docs/USER-MANUAL.md"
  merge_owner: "CR016-S04-simulation-live-runbook-and-approval-gates"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - "credential files or secret values"
    - "real broker operation"
lld_gate:
  required_inputs:
    - "process/HLD-QMT-TRADING.md#11"
    - "process/ARCHITECTURE-DECISION.md#ADR-059"
    - "process/ARCHITECTURE-DECISION.md#ADR-060"
    - "process/stories/CR016-S04-simulation-live-runbook-and-approval-gates.md"
  status: "approved"
  cp5_batch: "CR016-QMT-ACTIVATION-BATCH-A"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  requires_cr015_verified: true
  reason: "CR016-S01/S02/S03 均已 CP7 PASS / verified；CP5 已 approved；当前无 docs/QMT-SIMULATION-LIVE-RUNBOOK.md、tests/test_cr016_runbook_approval_gates.py、docs/QMT-TRADING-RUNBOOK.md、README.md 或 docs/USER-MANUAL.md 文件冲突，可进入文档 contract / 静态测试实现。runbook 完成不授权 simulation/live/small_live/scale_up 或任何真实 broker 操作。"
development_gate:
  implementation_handoff: "process/handoffs/META-DEV-CR016-S04-IMPLEMENT-2026-05-28.md"
  started_at: "2026-05-28T11:03:33+08:00"
  implemented_by: "meta-dev/dev-qin the 2nd"
  agent_id: "019e6c89-715f-7472-8b69-e20d1e9e4aa0"
  agent_name: "dev-qin the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
validation_gate:
  cp7: "process/checks/CP7-CR016-S04-simulation-live-runbook-and-approval-gates-VERIFICATION-DONE.md"
  status: "PASS"
  verified_at: "2026-05-28T11:43:56+08:00"
  verified_by: "meta-qa/qa-shi the 2nd"
  agent_id: "019e6c95-337c-7851-8f1f-0c558da719b4"
  agent_name: "qa-shi the 2nd"
  dispatch: "multi_agent_v1.spawn_agent"
  completed_at: "2026-05-28T11:18:54+08:00"
  close_attempt: "close_agent target not found at 2026-05-28T11:43:56+08:00; no closed_at fabricated."
  test_result: "41 passed in 0.19s"
  safety_counters_zero: true
created_at: "2026-05-28"
updated_at: "2026-05-28T11:43:56+08:00"
change_id: "CR-016"
---

# CR016-S04：simulation / live runbook 与审批门

## 目标

建立 simulation、live_readonly、small_live 的 runbook 与审批门，覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复和回滚。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-11 |
| 需求 | REQ-112、REQ-113、REQ-114、REQ-117、REQ-121 |
| HLD | `process/HLD-QMT-TRADING.md` §11 |
| ADR | ADR-059、ADR-060、ADR-061 |

## 开发上下文（dev_context）

**背景说明**：runbook 是 simulation 前硬门槛。该 Story 不授权真实运行，只定义后续用户审批和 incident playbook 所需文档与检查入口。

**输入文件**：CR016-S01/S02/S03、CR015-S07。

**输出文件**：`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`tests/test_cr016_runbook_approval_gates.py`；共享 `docs/QMT-TRADING-RUNBOOK.md`、`README.md`、`docs/USER-MANUAL.md`。

**接口约定**：

| 接口 | 输入 | 输出 | 错误 / 限制 |
|---|---|---|---|
| runbook readiness checker | runbook sections、stage | pass / missing_sections | 缺任一 P0 section blocked |
| approval gate | per-run authorization summary | pass / missing_fields | 只记录脱敏摘要 |
| rollback playbook | incident type、stage | rollback steps、owner | 不执行真实动作 |

**设计约束**：文档不能包含真实敏感值；不得把 runbook 视为自动授权；所有真实操作仍需 per-run 授权。

**命名规范**：`runbook_status`、`approval_status`、`rollback_status`、`owner_role=research_owner|trading_node_owner|approver`。

**平台目标**：操作手册与审批门。

### 依赖与并行门控

CR016-S01/S02/S03 合同冻结后可实现；与 CR016-S05/S06 LLD 可并行设计，但文档文件开发需串行合并。

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR016-S04-T1 | 创建 | `docs/QMT-SIMULATION-LIVE-RUNBOOK.md` | 写 simulation/live runbook 和审批门 |
| CR016-S04-T2 | 创建 | `tests/test_cr016_runbook_approval_gates.py` | 验证 runbook 必需章节和授权字段 |
| CR016-S04-T3 | 修改 | `README.md` / `docs/USER-MANUAL.md` | 按 LLD 写用户入口与禁止事项 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr016_runbook_approval_gates.py`。

**验证方式**：文档 / checklist contract。

**依赖环境**：Python 3.11、uv、pytest。

**关键验证场景**：缺异常处理 blocked；缺 kill switch blocked；缺审批字段 blocked；runbook 不自动授权。

## 量化验收标准（acceptance_criteria）

- [x] runbook 覆盖启动、审批、异常处理、对账、kill switch、暂停 / 恢复、回滚 7 类章节。
- [x] 缺任一 P0 章节时 runbook_status=fail。
- [x] approval gate 必需字段覆盖率 100%。
- [x] 文档中自动授权真实操作的声明次数为 0。

## 阻塞说明

已完成 CP7 验证并收敛为 `verified`。runbook 完成、CP6 / CP7 PASS 或 Story verified 均不等于真实运行授权；simulation、live_readonly、small_live、scale_up 和任何真实 broker 操作仍需后续 per-run authorization。
