# QMT Simulation / Live Activation Runbook

> Scope: CR-016 staged activation document contract only.
> This runbook defines offline approval, readiness, incident, reconciliation, kill switch, pause / resume, rollback, and recovery rules for `simulation`, `live_readonly`, `small_live`, and later `scale_up`.
> It does not execute or authorize QMT / MiniQMT / GUI launch, broker API calls, real order submission, real cancel, account query, account write, credential read, provider fetch, real lake write, real broker lake write, publish, `simulation` run, `live` run, `small_live` run, or `scale_up` run.

## 0. Authorization Boundary

本 runbook、[QMT Incident Playbook](QMT-INCIDENT-PLAYBOOK.md)、CP5、CP6/CP7、Story `verified` 状态或本文档存在，均不自动授权 `simulation`、`live`、`small_live`、`scale_up` 或任何真实 broker 操作。所有阶段请求必须逐 run 提供 per-run authorization，并在相应 stage gate、reconciliation gate、kill switch readiness 和 rollback gate 均满足后，才能作为后续受控执行输入。

当前 Story 只交付离线文档合同和静态测试，安全计数必须保持：

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
| `dependency_change` | `0` | 不修改 `pyproject.toml` / `uv.lock` |
| `simulation_run` | `0` | 不启动 simulation run |
| `live_run` | `0` | 不启动 live run |
| `small_live_run` | `0` | 不启动 small_live run |
| `scale_up_run` | `0` | 不启动 scale_up run |
| `real_snapshot_pull` | `0` | 不拉取真实 broker snapshot |
| `incident_persisted` | `0` | 不持久化真实 incident |
| `default_real_operation_authorization_claim` | `0` | 不把文档、Story 或检查点写成默认真实操作授权 |
| `sensitive_raw_value_output` | `0` | 不输出敏感原值 |

## 1. Stage Path And Entry Evidence

阶段路径固定为 `shadow -> simulation -> live_readonly -> small_live -> scale_up`，不得跳阶段。`live` 在本文档中只作为 `live_readonly` / `small_live` 的总称使用，不表示默认可运行状态。

| Stage | Previous evidence required | Exit evidence | Default status |
|---|---|---|---|
| `shadow` | CR-015 foundation CP7 PASS | order intent、risk result、mock / dry-run audit | allowed only by CR-015 offline contracts |
| `simulation` | CR016-S01 gate PASS、runbook readiness PASS、per-run authorization complete | simulation report candidate、reconciliation result、kill switch readiness | blocked until a separate authorized run |
| `live_readonly` | simulation exit evidence, reconciliation PASS, live-readonly admission gate | readonly broker snapshot evidence and diff report | later-gated |
| `small_live` | live_readonly observation PASS, capital cap, kill switch drill, approval | small_live run evidence and incident-free window | later-gated |
| `scale_up` | small_live stability, CR-017 verified, research maturity gates | scale-up review package | later-gated |

## P0-1 启动 / Start Gate

启动前必须只做门控检查和 evidence 装配。任何缺项都返回 `runbook_status=fail` 或 `stage_gate_status=blocked`，不得尝试实际运行。

| Check item | Required evidence | Owner | Fail behavior |
|---|---|---|---|
| Stage path | current stage and target stage are adjacent in `shadow -> simulation -> live_readonly -> small_live -> scale_up` | `research_owner` | `stage_skip_blocked` |
| CR-015 foundation | CR015-S01..S07 CP7 PASS or equivalent verified state | `research_owner` | `cr015_not_verified` |
| CR016 target gate | Target Story CP6 / CP7 PASS for the requested stage gate | `research_owner` | `target_gate_not_verified` |
| Runbook readiness | All P0 sections in this runbook exist and pass static checks | `research_owner` | `runbook_status=fail` |
| Reconciliation readiness | pre-market, intraday, post-market reconciliation policy refs exist | `trading_node_owner` | `reconciliation_policy_missing` |
| Kill switch readiness | heartbeat, stop-new-orders, planned-only cancel, recovery gate refs exist | `trading_node_owner` | `kill_switch_readiness_missing` |
| Per-run authorization | Required fields in Section P0-2 are complete and unexpired | `approver` | `authorization_required_missing` |

## P0-2 审批 / Per-run Approval Gate

Approval 只记录脱敏摘要，不记录真实账户号、token、password、cookie、session、private key、真实持仓、真实 broker root 或私有路径。缺任一字段时，`approval_status=fail`，目标 stage 保持 blocked。

| Field | Required meaning | Safe value rule | Blocking behavior |
|---|---|---|---|
| `authorization_id` | 单次审批唯一编号 | 使用审计编号或 ticket ref，不包含凭据值 | missing -> `authorization_required_missing` |
| `mode` | 请求模式，例如 `simulation`、`live_readonly`、`small_live`、`scale_up` | 必须与目标 stage 兼容 | mismatch -> `authorization_stage_mismatch` |
| `strategy_id` | 策略或组合所有者标识 | 使用内部策略编号，不含账户号 | missing -> `authorization_required_missing` |
| `run_id` | 本次运行唯一编号 | 用于对账、incident 和 rollback 关联 | missing -> `authorization_required_missing` |
| `stage` | 目标阶段 | 必须是固定阶段枚举之一 | invalid -> `stage_invalid` |
| `capital_limit` | 本次审批资金上限 | 使用限额摘要，不记录真实账户余额 | missing -> `authorization_required_missing` |
| `order_scope` | 本次允许的订单动作范围 | 例如 `order_intent_submit`、`readonly_snapshot_ref`，不得包含凭据 | missing -> `authorization_required_missing` |
| `approver` | 人工审批人或治理角色 | 使用角色或姓名标签，不使用个人凭据 | missing -> `authorization_required_missing` |
| `approved_at` | 审批时间 | ISO-like timestamp 或审计系统时间 | missing -> `authorization_required_missing` |
| `expires_at` | 审批过期时间 | 过期审批不得复用 | expired -> `authorization_expired` |
| `rollback_plan_ref` | 回滚方案引用 | 指向本文档 rollback matrix、incident playbook 或 ticket | missing -> `authorization_required_missing` |

可选字段可包含 `target_trade_date`、`observation_window`、`reconciliation_policy_ref`、`kill_switch_readiness_ref`、`manual_takeover_ref`。可选字段不得降低上表任何必填字段要求。

Incident 处理的详细合同见 [QMT Incident Playbook](QMT-INCIDENT-PLAYBOOK.md)。该 playbook 覆盖 `shadow`、`simulation`、`live_readonly`、`small_live`、`scale_up`，并按 `heartbeat_fail`、`risk_blocked`、`recon_diff`、`manual_trigger`、`recovery_required` 固定枚举记录 trigger、immediate action、owner、evidence required、recovery gate 和 rollback target。

## P0-3 异常处理 / Exception Handling

异常处理只输出候选动作、owner、blocked reason 和后续 evidence 要求，不执行真实 broker 动作。

| Incident type | Detection input | Immediate response | Owner | Required record |
|---|---|---|---|---|
| `authorization_missing_or_expired` | approval gate fail | keep target stage blocked | `approver` | missing fields, next approval request |
| `heartbeat_missed` | monitoring heartbeat fail | stop new order candidates, prepare planned-only cancel plan | `trading_node_owner` | incident candidate, heartbeat ref |
| `reconciliation_threshold_breach` | pre-market / intraday / post-market diff | enter manual_review or kill switch candidate | `trading_node_owner` | reconciliation report ref |
| `broker_ack_error` | ack/error enum from trading node | freeze stage transition, require manual review | `trading_node_owner` | redacted ack/error ref |
| `kill_switch_triggered` | kill switch result | freeze strategy, stop new order candidates | `trading_node_owner` | kill switch result ref |
| `manual_stop_request` | approver or owner stop request | pause requested stage and preserve evidence | `approver` | manual stop record |

## P0-4 对账 / Reconciliation

对账分为盘前、盘中、盘后三类。任何对账缺失、超阈值、敏感值输出或 owner/action 缺失，都阻断阶段推进。

| Reconciliation stage | Required comparison | Required output | Blocking status |
|---|---|---|---|
| `pre_market` | intended orders, cash / position snapshot refs, risk config refs | diff rows, threshold status, owner, action | `manual_review` or `blocked` |
| `intraday` | broker event refs, OMS state refs, heartbeat / kill switch refs | diff rows, threshold status, owner, action | `manual_review` or `kill_switch` |
| `post_market` | broker order/fill/position/asset refs, OMS state, broker lake candidate refs | final diff, threshold status, recovery recommendation | `blocked` until resolved |

Reconciliation 输出只允许引用脱敏 snapshot ref、root label、relative evidence ref 和 schema version。它不得拉取真实 snapshot、查询真实账户、写 broker lake、覆盖旧报告或 publish。

## P0-5 Kill Switch

Kill switch 的结果必须可审计，并保持 planned-only 行为，除非后续真实运行 Story 和 per-run authorization 明确授权执行动作。本 Story 不提供该授权。

| Trigger | Required output | Owner | Stop condition |
|---|---|---|---|
| heartbeat fail | incident candidate, stop-new-orders flag | `trading_node_owner` | new order allowed count remains `0` |
| reconciliation `manual_review` | freeze candidate, owner action | `trading_node_owner` | target stage remains blocked |
| reconciliation `kill_switch` | kill switch result, planned-only cancel plan | `trading_node_owner` | real cancel call remains `0` |
| manual trigger | incident candidate, manual takeover ref | `approver` | recovery blocked until takeover recorded |
| risk hard block | stop-new-orders flag, blocked reason | `research_owner` | adapter call remains `0` |

## P0-6 暂停 / 恢复

暂停和恢复必须由 evidence gate 控制。恢复不是重启真实运行的授权，只是将 blocked 状态转为可重新申请审批的候选状态。

| State | Required condition | Owner | Next gate |
|---|---|---|---|
| `paused` | manual stop, heartbeat fail, reconciliation manual_review, kill switch candidate, or expired approval | `trading_node_owner` | incident review |
| `manual_review` | diff threshold breach, broker ack error, unknown / timeout event | `research_owner` and `trading_node_owner` | reconciliation resolution |
| `frozen` | kill switch triggered or risk hard block | `trading_node_owner` | recovery gate |
| `recoverable` | reconciliation PASS, manual takeover recorded, approval still valid or re-approved | `approver` | per-run authorization refresh |
| `blocked` | missing evidence, expired approval, unresolved incident, CR-017 scale-up boundary missing | `approver` | remain blocked |

Recovery gate 只解除 incident blocked 状态，不启动真实运行。恢复必须至少满足 reconciliation PASS、`manual_takeover_record=recorded`、kill switch ready 或 shadow 不适用、authorization valid 或 refreshed，并保留 rollback target；缺任一项时目标 stage 保持 blocked。

## P0-7 回滚 / Rollback

Rollback 只定义目标状态和证据要求，不执行文件写入、撤单、发单、账户查询、真实 snapshot 拉取或 publish。

| Rollback target | Meaning | Required action | Owner |
|---|---|---|---|
| `shadow_only` | 回到 CR-015 offline foundation | stop stage progression, preserve audit refs | `research_owner` |
| `simulation_blocked` | 保持 simulation 请求 blocked | refresh runbook readiness and approval | `approver` |
| `live_readonly_blocked` | 保持 live readonly 请求 blocked | require reconciliation PASS and readonly evidence | `trading_node_owner` |
| `small_live_blocked` | 保持 small live 请求 blocked | require capital cap review and kill switch drill | `approver` |
| `scale_up_blocked` | 保持 scale-up 请求 blocked | require CR-017 verified and maturity gate evidence | `approver` |

## Rollback / Recovery Matrix

| incident type | stage | owner | action | rollback target | recovery gate |
|---|---|---|---|---|---|
| `authorization_missing_or_expired` | `simulation` | `approver` | keep stage blocked and request fresh per-run authorization | `simulation_blocked` | approval gate PASS and `expires_at` valid |
| `heartbeat_missed` | `simulation` | `trading_node_owner` | stop new order candidates and create incident candidate | `simulation_blocked` | heartbeat PASS and manual takeover recorded |
| `reconciliation_threshold_breach` | `simulation` | `trading_node_owner` | enter manual_review and freeze progression | `simulation_blocked` | reconciliation PASS across required stage |
| `broker_ack_error` | `live_readonly` | `trading_node_owner` | preserve redacted ack/error ref and block progression | `live_readonly_blocked` | ack/error resolved and reconciliation PASS |
| `kill_switch_triggered` | `small_live` | `trading_node_owner` | freeze strategy, keep cancel plan planned-only, escalate to approver | `small_live_blocked` | kill switch recovery gate PASS and new approval |
| `manual_stop_request` | `small_live` | `approver` | pause requested stage and retain evidence refs | `small_live_blocked` | manual resume approval and rollback plan review |
| `cr017_or_maturity_boundary_missing` | `scale_up` | `approver` | keep scale-up blocked and route to maturity evidence review | `scale_up_blocked` | CR-017 verified and research maturity gates PASS |

## CR019-S10 Bridge Boundary Addendum

CR-019 S10 adds the [QMT C/S Bridge Runbook](QMT-C-S-BRIDGE-RUNBOOK.md) as the user-facing boundary for Stage 6 admission, QMT C/S bridge, pairing/HMAC, endpoint matrix, run gate, fallback, and deferred capabilities. This addendum only aligns the CR016 staged activation runbook with that boundary.

The QMT C/S bridge does not change the stage path in this runbook. `shadow -> simulation -> live_readonly -> small_live -> scale_up` still requires adjacent-stage progression, per-run authorization, reconciliation gate, kill-switch readiness, recovery gate, and rollback gate. Endpoint visibility, HMAC pass, CP5, CP6, CP7, Story `verified`, README, USER-MANUAL, or runbook presence does not provide a real-operation permission.

No-real-operation counters for the CR-019 bridge boundary:

| Counter | Required value | Meaning in this runbook |
|---|---:|---|
| dependency_change | `0` | Do not add runtime dependencies while reading or applying this addendum. |
| service_start | `0` | Do not start FastAPI gateway, QMT, MiniQMT, GUI, socket, or port listener. |
| credential_read | `0` | Do not read `.env`, token, password, cookie, session, private-key material, account, position, or credential files. |
| qmt_miniqmt_xtquant_operation | `0` | Do not call QMT / MiniQMT / XtQuant / broker API. |
| provider_fetch | `0` | Do not fetch provider data for Stage 6 admission or QMT bridge checks. |
| lake_or_broker_lake_write | `0` | Do not write market-data lake, broker lake, raw, manifest, catalog, or incident storage. |
| publish | `0` | Do not publish current pointer or run artifact. |
| simulation_live_run | `0` | Do not start simulation, live_readonly, small_live, scale_up, or real trading flow. |

If a CR-019 bridge request reaches this runbook, treat it as a gate candidate only. Missing authorization, failed admission, failed stage gate, failed risk gate, active kill switch, failed reconciliation, unavailable gateway, auth failure, or fallback trigger all keep the target stage blocked. The next action is to return typed blocked evidence and route through meta-po / per-run authorization, not to start a run.

## Readiness Checklist

| Checklist | Required status |
|---|---|
| All seven P0 sections exist | `runbook_status=pass` |
| Per-run authorization required fields complete | `approval_status=pass` |
| Rollback / recovery matrix has required columns | `rollback_status=pass` |
| Forbidden default authorization claim count | `0` |
| Sensitive raw value output count | `0` |
| Real operation safety counters | all `0` |

## Stop Conditions

Stop this runbook flow when any request attempts to:

- Treat this runbook, CP5, CP6/CP7, Story `verified`, or document presence as authorization.
- Start `simulation`, `live`, `small_live`, or `scale_up` without per-run authorization.
- Launch QMT / MiniQMT / GUI or call broker APIs.
- Submit a real order, cancel a real order, query an account, write an account, read credentials, pull a real broker snapshot, write broker lake data, provider fetch, write a real lake, publish, or persist a real incident.

The correct next action is to keep the target stage blocked and route the request to the corresponding Story gate, per-run authorization, and meta-po approval path.
