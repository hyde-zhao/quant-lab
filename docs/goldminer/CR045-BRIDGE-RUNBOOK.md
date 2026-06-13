---
change_id: "CR-045"
scope: "Goldminer Windows Bridge L2 skeleton / fixture / static"
status: "cp6-implemented"
runtime_authorization: "L1/L2 only"
real_runtime_authorized: false
---

# CR045 Goldminer Bridge Runbook

## 当前交付范围

CR045 本轮只交付离线工程资产：

| 范围 | 当前状态 | 证据入口 |
|---|---|---|
| Windows bridge security boundary | skeleton-only | `engine/goldminer_bridge_contract.py` |
| WSL / Linux bridge client contract | fixture transport only | `engine/goldminer_bridge_client.py` |
| Readonly probe skeleton | blocked-first | `engine/goldminer_bridge_probe.py` |
| Redaction / no-operation validation | static + fixture | `tests/test_cr045_goldminer_no_operation_static.py` |
| 用户后续授权说明 | docs only | 本文件 |

当前所有真实能力 flag 必须保持 false：`real_broker_enabled=false`、`readonly_probe_ready=false`、`simulation_ready=false`、`live_ready=false`、`real_readonly_verified=false`。

## 不授权项

CP5、CP6、CP7 或 CP8 通过都不授权以下动作：

| 动作 | 当前状态 | 处理方式 |
|---|---|---|
| 读取 `.env` / `.env.*` | not-authorized | 停止并交回 meta-po |
| 读取 token / account_id / 账号 / 密码 | not-authorized | 停止并交回 meta-po |
| 读取 session / cookie / private key | not-authorized | 停止并交回 meta-po |
| 启动 Windows bridge runtime | not-authorized | 需要 L3 独立授权 |
| 登录 Goldminer 或 broker | not-authorized | 需要 L3 独立授权 |
| 连接 Goldminer 或 broker | not-authorized | 需要 L3 独立授权 |
| 查询 account state | not-authorized | 需要 L4 独立授权 |
| 查询 cash / funds | not-authorized | 需要 L4 独立授权 |
| 查询 position | not-authorized | 需要 L4 独立授权 |
| 查询 order | not-authorized | 需要 L4 独立授权 |
| 查询 fill / execution report | not-authorized | 需要 L4 独立授权 |
| submit order | not-authorized | 需要 L5 独立授权 |
| cancel order | not-authorized | 需要 L5 独立授权 |
| 启动 simulation runtime | not-authorized | 需要 L5 独立授权 |
| 启动 live runtime | not-authorized | 需要 L5 独立授权 |
| provider fetch | not-authorized | 新 CR 或独立 gate |
| lake write | not-authorized | 新 CR 或独立 gate |
| catalog publish | not-authorized | 新 CR 或独立 gate |

## L2 可执行验证

允许的本地验证只包括 fixture/static：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' uv run --python 3.11 pytest -q tests/test_cr045_goldminer_bridge_contract.py tests/test_cr045_goldminer_bridge_client.py tests/test_cr045_goldminer_readonly_probe.py tests/test_cr045_goldminer_no_operation_static.py
git diff --check
```

这些命令不得替代真实运行授权，也不得被解释为已经验证真实 Goldminer readonly、simulation 或 live 能力。

## 后续授权 Gate

| Gate | 目标 | 进入条件 | 当前 CR045 是否授权 |
|---|---|---|---|
| L3 Windows credential local setup / bridge health | 用户在 Windows 本地自主管理凭据和 runtime；Agent 不读取真实值 | meta-po 发起独立 `runtime_authorization`，包含操作者、时间窗、kill switch 和证据路径 | 否 |
| L4 readonly probe | 只读查询 cash / position / order / fill / account state 的脱敏证据 | L3 已通过，且 L4 独立授权明确允许只读动作 | 否 |
| L5 submit / cancel / simulation / live | 交易或仿真运行 | L3/L4 已通过，且 L5 高风险授权、订单白名单、回滚和对账计划齐备 | 否 |

用户要求“现在连接”“查一下账户”“读持仓”“下单”“撤单”“跑 simulation/live”“读取配置或凭据”时，当前实现必须停止在 L2，交回 meta-po 发起对应 gate 或新 CR。

## 敏感字段与证据

允许输出：

| 类型 | 示例 |
|---|---|
| 字段名 | `token`、`account_id`、`session` |
| 字段类别 | `credential`、`private_key`、`broker_account` |
| 脱敏占位 | `REDACTED` |
| 计数 | `count=0`、`present=true` |
| blocked reason | `per_run_authorization_missing`、`goldminer_readonly_query_not_authorized` |

禁止输出任何真实字段值、真实账号值、真实 session、cookie、private key、订单引用、成交引用或 broker payload。

## 关闭语义

未获得 L3/L4 授权时，CR045 只能关闭为以下之一：

| 结论 | 含义 |
|---|---|
| `readonly-bridge-skeleton-ready` | L2 skeleton、fixture、static 和 runbook 已准备好，但没有真实只读证据。 |
| `blocked-by-runtime-authorization` | 工程资产可用，但用户未授权真实 runtime 或 readonly probe。 |
| `not-recommended` | 当前风险或平台条件不适合继续推进。 |

不得把 L2 fixture/static 结果表述为真实账户、真实只读、simulation 或 live 能力已可用。

## CP7 / CP8 复核重点

| 维度 | 复核点 |
|---|---|
| 授权 | 所有真实能力 flag 为 false，所有真实动作仍 not-authorized。 |
| 运行边界 | 未启动 Windows bridge runtime，未连接 Goldminer，未打开真实网络 transport。 |
| SDK 边界 | `engine/goldminer_bridge_*` 未导入 `gm` 或 `gmtrade`。 |
| 凭据边界 | 未读取 `.env` / `.env.*`，未输出真实 token、account_id、账号、密码、session、cookie 或 private key。 |
| no-operation | forbidden operation counters 全部为 0。 |
| 文案 | CP8 结论不宣称真实只读、simulation 或 live ready。 |
