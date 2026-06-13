---
checkpoint_id: "CP2"
checkpoint_name: "CR045 Requirements / Windows Bridge Authorization Boundary Baseline"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-06-11T21:40:09+08:00"
reviewed_by: "user"
reviewed_at: "2026-06-11T21:49:16+08:00"
auto_check_result: "process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md"
auto_final_authorization: false
target:
  phase: "requirement-clarification"
  change_id: "CR-045"
  artifacts:
    - "process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md"
    - "process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml"
---

# CP2 CR045 Requirements / Windows Bridge Authorization Boundary Baseline 人工审查

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---:|---|
| `process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md` | PASS | 0 | CR045 formal CR、context capsule、授权边界和不授权边界已就绪。 |

## Decision Brief

### Context Capsule Summary

| 字段 | 内容 |
|---|---|
| capsule 路径 | `process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml` |
| capsule 状态 | ready |
| read_profile | compact |
| 默认读取策略 | 先读 capsule；仅在缺失、冲突、字段不足、人工审计或深度评审时读取完整文档。 |
| 全文档读取扩展 | 1 次；CR045 CP2 发起需要读取 CR044 关闭结论、CR043 Spike 结论和当前用户启动指令。 |
| 缺失 / waived 理由 | N/A |

### Decision Collection Coverage

| 来源 | 路径 / 对象 | 扫描状态 | 候选问题数 | 纳入待决策数 | 分类 / N/A 原因 |
|---|---|---:|---:|---:|---|
| STATE pending queue | `process/STATE.md.human_gate_decisions.pending_human_decisions[]` | scanned | 0 | 0 | 启动前无 pending gate；本轮从 CR / capsule / 用户指令聚合。 |
| 正式 CR | `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | scanned | 6 | 6 | 范围、架构、安全、运行授权、风险接受、follow-up tracking 均纳入决策。 |
| Context Capsule | `process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml` | scanned | 6 | 6 | 与 CR 决策一致。 |
| 自动预检结果 | `process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md` | scanned | 0 | 0 | 无阻断项。 |
| 用户显式选择题 | 当前对话 | scanned | 1 | 1 | 用户要求开始 CR045；未授权凭据、查询或交易。 |
| 上游正式产物 | `CR043` / `CR044` | scanned | 3 | 3 | `gm/gmtrade` 静态候选、CR044 offline admission 和不授权边界已纳入。 |

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣分析 | 影响 / 风险 | 回退 / 切换条件 |
|---|---|---|---|---|---|---|---|
| DQ-CP2-CR045-01 | scope | CR045 是否限定为 Windows bridge skeleton 和 readonly probe 准备，而非直接真实连接？ | 接受限定范围：先交付 bridge skeleton、WSL client 合同、fixture/static 测试和 runbook。 | A: 暂停 CR045，等待 L3/L4 授权；B: 直接授权真实 readonly probe。 | 推荐方案能推进工程资产且不触碰凭据；A 最保守但无工程进展；B 可验证真实字段但风险显著提高。 | 决定当前是否能进入 CP3/LLD/实现；防止把“开始实施”误读为真实运行授权。 | 若用户要求真实连接，必须改走 L3/L4 runtime authorization gate。 |
| DQ-CP2-CR045-02 | architecture | WSL 如何连接 Windows 已登录的掘金量化环境？ | 采用 Windows-side broker bridge 为主路线；WSL 只调用 bridge allowlist API。 | A: WSL 直接安装 SDK 并持有 token；B: WSL 直连 Windows 终端本地 endpoint。 | 推荐方案隔离凭据并方便 kill switch；A 实现更短但 token 进入 WSL；B 依赖未验证的终端本地协议。 | 影响平台边界、凭据驻留、网络拓扑和后续 Story 设计。 | 若官方确认本地终端 endpoint 且用户接受风险，可在 CP3 切换。 |
| DQ-CP2-CR045-03 | security | token/account_id 和 Windows 本地配置如何处理？ | 零敏感值入仓：token/account_id 只留在用户 Windows 本地 `.env.local` 或终端设置；Agent 不读取、不接收、不记录。 | A: 用户提供脱敏字段结构文档；B: 后续 L3 授权时由用户手工运行。 | 推荐方案安全边界最清楚；A 提高设计确定性；B 延后工程验证。 | 防止 token/account_id 进入对话、Markdown、STATE、测试或日志。 | 如果任何步骤需要真实敏感值，暂停并重提安全决策。 |
| DQ-CP2-CR045-04 | runtime_authorization | 当前是否仍不授权 L3/L4/L5？ | 确认不授权：不启动 bridge runtime，不登录/连接 Goldminer，不查询账户，不下单/撤单，不 simulation/live。 | A: 授权 L3 Windows 本地 bridge 启动健康检查；B: 授权 L4 readonly probe。 | 推荐方案权限最小；A/B 都需要逐 run manifest、操作者、时间窗和脱敏证据。 | 防止 CP2 approval 被误读为运行授权。 | 用户单独批准 L3/L4 后，创建或推进对应 run gate。 |
| DQ-CP2-CR045-05 | risk_acceptance | 是否接受 CR045 当前可能只能关闭为 skeleton-ready，而不是 real-readonly-verified？ | 接受。未获 L4 前，CP8 只能关闭为 `readonly-bridge-skeleton-ready` 或 `blocked-by-runtime-authorization`。 | A: 等 L4 后再启动 CR045；B: 取消 CR045。 | 推荐方案先完成安全工程准备；A 结果更真实但阻塞；B 风险最低但放弃 bridge 路线。 | 影响用户对交付结果的预期。 | 若用户要求 real-readonly-verified，必须先授权 L4 probe。 |
| DQ-CP2-CR045-06 | follow_up_tracking | 后续真实 readonly / submit-cancel 如何跟踪？ | 拆为后续逐 run 授权：L3 bridge health、L4 readonly probe、L5 submit/cancel 分开。 | A: CR045 永远只做 skeleton，不保留后续授权入口；B: 直接把 L4/L5 纳入当前 CP2。 | 推荐方案可控演进；A 限制未来验证；B 权限过大。 | 影响后续 CR / run gate 管理和审计成本。 | 授权粒度无法明确时，所有真实 runtime fail-closed。 |

### 用户视角复述与不授权项

如果你回复 `approve`，表示你接受以上 6 项推荐方案：CR045 进入 standard 工作流，当前只授权 Windows bridge skeleton / WSL client / fixture-only 工程实现，不授权任何真实 Goldminer runtime。

如果你回复 `approve`，不表示授权以下 13 项禁止操作：

| 不授权项 | 当前状态 |
|---|---|
| 读取 `.env`、token、account_id、账号、密码、session、cookie、private key | not-authorized |
| 让 Agent 接收或记录 token/account_id 原文 | not-authorized |
| 启动 Windows bridge runtime | not-authorized |
| 登录掘金 | not-authorized |
| 连接 Goldminer / broker / 终端 | not-authorized |
| 查询资金 / cash | not-authorized |
| 查询持仓 / position | not-authorized |
| 查询委托 / order | not-authorized |
| 查询成交 / fill / execution report | not-authorized |
| 下单 / submit order | not-authorized |
| 撤单 / cancel order | not-authorized |
| 启动 simulation/live | not-authorized |
| provider fetch / lake write / catalog publish | not-authorized |

自动终验授权：false。CP2 approved 不构成 CP3、CP5、CP6、CP7、CP8 自动通过，也不构成任何运行授权。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| 自动预检 PASS | PASS | `process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md` | 用户回复“同意”，按 `approve` 处理。 |
| 待人工决策项已收集 | PASS | 本文件 Decision Brief | 用户接受 6 项推荐方案。 |
| 不授权边界已用户可见 | PASS | 本文件“不授权项” | 用户回复“同意”不授权任何 L3+ runtime。 |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR045 限定为 bridge skeleton / readonly probe 准备 | 通过 | DQ-CP2-CR045-01 | 用户回复“同意”。 |
| 2 | 是否接受 Windows bridge 作为主路线 | 通过 | DQ-CP2-CR045-02 | 用户回复“同意”。 |
| 3 | 是否接受零敏感值入仓和 Windows 本地凭据驻留 | 通过 | DQ-CP2-CR045-03 | 用户回复“同意”。 |
| 4 | 是否确认当前不授权 L3/L4/L5 runtime | 通过 | DQ-CP2-CR045-04 | 用户回复“同意”。 |
| 5 | 是否接受 skeleton-ready 作为可能关闭结论 | 通过 | DQ-CP2-CR045-05 | 用户回复“同意”。 |
| 6 | 是否接受后续真实 run 拆分授权 | 通过 | DQ-CP2-CR045-06 | 用户回复“同意”。 |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| 用户明确 approve / 修改 / reject | PASS | 当前对话，2026-06-11T21:49:16+08:00 用户回复“同意” | 按 approve 处理，可进入 CP3。 |
| 无阻断项 | PASS | CP2 自动预检 | 阻断项 0。 |
| 不授权边界明确 | PASS | 本文件“不授权项” | CP2 不授权真实 runtime。 |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR045 正式 CR | `process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md` | 通过 | 用户回复“同意”。 |
| CP2 Context Capsule | `process/context/CP2-CR045-REQUIREMENT-CONTEXT.yaml` | 通过 | ready。 |
| CP2 自动预检 | `process/checks/CP2-CR045-REQUIREMENTS-BASELINE.md` | PASS | 阻断项 0。 |
| CP2 人工审查稿 | `process/checkpoints/CP2-CR045-REQUIREMENTS-BASELINE.md` | 通过 | 用户回复“同意”。 |

## 人工审查结果

- 结论：`approved`
- reviewed_by: user
- reviewed_at: 2026-06-11T21:49:16+08:00
- 备注：用户回复“同意”，按 `approve` 处理；接受 DQ-CP2-CR045-01..06 推荐方案。该确认只授权 CR045 进入 Windows bridge skeleton / WSL client / fixture-only 工程准备，不授权读取 token/account_id、不授权启动 Windows bridge runtime、不授权登录 / 连接 Goldminer、不授权账户查询、不授权下单 / 撤单或 simulation/live。
