# CR020 Windows S 端手工安装调试手册

本文件是 QMT Gateway 安装说明的安全占位版本，用于本地合同与文档回归测试。当前文档不得启动真实服务，不得写入真实凭据，不得连接 QMT / MiniQMT / XtQuant，不得绑定端口。

## Placeholders

| Placeholder | Meaning |
|---|---|
| `<windows-host>` | Windows 主机引用 |
| `<port>` | 端口占位符 |
| `<config-path>` | 配置文件占位符 |
| `<manual-client-id>` | 手工分配的 client id 引用 |
| `<manual-long-random-secret>` | 手工生成的 secret 引用，不写入真实值 |
| `<qmt-account-ref>` | 脱敏账号引用 |
| `<qmt-miniqmt-userdata-path>` | MiniQMT userdata 路径占位符 |
| `client_secret_ref` | `[REDACTED]` |

## Boundary

当前只允许生成命令结构、配置检查和 heartbeat fixture 摘要。真实 gateway start、port bind、credential read、QMT API call、account query、order submit、order cancel、simulation 或 live 都需要后续单独授权。
