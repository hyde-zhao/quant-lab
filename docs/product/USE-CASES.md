---
status: draft
version: "0.4"
confirmed_by: ""
confirmed_at: ""
engagement_mode: production
scenario_subject_type: target-artifact
scenario_subject_id: "CR-160"
target_artifact_type: workflow
governance_mode: review-gated
review_policy: strict
delivery_routing:
  mode: project-readme-contract
  output_root: "docs/product"
  source: docs
total_use_cases: 4
---

# Product Use Cases

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级用例基线草案，承接 `docs/components/MULTIFACTOR-RESEARCH.md` 和 no-lake initial slice 证据。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充模板 frontmatter、Scenario Gray Areas 详情、用户可见确认记录和 Deferred Ideas。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation 基线；保留 CR157 deferred 历史并记录 promotion 映射。 |
| v0.4 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review workflow 用例，并将 `DF-CR157-003` 标记为 promoted to CR160。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158` / `CR-160`
- 当前门禁：CR160 CP8 release readiness
- 旧基线保留：当前仓库未发现既有 `docs/product/USE-CASES.md`，本文件作为产品层用例入口；既有组件说明和场景文档不被重写。

## UC-58 多因子策略研究到准入

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58 |
| 名称 | 多因子策略研究到准入 |
| 主要用户 | 量化研究负责人、策略研究员、框架维护者 |
| 目标 | 在不授权运行时、交易、发布或真实写湖的前提下，升级 Stage 2 多因子研究框架合同，使后续真实研究产物可以被一致地打包、校验和交接。 |
| 当前 CR 范围 | Stage 2 framework deepening：成熟准入包 builder、研究证据索引、handoff 合同、fail-closed 校验和 no-runtime guard。 |
| 明确不在范围 | provider fetch、NAS 同步、lake write、catalog/store/registry 写入、QMT/MiniQMT/xtquant/gateway、simulation、paper/live trading、账户或订单操作、真实发布。 |

### 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 复用已有 Stage 2 no-lake 支撑 | 读取既有合同、typed unavailable 和历史 CR030/CR039/CR155 证据引用。 | 能形成候选输入清单，且不读取真实凭据、NAS 或 provider。 |
| 2 | 为成熟研究产物建立准入包 builder | 将真实研究产物引用、验证报告、runner offline preflight、observation plan 和风险策略组合成 mature admission package。 | package 字段完整，缺失证据 fail-closed，不把 package 解释为 runtime authorization。 |
| 3 | 硬化 Stage 2/Stage 3 handoff | 明确 Stage 2 输出、Stage 3 研究机输入和 Stage 4 观察候选之间的边界。 | handoff 可追溯到 evidence index、run manifest、data release ref 和不授权清单。 |
| 4 | 验证 no-runtime / no-publish 防线 | 对 lake/provider/catalog/QMT/gateway/simulation/live/credential 计数执行 fail-closed 校验。 | 任一禁用计数非 0 时阻断，输出可审计原因。 |
| 5 | 给后续策略类型扩展留接口 | 把事件型和 ML 策略 adapter 作为兼容合同和 backlog，不在 CR157 first slice 实现。 | CR157 不扩大为横切策略类型重构，后续 CR 可独立复用 adapter contract。 |

## Scenario Gray Areas

**讨论日志**：`process/discussions/CP2-CR157-SCENARIO-DISCUSSION-LOG.md`  
**恢复点**：`process/checks/CP2-CR157-DISCUSSION-CHECKPOINT.json`

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐讨论顺序 | 状态 | canonical refs |
|---|---|---|---|---:|---|---|
| SGQ-CR157-001 | CR157 first slice 是否只覆盖多因子 mature admission package builder 与 Stage 2/Stage 3 handoff hardening，还是同时纳入 event/ML adapters？ | 该选择会改变 CP3 架构边界、Feature owner、Story 数量、验证矩阵和后续 adapter 合同耦合程度。 | scope / architecture / story planning / implementation / validation | 1 | selected | `process/checkpoints/CP2-CR157-STAGE2-MULTIFACTOR-RESEARCH-FRAMEWORK-UPGRADE-SCOPE.md` |
| SGQ-CR157-002 | CP2 approve 是否授权真实 lake/NAS/provider/credential/QMT/gateway/simulation/live/trading/publish？ | 该选择决定安全边界和 runtime authorization 是否需要独立门禁。 | security / runtime_authorization / risk_acceptance | 2 | resolved | `process/changes/CR-157-STAGE2-MULTIFACTOR-RESEARCH-FRAMEWORK-UPGRADE-2026-07-05.md` |
| SGQ-CR157-003 | CP2 approve 是否允许直接进入 HLD、Story split、LLD 或实现？ | 该选择决定工作流是否绕过关键门禁。 | workflow gating / architecture / implementation | 3 | resolved | `process/context/CP2-CR157-STAGE2-MULTIFACTOR-RESEARCH-FRAMEWORK-UPGRADE-CONTEXT.yaml` |

## 用户可见场景确认证据

| Question ID | 问题 | 选项 / 候选理解 | 推荐方案 | 用户回答 | 复述确认 | 影响面 | 来源 | 状态 |
|---|---|---|---|---|---|---|---|---|
| SGQ-CR157-001 | CR157 first slice 是否延后 event/ML adapter implementation？ | A. 只做多因子 Stage 2 framework deepening；B. 加 event adapter；C. 加 event + ML adapters；D. 只做文档不做后续实现。 | A | 用户回复 `approve`。 | 本轮只覆盖多因子 Stage 2 framework deepening；event/ML adapters 进入 backlog 或后续 CR。 | scope / validation / gate | CR157 CP2 | confirmed |
| SGQ-CR157-002 | 是否授权真实外部系统、runtime 或 publish？ | A. 全部不授权；B. 授权部分只读；C. 授权 runtime。 | A | CR157 正文已明确不授权。 | CP2 approval 不改变不授权边界。 | security / runtime_authorization | CR157 frontmatter | confirmed |
| SGQ-CR157-003 | CP2 前是否允许进入 HLD/Story/LLD/实现？ | A. 不允许；B. 允许 HLD；C. 允许实现准备。 | A | CR157 正文已明确 CP2 前阻断。 | CP2 未批准前只允许产品基线和门禁准备。 | workflow / gate | CR157 Checkpoint Index | confirmed |

## Deferred Ideas

| ID | 想法 / 风险 / 扩展场景 | 来源 | 延后原因 | 触发重启条件 |
|---|---|---|---|---|
| DF-CR157-001 | Event strategy adapter implementation | SGQ-CR157-001 | 避免 CR157 first slice 扩大为跨策略类型重构。 | CR157 CP8 后，或 CP3 前用户明确修改 first slice 范围。 |
| DF-CR157-002 | ML strategy adapter implementation | SGQ-CR157-001 | 避免 FEAT-13 evidence index 合同过早绑定 ML 专属语义。 | Event/ML strategy E2E 需要统一 adapter contract 时另起 CR。 |
| DF-CR157-003 | Stage 4 observation review workflow | MVP-SCOPE | 当前 CR 不授权 simulation / paper / live 或 runtime。 | 已 promoted to `CR-160`，由 CR160 定义 Stage 4 observation review workflow 和 authorization gate contract；Stage 5 / runtime 仍需后续 CR。 |

## CR158 Deferred Promotion Mapping

| Legacy Deferred ID | CR158 tracking ID | 状态 | 正式 CR | 保留策略 |
|---|---|---|---|---|
| DF-CR157-001 | FU-CR157-001 | promoted-active | `CR-158` | 保留 CR157 deferred 历史，CR158 承接 event adapter 产品基线、架构和实现路径。 |
| DF-CR157-002 | FU-CR157-002 | promoted-active | `CR-158` | 保留 CR157 deferred 历史，CR158 承接 ML adapter 产品基线、架构和实现路径。 |

## CR160 Deferred Promotion Mapping

| Legacy Deferred ID | CR160 tracking ID | 状态 | 正式 CR | 保留策略 |
|---|---|---|---|---|
| DF-CR157-003 | FU-CR160-STAGE4-OBSERVATION-REVIEW | promoted-active | `CR-160` | 保留 CR157 deferred 历史，CR160 承接 Stage 4 observation review workflow、observation plan template、分层 checklist、fail-closed decision table 和 authorization gate contract；不承接 Stage 5 paper/simulation/live/runtime authorization。 |

## UC-58-CR160 Stage 4 Observation Review Workflow

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR160 |
| 名称 | Stage 4 observation review workflow |
| 主要用户 | 量化研究负责人、策略研究员、验证负责人、框架维护者 |
| 触发条件 | Stage 3 mature research package 或 admission package 需要进入 observation review，但 simulation / paper / live / runtime 尚未授权。 |
| 目标 | 在不授权新数据访问、runtime、simulation、paper 或 live 的前提下，定义 `observation_plan_ref` 指向的 plan 内容规范、分层审查 checklist、fail-closed decision table 和 Stage 4 到 Stage 5 的 authorization gate contract。 |
| 当前 CR 范围 | 纯设计交付：HLD、observation plan template、Stage 1/2/3 分层 checklist、EvidenceProfile / AdmissionReadiness / ObservationDecision / EscalationRoute 决策表、CR155 blocked admission fail-closed 样例、产品基线追溯。 |
| 明确不在范围 | 代码实现、schema/checker、执行 observation、执行 simulation/paper/live、strategy remediation、CR155 晋级、新 real lake read/write、NAS/provider/credential access、catalog/store/registry/model/prediction write、broker/order/trading、Git remote write、publish。 |
| 退出条件 | CP8 必须确认 design-only `READY_WITH_RISK`、产品基线已刷新、CR155 仍分类为 `blocked_admission_failed`，并确认 contract-only lane 不能输出 `paper_candidate=true` 或 `simulation_ready`。 |

### CR160 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 审查 Stage 3 handoff 是否具备 Stage 4 输入 | 读取 `observation_plan_ref`、admission package ref、research evidence index、input refs 和 blocked claims。 | 缺少 observation plan instance、P0 evidence 或 admission 非阻断证据时 fail-closed。 |
| 2 | 区分 contract-level 与 real-data evidence | 将输入归类为 `contract_only`、`real_data_validated`、`runtime_authorized` 或 `unknown`。 | `contract_only` lane 只能输出 contract review 结论，不能输出 paper/simulation readiness。 |
| 3 | 按 Stage 1/2/3 分层 checklist 审查 | 分别审查 PIT/universe/lineage、factor methodology/typed unavailable、statistical gate/OOS/economic significance/capacity/rerun。 | checklist 至少覆盖 4 层且每项有 PASS/NEEDS_REVIEW/FAIL/N/A。 |
| 4 | 用 CR155 反例验证 fail-closed | 将 CR155 `BLOCKED/FAIL/paper_candidate=false` 分类为 `blocked_admission_failed`。 | rerun consistency PASS 不提升 evidence 等级；admission FAIL 和 paper_candidate=false 必须保持阻断。 |
| 5 | 输出后续路由而非运行授权 | 根据 decision table 输出 blocked、needs_real_data_evidence、contract_review_complete 或 follow-up escalation。 | 不产生 runtime authorization；Stage 5 paper/simulation gate 必须由后续 CR 独立授权。 |

## UC-58-CR158 Event + ML Strategy Adapter Unified Implementation

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR158 |
| 名称 | Event + ML strategy adapter 统一实现路径 |
| 主要用户 | 量化研究负责人、策略研究员、框架维护者、验证负责人 |
| 触发条件 | CR157 已 CP8 关闭，用户明确要求把 `DF-CR157-001` 与 `DF-CR157-002` 合并为一个 CR。 |
| 目标 | 在不授权真实 event feed、真实模型训练、外部模型服务、provider/lake/NAS/credential/runtime/trading/publish 的前提下，统一 event strategy 与 ML strategy adapter 的产品范围、共享 contract、证据索引语义、handoff 和 fixture/static 验证路径。 |
| 当前 CR 范围 | CP2 产品基线确认、CP3 架构设计、CP4/CP5 Story + LLD 批次、CP6/CP7 本地静态/fixture 实现与验证、CP8 release readiness。 |
| 明确不在范围 | real event feed/live listener、real model training、external model service、model registry promotion、real lake/NAS/provider/credential access、QMT/gateway/runtime、simulation/paper/live/trading/broker、catalog/store/registry/prediction write、external framework run、Git remote write、publish。 |
| 退出条件 | CP2 approved 后才可进入 HLD；CP5 approved 后才可实现；CP7 必须证明 no-runtime/no-publish 边界。 |

### CR158 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 统一 event/ML adapter 产品边界 | 将两个 deferred items 合并为一个 adapter Change Package，并保留 CR157 历史映射。 | 一个 CR158 scope 同时覆盖 event adapter 与 ML adapter，且不会重开 CR157。 |
| 2 | 定义共享 adapter core 与类型扩展 | 区分共用 `StrategyTypeAdapter` / evidence / handoff 合同和 event-only、ML-only 扩展。 | 共享字段和类型专属字段可枚举；不得把 event 语义硬套到 ML，或反向硬套。 |
| 3 | 保持 evidence index refs-only 基线 | 扩展 evidence item 时只引用 fixture/static 证据，不复制报告正文或运行 transcript。 | event/ML evidence 都可回链到 refs；大型正文不进入 index。 |
| 4 | 证明 no-runtime 边界 | 对 event feed、model training、registry、provider、lake、credential、runtime、trading、publish 等计数执行 fail-closed 检查。 | 禁用操作计数必须为 0；任何非 0 均阻断。 |
| 5 | 形成可交付 adapter Story 批次 | CP2/CP3 后拆分共享 contract、event adapter、ML adapter、evidence/handoff、verification/docs Story。 | Story 可追溯到 REQ/SC；CP5 全量设计证据批准前不得实现。 |

## CR158 Scenario Gray Areas

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐讨论顺序 | 状态 | canonical refs |
|---|---|---|---|---:|---|---|
| SGQ-CR158-001 | Event adapter 与 ML adapter 是否使用一个共享核心 contract，并通过 type-specific extension 表达差异？ | 决定 HLD/ADR、Story 切分、schema 演进和验证矩阵。 | scope / architecture / implementation / validation | 1 | pending CP2 | `process/checkpoints/CP2-CR158-EVENT-ML-STRATEGY-ADAPTER-SCOPE.md` |
| SGQ-CR158-002 | CR158 是否只授权 local/static/fixture adapter 行为，不授权真实 feed/training/runtime/publish？ | 决定是否需要 runtime authorization CR，避免 release overclaim。 | security / runtime_authorization / risk_acceptance | 2 | pending CP2 | `process/changes/CR-158-EVENT-ML-STRATEGY-ADAPTER-UNIFIED-IMPLEMENTATION-2026-07-05.md` |
| SGQ-CR158-003 | CP2 approve 是否允许直接进入实现？ | 决定是否绕过 CP3/CP5。 | workflow gating / implementation | 3 | pending CP2 | `process/checks/CP0-CR158.route-plan.json` |

## CR158 用户可见场景确认证据

| Question ID | 问题 | 选项 / 候选理解 | 推荐方案 | 用户回答 | 复述确认 | 影响面 | 来源 | 状态 |
|---|---|---|---|---|---|---|---|---|
| SGQ-CR158-001 | 是否合并 event + ML adapter 为一个 CR？ | A. 合并为一个统一 adapter CR；B. 拆 event CR 与 ML CR；C. 只做 event；D. 只做 ML。 | A | 用户回复“批准，继续推进”。 | 本轮按一个 CR158 承接两个 deferred items；CP2 前只做产品基线和门禁，不启动实现。 | scope / architecture / validation | user request + CR158 CP0 | confirmed-for-CP2-brief |
| SGQ-CR158-002 | 是否授权真实 runtime / real data / publish？ | A. 全部不授权；B. 授权只读数据；C. 授权运行时训练或 feed。 | A | CR158 frontmatter 已明确不授权。 | CP2 approval 不授权真实 feed、训练、provider、lake、credential、runtime、trading 或 publish。 | security / runtime_authorization | CR158 frontmatter | pending CP2 |
| SGQ-CR158-003 | CP2 通过后下一步是什么？ | A. 进入 HLD/ADR；B. 直接实现；C. 取消 CR。 | A | route plan 已生成。 | CP2 只授权进入 solution-design；实现仍需 CP5。 | workflow / gate | route plan | pending CP2 |

## UC-58-CR157 Stage 2 Framework Deepening

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR157 |
| 触发条件 | CR156 已关闭，FU-CR154-001 已关闭，用户要求推进 Stage 2 多因子研究框架升级。 |
| 前置条件 | CP0 已通过；产品基线 draft 已生成；CP2 待人工确认。 |
| 主要产出 | mature admission package builder scope、Stage 2/Stage 3 handoff scope、requirements、scenarios、test matrix、MVP scope、release slices。 |
| 退出条件 | CP2 approved 后进入 solution-design；CP2 未批准时不得 HLD、Story split、LLD 或实现。 |
