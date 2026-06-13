# CP8 CR045 Human Gate Launch Message

请审查：`process/checkpoints/CP8-CR045-DELIVERY-READINESS.md`

自动预检结论：PASS

上下文胶囊：`process/release/RELEASE-CONTEXT-CR045.yaml`（read_profile=compact，release_decision=READY_WITH_RISK，完整来源见 checklist）

本轮待人工决策项：5

决策收集覆盖：已扫描 6 个来源，发现候选问题 13 个，纳入待决策 5 个；N/A / 缺失来源 0 个，原因见 checklist 的 Decision Collection Coverage。

如果你回复 approve，表示你接受以下 5 项推荐方案，不表示授权以下 10 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP8-CR045-01 | risk_acceptance | 是否接受 CR045 以 `READY_WITH_RISK / readonly-bridge-skeleton-ready` 关闭？ | 接受，关闭当前 L2 skeleton 交付，不宣称 real-readonly-verified。 | A: NOT_READY 等待 L3/L4；B: 回 CP7 补全全局矩阵。 | 推荐方案闭环已完成资产；备选会扩大范围或阻塞。 | 防止 L2 被误读为真实 runtime。 |
| DQ-CP8-CR045-02 | runtime_authorization | CP8 approve 是否授权 L3 Windows bridge runtime？ | 不授权。 | A: 另起 L3 gate；B: 关闭为 blocked-by-runtime-authorization。 | 推荐方案权限最小；A 需独立 manifest/时间窗/kill switch。 | 防止启动 bridge 或连接掘金。 |
| DQ-CP8-CR045-03 | runtime_authorization | CP8 approve 是否授权 L4 real readonly probe？ | 不授权。 | A: L3 后另起 L4 gate；B: 永久取消 readonly probe。 | 推荐方案保留入口但不越权。 | 防止查询真实账户数据。 |
| DQ-CP8-CR045-04 | runtime_authorization | CP8 approve 是否授权 L5 submit/cancel/simulation/live？ | 不授权。 | A: 新建 L5 高风险 CR；B: 永久禁止 L5。 | 推荐方案避免交易风险。 | 防止下单、撤单、simulation/live。 |
| DQ-CP8-CR045-05 | follow_up_tracking | 如何处理全局 TEST-MATRIX / TEST-STRATEGY 缺失和后续 L3/L4/L5？ | 接受 scoped evidence；后续作为候选治理 / runtime gate。 | A: 立即补全全局矩阵；B: 保持 CR045 active 等待 L3/L4。 | 推荐方案让已完成交付闭环；备选扩大范围或阻塞。 | 影响后续治理和 CR045 关闭速度。 |

不授权项：

- 读取 `.env`、token、account_id、账号、密码、session、cookie、private key
- 启动 Windows bridge runtime
- 登录 / 连接 Goldminer 或 broker
- 查询账户 / cash / funds
- 查询持仓 / position
- 查询委托 / order
- 查询成交 / fill / execution report
- 下单 / submit order
- 撤单 / cancel order
- 启动 simulation/live、provider fetch、lake write、catalog publish

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受上表全部推荐方案；如需调整，请用 `修改: <具体修改点>` 指明决策 ID 和修改内容。

审查后请直接回复以下任一整行：

approve

修改: <具体修改点>

reject
