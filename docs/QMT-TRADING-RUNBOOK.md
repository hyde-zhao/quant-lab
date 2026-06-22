# QMT Trading Foundation Runbook

> Scope: CR-015 foundation only. This runbook describes offline setup, shadow, dry-run, mock, and handoff evidence. It does not grant simulation, live_readonly, small_live, scale_up, real QMT access, real order, real cancel, account query, credential read, real broker lake write, provider fetch, real lake write, or publish authority.

## 1. Setup Boundary

### 1.1 Foundation Mode

CR-015 foundation has exactly three allowed modes:

| Mode | Current use | External effect |
|---|---|---|
| `shadow` | Build order intent and audit evidence from local target portfolio / fixture snapshots | No QMT / MiniQMT / broker API call |
| `dry_run` | Produce write plan, risk result, and broker-lake plan without opening or writing the target root | No real broker lake write |
| `mock` | Drive OMS state changes with local mock broker events | No real broker, account, or exchange interaction |

The following modes remain blocked in CR-015 and move to CR-016 or later authorization gates:

| Mode / stage | CR-015 status | Unblock condition |
|---|---|---|
| `simulation` | blocked / unauthorized | CR-016 simulation Story implemented, CP6 / CP7 PASS, and per-run approval |
| `live_readonly` | blocked / unauthorized | CR-016 live-readonly gate, reconciliation evidence, and per-run approval |
| `small_live` | blocked / unauthorized | CR-016 small-live admission, capital cap, kill switch, and per-run approval |
| `scale_up` | blocked / unauthorized | CR-016 scale-up gate, CR-017 production governance evidence, and explicit user approval |

### 1.2 Required Evidence Before Handoff

CR-015 foundation setup is complete only when these upstream evidence files exist and pass:

| Evidence | Required status | Purpose |
|---|---|---|
| `process/checks/CP7-CR015-S01-qmt-environment-and-interface-spike-VERIFICATION-DONE.md` | PASS | Environment, node role, transport payload, and forbidden broker API boundary |
| `process/checks/CP7-CR015-S02-qmt-broker-adapter-contract-VERIFICATION-DONE.md` | PASS | Offline adapter contract and allowed mode gate |
| `process/checks/CP7-CR015-S03-oms-order-state-machine-VERIFICATION-DONE.md` | PASS | OMS state machine and order intent metadata |
| `process/checks/CP7-CR015-S04-pretrade-risk-gate-VERIFICATION-DONE.md` | PASS | Hard risk gate and adapter-call zero boundary |
| `process/checks/CP7-CR015-S05-broker-lake-schema-and-writer-VERIFICATION-DONE.md` | PASS | Broker lake schema and dry-run writer plan |
| `process/checks/CP7-CR015-S06-target-portfolio-to-order-intent-shadow-mode-VERIFICATION-DONE.md` | PASS | Shadow order intent pipeline and safety counters |
| `process/checks/CP7-CR017-S06-research-qmt-consumer-docs-and-migration-guide-VERIFICATION-DONE.md` | PASS | Research / QMT raw execution boundary and consumer migration guidance |

### 1.3 Forbidden Operations

CR-015 does not authorize:

| Operation | CR-015 counter |
|---|---:|
| QMT / MiniQMT / GUI launch | `0` |
| XtQuant / broker API call | `0` |
| real order submission | `0` |
| real cancel request | `0` |
| real account query | `0` |
| account write | `0` |
| credential read, including `.env`, token, password, cookie, session, private key, account snapshot, or holdings file | `0` |
| real broker lake write | `0` |
| real market-data lake write | `0` |
| provider fetch | `0` |
| current pointer publish | `0` |
| dependency change | `0` |
| simulation activation | `0` |
| live activation | `0` |

## 2. Shadow Run

Shadow mode produces local evidence from target portfolio input and fixture snapshots. It is the default CR-015 runbook path.

### 2.1 Inputs

| Input | Allowed source | Notes |
|---|---|---|
| target portfolio | local fixture or user-reviewed offline object | Must include symbol, target quantity / weight, and strategy metadata |
| policy metadata | CR-017 raw execution contract | `execution_price_policy` must be `raw` |
| cash / position snapshot | fixture snapshot only | Real account snapshot remains blocked |
| risk config | local static config or fixture | No broker query |

### 2.2 Expected Outputs

| Output | Meaning |
|---|---|
| order intent draft | OMS-generated local intent with idempotency metadata |
| risk result | pass / blocked with rule id and reason |
| mock adapter event or blocked adapter result | Local event only |
| state transition audit | OMS transition history |
| broker-lake dry-run plan | Planned path and schema only; no open / mkdir / write |
| safety counters | All forbidden operation counters remain `0` |

### 2.3 Stop Conditions

Stop shadow processing and keep adapter calls at `0` when any condition is true:

| Condition | Stop reason |
|---|---|
| missing `research_adjustment_policy` or `execution_price_policy=raw` | `policy_metadata_missing_or_non_raw` |
| risk result is blocked | `pretrade_risk_blocked` |
| requested mode is not `shadow`, `dry_run`, or `mock` | `stage_not_authorized_in_cr015` |
| any credential path or value is present in input | `credential_access_blocked` |

## 3. Dry-run Plan

Dry-run mode is a planning surface, not a persistence surface.

### 3.1 Allowed Dry-run Artifacts

| Artifact | Allowed content |
|---|---|
| broker lake schema preview | table name, schema version, required columns, redaction status |
| write plan | root label such as `BROKER_LAKE_ROOT`, relative partition, file count estimate |
| reconciliation prerequisite list | expected inputs, threshold names, owner labels |
| failure remediation | blocked reason and next action |

### 3.2 Dry-run Rules

- Do not open, create, truncate, append, rename, delete, or publish any broker lake file.
- Do not print real private paths. Use root labels and relative paths only.
- Do not read `.env`, token, password, cookie, session, account, holdings, private key, or real account snapshot files.
- Do not write into repository `data/**`, `reports/**`, or any real broker lake root.
- Do not treat a dry-run plan as CR-016 authorization.

## 4. Mock Event

Mock mode uses local broker event fixtures to exercise OMS transitions.

### 4.1 Allowed Mock Events

| Event | Purpose |
|---|---|
| `accepted` | Verify accepted order path |
| `partially_filled` | Verify partial fill state |
| `filled` | Verify final fill state |
| `rejected` | Verify rejection handling |
| `timeout` | Verify manual review / timeout branch |
| `unknown` | Verify unknown branch is not silently treated as success |
| `cancel_pending` / `canceled` | Verify cancel state transitions without real cancel |

### 4.2 Mock Event Constraints

Mock events must be local fixtures. They may include synthetic order ids and redacted account labels, but must not include real account numbers, broker session ids, cookies, tokens, passwords, private keys, or real holdings snapshots.

Mock mode does not connect to QMT, MiniQMT, XtQuant, broker services, provider services, data lake production paths, or broker lake production paths.

## 5. Handoff to CR016

CR-016 owns simulation, live_readonly, small_live, scale_up, reconciliation service, monitoring, kill switch, incident playbooks, and per-run authorization. CR-015 only hands over evidence.

### 5.1 Handoff Package

| Package item | Required evidence |
|---|---|
| foundation CP7 set | CR015-S01..S06 and CR017-S06 CP7 PASS |
| S07 runbook boundary | This file and S07 CP6 / CP7 evidence |
| allowed mode summary | `shadow`, `dry_run`, `mock` only |
| forbidden operation counters | All counters in Section 6 remain `0` |
| blocked claim list | simulation / live / real QMT / real broker operations remain blocked |
| CR017 raw execution boundary | QMT intent and broker accounting use raw / broker reference only |

### 5.2 CR016 Prerequisites

Before any CR-016 simulation or live gate can run, the operator must confirm:

| Prerequisite | Required state |
|---|---|
| CR015 foundation | All target Story CP7 PASS, including this S07 runbook boundary |
| CR017 consumer boundary | S01..S06 CP7 PASS when production governance or scale-up is claimed |
| CR016 LLD / CP5 | Approved for the specific CR016 Story |
| CR016 CP6 / CP7 | Implementation and verification PASS for the target gate |
| per-run authorization | Explicit approval with account mode, strategy, date, capital cap, operation scope, approver, rollback, and stop condition |
| reconciliation and kill switch | Required for live_readonly / small_live / scale_up gates |

Missing any prerequisite keeps the requested stage blocked.

### 5.3 CR016-S01 Simulation Admission Checklist

CR016-S01 defines an offline gate contract for `shadow -> simulation`. Passing this checklist means the gate result may be consumed by a later adapter precheck; it does not start a simulation run and does not authorize QMT / MiniQMT, XtQuant, broker API, order, cancel, account query, credential read, broker lake write, provider fetch, lake write, or publish.

| Checklist item | Required evidence | Blocked reason when missing |
|---|---|---|
| Stage transition is exactly `shadow -> simulation` | `current_stage=shadow`, `target_stage=simulation` | `stage_skip_blocked` |
| CR015 foundation is verified | `cr015_verified=true` and CR015-S07 CP7 PASS evidence | `cr015_not_verified` |
| Runbook reference is present | `runbook_ref` pointing to this runbook and CR015-S07 boundary evidence | `runbook_required_missing` |
| CR017 consumer boundary reference is present | CR017-S06 CP7 / migration boundary evidence | `cr017_consumer_boundary_required_missing` |
| Reconciliation policy reference is present | `reconciliation_policy_ref` for the target run profile | `reconciliation_policy_missing` |
| Kill switch readiness reference is present | `kill_switch_readiness_ref` for the target run profile | `kill_switch_readiness_missing` |
| Per-run authorization summary is complete | All fields in Section 5.4 | `authorization_required_missing` |

When any checklist item is missing, the gate result must remain `gate_status=blocked`, `adapter_call_on_block=0`, `real_order_call=0`, `real_cancel_call=0`, `account_query_call=0`, `account_write_call=0`, `credential_read=0`, `real_broker_lake_write=0`, `real_lake_write=0`, `provider_fetch=0`, `publish=0`, `dependency_change=0`, `simulation_run=0`, and `live_activation=0`.

### 5.4 Per-run Authorization Summary Fields

The gate consumes only a redacted authorization summary. It must not contain account numbers, passwords, tokens, cookies, sessions, private keys, real holdings, or private broker paths.

| Field | Required meaning |
|---|---|
| `authorization_id` | Unique approval reference for the run |
| `mode` | Requested mode, such as `simulation` |
| `strategy_id` | Strategy or portfolio owner id |
| `run_id` | Unique run id for audit and rollback matching |
| `target_stage` | Requested stage, such as `simulation` |
| `target_trade_date` | Trade date covered by the approval |
| `capital_limit` | Maximum capital exposure allowed by the approval |
| `order_scope` | Allowed order action scope for this run |
| `approver` | Human approver or governance role |
| `approved_at` | Approval timestamp |
| `expires_at` | Expiration timestamp; stale approvals must not be reused |
| `rollback_plan_ref` | Runbook, incident, or rollback evidence reference |

Missing any field keeps the gate blocked with `authorization_required_missing`. A complete summary is still only an input to the gate; it does not by itself call QMT, submit an order, cancel an order, query an account, write broker lake data, or publish anything.

### 5.5 Runbook Is Not Authorization

Runbook 不等于授权. This file describes required evidence, blocked reasons, and safety counters. It is not a standing approval to run `simulation`, `live_readonly`, `small_live`, `scale_up`, real QMT, real order, real cancel, account query, credential read, real broker lake write, provider fetch, real lake write, or publish.

The only valid CR016-S01 implementation behavior is:

| Gate outcome | Allowed action | Forbidden action |
|---|---|---|
| `gate_status=blocked` | Return blocked reason, missing fields, next required action, and zero safety counters | Adapter call, order, cancel, account query, credential read, lake write, publish, simulation run, or live activation |
| `gate_status=pass` | Allow a later precheck to consume the gate result as offline evidence | Treat this runbook or the pass result as actual broker authorization |

### 5.6 CR016 Activation Runbook Entry

CR016 的 simulation / live activation 文档入口是 [QMT Simulation / Live Activation Runbook](QMT-SIMULATION-LIVE-RUNBOOK.md)。该文件拥有 `simulation`、`live_readonly`、`small_live`、`scale_up` 的启动、审批、异常处理、对账、kill switch、暂停 / 恢复和回滚合同；本 CR015 foundation runbook 只保留 `shadow` / `dry_run` / `mock` 的边界和交接证据。

Simulation 准入入口如下：

| Gate | Required evidence | Boundary |
|---|---|---|
| CR015 foundation evidence | CR015-S01..S07 CP7 PASS or verified state | 只证明 foundation 合同可交接，不启动 simulation |
| CR016-S01 stage gate | `shadow -> simulation` gate PASS with zero safety counters | 只产生离线 gate evidence |
| CR016-S02 reconciliation | pre-market / intraday / post-market reconciliation policy and report candidate | 不查询真实账户，不拉取真实 snapshot |
| CR016-S03 kill switch | heartbeat, stop-new-orders, planned-only cancel plan, recovery gate | 不执行真实撤单，不持久化真实 incident |
| CR016-S04 activation runbook | seven P0 sections, per-run authorization fields, rollback / recovery matrix | 文档合同不自动授权真实运行 |
| per-run authorization | run-specific approval with capital limit, order scope, approver, expiry, rollback ref | 缺失或过期时保持 blocked |

CR015 / CR016 边界必须按下表解释：

| Boundary | CR015 owner | CR016 owner |
|---|---|---|
| Allowed modes | `shadow`, `dry_run`, `mock` | `simulation`, `live_readonly`, `small_live`, `scale_up` gate contracts |
| Runbook role | foundation setup, shadow run, dry-run plan, mock event, handoff evidence | staged activation, approval gate, rollback / recovery, incident handling |
| Authorization | No real operation authorization | Per-run authorization is required but still not sufficient by itself |
| Broker operation | Forbidden, counters remain `0` | Still forbidden unless a later explicitly authorized run and gate allow it |
| Documentation status | Evidence for handoff | Not a standing authorization to run or operate broker paths |

## 6. Safety Counters

| Counter | Required value | Evidence scope |
|---|---:|---|
| `qmt_api_call` | `0` | No QMT / XtQuant / broker API call |
| `real_order_call` | `0` | No real order submission |
| `real_cancel_call` | `0` | No real cancel request |
| `account_query_call` | `0` | No real account query |
| `account_write_call` | `0` | No account mutation |
| `credential_read` | `0` | No `.env`, token, password, cookie, session, private key, real account snapshot, or holdings read |
| `real_broker_lake_write` | `0` | No real broker lake write |
| `real_lake_write` | `0` | No market data lake write |
| `provider_fetch` | `0` | No provider fetch |
| `publish` | `0` | No current pointer or data publish |
| `dependency_change` | `0` | No dependency file or package change |
| `simulation_activation` | `0` | No simulation stage activation |
| `live_activation` | `0` | No live_readonly / small_live / scale_up activation |
| `real_trading_supported_claim_count` | `0` | No real trading availability claim |
| `microstructure_allowed_claim_count` | `0` | No real VWAP / minute / tick / Level2 / order-match allowed claim |

## 7. Blocked Claims Register

| Claim | CR-015 status | Owner for future change |
|---|---|---|
| simulation stage is available | blocked / unauthorized | CR016-S01 / CR016-S04 |
| live_readonly stage is available | blocked / unauthorized | CR016-S05 |
| small_live stage is available | blocked / unauthorized | CR016-S05 |
| scale_up stage is available | blocked / unauthorized | CR016-S06 |
| real QMT or MiniQMT operation | blocked / unauthorized | CR016 with per-run approval |
| real order submission | blocked / unauthorized | CR016 with per-run approval |
| real cancel request | blocked / unauthorized | CR016 with per-run approval |
| real account query | blocked / unauthorized | CR016 with per-run approval |
| credential read | blocked / unauthorized | Never allowed in docs or tests; production runtime must use controlled secret handling |
| real broker lake write | blocked / unauthorized | CR016 broker lake / reconciliation gate |
| real provider fetch | blocked / unauthorized | Data-lake real-run Story with explicit authorization |
| real market-data lake write | blocked / unauthorized | Data-lake real-run Story with explicit authorization |
| publish current pointer | blocked / unauthorized | Explicit publish gate |
| real VWAP execution | blocked / unsupported | Separate source/interface, audit, CP5, and user approval |
| minute execution | blocked / unsupported | Separate source/interface, audit, CP5, and user approval |
| tick execution | blocked / unsupported | Separate source/interface, audit, CP5, and user approval |
| Level2 execution | blocked / unsupported | Separate source/interface, audit, CP5, and user approval |
| order-match execution | blocked / unsupported | Separate source/interface, audit, CP5, and user approval |

## 8. Failure Handling

| Failure | Action |
|---|---|
| forbidden claim appears in README, USER-MANUAL, or this runbook | Fail S07 static test and keep Story out of verification |
| credential-like value appears in docs | Remove value, keep only placeholder or environment variable name |
| CR016 stage wording appears to grant authority | Rewrite as prerequisite / blocked claim |
| missing upstream CP7 evidence | Stop handoff and request meta-po dependency review |
| README / USER-MANUAL shared section conflict | Stop and ask meta-po to serialize shared-file ownership |

## 9. Stop Conditions

Stop the current CR-015 runbook flow when any operator asks for real QMT, real order, real cancel, account query, credential read, real broker lake write, provider fetch, real lake write, publish, simulation, live_readonly, small_live, or scale_up activation.

The correct next action is to route the request to CR-016 or a later explicitly authorized Story / run, not to extend this foundation runbook.
