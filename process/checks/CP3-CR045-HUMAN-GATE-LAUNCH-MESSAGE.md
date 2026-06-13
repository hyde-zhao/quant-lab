请审查：`process/checkpoints/CP3-CR045-HLD-REVIEW.md`

自动预检结论：PASS，阻断项 0。预检文件：`process/checks/CP3-CR045-HLD-CONSISTENCY.md`

Context Capsule：`process/context/CP3-CR045-DESIGN-CONTEXT.yaml`，状态 ready，read_profile=compact。

决策收集覆盖摘要：已扫描 CP2 checkpoint、CR045 HLD、CR045 ADR、CP3 discussion log、CP3 discussion checkpoint、meta-se handoff 和自动预检结果；候选问题 23 个，纳入本轮待人工决策 6 个；CP2 的 6 项已 approved，本轮不重复发起；自动预检阻断项 0。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案，不表示授权下方 10 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP3-CR045-01 | architecture | WSL / 未来 Linux research server 如何接入 Windows Goldminer 环境？ | Windows-side bridge skeleton + WSL / Linux allowlist client；Linux 侧只做研究、回测、组合生成、order intent 和 client 调用。 | WSL / Linux direct SDK；WSL / Linux direct terminal endpoint Spike；暂停 CR045。 | 决定拓扑、依赖方向、安全边界和未来 Linux 研究服务器部署边界。 |
| DQ-CP3-CR045-02 | architecture | Bridge API 边界如何限定？ | L2 仅 health、capabilities、readonly probe skeleton，真实 readonly 默认 blocked。 | 真实查询 endpoint disabled；health-only。 | 影响 API、Story、QA 和 runbook。 |
| DQ-CP3-CR045-03 | security | token/account_id 如何驻留和脱敏？ | 仅未来用户 Windows 本地持有；Agent/WSL/Linux server/仓库/对话不读取不记录。 | 用户提供无真实值结构文档；WSL / Linux 持有凭据。 | 防止敏感值泄漏和误运行。 |
| DQ-CP3-CR045-04 | runtime_authorization | kill switch 和 allowlist 默认状态？ | 默认 hard-off；无 per-run 授权或 action 不在 allowlist 则 blocked。 | 仅日志警告不阻断；CP3 一次性授权 L4。 | 影响失败路径、验证和未来 runtime。 |
| DQ-CP3-CR045-05 | risk_acceptance | 是否接受 CR045 可能只关闭为 skeleton-ready？ | 接受 `readonly-bridge-skeleton-ready` 或 `blocked-by-runtime-authorization`，不宣称 real-readonly-verified。 | 等 L4 后再推进；取消 CR045。 | 影响 CP8 预期和用户验收。 |
| DQ-CP3-CR045-06 | implementation | Story / LLD 批次如何划分？ | S01-S05 full-lld，S06 technical-note/条件升 full-lld，CP3 后再进入 story-planning。 | 只做 S01-S03；加入真实 L4/L5 Story。 | 决定 CP5 设计证据范围。 |

不授权项：

| 项 | 状态 |
|---|---|
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
| 启动 Windows bridge runtime | not-authorized |
| 登录 / 连接 Goldminer 或 broker | not-authorized |
| 查询账户 / cash / funds | not-authorized |
| 查询持仓 / position | not-authorized |
| 查询委托 / order | not-authorized |
| 查询成交 / fill / execution report | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live、provider fetch、lake write、catalog publish | not-authorized |

推荐回复只能使用以下三种之一：

approve

修改: <具体修改点>

reject
