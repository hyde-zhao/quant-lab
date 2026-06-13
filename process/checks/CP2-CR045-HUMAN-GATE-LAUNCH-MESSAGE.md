请审查：`process/checkpoints/CP2-CR045-REQUIREMENTS-BASELINE.md`

自动预检结论：PASS，阻断项 0。预检文件：`process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md`

Context Capsule：`process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml`，状态 ready，read_profile=compact。

决策收集覆盖摘要：已扫描 CR045 正式 CR、CP2 context capsule、自动预检结果、上游 CR043/CR044 产物和当前用户启动指令；候选问题 10 个，纳入本轮待人工决策 6 个；无阻断缺失来源。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案，不表示授权下方 13 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP2-CR045-01 | scope | CR045 是否限定为 skeleton / readonly probe 准备？ | 先交付 bridge skeleton、WSL client 合同、fixture/static 测试和 runbook。 | 暂停等待 L3/L4；直接授权真实 readonly probe。 | 防止把“开始实施”误读为真实运行授权。 |
| DQ-CP2-CR045-02 | architecture | WSL 如何连接 Windows 已登录掘金？ | Windows-side broker bridge 为主路线，WSL 只调用 allowlist API。 | WSL 直接持 token；WSL 直连终端 endpoint。 | 决定凭据驻留和网络边界。 |
| DQ-CP2-CR045-03 | security | token/account_id 如何处理？ | 只留在用户 Windows 本地配置；Agent 不读取、不接收、不记录。 | 提供脱敏结构文档；后续 L3 用户手工运行。 | 防止敏感值进入仓库 / 对话 / 日志。 |
| DQ-CP2-CR045-04 | runtime_authorization | 当前是否仍不授权 L3/L4/L5？ | 不启动 bridge runtime，不登录/连接，不查询账户，不下单/撤单。 | 授权 L3 health；授权 L4 readonly。 | 保持真实操作计数为 0。 |
| DQ-CP2-CR045-05 | risk_acceptance | 是否接受 skeleton-ready 作为可能关闭结论？ | 接受 `readonly-bridge-skeleton-ready` / `blocked-by-runtime-authorization`。 | 等 L4 后再启动；取消 CR045。 | 避免误称 real-readonly-verified。 |
| DQ-CP2-CR045-06 | follow_up_tracking | 后续真实 run 如何跟踪？ | L3 bridge health、L4 readonly probe、L5 submit/cancel 分开授权。 | 永远只做 skeleton；直接纳入 L4/L5。 | 可审计但链路更长。 |

不授权项：

| 项 | 状态 |
|---|---|
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
| 让 Agent 接收或记录 token/account_id 原文 | not-authorized |
| 启动 Windows bridge runtime | not-authorized |
| 登录掘金 | not-authorized |
| 连接 Goldminer / broker / 终端 | not-authorized |
| 查询资金 / cash | not-authorized |
| 查询持仓 / position | not-authorized |
| 查询委托 / order | not-authorized |
| 查询成交 / fill / execution report | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |

推荐回复只能使用以下三种之一：

approve

修改: <具体修改点>

reject
