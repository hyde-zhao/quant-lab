---
story_id: "CR020-S02-server-qmt-login-session"
title: "Server QMT 登录与 session ready gate"
story_slug: "server-qmt-login-session"
status: "verified-fixture-static-pending-manual-validation"
priority: "P0"
wave: "CR020-W1-GATEWAY-RUNTIME-SESSION"
depends_on:
  - "CR020-S01-windows-gateway-runtime-admission"
dependency_type:
  - "gateway-runtime-contract"
cp5_batch: "CR020-QMT-GATEWAY-READONLY-BATCH-A"
implementation_allowed: true
real_env_read_allowed: false
credential_output_allowed: false
qmt_login_allowed: false
file_ownership:
  primary:
    - "trading/qmt_gateway_session.py"
    - ".env.example"
    - "tests/test_cr020_server_qmt_login_session.py"
  shared:
    - "trading/qmt_gateway_service.py"
    - "trading/qmt_gateway_config.py"
    - "trading/qmt_redaction.py"
  merge_owner: "CR020-S02-server-qmt-login-session"
  forbidden:
    - ".env"
    - ".env.*"
    - "real credential values"
    - "token/session/password/private key output"
    - "raw account output"
    - "QMT login before CP5/CP6/CP7 runtime gate"
lld_gate:
  required_inputs:
    - "process/HLD.md#36.4"
    - "process/HLD.md#36.9"
    - "process/HLD.md#36.10"
    - "process/ARCHITECTURE-DECISION.md#ADR-088"
    - "process/ARCHITECTURE-DECISION.md#ADR-089"
    - "process/ARCHITECTURE-DECISION.md#ADR-090"
    - "process/stories/CR020-S02-server-qmt-login-session.md"
  status: "confirmed"
dev_gate:
  cp5_required: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  implementation_allowed: true
  dependency_change_allowed: false
  real_env_read_allowed: false
  credential_output_allowed: false
  qmt_login_allowed: false
task_count: 5
created_at: "2026-06-05T07:03:10+08:00"
updated_at: "2026-06-05T09:21:16+08:00"
change_id: "CR-020"
cp6_result: "process/checks/CP6-CR020-S02-server-qmt-login-session-CODING-DONE.md"
cp7_result: "process/checks/CP7-CR020-FIXTURE-STATIC-VERIFICATION-DONE.md"
manual_windows_qmt_validation: "pending-user"
---

# CR020-S02：Server QMT 登录与 session ready gate

## 目标

定义 Windows S 端 QMT login、session state、redacted `credential_ref`、session ready gate、fail-closed 错误和只读查询前置阻断。该 Story 不授权真实登录、不读取真实 `.env`、不输出账号或 session。

## 需求 / HLD / ADR 映射

| 类型 | 映射 |
|---|---|
| 需求基线 | `checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md` D2、D3 |
| HLD | `process/HLD.md` §36.4、§36.9、§36.10、§36.17 |
| ADR | ADR-088、ADR-089、ADR-090 |
| CP3 决策 | DQ-CP3-CR020-02、DQ-CP3-CR020-03 |

## 开发上下文（dev_context）

**背景说明**：CR-020 的真实只读查询必须先满足 S 端登录与 session ready gate。过程产物只能描述凭据引用和 redaction，不得保存、读取、校验或打印真实凭据。

**输入文件**：`process/HLD.md` §36、`process/ARCHITECTURE-DECISION.md` ADR-088..090、`process/stories/CR020-S01-windows-gateway-runtime-admission.md`、本 Story 卡片。

**输出文件**：`trading/qmt_gateway_session.py`、`.env.example`、`tests/test_cr020_server_qmt_login_session.py`。

**接口约定**：

| 合同项 | 要求 |
|---|---|
| credential_ref | 只允许 redacted 引用，不保存真实账号、密码、token、session、交易密码或私钥 |
| session state | 至少覆盖 `not_configured`、`login_pending`、`ready`、`expired`、`blocked`、`error` |
| ready gate | session 非 ready 时 `query_positions` 必须 fail-closed，adapter call 为 0 |
| `.env.example` | 只包含 placeholder 和说明，不包含真实私有路径或凭据样本 |

**设计约束**：不得读取真实 `.env`；不得真实登录 QMT；不得查账户；不得写账户；不得输出 raw account / session / token。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR020-S01 | gateway-runtime-contract | 必须消费 S01 的 runtime/config/admission 合同 | CP5 前不得实现 | session gate 依赖 S 端 gateway runtime 合同 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `trading/qmt_gateway_session.py`、`.env.example`、`tests/test_cr020_server_qmt_login_session.py` | 当前 Story 独占 LLD owner |
| shared | `trading/qmt_gateway_service.py`、`trading/qmt_gateway_config.py`、`trading/qmt_redaction.py` | 与 S01/S04/S05 串行合并 |
| forbidden | `.env`、`.env.*`、真实凭据、真实登录、账户输出 | 禁止 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR020-S02-T1 | 设计 | `trading/qmt_gateway_session.py` | 定义 session state、ready gate 和 blocked reason |
| CR020-S02-T2 | 设计 | `.env.example` | 写 placeholder-only credential_ref 样例 |
| CR020-S02-T3 | 设计 | `tests/test_cr020_server_qmt_login_session.py` | 设计 not_ready、expired、redaction 和 leak tests |
| CR020-S02-T4 | 约束 | `trading/qmt_redaction.py` | 定义 session/account/token/password redaction 输入 |
| CR020-S02-T5 | 门控 | CP5 / CP7 | 真实登录必须等待 CP5 后 LLD、CP6 实现和 CP7 运行授权 |

## 验证上下文（validation_context）

**验证入口**：后续 LLD 可建议 `uv run --python 3.11 pytest -q tests/test_cr020_server_qmt_login_session.py`，但本阶段不执行。

**验证方式**：fixture-only session state 测试、placeholder `.env.example` 扫描、credential leak scan。

**依赖环境**：不依赖真实 QMT、MiniQMT、XtQuant 或 `.env`。

**关键验证场景**：

| 场景 | 预期 |
|---|---|
| session not ready | `query_positions` blocked，adapter call=0 |
| `.env.example` | 只含 placeholder |
| 日志 / error / evidence | 账号、密码、token、session 泄露次数为 0 |
| CP5 前真实登录 | allowed=false |

## 量化验收标准（acceptance_criteria）

- [ ] `.env.example` 真实凭据样本数量为 0。
- [ ] `credential_ref` 输出全部 redacted。
- [ ] session 非 ready 时 `query_positions` adapter call 为 0。
- [ ] 账号、密码、token、session、交易密码、私钥泄露次数为 0。
- [ ] CP5 前真实 QMT login 次数为 0。

## 阻塞说明

CP5 全量 LLD 确认前不得实现；真实登录、真实 `.env` 读取和真实账户输出必须等待后续独立运行授权。
