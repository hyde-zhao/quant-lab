# 场景案例：多因子策略模拟盘运行

本案例面向模拟盘操作者，目标是把研究输出的策略准入包导入 runner，通过 QMT gateway 运行一次 simulation operator，并完成检查、停止和对账。本案例只覆盖 `simulation`，不覆盖 `small_live` 或 `live`。

## 当前入口状态

截至 2026-06-26，Runner 已具备受控人工授权 simulation 模拟盘运行入口条件：

| 项目 | 状态 | 证据 |
|---|---|---|
| stability window | `5/5 pass` | `process/evidence/RUNNER-QMT-SIMULATION-MULTIFACTOR-STABILITY-WINDOW-SUMMARY-2026-06-26-r6.json` |
| readiness | `READY_WITH_RISK`，已接受 | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-SIMULATION-OPERATIONAL-READINESS-CLOSURE-2026-06-26.md` |
| runtime input policy | `POLICY_DEFINED` | `process/policies/RUNNER-QMT-SIMULATION-MULTIFACTOR-RUNTIME-INPUT-GATEWAY-LIFECYCLE-POLICY-2026-06-26.md` |
| gateway lifecycle policy | `POLICY_DEFINED` | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-OPS-POLICY-CLOSURE-2026-06-26.md` |

入口条件不等于自动运行授权。每一次 simulation runtime 都必须重新取得逐次 authorization，并从 P0 health / identity、P0 capabilities 和 P0.5 signed readonly 开始。长期自动化 / 无人值守模拟盘仍未就绪。

## 大步骤 0：非交易窗口准备

### 0.1 运行本地 readiness 检查

在交易窗口前先执行 [NON-TRADING-WINDOW-RUNNER-READINESS.md](NON-TRADING-WINDOW-RUNNER-READINESS.md)。该步骤只验证本地 operator 输入、策略准入包、evidence schema、异常恢复矩阵和稳定性窗口定义；不触达 QMT runtime。

截至 `2026-06-25`，非交易窗口正式输入和完成记录为：

| 对象 | 路径 |
|---|---|
| StrategyAdmissionPackage | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json` |
| operator spec | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json` |
| completion check | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-NON-TRADING-WINDOW-COMPLETION-2026-06-25.md` |

交易窗口内仍必须重新确认 runtime authorization、真实 current positions 脱敏摘要、gateway health / capabilities 和 manual takeover readiness；非交易窗口 `pass` 不等于 runtime 授权。

小步骤：

1. 使用 `--mode preflight-only` 校验 operator spec 和策略准入包。
2. 使用 `--mode plan-only` 生成本地订单计划 evidence。
3. 使用 `--mode fixture` 跑完本地 P1-P4 fixture 链路。
4. 使用 `--mode reconcile-only` 验证对账 evidence schema。
5. 检查 `operator-evidence.json` 和 `operator-evidence.index.json` 已写入指定 evidence 目录。

检查：

| 检查项 | 通过标准 |
|---|---|
| runtime 授权 | `runtime_authorization_granted=false`。 |
| runtime 触达 | `runtime_touched=false`，未读取 env，未构造 QMT client，未启动 gateway，未读取凭据。 |
| 订单动作 | `submitted_count=0`、`cancelled_count=0`。 |
| evidence | 原始账户、原始订单、原始成交、原始持仓和 secret 均未保存；evidence index 只保留摘要、digest、bucket 和 refs。 |
| 授权边界 | 非交易窗口 readiness 不等于 runtime authorization，不授权真实 simulation gateway、`small_live` 或 `live`。 |

## 大步骤 1：确认运行授权

### 1.1 准备授权材料

小步骤：

1. 确认本次只运行 `simulation`。
2. 准备 `<runtime-authorization-ref>`。
3. 明确授权窗口、操作者、run id、strategy id、资金上限和回滚计划。
4. 明确 forbidden commands：`small_live`、`live`、未知 endpoint、未脱敏日志、provider/lake/publish。

检查：

| 检查项 | 通过标准 |
|---|---|
| 授权范围 | 包含 gateway start、port bind、account_readonly、simulation、submit_cancel 中实际需要项。 |
| 过期时间 | 覆盖启动、只读、runner、对账和停止。 |
| 回滚 | manual takeover 和 kill-switch 条件明确。 |

## 大步骤 2：导入策略

### 2.1 检查策略准入包

小步骤：

1. 读取研究输出的 strategy admission package。
2. 检查 strategy_id、source_run_id、target_trade_date。
3. 检查 factor evidence、portfolio plan、risk limits。
4. 确认没有 live-ready 或真实交易授权声明。

检查：

| 检查项 | 通过标准 |
|---|---|
| 策略字段 | strategy_id、run_id、target date、capital base 完整。 |
| 证据 | 数据、因子、组合、风险均有 refs。 |
| blocked claims | QMT-ready / live-ready 不被误解。 |

### 2.2 生成私有 runtime operator spec

小步骤：

1. 在私有 runtime 目录准备 `<private-runtime-overlay.json>`。
2. 使用 runtime input builder 合成授权窗口内 spec / admission package。
3. 输入 `runtime_authorization_ref`、`run_id` 和 `expected_runtime_profile=cr138-simulation`。
4. 确认输出目录为 `/home/hyde/.quant-lab/runtime/qmt/cr138-simulation`，不得是 `process/` 或 Git tracked 路径。
5. 设置脱敏 evidence 输出路径。

```bash
uv run --python 3.11 python scripts/build_qmt_multifactor_runtime_inputs.py \
  --base-spec-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json \
  --strategy-admission-json process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json \
  --runtime-overlay-json <private-runtime-overlay.json> \
  --readonly-evidence-ref <redacted-readonly-evidence-ref> \
  --run-id <authorized-run-id> \
  --runtime-authorization-ref <runtime-authorization-ref> \
  --expected-runtime-profile cr138-simulation \
  --output-dir /home/hyde/.quant-lab/runtime/qmt/cr138-simulation
```

检查：

| 检查项 | 通过标准 |
|---|---|
| current positions | 只作为本机输入，evidence 不保存原文。 |
| risk snapshot | cash、positions、t1_sellable、raw_price_refs 齐全。 |
| output_path | runtime spec / admission package 位于私有 runtime 目录；正式 evidence 只保留脱敏 summary 和 refs。 |

## 大步骤 3：启动 QMT gateway

### 3.1 Windows S 端诊断

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli server-diagnostics \
  --env-file <windows-runtime-env> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

检查：

| 检查项 | 通过标准 |
|---|---|
| redaction | secrets redacted。 |
| runtime mode | `simulation`。 |
| account kind | `simulation`。 |
| profile | `cr138-simulation` 或本次授权 profile。 |

### 3.2 Windows S 端启动

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli serve \
  --env-file <windows-runtime-env> \
  --host <windows-wsl-host> \
  --port <gateway-port> \
  --runtime-authorization-ref <runtime-authorization-ref>
```

检查：

| 检查项 | 通过标准 |
|---|---|
| 进程 | 前台运行，可由 `Ctrl+C` 停止。 |
| session | 未返回 `session_expired`、`credential_not_configured`、`login_failed`。 |

## 大步骤 4：C 端只读检查

### 4.1 health 和 capabilities

```bash
curl -sS --max-time 5 http://<windows-host>:<port>/qmt/health
curl -sS --max-time 5 http://<windows-host>:<port>/qmt/capabilities
```

检查：

| 检查项 | 通过标准 |
|---|---|
| health | gateway 可达。 |
| capabilities | endpoint matrix 包含 positions、simulation submit、simulation cancel。 |

### 4.2 positions 只读检查

```bash
uv run --with typer --python 3.11 python -m trading.qmt_runtime_cli query-positions \
  --env-file <wsl-client-env> \
  --base-url http://<windows-host>:<port> \
  --run-id <run-id> \
  --request-id <request-id>
```

检查：

| 检查项 | 通过标准 |
|---|---|
| redaction | 只输出 digest、bucket、instrument_ref。 |
| session | 未过期。 |
| raw payload | `raw_payload_emitted=false`。 |

## 大步骤 5：运行 runner operator

### 5.1 执行命令

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py \
  --spec-json <private-spec-json> \
  --strategy-admission-json <private-admission-package-json> \
  --env-file <wsl-client-env> \
  --base-url http://<windows-host>:<port>
```

### 5.2 检查 P1-P4

| 阶段 | 检查 | 失败处理 |
|---|---|---|
| P1 target | target portfolio generated。 | 不生成 P2。 |
| P2 order plan | risk pass 或 no-op。 | 不执行 P3。 |
| P3 submit/cancel | unknown_count=0，cancel 状态明确。 | manual takeover。 |
| P4 reconciliation | pass 或差异明确。 | kill-switch 候选。 |

## 大步骤 6：停止、对账和日终

### 6.1 正常停止

小步骤：

1. operator 正常退出。
2. Windows gateway 终端按 `Ctrl+C`。
3. 再次确认没有遗留未知订单。

检查：

| 检查项 | 通过标准 |
|---|---|
| stdout | `status=pass`。 |
| evidence | 脱敏 evidence 存在。 |
| order state | submitted / cancelled / rejected / unknown 计数一致。 |

### 6.2 异常停止

| 异常 | 处理 |
|---|---|
| `session_expired` | 停止 operator，重启 / 重新登录 gateway，从只读检查重新开始。 |
| unknown order | 停止新 submit，在 MiniQMT 人工核对。 |
| cancel blocked | 人工撤单或记录无法撤单原因。 |
| recon diff | manual takeover，差异闭环前不恢复自动运行。 |

## 大步骤 7：模拟盘运行边界

| 运行形态 | 当前状态 | 说明 |
|---|---|---|
| 单次受控 simulation runtime | 已具备入口条件 | 仍需逐次授权、用户启动 gateway、P0/P0.5 前置检查。 |
| 连续人工授权 simulation 观察 | 可作为下一阶段目标 | 每次 run 都必须新授权并生成独立 evidence。 |
| 长期自动化 / 无人值守模拟盘 | 未就绪 | 需要额外的自动 preflight checker、运行日历、健康监控、日报和 incident 自动收敛。 |
| `small_live` / `live` | 未授权 | 必须独立 CR、独立人工决策、独立 runtime authorization。 |
