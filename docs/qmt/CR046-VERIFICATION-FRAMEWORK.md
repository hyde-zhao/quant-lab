---
status: "implemented-cp6"
version: "1.1"
change_id: "CR-046"
owner: "host-orchestrator"
runtime_verified: false
cp5_batch: "CR046-DUAL-TARGET-FRAMEWORK-BATCH-A"
cp6_implemented_at: "2026-06-14T00:16:26+08:00"
---

# CR046 验证框架与证据模型

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-13 | host-orchestrator | 初版验证框架，定义 schema/static/fixture/manual plan/runtime evidence 分级和 fail-closed 规则 |
| 1.1 | 2026-06-14 | host-orchestrator | CP6 状态收敛：确认本文作为验证框架契约资产实现；runtime_verified 仍为 false / unavailable |

## 验证目标

CR046 只能证明框架、合同、验证计划和不授权边界已经设计完成，不能证明 QMT 或 MiniQMT runtime 可用。

## StrategyValidationEvidence 分级

| 证据层级 | 含义 | CR046 是否允许产出 | 是否等于 runtime verified |
|---|---|---:|---:|
| `schema_pass` | manifest、contract、target schema 字段完整 | 是 | 否 |
| `static_guardrail_pass` | forbidden import、凭据、submit/cancel 声明静态检查计划通过 | 是 | 否 |
| `fixture_dry_run_pass` | 本地 fixture 能映射 core / target 合同 | 是 | 否 |
| `qmt_terminal_shadow_plan_ready` | QMT 终端 shadow 人工验证计划可读 | 是 | 否 |
| `miniqmt_install_dry_run_plan_ready` | MiniQMT runner 安装 dry-run 计划可读 | 是 | 否 |
| `runtime_verified` | 真实终端或真实 runner 运行验证通过 | 否 | 是 |

CR046 任何文档、检查点、报告不得把前五类证据写成 `runtime_verified=true`。

## 验证对象

| 对象 | 验证入口 | 失败行为 |
|---|---|---|
| StrategyCoreContract | schema review、forbidden import scan plan | 缺字段或出现平台 API，CP5/CP7 blocked |
| StrategyPackageContract | manifest schema、artifact/checksum 字段 review | 缺 artifact / sha256 / transfer_channel，blocked |
| QMTTerminalTargetContract | entry_file、config_schema、import_steps、shadow_report_schema review | runtime 授权字段为 true 时 blocked |
| MiniQMTRunnerTargetContract | install_layout、uv、dependency_policy、redacted config review | 出现真实凭据或 install 命令授权时 blocked |
| Documentation | authorization boundary / troubleshooting review | 声称可运行或可交易时 blocked |

## Guardrail 规则

| Guardrail ID | 规则 | 检查方式 | 失败处理 |
|---|---|---|---|
| G-CR046-01 | `strategy_core/` 不得导入 QMT、XtQuant、MiniQMT、broker SDK | 静态扫描计划 | FAIL |
| G-CR046-02 | manifest 必须包含 artifact、sha256、targets、validation_suite、authorization_boundary | schema review | FAIL |
| G-CR046-03 | target contract 默认 `runtime_authorized=false` | docs review | FAIL |
| G-CR046-04 | 配置示例不得包含真实账号、token、session、交易密码 | redaction review | FAIL |
| G-CR046-05 | submit/cancel、account query、simulation/live 默认均为 false | safety review | FAIL |
| G-CR046-06 | fixture/static pass 不得声明 runtime verified | wording guardrail | FAIL |

## QMT Terminal Shadow Plan

CR046 只定义后续计划：

1. 选择 CR047 具体策略包。
2. 校验 zip + sha256 + manifest。
3. 人工导入 QMT terminal target。
4. 在独立 runtime authorization gate 中确认运行窗口、操作者、回滚和证据脱敏。
5. 生成 shadow report。

CR046 不执行上述步骤。

## MiniQMT Install Dry-Run Plan

CR046 只定义后续计划：

1. 检查用户是否已开通 MiniQMT / XtQuant 权限。
2. 选择 Windows install root。
3. 使用 uv 管理 runner Python 环境。
4. 使用 redacted config template。
5. 仅在 CR049 或独立 authorization gate 中执行 install dry-run 或 readonly connection。

CR046 不安装、不连接、不启动 runner。

## 失败路径

| 触发条件 | 阶段结论 | 后续动作 |
|---|---|---|
| 缺少必填 schema 字段 | CP5 FAIL | 回到对应 LLD 修正 |
| 文档出现真实运行授权 | CP5 / CP7 FAIL | 移除授权或另起 runtime gate |
| 出现凭据字段或真实账号 | CP5 / CP7 BLOCKED | 停止并脱敏 |
| 用户要求当前交付策略 | scope change | 回退 CR046 或启动 CR047 |
| 用户要求真实 QMT / MiniQMT 验证 | runtime_authorization | 新 CR / 独立 gate |

## CP7 / CP8 声明边界

允许声明：

- `framework_contract_ready`
- `schema_plan_ready`
- `static_guardrail_plan_ready`
- `fixture_validation_plan_ready`
- `manual_shadow_plan_ready`
- `runtime_verified=false`

禁止声明：

- `qmt_ready`
- `miniqmt_ready`
- `simulation_ready`
- `trade_ready`
- `live_ready`
- `runtime_verified=true`
