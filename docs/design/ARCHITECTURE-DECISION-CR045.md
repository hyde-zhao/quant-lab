---
status: confirmed
version: "1.1"
complexity: "standard"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-11T22:28:46+08:00"
change_id: "CR-045"
source_hld: "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
---

# Architecture Decision：CR045 Goldminer Windows Bridge Readonly Probe

> 本文件是 CR045 的 CP3 ADR 确认稿。所有决策均已由用户在 CP3 人工门禁中接受，但不授权真实 bridge runtime、Goldminer 登录/连接、账户查询、下单/撤单、simulation/live、provider fetch、lake write 或 catalog publish。

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.1 | 2026-06-11 | meta-po | 回填 CP3 approved；补强未来高性能 Linux research server 边界，明确 Linux/WSL 不持有 SDK/凭据、不直接连接 Goldminer、不直接下单。 |
| 1.0 | 2026-06-11 | meta-se | 创建 CR045 scoped ADR 草案，覆盖 bridge 拓扑、API allowlist、凭据驻留、kill switch、后续授权和 Story / LLD 策略。 |

## 输入与边界

| 输入 | 结论 |
|---|---|
| `process/checkpoints/CP2-CR045-REQUIREMENTS-BASELINE.md` | 用户已同意 CR045 进入 L2 bridge skeleton / WSL client / fixture-only 工程准备；不授权 L3/L4/L5。 |
| `process/checkpoints/CP3-CR045-HLD-REVIEW.md` | 用户回复“同意”，接受 CP3 六项推荐方案；未来 Linux research server 仅作为研究、回测、组合生成、order intent 和 bridge client，不作为 Goldminer runtime。 |
| `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | 当前 authorization_scope 为 L1/L2；non_authorized_scope 覆盖凭据读取、bridge runtime、登录/连接、账户查询、交易、simulation/live、provider/lake/catalog。 |
| CR043 Spike | `gm` / `gmtrade` 静态候选存在，但真实字段、账号权限和运行语义未验证。 |
| CR044 Delivery | offline admission guard 已 ready-with-risk；真实 runtime 仍不授权。 |
| `engine/broker_adapter.py` | 已有敏感字段、operation counters、blocked reasons 和 CR044 fail-closed 合同。 |

## ADR-CR045-001：接入拓扑选择

| 字段 | 内容 |
|---|---|
| 状态 | accepted-at-cp3 |
| 决策类型 | architecture |
| 问题 | WSL 项目和未来 Linux research server 如何受控接入 Windows 已登录 Goldminer 环境？ |
| 决定 | 采用 Windows-side bridge skeleton + WSL / Linux allowlist client。Windows 侧是未来 SDK/终端上下文和交易执行边界；WSL / Linux 不持有 Goldminer SDK、token 或 account_id，不直接连接 Goldminer，不直接下单。 |
| 推荐理由 | 保持 token/account_id 在 Windows 用户本地，便于 allowlist、kill switch、redaction 和 no-operation evidence；符合当前 L2 授权；未来高性能 Linux 服务器可专注研究、回测、组合生成和 order intent。 |
| 备选方案 A | WSL / Linux direct SDK。优点是路径短；缺点是凭据进入 WSL / Linux，`gmtrade` Python 3.11 不匹配，误调用风险高。 |
| 备选方案 B | WSL / Linux direct Windows terminal endpoint Spike。优点是可能复用终端登录态；缺点是 endpoint 事实不足，仍需 L3/L4 授权。 |
| 影响 / 风险 | 决定网络边界、依赖方向、Story 文件所有权、后续 runbook 和 QA 验证方式。 |
| When to switch | 若官方 endpoint 可验证且用户逐 run 授权 L3/L4，可切换到 endpoint Spike；若用户明确要求 WSL / Linux 持有凭据，必须回退 CP3 并重发安全决策。 |

## ADR-CR045-002：Bridge API allowlist

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | architecture |
| 问题 | L2 bridge API 应暴露哪些动作？ |
| 决定 | L2 只允许 health、capabilities、readonly probe request/response skeleton 三类 allowlist action；所有真实 readonly 查询默认 blocked。 |
| 推荐理由 | 覆盖 CR045 readonly probe preparation，同时不触发 cash/position/order/fill/account state 查询。 |
| 备选方案 A | 提前定义真实 cash/position/order/fill endpoint 但 disabled。优点是后续扩展清晰；缺点是容易被误读为已授权。 |
| 备选方案 B | health-only。优点是最保守；缺点是不能满足 readonly probe skeleton 目标。 |
| 影响 / 风险 | 影响 API schema、Story S02-S04、CP7 验证和 runbook。 |
| When to switch | CP3 认为 readonly skeleton 仍过宽时降级 health-only；L4 逐 run 授权后可新增真实 readonly endpoint Story。 |

## ADR-CR045-003：token/account_id 驻留与脱敏

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | security |
| 问题 | token/account_id 如何处理？ |
| 决定 | 零敏感值入仓。token/account_id 只可在未来用户自主管理的 Windows 本地配置中存在；Agent、WSL、Linux research server、仓库、对话、STATE、fixture、日志和报告均不得读取或记录真实值。 |
| 推荐理由 | 与 CP2 DQ-03 一致，避免敏感材料泄漏。 |
| 备选方案 A | 用户提供不含真实值的结构文档或截图摘要。优点是提高设计确定性；缺点是仍需严格脱敏。 |
| 备选方案 B | WSL / Linux 或仓库存放 `.env`。优点是实施方便；缺点是违反当前不授权边界，禁止采用。 |
| 影响 / 风险 | 决定 redaction、artifact scan、runbook 和 CP7 验证标准。 |
| When to switch | 任何步骤必须处理真实值时，暂停并由 meta-po 发起 L3 security / runtime_authorization gate。 |

## ADR-CR045-004：Kill switch 与 authorization gate

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | runtime_authorization |
| 问题 | 未授权动作如何阻断？ |
| 决定 | 默认 hard-off。没有 per-run authorization、action 不在 allowlist、kill switch disabled、授权层级不足或敏感字段出现时，均返回 blocked，并记录脱敏 reason 与 zero operation counts。 |
| 推荐理由 | 外部 broker 接入必须 fail-closed；当前 L3/L4/L5 均 not-authorized。 |
| 备选方案 A | 仅日志警告但继续执行。优点是调试方便；缺点是可能越权运行，不采用。 |
| 备选方案 B | CP3 一次性批准 L4 readonly。优点是更快获得真实证据；缺点是超出当前 CP2 授权，不采用。 |
| 影响 / 风险 | 影响所有 Story 的失败路径、测试断言和 runbook。 |
| When to switch | 仅当用户逐 run 授权 L3/L4/L5，并且 run manifest、kill switch、redaction 和 QA 计划齐备时，才打开对应 action。 |

## ADR-CR045-005：L3/L4/L5 后续授权策略

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | follow_up_tracking |
| 问题 | 真实 bridge health、readonly probe、submit/cancel 如何推进？ |
| 决定 | 拆为后续逐 run gate：L3 Windows credential local setup / bridge health、L4 readonly probe、L5 submit/cancel/simulation/live 分开授权、分开证据、分开结论。 |
| 推荐理由 | 避免 CP3 架构批准被误读为运行许可，保持每次真实动作可审计。 |
| 备选方案 A | CR045 永久只做 skeleton。优点是风险最低；缺点是后续真实验证需重开完整 CR。 |
| 备选方案 B | 当前 CR 一次性包含 L3/L4/L5。优点是链路短；缺点是权限过大，当前不允许。 |
| 影响 / 风险 | 影响 CP8 关闭结论和 follow-up 台账。 |
| When to switch | 用户明确要求 real-readonly-verified 时，先申请 L3/L4；用户要求 submit/cancel 时，必须另起 L5 高风险决策。 |

## ADR-CR045-006：Story / LLD 策略

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | implementation |
| 问题 | CP3 后如何拆 Story 和设计证据？ |
| 决定 | 建议 6 个 Story：S01-S05 使用 `full-lld`，S06 使用 `technical-note`；若 S06 生成自动 manifest/schema 或 guard 脚本，则升为 `full-lld`。 |
| 推荐理由 | S01-S05 命中 security、permission、external-interface、data-model、rollback、shared-story-boundary；必须完整设计。S06 如果只是 runbook，可轻量承接。 |
| 备选方案 A | 只做 S01-S03。优点是范围小；缺点是 redaction/no-op/runbook 覆盖不足。 |
| 备选方案 B | 加入真实 L4/L5 runtime Story。优点是可验证真实结果；缺点是越过当前授权。 |
| 影响 / 风险 | 决定 CP5 设计证据、CP4 DAG、文件所有权和并行策略。 |
| When to switch | 若 story-planning 发现共享文件冲突或新增平台安装路径，S06 升 full-lld；若用户缩小范围，可延后 S06，但不得加入真实 runtime。 |

## ADR-CR045-007：关闭结论语义

| 字段 | 内容 |
|---|---|
| 状态 | proposed-for-cp3 |
| 决策类型 | risk_acceptance |
| 问题 | CR045 未获 L3/L4 时可以如何关闭？ |
| 决定 | 未获 L3/L4 时，CR045 只能关闭为 `readonly-bridge-skeleton-ready`、`blocked-by-runtime-authorization` 或 `not-recommended`，不得声明 `real-readonly-verified`。 |
| 推荐理由 | 当前没有真实 bridge runtime、Goldminer 登录/连接或账户查询证据。 |
| 备选方案 A | 等 L4 后再关闭。优点是真实证据更强；缺点是阻塞 L2 skeleton 交付。 |
| 备选方案 B | 取消 CR045。优点是零风险；缺点是放弃用户目标。 |
| 影响 / 风险 | 影响 CP8 用户预期、release readiness 和后续 follow-up。 |
| When to switch | 用户明确要求真实只读验证并授权 L3/L4 后，可新增结论候选，但必须有 CP7 证据。 |

## 决策与 HLD 对齐矩阵

| ADR | HLD 章节 | Story 影响 | 验证影响 |
|---|---|---|---|
| ADR-CR045-001 | §4/§5/§8/§9 | S02/S03 | WSL / Linux 不导入 SDK、不持有凭据；未来 Linux research server 只做研究、回测、组合生成、order intent 和 client。 |
| ADR-CR045-002 | §10/§12/§15 | S02/S04 | endpoint allowlist 与 blocked response。 |
| ADR-CR045-003 | §14/§15 | S01/S05/S06 | redaction scan、敏感值 0。 |
| ADR-CR045-004 | §12/§15 | S01/S04/S05 | kill switch default hard-off、operation counts=0。 |
| ADR-CR045-005 | §18/§21/§22 | S06 | runbook 和 follow-up gate。 |
| ADR-CR045-006 | §19/§20 | all stories | CP4/CP5 LLD 策略。 |
| ADR-CR045-007 | §1/§16/§18 | S06/CP8 | 不声明 real-readonly-verified。 |

## 不授权声明

本 ADR 草案不授权以下动作：

| 不授权项 | 状态 |
|---|---|
| 读取 token/account_id/账号/密码/session/cookie/private key | not-authorized |
| 启动 Windows bridge runtime | not-authorized |
| 登录 / 连接 Goldminer | not-authorized |
| 查询资金 / 持仓 / 委托 / 成交 / account state | not-authorized |
| 下单 / 撤单 | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |
| 将 `simulation_ready`、`live_ready` 或 `real_readonly_verified` 置为 true | not-authorized |

## 变更记录

| 日期 | 变更 | 状态 |
|---|---|---|
| 2026-06-11 | 创建 CR045 CP3 ADR 草案 | draft-for-cp3 |
