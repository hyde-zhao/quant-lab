---
story_id: "CR045-S06"
title: "User Runbook and Follow-up Gates"
story_slug: "user-runbook-and-follow-up-gates"
status: "ready-for-verification"
priority: "P1"
wave: "W4"
implementation_allowed: true
implementation_allowed_until: "CP5 approved at 2026-06-11T23:16:11+08:00; L2 docs / skeleton guidance only"
depends_on:
  - "CR045-S01"
  - "CR045-S02"
  - "CR045-S03"
  - "CR045-S04"
  - "CR045-S05"
dependency_contracts:
  - upstream_story: "CR045-S01"
    type: "contract"
    required_for: "security and authorization boundary"
  - upstream_story: "CR045-S02"
    type: "contract"
    required_for: "health/capabilities wording"
  - upstream_story: "CR045-S03"
    type: "contract"
    required_for: "WSL/Linux client boundary"
  - upstream_story: "CR045-S04"
    type: "contract"
    required_for: "readonly probe blocked-first wording"
  - upstream_story: "CR045-S05"
    type: "contract"
    required_for: "redaction and no-operation evidence wording"
feature_design_refs:
  - "docs/features/cr045-goldminer-bridge/DESIGN.md#人机协作与确认点"
  - "docs/features/cr045-goldminer-bridge/TEST-PLAN.md#手工验收"
  - "docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s06"
lld_policy:
  required_level: "technical-note"
  trigger_reasons:
    - "docs-handoff"
    - "runtime_authorization"
    - "follow_up_tracking"
  rationale: "当前只需要用户 runbook、后续 L3/L4/L5 gate 说明和 CP8 wording，不新增可执行 manifest/schema/guard。"
  waiver_reason: ""
  revisit_condition: "若 S06 引入自动 manifest、schema、guard script、状态机或安装路径，升级为 full-lld。"
  evidence_path: "process/stories/CR045-S06-user-runbook-and-follow-up-gates.md#技术说明"
file_ownership:
  primary:
    - "process/stories/CR045-S06-user-runbook-and-follow-up-gates.md"
    - "docs/goldminer/CR045-BRIDGE-RUNBOOK.md"
  shared:
    - "docs/features/cr045-goldminer-bridge/DESIGN.md"
  merge_owner: "CR045-S06"
  forbidden:
    - ".env"
    - ".env.*"
    - "engine/goldminer_bridge_contract.py"
    - "engine/goldminer_bridge_client.py"
    - "engine/goldminer_bridge_probe.py"
lld_gate:
  required_inputs:
    - "CR045-S01 design evidence"
    - "CR045-S02 design evidence"
    - "CR045-S03 design evidence"
    - "CR045-S04 design evidence"
    - "CR045-S05 design evidence"
  design_evidence_type: "technical-note"
  design_evidence_path: "process/stories/CR045-S06-user-runbook-and-follow-up-gates.md#技术说明"
  status: "confirmed"
dev_gate:
  implementation_allowed: true
  allowed_after: "CP5 approved"
  design_evidence_confirmed: true
  lld_confirmed: true
  dependencies_satisfied: true
  file_conflict_free: true
  real_runtime_authorized: false
---

# CR045-S06 User Runbook and Follow-up Gates

## 目标

把 S01-S05 的安全边界、bridge/client 合同、readonly blocked-first、redaction/no-operation 证据收敛为用户可审查的 runbook 和后续 L3/L4/L5 gate 说明。当前默认 `technical-note`，不写完整 LLD。

## 开发上下文（dev_context）

- 输入文件：S01-S05 设计证据、`docs/features/cr045-goldminer-bridge/DESIGN.md`、`process/DEVELOPMENT-PLAN-CR045.yaml`、CP3 checkpoint。
- 输出文件：本 Story 卡片的 CP5 技术说明；未来 CP6 可创建 `docs/goldminer/CR045-BRIDGE-RUNBOOK.md`。若升级 full-lld，则输出 `process/stories/CR045-S06-user-runbook-and-follow-up-gates-LLD.md`。
- 接口约定：runbook 只列出人工 gate、禁止操作、skeleton-ready/blocked-by-runtime-authorization 关闭语义和 CP7/CP8 关注点。
- 设计约束：不得把 runbook 写成运行授权；不得提供真实 runtime 命令；不得要求用户在对话或仓库提供 token/account_id。
- 平台目标：docs/review-only；如新增脚本/schema/manifest，则升 full-lld。

### 依赖与并行门控

| 上游 Story | 类型 | LLD 门控 | 开发门控 | 说明 |
|---|---|---|---|---|
| CR045-S01-S05 | contract | 上游设计证据齐全后补 technical-note | CP5 approved + 上游合同确认 | S06 是收敛 Story，不抢占实现文件。 |

### 文件所有权

| 类型 | 文件 | Owner / 合并规则 |
|---|---|---|
| primary | `process/stories/CR045-S06-user-runbook-and-follow-up-gates.md` | CR045-S06 |
| primary | `docs/goldminer/CR045-BRIDGE-RUNBOOK.md` | CR045-S06 future primary owner。 |
| forbidden | bridge implementation files、`.env`、`.env.*` | S06 不写代码，不读取凭据。 |

### AI 可执行任务清单

| TASK-ID | 动作 | 目标文件 | 描述 |
|---|---|---|---|
| CR045-S06-T1 | 补充 | 本文件 `## 技术说明` | CP5 前补齐 technical-note，覆盖 runbook 和 follow-up gates。 |
| CR045-S06-T2 | 补充 | 本文件 `## 技术说明` | 列出 CP5/CP8 approve 不授权的 L3/L4/L5 事项。 |
| CR045-S06-T3 | 判定 | 本文件或 LLD | 若新增自动 manifest/schema/guard script，升级 full-lld。 |

## 技术说明

| 项目 | 内容 |
|---|---|
| 设计证据类型 | `technical-note`。本次不升级 full-lld，因为 S06 只设计人工 runbook、follow-up gate 和 CP8 wording，不新增可执行 manifest、schema、guard script、状态机、安装路径或自动化校验脚本。 |
| 设计依据 | CP2/CP3 已批准 CR045 仅进入 L1/L2：Windows bridge skeleton、WSL/Linux allowlist client、fixture/static validation、runbook；S01-S05 LLD 已分别冻结安全边界、health/capabilities schema、client contract、readonly blocked-first、redaction/no-operation static validation。 |
| 文件影响 | CP5 阶段只修改本 Story 卡片 `## 技术说明` 并生成 `process/checks/CP5-CR045-S06-user-runbook-and-follow-up-gates-TECHNICAL-NOTE-IMPLEMENTABILITY.md`。未来 CP6 可创建 `docs/goldminer/CR045-BRIDGE-RUNBOOK.md`，但 S06 不修改 `engine/goldminer_bridge_contract.py`、`engine/goldminer_bridge_client.py`、`engine/goldminer_bridge_probe.py` 或测试实现文件。 |
| 接口变化 | 无代码接口变化。runbook 只描述人工 gate 和文档化合同：L3 Windows credential local setup、L4 readonly probe、L5 submit/cancel/simulation/live 必须由 meta-po 另行发起人工 gate 或新 CR；CP5/CP8 approve 不构成运行授权。 |
| 数据变化 | 无持久化数据变化，不创建 run manifest、schema 或状态机。runbook 只允许出现脱敏占位、字段类别、reason code 和 follow-up gate 描述；不得要求用户在对话、仓库、日志或 fixture 中提供 token/account_id/账号/密码/session/cookie/private key。 |
| 权限变化 | 权限保持 L1/L2 only。继续不授权 credential_read、token/account_id collection、Windows bridge runtime start、Goldminer login/connect、account/cash/position/order/fill query、order_submit、order_cancel、simulation_runtime、live_runtime、provider_fetch、lake_write、catalog_publish，以及任何将 `real_readonly_verified`、`simulation_ready` 或 `live_ready` 置为 true 的声明。 |
| 异常和回退 | 用户要求“现在连接 / 查一下 / 读账户 / 下单 / 撤单 / 跑 simulation/live / 读取配置或凭据”时，runbook 必须指示停止当前 CR045 L2 流程，交回 meta-po 发起 L3/L4/L5 runtime_authorization 或新 CR。若 CP5 认为 runbook 文案会被误读为授权，退回 S06 technical-note 修改；若需要自动 gate artifact，则升级为 full-lld。 |
| 测试入口 | CP5 technical-note review；CP7 manual/static review 检查 runbook 不含真实 runtime 命令、凭据采集步骤、真实账户查询步骤或授权性 ready/verified 声明；CP8 release wording review 检查关闭结论只能是 `readonly-bridge-skeleton-ready`、`blocked-by-runtime-authorization` 或 `not-recommended`，除非后续 L3/L4/L5 已单独授权并验证。 |
| 已知风险 | 主要风险是用户或后续执行者把 CP5/CP8 approve 误读为 runtime authorization；缓解方式是在 runbook、CP7、CP8 中重复列出不授权项和后续 gate。另一个风险是 runbook 为了可操作性加入真实命令或配置步骤；当前 technical-note 明确禁止，若要加入自动/真实步骤必须重新进入 CP5。 |
| 偏离记录 | 无偏离。S06 保持 `technical-note`，未生成 `process/stories/CR045-S06-user-runbook-and-follow-up-gates-LLD.md`，因为未引入自动 manifest/schema/guard script。 |

### S06 runbook 设计要点

| 章节 / 主题 | 必须包含 | 禁止包含 |
|---|---|---|
| 当前交付范围 | L2 skeleton、fixture/static validation、no-operation evidence、follow-up gate 描述。 | 真实 bridge runtime 启动步骤。 |
| 后续授权 | L3/L4/L5 分层说明、需要 meta-po 单独人工 gate、逐 run 授权和证据要求。 | “CP5/CP8 approve 即可运行”的暗示。 |
| 凭据边界 | token/account_id 只可由未来用户在 Windows 本地自主管理，Agent/WSL/Linux/仓库/对话不读取不记录。 | 让用户粘贴、保存或提交 token/account_id/账号/密码/session/cookie/private key。 |
| 只读 probe | 当前只说明 skeleton 和 blocked-first；`real_readonly_verified=false`。 | 资金、持仓、委托、成交、account state 的真实查询命令。 |
| 关闭语义 | 未获 L3/L4 时只能关闭为 `readonly-bridge-skeleton-ready`、`blocked-by-runtime-authorization` 或 `not-recommended`。 | `real-readonly-verified`、`simulation_ready=true`、`live_ready=true`。 |

### 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| N/A | S06 是否需要升级 full-lld。 | 推荐：保持 technical-note，因为本次只做文档 / runbook 设计；备选：若引入自动 manifest、schema、guard script、状态机或安装路径，则升级 full-lld。 | 本次未引入自动 artifact，保持 technical-note；无 `blocks_lld=true` 新项。 | 文档 / 权限 / CP8 / 后续 CR | `docs/design/FEATURE-DESIGN-MATRIX-CR045.md`；`docs/features/cr045-goldminer-bridge/TASKS.md#cr045-s06` | 任一自动 artifact 或真实 runtime 步骤纳入 S06 时，重开 CP5 并升级 full-lld。 |

## 验证上下文（validation_context）

| 项目 | 内容 |
|---|---|
| validation_mode | review-only + static-only |
| 验证入口 | CP5 technical-note review；CP8 manual review。 |
| 关键验证场景 | approve/CP5/CP8 不授权 L3+；不宣称 `real-readonly-verified`；runbook 不要求凭据。 |
| 禁止验证方式 | 不提供真实 runtime 命令，不读取凭据，不连接 Goldminer。 |

## 量化验收标准（acceptance_criteria）

- [ ] technical-note 必须列出至少 16 项 CR045 not-authorized actions。
- [ ] 明确 CP5/CP8 approve 不授权 credential_read、runtime start、Goldminer login/connect、query、submit/cancel、simulation/live、provider/lake/publish。
- [ ] 明确未获 L3/L4 时只能关闭为 `readonly-bridge-skeleton-ready`、`blocked-by-runtime-authorization` 或 `not-recommended`。
- [ ] 不得声明 `real-readonly-verified`、`simulation_ready=true` 或 `live_ready=true`。
- [ ] 若新增 executable manifest、schema、guard script 或状态机，`lld_policy.required_level` 必须升级为 `full-lld`。
- [ ] S06 不修改 bridge implementation files，不抢占 S02-S05 文件 ownership。

## 阻塞说明

无 CP4 阻塞。自动化 run manifest/schema/guard 若纳入范围，则需 CP5 前升级 full-lld。
