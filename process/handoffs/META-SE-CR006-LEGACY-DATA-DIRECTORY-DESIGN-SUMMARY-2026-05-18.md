---
handoff_id: "META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-SUMMARY-2026-05-18"
from_agent: "meta-se"
to_agent: "meta-po"
status: "completed"
created_at: "2026-05-18T21:30:00+08:00"
workflow_id: "local_backtest"
change_id: "CR-006"
wave_id: "CR006-BATCH-A"
dispatch_note: "父线程负责回填原 handoff 的 spawn_agent agent_id/thread_id；本文件仅记录 meta-se 设计修订结果。"
---

# META-SE Summary：CR-006 Tushare-first Data Design

## 本轮完成

| 产物 | 路径 | 状态 |
|---|---|---|
| HLD 增量 | `process/HLD.md` §23 | 已重写为 Tushare-first |
| ADR 增量 | `process/ARCHITECTURE-DECISION.md` ADR-018 | 已重写为 Tushare-first |
| Story Backlog | `process/STORY-BACKLOG.md` v0.8 | 已替换为 CR006-S01..S04 |
| Development Plan | `process/DEVELOPMENT-PLAN.yaml` v0.6 | 已更新 CR006-BATCH-A |
| Story 卡片 | `process/stories/CR006-S01-tushare-first-data-acquisition-runbook.md` | 已替换 |
| Story 卡片 | `process/stories/CR006-S02-canonical-gold-lightweight-engine-adapter.md` | 已替换 |
| Story 卡片 | `process/stories/CR006-S03-backtrader-clean-feed-contract.md` | 已替换 |
| Story 卡片 | `process/stories/CR006-S04-old-data-reference-only-guardrail.md` | 已新增 |
| CP3 自动预检 | `process/checks/CP3-CR006-HLD-PRECHECK.md` | PASS |
| CP4 自动预检 | `process/checks/CP4-CR006-STORY-PLAN-PRECHECK.md` | PASS |

## 关键设计结论

- CR-006 新主线改为 Tushare-first：Tushare structured lake 是新链路事实源。
- 不能承诺 Tushare 完全覆盖旧 repo `data/`；旧 `data/` 保持现状，仅供以后人工参考/比对。
- raw/manifest 仍然需要，但只属于数据获取、审计、断点续传、复现、replay 和质量追溯层，不是回测运行时依赖。
- 当前轻量回测框架应消费 canonical/gold reader，或消费由 canonical/gold 派生的 external `legacy_flat`，不得默认 fallback repo `data/`。
- Backtrader 只消费经过 quality gate、PIT as-of 和复权一致检查后的 clean OHLCV / factor / score feed。
- CR006-BATCH-A 覆盖全部 4 个 Story，CP5 必须全量 LLD 统一确认后才能开发。

## 安全确认

- 未读取、列出、迁移、复制或删除真实 `data/**` 数据。
- 未读取、打印或记录 `.env`、Tushare token、NAS 用户名、密码或真实私有路径。
- 未修改 `engine/**`、`experiments/**`、`config/**`、README、docs、tests、`market_data/**`、`delivery/**`。

## 交给 meta-po 的下一步

1. 生成 `checkpoints/CP3-CR006-HLD-REVIEW.md` 并发起 HLD/ADR 人工确认。
2. 若 CP3 approved，生成 `checkpoints/CP4-CR006-STORY-PLAN-REVIEW.md` 并发起 Story Plan 人工确认。
3. 若 CP4 approved，调度 meta-dev 为 CR006-BATCH-A 的全部 4 张 Story 生成 LLD；CP5 必须等全部 LLD 与自动预检完成后统一确认。
