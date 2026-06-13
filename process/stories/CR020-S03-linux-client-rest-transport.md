---
story_id: "CR020-S03-linux-client-rest-transport"
title: "Linux C 端 REST transport 与 Python client"
story_slug: "linux-client-rest-transport"
status: "verified-fixture-static-pending-manual-validation"
priority: "P0"
wave: "CR020-W2-CLIENT-AUTH"
depends_on:
  - "CR020-S01-windows-gateway-runtime-admission"
dependency_type:
  - "gateway-rest-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
xtquant_import_allowed_on_linux: false
credential_read_allowed: false
qmt_operation_allowed: false
file_ownership:
  primary:
    - "trading/qmt_client.py"
    - "trading/qmt_client_cli.py"
    - "tests/test_cr020_linux_client_rest_transport.py"
  shared:
    - "trading/qmt_cli.py"
    - "trading/qmt_transport.py"
    - "trading/qmt_gateway_contracts.py"
  merge_owner: "CR020-S03-linux-client-rest-transport"
  forbidden:
    - "XtQuant import on Linux C side"
    - "CLI as business runtime"
    - ".env"
    - "credential values"
    - "gateway start"
    - "real QMT call"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.3"
    - "process/HLD.md#36.5"
    - "process/HLD.md#36.8"
    - "process/ARCHITECTURE-DECISION.md#ADR-087"
    - "process/ARCHITECTURE-DECISION.md#ADR-088"
    - "process/ARCHITECTURE-DECISION.md#ADR-093"
    - "process/stories/CR020-S03-linux-client-rest-transport.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  xtquant_import_allowed_on_linux: false
  credential_read_allowed: false
  qmt_operation_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S03-linux-client-rest-transport-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S03：Linux C 端 REST transport 与 Python client

## 目标

冻结 Linux C 端 typed Python REST client、Typer CLI 验收面、request / response / error contract、timeout / retry 和 CLI 不承载业务运行边界。Linux C 端不得导入 XtQuant，也不得绕过 Python client 直接执行业务调用。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D1、D2 |
| HLD | `process/HLD.md` §36.3、§36.5、§36.8、§36.17 |
| ADR | ADR-087、ADR-088、ADR-093 |
| CP3 决策 | DQ-CP3-CR020-01、DQ-CP3-CR020-02 |

## 开发上下文（dev_context）

**背景说明**：CR-020 的 Linux C 端必须通过 Python REST client 消费 Windows S 端 gateway；Typer CLI 仅作为 smoke / ops / CP7 验收入口，不作为业务运行时。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-087 / ADR-088 / ADR-093、`process/stories/CR020-S01-windows-gateway-runtime-admission.md`、本 Story 卡片。

**输出文件**：`trading/qmt_client.py`、`trading/qmt_client_cli.py`、`tests/test_cr020_linux_client_rest_transport.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| Python REST client | 业务唯一调用入口，返回 typed success / blocked / error |
| Typer CLI | 只复用 client；不得复制业务逻辑 |
| error contract | 覆盖 gateway unavailable、auth fail、session not ready、scope insufficient、timeout |
| retry/timeout | 必须可配置且默认保守；不得自动扩大真实请求 |

**设计约束**：不得在 Linux C 端导入 XtQuant；不得读取 `.env` 或凭据；不得启动 gateway；不得调用真实 QMT。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR020-S01 | gateway-rest-contract | 需要 S01 的 REST / lifecycle / admission 合同 | CP5 前不得实现 | S03 可以与 S04 分轮 LLD，但开发需重新判定文件 owner |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_client.py`、`trading/qmt_client_cli.py`、`tests/test_cr020_linux_client_rest_transport.py` | 当前 Story 独占 LLD owner |
| shared | `trading/qmt_cli.py`、`trading/qmt_transport.py`、`trading/qmt_gateway_contracts.py` | 与 S04/S05 串行合并 |
| forbidden | Linux XtQuant import、CLI 业务运行时、`.env`、真实请求 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S03-T1 | 设计 | `trading/qmt_client.py` | 定义 REST client、typed result 和错误合同 |
| CR020-S03-T2 | 设计 | `trading/qmt_client_cli.py` | 定义 Typer CLI 验收面并复用 client |
| CR020-S03-T3 | 设计 | `tests/test_cr020_linux_client_rest_transport.py` | 设计 timeout、blocked result、CLI reuse、forbidden import tests |
| CR020-S03-T4 | 约束 | `trading/qmt_transport.py` | 规划 transport timeout/retry 和 no-real-call boundary |
| CR020-S03-T5 | 门控 | CP5 / CP7 | CP7 前不得真实连接 gateway 或 QMT |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_linux_client_rest_transport.py`，但本阶段不执行。

**验证方式**：fixture / monkeypatch / static import scan；不得启动真实 gateway。

**依赖环境**：仅本仓库 fixture，不依赖 Windows S 端、QMT、MiniQMT、XtQuant 或 `.env`。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| CLI 调用 | 100% 复用 Python client |
| Linux XtQuant import | 命中次数为 0 |
| gateway unavailable | typed blocked / error |
| CP5 前真实请求 | allowed=false |

## 量化验收标准（acceptance_criteria）

- [ ] Python REST client 是业务调用唯一入口。
- [ ] Typer CLI 业务逻辑复制次数为 0。
- [ ] Linux C 端 XtQuant import 次数为 0。
- [ ] `.env` / credential read 次数为 0。
- [ ] CP5 前 gateway start、真实 QMT call 次数为 0。

## 阻塞说明

CP5 已于 2026-06-05T08:25:46+08:00 由用户批准；本 Story 已完成受控 fixture-only 实现、CP6 PASS 与 CP7 fixture/static PASS，当前等待用户手工执行 Windows/QMT 只读实机验证。任何要求 Linux C 端导入 XtQuant、直接读取凭据或真实调用 gateway / QMT 的需求仍必须回退到 meta-po 门控。

## 实现交接

| 项目 | 内容 |
|---|---|
| CP6 结果 | `process/checks/CP6-CR020-S03-linux-client-rest-transport-CODING-DONE.md`，结论 `PASS` |
| 实现文件 | `trading/qmt_client.py`、`trading/qmt_client_cli.py`、`tests/test_cr020_linux_client_rest_transport.py` |
| 实现摘要 | `QmtClient` 增加可注入 REST transport / auth header provider / config / retry policy；`query_positions` 接入 CR020 typed REST client path；C 端 optional Typer CLI 只委托 `QmtClient`；Typer 缺失 fail-closed。 |
| 验证结果 | S03 专项 `9 passed in 0.08s`；CR019+CR020 组合回归 `16 passed in 0.14s`；py_compile 退出码 0。 |
| 安全边界 | 未修改依赖；未读取 `.env`；未启动 gateway；未绑定端口；未连接 QMT / MiniQMT / XtQuant；未执行真实 REST 请求；未发单 / 账户写入 / provider / lake / publish。 |
| 下一步 | 等待用户按手册执行真实 Windows/QMT `query_positions` 只读验证；该验证前不得关闭 CR-020 或授权交易 / 账户写入。 |
