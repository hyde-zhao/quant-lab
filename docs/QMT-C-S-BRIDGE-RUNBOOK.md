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
| `CR019-S09` | Deferred capability register | `docs/CR019-DEFERRED-CAPABILITIES.md`、`README.md`、`tests/test_cr019_deferred_capabilities.py` | 不新增依赖，不接 Qlib provider，不抓 minute / Level2 数据，不扩大 P0 | `process/checks/CP7-CR019-S09-deferred-capability-register-VERIFICATION-DONE.md` |
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
| Deferred register | `backtrader_w6`、`qlib_w7`、`minute_spike`、`level2_spike` 均有触发条件和后续 CR / CP 入口。 | Register 是范围合同，不是 runtime flag 或 dependency gate。 |

## 6. User Entry Points

| Entry | Purpose | Boundary |
|---|---|---|
| [README](../README.md) | 快速了解 Stage 6 admission、QMT C/S bridge 和 deferred capabilities | 只读说明，不提供运行许可 |
| [USER-MANUAL](USER-MANUAL.md) | 用户手册中的操作边界、真实授权禁区和后续 CR / CP 入口 | 只给出人工检查路径 |
| [QMT Simulation / Live Activation Runbook](QMT-SIMULATION-LIVE-RUNBOOK.md) | CR016 staged activation 治理入口 | 仍需 later-gated stage 和 per-run authorization |
| [QMT Incident Playbook](QMT-INCIDENT-PLAYBOOK.md) | incident、fallback、manual dry-run 和 recovery 边界 | 不持久化真实 incident，不写 broker lake |
| [Deferred Capability Register](CR019-DEFERRED-CAPABILITIES.md) | 后置能力范围合同 | 不新增依赖或数据获取 |

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
