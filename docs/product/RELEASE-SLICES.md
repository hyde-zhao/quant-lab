# Release Slices

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 发布切片草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 发布切片候选。 |
| v0.3 | 2026-07-11 | meta-pm | 增量追加 CR163 产品基线、架构、五 Story 设计/实现验证与 release-readiness 候选切片。 |
| v0.4 | 2026-07-11 | meta-pm | 根据 SGQ-A 将 CR163 producer slice 明确为 2 条去重 chains / CPI-CR163-001..004 全覆盖，不增加 Story 数。 |
| v0.5 | 2026-07-12 | meta-pm | 增量追加 CR164 产品基线、方法设计义务、五个 product-planning candidates、fixture/static 验证与 release-readiness 候选切片。 |
| v0.6 | 2026-07-13 | host-orchestrator-inline | 增量追加 CR166 CP2→CP8 候选切片，明确 fixture/static foundation 与 Stage 3 真实数据启动分离。 |
| v0.7 | 2026-07-13 | host-orchestrator | 回填 Slice 0 / CP2 已批准；当前进入 Slice 1 / CP3 设计，后续 Slice 2-4 仍受 CP3/CP5/CP8 门禁约束。 |
| v0.8 | 2026-07-13 | host-orchestrator-inline | 增量追加 CR168 CP2→CP8 候选切片；当前只打开 Slice 0/CP2，后续切片未授权。 |
| v0.9 | 2026-07-13 | host-orchestrator-inline | 将 CR168 Slice 0 场景更新为 17，并把 Gate 4 absent-no-na-reason 映射、reason-escape rejection、hash domain 与前向治理义务纳入 Slice 1；后续门禁与授权边界不变。 |
| v1.0 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 Slice 0 / CP2 批准；Slice 1 增加 adapter-only 调用、8-key denylist、strict allowlist、前置拒绝和后置非 PASS 断言，canonical 全局硬化仍不在 CR168。 |
| v1.1 | 2026-07-14 | host-orchestrator-inline-meta-pm | 增量追加 CR169 C4 fixture/static CP2→CP8 候选切片：strict joint adapter 是局部兼容层，alpha-decay 归属留 CP3，真实 C4 与 canonical/global integration 不在切片。 |
| v1.2 | 2026-07-14 | host-orchestrator-inline | CR169 CP2 评审整改与批准：Slice 4 新增 7/7 Stage 2 exit 核验交付义务并显式排除 Stage 3 entry；FU-007 拆分只作后续提案。 |
| v1.3 | 2026-07-15 | host-orchestrator-inline-meta-pm | 增量追加 CR170 canonical Gate 1-5 N/A semantics 与 Gate 6 admission hardening 候选切片；保留现有 bottom-up merge，并明确不含 runner/aggregate/Stage3。 |
| v1.4 | 2026-07-15 | host-orchestrator-inline | 回填 CR170 Slice 0 / CP2 批准；当前进入 Slice 1 / CP3 架构设计，future verifier 仅为契约 consumer，后续 Story/实现/验证仍受 CP3/CP5 门禁约束。 |
| v1.5 | 2026-07-15 | meta-pm | 增量追加 CR171 decision-only 发布切片；CP8 已收敛为决策闭环，仍不能替代数据、computation 或 runtime 授权。 |
| v1.6 | 2026-07-16 | meta-pm（pm-wu） | 增量追加 CR172 PATH-C 推荐发布切片、PATH-B 恢复链及 C2/C3 独立 follow-up；CP2 前只交付决策基线。 |
| v1.7 | 2026-07-16 | meta-pm（pm-zheng） | 增量追加 CR173 offline methodology CP2→CP8 候选切片；算法留 CP3，fixture-only 实现留 CP5 后，CP8 不自动恢复 CR172。 |
| v1.8 | 2026-07-16 | meta-pm（pm-zheng） | 按 CP3 estimator-only split 从 CR173 Slice 1-4 移除 public C1 projection；切片只交付 participation-ratio estimator、standalone 七字段 evidence、golden vectors 与 public-boundary stop。 |
| v1.9 | 2026-07-17 | meta-pm（pm-wu） | 在 CR172 activation slices 前加入 PATH-I instrumentation-first 的 scope/design/fixture-validation 切片；保留 prior PATH-B 与原 C1/C2/C3 activation 规划为 future conditional，PATH-I 完成不自动恢复。 |
| v1.10 | 2026-07-17 | meta-pm（pm-wu） | correction R1 将 PATH-I storage slice 改为 research-local→NAS replica→execution cache，并加入 execution-local/EOD mailbox signal slice 与 intraday future CR。 |
| v1.11 | 2026-07-17 | meta-pm（pm-wu） | correction R2 收缩信号切片为边界/8 字段 contract，详细交换实现全部 deferred；将 empirical positive claim 绑定 `FU-CR173-001`，并把 CP2/3/5/7/8 的授权与最高声明写成切片守卫。 |
| v1.12 | 2026-07-17 | meta-pm（pm-wu） | 回填 CR172 PATH-I scope-delta CP2 用户批准；Slice 0 标记 approved，当前只解锁 Slice I1/CP3 design-only，后续切片、范围与授权边界不变。 |

## CR157 Candidate Slices

| Slice | 目标 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | CP2 product baseline | 产品用例、需求、场景、测试矩阵、MVP scope、待人工决策 | HLD、Story split、实现 | CP2 |
| Slice 1 | Framework design | mature admission package builder HLD、handoff contract、evidence index design、guard design | 代码实现、runtime | CP3 |
| Slice 2 | Story design batch | Story LLD / technical notes、test plan、file ownership | 未批准 Story 实现 | CP5 |
| Slice 3 | Fixture/static implementation | Builder / validation / docs / tests in no-lake mode | provider、NAS、QMT、gateway、simulation/live | CP6/CP7 |
| Slice 4 | Delivery readiness | release notes、rollback、migration N/A、feedback | publish / Git remote write | CP8 |

## CR158 Candidate Slices

| Slice | 目标 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | CP2 product baseline | CR158 use case、requirements、scenarios、test matrix、MVP scope、Decision Brief | HLD、Story split、LLD、实现 | CP2 |
| Slice 1 | Adapter architecture | shared adapter core、event extension、ML extension、evidence typed refs、handoff HLD/ADR | 代码实现、runtime、真实 feed/training | CP3 |
| Slice 2 | Story design batch | CR158-S01..S06 Story plan、LLD/technical notes、file ownership、test plan | 未批准 Story 实现 | CP4/CP5 |
| Slice 3 | Fixture/static adapter implementation | local/static event adapter、ML adapter、typed evidence refs、no-runtime guard tests | provider、NAS、credential、QMT、gateway、model registry、simulation/live | CP6/CP7 |
| Slice 4 | Delivery readiness | release notes、verification report、rollback、feedback、not-authorized wording | publish / Git remote write / production enablement | CP8 |

## CR163 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 确认可信 lineage 的产品语义 | UC/REQ/scenario/matrix、冻结入口清单、count/availability/exclusion、SGQ Decision Brief 输入 | HLD、正式 Story、实现 | CP2 |
| Slice 1 | 冻结跨 run family contract 与 integrity architecture | lifecycle、event model、seal/supersession、existing-consumer integration HLD/ADR | code、runtime、统计方法 | CP3 |
| Slice 2 | 形成可实现的五 Story 设计证据 | CR163-S01..S05 正式拆分、LLD/technical notes、file ownership、fixture plan | 未批准实现 | CP4/CP5 |
| Slice 3 | 让未来研究可原生生成可信 lineage | contract/validator、recorder/seal、2 条去重 P0 producer chains / CPI-CR163-001..004 4/4 mappings、consumer integration、integrity/regression tests | real lake/NAS/provider/broker/trading、C1 statistical computation、backfill | CP6/CP7 |
| Slice 4 | 交付可审计但无 runtime overclaim 的能力 | release notes、migration/rollback、verification、CR155 regression、not-authorized wording | publish、Git remote write、production enablement | CP8 |

## CR164 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结可计算统计证据的用户语义 | 四方法、minima、10 项 QAC、无 OR-pass、raw-count DSR、UC-59/60 compatibility | HLD、正式 Story、实现、统计运行 | CP2 |
| Slice 1 | 冻结可审查的方法与 projection design | method schema；DSR raw-count non-alias；WRC/SPA stationary-bootstrap selection；disagreement decision table；existing consumers | code、外部框架、真实数据/runtime | CP3 |
| Slice 2 | 形成可实现的 Story 设计证据 | 由 meta-se 基于 CR164-S01..S05 候选正式拆分；LLD/technical notes、file ownership、fixture plan | 未批准实现 | CP4/CP5 |
| Slice 3 | 用本地证据证明可计算且 fail-closed | 四方法 fixture/static producer、consumer projection、negative/recovery/compatibility/CR155 validation | real research batch、lake/NAS/provider、ML training/event feed、trading | CP6/CP7 |
| Slice 4 | 交付不夸大的可审计能力 | verification、release notes、rollback/migration、not-authorized wording、remaining risks | publish、Git remote write、production enablement | CP8 |

## CR166 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结 C2 foundation 产品语义 | 输入合同、8 类 P0、daily/ML、event applicability、12 QAC、Stage claim ceiling | HLD、正式 Story、实现、真实数据 | CP2 |
| Slice 1 | 冻结不破坏未来扩展的架构 | C2 envelope、versioned component registry、canonical hash、purge/embargo policy、3 consumers、event applies/N/A | code、C3/C4 calculators、runtime | CP3 |
| Slice 2 | 形成全量实现设计证据 | CP4 正式 Story/DAG 与 CP5 LLD/technical notes/test plan | 未批准代码实现 | CP4/CP5 |
| Slice 3 | 本地证明 C2 可生产且 fail-closed | daily/ML fixtures、8 类负向、determinism、consumer projection、CR155 regression、zero-operation guards | lake/NAS/provider、真实 folds、event feed、trading | CP6/CP7 |
| Slice 4 | 交付桥接能力且不夸大 Stage 状态 | verification、release notes、rollback/migration、Stage2 complete/Stage3 not-started 声明 | Stage3 start、publish、deploy、Git remote write | CP8 |

## CR168 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结 C3 产品语义与方法边界 | use case、9 requirements、15 QAC、17 scenarios、两 fixture、Gate 4 联合边界与 absent-no-na-reason guard、claim ceiling、Decision Brief | HLD、Story、LLD、实现、真实数据 | CP2 |
| Slice 1 | 冻结最小且可演进的 C3 架构 | economic_cost component/schema、9 字段 schema、static approximation、C3/C4 shared header、availability→Gate 4 mapping、8-key denylist、strict allowlist、adapter-only 调用、pre/post guard、component/envelope hash domain、capability/evidence-kind disposition | code、canonical Gate 4 全局修改、C4 calculator、aggregate integration、runtime | CP3 |
| Slice 2 | 形成全量实现设计证据 | CP4 正式 Story/DAG/file ownership 与 CP5 LLD/technical notes/test plan | 未批准代码实现 | CP4/CP5 |
| Slice 3 | 用本地 fixture 证明 C3 可计算且 fail-closed | daily/ML、10 类 C3 输入负向、determinism、Gate 4 C4 absent 路径、na-reason 逃逸阻断、CR155 regression、zero-operation guards | real TCA/data/calibration、C4、event feed、trading | CP6/CP7 |
| Slice 4 | 交付不夸大的 C3 foundation | verification、quality docs under `docs/quality/`、release notes、rollback/migration、claim ceiling | Stage3 start、runtime-ready、publish/deploy/Git remote write | CP8 |

## CR169 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结 C4 产品语义与边界 | use case、9 requirements、15 QAC、17 scenarios、两 fixture、12 类 fail-closed、五项 DQ、claim ceiling | HLD、Story、LLD、实现、真实数据 | CP2 |
| Slice 1 | 冻结可演进 C4 架构 | `capacity_liquidity@v1`、independent C4 body、correlation header、strict joint adapter、seven-key payload、postcondition、alpha disposition | code、CR168 adapter/canonical Gate4/aggregate 修改、真实 capacity、runtime | CP3 |
| Slice 2 | 形成全量实现设计证据 | CP4 formal Story/DAG/file owner 与 CP5 LLD/technical notes/test plan | 未批准实现 | CP4/CP5 |
| Slice 3 | 用本地 fixture 证明 C4 合同 | daily/ML、12 类负向、determinism、C3-only regression、joint fixture contract、CR155 blocked、zero-operation guards | real ADV/liquidity/calibration、alpha（未归入时）、aggregate/trading | CP6/CP7 |
| Slice 4 | 交付不夸大的 C4 foundation | verification、quality docs under `docs/quality/`、release readiness、verifier-risk disclosure、claim ceiling、`STAGE2-EXIT-VERIFICATION.result.json` 的 7/7 合同核验 | Stage3 start/entry-ready、real capacity readiness、canonical hardening/aggregate、publish/deploy/Git remote write | CP8 |

## CR170 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结 canonical fail-closed 产品语义（已完成） | 9 requirements、15 QAC、20 scenarios、21-unit inventory、五态、tier policy、future-verifier 边界、Decision Brief | HLD、Story、代码、真实数据 | CP2 approved |
| Slice 1 | 冻结最小 hardening 架构 | Gate1-5 policy consumption、protected shared-summary merge、`resolve_admission_policy` 边界、public compatibility、adapter retention | current runner/aggregate 接入、adapter 删除、真实数据 | CP3 |
| Slice 2 | 形成全量 Story 设计证据 | CP4 formal Story/DAG/file owner、CP5 LLD/test design，含 Gate1 三层断言 | 未批准实现 | CP4/CP5 |
| Slice 3 | 证明 canonical 语义 fail-closed | 21-unit fixture/static tests、tier 4/4、adapter 2/2、CR155 regression、零外部操作 | Stage3/real lake/provider、aggregate、trading | CP6/CP7 |
| Slice 4 | 交付安全硬化且不夸大集成 | quality/release docs、rollback/migration、claim ceiling、follow-up refs | publish/deploy/Git remote write、Stage3 entry-ready、CR155 promotion | CP8 |

## CR171 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 形成可审计的 entry 决策包 | UC/REQ/scenario/matrix/scope/backlog、3 个 CP2 choices、legacy marker | 数据读取、HLD、Story、LLD、实现、runtime | CP1→CP2 approved |
| Slice 1 | 冻结获批准路线的决策合同 | 仅在 CP2 后设计 route/read/revalidation/verifier contract | 任何 C1-C4 computation、producer binding、repair、provider/lake/NAS 操作 | CP3 |
| Slice 2 | 验证后续受控行为的边界 | 仅在未来单独授权后验证 frozen boundary、legacy verdict 与 waiver expiry | 凭据、provider、写入、catalog/current pointer、runtime/trading | CP7 |
| Slice 3 | 交付不夸大的决策闭环 | release/verification 文档与 CP8 readiness；明确 CP8 不代表 entry-ready | Stage 3 start、real-evidence admission PASS、exit gate、publish/deploy | CP8 approved |

## CR172 Candidate Slices

状态：PATH-I scope-delta CP2 已于 `2026-07-17T16:54:09+08:00` 获用户批准；Slice 0 已确认，当前只解锁 Slice I1 / CP3 design-only，后续切片与真实动作仍未授权。

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结 PATH-I scope delta | 保留旧 8 DQ/8 scenarios；新增 REQ/DQ-009~015、19 scenarios、四组件/信号边界/MVP/矩阵 | HLD、Story、LLD、真实读取、sync/pull/signal/runtime/migration/Git write | CP1→CP2 approved |
| Slice I1 | 冻结 instrumentation 与部署设计 | trial-return source、stable URI/hash、research-local canonical、NAS replica、execution cache、六类动作、新路径、empirical 三选一、信号最小边界 | 目录创建、NAS write、multi-trial runtime、signal generation/transport | CP3 design-only |
| Slice I2 | 形成 PATH-I 全量设计与 repository-local 证据 | CP4 Story/DAG；CP5 LLD/test/rollback 与 repository-local code/test/fixture 边界 | 六类真实动作授权、C1/C2/C3 activation、真实 sync/pull/signal/runtime | CP4/CP5 |
| Slice I3 | 验证 fixture/static instrumentation 与零操作 | 错误对象、stale/partial/hash、direct-NAS-read、alignment、越权、deferred routing；六类真实动作计数 0/6 | 真实 lake read、multi-trial run、trial-return/R、NAS sync/pull、signal transport | CP6/CP7 |
| Slice IS | 验证信号边界 | execution-local 默认；EOD immutable batch 精确 8 字段；禁带字段；S01~S06 deferred/implementation=0 | mailbox path/state/ack/idempotency/replay/sync/transport/consumer、intraday implementation | CP3→CP7 |
| Slice I4 | 交付不夸大的 PATH-I readiness | quality/release/rollback、stable identity 与 component ownership；最高声明 `path_i_design_ready=true` | `stage3_entry_ready`、`c1_computable`、`real_data_authorized`、`multi_trial_runtime_authorized`、`signal_transport_authorized` 为 true | CP8 |
| Activation Resume Gate | 重新判断 PATH-C/A | source/owner、five fields、六类授权、stable URI、副本/materialization、signal boundary、fresh precheck，以及“完成 `FU-CR173-001` / split future activation / DQ-003 downgrade”三选一 | 由 PATH-I CP8 自动恢复或隐含 positive empirical claim | future CP2/runtime-high-risk gate |
| Activation A1-A4（历史条件切片） | 冻结/设计/实现/交付 C1-first activation | 原 Slice 1-4 的 C1 release/schema/PIT/lineage/run identity、typed-unavailable、producer binding 与 CP6/CP7/CP8 证据 | 未满足 Activation Resume Gate 时启动 | future conditional |
| Follow-up C2 | 复用已验证模式并独立授权 C2 | 独立 runtime-high-risk CR；默认在 C1 CP7 后启动 | 与 CR172 C1 同时扩大首次 blast radius | future CP0-CP8 |
| Follow-up C3 | 复用已验证模式并独立授权 C3 | 独立 runtime-high-risk CR；默认在 C1 CP7 后启动 | 与 CR172 C1 同时扩大首次 blast radius | future CP0-CP8 |

prior-approved PATH-B 已由 CR173 完成 estimator-only 方法学前置，但不形成 public C1 projection，也不视为 activation。当前先执行 PATH-I；I4 完成仍不得自动启动 A1-A4。`FU-CR173-001` 仅是 positive empirical output 的硬前置，不是 DQ-003 降级设计的绝对前置。详细低频 exchange 与 intraday transport 分别保留为 `DF-CR172-SIGNAL-BATCH-EXCHANGE`、`DF-CR172-INTRADAY-REALTIME-SIGNAL`，当前正式 CR 数为 0。未来若人工选择 PATH-A，C1/C2/C3 仍必须拆为三个独立可验证 Story，并显式接受 blast radius。

## CR173 Candidate Slices

| Slice | 用户价值 | 包含 | 不包含 | Gate |
|---|---|---|---|---|
| Slice 0 | 冻结可验收的离线方法产品语义 | 1 UC、8 REQ、8 scenarios、8 DQ、non-alias/typed-unavailable/七字段/claim ceiling | 算法、HLD、Story、实现、真实数据 | CP2（已批准） |
| Slice 1 | 冻结 estimator 与 public-boundary stop | `spectral_participation_ratio`、二阶 estimand、sealed-matrix 输入 inventory、有效域、version/hash、standalone schema 和 switch conditions | public C1 projection/write、代码、真实 producer/runtime | CP3 |
| Slice 2 | 形成 estimator-only 全量实现设计证据 | CP4 正式 Story/DAG/file owner；CP5 LLD/test/golden-vector/rollback | public projection Story/Feature、未批准实现 | CP4/CP5 |
| Slice 3 | 用本地 fixture 证明方法可信 | standalone 七字段 evidence、六类 vectors×三次、failure recovery、public-boundary stop、zero-operation guards | public C1 projection/write、真实研究、策略身份、lake/provider/runtime | CP6/CP7 |
| Slice 4 | 交付不夸大的 standalone offline method | quality/release/rollback、`offline_method_ready`、public C1 仍 unavailable、CR172 前置归属说明 | public projection、activation、Stage3/admission/aggregate、publish/deploy/Git remote write | CP8 |

CR173 完成只关闭 CR172 的 methodology prerequisite，不是 activation 完成。CR172 可按 DQ-003 保留 effective count unavailable 的降级绑定；恢复时仍须另行冻结 five fields + data owner、执行 fresh conflict precheck、冻结 strategy identity 并获得 runtime/real-producer 授权。public C1 versioned projection 只作 backlog 后续候选，未建立正式 CR；真正 `c1_computable` 需未来 projection CR。
