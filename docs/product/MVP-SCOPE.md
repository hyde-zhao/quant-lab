# MVP Scope

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 MVP 范围草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 统一 scope、out-of-scope 和 promoted deferred 映射。 |
| v0.3 | 2026-07-09 | host-orchestrator | 追加 CR160 Stage 4 observation review design-only scope，并将 `DF-CR157-003` promoted to CR160。 |
| v0.4 | 2026-07-10 | host-orchestrator | CR162 补齐 CR161 evidence availability 产品范围、fail-closed ceiling、CR155 regression 和 deferred producers。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158` / `CR-160` / `CR-161` / `CR-162`
- 当前门禁：CR162 CP7 static verification

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

## Deferred

| Deferred ID | 内容 | 推荐后续路径 |
|---|---|---|
| DF-CR157-001 | Event strategy adapter | 后续独立 CR，复用 `StrategyTypeAdapter` 合同。 |
| DF-CR157-002 | ML strategy adapter | 后续独立 CR，复用 `SignalSet` / `ResearchEvidenceIndex` 合同。 |
| DF-CR157-003 | Stage 4 observation review workflow | 已 promoted to `CR-160`；CR160 覆盖 Stage 4 review workflow design，不覆盖 Stage 5 simulation/paper/runtime authorization。 |
| FU-CR161-001..006 | Evidence producers and independent verifier lane | 保持 candidate；先满足输入 lineage/metrics/cost/capacity 和独立验证条件，再通过单独 CR 授权。 |
| FU-CR162-001 | Generic CP8 baseline-refresh checker | 保持 candidate；不得扩大当前 CR162 的文档纠错范围。 |

## Promoted to CR158

| Legacy Deferred ID | CR158 scope | 状态 | 说明 |
|---|---|---|---|
| DF-CR157-001 | MVP-CR158-001 / MVP-CR158-002 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | Event adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |
| DF-CR157-002 | MVP-CR158-001 / MVP-CR158-003 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | ML adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |

## Promoted to CR160

| Legacy Deferred ID | CR160 scope | 状态 | 说明 |
|---|---|---|---|
| DF-CR157-003 / BL-CR157-003 | MVP-CR160-001 / MVP-CR160-002 / MVP-CR160-003 / MVP-CR160-004 / MVP-CR160-005 / MVP-CR160-006 | active in CR160 | Stage 4 observation review workflow 从 CR157 deferred/backlog 进入 CR160 纯设计 scope；product baseline refresh 是 CP8 关闭前置条件，Stage 5 simulation/paper/live/runtime authorization 保持后续 CR。 |
