# CP3 CR051 Human Gate Launch Message

请审查：`process/checkpoints/CP3-CR051-HLD-REVIEW.md`

自动预检结论：PASS

Context Capsule：`process/context/CP3-CR051-DESIGN-CONTEXT.yaml`（read_profile=compact，完整来源见 checklist）

决策收集覆盖：已扫描 6 个来源，发现候选问题 24 个，纳入待决策 6 个；N/A / 缺失来源 0 个。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案，不表示授权任何真实操作。

## 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP3-CR051-01 | architecture | 是否确认单主仓库 + 外部 archive/lake/broker archive？ | 是，`quant-lab` 为未来主仓库名，当前 `local_backtest` 保留为 legacy alias。 | A: 拆多仓库；B: Git 全量保存。 | 推荐方案迁移成本最低；拆仓库过早；Git 全量保存风险高。 | 需要 path / forbidden content guardrail。 |
| DQ-CP3-CR051-02 | architecture | 是否确认基于当前硬件的冷热分层？ | 是，研究主机 2T SSD active workspace，NAS 512G SSD 热层，NAS 4T RAID warm archive，NAS 14T cold archive，交易主机 512G package consumer。 | A: 全部放研究主机；B: 全部放 14T；C: 交易主机完整 archive。 | 推荐方案兼顾性能、容量和安全。 | 路径需配置化，不写死私有挂载。 |
| DQ-CP3-CR051-03 | security | 是否确认交易主机不是研究环境？ | 是，只消费 package / checksum / manifest / docs。 | A: 完整 clone；B: 挂载 research archive。 | 推荐方案权限最小。 | 后续 package 交付必须有 checksum 和 gate。 |
| DQ-CP3-CR051-04 | implementation | 是否确认迁移采用归档点 + inventory + mechanical move + verification？ | 是，机械移动和语义修改分提交。 | A: 一次性迁移；B: 只改文档。 | 推荐方案可审计可回滚。 | 后续会有路径引用修正。 |
| DQ-CP3-CR051-05 | runtime_authorization | 是否确认 CP3 不授权真实操作？ | 是。 | A: 同时授权 NAS inventory；B: 同时授权 archive migration。 | 推荐方案保持设计门和执行门分离。 | inventory / migration 需后续单独授权。 |
| DQ-CP3-CR051-06 | architecture | 是否确认项目正式名称从 `local_backtest` 迁移为 `quant-lab`？ | 是，`quant-lab` 为正式名，`local_backtest` 为 legacy alias。 | A: 继续使用 `local_backtest`；B: 使用更长名称；C: 立即全量替换历史文件旧名。 | 推荐方案简洁且不再局限于 backtest；全量替换历史文件会污染审计链。 | 后续需迁移 README、USER-MANUAL、`pyproject.toml`、路径变量和 Windows 默认路径；历史 `process/` 不批量替换。 |

## 不授权项

- NAS mount / scan / copy / delete / migration execution
- provider fetch / lake write / catalog publish
- QMT / MiniQMT runtime、传输、导入、连接
- 账户 / 资金 / 持仓 / 委托 / 成交查询
- 下单 / 撤单 / simulation / live
- 凭据、token、account_id、账号、密码、session、cookie、private key 读取或记录
- git push、删除分支、重写历史

请直接回复以下任一整行：

approve

修改: <具体修改点>

reject
