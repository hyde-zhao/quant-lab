# Release Slices

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 发布切片草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 发布切片候选。 |

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
