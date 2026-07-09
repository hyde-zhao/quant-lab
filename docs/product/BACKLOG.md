# Backlog

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| v0.1 | 2026-07-05 | host-orchestrator | 新建 CR157 backlog 草案。 |
| v0.2 | 2026-07-05 | host-orchestrator | CP6 回写 CR157 deferred adapter refs 和 runtime boundary wording。 |
| v0.3 | 2026-07-05 | host-orchestrator | 将 `DF-CR157-001` / `DF-CR157-002` 标记为 promoted to CR158，并保留历史 backlog 追溯。 |
| v0.4 | 2026-07-09 | host-orchestrator | 将 `BL-CR157-003` / `DF-CR157-003` 标记为 promoted to CR160，并补齐 Stage 4 observation review 产品基线追溯。 |

## Candidates

| ID | 标题 | 类型 | 推荐优先级 | 触发条件 |
|---|---|---|---|---|
| DF-CR157-001 | Event strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 event strategy 归一到 `StrategyTypeAdapter` / `SignalSet` / `ResearchEvidenceIndex`；当前 CR 只保留 backlog ref，不实现 event feed / event-time adapter。 |
| DF-CR157-002 | ML strategy adapter implementation | follow-up CR | P1 | CR157 first slice 交付后，需要把 ML strategy 归一到项目级策略候选合同；当前 CR 只保留 backlog ref，不实现 training snapshot / model registry / ML evidence adapter。 |
| BL-CR157-003 | Stage 4 observation review workflow | promoted to CR160 | P1 | 已由 `CR-160` 承接 Stage 4 observation review workflow 设计、observation plan template、分层 checklist、fail-closed decision table 和 authorization gate contract；不授权 simulation / paper / live / runtime。 |
| BL-CR157-004 | Process compact route for existing-evidence hygiene | process follow-up | P2 | 来自 CR156 retrospective，用于减少后续 hygiene CR 过度处理。 |

## Promoted Items

| Legacy ID | Promoted ID | 状态 | 正式 CR | 说明 |
|---|---|---|---|---|
| DF-CR157-001 | FU-CR157-001 | active | `CR-158` | Event strategy adapter implementation 已进入 CR158 统一 adapter scope；仍不授权真实 event feed / live listener。 |
| DF-CR157-002 | FU-CR157-002 | active | `CR-158` | ML strategy adapter implementation 已进入 CR158 统一 adapter scope；仍不授权真实 model training / external model service / registry promotion。 |
| BL-CR157-003 / DF-CR157-003 | FU-CR160-STAGE4-OBSERVATION-REVIEW | active | `CR-160` | Stage 4 observation review workflow 已进入 CR160 纯设计 scope；CR160 关闭后只形成 review/gate contract 基线，不自动启动 Stage 5 paper/simulation 或 runtime authorization。 |

## Runtime Boundary

CR157 backlog refs, CR158 adapter scope and CR160 Stage 4 observation review scope do not authorize real lake/NAS/provider/credential/QMT/gateway/runtime/simulation/paper/live/trading/broker/feed/order/reconciliation/store/catalog/registry/model registry/prediction store/publish/external framework/Git remote operations. CR160 consumes existing CR155 evidence only as a fail-closed classification sample and may not create new data access or runtime authorization.
