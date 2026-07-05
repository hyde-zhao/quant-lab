# Story Map

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 Stage 2 多因子研究框架升级 Story Map 草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter unified implementation Story Map 候选。 |
| v0.3 | 2026-07-05 | host-orchestrator | CP3 approved 后将 CR158-S01..S06 对齐为 CP4 开发 Story；CP2 baseline 改为 gate evidence，不占开发 Story ID。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158`
- 当前门禁：CR158 CP2 pending user review
- 注意：CP2 未批准前，以下 Story 只是产品规划候选，不是 `DEVELOPMENT-PLAN` 或 dev-ready Story。

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

## Release Slice Candidate

| Slice | Included Candidate Stories | Out of Scope |
|---|---|---|
| CR157 first slice | CR157-S01, CR157-S02, CR157-S03, CR157-S04, CR157-S05, CR157-S06 backlog alignment only | event adapter implementation, ML adapter implementation, provider/lake/runtime/trading/publish |
| CR158 unified adapter slice | CR158-S01, CR158-S02, CR158-S03, CR158-S04, CR158-S05, CR158-S06 | real event feed, real ML model training, external model service, provider/lake/NAS/credential access, runtime/trading/publish |
