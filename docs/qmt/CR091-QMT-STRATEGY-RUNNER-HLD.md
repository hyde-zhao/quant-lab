# CR091 QMT Strategy Runner HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-18 | host-orchestrator | 首版 HLD，推荐 clean-room package-driven runner，优先支持多因子策略，同时保留通用策略适配能力。 |
| v0.2 | 2026-06-18 | host-orchestrator | 增补 CR091 推荐框架与参考框架的功能支持矩阵，明确支持 / 不支持和取舍原因。 |
| v0.3 | 2026-06-18 | host-orchestrator | 按文档分层约定收敛 HLD 对比内容：完整矩阵留在研究报告，HLD 仅保留架构决策摘要。 |

## 1. 问题定义

CR046 已关闭为 `closed-current-delivery / READY_WITH_RISK`，但只交付 framework-first 的静态 / fixture / 文档 / 契约能力，不表示真实 QMT / MiniQMT / XtQuant / gateway 可用，也不表示 runner 已实现。CR091 要解决的结构缺口是：

- 策略研究产物如何进入一个受控 runner。
- 多因子策略包如何被优先消费和验证。
- 现有 RSI / MACD / momentum 等非多因子策略如何走同一 runner 合同。
- runner 如何与 QMT 只读网关边界衔接，同时不把只读验证误解为交易授权。

## 2. 成功标准

| ID | 成功标准 | 可度量验收 |
|---|---|---|
| SC-CR091-01 | 多因子优先输入成立 | 首版设计必须把 `multifactor_strategy_admission_package_v1` 作为一等输入，至少覆盖 strategy candidate、risk/cost summary、factor contribution、operation counts 四类字段。 |
| SC-CR091-02 | 通用策略可运行合同成立 | 至少定义 3 类 adapter：`MultifactorAdmissionAdapter`、`LegacyStrategyResultAdapter`、`StrategyPackageAdapter`。 |
| SC-CR091-03 | 输出合同统一 | 所有 adapter 均输出同一类 `TargetPortfolioSnapshot` 和 `OrderIntentDraftV1`，不得为多因子另建 QMT 专用订单语义。 |
| SC-CR091-04 | 离线验证封闭 | CP6 前的自动化验证中，NAS / credential / account / qmt / xtquant / submit / cancel / simulation / live / provider / lake / publish 计数必须全部为 0。 |
| SC-CR091-05 | 只读网关范围可枚举 | 首版 gateway scope 只能包含 health、capabilities、query_positions 三类只读能力，其中 query_positions scope 固定为 `qmt:positions:read`。 |
| SC-CR091-06 | evidence 可脱敏审计 | evidence 至少包含 run_id、package_id、adapter_type、target_count、order_intent_count、readonly_reconciliation_status、forbidden_operation_counters、redaction_assurance。 |

## 3. 候选方案

| 方案 | 描述 | 优点 | 缺点 | 结论 |
|---|---|---|---|---|
| A. Clean-room package-driven runner | 在本仓库新增轻量 runner，消费策略包 / adapter 输出，通过 fake transport 做离线验证，只读 runtime 另走授权。 | 边界最清晰，能优先支持多因子，也能兼容其他策略；不引入外部交易写能力。 | 需要自行实现 package/cache/evidence。 | 推荐。 |
| B. 改造 lite-qmt-executor | 以现成 miniQMT 执行器为主体，裁剪买卖能力。 | 有执行引擎、策略插件、队列和启动脚本经验。 | 核心围绕真实账户和买卖，裁剪成本与安全风险高。 | 不采纳首版，只借鉴分层。 |
| C. 接入 qmt-gateway / xqshare | 以外部 gateway / remote proxy 为 runner 依赖。 | gateway 隔离成熟，接口丰富。 | 自动登录、API key、账户、订单和日志流风险面过大。 | 不采纳首版，只参考隔离思路。 |
| D. 接入 vn.py / vnpy_qmt | 使用成熟事件引擎和 gateway 体系。 | 长期交易系统能力强。 | 体量大，目标是交易应用，超出当前 runner gap。 | 后续下单 CR 再评估。 |
| E. 仅保留手工脚本 | 不建设 runner，只要求人工复制和手工执行。 | 最小变更。 | 无法解决“runner 没开发出来如何验证策略”的结构缺口。 | 不推荐。 |

推荐选择 A。

### 3.1 参考框架对比决策摘要

完整功能支持矩阵由 `CR091-RUNNER-RESEARCH-NOTES.md` 的“功能支持矩阵”维护。HLD 只保留影响架构取舍的决策摘要，避免研究证据和架构承诺双份漂移。以下支持判断来自 2026-06-18 静态研究，不表示已经完成真实 QMT / MiniQMT / XtQuant / gateway runtime 验证。

| 决策维度 | CR091 推荐框架 | 参考框架现状 | 架构取舍 |
|---|---|---|---|
| 策略输入模型 | 支持多因子 admission package 作为首选输入，并通过 `StrategyAdapter` 兼容 RSI / MACD / momentum 等策略。 | 参考框架主要面向执行、gateway、远程代理或 vn.py 事件体系，不直接消费本仓库多因子准入包。 | 选择 clean-room adapter 层，不把研究准入包强行塞进外部执行器。 |
| 策略包治理 | 支持 manifest / checksum、immutable local cache 和 active pointer。 | 参考框架通常围绕运行配置、账户连接或交易 API，不提供本仓库所需的策略包审批合同。 | 首版自建最小 package intake，保证可审计和可回放。 |
| 验证路径 | 支持离线 fixture / fake transport / redacted evidence。 | 参考框架普遍假设真实 QMT / miniQMT / xtquant 或远程服务可用。 | 首版只证明 runner 合同，不要求真实 runtime 可用。 |
| 只读网关边界 | 仅支持 health、capabilities、query_positions 三类最小只读能力。 | qmt-gateway、xqshare、lite-qmt-executor 等均暴露或依赖更丰富的账户、交易、行情或日志面。 | 保留最小只读对账面，禁止原始账户 / 持仓 / 委托 / 成交 / 日志进入 evidence。 |
| 交易写接口 | 不支持 buy / sell / cancel。 | lite-qmt-executor、qmt-gateway、vnpy_qmt 支持或面向真实买卖能力。 | 拆到 CR092，单独设计 order write、风控、kill switch 和逐 run 授权。 |
| runtime 启动与鉴权 | 不启动 QMT / miniQMT，不读取 `.env`、API key、secret、session 或账号凭据。 | lite-qmt-executor 和 qmt-gateway 包含 QMT 路径、账户、自动启动或 API Key；xqshare 包含 client secret。 | 自动启动和鉴权不进入 CR091，避免把设计确认误解为运行授权。 |
| 行情、UI、日志、NAS、simulation / live | 不支持 provider、行情下载、Web UI、日志流、NAS pull / publish、simulation 或 live。 | qmt-gateway / xqshare / vn.py 生态覆盖部分行情、UI、日志、事件驱动和实盘能力。 | 这些能力分别属于 provider、package distribution、runtime operations 或交易平台 CR，不合并进 runner 首版。 |
| 完整事件驱动交易系统 | 不支持，仅保留轻量 runner 合同。 | vn.py / vnpy_qmt 提供成熟事件引擎和交易应用边界。 | 当前不引入重型交易平台；当出现复杂实时事件、跨账户或实盘编排需求时再评估切换。 |

决策结论：CR091 首版支持的是“策略包验证 + adapter 归一 + 离线证据”能力，不支持“真实交易执行平台”能力。这个取舍牺牲了执行完整度，但保留了最小权限、可审计性和多策略扩展性。

## 4. 推荐架构

```text
Strategy Sources
  ├─ multifactor_strategy_admission_package_v1
  ├─ StrategyResult(rsi/macd/momentum)
  └─ future strategy package
        │
        ▼
StrategyAdapter Layer
  ├─ MultifactorAdmissionAdapter
  ├─ LegacyStrategyResultAdapter
  └─ StrategyPackageAdapter
        │
        ▼
TargetPortfolioSnapshot + OrderIntentDraftV1
        │
        ▼
Runner Core
  ├─ package manifest/checksum validator
  ├─ immutable local cache reader
  ├─ active pointer resolver
  ├─ offline fake gateway reconciliation
  └─ redacted evidence writer
        │
        ▼
QMT Readonly Boundary
  ├─ health
  ├─ capabilities
  └─ query_positions(qmt:positions:read)
```

核心原则：

- 策略 adapter 是 runner 的输入边界，QMT client 是 runner 的只读外部边界。
- runner 不直接 import `xtquant`，不启动 gateway，不读取 `.env`。
- 多因子不是特例分支，而是优先级最高的一等 adapter。
- 非多因子策略必须通过同样的 adapter 输出合同进入 runner。
- 首版 runner 不做下单、撤单、模拟盘、实盘或自动 NAS 拉取。

## 5. 模块职责

| 模块 | 职责 | 禁止职责 |
|---|---|---|
| `strategy_runner.adapters` | 定义 `StrategyAdapter` protocol；实现多因子准入包、legacy `StrategyResult`、未来策略包 adapter。 | 不连接 QMT；不读取凭据；不做交易风控放行。 |
| `strategy_runner.target_portfolio` | 定义 `TargetPortfolioSnapshot`，承载目标组合、权重、来源 run、限制和 lineage。 | 不宣称可交易；不修正真实账户。 |
| `strategy_runner.order_intents` | 复用 / 包装 `OrderIntentDraftV1`，确保 `qmt_allowed=false`、`not_authorization=true`。 | 不生成 submit / cancel 请求。 |
| `strategy_runner.package_loader` | 校验 manifest、checksum、schema、package id、adapter type、禁止操作声明。 | 不从 NAS 读取；不 publish；不自动解压远端包。 |
| `strategy_runner.cache` | 读取本地 immutable cache 和 active pointer。 | 不修改远端；不把 active pointer 当 publish。 |
| `strategy_runner.readonly_gateway` | 通过可注入 `QmtClient` 访问 fake transport；未来逐 run 授权后可接真实只读 transport。 | 不启动 gateway；不导入 XtQuant；不访问 submit/cancel/asset/orders/trades。 |
| `strategy_runner.evidence` | 生成脱敏 evidence summary 和 forbidden counters。 | 不输出账户、资金、持仓明细、委托、成交或日志原文。 |

## 6. 集成契约

| 调用方向 | 调用时机 | 输入契约 | 输出契约 | 降级策略 | 调用方需同步修改 |
|---|---|---|---|---|---|
| strategy package -> adapter | runner intake 后 | manifest、strategy payload、lineage、operation counts | `AdapterResult(status, target_portfolio, order_intents, warnings)` | schema 不匹配则 fail closed | 策略包必须声明 adapter_type 和 schema_version。 |
| legacy strategy -> adapter | 离线 fixture 或脚本调用后 | `StrategyResult(strategy_name, target_symbols, scores)` | 等权或配置权重的 `TargetPortfolioSnapshot` | 空 target 则 `blocked_empty_targets` | `strategies/base.py` 不需要改语义，只新增 adapter 消费端。 |
| multifactor package -> adapter | 首版主路径 | `multifactor_strategy_admission_package_v1` | 带 risk/cost/factor refs 的 target portfolio 和 order intents | operation counts 非 0 则阻断 | 多因子研究产物需稳定输出 admission package。 |
| runner -> QMT readonly client | 离线测试或逐 run 授权后 | `QmtRequest` / `QmtRestRequest`，scope 只允许 health/capabilities/query_positions | typed response + redacted payload | transport 缺失或未授权则 blocked | 不修改 gateway；只消费既有 typed contract。 |
| runner -> evidence consumer | 每次 runner 结束 | runner summary、adapter summary、readonly summary、counters | redacted evidence YAML / JSON | redaction 检查失败则阻断输出 | CP7 / CP8 消费 evidence 路径而非原始日志。 |

## 7. 相邻对象边界

| 相邻对象 | CR091 边界 |
|---|---|
| CR046 | CR046 只提供 framework-first 契约和后续路线，不表示 runner 已实现；CR091 可消费其策略包思想但不重开 CR046。 |
| CR047 | CR047 是第一个具体策略包交付；CR091 是 runner 能力。CR047 可成为 CR091 的输入，但不由 CR091 代替策略交付。 |
| CR089 | CR089 是本地离线 package skeleton / 只读 interface readiness；CR091 可复用其 manifest、redaction 和 readonly smoke 模型，但不自动激活 CR089 runtime。 |
| CR020 | CR020 的用户删除 QMT gateway 路线已关闭归档；CR091 不恢复该路线，只复用当前仍在仓库中的只读 typed contract。 |
| CR092 候选 | submit / cancel / order write 必须拆到 CR092 或等价新 CR，不能借 CR091 approve 偷渡。 |

## 8. 前置校验与失败路径

| 校验 | 失败条件 | 失败行为 |
|---|---|---|
| package schema | schema_version 不在允许列表 | `blocked_schema_mismatch`，不进入 adapter。 |
| checksum | checksum 缺失或不匹配 | `blocked_checksum_mismatch`，不更新 active pointer。 |
| adapter type | 未知 adapter 或 adapter 输出字段缺失 | `blocked_adapter_contract`。 |
| operation counts | 任一禁止计数非 0 | `blocked_forbidden_operation_nonzero`。 |
| sensitive scan | 输出包含 token / secret / account_id / raw positions 等模式 | 阻断 evidence 写出。 |
| gateway scope | 请求不在 health / capabilities / query_positions | `blocked_scope_denied`。 |
| runtime authorization | 未给逐 run runtime authorization | 使用 fake transport 或返回 blocked，不连接真实 gateway。 |
| redaction | redaction_status 非 pass 或 raw_payload_emitted 为 true | `blocked_redaction_failed`。 |

## 9. 回退与切换表

| 触发 | 回退 / 切换目标 | 理由 |
|---|---|---|
| 用户要求优先验证具体策略包 | 启动 CR047，CR091 保持 runner 方案输入 | 策略交付和 runner 能力是不同对象。 |
| 用户要求先做 NAS 自动取包 | 启动 CR093 候选 | NAS pull / publish 不是 CR091 首版默认职责。 |
| 用户要求验证下单 / 撤单 | 启动 CR092 候选 | order write 需要独立风控、kill switch 和逐 run 授权。 |
| 复杂事件驱动需求出现 | 重新评估 vn.py / Lean / RQAlpha 类框架 | 首版轻量 runner 不承担完整交易系统。 |
| 多因子 package 字段不稳定 | 降级为 `StrategyResult` adapter 或暂停实现 | 避免把研究中间态固化为 runtime 接口。 |

## 10. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 把只读 runner 误解为交易可用 | 造成错误授权预期 | evidence 和门禁中持续声明 `not_authorization=true` 和 `qmt_allowed=false`。 |
| 多因子 adapter 过拟合当前研究产物 | 后续策略难接入 | adapter protocol 只要求目标组合和 order intent 输出，不绑定因子内部实现。 |
| 引入外部执行器导致权限扩大 | 触发账户、密码、订单、日志风险 | 外部项目只作为设计参考，不 vendor、不 clone、不运行。 |
| 真实 gateway smoke 被提前执行 | 触碰账号 / 持仓 / 日志边界 | runtime authorization 单独门禁；本 CR 默认 fake transport。 |
| active pointer 被误当发布 | 造成策略版本漂移 | 首版只读本地 immutable cache，不做 publish。 |

## 11. ADR 候选

| ADR | 决策 | 状态 |
|---|---|---|
| ADR-CR091-01 | 采用 clean-room package-driven runner，而非改造外部 QMT 执行器。 | proposed |
| ADR-CR091-02 | 多因子作为首选 adapter，但所有策略输出统一到 target portfolio + order intent draft。 | proposed |
| ADR-CR091-03 | 首版 runtime 边界只允许 health / capabilities / query_positions。 | proposed |
| ADR-CR091-04 | submit / cancel / simulation / live 拆出 CR092 或后续独立 CR。 | proposed |

## 12. Gotchas

- 不要把 `query_positions` 只读 smoke 当成 QMT ready；它只说明受控只读链路可产生脱敏 evidence。
- 不要让 runner 直接读取 `.env` 或真实账号；真实运行时配置只能由用户在交易主机本地手工执行。
- 不要为多因子单独发明 QMT 订单格式；否则 RSI / MACD / momentum 和后续策略会再次分裂。
- 不要把外部 runner 的买卖 API 裁剪后直接接入；裁剪遗漏会比 clean-room 更难审计。
- 不要把 NAS path 写成 runner 默认输入；本地 immutable cache 和 active pointer 才是首版默认边界。

## 13. 推荐结论

批准 CR091 时，建议同时接受以下结论：

1. 首版 runner 采用 clean-room package-driven runner。
2. 多因子 admission package 是首选输入。
3. 非多因子策略通过 `StrategyAdapter` 进入同一输出合同。
4. 首版只允许离线 fixture / fake transport 自动验证。
5. 真实 QMT 只读 smoke 必须等 CP6 / CP7 后再由用户逐 run 授权。
6. 下单、撤单、simulation、live、NAS 自动取包和 publish 全部排除。
