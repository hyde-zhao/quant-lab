# CR043 Goldminer Adapter Spike 结论建议

生成时间：2026-06-11T08:36:20+08:00  
状态：ready-for-CP8-review  
推荐结论：`NEEDS_ACCOUNT_PERMISSION`

## 结论摘要

CR043 已达到工程事实 Spike 的当前授权目标，但不应关闭为完全 `PASS`。

推荐将 CR043 关闭结论定为：`NEEDS_ACCOUNT_PERMISSION`。

理由：

- L1 官方公开资料与 L2 隔离 SDK 静态核对显示，`gm` / `gmtrade` 均存在可映射到 CR042 `BrokerAdapter` 的候选交易、撤单、资金、持仓和成交接口。
- `gm` 在 Python 3.11 隔离环境可静态 import，更适合作为当前项目同 runtime 的主选候选。
- `gmtrade` 在 Python 3.10 隔离环境可静态 import，但公开 wheel 不支持 Python 3.11，需作为 fallback / 独立 runtime 风险处理。
- 资金、持仓、委托、成交字段结构、账号权限、错误语义和仿真账户可用性无法在当前不授权边界内完全验证。
- 当前仍不授权 token / account / login / connect / account query / order / cancel / simulation/live，因此不能把 CR043 结论写成完全可运行、可仿真或可交易。

## 证据输入

| 证据 | 路径 | 结论 |
|---|---|---|
| 工程事实报告 | `process/research/cr043_goldminer_adapter_spike/ENGINEERING-FEASIBILITY.md` | `gm` Python 3.11 静态核对成功；`gmtrade` Python 3.10 静态核对成功，Python 3.11 无 wheel；真实运行不授权。 |
| 接口映射矩阵 | `process/research/cr043_goldminer_adapter_spike/INTERFACE-MAPPING-MATRIX.md` | CR042 BrokerAdapter 合同可映射到 `gm` / `gmtrade` 静态候选接口，但真实字段和权限仍依赖账号 / 官方结构事实。 |
| CP2 审查 | `process/checkpoints/CP2-CR043-REQUIREMENTS-BASELINE.md` | 用户已批准继续 CR043、保持 L3/L4 不授权、CR044 不启动。 |
| CP3 审查 | `process/checkpoints/CP3-CR043-HLD-REVIEW.md` | 用户已批准 `gm` 主选 / `gmtrade` fallback、不写真实 adapter、capability 仅为静态候选能力。 |

## 关闭结论判定

| 候选结论 | 判定 | 原因 |
|---|---|---|
| `PASS` | 不采用 | 当前没有账号权限、登录、查询或仿真运行证据，不能声明完全通过。 |
| `PASS_WITH_UNKNOWN_RISKS` | 不作为主推荐 | 虽然 SDK 静态事实支持继续，但未知项不是普通风险，而是账号权限和真实字段结构前置条件。 |
| `NEEDS_ACCOUNT_PERMISSION` | 推荐 | 接口存在且可映射，但资金 / 持仓 / 委托 / 成交字段、账号权限和仿真账户可用性必须在后续受控授权中核对。 |
| `BLOCKED_BY_DOCS` | 不采用 | 当前公开资料和 SDK 静态核对足以形成接口映射候选，不是文档完全阻塞。 |
| `NOT_RECOMMENDED` | 不采用 | 当前未发现 SDK / Python runtime / no-operation guard 风险高到不建议继续。 |

## CR044 建议

CR043 关闭为 `NEEDS_ACCOUNT_PERMISSION` 后，CR044 仍不应自动启动。

若用户后续决定启动 CR044，建议 CR044 的第一步不是下单，而是受控账号 / 仿真权限准入：

1. 单独 CP2 决策授权范围。
2. 单独凭据处理方案，不在对话、文档或日志记录 token / account / password / session。
3. 先做最小只读权限核对或官方结构字段核对。
4. 下单 / 撤单 / simulation/live 必须作为更后面的逐 run 授权项。

## 不授权范围

本结论不授权以下动作：

- 读取 `.env`、token、账号、密码、session、cookie、密钥或终端配置。
- 登录掘金。
- 连接 broker。
- 查询资金、持仓、委托、成交。
- 下单、撤单、改单。
- 启动 simulation/live。
- provider fetch、lake write、catalog publish。
- 自动启动 CR044。

## 推荐 CP8 决策

| 决策 ID | 推荐方案 |
|---|---|
| DQ-CP8-CR043-01 | 接受 CR043 以 `NEEDS_ACCOUNT_PERMISSION` 作为 Spike 关闭结论。 |
| DQ-CP8-CR043-02 | 接受 CR044 保持 not-started；若要启动必须另起正式 CR 和逐 run 授权。 |
| DQ-CP8-CR043-03 | 接受所有真实 broker / 凭据 / 账户 / 交易 / simulation/live 动作继续不授权。 |
