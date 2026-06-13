---
story_id: "CR020-S05-query-positions-readonly"
title: "`query_positions` 单接口只读准入"
story_slug: "query-positions-readonly"
status: "verified-fixture-static-pending-manual-validation"
priority: "P0"
wave: "CR020-W3-READONLY-POSITIONS"
depends_on:
  - "CR020-S02-server-qmt-login-session"
  - "CR020-S03-linux-client-rest-transport"
  - "CR020-S04-hmac-pairing-allowlist-scope"
dependency_type:
  - "session-ready-runtime"
  - "client-transport-contract"
  - "auth-scope-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
only_query_positions_allowed: true
query_positions_scope: "qmt:positions:read"
qmt_real_call_allowed_before_cp5: false
account_write_allowed: false
order_cancel_modify_allowed: false
simulation_or_live_allowed: false
broker_lake_write_allowed: false
file_ownership:
  primary:
    - "trading/qmt_endpoint_matrix.py"
    - "trading/qmt_gateway_contracts.py"
    - "trading/qmt_gateway_service.py"
    - "trading/qmt_client.py"
    - "tests/test_cr020_query_positions_readonly.py"
  shared:
    - "trading/qmt_auth.py"
    - "trading/qmt_redaction.py"
    - "trading/qmt_gateway_session.py"
  merge_owner: "CR020-S05-query-positions-readonly"
  forbidden:
    - "real endpoints other than query_positions"
    - "account/orders/trades/simulation/live"
    - "order/cancel/account_write/broker_lake_write"
    - "provider fetch"
    - "lake write"
    - "publish"
    - "unredacted payload"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.4"
    - "process/HLD.md#36.9"
    - "process/HLD.md#36.11"
    - "process/ARCHITECTURE-DECISION.md#ADR-090"
    - "process/ARCHITECTURE-DECISION.md#ADR-091"
    - "process/ARCHITECTURE-DECISION.md#ADR-092"
    - "process/stories/CR020-S05-query-positions-readonly.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  only_query_positions_allowed: true
  query_positions_scope: "qmt:positions:read"
  qmt_real_call_allowed_before_cp5: false
  account_write_allowed: false
  order_cancel_modify_allowed: false
  simulation_or_live_allowed: false
  broker_lake_write_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S05-query-positions-readonly-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S05：`query_positions` 单接口只读准入

## 目标

定义 CR-020 唯一真实只读查询接口 `query_positions`、scope=`qmt:positions:read`、session/auth gate、response redaction、blocked endpoint matrix 和 failure reason。该 Story 不授权其他 endpoint、交易、账户写入或 simulation/live。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D5 |
| HLD | `process/HLD.md` §36.4、§36.9、§36.11、§36.17 |
| ADR | ADR-090、ADR-091、ADR-092 |
| CP3 决策 | DQ-CP3-CR020-05 |

## 开发上下文（dev_context）

**背景说明**：CR-020 的范围是 server login 后的只读持仓查询准入。其他 QMT endpoint 和任何写操作仍然 later-gated，不能借由 endpoint matrix 或 runbook 获得授权。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-090..092、`process/stories/CR020-S02-server-qmt-login-session.md`、`process/stories/CR020-S03-linux-client-rest-transport.md`、`process/stories/CR020-S04-hmac-pairing-allowlist-scope.md`、本 Story 卡片。

**输出文件**：`trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_gateway_service.py`、`trading/qmt_client.py`、`tests/test_cr020_query_positions_readonly.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| endpoint | 只允许 `query_positions` 进入 CR-020 真实只读范围 |
| scope | 固定为 `qmt:positions:read` |
| gates | session ready、HMAC、allowlist、scope、redaction 全部通过后才可进入后续只读查询 |
| blocked endpoints | account write、order、cancel、modify、trades、simulation、live、broker lake 均 blocked |
| response | 持仓响应必须 redacted，不输出敏感账号或未脱敏 payload |

**设计约束**：不得启用其他真实 endpoint；不得执行订单、撤单、改单、账户写入；不得 simulation/live；不得写 broker lake；不得 provider/lake/publish。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR020-S02 | session-ready-runtime | 必须消费 session ready gate | CP5 前不得实现 | session 非 ready 时 adapter_call=0 |
| CR020-S03 | client-transport-contract | 必须消费 REST client contract | CP5 前不得实现 | C 端只通过 Python client |
| CR020-S04 | auth-scope-contract | 必须消费 HMAC / scope contract | CP5 前不得实现 | scope 不足时 fail-closed |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_gateway_service.py`、`trading/qmt_client.py`、`tests/test_cr020_query_positions_readonly.py` | 当前 Story LLD owner；共享文件需与 S03/S04 串行合并 |
| shared | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`trading/qmt_gateway_session.py` | 消费上游合同，不擅自改 scope / redaction |
| forbidden | 除 `query_positions` 外真实 endpoint、订单/账户写入、broker lake、provider/lake/publish、未脱敏 payload | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S05-T1 | 设计 | `trading/qmt_endpoint_matrix.py` | 定义 CR-020 endpoint matrix 和 blocked reasons |
| CR020-S05-T2 | 设计 | `trading/qmt_gateway_contracts.py` | 定义 `query_positions` request/response/error schema |
| CR020-S05-T3 | 设计 | `trading/qmt_gateway_service.py` | 规划 session/auth/scope gate 串联 |
| CR020-S05-T4 | 设计 | `trading/qmt_client.py` | 规划 typed client 方法和 blocked result |
| CR020-S05-T5 | 验证设计 | `tests/test_cr020_query_positions_readonly.py` | 覆盖只读、blocked endpoint、redaction 和 no-real-operation tests |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_query_positions_readonly.py`，但本阶段不执行。

**验证方式**：fixture-only endpoint matrix、gate chain、response redaction、blocked endpoint scan；CP7 实机只读验证必须后置。

**依赖环境**：CP5 前不依赖真实 QMT、MiniQMT、XtQuant、gateway 或 `.env`。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| session not ready | `query_positions` blocked |
| HMAC / scope fail | adapter_call=0 |
| order/cancel/account_write endpoint | blocked |
| response payload | redacted |

## 量化验收标准（acceptance_criteria）

- [ ] CR-020 唯一真实只读 endpoint 为 `query_positions`。
- [ ] `query_positions` scope 固定为 `qmt:positions:read`。
- [ ] 除 `query_positions` 外真实 endpoint allowed 次数为 0。
- [ ] order、cancel、modify、account_write、broker_lake、provider、lake、publish、simulation、live 计数均为 0。
- [ ] 未脱敏 payload 输出次数为 0。

## 阻塞说明

CP5 前不得实现；任何新增 endpoint、交易、账户写入、broker lake、simulation/live 或真实 QMT 查询请求都必须回退 meta-po 独立门控。
