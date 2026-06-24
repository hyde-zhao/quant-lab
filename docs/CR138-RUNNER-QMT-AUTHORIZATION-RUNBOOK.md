# CR138 Runner / QMT Gateway Authorization Runbook

## Current Boundary

CR138 当前实现范围仅允许本地 fixture / contract / static guardrail / documentation validation。默认不授权真实 runtime、QMT、MiniQMT、XtQuant、gateway 启动、端口绑定、凭据读取、账户 / 行情 / 订单真实查询、submit/cancel、simulation/live、NAS、provider/lake/catalog 或 Git remote 写入。

Gateway health、capabilities、Runner preflight、OpsSummary、BatchOpsSummary、ChangePlan dry-run 和 fixture pass 都不等于 runtime authorization。

## Runtime Authorization Request Template

| Field | Required | Description |
|---|---|---|
| action_scope | yes | One of `readonly_runtime`, `market_readonly`, `account_readonly`, `order_write`, `submit_cancel`, `simulation`, `live`, `gateway_start`, `port_bind`, `nas_access`, `provider_lake_catalog`, `git_remote_write`. |
| time_window | yes | Exact start and end time for the authorized action. |
| environment_ref | yes | Redacted machine / environment reference; no secret value. |
| credential_policy | yes | Secret source and redaction plan; no plaintext credential. |
| data_redaction | yes | Fields that must be redacted before evidence capture. |
| rollback_plan | yes | How to stop, revert, or invalidate the action. |
| audit_ref | yes | Gate, operator, reason, and evidence destination. |
| allowed_commands | yes | Exact commands or UI actions allowed in the window. |
| forbidden_commands | yes | Explicitly forbidden actions that remain blocked. |

## Scope Separation

`readonly_runtime` may verify process visibility only. It does not grant account, market, order, submit, cancel, simulation, or live permissions.

`account_readonly` may read redacted account summaries only after a separate gate. It does not grant order submit/cancel.

`market_readonly` may read or subscribe to market data only after a separate gate. It does not grant account or order access.

`order_write`, `submit_cancel`, `simulation`, and `live` are separate high-risk scopes. Approval for one does not imply another.

## Evidence Rules

Evidence must use redacted references, no raw payload, no account id, no token, no secret, no private key, no session cookie, and no raw broker logs. If redaction fails, the run is blocked and evidence must not be published.
