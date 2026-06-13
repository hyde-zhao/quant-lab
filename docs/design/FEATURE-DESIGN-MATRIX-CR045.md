---
status: draft-for-cp4
version: "1.0"
cr_id: "CR-045"
feature_id: "FEAT-CR045-GOLDMINER-BRIDGE"
source_cr: "process/changes/CR-045-GOLDMINER-WINDOWS-BRIDGE-READONLY-PROBE-2026-06-11.md"
source_context: "process/context/CP3-CR045-DESIGN-CONTEXT.yaml"
source_hld: "docs/design/HLD-CR045-GOLDMINER-WINDOWS-BRIDGE.md"
source_adr: "docs/design/ARCHITECTURE-DECISION-CR045.md"
source_cp3: "process/checkpoints/CP3-CR045-HLD-REVIEW.md"
confirmed_by: ""
confirmed_at: ""
---

# CR045 Feature Design Matrix

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-11 | meta-se | 创建 CR045 scoped Feature 设计适用性矩阵、Feature 设计产物映射、Story LLD 分级和 CP5 批次范围。 |

## 适用性判定规则

| 维度 | CR045 判定 |
|---|---|
| 数据与状态 | 命中。需要冻结 `BridgeHealth`、`BridgeCapabilities`、`ReadonlyProbeRequest`、`ReadonlyProbeResponse`、`BridgeEvidence`、operation counters 和 blocked reason。 |
| 接口与依赖 | 命中。涉及 Windows-side bridge skeleton、WSL / Linux bridge client、fixture transport、allowlist API 和未来 `BrokerAdapter` 接入边界。 |
| 权限与安全 | 命中。涉及 L1-L5 授权层级、hard-off kill switch、zero secret custody、redaction、no-operation evidence。 |
| 外部系统 | 命中但当前禁止 runtime。Goldminer SDK / 终端上下文只属于未来 Windows trading PC，CR045 当前不启动、不登录、不连接、不查询。 |
| 多 Story 复用 | 命中。S01 授权边界、S02 API schema 和 S05 静态验证规则被 S03/S04/S06 复用。 |

结论：CR045 的 `FEAT-CR045-GOLDMINER-BRIDGE` 必须生成 Feature 级 `DESIGN.md`、`TEST-PLAN.md`、`TASKS.md`。S01-S05 使用 `full-lld`，S06 使用 `technical-note`；若 S06 引入自动 manifest、schema、guard script 或状态机，则升级为 `full-lld`。

## Feature 设计矩阵

| Feature ID | Feature / Epic | 来源 | 适用性 | 判定理由 | 需要产物 | 关联 Story | 建议 lld_policy | 重访条件 |
|---|---|---|---|---|---|---|---|---|
| FEAT-CR045-GOLDMINER-BRIDGE | Goldminer Windows Bridge L2 Skeleton and WSL/Linux Client Contract | HLD §5/§9/§19；ADR-CR045-001..007；CP3 DQ-CP3-CR045-01..06 | required | 跨 Windows/WSL/Linux 边界、外部 broker 接口、安全权限、blocked-first、敏感字段脱敏和多 Story 共享合同均命中 required 条件。 | `docs/features/cr045-goldminer-bridge/DESIGN.md`；`docs/features/cr045-goldminer-bridge/TEST-PLAN.md`；`docs/features/cr045-goldminer-bridge/TASKS.md` | CR045-S01..S06 | S01-S05 `full-lld`；S06 `technical-note` | 任一 Story 需要真实 runtime、凭据、Goldminer 登录/连接、账户查询、submit/cancel、simulation/live、provider/lake/publish 时，停止当前批次并交回 meta-po 发起 L3+ 授权或新 CR。 |

## Story 下游消费表

| Story ID | feature_design_refs | lld_policy.required_level | trigger_reasons | 设计证据 | CP5 审查方式 |
|---|---|---|---|---|---|
| CR045-S01 | `docs/features/cr045-goldminer-bridge/DESIGN.md#权限与安全`；`TEST-PLAN.md#权限--安全--失败路径`；`TASKS.md#cr045-s01` | full-lld | security、permission、runtime_authorization、shared-story-boundary | `process/stories/CR045-S01-windows-bridge-security-boundary-LLD.md` | CP5 自动预检 + CR045 全量批次人工确认 |
| CR045-S02 | `docs/features/cr045-goldminer-bridge/DESIGN.md#api--接口设计`；`TEST-PLAN.md#测试范围`；`TASKS.md#cr045-s02` | full-lld | cross-module-contract、external-interface、data-model | `process/stories/CR045-S02-bridge-health-capabilities-skeleton-LLD.md` | CP5 自动预检 + CR045 全量批次人工确认 |
| CR045-S03 | `docs/features/cr045-goldminer-bridge/DESIGN.md#feature-边界与相邻对象`；`TEST-PLAN.md#风险驱动测试`；`TASKS.md#cr045-s03` | full-lld | cross-platform-contract、external-interface、failure-path | `process/stories/CR045-S03-wsl-linux-client-contract-and-network-precheck-LLD.md` | CP5 自动预检 + CR045 全量批次人工确认 |
| CR045-S04 | `docs/features/cr045-goldminer-bridge/DESIGN.md#异常失败与降级策略`；`TEST-PLAN.md#权限--安全--失败路径`；`TASKS.md#cr045-s04` | full-lld | external-interface、security、permission、rollback | `process/stories/CR045-S04-readonly-probe-allowlist-and-blocked-first-LLD.md` | CP5 自动预检 + CR045 全量批次人工确认 |
| CR045-S05 | `docs/features/cr045-goldminer-bridge/DESIGN.md#测试与验收策略`；`TEST-PLAN.md#风险驱动测试`；`TASKS.md#cr045-s05` | full-lld | security、audit、validation、data-model | `process/stories/CR045-S05-redaction-and-no-operation-static-validation-LLD.md` | CP5 自动预检 + CR045 全量批次人工确认 |
| CR045-S06 | `docs/features/cr045-goldminer-bridge/DESIGN.md#人机协作与确认点`；`TEST-PLAN.md#手工验收`；`TASKS.md#cr045-s06` | technical-note | docs-handoff、runtime_authorization、follow_up_tracking | Story 内 `## 技术说明`；条件升 full-lld | CP5 自动预检 + CR045 全量批次人工确认 |

## 提前确认的关键决策

| Decision ID | 决策类型 | 问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 | 回退 / 切换条件 | 状态 |
|---|---|---|---|---|---|---|---|---|
| DQ-CP3-CR045-01 | architecture | WSL / 未来 Linux research server 如何接入 Windows Goldminer 环境？ | 已批准：Windows-side bridge skeleton + WSL / Linux allowlist client；Linux 侧只做研究、回测、组合生成、order intent 和 client。 | WSL / Linux direct SDK；terminal endpoint Spike；暂停 CR045。 | 推荐方案隔离 SDK runtime 和凭据；备选风险或事实不足。 | 决定 S02/S03/S04 的依赖方向。 | 官方 endpoint 可验证且 L3/L4 授权后才可切换。 | resolved-by-user |
| DQ-CP3-CR045-02 | architecture | L2 API 边界如何限定？ | 已批准：仅 health、capabilities、readonly probe skeleton。 | 提前定义真实查询 endpoint 但 disabled；health-only。 | 推荐方案覆盖目标且不过度暴露。 | 决定 S02/S04 的 API schema。 | 若 readonly skeleton 仍过宽，降级 health-only；L4 授权后新增真实 endpoint。 | resolved-by-user |
| DQ-CP3-CR045-03 | security | token/account_id 如何驻留和脱敏？ | 已批准：仅未来用户 Windows 本地持有，Agent/WSL/Linux/仓库/对话不读取不记录。 | 用户提供无真实值结构文档；WSL / Linux 持有凭据。 | 推荐方案泄漏风险最低；WSL/Linux 持有凭据禁止。 | 决定 S01/S05/S06 的安全 AC。 | 任何真实值处理需求都必须暂停并发起 L3 授权。 | resolved-by-user |
| DQ-CP3-CR045-04 | runtime_authorization | kill switch 和 allowlist 默认状态？ | 已批准：默认 hard-off，非 allowlist 或无 per-run 授权均 blocked。 | 仅日志警告；CP3 一次性授权 L4。 | 推荐方案 fail-closed；备选越权。 | 决定 S01/S04/S05 的失败路径。 | 仅后续 L3/L4 run manifest 明确允许时打开。 | resolved-by-user |
| DQ-CP3-CR045-05 | risk_acceptance | 是否接受 skeleton-ready 关闭语义？ | 已批准：可关闭为 `readonly-bridge-skeleton-ready` 或 `blocked-by-runtime-authorization`，不宣称 real-readonly-verified。 | 等 L4 后再推进；取消 CR045。 | 推荐方案可先交付安全工程准备。 | 决定 S06/CP8 文案。 | 若用户要求真实只读，先 L3/L4 授权。 | resolved-by-user |
| DQ-CP3-CR045-06 | implementation | Story / LLD 批次如何划分？ | 已批准：S01-S05 full-lld，S06 technical-note/条件升 full-lld。 | 只做 S01-S03；加入真实 L4/L5 Story。 | 推荐方案覆盖安全、bridge、client、readonly、redaction、runbook。 | 决定 CP4/CP5 范围。 | 缩小时可延后 S06；不得加入真实 runtime。 | resolved-by-user |

## 豁免与 N/A 说明

| Feature ID | 豁免 / N/A 原因 | 影响范围 | 风险接受 | 重访条件 | 责任方 |
|---|---|---|---|---|---|
| global-blueprint-update | CR045 是 CR-scoped bridge planning；HLD §2 已将全局 `BLUEPRINT.md` / `DOMAIN-MAP.md` / `DEPENDENCY-MAP.md` 判定为 waived-for-cr-scoped-hld。 | 不回写长期全局蓝图，不阻塞 CR045 Feature 设计。 | CP3 accepted。 | 若 Goldminer bridge 升为长期生产能力，必须通过新 CR 增量回写全局蓝图。 | meta-po / meta-se |
| feature-waiver | 本 CR 无 required Feature waived。 | N/A | N/A | N/A | meta-se |

## 自检

| 检查项 | 结果 | 证据 |
|---|---|---|
| 所有 CR045 Feature / Epic 均已判定 | PASS | 本矩阵覆盖唯一 required Feature `FEAT-CR045-GOLDMINER-BRIDGE`。 |
| required Feature 均有产物计划或已生成 | PASS | `docs/features/cr045-goldminer-bridge/DESIGN.md`、`TEST-PLAN.md`、`TASKS.md`。 |
| 每个 Story 均有 feature_design_refs 与 lld_policy | PASS | `process/stories/CR045-S01..S06-*.md`。 |
| 提前确认的关键决策已进入人工决策队列或 N/A | PASS | CP3 checkpoint 已 approved；DQ-CP3-CR045-01..06 均为 resolved-by-user。 |
| 未触碰真实 runtime | PASS | 本矩阵只写 CP4 规划，不读凭据、不启动 Windows bridge、不连接 Goldminer、不查询账户、不交易、不 simulation/live、不 provider/lake/publish。 |
