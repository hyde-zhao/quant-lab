---
story_id: "CR019-S04-windows-gateway-lifecycle-deployment"
title: "Windows FastAPI gateway 生命周期与部署合同"
story_slug: "windows-gateway-lifecycle-deployment"
status: "verified"
priority: "P0"
wave: "CR019-W2-CS-TRANSPORT"
depends_on:
  - "CR019-S03-qmt-cside-client-cli-contract"
dependency_type:
  - upstream: "CR019-S03-qmt-cside-client-cli-contract"
    type: "contract"
cp5_batch: "CR019-STAGE6-QMT-BRIDGE-BATCH-A"
implementation_allowed: true
file_ownership:
  primary:
    - "trading/qmt_gateway_service.py"
    - "trading/qmt_gateway_config.py"
    - "tests/test_cr019_qmt_gateway_lifecycle.py"
  shared:
    - "docs/QMT-GATEWAY-INSTALL.md"
  merge_owner: "CR019-S04-windows-gateway-lifecycle-deployment"
  forbidden:
    - "start FastAPI service"
    - "bind real port"
    - "install dependency"
    - "read Windows credential"
    - "call QMT service"
lld_gate:
  required_inputs:
    - "process/HLD.md#33.10"
    - "process/HLD-QMT-TRADING.md#17.1"
    - "process/HLD-QMT-TRADING.md#17.3"
    - "process/ARCHITECTURE-DECISION.md#ADR-068"
    - "process/stories/CR019-S04-windows-gateway-lifecycle-deployment.md"
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
updated_at: "2026-05-30T20:49:47+08:00"
change_id: "CR-019"
cp6_result: "process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md"
cp6_status: "PASS"
cp7_handoff: "process/handoffs/META-QA-CR019-S04-CP7-VERIFY-2026-05-30.md"
cp7_result: "process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md"
cp7_status: "PASS"
---

# CR019-S04：Windows FastAPI gateway 生命周期与部署合同

## 目标

定义 Windows QMT 节点上的 gateway 命令、配置、bind host/port、防火墙、heartbeat、运行生命周期和安装边界；本 Story 仍不启动服务。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 使用场景 | UC-16、UC-17 |
| 需求 | REQ-145、REQ-149、REQ-159 |
| HLD | `process/HLD.md` §33.4、§33.9、§33.10；`process/HLD-QMT-TRADING.md` §17.1、§17.3 |
| ADR | ADR-068 |

## 开发上下文（dev_context）

**输入文件**：CR019 C 侧 client Story、HLD-QMT companion §17、ADR-068。

**输出文件**：`trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`；共享 `docs/QMT-GATEWAY-INSTALL.md`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S03 | contract | REST request / response 合同先冻结 | S04 不复制 C 侧业务逻辑 | S 侧只接收 REST 并转换到 adapter boundary |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`tests/test_cr019_qmt_gateway_lifecycle.py` | 当前 Story 独占 |
| shared | `docs/QMT-GATEWAY-INSTALL.md` | merge owner 为当前 Story |
| forbidden | 服务启动、真实端口绑定、依赖安装、凭据读取、真实 QMT service call | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR019-S04-T1 | 创建 | `trading/qmt_gateway_config.py` | 定义 bind、firewall、allowlist、heartbeat、redaction config 合同 |
| CR019-S04-T2 | 创建 | `trading/qmt_gateway_service.py` | 定义 service lifecycle contract，不启动服务 |
| CR019-S04-T3 | 创建 | `tests/test_cr019_qmt_gateway_lifecycle.py` | 验证公网默认 fail、服务启动计数为 0、配置字段完整 |
| CR019-S04-T4 | 修改 | `docs/QMT-GATEWAY-INSTALL.md` | 按 LLD 输出安装 / 运行边界，不包含真实凭据 |

## 验证上下文（validation_context）

**验证入口**：`uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py`。

**验证方式**：离线配置合同测试，不启动 FastAPI，不绑定端口。

## 量化验收标准（acceptance_criteria）

- [ ] gateway command、配置路径、bind、firewall、allowlist、heartbeat 字段覆盖率为 100%。
- [ ] public exposure allowed count 为 0。
- [ ] service_start_count、port_bind_count、qmt_api_call 均为 0。
- [ ] dependency_change 和 credential_read 均为 0。

## 阻塞说明

CP5 已通过；S03 C 侧 client / CLI / REST transport 合同已 CP7 PASS 并收敛为 verified，当前 Story 已完成 `process/handoffs/META-DEV-CR019-S04-IMPLEMENT-2026-05-30.md` 调度给 `meta-dev/dev-lv` 的受控离线实现；CP7 已通过 `process/handoffs/META-QA-CR019-S04-CP7-VERIFY-2026-05-30.md` 调度给 `meta-qa/qa-wei` 验证并 PASS。仍不得启动服务、绑定真实端口、安装依赖、读取 Windows 凭据或访问真实 QMT 服务端。

## CP6 编码完成证据

| 项目 | 结果 | 证据 |
|---|---|---|
| CP6 结论 | PASS | `process/checks/CP6-CR019-S04-windows-gateway-lifecycle-deployment-CODING-DONE.md` |
| 实现 agent | `meta-dev/dev-lv` | agent_id / thread_id `019e78d8-0980-7af0-83a0-5c0b4aaa8d74` |
| 实现文件 | 完成 | `trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py`、`tests/test_cr019_qmt_gateway_lifecycle.py`、`docs/QMT-GATEWAY-INSTALL.md` |
| 验证结果 | PASS | `tests/test_cr019_qmt_gateway_lifecycle.py` + `tests/test_cr019_qmt_cside_client_cli.py`：16 passed；主线程复跑 `16 passed in 0.10s` |
| 禁止真实操作计数 | PASS | dependency_change、service_start、port_bind、credential_read、qmt_api_call、real_order、real_cancel、account_query、provider_fetch、lake_write、publish、simulation_or_live_run 均为 0 |
| OPEN | 非阻断 | `O-CR019-S04-01` 保持 OPEN：真实 FastAPI runtime 依赖、安装脚本和服务启动授权不在 S04 范围 |

## CP7 验证完成证据

| 项目 | 结果 | 证据 |
|---|---|---|
| CP7 结论 | PASS | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| 验证 agent | `meta-qa/qa-wei` | agent_id / thread_id `019e78e8-037c-78c1-81e8-050ec8d844f5` |
| 验证结果 | PASS | `tests/test_cr019_qmt_gateway_lifecycle.py` + `tests/test_cr019_qmt_cside_client_cli.py`：16 passed；主线程复跑 `16 passed in 0.11s` |
| 禁止真实操作计数 | PASS | dependency_change、service_start、port_bind、credential_read、qmt_api_call、real_order、real_cancel、account_query、provider_fetch、lake_write、publish、simulation_or_live_run 均为 0 |
| OPEN | 非阻断 | `O-CR019-S04-01` 保持 OPEN：真实 FastAPI runtime 依赖、安装脚本和服务启动授权不在 S04 范围 |
