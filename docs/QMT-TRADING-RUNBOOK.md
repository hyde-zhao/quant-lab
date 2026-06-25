# QMT Trading Foundation Runbook

本文件是 CR-015 QMT foundation 的兼容入口。新用户可先读 [components/QMT-GATEWAY.md](components/QMT-GATEWAY.md)、[components/RUNNER.md](components/RUNNER.md) 和 [scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md](scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md)。

## 1. Setup Boundary

CR-015 只允许 `shadow`、`dry_run`、`mock` 三类离线 / fixture 操作。它不授权 simulation、live_readonly、small_live、scale_up、真实 QMT、真实发单、撤单、账户查询、凭据读取、真实 broker lake 写入、真实抓取、真实 lake 写入或 publish。

## 2. Shadow Run

`shadow` 用本地 target portfolio、policy metadata 和 fixture snapshot 生成 order intent、risk result、state transition 和 audit summary。

检查：

| 检查项 | 必须值 |
|---|---|
| QMT API call | `0` |
| account query | `0` |
| real order | `0` |

## 3. Dry-run Plan

`dry_run` 只查看 broker lake schema、write plan 和 reconciliation prerequisites。它不打开、不创建、不写真实 broker lake。

## 4. Mock Event

`mock` 使用本地 mock broker event 验证 OMS 状态变化，不触达真实账户、柜台、交易节点或真实 broker event。

## 5. Handoff to CR016

CR016 承接 staged activation runbook。任何进入 simulation、live_readonly、small_live 或 scale_up 的动作都必须有 per-run authorization、stage gate、risk gate、reconciliation gate、kill switch 和 rollback plan。

## 6. Safety Counters

| Counter | Current value |
|---|---:|
| `qmt_api_call` | `0` |
| `real_order_call` | `0` |
| `real_cancel_call` | `0` |
| `account_query_call` | `0` |
| `account_write_call` | `0` |
| `credential_read` | `0` |
| `real_broker_lake_write` | `0` |
| `real_lake_write` | `0` |
| `provider_fetch` | `0` |
| `publish` | `0` |
| `dependency_change` | `0` |
| `simulation_activation` | `0` |
| `live_activation` | `0` |
| `real_trading_supported_claim_count` | `0` |
| `microstructure_allowed_claim_count` | `0` |
