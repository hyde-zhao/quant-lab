---
status: draft
version: "0.8"
confirmed: false
confirmed_by: ""
confirmed_at: ""
---

# Product Requirements

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级需求基线草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 补充 frontmatter，并把成功标准改为可量化字段集和计数。 |
| v0.3 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation 需求；保留 CR157 adapter backlog boundary 为历史基线。 |
| v0.4 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review workflow 需求，并补齐 `DF-CR157-003` / `BL-CR157-003` promotion 追溯。 |
| v0.5 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 七对象 evidence availability、typed_unavailable fail-closed、CR155 negative regression 和 deferred producer 需求追溯。 |
| v0.6 | 2026-07-11 | meta-pm | CR163 增量追加 experiment-family lifecycle、append-only lineage、count、seal、inventory、integration、integrity 和 authorization 需求。 |
| v0.7 | 2026-07-11 | meta-pm | 根据 SGQ 全部确认 A 归一化 inventory 为 2 条去重 producer chains / 4 个 instrumentation mappings，并明确 present/typed_unavailable/blocked 与 C1 raw-input-only ceiling。 |
| v0.8 | 2026-07-12 | meta-pm | CR164 增量追加方法集、lineage/input binding、输入充分性、确定性、方法冲突、consumer integration、effective-count ceiling 与授权边界需求；回填 SGQ-CR164-001..004 全部确认 A。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164`
- 当前门禁：CR164 CP3 已批准、CP4 PASS；5/5 LLD ready，等待 CP5 全量确认
- 旧基线保留：当前仓库未发现既有 `docs/product/REQUIREMENTS.md`；既有组件文档和检查证据作为输入，不被替换。

## Requirement Summary

| REQ ID | 标题 | 优先级 | 状态 | 验收要点 |
|---|---|---|---|---|
| REQ-CR157-001 | Mature admission package builder scope | P0 | draft | 能定义从 mature research package、validation report、offline preflight、observation plan 到准入包的字段与校验边界。 |
| REQ-CR157-002 | Stage 2/Stage 3 handoff hardening | P0 | draft | Handoff 必须显式区分 Stage 2 no-lake 支撑、Stage 3 真实研究输入和 Stage 4 观察候选。 |
| REQ-CR157-003 | Research evidence index traceability | P0 | draft | 每个 package 必须追溯 data release、run manifest、metric refs、lineage refs 和 typed unavailable / blocked reason。 |
| REQ-CR157-004 | Fail-closed no-runtime guard | P0 | draft | provider、lake write、catalog publish、credential、QMT、gateway、simulation、live 和 trading 计数非 0 时阻断。 |
| REQ-CR157-005 | Portfolio risk policy compatibility | P1 | draft | 准入包必须携带 top_n、max_weight、turnover、行业/风格/容量/费用/停止条件等风险策略引用。 |
| REQ-CR157-006 | Backlog strategy adapter boundary | P1 | draft | event/ML adapters 不进入 CR157 first slice；仅保留 adapter 合同兼容性和后续 CR 入口。 |
| REQ-CR157-007 | CP2-before-design gate | P0 | draft | CP2 未 approved 前不得启动 HLD、Story 拆分、LLD 或实现。 |
| REQ-CR158-001 | Unified adapter scope | P0 | draft | CR158 必须同时覆盖 event adapter 与 ML adapter，并明确共享 core 与 type-specific extension 边界。 |
| REQ-CR158-002 | Event strategy adapter contract | P0 | draft | Event adapter 必须能表达事件输入 refs、event-time alignment、signal output refs 和 blocked reasons，且不读取真实 event feed。 |
| REQ-CR158-003 | ML strategy adapter contract | P0 | draft | ML adapter 必须能表达 training snapshot refs、model artifact refs、prediction signal refs、validation refs 和 blocked reasons，且不训练真实模型或写 registry。 |
| REQ-CR158-004 | Evidence index typed extensions | P0 | draft | Event/ML adapter evidence 必须保持 refs-only，并为 event-specific 与 ML-specific refs 提供 typed extension。 |
| REQ-CR158-005 | No-runtime authorization guard | P0 | draft | CR158 不授权真实 feed、training、provider/lake/NAS/credential、runtime、trading、publish 或 registry/store/catalog write；禁用计数非 0 必须 blocked。 |
| REQ-CR158-006 | CP2/CP5 gate enforcement | P0 | draft | CP2 前不得 HLD/Story/LLD/实现；CP5 前不得实现；CP7 必须验证 no-runtime。 |
| REQ-CR158-007 | Release wording boundary | P1 | draft | CP8 release wording 必须区分 fixture/static adapter readiness 与 production/runtime/trading readiness。 |
| REQ-CR160-001 | Stage 4 observation review workflow contract | P0 | draft | 定义 6 个 Stage 4 design objects 的输入、输出、失败路径和后续路由。 |
| REQ-CR160-002 | Observation plan template and instance boundary | P0 | draft | `observation_plan_ref` 必须指向可审查实例；CR160 必须定义 template，Stage 3 产物必须声明 instance 合规性。 |
| REQ-CR160-003 | Layered observation review checklist | P0 | draft | Checklist 必须覆盖 Stage 1、Stage 2、Stage 3 和横切授权/no-overclaim 4 层，每层至少 5 项。 |
| REQ-CR160-004 | Fail-closed evidence lane decision table | P0 | draft | Decision table 必须覆盖 4 条 evidence lane；`contract_only` lane 不得输出 `paper_candidate=true` 或 `simulation_ready`。 |
| REQ-CR160-005 | CR155 blocked seed classification | P0 | draft | 既有 CR155 evidence 必须分类为 `blocked_admission_failed`，且 `paper_candidate=false` 不得被提升。 |
| REQ-CR160-006 | Design-only authorization boundary | P0 | draft | CR160 CP8 approval 不授权代码实现、新数据访问、runtime、simulation、paper、live、trading、publish 或 CR155 晋级。 |
| REQ-CR160-007 | Product baseline traceability refresh | P0 | draft | CP8 关闭前必须更新 6 个产品基线文档，记录 `DF-CR157-003` / `BL-CR157-003` promoted to CR160。 |
| REQ-CR161-001 | Seven-object admission evidence contract | P0 | baseline-refreshed | 当前产品基线必须可发现 C1-C4 对应的七个 evidence objects、用途、availability 和 follow-up producer。 |
| REQ-CR161-002 | Typed-unavailable fail-closed ceiling | P0 | baseline-refreshed | mandatory evidence 缺失或不可计算时必须 `typed_unavailable` 且阻断；不得静默 PASS。 |
| REQ-CR161-003 | Existing-gate integration and CR155 regression | P0 | baseline-refreshed | 复用 CR151/CR154 gate；CR155 仍 blocked，不能由新 contract 或既有 rerun 证据提升。 |
| REQ-CR161-004 | No computed-proof or runtime overclaim | P0 | baseline-refreshed | contract-only baseline 不得声称已计算 FDR/PBO/DSR、OOS folds、TCA、market impact 或容量 sizing，也不得输出 runtime readiness。 |
| REQ-CR161-005 | Deferred evidence-producer traceability | P1 | baseline-refreshed | FU-CR161-001..006 与 FU-CR162-001 必须被记录为 candidate；实现和通用 checker 均需独立授权。 |
| REQ-CR163-001 | Pre-search family lifecycle | P0 | draft | 首个 trial 前必须存在 family declaration；生命周期可校验且不可事后缩小。 |
| REQ-CR163-002 | Append-only trial / attempt / selection lineage | P0 | draft | trial、retry attempt、失败/取消/排除和 selection 事件全部保留且可追溯。 |
| REQ-CR163-003 | Raw trial count semantics | P0 | draft | 参数或 seed 不同形成不同 trial；retry 只增加 attempt；计数与稳定 identity 去重结果一致。 |
| REQ-CR163-004 | Deterministic seal and supersession | P0 | draft | seal 内容确定、hash 可复算；纠错只新增 superseding version，不修改旧版本。 |
| REQ-CR163-005 | Frozen candidate-producer inventory | P0 | confirmed-CP2-input | 2 条去重 producer chains 的 `CPI-CR163-001..004` 4/4 instrumentation mappings 共享 producer contract；excluded paths 不进入分母。 |
| REQ-CR163-006 | Existing-gate availability integration | P0 | confirmed-CP2-input | 只向 CR151/CR154/admission consumer 暴露 lineage availability/ref/raw count；effective count 仍 unavailable，C1 仍不可计算。 |
| REQ-CR163-007 | Completeness, tamper and recovery validation | P0 | draft | missing、duplicate、count mismatch、post-seal mutation 100% fail-closed，并可沿 supersession 恢复。 |
| REQ-CR163-008 | Authorization and CR155 regression boundary | P0 | draft | 禁止真实数据/runtime/外部写入/统计计算/历史回填；CR155 始终 blocked。 |
| REQ-CR164-001 | MVP statistical method set | P0 | confirmed-CP2-input | BH、WRC/SPA、PBO/CSCV、DSR 均为 MVP mandatory methods，claim-relevant 聚合无 OR-pass。 |
| REQ-CR164-002 | Validation-bound family/input identity | P0 | draft | 所有计算绑定同一 sealed family ref/hash/raw count 与完整 candidate membership。 |
| REQ-CR164-003 | Method-specific computable evidence | P0 | draft | 每个批准方法都有输入、输出、参数、provenance、availability 与 blocked reason。 |
| REQ-CR164-004 | Quantitative input sufficiency | P0 | confirmed-CP2-input | 候选、split/fold、sample、finite-value 与退化输入阈值按 SGQ A 可机器判定。 |
| REQ-CR164-005 | Determinism and numerical boundary | P0 | draft | 相同规范化 fixture 可复跑，NaN/Inf/退化输入 fail-closed。 |
| REQ-CR164-006 | Method disagreement projection | P0 | draft | mandatory FAIL/BLOCKED 不得被其他方法 PASS 覆盖；冲突最保守投影。 |
| REQ-CR164-007 | Existing-consumer integration | P0 | draft | 复用 CR151/CR154/admission package，不建立竞争 gate。 |
| REQ-CR164-008 | Effective-trial claim ceiling | P0 | confirmed-CP2-input | raw count 不得冒充 effective count；effective 保持 typed_unavailable。 |
| REQ-CR164-009 | Compatibility, authorization and regression | P0 | confirmed-CP2-input | UC-58 实现、UC-59/60 compatibility-only，禁用操作为 0，CR155 保持 blocked。 |

## Functional Requirements

### REQ-CR157-001 Mature Admission Package Builder Scope

CR157 应定义 mature admission package builder 的产品范围。Builder 后续实现应只消费研究产物引用和验证证据引用，不读取真实数据湖、不触发 provider、不导入 QMT、不调用 gateway，也不发布 registry/store/catalog。

成功标准：

- 字段清单固定为 11 类：strategy id、run id、data release ref、factor model validation report ref、mature research package ref、runner offline preflight ref、observation plan ref、risk policy ref、evidence index ref、blocked reasons、authorization flags；11/11 缺一即 blocked。
- 缺失 P0 evidence、`typed_unavailable:*`、placeholder 或 runtime flags 冲突时 fail-closed。
- 输出不能声明 simulation-ready、paper-ready、live-ready 或 trading-ready。

### REQ-CR157-002 Stage 2/Stage 3 Handoff Hardening

CR157 应把现有历史命名中的 `stage3` 兼容对象解释清楚：Stage 2 输出框架支撑和 handoff contract，Stage 3 研究机生产真实研究证据，Stage 4 才是观察候选审查。

成功标准：

- Handoff 文档或 schema 必须包含输入、输出、证据、边界、下一阶段消费方式和降级策略。
- 任一真实 runtime 或交易需求必须另开 authorization gate。

### REQ-CR157-003 Research Evidence Index Traceability

准入包必须能从轻量 package 引用追溯到完整研究证据，不复制大型证据正文。

成功标准：

- Evidence index 固定包含 7 类引用：data release ref、manifest ref、metric refs、lineage refs、risk policy ref、validation report ref、runner offline preflight ref；7/7 缺一即 blocked。
- blocked / unavailable 必须结构化表达，不能通过空字符串或自然语言隐藏。

### REQ-CR157-004 Fail-Closed No-Runtime Guard

CR157 必须延续 Stage 2 no-lake/no-runtime 防线。

成功标准：

- 禁用面包括 NAS access、provider fetch、credential/env read、lake write、catalog/store/registry write、QMT/MiniQMT/xtquant、gateway、simulation、paper/live trading、broker/order/account 操作、Git remote write、publish。
- 禁用计数非 0 时阻断，并给出 machine-readable reason。

### REQ-CR158-001 Unified Adapter Scope

CR158 必须把 CR157 延后的 event strategy adapter 与 ML strategy adapter 作为一个统一 adapter Change Package 推进。统一不等于强行相同：共享 core 只承载 strategy type、input refs、output signal refs、evidence refs、blocked reasons、authorization flags 和 handoff refs；event-only 与 ML-only 字段必须通过 type-specific extension 显式表达。

成功标准：

- CP2 Decision Brief 必须列出 3 个 scope 选项：统一 event+ML、只做 event、只做 ML；推荐方案为统一 event+ML。
- CP3 HLD 必须明确 shared core 字段不少于 7 类，type-specific extension 至少区分 event 与 ML 两类。
- 任何 Story 或 schema 不得把 event-only 字段设为 ML 必填，或把 ML-only 字段设为 event 必填。

### REQ-CR158-002 Event Strategy Adapter Contract

Event adapter 应将离散事件类策略输入转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static event refs，不允许接入真实 feed、live listener、provider 或 gateway。

成功标准：

- Event adapter contract 至少包含 6 类字段：event source ref、event time ref、event payload schema ref、alignment policy ref、signal output ref、blocked reason ref。
- 真实 event feed、live listener、provider fetch、gateway call 计数必须为 0。
- 缺少 event source ref、alignment policy ref 或 signal output ref 时必须 fail-closed。

### REQ-CR158-003 ML Strategy Adapter Contract

ML adapter 应将模型类策略的训练/验证/预测引用转化为统一 signal / evidence / handoff refs。CR158 只允许 fixture/static model artifact refs，不允许训练真实模型、调用外部模型服务或写 model registry。

成功标准：

- ML adapter contract 至少包含 7 类字段：training snapshot ref、feature set ref、label policy ref、model artifact ref、validation report ref、prediction signal ref、blocked reason ref。
- real model training、external model service、model registry write/promotion 计数必须为 0。
- 缺少 training snapshot ref、validation report ref 或 prediction signal ref 时必须 fail-closed。

### REQ-CR158-004 Evidence Index Typed Extensions

CR158 必须延续 CR157 refs-only evidence index 基线，新增 event/ML typed extension 时只能记录引用和短元数据，不复制报告正文、模型文件、event payload 全文、diff、transcript 或大型矩阵正文。

成功标准：

- Event extension 至少能引用 event source、alignment policy 和 signal output refs。
- ML extension 至少能引用 training snapshot、model artifact、validation report 和 prediction signal refs。
- Evidence index 中大型正文复制计数必须为 0。

### REQ-CR158-005 No-Runtime Authorization Guard

CR158 的任何 CP2 / CP3 / CP5 / CP6 / CP7 / CP8 approve 都不授权真实运行时或生产写入。

成功标准：

- 禁用面包括 real event feed、real model training、external model service、model registry write、provider fetch、NAS access、credential/env/session read、lake write、catalog/store/registry/prediction write、QMT/MiniQMT/xtquant/gateway、simulation/paper/live/trading/broker、external framework run、Git remote write、publish。
- CP7 evidence 必须报告禁用操作计数；每个禁用计数必须为 0。
- 任一禁用计数非 0 时，CP7 不得 PASS。

### REQ-CR158-006 CP2/CP5 Gate Enforcement

CR158 是 architecture-major product-scope CR，必须保留 CP2 / CP3 / CP5 / CP8 人工门禁。

成功标准：

- CP2 approved 前不得创建 dev-ready Story、LLD 或实现。
- CP5 approved 前不得修改 adapter source/test implementation。
- CP2 approve 只授权进入 solution-design；不授权 implementation、runtime 或 publish。

### REQ-CR158-007 Release Wording Boundary

CR158 的 release notes、verification report 和 component docs 必须明确区分 local/static/fixture adapter readiness 与 production/runtime readiness。

成功标准：

- CP8 release wording 必须包含 “not authorized” 清单，覆盖真实 feed、训练、registry、runtime、trading、publish。
- 不得出现 simulation-ready、paper-ready、live-ready、trading-ready、production-ready 或 registry-published 声明，除非后续独立授权 CR 明确批准。

### REQ-CR160-001 Stage 4 Observation Review Workflow Contract

CR160 必须补齐 CR157 预留但未定义的 Stage 4 observation review 语义，使 Stage 3 mature research package 到 Stage 5 paper/simulation admission 之间有可审查、可失败、可路由的 contract。

成功标准：

- HLD 必须定义 6 个 Stage 4 design objects：ObservationReviewInput、EvidenceProfile、AdmissionReadiness、ObservationDecision、EscalationRoute、AuthorizationBoundary。
- 每个 design object 必须列出输入、输出、失败路径和下一阶段消费方式。
- 缺少 observation plan instance、admission package ref、research evidence refs 或 authorization boundary 时必须 fail-closed。

### REQ-CR160-002 Observation Plan Template and Instance Boundary

CR160 必须区分 observation plan template 与 observation plan instance，避免把模板文档误当成已审查实例。

成功标准：

- Observation plan template 至少定义 5 类内容：观察周期、检查点频率、跟踪指标、退出条件、Stage 1/2/3 evidence refs 要求。
- Stage 3 产物必须提供 observation plan instance ref；仅有 template ref 时 Stage 4 review 不得通过。
- Review workflow 必须审查 instance 对 template 的合规性，并在不合规时输出 blocked 或 needs_review。

### REQ-CR160-003 Layered Observation Review Checklist

Observation review checklist 必须覆盖数据基础、研究生产、研究机 admission 和横切授权边界，不能只审 Stage 3 统计结果。

成功标准：

- Stage 1 层至少 5 项，覆盖 PIT、universe、lineage、dataset refs、leakage policy。
- Stage 2 层至少 5 项，覆盖 factor methodology、evaluation refs、typed_unavailable、blocked reasons、evidence index。
- Stage 3 层至少 5 项，覆盖 statistical gate、out-of-sample、economic significance、capacity/impact、rerun consistency。
- 横切层至少 5 项，覆盖 operation counters、authorization boundary、no-overclaim wording、follow-up route、human review outcome。
- 每个 checklist item 的结果枚举必须是 PASS、NEEDS_REVIEW、FAIL 或 N/A。

### REQ-CR160-004 Fail-Closed Evidence Lane Decision Table

CR160 必须用 evidence lane + admission readiness 的矩阵表达 Stage 4 结果，默认 fail-closed。

成功标准：

- Evidence lane 必须覆盖 4 类：`contract_only`、`real_data_validated`、`runtime_authorized`、`unknown`。
- `contract_only` lane 的 readiness=true 路径数量必须为 0。
- `unknown` lane 必须 blocked 或 needs_review，不能输出 paper/simulation readiness。
- `real_data_validated` lane 仍需 admission 非阻断；real-data evidence 不等于 runtime authorization。

### REQ-CR160-005 CR155 Blocked Seed Classification

CR155 daily baseline artifact 必须作为 fail-closed 反例样本被 CR160 workflow 正确分类。

成功标准：

- CR155 既有 evidence 必须显示 admission package `FAIL` 或 `BLOCKED`、`paper_candidate=false`、blocked gates 可追溯。
- CR160 classification 必须输出 `blocked_admission_failed`。
- Rerun consistency PASS 不得提升 CR155 evidence 等级，也不得绕过 admission FAIL。
- CR160 不得执行新的 real lake read/write；只消费既有 CR155 evidence ref。

### REQ-CR160-006 Design-Only Authorization Boundary

CR160 是 product-scope / requirement-change 的纯设计 CR，不是 runtime 或代码实现 CR。

成功标准：

- CP8 approve 不授权代码实现、schema/checker、strategy remediation、CR155 晋级、新 real lake read/write、NAS/provider/credential access、broker/order/trading、QMT/MiniQMT/xtquant/gateway、paper/simulation/live/runtime、catalog/store/registry/model/prediction write、Git remote write、deployment、release execution 或 publish。
- Release wording 必须明确 `READY_WITH_RISK` 只表示 Stage 4 design/gate contract 可用作后续基线。
- 所有 Stage 5 paper/simulation/live/runtime 动作必须另起 CR 和授权 gate。

### REQ-CR160-007 Product Baseline Traceability Refresh

CR160 CP0/CP2 已承诺刷新产品基线；CP8 关闭前必须补齐该追溯链。

成功标准：

- 6 个产品文档必须增量更新：`USE-CASES.md`、`REQUIREMENTS.md`、`SCENARIOS.yaml`、`TEST-MATRIX.md`、`MVP-SCOPE.md`、`BACKLOG.md`。
- `DF-CR157-003` 与 `BL-CR157-003` 必须标记为 promoted to CR160，且旧 CR157/CR158 基线不得被删除。
- 产品文档必须保留修订记录，并把 product baseline refresh 作为 CP8 关闭前置条件记录到 CP8 checkpoint。

### REQ-CR161-001 Seven-Object Admission Evidence Contract

- 当前产品基线必须枚举 `ExperimentFamilyManifest`、`MultipleTestingEvidence`、`DataSnoopingEvidence`、`OverfitRiskEvidence`、`WalkForwardEvidence`、`EconomicCostEvidence` 和 `CapacityLiquidityEvidence`。
- 每个对象必须能追溯其覆盖的 C1-C4 blocker、availability 语义、现有 gate 集成点和后续 evidence producer；不要求当前切片提供计算实现。

### REQ-CR161-002 Typed-Unavailable Fail-Closed Ceiling

- 缺 trial lineage、trial count、parameter-search lineage、raw p-values、fold metrics、成本输入或容量输入时，相关 mandatory evidence 必须是 `typed_unavailable` 并阻断 admission。
- `typed_unavailable` 不是 PASS、不是计算成功、不是风险接受，也不得降格为静默 warning。

### REQ-CR161-003 Existing-Gate Integration and CR155 Regression

- CR161 evidence availability 只补充 CR151 statistical gate 和 CR154 相关控制面；不得创建竞争性 admission gate。
- CR155 只能作为 negative regression：即使它缺少新 C1/C2 可计算输入，也必须保持 `blocked`，不得重建或推断缺失历史数据。

### REQ-CR161-004 No Computed-Proof or Runtime Overclaim

- 本基线只声明 evidence-computable 或 `typed_unavailable` fail-closed 的判别边界；当前已交付的是后者。
- FDR/PBO/DSR、walk-forward/OOS fold-level 指标、真实 market impact/TCA、capacity/liquidity sizing、真实数据访问和任何 runtime/trading 结论均不由本需求授权。

### REQ-CR161-005 Deferred Evidence-Producer Traceability

- `FU-CR161-001..006` 保持后续追溯链，分别覆盖 trial-lineage instrumentation、统计/数据偷窥/过拟合计算、walk-forward/OOS producer、economic/capacity producer、集成验证和 verifier-lane resilience。
- `FU-CR162-001` 只跟踪通用 CP8 product-baseline-refresh checker；它不改变 CR162 文档纠错的 design-only 边界。
- `FU-CR161-001` 由 CR163 承接为 active product-scope CR；`FU-CR161-002..006` 和 `FU-CR162-001` 继续保持 candidate。
- CR163 只解决 experiment-family raw lineage 事实来源，不隐式启动其余 producer。

### REQ-CR163-001 Pre-Search Family Lifecycle

- 首个 candidate-producing trial 开始前必须已有 family declaration；验证证据必须能证明 declaration timestamp / sequence 早于任何 trial start。
- family 生命周期至少区分 declared、recording、sealed、superseded 或 CP3 确认的等价状态；最终名称由 CP3 决定。
- sealed family 的 declared search space、trial membership 和 selection policy 不得原地缩小。

成功标准：P0 inventory 的 2/2 生产链均在 first trial 前声明 family；post-hoc declaration 验证 100% blocked。

### REQ-CR163-002 Append-Only Trial / Attempt / Selection Lineage

- 每个 trial 必须有稳定 trial identity；每次执行尝试必须有独立 attempt identity，并回链 family、trial、run、experiment 与 artifact refs。
- success、failed、cancelled、excluded 状态及 selection / rejection reason 均不得因最终候选选择而删除。
- 同一事件 identity 的完全相同重复写可幂等；同 identity 不同内容必须冲突并 blocked。

成功标准：声明的每个 trial 至少有 1 个 attempt 或明确的 never-started terminal reason；0 个未解释孤儿 trial；0 个无法回链的 selection。

### REQ-CR163-003 Raw Trial Count Semantics

- 不同参数组合或不同 seed 视为不同 trial，即使其余字段相同。
- 同一 trial 的 retry 产生新 attempt，不增加 `raw_trial_count`。
- failed、cancelled、excluded trial 仍属于 declared/search family 并计入 raw count；重复 delivery 不重复计数。

成功标准：`raw_trial_count = count(distinct stable_trial_id)`；seed A/B 产生 2 个 trial；同 trial 3 次 retry 仍为 1 个 raw trial、3 个 attempts；manifest count 与事件重算值不一致时 100% blocked。

### REQ-CR163-004 Deterministic Seal and Supersession

- seal 必须基于规范化内容与确定性排序，同一逻辑内容重复计算产生相同 content hash。
- sealed version immutable；任何纠错创建新 version，提供 `supersedes_ref` / reason，并保留旧 ref/hash。
- consumer 默认解析最新合法未撤销版本，但审计者仍能验证完整 version chain；最终对象名与 artifact 路径留给 CP3。

成功标准：相同 fixture 重复 seal 10 次得到 1 个 hash；原 sealed artifact 原地修改次数为 0；断链、循环或 hash mismatch 100% blocked。

### REQ-CR163-005 Frozen Candidate-Producer Inventory

- P0 分母固定为 **2 条去重 producer chains / 4 个 instrumentation mappings**：`CPI-CR163-001..004`；两个 public/legacy entrypoints 和两个 direct construction hooks 都有 mapping。
- wrapper 与 hook 属同一 producer chain，不得按调用层级重复增加 trial count。
- anomaly factor discovery、compatibility adapter、admission consumer、单次-run contract 和未存在的 real ML/event runner 均必须显式 excluded/N/A，而非静默漏测。

成功标准：2 条 producer chains 均被覆盖，P0 instrumentation mapping 4/4、coverage 100%；included path 未映射数 0；excluded path 均有理由和重访条件。

### REQ-CR163-006 Existing-Gate Availability Integration

- `ExperimentManifest` 保持单次-run object；family lineage 以独立 lifecycle 通过 `run_id`、`experiment_id` 和 artifact refs 连接。
- 对既有 admission consumer 只暴露 `present / typed_unavailable / not_applicable_with_reason / blocked` availability、lineage ref、raw count 与验证状态；不得新建竞争 gate family。
- 本 CR 中 `effective_trial_count` 必须保持 `typed_unavailable`，其 ref 与 method 为空；不得以 raw count 替代。
- 未来原生 instrumented run 仅在 seal、completeness、reference integrity、count 与 tamper checks 全 PASS 后，`ExperimentFamilyManifest` 才可 `present`；未 instrumented path 为 `typed_unavailable`；invalid/incomplete/tampered lineage 为 `blocked`。
- CR163 只使 C1 raw-lineage input-ready；缺少 raw p-values、effective-trial method 和 statistical producer 时，C1 multiple-testing/data-snooping/overfit evidence 仍不可计算。

成功标准：present 只在 seal、completeness、reference integrity、count 与 tamper checks 全 PASS 时出现；未 instrumented fixture 100% typed_unavailable；invalid/tampered fixture 100% blocked；effective count 的 available 声明数为 0；C1 computed-evidence 声明数为 0。

### REQ-CR163-007 Completeness, Tamper and Recovery Validation

- validator 必须覆盖 family declaration、trial/attempt/selection referential integrity、duplicate identity、raw count、seal hash、version chain 和 missing instrumentation。
- 失败后允许基于 append-only correction + superseding seal 恢复；不得删除失败事件或覆盖旧 sealed version。
- 所有 blocked reason 都必须 machine-readable 并指向 evidence ref 或缺失字段。

成功标准：正向、missing、duplicate-conflict、count-mismatch、tamper、broken-supersession 六类 fixture 均有确定结论；五类负向 fixture 5/5 blocked。

### REQ-CR163-008 Authorization and CR155 Regression Boundary

- 本 CR 不授权 real lake/NAS/provider/credential、runtime、simulation/paper/live、broker/trading、external framework、remote write、publish 或 catalog pointer mutation。
- 不授权 statistical correction、effective-trial computation、historical lineage reconstruction；不得用推断 backfill 生成 `present`。
- CR155 仅作为 negative regression，保持 blocked；新 lineage contract、rerun consistency 或 unavailable evidence 均不得提升它。

成功标准：所有 forbidden operation counters 为 0；CR155 regression 1/1 保持 blocked；runtime-ready / statistical-proof overclaim 数为 0。

### REQ-CR164-001 MVP Statistical Method Set

- SGQ-CR164-001 已确认 A：BH + WRC/SPA + PBO/CSCV + DSR；每种方法独立表达 `present / typed_unavailable / blocked`。
- positive statistical-significance、performance-robustness、Sharpe/IC reliability claim 只能消费其 claim-relevant mandatory methods；不得以任一方法 PASS 形成 OR-pass。
- Bonferroni/BH 现有 anomaly helper 只是可复用事实，不等于 strategy-family 方法或 schema 已获批准。

成功标准：CP2 method matrix 对 4/4 方法逐项记录 required/deferred、输入、claim、不可用语义与切换条件；未确认前 `ready_for_design=false`。

### REQ-CR164-002 Validation-Bound Family and Input Identity

- 所有 method evidence 必须绑定 CR163 trusted projection 的 family ref、target hash、raw trial count 与候选 membership；serialized/untrusted projection、hash mismatch 或 manual count mismatch 必须 blocked。
- candidate metric、p-value、return path 与 split 输入必须能回链同一 family/trial identity；不得混用不同 family 或选择后缩小分母。

成功标准：完整 fixture 的 lineage/input refs 100% 一致；missing lineage 为 typed_unavailable；family/hash/count/membership mismatch 5/5 负向 fixture blocked。

### REQ-CR164-003 Method-Specific Computable Evidence

- BH evidence 至少记录 raw/adjusted p-values、alpha、candidate count、rejected count、method/version 与 provenance。
- WRC/SPA evidence 至少记录候选集合、benchmark/null、对齐 return matrix、resampling policy、seed/config 与 corrected significance result。
- PBO/CSCV evidence 至少记录候选集合、组合 split 定义、train/test ranking或 loss、有效 split count 与 PBO。
- DSR evidence 至少记录 observed Sharpe、sample length、skew、kurtosis、trial-count provenance、approved trial-count mode 与 DSR。

成功标准：每个已批准方法 required fields 100% 存在且有限；缺字段不产生 present evidence。

### REQ-CR164-004 Quantitative Input Sufficiency

- SGQ-CR164-003 已确认 A：BH/WRC-SPA 至少 2 个完整候选；PBO/CSCV 至少 4 个完整候选和 4 个有效组合 splits，且每 split 的 train/test 观察均非空；DSR 至少 2 个 trials、sample_length >= 30、收益方差 > 0。
- 所有方法输入必须是有限值；空数组、NaN、Inf、零方差、无法对齐的 return path、缺失 split side 或低于阈值均不得计算正向证据。

成功标准：每个方法的下限、比较符号、required fields 和失败状态在 CP2 可度量；低阈值与退化 fixture 100% fail-closed。

### REQ-CR164-005 Determinism and Numerical Boundary

- 相同规范化 fixture、方法版本、参数、seed/config 必须生成相同 evidence summary；排序与 hash 输入必须确定。
- 浮点输出必须有限并满足方法定义域：p/q/PBO 在 [0,1]；count 为正整数；sample length、split count 与 candidate count 与输入一致。

成功标准：同一 fixture 10 次计算只产生 1 个摘要 hash；NaN、Inf、负 count、长度不一致、越界概率、零方差 6 类负向 fixture 6/6 blocked 或 typed_unavailable。

### REQ-CR164-006 Method Disagreement Projection

- 每个方法原始结论保留；聚合层不得改写或丢弃不利结果。
- claim-relevant mandatory 方法任一 BLOCKED/typed_unavailable 时相关 claim blocked；任一 FAIL 时不得由其他 PASS 提升；仅非 mandatory 方法差异可进入 needs_review 且必须有 reason/ref。

成功标准：BH PASS + WRC FAIL、PBO PASS + DSR unavailable、单一 method PASS + 另一 mandatory blocked 三类 fixture 均不输出 clean PASS。

### REQ-CR164-007 Existing-Consumer Integration

- method evidence 投影到既有 `strategy_admission_statistical_gate`、CR154 Gate 1 slots 与 `strategy_admission_package`；不得新建竞争 admission gate family。
- consumer 只能保持或恶化上游 admission status；evidence ref 不得改变 runtime authorization flags。

成功标准：3/3 consumer paths 可回链同一 method refs；blocked input 3/3 保持 blocked；新增 competing gate count 为 0。

### REQ-CR164-008 Effective-Trial Claim Ceiling

- SGQ-CR164-002 已确认 A：CR164 MVP 不定义 effective-trial estimator，`effective_trial_count`、ref、method 保持 typed_unavailable/空；raw count 不得代替它。
- CP3 schema 必须声明 `dsr_input_method=raw_trial_count`、lineage provenance 与 effective-count non-alias limitation。
- DSR 是否可在 raw-count mode 下形成独立 evidence，与现有 Gate-1 是否允许 deflated-performance claim 必须分开表达；现有 consumer 要求 effective count时保持 blocked。

成功标准：未获批 estimator 下 effective-count available 声明数为 0；raw-to-effective alias 数为 0；受影响 claim 的错误 PASS 数为 0。

### REQ-CR164-009 Compatibility, Authorization and Regression

- SGQ-CR164-004 已确认 A：UC-58 multifactor 是当前实现主体；UC-59 ML 与 UC-60 event 仅消费 compatibility contract，缺相同 sealed-family/statistical inputs 时 fail-closed。
- 不授权真实研究批次、production/lake/NAS/provider/credential、external framework、broker/trading、publish 或 remote write。
- CR155 只消费既有 evidence refs，始终保持 blocked；不得回填 p-values、returns、splits、effective counts 或统计结论。

成功标准：UC-58/59/60 compatibility cases 3/3 有确定结论；forbidden operation counters 全为 0；CR155 1/1 blocked；runtime-ready/statistical-proof overclaim 数为 0。

## CR164 Quantitative Acceptance Criteria

| AC ID | 指标 | 目标值 | 失败行为 | 来源 |
|---|---|---:|---|---|
| QAC-CR164-001 | selected-method required-input coverage | 100% | 任一 required input 缺失则该方法不得 present | SGQ-CR164-001/003 |
| QAC-CR164-002 | family/ref/hash/raw-count binding coverage | 100% | 缺失为 typed_unavailable；mismatch/tamper 为 blocked | REQ-CR164-002 |
| QAC-CR164-003 | candidate/raw-ledger/method-input count difference | 0 | 任一差异 blocked，不允许 post-selection shrink | REQ-CR164-002/004 |
| QAC-CR164-004 | enumerated negative-fixture fail-closed hit rate | 100% | 任一 false PASS 阻断 CP7 | REQ-CR164-004/005/006 |
| QAC-CR164-005 | same-fixture deterministic reruns | 10 runs -> 1 summary hash | hash 漂移 blocked | REQ-CR164-005 |
| QAC-CR164-006 | orphan method-evidence references | 0 | orphan ref blocked | REQ-CR164-003/007 |
| QAC-CR164-007 | consumer projection coverage | 3/3：UC-58 multifactor + UC-59 ML compatibility + UC-60 event compatibility | 缺 consumer projection 阻断对应 claim | REQ-CR164-007/009 |
| QAC-CR164-008 | CR155 negative-regression preservation | 1/1 blocked | 状态提升即 FAIL | REQ-CR164-009 |
| QAC-CR164-009 | forbidden-operation counters | 每项 0 | 任一非 0 blocked | REQ-CR164-009 |
| QAC-CR164-010 | runtime/statistical-proof overclaims | 0 | 任一 overclaim blocked | REQ-CR164-008/009 |

QAC-CR164-007 的 3/3 是产品 consumer coverage，不代表 UC-59/60 implementation scope。所有指标只由后续 fixture/static 验证证明；本阶段不执行统计计算。

## CR164 CP3 Design Obligations

| Obligation ID | 义务 | CP2 已冻结的不变量 | CP3 待决策内容 |
|---|---|---|---|
| DO-CR164-001 | DSR input semantics | effective count typed_unavailable；raw 不得别名 effective | schema 写入 `dsr_input_method=raw_trial_count`、lineage provenance、limitation/reason code |
| DO-CR164-002 | WRC/SPA bootstrap | WRC/SPA 属于 MVP；结果须确定性可复跑 | stationary bootstrap 的 block-length mode：`automatic_politis_romano_1994` vs `fixed_window`，参数/seed provenance、切换条件 |
| DO-CR164-003 | Method disagreement | claim-relevant mandatory methods 无 OR-pass；FAIL/BLOCKED 不得被 PASS 覆盖 | 完整 priority/final-status decision table 与 reason-code mapping |

## Non-Functional Requirements

| NFR ID | 维度 | 要求 | 度量 |
|---|---|---|---|
| NFR-CR157-001 | 可追溯性 | Package 不复制大证据正文，只引用 evidence index。 | P0 evidence refs 覆盖率 100%。 |
| NFR-CR157-002 | 安全性 | 禁用外部运行时和真实交易。 | 禁用计数必须为 0。 |
| NFR-CR157-003 | 可测试性 | 所有 P0 场景可用 fixture/static/no-lake 方式验证。 | P0 scenario 覆盖率 100%。 |
| NFR-CR157-004 | 可扩展性 | Adapter 合同不阻断 event/ML 后续扩展。 | `docs/product/BACKLOG.md` 必须保留 2 个 adapter follow-up：`BL-CR157-001` 和 `BL-CR157-002`。 |
| NFR-CR158-001 | 可追溯性 | Event/ML adapter evidence 只引用 refs，不复制大型正文。 | 大型正文复制计数为 0；P0 refs 覆盖率 100%。 |
| NFR-CR163-001 | 完整性 | 冻结 producer inventory、trial/attempt/selection 与 seal chain 全部可重算。 | P0 inventory mapping 4/4；未解释 orphan 与 count mismatch 均为 0。 |
| NFR-CR163-002 | 确定性 | 相同规范化 lineage 内容产生相同 seal。 | 同一 fixture 连续 seal 10 次仅产生 1 个 content hash。 |
| NFR-CR163-003 | 安全与权限 | fixture/static 验证不访问任何禁止 runtime/data/external write。 | 所有 forbidden operation counters 为 0；任一非 0 则 blocked。 |
| NFR-CR163-004 | 可维护性 | sealed 修正以 supersession 追加，保留旧版本审计。 | sealed artifact 原地修改数 0；有效 supersession chain 覆盖率 100%。 |
| NFR-CR158-002 | 安全性 | Event/ML adapter 实现必须保持 no-runtime/no-publish。 | 禁用操作计数全部为 0。 |
| NFR-CR158-003 | 可演进性 | Shared core 与 type-specific extension 分离。 | event-only 与 ML-only 字段互不成为对方必填项。 |
| NFR-CR158-004 | 可测试性 | 所有 P0 CR158 场景可用 fixture/static 方式验证。 | P0 scenario 覆盖率 100%。 |
| NFR-CR160-001 | 可追溯性 | Stage 4 review 必须可回链 Stage 1/2/3 refs、CR155 seed evidence 和产品基线 promotion。 | CR160 P0 requirement / scenario / matrix 覆盖率 100%；6/6 产品文档刷新。 |
| NFR-CR160-002 | 安全性 | Stage 4 design closure 不得被误读为 runtime、paper、simulation 或 live 授权。 | 禁用操作授权数量为 0；not-authorized 清单覆盖 12 类以上。 |
| NFR-CR160-003 | 可测试性 | Checklist、decision table 和 CR155 seed classification 必须可人工复核。 | Checklist item 数 >= 20；CR155 classification evidence ref 1 个以上。 |
| NFR-CR164-001 | 可追溯性 | 每个 method result 绑定 family、输入、参数、方法版本与 evidence ref。 | 已批准方法 provenance 字段覆盖率 100%；orphan ref 数为 0。 |
| NFR-CR164-002 | 确定性 | 相同规范化 fixture 的计算摘要稳定。 | 重复 10 次只产生 1 个摘要 hash。 |
| NFR-CR164-003 | 数值安全 | 非有限、退化、长度/计数不一致与越界值 fail-closed。 | 6 类负向 fixture 6/6 不产生 present/PASS。 |
| NFR-CR164-004 | 安全与权限 | 本地 fixture/static 验证不执行禁止操作。 | 所有 forbidden operation counters 为 0；任一非 0 则 blocked。 |

## Open Decisions

| 决策 ID | 类型 | 问题 | 推荐方案 | 状态 |
|---|---|---|---|---|
| DQ-CP2-CR157-FIRST-SLICE | scope | CR157 first slice 是否纳入 event/ML adapters？ | 不纳入；event/ML adapters 作为 backlog 或后续 CR。 | pending user review |
| DQ-CP2-CR158-UNIFIED-SCOPE | scope | CR158 是否把 event 与 ML adapter 合并为一个统一 adapter CR？ | 合并为一个 CR，shared core + type-specific extension。 | pending user review |
| DQ-CP2-CR158-NO-RUNTIME | security | CR158 CP2 approve 是否授权真实 feed、训练、registry、runtime、trading或 publish？ | 不授权；只允许 local/static/fixture 设计和后续验证。 | pending user review |
| DQ-CP2-CR158-GATE-SEQUENCE | implementation | CP2 approve 后是否允许直接实现？ | 不允许；CP2 后进入 CP3 HLD，CP5 批准后才实现。 | pending user review |
| DQ-CP2-CR160-EVIDENCE-PROFILE | scope | CR160 observation review 输入是 contract-level evidence 还是 real-data evidence？ | 双轨 fail-closed；contract lane 不能输出 paper/simulation readiness。 | approved |
| DQ-CP2-CR160-DELIVERABLE-SHAPE | implementation | CR160 是设计交付还是代码实现？ | 纯设计交付；CP4/CP5/CP6 N/A，CP7/CP8 做设计验证和发布就绪。 | approved |
| DQ-CP8-CR160-004 | scope / traceability | CP8 关闭前是否必须补齐产品基线刷新？ | 必须补齐 6 个产品文档，作为 CR160 关闭前置条件。 | resolved 2026-07-09 |
| DQ-CP2-CR164-METHOD-SET | scope | MVP 是否包含 BH + WRC/SPA + PBO/CSCV + DSR？ | 四类均纳入并逐方法 fail-closed。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-EFFECTIVE-TRIAL | scope / risk | 是否在本 CR 计算 effective trial count？ | 不计算；保持 typed_unavailable，防止未经批准的 estimator。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-SUFFICIENCY | risk_acceptance | 方法充分性下限采用推荐值还是更严格值？ | 采用方法特定推荐下限，后续 CP3 可在不降低下限的前提下收紧。 | resolved-A 2026-07-12 |
| DQ-CP2-CR164-COMPATIBILITY | scope | UC-59/60 是实现对象还是 compatibility-only？ | UC-58 实现，UC-59/60 compatibility-only。 | resolved-A 2026-07-12 |
