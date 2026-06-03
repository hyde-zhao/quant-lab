---
story_id: "CR019-S08-fallback-incident-signed-file-boundary"
title: "fallback / incident / signed file fail-closed 边界"
story_slug: "fallback-incident-signed-file-boundary"
status: "verified"
priority: "P0"
wave: "CR019-W4-FALLBACK-DEFERRED"
depends_on:
  - "CR019-S04-windows-gateway-lifecycle-deployment"
  - "CR019-S05-pairing-hmac-auth-redaction"
  - "CR019-S06-qmt-endpoint-matrix-contract"
  - "CR019-S07-run-gate-blocked-reason-integration"
dependency_type:
  - upstream: "CR019-S04-windows-gateway-lifecycle-deployment"
    type: "contract"
  - upstream: "CR019-S05-pairing-hmac-auth-redaction"
    type: "contract"
  - upstream: "CR019-S06-qmt-endpoint-matrix-contract"
    type: "contract"
  - upstream: "CR019-S07-run-gate-blocked-reason-integration"
    type: "runtime-gate"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_gateway_fallback.py"
    - "tests/test_cr019_qmt_gateway_fallback.py"
  shared:
    - "docs/QMT-INCIDENT-PLAYBOOK.md"
  merge_owner: "CR019-S08-fallback-incident-signed-file-boundary"
  forbidden:
    - "automatic real QMT fallback"
    - "real broker lake write"
    - "real order/cancel/account query"
    - "publish"
    - "simulation/live run"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.12"
    - "process/HLD-QMT-TRADING.md#17.4"
    - "process/ARCHITECTURE-DECISION.md#ADR-072"
    - "process/stories/CR019-S08-fallback-incident-signed-file-boundary.md"
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
updated_at: "2026-05-31T09:23:13+08:00"
change_id: "CR-019"
dev_ready_at: "2026-05-31T08:53:24+08:00"
dev_ready_reason: "S04/S05/S06/S07 均已 verified；CP5/LLD 已确认，当前无 dev_running 文件冲突；只允许 fixture-only fallback / incident / signed file fail-closed 合同实现，不授权真实 QMT / broker / account / order / simulation/live 操作。"
dev_handoff: "process/handoffs/META-DEV-CR019-S08-IMPLEMENT-2026-05-31.md"
dev_agent_id: "019e7b88-93ba-7223-b0f1-859c712eaf25"
dev_agent_name: "dev-yang"
dev_started_at: "2026-05-31T08:56:52+08:00"
dev_completed_at: "2026-05-31T09:04:53+08:00"
dev_closed_at: "2026-05-31T09:10:25+08:00"
cp6_status: "PASS"
cp6_result: "process/checks/CP6-CR019-S08-fallback-incident-signed-file-boundary-CODING-DONE.md"
cp6_checked_at: "2026-05-31T09:04:53+08:00"
ready_for_verification_at: "2026-05-31T09:04:53+08:00"
cp7_handoff: "process/handoffs/META-QA-CR019-S08-CP7-VERIFY-2026-05-31.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR019-S08-fallback-incident-signed-file-boundary-VERIFICATION-DONE.md"
cp7_conclusion: "PASS"
qa_agent_id: "019e7b97-e047-7673-ab10-e375d3ce62e0"
qa_agent_name: "qa-hua"
qa_started_at: "2026-05-31T09:13:33+08:00"
qa_completed_at: "2026-05-31T09:16:42+08:00"
qa_closed_at: "2026-05-31T09:23:13+08:00"
verified_at: "2026-05-31T09:23:13+08:00"
---

# CR019-S08：fallback / incident / signed file fail-closed 边界

## 目标

定义 gateway 不可达、auth fail、heartbeat fail、部署不满足和 gate fail 时的 blocked-only 或人工 dry-run / signed file drop fallback；确认 fallback 默认 fail-closed，不自动转为真实 QMT 或 broker 操作。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-16、UC-17 |
| 需求 | REQ-145、REQ-150、REQ-152 |
| HLD | `process/HLD.md` §33.12；`process/HLD-QMT-TRADING.md` §17.4 |
| ADR | ADR-072 |

## 开发上下文（dev_context）

**输入文件**：gateway lifecycle、auth、endpoint matrix、run gate Story 合同、QMT companion §17.4、本 Story 卡片。

**输出文件**：`trading/qmt_gateway_fallback.py`、`tests/test_cr019_qmt_gateway_fallback.py`；共享 `docs/QMT-INCIDENT-PLAYBOOK.md`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S04 | contract | gateway lifecycle / heartbeat 合同先冻结 | 不启动服务 | gateway unavailable 进入 blocked |
| CR019-S05 | contract | auth fail / redaction 合同先冻结 | 不读取 secret | auth fail 不触发真实 fallback |
| CR019-S06 | contract | endpoint blocked result shape 先冻结 | 不调用真实 endpoint | fallback 结果复用 typed blocked result |
| CR019-S07 | runtime-gate | run gate blocked reason 先冻结 | gate fail 时真实调用为 0 | signed file 仅人工 dry-run 入口 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_gateway_fallback.py`、`tests/test_cr019_qmt_gateway_fallback.py` | 当前 Story 独占 |
| shared | `docs/QMT-INCIDENT-PLAYBOOK.md` | merge owner 为当前 Story，S10 文档收敛时串行合并 |
| forbidden | 自动真实 QMT fallback、真实 broker lake 写入、真实发单 / 撤单 / 账户查询、publish、simulation/live run | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S08-T1 | 创建 | `trading/qmt_gateway_fallback.py` | 定义 gateway unavailable / auth fail / heartbeat fail / gate fail 的 fail-closed fallback |
| CR019-S08-T2 | 创建 | `tests/test_cr019_qmt_gateway_fallback.py` | 验证每类 failure 均不会触发真实 QMT / broker 操作 |
| CR019-S08-T3 | 修改 | `docs/QMT-INCIDENT-PLAYBOOK.md` | 按 LLD 增量记录人工 dry-run / signed file drop 处置边界 |
| CR019-S08-T4 | 定义 | `trading/qmt_gateway_fallback.py` | 定义 signed file payload 字段、签名状态、人工处理标记和过期策略 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_fallback.py`。

**验证方式**：fixture-only 合同测试；不得写 broker lake，不得生成真实 order，不得启动 gateway。

## 量化验收标准（acceptance_criteria）

- [ ] gateway/auth/heartbeat/gate fail 四类 failure 均返回 typed blocked result。
- [ ] fallback 自动触发真实 QMT / broker lake / order / cancel / account query 次数为 0。
- [ ] signed file 只包含 dry-run / manual handling 字段，自动执行字段数量为 0。
- [ ] incident 文档中敏感值、真实账户号、secret 示例出现次数为 0。

## 阻塞说明

CP5 已通过；仍需等待 W3 gate 合同满足后按 dev_gate 调度，fallback 不是绕过 gateway 或 run gate 的真实操作通道。
