# 组件说明：QMT Gateway

QMT gateway 组件负责 Windows S 端 MiniQMT / XtQuant session 与 Linux / WSL C 端签名 client 之间的受控通信。详细安装和命令见 [../QMT-GATEWAY-INSTALL.md](../QMT-GATEWAY-INSTALL.md)。

## 1. 组件边界

| 子组件 | 责任 |
|---|---|
| Windows S 端 env | 保存 gateway host、port、client id、secret、XtQuant 路径、模拟盘账号引用和 runtime profile。 |
| `server-diagnostics` | 输出脱敏 public config，不保存 secret。 |
| `serve` | 用户逐次授权后启动前台 gateway。 |
| health / capabilities | 检查 gateway 是否可达和 endpoint matrix。 |
| `query-positions` | 查询只读持仓摘要，输出 digest / bucket / refs。 |
| simulation submit/cancel endpoint | 仅在 simulation 授权、stage/risk gate 通过后由 runner 调用。 |

## 2. 必要环境字段

| 字段 | 要求 |
|---|---|
| `QMT_RUNTIME_MODE` | 必须是 `simulation` 才允许当前 runner 使用。 |
| `QMT_ACCOUNT_KIND` | 必须是 `simulation`。 |
| `QMT_RUNTIME_PROFILE` | 当前推荐 `cr138-simulation`。 |
| `QMT_CLIENT_SECRET` | 只保存在本机 env，证据只显示 `[REDACTED]`。 |
| `QMT_RUNTIME_REF` | 逐次授权引用。 |

## 3. 检查清单

| 检查 | 通过标准 | 失败处理 |
|---|---|---|
| 诊断 | public config 脱敏，profile 为 simulation。 | 停止，不启动 gateway。 |
| health | `/qmt/health` 可达。 | 停止 runner。 |
| capabilities | endpoint matrix 符合预期。 | 不调用未知 endpoint。 |
| positions | 只返回脱敏摘要。 | redaction fail 时不保存证据。 |
| session | 未过期。 | `session_expired` 时重启 / 重新登录。 |
