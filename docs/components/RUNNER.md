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
| [../USER-MANUAL.md](../USER-MANUAL.md) | 用户手册中的手动运行指南。 |
| `scripts/run_qmt_multifactor_simulation_operator.py` | 一次性 simulation operator。 |
| `process/runbooks/RUNNER-QMT-SIMULATION-MULTIFACTOR-STRATEGY-RUNTIME-RUNBOOK-2026-06-25.md` | 过程 runbook。 |

## 3. 检查清单

| 检查 | 必须满足 |
|---|---|
| strategy import | 策略包字段完整，未声明 live-ready。 |
| authorization | 本次 run 的 authorization_ref 有效，只覆盖 simulation。 |
| gateway | health / capabilities / positions 均通过。 |
| order plan | risk gate pass 或 no-op。 |
| execution | unknown_count 为 0；cancel_after_submit 按策略执行。 |
| reconciliation | 差异闭环；失败进入 manual takeover 或 kill-switch 候选。 |
