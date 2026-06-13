请审查：`checkpoints/CP2-CR020-REQUIREMENTS-BASELINE.md`

自动预检结论：PASS，阻断项 0。预检文件：`process/checks/CP2-CR020-REQUIREMENTS-BASELINE.md`

本轮待人工决策项：7

如果你回复 approve，表示你接受以下 7 项推荐方案，不表示授权以下 6 类禁止操作。

待人工决策清单：

| 决策 ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 影响 / 风险 |
|---|---|---|---|---|---|
| DQ-CP2-CR020-01 | `scope` | CR-020 是否从 gateway health 升级为服务端登录 + 只读查询 | 升级为 Windows Gateway 服务端登录与 `query_positions` 只读查询准入 | 缩回 health-only；拆成登录 / 查询两个 CR | high：影响需求、HLD、Story、测试、文档 |
| DQ-CP2-CR020-02 | `runtime_authorization` | 是否授权后续门禁内启动 gateway、绑定端口、QMT 登录和只读查询 | 仅授权 Linux `uv run` Typer CLI 配对 / 验收与 Python REST client 调用 health / capabilities / `query_positions` 的只读 runtime | 只做离线设计；只做 gateway health | high：涉及 Windows host、端口、QMT session、Python REST transport |
| DQ-CP2-CR020-03 | `security` | 账号密码如何以 `.env` 形式存放且不泄露 | 真实值只在本地未跟踪 `.env`；入库只放 `.env.example` 占位变量 | OS secret store；交互式输入 | high：凭据泄露即 blocker |
| DQ-CP2-CR020-04 | `implementation` | S 端命令、C 端配对命令和实际业务调用如何表达 | S 端 Windows 使用 `uv run` Typer CLI；C 端配对 / 诊断 / 验收使用 Linux `uv run` Typer CLI；实际业务调用由 Python REST client 直接调用 gateway REST API | S / C 两端改用 Click；S / C 两端改用 argparse；S 端 Typer、C 端非 Typer CLI | medium：影响安装、验收、`trading/qmt_gateway_cli.py`、`trading/qmt_client_cli.py`、`trading/qmt_client.py` 和 Python REST transport |
| DQ-CP2-CR020-05 | `implementation` | 首个查询接口选哪个 | `query_positions`，只读、脱敏、scope=`qmt:positions:read` | `query_account`；只做 health / capabilities | high：接触持仓敏感数据 |
| DQ-CP2-CR020-06 | `risk_acceptance` | 是否接受真实 QMT 只读 API 风险 | 接受 `query_positions` 只读调用，不授权交易或写操作 | 完全不调用真实 QMT；转 CR-021 simulation | high：只读不等于交易准入 |
| DQ-CP2-CR020-07 | `architecture` | gateway 与 CLI 依赖如何隔离 | S 端可选 runtime / group；C 端 Typer CLI 依赖隔离；Linux C 端业务 runtime 保持轻依赖，CP3 前不改主依赖 | 直接入主依赖；完全外部安装 | medium：影响依赖治理和平台兼容 |

不授权项：

| 禁止操作 | 说明 |
|---|---|
| 发单、撤单、改单、账户写入 | CR-020 只确认只读连接和查询。 |
| simulation / live / live-readonly / small-live / scale-up | 仍由 CR-021..CR-024 单独授权。 |
| provider fetch / lake write / broker lake write / publish | 不写数据湖、不发布、不补数。 |
| 打印或保存真实凭据 | 账号、密码、token、session、交易密码、私钥不得进入 Git、对话、日志、检查点、memory。 |
| 扩大查询接口白名单 | 本轮只确认 `query_positions`；其他接口后置或重发决策。 |
| 自动终验 | CP8 仍需人工确认；本轮没有自动终验授权。 |

请只回复以下三种之一：

approve

修改: <具体修改点>

reject
