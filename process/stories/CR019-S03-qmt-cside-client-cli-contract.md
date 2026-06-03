---
story_id: "CR019-S03-qmt-cside-client-cli-contract"
title: "QMT C 侧 Python client 与薄 CLI 合同"
story_slug: "qmt-cside-client-cli-contract"
status: "verified"
priority: "P0"
wave: "CR019-W2-CS-TRANSPORT"
depends_on:
  - "CR015-S02-qmt-broker-adapter-contract"
  - "CR016-S04-simulation-live-runbook-and-approval-gates"
dependency_type:
  - upstream: "CR015-S02-qmt-broker-adapter-contract"
    type: "contract"
  - upstream: "CR016-S04-simulation-live-runbook-and-approval-gates"
    type: "contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_client.py"
    - "trading/qmt_cli.py"
    - "tests/test_cr019_qmt_cside_client_cli.py"
  shared:
    - "trading/qmt_transport.py"
  merge_owner: "CR019-S03-qmt-cside-client-cli-contract"
  forbidden:
    - "xtquant import on local_backtest C side"
    - "credential files or secret values"
    - "service start"
    - "pyproject.toml"
    - "uv.lock"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.9"
    - "process/HLD-QMT-TRADING.md#17.1"
    - "process/ARCHITECTURE-DECISION.md#ADR-068"
    - "process/ARCHITECTURE-DECISION.md#ADR-069"
    - "process/stories/CR019-S03-qmt-cside-client-cli-contract.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  service_start_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 4
created_at: "2026-05-30T18:24:00+08:00"
updated_at: "2026-05-30T20:21:24+08:00"
change_id: "CR-019"
---

# CR019-S03：QMT C 侧 Python client 与薄 CLI 合同

## 目标

规划 local_backtest 内部 QMT C 侧 Python client / 函数调用主接口，并将 CLI 限定为复用同一 client 的薄包装。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-16、UC-17 |
| 需求 | REQ-142、REQ-145、REQ-159、REQ-160 |
| HLD | `process/HLD.md` §33.4、§33.9；`process/HLD-QMT-TRADING.md` §17.1 |
| ADR | ADR-068、ADR-069 |

## 开发上下文（dev_context）

**输入文件**：CR015 adapter contract、CR016 runbook、CR019 HLD / ADR、本 Story 卡片。

**输出文件**：`trading/qmt_client.py`、`trading/qmt_cli.py`、`tests/test_cr019_qmt_cside_client_cli.py`；共享 `trading/qmt_transport.py`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR015-S02 | contract | adapter boundary 可引用 | 不实现真实 adapter | C 侧只通过 REST/gateway |
| CR016-S04 | contract | stage / approval 字段可引用 | 不授权真实运行 | client 请求必须携带运行上下文 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_client.py`、`trading/qmt_cli.py`、`tests/test_cr019_qmt_cside_client_cli.py` | 当前 Story 独占 |
| shared | `trading/qmt_transport.py` | merge owner 为当前 Story |
| forbidden | C 侧 import `xtquant`、读取凭据、启动服务、依赖变更 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S03-T1 | 创建 | `trading/qmt_client.py` | 定义 typed request / response / blocked reason client 合同 |
| CR019-S03-T2 | 创建 | `trading/qmt_cli.py` | 定义薄 CLI wrapper，只负责参数解析、输出格式和退出码 |
| CR019-S03-T3 | 修改 | `trading/qmt_transport.py` | 按 LLD 接入 REST transport enum，不接真实 QMT |
| CR019-S03-T4 | 创建 | `tests/test_cr019_qmt_cside_client_cli.py` | 验证 CLI 复用 client、C 侧无 xtquant、blocked result 稳定 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_cside_client_cli.py`。

**验证方式**：离线合同测试和静态 import 禁区检查。

## 量化验收标准（acceptance_criteria）

- [x] C 侧 `xtquant` import 次数为 0。
- [x] CLI 业务逻辑复制次数为 0，100% 调用同一 client contract。
- [x] health / capabilities / query / order intent / simulation-live 请求均有 typed blocked result。
- [x] dependency_change、service_start、credential_read、qmt_operation 均为 0。

## 阻塞说明

CP5 已通过；CR015-S02、CR016-S04 和 CR019-W1 的 S01/S02 均已 verified，当前 Story 已完成受控离线实现并进入 `ready-for-verification`；仍不得导入 `xtquant`、读取凭据、启动服务或执行真实 QMT 操作。

## CP6 编码完成证据

| 字段 | 内容 |
|---|---|
| CP6 文件 | `process/checks/CP6-CR019-S03-qmt-cside-client-cli-contract-CODING-DONE.md` |
| CP6 结论 | PASS |
| 完成时间 | 2026-05-30T20:04:42+08:00 |
| 实现 agent | `meta-dev/dev-qin`，agent_id / thread_id `019e78be-613b-7783-bca1-b48ef8e38365` |
| 实现文件 | `trading/qmt_client.py`、`trading/qmt_cli.py`、`trading/qmt_transport.py`、`tests/test_cr019_qmt_cside_client_cli.py` |
| 验证结果 | `py_compile` PASS；S03 专项 `7 passed in 0.06s`；S03 + CR015 adapter + S01 admission 回归 `29 passed in 0.13s`；主线程复跑 S03 + CR015 adapter + S01 admission `29 passed in 0.13s` |
| 禁止操作计数 | dependency_change、service_start、credential_read、qmt_operation、real_order、real_cancel、account_query、provider_fetch、lake_write、broker_lake_write、publish、simulation_or_live_run 均为 0 |
| 状态 | verified |

## CP7 验证完成证据

| 字段 | 内容 |
|---|---|
| CP7 文件 | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` |
| CP7 结论 | PASS |
| 验证 agent | `meta-qa/qa-shi`，agent_id / thread_id `019e78cd-b3e8-74c0-ba1e-6172a5bf125e` |
| 完成时间 | 2026-05-30T20:16:35+08:00；主线程关闭 / 复核时间 2026-05-30T20:21:24+08:00 |
| 验证结果 | S03 + CR015 adapter + S01 admission 回归 `29 passed in 0.13s`；主线程复跑同组回归 `29 passed in 0.13s`；py_compile、diff check、禁区扫描和 counters probe 均 PASS |
| 禁止操作计数 | dependency_change、service_start、credential_read、qmt_operation、qmt_api_call、xtquant_import、real_order、real_cancel、account_query、provider_fetch、lake_write、broker_lake_write、publish、simulation_or_live_run、service_bind、http_client_call、gateway_socket_open 均为 0 |
