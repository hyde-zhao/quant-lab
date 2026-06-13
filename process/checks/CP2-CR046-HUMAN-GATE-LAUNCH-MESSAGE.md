请审查：`process/checkpoints/CP2-CR046-REQUIREMENTS-BASELINE.md`

自动预检结论：PASS，阻断项 0。预检文件：`process/checks/CP2-CR046-REQUIREMENTS-BASELINE.md`

Context Capsule：`process/context/CP2-CR046-REQUIREMENT-CONTEXT.yaml`，状态 ready，read_profile=compact。

决策收集覆盖摘要：已扫描 CR046 正式 CR、CP2 context capsule、discussion log / checkpoint、自动预检结果、`process/USE-CASES.md`、`process/REQUIREMENTS.md` 和当前用户指令；候选问题 13 个，纳入本轮待人工决策 6 个；无阻断缺失来源。当前仓库产品基线沿用 legacy `process/*`，未静默新建 `docs/product/` 双真相源。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案，不表示授权下方 14 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CR046-01 | scope | CR046 是否限定为 QMT + MiniQMT 双目标框架，而不是具体策略交付？ | 是，本轮先交付框架和验证框架。 | 交付一个 QMT 策略包；直接进入 MiniQMT runner 实现。 | 推荐方案避免双目标不一致；备选会扩大范围或被权限阻塞。 | 本轮不会产生可交易具体策略。 |
| DQ-CR046-02 | architecture | 后续研究策略是否同时支持 QMT 终端和 MiniQMT runner？ | 是，双目标为标准交付合同。 | 只支持 QMT；只支持 MiniQMT。 | 推荐方案兼顾当前 QMT 和未来 runner；备选更简单但迁移成本高或与权限事实冲突。 | 框架复杂度更高，但可避免后续目标不一致。 |
| DQ-CR046-03 | implementation | MiniQMT runner 组件安装是否纳入本 CR？ | 是，纳入安装设计和 dry-run 方案，不执行真实安装 / 连接。 | 完全不纳入；直接实现可运行 runner。 | 推荐方案冻结安装规范；备选会留下缺口或越过权限门禁。 | 冻结目录、uv、依赖、配置和日志规范，但不等于 runtime 授权。 |
| DQ-CR046-04 | security | 本 CR 是否继续禁止真实运行、账户查询、submit/cancel、live 和 MiniQMT 连接？ | 是，仅框架 / 验证框架设计 / fixture 设计。 | 授权 QMT shadow；授权只读连接；授权最小模拟盘提交。 | 推荐方案风险最低；备选都需要逐 run 授权、策略包和脱敏证据。 | 无真实运行证据，真实动作需后续 runtime_authorization。 |
| DQ-CR046-05 | follow_up_tracking | 首个具体策略交付是否作为 CR047 候选进入后续台账？ | 是，CR047-candidate。 | 在 CR046 内交付首个策略；暂不登记。 | 推荐方案保持职责分离；备选会扩大当前 CR 或丢失追踪。 | 保持框架与策略交付分离。 |
| DQ-CR046-06 | follow_up_tracking | 研究框架完善是否作为 CR051 候选进入后续台账？ | 是，CR051-candidate。 | 并入 CR046；暂不登记。 | 推荐方案先定交易框架再反向约束研究；备选会让当前 CR 过大或丢失缺口。 | 先冻结交易交付框架，再反向完善研究框架。 |

不授权项：

| 项 | 状态 |
|---|---|
| 交付具体交易策略或可交易策略包 | not-authorized |
| 执行 QMT 终端 shadow / 模拟盘运行验证 | not-authorized |
| 真实安装 MiniQMT runner | not-authorized |
| 连接 MiniQMT / XtQuant / QMT 外部 Python API | not-authorized |
| 订阅真实行情或启动 runner runtime | not-authorized |
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
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
