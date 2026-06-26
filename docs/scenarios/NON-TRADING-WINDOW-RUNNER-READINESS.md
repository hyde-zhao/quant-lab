# 场景案例：非交易窗口 Runner 准备

本案例用于在不开 QMT gateway、不读取凭据、不触达真实账户、不提交 / 撤单的情况下，完成交易窗口前的 runner 准备。所有步骤都应保持 `runtime_touched=false`，只生成脱敏 fixture evidence。

当前冻结输入：

| 对象 | 路径 |
|---|---|
| StrategyAdmissionPackage | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-STRATEGY-ADMISSION-PACKAGE-2026-06-25.json` |
| operator spec | `process/context/RUNNER-QMT-SIMULATION-MULTIFACTOR-FORMAL-OPERATOR-SPEC-2026-06-25.json` |
| 完成记录 | `process/checks/RUNNER-QMT-SIMULATION-MULTIFACTOR-NON-TRADING-WINDOW-COMPLETION-2026-06-25.md` |

这些输入只用于离线 readiness。它们不授权 `runtime`、不授权 `simulation submit/cancel`、不授权 `small_live` / `live`。

## 大步骤 1：冻结 operator 输入

### 1.1 准备 operator spec

小步骤：

1. 固定 `strategy_id`、`run_id`、`target_trade_date`。
2. 固定 `signal_rows` 或提供 `StrategyAdmissionPackage`。
3. 固定 `capital_base`、`current_positions` fixture、`risk_snapshot` 和 `risk_profile`。
4. 固定 `output_path` 或使用 `--output-dir`。

检查：

| 检查项 | 通过标准 |
|---|---|
| strategy input | `strategy_id`、`run_id`、`target_trade_date` 完整。 |
| evidence refs | risk snapshot / risk profile 有 evidence ref。 |
| raw data | spec 可以在本地含 symbol，但 evidence 不得输出原始 symbol。 |
| authorization | 非交易窗口模式不需要 runtime authorization。 |

## 大步骤 2：执行非交易窗口 CLI

### 2.1 preflight-only

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py \
  --mode preflight-only \
  --spec-json <operator-spec-json> \
  --output-dir process/evidence/runner-simulation
```

检查：

| 检查项 | 通过标准 |
|---|---|
| required fields | 必填字段完整。 |
| runtime | 不读取 env，不构造 QMT client。 |
| evidence | 写入 `operator-evidence.json` 和 `operator-evidence.index.json`。 |

### 2.2 plan-only

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py \
  --mode plan-only \
  --spec-json <operator-spec-json> \
  --output-dir process/evidence/runner-simulation
```

检查：

| 阶段 | 通过标准 |
|---|---|
| P1 | target portfolio generated。 |
| P2 | order plan generated 或 risk blocked。 |
| P3 | `status=skipped`，`runtime_touched=false`。 |
| P4 | `status=skipped`。 |

### 2.3 fixture / reconcile-only

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py \
  --mode fixture \
  --spec-json <operator-spec-json> \
  --output-dir process/evidence/runner-simulation
```

`fixture` 会执行 P1、P2 和 P4 fixture reconciliation，但 P3 submit/cancel 为 `no_op`。`reconcile-only` 使用同一 no-runtime 路径复核 P4 对账合同。

检查：

| 检查项 | 通过标准 |
|---|---|
| runtime | `runtime_authorization_granted=false`。 |
| execution | `submitted_count=0`、`cancelled_count=0`。 |
| evidence schema | `validate_operator_evidence(..., mode="fixture")` 通过。 |
| redaction | evidence 不包含原始证券代码、账户、token、broker raw ref。 |

## 大步骤 3：策略准入包输入契约

### 3.1 使用 StrategyAdmissionPackage

operator CLI 支持独立传入策略准入包：

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --python 3.11 python scripts/run_qmt_multifactor_simulation_operator.py \
  --mode plan-only \
  --spec-json <operator-base-spec-json> \
  --strategy-admission-json <strategy-admission-package-json> \
  --output-dir process/evidence/runner-simulation
```

检查：

| 检查项 | 通过标准 |
|---|---|
| schema | `multifactor_strategy_admission_package_v1`。 |
| authorization flags | `not_authorization`、`not_qmt_authorization`、`not_simulation_authorization`、`not_live_authorization`、`not_broker_order` 均为 true。 |
| operation counts | `credential_read`、`qmt_start`、`submit_order`、`cancel_order`、`simulation`、`live` 等均为 0。 |
| risk cost refs | `risk_cost_refs` 存在。 |
| signal rows | 可从 `strategy_scores` 转成 P1 `signal_rows`。 |

## 大步骤 4：交易窗口前 checklist

| Checklist | 必须证据 | 失败处理 |
|---|---|---|
| authorization draft ready | authorization draft ref | block runtime start |
| strategy admission contract pass | strategy admission contract ref | block P1 |
| operator fixture pass | fixture evidence ref | block runtime start |
| evidence schema pass | evidence schema validation ref | block evidence publish |
| manual takeover ready | manual takeover checklist ref | block submit/cancel |

## 大步骤 5：异常矩阵离线演练

| 异常 | 处理 |
|---|---|
| authorization expired | stop runner and gateway |
| gateway health fail | do not enter P3 |
| capabilities missing | do not enter P3 |
| query positions redaction fail | discard snapshot and block |
| risk gate blocked | do not submit |
| kill switch active | do not submit |
| order submit unknown | manual takeover |
| cancel unknown | manual takeover |
| recon diff | manual takeover or kill-switch candidate |

## 大步骤 6：稳定性窗口定义

默认建议：

| 字段 | 值 |
|---|---|
| required_runs | 5 |
| required_trading_days | 3 |
| pass criteria | authorization ref、P1-P4 evidence schema、unknown order count zero、manual takeover closed、gateway stop confirmed |
| fail criteria | authorization missing、raw payload in evidence、unknown order unresolved、reconciliation diff unclosed、gateway stop unconfirmed |

稳定性窗口定义可以在非交易窗口冻结；真实计数必须等交易窗口内的真实 simulation run 完成后再累计。

当前状态：交易窗口 evidence 已完成 `5/5` runtime count，并被接受为 `READY_WITH_RISK`。原 `required_trading_days=3` 保留为保守观察口径；若未来需要从 `READY_WITH_RISK` 升级为严格 `READY`，可补第三个交易日观察。

## 大步骤 7：证据保留和人工接管

| 项目 | 当前策略 |
|---|---|
| evidence 保存范围 | summary、bucket、digest、instrument ref、intent ref、validation result、evidence path |
| 禁止保存 | 真实账号、真实证券代码、原始持仓、原始订单、broker raw ref、资金明细、token、secret、raw payload |
| retention | 默认 `30` 天；长期只保留 index、check summary 和必要 digest refs |
| manual takeover | `session_expired`、`order_submit_unknown`、`cancel_unknown`、`recon_diff`、redaction fail 均 fail closed |
| kill-switch | 授权缺失、gateway health fail、unknown order、未关闭 recon diff、raw evidence 泄漏均停止新单 |

## 大步骤 8：从 readiness 进入模拟盘运行

当前已完成的 readiness 只允许进入受控人工授权 simulation 模拟盘运行，不允许直接进入长期自动化或 `small_live` / `live`。

| 后续方向 | 入口条件 |
|---|---|
| 单次 simulation runtime | 新的逐次 runtime authorization、用户启动 Windows gateway、P0/P0.5 通过、runtime input 按 policy 重新生成。 |
| 补第三个交易日观察 | 新的逐次 runtime authorization；运行完成后可更新 readiness 为更严格 `READY` 候选。 |
| 长期自动化模拟盘 | 另行实现自动 preflight checker、运行日历、健康监控、日报和 incident 自动收敛。 |
| `small_live` / `live` | 独立 CR、`DQ-LIVE-001..004` 人工决策、独立 runtime authorization。 |
