---
status: approved
version: "0.1"
complexity: "standard-runtime-gate"
selected_option: "A. Two-plane authorization design with fail-closed execution boundary"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-06-20T22:01:10+08:00"
source_cr: "CR-102"
parent_cr: "CR-101"
---

# CR102 NAS Real Package Exchange Authorization HLD

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-06-20 | host-orchestrator | 初版，定义真实 NAS package exchange 的授权架构、禁止边界、后续 CP5 输入和 CP3 待决策项。 |
| v0.2 | 2026-06-21 | host-orchestrator | 回填 CP3 approved 状态，作为 CP5 design-only 门禁输入；真实 NAS 执行仍不授权。 |

## 1. 问题定义

CR100 已完成本地 fake package exchange offline readiness，CR101 已完成 cross-platform strategy delivery 与 adapter layer 的离线交付闭环。当前缺口是：真实策略包经 NAS exchange 在 research_pc 与 trading_pc 之间流转的路径、挂载、权限、操作范围和证据格式尚未被用户明确授权。

CR102 的 CP3 目标不是执行真实 NAS 验证，而是冻结后续真实 NAS 授权门禁的架构边界，让后续 CP5 / CP7 只能在显式授权的路径和操作范围内推进。

### 目标

| 优先级 | 目标 | 度量方式 |
|---|---|---|
| P0 | 明确真实 NAS gate 的架构分层 | HLD 至少区分 authorization ledger、execution plan、evidence schema 三层 |
| P0 | 保持 fail-closed 执行边界 | NAS access/list/read/write/copy/publish/pull/delete/mount/check 默认全部为 false |
| P0 | 防止 CP3 approve 被误读为运行授权 | CP3 Decision Brief 至少 1 项 runtime_authorization DQ 明确不授权 |
| P1 | 为 CP5 提供设计输入 | CP5 输出对象、Story 切片、验证方式和阻断条件均可计算 |
| P1 | 保留 CR089 / CR100 / CR101 追溯关系 | HLD、context capsule 和 CP3 checkpoint 均引用上游关系 |

### 成功标准

- CP3 HLD 至少包含 4 个 Architecture Gray Areas、3 个候选方案、3 个关键场景模拟和 5 个待人工决策项。
- 授权矩阵中 10 类 NAS 动作为 false：access、list、read、write、copy、publish、pull、delete、mount、check。
- 凭据/env/account、QMT/MiniQMT/XtQuant/gateway runtime、submit/cancel/simulation/live、provider/lake/catalog publish 的授权计数全部为 0。
- path/export/root/mount/identity 均保持 `UNSET_BY_USER`，且不得由 agent 推断、探测或从环境读取。
- CP5 之前真实 NAS 执行动作为 0。

### 约束

| 类型 | 约束内容 |
|---|---|
| 权限 | 当前不授权任何 NAS、凭据、账户、runtime、交易或 publish 动作 |
| 安全 | 不读取 `.env`、secret、token、账户、持仓、委托、成交、原始日志 |
| 平台 | 不启动 QMT / MiniQMT / XtQuant / gateway runtime |
| 证据 | 后续只能使用脱敏摘要、hash、计数、状态和 pass/fail，不落真实凭据或账户原文 |
| 追溯 | CR102 是 RA-CR101-003 的正式 gate；不恢复 CR089，不重开 CR100/CR101 |

### 非目标

- 不访问、列取、读取、复制、写入、发布、拉取、删除或挂载真实 NAS。
- 不发现、猜测或验证真实 NAS path / export / root / mount point。
- 不读取凭据、env、账户、资金、持仓、委托、成交或原始日志。
- 不启动或连接 QMT / MiniQMT / XtQuant / gateway runtime。
- 不执行交易、simulation/live、provider fetch、lake write 或 catalog publish。
- 不把 CR100 fake exchange、CR101 READY_WITH_RISK 或 CR089 blocked-readiness 解释为真实 NAS ready。

## 2. Architecture Gray Areas

| 灰区 ID | 关键问题 | 为什么影响架构 | 影响面 | canonical refs | 状态 |
|---|---|---|---|---|---|
| AGA-CR102-01 | NAS gate 是一次性执行门，还是分层授权门？ | 直接执行会把 CP3 设计批准误读为运行授权；分层授权可保留人工决策点 | 范围 / 安全 / 验证 / 回退 | CP2 DQ-CP2-CR102-03/04 | selected |
| AGA-CR102-02 | path/mount/permission 由谁提供？ | 若 agent 自动发现，会触碰 NAS 或凭据边界；必须由用户显式提供 | 安全 / 权限 / 操作计划 | CR102 authorization_policy | selected |
| AGA-CR102-03 | 后续 CP5 是否允许实现真实检查脚本？ | 真实脚本可能执行 list/check/mount；CP5 只能先设计授权矩阵与 dry-run 计划 | 实现 / 测试 / 运行时 | CP2 approved no-execution | selected |
| AGA-CR102-04 | 如何处理 CR089 overlap？ | CR089 同时涉及 NAS exchange 与 QMT/runtime；合并会扩大风险 | CR tracking / runtime / 风险接受 | CR089 blocked, CR101 follow-up | selected |

### Advisor Table

| Option | Pros | Cons | Impact Surface | Recommendation | Assumptions / When to switch |
|---|---|---|---|---|---|
| A. Two-plane authorization design | 将 authorization ledger 与 future execution plan 分离；CP3 不触碰 NAS；后续可逐项授权 | 需要多一个 CP5/CP7 门禁，真实验证延后 | CR102 HLD、CP5 设计、evidence schema、安全边界 | 推荐 | 当前没有 path/mount/permission；用户要求最小权限时采用 |
| B. Single-pass real NAS check | 用户提供路径后直接设计并执行 check | 路径、挂载、权限、证据和回退未冻结前风险高；容易越过 CP5 | NAS、权限、证据、外部副作用 | 不推荐 | 只有用户在后续明确提供 path/mount/permission 且逐项授权 check 时重新评估 |
| C. Merge back into CR089 | 统一处理 NAS + QMT runtime | 会恢复更大 runtime 语义，扩大到 QMT / account / gateway 风险 | CR089、QMT runtime、NAS package exchange | 不推荐 | 仅当用户明确要求恢复 CR089 并接受 runtime gate |
| D. Cancel real NAS gate | 关闭 RA-CR101-003 | 权限最小，避免外部风险 | 真实交付链缺口保留 | 条件备选 | 若用户不再需要真实 NAS package exchange 验证时采用 |

## 3. 候选架构方案

| 方案 | 描述 | 优点 | 代价 / 风险 | 结论 |
|---|---|---|---|---|
| A. Two-plane authorization design | CP3 只冻结授权架构；CP5 设计 authorization matrix、future execution plan、evidence schema；真实动作必须后续单独批准 | 权限边界清晰，可审计，能与 CR089 解耦 | 真实验证不会在 CP3 发生 | 推荐 |
| B. Check-only direct design | CP3 后直接进入只读 check 设计 | 进度快 | 当前 `check=false` 且 path/mount 未提供，仍不可执行 | 不推荐 |
| C. CR089 combined route | 将 CR102 并回 CR089 处理 | 一个 CR 处理完整运行链 | 扩大到 QMT / runtime / account 风险 | 不推荐 |

推荐方案：A。

## 4. 推荐架构

```text
CP2 Approved Scope Boundary
  - no execution authorization
  - NAS path/export/root/mount/identity = UNSET_BY_USER
        |
        v
CP3 Authorization Architecture
  authorization ledger
    - operation matrix: all false by default
    - actor / host / identity placeholders
    - forbidden action list
  future execution plan shell
    - requires user supplied path/mount/permission
    - requires operation-specific approval
    - no command, no mount, no list, no check in CP3
  evidence schema
    - redacted status/hash/count/pass-fail only
        |
        v
CP5 Design Readiness, if approved
  - produce runbook / dry-run plan / guardrail checklist
  - still no NAS action unless user grants a later runtime authorization
```

## 5. 模块职责

| 模块 / 对象 | 职责 | 禁止职责 |
|---|---|---|
| CR102 authorization ledger | 保存 path/mount/permission 的状态、操作授权矩阵和不授权项 | 不保存真实凭据；不推断 path；不执行命令 |
| Future execution plan shell | 描述后续若授权时需要的步骤、前置条件、回退和证据格式 | 不包含可直接执行的 mount / copy / delete / publish 命令 |
| Evidence schema | 限定脱敏摘要、hash、计数、状态、pass/fail | 不保存账户、持仓、委托、成交、原始日志、secret |
| CP5 design package | 后续可生成 LLD / TASKS / TEST-PLAN | 不把 CP5 设计批准解释为真实执行批准 |
| CR tracking | 维护 CR102 active、CR089 overlap、RA-CR101-003 来源 | 不自动恢复 CR089、CR020 或 order-write |

## 6. 集成契约

| 调用方向 | 调用时机 | 输入契约 | 输出契约 | 降级策略 | 调用方需同步修改 |
|---|---|---|---|---|---|
| CP3 checkpoint -> user decision | CP3 人工评审 | HLD、precheck、context capsule、DQ-CP3-CR102-01..05 | approve / 修改 / reject | 修改 path 或操作授权时重出 CP3 或回 CP2 | `STATE.md.human_gate_decisions` |
| CP3 HLD -> CP5 design | CP3 approved 后 | accepted architecture DQ、不授权项、blocked-for-execution 条件 | CP5 LLD / TEST-PLAN / TASKS 输入 | CP3 rejected 时保持 CR102 active blocked 或 cancelled | CR102 formal CR、CR-INDEX |
| CP5 design -> future runtime gate | 仅当后续用户明确授权 | user supplied path/mount/permission、operation allowlist、evidence schema | runbook / preflight checklist / rollback plan | 任一授权缺失则 fail closed | follow-up runtime authorization checkpoint |
| evidence schema -> CP7/CP8 | 后续验证或终验 | 脱敏状态、hash、计数、pass/fail | PASS_WITH_RISK 或 BLOCKED 证据 | 发现敏感字段则 blocked_redaction_failed | quality / release docs |

## 7. 非功能与可量化成功标准

| ID | 标准 | 可验证阈值 |
|---|---|---|
| SC-CR102-01 | NAS 操作默认拒绝 | 10 类 NAS 操作授权均为 false |
| SC-CR102-02 | path/mount/permission 不被推断 | `UNSET_BY_USER` 字段数量至少 5 个，且无真实路径值 |
| SC-CR102-03 | 不触碰凭据和账户 | credential/env/account read flags 全部 false |
| SC-CR102-04 | 不触发 runtime | QMT/MiniQMT/XtQuant/gateway flags 全部 false |
| SC-CR102-05 | CP5 输入可计算 | 至少 3 个 CP5 输出对象：authorization matrix、execution plan shell、evidence schema |
| SC-CR102-06 | CR089 overlap 有防误读 | Decision Brief 至少 1 项 risk_acceptance DQ 覆盖 CR089 |

## 8. Use Case -> Architecture Traceability

| Use Case / 场景 | 架构对象 | 异常路径 | 验证方式 |
|---|---|---|---|
| UC-CR102-01 用户只批准设计门禁 | authorization ledger | 无 path/mount/permission 时 execution blocked | CP3 precheck + human gate |
| UC-CR102-02 后续用户提供只读 check 授权 | future execution plan shell | path 缺失、check 未授权、mount 未授权均 blocked | CP5 设计后重开授权 gate |
| UC-CR102-03 用户要求 publish/pull/copy | operation matrix | write/publish/delete 未单独授权则 blocked | Decision Brief 暴露 high-risk DQ |
| UC-CR102-04 涉及 QMT runtime 或账户 | CR102 boundary router | 切换到独立 runtime_authorization CR | CR tracking / state-router |

## 9. 关键场景模拟

| 模拟 ID | 场景 | 输入 / 前置条件 | 推荐架构执行路径 | 预期输出 | 失败 / 回退路径 | 结果 |
|---|---|---|---|---|---|---|
| SIM-CR102-01 | CP3 approve | 用户只回复 approve | HLD -> CP3 checkpoint -> accepted DQ | 进入 CP5 design pending；NAS ops 仍 false | 若用户要求执行，回 CP2/CP3 修改授权 | PASS |
| SIM-CR102-02 | 用户提供 path 但不授权 check | path 有值，check=false | authorization ledger detects missing operation approval | blocked-for-execution | 用户必须明确授权 check/list/read 等具体动作 | PASS as blocked |
| SIM-CR102-03 | 用户要求 publish | publish=true 请求 | high-risk operation route | 要求 path、identity、rollback、evidence、delete policy；未满足则 blocked | 拆为 publish-specific runtime gate | PASS as blocked |
| SIM-CR102-04 | CR089 被误恢复 | 试图把 CR102 解释为 CR089 runtime ready | boundary router | blocked; CR089 remains blocked | 需用户另起 CR089/runtime gate | PASS as blocked |

## 10. 风险矩阵

| 风险 ID | 风险 | 等级 | 缓解 | 回退 / 切换条件 |
|---|---|---|---|---|
| R-CR102-01 | CP3 approve 被误读为真实 NAS 授权 | HIGH | DQ-CP3-CR102-04 明确不授权，所有操作默认 false | 发现误读时回 CP3 修订并暂停 CP5 |
| R-CR102-02 | path/mount/permission 被 agent 推断 | HIGH | path/export/root/mount/identity 固定 `UNSET_BY_USER`，只能用户提供 | 用户提供具体值后重出授权矩阵 |
| R-CR102-03 | publish/delete 造成真实 NAS 副作用 | HIGH | publish/delete 默认 false，必须独立 high-risk DQ | 用户要求时拆出 publish/delete gate |
| R-CR102-04 | CR089 overlap 扩大到 QMT runtime | HIGH | CR102 只处理 NAS exchange authorization architecture | 任何 runtime/account 需求切到 runtime_authorization CR |
| R-CR102-05 | 证据泄露敏感信息 | HIGH | evidence schema 只允许脱敏摘要、hash、计数、状态 | 发现敏感字段则 blocked_redaction_failed |

## 11. ADR 候选

| ADR | 决策 | 状态 |
|---|---|---|
| ADR-CR102-01 | CR102 采用 authorization ledger 与 future execution plan 分离的 two-plane 架构。 | proposed |
| ADR-CR102-02 | path/export/root/mount/identity 只能由用户显式提供，不由 agent 探测或推断。 | proposed |
| ADR-CR102-03 | CP3/CP5 设计批准均不授权任何真实 NAS 操作；真实动作必须后续 runtime authorization gate。 | proposed |
| ADR-CR102-04 | CR102 不恢复 CR089、CR020、QMT/MiniQMT/XtQuant/gateway runtime 或 order-write。 | proposed |

## 12. HLD 拆分判定

| 判定项 | 结论 | 说明 |
|---|---|---|
| 核心产物数量 | 1 | 核心产物是 NAS real package exchange authorization gate |
| Story 预计数量 | 3 | authorization matrix、execution plan shell、evidence schema 可在同一 HLD 管理 |
| ADR 聚类 | 单一聚类 | 均围绕 NAS gate 授权边界 |
| 风险集中度 | high | 高风险来自同一授权边界，拆分会增加追溯成本 |
| 结论 | 不拆分 HLD | 若后续出现 publish/delete 真实执行需求，再拆 runtime-specific CR |

## 13. 非目标与不授权范围

- 不访问、列取、读取、复制、写入、发布、拉取、删除或挂载真实 NAS。
- 不读取 Windows/Linux `.env`、NAS 凭据、token、secret、账号、账户、资金、持仓、委托、成交或原始日志。
- 不启动、连接、安装或运行 QMT / MiniQMT / XtQuant / gateway runtime。
- 不执行 submit/cancel、buy/sell、simulation/live。
- 不执行 provider fetch、lake write、catalog publish。
- 不恢复 CR089 或 CR020，不自动启动 QMT direct-run、MiniQMT gateway 或 order-write gate。

## 14. CP3 待决策项草案

| 决策 ID | 决策类型 | 问题 | 推荐 |
|---|---|---|---|
| DQ-CP3-CR102-01 | architecture | 是否批准 two-plane authorization design？ | 批准 authorization ledger + future execution plan 分离架构。 |
| DQ-CP3-CR102-02 | security | path/mount/permission 是否继续只能由用户显式提供？ | 是，保持 `UNSET_BY_USER`，不得探测或推断。 |
| DQ-CP3-CR102-03 | implementation | CP5 是否只产出设计包而不执行 NAS？ | 是，CP5 只产出 authorization matrix、execution plan shell、evidence schema。 |
| DQ-CP3-CR102-04 | runtime_authorization | CP3 approve 是否授权 NAS 或 runtime 动作？ | 不授权；所有真实动作仍 false。 |
| DQ-CP3-CR102-05 | risk_acceptance | 是否接受 CR089 overlap 与 blocked-for-execution 状态？ | 接受，并保留 CR102 独立 gate，不恢复 CR089。 |

## 15. 自审记录

| 检查项 | 结论 | 说明 |
|---|---|---|
| 候选方案数量 >= 2 | PASS | 已列 3 个方案和 4 个 advisor options。 |
| advisor table-first | PASS | 使用固定表头。 |
| 集成契约显式化 | PASS | 覆盖调用方向、时机、输入、输出、降级和同步范围。 |
| NFR 量化 | PASS | 成功标准和 SC 均含计数或明确 false 状态。 |
| 场景模拟 2-3 个 | PASS | 已列 4 个关键场景。 |
| 不授权边界 | PASS | 已独立列出，并与 CP2 approved boundary 一致。 |
