# QMT Incident Playbook

本文件定义 QMT gateway 和 simulation operator 的人工接管入口。它不授权启动 gateway、不授权发单、不授权撤单。

## 1. Stage Coverage

| stage | incident handling scope | recovery owner | rollback target | default operation status |
|---|---|---|---|---|
| `shadow` | fixture / mock incident only | research_owner | shadow_only | blocked unless explicitly allowed |
| `simulation` | gateway, query, submit, cancel, recon incident | trading_node_owner | simulation_blocked | blocked unless per-run authorization passes |
| `live_readonly` | readonly incident candidate | trading_node_owner | live_readonly_blocked | later-gated |
| `small_live` | small capital incident candidate | approver | small_live_blocked | later-gated |
| `scale_up` | scale-up incident candidate | approver | scale_up_blocked | later-gated |

## 2. Incident Playbook

| incident type | trigger | immediate action | owner | evidence required | recovery gate | rollback target |
|---|---|---|---|---|---|---|
| heartbeat_fail | gateway heartbeat missed | stop operator and check gateway | trading_node_owner | health / capabilities result | gateway healthy | simulation_blocked |
| risk_blocked | P2 or stage/risk gate blocked | do not submit | research_owner | risk result ref | risk pass | shadow_only |
| recon_diff | reconciliation threshold breach | manual takeover | research_owner | diff summary and refs | reconciliation pass | simulation_blocked |
| manual_trigger | human stop request | stop operator and gateway | approver | manual stop record | approver release | simulation_blocked |
| recovery_required | prior incident unresolved | keep automation frozen | trading_node_owner | incident ref and takeover record | recovery gate pass | simulation_blocked |

## 3. Unsupported Execution Claims

The following execution claims remain blocked / unsupported:

| Claim | Status |
|---|---|
| real_vwap_execution | blocked / unsupported |
| minute_execution | blocked / unsupported |
| tick_execution | blocked / unsupported |
| Level2_execution | blocked / unsupported |
| order_match_execution | blocked / unsupported |

## 4. Recovery Gate

| condition | required value |
|---|---|
| reconciliation_status | pass |
| manual_takeover_record | recorded |
| kill_switch_state | ready_or_not_applicable |
| authorization_status | valid_or_refreshed |
| rollback_target | blocked_state_recorded |

Recovery requires `manual_takeover_record=recorded`, `reconciliation_status=pass`, valid `authorization_status`, known `kill_switch_state`, and explicit `rollback_target`.

## 5. Safety Counters

| Counter | Current value |
|---|---:|
| `qmt_api_call` | `0` |
| `real_order_call` | `0` |
| `real_cancel_call` | `0` |
| `account_query_call` | `0` |
| `account_write_call` | `0` |
| `credential_read` | `0` |
| `real_broker_operation` | `0` |
| `real_broker_lake_write` | `0` |
| `real_lake_write` | `0` |
| `provider_fetch` | `0` |
| `publish` | `0` |
| `simulation_run` | `0` |
| `live_run` | `0` |
| `small_live_run` | `0` |
| `scale_up_run` | `0` |
| `real_snapshot_pull` | `0` |
| `incident_persisted` | `0` |
| `default_real_operation_authorization_claim` | `0` |
| `unsupported_execution_claim_unblocked` | `0` |
| `sensitive_raw_value_output` | `0` |

## 8. CR019-S10 Documentation Boundary Addendum

QMT C/S bridge addendum covers admission blocked、auth failed、endpoint blocked、run gate blocked、gateway unavailable、signed file candidate 和 fallback blocked。所有路径 fail closed；No-real-operation counters remain zero until a separate per-run authorization and stage gate pass.
