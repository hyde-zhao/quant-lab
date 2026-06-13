# CP3 CR046 Human Gate Launch Message

## 门禁元信息

| 字段 | 内容 |
|---|---|
| Gate | CP3 HLD 人工审查 |
| Change | CR-046 |
| Checklist | `process/checkpoints/CP3-CR046-HLD-REVIEW.md` |
| 自动预检 | `process/checks/CP3-CR046-HLD-CONSISTENCY.md`，结论 `PASS`，阻断项 0 |
| Context Capsule | `process/context/CP3-CR046-DESIGN-CONTEXT.yaml`，状态 `ready` |
| Discussion checkpoint | `process/checks/CP3-CR046-DISCUSSION-CHECKPOINT.json`，结论 `PASS` |
| HLD | `docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md` |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR046.md` |
| 待决策项数量 | 6 |
| 不授权项数量 | 14 |

## 发起消息

请审查：`process/checkpoints/CP3-CR046-HLD-REVIEW.md`

自动预检结论：`PASS`，阻断项 0。Context Capsule：`process/context/CP3-CR046-DESIGN-CONTEXT.yaml`，状态 `ready`。

决策收集覆盖摘要：已扫描 CP2 checkpoint、BLUEPRINT / DOMAIN-MAP / DEPENDENCY-MAP、CR046 HLD、CR046 ADR、CP3 discussion log/checkpoint 和 CP3 自动预检；候选问题 6 项，纳入待人工决策 6 项。CP2 已 approved 的 DQ-CR046-01..06 作为前置事实，不重复发起。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案；不表示授权以下 14 项禁止操作。

待人工决策清单：

| 决策 ID | 类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP3-CR046-01 | architecture | 是否接受新增 FEAT-09 承载 QMT / MiniQMT 双目标策略交付框架？ | 接受；FEAT-05/06 继续只负责 gateway 和交易治理。 | 并入 FEAT-05；并入 FEAT-06。 | 影响蓝图、Story 拆解、后续 CR047/049/051 消费入口。 |
| DQ-CP3-CR046-02 | architecture | 是否接受 StrategyCoreContract 平台无关并禁止导入 QMT / XtQuant / MiniQMT？ | 接受；平台能力只在 target adapter 合同出现。 | core 允许 QMT API；只设计 QMT-only core。 | 影响静态 guardrail、策略包合同和后续策略交付。 |
| DQ-CP3-CR046-03 | implementation | MiniQMT runner 本 CR 是否只做安装设计和 install dry-run 方案？ | 接受；覆盖目录、uv、依赖隔离、配置、日志、kill switch、upgrade/uninstall/rollback。 | 完全不设计 runner；真实安装 / 连接。 | 影响 CR049 实机 install / readonly 验证前置。 |
| DQ-CP3-CR046-04 | risk_acceptance | 是否接受 StrategyValidationEvidence 证据分级，且 CR046 不声明 runtime verified？ | 接受；区分 schema/static/fixture/dry-run plan/runtime verified。 | fixture pass 即 runtime-ready；不设计验证框架。 | 影响 CP7/CP8 声明和用户手册。 |
| DQ-CP3-CR046-05 | follow_up_tracking | 是否接受首个具体策略交付继续后置 CR047？ | 接受；CR046 只交付合同和框架。 | 并入 CR046；暂不追踪。 | 影响 Story 范围和交付预期。 |
| DQ-CP3-CR046-06 | follow_up_tracking | 是否接受研究框架完善继续后置 CR051？ | 接受；CR051 消费 StrategyCoreContract 和 StrategyValidationEvidence。 | 并入 CR046；暂不追踪。 | 影响研究输出元数据、order intents 和准入证据后续完善。 |

不授权项：

| 不授权项 | 状态 |
|---|---|
| 交付具体交易策略或可交易策略包 | 不授权 |
| 执行 QMT 终端 shadow / 模拟盘运行验证 | 不授权 |
| 真实安装 MiniQMT runner | 不授权 |
| 连接 MiniQMT / XtQuant / QMT 外部 Python API | 不授权 |
| 订阅真实行情或启动 runner runtime | 不授权 |
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | 不授权 |
| 查询资金 / cash | 不授权 |
| 查询持仓 / position | 不授权 |
| 查询委托 / order | 不授权 |
| 查询成交 / fill / execution report | 不授权 |
| 下单 / submit order | 不授权 |
| 撤单 / cancel order | 不授权 |
| 启动 simulation/live | 不授权 |
| provider fetch / lake write / catalog publish | 不授权 |

推荐回复只有三种：

approve

修改: <具体修改点>

reject
