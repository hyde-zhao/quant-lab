# QMT Simulation / Live Activation Runbook

本文件是 CR-016 staged activation 的兼容入口。当前可操作的多因子模拟盘入口是 [USER-MANUAL.md](USER-MANUAL.md) 的 runner 模块，gateway 配置见 [QMT-GATEWAY-INSTALL.md](QMT-GATEWAY-INSTALL.md)，授权模板见 [reference/RUNNER-QMT-AUTHORIZATION.md](reference/RUNNER-QMT-AUTHORIZATION.md)。

Runbook、incident playbook、README、USER-MANUAL、CP5、CP6/CP7、Story verified 或文档存在均不自动授权 `simulation`、`live`、`small_live`、`scale_up`。文档合同不自动授权真实运行。

非交易窗口 readiness（`preflight-only` / `plan-only` / `fixture` / `reconcile-only`）只验证 operator spec、策略准入包、evidence schema、异常恢复矩阵和稳定性窗口定义；不读取 env、不构造 QMT client、不启动 gateway、不读取凭据、不连接账户、不提交或撤单。它不等于 runtime authorization，也不授权 `simulation`、`live`、`small_live` 或 `scale_up`。

| Counter | Current value |
|---|---:|
| `default_real_operation_authorization_claim` | `0` |

## P0-1 启动 / Start Gate

启动前必须确认：

| Gate | Required |
|---|---|
| runbook readiness | 本 runbook 可读，gateway 文档可读。 |
| authorization | per-run authorization 未过期。 |
| runtime identity | `mode=simulation`、profile 匹配。 |
| gateway | health / capabilities / positions 通过。 |

## P0-2 审批 / Per-run Approval Gate

Per-run authorization 摘要字段必须完整：

| Field | Required |
|---|---|
| `authorization_id` | yes |
| `mode` | yes |
| `strategy_id` | yes |
| `run_id` | yes |
| `stage` | yes |
| `capital_limit` | yes |
| `order_scope` | yes |
| `approver` | yes |
| `approved_at` | yes |
| `expires_at` | yes |
| `rollback_plan_ref` | yes |

## P0-3 异常处理 / Exception Handling

| Exception | Action |
|---|---|
| `authorization_missing_or_expired` | stop new run, refresh authorization. |
| `heartbeat_missed` | stop operator, check gateway. |
| `reconciliation_threshold_breach` | manual takeover. |
| `broker_ack_error` | stop submit, inspect broker state. |
| `kill_switch_triggered` | freeze automation. |
| `manual_stop_request` | stop gateway and operator. |
| `cr017_or_maturity_boundary_missing` | keep scale_up blocked. |

## P0-4 对账 / Reconciliation

Reconciliation gate 至少要求 order、fill、position、asset、cash 和 broker refs 的脱敏摘要一致。差异未闭环前不得恢复自动运行。

## P0-5 Kill Switch

Kill switch 在以下条件触发：unknown order、cancel blocked、reconciliation diff、session expired during execution、manual stop request。触发后 rollback target 必须进入 blocked 状态。

## P0-6 暂停 / 恢复

暂停后恢复必须满足：`manual_takeover_record=recorded`、reconciliation pass、authorization valid、gateway session fresh、positions redaction pass。

## P0-7 回滚 / Rollback

回滚只允许把状态退回 blocked 或 manual review；不得把 blocked 状态直接改成 pass。

## Rollback / Recovery Matrix

| incident type | stage | owner | action | rollback target | recovery gate |
|---|---|---|---|---|---|
| authorization_missing_or_expired | simulation | approver | refresh per-run authorization | simulation_blocked | authorization valid |
| heartbeat_missed | simulation | trading_node_owner | stop gateway and rerun health check | gateway_blocked | health and capabilities pass |
| reconciliation_threshold_breach | simulation | research_owner | record diff and manual takeover | reconciliation_blocked | reconciliation pass |
| broker_ack_error | simulation | trading_node_owner | stop submit and inspect order state | execution_blocked | unknown count zero |
| kill_switch_triggered | simulation | approver | freeze automation | kill_switch_blocked | recovery approval |
| manual_stop_request | simulation | trading_node_owner | stop operator and gateway | manual_stop_blocked | operator stopped |
| cr017_or_maturity_boundary_missing | scale_up | research_owner | keep scale-up disabled | scale_up_blocked | maturity gate approved |

## CR019-S10 Bridge Boundary Addendum

QMT C/S bridge 文档只说明 endpoint、pairing/HMAC、run gate、fallback 和 No-real-operation 边界。它仍需 per-run authorization、reconciliation 和 kill-switch；fallback / signed file candidate 只允许 fail-closed 和 manual dry-run candidate。
