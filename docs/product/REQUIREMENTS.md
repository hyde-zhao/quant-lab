---
status: confirmed-cp2
version: "1.6"
confirmed: true
confirmed_by: "user-CR169-CP2-review-remediation"
confirmed_at: "2026-07-14T17:45:00+08:00"
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
| v0.9 | 2026-07-13 | host-orchestrator-inline | CR166 增量追加 C2 producer 输入、泄漏边界、确定性 envelope、consumer projection、兼容与授权需求，以及 12 项量化成功标准。 |
| v1.0 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 批准，冻结 9 项需求、12 项 QAC、fixture/static 与 Stage 3 claim ceiling；解锁 CP3 设计但不授权实现。 |
| v1.1 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 批准；9 项需求与 12 项 QAC 映射到五个正式 Story 和 CP5 全量设计证据，继续不授权实现。 |
| v1.2 | 2026-07-13 | host-orchestrator-inline | CR168 增量追加 9 项 C3 需求、15 项精确 QAC、Gate 4 C3+C4 联合边界、两类 fixture 与 5 个 CP2 开放决策；保留既有需求基线。 |
| v1.3 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见为 REQ-CR168-006 增加 projection-side absent-no-na-reason guard，新增 `SC-CR168-B02`；9 项需求、15 项 QAC、10 类 C3 fail-closed 与范围边界均不变，并补齐 CP3 前向设计义务。 |
| v1.4 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准；依据 canonical Gate 4 代码评审，把 reason 逃逸整改精确为 CR168 adapter 的 8-key denylist、strict allowlist、调用前拒绝、调用后非 PASS 断言与 adapter-only 调用面，canonical 全局硬化仍不在本 CR。 |
| v1.5 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 的 9 项 C4 fixture/static requirements、15 项 QAC、strict C3+C4 joint adapter 边界、alpha-decay CP3 disposition 与五项 CP2 DQ；不改写 CR168、canonical Gate 4 或 CR155 基线。 |
| v1.6 | 2026-07-14 | host-orchestrator-inline | 根据 CR169 CP2 评审整改，明确 `stage3_entry_ready=false`，将 Stage 2 exit 的 7/7 事实核验固化为 CP8 / formal exit 义务，并把 FU-007 的 007a/007b 仅登记为后续提案。 |

## 状态

- 文档状态：awaiting-cp2（CR169 产品基线增量）
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168` / `CR-169`
- 当前门禁：CR169 CP2 待人工批准；CP2 前不得进入 HLD/CP3、Story、LLD、实现或验证
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
| REQ-CR168-001 | Versioned typed C3 component | P0 | awaiting-CP2 | 复用 CR166 envelope，把 `economic_cost@reserved` 演进为 1 个 active typed component / 1 个 schema version，不新建平行 gate/envelope/registry。 |
| REQ-CR168-002 | Nine-family explicit input contract | P0 | awaiting-CP2 | 9/9 字段族均有 required/optional/N/A/authorization 规则，含 cost-underestimation assumptions/limitations。 |
| REQ-CR168-003 | Transparent cost and impact approximation | P0 | awaiting-CP2 | 透明输出 fee/tax/spread/slippage/impact approximation、total、gross-to-net、availability、reason、lineage 和 `cost_underestimation_status`。 |
| REQ-CR168-004 | Ten-class fail-closed validation | P0 | awaiting-CP2 | 10/10 指定缺失、数值、basis、算术、lineage/auth 和 hash tamper 类别均不得产生 present/PASS。 |
| REQ-CR168-005 | Deterministic canonical identity | P0 | awaiting-CP2 | 同一规范化输入 10 次只产生 1 个 canonical hash，tamper 必须 blocked。 |
| REQ-CR168-006 | Joint Gate 4 C3 projection | P0 | awaiting-CP2 | 只投影 C3 四字段；C4 unavailable 映射为三个 refs absent-no-na-reason；字段级/通用 na-reason 逃逸由 projection 阻断；capacity/aggregate PASS=0。 |
| REQ-CR168-007 | Multi-strategy-type fixtures | P0 | awaiting-CP2 | daily multifactor synthetic 与 daily/ML compatibility 两族 2/2；event-specific producer=0。 |
| REQ-CR168-008 | Authorization and claim ceiling | P0 | awaiting-CP2 | 禁止真实数据/TCA/calibration/runtime/trading/remote write；Stage2=true、Stage3=false，其余真实/运行时 claim=false/0。 |
| REQ-CR168-009 | C4/FU-007/CR155 boundary | P0 | awaiting-CP2 | C4 calculator=0；aggregate integration 留给 FU-007；CR155 admission promotion=0。 |
| REQ-CR169-001 | Versioned typed C4 component | P0 | awaiting-CP2 | `capacity_liquidity@v1` component/schema=1/1；平行 envelope/registry/gate=0。 |
| REQ-CR169-002 | Independent C4 input and correlation header | P0 | awaiting-CP2 | C4 calculation body 独立，最小 correlation header 待 CP3 冻结且不默认进入 semantic hash。 |
| REQ-CR169-003 | Transparent static C4 proxy | P0 | awaiting-CP2 | 仅 synthetic/static ADV/reference、participation、capacity/liquidity sizing 与 auditable refs。 |
| REQ-CR169-004 | Twelve-class fail-closed validation | P0 | awaiting-CP2 | 12/12 输入、完整性、reason escape 与越权类别不得产生 present/PASS。 |
| REQ-CR169-005 | Deterministic C4 identity | P0 | awaiting-CP2 | 规范化输入 10 次→1 hash；tamper blocked。 |
| REQ-CR169-006 | Strict C3+C4 Gate 4 fixture compatibility | P0 | awaiting-CP2 | 新 adapter 精确组合 verified C3/C4；fixture contract PASS 仅为 1，aggregate/capacity admission PASS=0。 |
| REQ-CR169-007 | C3-only regression and fixtures | P0 | awaiting-CP2 | 2/2 fixture；CR168 C3-only absent-C4 fail-closed 不变。 |
| REQ-CR169-008 | Authorization and claim ceiling | P0 | awaiting-CP2 | 真实数据/calibration/runtime/trading/remote write=0；Stage3=false。 |
| REQ-CR169-009 | Alpha/verifier/FU-007/CR155 boundary | P0 | awaiting-CP2 | alpha CP3 disposition；canonical/global/aggregate 留 FU-007；CR155 BLOCKED。 |

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
| DQ-CP2-CR166-SCOPE | scope | 是否批准 fixture/static C2 foundation、8 类 P0 与 Stage 3 claim ceiling？ | 批准；真实 fold/OOS 数据与 Stage 3 启动另起 CR。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-EXTENSION | architecture-boundary | 是否只预留 C3/C4 versioned typed component 扩展点？ | 只冻结兼容约束，不实现或验证 C3/C4 计算。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-COMPATIBILITY | scope | event 是否与 daily/ML 同列 P0？ | daily + ML 为 P0；event 为 P1 applicability，语义未冻结时 N/A。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR166-AUTHZ | security | CP2 是否授权真实数据/runtime/外部系统或实现？ | 不授权；CP2 后只进入 CP3，CP5 后才可 fixture/static 实现。 | resolved-approved 2026-07-13 |
| DQ-CP2-CR168-METHOD | scope / methodology | C3 是否包含透明 impact approximation？ | 包含 fee/tax/spread/slippage/impact 分解，但 impact 只使用显式静态参数；备选为延后 impact。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-C3-C4 | architecture-boundary | 是否冻结 C3/C4 最小共享 header？ | 冻结最小共享 header；C4 专属字段 reserved，C4 calculator=0。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-GATE4 | integration-boundary | existing-gate integration 做到何种粒度？ | 只做 1 条 C3-to-Gate-4 compatibility projection；C4 reserved/not-built/typed_unavailable 映射为三个 refs absent；CR168 adapter 用精确 8-key denylist、strict allowlist、调用前拒绝和调用后非 PASS 断言局部封堵 reason 逃逸；不修改或宣称全局修复 canonical Gate 4。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-FIXTURE | compatibility | fixture 适用面是什么？ | 2 族：daily multifactor synthetic + daily/ML multi-strategy-type compatibility；event N/A/deferred。 | resolved-approved 2026-07-14 |
| DQ-CP2-CR168-CLAIM | claim-ceiling | CP2 是否改变 Stage/真实能力声明？ | 不改变：Stage2=true、Stage3=false；真实 TCA/impact calibration/data/runtime/C4/event/CR155 promotion=false/0。 | resolved-approved 2026-07-14 |

## CR166 Walk-forward / OOS Producer Requirements

| REQ ID | 标题 | 优先级 | 可验证要求 |
|---|---|---|---|
| REQ-CR166-001 | Typed fold input contract | P0 | fold manifest、split policy、train/validation/OOS bounds、purge/embargo、metrics、lineage refs 7/7 字段族有 schema 与 validation result。 |
| REQ-CR166-002 | Temporal and leakage boundary | P0 | 时间逆序、purge 缺失、embargo 不足 3/3 fail-closed，reason code 不为空。 |
| REQ-CR166-003 | Fold/metric sufficiency | P0 | 缺 fold、metric 缺失、NaN/Inf 3/3 不产生 present/PASS；valid fold 分母与 pass-rate 可重算。 |
| REQ-CR166-004 | Lineage integrity | P0 | lineage 缺失、ref/hash/membership 不一致 100% typed_unavailable 或 blocked；orphan refs=0。 |
| REQ-CR166-005 | Deterministic C2 envelope | P0 | 相同规范化 fixture 10 次只产生 1 个 canonical hash；header + versioned typed component 保持稳定。 |
| REQ-CR166-006 | Future C3/C4 compatibility | P0 design constraint | 支持注册式 versioned C3/C4 component 扩展；未知/未注册 component 不能满足 mandatory evidence 或产生 PASS；当前 C3/C4 calculators=0。 |
| REQ-CR166-007 | Existing-consumer projection | P0 | statistical gate、cross-strategy reliability gate、StrategyAdmissionPackage 3/3 使用同一 C2 refs/availability/reasons；不新建 gate。 |
| REQ-CR166-008 | Strategy compatibility | P0/P1 | daily multifactor 与 ML purged-embargo compatibility 2/2；event 在 CP3 完成 applicability decision，未冻结语义时为 N/A 而非假覆盖。 |
| REQ-CR166-009 | Deny-default authorization and Stage claim | P0 | external/real-data ref 解引用=0，forbidden counters=0；Stage 2 保持 complete，Stage 3 started/runtime-authorized/real-evidence-available 均为 false。 |

## CR166 Quantitative Acceptance Criteria

| QAC | 指标 | 目标 |
|---|---|---:|
| QAC-CR166-01 | P0 fail-closed 类别覆盖 | 8/8 |
| QAC-CR166-02 | daily + ML P0 fixture 族 | 2/2 |
| QAC-CR166-03 | event applicability 决策 | 1/1；实现可为 N/A |
| QAC-CR166-04 | typed input 字段族 | 7/7 |
| QAC-CR166-05 | temporal/leakage 负向类 | 3/3 blocked |
| QAC-CR166-06 | lineage negative coverage | 100% fail-closed，orphan=0 |
| QAC-CR166-07 | deterministic reruns | 10 次→1 hash |
| QAC-CR166-08 | existing-consumer projection | 3/3 |
| QAC-CR166-09 | C3/C4 calculators in CR166 | 0 |
| QAC-CR166-10 | external dereference / forbidden operations | 0 / 0 |
| QAC-CR166-11 | Stage claim flags | Stage2 complete=true；Stage3 started=false；real evidence available=false |
| QAC-CR166-12 | repository regression | CR166 新增代码路径引入失败=0；若触及 CR165 已重基线历史路径，CP7 必须逐项列出触发、归因与非回归理由 |

## CR166 CP3 Design Obligations

状态：`RESOLVED`（2026-07-13，CP3 人工批准；决策引用 `DQ-CP3-CR166-001..004`）。以下义务原文保留用于追溯，并作为 CP4/CP5 的强制设计输入。

1. 冻结 C2 envelope header、versioned component registry、canonical serialization 与 unknown-component decision table。
2. 冻结 fold 时间边界、purge/embargo 下限和 daily/ML policy 映射；event-time 语义单独作 applicability decision。
3. 显式定义 producer→三个 consumers 的调用方向、时机、输入、输出、降级与同步修改面。

## CR168 Economic Cost / Slippage / Impact Producer Requirements

### REQ-CR168-001 Versioned Typed C3 Component

- 必须复用 CR166 neutral strategy evidence envelope 和 canonical serialization/hash；不得创建平行 envelope、evidence registry 或 admission gate。
- `economic_cost@reserved` 只演进为 `1` 个 active typed C3 component，active schema version 为 `1` 个。
- 未注册/未知 component 不得满足 mandatory C3 evidence 或产生 Gate 4/aggregate PASS。

成功标准：typed C3 component 类型 `1`；active schema version `1`；平行 gate/envelope/registry `0`。

### REQ-CR168-002 Nine-Family Explicit Input Contract

输入合同必须精确覆盖 `9/9` 字段族：

1. manifest/run/strategy identity；
2. gross return 或 pre-cost performance basis；
3. trade、position change、turnover、notional basis；
4. commission/fee assumptions；
5. tax/levy assumptions；
6. spread/slippage assumptions；
7. impact model family/parameters 或 structured N/A，以及 `cost_underestimation_status`、model assumptions、structured limitations；
8. unit、currency、calendar、price/notional basis 与显式 conversion declaration；
9. lineage、provenance、authorization refs。

每个字段族必须有 required/optional/N/A/authorization 规则。C3/C4 可共享 identity、basis 与 lineage 的最小 header；capacity curve、ADV participation、liquidity sizing、alpha decay 字段由 C4 独占。

成功标准：9/9 字段族规则均可机器检查；C4 专属字段由 C3 计算的数量为 `0`。

### REQ-CR168-003 Transparent Static Cost and Impact Approximation

- 只允许使用显式传入的合成或静态参数，确定性计算 commission/fee、tax/levy、spread/slippage、impact approximation、total cost 与 gross-to-net reconciliation。
- 输出必须携带 availability/outcome、reason codes、lineage/provenance、model/version、`cost_underestimation_status`、`no_real_tca_claim=true`、structured limitations 与 canonical identity。
- impact approximation 不得被描述为真实 TCA、真实成交还原或经市场校准的 impact。

成功标准：每个 present C3 component 的成本分项、total 与 net 算术可重算；真实 TCA/market calibration claim 数为 `0`。

### REQ-CR168-004 Ten-Class Fail-Closed Validation

以下 `10/10` P0 类别必须分别形成 machine-readable reason，且不得产生 present/PASS：

1. 缺 gross/pre-cost basis；
2. 缺 trade/turnover/notional basis；
3. 缺 cost model/version；
4. 非有限值；
5. 未经策略允许的负成本或不可能数值；
6. unit/price/notional basis 不一致；
7. currency/price-basis/calendar 跨字段不一致且无显式汇率/转换声明；
8. gross/cost/net 算术不一致；
9. lineage/provenance/authorization 缺失或不一致；
10. canonical identity/hash tamper。

成功标准：10/10 类各有正交 negative fixture；false PASS 数为 `0`。

### REQ-CR168-005 Deterministic Canonical Identity

- 规范化、字段排序、数值编码、N/A 表达和 optional component 顺序必须确定。
- 同一规范化输入、schema/model version 与参数重复运行 `10` 次，必须只产生 `1` 个 canonical hash。
- 任何字段 tamper 后保留旧 hash 的输入必须 blocked；语义等价规范化输入不得因键顺序变化产生不同 hash。

成功标准：`10 runs -> 1 hash`；tamper false negative 数为 `0`。

### REQ-CR168-006 Joint Gate 4 C3 Compatibility Projection

- Gate 4 canonical 名称为 `GATE_4_CAPACITY_IMPACT`，是 C3+C4 联合门禁，不是 C3-only gate。
- CR168 的 `1` 条 compatibility projection 只能提供 C3 字段：`impact_model_family`、`impact_model_ref`、`cost_underestimation_status`、`no_real_tca_claim`。
- Envelope 中 C4 `reserved/not-built/typed_unavailable` 必须在 projection 输出中翻译为 `adv_participation_ref`、`capacity_dollars_ref`、`liquidity_sizing_refs` 三个字段 absent；不得输出与这三个字段相关的 `*_na_reason`、`*_n_a_reason`，也不得输出通用 `na_reason` 或 `n_a_reason`。
- CR168 adapter 必须按 key presence 精确拒绝以下 `8/8` 键：`adv_participation_ref_na_reason`、`adv_participation_ref_n_a_reason`、`capacity_dollars_ref_na_reason`、`capacity_dollars_ref_n_a_reason`、`liquidity_sizing_refs_na_reason`、`liquidity_sizing_refs_n_a_reason`、`na_reason`、`n_a_reason`；不得依赖私有 helper `_has_na_reason`，也不得把任意上游 mapping 直接透传。
- 任何字段级或通用 na-reason 逃逸输入必须在调用 canonical Gate 4 前由 projection `BLOCKED/REJECTED`，该路径的 canonical 调用数必须为 `0`。合法 absent-no-na-reason 路径调用后必须断言 Gate 4 不是 PASS；若出现意外 PASS，adapter 必须返回内部合同错误/阻断结果。
- 本 CR 的整改是 projection 入口局部 containment，不修改 `GATE_4_CAPACITY_IMPACT` canonical validator 或 aggregate orchestration，也不声明绕过 adapter 的未来直接调用已安全；全局语义复核归属 `FU-CR161-007` 或独立治理 CR。

成功标准：C3-to-Gate-4 projection `1`；合法 absent-no-na-reason 路径与 reason 逃逸负向路径均产生 capacity/aggregate PASS `0`；C1-C4 aggregate orchestration `0`。

### REQ-CR168-007 Multi-Strategy-Type Fixture Compatibility

- fixture 族精确为 `2/2`：1 个 daily multifactor synthetic economic-cost fixture；1 个同时验证 daily multifactor 与 ML package attach 的 multi-strategy-type compatibility fixture。
- 两种 strategy type 必须共享相同成本算术、basis、availability、reason 与 hash 语义；strategy-type 差异不得改变 C3 cost 定义。
- event-specific economic-cost 语义显式 N/A/deferred，event producer 数为 `0`。

成功标准：fixture 族 `2/2`；event-specific producer `0`；真实 model training/event feed 调用 `0`。

### REQ-CR168-008 Authorization and Claim Ceiling

- 本 CR 不授权 lake/NAS/provider/data vendor、credential/secret、真实 order/fill/quote/book/flow/ADV/liquidity、历史灌入/回填/校准、external runtime、broker/trading、catalog/store/registry pointer、publish/deploy/release/tag/push。
- CP2 approval 只允许进入 CP3 solution design，不授权实现；CP5 前不得实现。
- claim ceiling 固定：`stage2_complete=true`、`stage3_started=false`、`c3_fixture_static_foundation=false`（直至实际完成）、`real_tca_available=false`、`real_market_impact_calibrated=false`、`real_data_connected=false`、`runtime_ready=false`、`c4_calculators=0`、`event_specific_producer=false`、`cr155_promoted=false`。

成功标准：真实数据读取、真实 TCA、外部 runtime、broker/trading、Git remote write 等禁止操作计数分别为 `0`；overclaim 数为 `0`。

### REQ-CR168-009 C4, FU-007 and CR155 Regression Boundary

- C4 capacity curve、ADV participation、liquidity sizing、alpha decay calculator 保留给 `FU-CR161-005`，CR168 实现数为 `0`。
- C1-C4 aggregate orchestration、StrategyAdmissionPackage 最终聚合、existing-gate 全链路 integration 与 CR155 综合 regression/promotion decision 保留给 `FU-CR161-007`。
- CR155 formal CR lifecycle 已关闭，但现有 admission package 必须保持 `BLOCKED` 且 `paper_candidate=false`；C3 结果不得提升、解除或重解释。

成功标准：C4 calculator `0`；aggregate integration `0`；CR155 admission 状态提升 `0`。

## CR168 Quantitative Acceptance Criteria

| QAC | 指标 | 精确目标 | 失败行为 |
|---|---|---:|---|
| QAC-CR168-01 | 正式 C3 typed component 类型 | 1 | 非 1 阻断 CP7 |
| QAC-CR168-02 | active C3 schema version | 1 | 多版本并行 active 或缺版本阻断 |
| QAC-CR168-03 | 输入字段族规则覆盖 | 9/9 | 任一族无 required/optional/N/A/auth 规则阻断 |
| QAC-CR168-04 | fixture 族 | 2/2 | 任一族缺失阻断 |
| QAC-CR168-05 | P0 fail-closed 类别 | 10/10 | 任一类别 false PASS 阻断 |
| QAC-CR168-06 | deterministic reruns | 10 次 -> 1 canonical hash | hash 漂移或 tamper 漏检阻断 |
| QAC-CR168-07 | C3-to-Gate-4 compatibility projection | 1 | 缺投影或越界填充 C4 阻断 |
| QAC-CR168-08 | C4 缺失产生的 capacity/aggregate PASS | 0 | 任一 PASS 阻断 |
| QAC-CR168-09 | 新建平行 gate/envelope/registry | 0 | 任一新增阻断 |
| QAC-CR168-10 | C4 calculator | 0 | 任一实现阻断 |
| QAC-CR168-11 | event-specific producer | 0 | 任一实现阻断 |
| QAC-CR168-12 | 真实数据/TCA/runtime/broker/trading 操作 | 各 0 | 任一非 0 阻断 |
| QAC-CR168-13 | CR155 admission 状态提升 | 0 | 任一提升阻断 |
| QAC-CR168-14 | CR168 新增代码路径引入的测试失败 | 0 | 无法证明为既有问题时不得过 CP7 |
| QAC-CR168-15 | 带 process 前缀的错误质量引用 | 0 | 任一引用必须修正到 `docs/quality/` |

## CR168 Non-Functional Requirements

| NFR ID | 维度 | 要求 | 精确度量 |
|---|---|---|---|
| NFR-CR168-001 | 可审计性 | 所有分项、total、gross-to-net、model assumptions 与 limitations 可由输入重算。 | present component 的算术重算一致率 100%；orphan refs=0。 |
| NFR-CR168-002 | 确定性 | canonical serialization 对字段顺序与规范化等价输入稳定。 | 10 次执行仅 1 个 hash；tamper 检出率 100%。 |
| NFR-CR168-003 | 安全与权限 | fixture/static 路径不执行真实数据/runtime/trading/remote write。 | 每个 forbidden-operation counter=0。 |
| NFR-CR168-004 | 可演进性 | C3 复用 neutral envelope，最小共享 header 不占用 C4 专属语义。 | 平行 envelope/registry/gate=0；C4 calculator=0。 |

## CR168 CP3 Design Obligations

状态：`IN_PROGRESS_CP3`（CP2 于 2026-07-14 批准；以下作为 CP3 强制设计输入，尚未构成实现授权）。

1. 冻结 9 字段族的具体 schema、normalization、N/A、reason-code 与 numeric domain。
2. 冻结透明 impact approximation 的方法族、参数表达、`cost_underestimation_status` decision table 和 no-real-TCA wording。
3. 冻结 C3/C4 最小共享 header 与 C4-exclusive field ownership；禁止 C3 预占 capacity/ADV/liquidity/alpha-decay calculator。
4. 冻结 C3 producer → neutral envelope → Gate 4 compatibility projection 的调用方向、时机、输入、输出、降级和调用方同步修改面；canonical Gate 4 validator 与 aggregate orchestration 不在修改面。
5. 冻结 envelope availability 到 Gate 4 扁平 payload 的完整映射表：C3 `PRESENT/TYPED_UNAVAILABLE/BLOCKED` 与 C4 `reserved/not-built/typed_unavailable` 分别如何映射；C4 unavailable 的唯一安全映射为三个 refs absent-no-na-reason。
6. 冻结 projection-side reason-key denylist 与失败合同：精确 `8/8` 禁止键按 key presence 触发 `BLOCKED/REJECTED`；禁止对任意上游 mapping 盲目透传；reason 逃逸路径 canonical 调用数=`0`，并由 `SC-CR168-B02` 验证 Gate 4/capacity/aggregate PASS=`0`。
7. 处理当前 capability registry 缺失：优先记录 N/A-with-reason 并使用既有 feature/module refs；不得为了 CR168 新建平行 registry。若证明必须建立项目级 registry，转独立治理 CR 后再决定。
8. 把 `fixture_static_c3_typed_component`、`c3_gate4_compatibility_projection`、`cr155_admission_blocked_regression` 映射到既有结构化 evidence kind/taxonomy 或写出明确 N/A/替代验证路径；不得等到 CP7 才发现未知 kind。
9. 冻结 `impact_model_family=n/a-with-reason` 的合法 C3 条件：必须使用 impact 专属 reason/claim-limit/owner/trigger，不得输出通用或 C4 字段 na-reason；C3 可有效但 Gate 4 仍因 C4 absent 而 fail-closed，并在 CP5 场景/测试设计中保留验证。
10. 分离并冻结 component semantic hash 与完整 envelope canonical hash 的输入域；strategy type 不得改变相同规范化 C3 成本语义，但 subject/provenance/auth 不同的完整 envelope hash 允许不同，不新增“跨 strategy type 完整 hash 必须相同”的模糊 QAC。
11. 冻结 CR168 adapter-only 调用面：CR168 新增的 Gate 4 调用必须 `100%` 经过 projection adapter，adapter 外直接调用数=`0`；不得在运行时导入或依赖私有 `_has_na_reason`。
12. 冻结调用后安全断言：C4 unavailable 的合法 absent-no-na-reason 路径进入 canonical validator 后，Gate 4 status 必须为非 PASS；意外 PASS 必须转为内部合同错误/阻断，不得继续 aggregate。该断言不等价于 canonical Gate 4 已全局修复。
13. 将 canonical Gate 4 的全局 N/A 语义复核登记到 `FU-CR161-007`：任何未来绕过 CR168 adapter 的直接调用或 aggregate integration 前，必须重新评估并决定是否独立硬化 canonical validator。

## CR169 Capacity / Liquidity / ADV Producer Requirements

### CR169 需求清单

| Requirement ID | 名称 | 优先级 | 状态 | 精确要求 |
|---|---|---:|---|---|
| REQ-CR169-001 | Versioned typed C4 component | P0 | awaiting-CP2 | `capacity_liquidity@reserved` 只演进为 `1` 个 active C4 component / `1` 个 schema；平行 envelope/registry/gate=0。 |
| REQ-CR169-002 | Independent C4 input and correlation header | P0 | awaiting-CP2 | C4 计算字段独立；最小 C3/C4 correlation header 覆盖 identity、basis、currency、calendar、as-of、horizon、lineage/auth；CP3 冻结其规则，且不得默认进入 component semantic hash。 |
| REQ-CR169-003 | Transparent static C4 proxy | P0 | awaiting-CP2 | 仅显式 synthetic/static ADV/reference basis、participation cap、capacity curve 和 liquidity sizing 输出可审计 C4 proxy、refs、availability、reason、limitations 与 lineage。 |
| REQ-CR169-004 | Twelve-class fail-closed validation | P0 | awaiting-CP2 | 12/12 指定缺失、数值、关联、完整性、reason escape 与越权类别不得产生 present/PASS。 |
| REQ-CR169-005 | Deterministic C4 identity | P0 | awaiting-CP2 | 同一规范化 C4 输入运行 10 次只产生 1 个 canonical hash；tamper 必须 blocked。 |
| REQ-CR169-006 | Strict C3+C4 Gate 4 fixture compatibility | P0 | awaiting-CP2 | 新 joint adapter 只组合已验证的 `economic_cost@v1` + `capacity_liquidity@v1`，重建精确七字段 payload；有效 fixture 可产生 `gate4_fixture_contract_pass`，但 aggregate/capacity admission PASS=0。 |
| REQ-CR169-007 | C3-only regression and multi-strategy fixtures | P0 | awaiting-CP2 | 2/2 fixture 族；CR168 C3-only adapter 仍以 absent C4 fail-closed；C4 present 不得进入该 adapter。 |
| REQ-CR169-008 | Authorization and claim ceiling | P0 | confirmed-CP2 | real ADV/liquidity/data/calibration/runtime/trading/remote-write=0；`stage2_complete=true` 不蕴含可进入 Stage 3，`stage3_started=false`、`stage3_entry_ready=false`；真实能力 claim=false。 |
| REQ-CR169-009 | Alpha, verifier, FU-007, Stage exit and CR155 boundary | P0 | confirmed-CP2 | alpha-decay 只在 CP3 决定归属；CP8 / formal Stage 2 exit 前必须输出 `STAGE2-EXIT-VERIFICATION.result.json` 并核验 7/7 合同；FU-006 风险 CP8 披露；FU-007 的潜在 007a/007b 拆分只属后续提案，任何启动均需独立 CR/CP0/用户授权；CR155 保持 BLOCKED 与 `paper_candidate=false`。 |

### CR169 P0 fail-closed 分类

`12/12`：关联头缺失；synthetic ADV/reference basis 缺失；participation cap/method 缺失或非法；capacity model/ref 缺失；liquidity sizing/ref 缺失；非有限/负值/不可行数值；unit/currency/calendar/as-of/horizon 跨字段不一致；C3/C4 correlation mismatch；lineage/provenance/authorization 缺失或不一致；canonical identity/hash tamper；C4 N/A reason 或任意 flat-payload injection；真实数据/真实容量/runtime 越权声明或操作。

### CR169 Quantitative Acceptance Criteria

| QAC ID | 指标 | 目标值 | 失败处理 |
|---|---|---:|---|
| QAC-CR169-01 | 正式 C4 typed component 类型 | 1 | 非 1 阻断 CP7 |
| QAC-CR169-02 | active C4 schema version | 1 | 缺失或多 active 阻断 |
| QAC-CR169-03 | Gate 4 C4 refs | 3/3 | 任一缺失阻断 joint fixture contract |
| QAC-CR169-04 | C3/C4 correlation header 合同 | 1 | CP3 未冻结不得进入实现 |
| QAC-CR169-05 | fixture 族 | 2/2 | 任一缺失阻断 |
| QAC-CR169-06 | P0 fail-closed 类别 | 12/12 | 任一 false PASS 阻断 |
| QAC-CR169-07 | deterministic reruns | 10 次 -> 1 hash | 漂移或 tamper 漏检阻断 |
| QAC-CR169-08 | CR168 C3-only absent-C4 回归 | 1 | 行为变更阻断 |
| QAC-CR169-09 | strict C3+C4 Gate 4 fixture contract PASS | 1 | 缺失或非严格 payload 阻断 |
| QAC-CR169-10 | capacity/aggregate admission PASS、real-capacity claim、CR155 promotion、`stage3_entry_ready` | 0/0/0/false | 任一非零或 true 阻断 |
| QAC-CR169-11 | canonical Gate 4 / aggregate orchestration 修改 | 0/0 | 任一修改阻断 |
| QAC-CR169-12 | real data/calibration/runtime/broker/trading 操作 | 0 | 任一非零阻断 |
| QAC-CR169-13 | alpha-decay calculator（CP3 未归入时） | 0 | 任一实现阻断 |
| QAC-CR169-14 | CR169 新增路径引入的测试失败 | 0 | 无法归因既有问题时不得过 CP7 |
| QAC-CR169-15 | 带错误 `process/` 前缀的质量文档引用 | 0 | 必须修正到 `docs/quality/` |

### CR169 Non-Functional Requirements

| NFR ID | 维度 | 要求 | 精确度量 |
|---|---|---|---|
| NFR-CR169-001 | 可审计性 | C4 proxy、三个 refs、limitations、correlation 与 lineage 均可由 static input 重算。 | present component 重算一致率 100%；orphan refs=0。 |
| NFR-CR169-002 | 确定性 | 规范化、canonical serialization 与 hash 对等价输入稳定。 | 10 次仅 1 hash；tamper 检出率 100%。 |
| NFR-CR169-003 | 安全与权限 | 禁止真实数据、真实容量校准、runtime/trading/remote write。 | 每个 forbidden-operation counter=0。 |
| NFR-CR169-004 | 可演进性 | C4 复用 neutral envelope；joint adapter 不侵入 CR168 adapter/canonical Gate 4/aggregate。 | 三个既有边界修改数=0；C4 semantic hash 不被 correlation header 隐式污染。 |

### CR169 CP3 Design Obligations

状态：`CP2_APPROVED`。CP2 批准后，CP3 必须：

1. 冻结 C4 static proxy 的方法族、numeric domain、participation 边界、reason-code 与 no-real-ADV/capacity wording。
2. 冻结 minimal C3/C4 correlation header 的 owner、required/optional、cross-component equality 与它不进入 component semantic hash 的规则。
3. 冻结 strict joint adapter 的调用方向、type/version/identity/limitation checks、精确七字段 payload、denylist/allowlist、canonical postcondition 与降级行为；不得改变 CR168 adapter 或 canonical Gate 4。
4. 决定 alpha-decay 的归属（C4、C2 或独立 CR）并回写 Deferred 状态；未归入时维持 calculator=0。
5. 冻结 FU-006 verifier independence 的 CP8 披露模板与触发条件；不得把 fixture contract PASS 表述为真实 capacity readiness。
6. 保留 `stage3_entry_ready=false`，在设计中引用 CP8 / formal Stage 2 exit 的 `STAGE2-EXIT-VERIFICATION.result.json`（7/7）；仅把 FU-007 007a/007b 写作非绑定后续提案，不预建 CR、不修改 canonical Gate 4。
