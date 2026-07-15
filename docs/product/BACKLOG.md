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
| FU-CR161-005 | C4 capacity / liquidity / ADV evidence producer foundation | active (`CR-169`) | P0 | `CR-169` 已启动 fixture/static-only C4 foundation：输入合同与 C3 计算独立，CP3 冻结最小关联头并决定 alpha-decay 归属；不读取真实 ADV/liquidity，不修改 canonical Gate 4，不做 aggregate 或 CR-155 promotion。 |
| FU-CR161-006 | Independent CP7 verifier-lane resilience | process / QA follow-up | P1 | 高风险后续实现需要独立 QA 结论，或 CR161 waiver 到期前。 |
| FU-CR161-007 | Existing-gate integration, canonical Gate 4 N/A semantics and CR155 regression implementation | follow-up CR；可评估 007a/007b 拆分 | P1 | 非绑定提案：007a 可仅处理 canonical absent+na-reason 全局语义硬化，007b 可承接 aggregate + CR155 regression；任何一个均须另行创建正式 CR、完成 CP0 冲突预检并取得用户授权。当前 CR169 不启动、不修改 canonical 或 aggregate。 |
| FU-CR161-008 | Alpha-decay evidence ownership and C2-adjacent method evaluation | methodology / architecture follow-up | P1 | CR169 C4 v1 保持 `alpha_decay_calculator=0`；仅在需要冻结预测能力时间衰减的 owner、输入窗口、OOS/C2 关系和 schema version 时，通过独立 formal CR、CP0 冲突预检与用户授权启动。 |
| FU-CR162-001 | Generic CP8 product-baseline-refresh checker | process follow-up | P1 | 任一 CR 设置 `product_baseline_refresh_required=true` 时；需独立 process CR/授权。 |
| DF-CR163-001 | Effective-trial and statistical-correction producer | follow-up CR | P0 | CR163 raw lineage 已稳定、统计方法/输入/独立验证另行批准时。 |
| DF-CR163-002 | Historical lineage backfill | audit/data follow-up | P1 | 获得独立数据与审计授权，并明确 inferred/backfilled provenance 不得伪装为 native instrumentation 时。 |
| DF-CR163-003 | Real ML/event candidate runner instrumentation | runtime/data follow-up | P1 | real runner 存在且 runtime/data authorization 独立通过时；当前 adapter 仅 fixture/static compatibility。 |
| DF-CR164-001 | Effective-trial estimator / multiplicity model | methodology follow-up | P0 | CR164 维持 effective count typed_unavailable；另起 CR 冻结 estimator 假设、偏差、上下界与 verifier。 |
| DF-CR164-002 | Real ML/event computable-evidence adapters | runtime/data follow-up | P1 | UC-59/60 当前 compatibility-only；real runner、lineage 与 data/runtime authorization 均具备后重启。 |
| DF-CR164-003 | Real research recomputation / historical evidence migration | audit/data follow-up | P1 | 独立 data/runtime/audit gate 批准，且 inferred/backfilled provenance 不伪装为 native evidence。 |

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
| FU-CR161-005 | CR-169 | active | `CR-169` | C4 fixture/static capacity/liquidity/ADV foundation 已通过 CP3；严格 C3+C4 joint adapter 仅为 fixture compatibility，alpha-decay 已拆为 `FU-CR161-008`，真实 C4 与 CR155 promotion 不授权。 |

## Runtime Boundary

CR157 backlog refs, CR158 adapter scope, CR160 Stage 4 observation review scope, CR161/CR162 evidence availability baseline, CR163 trial-lineage instrumentation, CR164 C1 computable evidence, CR166 C2 fixture/static foundation and CR168 C3 fixture/static foundation do not authorize real lake/NAS/provider/credential/QMT/gateway/runtime/simulation/paper/live/trading/broker/feed/order/reconciliation/store/catalog/registry/model registry/prediction store/publish/external framework/Git remote operations. CR160/CR161/CR163/CR164/CR166/CR168 consume existing CR155 evidence only as a fail-closed classification sample; none may create new data access, runtime authorization or historical backfill. CR166 does not make real walk-forward/OOS evidence available; CR168 does not provide real TCA, C4 capacity evidence or Stage 3 readiness。CR155 lifecycle 已关闭，但 admission package 必须继续保持 `BLOCKED` 且 `paper_candidate=false`。
