# CP2 CR051 Human Gate Launch Message

请审查：`process/checkpoints/CP2-CR051-REQUIREMENTS-BASELINE.md`

自动预检结论：PASS

Context Capsule：`process/context/CP2-CR051-REQUIREMENT-CONTEXT.yaml`（read_profile=compact，完整来源见 checklist）

决策收集覆盖：已扫描 7 个来源，发现候选问题 17 个，纳入待决策 5 个；N/A / 缺失来源 0 个。

本轮待人工决策项：5

如果你回复 approve，表示你接受以下 5 项推荐方案，不表示授权以下 14 项禁止操作。

## 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CR051-01 | scope | CR051 是否定位为策略研究生命周期和项目迁移设计 CR？ | 是，只做框架、迁移和治理设计。 | A: 并入多因子 proof cycle；B: 只做文档不设计迁移。 | 推荐方案可支撑后续 CR052+ 和项目迁移；A 过大；B 不满足迁移目标。 | 不产出具体策略或 runtime。 |
| DQ-CR051-02 | architecture | 仓库拓扑是否采用一个主 Git 仓库 + 外部 archive/lake？ | 是，`local_backtest` 保持 canonical 主仓库。 | A: 拆多仓库；B: 单仓库保存全部 artifact。 | 推荐方案迁移成本最低且安全；A 运维成本高；B 污染 Git。 | 需要后续 guardrail。 |
| DQ-CR051-03 | architecture | 是否采用阶段化 Git 归档与清单化机械迁移？ | 是，baseline commit / 可选 tag -> design freeze -> inventory -> mechanical move -> verification。 | A: 一次性搬目录；B: 不迁移结构。 | 推荐方案可回滚；A 难审计；B 不满足目标。 | 后续会产生大文件移动 diff。 |
| DQ-CR051-04 | security | 是否禁止敏感事实和大 artifact 进入 Git？ | 是，Git 只存 schema、docs、summary、redacted fixture、manifest、pointer。 | A: 小型研究输出全留 Git；B: Git LFS。 | 推荐方案最保守；A 需逐项审查；B 增加工具治理。 | 迁移需 inventory 和 forbidden scan。 |
| DQ-CR051-05 | follow_up_tracking | 是否将 CR052..CR056 作为 CR051 后续路线？ | 是，均受 CR051 gate 阻塞。 | A: 只登记 CR052；B: backlog 不编号。 | 推荐方案可追踪；A 覆盖不足；B 可查询性弱。 | 后续 CR 不自动启动。 |

## 不授权项

- CR046 CP7 验证或关闭
- CR047 / CR048 / CR049 启动
- 交付具体交易策略或可交易策略包
- QMT / MiniQMT runtime、连接、传输、导入
- 账户 / 资金 / 持仓 / 委托 / 成交查询
- 下单 / 撤单 / simulation / live
- provider fetch / lake write / catalog publish
- 读取 `.env`、token、account_id、账号、密码、session、cookie、private key
- 外部 archive 实际复制 / 删除 / 搬迁
- 删除仓库历史文件或清空历史过程证据
- git push、删除分支、重写历史
- 创建真实交易 PC package 并传输

请直接回复以下任一整行：

approve

修改: <具体修改点>

reject
