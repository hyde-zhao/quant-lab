---
story_id: "CR020-S01-windows-gateway-runtime-admission"
title: "Windows gateway runtime 与准入合同"
story_slug: "windows-gateway-runtime-admission"
status: "verified-fixture-static-pending-manual-validation"
priority: "P0"
wave: "CR020-W1-GATEWAY-RUNTIME-SESSION"
depends_on:
  - "CR019-S04-windows-gateway-lifecycle-deployment"
dependency_type:
  - "prior-gateway-lifecycle-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
dependency_change_allowed: false
service_start_allowed: false
port_bind_allowed: false
real_env_read_allowed: false
qmt_operation_allowed: false
file_ownership:
  primary:
    - "trading/qmt_gateway_cli.py"
    - "trading/qmt_gateway_service.py"
    - "trading/qmt_gateway_config.py"
    - "tests/test_cr020_windows_gateway_runtime_admission.py"
  shared:
    - "docs/QMT-GATEWAY-INSTALL.md"
    - "trading/qmt_gateway_contracts.py"
  merge_owner: "CR020-S01-windows-gateway-runtime-admission"
  forbidden:
    - "pyproject.toml"
    - "uv.lock"
    - ".env"
    - ".env.*"
    - "service start before CP5/CP6/CP7 gate"
    - "port bind before runtime authorization"
    - "QMT / MiniQMT / XtQuant call during planning"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.3"
    - "process/HLD.md#36.8"
    - "process/HLD.md#36.12"
    - "process/ARCHITECTURE-DECISION.md#ADR-087"
    - "process/ARCHITECTURE-DECISION.md#ADR-088"
    - "process/ARCHITECTURE-DECISION.md#ADR-093"
    - "process/stories/CR020-S01-windows-gateway-runtime-admission.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  service_start_allowed: false
  port_bind_allowed: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S01-windows-gateway-runtime-admission-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S01：Windows gateway runtime 与准入合同

## 目标

冻结 Windows S 端 gateway runtime 的命令、配置、生命周期、bind / heartbeat、read-only admission 状态和 CP5 前运行禁止边界。该 Story 只进入 CR-020 全量 LLD 队列；CP5 人工确认前不得实现、启动服务、绑定端口或连接 QMT。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D1、D7 |
| HLD | `process/HLD.md` §36.3、§36.8、§36.12、§36.17 |
| ADR | ADR-087、ADR-088、ADR-093 |
| CP3 决策 | DQ-CP3-CR020-01、DQ-CP3-CR020-02、DQ-CP3-CR020-07 |

## 开发上下文（dev_context）

**背景说明**：CR-020 需要让 Windows S 端成为唯一 QMT 服务端触达点，但当前阶段只冻结 Story 计划和后续 LLD 输入，不启动 gateway，不连接 QMT，不读取真实环境变量。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-087 / ADR-088 / ADR-093、`process/changes/CR-020-QMT-WINDOWS-GATEWAY-SERVER-LOGIN-READONLY-QUERY-ADMISSION-2026-06-04.md`、本 Story 卡片。

**输出文件**：`trading/qmt_gateway_cli.py`、`trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`tests/test_cr020_windows_gateway_runtime_admission.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| S 端 CLI | 使用 Typer CLI 作为 Windows 管理入口；只定义命令、参数、错误和 dry admission，不在 CP5 前实现运行 |
| gateway service | 暴露 lifecycle、config、heartbeat、admission 状态合同；公网 bind 默认禁止 |
| config | 只接受安全配置合同和 placeholder；不得读取真实 `.env` |
| admission | `implementation_allowed=false`、`service_start_allowed=false`、`port_bind_allowed=false` 在 CP5 前必须保持 |

**设计约束**：不得改 `pyproject.toml` / `uv.lock`；不得启动 gateway；不得绑定端口；不得连接 QMT / MiniQMT / XtQuant；不得读取、打印、解析或校验真实 `.env`。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR019-S04 | prior-gateway-lifecycle-contract | 可只读引用 CR-019 生命周期合同 | CP5 前不得实现 | CR-020 收敛为只读查询准入，不继承 CR-019 运行授权 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_gateway_cli.py`、`trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`tests/test_cr020_windows_gateway_runtime_admission.py` | 当前 Story 独占 LLD owner |
| shared | `docs/QMT-GATEWAY-INSTALL.md`、`trading/qmt_gateway_contracts.py` | S06 汇总文档；S05 可能共享 contracts |
| forbidden | `pyproject.toml`、`uv.lock`、`.env`、`.env.*`、服务启动、端口绑定、真实 QMT 调用 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S01-T1 | 设计 | `trading/qmt_gateway_cli.py` | 定义 Typer CLI 命令、参数、错误和 dry admission contract |
| CR020-S01-T2 | 设计 | `trading/qmt_gateway_service.py` | 定义 lifecycle / heartbeat / admission 状态接口 |
| CR020-S01-T3 | 设计 | `trading/qmt_gateway_config.py` | 定义安全配置合同、bind 策略和 forbidden env boundary |
| CR020-S01-T4 | 验证设计 | `tests/test_cr020_windows_gateway_runtime_admission.py` | 设计 lifecycle/config/admission 字段和禁止运行测试 |
| CR020-S01-T5 | 门控 | CP5 / CP6 / CP7 | 保持 CP5 前 implementation_allowed=false 和真实操作计数为 0 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_windows_gateway_runtime_admission.py`，但本阶段不执行。

**验证方式**：fixture / static contract / no-runtime 测试；禁止启动服务、绑定端口或调用 QMT。

**依赖环境**：仅使用本仓库代码和 fixture；Windows S 端真实机器验证只允许在 CP7 且获得独立运行授权后执行。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| gateway lifecycle/config contract | 字段覆盖率 100% |
| public bind 默认策略 | allowed 次数为 0 |
| CP5 前启动服务 | fail closed / blocked |
| CP5 前 QMT 调用 | 调用次数为 0 |

## 量化验收标准（acceptance_criteria）

- [ ] gateway lifecycle、config、heartbeat、admission 字段覆盖率为 100%。
- [ ] public bind 默认 allowed 次数为 0。
- [ ] CP5 前 `implementation_allowed=false`、`service_start_allowed=false`、`port_bind_allowed=false`。
- [ ] CP5 前 QMT / MiniQMT / XtQuant 调用次数为 0。
- [ ] 依赖变更次数为 0；`pyproject.toml` / `uv.lock` 不属于输出文件。

## 阻塞说明

CP5 全量 LLD 确认前，本 Story 不得实现。任何 gateway 启动、端口绑定、真实 QMT 连接、依赖变更或真实 `.env` 读取请求都必须回到 meta-po 进行独立门控。
