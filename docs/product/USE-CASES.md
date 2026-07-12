---
status: draft
version: "0.8"
confirmed_by: ""
confirmed_at: ""
engagement_mode: production
scenario_subject_type: target-artifact
scenario_subject_id: "CR-164"
target_artifact_type: workflow
governance_mode: review-gated
review_policy: strict
delivery_routing:
  mode: project-readme-contract
  output_root: "docs/product"
  source: docs
total_use_cases: 7
---

# Product Use Cases

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级用例基线草案，承接 `docs/components/MULTIFACTOR-RESEARCH.md` 和 no-lake initial slice 证据。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充模板 frontmatter、Scenario Gray Areas 详情、用户可见确认记录和 Deferred Ideas。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation 基线；保留 CR157 deferred 历史并记录 promotion 映射。 |
| v0.4 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review workflow 用例，并将 `DF-CR157-003` 标记为 promoted to CR160。 |
| v0.5 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 strategy-admission evidence availability 用例；保留 CR161 closed 历史，仅刷新当前产品基线。 |
| v0.6 | 2026-07-11 | meta-pm | CR163 增量追加 experiment-family trial lineage instrumentation 用例、候选生产入口清单、count / availability 语义和 SGQ 待确认项；保留既有 CR157-CR162 基线。 |
| v0.7 | 2026-07-11 | meta-pm | 回填 SGQ-CR163-001..004 全部选择 A；将 inventory 统一表述为“2 条去重 producer chains / 4 个 instrumentation mappings”，并收紧 C1 raw-lineage claim ceiling。 |
| v0.8 | 2026-07-12 | meta-pm | CR164 增量追加 multiple-testing / WRC-SPA / PBO-CSCV / DSR 可计算证据旅程、fail-closed 语义及 UC-59/UC-60 compatibility 边界；回填 SGQ-CR164-001..004 全部确认强化推荐 A。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164`
- 当前门禁：CR164 CP3 已批准、CP4 PASS；5/5 LLD ready，等待 CP5 全量确认
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

## UC-58-CR161 Strategy Admission Evidence Availability

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR161 |
| 名称 | Strategy admission evidence availability and fail-closed review |
| 主要用户 | 量化研究负责人、策略研究员、验证负责人、框架维护者 |
| 触发条件 | 策略准入需要说明多重检验、数据偷窥、过拟合、walk-forward/OOS、经济成本和容量/流动性证据是否可计算。 |
| 目标 | 用七对象 evidence contract 明确策略准入需要的证据，并在 mandatory evidence 不存在或不能计算时输出 `typed_unavailable` 和阻断结论。 |
| 当前基线范围 | `ExperimentFamilyManifest`、`MultipleTestingEvidence`、`DataSnoopingEvidence`、`OverfitRiskEvidence`、`WalkForwardEvidence`、`EconomicCostEvidence`、`CapacityLiquidityEvidence`；与 CR151 statistical gate 和 CR154 follow-up 集成，不新建并行 gate。 |
| 明确不在范围 | 不计算 FDR/PBO/DSR、fold-level OOS、真实 TCA/market impact 或容量 sizing；不改造研究引擎 trial lineage；不访问真实数据或运行时。 |
| 负向回归 | CR155 保持 blocked；缺少 lineage、p-values 或 fold metrics 时只能给出 `typed_unavailable`，不得补造 PASS 或提升准入。 |
| 退出条件 | CR162 静态验证确认当前基线可追溯七对象、fail-closed ceiling、CR155 negative regression 与 FU-CR161-001..006；计算实现仍需独立 CR。 |

### CR161 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 识别一个策略准入缺少哪些证据 | 将 C1-C4 映射至七个 evidence objects 和 availability 状态。 | 每个 mandatory object 都有可发现的名称、用途和后续 producer。 |
| 2 | 防止缺失证据被静默通过 | 对缺少 trial lineage、统计输入、fold metrics 或成本/容量输入的对象给出 `typed_unavailable`。 | 缺失不能转为 PASS、NEEDS_REVIEW 或 runtime readiness。 |
| 3 | 消费已有失败样例 | 以 CR155 的既有 blocked evidence 运行负向追溯。 | CR155 仍 blocked；不重建历史数值，不把 rerun consistency 误读为新证据。 |
| 4 | 计划后续计算能力 | 追溯 FU-CR161-001..006 到 trial lineage、统计/OOS producer、成本容量 producer 和独立验证控制。 | follow-up 是 candidate，不授权实现、数据或运行时。 |

## UC-58-CR163 Experiment-Family Trial Lineage Instrumentation

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR163 |
| 名称 | Experiment-family trial lineage instrumentation |
| 主要用户 | 量化研究负责人、策略研究员、准入审查者、框架维护者、独立验证者 |
| 触发条件 | 候选生产研究准备开始参数、种子或配置搜索，而现有 `ExperimentManifest` 只能描述单次 run，准入侧的 trial lineage 仍为 `typed_unavailable`。 |
| 输入 | 预先声明的 experiment family、冻结的候选生产入口、每个 trial / attempt / selection 事件、单次 run 的 `run_id` / `experiment_id` / artifact refs。 |
| 处理逻辑 | 首个 trial 前声明 family；运行期间 append-only 记录 trial、attempt、失败/取消/排除与 selection；结束后校验完整性并 seal；后续修正只能 supersede。 |
| 输出 / 结果 | 可验证的 family lineage availability 与 ref、raw trial count、seal / supersession / tamper 结论，以及供既有 CR151/CR154/admission consumer 使用的 fail-closed 输入。 |
| 前置条件 | CR163 CP2/CP3/CP5 分别批准产品、架构和设计证据；真实运行与数据访问仍需独立授权。 |
| 排除情况 | 不计算 effective trial count、FDR/BH、WRC/SPA、PBO/CSCV、DSR、walk-forward、TCA、capacity 或 alpha decay；不回填历史 lineage；不提升 CR155。 |
| 成功标准 | 冻结入口清单 P0 覆盖率 100%；每个声明 trial 恰有一个稳定 trial identity；重试不增加 raw count，不同 seed 增加；seal 后原版本 0 次原地修改；tamper / 缺记录 / count 不一致 100% fail-closed；forbidden operation counts 全为 0。 |
| C1 claim ceiling | CR163 只使未来合法 instrumented run 的 C1 raw-lineage input 可就绪；它不提供 p-values、effective-trial method 或 multiple-testing/data-snooping/overfit 计算，因此不使 C1 computable。 |

### CR163 候选生产入口清单（CP2 冻结候选）

| Inventory ID | 分类 | 路径 / symbol | CP2 处理 | 仓库事实 |
|---|---|---|---|---|
| CPI-CR163-001 | P0 public entrypoint | `scripts/research/run_multifactor_strategy_research.py::main` → legacy wrapper → `engine.mature_multifactor_research.run_stage3_mature_multifactor_research` | included；public wrapper 与 engine orchestration 均需接入共享 producer contract | runner 调用 Stage 3 orchestration，后者调用 `build_strategy_candidate` 产出 `StrategyCandidate`。 |
| CPI-CR163-002 | P0 legacy entrypoint | `scripts/legacy/research/run_multifactor_strategy_candidates.py` → `engine.multifactor_strategy_candidates.run_strategy_research` | included；保留兼容入口，避免 legacy 候选链绕过 lineage | `run_strategy_research` 调用 `build_strategy_candidates`、refine 与 admission package builder。 |
| CPI-CR163-003 | P0 construction hook | `engine.mature_multifactor_research.build_strategy_candidate` | included as hook；不得被视为第三条独立 trial | Stage 3 orchestration 的直接候选构造点。 |
| CPI-CR163-004 | P0 construction hook | `engine.multifactor_strategy_candidates.build_strategy_candidates` | included as hook；不得被视为额外 trial | CR039 研究 runner 的候选构造点。 |
| CPI-CR163-X01 | excluded factor discovery | `engine.anomaly_discovery.run_anomaly_discovery` | excluded；产出 factor/anomaly discovery candidate，不是本 CR 的 strategy-admission candidate family | 输出 anomaly candidates / decisions；后续进入 factor catalog。 |
| CPI-CR163-X02 | excluded compatibility adapter | `engine.mature_multifactor_framework.build_project_strategy_candidate_from_cr039` | excluded from producer count；只归一化既有 CR039 candidate | 输入已有 candidate，不发起搜索或新 trial。 |
| CPI-CR163-X03 | excluded consumer | `engine.strategy_admission_statistical_gate`、`engine.cross_strategy_reliability_gates`、`engine.strategy_admission_package` | consumer integration only | 消费 trial/count/availability，不生产候选 family。 |
| CPI-CR163-X04 | excluded contract | `engine.backtest_production_contracts.build_backtest_run_spec`、`engine.research_manifest.ExperimentManifest` | shared identity contract only | 创建单次 run metadata，不执行候选搜索。 |
| CPI-CR163-X05 | compatibility-only | UC-59 ML / UC-60 event fixture-static adapters | shared producer contract compatibility；real runner instrumentation N/A | 当前没有已授权的 real ML/event candidate runner；不得伪称 runtime-ready。 |

P0 coverage 定义：共有 **2 条去重 producer chains、4 个 instrumentation mappings**；`CPI-CR163-001..004` 每项都必须有“声明 family / 记录 trial+attempt+selection / seal+completeness+ref validate / consumer availability”映射，4/4 才是 100%。包装入口与其 construction hook 属于同一生产链，raw trial count 只能由 stable trial identity 去重，不能按函数调用次数累加。

Availability ceiling：未来原生 instrumented run 只有在 seal、completeness、reference integrity 与 count/tamper validation 全部通过后，`ExperimentFamilyManifest` 才可为 `present`；未 instrumented producer/path 保持 `typed_unavailable`；invalid、incomplete 或 tampered lineage 必须为 `blocked`。这只准备 C1 raw-lineage input，不使 C1 computable。

### CR163 Scenario Gray Areas 与待转问 SGQ

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐 | 状态 |
|---|---|---|---|---|---|
| SGQ-CR163-001 | P0 清单是否冻结为 2 条去重 producer chains / 4 个 instrumentation mappings，并把 anomaly/adapter/consumer/contract 路径排除？ | 决定 instrumentation 完整性和“100% coverage”的分母。 | scope / architecture / validation / maintenance | A：冻结 CPI-CR163-001..004，以 stable identity 防止 wrapper+hook 双计数。 | confirmed-A |
| SGQ-CR163-002 | raw trial count 是否采用“不同参数或 seed = 不同 trial；同一 trial 的 retry = 新 attempt、不增加 trial；失败/取消/排除仍保留并计数”？ | 决定准入 count 可审计性，避免事后缩小 family。 | semantics / validation / risk | A：append-only 保留所有已声明 trial。 | confirmed-A |
| SGQ-CR163-003 | 是否维持 `effective_trial_count=typed_unavailable` 且 ref / method 为空，直到独立统计 CR？ | 防止 lineage instrumentation 被误读为 statistical correction。 | scope / claim ceiling / gate | A：CR163 只提供 raw lineage facts。 | confirmed-A |
| SGQ-CR163-004 | seal 后纠错是否只允许创建 superseding version，并保持旧 hash/ref 可验证？ | 决定审计、tamper detection 和恢复成本。 | integrity / recovery / release | A：禁止原地改写 sealed version。 | confirmed-A |

## CR163 Deferred Ideas

| ID | 内容 | 状态 | 重启条件 |
|---|---|---|---|
| DF-CR163-001 | effective trial count 与独立 statistical correction producer | deferred | family lineage 已稳定，另起 CR 明确方法、输入与独立验证。 |
| DF-CR163-002 | 历史 research run lineage backfill | deferred / not authorized | 独立审计与数据授权明确，且不会把推断记录伪装为原生 instrumentation。 |
| DF-CR163-003 | real ML / event candidate runner instrumentation | deferred | real runner 存在并通过独立 runtime/data authorization；当前只保留 contract compatibility。 |

## UC-58-CR164 Computable Multiple-Testing and Backtest-Overfitting Evidence

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR164 |
| 名称 | Computable multiple-testing / data-snooping / PBO / DSR evidence |
| 主要用户 | 量化研究负责人、策略研究员、准入审查者、独立验证者、框架维护者 |
| 触发条件 | CR163 已提供 sealed、validation-bound experiment-family lineage 与 `raw_trial_count`，但 CR161/CR154 的 FDR/BH、WRC/SPA、PBO/CSCV、DSR 与 effective-trial slots 仍缺少可计算 provenance。 |
| 输入 | 可信绑定的 family lineage ref/hash/raw count；完整且有限的候选级指标或 p-values；方法所需的对齐 return path、split/fold、样本长度、Sharpe、偏度、峰度与 provenance refs。 |
| 处理逻辑 | 先做 lineage、完整性、有限值、样本/候选/split 充分性 precheck；只对输入充分的方法确定性计算；逐方法输出 present / typed_unavailable / blocked；再按 claim 类型和方法冲突规则投影到既有 CR151/CR154/admission consumers。 |
| 输出 / 结果 | 方法级计算证据、输入/方法/参数/provenance refs、确定性摘要、不可用或阻断原因，以及不会提高原有失败状态的 admission projection。 |
| 前置条件 | CP2 冻结方法集与定量充分性，CP3 冻结 schema/模块/算法选择，CP5 批准全部设计证据；本阶段只形成产品基线。 |
| 排除情况 | 不执行真实统计批次、不读取 production/lake/NAS/provider/credential、不调用外部框架、不交易、不发布、不远端写；不重建 CR155 历史输入。 |
| 成功标准 | 同一规范化 fixture 重复计算 10 次得到 1 个稳定结果摘要；每个选定方法的 required-input 覆盖 100%；NaN/Inf/退化/低样本/缺 lineage/hash mismatch 100% typed_unavailable 或 blocked；CR155 1/1 保持 blocked；禁止操作计数全部为 0。 |

### CR164 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 确认同一实验族与候选集合 | 校验 CR163 lineage availability、ref/hash、raw count 与候选级输入 membership 一致。 | 只有 sealed 且 validation-bound 的完整 family 可进入计算；缺失为 typed_unavailable，冲突或篡改为 blocked。 |
| 2 | 获得多重检验与 data-snooping 控制 | 对完整有限输入按已批准方法计算 BH 与 WRC/SPA，记录方法、参数、输入摘要和 provenance。 | 方法结果可复跑；缺少 claim-relevant 方法时不得输出 statistical-significance PASS。 |
| 3 | 量化回测过拟合风险 | 对满足候选、return-path 和 split 充分性的 family 计算 PBO/CSCV。 | split 数、训练/测试观察与 loss ranking 完整；不充分时 fail-closed。 |
| 4 | 对 Sharpe/IC 声明做 deflation | 在批准的 trial-count 边界和有限矩输入上计算 DSR 或保持 typed_unavailable。 | 不以 raw count 冒充 effective count；当前 consumer 要求 effective count而未提供时，deflated-performance wording 保持 blocked。 |
| 5 | 解释部分可用与方法冲突 | 逐方法保留结果，并用最保守 claim projection 合并。 | 任一 mandatory 方法 blocked 则相关 claim blocked；FAIL 不因另一方法 PASS 而提升；冲突进入 needs_review 或 blocked，不做 OR-pass。 |
| 6 | 复用既有 admission consumers | 将证据 refs 投影到 CR151 statistical gate、CR154 Gate 1 与 admission package。 | 不创建竞争 gate；原状态只能保持或恶化，CR155 仍 blocked。 |

### CR164 Scenario Gray Areas 与 Relay SGQ

**讨论日志**：`process/discussions/CP2-CR164-SCENARIO-DISCUSSION-LOG.md`
**恢复点**：`process/checks/CP2-CR164-DISCUSSION-CHECKPOINT.json`

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐 | 状态 |
|---|---|---|---|---|---|
| SGA-CR164-001 | MVP 是 BH-only，还是同时覆盖 WRC/SPA、PBO/CSCV 与 DSR？ | 决定 C1 claim ceiling、输入面、验证矩阵与交付价值。 | scope / complexity / validation / gate | A：四类方法均纳入，逐方法 fail-closed，claim-relevant mandatory methods 无 OR-pass。 | confirmed-A |
| SGA-CR164-002 | effective trial count 是否在同一切片计算？ | 当前 CR163 明确禁止 effective count，CR154 对部分 deflated claims 又要求它。 | scope / methodology / claim ceiling / maintenance | A：MVP 保持 typed_unavailable；DSR 显式声明 raw-count input 且不别名 effective count。 | confirmed-A |
| SGA-CR164-003 | 各方法的最小候选、split/fold 与样本阈值是多少？ | 没有可量化下限会把退化或低信息输入误报为可计算。 | validation / risk / user value | A：采用方法特定保守最低线并冻结 consolidated quantitative AC。 | confirmed-A |
| SGA-CR164-004 | UC-59 ML / UC-60 event 是当前实现对象还是 compatibility consumer？ | 决定 adapter scope 与 cross-strategy schema 负担。 | scope / compatibility / story planning | A：UC-58 实现，UC-59/60 compatibility-only。 | confirmed-A |

### CR164 用户可见场景确认证据

| Question ID | 选项 | 推荐 | 用户回答 | 复述确认 | 状态 |
|---|---|---|---|---|---|
| SGQ-CR164-001 | A 四类方法 + conservative aggregation；B BH-only；C defer WRC/SPA | A | `批准，继续推进项目` | 四类方法均纳入；BH PASS + PBO FAIL 不得产生 clean PASS。 | confirmed |
| SGQ-CR164-002 | A raw-count DSR/effective unavailable；B compute effective；C defer DSR | A | `批准，继续推进项目` | CP3 必须声明 `dsr_input_method=raw_trial_count`，不得别名 effective count。 | confirmed |
| SGQ-CR164-003 | A 方法特定阈值 + consolidated AC；B stricter floor；C defer to CP3 | A | `批准，继续推进项目` | 采用 A 的 minima 与 10 行量化验收表。 | confirmed |
| SGQ-CR164-004 | A UC-58 implementation / UC-59/60 compatibility；B adapters in scope；C no compatibility | A | `批准，继续推进项目` | UC-59/60 缺同等输入时 fail-closed。 | confirmed |

Canonical answer：`process/context/CR164-CP2-SGQ-BATCH.yaml`。该回答不是 CP2 formal gate approval。

### CR164 Compatibility Boundary

- `UC-58` 是当前候选实现主体。
- `UC-59` ML 与 `UC-60` event 只要求消费同一证据 availability/ref/blocked 语义；未提供相同 sealed-family 与方法输入时必须 fail-closed。
- compatibility 不授权 real model training、event feed、provider、registry、runtime 或外部数据访问，也不要求本轮实现新的 ML/event runner。

### CR164 八维覆盖扫描

| 维度 | 状态 | CR164 覆盖 |
|---|---|---|
| 用户 | 已覆盖 | 研究负责人、研究员、准入审查者、独立验证者、维护者。 |
| 任务 | 已覆盖 | lineage/input precheck、四类方法证据、冲突投影、consumer integration。 |
| 动机 | 已覆盖 | 防止多重检验、data snooping 与 backtest overfit 被误报为 clean admission。 |
| 时间 | 已覆盖 | family sealed 后、admission projection 前；CP2/CP3/CP5 gate 顺序明确。 |
| 环境 | 已覆盖 | 本地 fixture/static；真实 data/runtime 明确不授权。 |
| 方式 | 已覆盖 | 确定性、provenance-bound、逐方法 availability 与 conservative aggregation。 |
| 异常 | 已覆盖 | 缺失、低充分性、NaN/Inf/退化、方法冲突、hash mismatch、CR155 regression。 |
| 集成 | 已覆盖 | CR151、CR154、admission package 以及 UC-59/60 compatibility。 |

## CR164 Deferred Ideas

| ID | 内容 | 状态 | 重启条件 |
|---|---|---|---|
| DF-CR164-001 | effective-trial estimator / multiplicity model | deferred-confirmed | 独立方法、偏差假设、估计上下界和 verifier 已在后续 CR 获批。 |
| DF-CR164-002 | real ML/event statistical-evidence adapters | deferred | real runners 与 runtime/data authorization 存在，且 compatibility contract 已经验证稳定。 |
| DF-CR164-003 | 真实研究批量重算与历史证据迁移 | not-authorized | 独立 data/runtime/audit gate 批准，且 provenance 不被回填伪装。 |
