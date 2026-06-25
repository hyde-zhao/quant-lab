# 场景案例：多因子策略模拟盘运行

本案例面向模拟盘操作者，目标是把研究输出的策略准入包导入 runner，通过 QMT gateway 运行一次 simulation operator，并完成检查、停止和对账。本案例只覆盖 `simulation`，不覆盖 `small_live` 或 `live`。

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

### 2.2 准备 operator spec

小步骤：

1. 从策略包提取 `signal_rows`。
2. 输入本地私有 `current_positions`。
3. 输入 `risk_snapshot` 和 `risk_profile`。
4. 设置 `cancel_submitted_after_submit=true`。
5. 设置脱敏 evidence 输出路径。

检查：

| 检查项 | 通过标准 |
|---|---|
| current positions | 只作为本机输入，evidence 不保存原文。 |
| risk snapshot | cash、positions、t1_sellable、raw_price_refs 齐全。 |
| output_path | 指向 `process/evidence/<run-id>-simulation-operator-evidence.json`。 |

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
