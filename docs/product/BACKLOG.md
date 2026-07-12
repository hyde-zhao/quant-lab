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

## Candidates

| ID | 标题 | 类型 | 推荐优先级 | 触发条件 |
|---|---|---|---|---|
| DF-CR157-001 | Event strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 event strategy 归一到 `StrategyTypeAdapter` / `SignalSet` / `ResearchEvidenceIndex`；当前 CR 只保留 backlog ref，不实现 event feed / event-time adapter。 |
| DF-CR157-002 | ML strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 ML strategy 归一到项目级策略候选合同；当前 CR 只保留 backlog ref，不实现 training snapshot / model registry / ML evidence adapter。 |
| BL-CR157-003 | Stage 4 observation review workflow | promoted to CR160 | P1 | 已由 `CR-160` 承接 Stage 4 observation review workflow 设计、observation plan template、分层 checklist、fail-closed decision table 和 authorization gate contract；不授权 simulation / paper / live / runtime。 |
| BL-CR157-004 | Process compact route for existing-evidence hygiene | process follow-up | P2 | 来自 CR156 retrospective，用于减少后续 hygiene CR 过度处理。 |
| FU-CR161-001 | Experiment-family trial lineage instrumentation | promoted to CR163 | P0 | 已由 `CR-163` 承接 pre-search family declaration、append-only trial/attempt/selection、raw count、seal/supersession、existing-gate integration 与 CR155 regression；CP2 前不得设计/实现。 |
| FU-CR161-002 | C1 multiple-testing, data-snooping and overfit evidence producer | promoted to CR164 | P0 | 已由 `CR-164` 承接 BH、WRC/SPA、PBO/CSCV、raw-count-declared DSR、输入充分性、保守聚合与 existing-consumer projection；effective-trial estimator 仍 deferred。 |
| FU-CR161-003 | C2 walk-forward / OOS evidence producer | follow-up CR | P0 | purged-embargo fold manifest、fold metrics 和 OOS inputs 可用时。 |
| FU-CR161-004 | C3/C4 economic cost and capacity evidence producer | follow-up CR | P0 | 真实可审计成本、impact、capacity 和 liquidity inputs 获独立授权时。 |
| FU-CR161-005 | Existing-gate integration and CR155 regression implementation | follow-up CR | P1 | 各 producer 可输出 typed evidence 后；必须复用 CR151/CR154，且 CR155 仍 blocked。 |
| FU-CR161-006 | Independent CP7 verifier-lane resilience | process / QA follow-up | P1 | 高风险后续实现需要独立 QA 结论，或 CR161 waiver 到期前。 |
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
| FU-CR161-001 | CR-163 | active | `CR-163` | 保留 CR161 follow-up 历史；CR163 只实现 raw experiment-family lineage 事实来源，不启动 FU-CR161-002..006。 |
| FU-CR161-002 | CR-164 | active | `CR-164` | 保留 CR161 follow-up 历史；CR164 承接 C1 computable evidence，但不承接 effective-trial estimator、real batch、UC-59/60 real adapters 或 runtime authorization。 |

## Runtime Boundary

CR157 backlog refs, CR158 adapter scope, CR160 Stage 4 observation review scope, CR161/CR162 evidence availability baseline, CR163 trial-lineage instrumentation and CR164 computable-evidence product scope do not authorize real lake/NAS/provider/credential/QMT/gateway/runtime/simulation/paper/live/trading/broker/feed/order/reconciliation/store/catalog/registry/model registry/prediction store/publish/external framework/Git remote operations. CR160/CR161/CR163/CR164 consume existing CR155 evidence only as a fail-closed classification sample; none may create new data access, runtime authorization or historical backfill. CR164 statistical computation remains future fixture/static implementation subject to CP5 and does not authorize real research execution.
