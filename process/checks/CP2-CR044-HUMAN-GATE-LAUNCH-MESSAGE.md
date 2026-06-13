请审查：`process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md`

自动预检结论：PASS，阻断项 0。预检文件：`process/checks/CP2-CR044-REQUIREMENTS-BASELINE.md`

Context Capsule：`process/context/CP2-CR044-REQUIREMENT-CONTEXT.yaml`，状态 ready，read_profile=compact。

决策收集覆盖摘要：已扫描 CR044 正式 CR、CP2 context capsule、meta-se 交还、自动预检结果和当前用户启动指令；候选问题 11 个，纳入本轮待人工决策 5 个；缺失 STATE pending queue 不阻断，因为本轮从正式 CR 和 handoff 聚合。

本轮待人工决策项：5

如果你回复 approve，表示你接受以下 5 项推荐方案，不表示授权下方 12 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP2-CR044-01 | scope | CR044 是否继续 standard scoped admission？ | 继续 standard admission design。 | 暂停 CR044；关闭为 blocked-by-account-permission。 | 工程化推进但不触碰 runtime。 |
| DQ-CP2-CR044-02 | runtime_authorization | 当前是否仅授权 L1/L2？ | 仅授权 formal orchestration 和 offline engineering design / fixture-only。 | 暂停到 L3+ 授权；只写文档。 | 保持真实操作计数为 0。 |
| DQ-CP2-CR044-03 | security | 凭据和账户材料如何处理？ | 零凭据持有，account_id 也按敏感字段脱敏。 | 提供无真实值结构文档；等待 L3 run manifest。 | 防止敏感值进入仓库 / 对话 / 日志。 |
| DQ-CP2-CR044-04 | risk_acceptance | 是否接受非 simulation-ready 的中间结论？ | 接受 offline-admission-design-ready / blocked-by-account-permission / not-recommended。 | 等待 L3+ 后再继续；不推进。 | 避免误称 simulation-ready。 |
| DQ-CP2-CR044-05 | follow_up_tracking | L3+ 是否逐 run 授权？ | 拆分为逐 run、逐动作授权。 | 本 CR 只设计；关闭为 not-recommended。 | 可审计但链路更长。 |

不授权项：

| 项 | 状态 |
|---|---|
| 读取 `.env`、token、账号、密码、session、cookie、private key | not-authorized |
| 登录掘金 | not-authorized |
| 连接 broker / 终端 | not-authorized |
| 查询资金 / cash | not-authorized |
| 查询持仓 / position | not-authorized |
| 查询委托 / order | not-authorized |
| 查询成交 / fill / execution report | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| 将 `simulation_ready` 或 `live_ready` 写为 true | not-authorized |

推荐回复只能使用以下三种之一：

approve

修改: <具体修改点>

reject
