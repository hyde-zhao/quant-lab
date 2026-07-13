# Story Map

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级 Story Map 草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation Story Map 候选。 |
| v0.3 | 2026-07-05 | host-orchestrator | CP3 approved 后将 CR158-S01..S06 对齐为 CP4 开发 Story；CP2 baseline 改为 gate evidence，不占开发 Story ID。 |
| v0.4 | 2026-07-11 | meta-pm | 增量追加 CR163 五个 outcome-oriented candidate Stories；仅作为 CP2/CP3 输入，不写入 DEVELOPMENT-PLAN。 |
| v0.5 | 2026-07-11 | meta-pm | 根据 SGQ-A 将 CR163-S03 明确覆盖 2 条去重 producer chains / 全部 CPI-CR163-001..004 mappings；五 Story 数量不变。 |
| v0.6 | 2026-07-12 | meta-pm | 增量追加 CR164 五个 outcome-oriented product-planning candidates，承接四方法、量化 AC、保守聚合与 compatibility-only 范围；不写入 DEVELOPMENT-PLAN。 |
| v0.7 | 2026-07-13 | host-orchestrator-inline | 增量追加 CR166 五个 outcome candidate；CP2 前不形成正式 Story、DAG 或文件所有权。 |
| v0.8 | 2026-07-13 | host-orchestrator | 回填 CR166 CP2 批准；五个 outcome 进入 CP3 架构输入，但在 CP3 批准前仍不是正式 Story。 |
| v0.9 | 2026-07-13 | host-orchestrator | 回填 CR166 CP3 批准；五个 outcome 由 CP4 正式化为 CR166-S01..S05，并进入五个串行安全 Wave。 |

## 状态

- 文档状态：confirmed-cp3
- 关联 CR：`CR-157` / `CR-158` / `CR-163` / `CR-164` / `CR-166`
- 当前门禁：CR166 CP3 已批准；CP4 自动预检与 CP5 全量设计证据准备中
- 注意：CR166-S01..S05 已成为正式 Story，但在 CP5 批准前均为 `lld-ready`，不是 `dev-ready`。

## Activities

| Activity | User Task | Candidate Story | Priority | Gate |
|---|---|---|---|---|
| Stage 2 scope confirmation | 确认 first slice 边界 | CR157-S01 CP2 product baseline confirmation | P0 | CP2 |
| Mature admission package | 定义 package builder 合同 | CR157-S02 Mature admission package builder design | P0 | CP3/CP5 |
| Evidence traceability | 定义 evidence index 和 refs | CR157-S03 Research evidence index integration | P0 | CP3/CP5 |
| Handoff hardening | 区分 Stage 2/3/4 边界 | CR157-S04 Stage 2/Stage 3 handoff hardening | P0 | CP3/CP5 |
| No-runtime safety | fail-closed guard | CR157-S05 No-runtime guard tests | P0 | CP5/CP7 |
| Future adapters | 保留 event/ML 扩展入口 | CR157-S06 Adapter backlog alignment | P1 | CP3 |
| CR158 scope confirmation | 确认 event+ML 统一 adapter 范围 | CR158-CP2 product baseline confirmation（gate evidence, not development Story） | P0 | CP2 |
| Shared adapter core | 定义共享 adapter core 与 type-specific extension | CR158-S01 Shared adapter core contract | P0 | CP4/CP5 |
| Event adapter | 实现 event strategy adapter fixture/static path | CR158-S02 Event strategy adapter extension | P0 | CP5/CP6/CP7 |
| ML adapter | 实现 ML strategy adapter fixture/static path | CR158-S03 ML strategy adapter extension | P0 | CP5/CP6/CP7 |
| Evidence and handoff | 扩展 evidence index typed refs 和 Stage 2/3 handoff | CR158-S04 Evidence and handoff typed refs | P0 | CP4/CP5/CP7 |
| No-runtime guard | 证明 forbidden operation counters fail-closed | CR158-S05 No-runtime guard counters | P0 | CP5/CP6/CP7 |
| Adapter release boundary | 文档、release wording 与 no-runtime 验证 | CR158-S06 Verification and release boundary | P1 | CP7/CP8 |
| Declare and validate lineage contract | 在首次搜索前建立 family 并验证完整性 | CR163-S01 Family contract + validator candidate | P0 | CP3/CP5 |
| Preserve research history | 记录 trial / attempt / selection 并确定性 seal | CR163-S02 Recorder + seal + hash candidate | P0 | CP3/CP5 |
| Cover all frozen producers | 让两条去重候选生产链及其 direct hooks 均不能绕过 lineage | CR163-S03 Both producer chains / CPI-CR163-001..004 instrumentation candidate | P0 | CP3/CP5 |
| Reuse existing admission controls | 把 availability/ref/raw count 接入既有 gate，维持 effective unavailable | CR163-S04 Existing admission integration candidate | P0 | CP3/CP5 |
| Prove integrity and regression | 验证 recovery/tamper/count/permission/CR155 fail-closed | CR163-S05 Integrity + recovery + CR155 regression candidate | P0 | CP5/CP7 |
| Freeze computable-evidence outcome | 确认四方法、输入充分性和 10 项量化 AC | CR164-S01 Method/input/QAC contract candidate | P0 | CP3/CP5 |
| Control multiple testing and data snooping | 获得 BH 与 WRC/SPA 的 provenance-bound evidence | CR164-S02 BH + WRC/SPA evidence candidate | P0 | CP3/CP5 |
| Quantify overfit and deflated performance | 获得 PBO/CSCV 与 raw-count-declared DSR evidence | CR164-S03 PBO/CSCV + DSR evidence candidate | P0 | CP3/CP5 |
| Preserve conservative admission semantics | 无 OR-pass 地投影到既有 consumers，并保持 UC-59/60 compatibility-only | CR164-S04 Conservative projection + compatibility candidate | P0 | CP3/CP5 |
| Prove fail-closed and determinism | 覆盖低充分性、NaN/Inf、冲突、tamper、recovery、permission 和 CR155 | CR164-S05 Independent fixture/static verification candidate | P0 | CP5/CP7 |

## Release Slice Candidate

| Slice | Included Candidate Stories | Out of Scope |
|---|---|---|
| CR157 first slice | CR157-S01, CR157-S02, CR157-S03, CR157-S04, CR157-S05, CR157-S06 backlog alignment only | event adapter implementation, ML adapter implementation, provider/lake/runtime/trading/publish |
| CR158 unified adapter slice | CR158-S01, CR158-S02, CR158-S03, CR158-S04, CR158-S05, CR158-S06 | real event feed, real ML model training, external model service, provider/lake/NAS/credential access, runtime/trading/publish |
| CR163 trial lineage slice | CR163-S01..S05 candidate set | statistical correction、historical backfill、real ML/event runner、real data/runtime/trading/publish |
| CR164 computable statistical evidence slice | CR164-S01..S05 product-planning candidates | effective-trial estimator、real ML/event adapter implementation、real research batch/data/runtime/trading/publish |

> CR163-S01..S05 是目标为五个 Stories 的产品规划候选，不是正式 Story decomposition；CP2 批准后仍须 CP3 HLD，之后由 meta-se 在 CP4 生成机器真相源。

CR163-S03 scope note：不增加第六个 Story；S03 单一 candidate Story 必须覆盖 public Stage 3 chain、legacy CR039 chain 及 `build_strategy_candidate` / `build_strategy_candidates` 两个 hook，即 CPI-CR163-001..004 4/4 instrumentation mappings。

> CR164-S01..S05 只是产品 outcome 候选，不是正式 Story decomposition。CP2 批准后仍须 CP3；正式 Story 数、边界、依赖与文件所有权由 meta-se 在 CP4 决定。
## CR166 Product-planning Candidates

| Activity | User Task | Candidate Story | Priority | Gate |
|---|---|---|---|---|
| C2 contract | 冻结 fold/split/purge/embargo/metric/lineage 输入与 typed envelope | CR166-S01 Common C2 input and evidence contract | P0 | CP3/CP5 |
| Leakage validation | 阻断时间逆序、purge/embargo 与 metric/lineage 缺口 | CR166-S02 Temporal, leakage and sufficiency validator | P0 | CP3/CP5/CP7 |
| Deterministic production | 输出 fold-level reason、pass-rate、canonical hash 与 version chain | CR166-S03 Deterministic C2 producer | P0 | CP5/CP6/CP7 |
| Existing integration | 保守投影到三个 existing consumers，保持 CR155 blocked | CR166-S04 Existing-consumer projection and regression | P0 | CP3/CP5/CP7 |
| Compatibility and verification | daily/ML fixtures、event applicability、deny-default 与 claim ceiling | CR166-S05 Compatibility and independent verification | P0/P1 | CP5/CP7/CP8 |

以上 5 项已获 CP3 批准，并由 CP4 冻结为正式 Story、五个串行安全 Wave、显式依赖、文件所有权与 `full-lld` policy；CP5 批准前不得实现。
