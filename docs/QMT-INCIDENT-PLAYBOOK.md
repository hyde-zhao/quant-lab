# QMT Incident Playbook

> Scope: CR016-S07 documentation contract and static verification only.
> This playbook defines incident handling for `shadow`, `simulation`, `live_readonly`, `small_live`, and `scale_up`.
> It does not execute or authorize QMT / MiniQMT / GUI launch, broker API calls, real order submission, real cancel, account query, account write, credential read, provider fetch, real lake write, real broker lake write, publish, `simulation` run, `live_readonly` run, `small_live` run, `scale_up` run, real snapshot pull, or real incident persistence.

## 0. Authorization Boundary

本文档、`docs/QMT-SIMULATION-LIVE-RUNBOOK.md`、README、USER-MANUAL、CP5、CP6、CP7、Story `verified` 状态或文档存在，均不自动授权真实操作。文档合同不自动授权真实运行；任何阶段请求都必须另有 per-run authorization、stage gate、reconciliation gate、kill switch readiness、recovery gate 和 rollback gate 证据。

安全计数必须保持：

| Counter | Required value | Boundary |
|---|---:|---|
| `qmt_api_call` | `0` | 不调用 QMT / MiniQMT / XtQuant / broker API |
| `real_order_call` | `0` | 不提交真实订单 |
| `real_cancel_call` | `0` | 不执行真实撤单 |
| `account_query_call` | `0` | 不查询真实账户 |
| `account_write_call` | `0` | 不写账户状态 |
| `credential_read` | `0` | 不读取 `.env`、token、password、cookie、session、private key、真实账户、真实持仓或凭据文件 |
| `real_broker_operation` | `0` | 不执行真实 broker 操作 |
| `real_broker_lake_write` | `0` | 不写真实 broker lake |
| `real_lake_write` | `0` | 不写真实 market-data lake |
| `provider_fetch` | `0` | 不抓取 provider 数据 |
| `publish` | `0` | 不 publish current pointer 或运行产物 |
| `simulation_run` | `0` | 不启动 simulation |
| `live_run` | `0` | 不启动 live |
| `small_live_run` | `0` | 不启动 small_live |
| `scale_up_run` | `0` | 不启动 scale_up |
| `real_snapshot_pull` | `0` | 不拉取真实 broker snapshot |
| `incident_persisted` | `0` | 不持久化真实 incident |
| `default_real_operation_authorization_claim` | `0` | 不把文档、Story 或检查点写成默认真实操作授权 |
| `unsupported_execution_claim_unblocked` | `0` | 不解除真实 VWAP、minute、tick、Level2 或 order-match blocked claim |
| `sensitive_raw_value_output` | `0` | 不输出敏感原值 |

## 1. Stage Coverage

阶段路径固定为 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，不得跳阶段。下表只定义 incident 处理边界，不表示阶段可运行。

| Stage | Incident handling scope | Recovery owner | Rollback target | Default operation status |
|---|---|---|---|---|
| `shadow` | 本地 order intent、risk result、mock / dry-run audit 的 incident candidate | `research_owner` | `shadow_only` | offline-only |
| `simulation` | 模拟盘申请的 heartbeat、risk、reconciliation、manual trigger、recovery gate incident | `trading_node_owner` | `simulation_blocked` | blocked until separate authorized run |
| `live_readonly` | 后续只读核对阶段的 snapshot ref、diff report、manual takeover evidence | `trading_node_owner` | `live_readonly_blocked` | later-gated |
| `small_live` | 后续小资金阶段的 capital cap、kill switch drill、incident-free window | `approver` | `small_live_blocked` | later-gated |
| `scale_up` | 后续资金放大阶段的 CR-017 verified、research maturity、unsupported claim boundary | `approver` | `scale_up_blocked` | later-gated |

## 2. Incident Playbook

每类 incident 都必须记录 `trigger`、`immediate action`、`owner`、`evidence required`、`recovery gate`、`rollback target`。所有 action 都是文档化或 planned-only 动作，不执行真实发单、撤单、账户查询、snapshot 拉取、broker lake 写入、provider fetch、publish 或真实 incident persistence。

| incident type | trigger | immediate action | owner | evidence required | recovery gate | rollback target |
|---|---|---|---|---|---|---|
| `heartbeat_fail` | heartbeat deadline missed、heartbeat status fail、trading node liveness unknown | stop new order candidates, freeze stage progression, create incident candidate | `trading_node_owner` | heartbeat event ref, stage, observed time, stop-new-orders flag, planned-only cancel plan ref | heartbeat PASS, reconciliation PASS, `manual_takeover_record=recorded`, approval still valid or refreshed | `simulation_blocked` |
| `risk_blocked` | pre-trade risk hard block、cash / lot / T+1 / price policy / duplicate / limit rule fail | keep adapter call count at `0`, freeze order intent, route to risk owner review | `research_owner` | risk result ref, rule_id, blocked reason, affected intent refs with sensitive values redacted | risk rule resolved or accepted as blocked, reconciliation PASS where applicable, `manual_takeover_record=recorded` | `shadow_only` |
| `recon_diff` | pre-market、intraday 或 post-market reconciliation diff exceeds threshold | enter manual_review, stop stage promotion, preserve redacted diff refs | `trading_node_owner` | reconciliation report ref, diff class, threshold status, owner action, affected stage | reconciliation PASS across required scope, owner action closed, `manual_takeover_record=recorded` | `simulation_blocked` |
| `manual_trigger` | approver、research owner 或 trading node owner requests pause / stop / takeover | pause target stage, freeze new order candidates, require explicit resume approval | `approver` | manual trigger ref, requester role, reason, timestamp, rollback plan ref | manual resume approval, rollback plan reviewed, `manual_takeover_record=recorded` | `small_live_blocked` |
| `recovery_required` | prior incident closed but recovery evidence missing, stale, expired, or inconsistent | keep target stage blocked, require recovery checklist completion before any new request | `approver` | incident close ref, recovery checklist, reconciliation status, kill switch state, authorization validity | recovery gate PASS with reconciliation PASS, kill switch ready, `manual_takeover_record=recorded`, fresh per-run authorization if expired | `scale_up_blocked` |

## 3. Stage-Specific Routing

| Stage | Allowed incident types | Required routing result |
|---|---|---|
| `shadow` | `risk_blocked`, `manual_trigger`, `recovery_required` | keep offline foundation only; rollback to `shadow_only` |
| `simulation` | `heartbeat_fail`, `risk_blocked`, `recon_diff`, `manual_trigger`, `recovery_required` | keep simulation request blocked until recovery gate PASS |
| `live_readonly` | `heartbeat_fail`, `recon_diff`, `manual_trigger`, `recovery_required` | keep readonly request later-gated; require readonly evidence and reconciliation PASS |
| `small_live` | `heartbeat_fail`, `risk_blocked`, `recon_diff`, `manual_trigger`, `recovery_required` | keep small live later-gated; require capital cap review and kill switch drill evidence |
| `scale_up` | `risk_blocked`, `recon_diff`, `manual_trigger`, `recovery_required` | keep scale_up blocked until CR-017 verified, research maturity gate PASS, and unsupported claims remain blocked |

## 4. Recovery Gate

Recovery gate 是解除 incident blocked 状态的证据门，不是启动真实运行的授权。恢复请求必须同时满足：

| Required condition | Required value | Failure status |
|---|---|---|
| `reconciliation_status` | `pass` | `recovery_gate_missing_reconciliation_pass` |
| `manual_takeover_record` | `recorded` | `recovery_gate_missing_manual_takeover_record` |
| `kill_switch_state` | `ready` or `not_applicable_for_shadow` | `recovery_gate_missing_kill_switch_ready` |
| `authorization_status` | `valid` or `refreshed` | `recovery_gate_missing_fresh_authorization` |
| `rollback_target` | one of `shadow_only`, `simulation_blocked`, `live_readonly_blocked`, `small_live_blocked`, `scale_up_blocked` | `recovery_gate_invalid_rollback_target` |

`manual_takeover_record` 至少包含 incident ref、stage、owner、takeover reason、action taken、rollback target、reviewed_at 和 approver / owner 标签。它只允许记录脱敏 ref 和角色标签，不记录真实账户、真实持仓、token、password、cookie、session、private key、真实 broker root 或私有路径。

## 5. Unsupported Claim Boundary

Incident 处理不得解除任何 unsupported execution claim。以下 claim 在本 playbook 中保持 blocked / unsupported：

| Claim | Required status | Reason |
|---|---|---|
| `real_vwap_execution` | blocked | 缺真实 VWAP 字段、execution audit 和授权 Story |
| `minute_execution` | blocked | minute 数据与执行模拟不在本 Story 范围 |
| `tick_execution` | blocked | tick 数据与逐笔执行不在本 Story 范围 |
| `Level2_execution` | blocked | Level2 / 盘口微观结构不在本 Story 范围 |
| `order_match_execution` | blocked | 撮合与订单簿仿真不在本 Story 范围 |

`unsupported_execution_claim_unblocked` 必须保持 `0`。如需解除上述 claim，必须另起 Story、LLD、CP5、CP6、CP7 和用户显式授权。

## 6. Stop Conditions

出现以下任一请求时，停止当前流程并保持目标 stage blocked：

- 把 README、USER-MANUAL、runbook、incident playbook、CP5、CP6、CP7、Story `verified` 或文档存在视为真实操作授权。
- 跳过 `shadow -> simulation -> live_readonly -> small_live -> scale_up` 的相邻阶段顺序。
- 在缺少 per-run authorization、reconciliation PASS、`manual_takeover_record=recorded` 或 rollback target 的情况下恢复。
- 要求启动 QMT / MiniQMT / GUI、调用 broker API、提交真实订单、撤真实订单、查询账户、写账户、读取凭据、拉取真实 snapshot、写真实 broker lake、provider fetch、写真实 lake、publish 或持久化真实 incident。
- 要求解除真实 VWAP、minute、tick、Level2 或 order-match blocked claim。

## 7. CR019-S08 Fallback / Signed File Manual-Only Boundary

CR019-S08 将 QMT C/S bridge 的 fallback 固化为 fail-closed 合同。gateway 不可达、`auth_failed`、`heartbeat_failed`、`deployment_not_ready` 或 `run_gate_blocked` 时，只允许返回 typed blocked result，或生成人工 dry-run 文件候选；该候选只用于演练、排障和人工复核。

### 7.1 Trigger Routing

| Trigger | Required result | Manual file boundary | Forbidden escalation |
|---|---|---|---|
| `gateway_unreachable` | `status=blocked` / `transport_unavailable` | 可生成脱敏 manual dry-run 候选 | 不得绕过 gateway 调用 QMT |
| `auth_failed` | `status=blocked` / `auth_blocked` | 可生成脱敏 manual dry-run 候选 | 不得把认证失败转成真实操作 |
| `heartbeat_failed` | `status=blocked` / `heartbeat_failed` | 可生成 heartbeat 事件引用候选 | 不得启动服务、探测端口或调用 QMT |
| `deployment_not_ready` | `status=blocked` / `deployment_not_ready` | 可生成部署证据缺口候选 | 不得安装依赖、改配置或启动 gateway |
| `run_gate_blocked` | `status=blocked` / 上游 typed reason | 可生成 gate reason 候选 | 不得绕过 stage gate、risk gate、kill switch 或 per-run authorization |

### 7.2 Signed File Payload Contract

manual dry-run 文件候选必须固定包含并保持以下字段：

| Field | Required value | Meaning |
|---|---|---|
| `mode` | `mode=manual_dry_run_only` | 只允许人工 dry-run / 演练 |
| `auto_execute` | `auto_execute=false` | 禁止自动执行 |
| `real_qmt_allowed` | `real_qmt_allowed=false` | 禁止真实 QMT 操作 |
| `manual_handling_required` | `manual_handling_required=true` | 必须人工复核 |
| `broker_lake_write_allowed` | `false` | 禁止 broker lake 写入 |
| `simulation_live_allowed` | `false` | 禁止 simulation/live 运行 |

payload 过期、签名状态未通过、出现敏感原值、出现自动执行字段或任一 forbidden counter 非 0 时，处理方必须返回 blocked / invalid result。返回 blocked 不表示 incident 已落库，也不表示后续运行获批。

### 7.3 Stop Conditions

出现以下任一情况时，保持 blocked 并停止：

- 把 signed file drop 理解为授权入口；该入口不授权真实交易、撤单、账户查询、broker lake 写入、publish 或 simulation/live。
- 试图通过 fallback 绕过 gateway、HMAC、endpoint matrix、run gate、stage gate、risk gate、kill switch 或 per-run authorization。
- 试图持久化真实 incident、写 broker lake、写 market-data lake、provider fetch、publish，或启动 simulation/live。
- payload 中 `auto_execute` 或 `real_qmt_allowed` 被置为 true、`manual_handling_required` 被置为 false，或 forbidden operation counters 任一非 0。

## 8. CR019-S10 Documentation Boundary Addendum

CR-019 S10 adds [QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md) as the consolidated user boundary. This playbook remains the incident and fallback handling document; it does not become a gateway runtime, broker event store, simulation launcher, or live operation entry.

When an incident involves the QMT C/S bridge, preserve these routing rules:

| Trigger source | Incident interpretation | Required response | Forbidden escalation |
|---|---|---|---|
| Stage 6 admission blocked | Admission package is not ready for a QMT stage request | keep target stage blocked and return evidence refs | do not request simulation/live |
| Pairing / HMAC failed | Caller identity, timestamp, nonce, or scope is invalid | return `auth_blocked` / typed blocked evidence | do not convert auth failure into fallback execution |
| Endpoint matrix blocked | Endpoint is unknown, unsupported, or gate input is incomplete | return endpoint / schema blocked result | do not call QMT / MiniQMT / XtQuant |
| Run gate blocked | stage, risk, kill switch, per-run authorization, or raw policy fails | preserve primary reason and suppressed reasons | do not bypass gate ordering |
| Gateway unavailable | Windows gateway cannot be reached or is not deployment-ready | return transport / deployment blocked result, optionally create manual dry-run candidate | do not start service, bind port, or open socket from this playbook |
| Signed file candidate | Manual dry-run candidate exists for review | require manual handling and keep `auto_execute=false` | do not write broker lake, publish, or start simulation/live |

No-real-operation counters stay closed in incident handling:

| Counter | Required value |
|---|---:|
| dependency_change | `0` |
| service_start | `0` |
| credential_read | `0` |
| qmt_miniqmt_xtquant_operation | `0` |
| provider_fetch | `0` |
| lake_or_broker_lake_write | `0` |
| publish | `0` |
| simulation_live_run | `0` |

If a user or operator asks to treat README, USER-MANUAL, runbook, incident playbook, CP5, CP6, CP7, Story `verified`, HMAC pass, endpoint visible, fallback, or signed file candidate as permission for real operations, keep the incident in blocked state and route back to meta-po / per-run authorization. The playbook may record only redacted evidence refs and manual review requirements.
