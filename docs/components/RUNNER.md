# 组件说明：Runner

Runner 负责把策略准入包或 operator spec 转成一次受控运行，按 P1-P4 完成目标组合、订单计划、simulation submit/cancel 和对账。Runner 不负责长期保存原始账户、原始订单或凭据。

## 1. 运行阶段

| 阶段 | 说明 | 输出 |
|---|---|---|
| P0 | runtime profile、安全身份、授权和 gateway 检查。 | blocked/pass 和 redacted refs。 |
| P1 | 多因子目标组合生成。 | target portfolio summary。 |
| P2 | 结合当前持仓和风险快照生成订单计划。 | order plan summary。 |
| P3 | 调用 simulation gateway submit/cancel。 | execution summary。 |
| P4 | 对账和 manual takeover 判定。 | reconciliation summary。 |

## 2. 操作入口

| 入口 | 用途 |
|---|---|
| [../scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md](../scenarios/MULTIFACTOR-SIMULATION-RUNNER-OPERATION.md) | 完整运行案例。 |
| [../scenarios/NON-TRADING-WINDOW-RUNNER-READINESS.md](../scenarios/NON-TRADING-WINDOW-RUNNER-READINESS.md) | 非交易窗口 fixture / preflight / plan / reconcile 准备。 |
| [../USER-MANUAL.md](../USER-MANUAL.md) | 用户手册中的手动运行指南。 |
| `scripts/run_qmt_multifactor_simulation_operator.py` | 一次性 simulation operator。 |
| `process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md` | 过程 runbook。 |

## 3. 非交易窗口模式

| mode | 是否触达 runtime | 用途 |
|---|---|---|
| `preflight-only` | 否 | 检查 operator spec 必填字段和 evidence 输出路径。 |
| `plan-only` | 否 | 生成 P1 target 和 P2 order plan，不进入 P3。 |
| `fixture` | 否 | 跑 P1、P2 和 P4 fixture reconciliation，P3 为 `no_op`。 |
| `reconcile-only` | 否 | 复核 P4 fixture 对账合同。 |
| `runtime` | 是 | 逐次授权后连接真实 simulation gateway。 |

当前已冻结的非交易窗口正式输入：

| 对象 | 路径 | 状态 |
|---|---|---|
| StrategyAdmissionPackage | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json` | 仅用于离线 readiness，不授权 runtime |
| operator spec | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json` | 不含凭据、账号或 broker ref |
| completion check | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-NON-TRADING-WINDOW-COMPLETION-2026-06-25.md` | 四个离线模式均 `pass` |

## 4. 当前 simulation readiness 状态

| 项目 | 状态 | 说明 |
|---|---|---|
| runtime stability window | `5/5 pass` | 已完成 after-restart、r3、r4、r5、r6 成功运行汇总。 |
| readiness decision | `READY_WITH_RISK` | 用户已接受；3 trading days 观察缺口作为风险保留，不阻塞 simulation readiness。 |
| runtime input policy | `POLICY_DEFINED` | private overlay、builder、字段边界、脱敏 evidence 边界已固化。 |
| gateway lifecycle policy | `POLICY_DEFINED` | Windows gateway 启停、重启、WSL/Windows 同步和 P0/P0.5 复验规则已固化。 |
| live readiness | `NOT_READY` | `small_live` / `live` 仍 deferred，必须独立 CR。 |

Runner 当前具备受控人工授权 simulation 模拟盘运行入口条件；不具备长期自动化 / 无人值守模拟盘的完整运营条件。后者还需要独立实现运行日历、自动 preflight、健康监控、日报和 incident 自动收敛。

## 5. 检查清单

| 检查 | 必须满足 |
|---|---|
| strategy import | 策略包字段完整，未声明 live-ready。 |
| authorization | 本次 run 的 authorization_ref 有效，只覆盖 simulation。 |
| gateway | health / capabilities / positions 均通过。 |
| order plan | risk gate pass 或 no-op。 |
| execution | unknown_count 为 0；cancel_after_submit 按策略执行。 |
| reconciliation | 差异闭环；失败进入 manual takeover 或 kill-switch 候选。 |

非交易窗口冻结的稳定性窗口标准曾设定为 `5` 次真实 simulation run、覆盖 `3` 个交易日。当前 5/5 count 已完成并被接受为 `READY_WITH_RISK`；如未来要求升级为严格 `READY`，可以补第三个交易日观察。离线 fixture pass 只证明合同和 evidence schema 可用，不计入真实 runtime 稳定性窗口。
