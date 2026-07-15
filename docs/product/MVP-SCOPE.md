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
| v1.3 | 2026-07-15 | meta-pm | CR171 增量追加 Stage 3 entry decision MVP、明确 out-of-scope 和 conditional follow-up；只准备 CP2，不启动任何真实数据/运行时行为。 |

## 状态

- 文档状态：awaiting-cp2
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162` / `CR-163` / `CR-164` / `CR-166` / `CR-168`
- 当前门禁：CR168 CP2 待人工批准；CP2 前只允许产品基线增量和人工门禁准备

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
| MVP-CR168-004 | Joint Gate 4 C3 compatibility projection | C3 投影=1；C4 refs absent-no-na-reason；字段级/通用 na-reason 逃逸由 projection BLOCKED/REJECTED；capacity/aggregate PASS=0；C4 calculator=0；canonical Gate 4 修改=0。 |
| MVP-CR168-005 | Two fixture families and event boundary | daily multifactor synthetic + daily/ML compatibility=2/2；event-specific producer=0。 |
| MVP-CR168-006 | Authorization and claim ceiling | Stage2=true、Stage3=false；真实 TCA/calibration/data/runtime=false；CR155 admission promotion=0。 |

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
| CR168 canonical Gate 4 validator、C1-C4 aggregate integration / final StrategyAdmissionPackage / CR155 promotion decision | canonical validator 与 aggregate orchestration 均不修改；端到端集成归属 `FU-CR161-007`；本 CR 只做 1 条带 absent-no-na-reason guard 的 C3-to-Gate-4 compatibility projection。 |
| CR168 event-specific producer | event-time/calendar/execution 语义未冻结；本 CR显式 N/A/deferred。 |
| CR168 runtime、broker/trading、catalog/store/registry pointer、publish/deploy/tag/release/Git remote write | 不在授权范围；所有相关操作计数为 0。 |

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
| FU-CR161-007 | Existing-gate integration and CR155 regression | C1-C4 producer 均稳定后再做端到端整合；CR155 必须保持 blocked。 |

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
| FU-CR161-004 | MVP-CR168-001..006 | active / awaiting CP2 | C3 fixture/static economic cost/slippage/impact approximation foundation 已进入 CR168；C4、FU-007 aggregate integration、真实 TCA/data/runtime、event 与 Stage 3 保持范围外。 |

## CR171 Decision MVP

| MVP ID | In Scope | 成功定义 |
|---|---|---|
| MVP-CR171-001 | 证据路线 CP2 决策 | 仅在 current runner / C1-C4 real-producer 中选择一条；推荐 C1-C4 路线且 activation 另立 CR。 |
| MVP-CR171-002 | FU-006 verifier CP2 决策 | `fu006_first` 或 2 个机械失效点的 event-bounded waiver 二选一。 |
| MVP-CR171-003 | 冻结 future read-contract 决策 | CP2 审查 5 个 allow fields 与 6 类 deny-default，未选择即不授权读取。 |
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
