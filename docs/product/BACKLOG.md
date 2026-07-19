# Backlog

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 backlog 草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | CP6 回写 CR157 deferred adapter refs 和 runtime boundary wording。 |
| v0.3 | 2026-07-05 | host-orchestrator | 将 `DF-CR157-001` / `DF-CR157-002` 标记为 promoted to CR158，并保留历史 backlog 追溯。 |
| v0.4 | 2026-07-09 | host-orchestrator | 将 `BL-CR157-003` / `DF-CR157-003` 标记为 promoted to CR160，并补齐 Stage 4 observation review 产品基线追溯。 |
| v0.5 | 2026-07-10 | host-orchestrator | CR162 登记 CR161 evidence-producer 与 verifier-lane follow-ups，以及通用 CP8 baseline-refresh checker candidate。 |
| v0.6 | 2026-07-11 | meta-pm | 将 `FU-CR161-001` 映射为 active `CR-163`，保留旧 candidate 行并追加 CR163 deferred 统计、backfill 与 real-runner 项。 |
| v0.7 | 2026-07-11 | meta-pm | 根据 SGQ-A 明确 CR163 只令 C1 raw-lineage input-ready；C1 计算仍由 FU-CR161-002 承接，CR155 继续 blocked。 |
| v0.8 | 2026-07-12 | meta-pm | 将 `FU-CR161-002` 映射为 active `CR-164`，并追加 effective-trial estimator、real ML/event adapters 与 real recomputation deferred items。 |
| v0.9 | 2026-07-13 | host-orchestrator-inline | 将 `FU-CR161-003` 映射为 active `CR-166`，把 C3、C4 与 existing-gate integration 归一化为独立 `004/005/007`，并与 CR161 structured tracking 对齐。 |
| v0.10 | 2026-07-13 | host-orchestrator-inline | 将 `FU-CR161-004` 映射为 active `CR-168`；修正 Gate 4 为 C3+C4 联合门禁，冻结 fixture/static-only C3、C4 unavailable/fail-closed、FU-007 deferred 和 CR155 admission BLOCKED 边界。 |
| v0.11 | 2026-07-13 | host-orchestrator-inline | 根据 CP2 修改意见把 CR168 的 C4 unavailable 投影收紧为 absent-no-na-reason，并禁止字段级/通用 na-reason 逃逸；不启动 C4、FU-007、registry 治理或 runtime 范围。 |
| v0.12 | 2026-07-14 | host-orchestrator-inline | 回填 CR168 CP2 批准；记录 projection guard 只对 CR168 adapter 局部生效，FU-CR161-007 在 aggregate integration 或新增直接 caller 前必须复核 canonical Gate 4 的 N/A reason 语义。 |
| v0.13 | 2026-07-14 | host-orchestrator-inline-meta-pm | 将 FU-CR161-005 映射为 active CR169，并校正 CR168 为已关闭交付；明确 alpha-decay 仍为 CR169 CP3 disposition、FU-006/007 边界不变。 |
| v0.14 | 2026-07-14 | host-orchestrator-inline | CR169 CP2 评审整改与批准：FU-007 可在未来评估 007a canonical N/A 语义硬化与 007b aggregate/CR155 regression 的拆分；两者均非已启动 CR，需独立 CR/CP0/用户授权。 |
| v0.15 | 2026-07-14 | host-orchestrator-inline-meta-se-critical | CR169 CP3 批准：alpha-decay 不进入 C4 v1，登记 `FU-CR161-008` 作为独立 / C2-adjacent owner 与方法边界评估候选；不创建 formal CR、不启动实现。 |
| v0.16 | 2026-07-15 | host-orchestrator-inline-meta-pm | 关闭 CR169 的 stale active 指针；将 FU-CR161-007 的 canonical-hardening 子切片映射为 active CR170，并把 aggregate + CR155 regression 剩余范围登记为数字型候选 FU-CR161-009。 |
| v0.17 | 2026-07-15 | host-orchestrator-inline | 回填 CR170 CP2 批准；明确 FU-006 独立验证者仅为 future consumer，本 CR 不声明 verifier independence；FU-009 aggregate/CR155 边界和未授权范围不变。 |
| v0.18 | 2026-07-15 | host-orchestrator | 回填 CR170 CP8 批准与 READY_WITH_RISK 关闭；canonical Gate 1-5 N/A semantics、Gate 6 admission hardening 已交付，FU-006/FU-008/FU-009 仍为未启动候选。 |
| v0.19 | 2026-07-15 | meta-pm | CR171 增量登记 historical remediation 与 real-evidence activation 的条件性 follow-up；不提前把任一项变成当前实现范围。 |
| v0.20 | 2026-07-16 | meta-pm（pm-wu） | 将 CR171 activation 候选映射为 active CR172，并登记 PATH-C 下 C2/C3 独立 follow-up、FU-CR164-004 estimator 前置与 OI-005 独立 audit lane。 |
| v0.21 | 2026-07-16 | meta-pm（pm-zheng） | 将 FU-CR164-004 / DF-CR164-001 方法学候选正式映射为 active CR173；明确 strategy-agnostic fixture-only、CP2 pending 和完成后不自动恢复 CR172。 |
| v0.22 | 2026-07-16 | meta-pm（pm-zheng） | 按 CP3 estimator-only split 将 FU-CR164-004 / CR173 当前交付收缩为 participation-ratio 方法与 standalone evidence；登记 public C1 versioned projection 后续候选，不创建正式 CR。 |
| v0.23 | 2026-07-17 | meta-pm（pm-wu） | CR172 PATH-I 增量登记 public projection、empirical-R method/import、legacy path migration 与 activation resume 后续候选；均不由 scope-delta CP2 自动启动。 |
| v0.24 | 2026-07-17 | host-orchestrator | CP2 发起前同步 CR173 closed/cp8_closed 与 CR172 scope-delta pending 状态，移除旧 active/CP3 pending 和未来实现措辞；候选项及触发条件不变。 |
| v0.25 | 2026-07-17 | meta-pm（pm-wu） | correction R1 更新 activation resume 为六类数据动作与 replica/materialization，并新增 intraday realtime signal transport 独立 CR 候选。 |
| v0.26 | 2026-07-17 | meta-pm（pm-wu） | correction R2 登记 `FU-CR173-001` empirical methodology v2 候选，并将低频 batch exchange 与 intraday realtime signal 分别登记为 `DF-CR172-SIGNAL-BATCH-EXCHANGE`、`DF-CR172-INTRADAY-REALTIME-SIGNAL`；均不创建正式 CR。 |
| v0.27 | 2026-07-17 | meta-pm（pm-wu） | 回填 CR172 PATH-I scope-delta CP2 用户批准；active tracking 从 pending 更新为 approved/ready-for-CP3，所有 deferred candidate、触发条件和未授权边界不变。 |

## Candidates

| ID | 标题 | 类型 | 推荐优先级 | 触发条件 |
|---|---|---|---|---|
| DF-CR157-001 | Event strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 event strategy 归一到 `StrategyTypeAdapter` / `SignalSet` / `ResearchEvidenceIndex`；当前 CR 只保留 backlog ref，不实现 event feed / event-time adapter。 |
| DF-CR157-002 | ML strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 ML strategy 归一到项目级策略候选合同；当前 CR 只保留 backlog ref，不实现 training snapshot / model registry / ML evidence adapter。 |
| BL-CR157-003 | Stage 4 observation review workflow | promoted to CR160 | P1 | 已由 `CR-160` 承接 Stage 4 observation review workflow 设计、observation plan template、分层 checklist、fail-closed decision table 和 authorization gate contract；不授权 simulation / paper / live / runtime。 |
| BL-CR157-004 | Process compact route for existing-evidence hygiene | process follow-up | P2 | 来自 CR156 retrospective，用于减少后续 hygiene CR 过度处理。 |
| FU-CR161-001 | Experiment-family trial lineage instrumentation | promoted to CR163 | P0 | 已由 `CR-163` 承接 pre-search family declaration、append-only trial/attempt/selection、raw count、seal/supersession、existing-gate integration 与 CR155 regression；CP2 前不得设计/实现。 |
| FU-CR161-002 | C1 multiple-testing, data-snooping and overfit evidence producer | promoted to CR164 | P0 | 已由 `CR-164` 承接 BH、WRC/SPA、PBO/CSCV、raw-count-declared DSR、输入充分性、保守聚合与 existing-consumer projection；effective-trial estimator 仍 deferred。 |
| FU-CR161-003 | C2 walk-forward / OOS evidence producer foundation | promoted to CR166 | P0 | CR-166 仅以 fixture/static 输入建立 producer、fail-closed 与既有 consumer projection；真实 fold/OOS 灌入和 Stage 3 运行另行授权。 |
| FU-CR161-004 | C3 economic cost / slippage / impact evidence producer foundation | promoted to CR168 | P0 | 已由 `CR-168` 启动 fixture/static-only 产品基线；只消费显式合成/静态参数，复用 versioned evidence component envelope，不授权真实 TCA、C4 计算或 Stage 3。 |
| FU-CR161-005 | C4 capacity / liquidity / ADV evidence producer foundation | closed (`CR-169`) | P0 | `CR-169` 已以 `READY_WITH_RISK` 关闭：5/5 Story、Stage 2 合同 7/7 与 repository suite 2159/0 已完成；真实 ADV/liquidity、Stage 3 和 CR155 promotion 仍未授权。 |
| FU-CR161-006 | Independent CP7 verifier-lane resilience | process / QA follow-up | P1 | 高风险后续实现需要独立 QA 结论，或 CR161 waiver 到期前。 |
| FU-CR161-007 | Canonical Gate 1-5 N/A semantics + Gate 6 admission hardening | closed (`CR-170`) | P0 | `CR-170` 已经 CP8 批准并以 `READY_WITH_RISK` 关闭：Gate 1-5 N/A semantics 与 Gate 6 admission tier 边界已硬化；未接 Stage3 runner，未实现 aggregate 或 CR155 promotion。 |
| FU-CR161-008 | Alpha-decay evidence ownership and C2-adjacent method evaluation | methodology / architecture follow-up | P1 | CR169 C4 v1 保持 `alpha_decay_calculator=0`；仅在需要冻结预测能力时间衰减的 owner、输入窗口、OOS/C2 关系和 schema version 时，通过独立 formal CR、CP0 冲突预检与用户授权启动。 |
| FU-CR161-009 | C1-C4 aggregate integration and CR155 regression | follow-up CR（former FU-007 aggregate slice） | P1 | 以 CR170 closed 为前置；后续才接 aggregate orchestration、最终 StrategyAdmissionPackage 和 CR155 综合 regression，任何 promotion 仍需独立决策。 |
| FU-CR162-001 | Generic CP8 product-baseline-refresh checker | process follow-up | P1 | 任一 CR 设置 `product_baseline_refresh_required=true` 时；需独立 process CR/授权。 |
| DF-CR163-001 | Effective-trial and statistical-correction producer | follow-up CR | P0 | CR163 raw lineage 已稳定、统计方法/输入/独立验证另行批准时。 |
| DF-CR163-002 | Historical lineage backfill | audit/data follow-up | P1 | 获得独立数据与审计授权，并明确 inferred/backfilled provenance 不得伪装为 native instrumentation 时。 |
| DF-CR163-003 | Real ML/event candidate runner instrumentation | runtime/data follow-up | P1 | real runner 存在且 runtime/data authorization 独立通过时；当前 adapter 仅 fixture/static compatibility。 |
| DF-CR164-001 | Effective-trial estimator / multiplicity model | methodology follow-up | P0 | CR164 维持 effective count typed_unavailable；另起 CR 冻结 estimator 假设、偏差、上下界与 verifier。 |
| DF-CR164-002 | Real ML/event computable-evidence adapters | runtime/data follow-up | P1 | UC-59/60 当前 compatibility-only；real runner、lineage 与 data/runtime authorization 均具备后重启。 |
| DF-CR164-003 | Real research recomputation / historical evidence migration | audit/data follow-up | P1 | 独立 data/runtime/audit gate 批准，且 inferred/backfilled provenance 不伪装为 native evidence。 |
| DF-CR171-REAL-EVIDENCE-ACTIVATION | C1-C4 real-producer activation | runtime/data follow-up | P0 | 仅当 CR171 CP2 选择 C1-C4 real-producer 后，另立 formal CR 并显式授权 computation、producer binding 与受控数据行为；CR171 本身不授权。 |
| DF-CR171-HISTORICAL-REMEDIATION | Historical Stage 3 evidence remediation | audit/data follow-up | P1 | 仅在获授权 revalidation 输出 `insufficient_for_current_entry` 或 `incompatible_rework_required` 后；不得在 CR171 内 repair/backfill/rerun。 |
| FU-CR164-004 | Effective-trial offline estimator methodology | delivered by `CR-173` / PATH-B history | P0 | CR173 已完成 strategy-agnostic participation-ratio estimator 与 standalone evidence 方法学；public C1 projection/write=`0/0`，仍不解决 trial-return source、empirical R、five fields、runtime 或 activation。 |
| DF-CR173-PUBLIC-C1-VERSIONED-PROJECTION | Public C1 versioned effective-dimensionality projection | follow-up candidate（未建正式 CR） | P0 | 只在 C1 contract owner 接受语义区分字段或 versioned discriminated schema、trust binding、旧/新迁移、无 dual truth、8/8 production paths 与 12/12 regression/authorization 路径都有独立授权时，才可发起正式 CR；在此前 public C1/Gate1/admission 保持 `typed_unavailable`。 |
| DF-CR172-C2-REAL-EVIDENCE-ACTIVATION | C2 real-evidence activation | runtime-high-risk follow-up CR | P0 | PATH-C 获批且 C1 CP7 通过后，按独立五字段/owner/rollback/证据边界启动；不预分配具体 CR 编号。 |
| DF-CR172-C3-REAL-EVIDENCE-ACTIVATION | C3 real-evidence activation | runtime-high-risk follow-up CR | P0 | PATH-C 获批且 C1 CP7 通过后，按独立五字段/owner/rollback/证据边界启动；不预分配具体 CR 编号。 |
| DF-CR172-OI005-REVALIDATION-AUDIT | OI-CR171-005 historical classification/revalidation | audit follow-up | P1 | 独立 audit authorization lane；classification 与 repair 均不属于 CR172 activation。 |
| FU-CR173-001 | Empirical dependency-matrix methodology v2 and sampling-error validation | CR173 methodology follow-up candidate（未建正式 CR） | P0 | 仅当要输出 available effective trial count 或声明 `c1_computable=true` 时为硬前置；最小范围含 sampling-error/uncertainty evidence、method version 2 + hash、有效域/偏差界限、独立验证。DQ-003 typed-unavailable 降级不被阻断。 |
| DF-CR172-EXTERNAL-R-IMPORT | External empirical-R import and validation contract | data/methodology follow-up | P1 | native producer 不可用且外部 R provenance 可达到 8/8 时评估；不得用 declared-exact fixture 或无 source/hash 的 matrix 替代。 |
| DF-CR172-LEGACY-PATH-MIGRATION | Historical stage3 path migration | migration/audit follow-up | P1 | 只有独立 inventory、hash、rollback、stable-URI preservation 与人工 migration authorization 齐备时启动；当前历史目录只读。 |
| DF-CR172-ACTIVATION-RESUME | Resume PATH-C/A after PATH-I | runtime-high-risk follow-up gate | P0 | source/owner、five fields、六类数据动作、stable URI、replica/materialization、signal disposition 和 fresh precheck 全部就绪后重新发起人工门禁；PATH-I CP8 不自动触发。 |
| DF-CR172-SIGNAL-BATCH-EXCHANGE | Low-frequency immutable SignalBatch/TargetPositionBatch exchange detailed design and implementation | deferred candidate（未建正式 CR） | P1 | PATH-I 只冻结精确 8 字段最小 contract；物理路径、七级状态机、ack、idempotency/replay、真实 sync/transport/consumer 均在 CR172 CP8 后再决定是否转 FU。 |
| DF-CR172-INTRADAY-REALTIME-SIGNAL | Intraday realtime signal transport | deferred realtime/security candidate（未建正式 CR） | P0 | 只有明确 intraday/低延迟需求时评估；mTLS、ordered delivery、ack/replay、failover、SLO 和交易授权均不进入 PATH-I，CR172 CP8 后再决定是否转 FU。 |

## Promoted Items

| Legacy ID | Promoted ID | 状态 | 正式 CR | 说明 |
|---|---|---|---|---|
| DF-CR157-001 | FU-CR157-001 | active | `CR-158` | Event strategy adapter implementation 已进入 CR158 统一 adapter scope；仍不授权真实 event feed / live listener。 |
| DF-CR157-002 | FU-CR157-002 | active | `CR-158` | ML strategy adapter implementation 已进入 CR158 统一 adapter scope；仍不授权真实 model training / external model service / registry promotion。 |
| BL-CR157-003 / DF-CR157-003 | FU-CR160-STAGE4-OBSERVATION-REVIEW | active | `CR-160` | Stage 4 observation review workflow 已进入 CR160 纯设计 scope；CR160 关闭后只形成 review/gate contract 基线，不自动启动 Stage 5 paper/simulation 或 runtime authorization。 |
| FU-CR161-001 | CR-163 | closed | `CR-163` | 保留 CR161 follow-up 历史；CR163 只实现 raw experiment-family lineage 事实来源。 |
| FU-CR161-002 | CR-164 | closed | `CR-164` | 保留 CR161 follow-up 历史；CR164 承接 C1 computable evidence，但不承接 effective-trial estimator、real batch、UC-59/60 real adapters 或 runtime authorization。 |
| FU-CR161-003 | CR-166 | closed | `CR-166` | C2 fixture/static producer foundation 已关闭交付；不连接真实 lake，不宣称真实 OOS evidence 可用，不启动 C3/C4 或 Stage 3。 |
| FU-CR161-004 | CR-168 | closed | `CR-168` | C3 fixture/static economic cost/slippage/impact approximation foundation 已以 READY_WITH_RISK 关闭；Gate 4 projection containment 仅在 CR168 adapter 局部生效，FU-007 aggregate/global hardening 继续 deferred。 |
| FU-CR161-005 | CR-169 | closed | `CR-169` | C4 fixture/static capacity/liquidity/ADV foundation 已以 READY_WITH_RISK 关闭；真实 C4、Stage 3 与 CR155 promotion 不授权。 |
| FU-CR161-007 | CR-170 | closed | `CR-170` | canonical Gate 1-5 N/A semantics 与 Gate 6 admission policy 已以 READY_WITH_RISK 关闭；aggregate/CR155 regression 仍保留为 FU-CR161-009。 |
| DF-CR171-REAL-EVIDENCE-ACTIVATION | CR-172 | active / scope-delta CP2 approved / ready-for-CP3 | `CR-172` | prior PATH-B 与 DQ-001~008 保持历史批准；PATH-I、trial-return、研究机 canonical/NAS replica/执行机 cache、stable URI、四组件、六动作授权、新路径、empirical-R 与 signal boundary 的 DQ-009~015 已于 `2026-07-17T16:54:09+08:00` 按推荐值批准，只解锁 CP3，不授权真实读取、sync、pull、signal、producer computation、runtime 或实现。 |
| DF-CR164-001 / FU-CR164-004 | CR-173 | closed / cp8_closed / READY_WITH_RISK | `CR-173` | 已交付 participation-ratio 二阶 effective-dimensionality 离线方法与 standalone evidence；不承接 public C1 projection、策略身份、真实数据或 activation，也不自动恢复 CR172。 |

## Runtime Boundary

CR157 backlog refs, CR158 adapter scope, CR160 Stage 4 observation review scope, CR161/CR162 evidence availability baseline, CR163 trial-lineage instrumentation, CR164 C1 computable evidence, CR166 C2 fixture/static foundation, CR168 C3 fixture/static foundation, CR171 decision baseline, CR172 activation candidate and CR173 offline methodology baseline do not authorize real lake/NAS/provider/credential/QMT/gateway/runtime/simulation/paper/live/trading/broker/feed/order/reconciliation/store/catalog/registry/model registry/prediction store/publish/external framework/Git remote operations. CR173 已以 synthetic/fixture/golden-vector estimator-only 范围关闭；它不需要策略身份，只产出 standalone evidence，public C1 projection/write 各为 `0`，不形成 real evidence，也不自动恢复 CR172。CR172 可保留 effective count unavailable 降级绑定；positive empirical available count / `c1_computable=true` 必须先完成 `FU-CR173-001`，并且 public C1 仍须等待 `DF-CR173-PUBLIC-C1-VERSIONED-PROJECTION` 的独立门禁。两个 DF signal candidate 均不是正式 CR，也不授权 exchange 或 transport。CR171/CR172 only define a future deny-default read contract candidate; CP1/CP2/CP8 are not real-data, computation or runtime authorization by implication. Historical Stage 3 evidence remains legacy/require-revalidation until a separately authorized revalidation reports a permitted verdict. CR160/CR161/CR163/CR164/CR166/CR168 consume existing CR155 evidence only as a fail-closed classification sample; none may create new data access, runtime authorization or historical backfill. CR166 does not make real walk-forward/OOS evidence available; CR168 does not provide real TCA, C4 capacity evidence or Stage 3 readiness。CR155 lifecycle 已关闭，但 admission package 必须继续保持 `BLOCKED` 且 `paper_candidate=false`。
