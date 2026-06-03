---
story_id: "CR019-S10-docs-runbook-user-manual-boundary"
title: "CR-019 文档、runbook 与用户手册边界"
story_slug: "docs-runbook-user-manual-boundary"
status: "verified"
priority: "P1"
wave: "CR019-W5-DOCS-RUNBOOK"
depends_on:
  - "CR019-S01-stage6-admission-gate-package"
  - "CR019-S02-primary-benchmark-dashboard"
  - "CR019-S03-qmt-cside-client-cli-contract"
  - "CR019-S04-windows-gateway-lifecycle-deployment"
  - "CR019-S05-pairing-hmac-auth-redaction"
  - "CR019-S06-qmt-endpoint-matrix-contract"
  - "CR019-S07-run-gate-blocked-reason-integration"
  - "CR019-S08-fallback-incident-signed-file-boundary"
  - "CR019-S09-deferred-capability-register"
dependency_type:
  - upstream: "CR019-S01-stage6-admission-gate-package"
    type: "documentation-merge"
  - upstream: "CR019-S02-primary-benchmark-dashboard"
    type: "documentation-merge"
  - upstream: "CR019-S03-qmt-cside-client-cli-contract"
    type: "documentation-merge"
  - upstream: "CR019-S04-windows-gateway-lifecycle-deployment"
    type: "documentation-merge"
  - upstream: "CR019-S05-pairing-hmac-auth-redaction"
    type: "documentation-merge"
  - upstream: "CR019-S06-qmt-endpoint-matrix-contract"
    type: "documentation-merge"
  - upstream: "CR019-S07-run-gate-blocked-reason-integration"
    type: "documentation-merge"
  - upstream: "CR019-S08-fallback-incident-signed-file-boundary"
    type: "documentation-merge"
  - upstream: "CR019-S09-deferred-capability-register"
    type: "documentation-merge"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "docs/QMT-C-S-BRIDGE-RUNBOOK.md"
    - "tests/test_cr019_docs_runbook_boundary.py"
  shared:
    - "README.md"
    - "docs/USER-MANUAL.md"
    - "docs/QMT-SIMULATION-LIVE-RUNBOOK.md"
    - "docs/QMT-INCIDENT-PLAYBOOK.md"
  merge_owner: "CR019-S10-docs-runbook-user-manual-boundary"
  forbidden:
    - "process/HLD.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "delivery/**"
    - "real credential examples"
    - "runbook authorizes real trade"
lld_gate:
  required_inputs:
    - "process/HLD.md#33"
    - "process/HLD-QMT-TRADING.md#17"
    - "process/ARCHITECTURE-DECISION.md#ADR-067..ADR-073"
    - "process/stories/CR019-S01-stage6-admission-gate-package.md"
    - "process/stories/CR019-S02-primary-benchmark-dashboard.md"
    - "process/stories/CR019-S03-qmt-cside-client-cli-contract.md"
    - "process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md"
    - "process/stories/CR019-S05-pairing-hmac-auth-redaction.md"
    - "process/stories/CR019-S06-qmt-endpoint-matrix-contract.md"
    - "process/stories/CR019-S07-run-gate-blocked-reason-integration.md"
    - "process/stories/CR019-S08-fallback-incident-signed-file-boundary.md"
    - "process/stories/CR019-S09-deferred-capability-register.md"
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
updated_at: "2026-05-31T10:21:33+08:00"
change_id: "CR-019"
dev_ready_at: "2026-05-31T09:52:21+08:00"
dev_ready_reason: "S01..S09 均已 verified；CP5/LLD 已确认，当前无 dev_running 文件冲突；只允许文档 / runbook / 静态测试实现，不授权真实交易、服务启动、凭据读取、provider fetch、lake / broker lake 写入、publish 或 simulation/live。"
dev_handoff: "process/handoffs/META-DEV-CR019-S10-IMPLEMENT-2026-05-31.md"
dev_agent_id: "019e7bbd-ebb5-74a3-8745-f3dc74cfc1f0"
dev_agent_name: "dev-qin"
dev_started_at: "2026-05-31T09:55:07+08:00"
dev_completed_at: "2026-05-31T10:04:36+08:00"
dev_closed_at: "2026-05-31T10:10:20+08:00"
cp6_status: "PASS"
cp6_result: "process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md"
cp6_completed_at: "2026-05-31T10:04:36+08:00"
ready_for_verification_at: "2026-05-31T10:04:36+08:00"
dev_agent_evidence: "spawn_agent returned agent_id=019e7bbd-ebb5-74a3-8745-f3dc74cfc1f0 nickname=dev-qin; wait_agent returned completed CR019-S10 CP6 PASS; close_agent previous_status returned completed CR019-S10 CP6 PASS"
main_thread_cp6_result: "PASS: py_compile; S10+S09+S08+S07 regression 38 passed in 0.17s; dependency diff empty; cache status empty; static doc boundary test PASS; suggested scans reviewed with only existing forbidden-term examples/placeholders and required blocked QMT/MiniQMT/XtQuant mentions; prompt scan empty; diff check PASS"
qa_handoff: "process/handoffs/META-QA-CR019-S10-CP7-VERIFY-2026-05-31.md"
qa_agent_id: "019e7bd0-f92b-7550-be16-3a8fe67f77de"
qa_agent_name: "qa-kong"
qa_started_at: "2026-05-31T10:15:57+08:00"
qa_completed_at: "2026-05-31T10:18:14+08:00"
qa_closed_at: "2026-05-31T10:21:33+08:00"
cp7_status: "PASS"
cp7_result: "process/checks/CP7-CR019-S10-docs-runbook-user-manual-boundary-VERIFICATION-DONE.md"
verified_at: "2026-05-31T10:21:33+08:00"
qa_agent_evidence: "spawn_agent returned agent_id=019e7bd0-f92b-7550-be16-3a8fe67f77de nickname=qa-kong; wait_agent returned completed CR019-S10 CP7 PASS; close_agent previous_status returned completed CR019-S10 CP7 PASS"
main_thread_cp7_result: "PASS: py_compile; S10+S09+S08+S07 regression 38 passed in 0.18s; dependency diff empty; cache status empty; sensitive/permission scan reviewed with only forbidden-boundary/placeholders/denylist/history safety hits; real-config scan reviewed with only pip-install prohibition; dangerous scan reviewed with uv sync examples; prompt scan empty; diff check PASS"
---

# CR019-S10：CR-019 文档、runbook 与用户手册边界

## 目标

汇总 admission、QMT C/S bridge、pairing/HMAC、endpoint/gate/fallback、后置能力和真实操作禁止声明到用户可读文档边界；确认文档只描述受控流程，不授权 simulation / live 或真实 broker 操作。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15、UC-16、UC-17、UC-18 |
| 需求 | REQ-151、REQ-152、REQ-153 |
| HLD | `process/HLD.md` §33；`process/HLD-QMT-TRADING.md` §17 |
| ADR | ADR-067..ADR-073 |

## 开发上下文（dev_context）

**输入文件**：CR019-S01..S09 Story 合同、CP3 approved HLD / ADR、QMT companion HLD、本 Story 卡片。

**输出文件**：`docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr019_docs_runbook_boundary.py`；共享 `README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S01..S09 | documentation-merge | 9 个 Story 合同先冻结 | CP5 前不得实现 | S10 只做文档收敛和边界校验 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`tests/test_cr019_docs_runbook_boundary.py` | 当前 Story 独占 |
| shared | `README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md` | 当前 Story 为文档 merge owner，需串行合并 S08/S09 共享文档 |
| forbidden | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md`、`delivery/**`、真实凭据示例、runbook 授权真实交易 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S10-T1 | 创建 | `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | 汇总 C/S bridge、gateway lifecycle、pairing/HMAC、endpoint matrix、run gate 与 fallback |
| CR019-S10-T2 | 修改 | `README.md` | 增量加入阶段六 admission 与 QMT C/S bridge 用户入口边界 |
| CR019-S10-T3 | 修改 | `docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md` | 增量对齐 no-real-operation、per-run authorization 和 incident fail-closed 说明 |
| CR019-S10-T4 | 创建 | `tests/test_cr019_docs_runbook_boundary.py` | 验证 DQ 决策、10 Story 边界、禁止真实授权表和敏感值脱敏 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_docs_runbook_boundary.py`。

**验证方式**：文档静态测试；不得启动服务，不得发布 delivery，不得读取或写入真实凭据。

## 量化验收标准（acceptance_criteria）

- [ ] 文档覆盖 DQ-01..DQ-07 共 7 个 CP3 决策。
- [ ] 文档列出 CR019-S01..S10 共 10 个 Story 边界。
- [ ] no-real-operation 表覆盖 dependency change、service start、credential read、QMT / MiniQMT / XtQuant、provider fetch、lake / broker lake、publish、simulation/live 共 8 类禁止项。
- [ ] “runbook / Story verified 授权真实交易”语义匹配次数为 0，真实凭据示例出现次数为 0。

## 阻塞说明

CP5 已通过；仍需等待 S01..S09 confirmed LLD / 实现字段复核后按 dev_gate 调度，文档和 runbook 不构成真实 simulation/live、账户查询、发单、撤单、broker lake 写入或 publish 授权。
