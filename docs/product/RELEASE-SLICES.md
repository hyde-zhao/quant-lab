# Release Slices

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 发布切片草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 发布切片候选。 |
| v0.3 | 2026-07-11 | meta-pm | 增量追加 CR163 产品基线、架构、五 Story 设计/实现验证与 release-readiness 候选切片。 |
| v0.4 | 2026-07-11 | meta-pm | 根据 SGQ-A 将 CR163 producer slice 明确为 2 条去重 chains / CPI-CR163-001..004 全覆盖，不增加 Story 数。 |

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
