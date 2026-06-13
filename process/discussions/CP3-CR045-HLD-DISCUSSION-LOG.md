---
discussion_id: "CP3-CR045-HLD-DISCUSSION"
change_id: "CR-045"
phase: "solution-design"
agent_role: "meta-se"
status: "ready-for-meta-po-cp3"
created_at: "2026-06-11T21:54:14+08:00"
source_handoff: "process/handoffs/META-SE-CR045-CP3-HLD-2026-06-11.md"
source_cp2: "process/checkpoints/CP2-CR045-REQUIREMENTS-BASELINE.md"
hld: "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
adr: "docs/design/ARCHITECTURE-DECISION-CR045.md"
checkpoint: "process/checks/CP3-CR045-DISCUSSION-CHECKPOINT.json"
cp3_approved: false
runtime_authorization: "L1/L2 only"
---

# CP3 CR045 HLD Discussion Log

## 1. 讨论定位

本日志记录 CR045 HLD 正式成文前的 Architecture Gray Areas 和 advisor table-first 方案形成输入。它不是 CP3 人工审查结果，不授权真实 Windows bridge runtime 或任何 Goldminer 操作。

## 2. 已消费输入

| 输入 | 关键事实 |
|---|---|
| `process/handoffs/META-SE-CR045-CP3-HLD-2026-06-11.md` | meta-po 委托 meta-se 完成 CP3 HLD 输入；推荐主路线是 Windows-side broker bridge，WSL 只调用 allowlist API。 |
| `process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml` | CR045 当前解释为 L2 bridge skeleton / fixture-only / static validation；L3/L4/L5 not-authorized。 |
| `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | formal CR active；authorization_scope 仅 L1/L2；non_authorized_scope 包含凭据读取、runtime、登录/连接、查询、交易、simulation/live、provider/lake/catalog。 |
| `process/checkpoints/CP2-CR045-REQUIREMENTS-BASELINE.md` | 用户回复“同意”，接受 CP2 DQ-01..06 推荐；不授权任何真实 runtime。 |
| CR043 工程事实 | `gm` / `gmtrade` 是静态候选，不证明真实连接；`gmtrade` Python 3.11 风险存在。 |
| CR044 关闭结论 | offline admission guard ready-with-risk；真实 runtime 仍 not-authorized。 |
| `engine/broker_adapter.py` | 现有敏感字段模式、operation counters、blocked reasons 和 CR044 fail-closed 合同可复用。 |

## 3. Architecture Gray Areas

| 灰区 ID | 关键问题 | 为什么会影响架构 | 影响面 | 推荐讨论顺序 | canonical refs | 状态 |
|---|---|---|---|---|---|---|
| AGA-CR045-01 | WSL 如何接入 Windows 已登录 Goldminer 环境 | 决定凭据驻留、SDK runtime 位置、网络边界、依赖方向和后续安全门禁 | 范围 / 模块 / 数据 / 安全 / 验证 / 文档 | 1 | CP2 DQ-02；CR045 handoff；CR043 SPIKE-CONCLUSION | recommendation-selected-for-cp3 |
| AGA-CR045-02 | bridge API 边界是否只允许 health/capabilities/readonly skeleton | 决定 allowlist、kill switch、endpoint 契约和是否会误触账户查询 | 模块 / 外部接口 / 安全 / 失败路径 / QA | 2 | CP2 DQ-01/04；CR045 CR `non_authorized_scope` | recommendation-selected-for-cp3 |
| AGA-CR045-03 | token/account_id 驻留与脱敏策略 | 决定是否存在凭据读取、日志泄漏、fixture 污染和 L3 授权前置 | 数据 / 安全 / 日志 / 证据 / runbook | 3 | CP2 DQ-03；`engine/broker_adapter.py` `SENSITIVE_FIELD_PATTERNS` | recommendation-selected-for-cp3 |
| AGA-CR045-04 | L3/L4/L5 如何从 L2 skeleton 切换 | 决定后续 run gate、Story/LLD 范围、CP8 结论和风险接受 | 运行授权 / Story / 回退 / 验证 / 发布 | 4 | CP2 DQ-04/05/06；CR044 closure | recommendation-selected-for-cp3 |

## 4. Advisor Tables

### AGA-CR045-01：接入拓扑

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| Windows-side bridge，WSL 调用 allowlist API | token/account_id 可留在 Windows 用户本地；WSL 不持有 SDK/凭据；可以集中做 kill switch、redaction、no-operation evidence | 需要设计跨 OS 本地网络边界；后续 runtime 部署多一个 Windows 进程 | 架构、网络、安全、WSL client、runbook、QA | 推荐 | 当前只 L2；若 L3/L4 获批，仍用 bridge 打开最小只读动作。 |
| WSL 直接安装 `gm` / `gmtrade` SDK 并持有 token | 路径短，少一个 bridge 进程 | token/account_id 进入 WSL；`gmtrade` Python 3.11 不匹配；难证明 no-operation；越过 Windows 已登录上下文 | 依赖、凭据、安全、项目 runtime | 不推荐 | 只有用户明确接受 WSL 持有凭据且 CP3 重新批准安全边界才可考虑。 |
| WSL 直连 Windows 终端本地 endpoint | 可能复用终端已有登录态；无需自建完整 bridge SDK 层 | 官方本地 endpoint 未验证；端口、认证、字段、稳定性未知；仍可能触发真实查询 | 外部接口、运行授权、平台兼容 | 治理备选 / Spike | 只有官方或用户提供可验证本地 endpoint 文档，且 L3/L4 逐 run 授权后才切换。 |
| 暂停 CR045，停在 CR044 offline admission | 零 runtime 风险 | 无 bridge skeleton，无法推进 WSL client 合同 | 范围、交付、follow-up | 回退备选 | 若用户拒绝 bridge 维护成本或 CP3 不接受安全风险，关闭为 `blocked-by-runtime-authorization` 或 `not-recommended`。 |

### AGA-CR045-02：Bridge API allowlist

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| 仅 health、capabilities、readonly probe request/response skeleton | 最小可审计；不触发账户查询；适合 fixture/static validation | 不能证明真实 readonly 字段 | API、测试、QA、runbook | 推荐 | 当前 L4 未授权；后续 L4 单次授权才新增真实 readonly endpoint。 |
| 提前定义 cash/position/order/fill 真实查询 endpoint 但默认 disabled | 后续扩展路径清晰 | 容易被误读为已可调用；需要更多敏感字段和错误语义 | API、redaction、安全、Story | 条件不推荐 | 仅在 CP5 后新增 run-gated Story，且 endpoint 默认返回 blocked。 |
| 暂不定义 readonly probe，只做 bridge health | 最保守 | 无法满足 CR045 readonly probe preparation 目标 | 范围、交付 | 回退备选 | 若 CP3 判定 readonly skeleton 仍有误授权风险，则降级到 health-only。 |

### AGA-CR045-03：凭据与证据

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| 零敏感值持有，所有敏感值仅脱敏占位 | 泄漏风险最低；符合 CP2 | 无法验证真实账号权限 | 数据、日志、fixture、文档、QA | 推荐 | 当前 L3 未授权。 |
| 用户 Windows 本地配置，Agent 不读取，bridge runtime 后续只返回状态摘要 | 可支持未来 L3/L4；凭据仍不入 WSL/仓库 | 需要用户手工配置和 run manifest | runbook、Windows bridge、审计 | 后续条件推荐 | 只有 L3 逐 run 授权，且所有值只留用户本地。 |
| 仓库存放 `.env` 或让 Agent 读取 token/account_id | 实施方便 | 违反不授权边界；泄漏风险不可接受 | 全仓、安全、合规 | 禁止 | 不切换。 |

### AGA-CR045-04：后续授权切换

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| L3/L4/L5 独立逐 run gate | 审计清晰；每次真实动作都有授权、时间窗、证据和 kill switch | 决策链较长 | CP3、CP5、runbook、QA、CP8 | 推荐 | 当前不授权真实 runtime。 |
| CP3 一次性批准到 L4 readonly | 可更快得到真实只读结果 | 超出用户当前 CP2 同意内容；需要凭据和 bridge runtime | 安全、运行、验证 | 不推荐 | 仅用户明确新授权后，由 meta-po 重发 runtime_authorization 决策。 |
| CR045 永久只做 skeleton，不保留后续授权入口 | 风险最低 | 后续真实验证需要重开完整设计 | follow-up、用户价值 | 治理备选 | 若用户只想交付离线工程资产，CP8 可关闭为 `readonly-bridge-skeleton-ready`。 |

## 5. Lane Summary

| Lane | 关注点 | 结论 | 进入 HLD / ADR |
|---|---|---|---|
| lane-product | 用户价值、交付预期 | 接受先交付 skeleton-ready；不得承诺 real-readonly-verified。 | HLD §1/§18/§22；ADR-CR045-007 |
| lane-architecture | 模块边界、依赖方向、演进 | 选择 Windows bridge；WSL 不持有 SDK/凭据；真实 SDK 留待未来 Windows runtime。 | HLD §4/§8/§10；ADR-CR045-001/002 |
| lane-quality | 质量、安全、失败路径 | 默认 blocked-first、敏感字段零泄漏、真实操作计数 0。 | HLD §13/§14/§15；ADR-CR045-003/004 |
| lane-docs-check | 可解释性和维护性 | CP3 与 runtime authorization 必须分开；所有不授权项重复列明。 | HLD §21/§22/§24；ADR 不授权声明 |

## 6. 用户选择与解释

| 来源 | 用户输入 / 选择 | meta-se 解释 | 状态 |
|---|---|---|---|
| CP2 人工门禁 | 用户回复“同意” | 接受 DQ-CP2-CR045-01..06 推荐：只授权 L2 skeleton / fixture-only；不授权 L3/L4/L5。 | resolved-by-user for CP2 |
| 当前委托指令 | 要求完成 CR045 CP3 HLD 设计输入，并明确设计边界 | 按指定边界生成 CP3 HLD/ADR/discussion/checkpoint；不发起 CP3 正式人工确认。 | applied |
| CP3 人工门禁 | 尚未由 meta-po 发起 | 本日志只提供 CP3 Decision Brief 输入。 | pending |

## 7. Deferred Options

| ID | 延后项 | 延后原因 | 触发条件 |
|---|---|---|---|
| DAI-CR045-01 | Windows bridge 真实 runtime 服务、端口和进程管理 | 当前不授权启动 runtime | L3 bridge health 单次授权 + CP5/CP6 设计证据完成。 |
| DAI-CR045-02 | 真实 cash/position/order/fill readonly probe | 当前不授权账户查询 | L3 credential setup + L4 readonly probe 逐 run 授权。 |
| DAI-CR045-03 | Goldminer submit/cancel simulation 或 live | 当前不授权 L5，风险高于 CR045 skeleton | L3/L4 通过后另起 L5 CR，并提供订单白名单、kill switch、回滚/对账计划。 |
| DAI-CR045-04 | WSL direct terminal endpoint | 官方 endpoint 未验证 | 官方文档或用户导出证据可验证，且 CP3/CR 重新决策。 |

## 8. CP3 Decision Brief 输入摘要

| 决策 ID | 类型 | 推荐方案 | 备选方案 | 风险 / 切换条件 |
|---|---|---|---|---|
| DQ-CP3-CR045-01 | architecture | Windows bridge + WSL allowlist client | WSL direct SDK；terminal endpoint Spike；暂停 CR045 | 若官方 endpoint 可验证且 L3/L4 授权，可切换；否则保持 bridge。 |
| DQ-CP3-CR045-02 | architecture | L2 API 仅 health/capabilities/readonly skeleton | disabled real endpoint；health-only | L4 授权后才能新增真实 readonly endpoint。 |
| DQ-CP3-CR045-03 | security | token/account_id 仅未来 Windows 本地，Agent 不读取 | 无真实值结构文档；WSL 持有凭据 | 任何真实值需求都暂停并走 L3 gate。 |
| DQ-CP3-CR045-04 | runtime_authorization | 默认 hard-off allowlist + kill switch | 仅日志警告；CP3 批准 L4 | 后续 per-run authorization 才打开对应动作。 |
| DQ-CP3-CR045-05 | risk_acceptance | 接受 skeleton-ready / blocked-by-runtime-authorization | 等 L4 后推进；取消 CR045 | 要求 real-readonly-verified 时必须先 L3/L4。 |
| DQ-CP3-CR045-06 | implementation | S01-S05 full-lld，S06 technical-note/条件升 full-lld | 只做 S01-S03；加入真实 L4/L5 Story | CP3 后再 story-planning，不得加入真实 runtime。 |

## 9. 不授权声明

本 discussion log 不授权读取 token/account_id，不授权启动 Windows bridge runtime，不授权登录/连接 Goldminer，不授权账户/资金/持仓/委托/成交查询，不授权下单/撤单，不授权 simulation/live，不授权 provider fetch/lake write/catalog publish。

