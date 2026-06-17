---
status: "draft-readiness-approved-no-runtime-authorization"
version: "0.1"
change_id: "CR-089"
owner: "host-orchestrator"
runtime_authorized: false
nas_operation_authorized: false
credential_read_authorized: false
---

# CR089 策略包输出与 NAS 交付规划

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 0.1 | 2026-06-17 | host-orchestrator | 初版策略包输出、NAS package exchange、交易主机取包、本地缓存和只读 QMT smoke 规划 |
| 0.2 | 2026-06-17 | host-orchestrator | 用户批准 CR089 CP2/CP3/CP5 推荐方案；规划进入 readiness-approved，但仍不授权 NAS / QMT / 凭据 / 账户 / 交易动作 |

## 目标

本规划定义 QMT 接口验证前，研究侧如何输出可运行策略包，QMT 运行级如何从 NAS 获取策略包，以及交易主机如何校验和本地化策略包。

本规划不是运行授权。当前不访问 NAS，不创建真实策略包，不启动 QMT / MiniQMT / XtQuant，不读取凭据，不查询账户，不 submit/cancel，不 simulation/live。

## 总体链路

```text
research_pc
  生成 strategy package、manifest、sha256、docs、validation evidence
      |
      v
NAS: STRATEGY_PACKAGE_EXCHANGE_ROOT
  只保存 approved package exchange 对象
      |
      v
trading_pc
  只读拉取 -> sha256/manifest 校验 -> 本地不可变缓存 -> QMT terminal / MiniQMT runner 消费
```

默认不建议 QMT 运行级在 NAS 路径原地执行策略代码。推荐行为是从 NAS 只读拉取已批准 package，校验后复制到交易主机本地缓存再运行。NAS 原地执行只可作为临时人工 smoke 选项，不能作为默认生产路径。

## NAS 交付位置

逻辑 root：

```text
${STRATEGY_PACKAGE_EXCHANGE_ROOT}/
```

目录布局：

```text
${STRATEGY_PACKAGE_EXCHANGE_ROOT}/
  packages/
    <strategy_id>/
      <version>/
        strategy-package-<strategy_id>-<version>.zip
        strategy-package-<strategy_id>-<version>.zip.sha256
        manifest.yaml
        manifest.sha256
        docs/
          USER-RUNBOOK.md
          AUTHORIZATION-BOUNDARY.md
          TROUBLESHOOTING.md
        validation/
          evidence.yaml
          static_guardrails.yaml
          fixture_result.yaml
  index/
    package-index.yaml
  approvals/
    CR089-readonly-<date>-001.yaml
  quarantine/
    <package_id>/
      rejection.yaml
  archive/
    <strategy_id>/
      <version>/
        closed-package-record.yaml
```

规则：

| 区域 | 写入方 | 读取方 | 说明 |
|---|---|---|---|
| `packages/` | package builder / research_pc | trading_pc 只读 | 正式策略包交换区 |
| `index/` | package builder | trading_pc 只读 | 当前可消费 package 索引 |
| `approvals/` | 人工门禁 / CR089 | trading_pc 只读 | 脱敏授权摘要 |
| `quarantine/` | 验证方 | 人工审计 | 失败包隔离，不允许运行 |
| `archive/` | package owner | 审计 | 已下线版本记录 |

禁止把 NAS 用户名、NAS 密码、QMT 账号、HMAC secret、token、session、cookie、交易密码或 raw broker payload 写入上述目录。

## 策略包结构

```text
strategy-package-<strategy_id>-<version>/
  manifest.yaml
  strategy_core/
    contract.yaml
    inputs.schema.yaml
    target_portfolio.schema.yaml
    order_intents.schema.yaml
    risk_assumptions.yaml
  targets/
    qmt_terminal/
      target.yaml
      entrypoint.py
      config.example.yaml
      import_steps.md
      shadow_report.schema.yaml
    miniqmt_runner/
      target.yaml
      runner_entrypoint.py
      config.example.yaml
      install_plan.yaml
      start_stop_status_contract.md
  validation/
    fixtures/
    expected/
    static_guardrails.yaml
    evidence.schema.yaml
  docs/
    USER-RUNBOOK.md
    AUTHORIZATION-BOUNDARY.md
    TROUBLESHOOTING.md
```

`strategy_core/` 必须平台无关，不得导入 QMT、XtQuant、MiniQMT 或 broker SDK。真实 broker 接口只能在后续 target adapter 的授权设计中出现。

## manifest 最小合同

```yaml
package_id: "strategy-package-qmt_interface_smoke-0.1.0"
layout_version: "1.0"
strategy_id: "qmt_interface_smoke"
strategy_version: "0.1.0"
source_commit: "<git-commit>"
created_at: "2026-06-17T00:00:00+08:00"

artifact:
  name: "strategy-package-qmt_interface_smoke-0.1.0.zip"
  checksum_sha256: "<sha256>"
  size_bytes: 0

storage:
  exchange_root_ref: "STRATEGY_PACKAGE_EXCHANGE_ROOT"
  storage_tier: "nas_hot"
  package_ref: "packages/qmt_interface_smoke/0.1.0/strategy-package-qmt_interface_smoke-0.1.0.zip"
  execute_policy: "copy_to_trading_local_then_run"

targets:
  - target_id: "qmt_terminal"
    enabled: true
    entry_file: "targets/qmt_terminal/entrypoint.py"
    runtime_authorized: false
    account_query_authorized: false
    submit_cancel_authorized: false
  - target_id: "miniqmt_runner"
    enabled: false
    connection_authorized: false
    submit_cancel_authorized: false

validation_suite:
  static_guardrails: "validation/static_guardrails.yaml"
  fixture_result: "validation/fixture_result.yaml"
  evidence_schema: "validation/evidence.schema.yaml"

authorization_boundary:
  cr_id: "CR-089"
  allowed_scope:
    - "package_checksum_verify"
    - "manifest_parse"
    - "qmt_interface_readonly_smoke"
  forbidden_scope:
    - "order_submit"
    - "order_cancel"
    - "account_write"
    - "simulation"
    - "live"
    - "credential_output"
    - "raw_positions_output"

docs_bundle:
  runbook: "docs/USER-RUNBOOK.md"
  authorization_boundary: "docs/AUTHORIZATION-BOUNDARY.md"
  troubleshooting: "docs/TROUBLESHOOTING.md"
```

## 首个验证策略

| 字段 | 推荐值 |
|---|---|
| `strategy_id` | `qmt_interface_smoke` |
| `strategy_version` | `0.1.0` |
| 目标 | 验证 package discovery、manifest/sha256 校验、交易主机本地化缓存、QMT 只读接口 smoke |
| 允许 | 读取自身 manifest、输出 package digest、检查 target 配置、在授权后执行只读 `query_positions` |
| 禁止 | 生成真实订单、撤单、账户写入、持仓原文输出、simulation/live |

该策略不代表生产策略，不代表 QMT-ready，不代表 trade-ready。

## 交易主机本地缓存

逻辑 root：

```text
${TRADING_PACKAGE_CACHE_ROOT}/
```

推荐布局：

```text
${TRADING_PACKAGE_CACHE_ROOT}/
  packages/
    qmt_interface_smoke/
      0.1.0/
        strategy-package-qmt_interface_smoke-0.1.0.zip
        manifest.yaml
        checksum.ok
        extracted/
          ...
  active/
    qmt_interface_smoke -> ../packages/qmt_interface_smoke/0.1.0/extracted
  evidence/
    CR089-readonly-<date>-001/
      package_intake_evidence.yaml
      qmt_readonly_smoke_evidence.yaml
```

交易主机只保存当前被批准导入的 package、少量 evidence 和脱敏日志，不保存 full research archive，不运行研究脚本。

## 状态机

```text
draft -> staged -> checksum_pass -> approved -> pulled_by_trading_pc -> active_local -> retired
                         \-> rejected/quarantine
```

QMT 运行级只消费 `approved`。不得消费 `draft` 或 `staged`。

## 校验规则

| 校验项 | 失败处理 |
|---|---|
| zip sha256 与 `.sha256` 一致 | fail closed，进入 quarantine |
| `manifest.yaml` 必填字段完整 | fail closed |
| `strategy_core` 无 QMT / XtQuant / MiniQMT / broker SDK import | fail closed |
| `runtime_authorized=false` 未被私自改为 true | fail closed |
| `submit_cancel_authorized=false` | fail closed |
| 示例配置不含账号、密码、token、session | fail closed |
| docs 不声明 `qmt_ready` / `trade_ready` / `runtime_verified=true` | fail closed |
| package ref 只指向 `STRATEGY_PACKAGE_EXCHANGE_ROOT` 下相对路径 | fail closed |

## 只读 QMT smoke 证据

用户手工执行后只允许回填脱敏摘要：

```yaml
cr: CR-089
endpoint_id: query_positions
scope: qmt:positions:read
run_id: CR089-readonly-<date>-001
request_id: CR089-readonly-<date>-001-pos
status: ok
session_ready: true
auth_status: ok
redaction_status: pass
position_count: 0
positions_digest: "positions:<hash>"
forbidden_counters:
  real_order: 0
  real_cancel: 0
  account_write: 0
  provider_fetch: 0
  lake_write: 0
  publish: 0
  simulation_or_live_run: 0
```

禁止提交真实 `.env`、账号、密码、token、session、cookie、HMAC secret、raw signature、raw positions、未脱敏证券代码、精确持仓数量、市值或交易 PC 私有路径。

## 不授权边界

- 不访问 NAS 内容、不挂载 NAS、不复制真实 package。
- 不启动 QMT、MiniQMT、XtQuant、gateway 或 socket。
- 不读取 `.env`、NAS 凭据、QMT 账号、HMAC secret。
- 不查询真实账户原文、资金、持仓原文、委托或成交。
- 不 submit/cancel，不 simulation/live。
- 不把本规划解释为 CR089 active、QMT-ready、trade-ready 或 runtime verified。
