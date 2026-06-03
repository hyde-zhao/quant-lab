---
story_id: "CR019-S06-qmt-endpoint-matrix-contract"
title: "完整 QMT endpoint matrix 与 typed blocked result"
story_slug: "qmt-endpoint-matrix-contract"
status: "verified"
priority: "P0"
wave: "CR019-W3-AUTH-ENDPOINT-GATE"
depends_on:
  - "CR019-S03-qmt-cside-client-cli-contract"
  - "CR019-S04-windows-gateway-lifecycle-deployment"
  - "CR019-S05-pairing-hmac-auth-redaction"
dependency_type:
  - upstream: "CR019-S03-qmt-cside-client-cli-contract"
    type: "contract"
  - upstream: "CR019-S04-windows-gateway-lifecycle-deployment"
    type: "contract"
  - upstream: "CR019-S05-pairing-hmac-auth-redaction"
    type: "contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_endpoint_matrix.py"
    - "trading/qmt_gateway_contracts.py"
    - "tests/test_cr019_qmt_endpoint_matrix.py"
  shared:
    - "trading/qmt_client.py"
  merge_owner: "CR019-S06-qmt-endpoint-matrix-contract"
  forbidden:
    - "dry-run-only target baseline"
    - "endpoint visible as operation authorization"
    - "real QMT call"
    - "MiniQMT / XtQuant operation"
    - "broker lake write"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.11"
    - "process/HLD-QMT-TRADING.md#17.2"
    - "process/ARCHITECTURE-DECISION.md#ADR-070"
    - "process/stories/CR019-S06-qmt-endpoint-matrix-contract.md"
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
updated_at: "2026-05-31T08:25:16+08:00"
change_id: "CR-019"
dev_ready_at: "2026-05-31T08:00:26+08:00"
dev_ready_reason: "S03/S04/S05 均已 CP7 PASS 且 verified；CP5/LLD 已确认，当前无 dev_running 文件冲突；只允许 fixture-only endpoint matrix contract 实现，不授权真实 QMT / MiniQMT / XtQuant / broker lake 操作。"
dev_handoff: "process/handoffs/META-DEV-CR019-S06-IMPLEMENT-2026-05-31.md"
dev_agent_id: "019e7b57-2b50-7353-a782-a0f6ddc513af"
dev_agent_name: "dev-you"
dev_started_at: "2026-05-31T08:02:53+08:00"
cp6_status: "PASS"
cp6_checkpoint: "process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md"
cp6_conclusion: "PASS"
implementation_completed_at: "2026-05-31T08:12:36+08:00"
ready_for_verification_at: "2026-05-31T08:12:36+08:00"
cp7_handoff: "process/handoffs/META-QA-CR019-S06-CP7-VERIFY-2026-05-31.md"
cp7_status: "PASS"
cp7_checkpoint: "process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md"
cp7_conclusion: "PASS"
qa_agent_id: "019e7b64-9eb5-7193-99d1-57466159d32d"
qa_agent_name: "qa-wei"
qa_started_at: "2026-05-31T08:17:35+08:00"
qa_completed_at: "2026-05-31T08:19:59+08:00"
qa_closed_at: "2026-05-31T08:25:16+08:00"
verified_at: "2026-05-31T08:25:16+08:00"
---

# CR019-S06：完整 QMT endpoint matrix 与 typed blocked result

## 目标

定义 health / capabilities、validate / dry-run、行情、账户、持仓、委托、成交、simulation / live、reconciliation、kill-switch 等 QMT gateway endpoint 类别，以及每类 endpoint 的 allowed / blocked typed result 合同；确认接口完整支持不等于真实操作授权。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-15、UC-16、UC-17 |
| 需求 | REQ-146、REQ-147、REQ-152 |
| HLD | `process/HLD.md` §33.11；`process/HLD-QMT-TRADING.md` §17.2 |
| ADR | ADR-070 |

## 开发上下文（dev_context）

**输入文件**：CP3 approved HLD endpoint matrix、QMT companion §17.2、CR019-S03/S04/S05 Story 合同、本 Story 卡片。

**输出文件**：`trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`tests/test_cr019_qmt_endpoint_matrix.py`；共享 `trading/qmt_client.py`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S03 | contract | C 侧 client request / result shape 先冻结 | 不导入 `xtquant` | endpoint matrix 必须由 Python client 可消费 |
| CR019-S04 | contract | S 侧 REST / gateway lifecycle 合同先冻结 | 不启动 gateway | endpoint path / method / response 不要求服务运行 |
| CR019-S05 | contract | auth header / scope / redaction 合同先冻结 | HMAC 不替代 run gate | endpoint 可见性与操作授权分离 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`tests/test_cr019_qmt_endpoint_matrix.py` | 当前 Story 独占 |
| shared | `trading/qmt_client.py` | merge owner 为当前 Story，需与 CR019-S03 串行合并 |
| forbidden | dry-run-only 目标基线、endpoint visible = operation authorization、真实 QMT / MiniQMT / XtQuant 调用、broker lake 写入 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S06-T1 | 创建 | `trading/qmt_endpoint_matrix.py` | 定义完整 endpoint matrix、类别、方法、scope 和 gate 输入字段 |
| CR019-S06-T2 | 创建 | `trading/qmt_gateway_contracts.py` | 定义 typed allowed / blocked result、blocked reason enum 和 error payload |
| CR019-S06-T3 | 修改 | `trading/qmt_client.py` | 按 LLD 接入 endpoint matrix 的类型化 client 方法，不复制业务逻辑 |
| CR019-S06-T4 | 创建 | `tests/test_cr019_qmt_endpoint_matrix.py` | 覆盖 endpoint 类别、blocked case、auth / gate 分离和真实调用计数为 0 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_endpoint_matrix.py`。

**验证方式**：fixture-only 合同测试；不得启动 gateway，不得调用 QMT / MiniQMT / XtQuant。

## 量化验收标准（acceptance_criteria）

- [ ] HLD §33.11 中 endpoint 类别覆盖率为 100%。
- [ ] 每类 endpoint 至少包含 1 个 typed blocked result case。
- [ ] health / capabilities 可见不提升为 account / order / cancel / simulation / live 授权。
- [ ] 真实 QMT / MiniQMT / XtQuant 调用计数为 0，broker lake 写入计数为 0。

## 阻塞说明

CP5 已通过；仍需等待 S03/S04/S05 合同实现 / 验证后按 dev_gate 调度，endpoint matrix 完整支持只冻结接口契约，不构成任何真实操作授权。

## CP6 / 状态证据

| 字段 | 结果 |
|---|---|
| 状态 | `ready-for-verification` |
| CP6 | `process/checks/CP6-CR019-S06-qmt-endpoint-matrix-contract-CODING-DONE.md` |
| CP6 结论 | `PASS` |
| 实现范围 | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_client.py`、`tests/test_cr019_qmt_endpoint_matrix.py` |
| 验证 | `py_compile` PASS；S06 + S03/S04/S05 回归 `36 passed in 0.21s` |
| Forbidden counters | client / contracts 全部为 0 |
| 安全边界 | 未读取 `.env` / secret，未启动服务，未绑定端口，未打开 socket，未调用真实 QMT / MiniQMT / XtQuant / provider / lake / broker / publish / simulation / live |

## CP7 / 状态证据

| 字段 | 结果 |
|---|---|
| 状态 | `verified` |
| CP7 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| CP7 结论 | `PASS` |
| QA agent | `meta-qa/qa-wei`，agent_id/thread_id=`019e7b64-9eb5-7193-99d1-57466159d32d` |
| 验证 | S06 + S03/S04/S05 回归 `36 passed in 0.19s`；py_compile、依赖 diff、缓存检查、forbidden import scan、宽泛 forbidden call scan、dangerous command scan、prompt injection scan 均 PASS |
| Forbidden counters | client / contracts 全部为 0 |
| 安全边界 | CP7 不授权真实 QMT、MiniQMT、XtQuant、provider、lake、broker、publish、simulation/live、服务启动、端口绑定、socket 或凭据读取 |
