# QMT C/S Bridge Runbook

本文是 QMT C/S bridge 的用户边界入口。它汇总 Windows S 端 gateway、Linux / WSL C 端 client、HMAC pairing、endpoint matrix、只读持仓和 simulation runtime 的操作边界。完整 gateway 安装与启动步骤见 [QMT-GATEWAY-INSTALL.md](QMT-GATEWAY-INSTALL.md)，操作者日常步骤见 [USER-MANUAL.md](USER-MANUAL.md)。

本文不是运行授权。任何真实 gateway start、port bind、credential read、QMT / MiniQMT / XtQuant session、account query、order submit、cancel、simulation、live、provider fetch、lake write 或 publish，都必须有逐次授权、stage gate、risk gate、kill switch 和对账证据。

命名说明：历史过程证据中出现的 `stage6` / `Stage 6 admission` 是 CR019 旧阶段命名；当前用户入口统一称为 legacy strategy readiness admission。旧名称只作为审计路径保留。

## 1. Authorization Boundary

Story `verified`、CP5、CP6、CP7、README、USER-MANUAL 和本 runbook 都不是交易许可。Endpoint visible、HMAC / pairing pass、Gateway health pass、Fallback / signed file candidate 可见，也不代表真实交易、broker lake 写入或 QMT operation 已获许可。真实运行必须逐次取得 per-run authorization，并通过 run gate、stage gate、risk gate、reconciliation gate 和 kill switch readiness。

## 2. CP3 Decision Boundary

| Decision | Accepted recommendation | User impact | Not authorization |
|---|---|---|---|
| CP3-CR019-DQ-01 | C/S bridge 使用 Windows gateway + C side client。 | 用户知道 gateway 与 client 分离。 | Not authorization for QMT runtime. |
| CP3-CR019-DQ-02 | HMAC / pairing 作为调用身份边界。 | 用户维护 client id / secret ref。 | Not authorization for account query. |
| CP3-CR019-DQ-03 | Endpoint matrix 固定白名单。 | 用户只调用列出的 endpoint。 | Not authorization for unknown endpoint. |
| CP3-CR019-DQ-04 | Run gate 阻断未授权操作。 | 用户看到 blocked reason。 | Not authorization for submit/cancel. |
| CP3-CR019-DQ-05 | Fallback / signed file candidate 只做 fail-closed。 | 用户可以人工审查候选。 | Not authorization for bypass gateway. |
| CP3-CR019-DQ-06 | Deferred capability register 保持 later-gated。 | 用户知道 minute / Level2 等后续处理。 | Not authorization for provider fetch. |
| CP3-CR019-DQ-07 | 文档出口汇总边界。 | 用户通过 runbook 查边界。 | Not authorization for live. |

## 3. CR019 Story Boundary

| Story | Forbidden operation | Verification entry |
|---|---|---|
| CR019-S01 | dependency change / QMT call | process/checks/CP7-CR019-S01-stage6-admission-gate-VERIFICATION-DONE.md *(legacy evidence path)* |
| CR019-S02 | service start / port bind | process/checks/CP7-CR019-S02-qmt-endpoint-matrix-VERIFICATION-DONE.md |
| CR019-S03 | credential read | process/checks/CP7-CR019-S03-pairing-hmac-auth-VERIFICATION-DONE.md |
| CR019-S04 | gateway launch | process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md |
| CR019-S05 | raw account output | process/checks/CP7-CR019-S05-cside-client-cli-VERIFICATION-DONE.md |
| CR019-S06 | provider fetch | process/checks/CP7-CR019-S06-run-gates-VERIFICATION-DONE.md |
| CR019-S07 | lake / broker lake write | process/checks/CP7-CR019-S07-fallback-VERIFICATION-DONE.md |
| CR019-S08 | publish | process/checks/CP7-CR019-S08-primary-benchmark-policy-VERIFICATION-DONE.md |
| CR019-S09 | simulation/live | process/checks/CP7-CR019-S09-deferred-capabilities-VERIFICATION-DONE.md |
| CR019-S10 | misleading docs | process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md |

## 4. No-Real-Operation Boundary

| Category | Count | Rule |
|---|---:|---|
| dependency change | `0` | no new dependency by this runbook |
| service start | `0` | no gateway start without per-run authorization |
| credential read | `0` | no raw secret / account output |
| QMT / MiniQMT / XtQuant | `0` | no runtime call from docs |
| provider fetch | `0` | no external data fetch |
| lake / broker lake | `0` | no write |
| publish | `0` | no current pointer update |
| simulation/live | `0` | no run from document presence |

## 5. Endpoint Matrix

| Endpoint | Scope | Status |
|---|---|---|
| `POST /qmt/account/positions` | `qmt:positions:read` | only with account_readonly or simulation authorization |
| `POST /qmt/simulation/orders` | `qmt:simulation:submit` | only with simulation submit authorization |
| `POST /qmt/simulation/orders/cancel` | `qmt:simulation:cancel` | only with simulation cancel authorization |

Unknown endpoint returns `endpoint_not_supported`.

## 6. Fallback Boundary

Fallback / signed file candidate is only a manual review candidate. It must not bypass gateway, endpoint matrix, per-run authorization, stage gate, risk gate or reconciliation.

## 7. User Documents

| Document | Purpose |
|---|---|
| `docs/README.md` | New docs navigation. |
| `docs/USER-MANUAL.md` | Operator manual. |
| `docs/components/QMT-GATEWAY.md` | Component view. |
| `docs/scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md` | Scenario view. |

## 8. Verification Contract

| Check | Required |
|---|---|
| Real operation count | `0` |
| `dependency_change` | `0` |
| `credential_read` | `0` |
| `provider_fetch` | `0` |
| `publish` | `0` |
| `simulation_run` | `0` unless separately authorized |

## 9. Gateway Manual Install Debug Guide

### Contract Summary

历史来源：本节继承 CR020 的 gateway 手工安装调试合同；CR020 只作为审计来源，不作为当前用户入口命名。

CR020 的运行边界是 Windows S 端服务 + Linux / WSL C 端签名 client。S 端只在用户手工执行 runtime CLI 时读取 `<windows-runtime-env>`、懒加载 XtQuant、创建 MiniQMT session 并绑定本机 gateway；C 端通过 `QmtClient`、`StdlibQmtRestTransport` 和 `build_runtime_hmac_provider` 构造 HMAC 签名请求。

白名单 endpoint：

| Endpoint | Scope | Contract |
|---|---|---|
| `POST /qmt/account/positions` | `qmt:positions:read` | `query_positions` 只读持仓摘要。 |
| `POST /qmt/simulation/orders` | `qmt:simulation:submit` | 已授权 simulation 订单提交。 |
| `POST /qmt/simulation/orders/cancel` | `qmt:simulation:cancel` | 已授权 simulation 撤单。 |

`query_positions` 必须使用 exact scope `qmt:positions:read`。其他 QMT endpoint 或非 CR020 白名单 endpoint 必须 fail closed，返回 `endpoint_not_supported` 或等价 blocked reason。

### Authorization Boundary

`server-diagnostics` 只输出 public config 和 redacted refs；不连接 gateway endpoint。`serve` 会读取私有 env、尝试登录 MiniQMT / XtQuant 并绑定端口，因此需要 `gateway_start`、`port_bind`、`readonly_runtime` 或对应 simulation 授权。`query-positions` 会访问真实 gateway，因此需要 `account_readonly` 或包含该只读动作的 simulation 授权。

未授权时下列动作均为 `not-authorized`：order、cancel、account_write / 账户写入、provider fetch、lake / broker lake write、publish、simulation、live、small_live 和 scale_up。

### Runtime Commands

Windows S 端诊断：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics \
  --env-file <windows-runtime-env> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

Windows S 端启动：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve \
  --env-file <windows-runtime-env> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

Linux / WSL C 端只读持仓检查：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions \
  --env-file <wsl-client-env> \
  --base-url http://<windows-host>:<port> \
  --run-id <run-id> \
  --request-id <request-id>
```

环境文件中可使用如下占位符，真实值只能保存在用户本机私有文件：

```dotenv
QMT_CLIENT_ID=<manual-client-id>
QMT_CLIENT_SECRET=<manual-long-random-secret>
QMT_CLIENT_SECRET=<same-client-secret-as-windows>
QMT_ACCOUNT_REF=<qmt-account-ref>
QMT_LOGIN_PASSWORD=<qmt-login-password-placeholder>
```

证据和日志只能写 `[REDACTED]`、hash、digest、bucket 和 ref。

### CP7 Readonly Evidence Schema

只读证据必须脱敏，允许字段包括：

| 字段 | 说明 |
|---|---|
| `positions_digest` | 持仓集合摘要，不可反推原始持仓。 |
| `position_count` | 计数或 bucket。 |
| `items_redacted` | 脱敏条目，只含 `instrument_ref` 和数量 bucket。 |
| `redaction_status` | 脱敏状态。 |
| `raw_payload_emitted` | 必须为 `false`。 |

禁止提交 raw positions、HMAC secret、raw signature、未脱敏证券代码、精确持仓数量、账号、cookie、session、private key、交易密码、broker 原始日志和未脱敏 broker order ref。

### Failure Handling

| 状态 | 处理 |
|---|---|
| `session_expired` | 停止策略和新请求，Windows 端重新登录 / 重启 gateway，刷新 session 后重新做只读检查。 |
| `runtime_profile_mismatch` | 停止；确认 gateway 与请求均为 `simulation` profile。 |
| `auth_blocked` / `auth_failed` | 核对 client id、secret、timestamp、nonce 和 scope；不得打印 secret。 |
| `endpoint_not_supported` | 检查 endpoint matrix；不要绕过 gateway 或临时开放未知 endpoint。 |
| unknown order / cancel / reconciliation diff | 进入 manual takeover 或 kill-switch 候选，禁止继续自动 submit。 |
