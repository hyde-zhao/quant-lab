# QMT Gateway 手工安装与运行手册

本文件是 Windows S 端 QMT gateway 的正式用户文档入口，覆盖环境文件、启动、检查、停止和常见故障。它只说明在用户已经取得逐次授权后的手工操作方式，不保存真实账号、密码、token、HMAC secret、session、原始持仓或原始订单回执。

## CR020 Windows S 端手工安装调试手册

### CR020 Contract Summary

历史来源：本节继承 CR020 的 Windows S 端手工安装调试合同；CR020 只作为审计来源，不作为当前用户入口命名。

QMT gateway 采用 C/S 边界：Windows S 端运行 MiniQMT / XtQuant 和本地 HTTP gateway；Linux / WSL C 端只通过 HMAC 签名请求访问白名单 endpoint。当前正式白名单包括：

| Endpoint | Scope | 用途 |
|---|---|---|
| `POST /qmt/account/positions` | `qmt:positions:read` | 只读持仓摘要，输出 digest、bucket 和 redacted refs。 |
| `POST /qmt/simulation/orders` | `qmt:simulation:submit` | 已授权 simulation run 的模拟盘提交。 |
| `POST /qmt/simulation/orders/cancel` | `qmt:simulation:cancel` | 已授权 simulation run 的模拟盘撤单。 |

其他 QMT endpoint 或非 CR020 白名单 endpoint 必须返回 `endpoint_not_supported` 或等价 blocked 结果。`query_positions` 只能使用 exact scope `qmt:positions:read`；scope 不能模糊匹配。

### Authorization Boundary

启动 gateway、绑定端口、读取本机 env 文件、连接 MiniQMT / XtQuant、查询只读持仓、提交 simulation 订单和撤单，都是需要逐次授权的运行时动作。授权必须写明 `action_scope`、时间窗口、环境引用、凭据策略、脱敏规则、回滚计划、审计引用、允许命令和禁止命令。

授权 simulation 不等于授权 `small_live` 或 `live`。本文档不授权真实 live 交易、不授权资金放大、不授权读取或落盘原始敏感信息。

未取得逐次授权时，不得启动真实服务，不得写入真实凭据。

### No-Authorization Table

| 动作 | 未授权时状态 | 说明 |
|---|---|---|
| gateway start / serve / port bind | `not-authorized` | 不启动服务，不绑定端口。 |
| QMT / MiniQMT / XtQuant login | `not-authorized` | 不读取凭据，不创建 session。 |
| query positions | `not-authorized` | 不查询账户，不输出 raw positions。 |
| order submit | `not-authorized` | 不提交 order。 |
| cancel | `not-authorized` | 不撤单。 |
| account_write / 账户写入 | `not-authorized` | 不改单、不写账户状态。 |
| provider fetch | `not-authorized` | 不抓取外部数据。 |
| lake / broker lake write | `not-authorized` | 不写数据湖或 broker lake。 |
| publish | `not-authorized` | 不更新 current pointer。 |
| simulation | `not-authorized` | 未获逐次 simulation 授权时不运行。 |
| live / small_live | `not-authorized` | 当前文档不提供 live 或 small_live 授权。 |

### Windows S 端环境文件

建议在 Windows 本机私有目录维护 runtime env，例如 `<windows-runtime-env>`。不要提交该文件，不要把真实值复制到 issue、README、process 证据或聊天记录。

```dotenv
QMT_GATEWAY_HOST=<windows-host>
QMT_GATEWAY_PORT=<port>
QMT_GATEWAY_ALLOWED_SOURCE=<wsl-client-cidr>
QMT_CLIENT_ID=<manual-client-id>
QMT_CLIENT_SECRET=<manual-long-random-secret>
QMT_XTQUANT_SITE_PACKAGES=<xtquant-site-packages-path>
QMT_MINIQMT_PATH=<qmt-miniqmt-userdata-path>
QMT_ACCOUNT_REF=<qmt-account-ref>
QMT_ACCOUNT_TYPE=STOCK
QMT_RUNTIME_MODE=simulation
QMT_ACCOUNT_KIND=simulation
QMT_RUNTIME_PROFILE=cr138-simulation
QMT_RUNTIME_REF=<runtime-authorization-ref>
QMT_SESSION_TTL_SECONDS=<session-ttl-seconds>
```

| Placeholder | Meaning |
|---|---|
| `<windows-host>` | Windows 主机地址或本机绑定地址。 |
| `<port>` | gateway 端口，占位示例通常是 `18765`。 |
| `<config-path>` | gateway 配置文件路径占位符。 |
| `<wsl-client-cidr>` | 允许访问 gateway 的 C 端来源网段。 |
| `<manual-client-id>` | 手工分配的 client id 引用。 |
| `<manual-long-random-secret>` | 手工生成的 HMAC secret 引用，不写入真实值。 |
| `<xtquant-site-packages-path>` | Windows XtQuant Python 包路径。 |
| `<qmt-miniqmt-userdata-path>` | MiniQMT userdata 路径占位符。 |
| `<qmt-account-ref>` | 脱敏账号引用。 |
| `<runtime-authorization-ref>` | 本次逐次授权引用。 |
| `<session-ttl-seconds>` | session 过期窗口。 |
| `client_secret_ref` | `[REDACTED]` |

如需兼容旧 CR020 session 文档，可在同一私有 env 中保留以下占位字段，但不得把真实值写入仓库：

```dotenv
QMT_CREDENTIAL_REF=<qmt-credential-ref-placeholder>
QMT_LOGIN_ACCOUNT=<qmt-login-account-placeholder>
QMT_LOGIN_PASSWORD=<qmt-login-password-placeholder>
QMT_SESSION_READY_TIMEOUT_SECONDS=<session-ready-timeout-seconds-placeholder>
```

### Linux / WSL C 端环境文件

C 端 env 只保存 gateway 地址和同一组 HMAC client 引用，例如 `<wsl-client-env>`：

```dotenv
QMT_GATEWAY_HOST=<windows-host>
QMT_GATEWAY_PORT=<port>
QMT_CLIENT_ID=<manual-client-id>
QMT_CLIENT_SECRET=<same-client-secret-as-windows>
QMT_RUNTIME_REF=<runtime-authorization-ref>
```

`<same-client-secret-as-windows>` 只表示两端内存中使用同一 HMAC secret；文档、证据和日志只能显示 `[REDACTED]`。

### 启动前诊断

在 Windows S 端先运行诊断，确认 public config 只输出 hash、ref 和 `[REDACTED]`：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics \
  --env-file <windows-runtime-env> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

诊断结果应包含 `secrets_redacted=true`、`runtime_mode=simulation`、`account_kind=simulation`、`runtime_profile=cr138-simulation`。如果 profile 不是 simulation，停止，不要启动 gateway。

### 启动 gateway

在 Windows S 端、已登录 MiniQMT 且逐次授权仍有效时执行：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve \
  --env-file <windows-runtime-env> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

该命令是阻塞式前台进程。启动后会先尝试创建 XtQuant session；如果返回 `credential_not_configured`、`qmt_runtime_unavailable`、`login_failed` 或 `session_expired`，不要继续跑策略。

### 检查 gateway

在 C 端或允许来源机器上检查 health 和 capabilities：

```bash
curl -sS --max-time 5 http://<windows-host>:<port>/qmt/health
curl -sS --max-time 5 http://<windows-host>:<port>/qmt/capabilities
```

再做只读持仓 smoke：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions \
  --env-file <wsl-client-env> \
  --base-url http://<windows-host>:<port> \
  --run-id <run-id> \
  --request-id <request-id>
```

只读返回只能用于脱敏摘要校验。允许保存的字段是 `positions_digest`、`position_count` / bucket、`items_redacted`、`instrument_ref`、`redaction_status` 和 blocked reason；禁止提交 raw positions、HMAC secret、raw signature、未脱敏证券代码、精确持仓数量、账户号、session 或 broker 原始日志。

### 停止 gateway

当前没有单独的 stop endpoint。停止方式是：

1. 在运行 `serve` 的终端按 `Ctrl+C`。
2. 或关闭该终端。
3. 或在 Windows 进程管理器中结束对应 Python 进程。

停止后再次访问 `/qmt/health` 应不可达。若是因为 `session_expired` 停止，应先在 Windows 端重新确认 MiniQMT 登录和 session，再重新执行 `server-diagnostics` 和 `serve`。

### CP7 Readonly Evidence Schema

只读证据最小字段如下：

```json
{
  "schema_version": "cr020-s05-query-positions-readonly-v1",
  "status": "allowed_or_blocked",
  "positions_digest": "<digest>",
  "position_count": "<count-or-bucket>",
  "items_redacted": [
    {
      "instrument_ref": "<instrument-ref>",
      "quantity_bucket": "<bucket>"
    }
  ],
  "raw_payload_emitted": false,
  "redaction_status": "pass",
  "client_secret_ref": "[REDACTED]"
}
```

禁止提交 raw positions、HMAC secret、raw signature、未脱敏证券代码、精确持仓数量、账号、cookie、session、private key、交易密码、真实 broker root 和未脱敏 broker order ref。

### 常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| `credential_not_configured` | env 缺少 MiniQMT 路径或账号引用 | 补齐私有 env，占位值不要写进仓库。 |
| `qmt_runtime_unavailable` | XtQuant import、连接或 MiniQMT 运行失败 | 检查 Windows 端 MiniQMT 和 `QMT_XTQUANT_SITE_PACKAGES`。 |
| `session_expired` | gateway session 过期 | 停止策略，重新登录 / 重启 gateway，刷新 session 后重跑只读检查。 |
| `runtime_profile_mismatch` | gateway 或请求不是 simulation profile | 停止；确认 `QMT_RUNTIME_MODE=simulation`、`QMT_ACCOUNT_KIND=simulation` 和 expected profile 一致。 |
| `auth_blocked` / `auth_failed` | HMAC client、secret、timestamp、nonce 或 scope 不匹配 | 重新核对两端 env 和授权 scope；不要打印 secret。 |
| `endpoint_not_supported` | 请求了非白名单 endpoint | 回到 endpoint matrix；不要临时开放未知 endpoint。 |
