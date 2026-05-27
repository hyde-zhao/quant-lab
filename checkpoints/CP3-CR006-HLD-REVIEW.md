---
checkpoint_id: "CP3"
checkpoint_name: "CR-006 HLD 架构评审门"
type: "auto_then_manual"
status: "approved"
owner: "meta-po"
created_at: "2026-05-18T22:13:32+08:00"
reviewed_by: "user"
reviewed_at: "2026-05-18T22:33:23+08:00"
auto_check_result: "process/checks/CP3-CR006-HLD-PRECHECK.md"
supersedes:
  - "previous CP3 draft for legacy data directory externalization before Tushare-first feedback"
target:
  phase: "solution-design"
  story_id: ""
  artifacts:
    - "process/HLD.md"
    - "process/ARCHITECTURE-DECISION.md"
    - "process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md"
    - "process/checks/CP3-CR006-HLD-PRECHECK.md"
    - "process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-SUMMARY-2026-05-18.md"
---

# CP3 CR-006 HLD 架构评审门

本检查点确认对象是 CR-006 的 **Tushare-first 数据方案**，不是上一版 legacy `data/` 外置化 + fallback 方案。

本 CP3 只确认 HLD / ADR 架构增量是否可作为 Story Plan 与后续 LLD 输入；不授权实现、测试改造、文档交付改造、Tushare 真实抓取、真实数据迁移、真实数据读取、复制、列出或删除。

## 自动预检摘要

| 预检文件 | 结论 | 阻断项 | 说明 |
|---|---|---|---|
| `process/checks/CP3-CR006-HLD-PRECHECK.md` | PASS | 0 | HLD §23 与 ADR-018 已重写为 Tushare-first：Tushare structured lake 为新事实源；raw/manifest 保留为采集审计和复现层；轻量回测与 Backtrader 只消费 quality gate 后的 canonical/gold 或 clean feed；旧 repo `data/` 只作以后人工参考。 |

## 审查回填说明

用户最新回复“全部接受，拉起meta-po继续推进，能够并行时，拉起子agent并行。”按 Codex exact 文本确认协议解析为本 CP3 的 `approved`。本批准只覆盖 CR-006 Tushare-first HLD / ADR 架构增量，不扩大为实现授权、真实 Tushare 抓取授权、旧 `data/**` 操作授权或凭据读取授权。

## Entry Criteria

| 条目 | 状态 | 证据 | 审查意见 |
|---|---|---|---|
| CP3 前用户修改意见已纳入 | approved | 用户要求旧 `data/` 不删除但先放弃，仅供以后参考；新方案以 Tushare 为主 |  |
| meta-se 已真实调度并完成 Tushare-first 修订 | approved | `process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-SUMMARY-2026-05-18.md`；agent_id/thread_id=`019e3b5f-402c-7321-bfd0-929247130042` |  |
| HLD 已重写 CR-006 架构增量 | approved | `process/HLD.md` §23 |  |
| ADR 已重写 CR-006 决策 | approved | `process/ARCHITECTURE-DECISION.md` ADR-018 |  |
| CP3 自动预检已通过 | approved | `process/checks/CP3-CR006-HLD-PRECHECK.md` |  |

## Checklist

| # | 检查项 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|---|
| 1 | 是否接受 CR-006 新主线从 legacy 外置化改为 Tushare-first 数据方案 | approved | `process/HLD.md` §23.1-§23.3 |  |
| 2 | 是否接受“不承诺 Tushare 完全覆盖旧 repo `data/`”作为正式设计边界 | approved | `process/HLD.md` §23.1、§23.10；ADR-018 |  |
| 3 | 是否接受旧 repo `data/` 保持现状、仅供以后人工参考/比对，不删除、不迁移、不复制、不读取、不列出 | approved | `process/HLD.md` §23.3、§23.8；ADR-018 |  |
| 4 | 是否接受 Tushare structured lake 作为新事实源，继续使用 `MARKET_DATA_LAKE_ROOT` 下 raw / manifest / canonical / quality / catalog / gold 分层 | approved | `process/HLD.md` §23.4；ADR-018 |  |
| 5 | 是否接受 raw / manifest 仍然需要，但只属于采集审计、断点续传、复现、replay 和质量追溯层，不属于回测运行时依赖 | approved | `process/HLD.md` §23.4；ADR-018 |  |
| 6 | 是否接受当前轻量回测框架消费 canonical/gold reader，或兼容期消费由 canonical/gold 派生的 external `legacy_flat`，不得默认 fallback repo `data/` | approved | `process/HLD.md` §23.4、§23.6、§23.7 |  |
| 7 | 是否接受 Backtrader 只消费 quality gate、PIT as-of、复权一致检查后的 clean OHLCV / factor / score feed | approved | `process/HLD.md` §23.6、§23.8；ADR-018 |  |
| 8 | 是否接受 Backtrader 不读 raw/manifest、不读 token、不导入 connector/runtime/storage、不触发补数 | approved | `process/HLD.md` §23.6、§23.8；ADR-016/017/018 |  |
| 9 | 是否接受 external `legacy_flat` 仅为从 canonical/gold 派生的兼容输出，不等同旧 repo `data/`，也不作为新事实源 | approved | `process/HLD.md` §23.4、§23.7；ADR-018 |  |
| 10 | 是否接受 CR006-BATCH-A 改为 4 个 Story：Tushare acquisition/runbook、轻量 engine adapter、Backtrader clean feed、old data reference-only guardrail | approved | `process/STORY-BACKLOG.md`；`process/DEVELOPMENT-PLAN.yaml` |  |
| 11 | 是否接受 CP3 通过不授权实现、Tushare 真实抓取、旧 `data/**` 比对或任何真实数据操作 | approved | 本文件；`process/checks/CP3-CR006-HLD-PRECHECK.md` |  |
| 12 | 是否接受风险、Gotchas 和 OPEN 项进入后续 CP4 / CP5 / 实现设计处理 | approved | `process/HLD.md` §23.10、§23.13、§23.14 |  |

## Exit Criteria

| 条目 | 审查结果 | 证据 | 审查意见 |
|---|---|---|---|
| Tushare-first HLD / ADR 增量可作为 CR-006 Story Plan 与 LLD 输入 | approved | `process/HLD.md`、`process/ARCHITECTURE-DECISION.md` |  |
| raw / manifest 职责边界已被接受 | approved | HLD §23；ADR-018 |  |
| 轻量回测和 Backtrader 消费边界已被接受 | approved | HLD §23；ADR-018 |  |
| 旧 repo `data/` reference-only 边界已被接受 | approved | HLD §23；ADR-018 |  |
| 未授权实现或真实数据操作 | approved | 本文件；CP3 自动预检 REQUIRED |  |

## Deliverables

| 交付物 | 路径 | 审查结果 | 审查意见 |
|---|---|---|---|
| CR-006 Tushare-first HLD 增量 | `process/HLD.md` | approved |  |
| CR-006 ADR 增量 | `process/ARCHITECTURE-DECISION.md` | approved |  |
| CR-006 变更单 | `process/changes/CR-006-LEGACY-DATA-DIRECTORY-EXTERNALIZATION-2026-05-18.md` | approved |  |
| CP3 自动预检 | `process/checks/CP3-CR006-HLD-PRECHECK.md` | approved |  |
| meta-se summary | `process/handoffs/META-SE-CR006-LEGACY-DATA-DIRECTORY-DESIGN-SUMMARY-2026-05-18.md` | approved |  |

## 人工审查结果

- 结论：`approved`
- 审查人：user
- 审查时间：2026-05-18T22:33:23+08:00
- 修改意见：无。用户“全部接受”当前 Tushare-first CP3 审查稿，允许进入 CP4 Story Plan 确认与后续 CR006-BATCH-A 全量 LLD 调度。
- 风险接受项：
  - CP3 通过只代表 CR-006 Tushare-first HLD / ADR 架构增量可进入 CP4 Story Plan 确认，不授权实现。
  - CP3 通过不授权 Tushare 真实抓取、回补、normalize、validate 或写入真实数据湖。
  - CP3 通过不授权读取、列出、迁移、复制、比对或删除真实 `data/**` 数据。
  - CP3 通过不授权读取、打印或记录 `.env`、Tushare token、NAS 用户名、密码或真实私有路径。
  - CP3 通过不授权修改 `engine/**`、`experiments/**`、`config/**`、README、docs、tests、`market_data/**`、`delivery/**` 或真实数据；这些只允许在 CP4、全量 CP5 和对应实现门控通过后按 Story 范围执行。
