---
handoff_id: "META-SE-CR044-CP2-CP3-DESIGN-2026-06-11"
cr_id: "CR-044"
role: "meta-se"
status: "ready-for-meta-po-cp2-cp3-brief"
created_at: "2026-06-11T10:00:43+08:00"
scope: "CP2/CP3 design input and Story/LLD batch recommendation only"
runtime_authorization: "L1/L2 only"
real_runtime_authorized: false
touches_source_code: false
dispatch:
  mode: "spawn_agent"
  agent_id: "019eb465-0053-7492-8692-6bde73dcc25f"
  agent_name: "se-chu"
  tool_name: "multi_agent_v1.spawn_agent"
  spawned_at: "2026-06-11T09:53:10+08:00"
  completed_at: "2026-06-11T10:00:43+08:00"
  requested_by: "meta-po"
---

# CR044 Goldminer Simulation Admission CP2/CP3 设计输入

## 0. 输入事实与不授权边界

本交还只消费并引用以下输入事实，不修改 `STATE`、`CR-INDEX`、CR 文件或源码：

| 输入 | 关键事实 |
|---|---|
| `process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md` | CR044 已获准启动 CP2 intake 与 L2 离线工程设计；当前不授权 `credential_read`、`login`、`connect`、账户查询、下单、撤单、simulation/live、provider fetch、lake write、catalog publish。 |
| `process/changes/CR-043-GOLDMINER-ADAPTER-SPIKE-2026-06-11.md` | CR043 已关闭为 `closed-spike-complete`，结论 `NEEDS_ACCOUNT_PERMISSION`；`gm` 是 Python 3.11 主选静态候选，`gmtrade` 是 Python 3.10 fallback；真实 adapter 不在 CR043 内实现。 |
| `process/research/cr043_goldminer_adapter_spike/SPIKE-CONCLUSION.md` | SDK 静态接口可映射，但资金、持仓、委托、成交字段、账号权限、错误语义和仿真账户可用性仍需后续受控授权核对。 |
| `process/research/cr043_goldminer_adapter_spike/INTERFACE-MAPPING-MATRIX.md` | `BrokerAdapter` 合同可映射到 `gm` / `gmtrade` 静态候选；真实调用必须 fail-closed；`account_id` 等账户标识属于敏感字段。 |
| `engine/broker_adapter.py` | 当前唯一 Goldminer 运行态对象是 `GoldminerStubBrokerAdapter`；`BrokerAdapterResult.to_dict()` 固定输出 `simulation_ready=false`、`live_ready=false`；敏感字段和非零 forbidden operation count 必须阻断。 |
| `tests/test_cr042_broker_adapter_contract.py` | 现有测试要求 adapter broker-neutral、API-less、JSON-safe、敏感字段零泄漏、真实操作计数为 0，并静态禁止 broker/network/trading runtime import/call。 |

本交还不要求、不收集、不记录 token、account、password、session、cookie、private key 或任何凭据材料。任何真实 runtime 行为默认 `BLOCKED` / fail-closed。

## 1. 问题定义

CR044 要解决的问题不是“马上跑掘金仿真”，而是把 CR043 的静态可行性结论提升为可审计的仿真准入设计：在不读取凭据、不登录、不连接、不查询账户、不下单、不撤单的 L1/L2 授权下，先定义账号权限准入、凭据边界、只读查询字段映射、下单/撤单门控、对账证据、kill switch、redaction 和 no-operation guard。

目标：

| 目标 | 可验证标准 |
|---|---|
| 授权边界清晰 | CP2 明确 L1/L2 已授权、L3/L4/L5 未授权；真实操作计数默认必须为 0。 |
| 架构 fail-closed | CP3 推荐方案中，未获得逐 run 授权时 `GoldminerStubBrokerAdapter` 或 admission gate 返回 blocked，不导入/调用真实 SDK runtime。 |
| 凭据与账户材料不落盘 | 文档、日志、fixture、测试报告不得包含 token、account、password、session、cookie、private key；账户标识也按敏感字段处理。 |
| 可继续 Story/LLD | 输出 Story 拆解、LLD policy、文件影响范围和验证矩阵，供 meta-po 后续组织 CP3/CP5。 |
| 后续 L3+ 可逐步准入 | 若用户另行授权，L3 凭据/账号检查、L4 只读查询、L5 submit/cancel/reconcile 必须逐 run、逐动作、逐证据执行。 |

非目标：

| 非目标 | 原因 |
|---|---|
| 不实现真实 Goldminer adapter | 当前只要求设计交还，且 L3+ 未授权。 |
| 不启动 simulation/live | CR044 当前只授权 L1/L2；simulation/live 属 L5+ 运行授权。 |
| 不读取 `.env` 或终端配置 | 任何 credential/account/session 读取均未授权。 |
| 不 provider fetch / lake write / catalog publish | 明确在不授权范围内。 |
| 不修改 CR042 paper simulation 语义 | CR044 只消费其 no-operation、ledger、reconciliation 经验，不替换 paper fixture。 |

关键假设：

| 假设 | 影响 | 失效处理 |
|---|---|---|
| `gm` 继续作为 Python 3.11 主选静态候选 | 设计优先围绕同 runtime admission gate | 若 CP3 改选 `gmtrade`，需要 Python 3.10 隔离 runtime 设计，不得在当前进程直接接入。 |
| L3+ 仍未授权 | Story 只能产出 blocked-first / fixture-only 资产 | 若用户逐 run 授权，新增独立 runtime authorization 决策并补 LLD。 |
| CR042 合同继续是 broker-neutral 单一合同 | CR044 不绕过 `BrokerAdapter`、operation counts、sensitive guard | 若合同需扩展，必须作为 CP3/CP5 决策项进入 Story。 |

## 2. CP2 人工门禁：授权决策候选表

以下内容必须进入 CP2 人工门禁。用户回复 `approve` 应只表示接受 L1/L2 推荐方案，不表示授权任何 L3+ 真实 runtime 行为。

| 决策 ID | 类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|
| CP2-CR044-DQ-01 | scope | CR044 是否进入 standard scoped admission，而非直接 runtime | 推荐：进入 standard，先做授权、架构和 Story/LLD，不运行 broker | 备选：关闭为 `blocked-by-account-permission`；或只保留 CR043 结论不推进 | standard 成本更高，但能审计安全边界；直接 runtime 风险不可接受 | 若用户不接受准入设计成本，回退 CR043 `NEEDS_ACCOUNT_PERMISSION` |
| CP2-CR044-DQ-02 | runtime_authorization | 当前授权层级 | 推荐：仅 L1 formal orchestration + L2 offline engineering design / fixture-only | 备选：暂停到用户准备 L3+ 逐 run 授权；或只写文档不排 Story | 限制真实验证，但保证不触碰凭据和账户 | 任何 credential/account/query/order 需求出现时，转 L3+ 决策，不得继续静默推进 |
| CP2-CR044-DQ-03 | security | 凭据和账户材料处理 | 推荐：不收集、不询问、不记录 token/account/password/session/cookie/private key；账户 ID 也按敏感字段脱敏 | 备选：用户另行提供离线脱敏结构文档，不含真实账号和值 | 降低泄漏风险；无法确认真实字段值 | 若必须处理真实材料，暂停并发起独立安全授权，不在对话或 Markdown 记录值 |
| CP2-CR044-DQ-04 | risk_acceptance | 是否接受当前只能得到 offline admission design 结论 | 推荐：接受 `offline-admission-design-ready` / `blocked-by-account-permission` 作为可能关闭结论 | 备选：等待 L3+ 授权后再启动 CR044 | 避免把静态设计误称为 simulation-ready | 若用户要求 simulation-ready，必须先逐 run 授权 L3/L4/L5 |
| CP2-CR044-DQ-05 | follow_up_tracking | 是否把 L3+ 行为拆成后续逐 run 决策 | 推荐：拆分，CP2/CP3 不授权运行；后续按 run manifest 单次授权 | 备选：本 CR 结束为 not-recommended，不进入运行授权 | 决策链更长，但安全边界清楚 | 若授权粒度无法明确，所有真实 runtime fail-closed |

## 3. CP3 架构灰区与方案表

以下内容必须进入 CP3。CP3 只确认架构与设计边界，不授权真实 runtime。

### 3.1 灰区 A：Goldminer 准入形态

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A1 blocked-first admission gate + 保留 stub | 与 CR042 合同一致；未授权时真实操作计数为 0；可用 fixture 覆盖 | 短期不能证明真实仿真字段 | `engine/broker_adapter.py`、测试、runbook、Story/LLD | 推荐 | 当前只有 L1/L2；若 L3+ 获批，再在独立 Story 中打开受控只读探针 |
| A2 直接实现真实 adapter 但默认 disabled | 后续切换成本较低 | 容易引入 import/call、凭据和配置误触；测试需更复杂隔离 | 源码、依赖、CI、安全审计 | 不推荐 | 只有在 CP3/CP5 明确真实 adapter 另行 CR 且 L3+ 授权后考虑 |
| A3 不推进 CR044，停在 CR043 结论 | 零 runtime 风险 | 无法形成后续工程门禁 | CR 台账、follow-up | 治理备选 | 若用户拒绝 L2 设计成本或无法接受未知项 |

### 3.2 灰区 B：SDK 选择和 runtime 隔离

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| B1 `gm` 为 Python 3.11 主选静态候选 | 与项目 runtime 匹配；CR043 静态 import 成功 | 真实交易语义仍需账号权限确认 | HLD、LLD、字段映射、测试 fixture | 推荐 | 若官方/账号事实证明 `gm` 交易字段不足，切换 B2 |
| B2 `gmtrade` 作为 Python 3.10 隔离 fallback | 更像独立交易 SDK | Python 3.11 wheel 不可用；需要跨 runtime 隔离 | 平台安装、runtime、进程边界 | 条件推荐 | 仅当 `gm` 不满足交易准入且用户接受隔离 runtime 成本 |
| B3 双 SDK 同时设计 | 覆盖面最大 | 复杂度和验证成本最高；权限矩阵加倍 | 架构、测试、文档、运维 | 不推荐 | 只有在业务必须双 SDK 容灾且 L3+ 已授权时考虑 |

### 3.3 灰区 C：凭据、redaction 与证据保存

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| C1 零凭据持有 + 结构脱敏 fixture | 最小泄漏风险；符合当前授权 | 不能验证真实账号字段 | 测试 fixture、日志、报告、adapter result | 推荐 | 当前 L3 未授权 |
| C2 用户本地逐 run 注入，产物只存 hash/状态不存值 | 可支持后续受控 runtime | 需要严格 run manifest、redaction 和销毁策略 | L3+ runbook、QA、审计 | 后续条件推荐 | 仅 L3+ 逐 run 授权，且不得把值写入仓库/对话 |
| C3 仓库配置持久保存凭据 | 接入方便 | 凭据泄漏和误运行风险不可接受 | 全仓库、安全、合规 | 禁止 | 不切换 |

### 3.4 灰区 D：reconciliation 与 kill switch

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| D1 离线对账合同 + 默认 hard kill switch | 可用 fixture 验证；真实 runtime 全阻断 | 不能确认真实 broker 最终状态 | adapter result、测试、runbook、CP7 | 推荐 | 当前只有 L1/L2 |
| D2 只读查询先行，submit/cancel 后置 | 风险分层；可先确认资金/持仓/委托字段 | 需要 L4 账号查询授权 | read-only adapter probe、redaction、QA | 后续条件推荐 | L3 credential/account + L4 readonly 被逐 run 授权后 |
| D3 submit/cancel/reconcile 一次性打通 | 端到端价值最高 | 下单/撤单副作用风险最高 | broker runtime、账户、交易安全 | 不推荐 | 仅在 L3/L4 已通过且 L5 单次运行有明确订单、撤单、kill switch 和回滚计划 |

## 4. 推荐方案

推荐方案：`blocked-first Goldminer admission gate + fixture-only engineering + staged L3+ run authorization`。

核心设计：

| 组件 / 能力 | 推荐职责 |
|---|---|
| `GoldminerStubBrokerAdapter` | 当前继续作为唯一 Goldminer 运行态对象，所有 query/submit/cancel 继续 blocked。 |
| Admission gate | 新增或扩展为设计对象：判断 authorization layer、capability state、kill switch、run manifest 是否允许某动作；默认 deny。 |
| Capability state | 区分 `sdk_static_candidate`、`offline_design_ready`、`credential_required`、`readonly_authorized_for_run`、`submit_cancel_authorized_for_run`；任何状态都不自动等于 `simulation_ready=true`。 |
| Redaction layer | 对 token/account/password/session/cookie/private key、`account_id`、broker account、order ref 等敏感字段做 deny-list + value redaction；报告只存脱敏摘要。 |
| No-operation guard | 对 forbidden operation counters 做统一校验；任一 `real_*`、`credential_read`、`goldminer_import_or_call`、`gmtrade_import_or_call` 或 provider/lake/catalog 计数非零则 blocked。 |
| Per-run authorization | 后续 L3+ 必须用单次 run manifest 记录授权层级、动作、输入来源、有效期、kill switch、预期真实操作计数上限和证据路径；本交还不创建该 manifest。 |
| Kill switch | 默认 hard-off；需要全局 disabled + per-run disabled 任一为 true 即阻断；未显式授权视为 disabled。 |
| Reconciliation | L2 只定义离线对账合同和 fixture；真实 broker 对账必须等 L4/L5 逐 run 授权。 |

推荐理由：

| 维度 | 结论 |
|---|---|
| 安全 | 不触碰凭据、不连接、不查询、不下单，符合当前授权。 |
| 可验证性 | 可通过现有 CR042 测试风格验证敏感字段、operation counts、静态禁用和 blocked result。 |
| 可演进 | L3/L4/L5 可在后续逐步打开，但每层都有独立 fail-closed 门。 |
| 维护成本 | 沿用 `BrokerAdapter` 合同，避免引入真实 SDK 依赖和跨 runtime 复杂度。 |
| 诚实性 | 不把 CR043 静态可行性误称为仿真可运行。 |

不推荐方案：

| 方案 | 不推荐原因 |
|---|---|
| 本 CR 直接实现真实 Goldminer adapter | 需要凭据、登录/连接、账户字段和真实 SDK runtime，均未授权。 |
| 在代码中预埋真实 SDK import | 现有测试明确禁止 broker/network/trading runtime import/call；也会让 no-operation guard 难以证明。 |
| 将 `simulation_ready` 设为 true | 当前没有任何 L3/L4/L5 运行证据；必须保持 false。 |

## 5. 门禁分层：CP2、CP3、L3+ 逐 run

| 内容 | 必须进入 CP2 | 必须进入 CP3 | 仅 L3+ 逐 run 授权后可执行 |
|---|---:|---:|---:|
| CR044 是否继续 standard admission | 是 | 否 | 否 |
| L1/L2 授权和 L3/L4/L5 不授权声明 | 是 | 是，作为架构前提 | 否 |
| 凭据/账户材料不收集不记录 | 是 | 是，作为安全设计 | 否 |
| `gm` 主选 / `gmtrade` fallback | 否 | 是 | 否 |
| blocked-first admission gate 架构 | 否 | 是 | 否 |
| no-operation guard / operation counters | 是，确认安全目标 | 是，确认实现边界 | 否 |
| redaction 规则 | 是，确认安全目标 | 是，确认架构合同 | 否 |
| per-run authorization manifest 形态 | 是，确认不自动授权 | 是，确认后续 gate 输入 | 否 |
| 读取凭据或账号标识 | 否 | 否 | 仅 L3 单次授权；不得记录值 |
| 登录 / connect | 否 | 否 | 仅 L3/L4 单次授权且 run manifest 明确允许 |
| 查询 cash / positions / orders / fills | 否 | 否 | 仅 L4 单次授权；结果必须 redacted |
| submit / cancel / simulation/live | 否 | 否 | 仅 L5 单次授权；需 kill switch、订单白名单和对账计划 |
| provider_fetch / lake_write / catalog_publish | 否 | 否 | 本 CR 不建议授权；若需要另起 CR |

## 6. Story 拆解建议与 LLD policy

建议 meta-po 后续在 CP3 通过后生成一个 CR044 LLD batch：`CR044-LLD-BATCH-A-ADMISSION-GUARD`。在 L3+ 未授权前，所有 Story 的实现策略只能是 blocked-first / fixture-only。

| Story ID | 标题 | 推荐 LLD policy | 触发原因 | 主要输出候选 | 依赖 | 备注 |
|---|---|---|---|---|---|---|
| CR044-S01 | authorization and secret boundary | `full-lld` | security、permission、runtime_authorization | authorization level model、sensitive field policy、decision table、redaction contract | CP2 | 阻塞所有后续 Story；不得要求用户提供凭据。 |
| CR044-S02 | admission gate and capability state | `full-lld` | cross-module-contract、data-model、rollback | capability state enum/contract、blocked result mapping、kill switch input | S01、CP3 | 保持 `simulation_ready=false`、`live_ready=false`，除非 L5 后续 CR 改变。 |
| CR044-S03 | readonly query field mapping blocked-first | `full-lld` | external-interface、data-model、security | cash/position/order/fill 字段映射候选、blocked readonly result、UNKNOWN 字段处理 | S01、S02 | L2 只做 fixture 和静态映射；L4 才能查询真实账户。 |
| CR044-S04 | submit/cancel kill switch contract | `full-lld` | security、external-interface、rollback | order intent whitelist、cancel whitelist、hard kill switch、operation count gate | S01、S02 | L2 不调用 submit/cancel；L5 才能执行。 |
| CR044-S05 | reconciliation and redacted evidence | `full-lld` | data-model、reconciliation、audit | offline reconciliation schema、redacted evidence shape、discrepancy taxonomy | S03、S04 | L2 使用 fixture；真实 broker reconciliation 需 L4/L5。 |
| CR044-S06 | runbook and no-real-operation guardrails | `technical-note` 或 `full-lld` | runtime_authorization、validation、docs | no-operation checklist、QA 验证入口、L3+ run manifest 模板说明 | S01-S05 | 若 runbook 要驱动自动 guard，升为 `full-lld`；若只写文档，可 `technical-note`。 |

推荐 Wave：

| Wave | Story | 并行性 | Gate |
|---|---|---|---|
| W1 | S01 | 串行 | CP2 通过后起草 LLD；定义授权和 redaction 基线。 |
| W2 | S02、S03 | 可并行，但共享 S01 合同 | CP3 通过后；不得新增真实 SDK import。 |
| W3 | S04、S05 | 可并行，但共享 S02 gate | 只写 kill switch / reconciliation 合同和 fixture。 |
| W4 | S06 | 串行收敛 | 汇总 guardrails、runbook 和 CP7 验证入口。 |

CP5 批次建议：

| 批次 | 范围 | 发起条件 | 不得包含 |
|---|---|---|---|
| `CR044-LLD-BATCH-A-ADMISSION-GUARD` | S01-S06 全量设计证据 | CP2/CP3 人工确认通过；meta-se 已完成 Story 计划 | 凭据值、账号值、真实 SDK runtime 调用、simulation/live 授权 |

## 7. 文件影响范围

本轮只写本 handoff。以下为后续 Story/LLD 的候选影响范围，不代表本轮修改。

| 文件 / 目录 | 影响类型 | 说明 | 当前轮状态 |
|---|---|---|---|
| `process/handoffs/META-SE-CR044-CP2-CP3-DESIGN-2026-06-11.md` | 新增 | 本交还文件 | 已写入 |
| `docs/design/HLD.md` 或 CR044 scoped HLD | 后续可能更新 / 新增 | CP3 架构方案与 ADR 归档 | 本轮不修改 |
| `docs/design/ARCHITECTURE-DECISION.md` | 后续可能更新 | 记录 blocked-first、SDK 主选、redaction、per-run authorization ADR | 本轮不修改 |
| `docs/design/FEATURE-DESIGN-MATRIX.md` | CP3 后新增/更新 | Feature 设计矩阵和 LLD policy | 本轮不修改 |
| `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/stories/CR044-*.md` | CP3 后新增/更新 | Story 卡片和批次计划 | 本轮不修改 |
| `engine/broker_adapter.py` | 后续候选修改 | admission gate、capability state、blocked result 扩展；不得导入真实 SDK | 本轮不修改 |
| `tests/test_cr042_broker_adapter_contract.py` | 后续可能补充 | 保持现有 CR042 合同回归 | 本轮不修改 |
| `tests/test_cr044_goldminer_admission_guard.py` | 后续候选新增 | CR044 no-operation、redaction、kill switch、blocked-first 测试 | 本轮不修改 |
| `docs/quality/*` | 后续验证输出 | CP7 验证报告、no-operation 证据、redaction 证据 | 本轮不修改 |

文件所有权建议：

| 对象 | 主要写入方 | 约束 |
|---|---|---|
| 设计 / Story / LLD 产物 | meta-se / meta-dev | CP3/CP5 通过前不得进入实现。 |
| `engine/broker_adapter.py` | meta-dev | 只能在 CP5 通过后改；真实 SDK import/call 继续禁止。 |
| 测试文件 | meta-dev / meta-qa | fixture-only；不得访问网络、SDK runtime、凭据或账户。 |

## 8. 测试 / 验证矩阵

| 验证项 | 层级 | 推荐验证方式 | 通过标准 | 禁止事项 |
|---|---|---|---|---|
| no-operation guard | L2 fixture | 单元测试构造非零 `operation_counts` | 任一真实操作计数非零时 blocked；默认全部为 0 | 不执行真实 broker call |
| sensitive field guard | L2 fixture | 构造含 token/account/password/session/cookie/private_key 的 payload | 返回 blocked 或 redacted；报告中无敏感 key/value | 不记录真实值 |
| static import boundary | L2 static | AST 扫描 `engine/broker_adapter.py` | 无 `gm`、`gmtrade`、network、broker/trading runtime import/call | 不安装/导入真实 SDK 作为项目依赖 |
| admission capability | L2 fixture | 调用 stub/admission capability | `real_broker_enabled=false`、`simulation_ready=false`、`live_ready=false`、`not_authorization=true` | 不把 SDK 静态候选标成授权 |
| kill switch | L2 fixture | 构造 disabled/default/unauthorized 状态 | 默认 blocked；任一 kill switch disabled 生效 | 不用真实订单验证 |
| readonly mapping | L2 fixture | 静态 fixture 覆盖 cash/position/order/fill 字段 | UNKNOWN 字段状态化；无真实账户查询 | 不查询 cash/position/order/fill |
| submit/cancel contract | L2 fixture | order intent whitelist 与 blocked result | 未授权时 submit/cancel 返回 blocked，真实 order/cancel count 为 0 | 不下单、不撤单 |
| reconciliation | L2 fixture | 本地 ledger 与 fixture execution report 对账 | 差异分类可审计；证据脱敏 | 不拉取真实成交 |
| CP7 no-real-operation evidence | L2 static + tests | pytest + 静态扫描 + artifact scan | 所有真实操作计数为 0；无敏感字段泄漏 | 不 provider fetch / lake write / catalog publish |

建议最小回归入口（后续实现后）：

| 命令 | 说明 |
|---|---|
| `uv run --python 3.11 pytest -q tests/test_cr042_broker_adapter_contract.py tests/test_cr044_goldminer_admission_guard.py` | 保持 CR042 合同并验证 CR044 guard。 |
| `uv run --python 3.11 python scripts/<future-static-scan>.py` | 若新增静态扫描脚本，必须检查 forbidden imports/calls 和敏感字段。 |

## 9. No-Operation Guard 设计要求

| 动作 | L2 设计行为 | L3+ 后续行为 |
|---|---|---|
| SDK import / call | 项目源码禁止；只允许 CR043 已完成的隔离静态事实作为输入 | 需要独立授权和隔离策略；真实 adapter 不应静默导入 |
| credential_read | blocked；计数必须为 0 | L3 单次授权才可在用户本地读取，且不得记录值 |
| login / connect | blocked；计数必须为 0 | L3/L4 单次授权才可执行 |
| account / cash / position / order / fill query | blocked；计数必须为 0 | L4 单次授权才可执行，证据必须 redacted |
| order_submit / order_cancel | blocked；计数必须为 0 | L5 单次授权才可执行，需订单白名单、kill switch、撤单/对账计划 |
| simulation/live start | blocked | L5+ 单次授权；不得由 CP3 设计确认自动授权 |
| provider_fetch / lake_write / catalog_publish | blocked | 本 CR 不建议授权；若必须，另起 CR |

必须保留的阻断语义：

| 条件 | 结果 |
|---|---|
| 未显式授权层级 | `blocked` |
| 授权层级不足 | `blocked` |
| kill switch disabled 或缺失 | `blocked` |
| 敏感字段出现在输入 / 输出 / artifact | `blocked` 或 redacted 后降级；真实值不得保存 |
| 任何 forbidden operation count 非零 | `blocked`，并在证据中暴露计数名称但不暴露敏感值 |
| SDK 静态候选存在 | 只可影响 `sdk_static_candidate`，不得提升到 `simulation_ready` |

## 10. Redaction 设计要求

敏感材料分类：

| 类别 | 示例 | 处理 |
|---|---|---|
| 凭据 | token、secret、password、passwd、trade_password、private_key | 不得收集；若 fixture 出现字段名，测试应 blocked；真实值不得落盘。 |
| 会话 | session、cookie | 不得收集；不进入日志、报告、artifact。 |
| 账户标识 | account_id、broker_account、real_account | 按敏感字段处理；后续 L3+ 证据只允许脱敏占位或 hash，不存原值。 |
| broker order reference | order_id、broker_order_id、entrust_no、client_order_id | L2 fixture 可用假值；L5 真实值必须 redacted。 |
| SDK/endpoint 配置 | endpoint、login context | 当前不授权读取；后续只可在 run manifest 中记录是否存在，不记录值。 |

Redaction 输出原则：

| 产物 | 允许 | 禁止 |
|---|---|---|
| Markdown 设计 / 报告 | `REDACTED`、`present=true/false`、字段结构摘要 | 原始凭据、账号、session、cookie、订单真实编号 |
| JSON/YAML fixture | 假值、脱敏占位、schema 字段 | 真实 token/account/session |
| 测试失败输出 | 字段名、规则 ID、计数名 | 字段值 |
| CP7 证据 | 操作计数、blocked reason、脱敏 diff | broker 原始 payload |

## 11. Per-Run Authorization 设计要求

后续若申请 L3+，必须由 meta-po 发起逐 run 授权；本 CP2/CP3 不能替代运行授权。建议 run authorization manifest 至少包含以下字段，但不得包含凭据值：

| 字段 | 说明 |
|---|---|
| `run_id` | 单次授权 ID，过期后不可复用。 |
| `authorized_level` | `L3_credential_check` / `L4_readonly_query` / `L5_submit_cancel_reconcile`。 |
| `allowed_actions` | 明确动作白名单，如 `credential_presence_check`、`query_cash`、`submit_single_fixture_order`。 |
| `forbidden_actions` | 默认列出所有未授权动作。 |
| `time_window` | 授权有效时间；过期 fail-closed。 |
| `input_source` | 用户本地提供 / 环境存在性检查；不得记录值。 |
| `max_real_operation_counts` | 每类真实操作允许上限；未列出即 0。 |
| `kill_switch_required` | 必须为 true。 |
| `redaction_policy` | 证据脱敏规则版本。 |
| `evidence_paths` | 运行后只保存脱敏证据路径。 |

逐 run 授权必须满足：

| 条件 | 要求 |
|---|---|
| 单次授权 | 一次授权只覆盖一个 run，不可默认为后续 run 继续有效。 |
| 最小动作 | L3 不能隐含 L4/L5；L4 不能隐含 submit/cancel；L5 不能隐含 live。 |
| 可撤销 | 用户可在运行前或运行中触发 kill switch，触发后不得重试真实操作。 |
| 证据脱敏 | 只保存 redacted evidence，不保存原始 broker payload。 |

## 12. Kill Switch 设计要求

Kill switch 必须是 fail-closed 双层门：

| 层 | 规则 |
|---|---|
| Global hard switch | 默认 disabled；未显式 enabled 视为 disabled。 |
| Per-run switch | 每个 L3+ run manifest 必须显式 enabled；缺失、过期、动作不匹配均 disabled。 |
| Operation-level switch | submit/cancel/simulation/live 还需要动作级白名单；不在白名单即 blocked。 |

触发 kill switch 后：

| 状态 | 行为 |
|---|---|
| 尚未调用真实 runtime | 直接返回 blocked result，真实操作计数保持 0。 |
| 正在 L4 查询 | 停止后续查询，不做重试；只保留脱敏 partial evidence。 |
| 正在 L5 submit/cancel | 不发起新 submit；是否 cancel 已发订单必须由原 run authorization 明确，否则停止并升级人工处理。 |

## 13. Reconciliation 设计要求

L2 reconciliation 只做离线合同，不做真实 broker 对账。

| 输入 | L2 允许 | L3+ 才允许 |
|---|---|---|
| 内部 order intent | fixture / paper intent | 后续真实 run 的脱敏 intent 摘要 |
| broker accepted order | fixture 假值 | L5 submit 后 broker 脱敏回报 |
| fill / execution report | fixture 假值 | L4/L5 查询或事件回报，必须 redacted |
| cash / position snapshot | fixture / paper ledger | L4 查询结果，必须 redacted |

对账状态建议：

| 状态 | 含义 |
|---|---|
| `matched_fixture` | L2 fixture 内部一致。 |
| `blocked_no_authorization` | 因无 L3/L4/L5 授权未执行真实对账。 |
| `unknown_broker_field` | 字段结构未知，等待官方结构或账号权限核对。 |
| `mismatch_requires_manual_review` | 后续真实 run 出现差异，必须人工审查，不自动补单或撤单。 |

禁止自动化行为：

| 行为 | 处理 |
|---|---|
| 对账失败后自动补单 | 禁止 |
| 对账失败后自动撤单 | 禁止，除非 L5 run manifest 明确授权该撤单动作 |
| 使用真实 broker payload 作为长期 fixture | 禁止；只能保存脱敏结构或合成 fixture |

## 14. 风险与回退

| 风险 ID | 风险 | 影响 | 缓解 | 回退 |
|---|---|---|---|---|
| R-01 | 静态 SDK 可映射但账号权限不可用 | 无法进入真实仿真 | CP2/CP3 明确 CR044 可关闭为 `blocked-by-account-permission` | 回退 CR043 `NEEDS_ACCOUNT_PERMISSION` |
| R-02 | 凭据或账户标识泄漏 | 安全事故 | 零凭据持有、redaction、sensitive field guard、artifact scan | 立即停止 CR044，删除/轮换外部凭据由用户自行处理；仓库不得保存值 |
| R-03 | `simulation_ready` 被误读为已授权 | 用户可能误运行 | capability 永远保留 `not_authorization=true`，L5 前 `simulation_ready=false` | CP3 返工 capability 语义 |
| R-04 | 真实 SDK import 进入项目路径 | CI / runtime 可能误触 broker | AST 禁止 import/call，依赖不得加入项目锁定 | 回退相关 Story，恢复 stub-only |
| R-05 | kill switch 语义不足 | 无法及时停止真实动作 | 双层 kill switch + action whitelist + no retry | L5 不通过，停留 offline design |
| R-06 | reconciliation 差异被自动修正 | 产生非授权交易 | 对账只出差异，不自动补单/撤单 | 转人工 review / 后续 CR |
| R-07 | `gmtrade` runtime 不兼容 Python 3.11 | 设计复杂度上升 | `gm` 主选，`gmtrade` 仅 fallback | 若必须 `gmtrade`，另行设计 Python 3.10 隔离 runtime |

## 15. 给 meta-po 的 CP2/CP3 Brief 摘要

CP2 建议主结论：

| 项 | 建议 |
|---|---|
| CR044 是否继续 | 继续 standard admission design。 |
| 当前授权 | 仅 L1/L2；L3/L4/L5 全部不授权。 |
| 用户需确认 | `approve` 仅接受 L1/L2 设计和不授权边界，不授权任何真实 broker runtime。 |
| 若不通过 | 关闭或挂起为 `blocked-by-authorization-scope` / `blocked-by-account-permission`。 |

CP3 建议主结论：

| 项 | 建议 |
|---|---|
| 推荐架构 | blocked-first admission gate + 保留 `GoldminerStubBrokerAdapter` + fixture-only guardrails。 |
| SDK 选择 | `gm` 为 Python 3.11 主选静态候选；`gmtrade` 为 Python 3.10 fallback。 |
| ADR 候选 | blocked-first、zero credential retention、per-run authorization、dual kill switch、redacted reconciliation、no SDK import in L2。 |
| Story / LLD | S01-S05 `full-lld`，S06 默认 `technical-note`，若 runbook 驱动自动 guard 则升 `full-lld`。 |
| 不授权项 | credential_read、login、connect、account/cash/position/order/fill query、submit、cancel、simulation/live、provider_fetch、lake_write、catalog_publish。 |

后续 L3+ 只有在以下条件全部满足后才可执行：

| 条件 | 状态 |
|---|---|
| CP2 人工确认授权边界 | 待 meta-po 发起 |
| CP3 人工确认架构 | 待 meta-po 发起 |
| CP5 全量 Story 设计证据确认 | 未开始 |
| 用户逐 run 授权 | 未授权 |
| run manifest、kill switch、redaction、no-operation guard 已就绪 | 未实现 |

## 16. 本轮结论

本轮 meta-se 结论：

1. CR044 可以进入 CP2/CP3 设计门禁，但不能进入任何真实 broker runtime。
2. 推荐 CP3 架构是 blocked-first admission gate，保留 `GoldminerStubBrokerAdapter` 为唯一 Goldminer 运行态对象，L2 只做 fixture-only 工程资产。
3. `gm` 可作为 Python 3.11 主选静态候选；`gmtrade` 仅作为 Python 3.10 fallback，不应引入当前项目 runtime。
4. Story 拆解建议为 S01-S06，一个 LLD batch；S01-S05 需要 `full-lld`，S06 视 runbook 自动化程度为 `technical-note` 或 `full-lld`。
5. 所有真实 runtime 行为必须 fail-closed；CP2/CP3 的 `approve` 不得被解释为 L3+ 运行授权。
