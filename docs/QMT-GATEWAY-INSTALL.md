# QMT Gateway 安装与运行边界

本文冻结 CR019-S04 的 Windows QMT gateway 生命周期与部署合同。当前范围只提供命令结构、配置字段、校验规则和离线验证入口；不得启动真实服务，不得绑定真实端口，不得访问 Windows QMT 节点，不得调用 QMT / MiniQMT / XtQuant。

## 适用范围

| 项目 | 边界 |
|---|---|
| 运行位置 | Windows QMT 节点 |
| C 侧入口 | local_backtest Python client / 薄 CLI |
| S 侧形态 | 未来 FastAPI gateway；本 Story 只冻结 lifecycle / deployment contract |
| 真实运行 | 本 Story 不授权 |
| 真实交易 | 本 Story 不授权 |
| 真实凭据 | 不得写入真实凭据，不得读取私有配置，不得把交易身份材料写进文档 |

## 命令结构

命令样例只表示结构，不可直接执行真实服务：

```bash
qmt-gateway serve --config <config-path> --host <windows-host> --port <port> --auth-mode pairing_hmac
```

字段说明：

| 字段 | 示例 | 说明 |
|---|---|---|
| `--config` | `<config-path>` | 配置文件路径占位符；当前测试只使用显式 fixture |
| `--host` | `<windows-host>` | Windows gateway bind host 占位符；公网和 `0.0.0.0` 默认阻断 |
| `--port` | `<port>` | 端口占位符；当前实现不绑定端口 |
| `--auth-mode` | `pairing_hmac` | S04 只保留鉴权模式槽位；配对细节由 S05 冻结 |

## 配置字段

| 配置组 | 必填字段 | Fail-closed 条件 |
|---|---|---|
| bind | `bind_host`、`port`、`public_exposure_allowed`、`wsl_access_host` | `0.0.0.0`、公网地址、端口越界或显式公网暴露 |
| firewall | `required`、`enabled`、`inbound_rule_present`、`rule_name`、`profile` | 防火墙未启用、规则缺失或不要求防火墙 |
| allowlist | `sources`、`required`、`description` | 来源为空、来源不可解析或来源为公网网段 |
| heartbeat | `interval_seconds`、`stale_after_seconds`、`unhealthy_after_missed` | 间隔小于等于 0，或 stale 小于 interval |
| redaction | `redacted_fields`、`required_fields`、`redaction_status` | 脱敏字段不完整 |

## 生命周期

| Transition | 当前 S04 行为 |
|---|---|
| `plan` | 只返回 `ready_to_start` 计划，不启动服务 |
| `start` / `serve` / `run` / `bind` | 返回 `service_start_forbidden` |
| `stop` / `shutdown` | 只记录 `stopped` 计划，不执行系统命令 |
| heartbeat unhealthy | 返回 `heartbeat_failed`，真实 QMT 调用计数保持 0 |

## 禁止事项

- 不得安装依赖或修改依赖锁定文件。
- 不得启动 FastAPI、uvicorn 或任何 Windows 服务。
- 不得绑定端口、打开网络连接或执行系统服务命令。
- 不得读取私有配置、交易身份材料、浏览器会话、私钥或本机认证材料。
- 不得调用 QMT / MiniQMT / XtQuant。
- 不得真实发单、撤单、查询交易账户或写 broker lake。
- 不得执行 provider fetch、lake write、publish、simulation 或 live run。

## 离线验证入口

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr019_qmt_gateway_lifecycle.py
```

预期结果：

| 检查 | 预期 |
|---|---|
| public exposure allowed count | 0 |
| service start count | 0 |
| port bind count | 0 |
| qmt api call count | 0 |
| dependency change count | 0 |
| credential read count | 0 |

## 后续边界

`O-CR019-S04-01` 保持 OPEN：真实 FastAPI runtime 依赖、安装脚本和服务启动授权不在 S04 范围。后续如需真实 Windows 节点 smoke、服务启动 dry-run 或端口验证，必须由 meta-po / user 单独授权，并重新进入对应 Story 或变更流程。

## CR020 Windows S 端手工安装调试手册

本节覆盖 CR-020 的 Windows S 端手工安装、配置、启动和排障。它只面向用户手动执行：本文档不授权 agent 读取真实 `.env`、启动 gateway、绑定端口、连接 QMT / MiniQMT / XtQuant、执行真实 `query_positions`，也不授权任何交易、撤单、改单、账户写入、simulation/live、provider/lake/publish。

### CR020 Contract Summary

| 组件 | 当前实现 | 文件 |
|---|---|---|
| S 端 runtime CLI | Typer CLI，命令为 `server-diagnostics`、`serve` | `trading/qmt_runtime_cli.py` |
| S 端 HTTP gateway | Python stdlib `ThreadingHTTPServer`，只暴露 `GET /qmt/health`、`GET /qmt/capabilities`、`POST /qmt/account/positions` | `trading/qmt_runtime.py` |
| QMT adapter | Windows 运行时懒加载 `xtquant.xttrader` / `xtquant.xttype`；导入发生在用户手动 `serve` 时 | `trading/qmt_runtime.py` |
| 登录 / session | `serve` 启动时执行 XtQuant connect/login，生成 redacted session snapshot | `trading/qmt_runtime.py` |
| 鉴权 | HMAC + allowlist + exact scope；scope 固定 `qmt:positions:read` | `trading/qmt_auth.py` |
| 查询接口 | 仅 `query_positions`，路径固定 `POST /qmt/account/positions` | `trading/qmt_gateway_service.py` |
| 响应脱敏 | 输出 `position_count`、`positions_digest`、`items_redacted`，不输出账号、证券代码、精确数量或市值原文 | `trading/qmt_gateway_contracts.py` |

### Authorization Boundary

| Gate | 允许的含义 | 不允许的含义 |
|---|---|---|
| CP5 / CP6 通过 | 允许进入代码实现和本地 fixture 验证 | 不表示 agent 可连接 QMT 或读取真实 `.env` |
| 用户手动执行本节命令 | 用户在自己的 Windows 机器上验证只读接口 | 不授权 agent 代为执行真实运行 |
| `server-diagnostics` 输出正常 | 配置占位 / 路径 / HMAC 配置可被解析 | 不表示 QMT 已登录 |
| `serve` health 中 `session_ready=true` | Windows S 端已通过 XtQuant session ready gate | 不表示交易、撤单、改单、账户写入或 live 已授权 |
| `query_positions` 成功 | 仅证明只读持仓查询链路可用且响应已脱敏 | 不表示其他 QMT endpoint 可用 |

### No-Authorization Table

| 类别 | CR020 状态 | 说明 |
|---|---|---|
| order submit / cancel / modify | not-authorized | `submit_live`、`cancel_live`、simulation submit/cancel 均不在本轮白名单 |
| account write | not-authorized | 本轮只读，不写账户、不修改账户状态 |
| simulation/live | not-authorized | 不启动 simulation/live/small-live/scale-up |
| provider/lake/publish | not-authorized | 不抓 provider、不写 lake、不 publish current pointer |
| raw positions output | not-authorized | 不输出原始持仓、未脱敏证券代码、精确数量或市值 |
| credential output | not-authorized | 不输出账号、密码、token、session、cookie、私钥或 HMAC secret |

### Windows 前置条件

| 前置项 | 要求 | 检查方式 |
|---|---|---|
| Windows | Windows 10/11，能运行 QMT / MiniQMT | 人工确认 |
| QMT / MiniQMT | 已安装并能在 Windows 桌面正常登录 | 先手工打开 QMT / MiniQMT |
| XtQuant | 与 MiniQMT 匹配的 Python XtQuant 包可被 Python 3.11 导入 | `uv run --python 3.11 python -c "import xtquant; print('xtquant ok')"` |
| uv | Windows 已安装 `uv` | `uv --version` |
| 项目代码 | 已复制或 clone 到 Windows 本地目录 | `dir` / 文件管理器确认 |
| 网络 | Linux C 端能访问 Windows S 端 host:port；防火墙只允许指定 Linux IP | `Test-NetConnection` 或 Linux `nc`，由用户手动执行 |

若券商要求 GUI 已登录或交易密码已由 MiniQMT 图形界面处理，请先在 Windows 桌面完成。当前 runtime adapter 使用 XtQuant 的 `XtQuantTrader(...).connect()`、`StockAccount(...)`、账户激活方法（优先 `login(...)`，若当前 XtQuant 版本无 `login` 则使用 `subscribe(...)`）和 `query_stock_positions(...)`；`.env` 中保留 `QMT_LOGIN_PASSWORD` 只是按用户要求存放登录材料，当前代码不会把它打印到输出中。

### Windows 安装步骤

1. 进入项目目录。

```bash
cd <local_backtest-windows-path>
```

2. 同步项目依赖。不要把 Windows XtQuant 依赖加入 Linux 主依赖；如果 XtQuant 需要单独安装，请按券商 / MiniQMT 提供的 Windows 指南安装到当前 Python 环境可见的位置。

```bash
uv sync --python 3.11
```

3. 创建本地未跟踪 `.env`。只复制占位模板，真实值只保存在 Windows 本机。

```bash
copy .env.example .env
```

4. 编辑 `.env`，至少填写以下字段。

```dotenv
QMT_GATEWAY_HOST=<windows-host-or-127.0.0.1>
QMT_GATEWAY_PORT=<port>
QMT_GATEWAY_ALLOWED_SOURCE=<linux-client-ip-or-cidr>
QMT_CLIENT_ID=<manual-client-id>
QMT_CLIENT_SECRET=<manual-long-random-secret>
QMT_ACCOUNT_REF=<qmt-account-ref>
QMT_ACCOUNT_TYPE=STOCK
QMT_XTQUANT_SITE_PACKAGES=<qmt-xtquant-site-packages-parent>
QMT_MINIQMT_PATH=<qmt-miniqmt-userdata-path>
QMT_RUNTIME_REF=<manual-runtime-authorization-ref>
QMT_SESSION_TTL_SECONDS=3600
```

字段说明：

| 字段 | 作用 | 注意 |
|---|---|---|
| `QMT_GATEWAY_HOST` | S 端绑定地址 | 本机调试可用 `127.0.0.1`；Linux 远程访问需填 Windows 局域网 IP |
| `QMT_GATEWAY_PORT` | S 端端口 | 建议先用 `18765` |
| `QMT_GATEWAY_ALLOWED_SOURCE` | C 端 allowlist | 远程 Linux 用 `<linux-ip>/32`；不要填公网网段 |
| `QMT_CLIENT_ID` / `QMT_CLIENT_SECRET` | C/S HMAC 身份 | Windows S 端和 Linux C 端必须一致 |
| `QMT_ACCOUNT_REF` | QMT 账号引用 | 不要把真实值贴到对话或日志 |
| `QMT_ACCOUNT_TYPE` | XtQuant `StockAccount` 类型 | A 股普通股票账户通常为 `STOCK` |
| `QMT_XTQUANT_SITE_PACKAGES` | 包含 `xtquant/` 目录的父目录 | 例如 QMT 安装目录下 `bin.x64\Lib\site-packages`；诊断输出只显示是否配置，不输出真实路径 |
| `QMT_MINIQMT_PATH` | MiniQMT user data 目录 | 常见为 `userdata_mini` 路径，以本机实际安装为准 |
| `QMT_RUNTIME_REF` | 本次人工运行授权引用 | 例如 `manual-cr020-20260605` |

### Windows S 端启动前诊断

先运行诊断，确认配置能被解析且输出已经脱敏：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics --env-file .env
```

预期输出要点：

| 字段 | 预期 |
|---|---|
| `status` | `ok` |
| `config.client_secret_ref` | `[REDACTED]` |
| `config.account_ref` | `account_ref:<hash>` |
| `config.xtquant_site_packages_configured` | `true` |
| `config.miniqmt_path_configured` | `true` |
| `config.allowed_source` | Linux C 端 IP/CIDR |

如果这里已经出现真实账号、密码、secret、token、session 或原始路径，请停止，删除输出记录并修正文档 / 代码脱敏问题。

### Windows S 端启动 gateway

确认 MiniQMT / QMT 已打开且处于可登录状态后，执行：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve --env-file .env --host <windows-host> --port <port> --runtime-authorization-ref <manual-runtime-ref>
```

启动后 CLI 会先打印一行 JSON，然后阻塞运行 HTTP server。重点看：

| 字段 | 成功预期 | 失败含义 |
|---|---|---|
| `status` | `starting` | CLI 已进入 server 启动流程 |
| `health.session_ready` | `true` | XtQuant connect + account activation 成功 |
| `health.session_state` | `ready` | session ready gate 通过 |
| `health.blocked_reason` | 空字符串 | 非空时查询会被阻断 |
| `health.runtime_status` | `xtquant-ready` | 其他值表示登录或 runtime 异常 |

如果 `serve` 已启动但 `session_ready=false`，C 端 `query-positions` 会返回 `session_not_ready` 或 QMT runtime 相关阻断原因。此时先按排障表修复，不要尝试其他 endpoint。

### Windows 本机 health 检查

在另一个终端手动访问 health：

```bash
curl http://<windows-host>:<port>/qmt/health
```

只检查脱敏状态，不要贴出包含真实路径或本机用户名的上下文。若没有 curl，可在浏览器打开 `http://<windows-host>:<port>/qmt/health`，只复制脱敏字段。

### Windows 停止和回滚

当前 `serve` 是前台进程。停止方式：

```bash
Ctrl+C
```

停止后从 Linux C 端再次访问应返回 transport unavailable / connection refused。若停止后仍能访问，说明有旧进程占用端口，必须在 Windows 任务管理器或命令行中定位并关闭旧进程，再重新启动。

### S 端排障表

| 现象 / reason | 常见原因 | 处理 |
|---|---|---|
| `typer_dependency_missing` | 未通过 `uv run --with typer` 启动 | 使用文档命令，或在隔离环境安装 Typer |
| `miniqmt_path_configured=false` | `.env` 未填 `QMT_MINIQMT_PATH` | 填入本机 MiniQMT `userdata_mini` 路径 |
| `missing-miniqmt-path-or-account` | `QMT_MINIQMT_PATH` 或 `QMT_ACCOUNT_REF` 缺失 | 补齐 `.env` |
| `xtquant-runtime-error:ModuleNotFoundError` | 当前 Python 环境找不到 XtQuant | 在 `.env` 设置 `QMT_XTQUANT_SITE_PACKAGES=<包含 xtquant 的 site-packages 父目录>`，或在 Windows 当前 uv/Python 环境安装券商提供的 XtQuant |
| `xtquant-connect-failed` | MiniQMT 未打开、路径错误或版本不匹配 | 打开 MiniQMT，确认路径和 XtQuant 版本 |
| `xtquant-account-activation-failed` / `xtquant-login-failed` | 账号类型不匹配、账号未登录、`login` / `subscribe` 失败或 broker 侧状态异常 | 检查 `QMT_ACCOUNT_REF`、`QMT_ACCOUNT_TYPE` 和 MiniQMT GUI |
| `auth_allowlist_mismatch` | Linux C 端 IP 不在 allowlist | 修改 `QMT_GATEWAY_ALLOWED_SOURCE=<linux-ip>/32` 并重启 S 端 |
| `auth_signature_mismatch` | C/S 两端 `QMT_CLIENT_SECRET` 不一致，或请求体被中间层改写 | 确认两端 `.env` 一致，避免代理修改 body |
| `auth_timestamp_skew` | Windows 与 Linux 时间相差过大 | 同步两端系统时间 |
| `auth_nonce_replay` | 重放同一请求 header | 重新执行 C 端命令，生成新 nonce |
| `session_not_ready` | S 端未完成 XtQuant connect 或 account activation | 回到 S 端 health，修复 MiniQMT 连接、账号激活和 session |
| `redaction_failed` | 响应脱敏扫描失败 | 不要保存 raw 输出，停止验证并回修 |

### CP7 Readonly Evidence Schema

手工验证成功后，建议只记录以下脱敏字段：

| 字段 | 示例形态 | 是否允许记录 |
|---|---|---|
| `run_id` | `manual-cr020-query-positions` | 允许 |
| `request_id` | `manual-cr020-query-positions-001` | 允许 |
| `endpoint_id` | `query_positions` | 允许 |
| `scope` | `qmt:positions:read` | 允许 |
| `status` | `ok` / `blocked` / `transport_error` / `auth_error` | 允许 |
| `position_count` | 整数 | 允许 |
| `positions_digest` | `positions:<hash>` | 允许 |
| `items_redacted` | ref / bucket | 允许 |
| `forbidden counters` | order/cancel/account_write/provider/lake/publish/simulation_live 均为 0 | 允许 |
| raw positions / 账号 / 密码 / token / session / secret | 原文 | 禁止 |
