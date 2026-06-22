---
title: "CR019 QMT C/S Bridge Runbook"
change_id: "CR-019"
story_id: "CR019-S10-docs-runbook-user-manual-boundary"
status: "controlled-offline-runbook"
created_at: "2026-05-31T10:00:00+08:00"
real_operation_permission_claims: 0
---

# QMT C/S Bridge Runbook

> Scope: CR-019 S10 documentation and static verification only.
> This runbook is the user-facing boundary for Stage 6 admission, QMT C/S bridge, pairing/HMAC, endpoint matrix, run gate, fallback, and deferred capability register.
> It does not execute QMT / MiniQMT / GUI launch, broker API calls, real order submission, real cancel, account query, account write, credential read, provider fetch, real lake write, real broker lake write, publish, `simulation` run, or `live` run.

## 1. Authorization Boundary

文档、runbook、README、USER-MANUAL、Story `verified`、CP5、CP6 和 CP7 都是设计 / 实现 / 验证证据，不是交易许可。它们不能把真实交易、账户查询、发单、撤单、broker lake 写入、provider fetch、publish、simulation 或 live 变成可执行动作。

真实操作必须另有后续 CR / CP 链路、逐次 per-run authorization、stage gate、risk gate、kill switch、reconciliation gate、rollback gate 和脱敏证据。缺任一项时，Stage 6 admission 和 QMT C/S bridge 只能保持 blocked / fixture-only / dry-run contract 状态。

| Object | Current meaning | Not authorization |
|---|---|---|
| This runbook | 用户可读的边界和排障入口 | 不是 QMT、broker、simulation 或 live 许可 |
| README / USER-MANUAL | 快速入口和操作说明 | 不是真实账户、真实发单、撤单或查询许可 |
| Story `verified` | CP7 对离线 / fixture / 静态合同的验证结果 | 不提供真实操作许可 |
| CP5 / CP6 / CP7 | LLD、编码和验证门禁证据 | 不替代 per-run authorization |
| HMAC / pairing | 调用方识别和防重放 | 不替代 stage / risk / kill-switch / per-run gates |
| Endpoint visible | API 类别存在并可返回 typed result | 不表示 endpoint 可直连真实 QMT |
| Fallback / signed file candidate | fail-closed 或人工 dry-run 候选 | 不绕过 gateway 或 run gate |

## 2. CP3 Decision Boundary

| Decision | Accepted recommendation | User impact | Not authorization |
|---|---|---|---|
| `CP3-CR019-DQ-01` | QMT 模块采用 local_backtest C 侧 Python client + Windows FastAPI gateway；signed file drop 只作为 fallback。 | 用户看到的主入口是 C/S bridge，而不是 WSL 直连 QMT。 | Gateway 可达不提供真实 QMT 许可。 |
| `CP3-CR019-DQ-02` | C 侧以 typed Python client / 函数调用为主，薄 CLI 只包装 client。 | 策略、OMS、admission dry-run 和测试复用同一 client 语义。 | CLI 存在不提供运行许可。 |
| `CP3-CR019-DQ-03` | endpoint matrix 完整建模，真实转发由 run mode、stage gate、risk gate、kill switch 和 per-run authorization 控制。 | 用户可查看 health、capabilities、行情、账户、委托、成交、simulation/live 等类别的 typed allowed / blocked result。 | Endpoint 类别存在不提供真实转发许可。 |
| `CP3-CR019-DQ-04` | 配对式 token/HMAC 默认启用；no-auth 只允许本机 debug、fixture 或显式临时模式。 | 用户需要先完成 pairing，再用 timestamp、nonce、scope 和 HMAC 调用 gateway。 | HMAC 通过不提供交易许可。 |
| `CP3-CR019-DQ-05` | fallback 采用 fail-closed：blocked-only 或人工 dry-run / signed file candidate。 | gateway 不可达、鉴权失败、heartbeat fail 或 gate fail 时得到 blocked result 和人工候选。 | Fallback 不提供真实操作许可。 |
| `CP3-CR019-DQ-06` | Backtrader W6、Qlib W7、minute Spike 和 Level2 Spike 均保持 deferred / later-gated。 | 用户可在 register 中查看触发条件和后续 CR / CP 入口。 | 后置能力 register 不提供依赖变更或数据获取许可。 |
| `CP3-CR019-DQ-07` | Stage 6 admission 采用新多因子 gate + 多基准 primary benchmark；旧失败策略只作为 blocked evidence。 | admission package 必须覆盖数据、因子、组合、成本、benchmark、稳健性、消融、冻结、pre-sim 和连续 5 个真实交易日 dry-run evidence。 | Admission pass 候选不提供 simulation/live 运行许可。 |

## 3. CR019 Story Boundary

| Story | Scope | Output surface | Forbidden operation | Verification entry |
|---|---|---|---|---|
| `CR019-S01` | Stage 6 admission gate 与 package 合同 | `engine/stage6_admission.py`、`trading/stage_gate.py`、`reports/stage6_admission/**`、`tests/test_cr019_stage6_admission_gate.py` | 不包装旧失败策略，不启动 simulation，不调用 QMT | `process/checks/CP7-CR019-S01-stage6-admission-gate-package-VERIFICATION-DONE.md` |
| `CR019-S02` | 多基准看板与 primary benchmark policy | `engine/benchmark_policy.py`、`reports/stage6_admission/benchmark_dashboard_schema.md`、`tests/test_cr019_primary_benchmark_policy.py` | 不补真实 benchmark，不抓 provider，不写 lake，不 publish | `process/checks/CP7-CR019-S02-primary-benchmark-dashboard-VERIFICATION-DONE.md` |
| `CR019-S03` | QMT C 侧 Python client 与薄 CLI 合同 | `trading/qmt_client.py`、`trading/qmt_cli.py`、`trading/qmt_transport.py`、`tests/test_cr019_qmt_cside_client_cli.py` | C 侧不导入或调用 QMT / MiniQMT / XtQuant | `process/checks/CP7-CR019-S03-qmt-cside-client-cli-contract-VERIFICATION-DONE.md` |
| `CR019-S04` | Windows gateway lifecycle / deployment 合同 | `trading/qmt_gateway_config.py`、`trading/qmt_gateway_service.py`、`docs/QMT-GATEWAY-INSTALL.md`、`tests/test_cr019_qmt_gateway_lifecycle.py` | 不启动服务，不绑定真实端口，不安装依赖，不读 Windows 凭据 | `process/checks/CP7-CR019-S04-windows-gateway-lifecycle-deployment-VERIFICATION-DONE.md` |
| `CR019-S05` | Pairing token/HMAC 与日志脱敏合同 | `trading/qmt_auth.py`、`trading/qmt_redaction.py`、`trading/qmt_gateway_config.py`、`tests/test_cr019_qmt_pairing_hmac_auth.py` | 不生成或读取真实 secret，不把 HMAC 当交易许可 | `process/checks/CP7-CR019-S05-pairing-hmac-auth-redaction-VERIFICATION-DONE.md` |
| `CR019-S06` | 完整 QMT endpoint matrix 与 typed blocked result | `trading/qmt_endpoint_matrix.py`、`trading/qmt_gateway_contracts.py`、`trading/qmt_client.py`、`tests/test_cr019_qmt_endpoint_matrix.py` | Endpoint 可见不等于真实 QMT / broker lake 操作许可 | `process/checks/CP7-CR019-S06-qmt-endpoint-matrix-contract-VERIFICATION-DONE.md` |
| `CR019-S07` | Run gate 与 blocked reason priority | `trading/qmt_gateway_gates.py`、`trading/stage_gate.py`、`trading/pretrade_risk.py`、`trading/kill_switch.py`、`tests/test_cr019_qmt_gateway_run_gates.py` | 不绕过 CR015 / CR016 stage、risk、kill-switch 或 per-run authorization | `process/checks/CP7-CR019-S07-run-gate-blocked-reason-integration-VERIFICATION-DONE.md` |
| `CR019-S08` | Fallback / incident / signed file fail-closed 边界 | `trading/qmt_gateway_fallback.py`、`docs/QMT-INCIDENT-PLAYBOOK.md`、`tests/test_cr019_qmt_gateway_fallback.py` | Fallback 不自动真实操作，不持久化真实 incident，不写 broker lake | `process/checks/CP7-CR019-S08-fallback-incident-signed-file-boundary-VERIFICATION-DONE.md` |
| `CR019-S09` | Deferred capability register | 本 runbook、`README.md`、`process/docs/source-archive/docs/CR019-DEFERRED-CAPABILITIES.md`、`tests/test_cr019_deferred_capabilities.py` | 不新增依赖，不接 Qlib provider，不抓 minute / Level2 数据，不扩大 P0 | `process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md` |
| `CR019-S10` | 文档、runbook 与用户手册边界 | `docs/QMT-C-S-BRIDGE-RUNBOOK.md`、`README.md`、`docs/USER-MANUAL.md`、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、`docs/QMT-INCIDENT-PLAYBOOK.md`、`tests/test_cr019_docs_runbook_boundary.py` | 不启动服务，不读凭据，不调用 QMT / provider / lake / publish / simulation / live | `process/checks/CP6-CR019-S10-docs-runbook-user-manual-boundary-CODING-DONE.md` |

## 4. No-Real-Operation Boundary

| Category | Required count | Forbidden operation | Later route |
|---|---:|---|---|
| dependency change | `0` | 不修改 `pyproject.toml`、`uv.lock` 或安装新运行依赖 | 新 CR / CP5 明确依赖范围后再处理 |
| service start | `0` | 不启动 FastAPI gateway、QMT、MiniQMT、GUI、socket 或端口监听 | Windows deployment Spike 或 per-run service-start authorization |
| credential read | `0` | 不读取 `.env`、token、password、cookie、session、private-key material、账户、持仓或凭据文件 | 真实运行 Story 的受控 secret handling |
| QMT / MiniQMT / XtQuant | `0` | 不导入、不调用、不探测真实 QMT / MiniQMT / XtQuant / broker API | 真实 adapter Story + per-run authorization |
| provider fetch | `0` | 不抓取 Tushare、JQData、Qlib、Level2、minute 或其他 provider 数据 | source/interface allowlist + explicit real-source gate |
| lake / broker lake | `0` | 不写 market-data lake、broker lake、raw、manifest、catalog 或 incident storage | Explicit Publish Gate 或 broker lake Story |
| publish | `0` | 不更新 catalog current pointer，不发布报告或运行产物 | 独立 publish approval |
| simulation/live | `0` | 不启动 simulation、live_readonly、small_live、scale_up 或真实交易流程 | CR016 later-gated stage + per-run authorization |

## 5. Pairing, HMAC, Endpoint, Gate, Fallback

| Area | User-visible behavior | Boundary |
|---|---|---|
| Pairing | C 侧发起 pairing request，S 侧管理员批准，C 侧完成 pair。 | Pairing 只建立调用方身份，不表达交易许可。 |
| HMAC | 后续请求携带 client id、timestamp、nonce、scope 和 HMAC signature。 | HMAC pass 后仍必须继续执行 endpoint、admission、stage、risk、kill-switch 和 per-run gates。 |
| Endpoint matrix | health / capabilities、validate / dry-run、行情、账户、持仓、委托、成交、simulation/live、reconciliation、kill-switch 等类别均有 typed result。 | Matrix 完整性只保证结果结构，不表示真实转发可用。 |
| Run gate | 主 blocked reason 优先级为 auth -> endpoint/schema -> admission/stage -> authorization -> risk -> kill_switch -> raw_policy -> operation_not_authorized，并保留 suppressed reasons。 | 任一 gate fail 时 adapter call count 保持 `0`。 |
| Fallback | gateway 不可达、auth fail、heartbeat fail、deployment not ready 或 run gate blocked 时 fail closed。 | 只返回 blocked result 或人工 dry-run candidate，不自动执行。 |
| Deferred register | `backtrader_w6`、`qlib_w7`、`minute_spike`、`level2_spike` 均有触发条件和后续 CR / CP 入口；详细 register 已归档到 `process/docs/source-archive/docs/CR019-DEFERRED-CAPABILITIES.md`。 | Register 是范围合同，不是 runtime flag 或 dependency gate。 |

## 6. User Entry Points

| Entry | Purpose | Boundary |
|---|---|---|
| [README](../README.md) | 快速了解 Stage 6 admission、QMT C/S bridge 和 deferred capabilities | 只读说明，不提供运行许可 |
| [USER-MANUAL](USER-MANUAL.md) | 用户手册中的操作边界、真实授权禁区和后续 CR / CP 入口 | 只给出人工检查路径 |
| [QMT Simulation / Live Activation Runbook](QMT-SIMULATION-LIVE-RUNBOOK.md) | CR016 staged activation 治理入口 | 仍需 later-gated stage 和 per-run authorization |
| [QMT Incident Playbook](QMT-INCIDENT-PLAYBOOK.md) | incident、fallback、manual dry-run 和 recovery 边界 | 不持久化真实 incident，不写 broker lake |
| Deferred capability summary | 本 runbook §5 与 README 摘要 | 不新增依赖或数据获取；详细 register 只在 `process/docs/source-archive/docs/CR019-DEFERRED-CAPABILITIES.md` 归档 |

## 7. Stop Conditions

出现以下任一请求时，停止当前流程并保持 blocked：

- 要求启动 QMT / MiniQMT / GUI、FastAPI gateway、socket 或端口监听。
- 要求调用 broker API、提交真实订单、撤真实订单、查询账户、写账户或拉取真实 snapshot。
- 要求读取 `.env`、token、password、cookie、session、private-key material、账户、持仓或凭据文件。
- 要求抓取 provider 数据、写 market-data lake、写 broker lake、publish current pointer 或持久化真实 incident。
- 要求把 CP5、CP6、CP7、Story `verified`、README、USER-MANUAL、runbook 或文档存在当作真实操作许可。
- 要求把 fallback、signed file candidate、HMAC pass 或 endpoint visible 当成绕过 stage gate / risk gate / kill switch / per-run authorization 的通道。

正确动作是返回 typed blocked result，记录脱敏 evidence ref，并回到 meta-po / stage gate / per-run authorization 路径。

## 8. Verification Contract

| Check | Required result |
|---|---|
| CP3 decision coverage | `CP3-CR019-DQ-01` through `CP3-CR019-DQ-07` all present |
| Story boundary coverage | `CR019-S01` through `CR019-S10` all present |
| No-real-operation coverage | 8 categories present and all counts are `0` |
| Sensitive real-value examples | `0` |
| Misleading permission semantics | `0` |
| Dependency / lock / `.env` modification | `0` |
| Real operation count | `0` |

## 9. CR020 Manual Install Debug Guide

本节覆盖 CR-020 手工安装调试。Windows S 端启动和 QMT 连接由用户手动执行；Linux C 端用 CLI 手动验证 `query_positions` 是否可用。本文档不授权 agent 读取真实 `.env`、启动 gateway、连接 QMT、执行真实查询或保存未脱敏输出。

### 9.1 CR020 Contract Summary

| Layer | Runtime entry | Purpose |
|---|---|---|
| Windows S 端 | `uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve` | 启动本地 HTTP gateway，登录 XtQuant session，暴露只读 positions endpoint |
| Linux C 端 CLI | `uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions` | 手工 CP7 / smoke 验证，不作为业务 runtime |
| Linux C 端业务 runtime | `QmtClient` + `StdlibQmtRestTransport` + `QmtHmacHeaderProvider` | Python 代码直接调用 REST API |
| Endpoint | `POST /qmt/account/positions` | 唯一 CR020 只读 QMT 查询接口 |
| Scope | `qmt:positions:read` | exact scope，其他 scope 不替代 |
| Response | redacted positions summary | 不输出账号、证券代码、精确数量、市值或 raw payload |

### 9.2 Authorization Boundary

| 动作 | CR020 当前状态 |
|---|---|
| 用户在 Windows 手动启动 S 端 gateway | allowed for manual validation |
| 用户在 Linux 手动执行 C 端 `query-positions` CLI | allowed for manual validation |
| agent 代为读取 `.env`、启动 server、连接 QMT 或查询持仓 | not-authorized |
| 业务代码通过 `QmtClient.query_positions()` 调 REST API | allowed after user deploys S 端 and provides runtime config |
| 任何发单、撤单、改单、账户写入、simulation/live、provider/lake/publish | not-authorized |
| `query_positions` 以外的真实 QMT endpoint | not-authorized in CR020 |

### 9.3 Linux C 端安装准备

1. 进入项目目录。

```bash
cd /home/hyde/workspace/local_backtest
```

2. 同步 Linux 依赖。Linux C 端不需要 XtQuant，也不应安装 Windows QMT 依赖。

```bash
uv sync --python 3.11
```

3. 创建 Linux C 端本地 `.env`。C 端只需要 REST 和 HMAC 相关字段，必须与 Windows S 端一致。

```bash
cp .env.example .env
```

至少填写：

```dotenv
QMT_GATEWAY_HOST=<windows-host>
QMT_GATEWAY_PORT=<port>
QMT_CLIENT_ID=<same-client-id-as-windows>
QMT_CLIENT_SECRET=<same-client-secret-as-windows>
QMT_RUNTIME_REF=<manual-runtime-authorization-ref>
```

不要在 Linux C 端填写或安装 XtQuant；`QMT_MINIQMT_PATH`、`QMT_ACCOUNT_REF` 等 Windows 专属字段可以保留占位或空值。

### 9.4 Linux C 端连通性检查

先确认 Windows S 端已经按 [QMT Gateway 安装与运行边界](QMT-GATEWAY-INSTALL.md) 启动，并且 health 中 `session_ready=true`。

Linux 上检查端口：

```bash
timeout 5 nc -vz <windows-host> <port>
```

如果没有 `nc`，可以直接执行 client diagnostics：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli client-diagnostics --env-file .env --base-url http://<windows-host>:<port>
```

预期输出：

| 字段 | 预期 |
|---|---|
| `status` | `ok` |
| `base_url` | `http://<windows-host>:<port>` |
| `client_id_hash` | 非空 hash |
| `client_secret_ref` | `[REDACTED]` |

### 9.5 Linux C 端手动验证 `query_positions`

执行：

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions --env-file .env --base-url http://<windows-host>:<port> --run-id manual-cr020-query-positions --request-id manual-cr020-query-positions-001
```

成功时，C 端 CLI 输出 `QmtResponse` JSON。关键字段：

| 字段路径 | 成功预期 |
|---|---|
| `status` | `ok` |
| `endpoint` | `positions` |
| `payload.query_positions.position_count` | 整数，可能为 0 |
| `payload.query_positions.positions_digest` | `positions:<hash>` |
| `payload.query_positions.items_redacted` | 只包含 `position_ref`、`instrument_ref`、`side_ref`、`quantity_bucket`、`value_bucket` |
| `payload.operation_authorized` | `false` |
| `payload.real_operation` | `false` |
| `counters.real_order` / `real_cancel` / `account_write` / `provider_fetch` / `lake_write` / `publish` / `simulation_or_live_run` | 全部 `0` |

输出中不应出现：

| 禁止出现 | 说明 |
|---|---|
| 账号原文 | 包括资金账号、交易账号、broker account |
| `QMT_CLIENT_SECRET` 原文 | HMAC secret 只能存在本地 `.env` |
| 未脱敏证券代码 | 例如直接显示股票代码原文 |
| 精确持仓数量 / 市值组合 | 只能出现 bucket |
| raw positions payload | 只能出现 redacted summary |

### 9.6 Python 业务代码调用示例

CLI 只用于手工验证。业务代码应直接使用 Python REST client：

```python
from trading.qmt_client import QmtClient, QmtClientConfig
from trading.qmt_runtime import (
    StdlibQmtRestTransport,
    build_runtime_config,
    build_runtime_hmac_provider,
    load_runtime_env,
)

env = load_runtime_env(".env")
config = build_runtime_config(env)

client = QmtClient(
    config=QmtClientConfig(
        base_url="http://<windows-host>:<port>",
        default_stage="manual_cp7",
        default_mode="live_readonly",
    ),
    transport=StdlibQmtRestTransport(),
    auth_header_provider=build_runtime_hmac_provider(config),
)

response = client.query_positions(
    run_id="manual-cr020-query-positions",
    request_id="manual-cr020-query-positions-001",
    authorization_ref=config.runtime_authorization_ref,
)
print(response.to_dict())
```

该示例仍只调用 `query_positions`，不提供任何交易、撤单、改单或账户写入入口。

### 9.7 C/S 排障表

| C 端输出 / reason | 可能原因 | 处理 |
|---|---|---|
| `transport_error` / `gateway_unavailable` | Windows S 端未启动、host/port 错误、防火墙阻断 | 先检查 S 端 `serve` 是否运行，再检查 Windows 防火墙和 Linux 到 Windows 网络 |
| `transport_timeout` | 网络延迟或 S 端阻塞 | 增大 timeout，检查 S 端日志和 MiniQMT 状态 |
| `auth_required` | C 端没有 HMAC provider 或 secret 缺失 | 检查 C 端 `.env` 的 `QMT_CLIENT_ID` / `QMT_CLIENT_SECRET` |
| `auth_client_not_approved` | C/S client id 不一致 | 确保两端 `QMT_CLIENT_ID` 相同并重启 S 端 |
| `auth_secret_unavailable` | S 端缺少对应 client secret | 确保 Windows S 端 `.env` 也填了同一 secret |
| `auth_signature_mismatch` | secret 不一致或请求体被改写 | 同步两端 secret，避免 HTTP 代理修改 body |
| `auth_allowlist_mismatch` | Linux IP 不在 S 端 allowlist | Windows `.env` 设置 `QMT_GATEWAY_ALLOWED_SOURCE=<linux-ip>/32` 并重启 |
| `auth_timestamp_skew` | Windows/Linux 时间不同步 | 同步系统时间 |
| `auth_nonce_replay` | 重复使用同一个请求 header | 重新执行 CLI |
| `scope_denied` / `auth_scope_denied` | scope 不是 `qmt:positions:read` | 使用 runtime CLI，不要自定义其他 scope |
| `session_not_ready` | S 端 QMT login/session 未 ready | 回 Windows S 端检查 health 和 `xtquant-*` reason |
| `adapter_unavailable` | S 端没有注入 XtQuant adapter | 使用 `qmt_runtime_cli serve`，不要只运行离线合同 CLI |
| `redaction_failed` | 响应脱敏失败 | 停止验证，不保存 raw 输出，回修 redaction |
| `endpoint_not_supported` | 调用了非 CR020 白名单 endpoint | 只调用 `query_positions` |

### 9.8 CP7 Readonly Evidence Schema

手动验证后，可向 meta-po/meta-qa 提供脱敏摘要：

| Evidence field | Required value |
|---|---|
| `endpoint_id` | `query_positions` |
| `scope` | `qmt:positions:read` |
| `run_id` | 本次手工 run id |
| `request_id` | 本次手工 request id |
| `status` | `ok` 或 blocked/error reason |
| `session_ready` | S 端 health 的脱敏状态 |
| `auth_status` | C 端输出中的 auth/error reason，不含 raw headers |
| `redaction_status` | `pass` |
| `position_count` | 整数 |
| `positions_digest` | `positions:<hash>` |
| `forbidden_counters` | order/cancel/modify/account_write/broker_lake/provider/lake/publish/simulation_live 均为 `0` |

禁止提交：真实 `.env`、账号、密码、token、session、cookie、HMAC secret、raw signature、raw positions、未脱敏证券代码、精确持仓数量、市值组合、MiniQMT 本机私有路径。

### 9.9 回滚和停止条件

| 条件 | 动作 |
|---|---|
| 输出出现真实凭据或 raw positions | 立即停止，删除输出记录，回修脱敏 |
| 任何非 `query_positions` endpoint 被允许 | 立即停止，回滚 CR020-S05 |
| forbidden counters 任一非 0 | 立即停止，回滚并重新验证 |
| Windows S 端停止后 Linux 仍可查询 | 查找并关闭旧 server 进程 |
| 用户需要交易 / 撤单 / simulation/live | 启动后续 CR，不在 CR020 内扩展 |
