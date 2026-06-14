请审查：`process/checkpoints/CP5-CR053-MIGRATION-INVENTORY-BATCH-A-LLD-BATCH.md`

自动预检结论：PASS。5 份 CP5 自动预检全部 PASS，阻断项 0，豁免项 0。

Context Capsule：`process/context/CP5-CR053-LLD-CONTEXT.yaml`（read_profile=compact，完整来源见 checklist）

决策收集覆盖：已扫描 7 个来源，发现候选问题 13 个，纳入待决策 4 个；历史 CP2 / CP3 已批准项只作追溯，N/A / 缺失来源 0 个，原因见 checklist 的 Decision Collection Coverage。

本轮待人工决策项：4

如果你回复 approve，表示你接受以下 4 项推荐方案，不表示授权以下 9 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP5-CR053-01 | implementation | 是否接受 CR053-MIGRATION-INVENTORY-BATCH-A 的全量设计证据批次？ | 接受 S01-S04 full-lld 和 S05 technical-note 作为后续 CP6 静态报告实现输入。 | A: 补强某个 Story LLD；B: 回 CP4 重拆 Story。 | 推荐方案覆盖 root map、inventory、path dry-run、backup plan 和 CR058 gate；备选更保守但延迟。 | 允许进入 CP6 静态报告实现；不授权真实迁移。 |
| DQ-CP5-CR053-02 | implementation | 是否接受 S05 保持 technical-note 而非 full-lld？ | 接受，S05 只定义 CR058 输入门禁和 CR053 close gate。 | A: 升级 S05 为 full-lld；B: 延后到 CP8 前补齐。 | 推荐方案匹配低代码治理收敛；升级更强但成本更高。 | 影响 CR058 启动输入追溯。 |
| DQ-CP5-CR053-03 | runtime_authorization | CP5 approve 是否仍不授权真实 NAS / data lake / git / Windows 映射操作？ | 确认不授权，只批准设计证据；后续 CP6 仅可实现静态 Markdown 报告和 guardrail 证据。 | A: 授权 repo-local dry-run scanner；B: 授权 NAS read-only inventory。 | 推荐方案权限最小；备选需独立运行授权和输出边界。 | 防止 CP5 被误读为可 mount、scan、copy、move、push 或改 `.env`。 |
| DQ-CP5-CR053-04 | risk_acceptance | 是否接受当前无阻断 clarification、OPEN / Spike 为 0，可进入 CP6 静态实现准备？ | 接受，`blocks_lld=true` 未回答项为 0。 | A: 先做真实路径 Spike；B: 等 CR058/CR060 授权后再实现。 | 推荐方案先交付可审计静态报告；备选获得更多真实事实但扩大授权或阻塞。 | 只允许静态 / 文档 / 结构验证，不触碰真实环境。 |

不授权项：

| 不授权项 | 当前状态 |
|---|---|
| NAS mount / scan / mkdir / copy / delete / migration | not-authorized |
| 真实目录移动、重命名、删除或 repo-local mechanical move | not-authorized |
| `MARKET_DATA_LAKE_ROOT` 替换或真实 data lake 移动 | not-authorized |
| Windows 交易机 full archive / cold backup / full lake 映射 | not-authorized |
| 读取 `.env`、token、账号、密码、session、cookie、private key | not-authorized |
| provider fetch、lake write、catalog publish | not-authorized |
| QMT / MiniQMT runtime、连接、查询账户或交易动作 | not-authorized |
| git push、tag、远端仓库改名或历史重写 | not-authorized |
| 启动 CR058 / CR060+ 或执行真实迁移 | not-authorized |

请直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```
