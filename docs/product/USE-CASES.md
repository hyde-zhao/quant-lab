---
status: confirmed
version: "3.1"
confirmed_by: "user"
confirmed_at: "2026-07-17T16:54:09+08:00"
engagement_mode: production
scenario_subject_type: target-artifact
scenario_subject_id: "CR-172"
target_artifact_type: workflow
governance_mode: review-gated
review_policy: strict
delivery_routing:
  mode: project-readme-contract
  output_root: "docs/product"
  source: docs
total_use_cases: 14
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
| v0.9 | 2026-07-13 | host-orchestrator-inline | CR166 增量追加 fixture/static Walk-forward/OOS C2 producer foundation、八类 fail-closed、ML compatibility、event P1 适用性与 Stage 3 claim ceiling。 |
| v1.0 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 人工批准；产品范围、Stage ceiling、C3/C4 扩展约束和 event P1 适用性成为 CP3 正式输入。 |
| v1.1 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 人工批准；用户旅程映射到五个正式 Story，event 适用性确定为显式 N/A，下一门禁为 CP5。 |
| v1.2 | 2026-07-13 | host-orchestrator-inline | CR168 增量追加 C3 economic cost/slippage/impact approximation 用例、Gate 4 C3+C4 联合边界、两类 fixture、10 类 fail-closed 和 CP2 决策项；保留 CR166 及更早基线。 |
| v1.3 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见收紧 Gate 4 projection-side fail-closed：C4 not-built/unavailable 只允许 absent-no-na-reason，任何字段级或通用 na_reason 逃逸由 projection 阻断；新增 1 个 P0 场景但不扩大 C3/C4 范围。 |
| v1.4 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准，并把代码评审发现固化为 CP3 义务：CR168 仅在自身 projection 入口以 8-key denylist、strict allowlist、调用前拒绝和调用后非 PASS 断言封堵 N/A reason 逃逸；不宣称 canonical Gate 4 已全局修复。 |
| v1.5 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 C4 fixture/static use case、17 个场景的产品语义、五项 CP2 待决与严格 C3+C4 Gate 4 joint adapter 边界；保留 CR168 C3-only adapter、canonical Gate 4、aggregate 和 CR155 基线。 |
| v1.6 | 2026-07-14 | host-orchestrator-inline | CR169 CP2 评审整改与批准：明确 Stage 2 complete 不等于 Stage 3 entry-ready，新增 7/7 Stage 2 exit 核验义务，并把 FU-007 007a/007b 仅保留为后续提案。 |
| v1.7 | 2026-07-15 | host-orchestrator-inline-meta-pm | 增量追加 CR170 canonical Gate 1-5 N/A evidence semantics 与 Gate 6 admission worst-state hardening 用例；明确保留既有底层 worst-state 合并、单独审查 `resolve_admission_policy`，并保留 Stage 3、aggregate 与真实数据边界。 |
| v1.8 | 2026-07-15 | host-orchestrator-inline-meta-pm | 根据 CP2 评审明确“独立验证者”为 `future consumer`：CR170 只建立可审计契约，当前验证由可靠性 Gate 维护者自验证代行，独立 verifier 实际消费留给 `FU-CR161-006`；补充 consumer 端到端调用期望，不增加用例、需求或场景分母。 |
| v1.9 | 2026-07-15 | meta-pm | CR171 增量追加 Stage 3 Launch / Real-Lake Entry Decision Gate 用例、三项 CP2 决策、historical-run legacy/require-revalidation ceiling 与零执行授权边界；CP8 不构成 entry-ready。 |
| v2.0 | 2026-07-16 | meta-pm（pm-wu） | CR172 增量追加 C1-first 默认 activation 场景、PATH-B 前置恢复链、C2/C3 独立后续 CR、effective-trial 双 owner 联合审批和 8 项 CP2 待决；保留 CR171 关闭基线且不授权真实数据。 |
| v2.1 | 2026-07-16 | meta-pm（pm-wu） | 根据 CP2 业务视角评审增量补齐 UC-58-CR172 的业务动机、用户痛点、使用价值与旅程第 0 步；将业务价值设为主锚点、activation 治理设为实现约束，并记录 `SGQ-CR172-002`，不改变 8 项需求/DQ 或授权边界。 |
| v2.2 | 2026-07-16 | meta-pm（pm-wu） | 根据 CP2 最终评审补充“策略 X”占位契约：当前仅为业务示例，PATH-B 与具体策略无关；未来 activation CP3 冻结 `strategy_id + strategy_name`，CP6 C1 evidence 锚定同一身份并对缺失/不一致 fail-closed；新增 `SGQ-CR172-003`，不增加需求、场景或 DQ。 |
| v2.3 | 2026-07-16 | meta-pm（pm-zheng） | 增量追加 CR173 strategy-agnostic offline effective-trial methodology 用例：明确 raw count 虚假独立性、typed-unavailable 痛点、七字段证据、六类失败/恢复边界与 CR172 PATH-B 前置关系；保留全部旧基线。 |
| v2.4 | 2026-07-16 | host-orchestrator | 回填 CR173 CP2 批准；将方法不可识别时转 Spike、projection 触及跨域公共 C1 contract 时拆分为后续 CR，固化为 CP3 强制设计义务。 |
| v2.5 | 2026-07-16 | meta-pm（pm-zheng） | 解析 CP2 已批准的条件分支：依据 `DO-CR173-CP3-001=PASS` 与 `DO-CR173-CP3-002=PASS_BY_SPLIT`，将 CR173 收缩为 participation-ratio estimator-only 和独立七字段证据；public C1 projection/write 固定为 `0`，后续 versioned projection 仅进 backlog 候选。 |
| v2.6 | 2026-07-16 | host-orchestrator | 修正 CR173 当前门禁与关联 CR 状态：CP2 基线已批准、CP3 待人工审查；补入 CR172/CR173 追溯，不改变 estimator-only 范围、8 项需求或授权边界。 |
| v2.7 | 2026-07-17 | meta-pm（pm-wu） | CR172 scope-delta 前轮草案：在已批准 PATH-B 历史上加入 PATH-I instrumentation-first、trial-return source/storage、stable logical URI、分动作授权、四组件部署、新运行路径与 empirical-R fail-closed；部署、授权与待决集合已由 v2.9 correction R1 全量替换。 |
| v2.8 | 2026-07-17 | host-orchestrator | CP2 发起前一致性修正：将 CR173 前置条件从旧 CP3/CP5 待办同步为已 closed/cp8_closed 的 offline-methodology 历史；其前轮 CR172 计数已由 v2.9 correction R1 替换。 |
| v2.9 | 2026-07-17 | meta-pm（pm-wu） | correction R1 冻结单一部署主权：研究机本地 active canonical → NAS verified replica/backup/distribution → 执行机 pull+verify+local immutable cache；新增 DQ/REQ-015，默认执行机本地生成信号，低频/EOD 可选 immutable mailbox，intraday 独立 CR。 |
| v3.0 | 2026-07-17 | meta-pm（pm-wu） | correction R2 将 DQ/REQ-015 收缩为信号边界与精确 8 字段最小 batch contract，详细 exchange/replay/ack/path 实现转 deferred；强化 DQ/REQ-014 的 `FU-CR173-001` 条件前置与三选一；补齐 CP2/3/5/7/8 阶段守卫。 |
| v3.1 | 2026-07-17 | meta-pm（pm-wu） | 回填 CR172 PATH-I scope-delta CP2 于 `2026-07-17T16:54:09+08:00` 获用户批准；仅更新 DQ/REQ-009~015、SGA/SGQ 与门禁状态，不改变推荐值、边界、场景或授权。 |

## 状态

- 文档状态：confirmed-CP2（CR172 PATH-I scope delta；CR173 estimator-only 历史基线继续保留）
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168` / `CR-169` / `CR-170` / `CR-171` / `CR-172` / `CR-173`
- 当前门禁：CR172 PATH-I scope-delta CP2 已于 `2026-07-17T16:54:09+08:00` 获用户批准，当前只解锁 CP3 design-only；该批准不授权实现、真实数据、multi-trial、NAS 写入/同步、信号传输、迁移或 empirical-R computation。
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

## UC-58-CR166 Walk-forward / OOS Evidence Producer Foundation

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR166 |
| 名称 | Fixture/static Walk-forward / OOS typed C2 evidence producer foundation |
| 主要用户 | 量化研究负责人、策略研究员、准入审查者、独立验证者、框架维护者 |
| 触发条件 | CR161 已定义 `WalkForwardEvidence` availability，现有 statistical gate 能消费 pass rate，但仓库尚无通用 fold-level producer、时间/泄漏边界校验与 lineage-bound C2 evidence。 |
| 输入 | 显式提供的 fold manifest、split policy、train/validation/OOS 时间边界、purge/embargo、fold metrics、lineage refs 与 fixture authorization metadata。 |
| 处理逻辑 | 先校验完整性、时间顺序、purge/embargo、有限值、lineage 与 external-ref 权限；再确定性汇总 fold-level 原因和 OOS 指标，生成 typed C2 evidence 并保守投影到既有三个 consumers。 |
| 输出 / 结果 | C2 evidence header、versioned component、fold-level reason codes、provenance refs、canonical hash、availability 与 consumer projection；未知扩展不得产生 PASS。 |
| 当前范围 | daily multifactor P0、ML purged-embargo compatibility P0；event 仅 P1 适用性审查。 |
| 明确不在范围 | 真实 lake/fold/OOS 数据、真实研究运行、C3/C4 计算、event-specific producer、runtime resolver 深度集成、交易/发布/部署。 |
| Stage 语义 | Stage 2 继续保持 complete；CR166 只是 Stage 2→Stage 3 桥接增强，Stage 3 未启动、真实 OOS evidence 未声明可用。 |

### CR166 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 提交可审计 fold 输入 | 校验 manifest、policy、fold 数、时间边界与 lineage refs。 | 所有必需字段齐备且 refs 一致；缺失或冲突 fail-closed。 |
| 2 | 防止 look-ahead 与 label overlap | 校验 train→validation→OOS 顺序以及 purge/embargo 下限。 | 时间逆序、purge 缺失、embargo 不足 3/3 被阻断。 |
| 3 | 形成 fold-level OOS 证据 | 校验 metric 有限性并确定性汇总 pass rate、退化与 reason codes。 | 相同规范化输入 10 次只产生 1 个 canonical hash。 |
| 4 | 复用既有准入 consumers | 投影至 statistical gate、cross-strategy reliability gate 与 StrategyAdmissionPackage。 | consumer projection 3/3，原 blocked/typed_unavailable 状态不被提升。 |
| 5 | 保持未来扩展和权限边界 | 允许注册 versioned C3/C4 components，但不计算；external/real-data ref 只作为未授权引用被拒绝。 | C3/C4 实现数 0；外部解引用与禁止操作计数均为 0。 |

### CR166 Scenario Gray Areas 与确认记录

| SGQ | 问题 | 推荐与用户确认 | 状态 |
|---|---|---|---|
| SGQ-CR166-001 | C2 是 Stage 2 完成项还是 Stage 3 桥接？ | Stage 2 已完成；C2 是 fixture/static 桥接增强，不构成 Stage 3 启动。 | confirmed-by-review |
| SGQ-CR166-002 | event fixture 是否为 P0？ | daily + ML 为 P0；event 降为 P1/CP3 applicability，语义未冻结时 N/A。 | confirmed-by-review |
| SGQ-CR166-003 | C3/C4 是否纳入实现？ | 不纳入；C2 envelope 必须预留 versioned typed component 扩展点。 | confirmed-by-review |
| SGQ-CR166-004 | 未授权 ref 与 deterministic hash 是否可降级？ | foundation 的零解引用和确定性属于 P0；深度 runtime resolver 与 event-specific semantics 可保持 P1。 | confirmed-by-scope-review |

讨论证据：`process/discussions/CP2-CR166-SCENARIO-DISCUSSION-LOG.md`；正式整体范围与架构分别由 CP2、CP3 于 2026-07-13 批准，当前作为 CP4/CP5 Story 与设计证据输入。

## UC-58-CR168 Economic Cost / Slippage / Impact Computable Evidence Producer Foundation

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR168 |
| 名称 | Fixture/static C3 economic cost/slippage/impact approximation typed evidence producer foundation |
| 主要用户 | 量化研究负责人、策略研究员、准入审查者、独立验证者、框架维护者 |
| 触发条件 | CR166 已交付 neutral strategy evidence envelope，`economic_cost@reserved` 可演进；现有 Gate 4 需要成本/impact 与容量/流动性联合证据，但仓库尚无通用 C3 producer。 |
| 输入 | 显式提供的 9 个字段族：身份；gross/pre-cost basis；trade/position-change/turnover/notional；fee；tax/levy；spread/slippage；impact model + `cost_underestimation_status`/limitations；unit/currency/calendar/price/notional basis；lineage/provenance/authorization refs。 |
| 处理逻辑 | 只用合成或静态参数做透明成本分项、total cost、gross-to-net reconciliation 与 impact approximation；先校验充分性、有限值、算术、跨字段 basis、权限和 canonical identity，再输出 typed C3 component。 |
| 输出 / 结果 | `economic_cost` active versioned component、availability/outcome、reason codes、lineage、成本分项、total cost、net reconciliation、impact approximation、`cost_underestimation_status`、canonical hash。 |
| Gate 4 边界 | Gate 4 是 C3+C4 联合门禁。CR168 只投影 C3 的 `impact_model_family`、`impact_model_ref`、`cost_underestimation_status`、`no_real_tca_claim`；C4 `reserved/not-built/typed_unavailable` 必须翻译为三个 C4 refs absent，且不得输出字段级 `*_na_reason` / `*_n_a_reason` 或通用 `na_reason` / `n_a_reason`。CR168 的 adapter 必须用精确 8-key denylist 与 strict allowlist 在调用前拒绝 reason 逃逸，并以调用后断言保证 C4 unavailable 时 Gate 4 不为 PASS；本 CR 不修改、也不宣称全局修复 canonical Gate 4。 |
| 当前范围 | daily multifactor synthetic fixture 1 族；daily multifactor + ML 的 multi-strategy-type compatibility fixture 1 族；C3-to-Gate-4 compatibility projection 1 条。 |
| 明确不在范围 | 真实数据、真实成交/盘口/ADV、真实 TCA、market-impact calibration、C4 calculator、event-specific producer、C1-C4 aggregate integration、runtime/trading/publish/remote write。 |
| Stage / claim ceiling | Stage 2 保持 complete；Stage 3 不启动；在实际 CP7/CP8 完成前 `c3_fixture_static_foundation=false`；真实 TCA、真实 impact calibration、真实数据、runtime、C4、event producer、CR155 promotion 均为 false/0。 |

### CR168 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 提交可审计的静态成本输入 | 校验 9/9 字段族的 required/optional/N/A/authorization 规则。 | 缺 gross basis、交易/turnover/notional basis、model/version 或 lineage 时 fail-closed。 |
| 2 | 得到透明的 gross-to-net 解释 | 分项计算 fee、tax/levy、spread/slippage、impact approximation 并核对 total/net。 | 分项、total 与 gross-to-net 算术可重算；不允许非有限值或不可能负成本。 |
| 3 | 防止单位和假设混用 | 校验 unit、currency、price/notional basis、calendar 与显式转换声明。 | 跨字段混用且无转换声明时 100% blocked；同一一致 basis 不误报。 |
| 4 | 复用 CR166 envelope | 注册 1 个 active `economic_cost` schema version，并生成 canonical identity。 | 同一规范化输入运行 10 次只得到 1 个 hash；tamper 被阻断；平行 envelope/registry/gate 数为 0。 |
| 5 | 保守适配 Gate 4 | 只填 C3 字段；把 C4 not-built/unavailable 映射为三个 refs absent 且不输出任何字段级或通用 na-reason。 | reason 逃逸输入由 projection 阻断；Gate 4 不产生 capacity-scalable 或 aggregate PASS；C4 calculator 数为 0。 |
| 6 | 证明跨策略类型语义一致 | 将相同 C3 算术合同 attach 到 daily multifactor 与 ML package fixture。 | 2/2 fixture 族使用相同 cost 语义；不训练模型、不访问 event feed。 |
| 7 | 保持授权和回归边界 | 检查禁止操作计数、claim ceiling 与 CR155 admission 状态。 | 禁止操作计数全为 0；CR155 `admission_package_status=BLOCKED`、`paper_candidate=false`，提升数为 0。 |

### CR168 Scenario Gray Areas 与确认记录

| SGQ | 问题 | 推荐方案 | 当前状态 | 决策引用 |
|---|---|---|---|---|
| SGQ-CR168-000 | 是否按评审修正启动 CR168？ | 修正 Gate 4 联合门禁、成本低估状态、multi-strategy fixture 和跨字段一致性条件后启动。 | RESOLVED；用户要求按提示词启动并继续推进 | `process/REQUEST.md` / `CR-168` |
| SGQ-CR168-001 | C3 是否包含透明 impact approximation？ | 包含，但只能使用显式静态参数；备选为延后 impact。 | RESOLVED-APPROVED，2026-07-14 | DQ-CP2-CR168-METHOD |
| SGQ-CR168-002 | C3/C4 是否冻结最小共享 header？ | 冻结最小共享 header，C4 专属字段 reserved，C4 calculator=0。 | RESOLVED-APPROVED，2026-07-14 | DQ-CP2-CR168-C3-C4 |
| SGQ-CR168-003 | existing-gate integration 粒度？ | 只做 1 条 C3-to-Gate-4 compatibility projection；C4 reserved/not-built/typed_unavailable 映射为 refs absent-no-na-reason；CR168 adapter 以 8-key denylist、strict allowlist、调用前拒绝和调用后非 PASS 断言局部封堵 reason 逃逸，不修改或全局修复 canonical Gate 4。 | RESOLVED-APPROVED，2026-07-14 | DQ-CP2-CR168-GATE4 |
| SGQ-CR168-004 | fixture 适用面？ | daily multifactor synthetic + daily/ML multi-strategy-type compatibility 两族；event N/A/deferred。 | RESOLVED-APPROVED，2026-07-14 | DQ-CP2-CR168-FIXTURE |
| SGQ-CR168-005 | claim ceiling？ | Stage2 complete、Stage3 not-started；真实 TCA/impact calibration/data/runtime/C4/event/CR155 promotion 均为 false/0。 | RESOLVED-APPROVED，2026-07-14 | DQ-CP2-CR168-CLAIM |

用户于 2026-07-13 对 `DQ-CP2-CR168-GATE4` 提出 `修改:`：上述 projection-side guard 与 `SC-CR168-B02` 已进入修订基线；该输入不是 CP2 批准，其余四项 DQ 仍与修订后的 Gate 4 DQ 一并等待统一 `approve`。

用户于 2026-07-14 要求“按照建议完成整改，整改后批准，并推进到下一个人工门禁”，视为批准修订后的五项 CP2 推荐方案。该批准只解锁 CP3；评审所揭示的 canonical Gate 4 宽松 N/A 语义被记录为局部 containment 的设计依据，而不是 CR168 的全局整改授权。

### CR168 Deferred Ideas

| ID | 内容 | 状态 | 重启条件 |
|---|---|---|---|
| FU-CR161-005 | C4 capacity/liquidity/ADV/alpha-decay producer | candidate | 独立 CR 冻结 C4 方法、输入与授权；不得由 CR168 隐式启动。 |
| FU-CR161-007 | C1-C4 aggregate orchestration、existing-gate 全链路集成、canonical Gate 4 availability/N/A 语义复核与 CR155 综合 regression/promotion decision | candidate | C1-C4 typed producers 全部稳定且获得独立授权；在增加任何绕过 CR168 adapter 的直接调用前，必须决定是否全局硬化 canonical Gate 4。 |
| DF-CR168-REAL-TCA | 真实 TCA / market-impact calibration / real-data parameter estimation | not-authorized | 独立数据、方法、权限、审计和 runtime gate 全部批准。 |
| DF-CR168-EVENT | event-specific economic-cost semantics and producer | deferred | event-time、交易日历、窗口和执行语义由独立 CR 冻结。 |

## UC-58-CR169 C4 Capacity / Liquidity / ADV Evidence Producer Foundation

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR169 |
| 名称 | Fixture/static C4 capacity / liquidity / ADV typed evidence producer foundation |
| 主要用户 | 量化研究负责人、策略研究员、准入审查者、验证者、框架维护者 |
| 触发条件 | CR-168 已交付 C3 `economic_cost@v1` 与 C3-only fail-closed adapter；Gate 4 同时需要 C4 capacity/liquidity refs，但当前 C4 仍为 reserved/typed unavailable。 |
| 输入 | 仅显式 synthetic/static 的 strategy/run/manifest identity、synthetic ADV/reference basis、participation cap/method、capacity curve/ref、liquidity sizing/ref、unit/currency/calendar/as-of/horizon、lineage/provenance/authorization 与 no-real-ADV limitations。 |
| 处理逻辑 | 先验证 C4 计算输入充分性、数值域、关联头、单位和授权边界；再确定性输出容量/流动性/ADV proxy。C3/C4 计算体独立，关联头只校验可组合性。 |
| 输出 / 结果 | `capacity_liquidity@v1`、availability/outcome、machine reason、三个 Gate 4 C4 refs、lineage、limitations 与 canonical hash；真实 ADV/liquidity/capacity 一律不宣称可用。 |
| Gate 4 边界 | 不修改 CR-168 C3-only adapter；新增独立 strict C3+C4 fixture compatibility adapter，只消费已验证 C3+C4 components，重建精确七字段 payload，并拒绝 reason escape、任意 flat mapping、身份/限制不一致和意外 PASS。canonical Gate 4 与 aggregate orchestration 不修改。 |
| 当前范围 | daily multifactor synthetic fixture 与 daily/ML multi-strategy-type compatibility fixture 共 2 族；C4 component=1、schema=1、strict joint fixture adapter=1。 |
| 明确不在范围 | 真实 ADV/liquidity/order/book/flow 数据、真实 capacity calibration、alpha-decay calculator（CP3 决定归属）、canonical Gate 4/global hardening、aggregate integration、Stage 3、runtime/trading/publish/remote write。 |
| Stage / claim ceiling | Stage 2 保持 complete，但 `stage3_entry_ready=false`、Stage 3 不启动；CP8 / formal Stage 2 exit 前必须以 `STAGE2-EXIT-VERIFICATION.result.json` 核验 7/7 合同。实际 CP7/CP8 前 `c4_fixture_static_foundation=false`、`gate4_fixture_contract_pass=false`；`aggregate_admission_pass=false`、`cr155_promoted=false`。 |

### CR169 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 提供受限的 static C4 输入 | 验证 synthetic ADV/reference basis、participation、capacity/liquidity 方法及关联头。 | 任何缺失、非有限、不可行、跨字段不一致或未经授权输入均 fail-closed。 |
| 2 | 取得可审计 C4 fixture component | 按显式 static 参数计算 proxy，记录 availability、reason、limitation、lineage 与 hash。 | 1 个 component / 1 个 active schema；同一规范化输入 10 次→1 hash。 |
| 3 | 让 C3/C4 安全组合进 Gate 4 | strict joint adapter 对 type/version/identity/limitation 验证后产生精确七字段 payload。 | 3/3 C4 refs present 时仅证明 `gate4_fixture_contract_pass`；不产生 aggregate/real-capacity PASS。 |
| 4 | 保持 CR168 回归安全 | C3-only adapter 持续将 C4 unavailable fail-closed。 | C3-only adapter 行为修改数=0；absent-C4 回归=1。 |
| 5 | 控制真实能力与晋级声明 | 审查 no-real-data limitation、forbidden counters 和 CR155 package。 | real-data/runtime/trading=0；CR155 仍 BLOCKED 且 `paper_candidate=false`。 |

### CR169 Scenario Gray Areas 与确认记录

| SGQ | 问题 | 推荐方案 | 当前状态 | 决策引用 |
|---|---|---|---|---|
| SGQ-CR169-001 | C4 fixture 方法与保守假设？ | 显式 synthetic/static ADV、participation cap、capacity curve、liquidity sizing，真实校准延后。 | OPEN-CP2 | DQ-CP2-CR169-C4-METHOD |
| SGQ-CR169-002 | C3/C4 共享边界？ | 冻结最小 correlation header；计算 body 与 component semantic hash 域独立。 | OPEN-CP2 | DQ-CP2-CR169-CORRELATION-HEADER |
| SGQ-CR169-003 | Gate 4 组合路径归谁？ | 新增 strict joint fixture adapter；CR168 adapter/canonical/aggregate 不变。 | OPEN-CP2 | DQ-CP2-CR169-GATE4-COMPOSITION-OWNER |
| SGQ-CR169-004 | alpha-decay 是否归 C4？ | CP3 由 meta-se 决定 C4、C2 或独立 CR；本 CR 默认不实现。 | OPEN-CP2 | DQ-CP2-CR169-ALPHA-DECAY |
| SGQ-CR169-005 | FU-006 verifier 是否前置？ | 不阻塞 foundation；未完成时 CP8 最多 READY_WITH_RISK。 | OPEN-CP2 | DQ-CP2-CR169-VERIFIER |

### CR169 Deferred / Adjacent Items

| ID | 内容 | 状态 | 重启 / 归属 |
|---|---|---|---|
| FU-CR161-005 | C4 fixture/static capacity/liquidity/ADV foundation | active (`CR-169`) | 当前 CR；CP2 前无实现。 |
| DF-CR169-ALPHA-DECAY | alpha-decay calculator 归属与方法 | deferred-pending-CP3 | CP3 决定归 C4、C2 或独立 CR 后才可规划。 |
| FU-CR161-006 | independent verifier lane | candidate | 不阻塞 CP2；若未完成，CP8 必须披露 verifier-independence 风险。 |
| FU-CR161-007 | canonical Gate 4 global N/A hardening、C1-C4 aggregate orchestration 与 CR155 promotion decision | candidate；可评估 007a/007b 拆分 | 007a（canonical N/A 语义硬化）与 007b（aggregate + CR155 regression）只是后续提案；各自必须先有独立 CR/CP0 conflict precheck 和用户授权，当前不启动。 |
| DF-CR169-REAL-C4 | real ADV/liquidity/capacity calibration | not-authorized | Stage 3 独立数据、方法、权限与审计 CR。 |

## UC-58-CR170 Canonical Cross-Strategy Reliability N/A Semantics and Admission Hardening

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR170 |
| 名称 | Canonical Gate 1-5 N/A evidence semantics 与 Gate 6 admission worst-state hardening |
| 主要用户 | 量化研究负责人、准入策略维护者、可靠性 Gate 维护者；独立验证者为 `future consumer`，实际 verifier lane 待 `FU-CR161-006` |
| 目标 | 使 mandatory evidence 的 missing、通用 reason 逃逸、边界不完整或 `NEEDS_REVIEW` 状态均不能在 canonical Gate / Gate 6 中产生无条件 PASS，同时保留合法结构化 N/A 的可审计边界。 |
| 当前 CR 范围 | 对 Gate 1-5 的 N/A evidence 业务语义做统一 inventory 与 fail-closed 处理；验证并保留现有底层 worst-state merge；在 `resolve_admission_policy` 边界落实 T0/T1/T2/T3 分层结果；回归 CR168/CR169 adapter。 |
| 明确不在范围 | 当前 Stage 3 runner 集成、真实数据/lake/provider/NAS、aggregate orchestration、FU-007b、CR155 promotion、runtime/broker/QMT/trading、canonical adapter 删除或简化。 |

### CR170 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 识别全部 canonical N/A 判定面 | 形成 Gate 1-5 共 21 个 policy units 的适用性、mandatory/conditional owner 与边界清单。 | inventory `21/21`，每项均有 Gate、字段族、适用条件、owner 和结果规则。 |
| 2 | 防止 reason 文本冒充 evidence | 将 PRESENT、MISSING、NA_WITH_COMPLETE_BOUNDARY、NA_WITH_INCOMPLETE_BOUNDARY、GENERIC_REASON_ESCAPE 作为业务语义输入。 | mandatory missing/generic/incomplete 的无条件 PASS 数为 `0`。 |
| 3 | 保护已经正确的聚合语义 | 先证明 `build_shared_gate_summary` 的现有 worst-state merge 可传播 `NEEDS_REVIEW`，只有失败证据才允许修改。 | 既有传播回归 `1/1 PASS`；无失败证据时修改数为 `0`。 |
| 4 | 让 admission tier 与风险强度一致 | 在 `resolve_admission_policy` 处分离 T0/T1/T2/T3 的最终判定。 | T0=`NEEDS_REVIEW` 且不得声称 PASS；T1/T2=`BLOCKED`；T3=`NOT_AUTHORIZED`。 |
| 5 | 保持相邻能力边界 | 回归 CR168/CR169 strict adapter，不把 CR170 描述成 current runner 或 aggregate 集成。 | adapter 回归 `2/2 PASS`；current runner 新增 canonical 调用 `0`；CR155 promotion `0`。 |
| 6 | 消费 canonical 判定且不越过 claim ceiling | 准入策略维护者以公开 Gate summary 调用 `resolve_admission_policy`；mandatory unresolved evidence 在 T0 只得到可诊断 `NEEDS_REVIEW`，在 T1/T2 得到 `BLOCKED`，T3 得到 `NOT_AUTHORIZED`。 | consumer 端到端 tier 结果 `4/4`；无条件 PASS=`0`；独立验证者当前可消费契约=`0`，future consumer contract=`1`。 |

### CR170 用户可用性边界

| 用户 | 本 CR 使用方式 | 当前可用性 | Claim Ceiling |
|---|---|---|---|
| 量化研究负责人 | 间接依赖 fail-closed 结论，避免把 unresolved evidence 误读为可靠性 PASS | 当前间接消费 | 不代表真实数据研究或 Stage 3 ready |
| 准入策略维护者 | 调用公开 Gate validator / `resolve_admission_policy`，消费分层 admission 结果 | 当前直接消费 | 只覆盖 canonical contract，不含 aggregate SAP |
| 可靠性 Gate 维护者 | 维护 21-unit inventory、五态判定、三层断言和回归 fixture | 当前验证主体 | 本 CR 的验证证据由该角色自验证产生 |
| 独立验证者 | 审计 owner/boundary/claim limit 与三层断言 | `future consumer` | CR170 只准备契约；独立 verifier lane 实现与实际使用留给 `FU-CR161-006`，不得声明 verifier independence 已交付 |

### CR170 Scenario Gray Areas 与启动确认

| 灰区 ID | 推荐方案 | 备选方案 | 切换条件 | 当前状态 |
|---|---|---|---|---|
| SGQ-CR170-001 | 一次覆盖 Gate 1-5 N/A semantics，并验证 Gate 6 admission policy。 | 只修 Gate 4。 | 仅当 inventory 证明其他 Gate 不存在 mandatory reason escape 时才可缩小。 | recommended-awaiting-CP2 |
| SGQ-CR170-002 | 五态先作为业务语义冻结，代码形态留 CP3。 | CP2 直接冻结 enum/dataclass。 | 仅当现有公共 schema 已要求固定代码类型时提前冻结。 | recommended-awaiting-CP2 |
| SGQ-CR170-003 | T0 `NEEDS_REVIEW` 仅允许诊断且不得声称 PASS；T1/T2 BLOCKED；T3 NOT_AUTHORIZED。 | 所有 tier 一律 BLOCKED。 | 若 CP3 证明 exploratory 诊断也会被下游误用为 admission 时切换。 | recommended-awaiting-CP2 |
| SGQ-CR170-004 | 保留现有底层 worst-state merge；只在失败证据下修改；单独硬化 `resolve_admission_policy`。 | 重写 Gate 6 聚合。 | 仅当回归证明现有 merge 无法传播上游 `NEEDS_REVIEW` 时切换。 | recommended-awaiting-CP2 |
| SGQ-CR170-005 | CR168/CR169 adapter 作为 defense-in-depth 保留，简化留给 FU-CR161-009。 | CR170 同时删除局部 guard。 | 只有全部 caller 经新 contract、删除不降 fail-closed、全回归通过且 ADR 获批时切换。 | recommended-awaiting-CP2 |

用户已审查 UC-58，并在明确“独立验证者是 future consumer、consumer 调用视角需补强”的前提下批准 CR170 CP2 五项推荐方案。该批准只解锁 CP3 solution-design，不授权 Story、LLD、实现、验证或任何真实/远端操作。

### CR170 Deferred / Adjacent Items

- `FU-CR161-009`（原 FU-007b）保留 aggregate orchestration、mature StrategyAdmissionPackage 聚合与 CR155 综合 regression/promotion 决策。
- Stage 3 Launch 必须另建 CR，处理 scoped research-data authorization、data release/PIT/lineage、历史 Stage 3 记录 revalidation、路线与 verifier 决策。
- 当前 Stage 3 runner 未调用 canonical Gate 1-6；CR170 不虚构现有运行依赖，也不负责接入。
## UC-58-CR171 Stage 3 Launch / Real-Lake Entry Decision Gate

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR171 |
| 主要用户 | 量化研究负责人、策略研究员、验证负责人、风险/发布审批人 |
| 触发条件 | 用户已授权创建 CR171，但尚未批准任何真实数据湖读取、真实 computation、runtime、provider、凭据、写入、publish 或 trading。 |
| 目标 | 在不执行任何真实数据或运行时操作的前提下，决定未来 Stage 3 的证据路线、FU-006 verifier 处置及 deny-default 的冻结 read scope，并把历史 Stage 3 事实限制为 legacy / require-revalidation。 |
| 当前 CR 范围 | 产品基线、CP2 决策包、历史叙事标注、候选 readiness inventory 语义和风险别名消费；不产出实现、Story、LLD 或真实读取结果。 |
| 明确不在范围 | C1-C4 producer binding 或 real computation、aggregate orchestration、repair/backfill/rerun、provider/NAS/lake 操作、凭据、catalog/current pointer、runtime/trading、CR010/018/032 修复或关闭。 |
| 成功标准 | CP2 必须分别决定 1 条证据路线、1 条 verifier 处置和 1 个冻结 read scope；三个决策均未确认前 `stage3_started=false`、`stage3_entry_ready=false`、`real_data_read_authorized=false`、`real_computation_authorized=false`。 |

### CR171 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 选择可审计的 Stage 3 证据路线 | 呈现 current runner 与 C1-C4 real-producer 路线的后续 CR 数、边界和残余风险。 | 只记录 CP2 候选，不开始 producer、aggregate 或 computation。 |
| 2 | 决定 verifier 是否可短期豁免 | 呈现 FU-006 first 与 event-bounded waiver，并把 waiver 失效点设为机械可判断事件。 | waiver 不继承 CR170 历史风险接受；在任一失效点前不能输出 real-evidence admission PASS/PASS_WITH_RISK 或启动 Stage 3 exit gate。 |
| 3 | 限定未来可能的研究数据读取 | 仅定义待 CP2 决定的 release/dataset/date/identity/output 五元组及 deny-default 清单。 | 此基线本身不读取任何真实数据、凭据或环境，也不授权 runner。 |
| 4 | 处理历史事实而不夸大 | 将历史运行标为 legacy / require-revalidation，未来 revalidation 只能分类、标注和报告。 | current-entry verdict 只允许 `revalidated_for_current_entry`、`insufficient_for_current_entry`、`incompatible_rework_required`；`reaffirmed_as_legacy_only` 仅是 annotation；发现缺陷必须另立 CR。 |

### CR171 Scenario Gray Areas 与 CP2 候选

| ID | 问题 | 推荐 | 备选 | 状态 |
|---|---|---|---|---|
| SGQ-CR171-001 / CP2-CR171-DQ-ROUTE | 选择 current runner 还是 C1-C4 real-producer 作为 Stage 3 证据路线？ | C1-C4 real-producer；随后必须另立 Real-Evidence Activation CR 才可授权 computation。 | current runner；CP3 必须先冻结其完整 read-only execution boundary。 | pending host CP2 relay |
| SGQ-CR171-002 / CP2-CR171-DQ-VERIFIER | FU-006 是否阻断 entry？ | event-bounded waiver；仅在两个机械失效点前有效。 | FU-006 first；entry 形成 3 个正式 CR。 | pending host CP2 relay |
| SGQ-CR171-003 / CP2-CR171-DQ-READ-SCOPE | 哪个 frozen release/dataset/date/read identity/output directory 可以在后续受控读取中使用？ | scoped research-data-lake read-only，且 credentials/provider/write/catalog/runtime/trading 全部 deny。 | 不批准 read scope，保持 Stage 3 未启动。 | resolved-approved 2026-07-15; no read authorization |

CP2 已确认 C1-C4 real-producer、event-bounded waiver 与 deny-default scope；该决定只定义后续 CR 的授权前提，不授予当前数据读取或 computation。

## UC-58-CR172 Stage 3 Real-Evidence Activation Phase A — C1-First Default

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-58-CR172 |
| 主要用户 | 量化研究负责人、策略研究员、strategy-admission 方法学 owner、数据授权 owner、独立验证负责人 |
| 业务动机 | 量化研究负责人需要用真实数据判断待评估策略在 multiple-testing / data-snooping / overfit 风险下是否可靠；fixture/static evidence 和当前 `effective_trial_count=typed_unavailable` 只能证明契约与流程，不能支撑成熟策略准入判断。 |
| 用户痛点 | 合成 fixture 可以验证 schema、PIT/lineage、fail-closed 和流程连通性，但不能作为待评估策略的真实 multiple-testing / overfit 评估或成熟准入依据；缺少 real typed evidence 时，研究员无法区分“流程可用”和“策略证据可靠”。 |
| 触发条件 | 量化研究负责人提出“策略 X 需要真实数据证据，以评估 multiple-testing / overfit 风险”的业务请求，其中“策略 X”只是 CP2 业务示例占位符，不代表当前已批准或已冻结的真实策略身份；同时 CR171 已以 design-only decision gate 关闭并选择 C1-C4 real-producer 路线，但真实 producer binding、五字段有限授权和 computation 尚未获批。 |
| 输入 | 已批准的 PATH-B / CR173 方法学历史，以及 CP2 已确认的 trial-return producer、family/run/trial identity、稳定 logical URI、NAS archive mapping、四组件 ownership、分动作授权与 empirical-R provenance；未来 activation 仍需冻结 `data_release`、`datasets`、`date_range`、`read_identity`、`output_directory` 五字段。 |
| 处理逻辑 | 在 PATH-C/A 之前新增 PATH-I：先冻结 trial-return 与 empirical-R 产品合同、research-local active canonical、NAS versioned/hash-verified replica、execution-local materialization、stable logical URI、四组件数据主权和逐动作授权。PATH-I 只允许设计冻结与 repository-local code/test/fixture；真实湖读取、multi-trial runtime、trial-return 生成、empirical-R 计算、NAS sync 与执行机 pull/materialize 六类动作始终保持未授权。 |
| 输出 / 结果 | 一份可审计的 instrumentation-first 产品基线：新 artifact identity 不依赖主机挂载路径；新单次运行默认路径不再使用 stage-based 名称；PATH-I 完成后仍保持 activation blocked，必须经 fresh precheck 和独立 runtime-high-risk 门禁才能重新选择 PATH-C/A。 |
| 使用价值 | 未来 C1 real typed evidence 可供策略研究员对策略 X 做真实 multiple-testing / overfit 评估，并为后续 mature StrategyAdmissionPackage 提供证据基础；该产出本身不构成 admission `PASS/PASS_WITH_RISK`、Stage 3 entry-ready 或 aggregate 完成。 |
| 策略占位契约 | “策略 X”只表示待未来 activation CP3 具化的策略对象；当前 CP2 不批准、不推断、不隐式继承任何真实 `strategy_id` 或 `strategy_name`。 |
| PATH-B 策略身份边界 | PATH-B offline estimator 是策略无关的方法学前置，不要求提供具体策略身份，也不得从 estimator 输入、历史 manifest、目录、run 或其他上下文推断策略身份。 |
| PATH-I instrumentation 边界 | PATH-I 定义并验证 fixture/static 合同，不把当前不存在的 multi-trial runner、trial-return series 或 empirical-R producer 写成既有能力；CP2 只解锁 CP3，CP3 只冻结设计，CP5 仅允许 repository-local code/test/fixture，CP7 必须验证六类真实动作 `0/6`，CP8 最高只可声明 `path_i_design_ready=true`。 |
| Trial-return identity | canonical identity 为 `research://experiment-families/{family_id}/runs/{run_id}/trials/{trial_id}/returns/v1/portfolio_returns.parquet` 加内容 hash；`${RESEARCH_ARCHIVE_ROOT}/...` 只负责物理映射，绝对挂载路径不得进入 lineage identity。 |
| 四组件部署边界 | 研究机本地 data lake、实验/回测报告与 trial returns 是实际运行目录及 active canonical；NAS 只承载 versioned/hash-verified replica、backup 与 distribution；执行机从 NAS 拉取后校验 release/manifest/hash，再原子物化为本地 immutable cache，runtime 不直读 NAS；GitHub 仅保存 metadata ceiling 内对象。 |
| 信号传递边界 | 默认不从研究机向执行机传信号；执行机基于批准策略包与本地行情生成信号。PATH-I/CP3 只冻结低频/EOD 可选 immutable `SignalBatch/TargetPositionBatch` 的精确 8 字段最小 contract：`schema_version`、`batch_id`、`strategy_id`、`strategy_package_hash`、`content_sha256`、`signature/key_id`、`valid_from/valid_until`、`sequence_no`。具体 mailbox 物理路径、七级状态机、ack、idempotency/replay、sync/transport/消费实现全部 deferred；intraday/低延迟传输由独立候选承接。 |
| Empirical-R 正向声明边界 | `FU-CR173-001`（Empirical dependency-matrix methodology v2 and sampling-error validation）不是重开 PATH-C/A 设计的绝对前置；DQ-003 允许 `effective_trial_count=typed_unavailable` 降级。只有要输出 available effective trial count 或声明 `c1_computable=true` 时，才必须先完成 sampling-error/uncertainty evidence、method v2 + hash、有效域/偏差界限与独立验证。 |
| 路径兼容边界 | 新运行默认写 `${QUANT_LAB_RESEARCH_RUNS_ROOT}/multifactor-strategy-research/{run_id}/`；历史 `stage3_mature_multifactor/{run_id}` 只读保留用于审计，不搬迁、不重命名、不 rewrite manifest。 |
| 未来 activation 身份冻结 | 仅当未来选择 PATH-C/A 时，activation CP3 Entry 必须同时冻结非空、无通配符、可审计的 `strategy_id + strategy_name`；缺任一字段、使用 `*`/动态别名或无法回链批准记录时不得进入 activation 设计。 |
| 未来 C1 evidence 锚定 | CP6 产出的 C1 typed evidence 必须携带与 CP3 批准完全一致的 `strategy_id + strategy_name`，并与批准的 five-field scope、run identity、PIT/lineage 同时一致；任一缺失或不一致均 fail-closed，不得产生 C1 computable 或 admission claim。 |
| 前置条件 | 原 DQ-001~008 与 PATH-B 历史继续有效；本轮 CP2 已批准新增 DQ-009~015 且只解锁 CP3。未来 PATH-C/A CP2 对 empirical positive path 必须显式三选一：完成 `FU-CR173-001`、拆为 future activation，或采用 DQ-003 typed-unavailable 降级。 |
| 排除情况 | 真实 data lake/NAS read/write/sync/publish、multi-trial runtime、trial-return generation、真实/empirical R computation、信号 sync/transport/消费、mailbox 物理路径、状态机、ack、idempotency/replay、目录迁移或历史 rewrite、C4、aggregate/FU-CR161-009、FU-006 implementation、OI-CR171-005 revalidation/audit、credential、QMT/trading、deploy/Git remote write。 |
| 成功标准 | 新增 DQ/REQ `7/7` 具备推荐、备选、影响、风险和切换/回退条件；logical URI + hash=`100%`；四组件=`4/4`；数据动作分离=`6/6`；replica stale/partial/hash mismatch、execution direct-NAS read、错误 returns、alignment、GitHub 泄漏与 empirical overclaim `100%` fail-closed；SignalBatch 最小字段=`8/8`、敏感/订单字段=`0`、详细 exchange implementation=`0`；CP7 六类真实动作=`0/6`；CP8 最高声明 `path_i_design_ready=true`，同时 `stage3_entry_ready=false`、`c1_computable=false`、`real_data_authorized=false`、`multi_trial_runtime_authorized=false`、`signal_transport_authorized=false`。 |

### CR172 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 0 | 为“策略 X”发起真实证据需求 | 量化研究负责人说明待评估策略需要真实数据证据来判断 multiple-testing / overfit 风险，并明确“策略 X”只是当前业务示例、fixture/static evidence 不能替代成熟准入证据。 | 业务问题和证据用途被明确记录；真实策略身份仍未批准，且不会因此产生任何数据读取、计算、runtime 或 admission 授权。 |
| 1 | 选择首次真实数据 activation 半径 | 比较 PATH-C、PATH-A 与 PATH-B 前置，默认推荐 C1-first；PATH-B 保持策略无关，PATH-C/A 的具体策略身份留给未来 CP3 Entry 冻结。 | 未明确接受 C1-C3 blast radius 时不会隐式选择 PATH-A；未选择 PATH-C/A 时不得要求或推断真实策略身份。 |
| 2 | 冻结有限授权 | 由 data owner 提供五字段精确有限值，禁止通配符、隐式继承或历史目录推断。 | 五字段 `5/5` 可审计；任一缺失时 activation 保持 blocked。 |
| 3 | 解耦 C1 通道与 empirical positive path | PATH-C/A CP2 显式选择：完成 `FU-CR173-001`、拆 future activation，或按 DQ-003 保持 `effective_trial_count=typed_unavailable`；方法 v2 不是降级设计路径的绝对前置。 | 未完成 v2 时 available effective count 与 `c1_computable=true` 均=`0`；typed-unavailable 路径仍可进入设计。 |
| 4 | 安排后续 producer | PATH-C 后将 C2、C3 默认分别路由到独立 runtime-high-risk CR；同 parent 顺序 slice 只作严格条件备选。 | 总 activation CR 数预计为 3，除非 CP2 明确批准备选治理。 |
| 5 | 防止联合审批越界 | owner 不同时要求两位 owner 对同一 scope revision/hash 分别写 approved ledger，权限取交集。 | partial/mismatched approval 不得合并 FU-CR164-004。 |
| 6 | 保持 Stage 3 claim ceiling | CR172 只允许 PATH-I contract-ready 证据；OI-005、C4、FU-006、aggregate 和真实动作保持独立。 | CP8 最高 `path_i_design_ready=true`；`stage3_entry_ready`、`c1_computable`、`real_data_authorized`、`multi_trial_runtime_authorized`、`signal_transport_authorized` 全为 `false`。 |
| 7 | 先定义 PATH-I instrumentation | 把 trial-return source、per-trial schema、family/run/trial alignment、empirical-R provenance 与 fail-closed 条件冻结为产品合同。 | 不把 layered forward returns、CR163 metadata/ref 或 CR173 已计算 R 输入误当作 trial-return source；错误对象/对齐失败阻断率=`100%`。 |
| 8 | 冻结长期 identity 与副本链 | 以 logical URI + content hash 识别 artifact；研究机本地 active canonical 经授权同步为 NAS verified replica。 | 主机绝对路径进入 identity=`0`；stale/partial/hash-mismatch replica 被拒绝；NAS 被声明为 runtime canonical=`0`。 |
| 9 | 分离多试验与分发动作授权 | 分别审批 data-lake read、multi-trial runtime/workspace write、trial-return generation、empirical-R computation、NAS sync、执行机 pull/materialize。 | 任一未批准动作不得被其他批准隐含；当前六类真实动作均=`0`。 |
| 10 | 落实四组件数据流 | 研究机 active canonical、NAS verified replica/distribution、GitHub metadata ceiling、执行机 approved-package + verified local cache。 | 四组件职责 `4/4`；execution direct-NAS runtime read=`0`；GitHub forbidden payload=`0`。 |
| 11 | 替换新运行路径且保留历史 | 新 run 使用 `multifactor-strategy-research/{run_id}`，旧 stage3 目录只读审计。 | 新 run 写入 legacy path=`0`；历史 move/rename/rewrite=`0`；legacy/new 默认双真相=`0`。 |
| 12 | 确定信号边界而不预做交换实现 | 默认执行机本地生成；低频/EOD 仅冻结可选 immutable batch 的精确 8 字段；详细 exchange、路径、状态机、ack、idempotency/replay 和 intraday transport 全部 deferred。 | 默认跨机信号传输=`0`；SignalBatch 最小字段=`8/8`；credential/secret/order command=`0`；exchange/ack/replay implementation=`0`。 |

### CR172 Scenario Gray Areas 与用户可见确认

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐 | 状态 |
|---|---|---|---|---|---|
| SGA-CR172-001 | 五字段可冻结时首次 activation 选 C1-first 还是 C1-C3 联合？ | 决定首次真实数据 blast radius、归因和回滚成本。 | scope / runtime authorization / validation / follow-up count | PATH-C；未显式接受三 producer 时保持 C1-first。 | approved-CP2 |
| SGA-CR172-002 | PATH-B 是 activation 替代还是前置？ | 决定 estimator 完成后是否错误宣称 Stage 3 已激活。 | scope / sequencing / claim ceiling | 前置；完成后五字段可冻结时必须恢复 PATH-C/A。 | approved-CP2 |
| SGA-CR172-003 | PATH-C 后 C2/C3 使用独立 CR 还是同 parent 顺序 slice？ | 决定 CR 总数、审批复用、证据隔离和回滚边界。 | governance / risk / delivery / maintenance | 默认两个独立 runtime-high-risk CR，总 activation CR 数为 3。 | approved-CP2 |
| SGA-CR172-004 | effective-trial 不同 owner 时如何 joint approve？ | 决定是否会用模糊自然语言扩大授权边界。 | security / methodology / audit / rollback | 同 revision/hash 双 ledger 批准，风险和权限取交集。 | approved-CP2 |
| SGA-CR172-005 | trial returns 由谁生成、何时成为可计算 R 的合格来源？ | 当前仓库没有独立 trial-return series；误用 layered returns 或 metadata/ref 会产生伪 empirical-R。 | scope / data contract / validation / claim ceiling | PATH-I 冻结 native multi-trial per-trial portfolio return contract；source 缺失或错型时 empirical-R typed-unavailable。 | approved-CP2 |
| SGA-CR172-006 | 研究机、NAS、执行机之间谁持有 active canonical？ | 错把 NAS 当 runtime canonical 会导致执行机直读共享盘、同步状态歧义和错误恢复。 | storage / deployment / recovery / maintenance | 研究机本地 active canonical；NAS verified replica/backup/distribution；执行机 verified local immutable cache。 | approved-CP2 |
| SGA-CR172-007 | multi-trial、同步与执行机 materialization 是否共享一次授权？ | 一次批准隐含 runtime、写入、同步和 pull 会扩大权限与 blast radius。 | security / runtime authorization / delivery / rollback | 六类数据动作逐项授权、逐项证据、逐项撤销。 | approved-CP2 |
| SGA-CR172-008 | 新路径如何与 stage3 历史兼容？ | 原地迁移或继续写旧目录都会制造身份漂移或历史审计破坏。 | compatibility / identity / migration / operations | 新运行切到语义路径；历史目录永久只读，迁移/重写另行授权。 | approved-CP2 |
| SGA-CR172-009 | 研究机与执行机之间是否传交易信号？ | 若在 PATH-I 提前冻结路径、ack/replay 或状态机，会把产品边界错误扩大为 exchange 实现。 | scope / runtime / security / delivery | 默认执行机本地生成；低频/EOD 只冻结精确 8 字段 immutable batch contract；详细 exchange 与 intraday 分别 deferred。 | approved-CP2 |
| SGA-CR172-010 | empirical methodology v2 是否阻断 PATH-C/A？ | 把它设成绝对前置会否定 DQ-003 typed-unavailable 降级；不设正向硬门又会产生 sampling-error overclaim。 | scope / methodology / validation / gate | 设计可在 typed-unavailable 降级下继续；available effective count 或 `c1_computable=true` 必须先完成 `FU-CR173-001`。 | approved-CP2 |

| Question ID | 问题 | 选项 / 候选理解 | 推荐方案 | 用户回答 | 复述确认 | 影响面 | 状态 |
|---|---|---|---|---|---|---|---|
| SGQ-CR172-001 | 五字段可冻结时，首次真实数据 activation 默认采用哪条路径？ | A. PATH-C C1-first；B. PATH-A C1-C3；C. PATH-B estimator 前置；D. 暂不 activation。 | A | 用户确认整改结构已最优，并明确“五字段可冻结时，倾向 PATH-C（C1-first）而非 PATH-A 作为默认”；同时要求整改后推进到下一个人工门禁。 | CR172 CP1 以 PATH-C 为默认推荐，但不把倾向伪装成最终 PATH、五字段值或风险接受；这三类事实仍由 CP2 决定。 | scope / authorization / validation / follow-up governance | confirmed-approved-CP2 |
| SGQ-CR172-002 | UC-58 是否应先说明研究负责人为何需要真实证据、fixture 的业务局限和未来 C1 evidence 的使用价值，再进入 activation 路径治理？ | A. 以业务需求为旅程第 0 步，治理作为实现约束；B. 维持 CP2 路径选择为旅程起点。 | A | 用户评审明确要求补齐业务动机、用户痛点、使用价值，并在 activation 半径选择前增加“策略 X 需要真实数据证据”的业务触发。 | UC-58 以真实 multiple-testing / overfit 评估需求为主锚点；PATH、五字段、blast radius 和 joint approval 继续约束如何安全实现，但不再代替用户价值。 | user value / journey / scope / validation / gate | confirmed-approved-CP2 |
| SGQ-CR172-003 | “策略 X”应在当前 CP2 被视为已选定真实策略，还是只作为业务示例，并把身份冻结与 evidence 锚定留给未来 activation gate？ | A. 仅作为占位；PATH-B 策略无关；PATH-C/A 在 CP3 冻结身份、CP6 锚定 evidence；B. 当前 CP2 直接指定策略身份。 | A | 用户自由文本评审要求明确“策略 X”占位契约、PATH-B 策略无关，并把未来身份冻结和 evidence 锚定分别设为 CP3/CP6 义务。 | 当前不批准或推断策略身份；未来 `strategy_id + strategy_name` 必须非空、无通配符、可审计且在 CP3/CP6 保持一致，缺失或不一致 fail-closed。 | scope / identity / traceability / validation / gate | confirmed-approved-CP2 |
| SGQ-CR172-004 | 是否把 PATH-I、research-local→NAS-replica→execution-local、stable URI、分动作授权、新路径和 empirical-R fail-closed 作为同一 CR172 scope delta？ | A. 同一 parent CR 增量确认；B. 保持旧 PATH-B；C. 直接 runtime。 | A | 用户 correction R1 明确研究机本地 active canonical、NAS verified replica/distribution、执行机 pull+verify+local immutable cache。 | 新增范围进入 DQ-009~015；真实能力和 activation 继续 blocked。 | scope / deployment / storage / authorization / validation / gate | confirmed-approved-CP2 |
| SGQ-CR172-005 | 默认是否跨机传交易信号？ | A. 执行机本地生成；低频/EOD 仅冻结 immutable 8 字段 contract；详细 exchange 与 intraday deferred；B. 所有频率经 NAS；C. 研究机直连执行机。 | A | 用户 R2 评审进一步收缩：PATH-I 不冻结 mailbox 物理路径、七级状态机、ack、idempotency/replay 或消费实现。 | 当前只保留信号边界和精确 8 字段；不授权信号生成、同步、交易或实时传输。 | signal / latency / security / reliability / gate | confirmed-approved-CP2 |
| SGQ-CR172-006 | empirical methodology v2 如何影响 PATH-C/A？ | A. 仅作为 positive empirical result 硬前置；B. 作为所有 PATH-C/A 设计的绝对前置；C. 完全不设前置。 | A | 用户明确：DQ-003 允许 typed-unavailable 降级，因此设计不被绝对阻断；但 available effective count 或 `c1_computable=true` 必须先完成 v2 sampling-error validation。 | PATH-C/A CP2 必须显式三选一：完成 `FU-CR173-001`、拆 future activation、或 DQ-003 降级。 | methodology / scope / validation / gate | confirmed-approved-CP2 |

### CR172 Deferred Ideas 与 8 维覆盖

| ID | 内容 | 延后原因 | 重启条件 |
|---|---|---|---|
| DEF-CR172-001 | C2 real-evidence activation | PATH-C 首次切片只验证 C1 模式。 | C1 CP7 通过且五字段/owner/rollback 获独立批准。 |
| DEF-CR172-002 | C3 real-evidence activation | 同上，且 C3 cost/impact 数据授权需独立审查。 | C1 模式验证完成并通过独立 runtime-high-risk CR。 |
| DEF-CR172-003 | C4 rework / authorization | CR171 判定 C4 `incompatible`，不能被 C1-C3 掩盖。 | 独立 C4 contract reconstruction CR。 |
| DEF-CR172-004 | OI-CR171-005 historical revalidation | 归独立 audit lane，不属于 activation。 | 独立审计授权与 revalidation contract 获批。 |
| FU-CR173-001 | Empirical dependency-matrix methodology v2 and sampling-error validation | CR173 已关闭；PATH-I 只登记正向 empirical claim 前置，不在 CR172 内实现。 | 要输出 available effective count 或声明 `c1_computable=true` 时，完成 sampling-error/uncertainty evidence、method v2 + hash、有效域/偏差界限与独立验证。 |
| DF-CR172-SIGNAL-BATCH-EXCHANGE | Low-frequency immutable SignalBatch/TargetPositionBatch exchange detailed design and implementation | PATH-I 只冻结 8 字段最小 contract，不冻结物理路径、状态机、ack、idempotency/replay 或真实 exchange。 | CR172 CP8 后独立评估并获得 signal sync/transport/consumer 授权。 |
| DF-CR172-INTRADAY-REALTIME-SIGNAL | Intraday realtime signal transport | 低延迟的安全、顺序、failover 与 SLO 不属于 PATH-I 四组件基础拓扑。 | 出现明确 intraday/低延迟业务需求后另行立项和门禁。 |

| 维度 | 状态 | 覆盖说明 |
|---|---|---|
| 用户 | 已覆盖 | 研究、数据授权、方法学、验证与风险审批角色均已列出。 |
| 任务 | 已覆盖 | 路径选择、五字段冻结、C1 降级、后续 C2/C3 治理和联合审批完整。 |
| 动机 | 已补充 | 主锚点是让研究负责人和策略研究员获得可用于策略 X 真实 multiple-testing / overfit 评估的 C1 typed evidence，并为 mature SAP 提供证据基础；最小 blast radius、有限授权和可审计扩展链是实现该价值的约束，不是全部用户价值。 |
| 时间 | 已覆盖 | PATH-B 恢复点、C1 CP7 后扩展、E1 触发前置均明确。 |
| 环境 | 已覆盖 | CP1/CP2 仅文档和静态审查；真实湖/runtime 均未授权。 |
| 方式 | 已覆盖 | PATH-B/C/A 决策树、双 ledger、独立 fail-closed 与有限字段合同。 |
| 异常 | 已覆盖 | 五字段缺失、partial approval、producer-local failure、越权与 claim overreach 均 fail-closed。 |
| 集成 | 已覆盖 | C1 与 FU-CR164-004、未来 C2/C3 CR、FU-006、FU-009、OI-005 边界明确。 |

## UC-CR173-EFFECTIVE-TRIAL-OFFLINE-METHODOLOGY

| 字段 | 内容 |
|---|---|
| 用例 ID | UC-CR173-EFFECTIVE-TRIAL-OFFLINE-METHODOLOGY |
| 名称 | Correlated-trial effective dimensionality — offline methodology |
| 主要用户 | 量化研究负责人、策略研究员、strategy-admission 方法学 owner、C1 evidence contract owner、独立验证负责人 |
| 业务动机 | 研究负责人需要为 multiple-testing / overfit 评估建立“相关结构的有效维度输入基础”，以区分名义试验数与二阶相关结构中实质参与的维度。直接使用 `raw_trial_count` 会把相关试验误当成相互独立。 |
| 用户痛点 | 当前 public C1 中 `effective_trial_count=typed_unavailable` 是诚实但缺少可审计的离线方法改善路径；把 raw count 直接复制到 effective 字段又会制造虚假精度并污染后续 C1 判断。 |
| 业务触发 | CR172 CP2 已批准 PATH-B，并确认 effective-trial 方法由独立 methodology CR 承接；FU-CR164-004 正式化为 CR173。 |
| 输入 | 仅仓库内 synthetic / fixture / golden-vector 的 sealed trial identity、有序 trial IDs、显式 canonical correlation matrix、方法规范和 provenance；CR173 不估计真实 correlation matrix。 |
| 处理逻辑 | 先验证 sealed identity、显式相关矩阵、方法版本/hash 和 provenance；再用 `spectral_participation_ratio` 计算二阶 effective dimensionality；最后只生成独立七字段 typed evidence 并停在 public C1 边界。结果不是 Li–Ji effective independent tests，也不是 BH/FWER/Šidák/DSR calibration；任一必要输入、方法、版本或 lineage 不合法时 fail-closed，不得回退为 raw alias。 |
| 输出 / 结果 | 可审计的 offline participation-ratio 方法合同、独立七字段 typed evidence 和确定性 golden vectors；public C1 projection/write=`0`，当前 C1 / Gate 1 / admission 继续 `typed_unavailable`，交付状态最高为 `offline_method_ready`。 |
| 使用价值 | 研究员可先审查相关结构的二阶有效维度是否可复现、可追溯且不别名 raw count；未来只有经独立 owner/迁移/回归门禁批准的 versioned public-C1 projection 才能将该基础接入 C1，本 CR 本身不产生真实策略证据。 |
| 前置条件 | CR173 已完成 CP3/CP5/CP6/CP7，并以 `closed/cp8_closed/READY_WITH_RISK` 交付 fixture-only offline methodology；该历史完成仍不提供 public C1 projection、真实数据或 CR172 activation 授权。 |
| 排除情况 | 具体 `strategy_id/strategy_name`、真实 lake/NAS/provider/credential、真实 producer 或 computation、C1 activation、C2/C3/C4、aggregate/FU-009、FU-006、OI-005、Stage 3/admission、trading、publish/deploy 和 Git remote write。 |
| 成功标准 | 用例 `1/1`；业务动机/痛点/使用价值/业务触发 `4/4`；P0 requirements/scenarios/DQ `8/8/8`；六类场景 `6/6`；七字段 schema `7/7`；standalone evidence=`1`；public C1 projection/write、raw-to-effective alias、Li–Ji/BH/FWER/DSR calibration claim、readiness overclaim、真实操作均为 `0`。 |

### CR173 用户旅程

| 步骤 | 用户意图 | 系统行为 | 成功标准 |
|---|---|---|---|
| 1 | 提出相关结构的有效维度需求 | 记录 raw count 的用途、局限，并将产品价值限定为 multiple-testing / overfit 的二阶结构输入基础。 | estimand 边界 `1/1`；raw alias 允许路径 `0`；Li–Ji/BH/FWER/DSR calibration claim `0`。 |
| 2 | 确认离线、策略无关边界 | 只接受 synthetic/fixture/golden-vector，不要求或推断具体策略身份。 | `strategy_id/strategy_name` 必填数 `0`；真实数据操作 `0`。 |
| 3 | 冻结可测行为与失败语义 | CP2 冻结 typed-unavailable、七字段证据、确定性和 claim ceiling；算法形态留 CP3。 | 8 个 DQ 均有推荐、备选、风险和切换条件。 |
| 4 | 选择方法与输入合同 | CP3 将 estimand 限定为 sealed correlation matrix 的 `spectral_participation_ratio` 二阶 effective dimensionality，冻结有效域、版本/hash 和 fail-closed；并将 public projection 判定为后续候选。 | `DO-001=PASS`、`DO-002=PASS_BY_SPLIT`；公共调用方修改数 `0`。 |
| 5 | 用本地证据实现与验证 | CP6/CP7 只运行固定 synthetic/fixture/golden vectors，生成独立七字段证据，验证 determinism、failure recovery 和 public-boundary stop。 | golden-vector 类别 `6/6`，每类重复 `3/3`，同一输入摘要唯一；public projection/write 与禁止操作各 `0`。 |
| 6 | 交付方法前置而不声称 activation | CP8 最多确认 `offline_method_ready`；public C1 / Gate 1 / admission 保持 `typed_unavailable`，且 CR172 的数据/身份/授权前置不变。 | public `c1_computable=false`；自动恢复/关闭 CR172 数 `0`；Stage 3/admission/real-evidence claim `0`。 |

### CR173 Scenario Gray Areas 与用户可见确认

| 灰区 ID | 问题 | 为什么重要 | 影响面 | 推荐 | 状态 |
|---|---|---|---|---|---|
| SGA-CR173-001 | CP2 冻结具体算法，还是只冻结 estimand 与可观察行为？ | 过早锁算法会绕过 CP3 方法评审；完全不锁行为又无法验收。 | scope / architecture / validation | CP2 冻结 non-alias estimand、失败语义和度量，具体算法留 CP3。 | resolved-approved-CP2 |
| SGA-CR173-002 | 无效或不足输入是否可退回 raw count？ | 回退会制造看似可用的虚假精度。 | correctness / risk / claim ceiling | 一律 `typed_unavailable`；矛盾或篡改输入可进一步 `blocked`。 | resolved-approved-CP2 |
| SGA-CR173-003 | estimator 是否需要具体策略身份？ | 与策略耦合会把 PATH-B 偷换成 activation。 | scope / integration / authorization | strategy-agnostic；具体身份仅由未来 CR172 activation 冻结。 | resolved-by-CR172-approval |
| SGA-CR173-004 | CR173 完成是否自动恢复或关闭 CR172？ | 自动推进会越过五字段和 runtime-high-risk 授权门。 | workflow / security / delivery | 不自动恢复或关闭；Host 仅在五字段可冻结且 fresh precheck 通过后重新打开 CR172 CP2。 | resolved-by-CR172-PATH-B-contract |

| Question ID | 问题 | 选项 / 候选理解 | 推荐方案 | 用户回答 | 复述确认 | 影响面 | 状态 |
|---|---|---|---|---|---|---|---|
| SGQ-CR173-001 | 五字段尚不可冻结且 methodology owner 独立时，应直接推进 activation，还是先完成策略无关的离线 estimator？ | A. 独立 CR 先完成 offline estimator；B. estimator 合并 CR172；C. 保持 typed-unavailable 并暂停全部推进。 | A | 用户批准 CR172 PATH-B，并于 CR173 CP2 接受八项推荐。 | FU-CR164-004 正式化为 CR173；它是 activation 前置而非替代，不授权真实数据、策略身份或 runtime。 | user value / scope / governance / authorization | confirmed-approved-CP2 |

CR173 CP2 于 2026-07-16 获用户批准。CP3 已解析两个条件分支：`DO-CR173-CP3-001=PASS`，方法限定为 participation-ratio 二阶 effective dimensionality；`DO-CR173-CP3-002=PASS_BY_SPLIT`，因 public C1 触达是 cross-owner + cross-domain + non-compatible，当前 CR 收缩为 estimator-only。未来 public C1 versioned projection 只作 backlog 候选，未建立正式 CR。

### CR173 八维覆盖与 Deferred

| 维度 | 状态 | 覆盖说明 |
|---|---|---|
| 用户 | 已覆盖 | 研究负责人、研究员、方法学 owner、consumer owner、验证负责人。 |
| 任务 | 已覆盖 | participation-ratio estimand、输入校验、估计、独立七字段 evidence、public-boundary stop 与恢复边界。 |
| 动机 | 已覆盖 | 避免相关试验被 raw count 虚假独立化，同时让当前 typed-unavailable 获得可审计的离线解决路径。 |
| 时间 | 已覆盖 | CR172 PATH-B 后启动；CP2/CP3/CP5/CP6/CP7/CP8 顺序明确。 |
| 环境 | 已覆盖 | synthetic/fixture/golden-vector only；真实系统全部 deny。 |
| 方式 | 已覆盖 | 算法延后 CP3、版本/hash/provenance、deterministic vector 与 fail-closed。 |
| 异常 | 已覆盖 | 缺失、无效、非有限、provenance/method/hash mismatch、public-boundary 越界、raw alias。 |
| 集成 | 已覆盖 | CR173 只产出 standalone evidence；public C1 projection/write、CR172 activation、C2-C4、aggregate 和 verifier 均独立。 |

Deferred：public C1 versioned projection 只登记为 backlog 候选，真正 `c1_computable` 必须经未来 projection CR；CR172 仍可按 DQ-003 以 `effective_trial_count=typed_unavailable` 降级绑定通道。五字段与 data owner、fresh precheck、真实策略身份、runtime binding，historical revalidation、C2/C3/C4、aggregate/FU-009 与 FU-006 均不进入 CR173。
