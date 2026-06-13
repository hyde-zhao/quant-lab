# CP5 CR-020 Human Gate Launch Message

请审查：checkpoints/CP5-CR020-QMT-GATEWAY-READONLY-LLD-BATCH.md

自动预检结论：PASS。CP4 自动预检 PASS；CR020-S01..S06 六份 LLD 已生成；六份 Story 级 CP5 自动预检均 PASS；阻断 clarification / OPEN 数量为 0。

本轮待人工决策项：6

如果你回复 approve，表示你接受以下 6 项推荐方案，不表示授权以下 12 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP5-CR020-01 | implementation | 是否批准 CR020-S01..S06 六份 LLD 作为后续受控实现输入。 | 批准全部 6 份 LLD；CP5 通过后允许进入 story-execution，并按 S01 -> S02/S03 -> S04 -> S05 -> S06 的依赖 / 文件 owner 顺序调度实现。 | A. 只批准 S01..S04，S05/S06 返工后再确认；B. 全部 LLD 返工后重新 CP5。 | 推荐方案一次冻结端到端合同；分批更保守但拖慢跨 Story 契约；全部返工最保守但重复消耗已通过预检。 | 影响 CR-020 能否进入实现、后续 dev_gate、文件合并顺序和 CP6/CP7 验证。 |
| DQ-CP5-CR020-02 | runtime_authorization | CP5 通过后授权边界是什么，是否允许真实运行或真实 QMT 连接。 | CP5 仅授权受控代码 / 文档实现和 fixture / static 验证输入；继续禁止 gateway 启动、端口绑定、真实 `.env` 读取、QMT 连接、真实 `query_positions`、交易、账户写入、simulation/live、provider/lake/publish。 | A. 仅批准 LLD，不进入实现；B. 同时授权 Windows gateway / QMT readonly smoke。 | 推荐方案推进实现且权限最小；真实 smoke 暴露事实更早但需要主机、端口、凭据、日志脱敏和回滚授权。 | 影响安全、运行权限、凭据边界和 CP6/CP7 调度。 |
| DQ-CP5-CR020-03 | implementation | 如何处理 Typer CLI 依赖尚未落地的问题。 | 接受 command matrix + optional Typer adapter；Typer 缺失时 fail-closed 为 `typer_dependency_missing`；本 CP5 不改 `pyproject.toml` / `uv.lock`。 | A. 本 CP5 同时授权修改依赖加入 Typer；B. 切换 argparse。 | 推荐方案符合依赖最小化；直接加依赖更完整但扩大变更面；argparse 零依赖但偏离已确认口径。 | 影响 S/C CLI、文档命令、安装说明和 CP7 验证。 |
| DQ-CP5-CR020-04 | risk_acceptance | 如何接受 QMT login/session 与 query_positions 原始字段仍需 CP7 Windows 实机确认的不确定性。 | 接受 adapter protocol + fixture-only gate；真实 API、ready/expiry 信号和 raw payload 字段在 CP7 Windows 实机只读授权下确认。 | A. CP5 前先做 Windows 实机 Spike；B. 收窄为 health/login only。 | 推荐方案保持无真实运行边界且推进实现；Spike 更早验证但需要运行授权；health/login only 不满足查询目标。 | 影响 S02 session adapter、S05 response schema、CP7 验证计划和回修成本。 |
| DQ-CP5-CR020-05 | security | 是否接受 nonce replay store 第一版为进程内 TTL，不覆盖多进程持久防重放。 | 接受单 gateway 进程内 TTL replay store；多进程 / 多实例 gateway 或更强防重放需求另起 CR 或回到 CP5 修改 LLD。 | A. 本轮引入持久 nonce store；B. 仅校验 timestamp 不记录 nonce。 | 推荐方案简单且不新增依赖；持久 store 更强但复杂；只校验 timestamp replay 防护不足。 | 影响 HMAC 安全、并发模型、测试和未来多实例部署。 |
| DQ-CP5-CR020-06 | risk_acceptance | 是否接受 S06 文档 / CP7 evidence 边界：文档只描述运行前置和验收边界，不形成运行授权。 | 文档只写 placeholder、redaction、no-real-operation、不授权表和 CP7 evidence schema；CP7 evidence 仅允许 `query_positions` / `qmt:positions:read` 脱敏只读证据，真实运行授权后续独立发起。 | A. 文档只写离线实现，不写 CP7 实机章节；B. 文档同时写入真实运行命令和授权模板。 | 推荐方案让用户准备操作步骤但不越权；离线文档缺少验收衔接；真实命令更完整但容易被误读为已授权。 | 影响 docs、CP7 证据、用户操作安全和审计。 |

不授权项：

- 不授权启动 gateway、绑定端口、打开 socket 或启动 Windows 服务进程。
- 不授权读取真实 `.env`、`.env.*`、账号、密码、token、session、交易密码、私钥或任何未脱敏凭据。
- 不授权连接 QMT / MiniQMT / XtQuant，或执行真实 `query_positions`。
- 不授权发单、撤单、改单、账户写入或任何 broker 写操作。
- 不授权 simulation、live-readonly、small-live、scale-up 或任何真实交易准入。
- 不授权 provider fetch、真实联网补数、真实 lake write、broker lake write、catalog publish / current pointer publish 或 reports overwrite。
- 不授权把 `query_positions` 以外的真实 QMT 查询接口纳入默认白名单。
- 不授权把 CP5 通过解释为 CP6 / CP7 / CP8 自动通过或 CR 自动关闭。
- 不授权把真实账号、密码、token、session、交易密码、私钥写入 Git、对话、日志、检查点、memory 或入库文档。
- 不授权修改 `pyproject.toml` / `uv.lock` 或安装依赖；依赖变更仍需后续明确门禁。
- 不授权把 C 端 Typer CLI 配对 / 验收命令误当成实际业务 runtime，业务 runtime 仍是 Python REST client。
- 不授权启动 CR-021..CR-024 或扩大到 simulation / live 路线。

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受上表全部推荐方案；如需调整，请用 `修改: <具体修改点>` 指明决策 ID 和修改内容。

approve

修改: <具体修改点>

reject
