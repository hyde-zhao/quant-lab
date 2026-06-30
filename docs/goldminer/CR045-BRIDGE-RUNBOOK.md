# CR045 Goldminer Bridge Runbook

本文件只描述 Goldminer bridge 的离线合同边界。它不授权 Goldminer login/connect，不授权 runtime start，不授权 simulation/live，不读取 token、secret、password、cookie、session、private key、account_id 或 broker 原始信息。

## Authorization Boundary

当前 CR045 仅允许静态合同、fixture 和 no-operation probe。任何真实 Goldminer runtime、真实只读连接、账户查询、下单、撤单、provider fetch、lake write、broker lake write 或 publish 都需要独立 CR、CP5 和逐次授权。

## No-Operation Counters

| Counter | Current value |
|---|---:|
| `runtime_start` | `0` |
| `login_connect` | `0` |
| `account_query` | `0` |
| `order_submit` | `0` |
| `order_cancel` | `0` |
| `credential_read` | `0` |
| `provider_fetch` | `0` |
| `lake_write` | `0` |
| `broker_lake_write` | `0` |
| `publish` | `0` |

## Runtime Claim Boundary

`simulation`、`live`、Goldminer bridge readonly 和 runtime start 当前均保持 blocked。文档存在、Story verified 或 fixture pass 都不是 standing approval。
