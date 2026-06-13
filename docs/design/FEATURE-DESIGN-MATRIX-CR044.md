---
status: draft-for-cp4
version: "1.0"
cr_id: "CR-044"
feature_id: "FEAT-CR044-GOLDMINER-SIMULATION-ADMISSION"
source_cr: "process/changes/CR-044-GOLDMINER-SIMULATION-ADMISSION-2026-06-11.md"
source_cp2: "process/checkpoints/CP2-CR044-REQUIREMENTS-BASELINE.md"
source_cp3: "process/checkpoints/CP3-CR044-HLD-REVIEW.md"
source_context: "process/context/CP3-CR044-DESIGN-CONTEXT.yaml"
confirmed_by: ""
confirmed_at: ""
---

# CR044 Feature Design Matrix

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-11 | meta-se | 创建 CR044 scoped Feature 设计适用性矩阵、Story LLD 分级和 CP5 批次范围。 |

## 适用性判定规则

| 维度 | CR044 判定 |
|---|---|
| 数据与状态 | 命中。需要定义 authorization layer、capability state、blocked result、kill switch state、reconciliation evidence state。 |
| 接口与依赖 | 命中。影响 `BrokerAdapter`、`GoldminerStubBrokerAdapter`、future CR044 guard tests、CP5 LLD batch。 |
| 权限与安全 | 命中。涉及 credential boundary、per-run authorization、redaction、no-real-operation guard。 |
| 外部系统 | 命中但当前禁止 runtime。`gm` / `gmtrade` 仅保留静态候选事实，不导入当前项目 runtime。 |
| 多 Story 复用 | 命中。S01 授权边界和 S02 gate contract 是 S03-S06 的共享输入。 |

结论：CR044 Feature 级设计为 `required`，不得 waived。由于本轮用户明确限定只写 CR044 scoped planning 文件，不生成 `docs/features/<feature>/DESIGN.md` / `TEST-PLAN.md` / `TASKS.md`；Feature 级细节必须由 CP5 全量设计证据承接，其中 S01-S05 为 `full-lld`，S06 为 `technical-note`，若 runbook 驱动自动 guard 则升为 `full-lld`。这不是 Feature 设计豁免，而是 CR044 scoped 输出路径约束下的 CP5 设计证据映射。

## Feature 设计矩阵

| Feature ID | Feature / Epic | 来源 | 适用性 | 判定理由 | 需要产物 | 关联 Story | 建议 lld_policy | 重访条件 |
|---|---|---|---|---|---|---|---|---|
| FEAT-CR044-AUTH | Authorization and Secret Boundary | CP2 DQ-02/03；CP3 DQ-03 | required | 权限、安全、敏感字段、运行授权边界是全部后续 Story 的前置合同。 | CP5 `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | CR044-S01 | full-lld | 任何 credential/account 材料需要真实处理时，必须暂停并发起 L3 安全授权。 |
| FEAT-CR044-GATE | Admission Gate and Capability State | CP3 DQ-01/05 | required | 需要冻结 blocked-first gate、capability state、`simulation_ready=false`、`live_ready=false` 和 fail-closed 行为。 | CP5 `process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md` | CR044-S02 | full-lld | 若后续 L3+ 授权要求真实 adapter，需新 CR 或回退 CP3。 |
| FEAT-CR044-READONLY | Readonly Query Field Mapping Blocked-First | CP3 DQ-01/02/03 | required | 涉及 cash/position/order/fill 字段映射、UNKNOWN 字段处理、敏感字段 redaction 和 L4 未授权阻断。 | CP5 `process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md` | CR044-S03 | full-lld | 用户逐 run 授权 L4 readonly query 后，新增运行探针 Story，不复用 L2 fixture 作为真实证据。 |
| FEAT-CR044-KILL | Submit / Cancel Kill Switch Contract | CP3 DQ-01/04/05 | required | submit/cancel 属高风险外部接口和回退边界，必须定义 order whitelist、cancel whitelist、dual kill switch、operation counter gate。 | CP5 `process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md` | CR044-S04 | full-lld | 若要求真实 submit/cancel，必须先通过 L5 单次授权并另行确认订单白名单。 |
| FEAT-CR044-RECON | Reconciliation and Redacted Evidence | CP3 DQ-03/04/05 | required | 对账证据、差异分类、脱敏 artifact 和禁止自动补单/撤单会影响 QA 和 CP8 风险结论。 | CP5 `process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md` | CR044-S05 | full-lld | 若真实 broker payload 需要保存，必须退回安全决策；默认只保存 redacted structure。 |
| FEAT-CR044-RUNBOOK | Runbook and No-Real-Operation Guardrails | CP3 DQ-04/05 | required | 需要把禁止操作、CP5/CP6/CP7 入口和 no-operation 证据整理为可执行运行手册；当前低代码风险可 technical-note。 | Story 内 `## 技术说明`，必要时 CP5 升级 `process/stories/CR044-S06-runbook-and-no-real-operation-guardrails-LLD.md` | CR044-S06 | technical-note；条件升 full-lld | 若 runbook 产物驱动自动 guard、脚本、schema 或状态机，升级 full-lld。 |

## Story 下游消费表

| Story ID | feature_design_refs | lld_policy.required_level | trigger_reasons | 设计证据 | CP5 审查方式 |
|---|---|---|---|---|---|
| CR044-S01 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md` | full-lld | security、permission、runtime_authorization、shared-story-boundary | `process/stories/CR044-S01-authorization-and-secret-boundary-LLD.md` | CP5 自动预检 + CR044 全量批次人工确认 |
| CR044-S02 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md`; S01 LLD | full-lld | cross-module-contract、data-model、rollback、shared-story-boundary | `process/stories/CR044-S02-admission-gate-and-capability-state-LLD.md` | CP5 自动预检 + CR044 全量批次人工确认 |
| CR044-S03 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md`; S01/S02 LLD | full-lld | external-interface、data-model、security、permission | `process/stories/CR044-S03-readonly-query-field-mapping-blocked-first-LLD.md` | CP5 自动预检 + CR044 全量批次人工确认 |
| CR044-S04 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md`; S01/S02 LLD | full-lld | external-interface、security、rollback、runtime_authorization | `process/stories/CR044-S04-submit-cancel-kill-switch-contract-LLD.md` | CP5 自动预检 + CR044 全量批次人工确认 |
| CR044-S05 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md`; S03/S04 LLD | full-lld | data-model、external-interface、security、audit、rollback | `process/stories/CR044-S05-reconciliation-and-redacted-evidence-LLD.md` | CP5 自动预检 + CR044 全量批次人工确认 |
| CR044-S06 | `docs/design/FEATURE-DESIGN-MATRIX-CR044.md`; S01-S05 design evidence | technical-note | validation、runtime_authorization、docs-handoff | Story 内 `## 技术说明`；条件升 full-lld | CP5 自动预检 + CR044 全量批次人工确认 |

## 关键决策与状态

| Decision ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 | 回退 / 切换条件 | 状态 |
|---|---|---|---|---|---|---|---|---|
| DQ-CP3-CR044-01 | architecture | 是否采用 blocked-first admission gate 并保留 stub | 已批准：保留 `GoldminerStubBrokerAdapter`，L2 只做 fixture-only guardrails。 | 真实 adapter 默认 disabled；停在 CR043。 | 推荐方案安全且可测试；备选真实 adapter 容易误触 runtime。 | 决定 S02-S05 全部 fail-closed。 | L3+ 授权后另起受控 runtime Story。 | resolved-by-user |
| DQ-CP3-CR044-02 | architecture | SDK 策略 | 已批准：`gm` Python 3.11 主选静态候选，`gmtrade` Python 3.10 fallback。 | `gmtrade` 主选隔离 runtime；双 SDK。 | 推荐方案匹配项目 runtime；备选成本高。 | 决定 S03 字段映射只记录静态候选，不导入 SDK。 | 若 `gm` 事实不足，回到 CP3/CR。 | resolved-by-user |
| DQ-CP3-CR044-03 | security | 凭据和 redaction | 已批准：零凭据持有、redaction-first、L2 禁止真实 SDK import/call。 | 后续逐 run 注入只存 hash/状态；持久凭据配置禁止。 | 推荐方案最安全。 | 影响所有 Story AC 和验证。 | 必须处理真实材料时，暂停并发起 L3 安全授权。 | resolved-by-user |
| DQ-CP3-CR044-04 | implementation | Story / LLD 批次范围 | 已批准：S01-S06，S01-S05 full-lld，S06 technical-note/条件升 full-lld。 | 只做 S01-S02；加入 L3+ runtime Story。 | 推荐方案覆盖完整 admission guard；备选 A 覆盖不足，B 越权。 | 决定 CP5 批次范围。 | 若 scope 过大，S06 可延后；不得加入真实 runtime。 | resolved-by-user |
| DQ-CP3-CR044-05 | risk_acceptance | CP3 是否等于 simulation-ready | 已批准：不等于，`simulation_ready/live_ready` 不得置 true。 | 暂停到 L3+；关闭 not-recommended。 | 推荐方案允许离线准备且防误授权。 | 防止产物误导。 | 任一产物误称 simulation-ready 必须返工。 | resolved-by-user |

## 不授权范围

CR044 当前仍不授权：`credential_read`、`login`、`connect`、`account_query`、`cash_query`、`position_query`、`order_query`、`fill_query`、`order_submit`、`order_cancel`、`simulation_runtime`、`live_runtime`、`provider_fetch`、`lake_write`、`catalog_publish`。任何真实 runtime 行为必须 fail-closed。

## 豁免与 N/A 说明

| Feature ID | 豁免 / N/A 原因 | 影响范围 | 风险接受 | 重访条件 | 责任方 |
|---|---|---|---|---|---|
| N/A | 本 CR 无 Feature waived。 | N/A | N/A | N/A | meta-se |

## 自检

| 检查项 | 结果 | 证据 |
|---|---|---|
| 所有 CR044 Feature / Epic 均已判定 | PASS | 本矩阵覆盖 FEAT-CR044-AUTH/GATE/READONLY/KILL/RECON/RUNBOOK。 |
| required Feature 均有 CP5 设计证据路径 | PASS | S01-S05 full-lld；S06 technical-note/条件升 full-lld。 |
| 每个 Story 均有 feature_design_refs 与 lld_policy | PASS | `process/stories/CR044-S01..S06-*.md`。 |
| 提前确认的关键决策已进入人工决策或 resolved | PASS | CP3 checkpoint 已 approved，5 项 DQ 为 resolved-by-user。 |
| 未触碰真实 runtime | PASS | 本矩阵只写规划，不读凭据、不连接、不查询、不下单、不撤单。 |
