# Runner / QMT Gateway Authorization Runbook

本文件是 runner / QMT 授权边界的 canonical reference。旧 `docs/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md` 已归档到 [../legacy/archive/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md](../legacy/archive/CR138-RUNNER-QMT-AUTHORIZATION-RUNBOOK.md)；新用户不应再把 CR 编号文档作为入口。

## Current Boundary

当前默认不授权真实 runtime、QMT、MiniQMT、XtQuant、gateway 启动、端口绑定、凭据读取、账户 / 行情 / 订单真实查询、submit/cancel、simulation/live、NAS、provider/lake/catalog 或 Git remote 写入。只有用户为单次运行提供明确 runtime authorization 时，才允许在该时间窗口内执行授权清单中的命令。

Gateway health、capabilities、Runner preflight、OpsSummary、BatchOpsSummary、ChangePlan dry-run 和 fixture pass 都不等于 runtime authorization。

当前 RUNNER-QMT-SIMULATION-MULTIFACTOR 的工程入口已具备 simulation operator，但这不等于 QMT、broker 或 runtime 验证通过。真实运行仍以逐次授权、Windows gateway session、stage/risk/kill-switch gate 和 P4 对账结果为准。授权 simulation 不包含 `small_live` 或 `live`。

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

For the multifactor simulation operator, the minimal allowed simulation scope is:

| Scope | Allowed only when explicitly listed | Still forbidden |
|---|---|---|
| `gateway_start` / `port_bind` | Start the Windows gateway for the approved time window. | Public exposure, unknown port, background persistence after the window. |
| `account_readonly` | Read redacted simulation account position summary. | Raw account payload, raw positions, fund details. |
| `simulation` | Run the authorized P1-P4 simulation operator. | `small_live`, `live`, scale-up, production trading. |
| `submit_cancel` | Submit and cancel only the generated simulation order intents. | Manual free-form orders, non-run orders, unsupported endpoint calls. |

The allowed command list should reference:

```text
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics ...
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve ...
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions ...
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py ...
```

The forbidden command list must include `small_live`, `live`, unredacted broker logs, raw account dump, raw order report dump, provider fetch, lake write, broker lake write, publish, unknown QMT endpoint and Git remote write unless separately approved.

## Evidence Rules

Evidence must use redacted references, no raw payload, no account id, no token, no secret, no private key, no session cookie, and no raw broker logs. If redaction fails, the run is blocked and evidence must not be published.

For RUNNER-QMT-SIMULATION-MULTIFACTOR evidence, only the following data classes may be persisted under `process/evidence` or `process/checks`:

| Data class | Allowed form |
|---|---|
| account / position | digest, bucket, count, `instrument_ref`, redaction status |
| target portfolio | target summary and instrument refs only |
| order plan | order counts, side counts, turnover summary, intent refs |
| submit / cancel | accepted / blocked / unknown counts and redacted refs |
| reconciliation | pass / blocked status, difference counts, digest refs |
| runtime authorization | authorization ref, stage, run id, expiry summary |

Raw payload, raw account id, raw symbol, raw broker order ref, token, password, HMAC secret, raw signature, session cookie, private key, precise holdings and fund detail are not allowed in evidence.

## User-Facing Documents

| Document | Purpose |
|---|---|
| `docs/USER-MANUAL.md` | Operator steps, stop/check procedure and typical user case. |
| `docs/QMT-GATEWAY-INSTALL.md` | Windows gateway env, start, health, capabilities, query and stop. |
| `docs/QMT-C-S-BRIDGE-RUNBOOK.md` | C/S bridge endpoint, HMAC, scope and evidence boundary. |
| `process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md` | Process runbook and audit checklist. |
