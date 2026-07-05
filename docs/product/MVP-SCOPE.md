# MVP Scope

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 MVP 范围草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | 追加 CR158 event + ML strategy adapter 统一 scope、out-of-scope 和 promoted deferred 映射。 |

## 状态

- 文档状态：draft
- 关联 CR：`CR-157` / `CR-158`
- 当前门禁：CR158 CP2 pending user review

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

## Deferred

| Deferred ID | 内容 | 推荐后续路径 |
|---|---|---|
| DF-CR157-001 | Event strategy adapter | 后续独立 CR，复用 `StrategyTypeAdapter` 合同。 |
| DF-CR157-002 | ML strategy adapter | 后续独立 CR，复用 `SignalSet` / `ResearchEvidenceIndex` 合同。 |
| DF-CR157-003 | Stage 4 observation review workflow | 后续 observation / simulation authorization gate。 |

## Promoted to CR158

| Legacy Deferred ID | CR158 scope | 状态 | 说明 |
|---|---|---|---|
| DF-CR157-001 | MVP-CR158-001 / MVP-CR158-002 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | Event adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |
| DF-CR157-002 | MVP-CR158-001 / MVP-CR158-003 / MVP-CR158-004 / MVP-CR158-005 | active in CR158 | ML adapter 从 CR157 deferred 进入 CR158 统一 adapter scope。 |
