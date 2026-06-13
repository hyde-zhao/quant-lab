请审查：process/checkpoints/CP2-CR040-REQUIREMENTS-BASELINE.md

自动预检结论：PASS。CR040 的需求范围、QMT 删除路线、新路线规划和不授权边界已通过自动预检。

本轮待人工决策项：2

如果你回复 approve，表示你接受以下 2 项推荐方案：CR040 只确认 QMT 路线删除和新路线规划，paper simulation 代码实现另起 CR041；当前不授权任何 broker、Backtrader、掘金、QMT、账户、凭据、下单或撤单操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR040-01 | scope | 是否接受 CR040 只关闭 / 删除 QMT 路线并规划新路线，而不直接写 paper simulation 代码？ | 接受；CR040 只做路线与状态变更，代码拆到 CR041。 | A: 在 CR040 中直接实现 paper simulation；B: 暂停新路线，仅关闭 QMT。 | 推荐方案门禁清楚、可追溯；A 会混合删除和新增实现，风险高；B 会阻断策略研究向本地模拟盘推进。 | 影响后续 Story 拆分、验证范围和 CR tracking。 | 若用户要求直接实现，则重新生成 CR040 范围与 CP3/CP5；若暂停，则 CR040 关闭为路线删除。 |
| DQ-CP2-CR040-02 | runtime_authorization | 是否授权任何 broker、Backtrader、掘金量化、QMT 或账号相关运行？ | 不授权；当前只允许静态文档、状态同步和本地代码阅读。 | A: 允许安装 Backtrader；B: 允许掘金 SDK Spike 前置安装。 | 推荐方案最小权限且不产生交易副作用；A/B 会引入依赖、凭据和运行边界，需要单独 CR。 | 防止误读为下单、撤单、账户查询或真实仿真授权。 | 未来如需真实运行，必须另起 CR043/CR044 并逐 run 授权。 |

不授权项：

| 项目 | 状态 |
|---|---|
| QMT / MiniQMT / XtQuant 连接 | not-authorized |
| Backtrader 安装或运行 | not-authorized |
| 掘金量化 SDK 安装、登录或连接 | not-authorized |
| 账户、持仓、委托、成交查询 | not-authorized |
| 下单、撤单、simulation/live 运行 | not-authorized |
| 凭据、token、cookie、session 读取 | not-authorized |

approve

修改: <具体修改点>

reject
