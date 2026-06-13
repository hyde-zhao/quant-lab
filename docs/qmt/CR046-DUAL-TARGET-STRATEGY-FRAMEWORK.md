---
status: "implemented-cp6"
version: "1.1"
change_id: "CR-046"
owner: "host-orchestrator"
source_hld: "docs/design/HLD-CR046-QMT-MINIQMT-DUAL-TARGET-FRAMEWORK.md"
source_feature: "docs/features/qmt-miniqmt-dual-target-framework/DESIGN.md"
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
runtime_authorized: false
cp6_implemented_at: "2026-06-14T00:16:26+08:00"
---

# CR046 QMT / MiniQMT 双目标策略交付框架

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | host-orchestrator | 初版框架文档，定义 StrategyCoreContract、StrategyPackageContract、QMT terminal target、MiniQMT runner target、artifact 传输合同和不授权边界 |
| 1.1 | 2026-06-14 | host-orchestrator | CP6 状态收敛：确认本文作为 framework-first 契约资产实现；不新增真实运行、传输、导入或交易授权 |

## 目标

CR046 只冻结交易交付框架和验证框架，不交付具体策略，不执行 QMT 终端验证，不连接或安装 MiniQMT，不读取凭据、账户、资金、持仓、委托或成交，不 submit/cancel，不 simulation/live。

本框架定义一个研究策略从研究侧进入后续交易交付的统一合同：

1. 研究侧产出平台无关的 `StrategyCoreContract`。
2. 策略交付以 `StrategyPackageContract` 组织为可审计 artifact。
3. QMT 终端使用 `QMTTerminalTargetContract` 做人工导入和 shadow 计划。
4. MiniQMT 未来 runner 使用 `MiniQMTRunnerTargetContract` 做安装与运行边界设计。
5. 所有验证声明通过 `StrategyValidationEvidence` 分级表达。

## 总体结构

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

本 CR 只定义上述结构和字段合同。`entrypoint.py` / `runner_entrypoint.py` 是后续 CR047 具体策略交付时的目标文件形态，不在 CR046 交付具体策略实现。

## StrategyCoreContract

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `strategy_id` | string | 是 | 研究策略稳定 ID |
| `strategy_version` | string | 是 | 策略版本，建议 SemVer 或日期版本 |
| `research_source` | object | 是 | 研究报告、admission package、实验 run_id 的只读引用 |
| `input_schema` | path | 是 | 策略输入 schema，不引用真实账户 |
| `target_portfolio_schema` | path | 是 | 目标持仓或目标权重 schema |
| `order_intent_schema` | path | 是 | order intent 草案 schema，仅表达意图，不代表订单 |
| `risk_assumptions` | path | 是 | 风险、成本、容量、成交假设 |
| `evidence_required` | list | 是 | schema/static/fixture/manual plan 等所需证据 |
| `forbidden_imports` | list | 是 | 必含 `qmt`、`xtquant`、`miniqmt`、broker SDK |

`strategy_core/` 必须保持平台无关。任何 QMT、XtQuant、MiniQMT、broker SDK、凭据读取、账户查询或 submit/cancel 只能出现在后续 target adapter 的授权设计中，不能进入 core。

## StrategyPackageContract

`manifest.yaml` 是策略包入口，至少包含：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `package_id` | string | 是 | `strategy_id` + 版本组成的包 ID |
| `layout_version` | string | 是 | 策略包布局版本，CR046 初始为 `1.0` |
| `strategy_core` | object | 是 | core 合同路径和 schema 列表 |
| `targets` | list | 是 | `qmt_terminal`、`miniqmt_runner` 的启用状态 |
| `validation_suite` | object | 是 | schema、static、fixture、manual plan 入口 |
| `docs_bundle` | object | 是 | 手册、授权边界、排错文档路径 |
| `authorization_boundary` | object | 是 | 当前包不授权项和后续 gate |
| `artifact_name` | string | 是 | `strategy-package-<strategy_id>-<version>.zip` |
| `checksum_sha256` | string | 是 | zip artifact 的 sha256 |
| `transfer_channel` | enum | 是 | `manual_controlled_file_transfer` / `git_release` / `internal_share` / `offline_media` |
| `manual_import_steps` | path | 是 | QMT terminal 人工导入步骤 |

默认传输形态由用户确认：`zip + sha256 + manifest.yaml + docs bundle`，经人工/受控文件通道传到交易运行 PC，再由 QMT terminal target 人工导入。该合同不授权真实传输、导入或运行。

## QMTTerminalTargetContract

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `target_id` | string | 是 | 固定为 `qmt_terminal` |
| `entry_file` | path | 是 | QMT 终端策略入口文件路径 |
| `config_schema` | path | 是 | QMT target 配置 schema |
| `import_steps` | path | 是 | 人工导入步骤 |
| `shadow_report_schema` | path | 是 | 后续 shadow 验证报告 schema |
| `runtime_authorized` | bool | 是 | CR046 固定为 `false` |
| `account_query_authorized` | bool | 是 | CR046 固定为 `false` |
| `submit_cancel_authorized` | bool | 是 | CR046 固定为 `false` |

QMT terminal target 只定义人工导入和 shadow plan。真实 QMT terminal shadow、模拟盘验证、submit/cancel、账户查询和 runtime verified 只能由后续 CR / runtime authorization gate 打开。

## MiniQMTRunnerTargetContract

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `target_id` | string | 是 | 固定为 `miniqmt_runner` |
| `install_layout` | path/object | 是 | Windows 目录布局 |
| `uv_python_version` | string | 是 | runner 目标 Python 版本 |
| `dependency_policy` | object | 是 | MiniQMT / XtQuant 依赖隔离策略 |
| `redacted_config_template` | path | 是 | 不含真实凭据的配置模板 |
| `log_paths` | object | 是 | 脱敏日志目录 |
| `kill_switch` | object | 是 | 默认 hard-off |
| `upgrade_uninstall_rollback` | object | 是 | 升级、卸载、回滚设计 |
| `real_install_authorized` | bool | 是 | CR046 固定为 `false` |
| `connection_authorized` | bool | 是 | CR046 固定为 `false` |

MiniQMT runner 在 CR046 中只是 design-only，不真实安装，不连接 XtQuant，不订阅行情，不查询账户，不下单撤单。

## Artifact 传输与导入合同

| 步骤 | 责任方 | 输入 | 输出 | 授权状态 |
|---|---|---|---|---|
| 1. 生成策略包 | 后续 CR047 | strategy core、target config、validation suite | zip artifact | CR046 不执行 |
| 2. 生成校验 | 后续 CR047 | zip artifact | `.sha256` | CR046 不执行 |
| 3. 传输到交易 PC | 人工/受控通道 | zip、sha256、manifest、docs | 交易 PC 本地 artifact | CR046 不授权实际传输 |
| 4. 校验 artifact | 交易 PC 人工步骤 | zip + sha256 | checksum pass/fail | CR046 只定义步骤 |
| 5. QMT 终端导入 | QMT terminal target | 已校验 artifact | 终端内策略配置 | 后续授权 |
| 6. Shadow / runtime | 后续 runtime gate | QMT 策略配置 | runtime evidence | CR046 不授权 |

失败路径：

| 失败 | 行为 |
|---|---|
| sha256 不匹配 | fail closed，禁止导入 |
| transfer_channel 未批准 | fail closed，回到人工确认 |
| manifest 缺必填字段 | fail closed，禁止导入 |
| 文档声称 runtime verified | CP7 / CP8 blocked |
| 需要 submit/cancel | 转后续 runtime authorization gate |

## 不授权项

CR046 不授权：

- 具体交易策略交付
- QMT 终端 shadow / 模拟盘运行验证
- 真实传输到交易 PC
- 真实导入 QMT 终端
- MiniQMT runner 真实安装
- MiniQMT / XtQuant 连接
- 真实行情订阅
- 账户、资金、持仓、委托、成交查询
- submit/cancel
- simulation/live
- provider fetch、lake write、catalog publish
- 凭据、token、session、账号、交易密码或 `.env` 读取

## 后续消费

| 后续对象 | 消费内容 | 前置条件 |
|---|---|---|
| CR047 | StrategyCoreContract、StrategyPackageContract、QMT target、validation evidence | CR046 CP8 通过 |
| CR048 | QMT terminal shadow / 最小 submit/cancel 授权验证 | CR047 具体策略包和 shadow 证据 |
| CR049 | MiniQMT install / readonly 实机验证 | MiniQMT 权限和独立 runtime authorization |
| CR051 | 研究框架反向完善 | CR046 策略核心和证据模型定稿 |
