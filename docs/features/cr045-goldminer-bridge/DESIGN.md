---
status: draft-for-cp4
version: "1.0"
feature_id: "FEAT-CR045-GOLDMINER-BRIDGE"
feature_name: "Goldminer Windows Bridge L2 Skeleton and WSL/Linux Client Contract"
source_blueprint: "waived-for-cr-scoped-hld"
source_hld: "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
source_adr: "docs/design/ARCHITECTURE-DECISION-CR045.md"
source_matrix: "docs/design/FEATURE-DESIGN-MATRIX-CR045.md"
related_stories:
  - "CR045-S01"
  - "CR045-S02"
  - "CR045-S03"
  - "CR045-S04"
  - "CR045-S05"
  - "CR045-S06"
lld_policy_summary: "S01-S05 full-lld; S06 technical-note unless executable manifest/schema/guard is introduced"
confirmed_by: ""
confirmed_at: ""
---

# Feature Design: CR045 Goldminer Windows Bridge

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-11 | meta-se | 创建 CR045 Feature 级设计，冻结 Windows bridge / WSL-Linux client / allowlist / redaction / no-operation 的 CP4 输入。 |

## 摘要

| 项目 | 内容 |
|---|---|
| Feature 目标 | 在不启动真实 runtime、不读取凭据、不查询账户、不交易的前提下，为 Windows-side Goldminer bridge skeleton 和 WSL / Linux client 建立可审查的合同、失败路径和验证边界。 |
| 推荐方案 | Windows trading PC 是唯一未来 Goldminer SDK runtime / 交易执行边界；WSL / Linux 只做研究、回测、组合生成、order intent 和 allowlist bridge client；当前只实现 L2 skeleton / fixture / static validation。 |
| 关键取舍 | 优化安全隔离、可审计和后续 L3/L4/L5 分层授权；牺牲短期真实只读验证能力。 |
| 下游 Story | CR045-S01, CR045-S02, CR045-S03, CR045-S04, CR045-S05, CR045-S06 |
| LLD 策略 | S01-S05 `full-lld`；S06 `technical-note`，如引入自动 manifest、schema、guard script 或状态机则升 `full-lld`。 |

## 背景与问题

| 问题 ID | 背景 | 触发场景 | 影响 | 若不设计的风险 |
|---|---|---|---|---|
| P-CR045-01 | 用户 Windows 电脑已登录 Goldminer，但 WSL / 未来 Linux research server 不能直接安全接入。 | UC-CR045-01/02/03 | 拓扑、SDK runtime、凭据驻留、网络边界 | 后续实现可能误选 WSL / Linux direct SDK，导致凭据或真实 SDK 进入研究环境。 |
| P-CR045-02 | 当前只授权 L2 skeleton / fixture/static，不授权 L3/L4/L5。 | CP2/CP3 DQ | Story dev_gate、测试入口、CP8 结论 | CP5/CP6/CP7 可能被误解为允许启动 runtime 或查询账户。 |
| P-CR045-03 | Readonly probe 需要表达合同，但不能触发真实查询。 | UC-CR045-03 | API schema、blocked reason、operation counters | 只读 skeleton 可能被误写为 real-readonly-verified。 |
| P-CR045-04 | 敏感字段和交易标识必须零泄漏。 | S01/S05/S06 | redaction、fixture、artifact scan | token/account_id/session/order ref 可能进入仓库、日志或报告。 |

## 上游依据与输入

| 来源 | 路径 / ID | 被本设计消费的内容 |
|---|---|---|
| HLD | `docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md` | 推荐方案、模块边界、Use Case traceability、Story 拆解建议、Feature 级设计触发条件。 |
| ADR | `docs/design/ARCHITECTURE-DECISION-CR045.md` | ADR-CR045-001..007：拓扑、API allowlist、凭据驻留、kill switch、后续授权、Story/LLD 策略、关闭语义。 |
| CP3 checkpoint | `process/checkpoints/CP3-CR045-HLD-REVIEW.md` | 用户已批准 CP3 六项决策；确认 Windows trading PC 是唯一 Goldminer SDK/runtime/execution boundary。 |
| CR | `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | L1/L2 当前授权，L3/L4/L5 当前不授权；关闭条件和验收标准。 |
| Existing contract | `engine/broker_adapter.py` | CR042/CR044 已有 sensitive field patterns、blocked reasons、operation counters、Goldminer not-authorized 语义；CR045 可复用概念但不得本轮写实现。 |

## 目标与非目标

| 类型 | 内容 | 来源 |
|---|---|---|
| Goal | 定义 Windows bridge skeleton 的授权边界、API allowlist、blocked-first、redaction 和 no-operation evidence。 | HLD §5/§10/§14/§15 |
| Goal | 定义 WSL / Linux bridge client 的 JSON-safe 请求/响应合同和 network precheck 行为。 | HLD §7/§10/§12 |
| Goal | 为 S01-S06 生成可进入 CP5 的 Story 边界、文件 owner、LLD 策略和验证入口。 | HLD §19 |
| Non-Goal | 不启动 Windows bridge runtime，不登录/连接 Goldminer，不查询 cash/position/order/fill/account state。 | CP3 checkpoint |
| Non-Goal | 不读取、请求、收集或记录 token/account_id/账号/密码/session/cookie/private key。 | ADR-CR045-003 |
| Non-Goal | 不实现真实 adapter，不 provider fetch，不 lake write，不 catalog publish，不下单/撤单，不 simulation/live。 | CR045 |

## Feature 边界与相邻对象

| 对象 | 本 Feature 负责 | 不负责 | 相邻 Feature / 模块 | 边界判定依据 |
|---|---|---|---|---|
| Windows Bridge skeleton | API 合同、future runtime boundary、fixture/static response、hard-off 默认状态 | 启动 Windows service、导入真实 SDK、登录/连接 Goldminer | future L3 bridge runtime CR | ADR-CR045-001/004 |
| WSL / Linux client | 构造 allowlist request、处理 blocked/fixture response、network precheck 只返回授权状态 | 持有 token/account_id、直接导入 `gm` / `gmtrade`、直接连接 Goldminer | research/backtest/order-intent modules | ADR-CR045-001 |
| Authorization gate | L1-L5 层级、allowlist、kill switch、blocked reason | 批准运行授权；真实 runtime 权限由 meta-po gate 处理 | Meta Flow human gate | ADR-CR045-004/005 |
| Readonly probe skeleton | request/response shape、blocked-first result、real_readonly_verified=false | cash/position/order/fill/account state 真实查询 | future L4 readonly probe CR | ADR-CR045-002/007 |
| Redaction evidence | 敏感字段类别、计数、operation counts=0、artifact scan rules | 保存真实敏感值或真实 broker payload | CR044 redaction concepts | ADR-CR045-003 |
| User runbook | 后续 L3/L4/L5 gate 入口、不授权项、skeleton-ready 关闭语义 | 授权用户真实运行或提供凭据 | CP8 release readiness | ADR-CR045-005/007 |

## 现有代码位置

| 区域 | 路径 | 当前职责 | 变更方式 |
|---|---|---|---|
| Broker-neutral contract | `engine/broker_adapter.py` | 已有 CR042/CR044 blocked reasons、sensitive patterns、operation counters、Goldminer not-authorized 概念。 | CP4 不改代码；CP5 LLD 判定是否新增 CR045 bridge contract 模块或最小复用。 |
| CR044 guard tests | `tests/test_cr044_goldminer_admission_guard.py` | 已验证 CR044 offline admission guard。 | CR045 不抢占；如需回归引用，由 S05 在 LLD 中声明。 |
| Future bridge contract | `engine/goldminer_bridge_contract.py` | 当前不存在。 | S02 未来 primary owner，CP5 后才可创建。 |
| Future bridge client | `engine/goldminer_bridge_client.py` | 当前不存在。 | S03 未来 primary owner，CP5 后才可创建。 |
| Future tests | `tests/test_cr045_goldminer_bridge_contract.py` 等 | 当前不存在。 | S02/S03/S04/S05 分别 primary/shared owner，CP5 后才可创建。 |
| Runbook | `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` | 当前不存在。 | S06 未来 primary owner，CP5 技术说明确认后才可创建。 |

## 推荐方案

| 设计点 | 推荐做法 | 理由 | 代价 |
|---|---|---|---|
| Topology | Windows-side bridge skeleton + WSL / Linux allowlist client | 凭据和 SDK runtime 留在 Windows 用户边界，Linux 侧保持研究和 client 角色。 | 需要维护跨 OS 合同和未来本地网络边界。 |
| API allowlist | L2 仅 `health`、`capabilities`、`readonly_probe_skeleton` | 覆盖 CR045 目标且不触发真实账户查询。 | L2 无法证明真实只读字段。 |
| Authorization | 默认 hard-off；缺 per-run 授权或 action 不在 allowlist 即 blocked | 外部 broker 接入必须 fail-closed。 | 后续真实验证需要额外 gate。 |
| Data exchange | JSON-safe schema，禁止 SDK object 透传 | 易脱敏、跨 OS、便于 fixture/static 验证。 | 字段语义需后续 L4 授权确认。 |
| Evidence | redacted evidence + zero operation counters + static artifact scan | 能证明 no-operation 和零敏感值，不需要 runtime。 | 不能证明真实 broker 状态。 |

## 方案对比与决策记录

| Decision ID | 方案 | Pros | Cons | Impact Surface | Recommendation | When to switch |
|---|---|---|---|---|---|---|
| DQ-FD-CR045-01 | Windows bridge skeleton + WSL/Linux client | 安全隔离、符合 CP3、后续可逐 run 授权 | 需维护 bridge contract | 架构、接口、安全、Story DAG | 推荐，已由 CP3 接受 | 官方 endpoint 可验证且 L3/L4 授权后再切换。 |
| DQ-FD-CR045-01 | WSL/Linux direct SDK | 路径短 | 凭据进入 Linux，SDK runtime 风险高 | 安全、依赖、运行授权 | 不采用 | 仅用户重开 CP3 安全决策后可考虑。 |
| DQ-FD-CR045-02 | S06 technical-note | 足以覆盖文档、runbook 和 follow-up gate | 不能承载可执行 guard/schema | CP5 设计证据、文档 | 推荐 | 一旦新增可执行 manifest/schema/guard，升 full-lld。 |

## 模块变更

| Module | 变更 | 输入 | 输出 | 失败路径 |
|---|---|---|---|---|
| Authorization model | 定义 L1-L5、allowed/offline-only actions、not-authorized actions | CP2/CP3 DQ、CR045 | authorization table、blocked reasons | 需要真实值或真实运行时，停止并交回 meta-po。 |
| Bridge API schema | 定义 health/capabilities/readonly probe skeleton schema | HLD/ADR、Feature Matrix | JSON-safe request/response | action 不在 allowlist 或 L4 未授权时 blocked。 |
| WSL/Linux client contract | 定义 fixture transport、network precheck、runtime-not-started response | Bridge API schema | client-side contract | 尝试连接真实 bridge runtime 时 blocked。 |
| Readonly allowlist | 定义 readonly skeleton allowlist 和 blocked-first response | Authorization model、API schema | `real_readonly_verified=false` response | cash/position/order/fill/account state 查询请求 blocked。 |
| Redaction/no-operation validation | 定义敏感字段规则、operation counters 和 artifact scan | Existing sensitive patterns、CP3 non-authorized list | redacted evidence requirements | 发现真实敏感值或 operation count 非 0 时 FAIL。 |
| Runbook | 定义用户可见后续授权流程和不授权项 | 上游 Story design evidence | CP8/CP5 可消费的 runbook outline | 被误写为运行授权时返工。 |

## 数据模型与状态

| Object | Owner | 新增 / 修改字段 | 状态变化 | 兼容性 |
|---|---|---|---|---|
| BridgeHealth | S02 | `status`、`runtime_started=false`、`not_authorization=true`、`reason`、`schema_version` | fixture/blocked only | 新对象；不影响现有 broker adapter。 |
| BridgeCapabilities | S02 | `real_broker_enabled=false`、`readonly_probe_ready=false`、`simulation_ready=false`、`live_ready=false`、`allowed_actions` | hard-off by default | 必须与 HLD/ADR 不授权项一致。 |
| ReadonlyProbeRequest | S04 | `probe_kind`、`request_id`、`client_context`、`contains_sensitive_material=false` | L4 未授权时只进入 blocked path | 不包含 token/account_id 或真实账户字段。 |
| ReadonlyProbeResponse | S04 | `status=blocked`、`reason`、`real_readonly_verified=false`、`operation_counts` | blocked-first | 不含 cash/position/order/fill/account data。 |
| BridgeEvidence | S05 | `redaction_summary`、`forbidden_operation_counts`、`artifact_scan_summary` | no-operation evidence | 只记录字段类别、计数和占位符。 |
| FollowUpGateDescriptor | S06 | `level=L3/L4/L5`、`required_authorization`、`not_authorized_by_current_cr` | doc-only | 不作为可执行 manifest。 |

## API / 接口设计

| Interface ID | 调用方 | 被调用方 | 输入契约 | 输出契约 | 错误模型 |
|---|---|---|---|---|---|
| IF-CR045-01 health | WSL / Linux client | Windows bridge skeleton fixture | action=`health`，无凭据字段，无真实 endpoint requirement | `BridgeHealth`；`runtime_started=false`；`not_authorization=true` | `windows_bridge_runtime_not_authorized`、`operation_not_whitelisted` |
| IF-CR045-02 capabilities | WSL / Linux client | Windows bridge skeleton fixture | action=`capabilities`，client version，可选 fixture mode | `BridgeCapabilities`；real/simulation/live flags 全 false | `global_kill_switch_disabled`、`per_run_authorization_missing` |
| IF-CR045-03 readonly_probe_skeleton | WSL / Linux client | Authorization gate / readonly probe skeleton | action=`readonly_probe_skeleton`，probe_kind 仅作 skeleton，不含真实账户数据 | blocked `ReadonlyProbeResponse`；`real_readonly_verified=false`；operation counts 全 0 | `goldminer_readonly_query_not_authorized`、`sensitive_material_present` |
| IF-CR045-04 static_validation | meta-qa / tests | Redaction evidence builder | artifact paths and fixture payloads，不读取 `.env` | scan summary、violations count、zero operation evidence | `forbidden_operation_nonzero`、`sensitive_material_present` |

## 关键流程

| Flow ID | 触发条件 | 主流程 | 异常流程 | 输出 / 状态变化 | 观测点 |
|---|---|---|---|---|---|
| FLOW-CR045-01 | CP6 后 fixture health check | client 构造 health -> fixture transport -> authorization gate hard-off -> response | 若实现尝试启动 Windows runtime，CP6/CP7 FAIL | `runtime_started=false`、operation counts=0 | Fixture test + CP7 report |
| FLOW-CR045-02 | capabilities request | client 请求 capabilities -> schema builder -> redaction -> response | 若出现 `simulation_ready=true` / `live_ready=true`，CP7 FAIL | `real_broker_enabled=false` | Static assertion |
| FLOW-CR045-03 | readonly probe skeleton | request -> allowlist -> L4 未授权 -> blocked response -> evidence | 请求含 token/account_id 或真实 query payload 时 blocked/redacted | `real_readonly_verified=false`、blocked reason | Fixture + artifact scan |
| FLOW-CR045-04 | follow-up authorization request | runbook 指示交回 meta-po -> 新 gate 决策 | 用户在对话/仓库提供真实凭据时停止并提示不记录 | 后续 CR / DQ，不在 CR045 自动执行 | Manual review |

## 人机协作与确认点

| 确认点 | 触发条件 | 需要谁确认 | 推荐方案 | 备选方案 | 不授权项 |
|---|---|---|---|---|---|
| DQ-FD-CR045-RUNTIME | 任何 Story 需要启动 Windows bridge、登录 Goldminer 或真实 readonly query | meta-po 发起用户人工 gate | 停止当前实现，转 L3/L4 授权或新 CR | 关闭为 skeleton-ready / blocked-by-runtime-authorization | 当前不授权 runtime、凭据、账户查询、交易、simulation/live。 |
| DQ-FD-CR045-S06-UPGRADE | S06 需要新增自动 manifest、schema、guard script 或状态机 | meta-po / CP5 | 升级 S06 为 full-lld | 保持文档 technical-note，延后自动化 | 不得把 runbook 写成运行授权。 |

## 异常、失败与降级策略

| Failure ID | 失败条件 | 系统行为 | 用户可见影响 | 恢复 / 回退 | 测试入口 |
|---|---|---|---|---|---|
| F-CR045-01 | 请求或 artifact 含 token/account_id/session/cookie/private key | blocked/redacted，只记录字段类别和计数 | CP6/CP7 不通过 | 移除真实值并重验；必要时交回 meta-po | TP-SEC-01 |
| F-CR045-02 | action 不在 `health/capabilities/readonly_probe_skeleton` allowlist | blocked，reason=`operation_not_whitelisted` | 请求不可执行 | 修改请求或新 CR 决策 | TP-SEC-03 |
| F-CR045-03 | L4 未授权但请求真实 readonly query | blocked，reason=`goldminer_readonly_query_not_authorized` | 无真实账户数据 | L3/L4 gate 后另行设计 | TP-SEC-04 |
| F-CR045-04 | operation counters 非 0 | CP6/CP7 FAIL | 不能进入 release readiness | 回修实现或测试 fixture | TP-RISK-03 |
| F-CR045-05 | bridge runtime 未启动 | L2 fixture/blocked response，不尝试启动 | 只能证明 skeleton-ready | 后续 L3 bridge health gate | TP-SCOPE-01 |

## 权限与安全

| Rule ID | 规则 | 触发条件 | 失败行为 | 测试入口 |
|---|---|---|---|---|
| SEC-CR045-01 | 零敏感值入仓、入对话、入日志、入 fixture | 任何 artifact scan | FAIL / blocked | `TEST-PLAN.md#权限--安全--失败路径` |
| SEC-CR045-02 | Windows trading PC 是唯一未来 SDK runtime / execution boundary | 代码或文档提到 WSL/Linux direct SDK | FAIL / return to CP3 | Story review |
| SEC-CR045-03 | L2 allowlist 仅三类 action | 新 action 出现 | FAIL / follow-up CR | Fixture tests |
| SEC-CR045-04 | No-operation counters 必须全 0 | CP6/CP7 验证 | FAIL / NEEDS_REWORK | Static validation |
| SEC-CR045-05 | `approve`/CP5/CP8 不等于 runtime authorization | runbook / release wording | FAIL / docs rework | Manual review |

## 测试与验收策略

| 验收对象 | 测试层级 | 覆盖场景 | 自动化方式 | 未自动化原因 / 手工入口 |
|---|---|---|---|---|
| Bridge health/capabilities schema | unit / fixture | UC-CR045-01/02 | CP6 后新增 fixture tests | 当前 CP4 不执行测试。 |
| WSL/Linux client contract | unit / fixture / static | Network precheck and runtime-not-started | CP6 后新增 fixture tests | 不连接真实 runtime。 |
| Readonly probe blocked-first | unit / fixture | L4 missing authorization | CP6 后新增 fixture tests | 不查询真实 account/cash/position/order/fill。 |
| Redaction/no-operation evidence | static / fixture | Sensitive material and operation counters | CP6 后 static artifact scan | 不读取 `.env` 或凭据材料。 |
| Runbook / follow-up gate | manual review | L3/L4/L5 gating and CP8 wording | CP5/CP8 review checklist | 文档语义需人工审查。 |

## 实现顺序

| Step | 内容 | 前置条件 | 输出 | 验证入口 |
|---|---|---|---|---|
| 1 | S01 冻结授权、安全和不授权边界 | CP4 PASS | S01 full LLD | CP5 |
| 2 | S02 定义 bridge health/capabilities skeleton | S01 contract declared | S02 full LLD | CP5 |
| 3 | S03 定义 WSL/Linux client and network precheck | S01 contract declared；S02 API contract frozen by Feature design | S03 full LLD | CP5 |
| 4 | S04 定义 readonly probe allowlist and blocked-first | S01/S02/S03 design evidence | S04 full LLD | CP5 |
| 5 | S05 定义 redaction/no-operation static validation | S01/S02/S03 design evidence；与 S04 可并行设计 | S05 full LLD | CP5 |
| 6 | S06 收敛 runbook and follow-up gates | S01-S05 design evidence | Story technical-note 或升级 full LLD | CP5 |

## Story 拆分建议与 LLD 策略

| Story ID | feature_design_refs | lld_policy.required_level | 触发原因 | 必须进一步设计的问题 | 可用设计证据 |
|---|---|---|---|---|---|
| CR045-S01 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | full-lld | security、permission、runtime_authorization | L1-L5、not-authorized table、sensitive pattern、fail-closed decision table | Feature DESIGN + ADR |
| CR045-S02 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | full-lld | cross-module-contract、external-interface、data-model | health/capabilities schema、schema version、blocked capabilities | Feature DESIGN + S01 |
| CR045-S03 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | full-lld | cross-platform-contract、external-interface、failure-path | fixture transport、network precheck、runtime-not-started behavior | Feature DESIGN + S01/S02 |
| CR045-S04 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | full-lld | external-interface、security、permission、rollback | readonly probe skeleton、allowlist、blocked reasons | Feature DESIGN + S01/S02/S03 |
| CR045-S05 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | full-lld | security、audit、validation、data-model | redaction summary、artifact scan scope、zero counters | Feature DESIGN + S01-S04 |
| CR045-S06 | `docs/features/cr045-goldminer-bridge/DESIGN.md` | technical-note | docs-handoff、runtime_authorization、follow_up_tracking | runbook wording、follow-up gate, no-authorized boundary | Feature DESIGN + S01-S05 |

## 下游消费契约

| 消费方 | 消费时机 | 输入契约 | 输出 / 状态要求 | 降级策略 |
|---|---|---|---|---|
| story-manager | CP4 | Story 拆分建议、file owner、`lld_policy` | Story 卡片含 `feature_design_refs`、依赖、dev_gate、不授权边界 | 缺失则 CP4 FAIL |
| lld-designer / meta-dev | CP5 前 | Story + Feature DESIGN / TEST-PLAN / TASKS | S01-S05 full-lld；S06 technical-note 或升级 full-lld | 出现 L3+ 需求则停止并交回 meta-po |
| meta-qa | CP7 / CP8 | TEST-PLAN、Story AC、不授权项 | Fixture/static verification；no-operation and redaction report | 不可真实运行时记录 skeleton-ready 风险，不阻塞 L2 |

## 风险与回退

| Risk ID | 风险 | 影响 | 缓解 | 回退 |
|---|---|---|---|---|
| R-CR045-FD-01 | CP5/CP6 把 skeleton 当作 runtime authorization | 安全高风险 | Story dev_gate 和 runbook 明确 `real_runtime_authorized=false` | 回退 CP5，修正设计证据。 |
| R-CR045-FD-02 | WSL/Linux direct SDK 被误实现 | 凭据泄漏和运行越权 | forbidden file owner 和 static scan 检查 `gm` / `gmtrade` import | 回退 CP6，必要时 CP3 重新决策。 |
| R-CR045-FD-03 | S02/S04/S05 共享 contract/test 文件冲突 | 开发冲突 | `merge_owner=CR045-S02`，`max_parallel_dev=1` | 串行合并。 |
| R-CR045-FD-04 | S06 technical-note 范围膨胀 | CP5 证据不足 | 升级条件写入 Story 和计划 | 升 full-lld 或延后自动化。 |
