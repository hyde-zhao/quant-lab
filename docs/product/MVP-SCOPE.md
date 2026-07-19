# MVP Scope

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 MVP 范围草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 统一 scope、out-of-scope 和 promoted deferred 映射。 |
| v0.3 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review design-only scope，并将 `DF-CR157-003` promoted to CR160。 |
| v0.4 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 evidence availability 产品范围、fail-closed ceiling、CR155 regression 和 deferred producers。 |
| v0.5 | 2026-07-11 | meta-pm | CR163 增量追加 trial lineage MVP、冻结入口清单、量化验收、排除项与 deferred 统计/回填/real-runner 项。 |
| v0.6 | 2026-07-11 | meta-pm | 回填 SGQ-A，归一化为 2 条 producer chains / 4 mappings，并明确 ExperimentFamilyManifest availability 与 C1 raw-input-only ceiling。 |
| v0.7 | 2026-07-12 | meta-pm | 增量追加 CR164 四方法 MVP、方法充分性、量化 AC、保守聚合、effective-count ceiling、consumer compatibility 与 deferred 范围。 |
| v0.8 | 2026-07-13 | host-orchestrator-inline | 增量追加 CR166 C2 fixture/static foundation、future component compatibility、P0/P1 分层、Stage 3 claim ceiling 与明确排除项。 |
| v0.9 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 批准；MVP 范围成为 CP3 正式输入，真实数据、C3/C4 计算、event producer 与 Stage 3 仍明确排除。 |
| v1.0 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 批准；范围映射到五个正式 Story，保持 fixture/static、event N/A、C3/C4 calculator=0 与 Stage 3 未启动。 |
| v1.1 | 2026-07-13 | host-orchestrator-inline | CR168 增量追加 fixture/static C3 typed component、9 字段族、10 类 fail-closed、两类 fixture、联合 Gate 4 投影、claim ceiling 与 C4/FU-007 边界。 |
| v1.2 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见收紧 Gate 4 projection-side guard：C4 unavailable 映射为 absent-no-na-reason，reason 逃逸必须阻断；新增 1 个 P0 场景，不改变 6 项 CR168 MVP scope 或 15 项 QAC。 |
| v1.3 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准；明确 Gate 4 整改只发生在 CR168 adapter 入口，以 8-key denylist、strict allowlist、前置拒绝和后置非 PASS 断言局部封堵，canonical 全局硬化继续 deferred。 |
| v1.4 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 C4 fixture/static MVP、strict C3+C4 joint adapter、12 类 fail-closed、alpha-decay CP3 disposition 与真实能力 claim ceiling；不改变 CR168 adapter 或 FU-007 owner 边界。 |
| v1.5 | 2026-07-14 | host-orchestrator-inline | CR169 CP2 评审整改与批准：补 `stage3_entry_ready=false`、7/7 Stage 2 exit 核验义务，以及 FU-007 007a/007b 的非绑定后续提案；不扩大 MVP 或授权。 |
| v1.6 | 2026-07-15 | host-orchestrator-inline-meta-pm | 增量追加 CR170 Gate 1-5 N/A semantics、Gate 6 protected merge/admission hardening、21-unit inventory 与明确的 runner/aggregate/Stage3 排除边界。 |
| v1.7 | 2026-07-15 | host-orchestrator-inline | 回填 CR170 CP2 批准；future verifier 只作为 FU-006 consumer contract，不声明本 CR verifier independence；范围、目标、量化验收和授权边界不变，进入 CP3 设计。 |
| v1.8 | 2026-07-15 | host-orchestrator | 回填 CR170 CP8 批准与 READY_WITH_RISK 关闭；21/21 policy inventory、Gate 1-5 N/A semantics、Gate 6 admission tier hardening 已交付，Stage3/aggregate/真实 evidence/runtime/CR155 promotion 仍未就绪。 |
| v1.9 | 2026-07-15 | meta-pm | CR171 增量追加 Stage 3 entry decision MVP、明确 out-of-scope 和 conditional follow-up；CP8 关闭只表示决策闭环，不启动真实数据/运行时行为。 |
| v2.0 | 2026-07-16 | meta-pm（pm-wu） | CR172 增量追加 C1-first 默认 MVP、PATH-B 恢复链、C2/C3 独立 CR 与联合审批边界；8 个 DQ 留 CP2。 |
| v2.1 | 2026-07-16 | meta-pm（pm-zheng） | CR173 增量追加 strategy-agnostic offline effective-trial MVP、七字段 evidence、六类 golden vectors、C1 projection 与 CR172 no-auto-resume 边界；8 个 DQ 留 CP2。 |
| v2.2 | 2026-07-16 | meta-pm（pm-zheng） | 按 CP3 条件分支将 CR173 MVP 收缩为 participation-ratio estimator-only + standalone 七字段 evidence；从 In Scope 移除 public C1 projection，并明确 CR172 其余数据/身份/runtime 前置不变。 |
| v2.3 | 2026-07-16 | host-orchestrator | 补齐 CR172/CR173 关联追溯；维持 CP3 待审、estimator-only 与 public C1 projection deferred 边界。 |
| v2.4 | 2026-07-17 | meta-pm（pm-wu） | CR172 在 prior-approved PATH-B 上增量加入 PATH-I instrumentation-first MVP、trial-return/NAS/stable URI、四组件 ownership、分动作授权、新路径和 empirical-R fail-closed；PATH-I 完成不自动恢复 activation。 |
| v2.5 | 2026-07-17 | host-orchestrator | CP2 发起前修正当前门禁：CR173 已 closed/cp8_closed，当前唯一产品门禁为 CR172 trial-return/deployment scope-delta CP2；范围与授权不变。 |
| v2.6 | 2026-07-17 | meta-pm（pm-wu） | correction R1 冻结 research-local canonical/NAS verified replica/execution immutable cache，并把 execution-local signal、EOD mailbox 与 intraday transport split 纳入 MVP/Deferred。 |
| v2.7 | 2026-07-17 | meta-pm（pm-wu） | correction R2 将当前信号范围收缩为本地默认、可选低频精确 8 字段 contract 与 intraday split；详细 exchange/ack/idempotency/path 实现转 Deferred；补 `FU-CR173-001` 条件前置和 CP2/3/5/7/8 阶段守卫。 |
| v2.8 | 2026-07-17 | meta-pm（pm-wu） | 回填 CR172 PATH-I scope-delta CP2 用户批准；MVP 内容、Deferred、成功指标与六类零授权不变，状态由 draft/pending 更新为 confirmed-CP2/ready-for-CP3。 |

## 状态

- 文档状态：confirmed-CP2（CR172 PATH-I scope delta；CR173 offline-methodology 作为已关闭历史保留）
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168` / `CR-169` / `CR-170` / `CR-171` / `CR-172` / `CR-173`
- 当前门禁：CR172 PATH-I scope-delta CP2 已于 `2026-07-17T16:54:09+08:00` 获用户批准；`ready_for_design=true`，当前只解锁 CP3 design-only。实现、真实数据、multi-trial、NAS 写入/同步、signal transport、迁移和 Git remote write 仍未授权。

## In Scope

| Scope ID | 内容 | 验收边界 |
|---|---|---|
| MVP-CR157-001 | Mature admission package builder 产品与设计范围 | 字段、输入 refs、输出 refs、blocked reasons、authorization flags 明确。 |
| MVP-CR157-002 | Stage 2/Stage 3 handoff hardening | Stage 2 support、Stage 3 research evidence、Stage 4 observation candidate 语义区分明确。 |
| MVP-CR157-003 | Research evidence index traceability | P0 evidence refs 可追溯，不复制大型证据正文。 |
| MVP-CR157-004 | No-runtime / no-publish guard | 禁用操作计数非 0 fail-closed。 |
| MVP-CR157-005 | Fixture/static validation plan | P0 场景均能以 fixture/static/no-lake 方式验证。 |
| MVP-CR158-001 | Unified event + ML adapter scope | 一个 CR 同时覆盖 event adapter 与 ML adapter，shared core 与 type-specific extension 明确。 |
| MVP-CR158-002 | Event adapter fixture/static contract | Event source refs、event-time alignment、signal output refs 和 blocked reasons 明确，且不读取真实 feed。 |
| MVP-CR158-003 | ML adapter fixture/static contract | Training snapshot refs、model artifact refs、prediction signal refs、validation refs 和 blocked reasons 明确，且不训练真实模型。 |
| MVP-CR158-004 | Evidence index typed refs | Event/ML evidence extension 保持 refs-only，不复制大型正文。 |
| MVP-CR158-005 | CR158 no-runtime validation | 禁用操作计数全部为 0；非 0 fail-closed。 |
| MVP-CR160-001 | Stage 4 observation review workflow design | ObservationReviewInput、EvidenceProfile、AdmissionReadiness、ObservationDecision、EscalationRoute 和 AuthorizationBoundary 的输入/输出/失败路径明确。 |
| MVP-CR160-002 | Observation plan template and instance boundary | CR160 定义 `observation_plan_template` 内容规范；Stage 3 产出 `observation_plan_instance`；review workflow 审查实例对模板的合规性。 |
| MVP-CR160-003 | 分层 observation review checklist | Checklist 覆盖 Stage 1 PIT/universe/lineage、Stage 2 factor methodology/typed unavailable、Stage 3 statistical gate/OOS/economic significance/rerun、横切 authorization/no-overclaim。 |
| MVP-CR160-004 | Fail-closed decision table | `contract_only`、`real_data_validated`、`runtime_authorized`、`unknown` 四条 evidence lane 均有可审查决策；`contract_only` lane 0 条路径可输出 `paper_candidate=true` 或 `simulation_ready`。 |
| MVP-CR160-005 | CR155 blocked seed classification | 既有 CR155 real lake validation evidence 只作为 fail-closed 样例消费，分类为 `blocked_admission_failed`，不执行新 lake 读取。 |
| MVP-CR160-006 | Product baseline traceability refresh | `USE-CASES`、`REQUIREMENTS`、`SCENARIOS`、`TEST-MATRIX`、`MVP-SCOPE`、`BACKLOG` 均记录 `DF-CR157-003` / `BL-CR157-003` promoted to CR160。 |
| MVP-CR161-001 | Seven-object evidence availability baseline | 当前基线可发现 C1-C4 对应七对象；每个对象有 availability、claim ceiling、gate integration 和 producer follow-up 说明。 |
| MVP-CR161-002 | Mandatory typed-unavailable fail-closed | 缺 trial lineage、p-values、fold metrics、成本或容量输入时，相关 evidence 为 `typed_unavailable` 并阻断。 |
| MVP-CR161-003 | CR155 negative regression | CR155 继续 `blocked`，不因 contract refresh、rerun consistency 或不可用新 evidence 而晋级。 |
| MVP-CR161-004 | Current-baseline reframe | CR162 刷新六个产品和三个 feature 文档；CR161 closed history 保留，仅标记为 reframed。 |
| MVP-CR163-001 | Pre-search family declaration and lifecycle | 2/2 P0 producer chains 在首个 trial 前声明 family；post-hoc declaration 全部 blocked。 |
| MVP-CR163-002 | Append-only trial/attempt/selection lineage | failed/cancelled/excluded/selected/rejected 全部保留；孤儿 trial 与孤儿 selection 为 0。 |
| MVP-CR163-003 | Raw count semantics | distinct trial identity 精确重算；retry 不增 raw count，不同 seed 增加；count mismatch blocked。 |
| MVP-CR163-004 | Deterministic seal and supersession | 同 fixture 10 次 seal 仅 1 个 hash；sealed 原地修改 0 次；纠错保留 version chain。 |
| MVP-CR163-005 | Frozen P0 producer inventory | 2 条去重 producer chains、CPI-CR163-001..004 4/4 instrumentation mappings；excluded/N/A paths 100% 有理由。 |
| MVP-CR163-006 | Existing-gate integration and negative regression | seal/completeness/ref/count/tamper 全通过才可 present；uninstrumented 为 typed_unavailable；invalid/tampered 为 blocked；仅 C1 raw-input-ready、C1 不可计算；CR155 仍 blocked。 |
| MVP-CR164-001 | Four-method computable-evidence contract | BH、WRC/SPA、PBO/CSCV、DSR 4/4 均有 method/input/output/provenance/availability 合同。 |
| MVP-CR164-002 | Validation-bound family/input identity | family/ref/hash/raw count 与 candidate/method inputs binding coverage 100%，count difference 0。 |
| MVP-CR164-003 | Method-specific sufficiency | BH/WRC-SPA >=2 candidates；PBO >=4 candidates/4 valid splits；DSR >=2 trials/sample_length>=30；所有输入有限且非退化。 |
| MVP-CR164-004 | Conservative method aggregation | claim-relevant mandatory methods 无 OR-pass；BH PASS + PBO FAIL 不得 clean PASS。 |
| MVP-CR164-005 | Raw-count DSR / effective-count ceiling | `dsr_input_method=raw_trial_count` 为 CP3 schema 义务；effective count 仍 typed_unavailable 且不得 alias。 |
| MVP-CR164-006 | Existing-consumer and compatibility projection | 复用 CR151/CR154/admission package；UC-58 implementation，UC-59/60 compatibility-only，consumer coverage 3/3。 |
| MVP-CR164-007 | Deterministic fail-closed verification contract | 10 reruns -> 1 hash；negative fail-closed 100%；CR155 1/1 blocked；forbidden counters/overclaims 0。 |
| MVP-CR166-001 | Common fold/OOS typed input contract | 7/7 输入字段族有 schema、validation 和 reason semantics。 |
| MVP-CR166-002 | Temporal/leakage fail-closed | 时间逆序、purge 缺失、embargo 不足 3/3 blocked；缺 fold/metric/lineage 同样不产生 PASS。 |
| MVP-CR166-003 | Deterministic typed C2 evidence | 10 reruns→1 canonical hash；fold-level reasons 与 pass-rate 可重算。 |
| MVP-CR166-004 | Versioned component compatibility | C3/C4 注册式扩展不破坏 C2；当前 C3/C4 calculators=0；unknown component 不得满足 mandatory evidence。 |
| MVP-CR166-005 | Existing consumer projection | CR151 statistical gate、CR154 reliability gate、StrategyAdmissionPackage 3/3 复用同一 evidence refs/availability；CR155 仍 blocked。 |
| MVP-CR166-006 | Strategy compatibility and claim ceiling | daily + ML 2/2 P0；event P1 applicability；external dereference=0；Stage2 complete，Stage3 not-started，real evidence unavailable。 |
| MVP-CR168-001 | Versioned typed C3 economic-cost component | 复用 CR166 envelope；component/schema=1/1；平行 gate/envelope/registry=0。 |
| MVP-CR168-002 | Nine-family static input and transparent arithmetic | 9/9 字段族；fee/tax/spread/slippage/impact/total/gross-to-net 可重算；含 `cost_underestimation_status`。 |
| MVP-CR168-003 | Ten-class deterministic fail-closed contract | 10/10 指定类别 false PASS=0；规范化输入 10 次→1 hash；tamper 检出率 100%。 |
| MVP-CR168-004 | Joint Gate 4 C3 compatibility projection | C3 投影=1；C4 refs absent-no-na-reason；adapter 8/8 禁止键拒绝、strict allowlist、逃逸路径 canonical 调用=0、safe absent 路径 post-call 非 PASS；capacity/aggregate PASS=0；C4 calculator=0；canonical Gate 4 修改=0。 |
| MVP-CR168-005 | Two fixture families and event boundary | daily multifactor synthetic + daily/ML compatibility=2/2；event-specific producer=0。 |
| MVP-CR168-006 | Authorization and claim ceiling | Stage2=true、Stage3=false；真实 TCA/calibration/data/runtime=false；CR155 admission promotion=0。 |
| MVP-CR169-001 | Versioned C4 typed component | `capacity_liquidity@v1` component/schema=1/1；平行 envelope/registry/gate=0。 |
| MVP-CR169-002 | Independent static C4 input and correlation header | C4 proxy input 独立；CP3 冻结一个最小 correlation header，且不默认污染 component semantic hash。 |
| MVP-CR169-003 | Deterministic C4 proxy and fail-closed contract | 12/12 fail-closed；同一规范化输入 10 次→1 hash；真实 ADV/capacity=0。 |
| MVP-CR169-004 | Strict C3+C4 Gate4 fixture compatibility | 新 joint adapter=1、三个 C4 refs=3/3、精确七字段 payload；仅 `gate4_fixture_contract_pass=1`，aggregate/capacity admission PASS=0。 |
| MVP-CR169-005 | CR168 regression and two fixtures | 2/2 fixture families；CR168 C3-only absent-C4 fail-closed 回归=1；C4 present 不进入旧 adapter。 |
| MVP-CR169-006 | Claim ceiling, Stage exit, alpha and CR155 boundary | Stage2=true 但 `stage3_entry_ready=false`、Stage3=false；CP8/formal Stage 2 exit 前 `STAGE2-EXIT-VERIFICATION.result.json=7/7`；alpha calculator=0（CP3 前）、canonical/aggregate 修改=0、CR155 promotion=0。 |
| MVP-CR170-001 | Gate 1-5 N/A policy inventory | 21/21 policy units；每项有 mandatory/conditional、owner、complete-boundary、result 规则。 |
| MVP-CR170-002 | Five-state evidence semantics | PRESENT/MISSING/COMPLETE-N/A/INCOMPLETE-N/A/GENERIC-ESCAPE=5/5；mandatory escape 的 unconditional PASS=0。 |
| MVP-CR170-003 | Gate 1 masked-escape and Gate 2-5 fail-closed | Gate 1 三层断言=3/3；Gate 2-5 applicable missing/generic/incomplete 全部非 PASS。 |
| MVP-CR170-004 | Protected merge and tiered admission | 现有 shared-summary NEEDS_REVIEW 传播回归=1；无失败不改；T0 NR、T1/T2 BLOCKED、T3 NOT_AUTHORIZED=4/4。 |
| MVP-CR170-005 | Compatibility and state correction | public break=0；CR168/169 adapter regressions=2/2；BACKLOG/baseline/legacy Stage3 marker 修正=3/3。 |
| MVP-CR170-006 | Authorization and claim ceiling | `stage3_entry_ready=false`；runner/aggregate/real-data/runtime/trading/remote-write/CR155 promotion=0。 |

## Out of Scope

| 对象 | 原因 |
|---|---|
| event strategy adapter implementation | 建议作为后续 CR；本轮只保持 adapter contract compatibility。 |
| ML strategy adapter implementation | 建议作为后续 CR；避免 CR157 扩大为横切策略类型重构。 |
| CR158 real event feed / live listener | CR158 只做 fixture/static adapter path，不授权真实 feed。 |
| CR158 real ML model training / external model service / model registry promotion | CR158 只做 fixture/static model refs，不授权训练或 registry 写入。 |
| real lake write / catalog publish / store or registry write | CR157 不授权生产写入。 |
| NAS / provider / credential access | CR157 不授权外部系统或秘密读取。 |
| QMT / MiniQMT / xtquant / gateway / broker / order / account | CR157 不授权运行时和交易。 |
| simulation / paper / live | CR157 只产生研究准入输入，不产生运行授权。 |
| Git remote write / publish / true release execution | CP8 也只能交付文档和本地证据，除非另有发布授权。 |
| CR160 code implementation / schema checker | CR160 走纯设计路径；checker/schema 可作为后续 CR 候选，不在本轮实现。 |
| CR160 new real lake read/write or CR155 promotion | CR160 只消费既有 CR155 evidence 作为反例样本，不授权新 lake 访问，也不把 CR155 升级为 paper/simulation candidate。 |
| CR160 Stage 5 paper/simulation authorization | Stage 4 design/gate contract 关闭后，Stage 5 gate 仍需后续 CR 独立授权。 |
| CR161 computed evidence producers | FDR/PBO/DSR、walk-forward/OOS folds、TCA/market impact、capacity/liquidity sizing 和 trial-lineage instrumentation 都需要独立实现型 CR。 |
| CR163 statistical correction / effective-trial computation | CR163 只提供 raw lineage facts，method/ref 保持空。 |
| CR163 historical lineage backfill | 不授权从历史产物推断并伪装成原生 instrumentation。 |
| CR163 real ML/event runner instrumentation | 当前只有 fixture/static adapter compatibility；没有获授权 real runner。 |
| CR163 real data/runtime/external writes | 不访问 lake/NAS/provider/credentials，不运行 simulation/paper/live/trading/broker，不写 remote/publish/catalog pointer。 |
| CR164 effective-trial estimator | SGQ 已确认不在 MVP；不得从 raw count 推导或别名。 |
| CR164 UC-59 ML / UC-60 event adapter implementation | 当前只保证 contract compatibility；不训练模型、不接 event feed、不新增 real runner。 |
| CR164 real statistical batch / historical recomputation | CP2 只冻结产品合同；不执行真实研究、历史 p-value/return/split 回填或数据迁移。 |
| CR164 external bootstrap framework run | WRC/SPA 参数在 CP3 设计；当前不安装或运行外部实现。 |
| CR166 real fold/OOS data ingestion or historical recomputation | 当前只接收显式 fixture/static 输入；不连接 lake/NAS/provider，不回填历史证据。 |
| CR166 C3/C4 computation | 只预留 versioned typed component 扩展点；经济成本、impact、capacity、liquidity、ADV、alpha decay 均不实现。 |
| CR166 event-specific producer | event-time/calendar-time 与窗口语义未冻结；CP3 可判 N/A，不交付空壳 producer。 |
| CR166 Stage 3 start or runtime authorization | CR166 关闭后 Stage 2 状态保持 complete；Stage 3 仍需独立 CR 和真实数据连接授权。 |
| CR168 真实 lake/NAS/provider/credential/data-vendor 或真实订单/成交/盘口/ADV/流动性访问 | 当前只消费显式 synthetic/static 输入；任何真实数据读取或参数估计均需独立授权。 |
| CR168 真实 TCA、真实成交还原或 market-impact calibration | impact 仅为透明静态 approximation，必须携带 `no_real_tca_claim=true` 与 limitations。 |
| CR168 C4 capacity/liquidity/ADV/alpha-decay calculator | 归属 `FU-CR161-005`；本 CR 数量固定为 0。 |
| CR168 canonical Gate 4 validator、C1-C4 aggregate integration / final StrategyAdmissionPackage / CR155 promotion decision | canonical validator 与 aggregate orchestration 均不修改；本 CR 的 adapter containment 不代表 canonical 已全局安全；端到端集成及绕过 adapter 前的 canonical N/A 语义复核归属 `FU-CR161-007`。 |
| CR168 event-specific producer | event-time/calendar/execution 语义未冻结；本 CR显式 N/A/deferred。 |
| CR168 runtime、broker/trading、catalog/store/registry pointer、publish/deploy/tag/release/Git remote write | 不在授权范围；所有相关操作计数为 0。 |
| CR170 current Stage 3 runner integration | 当前 runner 未调用 canonical Gate；接入必须由独立 Stage 3 Launch CR 决策和授权。 |
| CR170 aggregate orchestration / FU-CR161-009 | aggregate 与 mature SAP/CR155 综合决策保留给独立 follow-up。 |
| CR170 删除或简化 CR168/CR169 adapter guard | 本 CR 只作 regression；简化须满足 caller 全覆盖、fail-closed 不降低、全回归和 ADR 四条件。 |
| CR170 真实数据、Stage 3、runtime、broker/QMT/trading、publish/remote write | 全部不授权；CP2 仅批准产品范围，CP3 仅能设计。 |

## Deferred

| Deferred ID | 内容 | 推荐后续路径 |
|---|---|---|
| DF-CR157-001 | Event strategy adapter | 后续独立 CR，复用 `StrategyTypeAdapter` 合同。 |
| DF-CR157-002 | ML strategy adapter | 后续独立 CR，复用 `SignalSet` / `ResearchEvidenceIndex` 合同。 |
| DF-CR157-003 | Stage 4 observation review workflow | 已 promoted to `CR-160`；CR160 覆盖 Stage 4 review workflow design，不覆盖 Stage 5 simulation/paper/runtime authorization。 |
| FU-CR161-001..006 | Evidence producers and independent verifier lane | 保持 candidate；先满足输入 lineage/metrics/cost/capacity 和独立验证条件，再通过单独 CR 授权。 |
| FU-CR162-001 | Generic CP8 baseline-refresh checker | 保持 candidate；不得扩大当前 CR162 的文档纠错范围。 |
| DF-CR163-001 | Effective-trial/statistical correction producer | raw lineage 稳定后另起 CR，冻结方法与独立验证。 |
| DF-CR163-002 | Historical lineage backfill | 仅在独立数据/审计授权和 provenance 语义确认后重启。 |
| DF-CR163-003 | Real ML/event runner instrumentation | real runner 与 runtime/data authorization 同时具备后重启。 |
| DF-CR164-001 | Effective-trial estimator / multiplicity model | 独立方法 CR 冻结 estimator 假设、偏差、上下界和 verifier 后重启。 |
| DF-CR164-002 | Real ML/event computable-evidence adapters | real runners、同等 lineage contract 与 runtime/data authorization 全部具备后重启。 |
| DF-CR164-003 | Real research recomputation / historical evidence migration | 独立 data/runtime/audit gate 批准，且 inferred provenance 不伪装为 native evidence。 |
| FU-CR161-004 | C3 economic cost / impact producer | 已 promoted to `CR-168`；只启动 fixture/static foundation，真实 TCA/data/runtime 仍未授权。 |
| FU-CR161-005 | C4 capacity / liquidity producer | 独立方法、输入与数据授权；可与 C3 共用输入-contract wave，但计算与验证独立。 |
| FU-CR161-007 | Existing-gate integration、canonical Gate 4 N/A 语义复核和 CR155 regression | C1-C4 producer 均稳定后再做端到端整合；任何新增直接 Gate 4 caller 前决定是否全局硬化 canonical validator；CR155 必须保持 blocked。 |
| FU-CR161-009 | Aggregate orchestration、mature SAP 与 CR155 综合 regression/promotion decision | CR170 完成 canonical hardening 后另启正式 CR；必须在 Stage 3 退出/mature SAP PASS/CR155 promotion 前完成。 |

## CR169 In Scope / Out of Scope 增量

| 分类 | 项目 | 边界 |
|---|---|---|
| In Scope | C4 fixture/static typed evidence | synthetic ADV/reference、participation、capacity/liquidity sizing、三个 refs、lineage/authorization、deterministic hash。 |
| In Scope | strict joint fixture adapter | 仅 verified C3+C4 typed components；精确七字段 Gate4 payload；局部 postcondition。 |
| In Scope | product/architecture decision input | correlation header、alpha disposition、verifier-risk disclosure；CP2 前不形成 HLD 或 Story。 |
| Out of Scope | CR168 C3-only adapter | 保持不变，继续 C4 unavailable fail-closed；不得承载 C4 present。 |
| Out of Scope | canonical Gate4 / aggregate | canonical global N/A hardening、StrategyAdmissionPackage/C1-C4 aggregate 仍归 FU-CR161-007。 |
| Out of Scope | FU-007a / FU-007b 启动 | 007a（canonical N/A 语义硬化）和 007b（aggregate/CR155 regression）仅为拆分提案；必须未来独立 CR、CP0 冲突预检与用户授权。 |
| Out of Scope | real C4 capability | real ADV/liquidity/order/book/flow、真实 capacity calibration、真实 alpha-decay、Stage3/runtime/trading 均不授权。 |
| Out of Scope | CR155 promotion | CR155 admission 必须 BLOCKED 且 `paper_candidate=false`。 |

## Promoted to CR169

| Legacy Deferred ID | CR169 scope | 状态 | 说明 |
|---|---|---|---|
| FU-CR161-005 | MVP-CR169-001..006 | closed / CP8 approved / READY_WITH_RISK | C4 fixture/static foundation 已由 CR169 关闭交付；alpha-decay、真实 C4 与 global integration 仍不在该 CR 范围。 |

## Promoted to CR170

| Legacy Deferred ID | CR170 scope | 状态 | 说明 |
|---|---|---|---|
| FU-CR161-007 canonical-hardening slice | MVP-CR170-001..006 | closed / CP8 approved / READY_WITH_RISK | Gate 1-5 N/A semantics 与 Gate 6 admission hardening 已由 CR170 关闭交付；aggregate/CR155 综合决策仍由 FU-CR161-009 承接。 |

## Promoted to CR158

| Legacy Deferred ID | CR158 scope | 状态 | 说明 |
|---|---|---|---|
| DF-CR157-001 | MVP-CR158-001 / MVP-CR158-002 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | Event adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |
| DF-CR157-002 | MVP-CR158-001 / MVP-CR158-003 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | ML adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |

## Promoted to CR160

| Legacy Deferred ID | CR160 scope | 状态 | 说明 |
|---|---|---|---|
| DF-CR157-003 / BL-CR157-003 | MVP-CR160-001 / MVP-CR160-002 / MVP-CR160-003 / MVP-CR160-004 / MVP-CR160-005 / MVP-CR160-006 | active in CR160 | Stage 4 observation review workflow 从 CR157 deferred/backlog 进入 CR160 纯设计 scope；product baseline refresh 是 CP8 关闭前置条件，Stage 5 simulation/paper/live/runtime authorization 保持后续 CR。 |

## Promoted to CR168

| Legacy Deferred ID | CR168 scope | 状态 | 说明 |
|---|---|---|---|
| FU-CR161-004 | MVP-CR168-001..006 | active / CP2 approved | C3 fixture/static economic cost/slippage/impact approximation foundation 已进入 CR168 CP3；C4、FU-007 aggregate/global Gate4 hardening、真实 TCA/data/runtime、event 与 Stage 3 保持范围外。 |

## CR171 Decision MVP

| MVP ID | In Scope | 成功定义 |
|---|---|---|
| MVP-CR171-001 | 证据路线 CP2 决策 | 已选择 C1-C4 real-producer；activation 另立 CR。 |
| MVP-CR171-002 | FU-006 verifier CP2 决策 | 已选择 event-bounded waiver；在两个机械失效点前必须完成 FU-006。 |
| MVP-CR171-003 | 冻结 future read-contract 决策 | 5 个 allow fields 与 6 类 deny-default 已冻结；该冻结本身不授予读取。 |
| MVP-CR171-004 | 历史事实和 claim ceiling 收敛 | 历史 Stage 3 标为 legacy/require-revalidation；CP8 不能形成 entry-ready。 |

### CR171 Out of Scope

- 本 CR 不读取真实数据湖/NAS、凭据或环境，不执行 C1-C4 computation、runner、runtime、simulation、paper、live 或 trading。
- 不实施 producer、aggregate orchestration、FU-006、修复/回填/rerun、manifest rewrite、provider/NAS/lake 写入、catalog/current pointer 或 publish。
- 不修复 CR010、CR018 或 CR032；只披露其邻接债务与不重开原则。

### CR171 Deferred / Follow-up Conditions

| Deferred ID | 内容 | 重启条件 |
|---|---|---|
| DF-CR171-REAL-EVIDENCE-ACTIVATION | C1-C4 real-producer 的 computation/binding/real-evidence activation | 仅当 CP2 选 C1-C4 且后续独立 activation CR 获得明确授权。 |
| DF-CR171-HISTORICAL-REMEDIATION | 历史数据、schema、PIT、lineage、code、manifest 或证据缺陷修复 | 仅当未来 revalidation 产生 `insufficient_for_current_entry` 或 `incompatible_rework_required`，并另立 CR。 |

## CR172 MVP Scope

### In Scope（CP2 已批准基线）

- 保留 DQ/REQ-001~008 的 prior-approved PATH-B 与 CR173 offline-methodology 历史；本轮只确认 DQ/REQ-009~015。
- 冻结五字段精确有限值候选及 deny-default `6/6`。
- 五字段可冻结且未显式接受 C1-C3 blast radius 时，推荐 PATH-C C1-first。
- C1 release/schema/PIT/lineage/run-identity binding 合同，以及 effective count `typed_unavailable` 降级。
- PATH-B 完成后恢复 PATH-C/A 的 activation 链。
- PATH-C 后 C2/C3 默认分别进入独立 runtime-high-risk CR，总 activation CR 数预计为 `3`。
- effective-trial 不同 owner 合并时的同 revision/hash 双 ledger 和风险交集。
- shared blocker 与 producer-local failure 的隔离语义；不允许 aggregate OR-pass。
- 在 PATH-C/A 前新增 PATH-I，冻结 per-trial portfolio-return source/object、family/run/trial alignment 与错误对象 fail-closed。
- 稳定 identity 使用 logical URI + hash；研究机本地为 active canonical，NAS 为 verified replica/backup/distribution，执行机 pull+verify 后原子 materialize 为 immutable cache。
- 研究机、交易机、NAS、GitHub 四组件职责与允许/禁止数据流；GitHub metadata-only，交易机 approved-package-only。
- data-lake read、multi-trial runtime/workspace、trial-return generation、empirical-R compute、NAS sync、execution pull/materialize 六类动作分别授权。
- 默认执行机本地生成信号；低频/EOD 只冻结 immutable SignalBatch/TargetPositionBatch 的精确 8 字段最小 contract，不冻结 exchange 实现；intraday realtime transport deferred。
- 新运行默认 `${QUANT_LAB_RESEARCH_RUNS_ROOT}/multifactor-strategy-research/{run_id}/`；历史 stage3 目录只读审计。
- declared-exact/empirical R 显式分类；DQ-003 typed-unavailable 降级允许 PATH-C/A 继续设计，但 available effective count 或 `c1_computable=true` 必须先完成 `FU-CR173-001` sampling-error methodology v2。

### Out of Scope

- C4 rework/authorization、FU-CR161-009 aggregate/final SAP/CR155 promotion。
- FU-CR161-006 independent verifier implementation。
- OI-CR171-005 historical classification/revalidation audit，以及 repair/backfill/rerun/manifest rewrite。
- provider fetch、真实 lake/NAS read/write/sync、multi-trial runtime、trial-return generation、empirical-R computation、catalog/current-pointer mutation、credential/env/account、QMT/trading、publish/deploy/Git remote write。
- SignalBatch/TargetPositionBatch 物理 mailbox 路径、七级状态机、ack 状态机、idempotency/replay、真实 sync/transport/consumer；任何 intraday transport 实现。
- 历史目录 move/rename/rewrite、现有 run recanonicalization、真实 migration。
- CP2 前的设计、Story、LLD 或代码实现。

### Deferred / Conditional

- `FU-CR164-004` 默认独立；仅双 owner 合同全部满足时可在 CP2 讨论合并。
- PATH-A 仅在五字段可冻结且用户显式接受 C1-C3 blast radius 时启用。
- 同 parent 顺序 C2/C3 slice 仅在同五字段 revision、同审批/风险/回滚边界、C1 CP7 通过且证据独立时作为备选。
- PATH-I fixture implementation 和验证只证明合同；只有 source/owner、five fields、六类逐动作授权、stable URI、副本/materialization 映射和 fresh precheck 全部就绪后，才能重新发起 PATH-C/A 人工门禁。
- `DF-CR172-SIGNAL-BATCH-EXCHANGE` 承接未来低频 immutable exchange 详细设计与实现；`DF-CR172-INTRADAY-REALTIME-SIGNAL` 承接 intraday realtime transport。两者只登记 backlog candidate，不创建正式 CR。
- `FU-CR173-001` 承接 empirical dependency-matrix methodology v2 与 sampling-error validation；它不阻断 DQ-003 降级设计，但在任何 positive empirical effective-count/C1 claim 前必须完成。public C1 versioned projection、外部 R import contract 与历史路径迁移继续进入独立 Backlog/后续 CR。

### Phase Guards

| Gate | PATH-I 当前允许 | 不得发生 / 最高声明 |
|---|---|---|
| CP2 | 只批准产品范围并解锁 CP3 | 不设计实现，不创建目录，不写 NAS，不运行 multi-trial，不传信号 |
| CP3 | 只冻结设计 | 目录创建、NAS write、multi-trial runtime、signal generation/transport=`0` |
| CP5 | repository-local code/test/fixture | 六类真实动作授权=`0/6`；真实 sync/pull/signal/runtime=`0` |
| CP7 | fixture/static 与零操作验证 | 六类真实动作执行计数=`0/6` |
| CP8 | 最高 `path_i_design_ready=true` 或等价 verified contract-ready | `stage3_entry_ready=false`、`c1_computable=false`、`real_data_authorized=false`、`multi_trial_runtime_authorized=false`、`signal_transport_authorized=false` |

### Success Metrics

| 指标 | 目标 |
|---|---:|
| prior-approved DQ / scope-delta DQ 结构化覆盖 | 8/8 / 7/7 |
| 五字段有限值 | prior PATH-B history；未来 activation 仍需 5/5 |
| deny-default 类别 | 6/6 |
| 新增需求 / 正向+负向覆盖 | 7/7 / 7/7+7/7 |
| stable URI + hash / 四组件 / 数据动作 / SignalBatch 最小字段 | 100% / 4/4 / 6/6 / exactly 8/8 |
| detailed signal path/state/ack/idempotency/replay/sync/transport/consumer implementation | 0/0/0/0/0/0/0/0 |
| PATH-C/A empirical disposition / pre-v2 positive claim | 1/1 / available count=0、c1_computable=false |
| raw-to-effective alias | 0 |
| PATH-B 错误 activation-complete 声明 | 0 |
| partial/mismatched joint approval 合并 | 0 |
| 错误对象/stale/partial/hash/direct-NAS/alignment/forbidden-signal/empirical overclaim 成功数 | 0/0/0/0/0/0/0/0 |
| CP1 真实数据/NAS-sync-pull/signal/credential/provider/write/runtime-trading/migration/Git-remote 操作 | 0/0/0/0/0/0/0/0/0 |
| path_i_design_ready / stage3_entry_ready / c1_computable / real_data_authorized / multi_trial_runtime_authorized / signal_transport_authorized | true(max) / false / false / false / false / false |

## CR173 MVP Scope

### In Scope

- sealed-trial correlation matrix 的 `spectral_participation_ratio` 二阶 effective-dimensionality estimand 与 raw non-alias 边界；不声称 Li–Ji/BH/FWER/Šidák/DSR calibration。
- CP3 冻结的 sealed identity、ordered trial IDs、canonical PSD matrix、method/version/hash、数值契约、二阶假设和 Spike/版本切换条件。
- 缺失/无效/矛盾输入的 `typed_unavailable` / `blocked` fail-closed 与 append-only recovery。
- 独立七字段 `7/7` typed evidence 和 lineage/computation provenance。
- strategy-agnostic、synthetic/fixture/golden-vector-only 输入边界。
- 六类 golden vectors `6/6`，每类重复 `3/3` 的确定性验收。
- standalone evidence 生成 `1/1`、public C1 boundary stop 以及 public projection/write=`0/0` 的 claim ceiling。
- CP2/CP3/CP5 gate、零真实操作和 CR172 不自动恢复合同。

### Out of Scope

- 具体 `strategy_id/strategy_name`、five-field activation scope、真实 run identity 和 real producer binding。
- 真实 lake/NAS/provider/credential、真实计算、runtime、write、trading、publish/deploy、Git remote write。
- public C1 / Gate 1 / statistical summary / DSR / admission 的 versioned projection、adapter、migration、write 与回归；当前这些 consumer 保持 `typed_unavailable`。
- CR172 activation、C2/C3/C4、FU-006、OI-005、aggregate/FU-009、CR155 promotion 和 admission decision。
- 历史证据 backfill/revalidation、真实研究批次或从历史目录/manifest 推断输入。

### Deferred / Conditional

- empirical correlation matrix 的采样误差/稳定性、alpha/tail/FWER 校准需要未来 methodology Spike 或 activation evidence；本 CR 实现数为 `0`。
- public C1 versioned projection 只登记 backlog 后续候选，未建立正式 CR；真正 `c1_computable` 必须经该未来 CR 的 owner、migration 和回归门禁。
- CR173 只关闭 methodology prerequisite。CR172 可按 DQ-003 保留 effective count unavailable 的降级绑定；五字段 + data owner、fresh conflict precheck、strategy identity 和 runtime/real-producer binding 仍由 CR172 独立冻结/批准。

### Success Metrics

| 指标 | 目标 |
|---|---:|
| use case / P0 requirements / scenarios / CP2 DQ | 1 / 8 / 8 / 8 |
| 六类场景 | 6/6 |
| typed evidence schema | 7/7 |
| golden vectors / repeats | 6/6 / 3/3 |
| standalone evidence / public C1 projection / public C1 write / competing gate | 1 / 0 / 0 / 0 |
| raw alias / overclaim / CR172 auto-resume | 0 / 0 / 0 |
| 真实数据/credential/provider/write/runtime-trading/Git remote 操作 | 0/0/0/0/0/0 |
