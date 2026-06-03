---
story_id: "CR019-S07-run-gate-blocked-reason-integration"
title: "运行门控与 blocked reason 集成"
story_slug: "run-gate-blocked-reason-integration"
status: "verified"
priority: "P0"
wave: "CR019-W3-AUTH-ENDPOINT-GATE"
depends_on:
  - "CR019-S01-stage6-admission-gate-package"
  - "CR019-S06-qmt-endpoint-matrix-contract"
  - "CR015-S04-pretrade-risk-gate"
  - "CR016-S03-monitoring-heartbeat-and-kill-switch"
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
dependency_type:
  - upstream: "CR019-S01-stage6-admission-gate-package"
    type: "contract"
  - upstream: "CR019-S06-qmt-endpoint-matrix-contract"
    type: "contract"
  - upstream: "CR015-S04-pretrade-risk-gate"
    type: "runtime-gate"
  - upstream: "CR016-S03-monitoring-heartbeat-and-kill-switch"
    type: "runtime-gate"
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "authorization-contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_gateway_gates.py"
    - "tests/test_cr019_qmt_gateway_run_gates.py"
  shared:
    - "trading/stage_gate.py"
    - "trading/pretrade_risk.py"
    - "trading/kill_switch.py"
  merge_owner: "CR019-S07-run-gate-blocked-reason-integration"
  forbidden:
    - "HMAC pass as trade authorization"
    - "bypass CR015/CR016 gates"
    - "account query"
    - "real order/cancel"
    - "simulation/live run"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.11"
    - "process/HLD.md#33.12"
    - "process/HLD.md#33.13"
    - "process/HLD-QMT-TRADING.md#17.2"
    - "process/ARCHITECTURE-DECISION.md#ADR-070"
    - "process/ARCHITECTURE-DECISION.md#ADR-071"
    - "process/stories/CR019-S07-run-gate-blocked-reason-integration.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 4
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-31T08:50:59+08:00"
change_id: "CR-019"
dev_ready_at: "2026-05-31T08:25:16+08:00"
dev_ready_reason: "S01/S06 已 verified；CR015-S04、CR016-S03、CR016-S04 上游门控合同均已 verified；CP5/LLD 已确认，当前无 dev_running 文件冲突；只允许 fixture-only run gate blocked reason contract 实现，不授权真实 QMT / broker / account / order / simulation/live 操作。"
dev_handoff: "process/handoffs/META-DEV-CR019-S07-IMPLEMENT-2026-05-31.md"
dev_agent_id: "019e7b6d-929e-7bd2-be73-cbdad9a94a36"
dev_agent_name: "dev-he"
dev_started_at: "2026-05-31T08:27:22+08:00"
dev_completed_at: "2026-05-31T08:37:31+08:00"
dev_closed_at: "2026-05-31T08:42:42+08:00"
cp6_status: "PASS"
cp6_result: "process/checks/CP6-CR019-S07-run-gate-blocked-reason-integration-CODING-DONE.md"
cp6_checked_at: "2026-05-31T08:37:31+08:00"
ready_for_verification_at: "2026-05-31T08:37:31+08:00"
cp7_handoff: "process/handoffs/META-QA-CR019-S07-CP7-VERIFY-2026-05-31.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md"
cp7_conclusion: "PASS"
qa_agent_id: "019e7b7d-4f34-7fe0-9678-bf8f8b8f26ae"
qa_agent_name: "qa-yan"
qa_started_at: "2026-05-31T08:44:33+08:00"
qa_completed_at: "2026-05-31T08:46:57+08:00"
qa_closed_at: "2026-05-31T08:50:59+08:00"
verified_at: "2026-05-31T08:50:59+08:00"
---

# CR019-S07：运行门控与 blocked reason 集成

## 目标

将 run mode、CR016 stage gate、pre-trade risk、kill switch、per-run authorization、raw execution policy 接到 gateway blocked reason 合同；确认 pairing / HMAC 只做调用方识别，不替代交易授权。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15、UC-17 |
| 需求 | REQ-144、REQ-147、REQ-152、REQ-154 |
| HLD | `process/HLD.md` §33.11、§33.12、§33.13；`process/HLD-QMT-TRADING.md` §17.2 |
| ADR | ADR-070、ADR-071 |

## 开发上下文（dev_context）

**输入文件**：CR019-S01 admission package 合同、CR019-S06 endpoint matrix 合同、CR015/CR016 已验证门控合同、本 Story 卡片。

**输出文件**：`trading/qmt_gateway_gates.py`、`tests/test_cr019_qmt_gateway_run_gates.py`；共享 `trading/stage_gate.py`、`trading/pretrade_risk.py`、`trading/kill_switch.py`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S01 | contract | admission status / evidence package 字段先冻结 | admission blocked 时不得进入 QMT adapter | 阶段六 admission 是运行放行输入之一 |
| CR019-S06 | contract | endpoint blocked result shape 先冻结 | 不调用真实 endpoint | gate reason 必须回写到 endpoint typed result |
| CR015-S04 | runtime-gate | pre-trade risk gate 作为只读合同输入 | risk fail 时 adapter_call=0 | 不重写风险规则 |
| CR016-S03 | runtime-gate | kill switch / heartbeat 合同作为只读输入 | kill-switch fail 时 adapter_call=0 | 不启动监控服务 |
| CR016-S04 | authorization-contract | per-run authorization 合同作为只读输入 | 未授权时 simulation/live=blocked | 不发起真实 run |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_gateway_gates.py`、`tests/test_cr019_qmt_gateway_run_gates.py` | 当前 Story 独占 |
| shared | `trading/stage_gate.py`、`trading/pretrade_risk.py`、`trading/kill_switch.py` | 当前 Story 为 merge owner；需避免覆盖 CR015/CR016 已验证语义 |
| forbidden | HMAC pass 作为交易授权、绕过 CR015/CR016 gate、账户查询、真实发单 / 撤单、simulation/live run | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S07-T1 | 创建 | `trading/qmt_gateway_gates.py` | 定义 gateway 运行门控聚合器、blocked reason priority 和 fail-closed 行为 |
| CR019-S07-T2 | 修改 | `trading/stage_gate.py` | 按 LLD 暴露 admission / stage gate read-only 输入，不改变既有 gate 语义 |
| CR019-S07-T3 | 修改 | `trading/pretrade_risk.py`、`trading/kill_switch.py` | 按 LLD 接入只读 gate result，不增加真实 broker 操作 |
| CR019-S07-T4 | 创建 | `tests/test_cr019_qmt_gateway_run_gates.py` | 验证 gate、auth、risk、kill-switch、authorization blocked reason 与 adapter_call=0 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_run_gates.py`。

**验证方式**：fixture-only 合同测试；不得触发真实账户查询、发单、撤单、broker lake 写入或 simulation/live run。

## 量化验收标准（acceptance_criteria）

- [ ] gate、auth、risk、kill-switch、per-run authorization blocked reason 覆盖率为 100%。
- [ ] 任一 gate 缺失或失败时 adapter_call / real_order / cancel_order / account_query 均为 0。
- [ ] HMAC pass 直接授权 simulation/live/account/cancel 的次数为 0。
- [ ] CR015/CR016 既有 gate 语义被覆盖或绕过次数为 0。

## 阻塞说明

CP5 已通过；S01/S06 与 CR015/CR016 上游门控合同已满足，当前已进入受控离线实现。真实运行、真实账户查询、真实订单和 broker lake 写入均需后续独立授权，本 Story 只冻结门控合同。
