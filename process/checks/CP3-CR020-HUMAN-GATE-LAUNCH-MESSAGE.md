# CP3 CR-020 HLD 人工门禁发起消息

请审查：checkpoints/CP3-CR020-HLD-REVIEW.md

自动预检结论：PASS

自动预检文件：process/checks/CP3-CR020-HLD-CONSISTENCY.md

阻断项：0

本轮待人工决策项：7

如果你回复 approve，表示你接受以下 7 项推荐方案，不表示授权以下 10 项禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| DQ-CP3-CR020-01 | architecture | 是否接受 CR20-A 分层 Windows gateway + 双端 Typer CLI + C 端 Python REST client 作为推荐架构 | 接受 CR20-A：S 端 Windows `uv run` Typer CLI 管 gateway lifecycle / login / diagnostics；C 端 Linux `uv run` Typer CLI 仅 pairing / diagnostics / smoke / CP7；业务 runtime 为 Python REST client direct REST API。 | health/login only；外部 Windows runtime | 推荐方案满足 CP2 和最小闭环；health/login 风险低但不满足查询；外部 runtime 依赖干净但可审计性弱。 | 影响 CR020-S01..S06、CP5、CP7、docs、安全边界和依赖隔离。 |
| DQ-CP3-CR020-02 | implementation | 是否确认 S/C CLI 一致使用 Typer，但 C 端 CLI 不作为业务 runtime | 确认：S CLI 管 lifecycle；C CLI 管 pairing / diagnostics / validation；业务 runtime 为 Python REST client。 | CLI 作为 runtime；C 端无 CLI | 推荐方案与 CP2 一致；CLI runtime 类型和安全弱；无 C CLI 会削弱 CP7 验收。 | 影响 `qmt_gateway_cli.py`、`qmt_client_cli.py`、`qmt_client.py`、docs、QA。 |
| DQ-CP3-CR020-03 | security | 是否接受 `.env` 本地未跟踪 + redacted `credential_ref` 作为凭据策略 | 真实值只在本地未跟踪 `.env`；仓库只放 `.env.example` 占位；日志、检查点、文档、memory 只记录 redacted `credential_ref`。 | OS secret store；每次交互输入 | 推荐方案符合用户要求且落地简单；OS store 更安全但复杂；交互输入影响服务启动和复验。 | 凭据泄露为最高风险，影响安全、审计、运维和 CP7。 |
| DQ-CP3-CR020-04 | security | 是否接受 pairing_hmac + allowlist + scope + redaction 全部 fail-closed | pairing_hmac 默认启用，allowlist 必填，scope 逐 endpoint 校验，redaction fail-closed。 | no-auth local only；HMAC only | 推荐方案安全最完整；no-auth 风险高；HMAC only 网络边界不足。 | 影响 auth middleware、endpoint matrix、gateway config、CP7 wrong-scope / replay / source tests。 |
| DQ-CP3-CR020-05 | implementation | 是否确认只解锁 `query_positions`，scope=`qmt:positions:read` | 仅 `POST /qmt/account/positions` 进入本轮只读白名单，结果脱敏，其他 endpoint blocked。 | 改 `query_account`；health-only | positions 能证明真实只读连接；account 可替代但需重决策；health-only 不满足目标。 | 触达持仓敏感信息，需要强制 redaction 和 no-order safety。 |
| DQ-CP3-CR020-06 | architecture | 是否接受 S 端 gateway / XtQuant 依赖隔离，CP3 前不改 `pyproject.toml` / `uv.lock` | CP3 只定义隔离策略；CP5 LLD 再决定 extras / group / external runtime；CP3 前不改锁。 | 主依赖统一安装；完全外部 runtime | 推荐方案兼顾隔离和可交付；主依赖污染 Linux；外部 runtime 可审计性弱。 | 影响 Windows / Linux 兼容、CI、安装文档和运行手册。 |
| DQ-CP3-CR020-07 | runtime_authorization | 是否确认 CP3 通过不授权实现、启动、QMT 连接、交易、写入、simulation/live、provider/lake/publish 或凭据输出 | CP3 仅允许进入 Story Planning / CP4，不授权任何运行或真实凭据读取。 | 授权 bounded smoke；授权依赖准备 | 推荐方案权限最小；bounded smoke 或依赖准备需要后续 CP5/CP6/CP7 或独立运行授权。 | 防止越权运行、凭据泄露、交易误触和数据写入。 |

不授权项：

| 不授权项 | 说明 |
|---|---|
| 发单、撤单、改单、账户写入或任何 broker 写操作 | CR-020 仅只读查询设计和后续门控。 |
| simulation、live-readonly、small-live、scale-up 或任何真实交易准入 | 仍由 CR-021..CR-024 单独授权。 |
| provider fetch、真实联网补数、真实 lake write、catalog publish / current pointer publish、broker lake write 或 reports overwrite | CR-020 不触发数据生产 / 发布路径。 |
| 把 `query_positions` 以外的真实 QMT 查询接口纳入本轮默认白名单 | 其他 endpoint 保持 later-gated。 |
| 把账号、密码、token、session、交易密码、私钥写入 Git、对话、日志、检查点、memory 或任何入库文件 | 只允许 `.env.example` 占位和 redacted `credential_ref`。 |
| 在 CP3 前修改 `pyproject.toml` / `uv.lock` | 依赖形态 CP5 后再定。 |
| 把 Windows gateway / XtQuant 依赖加入 Linux C 端主依赖 | 必须隔离或外部 runtime。 |
| 把 C 端 Typer CLI 配对 / 验收命令误当成业务 runtime | 业务 runtime 必须是 Python REST client。 |
| 启动 gateway、绑定端口、连接 QMT、读取真实 `.env` | CP3 只确认 HLD，不授权运行。 |
| 启动 CR-021..CR-024 或扩大到 simulation / live 路线 | 后续 CR 独立门控。 |

该文件包含本检查点的 Entry Criteria、Checklist、Exit Criteria、Deliverables、自动预检摘要、Decision Brief、待人工决策清单和人工审查结果区。

回复 `approve` 表示接受上表全部推荐方案；如需调整，请用 `修改: <具体修改点>` 指明决策 ID 和修改内容。

approve

修改: <具体修改点>

reject
